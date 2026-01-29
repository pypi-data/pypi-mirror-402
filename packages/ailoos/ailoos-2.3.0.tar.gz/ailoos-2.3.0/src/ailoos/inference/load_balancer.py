"""
LoadBalancer - Balanceo de carga inteligente para modelos EmpoorioLM
Distribuye requests entre instancias basado en métricas de rendimiento.
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceo de carga."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    IP_HASH = "ip_hash"
    ADAPTIVE = "adaptive"


class InstanceStatus(Enum):
    """Estados de instancia."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"


@dataclass
class InstanceMetrics:
    """Métricas de una instancia."""
    instance_id: str
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: Optional[float] = None
    last_health_check: float = 0.0
    consecutive_failures: int = 0

    # Historial de tiempos de respuesta (últimos 100)
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))

    def update_response_time(self, response_time: float) -> None:
        """Actualizar tiempo de respuesta."""
        self.response_times.append(response_time)
        self.avg_response_time = statistics.mean(self.response_times) if self.response_times else 0.0

    def get_success_rate(self) -> float:
        """Obtener tasa de éxito."""
        total = self.total_requests
        return self.successful_requests / total if total > 0 else 1.0

    def is_overloaded(self, max_connections: int = 100, max_cpu: float = 90.0) -> bool:
        """Verificar si la instancia está sobrecargada."""
        return (
            self.active_connections >= max_connections or
            self.cpu_usage >= max_cpu or
            self.memory_usage >= 95.0
        )


@dataclass
class LoadBalancerConfig:
    """Configuración del load balancer."""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE
    health_check_interval: float = 30.0  # segundos
    max_connections_per_instance: int = 100
    max_cpu_usage: float = 90.0
    max_memory_usage: float = 95.0
    session_stickiness: bool = False
    stickiness_timeout: int = 300  # segundos
    circuit_breaker_threshold: int = 5  # fallos consecutivos
    circuit_breaker_timeout: int = 60  # segundos
    adaptive_update_interval: float = 10.0  # segundos

    # Configuración de failover
    enable_failover: bool = True
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 1.5


