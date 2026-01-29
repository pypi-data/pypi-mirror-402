"""
Topic Manager - Gestión de topics y suscripciones
"""

import asyncio
import logging
import time
from typing import Dict, List, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TopicStats:
    """Estadísticas de un topic"""
    name: str
    subscribers: Set[str] = field(default_factory=set)
    messages_published: int = 0
    messages_delivered: int = 0
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    @property
    def subscriber_count(self) -> int:
        return len(self.subscribers)


class TopicManager:
    """
    Gestión de topics y suscripciones.
    Mantiene estadísticas y metadatos de topics.
    """

    def __init__(self):
        self._topics: Dict[str, TopicStats] = {}
        self._lock = asyncio.Lock()

    async def add_subscription(self, topic: str, subscription_id: str) -> None:
        """
        Agrega una suscripción a un topic

        Args:
            topic: Nombre del topic
            subscription_id: ID de la suscripción
        """
        async with self._lock:
            if topic not in self._topics:
                self._topics[topic] = TopicStats(name=topic)

            self._topics[topic].subscribers.add(subscription_id)
            self._topics[topic].last_activity = time.time()

            logger.debug(f"Suscripción {subscription_id} agregada al topic {topic}")

    async def remove_subscription(self, topic: str, subscription_id: str) -> bool:
        """
        Remueve una suscripción de un topic

        Args:
            topic: Nombre del topic
            subscription_id: ID de la suscripción

        Returns:
            True si se removió correctamente
        """
        async with self._lock:
            if topic not in self._topics:
                return False

            if subscription_id in self._topics[topic].subscribers:
                self._topics[topic].subscribers.remove(subscription_id)
                self._topics[topic].last_activity = time.time()

                # Limpiar topic si no tiene suscriptores
                if not self._topics[topic].subscribers:
                    del self._topics[topic]

                logger.debug(f"Suscripción {subscription_id} removida del topic {topic}")
                return True

            return False

    async def record_publish(self, topic: str) -> None:
        """
        Registra una publicación en un topic

        Args:
            topic: Nombre del topic
        """
        async with self._lock:
            if topic not in self._topics:
                self._topics[topic] = TopicStats(name=topic)

            self._topics[topic].messages_published += 1
            self._topics[topic].last_activity = time.time()

    async def record_delivery(self, topic: str, count: int = 1) -> None:
        """
        Registra entregas de mensajes en un topic

        Args:
            topic: Nombre del topic
            count: Número de mensajes entregados
        """
        async with self._lock:
            if topic in self._topics:
                self._topics[topic].messages_delivered += count
                self._topics[topic].last_activity = time.time()

    async def get_topic_stats(self, topic: str) -> Dict[str, any]:
        """
        Obtiene estadísticas de un topic

        Args:
            topic: Nombre del topic

        Returns:
            Diccionario con estadísticas
        """
        async with self._lock:
            if topic not in self._topics:
                return {}

            stats = self._topics[topic]
            return {
                "name": stats.name,
                "subscriber_count": stats.subscriber_count,
                "messages_published": stats.messages_published,
                "messages_delivered": stats.messages_delivered,
                "created_at": stats.created_at,
                "last_activity": stats.last_activity,
                "subscribers": list(stats.subscribers)
            }

    async def get_all_topics(self) -> List[str]:
        """Obtiene lista de todos los topics activos"""
        async with self._lock:
            return list(self._topics.keys())

    async def get_topics_with_subscribers(self) -> List[str]:
        """Obtiene lista de topics que tienen suscriptores"""
        async with self._lock:
            return [topic for topic, stats in self._topics.items() if stats.subscriber_count > 0]

    async def get_topic_subscribers(self, topic: str) -> List[str]:
        """Obtiene lista de suscriptores de un topic"""
        async with self._lock:
            if topic not in self._topics:
                return []
            return list(self._topics[topic].subscribers)

    async def get_system_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas generales del sistema"""
        async with self._lock:
            total_topics = len(self._topics)
            total_subscribers = sum(len(stats.subscribers) for stats in self._topics.values())
            total_messages_published = sum(stats.messages_published for stats in self._topics.values())
            total_messages_delivered = sum(stats.messages_delivered for stats in self._topics.values())

            return {
                "total_topics": total_topics,
                "total_subscribers": total_subscribers,
                "total_messages_published": total_messages_published,
                "total_messages_delivered": total_messages_delivered,
                "topics": [await self.get_topic_stats(topic) for topic in self._topics.keys()]
            }

    async def cleanup_inactive_topics(self, max_age: float = 3600.0) -> int:
        """
        Limpia topics inactivos

        Args:
            max_age: Edad máxima en segundos para considerar inactivo

        Returns:
            Número de topics limpiados
        """
        async with self._lock:
            current_time = time.time()
            inactive_topics = []

            for topic, stats in self._topics.items():
                if (current_time - stats.last_activity) > max_age and stats.subscriber_count == 0:
                    inactive_topics.append(topic)

            for topic in inactive_topics:
                del self._topics[topic]

            if inactive_topics:
                logger.info(f"Limpiados {len(inactive_topics)} topics inactivos")

            return len(inactive_topics)

    async def get_most_active_topics(self, limit: int = 10) -> List[Dict[str, any]]:
        """Obtiene los topics más activos por mensajes publicados"""
        async with self._lock:
            sorted_topics = sorted(
                self._topics.items(),
                key=lambda x: x[1].messages_published,
                reverse=True
            )

            return [await self.get_topic_stats(topic) for topic, _ in sorted_topics[:limit]]

    async def get_topics_by_subscriber_count(self, limit: int = 10) -> List[Dict[str, any]]:
        """Obtiene los topics con más suscriptores"""
        async with self._lock:
            sorted_topics = sorted(
                self._topics.items(),
                key=lambda x: x[1].subscriber_count,
                reverse=True
            )

            return [await self.get_topic_stats(topic) for topic, _ in sorted_topics[:limit]]