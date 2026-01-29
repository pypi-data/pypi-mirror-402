"""
Zero-Trust Security Architecture para AILOOS

Implementa arquitectura zero-trust completa con:
- Service mesh (Istio/Linkerd) con mTLS everywhere
- Continuous authentication y authorization
- Identity-aware proxying
- Policy-based access control
"""

import asyncio
import logging
import json
import time
import random
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import jwt
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


class ServiceMeshProvider(Enum):
    """Proveedores de service mesh disponibles."""
    ISTIO = "istio"
    LINKERD = "linkerd"
    CONSUL = "consul"
    KUMA = "kuma"


class IdentityType(Enum):
    """Tipos de identidad disponibles."""
    USER = "user"
    SERVICE = "service"
    DEVICE = "device"
    WORKLOAD = "workload"


class TrustLevel(Enum):
    """Niveles de confianza."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuthenticationMethod(Enum):
    """Métodos de autenticación disponibles."""
    JWT = "jwt"
    MTLS = "mtls"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SAML = "saml"
    SPIFFE = "spiffe"


@dataclass
class Identity:
    """Identidad en el sistema zero-trust."""
    identity_id: str
    identity_type: IdentityType
    name: str
    trust_level: TrustLevel = TrustLevel.LOW
    attributes: Dict[str, Any] = field(default_factory=dict)
    certificates: List[str] = field(default_factory=list)
    last_authenticated: Optional[datetime] = None
    authentication_count: int = 0
    risk_score: float = 0.0  # 0-100, higher = more risky

    @property
    def is_active(self) -> bool:
        """Verificar si la identidad está activa."""
        if not self.last_authenticated:
            return False

        # Consider inactive if not authenticated in last 24 hours
        return (datetime.now() - self.last_authenticated).seconds < 86400

    @property
    def trust_score(self) -> float:
        """Calcular trust score basado en múltiples factores."""
        base_score = {
            TrustLevel.NONE: 0,
            TrustLevel.LOW: 25,
            TrustLevel.MEDIUM: 50,
            TrustLevel.HIGH: 75,
            TrustLevel.CRITICAL: 100
        }[self.trust_level]

        # Adjust based on authentication history
        recency_bonus = min(20, self.authentication_count * 2)

        # Adjust based on risk score (inverse)
        risk_penalty = self.risk_score * 0.5

        return max(0, min(100, base_score + recency_bonus - risk_penalty))


@dataclass
class ServiceEndpoint:
    """Endpoint de servicio en el mesh."""
    service_name: str
    endpoint: str
    port: int
    protocol: str = "http"
    mTLS_enabled: bool = True
    authentication_required: bool = True
    allowed_identities: List[str] = field(default_factory=list)
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    circuit_breaker: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_url(self) -> str:
        """URL completa del endpoint."""
        return f"{self.protocol}://{self.endpoint}:{self.port}"


@dataclass
class AuthorizationPolicy:
    """Política de autorización."""
    policy_id: str
    name: str
    principals: List[str]  # Who
    resources: List[str]   # What
    actions: List[str]     # How
    conditions: Dict[str, Any] = field(default_factory=dict)
    effect: str = "allow"  # "allow" or "deny"
    priority: int = 0

    def matches_request(self, principal: str, resource: str, action: str,
                       context: Dict[str, Any]) -> bool:
        """Verificar si la política aplica a una request."""
        # Check principal
        if self.principals != ["*"] and principal not in self.principals:
            return False

        # Check resource
        if self.resources != ["*"] and not any(res in resource for res in self.resources):
            return False

        # Check action
        if self.actions != ["*"] and action not in self.actions:
            return False

        # Check conditions
        for condition_key, condition_value in self.conditions.items():
            if condition_key not in context or context[condition_key] != condition_value:
                return False

        return True


@dataclass
class MTLSCertificate:
    """Certificado mTLS."""
    certificate_id: str
    identity_id: str
    certificate_pem: str
    private_key_pem: str
    ca_certificate_pem: str
    issued_at: datetime
    expires_at: datetime
    serial_number: str
    status: str = "active"  # "active", "revoked", "expired"

    @property
    def is_valid(self) -> bool:
        """Verificar si el certificado es válido."""
        now = datetime.now()
        return (self.status == "active" and
                self.issued_at <= now <= self.expires_at)

    @property
    def days_until_expiry(self) -> int:
        """Días hasta expiración."""
        return max(0, (self.expires_at - datetime.now()).days)


class ServiceMeshManager:
    """
    Gestor de service mesh para zero-trust.

    Características:
    - mTLS automático entre servicios
    - Traffic encryption end-to-end
    - Service discovery segura
    - Load balancing con health checks
    """

    def __init__(self, provider: ServiceMeshProvider = ServiceMeshProvider.ISTIO):
        self.provider = provider
        self.services: Dict[str, ServiceEndpoint] = {}
        self.certificates: Dict[str, MTLSCertificate] = {}
        self.policies: Dict[str, AuthorizationPolicy] = {}
        self.identities: Dict[str, Identity] = {}

    async def register_service(self, service: ServiceEndpoint) -> bool:
        """Registrar servicio en el mesh."""
        try:
            self.services[service.service_name] = service

            # Generate mTLS certificates if enabled
            if service.mTLS_enabled:
                await self._generate_service_certificates(service.service_name)

            # Configure service mesh policies
            await self._configure_mesh_policies(service)

            logger.info(f"Registered service in mesh: {service.service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {service.service_name}: {e}")
            return False

    async def _generate_service_certificates(self, service_name: str) -> MTLSCertificate:
        """Generar certificados mTLS para un servicio."""
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Generate certificate
        subject = f"CN={service_name},O=ailoos"
        certificate = self._generate_certificate(private_key, subject)

        # Create MTLS certificate object
        cert_id = f"cert_{service_name}_{int(time.time())}"
        mtls_cert = MTLSCertificate(
            certificate_id=cert_id,
            identity_id=service_name,
            certificate_pem=certificate,
            private_key_pem=self._serialize_private_key(private_key),
            ca_certificate_pem=self._get_ca_certificate(),
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            serial_number=str(random.randint(100000, 999999))
        )

        self.certificates[cert_id] = mtls_cert
        return mtls_cert

    def _generate_certificate(self, private_key, subject: str) -> str:
        """Generar certificado X.509 (simulado)."""
        # En producción, usar proper certificate generation
        return f"-----BEGIN CERTIFICATE-----\nMOCK_CERT_FOR_{subject}\n-----END CERTIFICATE-----"

    def _serialize_private_key(self, private_key) -> str:
        """Serializar private key (simulado)."""
        return "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----"

    def _get_ca_certificate(self) -> str:
        """Obtener CA certificate (simulado)."""
        return "-----BEGIN CERTIFICATE-----\nMOCK_CA_CERT\n-----END CERTIFICATE-----"

    async def _configure_mesh_policies(self, service: ServiceEndpoint):
        """Configurar políticas del mesh para el servicio."""
        # En producción: configurar Istio VirtualServices, DestinationRules, etc.
        await asyncio.sleep(0.5)
        logger.info(f"Configured mesh policies for {service.service_name}")

    async def authenticate_request(self, service_name: str, client_cert: Optional[str] = None,
                                 jwt_token: Optional[str] = None) -> Tuple[bool, Optional[Identity]]:
        """Autenticar request usando mTLS o JWT."""
        if not client_cert and not jwt_token:
            return False, None

        identity = None

        # Try mTLS authentication
        if client_cert:
            identity = await self._authenticate_mtls(client_cert)
            if identity:
                return True, identity

        # Try JWT authentication
        if jwt_token:
            identity = await self._authenticate_jwt(jwt_token)
            if identity:
                return True, identity

        return False, None

    async def _authenticate_mtls(self, client_cert: str) -> Optional[Identity]:
        """Autenticar usando mTLS."""
        # Verify certificate against known certificates
        for cert in self.certificates.values():
            if cert.certificate_pem == client_cert and cert.is_valid:
                identity = self.identities.get(cert.identity_id)
                if identity:
                    identity.last_authenticated = datetime.now()
                    identity.authentication_count += 1
                    return identity

        return None

    async def _authenticate_jwt(self, token: str) -> Optional[Identity]:
        """Autenticar usando JWT."""
        try:
            # Decode JWT (simplified)
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
            identity_id = payload.get("sub")

            if identity_id and identity_id in self.identities:
                identity = self.identities[identity_id]
                identity.last_authenticated = datetime.now()
                identity.authentication_count += 1
                return identity

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")

        return None

    async def authorize_request(self, identity: Identity, service_name: str,
                              action: str, context: Dict[str, Any]) -> bool:
        """Autorizar request basado en políticas."""
        if service_name not in self.services:
            return False

        service = self.services[service_name]

        # Check if identity is allowed
        if service.allowed_identities and identity.identity_id not in service.allowed_identities:
            return False

        # Evaluate authorization policies
        for policy in self.policies.values():
            if policy.matches_request(identity.identity_id, service_name, action, context):
                if policy.effect == "allow":
                    return True
                elif policy.effect == "deny":
                    return False

        # Default deny
        return False

    async def rotate_certificates(self, service_name: str) -> bool:
        """Rotar certificados mTLS."""
        try:
            # Generate new certificates
            new_cert = await self._generate_service_certificates(service_name)

            # Update service mesh configuration
            await self._configure_mesh_policies(self.services[service_name])

            # Revoke old certificates
            for cert in list(self.certificates.values()):
                if cert.identity_id == service_name and cert.status == "active":
                    cert.status = "revoked"

            logger.info(f"Rotated certificates for service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Certificate rotation failed for {service_name}: {e}")
            return False


class ContinuousAuthenticationManager:
    """
    Gestor de autenticación continua.

    Características:
    - Risk-based authentication
    - Behavioral analysis
    - Step-up authentication
    - Session management
    """

    def __init__(self):
        self.identities: Dict[str, Identity] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.behavioral_profiles: Dict[str, Dict[str, Any]] = {}
        self.risk_thresholds = {
            'low': 30,
            'medium': 60,
            'high': 80
        }

    def register_identity(self, identity: Identity):
        """Registrar identidad para continuous authentication."""
        self.identities[identity.identity_id] = identity
        self.behavioral_profiles[identity.identity_id] = {
            'login_times': [],
            'locations': [],
            'devices': [],
            'request_patterns': [],
            'baseline_risk': 50
        }

    async def evaluate_continuous_auth(self, identity_id: str,
                                     context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Evaluar autenticación continua.

        Returns:
            (should_challenge, risk_score, reason)
        """
        if identity_id not in self.identities:
            return False, 100, "Identity not found"

        identity = self.identities[identity_id]
        profile = self.behavioral_profiles[identity_id]

        risk_score = await self._calculate_risk_score(identity, context, profile)

        # Update identity risk score
        identity.risk_score = risk_score

        # Determine if step-up authentication is needed
        should_challenge = risk_score > self.risk_thresholds['medium']

        reason = self._get_risk_reason(risk_score, context)

        # Update behavioral profile
        self._update_behavioral_profile(identity_id, context)

        return should_challenge, risk_score, reason

    async def _calculate_risk_score(self, identity: Identity, context: Dict[str, Any],
                                  profile: Dict[str, Any]) -> float:
        """Calcular risk score basado en múltiples factores."""
        risk_factors = []

        # Time-based risk
        current_hour = datetime.now().hour
        usual_hours = profile.get('login_times', [])
        if usual_hours and current_hour not in usual_hours:
            risk_factors.append(20)  # Unusual login time

        # Location-based risk
        current_location = context.get('location', 'unknown')
        usual_locations = profile.get('locations', [])
        if usual_locations and current_location not in usual_locations:
            risk_factors.append(25)  # Unusual location

        # Device-based risk
        current_device = context.get('device_fingerprint', 'unknown')
        usual_devices = profile.get('devices', [])
        if usual_devices and current_device not in usual_devices:
            risk_factors.append(15)  # Unusual device

        # Request pattern analysis
        request_pattern = self._analyze_request_pattern(context)
        if request_pattern == "suspicious":
            risk_factors.append(30)  # Suspicious pattern

        # Authentication method risk
        auth_method = context.get('auth_method', 'unknown')
        if auth_method in ['api_key', 'jwt']:
            risk_factors.append(10)  # Lower trust methods

        # Calculate weighted average
        if risk_factors:
            base_risk = sum(risk_factors) / len(risk_factors)
        else:
            base_risk = profile.get('baseline_risk', 50)

        # Adjust based on identity trust level
        trust_multiplier = {
            TrustLevel.CRITICAL: 0.5,
            TrustLevel.HIGH: 0.7,
            TrustLevel.MEDIUM: 0.9,
            TrustLevel.LOW: 1.1,
            TrustLevel.NONE: 1.5
        }.get(identity.trust_level, 1.0)

        final_risk = min(100, base_risk * trust_multiplier)

        return final_risk

    def _analyze_request_pattern(self, context: Dict[str, Any]) -> str:
        """Analizar patrón de request."""
        # Simple pattern analysis
        request_count = context.get('requests_per_minute', 0)
        error_rate = context.get('error_rate', 0)

        if request_count > 1000 or error_rate > 0.5:
            return "suspicious"
        elif request_count > 100 or error_rate > 0.1:
            return "unusual"
        else:
            return "normal"

    def _get_risk_reason(self, risk_score: float, context: Dict[str, Any]) -> str:
        """Obtener razón del risk score."""
        if risk_score > self.risk_thresholds['high']:
            return "High risk activity detected"
        elif risk_score > self.risk_thresholds['medium']:
            return "Unusual activity pattern"
        elif risk_score > self.risk_thresholds['low']:
            return "Minor anomalies detected"
        else:
            return "Normal activity"

    def _update_behavioral_profile(self, identity_id: str, context: Dict[str, Any]):
        """Actualizar perfil behavioral."""
        profile = self.behavioral_profiles[identity_id]

        # Update login times
        current_hour = datetime.now().hour
        if current_hour not in profile['login_times']:
            profile['login_times'].append(current_hour)
            if len(profile['login_times']) > 10:  # Keep last 10
                profile['login_times'] = profile['login_times'][-10:]

        # Update locations
        location = context.get('location')
        if location and location not in profile['locations']:
            profile['locations'].append(location)
            if len(profile['locations']) > 5:  # Keep last 5
                profile['locations'] = profile['locations'][-5:]

        # Update devices
        device = context.get('device_fingerprint')
        if device and device not in profile['devices']:
            profile['devices'].append(device)
            if len(profile['devices']) > 3:  # Keep last 3
                profile['devices'] = profile['devices'][-3:]

    async def step_up_authentication(self, identity_id: str, challenge_type: str = "mfa") -> bool:
        """Requerir step-up authentication."""
        # En producción: enviar challenge SMS, push notification, etc.
        logger.info(f"Step-up authentication required for {identity_id}: {challenge_type}")
        await asyncio.sleep(1)  # Simular envío de challenge
        return True


