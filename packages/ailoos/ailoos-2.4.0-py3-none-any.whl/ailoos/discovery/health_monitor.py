"""
Health Monitor for Ailoos Federated Learning Nodes
Monitors node health, performance, and reliability in real-time.
"""

import asyncio
import time
import statistics
import psutil
import socket
import os
from typing import Dict, Any, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

if TYPE_CHECKING:
    from .node_discovery import NodeDiscovery, DiscoveredNode

from .node_registry import NodeRegistry, NodeRegistration
# Removed circular import - NodeDiscovery will be passed as parameter

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("ℹ️ prometheus_client not available - metrics export disabled")


class NodeStatus(Enum):
    """Estados posibles de un nodo"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class HealthStatus(Enum):
    """Estados de salud de un nodo"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Severidad de alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetrics:
    """Métricas de salud de un nodo"""
    node_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Conectividad
    connectivity_score: float = 0.0
    last_seen: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    uptime_ratio: float = 0.0

    # Rendimiento
    performance_score: float = 0.0
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    network_latency_ms: Optional[float] = None

    # Estabilidad
    stability_score: float = 0.0
    crash_count: int = 0
    error_rate: float = 0.0
    session_success_rate: float = 0.0

    # Contribuciones federadas
    contribution_score: float = 0.0
    total_contributions: int = 0
    successful_contributions: int = 0
    average_contribution_time: Optional[float] = None

    # Estado general
    overall_health: HealthStatus = HealthStatus.UNKNOWN
    consecutive_failures: int = 0
    last_health_check: Optional[datetime] = None

    # Historial reciente
    response_times_history: List[float] = field(default_factory=list)
    performance_history: List[float] = field(default_factory=list)

    def update_connectivity(self, response_time: Optional[float], success: bool):
        """Actualizar métricas de conectividad"""
        self.last_seen = datetime.now()
        self.last_health_check = datetime.now()

        if response_time is not None:
            self.response_time_ms = response_time
            self.response_times_history.append(response_time)
            # Mantener solo últimas 100 mediciones
            if len(self.response_times_history) > 100:
                self.response_times_history.pop(0)

        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

        # Calcular score de conectividad
        self._calculate_connectivity_score()

    def update_performance(self, cpu_usage: Optional[float], memory_usage: Optional[float],
                          network_latency: Optional[float]):
        """Actualizar métricas de rendimiento"""
        self.cpu_usage_percent = cpu_usage
        self.memory_usage_percent = memory_usage
        self.network_latency_ms = network_latency

        # Agregar a historial
        perf_score = self._calculate_performance_score()
        self.performance_history.append(perf_score)
        if len(self.performance_history) > 50:
            self.performance_history.pop(0)

        self._calculate_performance_score()

    def update_contributions(self, success: bool, contribution_time: Optional[float]):
        """Actualizar métricas de contribuciones"""
        self.total_contributions += 1
        if success:
            self.successful_contributions += 1

        if contribution_time is not None:
            if self.average_contribution_time is None:
                self.average_contribution_time = contribution_time
            else:
                # Media móvil
                self.average_contribution_time = (
                    self.average_contribution_time * 0.9 + contribution_time * 0.1
                )

        self.session_success_rate = (
            self.successful_contributions / self.total_contributions
            if self.total_contributions > 0 else 0.0
        )

        self._calculate_contribution_score()

    def _calculate_connectivity_score(self) -> float:
        """Calcular score de conectividad (0-1)"""
        if not self.response_times_history:
            self.connectivity_score = 0.0
            return 0.0

        # Score basado en latencia media y fallos consecutivos
        avg_response = statistics.mean(self.response_times_history)
        max_response = max(self.response_times_history)

        # Penalizar latencias altas (>500ms = malo, >1000ms = crítico)
        latency_penalty = min(avg_response / 1000.0, 1.0)

        # Penalizar fallos consecutivos
        failure_penalty = min(self.consecutive_failures / 5.0, 1.0)

        self.connectivity_score = max(0.0, 1.0 - latency_penalty - failure_penalty)
        return self.connectivity_score

    def _calculate_performance_score(self) -> float:
        """Calcular score de rendimiento (0-1)"""
        scores = []

        if self.cpu_usage_percent is not None:
            # CPU < 80% = bueno
            cpu_score = max(0.0, 1.0 - (self.cpu_usage_percent / 100.0) * 1.25)
            scores.append(cpu_score)

        if self.memory_usage_percent is not None:
            # Memoria < 90% = bueno
            mem_score = max(0.0, 1.0 - (self.memory_usage_percent / 100.0) * 1.11)
            scores.append(mem_score)

        if self.network_latency_ms is not None:
            # Latencia < 100ms = buena
            net_score = max(0.0, 1.0 - (self.network_latency_ms / 1000.0))
            scores.append(net_score)

        self.performance_score = statistics.mean(scores) if scores else 0.5
        return self.performance_score

    def _calculate_contribution_score(self) -> float:
        """Calcular score de contribuciones (0-1)"""
        if self.total_contributions == 0:
            self.contribution_score = 0.5  # Neutral para nodos nuevos
            return 0.5

        # Score basado en tasa de éxito y tiempo promedio
        success_score = self.session_success_rate

        time_score = 1.0
        if self.average_contribution_time is not None:
            # Penalizar tiempos > 300 segundos
            time_score = max(0.0, 1.0 - (self.average_contribution_time / 300.0))

        self.contribution_score = (success_score * 0.7 + time_score * 0.3)
        return self.contribution_score

    def calculate_overall_health(self) -> HealthStatus:
        """Calcular estado de salud general"""
        if not self.last_health_check:
            return HealthStatus.UNKNOWN

        # Verificar si el nodo está demasiado tiempo sin reportar
        time_since_check = datetime.now() - self.last_health_check
        if time_since_check > timedelta(minutes=5):
            return HealthStatus.CRITICAL

        # Calcular score compuesto
        weights = {
            'connectivity': 0.3,
            'performance': 0.25,
            'contribution': 0.25,
            'stability': 0.2
        }

        # Calcular estabilidad basada en fallos y errores
        stability_score = max(0.0, 1.0 - (self.error_rate + self.consecutive_failures / 10.0))
        self.stability_score = stability_score

        overall_score = (
            weights['connectivity'] * self.connectivity_score +
            weights['performance'] * self.performance_score +
            weights['contribution'] * self.contribution_score +
            weights['stability'] * stability_score
        )

        # Determinar estado basado en score
        if overall_score >= 0.8:
            self.overall_health = HealthStatus.HEALTHY
        elif overall_score >= 0.6:
            self.overall_health = HealthStatus.DEGRADED
        elif overall_score >= 0.3:
            self.overall_health = HealthStatus.UNHEALTHY
        else:
            self.overall_health = HealthStatus.CRITICAL

        return self.overall_health

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        data = asdict(self)
        data['overall_health'] = self.overall_health.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.last_seen:
            data['last_seen'] = self.last_seen.isoformat()
        if self.last_health_check:
            data['last_health_check'] = self.last_health_check.isoformat()
        return data


