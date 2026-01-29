"""
TrafficManager - Gestión inteligente de tráfico
Analiza y gestiona patrones de tráfico para optimizar el routing global.
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
class TrafficPattern:
    """Patrón de tráfico identificado."""
    pattern_id: str
    service_type: str
    region: str
    time_window: str  # 'hour', 'day', 'week'
    avg_requests_per_minute: float
    peak_requests_per_minute: float
    geographic_distribution: Dict[str, float]  # region -> percentage
    temporal_distribution: Dict[str, float]  # hour -> percentage
    confidence_score: float
    last_updated: datetime


@dataclass
class TrafficPrediction:
    """Predicción de tráfico."""
    region: str
    service_type: str
    predicted_load: float
    confidence_interval: Tuple[float, float]
    time_horizon_minutes: int
    prediction_timestamp: datetime
    factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrafficAnomaly:
    """Anomalía detectada en el tráfico."""
    anomaly_id: str
    region: str
    service_type: str
    anomaly_type: str  # 'spike', 'drop', 'distribution_shift'
    severity: float  # 0.0 - 1.0
    detected_at: datetime
    description: str
    affected_components: List[str] = field(default_factory=list)


class TrafficManager:
    """
    Gestor inteligente de tráfico que analiza patrones, predice demanda
    y optimiza la distribución de carga global.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Estado del tráfico
        self.current_traffic: Dict[str, Dict[str, Any]] = defaultdict(dict)  # region -> service -> metrics
        self.historical_traffic: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))  # region -> traffic history

        # Patrones identificados
        self.traffic_patterns: Dict[str, TrafficPattern] = {}

        # Predicciones
        self.traffic_predictions: Dict[str, List[TrafficPrediction]] = defaultdict(list)

        # Anomalías detectadas
        self.active_anomalies: Dict[str, TrafficAnomaly] = {}

        # Métricas de tráfico
        self.traffic_metrics: Dict[str, Any] = {
            'total_requests': 0,
            'requests_by_region': defaultdict(int),
            'requests_by_service': defaultdict(int),
            'peak_traffic_regions': [],
            'traffic_distribution_entropy': 0.0,
            'anomalies_detected': 0,
            'predictions_accuracy': 0.0
        }

        # Configuración
        self.analysis_window_minutes = 60
        self.pattern_update_interval = 300  # 5 minutos
        self.prediction_horizon_minutes = 30
        self.anomaly_detection_sensitivity = 0.7

        # Tareas
        self.is_running = False
        self.analysis_task: Optional[asyncio.Task] = None
        self.pattern_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar el gestor de tráfico."""
        if self.is_running:
            return

        self.is_running = True
        self.analysis_task = asyncio.create_task(self._traffic_analysis_loop())
        self.pattern_task = asyncio.create_task(self._pattern_update_loop())

        self.logger.info("🚦 Traffic Manager started")

    async def stop(self):
        """Detener el gestor de tráfico."""
        self.is_running = False

        if self.analysis_task:
            self.analysis_task.cancel()
        if self.pattern_task:
            self.pattern_task.cancel()

        try:
            await asyncio.gather(self.analysis_task, self.pattern_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        self.logger.info("🛑 Traffic Manager stopped")

    async def register_region(self, region_id: str, region_info: Dict[str, Any]):
        """Registrar región para análisis de tráfico."""
        self.current_traffic[region_id] = {
            'total_requests': 0,
            'requests_by_service': defaultdict(int),
            'avg_response_time': 0.0,
            'error_rate': 0.0,
            'last_update': datetime.now()
        }
        self.logger.debug(f"📍 Region {region_id} registered for traffic analysis")

    async def register_endpoint(self, endpoint_id: str, region_id: str, endpoint_info: Dict[str, Any]):
        """Registrar endpoint para análisis de tráfico."""
        # Los endpoints se rastrean a través de sus regiones
        pass

    async def record_request_routing(self, request: GlobalRequest, endpoint_id: str, region_id: str):
        """Registrar routing de una solicitud."""
        # Actualizar métricas actuales
        region_traffic = self.current_traffic[region_id]
        region_traffic['total_requests'] += 1
        region_traffic['requests_by_service'][request.service_type] += 1
        region_traffic['last_update'] = datetime.now()

        # Actualizar métricas globales
        self.traffic_metrics['total_requests'] += 1
        self.traffic_metrics['requests_by_region'][region_id] += 1
        self.traffic_metrics['requests_by_service'][request.service_type] += 1

        # Registrar en historial
        traffic_record = {
            'timestamp': datetime.now(),
            'region': region_id,
            'service_type': request.service_type,
            'client_location': request.client_location,
            'endpoint_id': endpoint_id
        }
        self.historical_traffic[region_id].append(traffic_record)

    async def update_traffic_patterns(self, request: GlobalRequest, success: bool):
        """Actualizar patrones de tráfico basados en solicitud."""
        # Actualizar patrones basados en ubicación del cliente
        client_lat, client_lng = request.client_location['lat'], request.client_location['lng']

        # Identificar zona geográfica aproximada
        geo_zone = self._get_geo_zone(client_lat, client_lng)

        # Actualizar distribución geográfica
        # (Esto se haría en el análisis periódico)

    async def get_traffic_distribution(self) -> Dict[str, Any]:
        """Obtener distribución actual de tráfico."""
        total_requests = self.traffic_metrics['total_requests']
        if total_requests == 0:
            return {'distribution': {}, 'total': 0}

        distribution = {}
        for region_id, requests in self.traffic_metrics['requests_by_region'].items():
            distribution[region_id] = {
                'requests': requests,
                'percentage': (requests / total_requests) * 100,
                'current_load': self.current_traffic[region_id]['total_requests']
            }

        return {
            'distribution': distribution,
            'total': total_requests,
            'entropy': self._calculate_traffic_entropy(distribution),
            'peak_regions': self._identify_peak_regions(distribution)
        }

    async def update_traffic_analysis(self):
        """Actualizar análisis de tráfico."""
        await self._analyze_current_traffic()
        await self._detect_anomalies()
        await self._update_predictions()

    async def _traffic_analysis_loop(self):
        """Bucle de análisis de tráfico."""
        while self.is_running:
            try:
                await self.update_traffic_analysis()
                await asyncio.sleep(60)  # Análisis cada minuto

            except Exception as e:
                self.logger.error(f"Error in traffic analysis loop: {e}")
                await asyncio.sleep(30)

    async def _pattern_update_loop(self):
        """Bucle de actualización de patrones."""
        while self.is_running:
            try:
                await self._update_traffic_patterns()
                await self._cleanup_old_data()
                await asyncio.sleep(self.pattern_update_interval)

            except Exception as e:
                self.logger.error(f"Error in pattern update loop: {e}")
                await asyncio.sleep(60)

    async def _analyze_current_traffic(self):
        """Analizar tráfico actual."""
        # Calcular métricas por región
        for region_id, traffic_data in self.current_traffic.items():
            if not traffic_data['total_requests']:
                continue

            # Calcular tasa de requests por minuto
            time_since_last_update = (datetime.now() - traffic_data['last_update']).total_seconds() / 60
            if time_since_last_update > 0:
                requests_per_minute = traffic_data['total_requests'] / time_since_last_update
                traffic_data['requests_per_minute'] = requests_per_minute

            # Analizar distribución por servicio
            service_distribution = {}
            for service, count in traffic_data['requests_by_service'].items():
                service_distribution[service] = (count / traffic_data['total_requests']) * 100

            traffic_data['service_distribution'] = service_distribution

        # Actualizar métricas globales
        self.traffic_metrics['traffic_distribution_entropy'] = self._calculate_traffic_entropy(
            self.get_traffic_distribution_sync()
        )

    async def _detect_anomalies(self):
        """Detectar anomalías en el tráfico."""
        anomalies = []

        # Detectar spikes de tráfico
        for region_id, traffic_data in self.current_traffic.items():
            if 'requests_per_minute' not in traffic_data:
                continue

            current_rpm = traffic_data['requests_per_minute']

            # Calcular baseline del historial
            historical_rpm = []
            cutoff_time = datetime.now() - timedelta(hours=1)

            for record in self.historical_traffic[region_id]:
                if record['timestamp'] > cutoff_time:
                    # Estimar RPM histórico (simplificado)
                    historical_rpm.append(1)  # Placeholder

            if historical_rpm:
                baseline_rpm = statistics.mean(historical_rpm)
                std_dev = statistics.stdev(historical_rpm) if len(historical_rpm) > 1 else baseline_rpm * 0.1

                # Detectar spike
                if current_rpm > baseline_rpm + (std_dev * 3):
                    anomaly = TrafficAnomaly(
                        anomaly_id=f"spike_{region_id}_{int(time.time())}",
                        region=region_id,
                        service_type='all',
                        anomaly_type='spike',
                        severity=min(1.0, (current_rpm - baseline_rpm) / (baseline_rpm + std_dev)),
                        detected_at=datetime.now(),
                        description=f"Traffic spike detected: {current_rpm:.1f} RPM vs baseline {baseline_rpm:.1f} RPM"
                    )
                    anomalies.append(anomaly)

        # Registrar anomalías
        for anomaly in anomalies:
            self.active_anomalies[anomaly.anomaly_id] = anomaly
            self.traffic_metrics['anomalies_detected'] += 1
            self.logger.warning(f"🚨 Traffic anomaly detected: {anomaly.description}")

    async def _update_predictions(self):
        """Actualizar predicciones de tráfico."""
        # Predicción simple basada en tendencias recientes
        for region_id in self.current_traffic:
            if len(self.historical_traffic[region_id]) < 10:
                continue

            # Analizar tendencia de las últimas horas
            recent_records = list(self.historical_traffic[region_id])[-60:]  # Última hora

            if not recent_records:
                continue

            # Calcular tasa de crecimiento
            time_span = (recent_records[-1]['timestamp'] - recent_records[0]['timestamp']).total_seconds() / 3600
            if time_span > 0:
                requests_per_hour = len(recent_records) / time_span
                growth_rate = requests_per_hour * 0.1  # Asumir 10% de crecimiento

                prediction = TrafficPrediction(
                    region=region_id,
                    service_type='all',
                    predicted_load=requests_per_hour * (1 + growth_rate),
                    confidence_interval=(requests_per_hour * 0.8, requests_per_hour * 1.2),
                    time_horizon_minutes=self.prediction_horizon_minutes,
                    prediction_timestamp=datetime.now(),
                    factors={'growth_rate': growth_rate, 'historical_data_points': len(recent_records)}
                )

                # Mantener solo las predicciones más recientes
                self.traffic_predictions[region_id].append(prediction)
                if len(self.traffic_predictions[region_id]) > 10:
                    self.traffic_predictions[region_id] = self.traffic_predictions[region_id][-10:]

    async def _update_traffic_patterns(self):
        """Actualizar patrones de tráfico identificados."""
        # Analizar patrones por hora del día
        hourly_patterns = defaultdict(lambda: defaultdict(int))

        for region_id in self.current_traffic:
            for record in self.historical_traffic[region_id]:
                hour = record['timestamp'].hour
                hourly_patterns[region_id][hour] += 1

        # Crear patrones identificados
        for region_id, hour_counts in hourly_patterns.items():
            if not hour_counts:
                continue

            total_requests = sum(hour_counts.values())
            temporal_distribution = {
                f"{hour:02d}:00": (count / total_requests) * 100
                for hour, count in hour_counts.items()
            }

            pattern = TrafficPattern(
                pattern_id=f"hourly_{region_id}",
                service_type='all',
                region=region_id,
                time_window='day',
                avg_requests_per_minute=total_requests / (24 * 60),  # Promedio diario
                peak_requests_per_minute=max(hour_counts.values()) / 60,
                geographic_distribution={},  # Se calcularía con más datos
                temporal_distribution=temporal_distribution,
                confidence_score=0.8,  # Placeholder
                last_updated=datetime.now()
            )

            self.traffic_patterns[pattern.pattern_id] = pattern

    async def _cleanup_old_data(self):
        """Limpiar datos antiguos."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Limpiar historial antiguo
        for region_id in self.historical_traffic:
            while self.historical_traffic[region_id]:
                if self.historical_traffic[region_id][0]['timestamp'] < cutoff_time:
                    self.historical_traffic[region_id].popleft()
                else:
                    break

        # Limpiar anomalías antiguas
        old_anomalies = [
            aid for aid, anomaly in self.active_anomalies.items()
            if (datetime.now() - anomaly.detected_at) > timedelta(hours=1)
        ]
        for aid in old_anomalies:
            del self.active_anomalies[aid]

    def _calculate_traffic_entropy(self, distribution: Dict[str, Any]) -> float:
        """Calcular entropía de la distribución de tráfico."""
        if not distribution:
            return 0.0

        percentages = [data['percentage'] / 100 for data in distribution.values() if data['percentage'] > 0]

        if not percentages:
            return 0.0

        # Normalizar
        total = sum(percentages)
        probabilities = [p / total for p in percentages]

        # Calcular entropía
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def _identify_peak_regions(self, distribution: Dict[str, Any]) -> List[str]:
        """Identificar regiones con pico de tráfico."""
        if not distribution:
            return []

        # Encontrar percentil 75
        percentages = [data['percentage'] for data in distribution.values()]
        if not percentages:
            return []

        threshold = statistics.quantiles(percentages, n=4)[2]  # Q3

        peak_regions = [
            region_id for region_id, data in distribution.items()
            if data['percentage'] >= threshold
        ]

        return peak_regions

    def _get_geo_zone(self, lat: float, lng: float) -> str:
        """Obtener zona geográfica aproximada."""
        # Simplificación: dividir por hemisferios y meridianos
        if lat >= 0:
            ns = "N"
        else:
            ns = "S"

        if lng >= 0:
            ew = "E"
        else:
            ew = "W"

        return f"{abs(int(lat))}{ns}_{abs(int(lng))}{ew}"

    def get_traffic_distribution_sync(self) -> Dict[str, Any]:
        """Versión síncrona de get_traffic_distribution."""
        total_requests = self.traffic_metrics['total_requests']
        if total_requests == 0:
            return {}

        distribution = {}
        for region_id, requests in self.traffic_metrics['requests_by_region'].items():
            distribution[region_id] = {
                'requests': requests,
                'percentage': (requests / total_requests) * 100
            }

        return distribution

    def get_traffic_status(self) -> Dict[str, Any]:
        """Obtener estado completo del tráfico."""
        return {
            'current_traffic': dict(self.current_traffic),
            'traffic_metrics': dict(self.traffic_metrics),
            'active_anomalies': len(self.active_anomalies),
            'traffic_patterns': len(self.traffic_patterns),
            'predictions': {
                region: len(predictions)
                for region, predictions in self.traffic_predictions.items()
            },
            'anomalies': [
                {
                    'id': anomaly.anomaly_id,
                    'region': anomaly.region,
                    'type': anomaly.anomaly_type,
                    'severity': anomaly.severity,
                    'detected_at': anomaly.detected_at.isoformat(),
                    'description': anomaly.description
                }
                for anomaly in self.active_anomalies.values()
            ]
        }