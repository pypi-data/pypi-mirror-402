"""
Disaster Recovery System for AILOOS

Handles disaster recovery with cross-region failover including:
- Multi-region deployment management
- Automatic failover detection and execution
- Cross-region data synchronization
- Failback procedures
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json

from .automated_backup_system import AutomatedBackupSystem
from .recovery_orchestrator import RecoveryOrchestrator
try:
    from ..infrastructure.multi_region import MultiRegionManager
except ImportError:
    MultiRegionManager = None
from ..monitoring import UnifiedMonitoringSystem as MonitoringSystem
from ..notifications import NotificationService

logger = logging.getLogger(__name__)


class RegionStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    RECOVERING = "recovering"


class FailoverStatus(Enum):
    NONE = "none"
    DETECTED = "detected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Region:
    """Represents a deployment region."""
    name: str
    primary: bool
    status: RegionStatus
    endpoint: str
    last_heartbeat: Optional[datetime] = None
    failover_priority: int = 0


@dataclass
class DisasterRecoveryPlan:
    """Disaster recovery plan configuration."""
    name: str
    primary_region: str
    backup_regions: List[str]
    rto_minutes: int  # Recovery Time Objective
    rpo_minutes: int  # Recovery Point Objective
    auto_failover: bool = True
    data_sync_interval: int = 300  # 5 minutes
    health_check_interval: int = 60  # 1 minute


class DisasterRecovery:
    """Manages disaster recovery and cross-region failover."""

    def __init__(self, backup_system: AutomatedBackupSystem,
                 recovery_orchestrator: RecoveryOrchestrator,
                 multi_region_manager: Optional[MultiRegionManager] = None,
                 monitoring_system: Optional[MonitoringSystem] = None,
                 notification_service: Optional[NotificationService] = None):
        self.backup_system = backup_system
        self.recovery_orchestrator = recovery_orchestrator
        self.multi_region = multi_region_manager
        self.monitoring = monitoring_system
        self.notifications = notification_service

        self.regions: Dict[str, Region] = {}
        self.plans: Dict[str, DisasterRecoveryPlan] = {}
        self.failover_status: Dict[str, FailoverStatus] = {}
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None

    def add_region(self, region: Region):
        """Add a region to the disaster recovery setup."""
        self.regions[region.name] = region
        self.failover_status[region.name] = FailoverStatus.NONE
        logger.info(f"Added region: {region.name}")

    def create_plan(self, plan: DisasterRecoveryPlan):
        """Create a disaster recovery plan."""
        self.plans[plan.name] = plan
        logger.info(f"Created DR plan: {plan.name}")

    async def start(self):
        """Start disaster recovery monitoring."""
        self.running = True
        self._monitor_task = asyncio.create_task(self._health_monitor_loop())
        self._sync_task = asyncio.create_task(self._data_sync_loop())
        logger.info("Disaster recovery system started")

    async def stop(self):
        """Stop disaster recovery monitoring."""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Disaster recovery system stopped")

    async def _health_monitor_loop(self):
        """Monitor region health and trigger failovers."""
        while self.running:
            try:
                await self._check_region_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)

    async def _check_region_health(self):
        """Check health of all regions."""
        for region_name, region in self.regions.items():
            try:
                healthy = await self._check_region_status(region)
                region.last_heartbeat = datetime.now()

                if not healthy and region.status == RegionStatus.ACTIVE:
                    logger.warning(f"Region {region_name} health check failed")
                    await self._initiate_failover(region_name)
                elif healthy and region.status == RegionStatus.FAILED:
                    logger.info(f"Region {region_name} recovered")
                    region.status = RegionStatus.STANDBY
                    await self._consider_failback(region_name)

            except Exception as e:
                logger.error(f"Health check error for {region_name}: {e}")
                if region.status == RegionStatus.ACTIVE:
                    await self._initiate_failover(region_name)

    async def _check_region_status(self, region: Region) -> bool:
        """Check if a region is healthy."""
        # This would implement actual health checks
        # For now, simulate based on configuration
        if self.monitoring:
            # Use monitoring system for health checks
            return await self.monitoring.check_region_health(region.name)
        else:
            # Simple ping check
            try:
                # Simulate health check
                return True  # Assume healthy for demo
            except:
                return False

    async def _initiate_failover(self, failed_region: str):
        """Initiate failover from a failed region."""
        region = self.regions[failed_region]
        region.status = RegionStatus.FAILED
        self.failover_status[failed_region] = FailoverStatus.DETECTED

        logger.warning(f"Initiating failover from region: {failed_region}")

        # Find applicable DR plan
        plan = self._find_dr_plan_for_region(failed_region)
        if not plan or not plan.auto_failover:
            logger.info(f"No auto-failover configured for {failed_region}")
            return

        # Find best backup region
        backup_region = self._select_backup_region(plan)
        if not backup_region:
            logger.error(f"No suitable backup region found for {failed_region}")
            self.failover_status[failed_region] = FailoverStatus.FAILED
            return

        self.failover_status[failed_region] = FailoverStatus.IN_PROGRESS

        try:
            # Execute failover
            success = await self._execute_failover(failed_region, backup_region, plan)
            if success:
                self.failover_status[failed_region] = FailoverStatus.COMPLETED
                logger.info(f"Failover completed: {failed_region} -> {backup_region}")
                if self.notifications:
                    await self.notifications.send_alert(
                        "Disaster Recovery: Failover Completed",
                        f"Failed over from {failed_region} to {backup_region}"
                    )
            else:
                self.failover_status[failed_region] = FailoverStatus.FAILED
                logger.error(f"Failover failed: {failed_region} -> {backup_region}")

        except Exception as e:
            self.failover_status[failed_region] = FailoverStatus.FAILED
            logger.error(f"Failover error: {e}")

    def _find_dr_plan_for_region(self, region_name: str) -> Optional[DisasterRecoveryPlan]:
        """Find the DR plan that includes the given region."""
        for plan in self.plans.values():
            if plan.primary_region == region_name or region_name in plan.backup_regions:
                return plan
        return None

    def _select_backup_region(self, plan: DisasterRecoveryPlan) -> Optional[str]:
        """Select the best backup region for failover."""
        available_regions = [
            r for r in plan.backup_regions
            if self.regions[r].status in [RegionStatus.STANDBY, RegionStatus.ACTIVE]
        ]

        if not available_regions:
            return None

        # Sort by failover priority
        available_regions.sort(key=lambda r: self.regions[r].failover_priority)
        return available_regions[0]

    async def _execute_failover(self, failed_region: str, backup_region: str, plan: DisasterRecoveryPlan) -> bool:
        """Execute the actual failover process."""
        try:
            # Update region statuses
            self.regions[failed_region].status = RegionStatus.FAILED
            self.regions[backup_region].status = RegionStatus.ACTIVE

            # Trigger recovery in backup region
            recovery_job_id = await self.recovery_orchestrator.initiate_recovery(
                # Create appropriate recovery job
                # This would be more detailed in practice
            )

            # Wait for recovery to complete or timeout
            timeout = timedelta(minutes=plan.rto_minutes)
            start_time = datetime.now()

            while datetime.now() - start_time < timeout:
                job = self.recovery_orchestrator.get_recovery_status(recovery_job_id)
                if job and job.status == 'completed':
                    return True
                elif job and job.status == 'failed':
                    return False
                await asyncio.sleep(10)

            # Timeout
            return False

        except Exception as e:
            logger.error(f"Failover execution error: {e}")
            return False

    async def _consider_failback(self, recovered_region: str):
        """Consider failing back to a recovered region."""
        # Check if this region was primary
        region = self.regions[recovered_region]
        plan = self._find_dr_plan_for_region(recovered_region)

        if plan and plan.primary_region == recovered_region:
            # Check if current active region can be failed back
            current_active = None
            for r_name, r in self.regions.items():
                if r.status == RegionStatus.ACTIVE and r_name != recovered_region:
                    current_active = r_name
                    break

            if current_active:
                logger.info(f"Considering failback to {recovered_region} from {current_active}")
                # Implement failback logic
                # This would be similar to failover but in reverse

    async def _data_sync_loop(self):
        """Continuously sync data across regions."""
        while self.running:
            try:
                await self._sync_data_across_regions()
                await asyncio.sleep(300)  # Sync every 5 minutes
            except Exception as e:
                logger.error(f"Data sync error: {e}")
                await asyncio.sleep(300)

    async def _sync_data_across_regions(self):
        """Sync critical data across regions."""
        for plan in self.plans.values():
            try:
                await self._sync_plan_data(plan)
            except Exception as e:
                logger.error(f"Data sync error for plan {plan.name}: {e}")

    async def _sync_plan_data(self, plan: DisasterRecoveryPlan):
        """Sync data for a specific DR plan."""
        primary_region = plan.primary_region

        # Sync from primary to backups
        for backup_region in plan.backup_regions:
            try:
                await self._sync_region_data(primary_region, backup_region)
            except Exception as e:
                logger.error(f"Sync error {primary_region} -> {backup_region}: {e}")

    async def _sync_region_data(self, source_region: str, target_region: str):
        """Sync data between two regions."""
        # This would implement actual data synchronization
        # Could use database replication, file sync, etc.
        if self.multi_region:
            await self.multi_region.sync_regions(source_region, target_region)
        else:
            # Fallback: trigger backup and restore
            await self.backup_system.manual_backup(f"sync_{source_region}_{target_region}")

    async def manual_failover(self, from_region: str, to_region: str) -> bool:
        """Manually trigger failover between regions."""
        if from_region not in self.regions or to_region not in self.regions:
            return False

        plan = self._find_dr_plan_for_region(from_region)
        if not plan:
            return False

        logger.info(f"Manual failover: {from_region} -> {to_region}")
        return await self._execute_failover(from_region, to_region, plan)

    def get_region_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all regions."""
        return {
            name: {
                'status': region.status.value,
                'primary': region.primary,
                'last_heartbeat': region.last_heartbeat.isoformat() if region.last_heartbeat else None,
                'failover_status': self.failover_status[name].value
            }
            for name, region in self.regions.items()
        }

    def get_dr_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all disaster recovery plans."""
        return {
            name: {
                'primary_region': plan.primary_region,
                'backup_regions': plan.backup_regions,
                'rto_minutes': plan.rto_minutes,
                'rpo_minutes': plan.rpo_minutes,
                'auto_failover': plan.auto_failover
            }
            for name, plan in self.plans.items()
        }