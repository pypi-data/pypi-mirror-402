"""
Framework Completo de Comparación de Precisión para EmpoorioLM vs Gigantes
Consolida métricas de precisión, latencia, energía y RAG con análisis estadístico avanzado,
reportes comparativos automáticos y visualizaciones avanzadas.
"""

import os
import sys
import time
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import statistics
from datetime import datetime

# Imports para análisis estadístico
try:
    import numpy as np
    import scipy.stats as stats
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False
    print("⚠️ scipy/numpy no disponibles, análisis estadístico limitado")

# Imports para visualizaciones
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    PLOTTING_AVAILABLE = True
    plt.style.use('seaborn-v0_8' if hasattr(plt.style, 'available') and 'seaborn-v0_8' in plt.style.available else 'default')
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️ matplotlib/seaborn/pandas no disponibles, visualizaciones deshabilitadas")

# Añadir src al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Imports de módulos existentes (se importan después de las definiciones de clase)
BENCHMARK_AVAILABLE = False
ENERGY_TRACKER_AVAILABLE = False
LATENCY_TESTER_AVAILABLE = False
RAG_EVALUATOR_AVAILABLE = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('accuracy_comparison.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AccuracyComparisonConfig:
    """Configuración del framework de comparación de precisión."""
    # Configuración general
    models_to_compare: List[str] = field(default_factory=lambda: ['empoorio', 'gpt4', 'claude', 'gemini'])
    output_dir: str = './accuracy_comparison_results'
    enable_statistical_analysis: bool = True
    confidence_level: float = 0.95
    enable_market_headlines: bool = True

    # Configuración de benchmarks existentes (se inicializan después de importar)
    benchmark_config: Any = None
    energy_config: Any = None
    latency_config: Any = None
    rag_config: Any = None

    # Configuración específica del framework
    generate_comprehensive_report: bool = True
    generate_executive_summary: bool = True
    enable_advanced_visualizations: bool = True
    save_raw_data: bool = True

    # Umbrales para análisis de mercado
    efficiency_threshold: float = 1.5  # X veces más eficiente
    accuracy_threshold: float = 0.05   # Y% más preciso
    latency_threshold: float = 0.8     # Z segundos más rápido


@dataclass
class StatisticalComparison:
    """Resultados de comparación estadística entre dos modelos."""
    model_a: str
    model_b: str
    metric: str
    mean_a: float
    mean_b: float
    difference: float
    relative_difference: float
    p_value: float
    significant: bool
    confidence_interval: Tuple[float, float]
    effect_size: float  # Cohen's d
    sample_size_a: int
    sample_size_b: int


@dataclass
class MarketHeadline:
    """Titular de mercado generado automáticamente."""
    headline: str
    metric: str
    model: str
    competitor: str
    improvement: float
    significance: str
    category: str  # 'efficiency', 'accuracy', 'latency', 'rag'


@dataclass
class ComprehensiveMetrics:
    """Métricas consolidadas de un modelo."""
    model_name: str

    # Métricas de precisión
    accuracy_mmlu: float = 0.0
    accuracy_gsm8k: float = 0.0
    accuracy_overall: float = 0.0

    # Métricas de latencia
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    time_to_first_token: float = 0.0
    throughput: float = 0.0

    # Métricas de energía
    total_energy_joules: float = 0.0
    joules_per_token: float = 0.0
    tokens_per_watt: float = 0.0
    carbon_emissions_kg: float = 0.0

    # Métricas RAG
    rag_accuracy: float = 0.0
    rag_context_sizes: List[int] = field(default_factory=list)
    rag_performance_curve: Dict[int, float] = field(default_factory=dict)

    # Métricas derivadas
    efficiency_score: float = 0.0  # accuracy / (latency * energy)
    intelligence_per_watt: float = 0.0  # accuracy * tokens_per_watt

    # Metadata
    sample_count: int = 0
    evaluation_timestamp: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)


