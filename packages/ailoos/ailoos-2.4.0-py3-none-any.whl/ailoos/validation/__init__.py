"""
Módulo de validaciones avanzadas para AILOOS.
Incluye validaciones de seguridad, rate limiting, errores jerárquicos y auditoría.
"""

from .advanced_validator import (
    AdvancedValidator,
    ValidationError,
    ValidationResult,
    ValidationErrorCode,
    RateLimiter,
    SecurityValidator,
    get_advanced_validator
)

from .error_handler import (
    ErrorHandler,
    ErrorCodes,
    ErrorCode,
    ErrorContext,
    AiloosError,
    create_validation_error,
    create_authentication_error,
    create_authorization_error,
    create_business_error,
    create_system_error,
    get_error_handler
)

from .config_auditor import (
    ConfigAuditor,
    ConfigChange,
    ConfigAuditEvent,
    get_config_auditor
)

from .rate_limiter import (
    RateLimitManager,
    RateLimitRule,
    RateLimitResult,
    RateLimitStrategy,
    RedisRateLimiter,
    check_api_rate_limit,
    check_federated_rate_limit,
    check_marketplace_rate_limit,
    get_rate_limit_manager
)

from .security_validator import (
    AdvancedSecurityValidator,
    PasswordPolicy,
    SecurityValidationResult,
    get_security_validator
)

from .integration_middleware import (
    ValidationMiddleware,
    ValidationMiddlewareConfig,
    create_user_registration_schema,
    create_federated_session_schema,
    create_marketplace_listing_schema,
    get_validation_middleware
)

__all__ = [
    # Advanced Validator
    'AdvancedValidator',
    'ValidationError',
    'ValidationResult',
    'ValidationErrorCode',
    'RateLimiter',
    'SecurityValidator',
    'get_advanced_validator',

    # Error Handler
    'ErrorHandler',
    'ErrorCodes',
    'ErrorCode',
    'ErrorContext',
    'AiloosError',
    'create_validation_error',
    'create_authentication_error',
    'create_authorization_error',
    'create_business_error',
    'create_system_error',
    'get_error_handler',

    # Config Auditor
    'ConfigAuditor',
    'ConfigChange',
    'ConfigAuditEvent',
    'get_config_auditor',

    # Rate Limiter
    'RateLimitManager',
    'RateLimitRule',
    'RateLimitResult',
    'RateLimitStrategy',
    'RedisRateLimiter',
    'check_api_rate_limit',
    'check_federated_rate_limit',
    'check_marketplace_rate_limit',
    'get_rate_limit_manager',

    # Security Validator
    'AdvancedSecurityValidator',
    'PasswordPolicy',
    'SecurityValidationResult',
    'get_security_validator',

    # Integration Middleware
    'ValidationMiddleware',
    'ValidationMiddlewareConfig',
    'create_user_registration_schema',
    'create_federated_session_schema',
    'create_marketplace_listing_schema',
    'get_validation_middleware',
]