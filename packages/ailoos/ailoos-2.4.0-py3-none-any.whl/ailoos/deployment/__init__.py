"""
AILOOS Deployment Module

This module provides deployment automation features for AILOOS distributed system.
"""

# GitOps Manager - FASE 5.1
from .gitops_manager import (
    GitOpsOrchestrator, ArgoCDManager, FluxManager, GitOpsConfig,
    GitOpsProvider, Application, SyncStatus, DeploymentStatus,
    create_argocd_setup, demonstrate_gitops
)

# CI/CD Pipeline - FASE 5.1
from .ci_cd_pipeline import (
    CICDPipeline, AutomatedTestingSuite, BlueGreenDeploymentManager,
    RollbackAutomation, PipelineStep, TestResult, Deployment,
    PipelineStage, TestType, DeploymentStrategy, PipelineStatus,
    demonstrate_ci_cd_pipeline
)

# Terraform Infrastructure - FASE 5.1
from .terraform_infrastructure import (
    InfrastructureManager, TerraformManager, CostOptimizationManager,
    MultiRegionManager, InfrastructureComponent, TerraformModule,
    MultiRegionDeployment, CloudProvider, Environment, ResourceType,
    create_production_infrastructure, demonstrate_infrastructure_as_code
)

__all__ = [
    # GitOps Manager
    'GitOpsOrchestrator',
    'ArgoCDManager',
    'FluxManager',
    'GitOpsConfig',
    'GitOpsProvider',
    'Application',
    'SyncStatus',
    'DeploymentStatus',
    'create_argocd_setup',
    'demonstrate_gitops',
    # CI/CD Pipeline
    'CICDPipeline',
    'AutomatedTestingSuite',
    'BlueGreenDeploymentManager',
    'RollbackAutomation',
    'PipelineStep',
    'TestResult',
    'Deployment',
    'PipelineStage',
    'TestType',
    'DeploymentStrategy',
    'PipelineStatus',
    'demonstrate_ci_cd_pipeline',
    # Terraform Infrastructure
    'InfrastructureManager',
    'TerraformManager',
    'CostOptimizationManager',
    'MultiRegionManager',
    'InfrastructureComponent',
    'TerraformModule',
    'MultiRegionDeployment',
    'CloudProvider',
    'Environment',
    'ResourceType',
    'create_production_infrastructure',
    'demonstrate_infrastructure_as_code'
]

__version__ = "1.0.0"