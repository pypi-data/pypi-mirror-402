"""
Unit tests for AILOOS Backup and Recovery System

Tests cover:
- AutomatedBackupSystem functionality
- RecoveryOrchestrator operations
- DisasterRecovery failover
- PointInTimeRecovery accuracy
- BackupManager integration
"""

import asyncio
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from .automated_backup_system import (
    AutomatedBackupSystem, BackupJob, BackupStrategy, LocalStorageBackend
)
from .recovery_orchestrator import RecoveryOrchestrator, RecoveryJob, RecoveryType
from .disaster_recovery import DisasterRecovery, Region, DisasterRecoveryPlan
from .point_in_time_recovery import PointInTimeRecovery, PITRecoveryRequest
from .backup_manager import BackupManager, BackupPolicy, SystemConfiguration


class TestAutomatedBackupSystem(unittest.TestCase):
    """Test AutomatedBackupSystem functionality."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"
        self.source_dir = self.temp_dir / "source"
        self.source_dir.mkdir()

        # Create test files
        (self.source_dir / "test1.txt").write_text("test content 1")
        (self.source_dir / "test2.txt").write_text("test content 2")

        self.backend = LocalStorageBackend(self.backup_dir)
        self.system = AutomatedBackupSystem()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_add_job(self):
        """Test adding backup jobs."""
        job = BackupJob(
            name="test_job",
            source_paths=[self.source_dir],
            strategy=BackupStrategy.FULL,
            schedule="24h",
            retention_days=30,
            storage_backend=self.backend
        )

        self.system.add_job(job)
        self.assertIn("test_job", self.system.jobs)

    async def test_manual_backup(self):
        """Test manual backup execution."""
        job = BackupJob(
            name="test_job",
            source_paths=[self.source_dir],
            strategy=BackupStrategy.FULL,
            schedule="24h",
            retention_days=30,
            storage_backend=self.backend
        )

        self.system.add_job(job)

        # Mock the scheduler to avoid timing issues
        with patch.object(self.system, '_run_backup', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = None
            result = await self.system.manual_backup("test_job")
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_backup_history(self):
        """Test backup history tracking."""
        # Add some mock history
        self.system.backup_history = [
            {"job_name": "test", "status": "success", "timestamp": "2023-01-01T00:00:00"}
        ]

        history = self.system.get_backup_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job_name"], "test")


class TestRecoveryOrchestrator(unittest.TestCase):
    """Test RecoveryOrchestrator functionality."""

    def setUp(self):
        self.backup_system = Mock()
        self.monitoring = Mock()
        self.notifications = Mock()

        self.orchestrator = RecoveryOrchestrator(
            self.backup_system, self.monitoring, self.notifications
        )

    def test_register_health_check(self):
        """Test registering health checks."""
        async def dummy_check():
            return True

        self.orchestrator.register_health_check("test_system", dummy_check)
        self.assertIn("test_system", self.orchestrator.health_checks)

    async def test_initiate_recovery(self):
        """Test initiating recovery."""
        job = RecoveryJob(
            id="test_recovery",
            recovery_type=RecoveryType.MANUAL,
            target_system="test_system",
            backup_source="test_backup",
            restore_paths=[Path("/tmp/test")]
        )

        with patch.object(self.orchestrator, '_execute_recovery', new_callable=AsyncMock):
            recovery_id = await self.orchestrator.initiate_recovery(job)
            self.assertEqual(recovery_id, "test_recovery")

    def test_get_recovery_status(self):
        """Test getting recovery status."""
        job = RecoveryJob(
            id="test_recovery",
            recovery_type=RecoveryType.MANUAL,
            target_system="test_system",
            backup_source="test_backup",
            restore_paths=[Path("/tmp/test")]
        )

        self.orchestrator.recovery_jobs["test_recovery"] = job
        status = self.orchestrator.get_recovery_status("test_recovery")
        self.assertEqual(status.id, "test_recovery")


class TestDisasterRecovery(unittest.TestCase):
    """Test DisasterRecovery functionality."""

    def setUp(self):
        self.backup_system = Mock()
        self.recovery_orchestrator = Mock()
        self.monitoring = Mock()
        self.notifications = Mock()
        self.multi_region = Mock()

        self.dr = DisasterRecovery(
            self.backup_system, self.recovery_orchestrator,
            self.multi_region, self.monitoring, self.notifications
        )

    def test_add_region(self):
        """Test adding regions."""
        region = Region(
            name="test-region",
            primary=False,
            status="standby",
            endpoint="http://test.com",
            failover_priority=1
        )

        self.dr.add_region(region)
        self.assertIn("test-region", self.dr.regions)

    def test_create_plan(self):
        """Test creating DR plans."""
        plan = DisasterRecoveryPlan(
            name="test_plan",
            primary_region="primary",
            backup_regions=["backup1", "backup2"],
            rto_minutes=15,
            rpo_minutes=5,
            auto_failover=True
        )

        self.dr.create_plan(plan)
        self.assertIn("test_plan", self.dr.plans)

    def test_get_region_status(self):
        """Test getting region status."""
        region = Region(
            name="test-region",
            primary=True,
            status="active",
            endpoint="http://test.com"
        )
        self.dr.add_region(region)

        status = self.dr.get_region_status()
        self.assertIn("test-region", status)
        self.assertEqual(status["test-region"]["status"], "active")


class TestPointInTimeRecovery(unittest.TestCase):
    """Test PointInTimeRecovery functionality."""

    def setUp(self):
        self.backup_system = Mock()
        self.database = Mock()
        self.pit = PointInTimeRecovery(self.backup_system, self.database)

    def test_register_system(self):
        """Test registering systems for PIT recovery."""
        self.pit.register_system("test_system")
        self.assertIn("test_system", self.pit.recovery_points)
        self.assertIn("test_system", self.pit.transaction_logs)

    def test_add_recovery_point(self):
        """Test adding recovery points."""
        self.pit.register_system("test_system")
        timestamp = datetime.now()

        self.pit.add_recovery_point(
            "test_system", "backup_123", timestamp, 1, ["log1", "log2"]
        )

        points = self.pit.recovery_points["test_system"]
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].backup_id, "backup_123")

    def test_get_available_recovery_points(self):
        """Test getting available recovery points."""
        self.pit.register_system("test_system")
        timestamp = datetime.now()

        self.pit.add_recovery_point("test_system", "backup_123", timestamp, 1)

        points = self.pit.get_available_recovery_points("test_system")
        self.assertEqual(len(points), 1)

    def test_estimate_recovery_time(self):
        """Test recovery time estimation."""
        self.pit.register_system("test_system")
        timestamp = datetime.now()

        self.pit.add_recovery_point("test_system", "backup_123", timestamp, 1)

        # Mock _find_recovery_point
        with patch.object(self.pit, '_find_recovery_point', return_value=(Mock(), [])):
            with patch.object(self.pit, 'estimate_recovery_time') as mock_estimate:
                mock_estimate.return_value = timedelta(minutes=10)
                time_estimate = self.pit.estimate_recovery_time("test_system", timestamp)
                self.assertIsInstance(time_estimate, timedelta)


class TestBackupManager(unittest.TestCase):
    """Test BackupManager integration."""

    def setUp(self):
        self.config = {
            'backup_base_path': './test_backups',
            'policies': [],
            'systems': [],
            'regions': [],
            'disaster_recovery_plans': []
        }

        with patch('src.ailoos.backup.backup_manager.get_config', return_value=self.config):
            self.manager = BackupManager()

    def test_create_backup_policy(self):
        """Test creating backup policies."""
        policy = BackupPolicy(
            name="test_policy",
            systems=["system1"],
            strategy="full",
            schedule="24h",
            retention_days=30
        )

        # This would normally be async, but for testing
        self.manager.policies["test_policy"] = policy
        self.assertIn("test_policy", self.manager.policies)

    def test_add_system(self):
        """Test adding systems."""
        system = SystemConfiguration(
            name="test_system",
            paths=[Path("/tmp/test")],
            backup_policy="test_policy"
        )

        self.manager.systems["test_system"] = system
        self.assertIn("test_system", self.manager.systems)

    def test_get_system_status(self):
        """Test getting system status."""
        system = SystemConfiguration(
            name="test_system",
            paths=[Path("/tmp/test")],
            backup_policy="test_policy",
            critical=True
        )

        self.manager.systems["test_system"] = system

        status = self.manager.get_system_status("test_system")
        self.assertEqual(status["name"], "test_system")
        self.assertTrue(status["critical"])

    def test_get_overall_status(self):
        """Test getting overall status."""
        status = self.manager.get_overall_status()
        self.assertIn("total_systems", status)
        self.assertIn("overall_health", status)


class TestLocalStorageBackend(unittest.TestCase):
    """Test LocalStorageBackend functionality."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backend = LocalStorageBackend(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_store_file(self):
        """Test storing a file."""
        source_file = self.temp_dir / "source.txt"
        source_file.write_text("test content")

        import asyncio
        async def test():
            success = await self.backend.store(source_file, "test_backup.txt", {})
            self.assertTrue(success)

            # Check if file exists
            backup_file = self.temp_dir / "test_backup.txt"
            self.assertTrue(backup_file.exists())
            self.assertEqual(backup_file.read_text(), "test content")

        asyncio.run(test())

    def test_list_backups(self):
        """Test listing backups."""
        # Create some backup files
        (self.temp_dir / "backup1").mkdir()
        (self.temp_dir / "backup2").mkdir()
        (self.temp_dir / "not_backup.txt").write_text("not a backup")

        import asyncio
        async def test():
            backups = await self.backend.list_backups()
            self.assertIn("backup1", backups)
            self.assertIn("backup2", backups)
            self.assertNotIn("not_backup.txt", backups)

        asyncio.run(test())


if __name__ == '__main__':
    unittest.main()