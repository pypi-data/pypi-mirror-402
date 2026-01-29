"""
Dashboard de auditoría para AILOOS.
Interfaz web para monitoreo en tiempo real y análisis de logs.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..core.config import get_config
from .audit_manager import get_audit_manager
from .security_monitor import get_security_monitor
from .metrics_collector import get_metrics_collector
from .structured_logger import get_structured_logger

logger = get_structured_logger("audit_dashboard")


class AuditDashboard:
    """
    Dashboard interactivo para monitoreo de auditoría y seguridad.
    Proporciona vistas en tiempo real y análisis históricos.
    """

    def __init__(self):
        self.config = get_config()
        self.audit_manager = get_audit_manager()
        self.security_monitor = get_security_monitor()
        self.metrics_collector = get_metrics_collector()

        # Configuración del dashboard
        self.refresh_interval = getattr(self.config, 'dashboard_refresh_seconds', 30)
        self.max_history_hours = getattr(self.config, 'dashboard_history_hours', 24)

        # Estado del dashboard
        self.active_connections: set = set()
        self.dashboard_data: Dict[str, Any] = {}

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos completos del dashboard."""
        try:
            # Estadísticas generales
            audit_stats = self.audit_manager.get_audit_statistics()
            security_status = self.security_monitor.get_security_status()
            latest_metrics = self.metrics_collector.get_latest_metrics()
            health_status = self.metrics_collector.get_health_status()

            # Eventos recientes
            recent_events = self.audit_manager.get_audit_events(
                start_date=datetime.now() - timedelta(hours=1),
                limit=20
            )

            # Alertas activas
            active_alerts = self.audit_manager.get_security_alerts(
                acknowledged=False,
                limit=10
            )

            # Métricas de rendimiento
            performance_stats = self.metrics_collector.get_performance_stats()

            # Historial de métricas (últimas 6 horas)
            metrics_history = self.metrics_collector.get_metrics_history(hours=6)

            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_events_24h": audit_stats.get('events_last_24h', 0),
                    "active_alerts": len(active_alerts),
                    "system_health": health_status.get('overall_status', 'unknown'),
                    "active_sessions": audit_stats.get('active_sessions', 0)
                },
                "security": {
                    "blocked_ips": security_status.get('blocked_ips_count', 0),
                    "blocked_users": security_status.get('blocked_users_count', 0),
                    "threat_indicators": security_status.get('threat_indicators_count', 0),
                    "active_alerts": [alert.to_dict() for alert in active_alerts]
                },
                "performance": {
                    "current": performance_stats.get('current', {}),
                    "trends": performance_stats.get('trends', {}),
                    "response_time_avg": performance_stats.get('current', {}).get('response_time_avg', 0),
                    "error_rate": performance_stats.get('current', {}).get('error_rate', 0),
                    "throughput": performance_stats.get('current', {}).get('throughput_requests_per_sec', 0)
                },
                "system": {
                    "cpu_usage": latest_metrics.get('resource', {}).get('cpu_usage_percent', 0),
                    "memory_usage": latest_metrics.get('resource', {}).get('memory_usage_percent', 0),
                    "disk_usage": latest_metrics.get('resource', {}).get('disk_usage_percent', 0),
                    "active_connections": latest_metrics.get('performance', {}).get('active_connections', 0),
                    "services_health": health_status.get('services', {})
                },
                "knowledge_graph": {
                    "triple_count": latest_metrics.get('knowledge_graph', {}).get('triple_count', 0),
                    "queries_per_second": latest_metrics.get('knowledge_graph', {}).get('queries_per_second', 0),
                    "inferences_executed": latest_metrics.get('knowledge_graph', {}).get('inferences_executed', 0),
                    "operation_latency_avg": latest_metrics.get('knowledge_graph', {}).get('operation_latency_avg', 0),
                    "active_queries": latest_metrics.get('knowledge_graph', {}).get('active_queries', 0),
                    "failed_queries": latest_metrics.get('knowledge_graph', {}).get('failed_queries', 0),
                    "cache_hit_rate": latest_metrics.get('knowledge_graph', {}).get('cache_hit_rate', 0),
                    "storage_size_mb": latest_metrics.get('knowledge_graph', {}).get('storage_size_mb', 0)
                },
                "recent_activity": {
                    "events": [event.to_dict() for event in recent_events],
                    "alerts": [alert.to_dict() for alert in active_alerts]
                },
                "charts": {
                    "metrics_history": metrics_history,
                    "events_timeline": self._generate_events_timeline(recent_events),
                    "alerts_timeline": self._generate_alerts_timeline(active_alerts),
                    "kg_metrics_history": self._generate_kg_metrics_history(metrics_history)
                }
            }

            # Cachear datos
            self.dashboard_data = dashboard_data

            return dashboard_data

        except Exception as e:
            logger.error("Error generating dashboard data", error=str(e))
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {"total_events_24h": 0, "active_alerts": 0, "system_health": "error"}
            }

    def _generate_events_timeline(self, events: List) -> List[Dict[str, Any]]:
        """Generar datos de timeline para eventos."""
        timeline = []
        now = datetime.now()

        # Agrupar por hora
        hourly_counts = {}
        for event in events:
            hour = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hour_str = hour.isoformat()
            hourly_counts[hour_str] = hourly_counts.get(hour_str, 0) + 1

        # Crear puntos de datos
        for hour_str, count in hourly_counts.items():
            timeline.append({
                "timestamp": hour_str,
                "count": count,
                "type": "events"
            })

        return sorted(timeline, key=lambda x: x['timestamp'])

    def _generate_alerts_timeline(self, alerts: List) -> List[Dict[str, Any]]:
        """Generar datos de timeline para alertas."""
        timeline = []
        now = datetime.now()

        # Agrupar por hora
        hourly_counts = {}
        for alert in alerts:
            hour = alert.timestamp.replace(minute=0, second=0, microsecond=0)
            hour_str = hour.isoformat()
            hourly_counts[hour_str] = hourly_counts.get(hour_str, 0) + 1

        # Crear puntos de datos
        for hour_str, count in hourly_counts.items():
            timeline.append({
                "timestamp": hour_str,
                "count": count,
                "type": "alerts"
            })

        return sorted(timeline, key=lambda x: x['timestamp'])

    def _generate_kg_metrics_history(self, metrics_history: Dict) -> List[Dict[str, Any]]:
        """Generar historial de métricas del Knowledge Graph."""
        kg_history = metrics_history.get('knowledge_graph', [])

        return [{
            "timestamp": m.get('timestamp'),
            "triple_count": m.get('triple_count', 0),
            "queries_per_second": m.get('queries_per_second', 0),
            "operation_latency_avg": m.get('operation_latency_avg', 0),
            "active_queries": m.get('active_queries', 0)
        } for m in kg_history]

    async def get_security_overview(self) -> Dict[str, Any]:
        """Obtener vista general de seguridad."""
        try:
            security_status = self.security_monitor.get_security_status()
            active_alerts = self.audit_manager.get_security_alerts(acknowledged=False, limit=50)

            # Análisis de amenazas recientes
            recent_threats = []
            for alert in active_alerts:
                if alert.level.value in ['high', 'critical']:
                    recent_threats.append({
                        "title": alert.title,
                        "description": alert.description,
                        "level": alert.level.value,
                        "timestamp": alert.timestamp.isoformat()
                    })

            # Estadísticas de seguridad
            security_stats = {
                "threats_detected": len(recent_threats),
                "blocked_entities": security_status.get('blocked_ips_count', 0) + security_status.get('blocked_users_count', 0),
                "active_indicators": security_status.get('threat_indicators_count', 0),
                "security_score": self._calculate_security_score(active_alerts, security_status)
            }

            return {
                "status": security_stats,
                "recent_threats": recent_threats[:10],  # Top 10
                "blocked_entities": {
                    "ips": security_status.get('blocked_ips_count', 0),
                    "users": security_status.get('blocked_users_count', 0)
                },
                "recommendations": self._generate_security_recommendations(security_stats, active_alerts)
            }

        except Exception as e:
            logger.error("Error generating security overview", error=str(e))
            return {"error": str(e)}

    def _calculate_security_score(self, alerts: List, security_status: Dict) -> float:
        """Calcular puntuación de seguridad (0-100)."""
        base_score = 100.0

        # Penalizaciones por alertas
        critical_alerts = len([a for a in alerts if a.level.value == 'critical'])
        high_alerts = len([a for a in alerts if a.level.value == 'high'])

        base_score -= critical_alerts * 20  # -20 por alerta crítica
        base_score -= high_alerts * 10      # -10 por alerta alta
        base_score -= len(alerts) * 2       # -2 por cualquier alerta

        # Penalizaciones por entidades bloqueadas
        blocked_count = security_status.get('blocked_ips_count', 0) + security_status.get('blocked_users_count', 0)
        base_score -= blocked_count * 1     # -1 por entidad bloqueada

        return max(0.0, min(100.0, base_score))

    def _generate_security_recommendations(self, security_stats: Dict, alerts: List) -> List[str]:
        """Generar recomendaciones de seguridad."""
        recommendations = []

        if security_stats['threats_detected'] > 5:
            recommendations.append("🚨 Alto número de amenazas detectadas. Revisar configuración de seguridad.")

        if security_stats['blocked_entities'] > 10:
            recommendations.append("⚠️ Múltiples entidades bloqueadas. Considerar revisión de reglas de bloqueo.")

        if security_stats['security_score'] < 50:
            recommendations.append("🔴 Puntuación de seguridad baja. Acción inmediata requerida.")

        critical_alerts = [a for a in alerts if a.level.value == 'critical']
        if critical_alerts:
            recommendations.append(f"🚨 {len(critical_alerts)} alertas críticas activas. Revisar inmediatamente.")

        if not recommendations:
            recommendations.append("✅ Estado de seguridad aceptable. Continuar monitoreo.")

        return recommendations

    async def get_performance_overview(self) -> Dict[str, Any]:
        """Obtener vista general de rendimiento."""
        try:
            performance_stats = self.metrics_collector.get_performance_stats()
            latest_metrics = self.metrics_collector.get_latest_metrics()
            health_status = self.metrics_collector.get_health_status()

            # Análisis de rendimiento
            current = performance_stats.get('current', {})
            trends = performance_stats.get('trends', {})

            performance_analysis = {
                "response_time_status": self._analyze_response_time(current.get('response_time_avg', 0)),
                "error_rate_status": self._analyze_error_rate(current.get('error_rate', 0)),
                "throughput_status": self._analyze_throughput(current.get('throughput_requests_per_sec', 0)),
                "resource_usage": {
                    "cpu": self._analyze_resource_usage(latest_metrics.get('resource', {}).get('cpu_usage_percent', 0), "CPU"),
                    "memory": self._analyze_resource_usage(latest_metrics.get('resource', {}).get('memory_usage_percent', 0), "Memory"),
                    "disk": self._analyze_resource_usage(latest_metrics.get('resource', {}).get('disk_usage_percent', 0), "Disk")
                }
            }

            return {
                "current_metrics": current,
                "trends": trends,
                "analysis": performance_analysis,
                "services_health": health_status.get('services', {}),
                "recommendations": self._generate_performance_recommendations(performance_analysis, trends)
            }

        except Exception as e:
            logger.error("Error generating performance overview", error=str(e))
            return {"error": str(e)}

    def _analyze_response_time(self, avg_time: float) -> str:
        """Analizar tiempo de respuesta."""
        if avg_time < 100:
            return "excellent"
        elif avg_time < 500:
            return "good"
        elif avg_time < 2000:
            return "warning"
        else:
            return "critical"

    def _analyze_error_rate(self, error_rate: float) -> str:
        """Analizar tasa de error."""
        if error_rate < 0.01:  # < 1%
            return "excellent"
        elif error_rate < 0.05:  # < 5%
            return "good"
        elif error_rate < 0.10:  # < 10%
            return "warning"
        else:
            return "critical"

    def _analyze_throughput(self, throughput: float) -> str:
        """Analizar throughput."""
        if throughput > 100:
            return "excellent"
        elif throughput > 50:
            return "good"
        elif throughput > 20:
            return "warning"
        else:
            return "critical"

    def _analyze_resource_usage(self, usage_percent: float, resource: str) -> str:
        """Analizar uso de recursos."""
        if usage_percent < 50:
            return "excellent"
        elif usage_percent < 70:
            return "good"
        elif usage_percent < 85:
            return "warning"
        else:
            return "critical"

    def _generate_performance_recommendations(self, analysis: Dict, trends: Dict) -> List[str]:
        """Generar recomendaciones de rendimiento."""
        recommendations = []

        # Análisis de tendencias
        response_time_trend = trends.get('response_time_percent_change', 0)
        if response_time_trend > 20:
            recommendations.append("📈 Tiempo de respuesta aumentando. Considerar optimización.")

        # Análisis de estado actual
        if analysis['response_time_status'] == 'critical':
            recommendations.append("🚨 Tiempos de respuesta críticos. Acción inmediata requerida.")

        if analysis['error_rate_status'] == 'critical':
            recommendations.append("🔴 Alta tasa de errores. Revisar logs de error.")

        if analysis['throughput_status'] == 'critical':
            recommendations.append("🐌 Throughput bajo. Considerar escalado horizontal.")

        # Análisis de recursos
        for resource, status in analysis['resource_usage'].items():
            if status == 'critical':
                recommendations.append(f"💥 Uso de {resource} crítico. Liberar recursos o escalar.")

        if not recommendations:
            recommendations.append("✅ Rendimiento aceptable. Continuar monitoreo.")

        return recommendations

    async def export_dashboard_report(self, format: str = 'json') -> str:
        """Exportar reporte completo del dashboard."""
        try:
            data = await self.get_dashboard_data()
            security = await self.get_security_overview()
            performance = await self.get_performance_overview()

            report = {
                "generated_at": datetime.now().isoformat(),
                "dashboard": data,
                "security_overview": security,
                "performance_overview": performance,
                "metadata": {
                    "format": format,
                    "version": "1.0",
                    "system": "AILOOS Audit Dashboard"
                }
            }

            if format == 'json':
                return json.dumps(report, indent=2, ensure_ascii=False)
            else:
                # Para otros formatos, devolver JSON por ahora
                return json.dumps(report, ensure_ascii=False)

        except Exception as e:
            logger.error("Error exporting dashboard report", error=str(e))
            return json.dumps({"error": str(e)}, indent=2)

    async def start_realtime_updates(self, websocket_connection):
        """Iniciar actualizaciones en tiempo real para un cliente."""
        self.active_connections.add(websocket_connection)

        try:
            while True:
                # Enviar actualización cada refresh_interval segundos
                data = await self.get_dashboard_data()
                await websocket_connection.send_json({
                    "type": "dashboard_update",
                    "data": data
                })

                await asyncio.sleep(self.refresh_interval)

        except Exception as e:
            logger.error("Error in realtime updates", error=str(e))
        finally:
            self.active_connections.discard(websocket_connection)

    def get_connected_clients_count(self) -> int:
        """Obtener número de clientes conectados al dashboard."""
        return len(self.active_connections)


# Instancia global
audit_dashboard = AuditDashboard()


def get_audit_dashboard() -> AuditDashboard:
    """Obtener instancia global del dashboard de auditoría."""
    return audit_dashboard