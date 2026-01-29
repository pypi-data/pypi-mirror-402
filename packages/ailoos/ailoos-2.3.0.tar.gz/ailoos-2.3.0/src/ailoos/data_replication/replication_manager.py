import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class ReplicationStrategy(Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    SEMI_SYNCHRONOUS = "semi_synchronous"

class ReplicationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

@dataclass
class ReplicationNode:
    node_id: str
    region: str
    endpoint: str
    priority: int = 1
    is_active: bool = True
    last_heartbeat: float = 0.0

@dataclass
class ReplicationTask:
    task_id: str
    data_id: str
    source_node: str
    target_nodes: List[str]
    strategy: ReplicationStrategy
    status: ReplicationStatus
    created_at: float
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

class ReplicationProvider(ABC):
    """Abstract base class for replication providers"""

    def __init__(self, node: ReplicationNode):
        self.node = node
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to replication node"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from replication node"""
        pass

    @abstractmethod
    async def replicate_data(self, data_id: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Replicate data to this node"""
        pass

    @abstractmethod
    async def get_data(self, data_id: str) -> Optional[bytes]:
        """Retrieve data from this node"""
        pass

    @abstractmethod
    async def delete_data(self, data_id: str) -> bool:
        """Delete data from this node"""
        pass

    @abstractmethod
    async def get_node_status(self) -> Dict[str, Any]:
        """Get node status and metrics"""
        pass

    @property
    def is_connected(self) -> bool:
        return self._is_connected

class LocalReplicationProvider(ReplicationProvider):
    """Local replication provider for testing"""

    def __init__(self, node: ReplicationNode):
        super().__init__(node)
        self._data_store: Dict[str, bytes] = {}
        self._metadata_store: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> bool:
        try:
            await asyncio.sleep(0.01)
            self._is_connected = True
            logger.info(f"Connected to local replication node: {self.node.node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local node {self.node.node_id}: {e}")
            return False

    async def disconnect(self) -> None:
        self._is_connected = False
        logger.info(f"Disconnected from local replication node: {self.node.node_id}")

    async def replicate_data(self, data_id: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        if not self.is_connected:
            return False
        try:
            await asyncio.sleep(0.02)
            self._data_store[data_id] = data
            self._metadata_store[data_id] = metadata.copy()
            logger.info(f"Replicated data {data_id} to local node {self.node.node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to replicate data {data_id}: {e}")
            return False

    async def get_data(self, data_id: str) -> Optional[bytes]:
        if not self.is_connected:
            return None
        return self._data_store.get(data_id)

    async def delete_data(self, data_id: str) -> bool:
        if not self.is_connected:
            return False
        if data_id in self._data_store:
            del self._data_store[data_id]
            if data_id in self._metadata_store:
                del self._metadata_store[data_id]
            logger.info(f"Deleted data {data_id} from local node {self.node.node_id}")
            return True
        return False

    async def get_node_status(self) -> Dict[str, Any]:
        return {
            "node_id": self.node.node_id,
            "region": self.node.region,
            "data_count": len(self._data_store),
            "is_connected": self.is_connected,
            "last_heartbeat": time.time()
        }

class ReplicationManager:
    """Main replication manager for coordinating data replication across nodes"""

    def __init__(self):
        self.nodes: Dict[str, ReplicationNode] = {}
        self.providers: Dict[str, ReplicationProvider] = {}
        self.active_tasks: Dict[str, ReplicationTask] = {}
        self.completed_tasks: List[ReplicationTask] = []
        self._lock = asyncio.Lock()
        self._task_counter = 0

    async def add_node(self, node: ReplicationNode) -> bool:
        """Add a replication node"""
        async with self._lock:
            if node.node_id in self.nodes:
                logger.warning(f"Node {node.node_id} already exists")
                return False

            self.nodes[node.node_id] = node
            provider = LocalReplicationProvider(node)  # For now, use local provider

            if await provider.connect():
                self.providers[node.node_id] = provider
                logger.info(f"Added replication node: {node.node_id}")
                return True
            else:
                logger.error(f"Failed to connect to node {node.node_id}")
                return False

    async def remove_node(self, node_id: str) -> bool:
        """Remove a replication node"""
        async with self._lock:
            if node_id not in self.nodes:
                return False

            if node_id in self.providers:
                await self.providers[node_id].disconnect()
                del self.providers[node_id]

            del self.nodes[node_id]
            logger.info(f"Removed replication node: {node_id}")
            return True

    async def replicate_data(self, data_id: str, data: bytes, target_nodes: List[str] = None,
                           strategy: ReplicationStrategy = ReplicationStrategy.ASYNCHRONOUS,
                           metadata: Dict[str, Any] = None) -> Optional[str]:
        """Replicate data to specified nodes or all available nodes"""
        async with self._lock:
            if not self.providers:
                logger.error("No replication nodes available")
                return None

            target_nodes = target_nodes or list(self.providers.keys())
            available_nodes = [node for node in target_nodes if node in self.providers]

            if not available_nodes:
                logger.error("No available target nodes")
                return None

            task_id = f"repl_{self._task_counter}"
            self._task_counter += 1

            task = ReplicationTask(
                task_id=task_id,
                data_id=data_id,
                source_node="local",  # Assuming local source for now
                target_nodes=available_nodes,
                strategy=strategy,
                status=ReplicationStatus.PENDING,
                created_at=time.time(),
                metadata=metadata or {}
            )

            self.active_tasks[task_id] = task

            # Start replication based on strategy
            if strategy == ReplicationStrategy.SYNCHRONOUS:
                await self._execute_synchronous_replication(task, data)
            else:
                asyncio.create_task(self._execute_asynchronous_replication(task, data))

            logger.info(f"Started replication task {task_id} for data {data_id}")
            return task_id

    async def _execute_synchronous_replication(self, task: ReplicationTask, data: bytes) -> None:
        """Execute synchronous replication"""
        task.status = ReplicationStatus.IN_PROGRESS
        success_count = 0

        for node_id in task.target_nodes:
            if node_id in self.providers:
                provider = self.providers[node_id]
                if await provider.replicate_data(task.data_id, data, task.metadata):
                    success_count += 1
                else:
                    logger.error(f"Failed to replicate to node {node_id}")

        if success_count == len(task.target_nodes):
            task.status = ReplicationStatus.COMPLETED
        else:
            task.status = ReplicationStatus.FAILED

        task.completed_at = time.time()
        self._move_task_to_completed(task)

    async def _execute_asynchronous_replication(self, task: ReplicationTask, data: bytes) -> None:
        """Execute asynchronous replication"""
        task.status = ReplicationStatus.IN_PROGRESS

        # For simplicity, execute all replications concurrently
        replication_tasks = []
        for node_id in task.target_nodes:
            if node_id in self.providers:
                provider = self.providers[node_id]
                replication_tasks.append(
                    provider.replicate_data(task.data_id, data, task.metadata)
                )

        results = await asyncio.gather(*replication_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True and not isinstance(result, Exception))

        if success_count == len(task.target_nodes):
            task.status = ReplicationStatus.COMPLETED
        elif success_count > 0:
            task.status = ReplicationStatus.CONFLICT  # Partial success
        else:
            task.status = ReplicationStatus.FAILED

        task.completed_at = time.time()
        self._move_task_to_completed(task)

    def _move_task_to_completed(self, task: ReplicationTask) -> None:
        """Move completed task from active to completed list"""
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        self.completed_tasks.append(task)
        # Keep only last 1000 completed tasks
        if len(self.completed_tasks) > 1000:
            self.completed_tasks = self.completed_tasks[-1000:]

    async def get_replication_status(self, task_id: str) -> Optional[ReplicationTask]:
        """Get status of a replication task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]

        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None

    async def get_data_from_node(self, data_id: str, node_id: str) -> Optional[bytes]:
        """Retrieve data from a specific node"""
        if node_id not in self.providers:
            return None

        provider = self.providers[node_id]
        return await provider.get_data(data_id)

    async def delete_data_from_nodes(self, data_id: str, node_ids: List[str] = None) -> Dict[str, bool]:
        """Delete data from specified nodes or all nodes"""
        node_ids = node_ids or list(self.providers.keys())
        results = {}

        for node_id in node_ids:
            if node_id in self.providers:
                provider = self.providers[node_id]
                results[node_id] = await provider.delete_data(data_id)
            else:
                results[node_id] = False

        return results

    def list_nodes(self) -> List[str]:
        """List all configured nodes"""
        return list(self.nodes.keys())

    def get_active_nodes(self) -> List[str]:
        """Get list of active nodes"""
        return [node_id for node_id, node in self.nodes.items() if node.is_active]

    async def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific node"""
        if node_id not in self.providers:
            return None

        provider = self.providers[node_id]
        return await provider.get_node_status()

    async def get_all_node_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all nodes"""
        status = {}
        for node_id, provider in self.providers.items():
            try:
                status[node_id] = await provider.get_node_status()
            except Exception as e:
                logger.error(f"Failed to get status for node {node_id}: {e}")
                status[node_id] = {"error": str(e)}
        return status

    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all nodes"""
        health = {}
        for node_id, provider in self.providers.items():
            health[node_id] = provider.is_connected
        return health