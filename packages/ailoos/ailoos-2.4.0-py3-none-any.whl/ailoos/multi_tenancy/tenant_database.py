#!/usr/bin/env python3
"""
TenantDatabase - Extensión de DB con tenant_id para Ailoos FASE 8
===============================================================

Sistema de base de datos multi-tenant con:
- Inyección automática de tenant_id en todas las queries
- Aislamiento completo de datos por tenant
- Migraciones tenant-aware
- Optimización de queries por tenant
- Backup y restore por tenant
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOperation(Enum):
    """Tipos de operaciones de DB"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"

@dataclass
class TenantQuery:
    """Query con contexto de tenant"""
    original_query: Dict[str, Any]
    tenant_id: str
    operation: DatabaseOperation
    table_name: str
    injected_query: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TenantSchema:
    """Esquema de base de datos por tenant"""
    tenant_id: str
    schema_name: str
    tables: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_migration: Optional[str] = None

class TenantDatabase:
    """
    Extensión de base de datos con soporte completo para multi-tenancy
    """

    def __init__(self, base_database_client, tenant_manager):
        self.base_db = base_database_client
        self.tenant_manager = tenant_manager

        # Configuración
        self.tenant_column = "tenant_id"
        self.system_tables = {
            "tenants", "migrations", "system_logs", "audit_trail"
        }

        # Cache de esquemas
        self.schema_cache: Dict[str, TenantSchema] = {}
        self.query_log: List[TenantQuery] = []

        # Configuración de particionamiento
        self.enable_partitioning = True
        self.partition_strategy = "hash"  # hash, range, list

        logger.info("🗄️ TenantDatabase initialized")

    async def execute_tenant_query(self, query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Ejecutar query con contexto de tenant
        """
        start_time = asyncio.get_event_loop().time()

        # Crear objeto de query con tenant
        tenant_query = TenantQuery(
            original_query=query,
            tenant_id=tenant_id,
            operation=self._classify_operation(query),
            table_name=self._extract_table_name(query)
        )

        # Verificar permisos del tenant
        if not await self._check_tenant_permissions(tenant_query):
            raise PermissionError(f"Tenant {tenant_id} not authorized for this operation")

        # Inyectar tenant_id en la query
        tenant_query.injected_query = await self._inject_tenant_filter(query, tenant_id)

        # Log de la query
        self.query_log.append(tenant_query)

        try:
            # Ejecutar query en base de datos
            result = await self.base_db.execute(tenant_query.injected_query)

            # Calcular tiempo de ejecución
            tenant_query.execution_time = asyncio.get_event_loop().time() - start_time

            # Log de éxito
            logger.info(f"✅ Tenant query executed: {tenant_id} -> {tenant_query.table_name} ({tenant_query.execution_time:.3f}s)")

            return result

        except Exception as e:
            logger.error(f"❌ Tenant query failed: {tenant_id} -> {tenant_query.table_name}: {e}")
            raise

    async def _inject_tenant_filter(self, query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Inyectar filtro de tenant_id en la query
        """
        query_copy = json.loads(json.dumps(query))  # Deep copy

        # Para operaciones de escritura, agregar tenant_id
        if 'insert' in query_copy:
            data = query_copy['insert']
            if isinstance(data, dict):
                data[self.tenant_column] = tenant_id
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        item[self.tenant_column] = tenant_id

        elif 'update' in query_copy:
            # Asegurar que el update tenga filtro de tenant
            if 'where' not in query_copy['update']:
                query_copy['update']['where'] = {}
            query_copy['update']['where'][self.tenant_column] = tenant_id

        elif 'delete' in query_copy:
            # Asegurar que el delete tenga filtro de tenant
            if 'where' not in query_copy['delete']:
                query_copy['delete']['where'] = {}
            query_copy['delete']['where'][self.tenant_column] = tenant_id

        elif 'select' in query_copy or 'find' in query_copy:
            # Para selects, agregar filtro de tenant
            key = 'select' if 'select' in query_copy else 'find'
            if 'where' not in query_copy[key]:
                query_copy[key]['where'] = {}
            query_copy[key]['where'][self.tenant_column] = tenant_id

        # Para operaciones DDL, verificar si es tabla de sistema
        elif 'create' in query_copy:
            table_name = self._extract_table_name(query_copy)
            if table_name not in self.system_tables:
                # Agregar columna tenant_id a la definición de tabla
                await self._inject_tenant_column_to_schema(query_copy, tenant_id)

        return query_copy

    async def _inject_tenant_column_to_schema(self, create_query: Dict[str, Any], tenant_id: str):
        """
        Inyectar columna tenant_id en definición de tabla
        """
        if 'create' in create_query and 'table' in create_query['create']:
            table_def = create_query['create']['table']

            # Agregar columna tenant_id si no existe
            if 'columns' in table_def:
                columns = table_def['columns']
                tenant_column_exists = any(
                    col.get('name') == self.tenant_column for col in columns
                )

                if not tenant_column_exists:
                    columns.insert(0, {
                        'name': self.tenant_column,
                        'type': 'VARCHAR(36)',
                        'nullable': False,
                        'default': tenant_id,
                        'index': True
                    })

                    # Agregar índice único compuesto si es necesario
                    if 'indexes' not in table_def:
                        table_def['indexes'] = []
                    table_def['indexes'].append({
                        'name': f'idx_{self.tenant_column}',
                        'columns': [self.tenant_column],
                        'unique': False
                    })

    def _classify_operation(self, query: Dict[str, Any]) -> DatabaseOperation:
        """Clasificar tipo de operación"""
        if 'select' in query or 'find' in query:
            return DatabaseOperation.SELECT
        elif 'insert' in query:
            return DatabaseOperation.INSERT
        elif 'update' in query:
            return DatabaseOperation.UPDATE
        elif 'delete' in query:
            return DatabaseOperation.DELETE
        elif 'create' in query:
            return DatabaseOperation.CREATE
        elif 'drop' in query:
            return DatabaseOperation.DROP
        else:
            return DatabaseOperation.SELECT

    def _extract_table_name(self, query: Dict[str, Any]) -> str:
        """Extraer nombre de tabla de la query"""
        for operation in ['select', 'insert', 'update', 'delete', 'create', 'drop']:
            if operation in query:
                op_data = query[operation]
                if isinstance(op_data, dict) and 'table' in op_data:
                    return op_data['table']
                elif isinstance(op_data, str):
                    return op_data

        # Fallback
        if 'from' in query:
            return query['from']

        return 'unknown'

    async def _check_tenant_permissions(self, tenant_query: TenantQuery) -> bool:
        """
        Verificar permisos del tenant para la operación
        """
        # Obtener tenant
        tenant = await self.tenant_manager.get_tenant(tenant_query.tenant_id)
        if not tenant:
            return False

        # Verificar estado del tenant
        if tenant.status.value != 'active':
            return False

        # Verificar límites
        violations = self.tenant_manager.check_limits(tenant, tenant_query.operation.value)
        if violations:
            logger.warning(f"🚫 Tenant {tenant_query.tenant_id} exceeded limits: {violations}")
            return False

        # Verificar permisos específicos por operación
        if tenant_query.operation in [DatabaseOperation.DROP, DatabaseOperation.DELETE]:
            # Operaciones peligrosas requieren permisos especiales
            if 'admin' not in tenant.config.get('permissions', []):
                return False

        return True

    async def create_tenant_schema(self, tenant_id: str) -> TenantSchema:
        """
        Crear esquema de base de datos para un tenant
        """
        schema_name = f"tenant_{tenant_id.replace('-', '_')}"

        schema = TenantSchema(
            tenant_id=tenant_id,
            schema_name=schema_name,
            tables=[],
            indexes=[]
        )

        # Crear esquema en DB
        create_schema_query = {
            'create': {
                'schema': {
                    'name': schema_name,
                    'if_not_exists': True
                }
            }
        }

        await self.base_db.execute(create_schema_query)
        self.schema_cache[tenant_id] = schema

        logger.info(f"📋 Created schema for tenant {tenant_id}: {schema_name}")
        return schema

    async def migrate_tenant_schema(self, tenant_id: str, migration_script: str) -> bool:
        """
        Ejecutar migración de esquema para un tenant
        """
        try:
            # Parsear y ejecutar script de migración
            migration_queries = self._parse_migration_script(migration_script)

            for query in migration_queries:
                await self.execute_tenant_query(query, tenant_id)

            # Actualizar schema cache
            if tenant_id in self.schema_cache:
                self.schema_cache[tenant_id].last_migration = migration_script[:50] + "..."

            logger.info(f"🔄 Migration completed for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Migration failed for tenant {tenant_id}: {e}")
            return False

    def _parse_migration_script(self, script: str) -> List[Dict[str, Any]]:
        """
        Parsear script de migración SQL a formato de query
        """
        # En implementación real, parsearía SQL
        # Por ahora, devolver lista vacía
        return []

    async def backup_tenant_data(self, tenant_id: str, backup_path: str) -> bool:
        """
        Crear backup de datos del tenant
        """
        try:
            # Obtener todas las tablas del tenant
            tables = await self._get_tenant_tables(tenant_id)

            backup_data = {
                'tenant_id': tenant_id,
                'timestamp': datetime.now().isoformat(),
                'tables': {}
            }

            # Backup de cada tabla
            for table in tables:
                if table not in self.system_tables:
                    query = {
                        'select': {
                            'table': table,
                            'columns': ['*']
                        }
                    }

                    result = await self.execute_tenant_query(query, tenant_id)
                    backup_data['tables'][table] = result.get('data', [])

            # Guardar backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"💾 Backup created for tenant {tenant_id}: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Backup failed for tenant {tenant_id}: {e}")
            return False

    async def restore_tenant_data(self, tenant_id: str, backup_path: str) -> bool:
        """
        Restaurar datos del tenant desde backup
        """
        try:
            # Cargar backup
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            if backup_data['tenant_id'] != tenant_id:
                raise ValueError("Backup tenant_id mismatch")

            # Restaurar cada tabla
            for table, data in backup_data['tables'].items():
                if data:
                    query = {
                        'insert': {
                            'table': table,
                            'data': data
                        }
                    }

                    await self.execute_tenant_query(query, tenant_id)

            logger.info(f"🔄 Restore completed for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Restore failed for tenant {tenant_id}: {e}")
            return False

    async def _get_tenant_tables(self, tenant_id: str) -> List[str]:
        """
        Obtener lista de tablas del tenant
        """
        # En implementación real, consultaría information_schema
        # Por ahora, devolver lista hardcodeada
        return ['users', 'models', 'training_jobs', 'inference_logs']

    async def get_tenant_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de uso de DB por tenant
        """
        stats = {
            'tenant_id': tenant_id,
            'total_queries': 0,
            'total_execution_time': 0.0,
            'table_counts': {},
            'last_activity': None
        }

        # Calcular desde query log
        tenant_queries = [q for q in self.query_log if q.tenant_id == tenant_id]

        if tenant_queries:
            stats['total_queries'] = len(tenant_queries)
            stats['total_execution_time'] = sum(q.execution_time for q in tenant_queries)
            stats['last_activity'] = max(q.created_at for q in tenant_queries).isoformat()

            # Contar por tabla
            table_counts = {}
            for query in tenant_queries:
                table = query.table_name
                table_counts[table] = table_counts.get(table, 0) + 1
            stats['table_counts'] = table_counts

        return stats

    def cleanup_query_log(self, max_age_hours: int = 24):
        """
        Limpiar log de queries antiguo
        """
        cutoff = datetime.now().replace(hour=datetime.now().hour - max_age_hours)
        self.query_log = [q for q in self.query_log if q.created_at > cutoff]

        logger.info(f"🧹 Cleaned {len(self.query_log)} old query log entries")

# Helper functions

def create_tenant_aware_query(original_query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """
    Función helper para crear queries con tenant_id
    """
    query_copy = json.loads(json.dumps(original_query))

    # Inyectar tenant_id en where clause
    if 'where' not in query_copy:
        query_copy['where'] = {}
    query_copy['where']['tenant_id'] = tenant_id

    return query_copy

def validate_tenant_query(query: Dict[str, Any], tenant_id: str) -> bool:
    """
    Validar que una query tiene el tenant_id correcto
    """
    where_clause = query.get('where', {})
    return where_clause.get('tenant_id') == tenant_id