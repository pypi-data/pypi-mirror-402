"""
Modelos de datos para configuraciones de AILOOS
==============================================

Este módulo define los modelos de datos para todas las categorías de configuraciones
del sistema AILOOS, proporcionando estructuras tipadas y validadas para cada sección.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import re


# Tipos comunes
@dataclass
class BaseSettings:
    """Clase base para todas las configuraciones con campos comunes."""

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def update_timestamp(self):
        """Actualiza el timestamp de modificación."""
        self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida la configuración. Retorna lista de errores."""
        return []


@dataclass
class GeneralSettings(BaseSettings):
    """Configuraciones generales de la aplicación."""

    # Apariencia
    appearance: str = "system"  # "system", "light", "dark"
    accent_color: str = "blue"  # "blue", "green", "purple", "red"
    font_size: str = "medium"  # "small", "medium", "large"

    # Comportamiento
    send_with_enter: bool = True
    ui_language: str = "es"  # "es", "en", "fr", "de"
    spoken_language: str = "es"  # "es", "en", "fr", "de"
    voice: str = "ember"  # "ember", "alloy", "echo"

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar apariencia
        if self.appearance not in ["system", "light", "dark"]:
            errors.append("appearance debe ser 'system', 'light' o 'dark'")

        # Validar color de acento
        if self.accent_color not in ["blue", "green", "purple", "red"]:
            errors.append("accent_color debe ser 'blue', 'green', 'purple' o 'red'")

        # Validar tamaño de fuente
        if self.font_size not in ["small", "medium", "large"]:
            errors.append("font_size debe ser 'small', 'medium' o 'large'")

        # Validar idiomas
        valid_languages = ["es", "en", "fr", "de"]
        if self.ui_language not in valid_languages:
            errors.append(f"ui_language debe ser uno de: {valid_languages}")
        if self.spoken_language not in valid_languages:
            errors.append(f"spoken_language debe ser uno de: {valid_languages}")

        # Validar voz
        if self.voice not in ["ember", "alloy", "echo"]:
            errors.append("voice debe ser 'ember', 'alloy' o 'echo'")

        return errors


@dataclass
class NotificationSettings(BaseSettings):
    """Configuraciones de notificaciones."""

    # Control general
    mute_all: bool = False

    # Notificaciones específicas
    responses_app: bool = True
    responses_email: bool = True
    tasks_app: bool = True
    tasks_email: bool = False
    projects_app: bool = True
    projects_email: bool = True
    recommendations_app: bool = False
    recommendations_email: bool = False

    def validate(self) -> List[str]:
        errors = super().validate()
        # Todas las validaciones pasan ya que son booleanos
        return errors


@dataclass
class PersonalizationSettings(BaseSettings):
    """Configuraciones de personalización."""

    # Controles principales
    enable_personalization: bool = True
    custom_instructions: bool = False

    # Estilo y tono
    base_style_tone: str = "witty"  # "talkative", "witty", "professional", "casual"

    # Información personal
    nickname: str = ""
    occupation: str = ""
    more_about_you: str = ""

    # Memoria y contexto
    reference_chat_history: bool = True

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar estilo y tono
        valid_tones = ["talkative", "witty", "professional", "casual"]
        if self.base_style_tone not in valid_tones:
            errors.append(f"base_style_tone debe ser uno de: {valid_tones}")

        # Validar longitud de textos
        if len(self.nickname) > 50:
            errors.append("nickname no puede exceder 50 caracteres")
        if len(self.occupation) > 100:
            errors.append("occupation no puede exceder 100 caracteres")
        if len(self.more_about_you) > 500:
            errors.append("more_about_you no puede exceder 500 caracteres")

        return errors


@dataclass
class MemorySettings(BaseSettings):
    """Configuraciones de memoria."""

    # Gestión de memoria
    memory_used: int = 0
    max_memory_items: int = 256

    # Controles
    reference_memories: bool = True

    def validate(self) -> List[str]:
        errors = super().validate()

        if self.memory_used < 0:
            errors.append("memory_used no puede ser negativo")
        if self.memory_used > self.max_memory_items:
            errors.append(f"memory_used no puede exceder max_memory_items ({self.max_memory_items})")
        if self.max_memory_items <= 0:
            errors.append("max_memory_items debe ser positivo")

        return errors


