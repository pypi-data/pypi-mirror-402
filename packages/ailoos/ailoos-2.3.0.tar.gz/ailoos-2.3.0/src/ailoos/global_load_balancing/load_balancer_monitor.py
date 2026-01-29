"""
LoadBalancerMonitor - Monitoreo y analytics del balanceo global
Recopila métricas, genera reportes y proporciona insights sobre el rendimiento.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import threading

from ...core.config import Config
from ...utils.logging import AiloosLogger
from .global_load_balancer import GlobalRequest, GlobalRoutingDecision


@dataclass
class MonitoringMetrics:
    """Métricas de monitoreo del sistema."""
    timestamp: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    geo_distribution: Dict[str, int] = field(default_factory=dict)
    service_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Alerta de rendimiento."""
    alert_id: str
    alert_type: str  # 'latency', 'error_rate', 'capacity', 'health'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    affected_components: List[str]
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    threshold_value: float = 0.0
    current_value: float = 0.0


@dataclass
class AnalyticsReport:
    """Reporte de analytics."""
    report_id: str
    report_type: str  # 'performance', 'usage', 'efficiency', 'predictive'
    time_range: Tuple[datetime, datetime]
    generated_at: datetime
    summary: Dict[str, Any]
    recommendations: List[str]
    charts_data: Dict[str, Any] = field(default_factory=dict)


