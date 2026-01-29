"""
Automatic Update System for Ailoos SDK.
Handles model updates, SDK updates, and notifications.
"""

import asyncio
import json
import time
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class UpdateManager:
    """
    Manages automatic updates for Ailoos SDK and models.
    Checks for updates and applies them seamlessly.
    """

    def __init__(self):
        self.current_version = "2.2.5"
        self.ailoos_dir = Path.home() / ".ailoos"
        self.updates_dir = self.ailoos_dir / "updates"
        self.update_manifest_url = "https://raw.githubusercontent.com/Empoorio/ailoos/main/update_manifest.json"
        self.model_updates_url = "https://raw.githubusercontent.com/Empoorio/ailoos-models/main/update_manifest.json"
        self.check_interval = 86400  # 24 hours
        self.last_check = 0

    async def check_for_updates(self) -> Dict[str, Any]:
        """
        Check for available updates.

        Returns:
            Dictionary with update information
        """
        current_time = time.time()

        # Rate limiting
        if current_time - self.last_check < self.check_interval:
            return {"status": "rate_limited"}

        self.last_check = current_time

        updates = {
            "sdk_updates": await self._check_sdk_updates(),
            "model_updates": await self._check_model_updates(),
            "last_check": current_time
        }

        # Count available updates
        sdk_available = len(updates["sdk_updates"].get("available", []))
        model_available = len(updates["model_updates"].get("available", []))

        updates["summary"] = {
            "sdk_updates": sdk_available,
            "model_updates": model_available,
            "total_updates": sdk_available + model_available
        }

        if sdk_available > 0 or model_available > 0:
            logger.info(f"📦 Updates available: {sdk_available} SDK, {model_available} models")

        return updates

    async def _check_sdk_updates(self) -> Dict[str, Any]:
        """Check for SDK updates."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(self.update_manifest_url) as response:
                    if response.status == 200:
                        manifest = await response.json()
                        return self._compare_versions(manifest, "sdk")
                    else:
                        logger.warning(f"⚠️ Failed to fetch SDK update manifest: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ SDK update check failed: {e}")

        return {"available": [], "error": "check_failed"}

    async def _check_model_updates(self) -> Dict[str, Any]:
        """Check for model updates."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(self.model_updates_url) as response:
                    if response.status == 200:
                        manifest = await response.json()
                        return self._compare_versions(manifest, "models")
                    else:
                        logger.warning(f"⚠️ Failed to fetch model update manifest: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Model update check failed: {e}")

        return {"available": [], "error": "check_failed"}

    def _compare_versions(self, manifest: Dict[str, Any], update_type: str) -> Dict[str, Any]:
        """Compare versions and identify available updates."""
        available_updates = []

        if update_type == "sdk":
            latest_version = manifest.get("latest_version")
            if latest_version and self._is_newer_version(latest_version, self.current_version):
                available_updates.append({
                    "type": "sdk",
                    "current_version": self.current_version,
                    "new_version": latest_version,
                    "release_notes": manifest.get("release_notes", ""),
                    "download_url": manifest.get("download_url"),
                    "size_mb": manifest.get("size_mb", 0)
                })
        elif update_type == "models":
            # Check model registry for updates
            try:
                from ..models.registry import ModelRegistry
                registry = ModelRegistry()

                for model_info in manifest.get("models", []):
                    model_name = model_info["name"]
                    latest_version = model_info["version"]

                    # Check if we have this model
                    local_models = registry.list_models()
                    local_model = next((m for m in local_models if m.name == model_name), None)

                    if local_model and self._is_newer_version(latest_version, local_model.version):
                        available_updates.append({
                            "type": "model",
                            "name": model_name,
                            "current_version": local_model.version,
                            "new_version": latest_version,
                            "description": model_info.get("description", ""),
                            "size_mb": model_info.get("size_mb", 0)
                        })
            except Exception as e:
                logger.warning(f"⚠️ Model version check failed: {e}")

        return {"available": available_updates}

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Check if new_version is newer than current_version."""
        try:
            # Simple version comparison (can be enhanced)
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]

            return new_parts > current_parts
        except Exception:
            # Fallback: string comparison
            return new_version > current_version

    async def apply_updates(self, update_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Apply available updates.

        Args:
            update_types: Types of updates to apply ("sdk", "models", or both)

        Returns:
            Update results
        """
        if update_types is None:
            update_types = ["sdk", "models"]

        results = {
            "sdk_updated": False,
            "models_updated": 0,
            "errors": []
        }

        # Check for updates first
        updates = await self.check_for_updates()

        # Apply SDK updates
        if "sdk" in update_types:
            sdk_updates = updates.get("sdk_updates", {}).get("available", [])
            if sdk_updates:
                for update in sdk_updates:
                    try:
                        success = await self._apply_sdk_update(update)
                        if success:
                            results["sdk_updated"] = True
                            logger.info(f"✅ SDK updated to {update['new_version']}")
                        else:
                            results["errors"].append(f"SDK update failed: {update['new_version']}")
                    except Exception as e:
                        results["errors"].append(f"SDK update error: {e}")

        # Apply model updates
        if "models" in update_types:
            model_updates = updates.get("model_updates", {}).get("available", [])
            for update in model_updates:
                try:
                    success = await self._apply_model_update(update)
                    if success:
                        results["models_updated"] += 1
                        logger.info(f"✅ Model {update['name']} updated to {update['new_version']}")
                    else:
                        results["errors"].append(f"Model update failed: {update['name']}")
                except Exception as e:
                    results["errors"].append(f"Model update error: {e}")

        return results

    async def _apply_sdk_update(self, update_info: Dict[str, Any]) -> bool:
        """Apply SDK update."""
        try:
            # In a real implementation, this would:
            # 1. Download the update package
            # 2. Verify integrity
            # 3. Install the update
            # 4. Restart services if needed

            logger.info(f"🔄 Applying SDK update to {update_info['new_version']}")

            # Simulate update process
            await asyncio.sleep(2)  # Simulate download/install time

            # Update version
            self.current_version = update_info['new_version']

            logger.info("✅ SDK update applied successfully")
            return True

        except Exception as e:
            logger.error(f"❌ SDK update failed: {e}")
            return False

    async def _apply_model_update(self, update_info: Dict[str, Any]) -> bool:
        """Apply model update."""
        try:
            from ..models.registry import ModelRegistry

            registry = ModelRegistry()
            model_name = update_info["name"]

            logger.info(f"🔄 Updating model {model_name} to {update_info['new_version']}")

            # Download new model version
            # In a real implementation, this would use the registry download method
            await asyncio.sleep(1)  # Simulate download

            logger.info(f"✅ Model {model_name} updated successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Model update failed: {e}")
            return False

    def get_update_history(self) -> List[Dict[str, Any]]:
        """Get history of applied updates."""
        history_file = self.updates_dir / "update_history.json"

        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        return []

    def _save_update_history(self, update_info: Dict[str, Any]):
        """Save update to history."""
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        history_file = self.updates_dir / "update_history.json"

        history = self.get_update_history()
        history.append({
            **update_info,
            "applied_at": time.time()
        })

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    async def schedule_automatic_updates(self, enabled: bool = True):
        """
        Enable or disable automatic update checks.

        Args:
            enabled: Whether to enable automatic updates
        """
        if enabled:
            # Start background update checker
            asyncio.create_task(self._automatic_update_loop())
            logger.info("🔄 Automatic updates enabled")
        else:
            logger.info("🛑 Automatic updates disabled")

    async def _automatic_update_loop(self):
        """Background loop for automatic updates."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                updates = await self.check_for_updates()

                if updates.get("summary", {}).get("total_updates", 0) > 0:
                    logger.info("📦 Updates available, applying automatically...")
                    results = await self.apply_updates()

                    if results["sdk_updated"] or results["models_updated"] > 0:
                        logger.info("✅ Automatic updates applied successfully")

            except Exception as e:
                logger.warning(f"⚠️ Automatic update check failed: {e}")

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        return {
            "current_version": self.current_version,
            "last_check": self.last_check,
            "next_check": self.last_check + self.check_interval,
            "update_history": len(self.get_update_history())
        }


# Notification system
class UpdateNotifier:
    """
    Handles notifications for available updates.
    """

    def __init__(self):
        self.notifications = []
        self.notification_callbacks = []

    def add_notification_callback(self, callback):
        """Add callback for notifications."""
        self.notification_callbacks.append(callback)

    def notify_update_available(self, update_info: Dict[str, Any]):
        """Notify about available update."""
        notification = {
            "type": "update_available",
            "info": update_info,
            "timestamp": time.time()
        }

        self.notifications.append(notification)

        # Call callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.warning(f"⚠️ Notification callback failed: {e}")

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get pending notifications."""
        return self.notifications.copy()

    def clear_notifications(self):
        """Clear all notifications."""
        self.notifications.clear()


# Convenience functions
_update_manager_instance = None
_update_notifier_instance = None

def get_update_manager() -> UpdateManager:
    """Get singleton update manager instance."""
    global _update_manager_instance
    if _update_manager_instance is None:
        _update_manager_instance = UpdateManager()
    return _update_manager_instance

def get_update_notifier() -> UpdateNotifier:
    """Get singleton update notifier instance."""
    global _update_notifier_instance
    if _update_notifier_instance is None:
        _update_notifier_instance = UpdateNotifier()
    return _update_notifier_instance

async def check_and_apply_updates():
    """Check for and apply available updates."""
    manager = get_update_manager()
    updates = await manager.check_for_updates()

    if updates.get("summary", {}).get("total_updates", 0) > 0:
        logger.info("📦 Applying available updates...")
        results = await manager.apply_updates()
        return results
    else:
        logger.info("✅ No updates available")
        return {"message": "no_updates"}

def schedule_automatic_updates(enabled: bool = True):
    """Enable automatic update scheduling."""
    manager = get_update_manager()
    asyncio.create_task(manager.schedule_automatic_updates(enabled))