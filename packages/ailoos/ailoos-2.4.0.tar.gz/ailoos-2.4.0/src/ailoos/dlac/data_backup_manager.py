#!/usr/bin/env python3
"""
Data Backup Manager - Gestión de backups y redundancia para DLAC
"""

import asyncio
import threading
import time
import json
import os
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib

from ..utils.logging import get_logger

logger = get_logger(__name__)


class BackupType(Enum):
    """Tipos de backup."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupStatus(Enum):
    """Estados de backup."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"


class RetentionPolicy(Enum):
    """Políticas de retención."""
    KEEP_ALL = "keep_all"
    KEEP_LAST_N = "keep_last_n"
    KEEP_DAILY_FOR_N_DAYS = "keep_daily_for_n_days"
    KEEP_WEEKLY_FOR_N_WEEKS = "keep_weekly_for_n_weeks"
    KEEP_MONTHLY_FOR_N_MONTHS = "keep_monthly_for_n_months"


@dataclass
class BackupInfo:
    """Información de un backup."""
    backup_id: str
    data_id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    storage_location: Optional[str] = None  # IPFS CID, file path, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_count: int = 0
    last_verified: Optional[datetime] = None
    retention_until: Optional[datetime] = None


@dataclass
class BackupPolicy:
    """Política de backup."""
    policy_id: str
    data_id: str
    backup_type: BackupType
    schedule_cron: str  # Expresión cron
    retention_policy: RetentionPolicy
    retention_value: int = 30  # Días, cantidad, etc.
    enabled: bool = True
    max_concurrent_backups: int = 1
    compression_enabled: bool = True
    encryption_enabled: bool = False
    verification_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupResult:
    """Resultado de una operación de backup."""
    success: bool
    backup_id: str
    data_id: str
    size_bytes: int
    duration: float
    checksum: str
    storage_location: str
    error_message: Optional[str] = None


