"""
Intelligent Caching Layer for AILOOS
Provides Redis-based caching with fallback to in-memory cache
"""

import json
import asyncio
import logging
from typing import Any, Optional, Dict, Callable, Union
from functools import wraps
import hashlib
import time

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..core.config import get_config

logger = logging.getLogger(__name__)

class CacheManager:
    """Intelligent cache manager with Redis backend and in-memory fallback"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize cache connections"""
        if self._initialized:
            return

        try:
            config = get_config()
            redis_url = getattr(config, 'redis_url', 'redis://localhost:6379')

            if REDIS_AVAILABLE:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info("🔴 Redis cache initialized")
            else:
                logger.warning("Redis not available, using in-memory cache only")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory cache")
            self.redis_client = None

        self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self._ensure_initialized()

        # Try Redis first
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry['expires'] > time.time():
                return entry['value']
            else:
                del self.memory_cache[key]

        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds"""
        await self._ensure_initialized()

        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache value: {e}")
            return False

        expires = time.time() + ttl

        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # Fallback to memory cache
        self.memory_cache[key] = {
            'value': value,
            'expires': expires
        }
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        await self._ensure_initialized()

        success = False

        # Try Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            success = True

        return success

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        await self._ensure_initialized()

        # Try Redis
        if self.redis_client:
            try:
                return await self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists failed: {e}")

        # Memory cache
        if key in self.memory_cache:
            return self.memory_cache[key]['expires'] > time.time()

        return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        await self._ensure_initialized()

        cleared = 0

        # Redis
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    cleared += len(keys)
            except Exception as e:
                logger.warning(f"Redis clear pattern failed: {e}")

        # Memory cache - simple implementation
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            cleared += 1

        return cleared

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        await self._ensure_initialized()

        stats = {
            'memory_cache_entries': len(self.memory_cache),
            'redis_available': self.redis_client is not None
        }

        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update({
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_used_memory': info.get('used_memory_human', 'unknown'),
                    'redis_total_keys': await self.redis_client.dbsize()
                })
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")

        return stats

    async def _ensure_initialized(self):
        """Ensure cache is initialized"""
        if not self._initialized:
            await self.initialize()

# Global cache instance
_cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    return _cache_manager

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            cache_key_full = f"{func_key}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = await cache_manager.get(cache_key_full)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key_full}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key_full, result, ttl)
            logger.debug(f"Cached result for {cache_key_full}")

            return result

        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache_manager = get_cache_manager()
            await cache_manager.clear_pattern(pattern)

            return result

        return wrapper
    return decorator

# Initialize cache on import
async def initialize_cache():
    """Initialize global cache manager"""
    await _cache_manager.initialize()

# Optional: Use distributed cache system
try:
    from ..cache import DistributedCacheManager as _DistributedCacheManager

    class HybridCacheManager:
        """Hybrid cache that can use either simple or distributed cache"""

        def __init__(self, use_distributed: bool = False, **kwargs):
            self.use_distributed = use_distributed
            if use_distributed:
                self.distributed_manager = _DistributedCacheManager(**kwargs)
                self.simple_manager = None
            else:
                self.simple_manager = CacheManager()
                self.distributed_manager = None

        async def initialize(self):
            if self.use_distributed:
                await self.distributed_manager.start()
            else:
                await self.simple_manager.initialize()

        async def get(self, key: str):
            if self.use_distributed:
                return await self.distributed_manager.get(key)
            else:
                return await self.simple_manager.get(key)

        async def set(self, key: str, value, ttl: int = 300):
            if self.use_distributed:
                return await self.distributed_manager.set(key, value, ttl)
            else:
                return await self.simple_manager.set(key, value, ttl)

        async def delete(self, key: str):
            if self.use_distributed:
                return await self.distributed_manager.delete(key)
            else:
                return await self.simple_manager.delete(key)

        async def exists(self, key: str):
            if self.use_distributed:
                return await self.distributed_manager.exists(key)
            else:
                return await self.simple_manager.exists(key)

        async def clear_pattern(self, pattern: str):
            if self.use_distributed:
                return await self.distributed_manager.invalidate_pattern(pattern)
            else:
                return await self.simple_manager.clear_pattern(pattern)

        async def get_stats(self):
            if self.use_distributed:
                return await self.distributed_manager.get_stats()
            else:
                return await self.simple_manager.get_stats()

    # Global hybrid cache instance
    _hybrid_cache_manager = None

    def get_hybrid_cache_manager(use_distributed: bool = False, **kwargs) -> HybridCacheManager:
        """Get hybrid cache manager (simple or distributed)"""
        global _hybrid_cache_manager
        if _hybrid_cache_manager is None or _hybrid_cache_manager.use_distributed != use_distributed:
            _hybrid_cache_manager = HybridCacheManager(use_distributed=use_distributed, **kwargs)
        return _hybrid_cache_manager

except ImportError:
    # Distributed cache not available
    def get_hybrid_cache_manager(use_distributed: bool = False, **kwargs):
        """Fallback to simple cache when distributed is not available"""
        if use_distributed:
            raise ImportError("Distributed cache system not available. Install required dependencies.")
        return get_cache_manager()

# Cache initialization is handled by the application startup