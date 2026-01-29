#!/usr/bin/env python3
"""
TenantManager - Gestión centralizada de tenants para Ailoos FASE 8
=================================================================

Sistema de gestión completo para tenants con:
- Creación y configuración de tenants
- Gestión del ciclo de vida
- Configuración de límites y cuotas
- Monitoreo de uso por tenant
- Integración con otros componentes del sistema
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    """Estados posibles de un tenant"""
    CREATING = "creating"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class TenantPlan(Enum):
    """Planes disponibles para tenants"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class TenantLimits:
    """Límites y cuotas por tenant"""
    max_users: int = 10
    max_storage_gb: float = 1.0
    max_api_calls_per_hour: int = 1000
    max_concurrent_sessions: int = 5
    max_models: int = 3
    max_training_hours_per_month: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_users': self.max_users,
            'max_storage_gb': self.max_storage_gb,
            'max_api_calls_per_hour': self.max_api_calls_per_hour,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'max_models': self.max_models,
            'max_training_hours_per_month': self.max_training_hours_per_month
        }

@dataclass
class TenantUsage:
    """Uso actual del tenant"""
    current_users: int = 0
    storage_used_gb: float = 0.0
    api_calls_this_hour: int = 0
    active_sessions: int = 0
    models_count: int = 0
    training_hours_this_month: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_users': self.current_users,
            'storage_used_gb': self.storage_used_gb,
            'api_calls_this_hour': self.api_calls_this_hour,
            'active_sessions': self.active_sessions,
            'models_count': self.models_count,
            'training_hours_this_month': self.training_hours_this_month,
            'last_updated': self.last_updated.isoformat()
        }

@dataclass
class Tenant:
    """Representa un tenant en el sistema"""
    tenant_id: str
    name: str
    description: str = ""
    owner_email: str = ""
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.CREATING
    limits: TenantLimits = field(default_factory=TenantLimits)
    usage: TenantUsage = field(default_factory=TenantUsage)
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    suspended_at: Optional[datetime] = None
    api_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'owner_email': self.owner_email,
            'plan': self.plan.value,
            'status': self.status.value,
            'limits': self.limits.to_dict(),
            'usage': self.usage.to_dict(),
            'config': self.config,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'suspended_at': self.suspended_at.isoformat() if self.suspended_at else None,
            'api_key_hash': hashlib.sha256(self.api_key.encode()).hexdigest()[:16] + "..."
        }

