import logging
import json
import hashlib
from typing import Dict, Any, Optional
from cryptography.x509 import load_pem_x509_certificate, Certificate
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import numpy as np

logger = logging.getLogger(__name__)

class WeightValidator:
    """
    Validator for cryptographic integrity of federated learning model weights.
    Implements X.509 signature verification, anti-poisoning bounds checking,
    proof-of-work for anti-Sybil protection, and weight structure validation.
    """

    def __init__(self, node_certificates: Dict[str, str], weight_bounds: tuple = (-100.0, 100.0), pow_difficulty: int = 4):
        """
        Initialize the WeightValidator.

        Args:
            node_certificates: Dict of node_id to PEM-encoded X.509 certificate string
            weight_bounds: Tuple of (min, max) bounds for weight values (anti-poisoning)
            pow_difficulty: Number of leading zeros required for proof-of-work
        """
        self.node_certificates: Dict[str, Certificate] = {}
        for node_id, cert_pem in node_certificates.items():
            try:
                self.node_certificates[node_id] = load_pem_x509_certificate(cert_pem.encode())
            except Exception as e:
                logger.error(f"Failed to load certificate for node {node_id}: {e}")
                raise ValueError(f"Invalid certificate for node {node_id}")

        self.weight_bounds = weight_bounds
        self.pow_difficulty = pow_difficulty
        self.logger = logger

    def validate_weight_integrity(self, weights: Dict[str, np.ndarray], signature: bytes, node_id: str, pow_proof: Dict[str, Any]) -> bool:
        """
        Validate the complete integrity of model weights.

        Args:
            weights: Dictionary of layer names to numpy arrays
            signature: Digital signature of the weights
            node_id: Identifier of the submitting node
            pow_proof: Proof-of-work data {'nonce': int, 'timestamp': int}

        Returns:
            bool: True if all validations pass, False otherwise
        """
        try:
            # Verify digital signature
            if not self._verify_signature(weights, signature, node_id):
                self.logger.warning(f"Signature verification failed for node {node_id}")
                return False

            # Check weight bounds for anti-poisoning
            if not self._check_weight_bounds(weights):
                self.logger.warning(f"Weight bounds check failed for node {node_id}")
                return False

            # Verify proof-of-work for anti-Sybil
            if not self._verify_pow_proof(pow_proof, node_id):
                self.logger.warning(f"Proof-of-work verification failed for node {node_id}")
                return False

            # Validate weight structure
            if not self._validate_weight_structure(weights):
                self.logger.warning(f"Weight structure validation failed for node {node_id}")
                return False

            self.logger.info(f"Weight integrity validation passed for node {node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error during weight validation for node {node_id}: {e}")
            return False

    def _verify_signature(self, weights: Dict[str, np.ndarray], signature: bytes, node_id: str) -> bool:
        """
        Verify X.509 digital signature of the weights.

        Args:
            weights: Model weights to verify
            signature: Signature bytes
            node_id: Node identifier

        Returns:
            bool: True if signature is valid
        """
        cert = self.node_certificates.get(node_id)
        if not cert:
            self.logger.error(f"No certificate found for node {node_id}")
            return False

        public_key = cert.public_key()
        if not isinstance(public_key, rsa.RSAPublicKey):
            self.logger.error(f"Unsupported public key type for node {node_id}")
            return False

        # Serialize weights deterministically for signing
        try:
            weight_data = json.dumps({k: v.tolist() for k, v in weights.items()}, sort_keys=True)
            weight_bytes = weight_data.encode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to serialize weights for node {node_id}: {e}")
            return False

        try:
            public_key.verify(signature, weight_bytes, padding.PKCS1v15(), hashes.SHA256())
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            self.logger.error(f"Signature verification error for node {node_id}: {e}")
            return False

    def _check_weight_bounds(self, weights: Dict[str, np.ndarray]) -> bool:
        """
        Check if all weight values are within acceptable bounds (anti-poisoning).

        Args:
            weights: Model weights

        Returns:
            bool: True if all values are within bounds
        """
        min_val, max_val = self.weight_bounds
        for layer_name, weight_array in weights.items():
            if not isinstance(weight_array, np.ndarray):
                self.logger.error(f"Weight for layer {layer_name} is not a numpy array")
                return False
            if weight_array.size == 0:
                continue  # Allow empty arrays
            if np.any(np.isnan(weight_array)) or np.any(np.isinf(weight_array)):
                self.logger.error(f"Invalid values (NaN/Inf) in layer {layer_name}")
                return False
            if np.any(weight_array < min_val) or np.any(weight_array > max_val):
                self.logger.warning(f"Weight values out of bounds in layer {layer_name}")
                return False
        return True

    def _verify_pow_proof(self, pow_proof: Dict[str, Any], node_id: str) -> bool:
        """
        Verify proof-of-work to prevent Sybil attacks.

        Args:
            pow_proof: Dict containing 'nonce' and 'timestamp'
            node_id: Node identifier

        Returns:
            bool: True if proof-of-work is valid
        """
        try:
            nonce = pow_proof.get('nonce')
            timestamp = pow_proof.get('timestamp')
            if not isinstance(nonce, int) or not isinstance(timestamp, int):
                return False

            # Create challenge string
            challenge = f"{node_id}:{timestamp}:{nonce}"
            hash_digest = hashlib.sha256(challenge.encode('utf-8')).hexdigest()

            # Check if hash has required number of leading zeros
            return hash_digest.startswith('0' * self.pow_difficulty)

        except Exception as e:
            self.logger.error(f"Proof-of-work verification error for node {node_id}: {e}")
            return False

    def _validate_weight_structure(self, weights: Dict[str, np.ndarray]) -> bool:
        """
        Validate the structure of the weights dictionary.

        Args:
            weights: Model weights

        Returns:
            bool: True if structure is valid
        """
        if not isinstance(weights, dict) or len(weights) == 0:
            return False

        for layer_name, weight_array in weights.items():
            if not isinstance(layer_name, str) or not isinstance(weight_array, np.ndarray):
                return False
            if weight_array.ndim > 2:  # Allow 1D and 2D arrays
                return False
        return True

    def get_node_certificate(self, node_id: str) -> Optional[Certificate]:
        """
        Retrieve the X.509 certificate for a node.

        Args:
            node_id: Node identifier

        Returns:
            Certificate or None if not found
        """
        return self.node_certificates.get(node_id)

    def update_node_certificate(self, node_id: str, cert_pem: str) -> bool:
        """
        Update or add a certificate for a node.

        Args:
            node_id: Node identifier
            cert_pem: PEM-encoded certificate

        Returns:
            bool: True if update successful
        """
        try:
            self.node_certificates[node_id] = load_pem_x509_certificate(cert_pem.encode())
            self.logger.info(f"Certificate updated for node {node_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update certificate for node {node_id}: {e}")
            return False