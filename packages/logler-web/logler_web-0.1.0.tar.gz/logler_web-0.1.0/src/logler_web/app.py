"""
FastAPI web application for Logler Web.

This is the backend API server that serves the Vue frontend and provides
log parsing, filtering, and analysis endpoints using the logler package.
"""

import glob
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import from logler package
from logler.parser import LogEntry, LogParser
from logler.log_reader import LogReader
from logler.tracker import ThreadTracker
from logler.investigate import follow_thread_hierarchy, analyze_error_flow

# SqlEngine may not be available in all logler versions
try:
    from logler.sql import SqlEngine
    HAS_SQL_ENGINE = True
except ImportError:
    SqlEngine = None
    HAS_SQL_ENGINE = False

# Configuration
LOG_ROOT = Path(os.environ.get("LOGLER_ROOT", ".")).expanduser().resolve()

# Static files directory (built frontend)
DIST_DIR = Path(__file__).parent / "static"
MAX_RETURNED_ENTRIES = 10000


def _ensure_within_root(path: Path) -> Path:
    """Ensure path is within LOG_ROOT to prevent directory traversal."""
    resolved = path.expanduser().resolve()
    if resolved == LOG_ROOT or LOG_ROOT in resolved.parents:
        return resolved
    raise HTTPException(
        status_code=403, detail="Requested path is outside the configured log root"
    )


def _sanitize_glob_pattern(pattern: str) -> str:
    """Remove path traversal sequences from glob patterns."""
    import re as _re

    while ".." in pattern:
        old_pattern = pattern
        pattern = _re.sub(r"\.\.[\\/]", "", pattern)
        pattern = _re.sub(r"[\\/]\.\.", "", pattern)
        pattern = _re.sub(r"^\.\.", "", pattern)
        if pattern == old_pattern:
            break
    return pattern


