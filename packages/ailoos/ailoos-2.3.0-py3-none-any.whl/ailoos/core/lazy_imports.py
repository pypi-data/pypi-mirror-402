"""
Lazy import system for AILOOS optional modules.

This module provides lazy loading of optional dependencies to prevent import errors
and improve startup performance.
"""

import importlib
import os
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# Registry of optional modules and their mock implementations
OPTIONAL_MODULES: Dict[str, Dict[str, Any]] = {
    'flwr': {
        'mock_available': True,
        'mock_class': 'MockFlowerClient',
        'description': 'Flower Federated Learning'
    },
    'tensorflow': {
        'mock_available': True,
        'mock_class': 'MockTensorFlow',
        'description': 'TensorFlow ML framework'
    },
    'torch': {
        'mock_available': False,  # Torch is critical, don't mock
        'description': 'PyTorch ML framework'
    },
    'transformers': {
        'mock_available': False,  # Critical for AI functionality
        'description': 'Hugging Face Transformers'
    },
    'kubernetes': {
        'mock_available': True,
        'mock_class': 'MockKubernetesClient',
        'description': 'Kubernetes client'
    },
    'pymongo': {
        'mock_available': True,
        'mock_class': 'MockMongoClient',
        'description': 'MongoDB client'
    }
}


class LazyImport:
    """Lazy import wrapper for optional modules."""

    def __init__(self, module_name: str, fallback: Optional[Any] = None):
        self.module_name = module_name
        self.fallback = fallback
        self._module = None
        self._loaded = False

    def __call__(self) -> Any:
        """Load the module on first access."""
        if not self._loaded:
            self._load_module()
        return self._module

    def _load_module(self):
        """Load the module with error handling."""
        try:
            self._module = importlib.import_module(self.module_name)
            self._loaded = True
            logger.debug(f"✅ Successfully imported {self.module_name}")
        except ImportError as e:
            if self.fallback is not None:
                logger.warning(f"⚠️ {self.module_name} not available, using fallback: {e}")
                self._module = self.fallback
            else:
                config = OPTIONAL_MODULES.get(self.module_name, {})
                if config.get('mock_available', False):
                    logger.warning(f"⚠️ {self.module_name} not available, using mock implementation: {e}")
                    self._module = self._create_mock()
                else:
                    logger.error(f"❌ {self.module_name} is required but not available: {e}")
                    raise
            self._loaded = True

    def _create_mock(self) -> Any:
        """Create a mock implementation for missing modules."""
        mock_class_name = OPTIONAL_MODULES.get(self.module_name, {}).get('mock_class', 'MockModule')
        description = OPTIONAL_MODULES.get(self.module_name, {}).get('description', self.module_name)

        class MockModule:
            """Mock implementation for missing modules."""

            def __init__(self, *args, **kwargs):
                self._module_name = self.module_name
                self._description = description
                logger.debug(f"🧪 Using mock implementation for {self._module_name}")

            def __getattr__(self, name):
                # Return mock functions/methods
                def mock_method(*args, **kwargs):
                    logger.debug(f"🧪 Mock {self._module_name}.{name} called with args={args}, kwargs={kwargs}")
                    return None
                return mock_method

            def __repr__(self):
                return f"<Mock {self._description} (module: {self._module_name})>"

        return MockModule()


def lazy_import(module_name: str, fallback: Optional[Any] = None) -> LazyImport:
    """Create a lazy import for an optional module."""
    return LazyImport(module_name, fallback)


def require_module(module_name: str, description: str = "") -> Any:
    """Require a module to be available, raise error if not."""
    try:
        module = importlib.import_module(module_name)
        logger.debug(f"✅ {description or module_name} available")
        return module
    except ImportError as e:
        logger.error(f"❌ {description or module_name} is required but not available: {e}")
        raise ImportError(f"Required module {module_name} not found: {e}")


# Specific lazy imports for common optional modules
flwr = lazy_import('flwr')
tensorflow = lazy_import('tensorflow')
kubernetes = lazy_import('kubernetes')
pymongo = lazy_import('pymongo')

ALLOW_MOCKS = os.getenv("AILOOS_ALLOW_MOCKS", "0") == "1"

# Critical modules that should not be mocked in production.
if ALLOW_MOCKS:
    torch = lazy_import('torch')
    transformers = lazy_import('transformers')
    numpy = lazy_import('numpy')
    pandas = lazy_import('pandas')
else:
    torch = require_module('torch', 'PyTorch ML framework')
    transformers = require_module('transformers', 'Hugging Face Transformers')
    numpy = require_module('numpy', 'NumPy scientific computing')
    pandas = require_module('pandas', 'Pandas data analysis')


class MockFlowerClient:
    """Mock Flower client for federated learning when flwr is not available."""

    def __init__(self, *args, **kwargs):
        logger.debug("🧪 Using MockFlowerClient - federated learning will be disabled")

    def start_numpy_client(self, *args, **kwargs):
        logger.warning("🧪 Federated learning disabled - flwr not available")
        return None


class MockKubernetesClient:
    """Mock Kubernetes client for development."""

    def __init__(self, *args, **kwargs):
        logger.debug("🧪 Using MockKubernetesClient - Kubernetes operations will be no-ops")

    def list_namespaced_pod(self, *args, **kwargs):
        return {'items': []}


class MockMongoClient:
    """Mock MongoDB client for development."""

    def __init__(self, *args, **kwargs):
        logger.debug("🧪 Using MockMongoClient - MongoDB operations will be no-ops")

    def __getitem__(self, key):
        return MockCollection()

    def close(self):
        pass


class MockCollection:
    """Mock MongoDB collection."""

    def find_one(self, *args, **kwargs):
        return None

    def insert_one(self, *args, **kwargs):
        return MockInsertResult()

    def update_one(self, *args, **kwargs):
        return MockUpdateResult()


class MockInsertResult:
    """Mock insert result."""
    inserted_id = "mock_id"


class MockUpdateResult:
    """Mock update result."""
    modified_count = 1


# Update the lazy imports with mock classes
flwr._fallback = MockFlowerClient
kubernetes._fallback = MockKubernetesClient
pymongo._fallback = MockMongoClient
