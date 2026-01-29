"""
Sistema avanzado de validaciones para AILOOS.
Incluye validaciones de seguridad, rate limiting, errores jerárquicos y auditoría.
"""

import asyncio
import hashlib
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import ipaddress
import secrets
import string

from ..core.logging import get_logger, log_api_request
from ..core.config import get_config

logger = get_logger(__name__)


class ValidationErrorCode(Enum):
    """Códigos de error jerárquicos para validaciones."""

    # Errores generales (1000-1999)
    INVALID_INPUT = 1000
    MISSING_REQUIRED_FIELD = 1001
    INVALID_FORMAT = 1002
    VALUE_OUT_OF_RANGE = 1003
    DUPLICATE_VALUE = 1004

    # Errores de autenticación (2000-2999)
    INVALID_CREDENTIALS = 2000
    TOKEN_EXPIRED = 2001
    INSUFFICIENT_PERMISSIONS = 2002
    ACCOUNT_LOCKED = 2003
    TWO_FACTOR_REQUIRED = 2004

    # Errores de seguridad (3000-3999)
    WEAK_PASSWORD = 3000
    PASSWORD_COMPROMISED = 3001
    SUSPICIOUS_ACTIVITY = 3002
    IP_BLOCKED = 3003
    RATE_LIMIT_EXCEEDED = 3004

    # Errores de negocio (4000-4999)
    INSUFFICIENT_BALANCE = 4000
    INVALID_TRANSACTION = 4001
    SESSION_FULL = 4002
    MODEL_NOT_AVAILABLE = 4003
    DATASET_INVALID = 4004

    # Errores de sistema (5000-5999)
    SERVICE_UNAVAILABLE = 5000
    DATABASE_ERROR = 5001
    EXTERNAL_API_ERROR = 5002
    CONFIGURATION_ERROR = 5003


@dataclass
class ValidationError:
    """Error de validación estructurado."""
    code: ValidationErrorCode
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "error"  # error, warning, info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "field": self.field,
            "details": self.details,
            "severity": self.severity
        }


@dataclass
class ValidationResult:
    """Resultado de validación."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: ValidationError):
        """Agregar error de validación."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: ValidationError):
        """Agregar advertencia de validación."""
        warning.severity = "warning"
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "metadata": self.metadata
        }


