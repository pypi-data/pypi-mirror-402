"""
Sistema de Load Testing Federado para AILOOS
Implementa pruebas de carga que simulan miles de usuarios concurrentes
consultando EmpoorioLM mientras el entrenamiento federado está activo,
validando estabilidad de inferencia bajo carga y resiliencia de FedAsync.
"""

import asyncio
import aiohttp
import time
import json
import logging
import random
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import psutil
import gc
from pathlib import Path

from .async_aggregator import AsyncAggregator, WeightUpdate
from .p2p_protocol import P2PProtocol, PeerInfo, FedAsyncUpdate
from ..inference.api import InferenceConfig, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuración del sistema de load testing federado."""

    # Configuración de usuarios concurrentes
    num_concurrent_users: int = 1000
    user_ramp_up_time: float = 30.0  # Tiempo para alcanzar carga máxima
    test_duration_seconds: int = 300  # Duración total del test

    # Configuración de consultas de inferencia
    inference_api_url: str = "http://localhost:8000"
    queries_per_second_per_user: float = 0.5  # Consultas por segundo por usuario
    query_templates: List[str] = field(default_factory=lambda: [
        "¿Cuál es la capital de {país}?",
        "Explica el concepto de {concepto} en machine learning",
        "Escribe un resumen sobre {tema}",
        "¿Cómo funciona {tecnología}?",
        "Traduce '{frase}' al inglés",
        "Genera una historia corta sobre {tema}",
        "¿Cuáles son los beneficios de {tecnología}?",
        "Resuelve este problema: {problema}",
        "Describe los pasos para {tarea}",
        "¿Qué significa {término} en contexto de IA?"
    ])

    # Configuración de federated learning simulado
    num_federated_nodes: int = 50
    federated_rounds_per_minute: float = 2.0
    models_per_round: int = 10  # Modelos por ronda de agregación
    sparsification_enabled: bool = True

    # Configuración de demoras de red
    network_delay_enabled: bool = True
    base_network_delay_ms: float = 50.0
    network_jitter_ms: float = 20.0
    packet_loss_rate: float = 0.02  # 2% packet loss
    network_burst_delay_ms: float = 500.0  # Delay bursts
    burst_probability: float = 0.05  # 5% chance of burst

    # Configuración de métricas
    metrics_collection_interval: float = 5.0
    enable_detailed_logging: bool = False


@dataclass
class LoadTestMetrics:
    """Métricas recopiladas durante las pruebas de carga."""

    # Métricas de inferencia
    total_inference_requests: int = 0
    successful_inference_requests: int = 0
    failed_inference_requests: int = 0
    inference_latencies: List[float] = field(default_factory=list)
    inference_throughput: float = 0.0

    # Métricas de federated learning
    federated_rounds_completed: int = 0
    federated_updates_processed: int = 0
    federated_aggregation_latencies: List[float] = field(default_factory=list)

    # Métricas de red
    network_delays_applied: List[float] = field(default_factory=list)
    packet_losses_simulated: int = 0

    # Métricas de estabilidad
    memory_usage_mb: List[float] = field(default_factory=list)
    cpu_usage_percent: List[float] = field(default_factory=list)
    error_rate_percent: float = 0.0

    # Timestamps
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def get_inference_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de inferencia."""
        if not self.inference_latencies:
            return {}

        return {
            'total_requests': self.total_inference_requests,
            'success_rate': self.successful_inference_requests / max(self.total_inference_requests, 1),
            'avg_latency': statistics.mean(self.inference_latencies),
            'median_latency': statistics.median(self.inference_latencies),
            'p95_latency': statistics.quantiles(self.inference_latencies, n=20)[18] if len(self.inference_latencies) >= 20 else max(self.inference_latencies),
            'p99_latency': statistics.quantiles(self.inference_latencies, n=100)[98] if len(self.inference_latencies) >= 100 else max(self.inference_latencies),
            'min_latency': min(self.inference_latencies),
            'max_latency': max(self.inference_latencies),
            'throughput_rps': self.inference_throughput
        }

    def get_federated_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de federated learning."""
        if not self.federated_aggregation_latencies:
            return {}

        return {
            'rounds_completed': self.federated_rounds_completed,
            'updates_processed': self.federated_updates_processed,
            'avg_aggregation_latency': statistics.mean(self.federated_aggregation_latencies),
            'updates_per_round': self.federated_updates_processed / max(self.federated_rounds_completed, 1)
        }

    def get_network_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de red."""
        if not self.network_delays_applied:
            return {}

        return {
            'avg_delay_ms': statistics.mean(self.network_delays_applied),
            'max_delay_ms': max(self.network_delays_applied),
            'packet_loss_rate': self.packet_losses_simulated / max(self.total_inference_requests + self.federated_updates_processed, 1)
        }

    def get_stability_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de estabilidad del sistema."""
        return {
            'avg_memory_mb': statistics.mean(self.memory_usage_mb) if self.memory_usage_mb else 0,
            'max_memory_mb': max(self.memory_usage_mb) if self.memory_usage_mb else 0,
            'avg_cpu_percent': statistics.mean(self.cpu_usage_percent) if self.cpu_usage_percent else 0,
            'max_cpu_percent': max(self.cpu_usage_percent) if self.cpu_usage_percent else 0,
            'error_rate_percent': self.error_rate_percent,
            'test_duration_seconds': (self.end_time or time.time()) - self.start_time
        }


class NetworkDelaySimulator:
    """Simulador de demoras de red para pruebas de resiliencia."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.delay_stats = []

    async def apply_network_delay(self) -> float:
        """Aplicar demora de red simulada."""
        if not self.config.network_delay_enabled:
            return 0.0

        # Delay base + jitter
        base_delay = self.config.base_network_delay_ms
        jitter = random.uniform(-self.config.network_jitter_ms, self.config.network_jitter_ms)
        delay = max(0, base_delay + jitter)

        # Burst delay (alta latencia ocasional)
        if random.random() < self.config.burst_probability:
            delay += self.config.network_burst_delay_ms

        # Packet loss simulation
        if random.random() < self.config.packet_loss_rate:
            # Simulate packet loss by adding very high delay
            delay += 10000  # 10 second delay to simulate loss

        delay_seconds = delay / 1000.0
        self.delay_stats.append(delay)

        await asyncio.sleep(delay_seconds)
        return delay

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de demoras de red."""
        if not self.delay_stats:
            return {}

        return {
            'avg_delay_ms': statistics.mean(self.delay_stats),
            'max_delay_ms': max(self.delay_stats),
            'delays_applied': len(self.delay_stats)
        }


class InferenceLoadSimulator:
    """Simulador de carga para consultas de inferencia."""

    def __init__(self, config: LoadTestConfig, metrics: LoadTestMetrics):
        self.config = config
        self.metrics = metrics
        self.session = aiohttp.ClientSession()
        self.is_running = False

        # Generador de consultas
        self.query_params = {
            'país': ['Francia', 'España', 'Alemania', 'Italia', 'Reino Unido', 'Estados Unidos', 'Japón', 'China'],
            'concepto': ['redes neuronales', 'aprendizaje profundo', 'transformers', 'embeddings', 'fine-tuning'],
            'tema': ['inteligencia artificial', 'machine learning', 'ciencia de datos', 'computación cuántica'],
            'tecnología': ['blockchain', '5G', 'IoT', 'realidad virtual', 'autonomous driving'],
            'frase': ['Hola mundo', 'Cómo estás', 'Gracias por tu ayuda', 'Hasta luego'],
            'problema': ['2x + 3 = 7', 'factorizar x² - 5x + 6', 'calcular integral de x²'],
            'tarea': ['instalar Python', 'configurar un servidor', 'hacer backup de datos'],
            'término': ['overfitting', 'gradient descent', 'attention mechanism', 'tokenization']
        }

    async def start(self):
        """Iniciar simulación de carga de inferencia."""
        self.is_running = True
        logger.info(f"🚀 Starting inference load simulation with {self.config.num_concurrent_users} concurrent users")

        # Crear tareas para usuarios concurrentes
        tasks = []
        for user_id in range(self.config.num_concurrent_users):
            task = asyncio.create_task(self._simulate_user(user_id))
            tasks.append(task)

        # Esperar a que todas las tareas terminen
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self):
        """Detener simulación de carga."""
        self.is_running = False
        await self.session.close()

    def _generate_query(self) -> str:
        """Generar una consulta aleatoria."""
        template = random.choice(self.config.query_templates)

        # Reemplazar placeholders con valores aleatorios
        query = template
        for param, values in self.query_params.items():
            if f"{{{param}}}" in query:
                value = random.choice(values)
                query = query.replace(f"{{{param}}}", value)

        return query

    async def _simulate_user(self, user_id: int):
        """Simular un usuario realizando consultas."""
        try:
            # Ramp-up: esperar antes de empezar para distribuir la carga
            ramp_up_delay = (user_id / self.config.num_concurrent_users) * self.config.user_ramp_up_time
            await asyncio.sleep(ramp_up_delay)

            queries_sent = 0
            start_time = time.time()

            while self.is_running and (time.time() - start_time) < self.config.test_duration_seconds:
                try:
                    # Generar consulta
                    query = self._generate_query()

                    # Enviar consulta
                    request_start = time.time()
                    success = await self._send_inference_request(query)
                    request_end = time.time()

                    latency = request_end - request_start

                    # Actualizar métricas
                    self.metrics.total_inference_requests += 1
                    if success:
                        self.metrics.successful_inference_requests += 1
                        self.metrics.inference_latencies.append(latency)
                    else:
                        self.metrics.failed_inference_requests += 1

                    queries_sent += 1

                    # Esperar antes de siguiente consulta
                    inter_query_delay = 1.0 / self.config.queries_per_second_per_user
                    await asyncio.sleep(inter_query_delay)

                except Exception as e:
                    logger.debug(f"User {user_id} request error: {e}")
                    self.metrics.failed_inference_requests += 1
                    await asyncio.sleep(1.0)  # Esperar antes de reintentar

            logger.debug(f"User {user_id} completed {queries_sent} queries")

        except Exception as e:
            logger.error(f"User {user_id} simulation error: {e}")

    async def _send_inference_request(self, query: str) -> bool:
        """Enviar solicitud de inferencia."""
        try:
            payload = {
                "prompt": query,
                "max_tokens": 100,
                "temperature": 0.7
            }

            async with self.session.post(
                f"{self.config.inference_api_url}/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30.0)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return 'text' in result
                else:
                    logger.debug(f"Inference request failed with status {response.status}")
                    return False

        except Exception as e:
            logger.debug(f"Inference request exception: {e}")
            return False


class FederatedTrainingSimulator:
    """Simulador de entrenamiento federado con actualizaciones P2P."""

    def __init__(self, config: LoadTestConfig, metrics: LoadTestMetrics,
                 network_simulator: NetworkDelaySimulator):
        self.config = config
        self.metrics = metrics
        self.network_simulator = network_simulator

        # Simular nodos federados
        self.nodes = [f"node_{i}" for i in range(self.config.num_federated_nodes)]

        # AsyncAggregator simulado
        self.aggregator = AsyncAggregator(
            session_id="load_test_session",
            model_name="empoorio_lm_test",
            expected_participants=self.nodes,
            enable_sparsification=self.config.sparsification_enabled
        )

        self.is_running = False

    async def start(self):
        """Iniciar simulación de entrenamiento federado."""
        self.is_running = True
        logger.info(f"🚀 Starting federated training simulation with {self.config.num_federated_nodes} nodes")

        # Iniciar aggregator
        asyncio.create_task(self._run_aggregation_loop())

        # Simular rondas de entrenamiento
        round_interval = 60.0 / self.config.federated_rounds_per_minute

        while self.is_running:
            await self._simulate_federated_round()
            await asyncio.sleep(round_interval)

    async def stop(self):
        """Detener simulación de entrenamiento federado."""
        self.is_running = False
        await self.aggregator.shutdown()

    async def _simulate_federated_round(self):
        """Simular una ronda completa de federated learning."""
        try:
            round_start = time.time()

            # Simular actualizaciones de nodos
            update_tasks = []
            for node_id in self.nodes:
                if random.random() < 0.8:  # 80% de nodos participan
                    task = asyncio.create_task(self._simulate_node_update(node_id))
                    update_tasks.append(task)

            # Esperar actualizaciones con demoras de red
            await asyncio.gather(*update_tasks, return_exceptions=True)

            # Ejecutar agregación
            await self.aggregator.aggregate_incrementally()

            round_end = time.time()
            round_latency = round_end - round_start

            # Actualizar métricas
            self.metrics.federated_rounds_completed += 1
            self.metrics.federated_updates_processed += len(update_tasks)
            self.metrics.federated_aggregation_latencies.append(round_latency)

            logger.debug(f"Completed federated round {self.metrics.federated_rounds_completed} in {round_latency:.2f}s")

        except Exception as e:
            logger.error(f"Error in federated round simulation: {e}")

    async def _simulate_node_update(self, node_id: str):
        """Simular actualización de un nodo."""
        try:
            # Aplicar demora de red
            delay = await self.network_simulator.apply_network_delay()
            self.metrics.network_delays_applied.append(delay)

            # Simular datos de modelo (pesos ficticios)
            model_weights = {
                f'layer_{i}': torch.randn(100, 100) if torch else [[random.random() for _ in range(10)] for _ in range(10)]
                for i in range(5)
            }

            # Crear actualización
            update = WeightUpdate(
                node_id=node_id,
                weights=model_weights,
                num_samples=random.randint(100, 1000),
                timestamp=time.time()
            )

            # Enviar a aggregator
            await self.aggregator.add_weight_update(update)

        except Exception as e:
            logger.error(f"Error simulating node update for {node_id}: {e}")


class SystemResourceMonitor:
    """Monitor de recursos del sistema."""

    def __init__(self, metrics: LoadTestMetrics, collection_interval: float = 5.0):
        self.metrics = metrics
        self.collection_interval = collection_interval
        self.process = psutil.Process()
        self.is_running = False

    async def start(self):
        """Iniciar monitoreo de recursos."""
        self.is_running = True
        logger.info("📊 Starting system resource monitoring")

        while self.is_running:
            try:
                # Medir uso de memoria
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.metrics.memory_usage_mb.append(memory_mb)

                # Medir uso de CPU
                cpu_percent = self.process.cpu_percent()
                self.metrics.cpu_usage_percent.append(cpu_percent)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.collection_interval)

    def stop(self):
        """Detener monitoreo de recursos."""
        self.is_running = False


class FederatedLoadTester:
    """Sistema principal de load testing federado."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics = LoadTestMetrics()
        self.network_simulator = NetworkDelaySimulator(config)

        # Componentes del sistema
        self.inference_simulator = InferenceLoadSimulator(config, self.metrics)
        self.federated_simulator = FederatedTrainingSimulator(config, self.metrics, self.network_simulator)
        self.resource_monitor = SystemResourceMonitor(self.metrics, config.metrics_collection_interval)

        self.is_running = False

    async def run_test(self) -> LoadTestMetrics:
        """Ejecutar prueba de carga completa."""
        logger.info("🎯 Starting federated load test")
        logger.info(f"Configuration: {self.config.num_concurrent_users} users, {self.config.num_federated_nodes} federated nodes")
        logger.info(f"Duration: {self.config.test_duration_seconds}s, Network delays: {self.config.network_delay_enabled}")

        self.is_running = True
        self.metrics.start_time = time.time()

        try:
            # Iniciar componentes
            await self.resource_monitor.start()

            # Iniciar simuladores en paralelo
            inference_task = asyncio.create_task(self.inference_simulator.start())
            federated_task = asyncio.create_task(self.federated_simulator.start())

            # Esperar duración del test
            await asyncio.sleep(self.config.test_duration_seconds)

            # Detener simuladores
            await self.inference_simulator.stop()
            await self.federated_simulator.stop()

            # Esperar a que terminen las tareas
            await asyncio.gather(inference_task, federated_task, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error during load test: {e}")
        finally:
            self.is_running = False
            self.resource_monitor.stop()
            self.metrics.end_time = time.time()

        # Calcular métricas finales
        self._calculate_final_metrics()

        logger.info("✅ Load test completed")
        return self.metrics

    def _calculate_final_metrics(self):
        """Calcular métricas finales."""
        total_requests = self.metrics.total_inference_requests
        failed_requests = self.metrics.failed_inference_requests

        if total_requests > 0:
            self.metrics.error_rate_percent = (failed_requests / total_requests) * 100

        duration = self.metrics.end_time - self.metrics.start_time
        if duration > 0:
            self.metrics.inference_throughput = self.metrics.successful_inference_requests / duration

    def save_results(self, filename: str = "federated_load_test_results.json"):
        """Guardar resultados del test."""
        results = {
            'config': {
                'num_concurrent_users': self.config.num_concurrent_users,
                'num_federated_nodes': self.config.num_federated_nodes,
                'test_duration_seconds': self.config.test_duration_seconds,
                'network_delay_enabled': self.config.network_delay_enabled
            },
            'inference_stats': self.metrics.get_inference_stats(),
            'federated_stats': self.metrics.get_federated_stats(),
            'network_stats': self.metrics.get_network_stats(),
            'stability_stats': self.metrics.get_stability_stats(),
            'timestamp': time.time()
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"📄 Results saved to {filename}")

    def print_summary(self):
        """Imprimir resumen de resultados."""
        print("\n" + "="*80)
        print("FEDERATED LOAD TEST RESULTS")
        print("="*80)

        print(f"Test Duration: {self.metrics.get_stability_stats()['test_duration_seconds']:.2f}s")
        print(f"Concurrent Users: {self.config.num_concurrent_users}")
        print(f"Federated Nodes: {self.config.num_federated_nodes}")

        print("\nINFERENCE PERFORMANCE:")
        inf_stats = self.metrics.get_inference_stats()
        if inf_stats:
            print(f"  Total Requests: {inf_stats['total_requests']}")
            print(f"  Success Rate: {inf_stats['success_rate']*100:.1f}%")
            print(f"  Throughput: {inf_stats['throughput_rps']:.2f} req/s")
            print(f"  Avg Latency: {inf_stats['avg_latency']*1000:.1f}ms")
            print(f"  P95 Latency: {inf_stats['p95_latency']*1000:.1f}ms")
            print(f"  P99 Latency: {inf_stats['p99_latency']*1000:.1f}ms")

        print("\nFEDERATED LEARNING PERFORMANCE:")
        fed_stats = self.metrics.get_federated_stats()
        if fed_stats:
            print(f"  Rounds Completed: {fed_stats['rounds_completed']}")
            print(f"  Updates Processed: {fed_stats['updates_processed']}")
            print(f"  Avg Aggregation Latency: {fed_stats['avg_aggregation_latency']:.2f}s")

        print("\nNETWORK SIMULATION:")
        net_stats = self.metrics.get_network_stats()
        if net_stats:
            print(f"  Avg Network Delay: {net_stats['avg_delay_ms']:.1f}ms")
            print(f"  Max Network Delay: {net_stats['max_delay_ms']:.1f}ms")
            print(f"  Packet Loss Rate: {net_stats['packet_loss_rate']*100:.2f}%")

        print("\nSYSTEM STABILITY:")
        stab_stats = self.metrics.get_stability_stats()
        print(f"  Avg Memory Usage: {stab_stats['avg_memory_mb']:.1f}MB")
        print(f"  Max Memory Usage: {stab_stats['max_memory_mb']:.1f}MB")
        print(f"  Avg CPU Usage: {stab_stats['avg_cpu_percent']:.1f}%")
        print(f"  Error Rate: {stab_stats['error_rate_percent']:.2f}%")

        print("\nVALIDATION RESULTS:")
        self._validate_results()

    def _validate_results(self):
        """Validar resultados contra criterios de aceptación."""
        inf_stats = self.metrics.get_inference_stats()
        fed_stats = self.metrics.get_federated_stats()
        stab_stats = self.metrics.get_stability_stats()

        # Criterios de validación
        validations = []

        # 1. Estabilidad de inferencia bajo carga
        if inf_stats and inf_stats.get('success_rate', 0) > 0.95:  # >95% success rate
            validations.append("✅ Inference stability: PASSED (>95% success rate)")
        else:
            validations.append("❌ Inference stability: FAILED (<95% success rate)")

        # 2. Latencia aceptable
        if inf_stats and inf_stats.get('p95_latency', float('inf')) < 5.0:  # <5s P95 latency
            validations.append("✅ Inference latency: PASSED (<5s P95)")
        else:
            validations.append("❌ Inference latency: FAILED (>5s P95)")

        # 3. Resiliencia de FedAsync
        if fed_stats and fed_stats.get('rounds_completed', 0) > 0:
            validations.append("✅ FedAsync resilience: PASSED (rounds completed)")
        else:
            validations.append("❌ FedAsync resilience: FAILED (no rounds completed)")

        # 4. Estabilidad del sistema
        if stab_stats.get('error_rate_percent', 100) < 5.0:  # <5% error rate
            validations.append("✅ System stability: PASSED (<5% error rate)")
        else:
            validations.append("❌ System stability: FAILED (>5% error rate)")

        for validation in validations:
            print(f"  {validation}")


# Función de conveniencia para ejecutar test
async def run_federated_load_test(config: Optional[LoadTestConfig] = None) -> LoadTestMetrics:
    """Ejecutar prueba de carga federada con configuración por defecto."""
    if config is None:
        config = LoadTestConfig()

    tester = FederatedLoadTester(config)
    results = await tester.run_test()
    tester.save_results()
    tester.print_summary()

    return results


if __name__ == "__main__":
    # Configuración de ejemplo para pruebas
    config = LoadTestConfig(
        num_concurrent_users=500,  # 500 usuarios concurrentes
        num_federated_nodes=20,    # 20 nodos federados
        test_duration_seconds=60,  # 1 minuto de test
        network_delay_enabled=True
    )

    # Ejecutar test
    asyncio.run(run_federated_load_test(config))