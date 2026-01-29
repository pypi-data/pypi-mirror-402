"""
AILOOS Reasoning Module
=======================

Advanced reasoning capabilities for AILOOS using EmpoorioLM.
Provides problem decomposition, response critiquing, and reflective reasoning.

Components:
- ProblemDecomposer: Breaks down complex problems into manageable steps
- ResponseCritic: Evaluates and improves generated responses
- ReflectionEngine: Analyzes reasoning processes and learns from experience
"""

from .planner import ProblemDecomposer
from .critic import ResponseCritic
from .reflection import ReflectionEngine
from .optimized_reasoning import (
    OptimizedReasoningEngine,
    ReasoningConfig,
    ReasoningResult,
    reason_with_optimized_fase12
)

__all__ = [
    'ProblemDecomposer',
    'ResponseCritic',
    'ReflectionEngine',
    'OptimizedReasoningEngine',
    'ReasoningConfig',
    'ReasoningResult',
    'reason_with_optimized_fase12'
]