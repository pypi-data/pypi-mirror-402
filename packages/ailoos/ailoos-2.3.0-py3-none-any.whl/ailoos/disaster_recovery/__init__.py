"""
AILOOS Disaster Recovery Module

This module provides disaster recovery and business continuity features for AILOOS distributed system.
"""

# Multi-Region Failover - FASE 5.2
from .multi_region_failover import (
    MultiRegionFailoverOrchestrator, CrossRegionDataReplication,
    DNSFailoverManager, ServiceMeshFailoverManager, Region,
    DataReplication, DNSFailoverConfig, ServiceMeshFailover,
    FailoverStrategy, FailoverTrigger, ReplicationType,
    create_production_regions, create_data_replications,
    demonstrate_multi_region_failover
)

# Business Continuity - FASE 5.2
from .business_continuity import (
    IncidentResponseOrchestrator, RTO_RPO_Manager, CommunicationManager,
    Incident, IncidentPlaybook, PlaybookStep, CommunicationTemplate,
    RTO_RPO_Objective, IncidentSeverity, IncidentStatus, RecoveryPhase,
    create_default_rto_rpo_objectives, create_default_playbooks,
    create_default_communication_templates, demonstrate_business_continuity
)

__all__ = [
    # Multi-Region Failover
    'MultiRegionFailoverOrchestrator',
    'CrossRegionDataReplication',
    'DNSFailoverManager',
    'ServiceMeshFailoverManager',
    'Region',
    'DataReplication',
    'DNSFailoverConfig',
    'ServiceMeshFailover',
    'FailoverStrategy',
    'FailoverTrigger',
    'ReplicationType',
    'create_production_regions',
    'create_data_replications',
    'demonstrate_multi_region_failover',
    # Business Continuity
    'IncidentResponseOrchestrator',
    'RTO_RPO_Manager',
    'CommunicationManager',
    'Incident',
    'IncidentPlaybook',
    'PlaybookStep',
    'CommunicationTemplate',
    'RTO_RPO_Objective',
    'IncidentSeverity',
    'IncidentStatus',
    'RecoveryPhase',
    'create_default_rto_rpo_objectives',
    'create_default_playbooks',
    'create_default_communication_templates',
    'demonstrate_business_continuity'
]

__version__ = "1.0.0"