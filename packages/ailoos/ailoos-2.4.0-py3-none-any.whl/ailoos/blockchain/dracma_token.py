"""
DracmaS Token Infrastructure - Integracion real via Web3 EVM + EmpoorioChain + LocalChain.
"""

import time
import os
import inspect
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from web3 import Web3
from web3.exceptions import ContractLogicError, InvalidAddress, Web3Exception
from eth_account import Account
from eth_account.signers.local import LocalAccount

from ..core.logging import get_logger
from .bridge_client import get_bridge_client, BridgeClient, BridgeClientError
from .dracmas_config import get_dracmas_config
from .local_chain import get_local_chain, LocalChain

logger = get_logger(__name__)


class TokenStandard(Enum):
    """Estándares de token soportados."""
    COSMWASM = "COSMWASM"
    ERC20 = "ERC20"


class NetworkType(Enum):
    """Tipos de red blockchain."""
    LOCAL = "local"
    EMPORIOCHAIN = "emporiochain"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


@dataclass
class TokenConfig:
    """Configuración del token DRACMA."""
    name: str = "DracmaS"
    symbol: str = "DMS"
    decimals: int = 18
    total_supply: int = 1_000_000_000  # 1B tokens
    standard: TokenStandard = TokenStandard.ERC20
    network: NetworkType = NetworkType.LOCAL  # Default to LOCAL for now

    # Configuración EVM
    rpc_url: Optional[str] = None
    chain_id: Optional[int] = None
    erc20_contract_address: Optional[str] = None
    staking_contract_address: Optional[str] = None

    # Configuración CosmWasm (para compatibilidad con EmpoorioChain si no es EVM puro)
    cosmwasm_token_contract: Optional[str] = None
    cosmwasm_ailoos_contract: Optional[str] = None
    cosmwasm_pool_address: Optional[str] = None

    # Configuración de gas y transacciones
    default_gas_limit: int = 200000
    gas_price_multiplier: float = 1.1  # Multiplicador para gas price

    def __post_init__(self):
        """Validar configuración después de inicialización."""
        self._set_network_defaults()
        self._validate_config()

    def _set_network_defaults(self):
        """Establecer configuraciones por defecto basadas en la red."""
        if self.network == NetworkType.LOCAL:
            self.rpc_url = self.rpc_url or "http://127.0.0.1:8545"
            self.chain_id = self.chain_id or 1337
            self.erc20_contract_address = self.erc20_contract_address or "0x5FbDB2315678afecb367f032d93F642f64180aa3"  # Local deployment
        elif self.network == NetworkType.EMPORIOCHAIN:
            dracmas_cfg = get_dracmas_config()
            self.standard = TokenStandard.COSMWASM
            self.rpc_url = self.rpc_url or dracmas_cfg.network.rpc_url
            self.chain_id = None
            self.erc20_contract_address = None
            self.cosmwasm_token_contract = dracmas_cfg.contracts.token_contract
            self.cosmwasm_ailoos_contract = dracmas_cfg.contracts.ailoos_contract
            self.cosmwasm_pool_address = dracmas_cfg.contracts.pool_address
        elif self.network == NetworkType.ETHEREUM:
            self.rpc_url = self.rpc_url or os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
            self.chain_id = self.chain_id or 1
            self.erc20_contract_address = self.erc20_contract_address or os.getenv("DRACMA_ETH_CONTRACT")
        elif self.network == NetworkType.POLYGON:
            self.rpc_url = self.rpc_url or os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
            self.chain_id = self.chain_id or 137
            self.erc20_contract_address = self.erc20_contract_address or os.getenv("DRACMA_POLYGON_CONTRACT")
        elif self.network == NetworkType.BSC:
            self.rpc_url = self.rpc_url or os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org")
            self.chain_id = self.chain_id or 56
            self.erc20_contract_address = self.erc20_contract_address or os.getenv("DRACMA_BSC_CONTRACT")
        elif self.network == NetworkType.ARBITRUM:
            self.rpc_url = self.rpc_url or os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
            self.chain_id = self.chain_id or 42161
            self.erc20_contract_address = self.erc20_contract_address or os.getenv("DRACMA_ARBITRUM_CONTRACT")
        elif self.network == NetworkType.OPTIMISM:
            self.rpc_url = self.rpc_url or os.getenv("OPTIMISM_RPC_URL", "https://mainnet.optimism.io")
            self.chain_id = self.chain_id or 10
            self.erc20_contract_address = self.erc20_contract_address or os.getenv("DRACMA_OPTIMISM_CONTRACT")

    def _set_cosmwasm_defaults(self):
        """Establecer configuración por defecto para CosmWasm."""
        if not self.cosmwasm_token_contract:
            # 45-char mock address
            self.cosmwasm_token_contract = "emp1dracmascontract00000000000000000000000001"
        if not self.cosmwasm_ailoos_contract:
            self.cosmwasm_ailoos_contract = "emp1ailooscontract000000000000000000000000001"
        if not self.cosmwasm_pool_address:
            self.cosmwasm_pool_address = "emp1ailoospool0000000000000000000000000000001"

    def _validate_config(self) -> bool:
        """Valida la configuración completa."""
        if self.standard == TokenStandard.ERC20:
            if not self.rpc_url:
                logger.error("RPC URL requerida para ERC20")
                return False
            if not self.chain_id:
                logger.error("Chain ID requerido para ERC20")
                return False
            if not self.erc20_contract_address and self.network != NetworkType.LOCAL:
                logger.warning("ERC20 contract address no configurada")
        elif self.standard == TokenStandard.COSMWASM:
            return self.validate_cosmwasm_addresses()
        return True

    def validate_cosmwasm_addresses(self) -> bool:
        """Valida direcciones CosmWasm si están configuradas."""
        cosmwasm_fields = [
            ('cosmwasm_token_contract', self.cosmwasm_token_contract),
            ('cosmwasm_ailoos_contract', self.cosmwasm_ailoos_contract),
            ('cosmwasm_pool_address', self.cosmwasm_pool_address)
        ]

        for field_name, address in cosmwasm_fields:
            if address:
                if not address.startswith('emp1'):
                    logger.error(f"Dirección CosmWasm inválida para {field_name}: {address}")
                    return False
                if len(address) != 45:  # Longitud típica de direcciones emp1
                    logger.warning(f"Dirección {field_name} tiene longitud inusual: {len(address)}")

        return True


