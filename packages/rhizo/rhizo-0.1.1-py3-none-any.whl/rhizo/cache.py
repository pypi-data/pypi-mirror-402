"""
CacheManager - LRU cache for Arrow tables with size-based eviction.

Provides efficient caching of Arrow tables for the OLAPEngine,
with automatic eviction when memory limits are reached.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any

import pyarrow as pa


@dataclass
class CacheKey:
    """Key for cache lookup - identifies a specific table version on a branch."""
    table_name: str
    version: int
    branch: str = "main"

    def __hash__(self) -> int:
        return hash((self.table_name.lower(), self.version, self.branch))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CacheKey):
            return False
        return (
            self.table_name.lower() == other.table_name.lower()
            and self.version == other.version
            and self.branch == other.branch
        )


@dataclass
class CacheEntry:
    """Entry in the cache with metadata."""
    table: pa.Table
    size_bytes: int
    created_at: float
    last_accessed: float
    access_count: int = 0


@dataclass
class CacheStats:
    """Statistics about cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size_bytes: int = 0
    max_size_bytes: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
            "current_size_bytes": self.current_size_bytes,
            "current_size_mb": round(self.current_size_bytes / 1024 / 1024, 2),
            "max_size_bytes": self.max_size_bytes,
            "max_size_mb": round(self.max_size_bytes / 1024 / 1024, 2),
            "utilization": round(self.current_size_bytes / self.max_size_bytes, 4)
            if self.max_size_bytes > 0
            else 0.0,
            "entry_count": self.entry_count,
        }


class CacheManager:
    """
    LRU cache for Arrow tables with size-based eviction.

    Features:
    - Size-based eviction (configurable max size in bytes)
    - LRU ordering (least recently used evicted first)
    - Per-table invalidation (e.g., after writes)
    - Hit/miss statistics

    Example:
        >>> cache = CacheManager(max_size_bytes=1_000_000_000)  # 1GB
        >>> key = CacheKey("users", version=5, branch="main")
        >>> cache.put(key, arrow_table)
        >>> cached = cache.get(key)  # Returns table, updates LRU order
        >>> cache.invalidate("users")  # Invalidate all versions

    Thread Safety:
        This implementation is NOT thread-safe. For concurrent access,
        wrap operations in appropriate locks.
    """

    def __init__(self, max_size_bytes: int = 1_000_000_000):
        """
        Initialize the cache.

        Args:
            max_size_bytes: Maximum cache size in bytes (default: 1GB)
        """
        if max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")

        self._max_size = max_size_bytes
        self._current_size = 0

        # OrderedDict maintains insertion order, used for LRU
        self._cache: OrderedDict[CacheKey, CacheEntry] = OrderedDict()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: CacheKey) -> Optional[pa.Table]:
        """
        Get a table from the cache.

        Updates LRU order on hit (moves to end of OrderedDict).

        Args:
            key: Cache key identifying the table

        Returns:
            Arrow table if found, None if not in cache
        """
        if key not in self._cache:
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        # Update access metadata
        entry = self._cache[key]
        entry.last_accessed = time.time()
        entry.access_count += 1

        self._hits += 1
        return entry.table

    def put(self, key: CacheKey, table: pa.Table) -> None:
        """
        Add a table to the cache.

        May evict other entries if cache is full.

        Args:
            key: Cache key identifying the table
            table: Arrow table to cache
        """
        # Calculate size of new entry
        size_bytes = _estimate_arrow_size(table)

        # If single entry is larger than max cache, don't cache it
        if size_bytes > self._max_size:
            return

        # Remove existing entry if present (will be re-added with new data)
        if key in self._cache:
            self._remove_entry(key)

        # Evict entries until we have room
        while self._current_size + size_bytes > self._max_size and self._cache:
            self._evict_lru()

        # Add new entry
        now = time.time()
        entry = CacheEntry(
            table=table,
            size_bytes=size_bytes,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        self._cache[key] = entry
        self._current_size += size_bytes

    def invalidate(self, table_name: str) -> int:
        """
        Invalidate all cached versions of a table.

        Args:
            table_name: Name of the table to invalidate

        Returns:
            Number of entries invalidated
        """
        table_lower = table_name.lower()

        # Find all keys for this table
        keys_to_remove = [
            k for k in self._cache if k.table_name.lower() == table_lower
        ]

        # Remove them
        for key in keys_to_remove:
            self._remove_entry(key)

        return len(keys_to_remove)

    def invalidate_version(self, table_name: str, version: int) -> bool:
        """
        Invalidate a specific version of a table.

        Args:
            table_name: Name of the table
            version: Version to invalidate

        Returns:
            True if entry was found and removed, False otherwise
        """
        # Find keys matching table and version (any branch)
        table_lower = table_name.lower()
        keys_to_remove = [
            k
            for k in self._cache
            if k.table_name.lower() == table_lower and k.version == version
        ]

        for key in keys_to_remove:
            self._remove_entry(key)

        return len(keys_to_remove) > 0

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._current_size = 0

    def contains(self, key: CacheKey) -> bool:
        """Check if a key is in the cache (without updating LRU order)."""
        return key in self._cache

    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            current_size_bytes=self._current_size,
            max_size_bytes=self._max_size,
            entry_count=len(self._cache),
        )

    def _remove_entry(self, key: CacheKey) -> None:
        """Remove an entry from the cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size -= entry.size_bytes

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # First item in OrderedDict is the LRU
        key = next(iter(self._cache))
        self._remove_entry(key)
        self._evictions += 1

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def __contains__(self, key: CacheKey) -> bool:
        """Check if key is in cache."""
        return key in self._cache


def _estimate_arrow_size(table: pa.Table) -> int:
    """
    Estimate the memory size of an Arrow table.

    Uses nbytes which gives the total buffer size.
    This is an approximation as it doesn't account for
    all metadata and Python object overhead.

    Args:
        table: Arrow table to measure

    Returns:
        Estimated size in bytes
    """
    return table.nbytes


@dataclass
class ChunkCacheStats:
    """Statistics about chunk cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size_bytes: int = 0
    max_size_bytes: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
            "current_size_bytes": self.current_size_bytes,
            "current_size_mb": round(self.current_size_bytes / 1024 / 1024, 2),
            "max_size_bytes": self.max_size_bytes,
            "max_size_mb": round(self.max_size_bytes / 1024 / 1024, 2),
            "utilization": round(self.current_size_bytes / self.max_size_bytes, 4)
            if self.max_size_bytes > 0
            else 0.0,
            "entry_count": self.entry_count,
        }


