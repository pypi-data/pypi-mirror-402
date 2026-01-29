"""
Sistema de logging unificado para AILOOS.
Proporciona logging estructurado con múltiples handlers y configuración centralizada.
"""

import logging
import logging.handlers
import json
import sys
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

from ..core.config import get_config


@dataclass
class LogConfig:
    """Configuración de logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = True
    console_enabled: bool = True
    file_enabled: bool = True
    file_path: str = "logs/ailoos.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    syslog_enabled: bool = False
    syslog_address: str = "/dev/log"
    include_extra_fields: bool = True


class StructuredFormatter(logging.Formatter):
    """Formatter estructurado para logs JSON."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Formatear log record como JSON."""
        # Extraer información básica
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "thread_name": record.threadName
        }

        # Incluir campos extra si están presentes
        if self.include_extra and hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                             'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                             'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process', 'message']:
                    # Convertir objetos no serializables
                    try:
                        json.dumps(value)
                        log_entry[f"extra_{key}"] = value
                    except (TypeError, ValueError):
                        log_entry[f"extra_{key}"] = str(value)

        # Incluir información de excepción si existe
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class AiloosLogger:
    """Logger personalizado para AILOOS con configuración avanzada."""

    def __init__(self, name: str, config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self._configured = False
        self._lock = threading.Lock()

        # Configurar logger si no está configurado
        if not self._configured:
            self._configure_logger()

    def _configure_logger(self):
        """Configurar el logger con handlers apropiados."""
        with self._lock:
            if self._configured:
                return

            # Limpiar handlers existentes
            self.logger.handlers.clear()

            # Establecer nivel
            level = getattr(logging, self.config.level.upper(), logging.INFO)
            self.logger.setLevel(level)

            # No propagar a root logger
            self.logger.propagate = False

            # Crear formatter
            if self.config.json_format:
                formatter = StructuredFormatter(self.config.include_extra_fields)
            else:
                formatter = logging.Formatter(self.config.format)

            # Handler de consola
            if self.config.console_enabled:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            # Handler de archivo
            if self.config.file_enabled:
                # Crear directorio si no existe
                log_file = Path(self.config.file_path)
                log_file.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.handlers.RotatingFileHandler(
                    self.config.file_path,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            # Handler de syslog (solo en sistemas Unix-like)
            if self.config.syslog_enabled and sys.platform != 'win32':
                try:
                    syslog_handler = logging.handlers.SysLogHandler(
                        address=self.config.syslog_address
                    )
                    syslog_handler.setLevel(logging.WARNING)  # Solo warnings y errores
                    syslog_handler.setFormatter(formatter)
                    self.logger.addHandler(syslog_handler)
                except OSError:
                    # Syslog no disponible
                    pass

            self._configured = True

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# Instancia global del logger manager
_logger_instances: Dict[str, AiloosLogger] = {}
_logger_lock = threading.Lock()


def get_logger(name: str) -> AiloosLogger:
    """
    Obtener instancia de logger para un módulo específico.

    Args:
        name: Nombre del logger (usualmente __name__)

    Returns:
        Instancia configurada de AiloosLogger
    """
    global _logger_instances

    with _logger_lock:
        if name not in _logger_instances:
            # Crear configuración desde config central
            config = get_config()
            log_config = LogConfig(
                level=config.log_level,
                json_format=not config.debug_mode,  # JSON en producción, texto en debug
                console_enabled=True,
                file_enabled=config.environment != "test",
                syslog_enabled=config.environment == "production"
            )

            _logger_instances[name] = AiloosLogger(name, log_config)

        return _logger_instances[name]


def configure_logging(level: str = None):
    """Configurar logging global para toda la aplicación."""
    config = get_config()

    # Usar el level pasado o el de config
    log_level = level or config.log_level

    # Configuración del root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Evitar logs duplicados
    root_logger.handlers.clear()

    # Configurar logging para bibliotecas externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('kubernetes').setLevel(logging.WARNING)

    # Configurar asyncio logger si está en modo debug
    if config.debug_mode:
        logging.getLogger('asyncio').setLevel(logging.DEBUG)


def setup_logging(level: str = 'INFO'):
    """Configurar logging con nivel específico (para compatibilidad)."""
    configure_logging(level)
    return get_logger("cli")


def log_performance(func_name: str, duration: float, **kwargs):
    """Log de métricas de rendimiento."""
    logger = get_logger("performance")
    logger.info(
        f"Performance metric: {func_name}",
        function=func_name,
        duration_ms=duration * 1000,
        **kwargs
    )


def log_api_request(method: str, endpoint: str, status_code: int, duration: float, **kwargs):
    """Log de requests API."""
    logger = get_logger("api")
    logger.info(
        f"API request: {method} {endpoint}",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration * 1000,
        **kwargs
    )


def log_blockchain_transaction(tx_hash: str, action: str, **kwargs):
    """Log de transacciones blockchain."""
    logger = get_logger("blockchain")
    logger.info(
        f"Blockchain transaction: {action}",
        tx_hash=tx_hash,
        action=action,
        **kwargs
    )


def log_federated_event(event_type: str, session_id: str, **kwargs):
    """Log de eventos federados."""
    logger = get_logger("federated")
    logger.info(
        f"Federated event: {event_type}",
        event_type=event_type,
        session_id=session_id,
        **kwargs
    )


def log_security_event(event_type: str, severity: str, **kwargs):
    """Log de eventos de seguridad."""
    logger = get_logger("security")
    level = logging.WARNING if severity in ['medium', 'high'] else logging.INFO
    logger.log(level,
        f"Security event: {event_type}",
        event_type=event_type,
        severity=severity,
        **kwargs
    )


class LogContextManager:
    """Context manager para logging con contexto adicional."""

    def __init__(self, logger: AiloosLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation}",
                duration=duration,
                error=str(exc_val),
                **self.context
            )
        else:
            self.logger.info(
                f"Operation completed: {self.operation}",
                duration=duration,
                **self.context
            )


def log_operation(operation: str, **context):
    """Decorator para logging de operaciones."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            with LogContextManager(logger, operation, **context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Configurar logging al importar
configure_logging()
