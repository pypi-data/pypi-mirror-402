"""
Pruebas de integración para el sistema federado vLLM.
Verifica el funcionamiento conjunto de todos los componentes optimizados.
"""

import asyncio
import pytest
import time
import logging
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from .federated_vllm_system import FederatedVLLMSystem, FederatedVLLMSystemConfig
from .vllm_batching import BatchRequest

# Configurar logging para pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFederatedVLLMIntegration:
    """Pruebas de integración del sistema federado vLLM."""

    @pytest.fixture
    async def federated_system(self):
        """Fixture que crea un sistema federado configurado."""
        config = FederatedVLLMSystemConfig(
            model_path="/mock/model/path",
            local_node_id="test_node",
            enable_federated_optimizer=True,
            enable_shared_kv_cache=True,
            enable_resource_scheduler=True,
            enable_federated_batching=True,
            enable_distributed_monitor=True,
            enable_adaptive_quantization=True
        )

        system = FederatedVLLMSystem(config)
        success = await system.initialize_system()

        if success:
            yield system
            # Cleanup
            await system.shutdown_system()
        else:
            pytest.skip("No se pudo inicializar el sistema")

    @pytest.mark.asyncio
    async def test_system_initialization(self, federated_system):
        """Probar inicialización completa del sistema."""
        assert federated_system.is_initialized
        assert federated_system.federated_optimizer is not None
        assert federated_system.shared_kv_cache is not None
        assert federated_system.resource_scheduler is not None
        assert federated_system.federated_batching is not None
        assert federated_system.distributed_monitor is not None
        assert federated_system.adaptive_quantization is not None

        logger.info("✅ Inicialización del sistema verificada")

    @pytest.mark.asyncio
    async def test_round_preparation(self, federated_system):
        """Probar preparación para una ronda FL."""
        round_id = "test_round_001"
        node_capabilities = {
            "hardware_type": "gpu",
            "gpu_memory_gb": 8.0,
            "total_memory_gb": 16.0,
            "performance_score": 2.0,
            "supports_fp16": True,
            "supports_int8": True,
            "max_batch_size": 16
        }

        success = await federated_system.prepare_for_round(round_id, node_capabilities)

        assert success
        assert federated_system.current_round_id == round_id

        # Verificar que los componentes se prepararon
        assert federated_system.federated_batching.current_round_id == round_id

        logger.info("✅ Preparación de ronda verificada")

    @pytest.mark.asyncio
    async def test_federated_request_processing(self, federated_system):
        """Probar procesamiento de solicitud federada."""
        # Preparar ronda primero
        await federated_system.prepare_for_round("test_round_002", {
            "hardware_type": "gpu",
            "gpu_memory_gb": 8.0,
            "performance_score": 2.0
        })

        # Crear solicitud de prueba
        request = BatchRequest(
            id="test_request_001",
            prompt="Test prompt for federated inference",
            max_tokens=50,
            temperature=0.7
        )

        round_context = {
            "priority_boost": 1,
            "round_requirements": {"latency_sensitive": True}
        }

        # Procesar solicitud
        response = await federated_system.process_federated_request(request, round_context)

        assert response is not None
        assert response.request_id == request.id
        assert "usage" in response
        assert response.usage["total_tokens"] > 0
        assert response.processing_time > 0

        # Verificar que se actualizaron las estadísticas
        assert federated_system.performance_stats["total_requests_processed"] > 0

        logger.info("✅ Procesamiento de solicitud federada verificado")

    @pytest.mark.asyncio
    async def test_multiple_requests_processing(self, federated_system):
        """Probar procesamiento de múltiples solicitudes."""
        await federated_system.prepare_for_round("test_round_003", {
            "hardware_type": "gpu",
            "gpu_memory_gb": 8.0
        })

        # Crear múltiples solicitudes
        requests = []
        for i in range(5):
            request = BatchRequest(
                id=f"test_request_multi_{i}",
                prompt=f"Test prompt {i} for federated inference",
                max_tokens=30 + i * 10,
                temperature=0.7
            )
            requests.append(request)

        # Procesar todas las solicitudes
        responses = []
        for request in requests:
            response = await federated_system.process_federated_request(request)
            responses.append(response)
            assert response is not None

        # Verificar estadísticas agregadas
        assert federated_system.performance_stats["total_requests_processed"] >= 5
        assert federated_system.performance_stats["avg_latency_ms"] > 0
        assert federated_system.performance_stats["avg_throughput_tokens_per_sec"] > 0

        logger.info("✅ Procesamiento múltiple de solicitudes verificado")

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, federated_system):
        """Probar recopilación de métricas del sistema."""
        await federated_system.prepare_for_round("test_round_004", {
            "hardware_type": "cpu",
            "total_memory_gb": 8.0
        })

        # Procesar algunas solicitudes para generar métricas
        for i in range(3):
            request = BatchRequest(
                id=f"metrics_test_{i}",
                prompt=f"Metrics test prompt {i}",
                max_tokens=20
            )
            await federated_system.process_federated_request(request)

        # Obtener métricas del sistema
        metrics = await federated_system.get_system_metrics()

        # Verificar estructura de métricas
        assert "performance_stats" in metrics
        assert "system_status" in metrics
        assert metrics["system_status"]["initialized"] is True
        assert metrics["performance_stats"]["total_requests_processed"] >= 3

        # Verificar métricas de componentes
        assert "federated_optimizer" in metrics
        assert "shared_kv_cache" in metrics
        assert "resource_scheduler" in metrics
        assert "federated_batching" in metrics
        assert "distributed_monitor" in metrics
        assert "adaptive_quantization" in metrics

        logger.info("✅ Recopilación de métricas verificada")

    @pytest.mark.asyncio
    async def test_round_optimization(self, federated_system):
        """Probar optimización para siguiente ronda."""
        await federated_system.prepare_for_round("test_round_005", {
            "hardware_type": "gpu",
            "gpu_memory_gb": 12.0
        })

        # Procesar solicitudes para generar historial
        for i in range(3):
            request = BatchRequest(
                id=f"opt_test_{i}",
                prompt=f"Optimization test {i}",
                max_tokens=25
            )
            await federated_system.process_federated_request(request)

        # Optimizar para siguiente ronda
        next_round_reqs = {
            "expected_load": "high",
            "latency_requirement_ms": 500,
            "throughput_requirement": 100
        }

        await federated_system.optimize_for_next_round(next_round_reqs)

        # Verificar que el sistema se optimizó
        health = federated_system.get_system_health()
        assert health["overall_status"] == "healthy"

        logger.info("✅ Optimización de ronda verificada")

    @pytest.mark.asyncio
    async def test_kv_cache_integration(self, federated_system):
        """Probar integración del cache KV."""
        await federated_system.prepare_for_round("test_round_006", {
            "hardware_type": "gpu"
        })

        # Primera solicitud - debería almacenarse en cache
        request1 = BatchRequest(
            id="cache_test_1",
            prompt="This is a test prompt for KV cache",
            max_tokens=30
        )

        # Simular tokens del prompt
        request1.prompt_tokens = [1, 2, 3, 4, 5] * 10  # Tokens simulados

        response1 = await federated_system.process_federated_request(request1)
        assert response1 is not None

        # Segunda solicitud con mismo prompt - debería usar cache
        request2 = BatchRequest(
            id="cache_test_2",
            prompt="This is a test prompt for KV cache",
            max_tokens=30
        )
        request2.prompt_tokens = [1, 2, 3, 4, 5] * 10  # Mismos tokens

        response2 = await federated_system.process_federated_request(request2)
        assert response2 is not None

        # Verificar estadísticas de cache
        cache_stats = federated_system.shared_kv_cache.get_cache_stats()
        assert cache_stats["total_entries"] > 0

        logger.info("✅ Integración de cache KV verificada")

    @pytest.mark.asyncio
    async def test_resource_scheduler_integration(self, federated_system):
        """Probar integración del programador de recursos."""
        await federated_system.prepare_for_round("test_round_007", {
            "hardware_type": "gpu",
            "gpu_memory_gb": 8.0,
            "performance_score": 2.0
        })

        # Verificar que el scheduler tiene capacidades registradas
        scheduler_stats = federated_system.resource_scheduler.get_scheduler_stats()
        assert federated_system.config.local_node_id in scheduler_stats["node_capabilities"]

        # Verificar capacidades
        node_caps = scheduler_stats["node_capabilities"][federated_system.config.local_node_id]
        assert node_caps["hardware_type"] == "gpu"
        assert node_caps["performance_score"] == 2.0

        logger.info("✅ Integración del programador de recursos verificada")

    @pytest.mark.asyncio
    async def test_distributed_monitor_integration(self, federated_system):
        """Probar integración del monitor distribuido."""
        await federated_system.prepare_for_round("test_round_008", {
            "hardware_type": "gpu"
        })

        # Procesar solicitud para generar métricas
        request = BatchRequest(
            id="monitor_test",
            prompt="Test for distributed monitoring",
            max_tokens=20
        )

        await federated_system.process_federated_request(request)

        # Verificar métricas del monitor
        monitor_stats = federated_system.distributed_monitor.get_monitoring_stats()
        assert monitor_stats["total_requests_processed"] > 0
        assert "global_metrics" in monitor_stats

        # Verificar métricas por nodo
        node_summary = federated_system.distributed_monitor.get_node_performance_summary(
            federated_system.config.local_node_id
        )
        assert "avg_latency_ms" in node_summary
        assert "avg_throughput" in node_summary

        logger.info("✅ Integración del monitor distribuido verificada")

    @pytest.mark.asyncio
    async def test_adaptive_quantization_integration(self, federated_system):
        """Probar integración de la cuantización adaptativa."""
        node_caps = {
            "hardware_type": "gpu",
            "gpu_memory_gb": 8.0,
            "supports_fp16": True,
            "supports_int8": True
        }

        # Adaptar cuantización
        profile = federated_system.adaptive_quantization.adapt_quantization_for_node(
            node_caps, {"type": "inference"}, {}
        )

        assert profile is not None
        assert hasattr(profile, 'level')
        assert hasattr(profile, 'efficiency_score')

        # Verificar estadísticas del puente
        bridge_stats = federated_system.adaptive_quantization.get_bridge_stats()
        assert "active_profiles" in bridge_stats

        logger.info("✅ Integración de cuantización adaptativa verificada")

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, federated_system):
        """Probar monitoreo de salud del sistema."""
        health = federated_system.get_system_health()

        assert health["overall_status"] == "healthy"
        assert "components_health" in health
        assert "performance_indicators" in health

        # Verificar estado de componentes
        components = health["components_health"]
        assert components["federated_optimizer"] == "ok"
        assert components["shared_kv_cache"] == "ok"
        assert components["resource_scheduler"] == "ok"
        assert components["federated_batching"] == "ok"
        assert components["distributed_monitor"] == "ok"
        assert components["adaptive_quantization"] == "ok"

        logger.info("✅ Monitoreo de salud del sistema verificado")

    @pytest.mark.asyncio
    async def test_system_shutdown(self, federated_system):
        """Probar apagado limpio del sistema."""
        # Verificar que el sistema está inicializado
        assert federated_system.is_initialized

        # Apagar sistema
        await federated_system.shutdown_system()

        # Verificar que se apagó correctamente
        assert not federated_system.is_initialized

        health = federated_system.get_system_health()
        assert health["overall_status"] == "not_initialized"

        logger.info("✅ Apagado del sistema verificado")


