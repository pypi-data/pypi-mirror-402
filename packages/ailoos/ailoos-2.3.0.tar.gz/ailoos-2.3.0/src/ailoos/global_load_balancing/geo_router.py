"""
GeoRouter - Routing geográfico inteligente
Optimiza el routing basado en ubicación geográfica del cliente y capacidad de regiones.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import math

from ...core.config import Config
from ...utils.logging import AiloosLogger
from .global_load_balancer import GlobalRequest


@dataclass
class GeoRoutingRule:
    """Regla de routing geográfico."""
    rule_id: str
    priority: int
    conditions: Dict[str, Any]  # Condiciones para aplicar la regla
    actions: Dict[str, Any]  # Acciones a tomar
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0


@dataclass
class GeoLocation:
    """Información de ubicación geográfica."""
    lat: float
    lng: float
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None

    def distance_to(self, other: 'GeoLocation') -> float:
        """Calcular distancia en kilómetros a otra ubicación."""
        # Fórmula de Haversine
        R = 6371  # Radio de la Tierra en km

        lat1_rad = math.radians(self.lat)
        lng1_rad = math.radians(self.lng)
        lat2_rad = math.radians(other.lat)
        lng2_rad = math.radians(other.lng)

        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c


@dataclass
class RoutingMetrics:
    """Métricas de routing geográfico."""
    total_routes: int = 0
    successful_routes: int = 0
    avg_routing_time_ms: float = 0.0
    geo_hit_rate: float = 0.0  # Porcentaje de rutas que usaron geo-routing
    cross_border_routes: int = 0
    compliance_violations: int = 0


class GeoRouter:
    """
    Router geográfico inteligente que optimiza el routing basado en
    ubicación del cliente, capacidad regional y restricciones de compliance.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Información de regiones
        self.regions: Dict[str, Dict[str, Any]] = {}
        self.region_locations: Dict[str, GeoLocation] = {}

        # Reglas de routing
        self.routing_rules: List[GeoRoutingRule] = []
        self._initialize_default_rules()

        # Cache de distancias
        self.distance_cache: Dict[Tuple[str, str], float] = {}

        # Métricas
        self.metrics = RoutingMetrics()

        # Configuración
        self.max_routing_time_ms = 100
        self.geo_routing_enabled = True
        self.compliance_check_enabled = True

        # Tareas
        self.is_running = False
        self.optimization_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar el geo router."""
        if self.is_running:
            return

        self.is_running = True
        self.optimization_task = asyncio.create_task(self._optimization_loop())

        self.logger.info("🌍 Geo Router started")

    async def stop(self):
        """Detener el geo router."""
        self.is_running = False

        if self.optimization_task:
            self.optimization_task.cancel()

        try:
            await self.optimization_task
        except asyncio.CancelledError:
            pass

        self.logger.info("🛑 Geo Router stopped")

    async def register_region(self, region_id: str, region_info: Dict[str, Any]):
        """Registrar región con información geográfica."""
        self.regions[region_id] = region_info

        # Extraer ubicación geográfica
        location = GeoLocation(
            lat=region_info.get('lat', 0.0),
            lng=region_info.get('lng', 0.0),
            country=region_info.get('country'),
            region=region_info.get('region_name'),
            city=region_info.get('city'),
            timezone=region_info.get('timezone')
        )
        self.region_locations[region_id] = location

        self.logger.debug(f"📍 Region {region_id} registered at {location.lat:.2f}, {location.lng:.2f}")

    async def route_request(
        self,
        request: GlobalRequest,
        available_regions: List[str],
        traffic_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrutar solicitud basada en criterios geográficos.

        Returns:
            Dict con selected_region, confidence, reason, geo_benefits
        """
        start_time = time.time()

        try:
            if not self.geo_routing_enabled or not available_regions:
                return {
                    'selected_region': available_regions[0] if available_regions else None,
                    'confidence': 0.5,
                    'reason': 'Geo-routing disabled or no regions available',
                    'geo_benefits': {}
                }

            # Aplicar reglas de routing
            applicable_rules = await self._find_applicable_rules(request)

            if applicable_rules:
                # Usar regla de mayor prioridad
                rule = max(applicable_rules, key=lambda r: r.priority)
                result = await self._apply_routing_rule(rule, request, available_regions, traffic_distribution)
                rule.last_used = datetime.now()
                rule.usage_count += 1

                # Calcular tiempo de routing
                routing_time = (time.time() - start_time) * 1000
                self._update_routing_metrics(True, routing_time)

                return result

            # Routing por defecto basado en distancia
            result = await self._default_geo_routing(request, available_regions, traffic_distribution)

            routing_time = (time.time() - start_time) * 1000
            self._update_routing_metrics(True, routing_time)

            return result

        except Exception as e:
            self.logger.error(f"Error in geo routing: {e}")
            routing_time = (time.time() - start_time) * 1000
            self._update_routing_metrics(False, routing_time)

            # Fallback a selección aleatoria
            return {
                'selected_region': available_regions[0] if available_regions else None,
                'confidence': 0.1,
                'reason': f'Error: {str(e)}',
                'geo_benefits': {}
            }

    async def _find_applicable_rules(self, request: GlobalRequest) -> List[GeoRoutingRule]:
        """Encontrar reglas aplicables para la solicitud."""
        applicable = []

        for rule in self.routing_rules:
            if not rule.enabled:
                continue

            if await self._rule_matches_request(rule, request):
                applicable.append(rule)

        return applicable

    async def _rule_matches_request(self, rule: GeoRoutingRule, request: GlobalRequest) -> bool:
        """Verificar si una regla coincide con la solicitud."""
        conditions = rule.conditions

        # Verificar tipo de servicio
        if 'service_type' in conditions:
            if request.service_type not in conditions['service_type']:
                return False

        # Verificar ubicación geográfica
        if 'geo_zones' in conditions:
            client_zone = self._get_geo_zone(request.client_location['lat'], request.client_location['lng'])
            if client_zone not in conditions['geo_zones']:
                return False

        # Verificar prioridad
        if 'min_priority' in conditions:
            if request.priority < conditions['min_priority']:
                return False

        # Verificar compliance
        if 'compliance_requirements' in conditions:
            required_compliance = set(conditions['compliance_requirements'])
            request_compliance = set(request.compliance_requirements or [])
            if not required_compliance.issubset(request_compliance):
                return False

        # Verificar latencia máxima
        if 'max_latency_ms' in conditions:
            if request.max_latency_ms > conditions['max_latency_ms']:
                return False

        return True

    async def _apply_routing_rule(
        self,
        rule: GeoRoutingRule,
        request: GlobalRequest,
        available_regions: List[str],
        traffic_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aplicar regla de routing."""
        actions = rule.actions

        # Acción: seleccionar región específica
        if 'select_region' in actions:
            region = actions['select_region']
            if region in available_regions:
                return {
                    'selected_region': region,
                    'confidence': actions.get('confidence', 0.9),
                    'reason': f'Rule {rule.rule_id}: direct region selection',
                    'geo_benefits': actions.get('geo_benefits', {})
                }

        # Acción: seleccionar por distancia mínima
        if actions.get('strategy') == 'closest':
            return await self._select_closest_region(request, available_regions)

        # Acción: seleccionar por menor carga
        if actions.get('strategy') == 'least_loaded':
            return await self._select_least_loaded_region(available_regions, traffic_distribution)

        # Acción: balancear por compliance
        if actions.get('strategy') == 'compliance_balanced':
            return await self._select_compliance_balanced_region(request, available_regions)

        # Default: closest region
        return await self._select_closest_region(request, available_regions)

    async def _default_geo_routing(
        self,
        request: GlobalRequest,
        available_regions: List[str],
        traffic_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Routing geográfico por defecto."""
        # Estrategia: closest + load balancing
        closest_result = await self._select_closest_region(request, available_regions)

        if len(available_regions) == 1:
            return closest_result

        # Verificar si la región más cercana está sobrecargada
        selected_region = closest_result['selected_region']
        region_load = traffic_distribution.get('distribution', {}).get(selected_region, {}).get('percentage', 0)

        # Si la carga es > 70%, buscar alternativa
        if region_load > 70:
            alternative = await self._select_least_loaded_region(available_regions, traffic_distribution)
            if alternative['selected_region'] != selected_region:
                return {
                    'selected_region': alternative['selected_region'],
                    'confidence': 0.7,
                    'reason': 'Closest region overloaded, using least loaded alternative',
                    'geo_benefits': {'load_balancing': True, 'latency_compromise': True}
                }

        return closest_result

    async def _select_closest_region(self, request: GlobalRequest, available_regions: List[str]) -> Dict[str, Any]:
        """Seleccionar región más cercana geográficamente."""
        client_location = GeoLocation(
            lat=request.client_location['lat'],
            lng=request.client_location['lng']
        )

        best_region = None
        best_distance = float('inf')
        best_latency = float('inf')

        for region_id in available_regions:
            if region_id not in self.region_locations:
                continue

            region_location = self.region_locations[region_id]
            distance = client_location.distance_to(region_location)

            # Estimar latencia basada en distancia (muy simplificado)
            estimated_latency = distance * 0.5  # ~0.5ms por km

            if estimated_latency < best_latency:
                best_region = region_id
                best_distance = distance
                best_latency = estimated_latency

        if best_region:
            # Verificar si es cross-border
            is_cross_border = self._is_cross_border_routing(client_location, self.region_locations[best_region])

            geo_benefits = {
                'distance_km': best_distance,
                'estimated_latency_ms': best_latency,
                'cross_border': is_cross_border,
                'latency_optimization': True
            }

            if is_cross_border:
                self.metrics.cross_border_routes += 1

            return {
                'selected_region': best_region,
                'confidence': 0.8,
                'reason': f'Closest region: {best_distance:.1f}km, {best_latency:.1f}ms latency',
                'geo_benefits': geo_benefits
            }

        # Fallback
        return {
            'selected_region': available_regions[0],
            'confidence': 0.3,
            'reason': 'No location data available, using first available',
            'geo_benefits': {}
        }

    async def _select_least_loaded_region(self, available_regions: List[str], traffic_distribution: Dict[str, Any]) -> Dict[str, Any]:
        """Seleccionar región con menor carga."""
        distribution = traffic_distribution.get('distribution', {})

        best_region = None
        best_load = float('inf')

        for region_id in available_regions:
            load = distribution.get(region_id, {}).get('percentage', 50)  # Default 50%
            if load < best_load:
                best_region = region_id
                best_load = load

        return {
            'selected_region': best_region or available_regions[0],
            'confidence': 0.7,
            'reason': f'Least loaded region: {best_load:.1f}% utilization',
            'geo_benefits': {'load_balancing': True}
        }

    async def _select_compliance_balanced_region(self, request: GlobalRequest, available_regions: List[str]) -> Dict[str, Any]:
        """Seleccionar región balanceando compliance y proximidad."""
        client_location = GeoLocation(
            lat=request.client_location['lat'],
            lng=request.client_location['lng']
        )

        # Puntuación por región
        scores = {}

        for region_id in available_regions:
            region_info = self.regions.get(region_id, {})
            region_location = self.region_locations.get(region_id)

            if not region_location:
                scores[region_id] = 0
                continue

            # Score de distancia (0-50 puntos, menor distancia = mayor score)
            distance = client_location.distance_to(region_location)
            max_distance = 20000  # 20,000 km como máximo razonable
            distance_score = 50 * (1 - min(distance / max_distance, 1))

            # Score de compliance (0-30 puntos)
            compliance_score = self._calculate_compliance_score(request, region_info)

            # Score de capacidad (0-20 puntos)
            capacity_score = region_info.get('capacity_score', 10)  # Placeholder

            total_score = distance_score + compliance_score + capacity_score
            scores[region_id] = total_score

        # Seleccionar mejor score
        best_region = max(scores.keys(), key=lambda r: scores[r])

        return {
            'selected_region': best_region,
            'confidence': 0.75,
            'reason': f'Compliance-balanced selection: score {scores[best_region]:.1f}',
            'geo_benefits': {'compliance_optimized': True, 'balanced_approach': True}
        }

    def _calculate_compliance_score(self, request: GlobalRequest, region_info: Dict[str, Any]) -> float:
        """Calcular score de compliance para una región."""
        if not request.compliance_requirements:
            return 15  # Score neutral

        region_compliance = set(region_info.get('compliance_certifications', []))
        required_compliance = set(request.compliance_requirements)

        # Compliance cumplido
        satisfied = len(required_compliance & region_compliance)
        total_required = len(required_compliance)

        if total_required == 0:
            return 15

        compliance_ratio = satisfied / total_required
        return compliance_ratio * 30  # 0-30 puntos

    def _is_cross_border_routing(self, client_location: GeoLocation, region_location: GeoLocation) -> bool:
        """Determinar si el routing cruza fronteras."""
        # Simplificación: si países diferentes, es cross-border
        if client_location.country and region_location.country:
            return client_location.country != region_location.country
        return False

    def _get_geo_zone(self, lat: float, lng: float) -> str:
        """Obtener zona geográfica aproximada."""
        # Dividir el mundo en zonas de 10 grados
        lat_zone = int(lat // 10) * 10
        lng_zone = int(lng // 10) * 10

        ns = "N" if lat >= 0 else "S"
        ew = "E" if lng >= 0 else "W"

        return f"{abs(lat_zone)}{ns}_{abs(lng_zone)}{ew}"

    def _update_routing_metrics(self, success: bool, routing_time_ms: float):
        """Actualizar métricas de routing."""
        self.metrics.total_routes += 1
        if success:
            self.metrics.successful_routes += 1

        # Actualizar tiempo promedio
        current_avg = self.metrics.avg_routing_time_ms
        total_routes = self.metrics.total_routes
        self.metrics.avg_routing_time_ms = (
            (current_avg * (total_routes - 1)) + routing_time_ms
        ) / total_routes

    def _initialize_default_rules(self):
        """Inicializar reglas de routing por defecto."""
        # Regla 1: Alta prioridad -> routing más cercano
        self.routing_rules.append(GeoRoutingRule(
            rule_id="high_priority_closest",
            priority=10,
            conditions={
                'min_priority': 8,
                'service_type': ['inference', 'training']
            },
            actions={
                'strategy': 'closest',
                'confidence': 0.9,
                'geo_benefits': {'latency_priority': True}
            }
        ))

        # Regla 2: Datos sensibles -> compliance primero
        self.routing_rules.append(GeoRoutingRule(
            rule_id="sensitive_data_compliance",
            priority=9,
            conditions={
                'compliance_requirements': ['gdpr', 'hipaa', 'ccpa']
            },
            actions={
                'strategy': 'compliance_balanced',
                'confidence': 0.85,
                'geo_benefits': {'compliance_priority': True}
            }
        ))

        # Regla 3: Latencia crítica -> más cercano sin importar carga
        self.routing_rules.append(GeoRoutingRule(
            rule_id="latency_critical",
            priority=8,
            conditions={
                'max_latency_ms': 50
            },
            actions={
                'strategy': 'closest',
                'confidence': 0.95,
                'geo_benefits': {'latency_critical': True}
            }
        ))

        # Regla 4: Europa -> preferir regiones europeas
        self.routing_rules.append(GeoRoutingRule(
            rule_id="europe_preference",
            priority=5,
            conditions={
                'geo_zones': ['50N_0E', '40N_10E', '50N_10E', '40N_0E']
            },
            actions={
                'select_region': 'europe-west1',  # Placeholder
                'confidence': 0.8,
                'geo_benefits': {'regional_preference': True}
            }
        ))

    async def _optimization_loop(self):
        """Bucle de optimización de reglas de routing."""
        while self.is_running:
            try:
                await self._optimize_routing_rules()
                await asyncio.sleep(600)  # Optimizar cada 10 minutos

            except Exception as e:
                self.logger.error(f"Error in routing optimization: {e}")
                await asyncio.sleep(300)

    async def _optimize_routing_rules(self):
        """Optimizar reglas de routing basadas en métricas."""
        # Deshabilitar reglas poco usadas
        for rule in self.routing_rules:
            if rule.usage_count == 0 and (datetime.now() - rule.created_at) > timedelta(hours=1):
                rule.enabled = False
                self.logger.debug(f"Disabled unused rule: {rule.rule_id}")

        # Ajustar prioridades basadas en efectividad
        # (Lógica simplificada)

        # Limpiar cache de distancias antiguas
        if len(self.distance_cache) > 1000:
            # Mantener solo las más recientes (simplificado)
            self.distance_cache.clear()

    def get_routing_status(self) -> Dict[str, Any]:
        """Obtener estado del geo router."""
        return {
            'regions_registered': len(self.regions),
            'routing_rules': len([r for r in self.routing_rules if r.enabled]),
            'metrics': {
                'total_routes': self.metrics.total_routes,
                'successful_routes': self.metrics.successful_routes,
                'avg_routing_time_ms': self.metrics.avg_routing_time_ms,
                'geo_hit_rate': self.metrics.geo_hit_rate,
                'cross_border_routes': self.metrics.cross_border_routes,
                'compliance_violations': self.metrics.compliance_violations
            },
            'rules': [
                {
                    'id': rule.rule_id,
                    'priority': rule.priority,
                    'enabled': rule.enabled,
                    'usage_count': rule.usage_count,
                    'last_used': rule.last_used.isoformat() if rule.last_used else None
                }
                for rule in self.routing_rules
            ]
        }