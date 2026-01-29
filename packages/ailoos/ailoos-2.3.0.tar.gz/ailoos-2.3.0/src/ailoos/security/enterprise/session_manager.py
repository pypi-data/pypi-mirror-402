#!/usr/bin/env python3
"""
Session Manager con MFA Avanzada
================================

Implementa gestión avanzada de sesiones de usuario con soporte para
autenticación multifactor (MFA), políticas de sesión, monitoreo
de actividad, y revocación de sesiones.
"""

import logging
import secrets
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFAType(Enum):
    """Tipos de autenticación multifactor"""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"   # SMS OTP
    EMAIL = "email"  # Email OTP
    PUSH = "push"  # Push notification
    HARDWARE = "hardware"  # Hardware token
    BIOMETRIC = "biometric"  # Biometric authentication

class MFAAuthenticationStatus(Enum):
    """Estados de autenticación MFA"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class SessionStatus(Enum):
    """Estados de sesión"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class SessionRiskLevel(Enum):
    """Niveles de riesgo de sesión"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MFAAuthentication:
    """Autenticación MFA"""
    id: str
    user_id: str
    mfa_type: MFAType
    status: MFAAuthenticationStatus = MFAAuthenticationStatus.PENDING
    code: Optional[str] = None
    challenge: Optional[str] = None  # Para desafíos específicos
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))
    verified_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Verifica si la autenticación MFA ha expirado"""
        return datetime.now() > self.expires_at

    def is_verified(self) -> bool:
        """Verifica si la autenticación MFA está verificada"""
        return self.status == MFAAuthenticationStatus.VERIFIED

    def can_attempt(self) -> bool:
        """Verifica si se puede intentar verificar"""
        return self.attempts < self.max_attempts and not self.is_expired()

    def record_attempt(self, success: bool = False):
        """Registra un intento de verificación"""
        self.attempts += 1
        if success:
            self.status = MFAAuthenticationStatus.VERIFIED
            self.verified_at = datetime.now()
        elif self.attempts >= self.max_attempts:
            self.status = MFAAuthenticationStatus.FAILED

