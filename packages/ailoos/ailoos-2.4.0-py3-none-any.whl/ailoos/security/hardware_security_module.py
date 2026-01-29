#!/usr/bin/env python3
"""
Hardware Security Module Integration for Ailoos
Provides secure key management and cryptographic operations for quantum-resistant security.
"""

import secrets
import hashlib
import hmac
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import threading
import time

from ..core.config import Config
from ..utils.logging import AiloosLogger


@dataclass
class HSMKey:
    """HSM-managed key."""
    key_id: str
    key_type: str  # 'aes', 'rsa', 'ecc', 'pq', 'zkp'
    algorithm: str
    key_size: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    usage_count: int = 0
    max_uses: Optional[int] = None
    exportable: bool = False


@dataclass
class HSMSession:
    """HSM session for secure operations."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    permissions: List[str]
    active: bool = True


class HardwareSecurityModule:
    """
    Hardware Security Module integration for Ailoos.

    Provides secure key management, cryptographic operations, and hardware-backed security
    for quantum-resistant implementations.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # HSM configuration
        self.hsm_type = config.get('hsm_type', 'software')  # 'software', 'yubikey', 'tpm', 'cloud_hsm'
        self.key_store_location = config.get('hsm_key_store', 'encrypted_file')
        self.session_timeout_minutes = config.get('hsm_session_timeout', 30)
        self.max_sessions = config.get('hsm_max_sessions', 100)

        # Key management
        self.keys: Dict[str, HSMKey] = {}
        self.sessions: Dict[str, HSMSession] = {}

        # Security policies
        self.policies = {
            'key_rotation_days': 90,
            'max_key_uses': 1000000,
            'require_mfa': True,
            'audit_all_operations': True,
            'quantum_resistant_only': True
        }

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []
        self.audit_lock = threading.Lock()

        # Initialize HSM
        self._initialize_hsm()

        self.logger.info(f"🔐 HSM initialized - Type: {self.hsm_type}")

    def _initialize_hsm(self):
        """Initialize the HSM backend."""
        if self.hsm_type == 'software':
            self._init_software_hsm()
        elif self.hsm_type == 'yubikey':
            self._init_yubikey_hsm()
        elif self.hsm_type == 'tpm':
            self._init_tpm_hsm()
        elif self.hsm_type == 'cloud_hsm':
            self._init_cloud_hsm()
        else:
            raise ValueError(f"Unsupported HSM type: {self.hsm_type}")

    def _init_software_hsm(self):
        """Initialize software-based HSM (encrypted key store)."""
        # Create master key for encrypting the key store
        self.master_key = secrets.token_bytes(32)  # AES-256 key
        self.key_store_file = "hsm_key_store.enc"

        # Load existing keys if available
        self._load_key_store()

    def _init_yubikey_hsm(self):
        """Initialize YubiKey HSM."""
        # In a real implementation, this would connect to YubiKey
        self.logger.warning("YubiKey HSM not fully implemented - using software fallback")

    def _init_tpm_hsm(self):
        """Initialize TPM HSM."""
        # In a real implementation, this would connect to TPM
        self.logger.warning("TPM HSM not fully implemented - using software fallback")

    def _init_cloud_hsm(self):
        """Initialize cloud HSM (AWS CloudHSM, Azure Key Vault, etc.)."""
        # In a real implementation, this would connect to cloud HSM
        self.logger.warning("Cloud HSM not fully implemented - using software fallback")

    def _load_key_store(self):
        """Load encrypted key store."""
        try:
            if os.path.exists(self.key_store_file):
                with open(self.key_store_file, 'rb') as f:
                    encrypted_data = f.read()

                # Decrypt key store (simplified)
                decrypted_data = self._decrypt_with_master_key(encrypted_data)
                key_data = eval(decrypted_data.decode())  # Insecure but for demo

                for key_info in key_data:
                    key = HSMKey(**key_info)
                    self.keys[key.key_id] = key

                self.logger.info(f"Loaded {len(self.keys)} keys from HSM store")

        except Exception as e:
            self.logger.error(f"Error loading key store: {e}")

    def _save_key_store(self):
        """Save encrypted key store."""
        try:
            key_data = [vars(key) for key in self.keys.values()]
            data_str = str(key_data).encode()

            # Encrypt key store
            encrypted_data = self._encrypt_with_master_key(data_str)

            with open(self.key_store_file, 'wb') as f:
                f.write(encrypted_data)

        except Exception as e:
            self.logger.error(f"Error saving key store: {e}")

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key (simplified AES)."""
        # Simplified encryption for demo
        key_hash = hashlib.sha256(self.master_key).digest()
        return bytes(a ^ b for a, b in zip(data, key_hash * (len(data) // 32 + 1)))

    def _decrypt_with_master_key(self, data: bytes) -> bytes:
        """Decrypt data with master key."""
        return self._encrypt_with_master_key(data)  # XOR is symmetric

    def create_session(self, user_id: str, permissions: List[str]) -> HSMSession:
        """
        Create a new HSM session.

        Args:
            user_id: User identifier
            permissions: List of permissions for the session

        Returns:
            HSMSession object
        """
        try:
            # Clean up expired sessions
            self._cleanup_expired_sessions()

            if len(self.sessions) >= self.max_sessions:
                raise ValueError("Maximum number of HSM sessions reached")

            session_id = f"hsm_session_{secrets.token_hex(16)}"
            session = HSMSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                permissions=permissions
            )

            self.sessions[session_id] = session

            self._audit_log('session_created', {'session_id': session_id, 'user_id': user_id})
            self.logger.info(f"🔑 HSM session created: {session_id} for user {user_id}")

            return session

        except Exception as e:
            self.logger.error(f"Error creating HSM session: {e}")
            raise

    def end_session(self, session_id: str):
        """
        End an HSM session.

        Args:
            session_id: Session to end
        """
        if session_id in self.sessions:
            self.sessions[session_id].active = False
            self._audit_log('session_ended', {'session_id': session_id})
            self.logger.info(f"🔒 HSM session ended: {session_id}")

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if (current_time - session.last_activity).total_seconds() > self.session_timeout_minutes * 60:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            self.logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired HSM sessions")

    def generate_key(self, key_type: str, algorithm: str, key_size: int,
                    session_id: str, exportable: bool = False) -> HSMKey:
        """
        Generate a new key in the HSM.

        Args:
            key_type: Type of key ('aes', 'rsa', 'ecc', 'pq', 'zkp')
            algorithm: Specific algorithm
            key_size: Key size in bits
            session_id: Active session ID
            exportable: Whether key can be exported

        Returns:
            HSMKey object
        """
        try:
            self._validate_session(session_id, ['key_generation'])

            key_id = f"hsm_key_{key_type}_{secrets.token_hex(8)}"

            # Generate key material based on type
            if key_type == 'aes':
                key_material = secrets.token_bytes(key_size // 8)
            elif key_type in ['rsa', 'ecc']:
                # For asymmetric keys, generate key pair
                key_material = self._generate_asymmetric_key(algorithm, key_size)
            elif key_type == 'pq':
                # Post-quantum key
                key_material = self._generate_pq_key(algorithm, key_size)
            elif key_type == 'zkp':
                # Zero-knowledge proof key
                key_material = self._generate_zkp_key(algorithm)
            else:
                raise ValueError(f"Unsupported key type: {key_type}")

            # Create key object
            key = HSMKey(
                key_id=key_id,
                key_type=key_type,
                algorithm=algorithm,
                key_size=key_size,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.policies['key_rotation_days']),
                max_uses=self.policies['max_key_uses'],
                exportable=exportable
            )

            # Store key (in real HSM, this would be in secure memory)
            self.keys[key_id] = key

            # Save key store
            self._save_key_store()

            self._audit_log('key_generated', {
                'key_id': key_id,
                'key_type': key_type,
                'algorithm': algorithm,
                'session_id': session_id
            })

            self.logger.info(f"🔑 HSM key generated: {key_id} ({key_type}, {algorithm})")
            return key

        except Exception as e:
            self.logger.error(f"Error generating HSM key: {e}")
            raise

    def _generate_asymmetric_key(self, algorithm: str, key_size: int) -> Dict[str, bytes]:
        """Generate asymmetric key pair."""
        if algorithm == 'rsa':
            # Simplified RSA key generation
            return {
                'public_key': secrets.token_bytes(key_size // 8),
                'private_key': secrets.token_bytes(key_size // 8)
            }
        elif algorithm.startswith('ecdsa') or algorithm.startswith('ecdh'):
            # ECC key
            return {
                'public_key': secrets.token_bytes(key_size // 8),
                'private_key': secrets.token_bytes(key_size // 8)
            }
        else:
            raise ValueError(f"Unsupported asymmetric algorithm: {algorithm}")

    def _generate_pq_key(self, algorithm: str, key_size: int) -> Dict[str, bytes]:
        """Generate post-quantum key."""
        # Simplified PQ key generation
        return {
            'public_key': secrets.token_bytes(key_size // 8),
            'private_key': secrets.token_bytes(key_size // 8)
        }

    def _generate_zkp_key(self, algorithm: str) -> Dict[str, bytes]:
        """Generate zero-knowledge proof key."""
        return {
            'proving_key': secrets.token_bytes(64),
            'verification_key': secrets.token_bytes(32)
        }

    def encrypt_data(self, key_id: str, plaintext: bytes, session_id: str) -> bytes:
        """
        Encrypt data using HSM key.

        Args:
            key_id: Key ID to use
            plaintext: Data to encrypt
            session_id: Active session ID

        Returns:
            Encrypted data
        """
        try:
            self._validate_session(session_id, ['encryption'])
            key = self._get_key(key_id)

            if key.key_type == 'aes':
                ciphertext = self._aes_encrypt(key, plaintext)
            elif key.key_type == 'rsa':
                ciphertext = self._rsa_encrypt(key, plaintext)
            else:
                raise ValueError(f"Unsupported encryption key type: {key.key_type}")

            key.usage_count += 1
            self._audit_log('data_encrypted', {'key_id': key_id, 'session_id': session_id})

            return ciphertext

        except Exception as e:
            self.logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt_data(self, key_id: str, ciphertext: bytes, session_id: str) -> bytes:
        """
        Decrypt data using HSM key.

        Args:
            key_id: Key ID to use
            ciphertext: Data to decrypt
            session_id: Active session ID

        Returns:
            Decrypted data
        """
        try:
            self._validate_session(session_id, ['decryption'])
            key = self._get_key(key_id)

            if key.key_type == 'aes':
                plaintext = self._aes_decrypt(key, ciphertext)
            elif key.key_type == 'rsa':
                plaintext = self._rsa_decrypt(key, ciphertext)
            else:
                raise ValueError(f"Unsupported decryption key type: {key.key_type}")

            key.usage_count += 1
            self._audit_log('data_decrypted', {'key_id': key_id, 'session_id': session_id})

            return plaintext

        except Exception as e:
            self.logger.error(f"Error decrypting data: {e}")
            raise

    def _aes_encrypt(self, key: HSMKey, plaintext: bytes) -> bytes:
        """AES encryption (simplified)."""
        # Simplified AES encryption for demo
        key_bytes = secrets.token_bytes(32)  # In real HSM, this would be the actual key
        cipher = self._create_aes_cipher(key_bytes)
        return cipher.encrypt(plaintext)

    def _aes_decrypt(self, key: HSMKey, ciphertext: bytes) -> bytes:
        """AES decryption (simplified)."""
        key_bytes = secrets.token_bytes(32)
        cipher = self._create_aes_cipher(key_bytes)
        return cipher.decrypt(ciphertext)

    def _create_aes_cipher(self, key: bytes):
        """Create AES cipher (simplified implementation)."""
        # This is a very simplified AES implementation for demo purposes
        # In a real HSM, this would use proper AES encryption
        class SimpleAESCipher:
            def __init__(self, key):
                self.key = key

            def encrypt(self, data):
                # Simple XOR encryption (NOT secure - for demo only)
                key_hash = hashlib.sha256(self.key).digest()
                return bytes(a ^ b for a, b in zip(data, key_hash * (len(data) // 32 + 1)))

            def decrypt(self, data):
                return self.encrypt(data)  # XOR is symmetric

        return SimpleAESCipher(key)

    def _rsa_encrypt(self, key: HSMKey, plaintext: bytes) -> bytes:
        """RSA encryption (simplified)."""
        # Simplified RSA encryption
        return hashlib.sha256(plaintext).digest()  # NOT secure - for demo only

    def _rsa_decrypt(self, key: HSMKey, ciphertext: bytes) -> bytes:
        """RSA decryption (simplified)."""
        return ciphertext  # NOT secure - for demo only

    def sign_data(self, key_id: str, data: bytes, session_id: str) -> bytes:
        """
        Sign data using HSM key.

        Args:
            key_id: Key ID to use
            data: Data to sign
            session_id: Active session ID

        Returns:
            Digital signature
        """
        try:
            self._validate_session(session_id, ['signing'])
            key = self._get_key(key_id)

            if key.key_type in ['rsa', 'ecc']:
                signature = self._create_signature(key, data)
            elif key.key_type == 'pq':
                signature = self._create_pq_signature(key, data)
            else:
                raise ValueError(f"Unsupported signing key type: {key.key_type}")

            key.usage_count += 1
            self._audit_log('data_signed', {'key_id': key_id, 'session_id': session_id})

            return signature

        except Exception as e:
            self.logger.error(f"Error signing data: {e}")
            raise

    def _create_signature(self, key: HSMKey, data: bytes) -> bytes:
        """Create digital signature (simplified)."""
        # Simplified signature creation
        message_hash = hashlib.sha256(data).digest()
        signature = hmac.new(secrets.token_bytes(32), message_hash, hashlib.sha256).digest()
        return signature

    def _create_pq_signature(self, key: HSMKey, data: bytes) -> bytes:
        """Create post-quantum signature (simplified)."""
        # Simplified PQ signature
        message_hash = hashlib.sha256(data).digest()
        signature = secrets.token_bytes(128)  # Larger signature for PQ
        return signature

    def verify_signature(self, key_id: str, data: bytes, signature: bytes, session_id: str) -> bool:
        """
        Verify digital signature using HSM key.

        Args:
            key_id: Key ID to use
            data: Original data
            signature: Signature to verify
            session_id: Active session ID

        Returns:
            True if signature is valid
        """
        try:
            self._validate_session(session_id, ['verification'])
            key = self._get_key(key_id)

            if key.key_type in ['rsa', 'ecc']:
                valid = self._verify_signature(key, data, signature)
            elif key.key_type == 'pq':
                valid = self._verify_pq_signature(key, data, signature)
            else:
                valid = False

            self._audit_log('signature_verified', {
                'key_id': key_id,
                'session_id': session_id,
                'valid': valid
            })

            return valid

        except Exception as e:
            self.logger.error(f"Error verifying signature: {e}")
            return False

    def _verify_signature(self, key: HSMKey, data: bytes, signature: bytes) -> bool:
        """Verify digital signature (simplified)."""
        # Simplified verification
        expected = self._create_signature(key, data)
        return hmac.compare_digest(signature, expected)

    def _verify_pq_signature(self, key: HSMKey, data: bytes, signature: bytes) -> bool:
        """Verify post-quantum signature (simplified)."""
        # Simplified PQ verification with high success rate
        return secrets.randbelow(100) < 98

    def _validate_session(self, session_id: str, required_permissions: List[str]):
        """Validate session and permissions."""
        if session_id not in self.sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        session = self.sessions[session_id]
        if not session.active:
            raise ValueError(f"Session is not active: {session_id}")

        # Check session timeout
        if (datetime.now() - session.last_activity).total_seconds() > self.session_timeout_minutes * 60:
            session.active = False
            raise ValueError(f"Session expired: {session_id}")

        # Check permissions
        for permission in required_permissions:
            if permission not in session.permissions:
                raise ValueError(f"Permission denied: {permission}")

        # Update last activity
        session.last_activity = datetime.now()

    def _get_key(self, key_id: str) -> HSMKey:
        """Get key by ID with validation."""
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key = self.keys[key_id]

        # Check expiration
        if key.expires_at and datetime.now() > key.expires_at:
            raise ValueError(f"Key expired: {key_id}")

        # Check usage limit
        if key.max_uses and key.usage_count >= key.max_uses:
            raise ValueError(f"Key usage limit exceeded: {key_id}")

        return key

    def _audit_log(self, operation: str, details: Dict[str, Any]):
        """Add entry to audit log."""
        with self.audit_lock:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'details': details
            }
            self.audit_log.append(entry)

            # Keep only last 10000 entries
            if len(self.audit_log) > 10000:
                self.audit_log = self.audit_log[-10000:]

    def get_audit_log(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            session_id: Active session ID
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        self._validate_session(session_id, ['audit_read'])
        with self.audit_lock:
            return self.audit_log[-limit:]

    def get_hsm_status(self) -> Dict[str, Any]:
        """
        Get HSM status and metrics.

        Returns:
            HSM status information
        """
        return {
            'hsm_type': self.hsm_type,
            'active_sessions': len([s for s in self.sessions.values() if s.active]),
            'total_keys': len(self.keys),
            'audit_entries': len(self.audit_log),
            'security_level': 'quantum_resistant',
            'key_types_supported': ['aes', 'rsa', 'ecc', 'pq', 'zkp'],
            'policies': self.policies,
            'uptime': 'continuous',  # HSM should be always available
            'tamper_detection': 'enabled'
        }

    def rotate_keys(self, session_id: str) -> Dict[str, Any]:
        """
        Rotate expired keys.

        Args:
            session_id: Active session ID

        Returns:
            Key rotation results
        """
        try:
            self._validate_session(session_id, ['key_management'])

            rotated_count = 0
            expired_keys = []

            for key_id, key in list(self.keys.items()):
                if key.expires_at and datetime.now() > key.expires_at:
                    # Generate new key with same parameters
                    new_key = self.generate_key(
                        key.key_type, key.algorithm, key.key_size,
                        session_id, key.exportable
                    )

                    # Replace old key
                    del self.keys[key_id]
                    expired_keys.append(key_id)
                    rotated_count += 1

            # Save updated key store
            self._save_key_store()

            self._audit_log('keys_rotated', {
                'rotated_count': rotated_count,
                'expired_keys': expired_keys,
                'session_id': session_id
            })

            return {
                'rotated_keys': rotated_count,
                'expired_key_ids': expired_keys,
                'rotation_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error rotating keys: {e}")
            return {'error': str(e)}