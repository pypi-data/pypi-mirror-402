"""
NetworkSyncManager - Sincronización con la red cuando esté disponible
Gestiona la conectividad de red y sincronización de datos de entrenamiento.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException
import socket
import threading
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)


class NetworkStatus(Enum):
    """Estados de conectividad de red."""
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ONLINE = "online"
    LIMITED = "limited"  # Conectado pero con limitaciones
    ERROR = "error"


class SyncPriority(Enum):
    """Prioridades de sincronización."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NetworkConfig:
    """Configuración de sincronización de red."""
    sync_server_url: str = "https://sync.ailoos.network"
    websocket_url: str = "wss://sync.ailoos.network/ws"
    api_key: Optional[str] = None
    device_id: str = "default_device"
    sync_interval_seconds: int = 30
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    connection_timeout: float = 10.0
    enable_auto_sync: bool = True
    sync_on_connectivity: bool = True
    compress_sync_data: bool = True
    max_sync_batch_size: int = 100


@dataclass
class SyncData:
    """Datos para sincronizar."""
    data_type: str  # 'checkpoint', 'metrics', 'config', etc.
    data_id: str
    content: Dict[str, Any]
    priority: SyncPriority = SyncPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    checksum: str = ""
    compressed: bool = False
    size_bytes: int = 0


@dataclass
class NetworkStats:
    """Estadísticas de red."""
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    total_data_uploaded: int = 0
    total_data_downloaded: int = 0
    average_sync_time: float = 0.0
    last_sync_time: Optional[float] = None
    current_status: NetworkStatus = NetworkStatus.OFFLINE
    uptime_percentage: float = 0.0


