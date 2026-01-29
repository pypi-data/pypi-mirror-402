"""
Sistema de Benchmarking Automático para EmpoorioLM

Este módulo proporciona herramientas completas para benchmarking automático,
comparación de versiones, perfilado de rendimiento, gestión de datasets,
detección de regresiones, generación de reportes y comparación con modelos baseline.

Componentes principales:
- AutomatedBenchmarkRunner: Ejecutor automático de benchmarks
- VersionComparator: Comparación entre versiones del modelo
- PerformanceProfiler: Perfilado detallado de rendimiento y recursos
- BenchmarkDatasetManager: Gestión de datasets de benchmark
- RegressionDetector: Detección automática de regresiones
- BenchmarkReporter: Generación de reportes automáticos
- ModelComparisonFramework: Comparación con modelos baseline (Llama-3, Mistral)

Uso típico:
    from ailoos.benchmarking import (
        AutomatedBenchmarkRunner,
        VersionComparator,
        PerformanceProfiler,
        BenchmarkDatasetManager,
        RegressionDetector,
        BenchmarkReporter,
        ModelComparisonFramework
    )
"""

from .automated_benchmark_runner import AutomatedBenchmarkRunner, BenchmarkConfig, BenchmarkResult
from .version_comparator import VersionComparator, VersionComparison, ComparisonReport
from .performance_profiler import PerformanceProfiler, PerformanceMetrics, ProfilingResult
from .benchmark_dataset_manager import BenchmarkDatasetManager, DatasetConfig, DatasetInfo
from .regression_detector import RegressionDetector, RegressionAlert, BaselineConfig, RegressionReport, RegressionSeverity
from .benchmark_reporter import BenchmarkReporter, ReportConfig, BenchmarkReport
from .model_comparison_framework import ModelComparisonFramework, ComparisonMetrics, ModelComparisonResult, ComparisonTask, run_model_comparison
from .benchmark_config import BenchmarkingConfig, get_config, load_env_config

__all__ = [
    # Main classes
    "AutomatedBenchmarkRunner",
    "VersionComparator",
    "PerformanceProfiler",
    "BenchmarkDatasetManager",
    "RegressionDetector",
    "BenchmarkReporter",
    "ModelComparisonFramework",
    "BenchmarkingConfig",

    # Data classes
    "BenchmarkConfig",
    "BenchmarkResult",
    "VersionComparison",
    "ComparisonReport",
    "PerformanceMetrics",
    "ProfilingResult",
    "DatasetConfig",
    "DatasetInfo",
    "RegressionAlert",
    "BaselineConfig",
    "RegressionReport",
    "RegressionSeverity",
    "ReportConfig",
    "BenchmarkReport",
    "ComparisonMetrics",
    "ModelComparisonResult",
    "ComparisonTask",

    # Functions
    "run_model_comparison",
    "get_config",
    "load_env_config",
]

__version__ = "1.0.0"
__author__ = "Ailoos Team"
__description__ = "Automated benchmarking system for EmpoorioLM"