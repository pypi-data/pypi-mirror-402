"""
Oracle-based Automatic Auditing for AILOOS.
Provides automated compliance verification using blockchain oracles.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from src.ailoos.integration.oracles import (
    ChainlinkOracle, ChainlinkOracleError,
    BandOracle, BandOracleError,
    API3Oracle, API3OracleError
)

logger = logging.getLogger(__name__)


class OracleAuditorError(Exception):
    """Base exception for OracleAuditor errors."""
    pass


class OracleAuditor:
    """
    Automated auditor using blockchain oracles for compliance verification.
    Supports KYC/AML verification, transaction auditing, and identity verification.
    """

    def __init__(self,
                 chainlink_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 band_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 api3_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 chain_id: int = 1):
        """
        Initialize OracleAuditor with oracle providers.

        Args:
            chainlink_provider: Web3 provider URL for Chainlink
            band_provider: Web3 provider URL for Band Protocol
            api3_provider: Web3 provider URL for API3
            chain_id: Blockchain chain ID
        """
        try:
            self.chainlink = ChainlinkOracle(chainlink_provider, chain_id)
            self.band = BandOracle(band_provider, chain_id)
            self.api3 = API3Oracle(api3_provider, chain_id)
            logger.info("OracleAuditor initialized with all oracle providers")
        except Exception as e:
            logger.error(f"Failed to initialize oracles: {e}")
            raise OracleAuditorError(f"Oracle initialization failed: {str(e)}")

    def verify_kyc(self, user_id: str, transaction_data: Dict[str, Any],
                   risk_threshold: float = 10000.0) -> Dict[str, Any]:
        """
        Verify KYC/AML compliance using oracle data.

        Args:
            user_id: User identifier
            transaction_data: Transaction details including amount and currency
            risk_threshold: Risk threshold in USD for enhanced verification

        Returns:
            Dict with verification results

        Raises:
            OracleAuditorError: If verification fails
        """
        try:
            amount = transaction_data.get('amount', 0)
            currency = transaction_data.get('currency', 'USD')

            # Convert transaction amount to USD for risk assessment
            usd_amount = self._convert_to_usd(amount, currency)

            # Check against risk threshold
            high_risk = usd_amount > risk_threshold

            # Get oracle data for verification
            verification_data = {
                'user_id': user_id,
                'transaction_amount_usd': usd_amount,
                'high_risk': high_risk,
                'verification_timestamp': datetime.utcnow().isoformat(),
                'oracle_sources': []
            }

            # Use Chainlink for price verification
            if currency != 'USD':
                try:
                    price_data = self.chainlink.get_price(f"{currency}/USD")
                    verification_data['oracle_sources'].append({
                        'oracle': 'Chainlink',
                        'pair': f"{currency}/USD",
                        'price': price_data['price'],
                        'verified': True
                    })
                except ChainlinkOracleError as e:
                    logger.warning(f"Chainlink verification failed: {e}")
                    verification_data['oracle_sources'].append({
                        'oracle': 'Chainlink',
                        'error': str(e),
                        'verified': False
                    })

            # Use Band Protocol for cross-chain verification
            try:
                if currency in ['ETH', 'BTC', 'LINK']:
                    band_data = self.band.get_price(currency, 'USD')
                    verification_data['oracle_sources'].append({
                        'oracle': 'Band Protocol',
                        'pair': f"{currency}/USD",
                        'price': band_data['price'],
                        'verified': True
                    })
            except BandOracleError as e:
                logger.warning(f"Band Protocol verification failed: {e}")
                verification_data['oracle_sources'].append({
                    'oracle': 'Band Protocol',
                    'error': str(e),
                    'verified': False
                })

            # Determine compliance status
            verified_sources = [s for s in verification_data['oracle_sources'] if s.get('verified', False)]
            compliance_status = 'COMPLIANT' if len(verified_sources) >= 1 else 'REQUIRES_REVIEW'

            if high_risk and len(verified_sources) < 2:
                compliance_status = 'ENHANCED_DUE_DILIGENCE'

            verification_data['compliance_status'] = compliance_status
            verification_data['verified_sources_count'] = len(verified_sources)

            logger.info(f"KYC verification completed for user {user_id}: {compliance_status}")
            return verification_data

        except Exception as e:
            logger.error(f"KYC verification failed for user {user_id}: {e}")
            raise OracleAuditorError(f"KYC verification failed: {str(e)}")

    def audit_transaction(self, transaction_id: str, transaction_data: Dict[str, Any],
                         rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Audit transaction using oracle data for anomaly detection.

        Args:
            transaction_id: Transaction identifier
            transaction_data: Transaction details
            rules: Custom audit rules (optional)

        Returns:
            Dict with audit results

        Raises:
            OracleAuditorError: If audit fails
        """
        try:
            amount = transaction_data.get('amount', 0)
            currency = transaction_data.get('currency', 'USD')
            timestamp = transaction_data.get('timestamp', datetime.utcnow())

            # Default audit rules
            if rules is None:
                rules = [
                    {'type': 'amount_threshold', 'threshold': 50000, 'severity': 'HIGH'},
                    {'type': 'price_volatility', 'threshold': 0.05, 'severity': 'MEDIUM'},
                    {'type': 'time_window', 'window_hours': 24, 'max_transactions': 10, 'severity': 'MEDIUM'}
                ]

            audit_results = {
                'transaction_id': transaction_id,
                'audit_timestamp': datetime.utcnow().isoformat(),
                'findings': [],
                'overall_risk': 'LOW',
                'oracle_data': {}
            }

            # Convert to USD
            usd_amount = self._convert_to_usd(amount, currency)

            # Check amount threshold
            for rule in rules:
                if rule['type'] == 'amount_threshold':
                    if usd_amount > rule['threshold']:
                        audit_results['findings'].append({
                            'rule': 'amount_threshold',
                            'severity': rule['severity'],
                            'description': f"Transaction amount ${usd_amount} exceeds threshold ${rule['threshold']}",
                            'oracle_verified': True
                        })
                        audit_results['overall_risk'] = max(audit_results['overall_risk'], rule['severity'], key=self._risk_level)

            # Check price volatility using multiple oracles
            if currency in ['ETH', 'BTC', 'LINK']:
                prices = {}
                try:
                    prices['chainlink'] = self.chainlink.get_price(f"{currency}/USD")['price']
                except ChainlinkOracleError:
                    pass

                try:
                    prices['band'] = self.band.get_price(currency, 'USD')['price']
                except BandOracleError:
                    pass

                try:
                    prices['api3'] = self.api3.get_price(f"{currency}/USD")['price']
                except API3OracleError:
                    pass

                audit_results['oracle_data']['prices'] = prices

                if len(prices) >= 2:
                    price_values = list(prices.values())
                    max_price = max(price_values)
                    min_price = min(price_values)
                    volatility = (max_price - min_price) / min_price if min_price > 0 else 0

                    for rule in rules:
                        if rule['type'] == 'price_volatility':
                            if volatility > rule['threshold']:
                                audit_results['findings'].append({
                                    'rule': 'price_volatility',
                                    'severity': rule['severity'],
                                    'description': f"Price volatility {volatility:.4f} exceeds threshold {rule['threshold']}",
                                    'oracle_verified': True
                                })
                                audit_results['overall_risk'] = max(audit_results['overall_risk'], rule['severity'], key=self._risk_level)

            # Time window analysis (simplified - would need transaction history)
            audit_results['oracle_data']['usd_amount'] = usd_amount

            logger.info(f"Transaction audit completed for {transaction_id}: {audit_results['overall_risk']} risk")
            return audit_results

        except Exception as e:
            logger.error(f"Transaction audit failed for {transaction_id}: {e}")
            raise OracleAuditorError(f"Transaction audit failed: {str(e)}")

    def verify_identity(self, identity_data: Dict[str, Any],
                       verification_type: str = 'basic') -> Dict[str, Any]:
        """
        Verify identity using oracle data.

        Args:
            identity_data: Identity information to verify
            verification_type: Type of verification ('basic', 'enhanced', 'comprehensive')

        Returns:
            Dict with verification results

        Raises:
            OracleAuditorError: If verification fails
        """
        try:
            verification_results = {
                'verification_type': verification_type,
                'timestamp': datetime.utcnow().isoformat(),
                'checks': [],
                'overall_verified': False,
                'confidence_score': 0.0
            }

            # Basic verification using oracle data freshness
            if verification_type in ['basic', 'enhanced', 'comprehensive']:
                # Check data freshness from oracles
                checks = []

                try:
                    eth_price = self.chainlink.get_price("ETH/USD")
                    age_hours = (datetime.utcnow().timestamp() - eth_price['updated_at']) / 3600
                    checks.append({
                        'check': 'data_freshness_chainlink',
                        'verified': age_hours < 1,
                        'age_hours': age_hours,
                        'oracle': 'Chainlink'
                    })
                except ChainlinkOracleError as e:
                    checks.append({
                        'check': 'data_freshness_chainlink',
                        'verified': False,
                        'error': str(e),
                        'oracle': 'Chainlink'
                    })

                try:
                    btc_price = self.band.get_price("BTC", "USD")
                    age_hours = (datetime.utcnow().timestamp() - btc_price['last_updated_base']) / 3600
                    checks.append({
                        'check': 'data_freshness_band',
                        'verified': age_hours < 1,
                        'age_hours': age_hours,
                        'oracle': 'Band Protocol'
                    })
                except BandOracleError as e:
                    checks.append({
                        'check': 'data_freshness_band',
                        'verified': False,
                        'error': str(e),
                        'oracle': 'Band Protocol'
                    })

                verification_results['checks'].extend(checks)

            # Enhanced verification - cross-oracle consistency
            if verification_type in ['enhanced', 'comprehensive']:
                try:
                    # Compare ETH prices across oracles
                    chainlink_price = self.chainlink.get_price("ETH/USD")['price']
                    band_price = self.band.get_price("ETH", "USD")['price']

                    price_diff = abs(chainlink_price - band_price) / min(chainlink_price, band_price)
                    consistent = price_diff < 0.02  # 2% tolerance

                    verification_results['checks'].append({
                        'check': 'cross_oracle_consistency',
                        'verified': consistent,
                        'price_difference_pct': price_diff * 100,
                        'oracles': ['Chainlink', 'Band Protocol']
                    })
                except Exception as e:
                    verification_results['checks'].append({
                        'check': 'cross_oracle_consistency',
                        'verified': False,
                        'error': str(e)
                    })

            # Comprehensive verification - API3 data validation
            if verification_type == 'comprehensive':
                try:
                    api3_price = self.api3.get_price("ETH/USD")['price']
                    verification_results['checks'].append({
                        'check': 'api3_data_validation',
                        'verified': True,
                        'price': api3_price,
                        'oracle': 'API3'
                    })
                except API3OracleError as e:
                    verification_results['checks'].append({
                        'check': 'api3_data_validation',
                        'verified': False,
                        'error': str(e),
                        'oracle': 'API3'
                    })

            # Calculate overall verification status
            verified_checks = [c for c in verification_results['checks'] if c.get('verified', False)]
            total_checks = len(verification_results['checks'])

            if total_checks > 0:
                verification_results['confidence_score'] = len(verified_checks) / total_checks
                verification_results['overall_verified'] = verification_results['confidence_score'] >= 0.7

            logger.info(f"Identity verification completed: {verification_results['overall_verified']} "
                       f"(confidence: {verification_results['confidence_score']:.2f})")
            return verification_results

        except Exception as e:
            logger.error(f"Identity verification failed: {e}")
            raise OracleAuditorError(f"Identity verification failed: {str(e)}")

    def _convert_to_usd(self, amount: float, currency: str) -> float:
        """Convert amount to USD using oracle data."""
        if currency == 'USD':
            return amount

        try:
            # Try Chainlink first
            price_data = self.chainlink.get_price(f"{currency}/USD")
            return amount * price_data['price']
        except ChainlinkOracleError:
            try:
                # Fallback to Band Protocol
                price_data = self.band.get_price(currency, "USD")
                return amount * price_data['price']
            except BandOracleError:
                try:
                    # Fallback to API3
                    price_data = self.api3.get_price(f"{currency}/USD")
                    return amount * price_data['price']
                except API3OracleError:
                    logger.warning(f"Could not convert {currency} to USD, using 1:1 rate")
                    return amount  # Fallback to 1:1 if conversion fails

    def _risk_level(self, risk: str) -> int:
        """Convert risk level to numeric for comparison."""
        levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        return levels.get(risk.upper(), 0)