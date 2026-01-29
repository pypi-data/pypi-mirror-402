"""
Repositorio SQLAlchemy para configuraciones de usuario de AILOOS
================================================================

Este módulo proporciona una capa de abstracción completa para acceder a la base de datos
PostgreSQL del coordinador, incluyendo métodos CRUD para todas las categorías de configuraciones,
manejo de transacciones y validación de datos.
"""

import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from .models import (
    SettingsContainer, GeneralSettings, NotificationSettings, PersonalizationSettings,
    MemorySettings, AppsConnectorsSettings, DataControlsSettings, SecuritySettings,
    ParentalControlsSettings, AccountSettings, create_default_settings, validate_settings,
    load_settings_from_dict
)
from .models_sqlalchemy import (
    User, GeneralSettings as GeneralSettingsDB, NotificationSettings as NotificationSettingsDB,
    PersonalizationSettings as PersonalizationSettingsDB, MemorySettings as MemorySettingsDB,
    AppsConnectorsSettings as AppsConnectorsSettingsDB, DataControlsSettings as DataControlsSettingsDB,
    SecuritySettings as SecuritySettingsDB, ParentalControlsSettings as ParentalControlsSettingsDB,
    AccountSettings as AccountSettingsDB
)

# Configurar logging
logger = logging.getLogger(__name__)


