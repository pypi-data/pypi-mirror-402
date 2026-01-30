"""Scale command for memrun CLI."""

import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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


def scale(
    service_name: str = typer.Argument(..., help="Service name"),
    workers: int = typer.Option(..., "--workers", "-w", help="Target number of workers"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for scaling to complete"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Scale a service to a specific number of workers.

    For local deployments, this stops (--workers 0) or restarts (--workers > 0) the container.
    Use 'memrun deploy' to start a stopped local service.

    Examples:

        # Scale to 5 workers (production)
        memrun scale my-service --workers 5

        # Stop local worker (scale to 0)
        memrun scale my-service --workers 0 --local

        # Scale without waiting
        memrun scale my-service --workers 10 --no-wait
    """
    # For local deployments, handle via Docker directly
    if local:
        _scale_local(service_name, workers)
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        try:
            task = progress.add_task("Getting service info...", total=None)

            with httpx.Client(timeout=30.0) as client:
                # Get current service info
                response = client.get(f"{url}/api/v1/services/{service_name}")
                if response.status_code == 404:
                    progress.remove_task(task)
                    console.print(f"[red]Service '{service_name}' not found[/red]")
                    raise typer.Exit(1)
                response.raise_for_status()
                service = response.json()

                current_workers = service["current_workers"]
                max_workers = service["max_workers"]

                # Validate target
                if workers > max_workers:
                    progress.remove_task(task)
                    console.print(
                        f"[red]Cannot scale beyond max_workers ({max_workers}). "
                        f"Update max_workers first.[/red]"
                    )
                    raise typer.Exit(1)

                if workers == current_workers:
                    progress.remove_task(task)
                    console.print(f"[yellow]Already at {workers} workers[/yellow]")
                    return

                # Execute scaling
                direction = "up" if workers > current_workers else "down"
                progress.update(
                    task,
                    description=f"Scaling {direction} from {current_workers} to {workers} workers...",
                )

                response = client.post(
                    f"{url}/api/v1/services/{service_name}/scale",
                    json={"workers": workers},
                )
                response.raise_for_status()

                if wait:
                    # Wait for scaling to complete
                    while True:
                        time.sleep(2)
                        response = client.get(f"{url}/api/v1/services/{service_name}")
                        response.raise_for_status()
                        service = response.json()

                        if service["status"] == "running" and service["current_workers"] == workers:
                            break
                        elif service["status"] == "failed":
                            progress.remove_task(task)
                            console.print("[red]Scaling failed[/red]")
                            raise typer.Exit(1)

                        progress.update(
                            task,
                            description=f"Scaling... ({service['current_workers']}/{workers} workers)",
                        )

            progress.remove_task(task)

        except httpx.ConnectError:
            console.print(f"[red]Could not connect to API at {url}[/red]")
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"[red]API error: {e.response.status_code}[/red]")
            if e.response.text:
                console.print(e.response.text)
            raise typer.Exit(1)

    console.print(f"[green]Scaled '{service_name}' to {workers} workers[/green]")


def _scale_local(service_name: str, workers: int) -> None:
    """Scale a local service via the local API server.

    Uses the API to handle scaling which manages Docker containers.
    """
    import httpx
    import time

    url = "http://localhost:8000"

    # Load config to get API token
    memrunctl_config = _load_memrunctl_config(local=True)
    headers = {}
    token = memrunctl_config.get("api_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Get current worker count from Docker
    result = subprocess.run(
        ["docker", "ps", "-q", "--filter", f"label=memrun.service={service_name}"],
        capture_output=True,
        text=True,
    )
    current_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    if workers == current_count:
        console.print(f"[yellow]Already at {workers} workers[/yellow]")
        return

    direction = "up" if workers > current_count else "down"
    console.print(f"Scaling {direction} from {current_count} to {workers} workers...")

    try:
        with httpx.Client(timeout=60.0, headers=headers) as client:
            # Check service exists
            response = client.get(f"{url}/api/v1/services/{service_name}")
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                console.print("[dim]Deploy the service first: memrun deploy <handler.py> --local[/dim]")
                raise typer.Exit(1)
            response.raise_for_status()

            # Execute scaling via API
            response = client.post(
                f"{url}/api/v1/services/{service_name}/scale",
                json={"workers": workers},
            )
            response.raise_for_status()

            # Wait for scaling to complete
            for _ in range(30):  # 30 second timeout
                time.sleep(1)
                result = subprocess.run(
                    ["docker", "ps", "-q", "--filter", f"label=memrun.service={service_name}"],
                    capture_output=True,
                    text=True,
                )
                actual = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
                if actual == workers:
                    break

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to local API at {url}[/red]")
        console.print("[dim]Make sure the local API is running: docker-compose up -d mem-api[/dim]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        if e.response.text:
            console.print(e.response.text)
        raise typer.Exit(1)

    # Verify final count
    result = subprocess.run(
        ["docker", "ps", "-q", "--filter", f"label=memrun.service={service_name}"],
        capture_output=True,
        text=True,
    )
    final_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    console.print(f"[green]Scaled '{service_name}' to {final_count} workers[/green]")
