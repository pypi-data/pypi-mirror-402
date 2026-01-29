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

class UniswapClient:
    """
    Cliente para interactuar con Uniswap V3 en Ethereum.
    Proporciona métodos para realizar swaps de tokens.
    """
    LEGACY_MESSAGE = (
        "Integracion EVM/DeFi legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Direcciones de contratos en Ethereum mainnet
    SWAP_ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # Uniswap V3 SwapRouter
    FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"  # Uniswap V3 Factory
    WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # Wrapped Ether

    # ABI simplificada para SwapRouter (solo métodos necesarios)
    SWAP_ROUTER_ABI = [
        {
            "inputs": [
                {
                    "components": [
                        {"internalType": "address", "name": "tokenIn", "type": "address"},
                        {"internalType": "address", "name": "tokenOut", "type": "address"},
                        {"internalType": "uint24", "name": "fee", "type": "uint24"},
                        {"internalType": "address", "name": "recipient", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                        {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                    ],
                    "internalType": "struct ISwapRouter.ExactInputSingleParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "exactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]

    def __init__(self, rpc_url: str, private_key: Optional[str] = None):
        """
        Inicializa el cliente Uniswap.

        Args:
            rpc_url: URL del nodo RPC de Ethereum
            private_key: Clave privada para firmar transacciones (opcional para operaciones de solo lectura)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("No se pudo conectar al nodo RPC de Ethereum")

        self.account: Optional[LocalAccount] = None
        if private_key:
            self.account = Account.from_key(private_key)

        self.swap_router = self.w3.eth.contract(
            address=self.SWAP_ROUTER_ADDRESS,
            abi=self.SWAP_ROUTER_ABI
        )

        logger.info("UniswapClient inicializado correctamente")

    def get_token_balance(self, token_address: str, wallet_address: str) -> int:
        """
        Obtiene el balance de un token ERC20 para una dirección.

        Args:
            token_address: Dirección del contrato del token
            wallet_address: Dirección de la wallet

        Returns:
            Balance del token en unidades mínimas
        """
        try:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=[{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
            )
            balance = token_contract.functions.balanceOf(wallet_address).call()
            logger.info(f"Balance de {token_address} para {wallet_address}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            raise

    def approve_token(self, token_address: str, spender_address: str, amount: int) -> str:
        """
        Aprueba a un spender para gastar tokens.

        Args:
            token_address: Dirección del token
            spender_address: Dirección del spender (ej. SwapRouter)
            amount: Cantidad a aprobar

        Returns:
            Hash de la transacción
        """
        if not self.account:
            raise ValueError("Se requiere private_key para operaciones de escritura")

        try:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=[{"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}]
            )

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            txn = token_contract.functions.approve(spender_address, amount).build_transaction({
                'chainId': 1,  # Ethereum mainnet
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

    def swap_exact_input_single(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_in: int,
        amount_out_minimum: int = 0,
        deadline: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Realiza un swap exacto de entrada única en Uniswap V3.

        Args:
            token_in: Dirección del token de entrada
            token_out: Dirección del token de salida
            fee: Fee del pool (ej. 3000 para 0.3%)
            amount_in: Cantidad de token_in a gastar
            amount_out_minimum: Cantidad mínima de token_out a recibir
            deadline: Timestamp límite para la transacción

        Returns:
            Diccionario con resultado del swap
        """
        if not self.account:
            raise ValueError("Se requiere private_key para swaps")

        try:
            if deadline is None:
                deadline = self.w3.eth.get_block('latest')['timestamp'] + 3600  # 1 hora

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price

            params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': fee,
                'recipient': self.account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': amount_out_minimum,
                'sqrtPriceLimitX96': 0
            }

            txn = self.swap_router.functions.exactInputSingle(params).build_transaction({
                'chainId': 1,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'value': 0 if token_in != self.WETH_ADDRESS else amount_in  # Si es ETH, enviar valor
            })

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Esperar confirmación
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            result = {
                'tx_hash': tx_hash.hex(),
                'status': receipt['status'],
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber']
            }

            logger.info(f"Swap completado: {result}")
            return result

        except ContractLogicError as e:
            logger.error(f"Error lógico en contrato: {e}")
            raise
        except Web3Exception as e:
            logger.error(f"Error Web3: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en swap: {e}")
            raise

    def get_quote(self, token_in: str, token_out: str, fee: int, amount_in: int) -> int:
        """
        Obtiene una cotización aproximada para un swap.

        Args:
            token_in: Dirección del token de entrada
            token_out: Dirección del token de salida
            fee: Fee del pool
            amount_in: Cantidad de entrada

        Returns:
            Cantidad aproximada de salida
        """
        try:
            # Para cotización, podríamos usar un contrato de quoter o simular
            # Por simplicidad, devolver un valor estimado (en producción usar Quoter contract)
            # Esto es una aproximación básica
            logger.warning("get_quote es una aproximación básica. Usar Quoter contract en producción.")
            return amount_in * 95 // 100  # 5% slippage aproximado
        except Exception as e:
            logger.error(f"Error obteniendo cotización: {e}")
            raise
