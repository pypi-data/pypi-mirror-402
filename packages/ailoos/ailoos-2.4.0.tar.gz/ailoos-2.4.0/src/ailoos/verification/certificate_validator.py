#!/usr/bin/env python3
"""
Certificate Validator for Ailoos PKI System
Implementa validación y revocación de certificados X.509
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import aiohttp
import json

from .certificate_authority import get_certificate_authority, CertificateAuthority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CertificateValidator:
    """Validador de certificados X.509 con soporte para CRL y OCSP"""

    def __init__(self, ca: CertificateAuthority):
        self.ca = ca
        self.crl_cache: Dict[str, Tuple[bytes, datetime]] = {}
        self.ocsp_cache: Dict[str, Tuple[bool, datetime]] = {}
        self.cache_ttl = timedelta(hours=1)  # Cache TTL

        # HTTP client for external validation
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize validator"""
        self.session = aiohttp.ClientSession()
        logger.info("🔍 Certificate Validator initialized")

    async def validate_certificate_chain(self, certificate_pem: str,
                                       intermediate_certs: List[str] = None) -> Dict[str, Any]:
        """
        Validar cadena completa de certificados

        Args:
            certificate_pem: Certificado a validar en formato PEM
            intermediate_certs: Lista de certificados intermedios en formato PEM

        Returns:
            Dict con resultado de validación
        """
        try:
            # Load certificate
            certificate = x509.load_pem_x509_certificate(
                certificate_pem.encode(),
                backend=default_backend()
            )

            # Build certificate chain
            chain = [certificate]
            if intermediate_certs:
                for cert_pem in intermediate_certs:
                    try:
                        cert = x509.load_pem_x509_certificate(
                            cert_pem.encode(),
                            backend=default_backend()
                        )
                        chain.append(cert)
                    except Exception as e:
                        logger.warning(f"Failed to load intermediate certificate: {e}")

            # Add root CA certificate
            ca_cert = x509.load_pem_x509_certificate(
                self.ca.get_ca_certificate().encode(),
                backend=default_backend()
            )
            chain.append(ca_cert)

            # Validate each certificate in chain
            validation_results = []
            for i, cert in enumerate(chain[:-1]):  # Exclude root CA from detailed validation
                result = await self._validate_single_certificate(cert, chain[i+1:])
                validation_results.append(result)

            # Overall validation
            all_valid = all(result['valid'] for result in validation_results)
            any_revoked = any(result.get('revoked', False) for result in validation_results)
            any_expired = any(result.get('expired', False) for result in validation_results)

            return {
                'valid': all_valid,
                'revoked': any_revoked,
                'expired': any_expired,
                'chain_length': len(chain),
                'certificate_results': validation_results,
                'validation_time': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Certificate chain validation failed: {e}")
            return {
                'valid': False,
                'error': str(e),
                'validation_time': datetime.utcnow().isoformat()
            }

    async def _validate_single_certificate(self, certificate: x509.Certificate,
                                         issuer_chain: List[x509.Certificate]) -> Dict[str, Any]:
        """Validar un certificado individual"""
        result = {
            'subject': str(certificate.subject),
            'issuer': str(certificate.issuer),
            'serial_number': hex(certificate.serial_number)[2:].upper(),
            'valid': False,
            'errors': []
        }

        try:
            # Check validity period
            now = datetime.utcnow()
            if now < certificate.not_valid_before:
                result['errors'].append("Certificate not yet valid")
                result['not_yet_valid'] = True
            elif now > certificate.not_valid_after:
                result['errors'].append("Certificate expired")
                result['expired'] = True
            else:
                result['valid_period'] = True

            # Check revocation status
            revocation_status = await self._check_revocation_status(certificate)
            if revocation_status['revoked']:
                result['errors'].append(f"Certificate revoked: {revocation_status['reason']}")
                result['revoked'] = True
                result['revocation_reason'] = revocation_status['reason']

            # Verify signature
            try:
                # Find issuer certificate
                issuer_cert = None
                for issuer in issuer_chain:
                    if issuer.subject == certificate.issuer_name:
                        issuer_cert = issuer
                        break

                if issuer_cert:
                    issuer_cert.public_key().verify(
                        certificate.signature,
                        certificate.tbs_certificate_bytes,
                        certificate.signature_hash_algorithm
                    )
                    result['signature_valid'] = True
                else:
                    result['errors'].append("Issuer certificate not found in chain")
                    result['signature_valid'] = False

            except InvalidSignature:
                result['errors'].append("Invalid certificate signature")
                result['signature_valid'] = False
            except Exception as e:
                result['errors'].append(f"Signature verification error: {e}")
                result['signature_valid'] = False

            # Check key usage
            key_usage_valid = self._validate_key_usage(certificate)
            if not key_usage_valid['valid']:
                result['errors'].extend(key_usage_valid['errors'])
                result['key_usage_valid'] = False
            else:
                result['key_usage_valid'] = True

            # Check extensions
            extensions_valid = self._validate_extensions(certificate)
            if not extensions_valid['valid']:
                result['errors'].extend(extensions_valid['errors'])
                result['extensions_valid'] = False
            else:
                result['extensions_valid'] = True

            # Overall validity
            result['valid'] = (
                result.get('valid_period', False) and
                not result.get('revoked', False) and
                result.get('signature_valid', False) and
                result.get('key_usage_valid', False) and
                result.get('extensions_valid', False)
            )

        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
            result['valid'] = False

        return result

    async def _check_revocation_status(self, certificate: x509.Certificate) -> Dict[str, Any]:
        """Verificar estado de revocación usando CRL"""
        serial_hex = hex(certificate.serial_number)[2:].upper()

        # Check local CA revocation list first
        ca_validation = self.ca.validate_certificate(
            certificate.public_bytes(serialization.Encoding.PEM).decode()
        )

        if ca_validation.get('revoked', False):
            return {
                'revoked': True,
                'reason': 'Revoked by CA',
                'source': 'local_ca'
            }

        # Check CRL cache
        cache_key = f"crl_{certificate.issuer}"
        if cache_key in self.crl_cache:
            crl_data, cache_time = self.crl_cache[cache_key]
            if datetime.utcnow() - cache_time < self.cache_ttl:
                # Parse CRL and check
                revocation_status = self._check_certificate_in_crl(certificate, crl_data)
                if revocation_status['revoked']:
                    return revocation_status

        # Fetch fresh CRL
        try:
            crl_pem = self.ca.generate_crl()
            if crl_pem:
                self.crl_cache[cache_key] = (crl_pem.encode(), datetime.utcnow())
                revocation_status = self._check_certificate_in_crl(certificate, crl_pem.encode())
                if revocation_status['revoked']:
                    return revocation_status
        except Exception as e:
            logger.warning(f"CRL check failed: {e}")

        return {'revoked': False}

    def _check_certificate_in_crl(self, certificate: x509.Certificate, crl_pem: bytes) -> Dict[str, Any]:
        """Verificar si un certificado está en la CRL"""
        try:
            crl = x509.load_pem_x509_crl(crl_pem, backend=default_backend())

            for revoked_cert in crl:
                if revoked_cert.serial_number == certificate.serial_number:
                    reason = "Unknown"
                    try:
                        reason_extension = revoked_cert.extensions.get_extension_for_oid(ExtensionOID.CRL_REASON)
                        reason = reason_extension.value.reason.name
                    except Exception:
                        pass

                    return {
                        'revoked': True,
                        'reason': reason,
                        'revocation_date': revoked_cert.revocation_date.isoformat(),
                        'source': 'crl'
                    }

        except Exception as e:
            logger.warning(f"CRL parsing failed: {e}")

        return {'revoked': False}

    def _validate_key_usage(self, certificate: x509.Certificate) -> Dict[str, Any]:
        """Validar uso de clave del certificado"""
        result = {'valid': True, 'errors': []}

        try:
            key_usage_ext = certificate.extensions.get_extension_for_oid(ExtensionOID.KEY_USAGE)
            key_usage = key_usage_ext.value

            # Basic validations
            if key_usage.digital_signature and key_usage.key_encipherment:
                # Valid for TLS server/client
                pass
            elif key_usage.key_cert_sign and key_usage.crl_sign:
                # Valid for CA certificate
                pass
            else:
                result['valid'] = False
                result['errors'].append("Key usage combination not standard")

        except x509.ExtensionNotFound:
            result['errors'].append("Key usage extension not found")
            result['valid'] = False
        except Exception as e:
            result['errors'].append(f"Key usage validation error: {e}")
            result['valid'] = False

        return result

    def _validate_extensions(self, certificate: x509.Certificate) -> Dict[str, Any]:
        """Validar extensiones del certificado"""
        result = {'valid': True, 'errors': []}

        try:
            # Check Subject Alternative Name
            try:
                san_ext = certificate.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                san = san_ext.value
                if len(san) == 0:
                    result['errors'].append("Subject Alternative Name is empty")
                    result['valid'] = False
            except x509.ExtensionNotFound:
                result['errors'].append("Subject Alternative Name extension missing")
                result['valid'] = False

            # Check Basic Constraints for CA certificates
            try:
                bc_ext = certificate.extensions.get_extension_for_oid(ExtensionOID.BASIC_CONSTRAINTS)
                bc = bc_ext.value
                if bc.ca:
                    # Additional CA validations
                    pass
            except x509.ExtensionNotFound:
                # Not a CA certificate, skip
                pass

        except Exception as e:
            result['errors'].append(f"Extensions validation error: {e}")
            result['valid'] = False

        return result

    async def validate_certificate_online(self, certificate_pem: str,
                                        ocsp_url: str = None) -> Dict[str, Any]:
        """Validar certificado usando OCSP (Online Certificate Status Protocol)"""
        try:
            certificate = x509.load_pem_x509_certificate(
                certificate_pem.encode(),
                backend=default_backend()
            )

            # Check OCSP cache first
            serial_hex = hex(certificate.serial_number)[2:].upper()
            cache_key = f"ocsp_{serial_hex}"

            if cache_key in self.ocsp_cache:
                status, cache_time = self.ocsp_cache[cache_key]
                if datetime.utcnow() - cache_time < self.cache_ttl:
                    return {
                        'valid': not status,  # status=True means revoked
                        'revoked': status,
                        'source': 'ocsp_cache',
                        'cached': True
                    }

            # OCSP validation would require implementing OCSP client
            # For now, fall back to CRL validation
            logger.info("OCSP validation not implemented, using CRL fallback")

            revocation_status = await self._check_revocation_status(certificate)
            self.ocsp_cache[cache_key] = (revocation_status['revoked'], datetime.utcnow())

            return {
                'valid': not revocation_status['revoked'],
                'revoked': revocation_status['revoked'],
                'reason': revocation_status.get('reason'),
                'source': 'crl_fallback'
            }

        except Exception as e:
            logger.error(f"Online certificate validation failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }

    async def get_certificate_info(self, certificate_pem: str) -> Dict[str, Any]:
        """Obtener información detallada de un certificado"""
        try:
            certificate = x509.load_pem_x509_certificate(
                certificate_pem.encode(),
                backend=default_backend()
            )

            # Extract basic information
            info = {
                'version': certificate.version.name,
                'serial_number': hex(certificate.serial_number)[2:].upper(),
                'subject': str(certificate.subject),
                'issuer': str(certificate.issuer),
                'not_before': certificate.not_valid_before.isoformat(),
                'not_after': certificate.not_valid_after.isoformat(),
                'signature_algorithm': certificate.signature_hash_algorithm.name,
                'public_key_algorithm': certificate.public_key_algorithm_oid._name
            }

            # Extract extensions
            extensions = {}
            for ext in certificate.extensions:
                ext_name = ext.oid._name
                try:
                    if ext_name == 'subjectAlternativeName':
                        extensions[ext_name] = [str(name) for name in ext.value]
                    elif ext_name == 'keyUsage':
                        extensions[ext_name] = [usage for usage in dir(ext.value) if not usage.startswith('_') and getattr(ext.value, usage)]
                    else:
                        extensions[ext_name] = str(ext.value)
                except Exception:
                    extensions[ext_name] = "Unable to parse"

            info['extensions'] = extensions

            # Check current status
            validation = await self.validate_certificate_chain(certificate_pem)
            info['current_status'] = {
                'valid': validation['valid'],
                'revoked': validation.get('revoked', False),
                'expired': validation.get('expired', False)
            }

            return info

        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return {'error': str(e)}

    async def close(self):
        """Close validator resources"""
        if self.session:
            await self.session.close()

# Global validator instance
validator_instance = None

def get_certificate_validator() -> CertificateValidator:
    """Get global certificate validator instance"""
    global validator_instance
    if validator_instance is None:
        ca = get_certificate_authority()
        validator_instance = CertificateValidator(ca)
    return validator_instance

async def validate_certificate_async(certificate_pem: str) -> Dict[str, Any]:
    """Convenience function for async certificate validation"""
    validator = get_certificate_validator()
    if not validator.session:
        await validator.initialize()

    try:
        return await validator.validate_certificate_chain(certificate_pem)
    finally:
        await validator.close()

if __name__ == '__main__':
    async def main():
        # Initialize CA and validator
        ca = get_certificate_authority()
        validator = CertificateValidator(ca)
        await validator.initialize()

        print("🔍 Certificate Validator Demo")
        print("=" * 50)

        try:
            # Generate test certificate
            from .certificate_authority import generate_node_keypair, CertificateRequest

            private_key_pem, public_key_pem = generate_node_keypair()

            request = CertificateRequest(
                node_id="test-node-001",
                public_key=public_key_pem.encode(),
                organization="Ailoos Network",
                common_name="test-node-001.ailoos.network"
            )

            cert_info = ca.generate_node_certificate(request)
            print("✅ Test certificate generated")

            # Validate certificate
            validation = await validator.validate_certificate_chain(cert_info.certificate_pem)
            print(f"✅ Certificate validation: {'Valid' if validation['valid'] else 'Invalid'}")

            if not validation['valid']:
                print("Validation errors:")
                for error in validation.get('errors', []):
                    print(f"  - {error}")

            # Get certificate info
            info = await validator.get_certificate_info(cert_info.certificate_pem)
            print(f"📋 Certificate info extracted for: {info.get('subject', 'Unknown')}")

            # Test revocation
            ca.revoke_certificate(cert_info.certificate_id, "Testing revocation")
            validation_after_revoke = await validator.validate_certificate_chain(cert_info.certificate_pem)
            print(f"🔒 Post-revocation validation: {'Invalid' if not validation_after_revoke['valid'] else 'Still valid'}")

        finally:
            await validator.close()

        print("\n🎉 Certificate Validator Demo completed!")

    asyncio.run(main())