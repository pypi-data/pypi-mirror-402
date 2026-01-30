"""memrun CLI - Serverless data platform CLI for Hetzner Cloud."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from memrun.commands import deploy as deploy_module
from memrun.commands import logs, scale, status

app = typer.Typer(
    name="memrun",
    help="Serverless data platform CLI for Hetzner Cloud",
    no_args_is_help=True,
)

console = Console()

# Register deploy as a direct command
app.command(name="deploy")(deploy_module.deploy)

# Add other command groups
app.add_typer(logs.app, name="logs", help="View service logs")
app.add_typer(scale.app, name="scale", help="Scale a service")
app.add_typer(status.app, name="status", help="Check service status")


@app.command()
def version() -> None:
    """Show the memrun version."""
    from memrun import __version__

    console.print(f"memrun version {__version__}")


def _load_memrunctl_config(local: bool = False) -> dict[str, str]:
    """Load config from ~/.memrunctl/config.toml.

    Args:
        local: If True, load from [local] section, otherwise [production].

    Returns:
        Config dict with api_url and api_token.
    """
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

    # Check for new format with environment sections
    if section in full_config:
        return full_config[section]

    # Backwards compatibility: if no sections, treat root as production
    if not local and "api_url" in full_config:
        return full_config

    return {}


@app.command("list")
def list_services(
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """List all deployed services."""
    import os
    import httpx

    # Load config from ~/.memrunctl/config.toml
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

    env_label = "local" if local else "production"

    try:
        response = httpx.get(f"{url}/api/v1/services", headers=headers)
        response.raise_for_status()
        services = response.json()

        if not services:
            console.print(f"[dim]No services deployed on {env_label}[/dim]")
            return

        table = Table(title=f"Services ({env_label})")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Workers")
        table.add_column("Memory")
        table.add_column("Disk")

        for svc in services:
            status_style = "green" if svc["status"] == "running" else "yellow"
            table.add_row(
                svc["name"],
                f"[{status_style}]{svc['status']}[/{status_style}]",
                f"{svc['current_workers']}/{svc['max_workers']}",
                svc["memory"],
                svc["disk"],
            )

        console.print(table)

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


@app.command()
def invoke(
    service_name: str = typer.Argument(..., help="Service name"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload"),
    sync: bool = typer.Option(True, "--sync/--async", help="Wait for response"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Invoke a deployed service."""
    import json
    import os
    import httpx

    # Load config from ~/.memrunctl/config.toml
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

    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON payload[/red]")
        raise typer.Exit(1)

    try:
        response = httpx.post(
            f"{url}/api/v1/services/{service_name}/invoke",
            json={"payload": payload_dict, "sync": sync},
            timeout=300.0,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") == "completed":
            console.print("[green]Request completed[/green]")
            if result.get("result"):
                console.print_json(data=result["result"])
        elif result.get("status") == "failed":
            console.print(f"[red]Request failed: {result.get('error')}[/red]")
        else:
            console.print(f"Request ID: {result.get('request_id')}")
            console.print(f"Status: {result.get('status')}")

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        if e.response.text:
            console.print(e.response.text)
        raise typer.Exit(1)


@app.command()
def delete(
    service_name: str = typer.Argument(..., help="Service name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Delete a deployed service."""
    import os
    import httpx

    # Load config from ~/.memrunctl/config.toml
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

    env_label = "local" if local else "production"

    if not force:
        confirm = typer.confirm(f"Delete service '{service_name}' from {env_label}?")
        if not confirm:
            raise typer.Abort()

    try:
        response = httpx.delete(f"{url}/api/v1/services/{service_name}", headers=headers)
        response.raise_for_status()

        console.print(f"[green]Deleted service '{service_name}' from {env_label}[/green]")

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[yellow]Service '{service_name}' not found on {env_label}[/yellow]")
        else:
            console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
