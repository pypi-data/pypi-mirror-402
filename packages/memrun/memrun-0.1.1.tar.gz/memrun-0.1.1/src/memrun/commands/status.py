"""Status command for memrun CLI."""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    service_name: str = typer.Argument(..., help="Service name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Check the status of a deployed service.

    Examples:

        # Check service status
        memrun status my-service

        # Get status as JSON
        memrun status my-service --json
    """
    if ctx.invoked_subcommand is not None:
        return

    import httpx

    url = api_url or os.environ.get("MEMRUN_API_URL", "http://localhost:8000")

    try:
        with httpx.Client(timeout=30.0) as client:
            # Get service info
            response = client.get(f"{url}/api/v1/services/{service_name}")
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                raise typer.Exit(1)
            response.raise_for_status()
            service = response.json()

            # Get deployments
            response = client.get(f"{url}/api/v1/services/{service_name}/deployments")
            response.raise_for_status()
            deployments = response.json()

            # Get recent requests
            response = client.get(
                f"{url}/api/v1/services/{service_name}/requests",
                params={"limit": 10},
            )
            response.raise_for_status()
            requests = response.json()

        if json_output:
            import json
            output = {
                "service": service,
                "deployments": deployments,
                "recent_requests": requests,
            }
            console.print_json(json.dumps(output))
            return

        # Display formatted status
        _display_service_status(service, deployments, requests)

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


def _display_service_status(
    service: dict,
    deployments: list,
    requests: list,
) -> None:
    """Display formatted service status."""
    # Service info panel
    status_color = _get_status_color(service["status"])

    info_lines = [
        f"[bold]Name:[/bold] {service['name']}",
        f"[bold]Status:[/bold] [{status_color}]{service['status']}[/{status_color}]",
        f"[bold]Workers:[/bold] {service['current_workers']}/{service['max_workers']}",
        f"[bold]Memory:[/bold] {service['memory']}",
        f"[bold]Disk:[/bold] {service['disk']}",
        f"[bold]Concurrency:[/bold] {service['concurrency']}",
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
    console.print()

    # Deployments table
    if deployments:
        table = Table(title="Recent Deployments")
        table.add_column("ID", style="dim")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Deployed")

        for dep in deployments[:5]:
            dep_status_color = _get_status_color(dep["status"])
            created = _format_datetime(dep.get("created_at"))
            deployed = _format_datetime(dep.get("deployed_at")) or "-"

            table.add_row(
                dep["id"][:8],
                f"[{dep_status_color}]{dep['status']}[/{dep_status_color}]",
                created,
                deployed,
            )

        console.print(table)
        console.print()

    # Recent requests table
    if requests:
        table = Table(title="Recent Requests")
        table.add_column("ID", style="dim")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Duration")

        for req in requests[:10]:
            req_status_color = _get_status_color(req["status"])
            created = _format_datetime(req.get("created_at"))

            # Calculate duration
            duration = "-"
            if req.get("started_at") and req.get("completed_at"):
                from datetime import datetime
                try:
                    start = datetime.fromisoformat(req["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(req["completed_at"].replace("Z", "+00:00"))
                    ms = int((end - start).total_seconds() * 1000)
                    duration = f"{ms}ms"
                except ValueError:
                    pass

            table.add_row(
                req["request_id"][:8],
                f"[{req_status_color}]{req['status']}[/{req_status_color}]",
                created,
                duration,
            )

        console.print(table)
    else:
        console.print("[dim]No recent requests[/dim]")


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
        "processing": "cyan",
        "failed": "red",
        "stopped": "dim",
        "timeout": "red",
    }
    return status_colors.get(status.lower(), "white")


def _format_datetime(dt_str: Optional[str]) -> str:
    """Format a datetime string for display."""
    if not dt_str:
        return "-"

    from datetime import datetime

    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return dt_str


@app.command("workers")
def list_workers(
    service_name: str = typer.Argument(..., help="Service name"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """List workers for a service."""
    import httpx

    url = api_url or os.environ.get("MEMRUN_API_URL", "http://localhost:8000")

    console.print("[yellow]Worker listing not yet implemented[/yellow]")
    console.print("Use 'memrun status <service>' to see worker count")
