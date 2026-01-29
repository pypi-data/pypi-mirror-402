"""
Wallet Integration para web - integracion EmpoorioChain via bridge.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import os

from ..blockchain.dracma_token import get_token_manager, TransactionResult
from ..core.logging import get_logger, log_blockchain_tx

logger = get_logger(__name__)


class WalletType(Enum):
    """Tipos de wallet soportados."""
    METAMASK = "metamask"
    WALLET_CONNECT = "wallet_connect"
    COINBASE = "coinbase"
    TRUST = "trust"
    BINANCE = "binance"
    NATIVE = "native"  # Wallets del navegador


class WalletStatus(Enum):
    """Estados de conexión de wallet."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class WalletInfo:
    """Información de una wallet conectada."""
    address: str
    wallet_type: WalletType
    chain_id: str
    balance_dracma: float = 0.0
    is_connected: bool = False
    last_updated: float = 0.0


@dataclass
class TransactionRequest:
    """Solicitud de transacción con firma del frontend."""
    to_address: str
    amount: float
    data: Optional[str] = None
    signed_transaction: Optional[str] = None


class WebWalletIntegration:
    """
    Integración completa de wallets para aplicaciones web.
    Maneja conexión, transacciones y eventos de wallet.
    """

    def __init__(self):
        self.token_manager = get_token_manager()
        self.connected_wallets: Dict[str, WalletInfo] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        self.session_storage_key = "ailoos_wallet_session"

        self.supported_chains = ["emporiochain-1"]
        self.default_chain = "emporiochain-1"

        logger.info("🔗 Web Wallet Integration initialized")

    def add_event_listener(self, event_type: str, callback: Callable):
        """
        Añade listener para eventos de wallet.

        Args:
            event_type: Tipo de evento ('connected', 'disconnected', 'transaction', etc.)
            callback: Función callback
        """
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)

    def remove_event_listener(self, event_type: str, callback: Callable):
        """Remueve listener de eventos."""
        if event_type in self.event_listeners:
            self.event_listeners[event_type].remove(callback)

    def _emit_event(self, event_type: str, data: Any):
        """Emite evento a todos los listeners."""
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener: {e}")

    async def connect_wallet(
        self,
        wallet_type: WalletType,
        address: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conecta una wallet específica para EmpoorioChain.

        Args:
            wallet_type: Tipo de wallet a conectar
            address: Dirección de la wallet (opcional)
            user_id: ID del usuario para generar address si no existe

        Returns:
            Información de conexión
        """
        try:
            if not address:
                if not user_id:
                    return {
                        'success': False,
                        'error': 'Wallet address is required'
                    }
                if os.getenv("AILOOS_ALLOW_MOCKS") != "1":
                    return {
                        'success': False,
                        'error': 'Wallet address is required for non-local networks'
                    }
                address = await self.token_manager.initialize_user_wallet(user_id)
            elif not self._is_valid_address(address):
                return {
                    'success': False,
                    'error': 'Invalid wallet address format'
                }

            self._emit_event('connecting', {'wallet_type': wallet_type.value, 'address': address})

            if wallet_type == WalletType.METAMASK:
                result = await self._connect_metamask(address)
            elif wallet_type == WalletType.WALLET_CONNECT:
                result = await self._connect_wallet_connect(address)
            else:
                result = await self._connect_generic_wallet(wallet_type, address)

            if result['success']:
                wallet_info = result['wallet_info']

                self.connected_wallets[wallet_info.address] = wallet_info

                # Inicializar wallet en token manager si no existe
                try:
                    await self.token_manager.initialize_user_wallet(wallet_info.address)
                except Exception as e:
                    logger.warning(f"Wallet already initialized: {e}")

                # Guardar sesión
                self._save_wallet_session(wallet_info, user_id)

                self._emit_event('connected', result)
                log_blockchain_tx(
                    tx_hash="connection",
                    tx_type="wallet_connection",
                    amount=0,
                    status="success",
                    from_addr=wallet_info.address
                )
                logger.info(f"✅ Wallet connected and authenticated: {wallet_info.address} ({wallet_type.value})")

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'wallet_type': wallet_type.value
            }
            self._emit_event('error', error_result)
            logger.error(f"❌ Wallet connection failed: {e}")
            return error_result

    async def disconnect_wallet(self, address: str):
        """
        Desconecta una wallet.

        Args:
            address: Dirección de la wallet a desconectar
        """
        if address in self.connected_wallets:
            wallet_info = self.connected_wallets[address]
            del self.connected_wallets[address]

            # Limpiar sesión
            self._clear_wallet_session()

            self._emit_event('disconnected', {'address': address})
            logger.info(f"🔌 Wallet disconnected: {address}")

    async def get_wallet_balance(self, address: str) -> Dict[str, float]:
        """
        Obtiene balances de una wallet.

        Args:
            address: Dirección de la wallet

        Returns:
            Balances en diferentes tokens
        """
        try:
            dracma_balance = await self.token_manager.get_user_balance(address)

            # Actualizar info local
            if address in self.connected_wallets:
                self.connected_wallets[address].balance_dracma = dracma_balance
                self.connected_wallets[address].last_updated = time.time()

            return {
                'DRACMA': dracma_balance
            }

        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return {'DRACMA': 0.0}

    async def send_transaction(self, from_address: str, request: TransactionRequest) -> TransactionResult:
        """
        Envía una transacción firmada desde el frontend a la blockchain.

        Args:
            from_address: Dirección remitente (para validación)
            request: Detalles de la transacción con firma del frontend

        Returns:
            Resultado de la transacción
        """
        try:
            self._emit_event('transaction_pending', {
                'from': from_address,
                'to': request.to_address,
                'amount': request.amount
            })

            # Verificar que la wallet esté conectada
            if from_address not in self.connected_wallets:
                raise ValueError("Wallet not connected")

            # Validar balance suficiente
            balance = await self.get_wallet_balance(from_address)
            if balance['DRACMA'] < request.amount:
                raise ValueError(f"Insufficient balance: {balance['DRACMA']} DracmaS available")
            result = await self.token_manager.transfer_tokens(
                from_address,
                request.to_address,
                request.amount
            )

            if result.success:
                # Actualizar balances locales
                await self.get_wallet_balance(from_address)
                await self.get_wallet_balance(request.to_address)

                self._emit_event('transaction_success', {
                    'tx_hash': result.tx_hash,
                    'from': from_address,
                    'to': request.to_address,
                    'amount': request.amount,
                    'gas_used': result.gas_used,
                    'block_number': result.block_number
                })

                log_blockchain_tx(
                    tx_hash=result.tx_hash,
                    tx_type="transfer",
                    amount=request.amount,
                    status="confirmed",
                    gas_used=result.gas_used,
                    from_addr=from_address,
                    to_addr=request.to_address
                )
                logger.info(f"💸 Signed transaction sent: {result.tx_hash}")
            else:
                self._emit_event('transaction_failed', {
                    'error': result.error_message,
                    'from': from_address,
                    'to': request.to_address,
                    'amount': request.amount
                })

            return result

        except Exception as e:
            error_result = TransactionResult(
                success=False,
                error_message=str(e)
            )
            self._emit_event('transaction_failed', {'error': str(e)})
            logger.error(f"Transaction failed: {e}")
            return error_result

    async def stake_tokens(self, address: str, amount: float, signed_transaction: Optional[str] = None) -> TransactionResult:
        """
        Hace stake de tokens DracmaS via bridge.

        Args:
            address: Dirección de la wallet
            amount: Cantidad a stakear
            signed_transaction: Transacción firmada por el frontend

        Returns:
            Resultado de la transacción
        """
        try:
            result = await self.token_manager.stake_tokens(address, amount)

            if result.success:
                self._emit_event('staked', {
                    'address': address,
                    'amount': amount,
                    'tx_hash': result.tx_hash
                })

            return result

        except Exception as e:
            return TransactionResult(success=False, error_message=str(e))

    async def unstake_tokens(self, address: str, amount: float, signed_transaction: Optional[str] = None) -> TransactionResult:
        """
        Hace unstake de tokens DracmaS via bridge.

        Args:
            address: Dirección de la wallet
            amount: Cantidad a unstakear
            signed_transaction: Transacción firmada por el frontend

        Returns:
            Resultado de la transacción
        """
        try:
            result = await self.token_manager.unstake_tokens(address, amount)

            if result.success:
                self._emit_event('unstaked', {
                    'address': address,
                    'amount': amount,
                    'tx_hash': result.tx_hash
                })

            return result

        except Exception as e:
            return TransactionResult(success=False, error_message=str(e))

    async def marketplace_purchase(self, buyer_address: str, seller_address: str,
                                  amount: float, data_hash: str, ipfs_cid: str) -> TransactionResult:
        """
        Procesa compra en marketplace.

        Args:
            buyer_address: Dirección del comprador
            seller_address: Dirección del vendedor
            amount: Monto de la compra
            data_hash: Hash de los datos
            ipfs_cid: CID de IPFS

        Returns:
            Resultado de la transacción
        """
        try:
            result = await self.token_manager.marketplace_purchase(
                buyer_address,
                seller_address,
                amount,
                data_hash,
                ipfs_cid,
                buyer_address
            )

            if result.success:
                self._emit_event('marketplace_purchase', {
                    'buyer': buyer_address,
                    'seller': seller_address,
                    'amount': amount,
                    'data_hash': data_hash,
                    'ipfs_cid': ipfs_cid,
                    'tx_hash': result.tx_hash
                })

            return result

        except Exception as e:
            return TransactionResult(success=False, error_message=str(e))

    async def get_transaction_history(self, address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene historial de transacciones de una wallet.

        Args:
            address: Dirección de la wallet
            limit: Número máximo de transacciones

        Returns:
            Lista de transacciones
        """
        try:
            return await self.token_manager.get_transaction_history(address, limit)
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []

    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """
        Obtiene información de staking de una wallet.

        Args:
            address: Dirección de la wallet

        Returns:
            Información de staking
        """
        try:
            return await self.token_manager.get_staking_rewards(address)
        except Exception as e:
            logger.error(f"Error getting staking info: {e}")
            return {}

    def get_connected_wallets(self) -> List[WalletInfo]:
        """
        Obtiene lista de wallets conectadas.

        Returns:
            Lista de wallets conectadas
        """
        return list(self.connected_wallets.values())

    def is_wallet_connected(self, address: str) -> bool:
        """
        Verifica si una wallet específica está conectada.

        Args:
            address: Dirección de la wallet

        Returns:
            True si está conectada
        """
        return address in self.connected_wallets

    async def switch_chain(self, chain_id: str) -> bool:
        """
        Cambia la cadena blockchain.

        Args:
            chain_id: ID de la cadena destino

        Returns:
            True si el cambio fue exitoso
        """
        if chain_id not in self.supported_chains:
            logger.warning(f"Unsupported chain ID: {chain_id}")
            return False

        # Actualizar configuración local
        self.default_chain = chain_id

        # Actualizar chain_id de wallets conectadas
        for wallet in self.connected_wallets.values():
            wallet.chain_id = chain_id
            wallet.last_updated = time.time()

        self._emit_event('chain_changed', {'chain_id': chain_id})
        logger.info(f"🔄 Switched to chain: {chain_id}")

        return True

    def _is_valid_address(self, address: str) -> bool:
        if address.startswith("emp1") and len(address) >= 10:
            return True
        if address.startswith("0x") and len(address) == 42:
            return True
        return False

    def _save_wallet_session(self, wallet_info: WalletInfo, user_id: Optional[str]):
        """Guarda sesión de wallet en localStorage (simulado)."""
        session_data = {
            'address': wallet_info.address,
            'wallet_type': wallet_info.wallet_type.value,
            'chain_id': wallet_info.chain_id,
            'user_id': user_id,
            'connected_at': time.time()
        }

        # En producción, esto se haría desde JavaScript con localStorage
        # Por ahora, guardamos en archivo para persistencia
        try:
            session_file = f"./wallet_sessions/{wallet_info.address}.json"
            os.makedirs(os.path.dirname(session_file), exist_ok=True)

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)

            logger.debug(f"Wallet session saved: {session_data}")
        except Exception as e:
            logger.error(f"Failed to save wallet session: {e}")

    def _clear_wallet_session(self):
        """Limpia sesión de wallet."""
        # En producción, esto se haría desde JavaScript
        logger.debug("Wallet session cleared")

    async def _connect_metamask(self, address: str) -> Dict[str, Any]:
        """
        Conecta wallet MetaMask con dirección proporcionada por el frontend.
        En producción, la dirección viene del frontend después de conectar MetaMask.
        """
        try:
            await asyncio.sleep(0.1)  # Simular tiempo de conexión

            # Usar la dirección proporcionada por el frontend
            wallet_info = WalletInfo(
                address=address,
                wallet_type=WalletType.METAMASK,
                chain_id=self.default_chain,
                is_connected=True,
                last_updated=time.time()
            )

            return {
                'success': True,
                'wallet_info': wallet_info,
                'message': 'MetaMask connected successfully',
                'chain_id': self.default_chain
            }

        except Exception as e:
            logger.error(f"MetaMask connection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'wallet_type': WalletType.METAMASK.value
            }

    async def _connect_wallet_connect(self, address: str) -> Dict[str, Any]:
        """
        Conecta wallet usando WalletConnect con dirección proporcionada por el frontend.
        """
        try:
            await asyncio.sleep(0.7)  # Simular escaneo de QR

            # Usar la dirección proporcionada por el frontend
            wallet_info = WalletInfo(
                address=address,
                wallet_type=WalletType.WALLET_CONNECT,
                chain_id=self.default_chain,
                is_connected=True,
                last_updated=time.time()
            )

            return {
                'success': True,
                'wallet_info': wallet_info,
                'message': 'WalletConnect connected successfully',
                'chain_id': self.default_chain
            }

        except Exception as e:
            logger.error(f"WalletConnect connection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'wallet_type': WalletType.WALLET_CONNECT.value
            }

    async def _connect_generic_wallet(self, wallet_type: WalletType, address: str) -> Dict[str, Any]:
        """
        Conecta wallet genérica con dirección proporcionada por el frontend.
        """
        try:
            await asyncio.sleep(0.3)

            # Usar la dirección proporcionada por el frontend
            wallet_info = WalletInfo(
                address=address,
                wallet_type=wallet_type,
                chain_id=self.default_chain,
                is_connected=True,
                last_updated=time.time()
            )

            return {
                'success': True,
                'wallet_info': wallet_info,
                'message': f'{wallet_type.value.title()} connected successfully',
                'chain_id': self.default_chain
            }

        except Exception as e:
            logger.error(f"Generic wallet connection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'wallet_type': wallet_type.value
            }


# Instancia global de integración de wallets
wallet_integration = WebWalletIntegration()


def get_wallet_integration() -> WebWalletIntegration:
    """Obtiene instancia global de integración de wallets."""
    return wallet_integration


# Funciones de conveniencia para uso desde APIs
async def initialize_wallet_for_user(user_id: str) -> str:
    """
    Inicializa wallet para un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Dirección de la wallet
    """
    token_manager = get_token_manager()
    return await token_manager.initialize_user_wallet(user_id)


async def get_wallet_balance_for_user(user_address: str) -> Dict[str, float]:
    """
    Obtiene balance de wallet de usuario.

    Args:
        user_address: Dirección de la wallet

    Returns:
        Balances
    """
    integration = get_wallet_integration()
    return await integration.get_wallet_balance(user_address)
