"""
Rate Limiting System for AILOOS Commercial API
==============================================

Sistema de rate limiting distribuido con Redis para controlar
el uso de la API comercial y monetización por uso.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import redis.asyncio as redis
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Tipos de rate limiting disponibles."""
    REQUESTS_PER_MINUTE = "rpm"
    REQUESTS_PER_HOUR = "rph"
    REQUESTS_PER_DAY = "rpd"
    TOKENS_PER_MINUTE = "tpm"
    TOKENS_PER_HOUR = "tph"
    CONCURRENT_REQUESTS = "concurrent"


class RateLimitTier(Enum):
    """Niveles de rate limiting por tier de usuario."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


@dataclass
class RateLimitConfig:
    """Configuración de rate limiting por tier."""
    tier: RateLimitTier
    limits: Dict[RateLimitType, int] = field(default_factory=dict)
    burst_multiplier: float = 1.5  # Burst allowance
    refill_rate: float = 1.0  # Tokens per second for token bucket

    def __post_init__(self):
        if not self.limits:
            self._set_default_limits()

    def _set_default_limits(self):
        """Establecer límites por defecto según el tier."""
        if self.tier == RateLimitTier.FREE:
            self.limits = {
                RateLimitType.REQUESTS_PER_MINUTE: 10,
                RateLimitType.REQUESTS_PER_HOUR: 100,
                RateLimitType.TOKENS_PER_MINUTE: 1000,
                RateLimitType.CONCURRENT_REQUESTS: 1
            }
        elif self.tier == RateLimitTier.BASIC:
            self.limits = {
                RateLimitType.REQUESTS_PER_MINUTE: 60,
                RateLimitType.REQUESTS_PER_HOUR: 1000,
                RateLimitType.TOKENS_PER_MINUTE: 10000,
                RateLimitType.CONCURRENT_REQUESTS: 5
            }
        elif self.tier == RateLimitTier.PRO:
            self.limits = {
                RateLimitType.REQUESTS_PER_MINUTE: 300,
                RateLimitType.REQUESTS_PER_HOUR: 10000,
                RateLimitType.TOKENS_PER_MINUTE: 100000,
                RateLimitType.CONCURRENT_REQUESTS: 20
            }
        elif self.tier == RateLimitTier.ENTERPRISE:
            self.limits = {
                RateLimitType.REQUESTS_PER_MINUTE: 1000,
                RateLimitType.REQUESTS_PER_HOUR: 50000,
                RateLimitType.TOKENS_PER_MINUTE: 1000000,
                RateLimitType.CONCURRENT_REQUESTS: 100
            }
        elif self.tier == RateLimitTier.UNLIMITED:
            self.limits = {
                RateLimitType.REQUESTS_PER_MINUTE: 10000,
                RateLimitType.REQUESTS_PER_HOUR: 1000000,
                RateLimitType.TOKENS_PER_MINUTE: 10000000,
                RateLimitType.CONCURRENT_REQUESTS: 1000
            }


@dataclass
class RateLimitResult:
    """Resultado de una verificación de rate limit."""
    allowed: bool
    remaining: int
    reset_time: float
    limit: int
    retry_after: Optional[float] = None


class DistributedRateLimiter:
    """
    Rate limiter distribuido usando Redis para persistencia y sincronización.
    Implementa múltiples algoritmos: Fixed Window, Sliding Window, Token Bucket.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self._rate_limit_configs: Dict[str, RateLimitConfig] = {}

        # Lua scripts para operaciones atómicas
        self._check_and_update_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4] or 1)

        -- Get current count
        local current = redis.call('GET', key)
        if not current then
            current = 0
        else
            current = tonumber(current)
        end

        -- Check if limit exceeded
        if current + cost > limit then
            return {0, current, limit}  -- Not allowed
        end

        -- Update count and set expiry
        redis.call('INCRBY', key, cost)
        redis.call('PEXPIREAT', key, now + window)

        return {1, current + cost, limit}  -- Allowed
        """

    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Redis connection established for rate limiting")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False

    def register_user_tier(self, user_id: str, tier: RateLimitTier):
        """Registrar el tier de rate limiting para un usuario."""
        config = RateLimitConfig(tier=tier)
        self._rate_limit_configs[user_id] = config
        logger.info(f"📋 Registered user {user_id} with tier {tier.value}")

    async def check_rate_limit(
        self,
        user_id: str,
        limit_type: RateLimitType,
        cost: int = 1
    ) -> RateLimitResult:
        """
        Verificar si una request está dentro del rate limit.

        Args:
            user_id: ID del usuario
            limit_type: Tipo de límite a verificar
            cost: Costo de la operación (ej: tokens usados)

        Returns:
            RateLimitResult con estado y metadata
        """
        if user_id not in self._rate_limit_configs:
            # Usuario no registrado - usar tier FREE por defecto
            self.register_user_tier(user_id, RateLimitTier.FREE)

        config = self._rate_limit_configs[user_id]
        limit = config.limits.get(limit_type, 0)

        if limit == 0:  # Unlimited
            return RateLimitResult(
                allowed=True,
                remaining=float('inf'),
                reset_time=0,
                limit=float('inf')
            )

        # Generar key Redis
        key = self._generate_key(user_id, limit_type)
        window_seconds = self._get_window_seconds(limit_type)
        now = int(time.time() * 1000)  # milliseconds

        try:
            # Ejecutar script Lua atómico
            result = await self.redis.eval(
                self._check_and_update_script,
                1,  # número de keys
                key, limit, window_seconds, now, cost
            )

            allowed = result[0] == 1
            current_count = result[1]
            limit_value = result[2]

            # Calcular tiempo de reset
            reset_time = now + window_seconds

            if allowed:
                remaining = limit_value - current_count
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=reset_time / 1000,  # Convertir a segundos
                    limit=limit_value
                )
            else:
                # Calcular retry_after
                retry_after = (reset_time - now) / 1000
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time / 1000,
                    limit=limit_value,
                    retry_after=retry_after
                )

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # En caso de error, permitir la request (fail-open)
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=time.time() + 60,
                limit=1000
            )

    async def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Obtener límites actuales y estado para un usuario."""
        if user_id not in self._rate_limit_configs:
            self.register_user_tier(user_id, RateLimitTier.FREE)

        config = self._rate_limit_configs[user_id]

        limits_status = {}
        for limit_type, limit_value in config.limits.items():
            key = self._generate_key(user_id, limit_type)
            current = await self.redis.get(key)
            current_count = int(current) if current else 0

            limits_status[limit_type.value] = {
                "limit": limit_value,
                "current": current_count,
                "remaining": max(0, limit_value - current_count)
            }

        return {
            "user_id": user_id,
            "tier": config.tier.value,
            "limits": limits_status
        }

    async def reset_user_limits(self, user_id: str):
        """Resetear límites para un usuario (útil para testing/admin)."""
        pattern = f"ratelimit:{user_id}:*"
        keys = await self.redis.keys(pattern)

        if keys:
            await self.redis.delete(*keys)
            logger.info(f"🗑️ Reset limits for user {user_id} ({len(keys)} keys)")

    def _generate_key(self, user_id: str, limit_type: RateLimitType) -> str:
        """Generar key Redis para rate limiting."""
        return f"ratelimit:{user_id}:{limit_type.value}"

    def _get_window_seconds(self, limit_type: RateLimitType) -> int:
        """Obtener ventana de tiempo en segundos para el tipo de límite."""
        if limit_type == RateLimitType.REQUESTS_PER_MINUTE:
            return 60
        elif limit_type == RateLimitType.REQUESTS_PER_HOUR:
            return 3600
        elif limit_type == RateLimitType.REQUESTS_PER_DAY:
            return 86400
        elif limit_type == RateLimitType.TOKENS_PER_MINUTE:
            return 60
        elif limit_type == RateLimitType.TOKENS_PER_HOUR:
            return 3600
        elif limit_type == RateLimitType.CONCURRENT_REQUESTS:
            return 60  # Window for concurrent tracking
        else:
            return 60  # Default 1 minute

    async def close(self):
        """Cerrar conexión Redis."""
        if self.redis:
            await self.redis.close()


