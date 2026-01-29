"""
Multi-Tenancy System for Ailoos FASE 8
======================================

Sistema completo de aislamiento multi-tenant con:
- TenantManager: Gestión centralizada de tenants
- TenantIsolation: Middleware de aislamiento por tenant
- TenantDatabase: Extensión de DB con tenant_id en todas las tablas
- TenantSecurity: Seguridad y permisos por tenant
- TenantBilling: Sistema de facturación por tenant
- TenantMigration: Migraciones seguras entre tenants
"""

from .tenant_manager import TenantManager, get_tenant_manager
from .tenant_isolation import TenantIsolationMiddleware
from .tenant_database import TenantDatabase
from .tenant_security import TenantSecurity
from .tenant_billing import TenantBilling
from .tenant_migration import TenantMigration

__version__ = "1.0.0"
__all__ = [
    'TenantManager',
    'get_tenant_manager',
    'TenantIsolationMiddleware',
    'TenantDatabase',
    'TenantSecurity',
    'TenantBilling',
    'TenantMigration'
]