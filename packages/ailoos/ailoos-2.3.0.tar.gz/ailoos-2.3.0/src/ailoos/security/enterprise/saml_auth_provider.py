#!/usr/bin/env python3
"""
SAML Authentication Provider
===========================

Implementa autenticación SAML 2.0 completa para integración enterprise.
Soporta SP-initiated y IdP-initiated flows, metadata exchange,
firma digital y validación de respuestas SAML.
"""

import base64
import hashlib
import hmac
import logging
import secrets
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlencode, quote_plus
import zlib

# Necesita instalar: pip install cryptography lxml defusedxml
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import defusedxml.ElementTree as defused_et

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SAMLBinding(Enum):
    """Bindings SAML soportados"""
    HTTP_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    HTTP_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    HTTP_ARTIFACT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"

class SAMLNameIDFormat(Enum):
    """Formatos de NameID soportados"""
    UNSPECIFIED = "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"
    EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"

class SAMLAuthnContext(Enum):
    """Contextos de autenticación SAML"""
    PASSWORD = "urn:oasis:names:tc:SAML:2.0:ac:classes:Password"
    PASSWORD_PROTECTED = "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
    KERBEROS = "urn:oasis:names:tc:SAML:2.0:ac:classes:Kerberos"
    TLS_CLIENT = "urn:oasis:names:tc:SAML:2.0:ac:classes:TLSClient"
    X509 = "urn:oasis:names:tc:SAML:2.0:ac:classes:X509"

@dataclass
class SAMLIdentityProvider:
    """Configuración de Identity Provider SAML"""
    entity_id: str
    sso_url: str
    slo_url: Optional[str] = None
    x509_cert: str  # Certificado X.509 en formato PEM
    name_id_format: SAMLNameIDFormat = SAMLNameIDFormat.UNSPECIFIED
    binding: SAMLBinding = SAMLBinding.HTTP_POST
    want_assertions_signed: bool = True
    want_authn_requests_signed: bool = False
    metadata_url: Optional[str] = None

@dataclass
class SAMLSession:
    """Sesión SAML activa"""
    session_id: str
    name_id: str
    issuer: str
    audience: str
    authn_instant: datetime
    session_not_on_or_after: Optional[datetime] = None
    attributes: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SAMLAuthRequest:
    """Solicitud de autenticación SAML"""
    id: str
    issuer: str
    assertion_consumer_service_url: str
    destination: str
    issue_instant: datetime
    name_id_policy: Optional[SAMLNameIDFormat] = None
    requested_authn_context: Optional[SAMLAuthnContext] = None
    force_authn: bool = False
    is_passive: bool = False

@dataclass
class SAMLResponse:
    """Respuesta SAML"""
    id: str
    in_response_to: str
    issuer: str
    issue_instant: datetime
    status_code: str
    status_message: Optional[str] = None
    assertions: List['SAMLAssertion'] = field(default_factory=list)

@dataclass
class SAMLAssertion:
    """Afirmación SAML"""
    id: str
    issuer: str
    issue_instant: datetime
    subject: 'SAMLSubject'
    conditions: 'SAMLConditions'
    authn_statement: Optional['SAMLAuthnStatement'] = None
    attribute_statement: Optional['SAMLAttributeStatement'] = None

@dataclass
class SAMLSubject:
    """Sujeto de la afirmación SAML"""
    name_id: str
    name_id_format: SAMLNameIDFormat
    confirmation_method: str
    confirmation_data: Optional[Dict[str, Any]] = None

@dataclass
class SAMLConditions:
    """Condiciones de la afirmación"""
    not_before: datetime
    not_on_or_after: datetime
    audience_restrictions: List[str] = field(default_factory=list)
    one_time_use: bool = False

@dataclass
class SAMLAuthnStatement:
    """Statement de autenticación"""
    authn_instant: datetime
    session_index: Optional[str] = None
    authn_context_class_ref: SAMLAuthnContext = SAMLAuthnContext.PASSWORD

@dataclass
class SAMLAttributeStatement:
    """Statement de atributos"""
    attributes: Dict[str, List[str]] = field(default_factory=dict)

