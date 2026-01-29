#!/usr/bin/env python3
"""
Certificate Authority (CA) System for Ailoos
Implementa un sistema completo de PKI con certificados X.509 para nodos
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.backends import default_backend
import ipaddress
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CertificateRequest:
    """Solicitud de certificado"""
    node_id: str
    public_key: bytes
    organization: str
    common_name: str
    validity_days: int = 365
    key_usage: List[str] = None
    extended_key_usage: List[str] = None

    def __post_init__(self):
        if self.key_usage is None:
            self.key_usage = ['digital_signature', 'key_encipherment']
        if self.extended_key_usage is None:
            self.extended_key_usage = ['server_auth', 'client_auth']

@dataclass
class CertificateInfo:
    """Información de certificado emitido"""
    certificate_id: str
    node_id: str
    serial_number: str
    certificate_pem: str
    private_key_pem: str
    issued_at: datetime
    expires_at: datetime
    status: str = 'active'  # active, revoked, expired
    revocation_reason: Optional[str] = None
    revocation_date: Optional[datetime] = None

class CertificateAuthority:
    """Autoridad Certificadora completa para Ailoos"""

    def __init__(self, ca_name: str = "Ailoos Root CA", key_size: int = 4096):
        self.ca_name = ca_name
        self.key_size = key_size

        # CA storage
        self.ca_certificates: Dict[str, CertificateInfo] = {}
        self.revoked_certificates: Dict[str, Dict[str, Any]] = {}
        self.crl_cache: Optional[bytes] = None
        self.crl_last_update: Optional[datetime] = None

        # Generate CA keys and certificate
        self._generate_ca_certificate()

        logger.info(f"🏛️ Certificate Authority '{ca_name}' initialized")

    def _generate_ca_certificate(self):
        """Generar certificado raíz de la CA"""
        # Generate private key
        self.ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend()
        )

        # Generate public key
        self.ca_public_key = self.ca_private_key.public_key()

        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Ailoos Network"),
            x509.NameAttribute(NameOID.COMMON_NAME, self.ca_name),
        ])

        # Certificate valid for 10 years
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=3650)

        # Certificate builder
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(self.ca_public_key)
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_until)

        # Add extensions
        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(self.ca_public_key),
            critical=False
        )

        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                x509.SubjectKeyIdentifier.from_public_key(self.ca_public_key)
            ),
            critical=False
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )

        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )

        # Sign certificate
        self.ca_certificate = builder.sign(
            private_key=self.ca_private_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        logger.info("✅ CA root certificate generated")

    def generate_node_certificate(self, request: CertificateRequest) -> CertificateInfo:
        """Generar certificado para un nodo"""
        try:
            # Load public key from request
            try:
                public_key = serialization.load_pem_public_key(
                    request.public_key,
                    backend=default_backend()
                )
            except Exception as e:
                raise ValueError(f"Invalid public key format: {e}")

            # Generate certificate
            certificate, serial_number = self._create_certificate(request, public_key)

            # Generate certificate ID
            cert_id = f"cert-{hashlib.sha256(certificate.public_bytes(serialization.Encoding.PEM)).hexdigest()[:16]}"

            # Create certificate info
            cert_info = CertificateInfo(
                certificate_id=cert_id,
                node_id=request.node_id,
                serial_number=hex(serial_number)[2:].upper(),
                certificate_pem=certificate.public_bytes(serialization.Encoding.PEM).decode(),
                private_key_pem="",  # Node should generate its own private key
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=request.validity_days)
            )

            # Store certificate
            self.ca_certificates[cert_id] = cert_info

            logger.info(f"✅ Certificate generated for node {request.node_id}: {cert_id}")
            return cert_info

        except Exception as e:
            logger.error(f"Failed to generate certificate for node {request.node_id}: {e}")
            raise

    def _create_certificate(self, request: CertificateRequest, public_key) -> Tuple[x509.Certificate, int]:
        """Crear certificado X.509"""
        # Subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, request.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, request.common_name),
        ])

        # Issuer (CA)
        issuer = self.ca_certificate.subject

        # Validity
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=request.validity_days)

        # Serial number
        serial_number = x509.random_serial_number()

        # Certificate builder
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(public_key)
        builder = builder.serial_number(serial_number)
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_until)

        # Add extensions
        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key),
            critical=False
        )

        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                self.ca_certificate.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_KEY_IDENTIFIER).value
            ),
            critical=False
        )

        # Key usage
        key_usage_flags = {
            'digital_signature': False,
            'content_commitment': False,
            'key_encipherment': False,
            'data_encipherment': False,
            'key_agreement': False,
            'key_cert_sign': False,
            'crl_sign': False,
            'encipher_only': False,
            'decipher_only': False
        }

        for usage in request.key_usage:
            if usage in key_usage_flags:
                key_usage_flags[usage] = True

        builder = builder.add_extension(
            x509.KeyUsage(**key_usage_flags),
            critical=True
        )

        # Extended key usage
        if request.extended_key_usage:
            extended_usage_list = []
            for usage in request.extended_key_usage:
                if usage == 'server_auth':
                    extended_usage_list.append(x509.oid.ObjectIdentifier("1.3.6.1.5.5.7.3.1"))  # serverAuth OID
                elif usage == 'client_auth':
                    extended_usage_list.append(x509.oid.ObjectIdentifier("1.3.6.1.5.5.7.3.2"))  # clientAuth OID

            if extended_usage_list:
                builder = builder.add_extension(
                    x509.ExtendedKeyUsage(extended_usage_list),
                    critical=False
                )

        # Subject Alternative Name (SAN)
        san = x509.SubjectAlternativeName([
            x509.DNSName(f"{request.node_id}.ailoos.network"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1"))  # Placeholder
        ])
        builder = builder.add_extension(san, critical=False)

        # Sign certificate
        certificate = builder.sign(
            private_key=self.ca_private_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        return certificate, serial_number

    def revoke_certificate(self, certificate_id: str, reason: str = "unspecified") -> bool:
        """Revocar un certificado"""
        if certificate_id not in self.ca_certificates:
            logger.warning(f"Certificate {certificate_id} not found")
            return False

        cert_info = self.ca_certificates[certificate_id]
        cert_info.status = 'revoked'
        cert_info.revocation_reason = reason
        cert_info.revocation_date = datetime.utcnow()

        # Add to revoked certificates
        self.revoked_certificates[certificate_id] = {
            'serial_number': cert_info.serial_number,
            'revocation_date': cert_info.revocation_date.isoformat(),
            'reason': reason
        }

        # Invalidate CRL cache
        self.crl_cache = None

        logger.info(f"🔒 Certificate {certificate_id} revoked: {reason}")
        return True

    def generate_crl(self) -> str:
        """Generar Certificate Revocation List (CRL)"""
        if self.crl_cache and self.crl_last_update:
            # Return cached CRL if less than 1 hour old
            if (datetime.utcnow() - self.crl_last_update).total_seconds() < 3600:
                return self.crl_cache.decode()

        try:
            # Create CRL builder
            builder = x509.CertificateRevocationListBuilder()
            builder = builder.issuer_name(self.ca_certificate.subject)
            builder = builder.last_update(datetime.utcnow())
            builder = builder.next_update(datetime.utcnow() + timedelta(hours=24))

            # Add revoked certificates
            for cert_id, revocation_info in self.revoked_certificates.items():
                revoked_cert = x509.RevokedCertificateBuilder()
                revoked_cert = revoked_cert.serial_number(int(revocation_info['serial_number'], 16))
                revoked_cert = revoked_cert.revocation_date(
                    datetime.fromisoformat(revocation_info['revocation_date'])
                )

                # Add revocation reason
                reason_code = self._get_crl_reason_code(revocation_info['reason'])
                if reason_code:
                    revoked_cert = revoked_cert.add_extension(
                        x509.CRLReason(reason_code),
                        critical=False
                    )

                builder = builder.add_revoked_certificate(revoked_cert.build())

            # Sign CRL
            crl = builder.sign(
                private_key=self.ca_private_key,
                algorithm=hashes.SHA256(),
                backend=default_backend()
            )

            # Cache CRL
            self.crl_cache = crl.public_bytes(serialization.Encoding.PEM)
            self.crl_last_update = datetime.utcnow()

            logger.info("📋 CRL generated with {} revoked certificates".format(len(self.revoked_certificates)))
            return self.crl_cache.decode()

        except Exception as e:
            logger.error(f"Failed to generate CRL: {e}")
            return ""

    def _get_crl_reason_code(self, reason: str) -> Optional[x509.ReasonFlags]:
        """Convert reason string to CRL reason code"""
        reason_map = {
            'unspecified': x509.ReasonFlags.unspecified,
            'key_compromise': x509.ReasonFlags.key_compromise,
            'ca_compromise': x509.ReasonFlags.ca_compromise,
            'affiliation_changed': x509.ReasonFlags.affiliation_changed,
            'superseded': x509.ReasonFlags.superseded,
            'cessation_of_operation': x509.ReasonFlags.cessation_of_operation,
            'certificate_hold': x509.ReasonFlags.certificate_hold,
            'remove_from_crl': x509.ReasonFlags.remove_from_crl,
            'privilege_withdrawn': x509.ReasonFlags.privilege_withdrawn,
            'aa_compromise': x509.ReasonFlags.aa_compromise
        }
        return reason_map.get(reason.lower())

    def validate_certificate(self, certificate_pem: str) -> Dict[str, Any]:
        """Validar un certificado"""
        try:
            # Load certificate
            certificate = x509.load_pem_x509_certificate(
                certificate_pem.encode(),
                backend=default_backend()
            )

            # Check if revoked
            serial_hex = hex(certificate.serial_number)[2:].upper()
            is_revoked = any(
                revocation['serial_number'] == serial_hex
                for revocation in self.revoked_certificates.values()
            )

            # Check validity period
            from datetime import timezone
            now = datetime.now(timezone.utc)
            is_expired = now < certificate.not_valid_before_utc or now > certificate.not_valid_after_utc

            # Verify signature
            try:
                # Use the certificate's signature algorithm
                self.ca_public_key.verify(
                    certificate.signature,
                    certificate.tbs_certificate_bytes,
                    certificate.signature_hash_algorithm
                )
                signature_valid = True
            except Exception as e:
                logger.debug(f"Signature verification failed: {e}")
                signature_valid = False

            result = {
                'valid': not is_revoked and not is_expired and signature_valid,
                'revoked': is_revoked,
                'expired': is_expired,
                'signature_valid': signature_valid,
                'subject': str(certificate.subject),
                'issuer': str(certificate.issuer),
                'serial_number': serial_hex,
                'not_before': certificate.not_valid_before_utc.isoformat(),
                'not_after': certificate.not_valid_after_utc.isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }

    def get_ca_certificate(self) -> str:
        """Obtener certificado de la CA"""
        return self.ca_certificate.public_bytes(serialization.Encoding.PEM).decode()

    def list_certificates(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar certificados"""
        certificates = []

        for cert_info in self.ca_certificates.values():
            if status_filter and cert_info.status != status_filter:
                continue

            certificates.append(asdict(cert_info))

        return certificates

