"""
Capacidades offline con sincronización diferida para dispositivos edge.

Permite funcionamiento completo sin conectividad, almacenando datos localmente
y sincronizando automáticamente cuando se restaure la conexión.
"""

import torch
import logging
import time
import threading
import json
import zlib
import hashlib
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import queue
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class OfflineOperation(Enum):
    """Tipos de operaciones offline."""
    INFERENCE = "inference"
    TRAINING = "training"
    METRICS_SYNC = "metrics_sync"
    MODEL_UPDATE = "model_update"
    DATA_COLLECTION = "data_collection"
    FEDERATED_UPDATE = "federated_update"


class SyncConflictResolution(Enum):
    """Estrategias de resolución de conflictos."""
    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    MERGE = "merge"
    MANUAL = "manual"


class ConnectivityState(Enum):
    """Estados de conectividad."""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    LIMITED = "limited"  # Conectividad limitada (solo datos críticos)


@dataclass
class OfflineData:
    """Datos almacenados offline."""
    id: str
    operation_type: OfflineOperation
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    priority: int = 1  # 1=baja, 5=alta
    compressed: bool = False
    size_bytes: int = 0
    checksum: str = ""


@dataclass
class SyncOperation:
    """Operación de sincronización."""
    operation_id: str
    offline_data_id: str
    sync_attempts: int = 0
    last_attempt: Optional[float] = None
    next_attempt: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None
    server_response: Optional[Dict[str, Any]] = None


@dataclass
class OfflineCapabilitiesConfig:
    """Configuración de capacidades offline."""
    # Almacenamiento
    storage_path: str = "./offline_data"
    max_storage_mb: int = 500
    enable_compression: bool = True

    # Cola de operaciones
    max_queue_size: int = 1000
    operation_timeout_hours: int = 24

    # Sincronización
    sync_interval_seconds: int = 300  # 5 minutos
    max_sync_attempts: int = 5
    sync_batch_size: int = 10

    # Conectividad
    connectivity_check_interval_seconds: int = 30
    enable_auto_sync: bool = True

    # Conflictos
    default_conflict_resolution: SyncConflictResolution = SyncConflictResolution.CLIENT_WINS

    # Monitoreo
    enable_offline_monitoring: bool = True
    cleanup_interval_hours: int = 6


