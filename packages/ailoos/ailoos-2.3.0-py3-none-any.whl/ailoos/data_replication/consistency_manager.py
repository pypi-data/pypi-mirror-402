import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class ConsistencyLevel(Enum):
    STRONG = "strong"  # All replicas must be consistent
    EVENTUAL = "eventual"  # Consistency achieved over time
    CAUSAL = "causal"  # Causal consistency
    READ_YOUR_WRITES = "read_your_writes"  # Read what you wrote

class ConsistencyStatus(Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    CHECKING = "checking"
    REPAIRING = "repairing"

@dataclass
class DataVersion:
    data_id: str
    version: int
    checksum: str
    timestamp: float
    node_id: str
    size: int
    metadata: Dict[str, Any]

@dataclass
class ConsistencyCheck:
    check_id: str
    data_id: str
    nodes_checked: List[str]
    status: ConsistencyStatus
    started_at: float
    completed_at: Optional[float] = None
    inconsistencies_found: List[str] = None
    repair_actions: List[str] = None

class ConsistencyManager:
    """Manages data consistency across replication nodes"""

    def __init__(self, replication_manager):
        self.replication_manager = replication_manager
        self.consistency_level = ConsistencyLevel.EVENTUAL
        self.version_history: Dict[str, List[DataVersion]] = {}
        self.active_checks: Dict[str, ConsistencyCheck] = {}
        self.completed_checks: List[ConsistencyCheck] = []
        self._lock = asyncio.Lock()
        self._check_counter = 0

    def set_consistency_level(self, level: ConsistencyLevel) -> None:
        """Set the consistency level"""
        self.consistency_level = level
        logger.info(f"Set consistency level to: {level.value}")

    async def record_data_version(self, data_id: str, data: bytes, node_id: str,
                                metadata: Dict[str, Any] = None) -> DataVersion:
        """Record a new version of data"""
        async with self._lock:
            checksum = hashlib.sha256(data).hexdigest()
            version_num = len(self.version_history.get(data_id, [])) + 1

            version = DataVersion(
                data_id=data_id,
                version=version_num,
                checksum=checksum,
                timestamp=time.time(),
                node_id=node_id,
                size=len(data),
                metadata=metadata or {}
            )

            if data_id not in self.version_history:
                self.version_history[data_id] = []
            self.version_history[data_id].append(version)

            # Keep only last 10 versions
            if len(self.version_history[data_id]) > 10:
                self.version_history[data_id] = self.version_history[data_id][-10:]

            logger.info(f"Recorded version {version_num} for data {data_id} on node {node_id}")
            return version

    async def check_consistency(self, data_id: str, nodes: List[str] = None) -> Optional[ConsistencyCheck]:
        """Check consistency of data across nodes"""
        async with self._lock:
            nodes = nodes or await self.replication_manager.get_active_nodes()
            if not nodes:
                logger.warning("No nodes available for consistency check")
                return None

            check_id = f"check_{self._check_counter}"
            self._check_counter += 1

            check = ConsistencyCheck(
                check_id=check_id,
                data_id=data_id,
                nodes_checked=nodes.copy(),
                status=ConsistencyStatus.CHECKING,
                started_at=time.time()
            )

            self.active_checks[check_id] = check
            asyncio.create_task(self._perform_consistency_check(check))

            logger.info(f"Started consistency check {check_id} for data {data_id}")
            return check

    async def _perform_consistency_check(self, check: ConsistencyCheck) -> None:
        """Perform the actual consistency check"""
        try:
            # Get data from all nodes
            data_versions = {}
            for node_id in check.nodes_checked:
                try:
                    data = await self.replication_manager.get_data_from_node(check.data_id, node_id)
                    if data is not None:
                        checksum = hashlib.sha256(data).hexdigest()
                        data_versions[node_id] = checksum
                    else:
                        data_versions[node_id] = None
                except Exception as e:
                    logger.error(f"Failed to get data from node {node_id}: {e}")
                    data_versions[node_id] = None

            # Analyze consistency
            checksums = [cs for cs in data_versions.values() if cs is not None]
            unique_checksums = set(checksums)

            if len(unique_checksums) <= 1:
                # All nodes have the same data or no data
                check.status = ConsistencyStatus.CONSISTENT
                check.inconsistencies_found = []
            else:
                # Inconsistencies found
                check.status = ConsistencyStatus.INCONSISTENT
                check.inconsistencies_found = [
                    f"Node {node}: {cs}" for node, cs in data_versions.items()
                ]

                # For strong consistency, trigger repair
                if self.consistency_level == ConsistencyLevel.STRONG:
                    await self._repair_inconsistency(check, data_versions)

            check.completed_at = time.time()
            self._move_check_to_completed(check)

        except Exception as e:
            logger.error(f"Consistency check failed: {e}")
            check.status = ConsistencyStatus.INCONSISTENT
            check.inconsistencies_found = [str(e)]
            check.completed_at = time.time()
            self._move_check_to_completed(check)

    async def _repair_inconsistency(self, check: ConsistencyCheck, data_versions: Dict[str, Optional[str]]) -> None:
        """Repair data inconsistency"""
        check.status = ConsistencyStatus.REPAIRING

        # Find the most recent version from version history
        if check.data_id in self.version_history:
            latest_version = max(self.version_history[check.data_id], key=lambda v: v.timestamp)
            latest_checksum = latest_version.checksum

            # Get the data from the node that has the latest version
            source_data = None
            for node_id, checksum in data_versions.items():
                if checksum == latest_checksum:
                    source_data = await self.replication_manager.get_data_from_node(check.data_id, node_id)
                    break

            if source_data:
                # Replicate correct data to inconsistent nodes
                inconsistent_nodes = [
                    node for node, cs in data_versions.items()
                    if cs != latest_checksum
                ]

                for node_id in inconsistent_nodes:
                    success = await self.replication_manager.providers[node_id].replicate_data(
                        check.data_id, source_data, latest_version.metadata
                    )
                    if success:
                        logger.info(f"Repaired data {check.data_id} on node {node_id}")
                    else:
                        logger.error(f"Failed to repair data {check.data_id} on node {node_id}")

                check.repair_actions = [
                    f"Replicated latest version to nodes: {', '.join(inconsistent_nodes)}"
                ]
            else:
                logger.error(f"Could not find source data for repair of {check.data_id}")
                check.repair_actions = ["Failed to find source data for repair"]
        else:
            logger.warning(f"No version history available for {check.data_id}")
            check.repair_actions = ["No version history available"]

    def _move_check_to_completed(self, check: ConsistencyCheck) -> None:
        """Move completed check from active to completed list"""
        if check.check_id in self.active_checks:
            del self.active_checks[check.check_id]
        self.completed_checks.append(check)
        # Keep only last 500 completed checks
        if len(self.completed_checks) > 500:
            self.completed_checks = self.completed_checks[-500:]

    async def get_consistency_status(self, check_id: str) -> Optional[ConsistencyCheck]:
        """Get status of a consistency check"""
        if check_id in self.active_checks:
            return self.active_checks[check_id]

        for check in self.completed_checks:
            if check.check_id == check_id:
                return check
        return None

    async def get_data_versions(self, data_id: str) -> List[DataVersion]:
        """Get version history for data"""
        return self.version_history.get(data_id, [])

    async def get_latest_version(self, data_id: str) -> Optional[DataVersion]:
        """Get the latest version of data"""
        versions = self.version_history.get(data_id, [])
        return max(versions, key=lambda v: v.timestamp) if versions else None

    async def validate_data_integrity(self, data_id: str, data: bytes) -> Tuple[bool, str]:
        """Validate data integrity against known versions"""
        checksum = hashlib.sha256(data).hexdigest()
        versions = self.version_history.get(data_id, [])

        for version in versions:
            if version.checksum == checksum:
                return True, f"Data matches version {version.version}"

        return False, f"Data checksum {checksum} not found in version history"

    async def bulk_consistency_check(self, data_ids: List[str] = None,
                                   nodes: List[str] = None) -> Dict[str, ConsistencyCheck]:
        """Perform consistency checks for multiple data items"""
        if data_ids is None:
            # Check all data that has version history
            data_ids = list(self.version_history.keys())

        checks = {}
        for data_id in data_ids:
            check = await self.check_consistency(data_id, nodes)
            if check:
                checks[data_id] = check

        return checks

    def get_consistency_stats(self) -> Dict[str, Any]:
        """Get consistency statistics"""
        total_checks = len(self.completed_checks)
        consistent_checks = sum(1 for check in self.completed_checks
                              if check.status == ConsistencyStatus.CONSISTENT)
        inconsistent_checks = sum(1 for check in self.completed_checks
                                if check.status == ConsistencyStatus.INCONSISTENT)

        return {
            "total_checks": total_checks,
            "consistent_checks": consistent_checks,
            "inconsistent_checks": inconsistent_checks,
            "consistency_rate": consistent_checks / total_checks if total_checks > 0 else 1.0,
            "active_checks": len(self.active_checks),
            "tracked_data_items": len(self.version_history)
        }

    async def cleanup_old_versions(self, max_age_days: int = 30) -> int:
        """Clean up old version history"""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        cleaned_count = 0

        async with self._lock:
            for data_id, versions in self.version_history.items():
                # Keep at least one version, and versions newer than cutoff
                filtered_versions = [
                    v for v in versions
                    if v.timestamp > cutoff_time or v == max(versions, key=lambda x: x.timestamp)
                ]
                if len(filtered_versions) < len(versions):
                    cleaned_count += len(versions) - len(filtered_versions)
                    self.version_history[data_id] = filtered_versions

        logger.info(f"Cleaned up {cleaned_count} old data versions")
        return cleaned_count