class DataBackupManager:
    """
    Gestor de backups y redundancia para datos en entornos federados P2P.

    Características:
    - Backups automáticos programados
    - Múltiples estrategias de backup
    - Almacenamiento distribuido con IPFS
    - Políticas de retención configurables
    - Verificación de integridad
    - Recuperación de datos
    """

    def __init__(self,
                 backup_directory: str = "./backups",
                 ipfs_client: Optional[Any] = None,
                 max_concurrent_backups: int = 3,
                 alert_callback: Optional[Callable] = None):
        """
        Inicializar gestor de backups.

        Args:
            backup_directory: Directorio para backups locales
            ipfs_client: Cliente IPFS para almacenamiento distribuido
            max_concurrent_backups: Máximo número de backups concurrentes
            alert_callback: Función para alertas
        """
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        self.ipfs_client = ipfs_client
        self.max_concurrent_backups = max_concurrent_backups
        self.alert_callback = alert_callback

        # Almacenamiento de backups y políticas
        self.backups: Dict[str, BackupInfo] = {}
        self.backup_policies: Dict[str, BackupPolicy] = {}
        self.backup_queue = []  # Usar lista en lugar de asyncio.Queue para evitar problemas de event loop

        # Estado del sistema
        self.is_running = False
        self.backup_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Estadísticas
        self.stats = {
            'total_backups_created': 0,
            'total_backups_verified': 0,
            'total_backups_failed': 0,
            'total_bytes_backed_up': 0,
            'total_recovery_operations': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'last_backup_time': None
        }

        logger.info("💾 Data Backup Manager initialized")

    def create_backup_policy(self, data_id: str, backup_type: BackupType = BackupType.FULL,
                           schedule_cron: str = "0 2 * * *",  # Daily at 2 AM
                           retention_policy: RetentionPolicy = RetentionPolicy.KEEP_LAST_N,
                           retention_value: int = 30) -> str:
        """
        Crear política de backup.

        Args:
            data_id: ID de los datos a respaldar
            backup_type: Tipo de backup
            schedule_cron: Expresión cron para el schedule
            retention_policy: Política de retención
            retention_value: Valor para la política de retención

        Returns:
            ID de la política creada
        """
        policy_id = f"policy_{data_id}_{int(time.time())}"

        policy = BackupPolicy(
            policy_id=policy_id,
            data_id=data_id,
            backup_type=backup_type,
            schedule_cron=schedule_cron,
            retention_policy=retention_policy,
            retention_value=retention_value
        )

        self.backup_policies[policy_id] = policy
        logger.info(f"📋 Created backup policy {policy_id} for data {data_id}")
        return policy_id

    def remove_backup_policy(self, policy_id: str) -> bool:
        """
        Remover política de backup.

        Args:
            policy_id: ID de la política

        Returns:
            True si se removió exitosamente
        """
        if policy_id in self.backup_policies:
            del self.backup_policies[policy_id]
            logger.info(f"🗑️ Removed backup policy {policy_id}")
            return True
        return False

    async def create_backup(self, data_id: str, data: Any,
                          backup_type: BackupType = BackupType.FULL,
                          metadata: Dict[str, Any] = None) -> BackupResult:
        """
        Crear backup de datos.

        Args:
            data_id: ID de los datos
            data: Los datos a respaldar
            backup_type: Tipo de backup
            metadata: Metadatos adicionales

        Returns:
            Resultado del backup
        """
        backup_id = f"backup_{data_id}_{int(time.time())}"
        start_time = time.time()

        try:
            logger.info(f"💾 Starting backup {backup_id} for data {data_id}")

            # Preparar datos para backup
            backup_data = self._prepare_backup_data(data, metadata or {})

            # Calcular checksum
            checksum = self._calculate_checksum(backup_data)

            # Almacenar backup
            storage_location = await self._store_backup_data(backup_data, backup_id, data_id)

            # Crear información del backup
            backup_info = BackupInfo(
                backup_id=backup_id,
                data_id=data_id,
                backup_type=backup_type,
                status=BackupStatus.COMPLETED,
                created_at=datetime.now(),
                completed_at=datetime.now(),
                size_bytes=len(backup_data),
                checksum=checksum,
                storage_location=storage_location,
                metadata=metadata or {}
            )

            self.backups[backup_id] = backup_info

            # Actualizar estadísticas
            self.stats['total_backups_created'] += 1
            self.stats['total_bytes_backed_up'] += len(backup_data)
            self.stats['last_backup_time'] = datetime.now()

            duration = time.time() - start_time
            logger.info(f"✅ Backup {backup_id} completed successfully in {duration:.2f}s")

            return BackupResult(
                success=True,
                backup_id=backup_id,
                data_id=data_id,
                size_bytes=len(backup_data),
                duration=duration,
                checksum=checksum,
                storage_location=storage_location
            )

        except Exception as e:
            logger.error(f"❌ Backup {backup_id} failed: {e}")
            self.stats['total_backups_failed'] += 1

            return BackupResult(
                success=False,
                backup_id=backup_id,
                data_id=data_id,
                size_bytes=0,
                duration=time.time() - start_time,
                checksum="",
                storage_location="",
                error_message=str(e)
            )

    async def restore_data(self, data_id: str, backup_id: Optional[str] = None) -> Optional[Any]:
        """
        Restaurar datos desde backup.

        Args:
            data_id: ID de los datos
            backup_id: ID específico del backup (opcional, usa el más reciente si no se especifica)

        Returns:
            Datos restaurados o None si falla
        """
        try:
            # Encontrar backup
            if backup_id:
                backup_info = self.backups.get(backup_id)
                if not backup_info or backup_info.data_id != data_id:
                    logger.error(f"❌ Backup {backup_id} not found for data {data_id}")
                    return None
            else:
                # Encontrar el backup más reciente
                available_backups = [b for b in self.backups.values()
                                   if b.data_id == data_id and b.status == BackupStatus.VERIFIED]
                if not available_backups:
                    logger.error(f"❌ No verified backups found for data {data_id}")
                    return None

                backup_info = max(available_backups, key=lambda b: b.created_at)

            logger.info(f"🔄 Restoring data {data_id} from backup {backup_info.backup_id}")

            # Recuperar datos
            restored_data = await self._retrieve_backup_data(backup_info)

            if restored_data:
                # Verificar integridad
                if self._verify_backup_integrity(restored_data, backup_info.checksum):
                    self.stats['total_recovery_operations'] += 1
                    self.stats['successful_recoveries'] += 1
                    logger.info(f"✅ Data {data_id} restored successfully")
                    return restored_data
                else:
                    logger.error(f"❌ Integrity verification failed for restored data {data_id}")
                    self.stats['failed_recoveries'] += 1
                    return None
            else:
                logger.error(f"❌ Failed to retrieve backup data for {data_id}")
                self.stats['failed_recoveries'] += 1
                return None

        except Exception as e:
            logger.error(f"❌ Restore operation failed for {data_id}: {e}")
            self.stats['failed_recoveries'] += 1
            return None

    async def verify_backup(self, backup_id: str) -> bool:
        """
        Verificar integridad de un backup.

        Args:
            backup_id: ID del backup

        Returns:
            True si el backup es íntegro
        """
        backup_info = self.backups.get(backup_id)
        if not backup_info:
            logger.error(f"❌ Backup {backup_id} not found")
            return False

        try:
            logger.info(f"🔍 Verifying backup {backup_id}")

            # Recuperar datos
            backup_data = await self._retrieve_backup_data(backup_info)
            if not backup_data:
                backup_info.status = BackupStatus.CORRUPTED
                return False

            # Verificar checksum
            if self._verify_backup_integrity(backup_data, backup_info.checksum):
                backup_info.status = BackupStatus.VERIFIED
                backup_info.verification_count += 1
                backup_info.last_verified = datetime.now()

                self.stats['total_backups_verified'] += 1
                logger.info(f"✅ Backup {backup_id} verified successfully")
                return True
            else:
                backup_info.status = BackupStatus.CORRUPTED
                logger.error(f"❌ Backup {backup_id} integrity check failed")
                return False

        except Exception as e:
            logger.error(f"❌ Backup verification failed for {backup_id}: {e}")
            backup_info.status = BackupStatus.CORRUPTED
            return False

    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de un backup.

        Args:
            backup_id: ID del backup

        Returns:
            Información del backup
        """
        backup = self.backups.get(backup_id)
        if not backup:
            return None

        return {
            'backup_id': backup.backup_id,
            'data_id': backup.data_id,
            'backup_type': backup.backup_type.value,
            'status': backup.status.value,
            'created_at': backup.created_at.isoformat(),
            'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
            'size_bytes': backup.size_bytes,
            'checksum': backup.checksum,
            'storage_location': backup.storage_location,
            'verification_count': backup.verification_count,
            'last_verified': backup.last_verified.isoformat() if backup.last_verified else None,
            'metadata': backup.metadata
        }

    def list_backups(self, data_id: Optional[str] = None,
                    status_filter: List[BackupStatus] = None) -> List[Dict[str, Any]]:
        """
        Listar backups.

        Args:
            data_id: Filtrar por ID de datos
            status_filter: Filtrar por estado

        Returns:
            Lista de backups
        """
        backups = list(self.backups.values())

        if data_id:
            backups = [b for b in backups if b.data_id == data_id]

        if status_filter:
            backups = [b for b in backups if b.status in status_filter]

        # Ordenar por fecha de creación descendente
        backups.sort(key=lambda b: b.created_at, reverse=True)

        return [self._backup_to_dict(b) for b in backups]

    async def cleanup_old_backups(self):
        """Limpiar backups antiguos según políticas de retención."""
        try:
            logger.info("🧹 Starting backup cleanup")

            cleaned_count = 0
            for policy in self.backup_policies.values():
                if not policy.enabled:
                    continue

                # Obtener backups para esta política
                policy_backups = [b for b in self.backups.values() if b.data_id == policy.data_id]
                policy_backups.sort(key=lambda b: b.created_at, reverse=True)

                # Aplicar política de retención
                to_delete = self._apply_retention_policy(policy_backups, policy)

                # Eliminar backups
                for backup in to_delete:
                    await self._delete_backup(backup)
                    cleaned_count += 1

            logger.info(f"🧹 Backup cleanup completed: {cleaned_count} backups removed")

        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")

    def _apply_retention_policy(self, backups: List[BackupInfo], policy: BackupPolicy) -> List[BackupInfo]:
        """Aplicar política de retención a una lista de backups."""
        if policy.retention_policy == RetentionPolicy.KEEP_ALL:
            return []
        elif policy.retention_policy == RetentionPolicy.KEEP_LAST_N:
            return backups[policy.retention_value:]
        elif policy.retention_policy == RetentionPolicy.KEEP_DAILY_FOR_N_DAYS:
            # Implementación simplificada
            cutoff = datetime.now() - timedelta(days=policy.retention_value)
            return [b for b in backups if b.created_at < cutoff]
        elif policy.retention_policy == RetentionPolicy.KEEP_WEEKLY_FOR_N_WEEKS:
            # Implementación simplificada
            cutoff = datetime.now() - timedelta(weeks=policy.retention_value)
            return [b for b in backups if b.created_at < cutoff]
        elif policy.retention_policy == RetentionPolicy.KEEP_MONTHLY_FOR_N_MONTHS:
            # Implementación simplificada
            cutoff = datetime.now() - timedelta(days=policy.retention_value * 30)
            return [b for b in backups if b.created_at < cutoff]

        return []

    def start_backup_manager(self):
        """Iniciar gestor de backups."""
        if self.is_running:
            logger.warning("⚠️ Backup manager already running")
            return

        self.is_running = True
        self.stop_event.clear()
        self.backup_thread = threading.Thread(target=self._backup_worker, daemon=True)
        self.backup_thread.start()

        logger.info("🚀 Started Data Backup Manager")

    def stop_backup_manager(self):
        """Detener gestor de backups."""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()

        if self.backup_thread:
            self.backup_thread.join(timeout=5)

        logger.info("⏹️ Stopped Data Backup Manager")

    def _backup_worker(self):
        """Worker para procesamiento de backups programados."""
        asyncio.run(self._backup_worker_async())

    async def _backup_worker_async(self):
        """Worker asíncrono para procesamiento de backups programados."""
        while not self.stop_event.is_set():
            try:
                # Procesar backups programados
                self._process_scheduled_backups()

                # Limpiar backups antiguos
                await self.cleanup_old_backups()

            except Exception as e:
                logger.error(f"❌ Backup worker error: {e}")

            # Esperar 5 minutos
            await asyncio.sleep(300)

    def _process_scheduled_backups(self):
        """Procesar backups programados."""
        # Implementación simplificada - en producción usaría un scheduler real
        current_time = datetime.now()

        for policy in self.backup_policies.values():
            if not policy.enabled:
                continue

            # Verificación simplificada de schedule (solo para demo)
            # En producción, parsear expresión cron correctamente
            if "daily" in policy.schedule_cron.lower() or "*" in policy.schedule_cron:
                # Simular backup diario
                last_backup = max((b.created_at for b in self.backups.values()
                                 if b.data_id == policy.data_id), default=None)

                if last_backup is None or (current_time - last_backup).days >= 1:
                    logger.info(f"📅 Scheduled backup triggered for data {policy.data_id}")
                    # En producción, aquí se iniciaría el backup real
                    # asyncio.run(self.create_backup(policy.data_id, ...))

    def _prepare_backup_data(self, data: Any, metadata: Dict[str, Any]) -> bytes:
        """Preparar datos para backup."""
        backup_obj = {
            'data': data,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }

        return json.dumps(backup_obj, ensure_ascii=False).encode('utf-8')

    def _calculate_checksum(self, data: bytes) -> str:
        """Calcular checksum de datos."""
        return hashlib.sha256(data).hexdigest()

    def _verify_backup_integrity(self, data: bytes, expected_checksum: str) -> bool:
        """Verificar integridad de backup."""
        actual_checksum = self._calculate_checksum(data)
        return actual_checksum == expected_checksum

    async def _store_backup_data(self, data: bytes, backup_id: str, data_id: str) -> str:
        """Almacenar datos de backup."""
        try:
            if self.ipfs_client:
                # Almacenar en IPFS
                cid = await self.ipfs_client.add_bytes(data)
                logger.info(f"📦 Backup {backup_id} stored in IPFS: {cid}")
                return f"ipfs://{cid}"
            else:
                # Almacenar localmente
                backup_path = self.backup_directory / f"{backup_id}.backup"
                with open(backup_path, 'wb') as f:
                    f.write(data)
                logger.info(f"📦 Backup {backup_id} stored locally: {backup_path}")
                return str(backup_path)

        except Exception as e:
            logger.error(f"❌ Failed to store backup {backup_id}: {e}")
            raise

    async def _retrieve_backup_data(self, backup_info: BackupInfo) -> Optional[bytes]:
        """Recuperar datos de backup."""
        try:
            storage_location = backup_info.storage_location

            if storage_location.startswith('ipfs://'):
                if not self.ipfs_client:
                    raise ValueError("IPFS client not available for IPFS backup retrieval")

                cid = storage_location[7:]  # Remove 'ipfs://'
                data = await self.ipfs_client.cat(cid)
                return data

            else:
                # Recuperar de archivo local
                backup_path = Path(storage_location)
                if backup_path.exists():
                    with open(backup_path, 'rb') as f:
                        return f.read()
                else:
                    raise FileNotFoundError(f"Backup file not found: {backup_path}")

        except Exception as e:
            logger.error(f"❌ Failed to retrieve backup {backup_info.backup_id}: {e}")
            return None

    async def _delete_backup(self, backup_info: BackupInfo):
        """Eliminar backup."""
        try:
            storage_location = backup_info.storage_location

            if storage_location.startswith('ipfs://'):
                # Para IPFS, solo removemos de nuestro registro
                # Los datos permanecen en la red hasta que expire el pin
                logger.info(f"🗑️ Marked IPFS backup {backup_info.backup_id} for cleanup")
            else:
                # Eliminar archivo local
                backup_path = Path(storage_location)
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"🗑️ Deleted local backup {backup_info.backup_id}")

            # Remover de registros
            del self.backups[backup_info.backup_id]

        except Exception as e:
            logger.error(f"❌ Failed to delete backup {backup_info.backup_id}: {e}")

    def _backup_to_dict(self, backup: BackupInfo) -> Dict[str, Any]:
        """Convertir backup a diccionario."""
        return {
            'backup_id': backup.backup_id,
            'data_id': backup.data_id,
            'backup_type': backup.backup_type.value,
            'status': backup.status.value,
            'created_at': backup.created_at.isoformat(),
            'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
            'size_bytes': backup.size_bytes,
            'checksum': backup.checksum,
            'storage_location': backup.storage_location,
            'verification_count': backup.verification_count,
            'last_verified': backup.last_verified.isoformat() if backup.last_verified else None,
            'metadata': backup.metadata
        }

    def list_backups(self, data_id: str) -> List[Dict[str, Any]]:
        """
        Listar backups para datos específicos.

        Args:
            data_id: ID de los datos

        Returns:
            Lista de backups
        """
        backups = [b for b in self.backups.values() if b.data_id == data_id]
        return [self._backup_to_dict(b) for b in backups]

    def get_backup_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de backups."""
        total_backups = len(self.backups)
        verified_backups = sum(1 for b in self.backups.values() if b.status == BackupStatus.VERIFIED)
        corrupted_backups = sum(1 for b in self.backups.values() if b.status == BackupStatus.CORRUPTED)

        return {
            **self.stats,
            'total_backups': total_backups,
            'verified_backups': verified_backups,
            'corrupted_backups': corrupted_backups,
            'active_policies': sum(1 for p in self.backup_policies.values() if p.enabled),
            'is_running': self.is_running
        }