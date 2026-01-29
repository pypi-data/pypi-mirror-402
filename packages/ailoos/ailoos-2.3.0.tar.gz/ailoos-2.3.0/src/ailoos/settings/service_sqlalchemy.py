"""
Servicio SQLAlchemy para configuraciones de usuario de AILOOS
=============================================================

Este módulo proporciona una capa de negocio completa sobre el repositorio SQLAlchemy de configuraciones,
incluyendo lógica de validación avanzada, transformación de datos, manejo de errores robusto
y métodos de alto nivel para gestionar configuraciones de usuario.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import hashlib
import re

from .repository_sqlalchemy import SettingsRepositorySQLAlchemy
from .models import (
    SettingsContainer, GeneralSettings, NotificationSettings, PersonalizationSettings,
    MemorySettings, AppsConnectorsSettings, DataControlsSettings, SecuritySettings,
    ParentalControlsSettings, AccountSettings, create_default_settings, validate_settings,
    load_settings_from_dict
)

# Configurar logging
logger = logging.getLogger(__name__)


class SettingsServiceSQLAlchemyError(Exception):
    """Excepción base para errores del servicio SQLAlchemy de configuraciones."""
    pass


class ValidationError(SettingsServiceSQLAlchemyError):
    """Error de validación de datos."""
    pass


class UserNotFoundError(SettingsServiceSQLAlchemyError):
    """Usuario no encontrado."""
    pass


class DuplicateUserError(SettingsServiceSQLAlchemyError):
    """Usuario duplicado."""
    pass


class SettingsServiceSQLAlchemy:
    """
    Servicio de negocio para gestionar configuraciones de usuario usando SQLAlchemy.

    Proporciona una interfaz de alto nivel con validación avanzada, transformación de datos,
    manejo de errores robusto y operaciones de negocio complejas sobre el repositorio SQLAlchemy.
    """

    def __init__(self, db_session_factory):
        """
        Inicializa el servicio con una fábrica de sesiones de base de datos.

        Args:
            db_session_factory: Función que retorna una sesión de SQLAlchemy
        """
        self.repository = SettingsRepositorySQLAlchemy(db_session_factory)
        logger.info("Servicio SQLAlchemy de configuraciones inicializado")

    # ==================== GESTIÓN DE USUARIOS ====================

    def create_user(self, username: str, email: str, name: str = "", phone: str = "") -> Dict[str, Any]:
        """
        Crea un nuevo usuario con validación avanzada.

        Args:
            username: Nombre de usuario único (3-30 caracteres, solo letras, números, guiones)
            email: Email único y válido
            name: Nombre completo opcional
            phone: Número de teléfono opcional

        Returns:
            Dict[str, Any]: Información del usuario creado

        Raises:
            ValidationError: Si los datos no pasan validación
            DuplicateUserError: Si el usuario o email ya existen
        """
        # Validar datos de entrada
        self._validate_username(username)
        self._validate_email(email)
        if name:
            self._validate_name(name)
        if phone:
            self._validate_phone(phone)

        try:
            user_id = self.repository.create_user(username, email)

            # Actualizar información adicional de cuenta si se proporciona
            if name or phone:
                account_settings = AccountSettings(name=name, email=email, phone=phone)
                self.repository.update_category_settings(user_id, 'account', {
                    'name': name,
                    'email': email,
                    'phone': phone
                }, validate=False)

            # Obtener usuario completo
            user = self.repository.get_user(user_id)
            logger.info(f"Usuario creado exitosamente: {username} (ID: {user_id})")

            return user

        except ValueError as e:
            if "ya existen" in str(e):
                raise DuplicateUserError(str(e))
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error al crear usuario {username}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al crear usuario: {e}")

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene información de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Información del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        user = self.repository.get_user(user_id)
        if not user:
            raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
        return user

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """
        Obtiene información de un usuario por nombre de usuario.

        Args:
            username: Nombre de usuario

        Returns:
            Dict[str, Any]: Información del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        user = self.repository.get_user_by_username(username)
        if not user:
            raise UserNotFoundError(f"Usuario '{username}' no encontrado")
        return user

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Obtiene información de un usuario por email.

        Args:
            email: Email del usuario

        Returns:
            Dict[str, Any]: Información del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        user = self.repository.get_user_by_email(email)
        if not user:
            raise UserNotFoundError(f"Usuario con email '{email}' no encontrado")
        return user

    def update_user(self, user_id: int, username: Optional[str] = None,
                    email: Optional[str] = None, name: Optional[str] = None,
                    phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Actualiza información de un usuario con validación.

        Args:
            user_id: ID del usuario
            username: Nuevo nombre de usuario
            email: Nuevo email
            name: Nuevo nombre completo
            phone: Nuevo número de teléfono

        Returns:
            Dict[str, Any]: Información actualizada del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si los datos no pasan validación
            DuplicateUserError: Si el nuevo username o email ya existen
        """
        # Validar datos si se proporcionan
        if username:
            self._validate_username(username)
        if email:
            self._validate_email(email)
        if name:
            self._validate_name(name)
        if phone:
            self._validate_phone(phone)

        try:
            # Actualizar usuario base
            success = self.repository.update_user(user_id, username, email)
            if not success:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Actualizar información de cuenta si se proporciona
            if name or phone:
                current_account = self.get_user_settings(user_id).account
                update_data = {}
                if name is not None:
                    update_data['name'] = name
                if phone is not None:
                    update_data['phone'] = phone

                self.repository.update_category_settings(user_id, 'account', update_data, validate=False)

            # Obtener usuario actualizado
            user = self.repository.get_user(user_id)
            logger.info(f"Usuario actualizado: ID {user_id}")

            return user

        except ValueError as e:
            if "ya existe" in str(e):
                raise DuplicateUserError(str(e))
            raise ValidationError(str(e))
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al actualizar usuario: {e}")

    def delete_user(self, user_id: int) -> bool:
        """
        Elimina un usuario y todas sus configuraciones.

        Args:
            user_id: ID del usuario a eliminar

        Returns:
            bool: True si se eliminó exitosamente

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            success = self.repository.delete_user(user_id)
            if not success:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            logger.info(f"Usuario eliminado: ID {user_id}")
            return True

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al eliminar usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al eliminar usuario: {e}")

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Lista todos los usuarios del sistema.

        Returns:
            List[Dict[str, Any]]: Lista de usuarios
        """
        try:
            return self.repository.list_users()
        except Exception as e:
            logger.error(f"Error al listar usuarios: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al listar usuarios: {e}")

    # ==================== GESTIÓN DE CONFIGURACIONES ====================

    def get_user_settings(self, user_id: int) -> SettingsContainer:
        """
        Obtiene todas las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            SettingsContainer: Contenedor con todas las configuraciones

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        settings = self.repository.get_user_settings(user_id)
        if not settings:
            raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
        return settings

    def update_user_settings(self, user_id: int, settings: SettingsContainer,
                            validate: bool = True) -> SettingsContainer:
        """
        Actualiza todas las configuraciones de un usuario con validación avanzada.

        Args:
            user_id: ID del usuario
            settings: Nuevas configuraciones
            validate: Si se debe validar antes de guardar

        Returns:
            SettingsContainer: Configuraciones actualizadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si la validación falla
        """
        # Transformar y validar datos
        transformed_settings = self._transform_settings_data(settings)

        if validate:
            errors = validate_settings(transformed_settings)
            if errors:
                raise ValidationError(f"Errores de validación: {errors}")

        # Aplicar reglas de negocio adicionales
        self._apply_business_rules(transformed_settings)

        try:
            success = self.repository.update_user_settings(user_id, transformed_settings, validate=False)
            if not success:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Retornar configuraciones actualizadas
            updated_settings = self.repository.get_user_settings(user_id)
            logger.info(f"Configuraciones actualizadas para usuario ID: {user_id}")

            return updated_settings

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar configuraciones para usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al actualizar configuraciones: {e}")

    def update_category_settings(self, user_id: int, category: str,
                                settings: Dict[str, Any], validate: bool = True) -> SettingsContainer:
        """
        Actualiza una categoría específica de configuraciones.

        Args:
            user_id: ID del usuario
            category: Nombre de la categoría
            settings: Diccionario con configuraciones a actualizar
            validate: Si se debe validar

        Returns:
            SettingsContainer: Todas las configuraciones actualizadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si la categoría no existe o validación falla
        """
        # Validar categoría
        if not self._is_valid_category(category):
            raise ValidationError(f"Categoría '{category}' no válida")

        # Transformar datos según categoría
        transformed_data = self._transform_category_data(category, settings)

        if validate:
            # Validación básica de tipos y rangos
            errors = self._validate_category_data(category, transformed_data)
            if errors:
                raise ValidationError(f"Errores de validación en {category}: {errors}")

        try:
            success = self.repository.update_category_settings(user_id, category, transformed_data, validate=False)
            if not success:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Retornar todas las configuraciones
            updated_settings = self.repository.get_user_settings(user_id)
            logger.info(f"Categoría '{category}' actualizada para usuario ID: {user_id}")

            return updated_settings

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar categoría {category} para usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al actualizar categoría: {e}")

    def reset_user_settings_to_default(self, user_id: int) -> SettingsContainer:
        """
        Resetea todas las configuraciones de un usuario a valores por defecto.

        Args:
            user_id: ID del usuario

        Returns:
            SettingsContainer: Configuraciones por defecto

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            success = self.repository.reset_user_settings_to_default(user_id)
            if not success:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Retornar configuraciones por defecto
            default_settings = self.repository.get_user_settings(user_id)
            logger.info(f"Configuraciones reseteadas a valores por defecto para usuario ID: {user_id}")

            return default_settings

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al resetear configuraciones para usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al resetear configuraciones: {e}")

    # ==================== MÉTODOS DE ALTO NIVEL ====================

    def initialize_user_settings(self, user_id: int) -> SettingsContainer:
        """
        Inicializa configuraciones completas para un usuario existente.

        Args:
            user_id: ID del usuario

        Returns:
            SettingsContainer: Configuraciones inicializadas

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        # Verificar que el usuario existe
        self.get_user(user_id)

        # Crear configuraciones por defecto
        default_settings = create_default_settings()

        # Aplicar inicializaciones específicas
        self._initialize_user_defaults(default_settings)

        return self.update_user_settings(user_id, default_settings, validate=False)

    def bulk_update_settings(self, user_id: int, updates: Dict[str, Dict[str, Any]],
                            validate: bool = True) -> SettingsContainer:
        """
        Actualiza múltiples categorías de configuraciones en una sola operación.

        Args:
            user_id: ID del usuario
            updates: Diccionario con categorías y sus actualizaciones
            validate: Si se debe validar

        Returns:
            SettingsContainer: Configuraciones actualizadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si alguna validación falla
        """
        # Obtener configuraciones actuales
        current_settings = self.get_user_settings(user_id)

        # Aplicar actualizaciones
        for category, settings in updates.items():
            if not self._is_valid_category(category):
                raise ValidationError(f"Categoría '{category}' no válida")

            transformed_data = self._transform_category_data(category, settings)
            current_settings.update_category(category, transformed_data)

        # Validar si se solicita
        if validate:
            errors = validate_settings(current_settings)
            if errors:
                raise ValidationError(f"Errores de validación: {errors}")

        # Aplicar reglas de negocio
        self._apply_business_rules(current_settings)

        # Actualizar en base de datos
        return self.update_user_settings(user_id, current_settings, validate=False)

    def get_settings_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen ejecutivo de las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Resumen de configuraciones

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            summary = self.repository.get_settings_summary(user_id)
            if not summary:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            return summary
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al obtener resumen para usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al obtener resumen: {e}")

    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Exporta todos los datos de un usuario (usuario + configuraciones).

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Datos completos del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        user = self.get_user(user_id)
        settings = self.get_user_settings(user_id)

        return {
            'user': user,
            'settings': settings.to_dict(),
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        }

    def import_user_data(self, user_id: int, data: Dict[str, Any], validate: bool = True) -> SettingsContainer:
        """
        Importa datos de usuario desde un export.

        Args:
            user_id: ID del usuario destino
            data: Datos exportados a importar
            validate: Si se debe validar

        Returns:
            SettingsContainer: Configuraciones importadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si los datos son inválidos
        """
        # Verificar que el usuario existe
        self.get_user(user_id)

        # Validar estructura de datos
        if 'settings' not in data:
            raise ValidationError("Datos de importación inválidos: falta sección 'settings'")

        try:
            # Cargar configuraciones desde diccionario
            settings = load_settings_from_dict(data['settings'])

            # Actualizar configuraciones
            return self.update_user_settings(user_id, settings, validate)

        except Exception as e:
            logger.error(f"Error al importar datos para usuario {user_id}: {e}")
            raise ValidationError(f"Error al importar datos: {e}")

    # ==================== VALIDACIÓN AVANZADA ====================

    def _validate_username(self, username: str) -> None:
        """Valida un nombre de usuario."""
        if not username or len(username) < 3:
            raise ValidationError("El nombre de usuario debe tener al menos 3 caracteres")
        if len(username) > 30:
            raise ValidationError("El nombre de usuario no puede exceder 30 caracteres")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("El nombre de usuario solo puede contener letras, números, guiones y guiones bajos")

    def _validate_email(self, email: str) -> None:
        """Valida una dirección de email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValidationError("La dirección de email no es válida")

    def _validate_name(self, name: str) -> None:
        """Valida un nombre completo."""
        if len(name) > 100:
            raise ValidationError("El nombre no puede exceder 100 caracteres")
        if not name.strip():
            raise ValidationError("El nombre no puede estar vacío")

    def _validate_phone(self, phone: str) -> None:
        """Valida un número de teléfono."""
        # Permite formatos españoles: +34 600 000 000, 600 000 000, +34600000000
        phone_pattern = re.compile(r'^(\+34\s?)?[6-9]\d{2}(\s?\d{3}){2}$')
        if not phone_pattern.match(phone.replace(' ', '')):
            raise ValidationError("El número de teléfono debe tener un formato válido (ej: +34 600 000 000)")

    def _is_valid_category(self, category: str) -> bool:
        """Verifica si una categoría es válida."""
        valid_categories = {
            'general', 'notifications', 'personalization', 'memory',
            'apps_connectors', 'data_controls', 'security', 'parental_controls', 'account'
        }
        return category in valid_categories

    def _validate_category_data(self, category: str, data: Dict[str, Any]) -> List[str]:
        """Valida datos de una categoría específica."""
        errors = []

        # Crear instancia temporal para validación
        category_class_map = {
            'general': GeneralSettings,
            'notifications': NotificationSettings,
            'personalization': PersonalizationSettings,
            'memory': MemorySettings,
            'apps_connectors': AppsConnectorsSettings,
            'data_controls': DataControlsSettings,
            'security': SecuritySettings,
            'parental_controls': ParentalControlsSettings,
            'account': AccountSettings,
        }

        try:
            category_class = category_class_map[category]
            temp_instance = category_class(**data)
            errors = temp_instance.validate()
        except Exception as e:
            errors.append(f"Error al validar datos de categoría {category}: {e}")

        return errors

    # ==================== TRANSFORMACIÓN DE DATOS ====================

    def _transform_settings_data(self, settings: SettingsContainer) -> SettingsContainer:
        """Aplica transformaciones de datos al contenedor completo."""
        # Normalizar emails a minúsculas
        if settings.account.email:
            settings.account.email = settings.account.email.lower()

        # Normalizar URLs
        if settings.apps_connectors.webhook_url:
            settings.apps_connectors.webhook_url = settings.apps_connectors.webhook_url.strip()

        # Asegurar consistencia en memoria
        if settings.memory.memory_used > settings.memory.max_memory_items:
            settings.memory.memory_used = settings.memory.max_memory_items

        return settings

    def _transform_category_data(self, category: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica transformaciones específicas por categoría."""
        transformed = data.copy()

        if category == 'account':
            if 'email' in transformed and transformed['email']:
                transformed['email'] = transformed['email'].lower()
        elif category == 'apps_connectors':
            if 'webhook_url' in transformed and transformed['webhook_url']:
                transformed['webhook_url'] = transformed['webhook_url'].strip()

        return transformed

    # ==================== REGLAS DE NEGOCIO ====================

    def _apply_business_rules(self, settings: SettingsContainer) -> None:
        """Aplica reglas de negocio específicas."""
        # Si el control parental está activado, forzar ciertos límites
        if settings.parental_controls.parental_control:
            if not settings.parental_controls.time_limits:
                settings.parental_controls.time_limits = True
            if settings.parental_controls.content_filter == 'lenient':
                settings.parental_controls.content_filter = 'moderate'

        # Si la personalización está desactivada, limpiar datos personales
        if not settings.personalization.enable_personalization:
            settings.personalization.nickname = ""
            settings.personalization.occupation = ""
            settings.personalization.more_about_you = ""

        # Si las notificaciones están silenciadas, desactivar todas
        if settings.notifications.mute_all:
            settings.notifications.responses_app = False
            settings.notifications.responses_email = False
            settings.notifications.tasks_app = False
            settings.notifications.tasks_email = False
            settings.notifications.projects_app = False
            settings.notifications.projects_email = False
            settings.notifications.recommendations_app = False
            settings.notifications.recommendations_email = False

    def _initialize_user_defaults(self, settings: SettingsContainer) -> None:
        """Aplica inicializaciones específicas para nuevos usuarios."""
        # Configurar idioma basado en zona horaria (si estuviera disponible)
        # Por ahora, mantener valores por defecto

        # Inicializar estadísticas
        settings.account.sessions_completed = 0
        settings.account.tokens_used = 0

        # Configurar memoria inicial
        settings.memory.memory_used = 0

    # ==================== MÉTODOS DE UTILIDAD ====================

    def validate_user_settings(self, user_id: int) -> List[str]:
        """
        Valida las configuraciones actuales de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[str]: Lista de errores de validación

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            return self.repository.validate_user_settings(user_id)
        except Exception as e:
            if "Usuario no encontrado" in str(e):
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            logger.error(f"Error al validar configuraciones para usuario {user_id}: {e}")
            raise SettingsServiceSQLAlchemyError(f"Error al validar configuraciones: {e}")

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Estadísticas del usuario

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        settings = self.get_user_settings(user_id)

        return {
            'user_id': user_id,
            'sessions_completed': settings.account.sessions_completed,
            'tokens_used': settings.account.tokens_used,
            'memory_usage': {
                'used': settings.memory.memory_used,
                'max': settings.memory.max_memory_items,
                'percentage': (settings.memory.memory_used / settings.memory.max_memory_items * 100) if settings.memory.max_memory_items > 0 else 0
            },
            'last_updated': settings.updated_at.isoformat()
        }

    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Limpia datos antiguos (logs, cachés, etc.). Método placeholder.

        Args:
            days: Días de antigüedad para considerar como "antiguo"

        Returns:
            int: Número de elementos limpiados
        """
        # Placeholder para futura implementación
        logger.info(f"Limpieza de datos antiguos ({days} días) - funcionalidad pendiente")
        return 0