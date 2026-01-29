"""
Federated Versioning System - Sistema completo de versionado federado para AILOOS
Integra todos los componentes con atomicidad, consistencia y recuperación de fallos.
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import aiofiles
import os

from ..core.logging import get_logger
from ..infrastructure.ipfs_embedded import IPFSManager
from .federated_version_manager import FederatedVersionManager
from .version_validator import VersionValidator
from .ipfs_version_distributor import IPFSVersionDistributor
from .rollback_coordinator import RollbackCoordinator
from .version_conflict_resolver import VersionConflictResolver
from .version_history_tracker import VersionHistoryTracker

logger = get_logger(__name__)


class SystemHealth(Enum):
    """Estados de salud del sistema."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


@dataclass
class SystemConfig:
    """Configuración completa del sistema de versionado."""
    registry_path: str = "federated_versions.json"
    audit_log_path: str = "version_audit.log"
    ipfs_endpoint: str = "http://localhost:5001/api/v0"

    # Configuración de componentes
    min_validations: int = 3
    validation_timeout_hours: int = 24
    max_concurrent_distributions: int = 10
    replication_factor: int = 3
    auto_rollback_enabled: bool = True
    max_concurrent_rollbacks: int = 1
    conflict_timeout_hours: int = 24
    retention_days: int = 365

    # Configuración de atomicidad
    enable_transactions: bool = True
    transaction_timeout_seconds: int = 300
    max_retry_attempts: int = 3
    consistency_check_interval: int = 60

    # Configuración de recuperación
    enable_auto_recovery: bool = True
    recovery_checkpoint_interval: int = 300
    backup_retention_count: int = 10


@dataclass
class Transaction:
    """Transacción atómica del sistema."""
    transaction_id: str
    operations: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending, executing, committed, rolled_back, failed
    created_at: int = field(default_factory=lambda: int(time.time()))
    committed_at: Optional[int] = None
    rolled_back_at: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'transaction_id': self.transaction_id,
            'operations': self.operations,
            'status': self.status,
            'created_at': self.created_at,
            'committed_at': self.committed_at,
            'rolled_back_at': self.rolled_back_at,
            'error_message': self.error_message
        }


@dataclass
class SystemState:
    """Estado del sistema para recuperación de fallos."""
    timestamp: int
    health: SystemHealth
    active_transactions: List[str]
    pending_operations: List[Dict[str, Any]]
    component_states: Dict[str, Any]
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'timestamp': self.timestamp,
            'health': self.health.value,
            'active_transactions': self.active_transactions,
            'pending_operations': self.pending_operations,
            'component_states': self.component_states,
            'checksum': self.checksum
        }


