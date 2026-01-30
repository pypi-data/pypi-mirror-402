"""Queue command for memrun CLI."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

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


def _format_duration(ms: float) -> str:
    """Format duration in milliseconds to human readable string."""
    if ms < 1000:
        return f"{int(ms)} ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f} s"
    else:
        return f"{ms / 60000:.1f} m"


def _format_timestamp(dt: datetime | str) -> str:
    """Format datetime to human readable string."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fetch_queue_stats(
    url: str,
    service_name: str,
    headers: dict[str, str],
) -> dict | None:
    """Fetch queue stats from the API."""
    try:
        response = httpx.get(
            f"{url}/api/v1/services/{service_name}/queue-stats",
            headers=headers,
            timeout=10.0,
        )
        if response.status_code == 404:
            console.print(f"[red]Service '{service_name}' not found[/red]")
            return None
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        return None
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        return None


def _render_queue_display(stats: dict, service_name: str) -> Panel:
    """Render the queue stats display."""
    queue_stats = stats["queue_stats"]
    sticky_distribution = stats["sticky_key_distribution"]
    worker_stats = stats["worker_stats"]

    # Build the display content
    lines = []

    # Queue Depth section
    lines.append("[bold]Queue Depth[/bold]")
    pending = queue_stats.get("pending", 0)
    queued = queue_stats.get("queued", 0)
    processing = queue_stats.get("processing", 0)
    backlog = pending + queued + processing

    lines.append(f"  Pending:     [yellow]{pending:>6}[/yellow]")
    lines.append(f"  Queued:      [yellow]{queued:>6}[/yellow]")
    lines.append(f"  Processing:  [cyan]{processing:>6}[/cyan]")
    lines.append("  " + "-" * 17)
    lines.append(f"  Backlog:     [bold]{backlog:>6}[/bold]")
    lines.append("")

    # Sticky Key Distribution section (if any)
    if sticky_distribution:
        lines.append(f"[bold]By Sticky Key[/bold] (top {len(sticky_distribution)})")

        sticky_table = Table(box=None, padding=(0, 1))
        sticky_table.add_column("Sticky Key", style="dim")
        sticky_table.add_column("Pending", justify="right")
        sticky_table.add_column("Queued", justify="right")
        sticky_table.add_column("Processing", justify="right")

        for item in sticky_distribution:
            key = item.get("sticky_key_value") or "(no sticky key)"
            if len(key) > 26:
                key = key[:23] + "..."
            sticky_table.add_row(
                key,
                str(item.get("pending", 0)),
                str(item.get("queued", 0)),
                str(item.get("processing", 0)),
            )

        lines.append("")

    # Workers section
    active_workers = len(worker_stats)
    lines.append(f"[bold]Workers[/bold] ({active_workers} active)")

    if worker_stats:
        worker_table = Table(box=None, padding=(0, 1))
        worker_table.add_column("Worker ID", style="dim")
        worker_table.add_column("Processed", justify="right")
        worker_table.add_column("Success", justify="right")
        worker_table.add_column("Active", justify="right")
        worker_table.add_column("Avg Latency", justify="right")

        for worker in worker_stats:
            worker_id = worker.get("worker_id", "")[:12]
            total = worker.get("total_requests", 0)
            success = worker.get("successful_requests", 0)
            active = worker.get("active_requests", 0)
            avg_ms = worker.get("avg_duration_ms", 0.0)

            worker_table.add_row(
                worker_id,
                str(total),
                str(success),
                str(active),
                _format_duration(avg_ms),
            )

        lines.append("")

    # Build final output
    output_parts = ["\n".join(lines)]

    if sticky_distribution:
        output_parts.append("")
        # Convert table to string for panel
        with console.capture() as capture:
            console.print(sticky_table)
        output_parts.append(capture.get().strip())

    if worker_stats:
        output_parts.append("")
        with console.capture() as capture:
            console.print(worker_table)
        output_parts.append(capture.get().strip())

    content = "\n".join(output_parts)

    return Panel(
        content,
        title=f"Queue Status: {service_name}",
        border_style="blue",
    )


def queue(
    service_name: str = typer.Argument(..., help="Service name"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch queue stats in real-time"),
    interval: int = typer.Option(2, "--interval", "-i", help="Refresh interval in seconds (with --watch)"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """View queue status and worker stats for a service.

    Examples:
        memrun queue my-service
        memrun queue my-service --watch
        memrun queue my-service --watch --interval 5 --local
    """
    # Load config
    memrunctl_config = _load_memrunctl_config(local=local)
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

    token = memrunctl_config.get("api_token")
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if watch:
        # Watch mode with live updates
        try:
            with Live(console=console, refresh_per_second=1) as live:
                while True:
                    stats = _fetch_queue_stats(url, service_name, headers)
                    if stats is None:
                        raise typer.Exit(1)

                    panel = _render_queue_display(stats, service_name)

                    # Add timestamp footer
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    footer = f"\n[dim]Last updated: {timestamp} (Ctrl+C to stop)[/dim]"
                    full_output = Panel(
                        panel.renderable + footer,
                        title=panel.title,
                        border_style=panel.border_style,
                    )
                    live.update(full_output)

                    time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[dim]Stopped watching.[/dim]")
    else:
        # Single fetch
        stats = _fetch_queue_stats(url, service_name, headers)
        if stats is None:
            raise typer.Exit(1)

        panel = _render_queue_display(stats, service_name)
        console.print(panel)
