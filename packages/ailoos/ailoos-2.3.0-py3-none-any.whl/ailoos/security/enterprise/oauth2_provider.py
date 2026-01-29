#!/usr/bin/env python3
"""
OAuth2 Provider con Scopes Avanzados
====================================

Implementa un servidor OAuth2 completo con soporte para múltiples flujos
de autorización, scopes avanzados, refresh tokens, PKCE, y gestión
de clientes y tokens.
"""

import base64
import hashlib
import hmac
import logging
import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlencode, parse_qs, urlparse
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OAuth2GrantType(Enum):
    """Tipos de grant OAuth2 soportados"""
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"

class OAuth2ResponseType(Enum):
    """Tipos de respuesta OAuth2"""
    CODE = "code"
    TOKEN = "token"

class OAuth2Scope(Enum):
    """Scopes OAuth2 avanzados"""
    # Scopes básicos
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

    # Scopes específicos de AILOOS
    MODEL_INFERENCE = "model:inference"
    MODEL_TRAIN = "model:train"
    MODEL_DEPLOY = "model:deploy"
    MODEL_MANAGE = "model:manage"

    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"

    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_ADMIN = "user:admin"

    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    TENANT_ADMIN = "tenant:admin"

    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"

    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"

    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WRITE = "compliance:write"

    FEDERATED_READ = "federated:read"
    FEDERATED_WRITE = "federated:write"
    FEDERATED_ADMIN = "federated:admin"

class OAuth2Error(Enum):
    """Errores OAuth2 estándar"""
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED_CLIENT = "unauthorized_client"
    ACCESS_DENIED = "access_denied"
    UNSUPPORTED_RESPONSE_TYPE = "unsupported_response_type"
    INVALID_SCOPE = "invalid_scope"
    SERVER_ERROR = "server_error"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    INVALID_CLIENT = "invalid_client"
    INVALID_GRANT = "invalid_grant"
    UNSUPPORTED_GRANT_TYPE = "unsupported_grant_type"

@dataclass
class OAuth2Client:
    """Cliente OAuth2 registrado"""
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    grant_types: List[OAuth2GrantType] = field(default_factory=lambda: [OAuth2GrantType.AUTHORIZATION_CODE])
    response_types: List[OAuth2ResponseType] = field(default_factory=lambda: [OAuth2ResponseType.CODE])
    scopes: List[OAuth2Scope] = field(default_factory=lambda: [OAuth2Scope.READ])
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    contacts: List[str] = field(default_factory=list)
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    jwks_uri: Optional[str] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class OAuth2AuthorizationCode:
    """Código de autorización OAuth2"""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: List[OAuth2Scope]
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=10))
    used: bool = False

@dataclass
class OAuth2AccessToken:
    """Token de acceso OAuth2"""
    token: str
    token_type: str = "Bearer"
    client_id: str
    user_id: Optional[str] = None
    scopes: List[OAuth2Scope] = field(default_factory=list)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    refresh_token: Optional[str] = None
    refresh_expires_at: Optional[datetime] = None

@dataclass
class OAuth2AuthorizationRequest:
    """Solicitud de autorización OAuth2"""
    response_type: OAuth2ResponseType
    client_id: str
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    nonce: Optional[str] = None

@dataclass
class OAuth2TokenRequest:
    """Solicitud de token OAuth2"""
    grant_type: OAuth2GrantType
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    code_verifier: Optional[str] = None

