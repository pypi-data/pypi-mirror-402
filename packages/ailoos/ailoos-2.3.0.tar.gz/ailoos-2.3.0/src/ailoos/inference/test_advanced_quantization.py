"""
Pruebas para el sistema avanzado de cuantización de EmpoorioLM.
"""

import torch
import torch.nn as nn
import unittest
from torch.utils.data import DataLoader, TensorDataset
import tempfile
import os
from pathlib import Path

from .quantization import (
    AdvancedQuantizer,
    DynamicCalibration,
    PerformanceMonitor,
    AdaptiveQuantization,
    FederatedQuantization,
    QuantizationAwareTraining,
    QuantizationConfig,
    FakeQuantLinear
)


class TestAdvancedQuantization(unittest.TestCase):
    """Pruebas unitarias para el sistema de cuantización avanzada."""

    def setUp(self):
        """Configurar pruebas."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Crear modelo dummy para pruebas
        self.dummy_model = self._create_dummy_model()

        # Crear datos de prueba
        self.test_data = self._create_test_data()

    def _create_dummy_model(self):
        """Crear modelo dummy para pruebas."""
        class DummyEmpoorioLM(nn.Module):
            def __init__(self):
                super().__init__()
                self.embed_tokens = nn.Embedding(1000, 512)
                self.layers = nn.ModuleList([
                    nn.ModuleDict({
                        "self_attn": nn.Linear(512, 512),
                        "mlp": nn.Linear(512, 2048)
                    }) for _ in range(2)
                ])
                self.norm = nn.LayerNorm(512)
                self.lm_head = nn.Linear(512, 1000)

            def forward(self, input_ids, **kwargs):
                x = self.embed_tokens(input_ids)
                for layer in self.layers:
                    x = layer["self_attn"](x)
                    x = layer["mlp"](x)
                x = self.norm(x)
                return self.lm_head(x)

            @classmethod
            def from_pretrained(cls, path):
                return cls()

            def save_pretrained(self, path):
                pass

            def to(self, device):
                return super().to(device)

        return DummyEmpoorioLM()

    def _create_test_data(self):
        """Crear datos de prueba."""
        # Datos dummy
        input_ids = torch.randint(0, 1000, (100, 50))
        labels = torch.randint(0, 1000, (100, 50))
        dataset = TensorDataset(input_ids, labels)
        return DataLoader(dataset, batch_size=8)

    def test_dynamic_calibration(self):
        """Probar calibración dinámica."""
        calibrator = DynamicCalibration()

        # Recopilar datos
        calibrator.collect_calibration_data(self.dummy_model, self.test_data)

        # Verificar que se recopilaron datos
        self.assertGreater(len(calibrator.activation_ranges), 0)

        # Obtener configuración óptima
        config = calibrator.get_optimal_quantization_config()
        self.assertIsInstance(config, dict)

    def test_performance_monitor(self):
        """Probar monitoreo de rendimiento."""
        monitor = PerformanceMonitor()

        # Medir rendimiento
        metrics = monitor.measure_inference_performance(
            self.dummy_model, self.test_data, None, num_runs=2
        )

        # Verificar métricas
        self.assertIn("avg_latency", metrics)
        self.assertIn("avg_throughput", metrics)
        self.assertGreater(metrics["avg_latency"], 0)
        self.assertGreater(metrics["avg_throughput"], 0)

    def test_adaptive_quantization(self):
        """Probar cuantización adaptativa."""
        config = QuantizationConfig()
        adapter = AdaptiveQuantization(config)

        # Simular carga de trabajo
        workload = {"requests_per_second": 50, "cpu_usage": 70}
        perf_metrics = {"avg_similarity": 0.9}

        # Adaptar cuantización
        new_config = adapter.adapt_quantization(
            self.dummy_model, workload, perf_metrics
        )

        self.assertIsInstance(new_config, dict)
        self.assertGreater(len(new_config), 0)

    def test_federated_quantization(self):
        """Probar cuantización federada."""
        fed_quant = FederatedQuantization()

        # Crear configuración para nodos
        configs = fed_quant.create_federated_quantization_config(3, heterogeneous_nodes=True)

        self.assertEqual(len(configs), 3)
        for node_config in configs.values():
            self.assertIsInstance(node_config, QuantizationConfig)

        # Probar agregación
        dummy_updates = [
            {"layer1": torch.randn(10, 10), "layer2": torch.randn(5, 5)},
            {"layer1": torch.randn(10, 10), "layer2": torch.randn(5, 5)},
            {"layer1": torch.randn(10, 10), "layer2": torch.randn(5, 5)}
        ]

        aggregated = fed_quant.aggregate_quantized_updates(dummy_updates)
        self.assertIn("layer1", aggregated)
        self.assertIn("layer2", aggregated)

    def test_fake_quant_linear(self):
        """Probar capa FakeQuantLinear."""
        layer = FakeQuantLinear(512, 256, quantization_type="int8")

        # Forward pass
        x = torch.randn(4, 512)
        output = layer(x)

        self.assertEqual(output.shape, (4, 256))

        # Obtener pesos cuantizados
        quantized_weights = layer.get_quantized_weight()
        self.assertEqual(quantized_weights.shape, layer.weight.shape)

    def test_quantization_config(self):
        """Probar configuración de cuantización."""
        config = QuantizationConfig(
            quantization_type="mixed",
            calibration_samples=2000,
            adaptive_threshold=0.9
        )

        self.assertEqual(config.quantization_type, "mixed")
        self.assertEqual(config.calibration_samples, 2000)
        self.assertEqual(config.adaptive_threshold, 0.9)

    def test_advanced_quantizer_initialization(self):
        """Probar inicialización del cuantizador avanzado."""
        config = QuantizationConfig()
        quantizer = AdvancedQuantizer(config)

        self.assertIsNotNone(quantizer.dynamic_calibration)
        self.assertIsNotNone(quantizer.performance_monitor)
        self.assertIsNotNone(quantizer.adaptive_quantization)
        self.assertEqual(quantizer.config, config)


class TestIntegration(unittest.TestCase):
    """Pruebas de integración del sistema completo."""

    def test_full_pipeline(self):
        """Probar pipeline completo (simulado)."""
        config = QuantizationConfig(
            quantization_type="int8",
            calibration_samples=100
        )

        # Crear componentes
        quantizer = AdvancedQuantizer(config)
        fed_quant = FederatedQuantization()
        qat = QuantizationAwareTraining(config)

        # Verificar que todos los componentes se inicializan correctamente
        self.assertIsNotNone(quantizer)
        self.assertIsNotNone(fed_quant)
        self.assertIsNotNone(qat)

        # Probar configuración federada
        fed_configs = fed_quant.create_federated_quantization_config(2)
        self.assertEqual(len(fed_configs), 2)


if __name__ == "__main__":
    # Ejecutar pruebas
    unittest.main(verbosity=2)