class SettingsRepositorySQLAlchemy:
    """
    Repositorio para gestionar configuraciones de usuario en base de datos PostgreSQL.

    Proporciona una interfaz completa para operaciones CRUD sobre todas las categorías
    de configuraciones, con soporte para transacciones y validación de datos.
    """

    def __init__(self, db_session_factory):
        """
        Inicializa el repositorio con una fábrica de sesiones de base de datos.

        Args:
            db_session_factory: Función que retorna una sesión de SQLAlchemy
        """
        self.db_session_factory = db_session_factory
        logger.info("Repositorio SQLAlchemy de configuraciones inicializado")

    @contextmanager
    def _get_session(self):
        """
        Context manager para obtener una sesión de base de datos.

        Yields:
            Session: Sesión de SQLAlchemy
        """
        session = self.db_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()

    @contextmanager
    def transaction(self):
        """
        Context manager para manejar transacciones.

        Yields:
            Session: Sesión en modo transacción
        """
        with self._get_session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Error en transacción: {e}")
                raise

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
        """
        with self.transaction() as session:
            # Verificar si ya existe
            existing = session.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            if existing:
                raise ValueError("Usuario o email ya existen")

            user = User(username=username, email=email)
            session.add(user)
            session.flush()  # Para obtener el ID

            # Crear configuraciones por defecto para el usuario
            self._create_default_settings_for_user(session, user.id)

            logger.info(f"Usuario creado: {username} (ID: {user.id})")
            return user.id

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por ID.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por nombre de usuario.

        Args:
            username: Nombre de usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por email.

        Args:
            email: Email del usuario

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si no existe
        """
        with self._get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            return None

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
        with self.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            # Verificar conflictos si se actualizan username o email
            if username and username != user.username:
                existing = session.query(User).filter(
                    and_(User.username == username, User.id != user_id)
                ).first()
                if existing:
                    raise ValueError("Nombre de usuario ya existe")

            if email and email != user.email:
                existing = session.query(User).filter(
                    and_(User.email == email, User.id != user_id)
                ).first()
                if existing:
                    raise ValueError("Email ya existe")

            # Actualizar campos
            if username:
                user.username = username
            if email:
                user.email = email

            logger.info(f"Usuario actualizado: ID {user_id}")
            return True

    def delete_user(self, user_id: int) -> bool:
        """
        Elimina un usuario y todas sus configuraciones.

        Args:
            user_id: ID del usuario a eliminar

        Returns:
            bool: True si se eliminó, False si no existía

        Note:
            Las relaciones con cascade eliminarán automáticamente las configuraciones relacionadas
        """
        with self.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                logger.info(f"Usuario eliminado: ID {user_id}")
                return True
            return False

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Lista todos los usuarios.

        Returns:
            List[Dict[str, Any]]: Lista de usuarios
        """
        with self._get_session() as session:
            users = session.query(User).order_by(User.created_at.desc()).all()
            return [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            } for user in users]

    # ==================== MÉTODOS PARA CONFIGURACIONES ====================

    def _create_default_settings_for_user(self, session: Session, user_id: int) -> None:
        """Crea configuraciones por defecto para un nuevo usuario."""
        # Configuraciones generales
        general = GeneralSettingsDB(user_id=user_id)
        session.add(general)

        # Notificaciones
        notifications = NotificationSettingsDB(user_id=user_id)
        session.add(notifications)

        # Personalización
        personalization = PersonalizationSettingsDB(user_id=user_id)
        session.add(personalization)

        # Memoria
        memory = MemorySettingsDB(user_id=user_id)
        session.add(memory)

        # Aplicaciones y conectores
        apps_connectors = AppsConnectorsSettingsDB(user_id=user_id)
        session.add(apps_connectors)

        # Controles de datos
        data_controls = DataControlsSettingsDB(user_id=user_id)
        session.add(data_controls)

        # Seguridad
        security = SecuritySettingsDB(user_id=user_id)
        session.add(security)

        # Controles parentales
        parental_controls = ParentalControlsSettingsDB(user_id=user_id)
        session.add(parental_controls)

        # Cuenta
        account = AccountSettingsDB(user_id=user_id)
        session.add(account)

    def get_user_settings(self, user_id: int) -> Optional[SettingsContainer]:
        """
        Obtiene todas las configuraciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[SettingsContainer]: Contenedor con todas las configuraciones o None si no existe
        """
        with self._get_session() as session:
            # Verificar que el usuario existe
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Obtener todas las configuraciones con joinedload para optimización
            user_with_settings = session.query(User).options(
                joinedload(User.general_settings),
                joinedload(User.notification_settings),
                joinedload(User.personalization_settings),
                joinedload(User.memory_settings),
                joinedload(User.apps_connectors_settings),
                joinedload(User.data_controls_settings),
                joinedload(User.security_settings),
                joinedload(User.parental_controls_settings),
                joinedload(User.account_settings)
            ).filter(User.id == user_id).first()

            if not user_with_settings:
                return None

            # Convertir a diccionario de configuraciones
            settings_data = {}

            # Configuraciones generales
            if user_with_settings.general_settings:
                gs = user_with_settings.general_settings
                settings_data['general'] = {
                    'appearance': gs.appearance,
                    'accent_color': gs.accent_color,
                    'font_size': gs.font_size,
                    'send_with_enter': gs.send_with_enter,
                    'ui_language': gs.ui_language,
                    'spoken_language': gs.spoken_language,
                    'voice': gs.voice,
                    'created_at': gs.created_at.isoformat(),
                    'updated_at': gs.updated_at.isoformat(),
                    'version': gs.version
                }

            # Notificaciones
            if user_with_settings.notification_settings:
                ns = user_with_settings.notification_settings
                settings_data['notifications'] = {
                    'mute_all': ns.mute_all,
                    'responses_app': ns.responses_app,
                    'responses_email': ns.responses_email,
                    'tasks_app': ns.tasks_app,
                    'tasks_email': ns.tasks_email,
                    'projects_app': ns.projects_app,
                    'projects_email': ns.projects_email,
                    'recommendations_app': ns.recommendations_app,
                    'recommendations_email': ns.recommendations_email,
                    'created_at': ns.created_at.isoformat(),
                    'updated_at': ns.updated_at.isoformat(),
                    'version': ns.version
                }

            # Personalización
            if user_with_settings.personalization_settings:
                ps = user_with_settings.personalization_settings
                settings_data['personalization'] = {
                    'enable_personalization': ps.enable_personalization,
                    'custom_instructions': ps.custom_instructions,
                    'base_style_tone': ps.base_style_tone,
                    'nickname': ps.nickname,
                    'occupation': ps.occupation,
                    'more_about_you': ps.more_about_you,
                    'reference_chat_history': ps.reference_chat_history,
                    'created_at': ps.created_at.isoformat(),
                    'updated_at': ps.updated_at.isoformat(),
                    'version': ps.version
                }

            # Memoria
            if user_with_settings.memory_settings:
                ms = user_with_settings.memory_settings
                settings_data['memory'] = {
                    'memory_used': ms.memory_used,
                    'max_memory_items': ms.max_memory_items,
                    'reference_memories': ms.reference_memories,
                    'created_at': ms.created_at.isoformat(),
                    'updated_at': ms.updated_at.isoformat(),
                    'version': ms.version
                }

            # Aplicaciones y conectores
            if user_with_settings.apps_connectors_settings:
                acs = user_with_settings.apps_connectors_settings
                settings_data['apps_connectors'] = {
                    'google_drive': acs.google_drive,
                    'dropbox': acs.dropbox,
                    'slack': acs.slack,
                    'discord': acs.discord,
                    'webhook_url': acs.webhook_url,
                    'created_at': acs.created_at.isoformat(),
                    'updated_at': acs.updated_at.isoformat(),
                    'version': acs.version
                }

            # Controles de datos
            if user_with_settings.data_controls_settings:
                dcs = user_with_settings.data_controls_settings
                settings_data['data_controls'] = {
                    'data_collection': dcs.data_collection,
                    'analytics': dcs.analytics,
                    'data_retention': dcs.data_retention,
                    'export_data': dcs.export_data,
                    'created_at': dcs.created_at.isoformat(),
                    'updated_at': dcs.updated_at.isoformat(),
                    'version': dcs.version
                }

            # Seguridad
            if user_with_settings.security_settings:
                ss = user_with_settings.security_settings
                settings_data['security'] = {
                    'two_factor': ss.two_factor,
                    'session_timeout': ss.session_timeout,
                    'login_alerts': ss.login_alerts,
                    'password_change_pending': ss.password_change_pending,
                    'password_last_changed': ss.password_last_changed.isoformat() if ss.password_last_changed else None,
                    'created_at': ss.created_at.isoformat(),
                    'updated_at': ss.updated_at.isoformat(),
                    'version': ss.version
                }

            # Controles parentales
            if user_with_settings.parental_controls_settings:
                pcs = user_with_settings.parental_controls_settings
                settings_data['parental_controls'] = {
                    'parental_control': pcs.parental_control,
                    'content_filter': pcs.content_filter,
                    'time_limits': pcs.time_limits,
                    'max_time_per_day': pcs.max_time_per_day,
                    'parental_pin_hash': pcs.parental_pin_hash,
                    'created_at': pcs.created_at.isoformat(),
                    'updated_at': pcs.updated_at.isoformat(),
                    'version': pcs.version
                }

            # Cuenta
            if user_with_settings.account_settings:
                accs = user_with_settings.account_settings
                settings_data['account'] = {
                    'name': accs.name,
                    'email': accs.email,
                    'phone': accs.phone,
                    'bio': accs.bio,
                    'sessions_completed': accs.sessions_completed,
                    'tokens_used': accs.tokens_used,
                    'created_at': accs.created_at.isoformat(),
                    'updated_at': accs.updated_at.isoformat(),
                    'version': accs.version
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
        if validate:
            errors = validate_settings(settings)
            if errors:
                raise ValueError(f"Errores de validación: {errors}")

        with self.transaction() as session:
            # Verificar que el usuario existe
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            # Actualizar cada categoría
            self._update_general_settings(session, user_id, settings.general)
            self._update_notification_settings(session, user_id, settings.notifications)
            self._update_personalization_settings(session, user_id, settings.personalization)
            self._update_memory_settings(session, user_id, settings.memory)
            self._update_apps_connectors_settings(session, user_id, settings.apps_connectors)
            self._update_data_controls_settings(session, user_id, settings.data_controls)
            self._update_security_settings(session, user_id, settings.security)
            self._update_parental_controls_settings(session, user_id, settings.parental_controls)
            self._update_account_settings(session, user_id, settings.account)

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
        with self.transaction() as session:
            update_method = getattr(self, f"_update_{category}_settings")
            update_method(session, user_id, category_obj)

            logger.info(f"Categoría '{category}' actualizada para usuario ID: {user_id}")
            return True

    # ==================== MÉTODOS DE ACTUALIZACIÓN POR CATEGORÍA ====================

    def _update_general_settings(self, session: Session, user_id: int, settings: GeneralSettings) -> None:
        """Actualiza configuraciones generales."""
        gs = session.query(GeneralSettingsDB).filter(GeneralSettingsDB.user_id == user_id).first()
        if gs:
            gs.appearance = settings.appearance
            gs.accent_color = settings.accent_color
            gs.font_size = settings.font_size
            gs.send_with_enter = settings.send_with_enter
            gs.ui_language = settings.ui_language
            gs.spoken_language = settings.spoken_language
            gs.voice = settings.voice
            gs.version = settings.version
        else:
            gs = GeneralSettingsDB(
                user_id=user_id,
                appearance=settings.appearance,
                accent_color=settings.accent_color,
                font_size=settings.font_size,
                send_with_enter=settings.send_with_enter,
                ui_language=settings.ui_language,
                spoken_language=settings.spoken_language,
                voice=settings.voice,
                version=settings.version
            )
            session.add(gs)

    def _update_notification_settings(self, session: Session, user_id: int, settings: NotificationSettings) -> None:
        """Actualiza configuraciones de notificaciones."""
        ns = session.query(NotificationSettingsDB).filter(NotificationSettingsDB.user_id == user_id).first()
        if ns:
            ns.mute_all = settings.mute_all
            ns.responses_app = settings.responses_app
            ns.responses_email = settings.responses_email
            ns.tasks_app = settings.tasks_app
            ns.tasks_email = settings.tasks_email
            ns.projects_app = settings.projects_app
            ns.projects_email = settings.projects_email
            ns.recommendations_app = settings.recommendations_app
            ns.recommendations_email = settings.recommendations_email
            ns.version = settings.version
        else:
            ns = NotificationSettingsDB(
                user_id=user_id,
                mute_all=settings.mute_all,
                responses_app=settings.responses_app,
                responses_email=settings.responses_email,
                tasks_app=settings.tasks_app,
                tasks_email=settings.tasks_email,
                projects_app=settings.projects_app,
                projects_email=settings.projects_email,
                recommendations_app=settings.recommendations_app,
                recommendations_email=settings.recommendations_email,
                version=settings.version
            )
            session.add(ns)

    def _update_personalization_settings(self, session: Session, user_id: int, settings: PersonalizationSettings) -> None:
        """Actualiza configuraciones de personalización."""
        ps = session.query(PersonalizationSettingsDB).filter(PersonalizationSettingsDB.user_id == user_id).first()
        if ps:
            ps.enable_personalization = settings.enable_personalization
            ps.custom_instructions = settings.custom_instructions
            ps.base_style_tone = settings.base_style_tone
            ps.nickname = settings.nickname
            ps.occupation = settings.occupation
            ps.more_about_you = settings.more_about_you
            ps.reference_chat_history = settings.reference_chat_history
            ps.version = settings.version
        else:
            ps = PersonalizationSettingsDB(
                user_id=user_id,
                enable_personalization=settings.enable_personalization,
                custom_instructions=settings.custom_instructions,
                base_style_tone=settings.base_style_tone,
                nickname=settings.nickname,
                occupation=settings.occupation,
                more_about_you=settings.more_about_you,
                reference_chat_history=settings.reference_chat_history,
                version=settings.version
            )
            session.add(ps)

    def _update_memory_settings(self, session: Session, user_id: int, settings: MemorySettings) -> None:
        """Actualiza configuraciones de memoria."""
        ms = session.query(MemorySettingsDB).filter(MemorySettingsDB.user_id == user_id).first()
        if ms:
            ms.memory_used = settings.memory_used
            ms.max_memory_items = settings.max_memory_items
            ms.reference_memories = settings.reference_memories
            ms.version = settings.version
        else:
            ms = MemorySettingsDB(
                user_id=user_id,
                memory_used=settings.memory_used,
                max_memory_items=settings.max_memory_items,
                reference_memories=settings.reference_memories,
                version=settings.version
            )
            session.add(ms)

    def _update_apps_connectors_settings(self, session: Session, user_id: int, settings: AppsConnectorsSettings) -> None:
        """Actualiza configuraciones de aplicaciones y conectores."""
        acs = session.query(AppsConnectorsSettingsDB).filter(AppsConnectorsSettingsDB.user_id == user_id).first()
        if acs:
            acs.google_drive = settings.google_drive
            acs.dropbox = settings.dropbox
            acs.slack = settings.slack
            acs.discord = settings.discord
            acs.webhook_url = settings.webhook_url
            acs.version = settings.version
        else:
            acs = AppsConnectorsSettingsDB(
                user_id=user_id,
                google_drive=settings.google_drive,
                dropbox=settings.dropbox,
                slack=settings.slack,
                discord=settings.discord,
                webhook_url=settings.webhook_url,
                version=settings.version
            )
            session.add(acs)

    def _update_data_controls_settings(self, session: Session, user_id: int, settings: DataControlsSettings) -> None:
        """Actualiza configuraciones de controles de datos."""
        dcs = session.query(DataControlsSettingsDB).filter(DataControlsSettingsDB.user_id == user_id).first()
        if dcs:
            dcs.data_collection = settings.data_collection
            dcs.analytics = settings.analytics
            dcs.data_retention = settings.data_retention
            dcs.export_data = settings.export_data
            dcs.version = settings.version
        else:
            dcs = DataControlsSettingsDB(
                user_id=user_id,
                data_collection=settings.data_collection,
                analytics=settings.analytics,
                data_retention=settings.data_retention,
                export_data=settings.export_data,
                version=settings.version
            )
            session.add(dcs)

    def _update_security_settings(self, session: Session, user_id: int, settings: SecuritySettings) -> None:
        """Actualiza configuraciones de seguridad."""
        ss = session.query(SecuritySettingsDB).filter(SecuritySettingsDB.user_id == user_id).first()
        if ss:
            ss.two_factor = settings.two_factor
            ss.session_timeout = settings.session_timeout
            ss.login_alerts = settings.login_alerts
            ss.password_change_pending = settings.password_change_pending
            ss.password_last_changed = settings.password_last_changed
            ss.version = settings.version
        else:
            ss = SecuritySettingsDB(
                user_id=user_id,
                two_factor=settings.two_factor,
                session_timeout=settings.session_timeout,
                login_alerts=settings.login_alerts,
                password_change_pending=settings.password_change_pending,
                password_last_changed=settings.password_last_changed,
                version=settings.version
            )
            session.add(ss)

    def _update_parental_controls_settings(self, session: Session, user_id: int, settings: ParentalControlsSettings) -> None:
        """Actualiza configuraciones de controles parentales."""
        pcs = session.query(ParentalControlsSettingsDB).filter(ParentalControlsSettingsDB.user_id == user_id).first()
        if pcs:
            pcs.parental_control = settings.parental_control
            pcs.content_filter = settings.content_filter
            pcs.time_limits = settings.time_limits
            pcs.max_time_per_day = settings.max_time_per_day
            pcs.parental_pin_hash = settings.parental_pin_hash
            pcs.version = settings.version
        else:
            pcs = ParentalControlsSettingsDB(
                user_id=user_id,
                parental_control=settings.parental_control,
                content_filter=settings.content_filter,
                time_limits=settings.time_limits,
                max_time_per_day=settings.max_time_per_day,
                parental_pin_hash=settings.parental_pin_hash,
                version=settings.version
            )
            session.add(pcs)

    def _update_account_settings(self, session: Session, user_id: int, settings: AccountSettings) -> None:
        """Actualiza configuraciones de cuenta."""
        accs = session.query(AccountSettingsDB).filter(AccountSettingsDB.user_id == user_id).first()
        if accs:
            accs.name = settings.name
            accs.email = settings.email
            accs.phone = settings.phone
            accs.bio = settings.bio
            accs.sessions_completed = settings.sessions_completed
            accs.tokens_used = settings.tokens_used
            accs.version = settings.version
        else:
            accs = AccountSettingsDB(
                user_id=user_id,
                name=settings.name,
                email=settings.email,
                phone=settings.phone,
                bio=settings.bio,
                sessions_completed=settings.sessions_completed,
                tokens_used=settings.tokens_used,
                version=settings.version
            )
            session.add(accs)

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

        with self.transaction() as session:
            # Verificar que el usuario existe
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            # Eliminar configuraciones actuales
            session.query(GeneralSettingsDB).filter(GeneralSettingsDB.user_id == user_id).delete()
            session.query(NotificationSettingsDB).filter(NotificationSettingsDB.user_id == user_id).delete()
            session.query(PersonalizationSettingsDB).filter(PersonalizationSettingsDB.user_id == user_id).delete()
            session.query(MemorySettingsDB).filter(MemorySettingsDB.user_id == user_id).delete()
            session.query(AppsConnectorsSettingsDB).filter(AppsConnectorsSettingsDB.user_id == user_id).delete()
            session.query(DataControlsSettingsDB).filter(DataControlsSettingsDB.user_id == user_id).delete()
            session.query(SecuritySettingsDB).filter(SecuritySettingsDB.user_id == user_id).delete()
            session.query(ParentalControlsSettingsDB).filter(ParentalControlsSettingsDB.user_id == user_id).delete()
            session.query(AccountSettingsDB).filter(AccountSettingsDB.user_id == user_id).delete()

            # Crear configuraciones por defecto
            self._create_default_settings_for_user(session, user_id)

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