def _glob_within_root(pattern: str, base_dir: Optional[str] = None) -> List[Path]:
    """Run a glob pattern scoped to LOG_ROOT."""
    if not pattern:
        return []

    pattern = _sanitize_glob_pattern(pattern)

    # Use base_dir if provided, otherwise LOG_ROOT
    root = Path(base_dir) if base_dir else LOG_ROOT
    try:
        root = _ensure_within_root(root)
    except HTTPException:
        root = LOG_ROOT

    if not Path(pattern).is_absolute():
        raw_pattern = str(root / pattern)
    else:
        raw_pattern = pattern

    matches = glob.glob(raw_pattern, recursive=True)
    results: List[Path] = []
    seen = set()

    for match in matches:
        p = Path(match)
        try:
            p = _ensure_within_root(p)
        except HTTPException:
            continue
        if not p.is_file():
            continue
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        results.append(p)

    return sorted(results)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Logler Web",
        description="Web UI for Logler - Beautiful log viewer",
    )

    # Global state
    parser = LogParser()
    tracker = ThreadTracker()
    websocket_clients: List[WebSocket] = []

    # Request/Response Models
    class FileRequest(BaseModel):
        path: str
        filters: Optional[Dict[str, Any]] = None
        limit: Optional[int] = None
        quick: Optional[bool] = None

    class FilesRequest(BaseModel):
        paths: List[str]
        filters: Optional[Dict[str, Any]] = None
        limit: Optional[int] = None

    class FilterRequest(BaseModel):
        paths: List[str]
        filters: Optional[Dict[str, Any]] = None
        limit: Optional[int] = None
        sample_per_level: Optional[int] = None
        sample_per_thread: Optional[int] = None

    class HierarchyRequest(BaseModel):
        paths: List[str]
        root_identifier: str
        max_depth: Optional[int] = None
        min_confidence: float = 0.0
        use_naming_patterns: bool = True
        use_temporal_inference: bool = True

    class SqlRequest(BaseModel):
        query: str

    # Helper functions
    def _parse_timestamp(ts: Any) -> Optional[datetime]:
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _entry_to_dict(entry: LogEntry, file_path: Optional[str] = None) -> Dict[str, Any]:
        result = {
            "line_number": entry.line_number,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "level": entry.level.upper() if entry.level else "UNKNOWN",
            "message": entry.message,
            "thread_id": entry.thread_id,
            "correlation_id": entry.correlation_id,
            "trace_id": entry.trace_id,
            "span_id": entry.span_id,
            "service_name": entry.service_name,
            "raw": entry.raw,
        }
        if file_path:
            result["file"] = file_path
        return result

    def _load_file_entries(
        file_path: str, quick: bool = True, limit: int = 1000
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """Load entries from a file, optionally in quick mode (tail only)."""
        path = _ensure_within_root(Path(file_path))
        entries = []
        total = 0
        partial = False

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            total = len(lines)

            if quick and total > limit:
                lines = lines[-limit:]
                partial = True
                start_line = total - limit + 1
            else:
                start_line = 1

            for i, line in enumerate(lines):
                line = line.rstrip("\n\r")
                if line:
                    entry = parser.parse_line(start_line + i, line)
                    entries.append(_entry_to_dict(entry, file_path))
                    tracker.track(entry)

        return entries, total, partial

    def _filter_entries(
        entries: List[Dict[str, Any]], filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply filters to entries."""
        if not filters:
            return entries

        result = entries

        # Filter by levels
        levels = filters.get("levels")
        if levels:
            normalized = {lvl.upper() for lvl in levels}
            result = [e for e in result if e.get("level") in normalized]

        # Filter by search query
        query = (filters.get("search") or "").lower()
        if query:
            result = [
                e
                for e in result
                if query in (e.get("message") or "").lower()
                or query in (e.get("raw") or "").lower()
            ]

        # Filter by thread_id
        thread_id = filters.get("thread_id")
        if thread_id:
            result = [e for e in result if thread_id in (e.get("thread_id") or "")]

        # Filter by correlation_id
        correlation_id = filters.get("correlation_id")
        if correlation_id:
            result = [
                e for e in result if correlation_id in (e.get("correlation_id") or "")
            ]

        return result

    # Routes

    @app.get("/api/files/browse")
    async def browse_files(directory: Optional[str] = None):
        """Browse directory for log files."""
        if directory:
            current = _ensure_within_root(Path(directory))
        else:
            current = LOG_ROOT

        parent = current.parent if current != LOG_ROOT else None
        if parent and parent not in [LOG_ROOT] + list(LOG_ROOT.parents):
            parent = None

        files = []
        directories = []

        for item in sorted(current.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                directories.append({"name": item.name, "path": str(item)})
            elif item.is_file():
                is_log = item.suffix.lower() in [".log", ".txt", ".json"]
                files.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat(),
                        "is_log": is_log,
                    }
                )

        return {
            "current_dir": str(current),
            "parent_dir": str(parent) if parent else None,
            "files": files,
            "directories": directories,
            "log_root": str(LOG_ROOT),
        }

    @app.get("/api/files/glob")
    async def glob_files(pattern: str, base_dir: Optional[str] = None, limit: int = 200):
        """Search for files using glob pattern."""
        results = _glob_within_root(pattern, base_dir)
        truncated = len(results) > limit
        results = results[:limit]

        files = []
        for path in results:
            files.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    "is_log": path.suffix.lower() in [".log", ".txt", ".json"],
                }
            )

        return {
            "pattern": pattern,
            "count": len(files),
            "files": files,
            "truncated": truncated,
        }

    @app.post("/api/files/open")
    async def open_file(request: FileRequest):
        """Open a single log file."""
        quick = request.quick if request.quick is not None else True
        limit = request.limit or 1000

        entries, total, partial = _load_file_entries(request.path, quick, limit)

        if request.filters:
            entries = _filter_entries(entries, request.filters)

        return {
            "file_path": request.path,
            "entries": entries[:MAX_RETURNED_ENTRIES],
            "total": total,
            "partial": partial,
        }

    @app.post("/api/files/open_many")
    async def open_many_files(request: FilesRequest):
        """Open multiple log files and interleave entries."""
        all_entries = []
        file_counts: Dict[str, int] = {}
        file_meta = []

        for file_path in request.paths:
            entries, total, _ = _load_file_entries(file_path, quick=False)
            file_counts[file_path] = len(entries)

            timestamps = [e.get("timestamp") for e in entries if e.get("timestamp")]
            file_meta.append(
                {
                    "path": file_path,
                    "count": len(entries),
                    "first_ts": min(timestamps) if timestamps else None,
                    "last_ts": max(timestamps) if timestamps else None,
                }
            )

            all_entries.extend(entries)

        # Sort by timestamp
        all_entries.sort(key=lambda e: e.get("timestamp") or "")

        if request.filters:
            all_entries = _filter_entries(all_entries, request.filters)

        limit = request.limit or MAX_RETURNED_ENTRIES

        return {
            "files": request.paths,
            "entries": all_entries[:limit],
            "total": len(all_entries),
            "file_counts": file_counts,
            "file_meta": file_meta,
        }

    @app.post("/api/files/filter")
    async def filter_files(request: FilterRequest):
        """Filter entries from loaded files."""
        all_entries = []

        for file_path in request.paths:
            entries, _, _ = _load_file_entries(file_path, quick=False)
            all_entries.extend(entries)

        all_entries.sort(key=lambda e: e.get("timestamp") or "")

        if request.filters:
            all_entries = _filter_entries(all_entries, request.filters)

        limit = request.limit or MAX_RETURNED_ENTRIES

        return {
            "entries": all_entries[:limit],
            "total": len(all_entries),
        }

    @app.get("/api/threads")
    async def get_threads():
        """Get tracked threads."""
        threads = []
        for thread_id, entries in tracker.threads.items():
            error_count = sum(
                1
                for e in entries
                if e.level and e.level.upper() in ["ERROR", "CRITICAL", "FATAL"]
            )
            timestamps = [e.timestamp for e in entries if e.timestamp]

            threads.append(
                {
                    "thread_id": thread_id,
                    "log_count": len(entries),
                    "error_count": error_count,
                    "first_seen": min(timestamps).isoformat() if timestamps else None,
                    "last_seen": max(timestamps).isoformat() if timestamps else None,
                }
            )

        return threads

    @app.get("/api/traces")
    async def get_traces():
        """Get OpenTelemetry traces."""
        traces = []
        for trace_id, entries in tracker.traces.items():
            spans = list({e.span_id for e in entries if e.span_id})
            timestamps = [e.timestamp for e in entries if e.timestamp]

            traces.append(
                {
                    "trace_id": trace_id,
                    "spans": spans,
                    "start_time": min(timestamps).isoformat() if timestamps else None,
                    "end_time": max(timestamps).isoformat() if timestamps else None,
                }
            )

        return traces

    @app.post("/api/hierarchy")
    async def build_hierarchy(request: HierarchyRequest):
        """Build thread/span hierarchy."""
        hierarchy = follow_thread_hierarchy(
            request.paths,
            request.root_identifier,
            max_depth=request.max_depth,
            min_confidence=request.min_confidence,
            use_naming_patterns=request.use_naming_patterns,
            use_temporal_inference=request.use_temporal_inference,
        )

        error_analysis = None
        if hierarchy:
            error_analysis = analyze_error_flow(hierarchy)

        return {
            "hierarchy": hierarchy,
            "error_analysis": error_analysis,
        }

    @app.post("/api/sql")
    async def execute_sql(request: SqlRequest):
        """Execute SQL query on loaded logs."""
        if not HAS_SQL_ENGINE:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": "SQL engine not available. Please upgrade logler package.",
            }

        try:
            # Get entries from tracker
            all_entries = []
            for entries in tracker.threads.values():
                all_entries.extend(entries)

            if not all_entries:
                return {
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "error": "No logs loaded. Open a file first.",
                }

            # Create SQL engine and load data
            engine = SqlEngine()

            # Create a simple index structure
            class LogIndex:
                pass

            idx = LogIndex()
            idx.entries = all_entries
            engine.load_files({"logs": idx})

            # Execute query
            result_json = engine.query(request.query)
            rows = json.loads(result_json)

            columns = list(rows[0].keys()) if rows else []

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
        except Exception as e:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": str(e),
            }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time log following."""
        await websocket.accept()
        websocket_clients.append(websocket)

        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")

                if action == "follow":
                    file_path = data.get("path")
                    if file_path:
                        path = _ensure_within_root(Path(file_path))
                        reader = LogReader(str(path))

                        async for entry in reader.tail():
                            entry_dict = _entry_to_dict(entry, file_path)
                            tracker.track(entry)
                            await websocket.send_json(
                                {"type": "log_entry", "entry": entry_dict}
                            )

        except WebSocketDisconnect:
            pass
        finally:
            if websocket in websocket_clients:
                websocket_clients.remove(websocket)

    # Serve Vue frontend
    if DIST_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve the Vue SPA."""
            # Try to serve static file first
            file_path = DIST_DIR / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            # Fall back to index.html for SPA routing
            return FileResponse(DIST_DIR / "index.html")

    return app


# Create default app instance
app = create_app()
