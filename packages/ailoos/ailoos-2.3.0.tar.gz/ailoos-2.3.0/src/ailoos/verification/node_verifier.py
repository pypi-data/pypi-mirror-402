"""
Node verification system for Ailoos federated learning.
Provides cryptographic verification of node identity, reputation, and capabilities.
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import Certificate, CertificateBuilder, Name, NameAttribute
from cryptography.x509.oid import NameOID
import base64

from ..core.config import Config
from ..utils.logging import AiloosLogger


@dataclass
class NodeIdentity:
    """Cryptographic identity of a node."""
    node_id: str
    public_key: str  # PEM format
    certificate: str  # X.509 certificate PEM
    created_at: datetime
    expires_at: datetime
    signature: str  # Self-signature of identity


@dataclass
class NodeReputation:
    """Reputation score and history of a node."""
    node_id: str
    reputation_score: float  # 0.0 to 1.0
    total_contributions: int
    successful_contributions: int
    failed_contributions: int
    total_rewards_earned: float
    last_activity: datetime
    trust_level: str  # 'untrusted', 'basic', 'verified', 'trusted', 'elite'
    sanctions: List[Dict[str, Any]]  # Active sanctions


@dataclass
class HardwareVerification:
    """Verified hardware capabilities of a node."""
    node_id: str
    cpu_model: str
    cpu_cores: int
    memory_gb: int
    gpu_model: Optional[str]
    gpu_memory_gb: Optional[int]
    storage_gb: int
    network_speed_mbps: int
    verified_at: datetime
    proof_of_work: str
    signature: str


@dataclass
class VerificationChallenge:
    """Cryptographic challenge for node verification."""
    challenge_id: str
    node_id: str
    challenge_data: str
    difficulty: int
    expires_at: datetime
    solution: Optional[str] = None
    verified: bool = False


class NodeVerifier:
    """Manages node verification, reputation, and trust."""

    def __init__(self, config: Config, coordinator: Optional[Any] = None):
        self.config = config
        self.coordinator = coordinator
        self.logger = AiloosLogger(__name__)

        # Verification settings
        self.min_reputation_score = config.get('min_reputation_score', 0.3)
        self.challenge_timeout = config.get('challenge_timeout', 300)  # 5 minutes
        self.cert_validity_days = config.get('cert_validity_days', 365)
        self.max_sanctions = config.get('max_sanctions', 3)

        # Storage
        self.identities: Dict[str, NodeIdentity] = {}
        self.reputations: Dict[str, NodeReputation] = {}
        self.hardware_verifications: Dict[str, HardwareVerification] = {}
        self.active_challenges: Dict[str, VerificationChallenge] = {}

        # Cryptographic keys (in production, these would be in HSM)
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096  # Increased key size for better security
        )
        self._public_key = self._private_key.public_key()

        # Initialize certificate authority for node certificates
        from .certificate_authority import CertificateAuthority
        self.ca = CertificateAuthority()

    async def register_node(self, node_id: str, public_key_pem: str) -> Optional[NodeIdentity]:
        """Register a new node with cryptographic identity."""
        try:
            # Validate public key
            try:
                public_key = serialization.load_pem_public_key(public_key_pem.encode())
            except Exception as e:
                self.logger.error(f"Invalid public key for node {node_id}: {e}")
                return None

            # Generate certificate using CA
            certificate_pem = self.ca.issue_node_certificate(node_id, public_key)

            # Create identity
            now = datetime.now()
            expires_at = now + timedelta(days=self.cert_validity_days)

            identity = NodeIdentity(
                node_id=node_id,
                public_key=public_key_pem,
                certificate=certificate_pem,
                created_at=now,
                expires_at=expires_at,
                signature=self._sign_identity(node_id, public_key_pem, certificate_pem)
            )

            # Store identity
            self.identities[node_id] = identity

            # Initialize reputation
            self.reputations[node_id] = NodeReputation(
                node_id=node_id,
                reputation_score=0.5,  # Neutral starting score
                total_contributions=0,
                successful_contributions=0,
                failed_contributions=0,
                total_rewards_earned=0.0,
                last_activity=now,
                trust_level='basic',
                sanctions=[]
            )

            self.logger.info(f"Registered new node: {node_id}")
            return identity

        except Exception as e:
            self.logger.error(f"Error registering node {node_id}: {e}")
            return None

    async def verify_node_identity(self, node_id: str, signature: str, data: str) -> bool:
        """Verify that data was signed by the node's private key."""
        try:
            identity = self.identities.get(node_id)
            if not identity:
                return False

            # Load public key
            public_key = serialization.load_pem_public_key(identity.public_key.encode())

            # Verify signature
            signature_bytes = base64.b64decode(signature)
            data_bytes = data.encode()

            public_key.verify(
                signature_bytes,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True

        except Exception as e:
            self.logger.warning(f"Identity verification failed for {node_id}: {e}")
            return False

    async def create_verification_challenge(self, node_id: str) -> Optional[VerificationChallenge]:
        """Create a cryptographic challenge for node verification."""
        try:
            if node_id not in self.identities:
                self.logger.warning(f"Node {node_id} not registered")
                return None

            # Generate cryptographically secure challenge data
            challenge_data = secrets.token_hex(64)  # Increased entropy

            # Adaptive difficulty based on node reputation
            reputation = self.reputations.get(node_id)
            if reputation:
                if reputation.trust_level == 'elite':
                    difficulty = 2  # Easier for trusted nodes
                elif reputation.trust_level == 'trusted':
                    difficulty = 3
                elif reputation.trust_level == 'verified':
                    difficulty = 4
                else:
                    difficulty = 5  # Harder for untrusted nodes
            else:
                difficulty = 4  # Default

            challenge = VerificationChallenge(
                challenge_id=secrets.token_hex(32),  # More entropy for challenge ID
                node_id=node_id,
                challenge_data=challenge_data,
                difficulty=difficulty,
                expires_at=datetime.now() + timedelta(seconds=self.challenge_timeout)
            )

            self.active_challenges[challenge.challenge_id] = challenge

            self.logger.info(f"Created verification challenge for {node_id}: difficulty={difficulty}, expires={challenge.expires_at}")
            return challenge

        except Exception as e:
            self.logger.error(f"Error creating challenge for {node_id}: {e}")
            return None

    async def verify_challenge_solution(
        self,
        challenge_id: str,
        solution: str,
        signature: str
    ) -> bool:
        """Verify the solution to a verification challenge."""
        try:
            challenge = self.active_challenges.get(challenge_id)
            if not challenge:
                return False

            # Check expiration
            if datetime.now() > challenge.expires_at:
                del self.active_challenges[challenge_id]
                return False

            # Verify signature
            data_to_verify = f"{challenge.challenge_data}:{solution}"
            if not await self.verify_node_identity(challenge.node_id, signature, data_to_verify):
                return False

            # Verify proof of work
            if not self._verify_proof_of_work(challenge.challenge_data, solution, challenge.difficulty):
                return False

            # Mark as verified
            challenge.solution = solution
            challenge.verified = True

            # Update reputation
            await self._update_reputation_for_verification(challenge.node_id, True)

            # Clean up
            del self.active_challenges[challenge_id]

            self.logger.info(f"Challenge {challenge_id} verified for node {challenge.node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying challenge {challenge_id}: {e}")
            return False

    def _verify_proof_of_work(self, challenge_data: str, solution: str, difficulty: int) -> bool:
        """Verify proof of work solution."""
        combined = f"{challenge_data}:{solution}"
        hash_result = hashlib.sha256(combined.encode()).hexdigest()
        return hash_result.startswith('0' * difficulty)

    async def verify_hardware_claims(
        self,
        node_id: str,
        hardware_claims: Dict[str, Any],
        proof_of_benchmark: str,
        signature: str
    ) -> Optional[HardwareVerification]:
        """Verify hardware capabilities claimed by a node."""
        try:
            # Verify signature
            claims_json = json.dumps(hardware_claims, sort_keys=True)
            data_to_verify = f"{claims_json}:{proof_of_benchmark}"

            if not await self.verify_node_identity(node_id, signature, data_to_verify):
                return None

            # Verify proof of benchmark with cryptographic validation
            if not await self._verify_benchmark_proof(proof_of_benchmark, hardware_claims):
                return None

            # Create hardware verification
            verification = HardwareVerification(
                node_id=node_id,
                cpu_model=hardware_claims.get('cpu_model', 'Unknown'),
                cpu_cores=hardware_claims.get('cpu_cores', 0),
                memory_gb=hardware_claims.get('memory_gb', 0),
                gpu_model=hardware_claims.get('gpu_model'),
                gpu_memory_gb=hardware_claims.get('gpu_memory_gb'),
                storage_gb=hardware_claims.get('storage_gb', 0),
                network_speed_mbps=hardware_claims.get('network_speed_mbps', 0),
                verified_at=datetime.now(),
                proof_of_work=proof_of_benchmark,
                signature=signature
            )

            self.hardware_verifications[node_id] = verification

            # Update reputation for hardware verification
            await self._update_reputation_for_verification(node_id, True)

            self.logger.info(f"Hardware verified for node {node_id}")
            return verification

        except Exception as e:
            self.logger.error(f"Error verifying hardware for {node_id}: {e}")
            return None

    async def _verify_benchmark_proof(self, proof: str, claims: Dict[str, Any]) -> bool:
        """Verify proof of benchmark execution with cryptographic validation."""
        try:
            proof_data = json.loads(proof)

            # Verify required fields
            required_fields = ['benchmark_results', 'signature', 'timestamp', 'node_id', 'hardware_hash']
            if not all(field in proof_data for field in required_fields):
                return False

            # Verify timestamp is recent (within last hour)
            proof_timestamp = proof_data.get('timestamp', 0)
            current_time = datetime.now().timestamp()
            if abs(current_time - proof_timestamp) > 3600:  # 1 hour
                return False

            # Verify hardware hash matches claims
            expected_hardware_hash = self._calculate_hardware_hash(claims)
            if proof_data.get('hardware_hash') != expected_hardware_hash:
                return False

            # Verify benchmark results are reasonable
            benchmark_results = proof_data.get('benchmark_results', {})
            if not self._validate_benchmark_results(benchmark_results, claims):
                return False

            # Verify signature of the proof
            proof_signature = proof_data.get('signature')
            proof_without_sig = {k: v for k, v in proof_data.items() if k != 'signature'}
            proof_json = json.dumps(proof_without_sig, sort_keys=True)

            # Verify against node's public key
            node_id = proof_data.get('node_id')
            if not node_id or not await self.verify_node_identity(node_id, proof_signature, proof_json):
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Benchmark proof verification failed: {e}")
            return False

    def _calculate_hardware_hash(self, claims: Dict[str, Any]) -> str:
        """Calculate hardware hash from claims."""
        # Create a deterministic string from hardware claims
        hardware_string = f"{claims.get('cpu_model', '')}:{claims.get('cpu_cores', 0)}:{claims.get('memory_gb', 0)}:{claims.get('gpu_model', '')}:{claims.get('gpu_memory_gb', 0)}:{claims.get('storage_gb', 0)}"
        return hashlib.sha256(hardware_string.encode()).hexdigest()

    def _validate_benchmark_results(self, results: Dict[str, Any], claims: Dict[str, Any]) -> bool:
        """Validate that benchmark results are reasonable for claimed hardware."""
        try:
            # CPU benchmark validation
            cpu_score = results.get('cpu_score', 0)
            claimed_cores = claims.get('cpu_cores', 1)

            # Basic sanity checks
            if cpu_score <= 0 or cpu_score > 100000:  # Unrealistic CPU score
                return False

            # Memory benchmark validation
            memory_score = results.get('memory_score', 0)
            claimed_memory = claims.get('memory_gb', 1)

            if memory_score <= 0 or memory_score > 100000:
                return False

            # GPU benchmark validation (if GPU claimed)
            if claims.get('gpu_model'):
                gpu_score = results.get('gpu_score', 0)
                if gpu_score <= 0 or gpu_score > 1000000:  # Unrealistic GPU score
                    return False

            # Network benchmark validation
            network_score = results.get('network_score', 0)
            if network_score <= 0 or network_score > 10000:  # Mbps unrealistic
                return False

            # Storage benchmark validation
            storage_score = results.get('storage_score', 0)
            if storage_score <= 0 or storage_score > 10000:  # MB/s unrealistic
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Benchmark results validation failed: {e}")
            return False

    async def update_node_reputation(
        self,
        node_id: str,
        contribution_success: bool,
        reward_amount: float = 0.0
    ):
        """Update node reputation based on contribution results."""
        try:
            reputation = self.reputations.get(node_id)
            if not reputation:
                return

            reputation.total_contributions += 1
            reputation.last_activity = datetime.now()

            if contribution_success:
                reputation.successful_contributions += 1
                reputation.total_rewards_earned += reward_amount

                # Increase reputation score
                reputation.reputation_score = min(1.0, reputation.reputation_score + 0.05)
            else:
                reputation.failed_contributions += 1

                # Decrease reputation score
                reputation.reputation_score = max(0.0, reputation.reputation_score - 0.1)

            # Update trust level
            reputation.trust_level = self._calculate_trust_level(reputation)

            # Check for sanctions
            await self._check_sanctions(node_id, reputation)

            self.logger.debug(f"Updated reputation for {node_id}: {reputation.reputation_score:.3f}")

        except Exception as e:
            self.logger.error(f"Error updating reputation for {node_id}: {e}")

    def _calculate_trust_level(self, reputation: NodeReputation) -> str:
        """Calculate trust level based on reputation score and history."""
        score = reputation.reputation_score
        total_contribs = reputation.total_contributions

        if score >= 0.9 and total_contribs >= 100:
            return 'elite'
        elif score >= 0.8 and total_contribs >= 50:
            return 'trusted'
        elif score >= 0.6 and total_contribs >= 10:
            return 'verified'
        elif score >= 0.3:
            return 'basic'
        else:
            return 'untrusted'

    async def _check_sanctions(self, node_id: str, reputation: NodeReputation):
        """Check if node should be sanctioned."""
        # Remove expired sanctions
        reputation.sanctions = [
            s for s in reputation.sanctions
            if datetime.fromisoformat(s['expires_at']) > datetime.now()
        ]

        # Check for sanction conditions
        if reputation.failed_contributions > reputation.successful_contributions * 3:
            # Too many failures
            await self._apply_sanction(node_id, 'excessive_failures', 7)  # 7 days

        if reputation.reputation_score < 0.1:
            # Very low reputation
            await self._apply_sanction(node_id, 'low_reputation', 30)  # 30 days

        if len(reputation.sanctions) >= self.max_sanctions:
            # Permanent ban
            await self._apply_sanction(node_id, 'permanent_ban', 36500)  # 100 years

    async def _apply_sanction(self, node_id: str, reason: str, days: int):
        """Apply a sanction to a node."""
        reputation = self.reputations[node_id]

        # Check if sanction already exists
        for sanction in reputation.sanctions:
            if sanction['reason'] == reason:
                return  # Already sanctioned for this reason

        sanction = {
            'reason': reason,
            'applied_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=days)).isoformat(),
            'severity': 'ban' if days > 30 else 'warning'
        }

        reputation.sanctions.append(sanction)

        self.logger.warning(f"Applied sanction to {node_id}: {reason} ({days} days)")

    async def _update_reputation_for_verification(self, node_id: str, success: bool):
        """Update reputation based on verification success."""
        reputation = self.reputations.get(node_id)
        if reputation:
            if success:
                reputation.reputation_score = min(1.0, reputation.reputation_score + 0.02)
            else:
                reputation.reputation_score = max(0.0, reputation.reputation_score - 0.05)

    def is_node_eligible(self, node_id: str) -> Tuple[bool, str]:
        """Check if a node is eligible to participate."""
        reputation = self.reputations.get(node_id)
        if not reputation:
            return False, "Node not registered"

        # Check reputation score
        if reputation.reputation_score < self.min_reputation_score:
            return False, f"Reputation score too low: {reputation.reputation_score:.3f}"

        # Check active sanctions
        active_sanctions = [
            s for s in reputation.sanctions
            if datetime.fromisoformat(s['expires_at']) > datetime.now()
        ]

        if active_sanctions:
            worst_sanction = max(active_sanctions, key=lambda s: s['severity'])
            return False, f"Active sanction: {worst_sanction['reason']}"

        # Check identity validity
        identity = self.identities.get(node_id)
        if not identity or datetime.now() > identity.expires_at:
            return False, "Identity expired or invalid"

        return True, "Eligible"

    def get_node_reputation(self, node_id: str) -> Optional[NodeReputation]:
        """Get reputation information for a node."""
        return self.reputations.get(node_id)

    def get_node_identity(self, node_id: str) -> Optional[NodeIdentity]:
        """Get identity information for a node."""
        return self.identities.get(node_id)

    def get_hardware_verification(self, node_id: str) -> Optional[HardwareVerification]:
        """Get hardware verification for a node."""
        return self.hardware_verifications.get(node_id)



    def _sign_identity(self, node_id: str, public_key_pem: str, certificate_pem: str) -> str:
        """Create self-signature of node identity using CA."""
        data = f"{node_id}:{public_key_pem}:{certificate_pem}"
        return self.ca.sign_data(data)

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification system statistics."""
        total_nodes = len(self.identities)
        verified_nodes = len([r for r in self.reputations.values() if r.trust_level in ['verified', 'trusted', 'elite']])
        sanctioned_nodes = len([r for r in self.reputations.values() if r.sanctions])

        avg_reputation = sum(r.reputation_score for r in self.reputations.values()) / max(len(self.reputations), 1)

        return {
            'total_nodes': total_nodes,
            'verified_nodes': verified_nodes,
            'sanctioned_nodes': sanctioned_nodes,
            'average_reputation': avg_reputation,
            'active_challenges': len(self.active_challenges),
            'hardware_verifications': len(self.hardware_verifications)
        }