class RateLimiter:
    """Sistema de rate limiting avanzado."""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_limits: Dict[str, List[float]] = {}
        self.config = get_config()

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_limit: int = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar rate limit.

        Args:
            key: Identificador único (ej: IP, user_id)
            max_requests: Máximo de requests en la ventana
            window_seconds: Ventana de tiempo en segundos
            burst_limit: Límite de burst (opcional)

        Returns:
            (allowed, metadata)
        """
        current_time = time.time()

        if self.redis:
            # Usar Redis para rate limiting distribuido
            return await self._check_redis_rate_limit(key, max_requests, window_seconds, burst_limit, current_time)
        else:
            # Usar memoria local
            return self._check_local_rate_limit(key, max_requests, window_seconds, burst_limit, current_time)

    async def _check_redis_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_limit: int,
        current_time: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting usando Redis."""
        try:
            # Usar Redis sorted sets para sliding window
            window_key = f"ratelimit:{key}:{int(current_time // window_seconds)}"

            # Añadir timestamp actual
            await self.redis.zadd(window_key, {str(current_time): current_time})

            # Remover timestamps fuera de la ventana
            min_time = current_time - window_seconds
            await self.redis.zremrangebyscore(window_key, '-inf', min_time)

            # Contar requests en la ventana
            count = await self.redis.zcard(window_key)

            # Verificar burst limit si está configurado
            if burst_limit and count > burst_limit:
                allowed = False
            else:
                allowed = count <= max_requests

            # Calcular tiempo de espera si está limitado
            reset_time = current_time + window_seconds

            # Configurar expiración de la key
            await self.redis.expire(window_key, window_seconds * 2)

            metadata = {
                "current_requests": count,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": reset_time,
                "burst_limit": burst_limit
            }

            return allowed, metadata

        except Exception as e:
            logger.error(f"Error en Redis rate limiting: {e}")
            # Fallback a local
            return self._check_local_rate_limit(key, max_requests, window_seconds, burst_limit, current_time)

    def _check_local_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_limit: int,
        current_time: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting usando memoria local."""
        if key not in self.local_limits:
            self.local_limits[key] = []

        # Limpiar timestamps antiguos
        min_time = current_time - window_seconds
        self.local_limits[key] = [t for t in self.local_limits[key] if t > min_time]

        # Verificar límites
        count = len(self.local_limits[key])

        if burst_limit and count >= burst_limit:
            allowed = False
        else:
            allowed = count < max_requests

        if allowed:
            self.local_limits[key].append(current_time)

        reset_time = current_time + window_seconds

        metadata = {
            "current_requests": count + (1 if allowed else 0),
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "reset_time": reset_time,
            "burst_limit": burst_limit
        }

        return allowed, metadata


class SecurityValidator:
    """Validador de seguridad avanzado."""

    def __init__(self):
        self.config = get_config()
        self.common_passwords = self._load_common_passwords()

    def _load_common_passwords(self) -> set:
        """Cargar lista de contraseñas comunes."""
        try:
            # En producción, cargar desde archivo o base de datos
            return {
                "password", "123456", "123456789", "qwerty", "abc123",
                "password123", "admin", "letmein", "welcome", "monkey",
                "1234567890", "password1", "qwerty123", "welcome123"
            }
        except:
            return set()

    def validate_password(self, password: str, user_context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validar contraseña con criterios avanzados.

        Args:
            password: Contraseña a validar
            user_context: Contexto del usuario (username, email, etc.)
        """
        result = ValidationResult(is_valid=True)

        # Longitud mínima
        min_length = self.config.get('password_min_length', 8)
        if len(password) < min_length:
            result.add_error(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message=f"La contraseña debe tener al menos {min_length} caracteres",
                field="password"
            ))

        # Longitud máxima
        max_length = self.config.get('password_max_length', 128)
        if len(password) > max_length:
            result.add_error(ValidationError(
                code=ValidationErrorCode.INVALID_FORMAT,
                message=f"La contraseña no puede exceder {max_length} caracteres",
                field="password"
            ))

        # Verificar caracteres requeridos
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

        required_types = self.config.get('password_requirements', ['upper', 'lower', 'digit'])
        if 'upper' in required_types and not has_upper:
            result.add_error(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message="La contraseña debe contener al menos una letra mayúscula",
                field="password"
            ))

        if 'lower' in required_types and not has_lower:
            result.add_error(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message="La contraseña debe contener al menos una letra minúscula",
                field="password"
            ))

        if 'digit' in required_types and not has_digit:
            result.add_error(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message="La contraseña debe contener al menos un número",
                field="password"
            ))

        if 'special' in required_types and not has_special:
            result.add_error(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message="La contraseña debe contener al menos un carácter especial",
                field="password"
            ))

        # Verificar contraseñas comunes
        if password.lower() in self.common_passwords:
            result.add_error(ValidationError(
                code=ValidationErrorCode.PASSWORD_COMPROMISED,
                message="Esta contraseña es muy común y fácil de adivinar",
                field="password"
            ))

        # Verificar si contiene información personal
        if user_context:
            personal_info = []
            if 'username' in user_context and user_context['username']:
                personal_info.extend(str(user_context['username']).lower().split())
            if 'email' in user_context and user_context['email']:
                personal_info.append(str(user_context['email']).split('@')[0].lower())
            if 'first_name' in user_context and user_context['first_name']:
                personal_info.append(str(user_context['first_name']).lower())
            if 'last_name' in user_context and user_context['last_name']:
                personal_info.append(str(user_context['last_name']).lower())

            password_lower = password.lower()
            for info in personal_info:
                if len(info) > 2 and info in password_lower:
                    result.add_warning(ValidationError(
                        code=ValidationErrorCode.WEAK_PASSWORD,
                        message="La contraseña contiene información personal",
                        field="password",
                        details={"personal_info": info}
                    ))
                    break

        # Calcular entropía
        entropy = self._calculate_password_entropy(password)
        min_entropy = self.config.get('password_min_entropy', 50)

        if entropy < min_entropy:
            result.add_warning(ValidationError(
                code=ValidationErrorCode.WEAK_PASSWORD,
                message=f"La contraseña es débil (entropía: {entropy:.1f}, mínimo: {min_entropy})",
                field="password",
                details={"entropy": entropy, "min_entropy": min_entropy}
            ))

        result.metadata.update({
            "length": len(password),
            "entropy": entropy,
            "has_upper": has_upper,
            "has_lower": has_lower,
            "has_digit": has_digit,
            "has_special": has_special
        })

        return result

    def _calculate_password_entropy(self, password: str) -> float:
        """Calcular entropía de contraseña."""
        if not password:
            return 0

        # Estimar tamaño del alfabeto
        charset_size = 0
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            charset_size += 32  # Caracteres especiales comunes

        if charset_size == 0:
            charset_size = 26  # Default a minúsculas

        # Entropía = log2(charset_size ^ length)
        import math
        return math.log2(charset_size) * len(password)

    def validate_email(self, email: str) -> ValidationResult:
        """Validar formato de email."""
        result = ValidationResult(is_valid=True)

        # Regex básico de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            result.add_error(ValidationError(
                code=ValidationErrorCode.INVALID_FORMAT,
                message="Formato de email inválido",
                field="email"
            ))
            return result

        # Verificar longitud
        if len(email) > 254:  # RFC 5321
            result.add_error(ValidationError(
                code=ValidationErrorCode.INVALID_FORMAT,
                message="Email demasiado largo",
                field="email"
            ))

        # Verificar dominios temporales/sospechosos
        domain = email.split('@')[1].lower()
        suspicious_domains = {
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'temp-mail.org', 'throwaway.email', 'yopmail.com'
        }

        if domain in suspicious_domains:
            result.add_warning(ValidationError(
                code=ValidationErrorCode.SUSPICIOUS_ACTIVITY,
                message="Dominio de email temporal detectado",
                field="email",
                details={"domain": domain}
            ))

        return result

    def validate_ip_address(self, ip_str: str) -> ValidationResult:
        """Validar dirección IP."""
        result = ValidationResult(is_valid=True)

        try:
            ip_obj = ipaddress.ip_address(ip_str)
            result.metadata["ip_version"] = ip_obj.version
            result.metadata["is_private"] = ip_obj.is_private
            result.metadata["is_loopback"] = ip_obj.is_loopback

            # Verificar IPs bloqueadas
            blocked_ranges = self.config.get('blocked_ip_ranges', [])
            for blocked_range in blocked_ranges:
                if ip_obj in ipaddress.ip_network(blocked_range, strict=False):
                    result.add_error(ValidationError(
                        code=ValidationErrorCode.IP_BLOCKED,
                        message="Dirección IP bloqueada",
                        field="ip_address",
                        details={"ip": ip_str, "blocked_range": blocked_range}
                    ))
                    break

        except ValueError:
            result.add_error(ValidationError(
                code=ValidationErrorCode.INVALID_FORMAT,
                message="Dirección IP inválida",
                field="ip_address"
            ))

        return result

    def sanitize_input(self, input_str: str, max_length: int = 1000) -> str:
        """Sanitizar entrada de usuario."""
        if not input_str:
            return ""

        # Limitar longitud
        if len(input_str) > max_length:
            input_str = input_str[:max_length]

        # Remover caracteres de control
        input_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)

        # Normalizar espacios
        input_str = re.sub(r'\s+', ' ', input_str).strip()

        return input_str


