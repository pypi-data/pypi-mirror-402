"""
AILOOS Feedback Loops System
===========================

Sistema completo de feedback loops para mejora continua de EmpoorioLM.

Este módulo proporciona todas las funcionalidades necesarias para:
- Recopilar feedback de usuarios y sistemas
- Analizar patrones y tendencias
- Generar tareas de entrenamiento basadas en feedback
- Mejorar continuamente el rendimiento del modelo
- Evaluar la calidad del feedback recibido

Componentes principales:
- FeedbackCollector: Recolección y anonimización de feedback
- FeedbackAnalyzer: Análisis inteligente de patrones
- FeedbackDrivenTrainer: Entrenamiento basado en feedback
- UserInteractionTracker: Seguimiento de interacciones
- ContinuousImprovementEngine: Motor de mejora continua
- FeedbackQualityAssessor: Evaluación de calidad del feedback
"""

from .feedback_collector import (
    FeedbackCollector,
    FeedbackEntry,
    FeedbackType,
    FeedbackSource
)

from .feedback_analyzer import (
    FeedbackAnalyzer,
    FeedbackInsight
)

from .feedback_driven_trainer import (
    FeedbackDrivenTrainer,
    TrainingTask,
    FeedbackDataGenerator
)

from .user_interaction_tracker import (
    UserInteractionTracker,
    UserInteraction,
    SessionSummary
)

from .continuous_improvement_engine import (
    ContinuousImprovementEngine,
    ImprovementCycle
)

from .feedback_quality_assessor import (
    FeedbackQualityAssessor,
    QualityAssessment,
    FeedbackQuality
)

__all__ = [
    # FeedbackCollector
    'FeedbackCollector',
    'FeedbackEntry',
    'FeedbackType',
    'FeedbackSource',

    # FeedbackAnalyzer
    'FeedbackAnalyzer',
    'FeedbackInsight',

    # FeedbackDrivenTrainer
    'FeedbackDrivenTrainer',
    'TrainingTask',
    'FeedbackDataGenerator',

    # UserInteractionTracker
    'UserInteractionTracker',
    'UserInteraction',
    'SessionSummary',

    # ContinuousImprovementEngine
    'ContinuousImprovementEngine',
    'ImprovementCycle',

    # FeedbackQualityAssessor
    'FeedbackQualityAssessor',
    'QualityAssessment',
    'FeedbackQuality'
]

__version__ = "1.0.0"
__author__ = "AILOOS Team"
__description__ = "Sistema de feedback loops para mejora continua de modelos de IA"