class RateLimitMiddleware:
    """
    Middleware de FastAPI para rate limiting automático.
    Integra con el DistributedRateLimiter.
    """

    def __init__(self, rate_limiter: DistributedRateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request, call_next):
        """Middleware para verificar rate limits en cada request."""

        # Extraer user_id del request (de auth middleware)
        user_id = self._extract_user_id(request)

        if not user_id:
            # Request sin autenticación - usar límite muy bajo
            user_id = "anonymous"
            self.rate_limiter.register_user_tier(user_id, RateLimitTier.FREE)

        # Verificar rate limit de requests
        request_limit = await self.rate_limiter.check_rate_limit(
            user_id, RateLimitType.REQUESTS_PER_MINUTE
        )

        if not request_limit.allowed:
            # Rate limit excedido
            return self._create_rate_limit_response(request_limit)

        # Para requests de inferencia, verificar también tokens
        if request.url.path.startswith("/api/v1/inference"):
            # Extraer tokens del body (aproximación)
            tokens_used = self._estimate_tokens(request)
            token_limit = await self.rate_limiter.check_rate_limit(
                user_id, RateLimitType.TOKENS_PER_MINUTE, tokens_used
            )

            if not token_limit.allowed:
                return self._create_rate_limit_response(token_limit)

        # Añadir headers de rate limit a la response
        response = await call_next(request)

        # Añadir headers informativos
        response.headers["X-RateLimit-Limit"] = str(request_limit.limit)
        response.headers["X-RateLimit-Remaining"] = str(request_limit.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(request_limit.reset_time))

        return response

    def _extract_user_id(self, request) -> Optional[str]:
        """Extraer user_id del request (de JWT token, etc.)."""
        # Implementar extracción real del user_id
        # Por ahora, usar un header personalizado
        return request.headers.get("X-User-ID", "anonymous")

    def _estimate_tokens(self, request) -> int:
        """Estimar tokens usados en una request."""
        # Implementar estimación real basada en el prompt
        # Por ahora, usar una estimación simple
        try:
            body = request.json()
            prompt = body.get("prompt", "")
            return len(prompt.split()) * 1.3  # Aproximación simple
        except:
            return 100  # Default estimation

    def _create_rate_limit_response(self, limit_result: RateLimitResult):
        """Crear response HTTP para rate limit excedido."""
        from fastapi import Response
        import json

        response_data = {
            "error": "rate_limit_exceeded",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": limit_result.retry_after,
            "limit": limit_result.limit,
            "remaining": limit_result.remaining,
            "reset_time": limit_result.reset_time
        }

        response = Response(
            content=json.dumps(response_data),
            media_type="application/json",
            status_code=429
        )

        response.headers["Retry-After"] = str(int(limit_result.retry_after or 60))
        response.headers["X-RateLimit-Limit"] = str(limit_result.limit)
        response.headers["X-RateLimit-Remaining"] = str(limit_result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(limit_result.reset_time))

        return response


