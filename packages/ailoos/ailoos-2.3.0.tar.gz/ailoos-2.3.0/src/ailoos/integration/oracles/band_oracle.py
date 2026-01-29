"""
Band Protocol Oracle Integration for AILOOS.
Provides access to Band Protocol cross-chain price feeds and data.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.exceptions import ContractLogicError, BadFunctionCallOutput
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    Contract = None
    ContractLogicError = BadFunctionCallOutput = Exception

logger = logging.getLogger(__name__)


class BandOracleError(Exception):
    """Base exception for Band oracle errors."""
    pass


class BandOracle:
    """
    Band Protocol Oracle integration class.
    Supports cross-chain price feeds and aggregated data.
    """
    LEGACY_MESSAGE = (
        "Oraculos EVM legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Mainnet contract addresses
    STD_REFERENCE_BASIC = "0xDA7a001b254CD22e46d3eAB04d937489c93174C3"

    # Supported symbols for price feeds
    SUPPORTED_SYMBOLS = [
        "BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "DOGE", "AVAX", "LUNA", "MATIC",
        "LINK", "UNI", "AAVE", "SUSHI", "COMP", "MKR", "YFI", "BAL", "REN", "KNC",
        "ZRX", "BAT", "OMG", "LRC", "REP", "GNT", "STORJ", "ANT", "WAVES", "LSK"
    ]

    # Simplified ABI for StdReferenceBasic contract
    STD_REFERENCE_ABI = [
        {
            "inputs": [{"internalType": "string[]", "name": "_symbols", "type": "string[]"}],
            "name": "getReferenceData",
            "outputs": [
                {
                    "components": [
                        {"internalType": "uint256", "name": "rate", "type": "uint256"},
                        {"internalType": "uint256", "name": "lastUpdatedBase", "type": "uint256"},
                        {"internalType": "uint256", "name": "lastUpdatedQuote", "type": "uint256"}
                    ],
                    "internalType": "struct IStdReference.ReferenceData[]",
                    "name": "", "type": "tuple[]"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "string", "name": "_base", "type": "string"}, {"internalType": "string", "name": "_quote", "type": "string"}],
            "name": "getReferenceData",
            "outputs": [
                {
                    "components": [
                        {"internalType": "uint256", "name": "rate", "type": "uint256"},
                        {"internalType": "uint256", "name": "lastUpdatedBase", "type": "uint256"},
                        {"internalType": "uint256", "name": "lastUpdatedQuote", "type": "uint256"}
                    ],
                    "internalType": "struct IStdReference.ReferenceData",
                    "name": "", "type": "tuple"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, web3_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 chain_id: int = 1):
        """
        Initialize Band Oracle.

        Args:
            web3_provider: Web3 provider URL
            chain_id: Blockchain chain ID (1 for Ethereum mainnet)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        if not self.web3.is_connected():
            raise BandOracleError("Failed to connect to Web3 provider")

        self.chain_id = chain_id

        # Cache for contract
        self._contract: Optional[Contract] = None

        logger.info(f"Band Oracle initialized on chain {chain_id}")

    def _get_contract(self) -> Contract:
        """Get or create contract instance."""
        if self._contract is None:
            self._contract = self.web3.eth.contract(address=self.STD_REFERENCE_BASIC, abi=self.STD_REFERENCE_ABI)
        return self._contract

    def get_price(self, base: str, quote: str = "USD") -> Dict[str, Any]:
        """
        Get price data from Band Protocol.

        Args:
            base: Base currency symbol (e.g., "ETH")
            quote: Quote currency symbol (default: "USD")

        Returns:
            Dict with price data

        Raises:
            BandOracleError: If symbols not supported or query fails
        """
        if base.upper() not in self.SUPPORTED_SYMBOLS:
            raise BandOracleError(f"Unsupported base symbol: {base}")

        try:
            contract = self._get_contract()

            # Get reference data
            reference_data = contract.functions.getReferenceData(base.upper(), quote.upper()).call()

            rate, last_updated_base, last_updated_quote = reference_data

            # Convert rate (Band uses 18 decimals for USD pairs)
            price = rate / (10 ** 18)

            result = {
                "pair": f"{base}/{quote}",
                "price": price,
                "rate": rate,
                "last_updated_base": last_updated_base,
                "last_updated_quote": last_updated_quote,
                "source": "Band Protocol"
            }

            logger.info(f"Retrieved price for {base}/{quote}: {price}")
            return result

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get price for {base}/{quote}: {e}")
            raise BandOracleError(f"Price query failed for {base}/{quote}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting price for {base}/{quote}: {e}")
            raise BandOracleError(f"Unexpected error: {str(e)}")

    def get_multiple_prices(self, pairs: List[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple price data points from Band Protocol.

        Args:
            pairs: List of (base, quote) tuples

        Returns:
            Dict mapping pair strings to price data

        Raises:
            BandOracleError: If query fails
        """
        try:
            contract = self._get_contract()

            # Prepare symbols for batch query
            symbols = [f"{base.upper()}{quote.upper()}" for base, quote in pairs]

            # Get reference data for all pairs
            reference_data_list = contract.functions.getReferenceData(symbols).call()

            results = {}
            for i, (base, quote) in enumerate(pairs):
                if i < len(reference_data_list):
                    rate, last_updated_base, last_updated_quote = reference_data_list[i]

                    price = rate / (10 ** 18)

                    pair_key = f"{base}/{quote}"
                    results[pair_key] = {
                        "pair": pair_key,
                        "price": price,
                        "rate": rate,
                        "last_updated_base": last_updated_base,
                        "last_updated_quote": last_updated_quote,
                        "source": "Band Protocol"
                    }

            logger.info(f"Retrieved {len(results)} price pairs from Band Protocol")
            return results

        except (ContractLogicError, BadFunctionCallOutput) as e:
            logger.error(f"Failed to get multiple prices: {e}")
            raise BandOracleError(f"Multiple price query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting multiple prices: {e}")
            raise BandOracleError(f"Unexpected error: {str(e)}")

    def get_cross_chain_data(self, symbol: str, chains: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get cross-chain aggregated data for a symbol.

        Args:
            symbol: Asset symbol
            chains: List of chains to query (optional, uses all available)

        Returns:
            Dict with aggregated cross-chain data

        Raises:
            BandOracleError: If symbol not supported or query fails
        """
        # Band Protocol aggregates data from multiple sources/chains
        # For simplicity, this returns the standard price data
        # In a full implementation, you might query multiple chain-specific contracts

        try:
            price_data = self.get_price(symbol, "USD")

            # Add cross-chain metadata
            cross_chain_info = {
                "symbol": symbol,
                "aggregated_price": price_data["price"],
                "supported_chains": ["Ethereum", "BSC", "Polygon", "Avalanche", "Fantom"],  # Band supported chains
                "data_sources": ["Binance", "Coinbase", "Kraken", "OKX", "Huobi"],  # Band data sources
                "last_updated": max(price_data["last_updated_base"], price_data["last_updated_quote"]),
                "confidence_interval": 0.02,  # Example confidence interval
                "source": "Band Protocol Cross-Chain"
            }

            logger.info(f"Retrieved cross-chain data for {symbol}")
            return cross_chain_info

        except BandOracleError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting cross-chain data for {symbol}: {e}")
            raise BandOracleError(f"Unexpected error: {str(e)}")

    def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported symbols.

        Returns:
            List of supported symbols
        """
        return self.SUPPORTED_SYMBOLS.copy()
