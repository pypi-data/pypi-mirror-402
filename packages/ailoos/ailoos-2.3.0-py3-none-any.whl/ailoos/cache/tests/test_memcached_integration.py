"""
Tests for Memcached Integration
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from src.ailoos.cache.memcached_integration import MemcachedIntegration, MemcachedConfig


class TestMemcachedIntegration:
    """Test Memcached integration functionality"""

    @pytest.fixture
    def memcached_config(self):
        """Memcached configuration fixture"""
        return MemcachedConfig(
            servers=[("localhost", 11211), ("localhost", 11212)],
            key_prefix="test:"
        )

    @pytest.fixture
    def memcached_integration(self, memcached_config):
        """Memcached integration fixture"""
        return MemcachedIntegration(memcached_config)

    @pytest.mark.asyncio
    async def test_initialization(self, memcached_integration, memcached_config):
        """Test Memcached integration initialization"""
        assert memcached_integration.config == memcached_config
        assert memcached_integration.client is None
        assert not memcached_integration.is_connected
        assert memcached_integration.stats['connections_created'] == 0

    @pytest.mark.asyncio
    async def test_connect_success(self, memcached_integration):
        """Test successful Memcached connection"""
        with patch('pymemcache.client.hash.HashClient') as mock_hash_client:
            mock_client = AsyncMock()
            mock_hash_client.return_value = mock_client

            # Mock the set operations for connection test
            mock_client.set.return_value = True

            result = await memcached_integration.connect()

            assert result is True
            assert memcached_integration.is_connected
            assert memcached_integration.client == mock_client
            assert memcached_integration.stats['connections_created'] == 1

    @pytest.mark.asyncio
    async def test_connect_failure(self, memcached_integration):
        """Test Memcached connection failure"""
        with patch('pymemcache.client.hash.HashClient') as mock_hash_client:
            mock_client = AsyncMock()
            mock_client.set.side_effect = Exception("Connection failed")
            mock_hash_client.return_value = mock_client

            result = await memcached_integration.connect()

            assert result is False
            assert not memcached_integration.is_connected

    @pytest.mark.asyncio
    async def test_disconnect(self, memcached_integration):
        """Test Memcached disconnection"""
        memcached_integration.is_connected = True
        memcached_integration.client = Mock()
        memcached_integration.client.close = Mock()

        await memcached_integration.disconnect()

        assert not memcached_integration.is_connected
        assert memcached_integration.stats['connections_closed'] == 1
        memcached_integration.client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hit(self, memcached_integration):
        """Test successful cache get"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()

        # Mock compressed data (flag + pickled data)
        test_data = b'0\x80\x03}q\x00(X\x03\x00\x00\x00keyq\x01X\x05\x00\x00\x00valueq\x02u.'
        memcached_integration.client.get.return_value = test_data

        result = await memcached_integration.get("test_key")

        assert result == {"key": "value"}
        assert memcached_integration.stats['hits'] == 1
        memcached_integration.client.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_get_miss(self, memcached_integration):
        """Test cache get miss"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.get.return_value = None

        result = await memcached_integration.get("test_key")

        assert result is None
        assert memcached_integration.stats['misses'] == 1

    @pytest.mark.asyncio
    async def test_get_compressed(self, memcached_integration):
        """Test getting compressed data"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()

        # Mock compressed data
        import zlib
        original_data = b'\x80\x03}q\x00(X\x03\x00\x00\x00keyq\x01X\x05\x00\x00\x00valueq\x02u.'
        compressed_data = zlib.compress(original_data)
        final_data = b'1' + compressed_data

        memcached_integration.client.get.return_value = final_data

        result = await memcached_integration.get("test_key")

        assert result == {"key": "value"}
        assert memcached_integration.stats['compression_savings'] == 0  # Would be calculated during set

    @pytest.mark.asyncio
    async def test_set_success(self, memcached_integration):
        """Test successful cache set"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.set.return_value = True

        result = await memcached_integration.set("test_key", {"data": "value"})

        assert result is True
        assert memcached_integration.stats['sets'] == 1

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, memcached_integration):
        """Test cache set with TTL"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.set.return_value = True

        result = await memcached_integration.set("test_key", "value", ttl=300)

        assert result is True
        # Verify set was called with expire parameter
        call_args = memcached_integration.client.set.call_args
        assert call_args[0][2] == 300  # expire_time parameter

    @pytest.mark.asyncio
    async def test_delete_success(self, memcached_integration):
        """Test successful cache delete"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.delete.return_value = True

        result = await memcached_integration.delete("test_key")

        assert result is True
        assert memcached_integration.stats['deletes'] == 1

    @pytest.mark.asyncio
    async def test_exists_true(self, memcached_integration):
        """Test key exists"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.get.return_value = b'data'

        result = await memcached_integration.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_touch(self, memcached_integration):
        """Test updating expiration"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.touch.return_value = True

        result = await memcached_integration.touch("test_key", 300)

        assert result is True
        memcached_integration.client.touch.assert_called_once_with("test:key", 300)

    @pytest.mark.asyncio
    async def test_incr(self, memcached_integration):
        """Test increment operation"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.incr.return_value = 5

        result = await memcached_integration.incr("counter", 2)

        assert result == 5
        memcached_integration.client.incr.assert_called_once_with("test:counter", 2, default=0)

    @pytest.mark.asyncio
    async def test_decr(self, memcached_integration):
        """Test decrement operation"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.decr.return_value = 3

        result = await memcached_integration.decr("counter", 2)

        assert result == 3
        memcached_integration.client.decr.assert_called_once_with("test:counter", 2, default=0)

    @pytest.mark.asyncio
    async def test_append(self, memcached_integration):
        """Test append operation"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.append.return_value = True

        result = await memcached_integration.append("test_key", b"_suffix")

        assert result is True
        memcached_integration.client.append.assert_called_once_with("test:test_key", b"_suffix")

    @pytest.mark.asyncio
    async def test_prepend(self, memcached_integration):
        """Test prepend operation"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.prepend.return_value = True

        result = await memcached_integration.prepend("test_key", b"prefix_")

        assert result is True
        memcached_integration.client.prepend.assert_called_once_with("test:test_key", b"prefix_")

    @pytest.mark.asyncio
    async def test_cas_operations(self, memcached_integration):
        """Test check-and-set operations"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()

        # Test GETS
        cas_data = (b'data', 12345)
        memcached_integration.client.gets.return_value = cas_data

        result = await memcached_integration.gets("test_key")
        assert result is not None
        assert result[1] == 12345  # CAS token

        # Test CAS
        memcached_integration.client.cas.return_value = True
        result = await memcached_integration.cas("test_key", "new_value", 12345)
        assert result is True

    @pytest.mark.asyncio
    async def test_flush_all(self, memcached_integration):
        """Test flush all operation"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        memcached_integration.client.flush_all.return_value = True

        result = await memcached_integration.flush_all()

        assert result is True
        memcached_integration.client.flush_all.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_stats_operation(self, memcached_integration):
        """Test stats retrieval"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()
        mock_stats = {"total_items": "100", "bytes": "1024000"}
        memcached_integration.client.stats.return_value = mock_stats

        result = await memcached_integration.stats()

        assert result == mock_stats

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, memcached_integration):
        """Test health check when healthy"""
        memcached_integration.is_connected = True
        memcached_integration.client = AsyncMock()

        # Mock successful operations
        memcached_integration.client.set.return_value = True
        memcached_integration.client.delete.return_value = True

        mock_server_stats = {"total_items": "50", "bytes": "512000", "curr_connections": "10"}
        memcached_integration.client.stats.return_value = mock_server_stats

        result = await memcached_integration.health_check()

        assert result['status'] == 'healthy'
        assert 'total_items' in result
        assert result['connections'] == '10'

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, memcached_integration):
        """Test health check when unhealthy"""
        memcached_integration.client = AsyncMock()
        memcached_integration.client.set.side_effect = Exception("Connection failed")

        result = await memcached_integration.health_check()

        assert result['status'] == 'unhealthy'
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_get_stats(self, memcached_integration):
        """Test getting statistics"""
        memcached_integration.stats['hits'] = 15
        memcached_integration.stats['compression_savings'] = 1024

        stats = memcached_integration.get_stats()

        assert stats['is_connected'] == memcached_integration.is_connected
        assert stats['stats']['hits'] == 15
        assert stats['stats']['compression_savings'] == 1024

    @pytest.mark.asyncio
    async def test_clear_stats(self, memcached_integration):
        """Test clearing statistics"""
        memcached_integration.stats['hits'] = 20
        memcached_integration.stats['errors'] = 3

        await memcached_integration.clear_stats()

        assert memcached_integration.stats['hits'] == 0
        assert memcached_integration.stats['errors'] == 0

    @pytest.mark.asyncio
    async def test_compression_logic(self, memcached_integration):
        """Test compression logic"""
        # Test small data (no compression)
        small_data = b'small'
        compressed_data, is_compressed = memcached_integration._compress_data(small_data)
        assert not is_compressed
        assert compressed_data == small_data

        # Test large data (should compress)
        large_data = b'x' * 2000  # 2000 bytes
        compressed_data, is_compressed = memcached_integration._compress_data(large_data)
        assert is_compressed
        assert len(compressed_data) < len(large_data)