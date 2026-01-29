"""
Multi-Coordinator Architecture para Federated Learning Horizontal Scaling

Implementa arquitectura de múltiples coordinators con:
- Load balancing automático
- Failover automático
- Coordinación distribuida
- State synchronization
"""

import asyncio
import logging
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import random
import uuid

logger = logging.getLogger(__name__)


class CoordinatorRole(Enum):
    """Roles de coordinator."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKUP = "backup"


class CoordinatorStatus(Enum):
    """Estados de coordinator."""
    STARTING = "starting"
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILING = "failing"
    OFFLINE = "offline"


@dataclass
class CoordinatorNode:
    """Nodo coordinator en la arquitectura distribuida."""
    coordinator_id: str
    host: str
    port: int
    role: CoordinatorRole = CoordinatorRole.SECONDARY
    status: CoordinatorStatus = CoordinatorStatus.STARTING
    last_heartbeat: Optional[datetime] = None
    active_sessions: int = 0
    total_sessions: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_latency: float = 0.0
    is_healthy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def url(self) -> str:
        """URL completa del coordinator."""
        return f"http://{self.host}:{self.port}"

    @property
    def is_primary(self) -> bool:
        """Verificar si es el coordinator primario."""
        return self.role == CoordinatorRole.PRIMARY

    @property
    def is_active(self) -> bool:
        """Verificar si está activo."""
        return self.status in [CoordinatorStatus.ACTIVE, CoordinatorStatus.DEGRADED]

    def update_health_metrics(self, cpu: float, memory: float, latency: float):
        """Actualizar métricas de salud."""
        self.cpu_usage = cpu
        self.memory_usage = memory
        self.network_latency = latency
        self.last_heartbeat = datetime.now()

        # Determinar salud basada en métricas
        self.is_healthy = (
            self.cpu_usage < 80.0 and
            self.memory_usage < 85.0 and
            self.network_latency < 100.0
        )

        # Actualizar status
        if not self.is_healthy and self.status == CoordinatorStatus.ACTIVE:
            self.status = CoordinatorStatus.DEGRADED
        elif self.is_healthy and self.status == CoordinatorStatus.DEGRADED:
            self.status = CoordinatorStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'coordinator_id': self.coordinator_id,
            'host': self.host,
            'port': self.port,
            'role': self.role.value,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'active_sessions': self.active_sessions,
            'total_sessions': self.total_sessions,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'network_latency': self.network_latency,
            'is_healthy': self.is_healthy,
            'metadata': self.metadata
        }


@dataclass
class SessionState:
    """Estado de una sesión federated learning."""
    session_id: str
    coordinator_id: str
    status: str = "active"
    node_count: int = 0
    round_number: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'session_id': self.session_id,
            'coordinator_id': self.coordinator_id,
            'status': self.status,
            'node_count': self.node_count,
            'round_number': self.round_number,
            'last_activity': self.last_activity.isoformat(),
            'metadata': self.metadata
        }


class LoadBalancer:
    """
    Load balancer para distribuir carga entre coordinators.

    Algoritmos soportados:
    - Round Robin
    - Least Connections
    - Weighted Round Robin
    - Resource Based
    """

    def __init__(self, coordinators: Dict[str, CoordinatorNode]):
        self.coordinators = coordinators
        self.algorithms = {
            'round_robin': self._round_robin,
            'least_connections': self._least_connections,
            'weighted_round_robin': self._weighted_round_robin,
            'resource_based': self._resource_based
        }
        self.current_index = 0
        self.weights: Dict[str, int] = {}

    def select_coordinator(self, algorithm: str = 'resource_based') -> Optional[CoordinatorNode]:
        """Seleccionar coordinator usando el algoritmo especificado."""
        if algorithm not in self.algorithms:
            algorithm = 'resource_based'

        return self.algorithms[algorithm]()

    def _round_robin(self) -> Optional[CoordinatorNode]:
        """Algoritmo Round Robin."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active]

        if not active_coordinators:
            return None

        coordinator = active_coordinators[self.current_index % len(active_coordinators)]
        self.current_index += 1
        return coordinator

    def _least_connections(self) -> Optional[CoordinatorNode]:
        """Algoritmo Least Connections."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active]

        if not active_coordinators:
            return None

        # Seleccionar coordinator con menos conexiones activas
        return min(active_coordinators, key=lambda c: c.active_sessions)

    def _weighted_round_robin(self) -> Optional[CoordinatorNode]:
        """Algoritmo Weighted Round Robin."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active]

        if not active_coordinators:
            return None

        # Usar pesos basados en capacidad (inversamente proporcional a la carga)
        total_weight = sum(self._get_weight(c) for c in active_coordinators)

        if total_weight == 0:
            return random.choice(active_coordinators)

        # Selección weighted
        rand = random.uniform(0, total_weight)
        current_weight = 0

        for coordinator in active_coordinators:
            current_weight += self._get_weight(coordinator)
            if rand <= current_weight:
                return coordinator

        return active_coordinators[-1]

    def _resource_based(self) -> Optional[CoordinatorNode]:
        """Algoritmo basado en recursos (recomendado)."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active and c.is_healthy]

        if not active_coordinators:
            return None

        # Calcular score basado en recursos disponibles
        scored_coordinators = []
        for coordinator in active_coordinators:
            # Score = capacidad disponible (inversamente proporcional a uso)
            cpu_score = max(0, 100 - coordinator.cpu_usage)
            memory_score = max(0, 100 - coordinator.memory_usage)
            latency_penalty = min(50, coordinator.network_latency)  # Penalización por latencia

            total_score = (cpu_score + memory_score) / 2 - latency_penalty
            scored_coordinators.append((coordinator, total_score))

        # Seleccionar coordinator con mejor score
        return max(scored_coordinators, key=lambda x: x[1])[0]

    def _get_weight(self, coordinator: CoordinatorNode) -> int:
        """Obtener peso para weighted round robin."""
        if coordinator.coordinator_id not in self.weights:
            # Peso base = 10, ajustado por recursos
            base_weight = 10
            cpu_factor = max(0.1, (100 - coordinator.cpu_usage) / 100)
            memory_factor = max(0.1, (100 - coordinator.memory_usage) / 100)
            self.weights[coordinator.coordinator_id] = int(base_weight * cpu_factor * memory_factor)

        return self.weights[coordinator.coordinator_id]


class FailoverManager:
    """
    Gestor de failover automático para coordinators.

    Características:
    - Detección automática de fallos
    - Promoción automática de secondary a primary
    - Rebalanceo automático de carga
    - Recuperación automática
    """

    def __init__(self, coordinators: Dict[str, CoordinatorNode], load_balancer: LoadBalancer):
        self.coordinators = coordinators
        self.load_balancer = load_balancer
        self.failover_history: List[Dict[str, Any]] = []
        self.heartbeat_timeout = 30  # segundos
        self.failover_lock = asyncio.Lock()

    async def monitor_health(self):
        """Monitorear salud de coordinators."""
        while True:
            try:
                await self._check_coordinator_health()
                await self._handle_failover_if_needed()
                await asyncio.sleep(10)  # Verificar cada 10 segundos

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(30)

    async def _check_coordinator_health(self):
        """Verificar salud de todos los coordinators."""
        for coordinator in self.coordinators.values():
            # Simular verificación de salud (en producción sería HTTP call)
            is_healthy = await self._perform_health_check(coordinator)

            if not is_healthy and coordinator.is_active:
                logger.warning(f"Coordinator {coordinator.coordinator_id} health check failed")
                coordinator.status = CoordinatorStatus.FAILING
                coordinator.is_healthy = False

            elif is_healthy and not coordinator.is_healthy:
                logger.info(f"Coordinator {coordinator.coordinator_id} recovered")
                coordinator.status = CoordinatorStatus.ACTIVE
                coordinator.is_healthy = True
                coordinator.last_heartbeat = datetime.now()

    async def _perform_health_check(self, coordinator: CoordinatorNode) -> bool:
        """Realizar verificación de salud de un coordinator."""
        try:
            # Simular network call con timeout
            await asyncio.sleep(0.1)  # Simular latencia

            # Verificar si el coordinator está respondiendo
            time_since_heartbeat = (
                datetime.now() - coordinator.last_heartbeat
            ).total_seconds() if coordinator.last_heartbeat else float('inf')

            # Considerar healthy si heartbeat reciente y métricas OK
            is_recent_heartbeat = time_since_heartbeat < self.heartbeat_timeout
            is_low_resource_usage = coordinator.cpu_usage < 90 and coordinator.memory_usage < 90

            return is_recent_heartbeat and is_low_resource_usage

        except Exception as e:
            logger.debug(f"Health check failed for {coordinator.coordinator_id}: {e}")
            return False

    async def _handle_failover_if_needed(self):
        """Manejar failover si es necesario."""
        async with self.failover_lock:
            # Verificar si hay primary coordinator caído
            primary_coordinators = [c for c in self.coordinators.values() if c.is_primary]

            if not primary_coordinators or not any(c.is_active for c in primary_coordinators):
                # No hay primary activo, iniciar failover
                await self._initiate_failover()

    async def _initiate_failover(self):
        """Iniciar proceso de failover."""
        logger.warning("Initiating coordinator failover...")

        # Encontrar el mejor candidate para primary
        candidates = [c for c in self.coordinators.values()
                     if c.status == CoordinatorStatus.ACTIVE and c.is_healthy]

        if not candidates:
            logger.error("No healthy coordinators available for failover!")
            return

        # Seleccionar candidate con mejor métricas
        new_primary = min(candidates, key=lambda c: c.cpu_usage + c.memory_usage)

        # Encontrar old primary
        old_primary = None
        for coordinator in self.coordinators.values():
            if coordinator.is_primary:
                old_primary = coordinator
                coordinator.role = CoordinatorRole.SECONDARY
                coordinator.status = CoordinatorStatus.OFFLINE
                break

        # Promover new primary
        new_primary.role = CoordinatorRole.PRIMARY
        new_primary.status = CoordinatorStatus.ACTIVE

        # Registrar failover
        failover_event = {
            'timestamp': datetime.now().isoformat(),
            'old_primary': old_primary.coordinator_id if old_primary else None,
            'new_primary': new_primary.coordinator_id,
            'reason': 'primary_failure',
            'candidates_count': len(candidates)
        }

        self.failover_history.append(failover_event)

        logger.info(f"Failover completed: {old_primary.coordinator_id if old_primary else 'None'} -> {new_primary.coordinator_id}")

        # Notificar otros coordinators (simulado)
        await self._notify_coordinators_of_failover(new_primary, old_primary)

    async def _notify_coordinators_of_failover(self, new_primary: CoordinatorNode, old_primary: Optional[CoordinatorNode]):
        """Notificar a otros coordinators del failover."""
        # En implementación real, esto sería una llamada HTTP a otros coordinators
        logger.info(f"Notifying coordinators of failover: {new_primary.coordinator_id} is now primary")

    def get_failover_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de failovers."""
        return self.failover_history


