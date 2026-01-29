"""
Tests for Redis Integration
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from src.ailoos.cache.redis_integration import RedisIntegration, RedisConfig


class TestRedisIntegration:
    """Test Redis integration functionality"""

    @pytest.fixture
    def redis_config(self):
        """Redis configuration fixture"""
        return RedisConfig(
            host="localhost",
            port=6379,
            db=1,
            password=None
        )

    @pytest.fixture
    def redis_integration(self, redis_config):
        """Redis integration fixture"""
        return RedisIntegration(redis_config)

    @pytest.mark.asyncio
    async def test_initialization(self, redis_integration, redis_config):
        """Test Redis integration initialization"""
        assert redis_integration.config == redis_config
        assert redis_integration.client is None
        assert not redis_integration.is_connected
        assert redis_integration.stats['connections_created'] == 0

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_integration):
        """Test successful Redis connection"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client

            result = await redis_integration.connect()

            assert result is True
            assert redis_integration.is_connected
            assert redis_integration.client == mock_client
            assert redis_integration.stats['connections_created'] == 1
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, redis_integration):
        """Test Redis connection failure"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_client = AsyncMock()
            mock_client.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_client

            result = await redis_integration.connect()

            assert result is False
            assert not redis_integration.is_connected
            assert redis_integration.stats['connections_created'] == 0

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_integration):
        """Test Redis disconnection"""
        # Setup connected state
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()

        await redis_integration.disconnect()

        assert not redis_integration.is_connected
        assert redis_integration.stats['connections_closed'] == 1
        redis_integration.client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hit(self, redis_integration):
        """Test successful cache get"""
        # Setup
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        test_data = b'\x80\x03}q\x00(X\x03\x00\x00\x00keyq\x01X\x05\x00\x00\x00valueq\x02u.'  # Pickled dict
        redis_integration.client.get.return_value = test_data

        result = await redis_integration.get("test_key")

        assert result == {"key": "value"}
        assert redis_integration.stats['hits'] == 1
        assert redis_integration.stats['bytes_read'] == len(test_data)
        redis_integration.client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_miss(self, redis_integration):
        """Test cache get miss"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.get.return_value = None

        result = await redis_integration.get("test_key")

        assert result is None
        assert redis_integration.stats['misses'] == 1

    @pytest.mark.asyncio
    async def test_get_disconnected(self, redis_integration):
        """Test get when disconnected"""
        redis_integration.is_connected = False

        result = await redis_integration.get("test_key")

        assert result is None
        assert redis_integration.stats['errors'] == 1

    @pytest.mark.asyncio
    async def test_set_success(self, redis_integration):
        """Test successful cache set"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.set.return_value = True

        result = await redis_integration.set("test_key", {"data": "value"})

        assert result is True
        assert redis_integration.stats['sets'] == 1
        redis_integration.client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_integration):
        """Test cache set with TTL"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.psetex.return_value = True

        result = await redis_integration.set("test_key", "value", ttl=300)

        assert result is True
        redis_integration.client.psetex.assert_called_once_with("test_key", 300000, pytest.any())  # 300 seconds in ms

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_integration):
        """Test successful cache delete"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.delete.return_value = 1

        result = await redis_integration.delete("test_key")

        assert result is True
        assert redis_integration.stats['deletes'] == 1

    @pytest.mark.asyncio
    async def test_exists_true(self, redis_integration):
        """Test key exists"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.exists.return_value = 1

        result = await redis_integration.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_expire(self, redis_integration):
        """Test setting expiration"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.expire.return_value = True

        result = await redis_integration.expire("test_key", 300)

        assert result is True
        redis_integration.client.expire.assert_called_once_with("test_key", 300)

    @pytest.mark.asyncio
    async def test_ttl(self, redis_integration):
        """Test getting TTL"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.ttl.return_value = 250

        result = await redis_integration.ttl("test_key")

        assert result == 250.0

    @pytest.mark.asyncio
    async def test_keys_pattern(self, redis_integration):
        """Test getting keys with pattern"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.keys.return_value = [b"key1", b"key2"]

        result = await redis_integration.keys("test_*")

        assert result == ["key1", "key2"]
        redis_integration.client.keys.assert_called_once_with("test_*")

    @pytest.mark.asyncio
    async def test_incr(self, redis_integration):
        """Test increment operation"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.incr.return_value = 5

        result = await redis_integration.incr("counter", 2)

        assert result == 5
        redis_integration.client.incr.assert_called_once_with("counter", 2)

    @pytest.mark.asyncio
    async def test_hget_hset(self, redis_integration):
        """Test hash operations"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()

        # Test HSET
        redis_integration.client.hset.return_value = True
        result = await redis_integration.hset("hash_key", "field", {"nested": "data"})
        assert result is True

        # Test HGET
        test_data = b'\x80\x03}q\x00(X\x06\x00\x00\x00nestedq\x01X\x04\x00\x00\x00dataq\x02u.'
        redis_integration.client.hget.return_value = test_data
        result = await redis_integration.hget("hash_key", "field")
        assert result == {"nested": "data"}

    @pytest.mark.asyncio
    async def test_publish(self, redis_integration):
        """Test publish operation"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.publish.return_value = 5

        result = await redis_integration.publish("channel", {"message": "data"})

        assert result is True
        redis_integration.client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, redis_integration):
        """Test health check when healthy"""
        redis_integration.is_connected = True
        redis_integration.client = AsyncMock()
        redis_integration.client.ping.return_value = True
        redis_integration.client.info.return_value = {
            "redis_version": "7.0.0",
            "connected_clients": "5",
            "used_memory_human": "1.2M",
            "total_keys": 100
        }
        redis_integration.client.dbsize.return_value = 100

        result = await redis_integration.health_check()

        assert result['status'] == 'healthy'
        assert 'redis_version' in result
        assert result['total_keys'] == 100

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, redis_integration):
        """Test health check when unhealthy"""
        redis_integration.client = AsyncMock()
        redis_integration.client.ping.side_effect = Exception("Connection failed")

        result = await redis_integration.health_check()

        assert result['status'] == 'unhealthy'
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_get_stats(self, redis_integration):
        """Test getting statistics"""
        redis_integration.stats['hits'] = 10
        redis_integration.stats['misses'] = 2

        stats = redis_integration.get_stats()

        assert stats['is_connected'] == redis_integration.is_connected
        assert stats['stats']['hits'] == 10
        assert stats['stats']['misses'] == 2

    @pytest.mark.asyncio
    async def test_clear_stats(self, redis_integration):
        """Test clearing statistics"""
        redis_integration.stats['hits'] = 10
        redis_integration.stats['errors'] = 5

        await redis_integration.clear_stats()

        assert redis_integration.stats['hits'] == 0
        assert redis_integration.stats['errors'] == 0