class ArrowChunkCache:
    """
    LRU cache for decoded Arrow RecordBatches, keyed by chunk hash.

    This cache leverages Rhizo's content-addressed storage model:
    - Chunks are immutable (same hash = same content forever)
    - No invalidation needed (content never changes)
    - Shared across tables, versions, and branches

    Mathematical Model:
        T_uncached = T_disk_io + T_parquet_decode ≈ 1.3ms + 5.0ms = 6.3ms
        T_cached   = T_cache_lookup ≈ 0.2ms
        Speedup    = 31x for repeated chunk reads

    This is a natural extension of content-addressed storage:
    - Same chunk appearing in multiple tables/versions hits cache
    - Branching benefits from shared chunks
    - Deduplication multiplies cache effectiveness

    Example:
        >>> cache = ArrowChunkCache(max_size_bytes=100_000_000)  # 100MB
        >>> batch = cache.get("abc123...")  # Returns None (miss)
        >>> cache.put("abc123...", decoded_batch)
        >>> batch = cache.get("abc123...")  # Returns batch (hit)

    Thread Safety:
        This implementation is NOT thread-safe. For concurrent access,
        wrap operations in appropriate locks or use per-thread caches.
    """

    def __init__(self, max_size_bytes: int = 100_000_000):
        """
        Initialize the chunk cache.

        Args:
            max_size_bytes: Maximum cache size in bytes (default: 100MB)
        """
        if max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")

        self._max_size = max_size_bytes
        self._current_size = 0

        # OrderedDict maintains insertion order for LRU eviction
        # Key: chunk_hash (str), Value: (RecordBatch, size_bytes)
        self._cache: OrderedDict[str, Tuple[pa.RecordBatch, int]] = OrderedDict()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, chunk_hash: str) -> Optional[pa.RecordBatch]:
        """
        Get a decoded RecordBatch from the cache.

        Updates LRU order on hit (moves to end).

        Args:
            chunk_hash: Content hash of the chunk (BLAKE3)

        Returns:
            RecordBatch if found, None if not in cache
        """
        if chunk_hash not in self._cache:
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(chunk_hash)
        self._hits += 1

        batch, _ = self._cache[chunk_hash]
        return batch

    def put(self, chunk_hash: str, batch: pa.RecordBatch) -> bool:
        """
        Add a decoded RecordBatch to the cache.

        May evict other entries if cache is full.

        Args:
            chunk_hash: Content hash of the chunk (BLAKE3)
            batch: Decoded Arrow RecordBatch

        Returns:
            True if cached successfully, False if too large for cache
        """
        size_bytes = batch.nbytes

        # If single entry is larger than max cache, don't cache
        if size_bytes > self._max_size:
            return False

        # Remove existing entry if present (shouldn't happen with content-addressing)
        if chunk_hash in self._cache:
            self._remove_entry(chunk_hash)

        # Evict LRU entries until we have room
        while self._current_size + size_bytes > self._max_size and self._cache:
            self._evict_lru()

        # Add new entry
        self._cache[chunk_hash] = (batch, size_bytes)
        self._current_size += size_bytes
        return True

    def contains(self, chunk_hash: str) -> bool:
        """Check if a chunk is in cache (without updating LRU order)."""
        return chunk_hash in self._cache

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._current_size = 0

    def stats(self) -> ChunkCacheStats:
        """Get cache statistics."""
        return ChunkCacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            current_size_bytes=self._current_size,
            max_size_bytes=self._max_size,
            entry_count=len(self._cache),
        )

    def _remove_entry(self, chunk_hash: str) -> None:
        """Remove an entry from the cache."""
        if chunk_hash in self._cache:
            _, size_bytes = self._cache.pop(chunk_hash)
            self._current_size -= size_bytes

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # First item in OrderedDict is the LRU
        chunk_hash = next(iter(self._cache))
        self._remove_entry(chunk_hash)
        self._evictions += 1

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def __contains__(self, chunk_hash: str) -> bool:
        """Check if chunk hash is in cache."""
        return chunk_hash in self._cache