class StateSynchronizer:
    """
    Sincronizador de estado entre coordinators.

    Características:
    - Sincronización de sesiones activas
    - Replicación de estado crítico
    - Conflict resolution
    - Consistency guarantees
    """

    def __init__(self, coordinators: Dict[str, CoordinatorNode]):
        self.coordinators = coordinators
        self.sessions: Dict[str, SessionState] = {}
        self.sync_interval = 5  # segundos
        self.last_sync: Dict[str, datetime] = {}

    async def start_sync(self):
        """Iniciar sincronización continua."""
        while True:
            try:
                await self._sync_all_coordinators()
                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in state synchronization: {e}")
                await asyncio.sleep(30)

    async def _sync_all_coordinators(self):
        """Sincronizar estado con todos los coordinators."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active]

        for coordinator in active_coordinators:
            try:
                await self._sync_with_coordinator(coordinator)
                self.last_sync[coordinator.coordinator_id] = datetime.now()

            except Exception as e:
                logger.warning(f"Failed to sync with coordinator {coordinator.coordinator_id}: {e}")

    async def _sync_with_coordinator(self, coordinator: CoordinatorNode):
        """Sincronizar estado con un coordinator específico."""
        # En implementación real, esto sería una llamada HTTP para obtener estado
        # Por ahora, simulamos sincronización

        # Simular obtener sesiones del coordinator remoto
        remote_sessions = await self._fetch_remote_sessions(coordinator)

        # Merge con estado local
        for session_id, remote_session in remote_sessions.items():
            if session_id not in self.sessions:
                self.sessions[session_id] = remote_session
            else:
                # Conflict resolution: last write wins
                local_session = self.sessions[session_id]
                if remote_session.last_activity > local_session.last_activity:
                    self.sessions[session_id] = remote_session

        # Propagar cambios locales al coordinator remoto
        local_sessions = {sid: s for sid, s in self.sessions.items()
                         if s.coordinator_id == coordinator.coordinator_id}

        await self._push_local_sessions(coordinator, local_sessions)

    async def _fetch_remote_sessions(self, coordinator: CoordinatorNode) -> Dict[str, SessionState]:
        """Obtener sesiones remotas (simulado)."""
        # Simulación: crear algunas sesiones de ejemplo
        sessions = {}
        for i in range(random.randint(0, 5)):
            session_id = f"session_{coordinator.coordinator_id}_{i}"
            sessions[session_id] = SessionState(
                session_id=session_id,
                coordinator_id=coordinator.coordinator_id,
                node_count=random.randint(10, 100),
                round_number=random.randint(1, 10)
            )
        return sessions

    async def _push_local_sessions(self, coordinator: CoordinatorNode, sessions: Dict[str, SessionState]):
        """Enviar sesiones locales al coordinator remoto (simulado)."""
        logger.debug(f"Pushing {len(sessions)} sessions to coordinator {coordinator.coordinator_id}")

    def add_session(self, session: SessionState):
        """Añadir nueva sesión al estado global."""
        self.sessions[session.session_id] = session

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Actualizar sesión."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.last_activity = datetime.now()

    def remove_session(self, session_id: str):
        """Remover sesión."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_sessions_for_coordinator(self, coordinator_id: str) -> List[SessionState]:
        """Obtener sesiones para un coordinator específico."""
        return [s for s in self.sessions.values() if s.coordinator_id == coordinator_id]

    def get_global_session_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas globales de sesiones."""
        total_sessions = len(self.sessions)
        active_sessions = sum(1 for s in self.sessions.values() if s.status == 'active')
        total_nodes = sum(s.node_count for s in self.sessions.values())

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_nodes': total_nodes,
            'avg_nodes_per_session': total_nodes / total_sessions if total_sessions > 0 else 0
        }


class MultiCoordinatorManager:
    """
    Gestor principal de arquitectura multi-coordinator.

    Coordina múltiples coordinators con load balancing,
    failover automático y sincronización de estado.
    """

    def __init__(self, coordinator_configs: List[Dict[str, Any]]):
        self.coordinators: Dict[str, CoordinatorNode] = {}
        self.load_balancer: Optional[LoadBalancer] = None
        self.failover_manager: Optional[FailoverManager] = None
        self.state_synchronizer: Optional[StateSynchronizer] = None

        # Inicializar coordinators
        self._initialize_coordinators(coordinator_configs)

        # Inicializar componentes
        self.load_balancer = LoadBalancer(self.coordinators)
        self.failover_manager = FailoverManager(self.coordinators, self.load_balancer)
        self.state_synchronizer = StateSynchronizer(self.coordinators)

        # Estado del sistema
        self.is_running = False
        self.start_time: Optional[datetime] = None

        logger.info(f"MultiCoordinatorManager initialized with {len(self.coordinators)} coordinators")

    def _initialize_coordinators(self, configs: List[Dict[str, Any]]):
        """Inicializar coordinators desde configuración."""
        for i, config in enumerate(configs):
            coordinator = CoordinatorNode(
                coordinator_id=config.get('id', f"coordinator_{i}"),
                host=config['host'],
                port=config['port'],
                role=CoordinatorRole.PRIMARY if i == 0 else CoordinatorRole.SECONDARY,
                status=CoordinatorStatus.STARTING
            )
            self.coordinators[coordinator.coordinator_id] = coordinator

    async def start(self):
        """Iniciar sistema multi-coordinator."""
        logger.info("Starting multi-coordinator system...")

        self.is_running = True
        self.start_time = datetime.now()

        # Iniciar monitoring de salud
        asyncio.create_task(self.failover_manager.monitor_health())

        # Iniciar sincronización de estado
        asyncio.create_task(self.state_synchronizer.start_sync())

        # Simular inicialización de coordinators
        await self._initialize_coordinator_states()

        logger.info("Multi-coordinator system started successfully")

    async def stop(self):
        """Detener sistema multi-coordinator."""
        logger.info("Stopping multi-coordinator system...")
        self.is_running = False

        # Aquí iría lógica de graceful shutdown
        logger.info("Multi-coordinator system stopped")

    async def _initialize_coordinator_states(self):
        """Inicializar estados de coordinators."""
        for coordinator in self.coordinators.values():
            # Simular métricas iniciales
            coordinator.update_health_metrics(
                cpu=random.uniform(10, 30),
                memory=random.uniform(20, 40),
                latency=random.uniform(5, 15)
            )
            coordinator.status = CoordinatorStatus.ACTIVE
            coordinator.last_heartbeat = datetime.now()

        logger.info("Coordinator states initialized")

    def select_coordinator(self, algorithm: str = 'resource_based') -> Optional[CoordinatorNode]:
        """Seleccionar coordinator óptimo."""
        return self.load_balancer.select_coordinator(algorithm) if self.load_balancer else None

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado general del sistema."""
        active_coordinators = [c for c in self.coordinators.values() if c.is_active]
        healthy_coordinators = [c for c in self.coordinators.values() if c.is_healthy]

        primary_coordinators = [c for c in active_coordinators if c.is_primary]

        session_stats = self.state_synchronizer.get_global_session_stats() if self.state_synchronizer else {}

        return {
            'total_coordinators': len(self.coordinators),
            'active_coordinators': len(active_coordinators),
            'healthy_coordinators': len(healthy_coordinators),
            'primary_coordinators': len(primary_coordinators),
            'system_health': 'healthy' if len(healthy_coordinators) >= len(self.coordinators) * 0.5 else 'degraded',
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'session_stats': session_stats,
            'failover_events': len(self.failover_manager.failover_history) if self.failover_manager else 0
        }

    def get_coordinator_details(self) -> List[Dict[str, Any]]:
        """Obtener detalles de todos los coordinators."""
        return [c.to_dict() for c in self.coordinators.values()]

    async def simulate_load_test(self, duration_seconds: int = 60):
        """Simular prueba de carga en el sistema multi-coordinator."""
        logger.info(f"Starting load test simulation for {duration_seconds} seconds...")

        start_time = time.time()
        session_count = 0

        while time.time() - start_time < duration_seconds and self.is_running:
            # Seleccionar coordinator
            coordinator = self.select_coordinator()
            if coordinator:
                # Simular nueva sesión
                session_id = f"test_session_{int(time.time())}_{session_count}"
                session = SessionState(
                    session_id=session_id,
                    coordinator_id=coordinator.coordinator_id,
                    node_count=random.randint(10, 50)
                )

                # Añadir sesión al estado
                self.state_synchronizer.add_session(session)
                coordinator.active_sessions += 1
                coordinator.total_sessions += 1

                session_count += 1

                # Simular actividad de sesión
                for _ in range(random.randint(5, 15)):
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    session.round_number += 1
                    session.last_activity = datetime.now()

                # Finalizar sesión
                coordinator.active_sessions -= 1

            await asyncio.sleep(random.uniform(0.5, 2.0))

        logger.info(f"Load test completed: {session_count} sessions simulated")

    def get_load_distribution(self) -> Dict[str, Any]:
        """Obtener distribución de carga entre coordinators."""
        distribution = {}

        for coordinator in self.coordinators.values():
            distribution[coordinator.coordinator_id] = {
                'active_sessions': coordinator.active_sessions,
                'total_sessions': coordinator.total_sessions,
                'cpu_usage': coordinator.cpu_usage,
                'memory_usage': coordinator.memory_usage,
                'is_primary': coordinator.is_primary,
                'status': coordinator.status.value
            }

        return distribution


