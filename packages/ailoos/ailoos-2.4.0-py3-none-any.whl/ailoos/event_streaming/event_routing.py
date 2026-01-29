import asyncio
import logging
import random
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class RoutingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    TYPE_BASED = "type_based"
    PRIORITY_BASED = "priority_based"
    SIZE_BASED = "size_based"

class EventRouting:
    """
    Routing inteligente de eventos entre diferentes streams.
    Decide automáticamente si enviar eventos a Kafka o Redis Streams
    basado en reglas configurables.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.routing_rules = config.get('routing_rules', [])
        self.default_strategy = RoutingStrategy(config.get('default_strategy', 'round_robin'))
        self.round_robin_index = 0
        self.stream_load = {'kafka': 0, 'redis': 0}  # Conteo simple de carga
        self.type_mappings = config.get('type_mappings', {})  # tipo -> stream
        self.priority_thresholds = config.get('priority_thresholds', {'high': 'kafka', 'low': 'redis'})

    async def start(self):
        """Inicia el sistema de routing."""
        if self.running:
            return
        self.running = True
        logger.info("EventRouting iniciado")

    async def stop(self):
        """Detiene el sistema de routing."""
        self.running = False
        logger.info("EventRouting detenido")

    async def route_event(self, event: Dict[str, Any], preferred_stream: Optional[str] = None) -> str:
        """
        Determina el stream apropiado para un evento.

        Args:
            event: El evento a rutear
            preferred_stream: Stream preferido (opcional)

        Returns:
            'kafka' o 'redis'
        """
        if not self.running:
            return preferred_stream or 'kafka'

        try:
            # Aplicar reglas de routing personalizadas
            for rule in self.routing_rules:
                if await self._matches_rule(event, rule):
                    return rule.get('target_stream', 'kafka')

            # Routing basado en tipo de evento
            event_type = event.get('type')
            if event_type in self.type_mappings:
                return self.type_mappings[event_type]

            # Routing basado en prioridad
            priority = event.get('priority', 'medium')
            if priority in self.priority_thresholds:
                return self.priority_thresholds[priority]

            # Routing basado en tamaño (aproximado)
            event_size = self._estimate_event_size(event)
            if event_size > self.config.get('size_threshold_kb', 10) * 1024:
                return 'kafka'  # Eventos grandes a Kafka

            # Aplicar estrategia por defecto
            if self.default_strategy == RoutingStrategy.ROUND_ROBIN:
                return self._round_robin_route()
            elif self.default_strategy == RoutingStrategy.LOAD_BALANCED:
                return self._load_balanced_route()
            elif self.default_strategy == RoutingStrategy.TYPE_BASED:
                return self._type_based_route(event)
            elif self.default_strategy == RoutingStrategy.PRIORITY_BASED:
                return self._priority_based_route(event)
            elif self.default_strategy == RoutingStrategy.SIZE_BASED:
                return self._size_based_route(event)
            else:
                return preferred_stream or 'kafka'

        except Exception as e:
            logger.error(f"Error en routing de evento: {e}")
            return preferred_stream or 'kafka'

    async def _matches_rule(self, event: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Verifica si un evento cumple con una regla de routing."""
        try:
            conditions = rule.get('conditions', {})

            for key, expected_value in conditions.items():
                if key not in event:
                    return False

                actual_value = event[key]

                # Soporte para operadores
                if isinstance(expected_value, dict):
                    operator = expected_value.get('op', 'eq')
                    value = expected_value.get('value')

                    if operator == 'eq' and actual_value != value:
                        return False
                    elif operator == 'ne' and actual_value == value:
                        return False
                    elif operator == 'gt' and not (actual_value > value):
                        return False
                    elif operator == 'lt' and not (actual_value < value):
                        return False
                    elif operator == 'in' and actual_value not in value:
                        return False
                elif actual_value != expected_value:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error evaluando regla: {e}")
            return False

    def _round_robin_route(self) -> str:
        """Routing round-robin entre streams."""
        streams = ['kafka', 'redis']
        stream = streams[self.round_robin_index % len(streams)]
        self.round_robin_index += 1
        return stream

    def _load_balanced_route(self) -> str:
        """Routing basado en carga actual."""
        kafka_load = self.stream_load.get('kafka', 0)
        redis_load = self.stream_load.get('redis', 0)

        # Elegir el stream con menos carga
        if kafka_load <= redis_load:
            self.stream_load['kafka'] = kafka_load + 1
            return 'kafka'
        else:
            self.stream_load['redis'] = redis_load + 1
            return 'redis'

    def _type_based_route(self, event: Dict[str, Any]) -> str:
        """Routing basado en tipo de evento."""
        event_type = event.get('type', 'unknown')

        # Tipos de alta frecuencia a Redis (más rápido para lectura)
        high_frequency_types = {'metrics', 'logs', 'heartbeat'}
        if event_type in high_frequency_types:
            return 'redis'

        # Tipos críticos a Kafka (más durable)
        critical_types = {'alert', 'error', 'security'}
        if event_type in critical_types:
            return 'kafka'

        return 'kafka'  # Default

    def _priority_based_route(self, event: Dict[str, Any]) -> str:
        """Routing basado en prioridad."""
        priority = event.get('priority', 'medium')

        if priority in ['high', 'critical']:
            return 'kafka'  # Alta durabilidad
        elif priority in ['low']:
            return 'redis'  # Más rápido
        else:
            return 'kafka'

    def _size_based_route(self, event: Dict[str, Any]) -> str:
        """Routing basado en tamaño del evento."""
        size = self._estimate_event_size(event)

        if size > 50000:  # > 50KB
            return 'kafka'  # Mejor para eventos grandes
        else:
            return 'redis'

    def _estimate_event_size(self, event: Dict[str, Any]) -> int:
        """Estima el tamaño del evento en bytes."""
        try:
            import json
            return len(json.dumps(event).encode('utf-8'))
        except:
            return 1024  # Estimación por defecto

    def update_load(self, stream: str, load_change: int = -1):
        """Actualiza la carga de un stream."""
        if stream in self.stream_load:
            self.stream_load[stream] = max(0, self.stream_load[stream] + load_change)

    def get_routing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de routing."""
        return {
            'current_load': self.stream_load.copy(),
            'routing_rules_count': len(self.routing_rules),
            'type_mappings_count': len(self.type_mappings),
            'default_strategy': self.default_strategy.value
        }