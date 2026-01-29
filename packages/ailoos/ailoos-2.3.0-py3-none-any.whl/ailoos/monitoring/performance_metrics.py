"""
Sistema de Métricas de Performance para AILOOS

Proporciona métricas detalladas de performance con integración Prometheus
y métricas específicas del sistema federado de IA.
"""

import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading
import logging

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available - metrics will be logged only")


@dataclass
class PerformanceSnapshot:
    """Snapshot de métricas de performance."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int
    open_files: int
    context_switches: int

    # Métricas específicas de AILOOS
    active_federated_sessions: int = 0
    pending_training_tasks: int = 0
    active_models: int = 0
    cache_hit_ratio: float = 0.0
    db_connection_pool_usage: float = 0.0
    ipfs_operations_pending: int = 0

    # Latencias
    avg_api_latency_ms: float = 0.0
    avg_db_query_latency_ms: float = 0.0
    avg_model_inference_latency_ms: float = 0.0


class PerformanceMetricsCollector:
    """
    Recolector de métricas de performance con integración Prometheus.

    Recopila métricas del sistema y componentes específicos de AILOOS,
    proporcionando tanto métricas en tiempo real como históricas.
    """

    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.snapshots: List[PerformanceSnapshot] = []
        self.max_snapshots = 1000
        self.collection_interval = 30  # seconds
        self._lock = threading.Lock()

        # Métricas de sistema
        self.system_metrics = {
            'cpu_percent': [],
            'memory_percent': [],
            'disk_usage_percent': [],
            'network_io': []
        }

        # Métricas específicas de AILOOS
        self.ailoos_metrics = {
            'federated_sessions': 0,
            'training_tasks': 0,
            'active_models': 0,
            'cache_stats': {'hits': 0, 'misses': 0},
            'db_pool_stats': {'used': 0, 'available': 10},
            'ipfs_queue': 0
        }

        # Latencies tracking
        self.latency_measurements = {
            'api_requests': [],
            'db_queries': [],
            'model_inference': []
        }

        # Callbacks para métricas custom
        self.metric_callbacks: Dict[str, Callable] = {}

        # Inicializar Prometheus metrics si está disponible
        if self.enable_prometheus:
            self._init_prometheus_metrics()

        logger.info(f"PerformanceMetricsCollector initialized (Prometheus: {self.enable_prometheus})")

    def _init_prometheus_metrics(self):
        """Inicializar métricas de Prometheus."""
        self.registry = CollectorRegistry()

        # System metrics
        self.cpu_gauge = Gauge('ailoos_cpu_percent', 'CPU usage percentage', registry=self.registry)
        self.memory_gauge = Gauge('ailoos_memory_percent', 'Memory usage percentage', registry=self.registry)
        self.disk_gauge = Gauge('ailoos_disk_percent', 'Disk usage percentage', registry=self.registry)

        # Network metrics
        self.network_sent_counter = Counter('ailoos_network_bytes_sent', 'Network bytes sent', registry=self.registry)
        self.network_recv_counter = Counter('ailoos_network_bytes_recv', 'Network bytes received', registry=self.registry)

        # AILOOS specific metrics
        self.federated_sessions_gauge = Gauge('ailoos_federated_sessions_active', 'Active federated sessions', registry=self.registry)
        self.training_tasks_gauge = Gauge('ailoos_training_tasks_pending', 'Pending training tasks', registry=self.registry)
        self.active_models_gauge = Gauge('ailoos_models_active', 'Active models loaded', registry=self.registry)
        self.cache_hit_ratio_gauge = Gauge('ailoos_cache_hit_ratio', 'Cache hit ratio', registry=self.registry)

        # Latency histograms
        self.api_latency_histogram = Histogram('ailoos_api_request_duration_seconds', 'API request duration', registry=self.registry)
        self.db_latency_histogram = Histogram('ailoos_db_query_duration_seconds', 'Database query duration', registry=self.registry)
        self.inference_latency_histogram = Histogram('ailoos_model_inference_duration_seconds', 'Model inference duration', registry=self.registry)

        # Business metrics
        self.dracma_transactions_counter = Counter('ailoos_dracma_transactions_total', 'Total DracmaS transactions', registry=self.registry)
        self.api_requests_counter = Counter('ailoos_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])

    async def start_collection(self):
        """Iniciar recolección periódica de métricas."""
        logger.info("Starting performance metrics collection")
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting performance metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self):
        """Recolectar métricas del sistema."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            # Process-specific metrics
            process = psutil.Process()
            threads = process.num_threads()
            try:
                open_files = len(process.open_files())
            except:
                open_files = 0

            context_switches = process.num_ctx_switches()

            # AILOOS specific metrics (from callbacks)
            federated_sessions = await self._get_metric_value('federated_sessions', 0)
            training_tasks = await self._get_metric_value('training_tasks', 0)
            active_models = await self._get_metric_value('active_models', 0)
            cache_stats = await self._get_metric_value('cache_stats', {'hits': 0, 'misses': 0})
            db_pool = await self._get_metric_value('db_pool_stats', {'used': 0, 'available': 10})
            ipfs_queue = await self._get_metric_value('ipfs_queue', 0)

            # Calculate cache hit ratio
            cache_hits = cache_stats.get('hits', 0)
            cache_misses = cache_stats.get('misses', 0)
            total_cache_ops = cache_hits + cache_misses
            cache_hit_ratio = (cache_hits / total_cache_ops) if total_cache_ops > 0 else 0.0

            # Calculate DB pool usage
            db_used = db_pool.get('used', 0)
            db_available = db_pool.get('available', 10)
            db_pool_usage = (db_used / (db_used + db_available)) if (db_used + db_available) > 0 else 0.0

            # Calculate average latencies
            avg_api_latency = self._calculate_avg_latency('api_requests')
            avg_db_latency = self._calculate_avg_latency('db_queries')
            avg_inference_latency = self._calculate_avg_latency('model_inference')

            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                disk_usage_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_threads=threads,
                open_files=open_files,
                context_switches=context_switches.voluntary + context_switches.involuntary,

                # AILOOS metrics
                active_federated_sessions=federated_sessions,
                pending_training_tasks=training_tasks,
                active_models=active_models,
                cache_hit_ratio=cache_hit_ratio,
                db_connection_pool_usage=db_pool_usage,
                ipfs_operations_pending=ipfs_queue,

                # Latencies
                avg_api_latency_ms=avg_api_latency,
                avg_db_query_latency_ms=avg_db_latency,
                avg_model_inference_latency_ms=avg_inference_latency
            )

            # Store snapshot
            with self._lock:
                self.snapshots.append(snapshot)
                if len(self.snapshots) > self.max_snapshots:
                    self.snapshots.pop(0)

                # Update rolling averages
                self._update_rolling_averages(snapshot)

            # Update Prometheus metrics
            if self.enable_prometheus:
                self._update_prometheus_metrics(snapshot)

            logger.debug(f"Collected performance metrics: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%")

        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")

    def _calculate_avg_latency(self, metric_type: str) -> float:
        """Calcular latencia promedio para un tipo de métrica."""
        measurements = self.latency_measurements.get(metric_type, [])
        if not measurements:
            return 0.0

        # Keep only last 100 measurements
        if len(measurements) > 100:
            measurements = measurements[-100:]

        return sum(measurements) / len(measurements)

    def _update_rolling_averages(self, snapshot: PerformanceSnapshot):
        """Actualizar promedios móviles."""
        # System metrics rolling averages
        for metric_name, values in self.system_metrics.items():
            if len(values) >= 10:  # Keep last 10 values
                values.pop(0)

        self.system_metrics['cpu_percent'].append(snapshot.cpu_percent)
        self.system_metrics['memory_percent'].append(snapshot.memory_percent)
        self.system_metrics['disk_usage_percent'].append(snapshot.disk_usage_percent)

    def _update_prometheus_metrics(self, snapshot: PerformanceSnapshot):
        """Actualizar métricas de Prometheus."""
        self.cpu_gauge.set(snapshot.cpu_percent)
        self.memory_gauge.set(snapshot.memory_percent)
        self.disk_gauge.set(snapshot.disk_usage_percent)

        self.federated_sessions_gauge.set(snapshot.active_federated_sessions)
        self.training_tasks_gauge.set(snapshot.pending_training_tasks)
        self.active_models_gauge.set(snapshot.active_models)
        self.cache_hit_ratio_gauge.set(snapshot.cache_hit_ratio)

    async def _get_metric_value(self, metric_name: str, default_value: Any) -> Any:
        """Obtener valor de métrica desde callback."""
        callback = self.metric_callbacks.get(metric_name)
        if callback:
            try:
                return await callback()
            except Exception as e:
                logger.error(f"Error getting metric {metric_name}: {e}")
                return default_value
        return default_value

    def register_metric_callback(self, metric_name: str, callback: Callable):
        """Registrar callback para métrica custom."""
        self.metric_callbacks[metric_name] = callback
        logger.info(f"Registered metric callback: {metric_name}")

    def record_api_latency(self, latency_ms: float):
        """Registrar latencia de API."""
        with self._lock:
            self.latency_measurements['api_requests'].append(latency_ms)
            if len(self.latency_measurements['api_requests']) > 1000:
                self.latency_measurements['api_requests'] = self.latency_measurements['api_requests'][-1000:]

        if self.enable_prometheus:
            self.api_latency_histogram.observe(latency_ms / 1000)  # Convert to seconds

    def record_db_latency(self, latency_ms: float):
        """Registrar latencia de base de datos."""
        with self._lock:
            self.latency_measurements['db_queries'].append(latency_ms)
            if len(self.latency_measurements['db_queries']) > 1000:
                self.latency_measurements['db_queries'] = self.latency_measurements['db_queries'][-1000:]

        if self.enable_prometheus:
            self.db_latency_histogram.observe(latency_ms / 1000)

    def record_inference_latency(self, latency_ms: float):
        """Registrar latencia de inferencia de modelo."""
        with self._lock:
            self.latency_measurements['model_inference'].append(latency_ms)
            if len(self.latency_measurements['model_inference']) > 1000:
                self.latency_measurements['model_inference'] = self.latency_measurements['model_inference'][-1000:]

        if self.enable_prometheus:
            self.inference_latency_histogram.observe(latency_ms / 1000)

    def record_dracma_transaction(self, amount: float, transaction_type: str = "transfer"):
        """Registrar transacción DRACMA."""
        if self.enable_prometheus:
            self.dracma_transactions_counter.labels(type=transaction_type).inc(amount)

    def record_api_request(self, method: str, endpoint: str, status_code: int):
        """Registrar request de API."""
        if self.enable_prometheus:
            self.api_requests_counter.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()

    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales."""
        with self._lock:
            if not self.snapshots:
                return {}

            latest = self.snapshots[-1]

            return {
                'timestamp': latest.timestamp.isoformat(),
                'system': {
                    'cpu_percent': latest.cpu_percent,
                    'memory_percent': latest.memory_percent,
                    'memory_used_gb': latest.memory_used_gb,
                    'disk_usage_percent': latest.disk_usage_percent,
                    'active_threads': latest.active_threads,
                    'open_files': latest.open_files
                },
                'ailoos': {
                    'active_federated_sessions': latest.active_federated_sessions,
                    'pending_training_tasks': latest.pending_training_tasks,
                    'active_models': latest.active_models,
                    'cache_hit_ratio': latest.cache_hit_ratio,
                    'db_connection_pool_usage': latest.db_connection_pool_usage,
                    'ipfs_operations_pending': latest.ipfs_operations_pending
                },
                'performance': {
                    'avg_api_latency_ms': latest.avg_api_latency_ms,
                    'avg_db_query_latency_ms': latest.avg_db_query_latency_ms,
                    'avg_model_inference_latency_ms': latest.avg_model_inference_latency_ms
                }
            }

    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Obtener historial de métricas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_snapshots = [
                s for s in self.snapshots
                if s.timestamp >= cutoff_time
            ]

            return [
                {
                    'timestamp': s.timestamp.isoformat(),
                    'cpu_percent': s.cpu_percent,
                    'memory_percent': s.memory_percent,
                    'federated_sessions': s.active_federated_sessions,
                    'api_latency': s.avg_api_latency_ms,
                    'cache_hit_ratio': s.cache_hit_ratio
                }
                for s in recent_snapshots
            ]

    def get_prometheus_metrics(self) -> str:
        """Obtener métricas en formato Prometheus."""
        if not self.enable_prometheus:
            return "# Prometheus metrics not available"

        return generate_latest(self.registry).decode('utf-8')

    def get_performance_report(self) -> Dict[str, Any]:
        """Generar reporte completo de performance."""
        with self._lock:
            if not self.snapshots:
                return {'error': 'No metrics available'}

            # Calculate averages from recent snapshots (last hour)
            recent_snapshots = [
                s for s in self.snapshots
                if (datetime.now() - s.timestamp).total_seconds() < 3600
            ]

            if not recent_snapshots:
                recent_snapshots = self.snapshots[-10:]  # Fallback to last 10

            # Calculate averages
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_federated_sessions = sum(s.active_federated_sessions for s in recent_snapshots) / len(recent_snapshots)
            avg_api_latency = sum(s.avg_api_latency_ms for s in recent_snapshots) / len(recent_snapshots)

            # Performance score (0-100)
            performance_score = 100.0
            performance_score -= min(avg_cpu / 2, 40)  # CPU impact
            performance_score -= min(avg_memory / 2, 30)  # Memory impact
            performance_score -= min(avg_api_latency / 10, 20)  # Latency impact
            performance_score = max(0, performance_score)

            return {
                'period': f"{len(recent_snapshots)} snapshots",
                'averages': {
                    'cpu_percent': round(avg_cpu, 1),
                    'memory_percent': round(avg_memory, 1),
                    'federated_sessions': round(avg_federated_sessions, 1),
                    'api_latency_ms': round(avg_api_latency, 1)
                },
                'performance_score': round(performance_score, 1),
                'recommendations': self._generate_performance_recommendations(
                    avg_cpu, avg_memory, avg_api_latency
                ),
                'generated_at': datetime.now().isoformat()
            }

    def _generate_performance_recommendations(self, cpu: float, memory: float, latency: float) -> List[str]:
        """Generar recomendaciones basadas en métricas."""
        recommendations = []

        if cpu > 80:
            recommendations.append("⚠️ Alto uso de CPU - Considerar escalado horizontal")
        if memory > 85:
            recommendations.append("⚠️ Alto uso de memoria - Revisar leaks de memoria")
        if latency > 500:
            recommendations.append("⚠️ Alta latencia API - Optimizar queries y caching")

        if not recommendations:
            recommendations.append("✅ Performance óptima - Sistema funcionando correctamente")

        return recommendations


# Instancia global del collector
_performance_collector = PerformanceMetricsCollector()


def get_performance_collector() -> PerformanceMetricsCollector:
    """Obtener instancia global del collector de métricas."""
    return _performance_collector


# Funciones de conveniencia para fácil uso

def record_api_latency(latency_ms: float):
    """Registrar latencia de API."""
    _performance_collector.record_api_latency(latency_ms)


def record_db_latency(latency_ms: float):
    """Registrar latencia de DB."""
    _performance_collector.record_db_latency(latency_ms)


def record_inference_latency(latency_ms: float):
    """Registrar latencia de inferencia."""
    _performance_collector.record_inference_latency(latency_ms)


def record_dracma_transaction(amount: float, transaction_type: str = "transfer"):
    """Registrar transacción DRACMA."""
    _performance_collector.record_dracma_transaction(amount, transaction_type)


def record_api_request(method: str, endpoint: str, status_code: int):
    """Registrar request de API."""
    _performance_collector.record_api_request(method, endpoint, status_code)


# Decoradores para medir performance automáticamente

def measure_latency(metric_type: str):
    """Decorador para medir latencia de funciones."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency_ms = (time.time() - start_time) * 1000

                if metric_type == 'api':
                    record_api_latency(latency_ms)
                elif metric_type == 'db':
                    record_db_latency(latency_ms)
                elif metric_type == 'inference':
                    record_inference_latency(latency_ms)

        return wrapper
    return decorator