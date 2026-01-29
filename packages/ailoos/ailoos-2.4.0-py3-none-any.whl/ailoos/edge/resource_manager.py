"""
Gestión inteligente de recursos limitados en dispositivos edge.

Monitorea y optimiza el uso de CPU, memoria, batería y otros recursos
para garantizar rendimiento eficiente en entornos edge.
"""

import torch
import logging
import time
import threading
import psutil
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import os
import gc

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Tipos de recursos gestionados."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    BATTERY = "battery"
    NETWORK = "network"
    STORAGE = "storage"


class TaskPriority(Enum):
    """Prioridades de tareas."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class ResourceState(Enum):
    """Estados de recursos."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


@dataclass
class ResourceLimits:
    """Límites de recursos."""
    cpu_percent: float = 80.0
    memory_percent: float = 85.0
    gpu_memory_percent: Optional[float] = 90.0
    battery_percent: float = 20.0  # Nivel mínimo de batería
    network_bandwidth_mbps: Optional[float] = None


@dataclass
class ResourceUsage:
    """Uso actual de recursos."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    gpu_memory_percent: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    battery_percent: Optional[float] = None
    network_bandwidth_mbps: Optional[float] = None
    storage_free_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ManagedTask:
    """Tarea gestionada por el ResourceManager."""
    task_id: str
    name: str
    priority: TaskPriority
    resource_requirements: Dict[ResourceType, float]
    current_resources: Dict[ResourceType, float] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceManagerConfig:
    """Configuración del ResourceManager."""
    # Monitoreo
    monitoring_interval_seconds: int = 5
    enable_resource_monitoring: bool = True

    # Límites de recursos
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)

    # Gestión de tareas
    max_concurrent_tasks: int = 3
    enable_task_prioritization: bool = True
    enable_resource_preemption: bool = True

    # Políticas de throttling
    enable_cpu_throttling: bool = True
    enable_memory_cleanup: bool = True
    enable_battery_optimization: bool = True

    # Liberación automática
    resource_cleanup_interval_seconds: int = 30
    task_timeout_seconds: int = 300  # 5 minutos

    # Optimizaciones
    enable_memory_pooling: bool = True
    enable_gpu_memory_optimization: bool = True
    adaptive_resource_allocation: bool = True


class ResourceMonitor:
    """Monitor de recursos del sistema."""

    def __init__(self, config: ResourceManagerConfig):
        self.config = config
        self.last_usage = ResourceUsage()

    def get_current_usage(self) -> ResourceUsage:
        """Obtener uso actual de recursos."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # GPU (simplificado - en implementación real usar libraries específicas)
            gpu_memory_percent = None
            gpu_memory_used_mb = None
            if torch.cuda.is_available():
                try:
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory
                    gpu_memory_used = torch.cuda.memory_allocated(0)
                    gpu_memory_percent = (gpu_memory_used / gpu_memory) * 100
                    gpu_memory_used_mb = gpu_memory_used / (1024 * 1024)
                except:
                    pass

            # Batería
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else None

            # Almacenamiento
            storage = psutil.disk_usage('/')
            storage_free_mb = storage.free / (1024 * 1024)

            # Red (simplificado)
            network_bandwidth_mbps = None  # Requiere monitoreo más complejo

            usage = ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                gpu_memory_percent=gpu_memory_percent,
                gpu_memory_used_mb=gpu_memory_used_mb,
                battery_percent=battery_percent,
                network_bandwidth_mbps=network_bandwidth_mbps,
                storage_free_mb=storage_free_mb
            )

            self.last_usage = usage
            return usage

        except Exception as e:
            logger.error(f"❌ Error obteniendo uso de recursos: {e}")
            return self.last_usage

    def get_resource_state(self, usage: ResourceUsage) -> Dict[ResourceType, ResourceState]:
        """Obtener estado de cada recurso."""
        states = {}

        # CPU
        if usage.cpu_percent >= self.config.resource_limits.cpu_percent:
            states[ResourceType.CPU] = ResourceState.CRITICAL
        elif usage.cpu_percent >= self.config.resource_limits.cpu_percent * 0.8:
            states[ResourceType.CPU] = ResourceState.WARNING
        else:
            states[ResourceType.CPU] = ResourceState.HEALTHY

        # Memoria
        if usage.memory_percent >= self.config.resource_limits.memory_percent:
            states[ResourceType.MEMORY] = ResourceState.CRITICAL
        elif usage.memory_percent >= self.config.resource_limits.memory_percent * 0.8:
            states[ResourceType.MEMORY] = ResourceState.WARNING
        else:
            states[ResourceType.MEMORY] = ResourceState.HEALTHY

        # GPU
        if usage.gpu_memory_percent is not None:
            if usage.gpu_memory_percent >= (self.config.resource_limits.gpu_memory_percent or 90):
                states[ResourceType.GPU] = ResourceState.CRITICAL
            elif usage.gpu_memory_percent >= (self.config.resource_limits.gpu_memory_percent or 90) * 0.8:
                states[ResourceType.GPU] = ResourceState.WARNING
            else:
                states[ResourceType.GPU] = ResourceState.HEALTHY

        # Batería
        if usage.battery_percent is not None:
            if usage.battery_percent <= self.config.resource_limits.battery_percent:
                states[ResourceType.BATTERY] = ResourceState.CRITICAL
            elif usage.battery_percent <= self.config.resource_limits.battery_percent * 1.5:
                states[ResourceType.BATTERY] = ResourceState.WARNING
            else:
                states[ResourceType.BATTERY] = ResourceState.HEALTHY

        return states


