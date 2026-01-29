"""
AILOOS Security Module

This module provides comprehensive security features for AILOOS distributed system.
"""

# Zero-Trust Security - FASE 5.3
from .zero_trust_security import (
    ZeroTrustOrchestrator, ServiceMeshManager, ContinuousAuthenticationManager,
    ServiceEndpoint, AuthorizationPolicy, MTLSCertificate, Identity,
    TrustLevel, IdentityType, AuthenticationMethod, ServiceMeshProvider,
    create_default_identities, demonstrate_zero_trust_security
)

# Advanced Threat Detection - FASE 5.3
from .advanced_threat_detection import (
    ThreatDetectionOrchestrator, AnomalyDetectionEngine, AutomatedResponseEngine,
    ThreatIndicator, BehavioralProfile, AIModel, ThreatSeverity,
    ThreatType, ResponseAction, demonstrate_advanced_threat_detection
)

# Existing security modules
from .gcp_secret_manager import (
    GCPSecretManager, SecretManagerConfig, get_secret_manager,
    migrate_all_secrets_to_gcp
)

from .secret_rotation import (
    SecretRotationManager, setup_secret_rotation, RotationPolicy,
    RotationTrigger, SecretRotationConfig
)

from .secure_node_id import (
    SecureNodeIDGenerator, generate_node_id, get_current_node_fingerprint,
    validate_node_id_format
)

from .sybil_protector import (
    SybilProtector, AntiSybilConfig, ProtectionLevel,
    demonstrate_anti_sybil_protection
)

__all__ = [
    # Zero-Trust Security
    'ZeroTrustOrchestrator',
    'ServiceMeshManager',
    'ContinuousAuthenticationManager',
    'ServiceEndpoint',
    'AuthorizationPolicy',
    'MTLSCertificate',
    'Identity',
    'TrustLevel',
    'IdentityType',
    'AuthenticationMethod',
    'ServiceMeshProvider',
    'create_default_identities',
    'demonstrate_zero_trust_security',
    # Advanced Threat Detection
    'ThreatDetectionOrchestrator',
    'AnomalyDetectionEngine',
    'AutomatedResponseEngine',
    'ThreatIndicator',
    'BehavioralProfile',
    'AIModel',
    'ThreatSeverity',
    'ThreatType',
    'ResponseAction',
    'demonstrate_advanced_threat_detection',
    # Existing modules
    'GCPSecretManager',
    'SecretManagerConfig',
    'get_secret_manager',
    'migrate_all_secrets_to_gcp',
    'SecretRotationManager',
    'setup_secret_rotation',
    'RotationPolicy',
    'RotationTrigger',
    'SecretRotationConfig',
    'SecureNodeIDGenerator',
    'generate_node_id',
    'get_current_node_fingerprint',
    'validate_node_id_format',
    'SybilProtector',
    'AntiSybilConfig',
    'ProtectionLevel',
    'demonstrate_anti_sybil_protection'
]

__version__ = "2.3.0"