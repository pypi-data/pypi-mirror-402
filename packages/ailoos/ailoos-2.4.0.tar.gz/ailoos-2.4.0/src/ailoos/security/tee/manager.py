"""
TEE Security Manager (Trusted Execution Environment)
Simulates SGX/SEV Enclave Attestation for Proof-of-Compute.

In a real environment, this connects to /dev/sgx or similar kernel drivers.
Here we simulate secure enclave storage and precise execution measurement.
"""

import hashlib
import json
import logging
import time
import secrets
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

logger = logging.getLogger(__name__)

class TeeManager:
    """
    Manages Trusted Execution Environment (TEE) operations.
    Generates cryptographic proofs that computation occurred on this specific hardware.
    """
    
    def __init__(self):
        self.is_simulated = True # On Mac we must simulate
        self._enclave_id = secrets.token_hex(8)
        # "Silicon Key" - In reality, baked into the CPU. We generate one per session.
        self._silicon_key = ec.generate_private_key(ec.SECP256R1())
        logger.info(f"🛡️ TEE Enclave Initialized. ID: {self._enclave_id}")

    def generate_proof_of_compute(self, 
                                task_id: str, 
                                computation_hash: str, 
                                metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Generates a simplified SGX-style Quote (Attestation).
        Binds the Task ID + Result Hash + Performance Metrics to the Hardware Key.
        """
        timestamp = time.time()
        
        # 1. Create Report Body (What happened inside the enclave)
        report_data = {
            "enclave_id": self._enclave_id,
            "task_id": task_id,
            "computation_hash": computation_hash,
            "metrics": metrics,
            "timestamp": timestamp,
            "nonce": secrets.token_hex(4)
        }
        
        # Canonical JSON
        report_json = json.dumps(report_data, sort_keys=True)
        
        # 2. Sign with Silicon Key (The "Quote")
        signature = self._silicon_key.sign(
            report_json.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        
        # 3. Public Key for Verification (In real SGX, this connects to Intel Attestation Service)
        public_key_pem = self._silicon_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        proof = {
            "version": "empoorio_tee_v1",
            "type": "SIMULATED_SGX",
            "report": report_data,
            "signature": signature.hex(),
            "attestation_key": public_key_pem
        }
        
        logger.info(f"🔐 Proof of Compute Generated for Task {task_id[:8]}...")
        return proof

    def verify_proof(self, proof: Dict[str, Any]) -> bool:
        """
        Verifies a Proof of Compute.
        Checks signature validty and report integrity.
        """
        try:
            report = proof.get("report")
            signature = bytes.fromhex(proof.get("signature"))
            pub_key_pem = proof.get("attestation_key")
            
            # Reconstruct signed data
            report_json = json.dumps(report, sort_keys=True).encode()
            
            # Load Public Key
            public_key = serialization.load_pem_public_key(pub_key_pem.encode())
            
            # Verify Signature
            public_key.verify(
                signature,
                report_json,
                ec.ECDSA(hashes.SHA256())
            )
            
            logger.info(f"✅ TEE Proof Verified: {report['task_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Invalid TEE Proof: {e}")
            return False

# Global Instance
tee_manager = TeeManager()
