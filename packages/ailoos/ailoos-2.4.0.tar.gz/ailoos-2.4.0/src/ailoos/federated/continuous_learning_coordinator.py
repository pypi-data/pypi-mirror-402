"""
Continuous Learning Coordinator - Coordinador que gestiona el aprendizaje continuo
Coordina actualizaciones automáticas del modelo con nuevos datos disponibles.
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import heapq
from collections import defaultdict

from ..core.logging import get_logger

logger = get_logger(__name__)


class LearningTrigger(Enum):
    """Tipos de triggers para aprendizaje continuo."""
    TIME_BASED = "time_based"
    DATA_VOLUME = "data_volume"
    PERFORMANCE_DROP = "performance_drop"
    DOMAIN_SHIFT = "domain_shift"
    MANUAL = "manual"


@dataclass
class LearningTask:
    """Tarea de aprendizaje continuo."""
    task_id: str
    trigger_type: LearningTrigger
    priority: int
    data_domains: List[str]
    estimated_data_volume: int
    scheduled_time: float
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContinuousLearningConfig:
    """Configuración para aprendizaje continuo."""
    time_interval_hours: int = 24  # Intervalo de tiempo para triggers temporales
    min_data_volume: int = 1000  # Volumen mínimo de datos para trigger
    performance_drop_threshold: float = 0.05  # Umbral de caída de rendimiento
    max_concurrent_tasks: int = 3  # Máximo de tareas concurrentes
    learning_budget_per_day: float = 10.0  # Presupuesto de aprendizaje diario (horas)
    enable_auto_scheduling: bool = True
    adaptive_triggering: bool = True


@dataclass
class LearningSchedule:
    """Horario de aprendizaje."""
    schedule_id: str
    task_type: str
    cron_expression: str  # Para scheduling avanzado
    next_run: float
    enabled: bool = True
    last_run: Optional[float] = None
    run_count: int = 0


class ContinuousLearningCoordinator:
    """
    Coordinador de aprendizaje continuo para sistemas federados.
    Gestiona triggers automáticos y coordina actualizaciones del modelo.
    """

    def __init__(self, session_id: str, config: ContinuousLearningConfig = None):
        self.session_id = session_id
        self.config = config or ContinuousLearningConfig()

        # Estado del coordinador
        self.is_active = False
        self.coordinator_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Cola de tareas de aprendizaje
        self.learning_queue: List[Tuple[float, LearningTask]] = []  # (priority, task)
        self.active_tasks: Dict[str, LearningTask] = {}
        self.completed_tasks: List[LearningTask] = []

        # Horarios programados
        self.schedules: Dict[str, LearningSchedule] = {}
        self._initialize_default_schedules()

        # Monitores de rendimiento
        self.performance_monitors: Dict[str, Dict[str, Any]] = {}
        self.baseline_performance: Dict[str, float] = {}

        # Callbacks para integración con otros componentes
        self.trigger_callbacks: Dict[LearningTrigger, List[Callable]] = defaultdict(list)
        self.task_completion_callbacks: List[Callable] = []

        # Estadísticas
        self.stats = {
            "total_tasks_scheduled": 0,
            "total_tasks_completed": 0,
            "avg_task_duration": 0.0,
            "triggers_activated": defaultdict(int),
            "learning_efficiency": 0.0,
            "uptime_seconds": 0.0
        }

        # Estado de recursos
        self.resource_usage = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "gpu_usage": 0.0,
            "network_usage": 0.0
        }

        logger.info(f"🔄 ContinuousLearningCoordinator initialized for session {session_id}")

    def _initialize_default_schedules(self):
        """Inicializar horarios por defecto."""
        # Aprendizaje diario
        daily_schedule = LearningSchedule(
            schedule_id="daily_learning",
            task_type="incremental_update",
            cron_expression="0 2 * * *",  # 2 AM daily
            next_run=time.time() + 3600,  # En 1 hora para testing
            enabled=True
        )

        # Aprendizaje semanal intensivo
        weekly_schedule = LearningSchedule(
            schedule_id="weekly_intensive",
            task_type="full_update",
            cron_expression="0 3 * * 0",  # 3 AM Sundays
            next_run=time.time() + 86400,  # En 24 horas
            enabled=True
        )

        self.schedules = {
            "daily_learning": daily_schedule,
            "weekly_intensive": weekly_schedule
        }

    def start_coordinator(self):
        """Iniciar el coordinador de aprendizaje continuo."""
        if self.is_active:
            logger.warning("⚠️ Coordinator already active")
            return

        self.is_active = True
        self.stop_event.clear()
        self.coordinator_thread = threading.Thread(target=self._coordinator_loop, daemon=True)
        self.coordinator_thread.start()

        logger.info("🚀 Continuous learning coordinator started")

    def stop_coordinator(self):
        """Detener el coordinador de aprendizaje continuo."""
        if not self.is_active:
            return

        self.is_active = False
        self.stop_event.set()

        if self.coordinator_thread and self.coordinator_thread.is_alive():
            self.coordinator_thread.join(timeout=5.0)

        logger.info("🛑 Continuous learning coordinator stopped")

    def _coordinator_loop(self):
        """Loop principal del coordinador."""
        logger.info("🔄 Starting coordinator loop")

        start_time = time.time()

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Verificar triggers
                self._check_triggers()

                # Procesar tareas programadas
                self._process_scheduled_tasks()

                # Ejecutar tareas pendientes
                self._execute_pending_tasks()

                # Limpiar tareas completadas
                self._cleanup_completed_tasks()

                # Actualizar estadísticas
                self.stats["uptime_seconds"] = current_time - start_time

                # Dormir antes de siguiente iteración
                self.stop_event.wait(60.0)  # Verificar cada minuto

            except Exception as e:
                logger.error(f"❌ Error in coordinator loop: {e}")
                self.stop_event.wait(30.0)  # Esperar antes de reintentar

        logger.info("🔄 Coordinator loop ended")

    def _check_triggers(self):
        """Verificar todos los triggers activos."""
        current_time = time.time()

        # Trigger temporal
        if self._should_trigger_time_based(current_time):
            self._activate_trigger(LearningTrigger.TIME_BASED, {"timestamp": current_time})

        # Trigger de volumen de datos
        data_volume = self._check_data_volume()
        if data_volume >= self.config.min_data_volume:
            self._activate_trigger(LearningTrigger.DATA_VOLUME, {"data_volume": data_volume})

        # Trigger de caída de rendimiento
        performance_drop = self._check_performance_drop()
        if performance_drop >= self.config.performance_drop_threshold:
            self._activate_trigger(LearningTrigger.PERFORMANCE_DROP,
                                 {"performance_drop": performance_drop})

        # Trigger de cambio de dominio
        domain_shift = self._check_domain_shift()
        if domain_shift:
            self._activate_trigger(LearningTrigger.DOMAIN_SHIFT, domain_shift)

    def _should_trigger_time_based(self, current_time: float) -> bool:
        """Verificar si debe activarse trigger temporal."""
        # Verificar intervalos de tiempo
        time_since_last_trigger = current_time - self.stats.get("last_time_trigger", 0)
        interval_seconds = self.config.time_interval_hours * 3600

        return time_since_last_trigger >= interval_seconds

    def _check_data_volume(self) -> int:
        """Verificar volumen de datos disponibles."""
        # Simulación - en producción consultaría fuentes de datos reales
        return 0  # Por ahora, no hay datos

    def _check_performance_drop(self) -> float:
        """Verificar caída de rendimiento."""
        # Comparar con baseline de rendimiento
        current_performance = self._get_current_performance()

        if not self.baseline_performance:
            self.baseline_performance = current_performance.copy()
            return 0.0

        # Calcular caída promedio
        total_drop = 0.0
        metrics_count = 0

        for metric, current_value in current_performance.items():
            baseline_value = self.baseline_performance.get(metric, current_value)
            if baseline_value > 0:
                drop = (baseline_value - current_value) / baseline_value
                total_drop += max(0, drop)  # Solo caídas positivas
                metrics_count += 1

        return total_drop / metrics_count if metrics_count > 0 else 0.0

    def _get_current_performance(self) -> Dict[str, float]:
        """Obtener métricas de rendimiento actuales."""
        # Simulación - en producción consultaría monitores reales
        return {
            "accuracy": 0.85,
            "f1_score": 0.82,
            "latency": 150.0
        }

    def _check_domain_shift(self) -> Optional[Dict[str, Any]]:
        """Verificar cambios de dominio."""
        # Simulación - en producción integraría con AdaptiveDomainAdapter
        return None

    def _activate_trigger(self, trigger_type: LearningTrigger, metadata: Dict[str, Any]):
        """Activar un trigger específico."""
        logger.info(f"🎯 Trigger activated: {trigger_type.value}")

        self.stats["triggers_activated"][trigger_type.value] += 1
        self.stats[f"last_{trigger_type.value}_trigger"] = time.time()

        # Ejecutar callbacks registrados
        for callback in self.trigger_callbacks[trigger_type]:
            try:
                asyncio.run(callback(trigger_type, metadata))
            except Exception as e:
                logger.error(f"❌ Error in trigger callback: {e}")

        # Crear tarea de aprendizaje basada en el trigger
        task = self._create_learning_task(trigger_type, metadata)
        if task:
            self._schedule_task(task)

    def _create_learning_task(self, trigger_type: LearningTrigger,
                            metadata: Dict[str, Any]) -> Optional[LearningTask]:
        """Crear tarea de aprendizaje basada en trigger."""
        task_id = f"task_{self.session_id}_{int(time.time())}_{trigger_type.value}"

        # Determinar prioridad basada en tipo de trigger
        priority_map = {
            LearningTrigger.MANUAL: 10,
            LearningTrigger.PERFORMANCE_DROP: 8,
            LearningTrigger.DOMAIN_SHIFT: 7,
            LearningTrigger.DATA_VOLUME: 5,
            LearningTrigger.TIME_BASED: 3
        }

        priority = priority_map.get(trigger_type, 5)

        # Estimar volumen de datos
        estimated_volume = metadata.get("data_volume", 1000)

        # Determinar dominios
        data_domains = metadata.get("domains", ["general"])

        task = LearningTask(
            task_id=task_id,
            trigger_type=trigger_type,
            priority=priority,
            data_domains=data_domains,
            estimated_data_volume=estimated_volume,
            scheduled_time=time.time(),  # Ejecutar inmediatamente
            metadata=metadata
        )

        return task

    def _schedule_task(self, task: LearningTask):
        """Programar tarea en la cola."""
        heapq.heappush(self.learning_queue, (-task.priority, task))  # Max-heap
        self.stats["total_tasks_scheduled"] += 1

        logger.info(f"📋 Task {task.task_id} scheduled with priority {task.priority}")

    def _process_scheduled_tasks(self):
        """Procesar tareas programadas."""
        current_time = time.time()

        for schedule in self.schedules.values():
            if not schedule.enabled:
                continue

            if current_time >= schedule.next_run:
                # Crear tarea programada
                task = LearningTask(
                    task_id=f"scheduled_{schedule.schedule_id}_{int(current_time)}",
                    trigger_type=LearningTrigger.TIME_BASED,
                    priority=4,  # Prioridad media para tareas programadas
                    data_domains=["scheduled"],
                    estimated_data_volume=5000,
                    scheduled_time=current_time,
                    metadata={"schedule_id": schedule.schedule_id, "task_type": schedule.task_type}
                )

                self._schedule_task(task)

                # Actualizar horario
                schedule.last_run = current_time
                schedule.run_count += 1
                schedule.next_run = current_time + (24 * 3600)  # Siguiente día

                logger.info(f"⏰ Scheduled task executed: {schedule.schedule_id}")

    def _execute_pending_tasks(self):
        """Ejecutar tareas pendientes respetando límites de concurrencia."""
        # Verificar límite de tareas concurrentes
        if len(self.active_tasks) >= self.config.max_concurrent_tasks:
            return

        # Verificar presupuesto diario
        if not self._check_learning_budget():
            return

        # Obtener siguiente tarea
        if not self.learning_queue:
            return

        priority, task = heapq.heappop(self.learning_queue)

        # Verificar si ya no es válida
        if task.scheduled_time > time.time() + 300:  # 5 minutos de tolerancia
            logger.info(f"⏰ Task {task.task_id} scheduled for future, re-queuing")
            heapq.heappush(self.learning_queue, (priority, task))
            return

        # Iniciar ejecución
        task.status = "running"
        self.active_tasks[task.task_id] = task

        # Ejecutar en thread separado
        execution_thread = threading.Thread(
            target=self._execute_task_async,
            args=(task,),
            daemon=True
        )
        execution_thread.start()

        logger.info(f"▶️ Started execution of task {task.task_id}")

    def _execute_task_async(self, task: LearningTask):
        """Ejecutar tarea de manera asíncrona."""
        try:
            start_time = time.time()

            # Simular ejecución de tarea
            logger.info(f"🔄 Executing learning task {task.task_id}")

            # Aquí iría la lógica real de fine-tuning, adaptación de dominio, etc.
            # Por ahora, simulamos

            # Simular progreso
            for i in range(10):
                if self.stop_event.is_set():
                    break
                task.progress = (i + 1) / 10.0
                time.sleep(0.1)  # Simular trabajo

            task.status = "completed"
            task.progress = 1.0

            execution_time = time.time() - start_time

            logger.info(f"✅ Task {task.task_id} completed in {execution_time:.2f}s")

            # Notificar callbacks
            for callback in self.task_completion_callbacks:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"❌ Error in completion callback: {e}")

        except Exception as e:
            logger.error(f"❌ Error executing task {task.task_id}: {e}")
            task.status = "failed"
            task.metadata["error"] = str(e)

        finally:
            # Mover a completadas
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.completed_tasks.append(task)

    def _check_learning_budget(self) -> bool:
        """Verificar presupuesto de aprendizaje diario."""
        # Calcular uso del día actual
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        today_tasks = [t for t in self.completed_tasks if t.created_at >= today_start]

        total_time_today = sum(
            getattr(t, 'execution_time', 0)
            for t in today_tasks
            if hasattr(t, 'execution_time')
        )

        budget_used = total_time_today / 3600.0  # Convertir a horas
        budget_remaining = self.config.learning_budget_per_day - budget_used

        return budget_remaining > 0.5  # Al menos 30 minutos disponibles

    def _cleanup_completed_tasks(self):
        """Limpiar tareas completadas antiguas."""
        # Mantener solo las últimas 100 tareas completadas
        if len(self.completed_tasks) > 100:
            self.completed_tasks = self.completed_tasks[-100:]

    def register_trigger_callback(self, trigger_type: LearningTrigger, callback: Callable):
        """Registrar callback para un tipo de trigger."""
        self.trigger_callbacks[trigger_type].append(callback)
        logger.info(f"📞 Registered callback for trigger {trigger_type.value}")

    def register_task_completion_callback(self, callback: Callable):
        """Registrar callback para completación de tareas."""
        self.task_completion_callbacks.append(callback)
        logger.info("📞 Registered task completion callback")

    def manual_trigger_learning(self, domains: List[str] = None,
                              priority: int = 8) -> str:
        """Trigger manual de aprendizaje."""
        task_id = f"manual_{self.session_id}_{int(time.time())}"

        metadata = {
            "manual_trigger": True,
            "requested_domains": domains or ["general"],
            "user_priority": priority
        }

        task = LearningTask(
            task_id=task_id,
            trigger_type=LearningTrigger.MANUAL,
            priority=priority,
            data_domains=domains or ["general"],
            estimated_data_volume=2000,
            scheduled_time=time.time(),
            metadata=metadata
        )

        self._schedule_task(task)
        logger.info(f"👤 Manual learning trigger activated: {task_id}")

        return task_id

    def get_coordinator_status(self) -> Dict[str, Any]:
        """Obtener estado del coordinador."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "uptime_seconds": self.stats["uptime_seconds"],
            "queued_tasks": len(self.learning_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "triggers_activated": dict(self.stats["triggers_activated"]),
            "learning_efficiency": self.stats["learning_efficiency"],
            "resource_usage": self.resource_usage.copy(),
            "config": {
                "time_interval_hours": self.config.time_interval_hours,
                "min_data_volume": self.config.min_data_volume,
                "performance_drop_threshold": self.config.performance_drop_threshold,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "learning_budget_per_day": self.config.learning_budget_per_day
            }
        }

    def get_learning_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de tareas de aprendizaje."""
        recent_tasks = self.completed_tasks[-limit:]

        return [
            {
                "task_id": t.task_id,
                "trigger_type": t.trigger_type.value,
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "created_at": t.created_at,
                "data_domains": t.data_domains,
                "estimated_data_volume": t.estimated_data_volume,
                "metadata": t.metadata
            }
            for t in recent_tasks
        ]

    def update_config(self, new_config: Dict[str, Any]):
        """Actualizar configuración del coordinador."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"🔧 Updated config {key} = {value}")

    def pause_learning(self):
        """Pausar aprendizaje continuo."""
        self.is_active = False
        logger.info("⏸️ Learning coordinator paused")

    def resume_learning(self):
        """Reanudar aprendizaje continuo."""
        if not self.is_active:
            self.start_coordinator()
        logger.info("▶️ Learning coordinator resumed")


