"""Request context for worker runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from mem_storage import LRUCache, S3Client, CacheConfig
from mem_common.config import get_settings


@dataclass
class WorkerRequestContext:
    """Context passed to handler functions in the worker runtime.

    Provides access to:
    - cache: LRU cache backed by NVMe storage
    - storage: S3 client for object storage
    - objects: In-memory object store (persists across requests)
    - request_id: Unique request identifier
    - service_name: Name of the service
    - worker_id: ID of this worker instance
    """

    request_id: UUID
    service_name: str
    worker_id: UUID | None = None
    cache: LRUCache | None = None
    storage: S3Client | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    _owns_cache: bool = False
    _shared_context: SharedWorkerContext | None = None

    @classmethod
    async def create(
        cls,
        request_id: UUID,
        service_name: str,
        worker_id: UUID | None = None,
        cache: LRUCache | None = None,
        storage: S3Client | None = None,
        cache_config: CacheConfig | None = None,
    ) -> WorkerRequestContext:
        """Create a new request context.

        Args:
            request_id: Unique request ID.
            service_name: Name of the service.
            worker_id: Optional worker ID.
            cache: Optional shared cache instance.
            storage: Optional shared storage client.
            cache_config: Cache configuration (if creating new cache).

        Returns:
            Initialized WorkerRequestContext.
        """
        owns_cache = False

        # Create cache if not provided
        if cache is None:
            settings = get_settings()
            cache_config = cache_config or CacheConfig(
                cache_dir=f"/var/lib/memrun/cache/{service_name}",
                max_size_bytes=100 * 1024**3,  # 100GB
            )
            cache = LRUCache(cache_config)
            await cache.start()
            owns_cache = True

        # Create storage if not provided
        if storage is None:
            storage = S3Client()

        return cls(
            request_id=request_id,
            service_name=service_name,
            worker_id=worker_id,
            cache=cache,
            storage=storage,
            _owns_cache=owns_cache,
        )

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
            key: S3 key (default: results/{request_id}/result).
            content_type: MIME type.

        Returns:
            S3 URL of the uploaded data.
        """
        if self.storage is None:
            raise RuntimeError("Storage not initialized")

        settings = get_settings()
        bucket = settings.s3_bucket_artifacts
        key = key or f"results/{self.request_id}/result"

        return await self.storage.upload_bytes(
            bucket=bucket,
            key=key,
            data=data,
            content_type=content_type,
        )

    async def cleanup(self) -> None:
        """Clean up resources owned by this context."""
        if self._owns_cache and self.cache:
            await self.cache.stop()

    def get_object(self, name: str) -> Any | None:
        """Get a named object from worker memory.

        Objects persist across requests on the same worker.

        Args:
            name: Object name.

        Returns:
            The object, or None if not found.

        Example:
            model = ctx.get_object("my_model")
            if model is None:
                model = load_model()
                ctx.set_object("my_model", model)
        """
        if self._shared_context is None:
            return None
        return self._shared_context.get_object(name)

    def set_object(self, name: str, obj: Any) -> None:
        """Store a named object in worker memory.

        Objects persist across requests on the same worker.

        Args:
            name: Object name.
            obj: Object to store.

        Example:
            ctx.set_object("embeddings", embeddings_matrix)
        """
        if self._shared_context is None:
            raise RuntimeError("Shared context not initialized")
        self._shared_context.set_object(name, obj)

    def has_object(self, name: str) -> bool:
        """Check if a named object exists in worker memory.

        Args:
            name: Object name.

        Returns:
            True if object exists.
        """
        if self._shared_context is None:
            return False
        return self._shared_context.has_object(name)

    def delete_object(self, name: str) -> bool:
        """Delete a named object from worker memory.

        Args:
            name: Object name.

        Returns:
            True if deleted, False if not found.
        """
        if self._shared_context is None:
            return False
        return self._shared_context.delete_object(name)

    def list_objects(self) -> list[str]:
        """List all stored object names.

        Returns:
            List of object names.
        """
        if self._shared_context is None:
            return []
        return self._shared_context.list_objects()


