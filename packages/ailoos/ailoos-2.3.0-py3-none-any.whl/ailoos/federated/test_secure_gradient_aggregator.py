"""
Pruebas de seguridad y validación para SecureGradientAggregator
Verifica que la agregación segura funcione correctamente y mantenga la privacidad.
"""

import asyncio
import time
import unittest
from unittest.mock import Mock, patch
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List

from .secure_gradient_aggregator import (
    SecureGradientAggregator,
    SecureAggregationConfig,
    AggregationPhase,
    aggregate_gradients_secure
)


class TestSecureGradientAggregator(unittest.TestCase):
    """Pruebas unitarias para SecureGradientAggregator."""

    def setUp(self):
        """Configurar pruebas."""
        self.config = SecureAggregationConfig(
            session_id="test_session",
            min_participants=2,
            max_participants=10,
            dropout_threshold=0.3,
            enable_dropout_verification=True,
            enable_integrity_validation=True,
            enable_fault_recovery=True,
            batch_size=5
        )
        self.aggregator = SecureGradientAggregator(self.config)

    def tearDown(self):
        """Limpiar después de pruebas."""
        asyncio.run(self.aggregator.shutdown())

    def _create_test_gradients(self, node_id: str, num_layers: int = 3) -> Dict[str, torch.Tensor]:
        """Crear gradientes de prueba para un nodo."""
        gradients = {}
        for i in range(num_layers):
            layer_name = f"layer_{i}"
            # Gradientes con valores realistas
            gradients[layer_name] = torch.randn(10, 10) * 0.01
        return gradients

    def test_initialization(self):
        """Probar inicialización del agregador."""
        self.assertEqual(self.aggregator.phase, AggregationPhase.INITIALIZING)
        self.assertEqual(self.aggregator.config.session_id, "test_session")
        self.assertIsNotNone(self.aggregator.he_manager)
        self.assertIsNotNone(self.aggregator.encryptor)

    async def test_basic_aggregation(self):
        """Probar agregación básica con pocos nodos."""
        # Inicializar agregación
        node_ids = ["node_1", "node_2", "node_3"]
        success = await self.aggregator.initialize_aggregation(node_ids)
        self.assertTrue(success)
        self.assertEqual(self.aggregator.phase, AggregationPhase.COLLECTING_MASKS)

        # Enviar actualizaciones
        gradients_list = []
        for node_id in node_ids:
            gradients = self._create_test_gradients(node_id)
            gradients_list.append(gradients)

            accepted = await self.aggregator.submit_gradient_update(
                node_id=node_id,
                gradients=gradients,
                num_samples=100
            )
            self.assertTrue(accepted)

        # Esperar a que complete la agregación
        await asyncio.sleep(0.1)  # Dar tiempo para procesamiento asíncrono

        # Verificar que la agregación se completó
        self.assertEqual(self.aggregator.phase, AggregationPhase.COMPLETED)
        aggregated = self.aggregator.get_aggregated_gradients()
        self.assertIsNotNone(aggregated)

        # Verificar que el agregado tiene las capas correctas
        expected_layers = {f"layer_{i}" for i in range(3)}
        self.assertEqual(set(aggregated.keys()), expected_layers)

        # Verificar que los gradientes agregados son razonables
        for layer_name, grad_tensor in aggregated.items():
            self.assertIsInstance(grad_tensor, torch.Tensor)
            self.assertEqual(grad_tensor.shape, torch.Size([10, 10]))

    async def test_privacy_preservation(self):
        """Probar que los gradientes individuales no se pueden ver."""
        node_ids = ["node_1", "node_2"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Enviar actualización de un nodo
        gradients = self._create_test_gradients("node_1")
        await self.aggregator.submit_gradient_update("node_1", gradients, 100)

        # Verificar que los gradientes encriptados no revelan información
        update = self.aggregator.gradient_updates["node_1"]
        self.assertIsNotNone(update.encrypted_gradients)
        self.assertNotEqual(update.encrypted_gradients, gradients)  # Deben ser diferentes

        # Verificar que no se puede acceder a gradientes sin desencriptación
        # (esto es difícil de probar directamente sin acceso a claves privadas,
        # pero podemos verificar que están encriptados)
        for layer_name, encrypted_layer in update.encrypted_gradients.items():
            self.assertIsNotNone(encrypted_layer)
            self.assertIsInstance(encrypted_layer, list)

    async def test_secure_aggregation_properties(self):
        """Probar propiedades de secure aggregation."""
        node_ids = ["node_1", "node_2", "node_3"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Recopilar gradientes originales
        original_gradients = {}
        for node_id in node_ids:
            gradients = self._create_test_gradients(node_id)
            original_gradients[node_id] = gradients
            await self.aggregator.submit_gradient_update(node_id, gradients, 100)

        await asyncio.sleep(0.1)

        # Obtener resultado agregado
        aggregated = self.aggregator.get_aggregated_gradients()
        self.assertIsNotNone(aggregated)

        # Calcular agregado esperado manualmente
        expected_aggregated = {}
        for layer_name in original_gradients["node_1"].keys():
            layer_sum = torch.zeros_like(original_gradients["node_1"][layer_name])
            for node_id in node_ids:
                layer_sum += original_gradients[node_id][layer_name]
            expected_aggregated[layer_name] = layer_sum

        # Verificar que el agregado es correcto (aproximadamente)
        for layer_name in expected_aggregated.keys():
            diff = torch.abs(aggregated[layer_name] - expected_aggregated[layer_name])
            # Debe ser pequeño debido a las máscaras que se cancelan
            self.assertTrue(torch.mean(diff) < 0.1)

    async def test_dropout_verification(self):
        """Probar verificación de dropout."""
        # Configurar con threshold bajo para forzar fallo
        config = SecureAggregationConfig(
            session_id="test_dropout",
            min_participants=3,
            dropout_threshold=0.1,  # Solo 10% dropout permitido
            enable_dropout_verification=True
        )
        aggregator = SecureGradientAggregator(config)

        try:
            node_ids = ["node_1", "node_2", "node_3", "node_4", "node_5"]
            await aggregator.initialize_aggregation(node_ids)

            # Solo enviar 2 actualizaciones (60% dropout - debería fallar)
            for i in range(2):
                node_id = f"node_{i+1}"
                gradients = self._create_test_gradients(node_id)
                await aggregator.submit_gradient_update(node_id, gradients, 100)

            await asyncio.sleep(0.1)

            # Debería fallar por dropout alto
            self.assertEqual(aggregator.phase, AggregationPhase.FAILED)

        finally:
            await aggregator.shutdown()

    async def test_fault_recovery(self):
        """Probar recuperación automática de fallos."""
        # Mock de callback de recuperación
        recovery_called = []
        self.aggregator.on_node_recovery = lambda node_id: recovery_called.append(node_id)

        node_ids = ["node_1", "node_2", "node_3"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Simular fallo de nodo
        self.aggregator._handle_node_failure("node_2", "connection_lost")

        # Esperar recuperación
        await asyncio.sleep(2)

        # Verificar que se intentó recuperación
        self.assertIn("node_2", self.aggregator.recovered_nodes)
        self.assertEqual(len(recovery_called), 1)
        self.assertEqual(recovery_called[0], "node_2")

    async def test_integrity_validation(self):
        """Probar validación de integridad."""
        node_ids = ["node_1", "node_2"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Enviar actualización válida
        gradients = self._create_test_gradients("node_1")
        accepted = await self.aggregator.submit_gradient_update("node_1", gradients, 100)
        self.assertTrue(accepted)

        # Intentar enviar actualización con integridad comprometida
        # (simular manipulando el hash)
        gradients2 = self._create_test_gradients("node_2")
        with patch.object(self.aggregator, '_compute_mask_hash', return_value="wrong_hash"):
            accepted = await self.aggregator.submit_gradient_update("node_2", gradients2, 100)
            self.assertFalse(accepted)  # Debería rechazarse

    async def test_scalability(self):
        """Probar escalabilidad con muchos nodos."""
        num_nodes = 20  # Simular 20 nodos
        node_ids = [f"node_{i}" for i in range(num_nodes)]

        config = SecureAggregationConfig(
            session_id="test_scalability",
            min_participants=num_nodes,
            batch_size=10  # Procesamiento por lotes
        )
        aggregator = SecureGradientAggregator(config)

        try:
            await aggregator.initialize_aggregation(node_ids)

            start_time = time.time()

            # Enviar actualizaciones concurrentemente
            tasks = []
            for node_id in node_ids:
                gradients = self._create_test_gradients(node_id, num_layers=2)  # Menos capas para velocidad
                task = aggregator.submit_gradient_update(node_id, gradients, 50)
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Esperar agregación
            timeout = 10  # segundos
            start_wait = time.time()
            while aggregator.phase != AggregationPhase.COMPLETED and (time.time() - start_wait) < timeout:
                await asyncio.sleep(0.1)

            end_time = time.time()

            # Verificar que se completó
            self.assertEqual(aggregator.phase, AggregationPhase.COMPLETED)

            # Verificar métricas de rendimiento
            metrics = aggregator.get_metrics()
            self.assertEqual(metrics["aggregation_metrics"]["active_nodes"], num_nodes)
            self.assertGreater(metrics["aggregation_metrics"]["throughput_nodes_per_second"], 0)

            processing_time = end_time - start_time
            self.assertLess(processing_time, 30)  # Debería ser razonablemente rápido

        finally:
            await aggregator.shutdown()

    async def test_metrics_and_logging(self):
        """Probar recopilación de métricas y logging."""
        node_ids = ["node_1", "node_2"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Enviar actualizaciones
        for node_id in node_ids:
            gradients = self._create_test_gradients(node_id)
            await self.aggregator.submit_gradient_update(node_id, gradients, 100)

        await asyncio.sleep(0.1)

        # Verificar métricas
        metrics = self.aggregator.get_metrics()
        self.assertIn("aggregation_metrics", metrics)
        self.assertIn("efficiency", metrics)
        self.assertEqual(metrics["aggregation_metrics"]["active_nodes"], 2)

        # Verificar logs
        logs = self.aggregator.get_logs()
        self.assertGreater(len(logs), 0)

        # Verificar que hay eventos importantes
        event_types = {log["event_type"] for log in logs}
        self.assertIn("aggregation_initialized", event_types)
        self.assertIn("gradient_update_received", event_types)
        self.assertIn("aggregation_completed", event_types)

    def test_status_reporting(self):
        """Probar reporte de estado."""
        status = self.aggregator.get_aggregation_status()
        expected_keys = ["session_id", "phase", "total_nodes", "active_nodes",
                        "failed_nodes", "progress", "is_complete"]
        for key in expected_keys:
            self.assertIn(key, status)

    async def test_convenience_function(self):
        """Probar función de conveniencia aggregate_gradients_secure."""
        # Preparar datos de prueba
        gradient_updates = []
        for i in range(3):
            node_id = f"node_{i}"
            gradients = self._create_test_gradients(node_id)
            gradient_updates.append((node_id, gradients, 100))

        # Ejecutar agregación
        result = await aggregate_gradients_secure(self.aggregator, gradient_updates)

        # Verificar resultado
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    async def test_error_handling(self):
        """Probar manejo de errores."""
        # Intentar inicializar con nodos vacíos
        success = await self.aggregator.initialize_aggregation([])
        self.assertFalse(success)

        # Intentar enviar actualización sin inicializar
        gradients = self._create_test_gradients("node_1")
        accepted = await self.aggregator.submit_gradient_update("node_1", gradients, 100)
        self.assertFalse(accepted)

    async def test_timeout_behavior(self):
        """Probar comportamiento con timeout."""
        config = SecureAggregationConfig(
            session_id="test_timeout",
            timeout_seconds=1,  # Timeout muy corto
            min_participants=5
        )
        aggregator = SecureGradientAggregator(config)

        try:
            node_ids = ["node_1", "node_2", "node_3", "node_4", "node_5"]
            await aggregator.initialize_aggregation(node_ids)

            # Solo enviar 2 actualizaciones (menos del mínimo)
            for i in range(2):
                gradients = self._create_test_gradients(f"node_{i+1}")
                await aggregator.submit_gradient_update(f"node_{i+1}", gradients, 100)

            # Esperar más que el timeout
            await asyncio.sleep(2)

            # La agregación no debería completarse
            status = aggregator.get_aggregation_status()
            self.assertNotEqual(status["phase"], "completed")

        finally:
            await aggregator.shutdown()


class TestSecurityProperties(unittest.TestCase):
    """Pruebas específicas de propiedades de seguridad."""

    def setUp(self):
        self.config = SecureAggregationConfig(session_id="security_test")
        self.aggregator = SecureGradientAggregator(self.config)

    def tearDown(self):
        asyncio.run(self.aggregator.shutdown())

    async def test_mask_cancellation(self):
        """Probar que las máscaras se cancelan correctamente."""
        node_ids = ["node_1", "node_2"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Gradientes simples para verificación
        gradients1 = {"layer1": torch.tensor([[1.0, 2.0], [3.0, 4.0]])}
        gradients2 = {"layer1": torch.tensor([[0.5, 1.5], [2.5, 3.5]])}

        await self.aggregator.submit_gradient_update("node_1", gradients1, 100)
        await self.aggregator.submit_gradient_update("node_2", gradients2, 100)

        await asyncio.sleep(0.1)

        aggregated = self.aggregator.get_aggregated_gradients()
        self.assertIsNotNone(aggregated)

        # El resultado debería ser aproximadamente la suma de los gradientes originales
        expected = gradients1["layer1"] + gradients2["layer1"]
        diff = torch.abs(aggregated["layer1"] - expected)
        self.assertTrue(torch.max(diff) < 0.01)  # Muy pequeña diferencia debido a precisión

    async def test_no_information_leakage(self):
        """Probar que no se filtra información de gradientes individuales."""
        node_ids = ["node_1", "node_2", "node_3"]
        await self.aggregator.initialize_aggregation(node_ids)

        # Gradientes con patrón reconocible
        special_gradient = torch.ones(5, 5) * 999  # Valor muy distintivo
        normal_gradients = torch.randn(5, 5) * 0.01

        gradients = {
            "node_1": {"layer1": special_gradient},
            "node_2": {"layer1": normal_gradients},
            "node_3": {"layer1": normal_gradients}
        }

        for node_id, grads in gradients.items():
            await self.aggregator.submit_gradient_update(node_id, grads, 100)

        await asyncio.sleep(0.1)

        aggregated = self.aggregator.get_aggregated_gradients()
        self.assertIsNotNone(aggregated)

        # Verificar que el gradiente especial no es visible directamente
        # (está enmascarado y mezclado con otros)
        result = aggregated["layer1"]
        self.assertFalse(torch.allclose(result, special_gradient))  # No debería ser igual
        self.assertFalse(torch.allclose(result, normal_gradients * 2 + special_gradient))  # No la suma simple


if __name__ == "__main__":
    # Configurar para pruebas asíncronas
    import sys

    # Ejecutar pruebas
    unittest.main()