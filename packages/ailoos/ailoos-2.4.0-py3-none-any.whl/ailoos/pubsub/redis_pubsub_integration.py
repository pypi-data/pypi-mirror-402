"""
Redis PubSub Integration - Integración completa con Redis Pub/Sub
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Set
import redis.asyncio as redis

from .config import PubSubConfig

logger = logging.getLogger(__name__)


class RedisPubSubIntegration:
    """
    Integración completa con Redis Pub/Sub.
    Maneja conexiones, publicación y suscripción usando Redis.
    """

    def __init__(self, config: PubSubConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._connected = False
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establece conexión con Redis"""
        if self._connected:
            return

        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                max_connections=self.config.max_connections,
                decode_responses=True
            )

            # Verificar conexión
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self._connected = True

            logger.info(f"Conectado a Redis en {self.config.redis_host}:{self.config.redis_port}")

        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Cierra la conexión con Redis"""
        if not self._connected:
            return

        try:
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass

            if self.pubsub:
                await self.pubsub.close()

            if self.redis_client:
                await self.redis_client.close()

            self._connected = False
            logger.info("Desconectado de Redis")

        except Exception as e:
            logger.error(f"Error desconectando de Redis: {e}")

    async def publish(self, channel: str, message: Any) -> bool:
        """
        Publica un mensaje en un canal Redis

        Args:
            channel: Nombre del canal
            message: Mensaje a publicar (se serializa a JSON)

        Returns:
            True si se publicó correctamente
        """
        if not self._connected or not self.redis_client:
            raise RuntimeError("No conectado a Redis")

        try:
            # Serializar mensaje si es necesario
            if isinstance(message, (dict, list)):
                message_str = json.dumps(message)
            else:
                message_str = str(message)

            await self.redis_client.publish(channel, message_str)
            logger.debug(f"Mensaje publicado en canal {channel}")
            return True

        except Exception as e:
            logger.error(f"Error publicando en canal {channel}: {e}")
            return False

    async def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        """
        Suscribe a un canal Redis

        Args:
            channel: Nombre del canal
            callback: Función callback para procesar mensajes
        """
        if not self._connected or not self.pubsub:
            raise RuntimeError("No conectado a Redis")

        try:
            if channel not in self._subscriptions:
                self._subscriptions[channel] = set()

            self._subscriptions[channel].add(callback)

            # Suscribir al canal si es la primera suscripción
            if len(self._subscriptions[channel]) == 1:
                await self.pubsub.subscribe(channel)
                logger.info(f"Suscrito al canal {channel}")

            # Iniciar listener si no está corriendo
            if not self._listener_task or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._listen_messages())

        except Exception as e:
            logger.error(f"Error suscribiendo al canal {channel}: {e}")
            raise

    async def unsubscribe(self, channel: str, callback: Optional[Callable[[Any], None]] = None) -> None:
        """
        Cancela suscripción a un canal Redis

        Args:
            channel: Nombre del canal
            callback: Función callback específica (opcional)
        """
        if not self._connected or not self.pubsub:
            raise RuntimeError("No conectado a Redis")

        try:
            if channel not in self._subscriptions:
                return

            if callback:
                self._subscriptions[channel].discard(callback)
            else:
                self._subscriptions[channel].clear()

            # Desuscribir del canal si no hay más callbacks
            if not self._subscriptions[channel]:
                await self.pubsub.unsubscribe(channel)
                del self._subscriptions[channel]
                logger.info(f"Desuscrito del canal {channel}")

        except Exception as e:
            logger.error(f"Error desuscribiendo del canal {channel}: {e}")
            raise

    async def _listen_messages(self) -> None:
        """Escucha mensajes de los canales suscritos"""
        try:
            while self._connected and self.pubsub:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']

                    # Deserializar mensaje
                    try:
                        if isinstance(data, str):
                            parsed_data = json.loads(data)
                        else:
                            parsed_data = data
                    except json.JSONDecodeError:
                        parsed_data = data

                    # Llamar callbacks
                    if channel in self._subscriptions:
                        for callback in self._subscriptions[channel]:
                            try:
                                await callback(parsed_data)
                            except Exception as e:
                                logger.error(f"Error en callback para canal {channel}: {e}")

        except asyncio.CancelledError:
            logger.info("Listener de mensajes cancelado")
        except Exception as e:
            logger.error(f"Error en listener de mensajes: {e}")

    async def get_channels(self) -> list:
        """Obtiene lista de canales activos"""
        if not self._connected or not self.redis_client:
            return []

        try:
            channels = await self.redis_client.pubsub_channels()
            return [ch.decode() if isinstance(ch, bytes) else ch for ch in channels]
        except Exception as e:
            logger.error(f"Error obteniendo canales: {e}")
            return []

    async def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """Obtiene información de un canal"""
        if not self._connected or not self.redis_client:
            return {}

        try:
            info = await self.redis_client.pubsub_numsub(channel)
            return {
                "channel": channel,
                "subscribers": info.get(channel, 0) if info else 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del canal {channel}: {e}")
            return {}

    def is_connected(self) -> bool:
        """Verifica si está conectado a Redis"""
        return self._connected