"""
Sistema de manejo de errores jerárquico para AILOOS.
Proporciona códigos de error específicos y manejo estructurado.
"""

import json
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Severidad de los errores."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorías de errores."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    EXTERNAL = "external"
    NETWORK = "network"
    DATABASE = "database"


@dataclass
class ErrorCode:
    """Código de error estructurado."""
    code: int
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    http_status: int
    description: str = ""
    suggested_actions: List[str] = field(default_factory=list)
    internal_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "http_status": self.http_status,
            "description": self.description,
            "suggested_actions": self.suggested_actions,
            "internal_only": self.internal_only
        }


class ErrorCodes:
    """Colección de códigos de error predefinidos."""

    # Errores generales (1000-1999)
    INVALID_INPUT = ErrorCode(
        code=1000,
        name="INVALID_INPUT",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Entrada inválida proporcionada",
        http_status=400,
        description="Los datos proporcionados no cumplen con los requisitos esperados",
        suggested_actions=["Verifique los datos enviados", "Consulte la documentación de la API"]
    )

    MISSING_REQUIRED_FIELD = ErrorCode(
        code=1001,
        name="MISSING_REQUIRED_FIELD",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Campo requerido faltante",
        http_status=400,
        description="Un campo obligatorio no fue proporcionado",
        suggested_actions=["Asegúrese de incluir todos los campos requeridos"]
    )

    INVALID_FORMAT = ErrorCode(
        code=1002,
        name="INVALID_FORMAT",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Formato de datos inválido",
        http_status=400,
        description="El formato de los datos no es válido",
        suggested_actions=["Verifique el formato requerido", "Consulte los ejemplos en la documentación"]
    )

    VALUE_OUT_OF_RANGE = ErrorCode(
        code=1003,
        name="VALUE_OUT_OF_RANGE",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Valor fuera del rango permitido",
        http_status=400,
        description="El valor proporcionado está fuera del rango aceptable",
        suggested_actions=["Verifique los límites permitidos", "Ajuste el valor según las especificaciones"]
    )

    DUPLICATE_VALUE = ErrorCode(
        code=1004,
        name="DUPLICATE_VALUE",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Valor duplicado no permitido",
        http_status=409,
        description="El valor ya existe y no se permiten duplicados",
        suggested_actions=["Use un valor único", "Verifique si el recurso ya existe"]
    )

    # Errores de autenticación (2000-2999)
    INVALID_CREDENTIALS = ErrorCode(
        code=2000,
        name="INVALID_CREDENTIALS",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        message="Credenciales inválidas",
        http_status=401,
        description="Las credenciales proporcionadas son incorrectas",
        suggested_actions=["Verifique usuario y contraseña", "Considere restablecer la contraseña"]
    )

    TOKEN_EXPIRED = ErrorCode(
        code=2001,
        name="TOKEN_EXPIRED",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        message="Token expirado",
        http_status=401,
        description="El token de autenticación ha expirado",
        suggested_actions=["Renueve el token", "Inicie sesión nuevamente"]
    )

    INSUFFICIENT_PERMISSIONS = ErrorCode(
        code=2002,
        name="INSUFFICIENT_PERMISSIONS",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        message="Permisos insuficientes",
        http_status=403,
        description="No tiene permisos para realizar esta acción",
        suggested_actions=["Contacte al administrador", "Verifique sus permisos"]
    )

    ACCOUNT_LOCKED = ErrorCode(
        code=2003,
        name="ACCOUNT_LOCKED",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Cuenta bloqueada",
        http_status=423,
        description="La cuenta ha sido bloqueada por seguridad",
        suggested_actions=["Contacte al soporte", "Espere el período de bloqueo"]
    )

    TWO_FACTOR_REQUIRED = ErrorCode(
        code=2004,
        name="TWO_FACTOR_REQUIRED",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        message="Autenticación de dos factores requerida",
        http_status=401,
        description="Se requiere código de verificación adicional",
        suggested_actions=["Ingrese el código de verificación", "Configure 2FA si no lo ha hecho"]
    )

    # Errores de seguridad (3000-3999)
    WEAK_PASSWORD = ErrorCode(
        code=3000,
        name="WEAK_PASSWORD",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Contraseña demasiado débil",
        http_status=400,
        description="La contraseña no cumple con los requisitos de seguridad",
        suggested_actions=["Use una contraseña más fuerte", "Incluya mayúsculas, números y símbolos"]
    )

    PASSWORD_COMPROMISED = ErrorCode(
        code=3001,
        name="PASSWORD_COMPROMISED",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.HIGH,
        message="Contraseña comprometida",
        http_status=400,
        description="Esta contraseña ha sido encontrada en brechas de seguridad",
        suggested_actions=["Use una contraseña única y segura", "Considere usar un gestor de contraseñas"]
    )

    SUSPICIOUS_ACTIVITY = ErrorCode(
        code=3002,
        name="SUSPICIOUS_ACTIVITY",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.HIGH,
        message="Actividad sospechosa detectada",
        http_status=400,
        description="Se detectó actividad potencialmente maliciosa",
        suggested_actions=["Verifique sus acciones", "Contacte al soporte si es un error"]
    )

    IP_BLOCKED = ErrorCode(
        code=3003,
        name="IP_BLOCKED",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.HIGH,
        message="Dirección IP bloqueada",
        http_status=403,
        description="Su dirección IP ha sido bloqueada",
        suggested_actions=["Contacte al soporte", "Use una conexión diferente"]
    )

    RATE_LIMIT_EXCEEDED = ErrorCode(
        code=3004,
        name="RATE_LIMIT_EXCEEDED",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Límite de tasa excedido",
        http_status=429,
        description="Demasiadas solicitudes en poco tiempo",
        suggested_actions=["Espere antes de reintentar", "Reduzca la frecuencia de solicitudes"]
    )

    # Errores de negocio (4000-4999)
    INSUFFICIENT_BALANCE = ErrorCode(
        code=4000,
        name="INSUFFICIENT_BALANCE",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.LOW,
        message="Saldo insuficiente",
        http_status=402,
        description="No tiene suficientes tokens para esta transacción",
        suggested_actions=["Aumente su saldo", "Reduzca el monto de la transacción"]
    )

    INVALID_TRANSACTION = ErrorCode(
        code=4001,
        name="INVALID_TRANSACTION",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.MEDIUM,
        message="Transacción inválida",
        http_status=400,
        description="La transacción no puede ser procesada",
        suggested_actions=["Verifique los detalles de la transacción", "Contacte al soporte"]
    )

    SESSION_FULL = ErrorCode(
        code=4002,
        name="SESSION_FULL",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.LOW,
        message="Sesión llena",
        http_status=409,
        description="La sesión ha alcanzado el límite máximo de participantes",
        suggested_actions=["Intente unirse a otra sesión", "Espere a que se libere espacio"]
    )

    MODEL_NOT_AVAILABLE = ErrorCode(
        code=4003,
        name="MODEL_NOT_AVAILABLE",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.MEDIUM,
        message="Modelo no disponible",
        http_status=503,
        description="El modelo solicitado no está disponible actualmente",
        suggested_actions=["Intente más tarde", "Use un modelo alternativo"]
    )

    DATASET_INVALID = ErrorCode(
        code=4004,
        name="DATASET_INVALID",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Dataset inválido",
        http_status=400,
        description="El dataset proporcionado no cumple con los requisitos",
        suggested_actions=["Verifique el formato del dataset", "Asegúrese de que cumpla con los estándares"]
    )

    # Errores de sistema (5000-5999)
    SERVICE_UNAVAILABLE = ErrorCode(
        code=5000,
        name="SERVICE_UNAVAILABLE",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.HIGH,
        message="Servicio no disponible",
        http_status=503,
        description="El servicio no está disponible temporalmente",
        suggested_actions=["Intente más tarde", "Contacte al soporte si persiste"]
    )

    DATABASE_ERROR = ErrorCode(
        code=5001,
        name="DATABASE_ERROR",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        message="Error de base de datos",
        http_status=500,
        description="Error interno de base de datos",
        suggested_actions=["Intente más tarde", "Contacte al soporte"],
        internal_only=True
    )

    EXTERNAL_API_ERROR = ErrorCode(
        code=5002,
        name="EXTERNAL_API_ERROR",
        category=ErrorCategory.EXTERNAL,
        severity=ErrorSeverity.MEDIUM,
        message="Error en servicio externo",
        http_status=502,
        description="Error al comunicarse con un servicio externo",
        suggested_actions=["Intente más tarde", "Contacte al soporte"]
    )

    CONFIGURATION_ERROR = ErrorCode(
        code=5003,
        name="CONFIGURATION_ERROR",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        message="Error de configuración",
        http_status=500,
        description="Error en la configuración del sistema",
        suggested_actions=["Contacte al administrador del sistema"],
        internal_only=True
    )


