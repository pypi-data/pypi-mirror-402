"""
Workflows Package - FASE 9: Workflows Multimodales
=================================================

Sistema de orquestación para automatizar procesos complejos que combinan:
- Visión (extracción de texto/imágenes)
- Expertos especializados (análisis por dominio)
- Herramientas (cálculos, validaciones)
- Salidas estructuradas

Ejemplos de workflows:
- Auditoría de facturas
- Análisis de contratos
- Diagnóstico médico asistido
- Análisis financiero automatizado
"""

from .engine import WorkflowEngine, WorkflowResult, WorkflowStep
from .templates import WorkflowTemplate, create_document_analysis_workflow
from .validators import WorkflowValidator

__all__ = [
    'WorkflowEngine',
    'WorkflowResult',
    'WorkflowStep',
    'WorkflowTemplate',
    'create_document_analysis_workflow',
    'WorkflowValidator'
]