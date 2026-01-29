"""
AILOOS Performance Module

This module provides performance optimization features for AILOOS distributed system.
"""

# Caching Layers - FASE 4.4
from .caching_layers import (
    MultiLevelCacheManager, RedisClusterManager, CDNManager, EdgeComputingManager,
    CacheLayer, CacheStrategy, CacheEntry, RedisNode, CDNNode, EdgeNode,
    create_redis_cluster_config, create_cdn_config, create_edge_config,
    initialize_caching_system, demonstrate_caching_layers
)

# Async Processing - FASE 4.4
from .async_processing import (
    AsyncProcessingOrchestrator, MessageQueueManager, BackgroundJobProcessor,
    EventDrivenManager, TaskScheduler, Message, BackgroundJob, Event,
    MessageQueueType, JobStatus, JobPriority,
    initialize_async_processing_system, setup_sample_workflows,
    demonstrate_async_processing
)

__all__ = [
    # Caching Layers
    'MultiLevelCacheManager',
    'RedisClusterManager',
    'CDNManager',
    'EdgeComputingManager',
    'CacheLayer',
    'CacheStrategy',
    'CacheEntry',
    'RedisNode',
    'CDNNode',
    'EdgeNode',
    'create_redis_cluster_config',
    'create_cdn_config',
    'create_edge_config',
    'initialize_caching_system',
    'demonstrate_caching_layers',
    # Async Processing
    'AsyncProcessingOrchestrator',
    'MessageQueueManager',
    'BackgroundJobProcessor',
    'EventDrivenManager',
    'TaskScheduler',
    'Message',
    'BackgroundJob',
    'Event',
    'MessageQueueType',
    'JobStatus',
    'JobPriority',
    'initialize_async_processing_system',
    'setup_sample_workflows',
    'demonstrate_async_processing'
]

__version__ = "1.0.0"