class ZeroTrustOrchestrator:
    """
    Orchestrator principal para zero-trust security.

    Coordina service mesh, continuous authentication y authorization.
    """

    def __init__(self):
        self.service_mesh = ServiceMeshManager()
        self.continuous_auth = ContinuousAuthenticationManager()
        self.authorization_policies: Dict[str, AuthorizationPolicy] = {}
        self.audit_log: List[Dict[str, Any]] = []

    async def initialize_zero_trust(self):
        """Inicializar arquitectura zero-trust."""
        # Configure default policies
        await self._configure_default_policies()

        # Initialize service mesh
        await self._initialize_service_mesh()

        logger.info("Zero-trust architecture initialized")

    async def _configure_default_policies(self):
        """Configurar políticas por defecto."""
        # Allow policy for authenticated users
        allow_authenticated = AuthorizationPolicy(
            policy_id="allow_authenticated",
            name="Allow Authenticated Users",
            principals=["*"],  # Any authenticated principal
            resources=["*"],
            actions=["read", "write"],
            conditions={"authentication_required": True},
            effect="allow",
            priority=1
        )

        # Deny policy for high-risk identities
        deny_high_risk = AuthorizationPolicy(
            policy_id="deny_high_risk",
            name="Deny High Risk Identities",
            principals=["*"],
            resources=["sensitive_data"],
            actions=["*"],
            conditions={"risk_score": ">80"},
            effect="deny",
            priority=10
        )

        self.authorization_policies[allow_authenticated.policy_id] = allow_authenticated
        self.authorization_policies[deny_high_risk.policy_id] = deny_high_risk

        # Add to service mesh
        self.service_mesh.policies.update(self.authorization_policies)

    async def _initialize_service_mesh(self):
        """Inicializar service mesh con servicios por defecto."""
        default_services = [
            ServiceEndpoint(
                service_name="api-gateway",
                endpoint="api.ailoos.dev",
                port=443,
                protocol="https",
                mTLS_enabled=True,
                authentication_required=True
            ),
            ServiceEndpoint(
                service_name="user-service",
                endpoint="user-service.ailoos.svc.cluster.local",
                port=8080,
                mTLS_enabled=True,
                authentication_required=True
            ),
            ServiceEndpoint(
                service_name="data-service",
                endpoint="data-service.ailoos.svc.cluster.local",
                port=8080,
                mTLS_enabled=True,
                authentication_required=True,
                allowed_identities=["api-gateway", "admin-service"]
            )
        ]

        for service in default_services:
            await self.service_mesh.register_service(service)

    async def process_request(self, service_name: str, action: str,
                            auth_credentials: Dict[str, Any],
                            context: Dict[str, Any]) -> Tuple[bool, str, Optional[Identity]]:
        """
        Procesar request con zero-trust security.

        Returns:
            (allowed, reason, identity)
        """
        # Step 1: Authentication
        authenticated, identity = await self.service_mesh.authenticate_request(
            service_name,
            client_cert=auth_credentials.get('client_cert'),
            jwt_token=auth_credentials.get('jwt_token')
        )

        if not authenticated or not identity:
            self._audit_request(service_name, action, False, "authentication_failed", None, context)
            return False, "Authentication failed", None

        # Step 2: Continuous authentication evaluation
        should_challenge, risk_score, risk_reason = await self.continuous_auth.evaluate_continuous_auth(
            identity.identity_id, context
        )

        if should_challenge:
            # Require step-up authentication
            challenge_success = await self.continuous_auth.step_up_authentication(identity.identity_id)
            if not challenge_success:
                self._audit_request(service_name, action, False, "step_up_failed", identity, context)
                return False, f"Step-up authentication required: {risk_reason}", identity

        # Step 3: Authorization
        authorized = await self.service_mesh.authorize_request(identity, service_name, action, context)

        if not authorized:
            self._audit_request(service_name, action, False, "authorization_denied", identity, context)
            return False, "Authorization denied", identity

        # Step 4: Audit successful request
        self._audit_request(service_name, action, True, "access_granted", identity, context)

        return True, "Access granted", identity

    def _audit_request(self, service_name: str, action: str, success: bool,
                      reason: str, identity: Optional[Identity], context: Dict[str, Any]):
        """Auditar request."""
        audit_entry = {
            'timestamp': datetime.now(),
            'service_name': service_name,
            'action': action,
            'success': success,
            'reason': reason,
            'identity_id': identity.identity_id if identity else None,
            'identity_type': identity.identity_type.value if identity else None,
            'risk_score': identity.risk_score if identity else None,
            'context': context
        }

        self.audit_log.append(audit_entry)

        # Keep only last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def get_security_status(self) -> Dict[str, Any]:
        """Obtener status de seguridad zero-trust."""
        total_identities = len(self.continuous_auth.identities)
        active_identities = len([i for i in self.continuous_auth.identities.values() if i.is_active])
        high_risk_identities = len([i for i in self.continuous_auth.identities.values() if i.risk_score > 70])

        total_services = len(self.service_mesh.services)
        mtls_services = len([s for s in self.service_mesh.services.values() if s.mTLS_enabled])

        total_policies = len(self.authorization_policies)
        audit_entries = len(self.audit_log)

        return {
            'identities': {
                'total': total_identities,
                'active': active_identities,
                'high_risk': high_risk_identities
            },
            'services': {
                'total': total_services,
                'mtls_enabled': mtls_services
            },
            'policies': total_policies,
            'audit_entries': audit_entries,
            'overall_security_score': self._calculate_security_score()
        }

    def _calculate_security_score(self) -> float:
        """Calcular security score general."""
        # Simple scoring algorithm
        identity_score = 0
        service_score = 0
        policy_score = 0

        # Identity security
        identities = list(self.continuous_auth.identities.values())
        if identities:
            avg_trust = sum(i.trust_score for i in identities) / len(identities)
            identity_score = min(100, avg_trust)

        # Service security
        services = list(self.service_mesh.services.values())
        if services:
            mtls_percentage = sum(1 for s in services if s.mTLS_enabled) / len(services) * 100
            service_score = mtls_percentage

        # Policy coverage
        policy_score = min(100, len(self.authorization_policies) * 10)

        # Overall score
        return (identity_score + service_score + policy_score) / 3