@dataclass
class HealthAlert:
    """Alerta de salud"""
    alert_id: str
    node_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve(self):
        """Marcar alerta como resuelta"""
        self.resolved = True
        self.resolved_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


class AnomalyDetector:
    """
    Detector de anomalías en métricas de salud
    """

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Desviaciones estándar para detectar anomalías
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.min_samples_for_baseline = 10

    def update_baseline(self, node_id: str, metrics: HealthMetrics):
        """Actualizar línea base para un nodo"""
        if node_id not in self.baseline_metrics:
            self.baseline_metrics[node_id] = {}

        # Actualizar promedios para métricas numéricas
        numeric_fields = [
            'response_time_ms', 'cpu_usage_percent', 'memory_usage_percent',
            'network_latency_ms', 'error_rate', 'average_contribution_time'
        ]

        for field in numeric_fields:
            value = getattr(metrics, field)
            if value is not None:
                if field not in self.baseline_metrics[node_id]:
                    self.baseline_metrics[node_id][field] = {'values': [], 'mean': 0.0, 'std': 0.0}

                baseline = self.baseline_metrics[node_id][field]
                baseline['values'].append(value)

                # Mantener solo últimas 100 muestras
                if len(baseline['values']) > 100:
                    baseline['values'].pop(0)

                # Recalcular estadísticas si tenemos suficientes muestras
                if len(baseline['values']) >= self.min_samples_for_baseline:
                    baseline['mean'] = statistics.mean(baseline['values'])
                    baseline['std'] = statistics.stdev(baseline['values']) if len(baseline['values']) > 1 else 0.0

    def detect_anomalies(self, node_id: str, metrics: HealthMetrics) -> List[str]:
        """Detectar anomalías en métricas"""
        anomalies = []

        if node_id not in self.baseline_metrics:
            return anomalies

        baseline = self.baseline_metrics[node_id]

        # Verificar cada métrica
        checks = [
            ('response_time_ms', 'High response time', lambda v, b: v > b['mean'] + self.sensitivity * b['std']),
            ('cpu_usage_percent', 'High CPU usage', lambda v, b: v > b['mean'] + self.sensitivity * b['std']),
            ('memory_usage_percent', 'High memory usage', lambda v, b: v > b['mean'] + self.sensitivity * b['std']),
            ('network_latency_ms', 'High network latency', lambda v, b: v > b['mean'] + self.sensitivity * b['std']),
            ('error_rate', 'High error rate', lambda v, b: v > b['mean'] + self.sensitivity * b['std']),
        ]

        for field, description, condition in checks:
            value = getattr(metrics, field)
            if value is not None and field in baseline:
                b = baseline[field]
                if len(b['values']) >= self.min_samples_for_baseline and b['std'] > 0:
                    if condition(value, b):
                        anomalies.append(f"{description}: {value:.2f} (baseline: {b['mean']:.2f} ± {b['std']:.2f})")

        # Verificar caídas en conectividad
        if metrics.connectivity_score < 0.3:
            anomalies.append(f"Critical connectivity degradation: {metrics.connectivity_score:.2f}")

        # Verificar tasa de éxito baja
        if metrics.session_success_rate < 0.5 and metrics.total_contributions > 5:
            anomalies.append(f"Low contribution success rate: {metrics.session_success_rate:.2%}")

        return anomalies


