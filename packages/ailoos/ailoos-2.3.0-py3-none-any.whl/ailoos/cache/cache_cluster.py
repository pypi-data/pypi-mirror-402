"""
Cache Cluster Management for Distributed Cache System
Manages multiple cache nodes with load balancing, failover, and consistency
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import random

try:
    from .redis_integration import RedisIntegration, RedisConfig
    from .memcached_integration import MemcachedIntegration, MemcachedConfig
except ImportError:
    # Fallback for direct imports
    from redis_integration import RedisIntegration, RedisConfig
    from memcached_integration import MemcachedIntegration, MemcachedConfig

logger = logging.getLogger(__name__)

class CacheBackend(Enum):
    """Supported cache backends"""
    REDIS = "redis"
    MEMCACHED = "memcached"
    MEMORY = "memory"

class NodeStatus(Enum):
    """Cache node status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    DISCONNECTED = "disconnected"

@dataclass
class CacheNode:
    """Represents a cache node in the cluster"""
    node_id: str
    backend: CacheBackend
    config: Union[RedisConfig, MemcachedConfig]
    weight: int = 1
    status: NodeStatus = NodeStatus.HEALTHY
    last_health_check: float = 0
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0

@dataclass
class ClusterConfig:
    """Configuration for cache cluster"""
    cluster_name: str = "default_cluster"
    health_check_interval: int = 30
    max_consecutive_failures: int = 3
    failover_timeout: float = 5.0
    load_balancing_strategy: str = "consistent_hashing"  # consistent_hashing, round_robin, least_loaded
    replication_factor: int = 1
    read_quorum: int = 1
    write_quorum: int = 1
    enable_consistency_checks: bool = True
    consistency_check_interval: int = 60