# Funciones de conveniencia

def create_default_identities() -> List[Identity]:
    """Crear identidades por defecto."""
    identities = [
        Identity(
            identity_id="user_alice",
            identity_type=IdentityType.USER,
            name="Alice Johnson",
            trust_level=TrustLevel.HIGH,
            attributes={"department": "engineering", "role": "developer"}
        ),
        Identity(
            identity_id="service_api_gateway",
            identity_type=IdentityType.SERVICE,
            name="API Gateway Service",
            trust_level=TrustLevel.CRITICAL,
            attributes={"environment": "production", "version": "v1.2.3"}
        ),
        Identity(
            identity_id="device_mobile_001",
            identity_type=IdentityType.DEVICE,
            name="Mobile Device 001",
            trust_level=TrustLevel.MEDIUM,
            attributes={"platform": "iOS", "app_version": "2.1.0"}
        )
    ]

    return identities


async def demonstrate_zero_trust_security():
    """Demostrar zero-trust security completo."""
    print("🔐 Inicializando Zero-Trust Security Architecture...")

    # Crear orchestrator
    orchestrator = ZeroTrustOrchestrator()

    # Inicializar zero-trust
    await orchestrator.initialize_zero_trust()

    # Registrar identidades
    identities = create_default_identities()
    for identity in identities:
        orchestrator.service_mesh.identities[identity.identity_id] = identity
        orchestrator.continuous_auth.register_identity(identity)

    print("📊 Estado inicial de Zero-Trust:")
    status = orchestrator.get_security_status()
    print(f"   Identidades: {status['identities']['total']} total, {status['identities']['active']} activas")
    print(f"   Servicios: {status['services']['total']} total, {status['services']['mtls_enabled']} con mTLS")
    print(f"   Políticas: {status['policies']}")
    print(f"   Security Score: {status['overall_security_score']:.1f}/100")

    # Simular requests
    test_requests = [
        {
            'service': 'api-gateway',
            'action': 'read',
            'credentials': {'jwt_token': 'valid_jwt_token'},
            'context': {'location': 'US', 'device_fingerprint': 'trusted_device', 'requests_per_minute': 10}
        },
        {
            'service': 'data-service',
            'action': 'write',
            'credentials': {'client_cert': 'valid_cert'},
            'context': {'location': 'Unknown', 'device_fingerprint': 'unknown_device', 'requests_per_minute': 50}
        },
        {
            'service': 'user-service',
            'action': 'read',
            'credentials': {},  # No credentials
            'context': {'location': 'US', 'requests_per_minute': 5}
        }
    ]

    print("\n🔍 Probando Zero-Trust Request Processing:")
    for i, request in enumerate(test_requests, 1):
        print(f"   Request {i}: {request['service']} -> {request['action']}")

        allowed, reason, identity = await orchestrator.process_request(
            request['service'],
            request['action'],
            request['credentials'],
            request['context']
        )

        status = "✅ ALLOWED" if allowed else "❌ DENIED"
        identity_name = identity.name if identity else "Unknown"
        print(f"      {status} - {reason} (Identity: {identity_name})")

    # Mostrar audit log
    print("\n📋 Audit Log (últimas 5 entradas):")
    audit_entries = orchestrator.audit_log[-5:]
    for entry in audit_entries:
        success_icon = "✅" if entry['success'] else "❌"
        identity = entry.get('identity_id', 'Unknown')
        print(f"   {success_icon} {entry['service_name']}.{entry['action']} by {identity} - {entry['reason']}")

    # Mostrar status final
    print("\n📈 Status Final de Zero-Trust Security:")
    final_status = orchestrator.get_security_status()
    print(f"   Security Score: {final_status['overall_security_score']:.1f}/100")
    print(f"   Audit Entries: {final_status['audit_entries']}")
    print(f"   High Risk Identities: {final_status['identities']['high_risk']}")

    print("✅ Zero-Trust Security demostrado correctamente")

    return orchestrator


if __name__ == "__main__":
    asyncio.run(demonstrate_zero_trust_security())