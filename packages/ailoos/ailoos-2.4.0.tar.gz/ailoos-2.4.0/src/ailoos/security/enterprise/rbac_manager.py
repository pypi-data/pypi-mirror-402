#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Manager con Roles Jerárquicos
============================================================

Implementa un sistema RBAC avanzado con roles jerárquicos, permisos granulares,
herencia de roles, y evaluación dinámica de políticas de acceso.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PermissionAction(Enum):
    """Acciones de permisos"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"
    ADMIN = "admin"

class PermissionResource(Enum):
    """Recursos de permisos"""
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    TENANT = "tenant"
    MODEL = "model"
    DATASET = "dataset"
    INFERENCE = "inference"
    TRAINING = "training"
    BILLING = "billing"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    FEDERATED = "federated"
    API = "api"
    SYSTEM = "system"

class PermissionScope(Enum):
    """Ámbitos de permisos"""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    RESOURCE = "resource"

@dataclass
class Permission:
    """Permiso individual"""
    action: PermissionAction
    resource: PermissionResource
    scope: PermissionScope = PermissionScope.GLOBAL
    resource_id: Optional[str] = None  # ID específico del recurso
    conditions: Dict[str, Any] = field(default_factory=dict)  # Condiciones adicionales

    def matches(self, action: PermissionAction, resource: PermissionResource,
               scope: PermissionScope = PermissionScope.GLOBAL,
               resource_id: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verifica si este permiso coincide con la solicitud

        Args:
            action: Acción solicitada
            resource: Recurso solicitado
            scope: Ámbito solicitado
            resource_id: ID del recurso solicitado
            context: Contexto adicional

        Returns:
            True si el permiso coincide
        """
        # Verificar acción
        if self.action != action and self.action != PermissionAction.ADMIN:
            return False

        # Verificar recurso
        if self.resource != resource:
            return False

        # Verificar ámbito
        if self.scope != PermissionScope.GLOBAL and self.scope != scope:
            return False

        # Verificar ID del recurso
        if self.resource_id and resource_id and self.resource_id != resource_id:
            return False

        # Verificar condiciones
        if self.conditions and context:
            for key, expected_value in self.conditions.items():
                actual_value = context.get(key)
                if actual_value != expected_value:
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte permiso a diccionario"""
        return {
            'action': self.action.value,
            'resource': self.resource.value,
            'scope': self.scope.value,
            'resource_id': self.resource_id,
            'conditions': self.conditions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Permission':
        """Crea permiso desde diccionario"""
        return cls(
            action=PermissionAction(data['action']),
            resource=PermissionResource(data['resource']),
            scope=PermissionScope(data.get('scope', 'global')),
            resource_id=data.get('resource_id'),
            conditions=data.get('conditions', {})
        )

@dataclass
class Role:
    """Rol con permisos y jerarquía"""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[Permission] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)  # IDs de roles padre
    child_roles: List[str] = field(default_factory=list)  # IDs de roles hijo
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True

    def add_permission(self, permission: Permission):
        """Agrega un permiso al rol"""
        self.permissions.append(permission)
        self.updated_at = datetime.now()

    def remove_permission(self, permission: Permission):
        """Remueve un permiso del rol"""
        self.permissions = [p for p in self.permissions if p != permission]
        self.updated_at = datetime.now()

    def has_permission(self, action: PermissionAction, resource: PermissionResource,
                      scope: PermissionScope = PermissionScope.GLOBAL,
                      resource_id: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verifica si el rol tiene un permiso específico

        Args:
            action: Acción
            resource: Recurso
            scope: Ámbito
            resource_id: ID del recurso
            context: Contexto

        Returns:
            True si tiene el permiso
        """
        for permission in self.permissions:
            if permission.matches(action, resource, scope, resource_id, context):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte rol a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.to_dict() for p in self.permissions],
            'parent_roles': self.parent_roles,
            'child_roles': self.child_roles,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Crea rol desde diccionario"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            permissions=[Permission.from_dict(p) for p in data.get('permissions', [])],
            parent_roles=data.get('parent_roles', []),
            child_roles=data.get('child_roles', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            active=data.get('active', True)
        )