class LoadBalancer:
    """
    Load balancer inteligente para distribución de requests entre instancias de modelos.

    Características:
    - Múltiples estrategias de balanceo
    - Health checks automáticos
    - Circuit breaker pattern
    - Sesión stickiness
    - Métricas detalladas
    - Failover automático
    """

    def __init__(self, config: LoadBalancerConfig = None):
        self.config = config or LoadBalancerConfig()

        # Instancias registradas: model_id -> [instance_ids]
        self.model_instances: Dict[str, List[str]] = defaultdict(list)

        # Información de instancias: instance_id -> InstanceMetrics
        self.instance_metrics: Dict[str, InstanceMetrics] = {}

        # Instancias saludables por modelo
        self.healthy_instances: Dict[str, List[str]] = defaultdict(list)

        # Circuit breakers: instance_id -> (is_open, opened_at)
        self.circuit_breakers: Dict[str, Tuple[bool, float]] = {}

        # Sesiones sticky: session_id -> (instance_id, expires_at)
        self.sticky_sessions: Dict[str, Tuple[str, float]] = {}

        # Contadores para round-robin
        self.round_robin_counters: Dict[str, int] = defaultdict(int)

        # Callbacks
        self.on_instance_failure: Optional[Callable[[str], Awaitable[None]]] = None
        self.on_instance_recovery: Optional[Callable[[str], Awaitable[None]]] = None

        # Tareas en background
        self.health_check_task: Optional[asyncio.Task] = None
        self.adaptive_update_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Locks
        self._lock = asyncio.Lock()

        logger.info(f"⚖️ LoadBalancer inicializado con estrategia: {self.config.strategy.value}")

    async def register_instance(
        self,
        model_id: str,
        instance_id: str,
        initial_weight: int = 1
    ) -> None:
        """Registrar nueva instancia."""
        async with self._lock:
            if instance_id not in self.instance_metrics:
                self.instance_metrics[instance_id] = InstanceMetrics(instance_id=instance_id)

            if instance_id not in self.model_instances[model_id]:
                self.model_instances[model_id].append(instance_id)

            # Marcar como saludable inicialmente
            if instance_id not in self.healthy_instances[model_id]:
                self.healthy_instances[model_id].append(instance_id)

            logger.info(f"✅ Instancia {instance_id} registrada para modelo {model_id}")

    async def unregister_instance(self, model_id: str, instance_id: str) -> None:
        """Desregistrar instancia."""
        async with self._lock:
            if instance_id in self.model_instances[model_id]:
                self.model_instances[model_id].remove(instance_id)

            if instance_id in self.healthy_instances[model_id]:
                self.healthy_instances[model_id].remove(instance_id)

            # Limpiar sesiones sticky
            sessions_to_remove = [
                sid for sid, (inst_id, _) in self.sticky_sessions.items()
                if inst_id == instance_id
            ]
            for sid in sessions_to_remove:
                del self.sticky_sessions[sid]

            logger.info(f"❌ Instancia {instance_id} desregistrada de modelo {model_id}")

    async def select_instance(
        self,
        model_id: str,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Seleccionar instancia para servir request.

        Args:
            model_id: ID del modelo
            client_ip: IP del cliente (para IP hash)
            session_id: ID de sesión (para stickiness)

        Returns:
            ID de instancia seleccionada o None si no hay disponibles
        """
        async with self._lock:
            # Verificar sesiones sticky
            if self.config.session_stickiness and session_id:
                instance_id = self._get_sticky_instance(session_id)
                if instance_id and instance_id in self.healthy_instances.get(model_id, []):
                    return instance_id

            # Obtener instancias saludables
            healthy_instances = self.healthy_instances.get(model_id, [])
            if not healthy_instances:
                logger.warning(f"⚠️ No hay instancias saludables para modelo {model_id}")
                return None

            # Aplicar estrategia de selección
            selected_instance = await self._apply_load_balancing_strategy(
                model_id, healthy_instances, client_ip
            )

            # Configurar stickiness si está habilitada
            if self.config.session_stickiness and session_id and selected_instance:
                self.sticky_sessions[session_id] = (
                    selected_instance,
                    time.time() + self.config.stickiness_timeout
                )

            return selected_instance

    async def _apply_load_balancing_strategy(
        self,
        model_id: str,
        healthy_instances: List[str],
        client_ip: Optional[str]
    ) -> Optional[str]:
        """Aplicar estrategia de balanceo de carga."""
        if not healthy_instances:
            return None

        strategy = self.config.strategy

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(model_id, healthy_instances)

        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_instances)

        elif strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(healthy_instances)

        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_instances)

        elif strategy == LoadBalancingStrategy.IP_HASH and client_ip:
            return self._ip_hash_selection(client_ip, healthy_instances)

        elif strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._adaptive_selection(healthy_instances)

        else:
            # Default to round-robin
            return self._round_robin_selection(model_id, healthy_instances)

    def _round_robin_selection(self, model_id: str, instances: List[str]) -> str:
        """Selección round-robin."""
        counter = self.round_robin_counters[model_id]
        instance = instances[counter % len(instances)]
        self.round_robin_counters[model_id] = (counter + 1) % len(instances)
        return instance

    def _least_connections_selection(self, instances: List[str]) -> str:
        """Selección por menor número de conexiones."""
        return min(
            instances,
            key=lambda iid: self.instance_metrics[iid].active_connections
        )

    def _least_response_time_selection(self, instances: List[str]) -> str:
        """Selección por menor tiempo de respuesta."""
        return min(
            instances,
            key=lambda iid: self.instance_metrics[iid].avg_response_time
        )

    def _ip_hash_selection(self, client_ip: str, instances: List[str]) -> str:
        """Selección basada en hash de IP."""
        ip_hash = hash(client_ip) % len(instances)
        return instances[ip_hash]

    def _adaptive_selection(self, instances: List[str]) -> str:
        """Selección adaptativa basada en múltiples métricas."""
        if len(instances) == 1:
            return instances[0]

        # Calcular scores para cada instancia
        scores = {}
        for instance_id in instances:
            metrics = self.instance_metrics[instance_id]
            score = self._calculate_adaptive_score(metrics)
            scores[instance_id] = score

        # Seleccionar instancia con mejor score
        return max(scores.keys(), key=lambda iid: scores[iid])

    def _calculate_adaptive_score(self, metrics: InstanceMetrics) -> float:
        """Calcular score adaptativo para una instancia."""
        # Factores considerados:
        # - Menos conexiones = mejor (peso 0.4)
        # - Menor tiempo de respuesta = mejor (peso 0.3)
        # - Mayor tasa de éxito = mejor (peso 0.2)
        # - Menor uso de CPU = mejor (peso 0.1)

        connections_score = 1.0 / (1.0 + metrics.active_connections)
        response_time_score = 1.0 / (1.0 + metrics.avg_response_time / 1000)  # normalizar a segundos
        success_rate_score = metrics.get_success_rate()
        cpu_score = 1.0 - (metrics.cpu_usage / 100.0)

        return (
            0.4 * connections_score +
            0.3 * response_time_score +
            0.2 * success_rate_score +
            0.1 * cpu_score
        )

    def _get_sticky_instance(self, session_id: str) -> Optional[str]:
        """Obtener instancia sticky para una sesión."""
        if session_id in self.sticky_sessions:
            instance_id, expires_at = self.sticky_sessions[session_id]
            if time.time() < expires_at:
                return instance_id
            else:
                # Sesión expirada
                del self.sticky_sessions[session_id]
        return None

    async def update_instance_metrics(
        self,
        instance_id: str,
        response_time: Optional[float] = None,
        success: bool = True,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        gpu_usage: Optional[float] = None
    ) -> None:
        """Actualizar métricas de instancia."""
        async with self._lock:
            if instance_id not in self.instance_metrics:
                return

            metrics = self.instance_metrics[instance_id]

            # Actualizar contadores
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            # Actualizar tiempos de respuesta
            if response_time is not None:
                metrics.update_response_time(response_time)

            # Actualizar uso de recursos
            if cpu_usage is not None:
                metrics.cpu_usage = cpu_usage
            if memory_usage is not None:
                metrics.memory_usage = memory_usage
            if gpu_usage is not None:
                metrics.gpu_usage = gpu_usage

            # Verificar circuit breaker
            await self._check_circuit_breaker(instance_id, success)

    async def _check_circuit_breaker(self, instance_id: str, success: bool) -> None:
        """Verificar y actualizar circuit breaker."""
        metrics = self.instance_metrics[instance_id]

        if success:
            metrics.consecutive_failures = 0
            # Cerrar circuit breaker si estaba abierto
            if instance_id in self.circuit_breakers:
                is_open, opened_at = self.circuit_breakers[instance_id]
                if is_open and time.time() - opened_at > self.config.circuit_breaker_timeout:
                    del self.circuit_breakers[instance_id]
                    logger.info(f"🔄 Circuit breaker cerrado para instancia {instance_id}")
                    if self.on_instance_recovery:
                        await self.on_instance_recovery(instance_id)
        else:
            metrics.consecutive_failures += 1

            # Abrir circuit breaker si excede threshold
            if (metrics.consecutive_failures >= self.config.circuit_breaker_threshold and
                instance_id not in self.circuit_breakers):
                self.circuit_breakers[instance_id] = (True, time.time())
                logger.warning(f"⚡ Circuit breaker abierto para instancia {instance_id}")

                # Remover de instancias saludables
                for model_id, instances in self.healthy_instances.items():
                    if instance_id in instances:
                        instances.remove(instance_id)
                        logger.warning(f"🚫 Instancia {instance_id} removida de pool saludable de {model_id}")
                        if self.on_instance_failure:
                            await self.on_instance_failure(instance_id)
                        break

    async def perform_health_checks(self) -> None:
        """Realizar health checks en todas las instancias."""
        async with self._lock:
            for instance_id, metrics in self.instance_metrics.items():
                # Simular health check (en producción sería HTTP call)
                is_healthy = await self._perform_instance_health_check(instance_id)

                # Verificar circuit breaker timeout
                if instance_id in self.circuit_breakers:
                    is_open, opened_at = self.circuit_breakers[instance_id]
                    if is_open and time.time() - opened_at > self.config.circuit_breaker_timeout:
                        # Intentar cerrar circuit breaker
                        if is_healthy:
                            del self.circuit_breakers[instance_id]
                            logger.info(f"🔄 Circuit breaker cerrado para instancia {instance_id}")
                            if self.on_instance_recovery:
                                await self.on_instance_recovery(instance_id)
                        continue

                # Actualizar estado de salud
                was_healthy = any(
                    instance_id in instances
                    for instances in self.healthy_instances.values()
                )

                if is_healthy and not was_healthy:
                    # Instancia recuperada
                    for model_id, instances in self.model_instances.items():
                        if instance_id in instances:
                            if instance_id not in self.healthy_instances[model_id]:
                                self.healthy_instances[model_id].append(instance_id)
                            break
                    logger.info(f"💚 Instancia {instance_id} recuperada")

                elif not is_healthy and was_healthy:
                    # Instancia falló
                    for model_id, instances in self.healthy_instances.items():
                        if instance_id in instances:
                            instances.remove(instance_id)
                            break
                    logger.warning(f"💔 Instancia {instance_id} falló health check")

                metrics.last_health_check = time.time()

    async def _perform_instance_health_check(self, instance_id: str) -> bool:
        """Realizar health check en una instancia."""
        # Simulación de health check
        # En producción: HTTP GET /health a la instancia
        await asyncio.sleep(0.01)  # Simular latencia de red

        # Simular fallos aleatorios (5% de probabilidad)
        return random.random() > 0.05

    async def start_background_tasks(self) -> None:
        """Iniciar tareas en background."""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.adaptive_update_task = asyncio.create_task(self._adaptive_update_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("▶️ Tareas de background del LoadBalancer iniciadas")

    async def stop_background_tasks(self) -> None:
        """Detener tareas en background."""
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.adaptive_update_task:
            self.adaptive_update_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        await asyncio.gather(
            self.health_check_task or asyncio.sleep(0),
            self.adaptive_update_task or asyncio.sleep(0),
            self.cleanup_task or asyncio.sleep(0),
            return_exceptions=True
        )

        logger.info("⏹️ Tareas de background del LoadBalancer detenidas")

    async def _health_check_loop(self) -> None:
        """Bucle de health checks."""
        while True:
            try:
                await self.perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en health check loop: {e}")
                await asyncio.sleep(5)

    async def _adaptive_update_loop(self) -> None:
        """Bucle de actualización adaptativa."""
        while True:
            try:
                await asyncio.sleep(self.config.adaptive_update_interval)
                # Aquí se podrían actualizar pesos dinámicos, etc.
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en adaptive update loop: {e}")

    async def _cleanup_loop(self) -> None:
        """Bucle de limpieza de sesiones expiradas."""
        while True:
            try:
                await asyncio.sleep(60)  # Limpiar cada minuto

                current_time = time.time()
                expired_sessions = [
                    sid for sid, (_, expires_at) in self.sticky_sessions.items()
                    if current_time > expires_at
                ]

                for sid in expired_sessions:
                    del self.sticky_sessions[sid]

                if expired_sessions:
                    logger.debug(f"🧹 Limpiadas {len(expired_sessions)} sesiones sticky expiradas")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en cleanup loop: {e}")

    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del load balancer."""
        total_instances = len(self.instance_metrics)
        healthy_instances = sum(len(instances) for instances in self.healthy_instances.values())
        unhealthy_instances = total_instances - healthy_instances

        return {
            'total_instances': total_instances,
            'healthy_instances': healthy_instances,
            'unhealthy_instances': unhealthy_instances,
            'models_served': len(self.model_instances),
            'active_circuit_breakers': len(self.circuit_breakers),
            'sticky_sessions': len(self.sticky_sessions),
            'strategy': self.config.strategy.value,
            'session_stickiness': self.config.session_stickiness
        }

    def get_instance_stats(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de una instancia específica."""
        if instance_id not in self.instance_metrics:
            return None

        metrics = self.instance_metrics[instance_id]
        circuit_breaker_status = self.circuit_breakers.get(instance_id)

        return {
            'instance_id': instance_id,
            'active_connections': metrics.active_connections,
            'total_requests': metrics.total_requests,
            'success_rate': metrics.get_success_rate(),
            'avg_response_time': metrics.avg_response_time,
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage,
            'gpu_usage': metrics.gpu_usage,
            'circuit_breaker_open': circuit_breaker_status[0] if circuit_breaker_status else False,
            'consecutive_failures': metrics.consecutive_failures
        }