class OfflineStorage:
    """Almacenamiento local para datos offline."""

    def __init__(self, config: OfflineCapabilitiesConfig):
        self.config = config
        self.db_path = Path(config.storage_path) / "offline.db"
        self.data_dir = Path(config.storage_path) / "data"

        # Crear directorios
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar base de datos
        self._init_database()

    def _init_database(self):
        """Inicializar base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS offline_data (
                    id TEXT PRIMARY KEY,
                    operation_type TEXT,
                    metadata TEXT,
                    created_at REAL,
                    priority INTEGER,
                    compressed BOOLEAN,
                    size_bytes INTEGER,
                    checksum TEXT,
                    data_path TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_operations (
                    operation_id TEXT PRIMARY KEY,
                    offline_data_id TEXT,
                    sync_attempts INTEGER,
                    last_attempt REAL,
                    next_attempt REAL,
                    status TEXT,
                    error TEXT,
                    server_response TEXT,
                    FOREIGN KEY (offline_data_id) REFERENCES offline_data(id)
                )
            ''')

    def store_data(self, data: OfflineData) -> bool:
        """Almacenar datos offline."""
        try:
            # Verificar espacio disponible
            if not self._check_storage_space(data.size_bytes):
                logger.warning("⚠️ Espacio insuficiente para almacenar datos offline")
                return False

            # Preparar datos para almacenamiento
            data_path = None
            if isinstance(data.data, (bytes, bytearray)):
                # Almacenar como archivo
                data_path = self.data_dir / f"{data.id}.bin"
                with open(data_path, 'wb') as f:
                    f.write(data.data)
            else:
                # Serializar y almacenar
                serialized = json.dumps(data.data, default=str)
                if self.config.enable_compression:
                    compressed = zlib.compress(serialized.encode())
                    data_path = self.data_dir / f"{data.id}.json.zlib"
                    with open(data_path, 'wb') as f:
                        f.write(compressed)
                    data.compressed = True
                    data.size_bytes = len(compressed)
                else:
                    data_path = self.data_dir / f"{data.id}.json"
                    with open(data_path, 'w') as f:
                        f.write(serialized)
                    data.size_bytes = len(serialized.encode())

            # Calcular checksum
            data.checksum = self._calculate_checksum(data_path)

            # Almacenar en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO offline_data
                    (id, operation_type, metadata, created_at, priority, compressed, size_bytes, checksum, data_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.id,
                    data.operation_type.value,
                    json.dumps(data.metadata),
                    data.created_at,
                    data.priority,
                    data.compressed,
                    data.size_bytes,
                    data.checksum,
                    str(data_path.relative_to(self.config.storage_path))
                ))

            return True

        except Exception as e:
            logger.error(f"❌ Error almacenando datos offline: {e}")
            return False

    def retrieve_data(self, data_id: str) -> Optional[OfflineData]:
        """Recuperar datos offline."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute('''
                    SELECT * FROM offline_data WHERE id = ?
                ''', (data_id,)).fetchone()

            if not row:
                return None

            # Reconstruir objeto
            data_path = Path(self.config.storage_path) / row[8]  # data_path

            if not data_path.exists():
                logger.error(f"❌ Archivo de datos no encontrado: {data_path}")
                return None

            # Leer datos
            if row[5]:  # compressed
                with open(data_path, 'rb') as f:
                    compressed_data = f.read()
                data_content = json.loads(zlib.decompress(compressed_data).decode())
            else:
                with open(data_path, 'r') as f:
                    data_content = json.loads(f.read())

            return OfflineData(
                id=row[0],
                operation_type=OfflineOperation(row[1]),
                data=data_content,
                metadata=json.loads(row[2]),
                created_at=row[3],
                priority=row[4],
                compressed=row[5],
                size_bytes=row[6],
                checksum=row[7]
            )

        except Exception as e:
            logger.error(f"❌ Error recuperando datos offline: {e}")
            return None

    def get_pending_operations(self, limit: Optional[int] = None) -> List[OfflineData]:
        """Obtener operaciones pendientes de sincronización."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute('''
                    SELECT od.* FROM offline_data od
                    LEFT JOIN sync_operations so ON od.id = so.offline_data_id
                    WHERE so.operation_id IS NULL OR so.status != 'completed'
                    ORDER BY od.priority DESC, od.created_at ASC
                    LIMIT ?
                ''', (limit or self.config.max_queue_size,)).fetchall()

            operations = []
            for row in rows:
                data_path = Path(self.config.storage_path) / row[8]
                if data_path.exists():
                    operations.append(self._row_to_offline_data(row))

            return operations

        except Exception as e:
            logger.error(f"❌ Error obteniendo operaciones pendientes: {e}")
            return []

    def mark_operation_synced(self, data_id: str, sync_result: Dict[str, Any]):
        """Marcar operación como sincronizada."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE sync_operations
                    SET status = 'completed', server_response = ?
                    WHERE offline_data_id = ?
                ''', (json.dumps(sync_result), data_id))

        except Exception as e:
            logger.error(f"❌ Error marcando operación como sincronizada: {e}")

    def cleanup_old_data(self, max_age_hours: int):
        """Limpiar datos antiguos."""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)

            with sqlite3.connect(self.db_path) as conn:
                # Obtener IDs de datos antiguos
                old_rows = conn.execute('''
                    SELECT id, data_path FROM offline_data
                    WHERE created_at < ?
                ''', (cutoff_time,)).fetchall()

                # Eliminar archivos
                for row in old_rows:
                    data_path = Path(self.config.storage_path) / row[1]
                    try:
                        data_path.unlink(missing_ok=True)
                    except:
                        pass

                # Eliminar de base de datos
                conn.execute('DELETE FROM offline_data WHERE created_at < ?', (cutoff_time,))
                conn.execute('DELETE FROM sync_operations WHERE offline_data_id NOT IN (SELECT id FROM offline_data)')

            logger.info(f"🧹 Limpiados {len(old_rows)} datos antiguos")

        except Exception as e:
            logger.error(f"❌ Error limpiando datos antiguos: {e}")

    def _check_storage_space(self, required_bytes: int) -> bool:
        """Verificar espacio de almacenamiento disponible."""
        try:
            # Calcular uso actual
            total_size = 0
            for file_path in self.data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            # Verificar límite
            max_bytes = self.config.max_storage_mb * 1024 * 1024
            return (total_size + required_bytes) <= max_bytes

        except Exception:
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcular checksum de archivo."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _row_to_offline_data(self, row) -> OfflineData:
        """Convertir fila de base de datos a OfflineData."""
        return OfflineData(
            id=row[0],
            operation_type=OfflineOperation(row[1]),
            data=None,  # Se carga bajo demanda
            metadata=json.loads(row[2]),
            created_at=row[3],
            priority=row[4],
            compressed=row[5],
            size_bytes=row[6],
            checksum=row[7]
        )


