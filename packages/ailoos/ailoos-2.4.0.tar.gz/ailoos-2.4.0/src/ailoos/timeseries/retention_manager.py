"""
Retention Policy Manager for time series data lifecycle management
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class RetentionAction(Enum):
    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    DOWN_SAMPLE = "down_sample"


@dataclass
class RetentionRule:
    """Retention policy rule"""
    measurement: str
    max_age_days: int
    action: RetentionAction
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    priority: int = 1
    enabled: bool = True


@dataclass
class RetentionPolicy:
    """Complete retention policy"""
    name: str
    description: str
    rules: List[RetentionRule]
    schedule: str = "0 2 * * *"  # Daily at 2 AM by default
    enabled: bool = True


class RetentionPolicyManager:
    """
    Manager for time series data retention policies
    """

    def __init__(self, manager, policies: Optional[Dict[str, Any]] = None):
        """
        Initialize retention policy manager

        Args:
            manager: TimeSeriesManager instance
            policies: Initial policies configuration
        """
        self.manager = manager
        self.logger = logging.getLogger(__name__)

        self.policies: Dict[str, RetentionPolicy] = {}
        self.running = False
        self.cleanup_task: Optional[asyncio.Task] = None

        if policies:
            self.load_policies(policies)

        # Default policies
        self._create_default_policies()

    def _create_default_policies(self):
        """Create default retention policies"""
        # System metrics policy
        system_policy = RetentionPolicy(
            name="system_metrics",
            description="Retention policy for system metrics",
            rules=[
                RetentionRule(
                    measurement="system_cpu",
                    max_age_days=30,
                    action=RetentionAction.DELETE
                ),
                RetentionRule(
                    measurement="system_memory",
                    max_age_days=30,
                    action=RetentionAction.DELETE
                ),
                RetentionRule(
                    measurement="system_disk",
                    max_age_days=90,
                    action=RetentionAction.DELETE
                ),
                RetentionRule(
                    measurement="system_network",
                    max_age_days=30,
                    action=RetentionAction.DELETE
                )
            ]
        )

        # Application metrics policy
        app_policy = RetentionPolicy(
            name="application_metrics",
            description="Retention policy for application metrics",
            rules=[
                RetentionRule(
                    measurement="app_requests",
                    max_age_days=7,
                    action=RetentionAction.DELETE
                ),
                RetentionRule(
                    measurement="app_errors",
                    max_age_days=30,
                    action=RetentionAction.DELETE
                ),
                RetentionRule(
                    measurement="app_performance",
                    max_age_days=90,
                    action=RetentionAction.COMPRESS
                )
            ]
        )

        self.add_policy(system_policy)
        self.add_policy(app_policy)

    def add_policy(self, policy: RetentionPolicy):
        """
        Add a retention policy

        Args:
            policy: Retention policy to add
        """
        self.policies[policy.name] = policy
        self.logger.info(f"Added retention policy: {policy.name}")

    def remove_policy(self, policy_name: str):
        """
        Remove a retention policy

        Args:
            policy_name: Name of policy to remove
        """
        if policy_name in self.policies:
            del self.policies[policy_name]
            self.logger.info(f"Removed retention policy: {policy_name}")

    def update_policy(self, policy_name: str, updates: Dict[str, Any]):
        """
        Update a retention policy

        Args:
            policy_name: Name of policy to update
            updates: Updates to apply
        """
        if policy_name not in self.policies:
            raise ValueError(f"Policy {policy_name} not found")

        policy = self.policies[policy_name]

        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        self.logger.info(f"Updated retention policy: {policy_name}")

    def load_policies(self, policies_config: Dict[str, Any]):
        """
        Load policies from configuration

        Args:
            policies_config: Policies configuration dictionary
        """
        for policy_name, policy_data in policies_config.items():
            rules = []
            for rule_data in policy_data.get('rules', []):
                rule = RetentionRule(
                    measurement=rule_data['measurement'],
                    max_age_days=rule_data['max_age_days'],
                    action=RetentionAction(rule_data['action']),
                    priority=rule_data.get('priority', 1),
                    enabled=rule_data.get('enabled', True)
                )
                rules.append(rule)

            policy = RetentionPolicy(
                name=policy_name,
                description=policy_data.get('description', ''),
                rules=rules,
                schedule=policy_data.get('schedule', '0 2 * * *'),
                enabled=policy_data.get('enabled', True)
            )

            self.add_policy(policy)

    async def apply_policy(self, measurement: str, backend_type) -> bool:
        """
        Apply retention policy for a specific measurement

        Args:
            measurement: Measurement name
            backend_type: Backend type

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find applicable rules
            applicable_rules = self._get_applicable_rules(measurement)

            if not applicable_rules:
                self.logger.debug(f"No retention rules found for measurement: {measurement}")
                return True

            success = True

            for rule in applicable_rules:
                if not rule.enabled:
                    continue

                try:
                    await self._apply_rule(rule, backend_type)
                except Exception as e:
                    self.logger.error(f"Error applying rule {rule.measurement}: {e}")
                    success = False

            return success

        except Exception as e:
            self.logger.error(f"Error applying retention policy for {measurement}: {e}")
            return False

    def _get_applicable_rules(self, measurement: str) -> List[RetentionRule]:
        """
        Get rules applicable to a measurement

        Args:
            measurement: Measurement name

        Returns:
            List of applicable rules
        """
        applicable = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            for rule in policy.rules:
                if rule.measurement == measurement or rule.measurement == "*":
                    applicable.append(rule)

        # Sort by priority (higher priority first)
        applicable.sort(key=lambda x: x.priority, reverse=True)

        return applicable

    async def _apply_rule(self, rule: RetentionRule, backend_type):
        """
        Apply a single retention rule

        Args:
            rule: Retention rule to apply
            backend_type: Backend type
        """
        cutoff_time = datetime.utcnow() - timedelta(days=rule.max_age_days)

        if rule.action == RetentionAction.DELETE:
            await self._delete_old_data(rule.measurement, cutoff_time, backend_type)
        elif rule.action == RetentionAction.ARCHIVE:
            await self._archive_old_data(rule.measurement, cutoff_time, backend_type)
        elif rule.action == RetentionAction.COMPRESS:
            await self._compress_old_data(rule.measurement, cutoff_time, backend_type)
        elif rule.action == RetentionAction.DOWN_SAMPLE:
            await self._down_sample_old_data(rule.measurement, cutoff_time, backend_type)

    async def _delete_old_data(self, measurement: str, cutoff_time: datetime, backend_type):
        """
        Delete data older than cutoff time

        Args:
            measurement: Measurement name
            cutoff_time: Cutoff timestamp
            backend_type: Backend type
        """
        self.logger.info(f"Deleting data older than {cutoff_time} for measurement: {measurement}")

        # Delete from all configured backends
        for backend in self.manager.backends.values():
            try:
                await backend.delete_data(measurement, datetime.min, cutoff_time)
            except Exception as e:
                self.logger.error(f"Error deleting from {backend.__class__.__name__}: {e}")

    async def _archive_old_data(self, measurement: str, cutoff_time: datetime, backend_type):
        """
        Archive data older than cutoff time (placeholder implementation)

        Args:
            measurement: Measurement name
            cutoff_time: Cutoff timestamp
            backend_type: Backend type
        """
        self.logger.info(f"Archiving data older than {cutoff_time} for measurement: {measurement}")

        # TODO: Implement actual archiving logic
        # This could involve:
        # 1. Exporting data to files
        # 2. Moving to separate storage
        # 3. Compressing and storing

        # For now, just log the action
        self.logger.warning("Archive action not fully implemented")

    async def _compress_old_data(self, measurement: str, cutoff_time: datetime, backend_type):
        """
        Compress data older than cutoff time (placeholder implementation)

        Args:
            measurement: Measurement name
            cutoff_time: Cutoff timestamp
            backend_type: Backend type
        """
        self.logger.info(f"Compressing data older than {cutoff_time} for measurement: {measurement}")

        # TODO: Implement actual compression logic
        # This could involve:
        # 1. Re-encoding data with compression
        # 2. Using database compression features

        # For now, just log the action
        self.logger.warning("Compress action not fully implemented")

    async def _down_sample_old_data(self, measurement: str, cutoff_time: datetime, backend_type):
        """
        Down-sample data older than cutoff time

        Args:
            measurement: Measurement name
            cutoff_time: Cutoff timestamp
            backend_type: Backend type
        """
        self.logger.info(f"Down-sampling data older than {cutoff_time} for measurement: {measurement}")

        # TODO: Implement down-sampling logic
        # This could involve:
        # 1. Aggregating data points (hourly -> daily)
        # 2. Reducing precision
        # 3. Storing aggregated data separately

        # For now, just log the action
        self.logger.warning("Down-sample action not fully implemented")

    async def run_cleanup_cycle(self):
        """
        Run a complete cleanup cycle for all policies and measurements
        """
        self.logger.info("Starting retention policy cleanup cycle")

        cleanup_stats = {
            "policies_processed": 0,
            "measurements_processed": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }

        try:
            for policy in self.policies.values():
                if not policy.enabled:
                    continue

                cleanup_stats["policies_processed"] += 1

                for rule in policy.rules:
                    if not rule.enabled:
                        continue

                    cleanup_stats["measurements_processed"] += 1

                    try:
                        # Apply rule to all backends
                        for backend_type in self.manager.backends.keys():
                            await self._apply_rule(rule, backend_type)
                    except Exception as e:
                        self.logger.error(f"Error applying rule for {rule.measurement}: {e}")
                        cleanup_stats["errors"] += 1

        except Exception as e:
            self.logger.error(f"Error in cleanup cycle: {e}")
            cleanup_stats["errors"] += 1

        cleanup_stats["end_time"] = datetime.utcnow()
        cleanup_stats["duration_seconds"] = (cleanup_stats["end_time"] - cleanup_stats["start_time"]).total_seconds()

        self.logger.info(f"Retention cleanup cycle completed: {cleanup_stats}")

        return cleanup_stats

    async def start_scheduler(self):
        """
        Start the retention policy scheduler
        """
        if self.running:
            self.logger.warning("Retention scheduler is already running")
            return

        self.running = True
        self.cleanup_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Retention policy scheduler started")

    async def stop_scheduler(self):
        """
        Stop the retention policy scheduler
        """
        if not self.running:
            return

        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Retention policy scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Run cleanup cycle
                await self.run_cleanup_cycle()

                # Wait for next cycle (daily)
                await asyncio.sleep(24 * 60 * 60)  # 24 hours

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    def get_policy_status(self) -> Dict[str, Any]:
        """
        Get status of all retention policies

        Returns:
            Policy status dictionary
        """
        return {
            "policies": {
                name: {
                    "description": policy.description,
                    "enabled": policy.enabled,
                    "rules_count": len(policy.rules),
                    "schedule": policy.schedule
                }
                for name, policy in self.policies.items()
            },
            "scheduler_running": self.running,
            "total_policies": len(self.policies)
        }

    def get_measurement_rules(self, measurement: str) -> List[Dict[str, Any]]:
        """
        Get retention rules for a specific measurement

        Args:
            measurement: Measurement name

        Returns:
            List of rule dictionaries
        """
        rules = self._get_applicable_rules(measurement)

        return [
            {
                "measurement": rule.measurement,
                "max_age_days": rule.max_age_days,
                "action": rule.action.value,
                "priority": rule.priority,
                "enabled": rule.enabled
            }
            for rule in rules
        ]