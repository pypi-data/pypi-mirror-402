import asyncio
import json
import logging
from typing import Dict, Any, Callable, List, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisStreamsIntegration:
    """
    Integración completa con Redis Streams para streaming de eventos.
    Maneja publicación y consumo de eventos con soporte para múltiples streams.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6379)
        self.db = config.get('db', 0)
        self.redis_client = None
        self.subscriptions = {}  # stream -> callback
        self.last_ids = {}  # stream -> last_id
        self.running = False
        self.stats = {
            'messages_published': 0,
            'messages_consumed': 0,
            'errors': 0
        }

    async def start(self):
        """Inicia la integración con Redis Streams."""
        if self.running:
            return

        logger.info("Iniciando RedisStreamsIntegration")
        self.running = True

        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )

        # Verificar conexión
        try:
            await self.redis_client.ping()
            logger.info("Conexión a Redis establecida")
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            raise

        logger.info("RedisStreamsIntegration iniciado correctamente")

    async def stop(self):
        """Detiene la integración con Redis Streams."""
        if not self.running:
            return

        logger.info("Deteniendo RedisStreamsIntegration")
        self.running = False

        if self.redis_client:
            await self.redis_client.close()

        logger.info("RedisStreamsIntegration detenido")

    async def publish_event(self, event: Dict[str, Any], stream: str = 'events') -> bool:
        """Publica un evento en un stream de Redis."""
        if not self.redis_client:
            logger.error("Cliente Redis no inicializado")
            return False

        try:
            event_data = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in event.items()}
            message_id = await self.redis_client.xadd(stream, event_data)
            self.stats['messages_published'] += 1
            logger.debug(f"Evento publicado en stream {stream} con ID {message_id}: {event}")
            return True
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error publicando evento: {e}")
            return False

    async def subscribe(self, stream: str, callback: Callable):
        """Suscribe a un stream específico."""
        self.subscriptions[stream] = callback
        self.last_ids[stream] = '0'  # Empezar desde el principio
        logger.info(f"Suscrito al stream: {stream}")

    async def consume_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Consume eventos de los streams suscritos."""
        if not self.redis_client or not self.subscriptions:
            return []

        try:
            streams = {}
            for stream in self.subscriptions.keys():
                streams[stream] = self.last_ids.get(stream, '0')

            if not streams:
                return []

            # Leer desde múltiples streams
            result = await self.redis_client.xread(streams, count=count, block=1000)

            events = []
            for stream_name, messages in result:
                for message_id, message_data in messages:
                    # Deserializar datos
                    event = {}
                    for k, v in message_data.items():
                        try:
                            event[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            event[k] = v

                    events.append(event)
                    self.stats['messages_consumed'] += 1

                    # Actualizar last_id
                    self.last_ids[stream_name] = message_id

                    # Llamar callback si existe
                    if stream_name in self.subscriptions:
                        try:
                            await self.subscriptions[stream_name](event)
                        except Exception as e:
                            logger.error(f"Error en callback para stream {stream_name}: {e}")

            return events
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error consumiendo eventos: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la integración Redis."""
        return {
            'messages_published': self.stats['messages_published'],
            'messages_consumed': self.stats['messages_consumed'],
            'errors': self.stats['errors'],
            'subscriptions': list(self.subscriptions.keys()),
            'running': self.running
        }