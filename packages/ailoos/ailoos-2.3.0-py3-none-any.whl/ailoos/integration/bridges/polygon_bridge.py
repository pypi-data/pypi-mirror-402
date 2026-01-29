import os
import logging
from typing import Optional, Dict, Any

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, TransactionNotFound
    from eth_account import Account
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    ContractLogicError = TransactionNotFound = Exception
    Account = None

# ABIs simplificadas para contratos clave de Polygon PoS Bridge
ROOT_CHAIN_MANAGER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "rootToken", "type": "address"},
            {"internalType": "bytes", "name": "depositData", "type": "bytes"}
        ],
        "name": "depositFor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"}
        ],
        "name": "depositEtherFor",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes", "name": "inputData", "type": "bytes"}
        ],
        "name": "exit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ERC20_PREDICATE_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "rootToken", "type": "address"},
            {"internalType": "address", "name": "childToken", "type": "address"},
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "lockTokens",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

CHILD_CHAIN_MANAGER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "rootToken", "type": "address"},
            {"internalType": "bytes", "name": "log", "type": "bytes"}
        ],
        "name": "exit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

class PolygonBridge:
    def __init__(self, eth_rpc: str, polygon_rpc: str, private_key: str):
        self.legacy_message = (
            "Bridge Polygon legacy. EmpoorioChain usa bridge nativo DracmaSToken."
        )
        raise NotImplementedError(self.legacy_message)
        self.logger = logging.getLogger(__name__)
        self.w3_eth = Web3(Web3.HTTPProvider(eth_rpc))
        self.w3_polygon = Web3(Web3.HTTPProvider(polygon_rpc))
        self.account = Account.from_key(private_key)

        if not self.w3_eth.is_connected():
            raise ConnectionError("No se pudo conectar a Ethereum RPC")
        if not self.w3_polygon.is_connected():
            raise ConnectionError("No se pudo conectar a Polygon RPC")

        # Direcciones de contratos (Mainnet)
        self.root_chain_manager_address = Web3.to_checksum_address('0xA0c68C638235ee32657e8f720a23ceC1bFc77C77E')
        self.erc20_predicate_address = Web3.to_checksum_address('0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf')
        self.child_chain_manager_address = Web3.to_checksum_address('0xD4888faB8bd39A663B63161F7D8E27C8e22b1Fbc')

        self.root_chain_contract = self.w3_eth.eth.contract(
            address=self.root_chain_manager_address, abi=ROOT_CHAIN_MANAGER_ABI
        )
        self.erc20_predicate_contract = self.w3_eth.eth.contract(
            address=self.erc20_predicate_address, abi=ERC20_PREDICATE_ABI
        )
        self.child_chain_contract = self.w3_polygon.eth.contract(
            address=self.child_chain_manager_address, abi=CHILD_CHAIN_MANAGER_ABI
        )

    def deposit_erc20(self, token_address: str, amount: int, user_address: str) -> str:
        """Deposita ERC20 desde Ethereum a Polygon"""
        try:
            token_address = Web3.to_checksum_address(token_address)
            user_address = Web3.to_checksum_address(user_address)

            # Aprobar tokens
            token_contract = self.w3_eth.eth.contract(address=token_address, abi=ERC20_ABI)
            approve_tx = token_contract.functions.approve(
                self.erc20_predicate_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3_eth.eth.gas_price,
                'nonce': self.w3_eth.eth.get_transaction_count(self.account.address),
            })
            signed_approve = self.account.sign_transaction(approve_tx)
            approve_hash = self.w3_eth.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3_eth.eth.wait_for_transaction_receipt(approve_hash)
            self.logger.info(f"Aprobación completada: {approve_hash.hex()}")

            # Depositar
            deposit_data = amount.to_bytes(32, 'big')
            deposit_tx = self.root_chain_contract.functions.depositFor(
                user_address, token_address, deposit_data
            ).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3_eth.eth.gas_price,
                'nonce': self.w3_eth.eth.get_transaction_count(self.account.address),
            })
            signed_deposit = self.account.sign_transaction(deposit_tx)
            deposit_hash = self.w3_eth.eth.send_raw_transaction(signed_deposit.rawTransaction)
            self.logger.info(f"Depósito iniciado: {deposit_hash.hex()}")
            return deposit_hash.hex()
        except Exception as e:
            self.logger.error(f"Error en deposit_erc20: {e}")
            raise

    def deposit_eth(self, amount: int, user_address: str) -> str:
        """Deposita ETH desde Ethereum a Polygon"""
        try:
            user_address = Web3.to_checksum_address(user_address)
            deposit_tx = self.root_chain_contract.functions.depositEtherFor(user_address).build_transaction({
                'from': self.account.address,
                'value': amount,
                'gas': 150000,
                'gasPrice': self.w3_eth.eth.gas_price,
                'nonce': self.w3_eth.eth.get_transaction_count(self.account.address),
            })
            signed = self.account.sign_transaction(deposit_tx)
            tx_hash = self.w3_eth.eth.send_raw_transaction(signed.rawTransaction)
            self.logger.info(f"Depósito ETH iniciado: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Error en deposit_eth: {e}")
            raise

    def withdraw_erc20(self, token_address: str, amount: int, user_address: str) -> str:
        """Retira ERC20 desde Polygon a Ethereum (burn en Polygon, exit en Ethereum)"""
        try:
            token_address = Web3.to_checksum_address(token_address)
            user_address = Web3.to_checksum_address(user_address)

            # Burn en Polygon
            token_contract = self.w3_polygon.eth.contract(address=token_address, abi=ERC20_ABI)
            burn_tx = token_contract.functions.transfer(
                '0x0000000000000000000000000000000000000000', amount  # Burn address
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3_polygon.eth.gas_price,
                'nonce': self.w3_polygon.eth.get_transaction_count(self.account.address),
            })
            signed_burn = self.account.sign_transaction(burn_tx)
            burn_hash = self.w3_polygon.eth.send_raw_transaction(signed_burn.rawTransaction)
            receipt = self.w3_polygon.eth.wait_for_transaction_receipt(burn_hash)
            self.logger.info(f"Burn completado: {burn_hash.hex()}")

            # Exit en Ethereum (usando proof, simplificado)
            # En producción, necesitar proof de burn
            exit_tx = self.root_chain_contract.functions.exit(b'proof_data').build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3_eth.eth.gas_price,
                'nonce': self.w3_eth.eth.get_transaction_count(self.account.address),
            })
            signed_exit = self.account.sign_transaction(exit_tx)
            exit_hash = self.w3_eth.eth.send_raw_transaction(signed_exit.rawTransaction)
            self.logger.info(f"Exit iniciado: {exit_hash.hex()}")
            return exit_hash.hex()
        except Exception as e:
            self.logger.error(f"Error en withdraw_erc20: {e}")
            raise

    def check_transaction_status(self, tx_hash: str, chain: str = 'eth') -> Dict[str, Any]:
        """Verifica el estado de una transacción"""
        try:
            w3 = self.w3_eth if chain == 'eth' else self.w3_polygon
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return {
                    'status': 'success' if receipt['status'] == 1 else 'failed',
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'logs': len(receipt['logs'])
                }
            else:
                return {'status': 'pending'}
        except TransactionNotFound:
            return {'status': 'not_found'}
        except Exception as e:
            self.logger.error(f"Error checking transaction: {e}")
            return {'status': 'error', 'message': str(e)}
