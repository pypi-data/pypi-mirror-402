"""
Recovery Orchestrator for AILOOS

Orchestrates automatic recovery operations including:
- Health monitoring and failure detection
- Automated recovery triggering
- Recovery workflow management
- Rollback coordination
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import json

from .automated_backup_system import AutomatedBackupSystem, BackupStrategy
from ..monitoring import UnifiedMonitoringSystem as MonitoringSystem
from ..notifications import NotificationService

logger = logging.getLogger(__name__)


class RecoveryType(Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    EMERGENCY = "emergency"


class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RecoveryJob:
    """Represents a recovery operation."""
    id: str
    recovery_type: RecoveryType
    target_system: str
    backup_source: str
    restore_paths: List[Path]
    status: RecoveryStatus = RecoveryStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RecoveryOrchestrator:
    """Orchestrates recovery operations across the system."""

    def __init__(self, backup_system: AutomatedBackupSystem,
                 monitoring_system: Optional[MonitoringSystem] = None,
                 notification_service: Optional[NotificationService] = None):
        self.backup_system = backup_system
        self.monitoring = monitoring_system
        self.notifications = notification_service
        self.recovery_jobs: Dict[str, RecoveryJob] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Default recovery strategies
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """Set up default recovery strategies."""
        self.recovery_strategies = {
            'database': self._recover_database,
            'models': self._recover_models,
            'configuration': self._recover_configuration,
            'federated_data': self._recover_federated_data
        }

    def register_health_check(self, system_name: str, check_func: Callable):
        """Register a health check function for a system."""
        self.health_checks[system_name] = check_func

    def register_recovery_strategy(self, system_name: str, strategy_func: Callable):
        """Register a custom recovery strategy."""
        self.recovery_strategies[system_name] = strategy_func

    async def start(self):
        """Start the recovery orchestrator."""
        self.running = True
        self._monitor_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Recovery orchestrator started")

    async def stop(self):
        """Stop the recovery orchestrator."""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Recovery orchestrator stopped")

    async def _health_monitor_loop(self):
        """Continuous health monitoring loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)

    async def _perform_health_checks(self):
        """Perform registered health checks."""
        for system_name, check_func in self.health_checks.items():
            try:
                healthy = await check_func()
                if not healthy:
                    logger.warning(f"Health check failed for {system_name}")
                    await self._trigger_automatic_recovery(system_name)
            except Exception as e:
                logger.error(f"Health check error for {system_name}: {e}")
                await self._trigger_automatic_recovery(system_name)

    async def _trigger_automatic_recovery(self, system_name: str):
        """Trigger automatic recovery for a failed system."""
        if system_name in self.recovery_strategies:
            job_id = f"auto_{system_name}_{int(datetime.now().timestamp())}"
            job = RecoveryJob(
                id=job_id,
                recovery_type=RecoveryType.AUTOMATIC,
                target_system=system_name,
                backup_source=f"{system_name}_latest",
                restore_paths=self._get_restore_paths(system_name)
            )
            await self.initiate_recovery(job)

    def _get_restore_paths(self, system_name: str) -> List[Path]:
        """Get restore paths for a system. Configurable."""
        # This would be configurable
        default_paths = {
            'database': [Path('./data/db')],
            'models': [Path('./models')],
            'configuration': [Path('./config')],
            'federated_data': [Path('./federated/data')]
        }
        return default_paths.get(system_name, [])

    async def initiate_recovery(self, job: RecoveryJob) -> str:
        """Initiate a recovery operation."""
        self.recovery_jobs[job.id] = job
        job.status = RecoveryStatus.IN_PROGRESS
        job.started_at = datetime.now()

        logger.info(f"Initiating recovery: {job.id} for {job.target_system}")

        # Notify if available
        if self.notifications:
            await self.notifications.send_alert(
                f"Recovery initiated: {job.target_system}",
                f"Recovery job {job.id} started"
            )

        # Start recovery in background
        asyncio.create_task(self._execute_recovery(job))

        return job.id

    async def _execute_recovery(self, job: RecoveryJob):
        """Execute the recovery operation."""
        try:
            # Create backup of current state for rollback
            job.rollback_info = await self._create_rollback_backup(job)

            # Execute recovery strategy
            strategy = self.recovery_strategies.get(job.target_system)
            if strategy:
                success = await strategy(job)
            else:
                success = await self._default_recovery(job)

            if success:
                job.status = RecoveryStatus.COMPLETED
                logger.info(f"Recovery completed: {job.id}")
                if self.notifications:
                    await self.notifications.send_alert(
                        f"Recovery completed: {job.target_system}",
                        f"Recovery job {job.id} successful"
                    )
            else:
                job.status = RecoveryStatus.FAILED
                logger.error(f"Recovery failed: {job.id}")
                # Attempt rollback
                await self._rollback_recovery(job)

        except Exception as e:
            job.status = RecoveryStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Recovery error: {e}")
            await self._rollback_recovery(job)

        finally:
            job.completed_at = datetime.now()

    async def _create_rollback_backup(self, job: RecoveryJob) -> Dict[str, Any]:
        """Create a rollback backup before recovery."""
        rollback_id = f"rollback_{job.id}_{int(datetime.now().timestamp())}"
        rollback_info = {
            'backup_id': rollback_id,
            'original_paths': [str(p) for p in job.restore_paths],
            'timestamp': datetime.now().isoformat()
        }

        # Create temporary backup of current state
        # This is simplified; in practice, would use the backup system
        for path in job.restore_paths:
            if path.exists():
                # Copy to temp location
                temp_path = Path(f"./temp/rollback_{path.name}_{rollback_id}")
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_file():
                    import shutil
                    shutil.copy2(path, temp_path)
                else:
                    shutil.copytree(path, temp_path, dirs_exist_ok=True)

        return rollback_info

    async def _rollback_recovery(self, job: RecoveryJob):
        """Rollback a failed recovery."""
        try:
            if job.rollback_info:
                logger.info(f"Rolling back recovery: {job.id}")
                # Restore from rollback backup
                # Simplified implementation
                for path_str in job.rollback_info['original_paths']:
                    path = Path(path_str)
                    temp_path = Path(f"./temp/rollback_{path.name}_{job.rollback_info['backup_id']}")
                    if temp_path.exists():
                        import shutil
                        if temp_path.is_file():
                            shutil.copy2(temp_path, path)
                        else:
                            shutil.copytree(temp_path, temp_path, dirs_exist_ok=True)
                        temp_path.unlink(missing_ok=True)

                job.status = RecoveryStatus.ROLLED_BACK
                logger.info(f"Recovery rolled back: {job.id}")

                if self.notifications:
                    await self.notifications.send_alert(
                        f"Recovery rolled back: {job.target_system}",
                        f"Recovery job {job.id} was rolled back due to failure"
                    )
        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    async def _default_recovery(self, job: RecoveryJob) -> bool:
        """Default recovery strategy - restore from latest backup."""
        try:
            # Find latest backup for the system
            backups = await self.backup_system.storage_backends['local'].list_backups(job.backup_source)
            if not backups:
                return False

            latest_backup = max(backups, key=lambda x: x.split('_')[-1])

            # Restore each path
            for restore_path in job.restore_paths:
                success = await self.backup_system.storage_backends['local'].retrieve(
                    latest_backup, restore_path
                )
                if not success:
                    return False

            return True
        except Exception as e:
            logger.error(f"Default recovery error: {e}")
            return False

    async def _recover_database(self, job: RecoveryJob) -> bool:
        """Database-specific recovery."""
        # Implementation would depend on database type
        # For now, use default recovery
        return await self._default_recovery(job)

    async def _recover_models(self, job: RecoveryJob) -> bool:
        """Model-specific recovery."""
        # Could include model validation after restore
        success = await self._default_recovery(job)
        if success:
            # Validate models
            pass
        return success

    async def _recover_configuration(self, job: RecoveryJob) -> bool:
        """Configuration-specific recovery."""
        return await self._default_recovery(job)

    async def _recover_federated_data(self, job: RecoveryJob) -> bool:
        """Federated data recovery."""
        # Might need coordination with federated coordinator
        return await self._default_recovery(job)

    def get_recovery_status(self, job_id: str) -> Optional[RecoveryJob]:
        """Get status of a recovery job."""
        return self.recovery_jobs.get(job_id)

    def list_recovery_jobs(self, status_filter: Optional[RecoveryStatus] = None) -> List[RecoveryJob]:
        """List recovery jobs, optionally filtered by status."""
        jobs = list(self.recovery_jobs.values())
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    async def cancel_recovery(self, job_id: str) -> bool:
        """Cancel a pending recovery job."""
        job = self.recovery_jobs.get(job_id)
        if job and job.status == RecoveryStatus.PENDING:
            job.status = RecoveryStatus.FAILED
            job.error_message = "Cancelled by user"
            return True
        return False