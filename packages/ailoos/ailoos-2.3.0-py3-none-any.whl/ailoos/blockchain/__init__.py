"""
Blockchain infrastructure para AILOOS.
Incluye blockchain completa con proof-of-work real, criptografía asimétrica y gestión de tokens DRACMA.
"""

from .core import (
    Blockchain,
    Block,
    Transaction,
    Wallet,
    get_blockchain,
    create_transaction,
    send_transaction,
    generate_keypair,
    address_from_public_key
)

from .dracma_token import (
    DRACMATokenManager,
    get_token_manager,
    initialize_dracma_infrastructure,
    TokenConfig,
    TokenStandard,
    NetworkType,
    TransactionResult
)

__all__ = [
    # Blockchain core
    'Blockchain',
    'Block',
    'Transaction',
    'Wallet',
    'get_blockchain',
    'create_transaction',
    'send_transaction',
    'generate_keypair',
    'address_from_public_key',

    # Token management
    'DRACMATokenManager',
    'get_token_manager',
    'initialize_dracma_infrastructure',
    'TokenConfig',
    'TokenStandard',
    'NetworkType',
    'TransactionResult'
]