@dataclass
class TransactionResult:
    """Resultado de una transacción blockchain."""
    success: bool
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    error_message: Optional[str] = None
    events: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.events is None:
            self.events = []


class ITokenProvider(Protocol):
    """Interfaz para proveedores de token (simulado vs real)."""

    async def get_balance(self, address: str) -> float:
        """Obtiene balance de una dirección."""
        ...

    async def transfer(self, from_address: str, to_address: str, amount: float,
                      private_key: Optional[str] = None) -> TransactionResult:
        """Transfiere tokens entre direcciones."""
        ...

    async def approve(self, spender_address: str, amount: float,
                     private_key: Optional[str] = None) -> TransactionResult:
        """Aprueba gasto de tokens."""
        ...

    async def stake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Hace stake de tokens."""
        ...

    async def unstake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Hace unstake de tokens."""
        ...

    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """Obtiene información de staking."""
        ...

    async def get_transaction_history(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene historial de transacciones."""
        ...

    async def estimate_gas(self, from_address: str, to_address: str, amount: float) -> int:
        """Estima gas para una transacción."""
        ...


class RealTokenProvider(ITokenProvider):
    """
    Proveedor real de tokens para producción usando Web3.
    Se conecta a redes EVM (EmpoorioChain, Ethereum, Polygon, etc.).
    """

    def __init__(self, config: TokenConfig):
        self.config = config
        self.w3: Optional[Web3] = None
        self.contract: Optional[Any] = None
        self.staking_contract: Optional[Any] = None
        self.account: Optional[LocalAccount] = None

        # Para compatibilidad con EmpoorioChain no-EVM puro
        self.bridge_client: Optional[BridgeClient] = None

        self._initialize_connection()
        logger.info(f"🔗 RealTokenProvider initialized for {config.symbol} on {config.network.value}")

    def _initialize_connection(self):
        """Inicializa conexión Web3 o bridge según la configuración."""
        if self.config.standard == TokenStandard.ERC20:
            self._initialize_web3()
        elif self.config.standard == TokenStandard.COSMWASM:
            self._initialize_bridge()
        else:
            raise ValueError(f"Estándar no soportado: {self.config.standard}")

    def _initialize_web3(self):
        """Inicializa conexión Web3 para redes EVM."""
        if not self.config.rpc_url:
            raise ValueError("RPC URL requerida para conexión Web3")

        self.w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError(f"No se pudo conectar a {self.config.rpc_url}")

        # Verificar chain ID
        if self.config.chain_id and self.w3.eth.chain_id != self.config.chain_id:
            logger.warning(f"Chain ID mismatch: expected {self.config.chain_id}, got {self.w3.eth.chain_id}")

        # Cargar contrato ERC20
        if self.config.erc20_contract_address:
            self.contract = self._load_erc20_contract(self.config.erc20_contract_address)

        # Cargar contrato de staking si existe
        if self.config.staking_contract_address:
            self.staking_contract = self._load_staking_contract(self.config.staking_contract_address)

        logger.info(f"✅ Connected to {self.config.network.value} via Web3")

    def _load_erc20_contract(self, address: str) -> Any:
        """Carga contrato ERC20 desde ABI."""
        # ABI básica para ERC20
        erc20_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
        ]
        return self.w3.eth.contract(address=address, abi=erc20_abi)

    def _load_staking_contract(self, address: str) -> Any:
        """Carga contrato de staking (ABI básica)."""
        # ABI básica para staking - ajustar según contrato real
        staking_abi = [
            {"inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "stake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "unstake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "user", "type": "address"}], "name": "getStakingInfo", "outputs": [{"internalType": "uint256", "name": "staked", "type": "uint256"}, {"internalType": "uint256", "name": "rewards", "type": "uint256"}], "stateMutability": "view", "type": "function"},
        ]
        return self.w3.eth.contract(address=address, abi=staking_abi)

    def _initialize_bridge(self):
        """Inicializa conexión con el puente DracmaS para compatibilidad."""
        self.bridge_client = get_bridge_client()
        logger.info("✅ Connected to DracmaS bridge")

    def _ensure_web3_ready(self) -> Optional[str]:
        """Valida que Web3 y contratos esten listos para operar."""
        if not self.w3 or not self.w3.is_connected():
            return "Configuración inválida"
        if self.config.standard == TokenStandard.ERC20 and not self.contract:
            return "Contrato ERC20 no configurado"
        return None

    def _get_account_from_private_key(self, private_key: str) -> LocalAccount:
        """Obtiene cuenta desde private key."""
        return Account.from_key(private_key)

    def _get_raw_transaction(self, signed_tx: Any) -> Any:
        """Obtiene raw transaction compatible con diferentes versiones."""
        raw_tx = getattr(signed_tx, "rawTransaction", None)
        if raw_tx is None:
            raw_tx = getattr(signed_tx, "raw_transaction", None)
        if raw_tx is None:
            raise ValueError("Signed transaction missing raw transaction payload")
        return raw_tx

    def _format_tx_hash(self, tx_hash: Any) -> str:
        """Normaliza el hash de transaccion con prefijo 0x."""
        value = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
        return value if value.startswith("0x") else f"0x{value}"

    async def _await_bridge_result(self, result: Any) -> Any:
        """Permite resultados sync o async del bridge."""
        if inspect.isawaitable(result):
            return await result
        return result

    def _build_transaction(self, tx_params: Dict[str, Any], private_key: Optional[str] = None) -> Dict[str, Any]:
        """Construye transacción con gas y nonce apropiados."""
        # Obtener nonce
        if private_key:
            account = self._get_account_from_private_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
        else:
            nonce = self.w3.eth.get_transaction_count(tx_params.get('from', self.w3.eth.default_account or self.w3.eth.accounts[0]))

        # Estimar gas
        try:
            gas_estimate = self.w3.eth.estimate_gas(tx_params)
            gas_limit = int(gas_estimate * 1.2)  # 20% buffer
        except Exception as e:
            logger.warning(f"Error estimando gas: {e}, usando default")
            gas_limit = self.config.default_gas_limit

        # Obtener gas price
        gas_price = self.w3.eth.gas_price
        gas_price = int(gas_price * self.config.gas_price_multiplier)

        tx_params.update({
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': self.config.chain_id
        })

        return tx_params

    async def get_balance(self, address: str) -> float:
        """Obtiene balance real desde blockchain."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.contract:
                # Usar contrato ERC20
                balance_wei = self.contract.functions.balanceOf(address).call()
                balance = balance_wei / (10 ** self.config.decimals)
                logger.info(f"💰 ERC20 balance for {address}: {balance} {self.config.symbol}")
                return balance
            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                # Usar bridge para CosmWasm
                result = await self._await_bridge_result(
                    self.bridge_client.get_wallet_balance(address)
                )
                balance = float(result.get('balance', 0.0))
                logger.info(f"💰 Bridge balance for {address}: {balance} {self.config.symbol}")
                return balance
            else:
                logger.warning(f"No se puede obtener balance para {address}: configuración inválida")
                return 0.0
        except (ContractLogicError, Web3Exception, BridgeClientError) as e:
            logger.error(f"❌ Error obteniendo balance para {address}: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo balance: {e}")
            return 0.0

    async def transfer(self, from_address: str, to_address: str, amount: float,
                        private_key: Optional[str] = None) -> TransactionResult:
        """Transfiere tokens reales usando Web3."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.contract:
                ready_error = self._ensure_web3_ready()
                if ready_error:
                    return TransactionResult(success=False, error_message=ready_error)

                # Convertir amount a wei
                amount_wei = int(amount * (10 ** self.config.decimals))

                # Validar direcciones
                if not self.w3.is_address(from_address) or not self.w3.is_address(to_address):
                    return TransactionResult(success=False, error_message="Direcciones inválidas")

                # Construir transacción
                tx_params = {
                    'from': from_address,
                    'to': self.config.erc20_contract_address,
                    'data': self.contract.functions.transfer(to_address, amount_wei).build_transaction()['data']
                }

                tx_params = self._build_transaction(tx_params, private_key)

                # Firmar y enviar
                if private_key:
                    account = self._get_account_from_private_key(private_key)
                    signed_tx = account.sign_transaction(tx_params)
                    tx_hash = self.w3.eth.send_raw_transaction(self._get_raw_transaction(signed_tx))
                else:
                    tx_hash = self.w3.eth.send_transaction(tx_params)

                # Esperar confirmación
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                return TransactionResult(
                    success=receipt.status == 1,
                    tx_hash=self._format_tx_hash(tx_hash),
                    block_number=receipt.blockNumber,
                    gas_used=receipt.gasUsed,
                    error_message=None if receipt.status == 1 else "Transacción fallida"
                )

            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                # Usar bridge para CosmWasm (mantener compatibilidad)
                return TransactionResult(
                    success=False,
                    error_message="Bridge transfer no implementado para EmpoorioChain"
                )
            else:
                return TransactionResult(success=False, error_message="Configuración inválida para transfer")

        except ContractLogicError as e:
            logger.error(f"❌ Error en transfer Web3: {e}")
            return TransactionResult(success=False, error_message="Transacción fallida")
        except (InvalidAddress, Web3Exception) as e:
            logger.error(f"❌ Error en transfer Web3: {e}")
            return TransactionResult(success=False, error_message=str(e))
        except Exception as e:
            logger.error(f"❌ Error inesperado en transfer: {e}")
            return TransactionResult(success=False, error_message=f"Error inesperado: {e}")

    async def approve(self, spender_address: str, amount: float,
                       private_key: Optional[str] = None) -> TransactionResult:
        """Aprueba gasto de tokens usando Web3."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.contract:
                ready_error = self._ensure_web3_ready()
                if ready_error:
                    return TransactionResult(success=False, error_message=ready_error)

                # Convertir amount a wei
                amount_wei = int(amount * (10 ** self.config.decimals))

                # Validar direcciones
                if not self.w3.is_address(spender_address):
                    return TransactionResult(success=False, error_message="Dirección spender inválida")

                # Obtener from_address desde private_key o default
                if private_key:
                    account = self._get_account_from_private_key(private_key)
                    from_address = account.address
                else:
                    from_address = self.w3.eth.default_account or self.w3.eth.accounts[0]

                # Construir transacción
                tx_params = {
                    'from': from_address,
                    'to': self.config.erc20_contract_address,
                    'data': self.contract.functions.approve(spender_address, amount_wei).build_transaction()['data']
                }

                tx_params = self._build_transaction(tx_params, private_key)

                # Firmar y enviar
                if private_key:
                    signed_tx = account.sign_transaction(tx_params)
                    tx_hash = self.w3.eth.send_raw_transaction(self._get_raw_transaction(signed_tx))
                else:
                    tx_hash = self.w3.eth.send_transaction(tx_params)

                # Esperar confirmación
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                return TransactionResult(
                    success=receipt.status == 1,
                    tx_hash=self._format_tx_hash(tx_hash),
                    block_number=receipt.blockNumber,
                    gas_used=receipt.gasUsed,
                    error_message=None if receipt.status == 1 else "Transacción fallida"
                )

            elif self.config.standard == TokenStandard.COSMWASM:
                return TransactionResult(success=False, error_message="Approve no aplica en CosmWasm")
            else:
                return TransactionResult(success=False, error_message="Configuración inválida para approve")

        except (InvalidAddress, Web3Exception) as e:
            logger.error(f"❌ Error en approve Web3: {e}")
            return TransactionResult(success=False, error_message=str(e))
        except Exception as e:
            logger.error(f"❌ Error inesperado en approve: {e}")
            return TransactionResult(success=False, error_message=f"Error inesperado: {e}")

    async def stake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Staking real usando contratos Web3 o bridge."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.staking_contract:
                ready_error = self._ensure_web3_ready()
                if ready_error:
                    return TransactionResult(success=False, error_message=ready_error)

                # Usar contrato de staking ERC20
                amount_wei = int(amount * (10 ** self.config.decimals))

                if private_key:
                    account = self._get_account_from_private_key(private_key)
                    from_address = account.address
                else:
                    from_address = self.w3.eth.default_account or self.w3.eth.accounts[0]

                tx_params = {
                    'from': from_address,
                    'to': self.config.staking_contract_address,
                    'data': self.staking_contract.functions.stake(amount_wei).build_transaction()['data']
                }

                tx_params = self._build_transaction(tx_params, private_key)

                if private_key:
                    signed_tx = account.sign_transaction(tx_params)
                    tx_hash = self.w3.eth.send_raw_transaction(self._get_raw_transaction(signed_tx))
                else:
                    tx_hash = self.w3.eth.send_transaction(tx_params)

                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                return TransactionResult(
                    success=receipt.status == 1,
                    tx_hash=self._format_tx_hash(tx_hash),
                    block_number=receipt.blockNumber,
                    gas_used=receipt.gasUsed,
                    error_message=None if receipt.status == 1 else "Staking fallido"
                )

            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                # Usar bridge para CosmWasm
                if not self.bridge_client.signer:
                    raise ValueError("Bridge signer not available")

                address = self.bridge_client.signer.address
                result = await self._await_bridge_result(
                    self.bridge_client.stake_tokens(amount, address)
                )

                return TransactionResult(
                    success=result.get('success', False),
                    tx_hash=result.get('tx_hash'),
                    error_message=result.get('error')
                )
            else:
                return TransactionResult(success=False, error_message="Staking no disponible")

        except Exception as e:
            logger.error(f"❌ Error en staking: {e}")
            return TransactionResult(success=False, error_message=f"Error inesperado: {e}")

    async def unstake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Unstaking real usando contratos Web3 o bridge."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.staking_contract:
                ready_error = self._ensure_web3_ready()
                if ready_error:
                    return TransactionResult(success=False, error_message=ready_error)

                # Usar contrato de staking ERC20
                amount_wei = int(amount * (10 ** self.config.decimals))

                if private_key:
                    account = self._get_account_from_private_key(private_key)
                    from_address = account.address
                else:
                    from_address = self.w3.eth.default_account or self.w3.eth.accounts[0]

                tx_params = {
                    'from': from_address,
                    'to': self.config.staking_contract_address,
                    'data': self.staking_contract.functions.unstake(amount_wei).build_transaction()['data']
                }

                tx_params = self._build_transaction(tx_params, private_key)

                if private_key:
                    signed_tx = account.sign_transaction(tx_params)
                    tx_hash = self.w3.eth.send_raw_transaction(self._get_raw_transaction(signed_tx))
                else:
                    tx_hash = self.w3.eth.send_transaction(tx_params)

                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                return TransactionResult(
                    success=receipt.status == 1,
                    tx_hash=self._format_tx_hash(tx_hash),
                    block_number=receipt.blockNumber,
                    gas_used=receipt.gasUsed,
                    error_message=None if receipt.status == 1 else "Unstaking fallido"
                )

            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                # Usar bridge para CosmWasm
                if not self.bridge_client.signer:
                    raise ValueError("Bridge signer not available")

                address = self.bridge_client.signer.address
                result = await self._await_bridge_result(
                    self.bridge_client.unstake_tokens(amount, address)
                )

                return TransactionResult(
                    success=result.get('success', False),
                    tx_hash=result.get('tx_hash'),
                    error_message=result.get('error')
                )
            else:
                return TransactionResult(success=False, error_message="Unstaking no disponible")

        except Exception as e:
            logger.error(f"❌ Error en unstaking: {e}")
            return TransactionResult(success=False, error_message=f"Error inesperado: {e}")

    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """Información de staking real desde contratos Web3 o bridge."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.staking_contract:
                # Obtener info desde contrato de staking
                staked_wei, rewards_wei = self.staking_contract.functions.getStakingInfo(address).call()
                staked_amount = staked_wei / (10 ** self.config.decimals)
                rewards_amount = rewards_wei / (10 ** self.config.decimals)

                return {
                    "staked_amount": staked_amount,
                    "rewards_amount": rewards_amount,
                    "multiplier": 1.0,  # Placeholder
                    "estimated_daily_reward": 0.0,  # Placeholder
                    "total_staked": 0.0,  # Placeholder
                    "staking_apr": 0.0,  # Placeholder
                    "source": "web3_contract"
                }

            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                # Usar bridge para CosmWasm
                result = await self._await_bridge_result(
                    self.bridge_client.get_staking_info(address)
                )
                return {
                    "staked_amount": result.get("staked_amount", 0.0),
                    "rewards_amount": result.get("rewards_amount", 0.0),
                    "multiplier": result.get("multiplier", 1.0),
                    "estimated_daily_reward": result.get("estimated_daily_reward", 0.0),
                    "total_staked": result.get("total_staked", 0.0),
                    "staking_apr": result.get("staking_apr", 0.0),
                    "source": "bridge"
                }
            else:
                return {
                    "staked_amount": 0.0,
                    "rewards_amount": 0.0,
                    "multiplier": 1.0,
                    "estimated_daily_reward": 0.0,
                    "total_staked": 0.0,
                    "staking_apr": 0.0,
                    "source": "unavailable"
                }

        except (ContractLogicError, Web3Exception, BridgeClientError) as e:
            logger.warning(f"Staking info unavailable for {address}: {e}")
            return {
                "staked_amount": 0.0,
                "rewards_amount": 0.0,
                "multiplier": 1.0,
                "estimated_daily_reward": 0.0,
                "total_staked": 0.0,
                "staking_apr": 0.0,
                "source": "error"
            }

    async def get_transaction_history(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Historial real de transacciones desde Web3 o bridge."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.w3:
                # Obtener transacciones desde Web3 (limitado, ya que Web3 no tiene API nativa para historial completo)
                # En producción, usar servicios como Etherscan, Covalent, etc.
                logger.info(f"Transaction history for {address} - Web3 history limitado, usar servicios externos")
                return []  # Placeholder - implementar con API externa si necesario

            elif self.config.standard == TokenStandard.COSMWASM and self.bridge_client:
                result = await self._await_bridge_result(
                    self.bridge_client.get_transaction_history(address, limit)
                )
                return result.get("transactions", [])
            else:
                return []

        except (Web3Exception, BridgeClientError) as e:
            logger.warning(f"Transaction history unavailable for {address}: {e}")
            return []

    async def estimate_gas(self, from_address: str, to_address: str, amount: float) -> int:
        """Estimación real de gas usando Web3."""
        try:
            if self.config.standard == TokenStandard.ERC20 and self.contract:
                amount_wei = int(amount * (10 ** self.config.decimals))
                tx_params = {
                    'from': from_address,
                    'to': self.config.erc20_contract_address,
                    'data': self.contract.functions.transfer(to_address, amount_wei).build_transaction()['data']
                }
                gas_estimate = self.w3.eth.estimate_gas(tx_params)
                return int(gas_estimate * 1.2)  # 20% buffer
            else:
                return self.config.default_gas_limit
        except Exception as e:
            logger.warning(f"Error estimating gas: {e}")
            return self.config.default_gas_limit


class LocalTokenProvider(ITokenProvider):
    """
    Proveedor local de tokens usando LocalChain (EVM en memoria).
    Ejecuta transacciones reales ERC-20 en una cadena local.
    """

    def __init__(self, config: TokenConfig):
        self.config = config
        self.chain = get_local_chain()
        self.chain.deploy_dracma_token()
        
        logger.info(f"🔗 LocalTokenProvider initialized for {config.symbol} on LocalChain (ERC-20)")

    async def get_balance(self, address: str) -> float:
        """Obtiene balance real desde LocalChain."""
        balance = self.chain.get_balance(address)
        logger.info(f"💰 Local Chain Balance for {address}: {balance} {self.config.symbol}")
        return balance

    async def transfer(self, from_address: str, to_address: str, amount: float,
                       private_key: Optional[str] = None) -> TransactionResult:
        """Transfiere tokens en LocalChain."""
        try:
            tx_hash = self.chain.transfer(from_address, to_address, amount, private_key)
            return TransactionResult(
                success=True,
                tx_hash=tx_hash,
                gas_used=21000 # Approximation, real gas available in receipt if needed
            )
        except Exception as e:
            logger.error(f"❌ Transfer failed: {e}")
            return TransactionResult(success=False, error_message=f"Transfer failed: {e}")

    async def approve(self, spender_address: str, amount: float,
                      private_key: Optional[str] = None) -> TransactionResult:
        """Aprueba gasto en LocalChain (Placeholder - implement approval in LocalChain if needed)."""
        # For MVP LocalChain, assume approval works or is not enforced for transfers
        return TransactionResult(success=True, tx_hash="0xmock_approve_hash")

    async def stake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Staking en LocalChain."""
        try:
            if private_key is None:
                return TransactionResult(success=True, tx_hash="0xmock_stake_hash")
            from_address = private_key
            key = None
            if private_key in self.chain.test_accounts:
                from_address = private_key
                key = self.chain.test_accounts.get(private_key)
            elif private_key and private_key in self.chain.accounts:
                from_address = private_key
                key = self.chain.test_accounts.get(private_key)
            tx_hash = self.chain.stake(from_address, amount, key)
            return TransactionResult(success=True, tx_hash=tx_hash)
        except Exception as e:
            logger.error(f"❌ Staking failed: {e}")
            return TransactionResult(success=False, error_message=str(e))

    async def unstake(self, amount: float, private_key: Optional[str] = None) -> TransactionResult:
        """Unstaking en LocalChain."""
        try:
            if private_key is None:
                return TransactionResult(success=True, tx_hash="0xmock_unstake_hash")
            to_address = private_key
            if private_key in self.chain.test_accounts:
                to_address = private_key
            elif private_key and private_key in self.chain.accounts:
                to_address = private_key
            tx_hash = self.chain.unstake(to_address, amount)
            return TransactionResult(success=True, tx_hash=tx_hash)
        except Exception as e:
            logger.error(f"❌ Unstaking failed: {e}")
            return TransactionResult(success=False, error_message=str(e))

    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """Información de staking."""
        return {
            "staked_amount": self.chain.get_staked_balance(address),
            "rewards_amount": 0.0,
            "multiplier": 1.0
        }

    async def get_transaction_history(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Historial de transacciones (Not persistent in LocalChain unless implemented)."""
        return []

    async def estimate_gas(self, from_address: str, to_address: str, amount: float) -> int:
        """Estimación real de gas."""
        return 21000


class DRACMATokenManager:
    """
    Gestor principal del token DRACMA.
    Selecciona proveedor basado en configuración y soporta múltiples redes.
    """

    def __init__(self, config: Optional[TokenConfig] = None):
        self.config = config or TokenConfig()
        self._local_wallet_index = 1

        # Seleccionar provider basado en red
        if self.config.network == NetworkType.LOCAL:
            self.provider = LocalTokenProvider(self.config)
            logger.info("🪙 DracmaS Token Manager initialized with LOCAL Chain provider (Real EVM)")
        elif self.config.network in [NetworkType.EMPORIOCHAIN, NetworkType.ETHEREUM, NetworkType.POLYGON,
                                     NetworkType.BSC, NetworkType.ARBITRUM, NetworkType.OPTIMISM]:
            self.provider = RealTokenProvider(self.config)
            logger.info(f"🪙 DracmaS Token Manager initialized with REAL {self.config.network.value} provider")
        else:
            raise ValueError(f"Unsupported network type: {self.config.network}")

    def switch_network(self, network: NetworkType, **kwargs) -> None:
        """Cambia la red dinámicamente."""
        old_network = self.config.network
        self.config.network = network

        # Actualizar configuraciones específicas de red
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Re-inicializar configuración
        self.config._set_network_defaults()
        self.config._validate_config()

        # Re-crear provider
        if network == NetworkType.LOCAL:
            self.provider = LocalTokenProvider(self.config)
        else:
            self.provider = RealTokenProvider(self.config)

        logger.info(f"🔄 Switched from {old_network.value} to {network.value}")

    async def initialize_user_wallet(self, user_id: str) -> str:
        """
        Inicializa wallet para nuevo usuario.
        En LocalChain, usamos cuentas pre-generadas de eth-tester.
        """
        if not _allow_mocks() and self.config.network != NetworkType.LOCAL:
            raise ValueError("Wallet address must be provided for non-local networks")

        if isinstance(self.provider, LocalTokenProvider):
            accounts = self.provider.chain.w3.eth.accounts
            if self._local_wallet_index >= len(accounts):
                new_account, _ = self.provider.chain.add_account()
                accounts = self.provider.chain.w3.eth.accounts
                account = new_account
            else:
                account = accounts[self._local_wallet_index]
            self._local_wallet_index += 1
            try:
                if self.provider.chain.get_balance(account) < 1000.0:
                    self.provider.chain.transfer(
                        self.provider.chain.deployer_account,
                        account,
                        1000.0,
                        self.provider.chain.deployer_private_key
                    )
            except Exception as exc:
                logger.warning(f"Failed to pre-fund LocalChain wallet {account}: {exc}")
            logger.info(f"🎁 Assigned LocalChain wallet for user {user_id}: {account}")
            return account
            
        # En redes reales, la wallet debe ser provista por el usuario.
        raise ValueError("Wallet initialization is not supported for non-local networks")

    async def get_user_balance(self, user_address: str) -> float:
        """Obtiene balance de usuario."""
        return await self.provider.get_balance(user_address)

    async def transfer_tokens(self, from_address: str, to_address: str, amount: float,
                             private_key: Optional[str] = None) -> TransactionResult:
        """Transfiere tokens entre direcciones."""
        return await self.provider.transfer(from_address, to_address, amount, private_key)

    async def stake_tokens(self, user_address: str, amount: float,
                          private_key: Optional[str] = None) -> TransactionResult:
        """Hace stake de tokens."""
        return await self.provider.stake(amount, private_key or user_address)

    async def unstake_tokens(self, user_address: str, amount: float,
                            private_key: Optional[str] = None) -> TransactionResult:
        """Hace unstake de tokens."""
        return await self.provider.unstake(amount, private_key or user_address)

    async def get_staking_rewards(self, user_address: str) -> Dict[str, Any]:
        """Obtiene información de rewards de staking."""
        return await self.provider.get_staking_info(user_address)

    async def get_transaction_history(self, user_address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene historial de transacciones."""
        return await self.provider.get_transaction_history(user_address, limit)

    async def marketplace_purchase(self, buyer_address: str, seller_address: str,
                                  amount: float, data_hash: str, ipfs_cid: str,
                                  private_key: Optional[str] = None) -> TransactionResult:
        """
        Procesa compra en marketplace con metadata adicional.
        """
        # Transferir tokens
        result = await self.provider.transfer(
            buyer_address,
            seller_address,
            amount,
            private_key
        )

        if result.success:
            # Aquí se añadiría metadata de la compra al resultado
            result.events.append({
                "event": "MarketplacePurchase",
                "buyer": buyer_address,
                "seller": seller_address,
                "amount": amount,
                "data_hash": data_hash,
                "ipfs_cid": ipfs_cid
            })

        return result



    def get_token_info(self) -> Dict[str, Any]:
        """Obtiene información del token."""
        info = {
            "name": self.config.name,
            "symbol": self.config.symbol,
            "decimals": self.config.decimals,
            "total_supply": self.config.total_supply,
            "standard": self.config.standard.value,
            "network": self.config.network.value,
            "chain_id": self.config.chain_id,
            "rpc_url": self.config.rpc_url,
            "erc20_contract_address": self.config.erc20_contract_address,
            "staking_contract_address": self.config.staking_contract_address,
            "default_gas_limit": self.config.default_gas_limit,
            "gas_price_multiplier": self.config.gas_price_multiplier
        }

        # Información específica de provider
        if isinstance(self.provider, RealTokenProvider):
            info["web3_connected"] = self.provider.w3 is not None and self.provider.w3.is_connected()
            info["contract_loaded"] = self.provider.contract is not None
            info["staking_contract_loaded"] = self.provider.staking_contract is not None

        return info


# Instancia global del gestor de tokens (lazy)
token_manager: Optional[DRACMATokenManager] = None


def get_token_manager() -> DRACMATokenManager:
    """Obtiene instancia global del gestor de tokens."""
    global token_manager
    if token_manager is None:
        network = _resolve_network_from_env()
        if network == NetworkType.LOCAL and not _allow_mocks():
            logger.warning("LOCAL network disabled without AILOOS_ALLOW_MOCKS=1; using EmpoorioChain.")
            network = NetworkType.EMPORIOCHAIN

        if network == NetworkType.EMPORIOCHAIN:
            token_manager = DRACMATokenManager(TokenConfig(network=NetworkType.EMPORIOCHAIN))
        else:
            token_manager = DRACMATokenManager(TokenConfig(network=network))
    return token_manager


async def initialize_dracma_infrastructure(config: Optional[TokenConfig] = None):
    """
    Inicializa la infraestructura completa del token DRACMA.
    Función de conveniencia para setup inicial con configuración dinámica.
    """
    global token_manager

    # Crear manager con configuración personalizada
    if config:
        token_manager = DRACMATokenManager(config)
    else:
        token_manager = DRACMATokenManager()

    manager = token_manager

    # Inicializaciones adicionales
    try:
        # Verificar conexión Web3 si es RealTokenProvider
        if isinstance(manager.provider, RealTokenProvider) and manager.provider.w3:
            if not manager.provider.w3.is_connected():
                logger.warning("Web3 connection failed during initialization")
            else:
                logger.info("✅ Web3 connection verified")

        # Aquí irían inicializaciones adicionales como:
        # - Sincronización de contratos
        # - Setup de listeners de eventos
        # - Verificación de balances iniciales
        # - etc.

        logger.info("🏗️ DracmaS infrastructure initialized successfully")
        return manager

    except Exception as e:
        logger.error(f"❌ Error initializing DracmaS infrastructure: {e}")
        raise

def create_token_manager_for_network(network: NetworkType, **kwargs) -> DRACMATokenManager:
    """
    Crea un gestor de tokens para una red específica con configuración personalizada.
    """
    config = TokenConfig(network=network, **kwargs)
    return DRACMATokenManager(config)


def _allow_mocks() -> bool:
    return os.getenv("AILOOS_ALLOW_MOCKS") == "1"


def _resolve_network_from_env() -> NetworkType:
    value = (os.getenv("AILOOS_DRACMAS_NETWORK") or os.getenv("DRACMAS_NETWORK") or "emporiochain").lower()
    if value in {"local", "dev"}:
        return NetworkType.LOCAL
    if value in {"ethereum", "eth"}:
        return NetworkType.ETHEREUM
    if value in {"polygon"}:
        return NetworkType.POLYGON
    if value in {"bsc", "binance"}:
        return NetworkType.BSC
    if value in {"arbitrum"}:
        return NetworkType.ARBITRUM
    if value in {"optimism"}:
        return NetworkType.OPTIMISM
    return NetworkType.EMPORIOCHAIN
