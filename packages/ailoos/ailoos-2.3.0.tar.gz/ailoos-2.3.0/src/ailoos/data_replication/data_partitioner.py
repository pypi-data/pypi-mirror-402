import asyncio
import logging
import hashlib
import math
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class PartitionStrategy(Enum):
    HASH_BASED = "hash_based"
    RANGE_BASED = "range_based"
    CONSISTENT_HASHING = "consistent_hashing"
    GEOGRAPHIC = "geographic"
    LOAD_BALANCED = "load_balanced"

class PartitionKeyType(Enum):
    STRING = "string"
    NUMERIC = "numeric"
    UUID = "uuid"
    COMPOSITE = "composite"

@dataclass
class Partition:
    partition_id: str
    node_ids: List[str]
    key_range: Tuple[Any, Any] = None  # For range-based partitioning
    token_range: Tuple[int, int] = None  # For consistent hashing
    metadata: Dict[str, Any] = None

@dataclass
class PartitionKey:
    key_type: PartitionKeyType
    key_value: Any
    key_extractor: Optional[Callable] = None

@dataclass
class PartitionConfig:
    strategy: PartitionStrategy
    num_partitions: int
    replication_factor: int
    partition_key: PartitionKey
    enable_rebalancing: bool = True
    rebalance_threshold: float = 0.1  # 10% imbalance threshold