class OfflineCapabilities:
    """
    Sistema de capacidades offline con sincronización diferida.

    Características principales:
    - Almacenamiento local de operaciones durante desconexión
    - Cola inteligente de sincronización
    - Compresión automática de datos
    - Resolución de conflictos
    - Sincronización automática al restaurar conectividad
    - Gestión eficiente de almacenamiento
    """

    def __init__(self, config: OfflineCapabilitiesConfig):
        self.config = config

        # Almacenamiento
        self.storage = OfflineStorage(config)

        # Estado de conectividad
        self.connectivity_state = ConnectivityState.OFFLINE
        self.last_connectivity_check = 0

        # Colas de sincronización
        self.sync_queue = queue.Queue(maxsize=config.max_queue_size)
        self.sync_results = queue.Queue()

        # Hilos
        self.sync_thread: Optional[threading.Thread] = None
        self.connectivity_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

        # Executor para operaciones concurrentes
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Estadísticas
        self.stats = {
            "operations_queued": 0,
            "operations_synced": 0,
            "operations_failed": 0,
            "storage_used_mb": 0.0,
            "connectivity_changes": 0,
            "compression_ratio": 1.0
        }

        # Callbacks
        self.sync_callbacks: List[Callable] = []
        self.connectivity_callbacks: List[Callable] = []

        logger.info("🔧 OfflineCapabilities inicializado")
        logger.info(f"   Almacenamiento: {config.storage_path}")
        logger.info(f"   Tamaño máximo: {config.max_storage_mb}MB")

    def start(self):
        """Iniciar capacidades offline."""
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("⚠️ OfflineCapabilities ya está ejecutándose")
            return

        # Iniciar hilos
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()

        self.connectivity_thread = threading.Thread(target=self._connectivity_loop, daemon=True)
        self.connectivity_thread.start()

        if self.config.enable_offline_monitoring:
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()

        logger.info("🚀 OfflineCapabilities iniciado")

    def stop(self):
        """Detener capacidades offline."""
        # Esperar a que terminen los hilos
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)

        if self.connectivity_thread:
            self.connectivity_thread.join(timeout=5.0)

        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5.0)

        self.executor.shutdown(wait=True)
        logger.info("🛑 OfflineCapabilities detenido")

    def queue_operation(
        self,
        operation_type: OfflineOperation,
        data: Any,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Poner en cola una operación offline.

        Args:
            operation_type: Tipo de operación
            data: Datos de la operación
            priority: Prioridad (1-5)
            metadata: Metadatos adicionales

        Returns:
            ID de la operación
        """
        operation_id = f"op_{int(time.time() * 1000)}_{hash(str(data)) % 10000}"

        offline_data = OfflineData(
            id=operation_id,
            operation_type=operation_type,
            data=data,
            metadata=metadata or {},
            priority=priority
        )

        # Almacenar localmente
        if self.storage.store_data(offline_data):
            # Agregar a cola de sincronización si está online
            if self.connectivity_state == ConnectivityState.ONLINE:
                self.sync_queue.put(operation_id)

            self.stats["operations_queued"] += 1
            logger.info(f"📋 Operación en cola: {operation_id} ({operation_type.value})")
            return operation_id
        else:
            logger.error(f"❌ Error almacenando operación: {operation_id}")
            return ""

    def get_offline_status(self) -> Dict[str, Any]:
        """Obtener estado offline."""
        return {
            "connectivity_state": self.connectivity_state.value,
            "queued_operations": self.sync_queue.qsize(),
            "pending_operations": len(self.storage.get_pending_operations()),
            "storage_used_mb": self._calculate_storage_usage(),
            "stats": self.stats.copy(),
            "last_connectivity_check": self.last_connectivity_check
        }

    def force_sync_now(self) -> bool:
        """
        Forzar sincronización inmediata.

        Returns:
            True si se inició la sincronización
        """
        if self.connectivity_state != ConnectivityState.ONLINE:
            logger.warning("⚠️ No hay conectividad para sincronización forzada")
            return False

        # Obtener operaciones pendientes
        pending_ops = self.storage.get_pending_operations(self.config.sync_batch_size)

        if not pending_ops:
            logger.info("ℹ️ No hay operaciones pendientes para sincronizar")
            return True

        # Sincronizar en background
        self.executor.submit(self._sync_operations_batch, pending_ops)
        return True

    def clear_old_data(self, max_age_hours: int = 24):
        """Limpiar datos antiguos."""
        self.storage.cleanup_old_data(max_age_hours)
        logger.info(f"🧹 Datos antiguos limpiados (>{max_age_hours}h)")

    def add_sync_callback(self, callback: Callable):
        """Agregar callback para eventos de sincronización."""
        self.sync_callbacks.append(callback)

    def add_connectivity_callback(self, callback: Callable):
        """Agregar callback para eventos de conectividad."""
        self.connectivity_callbacks.append(callback)

    def _sync_loop(self):
        """Bucle principal de sincronización."""
        logger.info("🔄 Iniciando bucle de sincronización")

        while True:
            try:
                # Esperar intervalo de sincronización
                time.sleep(self.config.sync_interval_seconds)

                # Verificar conectividad
                if self.connectivity_state != ConnectivityState.ONLINE:
                    continue

                # Obtener operaciones pendientes
                pending_ops = self.storage.get_pending_operations(self.config.sync_batch_size)

                if pending_ops:
                    self._sync_operations_batch(pending_ops)

            except Exception as e:
                logger.error(f"❌ Error en bucle de sincronización: {e}")

    def _sync_operations_batch(self, operations: List[OfflineData]):
        """Sincronizar un lote de operaciones."""
        logger.info(f"🔄 Sincronizando {len(operations)} operaciones")

        for operation in operations:
            try:
                # Recargar datos completos
                full_data = self.storage.retrieve_data(operation.id)
                if not full_data:
                    continue

                # Sincronizar operación
                success, result = self._sync_single_operation(full_data)

                if success:
                    self.storage.mark_operation_synced(operation.id, result)
                    self.stats["operations_synced"] += 1

                    # Notificar callbacks
                    for callback in self.sync_callbacks:
                        try:
                            callback(operation.id, "synced", result)
                        except Exception as e:
                            logger.warning(f"⚠️ Error en callback de sync: {e}")
                else:
                    self.stats["operations_failed"] += 1

                    # Notificar error
                    for callback in self.sync_callbacks:
                        try:
                            callback(operation.id, "failed", result)
                        except Exception as e:
                            logger.warning(f"⚠️ Error en callback de error: {e}")

            except Exception as e:
                logger.error(f"❌ Error sincronizando operación {operation.id}: {e}")
                self.stats["operations_failed"] += 1

    def _sync_single_operation(self, operation: OfflineData) -> Tuple[bool, Dict[str, Any]]:
        """Sincronizar una operación individual."""
        # En implementación real, aquí se haría la llamada al servidor central
        # Por ahora, simulamos sincronización exitosa

        try:
            # Simular procesamiento del servidor
            time.sleep(0.1)  # Simular latencia de red

            # Simular respuesta del servidor
            if operation.operation_type == OfflineOperation.INFERENCE:
                result = {
                    "status": "processed",
                    "inference_id": operation.id,
                    "processed_at": time.time()
                }
            elif operation.operation_type == OfflineOperation.METRICS_SYNC:
                result = {
                    "status": "stored",
                    "metrics_count": len(operation.data) if isinstance(operation.data, dict) else 1,
                    "stored_at": time.time()
                }
            else:
                result = {
                    "status": "accepted",
                    "operation_type": operation.operation_type.value,
                    "processed_at": time.time()
                }

            return True, result

        except Exception as e:
            return False, {"error": str(e)}

    def _connectivity_loop(self):
        """Bucle de verificación de conectividad."""
        while True:
            try:
                time.sleep(self.config.connectivity_check_interval_seconds)

                # Verificar conectividad (simplificado)
                new_state = self._check_connectivity()

                if new_state != self.connectivity_state:
                    old_state = self.connectivity_state
                    self.connectivity_state = new_state
                    self.stats["connectivity_changes"] += 1

                    logger.info(f"📡 Conectividad cambiada: {old_state.value} -> {new_state.value}")

                    # Notificar callbacks
                    for callback in self.connectivity_callbacks:
                        try:
                            callback(new_state, old_state)
                        except Exception as e:
                            logger.warning(f"⚠️ Error en callback de conectividad: {e}")

                    # Si se restauró la conectividad, iniciar sincronización
                    if (new_state == ConnectivityState.ONLINE and
                        old_state != ConnectivityState.ONLINE and
                        self.config.enable_auto_sync):
                        self.force_sync_now()

                self.last_connectivity_check = time.time()

            except Exception as e:
                logger.error(f"❌ Error en verificación de conectividad: {e}")

    def _check_connectivity(self) -> ConnectivityState:
        """Verificar estado de conectividad."""
        # En implementación real, verificar conectividad de red
        # Por ahora, simular conectividad
        import random
        return ConnectivityState.ONLINE if random.random() > 0.3 else ConnectivityState.OFFLINE

    def _cleanup_loop(self):
        """Bucle de limpieza."""
        while True:
            try:
                time.sleep(self.config.cleanup_interval_hours * 3600)

                # Limpiar datos antiguos
                self.storage.cleanup_old_data(self.config.operation_timeout_hours)

                # Actualizar estadísticas de almacenamiento
                self.stats["storage_used_mb"] = self._calculate_storage_usage()

            except Exception as e:
                logger.error(f"❌ Error en limpieza: {e}")

    def _calculate_storage_usage(self) -> float:
        """Calcular uso de almacenamiento."""
        try:
            total_size = 0
            for file_path in Path(self.config.storage_path).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # MB
        except Exception:
            return 0.0


# Funciones de conveniencia
def create_offline_capabilities_for_mobile(
    storage_path: str = "./mobile_offline_data"
) -> OfflineCapabilities:
    """
    Crear capacidades offline optimizadas para móviles.

    Args:
        storage_path: Ruta de almacenamiento

    Returns:
        OfflineCapabilities configurado
    """
    config = OfflineCapabilitiesConfig(
        storage_path=storage_path,
        max_storage_mb=200,  # Menos almacenamiento para móviles
        sync_interval_seconds=600,  # Sincronización menos frecuente
        enable_compression=True,
        enable_auto_sync=True
    )

    return OfflineCapabilities(config)


def create_offline_capabilities_for_iot(
    storage_path: str = "./iot_offline_data"
) -> OfflineCapabilities:
    """
    Crear capacidades offline optimizadas para IoT.

    Args:
        storage_path: Ruta de almacenamiento

    Returns:
        OfflineCapabilities configurado
    """
    config = OfflineCapabilitiesConfig(
        storage_path=storage_path,
        max_storage_mb=50,  # Almacenamiento muy limitado
        sync_interval_seconds=1800,  # Sincronización muy espaciada
        enable_compression=True,
        enable_auto_sync=True,
        max_queue_size=100  # Cola más pequeña
    )

    return OfflineCapabilities(config)


if __name__ == "__main__":
    # Demo de OfflineCapabilities
    print("🚀 OfflineCapabilities Demo")

    # Crear capacidades offline
    offline = create_offline_capabilities_for_mobile()
    offline.start()

    print("OfflineCapabilities iniciado")
    print(f"Almacenamiento: {offline.config.storage_path}")
    print(f"Tamaño máximo: {offline.config.max_storage_mb}MB")

    # Simular operaciones offline
    for i in range(3):
        op_id = offline.queue_operation(
            operation_type=OfflineOperation.INFERENCE,
            data={"input": f"sample_input_{i}", "timestamp": time.time()},
            priority=2,
            metadata={"model_version": "1.0"}
        )
        print(f"Operación en cola: {op_id}")

        time.sleep(0.5)

    # Obtener estado
    status = offline.get_offline_status()
    print(f"Estado de conectividad: {status['connectivity_state']}")
    print(f"Operaciones pendientes: {status['pending_operations']}")
    print(f"Almacenamiento usado: {status['storage_used_mb']:.2f}MB")

    # Forzar sincronización
    synced = offline.force_sync_now()
    print(f"Sincronización forzada: {'Iniciada' if synced else 'No disponible'}")

    time.sleep(2)

    # Estado final
    final_status = offline.get_offline_status()
    print(f"Operaciones sincronizadas: {final_status['stats']['operations_synced']}")

    offline.stop()
    print("OfflineCapabilities detenido")