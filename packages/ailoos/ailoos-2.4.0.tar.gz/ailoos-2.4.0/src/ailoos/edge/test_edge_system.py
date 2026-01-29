"""
Pruebas unitarias y de integración para el sistema de edge computing.

Cubre componentes individuales y integración completa del sistema edge.
"""

import unittest
import tempfile
import shutil
import time
import torch
import torch.nn as nn
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

from .edge_model_optimizer import EdgeModelOptimizer, EdgeDeviceCapabilities, EdgeDeviceType, EdgeOptimizationConfig
from .lightweight_runtime import LightweightRuntime, LightweightRuntimeConfig
from .edge_synchronization import EdgeSynchronization, EdgeSynchronizationConfig
from .resource_manager import ResourceManager, ResourceManagerConfig
from .offline_capabilities import OfflineCapabilities, OfflineCapabilitiesConfig
from .edge_federated_learning import EdgeFederatedLearning, EdgeFLConfig
from .edge_integration import EdgeSystem, EdgeSystemConfig


class TestEdgeModelOptimizer(unittest.TestCase):
    """Pruebas para EdgeModelOptimizer."""

    def setUp(self):
        self.config = EdgeOptimizationConfig(
            target_device_type=EdgeDeviceType.MOBILE_PHONE,
            max_memory_usage_mb=512
        )
        self.optimizer = EdgeModelOptimizer(self.config)

    def test_initialization(self):
        """Probar inicialización del optimizador."""
        self.assertIsInstance(self.optimizer, EdgeModelOptimizer)
        self.assertEqual(self.optimizer.config.target_device_type, EdgeDeviceType.MOBILE_PHONE)

    def test_device_capabilities_creation(self):
        """Probar creación de capacidades de dispositivo."""
        caps = EdgeDeviceCapabilities(
            device_type=EdgeDeviceType.MOBILE_PHONE,
            cpu_cores=8,
            total_memory_mb=4096,
            supports_fp16=True
        )
        self.assertEqual(caps.device_type, EdgeDeviceType.MOBILE_PHONE)
        self.assertEqual(caps.cpu_cores, 8)

    def test_optimization_profile_creation(self):
        """Probar creación de perfil de optimización."""
        caps = EdgeDeviceCapabilities(
            device_type=EdgeDeviceType.MOBILE_PHONE,
            cpu_cores=8,
            total_memory_mb=4096
        )

        # Crear modelo dummy
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save({"dummy": "model"}, f.name)
            model_path = f.name

        try:
            profile = self.optimizer.optimize_model_for_edge(model_path, caps)
            self.assertIsNotNone(profile)
            self.assertGreater(profile.efficiency_score, 0)
        finally:
            Path(model_path).unlink(missing_ok=True)


class TestLightweightRuntime(unittest.TestCase):
    """Pruebas para LightweightRuntime."""

    def setUp(self):
        self.config = LightweightRuntimeConfig(
            max_memory_usage_mb=256,
            max_concurrent_requests=2
        )
        self.runtime = LightweightRuntime(self.config)

    def test_initialization(self):
        """Probar inicialización del runtime."""
        self.assertIsInstance(self.runtime, LightweightRuntime)
        self.assertFalse(self.runtime.is_running)

    def test_start_stop(self):
        """Probar inicio y detención del runtime."""
        self.runtime.start()
        self.assertTrue(self.runtime.is_running)

        self.runtime.stop()
        self.assertFalse(self.runtime.is_running)

    def test_model_loading(self):
        """Probar carga de modelo."""
        # Crear archivo dummy
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save({"dummy": "model"}, f.name)
            model_path = f.name

        try:
            success = self.runtime.load_model(model_path, "test_model")
            self.assertTrue(success)

            models = self.runtime.get_loaded_models()
            self.assertIn("test_model", models)
        finally:
            Path(model_path).unlink(missing_ok=True)


class TestResourceManager(unittest.TestCase):
    """Pruebas para ResourceManager."""

    def setUp(self):
        self.config = ResourceManagerConfig(
            max_concurrent_tasks=2,
            enable_resource_monitoring=False  # Deshabilitar para pruebas
        )
        self.manager = ResourceManager(self.config)

    def test_initialization(self):
        """Probar inicialización del ResourceManager."""
        self.assertIsInstance(self.manager, ResourceManager)
        self.assertFalse(self.manager.is_running)

    def test_task_registration(self):
        """Probar registro de tareas."""
        from .resource_manager import ResourceType

        success = self.manager.register_task(
            task_id="test_task",
            name="Test Task",
            priority=self.manager.TaskPriority.NORMAL,
            resource_requirements={ResourceType.CPU: 20.0}
        )
        self.assertTrue(success)

        # Verificar que está registrado
        self.assertIn("test_task", self.manager.managed_tasks)

    def test_resource_status(self):
        """Probar obtención de estado de recursos."""
        status = self.manager.get_resource_status()
        self.assertIsInstance(status, dict)
        self.assertIn("current_usage", status)
        self.assertIn("active_tasks", status)