@dataclass
class AppsConnectorsSettings(BaseSettings):
    """Configuraciones de aplicaciones y conectores."""

    # Almacenamiento en la nube
    google_drive: bool = False
    dropbox: bool = False

    # Comunicación
    slack: bool = False
    discord: bool = False

    # Webhooks
    webhook_url: str = ""

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar URL del webhook si está presente
        if self.webhook_url and not self._is_valid_url(self.webhook_url):
            errors.append("webhook_url debe ser una URL válida")

        return errors

    def _is_valid_url(self, url: str) -> bool:
        """Valida si una cadena es una URL válida."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None


@dataclass
class DataControlsSettings(BaseSettings):
    """Configuraciones de controles de datos."""

    # Recopilación de datos
    data_collection: bool = True
    analytics: bool = True

    # Retención
    data_retention: str = "1year"  # "3months", "6months", "1year", "2years", "indefinite"

    # Exportación
    export_data: bool = False

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar retención de datos
        valid_retentions = ["3months", "6months", "1year", "2years", "indefinite"]
        if self.data_retention not in valid_retentions:
            errors.append(f"data_retention debe ser uno de: {valid_retentions}")

        return errors


@dataclass
class SecuritySettings(BaseSettings):
    """Configuraciones de seguridad."""

    # Autenticación
    two_factor: bool = False
    two_factor_secret: Optional[str] = None  # Base32 secret for TOTP
    two_factor_enabled: bool = False  # Whether 2FA is fully enabled
    two_factor_algorithm: str = "SHA256"  # "SHA1", "SHA256", "SHA512"
    two_factor_digits: int = 6  # 6 or 8
    two_factor_interval: int = 30  # seconds

    # Sesión
    session_timeout: str = "30min"  # "15min", "30min", "1hour", "4hours", "never"

    # Alertas
    login_alerts: bool = True

    # Cambio de contraseña (estado temporal)
    password_change_pending: bool = False
    password_last_changed: Optional[datetime] = None

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar timeout de sesión
        valid_timeouts = ["15min", "30min", "1hour", "4hours", "never"]
        if self.session_timeout not in valid_timeouts:
            errors.append(f"session_timeout debe ser uno de: {valid_timeouts}")

        # Validar algoritmo 2FA
        valid_algorithms = ["SHA1", "SHA256", "SHA512"]
        if self.two_factor_algorithm not in valid_algorithms:
            errors.append(f"two_factor_algorithm debe ser uno de: {valid_algorithms}")

        # Validar dígitos 2FA
        if self.two_factor_digits not in [6, 8]:
            errors.append("two_factor_digits debe ser 6 u 8")

        # Validar intervalo 2FA
        if not (15 <= self.two_factor_interval <= 60):
            errors.append("two_factor_interval debe estar entre 15 y 60 segundos")

        return errors


@dataclass
class ParentalControlsSettings(BaseSettings):
    """Configuraciones de controles parentales."""

    # Control principal
    parental_control: bool = False

    # Filtros
    content_filter: str = "moderate"  # "strict", "moderate", "lenient"

    # Límites de tiempo
    time_limits: bool = False
    max_time_per_day: str = "2hours"  # "1hour", "2hours", "4hours", "8hours"

    # Código parental (hash, no se almacena en texto plano)
    parental_pin_hash: Optional[str] = None

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar filtro de contenido
        valid_filters = ["strict", "moderate", "lenient"]
        if self.content_filter not in valid_filters:
            errors.append(f"content_filter debe ser uno de: {valid_filters}")

        # Validar tiempo máximo por día
        valid_times = ["1hour", "2hours", "4hours", "8hours"]
        if self.max_time_per_day not in valid_times:
            errors.append(f"max_time_per_day debe ser uno de: {valid_times}")

        return errors


@dataclass
class AccountSettings(BaseSettings):
    """Configuraciones de cuenta."""

    # Información personal
    name: str = ""
    email: str = ""
    phone: str = ""
    bio: str = ""

    # Estadísticas (solo lectura)
    sessions_completed: int = 0
    tokens_used: int = 0

    def validate(self) -> List[str]:
        errors = super().validate()

        # Validar email
        if self.email and not self._is_valid_email(self.email):
            errors.append("email debe ser una dirección de email válida")

        # Validar teléfono (formato español básico)
        if self.phone and not self._is_valid_phone(self.phone):
            errors.append("phone debe tener un formato válido (ej: +34 600 000 000)")

        # Validar longitudes
        if len(self.name) > 100:
            errors.append("name no puede exceder 100 caracteres")
        if len(self.bio) > 500:
            errors.append("bio no puede exceder 500 caracteres")

        # Validar estadísticas
        if self.sessions_completed < 0:
            errors.append("sessions_completed no puede ser negativo")
        if self.tokens_used < 0:
            errors.append("tokens_used no puede ser negativo")

        return errors

    def _is_valid_email(self, email: str) -> bool:
        """Valida si una cadena es un email válido."""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return email_pattern.match(email) is not None

    def _is_valid_phone(self, phone: str) -> bool:
        """Valida si una cadena es un número de teléfono válido (formato español)."""
        # Permite formatos como: +34 600 000 000, 600 000 000, +34600000000
        phone_pattern = re.compile(
            r'^(\+34\s?)?[6-9]\d{2}(\s?\d{3}){2}$'
        )
        return phone_pattern.match(phone.replace(' ', '')) is not None


@dataclass
class SettingsContainer(BaseSettings):
    """Contenedor principal que agrupa todas las configuraciones."""

    # Categorías de configuración
    general: GeneralSettings = field(default_factory=GeneralSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    personalization: PersonalizationSettings = field(default_factory=PersonalizationSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)
    apps_connectors: AppsConnectorsSettings = field(default_factory=AppsConnectorsSettings)
    data_controls: DataControlsSettings = field(default_factory=DataControlsSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    parental_controls: ParentalControlsSettings = field(default_factory=ParentalControlsSettings)
    account: AccountSettings = field(default_factory=AccountSettings)

    def validate(self) -> List[str]:
        """Valida todas las configuraciones."""
        errors = super().validate()

        # Validar cada subcategoría
        errors.extend(self.general.validate())
        errors.extend(self.notifications.validate())
        errors.extend(self.personalization.validate())
        errors.extend(self.memory.validate())
        errors.extend(self.apps_connectors.validate())
        errors.extend(self.data_controls.validate())
        errors.extend(self.security.validate())
        errors.extend(self.parental_controls.validate())
        errors.extend(self.account.validate())

        return errors

    def get_category(self, category: str) -> Optional[BaseSettings]:
        """Obtiene una categoría específica de configuraciones."""
        category_map = {
            'general': self.general,
            'notifications': self.notifications,
            'personalization': self.personalization,
            'memory': self.memory,
            'apps_connectors': self.apps_connectors,
            'data_controls': self.data_controls,
            'security': self.security,
            'parental_controls': self.parental_controls,
            'account': self.account,
        }
        return category_map.get(category)

    def update_category(self, category: str, settings: Dict[str, Any]):
        """Actualiza una categoría específica."""
        target = self.get_category(category)
        if target:
            for key, value in settings.items():
                if hasattr(target, key):
                    setattr(target, key, value)
            target.update_timestamp()
            self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte todo el contenedor a diccionario."""
        result = super().to_dict()
        # Remover campos duplicados que ya están en subcategorías
        result.pop('general', None)
        result.pop('notifications', None)
        result.pop('personalization', None)
        result.pop('memory', None)
        result.pop('apps_connectors', None)
        result.pop('data_controls', None)
        result.pop('security', None)
        result.pop('parental_controls', None)
        result.pop('account', None)

        # Agregar subcategorías
        result.update({
            'general': self.general.to_dict(),
            'notifications': self.notifications.to_dict(),
            'personalization': self.personalization.to_dict(),
            'memory': self.memory.to_dict(),
            'apps_connectors': self.apps_connectors.to_dict(),
            'data_controls': self.data_controls.to_dict(),
            'security': self.security.to_dict(),
            'parental_controls': self.parental_controls.to_dict(),
            'account': self.account.to_dict(),
        })

        return result


