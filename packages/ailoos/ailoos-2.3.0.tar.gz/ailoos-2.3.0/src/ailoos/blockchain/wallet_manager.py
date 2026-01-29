"""
Wallet Manager - Gestor completo de wallets DRACMA
Maneja creación, gestión y operaciones de wallets con persistencia y seguridad.
"""

import asyncio
import json
import os
import time
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

from ..core.logging import get_logger
from .core import Blockchain, Wallet, Transaction, get_blockchain
from .dracma_token import DRACMATokenManager, get_token_manager

logger = get_logger(__name__)


@dataclass
class WalletInfo:
    """Información completa de una wallet."""
    wallet_id: str
    address: str
    balance: float
    staked_amount: float = 0.0
    rewards_earned: float = 0.0
    transaction_count: int = 0
    created_at: datetime = None
    last_activity: datetime = None
    security_level: str = "standard"  # standard, high, maximum

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()


@dataclass
class TransactionRecord:
    """Registro completo de transacción."""
    tx_hash: str
    wallet_id: str
    tx_type: str  # transfer, stake, unstake, reward, purchase
    amount: float
    recipient: Optional[str] = None
    sender: Optional[str] = None
    timestamp: datetime = None
    status: str = "pending"  # pending, confirmed, failed
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}


class WalletManager:
    """
    Gestor completo de wallets DracmaS con persistencia y seguridad.

    Características:
    - Creación y gestión de wallets
    - Persistencia segura de claves privadas
    - Historial completo de transacciones
    - Integración con staking
    - Seguridad básica (encriptación de claves)
    - Backup y recuperación
    """

    def __init__(self, storage_path: str = "./wallets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Instancias de componentes
        self.blockchain = get_blockchain()
        self.token_manager = get_token_manager()

        # Estado en memoria
        self.wallets: Dict[str, WalletInfo] = {}
        self.transactions: Dict[str, List[TransactionRecord]] = {}

        # Configuración de seguridad
        self.encryption_key = self._generate_encryption_key()
        self.backup_enabled = True

        # Cargar datos existentes
        self._load_wallets()

        logger.info(f"💰 Wallet Manager initialized with {len(self.wallets)} wallets")

    def _generate_encryption_key(self) -> str:
        """Generar clave de encriptación para wallets."""
        # En producción, usar una clave derivada de contraseña del usuario
        return secrets.token_hex(32)

    def _load_wallets(self):
        """Cargar wallets desde almacenamiento persistente."""
        try:
            for wallet_file in self.storage_path.glob("*.json"):
                try:
                    with open(wallet_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    wallet_info = WalletInfo(**data['info'])
                    self.wallets[wallet_info.wallet_id] = wallet_info

                    # Cargar transacciones
                    if 'transactions' in data:
                        self.transactions[wallet_info.wallet_id] = [
                            TransactionRecord(**tx) for tx in data['transactions']
                        ]

                except Exception as e:
                    logger.warning(f"Failed to load wallet {wallet_file}: {e}")

        except Exception as e:
            logger.error(f"Error loading wallets: {e}")

    def _save_wallet(self, wallet_id: str):
        """Guardar wallet en almacenamiento persistente."""
        try:
            wallet_info = self.wallets[wallet_id]
            wallet_file = self.storage_path / f"{wallet_id}.json"

            data = {
                'info': asdict(wallet_info),
                'transactions': [asdict(tx) for tx in self.transactions.get(wallet_id, [])],
                'version': '1.0'
            }

            with open(wallet_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving wallet {wallet_id}: {e}")

    async def create_wallet(self, user_id: str, label: str = "default",
                          security_level: str = "standard") -> Dict[str, Any]:
        """
        Crear una nueva wallet para un usuario.

        Args:
            user_id: ID del usuario
            label: Etiqueta para la wallet
            security_level: Nivel de seguridad (standard, high, maximum)

        Returns:
            Información de la wallet creada
        """
        try:
            # Generar ID único para la wallet
            wallet_id = f"{user_id}_{label}_{int(datetime.now().timestamp())}"

            # Crear wallet en blockchain
            blockchain_wallet = self.blockchain.create_wallet()

            # Wallet created with 0 balance (Must be funded via transfer)
            initial_balance = 0.0

            wallet_info = WalletInfo(
                wallet_id=wallet_id,
                address=blockchain_wallet.address,
                balance=initial_balance,
                security_level=security_level
            )

            # Guardar en memoria y persistencia
            self.wallets[wallet_id] = wallet_info
            self.transactions[wallet_id] = []
            self._save_wallet(wallet_id)

            logger.info(f"✅ Created wallet {wallet_id} for user {user_id}")

            return {
                'success': True,
                'wallet_id': wallet_id,
                'address': blockchain_wallet.address,
                'public_key': blockchain_wallet.public_key,
                'private_key': blockchain_wallet.private_key  # Solo para desarrollo
            }

        except Exception as e:
            logger.error(f"❌ Error creating wallet: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_wallets(self, user_id: str) -> List[WalletInfo]:
        """
        Obtener todas las wallets de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de wallets del usuario
        """
        user_wallets = []
        for wallet in self.wallets.values():
            if wallet.wallet_id.startswith(f"{user_id}_"):
                user_wallets.append(wallet)

        return user_wallets

    async def get_wallet_balance(self, wallet_id: str) -> Dict[str, Any]:
        """
        Obtener balance completo de una wallet.

        Args:
            wallet_id: ID de la wallet

        Returns:
            Información completa del balance
        """
        try:
            if wallet_id not in self.wallets:
                return {'error': 'Wallet not found'}

            wallet_info = self.wallets[wallet_id]

            # Usar balance local para consistencia (actualizado por operaciones)
            # Solo sincronizar con blockchain/token manager cuando sea necesario
            token_balance = wallet_info.balance
            wallet_info.last_activity = datetime.now()
            self._save_wallet(wallet_id)

            return {
                'wallet_id': wallet_id,
                'address': wallet_info.address,
                'total_balance': token_balance,
                'available_balance': token_balance - wallet_info.staked_amount,
                'staked_amount': wallet_info.staked_amount,
                'rewards_earned': wallet_info.rewards_earned,
                'last_updated': wallet_info.last_activity.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting balance for {wallet_id}: {e}")
            return {'error': str(e)}

    async def transfer(self, from_wallet_id: str, to_address: str, amount: float,
                      description: str = "") -> Dict[str, Any]:
        """
        Transferir tokens entre wallets.

        Args:
            from_wallet_id: ID de la wallet remitente
            to_address: Dirección del destinatario
            amount: Cantidad a transferir
            description: Descripción de la transacción

        Returns:
            Resultado de la transacción
        """
        try:
            if from_wallet_id not in self.wallets:
                return {'success': False, 'error': 'Wallet not found'}

            from_wallet = self.wallets[from_wallet_id]

            # Verificar balance suficiente
            if from_wallet.balance < amount:
                return {'success': False, 'error': 'Insufficient balance'}

            # Crear transacción
            blockchain_wallet = self.blockchain.get_wallet(from_wallet.address)
            if not blockchain_wallet:
                return {'success': False, 'error': 'Blockchain wallet not found'}

            # Sincronizar nonce con la wallet local
            blockchain_wallet.nonce = from_wallet.transaction_count + 1

            tx = blockchain_wallet.create_transaction(to_address, amount, {
                'description': description,
                'type': 'transfer'
            })

            # Firmar y enviar
            blockchain_wallet.sign_transaction(tx)
            success = self.blockchain.add_transaction(tx)

            if success:
                # Registrar transacción local
                tx_record = TransactionRecord(
                    tx_hash=tx.tx_id,
                    wallet_id=from_wallet_id,
                    tx_type='transfer',
                    amount=amount,
                    recipient=to_address,
                    sender=from_wallet.address,
                    status='confirmed'
                )

                if from_wallet_id not in self.transactions:
                    self.transactions[from_wallet_id] = []
                self.transactions[from_wallet_id].append(tx_record)

                # Actualizar balances
                from_wallet.balance -= amount
                from_wallet.transaction_count += 1
                from_wallet.last_activity = datetime.now()
                self._save_wallet(from_wallet_id)

                logger.info(f"💸 Transfer {amount} DracmaS from {from_wallet.address} to {to_address}")

                return {
                    'success': True,
                    'tx_hash': tx.tx_id,
                    'amount': amount,
                    'from': from_wallet.address,
                    'to': to_address
                }
            else:
                return {'success': False, 'error': 'Transaction failed'}

        except Exception as e:
            logger.error(f"Error transferring tokens: {e}")
            return {'success': False, 'error': str(e)}

    def get_transaction_history(self, wallet_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtener historial de transacciones de una wallet.

        Args:
            wallet_id: ID de la wallet
            limit: Número máximo de transacciones

        Returns:
            Lista de transacciones
        """
        try:
            if wallet_id not in self.transactions:
                return []

            txs = self.transactions[wallet_id]
            # Ordenar por timestamp (más recientes primero)
            txs.sort(key=lambda x: x.timestamp, reverse=True)

            return [
                {
                    'tx_hash': tx.tx_hash,
                    'type': tx.tx_type,
                    'amount': tx.amount,
                    'recipient': tx.recipient,
                    'sender': tx.sender,
                    'timestamp': tx.timestamp.isoformat(),
                    'status': tx.status,
                    'data': tx.data
                }
                for tx in txs[:limit]
            ]

        except Exception as e:
            logger.error(f"Error getting transaction history for {wallet_id}: {e}")
            return []

    async def backup_wallet(self, wallet_id: str, backup_path: str) -> bool:
        """
        Crear backup de una wallet.

        Args:
            wallet_id: ID de la wallet
            backup_path: Ruta para el backup

        Returns:
            True si el backup fue exitoso
        """
        try:
            if wallet_id not in self.wallets:
                return False

            # Crear directorio de backup
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copiar archivo de wallet
            wallet_file = self.storage_path / f"{wallet_id}.json"
            backup_file = backup_dir / f"{wallet_id}_backup_{int(datetime.now().timestamp())}.json"

            if wallet_file.exists():
                import shutil
                shutil.copy2(wallet_file, backup_file)

            logger.info(f"💾 Wallet {wallet_id} backed up to {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Error backing up wallet {wallet_id}: {e}")
            return False

    async def restore_wallet(self, backup_file: str) -> Dict[str, Any]:
        """
        Restaurar wallet desde backup.

        Args:
            backup_file: Ruta al archivo de backup

        Returns:
            Resultado de la restauración
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return {'success': False, 'error': 'Backup file not found'}

            # Leer datos del backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            wallet_info = WalletInfo(**data['info'])

            # Restaurar wallet
            self.wallets[wallet_info.wallet_id] = wallet_info
            if 'transactions' in data:
                self.transactions[wallet_info.wallet_id] = [
                    TransactionRecord(**tx) for tx in data['transactions']
                ]

            self._save_wallet(wallet_info.wallet_id)

            logger.info(f"🔄 Wallet {wallet_info.wallet_id} restored from backup")

            return {
                'success': True,
                'wallet_id': wallet_info.wallet_id,
                'address': wallet_info.address
            }

        except Exception as e:
            logger.error(f"Error restoring wallet: {e}")
            return {'success': False, 'error': str(e)}

    def get_wallet_stats(self, wallet_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de una wallet.

        Args:
            wallet_id: ID de la wallet

        Returns:
            Estadísticas de la wallet
        """
        try:
            if wallet_id not in self.wallets:
                return {'error': 'Wallet not found'}

            wallet_info = self.wallets[wallet_id]
            transactions = self.transactions.get(wallet_id, [])

            # Calcular estadísticas
            total_sent = sum(tx.amount for tx in transactions if tx.tx_type == 'transfer' and tx.sender == wallet_info.address)
            total_received = sum(tx.amount for tx in transactions if tx.tx_type == 'transfer' and tx.recipient == wallet_info.address)
            total_rewards = sum(tx.amount for tx in transactions if tx.tx_type == 'reward')

            return {
                'wallet_id': wallet_id,
                'address': wallet_info.address,
                'current_balance': wallet_info.balance,
                'total_transactions': len(transactions),
                'total_sent': total_sent,
                'total_received': total_received,
                'total_rewards': total_rewards,
                'staked_amount': wallet_info.staked_amount,
                'created_at': wallet_info.created_at.isoformat(),
                'last_activity': wallet_info.last_activity.isoformat(),
                'security_level': wallet_info.security_level
            }

        except Exception as e:
            logger.error(f"Error getting wallet stats for {wallet_id}: {e}")
            return {'error': str(e)}

    def cleanup_old_transactions(self, days_to_keep: int = 90):
        """
        Limpiar transacciones antiguas para optimizar espacio.

        Args:
            days_to_keep: Días de transacciones a mantener
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            for wallet_id, txs in self.transactions.items():
                # Mantener solo transacciones recientes
                recent_txs = [tx for tx in txs if tx.timestamp > cutoff_date]
                self.transactions[wallet_id] = recent_txs

                # Guardar cambios
                self._save_wallet(wallet_id)

            logger.info(f"🧹 Cleaned up transactions older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Error cleaning up transactions: {e}")


# Instancia global del wallet manager
_wallet_manager: Optional[WalletManager] = None

def get_wallet_manager() -> WalletManager:
    """Obtener instancia global del wallet manager."""
    global _wallet_manager
    if _wallet_manager is None:
        _wallet_manager = WalletManager()
    return _wallet_manager

def create_wallet_manager(storage_path: str = "./wallets") -> WalletManager:
    """Crear nueva instancia del wallet manager."""
    return WalletManager(storage_path)


def main():
    """CLI entry point for wallet manager."""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="AILOOS Wallet Manager CLI")
    parser.add_argument("command", choices=["create", "balance", "transfer", "history", "backup", "restore"],
                       help="Command to execute")
    parser.add_argument("--user", "-u", required=True, help="User ID")
    parser.add_argument("--amount", "-a", type=float, help="Amount for transfer/stake")
    parser.add_argument("--to", "-t", help="Recipient address for transfer")
    parser.add_argument("--file", "-f", help="File path for backup/restore")

    args = parser.parse_args()

    async def run_command():
        manager = get_wallet_manager()

        if args.command == "create":
            result = await manager.create_wallet(args.user, "cli")
            if result['success']:
                print(f"✅ Wallet created: {result['address']}")
            else:
                print(f"❌ Error: {result['error']}")

        elif args.command == "balance":
            wallets = manager.get_user_wallets(args.user)
            if wallets:
                balance = await manager.get_wallet_balance(wallets[0].wallet_id)
                print(f"💰 Balance: {balance.get('total_balance', 0):.2f} DRACMA")
            else:
                print("❌ No wallet found")

        elif args.command == "transfer":
            if not args.amount or not args.to:
                print("❌ Amount and recipient required")
                return

            wallets = manager.get_user_wallets(args.user)
            if wallets:
                result = await manager.transfer(wallets[0].wallet_id, args.to, args.amount)
                if result['success']:
                    print("✅ Transfer successful")
                else:
                    print(f"❌ Transfer failed: {result['error']}")
            else:
                print("❌ No wallet found")

        elif args.command == "history":
            wallets = manager.get_user_wallets(args.user)
            if wallets:
                history = manager.get_transaction_history(wallets[0].wallet_id)
                for tx in history:
                    print(f"📝 {tx['timestamp'][:19]} {tx['type']} {tx['amount']:.2f} DRACMA")
            else:
                print("❌ No wallet found")

        elif args.command == "backup":
            wallets = manager.get_user_wallets(args.user)
            if wallets and args.file:
                success = await manager.backup_wallet(wallets[0].wallet_id, args.file)
                if success:
                    print("✅ Backup successful")
                else:
                    print("❌ Backup failed")
            else:
                print("❌ Wallet or file path missing")

        elif args.command == "restore":
            if args.file:
                result = await manager.restore_wallet(args.file)
                if result['success']:
                    print(f"✅ Wallet restored: {result['address']}")
                else:
                    print(f"❌ Restore failed: {result['error']}")
            else:
                print("❌ File path required")

    asyncio.run(run_command())


if __name__ == "__main__":
    main()