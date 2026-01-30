"""MemoryService class for defining serverless data services."""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, Field

from memrun.context import RequestContext
from memrun.decorators import HandlerConfig, InitHandlerConfig

F = TypeVar("F", bound=Callable[..., Any])


class ServiceConfig(BaseModel):
    """Configuration for a MemoryService."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$",
        description="Service name (DNS-compatible)",
    )
    image: str = Field(
        default="python:3.12-slim",
        description="Base Docker image (e.g., 'python:3.12', 'python:3.12-slim')",
    )
    memory: str = Field(
        default="4Gi",
        description="Memory allocation (e.g., '32Gi')",
        pattern=r"^\d+[KMGT]i$",
    )
    disk: str = Field(
        default="100Gi",
        description="Disk allocation for NVMe cache (e.g., '600Gi')",
        pattern=r"^\d+[KMGT]i$",
    )
    max_workers: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum number of worker instances",
    )
    min_workers: int = Field(
        default=0,
        ge=0,
        description="Minimum number of worker instances",
    )
    concurrency: int = Field(
        default=16,
        ge=1,
        le=1000,
        description="Concurrent requests per worker",
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Request timeout in seconds",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for workers",
    )


class MemoryService:
    """Define a serverless data service.

    Example:
        svc = MemoryService(
            name="matrix-qa",
            memory="32Gi",
            disk="600Gi",
            max_workers=50,
        )

        @svc.handler(sticky_key="user_id:dataset_id")
        def handle(ctx, req):
            data = ctx.cache.get_or_fetch(req.dataset_path)
            return process(data, req.params)

        svc.deploy()
    """

    def __init__(
        self,
        name: str,
        image: str = "python:3.12-slim",
        memory: str = "4Gi",
        disk: str = "100Gi",
        max_workers: int = 10,
        min_workers: int = 0,
        concurrency: int = 16,
        timeout_seconds: int = 300,
        env: dict[str, str] | None = None,
    ):
        self.config = ServiceConfig(
            name=name,
            image=image,
            memory=memory,
            disk=disk,
            max_workers=max_workers,
            min_workers=min_workers,
            concurrency=concurrency,
            timeout_seconds=timeout_seconds,
            env=env or {},
        )
        self._handler: Callable[..., Any] | None = None
        self._handler_config: HandlerConfig | None = None
        self._init_handler: Callable[..., Any] | None = None
        self._source_file: str | None = None

    def handler(
        self,
        sticky_key: str | None = None,
        timeout_seconds: int | None = None,
    ) -> Callable[[F], F]:
        """Decorator to register the request handler.

        Args:
            sticky_key: Request field for sticky routing (e.g., 'user_id:dataset_id').
                        Requests with the same sticky key value are routed to the same worker.
            timeout_seconds: Override the service-level timeout for this handler.

        Example:
            @svc.handler(sticky_key="user_id:dataset_id")
            def handle(ctx, req):
                data = ctx.cache.get_or_fetch(req.dataset_path)
                return {"result": process(data)}
        """

        def decorator(fn: F) -> F:
            self._handler = fn
            self._handler_config = HandlerConfig(
                sticky_key=sticky_key,
                timeout_seconds=timeout_seconds or self.config.timeout_seconds,
            )
            # Capture source file for deployment
            self._source_file = inspect.getfile(fn)
            return fn

        return decorator

    def init_handler(self) -> Callable[[F], F]:
        """Decorator to register an initialization handler.

        The init handler is called once after the worker is initialized
        and before any request handlers are invoked. Use this to load
        models, embeddings, or other data into memory.

        Example:
            @svc.init_handler()
            def setup(ctx):
                ctx.set_object("model", load_model())

            @svc.handler()
            def predict(ctx, req):
                model = ctx.get_object("model")
                return {"prediction": model.predict(req["input"])}
        """

        def decorator(fn: F) -> F:
            self._init_handler = fn
            # Attach config to the function for detection by handler_extractor
            fn._memrun_init_handler_config = InitHandlerConfig()  # type: ignore
            return fn

        return decorator

    def get_init_handler(self) -> Callable[..., Any] | None:
        """Get the registered init handler function."""
        return self._init_handler

    def deploy(
        self,
        api_url: str | None = None,
        wait: bool = True,
    ) -> dict[str, Any]:
        """Deploy the service to the memrun platform.

        Args:
            api_url: Override the API URL (default from MEMRUN_API_URL env).
            wait: Wait for deployment to complete.

        Returns:
            Deployment information including service URL.
        """
        from memrun.deploy import deploy_service

        if self._handler is None:
            raise ValueError("No handler registered. Use @svc.handler decorator.")

        return asyncio.run(
            deploy_service(
                service=self,
                api_url=api_url,
                wait=wait,
            )
        )

    def serve(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
    ) -> None:
        """Run the service locally for development.

        Starts a local HTTP server that mimics the production environment.

        Args:
            host: Host to bind to.
            port: Port to bind to.
        """
        from memrun.local import run_local_server

        if self._handler is None:
            raise ValueError("No handler registered. Use @svc.handler decorator.")

        asyncio.run(
            run_local_server(
                service=self,
                host=host,
                port=port,
            )
        )

    async def invoke(
        self,
        payload: dict[str, Any],
        sync: bool = True,
        api_url: str | None = None,
    ) -> dict[str, Any]:
        """Invoke the deployed service.

        Args:
            payload: Request payload.
            sync: Wait for response (default True).
            api_url: Override the API URL.

        Returns:
            Response from the service.
        """
        from memrun.deploy import invoke_service

        return await invoke_service(
            service_name=self.config.name,
            payload=payload,
            sync=sync,
            api_url=api_url,
        )

    def get_handler(self) -> Callable[..., Any] | None:
        """Get the registered handler function."""
        return self._handler

    def get_handler_config(self) -> HandlerConfig | None:
        """Get the handler configuration."""
        return self._handler_config

    def to_dict(self) -> dict[str, Any]:
        """Convert service configuration to dictionary."""
        return {
            **self.config.model_dump(),
            "sticky_key": self._handler_config.sticky_key if self._handler_config else None,
        }
