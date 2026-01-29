"""
Distributed Intelligent Cache System for AILOOS
"""

from .strategies import IntelligentCacheStrategy, LRUStrategy, LFUStrategy, ARCStrategy, AdaptiveStrategy
from .compression import CacheCompression, CompressedCacheEntry
from .invalidation import CacheInvalidation, SmartInvalidation, InvalidationPolicy
from .metrics import CacheMetricsMonitor
from .synchronization import P2PCacheSynchronization, VectorClock, SyncMessage
from .redis_integration import RedisIntegration, RedisConfig
from .memcached_integration import MemcachedIntegration, MemcachedConfig
from .cache_cluster import CacheCluster, ClusterConfig, CacheNode, CacheBackend, NodeStatus
from .cache_monitoring import CacheMonitoring, AlertRule, Alert, PerformanceMetrics
from .cache_manager import DistributedCacheManager, get_cache_manager, initialize_cache

__all__ = [
    'IntelligentCacheStrategy',
    'LRUStrategy',
    'LFUStrategy',
    'ARCStrategy',
    'AdaptiveStrategy',
    'CacheCompression',
    'CompressedCacheEntry',
    'CacheInvalidation',
    'SmartInvalidation',
    'InvalidationPolicy',
    'CacheMetricsMonitor',
    'P2PCacheSynchronization',
    'VectorClock',
    'SyncMessage',
    'RedisIntegration',
    'RedisConfig',
    'MemcachedIntegration',
    'MemcachedConfig',
    'CacheCluster',
    'ClusterConfig',
    'CacheNode',
    'CacheBackend',
    'NodeStatus',
    'CacheMonitoring',
    'AlertRule',
    'Alert',
    'PerformanceMetrics',
    'DistributedCacheManager',
    'get_cache_manager',
    'initialize_cache'
]