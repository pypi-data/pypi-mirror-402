"""
Wallet DracmaS integrada para AILOOS.
Gestión de tokens, staking y transacciones.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ..blockchain.dracma_token import get_token_manager, TransactionResult


@dataclass
class WalletAddress:
    """Dirección de wallet con clave privada."""
    address: str
    private_key: str
    public_key: str
    created_at: float


class DRACMAWallet:
    """
    Wallet completa para gestión de tokens DRACMA.
    Incluye staking, transacciones y gestión de balances.
    """

    def __init__(self, wallet_file: str = "./dracma_wallet.json"):
        self.wallet_file = Path(wallet_file)
        self.current_address: Optional[str] = None
        self.addresses: Dict[str, WalletAddress] = {}
        self.token_manager = get_token_manager()

        # Cargar wallet existente o crear nueva
        self._load_wallet()

    def create_address(self, label: str = "default") -> str:
        """
        Crea una nueva dirección de wallet.

        Args:
            label: Etiqueta para identificar la dirección

        Returns:
            Nueva dirección creada
        """
        # Generar clave privada (simulada - en producción usar criptografía real)
        timestamp = str(time.time())
        private_key = hashlib.sha256(f"private_{label}_{timestamp}".encode()).hexdigest()
        public_key = hashlib.sha256(f"public_{private_key}".encode()).hexdigest()
        address = f"0x{hashlib.sha256(public_key.encode()).hexdigest()[:40]}"

        wallet_address = WalletAddress(
            address=address,
            private_key=private_key,
            public_key=public_key,
            created_at=time.time()
        )

        self.addresses[label] = wallet_address
        self.current_address = address
        self._save_wallet()

        return address

    async def get_balance(self, address: Optional[str] = None) -> float:
        """Obtiene balance de DRACMA."""
        addr = address or self.current_address
        if not addr:
            return 0.0
        return await self.token_manager.get_user_balance(addr)

    async def transfer(self, to_address: str, amount: float, description: str = "") -> TransactionResult:
        """
        Transfiere DracmaS a otra dirección.

        Args:
            to_address: Dirección destinataria
            amount: Cantidad a transferir
            description: Descripción de la transacción

        Returns:
            Resultado de la transacción
        """
        if not self.current_address:
            raise ValueError("No hay dirección activa")

        return await self.token_manager.transfer_tokens(
            from_address=self.current_address,
            to_address=to_address,
            amount=amount
        )

    async def stake_tokens(self, amount: float) -> TransactionResult:
        """
        Stake DracmaS tokens para obtener rewards.

        Args:
            amount: Cantidad a stakear

        Returns:
            Resultado de la transacción
        """
        if not self.current_address:
            raise ValueError("No hay dirección activa")

        return await self.token_manager.stake_tokens(self.current_address, amount)

    async def unstake_tokens(self, amount: float) -> TransactionResult:
        """
        Unstake DracmaS tokens.

        Args:
            amount: Cantidad a unstakear

        Returns:
            Resultado de la transacción
        """
        if not self.current_address:
            raise ValueError("No hay dirección activa")

        return await self.token_manager.unstake_tokens(self.current_address, amount)

    async def get_staking_info(self) -> Dict[str, Any]:
        """Obtiene información de staking."""
        if not self.current_address:
            return {}
        return await self.token_manager.get_staking_info(self.current_address)

    async def get_transaction_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene historial de transacciones."""
        if not self.current_address:
            return []
        return await self.token_manager.get_transaction_history(self.current_address, limit)

    async def purchase_data(self, seller_address: str, amount: float,
                           data_hash: str, ipfs_cid: str) -> TransactionResult:
        """
        Compra datos en el marketplace.

        Args:
            seller_address: Dirección del vendedor
            amount: Monto a pagar
            data_hash: Hash de los datos
            ipfs_cid: CID de IPFS

        Returns:
            Resultado de la transacción
        """
        if not self.current_address:
            raise ValueError("No hay dirección activa")

        return await self.token_manager.transfer_tokens(
            from_address=self.current_address,
            to_address=seller_address,
            amount=amount
        )

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo del portfolio."""
        if not self.current_address:
            return {}

        balance = await self.get_balance()
        staking_info = await self.get_staking_info()
        recent_txs = await self.get_transaction_history(5)

        # Calcular valor total
        total_value = balance + staking_info.get("staked_amount", 0)

        # Calcular rendimiento estimado
        estimated_daily = staking_info.get("estimated_daily_reward", 0)
        estimated_monthly = estimated_daily * 30

        return {
            "address": self.current_address,
            "balance_dracma": balance,
            "staked_dracma": staking_info.get("staked_amount", 0),
            "total_value_dracma": total_value,
            "staking_multiplier": staking_info.get("multiplier", 1.0),
            "estimated_daily_reward": estimated_daily,
            "estimated_monthly_reward": estimated_monthly,
            "recent_transactions": len(recent_txs),
            "portfolio_health": "good" if balance > 100 else "low_balance"
        }

    def export_wallet(self, password: str) -> str:
        """
        Exporta wallet encriptada.

        Args:
            password: Contraseña para encriptar

        Returns:
            JSON encriptado de la wallet
        """
        wallet_data = {
            "addresses": {
                label: {
                    "address": addr.address,
                    "private_key": addr.private_key,
                    "public_key": addr.public_key,
                    "created_at": addr.created_at
                }
                for label, addr in self.addresses.items()
            },
            "current_address": self.current_address,
            "exported_at": time.time()
        }

        # Encriptación simple (en producción usar AES)
        data_str = json.dumps(wallet_data, indent=2)
        key = hashlib.sha256(password.encode()).digest()
        encrypted = self._simple_encrypt(data_str, key)

        return encrypted.decode('latin-1')

    def import_wallet(self, encrypted_data: str, password: str) -> bool:
        """
        Importa wallet desde datos encriptados.

        Args:
            encrypted_data: Datos encriptados
            password: Contraseña para desencriptar

        Returns:
            True si la importación fue exitosa
        """
        try:
            key = hashlib.sha256(password.encode()).digest()
            decrypted = self._simple_decrypt(encrypted_data.encode('latin-1'), key)
            wallet_data = json.loads(decrypted)

            # Reconstruir direcciones
            self.addresses = {}
            for label, addr_data in wallet_data["addresses"].items():
                self.addresses[label] = WalletAddress(**addr_data)

            self.current_address = wallet_data["current_address"]
            self._save_wallet()
            return True

        except Exception as e:
            print(f"Error importando wallet: {e}")
            return False

    def _load_wallet(self):
        """Carga wallet desde archivo."""
        if self.wallet_file.exists():
            try:
                with open(self.wallet_file, 'r') as f:
                    data = json.load(f)

                # Reconstruir direcciones
                self.addresses = {}
                for label, addr_data in data.get("addresses", {}).items():
                    self.addresses[label] = WalletAddress(**addr_data)

                self.current_address = data.get("current_address")

            except Exception as e:
                print(f"Error cargando wallet: {e}")
                self._create_default_wallet()
        else:
            self._create_default_wallet()

    def _save_wallet(self):
        """Guarda wallet en archivo."""
        try:
            data = {
                "addresses": {
                    label: {
                        "address": addr.address,
                        "private_key": addr.private_key,
                        "public_key": addr.public_key,
                        "created_at": addr.created_at
                    }
                    for label, addr in self.addresses.items()
                },
                "current_address": self.current_address,
                "last_updated": time.time()
            }

            self.wallet_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.wallet_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error guardando wallet: {e}")

    def _create_default_wallet(self):
        """Crea wallet por defecto."""
        self.create_address("default")

    def _simple_encrypt(self, data: str, key: bytes) -> bytes:
        """Encriptación simple XOR (solo para demo)."""
        data_bytes = data.encode()
        key_len = len(key)
        encrypted = bytearray()

        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key[i % key_len])

        return bytes(encrypted)

    def _simple_decrypt(self, data: bytes, key: bytes) -> str:
        """Desencriptación simple XOR."""
        return self._simple_encrypt(data.decode('latin-1'), key).decode('latin-1')


# Funciones de conveniencia
def create_wallet(wallet_file: str = "./dracma_wallet.json") -> DRACMAWallet:
    """Crea una nueva instancia de wallet."""
    return DRACMAWallet(wallet_file)


def get_default_wallet() -> DRACMAWallet:
    """Obtiene wallet por defecto."""
    return create_wallet()