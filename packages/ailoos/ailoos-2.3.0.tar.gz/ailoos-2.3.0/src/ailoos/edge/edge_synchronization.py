"""
Sincronización eficiente entre dispositivos edge y nodos centrales.

Gestiona la comunicación bidireccional, optimización de ancho de banda,
manejo de conectividad intermitente y sincronización de modelos y datos FL.
"""

import torch
import logging
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import zlib
import hashlib
import queue
from concurrent.futures import ThreadPoolExecutor
import requests
import socket

logger = logging.getLogger(__name__)


class SyncPriority(Enum):
    """Prioridades de sincronización."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SyncDirection(Enum):
    """Dirección de sincronización."""
    UPLOAD = "upload"  # Edge -> Central
    DOWNLOAD = "download"  # Central -> Edge
    BIDIRECTIONAL = "bidirectional"


class ConnectionState(Enum):
    """Estados de conexión."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    RECONNECTING = "reconnecting"


@dataclass
class SyncTask:
    """Tarea de sincronización."""
    task_id: str
    task_type: str
    direction: SyncDirection
    priority: SyncPriority
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    callback: Optional[Callable] = None


@dataclass
class SyncResult:
    """Resultado de sincronización."""
    task_id: str
    success: bool
    data_size_bytes: int
    transfer_time_seconds: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class CompressionConfig:
    """Configuración de compresión."""
    enabled: bool = True
    algorithm: str = "zlib"  # zlib, gzip, lzma
    level: int = 6  # 1-9 para zlib
    min_size_bytes: int = 1024  # Solo comprimir datos > 1KB


@dataclass
class EdgeSynchronizationConfig:
    """Configuración de sincronización edge."""
    # Conexión
    central_node_url: str
    device_id: str
    auth_token: Optional[str] = None

    # Sincronización
    sync_interval_seconds: int = 300  # 5 minutos
    max_concurrent_syncs: int = 2
    enable_compression: bool = True
    enable_encryption: bool = True

    # Reintento y resiliencia
    max_retry_attempts: int = 3
    retry_backoff_seconds: int = 30
    connection_timeout_seconds: int = 30
    enable_offline_buffering: bool = True

    # Límites de recursos
    max_buffer_size_mb: int = 50
    max_bandwidth_mbps: Optional[float] = None

    # Monitoreo
    enable_sync_monitoring: bool = True
    heartbeat_interval_seconds: int = 60


class DataCompressor:
    """Compresor de datos para optimización de ancho de banda."""

    def __init__(self, config: CompressionConfig):
        self.config = config

    def compress(self, data: bytes) -> Tuple[bytes, str]:
        """
        Comprimir datos.

        Returns:
            Tupla de (datos_comprimidos, algoritmo_usado)
        """
        if not self.config.enabled or len(data) < self.config.min_size_bytes:
            return data, "none"

        try:
            if self.config.algorithm == "zlib":
                compressed = zlib.compress(data, level=self.config.level)
                return compressed, "zlib"
            else:
                return data, "none"
        except Exception as e:
            logger.warning(f"⚠️ Error comprimiendo datos: {e}")
            return data, "none"

    def decompress(self, data: bytes, algorithm: str) -> bytes:
        """Descomprimir datos."""
        if algorithm == "none":
            return data

        try:
            if algorithm == "zlib":
                return zlib.decompress(data)
            else:
                return data
        except Exception as e:
            logger.error(f"❌ Error descomprimiendo datos: {e}")
            return data