@dataclass
class ErrorContext:
    """Contexto adicional para errores."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    timestamp: Optional[datetime] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AiloosError:
    """Error estructurado de AILOOS."""
    error_code: ErrorCode
    context: ErrorContext
    original_error: Optional[Exception] = None
    custom_message: Optional[str] = None
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.context.timestamp is None:
            self.context.timestamp = datetime.utcnow()

    def to_dict(self, include_internal: bool = False) -> Dict[str, Any]:
        """Convertir error a diccionario para respuesta API."""
        error_dict = {
            "error": {
                "code": self.error_code.code,
                "name": self.error_code.name,
                "message": self.custom_message or self.error_code.message,
                "category": self.error_code.category.value,
                "severity": self.error_code.severity.value,
                "field": self.field,
                "details": self.details,
                "timestamp": self.context.timestamp.isoformat() if self.context.timestamp else None,
                "request_id": self.context.request_id
            }
        }

        # Incluir información adicional solo si no es internal_only
        if not self.error_code.internal_only or include_internal:
            error_dict["error"].update({
                "description": self.error_code.description,
                "suggested_actions": self.error_code.suggested_actions,
                "http_status": self.error_code.http_status
            })

        # Incluir contexto adicional para debugging (solo internal)
        if include_internal:
            error_dict["context"] = {
                "user_id": self.context.user_id,
                "session_id": self.context.session_id,
                "ip_address": self.context.ip_address,
                "endpoint": self.context.endpoint,
                "method": self.context.method,
                "user_agent": self.context.user_agent,
                "additional_data": self.context.additional_data
            }

            if self.original_error:
                error_dict["debug"] = {
                    "original_error": str(self.original_error),
                    "traceback": traceback.format_exc()
                }

        return error_dict

    def get_http_status(self) -> int:
        """Obtener código HTTP correspondiente."""
        return self.error_code.http_status

    def should_log(self) -> bool:
        """Determinar si el error debe ser logueado."""
        return self.error_code.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]

    def get_log_level(self) -> str:
        """Obtener nivel de log apropiado."""
        severity_map = {
            ErrorSeverity.LOW: "DEBUG",
            ErrorSeverity.MEDIUM: "WARNING",
            ErrorSeverity.HIGH: "ERROR",
            ErrorSeverity.CRITICAL: "CRITICAL"
        }
        return severity_map.get(self.error_code.severity, "INFO")


class ErrorHandler:
    """Manejador centralizado de errores."""

    def __init__(self):
        self.error_codes = self._build_error_code_map()
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def _build_error_code_map(self) -> Dict[int, ErrorCode]:
        """Construir mapa de códigos de error."""
        code_map = {}
        for attr_name in dir(ErrorCodes):
            if not attr_name.startswith('_'):
                error_code = getattr(ErrorCodes, attr_name)
                if isinstance(error_code, ErrorCode):
                    code_map[error_code.code] = error_code
        return code_map

    def create_error(
        self,
        error_code: Union[ErrorCode, int, str],
        context: Optional[ErrorContext] = None,
        original_error: Optional[Exception] = None,
        custom_message: Optional[str] = None,
        field: Optional[str] = None,
        **details
    ) -> AiloosError:
        """
        Crear un error estructurado.

        Args:
            error_code: Código de error (ErrorCode, int, o string)
            context: Contexto del error
            original_error: Error original si aplica
            custom_message: Mensaje personalizado
            field: Campo específico donde ocurrió el error
            **details: Detalles adicionales
        """
        # Resolver código de error
        if isinstance(error_code, str):
            # Buscar por nombre
            resolved_code = None
            for code_obj in self.error_codes.values():
                if code_obj.name == error_code:
                    resolved_code = code_obj
                    break
            if not resolved_code:
                resolved_code = ErrorCodes.INVALID_INPUT
        elif isinstance(error_code, int):
            resolved_code = self.error_codes.get(error_code, ErrorCodes.INVALID_INPUT)
        else:
            resolved_code = error_code

        # Crear contexto si no se proporcionó
        if context is None:
            context = ErrorContext()

        # Crear error
        error = AiloosError(
            error_code=resolved_code,
            context=context,
            original_error=original_error,
            custom_message=custom_message,
            field=field,
            details=details
        )

        return error

    async def handle_error(
        self,
        error: Union[AiloosError, Exception],
        context: Optional[ErrorContext] = None,
        log_error: bool = True
    ) -> AiloosError:
        """
        Manejar un error y convertirlo a AiloosError si es necesario.

        Args:
            error: Error a manejar
            context: Contexto adicional
            log_error: Si debe loguearse el error
        """
        # Convertir a AiloosError si es necesario
        if isinstance(error, AiloosError):
            ail_error = error
        else:
            # Mapear excepciones comunes
            ail_error = self._map_exception_to_error(error, context)

        # Actualizar contexto
        if context:
            ail_error.context = context

        # Loguear error
        if log_error and ail_error.should_log():
            await self._log_error(ail_error)

        # Registrar en auditoría
        await self._audit_error(ail_error)

        # Ejecutar handlers específicos de categoría
        await self._execute_error_handlers(ail_error)

        return ail_error

    def _map_exception_to_error(
        self,
        exception: Exception,
        context: Optional[ErrorContext] = None
    ) -> AiloosError:
        """Mapear excepciones comunes a códigos de error."""
        exception_type = type(exception).__name__

        # Mapeo de excepciones comunes
        exception_map = {
            "ValueError": ErrorCodes.INVALID_INPUT,
            "TypeError": ErrorCodes.INVALID_FORMAT,
            "KeyError": ErrorCodes.MISSING_REQUIRED_FIELD,
            "PermissionError": ErrorCodes.INSUFFICIENT_PERMISSIONS,
            "TimeoutError": ErrorCodes.SERVICE_UNAVAILABLE,
            "ConnectionError": ErrorCodes.NETWORK,
            "sqlite3.Error": ErrorCodes.DATABASE_ERROR,
            "psycopg2.Error": ErrorCodes.DATABASE_ERROR,
        }

        error_code = exception_map.get(exception_type, ErrorCodes.SERVICE_UNAVAILABLE)

        return self.create_error(
            error_code,
            context=context,
            original_error=exception,
            custom_message=str(exception)
        )

    async def _log_error(self, error: AiloosError):
        """Loguear error usando el sistema de logging."""
        log_level = error.get_log_level()
        log_message = f"[{error.error_code.category.value}] {error.error_code.name}: {error.custom_message or error.error_code.message}"

        # Crear diccionario de log estructurado
        log_data = {
            "error_code": error.error_code.code,
            "error_name": error.error_code.name,
            "category": error.error_code.category.value,
            "severity": error.error_code.severity.value,
            "field": error.field,
            "user_id": error.context.user_id,
            "session_id": error.context.session_id,
            "request_id": error.context.request_id,
            "ip_address": error.context.ip_address,
            "endpoint": error.context.endpoint,
            "method": error.context.method,
            "details": error.details
        }

        # Remover valores None
        log_data = {k: v for k, v in log_data.items() if v is not None}

        # Loguear
        if log_level == "DEBUG":
            logger.debug(log_message, **log_data)
        elif log_level == "INFO":
            logger.info(log_message, **log_data)
        elif log_level == "WARNING":
            logger.warning(log_message, **log_data)
        elif log_level == "ERROR":
            logger.error(log_message, **log_data)
        elif log_level == "CRITICAL":
            logger.critical(log_message, **log_data)

    async def _audit_error(self, error: AiloosError):
        """Registrar error en auditoría."""
        audit_entry = {
            "timestamp": error.context.timestamp.isoformat() if error.context.timestamp else datetime.utcnow().isoformat(),
            "error_code": error.error_code.code,
            "error_name": error.error_code.name,
            "category": error.error_code.category.value,
            "severity": error.error_code.severity.value,
            "message": error.custom_message or error.error_code.message,
            "field": error.field,
            "context": {
                "user_id": error.context.user_id,
                "session_id": error.context.session_id,
                "request_id": error.context.request_id,
                "ip_address": error.context.ip_address,
                "endpoint": error.context.endpoint,
                "method": error.context.method,
            },
            "details": error.details
        }

        self.audit_log.append(audit_entry)

        # Mantener log limitado
        max_entries = 10000
        if len(self.audit_log) > max_entries:
            self.audit_log = self.audit_log[-max_entries:]

    async def _execute_error_handlers(self, error: AiloosError):
        """Ejecutar handlers específicos de categoría."""
        handlers = self.error_handlers.get(error.error_code.category, [])
        for handler in handlers:
            try:
                await handler(error)
            except Exception as e:
                logger.error(f"Error en handler de {error.error_code.category}: {e}")

    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Registrar handler para una categoría de error."""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        self.error_handlers[category].append(handler)

    def get_error_code(self, code: Union[int, str]) -> Optional[ErrorCode]:
        """Obtener ErrorCode por código o nombre."""
        if isinstance(code, int):
            return self.error_codes.get(code)
        else:
            for error_code in self.error_codes.values():
                if error_code.name == code:
                    return error_code
        return None

    def get_audit_log(self, limit: int = 100, category: Optional[ErrorCategory] = None) -> List[Dict[str, Any]]:
        """Obtener log de auditoría."""
        filtered_log = self.audit_log
        if category:
            filtered_log = [entry for entry in filtered_log if entry["category"] == category.value]

        return filtered_log[-limit:]

    def clear_audit_log(self):
        """Limpiar log de auditoría."""
        self.audit_log.clear()

    def get_error_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores."""
        if not self.audit_log:
            return {"total_errors": 0}

        stats = {
            "total_errors": len(self.audit_log),
            "by_category": {},
            "by_severity": {},
            "by_code": {},
            "recent_errors": len([e for e in self.audit_log[-100:] if e["severity"] in ["high", "critical"]])
        }

        for entry in self.audit_log:
            # Por categoría
            cat = entry["category"]
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            # Por severidad
            sev = entry["severity"]
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1

            # Por código
            code = entry["error_code"]
            stats["by_code"][code] = stats["by_code"].get(code, 0) + 1

        return stats


# Instancia global
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Obtener instancia global del manejador de errores."""
    return error_handler


