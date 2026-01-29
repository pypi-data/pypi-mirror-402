#!/usr/bin/env python3
"""
LDAP Integration para Active Directory
=====================================

Implementa integración completa con servidores LDAP/Active Directory
para autenticación, búsqueda de usuarios, grupos, y sincronización
de atributos de usuario.
"""

import logging
import ssl
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import hmac

# Necesita instalar: pip install ldap3
try:
    import ldap3
    from ldap3 import Server, Connection, ALL, SUBTREE, BASE, LEVEL
    from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPInvalidCredentialsResult
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    logging.warning("ldap3 not available. LDAP integration will be disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LDAPAuthMethod(Enum):
    """Métodos de autenticación LDAP"""
    SIMPLE = "simple"
    SASL_DIGEST_MD5 = "DIGEST-MD5"
    SASL_GSSAPI = "GSSAPI"
    NTLM = "NTLM"

class LDAPSearchScope(Enum):
    """Ámbitos de búsqueda LDAP"""
    BASE = BASE
    LEVEL = LEVEL
    SUBTREE = SUBTREE

class LDAPObjectClass(Enum):
    """Clases de objeto LDAP comunes"""
    PERSON = "person"
    USER = "user"
    GROUP = "group"
    ORGANIZATIONAL_UNIT = "organizationalUnit"
    COMPUTER = "computer"

@dataclass
class LDAPServerConfig:
    """Configuración de servidor LDAP"""
    host: str
    port: int = 389
    use_ssl: bool = False
    use_tls: bool = True
    timeout: int = 30
    get_info: str = "ALL"  # SCHEMA, ALL, DSA, OFF
    mode: str = "IP_V4_ONLY"  # IP_V4_ONLY, IP_V6_ONLY, IP_V4_PREFERRED, IP_V6_PREFERRED

@dataclass
class LDAPConnectionConfig:
    """Configuración de conexión LDAP"""
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    auth_method: LDAPAuthMethod = LDAPAuthMethod.SIMPLE
    auto_bind: bool = True
    client_strategy: str = "SYNC"  # SYNC, ASYNC, LDIF, RESTARTABLE
    check_names: bool = True
    read_only: bool = False
    lazy: bool = False
    pool_name: str = "default"
    pool_size: int = 10
    pool_lifetime: int = 3600

@dataclass
class LDAPUser:
    """Usuario LDAP"""
    dn: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    last_login: Optional[datetime] = None
    account_disabled: bool = False
    password_expired: bool = False
    locked: bool = False

@dataclass
class LDAPGroup:
    """Grupo LDAP"""
    dn: str
    name: str
    description: Optional[str] = None
    members: List[str] = field(default_factory=list)  # DNs de miembros
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LDAPSearchResult:
    """Resultado de búsqueda LDAP"""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    search_time: float = 0.0

class LDAPIntegration:
    """
    Integración completa con LDAP/Active Directory
    """

    def __init__(self, server_config: LDAPServerConfig, connection_config: LDAPConnectionConfig,
                 base_dn: str, user_search_filter: str = "(objectClass=user)",
                 group_search_filter: str = "(objectClass=group)"):
        """
        Inicializa la integración LDAP

        Args:
            server_config: Configuración del servidor
            connection_config: Configuración de conexión
            base_dn: DN base para búsquedas
            user_search_filter: Filtro para búsqueda de usuarios
            group_search_filter: Filtro para búsqueda de grupos
        """
        if not LDAP_AVAILABLE:
            raise ImportError("ldap3 library is required for LDAP integration")

        self.server_config = server_config
        self.connection_config = connection_config
        self.base_dn = base_dn
        self.user_search_filter = user_search_filter
        self.group_search_filter = group_search_filter

        # Cache de conexiones
        self._connections: Dict[str, Connection] = {}
        self._server = None

        # Cache de usuarios y grupos
        self._user_cache: Dict[str, LDAPUser] = {}
        self._group_cache: Dict[str, LDAPGroup] = {}
        self._cache_expiration = timedelta(minutes=30)
        self._last_cache_update = datetime.min

        # Configuración de atributos
        self.user_attributes = [
            'dn', 'cn', 'sn', 'givenName', 'displayName', 'mail', 'sAMAccountName',
            'userPrincipalName', 'memberOf', 'userAccountControl', 'pwdLastSet',
            'accountExpires', 'lockoutTime', 'badPasswordTime', 'lastLogon'
        ]

        self.group_attributes = [
            'dn', 'cn', 'description', 'member', 'memberOf', 'sAMAccountName',
            'groupType', 'objectSid'
        ]

        logger.info(f"🔗 LDAP Integration initialized for {server_config.host}:{server_config.port}")

    def connect(self, key: str = "default") -> Connection:
        """
        Establece conexión con el servidor LDAP

        Args:
            key: Clave para identificar la conexión

        Returns:
            Conexión LDAP

        Raises:
            LDAPException: Si falla la conexión
        """
        if key in self._connections:
            conn = self._connections[key]
            if conn.bound:
                return conn

        # Crear servidor
        if not self._server:
            tls_config = None
            if self.server_config.use_tls:
                tls_config = ldap3.Tls(validate=ssl.CERT_NONE)  # En producción, validar certificados

            self._server = Server(
                host=self.server_config.host,
                port=self.server_config.port,
                use_ssl=self.server_config.use_ssl,
                tls=tls_config,
                get_info=self.server_config.get_info,
                mode=self.server_config.mode,
                connect_timeout=self.server_config.timeout
            )

        # Crear conexión
        conn = Connection(
            server=self._server,
            user=self.connection_config.bind_dn,
            password=self.connection_config.bind_password,
            authentication=self.connection_config.auth_method.value,
            auto_bind=self.connection_config.auto_bind,
            client_strategy=self.connection_config.client_strategy,
            check_names=self.connection_config.check_names,
            read_only=self.connection_config.read_only,
            lazy=self.connection_config.lazy,
            pool_name=self.connection_config.pool_name,
            pool_size=self.connection_config.pool_size,
            pool_lifetime=self.connection_config.pool_lifetime
        )

        # Bind si no es auto_bind
        if not self.connection_config.auto_bind:
            if not conn.bind():
                raise LDAPBindError(f"Failed to bind to LDAP server: {conn.result}")

        self._connections[key] = conn
        logger.info(f"🔗 LDAP connection established: {key}")
        return conn

    def disconnect(self, key: str = "default"):
        """
        Cierra conexión LDAP

        Args:
            key: Clave de la conexión
        """
        if key in self._connections:
            conn = self._connections[key]
            conn.unbind()
            del self._connections[key]
            logger.info(f"🔌 LDAP connection closed: {key}")

    def authenticate_user(self, username: str, password: str, domain: Optional[str] = None) -> Optional[LDAPUser]:
        """
        Autentica un usuario contra LDAP

        Args:
            username: Nombre de usuario
            password: Contraseña
            domain: Dominio (opcional)

        Returns:
            Usuario LDAP si la autenticación es exitosa, None si falla
        """
        try:
            # Construir DN del usuario
            if domain:
                user_dn = f"cn={username},cn=users,dc={domain.replace('.', ',dc=')}"
            else:
                # Buscar DN del usuario primero
                user_info = self.get_user_info(username)
                if not user_info:
                    return None
                user_dn = user_info.dn

            # Intentar bind con credenciales del usuario
            conn = Connection(
                server=self._server,
                user=user_dn,
                password=password,
                authentication=LDAPAuthMethod.SIMPLE.value,
                auto_bind=True
            )

            if conn.bound:
                # Autenticación exitosa, obtener información completa del usuario
                user = self.get_user_info(username)
                if user:
                    user.last_login = datetime.now()
                conn.unbind()
                return user
            else:
                logger.warning(f"❌ LDAP authentication failed for user: {username}")
                return None

        except LDAPInvalidCredentialsResult:
            logger.warning(f"❌ Invalid credentials for user: {username}")
            return None
        except Exception as e:
            logger.error(f"❌ LDAP authentication error for user {username}: {e}")
            return None

    def get_user_info(self, username: str, use_cache: bool = True) -> Optional[LDAPUser]:
        """
        Obtiene información de un usuario LDAP

        Args:
            username: Nombre de usuario
            use_cache: Si usar cache

        Returns:
            Usuario LDAP o None si no encontrado
        """
        # Verificar cache
        if use_cache and username in self._user_cache:
            cached_user = self._user_cache[username]
            if datetime.now() - self._last_cache_update < self._cache_expiration:
                return cached_user

        try:
            conn = self.connect()

            # Buscar usuario
            search_filter = f"(&(sAMAccountName={username}){self.user_search_filter})"
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=self.user_attributes
            )

            if not conn.entries:
                return None

            entry = conn.entries[0]
            user = self._parse_user_entry(entry)

            # Cachear resultado
            if use_cache:
                self._user_cache[username] = user

            return user

        except Exception as e:
            logger.error(f"❌ Error getting user info for {username}: {e}")
            return None

    def get_group_info(self, group_name: str, use_cache: bool = True) -> Optional[LDAPGroup]:
        """
        Obtiene información de un grupo LDAP

        Args:
            group_name: Nombre del grupo
            use_cache: Si usar cache

        Returns:
            Grupo LDAP o None si no encontrado
        """
        # Verificar cache
        if use_cache and group_name in self._group_cache:
            cached_group = self._group_cache[group_name]
            if datetime.now() - self._last_cache_update < self._cache_expiration:
                return cached_group

        try:
            conn = self.connect()

            # Buscar grupo
            search_filter = f"(&(sAMAccountName={group_name}){self.group_search_filter})"
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=self.group_attributes
            )

            if not conn.entries:
                return None

            entry = conn.entries[0]
            group = self._parse_group_entry(entry)

            # Cachear resultado
            if use_cache:
                self._group_cache[group_name] = group

            return group

        except Exception as e:
            logger.error(f"❌ Error getting group info for {group_name}: {e}")
            return None

    def search_users(self, search_filter: str = "", attributes: Optional[List[str]] = None,
                    search_scope: LDAPSearchScope = LDAPSearchScope.SUBTREE) -> LDAPSearchResult:
        """
        Busca usuarios en LDAP

        Args:
            search_filter: Filtro de búsqueda adicional
            attributes: Atributos a recuperar
            search_scope: Ámbito de búsqueda

        Returns:
            Resultado de búsqueda
        """
        start_time = time.time()

        try:
            conn = self.connect()

            # Construir filtro completo
            full_filter = f"(&(objectClass=user){self.user_search_filter}"
            if search_filter:
                full_filter += search_filter
            full_filter += ")"

            # Buscar
            conn.search(
                search_base=self.base_dn,
                search_filter=full_filter,
                search_scope=search_scope.value,
                attributes=attributes or self.user_attributes
            )

            # Parsear resultados
            entries = []
            for entry in conn.entries:
                entries.append({
                    'dn': entry.entry_dn,
                    'attributes': dict(entry.entry_attributes_as_dict)
                })

            search_time = time.time() - start_time

            return LDAPSearchResult(
                entries=entries,
                total_count=len(entries),
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return LDAPSearchResult(search_time=time.time() - start_time)

    def search_groups(self, search_filter: str = "", attributes: Optional[List[str]] = None,
                     search_scope: LDAPSearchScope = LDAPSearchScope.SUBTREE) -> LDAPSearchResult:
        """
        Busca grupos en LDAP

        Args:
            search_filter: Filtro de búsqueda adicional
            attributes: Atributos a recuperar
            search_scope: Ámbito de búsqueda

        Returns:
            Resultado de búsqueda
        """
        start_time = time.time()

        try:
            conn = self.connect()

            # Construir filtro completo
            full_filter = f"(&(objectClass=group){self.group_search_filter}"
            if search_filter:
                full_filter += search_filter
            full_filter += ")"

            # Buscar
            conn.search(
                search_base=self.base_dn,
                search_filter=full_filter,
                search_scope=search_scope.value,
                attributes=attributes or self.group_attributes
            )

            # Parsear resultados
            entries = []
            for entry in conn.entries:
                entries.append({
                    'dn': entry.entry_dn,
                    'attributes': dict(entry.entry_attributes_as_dict)
                })

            search_time = time.time() - start_time

            return LDAPSearchResult(
                entries=entries,
                total_count=len(entries),
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"❌ Error searching groups: {e}")
            return LDAPSearchResult(search_time=time.time() - start_time)

    def get_user_groups(self, username: str) -> List[str]:
        """
        Obtiene los grupos de un usuario

        Args:
            username: Nombre de usuario

        Returns:
            Lista de nombres de grupos
        """
        user = self.get_user_info(username)
        return user.groups if user else []

    def is_user_in_group(self, username: str, group_name: str) -> bool:
        """
        Verifica si un usuario pertenece a un grupo

        Args:
            username: Nombre de usuario
            group_name: Nombre del grupo

        Returns:
            True si pertenece al grupo
        """
        groups = self.get_user_groups(username)
        return group_name in groups

    def sync_user_attributes(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Sincroniza atributos de usuario desde LDAP

        Args:
            username: Nombre de usuario

        Returns:
            Atributos sincronizados o None si falla
        """
        user = self.get_user_info(username, use_cache=False)
        if not user:
            return None

        # Mapear atributos LDAP a atributos de aplicación
        synced_attributes = {
            'username': user.username,
            'display_name': user.display_name,
            'email': user.email,
            'groups': user.groups,
            'account_disabled': user.account_disabled,
            'password_expired': user.password_expired,
            'locked': user.locked,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'ldap_dn': user.dn,
            'synced_at': datetime.now().isoformat()
        }

        # Agregar atributos adicionales
        for key, value in user.attributes.items():
            if key not in ['dn', 'memberOf']:  # Excluir atributos ya mapeados
                synced_attributes[f"ldap_{key}"] = value

        return synced_attributes

    def validate_user_account(self, username: str) -> Dict[str, bool]:
        """
        Valida el estado de la cuenta de usuario

        Args:
            username: Nombre de usuario

        Returns:
            Dict con estados de validación
        """
        user = self.get_user_info(username)
        if not user:
            return {
                'exists': False,
                'enabled': False,
                'password_valid': False,
                'not_locked': False,
                'not_expired': False
            }

        return {
            'exists': True,
            'enabled': not user.account_disabled,
            'password_valid': not user.password_expired,
            'not_locked': not user.locked,
            'not_expired': True  # Simplificado
        }

    def _parse_user_entry(self, entry) -> LDAPUser:
        """Parsea una entrada de usuario LDAP"""
        attrs = entry.entry_attributes_as_dict

        # Extraer información básica
        dn = entry.entry_dn
        username = attrs.get('sAMAccountName', [attrs.get('cn', [''])[0]])[0]
        display_name = attrs.get('displayName', [None])[0]
        email = attrs.get('mail', [None])[0]

        # Extraer grupos
        groups = []
        member_of = attrs.get('memberOf', [])
        for group_dn in member_of:
            # Extraer CN del DN del grupo
            if 'CN=' in group_dn:
                cn_start = group_dn.find('CN=') + 3
                cn_end = group_dn.find(',', cn_start)
                if cn_end == -1:
                    cn_end = len(group_dn)
                groups.append(group_dn[cn_start:cn_end])

        # Verificar estado de la cuenta (Active Directory)
        user_account_control = attrs.get('userAccountControl', [0])[0]
        account_disabled = bool(user_account_control & 0x0002)
        password_expired = bool(user_account_control & 0x800000)

        # Verificar si está bloqueado
        lockout_time = attrs.get('lockoutTime', [0])[0]
        locked = lockout_time != 0

        return LDAPUser(
            dn=dn,
            username=username,
            display_name=display_name,
            email=email,
            groups=groups,
            attributes=dict(attrs),
            account_disabled=account_disabled,
            password_expired=password_expired,
            locked=locked
        )

    def _parse_group_entry(self, entry) -> LDAPGroup:
        """Parsea una entrada de grupo LDAP"""
        attrs = entry.entry_attributes_as_dict

        dn = entry.entry_dn
        name = attrs.get('sAMAccountName', [attrs.get('cn', [''])[0]])[0]
        description = attrs.get('description', [None])[0]
        members = attrs.get('member', [])

        return LDAPGroup(
            dn=dn,
            name=name,
            description=description,
            members=members,
            attributes=dict(attrs)
        )

    def clear_cache(self):
        """Limpia el cache de usuarios y grupos"""
        self._user_cache.clear()
        self._group_cache.clear()
        self._last_cache_update = datetime.min
        logger.info("🧹 LDAP cache cleared")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de conexiones"""
        stats = {
            'active_connections': len(self._connections),
            'cached_users': len(self._user_cache),
            'cached_groups': len(self._group_cache),
            'cache_age_seconds': (datetime.now() - self._last_cache_update).total_seconds()
        }

        return stats

    def test_connection(self) -> bool:
        """
        Prueba la conexión al servidor LDAP

        Returns:
            True si la conexión es exitosa
        """
        try:
            conn = self.connect("test")
            result = conn.search(self.base_dn, '(objectClass=*)', BASE)
            self.disconnect("test")
            return result
        except Exception as e:
            logger.error(f"❌ LDAP connection test failed: {e}")
            return False


# Instancia global de integración LDAP
ldap_integration = None


def get_ldap_integration() -> Optional[LDAPIntegration]:
    """Obtiene la instancia global de integración LDAP"""
    return ldap_integration


def initialize_ldap_integration(server_config: LDAPServerConfig,
                              connection_config: LDAPConnectionConfig,
                              base_dn: str) -> LDAPIntegration:
    """
    Inicializa la integración LDAP global

    Args:
        server_config: Configuración del servidor
        connection_config: Configuración de conexión
        base_dn: DN base

    Returns:
        Instancia de LDAPIntegration
    """
    global ldap_integration
    ldap_integration = LDAPIntegration(server_config, connection_config, base_dn)
    return ldap_integration