"""
Web integration para AILOOS.
Incluye integración de wallets blockchain y APIs web.
"""

from .wallet_integration import (
    WebWalletIntegration,
    get_wallet_integration,
    initialize_wallet_for_user,
    get_wallet_balance_for_user,
    WalletType,
    WalletStatus,
    WalletInfo,
    TransactionRequest
)

__all__ = [
    'WebWalletIntegration',
    'get_wallet_integration',
    'initialize_wallet_for_user',
    'get_wallet_balance_for_user',
    'WalletType',
    'WalletStatus',
    'WalletInfo',
    'TransactionRequest'
]