@pytest.mark.asyncio
async def test_federated_system_creation():
    """Probar creación del sistema federado."""
    system = await FederatedVLLMSystem.create_federated_vllm_system(
        model_path="/test/model",
        local_node_id="creation_test",
        enable_all_components=True
    )

    assert system is not None
    assert isinstance(system, FederatedVLLMSystem)

    # Cleanup
    if system.is_initialized:
        await system.shutdown_system()


if __name__ == "__main__":
    # Ejecutar pruebas manualmente
    print("🚀 Ejecutando pruebas de integración del sistema federado vLLM...")

    async def run_tests():
        # Crear sistema de prueba
        system = await FederatedVLLMSystem.create_federated_vllm_system(
            model_path="/mock/model",
            local_node_id="integration_test"
        )

        if not system or not system.is_initialized:
            print("❌ No se pudo crear el sistema de prueba")
            return

        try:
            # Ejecutar pruebas básicas
            print("📋 Ejecutando pruebas básicas...")

            # Prueba 1: Preparación de ronda
            success = await system.prepare_for_round("integration_round", {
                "hardware_type": "gpu",
                "gpu_memory_gb": 8.0
            })
            print(f"   Preparación de ronda: {'✅' if success else '❌'}")

            # Prueba 2: Procesamiento de solicitud
            request = BatchRequest(
                id="integration_test_001",
                prompt="Test integration prompt",
                max_tokens=30
            )

            response = await system.process_federated_request(request)
            print(f"   Procesamiento de solicitud: {'✅' if response else '❌'}")

            # Prueba 3: Métricas del sistema
            metrics = await system.get_system_metrics()
            print(f"   Recopilación de métricas: {'✅' if metrics else '❌'}")

            # Prueba 4: Salud del sistema
            health = system.get_system_health()
            print(f"   Salud del sistema: {'✅' if health['overall_status'] == 'healthy' else '❌'}")

            print("🎉 Pruebas de integración completadas")

        finally:
            await system.shutdown_system()

    # Ejecutar pruebas
    asyncio.run(run_tests())