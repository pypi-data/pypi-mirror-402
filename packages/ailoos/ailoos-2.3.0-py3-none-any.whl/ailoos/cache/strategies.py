"""
Intelligent Cache Strategies for Distributed Cache System
Implements LRU, LFU, ARC, and Adaptive strategies
"""

import time
import heapq
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, List
from collections import OrderedDict, defaultdict
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a cache entry with metadata"""
    def __init__(self, key: str, value: Any, size: int = 1, ttl: Optional[float] = None):
        self.key = key
        self.value = value
        self.size = size
        self.access_time = time.time()
        self.frequency = 1
        self.ttl = ttl
        self.expires_at = time.time() + ttl if ttl else None

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at

    def access(self):
        self.access_time = time.time()
        self.frequency += 1

class CacheStrategy(ABC):
    """Abstract base class for cache replacement strategies"""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.current_size = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        pass

    @abstractmethod
    def put(self, entry: CacheEntry) -> bool:
        pass

    @abstractmethod
    def evict(self) -> Optional[str]:
        pass

    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': hit_rate,
            'current_size': self.current_size,
            'max_size': self.max_size
        }

class LRUStrategy(CacheStrategy):
    """Least Recently Used cache strategy"""

    def __init__(self, max_size: int):
        super().__init__(max_size)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Optional[CacheEntry]:
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.current_size -= entry.size
                self.misses += 1
                return None
            entry.access()
            self.cache.move_to_end(key)
            self.hits += 1
            return entry
        self.misses += 1
        return None

    def put(self, entry: CacheEntry) -> bool:
        if entry.key in self.cache:
            old_entry = self.cache[entry.key]
            self.current_size -= old_entry.size
            self.cache[entry.key] = entry
            self.cache.move_to_end(entry.key)
        else:
            self.cache[entry.key] = entry
            self.current_size += entry.size

        while self.current_size > self.max_size and self.cache:
            evicted_key = self.evict()
            if evicted_key:
                evicted_entry = self.cache[evicted_key]
                self.current_size -= evicted_entry.size
                del self.cache[evicted_key]
                self.evictions += 1

        return True

    def evict(self) -> Optional[str]:
        if self.cache:
            return next(iter(self.cache))
        return None

class LFUStrategy(CacheStrategy):
    """Least Frequently Used cache strategy"""

    def __init__(self, max_size: int):
        super().__init__(max_size)
        self.cache: Dict[str, CacheEntry] = {}
        self.freq_map: Dict[int, OrderedDict[str, CacheEntry]] = defaultdict(OrderedDict)
        self.key_freq: Dict[str, int] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                self._remove_entry(key)
                self.misses += 1
                return None
            entry.access()
            self._update_frequency(key, entry.frequency - 1)
            self.hits += 1
            return entry
        self.misses += 1
        return None

    def put(self, entry: CacheEntry) -> bool:
        if entry.key in self.cache:
            old_entry = self.cache[entry.key]
            self.current_size -= old_entry.size
            self._remove_entry(entry.key)
            self.cache[entry.key] = entry
            self.current_size += entry.size
            self._update_frequency(entry.key, entry.frequency)
        else:
            self.cache[entry.key] = entry
            self.current_size += entry.size
            self._update_frequency(entry.key, entry.frequency)

        while self.current_size > self.max_size and self.cache:
            evicted_key = self.evict()
            if evicted_key:
                self._remove_entry(evicted_key)
                self.evictions += 1

        return True

    def evict(self) -> Optional[str]:
        if not self.freq_map:
            return None
        min_freq = min(self.freq_map.keys())
        freq_dict = self.freq_map[min_freq]
        if freq_dict:
            return next(iter(freq_dict))
        return None

    def _update_frequency(self, key: str, new_freq: int):
        if key in self.key_freq:
            old_freq = self.key_freq[key]
            if old_freq in self.freq_map and key in self.freq_map[old_freq]:
                del self.freq_map[old_freq][key]
                if not self.freq_map[old_freq]:
                    del self.freq_map[old_freq]

        self.key_freq[key] = new_freq
        self.freq_map[new_freq][key] = self.cache[key]

    def _remove_entry(self, key: str):
        if key in self.cache:
            entry = self.cache[key]
            self.current_size -= entry.size
            del self.cache[key]
            if key in self.key_freq:
                freq = self.key_freq[key]
                if freq in self.freq_map and key in self.freq_map[freq]:
                    del self.freq_map[freq][key]
                    if not self.freq_map[freq]:
                        del self.freq_map[freq]
                del self.key_freq[key]

class ARCStrategy(CacheStrategy):
    """Adaptive Replacement Cache strategy"""

    def __init__(self, max_size: int):
        super().__init__(max_size)
        self.t1: OrderedDict[str, CacheEntry] = OrderedDict()  # Recent pages
        self.t2: OrderedDict[str, CacheEntry] = OrderedDict()  # Frequent pages
        self.b1: OrderedDict[str, CacheEntry] = OrderedDict()  # Ghost entries for t1
        self.b2: OrderedDict[str, CacheEntry] = OrderedDict()  # Ghost entries for t2
        self.p = 0  # Target size for t1

    def get(self, key: str) -> Optional[CacheEntry]:
        if key in self.t1 or key in self.t2:
            entry = self.t1.get(key, self.t2.get(key))
            if entry.is_expired():
                self._remove_entry(key)
                self.misses += 1
                return None
            entry.access()
            if key in self.t1:
                self.t1.move_to_end(key)
                self._move_to_t2(key)
            else:
                self.t2.move_to_end(key)
            self.hits += 1
            return entry
        elif key in self.b1 or key in self.b2:
            self._adapt(key)
            self.misses += 1
            return None
        self.misses += 1
        return None

    def put(self, entry: CacheEntry) -> bool:
        if entry.key in self.t1 or entry.key in self.t2:
            # Update existing
            if entry.key in self.t1:
                self.t1[entry.key] = entry
                self.t1.move_to_end(entry.key)
            else:
                self.t2[entry.key] = entry
                self.t2.move_to_end(entry.key)
            return True

        # New entry
        if len(self.t1) + len(self.t2) >= self.max_size:
            self._replace(entry.key)

        if entry.key in self.b1:
            self.p = min(self.p + max(len(self.b2) / len(self.b1) if self.b1 else 0, 1), self.max_size)
            self._replace(entry.key)
            self.t2[entry.key] = entry
            self.t2.move_to_end(entry.key)
        else:
            self.t1[entry.key] = entry
            self.t1.move_to_end(entry.key)

        return True

    def evict(self) -> Optional[str]:
        # ARC doesn't use simple evict, handled in put
        return None

    def _move_to_t2(self, key: str):
        if key in self.t1:
            entry = self.t1[key]
            del self.t1[key]
            self.t2[key] = entry
            self.t2.move_to_end(key)

    def _adapt(self, key: str):
        if len(self.t1) >= self.max_size:
            if key in self.b1:
                self.p = min(self.p + 1, self.max_size)
            elif key in self.b2:
                self.p = max(self.p - 1, 0)
        elif len(self.t1) + len(self.t2) == self.max_size:
            if len(self.t1) < self.max_size:
                if key in self.b1:
                    self.p = min(self.p + 1, self.max_size)
                elif key in self.b2:
                    self.p = max(self.p - 1, 0)

    def _replace(self, key: str):
        if not self.t1 and not self.t2:
            return

        if len(self.t1) > 0 and (len(self.t1) > self.p or (key in self.b2 and len(self.t1) == self.p)):
            # Replace from t1
            lru_t1 = next(iter(self.t1))
            del self.t1[lru_t1]
            self.b1[lru_t1] = self.cache.get(lru_t1)  # Assuming we have access to global cache
        else:
            # Replace from t2
            lru_t2 = next(iter(self.t2))
            del self.t2[lru_t2]
            self.b2[lru_t2] = self.cache.get(lru_t2)

    def _remove_entry(self, key: str):
        if key in self.t1:
            del self.t1[key]
        elif key in self.t2:
            del self.t2[key]
        elif key in self.b1:
            del self.b1[key]
        elif key in self.b2:
            del self.b2[key]

class AdaptiveStrategy(CacheStrategy):
    """Adaptive strategy that switches between LRU and LFU based on access patterns"""

    def __init__(self, max_size: int, adaptation_window: int = 1000):
        super().__init__(max_size)
        self.lru_strategy = LRUStrategy(max_size)
        self.lfu_strategy = LFUStrategy(max_size)
        self.current_strategy = self.lru_strategy
        self.adaptation_window = adaptation_window
        self.recent_requests = []
        self.last_adaptation = time.time()

    def get(self, key: str) -> Optional[CacheEntry]:
        self.recent_requests.append(('get', key, time.time()))
        if len(self.recent_requests) > self.adaptation_window:
            self.recent_requests.pop(0)

        entry = self.current_strategy.get(key)
        if time.time() - self.last_adaptation > 60:  # Adapt every minute
            self._adapt_strategy()
        return entry

    def put(self, entry: CacheEntry) -> bool:
        self.recent_requests.append(('put', entry.key, time.time()))
        if len(self.recent_requests) > self.adaptation_window:
            self.recent_requests.pop(0)

        result = self.current_strategy.put(entry)
        if time.time() - self.last_adaptation > 60:
            self._adapt_strategy()
        return result

    def evict(self) -> Optional[str]:
        return self.current_strategy.evict()

    def _adapt_strategy(self):
        if len(self.recent_requests) < 100:
            return

        # Calculate hit rates for both strategies (simplified)
        lru_hits = sum(1 for req in self.recent_requests[-100:] if req[0] == 'get' and self.lru_strategy.get(req[1]) is not None)
        lfu_hits = sum(1 for req in self.recent_requests[-100:] if req[0] == 'get' and self.lfu_strategy.get(req[1]) is not None)

        if lfu_hits > lru_hits * 1.2:  # LFU performing 20% better
            self.current_strategy = self.lfu_strategy
            logger.info("Switched to LFU strategy")
        elif lru_hits > lfu_hits * 1.2:
            self.current_strategy = self.lru_strategy
            logger.info("Switched to LRU strategy")

        self.last_adaptation = time.time()

class IntelligentCacheStrategy:
    """Factory and manager for cache strategies"""

    STRATEGIES = {
        'lru': LRUStrategy,
        'lfu': LFUStrategy,
        'arc': ARCStrategy,
        'adaptive': AdaptiveStrategy
    }

    def __init__(self, strategy_name: str = 'lru', max_size: int = 1000, **kwargs):
        self.strategy_name = strategy_name
        self.max_size = max_size
        self.strategy = self.STRATEGIES[strategy_name](max_size, **kwargs)

    def get(self, key: str) -> Optional[CacheEntry]:
        return self.strategy.get(key)

    def put(self, key: str, value: Any, size: int = 1, ttl: Optional[float] = None) -> bool:
        entry = CacheEntry(key, value, size, ttl)
        return self.strategy.put(entry)

    def evict(self) -> Optional[str]:
        return self.strategy.evict()

    def get_stats(self) -> Dict[str, Any]:
        return self.strategy.get_stats()

    def switch_strategy(self, new_strategy: str, **kwargs):
        """Switch to a different strategy"""
        if new_strategy in self.STRATEGIES:
            old_stats = self.strategy.get_stats()
            self.strategy = self.STRATEGIES[new_strategy](self.max_size, **kwargs)
            logger.info(f"Switched from {self.strategy_name} to {new_strategy}")
            self.strategy_name = new_strategy
            # Could migrate entries here if needed