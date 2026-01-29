"""
Chainlink Oracle Integration for AILOOS.
Provides access to Chainlink price feeds, external data, and VRF randomness.
"""

import logging
from typing import Dict, Any, Optional, Tuple
import time

try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.exceptions import ContractLogicError, BadFunctionCallOutput
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    Contract = None
    ContractLogicError = BadFunctionCallOutput = Exception

logger = logging.getLogger(__name__)


class ChainlinkOracleError(Exception):
    """Base exception for Chainlink oracle errors."""
    pass


class ChainlinkOracle:
    """
    Chainlink Oracle integration class.
    Supports price feeds, external data queries, and VRF randomness.
    """
    LEGACY_MESSAGE = (
        "Oraculos EVM legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Mainnet contract addresses
    VRF_COORDINATOR_V2 = "0x271682DEB8C4E0901D1a1550aD2e64D568E69909"
    LINK_TOKEN = "0x514910771AF9Ca656af840dff83E8264EcF986CA"

    # Common price feed addresses (ETH/USD, BTC/USD, etc.)
    PRICE_FEEDS = {
        "ETH/USD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
        "BTC/USD": "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
        "LINK/USD": "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
        "USDC/USD": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6F",
        "DAI/USD": "0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9",
    }

    # Simplified ABIs (in production, use full ABIs)
    PRICE_FEED_ABI = [
        {
            "inputs": [],
            "name": "latestRoundData",
            "outputs": [
                {"internalType": "uint80", "name": "roundId", "type": "uint80"},
                {"internalType": "int256", "name": "answer", "type": "int256"},
                {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
                {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    VRF_COORDINATOR_ABI = [
        {
            "inputs": [
                {"internalType": "uint64", "name": "subId", "type": "uint64"},
                {"internalType": "bytes32", "name": "keyHash", "type": "bytes32"},
                {"internalType": "uint32", "name": "callbackGasLimit", "type": "uint32"},
                {"internalType": "uint16", "name": "requestConfirmations", "type": "uint16"},
                {"internalType": "uint32", "name": "numWords", "type": "uint32"}
            ],
            "name": "requestRandomWords",
            "outputs": [{"internalType": "uint256", "name": "requestId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "requestId", "type": "uint256"}],
            "name": "getRequestStatus",
            "outputs": [
                {"internalType": "bool", "name": "fulfilled", "type": "bool"},
                {"internalType": "bool", "name": "exists", "type": "bool"},
                {"internalType": "uint256[]", "name": "randomWords", "type": "uint256[]"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, web3_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 chain_id: int = 1, private_key: Optional[str] = None):
        """
        Initialize Chainlink Oracle.

        Args:
            web3_provider: Web3 provider URL
            chain_id: Blockchain chain ID (1 for Ethereum mainnet)
            private_key: Private key for transactions (optional)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        if not self.web3.is_connected():
            raise ChainlinkOracleError("Failed to connect to Web3 provider")

        self.chain_id = chain_id
        self.account = None
        if private_key:
            self.account = self.web3.eth.account.from_key(private_key)

        # Cache for contracts
        self._contracts: Dict[str, Contract] = {}

        logger.info(f"Chainlink Oracle initialized on chain {chain_id}")

    def _get_contract(self, address: str, abi: list) -> Contract:
        """Get or create contract instance."""
        if address not in self._contracts:
            self._contracts[address] = self.web3.eth.contract(address=address, abi=abi)
        return self._contracts[address]

    def get_price(self, pair: str) -> Dict[str, Any]:
        """
        Get latest price data from Chainlink price feed.

        Args:
            pair: Price pair (e.g., "ETH/USD")

        Returns:
            Dict with price data

        Raises:
            ChainlinkOracleError: If pair not supported or query fails
        """
        if pair not in self.PRICE_FEEDS:
            raise ChainlinkOracleError(f"Unsupported price pair: {pair}")

        try:
            contract = self._get_contract(self.PRICE_FEEDS[pair], self.PRICE_FEED_ABI)

            # Get latest round data
            round_data = contract.functions.latestRoundData().call()
            decimals = contract.functions.decimals().call()

            round_id, answer, started_at, updated_at, answered_in_round = round_data

            # Convert to human readable price
            price = answer / (10 ** decimals)

            result = {
                "pair": pair,
                "price": price,
                "round_id": round_id,
                "updated_at": updated_at,
                "decimals": decimals,
                "raw_answer": answer
            }

            logger.info(f"Retrieved price for {pair}: {price}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get price for {pair}: {e}")
            raise ChainlinkOracleError(f"Price query failed for {pair}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting price for {pair}: {e}")
            raise ChainlinkOracleError(f"Unexpected error: {str(e)}")

    def get_external_data(self, feed_address: str) -> Dict[str, Any]:
        """
        Get external data from a Chainlink data feed.

        Args:
            feed_address: Contract address of the data feed

        Returns:
            Dict with data

        Raises:
            ChainlinkOracleError: If query fails
        """
        try:
            contract = self._get_contract(feed_address, self.PRICE_FEED_ABI)

            round_data = contract.functions.latestRoundData().call()
            decimals = contract.functions.decimals().call()

            round_id, answer, started_at, updated_at, answered_in_round = round_data

            result = {
                "feed_address": feed_address,
                "value": answer / (10 ** decimals),
                "round_id": round_id,
                "updated_at": updated_at,
                "decimals": decimals,
                "raw_answer": answer
            }

            logger.info(f"Retrieved external data from {feed_address}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get external data from {feed_address}: {e}")
            raise ChainlinkOracleError(f"External data query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting external data: {e}")
            raise ChainlinkOracleError(f"Unexpected error: {str(e)}")

    def request_randomness(self, subscription_id: int, key_hash: str,
                          callback_gas_limit: int = 100000,
                          request_confirmations: int = 3,
                          num_words: int = 1) -> int:
        """
        Request random words using Chainlink VRF v2.

        Args:
            subscription_id: VRF subscription ID
            key_hash: Key hash for the VRF
            callback_gas_limit: Gas limit for callback
            request_confirmations: Number of confirmations required
            num_words: Number of random words to request

        Returns:
            Request ID

        Raises:
            ChainlinkOracleError: If request fails
        """
        if not self.account:
            raise ChainlinkOracleError("Private key required for VRF requests")

        try:
            contract = self._get_contract(self.VRF_COORDINATOR_V2, self.VRF_COORDINATOR_ABI)

            # Build transaction
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            gas_price = self.web3.eth.gas_price

            txn = contract.functions.requestRandomWords(
                subscription_id,
                key_hash,
                callback_gas_limit,
                request_confirmations,
                num_words
            ).build_transaction({
                'chainId': self.chain_id,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'from': self.account.address
            })

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(txn, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            # Extract request ID from logs (simplified - in practice, parse logs properly)
            request_id = contract.functions.getRequestStatus(0).call()[2][0] if receipt.status == 1 else None

            if request_id:
                logger.info(f"VRF randomness requested, request ID: {request_id}")
                return request_id
            else:
                raise ChainlinkOracleError("Failed to extract request ID from transaction")

        except Exception as e:
            logger.error(f"Failed to request VRF randomness: {e}")
            raise ChainlinkOracleError(f"VRF request failed: {str(e)}")

    def get_randomness(self, request_id: int, max_attempts: int = 10) -> Optional[list]:
        """
        Get random words for a VRF request.

        Args:
            request_id: VRF request ID
            max_attempts: Maximum polling attempts

        Returns:
            List of random words or None if not ready

        Raises:
            ChainlinkOracleError: If query fails
        """
        try:
            contract = self._get_contract(self.VRF_COORDINATOR_V2, self.VRF_COORDINATOR_ABI)

            for attempt in range(max_attempts):
                fulfilled, exists, random_words = contract.functions.getRequestStatus(request_id).call()

                if fulfilled and exists:
                    logger.info(f"Retrieved VRF randomness for request {request_id}")
                    return random_words

                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait 2 seconds before retrying

            logger.warning(f"VRF request {request_id} not fulfilled after {max_attempts} attempts")
            return None

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get VRF randomness for request {request_id}: {e}")
            raise ChainlinkOracleError(f"VRF query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting VRF randomness: {e}")
            raise ChainlinkOracleError(f"Unexpected error: {str(e)}")
