"""
Programador inteligente de consolidación REM Sleep.
Detecta períodos óptimos de inactividad para ejecutar consolidación de memoria.
"""

import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import time
import psutil
import statistics

from ...utils.logging import get_logger


class ActivityLevel(Enum):
    """Niveles de actividad del sistema."""
    IDLE = "idle"           # Sistema inactivo
    LOW = "low"            # Actividad baja
    MODERATE = "moderate"  # Actividad moderada
    HIGH = "high"          # Actividad alta
    PEAK = "peak"          # Actividad máxima


@dataclass
class ActivityMetrics:
    """Métricas de actividad del sistema."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io: float
    network_io: float
    active_processes: int
    activity_level: ActivityLevel


@dataclass
class ConsolidationWindow:
    """Ventana óptima para consolidación."""
    start_time: datetime
    duration: timedelta
    confidence_score: float
    predicted_activity: ActivityLevel
    reason: str


@dataclass
class SchedulingDecision:
    """Decisión de programación."""
    should_consolidate: bool
    optimal_window: Optional[ConsolidationWindow]
    current_activity: ActivityLevel
    next_check: datetime
    reasoning: str


class SleepScheduler:
    """
    Programador inteligente que detecta períodos óptimos para consolidación REM.
    Monitorea actividad del sistema y predice ventanas de baja actividad.
    """

    def __init__(self,
                 monitoring_interval: int = 60,  # segundos
                 history_window: int = 24,  # horas
                 idle_threshold_cpu: float = 20.0,
                 idle_threshold_memory: float = 50.0,
                 min_consolidation_window: int = 30):  # minutos
        self.logger = get_logger(__name__)

        self.monitoring_interval = monitoring_interval
        self.history_window = timedelta(hours=history_window)
        self.idle_threshold_cpu = idle_threshold_cpu
        self.idle_threshold_memory = idle_threshold_memory
        self.min_consolidation_window = timedelta(minutes=min_consolidation_window)

        # Estado del scheduler
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.decision_callbacks: List[Callable[[SchedulingDecision], None]] = []

        # Historial de actividad
        self.activity_history: List[ActivityMetrics] = []
        self.lock = threading.RLock()

        # Estadísticas de predicción
        self.prediction_accuracy = 0.0
        self.total_predictions = 0
        self.correct_predictions = 0

        self.logger.info("SleepScheduler inicializado")

    async def start(self):
        """Iniciar el scheduler de consolidación."""
        if self.running:
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("SleepScheduler iniciado")

    async def stop(self):
        """Detener el scheduler de consolidación."""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("SleepScheduler detenido")

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.running:
            try:
                # Recopilar métricas de actividad
                metrics = await self._collect_activity_metrics()

                # Almacenar en historial
                with self.lock:
                    self.activity_history.append(metrics)
                    self._cleanup_old_history()

                # Analizar patrones y tomar decisiones
                decision = await self._analyze_and_decide()

                # Notificar callbacks
                for callback in self.decision_callbacks:
                    try:
                        callback(decision)
                    except Exception as e:
                        self.logger.warning(f"Error en callback: {e}")

                # Esperar al siguiente intervalo
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error en monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_activity_metrics(self) -> ActivityMetrics:
        """Recopilar métricas actuales de actividad del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disco I/O
            disk_io = 0.0
            try:
                disk_counters = psutil.disk_io_counters()
                if disk_counters:
                    disk_io = disk_counters.read_bytes + disk_counters.write_bytes
            except:
                pass

            # Red I/O
            network_io = 0.0
            try:
                net_counters = psutil.net_io_counters()
                if net_counters:
                    network_io = net_counters.bytes_sent + net_counters.bytes_recv
            except:
                pass

            # Procesos activos (relacionados con ML/inferencia)
            active_processes = 0
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in
                          ['python', 'torch', 'cuda', 'inference', 'training', 'ailoos']):
                        if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 2:
                            active_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Determinar nivel de actividad
            activity_level = self._classify_activity_level(
                cpu_percent, memory_percent, active_processes
            )

            return ActivityMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io=disk_io,
                network_io=network_io,
                active_processes=active_processes,
                activity_level=activity_level
            )

        except Exception as e:
            self.logger.warning(f"Error recopilando métricas: {e}")
            # Retornar métricas por defecto
            return ActivityMetrics(
                timestamp=datetime.now(),
                cpu_percent=50.0,
                memory_percent=50.0,
                disk_io=0.0,
                network_io=0.0,
                active_processes=5,
                activity_level=ActivityLevel.MODERATE
            )

    def _classify_activity_level(self, cpu: float, memory: float, processes: int) -> ActivityLevel:
        """Clasificar nivel de actividad basado en métricas."""
        # Sistema idle: bajo CPU, memoria razonable, pocos procesos ML
        if cpu < self.idle_threshold_cpu and memory < self.idle_threshold_memory and processes <= 1:
            return ActivityLevel.IDLE

        # Actividad baja: CPU moderado, memoria OK
        elif cpu < 40 and memory < 70 and processes <= 3:
            return ActivityLevel.LOW

        # Actividad moderada
        elif cpu < 70 and memory < 85 and processes <= 5:
            return ActivityLevel.MODERATE

        # Actividad alta
        elif cpu < 90 and processes <= 8:
            return ActivityLevel.HIGH

        # Actividad máxima
        else:
            return ActivityLevel.PEAK

    async def _analyze_and_decide(self) -> SchedulingDecision:
        """Analizar historial y decidir si consolidar."""
        with self.lock:
            if len(self.activity_history) < 10:  # Necesitamos datos suficientes
                return SchedulingDecision(
                    should_consolidate=False,
                    optimal_window=None,
                    current_activity=self.activity_history[-1].activity_level if self.activity_history else ActivityLevel.MODERATE,
                    next_check=datetime.now() + timedelta(seconds=self.monitoring_interval),
                    reasoning="Insuficientes datos históricos"
                )

            current_metrics = self.activity_history[-1]
            recent_history = self.activity_history[-60:]  # Última hora

            # Verificar si actualmente es buen momento
            is_currently_good = current_metrics.activity_level in [ActivityLevel.IDLE, ActivityLevel.LOW]

            # Predecir ventana óptima
            optimal_window = self._predict_optimal_window()

            # Decidir basado en condiciones actuales y predicción
            should_consolidate = False
            reasoning = ""

            if is_currently_good:
                should_consolidate = True
                reasoning = f"Sistema actualmente {current_metrics.activity_level.value}, buen momento para consolidar"
            elif optimal_window and optimal_window.confidence_score > 0.7:
                # Verificar si estamos cerca de la ventana óptima
                time_to_window = optimal_window.start_time - datetime.now()
                if time_to_window < timedelta(minutes=15):  # Dentro de 15 minutos
                    should_consolidate = True
                    reasoning = f"Acercándose ventana óptima (confianza: {optimal_window.confidence_score:.2f})"
                else:
                    reasoning = f"Esperando ventana óptima en {time_to_window}"
            else:
                reasoning = f"Actividad actual: {current_metrics.activity_level.value}, esperando mejor momento"

            return SchedulingDecision(
                should_consolidate=should_consolidate,
                optimal_window=optimal_window,
                current_activity=current_metrics.activity_level,
                next_check=datetime.now() + timedelta(seconds=self.monitoring_interval),
                reasoning=reasoning
            )

    def _predict_optimal_window(self) -> Optional[ConsolidationWindow]:
        """Predecir ventana óptima para consolidación basada en patrones históricos."""
        try:
            if len(self.activity_history) < 24:  # Necesitamos al menos 24 puntos
                return None

            # Analizar patrones horarios
            hourly_patterns = self._analyze_hourly_patterns()

            # Encontrar mejores horas
            best_hours = sorted(hourly_patterns.items(), key=lambda x: x[1]['avg_activity'])
            best_hour = best_hours[0][0]

            # Calcular confianza basada en consistencia
            activity_scores = [h['avg_activity'] for h in hourly_patterns.values()]
            consistency = 1.0 - (statistics.stdev(activity_scores) / statistics.mean(activity_scores))

            # Crear ventana
            now = datetime.now()
            next_best_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
            if next_best_time <= now:
                next_best_time += timedelta(days=1)

            # Duración estimada (hasta que actividad aumente)
            duration_hours = 2  # Por defecto 2 horas
            for hour in range(best_hour + 1, 24):
                if hour in hourly_patterns and hourly_patterns[hour]['avg_activity'] > ActivityLevel.LOW.value:
                    break
                duration_hours += 1

            duration = min(timedelta(hours=duration_hours), timedelta(hours=6))  # Máximo 6 horas

            # Verificar que la duración mínima se cumpla
            if duration < self.min_consolidation_window:
                return None

            return ConsolidationWindow(
                start_time=next_best_time,
                duration=duration,
                confidence_score=min(consistency, 0.9),  # Máximo 90% confianza
                predicted_activity=ActivityLevel.IDLE,
                reason=f"Patrón histórico: hora {best_hour} consistentemente baja actividad"
            )

        except Exception as e:
            self.logger.warning(f"Error prediciendo ventana óptima: {e}")
            return None

    def _analyze_hourly_patterns(self) -> Dict[int, Dict[str, float]]:
        """Analizar patrones de actividad por hora del día."""
        hourly_stats = {}

        for metrics in self.activity_history:
            hour = metrics.timestamp.hour
            activity_value = self._activity_level_to_value(metrics.activity_level)

            if hour not in hourly_stats:
                hourly_stats[hour] = {'activities': [], 'avg_activity': 0.0}

            hourly_stats[hour]['activities'].append(activity_value)

        # Calcular promedios
        for hour, stats in hourly_stats.items():
            if stats['activities']:
                stats['avg_activity'] = statistics.mean(stats['activities'])

        return hourly_stats

    def _activity_level_to_value(self, level: ActivityLevel) -> float:
        """Convertir nivel de actividad a valor numérico."""
        mapping = {
            ActivityLevel.IDLE: 0.0,
            ActivityLevel.LOW: 1.0,
            ActivityLevel.MODERATE: 2.0,
            ActivityLevel.HIGH: 3.0,
            ActivityLevel.PEAK: 4.0
        }
        return mapping.get(level, 2.0)

    def _cleanup_old_history(self):
        """Limpiar historial antiguo."""
        cutoff = datetime.now() - self.history_window
        self.activity_history = [
            m for m in self.activity_history
            if m.timestamp > cutoff
        ]

    def add_decision_callback(self, callback: Callable[[SchedulingDecision], None]):
        """Añadir callback para decisiones de scheduling."""
        self.decision_callbacks.append(callback)

    def get_current_activity(self) -> Optional[ActivityLevel]:
        """Obtener nivel de actividad actual."""
        with self.lock:
            return self.activity_history[-1].activity_level if self.activity_history else None

    def get_activity_history(self, hours: int = 24) -> List[ActivityMetrics]:
        """Obtener historial de actividad."""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self.lock:
            return [m for m in self.activity_history if m.timestamp > cutoff]

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del scheduler."""
        with self.lock:
            if not self.activity_history:
                return {}

            recent = self.activity_history[-100:]  # Últimos 100 puntos

            return {
                'total_measurements': len(self.activity_history),
                'current_activity': self.get_current_activity(),
                'avg_cpu_percent': statistics.mean(m.cpu_percent for m in recent),
                'avg_memory_percent': statistics.mean(m.memory_percent for m in recent),
                'prediction_accuracy': self.prediction_accuracy,
                'total_predictions': self.total_predictions,
                'monitoring_interval': self.monitoring_interval,
                'history_window_hours': self.history_window.total_seconds() / 3600
            }

    def force_consolidation_check(self) -> SchedulingDecision:
        """Forzar verificación inmediata de consolidación."""
        # Ejecutar análisis sincrónicamente
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si loop ya está corriendo, ejecutar en thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._analyze_and_decide())
                    return future.result()
            else:
                return loop.run_until_complete(self._analyze_and_decide())
        except Exception as e:
            self.logger.error(f"Error forzando verificación: {e}")
            return SchedulingDecision(
                should_consolidate=False,
                optimal_window=None,
                current_activity=ActivityLevel.MODERATE,
                next_check=datetime.now() + timedelta(seconds=self.monitoring_interval),
                reasoning=f"Error: {e}"
            )


# Instancia global
_sleep_scheduler: Optional[SleepScheduler] = None


def get_sleep_scheduler() -> SleepScheduler:
    """Obtener instancia global del sleep scheduler."""
    global _sleep_scheduler
    if _sleep_scheduler is None:
        _sleep_scheduler = SleepScheduler()
    return _sleep_scheduler