"""
Tests for Cache Cluster
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.ailoos.cache.cache_cluster import (
    CacheCluster, ClusterConfig, CacheNode, CacheBackend, NodeStatus
)
from src.ailoos.cache.redis_integration import RedisConfig
from src.ailoos.cache.memcached_integration import MemcachedConfig


class TestCacheCluster:
    """Test Cache Cluster functionality"""

    @pytest.fixture
    def cluster_config(self):
        """Cluster configuration fixture"""
        return ClusterConfig(
            cluster_name="test_cluster",
            load_balancing_strategy="consistent_hashing",
            replication_factor=2
        )

    @pytest.fixture
    def cache_cluster(self, cluster_config):
        """Cache cluster fixture"""
        return CacheCluster(cluster_config)

    @pytest.fixture
    def redis_node(self):
        """Redis cache node fixture"""
        return CacheNode(
            node_id="redis_node_1",
            backend=CacheBackend.REDIS,
            config=RedisConfig(host="localhost", port=6379),
            weight=2
        )

    @pytest.fixture
    def memcached_node(self):
        """Memcached cache node fixture"""
        return CacheNode(
            node_id="memcached_node_1",
            backend=CacheBackend.MEMCACHED,
            config=MemcachedConfig(servers=[("localhost", 11211)]),
            weight=1
        )

    @pytest.mark.asyncio
    async def test_initialization(self, cache_cluster, cluster_config):
        """Test cluster initialization"""
        assert cache_cluster.config == cluster_config
        assert len(cache_cluster.nodes) == 0
        assert len(cache_cluster.active_clients) == 0
        assert len(cache_cluster.node_hash_ring) == 0

    @pytest.mark.asyncio
    async def test_add_redis_node(self, cache_cluster, redis_node):
        """Test adding Redis node to cluster"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_redis.return_value = mock_client

            result = await cache_cluster.add_node(redis_node)

            assert result is True
            assert redis_node.node_id in cache_cluster.nodes
            assert redis_node.node_id in cache_cluster.active_clients
            assert len(cache_cluster.node_hash_ring) > 0  # Hash ring should be rebuilt

    @pytest.mark.asyncio
    async def test_add_memcached_node(self, cache_cluster, memcached_node):
        """Test adding Memcached node to cluster"""
        with patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_memcached.return_value = mock_client

            result = await cache_cluster.add_node(memcached_node)

            assert result is True
            assert memcached_node.node_id in cache_cluster.nodes
            assert memcached_node.node_id in cache_cluster.active_clients

    @pytest.mark.asyncio
    async def test_add_node_connection_failure(self, cache_cluster, redis_node):
        """Test adding node with connection failure"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = False
            mock_redis.return_value = mock_client

            result = await cache_cluster.add_node(redis_node)

            assert result is False
            assert redis_node.node_id not in cache_cluster.nodes

    @pytest.mark.asyncio
    async def test_remove_node(self, cache_cluster, redis_node):
        """Test removing node from cluster"""
        # First add the node
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)
            assert redis_node.node_id in cache_cluster.nodes

            # Now remove it
            result = await cache_cluster.remove_node(redis_node.node_id)

            assert result is True
            assert redis_node.node_id not in cache_cluster.nodes
            assert redis_node.node_id not in cache_cluster.active_clients
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_for_key_consistent_hashing(self, cache_cluster, redis_node, memcached_node):
        """Test consistent hashing node selection"""
        # Add nodes
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis, \
             patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:

            mock_redis_client = AsyncMock()
            mock_redis_client.connect.return_value = True
            mock_redis.return_value = mock_redis_client

            mock_memcached_client = AsyncMock()
            mock_memcached_client.connect.return_value = True
            mock_memcached.return_value = mock_memcached_client

            await cache_cluster.add_node(redis_node)
            await cache_cluster.add_node(memcached_node)

            # Test node selection for same key is consistent
            key = "test_key"
            node1 = cache_cluster._get_node_for_key(key)
            node2 = cache_cluster._get_node_for_key(key)

            assert node1 == node2
            assert node1 in [redis_node.node_id, memcached_node.node_id]

    @pytest.mark.asyncio
    async def test_get_round_robin(self, cache_cluster, redis_node, memcached_node):
        """Test round-robin load balancing"""
        cache_cluster.config.load_balancing_strategy = "round_robin"

        # Add nodes
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis, \
             patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:

            mock_redis_client = AsyncMock()
            mock_redis_client.connect.return_value = True
            mock_redis.return_value = mock_redis_client

            mock_memcached_client = AsyncMock()
            mock_memcached_client.connect.return_value = True
            mock_memcached.return_value = mock_memcached_client

            await cache_cluster.add_node(redis_node)
            await cache_cluster.add_node(memcached_node)

            # Test round-robin distribution
            nodes = []
            for i in range(4):
                node = cache_cluster._get_node_for_key(f"key_{i}")
                nodes.append(node)

            # Should alternate between nodes
            assert len(set(nodes)) == 2  # Both nodes should be used

    @pytest.mark.asyncio
    async def test_get_least_loaded(self, cache_cluster, redis_node, memcached_node):
        """Test least-loaded node selection"""
        cache_cluster.config.load_balancing_strategy = "least_loaded"

        # Add nodes
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis, \
             patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:

            mock_redis_client = AsyncMock()
            mock_redis_client.connect.return_value = True
            mock_redis.return_value = mock_redis_client

            mock_memcached_client = AsyncMock()
            mock_memcached_client.connect.return_value = True
            mock_memcached.return_value = mock_memcached_client

            await cache_cluster.add_node(redis_node)
            await cache_cluster.add_node(memcached_node)

            # Simulate different loads
            cache_cluster.nodes[redis_node.node_id].total_requests = 100
            cache_cluster.nodes[memcached_node.node_id].total_requests = 50

            # Should select memcached node (lower load)
            node = cache_cluster._get_node_for_key("test_key")
            assert node == memcached_node.node_id

    @pytest.mark.asyncio
    async def test_get_success(self, cache_cluster, redis_node):
        """Test successful get operation"""
        # Setup cluster with one node
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.get.return_value = "test_value"
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            result = await cache_cluster.get("test_key")

            assert result == "test_value"
            assert cache_cluster.stats['successful_requests'] == 1
            mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_with_failover(self, cache_cluster, redis_node, memcached_node):
        """Test get operation with failover"""
        # Setup cluster with two nodes
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis, \
             patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:

            mock_redis_client = AsyncMock()
            mock_redis_client.connect.return_value = True
            mock_redis_client.get.return_value = None  # Primary fails
            mock_redis.return_value = mock_redis_client

            mock_memcached_client = AsyncMock()
            mock_memcached_client.connect.return_value = True
            mock_memcached_client.get.return_value = "failover_value"  # Secondary succeeds
            mock_memcached.return_value = mock_memcached_client

            await cache_cluster.add_node(redis_node)
            await cache_cluster.add_node(memcached_node)

            result = await cache_cluster.get("test_key")

            assert result == "failover_value"
            assert cache_cluster.stats['load_balanced_requests'] == 1

    @pytest.mark.asyncio
    async def test_set_success(self, cache_cluster, redis_node):
        """Test successful set operation"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.set.return_value = True
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            result = await cache_cluster.set("test_key", "test_value")

            assert result is True
            assert cache_cluster.stats['successful_requests'] == 1

    @pytest.mark.asyncio
    async def test_set_with_replication(self, cache_cluster, redis_node, memcached_node):
        """Test set operation with replication"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis, \
             patch('src.ailoos.cache.memcached_integration.MemcachedIntegration') as mock_memcached:

            mock_redis_client = AsyncMock()
            mock_redis_client.connect.return_value = True
            mock_redis_client.set.return_value = True
            mock_redis.return_value = mock_redis_client

            mock_memcached_client = AsyncMock()
            mock_memcached_client.connect.return_value = True
            mock_memcached_client.set.return_value = True
            mock_memcached.return_value = mock_memcached_client

            await cache_cluster.add_node(redis_node)
            await cache_cluster.add_node(memcached_node)

            result = await cache_cluster.set("test_key", "test_value")

            assert result is True
            # Both clients should have been called (primary + replication)
            assert mock_redis_client.set.call_count >= 1
            assert mock_memcached_client.set.call_count >= 1

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_cluster, redis_node):
        """Test successful delete operation"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.delete.return_value = True
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            result = await cache_cluster.delete("test_key")

            assert result is True
            assert cache_cluster.stats['successful_requests'] == 1

    @pytest.mark.asyncio
    async def test_node_failure_detection(self, cache_cluster, redis_node):
        """Test node failure detection"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.get.side_effect = Exception("Connection failed")
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            # Trigger failure
            await cache_cluster.get("test_key")

            # Node should be marked as unhealthy after consecutive failures
            redis_node.consecutive_failures = cache_cluster.config.max_consecutive_failures
            await cache_cluster._mark_node_unhealthy(redis_node.node_id)

            assert cache_cluster.nodes[redis_node.node_id].status == NodeStatus.UNHEALTHY
            assert cache_cluster.stats['failover_events'] == 1

    @pytest.mark.asyncio
    async def test_health_check_all_nodes(self, cache_cluster, redis_node):
        """Test health checking all nodes"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.health_check.return_value = {'status': 'healthy'}
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            await cache_cluster.health_check_all_nodes()

            # Should update last health check time
            assert redis_node.last_health_check > 0

    @pytest.mark.asyncio
    async def test_get_cluster_stats(self, cache_cluster, redis_node):
        """Test getting cluster statistics"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            stats = await cache_cluster.get_cluster_stats()

            assert stats['cluster_name'] == cache_cluster.config.cluster_name
            assert stats['total_nodes'] == 1
            assert stats['healthy_nodes'] == 1
            assert redis_node.node_id in stats['node_stats']

    @pytest.mark.asyncio
    async def test_shutdown(self, cache_cluster, redis_node):
        """Test cluster shutdown"""
        with patch('src.ailoos.cache.redis_integration.RedisIntegration') as mock_redis:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_redis.return_value = mock_client

            await cache_cluster.add_node(redis_node)

            await cache_cluster.shutdown()

            assert len(cache_cluster.active_clients) == 0
            mock_client.disconnect.assert_called_once()

    def test_add_node_failure_callback(self, cache_cluster):
        """Test adding node failure callback"""
        callback_called = []

        def failure_callback(node_id):
            callback_called.append(node_id)

        cache_cluster.add_node_failure_callback(failure_callback)

        # Simulate callback trigger
        cache_cluster.node_failure_callbacks[0]("test_node")

        assert "test_node" in callback_called

    def test_add_node_recovery_callback(self, cache_cluster):
        """Test adding node recovery callback"""
        callback_called = []

        def recovery_callback(node_id):
            callback_called.append(node_id)

        cache_cluster.add_node_recovery_callback(recovery_callback)

        # Simulate callback trigger
        cache_cluster.node_recovery_callbacks[0]("test_node")

        assert "test_node" in callback_called