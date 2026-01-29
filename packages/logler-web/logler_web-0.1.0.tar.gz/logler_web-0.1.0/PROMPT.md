# Logler Web - Session Context

## Project Overview

**logler-web** is a standalone web UI for the [logler](https://github.com/gabu-quest/logler) log viewer package.

- **Frontend**: Vue 3 + Naive UI + Phosphor Icons + Pinia
- **Backend**: FastAPI serving Vue SPA + API endpoints
- **Design System**: the-style Cyberpunk edition (from `/home/gabu/the-style/cyberpunk/`)
- **Dependency**: Requires `logler` package for log parsing

## Current State

### Completed
- Repository structure with Vue 3 + TypeScript + Vite
- FastAPI backend with all API endpoints
- Design system integration (tokens, naive-theme, icons)
- Pinia stores (ui, files, logs, threads)
- Layout components (Header, Sidebar, MainContent)
- Log viewer with virtualized rendering
- File browser with directory navigation + glob search
- Filtering UI (search, levels, thread, correlation)

### Pending Implementation
1. **Hierarchy View** (`src/components/hierarchy/`) - Tree visualization of thread/span relationships
2. **Waterfall View** (`src/components/waterfall/`) - Timeline visualization
3. **SQL Tab** (`src/components/sql/`) - Query interface using DuckDB

## Key Files

| File | Purpose |
|------|---------|
| `src/App.vue` | Root component with NConfigProvider |
| `src/views/Home.vue` | Main layout with tabs |
| `src/stores/*.ts` | Pinia state management |
| `src/api/client.ts` | API client for backend |
| `src/api/types.ts` | TypeScript interfaces |
| `backend/app.py` | FastAPI server |
| `src/design/tokens.ts` | Design tokens (colors, spacing, etc.) |

## Development Commands

```bash
# Frontend dev server (port 5173, proxies to backend)
pnpm dev

# Backend server (port 8080)
LOGLER_ROOT=/path/to/logs python -m backend.cli --reload

# Build for production
pnpm build
```

## Design System Rules

From the-style Cyberpunk edition:
- **No text glow** - Use color, weight, spacing for hierarchy
- **Glows for focus/active only** - Neon is emitted, not ambient
- **Dark mode default** - Design for dark first
- **Log level colors**:
  - TRACE: `#808080` (steel)
  - DEBUG: `#00e5ff` (neonCyan)
  - INFO: `#a8ff60` (acidGreen)
  - WARN: `#ffcc00` (amber)
  - ERROR/CRITICAL/FATAL: `#ff3b3b` (neonRed)

## Related Projects

- `/home/gabu/projects/logler` - Core logler package (Rust + Python)
- `/home/gabu/the-style/cyberpunk/` - Design system source
