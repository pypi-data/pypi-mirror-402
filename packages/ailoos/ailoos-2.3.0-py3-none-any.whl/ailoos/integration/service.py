"""
Integration Service for AILOOS.
Handles business logic for integrations with external services.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import secrets
import base64

from ..settings.service import SettingsService
from .oauth import create_oauth_provider, OAuthProvider

logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Service class for managing integrations with external services.
    """

    def __init__(self):
        self.settings_service = SettingsService()

    def initiate_oauth_flow(self, user_id: int, provider: str, scope: Optional[str] = None,
                           base_url: str = "http://localhost:8000") -> Dict[str, str]:
        """
        Initiate OAuth flow for a provider.

        Args:
            user_id: User ID
            provider: OAuth provider name
            scope: Optional scope override
            base_url: Base URL for callback

        Returns:
            Dict with auth_url and state

        Raises:
            ValueError: If provider is not supported
        """
        # Get OAuth credentials (in production, from secure config)
        client_id, client_secret = self._get_oauth_credentials(provider)

        # Create redirect URI
        redirect_uri = f"{base_url}/api/integrations/oauth/callback"

        # Create OAuth provider
        oauth_provider = create_oauth_provider(provider, client_id, client_secret, redirect_uri)

        # Generate state token
        state = self._generate_state_token(user_id, provider)

        # Get authorization URL
        auth_url = oauth_provider.get_authorization_url(scope=scope, state=state)

        return {
            'auth_url': auth_url,
            'state': state
        }

    def complete_oauth_flow(self, user_id: int, provider: str, code: str, state: str,
                           base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """
        Complete OAuth flow after user authorization.

        Args:
            user_id: User ID
            provider: OAuth provider name
            code: Authorization code
            state: State token
            base_url: Base URL for callback

        Returns:
            Dict with connection result

        Raises:
            ValueError: If state is invalid or flow fails
        """
        # Validate state token
        if not self._validate_state_token(state, user_id, provider):
            raise ValueError("Invalid state token")

        # Get OAuth credentials
        client_id, client_secret = self._get_oauth_credentials(provider)

        # Create redirect URI
        redirect_uri = f"{base_url}/api/integrations/oauth/callback"

        # Create OAuth provider
        oauth_provider = create_oauth_provider(provider, client_id, client_secret, redirect_uri)

        # Exchange code for tokens
        tokens = oauth_provider.exchange_code_for_token(code)

        # Store tokens securely (TODO: Implement secure storage)
        self._store_tokens(user_id, provider, tokens)

        # Update settings to mark as connected
        self._update_integration_status(user_id, provider, True)

        return {
            'success': True,
            'provider': provider,
            'connected': True,
            'tokens_received': list(tokens.keys())
        }

    def disconnect_integration(self, user_id: int, provider: str) -> bool:
        """
        Disconnect an integration.

        Args:
            user_id: User ID
            provider: OAuth provider name

        Returns:
            True if disconnected successfully
        """
        # TODO: Revoke tokens with provider if possible

        # Remove stored tokens
        self._remove_tokens(user_id, provider)

        # Update settings to mark as disconnected
        self._update_integration_status(user_id, provider, False)

        logger.info(f"Integration disconnected: user {user_id}, provider {provider}")
        return True

    def get_integration_status(self, user_id: int, provider: str) -> Dict[str, Any]:
        """
        Get integration connection status.

        Args:
            user_id: User ID
            provider: OAuth provider name

        Returns:
            Dict with status information
        """
        # Get settings
        user_settings = self.settings_service.get_user_settings(user_id)
        apps_connectors = user_settings.apps_connectors

        connected = getattr(apps_connectors, provider, False)

        # TODO: Check token validity and get metadata
        last_connected = None
        token_valid = False

        if connected:
            # Try to validate token
            try:
                token_valid = self._validate_stored_token(user_id, provider)
            except Exception as e:
                logger.warning(f"Token validation failed for user {user_id}, provider {provider}: {e}")
                token_valid = False

            # If token is invalid, mark as disconnected
            if not token_valid:
                self._update_integration_status(user_id, provider, False)
                connected = False

        return {
            'provider': provider,
            'connected': connected,
            'token_valid': token_valid,
            'last_connected': last_connected
        }

    def configure_webhook(self, user_id: int, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Configure webhook for user.

        Args:
            user_id: User ID
            url: Webhook URL
            events: List of events to trigger webhook

        Returns:
            Dict with configuration result
        """
        # Update settings
        update_data = {
            'webhook_url': url,
            # TODO: Store events in a structured way
        }

        self.settings_service.update_category_settings(
            user_id=user_id,
            category='apps_connectors',
            settings=update_data,
            validate=True
        )

        logger.info(f"Webhook configured for user {user_id}: {url}")

        return {
            'url': url,
            'events': events,
            'configured': True
        }

    def remove_webhook(self, user_id: int) -> Dict[str, Any]:
        """
        Remove webhook configuration for user.

        Args:
            user_id: User ID

        Returns:
            Dict with removal result
        """
        # Clear webhook settings
        update_data = {
            'webhook_url': '',
        }

        self.settings_service.update_category_settings(
            user_id=user_id,
            category='apps_connectors',
            settings=update_data,
            validate=True
        )

        logger.info(f"Webhook removed for user {user_id}")

        return {
            'url': '',
            'events': [],
            'configured': False
        }

    def _get_oauth_credentials(self, provider: str) -> Tuple[str, str]:
        """
        Get OAuth credentials for provider.
        In production, this should load from secure configuration.
        """
        # TODO: Implement secure credential management
        credentials = {
            'google_drive': ('your_google_client_id', 'your_google_client_secret'),
            'dropbox': ('your_dropbox_client_id', 'your_dropbox_client_secret'),
            'slack': ('your_slack_client_id', 'your_slack_client_secret'),
            'discord': ('your_discord_client_id', 'your_discord_client_secret'),
        }

        if provider not in credentials:
            raise ValueError(f"Unsupported provider: {provider}")

        return credentials[provider]

    def _generate_state_token(self, user_id: int, provider: str) -> str:
        """Generate state token for CSRF protection."""
        state_data = f"{user_id}:{provider}:{secrets.token_urlsafe(16)}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()

    def _validate_state_token(self, state: str, user_id: int, provider: str) -> bool:
        """Validate state token."""
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            parts = decoded.split(':')
            return len(parts) == 3 and int(parts[0]) == user_id and parts[1] == provider
        except:
            return False

    def _store_tokens(self, user_id: int, provider: str, tokens: Dict[str, Any]):
        """Store OAuth tokens securely."""
        # TODO: Implement secure token storage (encrypted database)
        # For now, this is a placeholder
        logger.info(f"Storing tokens for user {user_id}, provider {provider}")
        pass

    def _remove_tokens(self, user_id: int, provider: str):
        """Remove stored OAuth tokens."""
        # TODO: Implement token removal from secure storage
        logger.info(f"Removing tokens for user {user_id}, provider {provider}")
        pass

    def _validate_stored_token(self, user_id: int, provider: str) -> bool:
        """Validate stored OAuth token."""
        # TODO: Implement token validation with provider
        # For now, return False to indicate token needs refresh
        return False

    def _update_integration_status(self, user_id: int, provider: str, connected: bool):
        """Update integration connection status in settings."""
        update_data = {provider: connected}
        self.settings_service.update_category_settings(
            user_id=user_id,
            category='apps_connectors',
            settings=update_data,
            validate=True
        )