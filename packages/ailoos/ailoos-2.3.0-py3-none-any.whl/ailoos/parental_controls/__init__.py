"""
Sistema de Controles Parentales de AILOOS
==========================================

Módulo completo para la gestión de controles parentales en AILOOS.
Proporciona funcionalidades avanzadas para protección infantil incluyendo:

- Gestión de PIN parental con encriptación segura
- Límites de tiempo con tracking detallado de uso
- Filtros de contenido adaptativos (estricto, moderado, permisivo)
- Moderación de contenido en tiempo real
- Validaciones de acceso basadas en edad y restricciones
- Integración completa con el sistema de configuraciones
- Logging y monitoreo de actividades
- API para integración con otros módulos

Características principales:
- Seguridad: PIN parental con hash SHA-256 + salt
- Flexibilidad: Configuración granular por usuario/edad
- Rendimiento: Caching inteligente y validaciones eficientes
- Escalabilidad: Soporte para múltiples usuarios concurrentes
- Auditabilidad: Logs detallados de todas las acciones
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib
import secrets
import re
from enum import Enum

# Importar dependencias del sistema
from ..settings import get_settings_manager, ParentalControlsSettings
from ..core.logging import get_logger

# Configurar logging
logger = get_logger(__name__)

# ==================== TIPOS Y ENUMERACIONES ====================

class ContentFilterLevel(Enum):
    """Niveles de filtro de contenido."""
    LENIENT = "lenient"
    MODERATE = "moderate"
    STRICT = "strict"

class AgeRestriction(Enum):
    """Restricciones por edad."""
    ALL_AGES = "all_ages"  # Sin restricciones
    AGE_7_PLUS = "7_plus"  # 7 años o más
    AGE_13_PLUS = "13_plus"  # 13 años o más
    AGE_16_PLUS = "16_plus"  # 16 años o más
    AGE_18_PLUS = "18_plus"  # 18 años o más

class TimeLimitType(Enum):
    """Tipos de límites de tiempo."""
    DAILY = "daily"
    SESSION = "session"
    WEEKLY = "weekly"

# ==================== EXCEPCIONES ====================

class ParentalControlError(Exception):
    """Excepción base para errores de controles parentales."""
    pass

class InvalidParentalPinError(ParentalControlError):
    """PIN parental inválido."""
    pass

class ParentalControlDisabledError(ParentalControlError):
    """Controles parentales desactivados."""
    pass

class TimeLimitExceededError(ParentalControlError):
    """Límite de tiempo excedido."""
    pass

class ContentBlockedError(ParentalControlError):
    """Contenido bloqueado por filtros parentales."""
    pass

class AgeRestrictionError(ParentalControlError):
    """Acceso denegado por restricción de edad."""
    pass

# ==================== MODELOS DE DATOS ====================

@dataclass
class UserProfile:
    """Perfil de usuario para controles parentales."""
    user_id: int
    age: Optional[int] = None
    is_child: bool = False
    parent_user_id: Optional[int] = None
    restrictions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class TimeUsage:
    """Registro de uso de tiempo."""
    user_id: int
    date: str  # YYYY-MM-DD
    total_minutes: int = 0
    session_minutes: int = 0
    last_activity: Optional[datetime] = None
    daily_limit: int = 120  # minutos por defecto
    session_limit: int = 60  # minutos por sesión

@dataclass
class ContentAnalysis:
    """Análisis de contenido para moderación."""
    content_type: str  # "text", "image", "video", "url"
    content: str
    risk_score: float = 0.0  # 0.0 - 1.0
    blocked: bool = False
    categories: List[str] = field(default_factory=list)
    analysis_time: datetime = field(default_factory=datetime.now)

# ==================== GESTOR PRINCIPAL ====================

class ParentalControlsManager:
    """
    Gestor principal de controles parentales.

    Proporciona una interfaz unificada para todas las funcionalidades
    de control parental en AILOOS.
    """

    def __init__(self, settings_manager=None):
        """
        Inicializa el gestor de controles parentales.

        Args:
            settings_manager: Instancia del gestor de configuraciones (opcional)
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self._user_profiles: Dict[int, UserProfile] = {}
        self._time_usage: Dict[int, TimeUsage] = {}
        self._pin_cache: Dict[int, str] = {}  # Cache de PINs verificados (temporal)
        self._content_cache: Dict[str, ContentAnalysis] = {}

        logger.info("ParentalControlsManager inicializado")

    # ==================== GESTIÓN DE PIN PARENTAL ====================

    def set_parental_pin(self, user_id: int, pin: str) -> bool:
        """
        Establece un PIN parental para un usuario padre/tutor.

        Args:
            user_id: ID del usuario padre/tutor
            pin: PIN de 4-8 dígitos

        Returns:
            bool: True si se estableció correctamente

        Raises:
            ValueError: Si el PIN no cumple los requisitos
        """
        if not self._validate_pin_format(pin):
            raise ValueError("PIN debe tener 4-8 dígitos numéricos")

        # Generar hash seguro del PIN
        pin_hash = self._hash_pin(pin)

        # Actualizar configuración
        settings = self.settings_manager.get_category('parental_controls')
        settings['parental_pin_hash'] = pin_hash

        self.settings_manager.set('parental_pin_hash', pin_hash, category='parental_controls')

        logger.info(f"PIN parental establecido para usuario {user_id}")
        return True

    def verify_parental_pin(self, user_id: int, pin: str) -> bool:
        """
        Verifica un PIN parental.

        Args:
            user_id: ID del usuario
            pin: PIN a verificar

        Returns:
            bool: True si el PIN es válido

        Raises:
            InvalidParentalPinError: Si el PIN es inválido
        """
        if not self._validate_pin_format(pin):
            raise InvalidParentalPinError("Formato de PIN inválido")

        # Obtener hash almacenado
        stored_hash = self.settings_manager.get('parental_pin_hash', category='parental_controls')
        if not stored_hash:
            raise ParentalControlDisabledError("Controles parentales no configurados")

        # Verificar PIN
        if not self._verify_pin_hash(pin, stored_hash):
            logger.warning(f"PIN parental inválido para usuario {user_id}")
            raise InvalidParentalPinError("PIN parental incorrecto")

        # Cache temporal para evitar verificaciones repetidas
        self._pin_cache[user_id] = pin

        logger.info(f"PIN parental verificado para usuario {user_id}")
        return True

    def is_parental_pin_set(self, user_id: int) -> bool:
        """
        Verifica si hay un PIN parental configurado.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si hay PIN configurado
        """
        pin_hash = self.settings_manager.get('parental_pin_hash', category='parental_controls')
        return bool(pin_hash)

    # ==================== GESTIÓN DE LÍMITES DE TIEMPO ====================

    def check_time_limits(self, user_id: int) -> Dict[str, Any]:
        """
        Verifica los límites de tiempo para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Estado de límites de tiempo
        """
        settings = self.settings_manager.get_category('parental_controls')

        if not settings.get('time_limits', False):
            return {
                'allowed': True,
                'reason': 'time_limits_disabled',
                'remaining_time': None
            }

        # Obtener uso actual
        usage = self._get_time_usage(user_id)
        max_time = self._parse_time_limit(settings.get('max_time_per_day', '2hours'))

        remaining_minutes = max(0, max_time - usage.total_minutes)

        if usage.total_minutes >= max_time:
            return {
                'allowed': False,
                'reason': 'daily_limit_exceeded',
                'remaining_time': 0,
                'used_today': usage.total_minutes,
                'limit_today': max_time
            }

        return {
            'allowed': True,
            'reason': 'within_limits',
            'remaining_time': remaining_minutes,
            'used_today': usage.total_minutes,
            'limit_today': max_time
        }

    def record_time_usage(self, user_id: int, minutes: int, activity_type: str = "general") -> None:
        """
        Registra uso de tiempo para un usuario.

        Args:
            user_id: ID del usuario
            minutes: Minutos usados
            activity_type: Tipo de actividad
        """
        usage = self._get_time_usage(user_id)
        usage.total_minutes += minutes
        usage.session_minutes += minutes
        usage.last_activity = datetime.now()

        # Verificar límites después del registro
        time_check = self.check_time_limits(user_id)
        if not time_check['allowed']:
            logger.warning(f"Límite de tiempo excedido para usuario {user_id}: {time_check}")

        logger.debug(f"Uso de tiempo registrado para usuario {user_id}: +{minutes} min ({activity_type})")

    def reset_daily_usage(self, user_id: int) -> None:
        """
        Resetea el uso diario de tiempo (para tareas programadas).

        Args:
            user_id: ID del usuario
        """
        if user_id in self._time_usage:
            today = datetime.now().strftime('%Y-%m-%d')
            if self._time_usage[user_id].date != today:
                self._time_usage[user_id] = TimeUsage(user_id=user_id, date=today)
                logger.info(f"Uso diario reseteado para usuario {user_id}")

    # ==================== FILTROS DE CONTENIDO ====================

    def check_content_access(self, user_id: int, content: str,
                           content_type: str = "text") -> Dict[str, Any]:
        """
        Verifica si el contenido está permitido según los filtros.

        Args:
            user_id: ID del usuario
            content: Contenido a verificar
            content_type: Tipo de contenido ("text", "url", etc.)

        Returns:
            Dict[str, Any]: Resultado del análisis de contenido
        """
        settings = self.settings_manager.get_category('parental_controls')
        filter_level = ContentFilterLevel(settings.get('content_filter', 'moderate'))

        # Análisis básico según nivel de filtro
        analysis = self._analyze_content(content, content_type, filter_level)

        if analysis.blocked:
            return {
                'allowed': False,
                'reason': 'content_blocked',
                'risk_score': analysis.risk_score,
                'categories': analysis.categories,
                'filter_level': filter_level.value
            }

        return {
            'allowed': True,
            'reason': 'content_allowed',
            'risk_score': analysis.risk_score,
            'categories': analysis.categories,
            'filter_level': filter_level.value
        }

    def moderate_content_realtime(self, user_id: int, content: str,
                                content_type: str = "text") -> str:
        """
        Modera contenido en tiempo real aplicando filtros.

        Args:
            user_id: ID del usuario
            content: Contenido original
            content_type: Tipo de contenido

        Returns:
            str: Contenido moderado

        Raises:
            ContentBlockedError: Si el contenido está completamente bloqueado
        """
        access_check = self.check_content_access(user_id, content, content_type)

        if not access_check['allowed']:
            raise ContentBlockedError(f"Contenido bloqueado: {access_check['reason']}")

        # Aplicar moderación según nivel
        return self._apply_content_moderation(content, content_type, access_check)

    # ==================== VALIDACIONES DE ACCESO POR EDAD ====================

    def validate_age_access(self, user_id: int, required_age: AgeRestriction,
                          content_category: str = "") -> bool:
        """
        Valida acceso basado en edad y restricciones.

        Args:
            user_id: ID del usuario
            required_age: Edad mínima requerida
            content_category: Categoría de contenido (opcional)

        Returns:
            bool: True si el acceso está permitido

        Raises:
            AgeRestrictionError: Si el acceso está denegado por edad
        """
        profile = self._get_user_profile(user_id)

        if not profile.age:
            # Si no hay edad registrada, asumir acceso restringido
            if required_age != AgeRestriction.ALL_AGES:
                raise AgeRestrictionError("Edad no registrada - acceso restringido")
            return True

        # Verificar edad mínima
        min_age = self._get_min_age_for_restriction(required_age)
        if profile.age < min_age:
            raise AgeRestrictionError(f"Contenido requiere edad mínima de {min_age} años")

        # Verificar restricciones específicas del perfil
        if content_category in profile.restrictions:
            raise AgeRestrictionError(f"Categoría '{content_category}' restringida para este usuario")

        return True

    def set_user_age(self, user_id: int, age: int, parent_pin: str) -> None:
        """
        Establece la edad de un usuario (requiere PIN parental).

        Args:
            user_id: ID del usuario
            age: Edad en años
            parent_pin: PIN parental para autorización

        Raises:
            ValueError: Si la edad es inválida
            InvalidParentalPinError: Si el PIN es incorrecto
        """
        if not 1 <= age <= 120:
            raise ValueError("Edad debe estar entre 1 y 120 años")

        # Verificar PIN parental
        self.verify_parental_pin(user_id, parent_pin)

        profile = self._get_user_profile(user_id)
        profile.age = age
        profile.is_child = age < 18
        profile.updated_at = datetime.now()

        logger.info(f"Edad actualizada para usuario {user_id}: {age} años")

    # ==================== MÉTODOS PRIVADOS ====================

    def _validate_pin_format(self, pin: str) -> bool:
        """Valida el formato del PIN."""
        return bool(re.match(r'^\d{4,8}$', pin))

    def _hash_pin(self, pin: str) -> str:
        """Genera hash seguro del PIN con salt."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256(f"{pin}{salt}".encode())
        return f"{salt}:{hash_obj.hexdigest()}"

    def _verify_pin_hash(self, pin: str, stored_hash: str) -> bool:
        """Verifica PIN contra hash almacenado."""
        try:
            salt, hash_value = stored_hash.split(':', 1)
            expected_hash = hashlib.sha256(f"{pin}{salt}".encode()).hexdigest()
            return secrets.compare_digest(hash_value, expected_hash)
        except ValueError:
            return False

    def _get_time_usage(self, user_id: int) -> TimeUsage:
        """Obtiene o crea registro de uso de tiempo."""
        today = datetime.now().strftime('%Y-%m-%d')

        if user_id not in self._time_usage or self._time_usage[user_id].date != today:
            settings = self.settings_manager.get_category('parental_controls')
            daily_limit = self._parse_time_limit(settings.get('max_time_per_day', '2hours'))

            self._time_usage[user_id] = TimeUsage(
                user_id=user_id,
                date=today,
                daily_limit=daily_limit
            )

        return self._time_usage[user_id]

    def _parse_time_limit(self, time_str: str) -> int:
        """Convierte string de tiempo a minutos."""
        time_map = {
            '1hour': 60,
            '2hours': 120,
            '4hours': 240,
            '8hours': 480
        }
        return time_map.get(time_str, 120)

    def _analyze_content(self, content: str, content_type: str,
                        filter_level: ContentFilterLevel) -> ContentAnalysis:
        """
        Analiza contenido según nivel de filtro.
        Implementación básica - puede extenderse con IA/ML.
        """
        analysis = ContentAnalysis(content_type=content_type, content=content)

        # Análisis simple basado en palabras clave
        risk_keywords = {
            ContentFilterLevel.STRICT: [
                'violencia', 'sexo', 'droga', 'alcohol', 'apuesta', 'muerte',
                'guerra', 'terrorismo', 'discriminación', 'odio'
            ],
            ContentFilterLevel.MODERATE: [
                'violencia', 'sexo', 'droga', 'alcohol', 'apuesta'
            ],
            ContentFilterLevel.LENIENT: [
                'violencia'  # Solo violencia explícita
            ]
        }

        keywords = risk_keywords.get(filter_level, [])
        content_lower = content.lower()

        found_keywords = [kw for kw in keywords if kw in content_lower]
        analysis.categories = found_keywords
        analysis.risk_score = min(len(found_keywords) * 0.3, 1.0)  # Aumentado a 0.3 para más sensibilidad
        analysis.blocked = analysis.risk_score >= 0.6  # Bajado a 0.6 para bloquear con menos palabras

        return analysis

    def _apply_content_moderation(self, content: str, content_type: str,
                                access_check: Dict[str, Any]) -> str:
        """
        Aplica moderación al contenido.
        Implementación básica - puede extenderse.
        """
        if access_check['risk_score'] < 0.3:
            return content  # Sin moderación

        # Moderación simple: reemplazar palabras problemáticas
        moderated = content
        for category in access_check['categories']:
            # Reemplazar con asteriscos
            moderated = re.sub(rf'\b{re.escape(category)}\b', '*' * len(category),
                             moderated, flags=re.IGNORECASE)

        return moderated

    def _get_user_profile(self, user_id: int) -> UserProfile:
        """Obtiene o crea perfil de usuario."""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserProfile(user_id=user_id)
        return self._user_profiles[user_id]

    def _get_min_age_for_restriction(self, restriction: AgeRestriction) -> int:
        """Obtiene edad mínima para una restricción."""
        age_map = {
            AgeRestriction.ALL_AGES: 0,
            AgeRestriction.AGE_7_PLUS: 7,
            AgeRestriction.AGE_13_PLUS: 13,
            AgeRestriction.AGE_16_PLUS: 16,
            AgeRestriction.AGE_18_PLUS: 18
        }
        return age_map.get(restriction, 0)

# ==================== INSTANCIA GLOBAL ====================

# Instancia global del gestor
parental_controls_manager = ParentalControlsManager()

# ==================== FUNCIONES DE CONVENIENCIA ====================

def get_parental_controls_manager() -> ParentalControlsManager:
    """Obtiene la instancia global del gestor de controles parentales."""
    return parental_controls_manager

def check_time_limits(user_id: int) -> Dict[str, Any]:
    """Función de conveniencia para verificar límites de tiempo."""
    return parental_controls_manager.check_time_limits(user_id)

def check_content_access(user_id: int, content: str, content_type: str = "text") -> Dict[str, Any]:
    """Función de conveniencia para verificar acceso a contenido."""
    return parental_controls_manager.check_content_access(user_id, content, content_type)

def validate_age_access(user_id: int, required_age: AgeRestriction,
                       content_category: str = "") -> bool:
    """Función de conveniencia para validar acceso por edad."""
    return parental_controls_manager.validate_age_access(user_id, required_age, content_category)

# ==================== EXPORTACIONES ====================

__all__ = [
    # Clases principales
    'ParentalControlsManager',

    # Enumeraciones
    'ContentFilterLevel',
    'AgeRestriction',
    'TimeLimitType',

    # Excepciones
    'ParentalControlError',
    'InvalidParentalPinError',
    'ParentalControlDisabledError',
    'TimeLimitExceededError',
    'ContentBlockedError',
    'AgeRestrictionError',

    # Modelos de datos
    'UserProfile',
    'TimeUsage',
    'ContentAnalysis',

    # Funciones de conveniencia
    'get_parental_controls_manager',
    'check_time_limits',
    'check_content_access',
    'validate_age_access',

    # Instancia global
    'parental_controls_manager'
]