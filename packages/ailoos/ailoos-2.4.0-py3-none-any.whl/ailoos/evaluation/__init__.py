"""
Sistema de evaluación real para validación de aprendizaje en EmpoorioLM.
Proporciona métricas irrefutables de que el modelo aprende de verdad.
"""

from .real_learning_evaluator import RealLearningEvaluator
from .federated_convergence_metrics import FederatedConvergenceMetrics
from .privacy_preservation_validator import PrivacyPreservationValidator
from .blockchain_audit_validator import BlockchainAuditValidator
from .performance_benchmark import PerformanceBenchmark
from .benchmark_evaluator import BenchmarkEvaluator

__all__ = [
    'RealLearningEvaluator',
    'FederatedConvergenceMetrics',
    'PrivacyPreservationValidator',
    'BlockchainAuditValidator',
    'PerformanceBenchmark',
    'BenchmarkEvaluator'
]