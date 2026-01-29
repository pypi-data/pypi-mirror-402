"""
Validador de seguridad avanzado para AILOOS.
Validaciones especializadas para contraseñas, datos sensibles y seguridad.
"""

import re
import hashlib
import secrets
import string
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import ipaddress
import bcrypt

from ..core.logging import get_logger
from ..core.config import get_config

logger = get_logger(__name__)


@dataclass
class PasswordPolicy:
    """Política de contraseñas."""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = False
    min_entropy: float = 50.0
    prevent_common_passwords: bool = True
    prevent_personal_info: bool = True
    max_consecutive_chars: int = 3
    history_check: int = 5  # Número de contraseñas anteriores a verificar

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_digits": self.require_digits,
            "require_special_chars": self.require_special_chars,
            "min_entropy": self.min_entropy,
            "prevent_common_passwords": self.prevent_common_passwords,
            "prevent_personal_info": self.prevent_personal_info,
            "max_consecutive_chars": self.max_consecutive_chars,
            "history_check": self.history_check
        }


@dataclass
class SecurityValidationResult:
    """Resultado de validación de seguridad."""
    is_valid: bool
    score: float  # 0-100, donde 100 es más seguro
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "issues": self.issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }


class AdvancedSecurityValidator:
    """
    Validador de seguridad avanzado con múltiples capas de validación.
    """

    def __init__(self):
        self.config = get_config()
        self.common_passwords = self._load_common_passwords()
        self.breached_passwords = self._load_breached_passwords()
        self.password_policy = self._load_password_policy()

    def _load_common_passwords(self) -> Set[str]:
        """Cargar lista de contraseñas comunes."""
        try:
            # En producción, esto podría cargarse desde un archivo o base de datos
            return {
                "password", "123456", "123456789", "qwerty", "abc123",
                "password123", "admin", "letmein", "welcome", "monkey",
                "1234567890", "password1", "qwerty123", "welcome123",
                "admin123", "root", "user", "guest", "test", "demo",
                "111111", "12345678", "1234567", "qwertyuiop", "asdfghjkl",
                "zxcvbnm", "password123456", "12345678910", "superman", "batman"
            }
        except Exception as e:
            logger.warning(f"Error loading common passwords: {e}")
            return set()

    def _load_breached_passwords(self) -> Set[str]:
        """Cargar hashes de contraseñas comprometidas (HaveIBeenPwned style)."""
        # En producción, esto sería una base de datos de hashes SHA-1
        # Por simplicidad, usamos un set vacío
        return set()

    def _load_password_policy(self) -> PasswordPolicy:
        """Cargar política de contraseñas desde configuración."""
        # Nota: La configuración actual no incluye políticas de contraseña,
        # usar valores por defecto seguros
        return PasswordPolicy(
            min_length=8,
            max_length=128,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_special_chars=False,
            min_entropy=50.0,
            prevent_common_passwords=True,
            prevent_personal_info=True,
            max_consecutive_chars=3,
            history_check=5
        )

    def validate_password_comprehensive(
        self,
        password: str,
        user_context: Optional[Dict[str, Any]] = None,
        check_history: Optional[List[str]] = None
    ) -> SecurityValidationResult:
        """
        Validación completa de contraseña.

        Args:
            password: Contraseña a validar
            user_context: Información contextual del usuario
            check_history: Lista de hashes de contraseñas anteriores

        Returns:
            Resultado detallado de validación
        """
        result = SecurityValidationResult(is_valid=True, score=100.0)
        issues = []
        warnings = []
        suggestions = []

        # 1. Validaciones básicas de longitud
        if len(password) < self.password_policy.min_length:
            issues.append(f"La contraseña debe tener al menos {self.password_policy.min_length} caracteres")
            result.score -= 30

        if len(password) > self.password_policy.max_length:
            issues.append(f"La contraseña no puede exceder {self.password_policy.max_length} caracteres")
            result.score -= 10

        # 2. Verificar composición de caracteres
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

        if self.password_policy.require_uppercase and not has_upper:
            issues.append("La contraseña debe contener al menos una letra mayúscula")
            result.score -= 15

        if self.password_policy.require_lowercase and not has_lower:
            issues.append("La contraseña debe contener al menos una letra minúscula")
            result.score -= 15

        if self.password_policy.require_digits and not has_digit:
            issues.append("La contraseña debe contener al menos un número")
            result.score -= 15

        if self.password_policy.require_special_chars and not has_special:
            issues.append("La contraseña debe contener al menos un carácter especial")
            result.score -= 10

        # 3. Verificar caracteres consecutivos
        if self._has_consecutive_chars(password, self.password_policy.max_consecutive_chars):
            warnings.append(f"La contraseña contiene más de {self.password_policy.max_consecutive_chars} caracteres consecutivos")
            result.score -= 10

        # 4. Verificar contraseñas comunes
        if self.password_policy.prevent_common_passwords:
            if password.lower() in self.common_passwords:
                issues.append("Esta contraseña es muy común y fácil de adivinar")
                result.score -= 40

        # 5. Verificar contraseñas comprometidas
        password_sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        if password_sha1 in self.breached_passwords:
            issues.append("Esta contraseña ha sido encontrada en brechas de seguridad")
            result.score -= 50

        # 6. Verificar información personal
        if self.password_policy.prevent_personal_info and user_context:
            personal_matches = self._check_personal_info(password, user_context)
            if personal_matches:
                warnings.append("La contraseña contiene información personal")
                result.score -= 15
                suggestions.append("Evite usar información personal en su contraseña")

        # 7. Calcular entropía
        entropy = self._calculate_password_entropy(password)
        if entropy < self.password_policy.min_entropy:
            warnings.append(f"La contraseña tiene baja entropía ({entropy:.1f})")
            result.score -= 20
            suggestions.append("Use una combinación de letras mayúsculas, minúsculas, números y símbolos")

        # 8. Verificar historial de contraseñas
        if check_history:
            for old_hash in check_history[-self.password_policy.history_check:]:
                if self._verify_password_against_hash(password, old_hash):
                    issues.append("Esta contraseña ya ha sido usada anteriormente")
                    result.score -= 25
                    break

        # 9. Generar sugerencias adicionales
        if result.score < 80:
            suggestions.extend([
                "Use una frase de contraseña memorable",
                "Considere usar un gestor de contraseñas",
                "Combine palabras con números y símbolos"
            ])

        # Actualizar resultado
        result.issues = issues
        result.warnings = warnings
        result.suggestions = list(set(suggestions))  # Remover duplicados
        result.is_valid = len(issues) == 0
        result.score = max(0, min(100, result.score))

        # Metadata
        result.metadata = {
            "length": len(password),
            "entropy": entropy,
            "has_upper": has_upper,
            "has_lower": has_lower,
            "has_digit": has_digit,
            "has_special": has_special,
            "complexity_score": self._calculate_complexity_score(password),
            "estimated_crack_time": self._estimate_crack_time(password)
        }

        return result

    def _has_consecutive_chars(self, password: str, max_consecutive: int) -> bool:
        """Verificar si hay caracteres consecutivos."""
        for i in range(len(password) - max_consecutive + 1):
            chars = password[i:i + max_consecutive]
            if all(ord(chars[j]) == ord(chars[j-1]) + 1 for j in range(1, len(chars))):
                return True
            if all(ord(chars[j]) == ord(chars[j-1]) - 1 for j in range(1, len(chars))):
                return True
        return False

    def _check_personal_info(self, password: str, user_context: Dict[str, Any]) -> List[str]:
        """Verificar si la contraseña contiene información personal."""
        matches = []
        password_lower = password.lower()

        # Extraer información personal
        personal_info = set()

        if 'username' in user_context and user_context['username']:
            personal_info.update(user_context['username'].lower().split())

        if 'email' in user_context and user_context['email']:
            email_parts = user_context['email'].split('@')[0].lower()
            personal_info.add(email_parts)

        if 'first_name' in user_context and user_context['first_name']:
            personal_info.add(user_context['first_name'].lower())

        if 'last_name' in user_context and user_context['last_name']:
            personal_info.add(user_context['last_name'].lower())

        if 'phone' in user_context and user_context['phone']:
            # Extraer últimos 4 dígitos del teléfono
            phone_digits = re.sub(r'\D', '', user_context['phone'])
            if len(phone_digits) >= 4:
                personal_info.add(phone_digits[-4:])

        if 'birth_year' in user_context and user_context['birth_year']:
            personal_info.add(str(user_context['birth_year']))

        # Verificar coincidencias
        for info in personal_info:
            if len(info) > 2 and info in password_lower:
                matches.append(info)

        return matches

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
            charset_size += 32

        if charset_size == 0:
            charset_size = 26

        # Entropía = log2(charset_size ^ length)
        import math
        return math.log2(charset_size) * len(password)

    def _calculate_complexity_score(self, password: str) -> float:
        """Calcular puntuación de complejidad (0-100)."""
        score = 0

        # Longitud
        length_score = min(40, len(password) * 2)
        score += length_score

        # Variedad de caracteres
        char_types = 0
        if re.search(r'[a-z]', password): char_types += 1
        if re.search(r'[A-Z]', password): char_types += 1
        if re.search(r'\d', password): char_types += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): char_types += 1

        variety_score = char_types * 15
        score += variety_score

        # Penalizaciones
        if password.lower() in self.common_passwords:
            score -= 30
        if self._has_consecutive_chars(password, 3):
            score -= 10

        return max(0, min(100, score))

    def _estimate_crack_time(self, password: str) -> str:
        """Estimar tiempo para crackear la contraseña."""
        entropy = self._calculate_password_entropy(password)

        # Suponiendo 1 billón de intentos por segundo (supercomputadora)
        attempts_per_second = 1_000_000_000
        total_attempts = 2 ** entropy
        seconds = total_attempts / attempts_per_second

        if seconds < 1:
            return "instantáneo"
        elif seconds < 60:
            return f"{seconds:.1f} segundos"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutos"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} horas"
        elif seconds < 31536000:
            return f"{seconds/86400:.1f} días"
        else:
            return f"{seconds/31536000:.1f} años"

    def _verify_password_against_hash(self, password: str, hash_str: str) -> bool:
        """Verificar contraseña contra hash."""
        try:
            return bcrypt.checkpw(password.encode(), hash_str.encode())
        except:
            return False

    def validate_data_sensitivity(self, data: Dict[str, Any]) -> SecurityValidationResult:
        """
        Validar sensibilidad de datos.

        Args:
            data: Datos a validar

        Returns:
            Resultado de validación de sensibilidad
        """
        result = SecurityValidationResult(is_valid=True, score=100.0)
        sensitive_fields = []

        # Patrones de datos sensibles
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'api_key': r'\b[A-Za-z0-9]{20,}\b',  # Simplificado
        }

        for key, value in data.items():
            if isinstance(value, str):
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, value, re.IGNORECASE):
                        sensitive_fields.append({
                            'field': key,
                            'type': pattern_name,
                            'value': self._mask_sensitive_value(value, pattern_name)
                        })
                        result.score -= 20

        if sensitive_fields:
            result.warnings.append(f"Se detectaron {len(sensitive_fields)} campos potencialmente sensibles")
            result.metadata['sensitive_fields'] = sensitive_fields
            result.suggestions.append("Considere encriptar o anonimizar datos sensibles")

        result.is_valid = result.score >= 60  # Umbral arbitrario

        return result

    def _mask_sensitive_value(self, value: str, type_hint: str) -> str:
        """Enmascarar valor sensible para logging."""
        if type_hint == 'email':
            parts = value.split('@')
            if len(parts) == 2:
                return f"{'*' * len(parts[0])}@{parts[1]}"
        elif type_hint in ['phone', 'ssn', 'credit_card']:
            return '*' * len(value)
        elif type_hint == 'ip_address':
            return '***.***.***.***'
        else:
            return '*' * min(len(value), 10) + ('...' if len(value) > 10 else '')

        return '***'

    def validate_input_sanitization(self, input_str: str) -> SecurityValidationResult:
        """
        Validar sanitización de entrada.

        Args:
            input_str: Cadena de entrada a validar

        Returns:
            Resultado de validación de sanitización
        """
        result = SecurityValidationResult(is_valid=True, score=100.0)

        # Verificar caracteres de control
        control_chars = re.findall(r'[\x00-\x1f\x7f-\x9f]', input_str)
        if control_chars:
            result.warnings.append(f"Se detectaron {len(control_chars)} caracteres de control")
            result.score -= 10

        # Verificar scripts potencialmente peligrosos
        dangerous_patterns = [
            (r'<script[^>]*>.*?</script>', 'script tags'),
            (r'javascript:', 'javascript URLs'),
            (r'on\w+\s*=', 'event handlers'),
            (r'<iframe[^>]*>', 'iframe tags'),
            (r'<object[^>]*>', 'object tags'),
            (r'<embed[^>]*>', 'embed tags'),
            (r'union\s+select', 'SQL injection'),
            (r';\s*drop\s', 'SQL injection'),
            (r'xp_cmdshell', 'SQL injection'),
            (r'eval\s*\(', 'code injection'),
            (r'exec\s*\(', 'code injection'),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, input_str, re.IGNORECASE | re.DOTALL):
                result.issues.append(f"Se detectó patrón peligroso: {description}")
                result.score -= 30

        # Verificar longitud excesiva
        if len(input_str) > 10000:
            result.warnings.append("Entrada excesivamente larga")
            result.score -= 5

        # Verificar URLs sospechosas
        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, input_str)
        for url in urls:
            if self._is_suspicious_url(url):
                result.warnings.append(f"URL potencialmente sospechosa: {url[:50]}...")
                result.score -= 15

        result.is_valid = len(result.issues) == 0

        return result

    def _is_suspicious_url(self, url: str) -> bool:
        """Determinar si una URL es sospechosa."""
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co',  # URL shorteners
            'pastebin.com', 'hastebin.com',  # Paste sites
            'onion', '.tk', '.ml', '.ga', '.cf'  # Suspicious TLDs
        ]

        url_lower = url.lower()
        for domain in suspicious_domains:
            if domain in url_lower:
                return True

        return False

    def generate_secure_password(self, length: int = 12) -> Tuple[str, SecurityValidationResult]:
        """
        Generar contraseña segura.

        Args:
            length: Longitud deseada

        Returns:
            Tupla de (contraseña, resultado de validación)
        """
        # Asegurar longitud mínima
        length = max(length, 12)

        # Generar contraseña con todos los tipos de caracteres
        chars = string.ascii_letters + string.digits + "!@#$%^&*"

        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))

            # Validar que cumple con requisitos
            result = self.validate_password_comprehensive(password)

            if result.is_valid and result.score >= 80:
                return password, result

    def hash_password(self, password: str) -> str:
        """Hashear contraseña de forma segura."""
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds es seguro y razonable
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, hash_str: str) -> bool:
        """Verificar contraseña contra hash."""
        try:
            return bcrypt.checkpw(password.encode(), hash_str.encode())
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def validate_ip_security(self, ip_str: str) -> SecurityValidationResult:
        """
        Validar seguridad de dirección IP.

        Args:
            ip_str: Dirección IP a validar

        Returns:
            Resultado de validación de IP
        """
        result = SecurityValidationResult(is_valid=True, score=100.0)

        try:
            ip_obj = ipaddress.ip_address(ip_str)

            # Verificar IPs privadas (podrían indicar ataques internos)
            if ip_obj.is_private:
                result.warnings.append("Dirección IP privada detectada")
                result.score -= 10

            # Verificar loopback
            if ip_obj.is_loopback:
                result.warnings.append("Dirección IP de loopback")
                result.score -= 5

            # Verificar IPs reservadas
            if ip_obj.is_reserved:
                result.warnings.append("Dirección IP reservada")
                result.score -= 15

            # Verificar listas negras conocidas (simplificado)
            blacklisted_ranges = [
                '10.0.0.0/8',  # RFC 1918
                '172.16.0.0/12',  # RFC 1918
                '192.168.0.0/16',  # RFC 1918
            ]

            for range_str in blacklisted_ranges:
                network = ipaddress.ip_network(range_str)
                if ip_obj in network:
                    result.warnings.append(f"IP en rango potencialmente problemático: {range_str}")
                    result.score -= 20

            result.metadata = {
                "ip_version": ip_obj.version,
                "is_private": ip_obj.is_private,
                "is_global": ip_obj.is_global,
                "is_loopback": ip_obj.is_loopback,
                "is_reserved": ip_obj.is_reserved
            }

        except ValueError:
            result.issues.append("Dirección IP inválida")
            result.is_valid = False
            result.score = 0

        return result

    def validate_tee_attestation(
        self,
        instance_name: str,
        project_id: str,
        zone: str,
        expected_measurements: Optional[Any] = None
    ) -> SecurityValidationResult:
        """
        Validar attestación remota de enclave TEE.

        Args:
            instance_name: Nombre de la instancia GCP
            project_id: ID del proyecto GCP
            zone: Zona de GCP
            expected_measurements: Mediciones esperadas (opcional)

        Returns:
            Resultado de validación de attestación TEE
        """
        from .tee_attestation_validator import get_tee_attestation_validator

        result = SecurityValidationResult(is_valid=False, score=0.0)

        try:
            tee_validator = get_tee_attestation_validator()
            attestation_result = tee_validator.validate_remote_attestation(
                instance_name=instance_name,
                project_id=project_id,
                zone=zone,
                expected_measurements=expected_measurements
            )

            result.is_valid = attestation_result.is_valid
            result.score = 100.0 if attestation_result.is_valid else 0.0
            result.issues = attestation_result.issues
            result.warnings = attestation_result.warnings
            result.metadata = {
                "attestation_type": "TEE_REMOTE",
                "instance_name": instance_name,
                "project_id": project_id,
                "zone": zone,
                **attestation_result.metadata
            }

            if attestation_result.is_valid:
                result.suggestions.append("Attestación TEE exitosa - enclave seguro")
            else:
                result.suggestions.append("Verificar configuración de enclave TEE")
                result.suggestions.append("Revisar mediciones de referencia")

        except Exception as e:
            logger.error(f"Error en validación de attestación TEE: {e}")
            result.issues.append(f"Error interno de attestación: {str(e)}")

        return result


# Instancia global
security_validator = AdvancedSecurityValidator()


def get_security_validator() -> AdvancedSecurityValidator:
    """Obtener instancia global del validador de seguridad."""
    return security_validator

# Alias for compatibility
SecurityValidator = AdvancedSecurityValidator