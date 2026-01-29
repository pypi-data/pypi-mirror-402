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

class CompoundClient:
    """
    Cliente para interactuar con Compound V3 (Comet) en Ethereum.
    Proporciona métodos para lending adicional.
    """
    LEGACY_MESSAGE = (
        "Integracion EVM/DeFi legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Direcciones de contratos en Ethereum mainnet
    COMET_USDC_ADDRESS = "0xc3d688B66703497DAA19211EEdff47f25384cdc3"  # Compound III USDC
    COMET_WETH_ADDRESS = "0xA17581A9E3356d9A858b789D68B4d866e593aE94"  # Compound III WETH

    # ABI simplificada para Comet
    COMET_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "borrow",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "repay",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
            "name": "borrowBalanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, rpc_url: str, private_key: Optional[str] = None, comet_address: str = COMET_USDC_ADDRESS):
        """
        Inicializa el cliente Compound.

        Args:
            rpc_url: URL del nodo RPC de Ethereum
            private_key: Clave privada para firmar transacciones
            comet_address: Dirección del contrato Comet (por defecto USDC)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("No se pudo conectar al nodo RPC de Ethereum")

        self.account: Optional[LocalAccount] = None
        if private_key:
            self.account = Account.from_key(private_key)

        self.comet = self.w3.eth.contract(
            address=comet_address,
            abi=self.COMET_ABI
        )

        logger.info(f"CompoundClient inicializado con Comet: {comet_address}")

    def supply(self, asset: str, amount: int) -> str:
        """
        Suministra activos al protocolo Compound.

        Args:
            asset: Dirección del activo a suministrar
            amount: Cantidad a suministrar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.comet.functions.supply(asset, amount).build_transaction({
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

    def withdraw(self, asset: str, amount: int) -> str:
        """
        Retira activos suministrados de Compound.

        Args:
            asset: Dirección del activo a retirar
            amount: Cantidad a retirar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.comet.functions.withdraw(asset, amount).build_transaction({
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

    def borrow(self, asset: str, amount: int) -> str:
        """
        Toma prestado activos del protocolo Compound.

        Args:
            asset: Dirección del activo a tomar prestado
            amount: Cantidad a tomar prestada

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.comet.functions.borrow(asset, amount).build_transaction({
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

    def repay(self, asset: str, amount: int) -> str:
        """
        Repaga un préstamo en Compound.

        Args:
            asset: Dirección del activo a repagar
            amount: Cantidad a repagar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = self.comet.functions.repay(asset, amount).build_transaction({
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

    def get_supply_balance(self, owner: str) -> int:
        """
        Obtiene el balance de suministro del usuario.

        Args:
            owner: Dirección del propietario

        Returns:
            Balance de suministro
        """
        try:
            balance = self.comet.functions.balanceOf(owner).call()
            logger.info(f"Supply balance de {owner}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error obteniendo supply balance: {e}")
            raise

    def get_borrow_balance(self, account: str) -> int:
        """
        Obtiene el balance de préstamo del usuario.

        Args:
            account: Dirección de la cuenta

        Returns:
            Balance de préstamo
        """
        try:
            balance = self.comet.functions.borrowBalanceOf(account).call()
            logger.info(f"Borrow balance de {account}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error obteniendo borrow balance: {e}")
            raise

    def get_account_data(self, account: str) -> Dict[str, Any]:
        """
        Obtiene datos completos de la cuenta en Compound.

        Args:
            account: Dirección de la cuenta

        Returns:
            Diccionario con datos de la cuenta
        """
        try:
            supply_balance = self.get_supply_balance(account)
            borrow_balance = self.get_borrow_balance(account)

            # Calcular health factor aproximado (simplificado)
            # En producción, usar el método getAccountLiquidity o similar
            health_factor = 0
            if borrow_balance > 0:
                health_factor = (supply_balance * 100) // borrow_balance  # Porcentaje simplificado

            result = {
                'supply_balance': supply_balance,
                'borrow_balance': borrow_balance,
                'health_factor': health_factor
            }

            logger.info(f"Datos de cuenta para {account}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error obteniendo datos de cuenta: {e}")
            raise

    def approve_asset(self, asset_address: str, spender_address: str, amount: int) -> str:
        """
        Aprueba a un spender para gastar un activo.

        Args:
            asset_address: Dirección del activo
            spender_address: Dirección del spender
            amount: Cantidad a aprobar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            asset_contract = self.w3.eth.contract(
                address=asset_address,
                abi=[{"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}]
            )

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = asset_contract.functions.approve(spender_address, amount).build_transaction({
                'chainId': 1,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Aprobación enviada: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en aprobación: {e}")
            raise
