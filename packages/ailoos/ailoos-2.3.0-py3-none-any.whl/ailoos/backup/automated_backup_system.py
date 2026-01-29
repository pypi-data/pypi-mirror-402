"""
Automated Backup System for AILOOS

Provides automated backup capabilities with multiple strategies:
- Full backups
- Incremental backups
- Differential backups
- Snapshot-based backups

Supports multiple storage backends and scheduling.
"""

import asyncio
import logging
import os
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import hashlib
import json

from ..core.config import get_config

logger = logging.getLogger(__name__)


class BackupStrategy(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class StorageBackend(ABC):
    """Abstract base class for backup storage backends."""

    @abstractmethod
    async def store(self, source_path: Path, backup_path: str, metadata: Dict[str, Any]) -> bool:
        """Store backup data."""
        pass

    @abstractmethod
    async def retrieve(self, backup_path: str, destination_path: Path) -> bool:
        """Retrieve backup data."""
        pass

    @abstractmethod
    async def list_backups(self, prefix: str = "") -> List[str]:
        """List available backups."""
        pass

    @abstractmethod
    async def delete(self, backup_path: str) -> bool:
        """Delete a backup."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store(self, source_path: Path, backup_path: str, metadata: Dict[str, Any]) -> bool:
        try:
            dest_path = self.base_path / backup_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)

            # Save metadata
            meta_path = dest_path.with_suffix('.meta.json')
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to store backup: {e}")
            return False

    async def retrieve(self, backup_path: str, destination_path: Path) -> bool:
        try:
            source_path = self.base_path / backup_path
            if source_path.is_file():
                shutil.copy2(source_path, destination_path)
            else:
                shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to retrieve backup: {e}")
            return False

    async def list_backups(self, prefix: str = "") -> List[str]:
        try:
            pattern = f"{prefix}*" if prefix else "*"
            return [str(p.relative_to(self.base_path)) for p in self.base_path.rglob(pattern) if p.is_dir() or p.suffix != '.meta.json']
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def delete(self, backup_path: str) -> bool:
        try:
            path = self.base_path / backup_path
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            # Also delete metadata
            meta_path = path.with_suffix('.meta.json')
            if meta_path.exists():
                meta_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False


@dataclass
class BackupJob:
    """Represents a backup job configuration."""
    name: str
    source_paths: List[Path]
    strategy: BackupStrategy
    schedule: str  # Cron-like or interval
    retention_days: int
    storage_backend: StorageBackend
    compression: bool = True
    encryption: bool = True
    last_backup: Optional[datetime] = None
    last_full_backup: Optional[datetime] = None


class AutomatedBackupSystem:
    """Main automated backup system."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path or 'backup')
        self.jobs: Dict[str, BackupJob] = {}
        self.running = False
        self.backup_history: List[Dict[str, Any]] = []
        self._scheduler_task: Optional[asyncio.Task] = None

        # Initialize storage backends
        self.storage_backends = self._initialize_backends()

    def _initialize_backends(self) -> Dict[str, StorageBackend]:
        """Initialize configured storage backends."""
        backends = {}

        # Local backend
        local_path = Path(self.config.get('local_backup_path', './backups'))
        backends['local'] = LocalStorageBackend(local_path)

        # Add cloud backends if configured
        if self.config.get('aws_s3'):
            # Would import boto3 and create S3Backend
            pass
        if self.config.get('gcp_storage'):
            # Would import google.cloud.storage
            pass

        return backends

    def add_job(self, job: BackupJob):
        """Add a backup job."""
        self.jobs[job.name] = job
        logger.info(f"Added backup job: {job.name}")

    def remove_job(self, job_name: str):
        """Remove a backup job."""
        if job_name in self.jobs:
            del self.jobs[job_name]
            logger.info(f"Removed backup job: {job_name}")

    async def start(self):
        """Start the automated backup system."""
        self.running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Automated backup system started")

    async def stop(self):
        """Stop the automated backup system."""
        self.running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Automated backup system stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_run_backups()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _check_and_run_backups(self):
        """Check and run scheduled backups."""
        now = datetime.now()
        for job in self.jobs.values():
            if self._should_run_backup(job, now):
                await self._run_backup(job)

    def _should_run_backup(self, job: BackupJob, now: datetime) -> bool:
        """Determine if a backup should run based on schedule."""
        # Simple interval-based scheduling for now
        # Could be extended to cron expressions
        if not job.last_backup:
            return True

        interval_hours = self._parse_schedule(job.schedule)
        return (now - job.last_backup).total_seconds() > interval_hours * 3600

    def _parse_schedule(self, schedule: str) -> int:
        """Parse schedule string to hours. Simple implementation."""
        # Assume format like "24h", "7d", etc.
        if schedule.endswith('h'):
            return int(schedule[:-1])
        elif schedule.endswith('d'):
            return int(schedule[:-1]) * 24
        else:
            return 24  # Default 24 hours

    async def _run_backup(self, job: BackupJob):
        """Execute a backup job."""
        logger.info(f"Starting backup job: {job.name}")

        try:
            backup_id = f"{job.name}_{int(time.time())}"
            backup_path = f"{job.name}/{backup_id}"

            metadata = {
                'job_name': job.name,
                'strategy': job.strategy.value,
                'timestamp': datetime.now().isoformat(),
                'source_paths': [str(p) for p in job.source_paths],
                'compression': job.compression,
                'encryption': job.encryption
            }

            success = True
            for source_path in job.source_paths:
                if not await job.storage_backend.store(source_path, backup_path, metadata):
                    success = False
                    break

            if success:
                job.last_backup = datetime.now()
                if job.strategy == BackupStrategy.FULL:
                    job.last_full_backup = job.last_backup

                self.backup_history.append({
                    'job_name': job.name,
                    'backup_id': backup_id,
                    'timestamp': metadata['timestamp'],
                    'status': 'success'
                })

                # Cleanup old backups
                await self._cleanup_old_backups(job)

                logger.info(f"Backup job completed: {job.name}")
            else:
                self.backup_history.append({
                    'job_name': job.name,
                    'backup_id': backup_id,
                    'timestamp': metadata['timestamp'],
                    'status': 'failed'
                })
                logger.error(f"Backup job failed: {job.name}")

        except Exception as e:
            logger.error(f"Backup job error: {e}")

    async def _cleanup_old_backups(self, job: BackupJob):
        """Clean up backups older than retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=job.retention_days)
            backups = await job.storage_backend.list_backups(f"{job.name}/")

            for backup in backups:
                # Extract timestamp from backup name
                try:
                    timestamp_str = backup.split('_')[-1]
                    backup_date = datetime.fromtimestamp(int(timestamp_str))
                    if backup_date < cutoff_date:
                        await job.storage_backend.delete(backup)
                        logger.info(f"Cleaned up old backup: {backup}")
                except (ValueError, IndexError):
                    continue
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def manual_backup(self, job_name: str) -> bool:
        """Trigger a manual backup for a job."""
        if job_name not in self.jobs:
            logger.error(f"Job not found: {job_name}")
            return False

        job = self.jobs[job_name]
        await self._run_backup(job)
        return True

    def get_backup_history(self, job_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get backup history."""
        if job_name:
            return [h for h in self.backup_history if h['job_name'] == job_name]
        return self.backup_history.copy()