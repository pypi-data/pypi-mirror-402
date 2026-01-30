"""Request context for handler functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from mem_storage import LRUCache, S3Client


@dataclass
class RequestContext:
    """Context passed to handler functions.

    Provides access to:
    - cache: LRU cache for large data (backed by NVMe)
    - storage: S3 storage client
    - request_id: Unique request identifier
    - service_name: Name of the service
    - worker_id: ID of the worker processing this request

    Example:
        @svc.handler()
        def handle(ctx: RequestContext, req: dict) -> dict:
            # Fetch data from cache or S3
            data = await ctx.cache.get_or_fetch_from_s3(req["data_url"])

            # Store results in S3
            result_url = await ctx.storage.upload_bytes(
                bucket="results",
                key=f"{ctx.request_id}/output.json",
                data=json.dumps(result).encode(),
            )

            return {"result_url": result_url}
    """

    request_id: UUID
    service_name: str
    worker_id: UUID | None = None
    cache: LRUCache | None = None
    storage: S3Client | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    async def get_or_fetch(self, s3_url: str, ttl_seconds: int | None = None) -> bytes:
        """Convenience method to get data from cache or fetch from S3.

        Args:
            s3_url: S3 URL (s3://bucket/key).
            ttl_seconds: Optional TTL for cached data.

        Returns:
            The data as bytes.
        """
        if self.cache is None:
            raise RuntimeError("Cache not initialized")
        return await self.cache.get_or_fetch_from_s3(s3_url, ttl_seconds)

    async def upload_result(
        self,
        data: bytes,
        key: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload result data to S3.

        Args:
            data: Data to upload.
            key: S3 key (default: {request_id}/result).
            content_type: MIME type.

        Returns:
            S3 URL of the uploaded data.
        """
        if self.storage is None:
            raise RuntimeError("Storage not initialized")

        from mem_common.config import get_settings

        settings = get_settings()
        bucket = settings.s3_bucket_artifacts
        key = key or f"results/{self.request_id}/result"

        return await self.storage.upload_bytes(
            bucket=bucket,
            key=key,
            data=data,
            content_type=content_type,
        )


@dataclass
class InitContext:
    """Context provided to initialization handlers.

    Provides access to cache, storage, and in-memory object store
    for pre-loading data before request processing begins.

    Example:
        @svc.init_handler()
        def setup(ctx: InitContext) -> None:
            # Download and cache model data
            model_data = await ctx.storage.download("s3://models/my-model.bin")

            # Store model in memory for fast access
            ctx.set_object("model", load_model(model_data))
    """

    service_name: str
    worker_id: UUID | None = None
    cache: LRUCache | None = None
    storage: S3Client | None = None
    _objects: dict[str, Any] = field(default_factory=dict)

    def get_object(self, name: str) -> Any | None:
        """Get a named object from worker memory.

        Args:
            name: Object name.

        Returns:
            The object, or None if not found.
        """
        return self._objects.get(name)

    def set_object(self, name: str, obj: Any) -> None:
        """Store a named object in worker memory.

        Args:
            name: Object name.
            obj: Object to store.
        """
        self._objects[name] = obj

    def has_object(self, name: str) -> bool:
        """Check if a named object exists in worker memory.

        Args:
            name: Object name.

        Returns:
            True if object exists.
        """
        return name in self._objects

    def delete_object(self, name: str) -> bool:
        """Delete a named object from worker memory.

        Args:
            name: Object name.

        Returns:
            True if deleted, False if not found.
        """
        if name in self._objects:
            del self._objects[name]
            return True
        return False

    def list_objects(self) -> list[str]:
        """List all stored object names.

        Returns:
            List of object names.
        """
        return list(self._objects.keys())


class LocalRequestContext(RequestContext):
    """Request context for local development.

    Uses local filesystem cache and MinIO for S3.
    """

    @classmethod
    async def create(
        cls,
        request_id: UUID,
        service_name: str,
    ) -> LocalRequestContext:
        """Create a local request context."""
        from mem_storage import LRUCache, S3Client, CacheConfig

        cache = LRUCache(CacheConfig(cache_dir="/tmp/memrun-local-cache"))
        await cache.start()

        storage = S3Client()

        return cls(
            request_id=request_id,
            service_name=service_name,
            cache=cache,
            storage=storage,
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.cache:
            await self.cache.stop()
