"""
PubSub Manager - Gestor principal del sistema de publicación-suscripción
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from .config import PubSubConfig
from .redis_pubsub_integration import RedisPubSubIntegration
from .message_broker import MessageBroker
from .topic_manager import TopicManager
from .message_processor import MessageProcessor
from .pubsub_monitoring import PubSubMonitoring

logger = logging.getLogger(__name__)


class PubSubManager:
    """
    Gestor principal del sistema PubSub.
    Coordina todos los componentes del sistema de publicación-suscripción.
    """

    def __init__(self, config: PubSubConfig):
        self.config = config
        self.redis_integration = RedisPubSubIntegration(config)
        self.topic_manager = TopicManager()
        self.message_broker = MessageBroker(self.topic_manager, self.redis_integration)
        self.message_processor = MessageProcessor()
        self.monitoring = PubSubMonitoring() if config.enable_monitoring else None

        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Inicia el sistema PubSub"""
        if self._running:
            return

        logger.info("Iniciando PubSubManager...")
        await self.redis_integration.connect()
        await self.message_broker.start()

        if self.monitoring:
            await self.monitoring.start()

        self._running = True
        logger.info("PubSubManager iniciado correctamente")

    async def stop(self) -> None:
        """Detiene el sistema PubSub"""
        if not self._running:
            return

        logger.info("Deteniendo PubSubManager...")
        self._running = False

        # Cancelar todas las tareas
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        await self.message_broker.stop()
        await self.redis_integration.disconnect()

        if self.monitoring:
            await self.monitoring.stop()

        logger.info("PubSubManager detenido correctamente")

    async def publish(self, topic: str, message: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publica un mensaje en un topic

        Args:
            topic: Nombre del topic
            message: Contenido del mensaje
            metadata: Metadatos adicionales

        Returns:
            True si se publicó correctamente
        """
        if not self._running:
            raise RuntimeError("PubSubManager no está ejecutándose")

        try:
            # Procesar el mensaje
            processed_message = await self.message_processor.process(message, metadata or {})

            # Publicar usando el broker
            success = await self.message_broker.publish(topic, processed_message)

            # Registrar métricas
            if self.monitoring:
                await self.monitoring.record_publish(topic, success)

            return success

        except Exception as e:
            logger.error(f"Error publicando mensaje en topic {topic}: {e}")
            if self.monitoring:
                await self.monitoring.record_error("publish", str(e))
            return False

    async def subscribe(self, topic: str, callback: Callable[[Any, Dict[str, Any]], None],
                       subscriber_id: Optional[str] = None) -> str:
        """
        Suscribe a un topic

        Args:
            topic: Nombre del topic
            callback: Función callback para procesar mensajes
            subscriber_id: ID del suscriptor (opcional)

        Returns:
            ID de la suscripción
        """
        if not self._running:
            raise RuntimeError("PubSubManager no está ejecutándose")

        try:
            subscription_id = await self.message_broker.subscribe(topic, callback, subscriber_id)

            # Registrar métricas
            if self.monitoring:
                await self.monitoring.record_subscribe(topic)

            return subscription_id

        except Exception as e:
            logger.error(f"Error suscribiendo a topic {topic}: {e}")
            if self.monitoring:
                await self.monitoring.record_error("subscribe", str(e))
            raise

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Cancela una suscripción

        Args:
            subscription_id: ID de la suscripción

        Returns:
            True si se canceló correctamente
        """
        if not self._running:
            raise RuntimeError("PubSubManager no está ejecutándose")

        try:
            success = await self.message_broker.unsubscribe(subscription_id)

            # Registrar métricas
            if self.monitoring:
                await self.monitoring.record_unsubscribe()

            return success

        except Exception as e:
            logger.error(f"Error cancelando suscripción {subscription_id}: {e}")
            if self.monitoring:
                await self.monitoring.record_error("unsubscribe", str(e))
            return False

    async def get_topic_stats(self, topic: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un topic"""
        if not self._running:
            raise RuntimeError("PubSubManager no está ejecutándose")

        stats = await self.topic_manager.get_topic_stats(topic)
        if self.monitoring:
            monitoring_stats = await self.monitoring.get_topic_stats(topic)
            stats.update(monitoring_stats)

        return stats

    async def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        if not self._running:
            raise RuntimeError("PubSubManager no está ejecutándose")

        stats = {
            "topics": await self.topic_manager.get_all_topics(),
            "running": self._running
        }

        if self.monitoring:
            stats["monitoring"] = await self.monitoring.get_system_stats()

        return stats

    def is_running(self) -> bool:
        """Verifica si el sistema está ejecutándose"""
        return self._running