class OAuth2Provider:
    """
    Proveedor OAuth2 completo con scopes avanzados
    """

    def __init__(self, issuer: str = "https://ailoos.com/oauth2"):
        """
        Inicializa el proveedor OAuth2

        Args:
            issuer: URL del issuer OAuth2
        """
        self.issuer = issuer
        self.authorization_endpoint = f"{issuer}/authorize"
        self.token_endpoint = f"{issuer}/token"
        self.introspection_endpoint = f"{issuer}/introspect"
        self.revocation_endpoint = f"{issuer}/revoke"

        # Clientes registrados
        self.clients: Dict[str, OAuth2Client] = {}

        # Códigos de autorización pendientes
        self.authorization_codes: Dict[str, OAuth2AuthorizationCode] = {}

        # Tokens activos
        self.access_tokens: Dict[str, OAuth2AccessToken] = {}
        self.refresh_tokens: Dict[str, str] = {}  # refresh_token -> access_token

        # Configuración
        self.access_token_expiration = timedelta(hours=1)
        self.refresh_token_expiration = timedelta(days=30)
        self.authorization_code_expiration = timedelta(minutes=10)

        # Scopes disponibles
        self.available_scopes = set(OAuth2Scope)

        logger.info(f"🔐 OAuth2 Provider initialized: {issuer}")

    def register_client(self, client: OAuth2Client):
        """
        Registra un nuevo cliente OAuth2

        Args:
            client: Configuración del cliente
        """
        self.clients[client.client_id] = client
        logger.info(f"📝 OAuth2 client registered: {client.client_id}")

    def unregister_client(self, client_id: str) -> bool:
        """
        Desregistra un cliente OAuth2

        Args:
            client_id: ID del cliente

        Returns:
            True si se desregistró correctamente
        """
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"🚫 OAuth2 client unregistered: {client_id}")
            return True
        return False

    def validate_client(self, client_id: str, client_secret: Optional[str] = None,
                       redirect_uri: Optional[str] = None) -> Optional[OAuth2Client]:
        """
        Valida las credenciales de un cliente

        Args:
            client_id: ID del cliente
            client_secret: Secreto del cliente (opcional)
            redirect_uri: URI de redirección (opcional)

        Returns:
            Cliente si es válido, None si no
        """
        client = self.clients.get(client_id)
        if not client:
            return None

        # Validar secreto si se proporciona
        if client_secret and not self._verify_client_secret(client, client_secret):
            return None

        # Validar redirect URI si se proporciona
        if redirect_uri and redirect_uri not in client.redirect_uris:
            return None

        return client

    def create_authorization_request(self, request: OAuth2AuthorizationRequest) -> Tuple[str, Optional[str]]:
        """
        Crea una solicitud de autorización OAuth2

        Args:
            request: Solicitud de autorización

        Returns:
            Tuple de (URL de autorización, parámetros)

        Raises:
            ValueError: Si la solicitud es inválida
        """
        # Validar cliente
        client = self.validate_client(request.client_id, redirect_uri=request.redirect_uri)
        if not client:
            raise ValueError("Invalid client")

        # Validar response_type
        if request.response_type not in client.response_types:
            raise ValueError("Unsupported response type")

        # Validar redirect_uri
        if request.redirect_uri and request.redirect_uri not in client.redirect_uris:
            raise ValueError("Invalid redirect URI")

        # Usar primera redirect_uri si no se especifica
        redirect_uri = request.redirect_uri or client.redirect_uris[0]

        # Parsear y validar scopes
        scopes = self._parse_scopes(request.scope or "")
        if not scopes.issubset(set(client.scopes)):
            raise ValueError("Invalid scope")

        # Construir URL de autorización
        params = {
            'response_type': request.response_type.value,
            'client_id': request.client_id,
            'redirect_uri': redirect_uri,
            'state': request.state or self._generate_state()
        }

        if scopes:
            params['scope'] = ' '.join(scope.value for scope in scopes)

        if request.code_challenge:
            params['code_challenge'] = request.code_challenge
            params['code_challenge_method'] = request.code_challenge_method or 'S256'

        if request.nonce:
            params['nonce'] = request.nonce

        query_string = urlencode(params)
        auth_url = f"{self.authorization_endpoint}?{query_string}"

        return auth_url, redirect_uri

    def process_authorization_response(self, user_id: str, client_id: str, redirect_uri: str,
                                    scopes: List[OAuth2Scope], approved: bool = True,
                                    state: Optional[str] = None) -> str:
        """
        Procesa la respuesta de autorización del usuario

        Args:
            user_id: ID del usuario que autoriza
            client_id: ID del cliente
            redirect_uri: URI de redirección
            scopes: Scopes autorizados
            approved: Si el usuario aprobó
            state: Estado de la solicitud

        Returns:
            URL de redirección con código o error
        """
        if not approved:
            # Usuario denegó la autorización
            params = {
                'error': OAuth2Error.ACCESS_DENIED.value,
                'state': state or ''
            }
            return f"{redirect_uri}?{urlencode(params)}"

        # Generar código de autorización
        code = self._generate_authorization_code()
        code_challenge = None  # En implementación completa, obtener de la solicitud original

        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=code_challenge
        )

        self.authorization_codes[code] = auth_code

        # Construir respuesta de éxito
        params = {
            'code': code,
            'state': state or ''
        }

        return f"{redirect_uri}?{urlencode(params)}"

    def exchange_authorization_code(self, request: OAuth2TokenRequest) -> OAuth2AccessToken:
        """
        Intercambia un código de autorización por tokens

        Args:
            request: Solicitud de token

        Returns:
            Token de acceso

        Raises:
            ValueError: Si el código es inválido
        """
        if request.grant_type != OAuth2GrantType.AUTHORIZATION_CODE:
            raise ValueError("Invalid grant type")

        # Validar código
        auth_code = self.authorization_codes.get(request.code)
        if not auth_code or auth_code.used or datetime.now() > auth_code.expires_at:
            raise ValueError("Invalid authorization code")

        # Validar cliente
        client = self.validate_client(request.client_id or auth_code.client_id,
                                    request.client_secret,
                                    auth_code.redirect_uri)
        if not client:
            raise ValueError("Invalid client")

        # Validar redirect_uri
        if request.redirect_uri != auth_code.redirect_uri:
            raise ValueError("Invalid redirect URI")

        # Validar PKCE si está presente
        if auth_code.code_challenge:
            if not request.code_verifier:
                raise ValueError("Code verifier required")
            if not self._verify_pkce(auth_code.code_challenge, request.code_verifier,
                                   auth_code.code_challenge_method):
                raise ValueError("Invalid code verifier")

        # Marcar código como usado
        auth_code.used = True

        # Generar tokens
        access_token = self._generate_access_token(
            client_id=auth_code.client_id,
            user_id=auth_code.user_id,
            scopes=auth_code.scopes
        )

        return access_token

    def refresh_access_token(self, refresh_token: str, scope: Optional[str] = None) -> OAuth2AccessToken:
        """
        Refresca un token de acceso

        Args:
            refresh_token: Token de refresco
            scope: Nuevos scopes (opcional)

        Returns:
            Nuevo token de acceso

        Raises:
            ValueError: Si el refresh token es inválido
        """
        # Buscar token de acceso correspondiente
        access_token_key = self.refresh_tokens.get(refresh_token)
        if not access_token_key:
            raise ValueError("Invalid refresh token")

        access_token = self.access_tokens.get(access_token_key)
        if not access_token or not access_token.refresh_expires_at or \
           datetime.now() > access_token.refresh_expires_at:
            raise ValueError("Refresh token expired")

        # Validar scopes
        new_scopes = self._parse_scopes(scope or "")
        if new_scopes and not new_scopes.issubset(set(access_token.scopes)):
            raise ValueError("Invalid scope")

        scopes = new_scopes if new_scopes else access_token.scopes

        # Generar nuevo token
        new_access_token = self._generate_access_token(
            client_id=access_token.client_id,
            user_id=access_token.user_id,
            scopes=scopes
        )

        # Invalidar token anterior
        del self.access_tokens[access_token_key]
        del self.refresh_tokens[refresh_token]

        return new_access_token

    def validate_access_token(self, token: str) -> Optional[OAuth2AccessToken]:
        """
        Valida un token de acceso

        Args:
            token: Token de acceso

        Returns:
            Token si es válido, None si no
        """
        access_token = self.access_tokens.get(token)
        if not access_token or datetime.now() > access_token.expires_at:
            return None
        return access_token

    def revoke_token(self, token: str, token_type_hint: Optional[str] = None) -> bool:
        """
        Revoca un token

        Args:
            token: Token a revocar
            token_type_hint: Tipo de token (access_token o refresh_token)

        Returns:
            True si se revocó correctamente
        """
        if token_type_hint == "refresh_token":
            # Revocar refresh token
            if token in self.refresh_tokens:
                access_token_key = self.refresh_tokens[token]
                del self.refresh_tokens[token]
                if access_token_key in self.access_tokens:
                    del self.access_tokens[access_token_key]
                return True
        else:
            # Revocar access token
            if token in self.access_tokens:
                access_token = self.access_tokens[token]
                del self.access_tokens[token]
                # Revocar refresh token asociado
                if access_token.refresh_token and access_token.refresh_token in self.refresh_tokens:
                    del self.refresh_tokens[access_token.refresh_token]
                return True

        return False

    def introspect_token(self, token: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Introspecciona un token (RFC 7662)

        Args:
            token: Token a introspeccionar
            client_id: ID del cliente que solicita (opcional)

        Returns:
            Información del token
        """
        access_token = self.validate_access_token(token)
        if not access_token:
            return {"active": False}

        return {
            "active": True,
            "client_id": access_token.client_id,
            "username": access_token.user_id,
            "scope": ' '.join(scope.value for scope in access_token.scopes),
            "token_type": access_token.token_type,
            "exp": int(access_token.expires_at.timestamp()),
            "iat": int((access_token.expires_at - self.access_token_expiration).timestamp()),
            "iss": self.issuer
        }

    def _generate_authorization_code(self) -> str:
        """Genera un código de autorización único"""
        return secrets.token_urlsafe(32)

    def _generate_access_token(self, client_id: str, user_id: Optional[str] = None,
                             scopes: List[OAuth2Scope] = None) -> OAuth2AccessToken:
        """Genera un token de acceso"""
        token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        access_token = OAuth2AccessToken(
            token=token,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes or [],
            expires_at=datetime.now() + self.access_token_expiration,
            refresh_token=refresh_token,
            refresh_expires_at=datetime.now() + self.refresh_token_expiration
        )

        self.access_tokens[token] = access_token
        self.refresh_tokens[refresh_token] = token

        return access_token

    def _generate_state(self) -> str:
        """Genera un valor state único"""
        return secrets.token_urlsafe(16)

    def _parse_scopes(self, scope_string: str) -> Set[OAuth2Scope]:
        """Parsea string de scopes a conjunto de OAuth2Scope"""
        if not scope_string:
            return set()

        scopes = set()
        for scope_str in scope_string.split():
            try:
                scope = OAuth2Scope(scope_str)
                if scope in self.available_scopes:
                    scopes.add(scope)
            except ValueError:
                continue  # Ignorar scopes inválidos

        return scopes

    def _verify_client_secret(self, client: OAuth2Client, secret: str) -> bool:
        """Verifica el secreto del cliente"""
        # En producción, usar hash seguro
        return hmac.compare_digest(client.client_secret, secret)

    def _verify_pkce(self, challenge: str, verifier: str, method: str = "S256") -> bool:
        """Verifica PKCE (RFC 7636)"""
        if method == "S256":
            # Crear challenge desde verifier
            expected_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode()).digest()
            ).decode().rstrip('=')
            return hmac.compare_digest(challenge, expected_challenge)
        elif method == "plain":
            return hmac.compare_digest(challenge, verifier)
        else:
            return False

    def cleanup_expired_tokens(self):
        """Limpia tokens expirados"""
        current_time = datetime.now()
        expired_access = []
        expired_refresh = []

        # Tokens de acceso expirados
        for token, access_token in self.access_tokens.items():
            if current_time > access_token.expires_at:
                expired_access.append(token)

        # Tokens de refresco expirados
        for refresh_token, access_token_key in self.refresh_tokens.items():
            access_token = self.access_tokens.get(access_token_key)
            if not access_token or not access_token.refresh_expires_at or \
               current_time > access_token.refresh_expires_at:
                expired_refresh.append(refresh_token)

        # Limpiar
        for token in expired_access:
            del self.access_tokens[token]

        for refresh_token in expired_refresh:
            del self.refresh_tokens[refresh_token]

        # Códigos de autorización expirados
        expired_codes = []
        for code, auth_code in self.authorization_codes.items():
            if current_time > auth_code.expires_at:
                expired_codes.append(code)

        for code in expired_codes:
            del self.authorization_codes[code]

        total_cleaned = len(expired_access) + len(expired_refresh) + len(expired_codes)
        if total_cleaned > 0:
            logger.info(f"🧹 Cleaned up {total_cleaned} expired OAuth2 tokens/codes")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema OAuth2"""
        return {
            'registered_clients': len(self.clients),
            'active_access_tokens': len(self.access_tokens),
            'active_refresh_tokens': len(self.refresh_tokens),
            'pending_auth_codes': len(self.authorization_codes)
        }

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un cliente (para discovery)"""
        client = self.clients.get(client_id)
        if not client:
            return None

        return {
            "client_id": client.client_id,
            "client_name": client.client_name,
            "client_uri": client.client_uri,
            "logo_uri": client.logo_uri,
            "tos_uri": client.tos_uri,
            "policy_uri": client.policy_uri,
            "software_id": client.software_id,
            "software_version": client.software_version
        }


# Instancia global del proveedor OAuth2
oauth2_provider = OAuth2Provider()


def get_oauth2_provider() -> OAuth2Provider:
    """Obtiene la instancia global del proveedor OAuth2"""
    return oauth2_provider