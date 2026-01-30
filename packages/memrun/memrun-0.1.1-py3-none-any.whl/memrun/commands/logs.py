"""Logs command for memrun CLI."""

import os
from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback(invoke_without_command=True)
def logs(
    ctx: typer.Context,
    service_name: str = typer.Argument(..., help="Service name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    worker: Optional[str] = typer.Option(None, "--worker", "-w", help="Filter by worker ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since (e.g., '5m', '1h')"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """View logs for a deployed service.

    Examples:

        # View recent logs
        memrun logs my-service

        # Follow logs in real-time
        memrun logs my-service --follow

        # Show logs from last hour
        memrun logs my-service --since 1h

        # Filter by worker
        memrun logs my-service --worker abc123
    """
    if ctx.invoked_subcommand is not None:
        return

    import httpx
    import time
    from datetime import datetime, timedelta

    url = api_url or os.environ.get("MEMRUN_API_URL", "http://localhost:8000")

    # Parse since parameter
    since_time = None
    if since:
        since_time = _parse_duration(since)

    try:
        with httpx.Client(timeout=30.0) as client:
            # Check if service exists
            response = client.get(f"{url}/api/v1/services/{service_name}")
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                raise typer.Exit(1)
            response.raise_for_status()

            # For now, we'll show request logs as a proxy for service logs
            # In production, this would stream actual container logs

            params = {"limit": tail}
            if since_time:
                params["since"] = since_time.isoformat()

            response = client.get(
                f"{url}/api/v1/services/{service_name}/requests",
                params=params,
            )
            response.raise_for_status()
            requests = response.json()

            if not requests:
                console.print("[dim]No logs available[/dim]")
                if follow:
                    console.print("[dim]Waiting for new requests...[/dim]")

            # Display logs
            for req in reversed(requests):  # Show oldest first
                _print_log_entry(req, worker)

            if follow:
                # Poll for new requests
                last_id = requests[0]["request_id"] if requests else None

                while True:
                    time.sleep(2)
                    response = client.get(
                        f"{url}/api/v1/services/{service_name}/requests",
                        params={"limit": 10},
                    )
                    if response.status_code == 200:
                        new_requests = response.json()
                        for req in reversed(new_requests):
                            if last_id is None or req["request_id"] != last_id:
                                _print_log_entry(req, worker)
                        if new_requests:
                            last_id = new_requests[0]["request_id"]

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped following logs[/dim]")


def _print_log_entry(req: dict, worker_filter: Optional[str] = None) -> None:
    """Print a log entry."""
    from datetime import datetime

    # Filter by worker if specified
    if worker_filter and req.get("worker_id") != worker_filter:
        return

    timestamp = req.get("created_at", "")
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    request_id = req.get("request_id", "")[:8]
    status = req.get("status", "unknown")

    # Color based on status
    if status == "completed":
        status_color = "green"
    elif status == "failed":
        status_color = "red"
    elif status == "processing":
        status_color = "yellow"
    else:
        status_color = "dim"

    # Build log line
    console.print(
        f"[dim]{timestamp}[/dim] "
        f"[cyan]{request_id}[/cyan] "
        f"[{status_color}]{status}[/{status_color}]",
        end="",
    )

    # Add error message if failed
    if status == "failed" and req.get("error"):
        error = req["error"].split("\n")[0][:100]
        console.print(f" [red]{error}[/red]", end="")

    console.print()


def _parse_duration(duration: str) -> Optional[datetime]:
    """Parse a duration string like '5m' or '1h' into a datetime."""
    if not duration:
        return None

    unit = duration[-1].lower()
    try:
        value = int(duration[:-1])
    except ValueError:
        return None

    now = datetime.utcnow()

    if unit == "s":
        return now - timedelta(seconds=value)
    elif unit == "m":
        return now - timedelta(minutes=value)
    elif unit == "h":
        return now - timedelta(hours=value)
    elif unit == "d":
        return now - timedelta(days=value)

    return None