class TestOfflineCapabilities(unittest.TestCase):
    """Pruebas para OfflineCapabilities."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = OfflineCapabilitiesConfig(
            storage_path=self.temp_dir,
            max_storage_mb=50,
            enable_offline_monitoring=False  # Deshabilitar para pruebas
        )
        self.offline = OfflineCapabilities(self.config)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Probar inicialización de OfflineCapabilities."""
        self.assertIsInstance(self.offline, OfflineCapabilities)
        self.assertFalse(self.offline.is_running)

    def test_operation_queueing(self):
        """Probar encolado de operaciones."""
        from .offline_capabilities import OfflineOperation

        op_id = self.offline.queue_operation(
            operation_type=OfflineOperation.INFERENCE,
            data={"input": "test"}
        )

        self.assertNotEqual(op_id, "")
        self.assertTrue(len(op_id) > 0)

    def test_offline_status(self):
        """Probar obtención de estado offline."""
        status = self.offline.get_offline_status()
        self.assertIsInstance(status, dict)
        self.assertIn("connectivity_state", status)
        self.assertIn("pending_operations", status)


class TestEdgeSynchronization(unittest.TestCase):
    """Pruebas para EdgeSynchronization."""

    def setUp(self):
        self.config = EdgeSynchronizationConfig(
            central_node_url="http://test.example.com",
            device_id="test_device",
            enable_sync_monitoring=False  # Deshabilitar para pruebas
        )
        self.sync = EdgeSynchronization(self.config)

    @patch('src.ailoos.edge.edge_synchronization.requests.post')
    def test_metrics_sync(self, mock_post):
        """Probar sincronización de métricas."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}

        task_id = self.sync.sync_metrics({"test": "data"})
        self.assertNotEqual(task_id, "")

    def test_sync_status(self):
        """Probar obtención de estado de sincronización."""
        status = self.sync.get_sync_status()
        self.assertIsInstance(status, dict)
        self.assertIn("connection_state", status)
        self.assertIn("buffered_tasks", status)


class TestEdgeFederatedLearning(unittest.TestCase):
    """Pruebas para EdgeFederatedLearning."""

    def setUp(self):
        self.config = EdgeFLConfig(
            local_epochs=1,
            batch_size=4,
            max_training_time_seconds=10
        )
        self.fl = EdgeFederatedLearning("test_device", self.config)

    def test_initialization(self):
        """Probar inicialización de EdgeFederatedLearning."""
        self.assertIsInstance(self.fl, EdgeFederatedLearning)
        self.assertEqual(self.fl.device_id, "test_device")

    def test_model_setting(self):
        """Probar establecimiento de modelo global."""
        # Crear modelo dummy
        model = nn.Linear(10, 2)
        self.fl.set_global_model(model, "v1.0")

        self.assertIsNotNone(self.fl.global_model)
        self.assertIsNotNone(self.fl.local_model)

    def test_fl_status(self):
        """Probar obtención de estado FL."""
        status = self.fl.get_fl_status()
        self.assertIsInstance(status, dict)
        self.assertIn("device_id", status)
        self.assertIn("current_state", status)


class TestEdgeSystemIntegration(unittest.TestCase):
    """Pruebas de integración para EdgeSystem."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = EdgeSystemConfig(
            device_id="test_integration",
            device_type=EdgeDeviceType.MOBILE_PHONE,
            central_node_url="http://test.example.com",
            model_storage_path=f"{self.temp_dir}/models",
            offline_storage_path=f"{self.temp_dir}/offline",
            resource_cache_path=f"{self.temp_dir}/cache"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_system_initialization(self):
        """Probar inicialización completa del sistema."""
        system = EdgeSystem(self.config)

        self.assertIsInstance(system, EdgeSystem)
        self.assertIsNotNone(system.resource_manager)
        self.assertIsNotNone(system.offline_capabilities)
        self.assertIsNotNone(system.edge_sync)
        self.assertIsNotNone(system.runtime)
        self.assertIsNotNone(system.model_optimizer)

    def test_system_status(self):
        """Probar obtención de estado del sistema."""
        system = EdgeSystem(self.config)
        status = system.get_system_status()

        self.assertIsInstance(status, dict)
        self.assertIn("device_id", status)
        self.assertIn("is_running", status)
        self.assertIn("resource_status", status)

    @patch('src.ailoos.edge.edge_synchronization.requests.post')
    def test_system_sync(self, mock_post):
        """Probar sincronización del sistema."""
        mock_post.return_value.status_code = 200

        system = EdgeSystem(self.config)
        sync_id = system.sync_system_status()

        self.assertNotEqual(sync_id, "")


class TestConvenienceFunctions(unittest.TestCase):
    """Pruebas para funciones de conveniencia."""

    def test_mobile_system_creation(self):
        """Probar creación de sistema móvil."""
        from .edge_integration import create_mobile_edge_system

        with patch('src.ailoos.edge.edge_integration.Path.mkdir'):
            system = create_mobile_edge_system(
                device_id="mobile_test",
                central_url="http://test.com"
            )

        self.assertIsInstance(system, EdgeSystem)
        self.assertEqual(system.config.device_type, EdgeDeviceType.MOBILE_PHONE)

    def test_iot_system_creation(self):
        """Probar creación de sistema IoT."""
        from .edge_integration import create_iot_edge_system

        with patch('src.ailoos.edge.edge_integration.Path.mkdir'):
            system = create_iot_edge_system(
                device_id="iot_test",
                central_url="http://test.com"
            )

        self.assertIsInstance(system, EdgeSystem)
        self.assertEqual(system.config.device_type, EdgeDeviceType.IOT_DEVICE)


if __name__ == '__main__':
    # Configurar logging para pruebas
    import logging
    logging.basicConfig(level=logging.WARNING)

    # Ejecutar pruebas
    unittest.main(verbosity=2)