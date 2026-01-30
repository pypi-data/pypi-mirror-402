"""Scale command for memrun CLI."""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback(invoke_without_command=True)
def scale(
    ctx: typer.Context,
    service_name: str = typer.Argument(..., help="Service name"),
    workers: int = typer.Option(..., "--workers", "-w", help="Target number of workers"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for scaling to complete"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Scale a service to a specific number of workers.

    Examples:

        # Scale to 5 workers
        memrun scale my-service --workers 5

        # Scale to zero (stop all workers)
        memrun scale my-service --workers 0

        # Scale without waiting
        memrun scale my-service --workers 10 --no-wait
    """
    if ctx.invoked_subcommand is not None:
        return

    import httpx
    import time

    url = api_url or os.environ.get("MEMRUN_API_URL", "http://localhost:8000")

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


@app.command("auto")
def auto_scale(
    service_name: str = typer.Argument(..., help="Service name"),
    min_workers: int = typer.Option(0, "--min", help="Minimum workers"),
    max_workers: int = typer.Option(10, "--max", help="Maximum workers"),
    target_queue_depth: int = typer.Option(100, "--target-queue", help="Target queue depth per worker"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
) -> None:
    """Configure autoscaling for a service.

    Examples:

        # Enable autoscaling with defaults
        memrun scale my-service auto

        # Configure autoscaling limits
        memrun scale my-service auto --min 2 --max 50

        # Set target queue depth
        memrun scale my-service auto --target-queue 50
    """
    import httpx

    url = api_url or os.environ.get("MEMRUN_API_URL", "http://localhost:8000")

    try:
        with httpx.Client(timeout=30.0) as client:
            # Update service configuration
            response = client.patch(
                f"{url}/api/v1/services/{service_name}",
                json={
                    "min_workers": min_workers,
                    "max_workers": max_workers,
                },
            )
            if response.status_code == 404:
                console.print(f"[red]Service '{service_name}' not found[/red]")
                raise typer.Exit(1)
            response.raise_for_status()

        console.print(f"[green]Configured autoscaling for '{service_name}'[/green]")
        console.print(f"  Min workers: {min_workers}")
        console.print(f"  Max workers: {max_workers}")
        console.print(f"  Target queue depth: {target_queue_depth}/worker")

    except httpx.ConnectError:
        console.print(f"[red]Could not connect to API at {url}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]API error: {e.response.status_code}[/red]")
        raise typer.Exit(1)
