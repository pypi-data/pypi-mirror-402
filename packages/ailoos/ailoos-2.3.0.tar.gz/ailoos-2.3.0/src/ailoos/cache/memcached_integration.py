"""
Memcached Integration for Distributed Cache System
Complete Memcached backend implementation with multi-server support
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List, Union, Tuple
from dataclasses import dataclass
import pickle
import hashlib

try:
    from pymemcache.client.base import Client as MemcachedClient
    from pymemcache.client.hash import HashClient
    from pymemcache.exceptions import MemcacheError
    MEMCACHED_AVAILABLE = True
except ImportError:
    MemcachedClient = None
    HashClient = None
    MemcacheError = Exception
    MEMCACHED_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MemcachedConfig:
    """Configuration for Memcached connection"""
    servers: List[Tuple[str, int]] = None  # List of (host, port) tuples
    default_server: Tuple[str, int] = ("localhost", 11211)
    timeout: float = 5.0
    connect_timeout: float = 5.0
    retry_attempts: int = 3
    retry_delay: float = 0.1
    key_prefix: str = ""
    key_hash_function: callable = None
    use_pooling: bool = True
    pool_size: int = 4
    health_check_interval: int = 30
    compression: bool = True
    compression_threshold: int = 1024  # Compress values larger than 1KB

    def __post_init__(self):
        if self.servers is None:
            self.servers = [self.default_server]

class MemcachedIntegration:
    """Complete Memcached integration for distributed caching"""

    def __init__(self, config: MemcachedConfig = None):
        if not MEMCACHED_AVAILABLE:
            raise ImportError("pymemcache package is required for Memcached integration")

        self.config = config or MemcachedConfig()
        self.client: Optional[Union[MemcachedClient, HashClient]] = None
        self.is_connected = False
        self.last_health_check = 0

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'compression_savings': 0,
            'connections_created': 0,
            'connections_closed': 0
        }

    async def connect(self) -> bool:
        """Establish connection to Memcached"""
        try:
            loop = asyncio.get_event_loop()

            if len(self.config.servers) > 1:
                # Multi-server setup
                servers = [f"{host}:{port}" for host, port in self.config.servers]
                self.client = HashClient(
                    servers,
                    timeout=self.config.timeout,
                    connect_timeout=self.config.connect_timeout,
                    retry_attempts=self.config.retry_attempts,
                    retry_delay=self.config.retry_delay,
                    key_prefix=self.config.key_prefix,
                    hashclient=self.config.key_hash_function
                )
            else:
                # Single server
                host, port = self.config.servers[0]
                self.client = MemcachedClient(
                    (host, port),
                    timeout=self.config.timeout,
                    connect_timeout=self.config.connect_timeout,
                    retry_attempts=self.config.retry_attempts,
                    retry_delay=self.config.retry_delay,
                    key_prefix=self.config.key_prefix
                )

            # Test connection with a simple operation
            test_key = f"_health_check_{int(time.time())}"
            await self._execute_async('set', test_key, b'1', 10)
            await self._execute_async('delete', test_key)

            self.is_connected = True
            self.stats['connections_created'] += 1
            logger.info(f"Connected to Memcached servers: {[f'{h}:{p}' for h, p in self.config.servers]}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Memcached: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close Memcached connection"""
        if self.client:
            try:
                if hasattr(self.client, 'close'):
                    self.client.close()
                elif hasattr(self.client, 'disconnect_all'):
                    self.client.disconnect_all()
                self.stats['connections_closed'] += 1
                self.is_connected = False
                logger.info("Disconnected from Memcached")
            except Exception as e:
                logger.error(f"Error disconnecting from Memcached: {e}")

    async def _execute_async(self, operation: str, *args, **kwargs):
        """Execute Memcached operation asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, getattr(self.client, operation), *args, **kwargs)

    def _make_key(self, key: str) -> str:
        """Create prefixed key"""
        if self.config.key_prefix:
            return f"{self.config.key_prefix}:{key}"
        return key

    def _should_compress(self, data: bytes) -> bool:
        """Check if data should be compressed"""
        return self.config.compression and len(data) > self.config.compression_threshold

    def _compress_data(self, data: bytes) -> Tuple[bytes, bool]:
        """Compress data if needed"""
        import zlib

        if self._should_compress(data):
            compressed = zlib.compress(data)
            if len(compressed) < len(data):  # Only use compression if it saves space
                return compressed, True
        return data, False

    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """Decompress data if needed"""
        import zlib

        if compressed:
            return zlib.decompress(data)
        return data

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Memcached"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return None

        try:
            start_time = time.time()
            mem_key = self._make_key(key)

            data = await self._execute_async('get', mem_key)

            if data is None:
                self.stats['misses'] += 1
                return None

            # Data format: compressed_flag (1 byte) + data
            compressed_flag = data[0:1]
            value_data = data[1:]

            compressed = compressed_flag == b'1'
            decompressed_data = self._decompress_data(value_data, compressed)

            # Deserialize
            value = pickle.loads(decompressed_data)
            self.stats['hits'] += 1
            self.stats['bytes_read'] += len(data)

            latency = time.time() - start_time
            logger.debug(f"Memcached GET {key}: {latency:.4f}s")
            return value

        except Exception as e:
            logger.error(f"Memcached GET error for key {key}: {e}")
            self.stats['errors'] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in Memcached with optional TTL"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return False

        try:
            start_time = time.time()

            # Serialize
            data = pickle.dumps(value)

            # Compress if needed
            compressed_data, compressed = self._compress_data(data)

            # Add compression flag
            final_data = (b'1' if compressed else b'0') + compressed_data

            mem_key = self._make_key(key)
            expire_time = int(ttl) if ttl else 0

            success = await self._execute_async('set', mem_key, final_data, expire_time)

            if success:
                self.stats['sets'] += 1
                self.stats['bytes_written'] += len(final_data)
                if compressed:
                    self.stats['compression_savings'] += (len(data) - len(compressed_data))

            latency = time.time() - start_time
            logger.debug(f"Memcached SET {key}: {latency:.4f}s")
            return bool(success)

        except Exception as e:
            logger.error(f"Memcached SET error for key {key}: {e}")
            self.stats['errors'] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Memcached"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return False

        try:
            start_time = time.time()
            mem_key = self._make_key(key)

            result = await self._execute_async('delete', mem_key)
            success = result is True  # Memcached returns True on success, False on not found

            if success:
                self.stats['deletes'] += 1

            latency = time.time() - start_time
            logger.debug(f"Memcached DELETE {key}: {latency:.4f}s")
            return success

        except Exception as e:
            logger.error(f"Memcached DELETE error for key {key}: {e}")
            self.stats['errors'] += 1
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Memcached"""
        if not self.is_connected or not self.client:
            return False

        try:
            mem_key = self._make_key(key)
            data = await self._execute_async('get', mem_key)
            return data is not None
        except Exception as e:
            logger.error(f"Memcached EXISTS error for key {key}: {e}")
            return False

    async def touch(self, key: str, ttl: float) -> bool:
        """Update expiration time for key"""
        if not self.is_connected or not self.client:
            return False

        try:
            mem_key = self._make_key(key)
            expire_time = int(ttl)
            return bool(await self._execute_async('touch', mem_key, expire_time))
        except Exception as e:
            logger.error(f"Memcached TOUCH error for key {key}: {e}")
            return False

    async def incr(self, key: str, amount: int = 1, initial_value: int = 0) -> Optional[int]:
        """Increment integer value"""
        if not self.is_connected or not self.client:
            return None

        try:
            mem_key = self._make_key(key)
            return await self._execute_async('incr', mem_key, amount, default=initial_value)
        except Exception as e:
            logger.error(f"Memcached INCR error for key {key}: {e}")
            return None

    async def decr(self, key: str, amount: int = 1, initial_value: int = 0) -> Optional[int]:
        """Decrement integer value"""
        if not self.is_connected or not self.client:
            return None

        try:
            mem_key = self._make_key(key)
            return await self._execute_async('decr', mem_key, amount, default=initial_value)
        except Exception as e:
            logger.error(f"Memcached DECR error for key {key}: {e}")
            return None

    async def append(self, key: str, value: bytes) -> bool:
        """Append data to existing key"""
        if not self.is_connected or not self.client:
            return False

        try:
            mem_key = self._make_key(key)
            return bool(await self._execute_async('append', mem_key, value))
        except Exception as e:
            logger.error(f"Memcached APPEND error for key {key}: {e}")
            return False

    async def prepend(self, key: str, value: bytes) -> bool:
        """Prepend data to existing key"""
        if not self.is_connected or not self.client:
            return False

        try:
            mem_key = self._make_key(key)
            return bool(await self._execute_async('prepend', mem_key, value))
        except Exception as e:
            logger.error(f"Memcached PREPEND error for key {key}: {e}")
            return False

    async def cas(self, key: str, value: Any, cas_token: int, ttl: Optional[float] = None) -> bool:
        """Check and set operation"""
        if not self.is_connected or not self.client:
            return False

        try:
            # Serialize
            data = pickle.dumps(value)
            compressed_data, compressed = self._compress_data(data)
            final_data = (b'1' if compressed else b'0') + compressed_data

            mem_key = self._make_key(key)
            expire_time = int(ttl) if ttl else 0

            success = await self._execute_async('cas', mem_key, final_data, cas_token, expire_time)
            return bool(success)

        except Exception as e:
            logger.error(f"Memcached CAS error for key {key}: {e}")
            return False

    async def gets(self, key: str) -> Optional[Tuple[Any, int]]:
        """Get value with CAS token"""
        if not self.is_connected or not self.client:
            return None

        try:
            mem_key = self._make_key(key)
            result = await self._execute_async('gets', mem_key)

            if result is None:
                return None

            data, cas_token = result

            # Data format: compressed_flag (1 byte) + data
            compressed_flag = data[0:1]
            value_data = data[1:]

            compressed = compressed_flag == b'1'
            decompressed_data = self._decompress_data(value_data, compressed)

            # Deserialize
            value = pickle.loads(decompressed_data)
            return value, cas_token

        except Exception as e:
            logger.error(f"Memcached GETS error for key {key}: {e}")
            return None

    async def flush_all(self, delay: int = 0) -> bool:
        """Flush all data from Memcached"""
        if not self.is_connected or not self.client:
            return False

        try:
            return bool(await self._execute_async('flush_all', delay))
        except Exception as e:
            logger.error(f"Memcached FLUSH_ALL error: {e}")
            return False

    async def stats(self, stat_args: Optional[str] = None) -> Dict[str, Any]:
        """Get Memcached statistics"""
        if not self.is_connected or not self.client:
            return {}

        try:
            stats_data = await self._execute_async('stats', stat_args)
            return dict(stats_data) if stats_data else {}
        except Exception as e:
            logger.error(f"Memcached STATS error: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        current_time = time.time()

        # Only check every health_check_interval seconds
        if current_time - self.last_health_check < self.config.health_check_interval:
            return {
                'status': 'healthy' if self.is_connected else 'disconnected',
                'last_check': self.last_health_check,
                'cached': True
            }

        self.last_health_check = current_time

        if not self.client:
            return {
                'status': 'disconnected',
                'error': 'No client initialized',
                'timestamp': current_time
            }

        try:
            # Test with a simple operation
            test_key = f"_health_check_{int(current_time)}"
            await self.set(test_key, "test", 10)
            await self.delete(test_key)

            # Get stats
            server_stats = await self.stats()

            return {
                'status': 'healthy',
                'timestamp': current_time,
                'servers': [f"{h}:{p}" for h, p in self.config.servers],
                'total_items': server_stats.get('total_items', 'unknown'),
                'bytes_used': server_stats.get('bytes', 'unknown'),
                'connections': server_stats.get('curr_connections', 'unknown')
            }

        except Exception as e:
            logger.error(f"Memcached health check failed: {e}")
            self.is_connected = False
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': current_time
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get Memcached integration statistics"""
        return {
            'is_connected': self.is_connected,
            'config': {
                'servers': [f"{h}:{p}" for h, p in self.config.servers],
                'key_prefix': self.config.key_prefix,
                'compression': self.config.compression
            },
            'stats': self.stats.copy(),
            'last_health_check': self.last_health_check
        }

    async def clear_stats(self):
        """Reset statistics counters"""
        self.stats = {k: 0 for k in self.stats.keys()}