class TenantManager:
    """
    Gestor centralizado de tenants con funcionalidades completas
    """

    def __init__(self, storage_path: str = "./tenant_data"):
        self.storage_path = storage_path
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_cache: Dict[str, Tenant] = {}
        self.cache_ttl = timedelta(minutes=5)

        # Configuración por defecto para diferentes planes
        self.plan_configs = {
            TenantPlan.FREE: TenantLimits(
                max_users=5,
                max_storage_gb=0.5,
                max_api_calls_per_hour=500,
                max_concurrent_sessions=2,
                max_models=1,
                max_training_hours_per_month=1
            ),
            TenantPlan.BASIC: TenantLimits(
                max_users=25,
                max_storage_gb=5.0,
                max_api_calls_per_hour=5000,
                max_concurrent_sessions=10,
                max_models=5,
                max_training_hours_per_month=10
            ),
            TenantPlan.PRO: TenantLimits(
                max_users=100,
                max_storage_gb=50.0,
                max_api_calls_per_hour=25000,
                max_concurrent_sessions=50,
                max_models=20,
                max_training_hours_per_month=100
            ),
            TenantPlan.ENTERPRISE: TenantLimits(
                max_users=1000,
                max_storage_gb=500.0,
                max_api_calls_per_hour=100000,
                max_concurrent_sessions=200,
                max_models=100,
                max_training_hours_per_month=1000
            )
        }

        logger.info("🏢 TenantManager initialized")

    async def create_tenant(self, name: str, owner_email: str,
                          plan: TenantPlan = TenantPlan.FREE,
                          description: str = "",
                          config: Optional[Dict[str, Any]] = None) -> Tenant:
        """
        Crear un nuevo tenant
        """
        tenant_id = str(uuid.uuid4())

        # Validar nombre único
        if any(t.name.lower() == name.lower() for t in self.tenants.values()):
            raise ValueError(f"Tenant name '{name}' already exists")

        # Validar email único
        if any(t.owner_email.lower() == owner_email.lower() for t in self.tenants.values()):
            raise ValueError(f"Owner email '{owner_email}' already registered")

        # Crear tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            description=description,
            owner_email=owner_email,
            plan=plan,
            limits=self.plan_configs[plan],
            config=config or {},
            status=TenantStatus.CREATING
        )

        # Inicializar configuración por defecto
        tenant.config.update({
            'database_schema': f"tenant_{tenant_id.replace('-', '_')}",
            'isolation_level': 'strict',
            'billing_enabled': True,
            'monitoring_enabled': True
        })

        self.tenants[tenant_id] = tenant
        self.tenant_cache[tenant_id] = tenant

        # Simular inicialización (en producción sería async con DB)
        await asyncio.sleep(0.1)  # Simular setup time
        tenant.status = TenantStatus.ACTIVE
        tenant.updated_at = datetime.now()

        logger.info(f"✅ Tenant '{name}' created with ID: {tenant_id}")
        return tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Obtener tenant por ID con cache
        """
        # Check cache first
        if tenant_id in self.tenant_cache:
            cached_tenant = self.tenant_cache[tenant_id]
            if datetime.now() - cached_tenant.updated_at < self.cache_ttl:
                return cached_tenant

        # Get from storage
        if tenant_id in self.tenants:
            tenant = self.tenants[tenant_id]
            self.tenant_cache[tenant_id] = tenant
            return tenant

        return None

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """
        Obtener tenant por API key
        """
        for tenant in self.tenants.values():
            if tenant.api_key == api_key and tenant.status == TenantStatus.ACTIVE:
                return tenant
        return None

    async def update_tenant_plan(self, tenant_id: str, new_plan: TenantPlan) -> bool:
        """
        Actualizar plan del tenant
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.status != TenantStatus.ACTIVE:
            raise ValueError(f"Cannot update plan for tenant in status: {tenant.status.value}")

        old_plan = tenant.plan
        tenant.plan = new_plan
        tenant.limits = self.plan_configs[new_plan]
        tenant.updated_at = datetime.now()

        # Limpiar cache
        if tenant_id in self.tenant_cache:
            del self.tenant_cache[tenant_id]

        logger.info(f"📈 Tenant '{tenant.name}' plan updated: {old_plan.value} -> {new_plan.value}")
        return True

    async def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """
        Suspender tenant
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.status != TenantStatus.ACTIVE:
            return False

        tenant.status = TenantStatus.SUSPENDED
        tenant.suspended_at = datetime.now()
        tenant.updated_at = datetime.now()
        tenant.config['suspension_reason'] = reason

        # Limpiar cache
        if tenant_id in self.tenant_cache:
            del self.tenant_cache[tenant_id]

        logger.info(f"🚫 Tenant '{tenant.name}' suspended: {reason}")
        return True

    async def reactivate_tenant(self, tenant_id: str) -> bool:
        """
        Reactivar tenant suspendido
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.status != TenantStatus.SUSPENDED:
            return False

        tenant.status = TenantStatus.ACTIVE
        tenant.suspended_at = None
        tenant.updated_at = datetime.now()
        if 'suspension_reason' in tenant.config:
            del tenant.config['suspension_reason']

        # Limpiar cache
        if tenant_id in self.tenant_cache:
            del self.tenant_cache[tenant_id]

        logger.info(f"✅ Tenant '{tenant.name}' reactivated")
        return True

    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Eliminar tenant (soft delete)
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED
        tenant.updated_at = datetime.now()

        # Limpiar cache
        if tenant_id in self.tenant_cache:
            del self.tenant_cache[tenant_id]

        logger.info(f"🗑️ Tenant '{tenant.name}' marked for deletion")
        return True

    async def update_tenant_usage(self, tenant_id: str, usage_updates: Dict[str, Any]) -> bool:
        """
        Actualizar métricas de uso del tenant
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        # Actualizar campos de uso
        for key, value in usage_updates.items():
            if hasattr(tenant.usage, key):
                setattr(tenant.usage, key, value)

        tenant.usage.last_updated = datetime.now()
        tenant.updated_at = datetime.now()

        # Limpiar cache
        if tenant_id in self.tenant_cache:
            del self.tenant_cache[tenant_id]

        return True

    def check_limits(self, tenant: Tenant, action: str) -> Dict[str, Any]:
        """
        Verificar si una acción excede los límites del tenant
        """
        violations = {}

        if action == "add_user" and tenant.usage.current_users >= tenant.limits.max_users:
            violations['users'] = f"Max users exceeded: {tenant.usage.current_users}/{tenant.limits.max_users}"

        if action == "api_call":
            # Reset counter if hour changed
            now = datetime.now()
            if tenant.usage.last_updated.hour != now.hour:
                tenant.usage.api_calls_this_hour = 0
            if tenant.usage.api_calls_this_hour >= tenant.limits.max_api_calls_per_hour:
                violations['api_calls'] = f"API rate limit exceeded: {tenant.usage.api_calls_this_hour}/{tenant.limits.max_api_calls_per_hour}"

        if action == "new_session" and tenant.usage.active_sessions >= tenant.limits.max_concurrent_sessions:
            violations['sessions'] = f"Max concurrent sessions exceeded: {tenant.usage.active_sessions}/{tenant.limits.max_concurrent_sessions}"

        if action == "create_model" and tenant.usage.models_count >= tenant.limits.max_models:
            violations['models'] = f"Max models exceeded: {tenant.usage.models_count}/{tenant.limits.max_models}"

        return violations

    async def list_tenants(self, status_filter: Optional[TenantStatus] = None,
                          plan_filter: Optional[TenantPlan] = None) -> List[Tenant]:
        """
        Listar tenants con filtros opcionales
        """
        tenants = list(self.tenants.values())

        if status_filter:
            tenants = [t for t in tenants if t.status == status_filter]

        if plan_filter:
            tenants = [t for t in tenants if t.plan == plan_filter]

        return sorted(tenants, key=lambda t: t.created_at, reverse=True)

    def get_tenant_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del sistema de tenants
        """
        total_tenants = len(self.tenants)
        active_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE])
        suspended_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.SUSPENDED])

        plan_distribution = {}
        for plan in TenantPlan:
            plan_distribution[plan.value] = len([t for t in self.tenants.values() if t.plan == plan])

        return {
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'suspended_tenants': suspended_tenants,
            'plan_distribution': plan_distribution,
            'cache_size': len(self.tenant_cache)
        }

    async def cleanup_expired_cache(self):
        """
        Limpiar cache expirada
        """
        now = datetime.now()
        expired_keys = [
            tenant_id for tenant_id, tenant in self.tenant_cache.items()
            if now - tenant.updated_at > self.cache_ttl
        ]

        for key in expired_keys:
            del self.tenant_cache[key]

        if expired_keys:
            logger.info(f"🧹 Cleaned {len(expired_keys)} expired cache entries")

# Instancia global
_tenant_manager_instance = None

def get_tenant_manager() -> TenantManager:
    """Obtener instancia global del TenantManager"""
    global _tenant_manager_instance
    if _tenant_manager_instance is None:
        _tenant_manager_instance = TenantManager()
    return _tenant_manager_instance