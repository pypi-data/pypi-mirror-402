"""
Modelos SQLAlchemy para configuraciones de usuario de AILOOS
===========================================================

Este módulo define los modelos SQLAlchemy para almacenar todas las configuraciones
del usuario en la base de datos PostgreSQL del coordinador.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Modelo de usuario para configuraciones."""
    __tablename__ = "settings_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones con configuraciones
    general_settings = relationship("GeneralSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    personalization_settings = relationship("PersonalizationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memory_settings = relationship("MemorySettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    apps_connectors_settings = relationship("AppsConnectorsSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    data_controls_settings = relationship("DataControlsSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    security_settings = relationship("SecuritySettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parental_controls_settings = relationship("ParentalControlsSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    account_settings = relationship("AccountSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class GeneralSettings(Base):
    """Configuraciones generales de la aplicación."""
    __tablename__ = "general_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Apariencia
    appearance = Column(String(10), nullable=False, default="system")
    accent_color = Column(String(10), nullable=False, default="blue")
    font_size = Column(String(10), nullable=False, default="medium")

    # Comportamiento
    send_with_enter = Column(Boolean, nullable=False, default=True)
    ui_language = Column(String(2), nullable=False, default="es")
    spoken_language = Column(String(2), nullable=False, default="es")
    voice = Column(String(10), nullable=False, default="ember")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="general_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("appearance IN ('system', 'light', 'dark')", name="check_general_appearance"),
        CheckConstraint("accent_color IN ('blue', 'green', 'purple', 'red')", name="check_general_accent_color"),
        CheckConstraint("font_size IN ('small', 'medium', 'large')", name="check_general_font_size"),
        CheckConstraint("ui_language IN ('es', 'en', 'fr', 'de')", name="check_general_ui_language"),
        CheckConstraint("spoken_language IN ('es', 'en', 'fr', 'de')", name="check_general_spoken_language"),
        CheckConstraint("voice IN ('ember', 'alloy', 'echo')", name="check_general_voice"),
        Index('idx_general_settings_user_id', 'user_id'),
    )


class NotificationSettings(Base):
    """Configuraciones de notificaciones."""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Control general
    mute_all = Column(Boolean, nullable=False, default=False)

    # Notificaciones específicas
    responses_app = Column(Boolean, nullable=False, default=True)
    responses_email = Column(Boolean, nullable=False, default=True)
    tasks_app = Column(Boolean, nullable=False, default=True)
    tasks_email = Column(Boolean, nullable=False, default=False)
    projects_app = Column(Boolean, nullable=False, default=True)
    projects_email = Column(Boolean, nullable=False, default=True)
    recommendations_app = Column(Boolean, nullable=False, default=False)
    recommendations_email = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="notification_settings")

    # Índices
    __table_args__ = (
        Index('idx_notification_settings_user_id', 'user_id'),
    )


class PersonalizationSettings(Base):
    """Configuraciones de personalización."""
    __tablename__ = "personalization_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Controles principales
    enable_personalization = Column(Boolean, nullable=False, default=True)
    custom_instructions = Column(Boolean, nullable=False, default=False)

    # Estilo y tono
    base_style_tone = Column(String(15), nullable=False, default="witty")

    # Información personal
    nickname = Column(String(50), default="")
    occupation = Column(String(100), default="")
    more_about_you = Column(Text, default="")

    # Memoria y contexto
    reference_chat_history = Column(Boolean, nullable=False, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="personalization_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("base_style_tone IN ('talkative', 'witty', 'professional', 'casual')", name="check_personalization_tone"),
        Index('idx_personalization_settings_user_id', 'user_id'),
    )


class MemorySettings(Base):
    """Configuraciones de memoria."""
    __tablename__ = "memory_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Gestión de memoria
    memory_used = Column(Integer, nullable=False, default=0)
    max_memory_items = Column(Integer, nullable=False, default=256)

    # Controles
    reference_memories = Column(Boolean, nullable=False, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="memory_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("memory_used >= 0", name="check_memory_used_non_negative"),
        CheckConstraint("max_memory_items > 0", name="check_max_memory_items_positive"),
        CheckConstraint("memory_used <= max_memory_items", name="check_memory_used_within_limit"),
        Index('idx_memory_settings_user_id', 'user_id'),
    )


class AppsConnectorsSettings(Base):
    """Configuraciones de aplicaciones y conectores."""
    __tablename__ = "apps_connectors_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Almacenamiento en la nube
    google_drive = Column(Boolean, nullable=False, default=False)
    dropbox = Column(Boolean, nullable=False, default=False)

    # Comunicación
    slack = Column(Boolean, nullable=False, default=False)
    discord = Column(Boolean, nullable=False, default=False)

    # Integraciones Discord detalladas
    discord_bot_token = Column(String(255), default="")
    discord_server_id = Column(String(50), default="")
    discord_channel_id = Column(String(50), default="")
    discord_webhook_url = Column(String(500), default="")

    # Webhooks
    webhook_url = Column(String(500), default="")
    webhook_headers = Column(Text, default="")  # JSON string con headers
    webhook_method = Column(String(10), nullable=False, default="POST")
    webhook_enabled = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="apps_connectors_settings")

    # Constraints e índices
    __table_args__ = (
        CheckConstraint("webhook_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')", name="check_webhook_method"),
        Index('idx_apps_connectors_settings_user_id', 'user_id'),
    )


class DataControlsSettings(Base):
    """Configuraciones de controles de datos."""
    __tablename__ = "data_controls_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Recopilación de datos
    data_collection = Column(Boolean, nullable=False, default=True)
    analytics = Column(Boolean, nullable=False, default=True)

    # Retención
    data_retention = Column(String(15), nullable=False, default="1year")

    # Exportación
    export_data = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="data_controls_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("data_retention IN ('3months', '6months', '1year', '2years', 'indefinite')", name="check_data_retention"),
        Index('idx_data_controls_settings_user_id', 'user_id'),
    )


