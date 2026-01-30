"""Local development server for memrun services."""

from __future__ import annotations

import asyncio
import inspect
import json
import traceback
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from memrun.service import MemoryService

from memrun.context import LocalRequestContext


async def run_local_server(
    service: MemoryService,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """Run a local development server for the service.

    This mimics the production environment but runs locally,
    useful for testing handlers before deployment.

    Args:
        service: The MemoryService to serve.
        host: Host to bind to.
        port: Port to bind to.
    """
    try:
        from aiohttp import web
    except ImportError:
        # Fallback to simple HTTP server
        await _run_simple_server(service, host, port)
        return

    await _run_aiohttp_server(service, host, port)


async def _run_aiohttp_server(
    service: MemoryService,
    host: str,
    port: int,
) -> None:
    """Run server using aiohttp."""
    from aiohttp import web

    handler = service.get_handler()
    if handler is None:
        raise ValueError("No handler registered")

    async def invoke_handler(request: web.Request) -> web.Response:
        """Handle invoke requests."""
        try:
            body = await request.json()
            payload = body.get("payload", {})

            # Create request context
            request_id = uuid4()
            ctx = await LocalRequestContext.create(
                request_id=request_id,
                service_name=service.config.name,
            )

            try:
                # Call handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(ctx, payload)
                else:
                    result = handler(ctx, payload)

                return web.json_response({
                    "request_id": str(request_id),
                    "status": "completed",
                    "result": result,
                })
            finally:
                await ctx.cleanup()

        except Exception as e:
            return web.json_response(
                {
                    "request_id": str(uuid4()),
                    "status": "failed",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
                status=500,
            )

    async def health_handler(request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "healthy", "service": service.config.name})

    async def status_handler(request: web.Request) -> web.Response:
        """Service status endpoint."""
        return web.json_response({
            "name": service.config.name,
            "config": service.config.model_dump(),
            "status": "running",
            "mode": "local",
        })

    app = web.Application()
    app.router.add_post("/invoke", invoke_handler)
    app.router.add_post(f"/invoke/{service.config.name}", invoke_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/status", status_handler)

    print(f"Starting local server for '{service.config.name}' at http://{host}:{port}")
    print(f"  POST /invoke - Invoke the handler")
    print(f"  GET  /health - Health check")
    print(f"  GET  /status - Service status")
    print()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await runner.cleanup()


async def _run_simple_server(
    service: MemoryService,
    host: str,
    port: int,
) -> None:
    """Run a simple HTTP server without aiohttp.

    Fallback for when aiohttp is not installed.
    """
    import http.server
    import socketserver
    from urllib.parse import urlparse

    handler_fn = service.get_handler()
    if handler_fn is None:
        raise ValueError("No handler registered")

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path in ("/invoke", f"/invoke/{service.config.name}"):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)

                try:
                    data = json.loads(body) if body else {}
                    payload = data.get("payload", {})

                    request_id = uuid4()

                    # Create a simple context (no async support)
                    class SimpleContext:
                        def __init__(self) -> None:
                            self.request_id = request_id
                            self.service_name = service.config.name
                            self.cache = None
                            self.storage = None

                    ctx = SimpleContext()

                    # Call handler (sync only in simple mode)
                    if asyncio.iscoroutinefunction(handler_fn):
                        result = asyncio.run(handler_fn(ctx, payload))
                    else:
                        result = handler_fn(ctx, payload)

                    response = json.dumps({
                        "request_id": str(request_id),
                        "status": "completed",
                        "result": result,
                    }).encode()

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", len(response))
                    self.end_headers()
                    self.wfile.write(response)

                except Exception as e:
                    response = json.dumps({
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }).encode()
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", len(response))
                    self.end_headers()
                    self.wfile.write(response)
            else:
                self.send_error(404)

        def do_GET(self) -> None:
            if self.path == "/health":
                response = json.dumps({"status": "healthy"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(response))
                self.end_headers()
                self.wfile.write(response)
            elif self.path == "/status":
                response = json.dumps({
                    "name": service.config.name,
                    "status": "running",
                    "mode": "local-simple",
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(response))
                self.end_headers()
                self.wfile.write(response)
            else:
                self.send_error(404)

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[{service.config.name}] {format % args}")

    print(f"Starting simple local server for '{service.config.name}' at http://{host}:{port}")
    print("  (Install aiohttp for full async support)")

    with socketserver.TCPServer((host, port), RequestHandler) as httpd:
        httpd.serve_forever()
