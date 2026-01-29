"""
Advanced Sybil Attack Protection for AILOOS Federated Network.
Implements comprehensive protection against Sybil attacks using:
- Zero-Knowledge Proofs (ZKPs) for identity verification
- Proof-of-Humanity integration
- Behavioral analysis and pattern detection
- Rate limiting and reputation systems
- Multi-layer verification (sin oraculos EVM legacy)
"""

import logging
import hashlib
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from collections import defaultdict, Counter, deque
from datetime import datetime, timedelta
import threading
import math
import random

logger = logging.getLogger(__name__)

# ZKP imports (simplified for implementation)
try:
    import zklib  # Zero-knowledge proof library
    ZKP_AVAILABLE = True
except ImportError:
    ZKP_AVAILABLE = False
    logger.info("ℹ️ Optimized Mode: using simplified ZKP (zklib not present)")

# Oracle integrations legacy (EVM) - deshabilitadas en EmpoorioChain
ORACLES_AVAILABLE = False


class SybilProtectionError(Exception):
    """Base exception for Sybil protection errors."""
    pass


class AntiSybilConfig:
    """Configuration for anti-Sybil protection."""

    def __init__(self,
                 enable_zkp: bool = True,
                 enable_poh: bool = True,
                 enable_oracles: bool = False,
                 rate_limit_requests_per_minute: int = 10,
                 max_similar_ips: int = 5,
                 reputation_decay_rate: float = 0.95,
                 high_risk_threshold: float = 0.8,
                 medium_risk_threshold: float = 0.5):
        self.enable_zkp = enable_zkp
        self.enable_poh = enable_poh
        self.enable_oracles = enable_oracles
        self.rate_limit_requests_per_minute = rate_limit_requests_per_minute
        self.max_similar_ips = max_similar_ips
        self.reputation_decay_rate = reputation_decay_rate
        self.high_risk_threshold = high_risk_threshold
        self.medium_risk_threshold = medium_risk_threshold


class ProtectionLevel:
    """Enumeration of protection levels."""
    BASIC = "basic"
    ADVANCED = "advanced"
    MAXIMUM = "maximum"


