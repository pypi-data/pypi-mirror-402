"""
Servicio de configuraciones de usuario con SQLAlchemy
=====================================================

Este módulo implementa UserSettingsService, un servicio de alto nivel que integra
los modelos SQLAlchemy con lógica de negocio avanzada para gestionar todas las
operaciones CRUD de configuraciones de usuario en AILOOS.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import hashlib
import re
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models_sqlalchemy import (
    Base, User, GeneralSettings, NotificationSettings, PersonalizationSettings,
    MemorySettings, AppsConnectorsSettings, DataControlsSettings, SecuritySettings,
    ParentalControlsSettings, AccountSettings
)

# Configurar logging
logger = logging.getLogger(__name__)


class UserSettingsServiceError(Exception):
    """Excepción base para errores del servicio de configuraciones."""
    pass


class ValidationError(UserSettingsServiceError):
    """Error de validación de datos."""
    pass


class UserNotFoundError(UserSettingsServiceError):
    """Usuario no encontrado."""
    pass


class DuplicateUserError(UserSettingsServiceError):
    """Usuario duplicado."""
    pass


class UserSettingsService:
    """
    Servicio de negocio para gestionar configuraciones de usuario usando SQLAlchemy.

    Proporciona una interfaz de alto nivel con validación avanzada, transformación de datos,
    manejo de errores robusto y operaciones de negocio complejas sobre modelos SQLAlchemy.
    """

    def __init__(self, database_url: str = "postgresql://user:password@localhost/ailoos"):
        """
        Inicializa el servicio con la URL de la base de datos.

        Args:
            database_url: URL de conexión a PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Crear tablas si no existen
        Base.metadata.create_all(bind=self.engine)

        logger.info("Servicio de configuraciones de usuario inicializado con SQLAlchemy")

    def _get_db(self) -> Session:
        """Obtiene una sesión de base de datos."""
        return self.SessionLocal()

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

        db = self._get_db()
        try:
            # Verificar duplicados
            existing = db.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            if existing:
                if existing.username == username:
                    raise DuplicateUserError("Nombre de usuario ya existe")
                else:
                    raise DuplicateUserError("Email ya existe")

            # Crear usuario
            user = User(username=username, email=email)
            db.add(user)
            db.flush()  # Para obtener el ID

            # Crear configuraciones por defecto
            self._create_default_settings_for_user(db, user.id)

            # Actualizar información adicional si se proporciona
            if name or phone:
                account_settings = db.query(AccountSettings).filter_by(user_id=user.id).first()
                if account_settings:
                    account_settings.name = name
                    account_settings.email = email
                    account_settings.phone = phone
                    account_settings.updated_at = datetime.utcnow()

            db.commit()

            # Obtener usuario completo con configuraciones
            user_data = self._user_to_dict(user)
            logger.info(f"Usuario creado exitosamente: {username} (ID: {user.id})")

            return user_data

        except IntegrityError as e:
            db.rollback()
            if "username" in str(e):
                raise DuplicateUserError("Nombre de usuario ya existe")
            elif "email" in str(e):
                raise DuplicateUserError("Email ya existe")
            raise ValidationError(f"Error de integridad: {e}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear usuario {username}: {e}")
            raise UserSettingsServiceError(f"Error al crear usuario: {e}")
        finally:
            db.close()

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
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            return self._user_to_dict(user)
        finally:
            db.close()

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
        db = self._get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise UserNotFoundError(f"Usuario '{username}' no encontrado")

            return self._user_to_dict(user)
        finally:
            db.close()

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
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise UserNotFoundError(f"Usuario con email '{email}' no encontrado")

            return self._user_to_dict(user)
        finally:
            db.close()

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

        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Verificar conflictos si se actualizan username o email
            if username and username != user.username:
                existing = db.query(User).filter(
                    and_(User.username == username, User.id != user_id)
                ).first()
                if existing:
                    raise DuplicateUserError("Nombre de usuario ya existe")

            if email and email != user.email:
                existing = db.query(User).filter(
                    and_(User.email == email, User.id != user_id)
                ).first()
                if existing:
                    raise DuplicateUserError("Email ya existe")

            # Actualizar usuario base
            if username:
                user.username = username
            if email:
                user.email = email
            user.updated_at = datetime.utcnow()

            # Actualizar información de cuenta si se proporciona
            if name is not None or phone is not None:
                account_settings = db.query(AccountSettings).filter_by(user_id=user_id).first()
                if account_settings:
                    if name is not None:
                        account_settings.name = name
                    if phone is not None:
                        account_settings.phone = phone
                    account_settings.updated_at = datetime.utcnow()

            db.commit()

            # Obtener usuario actualizado
            updated_user = self._user_to_dict(user)
            logger.info(f"Usuario actualizado: ID {user_id}")

            return updated_user

        except IntegrityError as e:
            db.rollback()
            raise DuplicateUserError("Datos duplicados")
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al actualizar usuario: {e}")
        finally:
            db.close()

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
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Eliminar usuario (las configuraciones se eliminan automáticamente por CASCADE)
            db.delete(user)
            db.commit()

            logger.info(f"Usuario eliminado: ID {user_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error al eliminar usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al eliminar usuario: {e}")
        finally:
            db.close()

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Lista todos los usuarios del sistema.

        Returns:
            List[Dict[str, Any]]: Lista de usuarios
        """
        db = self._get_db()
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()
            return [self._user_to_dict(user) for user in users]
        finally:
            db.close()

    # ==================== GESTIÓN DE CONFIGURACIONES ====================

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene todas las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Todas las configuraciones organizadas por categorías

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            settings = {
                'general': self._settings_to_dict(user.general_settings),
                'notifications': self._settings_to_dict(user.notification_settings),
                'personalization': self._settings_to_dict(user.personalization_settings),
                'memory': self._settings_to_dict(user.memory_settings),
                'apps_connectors': self._settings_to_dict(user.apps_connectors_settings),
                'data_controls': self._settings_to_dict(user.data_controls_settings),
                'security': self._settings_to_dict(user.security_settings),
                'parental_controls': self._settings_to_dict(user.parental_controls_settings),
                'account': self._settings_to_dict(user.account_settings),
            }

            return settings

        finally:
            db.close()

    def update_user_settings(self, user_id: int, settings: Dict[str, Any],
                           validate: bool = True) -> Dict[str, Any]:
        """
        Actualiza todas las configuraciones de un usuario con validación avanzada.

        Args:
            user_id: ID del usuario
            settings: Diccionario con todas las configuraciones por categorías
            validate: Si se debe validar antes de guardar

        Returns:
            Dict[str, Any]: Configuraciones actualizadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si la validación falla
        """
        # Transformar y validar datos
        transformed_settings = self._transform_settings_data(settings)

        if validate:
            errors = self._validate_settings_data(transformed_settings)
            if errors:
                raise ValidationError(f"Errores de validación: {errors}")

        # Aplicar reglas de negocio adicionales
        self._apply_business_rules(transformed_settings)

        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Actualizar cada categoría
            self._update_general_settings(db, user_id, transformed_settings.get('general', {}))
            self._update_notification_settings(db, user_id, transformed_settings.get('notifications', {}))
            self._update_personalization_settings(db, user_id, transformed_settings.get('personalization', {}))
            self._update_memory_settings(db, user_id, transformed_settings.get('memory', {}))
            self._update_apps_connectors_settings(db, user_id, transformed_settings.get('apps_connectors', {}))
            self._update_data_controls_settings(db, user_id, transformed_settings.get('data_controls', {}))
            self._update_security_settings(db, user_id, transformed_settings.get('security', {}))
            self._update_parental_controls_settings(db, user_id, transformed_settings.get('parental_controls', {}))
            self._update_account_settings(db, user_id, transformed_settings.get('account', {}))

            db.commit()

            # Retornar configuraciones actualizadas
            updated_settings = self.get_user_settings(user_id)
            logger.info(f"Configuraciones actualizadas para usuario ID: {user_id}")

            return updated_settings

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Error de integridad al actualizar configuraciones para usuario {user_id}: {e}")
            raise ValidationError(f"Los datos proporcionados violan restricciones de integridad: {e}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar configuraciones para usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al actualizar configuraciones: {e}")
        finally:
            db.close()

    def update_category_settings(self, user_id: int, category: str,
                               settings: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """
        Actualiza una categoría específica de configuraciones.

        Args:
            user_id: ID del usuario
            category: Nombre de la categoría
            settings: Diccionario con configuraciones a actualizar
            validate: Si se debe validar

        Returns:
            Dict[str, Any]: Todas las configuraciones actualizadas

        Raises:
            UserNotFoundError: Si el usuario no existe
            ValidationError: Si la categoría no existe o validación falla
        """
        # Validar categoría
        if not self._is_valid_category(category):
            raise ValidationError(f"Categoría '{category}' no válida")

        # Obtener configuraciones actuales
        current_settings = self.get_user_settings(user_id)

        # Aplicar cambios a la categoría específica
        current_settings[category].update(settings)

        # Aplicar reglas de negocio
        self._apply_business_rules(current_settings)

        # Transformar datos
        transformed_settings = self._transform_settings_data(current_settings)

        if validate:
            # Validación completa
            errors = self._validate_settings_data(transformed_settings)
            if errors:
                raise ValidationError(f"Errores de validación: {errors}")

        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Actualizar la categoría específica
            category_method_map = {
                'general': '_update_general_settings',
                'notifications': '_update_notification_settings',
                'personalization': '_update_personalization_settings',
                'memory': '_update_memory_settings',
                'apps_connectors': '_update_apps_connectors_settings',
                'data_controls': '_update_data_controls_settings',
                'security': '_update_security_settings',
                'parental_controls': '_update_parental_controls_settings',
                'account': '_update_account_settings',
            }

            update_method_name = category_method_map[category]
            update_method = getattr(self, update_method_name)
            update_method(db, user_id, transformed_settings[category])

            db.commit()

            # Retornar todas las configuraciones
            updated_settings = self.get_user_settings(user_id)
            logger.info(f"Categoría '{category}' actualizada para usuario ID: {user_id}")

            return updated_settings

        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar categoría {category} para usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al actualizar categoría: {e}")
        finally:
            db.close()

    def reset_user_settings_to_default(self, user_id: int) -> Dict[str, Any]:
        """
        Resetea todas las configuraciones de un usuario a valores por defecto.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Configuraciones por defecto

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")

            # Eliminar configuraciones actuales
            db.query(GeneralSettings).filter_by(user_id=user_id).delete()
            db.query(NotificationSettings).filter_by(user_id=user_id).delete()
            db.query(PersonalizationSettings).filter_by(user_id=user_id).delete()
            db.query(MemorySettings).filter_by(user_id=user_id).delete()
            db.query(AppsConnectorsSettings).filter_by(user_id=user_id).delete()
            db.query(DataControlsSettings).filter_by(user_id=user_id).delete()
            db.query(SecuritySettings).filter_by(user_id=user_id).delete()
            db.query(ParentalControlsSettings).filter_by(user_id=user_id).delete()
            db.query(AccountSettings).filter_by(user_id=user_id).delete()

            # Crear configuraciones por defecto
            self._create_default_settings_for_user(db, user_id)

            db.commit()

            # Retornar configuraciones por defecto
            default_settings = self.get_user_settings(user_id)
            logger.info(f"Configuraciones reseteadas a valores por defecto para usuario ID: {user_id}")

            return default_settings

        except Exception as e:
            db.rollback()
            logger.error(f"Error al resetear configuraciones para usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al resetear configuraciones: {e}")
        finally:
            db.close()

    # ==================== MÉTODOS DE ALTO NIVEL ====================

    def initialize_user_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Inicializa configuraciones completas para un usuario existente.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Configuraciones inicializadas

        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        # Verificar que el usuario existe
        self.get_user(user_id)

        # Crear configuraciones por defecto
        default_settings = self._get_default_settings()

        # Aplicar inicializaciones específicas
        self._initialize_user_defaults(default_settings)

        return self.update_user_settings(user_id, default_settings, validate=False)

    def bulk_update_settings(self, user_id: int, updates: Dict[str, Dict[str, Any]],
                           validate: bool = True) -> Dict[str, Any]:
        """
        Actualiza múltiples categorías de configuraciones en una sola operación.

        Args:
            user_id: ID del usuario
            updates: Diccionario con categorías y sus actualizaciones
            validate: Si se debe validar

        Returns:
            Dict[str, Any]: Configuraciones actualizadas

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
            current_settings[category].update(transformed_data)

        # Validar si se solicita
        if validate:
            errors = self._validate_settings_data(current_settings)
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
        settings = self.get_user_settings(user_id)

        return {
            'user_id': user_id,
            'last_updated': settings['general']['updated_at'],
            'version': settings['general']['version'],
            'categories': {
                'general': {
                    'appearance': settings['general']['appearance'],
                    'accent_color': settings['general']['accent_color'],
                    'ui_language': settings['general']['ui_language']
                },
                'notifications': {
                    'mute_all': settings['notifications']['mute_all'],
                    'responses_app': settings['notifications']['responses_app'],
                    'tasks_app': settings['notifications']['tasks_app']
                },
                'security': {
                    'two_factor': settings['security']['two_factor'],
                    'session_timeout': settings['security']['session_timeout']
                },
                'memory': {
                    'memory_used': settings['memory']['memory_used'],
                    'max_memory_items': settings['memory']['max_memory_items']
                }
            }
        }

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
            'settings': settings,
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        }

    def import_user_data(self, user_id: int, data: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """
        Importa datos de usuario desde un export.

        Args:
            user_id: ID del usuario destino
            data: Datos exportados a importar
            validate: Si se debe validar

        Returns:
            Dict[str, Any]: Configuraciones importadas

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
            # Actualizar configuraciones
            return self.update_user_settings(user_id, data['settings'], validate)

        except Exception as e:
            logger.error(f"Error al importar datos para usuario {user_id}: {e}")
            raise ValidationError(f"Error al importar datos: {e}")

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
            settings = self.get_user_settings(user_id)
            return self._validate_settings_data(settings)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error al validar configuraciones para usuario {user_id}: {e}")
            raise UserSettingsServiceError(f"Error al validar configuraciones: {e}")

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
            'sessions_completed': settings['account']['sessions_completed'],
            'tokens_used': settings['account']['tokens_used'],
            'memory_usage': {
                'used': settings['memory']['memory_used'],
                'max': settings['memory']['max_memory_items'],
                'percentage': (settings['memory']['memory_used'] / settings['memory']['max_memory_items'] * 100) if settings['memory']['max_memory_items'] > 0 else 0
            },
            'last_updated': settings['general']['updated_at']
        }

    # ==================== MÉTODOS PRIVADOS ====================

    def _create_default_settings_for_user(self, db: Session, user_id: int) -> None:
        """Crea configuraciones por defecto para un nuevo usuario."""
        # Configuraciones generales
        general = GeneralSettings(user_id=user_id)
        db.add(general)

        # Notificaciones
        notifications = NotificationSettings(user_id=user_id)
        db.add(notifications)

        # Personalización
        personalization = PersonalizationSettings(user_id=user_id)
        db.add(personalization)

        # Memoria
        memory = MemorySettings(user_id=user_id)
        db.add(memory)

        # Aplicaciones y conectores
        apps_connectors = AppsConnectorsSettings(user_id=user_id)
        db.add(apps_connectors)

        # Controles de datos
        data_controls = DataControlsSettings(user_id=user_id)
        db.add(data_controls)

        # Seguridad
        security = SecuritySettings(user_id=user_id)
        db.add(security)

        # Controles parentales
        parental_controls = ParentalControlsSettings(user_id=user_id)
        db.add(parental_controls)

        # Cuenta
        account = AccountSettings(user_id=user_id)
        db.add(account)

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convierte un objeto User a diccionario."""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }

    def _settings_to_dict(self, settings_obj) -> Dict[str, Any]:
        """Convierte un objeto de configuraciones a diccionario."""
        if not settings_obj:
            return {}

        result = {}
        for column in settings_obj.__table__.columns:
            value = getattr(settings_obj, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def _dict_to_settings_object(self, category: str, data: Dict[str, Any]):
        """Convierte un diccionario a objeto de configuraciones."""
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

        category_class = category_class_map[category]

        # Convertir strings de fecha a objetos datetime
        converted_data = {}
        for key, value in data.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                try:
                    converted_data[key] = datetime.fromisoformat(value)
                except ValueError:
                    converted_data[key] = value
            else:
                converted_data[key] = value

        return category_class(**converted_data)

    def _get_default_settings(self) -> Dict[str, Any]:
        """Obtiene configuraciones por defecto."""
        return {
            'general': {
                'appearance': 'system',
                'accent_color': 'blue',
                'font_size': 'medium',
                'send_with_enter': True,
                'ui_language': 'es',
                'spoken_language': 'es',
                'voice': 'ember'
            },
            'notifications': {
                'mute_all': False,
                'responses_app': True,
                'responses_email': True,
                'tasks_app': True,
                'tasks_email': False,
                'projects_app': True,
                'projects_email': True,
                'recommendations_app': False,
                'recommendations_email': False
            },
            'personalization': {
                'enable_personalization': True,
                'custom_instructions': False,
                'base_style_tone': 'witty',
                'nickname': '',
                'occupation': '',
                'more_about_you': '',
                'reference_chat_history': True
            },
            'memory': {
                'memory_used': 0,
                'max_memory_items': 256,
                'reference_memories': True
            },
            'apps_connectors': {
                'google_drive': False,
                'dropbox': False,
                'slack': False,
                'discord': False,
                'discord_bot_token': '',
                'discord_server_id': '',
                'discord_channel_id': '',
                'discord_webhook_url': '',
                'webhook_url': '',
                'webhook_headers': '',
                'webhook_method': 'POST',
                'webhook_enabled': False
            },
            'data_controls': {
                'data_collection': True,
                'analytics': True,
                'data_retention': '1year',
                'export_data': False
            },
            'security': {
                'two_factor': False,
                'session_timeout': '30min',
                'login_alerts': True,
                'password_change_pending': False
            },
            'parental_controls': {
                'parental_control': False,
                'content_filter': 'moderate',
                'time_limits': False,
                'max_time_per_day': '2hours',
                'parental_pin_hash': None
            },
            'account': {
                'name': '',
                'email': '',
                'phone': '',
                'bio': '',
                'sessions_completed': 0,
                'tokens_used': 0
            }
        }

    # Métodos de actualización por categoría (implementación básica)
    def _update_general_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones generales."""
        general = db.query(GeneralSettings).filter_by(user_id=user_id).first()
        if general:
            for key, value in settings.items():
                if hasattr(general, key) and key not in ['created_at', 'updated_at']:
                    setattr(general, key, value)
            general.updated_at = datetime.utcnow()

    def _update_notification_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de notificaciones."""
        notifications = db.query(NotificationSettings).filter_by(user_id=user_id).first()
        if notifications:
            for key, value in settings.items():
                if hasattr(notifications, key) and key not in ['created_at', 'updated_at']:
                    setattr(notifications, key, value)
            notifications.updated_at = datetime.utcnow()

    def _update_personalization_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de personalización."""
        personalization = db.query(PersonalizationSettings).filter_by(user_id=user_id).first()
        if personalization:
            for key, value in settings.items():
                if hasattr(personalization, key) and key not in ['created_at', 'updated_at']:
                    setattr(personalization, key, value)
            personalization.updated_at = datetime.utcnow()

    def _update_memory_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de memoria."""
        memory = db.query(MemorySettings).filter_by(user_id=user_id).first()
        if memory:
            for key, value in settings.items():
                if hasattr(memory, key) and key not in ['created_at', 'updated_at']:
                    setattr(memory, key, value)
            memory.updated_at = datetime.utcnow()

    def _update_apps_connectors_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de aplicaciones y conectores."""
        apps_connectors = db.query(AppsConnectorsSettings).filter_by(user_id=user_id).first()
        if apps_connectors:
            for key, value in settings.items():
                if hasattr(apps_connectors, key) and key not in ['created_at', 'updated_at']:
                    setattr(apps_connectors, key, value)
            apps_connectors.updated_at = datetime.utcnow()

    def _update_data_controls_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de controles de datos."""
        data_controls = db.query(DataControlsSettings).filter_by(user_id=user_id).first()
        if data_controls:
            for key, value in settings.items():
                if hasattr(data_controls, key) and key not in ['created_at', 'updated_at']:
                    setattr(data_controls, key, value)
            data_controls.updated_at = datetime.utcnow()

    def _update_security_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de seguridad."""
        security = db.query(SecuritySettings).filter_by(user_id=user_id).first()
        if security:
            for key, value in settings.items():
                if hasattr(security, key) and key not in ['created_at', 'updated_at']:
                    setattr(security, key, value)
            security.updated_at = datetime.utcnow()

    def _update_parental_controls_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de controles parentales."""
        parental_controls = db.query(ParentalControlsSettings).filter_by(user_id=user_id).first()
        if parental_controls:
            for key, value in settings.items():
                if hasattr(parental_controls, key) and key not in ['created_at', 'updated_at']:
                    setattr(parental_controls, key, value)
            parental_controls.updated_at = datetime.utcnow()

    def _update_account_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> None:
        """Actualiza configuraciones de cuenta."""
        account = db.query(AccountSettings).filter_by(user_id=user_id).first()
        if account:
            for key, value in settings.items():
                if hasattr(account, key) and key not in ['created_at', 'updated_at', 'id', 'user_id']:
                    setattr(account, key, value)
            account.updated_at = datetime.utcnow()

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

        # Crear instancia temporal para validación usando los modelos SQLAlchemy
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
            # Aquí podríamos agregar validación adicional si fuera necesaria
        except Exception as e:
            errors.append(f"Error al validar datos de categoría {category}: {e}")

        return errors

    def _validate_settings_data(self, settings: Dict[str, Any]) -> List[str]:
        """Valida todas las configuraciones."""
        errors = []

        for category, data in settings.items():
            if self._is_valid_category(category):
                category_errors = self._validate_category_data(category, data)
                errors.extend(category_errors)

        return errors

    # ==================== TRANSFORMACIÓN DE DATOS ====================

    def _transform_settings_data(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica transformaciones de datos al contenedor completo."""
        transformed = {}

        for category, data in settings.items():
            # Filtrar campos que no deben actualizarse
            filtered_data = {k: v for k, v in data.items() if k not in ['id', 'user_id', 'created_at', 'updated_at']}
            transformed[category] = self._transform_category_data(category, filtered_data)

        return transformed

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

    def _apply_business_rules(self, settings: Dict[str, Any]) -> None:
        """Aplica reglas de negocio específicas."""
        # Si el control parental está activado, forzar ciertos límites
        parental_controls = settings.get('parental_controls', {})
        if parental_controls.get('parental_control', False):
            parental_controls['time_limits'] = True
            if parental_controls.get('content_filter') == 'lenient':
                parental_controls['content_filter'] = 'moderate'

        # Si la personalización está desactivada, limpiar datos personales
        personalization = settings.get('personalization', {})
        if not personalization.get('enable_personalization', True):
            personalization['nickname'] = ""
            personalization['occupation'] = ""
            personalization['more_about_you'] = ""

        # Si las notificaciones están silenciadas, desactivar todas
        notifications = settings.get('notifications', {})
        if notifications.get('mute_all', False):
            notifications['responses_app'] = False
            notifications['responses_email'] = False
            notifications['tasks_app'] = False
            notifications['tasks_email'] = False
            notifications['projects_app'] = False
            notifications['projects_email'] = False
            notifications['recommendations_app'] = False
            notifications['recommendations_email'] = False

    def _initialize_user_defaults(self, settings: Dict[str, Any]) -> None:
        """Aplica inicializaciones específicas para nuevos usuarios."""
        # Configurar idioma basado en zona horaria (si estuviera disponible)
        # Por ahora, mantener valores por defecto

        # Inicializar estadísticas
        if 'account' in settings:
            settings['account']['sessions_completed'] = 0
            settings['account']['tokens_used'] = 0

        # Configurar memoria inicial
        if 'memory' in settings:
            settings['memory']['memory_used'] = 0