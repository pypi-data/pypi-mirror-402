"""
Redis Integration for Distributed Cache System
Complete Redis backend implementation with clustering support
"""

import asyncio
import json
import time
import logging
from typing import Any, Optional, Dict, List, Union, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import pickle

if TYPE_CHECKING:
    import redis.asyncio as redis

try:
    import redis.asyncio as redis
    from redis.asyncio.cluster import RedisCluster
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    RedisCluster = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class RedisConfig:
    """Configuration for Redis connection"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    cluster_mode: bool = False
    cluster_nodes: Optional[List[Dict[str, Union[str, int]]]] = None

class RedisIntegration:
    """Complete Redis integration for distributed caching"""

    def __init__(self, config: RedisConfig = None):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for Redis integration")

        self.config = config or RedisConfig()
        self.client: Optional[Any] = None
        self.is_connected = False
        self.last_health_check = 0
        self.connection_pool = None

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'connections_created': 0,
            'connections_closed': 0
        }

    async def connect(self) -> bool:
        """Establish connection to Redis"""
        try:
            if self.config.cluster_mode and self.config.cluster_nodes:
                # Cluster mode
                startup_nodes = [
                    redis.ClusterNode(node['host'], node['port'])
                    for node in self.config.cluster_nodes
                ]
                self.client = RedisCluster(
                    startup_nodes=startup_nodes,
                    password=self.config.password,
                    max_connections=self.config.max_connections,
                    retry_on_timeout=self.config.retry_on_timeout,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout
                )
            else:
                # Single node mode
                self.client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    password=self.config.password,
                    db=self.config.db,
                    max_connections=self.config.max_connections,
                    retry_on_timeout=self.config.retry_on_timeout,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    decode_responses=False  # We'll handle serialization
                )

            # Test connection
            await self.client.ping()
            self.is_connected = True
            self.stats['connections_created'] += 1
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.stats['connections_closed'] += 1
            self.is_connected = False
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return None

        try:
            start_time = time.time()
            data = await self.client.get(key)

            if data is None:
                self.stats['misses'] += 1
                return None

            # Deserialize
            value = pickle.loads(data)
            self.stats['hits'] += 1
            self.stats['bytes_read'] += len(data)

            latency = time.time() - start_time
            logger.debug(f"Redis GET {key}: {latency:.4f}s")
            return value

        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            self.stats['errors'] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return False

        try:
            start_time = time.time()

            # Serialize
            data = pickle.dumps(value)

            if ttl:
                # Convert to milliseconds for Redis
                ttl_ms = int(ttl * 1000)
                success = await self.client.psetex(key, ttl_ms, data)
            else:
                success = await self.client.set(key, data)

            if success:
                self.stats['sets'] += 1
                self.stats['bytes_written'] += len(data)

            latency = time.time() - start_time
            logger.debug(f"Redis SET {key}: {latency:.4f}s")
            return bool(success)

        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            self.stats['errors'] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.is_connected or not self.client:
            self.stats['errors'] += 1
            return False

        try:
            start_time = time.time()
            result = await self.client.delete(key)
            success = result > 0

            if success:
                self.stats['deletes'] += 1

            latency = time.time() - start_time
            logger.debug(f"Redis DELETE {key}: {latency:.4f}s")
            return success

        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            self.stats['errors'] += 1
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected or not self.client:
            return False

        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: float) -> bool:
        """Set expiration time for key"""
        if not self.is_connected or not self.client:
            return False

        try:
            ttl_seconds = int(ttl)
            return bool(await self.client.expire(key, ttl_seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> Optional[float]:
        """Get TTL for key"""
        if not self.is_connected or not self.client:
            return None

        try:
            ttl_seconds = await self.client.ttl(key)
            return float(ttl_seconds) if ttl_seconds > 0 else None
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return None

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        if not self.is_connected or not self.client:
            return []

        try:
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
            return []

    async def scan(self, pattern: str = "*", count: int = 100) -> List[str]:
        """Scan keys with pattern (more efficient than KEYS for large datasets)"""
        if not self.is_connected or not self.client:
            return []

        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern, count=count):
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                keys.append(key_str)
            return keys
        except Exception as e:
            logger.error(f"Redis SCAN error for pattern {pattern}: {e}")
            return []

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment integer value"""
        if not self.is_connected or not self.client:
            return None

        try:
            return await self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        if not self.is_connected or not self.client:
            return None

        try:
            data = await self.client.hget(key, field)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis HGET error for key {key}, field {field}: {e}")
            return None

    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field value"""
        if not self.is_connected or not self.client:
            return False

        try:
            data = pickle.dumps(value)
            return bool(await self.client.hset(key, field, data))
        except Exception as e:
            logger.error(f"Redis HSET error for key {key}, field {field}: {e}")
            return False

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.is_connected or not self.client:
            return {}

        try:
            data = await self.client.hgetall(key)
            result = {}
            for field, value_bytes in data.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                result[field_str] = pickle.loads(value_bytes)
            return result
        except Exception as e:
            logger.error(f"Redis HGETALL error for key {key}: {e}")
            return {}

    async def publish(self, channel: str, message: Any) -> bool:
        """Publish message to Redis channel"""
        if not self.is_connected or not self.client:
            return False

        try:
            message_data = json.dumps(message) if not isinstance(message, str) else message
            return bool(await self.client.publish(channel, message_data))
        except Exception as e:
            logger.error(f"Redis PUBLISH error for channel {channel}: {e}")
            return False

    async def subscribe(self, channels: List[str]) -> Optional[any]:
        """Subscribe to Redis channels"""
        if not self.is_connected or not self.client:
            return None

        try:
            pubsub = self.client.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE error for channels {channels}: {e}")
            return None

    async def pipeline(self) -> Optional[Any]:
        """Create Redis pipeline for batch operations"""
        if not self.is_connected or not self.client:
            return None

        try:
            return self.client.pipeline()
        except Exception as e:
            logger.error(f"Redis PIPELINE error: {e}")
            return None

    async def flushdb(self) -> bool:
        """Flush current database"""
        if not self.is_connected or not self.client:
            return False

        try:
            return bool(await self.client.flushdb())
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    async def dbsize(self) -> int:
        """Get number of keys in current database"""
        if not self.is_connected or not self.client:
            return 0

        try:
            return await self.client.dbsize()
        except Exception as e:
            logger.error(f"Redis DBSIZE error: {e}")
            return 0

    async def info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        if not self.is_connected or not self.client:
            return {}

        try:
            info_data = await self.client.info()
            return info_data
        except Exception as e:
            logger.error(f"Redis INFO error: {e}")
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
            await self.client.ping()
            info = await self.info()

            return {
                'status': 'healthy',
                'timestamp': current_time,
                'redis_version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'total_keys': await self.dbsize()
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.is_connected = False
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': current_time
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis integration statistics"""
        return {
            'is_connected': self.is_connected,
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'db': self.config.db,
                'cluster_mode': self.config.cluster_mode
            },
            'stats': self.stats.copy(),
            'last_health_check': self.last_health_check
        }

    async def clear_stats(self):
        """Reset statistics counters"""
        self.stats = {k: 0 for k in self.stats.keys()}