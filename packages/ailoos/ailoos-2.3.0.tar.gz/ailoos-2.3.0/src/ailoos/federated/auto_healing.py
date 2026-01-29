"""
Sistema de Auto-Healing para Aprendizaje Federado
Implementa detección automática de fallos en nodos y redistribución de carga de trabajo.
"""

import asyncio
import time
import threading
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from ..core.logging import get_logger
from .session import FederatedSession
from .round_orchestrator import RoundOrchestrator, RoundState, NodeParticipationStatus
from .node_scheduler import NodeScheduler, SelectionCriteria

logger = get_logger(__name__)


class NodeHealthStatus(Enum):
    """Estados de salud de un nodo."""
    HEALTHY = "healthy"
    UNSTABLE = "unstable"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


class HealingAction(Enum):
    """Acciones de auto-healing disponibles."""
    REPLACE_NODE = "replace_node"
    REDISTRIBUTE_WORKLOAD = "redistribute_workload"
    SCALE_DOWN = "scale_down"
    WAIT_FOR_RECOVERY = "wait_for_recovery"
    ABORT_ROUND = "abort_round"


@dataclass
class NodeHealth:
    """Información de salud de un nodo."""
    node_id: str
    status: NodeHealthStatus = NodeHealthStatus.UNKNOWN
    last_heartbeat: float = 0.0
    consecutive_failures: int = 0
    response_time: float = 0.0
    assigned_workload: int = 0
    completed_workload: int = 0
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3


@dataclass
class HealingConfig:
    """Configuración del sistema de auto-healing."""
    heartbeat_interval: int = 30  # segundos
    heartbeat_timeout: int = 90   # segundos
    max_consecutive_failures: int = 3
    healing_cooldown: int = 60    # segundos entre acciones de healing
    enable_automatic_replacement: bool = True
    enable_workload_redistribution: bool = True
    min_nodes_for_healing: int = 3
    max_replacement_attempts: int = 5
    graceful_degradation_threshold: float = 0.5  # 50% de nodos mínimos


