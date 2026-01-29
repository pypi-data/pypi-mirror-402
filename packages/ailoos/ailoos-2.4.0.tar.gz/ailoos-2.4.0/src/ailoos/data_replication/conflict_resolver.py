import asyncio
import logging
import difflib
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import time
import json

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy(Enum):
    LATEST_WRITER_WINS = "latest_writer_wins"
    MERGE = "merge"
    CUSTOM_RESOLVER = "custom_resolver"
    MANUAL = "manual"
    VECTOR_CLOCK = "vector_clock"

class ConflictType(Enum):
    DATA_MISMATCH = "data_mismatch"
    CONCURRENT_UPDATE = "concurrent_update"
    PARTIAL_UPDATE = "partial_update"
    SCHEMA_CONFLICT = "schema_conflict"

@dataclass
class Conflict:
    conflict_id: str
    data_id: str
    conflicting_versions: List[Dict[str, Any]]
    conflict_type: ConflictType
    detected_at: float
    resolved: bool = False
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    resolved_data: Optional[Any] = None
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = None

@dataclass
class ResolutionRule:
    priority: int
    condition: Callable[[Conflict], bool]
    strategy: ConflictResolutionStrategy
    resolver_function: Optional[Callable] = None

class ConflictResolver:
    """Automatic conflict resolution for data replication"""

    def __init__(self, consistency_manager, replication_manager):
        self.consistency_manager = consistency_manager
        self.replication_manager = replication_manager
        self.conflicts: Dict[str, Conflict] = {}
        self.resolved_conflicts: List[Conflict] = []
        self.resolution_rules: List[ResolutionRule] = []
        self._lock = asyncio.Lock()
        self._conflict_counter = 0

        # Set up default resolution rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Set up default conflict resolution rules"""

        # Rule 1: Latest writer wins for simple conflicts
        self.add_resolution_rule(
            priority=1,
            condition=lambda c: c.conflict_type == ConflictType.CONCURRENT_UPDATE,
            strategy=ConflictResolutionStrategy.LATEST_WRITER_WINS
        )

        # Rule 2: Merge for data mismatch conflicts
        self.add_resolution_rule(
            priority=2,
            condition=lambda c: c.conflict_type == ConflictType.DATA_MISMATCH,
            strategy=ConflictResolutionStrategy.MERGE
        )

        # Rule 3: Manual resolution for schema conflicts
        self.add_resolution_rule(
            priority=3,
            condition=lambda c: c.conflict_type == ConflictType.SCHEMA_CONFLICT,
            strategy=ConflictResolutionStrategy.MANUAL
        )

    def add_resolution_rule(self, priority: int, condition: Callable[[Conflict], bool],
                          strategy: ConflictResolutionStrategy,
                          resolver_function: Optional[Callable] = None) -> None:
        """Add a custom resolution rule"""
        rule = ResolutionRule(
            priority=priority,
            condition=condition,
            strategy=strategy,
            resolver_function=resolver_function
        )

        self.resolution_rules.append(rule)
        self.resolution_rules.sort(key=lambda r: r.priority)

        logger.info(f"Added conflict resolution rule with priority {priority}: {strategy.value}")

    async def detect_conflict(self, data_id: str, conflicting_data: List[Tuple[str, bytes]],
                            conflict_type: ConflictType = ConflictType.DATA_MISMATCH,
                            metadata: Dict[str, Any] = None) -> Optional[Conflict]:
        """Detect and register a data conflict"""
        async with self._lock:
            conflict_id = f"conflict_{self._conflict_counter}"
            self._conflict_counter += 1

            # Convert conflicting data to version format
            conflicting_versions = []
            for node_id, data in conflicting_data:
                try:
                    version_info = {
                        "node_id": node_id,
                        "data": data,
                        "checksum": hashlib.sha256(data).hexdigest(),
                        "size": len(data),
                        "timestamp": time.time()
                    }
                    conflicting_versions.append(version_info)
                except Exception as e:
                    logger.error(f"Failed to process conflicting data from {node_id}: {e}")

            if len(conflicting_versions) < 2:
                logger.warning("Need at least 2 conflicting versions to create conflict")
                return None

            conflict = Conflict(
                conflict_id=conflict_id,
                data_id=data_id,
                conflicting_versions=conflicting_versions,
                conflict_type=conflict_type,
                detected_at=time.time(),
                metadata=metadata or {}
            )

            self.conflicts[conflict_id] = conflict

            # Attempt automatic resolution
            asyncio.create_task(self._resolve_conflict(conflict))

            logger.info(f"Detected conflict {conflict_id} for data {data_id}: {conflict_type.value}")
            return conflict

    async def _resolve_conflict(self, conflict: Conflict) -> None:
        """Attempt to resolve a conflict automatically"""
        try:
            # Find applicable resolution rule
            applicable_rule = None
            for rule in self.resolution_rules:
                if rule.condition(conflict):
                    applicable_rule = rule
                    break

            if not applicable_rule:
                logger.warning(f"No resolution rule found for conflict {conflict.conflict_id}")
                return

            conflict.resolution_strategy = applicable_rule.strategy

            # Apply resolution strategy
            if applicable_rule.strategy == ConflictResolutionStrategy.LATEST_WRITER_WINS:
                resolved_data = await self._resolve_latest_writer_wins(conflict)
            elif applicable_rule.strategy == ConflictResolutionStrategy.MERGE:
                resolved_data = await self._resolve_merge(conflict)
            elif applicable_rule.strategy == ConflictResolutionStrategy.CUSTOM_RESOLVER:
                if applicable_rule.resolver_function:
                    resolved_data = await applicable_rule.resolver_function(conflict)
                else:
                    logger.error(f"No resolver function for custom strategy in conflict {conflict.conflict_id}")
                    return
            elif applicable_rule.strategy == ConflictResolutionStrategy.MANUAL:
                logger.info(f"Conflict {conflict.conflict_id} requires manual resolution")
                return
            else:
                logger.error(f"Unsupported resolution strategy: {applicable_rule.strategy}")
                return

            if resolved_data is not None:
                conflict.resolved_data = resolved_data
                conflict.resolved = True
                conflict.resolved_at = time.time()

                # Propagate resolved data to all nodes
                await self._propagate_resolution(conflict)

                logger.info(f"Successfully resolved conflict {conflict.conflict_id}")
            else:
                logger.error(f"Failed to resolve conflict {conflict.conflict_id}")

        except Exception as e:
            logger.error(f"Error resolving conflict {conflict.conflict_id}: {e}")
        finally:
            # Move to resolved conflicts list
            self._move_conflict_to_resolved(conflict)

    async def _resolve_latest_writer_wins(self, conflict: Conflict) -> Optional[bytes]:
        """Resolve conflict by choosing the latest writer"""
        # Find the version with the latest timestamp
        latest_version = max(conflict.conflicting_versions,
                           key=lambda v: v.get("timestamp", 0))
        return latest_version["data"]

    async def _resolve_merge(self, conflict: Conflict) -> Optional[bytes]:
        """Resolve conflict by merging data"""
        try:
            # For JSON data, attempt intelligent merge
            json_versions = []
            for version in conflict.conflicting_versions:
                try:
                    json_data = json.loads(version["data"].decode('utf-8'))
                    json_versions.append((version, json_data))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, fall back to text merge
                    return await self._resolve_text_merge(conflict)

            if not json_versions:
                return await self._resolve_text_merge(conflict)

            # Perform JSON merge
            merged_data = {}
            all_keys = set()

            for version, json_data in json_versions:
                if isinstance(json_data, dict):
                    all_keys.update(json_data.keys())
                    merged_data.update(json_data)
                else:
                    # For non-dict JSON, use the first version
                    return version["data"]

            # For conflicting keys, prefer the latest timestamp
            for key in all_keys:
                values_with_timestamps = [
                    (json_data.get(key), version.get("timestamp", 0))
                    for version, json_data in json_versions
                    if key in json_data
                ]
                if values_with_timestamps:
                    # Choose the value with latest timestamp
                    latest_value, _ = max(values_with_timestamps, key=lambda x: x[1])
                    merged_data[key] = latest_value

            return json.dumps(merged_data, indent=2).encode('utf-8')

        except Exception as e:
            logger.error(f"JSON merge failed, falling back to text merge: {e}")
            return await self._resolve_text_merge(conflict)

    async def _resolve_text_merge(self, conflict: Conflict) -> Optional[bytes]:
        """Resolve conflict by merging text data"""
        try:
            text_versions = []
            for version in conflict.conflicting_versions:
                try:
                    text = version["data"].decode('utf-8')
                    text_versions.append(text)
                except UnicodeDecodeError:
                    # Binary data, can't merge
                    return conflict.conflicting_versions[0]["data"]

            if len(text_versions) == 2:
                # Use difflib for simple 2-way merge
                merged = self._merge_texts(text_versions[0], text_versions[1])
                return merged.encode('utf-8')
            else:
                # For multiple versions, use the longest one as base
                base_text = max(text_versions, key=len)
                return base_text.encode('utf-8')

        except Exception as e:
            logger.error(f"Text merge failed: {e}")
            # Fall back to first version
            return conflict.conflicting_versions[0]["data"]

    def _merge_texts(self, text1: str, text2: str) -> str:
        """Simple text merge using difflib"""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        # Create unified diff
        diff = list(difflib.unified_diff(lines1, lines2, n=0))

        # Simple merge strategy: prefer longer version for conflicts
        if len(text1) >= len(text2):
            return text1
        else:
            return text2

    async def _propagate_resolution(self, conflict: Conflict) -> None:
        """Propagate resolved data to all replication nodes"""
        if not conflict.resolved_data:
            return

        # Get all active nodes
        active_nodes = await self.replication_manager.get_active_nodes()

        for node_id in active_nodes:
            try:
                success = await self.replication_manager.providers[node_id].replicate_data(
                    conflict.data_id,
                    conflict.resolved_data,
                    {"resolved_conflict": conflict.conflict_id}
                )
                if success:
                    logger.info(f"Propagated resolved data for {conflict.data_id} to node {node_id}")
                else:
                    logger.error(f"Failed to propagate resolved data to node {node_id}")
            except Exception as e:
                logger.error(f"Error propagating to node {node_id}: {e}")

    def _move_conflict_to_resolved(self, conflict: Conflict) -> None:
        """Move resolved conflict to completed list"""
        if conflict.conflict_id in self.conflicts:
            del self.conflicts[conflict.conflict_id]
        self.resolved_conflicts.append(conflict)

        # Keep only last 200 resolved conflicts
        if len(self.resolved_conflicts) > 200:
            self.resolved_conflicts = self.resolved_conflicts[-200:]

    async def get_conflict_status(self, conflict_id: str) -> Optional[Conflict]:
        """Get status of a conflict"""
        if conflict_id in self.conflicts:
            return self.conflicts[conflict_id]

        for conflict in self.resolved_conflicts:
            if conflict.conflict_id == conflict_id:
                return conflict
        return None

    async def resolve_conflict_manually(self, conflict_id: str, resolved_data: bytes,
                                      resolution_notes: str = "") -> bool:
        """Manually resolve a conflict"""
        async with self._lock:
            conflict = self.conflicts.get(conflict_id)
            if not conflict:
                logger.error(f"Conflict {conflict_id} not found")
                return False

            conflict.resolved = True
            conflict.resolved_data = resolved_data
            conflict.resolved_at = time.time()
            conflict.resolution_strategy = ConflictResolutionStrategy.MANUAL
            conflict.metadata["manual_resolution_notes"] = resolution_notes

            await self._propagate_resolution(conflict)
            self._move_conflict_to_resolved(conflict)

            logger.info(f"Manually resolved conflict {conflict_id}")
            return True

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict resolution statistics"""
        total_conflicts = len(self.resolved_conflicts) + len(self.conflicts)
        resolved_conflicts = len(self.resolved_conflicts)
        active_conflicts = len(self.conflicts)

        resolution_methods = {}
        for conflict in self.resolved_conflicts:
            method = conflict.resolution_strategy.value if conflict.resolution_strategy else "unknown"
            resolution_methods[method] = resolution_methods.get(method, 0) + 1

        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "active_conflicts": active_conflicts,
            "resolution_rate": resolved_conflicts / total_conflicts if total_conflicts > 0 else 1.0,
            "resolution_methods": resolution_methods
        }

    async def cleanup_old_conflicts(self, max_age_days: int = 30) -> int:
        """Clean up old resolved conflicts"""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        cleaned_count = 0

        async with self._lock:
            filtered_conflicts = [
                c for c in self.resolved_conflicts
                if c.resolved_at and c.resolved_at > cutoff_time
            ]
            cleaned_count = len(self.resolved_conflicts) - len(filtered_conflicts)
            self.resolved_conflicts = filtered_conflicts

        logger.info(f"Cleaned up {cleaned_count} old resolved conflicts")
        return cleaned_count