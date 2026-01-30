"""Deployment logic for memrun services."""

from __future__ import annotations

import json
import os
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from memrun.service import MemoryService


def get_api_url() -> str:
    """Get the API URL from environment or default."""
    return os.environ.get("MEMRUN_API_URL", "http://localhost:8000")


async def deploy_service(
    service: MemoryService,
    api_url: str | None = None,
    wait: bool = True,
) -> dict[str, Any]:
    """Deploy a service to the memrun platform.

    Args:
        service: The MemoryService to deploy.
        api_url: Override API URL.
        wait: Wait for deployment to complete.

    Returns:
        Deployment information.
    """
    api_url = api_url or get_api_url()

    # Build deployment package
    package_data = build_deployment_package(service)

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create or update service
        service_data = service.to_dict()

        response = await client.put(
            f"{api_url}/api/v1/services/{service.config.name}",
            json=service_data,
        )
        response.raise_for_status()
        service_info = response.json()

        # Upload deployment package
        files = {"package": ("package.tar.gz", package_data, "application/gzip")}
        response = await client.post(
            f"{api_url}/api/v1/services/{service.config.name}/deployments",
            files=files,
        )
        response.raise_for_status()
        deployment_info = response.json()

        if wait:
            # Poll for deployment completion
            deployment_id = deployment_info["id"]
            while True:
                response = await client.get(
                    f"{api_url}/api/v1/services/{service.config.name}/deployments/{deployment_id}"
                )
                response.raise_for_status()
                status = response.json()

                if status["status"] in ("active", "failed"):
                    deployment_info = status
                    break

                import asyncio
                await asyncio.sleep(2)

        return {
            "service": service_info,
            "deployment": deployment_info,
            "url": f"{api_url}/invoke/{service.config.name}",
        }


def build_deployment_package(service: MemoryService) -> bytes:
    """Build a deployment package (tarball) for the service.

    The package includes:
    - The handler source file
    - A manifest.json with service configuration
    - Any local dependencies

    Args:
        service: The service to package.

    Returns:
        Tarball bytes.
    """
    buffer = BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        # Add manifest
        manifest = {
            "name": service.config.name,
            "config": service.config.model_dump(),
            "handler_config": (
                {
                    "sticky_key": service._handler_config.sticky_key,
                    "timeout_seconds": service._handler_config.timeout_seconds,
                }
                if service._handler_config
                else None
            ),
            "entry_point": "handler.py",
        }
        manifest_data = json.dumps(manifest, indent=2).encode()
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest_data)
        tar.addfile(manifest_info, BytesIO(manifest_data))

        # Add handler source file
        if service._source_file:
            source_path = Path(service._source_file)
            if source_path.exists():
                tar.add(source_path, arcname="handler.py")

        # Add requirements.txt if exists
        if service._source_file:
            requirements_path = Path(service._source_file).parent / "requirements.txt"
            if requirements_path.exists():
                tar.add(requirements_path, arcname="requirements.txt")

    buffer.seek(0)
    return buffer.read()


async def invoke_service(
    service_name: str,
    payload: dict[str, Any],
    sync: bool = True,
    api_url: str | None = None,
) -> dict[str, Any]:
    """Invoke a deployed service.

    Args:
        service_name: Name of the service.
        payload: Request payload.
        sync: Wait for response.
        api_url: Override API URL.

    Returns:
        Service response.
    """
    api_url = api_url or get_api_url()

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{api_url}/api/v1/services/{service_name}/invoke",
            json={"payload": payload, "sync": sync},
        )
        response.raise_for_status()
        return response.json()


async def get_service_status(
    service_name: str,
    api_url: str | None = None,
) -> dict[str, Any]:
    """Get the status of a deployed service.

    Args:
        service_name: Name of the service.
        api_url: Override API URL.

    Returns:
        Service status information.
    """
    api_url = api_url or get_api_url()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{api_url}/api/v1/services/{service_name}"
        )
        response.raise_for_status()
        return response.json()


async def scale_service(
    service_name: str,
    workers: int,
    api_url: str | None = None,
) -> dict[str, Any]:
    """Scale a service to a specific number of workers.

    Args:
        service_name: Name of the service.
        workers: Target number of workers.
        api_url: Override API URL.

    Returns:
        Updated service status.
    """
    api_url = api_url or get_api_url()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/api/v1/services/{service_name}/scale",
            json={"workers": workers},
        )
        response.raise_for_status()
        return response.json()
