"""
Financial Compliance Module for AILOOS

Módulos de cumplimiento financiero:
- KYC/AML: Verificación de identidad y monitoreo de transacciones
- DracmaS Compliance: Travel Rule, VASPs y reportes regulatorios
"""

from .kyc_aml import (
    KYCManager, AMLMonitor, KYCProfile, TransactionRecord,
    get_kyc_manager, get_aml_monitor, initiate_kyc, get_kyc_status,
    record_transaction, get_user_risk_report,
    KYCStatus, RiskLevel, TransactionType, SuspiciousActivityType
)

from .dracma_compliance import (
    TravelRuleEngine, TransactionReportingEngine, VASPRegistration,
    TravelRuleTransaction, RegulatoryReport,
    get_travel_rule_engine, get_transaction_reporting_engine,
    register_vasp, process_dracma_transaction, generate_monthly_report,
    VASPStatus, VASPType, TravelRuleStatus
)

__all__ = [
    # KYC/AML
    'KYCManager',
    'AMLMonitor',
    'KYCProfile',
    'TransactionRecord',
    'get_kyc_manager',
    'get_aml_monitor',
    'initiate_kyc',
    'get_kyc_status',
    'record_transaction',
    'get_user_risk_report',
    'KYCStatus',
    'RiskLevel',
    'TransactionType',
    'SuspiciousActivityType',

    # DracmaS Compliance
    'TravelRuleEngine',
    'TransactionReportingEngine',
    'VASPRegistration',
    'TravelRuleTransaction',
    'RegulatoryReport',
    'get_travel_rule_engine',
    'get_transaction_reporting_engine',
    'register_vasp',
    'process_dracma_transaction',
    'generate_monthly_report',
    'VASPStatus',
    'VASPType',
    'TravelRuleStatus'
]