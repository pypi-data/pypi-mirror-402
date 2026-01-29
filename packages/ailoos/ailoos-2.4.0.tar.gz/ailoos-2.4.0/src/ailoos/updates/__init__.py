"""
Automatic updates system for Ailoos.
Provides seamless updates for models, software, and configurations.
"""

from .auto_updater import AutoUpdater, UpdateInfo, UpdateStatus
from .auto_updates import UpdateManager, get_update_manager

__all__ = [
    'AutoUpdater',
    'UpdateManager',
    'UpdateInfo',
    'UpdateStatus',
    'get_update_manager'
]