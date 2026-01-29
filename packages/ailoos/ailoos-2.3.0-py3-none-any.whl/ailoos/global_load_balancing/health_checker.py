"""
HealthChecker - Sistema de health checks distribuido
Realiza verificaciones de salud en regiones y endpoints de manera distribuida.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import aiohttp
import random

from ...core.config import Config
from ...utils.logging import AiloosLogger


@dataclass
class HealthCheckConfig:
    """Configuración de health checks."""
    check_interval: float = 30.0  # segundos
    timeout: float = 10.0  # segundos
    max_consecutive_failures: int = 3
    recovery_attempts: int = 3
    health_score_decay: float = 0.1  # reducción por fallo
    health_score_recovery: float = 0.05  # recuperación por éxito
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 300.0  # segundos


@dataclass
class HealthStatus:
    """Estado de salud de un componente."""
    component_id: str
    is_healthy: bool
    health_score: float  # 0.0 - 1.0
    last_check: datetime
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0
    avg_response_time: float = 0.0
    circuit_breaker_open: bool = False
    circuit_breaker_opened_at: Optional[datetime] = None
    failure_reasons: List[str] = field(default_factory=list)


class HealthChecker:
    """
    Sistema distribuido de health checks que monitorea la salud
    de regiones y endpoints globales.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Configuración
        self.hc_config = HealthCheckConfig()

        # Estado de componentes
        self.region_health: Dict[str, HealthStatus] = {}
        self.endpoint_health: Dict[str, HealthStatus] = {}

        # Información de componentes
        self.regions_info: Dict[str, Dict[str, Any]] = {}
        self.endpoints_info: Dict[str, Dict[str, Any]] = {}

        # Circuit breakers
        self.circuit_breakers: Dict[str, Tuple[bool, datetime]] = {}

        # Tareas
        self.is_running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.recovery_task: Optional[asyncio.Task] = None

        # HTTP client para health checks
        self.http_session: Optional[aiohttp.ClientSession] = None

        # Métricas
        self.health_metrics: Dict[str, Any] = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'circuit_breakers_triggered': 0,
            'recoveries': 0,
            'avg_response_time': 0.0
        }

    async def start(self):
        """Iniciar el sistema de health checks."""
        if self.is_running:
            return

        self.is_running = True
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.hc_config.timeout)
        )

        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.recovery_task = asyncio.create_task(self._recovery_loop())

        self.logger.info("🏥 Health Checker started")

    async def stop(self):
        """Detener el sistema de health checks."""
        self.is_running = False

        if self.health_check_task:
            self.health_check_task.cancel()
        if self.recovery_task:
            self.recovery_task.cancel()

        try:
            await asyncio.gather(self.health_check_task, self.recovery_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        if self.http_session:
            await self.http_session.close()

        self.logger.info("🛑 Health Checker stopped")

    async def register_region(self, region_id: str, region_info: Dict[str, Any]):
        """Registrar una región para health checks."""
        self.regions_info[region_id] = region_info

        self.region_health[region_id] = HealthStatus(
            component_id=region_id,
            is_healthy=True,
            health_score=1.0,
            last_check=datetime.now()
        )

        self.logger.debug(f"📍 Region {region_id} registered for health checks")

    async def register_endpoint(self, endpoint_id: str, region_id: str, endpoint_info: Dict[str, Any]):
        """Registrar un endpoint para health checks."""
        self.endpoints_info[endpoint_id] = {
            **endpoint_info,
            'region_id': region_id
        }

        self.endpoint_health[endpoint_id] = HealthStatus(
            component_id=endpoint_id,
            is_healthy=True,
            health_score=1.0,
            last_check=datetime.now()
        )

        self.logger.debug(f"🔗 Endpoint {endpoint_id} registered for health checks")

    async def perform_global_health_checks(self):
        """Realizar health checks globales."""
        await self._check_all_regions()
        await self._check_all_endpoints()
        await self._update_health_scores()

    async def _health_check_loop(self):
        """Bucle principal de health checks."""
        while self.is_running:
            try:
                start_time = time.time()
                await self.perform_global_health_checks()
                duration = time.time() - start_time

                # Ajustar intervalo basado en carga
                sleep_time = max(5.0, self.hc_config.check_interval - duration)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def _recovery_loop(self):
        """Bucle de recuperación de componentes fallidos."""
        while self.is_running:
            try:
                await self._attempt_recoveries()
                await asyncio.sleep(60)  # Intentar recuperaciones cada minuto

            except Exception as e:
                self.logger.error(f"Error in recovery loop: {e}")
                await asyncio.sleep(30)

    async def _check_all_regions(self):
        """Verificar salud de todas las regiones."""
        if not self.regions_info:
            return

        tasks = []
        for region_id in self.regions_info:
            tasks.append(self._check_region_health(region_id))

        # Ejecutar en paralelo con límite de concurrencia
        semaphore = asyncio.Semaphore(10)  # Máximo 10 checks simultáneos

        async def check_with_semaphore(region_id):
            async with semaphore:
                return await self._check_region_health(region_id)

        results = await asyncio.gather(
            *[check_with_semaphore(rid) for rid in self.regions_info],
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Region health check error: {result}")

    async def _check_all_endpoints(self):
        """Verificar salud de todos los endpoints."""
        if not self.endpoints_info:
            return

        # Agrupar por región para checks más eficientes
        endpoints_by_region = defaultdict(list)
        for endpoint_id, endpoint_info in self.endpoints_info.items():
            region_id = endpoint_info['region_id']
            endpoints_by_region[region_id].append(endpoint_id)

        tasks = []
        for region_id, endpoint_ids in endpoints_by_region.items():
            tasks.append(self._check_region_endpoints(region_id, endpoint_ids))

        # Ejecutar con concurrencia limitada
        semaphore = asyncio.Semaphore(20)  # Más concurrencia para endpoints

        async def check_endpoints_with_semaphore(region_id, endpoint_ids):
            async with semaphore:
                return await self._check_region_endpoints(region_id, endpoint_ids)

        results = await asyncio.gather(
            *[check_endpoints_with_semaphore(rid, eids) for rid, eids in endpoints_by_region.items()],
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Endpoint health check error: {result}")

    async def _check_region_health(self, region_id: str) -> bool:
        """Verificar salud de una región."""
        region_info = self.regions_info.get(region_id)
        if not region_info:
            return False

        health_status = self.region_health[region_id]
        check_start = time.time()

        try:
            # Health check de región (puede ser un endpoint central o gateway)
            health_url = region_info.get('health_url')
            if health_url:
                is_healthy = await self._perform_http_health_check(health_url)
            else:
                # Simulación si no hay URL real
                is_healthy = await self._simulate_region_health_check(region_id)

            response_time = time.time() - check_start

            # Actualizar métricas
            await self._update_component_health(
                health_status, is_healthy, response_time, f"Region {region_id} check"
            )

            self.health_metrics['total_checks'] += 1
            if is_healthy:
                self.health_metrics['successful_checks'] += 1
            else:
                self.health_metrics['failed_checks'] += 1

            return is_healthy

        except Exception as e:
            self.logger.warning(f"Region health check failed for {region_id}: {e}")
            response_time = time.time() - check_start

            await self._update_component_health(
                health_status, False, response_time, f"Exception: {str(e)}"
            )

            self.health_metrics['total_checks'] += 1
            self.health_metrics['failed_checks'] += 1
            return False

    async def _check_region_endpoints(self, region_id: str, endpoint_ids: List[str]):
        """Verificar salud de endpoints en una región."""
        # Verificar si la región está saludable primero
        region_healthy = self.region_health.get(region_id)
        if region_healthy and not region_healthy.is_healthy:
            # Si la región está down, marcar todos los endpoints como sospechosos
            for endpoint_id in endpoint_ids:
                health_status = self.endpoint_health.get(endpoint_id)
                if health_status:
                    await self._update_component_health(
                        health_status, False, 0.0, f"Region {region_id} is unhealthy"
                    )
            return

        # Verificar endpoints individualmente
        tasks = [self._check_endpoint_health(eid) for eid in endpoint_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_endpoint_health(self, endpoint_id: str) -> bool:
        """Verificar salud de un endpoint específico."""
        endpoint_info = self.endpoints_info.get(endpoint_id)
        if not endpoint_info:
            return False

        health_status = self.endpoint_health[endpoint_id]
        check_start = time.time()

        try:
            # Health check del endpoint
            health_url = endpoint_info.get('health_url')
            if health_url:
                is_healthy = await self._perform_http_health_check(health_url)
            else:
                # Simulación
                is_healthy = await self._simulate_endpoint_health_check(endpoint_id)

            response_time = time.time() - check_start

            # Actualizar métricas
            await self._update_component_health(
                health_status, is_healthy, response_time, f"Endpoint {endpoint_id} check"
            )

            return is_healthy

        except Exception as e:
            self.logger.warning(f"Endpoint health check failed for {endpoint_id}: {e}")
            response_time = time.time() - check_start

            await self._update_component_health(
                health_status, False, response_time, f"Exception: {str(e)}"
            )
            return False

    async def _perform_http_health_check(self, url: str) -> bool:
        """Realizar health check HTTP."""
        if not self.http_session:
            return False

        try:
            async with self.http_session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def _simulate_region_health_check(self, region_id: str) -> bool:
        """Simular health check de región."""
        # Simulación con 95% de éxito
        await asyncio.sleep(0.01)  # Simular latencia de red
        return random.random() > 0.05

    async def _simulate_endpoint_health_check(self, endpoint_id: str) -> bool:
        """Simular health check de endpoint."""
        # Simulación con 90% de éxito
        await asyncio.sleep(0.005)  # Menor latencia
        return random.random() > 0.10

    async def _update_component_health(
        self,
        health_status: HealthStatus,
        is_healthy: bool,
        response_time: float,
        failure_reason: str = ""
    ):
        """Actualizar estado de salud de un componente."""
        health_status.total_checks += 1
        health_status.last_check = datetime.now()

        if is_healthy:
            health_status.successful_checks += 1
            health_status.consecutive_failures = 0

            # Recuperar health score
            health_status.health_score = min(
                1.0,
                health_status.health_score + self.hc_config.health_score_recovery
            )

            # Actualizar tiempo de respuesta promedio
            if health_status.avg_response_time == 0:
                health_status.avg_response_time = response_time
            else:
                health_status.avg_response_time = (
                    health_status.avg_response_time * 0.9 + response_time * 0.1
                )

        else:
            health_status.consecutive_failures += 1
            health_status.failure_reasons.append(failure_reason)

            # Reducir health score
            health_status.health_score = max(
                0.0,
                health_status.health_score - self.hc_config.health_score_decay
            )

            # Limitar lista de razones de fallo
            if len(health_status.failure_reasons) > 10:
                health_status.failure_reasons = health_status.failure_reasons[-10:]

        # Actualizar estado general
        was_healthy = health_status.is_healthy
        health_status.is_healthy = (
            health_status.consecutive_failures < self.hc_config.max_consecutive_failures and
            health_status.health_score > 0.3  # Umbral mínimo
        )

        # Gestionar circuit breaker
        await self._manage_circuit_breaker(health_status)

        # Logging de cambios de estado
        if was_healthy != health_status.is_healthy:
            if health_status.is_healthy:
                self.logger.info(f"💚 Component {health_status.component_id} recovered")
                self.health_metrics['recoveries'] += 1
            else:
                self.logger.warning(f"💔 Component {health_status.component_id} became unhealthy")

    async def _manage_circuit_breaker(self, health_status: HealthStatus):
        """Gestionar circuit breaker para un componente."""
        component_id = health_status.component_id

        if health_status.consecutive_failures >= self.hc_config.circuit_breaker_threshold:
            # Abrir circuit breaker
            if not health_status.circuit_breaker_open:
                health_status.circuit_breaker_open = True
                health_status.circuit_breaker_opened_at = datetime.now()
                self.circuit_breakers[component_id] = (True, datetime.now())
                self.logger.warning(f"⚡ Circuit breaker opened for {component_id}")
                self.health_metrics['circuit_breakers_triggered'] += 1

        elif health_status.circuit_breaker_open and health_status.is_healthy:
            # Cerrar circuit breaker si está saludable
            if component_id in self.circuit_breakers:
                is_open, opened_at = self.circuit_breakers[component_id]
                if is_open and (datetime.now() - opened_at) > timedelta(seconds=self.hc_config.circuit_breaker_timeout):
                    health_status.circuit_breaker_open = False
                    del self.circuit_breakers[component_id]
                    self.logger.info(f"🔄 Circuit breaker closed for {component_id}")

    async def _update_health_scores(self):
        """Actualizar scores de salud globales."""
        # Actualizar métricas de respuesta promedio global
        all_response_times = []

        for health_status in list(self.region_health.values()) + list(self.endpoint_health.values()):
            if health_status.avg_response_time > 0:
                all_response_times.append(health_status.avg_response_time)

        if all_response_times:
            self.health_metrics['avg_response_time'] = statistics.mean(all_response_times)

    async def _attempt_recoveries(self):
        """Intentar recuperar componentes fallidos."""
        recovery_candidates = []

        # Encontrar componentes que necesitan recuperación
        for component_id, health_status in list(self.region_health.items()) + list(self.endpoint_health.items()):
            if (not health_status.is_healthy and
                health_status.consecutive_failures < self.hc_config.recovery_attempts * 2):
                recovery_candidates.append(component_id)

        if not recovery_candidates:
            return

        self.logger.debug(f"🔄 Attempting recovery for {len(recovery_candidates)} components")

        # Intentar recuperación (en producción, esto podría incluir reinicios, etc.)
        for component_id in recovery_candidates[:5]:  # Limitar concurrencia
            try:
                # Simular intento de recuperación
                await asyncio.sleep(0.1)
                # En producción: enviar señales de recuperación, reiniciar servicios, etc.

            except Exception as e:
                self.logger.error(f"Recovery attempt failed for {component_id}: {e}")

    async def get_healthy_regions(self) -> List[str]:
        """Obtener lista de regiones saludables."""
        healthy = []
        for region_id, health_status in self.region_health.items():
            if (health_status.is_healthy and
                not health_status.circuit_breaker_open and
                health_status.health_score > 0.5):
                healthy.append(region_id)
        return healthy

    async def get_healthy_endpoints(self, region_id: str) -> List[str]:
        """Obtener lista de endpoints saludables en una región."""
        healthy = []
        for endpoint_id, health_status in self.endpoint_health.items():
            endpoint_info = self.endpoints_info.get(endpoint_id)
            if (endpoint_info and
                endpoint_info['region_id'] == region_id and
                health_status.is_healthy and
                not health_status.circuit_breaker_open and
                health_status.health_score > 0.5):
                healthy.append(endpoint_id)
        return healthy

    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado completo de salud."""
        return {
            'total_regions': len(self.region_health),
            'healthy_regions': len([r for r in self.region_health.values() if r.is_healthy]),
            'total_endpoints': len(self.endpoint_health),
            'healthy_endpoints': len([e for e in self.endpoint_health.values() if e.is_healthy]),
            'circuit_breakers_active': len(self.circuit_breakers),
            'health_metrics': self.health_metrics,
            'regions_health': {
                rid: {
                    'healthy': status.is_healthy,
                    'score': status.health_score,
                    'last_check': status.last_check.isoformat(),
                    'consecutive_failures': status.consecutive_failures
                }
                for rid, status in self.region_health.items()
            },
            'endpoints_health': {
                eid: {
                    'healthy': status.is_healthy,
                    'score': status.health_score,
                    'region': self.endpoints_info.get(eid, {}).get('region_id'),
                    'last_check': status.last_check.isoformat()
                }
                for eid, status in self.endpoint_health.items()
            }
        }