import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import statistics
from datetime import datetime

@dataclass
class VersionComparison:
    version_a: str
    version_b: str
    metric: str
    score_a: float
    score_b: float
    delta: float
    delta_percentage: float
    significance: str  # "improvement", "regression", "neutral"
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class ComparisonReport:
    comparisons: List[VersionComparison]
    summary: Dict[str, Any]
    timestamp: str

class VersionComparator:
    """
    Comparación automática entre versiones del modelo basada en resultados de benchmarks.
    Proporciona análisis estadístico de mejoras y regresiones.
    """

    def __init__(self, results_dir: str = "benchmark_results", log_level: str = "INFO"):
        self.results_dir = Path(results_dir)
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        file_handler = logging.FileHandler(self.results_dir / "version_comparator.log")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def compare_versions(self, version_a: str, version_b: str,
                        metrics: Optional[List[str]] = None) -> ComparisonReport:
        """
        Compara dos versiones del modelo usando sus resultados de benchmark.
        """
        self.logger.info(f"Comparing versions: {version_a} vs {version_b}")

        # Load results for both versions
        results_a = self._load_version_results(version_a)
        results_b = self._load_version_results(version_b)

        if not results_a or not results_b:
            self.logger.error(f"Missing results for versions {version_a} or {version_b}")
            return ComparisonReport([], {}, datetime.now().isoformat())

        # Filter metrics if specified
        if metrics:
            results_a = [r for r in results_a if r["metric"] in metrics]
            results_b = [r for r in results_b if r["metric"] in metrics]

        # Group results by metric
        metrics_a = self._group_by_metric(results_a)
        metrics_b = self._group_by_metric(results_b)

        # Perform comparisons
        comparisons = []
        for metric in set(metrics_a.keys()) | set(metrics_b.keys()):
            if metric in metrics_a and metric in metrics_b:
                comparison = self._compare_metric(metric, metrics_a[metric], metrics_b[metric],
                                                version_a, version_b)
                comparisons.append(comparison)

        # Generate summary
        summary = self._generate_summary(comparisons, version_a, version_b)

        report = ComparisonReport(
            comparisons=comparisons,
            summary=summary,
            timestamp=datetime.now().isoformat()
        )

        self._save_comparison_report(report)
        return report

    def _load_version_results(self, version: str) -> List[Dict]:
        """Carga resultados de benchmark para una versión específica."""
        version_files = list(self.results_dir.glob(f"*_{version}_*.json"))
        if not version_files:
            # Try to find files containing the version string
            version_files = [f for f in self.results_dir.glob("*.json") if version in f.name]

        if not version_files:
            self.logger.warning(f"No result files found for version {version}")
            return []

        # Load the most recent file
        latest_file = max(version_files, key=lambda f: f.stat().st_mtime)
        self.logger.info(f"Loading results from {latest_file}")

        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                return data.get("results", [])
        except Exception as e:
            self.logger.error(f"Failed to load results from {latest_file}: {e}")
            return []

    def _group_by_metric(self, results: List[Dict]) -> Dict[str, List[float]]:
        """Agrupa resultados por métrica."""
        grouped = {}
        for result in results:
            metric = result["metric"]
            score = result["score"]
            if metric not in grouped:
                grouped[metric] = []
            grouped[metric].append(score)
        return grouped

    def _compare_metric(self, metric: str, scores_a: List[float], scores_b: List[float],
                       version_a: str, version_b: str) -> VersionComparison:
        """Compara scores de una métrica entre dos versiones."""
        # Calculate averages
        avg_a = statistics.mean(scores_a)
        avg_b = statistics.mean(scores_b)

        delta = avg_b - avg_a
        delta_percentage = (delta / avg_a) * 100 if avg_a != 0 else 0

        # Determine significance
        significance = self._determine_significance(delta, metric)

        # Calculate confidence (simplified - in practice, use statistical tests)
        confidence = self._calculate_confidence(scores_a, scores_b)

        return VersionComparison(
            version_a=version_a,
            version_b=version_b,
            metric=metric,
            score_a=avg_a,
            score_b=avg_b,
            delta=delta,
            delta_percentage=delta_percentage,
            significance=significance,
            confidence=confidence,
            metadata={
                "samples_a": len(scores_a),
                "samples_b": len(scores_b),
                "std_a": statistics.stdev(scores_a) if len(scores_a) > 1 else 0,
                "std_b": statistics.stdev(scores_b) if len(scores_b) > 1 else 0
            }
        )

    def _determine_significance(self, delta: float, metric: str) -> str:
        """Determina si el cambio es una mejora, regresión o neutral."""
        # Define thresholds based on metric type
        # For most metrics, positive delta is improvement
        # For perplexity, negative delta is improvement
        if metric.lower() in ["perplexity", "loss"]:
            if delta < -0.01:  # Significant improvement
                return "improvement"
            elif delta > 0.01:  # Significant regression
                return "regression"
            else:
                return "neutral"
        else:
            if delta > 0.01:  # Significant improvement
                return "improvement"
            elif delta < -0.01:  # Significant regression
                return "regression"
            else:
                return "neutral"

    def _calculate_confidence(self, scores_a: List[float], scores_b: List[float]) -> float:
        """Calcula confianza en la comparación (simplified)."""
        # Simplified confidence calculation
        # In practice, use t-test or other statistical methods
        try:
            std_a = statistics.stdev(scores_a)
            std_b = statistics.stdev(scores_b)
            n_a = len(scores_a)
            n_b = len(scores_b)

            # Pooled standard error
            se = ((std_a**2 / n_a) + (std_b**2 / n_b)) ** 0.5

            if se == 0:
                return 1.0

            # Z-score approximation
            z = abs(statistics.mean(scores_a) - statistics.mean(scores_b)) / se

            # Convert to confidence (simplified)
            confidence = min(1.0, z / 3.0)  # Rough approximation
            return confidence
        except:
            return 0.5

    def _generate_summary(self, comparisons: List[VersionComparison],
                         version_a: str, version_b: str) -> Dict[str, Any]:
        """Genera un resumen de la comparación."""
        improvements = sum(1 for c in comparisons if c.significance == "improvement")
        regressions = sum(1 for c in comparisons if c.significance == "regression")
        neutrals = sum(1 for c in comparisons if c.significance == "neutral")

        avg_confidence = statistics.mean([c.confidence for c in comparisons]) if comparisons else 0

        return {
            "total_metrics": len(comparisons),
            "improvements": improvements,
            "regressions": regressions,
            "neutrals": neutrals,
            "average_confidence": avg_confidence,
            "version_a": version_a,
            "version_b": version_b,
            "overall_assessment": "improvement" if improvements > regressions else
                                "regression" if regressions > improvements else "neutral"
        }

    def _save_comparison_report(self, report: ComparisonReport):
        """Guarda el reporte de comparación."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"version_comparison_{report.summary['version_a']}_vs_{report.summary['version_b']}_{timestamp}.json"
        filepath = self.results_dir / filename

        report_dict = {
            "comparisons": [c.__dict__ for c in report.comparisons],
            "summary": report.summary,
            "timestamp": report.timestamp
        }

        with open(filepath, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        self.logger.info(f"Comparison report saved to {filepath}")