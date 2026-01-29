import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


logger = logging.getLogger(__name__)


class CanaryMetric(Enum):
    """Métricas disponibles para monitoreo de canary"""
    RESPONSE_TIME = "response_time_ms"
    ERROR_RATE = "error_rate_percent"
    SUCCESS_RATE = "success_rate_percent"
    THROUGHPUT = "requests_per_second"
    CPU_USAGE = "cpu_usage_percent"
    MEMORY_USAGE = "memory_usage_percent"
    LATENCY_P95 = "latency_p95_ms"
    LATENCY_P99 = "latency_p99_ms"


class AlertSeverity(Enum):
    """Severidades de alertas de canary"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CanaryAlertRule:
    """Regla de alerta para canary"""
    rule_id: str
    metric: CanaryMetric
    condition: str  # e.g., "value > 100" or "baseline_diff > 0.1"
    severity: AlertSeverity
    threshold: float
    cooldown_minutes: int = 5
    enabled: bool = True


@dataclass
class CanaryMetricsSnapshot:
    """Snapshot de métricas de canary"""
    timestamp: datetime
    canary_version: str
    baseline_version: str
    metrics: Dict[CanaryMetric, float] = field(default_factory=dict)
    baseline_metrics: Dict[CanaryMetric, float] = field(default_factory=dict)
    traffic_percentage: float = 0.0
    sample_size: int = 0


@dataclass
class TrendAnalysis:
    """Análisis de tendencias"""
    metric: CanaryMetric
    trend_direction: str  # "improving", "degrading", "stable"
    change_rate: float
    confidence: float
    period_hours: int
    recommendation: str


class CanaryMonitor:
    """
    Monitor avanzado para despliegues canary.
    Proporciona monitoreo en tiempo real, dashboards, alertas y análisis de tendencias.
    """

    def __init__(self,
                 canary_version: str,
                 baseline_version: str,
                 metrics_api_url: str = "http://localhost:8080",
                 alert_email_config: Optional[Dict[str, Any]] = None,
                 slack_webhook_url: str = "",
                 logger: Optional[logging.Logger] = None):

        self.canary_version = canary_version
        self.baseline_version = baseline_version
        self.metrics_api_url = metrics_api_url
        self.logger = logger or logging.getLogger(__name__)

        # Configuración de alertas
        self.alert_email_config = alert_email_config or {}
        self.slack_webhook_url = slack_webhook_url

        # Estado del monitoreo
        self.monitoring_active = False
        self.collection_interval = 30  # segundos
        self.alert_rules: Dict[str, CanaryAlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []

        # Almacenamiento de métricas históricas
        self.metrics_history: List[CanaryMetricsSnapshot] = []
        self.max_history_size = 1000

        # Callbacks para integración
        self.metric_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []

        # Dashboard data
        self.dashboard_data: Dict[str, Any] = {}

        # Configurar reglas de alerta por defecto
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self):
        """Configurar reglas de alerta por defecto"""
        default_rules = [
            CanaryAlertRule(
                rule_id="high_error_rate",
                metric=CanaryMetric.ERROR_RATE,
                condition="value > 5.0",
                severity=AlertSeverity.WARNING,
                threshold=5.0,
                cooldown_minutes=10
            ),
            CanaryAlertRule(
                rule_id="response_time_degradation",
                metric=CanaryMetric.RESPONSE_TIME,
                condition="baseline_diff > 50",
                severity=AlertSeverity.ERROR,
                threshold=50.0,
                cooldown_minutes=5
            ),
            CanaryAlertRule(
                rule_id="critical_error_rate",
                metric=CanaryMetric.ERROR_RATE,
                condition="value > 10.0",
                severity=AlertSeverity.CRITICAL,
                threshold=10.0,
                cooldown_minutes=2
            ),
            CanaryAlertRule(
                rule_id="latency_spike",
                metric=CanaryMetric.LATENCY_P99,
                condition="baseline_diff > 100",
                severity=AlertSeverity.WARNING,
                threshold=100.0,
                cooldown_minutes=5
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    async def start_monitoring(self, traffic_percentage: float = 10.0):
        """Iniciar monitoreo de canary"""
        if self.monitoring_active:
            self.logger.warning("Monitoreo de canary ya está activo")
            return

        self.monitoring_active = True
        self.traffic_percentage = traffic_percentage
        self.start_time = datetime.now()

        self.logger.info(f"Iniciando monitoreo de canary: {self.canary_version} vs {self.baseline_version}")

        # Iniciar tareas de monitoreo
        asyncio.create_task(self._metrics_collection_loop())
        asyncio.create_task(self._alert_evaluation_loop())
        asyncio.create_task(self._dashboard_update_loop())

    async def stop_monitoring(self):
        """Detener monitoreo de canary"""
        self.monitoring_active = False
        self.logger.info("Monitoreo de canary detenido")

    async def _metrics_collection_loop(self):
        """Loop de recolección de métricas en tiempo real"""
        while self.monitoring_active:
            try:
                await self._collect_realtime_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error en recolección de métricas: {e}")
                await asyncio.sleep(10)

    async def _collect_realtime_metrics(self):
        """Recolectar métricas en tiempo real de canary y baseline"""
        try:
            # Recolectar métricas de canary
            canary_metrics = await self._fetch_version_metrics(self.canary_version)

            # Recolectar métricas de baseline
            baseline_metrics = await self._fetch_version_metrics(self.baseline_version)

            # Crear snapshot
            snapshot = CanaryMetricsSnapshot(
                timestamp=datetime.now(),
                canary_version=self.canary_version,
                baseline_version=self.baseline_version,
                metrics=canary_metrics,
                baseline_metrics=baseline_metrics,
                traffic_percentage=self.traffic_percentage,
                sample_size=100  # Simulado
            )

            # Almacenar en historial
            self._store_metrics_snapshot(snapshot)

            # Ejecutar callbacks
            for callback in self.metric_callbacks:
                try:
                    await callback(snapshot)
                except Exception as e:
                    self.logger.error(f"Error en callback de métricas: {e}")

            self.logger.debug(f"Métricas recolectadas: canary={len(canary_metrics)}, baseline={len(baseline_metrics)}")

        except Exception as e:
            self.logger.error(f"Error recolectando métricas: {e}")

    async def _fetch_version_metrics(self, version: str) -> Dict[CanaryMetric, float]:
        """Obtener métricas de una versión específica"""
        try:
            # En implementación real, esto haría llamadas API a los servicios
            # Por simplicidad, simulamos métricas
            metrics = {}

            async with aiohttp.ClientSession() as session:
                # Simular llamada a API de métricas
                url = f"{self.metrics_api_url}/api/canary/metrics/{version}"
                # En producción: async with session.get(url) as response:

                # Simulación de métricas
                base_time = time.time()
                metrics = {
                    CanaryMetric.RESPONSE_TIME: 150 + (hash(version) % 50),  # 150-200ms
                    CanaryMetric.ERROR_RATE: 2.0 + (hash(version + "error") % 5),  # 2-7%
                    CanaryMetric.SUCCESS_RATE: 95.0 + (hash(version + "success") % 5),  # 95-100%
                    CanaryMetric.THROUGHPUT: 100 + (hash(version + "throughput") % 50),  # 100-150 req/s
                    CanaryMetric.CPU_USAGE: 45 + (hash(version + "cpu") % 30),  # 45-75%
                    CanaryMetric.MEMORY_USAGE: 60 + (hash(version + "memory") % 20),  # 60-80%
                    CanaryMetric.LATENCY_P95: 200 + (hash(version + "p95") % 100),  # 200-300ms
                    CanaryMetric.LATENCY_P99: 300 + (hash(version + "p99") % 200),  # 300-500ms
                }

            return metrics

        except Exception as e:
            self.logger.error(f"Error obteniendo métricas para {version}: {e}")
            return {}

    def _store_metrics_snapshot(self, snapshot: CanaryMetricsSnapshot):
        """Almacenar snapshot de métricas en historial"""
        self.metrics_history.append(snapshot)

        # Mantener límite de historial
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)

    async def _alert_evaluation_loop(self):
        """Loop de evaluación de reglas de alerta"""
        while self.monitoring_active:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(60)  # Evaluar cada minuto
            except Exception as e:
                self.logger.error(f"Error evaluando alertas: {e}")
                await asyncio.sleep(30)

    async def _evaluate_alert_rules(self):
        """Evaluar todas las reglas de alerta activas"""
        if not self.metrics_history:
            return

        latest_snapshot = self.metrics_history[-1]

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            try:
                if await self._check_alert_condition(rule, latest_snapshot):
                    await self._trigger_alert(rule, latest_snapshot)
            except Exception as e:
                self.logger.error(f"Error evaluando regla {rule.rule_id}: {e}")

    async def _check_alert_condition(self, rule: CanaryAlertRule, snapshot: CanaryMetricsSnapshot) -> bool:
        """Verificar condición de alerta"""
        try:
            canary_value = snapshot.metrics.get(rule.metric, 0)
            baseline_value = snapshot.baseline_metrics.get(rule.metric, 0)
            diff = canary_value - baseline_value

            if "value >" in rule.condition:
                threshold = float(rule.condition.split(">")[1])
                return canary_value > threshold
            elif "baseline_diff >" in rule.condition:
                threshold = float(rule.condition.split(">")[1])
                return diff > threshold
            elif "value <" in rule.condition:
                threshold = float(rule.condition.split("<")[1])
                return canary_value < threshold

            return False

        except Exception as e:
            self.logger.error(f"Error verificando condición: {e}")
            return False

    async def _trigger_alert(self, rule: CanaryAlertRule, snapshot: CanaryMetricsSnapshot):
        """Disparar alerta"""
        try:
            # Verificar cooldown
            alert_key = f"{rule.rule_id}_{snapshot.timestamp.strftime('%Y%m%d%H%M')}"
            if alert_key in self.active_alerts:
                last_triggered = self.active_alerts[alert_key].get("last_triggered")
                if last_triggered and (datetime.now() - last_triggered).seconds < rule.cooldown_minutes * 60:
                    return

            # Crear alerta
            alert = {
                "alert_id": f"canary_alert_{int(time.time())}_{rule.rule_id}",
                "rule_id": rule.rule_id,
                "severity": rule.severity.value,
                "message": self._format_alert_message(rule, snapshot),
                "canary_version": snapshot.canary_version,
                "baseline_version": snapshot.baseline_version,
                "metric": rule.metric.value,
                "canary_value": snapshot.metrics.get(rule.metric, 0),
                "baseline_value": snapshot.baseline_metrics.get(rule.metric, 0),
                "traffic_percentage": snapshot.traffic_percentage,
                "timestamp": snapshot.timestamp.isoformat(),
                "last_triggered": datetime.now()
            }

            # Añadir a alertas activas
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            # Enviar notificaciones
            await self._send_alert_notifications(alert)

            # Ejecutar callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    self.logger.error(f"Error en callback de alerta: {e}")

            self.logger.warning(f"Alerta canary disparada: {rule.rule_id} ({rule.severity.value})")

        except Exception as e:
            self.logger.error(f"Error disparando alerta: {e}")

    def _format_alert_message(self, rule: CanaryAlertRule, snapshot: CanaryMetricsSnapshot) -> str:
        """Formatear mensaje de alerta"""
        canary_val = snapshot.metrics.get(rule.metric, 0)
        baseline_val = snapshot.baseline_metrics.get(rule.metric, 0)
        diff = canary_val - baseline_val

        return (f"🚨 CANARY ALERT: {rule.metric.value} - "
                f"Canary: {canary_val:.2f}, Baseline: {baseline_val:.2f}, "
                f"Diff: {diff:+.2f} (Traffic: {snapshot.traffic_percentage:.1f}%)")

    async def _send_alert_notifications(self, alert: Dict[str, Any]):
        """Enviar notificaciones de alerta"""
        try:
            # Email
            if self.alert_email_config.get("enabled", False):
                await self._send_email_alert(alert)

            # Slack
            if self.slack_webhook_url:
                await self._send_slack_alert(alert)

        except Exception as e:
            self.logger.error(f"Error enviando notificaciones: {e}")

    async def _send_email_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por email"""
        try:
            config = self.alert_email_config
            msg = MIMEMultipart()
            msg['From'] = config.get("username", "")
            msg['To'] = ', '.join(config.get("recipients", []))
            msg['Subject'] = f"🚨 Canary Alert - {alert['severity'].upper()}"

            body = f"""
            <h2>Alerta de Canary Deployment</h2>
            <p><strong>Severidad:</strong> {alert['severity']}</p>
            <p><strong>Mensaje:</strong> {alert['message']}</p>
            <p><strong>Versión Canary:</strong> {alert['canary_version']}</p>
            <p><strong>Versión Baseline:</strong> {alert['baseline_version']}</p>
            <p><strong>Timestamp:</strong> {alert['timestamp']}</p>

            <h3>Detalles Técnicos:</h3>
            <pre>{json.dumps(alert, indent=2)}</pre>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(config.get("smtp_server", "smtp.gmail.com"),
                                config.get("smtp_port", 587))
            server.starttls()
            server.login(config.get("username", ""), config.get("password", ""))
            server.sendmail(config.get("username", ""), config.get("recipients", []), msg.as_string())
            server.quit()

            self.logger.info("Alerta email enviada")

        except Exception as e:
            self.logger.error(f"Error enviando email: {e}")

    async def _send_slack_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por Slack"""
        try:
            payload = {
                "text": f"🚨 *Canary Alert*\n{alert['message']}",
                "attachments": [
                    {
                        "color": "danger" if alert["severity"] in ["error", "critical"] else "warning",
                        "fields": [
                            {"title": "Severity", "value": alert["severity"], "short": True},
                            {"title": "Metric", "value": alert["metric"], "short": True},
                            {"title": "Canary Version", "value": alert["canary_version"], "short": True},
                            {"title": "Traffic %", "value": f"{alert['traffic_percentage']:.1f}%", "short": True}
                        ]
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Alerta Slack enviada")
                    else:
                        self.logger.error(f"Error Slack: {response.status}")

        except Exception as e:
            self.logger.error(f"Error enviando Slack: {e}")

    async def _dashboard_update_loop(self):
        """Loop de actualización de dashboard"""
        while self.monitoring_active:
            try:
                self._update_dashboard_data()
                await asyncio.sleep(300)  # Actualizar cada 5 minutos
            except Exception as e:
                self.logger.error(f"Error actualizando dashboard: {e}")
                await asyncio.sleep(60)

    def _update_dashboard_data(self):
        """Actualizar datos del dashboard"""
        if not self.metrics_history:
            return

        latest = self.metrics_history[-1]
        recent_metrics = self.metrics_history[-20:]  # Últimas 20 mediciones

        # Calcular estadísticas
        stats = {}
        for metric in CanaryMetric:
            values = [s.metrics.get(metric, 0) for s in recent_metrics]
            baseline_values = [s.baseline_metrics.get(metric, 0) for s in recent_metrics]

            if values:
                stats[metric.value] = {
                    "current_canary": values[-1],
                    "current_baseline": baseline_values[-1] if baseline_values else 0,
                    "avg_canary": sum(values) / len(values),
                    "avg_baseline": sum(baseline_values) / len(baseline_values) if baseline_values else 0,
                    "min_canary": min(values),
                    "max_canary": max(values),
                    "trend": self._calculate_trend(values)
                }

        # Análisis de tendencias
        trends = self.analyze_trends(hours=24)

        self.dashboard_data = {
            "canary_version": self.canary_version,
            "baseline_version": self.baseline_version,
            "traffic_percentage": self.traffic_percentage,
            "monitoring_duration_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "total_samples": len(self.metrics_history),
            "latest_timestamp": latest.timestamp.isoformat(),
            "metrics_stats": stats,
            "trends": [trend.__dict__ for trend in trends],
            "active_alerts": len(self.active_alerts),
            "alerts_last_24h": len([a for a in self.alert_history
                                   if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=24)])
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendencia simple"""
        if len(values) < 2:
            return "stable"

        recent_avg = sum(values[-5:]) / min(5, len(values))
        older_avg = sum(values[:-5]) / max(1, len(values) - 5)

        diff = recent_avg - older_avg
        threshold = abs(older_avg) * 0.05  # 5% cambio

        if diff > threshold:
            return "increasing"
        elif diff < -threshold:
            return "decreasing"
        else:
            return "stable"

    def generate_dashboard_html(self) -> str:
        """Generar dashboard HTML"""
        if not self.dashboard_data:
            return "<h1>Dashboard no disponible</h1>"

        data = self.dashboard_data

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Canary Deployment Monitor</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .alert {{ color: red; }}
                .trend-up {{ color: green; }}
                .trend-down {{ color: red; }}
                .trend-stable {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>🚀 Canary Deployment Monitor</h1>

            <div class="metric">
                <h2>Estado General</h2>
                <p><strong>Canary:</strong> {data['canary_version']}</p>
                <p><strong>Baseline:</strong> {data['baseline_version']}</p>
                <p><strong>Tráfico Canary:</strong> {data['traffic_percentage']:.1f}%</p>
                <p><strong>Duración Monitoreo:</strong> {data['monitoring_duration_hours']:.1f} horas</p>
                <p><strong>Muestras Totales:</strong> {data['total_samples']}</p>
                <p><strong>Alertas Activas:</strong> <span class="alert">{data['active_alerts']}</span></p>
                <p><strong>Alertas (24h):</strong> {data['alerts_last_24h']}</p>
            </div>

            <h2>📊 Métricas Principales</h2>
            <table>
                <tr>
                    <th>Métrica</th>
                    <th>Canary Actual</th>
                    <th>Baseline Actual</th>
                    <th>Diferencia</th>
                    <th>Promedio Canary</th>
                    <th>Tendencia</th>
                </tr>
        """

        for metric_name, stats in data.get('metrics_stats', {}).items():
            diff = stats['current_canary'] - stats['current_baseline']
            trend_class = f"trend-{stats['trend']}"

            html += f"""
                <tr>
                    <td>{metric_name.replace('_', ' ').title()}</td>
                    <td>{stats['current_canary']:.2f}</td>
                    <td>{stats['current_baseline']:.2f}</td>
                    <td>{diff:+.2f}</td>
                    <td>{stats['avg_canary']:.2f}</td>
                    <td class="{trend_class}">{stats['trend'].title()}</td>
                </tr>
            """

        html += """
            </table>

            <h2>📈 Análisis de Tendencias</h2>
        """

        for trend in data.get('trends', []):
            html += f"""
            <div class="metric">
                <h3>{trend['metric'].replace('_', ' ').title()}</h3>
                <p><strong>Dirección:</strong> {trend['trend_direction']}</p>
                <p><strong>Tasa de Cambio:</strong> {trend['change_rate']:.3f}</p>
                <p><strong>Confianza:</strong> {trend['confidence']:.2f}</p>
                <p><strong>Recomendación:</strong> {trend['recommendation']}</p>
            </div>
            """

        html += """
        </body>
        </html>
        """

        return html

    def analyze_trends(self, hours: int = 24) -> List[TrendAnalysis]:
        """Analizar tendencias en las métricas"""
        if len(self.metrics_history) < 2:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [s for s in self.metrics_history if s.timestamp > cutoff_time]

        if len(recent_snapshots) < 10:  # Necesitamos suficientes datos
            return []

        trends = []

        for metric in CanaryMetric:
            values = [s.metrics.get(metric, 0) for s in recent_snapshots]
            timestamps = [(s.timestamp - recent_snapshots[0].timestamp).total_seconds() / 3600
                         for s in recent_snapshots]

            if len(values) < 5:
                continue

            # Análisis simple de regresión lineal
            n = len(values)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(timestamps, values))
            sum_x2 = sum(x * x for x in timestamps)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Calcular R² para confianza
            y_mean = sum_y / n
            ss_tot = sum((y - y_mean) ** 2 for y in values)
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(timestamps, values))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Determinar dirección de tendencia
            if slope > 0.1:
                direction = "degrading" if "error" in metric.value or "latency" in metric.value else "improving"
            elif slope < -0.1:
                direction = "improving" if "error" in metric.value or "latency" in metric.value else "degrading"
            else:
                direction = "stable"

            # Generar recomendación
            recommendation = self._generate_trend_recommendation(metric, direction, abs(slope))

            trend = TrendAnalysis(
                metric=metric,
                trend_direction=direction,
                change_rate=slope,
                confidence=min(r_squared, 1.0),
                period_hours=hours,
                recommendation=recommendation
            )

            trends.append(trend)

        return trends

    def _generate_trend_recommendation(self, metric: CanaryMetric, direction: str, change_rate: float) -> str:
        """Generar recomendación basada en tendencia"""
        if direction == "improving":
            if "error" in metric.value:
                return "✅ Error rate mejorando - Continuar monitoreo"
            elif "latency" in metric.value:
                return "✅ Latencia mejorando - Buen candidato para promoción"
            else:
                return "✅ Métrica mejorando - Tendencia positiva"
        elif direction == "degrading":
            if change_rate > 0.5:
                return "🚨 Degradación significativa - Considerar rollback inmediato"
            else:
                return "⚠️ Degradación gradual - Monitorear closely"
        else:
            return "➡️ Métrica estable - Continuar monitoreo normal"

    def add_metric_callback(self, callback: Callable):
        """Añadir callback para nuevas métricas"""
        self.metric_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable):
        """Añadir callback para alertas"""
        self.alert_callbacks.append(callback)

    def get_historical_metrics(self, hours: int = 24) -> List[CanaryMetricsSnapshot]:
        """Obtener métricas históricas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [s for s in self.metrics_history if s.timestamp > cutoff_time]

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtener historial de alertas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history
                if datetime.fromisoformat(a["timestamp"]) > cutoff_time]

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Obtener estado completo del monitoreo"""
        return {
            "monitoring_active": self.monitoring_active,
            "canary_version": self.canary_version,
            "baseline_version": self.baseline_version,
            "traffic_percentage": getattr(self, 'traffic_percentage', 0),
            "collection_interval": self.collection_interval,
            "metrics_collected": len(self.metrics_history),
            "active_alerts": len(self.active_alerts),
            "alert_rules_count": len(self.alert_rules),
            "start_time": getattr(self, 'start_time', None).isoformat() if hasattr(self, 'start_time') else None,
            "dashboard_available": bool(self.dashboard_data)
        }


# Función de conveniencia para iniciar monitoreo de canary
async def start_canary_monitoring(canary_version: str,
                                 baseline_version: str,
                                 traffic_percentage: float = 10.0,
                                 **kwargs) -> CanaryMonitor:
    """Función de conveniencia para iniciar monitoreo de canary"""
    monitor = CanaryMonitor(canary_version, baseline_version, **kwargs)
    await monitor.start_monitoring(traffic_percentage)
    return monitor