class SyncBuffer:
    """Buffer para datos pendientes de sincronización."""

    def __init__(self, max_size_mb: int):
        self.max_size_mb = max_size_mb
        self.buffer: Dict[str, SyncTask] = {}
        self.total_size_bytes = 0
        self.lock = threading.Lock()

    def add_task(self, task: SyncTask) -> bool:
        """Agregar tarea al buffer."""
        with self.lock:
            # Estimar tamaño
            task_size = self._estimate_task_size(task)

            if self.total_size_bytes + task_size > self.max_size_mb * 1024 * 1024:
                logger.warning("⚠️ Buffer lleno, no se puede agregar tarea")
                return False

            self.buffer[task.task_id] = task
            self.total_size_bytes += task_size
            return True

    def get_pending_tasks(self, priority_filter: Optional[SyncPriority] = None) -> List[SyncTask]:
        """Obtener tareas pendientes."""
        with self.lock:
            tasks = list(self.buffer.values())

            if priority_filter:
                tasks = [t for t in tasks if t.priority == priority_filter]

            # Ordenar por prioridad y tiempo de creación
            priority_order = {SyncPriority.CRITICAL: 0, SyncPriority.HIGH: 1,
                            SyncPriority.NORMAL: 2, SyncPriority.LOW: 3}

            tasks.sort(key=lambda t: (priority_order[t.priority], t.created_at))
            return tasks

    def remove_task(self, task_id: str):
        """Remover tarea del buffer."""
        with self.lock:
            if task_id in self.buffer:
                task_size = self._estimate_task_size(self.buffer[task_id])
                self.total_size_bytes -= task_size
                del self.buffer[task_id]

    def clear_completed_tasks(self, completed_task_ids: List[str]):
        """Limpiar tareas completadas."""
        for task_id in completed_task_ids:
            self.remove_task(task_id)

    def _estimate_task_size(self, task: SyncTask) -> int:
        """Estimar tamaño de una tarea."""
        # Estimación simplificada
        if isinstance(task.data, (bytes, bytearray)):
            return len(task.data)
        elif isinstance(task.data, dict):
            return len(json.dumps(task.data).encode())
        elif isinstance(task.data, torch.Tensor):
            return task.data.numel() * task.data.element_size()
        else:
            return 1024  # Estimación por defecto


