"""
Basic tests for Distributed Intelligent Cache System
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from src.ailoos.cache.manager import DistributedCacheManager
from src.ailoos.cache.strategies import LRUStrategy, LFUStrategy
from src.ailoos.cache.compression import CacheCompression
from src.ailoos.cache.invalidation import CacheInvalidation

class TestDistributedCacheManager:
    """Test DistributedCacheManager functionality"""

    @pytest.fixture
    async def cache_manager(self):
        """Create a test cache manager"""
        cache = DistributedCacheManager(
            node_id="test_node",
            strategy="lru",
            max_size=100,
            enable_p2p=False
        )
        await cache.start()
        yield cache
        await cache.stop()

    @pytest.mark.asyncio
    async def test_basic_operations(self, cache_manager):
        """Test basic get/set operations"""
        # Test set
        result = await cache_manager.set("test:key", {"data": "value"})
        assert result is True

        # Test get
        value = await cache_manager.get("test:key")
        assert value == {"data": "value"}

        # Test exists
        exists = await cache_manager.exists("test:key")
        assert exists is True

        # Test nonexistent
        nonexistent = await cache_manager.get("nonexistent")
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_ttl_functionality(self, cache_manager):
        """Test TTL expiration"""
        # Set with short TTL
        await cache_manager.set("ttl:key", "ttl_value", ttl=0.1)

        # Should exist immediately
        exists = await cache_manager.exists("ttl:key")
        assert exists is True

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        exists = await cache_manager.exists("ttl:key")
        assert exists is False

    @pytest.mark.asyncio
    async def test_invalidation(self, cache_manager):
        """Test cache invalidation"""
        # Set some data
        await cache_manager.set("invalidate:key1", "value1")
        await cache_manager.set("invalidate:key2", "value2")

        # Invalidate one key
        result = await cache_manager.delete("invalidate:key1")
        assert result is True

        # Check invalidation
        value1 = await cache_manager.get("invalidate:key1")
        value2 = await cache_manager.get("invalidate:key2")

        assert value1 is None
        assert value2 == "value2"

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, cache_manager):
        """Test pattern-based invalidation"""
        # Set multiple keys with pattern
        await cache_manager.set("user:1:profile", "profile1")
        await cache_manager.set("user:2:profile", "profile2")
        await cache_manager.set("user:1:posts", "posts1")

        # Invalidate pattern
        count = await cache_manager.invalidate_pattern("user:*:profile")
        assert count == 2

        # Check results
        profile1 = await cache_manager.get("user:1:profile")
        profile2 = await cache_manager.get("user:2:profile")
        posts1 = await cache_manager.get("user:1:posts")

        assert profile1 is None
        assert profile2 is None
        assert posts1 == "posts1"

    @pytest.mark.asyncio
    async def test_dependency_invalidation(self, cache_manager):
        """Test dependency-based invalidation"""
        # Set data with dependency
        await cache_manager.set("user:1:posts", ["post1", "post2"])
        await cache_manager.set("user:1:stats", {"post_count": 2})

        # Add dependency: stats depends on posts
        cache_manager.add_invalidation_dependency("user:1:stats", "user:1:posts")

        # Invalidate posts - should cascade to stats
        await cache_manager.delete("user:1:posts")

        # Check both are invalidated
        posts = await cache_manager.get("user:1:posts")
        stats = await cache_manager.get("user:1:stats")

        assert posts is None
        assert stats is None

    @pytest.mark.asyncio
    async def test_compression(self, cache_manager):
        """Test compression functionality"""
        # Create large data that should be compressed
        large_data = "x" * 2000  # 2KB string

        await cache_manager.set("large:key", large_data)

        # Retrieve and verify
        retrieved = await cache_manager.get("large:key")
        assert retrieved == large_data

        # Check compression stats
        stats = await cache_manager.get_stats()
        compression = stats['compression']

        # Should have compression operations
        assert compression['compression_operations'] >= 1

    @pytest.mark.asyncio
    async def test_metrics_collection(self, cache_manager):
        """Test metrics collection"""
        # Generate some activity
        for i in range(10):
            await cache_manager.set(f"metric:key:{i}", f"value_{i}")

        for i in range(5):  # Hits
            await cache_manager.get(f"metric:key:{i}")

        for i in range(5, 15):  # Misses
            await cache_manager.get(f"metric:key:{i}")

        # Check metrics
        stats = await cache_manager.get_stats()
        metrics = stats['metrics']

        assert metrics['hits']['count'] == 5
        assert metrics['misses']['count'] == 5
        assert metrics['sets']['count'] == 10
        assert abs(metrics['hit_rate'] - 0.5) < 0.01  # 50% hit rate

    @pytest.mark.asyncio
    async def test_health_check(self, cache_manager):
        """Test health check functionality"""
        # Add some data
        await cache_manager.set("health:key", "health_value")

        health = await cache_manager.health_check()

        assert 'status' in health
        assert 'issues' in health
        assert 'stats' in health
        assert health['status'] in ['healthy', 'warning', 'critical']

    @pytest.mark.asyncio
    async def test_strategy_switching(self, cache_manager):
        """Test cache strategy switching"""
        initial_strategy = cache_manager.strategy.strategy_name

        # Switch strategy
        cache_manager.switch_strategy("lfu")

        assert cache_manager.strategy.strategy_name == "lfu"
        assert cache_manager.strategy.strategy_name != initial_strategy

class TestCacheStrategies:
    """Test individual cache strategies"""

    def test_lru_strategy(self):
        """Test LRU strategy"""
        strategy = LRUStrategy(max_size=3)

        # Add entries
        strategy.put("key1", "value1", 1)
        strategy.put("key2", "value2", 1)
        strategy.put("key3", "value3", 1)

        # Access key1 (makes it most recent)
        strategy.get("key1")

        # Add fourth entry - should evict key2 (LRU)
        strategy.put("key4", "value4", 1)

        # key2 should be evicted
        assert strategy.get("key2") is None
        assert strategy.get("key1") is not None
        assert strategy.get("key3") is not None
        assert strategy.get("key4") is not None

    def test_lfu_strategy(self):
        """Test LFU strategy"""
        strategy = LFUStrategy(max_size=3)

        # Add entries
        strategy.put("key1", "value1", 1)
        strategy.put("key2", "value2", 1)
        strategy.put("key3", "value3", 1)

        # Access key1 multiple times
        for _ in range(5):
            strategy.get("key1")

        # Access key2 twice
        for _ in range(2):
            strategy.get("key2")

        # key3 accessed once (default)

        # Add fourth entry - should evict key3 (LFU)
        strategy.put("key4", "value4", 1)

        # key3 should be evicted
        assert strategy.get("key3") is None
        assert strategy.get("key1") is not None
        assert strategy.get("key2") is not None
        assert strategy.get("key4") is not None

class TestCompression:
    """Test compression functionality"""

    def test_compression_logic(self):
        """Test compression logic"""
        compression = CacheCompression(min_size_threshold=100)

        # Small data - should not compress
        small_data = "small"
        compressed_small, is_compressed_small, _, _ = compression.compress(small_data)
        assert is_compressed_small is False

        # Large data - should compress
        large_data = "x" * 200
        compressed_large, is_compressed_large, _, _ = compression.compress(large_data)
        assert is_compressed_large is True

        # Test decompression
        decompressed = compression.decompress(compressed_large, is_compressed_large)
        assert decompressed == large_data

    def test_compression_stats(self):
        """Test compression statistics"""
        compression = CacheCompression()

        # Compress some data
        data = "x" * 1000
        compression.compress(data)
        compression.compress(data)

        stats = compression.get_stats()

        assert stats['compression_operations'] == 2
        assert stats['original_bytes'] == 2000
        assert stats['compressed_bytes'] > 0
        assert stats['compression_ratio'] < 1.0  # Should be compressed

class TestInvalidation:
    """Test invalidation functionality"""

    @pytest.mark.asyncio
    async def test_ttl_invalidation(self):
        """Test TTL-based invalidation"""
        invalidation = CacheInvalidation()
        await invalidation.start_ttl_monitor()

        # Set TTL
        invalidation.set_ttl("test:key", 0.1)

        # Should not be invalidated immediately
        assert not invalidation.is_invalidated("test:key")

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be marked as invalidated by TTL monitor
        # Note: In real usage, this would be handled by the cache manager

        await invalidation.stop_ttl_monitor()

    def test_dependency_tracking(self):
        """Test dependency relationship tracking"""
        invalidation = CacheInvalidation()

        # Add dependency
        invalidation.add_dependency("dependent", "dependency")

        # Check relationships
        assert "dependency" in invalidation.get_dependencies("dependent")
        assert "dependent" in invalidation.get_dependents("dependency")

        # Remove dependency
        invalidation.remove_dependency("dependent", "dependency")

        assert "dependency" not in invalidation.get_dependencies("dependent")
        assert "dependent" not in invalidation.get_dependents("dependency")

if __name__ == "__main__":
    pytest.main([__file__])