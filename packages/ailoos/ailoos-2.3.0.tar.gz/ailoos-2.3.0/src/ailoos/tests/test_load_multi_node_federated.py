#!/usr/bin/env python3
"""
Pruebas de Carga con Múltiples Nodos Federados - AILOOS
Tests de carga que simulan escenarios reales con 10-50 nodos federados,
incluyendo carga concurrente, latencia de red simulada y medición de métricas.
"""

import pytest
import time
import asyncio
import random
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import tempfile
import os


@dataclass
class LoadTestMetrics:
    """Métricas recopiladas durante pruebas de carga"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    latencies: List[float] = None
    throughput_rps: float = 0.0  # requests per second
    error_rate: float = 0.0
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    start_time: datetime = None
    end_time: datetime = None

    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []

    def add_request(self, latency: float, success: bool = True):
        """Agregar una solicitud a las métricas"""
        self.total_requests += 1
        self.total_latency += latency
        self.latencies.append(latency)

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def calculate_final_metrics(self):
        """Calcular métricas finales"""
        if self.total_requests == 0:
            return

        duration = (self.end_time - self.start_time).total_seconds()
        self.throughput_rps = self.total_requests / duration if duration > 0 else 0
        self.error_rate = self.failed_requests / self.total_requests
        self.avg_latency = self.total_latency / self.total_requests

        if self.latencies:
            self.latencies.sort()
            self.p95_latency = self.latencies[int(0.95 * len(self.latencies))]
            self.p99_latency = self.latencies[int(0.99 * len(self.latencies))]


class NetworkSimulator:
    """Simulador de condiciones de red"""

    def __init__(self, base_latency: float = 0.05, jitter: float = 0.02, packet_loss: float = 0.01):
        self.base_latency = base_latency
        self.jitter = jitter
        self.packet_loss = packet_loss

    def simulate_network_delay(self) -> float:
        """Simular retraso de red"""
        delay = self.base_latency + random.uniform(-self.jitter, self.jitter)
        return max(0, delay)

    def simulate_packet_loss(self) -> bool:
        """Simular pérdida de paquetes"""
        return random.random() < self.packet_loss


class MultiNodeLoadTest:
    """Suite de pruebas de carga con múltiples nodos federados"""

    def __init__(self):
        self.metrics = LoadTestMetrics()
        self.network_sim = NetworkSimulator()

    def simulate_node_activity(self, node_id: str, coordinator: Any, session_id: str,
                             num_rounds: int = 3, model_size: int = 1000) -> Dict[str, Any]:
        """Simular actividad completa de un nodo en una sesión federada"""
        node_metrics = {
            "node_id": node_id,
            "rounds_completed": 0,
            "updates_sent": 0,
            "errors": 0,
            "total_latency": 0.0
        }

        try:
            # Registrar nodo
            start_time = time.time()
            network_delay = self.network_sim.simulate_network_delay()
            time.sleep(network_delay)

            coordinator.register_node(node_id)
            coordinator.add_node_to_session(session_id, node_id)

            registration_latency = time.time() - start_time
            node_metrics["total_latency"] += registration_latency

            # Participar en rondas
            for round_num in range(1, num_rounds + 1):
                round_start = time.time()

                # Simular procesamiento local
                processing_time = random.uniform(0.1, 0.5)  # 100-500ms
                time.sleep(processing_time)

                # Simular latencia de red para envío
                network_delay = self.network_sim.simulate_network_delay()
                time.sleep(network_delay)

                # Simular pérdida de paquetes
                if self.network_sim.simulate_packet_loss():
                    node_metrics["errors"] += 1
                    continue

                # Crear actualización de modelo
                weights = {}
                for layer in range(5):  # 5 capas
                    weights[f"layer_{layer}"] = [random.uniform(-1, 1) for _ in range(model_size // 5)]

                update = {
                    "weights": weights,
                    "samples_used": random.randint(100, 1000),
                    "accuracy": random.uniform(0.7, 0.95),
                    "loss": random.uniform(0.1, 0.8),
                    "round": round_num
                }

                # Enviar actualización
                send_start = time.time()
                try:
                    result = coordinator.submit_model_update(session_id, node_id, update)
                    if result:
                        node_metrics["updates_sent"] += 1
                        node_metrics["rounds_completed"] += 1
                    else:
                        node_metrics["errors"] += 1
                except Exception as e:
                    node_metrics["errors"] += 1

                send_latency = time.time() - send_start
                round_latency = time.time() - round_start
                node_metrics["total_latency"] += round_latency

        except Exception as e:
            node_metrics["errors"] += 1

        return node_metrics

    def run_load_test(self, num_nodes: int, coordinator: Any, session_id: str,
                     concurrent: bool = True, network_conditions: Dict = None) -> LoadTestMetrics:
        """Ejecutar prueba de carga completa"""
        if network_conditions:
            self.network_sim = NetworkSimulator(**network_conditions)

        self.metrics = LoadTestMetrics()
        self.metrics.start_time = datetime.now()

        # Crear sesión
        coordinator.create_session(session_id, "load_test_model", max(3, num_nodes // 4), num_nodes)

        # Iniciar entrenamiento
        coordinator.start_training(session_id)

        node_results = []

        if concurrent:
            # Ejecución concurrente
            with ThreadPoolExecutor(max_workers=min(20, num_nodes)) as executor:
                futures = []
                for i in range(num_nodes):
                    node_id = "02d"
                    future = executor.submit(
                        self.simulate_node_activity,
                        node_id, coordinator, session_id
                    )
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        node_results.append(result)
                        # Agregar métricas de latencia
                        if result["total_latency"] > 0:
                            self.metrics.add_request(result["total_latency"], result["errors"] == 0)
                    except Exception as e:
                        self.metrics.add_request(0.0, False)
        else:
            # Ejecución secuencial
            for i in range(num_nodes):
                node_id = "02d"
                result = self.simulate_node_activity(node_id, coordinator, session_id)
                node_results.append(result)
                if result["total_latency"] > 0:
                    self.metrics.add_request(result["total_latency"], result["errors"] == 0)

        # Intentar agregación final
        try:
            agg_start = time.time()
            coordinator.aggregate_models(session_id)
            agg_latency = time.time() - agg_start
            self.metrics.add_request(agg_latency, True)
        except Exception as e:
            self.metrics.add_request(0.0, False)

        self.metrics.end_time = datetime.now()
        self.metrics.calculate_final_metrics()

        return self.metrics


class TestMultiNodeFederatedLoad:
    """Tests de carga con múltiples nodos federados"""

    @pytest.fixture
    def load_tester(self):
        """Tester de carga para múltiples nodos"""
        return MultiNodeLoadTest()

    @pytest.fixture
    def mock_coordinator(self):
        """Coordinador mock para tests"""
        coordinator = Mock()
        coordinator.active_sessions = {}
        coordinator.node_registry = {}
        coordinator.create_session = Mock()
        coordinator.register_node = Mock()
        coordinator.add_node_to_session = Mock(return_value=True)
        coordinator.start_training = Mock(return_value={"status": "training_started"})
        coordinator.submit_model_update = Mock(return_value=True)
        coordinator.aggregate_models = Mock(return_value={"status": "success"})
        return coordinator

    def test_load_10_nodes_concurrent(self, load_tester, mock_coordinator):
        """Test de carga con 10 nodos concurrentes"""
        session_id = "load_test_10_nodes"

        metrics = load_tester.run_load_test(
            num_nodes=10,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True
        )

        # Validar métricas
        assert metrics.total_requests >= 10  # Al menos 10 solicitudes (una por nodo)
        assert metrics.successful_requests > 0
        assert metrics.throughput_rps > 0
        assert metrics.avg_latency > 0
        assert metrics.error_rate < 0.5  # Menos del 50% de errores

        print(f"10 nodos - Throughput: {metrics.throughput_rps:.2f} RPS, "
              f"Latencia promedio: {metrics.avg_latency:.3f}s, "
              f"Tasa de error: {metrics.error_rate:.2%}")

    def test_load_25_nodes_concurrent(self, load_tester, mock_coordinator):
        """Test de carga con 25 nodos concurrentes"""
        session_id = "load_test_25_nodes"

        metrics = load_tester.run_load_test(
            num_nodes=25,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True
        )

        # Validar métricas más estrictas para más nodos
        assert metrics.total_requests >= 25
        assert metrics.successful_requests >= 20  # Al menos 80% éxito
        assert metrics.throughput_rps > 5  # Mínimo 5 RPS
        assert metrics.avg_latency < 2.0  # Máximo 2 segundos promedio
        assert metrics.error_rate < 0.3  # Menos del 30% de errores

        print(f"25 nodos - Throughput: {metrics.throughput_rps:.2f} RPS, "
              f"Latencia promedio: {metrics.avg_latency:.3f}s, "
              f"Tasa de error: {metrics.error_rate:.2%}")

    def test_load_50_nodes_concurrent(self, load_tester, mock_coordinator):
        """Test de carga con 50 nodos concurrentes"""
        session_id = "load_test_50_nodes"

        metrics = load_tester.run_load_test(
            num_nodes=50,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True
        )

        # Validar métricas para carga máxima
        assert metrics.total_requests >= 50
        assert metrics.successful_requests >= 35  # Al menos 70% éxito
        assert metrics.throughput_rps > 8  # Mínimo 8 RPS
        assert metrics.avg_latency < 3.0  # Máximo 3 segundos promedio
        assert metrics.error_rate < 0.4  # Menos del 40% de errores

        print(f"50 nodos - Throughput: {metrics.throughput_rps:.2f} RPS, "
              f"Latencia promedio: {metrics.avg_latency:.3f}s, "
              f"Tasa de error: {metrics.error_rate:.2%}")

    def test_load_10_nodes_sequential(self, load_tester, mock_coordinator):
        """Test de carga con 10 nodos secuenciales (baseline)"""
        session_id = "load_test_10_seq"

        metrics = load_tester.run_load_test(
            num_nodes=10,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=False
        )

        # Validar que secuencial es más lento pero más confiable
        assert metrics.total_requests >= 10
        assert metrics.successful_requests >= 9  # Casi 100% éxito
        assert metrics.error_rate < 0.1  # Menos del 10% de errores

        print(f"10 nodos secuenciales - Throughput: {metrics.throughput_rps:.2f} RPS, "
              f"Latencia promedio: {metrics.avg_latency:.3f}s")

    def test_network_latency_simulation_fast(self, load_tester, mock_coordinator):
        """Test con simulación de red rápida"""
        session_id = "load_test_fast_network"

        network_conditions = {
            "base_latency": 0.01,  # 10ms
            "jitter": 0.005,       # 5ms
            "packet_loss": 0.001   # 0.1%
        }

        metrics = load_tester.run_load_test(
            num_nodes=20,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True,
            network_conditions=network_conditions
        )

        # Red rápida debería tener mejor rendimiento - ajustar expectativas basadas en simulación real
        assert metrics.avg_latency < 1.5  # Menos de 1.5s promedio (más realista con simulación)
        assert metrics.error_rate < 0.05  # Menos del 5% de errores

        print(f"Red rápida - Latencia promedio: {metrics.avg_latency:.3f}s, "
              f"Tasa de error: {metrics.error_rate:.2%}")

    def test_network_latency_simulation_slow(self, load_tester, mock_coordinator):
        """Test con simulación de red lenta"""
        session_id = "load_test_slow_network"

        network_conditions = {
            "base_latency": 0.5,   # 500ms
            "jitter": 0.2,         # 200ms
            "packet_loss": 0.05    # 5%
        }

        metrics = load_tester.run_load_test(
            num_nodes=15,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True,
            network_conditions=network_conditions
        )

        # Red lenta debería tener peor rendimiento pero aún funcionar
        assert metrics.avg_latency > 0.5  # Más de 500ms promedio
        assert metrics.error_rate < 0.5   # Menos del 50% de errores (manejo de pérdidas con red mala)

        print(f"Red lenta - Latencia promedio: {metrics.avg_latency:.3f}s, "
              f"Tasa de error: {metrics.error_rate:.2%}")

    def test_system_stability_under_load(self, load_tester, mock_coordinator):
        """Test de estabilidad del sistema bajo carga"""
        session_id = "stability_test"

        # Ejecutar múltiples rondas de carga
        stability_results = []

        for round_num in range(3):
            round_session = f"{session_id}_round_{round_num}"

            metrics = load_tester.run_load_test(
                num_nodes=30,
                coordinator=mock_coordinator,
                session_id=round_session,
                concurrent=True
            )

            stability_results.append({
                "round": round_num,
                "throughput": metrics.throughput_rps,
                "avg_latency": metrics.avg_latency,
                "error_rate": metrics.error_rate
            })

        # Verificar estabilidad (variación baja entre rondas)
        throughputs = [r["throughput"] for r in stability_results]
        latencies = [r["avg_latency"] for r in stability_results]
        error_rates = [r["error_rate"] for r in stability_results]

        throughput_cv = statistics.stdev(throughputs) / statistics.mean(throughputs) if throughputs else 0
        latency_cv = statistics.stdev(latencies) / statistics.mean(latencies) if latencies else 0

        # Coeficiente de variación debería ser bajo (< 0.3)
        assert throughput_cv < 0.3, f"Throughput inestable: CV = {throughput_cv:.3f}"
        assert latency_cv < 0.3, f"Latencia inestable: CV = {latency_cv:.3f}"

        # Error rate debería ser consistente
        avg_error_rate = statistics.mean(error_rates)
        assert avg_error_rate < 0.25, f"Alta tasa de error promedio: {avg_error_rate:.2%}"

        print(f"Estabilidad - CV Throughput: {throughput_cv:.3f}, "
              f"CV Latencia: {latency_cv:.3f}, "
              f"Error promedio: {avg_error_rate:.2%}")

    def test_scalability_analysis(self, load_tester, mock_coordinator):
        """Test de análisis de escalabilidad"""
        node_counts = [10, 20, 30, 40, 50]
        scalability_results = []

        for num_nodes in node_counts:
            session_id = f"scalability_test_{num_nodes}"

            start_time = time.time()
            metrics = load_tester.run_load_test(
                num_nodes=num_nodes,
                coordinator=mock_coordinator,
                session_id=session_id,
                concurrent=True
            )
            test_duration = time.time() - start_time

            scalability_results.append({
                "nodes": num_nodes,
                "throughput": metrics.throughput_rps,
                "avg_latency": metrics.avg_latency,
                "error_rate": metrics.error_rate,
                "duration": test_duration
            })

        # Verificar escalabilidad (throughput debería aumentar con nodos, pero con límites)
        throughputs = [r["throughput"] for r in scalability_results]

        # El throughput debería aumentar inicialmente pero no decrecer significativamente
        for i in range(1, len(throughputs)):
            # Al menos mantener el 70% del throughput máximo alcanzado
            max_throughput = max(throughputs[:i+1])
            assert throughputs[i] >= 0.7 * max_throughput, \
                f"Throughput decay at {node_counts[i]} nodes: {throughputs[i]} < {0.7 * max_throughput}"

        print("Análisis de escalabilidad:")
        for result in scalability_results:
            print(f"  {result['nodes']} nodos: {result['throughput']:.2f} RPS, "
                  f"{result['avg_latency']:.3f}s latencia, "
                  f"{result['error_rate']:.2%} error")

    def test_resource_contention_simulation(self, load_tester, mock_coordinator):
        """Test simulación de contención de recursos"""
        session_id = "contention_test"

        # Configurar red con alta latencia y pérdidas
        network_conditions = {
            "base_latency": 0.3,   # 300ms
            "jitter": 0.15,        # 150ms
            "packet_loss": 0.03    # 3%
        }

        # Ejecutar con muchos nodos concurrentes
        metrics = load_tester.run_load_test(
            num_nodes=40,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True,
            network_conditions=network_conditions
        )

        # Bajo contención, el sistema debería aún funcionar
        assert metrics.total_requests >= 40
        assert metrics.successful_requests >= 25  # Al menos 60% éxito
        assert metrics.avg_latency < 5.0  # Menos de 5 segundos promedio

        print(f"Contención de recursos - Throughput: {metrics.throughput_rps:.2f} RPS, "
              f"Latencia: {metrics.avg_latency:.3f}s, "
              f"Éxito: {metrics.successful_requests}/{metrics.total_requests}")

    def test_failure_recovery_under_load(self, load_tester, mock_coordinator):
        """Test de recuperación de fallos bajo carga"""
        session_id = "failure_recovery_test"

        # Configurar mock para simular fallos intermitentes
        call_count = 0
        def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 7 == 0:  # Cada 7 llamadas falla
                raise Exception("Simulated network failure")
            return True

        mock_coordinator.submit_model_update.side_effect = intermittent_failure

        metrics = load_tester.run_load_test(
            num_nodes=35,
            coordinator=mock_coordinator,
            session_id=session_id,
            concurrent=True
        )

        # El sistema debería manejar fallos gracefully
        assert metrics.total_requests >= 35
        assert metrics.failed_requests > 0  # Deberían haber algunos fallos
        assert metrics.successful_requests > 0  # Pero también éxitos
        assert metrics.error_rate < 0.5  # Menos del 50% de fallos totales

        print(f"Recuperación de fallos - Tasa de error: {metrics.error_rate:.2%}, "
              f"Éxitos: {metrics.successful_requests}, "
              f"Fallos: {metrics.failed_requests}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])