import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import statistics
from enum import Enum

class RegressionSeverity(Enum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

@dataclass
class RegressionAlert:
    metric: str
    current_value: float
    baseline_value: float
    delta: float
    delta_percentage: float
    severity: RegressionSeverity
    confidence: float
    timestamp: str
    details: Dict[str, Any]

@dataclass
class BaselineConfig:
    metric: str
    baseline_value: float
    threshold_percentage: float  # e.g., 5.0 for 5%
    direction: str  # "higher_better" or "lower_better"
    min_samples: int = 5
    stability_window: int = 3  # number of recent runs to consider for stability

@dataclass
class RegressionReport:
    alerts: List[RegressionAlert]
    summary: Dict[str, Any]
    timestamp: str

class RegressionDetector:
    """
    Detección automática de regresiones en rendimiento.
    Monitorea métricas contra baselines y genera alertas cuando se detectan regresiones.
    """

    def __init__(self, results_dir: str = "benchmark_results",
                 baselines_file: str = "regression_baselines.json",
                 log_level: str = "INFO"):
        self.results_dir = Path(results_dir)
        self.baselines_file = self.results_dir / baselines_file
        self.logger = self._setup_logger(log_level)
        self.baselines = self._load_baselines()

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        file_handler = logging.FileHandler(self.results_dir / "regression_detector.log")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _load_baselines(self) -> Dict[str, BaselineConfig]:
        """Carga las configuraciones de baseline desde archivo."""
        if not self.baselines_file.exists():
            self.logger.info("No baselines file found, starting with empty baselines")
            return {}

        try:
            with open(self.baselines_file, 'r') as f:
                data = json.load(f)

            baselines = {}
            for metric, config_data in data.items():
                baselines[metric] = BaselineConfig(**config_data)

            self.logger.info(f"Loaded {len(baselines)} baseline configurations")
            return baselines
        except Exception as e:
            self.logger.error(f"Failed to load baselines: {e}")
            return {}

    def _save_baselines(self):
        """Guarda las configuraciones de baseline."""
        try:
            data = {metric: config.__dict__ for metric, config in self.baselines.items()}
            with open(self.baselines_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info("Baselines saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save baselines: {e}")

    def set_baseline(self, metric: str, baseline_value: float,
                    threshold_percentage: float = 5.0,
                    direction: str = "higher_better"):
        """
        Establece o actualiza una baseline para una métrica.
        """
        config = BaselineConfig(
            metric=metric,
            baseline_value=baseline_value,
            threshold_percentage=threshold_percentage,
            direction=direction
        )

        self.baselines[metric] = config
        self._save_baselines()
        self.logger.info(f"Set baseline for {metric}: {baseline_value} (±{threshold_percentage}%)")

    def update_baseline_from_results(self, results_file: Optional[str] = None):
        """
        Actualiza baselines usando los resultados más recientes.
        """
        if results_file:
            results_path = Path(results_file)
        else:
            # Find the most recent results file
            result_files = list(self.results_dir.glob("benchmark_results_*.json"))
            if not result_files:
                self.logger.warning("No benchmark results found for baseline update")
                return
            results_path = max(result_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(results_path, 'r') as f:
                data = json.load(f)

            results = data.get("results", [])

            # Group by metric
            metric_scores = {}
            for result in results:
                metric = result["metric"]
                score = result["score"]
                if metric not in metric_scores:
                    metric_scores[metric] = []
                metric_scores[metric].append(score)

            # Update baselines with averages
            for metric, scores in metric_scores.items():
                if len(scores) >= 3:  # Require minimum samples
                    avg_score = statistics.mean(scores)
                    std_dev = statistics.stdev(scores) if len(scores) > 1 else 0

                    # Set threshold based on standard deviation (2-sigma rule)
                    threshold = max(1.0, (std_dev / avg_score) * 100 * 2) if avg_score != 0 else 5.0

                    # Determine direction (simplified - could be configurable)
                    direction = "higher_better" if metric not in ["perplexity", "loss", "latency"] else "lower_better"

                    self.set_baseline(metric, avg_score, threshold, direction)

            self.logger.info(f"Updated baselines from {results_path}")
        except Exception as e:
            self.logger.error(f"Failed to update baselines from results: {e}")

    def detect_regressions(self, current_results: List[Dict]) -> RegressionReport:
        """
        Detecta regresiones comparando resultados actuales con baselines.
        """
        alerts = []
        timestamp = datetime.now().isoformat()

        # Group current results by metric
        current_metrics = {}
        for result in current_results:
            metric = result["metric"]
            score = result["score"]
            if metric not in current_metrics:
                current_metrics[metric] = []
            current_metrics[metric].append(score)

        # Check each metric against its baseline
        for metric, scores in current_metrics.items():
            if metric not in self.baselines:
                self.logger.warning(f"No baseline found for metric {metric}, skipping regression check")
                continue

            baseline_config = self.baselines[metric]
            current_avg = statistics.mean(scores)

            # Check for regression
            alert = self._check_metric_regression(
                metric, current_avg, baseline_config, len(scores)
            )

            if alert:
                alerts.append(alert)

        # Generate summary
        summary = self._generate_regression_summary(alerts, current_metrics)

        report = RegressionReport(
            alerts=alerts,
            summary=summary,
            timestamp=timestamp
        )

        self._save_regression_report(report)
        return report

    def _check_metric_regression(self, metric: str, current_value: float,
                               baseline_config: BaselineConfig, num_samples: int) -> Optional[RegressionAlert]:
        """Verifica si hay regresión en una métrica específica."""
        baseline_value = baseline_config.baseline_value
        threshold_percentage = baseline_config.threshold_percentage
        direction = baseline_config.direction

        # Calculate delta
        delta = current_value - baseline_value
        delta_percentage = (abs(delta) / baseline_value) * 100 if baseline_value != 0 else 0

        # Check if regression threshold is exceeded
        is_regression = False
        if direction == "higher_better":
            is_regression = delta < -threshold_percentage
        else:  # lower_better
            is_regression = delta > threshold_percentage

        if not is_regression:
            return None

        # Determine severity
        severity = self._calculate_severity(delta_percentage, threshold_percentage)

        # Calculate confidence (simplified)
        confidence = min(1.0, num_samples / baseline_config.min_samples)

        alert = RegressionAlert(
            metric=metric,
            current_value=current_value,
            baseline_value=baseline_value,
            delta=delta,
            delta_percentage=delta_percentage,
            severity=severity,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            details={
                "direction": direction,
                "threshold_percentage": threshold_percentage,
                "num_samples": num_samples,
                "baseline_config": baseline_config.__dict__
            }
        )

        self.logger.warning(f"Regression detected for {metric}: {delta_percentage:.2f}% "
                          f"({severity.value}) - Current: {current_value:.4f}, "
                          f"Baseline: {baseline_value:.4f}")

        return alert

    def _calculate_severity(self, delta_percentage: float, threshold_percentage: float) -> RegressionSeverity:
        """Calcula la severidad de la regresión."""
        ratio = delta_percentage / threshold_percentage

        if ratio < 1.5:
            return RegressionSeverity.MINOR
        elif ratio < 3.0:
            return RegressionSeverity.MODERATE
        elif ratio < 5.0:
            return RegressionSeverity.SEVERE
        else:
            return RegressionSeverity.CRITICAL

    def _generate_regression_summary(self, alerts: List[RegressionAlert],
                                   current_metrics: Dict[str, List[float]]) -> Dict[str, Any]:
        """Genera un resumen del reporte de regresiones."""
        severity_counts = {
            severity.value: 0 for severity in RegressionSeverity
        }

        for alert in alerts:
            severity_counts[alert.severity.value] += 1

        total_metrics = len(current_metrics)
        regressed_metrics = len(set(alert.metric for alert in alerts))

        return {
            "total_alerts": len(alerts),
            "severity_breakdown": severity_counts,
            "total_metrics_checked": total_metrics,
            "regressed_metrics": regressed_metrics,
            "regression_rate": regressed_metrics / total_metrics if total_metrics > 0 else 0,
            "most_severe": max([alert.severity for alert in alerts], key=lambda s: list(RegressionSeverity).index(s)).value if alerts else "none"
        }

    def _save_regression_report(self, report: RegressionReport):
        """Guarda el reporte de regresiones."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"regression_report_{timestamp}.json"
        filepath = self.results_dir / filename

        report_dict = {
            "alerts": [alert.__dict__ for alert in report.alerts],
            "summary": report.summary,
            "timestamp": report.timestamp
        }

        with open(filepath, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        self.logger.info(f"Regression report saved to {filepath}")

    def get_baseline_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual de las baselines."""
        return {
            "total_baselines": len(self.baselines),
            "baselines": {metric: config.__dict__ for metric, config in self.baselines.items()},
            "last_updated": datetime.now().isoformat()
        }

    def clear_baseline(self, metric: str):
        """Elimina una baseline específica."""
        if metric in self.baselines:
            del self.baselines[metric]
            self._save_baselines()
            self.logger.info(f"Cleared baseline for {metric}")
        else:
            self.logger.warning(f"Baseline for {metric} not found")

    def should_block_deployment(self, report: RegressionReport,
                              max_critical: int = 0, max_severe: int = 1) -> bool:
        """
        Determina si se debe bloquear un deployment basado en regresiones detectadas.
        """
        critical_count = sum(1 for alert in report.alerts if alert.severity == RegressionSeverity.CRITICAL)
        severe_count = sum(1 for alert in report.alerts if alert.severity == RegressionSeverity.SEVERE)

        should_block = critical_count > max_critical or severe_count > max_severe

        if should_block:
            self.logger.warning(f"Deployment blocked due to regressions: "
                              f"{critical_count} critical, {severe_count} severe")

        return should_block