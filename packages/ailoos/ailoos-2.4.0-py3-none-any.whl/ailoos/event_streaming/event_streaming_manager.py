import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from .kafka_integration import KafkaIntegration
from .redis_streams_integration import RedisStreamsIntegration
from .event_processor import EventProcessor
from .stream_analytics import StreamAnalytics
from .event_routing import EventRouting

logger = logging.getLogger(__name__)

class EventStreamingManager:
    """
    Gestor principal de streaming de eventos para Ailoos.
    Coordina integraciones con Kafka, Redis Streams, procesamiento de eventos,
    analytics y routing inteligente.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kafka_integration = KafkaIntegration(config.get('kafka', {}))
        self.redis_integration = RedisStreamsIntegration(config.get('redis', {}))
        self.event_processor = EventProcessor(config.get('processor', {}))
        self.stream_analytics = StreamAnalytics(config.get('analytics', {}))
        self.event_routing = EventRouting(config.get('routing', {}))
        self.running = False
        self.tasks = []

    async def start(self):
        """Inicia el sistema de streaming de eventos."""
        if self.running:
            logger.warning("EventStreamingManager ya está ejecutándose")
            return

        logger.info("Iniciando EventStreamingManager")
        self.running = True

        # Iniciar integraciones
        await self.kafka_integration.start()
        await self.redis_integration.start()

        # Iniciar procesamiento y analytics
        await self.event_processor.start()
        await self.stream_analytics.start()
        await self.event_routing.start()

        # Crear tareas para procesamiento continuo
        self.tasks = [
            asyncio.create_task(self._process_kafka_events()),
            asyncio.create_task(self._process_redis_events()),
            asyncio.create_task(self._run_analytics()),
        ]

        logger.info("EventStreamingManager iniciado correctamente")

    async def stop(self):
        """Detiene el sistema de streaming de eventos."""
        if not self.running:
            return

        logger.info("Deteniendo EventStreamingManager")
        self.running = False

        # Cancelar tareas
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Detener componentes
        await self.event_routing.stop()
        await self.stream_analytics.stop()
        await self.event_processor.stop()
        await self.redis_integration.stop()
        await self.kafka_integration.stop()

        logger.info("EventStreamingManager detenido")

    async def publish_event(self, event: Dict[str, Any], stream_type: str = 'kafka') -> bool:
        """Publica un evento en el stream apropiado."""
        try:
            routed = await self.event_routing.route_event(event, stream_type)
            if routed == 'kafka':
                return await self.kafka_integration.publish_event(event)
            elif routed == 'redis':
                return await self.redis_integration.publish_event(event)
            else:
                logger.error(f"Tipo de stream no soportado: {routed}")
                return False
        except Exception as e:
            logger.error(f"Error publicando evento: {e}")
            return False

    async def subscribe_to_stream(self, stream_name: str, callback: Callable, stream_type: str = 'kafka'):
        """Suscribe a un stream específico."""
        if stream_type == 'kafka':
            await self.kafka_integration.subscribe(stream_name, callback)
        elif stream_type == 'redis':
            await self.redis_integration.subscribe(stream_name, callback)
        else:
            raise ValueError(f"Tipo de stream no soportado: {stream_type}")

    async def get_stream_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los streams."""
        kafka_stats = await self.kafka_integration.get_stats()
        redis_stats = await self.redis_integration.get_stats()
        analytics = await self.stream_analytics.get_current_metrics()
        return {
            'kafka': kafka_stats,
            'redis': redis_stats,
            'analytics': analytics
        }

    async def _process_kafka_events(self):
        """Procesa eventos de Kafka continuamente."""
        while self.running:
            try:
                events = await self.kafka_integration.consume_events()
                for event in events:
                    processed = await self.event_processor.process_event(event)
                    await self.stream_analytics.update_metrics(processed)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error procesando eventos Kafka: {e}")
                await asyncio.sleep(1)

    async def _process_redis_events(self):
        """Procesa eventos de Redis Streams continuamente."""
        while self.running:
            try:
                events = await self.redis_integration.consume_events()
                for event in events:
                    processed = await self.event_processor.process_event(event)
                    await self.stream_analytics.update_metrics(processed)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error procesando eventos Redis: {e}")
                await asyncio.sleep(1)

    async def _run_analytics(self):
        """Ejecuta analytics en tiempo real."""
        while self.running:
            try:
                await self.stream_analytics.run_real_time_analysis()
                await asyncio.sleep(5)  # Cada 5 segundos
            except Exception as e:
                logger.error(f"Error en analytics: {e}")
                await asyncio.sleep(1)