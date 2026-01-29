import logging
import os
from typing import Optional, Dict, Any

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, InvalidAddress, Web3Exception
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    ContractLogicError = InvalidAddress = Web3Exception = Exception
    Account = None
    LocalAccount = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AaveClient:
    """
    Cliente para interactuar con Aave V3 en Ethereum.
    Proporciona métodos para lending (supply, borrow, repay, withdraw) y staking.
    """
    LEGACY_MESSAGE = (
        "Integracion EVM/DeFi legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Direcciones de contratos en Ethereum mainnet
    POOL_ADDRESS = "0x87870Bcd2C42b4C4e0F5e38D4dC1F7B7E7C8b8"  # Aave V3 Pool
    POOL_DATA_PROVIDER_ADDRESS = "0x7B4EB56E7CD4b454BA8ff71E4510Ce793c118CF2"  # Pool Data Provider
    STK_AAVE_ADDRESS = "0x4da27a545c0c5B758a6BA100e3a049001de870f5"  # stkAAVE (para staking)
    WETH_GATEWAY_ADDRESS = "0xD322A49006FC828F9B5B37Ab215F99B4E5caB19C"  # WETH Gateway

    # ABI simplificada para Pool
    POOL_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
                {"internalType": "address", "name": "onBehalfOf", "type": "address"}
            ],
            "name": "borrow",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                {"internalType": "address", "name": "onBehalfOf", "type": "address"}
            ],
            "name": "repay",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address", "name": "to", "type": "address"}
            ],
            "name": "withdraw",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    # ABI para stkAAVE (staking)
    STK_AAVE_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "stake",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "uint256", "name": "cooldownTimestamp", "type": "uint256"}
            ],
            "name": "redeem",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    def __init__(self, rpc_url: str, private_key: Optional[str] = None):
        """
        Inicializa el cliente Aave.

        Args:
            rpc_url: URL del nodo RPC de Ethereum
            private_key: Clave privada para firmar transacciones
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("No se pudo conectar al nodo RPC de Ethereum")

        self.account: Optional[LocalAccount] = None
        if private_key:
            self.account = Account.from_key(private_key)

        self.pool = self.w3.eth.contract(
            address=self.POOL_ADDRESS,
            abi=self.POOL_ABI
        )

        self.stk_aave = self.w3.eth.contract(
            address=self.STK_AAVE_ADDRESS,
            abi=self.STK_AAVE_ABI
        )

        logger.info("AaveClient inicializado correctamente")

    def supply(self, asset: str, amount: int, on_behalf_of: Optional[str] = None, referral_code: int = 0) -> str:
        """
        Suministra activos al protocolo Aave.

        Args:
            asset: Dirección del activo a suministrar
            amount: Cantidad a suministrar
            on_behalf_of: Dirección en nombre de la cual suministrar (opcional)
            referral_code: Código de referido

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            if on_behalf_of is None:
                on_behalf_of = self.account.address

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.pool.functions.supply(asset, amount, on_behalf_of, referral_code).build_transaction({
                'chainId': 1,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Supply enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en supply: {e}")
            raise

    def borrow(self, asset: str, amount: int, interest_rate_mode: int = 1, referral_code: int = 0, on_behalf_of: Optional[str] = None) -> str:
        """
        Toma prestado activos del protocolo Aave.

        Args:
            asset: Dirección del activo a tomar prestado
            amount: Cantidad a tomar prestada
            interest_rate_mode: Modo de tasa de interés (1=estable, 2=variable)
            referral_code: Código de referido
            on_behalf_of: Dirección en nombre de la cual tomar prestado

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            if on_behalf_of is None:
                on_behalf_of = self.account.address

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.pool.functions.borrow(asset, amount, interest_rate_mode, referral_code, on_behalf_of).build_transaction({
                'chainId': 1,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Borrow enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en borrow: {e}")
            raise

    def repay(self, asset: str, amount: int, interest_rate_mode: int = 1, on_behalf_of: Optional[str] = None) -> str:
        """
        Repaga un préstamo en Aave.

        Args:
            asset: Dirección del activo a repagar
            amount: Cantidad a repagar (-1 para repagar todo)
            interest_rate_mode: Modo de tasa de interés
            on_behalf_of: Dirección en nombre de la cual repagar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            if on_behalf_of is None:
                on_behalf_of = self.account.address

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.pool.functions.repay(asset, amount, interest_rate_mode, on_behalf_of).build_transaction({
                'chainId': 1,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Repay enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en repay: {e}")
            raise

    def withdraw(self, asset: str, amount: int, to: Optional[str] = None) -> str:
        """
        Retira activos suministrados de Aave.

        Args:
            asset: Dirección del activo a retirar
            amount: Cantidad a retirar (-1 para retirar todo)
            to: Dirección a la que enviar los activos

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            if to is None:
                to = self.account.address

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.pool.functions.withdraw(asset, amount, to).build_transaction({
                'chainId': 1,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Withdraw enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en withdraw: {e}")
            raise

    def stake_aave(self, amount: int, recipient: Optional[str] = None) -> str:
        """
        Stake AAVE tokens para stkAAVE.

        Args:
            amount: Cantidad de AAVE a stakear
            recipient: Dirección que recibirá stkAAVE

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            if recipient is None:
                recipient = self.account.address

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.stk_aave.functions.stake(recipient, amount).build_transaction({
                'chainId': 1,
                'gas': 150000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Stake enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en stake: {e}")
            raise

    def redeem_stk_aave(self, amount: int) -> str:
        """
        Redeem stkAAVE tokens.

        Args:
            amount: Cantidad a redeem

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            # cooldownTimestamp = 0 para redeem inmediato si está disponible
            cooldown_timestamp = 0

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.stk_aave.functions.redeem(amount, cooldown_timestamp).build_transaction({
                'chainId': 1,
                'gas': 150000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Redeem enviado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en redeem: {e}")
            raise

    def get_user_account_data(self, user: str) -> Dict[str, Any]:
        """
        Obtiene datos de cuenta del usuario en Aave.

        Args:
            user: Dirección del usuario

        Returns:
            Diccionario con datos de la cuenta
        """
        try:
            # Usar Pool Data Provider para obtener datos
            data_provider = self.w3.eth.contract(
                address=self.POOL_DATA_PROVIDER_ADDRESS,
                abi=[{"inputs": [{"internalType": "address", "name": "user", "type": "address"}], "name": "getUserAccountData", "outputs": [{"components": [{"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"}, {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"}, {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"}, {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"}, {"internalType": "uint256", "name": "ltv", "type": "uint256"}, {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}], "internalType": "struct DataTypes.UserAccountData", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}]
            )
            data = data_provider.functions.getUserAccountData(user).call()
            result = {
                'totalCollateralBase': data[0],
                'totalDebtBase': data[1],
                'availableBorrowsBase': data[2],
                'currentLiquidationThreshold': data[3],
                'ltv': data[4],
                'healthFactor': data[5]
            }
            logger.info(f"Datos de cuenta para {user}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error obteniendo datos de cuenta: {e}")
            raise
