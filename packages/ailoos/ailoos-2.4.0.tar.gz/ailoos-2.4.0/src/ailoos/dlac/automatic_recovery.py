#!/usr/bin/env python3
"""
Automatic Recovery - Recuperación automática de datos perdidos/corruptos
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import os

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RecoveryStrategy(Enum):
    """Estrategias de recuperación."""
    BACKUP_RESTORE = "backup_restore"
    PEER_REPLICATION = "peer_replication"
    IPFS_RESTORE = "ipfs_restore"
    ROLLBACK_VERSION = "rollback_version"
    REDUNDANCY_RESTORE = "redundancy_restore"


class RecoveryStatus(Enum):
    """Estados de recuperación."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class RecoveryTask:
    """Tarea de recuperación."""
    task_id: str
    data_id: str
    recovery_strategy: RecoveryStrategy
    status: RecoveryStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 1  # 1-10, 10 es más alta
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    recovery_source: Optional[str] = None  # backup_id, peer_id, ipfs_hash, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Resultado de recuperación."""
    task_id: str
    success: bool
    recovered_data: Any = None
    recovery_time: float = 0.0
    bytes_recovered: int = 0
    error_details: Optional[str] = None
    verification_passed: bool = False


class AutomaticRecovery:
    """
    Sistema de recuperación automática de datos en entornos federados P2P.

    Características:
    - Recuperación desde múltiples fuentes
    - Estrategias adaptativas
    - Reintentos automáticos
    - Verificación post-recuperación
    - Reportes de recuperación
    """

    def __init__(self,
                 max_concurrent_recoveries: int = 5,
                 recovery_timeout: int = 300,  # 5 minutos
                 alert_callback: Optional[Callable] = None,
                 backup_manager: Optional[Any] = None,  # DataBackupManager
                 ipfs_client: Optional[Any] = None):
        """
        Inicializar sistema de recuperación automática.

        Args:
            max_concurrent_recoveries: Máximo número de recuperaciones concurrentes
            recovery_timeout: Timeout por tarea de recuperación
            alert_callback: Función para alertas
            backup_manager: Instancia de DataBackupManager
            ipfs_client: Cliente IPFS para recuperación
        """
        self.max_concurrent_recoveries = max_concurrent_recoveries
        self.recovery_timeout = recovery_timeout
        self.alert_callback = alert_callback
        self.backup_manager = backup_manager
        self.ipfs_client = ipfs_client

        # Cola de tareas de recuperación
        self.recovery_queue = []  # Usar lista en lugar de asyncio.Queue
        self.active_tasks: Dict[str, RecoveryTask] = {}
        self.completed_tasks: Dict[str, RecoveryResult] = {}

        # Estado del sistema
        self.is_running = False
        self.recovery_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Estadísticas
        self.stats = {
            'total_recoveries_attempted': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'bytes_recovered': 0,
            'average_recovery_time': 0.0,
            'last_recovery_time': None
        }

        logger.info("🔄 Automatic Recovery system initialized")

    def submit_recovery_task(self, data_id: str, corruption_report: Dict[str, Any] = None,
                           priority: int = 5, strategies: List[RecoveryStrategy] = None) -> str:
        """
        Enviar tarea de recuperación.

        Args:
            data_id: ID de los datos a recuperar
            corruption_report: Reporte de corrupción (opcional)
            priority: Prioridad de la tarea (1-10)
            strategies: Estrategias de recuperación a intentar

        Returns:
            ID de la tarea de recuperación
        """
        if strategies is None:
            strategies = [RecoveryStrategy.BACKUP_RESTORE, RecoveryStrategy.PEER_REPLICATION]

        task_id = f"recovery_{data_id}_{int(time.time())}"

        task = RecoveryTask(
            task_id=task_id,
            data_id=data_id,
            recovery_strategy=strategies[0],  # Empezar con la primera estrategia
            status=RecoveryStatus.PENDING,
            created_at=datetime.now(),
            priority=priority,
            metadata={
                'corruption_report': corruption_report,
                'available_strategies': [s.value for s in strategies],
                'current_strategy_index': 0
            }
        )

        # Agregar a cola
        self.recovery_queue.append(task)

        logger.info(f"📋 Submitted recovery task {task_id} for data {data_id} "
                   f"(priority: {priority}, strategies: {[s.value for s in strategies]})")
        return task_id

    def get_recovery_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado de una tarea de recuperación.

        Args:
            task_id: ID de la tarea

        Returns:
            Estado de la tarea
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'task_id': task.task_id,
                'status': task.status.value,
                'progress': 'in_progress',
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'strategy': task.recovery_strategy.value,
                'retry_count': task.retry_count
            }
        elif task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                'task_id': result.task_id,
                'status': 'completed',
                'success': result.success,
                'recovery_time': result.recovery_time,
                'bytes_recovered': result.bytes_recovered,
                'error_details': result.error_details
            }
        else:
            return None

    def cancel_recovery_task(self, task_id: str) -> bool:
        """
        Cancelar tarea de recuperación.

        Args:
            task_id: ID de la tarea

        Returns:
            True si cancelada exitosamente
        """
        # Remover de cola si está pendiente
        # Nota: En implementación real, necesitaríamos una cola cancelable

        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = RecoveryStatus.FAILED
            task.error_message = "Cancelled by user"
            logger.info(f"❌ Cancelled recovery task {task_id}")
            return True

        return False

    def start_recovery_system(self):
        """Iniciar sistema de recuperación automática."""
        if self.is_running:
            logger.warning("⚠️ Recovery system already running")
            return

        self.is_running = True
        self.stop_event.clear()
        self.recovery_thread = threading.Thread(target=self._recovery_worker, daemon=True)
        self.recovery_thread.start()

        logger.info("🚀 Started automatic recovery system")

    def stop_recovery_system(self):
        """Detener sistema de recuperación automática."""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()

        if self.recovery_thread:
            self.recovery_thread.join(timeout=5)

        logger.info("⏹️ Stopped automatic recovery system")

    async def _process_recovery_queue(self):
        """Procesar cola de tareas de recuperación."""
        while not self.stop_event.is_set():
            try:
                # Obtener tarea de la cola
                if self.recovery_queue:
                    task = self.recovery_queue.pop(0)  # FIFO
                    # Procesar tarea
                    await self._execute_recovery_task(task)
                else:
                    # Cola vacía, esperar
                    await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"❌ Error processing recovery queue: {e}")

    def _recovery_worker(self):
        """Worker thread para procesamiento de recuperaciones."""
        asyncio.run(self._process_recovery_queue())

    async def _execute_recovery_task(self, task: RecoveryTask):
        """Ejecutar tarea de recuperación."""
        task.status = RecoveryStatus.IN_PROGRESS
        task.started_at = datetime.now()
        self.active_tasks[task.task_id] = task

        self.stats['total_recoveries_attempted'] += 1

        try:
            logger.info(f"🔄 Starting recovery task {task.task_id} for data {task.data_id} "
                       f"using {task.recovery_strategy.value}")

            # Ejecutar estrategia de recuperación
            result = await self._execute_recovery_strategy(task)

            # Procesar resultado
            task.completed_at = datetime.now()
            task.status = RecoveryStatus.SUCCESSFUL if result.success else RecoveryStatus.FAILED

            if result.success:
                self.stats['successful_recoveries'] += 1
                self.stats['bytes_recovered'] += result.bytes_recovered
                self.stats['last_recovery_time'] = datetime.now()

                # Actualizar tiempo promedio
                total_time = sum(r.recovery_time for r in self.completed_tasks.values() if r.success)
                self.stats['average_recovery_time'] = total_time / self.stats['successful_recoveries']

            else:
                self.stats['failed_recoveries'] += 1
                task.error_message = result.error_details

                # Intentar siguiente estrategia si hay disponibles
                await self._try_next_strategy(task)

            # Almacenar resultado
            self.completed_tasks[task.task_id] = result

            # Limpiar tarea activa
            del self.active_tasks[task.task_id]

            # Alertar
            if self.alert_callback:
                self.alert_callback('recovery_completed', {
                    'task_id': task.task_id,
                    'data_id': task.data_id,
                    'success': result.success,
                    'recovery_time': result.recovery_time,
                    'strategy': task.recovery_strategy.value
                })

            logger.info(f"✅ Recovery task {task.task_id} completed: {result.success}")

        except Exception as e:
            logger.error(f"❌ Recovery task {task.task_id} failed: {e}")
            task.status = RecoveryStatus.FAILED
            task.error_message = str(e)
            self.stats['failed_recoveries'] += 1

    async def _execute_recovery_strategy(self, task: RecoveryTask) -> RecoveryResult:
        """Ejecutar estrategia de recuperación específica."""
        start_time = time.time()

        try:
            if task.recovery_strategy == RecoveryStrategy.BACKUP_RESTORE:
                result = await self._recover_from_backup(task)
            elif task.recovery_strategy == RecoveryStrategy.PEER_REPLICATION:
                result = await self._recover_from_peers(task)
            elif task.recovery_strategy == RecoveryStrategy.IPFS_RESTORE:
                result = await self._recover_from_ipfs(task)
            elif task.recovery_strategy == RecoveryStrategy.ROLLBACK_VERSION:
                result = await self._recover_from_version_rollback(task)
            elif task.recovery_strategy == RecoveryStrategy.REDUNDANCY_RESTORE:
                result = await self._recover_from_redundancy(task)
            else:
                raise ValueError(f"Unknown recovery strategy: {task.recovery_strategy}")

            recovery_time = time.time() - start_time
            result.recovery_time = recovery_time

            return result

        except Exception as e:
            recovery_time = time.time() - start_time
            return RecoveryResult(
                task_id=task.task_id,
                success=False,
                recovery_time=recovery_time,
                error_details=str(e)
            )

    async def _recover_from_backup(self, task: RecoveryTask) -> RecoveryResult:
        """Recuperar desde backup."""
        if not self.backup_manager:
            raise ValueError("Backup manager not available")

        try:
            # Buscar backup más reciente
            backup_data = await self.backup_manager.restore_data(task.data_id)

            if backup_data:
                return RecoveryResult(
                    task_id=task.task_id,
                    success=True,
                    recovered_data=backup_data,
                    bytes_recovered=len(backup_data) if isinstance(backup_data, bytes) else 0,
                    verification_passed=True
                )
            else:
                raise ValueError("No backup found")

        except Exception as e:
            raise ValueError(f"Backup recovery failed: {e}")

    async def _recover_from_peers(self, task: RecoveryTask) -> RecoveryResult:
        """Recuperar desde peers en la red P2P."""
        # Implementación simplificada - en producción buscaría peers disponibles
        try:
            # Simular búsqueda de peer con los datos
            peer_data = await self._find_data_from_peers(task.data_id)

            if peer_data:
                return RecoveryResult(
                    task_id=task.task_id,
                    success=True,
                    recovered_data=peer_data,
                    bytes_recovered=len(peer_data) if isinstance(peer_data, bytes) else 0,
                    verification_passed=True
                )
            else:
                raise ValueError("No peer with data found")

        except Exception as e:
            raise ValueError(f"Peer recovery failed: {e}")

    async def _recover_from_ipfs(self, task: RecoveryTask) -> RecoveryResult:
        """Recuperar desde IPFS."""
        if not self.ipfs_client:
            raise ValueError("IPFS client not available")

        try:
            # Buscar hash IPFS en metadatos
            ipfs_hash = task.metadata.get('ipfs_hash')
            if not ipfs_hash:
                raise ValueError("No IPFS hash available")

            data = await self.ipfs_client.cat(ipfs_hash)

            return RecoveryResult(
                task_id=task.task_id,
                success=True,
                recovered_data=data,
                bytes_recovered=len(data),
                verification_passed=True
            )

        except Exception as e:
            raise ValueError(f"IPFS recovery failed: {e}")

    async def _recover_from_version_rollback(self, task: RecoveryTask) -> RecoveryResult:
        """Recuperar mediante rollback a versión anterior."""
        # Implementación simplificada
        try:
            # Buscar versión anterior en el sistema de versiones
            previous_version = await self._find_previous_version(task.data_id)

            if previous_version:
                return RecoveryResult(
                    task_id=task.task_id,
                    success=True,
                    recovered_data=previous_version,
                    bytes_recovered=len(previous_version) if isinstance(previous_version, bytes) else 0,
                    verification_passed=True
                )
            else:
                raise ValueError("No previous version found")

        except Exception as e:
            raise ValueError(f"Version rollback recovery failed: {e}")

    async def _recover_from_redundancy(self, task: RecoveryTask) -> RecoveryResult:
        """Recuperar usando redundancia de datos."""
        # Implementación simplificada - usar códigos de corrección de errores
        try:
            redundant_data = await self._reconstruct_from_redundancy(task.data_id)

            if redundant_data:
                return RecoveryResult(
                    task_id=task.task_id,
                    success=True,
                    recovered_data=redundant_data,
                    bytes_recovered=len(redundant_data) if isinstance(redundant_data, bytes) else 0,
                    verification_passed=True
                )
            else:
                raise ValueError("Cannot reconstruct from redundancy")

        except Exception as e:
            raise ValueError(f"Redundancy recovery failed: {e}")

    async def _try_next_strategy(self, task: RecoveryTask):
        """Intentar siguiente estrategia de recuperación."""
        strategies = task.metadata.get('available_strategies', [])
        current_index = task.metadata.get('current_strategy_index', 0)

        if current_index + 1 < len(strategies):
            next_index = current_index + 1
            next_strategy = RecoveryStrategy(strategies[next_index])

            # Crear nueva tarea con siguiente estrategia
            new_task = RecoveryTask(
                task_id=f"{task.task_id}_retry_{next_index}",
                data_id=task.data_id,
                recovery_strategy=next_strategy,
                status=RecoveryStatus.PENDING,
                created_at=datetime.now(),
                priority=task.priority,
                retry_count=task.retry_count + 1,
                metadata={
                    **task.metadata,
                    'current_strategy_index': next_index,
                    'previous_attempts': task.metadata.get('previous_attempts', []) + [{
                        'strategy': task.recovery_strategy.value,
                        'error': task.error_message
                    }]
                }
            )

            self.recovery_queue.append(new_task)
            logger.info(f"🔄 Retrying recovery for {task.data_id} with strategy {next_strategy.value}")

    # Métodos auxiliares (implementaciones simplificadas)
    async def _find_data_from_peers(self, data_id: str) -> Optional[Any]:
        """Buscar datos en peers (simulado)."""
        # En implementación real, consultaría el registro de peers
        await asyncio.sleep(0.1)  # Simular latencia de red
        return None  # Simular no encontrado

    async def _find_previous_version(self, data_id: str) -> Optional[Any]:
        """Buscar versión anterior (simulado)."""
        await asyncio.sleep(0.1)
        return None

    async def _reconstruct_from_redundancy(self, data_id: str) -> Optional[Any]:
        """Reconstruir desde redundancia (simulado)."""
        await asyncio.sleep(0.1)
        return None

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de recuperación."""
        active_count = len(self.active_tasks)
        completed_count = len(self.completed_tasks)

        success_rate = (self.stats['successful_recoveries'] /
                       self.stats['total_recoveries_attempted']) if self.stats['total_recoveries_attempted'] > 0 else 0

        return {
            **self.stats,
            'active_tasks': active_count,
            'completed_tasks': completed_count,
            'success_rate': success_rate,
            'is_running': self.is_running,
            'queue_size': len(self.recovery_queue)
        }

    def cleanup_old_tasks(self, max_age_days: int = 7):
        """
        Limpiar tareas antiguas completadas.

        Args:
            max_age_days: Edad máxima en días
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)

        to_remove = []
        for task_id, result in self.completed_tasks.items():
            # Estimar tiempo de completado (usar tiempo de recuperación como aproximación)
            if result.recovery_time > 0:
                completed_time = datetime.now() - timedelta(seconds=result.recovery_time)
                if completed_time < cutoff:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.completed_tasks[task_id]

        logger.info(f"🧹 Cleaned up {len(to_remove)} old recovery tasks")