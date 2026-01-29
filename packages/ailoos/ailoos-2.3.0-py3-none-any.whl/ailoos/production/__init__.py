"""
Production Module for AILOOS
Complete production-ready federated training system.
"""

from .orchestrator import ProductionPipelineOrchestrator
from .federated_training import EndToEndFederatedTraining
from .monitoring_dashboard import RealTimeMonitoringDashboard
from .scaling_controller import AutomatedScalingController
from .deployment_manager import ProductionDeploymentManager

__all__ = [
    'ProductionPipelineOrchestrator',
    'EndToEndFederatedTraining',
    'RealTimeMonitoringDashboard',
    'AutomatedScalingController',
    'ProductionDeploymentManager'
]