"""
GlobalLoadBalancer - Balanceador principal con geo-routing inteligente
Coordina todos los componentes del sistema de balanceo global.
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import random
import math

from ...core.config import Config
from ...utils.logging import AiloosLogger
from .health_checker import HealthChecker
from .traffic_manager import TrafficManager
from .geo_router import GeoRouter
from .load_balancer_monitor import LoadBalancerMonitor
from .failover_manager import FailoverManager


@dataclass
class GlobalLoadBalancingConfig:
    """Configuración del sistema de balanceo global."""
    geo_routing_enabled: bool = True
    health_check_interval: float = 30.0  # segundos
    traffic_update_interval: float = 60.0  # segundos
    failover_detection_timeout: float = 300.0  # segundos
    max_regions_per_request: int = 3
    load_distribution_strategy: str = "adaptive"  # 'adaptive', 'round_robin', 'weighted'
    enable_predictive_scaling: bool = True
    predictive_window_minutes: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 300


@dataclass
class GlobalRequest:
    """Solicitud global con información geográfica."""
    request_id: str
    service_type: str  # 'inference', 'training', 'storage', 'cdn'
    client_location: Dict[str, float]  # {'lat': float, 'lng': float}
    priority: int = 1  # 1-10, higher = more important
    required_resources: Dict[str, Any] = field(default_factory=dict)
    max_latency_ms: int = 1000
    compliance_requirements: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GlobalRoutingDecision:
    """Decisión de routing global."""
    request_id: str
    selected_region: str
    selected_endpoint: str
    estimated_latency_ms: float
    confidence_score: float
    alternative_regions: List[str] = field(default_factory=list)
    routing_reason: str = ""
    geo_benefits: Dict[str, Any] = field(default_factory=dict)


class GlobalLoadBalancer:
    """
    Balanceador global principal que coordina geo-routing, health checks,
    gestión de tráfico y failover automático.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Configuración específica
        self.glb_config = GlobalLoadBalancingConfig()

        # Componentes del sistema
        self.health_checker = HealthChecker(config)
        self.traffic_manager = TrafficManager(config)
        self.geo_router = GeoRouter(config)
        self.monitor = LoadBalancerMonitor(config)
        self.failover_manager = FailoverManager(config)

        # Estado del sistema
        self.is_running = False
        self.regions: Dict[str, Dict[str, Any]] = {}  # region_id -> region_info
        self.endpoints: Dict[str, Dict[str, Any]] = {}  # endpoint_id -> endpoint_info

        # Cache de decisiones
        self.decision_cache: Dict[str, Tuple[GlobalRoutingDecision, datetime]] = {}
        self.cache_ttl_seconds = 300

        # Colas de procesamiento
        self.request_queue: asyncio.Queue[GlobalRequest] = asyncio.Queue()
        self.processing_requests: Dict[str, GlobalRequest] = {}

        # Métricas globales
        self.global_metrics: Dict[str, Any] = {
            'total_requests': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'avg_routing_latency': 0.0,
            'geo_distribution': defaultdict(int),
            'regional_health_scores': {},
            'traffic_patterns': defaultdict(list)
        }

        # Tareas en background
        self.routing_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.optimization_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar el sistema de balanceo global."""
        if self.is_running:
            self.logger.warning("Global Load Balancer already running")
            return

        self.is_running = True

        # Iniciar componentes
        await self.health_checker.start()
        await self.traffic_manager.start()
        await self.geo_router.start()
        await self.monitor.start()
        await self.failover_manager.start()

        # Iniciar tareas principales
        self.routing_task = asyncio.create_task(self._routing_loop())
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.optimization_task = asyncio.create_task(self._optimization_loop())

        self.logger.info("🌍 Global Load Balancer started")

    async def stop(self):
        """Detener el sistema de balanceo global."""
        self.is_running = False

        # Detener tareas
        if self.routing_task:
            self.routing_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.optimization_task:
            self.optimization_task.cancel()

        try:
            await asyncio.gather(
                self.routing_task, self.monitoring_task, self.optimization_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

        # Detener componentes
        await self.failover_manager.stop()
        await self.monitor.stop()
        await self.geo_router.stop()
        await self.traffic_manager.stop()
        await self.health_checker.stop()

        self.logger.info("🛑 Global Load Balancer stopped")

    async def register_region(self, region_id: str, region_info: Dict[str, Any]):
        """Registrar una nueva región."""
        self.regions[region_id] = {
            **region_info,
            'registered_at': datetime.now(),
            'health_score': 1.0,
            'active_endpoints': 0,
            'capacity': region_info.get('capacity', 100),
            'current_load': 0
        }

        # Registrar con componentes
        await self.health_checker.register_region(region_id, region_info)
        await self.traffic_manager.register_region(region_id, region_info)
        await self.geo_router.register_region(region_id, region_info)
        await self.failover_manager.register_region(region_id, region_info)

        self.logger.info(f"📍 Region {region_id} registered")

    async def register_endpoint(self, endpoint_id: str, region_id: str, endpoint_info: Dict[str, Any]):
        """Registrar un nuevo endpoint en una región."""
        if region_id not in self.regions:
            raise ValueError(f"Region {region_id} not registered")

        self.endpoints[endpoint_id] = {
            **endpoint_info,
            'region_id': region_id,
            'registered_at': datetime.now(),
            'health_score': 1.0,
            'active_connections': 0,
            'capacity': endpoint_info.get('capacity', 1000),
            'current_load': 0
        }

        # Actualizar región
        self.regions[region_id]['active_endpoints'] += 1

        # Registrar con componentes
        await self.health_checker.register_endpoint(endpoint_id, region_id, endpoint_info)
        await self.traffic_manager.register_endpoint(endpoint_id, region_id, endpoint_info)
        await self.failover_manager.register_endpoint(endpoint_id, region_id, endpoint_info)

        self.logger.info(f"🔗 Endpoint {endpoint_id} registered in region {region_id}")

    async def route_global_request(self, request: GlobalRequest) -> GlobalRoutingDecision:
        """Enrutar una solicitud global."""
        await self.request_queue.put(request)

        # Procesar inmediatamente para respuesta síncrona
        decision = await self._make_routing_decision(request)

        if decision.selected_endpoint:
            # Asignar a endpoint seleccionado
            await self._assign_request_to_endpoint(request, decision.selected_endpoint)

        return decision

    async def _make_routing_decision(self, request: GlobalRequest) -> GlobalRoutingDecision:
        """Tomar decisión de routing global."""
        try:
            # Verificar cache
            cache_key = self._generate_decision_cache_key(request)
            if cache_key in self.decision_cache:
                cached_decision, cache_time = self.decision_cache[cache_key]
                if (datetime.now() - cache_time) < timedelta(seconds=self.cache_ttl_seconds):
                    return cached_decision

            # Obtener estado actual de salud y tráfico
            healthy_regions = await self.health_checker.get_healthy_regions()
            traffic_distribution = await self.traffic_manager.get_traffic_distribution()

            if not healthy_regions:
                return GlobalRoutingDecision(
                    request_id=request.request_id,
                    selected_region="",
                    selected_endpoint="",
                    estimated_latency_ms=0.0,
                    confidence_score=0.0,
                    routing_reason="No healthy regions available"
                )

            # Aplicar geo-routing
            if self.glb_config.geo_routing_enabled:
                routing_result = await self.geo_router.route_request(
                    request, healthy_regions, traffic_distribution
                )
            else:
                # Fallback a selección simple
                routing_result = await self._simple_region_selection(request, healthy_regions)

            if not routing_result['selected_region']:
                return GlobalRoutingDecision(
                    request_id=request.request_id,
                    selected_region="",
                    selected_endpoint="",
                    estimated_latency_ms=0.0,
                    confidence_score=0.0,
                    routing_reason="No suitable region found"
                )

            selected_region = routing_result['selected_region']
            selected_endpoint = await self._select_endpoint_in_region(
                request, selected_region, routing_result
            )

            if not selected_endpoint:
                return GlobalRoutingDecision(
                    request_id=request.request_id,
                    selected_region=selected_region,
                    selected_endpoint="",
                    estimated_latency_ms=0.0,
                    confidence_score=0.0,
                    routing_reason="No healthy endpoints in selected region"
                )

            # Calcular latencia estimada
            estimated_latency = await self._estimate_latency(request, selected_region, selected_endpoint)

            # Encontrar alternativas
            alternative_regions = await self._find_alternative_regions(request, selected_region, healthy_regions)

            decision = GlobalRoutingDecision(
                request_id=request.request_id,
                selected_region=selected_region,
                selected_endpoint=selected_endpoint,
                estimated_latency_ms=estimated_latency,
                confidence_score=routing_result.get('confidence', 0.8),
                alternative_regions=alternative_regions,
                routing_reason=routing_result.get('reason', 'Geo-routing decision'),
                geo_benefits=routing_result.get('geo_benefits', {})
            )

            # Cachear decisión
            self.decision_cache[cache_key] = (decision, datetime.now())

            return decision

        except Exception as e:
            self.logger.error(f"Error making routing decision: {e}")
            return GlobalRoutingDecision(
                request_id=request.request_id,
                selected_region="",
                selected_endpoint="",
                estimated_latency_ms=0.0,
                confidence_score=0.0,
                routing_reason=f"Error: {str(e)}"
            )

    def _generate_decision_cache_key(self, request: GlobalRequest) -> str:
        """Generar clave de cache para decisiones."""
        key_components = [
            request.service_type,
            str(request.priority),
            f"{request.client_location['lat']:.2f},{request.client_location['lng']:.2f}",
            str(request.max_latency_ms),
            ','.join(sorted(request.compliance_requirements))
        ]
        return hashlib.md5('|'.join(key_components).encode()).hexdigest()

    async def _simple_region_selection(self, request: GlobalRequest, healthy_regions: List[str]) -> Dict[str, Any]:
        """Selección simple de región (fallback)."""
        # Seleccionar región más cercana geográficamente
        client_lat, client_lng = request.client_location['lat'], request.client_location['lng']

        best_region = None
        best_distance = float('inf')

        for region_id in healthy_regions:
            region_info = self.regions.get(region_id, {})
            region_lat = region_info.get('lat', 0)
            region_lng = region_info.get('lng', 0)

            distance = math.sqrt((client_lat - region_lat)**2 + (client_lng - region_lng)**2)

            if distance < best_distance:
                best_distance = distance
                best_region = region_id

        return {
            'selected_region': best_region,
            'confidence': 0.6,
            'reason': 'Simple geographic selection',
            'geo_benefits': {'latency_optimization': 'basic'}
        }

    async def _select_endpoint_in_region(self, request: GlobalRequest, region_id: str, routing_result: Dict[str, Any]) -> Optional[str]:
        """Seleccionar endpoint específico dentro de una región."""
        region_endpoints = [
            eid for eid, einfo in self.endpoints.items()
            if einfo['region_id'] == region_id
        ]

        if not region_endpoints:
            return None

        # Filtrar endpoints saludables
        healthy_endpoints = await self.health_checker.get_healthy_endpoints(region_id)

        if not healthy_endpoints:
            return None

        # Aplicar estrategia de distribución de carga
        if self.glb_config.load_distribution_strategy == 'adaptive':
            return await self._adaptive_endpoint_selection(request, healthy_endpoints)
        elif self.glb_config.load_distribution_strategy == 'weighted':
            return await self._weighted_endpoint_selection(healthy_endpoints)
        else:  # round_robin
            return await self._round_robin_endpoint_selection(healthy_endpoints)

    async def _adaptive_endpoint_selection(self, request: GlobalRequest, endpoints: List[str]) -> str:
        """Selección adaptativa de endpoint basada en múltiples métricas."""
        scores = {}

        for endpoint_id in endpoints:
            endpoint_info = self.endpoints[endpoint_id]

            # Score de carga actual (menos carga = mejor)
            load_score = 1.0 - (endpoint_info['current_load'] / endpoint_info['capacity'])

            # Score de salud
            health_score = endpoint_info['health_score']

            # Score de latencia (si disponible)
            latency_score = 1.0  # Placeholder

            # Score combinado
            final_score = (0.4 * load_score + 0.4 * health_score + 0.2 * latency_score)
            scores[endpoint_id] = final_score

        return max(scores.keys(), key=lambda x: scores[x])

    async def _weighted_endpoint_selection(self, endpoints: List[str]) -> str:
        """Selección por pesos basada en capacidad."""
        total_weight = sum(
            self.endpoints[eid]['capacity'] - self.endpoints[eid]['current_load']
            for eid in endpoints
        )

        if total_weight == 0:
            return random.choice(endpoints)

        pick = random.uniform(0, total_weight)
        current_weight = 0

        for endpoint_id in endpoints:
            endpoint_info = self.endpoints[endpoint_id]
            weight = endpoint_info['capacity'] - endpoint_info['current_load']
            current_weight += weight

            if current_weight >= pick:
                return endpoint_id

        return endpoints[-1]

    async def _round_robin_endpoint_selection(self, endpoints: List[str]) -> str:
        """Selección round-robin simple."""
        # Usar timestamp para round-robin determinístico
        index = int(time.time() * 1000) % len(endpoints)
        return endpoints[index]

    async def _estimate_latency(self, request: GlobalRequest, region_id: str, endpoint_id: str) -> float:
        """Estimar latencia para una ruta."""
        # Distancia geográfica básica
        client_lat, client_lng = request.client_location['lat'], request.client_location['lng']
        region_info = self.regions[region_id]
        region_lat = region_info.get('lat', 0)
        region_lng = region_info.get('lng', 0)

        # Distancia en grados (aproximada)
        distance_degrees = math.sqrt((client_lat - region_lat)**2 + (client_lng - region_lng)**2)

        # Convertir a latencia estimada (muy simplificada)
        # ~1ms por grado de distancia + latencia base
        base_latency = 50.0  # ms
        distance_latency = distance_degrees * 10.0  # ~10ms por grado

        return base_latency + distance_latency

    async def _find_alternative_regions(self, request: GlobalRequest, selected_region: str, healthy_regions: List[str]) -> List[str]:
        """Encontrar regiones alternativas."""
        alternatives = [r for r in healthy_regions if r != selected_region]

        # Ordenar por distancia geográfica
        client_lat, client_lng = request.client_location['lat'], request.client_location['lng']

        def distance_to_region(region_id: str) -> float:
            region_info = self.regions.get(region_id, {})
            region_lat = region_info.get('lat', 0)
            region_lng = region_info.get('lng', 0)
            return math.sqrt((client_lat - region_lat)**2 + (client_lng - region_lng)**2)

        alternatives.sort(key=distance_to_region)
        return alternatives[:2]  # Máximo 2 alternativas

    async def _assign_request_to_endpoint(self, request: GlobalRequest, endpoint_id: str):
        """Asignar solicitud a un endpoint."""
        self.processing_requests[request.request_id] = request

        # Actualizar métricas de carga
        endpoint_info = self.endpoints[endpoint_id]
        endpoint_info['current_load'] += 1
        endpoint_info['active_connections'] += 1

        region_id = endpoint_info['region_id']
        self.regions[region_id]['current_load'] += 1

        # Notificar a traffic manager
        await self.traffic_manager.record_request_routing(request, endpoint_id, region_id)

        self.logger.debug(f"📤 Request {request.request_id} assigned to endpoint {endpoint_id}")

    async def complete_request(self, request_id: str, success: bool = True, response_time_ms: float = 0.0):
        """Marcar solicitud como completada."""
        if request_id not in self.processing_requests:
            return

        request = self.processing_requests.pop(request_id)

        # Actualizar métricas globales
        self.global_metrics['total_requests'] += 1
        if success:
            self.global_metrics['successful_routes'] += 1
        else:
            self.global_metrics['failed_routes'] += 1

        # Actualizar latencia promedio
        if response_time_ms > 0:
            current_avg = self.global_metrics['avg_routing_latency']
            total_requests = self.global_metrics['total_requests']
            self.global_metrics['avg_routing_latency'] = (
                (current_avg * (total_requests - 1)) + response_time_ms
            ) / total_requests

        # Actualizar distribución geográfica
        region = None
        for endpoint_info in self.endpoints.values():
            if endpoint_info.get('current_load', 0) > 0:
                region = endpoint_info['region_id']
                break

        if region:
            self.global_metrics['geo_distribution'][region] += 1

        # Reducir carga en endpoint
        # Nota: En producción, esto debería hacerse con el endpoint específico
        for endpoint_info in self.endpoints.values():
            if endpoint_info['current_load'] > 0:
                endpoint_info['current_load'] -= 1
                endpoint_info['active_connections'] -= 1
                region_id = endpoint_info['region_id']
                self.regions[region_id]['current_load'] -= 1
                break

        # Notificar componentes
        await self.monitor.record_request_completion(request, success, response_time_ms)
        await self.traffic_manager.update_traffic_patterns(request, success)

    async def _routing_loop(self):
        """Bucle principal de routing."""
        while self.is_running:
            try:
                request = await self.request_queue.get()

                if request.request_id in self.processing_requests:
                    continue

                decision = await self._make_routing_decision(request)

                if decision.selected_endpoint:
                    await self._assign_request_to_endpoint(request, decision.selected_endpoint)

            except Exception as e:
                self.logger.error(f"Error in routing loop: {e}")
                await asyncio.sleep(1)

    async def _monitoring_loop(self):
        """Bucle de monitoreo continuo."""
        while self.is_running:
            try:
                # Actualizar métricas de salud
                await self.health_checker.perform_global_health_checks()

                # Actualizar patrones de tráfico
                await self.traffic_manager.update_traffic_analysis()

                # Verificar failovers necesarios
                await self.failover_manager.check_failover_conditions()

                # Recopilar métricas del monitor
                await self.monitor.collect_system_metrics()

                await asyncio.sleep(self.glb_config.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _optimization_loop(self):
        """Bucle de optimización continua."""
        while self.is_running:
            try:
                # Limpiar cache expirada
                await self._cleanup_decision_cache()

                # Optimizar distribución de carga
                await self._optimize_load_distribution()

                # Actualizar predicciones
                if self.glb_config.enable_predictive_scaling:
                    await self._update_predictive_scaling()

                await asyncio.sleep(300)  # Optimizar cada 5 minutos

            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_decision_cache(self):
        """Limpiar cache de decisiones expiradas."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.decision_cache.items()
            if (now - timestamp) > timedelta(seconds=self.cache_ttl_seconds)
        ]

        for key in expired_keys:
            del self.decision_cache[key]

        if expired_keys:
            self.logger.debug(f"🧹 Cleaned {len(expired_keys)} expired decision cache entries")

    async def _optimize_load_distribution(self):
        """Optimizar distribución de carga entre regiones."""
        # Analizar distribución actual
        current_distribution = {}
        for region_id, region_info in self.regions.items():
            capacity = region_info['capacity']
            current_load = region_info['current_load']
            utilization = current_load / capacity if capacity > 0 else 0
            current_distribution[region_id] = utilization

        # Identificar desbalances
        avg_utilization = sum(current_distribution.values()) / len(current_distribution)
        imbalances = {
            region: util - avg_utilization
            for region, util in current_distribution.items()
            if abs(util - avg_utilization) > 0.2  # 20% de desviación
        }

        if imbalances:
            self.logger.info(f"⚖️ Detected load imbalances: {imbalances}")
            # En producción, aquí se aplicarían ajustes de routing

    async def _update_predictive_scaling(self):
        """Actualizar escalado predictivo basado en patrones."""
        # Analizar patrones históricos
        traffic_patterns = self.global_metrics['traffic_patterns']

        if len(traffic_patterns) < 10:  # Necesitamos datos suficientes
            return

        # Predicción simple basada en promedio móvil
        recent_traffic = traffic_patterns[-10:]
        avg_traffic = sum(recent_traffic) / len(recent_traffic)

        # Predecir para la próxima ventana
        predicted_load = avg_traffic * 1.1  # 10% de crecimiento esperado

        # Aplicar escalado si es necesario
        total_capacity = sum(r['capacity'] for r in self.regions.values())
        if predicted_load > total_capacity * 0.8:  # 80% de capacidad
            self.logger.info("🔮 Predictive scaling triggered - high load expected")

    def get_global_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema global."""
        return {
            'is_running': self.is_running,
            'regions': len(self.regions),
            'endpoints': len(self.endpoints),
            'processing_requests': len(self.processing_requests),
            'queued_requests': self.request_queue.qsize(),
            'global_metrics': self.global_metrics,
            'cache_size': len(self.decision_cache),
            'health_status': self.health_checker.get_health_status(),
            'traffic_status': self.traffic_manager.get_traffic_status(),
            'failover_status': self.failover_manager.get_failover_status()
        }


# Instancia global
_global_load_balancer: Optional[GlobalLoadBalancer] = None

def get_global_load_balancer(config: Config = None) -> GlobalLoadBalancer:
    """Obtener instancia singleton del global load balancer."""
    global _global_load_balancer
    if _global_load_balancer is None:
        _global_load_balancer = GlobalLoadBalancer(config or Config())
    return _global_load_balancer