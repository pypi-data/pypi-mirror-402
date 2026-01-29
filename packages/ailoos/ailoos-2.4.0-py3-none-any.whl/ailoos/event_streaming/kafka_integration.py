import asyncio
import json
import logging
from typing import Dict, Any, Callable, List, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

class KafkaIntegration:
    """
    Integración completa con Apache Kafka para streaming de eventos.
    Maneja productores y consumidores con soporte para múltiples topics.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bootstrap_servers = config.get('bootstrap_servers', ['localhost:9092'])
        self.producer = None
        self.consumer = None
        self.subscriptions = {}  # topic -> callback
        self.running = False
        self.stats = {
            'messages_published': 0,
            'messages_consumed': 0,
            'errors': 0
        }

    async def start(self):
        """Inicia la integración con Kafka."""
        if self.running:
            return

        logger.info("Iniciando KafkaIntegration")
        self.running = True

        # Crear productor
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )

        # Crear consumidor
        self.consumer = KafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id=self.config.get('group_id', 'ailoos_event_streaming')
        )

        logger.info("KafkaIntegration iniciado correctamente")

    async def stop(self):
        """Detiene la integración con Kafka."""
        if not self.running:
            return

        logger.info("Deteniendo KafkaIntegration")
        self.running = False

        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()

        logger.info("KafkaIntegration detenido")

    async def publish_event(self, event: Dict[str, Any], topic: str = 'events', key: Optional[str] = None) -> bool:
        """Publica un evento en un topic de Kafka."""
        if not self.producer:
            logger.error("Productor no inicializado")
            return False

        try:
            # Ejecutar en thread separado ya que kafka-python es síncrono
            future = asyncio.get_event_loop().run_in_executor(
                None,
                self.producer.send,
                topic,
                event,
                key
            )
            await future
            self.stats['messages_published'] += 1
            logger.debug(f"Evento publicado en topic {topic}: {event}")
            return True
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error publicando evento: {e}")
            return False

    async def subscribe(self, topic: str, callback: Callable):
        """Suscribe a un topic específico."""
        if not self.consumer:
            logger.error("Consumidor no inicializado")
            return

        self.subscriptions[topic] = callback
        self.consumer.subscribe([topic])
        logger.info(f"Suscrito al topic: {topic}")

    async def consume_events(self, timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        """Consume eventos de los topics suscritos."""
        if not self.consumer:
            return []

        try:
            # Ejecutar en thread separado
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                self.consumer.poll,
                timeout_ms
            )

            events = []
            for topic_partition, records in messages.items():
                for record in records:
                    event = record.value
                    events.append(event)
                    self.stats['messages_consumed'] += 1

                    # Llamar callback si existe
                    topic = topic_partition.topic
                    if topic in self.subscriptions:
                        try:
                            await self.subscriptions[topic](event)
                        except Exception as e:
                            logger.error(f"Error en callback para topic {topic}: {e}")

            return events
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error consumiendo eventos: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la integración Kafka."""
        return {
            'messages_published': self.stats['messages_published'],
            'messages_consumed': self.stats['messages_consumed'],
            'errors': self.stats['errors'],
            'subscriptions': list(self.subscriptions.keys()),
            'running': self.running
        }