@dataclass
class UserSession:
    """Sesión de usuario"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    risk_level: SessionRiskLevel = SessionRiskLevel.LOW
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=8))
    mfa_verified: bool = False
    mfa_types_used: List[MFAType] = field(default_factory=list)
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    activity_log: List[Dict[str, Any]] = field(default_factory=list)

    def is_active(self) -> bool:
        """Verifica si la sesión está activa"""
        return (self.status == SessionStatus.ACTIVE and
                datetime.now() < self.expires_at and
                datetime.now() - self.last_activity < timedelta(hours=1))

    def is_expired(self) -> bool:
        """Verifica si la sesión ha expirado"""
        return datetime.now() > self.expires_at

    def update_activity(self, activity_type: str, details: Optional[Dict[str, Any]] = None):
        """Actualiza la actividad de la sesión"""
        self.last_activity = datetime.now()
        activity_entry = {
            'timestamp': self.last_activity.isoformat(),
            'type': activity_type,
            'details': details or {}
        }
        self.activity_log.append(activity_entry)

        # Mantener solo las últimas 100 actividades
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]

    def extend_session(self, duration: timedelta = timedelta(hours=1)):
        """Extiende la duración de la sesión"""
        self.expires_at = max(self.expires_at, datetime.now() + duration)
        self.update_activity('session_extended', {'new_expires_at': self.expires_at.isoformat()})

    def calculate_risk_level(self) -> SessionRiskLevel:
        """Calcula el nivel de riesgo de la sesión"""
        risk_score = 0

        # Factores de riesgo
        if not self.mfa_verified:
            risk_score += 30

        time_since_creation = datetime.now() - self.created_at
        if time_since_creation > timedelta(days=7):
            risk_score += 20

        if len(self.activity_log) > 50:  # Alta actividad
            risk_score += 10

        # Verificar patrones sospechosos
        recent_activities = [a for a in self.activity_log
                           if datetime.now() - datetime.fromisoformat(a['timestamp']) < timedelta(hours=1)]
        if len(recent_activities) > 20:
            risk_score += 25

        # Determinar nivel
        if risk_score >= 60:
            return SessionRiskLevel.CRITICAL
        elif risk_score >= 40:
            return SessionRiskLevel.HIGH
        elif risk_score >= 20:
            return SessionRiskLevel.MEDIUM
        else:
            return SessionRiskLevel.LOW

@dataclass
class SessionPolicy:
    """Política de sesión"""
    name: str
    description: Optional[str] = None
    max_sessions_per_user: int = 5
    session_timeout: timedelta = timedelta(hours=8)
    idle_timeout: timedelta = timedelta(hours=1)
    require_mfa: bool = True
    allowed_mfa_types: List[MFAType] = field(default_factory=lambda: [MFAType.TOTP, MFAType.SMS])
    risk_thresholds: Dict[SessionRiskLevel, List[str]] = field(default_factory=dict)
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    device_restrictions: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def check_ip_allowed(self, ip_address: str) -> bool:
        """Verifica si la IP está permitida"""
        if self.ip_blacklist and ip_address in self.ip_blacklist:
            return False
        if self.ip_whitelist and ip_address not in self.ip_whitelist:
            return False
        return True

class SessionManager:
    """
    Gestor avanzado de sesiones con MFA
    """

    def __init__(self):
        # Sesiones activas
        self.active_sessions: Dict[str, UserSession] = {}

        # Autenticaciones MFA pendientes
        self.pending_mfa: Dict[str, MFAAuthentication] = {}

        # Políticas de sesión
        self.session_policies: Dict[str, SessionPolicy] = {}

        # Sesiones por usuario
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)

        # Configuración
        self.session_cleanup_interval = timedelta(minutes=30)
        self.last_cleanup = datetime.now()

        # Política por defecto
        self._create_default_policy()

        logger.info("🔐 Session Manager initialized")

    def _create_default_policy(self):
        """Crea política de sesión por defecto"""
        default_policy = SessionPolicy(
            name="default",
            description="Default session policy",
            max_sessions_per_user=5,
            session_timeout=timedelta(hours=8),
            idle_timeout=timedelta(hours=1),
            require_mfa=True,
            allowed_mfa_types=[MFAType.TOTP, MFAType.SMS, MFAType.EMAIL],
            risk_thresholds={
                SessionRiskLevel.HIGH: ["require_additional_mfa", "reduce_session_timeout"],
                SessionRiskLevel.CRITICAL: ["force_logout", "notify_security"]
            }
        )
        self.session_policies["default"] = default_policy

    def create_session(self, user_id: str, ip_address: str, user_agent: Optional[str] = None,
                      device_fingerprint: Optional[str] = None,
                      policy_name: str = "default") -> UserSession:
        """
        Crea una nueva sesión para un usuario

        Args:
            user_id: ID del usuario
            ip_address: Dirección IP del cliente
            user_agent: User agent del navegador/cliente
            device_fingerprint: Huella digital del dispositivo
            policy_name: Nombre de la política a aplicar

        Returns:
            Sesión creada

        Raises:
            ValueError: Si se excede el límite de sesiones
        """
        policy = self.session_policies.get(policy_name, self.session_policies["default"])

        # Verificar límite de sesiones por usuario
        user_sessions = self.user_sessions[user_id]
        if len(user_sessions) >= policy.max_sessions_per_user:
            # Cerrar la sesión más antigua
            oldest_session_id = min(user_sessions,
                                  key=lambda s: self.active_sessions[s].created_at)
            self.revoke_session(oldest_session_id)

        # Verificar IP
        if not policy.check_ip_allowed(ip_address):
            raise ValueError("IP address not allowed")

        # Crear sesión
        session_id = secrets.token_urlsafe(32)
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.now() + policy.session_timeout
        )

        self.active_sessions[session_id] = session
        self.user_sessions[user_id].add(session_id)

        session.update_activity('session_created', {
            'policy': policy_name,
            'ip_address': ip_address,
            'user_agent': user_agent
        })

        logger.info(f"✅ Session created for user {user_id}: {session_id}")
        return session

    def validate_session(self, session_id: str) -> Optional[UserSession]:
        """
        Valida una sesión existente

        Args:
            session_id: ID de la sesión

        Returns:
            Sesión si es válida, None si no
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        # Verificar estado
        if session.status != SessionStatus.ACTIVE:
            return None

        # Verificar expiración
        if session.is_expired():
            session.status = SessionStatus.EXPIRED
            self._cleanup_session(session)
            return None

        # Verificar inactividad
        if datetime.now() - session.last_activity > timedelta(hours=1):
            session.status = SessionStatus.INACTIVE
            self._cleanup_session(session)
            return None

        # Actualizar nivel de riesgo
        session.risk_level = session.calculate_risk_level()

        # Aplicar medidas de seguridad basadas en riesgo
        self._apply_risk_measures(session)

        return session

    def initiate_mfa(self, user_id: str, mfa_type: MFAType,
                    challenge_data: Optional[Dict[str, Any]] = None) -> MFAAuthentication:
        """
        Inicia una autenticación MFA

        Args:
            user_id: ID del usuario
            mfa_type: Tipo de MFA
            challenge_data: Datos adicionales para el desafío

        Returns:
            Autenticación MFA creada
        """
        mfa_id = str(uuid.uuid4())

        # Generar código según tipo
        code = None
        if mfa_type in [MFAType.TOTP, MFAType.SMS, MFAType.EMAIL]:
            code = self._generate_mfa_code()
        elif mfa_type == MFAType.PUSH:
            # En implementación real, enviar notificación push
            code = "PUSH_CHALLENGE"
        elif mfa_type == MFAType.HARDWARE:
            # En implementación real, generar desafío U2F/WebAuthn
            code = "HARDWARE_CHALLENGE"

        mfa_auth = MFAAuthentication(
            id=mfa_id,
            user_id=user_id,
            mfa_type=mfa_type,
            code=code,
            challenge=json.dumps(challenge_data) if challenge_data else None
        )

        self.pending_mfa[mfa_id] = mfa_auth

        # Enviar código según tipo (simulado)
        self._send_mfa_code(mfa_auth)

        logger.info(f"🔐 MFA initiated for user {user_id}: {mfa_type.value}")
        return mfa_auth

    def verify_mfa(self, mfa_id: str, code: str) -> bool:
        """
        Verifica un código MFA

        Args:
            mfa_id: ID de la autenticación MFA
            code: Código proporcionado

        Returns:
            True si la verificación es exitosa
        """
        mfa_auth = self.pending_mfa.get(mfa_id)
        if not mfa_auth or not mfa_auth.can_attempt():
            return False

        # Verificar código
        success = False
        if mfa_auth.mfa_type in [MFAType.TOTP, MFAType.SMS, MFAType.EMAIL]:
            success = hmac.compare_digest(mfa_auth.code or "", code)
        elif mfa_auth.mfa_type == MFAType.PUSH:
            # En implementación real, verificar respuesta push
            success = code == "APPROVED"
        elif mfa_auth.mfa_type == MFAType.HARDWARE:
            # En implementación real, verificar firma WebAuthn
            success = code == "HARDWARE_SIGNATURE"

        mfa_auth.record_attempt(success)

        if success:
            del self.pending_mfa[mfa_id]
            logger.info(f"✅ MFA verified for user {mfa_auth.user_id}")
        else:
            logger.warning(f"❌ MFA verification failed for user {mfa_auth.user_id}")

        return success

    def complete_session_with_mfa(self, session_id: str, mfa_auth: MFAAuthentication) -> bool:
        """
        Completa una sesión con verificación MFA

        Args:
            session_id: ID de la sesión
            mfa_auth: Autenticación MFA verificada

        Returns:
            True si se completó correctamente
        """
        session = self.active_sessions.get(session_id)
        if not session or session.user_id != mfa_auth.user_id:
            return False

        session.mfa_verified = True
        session.mfa_types_used.append(mfa_auth.mfa_type)
        session.update_activity('mfa_completed', {
            'mfa_type': mfa_auth.mfa_type.value,
            'verified_at': mfa_auth.verified_at.isoformat()
        })

        logger.info(f"🔐 Session {session_id} completed with MFA")
        return True

    def revoke_session(self, session_id: str) -> bool:
        """
        Revoca una sesión

        Args:
            session_id: ID de la sesión

        Returns:
            True si se revocó correctamente
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = SessionStatus.REVOKED
        session.update_activity('session_revoked')

        self._cleanup_session(session)

        logger.info(f"🚫 Session revoked: {session_id}")
        return True

    def revoke_user_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """
        Revoca todas las sesiones de un usuario

        Args:
            user_id: ID del usuario
            except_session: ID de sesión a excluir

        Returns:
            Número de sesiones revocadas
        """
        session_ids = self.user_sessions.get(user_id, set()).copy()
        if except_session:
            session_ids.discard(except_session)

        revoked_count = 0
        for session_id in session_ids:
            if self.revoke_session(session_id):
                revoked_count += 1

        logger.info(f"🚫 Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count

    def suspend_session(self, session_id: str, reason: Optional[str] = None) -> bool:
        """
        Suspende una sesión temporalmente

        Args:
            session_id: ID de la sesión
            reason: Razón de la suspensión

        Returns:
            True si se suspendió correctamente
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = SessionStatus.SUSPENDED
        session.update_activity('session_suspended', {'reason': reason})

        logger.info(f"⏸️ Session suspended: {session_id}")
        return True

    def resume_session(self, session_id: str) -> bool:
        """
        Reanuda una sesión suspendida

        Args:
            session_id: ID de la sesión

        Returns:
            True si se reanudó correctamente
        """
        session = self.active_sessions.get(session_id)
        if not session or session.status != SessionStatus.SUSPENDED:
            return False

        session.status = SessionStatus.ACTIVE
        session.update_activity('session_resumed')

        logger.info(f"▶️ Session resumed: {session_id}")
        return True

    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """
        Obtiene todas las sesiones activas de un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Lista de sesiones activas
        """
        session_ids = self.user_sessions.get(user_id, set())
        sessions = []
        for session_id in session_ids:
            session = self.active_sessions.get(session_id)
            if session and session.is_active():
                sessions.append(session)
        return sessions

    def get_session_activity_log(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene el log de actividad de una sesión

        Args:
            session_id: ID de la sesión
            limit: Número máximo de entradas

        Returns:
            Lista de actividades
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return []

        return session.activity_log[-limit:] if limit > 0 else session.activity_log

    def _generate_mfa_code(self) -> str:
        """Genera un código MFA de 6 dígitos"""
        return ''.join(secrets.choice('0123456789') for _ in range(6))

    def _send_mfa_code(self, mfa_auth: MFAAuthentication):
        """Envía el código MFA (simulado)"""
        # En implementación real, enviar por SMS, email, etc.
        if mfa_auth.mfa_type == MFAType.SMS:
            logger.info(f"📱 SMS sent to user {mfa_auth.user_id}: {mfa_auth.code}")
        elif mfa_auth.mfa_type == MFAType.EMAIL:
            logger.info(f"📧 Email sent to user {mfa_auth.user_id}: {mfa_auth.code}")
        elif mfa_auth.mfa_type == MFAType.PUSH:
            logger.info(f"📲 Push notification sent to user {mfa_auth.user_id}")

    def _apply_risk_measures(self, session: UserSession):
        """Aplica medidas de seguridad basadas en el nivel de riesgo"""
        policy = self.session_policies.get("default")

        if session.risk_level == SessionRiskLevel.HIGH:
            # Reducir tiempo de sesión
            session.expires_at = min(session.expires_at, datetime.now() + timedelta(hours=2))
            session.update_activity('risk_measure_applied', {'measure': 'reduced_timeout'})

        elif session.risk_level == SessionRiskLevel.CRITICAL:
            # Forzar logout
            session.status = SessionStatus.SUSPENDED
            session.update_activity('risk_measure_applied', {'measure': 'forced_logout'})
            logger.warning(f"🚨 High-risk session suspended: {session.session_id}")

    def _cleanup_session(self, session: UserSession):
        """Limpia una sesión terminada"""
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]

        if session.user_id in self.user_sessions:
            self.user_sessions[session.user_id].discard(session.session_id)
            if not self.user_sessions[session.user_id]:
                del self.user_sessions[session.user_id]

    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        current_time = datetime.now()
        if current_time - self.last_cleanup < self.session_cleanup_interval:
            return

        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.is_expired() or session.status in [SessionStatus.EXPIRED, SessionStatus.REVOKED]:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            session = self.active_sessions[session_id]
            self._cleanup_session(session)

        # Limpiar MFA expiradas
        expired_mfa = []
        for mfa_id, mfa_auth in self.pending_mfa.items():
            if mfa_auth.is_expired():
                expired_mfa.append(mfa_id)

        for mfa_id in expired_mfa:
            del self.pending_mfa[mfa_id]

        self.last_cleanup = current_time

        if expired_sessions or expired_mfa:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} sessions and {len(expired_mfa)} MFA auths")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de sesiones"""
        total_sessions = len(self.active_sessions)
        active_sessions = len([s for s in self.active_sessions.values() if s.is_active()])
        suspended_sessions = len([s for s in self.active_sessions.values() if s.status == SessionStatus.SUSPENDED])

        risk_distribution = {}
        for session in self.active_sessions.values():
            risk_distribution[session.risk_level.value] = risk_distribution.get(session.risk_level.value, 0) + 1

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'suspended_sessions': suspended_sessions,
            'pending_mfa': len(self.pending_mfa),
            'users_with_sessions': len(self.user_sessions),
            'risk_distribution': risk_distribution
        }


# Instancia global del gestor de sesiones
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Obtiene la instancia global del gestor de sesiones"""
    return session_manager