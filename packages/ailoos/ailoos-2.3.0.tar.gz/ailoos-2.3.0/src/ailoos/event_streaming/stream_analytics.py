import asyncio
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List
import statistics

logger = logging.getLogger(__name__)

class StreamAnalytics:
    """
    Analytics en tiempo real de streams de eventos.
    Calcula métricas como throughput, distribución de tipos de eventos,
    latencias y tendencias.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.event_counter = Counter()
        self.event_timestamps = []
        self.throughput_history = []
        self.latency_measurements = []
        self.error_counts = Counter()
        self.last_analysis_time = datetime.utcnow()
        self.analysis_interval = config.get('analysis_interval_seconds', 60)
        self.max_history_size = config.get('max_history_size', 1000)

    async def start(self):
        """Inicia el sistema de analytics."""
        if self.running:
            return
        self.running = True
        logger.info("StreamAnalytics iniciado")

    async def stop(self):
        """Detiene el sistema de analytics."""
        self.running = False
        logger.info("StreamAnalytics detenido")

    async def update_metrics(self, processed_result: Any):
        """Actualiza métricas con el resultado del procesamiento de un evento."""
        if not self.running:
            return

        try:
            # Asumiendo que processed_result es un ProcessingResult o dict
            if hasattr(processed_result, 'event'):
                event = processed_result.event
                processed = processed_result.processed
                errors = processed_result.errors
            else:
                event = processed_result
                processed = True
                errors = []

            # Contar tipos de eventos
            event_type = event.get('type', 'unknown')
            self.event_counter[event_type] += 1

            # Registrar timestamp
            timestamp = datetime.utcnow()
            self.event_timestamps.append(timestamp)

            # Registrar errores
            for error in errors:
                self.error_counts[error] += 1

            # Mantener tamaño máximo de historial
            if len(self.event_timestamps) > self.max_history_size:
                self.event_timestamps = self.event_timestamps[-self.max_history_size:]

            # Registrar latencia si está disponible
            if 'latency_ms' in event:
                self.latency_measurements.append(event['latency_ms'])
                if len(self.latency_measurements) > self.max_history_size:
                    self.latency_measurements = self.latency_measurements[-self.max_history_size:]

        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")

    async def run_real_time_analysis(self):
        """Ejecuta análisis en tiempo real de las métricas."""
        if not self.running:
            return

        try:
            now = datetime.utcnow()
            time_diff = (now - self.last_analysis_time).total_seconds()

            if time_diff >= self.analysis_interval:
                # Calcular throughput (eventos por segundo)
                recent_events = [t for t in self.event_timestamps if (now - t).total_seconds() <= 60]
                throughput = len(recent_events) / 60.0 if recent_events else 0.0
                self.throughput_history.append((now, throughput))

                # Mantener historial de throughput
                if len(self.throughput_history) > 100:
                    self.throughput_history = self.throughput_history[-100:]

                self.last_analysis_time = now

                logger.debug(f"Throughput actual: {throughput:.2f} eventos/segundo")

        except Exception as e:
            logger.error(f"Error en análisis en tiempo real: {e}")

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Obtiene las métricas actuales del stream."""
        if not self.running:
            return {'status': 'stopped'}

        try:
            now = datetime.utcnow()

            # Métricas básicas
            total_events = sum(self.event_counter.values())
            event_types = dict(self.event_counter.most_common(10))

            # Throughput actual
            recent_events = [t for t in self.event_timestamps if (now - t).total_seconds() <= 60]
            current_throughput = len(recent_events) / 60.0 if recent_events else 0.0

            # Throughput promedio
            avg_throughput = statistics.mean([t for _, t in self.throughput_history]) if self.throughput_history else 0.0

            # Latencia
            avg_latency = statistics.mean(self.latency_measurements) if self.latency_measurements else 0.0
            max_latency = max(self.latency_measurements) if self.latency_measurements else 0.0

            # Errores
            top_errors = dict(self.error_counts.most_common(5))

            # Tendencias
            throughput_trend = self._calculate_trend([t for _, t in self.throughput_history])

            return {
                'status': 'running',
                'total_events': total_events,
                'event_types': event_types,
                'current_throughput': current_throughput,
                'average_throughput': avg_throughput,
                'throughput_trend': throughput_trend,
                'average_latency_ms': avg_latency,
                'max_latency_ms': max_latency,
                'top_errors': top_errors,
                'last_updated': now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula la tendencia de una serie de valores."""
        if len(values) < 2:
            return 'stable'

        try:
            # Calcular pendiente simple
            n = len(values)
            if n < 2:
                return 'stable'

            slope = (values[-1] - values[0]) / n

            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'unknown'

    def get_historical_data(self, hours: int = 1) -> Dict[str, Any]:
        """Obtiene datos históricos para análisis."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        historical_events = [t for t in self.event_timestamps if t > cutoff]
        historical_throughput = [(t, v) for t, v in self.throughput_history if t > cutoff]

        return {
            'time_range_hours': hours,
            'event_count': len(historical_events),
            'throughput_data': historical_throughput,
            'avg_throughput': statistics.mean([v for _, v in historical_throughput]) if historical_throughput else 0.0
        }