"""
Repositorio de datos para configuraciones de AILOOS
==================================================

Este módulo proporciona una capa de abstracción completa para acceder a la base de datos
settings.db, incluyendo métodos CRUD para todas las categorías de configuraciones,
manejo de transacciones y validación de datos.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import os

from .models import (
    SettingsContainer, GeneralSettings, NotificationSettings, PersonalizationSettings,
    MemorySettings, AppsConnectorsSettings, DataControlsSettings, SecuritySettings,
    ParentalControlsSettings, AccountSettings, create_default_settings, validate_settings,
    load_settings_from_dict
)

# Configurar logging
logger = logging.getLogger(__name__)


class SettingsRepository:
    """
    Repositorio para gestionar configuraciones de usuario en base de datos SQLite.

    Proporciona una interfaz completa para operaciones CRUD sobre todas las categorías
    de configuraciones, con soporte para transacciones y validación de datos.
    """

    def __init__(self, db_path: str = "settings.db"):
        """
        Inicializa el repositorio con la ruta de la base de datos.

        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Asegura que la base de datos existe, creándola si es necesario."""
        if not os.path.exists(self.db_path):
            logger.info(f"Base de datos '{self.db_path}' no existe. Creando esquema...")
            from .create_db import create_database_schema
            create_database_schema(self.db_path)

    @contextmanager
    def _get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos.

        Yields:
            sqlite3.Connection: Conexión a la base de datos
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        except Exception as e:
            logger.error(f"Error en conexión a base de datos: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def transaction(self):
        """
        Context manager para manejar transacciones.

        Yields:
            sqlite3.Connection: Conexión en modo transacción
        """
        with self._get_connection() as conn:
            try:
                # Iniciar transacción
                conn.execute("BEGIN TRANSACTION;")
                yield conn
                conn.commit()
                logger.debug("Transacción confirmada exitosamente")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error en transacción, rollback ejecutado: {e}")
                raise

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convierte una fila de SQLite a diccionario."""
        return dict(row)

    def _execute_query(self, conn: sqlite3.Connection, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Ejecuta una consulta y retorna los resultados como lista de diccionarios."""
        cursor = conn.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def _execute_single(self, conn: sqlite3.Connection, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Ejecuta una consulta que retorna un solo resultado."""
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def _execute_insert(self, conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
        """Ejecuta una inserción y retorna el ID del nuevo registro."""
        cursor = conn.execute(query, params)
        return cursor.lastrowid

    def _execute_update_delete(self, conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
        """Ejecuta una actualización o eliminación y retorna el número de filas afectadas."""
        cursor = conn.execute(query, params)
        return cursor.rowcount

    # ==================== MÉTODOS CRUD PARA USUARIOS ====================

    def create_user(self, username: str, email: str) -> int:
        """
        Crea un nuevo usuario.

        Args:
            username: Nombre de usuario único
            email: Email único del usuario

        Returns:
            int: ID del usuario creado

        Raises:
            ValueError: Si el usuario o email ya existen
            sqlite3.Error: Error de base de datos
        """
        with self.transaction() as conn:
            # Verificar si ya existe
            existing = self._execute_single(
                conn,
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            )
            if existing:
                raise ValueError("Usuario o email ya existen")

            user_id = self._execute_insert(
                conn,
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (username, email)
            )

            # Crear configuraciones por defecto para el usuario
            self._create_default_settings_for_user(conn, user_id)

            logger.info(f"Usuario creado: {username} (ID: {user_id})")
            return user_id

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por ID.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_connection() as conn:
            return self._execute_single(
                conn,
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por nombre de usuario.

        Args:
            username: Nombre de usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_connection() as conn:
            return self._execute_single(
                conn,
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por email.

        Args:
            email: Email del usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_connection() as conn:
            return self._execute_single(
                conn,
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )

    def update_user(self, user_id: int, username: Optional[str] = None, email: Optional[str] = None) -> bool:
        """
        Actualiza los datos de un usuario.

        Args:
            user_id: ID del usuario
            username: Nuevo nombre de usuario (opcional)
            email: Nuevo email (opcional)

        Returns:
            bool: True si se actualizó, False si no se encontró el usuario

        Raises:
            ValueError: Si el nuevo username o email ya existen
        """
        with self.transaction() as conn:
            # Verificar que el usuario existe
            user = self.get_user(user_id)
            if not user:
                return False

            # Verificar conflictos si se actualizan username o email
            updates = []
            params = []

            if username is not None and username != user['username']:
                # Verificar que no existe otro usuario con este username
                existing = self._execute_single(
                    conn,
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (username, user_id)
                )
                if existing:
                    raise ValueError("Nombre de usuario ya existe")

                updates.append("username = ?")
                params.append(username)

            if email is not None and email != user['email']:
                # Verificar que no existe otro usuario con este email
                existing = self._execute_single(
                    conn,
                    "SELECT id FROM users WHERE email = ? AND id != ?",
                    (email, user_id)
                )
                if existing:
                    raise ValueError("Email ya existe")

                updates.append("email = ?")
                params.append(email)

            if not updates:
                return True  # Nada que actualizar

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)

            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            affected = self._execute_update_delete(conn, query, tuple(params))

            logger.info(f"Usuario actualizado: ID {user_id}")
            return affected > 0

    def delete_user(self, user_id: int) -> bool:
        """
        Elimina un usuario y todas sus configuraciones.

        Args:
            user_id: ID del usuario a eliminar

        Returns:
            bool: True si se eliminó, False si no existía

        Note:
            Las claves foráneas eliminarán automáticamente las configuraciones relacionadas
        """
        with self.transaction() as conn:
            affected = self._execute_update_delete(
                conn,
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )

            if affected > 0:
                logger.info(f"Usuario eliminado: ID {user_id}")
            return affected > 0

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Lista todos los usuarios.

        Returns:
            List[Dict[str, Any]]: Lista de usuarios
        """
        with self._get_connection() as conn:
            return self._execute_query(
                conn,
                "SELECT * FROM users ORDER BY created_at DESC"
            )

    # ==================== MÉTODOS PARA CONFIGURACIONES ====================

    def _create_default_settings_for_user(self, conn: sqlite3.Connection, user_id: int) -> None:
        """Crea configuraciones por defecto para un nuevo usuario."""
        # Configuraciones generales
        conn.execute("""
            INSERT INTO general_settings (user_id, appearance, accent_color, font_size, send_with_enter, ui_language, spoken_language, voice)
            VALUES (?, 'system', 'blue', 'medium', 1, 'es', 'es', 'ember')
        """, (user_id,))

        # Notificaciones
        conn.execute("""
            INSERT INTO notification_settings (user_id, mute_all, responses_app, responses_email, tasks_app, tasks_email, projects_app, projects_email, recommendations_app, recommendations_email)
            VALUES (?, 0, 1, 1, 1, 0, 1, 1, 0, 0)
        """, (user_id,))

        # Personalización
        conn.execute("""
            INSERT INTO personalization_settings (user_id, enable_personalization, custom_instructions, base_style_tone, nickname, occupation, more_about_you, reference_chat_history)
            VALUES (?, 1, 0, 'witty', '', '', '', 1)
        """, (user_id,))

        # Memoria
        conn.execute("""
            INSERT INTO memory_settings (user_id, memory_used, max_memory_items, reference_memories)
            VALUES (?, 0, 256, 1)
        """, (user_id,))

        # Aplicaciones y conectores
        conn.execute("""
            INSERT INTO apps_connectors_settings (user_id, google_drive, dropbox, slack, discord, webhook_url)
            VALUES (?, 0, 0, 0, 0, '')
        """, (user_id,))

        # Controles de datos
        conn.execute("""
            INSERT INTO data_controls_settings (user_id, data_collection, analytics, data_retention, export_data)
            VALUES (?, 1, 1, '1year', 0)
        """, (user_id,))

        # Seguridad
        conn.execute("""
            INSERT INTO security_settings (user_id, two_factor, session_timeout, login_alerts, password_change_pending, password_last_changed)
            VALUES (?, 0, '30min', 1, 0, NULL)
        """, (user_id,))

        # Controles parentales
        conn.execute("""
            INSERT INTO parental_controls_settings (user_id, parental_control, content_filter, time_limits, max_time_per_day, parental_pin_hash)
            VALUES (?, 0, 'moderate', 0, '2hours', NULL)
        """, (user_id,))

        # Cuenta
        conn.execute("""
            INSERT INTO account_settings (user_id, name, email, phone, bio, sessions_completed, tokens_used)
            VALUES (?, '', '', '', '', 0, 0)
        """, (user_id,))

    def get_user_settings(self, user_id: int) -> Optional[SettingsContainer]:
        """
        Obtiene todas las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[SettingsContainer]: Contenedor con todas las configuraciones o None si no existe
        """
        with self._get_connection() as conn:
            # Verificar que el usuario existe
            user = self.get_user(user_id)
            if not user:
                return None

            # Obtener todas las configuraciones
            settings_data = {}

            # Configuraciones generales
            general = self._execute_single(
                conn,
                "SELECT * FROM general_settings WHERE user_id = ?",
                (user_id,)
            )
            if general:
                settings_data['general'] = {
                    'appearance': general['appearance'],
                    'accent_color': general['accent_color'],
                    'font_size': general['font_size'],
                    'send_with_enter': bool(general['send_with_enter']),
                    'ui_language': general['ui_language'],
                    'spoken_language': general['spoken_language'],
                    'voice': general['voice'],
                    'created_at': general['created_at'],
                    'updated_at': general['updated_at'],
                    'version': general['version']
                }

            # Notificaciones
            notifications = self._execute_single(
                conn,
                "SELECT * FROM notification_settings WHERE user_id = ?",
                (user_id,)
            )
            if notifications:
                settings_data['notifications'] = {
                    'mute_all': bool(notifications['mute_all']),
                    'responses_app': bool(notifications['responses_app']),
                    'responses_email': bool(notifications['responses_email']),
                    'tasks_app': bool(notifications['tasks_app']),
                    'tasks_email': bool(notifications['tasks_email']),
                    'projects_app': bool(notifications['projects_app']),
                    'projects_email': bool(notifications['projects_email']),
                    'recommendations_app': bool(notifications['recommendations_app']),
                    'recommendations_email': bool(notifications['recommendations_email']),
                    'created_at': notifications['created_at'],
                    'updated_at': notifications['updated_at'],
                    'version': notifications['version']
                }

            # Personalización
            personalization = self._execute_single(
                conn,
                "SELECT * FROM personalization_settings WHERE user_id = ?",
                (user_id,)
            )
            if personalization:
                settings_data['personalization'] = {
                    'enable_personalization': bool(personalization['enable_personalization']),
                    'custom_instructions': bool(personalization['custom_instructions']),
                    'base_style_tone': personalization['base_style_tone'],
                    'nickname': personalization['nickname'],
                    'occupation': personalization['occupation'],
                    'more_about_you': personalization['more_about_you'],
                    'reference_chat_history': bool(personalization['reference_chat_history']),
                    'created_at': personalization['created_at'],
                    'updated_at': personalization['updated_at'],
                    'version': personalization['version']
                }

            # Memoria
            memory = self._execute_single(
                conn,
                "SELECT * FROM memory_settings WHERE user_id = ?",
                (user_id,)
            )
            if memory:
                settings_data['memory'] = {
                    'memory_used': memory['memory_used'],
                    'max_memory_items': memory['max_memory_items'],
                    'reference_memories': bool(memory['reference_memories']),
                    'created_at': memory['created_at'],
                    'updated_at': memory['updated_at'],
                    'version': memory['version']
                }

            # Aplicaciones y conectores
            apps_connectors = self._execute_single(
                conn,
                "SELECT * FROM apps_connectors_settings WHERE user_id = ?",
                (user_id,)
            )
            if apps_connectors:
                settings_data['apps_connectors'] = {
                    'google_drive': bool(apps_connectors['google_drive']),
                    'dropbox': bool(apps_connectors['dropbox']),
                    'slack': bool(apps_connectors['slack']),
                    'discord': bool(apps_connectors['discord']),
                    'webhook_url': apps_connectors['webhook_url'],
                    'created_at': apps_connectors['created_at'],
                    'updated_at': apps_connectors['updated_at'],
                    'version': apps_connectors['version']
                }

            # Controles de datos
            data_controls = self._execute_single(
                conn,
                "SELECT * FROM data_controls_settings WHERE user_id = ?",
                (user_id,)
            )
            if data_controls:
                settings_data['data_controls'] = {
                    'data_collection': bool(data_controls['data_collection']),
                    'analytics': bool(data_controls['analytics']),
                    'data_retention': data_controls['data_retention'],
                    'export_data': bool(data_controls['export_data']),
                    'created_at': data_controls['created_at'],
                    'updated_at': data_controls['updated_at'],
                    'version': data_controls['version']
                }

            # Seguridad
            security = self._execute_single(
                conn,
                "SELECT * FROM security_settings WHERE user_id = ?",
                (user_id,)
            )
            if security:
                settings_data['security'] = {
                    'two_factor': bool(security['two_factor']),
                    'session_timeout': security['session_timeout'],
                    'login_alerts': bool(security['login_alerts']),
                    'password_change_pending': bool(security['password_change_pending']),
                    'password_last_changed': security['password_last_changed'],
                    'created_at': security['created_at'],
                    'updated_at': security['updated_at'],
                    'version': security['version']
                }

            # Controles parentales
            parental_controls = self._execute_single(
                conn,
                "SELECT * FROM parental_controls_settings WHERE user_id = ?",
                (user_id,)
            )
            if parental_controls:
                settings_data['parental_controls'] = {
                    'parental_control': bool(parental_controls['parental_control']),
                    'content_filter': parental_controls['content_filter'],
                    'time_limits': bool(parental_controls['time_limits']),
                    'max_time_per_day': parental_controls['max_time_per_day'],
                    'parental_pin_hash': parental_controls['parental_pin_hash'],
                    'created_at': parental_controls['created_at'],
                    'updated_at': parental_controls['updated_at'],
                    'version': parental_controls['version']
                }

            # Cuenta
            account = self._execute_single(
                conn,
                "SELECT * FROM account_settings WHERE user_id = ?",
                (user_id,)
            )
            if account:
                settings_data['account'] = {
                    'name': account['name'],
                    'email': account['email'],
                    'phone': account['phone'],
                    'bio': account['bio'],
                    'sessions_completed': account['sessions_completed'],
                    'tokens_used': account['tokens_used'],
                    'created_at': account['created_at'],
                    'updated_at': account['updated_at'],
                    'version': account['version']
                }

            # Crear el contenedor de configuraciones
            container = SettingsContainer()
            for category, data in settings_data.items():
                if hasattr(container, category):
                    category_class = type(getattr(container, category))
                    setattr(container, category, category_class(**data))

            return container

    def update_user_settings(self, user_id: int, settings: SettingsContainer, validate: bool = True) -> bool:
        """
        Actualiza todas las configuraciones de un usuario.

        Args:
            user_id: ID del usuario
            settings: Contenedor con las nuevas configuraciones
            validate: Si se debe validar antes de guardar

        Returns:
            bool: True si se actualizaron, False si el usuario no existe

        Raises:
            ValueError: Si la validación falla
        """
        # Validar si se solicita
        if validate:
            errors = validate_settings(settings)
            if errors:
                raise ValueError(f"Errores de validación: {errors}")

        with self.transaction() as conn:
            # Verificar que el usuario existe
            user = self.get_user(user_id)
            if not user:
                return False

            # Actualizar cada categoría
            self._update_general_settings(conn, user_id, settings.general)
            self._update_notification_settings(conn, user_id, settings.notifications)
            self._update_personalization_settings(conn, user_id, settings.personalization)
            self._update_memory_settings(conn, user_id, settings.memory)
            self._update_apps_connectors_settings(conn, user_id, settings.apps_connectors)
            self._update_data_controls_settings(conn, user_id, settings.data_controls)
            self._update_security_settings(conn, user_id, settings.security)
            self._update_parental_controls_settings(conn, user_id, settings.parental_controls)
            self._update_account_settings(conn, user_id, settings.account)

            logger.info(f"Configuraciones actualizadas para usuario ID: {user_id}")
            return True

    def update_category_settings(self, user_id: int, category: str, settings: Dict[str, Any], validate: bool = True) -> bool:
        """
        Actualiza una categoría específica de configuraciones.

        Args:
            user_id: ID del usuario
            category: Nombre de la categoría ('general', 'notifications', etc.)
            settings: Diccionario con las configuraciones a actualizar
            validate: Si se debe validar antes de guardar

        Returns:
            bool: True si se actualizaron, False si el usuario no existe

        Raises:
            ValueError: Si la categoría no existe o la validación falla
        """
        # Obtener configuraciones actuales
        current_settings = self.get_user_settings(user_id)
        if not current_settings:
            return False

        # Actualizar la categoría específica
        if not hasattr(current_settings, category):
            raise ValueError(f"Categoría '{category}' no existe")

        category_obj = getattr(current_settings, category)
        for key, value in settings.items():
            if hasattr(category_obj, key):
                setattr(category_obj, key, value)
            else:
                raise ValueError(f"Campo '{key}' no existe en la categoría '{category}'")

        category_obj.update_timestamp()
        current_settings.update_timestamp()

        # Validar si se solicita
        if validate:
            errors = current_settings.validate()
            if errors:
                raise ValueError(f"Errores de validación: {errors}")

        # Actualizar en base de datos
        with self.transaction() as conn:
            update_method = getattr(self, f"_update_{category}_settings")
            update_method(conn, user_id, category_obj)

            logger.info(f"Categoría '{category}' actualizada para usuario ID: {user_id}")
            return True

    # ==================== MÉTODOS DE ACTUALIZACIÓN POR CATEGORÍA ====================

    def _update_general_settings(self, conn: sqlite3.Connection, user_id: int, settings: GeneralSettings) -> None:
        """Actualiza configuraciones generales."""
        conn.execute("""
            UPDATE general_settings SET
                appearance = ?, accent_color = ?, font_size = ?, send_with_enter = ?,
                ui_language = ?, spoken_language = ?, voice = ?, updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.appearance, settings.accent_color, settings.font_size, settings.send_with_enter,
            settings.ui_language, settings.spoken_language, settings.voice, settings.version, user_id
        ))

    def _update_notification_settings(self, conn: sqlite3.Connection, user_id: int, settings: NotificationSettings) -> None:
        """Actualiza configuraciones de notificaciones."""
        conn.execute("""
            UPDATE notification_settings SET
                mute_all = ?, responses_app = ?, responses_email = ?, tasks_app = ?, tasks_email = ?,
                projects_app = ?, projects_email = ?, recommendations_app = ?, recommendations_email = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.mute_all, settings.responses_app, settings.responses_email, settings.tasks_app, settings.tasks_email,
            settings.projects_app, settings.projects_email, settings.recommendations_app, settings.recommendations_email,
            settings.version, user_id
        ))

    def _update_notifications_settings(self, conn: sqlite3.Connection, user_id: int, settings: NotificationSettings) -> None:
        """Alias para compatibilidad con categoría 'notifications'."""
        self._update_notification_settings(conn, user_id, settings)

    def _update_personalization_settings(self, conn: sqlite3.Connection, user_id: int, settings: PersonalizationSettings) -> None:
        """Actualiza configuraciones de personalización."""
        conn.execute("""
            UPDATE personalization_settings SET
                enable_personalization = ?, custom_instructions = ?, base_style_tone = ?,
                nickname = ?, occupation = ?, more_about_you = ?, reference_chat_history = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.enable_personalization, settings.custom_instructions, settings.base_style_tone,
            settings.nickname, settings.occupation, settings.more_about_you, settings.reference_chat_history,
            settings.version, user_id
        ))

    def _update_memory_settings(self, conn: sqlite3.Connection, user_id: int, settings: MemorySettings) -> None:
        """Actualiza configuraciones de memoria."""
        conn.execute("""
            UPDATE memory_settings SET
                memory_used = ?, max_memory_items = ?, reference_memories = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.memory_used, settings.max_memory_items, settings.reference_memories,
            settings.version, user_id
        ))

    def _update_apps_connectors_settings(self, conn: sqlite3.Connection, user_id: int, settings: AppsConnectorsSettings) -> None:
        """Actualiza configuraciones de aplicaciones y conectores."""
        conn.execute("""
            UPDATE apps_connectors_settings SET
                google_drive = ?, dropbox = ?, slack = ?, discord = ?, webhook_url = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.google_drive, settings.dropbox, settings.slack, settings.discord, settings.webhook_url,
            settings.version, user_id
        ))

    def _update_data_controls_settings(self, conn: sqlite3.Connection, user_id: int, settings: DataControlsSettings) -> None:
        """Actualiza configuraciones de controles de datos."""
        conn.execute("""
            UPDATE data_controls_settings SET
                data_collection = ?, analytics = ?, data_retention = ?, export_data = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.data_collection, settings.analytics, settings.data_retention, settings.export_data,
            settings.version, user_id
        ))

    def _update_security_settings(self, conn: sqlite3.Connection, user_id: int, settings: SecuritySettings) -> None:
        """Actualiza configuraciones de seguridad."""
        conn.execute("""
            UPDATE security_settings SET
                two_factor = ?, session_timeout = ?, login_alerts = ?, password_change_pending = ?, password_last_changed = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.two_factor, settings.session_timeout, settings.login_alerts, settings.password_change_pending, settings.password_last_changed,
            settings.version, user_id
        ))

    def _update_parental_controls_settings(self, conn: sqlite3.Connection, user_id: int, settings: ParentalControlsSettings) -> None:
        """Actualiza configuraciones de controles parentales."""
        conn.execute("""
            UPDATE parental_controls_settings SET
                parental_control = ?, content_filter = ?, time_limits = ?, max_time_per_day = ?, parental_pin_hash = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.parental_control, settings.content_filter, settings.time_limits, settings.max_time_per_day, settings.parental_pin_hash,
            settings.version, user_id
        ))

    def _update_account_settings(self, conn: sqlite3.Connection, user_id: int, settings: AccountSettings) -> None:
        """Actualiza configuraciones de cuenta."""
        conn.execute("""
            UPDATE account_settings SET
                name = ?, email = ?, phone = ?, bio = ?, sessions_completed = ?, tokens_used = ?,
                updated_at = CURRENT_TIMESTAMP, version = ?
            WHERE user_id = ?
        """, (
            settings.name, settings.email, settings.phone, settings.bio, settings.sessions_completed, settings.tokens_used,
            settings.version, user_id
        ))

    # ==================== MÉTODOS DE UTILIDAD ====================

    def reset_user_settings_to_default(self, user_id: int) -> bool:
        """
        Resetea todas las configuraciones de un usuario a valores por defecto.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si se reseteo, False si el usuario no existe
        """
        default_settings = create_default_settings()

        with self.transaction() as conn:
            # Verificar que el usuario existe
            user = self.get_user(user_id)
            if not user:
                return False

            # Eliminar configuraciones actuales
            tables = [
                'general_settings', 'notification_settings', 'personalization_settings',
                'memory_settings', 'apps_connectors_settings', 'data_controls_settings',
                'security_settings', 'parental_controls_settings', 'account_settings'
            ]

            for table in tables:
                conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))

            # Crear configuraciones por defecto
            self._create_default_settings_for_user(conn, user_id)

            logger.info(f"Configuraciones reseteadas a valores por defecto para usuario ID: {user_id}")
            return True

    def export_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Exporta todas las configuraciones de un usuario como diccionario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Dict[str, Any]]: Configuraciones exportadas o None si el usuario no existe
        """
        settings = self.get_user_settings(user_id)
        if not settings:
            return None

        return settings.to_dict()

    def import_user_settings(self, user_id: int, settings_data: Dict[str, Any], validate: bool = True) -> bool:
        """
        Importa configuraciones para un usuario desde un diccionario.

        Args:
            user_id: ID del usuario
            settings_data: Diccionario con las configuraciones a importar
            validate: Si se debe validar antes de importar

        Returns:
            bool: True si se importaron, False si el usuario no existe

        Raises:
            ValueError: Si los datos son inválidos o la validación falla
        """
        try:
            settings = load_settings_from_dict(settings_data)
        except Exception as e:
            raise ValueError(f"Error al cargar configuraciones: {e}")

        return self.update_user_settings(user_id, settings, validate)

    def get_settings_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resumen de las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Dict[str, Any]]: Resumen de configuraciones o None si el usuario no existe
        """
        settings = self.get_user_settings(user_id)
        if not settings:
            return None

        return {
            'user_id': user_id,
            'last_updated': settings.updated_at.isoformat(),
            'version': settings.version,
            'categories': {
                'general': {
                    'appearance': settings.general.appearance,
                    'accent_color': settings.general.accent_color,
                    'ui_language': settings.general.ui_language
                },
                'notifications': {
                    'mute_all': settings.notifications.mute_all,
                    'responses_app': settings.notifications.responses_app,
                    'tasks_app': settings.notifications.tasks_app
                },
                'security': {
                    'two_factor': settings.security.two_factor,
                    'session_timeout': settings.security.session_timeout,
                    'password_last_changed': settings.security.password_last_changed.isoformat() if settings.security.password_last_changed else None
                },
                'memory': {
                    'memory_used': settings.memory.memory_used,
                    'max_memory_items': settings.memory.max_memory_items
                }
            }
        }

    def validate_user_settings(self, user_id: int) -> List[str]:
        """
        Valida las configuraciones actuales de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[str]: Lista de errores de validación
        """
        settings = self.get_user_settings(user_id)
        if not settings:
            return ["Usuario no encontrado"]

        return validate_settings(settings)
