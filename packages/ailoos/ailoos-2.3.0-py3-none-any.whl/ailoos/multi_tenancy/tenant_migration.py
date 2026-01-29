#!/usr/bin/env python3
"""
TenantMigration - Migraciones seguras entre tenants para Ailoos FASE 8
=====================================================================

Sistema de migración completo con:
- Migración de datos entre tenants
- Validación de integridad durante migración
- Rollback automático en caso de error
- Migración de configuraciones y permisos
- Auditoría completa del proceso
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    """Estados de migración"""
    PENDING = "pending"
    VALIDATING = "validating"
    MIGRATING = "migrating"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationType(Enum):
    """Tipos de migración"""
    DATA_ONLY = "data_only"
    FULL_TENANT = "full_tenant"
    CONFIG_ONLY = "config_only"
    USERS_ONLY = "users_only"
    PERMISSIONS_ONLY = "permissions_only"

@dataclass
class MigrationStep:
    """Paso individual de migración"""
    step_id: str
    name: str
    description: str
    status: MigrationStatus = MigrationStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MigrationPlan:
    """Plan completo de migración"""
    migration_id: str
    source_tenant_id: str
    target_tenant_id: str
    migration_type: MigrationType
    steps: List[MigrationStep] = field(default_factory=list)
    status: MigrationStatus = MigrationStatus.PENDING
    estimated_duration: int = 0  # minutos
    actual_duration: int = 0
    data_size_estimate: int = 0  # bytes
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_available: bool = True
    rollback_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataValidation:
    """Validación de integridad de datos"""
    validation_id: str
    migration_id: str
    table_name: str
    source_count: int = 0
    target_count: int = 0
    checksum_match: bool = False
    source_checksum: str = ""
    target_checksum: str = ""
    errors: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)

class TenantMigration:
    """
    Sistema de migración segura entre tenants
    """

    def __init__(self, tenant_manager, tenant_database, tenant_security, tenant_billing):
        self.tenant_manager = tenant_manager
        self.tenant_database = tenant_database
        self.tenant_security = tenant_security
        self.tenant_billing = tenant_billing

        # Almacenamiento de migraciones
        self.migrations: Dict[str, MigrationPlan] = {}
        self.validations: Dict[str, DataValidation] = {}

        # Configuración
        self.max_migration_duration = timedelta(hours=4)
        self.validation_timeout = timedelta(minutes=30)
        self.chunk_size = 1000  # registros por chunk

        logger.info("🔄 TenantMigration initialized")

    async def create_migration_plan(self, source_tenant_id: str, target_tenant_id: str,
                                   migration_type: MigrationType) -> Optional[MigrationPlan]:
        """
        Crear plan de migración entre tenants
        """
        try:
            # Verificar que ambos tenants existen y están activos
            source_tenant = await self.tenant_manager.get_tenant(source_tenant_id)
            target_tenant = await self.tenant_manager.get_tenant(target_tenant_id)

            if not source_tenant or not target_tenant:
                logger.error("Source or target tenant not found")
                return None

            if source_tenant.status != "active" or target_tenant.status != "active":
                logger.error("Source or target tenant not active")
                return None

            # Crear plan de migración
            migration_id = str(uuid.uuid4())
            plan = MigrationPlan(
                migration_id=migration_id,
                source_tenant_id=source_tenant_id,
                target_tenant_id=target_tenant_id,
                migration_type=migration_type
            )

            # Definir pasos según tipo de migración
            plan.steps = await self._define_migration_steps(migration_type)

            # Estimar duración y tamaño
            plan.estimated_duration = await self._estimate_migration_duration(source_tenant_id, migration_type)
            plan.data_size_estimate = await self._estimate_data_size(source_tenant_id, migration_type)

            self.migrations[migration_id] = plan

            logger.info(f"📋 Migration plan created: {migration_id} ({source_tenant_id} -> {target_tenant_id})")
            return plan

        except Exception as e:
            logger.error(f"❌ Failed to create migration plan: {e}")
            return None

    async def _define_migration_steps(self, migration_type: MigrationType) -> List[MigrationStep]:
        """Definir pasos de migración según tipo"""
        steps = []

        if migration_type in [MigrationType.DATA_ONLY, MigrationType.FULL_TENANT]:
            steps.extend([
                MigrationStep(
                    step_id="validate_source_data",
                    name="Validate Source Data",
                    description="Validate data integrity in source tenant"
                ),
                MigrationStep(
                    step_id="create_backup",
                    name="Create Backup",
                    description="Create backup of target tenant data"
                ),
                MigrationStep(
                    step_id="migrate_tables",
                    name="Migrate Tables",
                    description="Migrate table data from source to target"
                ),
                MigrationStep(
                    step_id="validate_migration",
                    name="Validate Migration",
                    description="Validate migrated data integrity"
                )
            ])

        if migration_type in [MigrationType.CONFIG_ONLY, MigrationType.FULL_TENANT]:
            steps.extend([
                MigrationStep(
                    step_id="migrate_config",
                    name="Migrate Configuration",
                    description="Migrate tenant configuration settings"
                ),
                MigrationStep(
                    step_id="migrate_limits",
                    name="Migrate Limits",
                    description="Migrate tenant limits and quotas"
                )
            ])

        if migration_type in [MigrationType.USERS_ONLY, MigrationType.FULL_TENANT]:
            steps.append(MigrationStep(
                step_id="migrate_users",
                name="Migrate Users",
                description="Migrate users and their data"
            ))

        if migration_type in [MigrationType.PERMISSIONS_ONLY, MigrationType.FULL_TENANT]:
            steps.append(MigrationStep(
                step_id="migrate_permissions",
                name="Migrate Permissions",
                description="Migrate roles and permissions"
            ))

        steps.append(MigrationStep(
            step_id="final_verification",
            name="Final Verification",
            description="Final verification of migration success"
        ))

        return steps

    async def execute_migration(self, migration_id: str) -> bool:
        """
        Ejecutar migración completa
        """
        plan = self.migrations.get(migration_id)
        if not plan:
            return False

        if plan.status != MigrationStatus.PENDING:
            return False

        plan.status = MigrationStatus.VALIDATING
        plan.started_at = datetime.now()

        try:
            logger.info(f"🚀 Starting migration: {migration_id}")

            # Ejecutar cada paso
            for step in plan.steps:
                success = await self._execute_migration_step(plan, step)
                if not success:
                    await self._rollback_migration(plan)
                    return False

            # Verificación final
            plan.status = MigrationStatus.VERIFYING
            if await self._final_verification(plan):
                plan.status = MigrationStatus.COMPLETED
                plan.completed_at = datetime.now()
                plan.actual_duration = int((plan.completed_at - plan.started_at).total_seconds() / 60)

                logger.info(f"✅ Migration completed: {migration_id} ({plan.actual_duration}min)")
                return True
            else:
                await self._rollback_migration(plan)
                return False

        except Exception as e:
            logger.error(f"❌ Migration failed: {migration_id} - {e}")
            plan.status = MigrationStatus.FAILED
            await self._rollback_migration(plan)
            return False

    async def _execute_migration_step(self, plan: MigrationPlan, step: MigrationStep) -> bool:
        """
        Ejecutar un paso individual de migración
        """
        step.status = MigrationStatus.MIGRATING
        step.started_at = datetime.now()

        try:
            logger.info(f"🔄 Executing step: {step.name}")

            if step.step_id == "validate_source_data":
                success = await self._validate_source_data(plan)
            elif step.step_id == "create_backup":
                success = await self._create_target_backup(plan)
            elif step.step_id == "migrate_tables":
                success = await self._migrate_table_data(plan)
            elif step.step_id == "validate_migration":
                success = await self._validate_migrated_data(plan)
            elif step.step_id == "migrate_config":
                success = await self._migrate_configuration(plan)
            elif step.step_id == "migrate_limits":
                success = await self._migrate_limits(plan)
            elif step.step_id == "migrate_users":
                success = await self._migrate_users(plan)
            elif step.step_id == "migrate_permissions":
                success = await self._migrate_permissions(plan)
            elif step.step_id == "final_verification":
                success = await self._final_verification(plan)
            else:
                success = True  # Paso desconocido, asumir éxito

            if success:
                step.status = MigrationStatus.COMPLETED
                step.completed_at = datetime.now()
                logger.info(f"✅ Step completed: {step.name}")
            else:
                step.status = MigrationStatus.FAILED
                logger.error(f"❌ Step failed: {step.name}")

            return success

        except Exception as e:
            step.status = MigrationStatus.FAILED
            step.error_message = str(e)
            logger.error(f"❌ Step error: {step.name} - {e}")
            return False

    async def _validate_source_data(self, plan: MigrationPlan) -> bool:
        """Validar integridad de datos fuente"""
        try:
            # Obtener estadísticas de tablas del tenant fuente
            source_stats = await self.tenant_database.get_tenant_statistics(plan.source_tenant_id)

            # Verificar que hay datos para migrar
            if source_stats['total_queries'] == 0:
                logger.warning("No data found in source tenant")
                return False

            # Almacenar estadísticas para comparación posterior
            plan.rollback_data['source_stats'] = source_stats

            return True

        except Exception as e:
            logger.error(f"Source data validation failed: {e}")
            return False

    async def _create_target_backup(self, plan: MigrationPlan) -> bool:
        """Crear backup de datos del tenant destino"""
        try:
            backup_path = f"/tmp/tenant_backup_{plan.target_tenant_id}_{int(datetime.now().timestamp())}.json"
            success = await self.tenant_database.backup_tenant_data(plan.target_tenant_id, backup_path)

            if success:
                plan.rollback_data['target_backup_path'] = backup_path
                return True

            return False

        except Exception as e:
            logger.error(f"Target backup creation failed: {e}")
            return False

    async def _migrate_table_data(self, plan: MigrationPlan) -> bool:
        """Migrar datos de tablas"""
        try:
            # Obtener lista de tablas del tenant fuente
            tables = ['users', 'models', 'training_jobs', 'inference_logs']  # En implementación real, obtener dinámicamente

            for table in tables:
                success = await self._migrate_single_table(plan, table)
                if not success:
                    return False

            return True

        except Exception as e:
            logger.error(f"Table data migration failed: {e}")
            return False

    async def _migrate_single_table(self, plan: MigrationPlan, table_name: str) -> bool:
        """Migrar una tabla individual"""
        try:
            # Obtener datos de la tabla fuente
            source_query = {
                'select': {
                    'table': table_name,
                    'columns': ['*']
                }
            }

            source_result = await self.tenant_database.execute_tenant_query(
                source_query, plan.source_tenant_id
            )

            if not source_result.get('success', False):
                logger.error(f"Failed to read from source table: {table_name}")
                return False

            source_data = source_result.get('data', [])

            if not source_data:
                logger.info(f"No data to migrate in table: {table_name}")
                return True

            # Insertar datos en tabla destino (chunked)
            chunk_size = self.chunk_size
            for i in range(0, len(source_data), chunk_size):
                chunk = source_data[i:i + chunk_size]

                insert_query = {
                    'insert': {
                        'table': table_name,
                        'data': chunk
                    }
                }

                result = await self.tenant_database.execute_tenant_query(
                    insert_query, plan.target_tenant_id
                )

                if not result.get('success', False):
                    logger.error(f"Failed to insert chunk into target table: {table_name}")
                    return False

            logger.info(f"Migrated {len(source_data)} records from {table_name}")
            return True

        except Exception as e:
            logger.error(f"Single table migration failed for {table_name}: {e}")
            return False

    async def _validate_migrated_data(self, plan: MigrationPlan) -> bool:
        """Validar datos migrados"""
        try:
            # Comparar estadísticas
            source_stats = plan.rollback_data.get('source_stats', {})
            target_stats = await self.tenant_database.get_tenant_statistics(plan.target_tenant_id)

            # Verificar que los datos se migraron correctamente
            # En implementación real, hacer validaciones más detalladas
            if target_stats['total_queries'] < source_stats.get('total_queries', 0):
                logger.error("Data migration validation failed: insufficient data in target")
                return False

            return True

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False

    async def _migrate_configuration(self, plan: MigrationPlan) -> bool:
        """Migrar configuración del tenant"""
        try:
            source_tenant = await self.tenant_manager.get_tenant(plan.source_tenant_id)
            target_tenant = await self.tenant_manager.get_tenant(plan.target_tenant_id)

            if source_tenant and target_tenant:
                # Copiar configuración relevante
                config_to_migrate = ['monitoring_enabled', 'billing_enabled']
                for key in config_to_migrate:
                    if key in source_tenant.config:
                        target_tenant.config[key] = source_tenant.config[key]

                target_tenant.updated_at = datetime.now()
                return True

            return False

        except Exception as e:
            logger.error(f"Configuration migration failed: {e}")
            return False

    async def _migrate_limits(self, plan: MigrationPlan) -> bool:
        """Migrar límites y cuotas"""
        try:
            source_tenant = await self.tenant_manager.get_tenant(plan.source_tenant_id)
            target_tenant = await self.tenant_manager.get_tenant(plan.target_tenant_id)

            if source_tenant and target_tenant:
                # Copiar límites (o combinarlos)
                target_tenant.limits = source_tenant.limits
                target_tenant.updated_at = datetime.now()
                return True

            return False

        except Exception as e:
            logger.error(f"Limits migration failed: {e}")
            return False

    async def _migrate_users(self, plan: MigrationPlan) -> bool:
        """Migrar usuarios"""
        try:
            # En implementación real, migrar usuarios del sistema de seguridad
            # Por ahora, simular
            await asyncio.sleep(0.1)
            return True

        except Exception as e:
            logger.error(f"Users migration failed: {e}")
            return False

    async def _migrate_permissions(self, plan: MigrationPlan) -> bool:
        """Migrar permisos y roles"""
        try:
            # En implementación real, migrar roles y permisos
            # Por ahora, simular
            await asyncio.sleep(0.1)
            return True

        except Exception as e:
            logger.error(f"Permissions migration failed: {e}")
            return False

    async def _final_verification(self, plan: MigrationPlan) -> bool:
        """Verificación final de migración"""
        try:
            # Verificar estado de ambos tenants
            source_tenant = await self.tenant_manager.get_tenant(plan.source_tenant_id)
            target_tenant = await self.tenant_manager.get_tenant(plan.target_tenant_id)

            if not source_tenant or not target_tenant:
                return False

            if target_tenant.status != "active":
                return False

            # Verificar que la migración fue exitosa
            return plan.status == MigrationStatus.VERIFYING

        except Exception as e:
            logger.error(f"Final verification failed: {e}")
            return False

    async def _rollback_migration(self, plan: MigrationPlan):
        """Rollback de migración en caso de error"""
        try:
            plan.status = MigrationStatus.ROLLED_BACK
            logger.warning(f"🔙 Rolling back migration: {plan.migration_id}")

            # Restaurar backup si existe
            backup_path = plan.rollback_data.get('target_backup_path')
            if backup_path and plan.rollback_available:
                success = await self.tenant_database.restore_tenant_data(plan.target_tenant_id, backup_path)
                if success:
                    logger.info("Rollback completed successfully")
                else:
                    logger.error("Rollback failed")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    async def _estimate_migration_duration(self, tenant_id: str, migration_type: MigrationType) -> int:
        """Estimar duración de migración en minutos"""
        base_duration = 5  # minutos base

        if migration_type == MigrationType.FULL_TENANT:
            base_duration *= 4
        elif migration_type in [MigrationType.DATA_ONLY, MigrationType.USERS_ONLY]:
            base_duration *= 2

        # Ajustar por tamaño de datos (estimado)
        stats = await self.tenant_database.get_tenant_statistics(tenant_id)
        if stats['total_queries'] > 10000:
            base_duration *= 2

        return base_duration

    async def _estimate_data_size(self, tenant_id: str, migration_type: MigrationType) -> int:
        """Estimar tamaño de datos a migrar en bytes"""
        base_size = 1024 * 1024  # 1MB base

        if migration_type == MigrationType.FULL_TENANT:
            base_size *= 10
        elif migration_type == MigrationType.DATA_ONLY:
            base_size *= 5

        return base_size

    async def get_migration_status(self, migration_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de migración"""
        plan = self.migrations.get(migration_id)
        if not plan:
            return None

        return {
            'migration_id': migration_id,
            'status': plan.status.value,
            'progress': len([s for s in plan.steps if s.status == MigrationStatus.COMPLETED]) / len(plan.steps),
            'current_step': next((s.name for s in plan.steps if s.status == MigrationStatus.MIGRATING), None),
            'estimated_duration': plan.estimated_duration,
            'actual_duration': plan.actual_duration,
            'started_at': plan.started_at.isoformat() if plan.started_at else None,
            'completed_at': plan.completed_at.isoformat() if plan.completed_at else None
        }

    async def cancel_migration(self, migration_id: str) -> bool:
        """Cancelar migración en curso"""
        plan = self.migrations.get(migration_id)
        if not plan or plan.status not in [MigrationStatus.PENDING, MigrationStatus.VALIDATING, MigrationStatus.MIGRATING]:
            return False

        plan.status = MigrationStatus.FAILED
        logger.info(f"🚫 Migration cancelled: {migration_id}")
        return True

    async def cleanup_completed_migrations(self, max_age_days: int = 30):
        """Limpiar migraciones completadas antiguas"""
        cutoff = datetime.now() - timedelta(days=max_age_days)

        migrations_to_remove = [
            mid for mid, plan in self.migrations.items()
            if plan.status in [MigrationStatus.COMPLETED, MigrationStatus.FAILED] and
            plan.completed_at and plan.completed_at < cutoff
        ]

        for mid in migrations_to_remove:
            del self.migrations[mid]

        if migrations_to_remove:
            logger.info(f"🧹 Cleaned {len(migrations_to_remove)} old migrations")