@dataclass
class WorkerInitContext:
    """Context passed to initialization handlers in the worker runtime.

    Provides access to cache, storage, and in-memory object store
    for pre-loading data before request processing begins.
    """

    service_name: str
    worker_id: UUID
    cache: LRUCache | None = None
    storage: S3Client | None = None
    _shared_context: SharedWorkerContext | None = None

    def get_object(self, name: str) -> Any | None:
        """Get a named object from worker memory.

        Args:
            name: Object name.

        Returns:
            The object, or None if not found.
        """
        if self._shared_context is None:
            return None
        return self._shared_context.get_object(name)

    def set_object(self, name: str, obj: Any) -> None:
        """Store a named object in worker memory.

        Args:
            name: Object name.
            obj: Object to store.
        """
        if self._shared_context is None:
            raise RuntimeError("Shared context not initialized")
        self._shared_context.set_object(name, obj)

    def has_object(self, name: str) -> bool:
        """Check if a named object exists in worker memory.

        Args:
            name: Object name.

        Returns:
            True if object exists.
        """
        if self._shared_context is None:
            return False
        return self._shared_context.has_object(name)

    def delete_object(self, name: str) -> bool:
        """Delete a named object from worker memory.

        Args:
            name: Object name.

        Returns:
            True if deleted, False if not found.
        """
        if self._shared_context is None:
            return False
        return self._shared_context.delete_object(name)

    def list_objects(self) -> list[str]:
        """List all stored object names.

        Returns:
            List of object names.
        """
        if self._shared_context is None:
            return []
        return self._shared_context.list_objects()


class SharedWorkerContext:
    """Shared context for a worker instance.

    Manages shared resources (cache, storage, in-memory objects) across all requests
    processed by this worker.
    """

    def __init__(
        self,
        service_name: str,
        worker_id: UUID,
        cache_config: CacheConfig | None = None,
    ):
        self.service_name = service_name
        self.worker_id = worker_id
        self._cache_config = cache_config
        self._cache: LRUCache | None = None
        self._storage: S3Client | None = None
        self._objects: dict[str, Any] = {}

    async def start(self) -> None:
        """Start shared resources."""
        settings = get_settings()

        # Initialize cache
        self._cache_config = self._cache_config or CacheConfig(
            cache_dir=f"/var/lib/memrun/cache/{self.service_name}",
            max_size_bytes=100 * 1024**3,
        )
        self._cache = LRUCache(self._cache_config)
        await self._cache.start()

        # Initialize storage
        self._storage = S3Client()

    async def stop(self) -> None:
        """Stop shared resources."""
        if self._cache:
            await self._cache.stop()

    def create_request_context(self, request_id: UUID) -> WorkerRequestContext:
        """Create a request context using shared resources.

        Args:
            request_id: Unique request ID.

        Returns:
            WorkerRequestContext with shared cache, storage, and object store.
        """
        return WorkerRequestContext(
            request_id=request_id,
            service_name=self.service_name,
            worker_id=self.worker_id,
            cache=self._cache,
            storage=self._storage,
            _owns_cache=False,  # Shared, don't stop on cleanup
            _shared_context=self,
        )

    def create_init_context(self) -> WorkerInitContext:
        """Create an init context using shared resources.

        Returns:
            WorkerInitContext with shared cache, storage, and object store.
        """
        return WorkerInitContext(
            service_name=self.service_name,
            worker_id=self.worker_id,
            cache=self._cache,
            storage=self._storage,
            _shared_context=self,
        )

    @property
    def cache(self) -> LRUCache | None:
        """Get the shared cache."""
        return self._cache

    @property
    def storage(self) -> S3Client | None:
        """Get the shared storage client."""
        return self._storage

    def get_object(self, name: str) -> Any | None:
        """Get a named object from memory.

        Args:
            name: Object name.

        Returns:
            The object, or None if not found.
        """
        return self._objects.get(name)

    def set_object(self, name: str, obj: Any) -> None:
        """Store a named object in memory.

        Args:
            name: Object name.
            obj: Object to store.
        """
        self._objects[name] = obj

    def has_object(self, name: str) -> bool:
        """Check if a named object exists.

        Args:
            name: Object name.

        Returns:
            True if object exists.
        """
        return name in self._objects

    def delete_object(self, name: str) -> bool:
        """Delete a named object from memory.

        Args:
            name: Object name.

        Returns:
            True if object was deleted, False if not found.
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
