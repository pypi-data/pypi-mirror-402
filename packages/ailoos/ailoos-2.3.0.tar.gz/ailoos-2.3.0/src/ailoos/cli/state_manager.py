import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio


class AILOOSStateManager:
    """Gestor de estado persistente para el CLI de AILOOS."""

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.data_dir = Path.home() / '.ailoos-cli'
        self.data_file = self.data_dir / f'{user_id}_state.json'
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Carga el estado desde archivo."""
        try:
            self.data_dir.mkdir(exist_ok=True)

            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_state()

        except Exception as e:
            print(f"Error loading state: {e}")
            return self._get_default_state()

    def _get_default_state(self) -> Dict[str, Any]:
        """Estado por defecto."""
        return {
            'node': {
                'id': os.getenv('AILOOS_NODE_ID', 'unregistered'),
                'status': 'Pending',
                'role': 'FORGE',
                'peers': 0,
                'reputation': 0,
                'level': 1,
                'joined': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            },
            'stats': {
                'total_earned': 0.0,
                'datasets_processed': 0,
                'training_sessions': 0,
                'validation_tasks': 0,
                'uptime_hours': 0
            },
            'missions': {
                'completed': 0,
                'active': 0,
                'available': 0
            },
            'datasets': [],
            'models': [],
            'governance': {
                'votes_cast': 0,
                'proposals_supported': 0,
                'voting_power': 0.0
            },
            'settings': {
                'auto_update': True,
                'notifications': True,
                'theme': 'dark',
                'language': 'en'
            },
            'last_updated': datetime.now().isoformat(),
            'version': '2.0.0'
        }

    def save_state(self):
        """Guarda el estado en archivo."""
        try:
            self.state['last_updated'] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving state: {e}")

    def update_node_stats(self, hardware_info: Dict[str, Any], system_info: Dict[str, Any]):
        """Actualiza estadísticas del nodo con información real."""
        try:
            # Actualizar hardware
            if 'cpu' in hardware_info:
                self.state['node']['hardware'] = hardware_info

            # Actualizar peers y uptime
            if 'peers' in system_info:
                self.state['node']['peers'] = system_info['peers']

            if 'uptime' in system_info:
                # Convertir uptime a horas si es necesario
                uptime_str = system_info['uptime']
                if 'h' in uptime_str:
                    hours = int(uptime_str.split('h')[0])
                    self.state['stats']['uptime_hours'] = hours

            self.state['node']['last_activity'] = datetime.now().isoformat()
            self.save_state()

        except Exception as e:
            print(f"Error updating node stats: {e}")

    def update_wallet_info(self, wallet_info: Dict[str, Any]):
        """Actualiza información de wallet."""
        try:
            if 'wallet' not in self.state:
                self.state['wallet'] = {}

            self.state['wallet'].update({
                'address': wallet_info.get('address'),
                'balance': wallet_info.get('balance', 0.0),
                'staked': wallet_info.get('staked', 0.0),
                'rewards': wallet_info.get('rewards', 0.0),
                'last_updated': datetime.now().isoformat()
            })

            self.save_state()

        except Exception as e:
            print(f"Error updating wallet info: {e}")

    def update_staking_info(self, staking_info: Dict[str, Any]):
        """Actualiza información de staking."""
        try:
            if 'staking' not in self.state:
                self.state['staking'] = {}

            self.state['staking'].update({
                'vault': staking_info.get('total_staked', 0.0),
                'apy': staking_info.get('apy', 15.5),
                'rewards': staking_info.get('rewards_earned', 0.0),
                'last_updated': datetime.now().isoformat()
            })

            self.save_state()

        except Exception as e:
            print(f"Error updating staking info: {e}")

    def add_transaction(self, tx_data: Dict[str, Any]):
        """Añade una transacción al historial."""
        try:
            if 'transactions' not in self.state:
                self.state['transactions'] = []

            transaction = {
                'id': tx_data.get('id', os.urandom(8).hex()),
                'type': tx_data.get('type', 'transfer'),
                'amount': tx_data.get('amount', 0.0),
                'description': tx_data.get('description', ''),
                'timestamp': datetime.now().isoformat(),
                'status': tx_data.get('status', 'confirmed')
            }

            self.state['transactions'].insert(0, transaction)  # Más reciente primero

            # Mantener solo últimas 50 transacciones
            if len(self.state['transactions']) > 50:
                self.state['transactions'] = self.state['transactions'][:50]

            self.save_state()

        except Exception as e:
            print(f"Error adding transaction: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Obtiene el estado completo."""
        return self.state.copy()

    def get_node_info(self) -> Dict[str, Any]:
        """Obtiene información del nodo."""
        return self.state.get('node', {})

    def get_wallet_info(self) -> Dict[str, Any]:
        """Obtiene información de wallet."""
        return self.state.get('wallet', {})

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas."""
        return self.state.get('stats', {})

    def get_recent_transactions(self, limit: int = 10) -> list:
        """Obtiene transacciones recientes."""
        transactions = self.state.get('transactions', [])
        return transactions[:limit]

    def reset_state(self):
        """Reinicia el estado a valores por defecto."""
        self.state = self._get_default_state()
        self.save_state()

    def export_state(self, filepath: str):
        """Exporta el estado a un archivo."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error exporting state: {e}")

    def import_state(self, filepath: str):
        """Importa el estado desde un archivo."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_state = json.load(f)

            # Validar estructura básica
            if 'node' in imported_state and 'stats' in imported_state:
                self.state = imported_state
                self.save_state()
                print("State imported successfully")
            else:
                print("Invalid state file format")

        except Exception as e:
            print(f"Error importing state: {e}")