class EdgeSynchronization:
    """
    Sistema de sincronización eficiente para dispositivos edge.

    Características principales:
    - Sincronización bidireccional optimizada
    - Compresión automática de datos
    - Manejo de conectividad intermitente
    - Buffer inteligente para datos offline
    - Monitoreo de rendimiento de red
    - Reintentos automáticos con backoff
    """

    def __init__(self, config: EdgeSynchronizationConfig):
        self.config = config

        # Estado de conexión
        self.connection_state = ConnectionState.DISCONNECTED
        self.last_connection_time = 0
        self.connection_lock = threading.Lock()

        # Buffer de sincronización
        self.sync_buffer = SyncBuffer(config.max_buffer_size_mb)

        # Compresión
        self.compressor = DataCompressor(CompressionConfig(
            enabled=config.enable_compression,
            algorithm="zlib",
            level=6
        ))

        # Colas de sincronización
        self.sync_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()

        # Hilos
        self.sync_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None

        # Executor para tareas concurrentes
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_syncs)

        # Estadísticas
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "bytes_uploaded": 0,
            "bytes_downloaded": 0,
            "compression_ratio": 1.0,
            "avg_sync_time_seconds": 0.0,
            "connection_drops": 0
        }

        # Callbacks
        self.sync_callbacks: List[Callable] = []
        self.connection_callbacks: List[Callable] = []

        logger.info("🔧 EdgeSynchronization inicializado")
        logger.info(f"   Nodo central: {config.central_node_url}")
        logger.info(f"   Device ID: {config.device_id}")

    def start(self):
        """Iniciar sincronización."""
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("⚠️ Sincronización ya está ejecutándose")
            return

        # Iniciar hilos
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()

        if self.config.enable_sync_monitoring:
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

        logger.info("🚀 EdgeSynchronization iniciado")

    def stop(self):
        """Detener sincronización."""
        # Esperar a que terminen los hilos
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)

        self.executor.shutdown(wait=True)
        logger.info("🛑 EdgeSynchronization detenido")

    def sync_model_update(
        self,
        model_data: Any,
        model_version: str,
        priority: SyncPriority = SyncPriority.NORMAL,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Sincronizar actualización de modelo.

        Args:
            model_data: Datos del modelo
            model_version: Versión del modelo
            priority: Prioridad de sincronización
            callback: Callback opcional

        Returns:
            ID de tarea de sincronización
        """
        task_id = f"model_sync_{int(time.time() * 1000)}_{np.random.randint(1000)}"

        task = SyncTask(
            task_id=task_id,
            task_type="model_update",
            direction=SyncDirection.UPLOAD,
            priority=priority,
            data=model_data,
            metadata={
                "model_version": model_version,
                "data_type": "model"
            },
            callback=callback
        )

        self._queue_sync_task(task)
        return task_id

    def sync_federated_update(
        self,
        gradients: Any,
        round_number: int,
        priority: SyncPriority = SyncPriority.HIGH,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Sincronizar actualización federada.

        Args:
            gradients: Gradientes del modelo
            round_number: Número de ronda FL
            priority: Prioridad de sincronización
            callback: Callback opcional

        Returns:
            ID de tarea de sincronización
        """
        task_id = f"fl_sync_{round_number}_{int(time.time() * 1000)}"

        task = SyncTask(
            task_id=task_id,
            task_type="federated_update",
            direction=SyncDirection.UPLOAD,
            priority=priority,
            data=gradients,
            metadata={
                "round_number": round_number,
                "data_type": "gradients"
            },
            callback=callback
        )

        self._queue_sync_task(task)
        return task_id

    def sync_metrics(
        self,
        metrics_data: Dict[str, Any],
        priority: SyncPriority = SyncPriority.LOW,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Sincronizar métricas de rendimiento.

        Args:
            metrics_data: Datos de métricas
            priority: Prioridad de sincronización
            callback: Callback opcional

        Returns:
            ID de tarea de sincronización
        """
        task_id = f"metrics_sync_{int(time.time() * 1000)}"

        task = SyncTask(
            task_id=task_id,
            task_type="metrics",
            direction=SyncDirection.UPLOAD,
            priority=priority,
            data=metrics_data,
            metadata={"data_type": "metrics"},
            callback=callback
        )

        self._queue_sync_task(task)
        return task_id

    def request_model_download(
        self,
        model_version: Optional[str] = None,
        priority: SyncPriority = SyncPriority.HIGH,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Solicitar descarga de modelo desde nodo central.

        Args:
            model_version: Versión específica del modelo (opcional)
            priority: Prioridad de sincronización
            callback: Callback opcional

        Returns:
            ID de tarea de sincronización
        """
        task_id = f"model_download_{int(time.time() * 1000)}"

        task = SyncTask(
            task_id=task_id,
            task_type="model_download",
            direction=SyncDirection.DOWNLOAD,
            priority=priority,
            data=None,
            metadata={
                "requested_version": model_version,
                "data_type": "model_request"
            },
            callback=callback
        )

        self._queue_sync_task(task)
        return task_id

    def get_sync_status(self) -> Dict[str, Any]:
        """Obtener estado de sincronización."""
        return {
            "connection_state": self.connection_state.value,
            "buffered_tasks": len(self.sync_buffer.buffer),
            "buffer_size_mb": self.sync_buffer.total_size_bytes / (1024 * 1024),
            "pending_queue_size": self.sync_queue.qsize(),
            "stats": self.stats.copy(),
            "last_connection": self.last_connection_time
        }

    def add_sync_callback(self, callback: Callable):
        """Agregar callback para eventos de sincronización."""
        self.sync_callbacks.append(callback)

    def add_connection_callback(self, callback: Callable):
        """Agregar callback para eventos de conexión."""
        self.connection_callbacks.append(callback)

    def _queue_sync_task(self, task: SyncTask):
        """Agregar tarea a la cola de sincronización."""
        # Agregar al buffer si está habilitado
        if self.config.enable_offline_buffering:
            if not self.sync_buffer.add_task(task):
                logger.error(f"❌ No se pudo buffer la tarea {task.task_id}")
                return

        # Agregar a cola de procesamiento
        priority_value = self._get_priority_value(task.priority)
        self.sync_queue.put((priority_value, task))

    def _get_priority_value(self, priority: SyncPriority) -> int:
        """Convertir prioridad a valor numérico."""
        priority_map = {
            SyncPriority.CRITICAL: 0,
            SyncPriority.HIGH: 1,
            SyncPriority.NORMAL: 2,
            SyncPriority.LOW: 3
        }
        return priority_map[priority]

    def _sync_loop(self):
        """Bucle principal de sincronización."""
        logger.info("🔄 Iniciando bucle de sincronización")

        while True:
            try:
                # Obtener tarea de la cola
                priority_value, task = self.sync_queue.get(timeout=5.0)

                # Verificar conexión
                if not self._ensure_connection():
                    # Reencolar tarea si no hay conexión
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        time.sleep(self.config.retry_backoff_seconds * task.retry_count)
                        self.sync_queue.put((priority_value, task))
                    else:
                        logger.error(f"❌ Máximo reintentos alcanzado para tarea {task.task_id}")
                        self._notify_sync_result(SyncResult(
                            task_id=task.task_id,
                            success=False,
                            data_size_bytes=0,
                            transfer_time_seconds=0,
                            error="Connection failed after max retries"
                        ))
                    continue

                # Procesar tarea
                self.executor.submit(self._process_sync_task, task)

                self.sync_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error en bucle de sincronización: {e}")
                time.sleep(5)

    def _process_sync_task(self, task: SyncTask):
        """Procesar una tarea de sincronización."""
        start_time = time.time()

        try:
            if task.direction == SyncDirection.UPLOAD:
                result = self._upload_data(task)
            elif task.direction == SyncDirection.DOWNLOAD:
                result = self._download_data(task)
            else:
                result = SyncResult(
                    task_id=task.task_id,
                    success=False,
                    data_size_bytes=0,
                    transfer_time_seconds=time.time() - start_time,
                    error="Unsupported sync direction"
                )

            # Actualizar estadísticas
            self._update_sync_stats(result)

            # Notificar resultado
            self._notify_sync_result(result)

            # Limpiar del buffer
            self.sync_buffer.remove_task(task.task_id)

        except Exception as e:
            logger.error(f"❌ Error procesando tarea {task.task_id}: {e}")

            result = SyncResult(
                task_id=task.task_id,
                success=False,
                data_size_bytes=0,
                transfer_time_seconds=time.time() - start_time,
                error=str(e)
            )

            self._notify_sync_result(result)

    def _upload_data(self, task: SyncTask) -> SyncResult:
        """Subir datos al nodo central."""
        try:
            # Serializar datos
            data_bytes = self._serialize_data(task.data)

            # Comprimir
            compressed_data, compression_alg = self.compressor.compress(data_bytes)

            # Preparar payload
            payload = {
                "device_id": self.config.device_id,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "data": compressed_data.hex(),
                "compression": compression_alg,
                "metadata": task.metadata,
                "timestamp": time.time()
            }

            # Enviar solicitud
            headers = {"Content-Type": "application/json"}
            if self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"

            response = requests.post(
                f"{self.config.central_node_url}/sync/upload",
                json=payload,
                headers=headers,
                timeout=self.config.connection_timeout_seconds
            )

            if response.status_code == 200:
                return SyncResult(
                    task_id=task.task_id,
                    success=True,
                    data_size_bytes=len(compressed_data),
                    transfer_time_seconds=time.time() - task.created_at,
                    metadata={"compression_ratio": len(data_bytes) / len(compressed_data) if len(compressed_data) > 0 else 1.0}
                )
            else:
                return SyncResult(
                    task_id=task.task_id,
                    success=False,
                    data_size_bytes=0,
                    transfer_time_seconds=time.time() - task.created_at,
                    error=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            return SyncResult(
                task_id=task.task_id,
                success=False,
                data_size_bytes=0,
                transfer_time_seconds=time.time() - task.created_at,
                error=str(e)
            )

    def _download_data(self, task: SyncTask) -> SyncResult:
        """Descargar datos desde el nodo central."""
        try:
            # Preparar parámetros de solicitud
            params = {
                "device_id": self.config.device_id,
                "task_id": task.task_id,
                "task_type": task.task_type
            }
            params.update(task.metadata)

            # Enviar solicitud
            headers = {}
            if self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"

            response = requests.get(
                f"{self.config.central_node_url}/sync/download",
                params=params,
                headers=headers,
                timeout=self.config.connection_timeout_seconds
            )

            if response.status_code == 200:
                response_data = response.json()

                # Descomprimir datos
                compressed_data = bytes.fromhex(response_data["data"])
                decompressed_data = self.compressor.decompress(
                    compressed_data,
                    response_data.get("compression", "none")
                )

                # Deserializar
                data = self._deserialize_data(decompressed_data, response_data.get("data_type"))

                return SyncResult(
                    task_id=task.task_id,
                    success=True,
                    data_size_bytes=len(decompressed_data),
                    transfer_time_seconds=time.time() - task.created_at,
                    metadata={"downloaded_data": data}
                )
            else:
                return SyncResult(
                    task_id=task.task_id,
                    success=False,
                    data_size_bytes=0,
                    transfer_time_seconds=time.time() - task.created_at,
                    error=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            return SyncResult(
                task_id=task.task_id,
                success=False,
                data_size_bytes=0,
                transfer_time_seconds=time.time() - task.created_at,
                error=str(e)
            )

    def _serialize_data(self, data: Any) -> bytes:
        """Serializar datos para transmisión."""
        if isinstance(data, torch.Tensor):
            return data.detach().cpu().numpy().tobytes()
        elif isinstance(data, dict):
            return json.dumps(data).encode()
        elif isinstance(data, (bytes, bytearray)):
            return bytes(data)
        else:
            return str(data).encode()

    def _deserialize_data(self, data: bytes, data_type: str) -> Any:
        """Deserializar datos recibidos."""
        if data_type == "model":
            # Simular deserialización de modelo
            return {"model_data": data[:100]}  # Placeholder
        elif data_type == "json":
            return json.loads(data.decode())
        else:
            return data

    def _ensure_connection(self) -> bool:
        """Asegurar que hay conexión con el nodo central."""
        with self.connection_lock:
            if self.connection_state == ConnectionState.CONNECTED:
                return True

            try:
                # Verificar conectividad
                socket.create_connection(
                    (self.config.central_node_url.split("://")[-1].split("/")[0], 80),
                    timeout=5
                )

                if self.connection_state != ConnectionState.CONNECTED:
                    self.connection_state = ConnectionState.CONNECTED
                    self.last_connection_time = time.time()
                    self._notify_connection_change(True)

                return True

            except:
                if self.connection_state == ConnectionState.CONNECTED:
                    self.connection_state = ConnectionState.DISCONNECTED
                    self.stats["connection_drops"] += 1
                    self._notify_connection_change(False)

                return False

    def _notify_connection_change(self, connected: bool):
        """Notificar cambio de estado de conexión."""
        for callback in self.connection_callbacks:
            try:
                callback(connected, self.connection_state.value)
            except Exception as e:
                logger.warning(f"⚠️ Error en callback de conexión: {e}")

    def _notify_sync_result(self, result: SyncResult):
        """Notificar resultado de sincronización."""
        for callback in self.sync_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.warning(f"⚠️ Error en callback de sincronización: {e}")

    def _update_sync_stats(self, result: SyncResult):
        """Actualizar estadísticas de sincronización."""
        self.stats["total_syncs"] += 1

        if result.success:
            self.stats["successful_syncs"] += 1
            if "bytes_uploaded" in result.metadata:
                self.stats["bytes_uploaded"] += result.data_size_bytes
            else:
                self.stats["bytes_downloaded"] += result.data_size_bytes

            if "compression_ratio" in result.metadata:
                # Actualizar ratio de compresión promedio
                current_ratio = self.stats["compression_ratio"]
                self.stats["compression_ratio"] = (current_ratio + result.metadata["compression_ratio"]) / 2
        else:
            self.stats["failed_syncs"] += 1

        # Actualizar tiempo promedio de sincronización
        current_avg = self.stats["avg_sync_time_seconds"]
        self.stats["avg_sync_time_seconds"] = (current_avg + result.transfer_time_seconds) / 2

    def _monitor_loop(self):
        """Bucle de monitoreo de sincronización."""
        while True:
            try:
                time.sleep(60)  # Monitorear cada minuto

                status = self.get_sync_status()

                # Log de estado
                logger.info(f"📊 Estado de sincronización: {status['connection_state']}")
                logger.info(f"   Tareas buffer: {status['buffered_tasks']}")
                logger.info(f"   Cola pendiente: {status['pending_queue_size']}")
                logger.info(f"   Ratio compresión: {status['stats']['compression_ratio']:.2f}")

            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")

    def _heartbeat_loop(self):
        """Bucle de heartbeat con nodo central."""
        while True:
            try:
                time.sleep(self.config.heartbeat_interval_seconds)

                if self.connection_state == ConnectionState.CONNECTED:
                    # Enviar heartbeat
                    heartbeat_data = {
                        "device_id": self.config.device_id,
                        "timestamp": time.time(),
                        "status": "active"
                    }

                    headers = {"Content-Type": "application/json"}
                    if self.config.auth_token:
                        headers["Authorization"] = f"Bearer {self.config.auth_token}"

                    try:
                        response = requests.post(
                            f"{self.config.central_node_url}/heartbeat",
                            json=heartbeat_data,
                            headers=headers,
                            timeout=10
                        )

                        if response.status_code != 200:
                            logger.warning(f"⚠️ Heartbeat fallido: HTTP {response.status_code}")

                    except Exception as e:
                        logger.warning(f"⚠️ Error en heartbeat: {e}")
                        self.connection_state = ConnectionState.DISCONNECTED

            except Exception as e:
                logger.error(f"❌ Error en heartbeat loop: {e}")


# Funciones de conveniencia
def create_edge_sync_for_mobile(
    central_url: str,
    device_id: str,
    auth_token: Optional[str] = None
) -> EdgeSynchronization:
    """
    Crear sincronización optimizada para dispositivos móviles.

    Args:
        central_url: URL del nodo central
        device_id: ID único del dispositivo
        auth_token: Token de autenticación opcional

    Returns:
        Sistema de sincronización configurado
    """
    config = EdgeSynchronizationConfig(
        central_node_url=central_url,
        device_id=device_id,
        auth_token=auth_token,
        sync_interval_seconds=600,  # 10 minutos para móviles
        max_concurrent_syncs=1,
        enable_compression=True,
        max_buffer_size_mb=20  # Menos buffer para móviles
    )

    return EdgeSynchronization(config)


def create_edge_sync_for_iot(
    central_url: str,
    device_id: str,
    auth_token: Optional[str] = None
) -> EdgeSynchronization:
    """
    Crear sincronización optimizada para dispositivos IoT.

    Args:
        central_url: URL del nodo central
        device_id: ID único del dispositivo
        auth_token: Token de autenticación opcional

    Returns:
        Sistema de sincronización configurado
    """
    config = EdgeSynchronizationConfig(
        central_node_url=central_url,
        device_id=device_id,
        auth_token=auth_token,
        sync_interval_seconds=1800,  # 30 minutos para IoT
        max_concurrent_syncs=1,
        enable_compression=True,
        max_buffer_size_mb=10,  # Buffer pequeño para IoT
        max_bandwidth_mbps=1.0  # Ancho de banda limitado
    )

    return EdgeSynchronization(config)


if __name__ == "__main__":
    # Demo de sincronización edge
    print("🚀 EdgeSynchronization Demo")

    # Crear sincronización
    sync = create_edge_sync_for_mobile(
        central_url="https://central.ailoos.example.com",
        device_id="mobile_device_001"
    )

    print("Sistema de sincronización creado")
    print(f"Nodo central: {sync.config.central_node_url}")
    print(f"Device ID: {sync.config.device_id}")

    # Simular sincronización de métricas
    metrics = {
        "inference_count": 100,
        "avg_latency_ms": 50.0,
        "memory_usage_mb": 150.0
    }

    task_id = sync.sync_metrics(metrics)
    print(f"Tarea de sincronización creada: {task_id}")

    # Obtener estado
    status = sync.get_sync_status()
    print(f"Estado: {status['connection_state']}")
    print(f"Tareas buffer: {status['buffered_tasks']}")

    print("Demo completado")