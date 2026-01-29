"""
Sistema de colas para envío asíncrono de notificaciones
====================================================

Este módulo implementa un sistema de colas para el envío asíncrono
de notificaciones push y email.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import heapq
import threading
import time

from .models import QueueItem, Notification, NotificationPriority, NotificationStatus


logger = logging.getLogger(__name__)


class NotificationQueue:
    """
    Cola de prioridad para notificaciones con envío asíncrono.
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self._queue: List[QueueItem] = []
        self._processing = False
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._lock = threading.Lock()
        self._send_callback: Optional[Callable[[Notification], None]] = None

        # Estadísticas
        self.stats = {
            'processed': 0,
            'failed': 0,
            'retries': 0,
            'avg_processing_time': 0.0
        }

    def set_send_callback(self, callback: Callable[[Notification], None]):
        """Establece la función de envío de notificaciones."""
        self._send_callback = callback

    def enqueue(self, notification: Notification) -> bool:
        """
        Agrega una notificación a la cola.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se agregó exitosamente
        """
        if not self._send_callback:
            logger.error("No se ha configurado callback de envío")
            return False

        with self._lock:
            # Crear elemento de cola
            queue_item = QueueItem(
                notification_id=notification.id,
                priority=notification.priority,
                scheduled_at=notification.scheduled_at
            )

            # Agregar a cola de prioridad (usando heapq con tupla: prioridad, timestamp, item)
            priority_value = self._get_priority_value(notification.priority)
            timestamp = notification.scheduled_at.timestamp() if notification.scheduled_at else time.time()

            heapq.heappush(self._queue, (priority_value, timestamp, queue_item))

            logger.info(f"Notificación {notification.id} agregada a cola (prioridad: {notification.priority.value})")
            return True

    def enqueue_multiple(self, notifications: List[Notification]) -> int:
        """
        Agrega múltiples notificaciones a la cola.

        Args:
            notifications: Lista de notificaciones

        Returns:
            int: Número de notificaciones agregadas
        """
        count = 0
        for notification in notifications:
            if self.enqueue(notification):
                count += 1
        return count

    def start(self):
        """Inicia el procesamiento de la cola."""
        if self._processing:
            logger.warning("La cola ya está procesándose")
            return

        self._processing = True
        self._stop_event.clear()

        # Crear workers
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"NotificationWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

        logger.info(f"Cola de notificaciones iniciada con {self.max_workers} workers")

    def stop(self, timeout: float = 5.0):
        """Detiene el procesamiento de la cola."""
        if not self._processing:
            return

        self._processing = False
        self._stop_event.set()

        # Esperar a que terminen los workers
        for worker in self._workers:
            worker.join(timeout=timeout)

        self._workers.clear()
        logger.info("Cola de notificaciones detenida")

    def get_queue_size(self) -> int:
        """Obtiene el tamaño actual de la cola."""
        with self._lock:
            return len(self._queue)

    def get_pending_notifications(self) -> List[QueueItem]:
        """Obtiene lista de notificaciones pendientes."""
        with self._lock:
            return [item for _, _, item in self._queue]

    def clear_queue(self):
        """Limpia la cola de notificaciones pendientes."""
        with self._lock:
            self._queue.clear()
        logger.info("Cola de notificaciones limpiada")

    def _get_priority_value(self, priority: NotificationPriority) -> int:
        """Convierte prioridad a valor numérico para heapq (menor = mayor prioridad)."""
        priority_map = {
            NotificationPriority.URGENT: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.NORMAL: 2,
            NotificationPriority.LOW: 3
        }
        return priority_map.get(priority, 2)

    def _worker_loop(self):
        """Bucle principal de procesamiento de un worker."""
        while not self._stop_event.is_set():
            try:
                # Obtener lote de notificaciones para procesar
                batch = self._get_batch()
                if not batch:
                    time.sleep(0.1)  # Pequeña pausa si no hay trabajo
                    continue

                # Procesar lote
                self._process_batch(batch)

            except Exception as e:
                logger.error(f"Error en worker de notificaciones: {e}")
                time.sleep(1.0)  # Pausa en caso de error

    def _get_batch(self) -> List[QueueItem]:
        """Obtiene un lote de notificaciones para procesar."""
        batch = []
        current_time = time.time()

        with self._lock:
            # Procesar hasta batch_size elementos que estén listos
            while len(batch) < self.batch_size and self._queue:
                priority, scheduled_time, item = heapq.heappop(self._queue)

                # Verificar si está programado para el futuro
                if scheduled_time > current_time:
                    # Volver a agregar si no es tiempo aún
                    heapq.heappush(self._queue, (priority, scheduled_time, item))
                    break

                batch.append(item)

        return batch

    def _process_batch(self, batch: List[QueueItem]):
        """Procesa un lote de notificaciones."""
        for item in batch:
            try:
                start_time = time.time()

                # Aquí iría la lógica para obtener la notificación completa
                # y enviarla usando el callback
                # Por ahora, simulamos el envío
                if self._send_callback:
                    # Nota: En implementación real, necesitaríamos obtener la notificación
                    # completa desde una base de datos o repositorio
                    logger.info(f"Procesando notificación {item.notification_id}")

                    # Simular procesamiento
                    processing_time = time.time() - start_time
                    self._update_stats(True, processing_time)

                else:
                    logger.warning(f"No hay callback configurado para {item.notification_id}")
                    self._update_stats(False, 0)

            except Exception as e:
                logger.error(f"Error procesando notificación {item.notification_id}: {e}")
                self._update_stats(False, 0)

    def _update_stats(self, success: bool, processing_time: float):
        """Actualiza estadísticas de procesamiento."""
        with self._lock:
            if success:
                self.stats['processed'] += 1
            else:
                self.stats['failed'] += 1

            # Actualizar tiempo promedio de procesamiento
            if self.stats['processed'] > 0:
                total_processed = self.stats['processed']
                current_avg = self.stats['avg_processing_time']
                self.stats['avg_processing_time'] = (current_avg * (total_processed - 1) + processing_time) / total_processed

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola."""
        with self._lock:
            return self.stats.copy()


class AsyncNotificationQueue:
    """
    Versión asíncrona de la cola de notificaciones usando asyncio.
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._processing = False
        self._stop_event = asyncio.Event()
        self._send_callback: Optional[Callable[[Notification], Awaitable[None]]] = None
        self._tasks: List[asyncio.Task] = []

        # Estadísticas
        self.stats = {
            'processed': 0,
            'failed': 0,
            'retries': 0,
            'avg_processing_time': 0.0
        }

    def set_send_callback(self, callback: Callable[[Notification], Awaitable[None]]):
        """Establece la función asíncrona de envío de notificaciones."""
        self._send_callback = callback

    async def enqueue(self, notification: Notification) -> bool:
        """
        Agrega una notificación a la cola de forma asíncrona.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se agregó exitosamente
        """
        if not self._send_callback:
            logger.error("No se ha configurado callback de envío")
            return False

        try:
            # Crear elemento de cola
            queue_item = QueueItem(
                notification_id=notification.id,
                priority=notification.priority,
                scheduled_at=notification.scheduled_at
            )

            # Calcular prioridad y timestamp
            priority_value = self._get_priority_value(notification.priority)
            timestamp = notification.scheduled_at.timestamp() if notification.scheduled_at else time.time()

            await self._queue.put((priority_value, timestamp, queue_item))

            logger.info(f"Notificación {notification.id} agregada a cola async (prioridad: {notification.priority.value})")
            return True

        except Exception as e:
            logger.error(f"Error agregando notificación a cola: {e}")
            return False

    async def enqueue_multiple(self, notifications: List[Notification]) -> int:
        """
        Agrega múltiples notificaciones a la cola de forma asíncrona.

        Args:
            notifications: Lista de notificaciones

        Returns:
            int: Número de notificaciones agregadas
        """
        count = 0
        for notification in notifications:
            if await self.enqueue(notification):
                count += 1
        return count

    async def start(self):
        """Inicia el procesamiento asíncrono de la cola."""
        if self._processing:
            logger.warning("La cola async ya está procesándose")
            return

        self._processing = True
        self._stop_event.clear()

        # Crear tareas de worker
        for i in range(self.max_workers):
            task = asyncio.create_task(
                self._worker_loop(),
                name=f"AsyncNotificationWorker-{i+1}"
            )
            self._tasks.append(task)

        logger.info(f"Cola de notificaciones async iniciada con {self.max_workers} workers")

    async def stop(self):
        """Detiene el procesamiento asíncrono de la cola."""
        if not self._processing:
            return

        self._processing = False
        self._stop_event.set()

        # Cancelar tareas
        for task in self._tasks:
            task.cancel()

        # Esperar a que terminen
        try:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        self._tasks.clear()
        logger.info("Cola de notificaciones async detenida")

    async def get_queue_size(self) -> int:
        """Obtiene el tamaño actual de la cola."""
        return self._queue.qsize()

    def _get_priority_value(self, priority: NotificationPriority) -> int:
        """Convierte prioridad a valor numérico para PriorityQueue."""
        priority_map = {
            NotificationPriority.URGENT: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.NORMAL: 2,
            NotificationPriority.LOW: 3
        }
        return priority_map.get(priority, 2)

    async def _worker_loop(self):
        """Bucle principal de procesamiento asíncrono de un worker."""
        while not self._stop_event.is_set():
            try:
                # Obtener lote de notificaciones para procesar
                batch = await self._get_batch()
                if not batch:
                    await asyncio.sleep(0.1)  # Pequeña pausa si no hay trabajo
                    continue

                # Procesar lote
                await self._process_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en worker async de notificaciones: {e}")
                await asyncio.sleep(1.0)  # Pausa en caso de error

    async def _get_batch(self) -> List[QueueItem]:
        """Obtiene un lote de notificaciones para procesar de forma asíncrona."""
        batch = []
        current_time = time.time()

        try:
            while len(batch) < self.batch_size:
                # Intentar obtener elemento con timeout
                try:
                    priority, scheduled_time, item = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    break

                # Verificar si está programado para el futuro
                if scheduled_time > current_time:
                    # Volver a agregar si no es tiempo aún
                    await self._queue.put((priority, scheduled_time, item))
                    break

                batch.append(item)

        except Exception as e:
            logger.error(f"Error obteniendo lote: {e}")

        return batch

    async def _process_batch(self, batch: List[QueueItem]):
        """Procesa un lote de notificaciones de forma asíncrona."""
        for item in batch:
            try:
                start_time = time.time()

                # Aquí iría la lógica para obtener la notificación completa
                # y enviarla usando el callback
                if self._send_callback:
                    logger.info(f"Procesando notificación async {item.notification_id}")

                    # Simular procesamiento asíncrono
                    await asyncio.sleep(0.01)  # Simular I/O
                    processing_time = time.time() - start_time
                    self._update_stats(True, processing_time)

                else:
                    logger.warning(f"No hay callback configurado para {item.notification_id}")
                    self._update_stats(False, 0)

            except Exception as e:
                logger.error(f"Error procesando notificación async {item.notification_id}: {e}")
                self._update_stats(False, 0)

    def _update_stats(self, success: bool, processing_time: float):
        """Actualiza estadísticas de procesamiento."""
        if success:
            self.stats['processed'] += 1
        else:
            self.stats['failed'] += 1

        # Actualizar tiempo promedio de procesamiento
        if self.stats['processed'] > 0:
            total_processed = self.stats['processed']
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = (current_avg * (total_processed - 1) + processing_time) / total_processed

    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola async."""
        return self.stats.copy()