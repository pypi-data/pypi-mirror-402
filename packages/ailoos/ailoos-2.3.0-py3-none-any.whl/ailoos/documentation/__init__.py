"""
AILOOS Documentation Module

This module provides comprehensive documentation and training features for AILOOS distributed system.
"""

# Production Runbooks - FASE 5.4
from .production_runbooks import (
    ProductionRunbookManager, Runbook, RunbookStep, DeploymentProcedure,
    TroubleshootingGuide, MaintenanceSchedule, RunbookType, DeploymentType,
    MaintenanceWindow, create_deployment_runbooks, create_troubleshooting_guides,
    create_maintenance_schedules, demonstrate_production_runbooks
)

# Team Training - FASE 5.4
from .team_training import (
    TeamTrainingOrchestrator, SecurityAwarenessManager, IncidentResponseTrainingManager,
    ComplianceTrainingManager, TrainingModule, TrainingSession, Certification,
    SecurityAwarenessCampaign, IncidentSimulation, TrainingType, TrainingLevel,
    CertificationStatus, create_default_modules, create_default_simulations,
    demonstrate_team_training
)

__all__ = [
    # Production Runbooks
    'ProductionRunbookManager',
    'Runbook',
    'RunbookStep',
    'DeploymentProcedure',
    'TroubleshootingGuide',
    'MaintenanceSchedule',
    'RunbookType',
    'DeploymentType',
    'MaintenanceWindow',
    'create_deployment_runbooks',
    'create_troubleshooting_guides',
    'create_maintenance_schedules',
    'demonstrate_production_runbooks',
    # Team Training
    'TeamTrainingOrchestrator',
    'SecurityAwarenessManager',
    'IncidentResponseTrainingManager',
    'ComplianceTrainingManager',
    'TrainingModule',
    'TrainingSession',
    'Certification',
    'SecurityAwarenessCampaign',
    'IncidentSimulation',
    'TrainingType',
    'TrainingLevel',
    'CertificationStatus',
    'create_default_modules',
    'create_default_simulations',
    'demonstrate_team_training'
]

__version__ = "1.0.0"