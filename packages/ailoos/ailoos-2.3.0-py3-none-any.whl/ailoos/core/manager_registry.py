"""
Centralized Manager Registry for AILOOS

This module provides a unified registry pattern for all Manager classes
to prevent duplication and provide centralized access.
"""

import logging
from typing import Dict, Type, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ManagerRegistry:
    """
    Centralized registry for all Manager classes in AILOOS.

    This registry prevents duplication by providing:
    - Single instance management (Singleton pattern)
    - Centralized configuration
    - Unified access patterns
    - Automatic dependency injection
    """

    _instance = None
    _managers: Dict[str, Any] = {}
    _manager_classes: Dict[str, Type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_manager(cls, name: str, manager_class: Type):
        """Register a manager class in the central registry."""
        cls._manager_classes[name] = manager_class
        logger.info(f"Registered manager class: {name}")

    @classmethod
    def get_manager(cls, name: str, *args, **kwargs) -> Any:
        """Get or create a manager instance."""
        if name not in cls._managers:
            if name not in cls._manager_classes:
                raise ValueError(f"Manager '{name}' not registered")

            manager_class = cls._manager_classes[name]
            cls._managers[name] = manager_class(*args, **kwargs)
            logger.info(f"Created manager instance: {name}")

        return cls._managers[name]

    @classmethod
    def has_manager(cls, name: str) -> bool:
        """Check if a manager is registered."""
        return name in cls._manager_classes

    @classmethod
    def list_managers(cls) -> list:
        """List all registered manager names."""
        return list(cls._manager_classes.keys())

    @classmethod
    def reset(cls):
        """Reset the registry (mainly for testing)."""
        cls._managers.clear()
        logger.info("Manager registry reset")


class BaseManager(ABC):
    """
    Base class for all Manager classes in AILOOS.

    Provides common functionality and ensures proper registration.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-register managers that inherit from BaseManager
        manager_name = cls.__name__.lower().replace('manager', '')
        ManagerRegistry.register_manager(manager_name, cls)

    @abstractmethod
    def initialize(self):
        """Initialize the manager."""
        pass

    @abstractmethod
    def shutdown(self):
        """Shutdown the manager gracefully."""
        pass


# Convenience functions for global access
def get_manager(name: str, *args, **kwargs) -> Any:
    """Global function to get a manager instance."""
    return ManagerRegistry.get_manager(name, *args, **kwargs)


def register_manager(name: str, manager_class: Type):
    """Global function to register a manager class."""
    ManagerRegistry.register_manager(name, manager_class)


# Initialize the registry
registry = ManagerRegistry()