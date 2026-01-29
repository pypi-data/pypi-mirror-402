import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class SyncStatus(Enum):
    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    SYNCING = "syncing"
    ERROR = "error"

@dataclass
class ApplicationMetrics:
    name: str
    health_status: HealthStatus
    sync_status: SyncStatus
    last_sync_time: Optional[datetime]
    last_health_check: Optional[datetime]
    error_count: int
    sync_count: int
    uptime_percentage: float

class GitOpsMonitoring:
    """
    Monitoreo de estado de GitOps para aplicaciones desplegadas.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.monitor_interval = config.get('monitor_interval', 30)  # segundos
        self.health_check_timeout = config.get('health_check_timeout', 10)
        self.alert_thresholds = config.get('alert_thresholds', {
            'error_count': 5,
            'sync_age_hours': 2,
            'uptime_percentage': 95.0
        })
        self.applications: Dict[str, ApplicationMetrics] = {}
        self.alert_callbacks: List[Callable] = []
        self.running = False

    async def initialize(self) -> bool:
        """Inicializa el sistema de monitoreo."""
        try:
            logger.info("GitOps monitoring initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing GitOps monitoring: {e}")
            return False

    async def start_monitoring(self, app_name: str):
        """Inicia el monitoreo de una aplicación."""
        try:
            if app_name not in self.applications:
                self.applications[app_name] = ApplicationMetrics(
                    name=app_name,
                    health_status=HealthStatus.UNKNOWN,
                    sync_status=SyncStatus.UNKNOWN,
                    last_sync_time=None,
                    last_health_check=None,
                    error_count=0,
                    sync_count=0,
                    uptime_percentage=100.0
                )

            logger.info(f"Started monitoring application {app_name}")
        except Exception as e:
            logger.error(f"Error starting monitoring for {app_name}: {e}")

    async def stop_monitoring(self):
        """Detiene todo el monitoreo."""
        self.running = False
        logger.info("GitOps monitoring stopped")

    def register_alert_callback(self, callback: Callable):
        """Registra un callback para alertas."""
        self.alert_callbacks.append(callback)

    async def update_application_status(self, app_name: str, health_status: HealthStatus,
                                      sync_status: SyncStatus, last_sync: Optional[datetime] = None):
        """
        Actualiza el estado de una aplicación.

        Args:
            app_name: Nombre de la aplicación
            health_status: Estado de salud
            sync_status: Estado de sincronización
            last_sync: Última sincronización
        """
        try:
            if app_name not in self.applications:
                await self.start_monitoring(app_name)

            metrics = self.applications[app_name]
            old_health = metrics.health_status
            old_sync = metrics.sync_status

            metrics.health_status = health_status
            metrics.sync_status = sync_status
            metrics.last_health_check = datetime.now()

            if last_sync:
                metrics.last_sync_time = last_sync
                metrics.sync_count += 1

            # Calcular uptime
            metrics.uptime_percentage = self._calculate_uptime(metrics)

            # Verificar alertas
            await self._check_alerts(metrics, old_health, old_sync)

            logger.debug(f"Updated status for {app_name}: health={health_status.value}, sync={sync_status.value}")

        except Exception as e:
            logger.error(f"Error updating status for {app_name}: {e}")

    async def record_error(self, app_name: str, error_message: str):
        """Registra un error para una aplicación."""
        try:
            if app_name in self.applications:
                self.applications[app_name].error_count += 1
                await self._check_alerts(self.applications[app_name])
                logger.warning(f"Error recorded for {app_name}: {error_message}")
        except Exception as e:
            logger.error(f"Error recording error for {app_name}: {e}")

    def get_application_metrics(self, app_name: str) -> Optional[ApplicationMetrics]:
        """Obtiene las métricas de una aplicación."""
        return self.applications.get(app_name)

    def get_all_metrics(self) -> List[ApplicationMetrics]:
        """Obtiene métricas de todas las aplicaciones."""
        return list(self.applications.values())

    def get_health_summary(self) -> Dict:
        """Obtiene un resumen del estado de salud general."""
        total = len(self.applications)
        if total == 0:
            return {'total': 0, 'healthy': 0, 'degraded': 0, 'unhealthy': 0}

        healthy = sum(1 for m in self.applications.values() if m.health_status == HealthStatus.HEALTHY)
        degraded = sum(1 for m in self.applications.values() if m.health_status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for m in self.applications.values() if m.health_status == HealthStatus.UNHEALTHY)

        return {
            'total': total,
            'healthy': healthy,
            'degraded': degraded,
            'unhealthy': unhealthy,
            'healthy_percentage': (healthy / total) * 100 if total > 0 else 0
        }

    async def run_health_checks(self):
        """Ejecuta verificaciones de salud periódicas."""
        self.running = True
        while self.running:
            try:
                for app_name in list(self.applications.keys()):
                    await self._perform_health_check(app_name)

                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.monitor_interval)

    async def _perform_health_check(self, app_name: str):
        """Realiza una verificación de salud para una aplicación."""
        try:
            # Aquí se integraría con ArgoCD/Flux para obtener estado real
            # Por simplicidad, simulamos una verificación

            # Simular verificación de salud
            # En implementación real, consultar APIs de ArgoCD/Flux/Kubernetes

            # Para demo, asumir healthy si no hay errores recientes
            metrics = self.applications[app_name]

            # Verificar si la sincronización está desactualizada
            if metrics.last_sync_time:
                sync_age = datetime.now() - metrics.last_sync_time
                if sync_age > timedelta(hours=self.alert_thresholds['sync_age_hours']):
                    await self.update_application_status(
                        app_name, HealthStatus.DEGRADED, SyncStatus.OUT_OF_SYNC
                    )
                    return

            # Verificar errores
            if metrics.error_count > self.alert_thresholds['error_count']:
                await self.update_application_status(
                    app_name, HealthStatus.UNHEALTHY, metrics.sync_status
                )
                return

            # Asumir healthy si pasa las verificaciones
            await self.update_application_status(
                app_name, HealthStatus.HEALTHY, SyncStatus.SYNCED
            )

        except Exception as e:
            logger.error(f"Error performing health check for {app_name}: {e}")
            await self.record_error(app_name, str(e))

    def _calculate_uptime(self, metrics: ApplicationMetrics) -> float:
        """Calcula el porcentaje de uptime basado en el historial."""
        # Implementación simplificada
        # En producción, mantener un historial de estados
        if metrics.error_count == 0:
            return 100.0
        elif metrics.error_count < 3:
            return 95.0
        else:
            return 80.0

    async def _check_alerts(self, metrics: ApplicationMetrics,
                          old_health: Optional[HealthStatus] = None,
                          old_sync: Optional[SyncStatus] = None):
        """Verifica si se deben generar alertas."""
        try:
            alerts = []

            # Alerta por cambio de estado de salud
            if old_health and old_health != metrics.health_status:
                if metrics.health_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
                    alerts.append({
                        'type': 'health_change',
                        'severity': 'warning' if metrics.health_status == HealthStatus.DEGRADED else 'error',
                        'message': f"Application {metrics.name} health changed from {old_health.value} to {metrics.health_status.value}"
                    })

            # Alerta por cambio de estado de sync
            if old_sync and old_sync != metrics.sync_status:
                if metrics.sync_status == SyncStatus.ERROR:
                    alerts.append({
                        'type': 'sync_error',
                        'severity': 'error',
                        'message': f"Application {metrics.name} sync status changed to error"
                    })

            # Alerta por muchos errores
            if metrics.error_count >= self.alert_thresholds['error_count']:
                alerts.append({
                    'type': 'error_threshold',
                    'severity': 'error',
                    'message': f"Application {metrics.name} has {metrics.error_count} errors (threshold: {self.alert_thresholds['error_count']})"
                })

            # Alerta por uptime bajo
            if metrics.uptime_percentage < self.alert_thresholds['uptime_percentage']:
                alerts.append({
                    'type': 'uptime_low',
                    'severity': 'warning',
                    'message': f"Application {metrics.name} uptime is {metrics.uptime_percentage:.1f}% (threshold: {self.alert_thresholds['uptime_percentage']}%)"
                })

            # Enviar alertas
            for alert in alerts:
                await self._send_alert(alert)

        except Exception as e:
            logger.error(f"Error checking alerts for {metrics.name}: {e}")

    async def _send_alert(self, alert: Dict):
        """Envía una alerta a través de los callbacks registrados."""
        try:
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")

            logger.warning(f"Alert sent: {alert}")
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    def export_metrics(self) -> Dict:
        """Exporta métricas en formato Prometheus-like."""
        metrics = {}

        for app_name, app_metrics in self.applications.items():
            metrics[f"gitops_app_health_status{{app=\"{app_name}\"}}"] = \
                1 if app_metrics.health_status == HealthStatus.HEALTHY else 0
            metrics[f"gitops_app_sync_status{{app=\"{app_name}\"}}"] = \
                1 if app_metrics.sync_status == SyncStatus.SYNCED else 0
            metrics[f"gitops_app_error_count{{app=\"{app_name}\"}}"] = app_metrics.error_count
            metrics[f"gitops_app_sync_count{{app=\"{app_name}\"}}"] = app_metrics.sync_count
            metrics[f"gitops_app_uptime_percentage{{app=\"{app_name}\"}}"] = app_metrics.uptime_percentage

        return metrics