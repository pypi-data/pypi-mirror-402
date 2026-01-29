#!/usr/bin/env python3
"""
Módulo Enterprise Security para AILOOS - FASE 8
===============================================

Sistema completo de seguridad enterprise con:

- SAML Authentication Provider
- OAuth2 Provider con scopes avanzados
- LDAP/Active Directory Integration
- Role-Based Access Control (RBAC) jerárquico
- Session Management con MFA
- Security Policy Engine dinámico

Este módulo proporciona capacidades de seguridad enterprise-grade
para integraciones corporativas y cumplimiento de estándares de seguridad.
"""

from .saml_auth_provider import SAMLAuthProvider
from .oauth2_provider import OAuth2Provider
from .ldap_integration import LDAPIntegration
from .rbac_manager import RBACManager
from .session_manager import SessionManager
from .security_policy_engine import SecurityPolicyEngine

__all__ = [
    'SAMLAuthProvider',
    'OAuth2Provider',
    'LDAPIntegration',
    'RBACManager',
    'SessionManager',
    'SecurityPolicyEngine'
]

__version__ = "1.0.0"
__author__ = "AILOOS Security Team"