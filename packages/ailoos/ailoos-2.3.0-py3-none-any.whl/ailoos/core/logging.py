"""
Sistema de logging centralizado para AILOOS.
Configuración de logs estructurados y monitoreo.
"""

import logging
import logging.handlers
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import structlog


class AiloosLogger:
    """
    Logger avanzado para AILOOS con structured logging y JSON.
    Soporta logging a archivos, consola, JSON y diferentes niveles.
    """

    def __init__(self, name: str, level: str = "INFO", log_file: str = None,
                 json_format: bool = False, include_extra: bool = True):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_file = log_file
        self.json_format = json_format
        self.include_extra = include_extra
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configurar logger avanzado con structured logging."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        # Evitar duplicación de handlers
        if logger.handlers:
            return logger

        # Configurar structlog para logging estructurado
        if self.json_format:
            # Formato JSON para producción
            try:
                from pythonjsonlogger import jsonlogger
                formatter = jsonlogger.JsonFormatter(
                    '%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            except ImportError:
                # Fallback si no está disponible
                formatter = logging.Formatter(
                    '%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
        else:
            # Formato legible para desarrollo
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler para archivo si se especifica
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=50*1024*1024,  # 50MB
                backupCount=10
            )
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

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
        log_method = getattr(self.logger, level)

        if self.json_format and extra:
            # Logging estructurado con JSON
            log_method(message, extra=extra)
        elif extra:
            # Añadir campos extra al mensaje
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            message = f"{message} | {extra_str}"
            log_method(message)
        else:
            log_method(message)


# Logger global por defecto
_default_logger = None


def get_logger(name: str = "ailoos") -> AiloosLogger:
    """Obtener logger configurado con structured logging."""
    global _default_logger

    if _default_logger is None:
        from .config import get_config
        config = get_config()

        log_file = getattr(config, 'log_file', None)
        log_level = getattr(config, 'log_level', 'INFO')
        json_format = getattr(config, 'json_logging', False)

        _default_logger = AiloosLogger(
            name=name,
            level=log_level,
            log_file=log_file,
            json_format=json_format
        )

    return _default_logger


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    format_string: str = None,
    json_format: bool = False,
    enable_structlog: bool = True
):
    """
    Configurar logging avanzado para la aplicación con structured logging.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar logs
        format_string: Formato personalizado para logs
        json_format: Usar formato JSON para logs
        enable_structlog: Habilitar structured logging
    """
    global _default_logger

    # Configurar structlog si está habilitado
    if enable_structlog:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if json_format else structlog.processors.KeyValueRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Configurar logging raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formato
    if json_format:
        try:
            from pythonjsonlogger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        except ImportError:
            # Fallback si no está disponible
            formatter = logging.Formatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    elif format_string:
        formatter = logging.Formatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler para archivo
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Actualizar logger por defecto
    _default_logger = AiloosLogger(
        name="ailoos",
        level=level,
        log_file=log_file,
        json_format=json_format
    )


# Funciones adicionales para logging estructurado
def log_performance(func_name: str, duration: float, **metrics):
    """Log de métricas de rendimiento."""
    logger = get_logger()
    logger.info(
        f"Performance: {func_name}",
        duration=duration,
        **metrics
    )

def log_api_request(endpoint: str, method: str, status_code: int, duration: float, user_id: str = None):
    """Log de requests API."""
    logger = get_logger("api")
    logger.info(
        f"API Request: {method} {endpoint}",
        status_code=status_code,
        duration=duration,
        user_id=user_id
    )

def log_blockchain_tx(tx_hash: str, tx_type: str, amount: float, status: str, **extra):
    """Log de transacciones blockchain."""
    logger = get_logger("blockchain")
    logger.info(
        f"Blockchain TX: {tx_type}",
        tx_hash=tx_hash,
        amount=amount,
        status=status,
        **extra
    )

def log_federated_event(event_type: str, node_id: str, session_id: str, **data):
    """Log de eventos federados."""
    logger = get_logger("federated")
    logger.info(
        f"Federated Event: {event_type}",
        node_id=node_id,
        session_id=session_id,
        **data
    )

def log_marketplace_event(event_type: str, user_id: str, amount: float = None, **data):
    """Log de eventos del marketplace."""
    logger = get_logger("marketplace")
    logger.info(
        f"Marketplace Event: {event_type}",
        user_id=user_id,
        amount=amount,
        **data
    )


# Configurar logging al importar
setup_logging()