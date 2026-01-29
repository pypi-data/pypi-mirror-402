"""
Unit tests for ArrowChunkCache and CacheManager.

Tests cover:
- Basic cache operations (get, put, eviction)
- LRU ordering
- Size limits
- Statistics tracking
"""
# pyright: reportMissingImports=false

import sys
sys.path.insert(0, ".")

import pytest
import pyarrow as pa

from rhizo.cache import (
    ArrowChunkCache,
    ChunkCacheStats,
    CacheManager,
    CacheKey,
    CacheStats,
)


class TestArrowChunkCache:
    """Tests for ArrowChunkCache."""

    def test_init_with_valid_size(self):
        """Cache initializes with valid max size."""
        cache = ArrowChunkCache(max_size_bytes=1000)
        assert len(cache) == 0
        stats = cache.stats()
        assert stats.max_size_bytes == 1000
        assert stats.current_size_bytes == 0

    def test_init_with_invalid_size_raises(self):
        """Cache rejects invalid max size."""
        with pytest.raises(ValueError):
            ArrowChunkCache(max_size_bytes=0)
        with pytest.raises(ValueError):
            ArrowChunkCache(max_size_bytes=-100)

    def test_put_and_get(self):
        """Basic put and get operations work."""
        cache = ArrowChunkCache(max_size_bytes=10_000_000)

        # Create a small RecordBatch
        batch = pa.RecordBatch.from_pydict({
            "id": [1, 2, 3],
            "value": ["a", "b", "c"]
        })

        # Put in cache
        chunk_hash = "abc123"
        result = cache.put(chunk_hash, batch)
        assert result is True

        # Get from cache
        retrieved = cache.get(chunk_hash)
        assert retrieved is not None
        assert retrieved.num_rows == 3
        assert retrieved.column("id").to_pylist() == [1, 2, 3]

    def test_get_miss_returns_none(self):
        """Get returns None for missing keys."""
        cache = ArrowChunkCache(max_size_bytes=10_000_000)
        assert cache.get("nonexistent") is None

    def test_contains(self):
        """Contains check works without updating LRU."""
        cache = ArrowChunkCache(max_size_bytes=10_000_000)
        batch = pa.RecordBatch.from_pydict({"x": [1, 2, 3]})

        cache.put("key1", batch)

        assert cache.contains("key1") is True
        assert cache.contains("key2") is False
        assert "key1" in cache
        assert "key2" not in cache

    def test_lru_eviction(self):
        """LRU eviction removes least recently used."""
        # Create batches with known sizes (list of 100 ints = ~800 bytes each)
        batch1 = pa.RecordBatch.from_pydict({"x": list(range(100))})
        batch2 = pa.RecordBatch.from_pydict({"x": list(range(100, 200))})
        batch3 = pa.RecordBatch.from_pydict({"x": list(range(200, 300))})

        # Cache that can hold about 2 batches
        batch_size = batch1.nbytes
        cache = ArrowChunkCache(max_size_bytes=int(batch_size * 2.5))

        cache.put("first", batch1)
        cache.put("second", batch2)

        # Access first to make it more recent
        cache.get("first")

        # Add third, should evict second (LRU)
        cache.put("third", batch3)

        # first and third should still be present
        # second should have been evicted
        stats = cache.stats()
        assert stats.evictions >= 1
        assert cache.contains("first")  # Was accessed recently
        assert cache.contains("third")  # Newly added
        assert not cache.contains("second")  # Should be evicted (LRU)

    def test_statistics_tracking(self):
        """Statistics are tracked correctly."""
        cache = ArrowChunkCache(max_size_bytes=10_000_000)
        batch = pa.RecordBatch.from_pydict({"x": [1, 2, 3]})

        # Initial stats
        stats = cache.stats()
        assert stats.hits == 0
        assert stats.misses == 0

        # Miss
        cache.get("missing")
        stats = cache.stats()
        assert stats.misses == 1

        # Put
        cache.put("key1", batch)

        # Hit
        cache.get("key1")
        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5

    def test_clear(self):
        """Clear removes all entries."""
        cache = ArrowChunkCache(max_size_bytes=10_000_000)
        batch = pa.RecordBatch.from_pydict({"x": [1]})

        cache.put("key1", batch)
        cache.put("key2", batch)
        assert len(cache) == 2

        cache.clear()
        assert len(cache) == 0
        assert cache.stats().current_size_bytes == 0

    def test_oversized_entry_not_cached(self):
        """Entries larger than max cache size are not cached."""
        cache = ArrowChunkCache(max_size_bytes=100)  # Tiny cache

        # Create a batch that's definitely > 100 bytes
        batch = pa.RecordBatch.from_pydict({
            "data": list(range(1000))
        })

        result = cache.put("big", batch)
        assert result is False
        assert len(cache) == 0

    def test_stats_to_dict(self):
        """Stats convert to dictionary correctly."""
        stats = ChunkCacheStats(
            hits=10,
            misses=5,
            evictions=2,
            current_size_bytes=500_000,
            max_size_bytes=1_000_000,
            entry_count=3
        )

        d = stats.to_dict()
        assert d["hits"] == 10
        assert d["misses"] == 5
        assert d["hit_rate"] == 0.6667
        assert d["utilization"] == 0.5
        assert d["current_size_mb"] == 0.48
        assert d["max_size_mb"] == 0.95


