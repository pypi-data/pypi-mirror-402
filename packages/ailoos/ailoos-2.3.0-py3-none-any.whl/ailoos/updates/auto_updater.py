#!/usr/bin/env python3
"""
Auto Updater System for Ailoos
Implementa actualizaciones automáticas con rollback y verificación de integridad
"""

import asyncio
import logging
import os
import sys
import hashlib
import json
import tempfile
import shutil
import subprocess
import time
import importlib.util
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import aiofiles
from pathlib import Path
import platform
import zipfile
import tarfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpdateStatus(Enum):
    """Estados de actualización"""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class UpdateType(Enum):
    """Tipos de actualización"""
    PATCH = "patch"           # Corrección de bugs
    MINOR = "minor"          # Nuevas funcionalidades compatibles
    MAJOR = "major"          # Cambios incompatibles
    SECURITY = "security"    # Actualización de seguridad crítica
    HOTFIX = "hotfix"        # Corrección urgente

@dataclass
class UpdateInfo:
    """Información de una actualización"""
    version: str
    update_type: UpdateType
    release_date: datetime
    description: str
    changelog: List[str]
    download_url: str
    checksum_sha256: str
    file_size: int
    minimum_version: str
    breaking_changes: bool = False
    requires_restart: bool = True
    rollback_available: bool = True

@dataclass
class UpdateAttempt:
    """Intento de actualización"""
    update_id: str
    update_info: UpdateInfo
    status: UpdateStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_available: bool = True
    backup_path: Optional[str] = None

@dataclass
class UpdatePolicy:
    """Política de actualizaciones"""
    auto_update_enabled: bool = True
    update_check_interval_hours: int = 24
    allowed_update_types: List[UpdateType] = field(default_factory=lambda: [UpdateType.PATCH, UpdateType.MINOR, UpdateType.SECURITY])
    maintenance_window_start: str = "02:00"  # HH:MM
    maintenance_window_end: str = "04:00"    # HH:MM
    max_download_retries: int = 3
    download_timeout_seconds: int = 300
    verification_required: bool = True
    backup_before_update: bool = True
    rollback_on_failure: bool = True
    notify_on_available: bool = True

