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

# ABI simplificada para AnySwapV4Router (Multichain/Anyswap)
ANYSWAP_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "toChainID", "type": "uint256"}
        ],
        "name": "anySwapOut",
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
    }
]

class CrossChainBridge:
    def __init__(self, source_rpc: str, dest_rpc: str, private_key: str, router_address: str, source_chain_id: int, dest_chain_id: int):
        self.legacy_message = (
            "Bridge EVM legacy. EmpoorioChain usa bridge nativo DracmaSToken."
        )
        raise NotImplementedError(self.legacy_message)
        self.logger = logging.getLogger(__name__)
        self.w3_source = Web3(Web3.HTTPProvider(source_rpc))
        self.w3_dest = Web3(Web3.HTTPProvider(dest_rpc))
        self.account = Account.from_key(private_key)
        self.source_chain_id = source_chain_id
        self.dest_chain_id = dest_chain_id

        if not self.w3_source.is_connected():
            raise ConnectionError("No se pudo conectar a RPC de cadena origen")
        if not self.w3_dest.is_connected():
            raise ConnectionError("No se pudo conectar a RPC de cadena destino")

        self.router_address = Web3.to_checksum_address(router_address)
        self.router_contract = self.w3_source.eth.contract(
            address=self.router_address, abi=ANYSWAP_ROUTER_ABI
        )

    def deposit(self, token_address: str, amount: int, to_address: str) -> str:
        """Deposita tokens desde cadena origen a destino usando AnySwapOut"""
        try:
            token_address = Web3.to_checksum_address(token_address)
            to_address = Web3.to_checksum_address(to_address)

            # Aprobar tokens al router
            token_contract = self.w3_source.eth.contract(address=token_address, abi=ERC20_ABI)
            approve_tx = token_contract.functions.approve(
                self.router_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3_source.eth.gas_price,
                'nonce': self.w3_source.eth.get_transaction_count(self.account.address),
            })
            signed_approve = self.account.sign_transaction(approve_tx)
            approve_hash = self.w3_source.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3_source.eth.wait_for_transaction_receipt(approve_hash)
            self.logger.info(f"Aprobación completada: {approve_hash.hex()}")

            # AnySwapOut
            swap_tx = self.router_contract.functions.anySwapOut(
                token_address, to_address, amount, self.dest_chain_id
            ).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3_source.eth.gas_price,
                'nonce': self.w3_source.eth.get_transaction_count(self.account.address),
            })
            signed_swap = self.account.sign_transaction(swap_tx)
            swap_hash = self.w3_source.eth.send_raw_transaction(signed_swap.rawTransaction)
            self.logger.info(f"Depósito cross-chain iniciado: {swap_hash.hex()}")
            return swap_hash.hex()
        except Exception as e:
            self.logger.error(f"Error en deposit: {e}")
            raise

    def withdraw(self, token_address: str, amount: int, to_address: str) -> str:
        """Retira tokens desde cadena destino a origen (swap de vuelta)"""
        # Similar a deposit, pero desde dest a source
        try:
            # Cambiar a w3_dest para withdraw
            router_contract_dest = self.w3_dest.eth.contract(
                address=self.router_address, abi=ANYSWAP_ROUTER_ABI
            )
            token_contract = self.w3_dest.eth.contract(address=token_address, abi=ERC20_ABI)
            approve_tx = token_contract.functions.approve(
                self.router_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3_dest.eth.gas_price,
                'nonce': self.w3_dest.eth.get_transaction_count(self.account.address),
            })
            signed_approve = self.account.sign_transaction(approve_tx)
            approve_hash = self.w3_dest.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3_dest.eth.wait_for_transaction_receipt(approve_hash)
            self.logger.info(f"Aprobación en destino completada: {approve_hash.hex()}")

            swap_tx = router_contract_dest.functions.anySwapOut(
                token_address, to_address, amount, self.source_chain_id
            ).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3_dest.eth.gas_price,
                'nonce': self.w3_dest.eth.get_transaction_count(self.account.address),
            })
            signed_swap = self.account.sign_transaction(swap_tx)
            swap_hash = self.w3_dest.eth.send_raw_transaction(signed_swap.rawTransaction)
            self.logger.info(f"Retiro cross-chain iniciado: {swap_hash.hex()}")
            return swap_hash.hex()
        except Exception as e:
            self.logger.error(f"Error en withdraw: {e}")
            raise

    def check_transaction_status(self, tx_hash: str, chain: str = 'source') -> Dict[str, Any]:
        """Verifica el estado de una transacción"""
        try:
            w3 = self.w3_source if chain == 'source' else self.w3_dest
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