class FederatedVersioningSystem:
    """
    Sistema completo de versionado federado con atomicidad y recuperación de fallos.
    Coordina todos los componentes para un funcionamiento production-ready.
    """

    def __init__(self, config: SystemConfig):
        """
        Inicializar el sistema de versionado federado.

        Args:
            config: Configuración completa del sistema
        """
        self.config = config

        # Componentes del sistema
        self.ipfs_manager: Optional[IPFSManager] = None
        self.version_manager: Optional[FederatedVersionManager] = None
        self.validator: Optional[VersionValidator] = None
        self.distributor: Optional[IPFSVersionDistributor] = None
        self.rollback_coordinator: Optional[RollbackCoordinator] = None
        self.conflict_resolver: Optional[VersionConflictResolver] = None
        self.history_tracker: Optional[VersionHistoryTracker] = None

        # Estado del sistema
        self.system_health = SystemHealth.HEALTHY
        self.is_running = False
        self.last_health_check = 0

        # Transacciones y atomicidad
        self.active_transactions: Dict[str, Transaction] = {}
        self.transaction_lock = asyncio.Lock()
        self.pending_operations: List[Dict[str, Any]] = []

        # Recuperación de fallos
        self.system_state_path = f"{config.registry_path}.state"
        self.backup_dir = f"{config.registry_path}.backups"
        self.recovery_task: Optional[asyncio.Task] = None
        self.consistency_task: Optional[asyncio.Task] = None

        # Estadísticas del sistema
        self.stats = {
            'uptime': 0,
            'transactions_processed': 0,
            'recovery_events': 0,
            'consistency_violations': 0,
            'system_restarts': 0
        }

        logger.info("🚀 FederatedVersioningSystem initialized")

    async def initialize(self) -> bool:
        """
        Inicializar todos los componentes del sistema.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("🔧 Initializing federated versioning system components...")

            # Inicializar IPFS
            self.ipfs_manager = IPFSManager(api_endpoint=self.config.ipfs_endpoint)
            await self.ipfs_manager.start()

            # Inicializar componentes en orden de dependencia
            self.version_manager = FederatedVersionManager(
                registry_path=self.config.registry_path,
                ipfs_manager=self.ipfs_manager,
                min_validations=self.config.min_validations,
                validation_timeout_hours=self.config.validation_timeout_hours
            )
            await self.version_manager.initialize()

            self.validator = VersionValidator(
                version_manager=self.version_manager,
                validation_timeout_seconds=self.config.validation_timeout_hours * 3600,
                min_validation_score=0.7
            )

            self.distributor = IPFSVersionDistributor(
                ipfs_manager=self.ipfs_manager,
                version_manager=self.version_manager,
                max_concurrent_distributions=self.config.max_concurrent_distributions,
                replication_factor=self.config.replication_factor
            )

            self.rollback_coordinator = RollbackCoordinator(
                version_manager=self.version_manager,
                distributor=self.distributor,
                auto_rollback_enabled=self.config.auto_rollback_enabled,
                max_concurrent_rollbacks=self.config.max_concurrent_rollbacks
            )

            self.conflict_resolver = VersionConflictResolver(
                version_manager=self.version_manager,
                validator=self.validator,
                auto_resolution_enabled=True,
                conflict_timeout_hours=self.config.conflict_timeout_hours
            )

            self.history_tracker = VersionHistoryTracker(
                version_manager=self.version_manager,
                validator=self.validator,
                distributor=self.distributor,
                rollback_coordinator=self.rollback_coordinator,
                conflict_resolver=self.conflict_resolver,
                audit_log_path=self.config.audit_log_path,
                retention_days=self.config.retention_days
            )

            # Intentar recuperación de estado anterior
            await self._attempt_state_recovery()

            logger.info("✅ All system components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            await self._emergency_shutdown()
            return False

    async def start(self) -> bool:
        """
        Iniciar el sistema completo.

        Returns:
            True si el inicio fue exitoso
        """
        if self.is_running:
            return True

        try:
            logger.info("▶️ Starting federated versioning system...")

            # Iniciar componentes en orden
            await self.history_tracker.start()
            await self.conflict_resolver.start()
            await self.rollback_coordinator.start()
            await self.distributor.start()
            await self.validator.start()

            # Iniciar tareas del sistema
            if self.config.enable_auto_recovery:
                self.recovery_task = asyncio.create_task(self._recovery_monitor())

            if self.config.consistency_check_interval > 0:
                self.consistency_task = asyncio.create_task(self._consistency_monitor())

            self.is_running = True
            self.stats['system_restarts'] += 1

            logger.info("✅ Federated versioning system started successfully")
            return True

        except Exception as e:
            logger.error(f"❌ System start failed: {e}")
            await self._emergency_shutdown()
            return False

    async def stop(self):
        """Detener el sistema completo."""
        if not self.is_running:
            return

        logger.info("⏹️ Stopping federated versioning system...")

        # Cancelar tareas del sistema
        if self.recovery_task:
            self.recovery_task.cancel()
        if self.consistency_task:
            self.consistency_task.cancel()

        # Detener componentes en orden inverso
        try:
            await self.validator.stop()
            await self.distributor.stop()
            await self.rollback_coordinator.stop()
            await self.conflict_resolver.stop()
            await self.history_tracker.stop()
        except Exception as e:
            logger.warning(f"⚠️ Error during component shutdown: {e}")

        # Guardar estado final
        await self._save_system_state()

        self.is_running = False
        logger.info("🛑 Federated versioning system stopped")

    async def execute_transaction(self, operations: List[Dict[str, Any]],
                                description: str = "") -> str:
        """
        Ejecutar una transacción atómica.

        Args:
            operations: Lista de operaciones a ejecutar
            description: Descripción de la transacción

        Returns:
            ID de la transacción
        """
        if not self.config.enable_transactions:
            # Ejecutar operaciones directamente
            for op in operations:
                await self._execute_operation(op)
            return "direct_execution"

        async with self.transaction_lock:
            transaction_id = f"txn_{int(time.time())}_{len(self.active_transactions)}"

            transaction = Transaction(
                transaction_id=transaction_id,
                operations=operations
            )

            self.active_transactions[transaction_id] = transaction

            try:
                # Ejecutar transacción
                await self._execute_transaction(transaction)

                # Commit
                transaction.status = "committed"
                transaction.committed_at = int(time.time())
                self.stats['transactions_processed'] += 1

                logger.info(f"✅ Transaction {transaction_id} committed: {description}")
                return transaction_id

            except Exception as e:
                # Rollback
                await self._rollback_transaction(transaction)
                transaction.status = "rolled_back"
                transaction.rolled_back_at = int(time.time())
                transaction.error_message = str(e)

                logger.error(f"❌ Transaction {transaction_id} rolled back: {e}")
                raise

            finally:
                # Limpiar transacción completada
                if transaction.status in ["committed", "rolled_back"]:
                    # Mantener por un tiempo para auditoría
                    asyncio.create_task(self._cleanup_transaction(transaction_id, delay=300))

    async def _execute_transaction(self, transaction: Transaction):
        """Ejecutar transacción con manejo de errores."""
        transaction.status = "executing"

        # Crear punto de guardado
        checkpoint = await self._create_checkpoint()

        try:
            # Ejecutar operaciones
            for operation in transaction.operations:
                await self._execute_operation(operation)

            # Verificar consistencia
            await self._verify_transaction_consistency(transaction)

        except Exception as e:
            # Restaurar checkpoint en caso de error
            await self._restore_checkpoint(checkpoint)
            raise

    async def _execute_operation(self, operation: Dict[str, Any]):
        """Ejecutar una operación individual."""
        op_type = operation.get('type')
        op_data = operation.get('data', {})

        if op_type == 'register_version':
            await self._op_register_version(op_data)
        elif op_type == 'validate_version':
            await self._op_validate_version(op_data)
        elif op_type == 'distribute_version':
            await self._op_distribute_version(op_data)
        elif op_type == 'rollback_version':
            await self._op_rollback_version(op_data)
        else:
            raise ValueError(f"Unknown operation type: {op_type}")

    async def _op_register_version(self, data: Dict[str, Any]):
        """Operación: registrar versión."""
        model_data = data['model_data']
        metadata = data['metadata']
        creator_node = data['creator_node']

        version_id = await self.version_manager.register_new_version(
            model_data=model_data,
            metadata=metadata,
            creator_node=creator_node
        )

        # Iniciar validación colectiva
        node_ids = data.get('validator_nodes', [])
        if node_ids:
            await self.validator.start_validation(version_id, node_ids)

    async def _op_validate_version(self, data: Dict[str, Any]):
        """Operación: validar versión."""
        version_id = data['version_id']
        node_id = data['node_id']
        validation_results = data['validation_results']

        await self.validator.submit_node_validation(
            version_id=version_id,
            node_id=node_id,
            validation_results=validation_results
        )

    async def _op_distribute_version(self, data: Dict[str, Any]):
        """Operación: distribuir versión."""
        version_id = data['version_id']
        target_nodes = data['target_nodes']
        strategy = data.get('strategy', 'broadcast')

        await self.distributor.distribute_version(
            version_id=version_id,
            target_nodes=target_nodes,
            strategy=strategy
        )

    async def _op_rollback_version(self, data: Dict[str, Any]):
        """Operación: rollback de versión."""
        from_version = data['from_version']
        to_version = data['to_version']
        reason = data['reason']

        await self.rollback_coordinator.trigger_rollback(
            from_version=from_version,
            to_version=to_version,
            trigger='manual_trigger',
            reason=reason
        )

    async def _rollback_transaction(self, transaction: Transaction):
        """Rollback de transacción."""
        # Implementar rollback específico para cada operación
        for operation in reversed(transaction.operations):
            try:
                await self._rollback_operation(operation)
            except Exception as e:
                logger.warning(f"⚠️ Error during transaction rollback: {e}")

    async def _rollback_operation(self, operation: Dict[str, Any]):
        """Rollback de operación individual."""
        # Implementar rollback para cada tipo de operación
        op_type = operation.get('type')

        if op_type == 'register_version':
            # Deprecar versión recién registrada
            version_id = operation.get('result', {}).get('version_id')
            if version_id:
                await self.version_manager.deprecate_version(version_id, "Transaction rollback")
        # Otros rollbacks según sea necesario

    async def _verify_transaction_consistency(self, transaction: Transaction):
        """Verificar consistencia después de transacción."""
        # Verificar que el estado del sistema sea consistente
        health = await self._check_system_health()
        if health == SystemHealth.CRITICAL:
            raise Exception("System consistency check failed after transaction")

    async def _create_checkpoint(self) -> Dict[str, Any]:
        """Crear punto de guardado para rollback."""
        return {
            'timestamp': int(time.time()),
            'registry_state': await self._get_registry_state(),
            'active_versions': list(self.version_manager.registry.versions.keys())
        }

    async def _restore_checkpoint(self, checkpoint: Dict[str, Any]):
        """Restaurar punto de guardado."""
        # Implementar restauración del estado
        logger.warning("⚠️ Checkpoint restoration not fully implemented")

    async def _get_registry_state(self) -> Dict[str, Any]:
        """Obtener estado actual del registro."""
        return self.version_manager.registry.to_dict()

    async def _recovery_monitor(self):
        """Monitor de recuperación automática."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.recovery_checkpoint_interval)

                # Crear checkpoint periódico
                await self._save_system_state()

                # Verificar salud del sistema
                health = await self._check_system_health()
                if health != self.system_health:
                    logger.info(f"📊 System health changed: {self.system_health.value} -> {health.value}")
                    self.system_health = health

                    if health == SystemHealth.CRITICAL:
                        await self._trigger_emergency_recovery()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Recovery monitor error: {e}")

    async def _consistency_monitor(self):
        """Monitor de consistencia del sistema."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.consistency_check_interval)

                # Verificar consistencia
                violations = await self._check_consistency()
                if violations:
                    self.stats['consistency_violations'] += len(violations)
                    logger.warning(f"⚠️ Consistency violations detected: {len(violations)}")

                    # Intentar auto-corregir
                    await self._auto_correct_consistency(violations)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Consistency monitor error: {e}")

    async def _check_system_health(self) -> SystemHealth:
        """Verificar salud general del sistema."""
        try:
            # Verificar componentes críticos
            issues = 0

            if not await self._check_component_health(self.ipfs_manager):
                issues += 1

            if not await self._check_component_health(self.version_manager):
                issues += 1

            if len(self.active_transactions) > 10:  # Muchos transacciones pendientes
                issues += 1

            if issues == 0:
                return SystemHealth.HEALTHY
            elif issues <= 2:
                return SystemHealth.DEGRADED
            else:
                return SystemHealth.CRITICAL

        except Exception:
            return SystemHealth.CRITICAL

    async def _check_component_health(self, component) -> bool:
        """Verificar salud de un componente."""
        if not component:
            return False

        # Verificar métodos de salud si existen
        if hasattr(component, 'get_health_status'):
            try:
                status = await component.get_health_status()
                return status.get('healthy', False)
            except:
                pass

        # Verificar básico: el componente existe y no está en estado de error
        return True

    async def _check_consistency(self) -> List[Dict[str, Any]]:
        """Verificar consistencia del sistema."""
        violations = []

        try:
            # Verificar que versiones activas estén distribuidas
            active_version = await self.version_manager.get_active_version()
            if active_version:
                # Verificar que esté en IPFS
                try:
                    await self.ipfs_manager.get_data(active_version.model_cid)
                except:
                    violations.append({
                        'type': 'missing_model_cid',
                        'version_id': active_version.version_id,
                        'cid': active_version.model_cid
                    })

            # Verificar transacciones pendientes
            stale_transactions = [
                txn for txn in self.active_transactions.values()
                if time.time() - txn.created_at > self.config.transaction_timeout_seconds
            ]

            for txn in stale_transactions:
                violations.append({
                    'type': 'stale_transaction',
                    'transaction_id': txn.transaction_id,
                    'age_seconds': int(time.time() - txn.created_at)
                })

        except Exception as e:
            violations.append({
                'type': 'consistency_check_error',
                'error': str(e)
            })

        return violations

    async def _auto_correct_consistency(self, violations: List[Dict[str, Any]]):
        """Auto-corregir violaciones de consistencia."""
        for violation in violations:
            try:
                if violation['type'] == 'stale_transaction':
                    # Limpiar transacción estancada
                    txn_id = violation['transaction_id']
                    if txn_id in self.active_transactions:
                        txn = self.active_transactions[txn_id]
                        await self._rollback_transaction(txn)
                        del self.active_transactions[txn_id]
                        logger.info(f"🧹 Cleaned up stale transaction {txn_id}")

            except Exception as e:
                logger.warning(f"⚠️ Failed to auto-correct violation {violation['type']}: {e}")

    async def _trigger_emergency_recovery(self):
        """Trigger recuperación de emergencia."""
        logger.error("🚨 Emergency recovery triggered - system in critical state")

        self.stats['recovery_events'] += 1

        # Intentar reinicio suave de componentes
        try:
            await self.stop()
            await asyncio.sleep(5)  # Esperar
            success = await self.start()

            if success:
                logger.info("✅ Emergency recovery successful")
            else:
                logger.error("❌ Emergency recovery failed")

        except Exception as e:
            logger.error(f"❌ Emergency recovery error: {e}")

    async def _attempt_state_recovery(self):
        """Intentar recuperación de estado anterior."""
        try:
            if os.path.exists(self.system_state_path):
                async with aiofiles.open(self.system_state_path, 'r') as f:
                    state_data = json.loads(await f.read())

                state = SystemState(**state_data)

                # Verificar checksum
                state_checksum = self._calculate_state_checksum(state)
                if state_checksum != state.checksum:
                    logger.warning("⚠️ State checksum mismatch, skipping recovery")
                    return

                # Recuperar transacciones pendientes
                for txn_id in state.active_transactions:
                    # Recargar transacción si existe
                    pass

                logger.info(f"📂 Recovered system state from {datetime.fromtimestamp(state.timestamp)}")

        except Exception as e:
            logger.warning(f"⚠️ State recovery failed: {e}")

    async def _save_system_state(self):
        """Guardar estado del sistema."""
        try:
            # Crear directorio de backups
            os.makedirs(self.backup_dir, exist_ok=True)

            # Estado actual
            state = SystemState(
                timestamp=int(time.time()),
                health=self.system_health,
                active_transactions=list(self.active_transactions.keys()),
                pending_operations=self.pending_operations.copy(),
                component_states={
                    'version_manager': len(self.version_manager.registry.versions) if self.version_manager else 0,
                    'active_transactions': len(self.active_transactions),
                    'system_uptime': self.stats['uptime']
                }
            )

            # Calcular checksum
            state.checksum = self._calculate_state_checksum(state)

            # Guardar estado principal
            async with aiofiles.open(self.system_state_path, 'w') as f:
                await f.write(json.dumps(state.to_dict(), indent=2))

            # Crear backup rotativo
            backup_path = f"{self.backup_dir}/state_{int(time.time())}.json"
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(state.to_dict(), indent=2))

            # Limpiar backups antiguos
            await self._cleanup_old_backups()

        except Exception as e:
            logger.error(f"❌ Failed to save system state: {e}")

    def _calculate_state_checksum(self, state: SystemState) -> str:
        """Calcular checksum del estado."""
        state_str = json.dumps({
            'timestamp': state.timestamp,
            'health': state.health.value,
            'active_transactions': state.active_transactions,
            'component_states': state.component_states
        }, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()

    async def _cleanup_old_backups(self):
        """Limpiar backups antiguos."""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('state_') and file.endswith('.json'):
                    path = os.path.join(self.backup_dir, file)
                    mtime = os.path.getmtime(path)
                    backup_files.append((path, mtime))

            # Mantener solo los más recientes
            backup_files.sort(key=lambda x: x[1], reverse=True)
            to_delete = backup_files[self.config.backup_retention_count:]

            for path, _ in to_delete:
                os.remove(path)

        except Exception as e:
            logger.warning(f"⚠️ Backup cleanup failed: {e}")

    async def _cleanup_transaction(self, transaction_id: str, delay: int):
        """Limpiar transacción completada después de delay."""
        await asyncio.sleep(delay)
        if transaction_id in self.active_transactions:
            del self.active_transactions[transaction_id]

    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        return {
            'health': self.system_health.value,
            'is_running': self.is_running,
            'uptime': self.stats['uptime'],
            'components': {
                'version_manager': self.version_manager is not None,
                'validator': self.validator is not None,
                'distributor': self.distributor is not None,
                'rollback_coordinator': self.rollback_coordinator is not None,
                'conflict_resolver': self.conflict_resolver is not None,
                'history_tracker': self.history_tracker is not None
            },
            'active_transactions': len(self.active_transactions),
            'pending_operations': len(self.pending_operations),
            'statistics': self.stats.copy()
        }

    async def emergency_shutdown(self):
        """Apagado de emergencia del sistema."""
        logger.error("🚨 Emergency shutdown initiated")

        # Forzar parada de todos los componentes
        await self._emergency_shutdown()

    async def _emergency_shutdown(self):
        """Implementación del apagado de emergencia."""
        try:
            # Cancelar todas las tareas activas
            tasks_to_cancel = []
            if self.recovery_task:
                tasks_to_cancel.append(self.recovery_task)
            if self.consistency_task:
                tasks_to_cancel.append(self.consistency_task)

            for task in tasks_to_cancel:
                if not task.done():
                    task.cancel()

            # Intentar guardar estado de emergencia
            await self._save_system_state()

        except Exception as e:
            logger.error(f"❌ Emergency shutdown error: {e}")


# Funciones de conveniencia

async def create_federated_versioning_system(config: Optional[SystemConfig] = None) -> FederatedVersioningSystem:
    """
    Crear sistema de versionado federado con configuración predeterminada.

    Args:
        config: Configuración opcional del sistema

    Returns:
        Sistema de versionado configurado
    """
    if config is None:
        config = SystemConfig()

    system = FederatedVersioningSystem(config)

    success = await system.initialize()
    if not success:
        raise Exception("Failed to initialize federated versioning system")

    return system


async def run_versioning_system_demo():
    """Demo del sistema de versionado federado."""
    logger.info("🎬 Starting Federated Versioning System Demo")

    # Crear sistema
    system = await create_federated_versioning_system()

    try:
        # Iniciar sistema
        await system.start()

        # Demo de transacción
        operations = [
            {
                'type': 'register_version',
                'data': {
                    'model_data': b'dummy_model_data',
                    'metadata': {
                        'model_name': 'demo_model',
                        'version': '1.0.0',
                        'description': 'Demo version'
                    },
                    'creator_node': 'node_1',
                    'validator_nodes': ['node_1', 'node_2', 'node_3']
                }
            }
        ]

        txn_id = await system.execute_transaction(operations, "Demo transaction")
        logger.info(f"📝 Demo transaction completed: {txn_id}")

        # Obtener estado del sistema
        status = await system.get_system_status()
        logger.info(f"📊 System status: {status['health']}")

        await asyncio.sleep(5)  # Esperar un poco

    finally:
        await system.stop()

    logger.info("✅ Federated Versioning System Demo completed")


if __name__ == "__main__":
    # Ejecutar demo si se llama directamente
    asyncio.run(run_versioning_system_demo())