class DataPartitioner:
    """Intelligent data partitioning for replication"""

    def __init__(self, replication_manager):
        self.replication_manager = replication_manager
        self.partitions: Dict[str, Partition] = {}
        self.data_to_partition: Dict[str, str] = {}
        self.node_to_partitions: Dict[str, Set[str]] = defaultdict(set)
        self.config: Optional[PartitionConfig] = None

        # Consistent hashing ring
        self.hash_ring: List[Tuple[int, str]] = []
        self.ring_replicas = 100  # Virtual nodes per physical node

        self._lock = asyncio.Lock()

    def configure_partitioning(self, config: PartitionConfig) -> None:
        """Configure the partitioning strategy"""
        self.config = config
        logger.info(f"Configured partitioning with strategy: {config.strategy.value}")

        # Initialize partitions based on strategy
        if config.strategy == PartitionStrategy.CONSISTENT_HASHING:
            self._initialize_consistent_hashing()
        elif config.strategy == PartitionStrategy.HASH_BASED:
            self._initialize_hash_based()
        elif config.strategy == PartitionStrategy.RANGE_BASED:
            self._initialize_range_based()

    def _initialize_consistent_hashing(self) -> None:
        """Initialize consistent hashing ring"""
        if not self.config:
            return

        self.hash_ring = []
        active_nodes = self.replication_manager.list_nodes()

        for node_id in active_nodes:
            # Create virtual nodes for each physical node
            for i in range(self.ring_replicas):
                token = self._hash(f"{node_id}:{i}")
                self.hash_ring.append((token, node_id))

        self.hash_ring.sort()  # Sort by token

        # Create partitions based on token ranges
        self.partitions = {}
        ring_size = len(self.hash_ring)

        for i in range(ring_size):
            token_start = self.hash_ring[i][0]
            token_end = self.hash_ring[(i + 1) % ring_size][0]
            node_id = self.hash_ring[i][1]

            partition_id = f"partition_{i}"
            partition = Partition(
                partition_id=partition_id,
                node_ids=[node_id],
                token_range=(token_start, token_end)
            )

            self.partitions[partition_id] = partition
            self.node_to_partitions[node_id].add(partition_id)

    def _initialize_hash_based(self) -> None:
        """Initialize hash-based partitioning"""
        if not self.config:
            return

        active_nodes = self.replication_manager.list_nodes()
        if not active_nodes:
            return

        self.partitions = {}
        nodes_per_partition = max(1, len(active_nodes) // self.config.num_partitions)

        for i in range(self.config.num_partitions):
            start_idx = i * nodes_per_partition
            end_idx = min((i + 1) * nodes_per_partition, len(active_nodes))
            partition_nodes = active_nodes[start_idx:end_idx]

            partition_id = f"partition_{i}"
            partition = Partition(
                partition_id=partition_id,
                node_ids=partition_nodes
            )

            self.partitions[partition_id] = partition
            for node_id in partition_nodes:
                self.node_to_partitions[node_id].add(partition_id)

    def _initialize_range_based(self) -> None:
        """Initialize range-based partitioning"""
        if not self.config:
            return

        # For numeric ranges, divide the key space
        active_nodes = self.replication_manager.list_nodes()
        if not active_nodes:
            return

        self.partitions = {}
        total_range = 1000  # Assume 0-1000 range for demo
        range_per_partition = total_range // self.config.num_partitions

        for i in range(self.config.num_partitions):
            range_start = i * range_per_partition
            range_end = (i + 1) * range_per_partition if i < self.config.num_partitions - 1 else total_range

            # Assign nodes round-robin
            node_id = active_nodes[i % len(active_nodes)]

            partition_id = f"partition_{i}"
            partition = Partition(
                partition_id=partition_id,
                node_ids=[node_id],
                key_range=(range_start, range_end)
            )

            self.partitions[partition_id] = partition
            self.node_to_partitions[node_id].add(partition_id)

    def _hash(self, key: str) -> int:
        """Generate hash for a key"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    async def get_partition_for_data(self, data_id: str, data: Optional[bytes] = None) -> Optional[str]:
        """Determine which partition a data item belongs to"""
        async with self._lock:
            if not self.config:
                return None

            if data_id in self.data_to_partition:
                return self.data_to_partition[data_id]

            partition_id = None

            if self.config.strategy == PartitionStrategy.CONSISTENT_HASHING:
                partition_id = self._get_consistent_hash_partition(data_id)
            elif self.config.strategy == PartitionStrategy.HASH_BASED:
                partition_id = self._get_hash_based_partition(data_id)
            elif self.config.strategy == PartitionStrategy.RANGE_BASED:
                partition_id = self._get_range_based_partition(data_id, data)
            elif self.config.strategy == PartitionStrategy.LOAD_BALANCED:
                partition_id = self._get_load_balanced_partition()

            if partition_id:
                self.data_to_partition[data_id] = partition_id

            return partition_id

    def _get_consistent_hash_partition(self, data_id: str) -> Optional[str]:
        """Get partition using consistent hashing"""
        if not self.hash_ring:
            return None

        key_hash = self._hash(data_id)

        # Find the first node with token >= key_hash
        for token, node_id in self.hash_ring:
            if token >= key_hash:
                # Find partition for this node
                for partition_id, partition in self.partitions.items():
                    if node_id in partition.node_ids:
                        return partition_id

        # Wrap around to first partition
        if self.partitions:
            return next(iter(self.partitions.keys()))

        return None

    def _get_hash_based_partition(self, data_id: str) -> Optional[str]:
        """Get partition using hash-based partitioning"""
        if not self.partitions:
            return None

        partition_count = len(self.partitions)
        hash_value = self._hash(data_id)
        partition_index = hash_value % partition_count

        partition_ids = list(self.partitions.keys())
        return partition_ids[partition_index]

    def _get_range_based_partition(self, data_id: str, data: Optional[bytes]) -> Optional[str]:
        """Get partition using range-based partitioning"""
        if not self.config or not self.partitions:
            return None

        # Extract numeric key from data_id or data
        try:
            if self.config.partition_key.key_type == PartitionKeyType.NUMERIC:
                key_value = int(data_id.split('_')[-1])  # Extract number from ID
            else:
                key_value = self._hash(data_id) % 1000  # Fallback to hash

            for partition in self.partitions.values():
                if partition.key_range and partition.key_range[0] <= key_value < partition.key_range[1]:
                    return partition.partition_id

        except (ValueError, IndexError):
            # Fallback to first partition
            return next(iter(self.partitions.keys()), None)

        return None

    def _get_load_balanced_partition(self) -> Optional[str]:
        """Get partition using load balancing"""
        if not self.partitions:
            return None

        # Find partition with least data items
        min_load = float('inf')
        selected_partition = None

        for partition_id, partition in self.partitions.items():
            # Count data items in this partition
            load = sum(1 for pid in self.data_to_partition.values() if pid == partition_id)
            if load < min_load:
                min_load = load
                selected_partition = partition_id

        return selected_partition

    async def replicate_to_partition(self, data_id: str, data: bytes,
                                   metadata: Dict[str, Any] = None) -> List[str]:
        """Replicate data to its assigned partition"""
        partition_id = await self.get_partition_for_data(data_id, data)

        if not partition_id or partition_id not in self.partitions:
            logger.error(f"No valid partition found for data {data_id}")
            return []

        partition = self.partitions[partition_id]
        target_nodes = partition.node_ids

        # Replicate to all nodes in the partition
        task_id = await self.replication_manager.replicate_data(
            data_id, data, target_nodes, metadata=metadata
        )

        if task_id:
            logger.info(f"Replicated data {data_id} to partition {partition_id} nodes: {target_nodes}")
            return target_nodes
        else:
            logger.error(f"Failed to replicate data {data_id} to partition {partition_id}")
            return []

    async def add_node_to_partitioning(self, node_id: str) -> None:
        """Add a new node to the partitioning scheme"""
        async with self._lock:
            if not self.config:
                return

            if self.config.strategy == PartitionStrategy.CONSISTENT_HASHING:
                await self._add_node_consistent_hashing(node_id)
            elif self.config.enable_rebalancing:
                await self._rebalance_partitions()

            logger.info(f"Added node {node_id} to partitioning")

    async def remove_node_from_partitioning(self, node_id: str) -> None:
        """Remove a node from the partitioning scheme"""
        async with self._lock:
            if node_id not in self.node_to_partitions:
                return

            affected_partitions = self.node_to_partitions[node_id]

            if self.config and self.config.strategy == PartitionStrategy.CONSISTENT_HASHING:
                await self._remove_node_consistent_hashing(node_id)
            elif self.config and self.config.enable_rebalancing:
                await self._rebalance_partitions()

            # Clean up data to partition mapping for affected partitions
            data_to_remove = [
                data_id for data_id, pid in self.data_to_partition.items()
                if pid in affected_partitions
            ]
            for data_id in data_to_remove:
                del self.data_to_partition[data_id]

            del self.node_to_partitions[node_id]
            logger.info(f"Removed node {node_id} from partitioning")

    async def _add_node_consistent_hashing(self, node_id: str) -> None:
        """Add node to consistent hashing ring"""
        # Add virtual nodes to ring
        for i in range(self.ring_replicas):
            token = self._hash(f"{node_id}:{i}")
            self.hash_ring.append((token, node_id))

        self.hash_ring.sort()

        # Rebuild partitions
        self._initialize_consistent_hashing()

    async def _remove_node_consistent_hashing(self, node_id: str) -> None:
        """Remove node from consistent hashing ring"""
        # Remove all virtual nodes for this node
        self.hash_ring = [(token, nid) for token, nid in self.hash_ring if nid != node_id]

        # Rebuild partitions
        self._initialize_consistent_hashing()

    async def _rebalance_partitions(self) -> None:
        """Rebalance partitions across available nodes"""
        if not self.config:
            return

        active_nodes = self.replication_manager.list_nodes()
        if not active_nodes:
            return

        # Simple rebalancing: redistribute partitions evenly
        partitions_per_node = math.ceil(len(self.partitions) / len(active_nodes))

        new_node_to_partitions = defaultdict(set)
        partition_list = list(self.partitions.keys())

        for i, partition_id in enumerate(partition_list):
            node_index = i % len(active_nodes)
            node_id = active_nodes[node_index]
            new_node_to_partitions[node_id].add(partition_id)

            # Update partition node assignment
            if partition_id in self.partitions:
                self.partitions[partition_id].node_ids = [node_id]

        self.node_to_partitions = new_node_to_partitions
        logger.info("Rebalanced partitions across nodes")

    def get_partition_info(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a partition"""
        if partition_id not in self.partitions:
            return None

        partition = self.partitions[partition_id]
        data_count = sum(1 for pid in self.data_to_partition.values() if pid == partition_id)

        return {
            "partition_id": partition.partition_id,
            "node_ids": partition.node_ids,
            "key_range": partition.key_range,
            "token_range": partition.token_range,
            "data_count": data_count
        }

    def get_partition_stats(self) -> Dict[str, Any]:
        """Get partitioning statistics"""
        total_data = len(self.data_to_partition)
        partition_loads = {}

        for partition_id in self.partitions.keys():
            load = sum(1 for pid in self.data_to_partition.values() if pid == partition_id)
            partition_loads[partition_id] = load

        avg_load = total_data / len(self.partitions) if self.partitions else 0
        max_load = max(partition_loads.values()) if partition_loads else 0
        min_load = min(partition_loads.values()) if partition_loads else 0

        imbalance_ratio = max_load / avg_load if avg_load > 0 else 0

        return {
            "total_partitions": len(self.partitions),
            "total_data_items": total_data,
            "average_load": avg_load,
            "max_load": max_load,
            "min_load": min_load,
            "load_imbalance_ratio": imbalance_ratio,
            "partition_loads": partition_loads
        }

    async def optimize_partitions(self) -> None:
        """Optimize partition distribution"""
        async with self._lock:
            stats = self.get_partition_stats()

            if self.config and self.config.enable_rebalancing:
                imbalance_ratio = stats["load_imbalance_ratio"]
                if imbalance_ratio > (1 + self.config.rebalance_threshold):
                    logger.info(f"Partition imbalance detected (ratio: {imbalance_ratio:.2f}), rebalancing...")
                    await self._rebalance_partitions()
                else:
                    logger.info("Partitions are well balanced")

    def list_partitions(self) -> List[str]:
        """List all partition IDs"""
        return list(self.partitions.keys())

    def get_node_partitions(self, node_id: str) -> List[str]:
        """Get partitions assigned to a node"""
        return list(self.node_to_partitions.get(node_id, []))