"""Logs command for memrun CLI."""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def _load_memrunctl_config(local: bool = False) -> dict[str, str]:
    """Load config from ~/.memrunctl/config.toml."""
    config_file = Path.home() / ".memrunctl" / "config.toml"
    if not config_file.exists():
        return {}
    try:
        import tomli
        with open(config_file, "rb") as f:
            full_config = tomli.load(f)
    except Exception:
        return {}
    section = "local" if local else "production"
    if section in full_config:
        return full_config[section]
    if not local and "api_url" in full_config:
        return full_config
    return {}


def logs(
    service_name: str = typer.Argument(..., help="Service name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since (e.g., '5m', '1h')"),
    local: bool = typer.Option(False, "--local", "-l", help="Get logs from local Docker container (runs: docker logs memrun-worker-<service>)"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """View logs for a deployed service.

    Examples:

        # View recent logs (local)
        memrun logs my-service --local

        # Follow logs in real-time (local)
        memrun logs my-service --local --follow

        # View logs from production API
        memrun logs my-service

        # Show logs from last hour
        memrun logs my-service --since 1h
    """
    # For local deployments, use docker logs directly
    if local:
        _get_local_logs(service_name, follow=follow, tail=tail, since=since)
        return

    import httpx
    import time

    memrunctl_config = _load_memrunctl_config(local=local)
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

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
                _print_log_entry(req)

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
                                _print_log_entry(req)
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


def _print_log_entry(req: dict) -> None:
    """Print a log entry."""
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


def _get_local_logs(
    service_name: str,
    follow: bool = False,
    tail: int = 100,
    since: Optional[str] = None,
) -> None:
    """Get logs from local Docker containers for a service.

    Finds containers by label and shows combined logs.
    """
    # Find all containers for this service by label
    find_cmd = [
        "docker", "ps", "-a",
        "--filter", f"label=memrun.service={service_name}",
        "--format", "{{.Names}}"
    ]

    try:
        result = subprocess.run(find_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Error finding containers: {result.stderr}[/red]")
            raise typer.Exit(1)

        containers = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]

        if not containers:
            console.print(f"[red]No containers found for service '{service_name}'[/red]")
            console.print("[dim]Is the service deployed? Try: memrun deploy <handler.py> --local[/dim]")
            raise typer.Exit(1)

        console.print(f"[dim]Found {len(containers)} worker(s): {', '.join(containers)}[/dim]")
        console.print()

        if follow:
            # For follow mode with multiple containers, use docker compose-style output
            # We'll just follow the first container for simplicity
            if len(containers) > 1:
                console.print(f"[dim]Following logs from first container: {containers[0]}[/dim]")

            cmd = ["docker", "logs", "--follow", "--tail", str(tail)]
            if since:
                cmd.extend(["--since", since])
            cmd.append(containers[0])

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                for line in process.stdout:  # type: ignore
                    console.print(line, end="")
            except KeyboardInterrupt:
                process.terminate()
                console.print("\n[dim]Stopped following logs[/dim]")
        else:
            # Show logs from all containers
            for container in containers:
                if len(containers) > 1:
                    console.print(f"[cyan]═══ {container} ═══[/cyan]")

                cmd = ["docker", "logs", "--tail", str(tail)]
                if since:
                    cmd.extend(["--since", since])
                cmd.append(container)

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    console.print(f"[red]Error getting logs: {result.stderr}[/red]")
                else:
                    console.print(result.stdout, end="")
                    if result.stderr:
                        console.print(result.stderr, end="")

                if len(containers) > 1:
                    console.print()

    except FileNotFoundError:
        console.print("[red]Docker not found. Is Docker installed?[/red]")
        raise typer.Exit(1)
