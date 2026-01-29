"""
Command-line interface for logler-web.
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    """Run the logler-web server."""
    parser = argparse.ArgumentParser(
        description="Logler Web - Web interface for log viewing"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory for log files (default: current directory)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    # Set log root
    os.environ["LOGLER_ROOT"] = str(Path(args.root).expanduser().resolve())

    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn not installed.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting logler-web on http://{args.host}:{args.port}")
    print(f"Log root: {os.environ['LOGLER_ROOT']}")

    uvicorn.run(
        "logler_web:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
