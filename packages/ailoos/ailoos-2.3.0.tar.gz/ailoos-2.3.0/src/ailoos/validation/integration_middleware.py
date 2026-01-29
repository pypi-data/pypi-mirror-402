"""
Middleware de integración para validaciones en endpoints de AILOOS.
Facilita la integración de validaciones avanzadas en APIs FastAPI/Flask.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from functools import wraps
from dataclasses import dataclass

from ..core.logging import get_logger
from .advanced_validator import get_advanced_validator, ValidationResult
from .error_handler import get_error_handler, AiloosError, ErrorContext
from .rate_limiter import get_rate_limit_manager, RateLimitResult
from .security_validator import get_security_validator

logger = get_logger(__name__)


@dataclass
class ValidationMiddlewareConfig:
    """Configuración del middleware de validaciones."""
    enable_rate_limiting: bool = True
    enable_input_validation: bool = True
    enable_security_validation: bool = True
    enable_audit_logging: bool = True
    fail_on_validation_error: bool = True
    sanitize_inputs: bool = True
    log_validation_errors: bool = True


class ValidationMiddleware:
    """
    Middleware que integra todas las validaciones en endpoints.
    Compatible con FastAPI, Flask y otros frameworks web.
    """

    def __init__(self, config: Optional[ValidationMiddlewareConfig] = None):
        self.config = config or ValidationMiddlewareConfig()
        self.advanced_validator = get_advanced_validator()
        self.error_handler = get_error_handler()
        # rate_limiter se obtiene asíncronamente en validate_request
        self.security_validator = get_security_validator()

    async def validate_request(
        self,
        request_data: Dict[str, Any],
        validation_schema: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validar request completo con todas las capas de validación.

        Args:
            request_data: Datos del request
            validation_schema: Esquema de validación
            context: Contexto del request (user_id, ip, endpoint, etc.)

        Returns:
            Resultado de validación completo
        """
        # Rate limiting
        if self.config.enable_rate_limiting and 'rate_limit' in validation_schema:
            rate_limit_config = validation_schema['rate_limit']
            key = context.get('ip', context.get('user_id', 'anonymous'))

            # Obtener rate limiter de manera asíncrona
            rate_limiter_mgr = await get_rate_limit_manager()
            rate_limit_result = await rate_limiter_mgr.check_limit(
                key,
                rate_limit_config.get('rule_name', 'api_general'),
                context
            )

            if not rate_limit_result.allowed:
                # Crear error de rate limit
                error = self.error_handler.create_error(
                    3004,  # RATE_LIMIT_EXCEEDED
                    ErrorContext(
                        user_id=context.get('user_id'),
                        ip_address=context.get('ip'),
                        endpoint=context.get('endpoint'),
                        method=context.get('method')
                    ),
                    custom_message="Demasiadas solicitudes. Intente más tarde.",
                    details=rate_limit_result.to_dict()
                )

                if self.config.fail_on_validation_error:
                    raise error

                return ValidationResult(
                    is_valid=False,
                    errors=[{
                        'code': 3004,
                        'message': 'Rate limit exceeded',
                        'severity': 'error',
                        'details': rate_limit_result.to_dict()
                    }],
                    metadata={'rate_limit': rate_limit_result.to_dict()}
                )

        # Validación de entrada
        if self.config.enable_input_validation:
            validation_result = await self.advanced_validator.validate_request(
                request_data,
                validation_schema,
                context
            )

            if not validation_result.is_valid and self.config.fail_on_validation_error:
                # Crear error de validación
                error = self.error_handler.create_error(
                    1000,  # INVALID_INPUT
                    ErrorContext(
                        user_id=context.get('user_id'),
                        ip_address=context.get('ip'),
                        endpoint=context.get('endpoint'),
                        method=context.get('method')
                    ),
                    custom_message="Datos de entrada inválidos",
                    details=validation_result.to_dict()
                )
                raise error

            return validation_result

        return ValidationResult(is_valid=True)

    def create_endpoint_validator(
        self,
        validation_schema: Dict[str, Any],
        require_auth: bool = False,
        allowed_roles: Optional[List[str]] = None
    ):
        """
        Crear decorador para validar endpoints.

        Args:
            validation_schema: Esquema de validación
            require_auth: Si requiere autenticación
            allowed_roles: Roles permitidos

        Returns:
            Decorador para endpoints
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extraer request data y context
                request_data, context = self._extract_request_info(args, kwargs)

                try:
                    # Validar request
                    validation_result = await self.validate_request(
                        request_data,
                        validation_schema,
                        context
                    )

                    # Sanitizar inputs si está habilitado
                    if self.config.sanitize_inputs:
                        request_data = self._sanitize_request_data(request_data)

                    # Añadir metadata de validación al contexto
                    context['validation_result'] = validation_result

                    # Ejecutar función original
                    return await func(*args, **kwargs)

                except AiloosError as e:
                    # Log error si está habilitado
                    if self.config.log_validation_errors:
                        await self.error_handler.handle_error(e, context)

                    # Re-raise para que el framework lo maneje
                    raise

                except Exception as e:
                    # Convertir errores inesperados
                    error = await self.error_handler.handle_error(
                        e,
                        ErrorContext(
                            user_id=context.get('user_id'),
                            ip_address=context.get('ip'),
                            endpoint=context.get('endpoint'),
                            method=context.get('method')
                        )
                    )
                    raise error

            return wrapper
        return decorator

    def _extract_request_info(self, args, kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extraer información del request de los argumentos de la función.
        Esta implementación es genérica y debe adaptarse al framework usado.
        """
        # Implementación básica - debe adaptarse al framework específico
        request_data = {}
        context = {
            'ip': '127.0.0.1',  # Default
            'endpoint': 'unknown',
            'method': 'GET',
            'user_id': None
        }

        # Intentar extraer de argumentos comunes
        for arg in args:
            if hasattr(arg, '__dict__'):
                # Podría ser un objeto request
                if hasattr(arg, 'json') and callable(getattr(arg, 'json')):
                    # FastAPI request
                    try:
                        # En FastAPI, el request body ya está parseado
                        request_data = arg.__dict__
                    except:
                        pass
                elif hasattr(arg, 'form'):
                    # Flask request
                    request_data = dict(arg.form) if arg.form else {}

        # Extraer de kwargs
        for key, value in kwargs.items():
            if key in ['user_id', 'ip_address', 'endpoint', 'method']:
                context[key] = value
            elif isinstance(value, dict) and not request_data:
                request_data = value

        return request_data, context

    def _sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar datos del request."""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.security_validator.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.security_validator.sanitize_input(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    async def validate_file_upload(
        self,
        file_data: bytes,
        filename: str,
        allowed_types: List[str] = None,
        max_size: int = 10*1024*1024  # 10MB
    ) -> ValidationResult:
        """
        Validar subida de archivos.

        Args:
            file_data: Datos del archivo
            filename: Nombre del archivo
            allowed_types: Tipos MIME permitidos
            max_size: Tamaño máximo en bytes

        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True)

        # Verificar tamaño
        if len(file_data) > max_size:
            result.errors.append({
                'code': 1003,  # VALUE_OUT_OF_RANGE
                'message': f'Archivo demasiado grande. Máximo {max_size} bytes',
                'field': 'file',
                'severity': 'error'
            })
            result.is_valid = False

        # Verificar tipo MIME básico
        if allowed_types:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)

            if mime_type and mime_type not in allowed_types:
                result.errors.append({
                    'code': 1002,  # INVALID_FORMAT
                    'message': f'Tipo de archivo no permitido: {mime_type}',
                    'field': 'file',
                    'severity': 'error'
                })
                result.is_valid = False

        # Verificar contenido peligroso (básico)
        if self._contains_malicious_content(file_data):
            result.errors.append({
                'code': 3002,  # SUSPICIOUS_ACTIVITY
                'message': 'Archivo contiene contenido potencialmente peligroso',
                'field': 'file',
                'severity': 'error'
            })
            result.is_valid = False

        return result

    def _contains_malicious_content(self, file_data: bytes) -> bool:
        """Verificación básica de contenido malicioso."""
        # Convertir a string para análisis
        try:
            content = file_data.decode('utf-8', errors='ignore').lower()
        except:
            return False  # No se puede analizar como texto

        # Patrones peligrosos
        dangerous_patterns = [
            '<?php', '<script', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'eval(', 'exec(',
            'union select', 'drop table', 'xp_cmdshell'
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                return True

        return False


# Funciones de conveniencia para esquemas de validación comunes

def create_user_registration_schema() -> Dict[str, Any]:
    """Esquema de validación para registro de usuarios."""
    return {
        'rate_limit': {
            'rule_name': 'api_auth',
            'max_requests': 5,
            'window_seconds': 300
        },
        'fields': {
            'username': {
                'required': True,
                'type': 'str',
                'min_length': 3,
                'max_length': 50,
                'pattern': r'^[a-zA-Z0-9_-]+$'
            },
            'email': {
                'required': True,
                'type': 'email'
            },
            'password': {
                'required': True,
                'type': 'password',
                'min_length': 8
            },
            'confirmPassword': {
                'required': True,
                'type': 'str'
            }
        },
        'business': {
            'passwords_match': True  # Validación personalizada
        }
    }


def create_federated_session_schema() -> Dict[str, Any]:
    """Esquema de validación para sesiones federadas."""
    return {
        'rate_limit': {
            'rule_name': 'federated_training',
            'max_requests': 10,
            'window_seconds': 60
        },
        'fields': {
            'name': {
                'required': True,
                'type': 'str',
                'min_length': 3,
                'max_length': 100
            },
            'description': {
                'required': False,
                'type': 'str',
                'max_length': 500
            },
            'minNodes': {
                'required': True,
                'type': 'int',
                'min_value': 2,
                'max_value': 1000
            },
            'maxNodes': {
                'required': True,
                'type': 'int',
                'min_value': 2,
                'max_value': 1000
            },
            'privacyBudget': {
                'required': True,
                'type': 'float',
                'min_value': 0.1,
                'max_value': 10.0
            }
        },
        'business': {
            'min_nodes_leq_max_nodes': True
        }
    }


def create_marketplace_listing_schema() -> Dict[str, Any]:
    """Esquema de validación para listings del marketplace."""
    return {
        'rate_limit': {
            'rule_name': 'marketplace',
            'max_requests': 20,
            'window_seconds': 3600
        },
        'fields': {
            'title': {
                'required': True,
                'type': 'str',
                'min_length': 5,
                'max_length': 200
            },
            'description': {
                'required': True,
                'type': 'str',
                'min_length': 20,
                'max_length': 2000
            },
            'price': {
                'required': True,
                'type': 'float',
                'min_value': 0.01,
                'max_value': 10000
            },
            'category': {
                'required': True,
                'type': 'str',
                'allowed_values': ['dataset', 'model', 'computation', 'other']
            },
            'tags': {
                'required': True,
                'type': 'list',
                'min_length': 1,
                'max_length': 10
            }
        }
    }


# Instancia global del middleware
validation_middleware = ValidationMiddleware()


def get_validation_middleware() -> ValidationMiddleware:
    """Obtener instancia global del middleware de validaciones."""
    return validation_middleware