class TestCacheManager:
    """Tests for the table-level CacheManager."""

    def test_cache_key_equality(self):
        """CacheKey equality is case-insensitive for table name."""
        key1 = CacheKey("Users", 1, "main")
        key2 = CacheKey("users", 1, "main")
        key3 = CacheKey("Users", 2, "main")

        assert key1 == key2
        assert key1 != key3
        assert hash(key1) == hash(key2)

    def test_put_and_get_table(self):
        """Table caching works correctly."""
        cache = CacheManager(max_size_bytes=100_000_000)

        table = pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        key = CacheKey("test_table", 1, "main")

        cache.put(key, table)

        result = cache.get(key)
        assert result is not None
        assert result.num_rows == 3

    def test_invalidate_table(self):
        """Invalidate removes all versions of a table."""
        cache = CacheManager(max_size_bytes=100_000_000)

        table = pa.table({"x": [1]})
        cache.put(CacheKey("mytable", 1, "main"), table)
        cache.put(CacheKey("mytable", 2, "main"), table)
        cache.put(CacheKey("othertable", 1, "main"), table)

        assert len(cache) == 3

        removed = cache.invalidate("mytable")

        assert removed == 2
        assert len(cache) == 1
        assert cache.contains(CacheKey("othertable", 1, "main"))

    def test_invalidate_version(self):
        """Invalidate specific version works."""
        cache = CacheManager(max_size_bytes=100_000_000)

        table = pa.table({"x": [1]})
        cache.put(CacheKey("mytable", 1, "main"), table)
        cache.put(CacheKey("mytable", 2, "main"), table)

        result = cache.invalidate_version("mytable", 1)

        assert result is True
        assert len(cache) == 1
        assert cache.contains(CacheKey("mytable", 2, "main"))


class TestIntegration:
    """Integration tests for cache with reader."""

    def test_cache_disabled(self):
        """Reader works with cache disabled."""
        import tempfile
        import os
        from _rhizo import PyChunkStore, PyCatalog  # type: ignore[import-not-found]
        from rhizo import TableWriter, TableReader

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_dir = os.path.join(tmpdir, "chunks")
            catalog_dir = os.path.join(tmpdir, "catalog")
            os.makedirs(chunks_dir)
            os.makedirs(catalog_dir)

            store = PyChunkStore(chunks_dir)
            catalog = PyCatalog(catalog_dir)

            writer = TableWriter(store, catalog)
            table = pa.table({"id": [1, 2, 3]})
            writer.write("test", table)

            # Create reader with cache disabled
            reader = TableReader(store, catalog, enable_chunk_cache=False)

            result = reader.read_arrow("test")
            assert result.num_rows == 3
            assert reader.cache_stats() is None

    def test_cache_enabled(self):
        """Reader works with cache enabled and provides stats."""
        import tempfile
        import os
        from _rhizo import PyChunkStore, PyCatalog  # type: ignore[import-not-found]
        from rhizo import TableWriter, TableReader

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_dir = os.path.join(tmpdir, "chunks")
            catalog_dir = os.path.join(tmpdir, "catalog")
            os.makedirs(chunks_dir)
            os.makedirs(catalog_dir)

            store = PyChunkStore(chunks_dir)
            catalog = PyCatalog(catalog_dir)

            writer = TableWriter(store, catalog)
            table = pa.table({"id": [1, 2, 3]})
            writer.write("test", table)

            # Create reader with cache enabled
            reader = TableReader(store, catalog, enable_chunk_cache=True, chunk_cache_size_mb=10)

            # First read (miss)
            result1 = reader.read_arrow("test")
            assert result1.num_rows == 3

            stats1 = reader.cache_stats()
            assert stats1 is not None
            assert stats1.misses == 1
            assert stats1.hits == 0

            # Second read (hit)
            result2 = reader.read_arrow("test")
            assert result2.num_rows == 3

            stats2 = reader.cache_stats()
            assert stats2 is not None
            assert stats2.hits == 1
            assert stats2.misses == 1
            assert stats2.hit_rate == 0.5

    def test_cache_with_projection(self):
        """Cache works correctly with column projection."""
        import tempfile
        import os
        from _rhizo import PyChunkStore, PyCatalog  # type: ignore[import-not-found]
        from rhizo import TableWriter, TableReader

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_dir = os.path.join(tmpdir, "chunks")
            catalog_dir = os.path.join(tmpdir, "catalog")
            os.makedirs(chunks_dir)
            os.makedirs(catalog_dir)

            store = PyChunkStore(chunks_dir)
            catalog = PyCatalog(catalog_dir)

            writer = TableWriter(store, catalog)
            table = pa.table({
                "id": [1, 2, 3],
                "name": ["a", "b", "c"],
                "value": [10, 20, 30]
            })
            writer.write("test", table)

            reader = TableReader(store, catalog, enable_chunk_cache=True)

            # Read with projection
            result = reader.read_arrow("test", columns=["id", "name"])
            assert result.num_columns == 2
            assert "value" not in result.column_names

            # Cache should still work for different projections
            result2 = reader.read_arrow("test", columns=["value"])
            assert result2.num_columns == 1

            # Should be 2 hits (cache stores full batch, projection applied after)
            stats = reader.cache_stats()
            assert stats is not None
            assert stats.hits >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
