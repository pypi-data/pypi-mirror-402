#!/usr/bin/env python3
"""
TenantSecurity - Seguridad y permisos por tenant para Ailoos FASE 8
=================================================================

Sistema de seguridad multi-tenant con:
- Control de acceso basado en roles por tenant
- Políticas de seguridad específicas por tenant
- Encriptación de datos por tenant
- Auditoría de seguridad por tenant
- Gestión de API keys y tokens por tenant
"""

import asyncio
import logging
import hashlib
import secrets
import jwt
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Permission(Enum):
    """Permisos disponibles en el sistema"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    BILLING = "billing"
    TRAINING = "training"
    INFERENCE = "inference"
    MONITORING = "monitoring"

class Role(Enum):
    """Roles predefinidos"""
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"

@dataclass
class TenantRole:
    """Definición de rol por tenant"""
    role_id: str
    tenant_id: str
    name: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class TenantUser:
    """Usuario dentro de un tenant"""
    user_id: str
    tenant_id: str
    email: str
    roles: Set[str] = field(default_factory=set)  # role_ids
    permissions: Set[Permission] = field(default_factory=set)  # permisos efectivos
    api_keys: List[str] = field(default_factory=list)
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SecurityPolicy:
    """Política de seguridad por tenant"""
    policy_id: str
    tenant_id: str
    name: str
    rules: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AuditEvent:
    """Evento de auditoría de seguridad"""
    event_id: str
    tenant_id: str
    user_id: Optional[str]
    action: str
    resource: str
    result: str  # success, failure, denied
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class TenantSecurity:
    """
    Sistema de seguridad completo para multi-tenancy
    """

    def __init__(self, tenant_manager, encryption_key: str = None):
        self.tenant_manager = tenant_manager
        self.encryption_key = encryption_key or secrets.token_bytes(32)

        # Almacenamiento de datos de seguridad
        self.roles: Dict[str, TenantRole] = {}  # role_id -> role
        self.users: Dict[str, TenantUser] = {}  # user_id -> user
        self.policies: Dict[str, SecurityPolicy] = {}  # policy_id -> policy
        self.audit_log: List[AuditEvent] = []

        # JWT configuration
        self.jwt_secret = secrets.token_urlsafe(64)
        self.jwt_algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)

        # Rate limiting para seguridad
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

        # Roles por defecto
        self._initialize_default_roles()

        logger.info("🔐 TenantSecurity initialized")

    def _initialize_default_roles(self):
        """Inicializar roles por defecto para todos los tenants"""
        default_roles = {
            Role.OWNER.value: {
                'permissions': {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.BILLING},
                'description': 'Full access to tenant resources'
            },
            Role.ADMIN.value: {
                'permissions': {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.TRAINING, Permission.INFERENCE},
                'description': 'Administrative access to tenant'
            },
            Role.DEVELOPER.value: {
                'permissions': {Permission.READ, Permission.WRITE, Permission.TRAINING, Permission.INFERENCE},
                'description': 'Development and training access'
            },
            Role.ANALYST.value: {
                'permissions': {Permission.READ, Permission.INFERENCE, Permission.MONITORING},
                'description': 'Analysis and monitoring access'
            },
            Role.VIEWER.value: {
                'permissions': {Permission.READ, Permission.MONITORING},
                'description': 'Read-only access'
            }
        }

        # Estos se crearán cuando se cree un tenant
        self.default_role_templates = default_roles

    async def create_tenant_security(self, tenant_id: str) -> bool:
        """
        Inicializar estructura de seguridad para un tenant
        """
        try:
            # Crear roles por defecto para el tenant
            for role_name, role_data in self.default_role_templates.items():
                role_id = f"{tenant_id}_{role_name}"
                role = TenantRole(
                    role_id=role_id,
                    tenant_id=tenant_id,
                    name=role_name,
                    permissions=role_data['permissions'],
                    description=role_data['description']
                )
                self.roles[role_id] = role

            # Crear política de seguridad por defecto
            policy = SecurityPolicy(
                policy_id=f"{tenant_id}_default",
                tenant_id=tenant_id,
                name="Default Security Policy",
                rules={
                    'password_min_length': 8,
                    'require_2fa': False,
                    'session_timeout': 3600,  # 1 hour
                    'max_api_keys_per_user': 5,
                    'audit_all_actions': True
                }
            )
            self.policies[policy.policy_id] = policy

            logger.info(f"🔐 Security initialized for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize security for tenant {tenant_id}: {e}")
            return False

    async def create_user(self, tenant_id: str, email: str, initial_role: str = Role.VIEWER.value) -> Optional[TenantUser]:
        """
        Crear usuario en un tenant
        """
        # Verificar que el tenant existe
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return None

        # Verificar email único en el tenant
        for user in self.users.values():
            if user.tenant_id == tenant_id and user.email == email:
                return None

        user_id = f"{tenant_id}_{email.replace('@', '_').replace('.', '_')}"
        role_id = f"{tenant_id}_{initial_role}"

        # Verificar que el rol existe
        if role_id not in self.roles:
            logger.error(f"Role {role_id} not found for tenant {tenant_id}")
            return None

        user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            roles={role_id}
        )

        # Calcular permisos efectivos
        user.permissions = self._calculate_user_permissions(user)

        self.users[user_id] = user

        # Auditar creación
        await self.audit_event(tenant_id, None, "user_created", f"user:{user_id}", "success", {
            'email': email,
            'initial_role': initial_role
        })

        logger.info(f"👤 User created: {email} in tenant {tenant_id}")
        return user

    async def authenticate_user(self, tenant_id: str, email: str, password: str) -> Optional[str]:
        """
        Autenticar usuario y devolver token JWT
        """
        # Verificar rate limiting
        if self._is_account_locked(email):
            await self.audit_event(tenant_id, None, "login_failed", f"user:{email}", "denied", {
                'reason': 'account_locked'
            })
            return None

        # Buscar usuario
        user = None
        for u in self.users.values():
            if u.tenant_id == tenant_id and u.email == email:
                user = u
                break

        if not user or not user.is_active:
            self._record_failed_attempt(email)
            await self.audit_event(tenant_id, None, "login_failed", f"user:{email}", "failure", {
                'reason': 'invalid_credentials'
            })
            return None

        # En implementación real, verificaría hash de password
        # Por ahora, simular verificación
        if not self._verify_password(password, user.user_id):
            self._record_failed_attempt(email)
            await self.audit_event(tenant_id, user.user_id, "login_failed", f"user:{user.user_id}", "failure", {
                'reason': 'invalid_password'
            })
            return None

        # Limpiar intentos fallidos
        if email in self.failed_attempts:
            del self.failed_attempts[email]

        # Actualizar último login
        user.last_login = datetime.now()

        # Generar token JWT
        token = self._generate_jwt_token(user)

        await self.audit_event(tenant_id, user.user_id, "login_success", f"user:{user.user_id}", "success")

        logger.info(f"🔑 User authenticated: {email} in tenant {tenant_id}")
        return token

    def _verify_password(self, password: str, user_id: str) -> bool:
        """Verificar password (simulado)"""
        # En implementación real, verificaría hash
        return len(password) >= 8

    def _generate_jwt_token(self, user: TenantUser) -> str:
        """Generar token JWT para usuario"""
        payload = {
            'user_id': user.user_id,
            'tenant_id': user.tenant_id,
            'email': user.email,
            'permissions': [p.value for p in user.permissions],
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validar token JWT y devolver claims
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Verificar expiración
            exp = datetime.fromtimestamp(payload['exp'])
            if datetime.utcnow() > exp:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def check_permission(self, tenant_id: str, user_id: str, permission: Permission, resource: str = "") -> bool:
        """
        Verificar si usuario tiene un permiso específico
        """
        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id or not user.is_active:
            return False

        # Verificar permiso directo
        if permission in user.permissions:
            await self.audit_event(tenant_id, user_id, "permission_check", resource, "success", {
                'permission': permission.value,
                'granted': True
            })
            return True

        await self.audit_event(tenant_id, user_id, "permission_check", resource, "denied", {
            'permission': permission.value,
            'granted': False
        })
        return False

    async def get_tenant_permissions(self, tenant_id: str, user_id: Optional[str] = None) -> List[str]:
        """
        Obtener lista de permisos para un usuario en un tenant
        """
        if not user_id:
            return []

        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id:
            return []

        return [p.value for p in user.permissions]

    def _calculate_user_permissions(self, user: TenantUser) -> Set[Permission]:
        """Calcular permisos efectivos de un usuario"""
        permissions = set()

        for role_id in user.roles:
            role = self.roles.get(role_id)
            if role:
                permissions.update(role.permissions)

        return permissions

    async def assign_role(self, tenant_id: str, user_id: str, role_name: str) -> bool:
        """
        Asignar rol a usuario
        """
        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id:
            return False

        role_id = f"{tenant_id}_{role_name}"
        if role_id not in self.roles:
            return False

        user.roles.add(role_id)
        user.permissions = self._calculate_user_permissions(user)
        user.updated_at = datetime.now()

        await self.audit_event(tenant_id, None, "role_assigned", f"user:{user_id}", "success", {
            'role': role_name
        })

        logger.info(f"👥 Role {role_name} assigned to user {user.email}")
        return True

    async def create_api_key(self, tenant_id: str, user_id: str, name: str = "") -> Optional[str]:
        """
        Crear API key para usuario
        """
        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id:
            return None

        # Verificar límite de API keys
        policy = self.policies.get(f"{tenant_id}_default")
        max_keys = policy.rules.get('max_api_keys_per_user', 5) if policy else 5

        if len(user.api_keys) >= max_keys:
            return None

        # Generar API key
        api_key = secrets.token_urlsafe(32)
        user.api_keys.append(api_key)

        await self.audit_event(tenant_id, user_id, "api_key_created", f"key:{name}", "success")

        logger.info(f"🔑 API key created for user {user.email}")
        return api_key

    async def revoke_api_key(self, tenant_id: str, user_id: str, api_key: str) -> bool:
        """
        Revocar API key
        """
        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id:
            return False

        if api_key in user.api_keys:
            user.api_keys.remove(api_key)
            await self.audit_event(tenant_id, user_id, "api_key_revoked", f"key:{api_key[:8]}...", "success")
            return True

        return False

    def _record_failed_attempt(self, identifier: str):
        """Registrar intento fallido de autenticación"""
        now = datetime.now()

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        self.failed_attempts[identifier].append(now)

        # Limpiar intentos antiguos
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]

    def _is_account_locked(self, identifier: str) -> bool:
        """Verificar si cuenta está bloqueada por intentos fallidos"""
        if identifier not in self.failed_attempts:
            return False

        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if datetime.now() - attempt < self.lockout_duration
        ]

        return len(recent_attempts) >= self.max_failed_attempts

    async def audit_event(self, tenant_id: str, user_id: Optional[str], action: str,
                         resource: str, result: str, details: Optional[Dict[str, Any]] = None):
        """
        Registrar evento de auditoría
        """
        event = AuditEvent(
            event_id=secrets.token_hex(16),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details or {}
        )

        self.audit_log.append(event)

        # Mantener log limitado
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]

    async def get_audit_log(self, tenant_id: str, user_id: Optional[str] = None,
                           action: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        """
        Obtener log de auditoría filtrado
        """
        events = self.audit_log

        # Filtrar por tenant
        events = [e for e in events if e.tenant_id == tenant_id]

        # Filtrar por usuario
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        # Filtrar por acción
        if action:
            events = [e for e in events if e.action == action]

        # Ordenar por timestamp descendente y limitar
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def encrypt_tenant_data(self, tenant_id: str, data: str) -> str:
        """
        Encriptar datos específicos del tenant
        """
        # En implementación real, usaría AES con tenant-specific key
        # Por ahora, simular encriptación
        key = hashlib.sha256(f"{self.encryption_key}_{tenant_id}".encode()).digest()
        # Simular encriptación simple
        encrypted = hashlib.sha256((data + str(key)).encode()).hexdigest()
        return encrypted

    async def get_security_report(self, tenant_id: str) -> Dict[str, Any]:
        """
        Generar reporte de seguridad para un tenant
        """
        report = {
            'tenant_id': tenant_id,
            'total_users': 0,
            'active_users': 0,
            'total_roles': 0,
            'total_api_keys': 0,
            'recent_audit_events': 0,
            'failed_login_attempts': 0,
            'security_score': 0
        }

        # Contar usuarios
        tenant_users = [u for u in self.users.values() if u.tenant_id == tenant_id]
        report['total_users'] = len(tenant_users)
        report['active_users'] = len([u for u in tenant_users if u.is_active])

        # Contar roles
        tenant_roles = [r for r in self.roles.values() if r.tenant_id == tenant_id]
        report['total_roles'] = len(tenant_roles)

        # Contar API keys
        report['total_api_keys'] = sum(len(u.api_keys) for u in tenant_users)

        # Eventos de auditoría recientes
        recent_events = [e for e in self.audit_log
                        if e.tenant_id == tenant_id and
                        (datetime.now() - e.timestamp) < timedelta(days=7)]
        report['recent_audit_events'] = len(recent_events)

        # Intentos fallidos
        report['failed_login_attempts'] = len([
            e for e in recent_events
            if e.action == 'login_failed'
        ])

        # Calcular score de seguridad básico
        score = 100
        if report['failed_login_attempts'] > 10:
            score -= 20
        if report['total_api_keys'] > report['total_users'] * 2:
            score -= 10
        if not any(r.permissions for r in tenant_roles):
            score -= 30

        report['security_score'] = max(0, score)

        return report