@dataclass
class UserRoleAssignment:
    """Asignación de rol a usuario"""
    user_id: str
    role_id: str
    assigned_by: str
    assigned_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    scope: PermissionScope = PermissionScope.GLOBAL
    scope_resource_id: Optional[str] = None  # ID del recurso si scope es específico

    def is_active(self) -> bool:
        """Verifica si la asignación está activa"""
        if not self.expires_at:
            return True
        return datetime.now() < self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convierte asignación a diccionario"""
        return {
            'user_id': self.user_id,
            'role_id': self.role_id,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'scope': self.scope.value,
            'scope_resource_id': self.scope_resource_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRoleAssignment':
        """Crea asignación desde diccionario"""
        return cls(
            user_id=data['user_id'],
            role_id=data['role_id'],
            assigned_by=data['assigned_by'],
            assigned_at=datetime.fromisoformat(data['assigned_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            scope=PermissionScope(data.get('scope', 'global')),
            scope_resource_id=data.get('scope_resource_id')
        )

class RBACManager:
    """
    Gestor de Role-Based Access Control con jerarquía de roles
    """

    def __init__(self):
        # Roles definidos
        self.roles: Dict[str, Role] = {}

        # Asignaciones de roles a usuarios
        self.user_role_assignments: Dict[str, List[UserRoleAssignment]] = defaultdict(list)

        # Cache de permisos por usuario
        self._user_permissions_cache: Dict[str, Set[Tuple]] = {}
        self._cache_expiration = timedelta(minutes=15)
        self._last_cache_update: Dict[str, datetime] = {}

        # Roles predefinidos
        self._initialize_default_roles()

        logger.info("🔐 RBAC Manager initialized")

    def _initialize_default_roles(self):
        """Inicializa roles predefinidos"""
        # Rol de super administrador
        super_admin = Role(
            id="super_admin",
            name="Super Administrator",
            description="Full system access",
            permissions=[
                Permission(PermissionAction.ADMIN, PermissionResource.SYSTEM),
                Permission(PermissionAction.ADMIN, PermissionResource.USER),
                Permission(PermissionAction.ADMIN, PermissionResource.TENANT),
                Permission(PermissionAction.ADMIN, PermissionResource.MODEL),
                Permission(PermissionAction.ADMIN, PermissionResource.BILLING),
                Permission(PermissionAction.ADMIN, PermissionResource.AUDIT),
                Permission(PermissionAction.ADMIN, PermissionResource.COMPLIANCE)
            ]
        )

        # Rol de administrador de tenant
        tenant_admin = Role(
            id="tenant_admin",
            name="Tenant Administrator",
            description="Full tenant access",
            permissions=[
                Permission(PermissionAction.ADMIN, PermissionResource.TENANT, PermissionScope.TENANT),
                Permission(PermissionAction.MANAGE, PermissionResource.USER, PermissionScope.TENANT),
                Permission(PermissionAction.MANAGE, PermissionResource.MODEL, PermissionScope.TENANT),
                Permission(PermissionAction.MANAGE, PermissionResource.DATASET, PermissionScope.TENANT),
                Permission(PermissionAction.READ, PermissionResource.BILLING, PermissionScope.TENANT),
                Permission(PermissionAction.READ, PermissionResource.AUDIT, PermissionScope.TENANT)
            ]
        )

        # Rol de desarrollador
        developer = Role(
            id="developer",
            name="Developer",
            description="Development and deployment access",
            permissions=[
                Permission(PermissionAction.CREATE, PermissionResource.MODEL, PermissionScope.TENANT),
                Permission(PermissionAction.READ, PermissionResource.MODEL, PermissionScope.TENANT),
                Permission(PermissionAction.UPDATE, PermissionResource.MODEL, PermissionScope.TENANT),
                Permission(PermissionAction.DELETE, PermissionResource.MODEL, PermissionScope.TENANT),
                Permission(PermissionAction.EXECUTE, PermissionResource.INFERENCE, PermissionScope.TENANT),
                Permission(PermissionAction.MANAGE, PermissionResource.TRAINING, PermissionScope.TENANT),
                Permission(PermissionAction.READ, PermissionResource.DATASET, PermissionScope.TENANT)
            ]
        )

        # Rol de analista
        analyst = Role(
            id="analyst",
            name="Data Analyst",
            description="Data analysis access",
            permissions=[
                Permission(PermissionAction.READ, PermissionResource.DATASET, PermissionScope.TENANT),
                Permission(PermissionAction.EXECUTE, PermissionResource.INFERENCE, PermissionScope.TENANT),
                Permission(PermissionAction.READ, PermissionResource.MODEL, PermissionScope.TENANT)
            ]
        )

        # Rol de usuario básico
        user = Role(
            id="user",
            name="Basic User",
            description="Basic user access",
            permissions=[
                Permission(PermissionAction.EXECUTE, PermissionResource.INFERENCE, PermissionScope.USER),
                Permission(PermissionAction.READ, PermissionResource.USER, PermissionScope.USER)
            ]
        )

        # Establecer jerarquía
        tenant_admin.parent_roles = ["super_admin"]
        developer.parent_roles = ["tenant_admin"]
        analyst.parent_roles = ["developer"]
        user.parent_roles = ["analyst"]

        super_admin.child_roles = ["tenant_admin"]
        tenant_admin.child_roles = ["developer"]
        developer.child_roles = ["analyst"]
        analyst.child_roles = ["user"]

        # Registrar roles
        for role in [super_admin, tenant_admin, developer, analyst, user]:
            self.roles[role.id] = role

    def create_role(self, role: Role) -> Role:
        """
        Crea un nuevo rol

        Args:
            role: Rol a crear

        Returns:
            Rol creado

        Raises:
            ValueError: Si el rol ya existe
        """
        if role.id in self.roles:
            raise ValueError(f"Role {role.id} already exists")

        self.roles[role.id] = role

        # Actualizar jerarquía
        for parent_id in role.parent_roles:
            if parent_id in self.roles:
                self.roles[parent_id].child_roles.append(role.id)

        for child_id in role.child_roles:
            if child_id in self.roles:
                self.roles[child_id].parent_roles.append(role.id)

        logger.info(f"📝 Role created: {role.id}")
        return role

    def update_role(self, role_id: str, updates: Dict[str, Any]) -> Optional[Role]:
        """
        Actualiza un rol existente

        Args:
            role_id: ID del rol
            updates: Campos a actualizar

        Returns:
            Rol actualizado o None si no existe
        """
        role = self.roles.get(role_id)
        if not role:
            return None

        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)

        role.updated_at = datetime.now()

        # Limpiar cache
        self._clear_user_cache()

        logger.info(f"📝 Role updated: {role_id}")
        return role

    def delete_role(self, role_id: str) -> bool:
        """
        Elimina un rol

        Args:
            role_id: ID del rol

        Returns:
            True si se eliminó correctamente
        """
        role = self.roles.get(role_id)
        if not role:
            return False

        # Verificar que no tenga hijos
        if role.child_roles:
            raise ValueError(f"Cannot delete role {role_id}: has child roles")

        # Remover de jerarquía de padres
        for parent_id in role.parent_roles:
            if parent_id in self.roles:
                self.roles[parent_id].child_roles.remove(role_id)

        # Remover asignaciones de usuarios
        for user_id, assignments in self.user_role_assignments.items():
            self.user_role_assignments[user_id] = [
                a for a in assignments if a.role_id != role_id
            ]

        del self.roles[role_id]

        # Limpiar cache
        self._clear_user_cache()

        logger.info(f"🚫 Role deleted: {role_id}")
        return True

    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str,
                           expires_at: Optional[datetime] = None,
                           scope: PermissionScope = PermissionScope.GLOBAL,
                           scope_resource_id: Optional[str] = None) -> UserRoleAssignment:
        """
        Asigna un rol a un usuario

        Args:
            user_id: ID del usuario
            role_id: ID del rol
            assigned_by: Usuario que asigna el rol
            expires_at: Fecha de expiración
            scope: Ámbito del rol
            scope_resource_id: ID del recurso si ámbito específico

        Returns:
            Asignación creada

        Raises:
            ValueError: Si el rol no existe
        """
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} does not exist")

        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
            scope=scope,
            scope_resource_id=scope_resource_id
        )

        self.user_role_assignments[user_id].append(assignment)

        # Limpiar cache del usuario
        if user_id in self._user_permissions_cache:
            del self._user_permissions_cache[user_id]
        if user_id in self._last_cache_update:
            del self._last_cache_update[user_id]

        logger.info(f"👤 Role {role_id} assigned to user {user_id}")
        return assignment

    def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        Revoca un rol de un usuario

        Args:
            user_id: ID del usuario
            role_id: ID del rol

        Returns:
            True si se revocó correctamente
        """
        assignments = self.user_role_assignments.get(user_id, [])
        original_count = len(assignments)

        self.user_role_assignments[user_id] = [
            a for a in assignments if a.role_id != role_id
        ]

        if len(self.user_role_assignments[user_id]) < original_count:
            # Limpiar cache del usuario
            if user_id in self._user_permissions_cache:
                del self._user_permissions_cache[user_id]
            if user_id in self._last_cache_update:
                del self._last_cache_update[user_id]

            logger.info(f"🚫 Role {role_id} revoked from user {user_id}")
            return True

        return False

    def get_user_roles(self, user_id: str) -> List[UserRoleAssignment]:
        """
        Obtiene los roles asignados a un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Lista de asignaciones de roles activas
        """
        assignments = self.user_role_assignments.get(user_id, [])
        return [a for a in assignments if a.is_active()]

    def get_user_permissions(self, user_id: str, include_inherited: bool = True) -> Set[Tuple]:
        """
        Obtiene todos los permisos de un usuario

        Args:
            user_id: ID del usuario
            include_inherited: Si incluir permisos heredados de roles padre

        Returns:
            Set de tuplas (action, resource, scope, resource_id)
        """
        # Verificar cache
        if user_id in self._user_permissions_cache:
            cache_time = self._last_cache_update.get(user_id, datetime.min)
            if datetime.now() - cache_time < self._cache_expiration:
                return self._user_permissions_cache[user_id]

        permissions = set()
        visited_roles = set()

        def collect_permissions(role_id: str):
            if role_id in visited_roles:
                return
            visited_roles.add(role_id)

            role = self.roles.get(role_id)
            if not role or not role.active:
                return

            # Agregar permisos del rol
            for permission in role.permissions:
                perm_tuple = (
                    permission.action.value,
                    permission.resource.value,
                    permission.scope.value,
                    permission.resource_id
                )
                permissions.add(perm_tuple)

            # Recursivamente agregar permisos de roles padre
            if include_inherited:
                for parent_id in role.parent_roles:
                    collect_permissions(parent_id)

        # Obtener roles del usuario
        user_assignments = self.get_user_roles(user_id)
        for assignment in user_assignments:
            collect_permissions(assignment.role_id)

        # Cachear resultado
        self._user_permissions_cache[user_id] = permissions
        self._last_cache_update[user_id] = datetime.now()

        return permissions

    def check_permission(self, user_id: str, action: PermissionAction,
                        resource: PermissionResource,
                        scope: PermissionScope = PermissionScope.GLOBAL,
                        resource_id: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verifica si un usuario tiene un permiso específico

        Args:
            user_id: ID del usuario
            action: Acción solicitada
            resource: Recurso solicitado
            scope: Ámbito
            resource_id: ID del recurso
            context: Contexto adicional

        Returns:
            True si tiene el permiso
        """
        user_permissions = self.get_user_permissions(user_id)

        # Verificar permiso directo
        requested_perm = (action.value, resource.value, scope.value, resource_id)
        if requested_perm in user_permissions:
            return True

        # Verificar permisos con comodines (resource_id None)
        wildcard_perm = (action.value, resource.value, scope.value, None)
        if wildcard_perm in user_permissions:
            return True

        # Verificar permisos admin
        admin_perm = (PermissionAction.ADMIN.value, resource.value, scope.value, None)
        if admin_perm in user_permissions:
            return True

        # Verificar permisos admin global
        global_admin = (PermissionAction.ADMIN.value, PermissionResource.SYSTEM.value, PermissionScope.GLOBAL.value, None)
        if global_admin in user_permissions:
            return True

        return False

    def get_role_hierarchy(self, role_id: str) -> Dict[str, Any]:
        """
        Obtiene la jerarquía completa de un rol

        Args:
            role_id: ID del rol

        Returns:
            Dict con jerarquía
        """
        role = self.roles.get(role_id)
        if not role:
            return {}

        hierarchy = {
            'role': role.to_dict(),
            'parents': [],
            'children': []
        }

        # Agregar padres
        for parent_id in role.parent_roles:
            parent_hierarchy = self.get_role_hierarchy(parent_id)
            if parent_hierarchy:
                hierarchy['parents'].append(parent_hierarchy)

        # Agregar hijos
        for child_id in role.child_roles:
            child_hierarchy = self.get_role_hierarchy(child_id)
            if child_hierarchy:
                hierarchy['children'].append(child_hierarchy)

        return hierarchy

    def list_roles(self, include_inactive: bool = False) -> List[Role]:
        """
        Lista todos los roles

        Args:
            include_inactive: Si incluir roles inactivos

        Returns:
            Lista de roles
        """
        roles = list(self.roles.values())
        if not include_inactive:
            roles = [r for r in roles if r.active]
        return roles

    def get_users_with_role(self, role_id: str) -> List[str]:
        """
        Obtiene usuarios que tienen un rol específico

        Args:
            role_id: ID del rol

        Returns:
            Lista de IDs de usuario
        """
        users = []
        for user_id, assignments in self.user_role_assignments.items():
            if any(a.role_id == role_id and a.is_active() for a in assignments):
                users.append(user_id)
        return users

    def _clear_user_cache(self, user_id: Optional[str] = None):
        """Limpia el cache de permisos"""
        if user_id:
            if user_id in self._user_permissions_cache:
                del self._user_permissions_cache[user_id]
            if user_id in self._last_cache_update:
                del self._last_cache_update[user_id]
        else:
            self._user_permissions_cache.clear()
            self._last_cache_update.clear()

    def cleanup_expired_assignments(self):
        """Limpia asignaciones de roles expiradas"""
        current_time = datetime.now()
        cleaned = 0

        for user_id, assignments in self.user_role_assignments.items():
            original_count = len(assignments)
            self.user_role_assignments[user_id] = [
                a for a in assignments if a.is_active()
            ]
            cleaned += original_count - len(self.user_role_assignments[user_id])

        if cleaned > 0:
            logger.info(f"🧹 Cleaned up {cleaned} expired role assignments")
            self._clear_user_cache()

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema RBAC"""
        total_assignments = sum(len(assignments) for assignments in self.user_role_assignments.values())
        active_assignments = sum(
            len([a for a in assignments if a.is_active()])
            for assignments in self.user_role_assignments.values()
        )

        return {
            'total_roles': len(self.roles),
            'active_roles': len([r for r in self.roles.values() if r.active]),
            'total_users_with_roles': len(self.user_role_assignments),
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'cached_permissions': len(self._user_permissions_cache)
        }


# Instancia global del gestor RBAC
rbac_manager = RBACManager()


def get_rbac_manager() -> RBACManager:
    """Obtiene la instancia global del gestor RBAC"""
    return rbac_manager