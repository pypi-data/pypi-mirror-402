"""
Integration module for AILOOS.
Handles integrations with external services like Google Drive, Dropbox, Slack, Discord, webhooks, and blockchain oracles.
"""

from .oauth import (
    OAuthProvider,
    GoogleDriveOAuth,
    DropboxOAuth,
    SlackOAuth,
    DiscordOAuth,
    create_oauth_provider
)
from .service import IntegrationService
from .oracles import (
    ChainlinkOracle,
    ChainlinkOracleError,
    BandOracle,
    BandOracleError,
    API3Oracle,
    API3OracleError
)

__all__ = [
    'OAuthProvider',
    'GoogleDriveOAuth',
    'DropboxOAuth',
    'SlackOAuth',
    'DiscordOAuth',
    'create_oauth_provider',
    'IntegrationService',
    'ChainlinkOracle',
    'ChainlinkOracleError',
    'BandOracle',
    'BandOracleError',
    'API3Oracle',
    'API3OracleError'
]