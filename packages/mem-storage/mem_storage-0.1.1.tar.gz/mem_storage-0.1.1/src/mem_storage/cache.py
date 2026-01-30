"""LRU cache backed by NVMe storage for persistent caching."""

import asyncio
import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine

import aiofiles
import aiofiles.os

from mem_common.config import get_settings


@dataclass
class CacheConfig:
    """Configuration for the LRU cache."""

    cache_dir: str = "/tmp/memrun-cache"
    max_size_bytes: int = 100 * 1024**3  # 100 GB default
    max_items: int = 100_000
    ttl_seconds: int | None = None  # None = no expiry
    cleanup_interval_seconds: int = 300  # 5 minutes


@dataclass
class CacheEntry:
    """Metadata for a cached item."""

    key: str
    file_path: str
    size_bytes: int
    created_at: float
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: int | None = None

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() > self.created_at + self.ttl_seconds


class LRUCache:
    """LRU cache backed by local disk (NVMe) storage.

    Provides fast access to cached data with configurable size limits
    and optional TTL. Designed for large datasets that need to survive
    worker restarts.
    """

    def __init__(self, config: CacheConfig | None = None):
        self._config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._total_size: int = 0
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._s3_client: Any = None

    async def start(self) -> None:
        """Start the cache (load index, start cleanup task)."""
        await self._ensure_cache_dir()
        await self._load_index()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the cache (save index, cancel cleanup)."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self._save_index()

    async def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        path = Path(self._config.cache_dir)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> str:
        """Convert a cache key to a file path."""
        # Use SHA256 hash for consistent, safe filenames
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        # Use first 2 chars as subdirectory for distribution
        subdir = key_hash[:2]
        return str(Path(self._config.cache_dir) / subdir / key_hash)

    async def get(self, key: str) -> bytes | None:
        """Get a value from the cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                await self._remove_entry(key)
                return None

            # Update access time and move to end (most recently used)
            entry.last_accessed = time.time()
            self._cache.move_to_end(key)

        # Read file outside of lock
        try:
            async with aiofiles.open(entry.file_path, "rb") as f:
                return await f.read()
        except FileNotFoundError:
            async with self._lock:
                await self._remove_entry(key)
            return None

    async def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set a value in the cache."""
        file_path = self._key_to_path(key)
        size_bytes = len(value)

        # Ensure subdirectory exists
        subdir = Path(file_path).parent
        if not subdir.exists():
            subdir.mkdir(parents=True, exist_ok=True)

        # Write file first
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(value)

        async with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                await self._remove_entry(key)

            # Evict if necessary
            await self._evict_if_needed(size_bytes)

            # Add new entry
            entry = CacheEntry(
                key=key,
                file_path=file_path,
                size_bytes=size_bytes,
                created_at=time.time(),
                ttl_seconds=ttl_seconds or self._config.ttl_seconds,
            )
            self._cache[key] = entry
            self._total_size += size_bytes

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        async with self._lock:
            if key in self._cache:
                await self._remove_entry(key)
                return True
            return False

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Coroutine[Any, Any, bytes]],
        ttl_seconds: int | None = None,
    ) -> bytes:
        """Get from cache or fetch and cache the result."""
        # Try to get from cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Fetch the value
        value = await fetch_fn()

        # Cache it
        await self.set(key, value, ttl_seconds)

        return value

    async def get_or_fetch_from_s3(
        self,
        s3_url: str,
        ttl_seconds: int | None = None,
    ) -> bytes:
        """Get from cache or fetch from S3."""
        from mem_storage.s3 import S3Client

        if self._s3_client is None:
            self._s3_client = S3Client()

        async def fetch() -> bytes:
            bucket, key = S3Client.parse_s3_url(s3_url)
            return await self._s3_client.download_bytes(bucket, key)

        return await self.get_or_fetch(s3_url, fetch, ttl_seconds)

    async def _remove_entry(self, key: str) -> None:
        """Remove an entry from the cache (must hold lock)."""
        entry = self._cache.pop(key, None)
        if entry:
            self._total_size -= entry.size_bytes
            try:
                await aiofiles.os.remove(entry.file_path)
            except FileNotFoundError:
                pass

    async def _evict_if_needed(self, needed_bytes: int) -> None:
        """Evict entries if cache is full (must hold lock)."""
        # Evict by item count
        while len(self._cache) >= self._config.max_items:
            # Remove oldest (first) entry
            oldest_key = next(iter(self._cache))
            await self._remove_entry(oldest_key)

        # Evict by size
        while self._total_size + needed_bytes > self._config.max_size_bytes:
            if not self._cache:
                break
            oldest_key = next(iter(self._cache))
            await self._remove_entry(oldest_key)

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired entries."""
        while True:
            await asyncio.sleep(self._config.cleanup_interval_seconds)
            await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                await self._remove_entry(key)

    async def _load_index(self) -> None:
        """Load cache index from disk."""
        index_path = Path(self._config.cache_dir) / "index.json"
        if not index_path.exists():
            return

        try:
            async with aiofiles.open(index_path, "r") as f:
                data = json.loads(await f.read())

            async with self._lock:
                for entry_data in data.get("entries", []):
                    entry = CacheEntry(**entry_data)
                    # Verify file exists
                    if Path(entry.file_path).exists():
                        self._cache[entry.key] = entry
                        self._total_size += entry.size_bytes
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    async def _save_index(self) -> None:
        """Save cache index to disk."""
        index_path = Path(self._config.cache_dir) / "index.json"

        async with self._lock:
            data = {
                "entries": [
                    {
                        "key": e.key,
                        "file_path": e.file_path,
                        "size_bytes": e.size_bytes,
                        "created_at": e.created_at,
                        "last_accessed": e.last_accessed,
                        "ttl_seconds": e.ttl_seconds,
                    }
                    for e in self._cache.values()
                ]
            }

        async with aiofiles.open(index_path, "w") as f:
            await f.write(json.dumps(data))

    @property
    def size_bytes(self) -> int:
        """Current cache size in bytes."""
        return self._total_size

    @property
    def item_count(self) -> int:
        """Current number of items in cache."""
        return len(self._cache)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size_bytes": self._total_size,
            "item_count": len(self._cache),
            "max_size_bytes": self._config.max_size_bytes,
            "max_items": self._config.max_items,
            "utilization_pct": (
                self._total_size / self._config.max_size_bytes * 100
                if self._config.max_size_bytes > 0
                else 0
            ),
        }
