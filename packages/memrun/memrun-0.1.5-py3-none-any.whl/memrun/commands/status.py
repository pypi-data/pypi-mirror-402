"""Status command for memrun CLI."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def _get_local_worker_count(service_name: str) -> int:
    """Get actual running worker count from Docker containers for a service."""
    import subprocess

    try:
        # Filter containers by service label
        result = subprocess.run(
            [
                "docker", "ps", "-q",
                "--filter", f"label=memrun.service={service_name}",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return 0

        output = result.stdout.strip()
        if not output:
            return 0
        return len(output.split("\n"))
    except Exception:
        return 0


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


def status(
    service_name: str = typer.Argument(..., help="Service name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Check the status of a deployed service.

    Examples:

        # Check local service status
        memrun status my-service --local

        # Check production service status
        memrun status my-service

        # Get status as JSON
        memrun status my-service --json
    """
    import httpx

    memrunctl_config = _load_memrunctl_config(local=local)
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

    try:
        with httpx.Client(timeout=30.0) as client:
            # Get service info
            response = client.get(f"{url}/api/v1/services/{service_name}")
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                raise typer.Exit(1)
            response.raise_for_status()
            service = response.json()

            # For local deployments, use actual Docker container count
            # but trust the API status (which checks worker readiness)
            if local:
                actual_workers = _get_local_worker_count(service_name)
                service["current_workers"] = actual_workers
                # Only override to "stopped" if no containers; otherwise trust API status
                if actual_workers == 0:
                    service["status"] = "stopped"

            # Get pending requests count from queue-stats (filters out stale requests)
            response = client.get(f"{url}/api/v1/services/{service_name}/queue-stats")
            response.raise_for_status()
            queue_stats = response.json().get("queue_stats", {})
            pending_count = queue_stats.get("pending", 0) + queue_stats.get("queued", 0)

        if json_output:
            import json
            output = {
                "service": service,
                "pending_requests": pending_count,
            }
            console.print_json(json.dumps(output))
            return

        # Display formatted status
        _display_service_status(service, pending_count)

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


def _display_service_status(
    service: dict,
    pending_requests: int,
) -> None:
    """Display formatted service status."""
    # Build status display showing ready/initializing breakdown
    ready = service.get("ready_workers", 0)
    initializing = service.get("initializing_workers", 0)

    status_parts = []
    if ready > 0:
        status_parts.append(f"[green]{ready} ready[/green]")
    if initializing > 0:
        status_parts.append(f"[cyan]{initializing} initializing[/cyan]")

    if status_parts:
        status_display = ", ".join(status_parts)
    elif service["status"] == "stopped":
        status_display = "[dim]stopped[/dim]"
    else:
        status_color = _get_status_color(service["status"])
        status_display = f"[{status_color}]{service['status']}[/{status_color}]"

    info_lines = [
        f"[bold]Name:[/bold] {service['name']}",
        f"[bold]Status:[/bold] {status_display}",
        f"[bold]Workers:[/bold] {service['current_workers']}/{service['max_workers']}",
        f"[bold]Memory:[/bold] {service['memory']}",
        f"[bold]Disk:[/bold] {service['disk']}",
        f"[bold]Concurrency:[/bold] {service['concurrency']}",
        f"[bold]Pending Requests:[/bold] {pending_requests}",
    ]

    if service.get("url"):
        info_lines.append(f"[bold]URL:[/bold] [cyan]{service['url']}[/cyan]")

    if service.get("sticky_key"):
        info_lines.append(f"[bold]Sticky Key:[/bold] {service['sticky_key']}")

    panel = Panel(
        "\n".join(info_lines),
        title="Service Info",
        border_style="blue",
    )
    console.print(panel)


def _get_status_color(status: str) -> str:
    """Get color for a status value."""
    status_colors = {
        "running": "green",
        "active": "green",
        "completed": "green",
        "pending": "yellow",
        "deploying": "yellow",
        "scaling": "yellow",
        "queued": "yellow",
        "initializing": "cyan",
        "processing": "cyan",
        "failed": "red",
        "stopped": "dim",
        "timeout": "red",
    }
    return status_colors.get(status.lower(), "white")
