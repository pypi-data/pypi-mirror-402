"""Deploy command for memrun CLI."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def _load_memrunctl_config(local: bool = False) -> dict[str, str]:
    """Load config from ~/.memrunctl/config.toml.

    Args:
        local: If True, load from [local] section, otherwise [production].

    Returns:
        Config dict with api_url and api_token.
    """
    config_dir = Path.home() / ".memrunctl"
    config_file = config_dir / "config.toml"

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


def _run_local_server(
    handler_path: Path,
    handler_function: str,
    service_name: str,
    port: int,
) -> None:
    """Run a local development server for the handler.

    Args:
        handler_path: Path to the handler Python file.
        handler_function: Name of the handler function.
        service_name: Name of the service.
        port: Port to run on.
    """
    import asyncio
    import importlib.util
    import sys

    # Load the handler module dynamically
    spec = importlib.util.spec_from_file_location("handler", handler_path)
    if spec is None or spec.loader is None:
        console.print(f"[red]Could not load handler from {handler_path}[/red]")
        raise typer.Exit(1)

    module = importlib.util.module_from_spec(spec)
    sys.modules["handler"] = module

    # Add handler directory to path for imports
    handler_dir = str(handler_path.parent)
    if handler_dir not in sys.path:
        sys.path.insert(0, handler_dir)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        console.print(f"[red]Error loading handler: {e}[/red]")
        raise typer.Exit(1)

    # Get the handler function
    handler_fn = getattr(module, handler_function, None)
    if handler_fn is None:
        console.print(f"[red]Handler function '{handler_function}' not found[/red]")
        raise typer.Exit(1)

    # Create a minimal MemoryService-like object for the local server
    from memrun.service import MemoryService

    # Check if there's a MemoryService instance in the module
    svc = None
    for name, obj in vars(module).items():
        if isinstance(obj, MemoryService):
            svc = obj
            break

    if svc is None:
        # Create a minimal service for serving
        svc = MemoryService(name=service_name)
        svc._handler = handler_fn

    local_domain = f"{service_name}.memrun.local"

    console.print()
    console.print(Panel.fit(
        f"[bold green]Local server starting![/bold green]\n\n"
        f"[bold]Service:[/bold] {service_name}\n"
        f"[bold]Handler:[/bold] {handler_function}\n"
        f"[bold]Port:[/bold] {port}\n\n"
        f"[bold]Local URL:[/bold]\n"
        f"  [cyan]http://{local_domain}:{port}[/cyan]\n"
        f"  [cyan]http://localhost:{port}[/cyan]\n\n"
        f"[dim]To use {local_domain}, add to /etc/hosts:[/dim]\n"
        f"[dim]  127.0.0.1 {local_domain}[/dim]",
        title="memrun deploy --serve",
        border_style="green",
    ))

    console.print()
    console.print("[bold]Invoke with:[/bold]")
    console.print(f"  curl -X POST http://localhost:{port}/invoke \\")
    console.print("    -H \"Content-Type: application/json\" \\")
    console.print("    -d '{\"payload\": {\"key\": \"value\"}}'")
    console.print()
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    # Run the local server
    from memrun.local import run_local_server

    try:
        asyncio.run(run_local_server(svc, host="0.0.0.0", port=port))
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Server stopped[/yellow]")


def deploy(
    handler_file: str = typer.Argument(
        ...,
        help="Python file containing @svc.handler decorated function",
    ),
    name: str = typer.Option(..., "--name", "-n", help="Service name"),
    image: Optional[str] = typer.Option(None, "--image", "-i", help="Base Docker image for workers (required for remote deploy)"),
    local: bool = typer.Option(False, "--local", "-l", help="Target local API server instead of production"),
    serve: bool = typer.Option(False, "--serve", "-s", help="Run as local development server instead of deploying"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for local server (--serve only)"),
    memory: str = typer.Option("4Gi", "--memory", "-m", help="Memory allocation"),
    disk: str = typer.Option("100Gi", "--disk", "-d", help="Disk allocation"),
    max_workers: int = typer.Option(10, "--max-workers", help="Maximum workers"),
    concurrency: int = typer.Option(16, "--concurrency", "-c", help="Concurrent requests per worker"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="MEMRUN_API_URL"),
    api_token: Optional[str] = typer.Option(None, "--token", "-t", envvar="MEMRUN_API_TOKEN", help="API authentication token"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for deployment"),
) -> None:
    """Deploy a service to the memrun platform.

    The handler file must contain exactly one @svc.handler decorated function.

    Examples:

        # Run as local development server
        memrun deploy handler.py --name my-service --serve

        # Deploy to production API server
        memrun deploy handler.py --name my-service --image python:3.12-slim

        # Deploy to local API server
        memrun deploy handler.py --name my-service --image python:3.12-slim --local

        # Deploy with custom resources
        memrun deploy ml_handler.py --name ml-service --image python:3.12-slim --memory 32Gi
    """
    from memrun.handler_extractor import validate_handler_file

    # Resolve handler file path
    handler_path = Path(handler_file).resolve()

    # Validate handler file
    console.print(f"Validating handler file [cyan]{handler_file}[/cyan]...")
    try:
        file_info = validate_handler_file(handler_path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)
    except SyntaxError as e:
        console.print(f"[red]Syntax error: {e}[/red]")
        raise typer.Exit(1)

    handler_info = file_info.handler
    init_handler_info = file_info.init_handler

    console.print(f"  Found handler: [green]{handler_info.function_name}[/green]")
    if handler_info.sticky_key:
        console.print(f"  Sticky key: [cyan]{handler_info.sticky_key}[/cyan]")
    if init_handler_info:
        console.print(f"  Found init handler: [green]{init_handler_info.function_name}[/green]")

    # Handle serve mode (local development server)
    if serve:
        _run_local_server(
            handler_path=handler_path,
            handler_function=handler_info.function_name,
            service_name=name,
            port=port,
        )
        return

    # Remote deployment requires image
    if not image:
        console.print("[red]Error: --image is required for remote deployment[/red]")
        console.print("Use --serve for local development, or specify --image for remote deployment.")
        raise typer.Exit(1)

    import httpx

    from memrun.handler_builder import build_handler_package

    # Load config from ~/.memrunctl/config.toml as fallback
    memrunctl_config = _load_memrunctl_config(local=local)

    # Resolve API URL: CLI option > env var > memrunctl config > default
    url = (
        api_url
        or os.environ.get("MEMRUN_API_URL")
        or memrunctl_config.get("api_url")
        or "http://localhost:8000"
    )

    # Resolve token: CLI option > env var > memrunctl config
    token = (
        api_token
        or os.environ.get("MEMRUN_API_TOKEN")
        or memrunctl_config.get("api_token")
    )

    # Build headers with optional auth token
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    env_label = "local" if local else "production"
    console.print(f"Deploying service [cyan]{name}[/cyan] to [cyan]{env_label}[/cyan] ({url})...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        try:
            # Build deployment package
            task = progress.add_task("Building deployment package...", total=None)

            service_config = {
                "memory": memory,
                "disk": disk,
                "max_workers": max_workers,
                "concurrency": concurrency,
            }

            # Add sticky_key to service config if present
            if handler_info.sticky_key:
                service_config["sticky_key"] = handler_info.sticky_key

            package_bytes = build_handler_package(
                handler_file=handler_path,
                service_name=name,
                handler_info=handler_info,
                image=image,
                service_config=service_config,
                init_handler_info=init_handler_info,
            )
            progress.update(task, description=f"Package built ({len(package_bytes)} bytes)")

            # Create or update service
            progress.update(task, description="Creating service...")

            full_service_config = {
                "name": name,
                "image": image,
                **service_config,
            }

            with httpx.Client(timeout=30.0, headers=headers) as client:
                response = client.put(
                    f"{url}/api/v1/services/{name}",
                    json=full_service_config,
                )
                response.raise_for_status()

            progress.update(task, description="Service created")

            # Create deployment with package upload
            progress.update(task, description="Uploading deployment package...")
            with httpx.Client(timeout=300.0, headers=headers) as client:
                # Use multipart form data for package upload
                files = {
                    "package": ("package.tar.gz", package_bytes, "application/gzip"),
                }
                response = client.post(
                    f"{url}/api/v1/services/{name}/deployments",
                    files=files,
                )
                response.raise_for_status()
                deployment = response.json()

            deployment_id = deployment["id"]

            # Wait for deployment
            if wait:
                progress.update(task, description="Waiting for deployment...")
                import time

                while True:
                    with httpx.Client(headers=headers) as client:
                        response = client.get(
                            f"{url}/api/v1/services/{name}/deployments/{deployment_id}"
                        )
                        response.raise_for_status()
                        status_data = response.json()

                    if status_data["status"] == "active":
                        progress.update(task, description="Deployment complete!")
                        break
                    elif status_data["status"] == "failed":
                        progress.update(task, description="Deployment failed")
                        console.print(f"[red]Deployment failed: {status_data.get('error_message')}[/red]")
                        raise typer.Exit(1)

                    time.sleep(2)

            progress.remove_task(task)

            # Fetch service to get URL
            with httpx.Client(timeout=30.0, headers=headers) as client:
                response = client.get(f"{url}/api/v1/services/{name}")
                response.raise_for_status()
                service_data = response.json()

        except httpx.ConnectError:
            console.print(f"[red]Could not connect to API at {url}[/red]")
            raise typer.Exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"[red]API error: {e.response.status_code}[/red]")
            if e.response.text:
                console.print(e.response.text)
            raise typer.Exit(1)

    console.print()
    console.print(f"[green]Successfully deployed '{name}' to {env_label}[/green]")

    service_url = service_data.get("url")
    if service_url:
        console.print()
        console.print("[bold]Service URL:[/bold]")
        console.print(f"  [cyan]{service_url}[/cyan]")

    console.print()
    console.print("[bold]Invoke via CLI:[/bold]")
    local_flag = " --local" if local else ""
    console.print(f"  memrun invoke {name} --payload '{{\"key\": \"value\"}}'{local_flag}")

    if service_url:
        console.print()
        console.print("[bold]Invoke via HTTP:[/bold]")
        console.print("  # Async (returns request ID):")
        console.print(f"  curl -X POST {service_url} \\")
        console.print("    -H \"Content-Type: application/json\" \\")
        console.print("    -d '{\"key\": \"value\"}'")
        console.print()
        console.print("  # Sync (waits for result):")
        console.print(f"  curl -X POST \"{service_url}?sync=true\" \\")
        console.print("    -H \"Content-Type: application/json\" \\")
        console.print("    -d '{\"key\": \"value\"}'")

    console.print()
    console.print("[bold]Check status:[/bold]")
    console.print(f"  memrun status {name}{local_flag}")
