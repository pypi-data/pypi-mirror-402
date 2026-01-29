import asyncio
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"

@dataclass
class CacheEntry:
    key: str
    value: Any
    ttl: Optional[int] = None  # Time to live in seconds
    created_at: float = None
    last_accessed: float = None
    access_count: int = 0
    size_bytes: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_accessed is None:
            self.last_accessed = time.time()

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """Update last accessed time"""
        self.last_accessed = time.time()
        self.access_count += 1

@dataclass
class CacheNode:
    node_id: str
    region: str
    capacity_mb: int
    current_size_mb: float = 0.0
    hit_count: int = 0
    miss_count: int = 0

class GlobalCache:
    """Distributed global cache system for CDN"""

    def __init__(self, max_memory_mb: int = 1024, cleanup_interval: int = 60):
        self.max_memory_mb = max_memory_mb
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_nodes: Dict[str, CacheNode] = {}
        self.replication_factor = 3  # Number of nodes to replicate to
        self.cache_strategy = CacheStrategy.LRU
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = cleanup_interval
        self._running = False

    async def start(self) -> None:
        """Start the global cache system"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        logger.info("Global cache system started")

    async def stop(self) -> None:
        """Stop the global cache system"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Global cache system stopped")

    async def add_cache_node(self, node: CacheNode) -> bool:
        """Add a cache node to the distributed system"""
        async with self._lock:
            if node.node_id in self.cache_nodes:
                return False

            self.cache_nodes[node.node_id] = node
            logger.info(f"Added cache node: {node.node_id} in {node.region}")
            return True

    async def remove_cache_node(self, node_id: str) -> bool:
        """Remove a cache node"""
        async with self._lock:
            if node_id not in self.cache_nodes:
                return False

            del self.cache_nodes[node_id]
            logger.info(f"Removed cache node: {node_id}")
            return True

    async def put(self, key: str, value: Any, ttl: Optional[int] = None,
                 regions: Optional[List[str]] = None) -> bool:
        """Store value in global cache"""
        async with self._lock:
            # Calculate entry size (rough estimate)
            size_bytes = self._calculate_size(value)
            size_mb = size_bytes / (1024 * 1024)

            # Check if we have space
            if not self._ensure_space(size_mb):
                logger.warning(f"Insufficient cache space for key {key}")
                return False

            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                size_bytes=size_bytes
            )

            self.cache[key] = entry
            self.cache.move_to_end(key)  # LRU: move to end

            # Update memory usage
            self._update_memory_usage(size_mb)

            # Replicate to other nodes
            await self._replicate_entry(entry, regions)

            logger.debug(f"Cached key {key} with TTL {ttl}")
            return True

    async def get(self, key: str, region: Optional[str] = None) -> Optional[Any]:
        """Retrieve value from global cache"""
        async with self._lock:
            entry = self.cache.get(key)

            if entry is None:
                # Try to fetch from other nodes
                entry = await self._fetch_from_nodes(key, region)
                if entry:
                    self.cache[key] = entry
                    self.cache.move_to_end(key)

            if entry and not entry.is_expired():
                entry.touch()

                # Update hit statistics
                if region and region in [node.region for node in self.cache_nodes.values()]:
                    for node in self.cache_nodes.values():
                        if node.region == region:
                            node.hit_count += 1

                return entry.value
            else:
                # Cache miss
                if region:
                    for node in self.cache_nodes.values():
                        if node.region == region:
                            node.miss_count += 1

                if entry:
                    # Remove expired entry
                    del self.cache[key]

                return None

    async def delete(self, key: str) -> bool:
        """Delete value from global cache"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                size_mb = entry.size_bytes / (1024 * 1024)
                self._update_memory_usage(-size_mb)
                del self.cache[key]

                # Propagate deletion to other nodes
                await self._delete_from_nodes(key)

                logger.debug(f"Deleted key {key} from cache")
                return True

            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        async with self._lock:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            deleted_count = 0

            for key in keys_to_delete:
                await self.delete(key)
                deleted_count += 1

            logger.info(f"Invalidated {deleted_count} keys matching pattern '{pattern}'")
            return deleted_count

    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        async with self._lock:
            total_entries = len(self.cache)
            total_size_mb = sum(entry.size_bytes for entry in self.cache.values()) / (1024 * 1024)
            memory_utilization = total_size_mb / self.max_memory_mb if self.max_memory_mb > 0 else 0

            expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())

            # Node metrics
            node_metrics = {}
            total_hits = 0
            total_misses = 0

            for node_id, node in self.cache_nodes.items():
                hit_rate = node.hit_count / (node.hit_count + node.miss_count) if (node.hit_count + node.miss_count) > 0 else 0
                node_metrics[node_id] = {
                    'region': node.region,
                    'capacity_mb': node.capacity_mb,
                    'current_size_mb': node.current_size_mb,
                    'utilization': node.current_size_mb / node.capacity_mb if node.capacity_mb > 0 else 0,
                    'hit_count': node.hit_count,
                    'miss_count': node.miss_count,
                    'hit_rate': hit_rate
                }
                total_hits += node.hit_count
                total_misses += node.miss_count

            overall_hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0

            return {
                'total_entries': total_entries,
                'total_size_mb': total_size_mb,
                'memory_utilization': memory_utilization,
                'max_memory_mb': self.max_memory_mb,
                'expired_entries': expired_count,
                'overall_hit_rate': overall_hit_rate,
                'total_hits': total_hits,
                'total_misses': total_misses,
                'node_count': len(self.cache_nodes),
                'node_metrics': node_metrics,
                'cache_strategy': self.cache_strategy.value
            }

    def _ensure_space(self, required_mb: float) -> bool:
        """Ensure there's enough space for new entry"""
        current_size_mb = sum(entry.size_bytes for entry in self.cache.values()) / (1024 * 1024)

        if current_size_mb + required_mb <= self.max_memory_mb:
            return True

        # Need to evict entries
        space_needed = required_mb - (self.max_memory_mb - current_size_mb)
        evicted_mb = self._evict_entries(space_needed)

        return evicted_mb >= space_needed

    def _evict_entries(self, target_mb: float) -> float:
        """Evict entries to free up space"""
        evicted_mb = 0.0
        keys_to_evict = []

        if self.cache_strategy == CacheStrategy.LRU:
            # Evict least recently used
            for key, entry in self.cache.items():
                if evicted_mb >= target_mb:
                    break
                keys_to_evict.append(key)
                evicted_mb += entry.size_bytes / (1024 * 1024)

        elif self.cache_strategy == CacheStrategy.LFU:
            # Evict least frequently used
            sorted_entries = sorted(self.cache.items(),
                                  key=lambda x: x[1].access_count)
            for key, entry in sorted_entries:
                if evicted_mb >= target_mb:
                    break
                keys_to_evict.append(key)
                evicted_mb += entry.size_bytes / (1024 * 1024)

        # Remove evicted entries
        for key in keys_to_evict:
            if key in self.cache:
                del self.cache[key]

        logger.debug(f"Evicted {len(keys_to_evict)} entries, freed {evicted_mb:.2f} MB")
        return evicted_mb

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        if isinstance(value, (int, float)):
            return 8
        elif isinstance(value, str):
            return len(value.encode('utf-8'))
        elif isinstance(value, (list, tuple)):
            return sum(self._calculate_size(item) for item in value) + 64
        elif isinstance(value, dict):
            return sum(len(k.encode('utf-8')) + self._calculate_size(v) for k, v in value.items()) + 128
        else:
            # Rough estimate for other objects
            return 256

    def _update_memory_usage(self, delta_mb: float) -> None:
        """Update memory usage for nodes (simplified)"""
        # In a real system, this would track per-node usage
        pass

    async def _replicate_entry(self, entry: CacheEntry, regions: Optional[List[str]] = None) -> None:
        """Replicate entry to other cache nodes"""
        # Simplified replication - in real system would use consensus, etc.
        target_nodes = self._select_replication_nodes(entry.key, regions)

        for node_id in target_nodes:
            if node_id in self.cache_nodes:
                # Simulate network replication
                await asyncio.sleep(0.001)
                logger.debug(f"Replicated {entry.key} to node {node_id}")

    async def _fetch_from_nodes(self, key: str, region: Optional[str] = None) -> Optional[CacheEntry]:
        """Try to fetch entry from other nodes"""
        # Simplified - in real system would query other nodes
        await asyncio.sleep(0.001)  # Simulate network latency
        return None  # For demo, assume not found

    async def _delete_from_nodes(self, key: str) -> None:
        """Delete entry from all nodes"""
        for node_id in self.cache_nodes:
            await asyncio.sleep(0.001)  # Simulate network operation
            logger.debug(f"Deleted {key} from node {node_id}")

    def _select_replication_nodes(self, key: str, regions: Optional[List[str]] = None) -> List[str]:
        """Select nodes for replication"""
        available_nodes = list(self.cache_nodes.keys())

        if regions:
            # Prefer nodes in specified regions
            regional_nodes = [n for n in available_nodes
                            if self.cache_nodes[n].region in regions]
            if len(regional_nodes) >= self.replication_factor:
                available_nodes = regional_nodes

        # Use consistent hashing or simple hash for node selection
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        selected = []

        for i in range(self.replication_factor):
            index = (hash_value + i) % len(available_nodes)
            selected.append(available_nodes[index])

        return selected

    async def _cleanup_worker(self) -> None:
        """Background worker to clean up expired entries"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        async with self._lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]

            for key in expired_keys:
                entry = self.cache[key]
                size_mb = entry.size_bytes / (1024 * 1024)
                self._update_memory_usage(-size_mb)
                del self.cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")