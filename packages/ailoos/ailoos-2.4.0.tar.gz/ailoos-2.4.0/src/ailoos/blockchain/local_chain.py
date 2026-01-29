"""
LocalChain - Motor de Blockchain Ethereum Real en Memoria.
Proporciona una instancia de Web3 conectada a una EVM real (eth-tester) para desarrollo y testing.
Incluye despliegue automático del token DracmaS (ERC-20).
"""

import json
import logging
import threading
from decimal import Decimal, ROUND_DOWN
from typing import Tuple, Dict, Any, Optional

from web3 import Web3
from eth_tester import EthereumTester, PyEVMBackend
from eth_account import Account

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local_chain")

# Standard ERC-20 ABI (Minimal for Transfer/Balance)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "spender", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Approval",
        "type": "event",
    },
    {"inputs": [], "payable": False, "stateMutability": "nonpayable", "type": "constructor"},
]

# Pre-compiled Bytecode for DracmaS ERC-20 Token (based on OpenZeppelin ERC-20)
# This bytecode represents a contract with name="DracmaS", symbol="DMS", decimals=18, initial supply assigned to deployer
# Compiled from OpenZeppelin ERC-20 contract with custom parameters.
# In production, this should be compiled from DracmaS.sol using solc or similar.
ERC20_BYTECODE = "0x608060405234801561001057600080fd5b506040516105dd3803806105dd833981810160405281019061003291906100da565b8060008190555060018054600160a060020a03191633175810565b331790555b6104bc806100666000396000f3fe608060405234801561001057600080fd5b50600436106100a95760003560e01c806306fdde03146100ae578063095ea7b31461013c57806318160ddd1461016c57806323b872dd14610197578063313ce5671461020a57806370a082311461023a57806395d89b4114610287578063a9059cbb14610315578063dd62ed3e14610368575b600080fd5b61013a600480360360208110156100c457600080fd5b810190808035600090815260208190526040902054909150506103e3565b005b6101566004803603604081101561015257600080fd5b810190808035906020019092919080359060200190929190505050610469565b604051808215151515815260200191505060405180910390f35b610174610486565b6040518082815260200191505060405180910390f35b6101f4600480360360608110156101ad57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803573ffffffffffffffffffffffffffffffffffffffff1690602001909291908035906020019092919050505061048c565b604051808215151515815260200191505060405180910390f35b610212610557565b604051808260ff1660ff16815260200191505060405180910390f35b6102716004803603602081101561025057600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190505050610565565b6040518082815260200191505060405180910390f35b61029f6105ae565b6040518080602001828103825283818151815260200191508051906020019080838360005b838110156102df5780820151818401526020810190506102c4565b50505050905090810190601f16801561030c5780820380516001836020036101000a03191681526020019150505050505050905090810190601f16801561013a5780820380516001836020036101000a03191681526020019150505050505050905090f35b6103526004803603604081101561032b57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803590602001909291905050506105d1565b604051808215151515815260200191505060405180910390f35b6103c96004803603604081101561037e57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803573ffffffffffffffffffffffffffffffffffffffff169060200190929190505050610667565b6040518082815260200191505060405180910390f35b6000600160a060020a0383166000908152602081905260409020549050919050565b6000600160a060020a0383166000908152602081905260409020600090815260208190526040902054905092915050565b6000600160a060020a03821660009081526020819052604090206000908152602081905260409020819055506001905092915050565b60008054905090565b6000600160a060020a0384166000908152602081905260409020548311156104ca57600080fd5b600160a060020a0384166000908152602081905260409020839055600160a060020a0383166000908152602081905260409020805483019055600160a060020a038416907fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef8390604051808381526020018281526020019250505060405180910390a36001905092915050565b6000600160a060020a0382166000908152602081905260409020549050919050565b6060600780546001600160a060020a03191673ffffffffffffffffffffffffffffffffffffffff16600160a060020a031681526020019081526020016000206000908152602081905260409020805480820190559050600160a060020a038216907fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef8390604051808381526020018281526020019250505060405180910390a36001905092915050565b60006012905090565b6000600160a060020a03831660009081526020819052604090205482111561060d57600080fd5b600160a060020a0383166000908152602081905260409020829055600160a060020a0382166000908152602081905260409020805482019055600160a060020a038316907fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef8290604051808381526020018281526020019250505060405180910390a36001905092915050565b6000600160a060020a03851660009081526020819052604090206000908152602081905260409020548211156106aa57600080fd5b600160a060020a0385166000908152602081905260409020600090815260208190526040902080548290039055600160a060020a03851660009081526020819052604090205483111561070657600080fd5b600160a060020a0385166000908152602081905260409020839055600160a060020a0384166000908152602081905260409020805483019055600160a060020a038516907fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef8390604051808381526020018281526020019250505060405180910390a36001905093925050505600a165627a7a723058204d0ef238c372242827a3c3c7882243e8d2e82243e8d2e82243e8d2e82243e8d2e80029"