class AutoUpdater:
    """
    Sistema de actualizaciones automáticas con rollback inteligente
    """

    def __init__(self, current_version: str, update_server_url: str,
                 install_path: str, policy: UpdatePolicy = None):
        self.current_version = current_version
        self.update_server_url = update_server_url
        self.install_path = Path(install_path)
        self.policy = policy or UpdatePolicy()

        # Update state
        self.available_updates: List[UpdateInfo] = []
        self.update_history: List[UpdateAttempt] = []
        self.current_attempt: Optional[UpdateAttempt] = None

        # File management
        self.temp_dir = Path(tempfile.gettempdir()) / "ailoos_updates"
        self.backup_dir = self.install_path / ".backups"
        self.temp_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # HTTP client
        self.session: Optional[aiohttp.ClientSession] = None

        # Callbacks
        self.update_callbacks: Dict[str, List[Callable]] = {
            'update_available': [],
            'update_started': [],
            'update_progress': [],
            'update_completed': [],
            'update_failed': [],
            'rollback_started': [],
            'rollback_completed': []
        }

        # Background tasks
        self.check_task: Optional[asyncio.Task] = None
        self.is_running = False

        logger.info(f"🔄 Auto Updater initialized for version {current_version}")

    async def start(self):
        """Start the auto updater"""
        if self.is_running:
            return

        self.is_running = True
        self.session = aiohttp.ClientSession()

        # Initial update check
        await self.check_for_updates()

        # Start periodic update checks
        self.check_task = asyncio.create_task(self._periodic_update_check())

        logger.info("▶️ Auto updater started")

    async def stop(self):
        """Stop the auto updater"""
        if not self.is_running:
            return

        self.is_running = False

        if self.check_task:
            self.check_task.cancel()

        if self.session:
            await self.session.close()

        logger.info("⏹️ Auto updater stopped")

    def register_callback(self, event: str, callback: Callable):
        """Register callback for update events"""
        if event in self.update_callbacks:
            self.update_callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger callbacks for an event"""
        for callback in self.update_callbacks[event]:
            try:
                await callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    async def check_for_updates(self) -> List[UpdateInfo]:
        """Check for available updates"""
        try:
            url = f"{self.update_server_url}/updates/check"
            params = {
                'current_version': self.current_version,
                'platform': platform.system().lower(),
                'architecture': platform.machine()
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    updates = []

                    for update_data in data.get('updates', []):
                        update = UpdateInfo(
                            version=update_data['version'],
                            update_type=UpdateType(update_data['type']),
                            release_date=datetime.fromisoformat(update_data['release_date']),
                            description=update_data['description'],
                            changelog=update_data.get('changelog', []),
                            download_url=update_data['download_url'],
                            checksum_sha256=update_data['checksum'],
                            file_size=update_data['size'],
                            minimum_version=update_data.get('minimum_version', '0.0.0'),
                            breaking_changes=update_data.get('breaking_changes', False),
                            requires_restart=update_data.get('requires_restart', True),
                            rollback_available=update_data.get('rollback_available', True)
                        )

                        # Filter by policy
                        if update.update_type in self.policy.allowed_update_types:
                            updates.append(update)

                    self.available_updates = updates

                    if updates:
                        logger.info(f"📦 Found {len(updates)} available updates")
                        await self._trigger_callbacks('update_available', updates)
                    else:
                        logger.debug("No updates available")

                    return updates

                else:
                    logger.warning(f"Update check failed: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Update check error: {e}")
            return []

    async def download_update(self, update_info: UpdateInfo) -> Optional[Path]:
        """Download update package"""
        try:
            # Create download path
            download_path = self.temp_dir / f"update_{update_info.version}_{int(time.time())}.tmp"

            logger.info(f"⬇️ Downloading update {update_info.version}...")

            # Download with progress
            async with self.session.get(update_info.download_url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed: HTTP {response.status}")

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                async with aiofiles.open(download_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                        downloaded += len(chunk)

                        # Report progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            await self._trigger_callbacks('update_progress',
                                                        update_info.version, 'download', progress)

            # Verify checksum
            if self.policy.verification_required:
                await self._verify_checksum(download_path, update_info.checksum_sha256)

            logger.info(f"✅ Update {update_info.version} downloaded successfully")
            return download_path

        except Exception as e:
            logger.error(f"Download failed: {e}")
            if download_path.exists():
                download_path.unlink()
            return None

    async def _verify_checksum(self, file_path: Path, expected_checksum: str):
        """Verify file checksum"""
        sha256 = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)

        actual_checksum = sha256.hexdigest()

        if actual_checksum != expected_checksum:
            raise Exception(f"Checksum verification failed. Expected: {expected_checksum}, Got: {actual_checksum}")

    async def install_update(self, update_info: UpdateInfo, download_path: Path) -> bool:
        """Install update with rollback capability"""
        attempt = UpdateAttempt(
            update_id=f"update_{update_info.version}_{int(time.time())}",
            update_info=update_info,
            status=UpdateStatus.INSTALLING,
            started_at=datetime.now(),
            rollback_available=update_info.rollback_available
        )

        self.current_attempt = attempt
        self.update_history.append(attempt)

        try:
            await self._trigger_callbacks('update_started', update_info)

            # Create backup if required
            if self.policy.backup_before_update and update_info.rollback_available:
                attempt.backup_path = await self._create_backup()
                logger.info(f"💾 Backup created: {attempt.backup_path}")

            # Extract update
            extract_path = self.temp_dir / f"extract_{update_info.version}"
            extract_path.mkdir(exist_ok=True)

            await self._extract_package(download_path, extract_path)

            # Pre-installation checks
            await self._run_pre_install_checks(update_info, extract_path)

            # Install files
            await self._install_files(extract_path, update_info)

            # Post-installation tasks
            await self._run_post_install_tasks(update_info)

            # Mark as installed
            attempt.status = UpdateStatus.INSTALLED
            attempt.completed_at = datetime.now()

            await self._trigger_callbacks('update_completed', update_info)

            # Update current version
            self.current_version = update_info.version

            logger.info(f"✅ Update {update_info.version} installed successfully")
            return True

        except Exception as e:
            logger.error(f"Installation failed: {e}")

            attempt.status = UpdateStatus.FAILED
            attempt.error_message = str(e)
            attempt.completed_at = datetime.now()

            await self._trigger_callbacks('update_failed', update_info, str(e))

            # Attempt rollback if enabled
            if self.policy.rollback_on_failure and attempt.backup_path:
                await self.rollback_update(attempt)

            return False

    async def _create_backup(self) -> str:
        """Create backup of current installation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{self.current_version}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        # Create backup archive
        backup_archive = backup_path.with_suffix('.tar.gz')
        await self._create_archive(str(self.install_path), str(backup_archive))

        return str(backup_archive)

    async def _create_archive(self, source_path: str, archive_path: str):
        """Create compressed archive"""
        def create_tar():
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(source_path, arcname=os.path.basename(source_path))

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_tar)

    async def _extract_package(self, package_path: Path, extract_path: Path):
        """Extract update package"""
        def extract():
            if package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            elif package_path.suffixes[-2:] == ['.tar', '.gz']:
                with tarfile.open(package_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_path)
            else:
                raise Exception(f"Unsupported package format: {package_path.suffix}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, extract)

    async def _run_pre_install_checks(self, update_info: UpdateInfo, extract_path: Path):
        """Run pre-installation checks"""
        # Check minimum version requirement
        if self._compare_versions(update_info.minimum_version, self.current_version) > 0:
            raise Exception(f"Current version {self.current_version} is below minimum required {update_info.minimum_version}")

        # Check for required files
        required_files = ['manifest.json', 'version.txt']  # Example
        for required_file in required_files:
            if not (extract_path / required_file).exists():
                raise Exception(f"Required file missing: {required_file}")

        # Validate manifest
        manifest_path = extract_path / 'manifest.json'
        async with aiofiles.open(manifest_path, 'r') as f:
            manifest = json.loads(await f.read())

        # Additional validation logic here...

    async def _install_files(self, extract_path: Path, update_info: UpdateInfo):
        """Install update files"""
        # Read manifest
        manifest_path = extract_path / 'manifest.json'
        async with aiofiles.open(manifest_path, 'r') as f:
            manifest = json.loads(await f.read())

        # Install files according to manifest
        for file_spec in manifest.get('files', []):
            source = extract_path / file_spec['source']
            destination = self.install_path / file_spec['destination']

            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)

            if source.is_file():
                # Copy file
                shutil.copy2(source, destination)
            elif source.is_dir():
                # Copy directory
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)

        logger.info(f"📁 Installed {len(manifest.get('files', []))} files")

    async def _run_post_install_tasks(self, update_info: UpdateInfo):
        """Run post-installation tasks"""
        # Run post-install script if present
        post_install_script = self.install_path / 'post_install.py'
        if post_install_script.exists():
            try:
                # Import and run post-install script
                spec = importlib.util.spec_from_file_location("post_install", post_install_script)
                post_install_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(post_install_module)

                if hasattr(post_install_module, 'main'):
                    await post_install_module.main()

            except Exception as e:
                logger.warning(f"Post-install script failed: {e}")

        # Clean up temporary files
        await self._cleanup_temp_files()

    async def rollback_update(self, attempt: UpdateAttempt) -> bool:
        """Rollback a failed update"""
        if not attempt.backup_path or not attempt.rollback_available:
            logger.warning("Rollback not available for this update")
            return False

        try:
            await self._trigger_callbacks('rollback_started', attempt)

            backup_path = Path(attempt.backup_path)
            if not backup_path.exists():
                raise Exception(f"Backup file not found: {backup_path}")

            # Extract backup
            temp_restore_path = self.temp_dir / f"restore_{attempt.update_id}"
            temp_restore_path.mkdir(exist_ok=True)

            await self._extract_archive(backup_path, temp_restore_path)

            # Restore files
            for item in temp_restore_path.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(temp_restore_path)
                    destination = self.install_path / relative_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, destination)

            # Update attempt status
            attempt.status = UpdateStatus.ROLLED_BACK

            await self._trigger_callbacks('rollback_completed', attempt)

            # Revert version
            self.current_version = attempt.update_info.minimum_version  # Simplified

            logger.info(f"🔄 Successfully rolled back update {attempt.update_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def _extract_archive(self, archive_path: Path, extract_path: Path):
        """Extract archive"""
        def extract():
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_path)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, extract)

    async def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            # Remove old temp files (older than 1 hour)
            cutoff_time = time.time() - 3600

            for item in self.temp_dir.iterdir():
                if item.stat().st_mtime < cutoff_time:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # Pad shorter version
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1

        return 0

    async def _periodic_update_check(self):
        """Periodic update checking"""
        while self.is_running:
            try:
                await asyncio.sleep(self.policy.update_check_interval_hours * 3600)
                if self.policy.auto_update_enabled:
                    await self.check_for_updates()

                    # Auto-install security updates
                    security_updates = [u for u in self.available_updates
                                      if u.update_type == UpdateType.SECURITY]

                    for update in security_updates:
                        if await self._is_maintenance_window():
                            await self.perform_update(update)
                            break  # Only one security update at a time

            except Exception as e:
                logger.error(f"Periodic update check failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    async def _is_maintenance_window(self) -> bool:
        """Check if current time is within maintenance window"""
        now = datetime.now().time()
        start_time = datetime.strptime(self.policy.maintenance_window_start, "%H:%M").time()
        end_time = datetime.strptime(self.policy.maintenance_window_end, "%H:%M").time()

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Overnight window
            return now >= start_time or now <= end_time

    async def perform_update(self, update_info: UpdateInfo) -> bool:
        """Perform complete update process"""
        try:
            # Download
            download_path = await self.download_update(update_info)
            if not download_path:
                return False

            # Install
            return await self.install_update(update_info, download_path)

        except Exception as e:
            logger.error(f"Update process failed: {e}")
            return False

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status"""
        return {
            'current_version': self.current_version,
            'available_updates': len(self.available_updates),
            'current_attempt': self.current_attempt.update_id if self.current_attempt else None,
            'is_running': self.is_running,
            'policy': {
                'auto_update_enabled': self.policy.auto_update_enabled,
                'update_check_interval_hours': self.policy.update_check_interval_hours,
                'allowed_types': [t.value for t in self.policy.allowed_update_types]
            },
            'recent_updates': [
                {
                    'version': attempt.update_info.version,
                    'status': attempt.status.value,
                    'started_at': attempt.started_at.isoformat(),
                    'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None
                }
                for attempt in self.update_history[-5:]  # Last 5 updates
            ]
        }

# Global updater instance
updater_instance = None

def get_auto_updater(current_version: str, **kwargs) -> AutoUpdater:
    """Get global auto updater instance"""
    global updater_instance
    if updater_instance is None:
        updater_instance = AutoUpdater(current_version, **kwargs)
    return updater_instance

if __name__ == '__main__':
    # Demo
    async def main():
        updater = get_auto_updater(
            current_version="1.0.0",
            update_server_url="https://updates.ailoos.network",
            install_path="/opt/ailoos"
        )

        print("🔄 Auto Updater Demo")
        print("=" * 50)

        # Start updater
        await updater.start()
        print("✅ Auto updater started")

        try:
            # Check for updates
            updates = await updater.check_for_updates()
            print(f"📦 Found {len(updates)} available updates")

            if updates:
                # Show first update
                update = updates[0]
                print(f"🎯 Latest update: {update.version} ({update.update_type.value})")
                print(f"📝 Description: {update.description}")

                # Simulate download and install (would need real update server)
                print("⚠️  Note: Download and install would require real update server")

        finally:
            await updater.stop()
            print("⏹️ Auto updater stopped")

        print("🎉 Auto Updater Demo completed!")

    asyncio.run(main())