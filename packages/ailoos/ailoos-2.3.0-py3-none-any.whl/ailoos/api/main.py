#!/usr/bin/env python3
"""
AILOOS Unified API Gateway - Main Entry Point
Combines all API modules into a single FastAPI application.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from ..core.config import get_config
from ..core.logging import get_logger

# Import all API modules with fallback handling
logger = get_logger(__name__)

# Available API modules with their create functions
API_MODULES = {
    "gateway": ("gateway", "create_app"),
    "wallet": ("wallet_api", "create_wallet_app"),
    "federated": ("federated_api", "create_federated_app"),
    "dashboard": ("dashboard_api", "create_dashboard_app"),
    "rag": ("rag_api", "create_rag_app"),
    "models": ("models_api", "create_models_app"),
    "analytics": ("analytics_api", "create_analytics_app"),
    "compliance": ("compliance_api", "create_compliance_app"),
    "marketplace": ("marketplace_api", "create_marketplace_app"),
    "datahub": ("datahub_api", "create_datahub_app"),
    "system_tools": ("system_tools_api", "create_system_tools_app"),
    "technical_dashboard": ("technical_dashboard_api", "create_technical_dashboard_app"),
    "empoorio": ("empoorio_api", "create_empoorio_app"),
    "settings": ("settings_api", "create_settings_app")
}

# Import available API modules
imported_apis = {}
for api_name, (module_name, func_name) in API_MODULES.items():
    try:
        module = __import__(f"ailoos.api.{module_name}", fromlist=[func_name])
        func = getattr(module, func_name, None)
        if func:
            imported_apis[api_name] = func
            logger.info(f"✅ Imported {api_name} API from {module_name}")
        else:
            logger.warning(f"⚠️ Function {func_name} not found in {module_name}")
    except ImportError as e:
        logger.warning(f"⚠️ Could not import {api_name} API from {module_name}: {e}")
    except Exception as e:
        logger.error(f"❌ Error importing {api_name} API: {e}")

if not imported_apis:
    raise RuntimeError("No API modules could be imported. Check your installation.")

logger.info(f"🎯 Successfully imported {len(imported_apis)} API modules: {', '.join(imported_apis.keys())}")

logger = get_logger(__name__)
config = get_config()

# API prefixes for each module
API_PREFIXES = {
    "gateway": "",  # Root API
    "wallet": "/api/wallet",
    "federated": "/api/federated",
    "dashboard": "/api/dashboard",
    "rag": "/api/rag",
    "models": "/api/models",
    "analytics": "/api/analytics",
    "compliance": "/api/compliance",
    "marketplace": "/api/marketplace",
    "datahub": "/api/datahub",
    "system_tools": "/api/system",
    "technical_dashboard": "/api/technical",
    "empoorio": "/api/empoorio",
    "settings": "/api/settings"
}

ROUTE_RATE_LIMITS = {
    "/health": {"limit": 300, "window": 60},
    "/api/system/status": {"limit": 120, "window": 60},
    "/api/auth/login": {"limit": 30, "window": 60},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting AILOOS Unified API Gateway")

    # Startup tasks
    app.state.start_time = time.time()

    yield

    # Shutdown tasks
    logger.info("🛑 Shutting down AILOOS Unified API Gateway")
    shutdown_time = time.time() - app.state.start_time
    logger.info(".2f")


def create_app() -> FastAPI:
    """Create the unified FastAPI application."""

    # Validar configuración segura al inicializar API
    config.ensure_secure_config()

    # Create main app
    app = FastAPI(
        title="AILOOS Unified API Gateway",
        description="Complete API ecosystem for AILOOS decentralized AI platform",
        version="3.0.0",
        lifespan=lifespan
    )

    # Add CORS middleware with environment-specific origins
    cors_origins = config.api.get_cors_origins(config.environment)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=config.environment != "development",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add HTTPS redirect middleware (staging and production)
    if config.environment in ["staging", "production"]:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Add trusted host middleware with environment-specific hosts
    trusted_hosts = config.api.get_trusted_hosts(config.environment)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Add security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)

            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

            # HSTS header (production only)
            if config.environment == "production":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Simple in-memory rate limiter to reduce brute force / flood (per IP)
    class RateLimiterMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, limit: int = 100, window_seconds: int = 60,
                     route_limits: Optional[Dict[str, Dict[str, int]]] = None,
                     redis_client=None):
            super().__init__(app)
            self.limit = limit
            self.window_seconds = window_seconds
            self.route_limits = route_limits or {}
            self.redis = redis_client
            self.requests = {}

        async def _redis_allowed(self, key: str, limit: int, window: int) -> bool:
            try:
                current = await self.redis.incr(key)
                if current == 1:
                    await self.redis.expire(key, window)
                return current <= limit
            except Exception as exc:
                logger.warning(f"Rate limiter Redis backend failed: {exc}")
                return True

        def _memory_allowed(self, key: str, limit: int, window: int, now: float) -> bool:
            window_start = now - window
            timestamps = [t for t in self.requests.get(key, []) if t >= window_start]
            if len(timestamps) >= limit:
                return False
            timestamps.append(now)
            self.requests[key] = timestamps
            return True

        async def dispatch(self, request, call_next):
            client_ip = request.client.host if request.client else "unknown"
            path = request.url.path
            route_cfg = self.route_limits.get(path, {})
            limit = route_cfg.get("limit", self.limit)
            window = route_cfg.get("window", self.window_seconds)
            bucket_key = f"rl:{path}:{client_ip}"
            now = time.time()

            if self.redis:
                allowed = await self._redis_allowed(bucket_key, limit, window)
            else:
                allowed = self._memory_allowed(bucket_key, limit, window, now)

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."}
                )

            return await call_next(request)

    if config.security.enable_rate_limiting:
        redis_client = None
        if aioredis:
            try:
                redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
                if config.redis.password:
                    redis_url = f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/{config.redis.db}"
                redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                logger.info("✅ Rate limiter using Redis backend")
            except Exception as exc:
                logger.warning(f"⚠️ Could not initialize Redis rate limiter backend: {exc}")
                redis_client = None

        app.add_middleware(
            RateLimiterMiddleware,
            limit=config.security.rate_limit_requests_per_minute,
            window_seconds=60,
            route_limits=ROUTE_RATE_LIMITS,
            redis_client=redis_client
        )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_id = str(uuid.uuid4())
        logger.error(f"Unhandled exception [{error_id}]: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_id": error_id}
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Global health check."""
        return {
            "status": "healthy",
            "service": "ailoos-unified-api",
            "version": "3.0.0",
            "timestamp": time.time(),
            "uptime": time.time() - app.state.start_time
        }

    # API info endpoint
    @app.get("/api/info")
    async def api_info():
        """Information about available APIs."""
        return {
            "service": "ailoos-unified-api",
            "version": "3.0.0",
            "apis": list(API_PREFIXES.keys()),
            "endpoints": API_PREFIXES,
            "timestamp": time.time()
        }

    # Mount all available API modules
    mounted_apis = []

    for api_name, create_func in imported_apis.items():
        try:
            if api_name in API_PREFIXES:
                api_app = create_func()
                app.mount(API_PREFIXES[api_name], api_app)
                mounted_apis.append(api_name)
                logger.info(f"✅ {api_name.title()} API mounted at {API_PREFIXES[api_name]}")
        except Exception as e:
            logger.error(f"❌ Failed to mount {api_name} API: {e}")
            # Continue with other APIs

    logger.info(f"🎯 AILOOS Unified API Gateway initialized with {len(mounted_apis)} APIs: {', '.join(mounted_apis)}")

    return app


# Create the global app instance
app = create_app()


def main():
    """Main entry point for the ailoos-api command."""
    import argparse

    parser = argparse.ArgumentParser(description="AILOOS Unified API Gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"🚀 Starting AILOOS API Gateway on {args.host}:{args.port}")

    uvicorn.run(
        "ailoos.api.main:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True
    )


if __name__ == "__main__":
    # Run the unified API server
    uvicorn.run(
        "src.ailoos.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