class CacheCluster:
    """Manages a cluster of cache nodes with load balancing and failover"""

    def __init__(self, config: ClusterConfig = None):
        self.config = config or ClusterConfig()
        self.nodes: Dict[str, CacheNode] = {}
        self.active_clients: Dict[str, Union[RedisIntegration, MemcachedIntegration]] = {}
        self.node_hash_ring: List[str] = []
        self.round_robin_index = 0

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'load_balanced_requests': 0,
            'failover_events': 0,
            'consistency_checks': 0,
            'consistency_violations': 0
        }

        # Consistency tracking
        self.consistency_map: Dict[str, Dict[str, Any]] = {}  # key -> {node_id: value}

        # Callbacks
        self.node_failure_callbacks: List[Callable[[str], None]] = []
        self.node_recovery_callbacks: List[Callable[[str], None]] = []

    async def add_node(self, node: CacheNode) -> bool:
        """Add a cache node to the cluster"""
        try:
            # Create client based on backend
            if node.backend == CacheBackend.REDIS:
                client = RedisIntegration(node.config)
            elif node.backend == CacheBackend.MEMCACHED:
                client = MemcachedIntegration(node.config)
            else:
                logger.error(f"Unsupported backend: {node.backend}")
                return False

            # Connect to node
            if await client.connect():
                self.nodes[node.node_id] = node
                self.active_clients[node.node_id] = client
                self._rebuild_hash_ring()
                logger.info(f"Added cache node {node.node_id} to cluster")
                return True
            else:
                logger.error(f"Failed to connect to cache node {node.node_id}")
                return False

        except Exception as e:
            logger.error(f"Error adding cache node {node.node_id}: {e}")
            return False

    async def remove_node(self, node_id: str) -> bool:
        """Remove a cache node from the cluster"""
        if node_id not in self.nodes:
            return False

        try:
            # Disconnect client
            if node_id in self.active_clients:
                await self.active_clients[node_id].disconnect()
                del self.active_clients[node_id]

            # Remove node
            del self.nodes[node_id]
            self._rebuild_hash_ring()
            logger.info(f"Removed cache node {node_id} from cluster")
            return True

        except Exception as e:
            logger.error(f"Error removing cache node {node_id}: {e}")
            return False

    def _rebuild_hash_ring(self):
        """Rebuild consistent hashing ring"""
        if self.config.load_balancing_strategy != "consistent_hashing":
            return

        self.node_hash_ring = []
        for node_id, node in self.nodes.items():
            if node.status == NodeStatus.HEALTHY:
                # Add multiple virtual nodes based on weight
                for i in range(node.weight):
                    virtual_node = f"{node_id}:{i}"
                    hash_value = int(hashlib.md5(virtual_node.encode()).hexdigest(), 16)
                    self.node_hash_ring.append((hash_value, node_id))

        self.node_hash_ring.sort(key=lambda x: x[0])

    def _get_node_for_key(self, key: str) -> Optional[str]:
        """Get the appropriate node for a key using load balancing strategy"""
        healthy_nodes = [node_id for node_id, node in self.nodes.items()
                        if node.status == NodeStatus.HEALTHY]

        if not healthy_nodes:
            return None

        if self.config.load_balancing_strategy == "consistent_hashing":
            return self._get_consistent_hash_node(key)
        elif self.config.load_balancing_strategy == "round_robin":
            return self._get_round_robin_node()
        elif self.config.load_balancing_strategy == "least_loaded":
            return self._get_least_loaded_node()
        else:
            return random.choice(healthy_nodes)

    def _get_consistent_hash_node(self, key: str) -> Optional[str]:
        """Get node using consistent hashing"""
        if not self.node_hash_ring:
            return None

        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)

        # Find the first node with hash >= key_hash
        for hash_value, node_id in self.node_hash_ring:
            if hash_value >= key_hash:
                return node_id

        # Wrap around to first node
        return self.node_hash_ring[0][1] if self.node_hash_ring else None

    def _get_round_robin_node(self) -> Optional[str]:
        """Get node using round-robin"""
        healthy_nodes = [node_id for node_id, node in self.nodes.items()
                        if node.status == NodeStatus.HEALTHY]

        if not healthy_nodes:
            return None

        node_id = healthy_nodes[self.round_robin_index % len(healthy_nodes)]
        self.round_robin_index += 1
        return node_id

    def _get_least_loaded_node(self) -> Optional[str]:
        """Get least loaded node"""
        healthy_nodes = [(node_id, node) for node_id, node in self.nodes.items()
                        if node.status == NodeStatus.HEALTHY]

        if not healthy_nodes:
            return None

        # Sort by total_requests (ascending)
        healthy_nodes.sort(key=lambda x: x[1].total_requests)
        return healthy_nodes[0][0]

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cluster"""
        self.stats['total_requests'] += 1

        primary_node = self._get_node_for_key(key)
        if not primary_node:
            self.stats['failed_requests'] += 1
            return None

        # Try primary node
        value = await self._get_from_node(primary_node, key)
        if value is not None:
            self.stats['successful_requests'] += 1
            return value

        # Try failover nodes
        failover_nodes = self._get_failover_nodes(primary_node, key)
        for node_id in failover_nodes:
            value = await self._get_from_node(node_id, key)
            if value is not None:
                self.stats['load_balanced_requests'] += 1
                self.stats['successful_requests'] += 1
                return value

        self.stats['failed_requests'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cluster"""
        self.stats['total_requests'] += 1

        primary_node = self._get_node_for_key(key)
        if not primary_node:
            self.stats['failed_requests'] += 1
            return False

        # Write to primary node
        success = await self._set_in_node(primary_node, key, value, ttl)
        if success:
            self.stats['successful_requests'] += 1

            # Replicate to other nodes if replication_factor > 1
            if self.config.replication_factor > 1:
                await self._replicate_write(key, value, ttl, primary_node)

            return True

        # Try failover nodes
        failover_nodes = self._get_failover_nodes(primary_node, key)
        for node_id in failover_nodes:
            success = await self._set_in_node(node_id, key, value, ttl)
            if success:
                self.stats['load_balanced_requests'] += 1
                self.stats['successful_requests'] += 1
                return True

        self.stats['failed_requests'] += 1
        return False

    async def delete(self, key: str) -> bool:
        """Delete key from cluster"""
        self.stats['total_requests'] += 1

        primary_node = self._get_node_for_key(key)
        if not primary_node:
            self.stats['failed_requests'] += 1
            return False

        # Delete from primary node
        success = await self._delete_from_node(primary_node, key)
        if success:
            self.stats['successful_requests'] += 1

            # Delete from replicas
            if self.config.replication_factor > 1:
                await self._replicate_delete(key, primary_node)

            return True

        # Try failover nodes
        failover_nodes = self._get_failover_nodes(primary_node, key)
        for node_id in failover_nodes:
            success = await self._delete_from_node(node_id, key)
            if success:
                self.stats['load_balanced_requests'] += 1
                self.stats['successful_requests'] += 1
                return True

        self.stats['failed_requests'] += 1
        return False

    def _get_failover_nodes(self, primary_node: str, key: str) -> List[str]:
        """Get failover nodes for a key"""
        healthy_nodes = [node_id for node_id, node in self.nodes.items()
                        if node_id != primary_node and node.status == NodeStatus.HEALTHY]
        return healthy_nodes[:self.config.replication_factor - 1]

    async def _get_from_node(self, node_id: str, key: str) -> Optional[Any]:
        """Get value from specific node"""
        if node_id not in self.active_clients:
            return None

        client = self.active_clients[node_id]
        node = self.nodes[node_id]

        start_time = time.time()
        try:
            value = await client.get(key)
            response_time = time.time() - start_time

            # Update node statistics
            node.total_requests += 1
            node.avg_response_time = (node.avg_response_time * (node.total_requests - 1) + response_time) / node.total_requests

            return value

        except Exception as e:
            logger.error(f"Error getting from node {node_id}: {e}")
            node.failed_requests += 1
            node.consecutive_failures += 1

            if node.consecutive_failures >= self.config.max_consecutive_failures:
                await self._mark_node_unhealthy(node_id)

            return None

    async def _set_in_node(self, node_id: str, key: str, value: Any, ttl: Optional[float]) -> bool:
        """Set value in specific node"""
        if node_id not in self.active_clients:
            return False

        client = self.active_clients[node_id]
        node = self.nodes[node_id]

        start_time = time.time()
        try:
            success = await client.set(key, value, ttl)
            response_time = time.time() - start_time

            # Update node statistics
            node.total_requests += 1
            node.avg_response_time = (node.avg_response_time * (node.total_requests - 1) + response_time) / node.total_requests

            if success:
                node.consecutive_failures = 0  # Reset failure count
            else:
                node.failed_requests += 1
                node.consecutive_failures += 1

            return success

        except Exception as e:
            logger.error(f"Error setting in node {node_id}: {e}")
            node.failed_requests += 1
            node.consecutive_failures += 1

            if node.consecutive_failures >= self.config.max_consecutive_failures:
                await self._mark_node_unhealthy(node_id)

            return False

    async def _delete_from_node(self, node_id: str, key: str) -> bool:
        """Delete key from specific node"""
        if node_id not in self.active_clients:
            return False

        client = self.active_clients[node_id]
        node = self.nodes[node_id]

        start_time = time.time()
        try:
            success = await client.delete(key)
            response_time = time.time() - start_time

            # Update node statistics
            node.total_requests += 1
            node.avg_response_time = (node.avg_response_time * (node.total_requests - 1) + response_time) / node.total_requests

            if success:
                node.consecutive_failures = 0
            else:
                node.failed_requests += 1
                node.consecutive_failures += 1

            return success

        except Exception as e:
            logger.error(f"Error deleting from node {node_id}: {e}")
            node.failed_requests += 1
            node.consecutive_failures += 1

            if node.consecutive_failures >= self.config.max_consecutive_failures:
                await self._mark_node_unhealthy(node_id)

            return False

    async def _replicate_write(self, key: str, value: Any, ttl: Optional[float], exclude_node: str):
        """Replicate write to other nodes"""
        replica_nodes = [node_id for node_id in self.nodes.keys()
                        if node_id != exclude_node and self.nodes[node_id].status == NodeStatus.HEALTHY]

        replication_tasks = []
        for node_id in replica_nodes[:self.config.replication_factor - 1]:
            task = self._set_in_node(node_id, key, value, ttl)
            replication_tasks.append(task)

        if replication_tasks:
            await asyncio.gather(*replication_tasks, return_exceptions=True)

    async def _replicate_delete(self, key: str, exclude_node: str):
        """Replicate delete to other nodes"""
        replica_nodes = [node_id for node_id in self.nodes.keys()
                        if node_id != exclude_node and self.nodes[node_id].status == NodeStatus.HEALTHY]

        replication_tasks = []
        for node_id in replica_nodes[:self.config.replication_factor - 1]:
            task = self._delete_from_node(node_id, key)
            replication_tasks.append(task)

        if replication_tasks:
            await asyncio.gather(*replication_tasks, return_exceptions=True)

    async def _mark_node_unhealthy(self, node_id: str):
        """Mark a node as unhealthy and trigger failover"""
        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus.UNHEALTHY
            self.stats['failover_events'] += 1
            self._rebuild_hash_ring()

            # Trigger failure callbacks
            for callback in self.node_failure_callbacks:
                try:
                    await callback(node_id)
                except Exception as e:
                    logger.error(f"Error in node failure callback: {e}")

            logger.warning(f"Marked cache node {node_id} as unhealthy")

    async def _mark_node_healthy(self, node_id: str):
        """Mark a node as healthy"""
        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus.HEALTHY
            self.nodes[node_id].consecutive_failures = 0
            self._rebuild_hash_ring()

            # Trigger recovery callbacks
            for callback in self.node_recovery_callbacks:
                try:
                    await callback(node_id)
                except Exception as e:
                    logger.error(f"Error in node recovery callback: {e}")

            logger.info(f"Marked cache node {node_id} as healthy")

    async def health_check_all_nodes(self):
        """Perform health check on all nodes"""
        current_time = time.time()

        for node_id, node in self.nodes.items():
            if current_time - node.last_health_check < self.config.health_check_interval:
                continue

            node.last_health_check = current_time

            if node_id in self.active_clients:
                client = self.active_clients[node_id]
                health = await client.health_check()

                if health['status'] == 'healthy':
                    if node.status != NodeStatus.HEALTHY:
                        await self._mark_node_healthy(node_id)
                else:
                    if node.status == NodeStatus.HEALTHY:
                        await self._mark_node_unhealthy(node_id)

    async def check_consistency(self):
        """Check data consistency across nodes"""
        if not self.config.enable_consistency_checks:
            return

        self.stats['consistency_checks'] += 1

        # Sample some keys to check consistency
        sample_keys = list(self.consistency_map.keys())[:10]  # Check up to 10 keys

        for key in sample_keys:
            values = {}
            for node_id in self.active_clients.keys():
                try:
                    value = await self._get_from_node(node_id, key)
                    values[node_id] = value
                except Exception:
                    continue

            # Check if all values are the same
            unique_values = set(str(v) for v in values.values() if v is not None)
            if len(unique_values) > 1:
                self.stats['consistency_violations'] += 1
                logger.warning(f"Consistency violation for key {key}: {values}")

    def add_node_failure_callback(self, callback: Callable[[str], None]):
        """Add callback for node failure events"""
        self.node_failure_callbacks.append(callback)

    def add_node_recovery_callback(self, callback: Callable[[str], None]):
        """Add callback for node recovery events"""
        self.node_recovery_callbacks.append(callback)

    async def get_cluster_stats(self) -> Dict[str, Any]:
        """Get comprehensive cluster statistics"""
        node_stats = {}
        for node_id, node in self.nodes.items():
            node_stats[node_id] = {
                'status': node.status.value,
                'backend': node.backend.value,
                'weight': node.weight,
                'total_requests': node.total_requests,
                'failed_requests': node.failed_requests,
                'avg_response_time': node.avg_response_time,
                'consecutive_failures': node.consecutive_failures
            }

        return {
            'cluster_name': self.config.cluster_name,
            'total_nodes': len(self.nodes),
            'healthy_nodes': len([n for n in self.nodes.values() if n.status == NodeStatus.HEALTHY]),
            'load_balancing_strategy': self.config.load_balancing_strategy,
            'replication_factor': self.config.replication_factor,
            'stats': self.stats.copy(),
            'node_stats': node_stats
        }

    async def shutdown(self):
        """Shutdown the cluster"""
        logger.info("Shutting down cache cluster")

        # Disconnect all clients
        disconnect_tasks = []
        for client in self.active_clients.values():
            disconnect_tasks.append(client.disconnect())

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        self.active_clients.clear()
        logger.info("Cache cluster shutdown complete")