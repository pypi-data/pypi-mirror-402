import logging
from phe import paillier
from typing import Optional, Union
import math

logger = logging.getLogger(__name__)

class HomomorphicEncryptionManager:
    """
    Manager for homomorphic encryption using Paillier cryptosystem.
    Supports secure addition of encrypted values without decryption.
    Optimized for federated learning aggregation.
    """

    def __init__(self, precision: int = 6):
        """
        Initialize the homomorphic encryption manager.

        Args:
            precision: Number of decimal places for float handling (default: 6)
        """
        self.precision = precision
        self.public_key: Optional[paillier.PaillierPublicKey] = None
        self.private_key: Optional[paillier.PaillierPrivateKey] = None
        self.accumulated_sum: Optional[paillier.EncryptedNumber] = None
        self._generate_keys()
        logger.info("HomomorphicEncryptionManager initialized with precision %d", precision)

    def _generate_keys(self) -> None:
        """
        Generate Paillier public and private keys.
        """
        try:
            self.public_key, self.private_key = paillier.generate_paillier_keypair()
            logger.info("Paillier keypair generated successfully")
        except Exception as e:
            logger.error("Failed to generate Paillier keypair: %s", str(e))
            raise RuntimeError(f"Key generation failed: {e}")

    def get_public_key(self) -> paillier.PaillierPublicKey:
        """
        Get the public key for encryption.

        Returns:
            PaillierPublicKey: The public key
        """
        if self.public_key is None:
            raise RuntimeError("Public key not available")
        return self.public_key

    def encrypt(self, value: Union[int, float]) -> paillier.EncryptedNumber:
        """
        Encrypt a numeric value (int or float).

        Args:
            value: The value to encrypt

        Returns:
            EncryptedNumber: The encrypted value
        """
        if self.public_key is None:
            raise RuntimeError("Public key not available for encryption")

        try:
            if isinstance(value, float):
                # Convert float to int with precision
                scaled_value = int(value * (10 ** self.precision))
            else:
                scaled_value = value

            encrypted = self.public_key.encrypt(scaled_value)
            logger.debug("Value encrypted successfully")
            return encrypted
        except Exception as e:
            logger.error("Encryption failed: %s", str(e))
            raise RuntimeError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_value: paillier.EncryptedNumber) -> Union[int, float]:
        """
        Decrypt an encrypted value.

        Args:
            encrypted_value: The encrypted value to decrypt

        Returns:
            Union[int, float]: The decrypted value
        """
        if self.private_key is None:
            raise RuntimeError("Private key not available for decryption")

        try:
            decrypted_scaled = self.private_key.decrypt(encrypted_value)
            # Convert back to float if it was originally a float
            decrypted = decrypted_scaled / (10 ** self.precision)
            logger.debug("Value decrypted successfully")
            return decrypted
        except Exception as e:
            logger.error("Decryption failed: %s", str(e))
            raise RuntimeError(f"Decryption failed: {e}")

    def add_to_sum(self, encrypted_value: paillier.EncryptedNumber) -> None:
        """
        Add an encrypted value to the accumulated sum without decryption.

        Args:
            encrypted_value: The encrypted value to add
        """
        try:
            if self.accumulated_sum is None:
                self.accumulated_sum = encrypted_value
            else:
                self.accumulated_sum = self.accumulated_sum + encrypted_value
            logger.debug("Encrypted value added to accumulated sum")
        except Exception as e:
            logger.error("Failed to add encrypted value to sum: %s", str(e))
            raise RuntimeError(f"Addition to sum failed: {e}")

    def get_current_sum(self) -> Optional[paillier.EncryptedNumber]:
        """
        Get the current accumulated sum (encrypted).

        Returns:
            Optional[EncryptedNumber]: The accumulated encrypted sum, or None if no values added
        """
        return self.accumulated_sum

    def get_decrypted_sum(self) -> Union[int, float, None]:
        """
        Get the decrypted accumulated sum.

        Returns:
            Union[int, float, None]: The decrypted sum, or None if no values added
        """
        if self.accumulated_sum is None:
            return None
        return self.decrypt(self.accumulated_sum)

    def reset_sum(self) -> None:
        """
        Reset the accumulated sum to None.
        """
        self.accumulated_sum = None
        logger.info("Accumulated sum reset")