class NetworkSyncManager:
    """
    Gestor de sincronización de red para entrenamiento asíncrono.

    Características:
    - Detección automática de conectividad
    - Sincronización inteligente de datos
    - Reintentos automáticos
    - Compresión de datos
    - WebSocket para actualizaciones en tiempo real
    """

    def __init__(self, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self.stats = NetworkStats()

        # Estado de red
        self.current_status = NetworkStatus.OFFLINE
        self.last_connectivity_check = 0.0
        self.connectivity_check_interval = 5.0  # segundos

        # Colas de sincronización
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.pending_syncs: Dict[str, SyncData] = {}
        self.completed_syncs: Dict[str, SyncData] = {}

        # Conexiones
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.websocket_connected = False

        # Callbacks
        self.on_connectivity_change: Optional[Callable[[NetworkStatus, NetworkStatus], Awaitable[None]]] = None
        self.on_sync_success: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
        self.on_sync_failure: Optional[Callable[[str, Exception], Awaitable[None]]] = None

        # Control de concurrencia
        self._lock = asyncio.Lock()
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._websocket_task: Optional[asyncio.Task] = None

        logger.info(f"🚀 NetworkSyncManager inicializado para dispositivo {self.config.device_id}")

    async def start(self) -> None:
        """Iniciar el gestor de sincronización."""
        async with self._lock:
            if self._running:
                return

            self._running = True

            # Crear sesión HTTP
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout),
                headers=self._get_auth_headers()
            )

            # Iniciar tareas
            self._sync_task = asyncio.create_task(self._sync_worker())
            self._monitor_task = asyncio.create_task(self._connectivity_monitor())
            self._websocket_task = asyncio.create_task(self._websocket_handler())

            logger.info("✅ NetworkSyncManager iniciado")

    async def stop(self) -> None:
        """Detener el gestor de sincronización."""
        async with self._lock:
            if not self._running:
                return

            self._running = False

            # Cancelar tareas
            for task in [self._sync_task, self._monitor_task, self._websocket_task]:
                if task and not task.done():
                    task.cancel()

            # Cerrar conexiones
            if self.websocket and self.websocket_connected:
                await self.websocket.close()

            if self.http_session:
                await self.http_session.close()

            logger.info("🛑 NetworkSyncManager detenido")

    async def queue_sync_data(
        self,
        data_type: str,
        data_id: str,
        content: Dict[str, Any],
        priority: SyncPriority = SyncPriority.NORMAL
    ) -> str:
        """
        Encolar datos para sincronización.

        Args:
            data_type: Tipo de datos ('checkpoint', 'metrics', etc.)
            data_id: ID único de los datos
            content: Contenido a sincronizar
            priority: Prioridad de sincronización

        Returns:
            ID de sincronización
        """
        sync_data = SyncData(
            data_type=data_type,
            data_id=data_id,
            content=content,
            priority=priority,
            size_bytes=len(json.dumps(content).encode())
        )

        # Calcular checksum
        sync_data.checksum = self._calculate_checksum(content)

        # Comprimir si está habilitado
        if self.config.compress_sync_data:
            sync_data.content = self._compress_data(content)
            sync_data.compressed = True

        # Encolar
        await self.sync_queue.put(sync_data)
        self.pending_syncs[data_id] = sync_data

        logger.debug(f"📋 Encolado sync {data_id} ({data_type}) - prioridad {priority.value}")
        return data_id

    async def sync_now(self, data_type: str, data_id: str, content: Dict[str, Any]) -> bool:
        """
        Sincronizar datos inmediatamente.

        Args:
            data_type: Tipo de datos
            data_id: ID de los datos
            content: Contenido a sincronizar

        Returns:
            True si la sincronización fue exitosa
        """
        if self.current_status == NetworkStatus.OFFLINE:
            logger.warning(f"⚠️ No se puede sincronizar {data_id} - sin conexión")
            return False

        try:
            success = await self._perform_sync(data_type, data_id, content)
            if success:
                self.stats.successful_syncs += 1
                if self.on_sync_success:
                    await self.on_sync_success(data_id, content)
            else:
                self.stats.failed_syncs += 1
                if self.on_sync_failure:
                    await self.on_sync_failure(data_id, Exception("Sync failed"))

            return success

        except Exception as e:
            logger.error(f"❌ Error sincronizando {data_id}: {e}")
            self.stats.failed_syncs += 1
            if self.on_sync_failure:
                await self.on_sync_failure(data_id, e)
            return False

    async def get_sync_status(self, data_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado de sincronización de datos específicos.

        Args:
            data_id: ID de los datos

        Returns:
            Estado de sincronización o None si no existe
        """
        async with self._lock:
            if data_id in self.completed_syncs:
                sync_data = self.completed_syncs[data_id]
                return {
                    'status': 'completed',
                    'data_type': sync_data.data_type,
                    'timestamp': sync_data.timestamp,
                    'size_bytes': sync_data.size_bytes
                }
            elif data_id in self.pending_syncs:
                sync_data = self.pending_syncs[data_id]
                return {
                    'status': 'pending',
                    'data_type': sync_data.data_type,
                    'priority': sync_data.priority.value,
                    'size_bytes': sync_data.size_bytes
                }
            else:
                return None

    async def get_network_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de red."""
        async with self._lock:
            return {
                'current_status': self.current_status.value,
                'total_syncs': self.stats.total_syncs,
                'successful_syncs': self.stats.successful_syncs,
                'failed_syncs': self.stats.failed_syncs,
                'success_rate': (self.stats.successful_syncs / max(self.stats.total_syncs, 1)) * 100,
                'total_data_uploaded': self.stats.total_data_uploaded,
                'total_data_downloaded': self.stats.total_data_downloaded,
                'average_sync_time': self.stats.average_sync_time,
                'last_sync_time': self.stats.last_sync_time,
                'uptime_percentage': self.stats.uptime_percentage,
                'pending_syncs': len(self.pending_syncs),
                'completed_syncs': len(self.completed_syncs)
            }

    async def force_connectivity_check(self) -> NetworkStatus:
        """Forzar verificación de conectividad."""
        new_status = await self._check_connectivity()
        await self._update_network_status(new_status)
        return new_status

    async def _sync_worker(self) -> None:
        """Trabajador de sincronización en background."""
        while self._running:
            try:
                # Esperar datos para sincronizar
                sync_data = await self.sync_queue.get()

                # Solo sincronizar si hay conectividad
                if self.current_status in [NetworkStatus.ONLINE, NetworkStatus.LIMITED]:
                    success = await self._perform_sync(
                        sync_data.data_type,
                        sync_data.data_id,
                        sync_data.content
                    )

                    if success:
                        self.stats.successful_syncs += 1
                        self.completed_syncs[sync_data.data_id] = sync_data
                        if self.on_sync_success:
                            await self.on_sync_success(sync_data.data_id, sync_data.content)
                    else:
                        self.stats.failed_syncs += 1
                        # Re-encolar con backoff si es alta prioridad
                        if sync_data.priority in [SyncPriority.HIGH, SyncPriority.CRITICAL]:
                            await asyncio.sleep(1.0)
                            await self.sync_queue.put(sync_data)
                        if self.on_sync_failure:
                            await self.on_sync_failure(sync_data.data_id, Exception("Sync failed"))

                    # Limpiar de pendientes
                    if sync_data.data_id in self.pending_syncs:
                        del self.pending_syncs[sync_data.data_id]

                else:
                    # Re-encolar si no hay conectividad
                    await asyncio.sleep(0.1)
                    await self.sync_queue.put(sync_data)

                self.sync_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en sync worker: {e}")
                await asyncio.sleep(1.0)

    async def _connectivity_monitor(self) -> None:
        """Monitor de conectividad en background."""
        while self._running:
            try:
                # Verificar conectividad
                new_status = await self._check_connectivity()
                await self._update_network_status(new_status)

                # Actualizar estadísticas de uptime
                self._update_uptime_stats()

                await asyncio.sleep(self.connectivity_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en connectivity monitor: {e}")
                await asyncio.sleep(1.0)

    async def _websocket_handler(self) -> None:
        """Manejador de WebSocket para actualizaciones en tiempo real."""
        while self._running:
            try:
                if self.current_status == NetworkStatus.ONLINE and not self.websocket_connected:
                    await self._connect_websocket()

                elif self.current_status != NetworkStatus.ONLINE and self.websocket_connected:
                    await self._disconnect_websocket()

                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en websocket handler: {e}")
                await asyncio.sleep(5.0)

    async def _connect_websocket(self) -> None:
        """Conectar WebSocket."""
        try:
            uri = f"{self.config.websocket_url}?device_id={self.config.device_id}"
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.websocket_connected = True
                logger.info("🔗 WebSocket conectado")

                # Mantener conexión viva
                while self.websocket_connected and self._running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        await self._handle_websocket_message(message)
                    except asyncio.TimeoutError:
                        # Enviar ping
                        await websocket.ping()
                    except (ConnectionClosedError, WebSocketException):
                        break

        except Exception as e:
            logger.warning(f"⚠️ Error conectando WebSocket: {e}")
        finally:
            self.websocket_connected = False
            self.websocket = None

    async def _disconnect_websocket(self) -> None:
        """Desconectar WebSocket."""
        if self.websocket and self.websocket_connected:
            await self.websocket.close()
            self.websocket_connected = False
            logger.info("🔌 WebSocket desconectado")

    async def _handle_websocket_message(self, message: str) -> None:
        """Manejar mensaje recibido por WebSocket."""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'sync_request':
                # Servidor solicita sincronización
                await self._handle_sync_request(data)
            elif message_type == 'config_update':
                # Actualización de configuración
                await self._handle_config_update(data)
            elif message_type == 'status_update':
                # Actualización de estado
                await self._handle_status_update(data)

        except json.JSONDecodeError:
            logger.warning(f"⚠️ Mensaje WebSocket inválido: {message}")
        except Exception as e:
            logger.error(f"❌ Error manejando mensaje WebSocket: {e}")

    async def _handle_sync_request(self, data: Dict[str, Any]) -> None:
        """Manejar solicitud de sincronización."""
        data_type = data.get('data_type')
        data_id = data.get('data_id')

        if data_type and data_id:
            # Buscar datos locales
            if data_id in self.completed_syncs:
                sync_data = self.completed_syncs[data_id]
                await self.sync_now(data_type, data_id, sync_data.content)

    async def _handle_config_update(self, data: Dict[str, Any]) -> None:
        """Manejar actualización de configuración."""
        logger.info(f"📡 Configuración actualizada: {data}")

    async def _handle_status_update(self, data: Dict[str, Any]) -> None:
        """Manejar actualización de estado."""
        logger.debug(f"📡 Estado actualizado: {data}")

    async def _check_connectivity(self) -> NetworkStatus:
        """Verificar conectividad de red."""
        try:
            # Verificación básica de conectividad
            socket.create_connection((self.config.sync_server_url.replace('https://', '').replace('http://', '').split('/')[0], 80), timeout=5)
            return NetworkStatus.ONLINE

        except (socket.timeout, socket.gaierror, OSError):
            return NetworkStatus.OFFLINE

    async def _update_network_status(self, new_status: NetworkStatus) -> None:
        """Actualizar estado de red."""
        if new_status != self.current_status:
            old_status = self.current_status
            self.current_status = new_status

            logger.info(f"📡 Estado de red: {old_status.value} → {new_status.value}")

            if self.on_connectivity_change:
                await self.on_connectivity_change(old_status, new_status)

    async def _perform_sync(self, data_type: str, data_id: str, content: Dict[str, Any]) -> bool:
        """Realizar sincronización HTTP."""
        if not self.http_session:
            return False

        try:
            start_time = time.time()

            url = f"{self.config.sync_server_url}/api/v1/sync/{data_type}"
            payload = {
                'device_id': self.config.device_id,
                'data_id': data_id,
                'content': content,
                'timestamp': time.time()
            }

            async with self.http_session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    sync_time = time.time() - start_time

                    # Actualizar estadísticas
                    self.stats.total_syncs += 1
                    self.stats.last_sync_time = time.time()
                    self.stats.average_sync_time = (
                        (self.stats.average_sync_time * (self.stats.total_syncs - 1)) + sync_time
                    ) / self.stats.total_syncs

                    data_size = len(json.dumps(content).encode())
                    self.stats.total_data_uploaded += data_size

                    logger.debug(f"✅ Sync completado: {data_id} en {sync_time:.2f}s")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Sync falló ({response.status}): {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error en sync HTTP: {e}")
            return False

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calcular checksum de datos."""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _compress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprimir datos (simplificado)."""
        # En implementación real, usar compresión real
        return data

    def _get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación."""
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key:
            headers['Authorization'] = f"Bearer {self.config.api_key}"
        return headers

    def _update_uptime_stats(self) -> None:
        """Actualizar estadísticas de uptime."""
        # Implementación simplificada
        if self.current_status == NetworkStatus.ONLINE:
            self.stats.uptime_percentage = min(100.0, self.stats.uptime_percentage + 1.0)
        else:
            self.stats.uptime_percentage = max(0.0, self.stats.uptime_percentage - 0.5)

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()