# Funciones de utilidad
def create_default_settings() -> SettingsContainer:
    """Crea una instancia de configuraciones con valores por defecto."""
    return SettingsContainer()


def load_settings_from_dict(data: Dict[str, Any]) -> SettingsContainer:
    """Carga configuraciones desde un diccionario."""
    container = SettingsContainer()

    # Cargar cada categoría
    if 'general' in data:
        container.general = GeneralSettings(**data['general'])
    if 'notifications' in data:
        container.notifications = NotificationSettings(**data['notifications'])
    if 'personalization' in data:
        container.personalization = PersonalizationSettings(**data['personalization'])
    if 'memory' in data:
        container.memory = MemorySettings(**data['memory'])
    if 'apps_connectors' in data:
        container.apps_connectors = AppsConnectorsSettings(**data['apps_connectors'])
    if 'data_controls' in data:
        container.data_controls = DataControlsSettings(**data['data_controls'])
    if 'security' in data:
        container.security = SecuritySettings(**data['security'])
    if 'parental_controls' in data:
        container.parental_controls = ParentalControlsSettings(**data['parental_controls'])
    if 'account' in data:
        container.account = AccountSettings(**data['account'])

    return container


def validate_settings(settings: SettingsContainer) -> List[str]:
    """Valida un contenedor de configuraciones completo."""
    return settings.validate()