"""
Distributed Cache Manager - Central coordinator for intelligent distributed caching
Integrates all cache components: strategies, compression, invalidation, metrics, P2P sync,
Redis, Memcached, clustering, and advanced monitoring
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List, Callable, Union
from concurrent.futures import ThreadPoolExecutor
import threading

from .strategies import IntelligentCacheStrategy
from .compression import CacheCompression, CompressedCacheEntry
from .invalidation import CacheInvalidation, SmartInvalidation
from .metrics import CacheMetricsMonitor
from .synchronization import P2PCacheSynchronization, SyncMessage
from .redis_integration import RedisIntegration, RedisConfig
from .memcached_integration import MemcachedIntegration, MemcachedConfig
from .cache_cluster import CacheCluster, ClusterConfig, CacheNode, CacheBackend
from .cache_monitoring import CacheMonitoring

logger = logging.getLogger(__name__)

class DistributedCacheManager:
    """Central manager for distributed intelligent cache system"""

    def __init__(self,
                 node_id: str,
                 strategy: str = 'adaptive',
                 max_size: int = 10000,
                 compression_type: str = 'zlib',
                 enable_p2p: bool = True,
                 known_nodes: List[str] = None,
                 enable_prometheus: bool = False,
                 redis_config: Optional[RedisConfig] = None,
                 memcached_config: Optional[MemcachedConfig] = None,
                 cluster_config: Optional[ClusterConfig] = None,
                 enable_advanced_monitoring: bool = True):
        """
        Initialize distributed cache manager

        Args:
            node_id: Unique identifier for this cache node
            strategy: Cache replacement strategy ('lru', 'lfu', 'arc', 'adaptive')
            max_size: Maximum number of entries in cache
            compression_type: Compression algorithm ('zlib', 'gzip', 'lz4')
            enable_p2p: Whether to enable P2P synchronization
            known_nodes: List of known peer nodes
            enable_prometheus: Whether to enable Prometheus metrics
            redis_config: Redis configuration for Redis backend
            memcached_config: Memcached configuration for Memcached backend
            cluster_config: Cluster configuration for multi-node setup
            enable_advanced_monitoring: Whether to enable advanced monitoring
        """
        self.node_id = node_id
        self.is_running = False

        # Core components
        self.strategy = IntelligentCacheStrategy(strategy, max_size)
        self.compression = CacheCompression(compression_type=compression_type)
        self.invalidation = CacheInvalidation()
        self.smart_invalidation = SmartInvalidation(self.invalidation)
        self.metrics = CacheMetricsMonitor(node_id, enable_prometheus)

        # Backend integrations
        self.redis = None
        if redis_config:
            self.redis = RedisIntegration(redis_config)

        self.memcached = None
        if memcached_config:
            self.memcached = MemcachedIntegration(memcached_config)

        # Cluster management
        self.cluster = None
        if cluster_config:
            self.cluster = CacheCluster(cluster_config)

        # Advanced monitoring
        self.advanced_monitoring = None
        if enable_advanced_monitoring:
            self.advanced_monitoring = CacheMonitoring(node_id, enable_prometheus)

        # P2P synchronization
        self.p2p_sync = None
        if enable_p2p:
            self.p2p_sync = P2PCacheSynchronization(
                node_id=node_id,
                known_nodes=known_nodes or []
            )
            self._setup_p2p_callbacks()

        # Cache storage: key -> CompressedCacheEntry
        self.cache: Dict[str, CompressedCacheEntry] = {}

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()

        # Initialization
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Setup internal callbacks between components"""

        # Invalidation callbacks
        self.invalidation.add_invalidation_listener(self._on_invalidation)

        # P2P callbacks if enabled
        if self.p2p_sync:
            self.p2p_sync.set_entry_update_callback(self._on_p2p_entry_update)
            self.p2p_sync.set_invalidation_callback(self._on_p2p_invalidation)

    def _setup_p2p_callbacks(self):
        """Setup P2P message handling"""
        def send_message(target_node: str, message: SyncMessage):
            # In a real implementation, this would send over network
            # For now, it's a placeholder for network communication
            logger.debug(f"Would send {message.message_type} to {target_node}")

        self.p2p_sync.set_message_callback(send_message)

    async def start(self):
        """Start the distributed cache manager"""
        if self.is_running:
            return

        logger.info(f"Starting Distributed Cache Manager for node {self.node_id}")

        # Start backend connections
        if self.redis:
            if not await self.redis.connect():
                logger.warning("Failed to connect to Redis backend")

        if self.memcached:
            if not await self.memcached.connect():
                logger.warning("Failed to connect to Memcached backend")

        # Start cluster if configured
        if self.cluster:
            # Add this node to cluster if backends are available
            if self.redis:
                redis_node = CacheNode(
                    node_id=f"{self.node_id}_redis",
                    backend=CacheBackend.REDIS,
                    config=self.redis.config
                )
                await self.cluster.add_node(redis_node)

            if self.memcached:
                memcached_node = CacheNode(
                    node_id=f"{self.node_id}_memcached",
                    backend=CacheBackend.MEMCACHED,
                    config=self.memcached.config
                )
                await self.cluster.add_node(memcached_node)

        # Start TTL monitoring
        await self.invalidation.start_ttl_monitor()

        # Start P2P sync if enabled
        if self.p2p_sync:
            await self.p2p_sync.start()

        # Start metrics monitoring
        asyncio.create_task(self.metrics.start_monitoring())

        # Start advanced monitoring
        if self.advanced_monitoring:
            await self.advanced_monitoring.start_monitoring()

        self.is_running = True
        logger.info("Distributed Cache Manager started successfully")

    async def stop(self):
        """Stop the distributed cache manager"""
        if not self.is_running:
            return

        logger.info("Stopping Distributed Cache Manager")

        # Stop advanced monitoring
        if self.advanced_monitoring:
            await self.advanced_monitoring.stop_monitoring()

        # Stop cluster
        if self.cluster:
            await self.cluster.shutdown()

        # Disconnect backends
        if self.redis:
            await self.redis.disconnect()

        if self.memcached:
            await self.memcached.disconnect()

        # Stop components
        await self.invalidation.stop_ttl_monitor()
        if self.p2p_sync:
            await self.p2p_sync.stop()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        self.is_running = False
        logger.info("Distributed Cache Manager stopped")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()

        # Try cluster first if available
        if self.cluster:
            value = await self.cluster.get(key)
            if value is not None:
                latency = time.time() - start_time
                self.metrics.record_hit(latency)
                return value

        # Fall back to local cache
        with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                # Try backends if available
                value = await self._get_from_backends(key)
                if value is not None:
                    latency = time.time() - start_time
                    self.metrics.record_hit(latency)
                    return value

                self.metrics.record_miss(time.time() - start_time)
                return None

            if entry.is_expired():
                # Entry expired, remove it
                del self.cache[key]
                await self.invalidation.invalidate_key(key, "expired")
                self.metrics.record_miss(time.time() - start_time)
                return None

            # Update access patterns for smart invalidation
            self.smart_invalidation.record_access(key)

            # Get decompressed value
            value = entry.get_value()

            # Update strategy
            strategy_entry = self.strategy.get(key)
            if strategy_entry:
                # Update strategy metadata if needed
                pass

            latency = time.time() - start_time
            self.metrics.record_hit(latency)

            return value

    async def _get_from_backends(self, key: str) -> Optional[Any]:
        """Get value from backend stores (Redis/Memcached)"""
        # Try Redis first
        if self.redis and self.redis.is_connected:
            value = await self.redis.get(key)
            if value is not None:
                return value

        # Try Memcached
        if self.memcached and self.memcached.is_connected:
            value = await self.memcached.get(key)
            if value is not None:
                return value

        return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache with optional TTL"""
        start_time = time.time()

        # Try cluster first if available
        if self.cluster:
            success = await self.cluster.set(key, value, ttl)
            if success:
                latency = time.time() - start_time
                self.metrics.record_set(latency, len(str(value).encode('utf-8')))
                return True

        # Fall back to local cache and backends
        with self._lock:
            # Create compressed entry
            entry = CompressedCacheEntry(key, value, self.compression, ttl)

            # Check if we should compress
            original_size = len(str(value).encode('utf-8'))
            compressed_size = entry.get_size()

            # Record compression metrics
            self.metrics.record_compression(original_size, compressed_size)

            # Add to cache
            self.cache[key] = entry

            # Update strategy
            self.strategy.put(key, value, compressed_size, ttl)

            # Set TTL in invalidation system
            if ttl:
                self.invalidation.set_ttl(key, ttl)

            # Update access patterns
            self.smart_invalidation.record_write(key)

            # Store in backends
            await self._set_in_backends(key, value, ttl)

            # P2P sync
            if self.p2p_sync:
                self.p2p_sync.update_local_entry(key, value, ttl)

            latency = time.time() - start_time
            self.metrics.record_set(latency, compressed_size)

            return True

    async def _set_in_backends(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in backend stores (Redis/Memcached)"""
        # Store in Redis
        if self.redis and self.redis.is_connected:
            await self.redis.set(key, value, ttl)

        # Store in Memcached
        if self.memcached and self.memcached.is_connected:
            await self.memcached.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        start_time = time.time()

        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                size = entry.get_size()
                del self.cache[key]

                # Update strategy
                self.strategy.cache.pop(key, None)

                # Invalidate
                await self.invalidation.invalidate_key(key, "manual_delete")

                # P2P sync
                if self.p2p_sync:
                    self.p2p_sync.invalidate_local_entry(key)

                latency = time.time() - start_time
                self.metrics.record_delete(latency, size)

                return True

            latency = time.time() - start_time
            self.metrics.record_delete(latency, 0)

            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        return await self.invalidation.invalidate_pattern(pattern)

    async def clear(self) -> int:
        """Clear all cache entries"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            self.strategy.cache.clear()

            # Invalidate all
            await self.invalidation.invalidate_all()

            # P2P sync
            if self.p2p_sync:
                # Invalidate all local entries
                for key in list(self.p2p_sync.local_metadata.keys()):
                    self.p2p_sync.invalidate_local_entry(key)

            self.metrics.record_invalidation(count)
            return count

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                return False
            return not entry.is_expired()

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            current_entries = len(self.cache)
            total_size = sum(entry.get_size() for entry in self.cache.values())

        self.metrics.update_size_metrics(current_entries, total_size)

        stats = {
            'node_id': self.node_id,
            'is_running': self.is_running,
            'cache_entries': current_entries,
            'cache_size_bytes': total_size,
            'max_size': self.strategy.max_size,
            'strategy': self.strategy.strategy_name,
            'compression': self.compression.get_stats(),
            'invalidation': self.invalidation.get_stats(),
            'metrics': self.metrics.get_stats(),
            'p2p_sync': self.p2p_sync.get_stats() if self.p2p_sync else None,
            'redis': self.redis.get_stats() if self.redis else None,
            'memcached': self.memcached.get_stats() if self.memcached else None,
            'cluster': await self.cluster.get_cluster_stats() if self.cluster else None,
            'advanced_monitoring': self.advanced_monitoring.get_comprehensive_report() if self.advanced_monitoring else None
        }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        stats = await self.get_stats()
        health = self.metrics.get_health_status()

        return {
            'status': health['status'],
            'timestamp': time.time(),
            'node_id': self.node_id,
            'issues': health['issues'],
            'stats': stats
        }

    def add_invalidation_dependency(self, key: str, depends_on: str):
        """Add dependency relationship for invalidation"""
        self.invalidation.add_dependency(key, depends_on)

    def remove_invalidation_dependency(self, key: str, depends_on: str):
        """Remove dependency relationship"""
        self.invalidation.remove_dependency(key, depends_on)

    def switch_strategy(self, new_strategy: str, **kwargs):
        """Switch cache replacement strategy"""
        old_strategy = self.strategy.strategy_name
        self.strategy.switch_strategy(new_strategy, **kwargs)
        self.metrics.record_strategy_switch(new_strategy)

        logger.info(f"Switched cache strategy from {old_strategy} to {new_strategy}")

    def add_p2p_node(self, node_id: str):
        """Add a P2P peer node"""
        if self.p2p_sync:
            self.p2p_sync.add_node(node_id)

    def remove_p2p_node(self, node_id: str):
        """Remove a P2P peer node"""
        if self.p2p_sync:
            self.p2p_sync.remove_node(node_id)

    async def handle_p2p_message(self, message: SyncMessage):
        """Handle incoming P2P message"""
        if self.p2p_sync:
            await self.p2p_sync.handle_message(message)

    async def _on_invalidation(self, key: str):
        """Handle invalidation events"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.strategy.cache.pop(key, None)

        # P2P sync
        if self.p2p_sync:
            self.p2p_sync.invalidate_local_entry(key)

    async def _on_p2p_entry_update(self, key: str, value: Any, version):
        """Handle P2P entry updates"""
        # In a real implementation, this would fetch the value from the network
        # For now, just log the update
        logger.debug(f"P2P entry update: {key}")

    async def _on_p2p_invalidation(self, key: str):
        """Handle P2P invalidation"""
        await self._on_invalidation(key)

    # Synchronous versions for compatibility
    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous get"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get(key))
        finally:
            loop.close()

    def set_sync(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Synchronous set"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.set(key, value, ttl))
        finally:
            loop.close()

    def delete_sync(self, key: str) -> bool:
        """Synchronous delete"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.delete(key))
        finally:
            loop.close()

    def exists_sync(self, key: str) -> bool:
        """Synchronous exists"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.exists(key))
        finally:
            loop.close()

# Global instance for singleton-like usage
_cache_manager_instance: Optional[DistributedCacheManager] = None

def get_cache_manager(node_id: str = "default", **kwargs) -> DistributedCacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = DistributedCacheManager(node_id, **kwargs)
    return _cache_manager_instance

async def initialize_cache(node_id: str = "default", **kwargs):
    """Initialize global cache manager"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = DistributedCacheManager(node_id, **kwargs)
        await _cache_manager_instance.start()
    return _cache_manager_instance