# Global CA instance
ca_instance = None

def get_certificate_authority() -> CertificateAuthority:
    """Get global CA instance"""
    global ca_instance
    if ca_instance is None:
        ca_instance = CertificateAuthority()
    return ca_instance

# Utility functions
def generate_node_keypair(key_type: str = 'rsa', key_size: int = 2048) -> Tuple[str, str]:
    """Generar par de claves para un nodo"""
    if key_type.lower() == 'rsa':
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
    elif key_type.lower() == 'ec':
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    else:
        raise ValueError(f"Unsupported key type: {key_type}")

    public_key = private_key.public_key()

    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return private_pem, public_pem

if __name__ == '__main__':
    # Demo
    ca = get_certificate_authority()

    print("🏛️ Ailoos Certificate Authority Demo")
    print("=" * 50)

    # Generate node keypair
    private_key_pem, public_key_pem = generate_node_keypair()
    print("✅ Node keypair generated")

    # Create certificate request
    request = CertificateRequest(
        node_id="node-001",
        public_key=public_key_pem.encode(),
        organization="Ailoos Network",
        common_name="node-001.ailoos.network"
    )

    # Generate certificate
    cert_info = ca.generate_node_certificate(request)
    print(f"✅ Certificate generated: {cert_info.certificate_id}")

    # Validate certificate
    validation = ca.validate_certificate(cert_info.certificate_pem)
    print(f"✅ Certificate validation: {'Valid' if validation.get('valid', False) else 'Invalid'}")
    if not validation.get('valid', False):
        print(f"   Debug info: revoked={validation.get('revoked')}, expired={validation.get('expired')}, signature_valid={validation.get('signature_valid')}")

    # Generate CRL
    crl = ca.generate_crl()
    print(f"✅ CRL generated ({len(ca.revoked_certificates)} revoked certificates)")

    print("\n🎉 CA Demo completed successfully!")