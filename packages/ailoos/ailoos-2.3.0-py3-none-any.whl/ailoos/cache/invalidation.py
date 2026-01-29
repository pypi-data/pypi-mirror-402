"""
Cache Invalidation System for Distributed Cache
Handles automatic and manual cache invalidation with dependencies
"""

import asyncio
import time
import re
from typing import Set, Dict, List, Callable, Optional, Any
from collections import defaultdict
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class InvalidationPolicy(Enum):
    """Cache invalidation policies"""
    WRITE_THROUGH = "write_through"  # Invalidate immediately on write
    WRITE_BEHIND = "write_behind"    # Invalidate after write completes
    TIME_BASED = "time_based"       # TTL-based invalidation
    EVENT_BASED = "event_based"     # Event-driven invalidation

class CacheInvalidation:
    """Manages cache invalidation with dependencies and policies"""

    def __init__(self, policy: InvalidationPolicy = InvalidationPolicy.TIME_BASED):
        self.policy = policy
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # key -> dependent keys
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)  # key -> keys that depend on it
        self.invalidated_keys: Set[str] = set()
        self.invalidation_listeners: List[Callable[[str], None]] = []
        self.pattern_listeners: Dict[str, List[Callable[[str], None]]] = defaultdict(list)

        # TTL management
        self.ttl_entries: Dict[str, float] = {}  # key -> expiration time
        self.ttl_check_interval = 60  # seconds
        self._ttl_task: Optional[asyncio.Task] = None

        # Stats
        self.manual_invalidations = 0
        self.auto_invalidations = 0
        self.dependency_invalidations = 0

    async def start_ttl_monitor(self):
        """Start the TTL monitoring task"""
        if self._ttl_task is None or self._ttl_task.done():
            self._ttl_task = asyncio.create_task(self._monitor_ttl())

    async def stop_ttl_monitor(self):
        """Stop the TTL monitoring task"""
        if self._ttl_task:
            self._ttl_task.cancel()
            try:
                await self._ttl_task
            except asyncio.CancelledError:
                pass

    async def _monitor_ttl(self):
        """Monitor TTL entries and invalidate expired ones"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []

                for key, expires_at in self.ttl_entries.items():
                    if current_time >= expires_at:
                        expired_keys.append(key)

                for key in expired_keys:
                    await self.invalidate_key(key, reason="TTL expired")
                    del self.ttl_entries[key]

                await asyncio.sleep(self.ttl_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TTL monitoring error: {e}")
                await asyncio.sleep(self.ttl_check_interval)

    def set_ttl(self, key: str, ttl_seconds: float):
        """Set TTL for a cache key"""
        self.ttl_entries[key] = time.time() + ttl_seconds

    def remove_ttl(self, key: str):
        """Remove TTL for a cache key"""
        self.ttl_entries.pop(key, None)

    async def invalidate_key(self, key: str, reason: str = "manual"):
        """Invalidate a single cache key"""
        if key in self.invalidated_keys:
            return

        self.invalidated_keys.add(key)
        self.manual_invalidations += 1

        # Invalidate dependent keys
        await self._invalidate_dependencies(key)

        # Notify listeners
        await self._notify_invalidation(key, reason)

        logger.debug(f"Invalidated key: {key} (reason: {reason})")

    async def invalidate_pattern(self, pattern: str, reason: str = "pattern"):
        """Invalidate keys matching a pattern"""
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(f"^{regex_pattern}$")

        invalidated_count = 0
        keys_to_check = list(self.dependencies.keys()) + list(self.reverse_dependencies.keys())
        keys_to_check = list(set(keys_to_check))  # Remove duplicates

        for key in keys_to_check:
            if regex.match(key):
                await self.invalidate_key(key, reason)
                invalidated_count += 1

        # Notify pattern listeners
        for listener_pattern, listeners in self.pattern_listeners.items():
            if re.match(listener_pattern.replace('*', '.*').replace('?', '.'), pattern):
                for listener in listeners:
                    try:
                        await listener(pattern)
                    except Exception as e:
                        logger.error(f"Pattern invalidation listener error: {e}")

        logger.info(f"Invalidated {invalidated_count} keys matching pattern: {pattern}")

    async def invalidate_all(self, reason: str = "clear_all"):
        """Invalidate all cache keys"""
        all_keys = set(self.dependencies.keys()) | set(self.reverse_dependencies.keys())
        for key in all_keys:
            await self.invalidate_key(key, reason)

        logger.info(f"Invalidated all {len(all_keys)} cache keys")

    def add_dependency(self, key: str, depends_on: str):
        """Add dependency relationship: key depends on depends_on"""
        self.dependencies[key].add(depends_on)
        self.reverse_dependencies[depends_on].add(key)

    def remove_dependency(self, key: str, depends_on: str):
        """Remove dependency relationship"""
        self.dependencies[key].discard(depends_on)
        self.reverse_dependencies[depends_on].discard(key)

        # Clean up empty sets
        if not self.dependencies[key]:
            del self.dependencies[key]
        if not self.reverse_dependencies[depends_on]:
            del self.reverse_dependencies[depends_on]

    def get_dependencies(self, key: str) -> Set[str]:
        """Get keys that this key depends on"""
        return self.dependencies.get(key, set()).copy()

    def get_dependents(self, key: str) -> Set[str]:
        """Get keys that depend on this key"""
        return self.reverse_dependencies.get(key, set()).copy()

    async def _invalidate_dependencies(self, key: str):
        """Invalidate all keys that depend on the given key"""
        dependents = self.get_dependents(key)
        for dependent in dependents:
            if dependent not in self.invalidated_keys:
                await self.invalidate_key(dependent, f"dependency of {key}")
                self.dependency_invalidations += 1

    def add_invalidation_listener(self, listener: Callable[[str], None]):
        """Add listener for key invalidation events"""
        self.invalidation_listeners.append(listener)

    def remove_invalidation_listener(self, listener: Callable[[str], None]):
        """Remove invalidation listener"""
        self.invalidation_listeners.remove(listener)

    def add_pattern_listener(self, pattern: str, listener: Callable[[str], None]):
        """Add listener for pattern-based invalidation"""
        self.pattern_listeners[pattern].append(listener)

    def remove_pattern_listener(self, pattern: str, listener: Callable[[str], None]):
        """Remove pattern listener"""
        if pattern in self.pattern_listeners:
            self.pattern_listeners[pattern].remove(listener)
            if not self.pattern_listeners[pattern]:
                del self.pattern_listeners[pattern]

    async def _notify_invalidation(self, key: str, reason: str):
        """Notify all listeners of key invalidation"""
        for listener in self.invalidation_listeners:
            try:
                await listener(key)
            except Exception as e:
                logger.error(f"Invalidation listener error: {e}")

    def is_invalidated(self, key: str) -> bool:
        """Check if a key has been invalidated"""
        return key in self.invalidated_keys

    def clear_invalidated(self):
        """Clear the set of invalidated keys"""
        self.invalidated_keys.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics"""
        return {
            'policy': self.policy.value,
            'manual_invalidations': self.manual_invalidations,
            'auto_invalidations': self.auto_invalidations,
            'dependency_invalidations': self.dependency_invalidations,
            'total_invalidations': self.manual_invalidations + self.auto_invalidations + self.dependency_invalidations,
            'active_ttl_entries': len(self.ttl_entries),
            'invalidated_keys_count': len(self.invalidated_keys),
            'dependency_relationships': len(self.dependencies),
            'listeners_count': len(self.invalidation_listeners),
            'pattern_listeners_count': len(self.pattern_listeners)
        }

    def reset_stats(self):
        """Reset invalidation statistics"""
        self.manual_invalidations = 0
        self.auto_invalidations = 0
        self.dependency_invalidations = 0