# Funciones de conveniencia
def create_learning_coordinator(session_id: str,
                              config: ContinuousLearningConfig = None) -> ContinuousLearningCoordinator:
    """Crear un nuevo coordinador de aprendizaje continuo."""
    return ContinuousLearningCoordinator(session_id, config)


async def setup_learning_triggers(coordinator: ContinuousLearningCoordinator,
                                fine_tuner: Any = None,
                                domain_adapter: Any = None):
    """
    Configurar triggers automáticos para componentes de aprendizaje.

    Args:
        coordinator: Coordinador de aprendizaje
        fine_tuner: Fine-tuner federado (opcional)
        domain_adapter: Adaptador de dominio (opcional)
    """
    # Trigger para fine-tuning automático
    if fine_tuner:
        coordinator.register_trigger_callback(
            LearningTrigger.DATA_VOLUME,
            lambda t, m: trigger_fine_tuning(fine_tuner, m)
        )

    # Trigger para adaptación de dominio
    if domain_adapter:
        coordinator.register_trigger_callback(
            LearningTrigger.DOMAIN_SHIFT,
            lambda t, m: trigger_domain_adaptation(domain_adapter, m)
        )

    # Trigger para caída de rendimiento
    coordinator.register_trigger_callback(
        LearningTrigger.PERFORMANCE_DROP,
        lambda t, m: trigger_performance_recovery(m)
    )


async def trigger_fine_tuning(fine_tuner: Any, metadata: Dict[str, Any]):
    """Trigger para fine-tuning automático."""
    logger.info("🎯 Triggering automatic fine-tuning")
    # Implementación específica del fine-tuning


async def trigger_domain_adaptation(domain_adapter: Any, metadata: Dict[str, Any]):
    """Trigger para adaptación de dominio."""
    logger.info("🎯 Triggering domain adaptation")
    # Implementación específica de adaptación de dominio


async def trigger_performance_recovery(metadata: Dict[str, Any]):
    """Trigger para recuperación de rendimiento."""
    logger.info("🎯 Triggering performance recovery")
    # Implementación específica de recuperación de rendimiento