class NodeHealthMonitor:
    """
    Monitor de salud de nodos basado en heartbeats.
    """

    def __init__(self, config: HealingConfig):
        self.config = config
        self.node_health: Dict[str, NodeHealth] = {}
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.heartbeat_callbacks: List[Callable] = []
        self._lock = threading.RLock()

        logger.info("🏥 NodeHealthMonitor initialized")

    async def start_monitoring(self, initial_nodes: List[str]):
        """Iniciar monitoreo de nodos."""
        with self._lock:
            if self.monitoring_active:
                return

            # Inicializar estado de salud para nodos
            for node_id in initial_nodes:
                self.node_health[node_id] = NodeHealth(node_id=node_id)

            self.monitoring_active = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())

            logger.info(f"🏥 Started monitoring {len(initial_nodes)} nodes")

    async def stop_monitoring(self):
        """Detener monitoreo."""
        with self._lock:
            self.monitoring_active = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass

            logger.info("🏥 Stopped node monitoring")

    def record_heartbeat(self, node_id: str, response_time: float = 0.0):
        """Registrar heartbeat de un nodo."""
        with self._lock:
            if node_id not in self.node_health:
                self.node_health[node_id] = NodeHealth(node_id=node_id)

            health = self.node_health[node_id]
            health.last_heartbeat = time.time()
            health.response_time = response_time
            health.consecutive_failures = 0
            health.status = NodeHealthStatus.HEALTHY

            # Trigger callbacks
            for callback in self.heartbeat_callbacks:
                try:
                    callback(node_id, health)
                except Exception as e:
                    logger.error(f"Error in heartbeat callback: {e}")

    def record_failure(self, node_id: str, failure_reason: str):
        """Registrar fallo de un nodo."""
        with self._lock:
            if node_id not in self.node_health:
                self.node_health[node_id] = NodeHealth(node_id=node_id)

            health = self.node_health[node_id]
            health.consecutive_failures += 1
            health.failure_history.append({
                'timestamp': time.time(),
                'reason': failure_reason,
                'consecutive_failures': health.consecutive_failures
            })

            # Actualizar estado basado en fallos consecutivos
            if health.consecutive_failures >= self.config.max_consecutive_failures:
                health.status = NodeHealthStatus.FAILED
                logger.warning(f"🚨 Node {node_id} marked as FAILED after {health.consecutive_failures} consecutive failures")
            else:
                health.status = NodeHealthStatus.UNSTABLE
                logger.warning(f"⚠️ Node {node_id} marked as UNSTABLE ({health.consecutive_failures}/{self.config.max_consecutive_failures} failures)")

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.monitoring_active:
            try:
                current_time = time.time()

                with self._lock:
                    failed_nodes = []

                    for node_id, health in self.node_health.items():
                        # Verificar timeout de heartbeat
                        if current_time - health.last_heartbeat > self.config.heartbeat_timeout:
                            if health.status != NodeHealthStatus.FAILED:
                                self.record_failure(node_id, "heartbeat_timeout")
                                if health.status == NodeHealthStatus.FAILED:
                                    failed_nodes.append(node_id)

                        # Verificar nodos en recuperación
                        elif health.status == NodeHealthStatus.RECOVERING:
                            # Intentar reactivar si han pasado suficientes heartbeats
                            if health.recovery_attempts < health.max_recovery_attempts:
                                health.recovery_attempts += 1
                                # Aquí podríamos enviar ping de recuperación
                            else:
                                health.status = NodeHealthStatus.FAILED
                                failed_nodes.append(node_id)

                    # Reportar nodos fallidos
                    if failed_nodes:
                        logger.warning(f"🚨 Detected {len(failed_nodes)} failed nodes: {failed_nodes}")

                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    def get_node_health(self, node_id: str) -> Optional[NodeHealth]:
        """Obtener estado de salud de un nodo."""
        with self._lock:
            return self.node_health.get(node_id)

    def get_failed_nodes(self) -> List[str]:
        """Obtener lista de nodos fallidos."""
        with self._lock:
            return [node_id for node_id, health in self.node_health.items()
                    if health.status == NodeHealthStatus.FAILED]

    def get_unhealthy_nodes(self) -> List[str]:
        """Obtener lista de nodos no saludables."""
        with self._lock:
            return [node_id for node_id, health in self.node_health.items()
                    if health.status in [NodeHealthStatus.UNSTABLE, NodeHealthStatus.FAILED]]

    def add_heartbeat_callback(self, callback: Callable):
        """Agregar callback para heartbeats."""
        self.heartbeat_callbacks.append(callback)

    def update_workload(self, node_id: str, assigned: int, completed: int):
        """Actualizar métricas de carga de trabajo."""
        with self._lock:
            if node_id in self.node_health:
                health = self.node_health[node_id]
                health.assigned_workload = assigned
                health.completed_workload = completed


class FailureDetector:
    """
    Detector de fallos que analiza múltiples señales de falla.
    """

    def __init__(self, health_monitor: NodeHealthMonitor):
        self.health_monitor = health_monitor
        self.failure_callbacks: List[Callable] = []
        self.last_healing_action = 0.0

    def detect_failures(self) -> List[str]:
        """Detectar nodos fallidos usando múltiples criterios."""
        failed_nodes = set()

        # Criterio 1: Estado de salud del monitor
        failed_nodes.update(self.health_monitor.get_failed_nodes())

        # Criterio 2: Nodos desconectados por tiempo prolongado
        # (ya manejado por el health monitor)

        # Criterio 3: Nodos con alta tasa de error
        # (podría implementarse analizando failure_history)

        return list(failed_nodes)

    def should_trigger_healing(self, failed_nodes: List[str], total_nodes: int,
                             min_required_nodes: int) -> bool:
        """Determinar si se debe activar auto-healing."""
        if not failed_nodes:
            return False

        # Verificar cooldown entre acciones de healing
        current_time = time.time()
        if current_time - self.last_healing_action < 60:  # 60 segundos cooldown
            return False

        # Calcular nodos saludables restantes
        healthy_nodes = total_nodes - len(failed_nodes)

        # Activar healing si:
        # 1. Hay nodos fallidos
        # 2. Aún tenemos suficientes nodos para continuar
        # 3. No estamos por debajo del mínimo absoluto
        return (len(failed_nodes) > 0 and
                healthy_nodes >= min_required_nodes and
                healthy_nodes >= 1)  # Al menos 1 nodo para continuar

    def add_failure_callback(self, callback: Callable):
        """Agregar callback para detección de fallos."""
        self.failure_callbacks.append(callback)

    def trigger_failure_callbacks(self, failed_nodes: List[str]):
        """Disparar callbacks de fallo."""
        for callback in self.failure_callbacks:
            try:
                callback(failed_nodes)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")


