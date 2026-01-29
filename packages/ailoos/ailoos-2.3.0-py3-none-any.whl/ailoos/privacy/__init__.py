"""
Sistema de privacidad y cumplimiento GDPR para AILOOS
====================================================

Este módulo proporciona funcionalidades para el cumplimiento del Reglamento General
de Protección de Datos (GDPR), incluyendo exportación de datos personales,
derecho al olvido, gestión de consentimientos y anonimización de datos para analytics.
"""

from .export import ExportService, ExportStatus
from .anonymization import (
    AnonymizationService,
    AnonymizationConfig,
    AnonymizationRule,
    AnonymizationTechnique,
    PrivacyLevel
)
from .pii_filter import (
    PIIFilterService,
    PIIDetector,
    PIIFilterConfig,
    PIIPattern,
    PIICategory,
    PIIAction
)

# New GDPR compliance components
from .data_retention import (
    DataRetentionManager, RetentionRule, RetentionPolicy, DataCategory,
    get_retention_manager, retention_tracked
)
from .consent_management import (
    ConsentManager, ConsentRecord, ConsentCategory, ConsentPurpose, ConsentTemplate,
    get_consent_manager, check_user_consent, grant_user_consent, withdraw_user_consent
)
from .data_deletion import (
    DataDeletionManager, DeletionWorkflow, DeletionTask, DeletionStatus, DataLocation,
    get_deletion_manager, initiate_user_data_deletion, get_deletion_workflow_status
)
from .right_to_erasure_api import RightToErasureAPI, start_right_to_erasure_api

# CCPA compliance components
from .do_not_sell import (
    DoNotSellManager, DoNotSellPreference, DataSaleCategory, ThirdPartyRecipient, DataSaleTransaction,
    get_do_not_sell_manager, set_user_do_not_sell_preference, check_data_sale_compliance,
    record_data_sale_transaction
)
from .ccpa_privacy_api import CCPAPrivacyAPI, start_ccpa_privacy_api

# Web Search Privacy Bridge
from .privacy_web_search_bridge import (
    PrivacyWebSearchBridge,
    SearchOptions,
    SearchResult
)

__all__ = [
    # Existing
    'ExportService',
    'ExportStatus',
    'AnonymizationService',
    'AnonymizationConfig',
    'AnonymizationRule',
    'AnonymizationTechnique',
    'PrivacyLevel',
    'PIIFilterService',
    'PIIDetector',
    'PIIFilterConfig',
    'PIIPattern',
    'PIICategory',
    'PIIAction',

    # Data Retention
    'DataRetentionManager',
    'RetentionRule',
    'RetentionPolicy',
    'DataCategory',
    'get_retention_manager',
    'retention_tracked',

    # Consent Management
    'ConsentManager',
    'ConsentRecord',
    'ConsentCategory',
    'ConsentPurpose',
    'ConsentTemplate',
    'get_consent_manager',
    'check_user_consent',
    'grant_user_consent',
    'withdraw_user_consent',

    # Data Deletion
    'DataDeletionManager',
    'DeletionWorkflow',
    'DeletionTask',
    'DeletionStatus',
    'DataLocation',
    'get_deletion_manager',
    'initiate_user_data_deletion',
    'get_deletion_workflow_status',

    # Right to Erasure API
    'RightToErasureAPI',
    'start_right_to_erasure_api',

    # CCPA Compliance
    'DoNotSellManager',
    'DoNotSellPreference',
    'DataSaleCategory',
    'ThirdPartyRecipient',
    'DataSaleTransaction',
    'get_do_not_sell_manager',
    'set_user_do_not_sell_preference',
    'check_data_sale_compliance',
    'record_data_sale_transaction',
    'CCPAPrivacyAPI',
    'start_ccpa_privacy_api',

    # Web Search Privacy Bridge
    'PrivacyWebSearchBridge',
    'SearchOptions',
    'SearchResult'
]