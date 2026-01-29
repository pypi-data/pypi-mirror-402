"""
PubSub Monitoring - Monitoreo y analytics del sistema
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class MonitoringMetrics:
    """Métricas de monitoreo"""
    messages_published: int = 0
    messages_delivered: int = 0
    subscriptions_created: int = 0
    subscriptions_removed: int = 0
    errors: int = 0
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    throughput_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    start_time: float = field(default_factory=time.time)


@dataclass
class TopicMetrics:
    """Métricas por topic"""
    messages_published: int = 0
    messages_delivered: int = 0
    subscribers: int = 0
    last_activity: float = 0.0
    error_count: int = 0


class PubSubMonitoring:
    """
    Monitoreo y analytics del sistema PubSub.
    Recopila métricas, latencias y estadísticas de rendimiento.
    """

    def __init__(self, retention_period: int = 3600):
        self.retention_period = retention_period  # segundos
        self._metrics = MonitoringMetrics()
        self._topic_metrics: Dict[str, TopicMetrics] = {}
        self._error_log: deque = deque(maxlen=1000)
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Inicia el monitoreo"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("PubSubMonitoring iniciado")

    async def stop(self) -> None:
        """Detiene el monitoreo"""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("PubSubMonitoring detenido")

    async def record_publish(self, topic: str, success: bool) -> None:
        """
        Registra una publicación

        Args:
            topic: Nombre del topic
            success: Si la publicación fue exitosa
        """
        self._metrics.messages_published += 1

        if topic not in self._topic_metrics:
            self._topic_metrics[topic] = TopicMetrics()

        self._topic_metrics[topic].messages_published += 1
        self._topic_metrics[topic].last_activity = time.time()

        if success:
            # Registrar throughput
            current_time = time.time()
            self._metrics.throughput_samples.append(current_time)

    async def record_subscribe(self, topic: str) -> None:
        """
        Registra una suscripción

        Args:
            topic: Nombre del topic
        """
        self._metrics.subscriptions_created += 1

        if topic not in self._topic_metrics:
            self._topic_metrics[topic] = TopicMetrics()

        self._topic_metrics[topic].subscribers += 1
        self._topic_metrics[topic].last_activity = time.time()

    async def record_unsubscribe(self) -> None:
        """Registra una cancelación de suscripción"""
        self._metrics.subscriptions_removed += 1

    async def record_delivery(self, topic: str, latency: Optional[float] = None) -> None:
        """
        Registra una entrega de mensaje

        Args:
            topic: Nombre del topic
            latency: Latencia de entrega en segundos
        """
        self._metrics.messages_delivered += 1

        if topic in self._topic_metrics:
            self._topic_metrics[topic].messages_delivered += 1

        if latency is not None:
            self._metrics.latency_samples.append(latency)

    async def record_error(self, operation: str, error_message: str) -> None:
        """
        Registra un error

        Args:
            operation: Operación que falló
            error_message: Mensaje de error
        """
        self._metrics.errors += 1

        error_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "error": error_message
        }

        self._error_log.append(error_entry)

        # Registrar error por topic si aplica
        if operation in ["publish", "subscribe", "unsubscribe"]:
            # Extraer topic del mensaje de error si está presente
            pass

        logger.warning(f"Error registrado: {operation} - {error_message}")

    async def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del sistema"""
        uptime = time.time() - self._metrics.start_time

        # Calcular throughput (mensajes por segundo)
        throughput = self._calculate_throughput()

        # Calcular latencia promedio
        avg_latency = self._calculate_avg_latency()

        return {
            "uptime": uptime,
            "messages_published": self._metrics.messages_published,
            "messages_delivered": self._metrics.messages_delivered,
            "subscriptions_created": self._metrics.subscriptions_created,
            "subscriptions_removed": self._metrics.subscriptions_removed,
            "errors": self._metrics.errors,
            "throughput_msg_per_sec": throughput,
            "avg_latency_sec": avg_latency,
            "active_topics": len(self._topic_metrics),
            "total_subscribers": sum(tm.subscribers for tm in self._topic_metrics.values())
        }

    async def get_topic_stats(self, topic: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un topic específico

        Args:
            topic: Nombre del topic

        Returns:
            Diccionario con estadísticas del topic
        """
        if topic not in self._topic_metrics:
            return {}

        tm = self._topic_metrics[topic]

        return {
            "messages_published": tm.messages_published,
            "messages_delivered": tm.messages_delivered,
            "subscribers": tm.subscribers,
            "last_activity": tm.last_activity,
            "error_count": tm.error_count,
            "delivery_rate": tm.messages_delivered / max(tm.messages_published, 1),
            "age": time.time() - tm.last_activity
        }

    async def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene errores recientes

        Args:
            limit: Número máximo de errores a retornar

        Returns:
            Lista de errores recientes
        """
        return list(self._error_log)[-limit:]

    async def get_performance_report(self) -> Dict[str, Any]:
        """Genera un reporte de rendimiento completo"""
        system_stats = await self.get_system_stats()

        # Top topics por actividad
        top_topics = sorted(
            self._topic_metrics.items(),
            key=lambda x: x[1].messages_published,
            reverse=True
        )[:10]

        topic_reports = []
        for topic, metrics in top_topics:
            topic_reports.append({
                "topic": topic,
                **await self.get_topic_stats(topic)
            })

        # Análisis de latencia
        latencies = list(self._metrics.latency_samples)
        latency_stats = {}
        if latencies:
            latency_stats = {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            }

        return {
            "system": system_stats,
            "top_topics": topic_reports,
            "latency_stats": latency_stats,
            "error_rate": system_stats["errors"] / max(system_stats["messages_published"], 1),
            "generated_at": time.time()
        }

    def _calculate_throughput(self) -> float:
        """Calcula throughput actual (mensajes por segundo)"""
        if len(self._metrics.throughput_samples) < 2:
            return 0.0

        # Usar últimas 10 muestras para calcular throughput promedio
        recent_samples = list(self._metrics.throughput_samples)[-10:]
        if len(recent_samples) < 2:
            return 0.0

        time_span = recent_samples[-1] - recent_samples[0]
        if time_span <= 0:
            return 0.0

        return len(recent_samples) / time_span

    def _calculate_avg_latency(self) -> float:
        """Calcula latencia promedio"""
        latencies = list(self._metrics.latency_samples)
        return statistics.mean(latencies) if latencies else 0.0

    async def _periodic_cleanup(self) -> None:
        """Limpieza periódica de métricas antiguas"""
        try:
            while self._running:
                await asyncio.sleep(300)  # Cada 5 minutos

                current_time = time.time()

                # Limpiar topics inactivos
                inactive_topics = []
                for topic, metrics in self._topic_metrics.items():
                    if current_time - metrics.last_activity > self.retention_period:
                        inactive_topics.append(topic)

                for topic in inactive_topics:
                    del self._topic_metrics[topic]

                # Limpiar muestras antiguas de throughput
                cutoff_time = current_time - 300  # Últimos 5 minutos
                while self._metrics.throughput_samples and self._metrics.throughput_samples[0] < cutoff_time:
                    self._metrics.throughput_samples.popleft()

                if inactive_topics:
                    logger.info(f"Limpiados {len(inactive_topics)} topics inactivos del monitoreo")

        except asyncio.CancelledError:
            logger.info("Limpieza periódica cancelada")
        except Exception as e:
            logger.error(f"Error en limpieza periódica: {e}")

    async def reset_metrics(self) -> None:
        """Reinicia todas las métricas (para testing)"""
        self._metrics = MonitoringMetrics()
        self._topic_metrics.clear()
        self._error_log.clear()