"""
Sistema de rate limiting avanzado para AILOOS.
Implementa múltiples estrategias de rate limiting con Redis y memoria local.
"""

import asyncio
import time
try:
    import redis.asyncio as redis
except ImportError:
    redis = None
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..core.logging import get_logger
from ..core.config import get_config

logger = get_logger(__name__)


class RateLimitStrategy(Enum):
    """Estrategias de rate limiting."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitRule:
    """Regla de rate limiting."""
    name: str
    max_requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    burst_limit: Optional[int] = None
    refill_rate: Optional[float] = None  # Para token bucket
    bucket_capacity: Optional[int] = None  # Para leaky bucket
    block_duration_seconds: int = 0  # Duración del bloqueo tras exceder límite
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "strategy": self.strategy.value,
            "burst_limit": self.burst_limit,
            "refill_rate": self.refill_rate,
            "bucket_capacity": self.bucket_capacity,
            "block_duration_seconds": self.block_duration_seconds,
            "whitelist": self.whitelist,
            "blacklist": self.blacklist
        }


@dataclass
class RateLimitResult:
    """Resultado de verificación de rate limit."""
    allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[float] = None
    blocked_until: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "remaining_requests": self.remaining_requests,
            "reset_time": self.reset_time,
            "retry_after": self.retry_after,
            "blocked_until": self.blocked_until,
            "metadata": self.metadata
        }


class RedisRateLimiter:
    """Rate limiter usando Redis para persistencia distribuida."""

    def __init__(self, redis_client: Optional[Any] = None):
        self.redis = redis_client
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self):
        """Inicializar conexión Redis."""
        if self._initialized:
            return

        if not self.redis:
            try:
                config = get_config()
                redis_url = config.get('redis_url', 'redis://localhost:6379')
                self.redis = redis.from_url(redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info("🔴 Redis rate limiter initialized")
            except Exception as e:
                logger.warning(f"Redis not available for rate limiting: {e}")
                self.redis = None

        self._initialized = True

    async def check_limit(
        self,
        key: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """
        Verificar rate limit usando Redis.

        Args:
            key: Clave identificadora (IP, user_id, etc.)
            rule: Regla de rate limiting

        Returns:
            Resultado de la verificación
        """
        if not self.redis:
            # Fallback a implementación local
            return await self._check_local_limit(key, rule)

        current_time = time.time()

        try:
            if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._check_fixed_window(key, rule, current_time)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._check_sliding_window(key, rule, current_time)
            elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._check_token_bucket(key, rule, current_time)
            elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
                return await self._check_leaky_bucket(key, rule, current_time)
            else:
                logger.error(f"Unknown rate limit strategy: {rule.strategy}")
                return RateLimitResult(
                    allowed=True,
                    remaining_requests=rule.max_requests,
                    reset_time=current_time + rule.window_seconds
                )

        except Exception as e:
            logger.error(f"Error in Redis rate limiting: {e}")
            # Fallback a local
            return await self._check_local_limit(key, rule)

    async def _check_fixed_window(
        self,
        key: str,
        rule: RateLimitRule,
        current_time: float
    ) -> RateLimitResult:
        """Fixed window rate limiting."""
        window_key = f"ratelimit:fw:{key}:{int(current_time // rule.window_seconds)}"
        block_key = f"ratelimit:block:{key}"

        # Verificar si está bloqueado
        blocked_until = await self.redis.get(block_key)
        if blocked_until and float(blocked_until) > current_time:
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=float(blocked_until),
                blocked_until=float(blocked_until)
            )

        # Contar requests en la ventana actual
        count = await self.redis.incr(window_key)

        # Establecer expiración si es el primer request
        if count == 1:
            await self.redis.expire(window_key, rule.window_seconds)

        # Verificar límites
        allowed = count <= rule.max_requests
        remaining = max(0, rule.max_requests - count)

        if not allowed:
            # Aplicar bloqueo si está configurado
            if rule.block_duration_seconds > 0:
                await self.redis.setex(
                    block_key,
                    rule.block_duration_seconds,
                    current_time + rule.block_duration_seconds
                )

        reset_time = (int(current_time // rule.window_seconds) + 1) * rule.window_seconds

        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining,
            reset_time=reset_time,
            retry_after=reset_time - current_time if not allowed else None
        )

    async def _check_sliding_window(
        self,
        key: str,
        rule: RateLimitRule,
        current_time: float
    ) -> RateLimitResult:
        """Sliding window rate limiting usando sorted sets."""
        window_key = f"ratelimit:sw:{key}"

        # Añadir timestamp actual
        await self.redis.zadd(window_key, {str(current_time): current_time})

        # Remover timestamps fuera de la ventana
        min_time = current_time - rule.window_seconds
        await self.redis.zremrangebyscore(window_key, '-inf', min_time)

        # Contar requests en la ventana
        count = await self.redis.zcard(window_key)

        # Verificar límites
        allowed = count <= rule.max_requests
        remaining = max(0, rule.max_requests - count)

        # Calcular reset time (tiempo hasta que expire el request más antiguo)
        if count > 0:
            oldest_timestamp = await self.redis.zrange(window_key, 0, 0, withscores=True)
            if oldest_timestamp:
                reset_time = float(oldest_timestamp[0][1]) + rule.window_seconds
            else:
                reset_time = current_time + rule.window_seconds
        else:
            reset_time = current_time + rule.window_seconds

        # Limpiar ventana antigua periódicamente
        await self.redis.expire(window_key, rule.window_seconds * 2)

        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining,
            reset_time=reset_time,
            retry_after=reset_time - current_time if not allowed else None
        )

    async def _check_token_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        current_time: float
    ) -> RateLimitResult:
        """Token bucket rate limiting."""
        tokens_key = f"ratelimit:tb:tokens:{key}"
        last_refill_key = f"ratelimit:tb:last:{key}"

        bucket_capacity = rule.bucket_capacity or rule.max_requests
        refill_rate = rule.refill_rate or (rule.max_requests / rule.window_seconds)

        # Obtener estado actual
        tokens_str = await self.redis.get(tokens_key)
        last_refill_str = await self.redis.get(last_refill_key)

        if tokens_str is None:
            # Inicializar bucket
            tokens = float(bucket_capacity)
            last_refill = current_time
        else:
            tokens = float(tokens_str)
            last_refill = float(last_refill_str or current_time)

        # Refill tokens
        time_passed = current_time - last_refill
        tokens_to_add = time_passed * refill_rate
        tokens = min(bucket_capacity, tokens + tokens_to_add)

        # Intentar consumir token
        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False

        # Actualizar estado
        await self.redis.setex(tokens_key, rule.window_seconds * 2, str(tokens))
        await self.redis.setex(last_refill_key, rule.window_seconds * 2, str(current_time))

        # Calcular reset time
        tokens_needed = 1 - tokens
        reset_time = current_time + (tokens_needed / refill_rate) if tokens_needed > 0 else current_time

        return RateLimitResult(
            allowed=allowed,
            remaining_requests=int(tokens),
            reset_time=reset_time,
            retry_after=reset_time - current_time if not allowed else None,
            metadata={
                "bucket_capacity": bucket_capacity,
                "current_tokens": tokens,
                "refill_rate": refill_rate
            }
        )

    async def _check_leaky_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        current_time: float
    ) -> RateLimitResult:
        """Leaky bucket rate limiting."""
        queue_key = f"ratelimit:lb:queue:{key}"
        last_leak_key = f"ratelimit:lb:last:{key}"

        bucket_capacity = rule.bucket_capacity or rule.max_requests
        leak_rate = rule.refill_rate or (rule.max_requests / rule.window_seconds)

        # Obtener estado actual
        queue_size = await self.redis.llen(queue_key)
        last_leak_str = await self.redis.get(last_leak_key)
        last_leak = float(last_leak_str or current_time)

        # Simular leaking
        time_passed = current_time - last_leak
        leaks_to_remove = int(time_passed * leak_rate)

        if leaks_to_remove > 0:
            # Remover elementos del queue (simulando leaking)
            for _ in range(min(leaks_to_remove, queue_size)):
                await self.redis.lpop(queue_key)
            queue_size = max(0, queue_size - leaks_to_remove)
            last_leak = current_time

        # Intentar añadir request al bucket
        if queue_size < bucket_capacity:
            await self.redis.rpush(queue_key, str(current_time))
            queue_size += 1
            allowed = True
        else:
            allowed = False

        # Actualizar last leak time
        await self.redis.setex(last_leak_key, rule.window_seconds * 2, str(last_leak))
        await self.redis.expire(queue_key, rule.window_seconds * 2)

        # Calcular reset time
        remaining_capacity = bucket_capacity - queue_size
        reset_time = current_time + (remaining_capacity / leak_rate) if remaining_capacity > 0 else current_time

        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining_capacity,
            reset_time=reset_time,
            retry_after=reset_time - current_time if not allowed else None,
            metadata={
                "bucket_capacity": bucket_capacity,
                "current_queue_size": queue_size,
                "leak_rate": leak_rate
            }
        )

    async def _check_local_limit(
        self,
        key: str,
        rule: RateLimitRule,
        current_time: float = None
    ) -> RateLimitResult:
        """Fallback local para rate limiting."""
        if current_time is None:
            current_time = time.time()

        if key not in self.local_cache:
            self.local_cache[key] = {
                'count': 0,
                'window_start': current_time,
                'blocked_until': 0
            }

        cache = self.local_cache[key]

        # Verificar bloqueo
        if cache['blocked_until'] > current_time:
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=cache['blocked_until'],
                blocked_until=cache['blocked_until']
            )

        # Reset window si es necesario
        if current_time - cache['window_start'] >= rule.window_seconds:
            cache['count'] = 0
            cache['window_start'] = current_time

        # Verificar límite
        allowed = cache['count'] < rule.max_requests
        if allowed:
            cache['count'] += 1

        remaining = max(0, rule.max_requests - cache['count'])
        reset_time = cache['window_start'] + rule.window_seconds

        # Aplicar bloqueo si excedió límite
        if not allowed and rule.block_duration_seconds > 0:
            cache['blocked_until'] = current_time + rule.block_duration_seconds
            reset_time = cache['blocked_until']

        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining,
            reset_time=reset_time,
            retry_after=reset_time - current_time if not allowed else None
        )

    async def cleanup_expired_keys(self):
        """Limpiar keys expiradas (mantenimiento)."""
        if not self.redis:
            return

        try:
            # Este método puede ser llamado periódicamente para mantenimiento
            # En Redis, las keys con TTL se limpian automáticamente
            pass
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")


class RateLimitManager:
    """
    Gestor principal de rate limiting.
    Maneja múltiples reglas y estrategias.
    """

    def __init__(self):
        self.redis_limiter = RedisRateLimiter()
        self.rules: Dict[str, RateLimitRule] = {}
        self._initialized = False

    async def initialize(self):
        """Inicializar el gestor de rate limiting."""
        if self._initialized:
            return

        await self.redis_limiter.initialize()

        # Cargar reglas por defecto
        await self._load_default_rules()

        self._initialized = True
        logger.info("🚦 Rate limit manager initialized")

    async def _load_default_rules(self):
        """Cargar reglas de rate limiting por defecto."""
        config = get_config()

        # Reglas por defecto
        default_rules = {
            'api_general': RateLimitRule(
                name='api_general',
                max_requests=config.get('rate_limit_api_general', 100),
                window_seconds=60,  # por minuto
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                burst_limit=config.get('rate_limit_burst', 150)
            ),
            'api_auth': RateLimitRule(
                name='api_auth',
                max_requests=config.get('rate_limit_api_auth', 5),
                window_seconds=300,  # por 5 minutos
                strategy=RateLimitStrategy.FIXED_WINDOW,
                block_duration_seconds=600  # bloqueo de 10 minutos
            ),
            'federated_training': RateLimitRule(
                name='federated_training',
                max_requests=config.get('rate_limit_federated', 50),
                window_seconds=60,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                bucket_capacity=100,
                refill_rate=1.0  # 1 token por segundo
            ),
            'marketplace': RateLimitRule(
                name='marketplace',
                max_requests=config.get('rate_limit_marketplace', 20),
                window_seconds=3600,  # por hora
                strategy=RateLimitStrategy.SLIDING_WINDOW
            )
        }

        for rule in default_rules.values():
            self.add_rule(rule)

    def add_rule(self, rule: RateLimitRule):
        """Añadir regla de rate limiting."""
        self.rules[rule.name] = rule
        logger.debug(f"Added rate limit rule: {rule.name}")

    def get_rule(self, name: str) -> Optional[RateLimitRule]:
        """Obtener regla por nombre."""
        return self.rules.get(name)

    async def check_limit(
        self,
        key: str,
        rule_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RateLimitResult:
        """
        Verificar rate limit para una regla específica.

        Args:
            key: Clave identificadora
            rule_name: Nombre de la regla
            context: Contexto adicional (IP, user_id, etc.)

        Returns:
            Resultado de la verificación
        """
        rule = self.get_rule(rule_name)
        if not rule:
            # Si no hay regla, permitir
            return RateLimitResult(
                allowed=True,
                remaining_requests=999,
                reset_time=time.time() + 60
            )

        # Verificar whitelist/blacklist
        if context:
            client_ip = context.get('ip')
            user_id = context.get('user_id')

            # Blacklist tiene prioridad
            if client_ip in rule.blacklist or (user_id and user_id in rule.blacklist):
                return RateLimitResult(
                    allowed=False,
                    remaining_requests=0,
                    reset_time=time.time() + 3600,  # Bloqueado por 1 hora
                    blocked_until=time.time() + 3600
                )

            # Whitelist permite sin límites
            if client_ip in rule.whitelist or (user_id and user_id in rule.whitelist):
                return RateLimitResult(
                    allowed=True,
                    remaining_requests=999,
                    reset_time=time.time() + 60
                )

        # Aplicar rate limiting
        result = await self.redis_limiter.check_limit(key, rule)

        # Log si fue rechazado
        if not result.allowed:
            logger.warning(
                f"Rate limit exceeded: {rule_name} for {key}",
                rule_name=rule_name,
                key=key,
                remaining_requests=result.remaining_requests,
                reset_time=result.reset_time
            )

        return result

    async def get_limits_status(
        self,
        key: str,
        rule_names: List[str]
    ) -> Dict[str, RateLimitResult]:
        """
        Obtener estado de límites para múltiples reglas.

        Args:
            key: Clave identificadora
            rule_names: Lista de nombres de reglas

        Returns:
            Diccionario con estado de cada regla
        """
        results = {}
        for rule_name in rule_names:
            results[rule_name] = await self.check_limit(key, rule_name)
        return results

    def get_all_rules(self) -> Dict[str, RateLimitRule]:
        """Obtener todas las reglas."""
        return self.rules.copy()

    async def reset_limit(self, key: str, rule_name: str):
        """
        Resetear límite para una clave específica.

        Args:
            key: Clave a resetear
            rule_name: Nombre de la regla
        """
        # Esta funcionalidad depende de la implementación de Redis
        # Por simplicidad, no se implementa aquí
        logger.info(f"Rate limit reset requested for {key}:{rule_name}")

    async def cleanup(self):
        """Limpiar estado expirado."""
        await self.redis_limiter.cleanup_expired_keys()

        # Limpiar cache local antigua
        current_time = time.time()
        expired_keys = [
            key for key, data in self.redis_limiter.local_cache.items()
            if data.get('blocked_until', 0) < current_time and
               current_time - data.get('window_start', 0) > 3600  # 1 hora
        ]

        for key in expired_keys:
            del self.redis_limiter.local_cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")


# Instancia global
rate_limit_manager = RateLimitManager()


async def get_rate_limit_manager() -> RateLimitManager:
    """Obtener instancia global del gestor de rate limiting."""
    if not rate_limit_manager._initialized:
        await rate_limit_manager.initialize()
    return rate_limit_manager


# Funciones de conveniencia
async def check_api_rate_limit(
    key: str,
    endpoint: str = 'general',
    context: Optional[Dict[str, Any]] = None
) -> RateLimitResult:
    """
    Verificar rate limit para APIs.

    Args:
        key: Clave identificadora (IP, user_id)
        endpoint: Tipo de endpoint ('general', 'auth', 'federated', 'marketplace')
        context: Contexto adicional

    Returns:
        Resultado de la verificación
    """
    manager = await get_rate_limit_manager()
    rule_name = f'api_{endpoint}'
    return await manager.check_limit(key, rule_name, context)


async def check_federated_rate_limit(
    node_id: str,
    context: Optional[Dict[str, Any]] = None
) -> RateLimitResult:
    """Verificar rate limit para nodos federados."""
    manager = await get_rate_limit_manager()
    return await manager.check_limit(node_id, 'federated_training', context)


async def check_marketplace_rate_limit(
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> RateLimitResult:
    """Verificar rate limit para marketplace."""
    manager = await get_rate_limit_manager()
    return await manager.check_limit(user_id, 'marketplace', context)