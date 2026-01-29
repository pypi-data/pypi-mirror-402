import os
from typing import Dict, Any, List
from datetime import datetime

from ..blockchain.bridge_client import get_bridge_client, BridgeClientError


class WalletMonitor:
    """Monitor de wallet real para el CLI de AILOOS."""

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.bridge_client = get_bridge_client()
        self.wallet_address = os.getenv('WALLET_ADDRESS', '')
        self.node_id = os.getenv('AILOOS_NODE_ID', 'default_node')

    async def get_wallet_balance(self) -> Dict[str, Any]:
        """Obtiene balance real de la wallet."""
        try:
            if not self.wallet_address:
                return {
                    'address': '',
                    'balance': 0.0,
                    'available': 0.0,
                    'staked': 0.0,
                    'rewards': 0.0,
                    'last_updated': datetime.now().isoformat(),
                    'note': 'WALLET_ADDRESS no configurada'
                }

            result = await self.bridge_client.get_wallet_balance(self.wallet_address)
            balance = float(result.get('balance', 0.0))

            return {
                'address': self.wallet_address,
                'balance': balance,
                'available': balance,
                'staked': float(result.get('staked_amount', 0.0)),
                'rewards': float(result.get('rewards_amount', 0.0)),
                'last_updated': datetime.now().isoformat()
            }

        except BridgeClientError as e:
            print(f"Error getting wallet balance: {e}")
            return {
                'address': self.wallet_address or '',
                'balance': 0.0,
                'available': 0.0,
                'staked': 0.0,
                'rewards': 0.0,
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }

    async def get_staking_info(self) -> Dict[str, Any]:
        """Obtiene información de staking."""
        try:
            if not self.wallet_address:
                return {
                    'total_staked': 0.0,
                    'apy': 0.0,
                    'rewards_earned': 0.0,
                    'positions': [],
                    'voting_power': 0.0,
                    'note': 'WALLET_ADDRESS no configurada'
                }

            staking_info = await self.bridge_client.get_staking_info(self.wallet_address)

            return {
                'total_staked': float(staking_info.get('staked_amount', 0.0)),
                'apy': float(staking_info.get('staking_apr', 0.0)),
                'rewards_earned': float(staking_info.get('rewards_amount', 0.0)),
                'positions': staking_info.get('positions', []),
                'voting_power': float(staking_info.get('staked_amount', 0.0))
            }

        except BridgeClientError as e:
            print(f"Error getting staking info: {e}")
            return {
                'total_staked': 0.0,
                'apy': 0.0,
                'rewards_earned': 0.0,
                'positions': [],
                'voting_power': 0.0,
                'error': str(e)
            }

    async def get_transaction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene historial de transacciones."""
        try:
            if not self.wallet_address:
                return []

            history = await self.bridge_client.get_transaction_history(self.wallet_address, limit)
            transactions = history.get('transactions', history if isinstance(history, list) else [])

            formatted = []
            for tx in transactions[:limit]:
                formatted.append({
                    'date': tx.get('timestamp') or tx.get('date') or datetime.now().isoformat(),
                    'type': tx.get('type', 'unknown'),
                    'amount': float(tx.get('amount', 0.0)),
                    'description': tx.get('description', ''),
                    'status': tx.get('status', 'confirmed')
                })

            return formatted

        except BridgeClientError as e:
            print(f"Error getting transaction history: {e}")
            return []

    async def get_governance_info(self) -> Dict[str, Any]:
        """Obtiene información de gobernanza."""
        try:
            staking_info = await self.get_staking_info()
            voting_power = staking_info.get('voting_power', 0.0)

            return {
                'voting_power': voting_power,
                'active_proposals': 0,
                'proposals': [],
                'participation_rate': 0.0
            }

        except Exception as e:
            print(f"Error getting governance info: {e}")
            return {
                'voting_power': 0.0,
                'active_proposals': 0,
                'proposals': [],
                'participation_rate': 0.0,
                'error': str(e)
            }

    async def get_all_wallet_info(self) -> Dict[str, Any]:
        """Obtiene toda la información de wallet."""
        balance = await self.get_wallet_balance()
        staking = await self.get_staking_info()
        governance = await self.get_governance_info()
        transactions = await self.get_transaction_history(5)

        return {
            'balance': balance,
            'staking': staking,
            'governance': governance,
            'recent_transactions': transactions,
            'last_updated': datetime.now().isoformat()
        }