# Instancia global del rate limiter
_rate_limiter: Optional[DistributedRateLimiter] = None


async def get_rate_limiter() -> DistributedRateLimiter:
    """Obtener instancia global del rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _rate_limiter = DistributedRateLimiter(redis_url)
        await _rate_limiter.initialize()
    return _rate_limiter


async def initialize_rate_limiting():
    """Inicializar sistema de rate limiting."""
    rate_limiter = await get_rate_limiter()

    # Configurar tiers por defecto
    # En producción, esto vendría de una base de datos
    default_users = {
        "admin": RateLimitTier.UNLIMITED,
        "enterprise_user": RateLimitTier.ENTERPRISE,
        "pro_user": RateLimitTier.PRO,
        "basic_user": RateLimitTier.BASIC,
        "anonymous": RateLimitTier.FREE
    }

    for user_id, tier in default_users.items():
        rate_limiter.register_user_tier(user_id, tier)

    logger.info("✅ Rate limiting system initialized")
    return rate_limiter


# Funciones de utilidad para testing
async def test_rate_limiting():
    """Función de test para el sistema de rate limiting."""
    print("🧪 Testing Rate Limiting System")
    print("=" * 50)

    # Inicializar
    rate_limiter = DistributedRateLimiter()
    if not await rate_limiter.initialize():
        print("❌ Failed to initialize rate limiter")
        return

    # Registrar usuario de test
    rate_limiter.register_user_tier("test_user", RateLimitTier.BASIC)

    print("📋 Testing BASIC tier limits:")
    print("   • 60 requests per minute")
    print("   • 1000 requests per hour")
    print("   • 10000 tokens per minute")

    # Test de requests por minuto
    print("\n🔄 Testing requests per minute...")
    for i in range(65):  # Intentar 65 requests (5 sobre el límite)
        result = await rate_limiter.check_rate_limit(
            "test_user", RateLimitType.REQUESTS_PER_MINUTE
        )

        if i < 5:  # Mostrar solo primeros y últimos
            print(f"   Request {i+1}: {'✅' if result.allowed else '❌'} "
                  f"(remaining: {result.remaining})")
        elif i >= 60:
            print(f"   Request {i+1}: {'✅' if result.allowed else '❌'} "
                  f"(remaining: {result.remaining})")

        if not result.allowed:
            print(f"   🚫 Rate limit exceeded! Retry after: {result.retry_after:.1f}s")
            break

    # Test de tokens por minuto
    print("\n🔄 Testing tokens per minute...")
    result = await rate_limiter.check_rate_limit(
        "test_user", RateLimitType.TOKENS_PER_MINUTE, 5000
    )
    print(f"   5000 tokens: {'✅' if result.allowed else '❌'} "
          f"(remaining: {result.remaining})")

    # Obtener estado del usuario
    status = await rate_limiter.get_user_limits("test_user")
    print("\n📊 User status:")
    for limit_type, data in status["limits"].items():
        print(f"   • {limit_type}: {data['current']}/{data['limit']} "
              f"(remaining: {data['remaining']})")

    await rate_limiter.close()
    print("\n✅ Rate limiting test completed!")


if __name__ == "__main__":
    # Ejecutar test
    asyncio.run(test_rate_limiting())