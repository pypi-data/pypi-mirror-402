# Sample Log Files

This directory contains sample log files for testing and demonstration purposes.

## Files

### sample-app.log

Basic application log file with mixed log levels (~50 lines).

- **Format**: Standard log format `TIMESTAMP [LEVEL] message`
- **Levels**: DEBUG, INFO, WARN, ERROR
- **Use case**: Testing basic log viewing, level filtering, and search

### sample-json.log

JSON-structured log file with correlation IDs and service metadata (~30 lines).

- **Format**: JSON lines (one JSON object per line)
- **Fields**: timestamp, level, message, service_name, correlation_id
- **Use case**: Testing JSON parsing, correlation ID filtering, service filtering

### sample-threaded.log

Multi-threaded application log with thread IDs (~110 lines).

- **Format**: Standard log format with thread ID `TIMESTAMP [LEVEL] [thread_id] message`
- **Thread IDs**: main, worker-1, worker-2, worker-3, worker-4, http-handler
- **Use case**: Testing thread filtering, hierarchy building, waterfall view

## Usage

### Manual Testing

1. Start the backend: `uv run uvicorn backend.app:app --reload`
2. Start the frontend: `pnpm dev`
3. Open the file browser and navigate to the `examples/` directory
4. Select one or more log files to view

### E2E Testing

The E2E tests use these files as fixtures. The backend must be running with access to this directory for E2E tests to pass.

### Unit Testing

Test factories in `src/test/factories/` generate data structures similar to what these log files would produce when parsed.