class ResourceManager:
    """
    Gestor inteligente de recursos para dispositivos edge.

    Características principales:
    - Monitoreo continuo de recursos del sistema
    - Gestión de prioridades de tareas
    - Políticas de throttling automático
    - Optimización de memoria y CPU
    - Liberación automática de recursos
    - Adaptación dinámica a condiciones del dispositivo
    """

    def __init__(self, config: ResourceManagerConfig):
        self.config = config

        # Monitor de recursos
        self.monitor = ResourceMonitor(config)

        # Gestión de tareas
        self.managed_tasks: Dict[str, ManagedTask] = {}
        self.active_tasks: Dict[str, threading.Thread] = {}
        self.task_lock = threading.Lock()

        # Estado de recursos
        self.current_usage = ResourceUsage()
        self.resource_states: Dict[ResourceType, ResourceState] = {}

        # Hilos de gestión
        self.monitor_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

        # Estadísticas
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "resource_throttles": 0,
            "memory_cleanups": 0,
            "preemptions": 0,
            "avg_resource_usage": {},
            "peak_resource_usage": {}
        }

        # Callbacks
        self.resource_callbacks: List[Callable] = []
        self.task_callbacks: List[Callable] = []

        logger.info("🔧 ResourceManager inicializado")
        logger.info(f"   Monitoreo: {config.enable_resource_monitoring}")
        logger.info(f"   Tareas concurrentes máx: {config.max_concurrent_tasks}")

    def start(self):
        """Iniciar gestión de recursos."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("⚠️ ResourceManager ya está ejecutándose")
            return

        # Iniciar hilos
        if self.config.enable_resource_monitoring:
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        logger.info("🚀 ResourceManager iniciado")

    def stop(self):
        """Detener gestión de recursos."""
        # Esperar a que terminen los hilos
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5.0)

        # Limpiar tareas activas
        with self.task_lock:
            for task_id, thread in self.active_tasks.items():
                try:
                    thread.join(timeout=2.0)
                except:
                    pass

        logger.info("🛑 ResourceManager detenido")

    def register_task(
        self,
        task_id: str,
        name: str,
        priority: TaskPriority,
        resource_requirements: Dict[ResourceType, float],
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registrar una tarea para gestión de recursos.

        Args:
            task_id: ID único de la tarea
            name: Nombre descriptivo
            priority: Prioridad de la tarea
            resource_requirements: Requisitos de recursos (ej: {ResourceType.CPU: 20.0})
            callback: Callback opcional
            metadata: Metadatos adicionales

        Returns:
            True si se registró exitosamente
        """
        if task_id in self.managed_tasks:
            logger.warning(f"⚠️ Tarea {task_id} ya está registrada")
            return False

        task = ManagedTask(
            task_id=task_id,
            name=name,
            priority=priority,
            resource_requirements=resource_requirements,
            callback=callback,
            metadata=metadata or {}
        )

        self.managed_tasks[task_id] = task
        logger.info(f"✅ Tarea registrada: {task_id} ({priority.value})")
        return True

    def start_task(self, task_id: str, task_function: Callable, *args, **kwargs) -> bool:
        """
        Iniciar una tarea gestionada.

        Args:
            task_id: ID de la tarea registrada
            task_function: Función a ejecutar
            *args, **kwargs: Argumentos para la función

        Returns:
            True si se inició exitosamente
        """
        if task_id not in self.managed_tasks:
            logger.error(f"❌ Tarea {task_id} no está registrada")
            return False

        task = self.managed_tasks[task_id]

        # Verificar recursos disponibles
        if not self._can_start_task(task):
            logger.warning(f"⚠️ Recursos insuficientes para iniciar tarea {task_id}")
            return False

        # Crear y iniciar hilo
        def task_wrapper():
            try:
                task.status = "running"
                task.last_active = time.time()

                # Ejecutar función
                result = task_function(*args, **kwargs)

                # Notificar callback
                if task.callback:
                    try:
                        task.callback(task_id, "completed", result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error en callback: {e}")

                task.status = "completed"
                self.stats["tasks_completed"] += 1

            except Exception as e:
                logger.error(f"❌ Error en tarea {task_id}: {e}")
                task.status = "failed"

                if task.callback:
                    try:
                        task.callback(task_id, "failed", str(e))
                    except Exception as callback_error:
                        logger.warning(f"⚠️ Error en callback de error: {callback_error}")

                self.stats["tasks_failed"] += 1

            finally:
                # Limpiar recursos
                with self.task_lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]

        thread = threading.Thread(target=task_wrapper, daemon=True)

        with self.task_lock:
            self.active_tasks[task_id] = thread
            thread.start()

        logger.info(f"▶️ Tarea iniciada: {task_id}")
        return True

    def stop_task(self, task_id: str) -> bool:
        """Detener una tarea."""
        with self.task_lock:
            if task_id not in self.active_tasks:
                return False

            thread = self.active_tasks[task_id]
            # Nota: En Python no hay forma directa de detener un hilo,
            # esto debería manejarse en la función de la tarea
            logger.info(f"⏹️ Solicitud de detención para tarea: {task_id}")
            return True

    def get_resource_status(self) -> Dict[str, Any]:
        """Obtener estado actual de recursos."""
        return {
            "current_usage": self.current_usage.__dict__,
            "resource_states": {k.value: v.value for k, v in self.resource_states.items()},
            "active_tasks": len(self.active_tasks),
            "managed_tasks": len(self.managed_tasks),
            "stats": self.stats.copy()
        }

    def request_resources(self, task_id: str, resources: Dict[ResourceType, float]) -> bool:
        """
        Solicitar asignación de recursos adicionales.

        Args:
            task_id: ID de la tarea
            resources: Recursos solicitados

        Returns:
            True si se asignaron exitosamente
        """
        if task_id not in self.managed_tasks:
            return False

        task = self.managed_tasks[task_id]

        # Verificar disponibilidad
        if self._check_resource_availability(resources):
            task.current_resources.update(resources)
            logger.info(f"📈 Recursos asignados a {task_id}: {resources}")
            return True
        else:
            logger.warning(f"⚠️ Recursos no disponibles para {task_id}")
            return False

    def release_resources(self, task_id: str, resources: Optional[Dict[ResourceType, float]] = None):
        """Liberar recursos de una tarea."""
        if task_id not in self.managed_tasks:
            return

        task = self.managed_tasks[task_id]

        if resources:
            for resource_type, amount in resources.items():
                if resource_type in task.current_resources:
                    task.current_resources[resource_type] = max(0, task.current_resources[resource_type] - amount)
        else:
            # Liberar todos los recursos
            task.current_resources.clear()

        logger.info(f"📉 Recursos liberados de {task_id}")

    def add_resource_callback(self, callback: Callable):
        """Agregar callback para eventos de recursos."""
        self.resource_callbacks.append(callback)

    def add_task_callback(self, callback: Callable):
        """Agregar callback para eventos de tareas."""
        self.task_callbacks.append(callback)

    def _can_start_task(self, task: ManagedTask) -> bool:
        """Verificar si una tarea puede iniciarse."""
        # Verificar límite de tareas concurrentes
        if len(self.active_tasks) >= self.config.max_concurrent_tasks:
            return False

        # Verificar recursos disponibles
        return self._check_resource_availability(task.resource_requirements)

    def _check_resource_availability(self, requirements: Dict[ResourceType, float]) -> bool:
        """Verificar disponibilidad de recursos."""
        for resource_type, required_amount in requirements.items():
            if resource_type == ResourceType.CPU:
                available = 100.0 - self.current_usage.cpu_percent
                if available < required_amount:
                    return False

            elif resource_type == ResourceType.MEMORY:
                available = 100.0 - self.current_usage.memory_percent
                if available < required_amount:
                    return False

            elif resource_type == ResourceType.GPU and self.current_usage.gpu_memory_percent is not None:
                available = 100.0 - self.current_usage.gpu_memory_percent
                if available < required_amount:
                    return False

        return True

    def _monitor_loop(self):
        """Bucle de monitoreo de recursos."""
        while True:
            try:
                time.sleep(self.config.monitoring_interval_seconds)

                # Obtener uso actual
                self.current_usage = self.monitor.get_current_usage()
                self.resource_states = self.monitor.get_resource_state(self.current_usage)

                # Verificar estados críticos
                critical_resources = [
                    res for res, state in self.resource_states.items()
                    if state == ResourceState.CRITICAL
                ]

                if critical_resources:
                    self._handle_critical_resources(critical_resources)

                # Actualizar estadísticas
                self._update_resource_stats()

                # Notificar callbacks
                for callback in self.resource_callbacks:
                    try:
                        callback(self.current_usage, self.resource_states)
                    except Exception as e:
                        logger.warning(f"⚠️ Error en callback de recursos: {e}")

            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")

    def _cleanup_loop(self):
        """Bucle de limpieza de recursos."""
        while True:
            try:
                time.sleep(self.config.resource_cleanup_interval_seconds)

                # Limpiar tareas timeout
                current_time = time.time()
                timeout_tasks = []

                for task_id, task in self.managed_tasks.items():
                    if (task.status == "running" and
                        current_time - task.last_active > self.config.task_timeout_seconds):
                        timeout_tasks.append(task_id)

                for task_id in timeout_tasks:
                    logger.warning(f"⏰ Tarea timeout: {task_id}")
                    self.stop_task(task_id)

                # Limpieza de memoria si está habilitado
                if self.config.enable_memory_cleanup:
                    self._perform_memory_cleanup()

                # Liberar tareas completadas/fallidas
                completed_tasks = [
                    task_id for task_id, task in self.managed_tasks.items()
                    if task.status in ["completed", "failed"]
                ]

                for task_id in completed_tasks:
                    self.release_resources(task_id)
                    logger.info(f"🧹 Recursos limpiados para tarea: {task_id}")

            except Exception as e:
                logger.error(f"❌ Error en limpieza: {e}")

    def _handle_critical_resources(self, critical_resources: List[ResourceType]):
        """Manejar recursos en estado crítico."""
        logger.warning(f"🚨 Recursos críticos: {[r.value for r in critical_resources]}")

        # Throttling de CPU si está habilitado
        if (ResourceType.CPU in critical_resources and
            self.config.enable_cpu_throttling and
            len(self.active_tasks) > 1):

            # Reducir prioridad de tareas menos críticas
            self._throttle_background_tasks()
            self.stats["resource_throttles"] += 1

        # Liberar memoria si es crítica
        if ResourceType.MEMORY in critical_resources and self.config.enable_memory_cleanup:
            self._perform_memory_cleanup()
            self.stats["memory_cleanups"] += 1

        # Preemption si está habilitado
        if self.config.enable_resource_preemption:
            self._perform_resource_preemption(critical_resources)

    def _throttle_background_tasks(self):
        """Reducir prioridad de tareas en background."""
        background_tasks = [
            task_id for task_id, task in self.managed_tasks.items()
            if task.priority == TaskPriority.BACKGROUND and task.status == "running"
        ]

        for task_id in background_tasks[:2]:  # Throttle máximo 2 tareas
            logger.info(f"🐌 Throttling tarea: {task_id}")
            # En implementación real, ajustar prioridad del hilo o CPU

    def _perform_memory_cleanup(self):
        """Realizar limpieza de memoria."""
        try:
            # Forzar garbage collection
            collected = gc.collect()
            logger.info(f"🗑️ GC recolectó {collected} objetos")

            # Limpiar cache de PyTorch si está disponible
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            logger.warning(f"⚠️ Error en limpieza de memoria: {e}")

    def _perform_resource_preemption(self, critical_resources: List[ResourceType]):
        """Realizar preemption de recursos."""
        # Identificar tareas con menor prioridad que pueden ser preemptadas
        preemptable_tasks = [
            (task_id, task) for task_id, task in self.managed_tasks.items()
            if task.status == "running" and task.priority in [TaskPriority.LOW, TaskPriority.BACKGROUND]
        ]

        if preemptable_tasks:
            # Preemptar la tarea con menor prioridad
            task_id, task = min(preemptable_tasks, key=lambda x: x[1].priority.value)
            logger.warning(f"⚡ Preemptando tarea: {task_id}")
            self.stop_task(task_id)
            self.stats["preemptions"] += 1

    def _update_resource_stats(self):
        """Actualizar estadísticas de recursos."""
        # Actualizar promedios
        for key, value in self.current_usage.__dict__.items():
            if isinstance(value, (int, float)) and value > 0:
                if key not in self.stats["avg_resource_usage"]:
                    self.stats["avg_resource_usage"][key] = value
                else:
                    # Promedio móvil
                    self.stats["avg_resource_usage"][key] = (
                        self.stats["avg_resource_usage"][key] * 0.9 + value * 0.1
                    )

                # Actualizar picos
                if key not in self.stats["peak_resource_usage"]:
                    self.stats["peak_resource_usage"][key] = value
                else:
                    self.stats["peak_resource_usage"][key] = max(
                        self.stats["peak_resource_usage"][key], value
                    )


