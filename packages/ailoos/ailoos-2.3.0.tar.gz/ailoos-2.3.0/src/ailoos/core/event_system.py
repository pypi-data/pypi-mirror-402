"""
Sistema de eventos global para AILOOS.
Permite comunicación asíncrona entre componentes del sistema.
"""

import asyncio
import json
import os
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import weakref

from .config import get_config
from ..utils.logging import get_logger


class EventPriority(Enum):
    """Prioridades de eventos."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Evento del sistema."""
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    ttl_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "ttl_seconds": self.ttl_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(
            event_type=data["event_type"],
            data=data["data"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=EventPriority(data["priority"]),
            correlation_id=data.get("correlation_id"),
            ttl_seconds=data.get("ttl_seconds")
        )

    def is_expired(self) -> bool:
        """Verificar si el evento ha expirado."""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl_seconds


@dataclass
class EventHandler:
    """Handler de eventos."""
    handler_id: str
    event_types: List[str]
    callback: Callable[[Event], Awaitable[None]]
    priority: int = 0
    filter_func: Optional[Callable[[Event], bool]] = None

    def matches_event(self, event: Event) -> bool:
        """Verificar si este handler maneja el evento."""
        if event.event_type not in self.event_types:
            return False

        if self.filter_func and not self.filter_func(event):
            return False

        return True


class EventBus:
    """
    Bus de eventos centralizado para comunicación entre componentes.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()

        # Handlers registrados
        self.handlers: Dict[str, EventHandler] = {}
        self.handlers_lock = threading.RLock()

        # Cola de eventos
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.processing_active = False

        # Estadísticas
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0,
            "start_time": time.time()
        }

        self.logger.info("EventBus inicializado")

    async def start(self):
        """Iniciar procesamiento de eventos."""
        if self.processing_active:
            return

        self.processing_active = True
        self.processing_task = asyncio.create_task(self._process_events())
        self.logger.info("Procesamiento de eventos iniciado")

    async def stop(self):
        """Detener procesamiento de eventos."""
        self.processing_active = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Procesamiento de eventos detenido")

    def register_handler(self, handler_id: str, event_types: List[str],
                        callback: Callable[[Event], Awaitable[None]],
                        priority: int = 0,
                        filter_func: Optional[Callable[[Event], bool]] = None):
        """Registrar un handler de eventos."""
        with self.handlers_lock:
            if handler_id in self.handlers:
                self.logger.warning(f"Handler {handler_id} ya registrado, reemplazando")

            handler = EventHandler(
                handler_id=handler_id,
                event_types=event_types,
                callback=callback,
                priority=priority,
                filter_func=filter_func
            )

            self.handlers[handler_id] = handler
            self.stats["handlers_registered"] = len(self.handlers)

            self.logger.info(f"Handler registrado: {handler_id} para eventos {event_types}")

    def unregister_handler(self, handler_id: str):
        """Remover un handler de eventos."""
        with self.handlers_lock:
            if handler_id in self.handlers:
                del self.handlers[handler_id]
                self.stats["handlers_registered"] = len(self.handlers)
                self.logger.info(f"Handler removido: {handler_id}")

    async def publish_event(self, event: Event):
        """Publicar un evento en el bus."""
        try:
            await self.event_queue.put(event)
            self.stats["events_published"] += 1

            self.logger.debug(f"Evento publicado: {event.event_type} desde {event.source}",
                            event_type=event.event_type,
                            source=event.source,
                            correlation_id=event.correlation_id)

        except Exception as e:
            self.stats["events_failed"] += 1
            self.logger.error(f"Error publicando evento: {e}")

    async def publish(self, event_type: str, data: Dict[str, Any],
                     source: str, priority: EventPriority = EventPriority.NORMAL,
                     correlation_id: Optional[str] = None,
                     ttl_seconds: Optional[int] = None):
        """Método de conveniencia para publicar eventos."""
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            priority=priority,
            correlation_id=correlation_id,
            ttl_seconds=ttl_seconds
        )
        await self.publish_event(event)

    async def _process_events(self):
        """Procesar eventos de la cola."""
        while self.processing_active:
            try:
                # Obtener evento de la cola
                event = await self.event_queue.get()

                # Verificar si el evento ha expirado
                if event.is_expired():
                    self.logger.warning(f"Evento expirado descartado: {event.event_type}")
                    self.event_queue.task_done()
                    continue

                # Procesar evento
                await self._dispatch_event(event)

                self.stats["events_processed"] += 1
                self.event_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.stats["events_failed"] += 1
                self.logger.error(f"Error procesando evento: {e}")

                # Esperar un poco antes de continuar para evitar bucles de error
                await asyncio.sleep(1)

    async def _dispatch_event(self, event: Event):
        """Despachar evento a handlers registrados."""
        matching_handlers = []

        with self.handlers_lock:
            for handler in self.handlers.values():
                if handler.matches_event(event):
                    matching_handlers.append(handler)

        # Ordenar por prioridad (mayor primero)
        matching_handlers.sort(key=lambda h: h.priority, reverse=True)

        if not matching_handlers:
            self.logger.debug(f"No hay handlers para evento: {event.event_type}")
            return

        self.logger.debug(f"Despachando evento {event.event_type} a {len(matching_handlers)} handlers")

        # Ejecutar handlers concurrentemente
        tasks = []
        for handler in matching_handlers:
            task = asyncio.create_task(self._execute_handler(handler, event))
            tasks.append(task)

        # Esperar a que todos terminen (con timeout)
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True),
                                 timeout=30.0)
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout procesando evento {event.event_type}")

    async def _execute_handler(self, handler: EventHandler, event: Event):
        """Ejecutar un handler para un evento."""
        try:
            await handler.callback(event)
            self.logger.debug(f"Handler {handler.handler_id} procesó evento {event.event_type}")

        except Exception as e:
            self.logger.error(f"Error en handler {handler.handler_id} para evento {event.event_type}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del bus de eventos."""
        return {
            "events_published": self.stats["events_published"],
            "events_processed": self.stats["events_processed"],
            "events_failed": self.stats["events_failed"],
            "events_pending": self.event_queue.qsize(),
            "handlers_registered": self.stats["handlers_registered"],
            "uptime_seconds": time.time() - self.stats["start_time"],
            "processing_active": self.processing_active
        }


# Instancia global del event bus
_event_bus_instance: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Obtener instancia global del event bus."""
    global _event_bus_instance

    if _event_bus_instance is None:
        with _event_bus_lock:
            if _event_bus_instance is None:
                _event_bus_instance = EventBus()

    return _event_bus_instance


# Funciones de conveniencia para publicar eventos comunes
async def publish_system_event(event_type: str, data: Dict[str, Any], source: str = "system"):
    """Publicar evento del sistema."""
    bus = get_event_bus()
    await bus.publish(event_type, data, source, EventPriority.NORMAL)


async def publish_component_event(component: str, event_type: str, data: Dict[str, Any]):
    """Publicar evento de componente."""
    bus = get_event_bus()
    await bus.publish(f"component.{component}.{event_type}", data, component, EventPriority.NORMAL)


async def publish_federated_event(session_id: str, event_type: str, data: Dict[str, Any]):
    """Publicar evento federado."""
    bus = get_event_bus()
    data["session_id"] = session_id
    await bus.publish(f"federated.{event_type}", data, "federated_coordinator", EventPriority.HIGH)


async def publish_blockchain_event(event_type: str, data: Dict[str, Any]):
    """Publicar evento de blockchain."""
    bus = get_event_bus()
    await bus.publish(f"blockchain.{event_type}", data, "blockchain_client", EventPriority.HIGH)


async def publish_monitoring_event(event_type: str, data: Dict[str, Any]):
    """Publicar evento de monitoreo."""
    bus = get_event_bus()
    await bus.publish(f"monitoring.{event_type}", data, "monitor", EventPriority.NORMAL)


async def publish_api_event(endpoint: str, method: str, status_code: int, duration: float):
    """Publicar evento de API."""
    bus = get_event_bus()
    await bus.publish("api.request", {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "duration": duration
    }, "api_gateway", EventPriority.LOW)


# Clase base para componentes que usan eventos
class EventAwareComponent:
    """Clase base para componentes que escuchan eventos."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.event_bus = get_event_bus()
        self.event_handlers = []
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    async def start_listening(self):
        """Iniciar escucha de eventos."""
        # Registrar handlers específicos del componente
        await self._register_event_handlers()

    async def stop_listening(self):
        """Detener escucha de eventos."""
        for handler_id in self.event_handlers:
            self.event_bus.unregister_handler(handler_id)
        self.event_handlers.clear()

    async def _register_event_handlers(self):
        """Registrar handlers de eventos específicos del componente."""
        # Override en subclases
        pass

    def register_event_handler(self, handler_id: str, event_types: List[str],
                              callback: Callable[[Event], Awaitable[None]],
                              priority: int = 0,
                              filter_func: Optional[Callable[[Event], bool]] = None):
        """Registrar un handler de eventos."""
        self.event_bus.register_handler(handler_id, event_types, callback, priority, filter_func)
        self.event_handlers.append(handler_id)

    async def publish_event(self, event_type: str, data: Dict[str, Any],
                           priority: EventPriority = EventPriority.NORMAL):
        """Publicar evento desde este componente."""
        await self.event_bus.publish(event_type, data, self.component_name, priority)


# Sistema de eventos persistentes (para eventos importantes)
class PersistentEventStore:
    """Almacén persistente de eventos importantes."""

    def __init__(self, storage_path: str = "data/events"):
        self.storage_path = storage_path
        self.logger = get_logger(__name__)

        # Crear directorio si no existe
        import os
        os.makedirs(storage_path, exist_ok=True)

    def store_event(self, event: Event):
        """Almacenar evento de manera persistente."""
        try:
            filename = f"{event.timestamp.strftime('%Y%m%d_%H%M%S')}_{event.event_type}_{event.correlation_id or 'no_id'}.json"
            filepath = os.path.join(self.storage_path, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(event.to_dict(), f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error almacenando evento: {e}")

    def load_events(self, event_type: Optional[str] = None,
                   since: Optional[datetime] = None) -> List[Event]:
        """Cargar eventos desde almacenamiento."""
        events = []

        try:
            import glob
            pattern = os.path.join(self.storage_path, "*.json")
            files = glob.glob(pattern)

            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        event = Event.from_dict(data)

                        # Aplicar filtros
                        if event_type and event.event_type != event_type:
                            continue
                        if since and event.timestamp < since:
                            continue

                        events.append(event)

                except Exception as e:
                    self.logger.warning(f"Error cargando evento desde {file}: {e}")

        except Exception as e:
            self.logger.error(f"Error cargando eventos: {e}")

        return sorted(events, key=lambda e: e.timestamp)


# Instancia global del event store
_event_store_instance: Optional[PersistentEventStore] = None


def get_event_store() -> PersistentEventStore:
    """Obtener instancia global del event store."""
    global _event_store_instance

    if _event_store_instance is None:
        _event_store_instance = PersistentEventStore()

    return _event_store_instance