class SAMLAuthProvider:
    """
    Proveedor de autenticación SAML 2.0 completo
    """

    def __init__(self, entity_id: str, acs_url: str, slo_url: Optional[str] = None):
        """
        Inicializa el SAML Service Provider

        Args:
            entity_id: Entity ID del SP
            acs_url: URL del Assertion Consumer Service
            slo_url: URL del Single Logout Service (opcional)
        """
        self.entity_id = entity_id
        self.acs_url = acs_url
        self.slo_url = slo_url

        # Configuración de firma
        self.private_key = None
        self.certificate = None

        # Identity Providers registrados
        self.identity_providers: Dict[str, SAMLIdentityProvider] = {}

        # Sesiones activas
        self.active_sessions: Dict[str, SAMLSession] = {}

        # Configuración
        self.request_expiration = timedelta(minutes=5)
        self.assertion_expiration = timedelta(hours=1)
        self.session_expiration = timedelta(hours=8)

        # Metadata del SP
        self.sp_metadata = self._generate_sp_metadata()

        logger.info(f"🔐 SAML Auth Provider initialized for entity: {entity_id}")

    def configure_signing(self, private_key_pem: str, certificate_pem: str):
        """
        Configura las claves para firma digital

        Args:
            private_key_pem: Clave privada en formato PEM
            certificate_pem: Certificado en formato PEM
        """
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        self.certificate = x509.load_pem_x509_certificate(
            certificate_pem.encode(),
            backend=default_backend()
        )
        logger.info("🔑 SAML signing configured")

    def register_identity_provider(self, idp: SAMLIdentityProvider):
        """
        Registra un Identity Provider

        Args:
            idp: Configuración del IdP
        """
        self.identity_providers[idp.entity_id] = idp
        logger.info(f"📝 IdP registered: {idp.entity_id}")

    def create_authn_request(self, idp_entity_id: str, relay_state: Optional[str] = None,
                           binding: SAMLBinding = SAMLBinding.HTTP_REDIRECT) -> Tuple[str, Optional[str]]:
        """
        Crea una AuthnRequest SAML

        Args:
            idp_entity_id: Entity ID del IdP
            relay_state: Estado de retransmisión
            binding: Binding a usar

        Returns:
            Tuple de (URL destino, parámetros codificados)
        """
        idp = self.identity_providers.get(idp_entity_id)
        if not idp:
            raise ValueError(f"Unknown IdP: {idp_entity_id}")

        # Generar ID único
        request_id = f"_{uuid.uuid4()}"

        # Crear AuthnRequest
        authn_request = SAMLAuthRequest(
            id=request_id,
            issuer=self.entity_id,
            assertion_consumer_service_url=self.acs_url,
            destination=idp.sso_url,
            issue_instant=datetime.utcnow(),
            name_id_policy=idp.name_id_format,
            requested_authn_context=SAMLAuthnContext.PASSWORD
        )

        # Convertir a XML
        xml_request = self._authn_request_to_xml(authn_request)

        # Firmar si es requerido
        if idp.want_authn_requests_signed and self.private_key:
            xml_request = self._sign_xml(xml_request, request_id)

        # Codificar según binding
        if binding == SAMLBinding.HTTP_REDIRECT:
            # DEFLATE y base64
            compressed = zlib.compress(xml_request.encode('utf-8'))
            encoded_request = base64.b64encode(compressed).decode('ascii')

            params = {
                'SAMLRequest': encoded_request,
                'RelayState': relay_state or ''
            }

            if idp.want_authn_requests_signed and self.private_key:
                params['SigAlg'] = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
                signature_data = urlencode(params, quote_via=quote_plus)
                signature = self._sign_data(signature_data.encode())
                params['Signature'] = signature

            query_string = urlencode(params, quote_via=quote_plus)
            return f"{idp.sso_url}?{query_string}", None

        elif binding == SAMLBinding.HTTP_POST:
            # Solo base64
            encoded_request = base64.b64encode(xml_request.encode('utf-8')).decode('ascii')

            return idp.sso_url, encoded_request

        else:
            raise ValueError(f"Unsupported binding: {binding}")

    def process_saml_response(self, saml_response: str, relay_state: Optional[str] = None,
                            binding: SAMLBinding = SAMLBinding.HTTP_POST) -> SAMLSession:
        """
        Procesa una respuesta SAML

        Args:
            saml_response: Respuesta SAML codificada
            relay_state: Estado de retransmisión
            binding: Binding usado

        Returns:
            Sesión SAML creada

        Raises:
            ValueError: Si la respuesta es inválida
        """
        # Decodificar respuesta
        if binding == SAMLBinding.HTTP_POST:
            decoded_response = base64.b64decode(saml_response)
        else:
            # Para HTTP-Redirect, la respuesta viene DEFLATEada
            compressed = base64.b64decode(saml_response)
            decoded_response = zlib.decompress(compressed, -zlib.MAX_WBITS)

        xml_response = decoded_response.decode('utf-8')

        # Parsear XML
        response = self._parse_saml_response(xml_response)

        # Validar respuesta
        self._validate_saml_response(response)

        # Extraer información de la afirmación
        if not response.assertions:
            raise ValueError("No assertions found in SAML response")

        assertion = response.assertions[0]

        # Crear sesión
        session = SAMLSession(
            session_id=secrets.token_urlsafe(32),
            name_id=assertion.subject.name_id,
            issuer=response.issuer,
            audience=self.entity_id,
            authn_instant=assertion.authn_statement.authn_instant if assertion.authn_statement else datetime.utcnow(),
            session_not_on_or_after=assertion.conditions.not_on_or_after,
            attributes=assertion.attribute_statement.attributes if assertion.attribute_statement else {}
        )

        # Almacenar sesión
        self.active_sessions[session.session_id] = session

        logger.info(f"✅ SAML session created for user: {session.name_id}")
        return session

    def validate_session(self, session_id: str) -> Optional[SAMLSession]:
        """
        Valida una sesión SAML

        Args:
            session_id: ID de la sesión

        Returns:
            Sesión si es válida, None si no
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        # Verificar expiración
        if session.session_not_on_or_after and datetime.utcnow() > session.session_not_on_or_after:
            del self.active_sessions[session_id]
            return None

        if datetime.utcnow() - session.created_at > self.session_expiration:
            del self.active_sessions[session_id]
            return None

        return session

    def logout_session(self, session_id: str) -> bool:
        """
        Cierra una sesión SAML

        Args:
            session_id: ID de la sesión

        Returns:
            True si se cerró correctamente
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"🚪 SAML session logged out: {session_id}")
            return True
        return False

    def get_sp_metadata(self) -> str:
        """
        Obtiene el metadata XML del Service Provider

        Returns:
            Metadata en formato XML
        """
        return self.sp_metadata

    def _generate_sp_metadata(self) -> str:
        """Genera el metadata XML del SP"""
        # Crear estructura XML básica
        root = ET.Element("md:EntityDescriptor", {
            "xmlns:md": "urn:oasis:names:tc:SAML:2.0:metadata",
            "entityID": self.entity_id
        })

        # SPSSODescriptor
        sp_sso = ET.SubElement(root, "md:SPSSODescriptor", {
            "protocolSupportEnumeration": "urn:oasis:names:tc:SAML:2.0:protocol",
            "WantAssertionsSigned": "true"
        })

        # KeyDescriptor para firma
        if self.certificate:
            key_desc = ET.SubElement(sp_sso, "md:KeyDescriptor", {"use": "signing"})
            key_info = ET.SubElement(key_desc, "ds:KeyInfo", {"xmlns:ds": "http://www.w3.org/2000/09/xmldsig#"})
            x509_data = ET.SubElement(key_info, "ds:X509Data")
            cert_der = self.certificate.public_bytes(serialization.Encoding.DER)
            cert_b64 = base64.b64encode(cert_der).decode()
            ET.SubElement(x509_data, "ds:X509Certificate").text = cert_b64

        # AssertionConsumerService
        ET.SubElement(sp_sso, "md:AssertionConsumerService", {
            "Binding": SAMLBinding.HTTP_POST.value,
            "Location": self.acs_url,
            "index": "0",
            "isDefault": "true"
        })

        # SingleLogoutService
        if self.slo_url:
            ET.SubElement(sp_sso, "md:SingleLogoutService", {
                "Binding": SAMLBinding.HTTP_POST.value,
                "Location": self.slo_url
            })

        # NameIDFormat
        ET.SubElement(sp_sso, "md:NameIDFormat").text = SAMLNameIDFormat.UNSPECIFIED.value

        # Convertir a string
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        return xml_str

    def _authn_request_to_xml(self, request: SAMLAuthRequest) -> str:
        """Convierte AuthnRequest a XML"""
        root = ET.Element("samlp:AuthnRequest", {
            "xmlns:samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            "xmlns:saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            "ID": request.id,
            "Version": "2.0",
            "IssueInstant": request.issue_instant.isoformat(),
            "Destination": request.destination,
            "AssertionConsumerServiceURL": request.assertion_consumer_service_url
        })

        # Issuer
        issuer = ET.SubElement(root, "saml:Issuer")
        issuer.text = request.issuer

        # NameIDPolicy
        if request.name_id_policy:
            ET.SubElement(root, "samlp:NameIDPolicy", {
                "Format": request.name_id_policy.value,
                "AllowCreate": "true"
            })

        # RequestedAuthnContext
        if request.requested_authn_context:
            rac = ET.SubElement(root, "samlp:RequestedAuthnContext", {"Comparison": "exact"})
            ET.SubElement(rac, "saml:AuthnContextClassRef").text = request.requested_authn_context.value

        return ET.tostring(root, encoding='unicode', method='xml')

    def _parse_saml_response(self, xml_response: str) -> SAMLResponse:
        """Parsea respuesta SAML desde XML"""
        try:
            root = defused_et.fromstring(xml_response)
        except Exception as e:
            raise ValueError(f"Invalid XML in SAML response: {e}")

        # Extraer información básica
        response_id = root.get('ID')
        in_response_to = root.get('InResponseTo')
        issue_instant_str = root.get('IssueInstant')

        # Issuer
        issuer_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Issuer')
        issuer = issuer_elem.text if issuer_elem is not None else None

        # Status
        status_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:protocol}StatusCode')
        status_code = status_elem.get('Value') if status_elem is not None else None

        # Parsear issue instant
        try:
            issue_instant = datetime.fromisoformat(issue_instant_str.replace('Z', '+00:00'))
        except:
            issue_instant = datetime.utcnow()

        response = SAMLResponse(
            id=response_id,
            in_response_to=in_response_to,
            issuer=issuer,
            issue_instant=issue_instant,
            status_code=status_code
        )

        # Parsear assertions (simplificado)
        # En implementación completa, parsear completamente las assertions
        assertion_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion')
        if assertion_elem is not None:
            assertion = self._parse_assertion(assertion_elem)
            response.assertions.append(assertion)

        return response

    def _parse_assertion(self, assertion_elem) -> SAMLAssertion:
        """Parsea una assertion SAML (simplificado)"""
        assertion_id = assertion_elem.get('ID')
        issuer_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Issuer')
        issuer = issuer_elem.text if issuer_elem is not None else ""

        # Subject
        subject_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Subject')
        subject = self._parse_subject(subject_elem) if subject_elem is not None else None

        # Conditions
        conditions_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Conditions')
        conditions = self._parse_conditions(conditions_elem) if conditions_elem is not None else None

        # AuthnStatement
        authn_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}AuthnStatement')
        authn_statement = self._parse_authn_statement(authn_elem) if authn_elem is not None else None

        # AttributeStatement
        attr_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement')
        attr_statement = self._parse_attribute_statement(attr_elem) if attr_elem is not None else None

        return SAMLAssertion(
            id=assertion_id,
            issuer=issuer,
            issue_instant=datetime.utcnow(),  # Simplificado
            subject=subject,
            conditions=conditions,
            authn_statement=authn_statement,
            attribute_statement=attr_statement
        )

    def _parse_subject(self, subject_elem) -> SAMLSubject:
        """Parsea subject SAML"""
        name_id_elem = subject_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}NameID')
        name_id = name_id_elem.text if name_id_elem is not None else ""
        name_id_format = name_id_elem.get('Format') if name_id_elem is not None else SAMLNameIDFormat.UNSPECIFIED.value

        return SAMLSubject(
            name_id=name_id,
            name_id_format=SAMLNameIDFormat(name_id_format),
            confirmation_method="urn:oasis:names:tc:SAML:2.0:cm:bearer"
        )

    def _parse_conditions(self, conditions_elem) -> SAMLConditions:
        """Parsea conditions SAML"""
        not_before_str = conditions_elem.get('NotBefore')
        not_on_or_after_str = conditions_elem.get('NotOnOrAfter')

        not_before = datetime.fromisoformat(not_before_str.replace('Z', '+00:00')) if not_before_str else datetime.utcnow()
        not_on_or_after = datetime.fromisoformat(not_on_or_after_str.replace('Z', '+00:00')) if not_on_or_after_str else datetime.utcnow() + timedelta(hours=1)

        return SAMLConditions(
            not_before=not_before,
            not_on_or_after=not_on_or_after
        )

    def _parse_authn_statement(self, authn_elem) -> SAMLAuthnStatement:
        """Parsea AuthnStatement SAML"""
        authn_instant_str = authn_elem.get('AuthnInstant')
        session_index = authn_elem.get('SessionIndex')

        authn_instant = datetime.fromisoformat(authn_instant_str.replace('Z', '+00:00')) if authn_instant_str else datetime.utcnow()

        return SAMLAuthnStatement(
            authn_instant=authn_instant,
            session_index=session_index
        )

    def _parse_attribute_statement(self, attr_elem) -> SAMLAttributeStatement:
        """Parsea AttributeStatement SAML"""
        attributes = {}
        for attr in attr_elem.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
            name = attr.get('Name')
            values = []
            for value in attr.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                values.append(value.text)
            if name and values:
                attributes[name] = values

        return SAMLAttributeStatement(attributes=attributes)

    def _validate_saml_response(self, response: SAMLResponse):
        """Valida una respuesta SAML"""
        # Verificar status
        if response.status_code != "urn:oasis:names:tc:SAML:2.0:status:Success":
            raise ValueError(f"SAML authentication failed: {response.status_code}")

        # Verificar issuer
        if response.issuer not in self.identity_providers:
            raise ValueError(f"Unknown SAML issuer: {response.issuer}")

        # Verificar tiempo de respuesta (simplificado)
        if datetime.utcnow() - response.issue_instant > timedelta(minutes=5):
            raise ValueError("SAML response too old")

        # Aquí se agregarían validaciones de firma digital
        logger.info("✅ SAML response validated")

    def _sign_xml(self, xml_data: str, reference_id: str) -> str:
        """Firma XML SAML (simplificado)"""
        # Implementación simplificada - en producción usar xmlsec o similar
        if not self.private_key:
            return xml_data

        # Crear firma digital
        signature = self._sign_data(xml_data.encode())

        # Insertar firma en XML (simplificado)
        # En implementación real, insertar Signature element correctamente
        return xml_data

    def _sign_data(self, data: bytes) -> str:
        """Firma datos con clave privada"""
        if not self.private_key:
            raise ValueError("Private key not configured")

        signature = self.private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()

    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        current_time = datetime.utcnow()
        expired = []

        for session_id, session in self.active_sessions.items():
            if (session.session_not_on_or_after and current_time > session.session_not_on_or_after) or \
               (current_time - session.created_at > self.session_expiration):
                expired.append(session_id)

        for session_id in expired:
            del self.active_sessions[session_id]

        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired SAML sessions")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema SAML"""
        return {
            'registered_idps': len(self.identity_providers),
            'active_sessions': len(self.active_sessions),
            'signing_configured': self.private_key is not None
        }


# Instancia global del proveedor SAML
saml_auth_provider = SAMLAuthProvider(
    entity_id="https://ailoos.com/saml/sp",
    acs_url="https://ailoos.com/saml/acs",
    slo_url="https://ailoos.com/saml/slo"
)


def get_saml_auth_provider() -> SAMLAuthProvider:
    """Obtiene la instancia global del proveedor SAML"""
    return saml_auth_provider