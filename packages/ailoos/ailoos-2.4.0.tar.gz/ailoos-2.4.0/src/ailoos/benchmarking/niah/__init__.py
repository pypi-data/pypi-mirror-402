"""
AILOOS Professional Needle In A Haystack (NIAH) Benchmarking Suite
==================================================================

Industry-standard benchmarking framework for evaluating long context understanding
and retrieval capabilities in large language models.

This module implements the complete NIAH testing methodology used by leading AI
companies (Google, OpenAI, Anthropic) to validate model performance on long contexts.

Features:
- Synthetic dataset generation with controlled needle placement
- Sophisticated evaluation metrics (0-10 scoring)
- Professional heatmap visualization
- Systematic testing across context lengths and depths
- Statistical analysis and reporting
- Integration with AILOOS reasoning capabilities

Usage:
    from ailoos.benchmarking.niah import NIAHGenerator, NIAHEvaluator, NIAHVisualizer, run_niah_benchmark

    # Quick benchmark
    results = run_niah_benchmark(model, context_lengths=[1024, 4096, 8192])

Classes:
    NIAHGenerator: Creates synthetic haystacks with precisely placed needles
    NIAHEvaluator: Evaluates model responses with sophisticated metrics
    NIAHVisualizer: Generates professional heatmaps and reports
    NIAHBenchmark: Orchestrates complete benchmarking campaigns
"""

from .generator import NIAHGenerator, NeedleSpec, HaystackDocument
from .evaluator import NIAHEvaluator, EvaluationResult
from .visualizer import NIAHVisualizer
from .runner import NIAHBenchmark, run_niah_benchmark

__all__ = [
    'NIAHGenerator',
    'NIAHEvaluator',
    'NIAHVisualizer',
    'NIAHBenchmark',
    'run_niah_benchmark'
]

__version__ = "1.0.0"
__author__ = "AILOOS Team"
__description__ = "Professional Needle In A Haystack benchmarking for long context evaluation"