"""
API3 Oracle Integration for AILOOS.
Provides access to API3 first-party data feeds and oracles.
"""

import logging
from typing import Dict, Any, Optional

try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.exceptions import ContractLogicError, BadFunctionCallOutput
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    Contract = None
    ContractLogicError = BadFunctionCallOutput = Exception

logger = logging.getLogger(__name__)


class API3OracleError(Exception):
    """Base exception for API3 oracle errors."""
    pass


class API3Oracle:
    """
    API3 Oracle integration class.
    Supports first-party data feeds with direct API provider data.
    """
    LEGACY_MESSAGE = (
        "Oraculos EVM legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Mainnet contract addresses
    DAPI_SERVER = "0x9d1b464a3a5f2c6e54b9cc9b4a7c1b7c6f0d5c8"

    # Common data feed IDs (dAPI names as bytes32)
    DATA_FEEDS = {
        "ETH/USD": "0x4554482f55534400000000000000000000000000000000000000000000000000",  # ETH/USD
        "BTC/USD": "0x4254432f55534400000000000000000000000000000000000000000000000000",  # BTC/USD
        "LINK/USD": "0x4c494e4b2f555344000000000000000000000000000000000000000000000000",  # LINK/USD
        "UNI/USD": "0x554e492f55534400000000000000000000000000000000000000000000000000",  # UNI/USD
        "AAVE/USD": "0x414156452f555344000000000000000000000000000000000000000000000000",  # AAVE/USD
    }

    # Simplified ABI for DapiServer contract
    DAPI_SERVER_ABI = [
        {
            "inputs": [{"internalType": "bytes32", "name": "dapiId", "type": "bytes32"}],
            "name": "readDataFeedWithId",
            "outputs": [
                {"internalType": "int224", "name": "value", "type": "int224"},
                {"internalType": "uint32", "name": "timestamp", "type": "uint32"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "dapiId", "type": "bytes32"}],
            "name": "readDataFeedWithDapiName",
            "outputs": [
                {"internalType": "int224", "name": "value", "type": "int224"},
                {"internalType": "uint32", "name": "timestamp", "type": "uint32"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "bytes32", "name": "dapiId", "type": "bytes32"}],
            "name": "dataFeedIdToReaderToWhitelistStatus",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, web3_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 chain_id: int = 1):
        """
        Initialize API3 Oracle.

        Args:
            web3_provider: Web3 provider URL
            chain_id: Blockchain chain ID (1 for Ethereum mainnet)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        if not self.web3.is_connected():
            raise API3OracleError("Failed to connect to Web3 provider")

        self.chain_id = chain_id

        # Cache for contract
        self._contract: Optional[Contract] = None

        logger.info(f"API3 Oracle initialized on chain {chain_id}")

    def _get_contract(self) -> Contract:
        """Get or create contract instance."""
        if self._contract is None:
            self._contract = self.web3.eth.contract(address=self.DAPI_SERVER, abi=self.DAPI_SERVER_ABI)
        return self._contract

    def _dapi_name_to_id(self, dapi_name: str) -> str:
        """Convert dAPI name to bytes32 ID."""
        # Simple conversion - in practice, use proper encoding
        return Web3.to_bytes(text=dapi_name).ljust(32, b'\0').hex()

    def get_price(self, pair: str) -> Dict[str, Any]:
        """
        Get price data from API3 first-party feed.

        Args:
            pair: Price pair (e.g., "ETH/USD")

        Returns:
            Dict with price data

        Raises:
            API3OracleError: If pair not supported or query fails
        """
        if pair not in self.DATA_FEEDS:
            raise API3OracleError(f"Unsupported price pair: {pair}")

        try:
            contract = self._get_contract()
            dapi_id = self.DATA_FEEDS[pair]

            # Read data feed
            value, timestamp = contract.functions.readDataFeedWithId(dapi_id).call()

            # API3 uses 18 decimals for price feeds
            price = value / (10 ** 18)

            result = {
                "pair": pair,
                "price": price,
                "value": value,
                "timestamp": timestamp,
                "dapi_id": dapi_id,
                "source": "API3 First-Party Data"
            }

            logger.info(f"Retrieved price for {pair}: {price}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get price for {pair}: {e}")
            raise API3OracleError(f"Price query failed for {pair}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting price for {pair}: {e}")
            raise API3OracleError(f"Unexpected error: {str(e)}")

    def get_data_feed(self, dapi_name: str) -> Dict[str, Any]:
        """
        Get data from API3 data feed by name.

        Args:
            dapi_name: dAPI name (e.g., "ETH/USD")

        Returns:
            Dict with data feed information

        Raises:
            API3OracleError: If query fails
        """
        try:
            contract = self._get_contract()
            dapi_id = self._dapi_name_to_id(dapi_name)

            # Read data feed with dAPI name
            value, timestamp = contract.functions.readDataFeedWithDapiName(dapi_id).call()

            # Determine decimals based on data type (price feeds use 18)
            decimals = 18  # Assuming price data
            data_value = value / (10 ** decimals)

            result = {
                "dapi_name": dapi_name,
                "dapi_id": dapi_id,
                "value": data_value,
                "raw_value": value,
                "timestamp": timestamp,
                "decimals": decimals,
                "source": "API3 First-Party Data"
            }

            logger.info(f"Retrieved data feed for {dapi_name}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get data feed for {dapi_name}: {e}")
            raise API3OracleError(f"Data feed query failed for {dapi_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting data feed for {dapi_name}: {e}")
            raise API3OracleError(f"Unexpected error: {str(e)}")

    def get_first_party_data(self, data_type: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get first-party data from API3 oracles.

        Args:
            data_type: Type of data to retrieve (e.g., "price", "weather", "sports")
            parameters: Additional parameters for the data request

        Returns:
            Dict with first-party data

        Raises:
            API3OracleError: If data type not supported or query fails
        """
        # API3 provides various first-party data feeds
        # This is a simplified implementation focusing on price data
        # In practice, you would have different contracts/methods for different data types

        if data_type.lower() == "price":
            if not parameters or "pair" not in parameters:
                raise API3OracleError("Price data requires 'pair' parameter")
            return self.get_price(parameters["pair"])

        elif data_type.lower() == "custom_feed":
            if not parameters or "dapi_name" not in parameters:
                raise API3OracleError("Custom feed requires 'dapi_name' parameter")
            return self.get_data_feed(parameters["dapi_name"])

        else:
            raise API3OracleError(f"Unsupported data type: {data_type}")

    def check_data_feed_status(self, dapi_id: str) -> Dict[str, Any]:
        """
        Check the status of a data feed.

        Args:
            dapi_id: Data feed ID

        Returns:
            Dict with status information

        Raises:
            API3OracleError: If query fails
        """
        try:
            contract = self._get_contract()

            # Check whitelist status (simplified)
            whitelist_status = contract.functions.dataFeedIdToReaderToWhitelistStatus(dapi_id).call()

            result = {
                "dapi_id": dapi_id,
                "whitelist_status": whitelist_status,
                "is_active": whitelist_status > 0,
                "source": "API3"
            }

            logger.info(f"Checked status for data feed {dapi_id}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to check status for data feed {dapi_id}: {e}")
            raise API3OracleError(f"Status check failed for {dapi_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking status for {dapi_id}: {e}")
            raise API3OracleError(f"Unexpected error: {str(e)}")

    def get_supported_pairs(self) -> Dict[str, str]:
        """
        Get list of supported price pairs.

        Returns:
            Dict mapping pairs to dAPI IDs
        """
        return self.DATA_FEEDS.copy()
