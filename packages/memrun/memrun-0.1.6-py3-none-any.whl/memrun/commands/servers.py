"""Server management commands for memrun CLI."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
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


def servers(
    service_name: str = typer.Argument(..., help="Service name"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
    api_token: Optional[str] = typer.Option(None, "--token", "-t", envvar="MEMRUN_API_TOKEN", help="API authentication token"),
) -> None:
    """List all worker servers for a service.

    Shows server name, IP address, status, and worker ID for each worker.

    Examples:

        # List production servers
        memrun servers my-service

        # List local containers
        memrun servers my-service --local
    """
    import httpx

    memrunctl_config = _load_memrunctl_config(local=local)
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

    token = (
        api_token
        or os.environ.get("MEMRUN_API_TOKEN")
        or memrunctl_config.get("api_token")
    )

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    env_label = "local" if local else "production"

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{url}/api/v1/services/{service_name}/workers")
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                raise typer.Exit(1)
            response.raise_for_status()
            workers = response.json()

        if not workers:
            console.print(f"[dim]No workers found for '{service_name}' on {env_label}[/dim]")
            return

        table = Table(title=f"Workers for '{service_name}' ({env_label})")
        table.add_column("Name", style="cyan")
        table.add_column("IP", style="green")
        table.add_column("Status")
        table.add_column("Worker ID", style="dim")

        for w in workers:
            status = w.get("status", "unknown")
            status_color = "green" if status in ("running", "active") else "yellow" if status == "initializing" else "red"

            table.add_row(
                w.get("name", ""),
                w.get("ip") or "-",
                f"[{status_color}]{status}[/{status_color}]",
                w.get("worker_id", "")[:8] if w.get("worker_id") else "",
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(workers)} worker(s)[/dim]")

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        if e.response.text:
            console.print(e.response.text)
        raise typer.Exit(1)


def delete_server(
    service_name: str = typer.Argument(..., help="Service name"),
    identifier: str = typer.Argument(..., help="Server name, IP address, or worker ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
    api_token: Optional[str] = typer.Option(None, "--token", "-t", envvar="MEMRUN_API_TOKEN", help="API authentication token"),
) -> None:
    """Delete a specific worker server by name, IP, or worker ID.

    This is useful for scaling down by removing a specific server rather than
    letting the system choose which server to remove.

    Examples:

        # Delete by server name
        memrun delete-server my-service memrun-my-service-abc12345

        # Delete by IP address
        memrun delete-server my-service 168.119.123.456

        # Delete by worker ID (or prefix)
        memrun delete-server my-service abc12345

        # Delete local container
        memrun delete-server my-service my-service-abc1-worker --local

        # Skip confirmation
        memrun delete-server my-service memrun-my-service-abc12345 --force
    """
    import httpx

    memrunctl_config = _load_memrunctl_config(local=local)
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

    token = (
        api_token
        or os.environ.get("MEMRUN_API_TOKEN")
        or memrunctl_config.get("api_token")
    )

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    env_label = "local" if local else "production"

    if not force:
        confirm = typer.confirm(
            f"Delete worker '{identifier}' from service '{service_name}' on {env_label}?"
        )
        if not confirm:
            raise typer.Abort()

    try:
        with httpx.Client(timeout=60.0, headers=headers) as client:
            response = client.delete(
                f"{url}/api/v1/services/{service_name}/workers/{identifier}"
            )

            if response.status_code == 404:
                error_detail = response.json().get("detail", "Not found")
                console.print(f"[red]{error_detail}[/red]")
                raise typer.Exit(1)

            response.raise_for_status()
            result = response.json()

        worker_name = result.get("worker_name", identifier)
        worker_ip = result.get("worker_ip")

        if worker_ip:
            console.print(f"[green]Deleted worker '{worker_name}' ({worker_ip}) from {env_label}[/green]")
        else:
            console.print(f"[green]Deleted worker '{worker_name}' from {env_label}[/green]")

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        if e.response.text:
            console.print(e.response.text)
        raise typer.Exit(1)
