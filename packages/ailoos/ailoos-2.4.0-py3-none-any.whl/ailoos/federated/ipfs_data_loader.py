"""
IPFS Data Loader for Federated Training
Handles loading of training data from IPFS with caching, prefetching, and memory management optimizations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from collections import OrderedDict
from pathlib import Path

from ..core.logging import get_logger
from ..infrastructure.ipfs_embedded import IPFSManager

logger = get_logger(__name__)


class IPFSDataLoader:
    """
    Data loader for federated nodes to load training data from IPFS.
    Features caching, prefetching, and memory management for efficient data access.
    """

    def __init__(self,
                 ipfs_manager: IPFSManager,
                 cache_dir: Optional[str] = None,
                 max_memory_mb: int = 100,
                 prefetch_workers: int = 2):
        """
        Initialize the IPFS Data Loader.

        Args:
            ipfs_manager: IPFS manager instance for data retrieval
            cache_dir: Optional directory for file-based caching (not implemented yet)
            max_memory_mb: Maximum memory to use for caching (MB)
            prefetch_workers: Number of background prefetch workers
        """
        self.ipfs_manager = ipfs_manager
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.prefetch_workers = prefetch_workers

        # In-memory LRU cache
        self.cache: OrderedDict[str, bytes] = OrderedDict()
        self.memory_used = 0

        # Prefetching
        self.prefetch_queue: asyncio.Queue[str] = asyncio.Queue()
        self.prefetch_tasks: List[asyncio.Task] = []

        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_loaded_bytes': 0,
            'prefetched_items': 0,
            'evictions': 0
        }

        logger.info(f"🚀 IPFSDataLoader initialized with {max_memory_mb}MB cache limit")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the data loader and prefetch workers."""
        # Start prefetch workers
        self.prefetch_tasks = []
        for i in range(self.prefetch_workers):
            task = asyncio.create_task(self._prefetch_worker())
            self.prefetch_tasks.append(task)
            logger.debug(f"Started prefetch worker {i+1}")

        logger.info(f"✅ IPFSDataLoader started with {self.prefetch_workers} prefetch workers")

    async def stop(self):
        """Stop the data loader and prefetch workers."""
        # Cancel prefetch tasks
        for task in self.prefetch_tasks:
            task.cancel()

        # Wait for tasks to finish
        if self.prefetch_tasks:
            await asyncio.gather(*self.prefetch_tasks, return_exceptions=True)

        logger.info("🛑 IPFSDataLoader stopped")

    async def load_data(self, cid: str) -> bytes:
        """
        Load data for a given CID, using enhanced caching and IPFS optimizations.

        Args:
            cid: Content identifier

        Returns:
            Data bytes
        """
        # Check local cache first
        if cid in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(cid)
            self.stats['cache_hits'] += 1
            logger.debug(f"Cache hit for {cid}")
            return self.cache[cid]

        # Check prefetch cache in IPFS manager
        if hasattr(self.ipfs_manager, 'latency_optimizer'):
            prefetched_data = self.ipfs_manager.latency_optimizer.get_prefetched_content(cid)
            if prefetched_data:
                self.stats['cache_hits'] += 1
                await self._add_to_cache(cid, prefetched_data)
                self.stats['total_loaded_bytes'] += len(prefetched_data)
                logger.debug(f"Prefetch cache hit for {cid}")
                return prefetched_data

        # Cache miss - load from IPFS with optimizations
        self.stats['cache_misses'] += 1
        logger.debug(f"Cache miss for {cid}, loading from IPFS")

        try:
            data = await self.ipfs_manager.get_data(cid)
            await self._add_to_cache(cid, data)
            self.stats['total_loaded_bytes'] += len(data)

            # Trigger prefetching for related content
            if hasattr(self.ipfs_manager, 'latency_optimizer'):
                await self.ipfs_manager.latency_optimizer.prefetch_content(cid, data)

            return data

        except Exception as e:
            logger.error(f"❌ Failed to load data for CID {cid}: {e}")
            raise

    async def prefetch_cids(self, cids: List[str]):
        """
        Prefetch data for multiple CIDs in the background.

        Args:
            cids: List of CIDs to prefetch
        """
        for cid in cids:
            if cid not in self.cache:
                await self.prefetch_queue.put(cid)
                logger.debug(f"Queued prefetch for {cid}")

    async def _add_to_cache(self, cid: str, data: bytes):
        """
        Add data to cache, evicting if necessary.

        Args:
            cid: Content identifier
            data: Data bytes
        """
        data_size = len(data)

        # Evict items if needed
        while self.memory_used + data_size > self.max_memory_bytes and self.cache:
            evicted_cid, evicted_data = self.cache.popitem(last=False)  # Remove oldest
            self.memory_used -= len(evicted_data)
            self.stats['evictions'] += 1
            logger.debug(f"Evicted {evicted_cid} from cache")

        # Add to cache
        self.cache[cid] = data
        self.cache.move_to_end(cid)  # Mark as most recently used
        self.memory_used += data_size

        logger.debug(f"Added {cid} to cache ({data_size} bytes)")

    async def _prefetch_worker(self):
        """Background worker for prefetching data."""
        while True:
            try:
                cid = await self.prefetch_queue.get()

                if cid not in self.cache:
                    try:
                        data = await self.ipfs_manager.get_data(cid)
                        await self._add_to_cache(cid, data)
                        self.stats['prefetched_items'] += 1
                        logger.debug(f"Prefetched {cid}")

                    except Exception as e:
                        logger.warning(f"Failed to prefetch {cid}: {e}")

                self.prefetch_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prefetch worker error: {e}")

    def clear_cache(self):
        """Clear the in-memory cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        self.memory_used = 0
        logger.info(f"🧹 Cleared cache ({cache_size} items)")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = self.stats['cache_hits'] / max(1, total_requests)

        return {
            'cached_items': len(self.cache),
            'memory_used_mb': self.memory_used / (1024 * 1024),
            'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
            'queue_size': self.prefetch_queue.qsize(),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': hit_rate,
            'total_loaded_bytes': self.stats['total_loaded_bytes'],
            'prefetched_items': self.stats['prefetched_items'],
            'evictions': self.stats['evictions']
        }

    def is_cached(self, cid: str) -> bool:
        """
        Check if a CID is cached.

        Args:
            cid: Content identifier

        Returns:
            True if cached
        """
        return cid in self.cache

    async def preload_cids(self, cids: List[str]) -> Dict[str, bool]:
        """
        Preload multiple CIDs synchronously (wait for completion).

        Args:
            cids: List of CIDs to load

        Returns:
            Dictionary mapping CID to success status
        """
        results = {}
        for cid in cids:
            try:
                await self.load_data(cid)
                results[cid] = True
            except Exception as e:
                logger.warning(f"Failed to preload {cid}: {e}")
                results[cid] = False

        return results


# Convenience functions

async def create_ipfs_data_loader(ipfs_endpoint: str = "http://localhost:5001/api/v0",
                                 **kwargs) -> IPFSDataLoader:
    """
    Create an IPFS Data Loader with default IPFS manager.

    Args:
        ipfs_endpoint: IPFS API endpoint
        **kwargs: Additional arguments for IPFSDataLoader

    Returns:
        Configured IPFSDataLoader instance
    """
    ipfs_manager = IPFSManager(api_endpoint=ipfs_endpoint)
    await ipfs_manager.start()

    loader = IPFSDataLoader(ipfs_manager=ipfs_manager, **kwargs)
    await loader.start()

    return loader