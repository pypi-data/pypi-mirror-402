"""
FailoverManager - Gestión automática de failover
Detecta fallos y ejecuta failover automático entre regiones y endpoints.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import random

from ...core.config import Config
from ...utils.logging import AiloosLogger


@dataclass
class FailoverPolicy:
    """Política de failover."""
    policy_id: str
    trigger_condition: str  # 'health_below_threshold', 'latency_above_threshold', 'manual'
    threshold_value: float
    cooldown_period_seconds: int = 300
    max_failover_attempts: int = 3
    failover_strategy: str = 'automatic'  # 'automatic', 'manual', 'gradual'
    notification_required: bool = True
    enabled: bool = True


@dataclass
class FailoverEvent:
    """Evento de failover."""
    event_id: str
    component_type: str  # 'region', 'endpoint'
    component_id: str
    failover_type: str  # 'automatic', 'manual', 'emergency'
    trigger_reason: str
    from_component: str
    to_component: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    affected_requests: int = 0
    rollback_possible: bool = True
    rollback_at: Optional[datetime] = None


@dataclass
class FailoverState:
    """Estado de failover de un componente."""
    component_id: str
    is_in_failover: bool = False
    active_failover_event: Optional[FailoverEvent] = None
    last_failover_attempt: Optional[datetime] = None
    consecutive_failures: int = 0
    cooldown_until: Optional[datetime] = None
    backup_components: List[str] = field(default_factory=list)


class FailoverManager:
    """
    Gestor de failover automático que detecta fallos críticos,
    ejecuta transiciones suaves y gestiona recuperación.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Políticas de failover
        self.failover_policies: Dict[str, FailoverPolicy] = {}
        self._initialize_default_policies()

        # Estados de failover
        self.failover_states: Dict[str, FailoverState] = {}

        # Historial de eventos
        self.failover_history: deque[FailoverEvent] = deque(maxlen=1000)

        # Información de componentes
        self.regions_info: Dict[str, Dict[str, Any]] = {}
        self.endpoints_info: Dict[str, Dict[str, Any]] = {}

        # Métricas
        self.failover_metrics: Dict[str, Any] = {
            'total_failovers': 0,
            'successful_failovers': 0,
            'failed_failovers': 0,
            'avg_failover_time_seconds': 0.0,
            'active_failovers': 0,
            'emergency_failovers': 0
        }

        # Configuración
        self.health_check_interval = 30
        self.failover_timeout_seconds = 300
        self.max_concurrent_failovers = 3

        # Tareas
        self.is_running = False
        self.failover_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.recovery_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar el gestor de failover."""
        if self.is_running:
            return

        self.is_running = True
        self.failover_task = asyncio.create_task(self._failover_loop())
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.recovery_task = asyncio.create_task(self._recovery_loop())

        self.logger.info("🔄 Failover Manager started")

    async def stop(self):
        """Detener el gestor de failover."""
        self.is_running = False

        if self.failover_task:
            self.failover_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.recovery_task:
            self.recovery_task.cancel()

        try:
            await asyncio.gather(
                self.failover_task, self.monitoring_task, self.recovery_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

        self.logger.info("🛑 Failover Manager stopped")

    async def register_region(self, region_id: str, region_info: Dict[str, Any]):
        """Registrar región para failover."""
        self.regions_info[region_id] = region_info

        # Inicializar estado de failover
        self.failover_states[region_id] = FailoverState(
            component_id=region_id,
            backup_components=region_info.get('backup_regions', [])
        )

        self.logger.debug(f"📍 Region {region_id} registered for failover")

    async def register_endpoint(self, endpoint_id: str, region_id: str, endpoint_info: Dict[str, Any]):
        """Registrar endpoint para failover."""
        self.endpoints_info[endpoint_id] = {
            **endpoint_info,
            'region_id': region_id
        }

        # Inicializar estado de failover
        self.failover_states[endpoint_id] = FailoverState(
            component_id=endpoint_id,
            backup_components=endpoint_info.get('backup_endpoints', [])
        )

        self.logger.debug(f"🔗 Endpoint {endpoint_id} registered for failover")

    async def check_failover_conditions(self):
        """Verificar condiciones que requieren failover."""
        await self._check_region_failover()
        await self._check_endpoint_failover()

    async def execute_manual_failover(
        self,
        component_id: str,
        target_component: str,
        reason: str = "Manual failover"
    ) -> bool:
        """Ejecutar failover manual."""
        return await self._execute_failover(
            component_id, target_component, 'manual', reason
        )

    async def _failover_loop(self):
        """Bucle principal de failover automático."""
        while self.is_running:
            try:
                await self.check_failover_conditions()
                await self._execute_pending_failovers()
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in failover loop: {e}")
                await asyncio.sleep(10)

    async def _monitoring_loop(self):
        """Bucle de monitoreo de failovers activos."""
        while self.is_running:
            try:
                await self._monitor_active_failovers()
                await self._check_failover_timeouts()
                await asyncio.sleep(60)  # Monitoreo cada minuto

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)

    async def _recovery_loop(self):
        """Bucle de recuperación de componentes."""
        while self.is_running:
            try:
                await self._attempt_recoveries()
                await asyncio.sleep(300)  # Intentar recuperaciones cada 5 minutos

            except Exception as e:
                self.logger.error(f"Error in recovery loop: {e}")
                await asyncio.sleep(150)

    async def _check_region_failover(self):
        """Verificar condiciones de failover para regiones."""
        for region_id, region_info in self.regions_info.items():
            state = self.failover_states.get(region_id)
            if not state or state.is_in_failover:
                continue

            # Verificar políticas aplicables
            for policy in self.failover_policies.values():
                if not policy.enabled:
                    continue

                should_failover = await self._evaluate_failover_condition(
                    policy, region_id, 'region'
                )

                if should_failover:
                    await self._initiate_failover(region_id, 'region', policy)
                    break

    async def _check_endpoint_failover(self):
        """Verificar condiciones de failover para endpoints."""
        for endpoint_id, endpoint_info in self.endpoints_info.items():
            state = self.failover_states.get(endpoint_id)
            if not state or state.is_in_failover:
                continue

            # Verificar políticas aplicables
            for policy in self.failover_policies.values():
                if not policy.enabled:
                    continue

                should_failover = await self._evaluate_failover_condition(
                    policy, endpoint_id, 'endpoint'
                )

                if should_failover:
                    await self._initiate_failover(endpoint_id, 'endpoint', policy)
                    break

    async def _evaluate_failover_condition(
        self,
        policy: FailoverPolicy,
        component_id: str,
        component_type: str
    ) -> bool:
        """Evaluar si se cumple la condición de failover."""
        # Verificar cooldown
        state = self.failover_states.get(component_id)
        if state and state.cooldown_until and datetime.now() < state.cooldown_until:
            return False

        # Evaluar condición específica
        if policy.trigger_condition == 'health_below_threshold':
            health_score = await self._get_component_health_score(component_id, component_type)
            return health_score < policy.threshold_value

        elif policy.trigger_condition == 'latency_above_threshold':
            avg_latency = await self._get_component_avg_latency(component_id, component_type)
            return avg_latency > policy.threshold_value

        elif policy.trigger_condition == 'manual':
            return False  # Solo manual

        return False

    async def _initiate_failover(self, component_id: str, component_type: str, policy: FailoverPolicy):
        """Iniciar proceso de failover."""
        state = self.failover_states.get(component_id)
        if not state:
            return

        # Verificar límite de failovers concurrentes
        active_failovers = len([s for s in self.failover_states.values() if s.is_in_failover])
        if active_failovers >= self.max_concurrent_failovers:
            self.logger.warning(f"⚠️ Maximum concurrent failovers reached ({active_failovers})")
            return

        # Encontrar componente de respaldo
        backup_component = await self._select_backup_component(component_id, component_type)
        if not backup_component:
            self.logger.warning(f"⚠️ No backup component available for {component_id}")
            return

        # Crear evento de failover
        event = FailoverEvent(
            event_id=f"failover_{component_id}_{int(time.time())}",
            component_type=component_type,
            component_id=component_id,
            failover_type='automatic',
            trigger_reason=f"Policy {policy.policy_id}: {policy.trigger_condition}",
            from_component=component_id,
            to_component=backup_component,
            started_at=datetime.now()
        )

        # Actualizar estado
        state.is_in_failover = True
        state.active_failover_event = event
        state.last_failover_attempt = datetime.now()

        # Registrar evento
        self.failover_history.append(event)
        self.failover_metrics['total_failovers'] += 1
        self.failover_metrics['active_failovers'] += 1

        self.logger.warning(f"🔄 Initiating failover: {component_id} -> {backup_component}")

        # Notificar (en producción: enviar alertas)

    async def _execute_pending_failovers(self):
        """Ejecutar failovers pendientes."""
        for component_id, state in self.failover_states.items():
            if not state.is_in_failover or not state.active_failover_event:
                continue

            event = state.active_failover_event
            if event.completed_at:  # Ya completado
                continue

            try:
                # Ejecutar failover
                success = await self._perform_failover(event)

                # Actualizar evento
                event.completed_at = datetime.now()
                event.success = success

                if success:
                    self.failover_metrics['successful_failovers'] += 1
                    self.logger.info(f"✅ Failover completed: {event.from_component} -> {event.to_component}")
                else:
                    self.failover_metrics['failed_failovers'] += 1
                    self.logger.error(f"❌ Failover failed: {event.from_component} -> {event.to_component}")

                # Limpiar estado
                state.is_in_failover = False
                state.active_failover_event = None
                self.failover_metrics['active_failovers'] -= 1

                # Establecer cooldown
                state.cooldown_until = datetime.now() + timedelta(seconds=300)  # 5 minutos

            except Exception as e:
                self.logger.error(f"Error executing failover for {component_id}: {e}")

    async def _perform_failover(self, event: FailoverEvent) -> bool:
        """Ejecutar el failover real."""
        try:
            # Simular tiempo de failover
            await asyncio.sleep(random.uniform(5, 30))  # 5-30 segundos

            # En producción, aquí iría la lógica real:
            # - Actualizar DNS/routing
            # - Migrar conexiones activas
            # - Actualizar configuración
            # - Verificar que el componente de respaldo esté funcionando

            # Simular éxito/fracaso
            success = random.random() > 0.1  # 90% de éxito

            if success:
                # Actualizar referencias
                await self._update_component_references(event.from_component, event.to_component)

            return success

        except Exception as e:
            self.logger.error(f"Failover execution error: {e}")
            return False

    async def _select_backup_component(self, component_id: str, component_type: str) -> Optional[str]:
        """Seleccionar componente de respaldo."""
        state = self.failover_states.get(component_id)
        if not state or not state.backup_components:
            return None

        # Filtrar componentes disponibles
        available_backups = []
        for backup_id in state.backup_components:
            if component_type == 'region':
                if backup_id in self.regions_info:
                    # Verificar que no esté en failover
                    backup_state = self.failover_states.get(backup_id)
                    if not backup_state or not backup_state.is_in_failover:
                        available_backups.append(backup_id)
            else:  # endpoint
                if backup_id in self.endpoints_info:
                    backup_state = self.failover_states.get(backup_id)
                    if not backup_state or not backup_state.is_in_failover:
                        available_backups.append(backup_id)

        if not available_backups:
            return None

        # Seleccionar el mejor (por ahora aleatorio)
        return random.choice(available_backups)

    async def _update_component_references(self, from_component: str, to_component: str):
        """Actualizar referencias al componente failover."""
        # En producción, actualizar:
        # - Load balancers
        # - DNS records
        # - Service discovery
        # - Configuration management
        pass

    async def _monitor_active_failovers(self):
        """Monitorear failovers activos."""
        for state in self.failover_states.values():
            if state.is_in_failover and state.active_failover_event:
                event = state.active_failover_event

                # Verificar tiempo transcurrido
                elapsed = (datetime.now() - event.started_at).total_seconds()

                if elapsed > self.failover_timeout_seconds:
                    self.logger.error(f"⏰ Failover timeout: {event.from_component}")
                    # Marcar como fallido
                    event.completed_at = datetime.now()
                    event.success = False
                    state.is_in_failover = False
                    state.active_failover_event = None
                    self.failover_metrics['active_failovers'] -= 1
                    self.failover_metrics['failed_failovers'] += 1

    async def _check_failover_timeouts(self):
        """Verificar timeouts de failover."""
        # Ya manejado en _monitor_active_failovers
        pass

    async def _attempt_recoveries(self):
        """Intentar recuperar componentes fallidos."""
        for component_id, state in self.failover_states.items():
            if state.is_in_failover:
                continue  # Aún en failover

            # Verificar si el componente original está saludable
            component_type = 'region' if component_id in self.regions_info else 'endpoint'
            health_score = await self._get_component_health_score(component_id, component_type)

            if health_score > 0.8:  # Umbral de recuperación
                # Intentar failback
                await self._execute_failback(component_id, component_type)

    async def _execute_failback(self, component_id: str, component_type: str):
        """Ejecutar failback al componente original."""
        # Encontrar componente actual (al que se hizo failover)
        current_component = None
        for event in reversed(self.failover_history):
            if (event.from_component == component_id and
                event.success and
                not event.rollback_at):
                current_component = event.to_component
                break

        if not current_component:
            return

        # Crear evento de failback
        event = FailoverEvent(
            event_id=f"failback_{component_id}_{int(time.time())}",
            component_type=component_type,
            component_id=current_component,  # Failback desde el backup
            failover_type='automatic',
            trigger_reason='Component recovered',
            from_component=current_component,
            to_component=component_id,
            started_at=datetime.now(),
            rollback_possible=False  # Es un failback
        )

        self.failover_history.append(event)
        self.logger.info(f"🔙 Executing failback: {current_component} -> {component_id}")

        # Ejecutar failback (similar al failover)
        success = await self._perform_failover(event)
        event.completed_at = datetime.now()
        event.success = success

        if success:
            self.logger.info(f"✅ Failback completed: {component_id} restored")
        else:
            self.logger.error(f"❌ Failback failed: {component_id} not restored")

    async def _get_component_health_score(self, component_id: str, component_type: str) -> float:
        """Obtener score de salud de un componente."""
        # En producción, consultar HealthChecker
        # Simulación
        return random.uniform(0.5, 1.0)

    async def _get_component_avg_latency(self, component_id: str, component_type: str) -> float:
        """Obtener latencia promedio de un componente."""
        # En producción, consultar LoadBalancerMonitor
        # Simulación
        return random.uniform(50, 2000)

    def _initialize_default_policies(self):
        """Inicializar políticas de failover por defecto."""
        self.failover_policies = {
            'critical_health': FailoverPolicy(
                policy_id='critical_health',
                trigger_condition='health_below_threshold',
                threshold_value=0.3,
                cooldown_period_seconds=300,
                max_failover_attempts=5,
                failover_strategy='automatic',
                notification_required=True
            ),
            'high_latency': FailoverPolicy(
                policy_id='high_latency',
                trigger_condition='latency_above_threshold',
                threshold_value=2000,  # 2 segundos
                cooldown_period_seconds=600,
                max_failover_attempts=3,
                failover_strategy='automatic',
                notification_required=False
            ),
            'emergency_manual': FailoverPolicy(
                policy_id='emergency_manual',
                trigger_condition='manual',
                threshold_value=0.0,
                cooldown_period_seconds=60,
                max_failover_attempts=10,
                failover_strategy='manual',
                notification_required=True
            )
        }

    def get_failover_status(self) -> Dict[str, Any]:
        """Obtener estado completo del failover."""
        active_failovers = [
            {
                'component_id': state.component_id,
                'event_id': state.active_failover_event.event_id if state.active_failover_event else None,
                'started_at': state.active_failover_event.started_at.isoformat() if state.active_failover_event else None,
                'reason': state.active_failover_event.trigger_reason if state.active_failover_event else None
            }
            for state in self.failover_states.values()
            if state.is_in_failover
        ]

        recent_events = [
            {
                'event_id': event.event_id,
                'component_id': event.component_id,
                'type': event.failover_type,
                'from_component': event.from_component,
                'to_component': event.to_component,
                'success': event.success,
                'started_at': event.started_at.isoformat(),
                'completed_at': event.completed_at.isoformat() if event.completed_at else None
            }
            for event in list(self.failover_history)[-20:]  # Últimos 20 eventos
        ]

        return {
            'is_running': self.is_running,
            'active_failovers': len(active_failovers),
            'total_failovers': self.failover_metrics['total_failovers'],
            'successful_failovers': self.failover_metrics['successful_failovers'],
            'failed_failovers': self.failover_metrics['failed_failovers'],
            'avg_failover_time_seconds': self.failover_metrics['avg_failover_time_seconds'],
            'policies': {
                pid: {
                    'enabled': policy.enabled,
                    'trigger_condition': policy.trigger_condition,
                    'threshold_value': policy.threshold_value
                }
                for pid, policy in self.failover_policies.items()
            },
            'active_failovers_detail': active_failovers,
            'recent_events': recent_events
        }