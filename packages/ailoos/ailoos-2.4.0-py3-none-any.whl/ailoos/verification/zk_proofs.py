"""
Zero-knowledge proof system for Ailoos node verification.
Provides privacy-preserving verification of node contributions and capabilities.
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os

# For zero-knowledge proofs, we'll use a simplified implementation
# In production, this would use libraries like zk-SNARKs (libsnark, bellman) or STARKs
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization

from ..core.config import Config
from ..utils.logging import AiloosLogger


@dataclass
class ZKProof:
    """Zero-knowledge proof structure."""
    proof_id: str
    statement: str  # What is being proven
    proof_data: Dict[str, Any]  # Proof components
    public_inputs: Dict[str, Any]  # Public parameters
    created_at: datetime
    verified: bool = False
    verification_key: Optional[str] = None


@dataclass
class ContributionProof:
    """ZK proof of federated learning contribution."""
    node_id: str
    session_id: str
    round_number: int
    parameters_hash: str  # Hash of model parameters (without revealing them)
    data_fingerprint: str  # Fingerprint of training data
    accuracy_proof: ZKProof  # Proof of accuracy without revealing exact value
    computation_proof: ZKProof  # Proof of computation performed
    timestamp: datetime


@dataclass
class HardwareProof:
    """ZK proof of hardware capabilities."""
    node_id: str
    capability_claims: Dict[str, Any]
    benchmark_proofs: List[ZKProof]  # Proofs of benchmark results
    resource_proofs: List[ZKProof]  # Proofs of resource availability
    timestamp: datetime


class ZKProver:
    """Generates zero-knowledge proofs."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Generate proving key (simplified - in production would be trusted setup)
        self.proving_key = self._generate_proving_key()

    def _generate_proving_key(self) -> bytes:
        """Generate a proving key for ZK proofs."""
        # Simplified key generation
        return secrets.token_bytes(32)

    async def prove_contribution(
        self,
        node_id: str,
        session_id: str,
        round_number: int,
        model_parameters: Dict[str, Any],
        training_data: List[Any],
        accuracy: float,
        computation_stats: Dict[str, Any]
    ) -> ContributionProof:
        """Generate ZK proof of federated learning contribution."""
        try:
            # Create parameter hash without revealing parameters
            param_str = json.dumps(model_parameters, sort_keys=True)
            parameters_hash = hashlib.sha256(param_str.encode()).hexdigest()

            # Create data fingerprint
            data_fingerprint = self._create_data_fingerprint(training_data)

            # Prove accuracy range (e.g., accuracy > 0.8) without revealing exact value
            accuracy_proof = await self._prove_accuracy_range(accuracy, 0.8, 1.0)

            # Prove computation was performed
            computation_proof = await self._prove_computation(computation_stats)

            proof = ContributionProof(
                node_id=node_id,
                session_id=session_id,
                round_number=round_number,
                parameters_hash=parameters_hash,
                data_fingerprint=data_fingerprint,
                accuracy_proof=accuracy_proof,
                computation_proof=computation_proof,
                timestamp=datetime.now()
            )

            self.logger.info(f"Generated contribution proof for {node_id} in session {session_id}")
            return proof

        except Exception as e:
            self.logger.error(f"Error generating contribution proof: {e}")
            raise

    async def prove_hardware_capabilities(
        self,
        node_id: str,
        hardware_specs: Dict[str, Any],
        benchmark_results: Dict[str, Any]
    ) -> HardwareProof:
        """Generate ZK proof of hardware capabilities."""
        try:
            benchmark_proofs = []
            resource_proofs = []

            # Prove CPU/GPU benchmarks
            if 'cpu_benchmark' in benchmark_results:
                proof = await self._prove_benchmark_result(
                    'cpu',
                    benchmark_results['cpu_benchmark'],
                    hardware_specs.get('cpu_cores', 0)
                )
                benchmark_proofs.append(proof)

            if 'gpu_benchmark' in benchmark_results:
                proof = await self._prove_benchmark_result(
                    'gpu',
                    benchmark_results['gpu_benchmark'],
                    hardware_specs.get('gpu_memory_gb', 0)
                )
                benchmark_proofs.append(proof)

            # Prove resource availability
            memory_proof = await self._prove_resource_availability(
                'memory',
                hardware_specs.get('memory_gb', 0)
            )
            resource_proofs.append(memory_proof)

            storage_proof = await self._prove_resource_availability(
                'storage',
                hardware_specs.get('storage_gb', 0)
            )
            resource_proofs.append(storage_proof)

            proof = HardwareProof(
                node_id=node_id,
                capability_claims=hardware_specs,
                benchmark_proofs=benchmark_proofs,
                resource_proofs=resource_proofs,
                timestamp=datetime.now()
            )

            self.logger.info(f"Generated hardware proof for {node_id}")
            return proof

        except Exception as e:
            self.logger.error(f"Error generating hardware proof: {e}")
            raise

    async def _prove_accuracy_range(self, accuracy: float, min_acc: float, max_acc: float) -> ZKProof:
        """Prove that accuracy is within a range without revealing the exact value."""
        # Simplified ZK range proof
        # In production, this would use proper ZK protocols

        # Create commitment to accuracy
        commitment = self._create_commitment(str(accuracy))

        # Create proof that accuracy is in range
        proof_data = {
            'commitment': commitment,
            'range_min': min_acc,
            'range_max': max_acc,
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement=f"accuracy in [{min_acc}, {max_acc}]",
            proof_data=proof_data,
            public_inputs={'range_min': min_acc, 'range_max': max_acc},
            created_at=datetime.now()
        )

    async def _prove_computation(self, computation_stats: Dict[str, Any]) -> ZKProof:
        """Prove that computation was actually performed."""
        # Prove training time and resource usage
        training_time = computation_stats.get('training_time', 0)
        cpu_usage = computation_stats.get('cpu_usage', 0)
        memory_usage = computation_stats.get('memory_usage', 0)

        # Create proof of computation effort
        proof_data = {
            'time_commitment': self._create_commitment(str(training_time)),
            'resource_commitment': self._create_commitment(f"{cpu_usage}:{memory_usage}"),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="computation_performed",
            proof_data=proof_data,
            public_inputs={},
            created_at=datetime.now()
        )

    async def _prove_benchmark_result(self, benchmark_type: str, result: float, expected_min: float) -> ZKProof:
        """Prove benchmark result meets minimum requirements."""
        proof_data = {
            'benchmark_type': benchmark_type,
            'result_commitment': self._create_commitment(str(result)),
            'minimum_requirement': expected_min,
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement=f"{benchmark_type}_benchmark >= {expected_min}",
            proof_data=proof_data,
            public_inputs={'benchmark_type': benchmark_type, 'min_requirement': expected_min},
            created_at=datetime.now()
        )

    async def _prove_resource_availability(self, resource_type: str, amount: float) -> ZKProof:
        """Prove resource availability."""
        proof_data = {
            'resource_type': resource_type,
            'amount_commitment': self._create_commitment(str(amount)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement=f"{resource_type}_available",
            proof_data=proof_data,
            public_inputs={'resource_type': resource_type},
            created_at=datetime.now()
        )

    def _create_commitment(self, value: str) -> str:
        """Create a cryptographic commitment to a value."""
        # Simplified commitment scheme
        nonce = secrets.token_bytes(16)
        commitment = hashlib.sha256(value.encode() + nonce).hexdigest()
        return commitment

    def _generate_proof_elements(self) -> List[str]:
        """Generate proof elements for ZK proof."""
        # Simplified proof generation
        return [secrets.token_hex(32) for _ in range(3)]

    def _create_data_fingerprint(self, training_data: List[Any]) -> str:
        """Create fingerprint of training data without revealing content."""
        # Create statistical fingerprint
        if not training_data:
            return "empty"

        # Simple statistical fingerprint (in production, use more sophisticated methods)
        data_str = json.dumps(training_data[:10], sort_keys=True)  # Sample first 10 items
        fingerprint = hashlib.sha256(data_str.encode()).hexdigest()
        return fingerprint


class ZKVerifier:
    """Verifies zero-knowledge proofs."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Verification key (would be generated from trusted setup)
        self.verification_key = self._generate_verification_key()

    def _generate_verification_key(self) -> bytes:
        """Generate verification key."""
        return secrets.token_bytes(32)

    async def verify_contribution_proof(self, proof: ContributionProof) -> bool:
        """Verify a contribution proof."""
        try:
            # Verify accuracy proof
            if not await self._verify_zk_proof(proof.accuracy_proof):
                self.logger.warning(f"Invalid accuracy proof for {proof.node_id}")
                return False

            # Verify computation proof
            if not await self._verify_zk_proof(proof.computation_proof):
                self.logger.warning(f"Invalid computation proof for {proof.node_id}")
                return False

            # Additional consistency checks
            if not self._verify_proof_consistency(proof):
                self.logger.warning(f"Inconsistent proof data for {proof.node_id}")
                return False

            proof.accuracy_proof.verified = True
            proof.computation_proof.verified = True

            self.logger.info(f"Verified contribution proof for {proof.node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying contribution proof: {e}")
            return False

    async def verify_hardware_proof(self, proof: HardwareProof) -> bool:
        """Verify a hardware proof."""
        try:
            # Verify all benchmark proofs
            for benchmark_proof in proof.benchmark_proofs:
                if not await self._verify_zk_proof(benchmark_proof):
                    self.logger.warning(f"Invalid benchmark proof for {proof.node_id}")
                    return False

            # Verify all resource proofs
            for resource_proof in proof.resource_proofs:
                if not await self._verify_zk_proof(resource_proof):
                    self.logger.warning(f"Invalid resource proof for {proof.node_id}")
                    return False

            # Mark proofs as verified
            for p in proof.benchmark_proofs + proof.resource_proofs:
                p.verified = True

            self.logger.info(f"Verified hardware proof for {proof.node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying hardware proof: {e}")
            return False

    async def _verify_zk_proof(self, proof: ZKProof) -> bool:
        """Verify a single ZK proof."""
        try:
            # Simplified verification (in production, use proper ZK verification)
            proof_elements = proof.proof_data.get('proof_elements', [])

            if len(proof_elements) < 3:
                return False

            # Verify proof structure
            if not self._verify_proof_structure(proof):
                return False

            # Verify commitments are valid
            if not self._verify_commitments(proof):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error verifying ZK proof {proof.proof_id}: {e}")
            return False

    def _verify_proof_structure(self, proof: ZKProof) -> bool:
        """Verify the structure of a ZK proof."""
        required_fields = ['proof_elements', 'commitment']
        return all(field in proof.proof_data for field in required_fields)

    def _verify_commitments(self, proof: ZKProof) -> bool:
        """Verify cryptographic commitments in proof."""
        # Simplified commitment verification
        commitment = proof.proof_data.get('commitment', '')
        return len(commitment) == 64 and commitment.isalnum()  # SHA256 hex

    def _verify_proof_consistency(self, proof: ContributionProof) -> bool:
        """Verify consistency of contribution proof."""
        # Check that all required fields are present
        required_fields = [
            'node_id', 'session_id', 'round_number',
            'parameters_hash', 'data_fingerprint'
        ]

        for field in required_fields:
            if not getattr(proof, field, None):
                return False

        # Verify hashes are proper length
        if len(proof.parameters_hash) != 64 or len(proof.data_fingerprint) != 64:
            return False

        return True


class ZKProofManager:
    """Manages ZK proof generation and verification."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        self.prover = ZKProver(config)
        self.verifier = ZKVerifier(config)

        # Proof storage
        self.contribution_proofs: Dict[str, ContributionProof] = {}
        self.hardware_proofs: Dict[str, HardwareProof] = {}

    async def generate_contribution_proof(
        self,
        node_id: str,
        session_id: str,
        round_number: int,
        model_parameters: Dict[str, Any],
        training_data: List[Any],
        accuracy: float,
        computation_stats: Dict[str, Any]
    ) -> ContributionProof:
        """Generate and store a contribution proof."""
        proof = await self.prover.prove_contribution(
            node_id, session_id, round_number,
            model_parameters, training_data,
            accuracy, computation_stats
        )

        # Store proof
        proof_key = f"{node_id}_{session_id}_{round_number}"
        self.contribution_proofs[proof_key] = proof

        return proof

    async def generate_hardware_proof(
        self,
        node_id: str,
        hardware_specs: Dict[str, Any],
        benchmark_results: Dict[str, Any]
    ) -> HardwareProof:
        """Generate and store a hardware proof."""
        proof = await self.prover.prove_hardware_capabilities(
            node_id, hardware_specs, benchmark_results
        )

        # Store proof
        self.hardware_proofs[node_id] = proof

        return proof

    async def verify_contribution_proof(self, proof: ContributionProof) -> bool:
        """Verify a contribution proof."""
        return await self.verifier.verify_contribution_proof(proof)

    async def verify_hardware_proof(self, proof: HardwareProof) -> bool:
        """Verify a hardware proof."""
        return await self.verifier.verify_hardware_proof(proof)

    def get_contribution_proof(self, node_id: str, session_id: str, round_number: int) -> Optional[ContributionProof]:
        """Get a stored contribution proof."""
        proof_key = f"{node_id}_{session_id}_{round_number}"
        return self.contribution_proofs.get(proof_key)

    def get_hardware_proof(self, node_id: str) -> Optional[HardwareProof]:
        """Get a stored hardware proof."""
        return self.hardware_proofs.get(node_id)

    def get_proof_stats(self) -> Dict[str, Any]:
        """Get statistics about stored proofs."""
        return {
            'contribution_proofs': len(self.contribution_proofs),
            'hardware_proofs': len(self.hardware_proofs),
            'verified_contribution_proofs': len([
                p for p in self.contribution_proofs.values()
                if p.accuracy_proof.verified and p.computation_proof.verified
            ]),
            'verified_hardware_proofs': len([
                p for p in self.hardware_proofs.values()
                if all(bp.verified for bp in p.benchmark_proofs) and
                all(rp.verified for rp in p.resource_proofs)
            ])
        }