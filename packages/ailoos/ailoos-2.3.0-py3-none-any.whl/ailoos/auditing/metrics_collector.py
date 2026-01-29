"""
Sistema de recopilación de métricas y estadísticas del sistema para AILOOS.
Proporciona métricas de rendimiento, uso y salud del sistema.
"""

import asyncio
import psutil
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import threading
import platform
import os

from ..core.logging import get_logger
from .audit_manager import get_audit_manager
from .structured_logger import get_structured_logger
from ..core.config import get_config

logger = get_logger(__name__)
structured_logger = get_structured_logger("metrics")


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento."""
    timestamp: datetime
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    throughput_requests_per_sec: float
    error_rate: float
    active_connections: int
    queued_requests: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "response_time_avg": self.response_time_avg,
            "response_time_p95": self.response_time_p95,
            "response_time_p99": self.response_time_p99,
            "throughput_requests_per_sec": self.throughput_requests_per_sec,
            "error_rate": self.error_rate,
            "active_connections": self.active_connections,
            "queued_requests": self.queued_requests
        }


@dataclass
class ResourceMetrics:
    """Métricas de recursos del sistema."""
    timestamp: datetime
    cpu_usage_percent: float
    cpu_usage_per_core: List[float]
    memory_usage_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_available_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    open_file_descriptors: int
    threads_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage_percent": self.cpu_usage_percent,
            "cpu_usage_per_core": self.cpu_usage_per_core,
            "memory_usage_percent": self.memory_usage_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_available_gb": self.memory_available_gb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_used_gb": self.disk_used_gb,
            "disk_available_gb": self.disk_available_gb,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "network_packets_sent": self.network_packets_sent,
            "network_packets_recv": self.network_packets_recv,
            "open_file_descriptors": self.open_file_descriptors,
            "threads_count": self.threads_count
        }


@dataclass
class ApplicationMetrics:
    """Métricas específicas de la aplicación."""
    timestamp: datetime
    active_sessions: int
    total_users: int
    active_federated_sessions: int
    pending_training_jobs: int
    completed_training_jobs: int
    failed_training_jobs: int
    marketplace_transactions: int
    api_requests_total: int
    api_requests_success: int
    database_connections_active: int
    cache_hit_rate: float
    blockchain_sync_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "active_sessions": self.active_sessions,
            "total_users": self.total_users,
            "active_federated_sessions": self.active_federated_sessions,
            "pending_training_jobs": self.pending_training_jobs,
            "completed_training_jobs": self.completed_training_jobs,
            "failed_training_jobs": self.failed_training_jobs,
            "marketplace_transactions": self.marketplace_transactions,
            "api_requests_total": self.api_requests_total,
            "api_requests_success": self.api_requests_success,
            "database_connections_active": self.database_connections_active,
            "cache_hit_rate": self.cache_hit_rate,
            "blockchain_sync_status": self.blockchain_sync_status
        }


@dataclass
class KnowledgeGraphMetrics:
    """Métricas específicas del Knowledge Graph."""
    timestamp: datetime
    triple_count: int
    queries_per_second: float
    inferences_executed: int
    operation_latency_avg: float
    operation_latency_p95: float
    operation_latency_p99: float
    active_queries: int
    failed_queries: int
    cache_hit_rate: float
    storage_size_mb: float
    index_size_mb: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "triple_count": self.triple_count,
            "queries_per_second": self.queries_per_second,
            "inferences_executed": self.inferences_executed,
            "operation_latency_avg": self.operation_latency_avg,
            "operation_latency_p95": self.operation_latency_p95,
            "operation_latency_p99": self.operation_latency_p99,
            "active_queries": self.active_queries,
            "failed_queries": self.failed_queries,
            "cache_hit_rate": self.cache_hit_rate,
            "storage_size_mb": self.storage_size_mb,
            "index_size_mb": self.index_size_mb
        }


@dataclass
class HealthStatus:
    """Estado de salud del sistema."""
    service_name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)
    uptime_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "last_check": self.last_check.isoformat(),
            "uptime_seconds": self.uptime_seconds
        }


class MetricsCollector:
    """
    Recolector centralizado de métricas del sistema.
    Recopila métricas de rendimiento, recursos y aplicación.
    """

    def __init__(self):
        self.config = get_config()
        self.audit_manager = get_audit_manager()

        # Buffers de métricas
        self.performance_metrics: deque = deque(maxlen=1000)
        self.resource_metrics: deque = deque(maxlen=1000)
        self.application_metrics: deque = deque(maxlen=1000)
        self.knowledge_graph_metrics: deque = deque(maxlen=1000)

        # Estado de salud de servicios
        self.service_health: Dict[str, HealthStatus] = {}

        # Tiempos de respuesta recientes
        self.response_times: deque = deque(maxlen=10000)
        self.error_counts: Dict[str, int] = {}
        self.request_counts: Dict[str, int] = {}

        # Información del sistema
        self.system_info = self._get_system_info()

        # Configuración
        self.collection_interval = getattr(self.config, 'metrics_collection_interval_seconds', 30)
        self.retention_hours = getattr(self.config, 'metrics_retention_hours', 24)

        # Callbacks
        self.metrics_callbacks: List[Callable] = []

        # Recopilación se inicia por separado después de la inicialización

    def _get_system_info(self) -> Dict[str, Any]:
        """Obtener información básica del sistema."""
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "system": platform.system()
        }
        try:
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        except Exception as exc:
            logger.warning(f"Unable to read CPU info: {exc}")
            info["cpu_count"] = None
            info["cpu_count_logical"] = None
        try:
            info["memory_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
        except Exception as exc:
            logger.warning(f"Unable to read memory info: {exc}")
            info["memory_total_gb"] = None
        try:
            info["disk_total_gb"] = round(psutil.disk_usage('/').total / (1024**3), 2)
        except Exception as exc:
            logger.warning(f"Unable to read disk info: {exc}")
            info["disk_total_gb"] = None
        return info

    async def _collection_loop(self):
        """Loop principal de recopilación de métricas."""
        while True:
            try:
                start_time = time.time()

                # Recopilar métricas de recursos
                resource_metrics = await self._collect_resource_metrics()
                self.resource_metrics.append(resource_metrics)

                # Recopilar métricas de rendimiento
                performance_metrics = self._collect_performance_metrics()
                self.performance_metrics.append(performance_metrics)

                # Recopilar métricas de aplicación
                app_metrics = await self._collect_application_metrics()
                self.application_metrics.append(app_metrics)

                # Recopilar métricas del Knowledge Graph
                kg_metrics = await self._collect_knowledge_graph_metrics()
                self.knowledge_graph_metrics.append(kg_metrics)

                # Notificar callbacks
                for callback in self.metrics_callbacks:
                    try:
                        await callback({
                            "resource": resource_metrics,
                            "performance": performance_metrics,
                            "application": app_metrics,
                            "knowledge_graph": kg_metrics
                        })
                    except Exception as e:
                        logger.error(f"Error in metrics callback: {e}")

                # Log métricas cada 5 minutos
                if int(time.time()) % 300 == 0:
                    structured_logger.info("System metrics collected",
                                          cpu_usage=resource_metrics.cpu_usage_percent,
                                          memory_usage=resource_metrics.memory_usage_percent,
                                          active_sessions=app_metrics.active_sessions)

                collection_time = (time.time() - start_time) * 1000
                if collection_time > 1000:  # Más de 1 segundo
                    structured_logger.warning("Slow metrics collection",
                                            collection_time_ms=collection_time)

            except Exception as e:
                structured_logger.error("Error collecting metrics", error=str(e))

            await asyncio.sleep(self.collection_interval)

    async def _collect_resource_metrics(self) -> ResourceMetrics:
        """Recopilar métricas de recursos del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # Memoria
            memory = psutil.virtual_memory()

            # Disco
            disk = psutil.disk_usage('/')

            # Red
            network = psutil.net_io_counters()

            # Sistema de archivos
            try:
                open_files = len(psutil.Process().open_files())
            except:
                open_files = 0

            threads = threading.active_count()

            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                cpu_usage_per_core=cpu_per_core,
                memory_usage_percent=memory.percent,
                memory_used_gb=round(memory.used / (1024**3), 2),
                memory_available_gb=round(memory.available / (1024**3), 2),
                disk_usage_percent=disk.percent,
                disk_used_gb=round(disk.used / (1024**3), 2),
                disk_available_gb=round(disk.free / (1024**3), 2),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                open_file_descriptors=open_files,
                threads_count=threads
            )

        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            # Retornar métricas vacías en caso de error
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=0.0,
                cpu_usage_per_core=[],
                memory_usage_percent=0.0,
                memory_used_gb=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_available_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                network_packets_sent=0,
                network_packets_recv=0,
                open_file_descriptors=0,
                threads_count=0
            )

    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Recopilar métricas de rendimiento."""
        # Calcular percentiles de tiempo de respuesta
        if self.response_times:
            sorted_times = sorted(self.response_times)
            avg_time = sum(sorted_times) / len(sorted_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_time = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_time = p95_time = p99_time = 0.0

        # Calcular throughput (requests por segundo en el último minuto)
        recent_requests = sum(self.request_counts.get(endpoint, 0)
                            for endpoint in self.request_counts.keys())
        throughput = recent_requests / 60.0 if recent_requests > 0 else 0.0

        # Calcular tasa de error
        total_errors = sum(self.error_counts.values())
        total_requests = sum(self.request_counts.values())
        error_rate = total_errors / max(total_requests, 1)

        return PerformanceMetrics(
            timestamp=datetime.now(),
            response_time_avg=avg_time,
            response_time_p95=p95_time,
            response_time_p99=p99_time,
            throughput_requests_per_sec=throughput,
            error_rate=error_rate,
            active_connections=self._get_active_connections(),
            queued_requests=self._get_queued_requests()
        )

    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """Recopilar métricas específicas de la aplicación."""
        try:
            # En implementación real, estas vendrían de los servicios correspondientes
            # Por ahora, valores de ejemplo/simulados

            # Sesiones activas (del audit manager)
            active_sessions = len(self.audit_manager.active_sessions) if hasattr(self.audit_manager, 'active_sessions') else 0

            # Métricas de federated learning (simuladas)
            active_federated_sessions = 0  # TODO: integrar con federated coordinator
            pending_training_jobs = 0
            completed_training_jobs = 0
            failed_training_jobs = 0

            # Marketplace (simulado)
            marketplace_transactions = 0

            # API requests
            api_requests_total = sum(self.request_counts.values())
            api_requests_success = api_requests_total - sum(self.error_counts.values())

            # Database connections (simulado)
            database_connections_active = 0

            # Cache hit rate (simulado)
            cache_hit_rate = 0.85

            # Blockchain sync (simulado)
            blockchain_sync_status = "synced"

            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_sessions=active_sessions,
                total_users=0,  # TODO: integrar con user service
                active_federated_sessions=active_federated_sessions,
                pending_training_jobs=pending_training_jobs,
                completed_training_jobs=completed_training_jobs,
                failed_training_jobs=failed_training_jobs,
                marketplace_transactions=marketplace_transactions,
                api_requests_total=api_requests_total,
                api_requests_success=api_requests_success,
                database_connections_active=database_connections_active,
                cache_hit_rate=cache_hit_rate,
                blockchain_sync_status=blockchain_sync_status
            )

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_sessions=0,
                total_users=0,
                active_federated_sessions=0,
                pending_training_jobs=0,
                completed_training_jobs=0,
                failed_training_jobs=0,
                marketplace_transactions=0,
                api_requests_total=0,
                api_requests_success=0,
                database_connections_active=0,
                cache_hit_rate=0.0,
                blockchain_sync_status="unknown"
            )

    async def _collect_knowledge_graph_metrics(self) -> KnowledgeGraphMetrics:
        """Recopilar métricas específicas del Knowledge Graph."""
        try:
            # En implementación real, estas vendrían de los servicios KG correspondientes
            # Por ahora, valores simulados/ejemplo

            # Conteo de triples (simulado)
            triple_count = 0  # TODO: integrar con KG storage backends

            # Queries por segundo (basado en contadores)
            recent_kg_queries = sum(self.request_counts.get(endpoint, 0)
                                  for endpoint in self.request_counts.keys()
                                  if 'kg' in endpoint.lower() or 'graph' in endpoint.lower())
            queries_per_second = recent_kg_queries / 60.0 if recent_kg_queries > 0 else 0.0

            # Inferencias ejecutadas (simulado)
            inferences_executed = 0  # TODO: integrar con inference engine

            # Latencia de operaciones (simulada basada en tiempos de respuesta)
            kg_latencies = [t for t in self.response_times if len(self.response_times) > 0]  # Placeholder
            if kg_latencies:
                avg_latency = sum(kg_latencies) / len(kg_latencies)
                sorted_latencies = sorted(kg_latencies)
                p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            else:
                avg_latency = p95_latency = p99_latency = 0.0

            # Queries activas y fallidas (simulado)
            active_queries = 0  # TODO: integrar con query engine
            failed_queries = sum(self.error_counts.get(endpoint, 0)
                               for endpoint in self.error_counts.keys()
                               if 'kg' in endpoint.lower() or 'graph' in endpoint.lower())

            # Cache hit rate (simulado)
            kg_cache_hit_rate = 0.85

            # Tamaños de almacenamiento (simulado)
            storage_size_mb = 0.0  # TODO: integrar con storage backends
            index_size_mb = 0.0

            return KnowledgeGraphMetrics(
                timestamp=datetime.now(),
                triple_count=triple_count,
                queries_per_second=queries_per_second,
                inferences_executed=inferences_executed,
                operation_latency_avg=avg_latency,
                operation_latency_p95=p95_latency,
                operation_latency_p99=p99_latency,
                active_queries=active_queries,
                failed_queries=failed_queries,
                cache_hit_rate=kg_cache_hit_rate,
                storage_size_mb=storage_size_mb,
                index_size_mb=index_size_mb
            )

        except Exception as e:
            logger.error(f"Error collecting knowledge graph metrics: {e}")
            return KnowledgeGraphMetrics(
                timestamp=datetime.now(),
                triple_count=0,
                queries_per_second=0.0,
                inferences_executed=0,
                operation_latency_avg=0.0,
                operation_latency_p95=0.0,
                operation_latency_p99=0.0,
                active_queries=0,
                failed_queries=0,
                cache_hit_rate=0.0,
                storage_size_mb=0.0,
                index_size_mb=0.0
            )

    def _get_active_connections(self) -> int:
        """Obtener número de conexiones activas."""
        try:
            connections = psutil.net_connections()
            return len([c for c in connections if c.status == 'ESTABLISHED'])
        except:
            return 0

    def _get_queued_requests(self) -> int:
        """Obtener número de requests en cola."""
        # En implementación real, esto vendría del servidor web
        return 0

    async def _health_check_loop(self):
        """Loop de verificación de salud de servicios."""
        while True:
            try:
                # Verificar servicios críticos
                services_to_check = [
                    "database",
                    "redis",
                    "ipfs",
                    "federated_coordinator",
                    "marketplace",
                    "blockchain"
                ]

                for service in services_to_check:
                    await self._check_service_health(service)

                # Log estado de salud cada 10 minutos
                if int(time.time()) % 600 == 0:
                    healthy_count = len([s for s in self.service_health.values() if s.status == 'healthy'])
                    total_count = len(self.service_health)
                    structured_logger.info("Health check completed",
                                         healthy_services=healthy_count,
                                         total_services=total_count)

            except Exception as e:
                structured_logger.error("Error in health check loop", error=str(e))

            await asyncio.sleep(60)  # Cada minuto

    async def _check_service_health(self, service_name: str):
        """Verificar salud de un servicio específico."""
        try:
            start_time = time.time()

            # Lógica específica por servicio
            if service_name == "database":
                health_status = await self._check_database_health()
            elif service_name == "redis":
                health_status = await self._check_redis_health()
            elif service_name == "ipfs":
                health_status = await self._check_ipfs_health()
            else:
                # Para otros servicios, simular verificación
                health_status = ("healthy", None)

            response_time = (time.time() - start_time) * 1000

            status, error_msg = health_status
            uptime = self._get_service_uptime(service_name)

            health = HealthStatus(
                service_name=service_name,
                status=status,
                response_time_ms=response_time,
                error_message=error_msg,
                uptime_seconds=uptime
            )

            self.service_health[service_name] = health

            if status != 'healthy':
                structured_logger.warning(f"Service health check failed: {service_name}",
                                        status=status,
                                        error=error_msg,
                                        response_time_ms=response_time)

        except Exception as e:
            self.service_health[service_name] = HealthStatus(
                service_name=service_name,
                status='unhealthy',
                error_message=str(e)
            )

    async def _check_database_health(self) -> tuple:
        """Verificar salud de la base de datos."""
        # En implementación real, ejecutar una query simple
        return ("healthy", None)

    async def _check_redis_health(self) -> tuple:
        """Verificar salud de Redis."""
        # En implementación real, ping a Redis
        return ("healthy", None)

    async def _check_ipfs_health(self) -> tuple:
        """Verificar salud de IPFS."""
        # En implementación real, verificar conexión IPFS
        return ("healthy", None)

    def _get_service_uptime(self, service_name: str) -> Optional[int]:
        """Obtener uptime de un servicio."""
        # En implementación real, esto vendría del process manager
        return None

    async def _cleanup_loop(self):
        """Loop de limpieza de métricas antiguas."""
        while True:
            try:
                await asyncio.sleep(3600)  # Cada hora

                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

                # Limpiar métricas antiguas
                self.performance_metrics = deque(
                    [m for m in self.performance_metrics if m.timestamp > cutoff_time],
                    maxlen=1000
                )

                self.resource_metrics = deque(
                    [m for m in self.resource_metrics if m.timestamp > cutoff_time],
                    maxlen=1000
                )

                self.application_metrics = deque(
                    [m for m in self.application_metrics if m.timestamp > cutoff_time],
                    maxlen=1000
                )

                self.knowledge_graph_metrics = deque(
                    [m for m in self.knowledge_graph_metrics if m.timestamp > cutoff_time],
                    maxlen=1000
                )

                # Limpiar contadores antiguos
                self.error_counts.clear()
                self.request_counts.clear()

                structured_logger.info("Metrics cleanup completed")

            except Exception as e:
                structured_logger.error("Error in cleanup loop", error=str(e))

    # Métodos públicos
    def record_response_time(self, response_time_ms: float):
        """Registrar tiempo de respuesta."""
        self.response_times.append(response_time_ms)
        self.audit_manager.track_response_time(response_time_ms)

    def record_request(self, endpoint: str):
        """Registrar request."""
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1

    def record_error(self, endpoint: str, error_type: str = "unknown"):
        """Registrar error."""
        self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
        self.audit_manager.track_error(error_type)

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Obtener las métricas más recientes."""
        return {
            "resource": self.resource_metrics[-1].to_dict() if self.resource_metrics else None,
            "performance": self.performance_metrics[-1].to_dict() if self.performance_metrics else None,
            "application": self.application_metrics[-1].to_dict() if self.application_metrics else None,
            "knowledge_graph": self.knowledge_graph_metrics[-1].to_dict() if self.knowledge_graph_metrics else None,
            "system_info": self.system_info
        }

    def get_metrics_history(self, hours: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Obtener historial de métricas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return {
            "resource": [m.to_dict() for m in self.resource_metrics if m.timestamp > cutoff_time],
            "performance": [m.to_dict() for m in self.performance_metrics if m.timestamp > cutoff_time],
            "application": [m.to_dict() for m in self.application_metrics if m.timestamp > cutoff_time],
            "knowledge_graph": [m.to_dict() for m in self.knowledge_graph_metrics if m.timestamp > cutoff_time]
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud de todos los servicios."""
        return {
            "services": {name: health.to_dict() for name, health in self.service_health.items()},
            "overall_status": self._calculate_overall_health_status()
        }

    def _calculate_overall_health_status(self) -> str:
        """Calcular estado de salud general."""
        if not self.service_health:
            return "unknown"

        statuses = [health.status for health in self.service_health.values()]

        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"

    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento."""
        if not self.performance_metrics:
            return {}

        latest = self.performance_metrics[-1]

        # Calcular tendencias
        if len(self.performance_metrics) > 1:
            prev = self.performance_metrics[-2]
            response_time_trend = ((latest.response_time_avg - prev.response_time_avg) / max(prev.response_time_avg, 0.001)) * 100
            throughput_trend = ((latest.throughput_requests_per_sec - prev.throughput_requests_per_sec) / max(prev.throughput_requests_per_sec, 0.001)) * 100
        else:
            response_time_trend = 0.0
            throughput_trend = 0.0

        return {
            "current": latest.to_dict(),
            "trends": {
                "response_time_percent_change": response_time_trend,
                "throughput_percent_change": throughput_trend
            },
            "averages_1h": self._calculate_averages(hours=1),
            "averages_24h": self._calculate_averages(hours=24)
        }

    def _calculate_averages(self, hours: int) -> Dict[str, float]:
        """Calcular promedios para un período."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {}

        return {
            "avg_response_time": sum(m.response_time_avg for m in recent_metrics) / len(recent_metrics),
            "avg_throughput": sum(m.throughput_requests_per_sec for m in recent_metrics) / len(recent_metrics),
            "avg_error_rate": sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        }

    def start_collection(self):
        """Iniciar la recopilación de métricas después de la inicialización del servidor."""
        asyncio.create_task(self._collection_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._cleanup_loop())

    def add_metrics_callback(self, callback: Callable):
        """Agregar callback para nuevas métricas."""
        self.metrics_callbacks.append(callback)


# Instancia global
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Obtener instancia global del recolector de métricas."""
    return metrics_collector