class SecuritySettings(Base):
    """Configuraciones de seguridad."""
    __tablename__ = "security_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Autenticación
    two_factor = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String(32), nullable=True)  # Base32 secret for TOTP
    two_factor_enabled = Column(Boolean, nullable=False, default=False)  # Whether 2FA is fully enabled
    two_factor_algorithm = Column(String(10), nullable=False, default="SHA256")
    two_factor_digits = Column(Integer, nullable=False, default=6)
    two_factor_interval = Column(Integer, nullable=False, default=30)

    # Sesión
    session_timeout = Column(String(10), nullable=False, default="30min")

    # Alertas
    login_alerts = Column(Boolean, nullable=False, default=True)

    # Cambio de contraseña (estado temporal)
    password_change_pending = Column(Boolean, nullable=False, default=False)
    password_last_changed = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="security_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("two_factor_algorithm IN ('SHA1', 'SHA256', 'SHA512')", name="check_two_factor_algorithm"),
        CheckConstraint("two_factor_digits IN (6, 8)", name="check_two_factor_digits"),
        CheckConstraint("two_factor_interval BETWEEN 15 AND 60", name="check_two_factor_interval"),
        CheckConstraint("session_timeout IN ('15min', '30min', '1hour', '4hours', 'never')", name="check_session_timeout"),
        Index('idx_security_settings_user_id', 'user_id'),
    )


class ParentalControlsSettings(Base):
    """Configuraciones de controles parentales."""
    __tablename__ = "parental_controls_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Control principal
    parental_control = Column(Boolean, nullable=False, default=False)

    # Filtros
    content_filter = Column(String(10), nullable=False, default="moderate")

    # Límites de tiempo
    time_limits = Column(Boolean, nullable=False, default=False)
    max_time_per_day = Column(String(10), nullable=False, default="2hours")

    # Código parental (hash, no se almacena en texto plano)
    parental_pin_hash = Column(String(255))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="parental_controls_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("content_filter IN ('strict', 'moderate', 'lenient')", name="check_content_filter"),
        CheckConstraint("max_time_per_day IN ('1hour', '2hours', '4hours', '8hours')", name="check_max_time_per_day"),
        Index('idx_parental_controls_settings_user_id', 'user_id'),
    )


class AccountSettings(Base):
    """Configuraciones de cuenta."""
    __tablename__ = "account_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, unique=True)

    # Información personal
    name = Column(String(100), default="")
    email = Column(String(255), default="")
    phone = Column(String(20), default="")
    bio = Column(Text, default="")

    # Estadísticas (solo lectura)
    sessions_completed = Column(Integer, nullable=False, default=0)
    tokens_used = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(10), nullable=False, default="1.0.0")

    # Relaciones
    user = relationship("User", back_populates="account_settings")

    # Constraints
    __table_args__ = (
        CheckConstraint("sessions_completed >= 0", name="check_sessions_completed_non_negative"),
        CheckConstraint("tokens_used >= 0", name="check_tokens_used_non_negative"),
        Index('idx_account_settings_user_id', 'user_id'),
    )


# Modelo para suscripciones de notificaciones push
class PushSubscription(Base):
    """Modelo para suscripciones de notificaciones push web."""
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("settings_users.id"), nullable=False, index=True)

    # Datos de la suscripción Push API
    endpoint = Column(String(500), nullable=False, unique=True)  # URL del endpoint push
    p256dh_key = Column(String(100), nullable=False)  # Clave pública P-256DH en base64
    auth_key = Column(String(50), nullable=False)    # Clave de autenticación en base64

    # Metadatos
    user_agent = Column(String(500), nullable=True)  # User-Agent del navegador
    browser_info = Column(String(200), nullable=True)  # Información del navegador
    ip_address = Column(String(45), nullable=True)    # IPv4/IPv6 del cliente

    # Estado y timestamps
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    user = relationship("User", backref="push_subscriptions")

    # Constraints
    __table_args__ = (
        Index('idx_push_subscriptions_user_id', 'user_id'),
        Index('idx_push_subscriptions_endpoint', 'endpoint'),
        Index('idx_push_subscriptions_active', 'is_active'),
        Index('idx_push_subscriptions_created_at', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la suscripción a diccionario."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'p256dh_key': self.p256dh_key,
            'auth_key': self.auth_key,
            'user_agent': self.user_agent,
            'browser_info': self.browser_info,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PushSubscription':
        """Crea una suscripción desde un diccionario."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            endpoint=data.get('endpoint'),
            p256dh_key=data.get('p256dh_key'),
            auth_key=data.get('auth_key'),
            user_agent=data.get('user_agent'),
            browser_info=data.get('browser_info'),
            ip_address=data.get('ip_address'),
            is_active=data.get('is_active', True),
            last_used_at=datetime.fromisoformat(data['last_used_at']) if data.get('last_used_at') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


# Índices adicionales para optimización
Index('idx_settings_users_email', User.email)
Index('idx_settings_users_username', User.username)
Index('idx_push_subscriptions_user_active', PushSubscription.user_id, PushSubscription.is_active)