class AccuracyComparisonFramework:
    """
    Framework completo para comparación de precisión entre EmpoorioLM y modelos gigantes.
    Consolida todas las métricas de benchmark con análisis estadístico avanzado.
    """

    def __init__(self, config: AccuracyComparisonConfig = None):
        self.config = config or AccuracyComparisonConfig()
        self.comprehensive_metrics: Dict[str, ComprehensiveMetrics] = {}
        self.statistical_comparisons: List[StatisticalComparison] = []
        self.market_headlines: List[MarketHeadline] = []

        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)

        # Inicializar componentes
        self._init_components()

        logger.info("🚀 AccuracyComparisonFramework inicializado")

    def _init_components(self):
        """Inicializar componentes del framework."""
        self.benchmark_runner = None
        self.energy_tracker = None
        self.latency_tester = None
        self.rag_evaluator = None

        # Inicializar configuraciones si no están definidas
        if BENCHMARK_AVAILABLE:
            from scripts.benchmark_vs_giants import BenchmarkConfig
            if self.config.benchmark_config is None:
                self.config.benchmark_config = BenchmarkConfig()

        if ENERGY_TRACKER_AVAILABLE:
            from ailoos.benchmarking.energy_tracker import EnergyTrackerConfig
            if self.config.energy_config is None:
                self.config.energy_config = EnergyTrackerConfig()

        if LATENCY_TESTER_AVAILABLE:
            from ailoos.benchmarking.latency_tester import LatencyTestConfig
            if self.config.latency_config is None:
                self.config.latency_config = LatencyTestConfig()

        if RAG_EVALUATOR_AVAILABLE:
            from ailoos.benchmarking.rag_needle_evaluator import RagNeedleConfig
            if self.config.rag_config is None:
                self.config.rag_config = RagNeedleConfig()

        if BENCHMARK_AVAILABLE and self.config.benchmark_config:
            from scripts.benchmark_vs_giants import BenchmarkRunner
            self.benchmark_runner = BenchmarkRunner(self.config.benchmark_config)
            logger.info("✅ BenchmarkRunner inicializado")

        if ENERGY_TRACKER_AVAILABLE and self.config.energy_config:
            from ailoos.benchmarking.energy_tracker import EnergyTracker
            self.energy_tracker = EnergyTracker(self.config.energy_config)
            logger.info("✅ EnergyTracker inicializado")

        if LATENCY_TESTER_AVAILABLE and self.config.latency_config:
            from ailoos.benchmarking.latency_tester import LatencyTester
            self.latency_tester = LatencyTester(self.config.latency_config)
            logger.info("✅ LatencyTester inicializado")

        if RAG_EVALUATOR_AVAILABLE and self.config.rag_config:
            from ailoos.benchmarking.rag_needle_evaluator import RagNeedleEvaluator
            self.rag_evaluator = RagNeedleEvaluator(self.config.rag_config)
            logger.info("✅ RagNeedleEvaluator inicializado")

    def run_comprehensive_comparison(self) -> Dict[str, ComprehensiveMetrics]:
        """
        Ejecuta comparación completa consolidando todas las métricas.
        """
        logger.info("🚀 Iniciando comparación comprehensiva de precisión")

        # Ejecutar benchmarks individuales
        benchmark_results = self._run_benchmark_comparison()
        latency_results = self._run_latency_comparison()
        energy_results = self._run_energy_comparison()
        rag_results = self._run_rag_comparison()

        # Consolidar métricas
        self._consolidate_metrics(benchmark_results, latency_results, energy_results, rag_results)

        # Realizar análisis estadístico
        if self.config.enable_statistical_analysis and STATISTICS_AVAILABLE:
            self._perform_statistical_analysis()

        # Generar titulares de mercado
        if self.config.enable_market_headlines:
            self._generate_market_headlines()

        logger.info("✅ Comparación comprehensiva completada")
        return self.comprehensive_metrics

    def _run_benchmark_comparison(self) -> Dict[str, List[Any]]:
        """Ejecuta comparación de benchmarks de precisión."""
        if not self.benchmark_runner:
            logger.warning("⚠️ BenchmarkRunner no disponible")
            return {}

        logger.info("📊 Ejecutando benchmarks de precisión")
        results = self.benchmark_runner.run_benchmark()

        # Agrupar por modelo
        grouped_results = {}
        for result in results:
            if result.model_name not in grouped_results:
                grouped_results[result.model_name] = []
            grouped_results[result.model_name].append(result)

        return grouped_results

    def _run_latency_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Ejecuta comparación de latencias detalladas."""
        if not self.latency_tester:
            logger.warning("⚠️ LatencyTester no disponible")
            return {}

        logger.info("🧪 Ejecutando pruebas de latencia detalladas")
        # Usar prompts de prueba del latency tester
        test_prompts = self.latency_tester._generate_test_prompts()[:10]  # Limitar para eficiencia

        results = {}
        for model_name in self.config.models_to_compare:
            if model_name in self.benchmark_runner.models:
                model_wrapper = self.benchmark_runner.models[model_name]
                try:
                    model_results = self.latency_tester.run_latency_tests(model_wrapper, model_name, test_prompts)
                    results[model_name] = model_results
                except Exception as e:
                    logger.error(f"Error en pruebas de latencia para {model_name}: {e}")

        return results

    def _run_energy_comparison(self) -> Dict[str, Any]:
        """Ejecuta comparación de consumo energético."""
        if not self.energy_tracker:
            logger.warning("⚠️ EnergyTracker no disponible")
            return {}

        logger.info("🔋 Ejecutando medición de consumo energético")

        results = {}
        for model_name in self.config.models_to_compare:
            if model_name in self.benchmark_runner.models:
                model_wrapper = self.benchmark_runner.models[model_name]
                try:
                    # Medir energía durante una inferencia de prueba
                    with self.energy_tracker.track_inference(tokens_expected=100):
                        model_wrapper.generate("Test prompt for energy measurement", max_tokens=50)

                    metrics = self.energy_tracker.stop_monitoring(tokens_generated=50, accuracy=0.8)
                    results[model_name] = metrics
                except Exception as e:
                    logger.error(f"Error en medición energética para {model_name}: {e}")

        return results

    def _run_rag_comparison(self) -> Dict[str, List[Any]]:
        """Ejecuta comparación RAG needle-in-haystack."""
        if not self.rag_evaluator:
            logger.warning("⚠️ RagNeedleEvaluator no disponible")
            return {}

        logger.info("🧪 Ejecutando evaluación RAG needle-in-haystack")
        results = self.rag_evaluator.run_evaluation()

        # Agrupar por modelo
        grouped_results = {}
        for result in results:
            if result.model_name not in grouped_results:
                grouped_results[result.model_name] = []
            grouped_results[result.model_name].append(result)

        return grouped_results

    def _consolidate_metrics(self, benchmark_results: Dict, latency_results: Dict,
                           energy_results: Dict, rag_results: Dict):
        """Consolida todas las métricas en ComprehensiveMetrics."""
        logger.info("🔄 Consolidando métricas comprehensivas")

        for model_name in self.config.models_to_compare:
            metrics = ComprehensiveMetrics(
                model_name=model_name,
                evaluation_timestamp=datetime.now().isoformat()
            )

            # Consolidar precisión
            if model_name in benchmark_results:
                model_benchmarks = benchmark_results[model_name]
                mmlu_results = [r for r in model_benchmarks if r.dataset == 'mmlu']
                gsm8k_results = [r for r in model_benchmarks if r.dataset == 'gsm8k']

                if mmlu_results:
                    metrics.accuracy_mmlu = statistics.mean([r.accuracy for r in mmlu_results])
                if gsm8k_results:
                    metrics.accuracy_gsm8k = statistics.mean([r.accuracy for r in gsm8k_results])

                metrics.accuracy_overall = statistics.mean([r.accuracy for r in model_benchmarks])
                metrics.sample_count = len(model_benchmarks)

            # Consolidar latencia
            if model_name in latency_results:
                model_latencies = latency_results[model_name]
                all_latencies = []
                all_ttft = []
                all_throughput = []

                for config_key, latency_metrics in model_latencies.items():
                    if latency_metrics.successful_requests > 0:
                        all_latencies.extend(latency_metrics.raw_latencies)
                        all_ttft.extend(latency_metrics.raw_ttft)
                        all_throughput.extend(latency_metrics.raw_throughputs)

                if all_latencies:
                    metrics.avg_latency = statistics.mean(all_latencies)
                    metrics.p95_latency = statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else max(all_latencies)
                if all_ttft:
                    metrics.time_to_first_token = statistics.mean(all_ttft)
                if all_throughput:
                    metrics.throughput = statistics.mean(all_throughput)

            # Consolidar energía
            if model_name in energy_results:
                energy_metrics = energy_results[model_name]
                metrics.total_energy_joules = energy_metrics.total_energy_joules
                metrics.joules_per_token = energy_metrics.joules_per_token
                metrics.tokens_per_watt = energy_metrics.tokens_per_watt
                metrics.carbon_emissions_kg = energy_metrics.carbon_emissions_kg

            # Consolidar RAG
            if model_name in rag_results:
                model_rag = rag_results[model_name]
                if model_rag:
                    accuracies = [r.accuracy for r in model_rag]
                    metrics.rag_accuracy = statistics.mean(accuracies) if accuracies else 0.0

                    # Curva de rendimiento por tamaño de contexto
                    context_performance = {}
                    for result in model_rag:
                        size = result.context_size
                        if size not in context_performance:
                            context_performance[size] = []
                        context_performance[size].append(result.accuracy)

                    metrics.rag_context_sizes = sorted(context_performance.keys())
                    metrics.rag_performance_curve = {
                        size: statistics.mean(accs) for size, accs in context_performance.items()
                    }

            # Calcular métricas derivadas
            metrics.efficiency_score = self._calculate_efficiency_score(metrics)
            metrics.intelligence_per_watt = metrics.accuracy_overall * metrics.tokens_per_watt

            # Guardar datos crudos
            if self.config.save_raw_data:
                metrics.raw_data = {
                    'benchmark_results': benchmark_results.get(model_name, []),
                    'latency_results': latency_results.get(model_name, {}),
                    'energy_results': energy_results.get(model_name, {}),
                    'rag_results': rag_results.get(model_name, [])
                }

            self.comprehensive_metrics[model_name] = metrics

    def _calculate_efficiency_score(self, metrics: ComprehensiveMetrics) -> float:
        """Calcula score de eficiencia combinando precisión, latencia y energía."""
        if metrics.avg_latency == 0 or metrics.total_energy_joules == 0:
            return 0.0

        # Score = accuracy / (normalized_latency * normalized_energy)
        # Normalizar latencia (asumiendo baseline de 1s)
        norm_latency = metrics.avg_latency / 1.0
        # Normalizar energía (asumiendo baseline de 10J)
        norm_energy = metrics.total_energy_joules / 10.0

        return metrics.accuracy_overall / (norm_latency * norm_energy)

    def _perform_statistical_analysis(self):
        """Realiza análisis estadístico entre modelos."""
        logger.info("📊 Realizando análisis estadístico")

        if not STATISTICS_AVAILABLE:
            logger.warning("scipy no disponible, saltando análisis estadístico")
            return

        metrics_to_compare = [
            ('accuracy_overall', 'accuracy'),
            ('avg_latency', 'latency'),
            ('total_energy_joules', 'energy'),
            ('rag_accuracy', 'rag_accuracy')
        ]

        for metric_attr, metric_name in metrics_to_compare:
            for i, model_a in enumerate(self.config.models_to_compare):
                for j, model_b in enumerate(self.config.models_to_compare):
                    if i >= j:  # Evitar comparaciones duplicadas
                        continue

                    metrics_a = self.comprehensive_metrics.get(model_a)
                    metrics_b = self.comprehensive_metrics.get(model_b)

                    if not metrics_a or not metrics_b:
                        continue

                    # Obtener datos para comparación
                    data_a = self._extract_metric_data(metrics_a, metric_attr)
                    data_b = self._extract_metric_data(metrics_b, metric_attr)

                    if not data_a or not data_b:
                        continue

                    # Realizar prueba estadística
                    comparison = self._statistical_test(data_a, data_b, model_a, model_b, metric_name)
                    if comparison:
                        self.statistical_comparisons.append(comparison)

    def _extract_metric_data(self, metrics: ComprehensiveMetrics, metric_attr: str) -> List[float]:
        """Extrae datos de una métrica específica para análisis estadístico."""
        if metric_attr == 'accuracy_overall':
            # Para precisión, usar datos crudos de benchmarks
            raw_data = metrics.raw_data.get('benchmark_results', [])
            return [r.accuracy for r in raw_data] if raw_data else [metrics.accuracy_overall]

        elif metric_attr == 'avg_latency':
            # Para latencia, usar datos crudos de latency tests
            raw_data = metrics.raw_data.get('latency_results', {})
            all_latencies = []
            for config_results in raw_data.values():
                if hasattr(config_results, 'raw_latencies'):
                    all_latencies.extend(config_results.raw_latencies)
            return all_latencies if all_latencies else [metrics.avg_latency]

        elif metric_attr == 'total_energy_joules':
            # Para energía, usar datos crudos si disponibles
            return [metrics.total_energy_joules]

        elif metric_attr == 'rag_accuracy':
            # Para RAG, usar datos crudos de RAG evaluation
            raw_data = metrics.raw_data.get('rag_results', [])
            return [r.accuracy for r in raw_data] if raw_data else [metrics.rag_accuracy]

        return []

    def _statistical_test(self, data_a: List[float], data_b: List[float],
                         model_a: str, model_b: str, metric: str) -> Optional[StatisticalComparison]:
        """Realiza prueba estadística entre dos conjuntos de datos."""
        try:
            # Calcular estadísticas básicas
            mean_a = statistics.mean(data_a)
            mean_b = statistics.mean(data_b)
            diff = mean_a - mean_b
            rel_diff = diff / mean_b if mean_b != 0 else 0

            # Prueba t de Student (asumiendo distribuciones normales)
            if len(data_a) >= 3 and len(data_b) >= 3:
                t_stat, p_value = stats.ttest_ind(data_a, data_b, equal_var=False)
            else:
                # Para muestras pequeñas, usar Mann-Whitney U test
                u_stat, p_value = stats.mannwhitneyu(data_a, data_b, alternative='two-sided')

            # Determinar significancia
            significant = p_value < (1 - self.config.confidence_level)

            # Calcular intervalo de confianza para la diferencia de medias
            if len(data_a) >= 2 and len(data_b) >= 2:
                # Usar bootstrap para intervalo de confianza
                n_bootstrap = 1000
                bootstrap_diffs = []
                for _ in range(n_bootstrap):
                    sample_a = np.random.choice(data_a, size=len(data_a), replace=True)
                    sample_b = np.random.choice(data_b, size=len(data_b), replace=True)
                    bootstrap_diffs.append(np.mean(sample_a) - np.mean(sample_b))

                ci_lower = np.percentile(bootstrap_diffs, (1 - self.config.confidence_level) / 2 * 100)
                ci_upper = np.percentile(bootstrap_diffs, (1 - self.config.confidence_level + (1 - self.config.confidence_level) / 2) * 100)
                confidence_interval = (ci_lower, ci_upper)
            else:
                confidence_interval = (diff, diff)  # Sin intervalo si datos insuficientes

            # Calcular tamaño del efecto (Cohen's d)
            pooled_std = np.sqrt((np.std(data_a, ddof=1)**2 + np.std(data_b, ddof=1)**2) / 2)
            effect_size = diff / pooled_std if pooled_std != 0 else 0

            return StatisticalComparison(
                model_a=model_a,
                model_b=model_b,
                metric=metric,
                mean_a=mean_a,
                mean_b=mean_b,
                difference=diff,
                relative_difference=rel_diff,
                p_value=p_value,
                significant=significant,
                confidence_interval=confidence_interval,
                effect_size=effect_size,
                sample_size_a=len(data_a),
                sample_size_b=len(data_b)
            )

        except Exception as e:
            logger.debug(f"Error en prueba estadística {model_a} vs {model_b} ({metric}): {e}")
            return None

    def _generate_market_headlines(self):
        """Genera titulares de mercado basados en las comparaciones."""
        logger.info("📰 Generando titulares de mercado")

        # Comparar EmpoorioLM con cada gigante
        empoorio_metrics = self.comprehensive_metrics.get('empoorio')
        if not empoorio_metrics:
            return

        for competitor in ['gpt4', 'claude', 'gemini']:
            competitor_metrics = self.comprehensive_metrics.get(competitor)
            if not competitor_metrics:
                continue

            # Generar titulares para cada métrica
            self._generate_headline_for_metric(empoorio_metrics, competitor_metrics, competitor, 'accuracy')
            self._generate_headline_for_metric(empoorio_metrics, competitor_metrics, competitor, 'latency')
            self._generate_headline_for_metric(empoorio_metrics, competitor_metrics, competitor, 'energy')
            self._generate_headline_for_metric(empoorio_metrics, competitor_metrics, competitor, 'efficiency')

    def _generate_headline_for_metric(self, empoorio: ComprehensiveMetrics,
                                    competitor: ComprehensiveMetrics, competitor_name: str, metric: str):
        """Genera titular para una métrica específica."""
        try:
            if metric == 'accuracy':
                emp_value = empoorio.accuracy_overall
                comp_value = competitor.accuracy_overall
                unit = "%"
                improvement = (emp_value - comp_value) / comp_value * 100

                if improvement >= self.config.accuracy_threshold:
                    headline = f"EmpoorioLM {improvement:+.1f}% más preciso que {competitor_name.upper()} en benchmarks"
                    category = 'accuracy'

            elif metric == 'latency':
                emp_value = empoorio.avg_latency
                comp_value = competitor.avg_latency
                unit = "s"
                improvement = (comp_value - emp_value) / comp_value * 100  # Positivo = más rápido

                if improvement >= self.config.latency_threshold:
                    headline = f"EmpoorioLM {improvement:.1f}% más rápido que {competitor_name.upper()}"
                    category = 'latency'

            elif metric == 'energy':
                emp_value = empoorio.total_energy_joules
                comp_value = competitor.total_energy_joules
                unit = "J"
                efficiency_ratio = comp_value / emp_value if emp_value > 0 else 1

                if efficiency_ratio >= self.config.efficiency_threshold:
                    headline = f"EmpoorioLM {efficiency_ratio:.1f}x más eficiente energéticamente que {competitor_name.upper()}"
                    category = 'efficiency'
                    improvement = efficiency_ratio

            elif metric == 'efficiency':
                emp_value = empoorio.efficiency_score
                comp_value = competitor.efficiency_score
                efficiency_ratio = emp_value / comp_value if comp_value > 0 else 1

                if efficiency_ratio >= self.config.efficiency_threshold:
                    headline = f"EmpoorioLM {efficiency_ratio:.1f}x más eficiente en general que {competitor_name.upper()}"
                    category = 'efficiency'
                    improvement = efficiency_ratio

            else:
                return

            # Determinar significancia
            stat_comp = None
            for comp in self.statistical_comparisons:
                if ((comp.model_a == 'empoorio' and comp.model_b == competitor_name) or
                    (comp.model_a == competitor_name and comp.model_b == 'empoorio')) and comp.metric == metric:
                    stat_comp = comp
                    break

            significance = "estadísticamente significativo" if stat_comp and stat_comp.significant else "preliminar"

            self.market_headlines.append(MarketHeadline(
                headline=headline,
                metric=metric,
                model='empoorio',
                competitor=competitor_name,
                improvement=improvement,
                significance=significance,
                category=category
            ))

        except Exception as e:
            logger.debug(f"Error generando titular para {metric}: {e}")

    def generate_comprehensive_report(self):
        """Genera reporte comprehensivo con todas las métricas y análisis."""
        logger.info("📊 Generando reporte comprehensivo")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Reporte JSON completo
        json_file = os.path.join(self.config.output_dir, f'comprehensive_comparison_{timestamp}.json')
        report_data = {
            'timestamp': timestamp,
            'config': self.config.__dict__,
            'comprehensive_metrics': {k: v.__dict__ for k, v in self.comprehensive_metrics.items()},
            'statistical_comparisons': [comp.__dict__ for comp in self.statistical_comparisons],
            'market_headlines': [h.__dict__ for h in self.market_headlines]
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Reporte ejecutivo
        if self.config.generate_executive_summary:
            self._generate_executive_summary(timestamp)

        # Visualizaciones avanzadas
        if self.config.enable_advanced_visualizations and PLOTTING_AVAILABLE:
            self._generate_advanced_visualizations(timestamp)

        logger.info(f"📁 Reportes guardados en {self.config.output_dir}")

    def _generate_executive_summary(self, timestamp: str):
        """Genera resumen ejecutivo con titulares de mercado."""
        summary_file = os.path.join(self.config.output_dir, f'executive_summary_{timestamp}.txt')

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("🚀 EmpoorioLM vs Gigantes - Resumen Ejecutivo\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Titulares principales
            f.write("📰 TITULARES PRINCIPALES\n")
            f.write("-" * 30 + "\n")
            for headline in self.market_headlines[:5]:  # Top 5 headlines
                f.write(f"• {headline.headline}\n")
            f.write("\n")

            # Tabla comparativa
            f.write("📊 TABLA COMPARATIVA\n")
            f.write("-" * 30 + "\n")
            f.write("<10")
            f.write("-" * 50 + "\n")

            for model_name, metrics in self.comprehensive_metrics.items():
                f.write("<10"
                        "<10.3f"
                        "<10.3f"
                        "<10.1f"
                        "<10.3f"
                        "<10.3f"
                        "<10.3f\n")

            f.write("\n")

            # Análisis estadístico
            if self.statistical_comparisons:
                f.write("📈 ANÁLISIS ESTADÍSTICO\n")
                f.write("-" * 30 + "\n")
                significant_comparisons = [c for c in self.statistical_comparisons if c.significant]
                f.write(f"Comparaciones estadísticamente significativas: {len(significant_comparisons)}\n\n")

                for comp in significant_comparisons[:3]:  # Top 3 significant comparisons
                    f.write(f"• {comp.model_a.upper()} vs {comp.model_b.upper()} ({comp.metric}):\n")
                    f.write(f"  Diferencia: {comp.difference:.3f} ({comp.relative_difference:+.1%})\n")
                    f.write(f"  p-value: {comp.p_value:.4f}, Tamaño del efecto: {comp.effect_size:.2f}\n\n")

            # Conclusiones
            f.write("💡 CONCLUSIONES\n")
            f.write("-" * 30 + "\n")
            f.write("Este análisis comprehensivo demuestra el rendimiento relativo de EmpoorioLM\n")
            f.write("frente a los modelos líderes de la industria. Los resultados incluyen\n")
            f.write("métricas de precisión, latencia, consumo energético y capacidad RAG,\n")
            f.write("con análisis estadístico para validar la significancia de las diferencias.\n")

        logger.info(f"📋 Resumen ejecutivo guardado: {summary_file}")

    def _generate_advanced_visualizations(self, timestamp: str):
        """Genera visualizaciones avanzadas."""
        if not PLOTTING_AVAILABLE:
            return

        # Preparar datos
        df = pd.DataFrame([{
            'model': k,
            'accuracy': v.accuracy_overall,
            'latency': v.avg_latency,
            'energy': v.total_energy_joules,
            'efficiency': v.efficiency_score,
            'rag_accuracy': v.rag_accuracy
        } for k, v in self.comprehensive_metrics.items()])

        if df.empty:
            return

        # Gráfico radar de rendimiento multi-dimensional
        self._create_radar_plot(df, timestamp)

        # Gráfico de eficiencia (accuracy vs energy efficiency)
        self._create_efficiency_plot(df, timestamp)

        # Gráfico de distribución de latencias (si hay datos)
        self._create_latency_distribution_plot(timestamp)

        # Gráfico de curva RAG por contexto
        self._create_rag_curve_plot(timestamp)

        logger.info(f"📈 Visualizaciones avanzadas guardadas")

    def _create_radar_plot(self, df: pd.DataFrame, timestamp: str):
        """Crea gráfico radar de rendimiento multi-dimensional."""
        # Normalizar métricas para radar plot
        metrics = ['accuracy', 'latency', 'energy', 'efficiency', 'rag_accuracy']

        # Normalizar (invertir latencia y energía ya que menores son mejores)
        df_norm = df.copy()
        for metric in metrics:
            if metric in ['latency', 'energy']:
                # Invertir y normalizar (menor = mejor)
                min_val = df[metric].min()
                max_val = df[metric].max()
                df_norm[metric] = 1 - (df[metric] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            else:
                # Normalizar (mayor = mejor)
                min_val = df[metric].min()
                max_val = df[metric].max()
                df_norm[metric] = (df[metric] - min_val) / (max_val - min_val) if max_val != min_val else 0.5

        # Crear radar plot
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # Cerrar el círculo

        for _, row in df_norm.iterrows():
            values = [row[metric] for metric in metrics]
            values += values[:1]  # Cerrar el círculo

            ax.plot(angles, values, 'o-', linewidth=2, label=row['model'])
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 1)
        ax.set_title('Comparación Multi-dimensional de Rendimiento', size=16, fontweight='bold')
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)

        plt.tight_layout()
        radar_file = os.path.join(self.config.output_dir, f'radar_comparison_{timestamp}.png')
        plt.savefig(radar_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_efficiency_plot(self, df: pd.DataFrame, timestamp: str):
        """Crea gráfico de eficiencia (accuracy vs energy efficiency)."""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot con tamaño basado en latencia
        scatter = ax.scatter(df['energy'], df['accuracy'],
                           s=df['latency'] * 100,  # Tamaño basado en latencia (invertido)
                           c=df['efficiency'], cmap='viridis', alpha=0.7, edgecolors='black')

        # Etiquetas
        for _, row in df.iterrows():
            ax.annotate(row['model'].upper(), (row['energy'], row['accuracy']),
                       xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')

        ax.set_xlabel('Consumo Energético (J)', fontsize=12)
        ax.set_ylabel('Precisión', fontsize=12)
        ax.set_title('Eficiencia: Precisión vs Consumo Energético\n(Tamaño = Latencia)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Colorbar
        cbar = plt.colorbar(scatter)
        cbar.set_label('Score de Eficiencia', fontsize=10)

        plt.tight_layout()
        efficiency_file = os.path.join(self.config.output_dir, f'efficiency_plot_{timestamp}.png')
        plt.savefig(efficiency_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_latency_distribution_plot(self, timestamp: str):
        """Crea gráfico de distribución de latencias."""
        # Recopilar datos de latencia de todos los modelos
        latency_data = {}
        for model_name, metrics in self.comprehensive_metrics.items():
            raw_latencies = []
            for config_results in metrics.raw_data.get('latency_results', {}).values():
                if hasattr(config_results, 'raw_latencies'):
                    raw_latencies.extend(config_results.raw_latencies)

            if raw_latencies:
                latency_data[model_name] = raw_latencies

        if not latency_data:
            return

        fig, ax = plt.subplots(figsize=(12, 8))

        # Box plot
        models = list(latency_data.keys())
        data = [latency_data[model] for model in models]

        bp = ax.boxplot(data, labels=[m.upper() for m in models], patch_artist=True)

        # Colores
        colors = ['lightblue', 'lightgreen', 'orange', 'pink']
        for patch, color in zip(bp['boxes'], colors[:len(models)]):
            patch.set_facecolor(color)

        ax.set_ylabel('Latencia (s)', fontsize=12)
        ax.set_title('Distribución de Latencias por Modelo', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        latency_dist_file = os.path.join(self.config.output_dir, f'latency_distribution_{timestamp}.png')
        plt.savefig(latency_dist_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _create_rag_curve_plot(self, timestamp: str):
        """Crea gráfico de curva RAG por tamaño de contexto."""
        fig, ax = plt.subplots(figsize=(12, 8))

        for model_name, metrics in self.comprehensive_metrics.items():
            if metrics.rag_performance_curve:
                sizes = list(metrics.rag_performance_curve.keys())
                accuracies = list(metrics.rag_performance_curve.values())

                ax.plot(sizes, accuracies, 'o-', linewidth=2, label=model_name.upper(), markersize=6)

        ax.set_xlabel('Tamaño del Contexto (tokens)', fontsize=12)
        ax.set_ylabel('Precisión RAG', fontsize=12)
        ax.set_title('Capacidad de Recuperación RAG vs Tamaño del Contexto', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')

        plt.tight_layout()
        rag_curve_file = os.path.join(self.config.output_dir, f'rag_curve_{timestamp}.png')
        plt.savefig(rag_curve_file, dpi=300, bbox_inches='tight')
        plt.close()


# Importaciones tardías de módulos opcionales
def _import_optional_modules():
    """Importa módulos opcionales y actualiza flags de disponibilidad."""
    global BENCHMARK_AVAILABLE, ENERGY_TRACKER_AVAILABLE, LATENCY_TESTER_AVAILABLE, RAG_EVALUATOR_AVAILABLE

    try:
        from scripts.benchmark_vs_giants import BenchmarkRunner, BenchmarkConfig, PerformanceMetrics
        BENCHMARK_AVAILABLE = True
        logger.info("✅ BenchmarkRunner disponible")
    except ImportError:
        BENCHMARK_AVAILABLE = False
        logger.warning("⚠️ BenchmarkRunner no disponible")

    try:
        from ailoos.benchmarking.energy_tracker import EnergyTracker, EnergyTrackerConfig, EnergyMetrics
        ENERGY_TRACKER_AVAILABLE = True
        logger.info("✅ EnergyTracker disponible")
    except ImportError:
        ENERGY_TRACKER_AVAILABLE = False
        logger.warning("⚠️ EnergyTracker no disponible")

    try:
        from ailoos.benchmarking.latency_tester import LatencyTester, LatencyTestConfig, LatencyMetrics
        LATENCY_TESTER_AVAILABLE = True
        logger.info("✅ LatencyTester disponible")
    except ImportError:
        LATENCY_TESTER_AVAILABLE = False
        logger.warning("⚠️ LatencyTester no disponible")

    try:
        from ailoos.benchmarking.rag_needle_evaluator import RagNeedleEvaluator, RagNeedleConfig, RagNeedleResult
        RAG_EVALUATOR_AVAILABLE = True
        logger.info("✅ RagNeedleEvaluator disponible")
    except ImportError:
        RAG_EVALUATOR_AVAILABLE = False
        logger.warning("⚠️ RagNeedleEvaluator no disponible")

# Ejecutar importaciones tardías
_import_optional_modules()


def create_accuracy_comparison_framework(models: List[str] = None, output_dir: str = './accuracy_comparison_results') -> AccuracyComparisonFramework:
    """Crea un AccuracyComparisonFramework con configuración por defecto."""
    config = AccuracyComparisonConfig(
        models_to_compare=models or ['empoorio', 'gpt4', 'claude', 'gemini'],
        output_dir=output_dir
    )
    return AccuracyComparisonFramework(config)


def run_accuracy_comparison(models: List[str] = None, output_dir: str = './accuracy_comparison_results') -> Dict[str, ComprehensiveMetrics]:
    """
    Ejecuta comparación completa de precisión de manera conveniente.

    Args:
        models: Lista de modelos a comparar
        output_dir: Directorio de salida

    Returns:
        Dict con métricas comprehensivas por modelo
    """
    framework = create_accuracy_comparison_framework(models, output_dir)
    results = framework.run_comprehensive_comparison()
    framework.generate_comprehensive_report()
    return results


def main():
    """Función principal para CLI."""
    parser = argparse.ArgumentParser(description='Framework de Comparación de Precisión EmpoorioLM vs Gigantes')
    parser.add_argument('--models', nargs='+', help='Modelos a comparar')
    parser.add_argument('--output', type=str, default='./accuracy_comparison_results', help='Directorio de salida')
    parser.add_argument('--config', type=str, help='Archivo de configuración JSON')
    parser.add_argument('--no-stats', action='store_true', help='Deshabilitar análisis estadístico')
    parser.add_argument('--no-plots', action='store_true', help='Deshabilitar visualizaciones')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (menos muestras)')

    args = parser.parse_args()

    # Configuración por defecto
    config = AccuracyComparisonConfig()

    # Sobrescribir con argumentos
    if args.models:
        config.models_to_compare = args.models
    if args.output:
        config.output_dir = args.output
    if args.no_stats:
        config.enable_statistical_analysis = False
    if args.no_plots:
        config.enable_advanced_visualizations = False
    if args.quick:
        # Configuración rápida
        config.benchmark_config.num_samples = 10
        config.latency_config.num_requests = 5
        config.rag_config.num_tasks_per_size = 3

    # Cargar desde archivo si especificado
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

    # Ejecutar comparación
    print("🚀 Iniciando Framework de Comparación de Precisión...")
    framework = AccuracyComparisonFramework(config)
    results = framework.run_comprehensive_comparison()
    framework.generate_comprehensive_report()

    print("\n🎉 Comparación completada!")
    print(f"📁 Resultados guardados en: {config.output_dir}")

    # Mostrar resumen
    if results:
        print("\n📊 Resumen de resultados:")
        for model, metrics in results.items():
            print(f"🤖 {model.upper()}: Precisión {metrics.accuracy_overall:.3f}, "
                  f"Latencia {metrics.avg_latency:.3f}s, "
                  f"Energía {metrics.total_energy_joules:.1f}J, "
                  f"RAG {metrics.rag_accuracy:.3f}")

    # Mostrar titulares de mercado
    if framework.market_headlines:
        print("\n📰 Titulares de mercado:")
        for headline in framework.market_headlines[:3]:
            print(f"• {headline.headline}")


if __name__ == "__main__":
    main()