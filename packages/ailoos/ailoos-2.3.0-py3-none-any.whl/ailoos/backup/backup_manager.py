"""
Backup Manager for AILOOS

Unified manager that coordinates all backup and recovery operations including:
- Centralized configuration management
- Orchestration of backup operations
- Recovery workflow management
- Monitoring and alerting
- Compliance and audit logging
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import json
import uuid

from .automated_backup_system import AutomatedBackupSystem, BackupJob, BackupStrategy
from .recovery_orchestrator import RecoveryOrchestrator, RecoveryJob, RecoveryType
from .disaster_recovery import DisasterRecovery, Region, DisasterRecoveryPlan
from .point_in_time_recovery import PointInTimeRecovery, PITRecoveryRequest
from ..monitoring import UnifiedMonitoringSystem as MonitoringSystem
from ..notifications import NotificationService
try:
    from ..auditing import AuditLogger
except ImportError:
    AuditLogger = None

logger = logging.getLogger(__name__)


@dataclass
class BackupPolicy:
    """Backup policy configuration."""
    name: str
    systems: List[str]
    strategy: BackupStrategy
    schedule: str
    retention_days: int
    priority: int = 1
    enabled: bool = True


@dataclass
class SystemConfiguration:
    """Configuration for a system to be backed up."""
    name: str
    paths: List[Path]
    backup_policy: str
    critical: bool = False
    point_in_time_enabled: bool = False


class BackupManager:
    """Centralized backup and recovery management."""

    def __init__(self, config_path: Optional[str] = None,
                 monitoring: Optional[MonitoringSystem] = None,
                 notifications: Optional[NotificationService] = None,
                 audit_logger: Optional[AuditLogger] = None):
        self.config = self._load_config(config_path)
        self.monitoring = monitoring
        self.notifications = notifications
        self.audit_logger = audit_logger

        # Initialize components
        self.backup_system = AutomatedBackupSystem(config_path)
        self.recovery_orchestrator = RecoveryOrchestrator(
            self.backup_system, monitoring, notifications
        )
        self.disaster_recovery = DisasterRecovery(
            self.backup_system, self.recovery_orchestrator, None, monitoring, notifications
        )
        self.pit_recovery = PointInTimeRecovery(self.backup_system)

        # Configuration
        self.policies: Dict[str, BackupPolicy] = {}
        self.systems: Dict[str, SystemConfiguration] = {}
        self.regions: Dict[str, Region] = {}
        self.dr_plans: Dict[str, DisasterRecoveryPlan] = {}

        # State
        self.running = False
        self._maintenance_task: Optional[asyncio.Task] = None

        # Load configuration
        self._load_backup_configuration()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load backup configuration."""
        default_config = {
            'backup_base_path': './backups',
            'max_concurrent_backups': 3,
            'maintenance_interval_hours': 24,
            'audit_enabled': True
        }

        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Failed to load config {config_path}: {e}")

        return default_config

    def _load_backup_configuration(self):
        """Load backup policies and system configurations."""
        # Load policies
        policies_config = self.config.get('policies', [])
        for policy_data in policies_config:
            policy = BackupPolicy(**policy_data)
            self.policies[policy.name] = policy

        # Load systems
        systems_config = self.config.get('systems', [])
        for system_data in systems_config:
            system = SystemConfiguration(**system_data)
            self.systems[system.name] = system
            # Register with PIT recovery if enabled
            if system.point_in_time_enabled:
                self.pit_recovery.register_system(system.name)

        # Load regions
        regions_config = self.config.get('regions', [])
        for region_data in regions_config:
            region = Region(**region_data)
            self.regions[region.name] = region
            self.disaster_recovery.add_region(region)

        # Load DR plans
        dr_config = self.config.get('disaster_recovery_plans', [])
        for plan_data in dr_config:
            plan = DisasterRecoveryPlan(**plan_data)
            self.dr_plans[plan.name] = plan
            self.disaster_recovery.create_plan(plan)

    async def start(self):
        """Start the backup manager and all components."""
        logger.info("Starting Backup Manager")

        # Start components
        await self.backup_system.start()
        await self.recovery_orchestrator.start()
        await self.disaster_recovery.start()

        # Create backup jobs from policies
        self._create_backup_jobs()

        # Register health checks
        self._register_health_checks()

        self.running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())

        logger.info("Backup Manager started successfully")

    async def stop(self):
        """Stop the backup manager and all components."""
        logger.info("Stopping Backup Manager")

        self.running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        await self.disaster_recovery.stop()
        await self.recovery_orchestrator.stop()
        await self.backup_system.stop()

        logger.info("Backup Manager stopped")

    def _create_backup_jobs(self):
        """Create backup jobs from policies and systems."""
        for system_name, system in self.systems.items():
            if system.backup_policy not in self.policies:
                logger.warning(f"Policy {system.backup_policy} not found for system {system_name}")
                continue

            policy = self.policies[system.backup_policy]
            if not policy.enabled:
                continue

            job = BackupJob(
                name=f"{system_name}_backup",
                source_paths=system.paths,
                strategy=policy.strategy,
                schedule=policy.schedule,
                retention_days=policy.retention_days,
                storage_backend=self.backup_system.storage_backends['local']
            )

            self.backup_system.add_job(job)
            logger.info(f"Created backup job for system: {system_name}")

    def _register_health_checks(self):
        """Register health checks for critical systems."""
        for system_name, system in self.systems.items():
            if system.critical:
                self.recovery_orchestrator.register_health_check(
                    system_name, self._create_health_check(system_name)
                )

    def _create_health_check(self, system_name: str) -> Callable:
        """Create a health check function for a system."""
        async def health_check():
            # Implement system-specific health checks
            system_config = self.systems[system_name]

            # Check if critical paths exist and are accessible
            for path in system_config.paths:
                if not path.exists():
                    return False

            # Additional checks based on system type
            if 'database' in system_name.lower():
                # Database connectivity check
                pass
            elif 'federated' in system_name.lower():
                # Federated system check
                pass

            return True

        return health_check

    async def _maintenance_loop(self):
        """Perform regular maintenance tasks."""
        while self.running:
            try:
                await self._perform_maintenance()
                interval = self.config.get('maintenance_interval_hours', 24)
                await asyncio.sleep(interval * 3600)
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                await asyncio.sleep(3600)

    async def _perform_maintenance(self):
        """Perform maintenance tasks."""
        logger.info("Performing backup maintenance")

        # Verify backup integrity
        await self._verify_backup_integrity()

        # Clean up expired backups
        await self._cleanup_expired_backups()

        # Update recovery points
        await self._update_recovery_points()

        # Generate reports
        await self._generate_backup_report()

    async def _verify_backup_integrity(self):
        """Verify integrity of recent backups."""
        # Check a sample of recent backups
        history = self.backup_system.get_backup_history()
        recent_backups = [h for h in history if h['status'] == 'success'][:10]

        for backup in recent_backups:
            # Verify backup exists and is readable
            try:
                # Implementation would check backup integrity
                pass
            except Exception as e:
                logger.error(f"Backup integrity check failed for {backup['backup_id']}: {e}")

    async def _cleanup_expired_backups(self):
        """Clean up backups that have exceeded retention periods."""
        # This is handled by the backup system, but we can add additional cleanup
        pass

    async def _update_recovery_points(self):
        """Update point-in-time recovery points."""
        for system_name in self.systems:
            if self.systems[system_name].point_in_time_enabled:
                # Add current state as recovery point
                # This would be done after successful backups
                pass

    async def _generate_backup_report(self):
        """Generate a backup status report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'systems': {},
            'overall_status': 'healthy'
        }

        for system_name, system in self.systems.items():
            system_status = {
                'last_backup': None,
                'backup_count': 0,
                'status': 'unknown'
            }

            # Get backup history for this system
            history = self.backup_system.get_backup_history()
            system_history = [h for h in history if h['job_name'].startswith(system_name)]

            if system_history:
                latest = max(system_history, key=lambda h: h['timestamp'])
                system_status['last_backup'] = latest['timestamp']
                system_status['backup_count'] = len(system_history)
                system_status['status'] = 'healthy' if latest['status'] == 'success' else 'failed'

                # Check if backup is recent enough
                last_backup_time = datetime.fromisoformat(latest['timestamp'])
                policy = self.policies.get(system.backup_policy)
                if policy:
                    expected_interval = timedelta(hours=self._parse_schedule_to_hours(policy.schedule))
                    if datetime.now() - last_backup_time > expected_interval * 2:
                        system_status['status'] = 'overdue'

            report['systems'][system_name] = system_status
            if system_status['status'] != 'healthy':
                report['overall_status'] = 'warning'

        # Save report
        report_path = Path(self.config['backup_base_path']) / 'reports' / f"backup_report_{int(datetime.now().timestamp())}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info("Backup report generated")

    def _parse_schedule_to_hours(self, schedule: str) -> int:
        """Parse schedule string to hours."""
        if schedule.endswith('h'):
            return int(schedule[:-1])
        elif schedule.endswith('d'):
            return int(schedule[:-1]) * 24
        else:
            return 24

    # Public API methods

    async def create_backup_policy(self, policy: BackupPolicy):
        """Create a new backup policy."""
        self.policies[policy.name] = policy
        self._save_configuration()
        logger.info(f"Created backup policy: {policy.name}")

    async def update_backup_policy(self, policy_name: str, updates: Dict[str, Any]):
        """Update an existing backup policy."""
        if policy_name not in self.policies:
            raise ValueError(f"Policy {policy_name} not found")

        policy = self.policies[policy_name]
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        self._save_configuration()
        logger.info(f"Updated backup policy: {policy_name}")

    async def add_system(self, system: SystemConfiguration):
        """Add a system to be backed up."""
        self.systems[system.name] = system
        if system.point_in_time_enabled:
            self.pit_recovery.register_system(system.name)

        # Create backup job
        self._create_backup_jobs()
        self._save_configuration()
        logger.info(f"Added system: {system.name}")

    async def manual_backup(self, system_name: str) -> bool:
        """Trigger a manual backup for a system."""
        job_name = f"{system_name}_backup"
        return await self.backup_system.manual_backup(job_name)

    async def initiate_recovery(self, system_name: str, recovery_type: RecoveryType = RecoveryType.MANUAL) -> str:
        """Initiate recovery for a system."""
        if system_name not in self.systems:
            raise ValueError(f"System {system_name} not found")

        system = self.systems[system_name]
        job = RecoveryJob(
            id=str(uuid.uuid4()),
            recovery_type=recovery_type,
            target_system=system_name,
            backup_source=f"{system_name}_latest",
            restore_paths=system.paths
        )

        return await self.recovery_orchestrator.initiate_recovery(job)

    async def initiate_pit_recovery(self, system_name: str, target_timestamp: datetime) -> str:
        """Initiate point-in-time recovery."""
        if system_name not in self.systems:
            raise ValueError(f"System {system_name} not found")

        system = self.systems[system_name]
        request = PITRecoveryRequest(
            id=str(uuid.uuid4()),
            target_timestamp=target_timestamp,
            source_system=system_name,
            restore_paths=system.paths
        )

        return await self.pit_recovery.initiate_pit_recovery(request)

    async def manual_failover(self, from_region: str, to_region: str) -> bool:
        """Trigger manual failover between regions."""
        return await self.disaster_recovery.manual_failover(from_region, to_region)

    def get_system_status(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of systems."""
        if system_name:
            return self._get_single_system_status(system_name)
        else:
            return {name: self._get_single_system_status(name) for name in self.systems}

    def _get_single_system_status(self, system_name: str) -> Dict[str, Any]:
        """Get status for a single system."""
        system = self.systems[system_name]
        history = self.backup_system.get_backup_history(system_name)

        status = {
            'name': system_name,
            'policy': system.backup_policy,
            'critical': system.critical,
            'point_in_time_enabled': system.point_in_time_enabled,
            'last_backup': None,
            'backup_count': len(history),
            'recovery_points': 0
        }

        if history:
            latest = max(history, key=lambda h: h['timestamp'])
            status['last_backup'] = latest['timestamp']

        if system.point_in_time_enabled:
            points = self.pit_recovery.get_available_recovery_points(system_name)
            status['recovery_points'] = len(points)

        return status

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall backup system status."""
        systems_status = self.get_system_status()

        total_systems = len(systems_status)
        healthy_systems = sum(1 for s in systems_status.values() if s.get('last_backup') is not None)
        critical_systems = sum(1 for s in systems_status.values() if s['critical'])

        return {
            'total_systems': total_systems,
            'healthy_systems': healthy_systems,
            'critical_systems': critical_systems,
            'overall_health': 'healthy' if healthy_systems == total_systems else 'warning',
            'regions': self.disaster_recovery.get_region_status(),
            'last_maintenance': getattr(self, '_last_maintenance', None)
        }

    def _save_configuration(self):
        """Save current configuration."""
        config_path = self.config.get('config_path', './backup_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'policies': [vars(p) for p in self.policies.values()],
                'systems': [vars(s) for s in self.systems.values()],
                'regions': [vars(r) for r in self.regions.values()],
                'disaster_recovery_plans': [vars(p) for p in self.dr_plans.values()]
            }, f, indent=2, default=str)