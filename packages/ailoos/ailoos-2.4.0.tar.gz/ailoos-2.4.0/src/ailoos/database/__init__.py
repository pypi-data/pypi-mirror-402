"""
Database Scalability Module para AILOOS

Incluye sharding implementation y read replicas para escalabilidad horizontal.
"""

# Sharding Implementation - FASE 4.2
from .sharding import (
    ShardManager, ShardMap, Shard, ShardStrategy, ShardStatus,
    ShardHealthMonitor, ShardRebalancer, CrossShardQueryOptimizer,
    create_user_sharding_config, create_transaction_sharding_config,
    initialize_database_sharding, example_sharding_usage
)

# Read Replicas - FASE 4.2
from .read_replicas import (
    ReadReplicaManager, ReadReplica, ReplicaRole, ReplicaStatus,
    ReadDistributionStats, ReplicaHealthMonitor, ReplicaFailoverManager,
    create_global_read_replicas_config, initialize_read_replicas_system,
    demonstrate_read_replicas
)

__all__ = [
    # Sharding Implementation
    'ShardManager',
    'ShardMap',
    'Shard',
    'ShardStrategy',
    'ShardStatus',
    'ShardHealthMonitor',
    'ShardRebalancer',
    'CrossShardQueryOptimizer',
    'create_user_sharding_config',
    'create_transaction_sharding_config',
    'initialize_database_sharding',
    'example_sharding_usage',
    # Read Replicas
    'ReadReplicaManager',
    'ReadReplica',
    'ReplicaRole',
    'ReplicaStatus',
    'ReadDistributionStats',
    'ReplicaHealthMonitor',
    'ReplicaFailoverManager',
    'create_global_read_replicas_config',
    'initialize_read_replicas_system',
    'demonstrate_read_replicas'
]