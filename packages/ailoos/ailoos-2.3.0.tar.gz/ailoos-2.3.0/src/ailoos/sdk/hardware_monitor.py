"""
HardwareMonitor - Monitor de hardware y sistema
Proporciona métricas de hardware y monitoring para nodos federados.
"""

import asyncio
import time
import psutil
import platform
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HardwareInfo:
    """Información del hardware del sistema."""
    cpu_count: int
    cpu_count_logical: int
    memory_total_gb: float
    gpu_info: str
    platform: str
    architecture: str
    hostname: str
    python_version: str


@dataclass
class SystemMetrics:
    """Métricas actuales del sistema."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    disk_percent: float
    disk_used_gb: float
    network_sent_mb: float
    network_recv_mb: float
    uptime_seconds: float
    load_average: Optional[List[float]] = None


@dataclass
class PerformanceReport:
    """Reporte completo de rendimiento."""
    generated_at: datetime
    period_seconds: float
    hardware_info: HardwareInfo
    current_metrics: SystemMetrics
    averages: Dict[str, float]
    peaks: Dict[str, float]
    recommendations: List[str]


class HardwareMonitor:
    """
    Monitor de hardware y sistema para nodos federados.

    Proporciona:
    - Información del hardware
    - Métricas en tiempo real
    - Reportes de rendimiento
    - Alertas de recursos
    """

    def __init__(self, node_id: str, monitoring_interval: int = 30):
        """
        Inicializar el monitor de hardware.

        Args:
            node_id: ID del nodo
            monitoring_interval: Intervalo de monitoreo en segundos
        """
        self.node_id = node_id
        self.monitoring_interval = monitoring_interval

        # Información del hardware
        self.hardware_info: Optional[HardwareInfo] = None

        # Estado de monitoreo
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_history: List[SystemMetrics] = []
        self._max_history_size = 1000  # Mantener últimas 1000 mediciones

        # Callbacks
        self.alert_callbacks: Dict[str, List[Callable]] = {}

        # Thresholds para alertas
        self.alert_thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_percent": 90.0
        }

        # Estadísticas
        self.stats = {
            "monitoring_started_at": None,
            "total_measurements": 0,
            "alerts_triggered": 0
        }

        logger.info(f"📊 HardwareMonitor initialized for node {node_id}")

    async def initialize(self) -> bool:
        """
        Inicializar el monitor.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            # Detectar hardware
            self.hardware_info = self._detect_hardware()

            # Primera medición
            initial_metrics = self._collect_metrics()
            self._metrics_history.append(initial_metrics)

            logger.info(f"✅ HardwareMonitor initialized for node {self.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing HardwareMonitor: {e}")
            return False

    async def start(self):
        """Iniciar monitoreo continuo."""
        if self._running:
            return

        self._running = True
        self.stats["monitoring_started_at"] = datetime.now()

        # Iniciar tarea de monitoreo
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"▶️ HardwareMonitor started for node {self.node_id}")

    async def stop(self):
        """Detener monitoreo."""
        if not self._running:
            return

        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info(f"⏹️ HardwareMonitor stopped for node {self.node_id}")

    def _detect_hardware(self) -> HardwareInfo:
        """Detectar información del hardware."""
        try:
            # CPU
            cpu_count = psutil.cpu_count(logical=False) or 1
            cpu_count_logical = psutil.cpu_count(logical=True) or cpu_count

            # Memoria
            memory = psutil.virtual_memory()
            memory_total_gb = round(memory.total / (1024**3), 1)

            # GPU (simplificado)
            gpu_info = "Unknown"
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = torch.cuda.get_device_name(0)
                else:
                    gpu_info = "CPU Only"
            except ImportError:
                gpu_info = "PyTorch not available"

            # Sistema
            platform_info = platform.system()
            architecture = platform.machine()
            hostname = platform.node()

            # Python
            python_version = platform.python_version()

            return HardwareInfo(
                cpu_count=cpu_count,
                cpu_count_logical=cpu_count_logical,
                memory_total_gb=memory_total_gb,
                gpu_info=gpu_info,
                platform=platform_info,
                architecture=architecture,
                hostname=hostname,
                python_version=python_version
            )

        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}")
            return HardwareInfo(
                cpu_count=1,
                cpu_count_logical=1,
                memory_total_gb=1.0,
                gpu_info="Unknown",
                platform="Unknown",
                architecture="Unknown",
                hostname="Unknown",
                python_version="Unknown"
            )

    def _collect_metrics(self) -> SystemMetrics:
        """Recopilar métricas actuales del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = round(memory.used / (1024**3), 2)

            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = round(disk.used / (1024**3), 2)

            # Red
            net_io = psutil.net_io_counters()
            network_sent_mb = round(net_io.bytes_sent / (1024**2), 2)
            network_recv_mb = round(net_io.bytes_recv / (1024**2), 2)

            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()

            # Load average (solo en Unix)
            load_average = None
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                pass

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                uptime_seconds=uptime_seconds,
                load_average=load_average
            )

        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                uptime_seconds=0.0
            )

    async def _monitoring_loop(self):
        """Loop de monitoreo continuo."""
        while self._running:
            try:
                # Recopilar métricas
                metrics = self._collect_metrics()
                self._metrics_history.append(metrics)

                # Mantener límite de historial
                if len(self._metrics_history) > self._max_history_size:
                    self._metrics_history = self._metrics_history[-self._max_history_size:]

                # Verificar alertas
                await self._check_alerts(metrics)

                # Actualizar estadísticas
                self.stats["total_measurements"] += 1

                # Esperar al próximo intervalo
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self, metrics: SystemMetrics):
        """Verificar condiciones de alerta."""
        alerts = []

        # CPU alta
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent}%")

        # Memoria alta
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent}%")

        # Disco lleno
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append(f"High disk usage: {metrics.disk_percent}%")

        # Trigger alertas
        for alert in alerts:
            await self._trigger_alert("resource_alert", alert)
            self.stats["alerts_triggered"] += 1

    async def _trigger_alert(self, alert_type: str, message: str):
        """Trigger callbacks de alerta."""
        try:
            callbacks = self.alert_callbacks.get(alert_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        await asyncio.get_event_loop().run_in_executor(None, callback, message)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
        except Exception as e:
            logger.error(f"Error triggering alerts: {e}")

    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Obtener información del hardware.

        Returns:
            Información del hardware
        """
        if not self.hardware_info:
            return {}

        return {
            "cpu_count": self.hardware_info.cpu_count,
            "cpu_count_logical": self.hardware_info.cpu_count_logical,
            "memory_total_gb": self.hardware_info.memory_total_gb,
            "gpu_info": self.hardware_info.gpu_info,
            "platform": self.hardware_info.platform,
            "architecture": self.hardware_info.architecture,
            "hostname": self.hardware_info.hostname,
            "python_version": self.hardware_info.python_version
        }

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas actuales.

        Returns:
            Métricas actuales del sistema
        """
        if not self._metrics_history:
            return {}

        latest = self._metrics_history[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_used_gb": latest.memory_used_gb,
            "disk_percent": latest.disk_percent,
            "disk_used_gb": latest.disk_used_gb,
            "network_sent_mb": latest.network_sent_mb,
            "network_recv_mb": latest.network_recv_mb,
            "uptime_seconds": latest.uptime_seconds,
            "load_average": latest.load_average
        }

    async def generate_report(self, period_minutes: int = 60) -> Dict[str, Any]:
        """
        Generar reporte de rendimiento.

        Args:
            period_minutes: Período en minutos para el reporte

        Returns:
            Reporte de rendimiento
        """
        try:
            if not self._metrics_history:
                return {"error": "No metrics available"}

            # Filtrar métricas del período
            cutoff_time = datetime.now().timestamp() - (period_minutes * 60)
            recent_metrics = [
                m for m in self._metrics_history
                if m.timestamp.timestamp() > cutoff_time
            ]

            if not recent_metrics:
                return {"error": "No recent metrics available"}

            # Calcular promedios
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics)

            # Encontrar picos
            peak_cpu = max(m.cpu_percent for m in recent_metrics)
            peak_memory = max(m.memory_percent for m in recent_metrics)
            peak_disk = max(m.disk_percent for m in recent_metrics)

            # Generar recomendaciones
            recommendations = self._generate_recommendations(avg_cpu, avg_memory, avg_disk)

            report = {
                "generated_at": datetime.now().isoformat(),
                "period_minutes": period_minutes,
                "measurements_count": len(recent_metrics),
                "hardware_info": self.get_hardware_info(),
                "current_metrics": self.get_current_metrics(),
                "averages": {
                    "cpu_percent": round(avg_cpu, 1),
                    "memory_percent": round(avg_memory, 1),
                    "disk_percent": round(avg_disk, 1)
                },
                "peaks": {
                    "cpu_percent": peak_cpu,
                    "memory_percent": peak_memory,
                    "disk_percent": peak_disk
                },
                "recommendations": recommendations,
                "alerts_triggered": self.stats["alerts_triggered"]
            }

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, avg_cpu: float, avg_memory: float,
                                avg_disk: float) -> List[str]:
        """Generar recomendaciones basadas en métricas."""
        recommendations = []

        if avg_cpu > 80:
            recommendations.append("High CPU usage detected. Consider optimizing training workload or upgrading CPU.")

        if avg_memory > 80:
            recommendations.append("High memory usage detected. Consider increasing RAM or optimizing memory usage.")

        if avg_disk > 80:
            recommendations.append("High disk usage detected. Consider cleaning up old models or adding more storage.")

        if avg_cpu < 20 and avg_memory < 20:
            recommendations.append("System has spare resources. Consider increasing batch size or concurrent training sessions.")

        return recommendations

    def register_alert_callback(self, alert_type: str, callback: Callable):
        """
        Registrar callback para alertas.

        Args:
            alert_type: Tipo de alerta
            callback: Función callback
        """
        if alert_type not in self.alert_callbacks:
            self.alert_callbacks[alert_type] = []

        self.alert_callbacks[alert_type].append(callback)
        logger.debug(f"Registered alert callback for {alert_type}")

    def set_alert_threshold(self, metric: str, threshold: float):
        """
        Establecer threshold para alertas.

        Args:
            metric: Métrica ('cpu_percent', 'memory_percent', 'disk_percent')
            threshold: Valor del threshold
        """
        if metric in self.alert_thresholds:
            self.alert_thresholds[metric] = threshold
            logger.info(f"Set {metric} alert threshold to {threshold}")

    def get_monitor_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del monitor.

        Returns:
            Estadísticas del monitor
        """
        return {
            "node_id": self.node_id,
            "is_running": self._running,
            "monitoring_interval": self.monitoring_interval,
            "total_measurements": self.stats["total_measurements"],
            "alerts_triggered": self.stats["alerts_triggered"],
            "history_size": len(self._metrics_history),
            "monitoring_started_at": self.stats["monitoring_started_at"].isoformat() if self.stats["monitoring_started_at"] else None,
            "alert_thresholds": self.alert_thresholds.copy()
        }

    # ==================== MÉTODOS SÍNCRONOS PARA COMPATIBILIDAD ====================

    def get_hardware_info_sync(self) -> Dict[str, Any]:
        """Versión síncrona de get_hardware_info."""
        return self.get_hardware_info()

    def get_current_metrics_sync(self) -> Dict[str, Any]:
        """Versión síncrona de get_current_metrics."""
        return self.get_current_metrics()

    def generate_report_sync(self, period_minutes: int = 60) -> Dict[str, Any]:
        """Versión síncrona de generate_report."""
        try:
            # Crear event loop si no existe
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.generate_report(period_minutes))
        except Exception as e:
            logger.error(f"Error in sync report generation: {e}")
            return {"error": str(e)}


# Funciones de conveniencia

def create_hardware_monitor(node_id: str, **kwargs) -> HardwareMonitor:
    """
    Crear monitor de hardware.

    Args:
        node_id: ID del nodo
        **kwargs: Configuraciones adicionales

    Returns:
        Instancia del monitor
    """
    return HardwareMonitor(node_id, **kwargs)


async def initialize_monitor(monitor: HardwareMonitor) -> bool:
    """
    Inicializar monitor de hardware.

    Args:
        monitor: Instancia del monitor

    Returns:
        True si la inicialización fue exitosa
    """
    return await monitor.initialize()


def get_system_info() -> Dict[str, Any]:
    """
    Obtener información básica del sistema.

    Returns:
        Información del sistema
    """
    try:
        monitor = HardwareMonitor("temp")
        return monitor.get_hardware_info()
    except Exception:
        return {"error": "Failed to get system info"}