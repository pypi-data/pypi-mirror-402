"""
Módulo de gestión de usuarios para AILOOS
========================================

Este módulo proporciona funcionalidades para la gestión completa de usuarios,
incluyendo autenticación, perfiles, eliminación de cuentas y más.
"""

from .account_deletion import (
    AccountDeletionService,
    AccountDeletionConfig,
    DeletionStatus,
    DeletionReason,
    DeletionRequest,
    DeletionResult,
    AccountDeletionRequest,
    AccountDeletionStatus,
    AccountDeletionResult,
    get_account_deletion_service,
    create_default_deletion_templates
)

from .stats import (
    UserStatsService,
    ComprehensiveUserStats,
    UserActivityMetrics,
    FederatedLearningStats,
    RewardStats,
    MemoryStats,
    MarketplaceStats,
    UserReputationProfile,
    ActivityType,
    ReputationTier,
    create_user_stats_service,
    get_user_comprehensive_stats,
    get_user_realtime_stats
)

__all__ = [
    # Servicios principales
    'AccountDeletionService',
    'AccountDeletionConfig',
    'UserStatsService',

    # Enums y dataclasses
    'DeletionStatus',
    'DeletionReason',
    'DeletionRequest',
    'DeletionResult',
    'ActivityType',
    'ReputationTier',
    'UserActivityMetrics',
    'FederatedLearningStats',
    'RewardStats',
    'MemoryStats',
    'MarketplaceStats',
    'UserReputationProfile',
    'ComprehensiveUserStats',

    # Modelos Pydantic
    'AccountDeletionRequest',
    'AccountDeletionStatus',
    'AccountDeletionResult',

    # Funciones de utilidad
    'get_account_deletion_service',
    'create_default_deletion_templates',
    'create_user_stats_service',
    'get_user_comprehensive_stats',
    'get_user_realtime_stats'
]