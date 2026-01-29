import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import statistics

# Optional plotting dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

@dataclass
class ReportConfig:
    title: str = "Benchmark Report"
    include_plots: bool = True
    include_tables: bool = True
    include_summary: bool = True
    output_formats: List[str] = None  # ["html", "json", "markdown"]

    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ["html", "json"]

@dataclass
class BenchmarkReport:
    title: str
    summary: Dict[str, Any]
    results: List[Dict]
    timestamp: str
    comparisons: Optional[List[Dict]] = None
    performance_data: Optional[Dict] = None
    regressions: Optional[List[Dict]] = None

class BenchmarkReporter:
    """
    Generación automática de reportes de comparación de benchmarks.
    Crea reportes en múltiples formatos con visualizaciones y análisis.
    """

    def __init__(self, results_dir: str = "benchmark_results",
                 reports_dir: str = "reports",
                 log_level: str = "INFO"):
        self.results_dir = Path(results_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        file_handler = logging.FileHandler(self.results_dir / "benchmark_reporter.log")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def generate_report(self, config: ReportConfig,
                       results: List[Dict],
                       comparisons: Optional[List[Dict]] = None,
                       performance_data: Optional[Dict] = None,
                       regressions: Optional[List[Dict]] = None) -> Dict[str, str]:
        """
        Genera reportes en los formatos especificados.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = BenchmarkReport(
            title=config.title,
            summary=self._generate_summary(results, comparisons, regressions),
            results=results,
            comparisons=comparisons,
            performance_data=performance_data,
            regressions=regressions,
            timestamp=timestamp
        )

        generated_files = {}

        for format_type in config.output_formats:
            try:
                if format_type == "html":
                    filepath = self._generate_html_report(report, config)
                elif format_type == "json":
                    filepath = self._generate_json_report(report)
                elif format_type == "markdown":
                    filepath = self._generate_markdown_report(report)
                else:
                    self.logger.warning(f"Unsupported format: {format_type}")
                    continue

                generated_files[format_type] = str(filepath)
                self.logger.info(f"Generated {format_type} report: {filepath}")
            except Exception as e:
                self.logger.error(f"Failed to generate {format_type} report: {e}")

        return generated_files

    def _generate_summary(self, results: List[Dict],
                         comparisons: Optional[List[Dict]] = None,
                         regressions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Genera un resumen estadístico del reporte."""
        summary = {
            "total_results": len(results),
            "metrics_count": len(set(r["metric"] for r in results)),
            "datasets_count": len(set(r["dataset"] for r in results if "dataset" in r)),
            "timestamp": datetime.now().isoformat()
        }

        # Metric statistics
        metric_stats = {}
        for result in results:
            metric = result["metric"]
            score = result["score"]
            if metric not in metric_stats:
                metric_stats[metric] = []
            metric_stats[metric].append(score)

        summary["metric_statistics"] = {}
        for metric, scores in metric_stats.items():
            summary["metric_statistics"][metric] = {
                "count": len(scores),
                "mean": statistics.mean(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0,
                "min": min(scores),
                "max": max(scores)
            }

        # Comparison summary
        if comparisons:
            summary["comparison_summary"] = {
                "total_comparisons": len(comparisons),
                "improvements": sum(1 for c in comparisons if c.get("significance") == "improvement"),
                "regressions": sum(1 for c in comparisons if c.get("significance") == "regression"),
                "neutrals": sum(1 for c in comparisons if c.get("significance") == "neutral")
            }

        # Regression summary
        if regressions:
            severity_counts = {}
            for reg in regressions:
                severity = reg.get("severity", "unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            summary["regression_summary"] = {
                "total_regressions": len(regressions),
                "severity_breakdown": severity_counts
            }

        return summary

    def _generate_html_report(self, report: BenchmarkReport, config: ReportConfig) -> Path:
        """Genera un reporte HTML con visualizaciones."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{timestamp}.html"
        filepath = self.reports_dir / filename

        html_content = self._build_html_content(report, config)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath

    def _build_html_content(self, report: BenchmarkReport, config: ReportConfig) -> str:
        """Construye el contenido HTML del reporte."""
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report.title}</h1>
            <p class="timestamp">Generado: {report.timestamp}</p>
        </header>

        <section id="summary">
            <h2>Resumen Ejecutivo</h2>
            {self._build_summary_html(report.summary)}
        </section>

        <section id="results">
            <h2>Resultados de Benchmarks</h2>
            {self._build_results_html(report.results)}
        </section>
"""

        if report.comparisons:
            html += f"""
        <section id="comparisons">
            <h2>Comparaciones de Versiones</h2>
            {self._build_comparisons_html(report.comparisons)}
        </section>
"""

        if report.regressions:
            html += f"""
        <section id="regressions">
            <h2>Regresiones Detectadas</h2>
            {self._build_regressions_html(report.regressions)}
        </section>
"""

        if config.include_plots and (PLOTTING_AVAILABLE or PLOTLY_AVAILABLE):
            html += f"""
        <section id="plots">
            <h2>Visualizaciones</h2>
            {self._build_plots_html(report)}
        </section>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    def _get_css_styles(self) -> str:
        """Retorna los estilos CSS para el reporte."""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #007acc;
            padding-bottom: 20px;
        }
        h1 {
            color: #007acc;
            margin-bottom: 10px;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
        }
        section {
            margin-bottom: 40px;
        }
        h2 {
            color: #007acc;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .metric-card {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .improvement {
            color: #28a745;
            font-weight: bold;
        }
        .regression {
            color: #dc3545;
            font-weight: bold;
        }
        .neutral {
            color: #6c757d;
        }
        .severity-critical {
            background-color: #f8d7da;
            color: #721c24;
        }
        .severity-severe {
            background-color: #fff3cd;
            color: #856404;
        }
        .plot-container {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: #f8f9fa;
        }
        """

    def _build_summary_html(self, summary: Dict[str, Any]) -> str:
        """Construye la sección de resumen en HTML."""
        html = f"""
        <div class="metric-card">
            <h3>Estadísticas Generales</h3>
            <p><strong>Total de Resultados:</strong> {summary['total_results']}</p>
            <p><strong>Métricas Evaluadas:</strong> {summary['metrics_count']}</p>
            <p><strong>Datasets Usados:</strong> {summary.get('datasets_count', 'N/A')}</p>
        </div>
"""

        if "comparison_summary" in summary:
            comp = summary["comparison_summary"]
            html += f"""
        <div class="metric-card">
            <h3>Resumen de Comparaciones</h3>
            <p><strong>Mejoras:</strong> <span class="improvement">{comp['improvements']}</span></p>
            <p><strong>Regresiones:</strong> <span class="regression">{comp['regressions']}</span></p>
            <p><strong>Neutral:</strong> <span class="neutral">{comp['neutrals']}</span></p>
        </div>
"""

        if "regression_summary" in summary:
            reg = summary["regression_summary"]
            html += f"""
        <div class="metric-card">
            <h3>Regresiones Detectadas</h3>
            <p><strong>Total:</strong> {reg['total_regressions']}</p>
        </div>
"""

        return html

    def _build_results_html(self, results: List[Dict]) -> str:
        """Construye la tabla de resultados."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Dataset</th>
                    <th>Métrica</th>
                    <th>Valor</th>
                    <th>Tiempo de Ejecución (s)</th>
                </tr>
            </thead>
            <tbody>
"""

        for result in results:
            html += f"""
                <tr>
                    <td>{result.get('dataset', 'N/A')}</td>
                    <td>{result['metric']}</td>
                    <td>{result['score']:.4f}</td>
                    <td>{result.get('execution_time', 'N/A')}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""

        return html

    def _build_comparisons_html(self, comparisons: List[Dict]) -> str:
        """Construye la tabla de comparaciones."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Métrica</th>
                    <th>Versión A</th>
                    <th>Versión B</th>
                    <th>Delta</th>
                    <th>Delta %</th>
                    <th>Significado</th>
                </tr>
            </thead>
            <tbody>
"""

        for comp in comparisons:
            significance_class = comp.get('significance', 'neutral')
            html += f"""
                <tr>
                    <td>{comp['metric']}</td>
                    <td>{comp['score_a']:.4f}</td>
                    <td>{comp['score_b']:.4f}</td>
                    <td>{comp['delta']:.4f}</td>
                    <td>{comp['delta_percentage']:.2f}%</td>
                    <td class="{significance_class}">{comp['significance']}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""

        return html

    def _build_regressions_html(self, regressions: List[Dict]) -> str:
        """Construye la tabla de regresiones."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Métrica</th>
                    <th>Valor Actual</th>
                    <th>Baseline</th>
                    <th>Delta %</th>
                    <th>Severidad</th>
                </tr>
            </thead>
            <tbody>
"""

        for reg in regressions:
            severity_class = f"severity-{reg.get('severity', 'unknown')}"
            html += f"""
                <tr class="{severity_class}">
                    <td>{reg['metric']}</td>
                    <td>{reg['current_value']:.4f}</td>
                    <td>{reg['baseline_value']:.4f}</td>
                    <td>{reg['delta_percentage']:.2f}%</td>
                    <td>{reg.get('severity', 'unknown')}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""

        return html

    def _build_plots_html(self, report: BenchmarkReport) -> str:
        """Construye la sección de visualizaciones."""
        html = ""

        # Simple bar chart for metrics
        if PLOTLY_AVAILABLE and report.results:
            try:
                fig = self._create_metrics_plot(report.results)
                plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                html += f"""
        <div class="plot-container">
            <h3>Comparación de Métricas</h3>
            {plot_html}
        </div>
"""
            except Exception as e:
                self.logger.warning(f"Failed to create metrics plot: {e}")

        return html

    def _create_metrics_plot(self, results: List[Dict]):
        """Crea un gráfico de barras para las métricas."""
        import plotly.express as px
        import pandas as pd

        df = pd.DataFrame(results)
        fig = px.bar(df, x='metric', y='score', color='dataset',
                    title='Resultados por Métrica y Dataset')
        return fig

    def _generate_json_report(self, report: BenchmarkReport) -> Path:
        """Genera un reporte JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{timestamp}.json"
        filepath = self.reports_dir / filename

        report_dict = {
            "title": report.title,
            "summary": report.summary,
            "results": report.results,
            "comparisons": report.comparisons,
            "performance_data": report.performance_data,
            "regressions": report.regressions,
            "timestamp": report.timestamp
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        return filepath

    def _generate_markdown_report(self, report: BenchmarkReport) -> Path:
        """Genera un reporte en formato Markdown."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_report_{timestamp}.md"
        filepath = self.reports_dir / filename

        md_content = self._build_markdown_content(report)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        return filepath

    def _build_markdown_content(self, report: BenchmarkReport) -> str:
        """Construye el contenido Markdown del reporte."""
        md = f"""# {report.title}

**Generado:** {report.timestamp}

## Resumen Ejecutivo

- **Total de Resultados:** {report.summary['total_results']}
- **Métricas Evaluadas:** {report.summary['metrics_count']}
- **Datasets Usados:** {report.summary.get('datasets_count', 'N/A')}

"""

        if "comparison_summary" in report.summary:
            comp = report.summary["comparison_summary"]
            md += f"""
## Resumen de Comparaciones

- **Mejoras:** {comp['improvements']}
- **Regresiones:** {comp['regressions']}
- **Neutral:** {comp['neutrals']}

"""

        if "regression_summary" in report.summary:
            reg = report.summary["regression_summary"]
            md += f"""
## Regresiones Detectadas

- **Total:** {reg['total_regressions']}

"""

        # Add results table
        if report.results:
            md += """
## Resultados de Benchmarks

| Dataset | Métrica | Valor | Tiempo de Ejecución (s) |
|---------|---------|-------|-------------------------|
"""
            for result in report.results:
                md += f"| {result.get('dataset', 'N/A')} | {result['metric']} | {result['score']:.4f} | {result.get('execution_time', 'N/A')} |\n"

        return md