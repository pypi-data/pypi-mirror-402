"""memrun: Serverless data platform SDK and CLI for Hetzner Cloud.

Example usage:
    from memrun import MemoryService

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

    if __name__ == "__main__":
        svc.deploy()  # or svc.serve() for local dev
"""

from memrun.service import MemoryService
from memrun.context import RequestContext, InitContext
from memrun.decorators import handler, init_handler

__version__ = "0.1.0"

__all__ = [
    "MemoryService",
    "RequestContext",
    "InitContext",
    "handler",
    "init_handler",
    "__version__",
]