# Funciones de conveniencia

def create_default_coordinator_config() -> List[Dict[str, Any]]:
    """Crear configuración por defecto de coordinators."""
    return [
        {
            'id': 'coordinator-01',
            'host': 'localhost',
            'port': 8000,
            'role': 'primary'
        },
        {
            'id': 'coordinator-02',
            'host': 'localhost',
            'port': 8001,
            'role': 'secondary'
        },
        {
            'id': 'coordinator-03',
            'host': 'localhost',
            'port': 8002,
            'role': 'secondary'
        }
    ]


async def create_multi_coordinator_system(config: Optional[List[Dict[str, Any]]] = None) -> MultiCoordinatorManager:
    """Crear sistema multi-coordinator."""
    if config is None:
        config = create_default_coordinator_config()

    manager = MultiCoordinatorManager(config)
    await manager.start()
    return manager


async def run_failover_test(manager: MultiCoordinatorManager):
    """Ejecutar prueba de failover."""
    logger.info("Running failover test...")

    # Simular fallo del primary coordinator
    primary_coordinators = [c for c in manager.coordinators.values() if c.is_primary]
    if primary_coordinators:
        primary = primary_coordinators[0]
        logger.info(f"Simulating failure of primary coordinator: {primary.coordinator_id}")

        # Simular fallo
        primary.status = CoordinatorStatus.FAILING
        primary.is_healthy = False
        primary.cpu_usage = 95.0  # Simular alta carga

        # Esperar a que failover ocurra
        await asyncio.sleep(15)

        # Verificar nuevo primary
        new_primary = [c for c in manager.coordinators.values() if c.is_primary]
        if new_primary and new_primary[0] != primary:
            logger.info(f"✅ Failover successful: {primary.coordinator_id} -> {new_primary[0].coordinator_id}")
        else:
            logger.error("❌ Failover failed")

    return manager.get_system_status()