# Funciones de conveniencia
def create_validation_error(
    field: str,
    message: str,
    context: Optional[ErrorContext] = None
) -> AiloosError:
    """Crear error de validación."""
    return error_handler.create_error(
        ErrorCodes.INVALID_INPUT,
        context=context,
        custom_message=message,
        field=field
    )


def create_authentication_error(
    message: str = "Credenciales inválidas",
    context: Optional[ErrorContext] = None
) -> AiloosError:
    """Crear error de autenticación."""
    return error_handler.create_error(
        ErrorCodes.INVALID_CREDENTIALS,
        context=context,
        custom_message=message
    )


def create_authorization_error(
    message: str = "Permisos insuficientes",
    context: Optional[ErrorContext] = None
) -> AiloosError:
    """Crear error de autorización."""
    return error_handler.create_error(
        ErrorCodes.INSUFFICIENT_PERMISSIONS,
        context=context,
        custom_message=message
    )


def create_business_error(
    message: str,
    context: Optional[ErrorContext] = None
) -> AiloosError:
    """Crear error de negocio."""
    return error_handler.create_error(
        ErrorCodes.INVALID_TRANSACTION,
        context=context,
        custom_message=message
    )


def create_system_error(
    message: str,
    context: Optional[ErrorContext] = None
) -> AiloosError:
    """Crear error de sistema."""
    return error_handler.create_error(
        ErrorCodes.SERVICE_UNAVAILABLE,
        context=context,
        custom_message=message
    )