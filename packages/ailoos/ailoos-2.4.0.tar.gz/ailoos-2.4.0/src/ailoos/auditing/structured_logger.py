"""
Sistema de logging estructurado para todas las operaciones de AILOOS.
Proporciona logging consistente y detallado para debugging, monitoreo y auditoría.
"""

import asyncio
import logging
import json
import sys
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import structlog
from pythonjsonlogger import jsonlogger

from ..core.logging import get_logger
from .audit_manager import get_audit_manager, AuditEventType, SecurityAlertLevel
from ..core.config import get_config

logger = get_logger(__name__)


@dataclass
class LogContext:
    """Contexto de logging estructurado."""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    resource: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    start_time: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir contexto a diccionario."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "operation": self.operation,
            "resource": self.resource,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "tags": self.tags,
            "metadata": self.metadata
        }


class StructuredLogger:
    """
    Logger estructurado que integra con el sistema de auditoría.
    Proporciona logging consistente para todas las operaciones del sistema.
    """

    def __init__(self, name: str, audit_events: bool = True):
        self.name = name
        self.audit_events = audit_events
        self.audit_manager = get_audit_manager() if audit_events else None
        self.config = get_config()

        # Configurar logger subyacente
        self.logger = logging.getLogger(f"ailoos.structured.{name}")
        self._setup_logger()

        # Contexto de thread local
        self._local = threading.local()

    def _setup_logger(self):
        """Configurar el logger subyacente."""
        # Evitar configuración duplicada
        if self.logger.handlers:
            return

        # Formato JSON para producción
        json_format = getattr(self.config, 'json_logging', False)
        if json_format:
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Handler para archivo si está configurado
        log_file = getattr(self.config, 'structured_log_file', './logs/structured.log')
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=100*1024*1024,  # 100MB
                backupCount=10
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Configurar nivel
        level = getattr(logging, getattr(self.config, 'log_level', 'INFO').upper(), logging.INFO)
        self.logger.setLevel(level)

    @property
    def context(self) -> LogContext:
        """Obtener contexto del thread actual."""
        if not hasattr(self._local, 'context'):
            self._local.context = LogContext()
        return self._local.context

    @context.setter
    def context(self, ctx: LogContext):
        """Establecer contexto del thread actual."""
        self._local.context = ctx

    def with_context(self, **kwargs) -> 'StructuredLogger':
        """Crear logger con contexto adicional."""
        new_logger = StructuredLogger(self.name, self.audit_events)
        new_logger.context = LogContext(**kwargs)
        return new_logger

    def start_operation(self, operation: str, resource: str = None, **metadata) -> str:
        """
        Iniciar una operación y crear contexto.

        Returns:
            ID de la operación/request
        """
        import secrets

        request_id = secrets.token_hex(8)
        start_time = datetime.now()

        self.context.request_id = request_id
        self.context.operation = operation
        self.context.resource = resource or operation
        self.context.start_time = start_time
        self.context.metadata.update(metadata)

        self.info(f"Started operation: {operation}",
                 operation=operation,
                 resource=resource,
                 request_id=request_id,
                 **metadata)

        return request_id

    def end_operation(self, success: bool = True, result: Any = None, error: Exception = None):
        """Finalizar operación."""
        if not self.context.start_time:
            return

        duration = (datetime.now() - self.context.start_time).total_seconds() * 1000  # ms

        log_data = {
            "operation": self.context.operation,
            "resource": self.context.resource,
            "request_id": self.context.request_id,
            "duration_ms": duration,
            "success": success
        }

        if result is not None:
            log_data["result"] = str(result)[:500]  # Limitar tamaño

        if error:
            log_data["error"] = str(error)
            log_data["error_type"] = type(error).__name__

        if success:
            self.info(f"Completed operation: {self.context.operation}", **log_data)
        else:
            self.error(f"Failed operation: {self.context.operation}", **log_data)

        # Registrar en auditoría si está habilitado
        if self.audit_events and self.audit_manager:
            audit_event_type = AuditEventType.SYSTEM_OPERATION
            severity = SecurityAlertLevel.LOW

            if not success:
                severity = SecurityAlertLevel.MEDIUM if isinstance(error, Exception) else SecurityAlertLevel.HIGH

            self.audit_manager.log_event(
                event_type=audit_event_type,
                resource=self.context.resource or "unknown",
                action=self.context.operation or "unknown",
                user_id=self.context.user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                details={
                    "request_id": self.context.request_id,
                    "duration_ms": duration,
                    "success": success,
                    "result": str(result)[:200] if result else None,
                    "error": str(error) if error else None,
                    **self.context.metadata
                },
                severity=severity,
                success=success,
                processing_time_ms=duration
            )

        # Limpiar contexto
        self.context.start_time = None

    def log_api_request(self, method: str, endpoint: str, status_code: int,
                       duration_ms: float, user_id: Optional[str] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log específico para requests API."""
        severity = SecurityAlertLevel.LOW
        if status_code >= 500:
            severity = SecurityAlertLevel.HIGH
        elif status_code >= 400:
            severity = SecurityAlertLevel.MEDIUM

        log_data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        if status_code >= 400:
            self.warning(f"API Request: {method} {endpoint} -> {status_code}", **log_data)
        else:
            self.info(f"API Request: {method} {endpoint} -> {status_code}", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            self.audit_manager.log_event(
                event_type=AuditEventType.SYSTEM_OPERATION,
                resource=f"api:{endpoint}",
                action=f"{method.lower()}_request",
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=log_data,
                severity=severity,
                success=status_code < 400,
                processing_time_ms=duration_ms
            )

    def log_security_event(self, event_type: str, details: Dict[str, Any],
                          severity: SecurityAlertLevel = SecurityAlertLevel.MEDIUM):
        """Log específico para eventos de seguridad."""
        log_data = {
            "security_event_type": event_type,
            "severity": severity.value,
            **details
        }

        if severity == SecurityAlertLevel.CRITICAL:
            self.critical(f"Security Event: {event_type}", **log_data)
        elif severity == SecurityAlertLevel.HIGH:
            self.error(f"Security Event: {event_type}", **log_data)
        elif severity == SecurityAlertLevel.MEDIUM:
            self.warning(f"Security Event: {event_type}", **log_data)
        else:
            self.info(f"Security Event: {event_type}", **log_data)

        # Registrar en auditoría como alerta de seguridad
        if self.audit_events and self.audit_manager:
            self.audit_manager.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                resource="security",
                action=event_type,
                user_id=self.context.user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                details={
                    "alert_type": event_type,
                    **details,
                    **self.context.metadata
                },
                severity=severity,
                success=False  # Eventos de seguridad generalmente indican problemas
            )

    def log_config_change(self, key: str, old_value: Any, new_value: Any,
                         changed_by: str, reason: str = ""):
        """Log específico para cambios de configuración."""
        log_data = {
            "config_key": key,
            "old_value": str(old_value)[:200] if old_value is not None else None,
            "new_value": str(new_value)[:200] if new_value is not None else None,
            "changed_by": changed_by,
            "change_reason": reason
        }

        self.info(f"Config change: {key}", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            severity = SecurityAlertLevel.LOW
            # Verificar si es configuración sensible
            sensitive_keys = ['password', 'secret', 'key', 'token', 'jwt', 'encryption']
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                severity = SecurityAlertLevel.MEDIUM

            self.audit_manager.log_event(
                event_type=AuditEventType.CONFIG_CHANGE,
                resource=f"config:{key}",
                action="change",
                user_id=changed_by,
                details=log_data,
                severity=severity,
                success=True
            )

    def log_user_action(self, action: str, user_id: str, resource: str,
                        details: Optional[Dict[str, Any]] = None):
        """Log específico para acciones de usuario."""
        log_data = {
            "action": action,
            "user_id": user_id,
            "resource": resource,
            **(details or {})
        }

        self.info(f"User action: {action} on {resource}", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            self.audit_manager.log_event(
                event_type=AuditEventType.USER_ACTION,
                resource=resource,
                action=action,
                user_id=user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                user_agent=self.context.user_agent,
                details=details or {},
                severity=SecurityAlertLevel.LOW,
                success=True
            )

    def log_kg_operation(self, operation: str, details: Dict[str, Any],
                        user_id: Optional[str] = None, success: bool = True,
                        processing_time_ms: Optional[float] = None):
        """Log específico para operaciones de Knowledge Graph."""
        log_data = {
            "kg_operation": operation,
            "success": success,
            **details
        }

        if processing_time_ms:
            log_data["processing_time_ms"] = processing_time_ms

        if success:
            self.info(f"KG Operation: {operation}", **log_data)
        else:
            self.warning(f"KG Operation failed: {operation}", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            event_type = AuditEventType.KNOWLEDGE_GRAPH_OPERATION
            severity = SecurityAlertLevel.LOW if success else SecurityAlertLevel.MEDIUM

            self.audit_manager.log_event(
                event_type=event_type,
                resource="knowledge_graph",
                action=operation,
                user_id=user_id or self.context.user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                details=log_data,
                severity=severity,
                success=success,
                processing_time_ms=processing_time_ms
            )

    def log_kg_query(self, query: str, language: str, result_count: int,
                    execution_time_ms: float, user_id: Optional[str] = None,
                    optimized: bool = False, parameters: Optional[Dict[str, Any]] = None):
        """Log específico para consultas de Knowledge Graph."""
        log_data = {
            "query": query[:500] if len(query) > 500 else query,  # Limitar tamaño
            "language": language,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "optimized": optimized,
            "parameters": parameters or {}
        }

        self.info(f"KG Query: {language} -> {result_count} results", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_QUERY,
                resource="knowledge_graph",
                action="execute_query",
                user_id=user_id or self.context.user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                details=log_data,
                severity=SecurityAlertLevel.LOW,
                success=True,
                processing_time_ms=execution_time_ms
            )

    def log_kg_inference(self, inference_type: str, rules_applied: int,
                        triples_inferred: int, execution_time_ms: float,
                        user_id: Optional[str] = None, confidence_score: float = 1.0):
        """Log específico para operaciones de inferencia de Knowledge Graph."""
        log_data = {
            "inference_type": inference_type,
            "rules_applied": rules_applied,
            "triples_inferred": triples_inferred,
            "execution_time_ms": execution_time_ms,
            "confidence_score": confidence_score
        }

        self.info(f"KG Inference: {inference_type} -> {triples_inferred} triples", **log_data)

        # Registrar en auditoría
        if self.audit_events and self.audit_manager:
            severity = SecurityAlertLevel.LOW
            if triples_inferred > 1000:  # Inferencia masiva
                severity = SecurityAlertLevel.MEDIUM

            self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_INFERENCE,
                resource="knowledge_graph",
                action="inference",
                user_id=user_id or self.context.user_id,
                session_id=self.context.session_id,
                ip_address=self.context.ip_address,
                details=log_data,
                severity=severity,
                success=True,
                processing_time_ms=execution_time_ms
            )

    def log_performance(self, operation: str, duration_ms: float, **metrics):
        """Log de métricas de rendimiento."""
        log_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            **metrics
        }

        # Determinar nivel basado en rendimiento
        if duration_ms > 5000:  # Más de 5 segundos
            self.warning(f"Slow operation: {operation}", **log_data)
        elif duration_ms > 1000:  # Más de 1 segundo
            self.info(f"Slow operation: {operation}", **log_data)
        else:
            self.debug(f"Performance: {operation}", **log_data)

        # Registrar tiempo de respuesta en el audit manager
        if self.audit_manager:
            self.audit_manager.track_response_time(duration_ms)

    def log_error(self, error: Exception, operation: str = None, **context):
        """Log estructurado de errores."""
        operation = operation or self.context.operation or "unknown"

        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "operation": operation,
            "traceback": self._get_traceback(error),
            **context
        }

        self.error(f"Error in {operation}: {type(error).__name__}", **log_data)

        # Registrar error en audit manager
        if self.audit_manager:
            self.audit_manager.track_error(type(error).__name__)

        # Registrar en auditoría si es error crítico
        if self.audit_events and self.audit_manager:
            severity = SecurityAlertLevel.MEDIUM
            # Determinar severidad basada en tipo de error
            if isinstance(error, (SystemExit, KeyboardInterrupt)):
                severity = SecurityAlertLevel.LOW
            elif isinstance(error, (ConnectionError, TimeoutError)):
                severity = SecurityAlertLevel.MEDIUM
            else:
                severity = SecurityAlertLevel.HIGH

            self.audit_manager.log_event(
                event_type=AuditEventType.SYSTEM_OPERATION,
                resource="error_handler",
                action="error_occurred",
                user_id=self.context.user_id,
                details=log_data,
                severity=severity,
                success=False
            )

    def _get_traceback(self, error: Exception) -> str:
        """Obtener traceback formateado."""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    # Métodos de logging estándar con contexto
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log('debug', message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log('info', message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log('warning', message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log('error', message, kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log('critical', message, kwargs)

    def _log(self, level: str, message: str, extra: Dict[str, Any]):
        """Método interno para logging estructurado."""
        # Combinar contexto con datos extra
        log_data = {
            **self.context.to_dict(),
            **extra
        }

        # Filtrar valores None
        log_data = {k: v for k, v in log_data.items() if v is not None}

        # Log con el logger subyacente
        log_method = getattr(self.logger, level)
        log_method(message, extra=log_data)


# Logger global estructurado
_structured_loggers = {}


def get_structured_logger(name: str, audit_events: bool = True) -> StructuredLogger:
    """Obtener logger estructurado."""
    global _structured_loggers

    key = f"{name}:{audit_events}"
    if key not in _structured_loggers:
        _structured_loggers[key] = StructuredLogger(name, audit_events)

    return _structured_loggers[key]


# Funciones de conveniencia para logging común
def log_api_request(method: str, endpoint: str, status_code: int, duration_ms: float, **context):
    """Función de conveniencia para logging de API."""
    logger = get_structured_logger("api")
    logger.log_api_request(method, endpoint, status_code, duration_ms, **context)


def log_security_event(event_type: str, details: Dict[str, Any], severity: SecurityAlertLevel = SecurityAlertLevel.MEDIUM):
    """Función de conveniencia para logging de seguridad."""
    logger = get_structured_logger("security")
    logger.log_security_event(event_type, details, severity)


def log_config_change(key: str, old_value: Any, new_value: Any, changed_by: str, reason: str = ""):
    """Función de conveniencia para logging de configuración."""
    logger = get_structured_logger("config")
    logger.log_config_change(key, old_value, new_value, changed_by, reason)


def log_user_action(action: str, user_id: str, resource: str, **details):
    """Función de conveniencia para logging de acciones de usuario."""
    logger = get_structured_logger("user")
    logger.log_user_action(action, user_id, resource, details)


def log_performance(operation: str, duration_ms: float, **metrics):
    """Función de conveniencia para logging de rendimiento."""
    logger = get_structured_logger("performance")
    logger.log_performance(operation, duration_ms, **metrics)


def log_kg_operation(operation: str, details: Dict[str, Any], **context):
    """Función de conveniencia para logging de operaciones KG."""
    logger = get_structured_logger("knowledge_graph")
    logger.log_kg_operation(operation, details, **context)


def log_kg_query(query: str, language: str, result_count: int, execution_time_ms: float, **context):
    """Función de conveniencia para logging de consultas KG."""
    logger = get_structured_logger("knowledge_graph")
    logger.log_kg_query(query, language, result_count, execution_time_ms, **context)


def log_kg_inference(inference_type: str, rules_applied: int, triples_inferred: int, execution_time_ms: float, **context):
    """Función de conveniencia para logging de inferencias KG."""
    logger = get_structured_logger("knowledge_graph")
    logger.log_kg_inference(inference_type, rules_applied, triples_inferred, execution_time_ms, **context)


# Decorador para operaciones
def log_operation(operation_name: str = None, log_performance: bool = True):
    """Decorador para logging automático de operaciones."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            request_id = logger.start_operation(op_name)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                if log_performance:
                    duration = (time.time() - start_time) * 1000
                    logger.log_performance(op_name, duration)
                logger.end_operation(success=True, result=result)
                return result
            except Exception as e:
                if log_performance:
                    duration = (time.time() - start_time) * 1000
                    logger.log_performance(op_name, duration, error=str(e))
                logger.end_operation(success=False, error=e)
                raise

        def sync_wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            request_id = logger.start_operation(op_name)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                if log_performance:
                    duration = (time.time() - start_time) * 1000
                    logger.log_performance(op_name, duration)
                logger.end_operation(success=True, result=result)
                return result
            except Exception as e:
                if log_performance:
                    duration = (time.time() - start_time) * 1000
                    logger.log_performance(op_name, duration, error=str(e))
                logger.end_operation(success=False, error=e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator