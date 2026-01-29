"""
Utilidades avanzadas para el SDK de AILOOS
Incluye decoradores para manejo de errores, circuit breaker, rate limiting, etc.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Estado del circuit breaker."""
    failures: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    success_count: int = 0


class CircuitBreaker:
    """Implementación de Circuit Breaker pattern."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 expected_exception: Exception = Exception, success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self._state: Dict[str, CircuitBreakerState] = {}

    def _get_state(self, key: str) -> CircuitBreakerState:
        if key not in self._state:
            self._state[key] = CircuitBreakerState()
        return self._state[key]

    def _can_attempt(self, state: CircuitBreakerState) -> bool:
        if state.state == "closed":
            return True
        elif state.state == "open":
            if state.last_failure_time and \
               (datetime.now() - state.last_failure_time).seconds > self.recovery_timeout:
                state.state = "half_open"
                state.success_count = 0
                return True
            return False
        elif state.state == "half_open":
            return True
        return False

    def _record_success(self, state: CircuitBreakerState):
        state.success_count += 1
        if state.state == "half_open" and state.success_count >= self.success_threshold:
            state.state = "closed"
            state.failures = 0
            logger.info("Circuit breaker closed - service recovered")

    def _record_failure(self, state: CircuitBreakerState):
        state.failures += 1
        state.last_failure_time = datetime.now()
        state.success_count = 0

        if state.failures >= self.failure_threshold:
            state.state = "open"
            logger.warning(f"Circuit breaker opened after {state.failures} failures")

    async def call(self, func: Callable, *args, key: str = "default", **kwargs) -> Any:
        """Ejecutar función con circuit breaker."""
        state = self._get_state(key)

        if not self._can_attempt(state):
            raise CircuitBreakerOpenException(f"Circuit breaker is {state.state}")

        try:
            result = await func(*args, **kwargs)
            self._record_success(state)
            return result
        except self.expected_exception as e:
            self._record_failure(state)
            raise e


class CircuitBreakerOpenException(Exception):
    """Excepción cuando el circuit breaker está abierto."""
    pass


# Instancia global del circuit breaker
_global_circuit_breaker = CircuitBreaker()


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60,
                   expected_exception: Exception = Exception, key: Optional[str] = None):
    """
    Decorador para circuit breaker.

    Args:
        failure_threshold: Número de fallos antes de abrir el circuito
        recovery_timeout: Segundos para intentar recuperación
        expected_exception: Excepción que cuenta como fallo
        key: Clave única para el circuito (por defecto usa nombre de función)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_key = key or f"{func.__module__}.{func.__name__}"
            return await _global_circuit_breaker.call(func, *args, key=circuit_key, **kwargs)
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
          exceptions: tuple = (Exception,), jitter: bool = True):
    """
    Decorador para reintento automático con backoff exponencial.

    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial en segundos
        backoff: Factor de backoff
        exceptions: Tupla de excepciones a reintentar
        jitter: Añadir jitter aleatorio al delay
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                        raise e

                    # Calcular delay con jitter
                    actual_delay = current_delay
                    if jitter:
                        import random
                        actual_delay = current_delay * (0.5 + random.random())

                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {actual_delay:.2f}s")
                    await asyncio.sleep(actual_delay)
                    current_delay *= backoff

            # Esto nunca debería alcanzarse, pero por si acaso
            raise last_exception

        return wrapper
    return decorator


@dataclass
class RateLimitState:
    """Estado del rate limiter."""
    requests: int = 0
    window_start: datetime = field(default_factory=datetime.now)


class RateLimiter:
    """Rate limiter basado en sliding window."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # segundos
        self._state: Dict[str, RateLimitState] = {}

    def _get_state(self, key: str) -> RateLimitState:
        if key not in self._state:
            self._state[key] = RateLimitState()
        return self._state[key]

    def _is_allowed(self, state: RateLimitState) -> bool:
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_size)

        # Reset window if needed
        if state.window_start < window_start:
            state.requests = 0
            state.window_start = now

        return state.requests < self.requests_per_minute

    def allow(self, key: str) -> bool:
        """Verificar si se permite la request."""
        state = self._get_state(key)

        if self._is_allowed(state):
            state.requests += 1
            return True

        return False


# Instancia global del rate limiter
_global_rate_limiter = RateLimiter()


def rate_limit(requests_per_minute: int = 60, key_func: Optional[Callable] = None):
    """
    Decorador para rate limiting.

    Args:
        requests_per_minute: Límite de requests por minuto
        key_func: Función para generar clave (por defecto usa IP)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer IP del request si es posible
            request = None
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg.client, 'host'):
                    request = arg
                    break

            if key_func:
                key = key_func(*args, **kwargs)
            elif request:
                key = request.client.host
            else:
                key = "default"

            if not _global_rate_limiter.allow(key):
                raise RateLimitExceededException(f"Rate limit exceeded for {key}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitExceededException(Exception):
    """Excepción cuando se excede el rate limit."""
    pass


def log_execution_time(level: int = logging.DEBUG):
    """
    Decorador para loggear tiempo de ejecución.

    Args:
        level: Nivel de logging
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.log(level, f"{func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise e
        return wrapper
    return decorator


def validate_with_pydantic(model_class):
    """
    Decorador para validar input con Pydantic.

    Args:
        model_class: Clase Pydantic para validación
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Validar kwargs que coincidan con campos del modelo
            model_fields = model_class.__fields__
            validated_data = {}

            for field_name, field in model_fields.items():
                if field_name in kwargs:
                    try:
                        validated_data[field_name] = field.validate(kwargs[field_name])
                    except Exception as e:
                        raise ValueError(f"Validation error for {field_name}: {e}")

            # Actualizar kwargs con datos validados
            kwargs.update(validated_data)

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Funciones de utilidad para logging estructurado
def log_structured(level: int, message: str, **context):
    """
    Logging estructurado con contexto adicional.

    Args:
        level: Nivel de logging
        message: Mensaje
        **context: Contexto adicional como kwargs
    """
    extra = {"structured": True, **context}
    logger.log(level, message, extra=extra)


def create_structured_logger(name: str, **default_context):
    """
    Crear logger estructurado con contexto por defecto.

    Args:
        name: Nombre del logger
        **default_context: Contexto por defecto
    """
    logger = logging.getLogger(name)

    class StructuredLogger:
        def __init__(self, logger, default_context):
            self.logger = logger
            self.default_context = default_context

        def log(self, level, message, **context):
            full_context = {**self.default_context, **context}
            log_structured(level, message, **full_context)

        def debug(self, message, **context):
            self.log(logging.DEBUG, message, **context)

        def info(self, message, **context):
            self.log(logging.INFO, message, **context)

        def warning(self, message, **context):
            self.log(logging.WARNING, message, **context)

        def error(self, message, **context):
            self.log(logging.ERROR, message, **context)

        def critical(self, message, **context):
            self.log(logging.CRITICAL, message, **context)

    return StructuredLogger(logger, default_context)


# Utilidades para performance
async def gather_with_concurrency(n: int, *coroutines):
    """
    Ejecutar coroutines con concurrencia limitada.

    Args:
        n: Número máximo de coroutines concurrentes
        *coroutines: Coroutines a ejecutar
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coroutines))


def cache_async(ttl_seconds: int = 300):
    """
    Decorador de cache simple para funciones async.

    Args:
        ttl_seconds: Tiempo de vida del cache en segundos
    """
    cache = {}

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Crear clave de cache
            key = str((args, tuple(sorted(kwargs.items()))))

            # Verificar cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result

            # Ejecutar función
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())

            return result

        return wrapper
    return decorator