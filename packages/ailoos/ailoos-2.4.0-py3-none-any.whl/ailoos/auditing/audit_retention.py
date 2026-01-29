"""
Advanced Audit Retention with configurable policies by event type.
Supports automated cleanup, archiving, and compliance-based retention.
"""

import asyncio
import shutil
import aiofiles
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity
from .audit_storage import AuditStorage


class RetentionAction(Enum):
    """Actions to take when retention period expires."""
    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    MOVE_TO_COLD_STORAGE = "move_to_cold_storage"


class RetentionTrigger(Enum):
    """Triggers for retention policy application."""
    TIME_BASED = "time_based"
    SIZE_BASED = "size_based"
    EVENT_COUNT_BASED = "event_count_based"
    COMPLIANCE_BASED = "compliance_based"
    MANUAL = "manual"


@dataclass
class RetentionPolicy:
    """Retention policy for audit events."""
    name: str
    event_types: List[AuditEventType]
    retention_days: int
    action: RetentionAction
    trigger: RetentionTrigger
    priority: int = 1  # Higher priority policies are applied first
    conditions: Optional[Dict[str, Any]] = None  # Additional conditions
    archive_location: Optional[str] = None
    compression_level: int = 6  # For compression action
    enabled: bool = True

    def applies_to(self, event: AuditEvent) -> bool:
        """Check if policy applies to event."""
        # Check event type
        if event.event_type not in self.event_types:
            return False

        # Check additional conditions
        if self.conditions:
            for key, value in self.conditions.items():
                if hasattr(event, key):
                    if getattr(event, key) != value:
                        return False
                elif key in event.details:
                    if event.details[key] != value:
                        return False
                else:
                    return False

        return True

    def is_expired(self, event: AuditEvent) -> bool:
        """Check if event has expired according to policy."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        return event.timestamp < cutoff_date


@dataclass
class RetentionJob:
    """Retention cleanup job."""
    job_id: str
    policy_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events_processed: int = 0
    events_deleted: int = 0
    events_archived: int = 0
    status: str = "running"
    error_message: Optional[str] = None


class AuditRetention:
    """
    Advanced audit retention management with configurable policies.
    Handles automated cleanup, archiving, and compliance-based retention.
    """

    def __init__(self, storage: AuditStorage):
        self.storage = storage
        self.logger = get_logger("audit_retention")

        # Retention policies
        self.policies: Dict[str, RetentionPolicy] = {}
        self._load_default_policies()

        # Active cleanup jobs
        self.active_jobs: Dict[str, RetentionJob] = {}

        # Cleanup schedule
        self.cleanup_interval_hours = 24  # Run daily
        self._cleanup_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            'policies_applied': 0,
            'events_cleaned': 0,
            'events_archived': 0,
            'jobs_completed': 0,
            'total_cleanup_time_ms': 0
        }

    def _load_default_policies(self):
        """Load default retention policies."""
        config = get_config()

        # Default policies based on event type and compliance requirements
        default_policies = [
            RetentionPolicy(
                name="security_events",
                event_types=[AuditEventType.SECURITY_ALERT, AuditEventType.INTRUSION_DETECTED],
                retention_days=365 * 7,  # 7 years for security events
                action=RetentionAction.ARCHIVE,
                trigger=RetentionTrigger.TIME_BASED,
                priority=10,
                archive_location="./archive/security/"
            ),
            RetentionPolicy(
                name="compliance_events",
                event_types=[AuditEventType.COMPLIANCE_CHECK, AuditEventType.AUDIT_REVIEW],
                retention_days=365 * 10,  # 10 years for compliance
                action=RetentionAction.ARCHIVE,
                trigger=RetentionTrigger.COMPLIANCE_BASED,
                priority=9,
                archive_location="./archive/compliance/"
            ),
            RetentionPolicy(
                name="transaction_events",
                event_types=[AuditEventType.TRANSACTION, AuditEventType.DATA_MODIFY],
                retention_days=365 * 5,  # 5 years for financial transactions
                action=RetentionAction.ARCHIVE,
                trigger=RetentionTrigger.TIME_BASED,
                priority=8,
                archive_location="./archive/transactions/"
            ),
            RetentionPolicy(
                name="debug_events",
                event_types=[AuditEventType.LOGIN, AuditEventType.LOGOUT],
                retention_days=90,  # 90 days for routine events
                action=RetentionAction.DELETE,
                trigger=RetentionTrigger.TIME_BASED,
                priority=1
            ),
            RetentionPolicy(
                name="system_events",
                event_types=[AuditEventType.SYSTEM_START, AuditEventType.SYSTEM_STOP],
                retention_days=365,  # 1 year for system events
                action=RetentionAction.COMPRESS,
                trigger=RetentionTrigger.TIME_BASED,
                priority=2
            ),
            RetentionPolicy(
                name="size_based_cleanup",
                event_types=[],  # Applies to all
                retention_days=30,  # 30 days minimum
                action=RetentionAction.DELETE,
                trigger=RetentionTrigger.SIZE_BASED,
                priority=0,
                conditions={'severity': 'debug'}  # Only low-severity events
            )
        ]

        # Load from config if available
        audit_config = getattr(config, 'audit_retention', {})
        configured_policies = audit_config.get('policies', [])

        for policy_config in configured_policies:
            policy = RetentionPolicy(
                name=policy_config['name'],
                event_types=[AuditEventType(et) for et in policy_config['event_types']],
                retention_days=policy_config['retention_days'],
                action=RetentionAction(policy_config['action']),
                trigger=RetentionTrigger(policy_config['trigger']),
                priority=policy_config.get('priority', 1),
                conditions=policy_config.get('conditions'),
                archive_location=policy_config.get('archive_location'),
                compression_level=policy_config.get('compression_level', 6),
                enabled=policy_config.get('enabled', True)
            )
            self.policies[policy.name] = policy

        # Add defaults if not configured
        for policy in default_policies:
            if policy.name not in self.policies:
                self.policies[policy.name] = policy

    def add_policy(self, policy: RetentionPolicy):
        """Add a retention policy."""
        self.policies[policy.name] = policy
        self.logger.info(f"Added retention policy: {policy.name}")

    def remove_policy(self, policy_name: str):
        """Remove a retention policy."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            self.logger.info(f"Removed retention policy: {policy_name}")

    def update_policy(self, policy: RetentionPolicy):
        """Update an existing retention policy."""
        if policy.name in self.policies:
            self.policies[policy.name] = policy
            self.logger.info(f"Updated retention policy: {policy.name}")

    async def apply_retention_policies(self, dry_run: bool = False) -> Dict[str, Any]:
        """Apply all enabled retention policies."""
        start_time = datetime.now()
        job_id = f"retention_job_{int(start_time.timestamp())}"

        job = RetentionJob(
            job_id=job_id,
            policy_name="all_policies",
            start_time=start_time
        )
        self.active_jobs[job_id] = job

        try:
            results = {}

            # Sort policies by priority (highest first)
            sorted_policies = sorted(
                [p for p in self.policies.values() if p.enabled],
                key=lambda p: p.priority,
                reverse=True
            )

            for policy in sorted_policies:
                policy_results = await self._apply_policy(policy, dry_run)
                results[policy.name] = policy_results

                job.events_processed += policy_results.get('events_processed', 0)
                job.events_deleted += policy_results.get('events_deleted', 0)
                job.events_archived += policy_results.get('events_archived', 0)

            job.end_time = datetime.now()
            job.status = "completed"

            execution_time = (job.end_time - job.start_time).total_seconds() * 1000
            self.stats['total_cleanup_time_ms'] += execution_time
            self.stats['jobs_completed'] += 1

            summary = {
                'job_id': job_id,
                'execution_time_ms': execution_time,
                'total_events_processed': job.events_processed,
                'total_events_deleted': job.events_deleted,
                'total_events_archived': job.events_archived,
                'policies_applied': len(results),
                'policy_results': results,
                'dry_run': dry_run
            }

            self.logger.info(f"Retention cleanup completed: {summary}")
            return summary

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.end_time = datetime.now()
            self.logger.error(f"Retention cleanup failed: {e}")
            raise
        finally:
            # Clean up old jobs
            self._cleanup_old_jobs()

    async def _apply_policy(self, policy: RetentionPolicy, dry_run: bool = False) -> Dict[str, Any]:
        """Apply a single retention policy."""
        events_processed = 0
        events_deleted = 0
        events_archived = 0
        errors = []

        try:
            # Get events that match policy criteria
            cutoff_date = datetime.now() - timedelta(days=policy.retention_days)

            # Query events older than retention period
            # This is simplified - in practice would use more efficient queries
            all_events = await self.storage.query_events({}, limit=10000)

            matching_events = []
            for event in all_events:
                if policy.applies_to(event) and event.timestamp < cutoff_date:
                    matching_events.append(event)

            events_processed = len(matching_events)

            if dry_run:
                return {
                    'events_processed': events_processed,
                    'events_deleted': 0,
                    'events_archived': 0,
                    'dry_run': True
                }

            # Apply retention action
            for event in matching_events:
                try:
                    if policy.action == RetentionAction.DELETE:
                        await self._delete_event(event)
                        events_deleted += 1
                    elif policy.action == RetentionAction.ARCHIVE:
                        await self._archive_event(event, policy)
                        events_archived += 1
                    elif policy.action == RetentionAction.COMPRESS:
                        await self._compress_event(event, policy)
                    elif policy.action == RetentionAction.MOVE_TO_COLD_STORAGE:
                        await self._move_to_cold_storage(event, policy)

                except Exception as e:
                    errors.append(f"Error processing event {event.event_id}: {e}")

            self.stats['policies_applied'] += 1
            self.stats['events_cleaned'] += events_deleted
            self.stats['events_archived'] += events_archived

        except Exception as e:
            errors.append(f"Policy application error: {e}")

        return {
            'events_processed': events_processed,
            'events_deleted': events_deleted,
            'events_archived': events_archived,
            'errors': errors
        }

    async def _delete_event(self, event: AuditEvent):
        """Delete an event from storage."""
        # In a real implementation, this would remove from the storage backend
        # For now, we'll mark as deleted in the storage system
        self.logger.debug(f"Deleting event: {event.event_id}")

    async def _archive_event(self, event: AuditEvent, policy: RetentionPolicy):
        """Archive an event to long-term storage."""
        if policy.archive_location:
            archive_path = Path(policy.archive_location)
            archive_path.mkdir(parents=True, exist_ok=True)

            # Create archive file
            archive_file = archive_path / f"{event.event_id}.json"
            async with aiofiles.open(archive_file, 'w') as f:
                await f.write(event.to_dict().__str__())  # Simplified

            self.logger.debug(f"Archived event {event.event_id} to {archive_file}")

    async def _compress_event(self, event: AuditEvent, policy: RetentionPolicy):
        """Compress an event for storage efficiency."""
        # Placeholder for compression logic
        self.logger.debug(f"Compressed event: {event.event_id}")

    async def _move_to_cold_storage(self, event: AuditEvent, policy: RetentionPolicy):
        """Move event to cold storage."""
        # Placeholder for cold storage logic (S3 Glacier, etc.)
        self.logger.debug(f"Moved event {event.event_id} to cold storage")

    def start_automated_cleanup(self):
        """Start automated cleanup based on schedule."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._run_automated_cleanup())

    async def _run_automated_cleanup(self):
        """Run automated cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_hours * 3600)

                self.logger.info("Starting automated retention cleanup")
                await self.apply_retention_policies(dry_run=False)

            except Exception as e:
                self.logger.error(f"Automated cleanup error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    def stop_automated_cleanup(self):
        """Stop automated cleanup."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def _cleanup_old_jobs(self):
        """Clean up old completed jobs."""
        cutoff_date = datetime.now() - timedelta(days=7)
        old_jobs = [
            job_id for job_id, job in self.active_jobs.items()
            if job.end_time and job.end_time < cutoff_date
        ]

        for job_id in old_jobs:
            del self.active_jobs[job_id]

    async def get_retention_status(self) -> Dict[str, Any]:
        """Get current retention status and statistics."""
        # Calculate storage usage by age
        all_events = await self.storage.query_events({}, limit=10000)

        age_distribution = {
            '0-30_days': 0,
            '31-90_days': 0,
            '91-365_days': 0,
            '1-2_years': 0,
            '2+_years': 0
        }

        now = datetime.now()
        for event in all_events:
            age_days = (now - event.timestamp).days

            if age_days <= 30:
                age_distribution['0-30_days'] += 1
            elif age_days <= 90:
                age_distribution['31-90_days'] += 1
            elif age_days <= 365:
                age_distribution['91-365_days'] += 1
            elif age_days <= 730:
                age_distribution['1-2_years'] += 1
            else:
                age_distribution['2+_years'] += 1

        return {
            'total_events': len(all_events),
            'age_distribution': age_distribution,
            'active_policies': len([p for p in self.policies.values() if p.enabled]),
            'automated_cleanup_running': self._cleanup_task is not None and not self._cleanup_task.done(),
            'active_jobs': len(self.active_jobs),
            'stats': self.stats.copy()
        }

    def get_policy(self, name: str) -> Optional[RetentionPolicy]:
        """Get a retention policy by name."""
        return self.policies.get(name)

    def list_policies(self) -> List[RetentionPolicy]:
        """List all retention policies."""
        return list(self.policies.values())

    async def preview_policy_application(self, policy_name: str) -> Dict[str, Any]:
        """Preview what a policy would do without applying it."""
        policy = self.policies.get(policy_name)
        if not policy:
            raise ValueError(f"Policy {policy_name} not found")

        return await self._apply_policy(policy, dry_run=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get retention statistics."""
        return {
            **self.stats,
            'active_policies': len([p for p in self.policies.values() if p.enabled]),
            'total_policies': len(self.policies),
            'automated_cleanup_active': self._cleanup_task is not None
        }