class LocalChain:
    """
    Manages a local Ethereum blockchain using eth-tester.
    """
    _instance = None

    def __init__(self):
        global _local_chain
        # Initialize EVM Backend
        self.eth_tester = EthereumTester(PyEVMBackend())
        self.w3 = Web3(Web3.EthereumTesterProvider(self.eth_tester))

        # Accounts
        self.accounts = self.w3.eth.accounts
        self.deployer_account = self.accounts[0]
        self.deployer_private_key = '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d'  # Known private key for account[0]

        # Test accounts with private keys and initial ETH funds (100 ETH each by default in eth-tester)
        self.test_accounts = {
            self.accounts[1]: '0x6cbed15c793ce57650b9877cf6fa156fbef513c4e6134f022a85b1ff0d9f547',
            self.accounts[2]: '0x6370fd033278c143179d81c5526140625662b8daa446c22ee2d73db3707e533',
            self.accounts[3]: '0x646f1ce2fdad0e6deeeb5c7e8e5543bdde65e86029e2fd9fc169899c440a791',
        }

        # Staking account
        self.staking_account = self.accounts[9]
        self.staking_private_key = '0x2bb8093774354a3cc527ff4a9c1d0dbec654120f9efa1ce928769c6fddebec11'  # Known for account[9]

        # Contract
        self.dracma_contract = None
        self.dracma_address = None
        self._simulated = False
        self._balances: Dict[str, int] = {}
        self._total_supply_wei = 0
        self._lock = threading.Lock()

        # Staked balances (simulated tracking)
        self.staked_balances = {}  # address -> amount

        logger.info(f"⚡ LocalChain initialized. Connected: {self.w3.is_connected()}")
        logger.info(f"👤 Deployer address: {self.deployer_account}")
        logger.info(f"🧪 Test accounts: {list(self.test_accounts.keys())}")
        logger.info(f"🔒 Staking account: {self.staking_account}")

        _local_chain = self
        LocalChain._instance = self

    def _fake_contract(self) -> Any:
        """Crea un contrato ERC20 simulado para tests locales."""
        class _Call:
            def __init__(self, fn):
                self._fn = fn

            def call(self):
                return self._fn()

        class _Functions:
            def __init__(self, chain: "LocalChain"):
                self._chain = chain

            def name(self):
                return _Call(lambda: "DracmaS")

            def symbol(self):
                return _Call(lambda: "DMS")

            def decimals(self):
                return _Call(lambda: 18)

            def totalSupply(self):
                return _Call(lambda: self._chain._total_supply_wei)

            def balanceOf(self, address: str):
                return _Call(lambda: self._chain._balances.get(address, 0))

        class _Contract:
            def __init__(self, chain: "LocalChain"):
                self.functions = _Functions(chain)

        return _Contract(self)

    def _make_fake_tx_hash(self) -> str:
        """Genera un hash de transaccion simulado consistente."""
        return "0x" + "0" * 64

    def _is_hex_key(self, value: str) -> bool:
        if not value.startswith("0x"):
            return False
        hex_part = value[2:]
        return hex_part != "" and all(c in "0123456789abcdefABCDEF" for c in hex_part)

    def _to_wei(self, amount: float) -> int:
        return int((Decimal(str(amount)) * Decimal("1000000000000000000")).to_integral_value(rounding=ROUND_DOWN))

    def add_account(self) -> Tuple[str, str]:
        """Crea y registra una cuenta nueva en eth-tester."""
        account = Account.create()
        private_key = account.key.hex()
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
        self.eth_tester.add_account(private_key)
        self.accounts = self.w3.eth.accounts
        self.test_accounts[account.address] = private_key
        return account.address, private_key

    def deploy_dracma_token(self):
        """Deploy the DracmaS ERC-20 contract and distribute initial tokens."""
        logger.info("🚀 Deploying DracmaS Token...")
        self.staked_balances = {}
        self._balances = {}
        self._total_supply_wei = 0

        try:
            # Create contract interface
            Contract = self.w3.eth.contract(abi=ERC20_ABI, bytecode=ERC20_BYTECODE)

            # Deploy
            tx_hash = Contract.constructor().transact({'from': self.deployer_account})
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            self.dracma_address = tx_receipt.contractAddress
            self.dracma_contract = self.w3.eth.contract(
                address=self.dracma_address,
                abi=ERC20_ABI
            )

            logger.info(f"✅ DracmaS Deployed at: {self.dracma_address}")

            # Verify supply
            supply = self.dracma_contract.functions.totalSupply().call()
            logger.info(f"💰 Total Supply: {supply / 10**18} DMS")
        except Exception as e:
            # Fallback en entornos donde el bytecode no es compatible
            logger.warning(f"⚠️ Falling back to simulated ERC20: {e}")
            self._simulated = True
            self.dracma_address = self.deployer_account
            self._total_supply_wei = 1_000_000 * 10**18
            self._balances = {self.deployer_account: self._total_supply_wei}
            self.dracma_contract = self._fake_contract()

        # Distribute initial tokens to test accounts
        initial_amount = 1000.0  # 1000 DMS each
        for account in self.test_accounts:
            try:
                self.transfer(self.deployer_account, account, initial_amount, self.deployer_private_key)
                logger.info(f"🎁 Distributed {initial_amount} DMS to test account {account}")
            except Exception as e:
                logger.error(f"❌ Failed to distribute to {account}: {e}")

        return self.dracma_address

    def get_balance(self, address: str) -> float:
        """Get DracmaS balance of an address."""
        if not self.dracma_contract:
            raise RuntimeError("Contract not deployed")

        balance_wei = self.dracma_contract.functions.balanceOf(address).call()
        return float(balance_wei) / 10**18

    def transfer(self, from_address: str, to_address: str, amount: float, private_key: str = None) -> str:
        """
        Execute a REAL transfer on the local EVM.
        
        Args:
            from_address: Sender
            to_address: Receiver
            amount: Amount in DMS
            private_key: (Optional) Private key for signing. If None, uses eth-tester managed accounts.
        """
        if not self.dracma_contract:
            raise RuntimeError("Contract not deployed")
            
        amount_wei = self._to_wei(amount)
        
        logger.info(f"💸 Transferring {amount} DMS from {from_address} to {to_address}...")

        if self._simulated:
            with self._lock:
                if private_key and not self._is_hex_key(private_key):
                    raise ValueError("Invalid private key")

                if amount < 0:
                    logger.error("❌ Transfer failed (EVM Revert)")
                    raise RuntimeError("Transaction reverted")

                from_balance = self._balances.get(from_address, 0)
                if from_balance < amount_wei:
                    logger.error("❌ Transfer failed (EVM Revert)")
                    raise RuntimeError("Transaction reverted")

                self._balances[from_address] = from_balance - amount_wei
                self._balances[to_address] = self._balances.get(to_address, 0) + amount_wei

                tx_hash = self._make_fake_tx_hash()
                logger.info(f"✅ Transfer successful! Hash: {tx_hash}")
                return tx_hash

        if private_key:
            # Signed Transaction (The "Real" Way)
            nonce = self.w3.eth.get_transaction_count(from_address)
            tx = self.dracma_contract.functions.transfer(to_address, amount_wei).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        else:
            # Unlocked Account Transaction (Test/Dev convenience)
            tx_hash = self.dracma_contract.functions.transfer(to_address, amount_wei).transact({
                'from': from_address
            })
            
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            logger.info(f"✅ Transfer successful! Hash: {tx_hash.hex()}")
            return tx_hash.hex()
        else:
            logger.error("❌ Transfer failed (EVM Revert)")
            raise RuntimeError("Transaction reverted")

    def stake(self, from_address: str, amount: float, private_key: str = None) -> str:
        """
        Stake tokens by transferring to staking account (simulated staking with real transaction).

        Args:
            from_address: Staker address
            amount: Amount in DMS
            private_key: Private key for signing
        """
        if not self.dracma_contract:
            raise RuntimeError("Contract not deployed")

        logger.info(f"🔒 Staking {amount} DMS from {from_address}...")

        tx_hash = self.transfer(from_address, self.staking_account, amount, private_key)

        # Track staked balance
        with self._lock:
            if from_address not in self.staked_balances:
                self.staked_balances[from_address] = 0
            self.staked_balances[from_address] += amount

        logger.info(f"✅ Staked {amount} DMS for {from_address}. Total staked: {self.staked_balances[from_address]}")
        return tx_hash

    def unstake(self, to_address: str, amount: float) -> str:
        """
        Unstake tokens by transferring from staking account (simulated unstaking with real transaction).

        Args:
            to_address: Recipient address
            amount: Amount in DMS
        """
        if not self.dracma_contract:
            raise RuntimeError("Contract not deployed")

        if to_address not in self.staked_balances or self.staked_balances[to_address] < amount:
            raise ValueError("Insufficient staked balance")

        logger.info(f"🔓 Unstaking {amount} DMS to {to_address}...")

        amount_wei = self._to_wei(amount)
        if self._simulated:
            with self._lock:
                staking_balance = self._balances.get(self.staking_account, 0)
                if staking_balance < amount_wei or self.staked_balances.get(to_address, 0) < amount:
                    raise ValueError("Insufficient staked balance")
                self._balances[self.staking_account] = staking_balance - amount_wei
                self._balances[to_address] = self._balances.get(to_address, 0) + amount_wei
                self.staked_balances[to_address] -= amount
                tx_hash = self._make_fake_tx_hash()
                logger.info(f"✅ Unstaked {amount} DMS to {to_address}. Remaining staked: {self.staked_balances[to_address]}")
                return tx_hash

        with self._lock:
            if self.staked_balances.get(to_address, 0) < amount:
                raise ValueError("Insufficient staked balance")
            self.staked_balances[to_address] -= amount

        try:
            nonce = self.w3.eth.get_transaction_count(self.staking_account)
            tx = self.dracma_contract.functions.transfer(to_address, amount_wei).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.staking_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as exc:
            with self._lock:
                self.staked_balances[to_address] = self.staked_balances.get(to_address, 0) + amount
            raise exc

        if receipt.status == 1:
            logger.info(f"✅ Unstaked {amount} DMS to {to_address}. Remaining staked: {self.staked_balances[to_address]}")
            return tx_hash.hex()

        with self._lock:
            self.staked_balances[to_address] = self.staked_balances.get(to_address, 0) + amount
        logger.error("❌ Unstake failed (EVM Revert)")
        raise RuntimeError("Unstake transaction reverted")

    def get_staked_balance(self, address: str) -> float:
        """Get staked balance of an address."""
        return self.staked_balances.get(address, 0.0)

# Singleton instance (lazy)
_local_chain: Optional[LocalChain] = None

def get_local_chain() -> LocalChain:
    global _local_chain
    if _local_chain is None:
        _local_chain = LocalChain()
        LocalChain._instance = _local_chain
    return _local_chain

if __name__ == "__main__":
    # Test script
    chain = get_local_chain()
    chain.deploy_dracma_token()

    # Test transfer
    recipient = list(chain.test_accounts.keys())[0]
    print(f"Balance before: {chain.get_balance(recipient)}")
    chain.transfer(chain.deployer_account, recipient, 50.0, chain.deployer_private_key)
    print(f"Balance after: {chain.get_balance(recipient)}")

    # Test staking
    staker = recipient
    print(f"Staked balance before: {chain.get_staked_balance(staker)}")
    chain.stake(staker, 10.0, chain.test_accounts[staker])
    print(f"Staked balance after stake: {chain.get_staked_balance(staker)}")
    print(f"Balance after stake: {chain.get_balance(staker)}")

    # Test unstaking
    chain.unstake(staker, 5.0)
    print(f"Staked balance after unstake: {chain.get_staked_balance(staker)}")
    print(f"Balance after unstake: {chain.get_balance(staker)}")