# Funciones de conveniencia
def create_resource_manager_for_mobile() -> ResourceManager:
    """
    Crear ResourceManager optimizado para dispositivos móviles.

    Returns:
        ResourceManager configurado
    """
    config = ResourceManagerConfig(
        monitoring_interval_seconds=3,  # Monitoreo más frecuente
        resource_limits=ResourceLimits(
            cpu_percent=70.0,  # Más conservador para móviles
            memory_percent=80.0,
            battery_percent=15.0  # Nivel crítico más bajo
        ),
        max_concurrent_tasks=2,
        enable_battery_optimization=True,
        enable_cpu_throttling=True
    )

    return ResourceManager(config)


def create_resource_manager_for_iot() -> ResourceManager:
    """
    Crear ResourceManager optimizado para dispositivos IoT.

    Returns:
        ResourceManager configurado
    """
    config = ResourceManagerConfig(
        monitoring_interval_seconds=10,  # Monitoreo menos frecuente
        resource_limits=ResourceLimits(
            cpu_percent=60.0,  # Muy conservador para IoT
            memory_percent=70.0,
            battery_percent=10.0
        ),
        max_concurrent_tasks=1,  # Solo una tarea concurrente
        enable_battery_optimization=True,
        enable_memory_cleanup=True,
        task_timeout_seconds=180  # Timeout más corto
    )

    return ResourceManager(config)


