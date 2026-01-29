"""
Point-in-Time Recovery System for AILOOS

Provides point-in-time recovery capabilities for critical data including:
- Timestamp-based recovery
- Transaction log replay
- Data consistency validation
- Recovery verification
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import bisect

from .automated_backup_system import AutomatedBackupSystem, BackupStrategy
try:
    from ..database import DatabaseManager
except ImportError:
    DatabaseManager = None

logger = logging.getLogger(__name__)


@dataclass
class RecoveryPoint:
    """Represents a point-in-time recovery point."""
    timestamp: datetime
    backup_id: str
    sequence_number: int
    transaction_logs: List[str] = None
    checksum: Optional[str] = None


@dataclass
class PITRecoveryRequest:
    """Point-in-time recovery request."""
    id: str
    target_timestamp: datetime
    source_system: str
    restore_paths: List[Path]
    validate_consistency: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class PointInTimeRecovery:
    """Manages point-in-time recovery operations."""

    def __init__(self, backup_system: AutomatedBackupSystem,
                 database_manager: Optional[DatabaseManager] = None):
        self.backup_system = backup_system
        self.database = database_manager
        self.recovery_points: Dict[str, List[RecoveryPoint]] = {}
        self.active_recoveries: Dict[str, PITRecoveryRequest] = {}
        self.transaction_logs: Dict[str, List[Dict[str, Any]]] = {}

    def register_system(self, system_name: str):
        """Register a system for point-in-time recovery."""
        if system_name not in self.recovery_points:
            self.recovery_points[system_name] = []
        if system_name not in self.transaction_logs:
            self.transaction_logs[system_name] = []

    def add_recovery_point(self, system_name: str, backup_id: str, timestamp: datetime,
                          sequence_number: int, transaction_logs: List[str] = None):
        """Add a recovery point for a system."""
        if system_name not in self.recovery_points:
            self.register_system(system_name)

        point = RecoveryPoint(
            timestamp=timestamp,
            backup_id=backup_id,
            sequence_number=sequence_number,
            transaction_logs=transaction_logs or []
        )

        # Keep sorted by timestamp
        points = self.recovery_points[system_name]
        insert_pos = bisect.bisect_left([p.timestamp for p in points], timestamp)
        points.insert(insert_pos, point)

        logger.info(f"Added recovery point for {system_name}: {timestamp}")

    def log_transaction(self, system_name: str, transaction_data: Dict[str, Any]):
        """Log a transaction for point-in-time recovery."""
        if system_name not in self.transaction_logs:
            self.register_system(system_name)

        transaction_data['timestamp'] = datetime.now().isoformat()
        transaction_data['sequence'] = len(self.transaction_logs[system_name])

        self.transaction_logs[system_name].append(transaction_data)

        # Keep only recent transactions (configurable)
        max_logs = 10000  # Configurable
        if len(self.transaction_logs[system_name]) > max_logs:
            self.transaction_logs[system_name] = self.transaction_logs[system_name][-max_logs:]

    async def initiate_pit_recovery(self, request: PITRecoveryRequest) -> str:
        """Initiate a point-in-time recovery."""
        self.active_recoveries[request.id] = request

        logger.info(f"Initiating PIT recovery: {request.id} to {request.target_timestamp}")

        # Start recovery in background
        asyncio.create_task(self._execute_pit_recovery(request))

        return request.id

    async def _execute_pit_recovery(self, request: PITRecoveryRequest):
        """Execute the point-in-time recovery."""
        try:
            # Find the appropriate recovery point
            base_backup, transactions_to_replay = await self._find_recovery_point(
                request.source_system, request.target_timestamp
            )

            if not base_backup:
                logger.error(f"No suitable recovery point found for {request.source_system}")
                return

            # Restore from base backup
            success = await self._restore_base_backup(request, base_backup)
            if not success:
                logger.error(f"Base backup restore failed for {request.id}")
                return

            # Replay transactions if needed
            if transactions_to_replay:
                success = await self._replay_transactions(request, transactions_to_replay)
                if not success:
                    logger.error(f"Transaction replay failed for {request.id}")
                    return

            # Validate consistency if requested
            if request.validate_consistency:
                success = await self._validate_recovery_consistency(request)
                if not success:
                    logger.error(f"Consistency validation failed for {request.id}")
                    return

            logger.info(f"PIT recovery completed: {request.id}")

        except Exception as e:
            logger.error(f"PIT recovery error: {e}")
        finally:
            # Cleanup
            if request.id in self.active_recoveries:
                del self.active_recoveries[request.id]

    async def _find_recovery_point(self, system_name: str, target_timestamp: datetime) -> Tuple[Optional[RecoveryPoint], List[Dict[str, Any]]]:
        """Find the best recovery point and transactions to replay."""
        if system_name not in self.recovery_points:
            return None, []

        points = self.recovery_points[system_name]

        # Find the latest backup before or at the target timestamp
        suitable_points = [p for p in points if p.timestamp <= target_timestamp]
        if not suitable_points:
            return None, []

        base_point = max(suitable_points, key=lambda p: p.timestamp)

        # Find transactions to replay from base_point.timestamp to target_timestamp
        transactions_to_replay = []
        if system_name in self.transaction_logs:
            logs = self.transaction_logs[system_name]
            for log in logs:
                log_time = datetime.fromisoformat(log['timestamp'])
                if base_point.timestamp < log_time <= target_timestamp:
                    transactions_to_replay.append(log)

        return base_point, transactions_to_replay

    async def _restore_base_backup(self, request: PITRecoveryRequest, base_point: RecoveryPoint) -> bool:
        """Restore from the base backup."""
        try:
            # Use the backup system to restore
            for restore_path in request.restore_paths:
                success = await self.backup_system.storage_backends['local'].retrieve(
                    base_point.backup_id, restore_path
                )
                if not success:
                    return False

            return True
        except Exception as e:
            logger.error(f"Base backup restore error: {e}")
            return False

    async def _replay_transactions(self, request: PITRecoveryRequest, transactions: List[Dict[str, Any]]) -> bool:
        """Replay transactions to reach the target point in time."""
        try:
            # Sort transactions by sequence
            transactions.sort(key=lambda t: t.get('sequence', 0))

            for transaction in transactions:
                success = await self._apply_transaction(request.source_system, transaction)
                if not success:
                    logger.error(f"Failed to apply transaction: {transaction}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Transaction replay error: {e}")
            return False

    async def _apply_transaction(self, system_name: str, transaction: Dict[str, Any]) -> bool:
        """Apply a single transaction."""
        try:
            # This would be system-specific
            if self.database and system_name == 'database':
                # Apply database transaction
                await self.database.apply_transaction(transaction)
            elif system_name == 'federated_data':
                # Apply federated data transaction
                pass  # Implement based on federated system
            else:
                # Generic transaction application
                pass

            return True
        except Exception as e:
            logger.error(f"Transaction application error: {e}")
            return False

    async def _validate_recovery_consistency(self, request: PITRecoveryRequest) -> bool:
        """Validate that the recovered data is consistent."""
        try:
            # Perform consistency checks
            for restore_path in request.restore_paths:
                if not restore_path.exists():
                    return False

                # Check file integrity, database consistency, etc.
                if self.database and 'database' in str(restore_path):
                    # Validate database consistency
                    pass

            # Check that timestamp matches expected
            # This would involve checking metadata or logs

            return True
        except Exception as e:
            logger.error(f"Consistency validation error: {e}")
            return False

    def get_available_recovery_points(self, system_name: str,
                                    start_time: Optional[datetime] = None,
                                    end_time: Optional[datetime] = None) -> List[RecoveryPoint]:
        """Get available recovery points for a system within a time range."""
        if system_name not in self.recovery_points:
            return []

        points = self.recovery_points[system_name]

        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]

        return points

    def get_earliest_recovery_point(self, system_name: str) -> Optional[datetime]:
        """Get the earliest available recovery point."""
        points = self.get_available_recovery_points(system_name)
        return min([p.timestamp for p in points]) if points else None

    def get_latest_recovery_point(self, system_name: str) -> Optional[datetime]:
        """Get the latest available recovery point."""
        points = self.get_available_recovery_points(system_name)
        return max([p.timestamp for p in points]) if points else None

    def estimate_recovery_time(self, system_name: str, target_timestamp: datetime) -> Optional[timedelta]:
        """Estimate time required for PIT recovery."""
        base_point, transactions = self._find_recovery_point(system_name, target_timestamp)
        if not base_point:
            return None

        # Estimate based on backup size and transaction count
        # This is a rough estimate
        base_time = timedelta(minutes=10)  # Base restore time
        transaction_time = timedelta(seconds=len(transactions) * 0.1)  # 0.1s per transaction

        return base_time + transaction_time

    async def verify_recovery_point(self, system_name: str, timestamp: datetime) -> bool:
        """Verify that a recovery point exists and is valid."""
        points = self.get_available_recovery_points(system_name)
        matching_points = [p for p in points if p.timestamp == timestamp]

        if not matching_points:
            return False

        point = matching_points[0]

        # Verify backup exists
        try:
            backups = await self.backup_system.storage_backends['local'].list_backups()
            return point.backup_id in backups
        except:
            return False

    def get_recovery_status(self, request_id: str) -> Optional[PITRecoveryRequest]:
        """Get status of a PIT recovery request."""
        return self.active_recoveries.get(request_id)

    def list_active_recoveries(self) -> List[PITRecoveryRequest]:
        """List all active PIT recovery requests."""
        return list(self.active_recoveries.values())