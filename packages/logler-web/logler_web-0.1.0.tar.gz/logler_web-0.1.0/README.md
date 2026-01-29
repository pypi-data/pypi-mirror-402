# Logler Web

Web UI for [Logler](https://github.com/gabu-quest/logler) - Beautiful log viewer with Vue3 + Naive-UI.

## Features

- **Log Viewer** - Virtualized rendering with color-coded log levels
- **File Browser** - Navigate directories and search with glob patterns
- **Multi-File Interleaving** - Open multiple files with merged timeline
- **Filtering** - Search, level, thread, and correlation ID filters
- **Live Following** - Real-time log updates via WebSocket
- **Hierarchy View** - Thread/span tree visualization
- **Waterfall View** - Timeline visualization
- **SQL Queries** - Query logs with SQL using DuckDB

## Installation

```bash
pip install logler-web
```

## Usage

```bash
# Start the web server
logler-web --port 8080

# With custom log root directory
LOGLER_ROOT=/var/log logler-web
```

## Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- pnpm (recommended) or npm

### Setup

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Install Node dependencies
pnpm install

# Start development servers
pnpm dev          # Vue dev server (port 5173)
logler-web --reload  # FastAPI server (port 8080)
```

### Build

```bash
# Build Vue frontend
pnpm build

# The built files go to dist/ and are served by FastAPI
```

## Tech Stack

- **Frontend**: Vue 3, Naive UI, Phosphor Icons, Pinia
- **Backend**: FastAPI, Uvicorn
- **Design**: [the-style](https://github.com/gabu-quest/the-style) Cyberpunk edition
- **Log Processing**: [logler](https://github.com/gabu-quest/logler) package

## License

MIT
