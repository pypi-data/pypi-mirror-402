import requests
import json
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class OAuthProvider(ABC):
    """
    Clase base abstracta para proveedores OAuth 2.0.
    Proporciona funcionalidades comunes para autenticación OAuth.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    @abstractmethod
    def auth_url(self) -> str:
        """URL de autorización del proveedor."""
        pass

    @property
    @abstractmethod
    def token_url(self) -> str:
        """URL para intercambio de tokens."""
        pass

    @property
    @abstractmethod
    def default_scope(self) -> str:
        """Scope por defecto para el proveedor."""
        pass

    @property
    @abstractmethod
    def validation_url(self) -> Optional[str]:
        """URL para validar tokens, si aplica."""
        pass

    def get_authorization_url(self, scope: Optional[str] = None, state: Optional[str] = None) -> str:
        """
        Genera la URL de autorización para iniciar el flujo OAuth.

        Args:
            scope: Scopes solicitados (opcional, usa default si no se especifica)
            state: Estado para prevenir CSRF (opcional)

        Returns:
            URL de autorización completa
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope or self.default_scope,
        }
        if state:
            params['state'] = state

        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Intercambia el código de autorización por tokens de acceso.

        Args:
            code: Código de autorización recibido del callback

        Returns:
            Diccionario con tokens (access_token, refresh_token, expires_in, etc.)

        Raises:
            Exception: Si el intercambio falla
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        }

        response = requests.post(self.token_url, data=data)
        if response.status_code != 200:
            raise Exception(f"Error en intercambio de código: {response.text}")

        return response.json()

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresca el token de acceso usando el refresh token.

        Args:
            refresh_token: Token de refresco

        Returns:
            Diccionario con nuevos tokens

        Raises:
            Exception: Si el refresco falla
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        response = requests.post(self.token_url, data=data)
        if response.status_code != 200:
            raise Exception(f"Error en refresco de token: {response.text}")

        return response.json()

    def validate_token(self, access_token: str) -> bool:
        """
        Valida si el token de acceso es válido.

        Args:
            access_token: Token de acceso a validar

        Returns:
            True si el token es válido, False en caso contrario
        """
        if not self.validation_url:
            # Para proveedores sin endpoint de validación específico,
            # intentar una llamada de prueba
            return self._test_token_validity(access_token)

        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.validation_url, headers=headers)
            return response.status_code == 200
        except:
            return False

    @abstractmethod
    def _test_token_validity(self, access_token: str) -> bool:
        """
        Método abstracto para probar la validez del token de manera específica del proveedor.
        """
        pass


class GoogleDriveOAuth(OAuthProvider):
    """
    Implementación OAuth para Google Drive.
    """

    @property
    def auth_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/auth"

    @property
    def token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"

    @property
    def default_scope(self) -> str:
        return "https://www.googleapis.com/auth/drive"

    @property
    def validation_url(self) -> Optional[str]:
        return "https://www.googleapis.com/oauth2/v1/tokeninfo"

    def _test_token_validity(self, access_token: str) -> bool:
        # Para Google, podemos usar el endpoint de tokeninfo
        try:
            response = requests.get(f"{self.validation_url}?access_token={access_token}")
            return response.status_code == 200
        except:
            return False


class DropboxOAuth(OAuthProvider):
    """
    Implementación OAuth para Dropbox.
    """

    @property
    def auth_url(self) -> str:
        return "https://www.dropbox.com/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return "https://api.dropboxapi.com/oauth2/token"

    @property
    def default_scope(self) -> str:
        return "files.content.read"

    @property
    def validation_url(self) -> Optional[str]:
        return None  # Dropbox no tiene endpoint directo de validación

    def _test_token_validity(self, access_token: str) -> bool:
        # Para Dropbox, hacer una llamada de prueba a get_current_account
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.post(
                'https://api.dropboxapi.com/2/users/get_current_account',
                headers=headers
            )
            return response.status_code == 200
        except:
            return False


class SlackOAuth(OAuthProvider):
    """
    Implementación OAuth para Slack.
    """

    @property
    def auth_url(self) -> str:
        return "https://slack.com/oauth/v2/authorize"

    @property
    def token_url(self) -> str:
        return "https://slack.com/api/oauth.v2.access"

    @property
    def default_scope(self) -> str:
        return "channels:read,chat:write,files:read"

    @property
    def validation_url(self) -> Optional[str]:
        return "https://slack.com/api/auth.test"

    def _test_token_validity(self, access_token: str) -> bool:
        # Para Slack, usar auth.test
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.post(self.validation_url, headers=headers)
            return response.status_code == 200 and response.json().get('ok', False)
        except:
            return False


class DiscordOAuth(OAuthProvider):
    """
    Implementación OAuth para Discord.
    """

    @property
    def auth_url(self) -> str:
        return "https://discord.com/api/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return "https://discord.com/api/oauth2/token"

    @property
    def default_scope(self) -> str:
        return "bot"

    @property
    def validation_url(self) -> Optional[str]:
        return "https://discord.com/api/users/@me"

    def _test_token_validity(self, access_token: str) -> bool:
        # Para Discord, hacer una llamada a /users/@me
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.validation_url, headers=headers)
            return response.status_code == 200
        except:
            return False


# Función de fábrica para crear instancias de proveedores OAuth
def create_oauth_provider(provider_name: str, client_id: str, client_secret: str, redirect_uri: str) -> OAuthProvider:
    """
    Crea una instancia del proveedor OAuth especificado.

    Args:
        provider_name: Nombre del proveedor ('google_drive', 'dropbox', 'slack', 'discord')
        client_id: ID del cliente OAuth
        client_secret: Secreto del cliente OAuth
        redirect_uri: URI de redirección

    Returns:
        Instancia del proveedor OAuth

    Raises:
        ValueError: Si el proveedor no es soportado
    """
    providers = {
        'google_drive': GoogleDriveOAuth,
        'dropbox': DropboxOAuth,
        'slack': SlackOAuth,
        'discord': DiscordOAuth,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Proveedor OAuth no soportado: {provider_name}")

    return provider_class(client_id, client_secret, redirect_uri)