class LoadBalancerMonitor:
    """
    Monitor avanzado que recopila métricas detalladas, detecta anomalías,
    genera reportes y proporciona insights para optimización continua.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Almacenamiento de métricas
        self.metrics_history: deque[MonitoringMetrics] = deque(maxlen=10000)  # Últimas 10k métricas
        self.request_details: deque[Dict[str, Any]] = deque(maxlen=50000)  # Detalles de requests

        # Alertas activas
        self.active_alerts: Dict[str, PerformanceAlert] = {}

        # Reportes generados
        self.generated_reports: Dict[str, AnalyticsReport] = {}

        # Configuración de umbrales
        self.alert_thresholds = {
            'max_error_rate': 0.05,  # 5%
            'max_avg_latency_ms': 1000,
            'max_p95_latency_ms': 2000,
            'min_health_score': 0.7,
            'max_failed_regions': 2
        }

        # Estadísticas en tiempo real
        self.realtime_stats = {
            'current_rps': 0.0,
            'avg_rps_last_minute': 0.0,
            'total_requests_today': 0,
            'error_rate_today': 0.0,
            'top_regions': [],
            'health_status': 'healthy'
        }

        # Locks para thread safety
        self._metrics_lock = threading.Lock()
        self._alerts_lock = threading.Lock()

        # Tareas
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.analytics_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar el sistema de monitoreo."""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.analytics_task = asyncio.create_task(self._analytics_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("📊 Load Balancer Monitor started")

    async def stop(self):
        """Detener el sistema de monitoreo."""
        self.is_running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.analytics_task:
            self.analytics_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        try:
            await asyncio.gather(
                self.monitoring_task, self.analytics_task, self.cleanup_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

        self.logger.info("🛑 Load Balancer Monitor stopped")

    async def record_request_completion(
        self,
        request: GlobalRequest,
        success: bool,
        response_time_ms: float
    ):
        """Registrar completación de solicitud."""
        request_detail = {
            'request_id': request.request_id,
            'service_type': request.service_type,
            'client_location': request.client_location,
            'priority': request.priority,
            'success': success,
            'response_time_ms': response_time_ms,
            'timestamp': datetime.now(),
            'compliance_requirements': request.compliance_requirements
        }

        with self._metrics_lock:
            self.request_details.append(request_detail)

        # Actualizar estadísticas en tiempo real
        self._update_realtime_stats(request_detail)

    async def record_routing_decision(self, decision: GlobalRoutingDecision):
        """Registrar decisión de routing."""
        routing_detail = {
            'request_id': decision.request_id,
            'selected_region': decision.selected_region,
            'selected_endpoint': decision.selected_endpoint,
            'estimated_latency_ms': decision.estimated_latency_ms,
            'confidence_score': decision.confidence_score,
            'routing_reason': decision.routing_reason,
            'geo_benefits': decision.geo_benefits,
            'timestamp': datetime.now()
        }

        with self._metrics_lock:
            self.request_details.append(routing_detail)

    async def _monitoring_loop(self):
        """Bucle principal de monitoreo."""
        while self.is_running:
            try:
                # Recopilar métricas cada 10 segundos
                await self._collect_system_metrics()
                await self._check_alerts()

                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _analytics_loop(self):
        """Bucle de análisis y generación de reportes."""
        while self.is_running:
            try:
                # Generar reportes cada hora
                await self._generate_hourly_report()
                await asyncio.sleep(3600)  # 1 hora

            except Exception as e:
                self.logger.error(f"Error in analytics loop: {e}")
                await asyncio.sleep(1800)

    async def _cleanup_loop(self):
        """Bucle de limpieza de datos antiguos."""
        while self.is_running:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(86400)  # 1 día

            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(43200)

    async def _collect_system_metrics(self):
        """Recopilar métricas del sistema."""
        with self._metrics_lock:
            if not self.request_details:
                return

            # Calcular ventana de tiempo (último minuto)
            cutoff_time = datetime.now() - timedelta(minutes=1)
            recent_requests = [
                r for r in self.request_details
                if isinstance(r.get('timestamp'), datetime) and r['timestamp'] > cutoff_time
            ]

            if not recent_requests:
                return

            # Calcular métricas
            total_requests = len(recent_requests)
            successful_requests = len([r for r in recent_requests if r.get('success', True)])
            failed_requests = total_requests - successful_requests

            response_times = [
                r.get('response_time_ms', 0)
                for r in recent_requests
                if 'response_time_ms' in r and r['response_time_ms'] > 0
            ]

            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times) if response_times else 0.0
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times) if response_times else 0.0

            requests_per_second = total_requests / 60.0
            error_rate = failed_requests / total_requests if total_requests > 0 else 0.0

            # Distribución geográfica
            geo_distribution = defaultdict(int)
            service_distribution = defaultdict(int)

            for request in recent_requests:
                if 'client_location' in request:
                    # Simplificar ubicación a zona
                    lat, lng = request['client_location']['lat'], request['client_location']['lng']
                    zone = self._get_geo_zone(lat, lng)
                    geo_distribution[zone] += 1

                if 'service_type' in request:
                    service_distribution[request['service_type']] += 1

            # Crear métrica
            metrics = MonitoringMetrics(
                timestamp=datetime.now(),
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                geo_distribution=dict(geo_distribution),
                service_distribution=dict(service_distribution)
            )

            self.metrics_history.append(metrics)

    async def _check_alerts(self):
        """Verificar condiciones de alerta."""
        if not self.metrics_history:
            return

        latest_metrics = self.metrics_history[-1]

        # Verificar tasa de error
        if latest_metrics.error_rate > self.alert_thresholds['max_error_rate']:
            await self._trigger_alert(
                alert_type='error_rate',
                severity='high' if latest_metrics.error_rate > 0.1 else 'medium',
                message=f"High error rate: {latest_metrics.error_rate:.2%}",
                current_value=latest_metrics.error_rate,
                threshold_value=self.alert_thresholds['max_error_rate']
            )

        # Verificar latencia
        if latest_metrics.avg_response_time_ms > self.alert_thresholds['max_avg_latency_ms']:
            await self._trigger_alert(
                alert_type='latency',
                severity='medium',
                message=f"High average latency: {latest_metrics.avg_response_time_ms:.0f}ms",
                current_value=latest_metrics.avg_response_time_ms,
                threshold_value=self.alert_thresholds['max_avg_latency_ms']
            )

        # Verificar P95 latencia
        if latest_metrics.p95_response_time_ms > self.alert_thresholds['max_p95_latency_ms']:
            await self._trigger_alert(
                alert_type='latency',
                severity='high',
                message=f"High P95 latency: {latest_metrics.p95_response_time_ms:.0f}ms",
                current_value=latest_metrics.p95_response_time_ms,
                threshold_value=self.alert_thresholds['max_p95_latency_ms']
            )

    async def _trigger_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float,
        threshold_value: float,
        affected_components: List[str] = None
    ):
        """Disparar alerta de rendimiento."""
        alert_id = f"{alert_type}_{int(time.time())}"

        with self._alerts_lock:
            if alert_id in self.active_alerts:
                return  # Alerta ya activa

            alert = PerformanceAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                affected_components=affected_components or [],
                triggered_at=datetime.now(),
                threshold_value=threshold_value,
                current_value=current_value
            )

            self.active_alerts[alert_id] = alert

        self.logger.warning(f"🚨 Performance Alert: {message}")

        # En producción, aquí se enviarían notificaciones

    async def _generate_hourly_report(self):
        """Generar reporte horario de analytics."""
        if len(self.metrics_history) < 6:  # Necesitamos al menos 1 hora de datos
            return

        # Obtener datos de la última hora
        cutoff_time = datetime.now() - timedelta(hours=1)
        hourly_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

        if not hourly_metrics:
            return

        # Calcular estadísticas
        avg_rps = statistics.mean(m.requests_per_second for m in hourly_metrics)
        avg_error_rate = statistics.mean(m.error_rate for m in hourly_metrics)
        avg_latency = statistics.mean(m.avg_response_time_ms for m in hourly_metrics)

        # Top servicios
        all_services = defaultdict(int)
        for m in hourly_metrics:
            for service, count in m.service_distribution.items():
                all_services[service] += count

        top_services = sorted(all_services.items(), key=lambda x: x[1], reverse=True)[:5]

        # Top regiones
        all_regions = defaultdict(int)
        for m in hourly_metrics:
            for region, count in m.geo_distribution.items():
                all_regions[region] += count

        top_regions = sorted(all_regions.items(), key=lambda x: x[1], reverse=True)[:5]

        # Generar recomendaciones
        recommendations = []

        if avg_error_rate > 0.05:
            recommendations.append("Investigate high error rates - check health of endpoints")
        if avg_latency > 500:
            recommendations.append("Optimize routing for lower latency - consider geo-distribution")
        if len(top_regions) > 3:
            recommendations.append("Traffic is geographically concentrated - consider regional scaling")

        # Crear reporte
        report = AnalyticsReport(
            report_id=f"hourly_{int(time.time())}",
            report_type='performance',
            time_range=(cutoff_time, datetime.now()),
            generated_at=datetime.now(),
            summary={
                'avg_requests_per_second': avg_rps,
                'avg_error_rate': avg_error_rate,
                'avg_response_time_ms': avg_latency,
                'total_requests': sum(m.total_requests for m in hourly_metrics),
                'top_services': top_services,
                'top_regions': top_regions
            },
            recommendations=recommendations,
            charts_data={
                'rps_over_time': [(m.timestamp.isoformat(), m.requests_per_second) for m in hourly_metrics],
                'latency_over_time': [(m.timestamp.isoformat(), m.avg_response_time_ms) for m in hourly_metrics],
                'error_rate_over_time': [(m.timestamp.isoformat(), m.error_rate) for m in hourly_metrics]
            }
        )

        self.generated_reports[report.report_id] = report
        self.logger.info(f"📈 Generated hourly analytics report: {report.report_id}")

    async def _cleanup_old_data(self):
        """Limpiar datos antiguos."""
        # Mantener solo últimos 7 días de métricas detalladas
        cutoff_time = datetime.now() - timedelta(days=7)

        with self._metrics_lock:
            while self.request_details:
                if self.request_details[0].get('timestamp', datetime.min) < cutoff_time:
                    self.request_details.popleft()
                else:
                    break

        # Limpiar reportes antiguos (mantener 30 días)
        report_cutoff = datetime.now() - timedelta(days=30)
        old_reports = [
            rid for rid, report in self.generated_reports.items()
            if report.generated_at < report_cutoff
        ]
        for rid in old_reports:
            del self.generated_reports[rid]

        # Resolver alertas antiguas
        alert_cutoff = datetime.now() - timedelta(hours=24)
        with self._alerts_lock:
            resolved_alerts = [
                aid for aid, alert in self.active_alerts.items()
                if alert.triggered_at < alert_cutoff
            ]
            for aid in resolved_alerts:
                self.active_alerts[aid].resolved_at = datetime.now()

    def _update_realtime_stats(self, request_detail: Dict[str, Any]):
        """Actualizar estadísticas en tiempo real."""
        # Actualizar RPS (requests por segundo)
        current_time = time.time()
        # Lógica simplificada para estadísticas en tiempo real

    def _get_geo_zone(self, lat: float, lng: float) -> str:
        """Obtener zona geográfica para analytics."""
        # Similar al geo router
        lat_zone = int(lat // 15) * 15  # Zonas más grandes para analytics
        lng_zone = int(lng // 15) * 15

        ns = "N" if lat >= 0 else "S"
        ew = "E" if lng >= 0 else "W"

        return f"{abs(lat_zone)}{ns}_{abs(lng_zone)}{ew}"

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Obtener estado completo del monitoreo."""
        with self._metrics_lock:
            latest_metrics = self.metrics_history[-1] if self.metrics_history else None

        with self._alerts_lock:
            active_alerts_count = len([a for a in self.active_alerts.values() if not a.resolved_at])

        return {
            'is_running': self.is_running,
            'metrics_collected': len(self.metrics_history),
            'requests_tracked': len(self.request_details),
            'active_alerts': active_alerts_count,
            'reports_generated': len(self.generated_reports),
            'latest_metrics': {
                'timestamp': latest_metrics.timestamp.isoformat() if latest_metrics else None,
                'total_requests': latest_metrics.total_requests if latest_metrics else 0,
                'successful_requests': latest_metrics.successful_requests if latest_metrics else 0,
                'avg_response_time_ms': latest_metrics.avg_response_time_ms if latest_metrics else 0,
                'error_rate': latest_metrics.error_rate if latest_metrics else 0,
                'requests_per_second': latest_metrics.requests_per_second if latest_metrics else 0
            } if latest_metrics else {},
            'realtime_stats': self.realtime_stats,
            'alerts': [
                {
                    'id': alert.alert_id,
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'triggered_at': alert.triggered_at.isoformat(),
                    'resolved': alert.resolved_at is not None
                }
                for alert in list(self.active_alerts.values())[-10:]  # Últimas 10 alertas
            ]
        }

    def get_performance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        report_type: str = 'performance'
    ) -> Optional[AnalyticsReport]:
        """Generar reporte de rendimiento personalizado."""
        # Filtrar métricas en el rango de tiempo
        relevant_metrics = [
            m for m in self.metrics_history
            if start_time <= m.timestamp <= end_time
        ]

        if not relevant_metrics:
            return None

        # Calcular estadísticas
        total_requests = sum(m.total_requests for m in relevant_metrics)
        avg_rps = statistics.mean(m.requests_per_second for m in relevant_metrics)
        avg_error_rate = statistics.mean(m.error_rate for m in relevant_metrics)
        avg_latency = statistics.mean(m.avg_response_time_ms for m in relevant_metrics)

        # Crear reporte
        report = AnalyticsReport(
            report_id=f"custom_{report_type}_{int(time.time())}",
            report_type=report_type,
            time_range=(start_time, end_time),
            generated_at=datetime.now(),
            summary={
                'total_requests': total_requests,
                'avg_requests_per_second': avg_rps,
                'avg_error_rate': avg_error_rate,
                'avg_response_time_ms': avg_latency,
                'data_points': len(relevant_metrics)
            },
            recommendations=self._generate_recommendations(avg_error_rate, avg_latency, total_requests)
        )

        return report

    def _generate_recommendations(self, error_rate: float, avg_latency: float, total_requests: int) -> List[str]:
        """Generar recomendaciones basadas en métricas."""
        recommendations = []

        if error_rate > 0.1:
            recommendations.append("Critical: High error rate detected. Check endpoint health and failover mechanisms.")
        elif error_rate > 0.05:
            recommendations.append("Warning: Elevated error rate. Monitor endpoint health closely.")

        if avg_latency > 1000:
            recommendations.append("Performance: High latency detected. Consider geo-routing optimizations.")
        elif avg_latency > 500:
            recommendations.append("Optimization: Moderate latency. Review regional distribution.")

        if total_requests > 10000:  # Alto volumen
            recommendations.append("Scaling: High request volume. Consider additional capacity planning.")

        return recommendations