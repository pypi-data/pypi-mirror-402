"""CLI entry point for logler-web."""

import click
import uvicorn


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def main(host: str, port: int, reload: bool):
    """Start the Logler Web server."""
    click.echo(f"Starting Logler Web on http://{host}:{port}")
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
