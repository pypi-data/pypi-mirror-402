"""
Programador consciente de recursos para entornos federated learning.
Adapta asignación de tareas a capacidades heterogéneas de hardware.
"""

import asyncio
import torch
import logging
import time
import psutil
import cpuinfo
import GPUtil
from typing import Dict, List, Any, Optional, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class HardwareType(Enum):
    """Tipos de hardware soportados."""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    MPS = "mps"  # Apple Silicon


class TaskPriority(Enum):
    """Prioridades de tareas."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class HardwareCapabilities:
    """Capacidades de hardware de un nodo."""

    node_id: str
    hardware_type: HardwareType
    device_name: str

    # CPU
    cpu_cores: int = 0
    cpu_frequency_mhz: float = 0.0

    # Memoria
    total_memory_gb: float = 0.0
    available_memory_gb: float = 0.0

    # GPU (si aplica)
    gpu_memory_gb: float = 0.0
    gpu_compute_capability: Optional[Tuple[int, int]] = None
    cuda_cores: int = 0

    # Rendimiento relativo
    performance_score: float = 1.0  # Score relativo (1.0 = baseline)

    # Estado dinámico
    current_load: float = 0.0  # 0.0 - 1.0
    temperature_celsius: float = 0.0
    power_consumption_w: float = 0.0

    # Capacidades específicas
    supports_fp16: bool = False
    supports_int8: bool = False
    supports_bfloat16: bool = False
    max_batch_size: int = 1

    # Latencia de red (para coordinación FL)
    network_latency_ms: float = 0.0
    bandwidth_mbps: float = 0.0

    last_updated: float = field(default_factory=time.time)


@dataclass
class ScheduledTask:
    """Tarea programada para ejecución."""

    task_id: str
    task_type: str  # "inference", "training", "aggregation", etc.
    priority: TaskPriority
    estimated_duration: float  # Segundos estimados
    resource_requirements: Dict[str, Any]

    # Asignación
    assigned_node: Optional[str] = None
    assigned_device: Optional[str] = None
    scheduled_time: Optional[float] = None

    # Estado
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    # Callbacks
    on_complete: Optional[Callable[[], Awaitable[None]]] = None
    on_failure: Optional[Callable[[Exception], Awaitable[None]]] = None

    # Metadatos FL
    round_id: str = ""
    federated_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """Configuración del programador."""

    # Monitoreo
    monitoring_interval_seconds: float = 5.0
    hardware_detection_interval_seconds: float = 60.0

    # Políticas de asignación
    load_balancing_strategy: str = "adaptive"  # adaptive, round_robin, performance_based
    priority_queuing: bool = True
    preemption_enabled: bool = False

    # Límites
    max_concurrent_tasks_per_node: int = 4
    max_queue_size: int = 1000
    task_timeout_seconds: float = 300.0

    # Optimizaciones FL
    federated_aware_scheduling: bool = True
    cross_round_optimization: bool = True
    resource_reservation_ratio: float = 0.1  # 10% reservado para coordinación FL

    # Adaptación
    adaptive_scaling: bool = True
    performance_history_window: int = 100
    load_threshold_high: float = 0.8
    load_threshold_low: float = 0.3


class ResourceAwareScheduler:
    """
    Programador consciente de recursos para federated learning.

    Características principales:
    - Detección automática de capacidades de hardware
    - Asignación inteligente de tareas basada en rendimiento
    - Balanceo de carga adaptativo
    - Optimizaciones específicas para FL
    - Monitoreo en tiempo real de recursos
    - Escalado dinámico basado en carga
    """

    def __init__(self, config: SchedulerConfig, local_node_id: str = "local"):
        self.config = config
        self.local_node_id = local_node_id

        # Estado de nodos
        self.node_capabilities: Dict[str, HardwareCapabilities] = {}
        self.active_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=config.max_queue_size)

        # Historial de rendimiento
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.performance_history_window))
        self.task_execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # Estadísticas
        self.stats = {
            "total_tasks_scheduled": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "average_queue_time": 0.0,
            "average_execution_time": 0.0,
            "resource_utilization": 0.0,
            "load_balancing_efficiency": 0.0
        }

        # Componentes de ejecución
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_tasks_per_node)
        self.monitoring_task: Optional[asyncio.Task] = None
        self.scheduling_task: Optional[asyncio.Task] = None
        self.running = False

        # Políticas de asignación
        self.assignment_strategies = {
            "adaptive": self._adaptive_assignment,
            "round_robin": self._round_robin_assignment,
            "performance_based": self._performance_based_assignment
        }

        logger.info("🔧 ResourceAwareScheduler inicializado")
        logger.info(f"   Estrategia de balanceo: {config.load_balancing_strategy}")
        logger.info(f"   Nodo local: {local_node_id}")

    async def start(self):
        """Iniciar el programador."""
        self.running = True

        # Detectar capacidades del nodo local
        await self._detect_local_capabilities()

        # Iniciar tareas de monitoreo y programación
        self.monitoring_task = asyncio.create_task(self._monitoring_worker())
        self.scheduling_task = asyncio.create_task(self._scheduling_worker())

        logger.info("▶️ ResourceAwareScheduler iniciado")

    async def stop(self):
        """Detener el programador."""
        self.running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.scheduling_task:
            self.scheduling_task.cancel()

        # Esperar a que terminen las tareas activas
        await self._wait_for_active_tasks()

        self.executor.shutdown(wait=True)
        logger.info("⏹️ ResourceAwareScheduler detenido")

    async def schedule_task(
        self,
        task: ScheduledTask,
        callback: Optional[Callable[[ScheduledTask], Awaitable[None]]] = None
    ) -> bool:
        """
        Programar una tarea para ejecución.

        Args:
            task: Tarea a programar
            callback: Callback opcional cuando se complete

        Returns:
            True si se programó exitosamente
        """
        try:
            # Asignar callback si se proporciona
            if callback:
                original_callback = task.on_complete
                async def combined_callback():
                    if original_callback:
                        await original_callback()
                    await callback(task)
                task.on_complete = combined_callback

            # Agregar timestamp de cola
            task.scheduled_time = time.time()

            # Encolar con prioridad
            priority_value = task.priority.value
            await self.task_queue.put((priority_value, task))

            self.stats["total_tasks_scheduled"] += 1
            logger.debug(f"📋 Tarea programada: {task.task_id} (prioridad: {task.priority.name})")

            return True

        except asyncio.QueueFull:
            logger.warning(f"⚠️ Cola llena, rechazando tarea: {task.task_id}")
            return False

    async def _scheduling_worker(self):
        """Worker principal de programación."""
        while self.running:
            try:
                # Obtener tarea de la cola
                priority, task = await self.task_queue.get()

                # Asignar tarea a un nodo
                assigned_node = await self._assign_task_to_node(task)

                if assigned_node:
                    # Iniciar ejecución
                    asyncio.create_task(self._execute_task(task, assigned_node))
                else:
                    # Reencolar si no se puede asignar
                    logger.warning(f"⚠️ No se pudo asignar tarea {task.task_id}, reencolando")
                    await asyncio.sleep(1)  # Pequeño delay antes de reencolar
                    await self.task_queue.put((priority, task))

            except Exception as e:
                logger.error(f"❌ Error en scheduling worker: {e}")
                await asyncio.sleep(1)

    async def _assign_task_to_node(self, task: ScheduledTask) -> Optional[str]:
        """Asignar tarea al mejor nodo disponible."""
        if not self.node_capabilities:
            return None

        # Usar estrategia de asignación configurada
        strategy = self.assignment_strategies.get(
            self.config.load_balancing_strategy,
            self._adaptive_assignment
        )

        return await strategy(task)

    async def _adaptive_assignment(self, task: ScheduledTask) -> Optional[str]:
        """Asignación adaptativa basada en carga y capacidades."""
        best_node = None
        best_score = -1.0

        for node_id, capabilities in self.node_capabilities.items():
            # Verificar si el nodo puede manejar la tarea
            if not self._can_node_handle_task(capabilities, task):
                continue

            # Calcular score de asignación
            score = self._calculate_assignment_score(capabilities, task)

            # Aplicar factor de carga actual
            load_factor = 1.0 - capabilities.current_load
            score *= load_factor

            # Bonus por afinidad FL (misma ronda)
            if task.round_id and task.round_id in capabilities.device_name:
                score *= 1.2

            if score > best_score:
                best_score = score
                best_node = node_id

        return best_node

    async def _round_robin_assignment(self, task: ScheduledTask) -> Optional[str]:
        """Asignación round-robin simple."""
        available_nodes = [
            node_id for node_id, cap in self.node_capabilities.items()
            if self._can_node_handle_task(cap, task)
        ]

        if not available_nodes:
            return None

        # Usar hash de task_id para distribución
        node_index = hash(task.task_id) % len(available_nodes)
        return available_nodes[node_index]

    async def _performance_based_assignment(self, task: ScheduledTask) -> Optional[str]:
        """Asignación basada en historial de rendimiento."""
        best_node = None
        best_performance = 0.0

        for node_id, capabilities in self.node_capabilities.items():
            if not self._can_node_handle_task(capabilities, task):
                continue

            # Calcular rendimiento promedio para este tipo de tarea
            task_key = f"{task.task_type}_{node_id}"
            if task_key in self.task_execution_times:
                avg_time = np.mean(self.task_execution_times[task_key])
                performance = 1.0 / avg_time if avg_time > 0 else 0.0
            else:
                performance = capabilities.performance_score

            if performance > best_performance:
                best_performance = performance
                best_node = node_id

        return best_node

    def _can_node_handle_task(self, capabilities: HardwareCapabilities, task: ScheduledTask) -> bool:
        """Verificar si un nodo puede manejar una tarea."""
        # Verificar límites de concurrencia
        active_tasks_on_node = sum(1 for t in self.active_tasks.values() if t.assigned_node == capabilities.node_id)
        if active_tasks_on_node >= self.config.max_concurrent_tasks_per_node:
            return False

        # Verificar requisitos de recursos
        required_memory = task.resource_requirements.get("memory_gb", 0)
        if required_memory > capabilities.available_memory_gb:
            return False

        # Verificar tipo de hardware
        required_hardware = task.resource_requirements.get("hardware_type")
        if required_hardware and capabilities.hardware_type.value != required_hardware:
            return False

        # Verificar capacidades específicas
        if task.task_type == "inference":
            required_precision = task.resource_requirements.get("precision", "fp32")
            if required_precision == "fp16" and not capabilities.supports_fp16:
                return False
            elif required_precision == "int8" and not capabilities.supports_int8:
                return False

        return True

    def _calculate_assignment_score(self, capabilities: HardwareCapabilities, task: ScheduledTask) -> float:
        """Calcular score de asignación para un nodo y tarea."""
        score = capabilities.performance_score

        # Factor de memoria disponible
        memory_ratio = capabilities.available_memory_gb / capabilities.total_memory_gb
        score *= (0.5 + 0.5 * memory_ratio)  # 0.5 - 1.0

        # Factor de carga actual (invertido)
        load_factor = 1.0 - capabilities.current_load
        score *= load_factor

        # Bonus por compatibilidad de precisión
        if task.task_type == "inference":
            precision = task.resource_requirements.get("precision", "fp32")
            if precision == "fp16" and capabilities.supports_fp16:
                score *= 1.1
            elif precision == "int8" and capabilities.supports_int8:
                score *= 1.1

        return score

    async def _execute_task(self, task: ScheduledTask, node_id: str):
        """Ejecutar tarea en el nodo asignado."""
        task.assigned_node = node_id
        task.status = "running"
        task.start_time = time.time()
        self.active_tasks[task.task_id] = task

        try:
            # Simular ejecución (en implementación real, esto sería la lógica específica)
            execution_time = await self._simulate_task_execution(task, node_id)

            # Marcar como completada
            task.status = "completed"
            task.end_time = time.time()

            # Calcular métricas
            actual_duration = task.end_time - task.start_time
            self.task_execution_times[f"{task.task_type}_{node_id}"].append(actual_duration)

            # Callback de éxito
            if task.on_complete:
                await task.on_complete()

            self.stats["total_tasks_completed"] += 1
            logger.info(f"✅ Tarea completada: {task.task_id} en {actual_duration:.2f}s")
        except Exception as e:
            task.status = "failed"
            task.end_time = time.time()

            # Callback de error
            if task.on_failure:
                await task.on_failure(e)

            self.stats["total_tasks_failed"] += 1
            logger.error(f"❌ Tarea fallida: {task.task_id} - {e}")

        finally:
            # Limpiar tarea activa
            self.active_tasks.pop(task.task_id, None)

    async def _simulate_task_execution(self, task: ScheduledTask, node_id: str) -> float:
        """Simular ejecución de tarea (placeholder para implementación real)."""
        # En implementación real, aquí iría la lógica específica de cada tipo de tarea
        base_time = task.estimated_duration

        # Ajustar por capacidades del nodo
        if node_id in self.node_capabilities:
            capabilities = self.node_capabilities[node_id]
            base_time /= capabilities.performance_score

        # Añadir variabilidad
        variation = np.random.normal(0, 0.1 * base_time)
        actual_time = max(0.1, base_time + variation)

        await asyncio.sleep(actual_time)
        return actual_time

    async def _monitoring_worker(self):
        """Worker de monitoreo de recursos."""
        while self.running:
            try:
                await self._update_node_capabilities()
                await self._update_resource_stats()

                # Verificar si necesitamos escalado
                if self.config.adaptive_scaling:
                    await self._check_scaling_needs()

                await asyncio.sleep(self.config.monitoring_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Error en monitoring worker: {e}")
                await asyncio.sleep(5)

    async def _detect_local_capabilities(self):
        """Detectar capacidades del nodo local."""
        capabilities = HardwareCapabilities(node_id=self.local_node_id)

        try:
            # Detectar CPU
            cpu_info = cpuinfo.get_cpu_info()
            capabilities.cpu_cores = psutil.cpu_count(logical=True)
            capabilities.cpu_frequency_mhz = cpu_info.get("hz_actual", [0])[0] / 1e6 if cpu_info.get("hz_actual") else 0

            # Detectar memoria
            memory = psutil.virtual_memory()
            capabilities.total_memory_gb = memory.total / (1024**3)
            capabilities.available_memory_gb = memory.available / (1024**3)

            # Detectar GPU
            if torch.cuda.is_available():
                capabilities.hardware_type = HardwareType.GPU
                capabilities.device_name = torch.cuda.get_device_name(0)
                capabilities.gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

                # Calcular score de rendimiento
                gpu_name = capabilities.device_name.lower()
                if "rtx" in gpu_name or "gtx" in gpu_name:
                    capabilities.performance_score = 2.0  # GPUs de consumidor
                elif "a100" in gpu_name or "v100" in gpu_name:
                    capabilities.performance_score = 4.0  # GPUs de datacenter
                elif "t4" in gpu_name:
                    capabilities.performance_score = 1.5

                capabilities.supports_fp16 = True
                capabilities.supports_bfloat16 = "ampere" in gpu_name or "ada" in gpu_name

            elif torch.backends.mps.is_available():
                capabilities.hardware_type = HardwareType.MPS
                capabilities.device_name = "Apple Silicon"
                capabilities.performance_score = 1.5
                capabilities.supports_fp16 = True

            else:
                capabilities.hardware_type = HardwareType.CPU
                capabilities.device_name = cpu_info.get("brand_raw", "Unknown CPU")
                capabilities.performance_score = 1.0

            # Calcular batch size máximo basado en memoria
            if capabilities.hardware_type == HardwareType.GPU:
                # Estimación conservadora: 1GB por batch unit
                capabilities.max_batch_size = max(1, int(capabilities.gpu_memory_gb / 1.0))
            else:
                capabilities.max_batch_size = min(4, capabilities.cpu_cores // 2)

            self.node_capabilities[self.local_node_id] = capabilities
            logger.info(f"🔍 Capacidades detectadas para {self.local_node_id}: {capabilities.hardware_type.value}, {capabilities.performance_score:.1f} score")

        except Exception as e:
            logger.error(f"❌ Error detectando capacidades: {e}")

    async def _update_node_capabilities(self):
        """Actualizar capacidades dinámicas de nodos."""
        for node_id, capabilities in self.node_capabilities.items():
            try:
                # Actualizar carga actual
                if capabilities.hardware_type == HardwareType.GPU and torch.cuda.is_available():
                    capabilities.current_load = torch.cuda.utilization() / 100.0
                else:
                    capabilities.current_load = psutil.cpu_percent() / 100.0

                # Actualizar memoria disponible
                memory = psutil.virtual_memory()
                capabilities.available_memory_gb = memory.available / (1024**3)

                capabilities.last_updated = time.time()

            except Exception as e:
                logger.warning(f"⚠️ Error actualizando capacidades de {node_id}: {e}")

    async def _update_resource_stats(self):
        """Actualizar estadísticas generales de recursos."""
        if not self.node_capabilities:
            return

        total_load = 0.0
        total_performance = 0.0

        for capabilities in self.node_capabilities.values():
            total_load += capabilities.current_load
            total_performance += capabilities.performance_score

        avg_load = total_load / len(self.node_capabilities)
        avg_performance = total_performance / len(self.node_capabilities)

        self.stats["resource_utilization"] = avg_load
        self.stats["load_balancing_efficiency"] = 1.0 - abs(avg_load - 0.5)  # Eficiencia de balanceo

    async def _check_scaling_needs(self):
        """Verificar si se necesita escalado."""
        avg_load = self.stats["resource_utilization"]

        if avg_load > self.config.load_threshold_high:
            logger.warning(f"⚠️ Alta carga detectada: {avg_load:.2f}, considerando escalado")
        elif avg_load < self.config.load_threshold_low:
            logger.info(f"💤 Baja carga detectada: {avg_load:.2f}, recursos subutilizados")
    async def _wait_for_active_tasks(self):
        """Esperar a que terminen las tareas activas."""
        if not self.active_tasks:
            return

        logger.info(f"⏳ Esperando {len(self.active_tasks)} tareas activas...")

        # Esperar con timeout
        timeout = self.config.task_timeout_seconds
        start_time = time.time()

        while self.active_tasks and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)

        if self.active_tasks:
            logger.warning(f"⚠️ {len(self.active_tasks)} tareas no terminaron en timeout")

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del programador."""
        queue_size = self.task_queue.qsize() if hasattr(self.task_queue, 'qsize') else 0

        return {
            **self.stats,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": queue_size,
            "available_nodes": len(self.node_capabilities),
            "node_capabilities": {
                node_id: {
                    "hardware_type": cap.hardware_type.value,
                    "performance_score": cap.performance_score,
                    "current_load": cap.current_load,
                    "available_memory_gb": cap.available_memory_gb
                }
                for node_id, cap in self.node_capabilities.items()
            }
        }

    def register_remote_node(self, node_id: str, capabilities: HardwareCapabilities):
        """Registrar un nodo remoto para scheduling distribuido."""
        self.node_capabilities[node_id] = capabilities
        logger.info(f"📡 Nodo remoto registrado: {node_id} ({capabilities.hardware_type.value})")

    def unregister_node(self, node_id: str):
        """Desregistrar un nodo."""
        if node_id in self.node_capabilities:
            del self.node_capabilities[node_id]

            # Reasignar tareas activas de este nodo
            affected_tasks = [t for t in self.active_tasks.values() if t.assigned_node == node_id]
            for task in affected_tasks:
                task.assigned_node = None
                task.status = "pending"
                # Reencolar (esto sería más complejo en implementación real)

            logger.info(f"📴 Nodo desregistrado: {node_id}")


# Funciones de conveniencia
def create_resource_aware_scheduler(
    local_node_id: str = "local",
    load_balancing_strategy: str = "adaptive",
    max_concurrent_tasks: int = 4
) -> ResourceAwareScheduler:
    """
    Crear programador consciente de recursos con configuración optimizada.

    Args:
        local_node_id: ID del nodo local
        load_balancing_strategy: Estrategia de balanceo de carga
        max_concurrent_tasks: Máximo de tareas concurrentes por nodo

    Returns:
        Programador configurado
    """
    config = SchedulerConfig(
        load_balancing_strategy=load_balancing_strategy,
        max_concurrent_tasks_per_node=max_concurrent_tasks,
        federated_aware_scheduling=True
    )

    return ResourceAwareScheduler(config, local_node_id)


if __name__ == "__main__":
    # Demo del programador consciente de recursos
    print("🚀 ResourceAwareScheduler Demo")
    print("Para uso completo, inicializar con configuración específica")