class HealthMonitor:
    """
    Monitor de salud para nodos federados
    """

    def __init__(self, node_registry: Optional[NodeRegistry] = None,
                  node_discovery: Optional["NodeDiscovery"] = None,
                  prometheus_port: int = 8000):
        self.node_registry = node_registry
        self.node_discovery = node_discovery

        # Estado del monitor
        self.is_running = False
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}

        # Configuración
        self.health_check_interval = 30  # segundos
        self.alert_cooldown = timedelta(minutes=5)  # Evitar spam de alertas
        self.critical_timeout = timedelta(minutes=2)  # Timeout para marcar crítico
        self.anomaly_detector = AnomalyDetector()

        # Estadísticas
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'alerts_generated': 0,
            'nodes_monitored': 0
        }

        # Callbacks para alertas
        self.alert_callbacks: List[callable] = []

        # Métricas Prometheus
        self.prometheus_port = prometheus_port
        self._setup_prometheus_metrics()

    def _setup_prometheus_metrics(self):
        """Configurar métricas Prometheus"""
        if not PROMETHEUS_AVAILABLE:
            return

        # Métricas de salud de nodos
        self.node_health_status = Gauge(
            'ailoos_node_health_status',
            'Health status of nodes (0=unknown, 1=healthy, 2=degraded, 3=unhealthy, 4=critical)',
            ['node_id']
        )

        self.node_connectivity_score = Gauge(
            'ailoos_node_connectivity_score',
            'Connectivity score of nodes (0-1)',
            ['node_id']
        )

        self.node_performance_score = Gauge(
            'ailoos_node_performance_score',
            'Performance score of nodes (0-1)',
            ['node_id']
        )

        self.node_cpu_usage = Gauge(
            'ailoos_node_cpu_usage_percent',
            'CPU usage percentage of nodes',
            ['node_id']
        )

        self.node_memory_usage = Gauge(
            'ailoos_node_memory_usage_percent',
            'Memory usage percentage of nodes',
            ['node_id']
        )

        self.node_response_time = Gauge(
            'ailoos_node_response_time_ms',
            'Response time in milliseconds',
            ['node_id']
        )

        # Métricas del monitor
        self.monitor_total_checks = Counter(
            'ailoos_monitor_total_checks',
            'Total number of health checks performed'
        )

        self.monitor_successful_checks = Counter(
            'ailoos_monitor_successful_checks',
            'Number of successful health checks'
        )

        self.monitor_failed_checks = Counter(
            'ailoos_monitor_failed_checks',
            'Number of failed health checks'
        )

        self.monitor_active_alerts = Gauge(
            'ailoos_monitor_active_alerts',
            'Number of active alerts'
        )

        # Métricas del sistema local
        self.system_cpu_usage = Gauge(
            'ailoos_system_cpu_usage_percent',
            'Local system CPU usage percentage'
        )

        self.system_memory_usage = Gauge(
            'ailoos_system_memory_usage_percent',
            'Local system memory usage percentage'
        )

        self.system_uptime = Gauge(
            'ailoos_system_uptime_seconds',
            'Local system uptime in seconds'
        )

    async def start_monitoring(self):
        """Iniciar monitoreo de salud"""
        if self.is_running:
            logger.warning("⚠️ Health monitor already running")
            return

        self.is_running = True
        logger.info("🚀 Starting health monitoring...")

        # Iniciar servidor Prometheus si está disponible
        if PROMETHEUS_AVAILABLE:
            try:
                start_http_server(self.prometheus_port)
                logger.info(f"📊 Prometheus metrics server started on port {self.prometheus_port}")
            except Exception as e:
                logger.warning(f"Failed to start Prometheus server: {e}")

        # Iniciar tareas de monitoreo
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._alert_monitor_loop())
        asyncio.create_task(self._cleanup_old_alerts())
        asyncio.create_task(self._system_metrics_loop())

    async def stop_monitoring(self):
        """Detener monitoreo de salud"""
        self.is_running = False
        logger.info("🛑 Health monitoring stopped")

    async def _health_check_loop(self):
        """Loop principal de health checks"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)

    async def _perform_health_checks(self):
        """Realizar health checks en todos los nodos"""
        nodes_to_check = await self._get_nodes_to_monitor()

        if not nodes_to_check:
            return

        self.stats['nodes_monitored'] = len(nodes_to_check)

        # Realizar checks en paralelo con límite de concurrencia
        semaphore = asyncio.Semaphore(10)  # Máximo 10 checks simultáneos

        async def check_node(node_info: Tuple[str, Any]):
            async with semaphore:
                node_id, node_data = node_info
                await self._check_node_health(node_id, node_data)

        tasks = [check_node(node) for node in nodes_to_check.items()]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"✅ Health checks completed for {len(nodes_to_check)} nodes")

    async def _get_nodes_to_monitor(self) -> Dict[str, Any]:
        """Obtener lista de nodos a monitorear"""
        nodes = {}

        # Obtener nodos del registry si está disponible
        if self.node_registry:
            registry_nodes = await self.node_registry.list_nodes()
            for node in registry_nodes:
                if node.status in [NodeStatus.ACTIVE, NodeStatus.INACTIVE]:
                    nodes[node.node_id] = node

        # Obtener nodos del discovery si está disponible
        if self.node_discovery:
            discovery_nodes = self.node_discovery.get_online_nodes()
            for node in discovery_nodes:
                if node.node_id not in nodes:
                    nodes[node.node_id] = node

        return nodes

    async def _check_node_health(self, node_id: str, node_data: Any):
        """Verificar salud de un nodo específico"""
        self.stats['total_checks'] += 1

        # Obtener o crear métricas para este nodo
        if node_id not in self.health_metrics:
            self.health_metrics[node_id] = HealthMetrics(node_id=node_id)

        metrics = self.health_metrics[node_id]

        try:
            # Realizar health check
            start_time = time.time()
            success, response_time, node_metrics = await self._perform_node_health_check(node_id, node_data)
            check_time = (time.time() - start_time) * 1000  # ms

            # Actualizar métricas
            metrics.update_connectivity(response_time if success else None, success)

            if success and node_metrics:
                metrics.update_performance(
                    node_metrics.get('cpu_usage'),
                    node_metrics.get('memory_usage'),
                    node_metrics.get('network_latency')
                )

            # Calcular estado general
            old_health = metrics.overall_health
            new_health = metrics.calculate_overall_health()

            # Detectar anomalías
            anomalies = self.anomaly_detector.detect_anomalies(node_id, metrics)
            self.anomaly_detector.update_baseline(node_id, metrics)

            # Actualizar métricas Prometheus
            if PROMETHEUS_AVAILABLE:
                health_value = {
                    HealthStatus.UNKNOWN: 0,
                    HealthStatus.HEALTHY: 1,
                    HealthStatus.DEGRADED: 2,
                    HealthStatus.UNHEALTHY: 3,
                    HealthStatus.CRITICAL: 4
                }.get(new_health, 0)

                self.node_health_status.labels(node_id=node_id).set(health_value)
                self.node_connectivity_score.labels(node_id=node_id).set(metrics.connectivity_score)
                self.node_performance_score.labels(node_id=node_id).set(metrics.performance_score)

                if metrics.cpu_usage_percent is not None:
                    self.node_cpu_usage.labels(node_id=node_id).set(metrics.cpu_usage_percent)
                if metrics.memory_usage_percent is not None:
                    self.node_memory_usage.labels(node_id=node_id).set(metrics.memory_usage_percent)
                if metrics.response_time_ms is not None:
                    self.node_response_time.labels(node_id=node_id).set(metrics.response_time_ms)

                # Actualizar contadores del monitor
                self.monitor_total_checks.inc()
                self.monitor_successful_checks.inc()
                self.monitor_active_alerts.set(len(self.active_alerts))

            # Generar alertas si es necesario
            await self._generate_alerts(node_id, metrics, old_health, new_health, anomalies)

            self.stats['successful_checks'] += 1

        except Exception as e:
            logger.warning(f"Failed to check health for node {node_id}: {e}")
            self.stats['failed_checks'] += 1
            metrics.update_connectivity(None, False)

            # Actualizar métricas Prometheus para checks fallidos
            if PROMETHEUS_AVAILABLE:
                self.monitor_total_checks.inc()
                self.monitor_failed_checks.inc()
                self.monitor_active_alerts.set(len(self.active_alerts))

    async def _perform_node_health_check(self, node_id: str, node_data: Any) -> Tuple[bool, Optional[float], Optional[Dict[str, Any]]]:
        """
        Realizar health check real en un nodo
        Returns: (success, response_time_ms, metrics_dict)
        """
        # En una implementación real, esto haría una llamada HTTP/gRPC al nodo
        # Por ahora, simulamos basado en datos disponibles

        start_time = time.time()

        try:
            # Simular latencia de red
            await asyncio.sleep(0.01)  # 10ms simulado

            # Simular métricas basadas en datos del nodo
            if hasattr(node_data, 'hardware_specs'):
                # Nodo del registry
                cpu_usage = 60 + (hash(node_id) % 40)  # 60-99%
                memory_usage = 50 + (hash(node_id + 'mem') % 40)  # 50-89%
                network_latency = 10 + (hash(node_id + 'net') % 90)  # 10-99ms
            else:
                # Nodo del discovery
                cpu_usage = 70
                memory_usage = 65
                network_latency = 25

            response_time = (time.time() - start_time) * 1000

            metrics = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'network_latency': network_latency
            }

            # Simular fallos ocasionales (5% de probabilidad)
            success = (hash(node_id + str(int(time.time() / 300))) % 100) > 5

            return success, response_time, metrics if success else None

        except Exception as e:
            logger.debug(f"Health check failed for {node_id}: {e}")
            response_time = (time.time() - start_time) * 1000
            return False, response_time, None

    async def ping_node(self, node_id: str, host: str, port: Optional[int] = None, timeout: float = 5.0) -> Tuple[bool, Optional[float]]:
        """
        Realizar ping a un nodo para verificar conectividad

        Args:
            node_id: ID del nodo
            host: Dirección IP o hostname
            port: Puerto (opcional)
            timeout: Timeout en segundos

        Returns:
            (success, response_time_ms)
        """
        try:
            start_time = time.time()

            # Intentar conexión TCP si hay puerto
            if port:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = await asyncio.get_event_loop().sock_connect(sock, (host, port))
                    sock.close()
                    response_time = (time.time() - start_time) * 1000
                    return True, response_time
                except (socket.timeout, socket.error):
                    return False, None
            else:
                # Ping ICMP simple (requiere permisos)
                try:
                    import subprocess
                    result = await asyncio.create_subprocess_exec(
                        'ping', '-c', '1', '-W', str(int(timeout)), host,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    await result.wait()
                    response_time = (time.time() - start_time) * 1000
                    return result.returncode == 0, response_time if result.returncode == 0 else None
                except Exception:
                    # Fallback: intentar resolver DNS
                    try:
                        await asyncio.get_event_loop().getaddrinfo(host, None)
                        response_time = (time.time() - start_time) * 1000
                        return True, response_time
                    except Exception:
                        return False, None

        except Exception as e:
            logger.debug(f"Ping failed for {node_id} ({host}:{port}): {e}")
            return False, None

    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Recopilar métricas del sistema local usando psutil

        Returns:
            Diccionario con métricas del sistema
        """
        try:
            metrics = {
                'timestamp': datetime.now(),
                'cpu': {
                    'usage_percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                    'freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else None,
                },
                'memory': {
                    'total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                    'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                    'used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
                    'usage_percent': psutil.virtual_memory().percent,
                },
                'disk': {
                    'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                    'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                    'used_gb': round(psutil.disk_usage('/').used / (1024**3), 2),
                    'usage_percent': psutil.disk_usage('/').percent,
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv,
                    'packets_sent': psutil.net_io_counters().packets_sent,
                    'packets_recv': psutil.net_io_counters().packets_recv,
                },
                'uptime_seconds': time.time() - psutil.boot_time(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            }

            # Actualizar métricas Prometheus si disponibles
            if PROMETHEUS_AVAILABLE:
                self.system_cpu_usage.set(metrics['cpu']['usage_percent'])
                self.system_memory_usage.set(metrics['memory']['usage_percent'])
                self.system_uptime.set(metrics['uptime_seconds'])

            return metrics

        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }

    async def notify_coordinator(self, alert: HealthAlert, coordinator_url: Optional[str] = None) -> bool:
        """
        Notificar al coordinador sobre alertas de salud

        Args:
            alert: Alerta a notificar
            coordinator_url: URL del coordinador (opcional)

        Returns:
            True si la notificación fue exitosa
        """
        try:
            if not coordinator_url:
                # Intentar obtener URL del coordinador de configuración o entorno
                coordinator_url = os.getenv('AILOOS_COORDINATOR_URL', 'http://localhost:8000')

            import aiohttp

            notification_data = {
                'type': 'health_alert',
                'alert': alert.to_dict(),
                'timestamp': datetime.now().isoformat(),
                'source_node': getattr(self, 'node_id', 'unknown')
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{coordinator_url}/api/health/alerts",
                    json=notification_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Alert notified to coordinator: {alert.title}")
                        return True
                    else:
                        logger.warning(f"Failed to notify coordinator: HTTP {response.status}")
                        return False

        except Exception as e:
            logger.warning(f"Failed to notify coordinator: {e}")
            return False

    async def _generate_alerts(self, node_id: str, metrics: HealthMetrics,
                              old_health: HealthStatus, new_health: HealthStatus,
                              anomalies: List[str]):
        """Generar alertas basadas en cambios de salud"""

        # Alertas por cambio de estado
        if new_health != old_health:
            severity_map = {
                HealthStatus.CRITICAL: AlertSeverity.CRITICAL,
                HealthStatus.UNHEALTHY: AlertSeverity.ERROR,
                HealthStatus.DEGRADED: AlertSeverity.WARNING,
                HealthStatus.HEALTHY: AlertSeverity.INFO
            }

            severity = severity_map.get(new_health, AlertSeverity.INFO)
            title = f"Node {node_id} health changed to {new_health.value}"
            message = f"Health status changed from {old_health.value} to {new_health.value}"

            await self._create_alert(node_id, severity, title, message, {
                'old_health': old_health.value,
                'new_health': new_health.value,
                'connectivity_score': metrics.connectivity_score,
                'performance_score': metrics.performance_score
            })

        # Alertas por anomalías
        for anomaly in anomalies:
            await self._create_alert(
                node_id,
                AlertSeverity.WARNING,
                f"Anomaly detected for node {node_id}",
                anomaly,
                {'anomaly_type': 'metric_anomaly'}
            )

        # Alerta por fallos consecutivos
        if metrics.consecutive_failures >= 3:
            await self._create_alert(
                node_id,
                AlertSeverity.ERROR,
                f"Node {node_id} has {metrics.consecutive_failures} consecutive failures",
                f"Node is experiencing connectivity issues",
                {'consecutive_failures': metrics.consecutive_failures}
            )

    async def _create_alert(self, node_id: str, severity: AlertSeverity,
                           title: str, message: str, metadata: Dict[str, Any]):
        """Crear una nueva alerta"""

        # Verificar cooldown para evitar spam
        alert_key = f"{node_id}:{title}"
        if alert_key in self.active_alerts:
            last_alert = self.active_alerts[alert_key]
            if datetime.now() - last_alert.timestamp < self.alert_cooldown:
                return  # Alert aún en cooldown

        alert = HealthAlert(
            alert_id=f"alert_{node_id}_{int(time.time())}_{hash(title) % 1000}",
            node_id=node_id,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata
        )

        self.active_alerts[alert_key] = alert
        self.stats['alerts_generated'] += 1

        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.warning(f"Alert callback failed: {e}")

        # Notificar al coordinador
        await self.notify_coordinator(alert)

        logger.warning(f"🚨 {severity.value.upper()}: {title} - {message}")

    async def _alert_monitor_loop(self):
        """Monitorear y actualizar estado de alertas"""
        while self.is_running:
            try:
                await self._update_alert_states()
                await asyncio.sleep(60)  # Cada minuto
            except Exception as e:
                logger.error(f"Alert monitor error: {e}")
                await asyncio.sleep(30)

    async def _update_alert_states(self):
        """Actualizar estado de alertas activas"""
        now = datetime.now()
        resolved_keys = []

        for alert_key, alert in self.active_alerts.items():
            node_id = alert.node_id

            # Resolver alertas de nodos que se recuperaron
            if node_id in self.health_metrics:
                metrics = self.health_metrics[node_id]

                # Resolver alertas de conectividad si el nodo responde
                if 'connectivity' in alert.title.lower() and metrics.connectivity_score > 0.7:
                    alert.resolve()
                    resolved_keys.append(alert_key)

                # Resolver alertas de rendimiento si mejora
                elif 'performance' in alert.title.lower() and metrics.performance_score > 0.8:
                    alert.resolve()
                    resolved_keys.append(alert_key)

                # Resolver alertas de anomalías después de 10 minutos si no hay nuevas anomalías
                elif 'anomaly' in alert.title.lower() and (now - alert.timestamp) > timedelta(minutes=10):
                    alert.resolve()
                    resolved_keys.append(alert_key)

        # Limpiar alertas resueltas
        for key in resolved_keys:
            del self.active_alerts[key]

        if resolved_keys:
            logger.info(f"✅ Resolved {len(resolved_keys)} alerts")

    async def _cleanup_old_alerts(self):
        """Limpiar alertas antiguas"""
        while self.is_running:
            try:
                now = datetime.now()
                old_alerts = []

                for alert_key, alert in self.active_alerts.items():
                    # Alertas no resueltas después de 1 hora
                    if not alert.resolved and (now - alert.timestamp) > timedelta(hours=1):
                        old_alerts.append(alert_key)

                for key in old_alerts:
                    del self.active_alerts[key]

                if old_alerts:
                    logger.debug(f"🧹 Cleaned {len(old_alerts)} old alerts")

                await asyncio.sleep(600)  # Cada 10 minutos

            except Exception as e:
                logger.error(f"Alert cleanup error: {e}")
                await asyncio.sleep(60)

    async def _system_metrics_loop(self):
        """Loop para recopilar métricas del sistema local"""
        while self.is_running:
            try:
                # Recopilar métricas del sistema
                system_metrics = self.collect_system_metrics()

                # Log métricas críticas
                cpu_usage = system_metrics.get('cpu', {}).get('usage_percent', 0)
                mem_usage = system_metrics.get('memory', {}).get('usage_percent', 0)

                if cpu_usage > 90:
                    logger.warning(f"High CPU usage: {cpu_usage:.1f}%")
                if mem_usage > 95:
                    logger.warning(f"High memory usage: {mem_usage:.1f}%")

                await asyncio.sleep(60)  # Cada minuto

            except Exception as e:
                logger.error(f"System metrics loop error: {e}")
                await asyncio.sleep(30)

    def add_alert_callback(self, callback: callable):
        """Agregar callback para alertas"""
        self.alert_callbacks.append(callback)

    def get_node_health(self, node_id: str) -> Optional[HealthMetrics]:
        """Obtener métricas de salud de un nodo"""
        return self.health_metrics.get(node_id)

    def get_all_health_metrics(self) -> Dict[str, HealthMetrics]:
        """Obtener todas las métricas de salud"""
        return self.health_metrics.copy()

    def get_active_alerts(self) -> List[HealthAlert]:
        """Obtener alertas activas"""
        return list(self.active_alerts.values())

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Obtener resumen de salud del sistema"""
        if not self.health_metrics:
            return {'status': 'no_data'}

        total_nodes = len(self.health_metrics)
        healthy_nodes = sum(1 for m in self.health_metrics.values()
                           if m.overall_health == HealthStatus.HEALTHY)
        degraded_nodes = sum(1 for m in self.health_metrics.values()
                            if m.overall_health == HealthStatus.DEGRADED)
        unhealthy_nodes = sum(1 for m in self.health_metrics.values()
                             if m.overall_health in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL])

        avg_connectivity = statistics.mean(m.connectivity_score for m in self.health_metrics.values()
                                         if m.connectivity_score > 0) if self.health_metrics else 0
        avg_performance = statistics.mean(m.performance_score for m in self.health_metrics.values()
                                        if m.performance_score > 0) if self.health_metrics else 0

        # Determinar estado general del sistema
        if unhealthy_nodes > total_nodes * 0.3:  # >30% unhealthy
            system_status = 'critical'
        elif degraded_nodes > total_nodes * 0.5:  # >50% degraded
            system_status = 'degraded'
        elif healthy_nodes >= total_nodes * 0.8:  # >80% healthy
            system_status = 'healthy'
        else:
            system_status = 'warning'

        return {
            'status': system_status,
            'total_nodes': total_nodes,
            'healthy_nodes': healthy_nodes,
            'degraded_nodes': degraded_nodes,
            'unhealthy_nodes': unhealthy_nodes,
            'average_connectivity': round(avg_connectivity, 3),
            'average_performance': round(avg_performance, 3),
            'active_alerts': len(self.active_alerts),
            'last_updated': datetime.now().isoformat()
        }

    def get_monitor_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del monitor"""
        success_rate = (self.stats['successful_checks'] / self.stats['total_checks']
                       if self.stats['total_checks'] > 0 else 0)

        return {
            'is_running': self.is_running,
            'total_checks': self.stats['total_checks'],
            'successful_checks': self.stats['successful_checks'],
            'failed_checks': self.stats['failed_checks'],
            'success_rate': f"{success_rate:.2%}",
            'alerts_generated': self.stats['alerts_generated'],
            'nodes_monitored': self.stats['nodes_monitored'],
            'active_alerts': len(self.active_alerts),
            'health_metrics_tracked': len(self.health_metrics)
        }

    async def report_node_contribution(self, node_id: str, success: bool,
                                     contribution_time: Optional[float] = None):
        """Reportar resultado de contribución de un nodo"""
        if node_id not in self.health_metrics:
            self.health_metrics[node_id] = HealthMetrics(node_id=node_id)

        self.health_metrics[node_id].update_contributions(success, contribution_time)

    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Obtener métricas para optimización del sistema"""
        if not self.health_metrics:
            return {}

        # Calcular métricas de rendimiento del sistema
        connectivity_scores = [m.connectivity_score for m in self.health_metrics.values()
                              if m.connectivity_score > 0]
        performance_scores = [m.performance_score for m in self.health_metrics.values()
                             if m.performance_score > 0]
        contribution_scores = [m.contribution_score for m in self.health_metrics.values()
                              if m.contribution_score > 0]

        # Identificar nodos problemáticos
        problematic_nodes = []
        for node_id, metrics in self.health_metrics.items():
            if (metrics.overall_health in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL] or
                metrics.consecutive_failures > 2):
                problematic_nodes.append({
                    'node_id': node_id,
                    'health': metrics.overall_health.value,
                    'connectivity': metrics.connectivity_score,
                    'performance': metrics.performance_score,
                    'failures': metrics.consecutive_failures
                })

        return {
            'average_connectivity': statistics.mean(connectivity_scores) if connectivity_scores else 0,
            'average_performance': statistics.mean(performance_scores) if performance_scores else 0,
            'average_contribution_success': statistics.mean(contribution_scores) if contribution_scores else 0,
            'connectivity_std': statistics.stdev(connectivity_scores) if len(connectivity_scores) > 1 else 0,
            'performance_std': statistics.stdev(performance_scores) if len(performance_scores) > 1 else 0,
            'problematic_nodes': problematic_nodes,
            'system_reliability_score': self._calculate_system_reliability(),
            'recommended_actions': self._generate_optimization_recommendations()
        }

    def _calculate_system_reliability(self) -> float:
        """Calcular score de confiabilidad del sistema"""
        if not self.health_metrics:
            return 0.0

        health_weights = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.DEGRADED: 0.7,
            HealthStatus.UNHEALTHY: 0.3,
            HealthStatus.CRITICAL: 0.0,
            HealthStatus.UNKNOWN: 0.5
        }

        total_weight = 0
        total_score = 0

        for metrics in self.health_metrics.values():
            weight = 1.0  # Peso base
            score = health_weights.get(metrics.overall_health, 0.5)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generar recomendaciones de optimización"""
        recommendations = []

        summary = self.get_system_health_summary()

        if summary.get('status') == 'critical':
            recommendations.append("Critical system health - immediate intervention required")
        elif summary.get('status') == 'degraded':
            recommendations.append("System health degraded - monitor closely")

        if summary.get('average_connectivity', 0) < 0.7:
            recommendations.append("Poor average connectivity - check network infrastructure")

        if summary.get('average_performance', 0) < 0.6:
            recommendations.append("Low average performance - consider resource optimization")

        problematic_count = len([n for n in self.health_metrics.values()
                                if n.overall_health in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]])
        if problematic_count > 0:
            recommendations.append(f"Address {problematic_count} problematic nodes")

        return recommendations


# Instancia global del monitor
_health_monitor_instance = None

def get_health_monitor(node_registry: Optional[NodeRegistry] = None,
                      node_discovery: Optional["NodeDiscovery"] = None) -> HealthMonitor:
    """Obtener instancia global del health monitor"""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor(node_registry, node_discovery)
    return _health_monitor_instance

async def start_health_monitoring():
    """Iniciar servicio de monitoreo de salud"""
    monitor = get_health_monitor()
    await monitor.start_monitoring()

async def stop_health_monitoring():
    """Detener servicio de monitoreo de salud"""
    global _health_monitor_instance
    if _health_monitor_instance:
        await _health_monitor_instance.stop_monitoring()
        _health_monitor_instance = None