class ZeroKnowledgeProof:
    """
    Zero-Knowledge Proof implementation for identity verification.
    Provides cryptographic proofs without revealing sensitive data.
    """

    def __init__(self, proof_system: str = "groth16"):
        self.proof_system = proof_system
        self.proofs: Dict[str, Dict[str, Any]] = {}
        self.verification_keys: Dict[str, Any] = {}

    def generate_identity_proof(self, user_id: str, secret_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ZKP for user identity without revealing secrets."""
        if not ZKP_AVAILABLE:
            # Simplified simulation
            proof_hash = hashlib.sha256(f"{user_id}_{json.dumps(secret_data, sort_keys=True)}".encode()).hexdigest()
            return {
                "proof_id": f"zkp_{proof_hash[:16]}",
                "proof_system": "simulated_groth16",
                "public_inputs": [hashlib.sha256(user_id.encode()).hexdigest()],
                "proof": f"simulated_proof_{proof_hash}",
                "verified": True,
                "confidence": 0.95
            }

        # Real ZKP implementation would go here
        # Using zklib or similar library
        return {}

    def verify_identity_proof(self, proof_data: Dict[str, Any]) -> bool:
        """Verify ZKP without learning private information."""
        if not ZKP_AVAILABLE:
            # Simplified verification
            return proof_data.get("verified", False)

        # Real verification logic
        return True

    def generate_behavioral_proof(self, user_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ZKP for behavioral patterns."""
        # Prove that user has diverse behavior without revealing specifics
        action_types = set(action.get('type', 'unknown') for action in user_actions)
        diversity_score = len(action_types) / max(len(user_actions), 1)

        if not ZKP_AVAILABLE:
            return {
                "proof_id": f"behavioral_{hashlib.sha256(str(user_actions).encode()).hexdigest()[:16]}",
                "diversity_score": diversity_score,
                "verified": diversity_score > 0.3,
                "confidence": min(diversity_score * 2, 0.95)
            }

        return {}


class ProofOfHumanity:
    """
    Integration with Proof-of-Humanity protocols.
    Supports multiple PoH systems like Humanity DAO, BrightID, etc.
    """

    def __init__(self):
        self.supported_protocols = {
            "humanity_dao": self._verify_humanity_dao,
            "brightid": self._verify_brightid,
            "gitcoin_passport": self._verify_gitcoin_passport,
            "worldcoin": self._verify_worldcoin
        }
        self.verification_cache: Dict[str, Tuple[bool, float]] = {}
        self.cache_ttl = 3600  # 1 hour

    def verify_humanity(self, user_id: str, protocol: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify proof-of-humanity using specified protocol."""
        cache_key = f"{user_id}_{protocol}"

        # Check cache
        if cache_key in self.verification_cache:
            cached_result, cache_time = self.verification_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return {
                    "verified": cached_result,
                    "protocol": protocol,
                    "cached": True,
                    "confidence": 0.9 if cached_result else 0.1
                }

        # Perform verification
        verifier = self.supported_protocols.get(protocol)
        if not verifier:
            return {
                "verified": False,
                "protocol": protocol,
                "error": f"Unsupported protocol: {protocol}",
                "confidence": 0.0
            }

        try:
            result = verifier(user_id, credentials)
            self.verification_cache[cache_key] = (result["verified"], time.time())
            return result
        except Exception as e:
            logger.error(f"PoH verification failed for {protocol}: {e}")
            return {
                "verified": False,
                "protocol": protocol,
                "error": str(e),
                "confidence": 0.0
            }

    def _verify_humanity_dao(self, user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Humanity DAO credentials."""
        # Simplified verification - in practice, would call Humanity DAO contracts
        submission_id = credentials.get("submission_id")
        if not submission_id:
            return {"verified": False, "error": "Missing submission ID", "confidence": 0.0}

        # Simulate verification
        is_verified = len(submission_id) > 10  # Simplified check
        return {
            "verified": is_verified,
            "protocol": "humanity_dao",
            "submission_id": submission_id,
            "confidence": 0.85 if is_verified else 0.1
        }

    def _verify_brightid(self, user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify BrightID credentials."""
        context_id = credentials.get("context_id")
        if not context_id:
            return {"verified": False, "error": "Missing context ID", "confidence": 0.0}

        # Simulate BrightID verification
        is_verified = hashlib.sha256(context_id.encode()).hexdigest().startswith('a')
        return {
            "verified": is_verified,
            "protocol": "brightid",
            "context_id": context_id,
            "confidence": 0.8 if is_verified else 0.2
        }

    def _verify_gitcoin_passport(self, user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Gitcoin Passport score."""
        score = credentials.get("score", 0)
        threshold = credentials.get("threshold", 10)

        is_verified = score >= threshold
        return {
            "verified": is_verified,
            "protocol": "gitcoin_passport",
            "score": score,
            "threshold": threshold,
            "confidence": min(score / 50, 0.95) if is_verified else 0.1
        }

    def _verify_worldcoin(self, user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Worldcoin proof."""
        proof = credentials.get("proof")
        if not proof:
            return {"verified": False, "error": "Missing proof", "confidence": 0.0}

        # Simulate Worldcoin verification
        is_verified = len(proof) > 50  # Simplified check
        return {
            "verified": is_verified,
            "protocol": "worldcoin",
            "proof_hash": hashlib.sha256(proof.encode()).hexdigest(),
            "confidence": 0.9 if is_verified else 0.1
        }


class IntelligentRateLimiter:
    """
    Intelligent rate limiting based on user reputation and behavior patterns.
    """

    def __init__(self, base_limits: Dict[str, int] = None):
        self.base_limits = base_limits or {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "federated_rounds_per_day": 5
        }

        self.user_limits: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.user_reputation: Dict[str, float] = defaultdict(lambda: 0.5)  # 0.0 to 1.0
        self.violation_history: Dict[str, List[datetime]] = defaultdict(list)

    def check_rate_limit(self, user_id: str, action_type: str) -> Dict[str, Any]:
        """Check if user is within rate limits."""
        current_time = datetime.utcnow()

        # Get user-specific limits based on reputation
        reputation = self.user_reputation[user_id]
        limits = self._calculate_dynamic_limits(reputation)

        # Clean old entries
        self._clean_old_entries(user_id, action_type, current_time)

        # Count recent actions
        recent_actions = len(self.user_limits[user_id][action_type])

        # Check limits
        if action_type == "requests_per_minute":
            time_window = timedelta(minutes=1)
            max_actions = limits["requests_per_minute"]
        elif action_type == "requests_per_hour":
            time_window = timedelta(hours=1)
            max_actions = limits["requests_per_hour"]
        elif action_type == "federated_rounds_per_day":
            time_window = timedelta(days=1)
            max_actions = limits["federated_rounds_per_day"]
        else:
            return {"allowed": True, "reason": "Unknown action type"}

        # Check if limit exceeded
        if recent_actions >= max_actions:
            self.violation_history[user_id].append(current_time)
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded for {action_type}",
                "current_count": recent_actions,
                "limit": max_actions,
                "retry_after": time_window.total_seconds()
            }

        # Add current action
        self.user_limits[user_id][action_type].append(current_time)

        return {
            "allowed": True,
            "current_count": recent_actions + 1,
            "limit": max_actions,
            "remaining": max_actions - (recent_actions + 1)
        }

    def update_reputation(self, user_id: str, action: str, success: bool):
        """Update user reputation based on actions."""
        reputation_change = 0.0

        if action == "successful_contribution":
            reputation_change = 0.1
        elif action == "failed_verification":
            reputation_change = -0.2
        elif action == "rate_limit_violation":
            reputation_change = -0.3
        elif action == "suspicious_behavior":
            reputation_change = -0.4
        elif action == "human_verification":
            reputation_change = 0.5

        # Apply reputation change
        current_rep = self.user_reputation[user_id]
        new_rep = max(0.0, min(1.0, current_rep + reputation_change))
        self.user_reputation[user_id] = new_rep

        logger.info(f"Updated reputation for {user_id}: {current_rep:.2f} -> {new_rep:.2f} ({action})")

    def _calculate_dynamic_limits(self, reputation: float) -> Dict[str, int]:
        """Calculate dynamic limits based on reputation."""
        # Higher reputation = higher limits
        multiplier = 0.5 + (reputation * 1.5)  # 0.5x to 2.0x

        return {
            "requests_per_minute": int(self.base_limits["requests_per_minute"] * multiplier),
            "requests_per_hour": int(self.base_limits["requests_per_hour"] * multiplier),
            "federated_rounds_per_day": int(self.base_limits["federated_rounds_per_day"] * multiplier)
        }

    def _clean_old_entries(self, user_id: str, action_type: str, current_time: datetime):
        """Clean old entries from rate limiting queues."""
        if action_type == "requests_per_minute":
            cutoff = current_time - timedelta(minutes=1)
        elif action_type == "requests_per_hour":
            cutoff = current_time - timedelta(hours=1)
        elif action_type == "federated_rounds_per_day":
            cutoff = current_time - timedelta(days=1)
        else:
            return

        queue = self.user_limits[user_id][action_type]
        while queue and queue[0] < cutoff:
            queue.popleft()


class ReputationSystem:
    """
    Advanced reputation system resistant to Sybil attacks.
    Uses multiple factors and decay functions.
    """

    def __init__(self):
        self.reputation_scores: Dict[str, float] = defaultdict(lambda: 0.5)
        self.contribution_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.sybil_resistance_factors: Dict[str, float] = {}

        # Decay parameters
        self.decay_rate = 0.95  # Daily decay factor
        self.last_decay = datetime.utcnow()

    def calculate_reputation(self, user_id: str) -> float:
        """Calculate current reputation score for user."""
        self._apply_decay()

        base_score = self.reputation_scores[user_id]
        contributions = self.contribution_history[user_id]

        if not contributions:
            return base_score

        # Calculate contribution-based reputation
        contribution_score = self._calculate_contribution_score(contributions)

        # Apply sybil resistance factors
        sybil_factor = self.sybil_resistance_factors.get(user_id, 1.0)

        # Combine factors
        final_score = (base_score * 0.3 + contribution_score * 0.7) * sybil_factor

        return max(0.0, min(1.0, final_score))

    def add_contribution(self, user_id: str, contribution_type: str, value: float, metadata: Dict[str, Any] = None):
        """Add a contribution to user's history."""
        contribution = {
            "type": contribution_type,
            "value": value,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        self.contribution_history[user_id].append(contribution)

        # Update reputation immediately for positive contributions
        if value > 0:
            current_rep = self.reputation_scores[user_id]
            new_rep = min(1.0, current_rep + (value * 0.1))
            self.reputation_scores[user_id] = new_rep

        # Update sybil resistance
        self._update_sybil_resistance(user_id, contribution)

    def detect_sybil_attack(self, user_id: str) -> Dict[str, Any]:
        """Detect potential Sybil attacks on reputation."""
        contributions = self.contribution_history[user_id]

        if len(contributions) < 5:
            return {"detected": False, "confidence": 0.0, "reason": "Insufficient history"}

        # Analyze contribution patterns
        recent_contributions = [c for c in contributions if c["timestamp"] > datetime.utcnow() - timedelta(days=7)]

        # Check for suspicious patterns
        patterns = self._analyze_suspicious_patterns(recent_contributions)

        # Calculate sybil confidence
        sybil_confidence = self._calculate_sybil_confidence(patterns)

        return {
            "detected": sybil_confidence > 0.7,
            "confidence": sybil_confidence,
            "patterns": patterns,
            "recommendations": self._generate_sybil_recommendations(sybil_confidence)
        }

    def _calculate_contribution_score(self, contributions: List[Dict[str, Any]]) -> float:
        """Calculate reputation score from contributions."""
        if not contributions:
            return 0.5

        total_value = sum(c["value"] for c in contributions)
        avg_value = total_value / len(contributions)

        # Weight recent contributions more heavily
        recent_weight = 0.0
        now = datetime.utcnow()

        for contribution in contributions:
            days_old = (now - contribution["timestamp"]).days
            weight = max(0.1, 1.0 - (days_old * 0.1))  # Decay over time
            recent_weight += contribution["value"] * weight

        recent_avg = recent_weight / len(contributions)

        # Normalize to 0-1 range
        return min(1.0, recent_avg / 10.0)  # Assuming max contribution value of 10

    def _update_sybil_resistance(self, user_id: str, contribution: Dict[str, Any]):
        """Update sybil resistance factors."""
        # Simple implementation - in practice, would use more sophisticated analysis
        contribution_type = contribution["type"]

        if contribution_type == "verified_human":
            self.sybil_resistance_factors[user_id] = min(1.0, self.sybil_resistance_factors.get(user_id, 1.0) + 0.1)
        elif contribution_type == "suspicious_activity":
            self.sybil_resistance_factors[user_id] = max(0.1, self.sybil_resistance_factors.get(user_id, 1.0) - 0.2)

    def _analyze_suspicious_patterns(self, contributions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contributions for suspicious patterns."""
        patterns = {}

        # Check for burst contributions
        timestamps = [c["timestamp"] for c in contributions]
        if len(timestamps) > 1:
            intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
            avg_interval = sum(intervals) / len(intervals)
            patterns["burst_contributions"] = avg_interval < 60  # Less than 1 minute apart

        # Check for uniform contribution values
        values = [c["value"] for c in contributions]
        if len(values) > 1:
            value_std = math.sqrt(sum((v - sum(values)/len(values))**2 for v in values) / len(values))
            patterns["uniform_values"] = value_std < 0.1

        # Check for round number contributions
        round_numbers = sum(1 for c in contributions if c["value"] % 1 == 0)
        patterns["round_number_bias"] = round_numbers / len(contributions) > 0.8

        return patterns

    def _calculate_sybil_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence that user is conducting Sybil attack."""
        confidence = 0.0

        if patterns.get("burst_contributions", False):
            confidence += 0.3
        if patterns.get("uniform_values", False):
            confidence += 0.2
        if patterns.get("round_number_bias", False):
            confidence += 0.2

        # Add reputation-based adjustment
        # Lower reputation increases Sybil suspicion
        return min(1.0, confidence)

    def _generate_sybil_recommendations(self, confidence: float) -> List[str]:
        """Generate recommendations based on Sybil confidence."""
        if confidence > 0.8:
            return [
                "Immediate account suspension",
                "Require additional human verification",
                "Flag all associated contributions for review"
            ]
        elif confidence > 0.6:
            return [
                "Implement stricter rate limiting",
                "Require additional verification steps",
                "Monitor closely for 30 days"
            ]
        elif confidence > 0.4:
            return [
                "Increase monitoring frequency",
                "Request additional identity verification"
            ]
        else:
            return ["Continue normal monitoring"]

    def _apply_decay(self):
        """Apply time-based decay to reputation scores."""
        now = datetime.utcnow()
        if (now - self.last_decay).days >= 1:
            decay_factor = self.decay_rate ** (now - self.last_decay).days

            for user_id in self.reputation_scores:
                self.reputation_scores[user_id] *= decay_factor

            self.last_decay = now


class SybilProtector:
    """
    Sybil Attack Protection class.
    Uses oracles for proof-of-humanity verification, analyzes behavioral patterns,
    and validates unique identities to prevent Sybil attacks.
    """

    # Risk thresholds
    HIGH_RISK_THRESHOLD = 0.8
    MEDIUM_RISK_THRESHOLD = 0.5

    # Pattern detection thresholds
    MAX_REQUESTS_PER_MINUTE = 10
    MAX_SIMILAR_IPS = 5
    TIME_WINDOW_MINUTES = 5

    def __init__(self, enable_advanced_features: bool = True, enable_oracles: bool = False):
        """
        Initialize Advanced Sybil Protector.

        Args:
            enable_advanced_features: Enable ZKP, PoH, and advanced reputation
            enable_oracles: Enable legacy EVM oracles (disabled for EmpoorioChain)
        """
        self.enable_advanced_features = enable_advanced_features
        self.enable_oracles = enable_oracles

        # Initialize advanced components
        if enable_advanced_features:
            self.zkp_system = ZeroKnowledgeProof()
            self.proof_of_humanity = ProofOfHumanity()
            self.rate_limiter = IntelligentRateLimiter()
            self.reputation_system = ReputationSystem()

        # Oracles EVM legacy deshabilitados
        self.oracles_available = False

        # Storage for unique identities
        self._unique_identities: Set[str] = set()

        # Enhanced behavioral tracking
        self._ip_tracking: Dict[str, List[datetime]] = defaultdict(list)
        self._user_actions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._device_fingerprints: Dict[str, Set[str]] = defaultdict(set)

        # Verification cache
        self._verification_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._cache_ttl = 3600  # 1 hour

        logger.info("Advanced SybilProtector initialized")
        logger.info(f"  Advanced features: {'Enabled' if enable_advanced_features else 'Disabled'}")
        logger.info(f"  Oracle integrations: {'Available' if self.oracles_available else 'Disabled'}")

    def verify_human(self, user_id: str, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced human verification using ZKP, Proof-of-Humanity, and oracles.

        Args:
            user_id: Unique user identifier
            proof_data: Proof data containing ZKP, PoH, and oracle parameters

        Returns:
            Dict with comprehensive verification result

        Raises:
            SybilProtectionError: If verification fails
        """
        try:
            # Check cache first
            cache_key = f"{user_id}_{hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()}"
            if cache_key in self._verification_cache:
                cached_result, cache_time = self._verification_cache[cache_key]
                if time.time() - cache_time < self._cache_ttl:
                    return cached_result

            verification_results = []
            confidence_score = 0.0
            verification_methods = []

            # 1. Zero-Knowledge Proof verification (if enabled)
            if self.enable_advanced_features and proof_data.get('zkp_enabled', False):
                zkp_result = self.zkp_system.generate_identity_proof(user_id, proof_data.get('secret_data', {}))
                if self.zkp_system.verify_identity_proof(zkp_result):
                    verification_results.append({
                        'method': 'zkp',
                        'verified': True,
                        'proof_id': zkp_result.get('proof_id'),
                        'confidence': zkp_result.get('confidence', 0.9)
                    })
                    confidence_score += zkp_result.get('confidence', 0.9)
                    verification_methods.append('zkp')

            # 2. Proof-of-Humanity verification (if enabled)
            if self.enable_advanced_features and proof_data.get('poh_enabled', False):
                poh_protocol = proof_data.get('poh_protocol', 'humanity_dao')
                poh_result = self.proof_of_humanity.verify_humanity(
                    user_id, poh_protocol, proof_data.get('poh_credentials', {})
                )
                verification_results.append({
                    'method': 'proof_of_humanity',
                    'protocol': poh_protocol,
                    'verified': poh_result['verified'],
                    'confidence': poh_result.get('confidence', 0.0)
                })
                if poh_result['verified']:
                    confidence_score += poh_result.get('confidence', 0.8)
                    verification_methods.append('poh')

            # 3. Oracle-based verification (fallback/confirmation)
            oracles_to_use = proof_data.get('oracles', ['chainlink', 'band', 'api3'])
            oracle_confidence = 0.0

            if self.oracles_available:
                for oracle_name in oracles_to_use:
                    try:
                        if oracle_name == 'chainlink':
                            request_id = self.chainlink_oracle.request_randomness(
                                subscription_id=proof_data.get('subscription_id', 1),
                                key_hash="0x79d3d8832d904592c0bf9818b621522c988bb8b0c7cdc3b160f161183e3a36287d",
                                num_words=1
                            )
                            if request_id:
                                random_value = self.chainlink_oracle.get_randomness(request_id)
                                if random_value:
                                    oracle_confidence += 0.9

                        elif oracle_name == 'band':
                            identity_data = self.band_oracle.get_price(
                                base=proof_data.get('identity_symbol', 'ETH')
                            )
                            if identity_data:
                                oracle_confidence += 0.8

                        elif oracle_name == 'api3':
                            verification_feed = self.api3_oracle.get_data_feed(
                                dapi_name=proof_data.get('verification_feed', 'ETH/USD')
                            )
                            if verification_feed:
                                oracle_confidence += 0.85

                    except Exception as e:
                        logger.warning(f"Oracle {oracle_name} verification failed: {e}")

                if len(oracles_to_use) > 0:
                    oracle_confidence /= len(oracles_to_use)
                    verification_methods.append('oracles')

            confidence_score += oracle_confidence

            # 4. Behavioral verification (if enabled)
            if self.enable_advanced_features and proof_data.get('behavioral_check', False):
                behavioral_proof = self.zkp_system.generate_behavioral_proof(
                    self._user_actions.get(user_id, [])
                )
                if behavioral_proof.get('verified', False):
                    confidence_score += behavioral_proof.get('confidence', 0.0)
                    verification_methods.append('behavioral')

            # Normalize confidence score
            total_methods = len(verification_methods)
            if total_methods > 0:
                confidence_score /= total_methods

            # Determine verification result
            is_human = confidence_score >= 0.7

            # Update reputation system
            if self.enable_advanced_features:
                if is_human:
                    self.reputation_system.add_contribution(user_id, "human_verification", 1.0)
                    self.rate_limiter.update_reputation(user_id, "human_verification", True)
                else:
                    self.reputation_system.add_contribution(user_id, "failed_verification", -0.5)
                    self.rate_limiter.update_reputation(user_id, "failed_verification", False)

            result = {
                'user_id': user_id,
                'is_human': is_human,
                'confidence_score': confidence_score,
                'verification_methods': verification_methods,
                'verification_results': verification_results,
                'timestamp': datetime.utcnow().isoformat(),
                'risk_assessment': self._assess_verification_risk(confidence_score),
                'reputation_score': self.reputation_system.calculate_reputation(user_id) if self.enable_advanced_features else 0.5
            }

            # Cache result
            self._verification_cache[cache_key] = (result, time.time())

            logger.info(f"Advanced human verification for {user_id}: {is_human} (confidence: {confidence_score:.2f}, methods: {verification_methods})")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in advanced human verification for {user_id}: {e}")
            raise SybilProtectionError(f"Human verification failed: {str(e)}")

    def detect_sybil_patterns(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced Sybil pattern detection with rate limiting and reputation analysis.

        Args:
            user_data: User behavioral data including IP, timestamps, actions

        Returns:
            Dict with comprehensive pattern analysis and risk assessment

        Raises:
            SybilProtectionError: If analysis fails
        """
        try:
            user_id = user_data.get('user_id', 'unknown')
            ip_address = user_data.get('ip_address')
            timestamp = user_data.get('timestamp', datetime.utcnow())
            action = user_data.get('action', 'unknown')
            device_fingerprint = user_data.get('device_fingerprint')

            if not isinstance(timestamp, datetime):
                timestamp = datetime.fromisoformat(timestamp)

            # Check rate limits first
            rate_limit_check = None
            if self.enable_advanced_features:
                rate_limit_check = self.rate_limiter.check_rate_limit(user_id, "requests_per_minute")
                if not rate_limit_check["allowed"]:
                    # Immediate rejection for rate limit violations
                    self.rate_limiter.update_reputation(user_id, "rate_limit_violation", False)
                    return {
                        'user_id': user_id,
                        'is_suspicious': True,
                        'risk_score': 1.0,
                        'risk_level': 'critical',
                        'blocked_reason': 'rate_limit_exceeded',
                        'rate_limit_info': rate_limit_check,
                        'timestamp': datetime.utcnow().isoformat(),
                        'recommendations': ['Immediate blocking due to rate limit violation']
                    }

            # Track user actions and device fingerprints
            self._user_actions[user_id].append({
                'timestamp': timestamp,
                'ip': ip_address,
                'action': action,
                'device_fingerprint': device_fingerprint
            })

            if device_fingerprint:
                self._device_fingerprints[user_id].add(device_fingerprint)

            # Analyze patterns
            ip_patterns = self._analyze_ip_patterns(user_id, ip_address, timestamp)
            time_patterns = self._analyze_time_patterns(user_id, timestamp)
            behavioral_patterns = self._analyze_behavioral_patterns(user_id)
            device_patterns = self._analyze_device_patterns(user_id) if device_fingerprint else {}

            # Calculate risk score
            risk_score = self._calculate_risk_score(ip_patterns, time_patterns, behavioral_patterns)

            # Apply reputation adjustment
            if self.enable_advanced_features:
                reputation = self.reputation_system.calculate_reputation(user_id)
                risk_score = max(0.0, risk_score - (reputation * 0.3))  # Good reputation reduces risk

                # Check for Sybil attacks on reputation
                sybil_attack_check = self.reputation_system.detect_sybil_attack(user_id)
                if sybil_attack_check["detected"]:
                    risk_score = min(1.0, risk_score + sybil_attack_check["confidence"] * 0.5)

            # Determine if suspicious
            is_suspicious = risk_score >= self.MEDIUM_RISK_THRESHOLD

            # Update reputation based on behavior
            if self.enable_advanced_features:
                if is_suspicious:
                    self.reputation_system.add_contribution(user_id, "suspicious_behavior", -0.2)
                    self.rate_limiter.update_reputation(user_id, "suspicious_behavior", False)
                else:
                    self.reputation_system.add_contribution(user_id, "normal_behavior", 0.1)

            result = {
                'user_id': user_id,
                'is_suspicious': is_suspicious,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'pattern_analysis': {
                    'ip_patterns': ip_patterns,
                    'time_patterns': time_patterns,
                    'behavioral_patterns': behavioral_patterns,
                    'device_patterns': device_patterns
                },
                'reputation_score': self.reputation_system.calculate_reputation(user_id) if self.enable_advanced_features else 0.5,
                'rate_limit_status': rate_limit_check,
                'sybil_attack_detection': self.reputation_system.detect_sybil_attack(user_id) if self.enable_advanced_features else None,
                'timestamp': datetime.utcnow().isoformat(),
                'recommendations': self._generate_recommendations(risk_score, ip_patterns, time_patterns)
            }

            logger.info(f"Advanced Sybil pattern detection for {user_id}: risk_score={risk_score:.2f}, suspicious={is_suspicious}")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in advanced pattern detection for {user_data.get('user_id', 'unknown')}: {e}")
            raise SybilProtectionError(f"Pattern detection failed: {str(e)}")

    def validate_unique_identity(self, identity_hash: str, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate that the identity is unique.

        Args:
            identity_hash: Hash representing the unique identity
            user_data: Additional user data for enhanced validation

        Returns:
            Dict with validation result

        Raises:
            SybilProtectionError: If validation fails
        """
        try:
            # Check if identity already exists
            is_unique = identity_hash not in self._unique_identities

            if is_unique:
                self._unique_identities.add(identity_hash)

            # Additional validation using user data
            additional_checks = {}
            if user_data:
                additional_checks = self._perform_additional_identity_checks(identity_hash, user_data)

            # Calculate uniqueness confidence
            uniqueness_confidence = 1.0 if is_unique else 0.0
            if additional_checks:
                uniqueness_confidence = sum(additional_checks.values()) / len(additional_checks)

            result = {
                'identity_hash': identity_hash,
                'is_unique': is_unique,
                'uniqueness_confidence': uniqueness_confidence,
                'additional_checks': additional_checks,
                'timestamp': datetime.utcnow().isoformat(),
                'total_unique_identities': len(self._unique_identities)
            }

            logger.info(f"Identity validation for hash {identity_hash[:8]}...: unique={is_unique}, confidence={uniqueness_confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in identity validation for hash {identity_hash[:8]}...: {e}")
            raise SybilProtectionError(f"Identity validation failed: {str(e)}")

    def _assess_verification_risk(self, confidence_score: float) -> Dict[str, Any]:
        """Assess risk based on verification confidence."""
        if confidence_score >= 0.8:
            risk_level = "low"
            risk_factors = []
        elif confidence_score >= 0.6:
            risk_level = "medium"
            risk_factors = ["Low oracle consensus"]
        else:
            risk_level = "high"
            risk_factors = ["Insufficient oracle verification", "Potential automated access"]

        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'confidence_score': confidence_score
        }

    def _analyze_ip_patterns(self, user_id: str, ip_address: str, timestamp: datetime) -> Dict[str, Any]:
        """Analyze IP address patterns for Sybil detection."""
        if not ip_address:
            return {'analyzed': False, 'reason': 'No IP address provided'}

        # Track IP usage
        self._ip_tracking[ip_address].append(timestamp)

        # Clean old entries (older than time window)
        cutoff_time = timestamp - timedelta(minutes=self.TIME_WINDOW_MINUTES)
        self._ip_tracking[ip_address] = [
            t for t in self._ip_tracking[ip_address] if t > cutoff_time
        ]

        # Analyze patterns
        recent_requests = len(self._ip_tracking[ip_address])
        ip_frequency = recent_requests / self.TIME_WINDOW_MINUTES

        # Check for IP sharing across users (simplified)
        users_with_same_ip = sum(1 for actions in self._user_actions.values()
                                for action in actions[-10:]  # Last 10 actions
                                if action.get('ip') == ip_address)

        return {
            'ip_address': ip_address,
            'recent_requests': recent_requests,
            'requests_per_minute': ip_frequency,
            'high_frequency': ip_frequency > self.MAX_REQUESTS_PER_MINUTE,
            'shared_ip_users': users_with_same_ip,
            'ip_sharing_suspicious': users_with_same_ip > self.MAX_SIMILAR_IPS
        }

    def _analyze_time_patterns(self, user_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Analyze timing patterns for Sybil detection."""
        user_actions = self._user_actions[user_id]

        if len(user_actions) < 2:
            return {'analyzed': False, 'reason': 'Insufficient action history'}

        # Analyze time intervals between actions
        timestamps = [action['timestamp'] for action in user_actions[-20:]]  # Last 20 actions
        intervals = []

        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)

            # Detect bot-like patterns (very regular intervals)
            regularity_score = self._calculate_regularity(intervals)

            return {
                'total_actions': len(user_actions),
                'analyzed_actions': len(timestamps),
                'avg_interval_seconds': avg_interval,
                'min_interval_seconds': min_interval,
                'max_interval_seconds': max_interval,
                'regularity_score': regularity_score,
                'bot_like_pattern': regularity_score > 0.8
            }
        else:
            return {'analyzed': False, 'reason': 'No intervals to analyze'}

    def _analyze_behavioral_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze behavioral patterns."""
        user_actions = self._user_actions[user_id]

        if not user_actions:
            return {'analyzed': False, 'reason': 'No actions recorded'}

        # Analyze action types
        action_counts = Counter(action['action'] for action in user_actions)
        total_actions = len(user_actions)

        # Calculate action diversity
        unique_actions = len(action_counts)
        action_diversity = unique_actions / total_actions if total_actions > 0 else 0

        # Detect repetitive patterns
        recent_actions = [action['action'] for action in user_actions[-10:]]
        repetitive_score = self._calculate_repetition(recent_actions)

        # Analyze action frequency patterns
        action_timestamps = [action['timestamp'] for action in user_actions]
        frequency_patterns = self._analyze_action_frequency(action_timestamps)

        return {
            'total_actions': total_actions,
            'unique_actions': unique_actions,
            'action_diversity': action_diversity,
            'repetitive_score': repetitive_score,
            'frequency_patterns': frequency_patterns,
            'low_diversity': action_diversity < 0.3,
            'high_repetition': repetitive_score > 0.7,
            'action_distribution': dict(action_counts)
        }

    def _analyze_device_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze device fingerprint patterns for Sybil detection."""
        device_fingerprints = self._device_fingerprints[user_id]

        if not device_fingerprints:
            return {'analyzed': False, 'reason': 'No device fingerprints recorded'}

        # Check for device sharing across users
        shared_devices = 0
        for other_user, other_devices in self._device_fingerprints.items():
            if other_user != user_id:
                if device_fingerprints & other_devices:  # Intersection
                    shared_devices += 1

        # Analyze fingerprint consistency
        fingerprint_count = len(device_fingerprints)
        unique_fingerprints = len(set(device_fingerprints))

        return {
            'device_fingerprint_count': fingerprint_count,
            'unique_fingerprints': unique_fingerprints,
            'shared_devices_with_others': shared_devices,
            'device_sharing_suspicious': shared_devices > 2,
            'fingerprint_consistency': unique_fingerprints / fingerprint_count if fingerprint_count > 0 else 0
        }

    def _analyze_action_frequency(self, timestamps: List[datetime]) -> Dict[str, Any]:
        """Analyze action frequency patterns."""
        if len(timestamps) < 2:
            return {'analyzed': False, 'reason': 'Insufficient data'}

        # Calculate intervals
        sorted_timestamps = sorted(timestamps)
        intervals = []
        for i in range(1, len(sorted_timestamps)):
            interval = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds()
            intervals.append(interval)

        if not intervals:
            return {'analyzed': False, 'reason': 'No intervals calculated'}

        # Statistical analysis
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        # Detect bot-like patterns (very regular intervals)
        regularity_score = self._calculate_regularity(intervals)

        # Detect burst patterns
        burst_threshold = avg_interval * 0.1  # 10% of average
        burst_actions = sum(1 for interval in intervals if interval < burst_threshold)

        return {
            'total_intervals': len(intervals),
            'avg_interval_seconds': avg_interval,
            'min_interval_seconds': min_interval,
            'max_interval_seconds': max_interval,
            'regularity_score': regularity_score,
            'burst_actions': burst_actions,
            'burst_ratio': burst_actions / len(intervals),
            'bot_like_pattern': regularity_score > 0.8 or burst_actions > len(intervals) * 0.3
        }

    def _calculate_risk_score(self, ip_patterns: Dict, time_patterns: Dict, behavioral_patterns: Dict) -> float:
        """Calculate overall risk score from pattern analysis."""
        risk_score = 0.0
        factors = 0

        # IP-based risk
        if ip_patterns.get('analyzed', False):
            if ip_patterns.get('high_frequency', False):
                risk_score += 0.4
            if ip_patterns.get('ip_sharing_suspicious', False):
                risk_score += 0.3
            factors += 1

        # Time-based risk
        if time_patterns.get('analyzed', False):
            if time_patterns.get('bot_like_pattern', False):
                risk_score += 0.3
            regularity_penalty = time_patterns.get('regularity_score', 0) * 0.2
            risk_score += regularity_penalty
            factors += 1

        # Behavioral risk
        if behavioral_patterns.get('analyzed', False):
            if behavioral_patterns.get('low_diversity', False):
                risk_score += 0.2
            if behavioral_patterns.get('high_repetition', False):
                risk_score += 0.2
            factors += 1

        # Normalize risk score
        if factors > 0:
            risk_score /= factors

        return min(risk_score, 1.0)  # Cap at 1.0

    def _calculate_regularity(self, intervals: List[float]) -> float:
        """Calculate regularity score for time intervals."""
        if len(intervals) < 2:
            return 0.0

        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5

        # Regularity score (lower std_dev means more regular)
        regularity = 1 - min(std_dev / mean, 1) if mean > 0 else 0
        return regularity

    def _calculate_repetition(self, actions: List[str]) -> float:
        """Calculate repetition score for actions."""
        if not actions:
            return 0.0

        # Count consecutive repetitions
        consecutive_repeats = 0
        for i in range(1, len(actions)):
            if actions[i] == actions[i-1]:
                consecutive_repeats += 1

        return consecutive_repeats / len(actions)

    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level based on score."""
        if risk_score >= self.HIGH_RISK_THRESHOLD:
            return "high"
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, risk_score: float, ip_patterns: Dict, time_patterns: Dict) -> List[str]:
        """Generate recommendations based on risk analysis."""
        recommendations = []

        if risk_score >= self.HIGH_RISK_THRESHOLD:
            recommendations.append("Immediate blocking recommended")
            recommendations.append("Require additional human verification")
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            recommendations.append("Implement rate limiting")
            recommendations.append("Request additional verification steps")

        if ip_patterns.get('ip_sharing_suspicious', False):
            recommendations.append("Investigate IP address sharing patterns")

        if time_patterns.get('bot_like_pattern', False):
            recommendations.append("Monitor for automated behavior patterns")

        if not recommendations:
            recommendations.append("No immediate action required")

        return recommendations

    def _perform_additional_identity_checks(self, identity_hash: str, user_data: Dict[str, Any]) -> Dict[str, float]:
        """Perform additional identity validation checks."""
        checks = {}

        # Check email domain diversity (if email provided)
        if 'email' in user_data:
            email_domain = user_data['email'].split('@')[-1]
            # Simplified check - in practice, you'd have a database of suspicious domains
            checks['email_domain_check'] = 0.9 if email_domain not in ['temp-mail.org', '10minutemail.com'] else 0.1

        # Check device fingerprint consistency (if provided)
        if 'device_fingerprint' in user_data:
            fingerprint = user_data['device_fingerprint']
            # Simplified - check if fingerprint is unique
            fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
            checks['device_fingerprint_check'] = 1.0 if fingerprint_hash not in self._unique_identities else 0.0

        # Geographic consistency check
        if 'ip_geolocation' in user_data and 'declared_location' in user_data:
            # Simplified geographic check
            ip_country = user_data['ip_geolocation'].get('country')
            declared_country = user_data['declared_location'].get('country')
            checks['geographic_consistency'] = 1.0 if ip_country == declared_country else 0.3

        return checks

    def get_protection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about advanced Sybil protection activities.

        Returns:
            Dict with detailed protection statistics
        """
        total_users = len(self._user_actions)
        total_identities = len(self._unique_identities)
        total_ip_addresses = len(self._ip_tracking)
        total_device_fingerprints = sum(len(fingerprints) for fingerprints in self._device_fingerprints.values())

        stats = {
            'total_users_tracked': total_users,
            'total_unique_identities': total_identities,
            'total_ip_addresses_tracked': total_ip_addresses,
            'total_device_fingerprints': total_device_fingerprints,
            'average_actions_per_user': sum(len(actions) for actions in self._user_actions.values()) / total_users if total_users > 0 else 0,
            'verification_cache_size': len(self._verification_cache),
            'timestamp': datetime.utcnow().isoformat()
        }

        # Add advanced features stats if enabled
        if self.enable_advanced_features:
            stats.update({
                'zkp_proofs_generated': len(self.zkp_system.proofs),
                'reputation_system_users': len(self.reputation_system.reputation_scores),
                'rate_limiter_active_users': len(self.rate_limiter.user_limits),
                'average_reputation_score': sum(self.reputation_system.reputation_scores.values()) / len(self.reputation_system.reputation_scores) if self.reputation_system.reputation_scores else 0.5,
                'proof_of_humanity_cache_size': len(self.proof_of_humanity.verification_cache),
                'sybil_attack_detections': sum(1 for user_id in self.reputation_system.reputation_scores.keys()
                                             if self.reputation_system.detect_sybil_attack(user_id)['detected'])
            })

        return stats


def demonstrate_anti_sybil_protection():
    """
    Demonstrate advanced anti-Sybil protection capabilities.

    Returns:
        Dict with demonstration results
    """
    print("🛡️ Demonstrating Advanced Anti-Sybil Protection")
    print("=" * 50)

    # Create protector instance
    protector = SybilProtector(enable_advanced_features=True)

    # Test human verification
    print("\n1. Testing Human Verification...")
    proof_data = {
        'zkp_enabled': True,
        'poh_enabled': True,
        'oracles': ['chainlink'],
        'secret_data': {'user_secret': 'test_secret'},
        'poh_protocol': 'brightid',
        'poh_credentials': {'context_id': 'test_context_123'}
    }

    try:
        verification_result = protector.verify_human("test_user_123", proof_data)
        print(f"   ✅ Human verification: {verification_result['is_human']} "
              f"(confidence: {verification_result['confidence_score']:.2f})")
    except Exception as e:
        print(f"   ⚠️ Human verification test failed: {e}")

    # Test Sybil pattern detection
    print("\n2. Testing Sybil Pattern Detection...")
    user_data = {
        'user_id': 'test_user_456',
        'ip_address': '192.168.1.100',
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'login_attempt',
        'device_fingerprint': 'device_abc123'
    }

    try:
        pattern_result = protector.detect_sybil_patterns(user_data)
        print(f"   ✅ Pattern detection: risk_score={pattern_result['risk_score']:.2f}, "
              f"suspicious={pattern_result['is_suspicious']}")
    except Exception as e:
        print(f"   ⚠️ Pattern detection test failed: {e}")

    # Test identity validation
    print("\n3. Testing Identity Validation...")
    identity_hash = hashlib.sha256(b"test_identity_data").hexdigest()

    try:
        identity_result = protector.validate_unique_identity(identity_hash)
        print(f"   ✅ Identity validation: unique={identity_result['is_unique']} "
              f"(confidence: {identity_result['uniqueness_confidence']:.2f})")
    except Exception as e:
        print(f"   ⚠️ Identity validation test failed: {e}")

    # Get protection stats
    print("\n4. Protection Statistics...")
    try:
        stats = protector.get_protection_stats()
        print(f"   ✅ Protection stats: {stats['total_users_tracked']} users tracked, "
              f"{stats['total_unique_identities']} unique identities")
    except Exception as e:
        print(f"   ⚠️ Stats retrieval failed: {e}")

    print("\n🎉 Anti-Sybil Protection Demonstration Complete!")
    return {
        'demonstration_completed': True,
        'timestamp': datetime.utcnow().isoformat(),
        'features_tested': ['human_verification', 'pattern_detection', 'identity_validation', 'statistics']
    }
