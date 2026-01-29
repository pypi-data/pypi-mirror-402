"""
Load Testing Infrastructure para Federated Learning con 1000+ nodos

Implementa herramientas completas de testing de carga para simular
y probar escalabilidad con miles de nodos federados.
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import random
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuración para pruebas de carga."""
    total_nodes: int = 1000
    concurrent_connections: int = 100
    test_duration_seconds: int = 300  # 5 minutos
    message_size_kb: int = 50
    network_latency_ms: int = 50
    packet_loss_rate: float = 0.01
    coordinator_url: str = "http://localhost:8000"
    enable_network_simulation: bool = True
    enable_metrics_collection: bool = True
    results_output_dir: str = "./load_test_results"


@dataclass
class NodeSimulator:
    """Simulador de nodo federado para testing."""
    node_id: str
    coordinator_url: str
    network_latency: int = 50
    packet_loss_rate: float = 0.01
    is_connected: bool = False
    last_heartbeat: Optional[datetime] = None
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    async def connect(self) -> bool:
        """Conectar al coordinator."""
        try:
            # Simular latencia de red
            await asyncio.sleep(self.network_latency / 1000)

            # Simular pérdida de paquetes
            if random.random() < self.packet_loss_rate:
                raise Exception("Packet loss simulation")

            self.is_connected = True
            self.last_heartbeat = datetime.now()
            logger.debug(f"Node {self.node_id} connected")
            return True

        except Exception as e:
            self.errors.append(f"Connection failed: {str(e)}")
            return False

    async def send_heartbeat(self) -> bool:
        """Enviar heartbeat al coordinator."""
        if not self.is_connected:
            return False

        try:
            start_time = time.time()

            # Simular latencia de red
            await asyncio.sleep(self.network_latency / 1000)

            # Simular pérdida de paquetes
            if random.random() < self.packet_loss_rate:
                raise Exception("Heartbeat packet loss")

            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.last_heartbeat = datetime.now()
            self.messages_sent += 1

            return True

        except Exception as e:
            self.errors.append(f"Heartbeat failed: {str(e)}")
            return False

    async def send_model_update(self, model_size_kb: int = 50) -> bool:
        """Enviar actualización de modelo."""
        if not self.is_connected:
            return False

        try:
            start_time = time.time()

            # Simular latencia de red + tiempo de transmisión
            transmission_time = (model_size_kb * 1024) / (10 * 1024 * 1024)  # 10 Mbps
            total_delay = self.network_latency / 1000 + transmission_time
            await asyncio.sleep(total_delay)

            # Simular pérdida de paquetes
            if random.random() < self.packet_loss_rate:
                raise Exception("Model update packet loss")

            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.messages_sent += 1
            self.bytes_sent += model_size_kb * 1024

            return True

        except Exception as e:
            self.errors.append(f"Model update failed: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del nodo."""
        return {
            'node_id': self.node_id,
            'is_connected': self.is_connected,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'avg_response_time': statistics.mean(self.response_times) if self.response_times else 0,
            'min_response_time': min(self.response_times) if self.response_times else 0,
            'max_response_time': max(self.response_times) if self.response_times else 0,
            'error_count': len(self.errors),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


@dataclass
class LoadTestResults:
    """Resultados de pruebas de carga."""
    test_start_time: datetime
    test_end_time: Optional[datetime] = None
    config: LoadTestConfig = field(default_factory=LoadTestConfig)
    node_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    system_metrics: Dict[str, List[Tuple[datetime, Any]]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Duración de la prueba en segundos."""
        if not self.test_end_time:
            return 0
        return (self.test_end_time - self.test_start_time).total_seconds()

    @property
    def total_nodes_connected(self) -> int:
        """Total de nodos conectados."""
        return sum(1 for stats in self.node_stats.values() if stats.get('is_connected', False))

    @property
    def connection_success_rate(self) -> float:
        """Tasa de éxito de conexiones."""
        if not self.node_stats:
            return 0.0
        return self.total_nodes_connected / len(self.node_stats) * 100

    @property
    def avg_response_time(self) -> float:
        """Tiempo de respuesta promedio."""
        response_times = []
        for stats in self.node_stats.values():
            if stats.get('avg_response_time', 0) > 0:
                response_times.append(stats['avg_response_time'])
        return statistics.mean(response_times) if response_times else 0

    @property
    def total_messages_sent(self) -> int:
        """Total de mensajes enviados."""
        return sum(stats.get('messages_sent', 0) for stats in self.node_stats.values())

    @property
    def total_bytes_sent(self) -> int:
        """Total de bytes enviados."""
        return sum(stats.get('bytes_sent', 0) for stats in self.node_stats.values())

    @property
    def throughput_messages_per_second(self) -> float:
        """Throughput de mensajes por segundo."""
        if self.duration_seconds == 0:
            return 0
        return self.total_messages_sent / self.duration_seconds

    @property
    def throughput_mbps(self) -> float:
        """Throughput en Mbps."""
        if self.duration_seconds == 0:
            return 0
        return (self.total_bytes_sent * 8) / (self.duration_seconds * 1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'test_start_time': self.test_start_time.isoformat(),
            'test_end_time': self.test_end_time.isoformat() if self.test_end_time else None,
            'duration_seconds': self.duration_seconds,
            'config': {
                'total_nodes': self.config.total_nodes,
                'concurrent_connections': self.config.concurrent_connections,
                'test_duration_seconds': self.config.test_duration_seconds,
                'message_size_kb': self.config.message_size_kb,
                'network_latency_ms': self.config.network_latency_ms,
                'packet_loss_rate': self.config.packet_loss_rate
            },
            'summary': {
                'total_nodes_connected': self.total_nodes_connected,
                'connection_success_rate': round(self.connection_success_rate, 2),
                'avg_response_time': round(self.avg_response_time, 3),
                'total_messages_sent': self.total_messages_sent,
                'total_bytes_sent': self.total_bytes_sent,
                'throughput_messages_per_second': round(self.throughput_messages_per_second, 2),
                'throughput_mbps': round(self.throughput_mbps, 2),
                'total_errors': len(self.errors)
            },
            'node_stats': self.node_stats,
            'system_metrics': {
                k: [(t.isoformat(), v) for t, v in values]
                for k, values in self.system_metrics.items()
            },
            'errors': self.errors
        }


class NetworkSimulator:
    """Simulador de red para testing de carga."""

    def __init__(self, latency_ms: int = 50, packet_loss_rate: float = 0.01, bandwidth_mbps: float = 10):
        self.latency_ms = latency_ms
        self.packet_loss_rate = packet_loss_rate
        self.bandwidth_mbps = bandwidth_mbps  # Mbps

    async def simulate_network_delay(self, data_size_bytes: int = 0) -> float:
        """Simular delay de red incluyendo transmisión."""
        # Latencia base
        delay = self.latency_ms / 1000

        # Tiempo de transmisión
        if data_size_bytes > 0:
            transmission_time = (data_size_bytes * 8) / (self.bandwidth_mbps * 1024 * 1024)
            delay += transmission_time

        # Jitter aleatorio (±20%)
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        delay += jitter

        await asyncio.sleep(delay)
        return delay

    def simulate_packet_loss(self) -> bool:
        """Simular pérdida de paquetes."""
        return random.random() < self.packet_loss_rate


class LoadTestingCoordinator:
    """
    Coordinador de pruebas de carga para federated learning.

    Características:
    - Simulación de 1000+ nodos
    - Control de concurrencia
    - Métricas en tiempo real
    - Network simulation
    - Resultados detallados
    """

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.nodes: Dict[str, NodeSimulator] = {}
        self.network_simulator = NetworkSimulator(
            latency_ms=config.network_latency_ms,
            packet_loss_rate=config.packet_loss_rate
        )
        self.results = LoadTestResults(
            test_start_time=datetime.now(),
            config=config
        )
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=config.concurrent_connections)

        # Crear directorio de resultados
        os.makedirs(config.results_output_dir, exist_ok=True)

    def create_nodes(self):
        """Crear nodos simulados."""
        logger.info(f"Creating {self.config.total_nodes} simulated nodes...")

        for i in range(self.config.total_nodes):
            node_id = "02d"
            node = NodeSimulator(
                node_id=node_id,
                coordinator_url=self.config.coordinator_url,
                network_latency=self.config.network_latency_ms,
                packet_loss_rate=self.config.packet_loss_rate
            )
            self.nodes[node_id] = node

        logger.info(f"Created {len(self.nodes)} nodes")

    async def run_connection_phase(self) -> Dict[str, Any]:
        """Fase de conexión inicial."""
        logger.info("Starting connection phase...")

        semaphore = asyncio.Semaphore(self.config.concurrent_connections)
        connection_results = []

        async def connect_node(node: NodeSimulator):
            async with semaphore:
                success = await node.connect()
                connection_results.append((node.node_id, success))
                return success

        # Conectar nodos en paralelo con control de concurrencia
        tasks = [connect_node(node) for node in self.nodes.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Actualizar estadísticas
        successful_connections = sum(1 for _, success in connection_results if success)
        total_connections = len(connection_results)

        logger.info(f"Connection phase completed: {successful_connections}/{total_connections} successful")

        return {
            'successful_connections': successful_connections,
            'total_connections': total_connections,
            'success_rate': successful_connections / total_connections * 100 if total_connections > 0 else 0
        }

    async def run_heartbeat_phase(self) -> Dict[str, Any]:
        """Fase de heartbeats continuos."""
        logger.info("Starting heartbeat phase...")

        heartbeat_interval = 30  # segundos
        end_time = time.time() + self.config.test_duration_seconds

        heartbeat_stats = {
            'total_heartbeats': 0,
            'successful_heartbeats': 0,
            'failed_heartbeats': 0
        }

        while time.time() < end_time and self.is_running:
            semaphore = asyncio.Semaphore(self.config.concurrent_connections)

            async def send_heartbeat(node: NodeSimulator):
                async with semaphore:
                    success = await node.send_heartbeat()
                    return success

            # Enviar heartbeats en paralelo
            tasks = [send_heartbeat(node) for node in self.nodes.values() if node.is_connected]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if r is True)
            heartbeat_stats['total_heartbeats'] += len(results)
            heartbeat_stats['successful_heartbeats'] += successful
            heartbeat_stats['failed_heartbeats'] += (len(results) - successful)

            # Registrar métricas del sistema
            self._record_system_metric('active_connections', len([n for n in self.nodes.values() if n.is_connected]))
            self._record_system_metric('heartbeat_success_rate', successful / len(results) * 100 if results else 0)

            await asyncio.sleep(heartbeat_interval)

        logger.info(f"Heartbeat phase completed: {heartbeat_stats['successful_heartbeats']}/{heartbeat_stats['total_heartbeats']} successful")

        return heartbeat_stats

    async def run_model_update_phase(self) -> Dict[str, Any]:
        """Fase de actualizaciones de modelo."""
        logger.info("Starting model update phase...")

        model_update_stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'total_bytes_transferred': 0
        }

        # Simular múltiples rondas de federated learning
        rounds = 5
        for round_num in range(rounds):
            if not self.is_running:
                break

            logger.info(f"Starting model update round {round_num + 1}/{rounds}")

            semaphore = asyncio.Semaphore(self.config.concurrent_connections)

            async def send_model_update(node: NodeSimulator):
                async with semaphore:
                    success = await node.send_model_update(self.config.message_size_kb)
                    return success

            # Enviar actualizaciones en paralelo
            connected_nodes = [node for node in self.nodes.values() if node.is_connected]
            tasks = [send_model_update(node) for node in connected_nodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if r is True)
            model_update_stats['total_updates'] += len(results)
            model_update_stats['successful_updates'] += successful
            model_update_stats['failed_updates'] += (len(results) - successful)
            model_update_stats['total_bytes_transferred'] += successful * self.config.message_size_kb * 1024

            # Registrar métricas
            self._record_system_metric('model_updates_successful', successful)
            self._record_system_metric('model_updates_total', len(results))

            # Esperar entre rondas
            await asyncio.sleep(10)

        logger.info(f"Model update phase completed: {model_update_stats['successful_updates']}/{model_update_stats['total_updates']} successful")

        return model_update_stats

    def _record_system_metric(self, metric_name: str, value: Any):
        """Registrar métrica del sistema."""
        if metric_name not in self.results.system_metrics:
            self.results.system_metrics[metric_name] = []
        self.results.system_metrics[metric_name].append((datetime.now(), value))

    async def run_load_test(self) -> LoadTestResults:
        """Ejecutar prueba de carga completa."""
        logger.info("Starting comprehensive load test...")
        logger.info(f"Configuration: {self.config.total_nodes} nodes, {self.config.test_duration_seconds}s duration")

        self.is_running = True
        self.create_nodes()

        try:
            # Fase 1: Conexiones iniciales
            connection_results = await self.run_connection_phase()

            # Fase 2: Heartbeats continuos
            heartbeat_task = asyncio.create_task(self.run_heartbeat_phase())

            # Fase 3: Actualizaciones de modelo
            model_update_task = asyncio.create_task(self.run_model_update_phase())

            # Esperar a que ambas fases terminen
            await asyncio.gather(heartbeat_task, model_update_task)

            # Recopilar estadísticas finales
            for node_id, node in self.nodes.items():
                self.results.node_stats[node_id] = node.get_stats()

            self.results.test_end_time = datetime.now()

            logger.info("Load test completed successfully")
            return self.results

        except Exception as e:
            self.results.errors.append(f"Load test failed: {str(e)}")
            self.results.test_end_time = datetime.now()
            logger.error(f"Load test failed: {e}")
            return self.results

        finally:
            self.is_running = False

    def save_results(self, filename: Optional[str] = None) -> str:
        """Guardar resultados en archivo."""
        if not filename:
            timestamp = self.results.test_start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"

        filepath = os.path.join(self.config.results_output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(self.results.to_dict(), f, indent=2)

        logger.info(f"Results saved to {filepath}")
        return filepath

    def generate_report(self) -> str:
        """Generar reporte de resultados."""
        results = self.results

        report = f"""
LOAD TESTING REPORT - FEDERATED LEARNING SCALABILITY
{'='*60}

TEST CONFIGURATION:
- Total Nodes: {results.config.total_nodes}
- Concurrent Connections: {results.config.concurrent_connections}
- Test Duration: {results.config.test_duration_seconds} seconds
- Message Size: {results.config.message_size_kb} KB
- Network Latency: {results.config.network_latency_ms} ms
- Packet Loss Rate: {results.config.packet_loss_rate * 100}%

TEST RESULTS:
- Duration: {results.duration_seconds:.1f} seconds
- Nodes Connected: {results.total_nodes_connected}/{len(results.node_stats)}
- Connection Success Rate: {results.connection_success_rate:.1f}%
- Average Response Time: {results.avg_response_time:.3f} seconds
- Total Messages Sent: {results.total_messages_sent:,}
- Total Bytes Sent: {results.total_bytes_sent:,} bytes
- Throughput: {results.throughput_messages_per_second:.1f} messages/second
- Network Throughput: {results.throughput_mbps:.2f} Mbps

PERFORMANCE METRICS:
"""

        # Añadir métricas detalladas
        if results.node_stats:
            response_times = [stats['avg_response_time'] for stats in results.node_stats.values() if stats['avg_response_time'] > 0]
            if response_times:
                report += f"- Response Time (avg): {statistics.mean(response_times):.3f}s\n"
                report += f"- Response Time (min): {min(response_times):.3f}s\n"
                report += f"- Response Time (max): {max(response_times):.3f}s\n"
                report += f"- Response Time (95th percentile): {statistics.quantiles(response_times, n=20)[18]:.3f}s\n"

        # Añadir métricas del sistema
        if results.system_metrics:
            report += "\nSYSTEM METRICS OVER TIME:\n"
            for metric_name, values in results.system_metrics.items():
                if values:
                    avg_value = statistics.mean([v for _, v in values])
                    report += f"- {metric_name}: {avg_value:.2f} (avg)\n"

        # Añadir errores
        if results.errors:
            report += f"\nERRORS ({len(results.errors)}):\n"
            for error in results.errors[:10]:  # Primeros 10 errores
                report += f"- {error}\n"

        report += f"\nCONCLUSION:\n"
        if results.connection_success_rate >= 95:
            report += "✅ EXCELLENT: High connection success rate\n"
        elif results.connection_success_rate >= 80:
            report += "👍 GOOD: Acceptable connection success rate\n"
        else:
            report += "⚠️ POOR: Connection issues detected\n"

        if results.throughput_messages_per_second >= 100:
            report += "✅ EXCELLENT: High message throughput\n"
        elif results.throughput_messages_per_second >= 50:
            report += "👍 GOOD: Acceptable message throughput\n"
        else:
            report += "⚠️ POOR: Low message throughput\n"

        return report


# Funciones de conveniencia

async def run_load_test(config: LoadTestConfig) -> LoadTestResults:
    """Ejecutar prueba de carga con configuración dada."""
    coordinator = LoadTestingCoordinator(config)
    results = await coordinator.run_load_test()

    # Guardar resultados
    coordinator.save_results()

    # Generar y mostrar reporte
    report = coordinator.generate_report()
    print(report)

    return results


def create_default_load_test_config() -> LoadTestConfig:
    """Crear configuración por defecto para pruebas de carga."""
    return LoadTestConfig(
        total_nodes=1000,
        concurrent_connections=100,
        test_duration_seconds=300,
        message_size_kb=50,
        network_latency_ms=50,
        packet_loss_rate=0.01,
        enable_network_simulation=True,
        enable_metrics_collection=True
    )


async def run_scalability_test(nodes: int = 1000, duration: int = 300) -> LoadTestResults:
    """Ejecutar prueba de escalabilidad con parámetros simplificados."""
    config = LoadTestConfig(
        total_nodes=nodes,
        test_duration_seconds=duration,
        concurrent_connections=min(200, nodes // 10),  # Máximo 200 conexiones concurrentes
    )

    logger.info(f"Running scalability test: {nodes} nodes, {duration}s duration")
    return await run_load_test(config)