class WorkloadRedistributor:
    """
    Redistribuye carga de trabajo cuando nodos fallan.
    """

    def __init__(self, health_monitor: NodeHealthMonitor):
        self.health_monitor = health_monitor

    def calculate_redistribution(self, failed_nodes: List[str],
                               active_nodes: List[str],
                               total_workload: int) -> Dict[str, int]:
        """
        Calcular redistribución de carga de trabajo.

        Args:
            failed_nodes: Nodos que fallaron
            active_nodes: Nodos aún activos
            total_workload: Carga total a redistribuir

        Returns:
            Dict[node_id: workload_amount]
        """
        if not active_nodes:
            return {}

        # Calcular carga fallida
        failed_workload = 0
        for node_id in failed_nodes:
            health = self.health_monitor.get_node_health(node_id)
            if health:
                failed_workload += health.assigned_workload

        if failed_workload == 0:
            return {}

        # Redistribuir equitativamente entre nodos activos
        base_workload = failed_workload // len(active_nodes)
        remainder = failed_workload % len(active_nodes)

        redistribution = {}
        for i, node_id in enumerate(active_nodes):
            additional_workload = base_workload
            if i < remainder:
                additional_workload += 1
            redistribution[node_id] = additional_workload

        logger.info(f"🔄 Redistributing {failed_workload} workload units from {len(failed_nodes)} failed nodes to {len(active_nodes)} active nodes")
        return redistribution

    def get_optimal_node_assignment(self, available_nodes: List[str],
                                  workload_requirements: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Asignar nodos óptimos para requisitos de carga de trabajo.

        Args:
            available_nodes: Nodos disponibles
            workload_requirements: Requisitos de carga (tipo, cantidad, etc.)

        Returns:
            Dict[workload_type: [node_ids]]
        """
        # Implementación simplificada - asignación equitativa
        if not available_nodes:
            return {}

        # Para cada tipo de carga, asignar nodos disponibles
        assignment = {}
        nodes_per_type = max(1, len(available_nodes) // len(workload_requirements))

        node_index = 0
        for workload_type in workload_requirements.keys():
            assigned_nodes = []
            for _ in range(nodes_per_type):
                if node_index < len(available_nodes):
                    assigned_nodes.append(available_nodes[node_index])
                    node_index += 1

            if assigned_nodes:
                assignment[workload_type] = assigned_nodes

        return assignment


class AutoHealingCoordinator:
    """
    Coordinador principal del sistema de auto-healing.
    """

    def __init__(self, session: FederatedSession, orchestrator: RoundOrchestrator,
                 node_scheduler: Optional[NodeScheduler] = None):
        self.session = session
        self.orchestrator = orchestrator
        self.node_scheduler = node_scheduler

        # Componentes del sistema
        self.config = HealingConfig()
        self.health_monitor = NodeHealthMonitor(self.config)
        self.failure_detector = FailureDetector(self.health_monitor)
        self.workload_redistributor = WorkloadRedistributor(self.health_monitor)

        # Estado
        self.healing_active = False
        self.last_healing_action = 0.0
        self.healing_stats = {
            'nodes_replaced': 0,
            'workload_redistributed': 0,
            'rounds_recovered': 0,
            'total_healing_actions': 0
        }

        # Callbacks
        self._setup_callbacks()

        logger.info("🛠️ AutoHealingCoordinator initialized")

    def _setup_callbacks(self):
        """Configurar callbacks entre componentes."""
        # Callback para heartbeats
        self.health_monitor.add_heartbeat_callback(self._on_heartbeat)

        # Callback para fallos
        self.failure_detector.add_failure_callback(self._on_failure_detected)

    async def start_auto_healing(self):
        """Iniciar sistema de auto-healing."""
        if self.healing_active:
            return

        # Obtener nodos iniciales de la sesión
        initial_nodes = self.session.participants.copy()

        # Iniciar monitoreo
        await self.health_monitor.start_monitoring(initial_nodes)

        self.healing_active = True
        logger.info("🚀 Auto-healing system started")

        # Iniciar loop de verificación periódica
        asyncio.create_task(self._healing_loop())

    async def stop_auto_healing(self):
        """Detener sistema de auto-healing."""
        self.healing_active = False
        await self.health_monitor.stop_monitoring()
        logger.info("🛑 Auto-healing system stopped")

    async def _healing_loop(self):
        """Loop principal de auto-healing."""
        while self.healing_active:
            try:
                await self._check_and_heal()
                await asyncio.sleep(10)  # Verificar cada 10 segundos

            except Exception as e:
                logger.error(f"Error in healing loop: {e}")
                await asyncio.sleep(5)

    async def _check_and_heal(self):
        """Verificar estado y aplicar healing si necesario."""
        # Detectar fallos
        failed_nodes = self.failure_detector.detect_failures()

        if not failed_nodes:
            return

        # Obtener rondas activas
        active_rounds = self.orchestrator.get_active_rounds()

        for round_info in active_rounds:
            round_id = round_info['round_id']
            total_participants = round_info['participants']['expected']
            min_participants = 3  # Configurable

            # Verificar si se debe activar healing
            if self.failure_detector.should_trigger_healing(failed_nodes, total_participants, min_participants):
                await self._heal_round(round_id, failed_nodes)

    async def _heal_round(self, round_id: str, failed_nodes: List[str]):
        """Aplicar healing a una ronda específica."""
        logger.info(f"🩹 Starting healing for round {round_id}, failed nodes: {failed_nodes}")

        try:
            # Determinar acción de healing
            healing_action = await self._determine_healing_action(round_id, failed_nodes)

            # Ejecutar acción
            success = await self._execute_healing_action(round_id, healing_action, failed_nodes)

            if success:
                self.healing_stats['total_healing_actions'] += 1
                self.last_healing_action = time.time()
                logger.info(f"✅ Healing successful for round {round_id}")
            else:
                logger.warning(f"❌ Healing failed for round {round_id}")

        except Exception as e:
            logger.error(f"Error healing round {round_id}: {e}")

    async def _determine_healing_action(self, round_id: str, failed_nodes: List[str]) -> HealingAction:
        """Determinar la mejor acción de healing."""
        round_info = self.orchestrator.get_round_status(round_id)
        if not round_info:
            return HealingAction.ABORT_ROUND

        active_participants = round_info['participants']['active']
        min_required = 3  # Debería venir de configuración

        # Si tenemos suficientes nodos activos, intentar reemplazo
        if active_participants >= min_required and self.config.enable_automatic_replacement:
            return HealingAction.REPLACE_NODE

        # Si podemos redistribuir carga
        elif active_participants >= 1 and self.config.enable_workload_redistribution:
            return HealingAction.REDISTRIBUTE_WORKLOAD

        # Si estamos por debajo del mínimo, esperar recuperación o abortar
        elif active_participants < min_required:
            # Verificar si algunos nodos están en recuperación
            recovering_nodes = [n for n in failed_nodes
                              if (self.health_monitor.get_node_health(n) and
                                  self.health_monitor.get_node_health(n).status == NodeHealthStatus.RECOVERING)]

            if recovering_nodes and len(recovering_nodes) + active_participants >= min_required:
                return HealingAction.WAIT_FOR_RECOVERY
            else:
                return HealingAction.ABORT_ROUND

        return HealingAction.WAIT_FOR_RECOVERY

    async def _execute_healing_action(self, round_id: str, action: HealingAction,
                                    failed_nodes: List[str]) -> bool:
        """Ejecutar acción de healing."""
        try:
            if action == HealingAction.REPLACE_NODE:
                return await self._replace_failed_nodes(round_id, failed_nodes)

            elif action == HealingAction.REDISTRIBUTE_WORKLOAD:
                return await self._redistribute_workload(round_id, failed_nodes)

            elif action == HealingAction.WAIT_FOR_RECOVERY:
                return await self._wait_for_recovery(round_id, failed_nodes)

            elif action == HealingAction.ABORT_ROUND:
                return await self.orchestrator.cancel_round(round_id, "Auto-healing: insufficient nodes")

            else:
                logger.warning(f"Unknown healing action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing healing action {action}: {e}")
            return False

    async def _replace_failed_nodes(self, round_id: str, failed_nodes: List[str]) -> bool:
        """Reemplazar nodos fallidos con nodos nuevos."""
        if not self.node_scheduler:
            logger.warning("No node scheduler available for replacement")
            return False

        success_count = 0

        for failed_node in failed_nodes:
            try:
                # Seleccionar nodo de reemplazo
                criteria = SelectionCriteria(
                    min_participants=1,
                    max_participants=1,
                    exclude_nodes=[failed_node] + list(self.session.participants)
                )

                replacement_nodes = await self.node_scheduler.select_round_participants(criteria)

                if replacement_nodes:
                    new_node = replacement_nodes[0]

                    # Agregar nuevo nodo a la ronda
                    if await self.orchestrator.add_node_to_round(round_id, new_node):
                        # Agregar a sesión
                        self.session.add_participant(new_node)

                        # Iniciar monitoreo del nuevo nodo
                        await self.health_monitor.start_monitoring([new_node])

                        # Remover nodo fallido
                        await self.orchestrator.remove_node_from_round(round_id, failed_node, "Replaced by auto-healing")

                        self.healing_stats['nodes_replaced'] += 1
                        success_count += 1

                        logger.info(f"🔄 Replaced failed node {failed_node} with {new_node} in round {round_id}")

            except Exception as e:
                logger.error(f"Error replacing node {failed_node}: {e}")

        return success_count > 0

    async def _redistribute_workload(self, round_id: str, failed_nodes: List[str]) -> bool:
        """Redistribuir carga de trabajo de nodos fallidos."""
        try:
            # Obtener nodos activos
            round_info = self.orchestrator.get_round_status(round_id)
            if not round_info:
                return False

            active_nodes = []
            for participant in round_info.get('participants', {}):
                # Aquí necesitaríamos lógica para determinar nodos activos
                # Por simplicidad, asumimos que todos los participantes esperados están activos
                # menos los fallidos
                pass

            # Calcular redistribución
            redistribution = self.workload_redistributor.calculate_redistribution(
                failed_nodes, active_nodes, 100  # Carga total simplificada
            )

            if redistribution:
                # Aplicar redistribución (aquí iría la lógica específica)
                self.healing_stats['workload_redistributed'] += sum(redistribution.values())
                logger.info(f"🔄 Workload redistributed in round {round_id}: {redistribution}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error redistributing workload: {e}")
            return False

    async def _wait_for_recovery(self, round_id: str, failed_nodes: List[str]) -> bool:
        """Esperar recuperación de nodos."""
        logger.info(f"⏳ Waiting for recovery of nodes: {failed_nodes}")

        # Marcar nodos como en recuperación
        for node_id in failed_nodes:
            health = self.health_monitor.get_node_health(node_id)
            if health:
                health.status = NodeHealthStatus.RECOVERING
                health.recovery_attempts = 0

        # Por ahora, solo loggear - en implementación completa podría
        # enviar señales de recuperación o extender timeouts
        return True

    def _on_heartbeat(self, node_id: str, health: NodeHealth):
        """Callback para heartbeats."""
        logger.debug(f"💓 Heartbeat from {node_id} (status: {health.status.value})")

    def _on_failure_detected(self, failed_nodes: List[str]):
        """Callback para detección de fallos."""
        logger.warning(f"🚨 Failures detected: {failed_nodes}")

    def get_healing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de auto-healing."""
        return dict(self.healing_stats)

    def update_config(self, new_config: HealingConfig):
        """Actualizar configuración de healing."""
        self.config = new_config
        self.health_monitor.config = new_config
        logger.info("🔧 Auto-healing configuration updated")


# Funciones de conveniencia

def create_auto_healing_coordinator(session: FederatedSession,
                                  orchestrator: RoundOrchestrator,
                                  node_scheduler: Optional[NodeScheduler] = None) -> AutoHealingCoordinator:
    """Crear coordinador de auto-healing."""
    return AutoHealingCoordinator(session, orchestrator, node_scheduler)


async def initialize_auto_healing(coordinator: AutoHealingCoordinator) -> bool:
    """Inicializar sistema de auto-healing."""
    try:
        await coordinator.start_auto_healing()
        return True
    except Exception as e:
        logger.error(f"Error initializing auto-healing: {e}")
        return False