class AdvancedValidator:
    """Validador avanzado principal."""

    def __init__(self):
        self.config = get_config()
        self.security_validator = SecurityValidator()
        self.rate_limiter = RateLimiter()
        self.audit_log: List[Dict[str, Any]] = []

    async def validate_request(
        self,
        request_data: Dict[str, Any],
        validation_rules: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ValidationResult:
        """
        Validar request completo con reglas avanzadas.

        Args:
            request_data: Datos del request
            validation_rules: Reglas de validación
            context: Contexto adicional (user_id, ip, etc.)
        """
        result = ValidationResult(is_valid=True)
        context = context or {}

        # Rate limiting
        if 'rate_limit' in validation_rules:
            rl_config = validation_rules['rate_limit']
            key = context.get('ip', context.get('user_id', 'anonymous'))
            allowed, rl_metadata = await self.rate_limiter.check_rate_limit(
                key=key,
                max_requests=rl_config.get('max_requests', 100),
                window_seconds=rl_config.get('window_seconds', 60),
                burst_limit=rl_config.get('burst_limit')
            )

            if not allowed:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.RATE_LIMIT_EXCEEDED,
                    message="Demasiadas solicitudes. Intente más tarde.",
                    details=rl_metadata
                ))
                return result

            result.metadata['rate_limit'] = rl_metadata

        # Validaciones de campos
        if 'fields' in validation_rules:
            await self._validate_fields(request_data, validation_rules['fields'], result, context)

        # Validaciones de seguridad
        if 'security' in validation_rules:
            await self._validate_security(request_data, validation_rules['security'], result, context)

        # Validaciones de negocio
        if 'business' in validation_rules:
            await self._validate_business(request_data, validation_rules['business'], result, context)

        # Registrar auditoría
        await self._audit_validation(request_data, validation_rules, result, context)

        return result

    async def _validate_fields(
        self,
        data: Dict[str, Any],
        field_rules: Dict[str, Any],
        result: ValidationResult,
        context: Dict[str, Any]
    ):
        """Validar campos individuales."""
        for field_name, rules in field_rules.items():
            field_value = data.get(field_name)

            # Campo requerido
            if rules.get('required', False) and (field_value is None or field_value == ""):
                result.add_error(ValidationError(
                    code=ValidationErrorCode.MISSING_REQUIRED_FIELD,
                    message=f"El campo '{field_name}' es requerido",
                    field=field_name
                ))
                continue

            if field_value is None or field_value == "":
                continue

            # Tipo de dato
            if 'type' in rules:
                if not self._validate_type(field_value, rules['type']):
                    result.add_error(ValidationError(
                        code=ValidationErrorCode.INVALID_FORMAT,
                        message=f"El campo '{field_name}' debe ser de tipo {rules['type']}",
                        field=field_name,
                        details={"expected_type": rules['type'], "actual_value": str(field_value)}
                    ))
                    continue

            # Longitud
            if 'min_length' in rules and len(str(field_value)) < rules['min_length']:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.VALUE_OUT_OF_RANGE,
                    message=f"El campo '{field_name}' debe tener al menos {rules['min_length']} caracteres",
                    field=field_name
                ))

            if 'max_length' in rules and len(str(field_value)) > rules['max_length']:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.VALUE_OUT_OF_RANGE,
                    message=f"El campo '{field_name}' no puede exceder {rules['max_length']} caracteres",
                    field=field_name
                ))

            # Rango numérico
            if 'min_value' in rules and isinstance(field_value, (int, float)) and field_value < rules['min_value']:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.VALUE_OUT_OF_RANGE,
                    message=f"El campo '{field_name}' debe ser mayor o igual a {rules['min_value']}",
                    field=field_name
                ))

            if 'max_value' in rules and isinstance(field_value, (int, float)) and field_value > rules['max_value']:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.VALUE_OUT_OF_RANGE,
                    message=f"El campo '{field_name}' debe ser menor o igual a {rules['max_value']}",
                    field=field_name
                ))

            # Regex pattern
            if 'pattern' in rules and not re.match(rules['pattern'], str(field_value)):
                result.add_error(ValidationError(
                    code=ValidationErrorCode.INVALID_FORMAT,
                    message=f"El formato del campo '{field_name}' es inválido",
                    field=field_name,
                    details={"pattern": rules['pattern']}
                ))

            # Valores permitidos
            if 'allowed_values' in rules and field_value not in rules['allowed_values']:
                result.add_error(ValidationError(
                    code=ValidationErrorCode.INVALID_INPUT,
                    message=f"El valor del campo '{field_name}' no está permitido",
                    field=field_name,
                    details={"allowed_values": rules['allowed_values']}
                ))

            # Validaciones específicas por tipo
            if rules.get('type') == 'email':
                email_result = self.security_validator.validate_email(field_value)
                result.errors.extend(email_result.errors)
                result.warnings.extend(email_result.warnings)

            elif rules.get('type') == 'password':
                user_context = {
                    'username': data.get('username'),
                    'email': data.get('email'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name')
                }
                password_result = self.security_validator.validate_password(field_value, user_context)
                result.errors.extend(password_result.errors)
                result.warnings.extend(password_result.warnings)

            elif rules.get('type') == 'ip_address':
                ip_result = self.security_validator.validate_ip_address(field_value)
                result.errors.extend(ip_result.errors)
                result.warnings.extend(ip_result.warnings)

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validar tipo de dato."""
        type_mappings = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'email': str,  # Validado por separado
            'password': str,  # Validado por separado
            'ip_address': str  # Validado por separado
        }

        expected_python_type = type_mappings.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Tipo desconocido, asumir válido

    async def _validate_security(
        self,
        data: Dict[str, Any],
        security_rules: Dict[str, Any],
        result: ValidationResult,
        context: Dict[str, Any]
    ):
        """Validaciones de seguridad."""
        # Sanitización de inputs
        if security_rules.get('sanitize_inputs', True):
            for field in data:
                if isinstance(data[field], str):
                    data[field] = self.security_validator.sanitize_input(data[field])

        # Detección de SQL injection básica
        if security_rules.get('check_sql_injection', True):
            for field, value in data.items():
                if isinstance(value, str) and self._detect_sql_injection(value):
                    result.add_error(ValidationError(
                        code=ValidationErrorCode.SUSPICIOUS_ACTIVITY,
                        message=f"Contenido sospechoso detectado en '{field}'",
                        field=field
                    ))

        # Detección de XSS básica
        if security_rules.get('check_xss', True):
            for field, value in data.items():
                if isinstance(value, str) and self._detect_xss(value):
                    result.add_error(ValidationError(
                        code=ValidationErrorCode.SUSPICIOUS_ACTIVITY,
                        message=f"Contenido potencialmente peligroso detectado en '{field}'",
                        field=field
                    ))

    def _detect_sql_injection(self, value: str) -> bool:
        """Detección básica de SQL injection."""
        sql_patterns = [
            r';\s*(drop|delete|update|insert|alter)\s',
            r'union\s+select',
            r'--\s*$',
            r'/\*.*\*/',
            r'xp_cmdshell',
            r'exec\s*\(',
        ]

        value_lower = value.lower()
        for pattern in sql_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    def _detect_xss(self, value: str) -> bool:
        """Detección básica de XSS."""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]

        value_lower = value.lower()
        for pattern in xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    async def _validate_business(
        self,
        data: Dict[str, Any],
        business_rules: Dict[str, Any],
        result: ValidationResult,
        context: Dict[str, Any]
    ):
        """Validaciones de negocio."""
        # Aquí irían validaciones específicas del negocio
        # Por ejemplo: verificar saldo, límites de transacción, etc.
        pass

    async def _audit_validation(
        self,
        request_data: Dict[str, Any],
        validation_rules: Dict[str, Any],
        result: ValidationResult,
        context: Dict[str, Any]
    ):
        """Registrar auditoría de validación."""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'request_data': self._sanitize_for_audit(request_data),
            'validation_rules': validation_rules,
            'result': result.to_dict(),
            'context': context,
            'errors_count': len(result.errors),
            'warnings_count': len(result.warnings)
        }

        self.audit_log.append(audit_entry)

        # Log structured
        logger.info(
            "Validation completed",
            validation_result=result.is_valid,
            errors_count=len(result.errors),
            warnings_count=len(result.warnings),
            user_id=context.get('user_id'),
            ip_address=context.get('ip'),
            endpoint=context.get('endpoint')
        )

        # Mantener tamaño del log limitado
        max_audit_entries = self.config.get('max_audit_entries', 10000)
        if len(self.audit_log) > max_audit_entries:
            self.audit_log = self.audit_log[-max_audit_entries:]

    def _sanitize_for_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar datos sensibles para auditoría."""
        sanitized = {}
        sensitive_fields = {'password', 'token', 'secret', 'key', 'private_key'}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_for_audit(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_for_audit({'item': item})['item'] if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener log de auditoría."""
        return self.audit_log[-limit:]

    def clear_audit_log(self):
        """Limpiar log de auditoría."""
        self.audit_log.clear()


# Instancia global
advanced_validator = AdvancedValidator()


def get_advanced_validator() -> AdvancedValidator:
    """Obtener instancia global del validador avanzado."""
    return advanced_validator