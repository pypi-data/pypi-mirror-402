"""
SOC2 Compliance Framework for AILOOS
====================================

Este módulo implementa el marco de cumplimiento SOC2 para AILOOS,
proporcionando controles automatizados y evidence collection para
los 5 criterios principales de SOC2:

- Security (Seguridad)
- Availability (Disponibilidad)
- Processing Integrity (Integridad de Procesamiento)
- Confidentiality (Confidencialidad)
- Privacy (Privacidad)

El sistema aprovecha la arquitectura de seguridad existente de AILOOS
y añade las capas necesarias para cumplimiento SOC2 Type 1 y Type 2.
"""

from .security import SOC2SecurityControls

__all__ = [
    'SOC2SecurityControls',
    # Other modules will be added as they are implemented
    # 'SOC2AvailabilityControls',
    # 'SOC2ProcessingIntegrityControls',
    # 'SOC2ConfidentialityControls',
    # 'SOC2PrivacyControls',
    # 'SOC2AuditSystem',
    # 'SOC2ContinuousMonitoring',
    # 'SOC2ComplianceManager'
]

__version__ = "1.0.0"
__author__ = "AILOOS SOC2 Team"