"""Handler package builder for creating deployment tarballs."""

import io
import json
import tarfile
from pathlib import Path
from typing import Any

from memrun.handler_extractor import HandlerInfo, InitHandlerInfo


def build_handler_package(
    handler_file: Path,
    service_name: str,
    handler_info: HandlerInfo,
    image: str,
    service_config: dict[str, Any],
    init_handler_info: InitHandlerInfo | None = None,
) -> bytes:
    """Build a deployment tarball containing handler and manifest.

    The tarball contains:
    - manifest.json: Service config, handler config, entry point info
    - handler.py: The user's handler file (renamed for consistency)
    - requirements.txt: If exists in same directory as handler

    Args:
        handler_file: Path to the Python handler file.
        service_name: Name of the service.
        handler_info: Extracted handler information.
        image: Base Docker image for workers.
        service_config: Service configuration dict (memory, disk, etc.).
        init_handler_info: Optional init handler information.

    Returns:
        Bytes of the tarball.
    """
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        # Create manifest.json
        manifest = _create_manifest(
            service_name=service_name,
            handler_info=handler_info,
            image=image,
            service_config=service_config,
            original_filename=handler_file.name,
            init_handler_info=init_handler_info,
        )
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        _add_bytes_to_tar(tar, "manifest.json", manifest_bytes)

        # Add the handler file as handler.py
        handler_content = handler_file.read_bytes()
        _add_bytes_to_tar(tar, "handler.py", handler_content)

        # Check for requirements.txt in the same directory
        requirements_file = handler_file.parent / "requirements.txt"
        if requirements_file.exists():
            requirements_content = requirements_file.read_bytes()
            _add_bytes_to_tar(tar, "requirements.txt", requirements_content)

    return buffer.getvalue()


def _create_manifest(
    service_name: str,
    handler_info: HandlerInfo,
    image: str,
    service_config: dict[str, Any],
    original_filename: str,
    init_handler_info: InitHandlerInfo | None = None,
) -> dict[str, Any]:
    """Create the manifest.json content.

    The manifest contains all information needed by workers to:
    1. Set up the correct environment
    2. Load and execute the handler

    Args:
        service_name: Name of the service.
        handler_info: Handler metadata.
        image: Base Docker image.
        service_config: Service configuration.
        original_filename: Original name of the handler file.
        init_handler_info: Optional init handler metadata.

    Returns:
        Manifest dictionary.
    """
    manifest: dict[str, Any] = {
        "version": "1",
        "service": {
            "name": service_name,
            "image": image,
            **service_config,
        },
        "handler": {
            "file": "handler.py",
            "function": handler_info.function_name,
            "original_filename": original_filename,
            "sticky_key": handler_info.sticky_key,
            "timeout_seconds": handler_info.timeout_seconds,
        },
        "entry_point": {
            "module": "handler",
            "function": handler_info.function_name,
        },
    }

    if init_handler_info is not None:
        manifest["init_handler"] = init_handler_info.to_dict()

    return manifest


def _add_bytes_to_tar(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    """Add bytes to a tarfile with proper metadata."""
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))
