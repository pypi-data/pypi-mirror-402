"""
Message Broker - Broker de mensajes avanzado
"""

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from .topic_manager import TopicManager
from .redis_pubsub_integration import RedisPubSubIntegration

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Representa una suscripción"""
    id: str
    topic: str
    callback: Callable[[Any, Dict[str, Any]], None]
    subscriber_id: Optional[str] = None
    active: bool = True
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class MessageBroker:
    """
    Broker de mensajes avanzado.
    Maneja el enrutamiento de mensajes entre publishers y subscribers.
    """

    def __init__(self, topic_manager: TopicManager, redis_integration: RedisPubSubIntegration):
        self.topic_manager = topic_manager
        self.redis_integration = redis_integration
        self._subscriptions: Dict[str, Subscription] = {}
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Inicia el message broker"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_messages())
        logger.info("MessageBroker iniciado")

    async def stop(self) -> None:
        """Detiene el message broker"""
        if not self._running:
            return

        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Limpiar suscripciones
        for sub_id in list(self._subscriptions.keys()):
            await self.unsubscribe(sub_id)

        logger.info("MessageBroker detenido")

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
            raise RuntimeError("MessageBroker no está ejecutándose")

        try:
            # Actualizar estadísticas del topic
            await self.topic_manager.record_publish(topic)

            # Publicar en Redis
            success = await self.redis_integration.publish(topic, message)

            if success:
                # Enviar a subscribers locales
                await self._deliver_to_local_subscribers(topic, message, metadata or {})

            return success

        except Exception as e:
            logger.error(f"Error publicando mensaje en topic {topic}: {e}")
            return False

    async def subscribe(self, topic: str, callback: Callable[[Any, Dict[str, Any]], None],
                       subscriber_id: Optional[str] = None) -> str:
        """
        Suscribe a un topic

        Args:
            topic: Nombre del topic
            callback: Función callback
            subscriber_id: ID del suscriptor

        Returns:
            ID de la suscripción
        """
        if not self._running:
            raise RuntimeError("MessageBroker no está ejecutándose")

        subscription_id = str(uuid.uuid4())

        subscription = Subscription(
            id=subscription_id,
            topic=topic,
            callback=callback,
            subscriber_id=subscriber_id
        )

        self._subscriptions[subscription_id] = subscription

        # Registrar en topic manager
        await self.topic_manager.add_subscription(topic, subscription_id)

        # Suscribir a Redis para mensajes remotos
        await self.redis_integration.subscribe(topic, lambda msg: self._handle_remote_message(topic, msg))

        logger.info(f"Suscripción creada: {subscription_id} para topic {topic}")
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Cancela una suscripción

        Args:
            subscription_id: ID de la suscripción

        Returns:
            True si se canceló correctamente
        """
        if subscription_id not in self._subscriptions:
            return False

        subscription = self._subscriptions[subscription_id]
        subscription.active = False

        # Remover del topic manager
        await self.topic_manager.remove_subscription(subscription.topic, subscription_id)

        # Si no hay más suscripciones locales al topic, desuscribir de Redis
        local_subs = [s for s in self._subscriptions.values()
                     if s.topic == subscription.topic and s.active and s.id != subscription_id]

        if not local_subs:
            await self.redis_integration.unsubscribe(subscription.topic)

        del self._subscriptions[subscription_id]

        logger.info(f"Suscripción cancelada: {subscription_id}")
        return True

    async def _deliver_to_local_subscribers(self, topic: str, message: Any, metadata: Dict[str, Any]) -> None:
        """Entrega mensaje a subscribers locales"""
        for subscription in self._subscriptions.values():
            if subscription.topic == topic and subscription.active:
                try:
                    # Ejecutar callback en task separada para no bloquear
                    asyncio.create_task(self._call_callback(subscription, message, metadata))
                except Exception as e:
                    logger.error(f"Error entregando mensaje a suscripción {subscription.id}: {e}")

    async def _call_callback(self, subscription: Subscription, message: Any, metadata: Dict[str, Any]) -> None:
        """Llama al callback de una suscripción"""
        try:
            await subscription.callback(message, metadata)
        except Exception as e:
            logger.error(f"Error en callback de suscripción {subscription.id}: {e}")

    async def _handle_remote_message(self, topic: str, message: Any) -> None:
        """Maneja mensajes recibidos desde Redis"""
        # Evitar loop infinito: no reenviar mensajes que ya vienen de Redis
        metadata = {"source": "redis"}
        await self._deliver_to_local_subscribers(topic, message, metadata)

    async def _process_messages(self) -> None:
        """Procesa mensajes de la cola (para futuras extensiones)"""
        try:
            while self._running:
                try:
                    # Timeout para permitir cancelación
                    message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                    # Procesar mensaje aquí si es necesario
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error procesando mensaje de cola: {e}")
        except asyncio.CancelledError:
            logger.info("Procesador de mensajes cancelado")

    async def get_subscriptions(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene lista de suscripciones activas"""
        subscriptions = []
        for sub in self._subscriptions.values():
            if sub.active and (topic is None or sub.topic == topic):
                subscriptions.append({
                    "id": sub.id,
                    "topic": sub.topic,
                    "subscriber_id": sub.subscriber_id,
                    "created_at": sub.created_at
                })
        return subscriptions

    async def get_topic_subscribers(self, topic: str) -> List[str]:
        """Obtiene IDs de suscriptores de un topic"""
        return [sub.id for sub in self._subscriptions.values()
                if sub.topic == topic and sub.active]

    def is_running(self) -> bool:
        """Verifica si el broker está ejecutándose"""
        return self._running