if __name__ == "__main__":
    # Demo del ResourceManager
    print("🚀 ResourceManager Demo")

    # Crear manager para móvil
    manager = create_resource_manager_for_mobile()
    manager.start()

    print("ResourceManager iniciado")
    print(f"Tareas concurrentes máx: {manager.config.max_concurrent_tasks}")
    print(f"Límite CPU: {manager.config.resource_limits.cpu_percent}%")

    # Registrar tarea de ejemplo
    def example_task():
        print("Ejecutando tarea de ejemplo...")
        time.sleep(2)
        return "Completada"

    success = manager.register_task(
        task_id="example_task",
        name="Tarea de ejemplo",
        priority=TaskPriority.NORMAL,
        resource_requirements={ResourceType.CPU: 10.0, ResourceType.MEMORY: 50.0}
    )

    if success:
        print("Tarea registrada exitosamente")

        # Iniciar tarea
        started = manager.start_task("example_task", example_task)
        if started:
            print("Tarea iniciada")

            # Esperar un poco
            time.sleep(3)

            # Obtener estado
            status = manager.get_resource_status()
            print(f"Tareas activas: {status['active_tasks']}")
            print(f"Uso de CPU: {status['current_usage']['cpu_percent']:.1f}%")
            print(f"Uso de memoria: {status['current_usage']['memory_percent']:.1f}%")

    manager.stop()
    print("ResourceManager detenido")