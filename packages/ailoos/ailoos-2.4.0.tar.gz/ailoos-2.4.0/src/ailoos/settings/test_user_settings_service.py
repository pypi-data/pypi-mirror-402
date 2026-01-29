"""
Tests básicos para UserSettingsService
======================================

Este módulo contiene tests unitarios para validar el funcionamiento
del servicio UserSettingsService con SQLAlchemy.
"""

import pytest
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .user_settings_service import (
    UserSettingsService,
    ValidationError,
    UserNotFoundError,
    DuplicateUserError,
    UserSettingsServiceError
)
from .models_sqlalchemy import Base


class TestUserSettingsService:
    """Tests para UserSettingsService."""

    @pytest.fixture
    def db_url(self):
        """URL de base de datos para tests."""
        return "sqlite:///:memory:"

    @pytest.fixture
    def service(self, db_url):
        """Instancia del servicio para tests."""
        service = UserSettingsService(db_url)
        # Crear tablas
        Base.metadata.create_all(bind=service.engine)
        return service

    def test_create_user_success(self, service):
        """Test creación exitosa de usuario."""
        user_data = service.create_user(
            username="testuser",
            email="test@example.com",
            name="Test User",
            phone="+34 600 000 000"
        )

        assert user_data['username'] == "testuser"
        assert user_data['email'] == "test@example.com"
        assert 'id' in user_data
        assert 'created_at' in user_data

    def test_create_user_validation_errors(self, service):
        """Test validaciones en creación de usuario."""
        # Username demasiado corto
        with pytest.raises(ValidationError):
            service.create_user(username="ab", email="test@example.com")

        # Email inválido
        with pytest.raises(ValidationError):
            service.create_user(username="testuser", email="invalid-email")

        # Username con caracteres inválidos
        with pytest.raises(ValidationError):
            service.create_user(username="test@#$%", email="test@example.com")

    def test_create_duplicate_user(self, service):
        """Test creación de usuario duplicado."""
        service.create_user(username="testuser", email="test@example.com")

        # Duplicar username
        with pytest.raises(UserSettingsServiceError):
            service.create_user(username="testuser", email="other@example.com")

        # Duplicar email
        with pytest.raises(UserSettingsServiceError):
            service.create_user(username="otheruser", email="test@example.com")

    def test_get_user(self, service):
        """Test obtener usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        user = service.get_user(created_user['id'])

        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_get_user_not_found(self, service):
        """Test obtener usuario inexistente."""
        with pytest.raises(UserNotFoundError):
            service.get_user(999)

    def test_get_user_by_username(self, service):
        """Test obtener usuario por username."""
        service.create_user(username="testuser", email="test@example.com")

        user = service.get_user_by_username("testuser")

        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_get_user_by_email(self, service):
        """Test obtener usuario por email."""
        service.create_user(username="testuser", email="test@example.com")

        user = service.get_user_by_email("test@example.com")

        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_update_user(self, service):
        """Test actualizar usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        updated_user = service.update_user(
            user_id=created_user['id'],
            username="newusername",
            email="new@example.com",
            name="New Name"
        )

        assert updated_user['username'] == "newusername"
        assert updated_user['email'] == "new@example.com"

    def test_update_user_not_found(self, service):
        """Test actualizar usuario inexistente."""
        with pytest.raises(UserSettingsServiceError):
            service.update_user(user_id=999, username="newname")

    def test_delete_user(self, service):
        """Test eliminar usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        result = service.delete_user(created_user['id'])

        assert result is True

        # Verificar que ya no existe
        with pytest.raises(UserNotFoundError):
            service.get_user(created_user['id'])

    def test_delete_user_not_found(self, service):
        """Test eliminar usuario inexistente."""
        with pytest.raises(UserSettingsServiceError):
            service.delete_user(999)

    def test_list_users(self, service):
        """Test listar usuarios."""
        service.create_user(username="user1", email="user1@example.com")
        service.create_user(username="user2", email="user2@example.com")

        users = service.list_users()

        assert len(users) == 2
        usernames = [u['username'] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames

    def test_get_user_settings(self, service):
        """Test obtener configuraciones de usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        settings = service.get_user_settings(created_user['id'])

        # Verificar que todas las categorías existen
        expected_categories = [
            'general', 'notifications', 'personalization', 'memory',
            'apps_connectors', 'data_controls', 'security', 'parental_controls', 'account'
        ]

        for category in expected_categories:
            assert category in settings
            assert isinstance(settings[category], dict)

        # Verificar valores por defecto
        assert settings['general']['appearance'] == 'system'
        assert settings['general']['ui_language'] == 'es'
        assert settings['notifications']['mute_all'] is False
        assert settings['memory']['max_memory_items'] == 256

    def test_update_category_settings(self, service):
        """Test actualizar categoría específica."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Actualizar configuraciones generales
        updated_settings = service.update_category_settings(
            user_id=created_user['id'],
            category='general',
            settings={
                'appearance': 'dark',
                'accent_color': 'green',
                'font_size': 'large'
            }
        )

        assert updated_settings['general']['appearance'] == 'dark'
        assert updated_settings['general']['accent_color'] == 'green'
        assert updated_settings['general']['font_size'] == 'large'

    def test_update_category_invalid_category(self, service):
        """Test actualizar categoría inválida."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        with pytest.raises(ValidationError):
            service.update_category_settings(
                user_id=created_user['id'],
                category='invalid_category',
                settings={}
            )

    def test_update_user_settings_validation(self, service):
        """Test validación en actualización de configuraciones."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Configuraciones inválidas
        invalid_settings = {
            'general': {
                'appearance': 'invalid_appearance',
                'font_size': 'invalid_size'
            }
        }

        with pytest.raises(ValidationError):
            service.update_user_settings(created_user['id'], invalid_settings)

    def test_reset_user_settings_to_default(self, service):
        """Test resetear configuraciones a valores por defecto."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Modificar algunas configuraciones
        service.update_category_settings(
            created_user['id'], 'general',
            {'appearance': 'dark', 'accent_color': 'red'}
        )

        # Resetear
        reset_settings = service.reset_user_settings_to_default(created_user['id'])

        # Verificar que volvieron a valores por defecto
        assert reset_settings['general']['appearance'] == 'system'
        assert reset_settings['general']['accent_color'] == 'blue'

    def test_bulk_update_settings(self, service):
        """Test actualización masiva de configuraciones."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        updates = {
            'general': {
                'appearance': 'light',
                'accent_color': 'purple'
            },
            'notifications': {
                'mute_all': True,
                'responses_app': False
            }
        }

        updated_settings = service.bulk_update_settings(created_user['id'], updates)

        assert updated_settings['general']['appearance'] == 'light'
        assert updated_settings['general']['accent_color'] == 'purple'
        assert updated_settings['notifications']['mute_all'] is True
        assert updated_settings['notifications']['responses_app'] is False

    def test_get_settings_summary(self, service):
        """Test obtener resumen de configuraciones."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        summary = service.get_settings_summary(created_user['id'])

        assert 'user_id' in summary
        assert 'last_updated' in summary
        assert 'version' in summary
        assert 'categories' in summary

        categories = summary['categories']
        assert 'general' in categories
        assert 'notifications' in categories
        assert 'security' in categories
        assert 'memory' in categories

    def test_export_import_user_data(self, service):
        """Test exportar e importar datos de usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Modificar algunas configuraciones
        service.update_category_settings(
            created_user['id'], 'general',
            {'appearance': 'dark', 'accent_color': 'green'}
        )

        # Exportar
        export_data = service.export_user_data(created_user['id'])

        assert 'user' in export_data
        assert 'settings' in export_data
        assert 'exported_at' in export_data

        # Crear otro usuario
        other_user = service.create_user(username="otheruser", email="other@example.com")

        # Importar datos
        imported_settings = service.import_user_data(other_user['id'], export_data)

        # Verificar que las configuraciones se importaron
        assert imported_settings['general']['appearance'] == 'dark'
        assert imported_settings['general']['accent_color'] == 'green'

    def test_validate_user_settings(self, service):
        """Test validar configuraciones de usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Configuraciones válidas
        errors = service.validate_user_settings(created_user['id'])
        assert len(errors) == 0

    def test_get_user_statistics(self, service):
        """Test obtener estadísticas de usuario."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        stats = service.get_user_statistics(created_user['id'])

        assert 'user_id' in stats
        assert 'sessions_completed' in stats
        assert 'tokens_used' in stats
        assert 'memory_usage' in stats
        assert 'last_updated' in stats

        assert stats['sessions_completed'] == 0
        assert stats['tokens_used'] == 0
        assert stats['memory_usage']['used'] == 0
        assert stats['memory_usage']['max'] == 256

    def test_business_rules_application(self, service):
        """Test aplicación de reglas de negocio."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Activar control parental - debería forzar time_limits = True
        settings = service.update_category_settings(
            created_user['id'], 'parental_controls',
            {'parental_control': True, 'time_limits': False}
        )

        assert settings['parental_controls']['time_limits'] is True

        # Desactivar personalización - debería limpiar datos personales
        settings = service.update_category_settings(
            created_user['id'], 'personalization',
            {
                'enable_personalization': False,
                'nickname': 'Test Nick',
                'occupation': 'Test Job'
            }
        )

        assert settings['personalization']['nickname'] == ''
        assert settings['personalization']['occupation'] == ''

        # Silenciar notificaciones - debería desactivar todas
        settings = service.update_category_settings(
            created_user['id'], 'notifications',
            {
                'mute_all': True,
                'responses_app': True,
                'tasks_app': True
            }
        )

        assert settings['notifications']['responses_app'] is False
        assert settings['notifications']['tasks_app'] is False

    def test_data_transformation(self, service):
        """Test transformación de datos."""
        created_user = service.create_user(username="testuser", email="test@example.com")

        # Email debería normalizarse a minúsculas
        settings = service.update_category_settings(
            created_user['id'], 'account',
            {'email': 'TEST@EXAMPLE.COM'}
        )

        assert settings['account']['email'] == 'test@example.com'

        # URL debería trimarse
        settings = service.update_category_settings(
            created_user['id'], 'apps_connectors',
            {'webhook_url': '  https://example.com/webhook  '}
        )

        assert settings['apps_connectors']['webhook_url'] == 'https://example.com/webhook'


if __name__ == "__main__":
    pytest.main([__file__])