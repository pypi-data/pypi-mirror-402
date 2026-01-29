"""
Tests básicos para el módulo de controles parentales
====================================================

Suite de pruebas unitarias para validar las funcionalidades
del sistema de controles parentales de AILOOS.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from datetime import datetime, timedelta

from . import (
    ParentalControlsManager,
    ContentFilterLevel,
    AgeRestriction,
    InvalidParentalPinError,
    ParentalControlDisabledError,
    TimeLimitExceededError,
    ContentBlockedError,
    AgeRestrictionError,
    UserProfile,
    TimeUsage,
    ContentAnalysis
)

class TestParentalControlsManager(unittest.TestCase):
    """Tests para ParentalControlsManager."""

    def setUp(self):
        """Configuración inicial para cada test."""
        self.mock_settings = Mock()
        self.manager = ParentalControlsManager(settings_manager=self.mock_settings)

        # Configurar mocks por defecto
        self.mock_settings.get_category.return_value = {
            'parental_control': True,
            'content_filter': 'moderate',
            'time_limits': True,
            'max_time_per_day': '2hours'
        }
        self.mock_settings.get.return_value = None

    def test_pin_validation(self):
        """Test validación de formato de PIN."""
        # PINs válidos
        self.assertTrue(self.manager._validate_pin_format("1234"))
        self.assertTrue(self.manager._validate_pin_format("12345678"))

        # PINs inválidos
        self.assertFalse(self.manager._validate_pin_format("123"))  # Muy corto
        self.assertFalse(self.manager._validate_pin_format("123456789"))  # Muy largo
        self.assertFalse(self.manager._validate_pin_format("12a4"))  # Contiene letras
        self.assertFalse(self.manager._validate_pin_format("abcd"))  # Solo letras

    def test_pin_hashing(self):
        """Test generación y verificación de hash de PIN."""
        pin = "1234"

        # Generar hash
        hash_value = self.manager._hash_pin(pin)

        # Verificar formato (salt:hash)
        self.assertIn(':', hash_value)
        salt, hash_part = hash_value.split(':', 1)
        self.assertEqual(len(salt), 32)  # 16 bytes en hex = 32 caracteres
        self.assertEqual(len(hash_part), 64)  # SHA256 en hex = 64 caracteres

        # Verificar PIN correcto
        self.assertTrue(self.manager._verify_pin_hash(pin, hash_value))

        # Verificar PIN incorrecto
        self.assertFalse(self.manager._verify_pin_hash("9999", hash_value))

    def test_set_and_verify_pin(self):
        """Test establecimiento y verificación de PIN parental."""
        user_id = 1
        pin = "1234"

        # Configurar mock para devolver None inicialmente
        self.mock_settings.get.return_value = None

        # Establecer PIN
        result = self.manager.set_parental_pin(user_id, pin)
        self.assertTrue(result)

        # Verificar que se llamó a set con el hash
        self.mock_settings.set.assert_called()
        call_args = self.mock_settings.set.call_args
        self.assertEqual(call_args[0][0], 'parental_pin_hash')
        self.assertIn(':', call_args[0][1])  # Debe contener el hash

        # Configurar mock para devolver el hash
        stored_hash = call_args[0][1]
        self.mock_settings.get.return_value = stored_hash

        # Verificar PIN correcto
        self.assertTrue(self.manager.verify_parental_pin(user_id, pin))

        # Verificar PIN incorrecto
        with self.assertRaises(InvalidParentalPinError):
            self.manager.verify_parental_pin(user_id, "9999")

    def test_time_limits_check(self):
        """Test verificación de límites de tiempo."""
        user_id = 1

        # Configurar límites
        self.mock_settings.get_category.return_value = {
            'time_limits': True,
            'max_time_per_day': '2hours'  # 120 minutos
        }

        # Sin uso previo - debe permitir
        result = self.manager.check_time_limits(user_id)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['remaining_time'], 120)

        # Registrar uso
        self.manager.record_time_usage(user_id, 60)  # 1 hora

        # Verificar estado actualizado
        result = self.manager.check_time_limits(user_id)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['remaining_time'], 60)

        # Exceder límite
        self.manager.record_time_usage(user_id, 70)  # Total: 130 minutos

        result = self.manager.check_time_limits(user_id)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'daily_limit_exceeded')

    def test_content_filtering(self):
        """Test filtrado de contenido."""
        user_id = 1

        # Configurar filtro moderado
        self.mock_settings.get_category.return_value = {
            'content_filter': 'moderate'
        }

        # Contenido seguro
        result = self.manager.check_content_access(user_id, "Este es un contenido seguro")
        self.assertTrue(result['allowed'])

        # Contenido con palabras problemáticas
        result = self.manager.check_content_access(user_id, "Contenido sobre violencia y drogas")
        self.assertFalse(result['allowed'])
        self.assertIn('violencia', result['categories'])
        self.assertIn('droga', result['categories'])

    def test_age_restrictions(self):
        """Test restricciones por edad."""
        user_id = 1

        # Usuario sin edad registrada
        with self.assertRaises(AgeRestrictionError):
            self.manager.validate_age_access(user_id, AgeRestriction.AGE_13_PLUS)

        # Establecer edad de 10 años
        profile = self.manager._get_user_profile(user_id)
        profile.age = 10

        # Debe permitir contenido para todas las edades
        self.assertTrue(self.manager.validate_age_access(user_id, AgeRestriction.ALL_AGES))

        # Debe denegar contenido para 13+
        with self.assertRaises(AgeRestrictionError):
            self.manager.validate_age_access(user_id, AgeRestriction.AGE_13_PLUS)

        # Debe permitir contenido para 7+
        self.assertTrue(self.manager.validate_age_access(user_id, AgeRestriction.AGE_7_PLUS))

    def test_content_moderation(self):
        """Test moderación de contenido en tiempo real."""
        user_id = 1

        # Configurar filtro lenient (para que permita moderación)
        self.mock_settings.get_category.return_value = {
            'content_filter': 'lenient'
        }

        # Contenido con palabras problemáticas (debe moderarse)
        content = "Este contenido habla sobre violencia"
        result = self.manager.moderate_content_realtime(user_id, content)

        # Debe contener moderación (asteriscos)
        self.assertIn('*', result)

        # Configurar filtro estricto para bloqueo completo
        self.mock_settings.get_category.return_value = {
            'content_filter': 'strict'
        }

        # Contenido bloqueado completamente
        with self.assertRaises(ContentBlockedError):
            self.manager.moderate_content_realtime(user_id, "Contenido con mucha violencia y drogas")

    def test_time_limit_parsing(self):
        """Test parsing de límites de tiempo."""
        # Valores válidos
        self.assertEqual(self.manager._parse_time_limit('1hour'), 60)
        self.assertEqual(self.manager._parse_time_limit('2hours'), 120)
        self.assertEqual(self.manager._parse_time_limit('4hours'), 240)
        self.assertEqual(self.manager._parse_time_limit('8hours'), 480)

        # Valor por defecto
        self.assertEqual(self.manager._parse_time_limit('invalid'), 120)

    def test_user_profile_management(self):
        """Test gestión de perfiles de usuario."""
        user_id = 1

        # Obtener perfil (debe crearse automáticamente)
        profile = self.manager._get_user_profile(user_id)
        self.assertEqual(profile.user_id, user_id)
        self.assertIsNone(profile.age)
        self.assertFalse(profile.is_child)

        # Verificar que se cachea
        profile2 = self.manager._get_user_profile(user_id)
        self.assertIs(profile, profile2)

class TestExceptions(unittest.TestCase):
    """Tests para excepciones específicas."""

    def setUp(self):
        self.manager = ParentalControlsManager()

    def test_invalid_pin_error(self):
        """Test InvalidParentalPinError."""
        with self.assertRaises(InvalidParentalPinError):
            raise InvalidParentalPinError("PIN incorrecto")

    def test_parental_control_disabled_error(self):
        """Test ParentalControlDisabledError."""
        with self.assertRaises(ParentalControlDisabledError):
            raise ParentalControlDisabledError("Controles desactivados")

    def test_time_limit_exceeded_error(self):
        """Test TimeLimitExceededError."""
        with self.assertRaises(TimeLimitExceededError):
            raise TimeLimitExceededError("Límite excedido")

    def test_content_blocked_error(self):
        """Test ContentBlockedError."""
        with self.assertRaises(ContentBlockedError):
            raise ContentBlockedError("Contenido bloqueado")

    def test_age_restriction_error(self):
        """Test AgeRestrictionError."""
        with self.assertRaises(AgeRestrictionError):
            raise AgeRestrictionError("Acceso denegado por edad")

class TestDataModels(unittest.TestCase):
    """Tests para modelos de datos."""

    def test_user_profile(self):
        """Test UserProfile dataclass."""
        profile = UserProfile(
            user_id=1,
            age=12,
            is_child=True,
            parent_user_id=2,
            restrictions=['violence', 'drugs']
        )

        self.assertEqual(profile.user_id, 1)
        self.assertEqual(profile.age, 12)
        self.assertTrue(profile.is_child)
        self.assertEqual(profile.parent_user_id, 2)
        self.assertEqual(profile.restrictions, ['violence', 'drugs'])

    def test_time_usage(self):
        """Test TimeUsage dataclass."""
        usage = TimeUsage(
            user_id=1,
            date="2024-01-01",
            total_minutes=90,
            session_minutes=30,
            daily_limit=120
        )

        self.assertEqual(usage.user_id, 1)
        self.assertEqual(usage.date, "2024-01-01")
        self.assertEqual(usage.total_minutes, 90)
        self.assertEqual(usage.session_minutes, 30)
        self.assertEqual(usage.daily_limit, 120)

    def test_content_analysis(self):
        """Test ContentAnalysis dataclass."""
        analysis = ContentAnalysis(
            content_type="text",
            content="test content",
            risk_score=0.7,
            blocked=True,
            categories=['violence']
        )

        self.assertEqual(analysis.content_type, "text")
        self.assertEqual(analysis.content, "test content")
        self.assertEqual(analysis.risk_score, 0.7)
        self.assertTrue(analysis.blocked)
        self.assertEqual(analysis.categories, ['violence'])

class TestEnums(unittest.TestCase):
    """Tests para enumeraciones."""

    def test_content_filter_level(self):
        """Test ContentFilterLevel enum."""
        self.assertEqual(ContentFilterLevel.LENIENT.value, "lenient")
        self.assertEqual(ContentFilterLevel.MODERATE.value, "moderate")
        self.assertEqual(ContentFilterLevel.STRICT.value, "strict")

    def test_age_restriction(self):
        """Test AgeRestriction enum."""
        self.assertEqual(AgeRestriction.ALL_AGES.value, "all_ages")
        self.assertEqual(AgeRestriction.AGE_7_PLUS.value, "7_plus")
        self.assertEqual(AgeRestriction.AGE_13_PLUS.value, "13_plus")
        self.assertEqual(AgeRestriction.AGE_16_PLUS.value, "16_plus")
        self.assertEqual(AgeRestriction.AGE_18_PLUS.value, "18_plus")

if __name__ == '__main__':
    unittest.main()