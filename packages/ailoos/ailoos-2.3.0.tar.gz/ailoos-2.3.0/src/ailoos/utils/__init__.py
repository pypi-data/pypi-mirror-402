"""
Utility functions for Ailoos library.
"""

from .logging import configure_logging as setup_logging
from .hardware import get_hardware_info

__all__ = ["setup_logging", "get_hardware_info"]