class SmartInvalidation:
    """Advanced invalidation with predictive capabilities"""

    def __init__(self, invalidation: CacheInvalidation):
        self.invalidation = invalidation
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)  # key -> access timestamps
        self.write_patterns: Dict[str, List[float]] = defaultdict(list)  # key -> write timestamps
        self.correlation_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)

    def record_access(self, key: str):
        """Record access pattern for predictive invalidation"""
        self.access_patterns[key].append(time.time())
        # Keep only recent accesses
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-100:]

    def record_write(self, key: str):
        """Record write pattern"""
        self.write_patterns[key].append(time.time())
        if len(self.write_patterns[key]) > 100:
            self.write_patterns[key] = self.write_patterns[key][-100:]

    async def predictive_invalidate(self, key: str):
        """Predict and invalidate related keys based on correlation"""
        correlated_keys = self._find_correlated_keys(key)
        for correlated_key in correlated_keys:
            if self._should_invalidate_correlated(correlated_key):
                await self.invalidation.invalidate_key(correlated_key, f"predictive correlation with {key}")

    def _find_correlated_keys(self, key: str) -> List[str]:
        """Find keys that are correlated with the given key"""
        if key not in self.correlation_matrix:
            return []

        correlations = self.correlation_matrix[key]
        # Return keys with correlation > 0.7
        return [k for k, corr in correlations.items() if corr > 0.7]

    def _should_invalidate_correlated(self, key: str) -> bool:
        """Determine if correlated key should be invalidated"""
        # Simple heuristic: if recently accessed and correlated, invalidate
        if key in self.access_patterns:
            last_access = max(self.access_patterns[key])
            if time.time() - last_access < 300:  # 5 minutes
                return True
        return False

    def update_correlations(self):
        """Update correlation matrix based on access patterns"""
        all_keys = set(self.access_patterns.keys()) | set(self.write_patterns.keys())

        for key1 in all_keys:
            for key2 in all_keys:
                if key1 != key2:
                    corr = self._calculate_correlation(key1, key2)
                    if corr > 0.5:  # Only store significant correlations
                        self.correlation_matrix[key1][key2] = corr

    def _calculate_correlation(self, key1: str, key2: str) -> float:
        """Calculate correlation between two keys' access patterns"""
        # Simple correlation based on access time proximity
        accesses1 = self.access_patterns.get(key1, [])
        accesses2 = self.access_patterns.get(key2, [])

        if not accesses1 or not accesses2:
            return 0.0

        # Count co-occurrences within 60 seconds
        co_occurrences = 0
        total_possible = min(len(accesses1), len(accesses2))

        for t1 in accesses1:
            for t2 in accesses2:
                if abs(t1 - t2) <= 60:
                    co_occurrences += 1
                    break

        return co_occurrences / total_possible if total_possible > 0 else 0.0