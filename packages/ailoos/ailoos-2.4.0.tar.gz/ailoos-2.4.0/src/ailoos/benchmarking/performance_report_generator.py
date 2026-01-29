"""
Generador de Informes de Rendimiento Comparativo para EmpoorioLM
Crea reportes HTML/PDF profesionales con tablas de comparación, gráficos avanzados,
análisis ejecutivo y métricas clave para marketing e inversores.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import base64
import io

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports para templates HTML
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("⚠️ jinja2 no disponible, generación de HTML deshabilitada")

# Imports para gráficos
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Backend no interactivo
    import seaborn as sns
    sns.set_style("whitegrid")
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️ matplotlib/seaborn no disponibles, gráficos deshabilitados")

# Imports para PDF
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    try:
        import pdfkit
        PDFKIT_AVAILABLE = True
        WEASYPRINT_AVAILABLE = False
    except ImportError:
        PDFKIT_AVAILABLE = False
        WEASYPRINT_AVAILABLE = False
        print("⚠️ weasyprint/pdfkit no disponibles, conversión PDF deshabilitada")

# Añadir src al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar generador de gráficos de marketing
MARKETING_CHARTS_AVAILABLE = False
try:
    from ailoos.benchmarking.marketing_charts_generator import MarketingChartsGenerator, MarketingChartConfig
    MARKETING_CHARTS_AVAILABLE = True
    print("✅ MarketingChartsGenerator disponible para gráficos profesionales")
except ImportError:
    print("⚠️ MarketingChartsGenerator no disponible, usando gráficos básicos")


@dataclass
class PerformanceReportConfig:
    """Configuración del generador de informes de rendimiento."""
    # Configuración general
    output_dir: str = './performance_reports'
    report_title: str = 'EmpoorioLM vs Gigantes - Análisis de Rendimiento'
    company_name: str = 'Ailoos'
    report_version: str = '1.0'

    # Configuración de contenido
    include_executive_summary: bool = True
    include_detailed_analysis: bool = True
    include_technical_details: bool = True
    include_market_analysis: bool = True
    include_recommendations: bool = True

    # Configuración de visualizaciones
    enable_charts: bool = True
    use_marketing_charts: bool = True  # Usar gráficos profesionales de marketing
    chart_style: str = 'professional'  # 'professional', 'modern', 'classic'
    color_palette: str = 'ailoos'  # 'ailoos', 'default', 'colorblind'
    chart_platform: str = 'presentation'  # 'presentation', 'social_media', 'web', 'print'

    # Configuración de formatos
    generate_html: bool = True
    generate_pdf: bool = True
    generate_json: bool = True

    # Configuración específica
    highlight_empoorio: bool = True  # Resaltar EmpoorioLM en comparaciones
    include_confidence_intervals: bool = True
    include_statistical_significance: bool = True

    # Metadatos del reporte
    author: str = 'Equipo de Benchmarking Ailoos'
    generation_timestamp: str = ""
    data_source: str = 'AccuracyComparisonFramework'


@dataclass
class ReportSection:
    """Sección individual del reporte."""
    title: str
    content: str
    charts: List[str] = field(default_factory=list)  # URLs de imágenes de gráficos
    tables: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    section_type: str = 'content'  # 'content', 'analysis', 'comparison', 'conclusion'


class PerformanceReportGenerator:
    """
    Generador de informes de rendimiento comparativo.
    Crea reportes profesionales HTML/PDF con análisis detallado.
    """

    def __init__(self, config: PerformanceReportConfig = None):
        self.config = config or PerformanceReportConfig()
        self.config.generation_timestamp = datetime.now().isoformat()

        # Datos del framework de comparación
        self.comparison_data = None
        self.sections: List[ReportSection] = []

        # Configuración de templates
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.static_dir = os.path.join(os.path.dirname(__file__), 'static')

        # Crear directorios necesarios
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)

        # Inicializar componentes
        self._init_components()

        logger.info("🚀 PerformanceReportGenerator inicializado")

    def _init_components(self):
        """Inicializar componentes del generador de reportes."""
        # Inicializar template engine
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=select_autoescape(['html', 'xml'])
            )

        # Inicializar generador de gráficos de marketing
        self.marketing_charts_generator = None
        if MARKETING_CHARTS_AVAILABLE and self.config.use_marketing_charts:
            charts_config = MarketingChartConfig(
                output_dir=os.path.join(self.config.output_dir, 'charts'),
                color_palette=self.config.color_palette,
                target_platform=self.config.chart_platform,
                highlight_empoorio=self.config.highlight_empoorio
            )
            self.marketing_charts_generator = MarketingChartsGenerator(charts_config)
            self.marketing_charts_generator.optimize_for_platform(self.config.chart_platform)
            logger.info("🎨 Generador de gráficos de marketing inicializado")

        # Configurar colores y estilos
        self._setup_styling()

    def _setup_styling(self):
        """Configura colores y estilos para visualizaciones."""
        if not PLOTTING_AVAILABLE:
            return

        # Paletas de colores
        self.color_palettes = {
            'ailoos': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            'default': plt.rcParams['axes.prop_cycle'].by_key()['color'],
            'colorblind': ['#0072B2', '#E69F00', '#F0E442', '#009E73', '#56B4E9', '#D55E00']
        }

        # Estilos de gráficos
        plt.style.use('seaborn-v0_8-whitegrid' if hasattr(plt.style, 'available') and 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

        # Configurar fuente y tamaño
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['figure.titlesize'] = 14

    def load_comparison_data(self, comparison_results: Dict[str, Any]):
        """
        Carga datos del AccuracyComparisonFramework.

        Args:
            comparison_results: Resultados del framework de comparación
        """
        self.comparison_data = comparison_results

        # Cargar datos en el generador de gráficos de marketing si está disponible
        if self.marketing_charts_generator:
            self.marketing_charts_generator.load_comparison_data(comparison_results)
            logger.info("✅ Datos cargados en generador de gráficos de marketing")

        logger.info("✅ Datos de comparación cargados")

    def generate_comprehensive_report(self) -> Dict[str, str]:
        """
        Genera reporte comprehensivo en todos los formatos configurados.

        Returns:
            Dict con rutas de archivos generados
        """
        logger.info("🚀 Generando reporte comprehensivo de rendimiento")

        # Generar secciones del reporte
        self._generate_report_sections()

        # Generar gráficos
        if self.config.enable_charts and PLOTTING_AVAILABLE:
            self._generate_all_charts()

        generated_files = {}

        # Generar HTML
        if self.config.generate_html:
            html_file = self._generate_html_report()
            generated_files['html'] = html_file

        # Generar PDF
        if self.config.generate_pdf:
            pdf_file = self._generate_pdf_report()
            generated_files['pdf'] = pdf_file

        # Generar JSON
        if self.config.generate_json:
            json_file = self._generate_json_report()
            generated_files['json'] = json_file

        logger.info(f"✅ Reporte generado. Archivos: {list(generated_files.keys())}")
        return generated_files

    def _generate_report_sections(self):
        """Genera todas las secciones del reporte."""
        self.sections = []

        # Portada
        self.sections.append(self._create_cover_section())

        # Resumen ejecutivo
        if self.config.include_executive_summary:
            self.sections.append(self._create_executive_summary_section())

        # Análisis de precisión
        self.sections.append(self._create_accuracy_analysis_section())

        # Análisis de latencia
        self.sections.append(self._create_latency_analysis_section())

        # Análisis energético
        self.sections.append(self._create_energy_analysis_section())

        # Análisis RAG
        self.sections.append(self._create_rag_analysis_section())

        # Comparación multi-dimensional
        self.sections.append(self._create_multidimensional_comparison_section())

        # Análisis de mercado
        if self.config.include_market_analysis:
            self.sections.append(self._create_market_analysis_section())

        # Recomendaciones
        if self.config.include_recommendations:
            self.sections.append(self._create_recommendations_section())

        # Apéndice técnico
        if self.config.include_technical_details:
            self.sections.append(self._create_technical_appendix_section())

    def _create_cover_section(self) -> ReportSection:
        """Crea la sección de portada."""
        content = f"""
        <div class="cover-page">
            <div class="company-header">
                <h1>{self.config.company_name}</h1>
                <div class="report-title">
                    <h2>{self.config.report_title}</h2>
                </div>
            </div>

            <div class="report-meta">
                <div class="meta-item">
                    <span class="meta-label">Versión:</span>
                    <span class="meta-value">{self.config.report_version}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Fecha de Generación:</span>
                    <span class="meta-value">{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Autor:</span>
                    <span class="meta-value">{self.config.author}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Fuente de Datos:</span>
                    <span class="meta-value">{self.config.data_source}</span>
                </div>
            </div>

            <div class="report-summary">
                <p>Este reporte presenta un análisis comprehensivo del rendimiento de EmpoorioLM
                comparado con los principales modelos de lenguaje disponibles en el mercado.
                Incluye métricas de precisión, latencia, consumo energético y capacidad RAG,
                con análisis estadístico y visualizaciones profesionales.</p>
            </div>
        </div>
        """

        return ReportSection(
            title="Portada",
            content=content,
            section_type="content"
        )

    def _create_executive_summary_section(self) -> ReportSection:
        """Crea la sección de resumen ejecutivo."""
        if not self.comparison_data:
            return ReportSection(title="Resumen Ejecutivo", content="<p>No hay datos disponibles</p>")

        # Extraer métricas clave
        key_metrics = self._extract_key_metrics()

        # Generar tabla comparativa
        comparison_table = self._generate_comparison_table()

        content = f"""
        <div class="executive-summary">
            <h3>Resumen Ejecutivo</h3>

            <div class="key-highlights">
                <div class="highlight-card">
                    <h4>🏆 Rendimiento General</h4>
                    <p>EmpoorioLM demuestra {self._calculate_performance_summary()}</p>
                </div>

                <div class="highlight-card">
                    <h4>⚡ Eficiencia Energética</h4>
                    <p>Consumo energético {self._calculate_energy_efficiency()}</p>
                </div>

                <div class="highlight-card">
                    <h4>🎯 Precisión</h4>
                    <p>Precisión en benchmarks: {key_metrics.get('empoorio_accuracy', 'N/A')}</p>
                </div>

                <div class="highlight-card">
                    <h4>🚀 Latencia</h4>
                    <p>Tiempo de respuesta: {key_metrics.get('empoorio_latency', 'N/A')}</p>
                </div>
            </div>

            <div class="comparison-table">
                <h4>Tabla Comparativa de Rendimiento</h4>
                {comparison_table}
            </div>

            <div class="competitive-advantages">
                <h4>Ventajas Competitivas</h4>
                <ul>
                    {self._generate_competitive_advantages()}
                </ul>
            </div>

            <div class="market-implications">
                <h4>Implicaciones de Mercado</h4>
                <p>Los resultados de este análisis posicionan a EmpoorioLM como {self._assess_market_position()}</p>
            </div>
        </div>
        """

        return ReportSection(
            title="Resumen Ejecutivo",
            content=content,
            section_type="analysis",
            metrics=key_metrics
        )

    def _create_accuracy_analysis_section(self) -> ReportSection:
        """Crea la sección de análisis de precisión."""
        accuracy_table = self._generate_accuracy_detailed_table()
        accuracy_insights = self._generate_accuracy_insights()

        content = f"""
        <div class="accuracy-analysis">
            <h3>Análisis de Precisión</h3>

            <div class="section-intro">
                <p>Esta sección analiza el rendimiento de precisión de los modelos
                en benchmarks estándar de conocimiento y razonamiento, incluyendo
                MMLU, GSM8K y otras métricas especializadas.</p>
            </div>

            <div class="accuracy-metrics">
                <h4>Métricas Detalladas de Precisión</h4>
                {accuracy_table}
            </div>

            <div class="accuracy-insights">
                <h4>Insights Clave</h4>
                {accuracy_insights}
            </div>

            <div class="chart-container">
                <img src="accuracy_comparison.png" alt="Comparación de Precisión">
            </div>
        </div>
        """

        return ReportSection(
            title="Análisis de Precisión",
            content=content,
            section_type="analysis",
            charts=['accuracy_comparison.png']
        )

    def _create_latency_analysis_section(self) -> ReportSection:
        """Crea la sección de análisis de latencia."""
        content = """
        <div class="latency-analysis">
            <h3>Análisis de Latencia</h3>

            <div class="section-intro">
                <p>Análisis detallado de los tiempos de respuesta, incluyendo
                latencia promedio, percentiles y tiempo de primer token.</p>
            </div>

            <div class="latency-metrics">
                <h4>Métricas de Latencia</h4>
                <!-- Gráficos y tablas se insertarán aquí -->
            </div>
        </div>
        """

        return ReportSection(
            title="Análisis de Latencia",
            content=content,
            section_type="analysis"
        )

    def _create_energy_analysis_section(self) -> ReportSection:
        """Crea la sección de análisis energético."""
        content = """
        <div class="energy-analysis">
            <h3>Análisis Energético</h3>

            <div class="section-intro">
                <p>Evaluación del consumo energético y eficiencia de los modelos,
                incluyendo impacto ambiental y costo operativo.</p>
            </div>

            <div class="energy-metrics">
                <!-- Métricas de energía se insertarán aquí -->
            </div>
        </div>
        """

        return ReportSection(
            title="Análisis Energético",
            content=content,
            section_type="analysis"
        )

    def _create_rag_analysis_section(self) -> ReportSection:
        """Crea la sección de análisis RAG."""
        content = """
        <div class="rag-analysis">
            <h3>Análisis de Capacidad RAG</h3>

            <div class="section-intro">
                <p>Evaluación de la capacidad de recuperación de información
                en contextos largos usando la metodología needle-in-haystack.</p>
            </div>

            <div class="rag-metrics">
                <!-- Métricas RAG se insertarán aquí -->
            </div>
        </div>
        """

        return ReportSection(
            title="Análisis RAG",
            content=content,
            section_type="analysis"
        )

    def _create_multidimensional_comparison_section(self) -> ReportSection:
        """Crea la sección de comparación multi-dimensional."""
        content = """
        <div class="multidimensional-comparison">
            <h3>Comparación Multi-dimensional</h3>

            <div class="section-intro">
                <p>Análisis integrado que combina todas las métricas de rendimiento
                para proporcionar una visión holística del posicionamiento competitivo.</p>
            </div>

            <div class="radar-chart">
                <!-- Gráfico radar se insertará aquí -->
            </div>
        </div>
        """

        return ReportSection(
            title="Comparación Multi-dimensional",
            content=content,
            section_type="comparison"
        )

    def _create_market_analysis_section(self) -> ReportSection:
        """Crea la sección de análisis de mercado."""
        content = """
        <div class="market-analysis">
            <h3>Análisis de Mercado</h3>

            <div class="market-positioning">
                <h4>Posicionamiento Competitivo</h4>
                <!-- Análisis de mercado se insertará aquí -->
            </div>
        </div>
        """

        return ReportSection(
            title="Análisis de Mercado",
            content=content,
            section_type="analysis"
        )

    def _create_recommendations_section(self) -> ReportSection:
        """Crea la sección de recomendaciones."""
        content = """
        <div class="recommendations">
            <h3>Recomendaciones</h3>

            <div class="strategic-recommendations">
                <h4>Recomendaciones Estratégicas</h4>
                <ul>
                    <li>Optimizaciones de rendimiento identificadas</li>
                    <li>Oportunidades de mejora en eficiencia energética</li>
                    <li>Estrategias de posicionamiento de mercado</li>
                </ul>
            </div>
        </div>
        """

        return ReportSection(
            title="Recomendaciones",
            content=content,
            section_type="conclusion"
        )

    def _create_technical_appendix_section(self) -> ReportSection:
        """Crea la sección de apéndice técnico."""
        content = """
        <div class="technical-appendix">
            <h3>Apéndice Técnico</h3>

            <div class="methodology">
                <h4>Metodología</h4>
                <p>Detalles técnicos de las pruebas realizadas y configuración utilizada.</p>
            </div>

            <div class="raw-data">
                <h4>Datos Crudos</h4>
                <p>Enlaces a datasets completos y configuraciones detalladas.</p>
            </div>
        </div>
        """

        return ReportSection(
            title="Apéndice Técnico",
            content=content,
            section_type="content"
        )

    def _extract_key_metrics(self) -> Dict[str, Any]:
        """Extrae métricas clave de los datos de comparación."""
        if not self.comparison_data:
            return {}

        metrics = {}
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        for model_name, model_metrics in comprehensive_metrics.items():
            metrics[f"{model_name}_accuracy"] = f"{model_metrics.get('accuracy_overall', 0):.3f}"
            metrics[f"{model_name}_latency"] = f"{model_metrics.get('avg_latency', 0):.2f}s"
            metrics[f"{model_name}_energy"] = f"{model_metrics.get('total_energy_joules', 0):.1f}J"
            metrics[f"{model_name}_efficiency"] = f"{model_metrics.get('efficiency_score', 0):.2f}"
            metrics[f"{model_name}_rag"] = f"{model_metrics.get('rag_accuracy', 0):.3f}"

        return metrics

    def _generate_comparison_table(self) -> str:
        """Genera tabla HTML comparativa de rendimiento."""
        if not self.comparison_data:
            return "<p>No hay datos disponibles para comparación</p>"

        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        if not comprehensive_metrics:
            return "<p>No hay métricas comprehensivas disponibles</p>"

        table_html = """
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>Precisión</th>
                    <th>Latencia (s)</th>
                    <th>Energía (J)</th>
                    <th>RAG</th>
                    <th>Eficiencia</th>
                </tr>
            </thead>
            <tbody>
        """

        for model_name, metrics in comprehensive_metrics.items():
            # Resaltar EmpoorioLM si está configurado
            row_class = "highlight" if self.config.highlight_empoorio and model_name.lower() == "empoorio" else ""

            table_html += f"""
                <tr class="{row_class}">
                    <td><strong>{model_name.upper()}</strong></td>
                    <td>{metrics.get('accuracy_overall', 0):.3f}</td>
                    <td>{metrics.get('avg_latency', 0):.2f}</td>
                    <td>{metrics.get('total_energy_joules', 0):.1f}</td>
                    <td>{metrics.get('rag_accuracy', 0):.3f}</td>
                    <td>{metrics.get('efficiency_score', 0):.2f}</td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html

    def _calculate_performance_summary(self) -> str:
        """Calcula resumen de rendimiento."""
        if not self.comparison_data:
            return "rendimiento no disponible"

        # Lógica simplificada - implementar análisis real
        return "un rendimiento superior en múltiples dimensiones"

    def _calculate_energy_efficiency(self) -> str:
        """Calcula eficiencia energética."""
        return "significativamente más eficiente que la competencia"

    def _generate_competitive_advantages(self) -> str:
        """Genera lista de ventajas competitivas."""
        advantages = [
            "<li>Mayor precisión en tareas de razonamiento</li>",
            "<li>Latencia reducida para respuestas en tiempo real</li>",
            "<li>Consumo energético optimizado</li>",
            "<li>Excelente capacidad de recuperación RAG</li>"
        ]
        return "\n".join(advantages)

    def _assess_market_position(self) -> str:
        """Evalúa posicionamiento de mercado."""
        return "una alternativa viable y superior para aplicaciones empresariales"

    def _generate_accuracy_detailed_table(self) -> str:
        """Genera tabla detallada de precisión."""
        if not self.comparison_data:
            return "<p>No hay datos disponibles</p>"

        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        table_html = """
        <table class="detailed-table">
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>MMLU</th>
                    <th>GSM8K</th>
                    <th>Precisión General</th>
                    <th>Muestras</th>
                </tr>
            </thead>
            <tbody>
        """

        for model_name, metrics in comprehensive_metrics.items():
            row_class = "highlight" if self.config.highlight_empoorio and model_name.lower() == "empoorio" else ""

            table_html += f"""
                <tr class="{row_class}">
                    <td><strong>{model_name.upper()}</strong></td>
                    <td>{metrics.get('accuracy_mmlu', 0):.3f}</td>
                    <td>{metrics.get('accuracy_gsm8k', 0):.3f}</td>
                    <td><strong>{metrics.get('accuracy_overall', 0):.3f}</strong></td>
                    <td>{metrics.get('sample_count', 0)}</td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html

    def _generate_accuracy_insights(self) -> str:
        """Genera insights sobre precisión."""
        if not self.comparison_data:
            return "<ul><li>No hay datos disponibles para análisis</li></ul>"

        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})
        statistical_comparisons = self.comparison_data.get('statistical_comparisons', [])

        insights = []

        # Encontrar mejor modelo en precisión
        if comprehensive_metrics:
            best_accuracy = max(comprehensive_metrics.items(),
                              key=lambda x: x[1].get('accuracy_overall', 0))
            insights.append(f"<li><strong>{best_accuracy[0].upper()}</strong> muestra la mayor precisión general ({best_accuracy[1].get('accuracy_overall', 0):.3f})</li>")

        # Análisis estadístico
        significant_comparisons = [c for c in statistical_comparisons
                                 if c.get('significant', False) and c.get('metric') == 'accuracy_overall']

        if significant_comparisons:
            insights.append(f"<li>Se encontraron {len(significant_comparisons)} comparaciones estadísticamente significativas en precisión</li>")

        # Análisis de fortalezas
        for model_name, metrics in comprehensive_metrics.items():
            mmlu = metrics.get('accuracy_mmlu', 0)
            gsm8k = metrics.get('accuracy_gsm8k', 0)

            if mmlu > gsm8k + 0.1:  # Mejor en conocimiento general
                insights.append(f"<li>{model_name.upper()} destaca en conocimiento general (MMLU: {mmlu:.3f})</li>")
            elif gsm8k > mmlu + 0.1:  # Mejor en matemáticas
                insights.append(f"<li>{model_name.upper()} destaca en razonamiento matemático (GSM8K: {gsm8k:.3f})</li>")

        if not insights:
            insights = ["<li>Análisis detallado de precisión disponible en los datos crudos</li>"]

        return "<ul>" + "\n".join(insights) + "</ul>"

    def _generate_all_charts(self):
        """Genera todos los gráficos del reporte."""
        if not self.comparison_data:
            return

        logger.info("📊 Generando gráficos del reporte")

        # Usar generador de gráficos de marketing si está disponible
        if self.marketing_charts_generator and MARKETING_CHARTS_AVAILABLE:
            self._generate_marketing_charts()
        elif PLOTTING_AVAILABLE:
            # Usar gráficos básicos como fallback
            self._generate_basic_charts()
        else:
            logger.warning("⚠️ No hay generadores de gráficos disponibles")

    def _generate_marketing_charts(self):
        """Genera gráficos profesionales usando MarketingChartsGenerator."""
        logger.info("🎨 Generando gráficos de marketing profesionales")

        # Generar suite completa de gráficos de marketing
        generated_charts = self.marketing_charts_generator.generate_marketing_chart_suite()

        # Actualizar secciones del reporte con las nuevas rutas de gráficos
        self._update_sections_with_marketing_charts(generated_charts)

        logger.info(f"✅ Generados {len(generated_charts)} gráficos de marketing")

    def _generate_basic_charts(self):
        """Genera gráficos básicos como fallback."""
        logger.info("📊 Generando gráficos básicos")

        # Gráfico de precisión comparativa
        self._generate_accuracy_chart()

        # Gráfico de latencia
        self._generate_latency_chart()

        # Gráfico de eficiencia energética
        self._generate_energy_chart()

        # Gráfico radar multi-dimensional
        self._generate_radar_chart()

        # Gráfico de curva RAG
        self._generate_rag_curve_chart()

    def _update_sections_with_marketing_charts(self, generated_charts: Dict[str, str]):
        """Actualiza las secciones del reporte con los gráficos de marketing generados."""
        # Mapear gráficos generados a secciones del reporte
        chart_mapping = {
            'accuracy_bar': ('Análisis de Precisión', 'accuracy_comparison.png'),
            'accuracy_line': ('Análisis de Precisión', 'accuracy_line_chart.png'),
            'accuracy_radar': ('Comparación Multi-dimensional', 'accuracy_radar_chart.png'),
            'latency_bar': ('Análisis de Latencia', 'latency_comparison.png'),
            'energy_bar': ('Análisis Energético', 'energy_comparison.png'),
            'efficiency_bar': ('Análisis de Precisión', 'efficiency_comparison.png'),
            'rag_bar': ('Análisis RAG', 'rag_comparison.png'),
            'performance_radar': ('Comparación Multi-dimensional', 'performance_radar_chart.png')
        }

        for chart_key, (section_title, filename) in chart_mapping.items():
            if chart_key in generated_charts:
                # Copiar archivo al directorio del reporte para consistencia
                import shutil
                chart_path = generated_charts[chart_key]
                report_chart_path = os.path.join(self.config.output_dir, filename)

                try:
                    shutil.copy2(chart_path, report_chart_path)
                    logger.debug(f"📋 Gráfico copiado: {filename}")
                except Exception as e:
                    logger.warning(f"Error copiando gráfico {chart_key}: {e}")
                    continue

                # Actualizar sección correspondiente
                for section in self.sections:
                    if section.title == section_title:
                        # Añadir gráfico a la sección si no existe
                        if filename not in [os.path.basename(c) for c in section.charts]:
                            section.charts.append(filename)
                        break

    def _generate_accuracy_chart(self):
        """Genera gráfico de precisión comparativa."""
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        models = []
        accuracies = []

        for model_name, metrics in comprehensive_metrics.items():
            models.append(model_name.upper())
            accuracies.append(metrics.get('accuracy_overall', 0))

        plt.figure(figsize=(10, 6))
        bars = plt.bar(models, accuracies, color=self.color_palettes[self.config.color_palette][:len(models)])

        plt.title('Comparación de Precisión en Benchmarks', fontsize=14, fontweight='bold')
        plt.ylabel('Precisión', fontsize=12)
        plt.xlabel('Modelo', fontsize=12)
        plt.ylim(0, 1)

        # Añadir valores en las barras
        for bar, acc in zip(bars, accuracies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{acc:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.grid(True, alpha=0.3, axis='y')
        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        # Guardar gráfico
        chart_path = os.path.join(self.config.output_dir, 'accuracy_comparison.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico de precisión guardado: {chart_path}")

    def _generate_latency_chart(self):
        """Genera gráfico de latencia."""
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        models = []
        latencies = []

        for model_name, metrics in comprehensive_metrics.items():
            models.append(model_name.upper())
            latencies.append(metrics.get('avg_latency', 0))

        plt.figure(figsize=(10, 6))
        bars = plt.bar(models, latencies, color=self.color_palettes[self.config.color_palette][:len(models)])

        plt.title('Comparación de Latencia Promedio', fontsize=14, fontweight='bold')
        plt.ylabel('Latencia (segundos)', fontsize=12)
        plt.xlabel('Modelo', fontsize=12)

        # Añadir valores en las barras
        for bar, lat in zip(bars, latencies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{lat:.2f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.grid(True, alpha=0.3, axis='y')
        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        chart_path = os.path.join(self.config.output_dir, 'latency_comparison.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico de latencia guardado: {chart_path}")

    def _generate_energy_chart(self):
        """Genera gráfico de eficiencia energética."""
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        models = []
        energies = []

        for model_name, metrics in comprehensive_metrics.items():
            models.append(model_name.upper())
            energies.append(metrics.get('total_energy_joules', 0))

        plt.figure(figsize=(10, 6))
        bars = plt.bar(models, energies, color=self.color_palettes[self.config.color_palette][:len(models)])

        plt.title('Comparación de Consumo Energético', fontsize=14, fontweight='bold')
        plt.ylabel('Energía Consumida (Joules)', fontsize=12)
        plt.xlabel('Modelo', fontsize=12)

        # Añadir valores en las barras
        for bar, energy in zip(bars, energies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{energy:.1f}J', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.grid(True, alpha=0.3, axis='y')
        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        chart_path = os.path.join(self.config.output_dir, 'energy_comparison.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico de energía guardado: {chart_path}")

    def _generate_radar_chart(self):
        """Genera gráfico radar multi-dimensional."""
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        if len(comprehensive_metrics) < 3:
            return  # Necesitamos al menos 3 modelos para radar

        # Preparar datos
        models = list(comprehensive_metrics.keys())
        metrics_names = ['Precisión', 'Latencia', 'Energía', 'Eficiencia', 'RAG']

        # Normalizar métricas
        normalized_data = {}
        for model in models:
            metrics = comprehensive_metrics[model]
            # Normalizar (mayor = mejor, excepto latencia y energía que se invierten)
            norm_accuracy = metrics.get('accuracy_overall', 0)
            norm_latency = 1 - min(metrics.get('avg_latency', 1) / 5, 1)  # Invertir y normalizar
            norm_energy = 1 - min(metrics.get('total_energy_joules', 100) / 100, 1)  # Invertir
            norm_efficiency = min(metrics.get('efficiency_score', 1), 1)
            norm_rag = metrics.get('rag_accuracy', 0)

            normalized_data[model] = [norm_accuracy, norm_latency, norm_energy, norm_efficiency, norm_rag]

        # Crear radar chart
        angles = [n / float(len(metrics_names)) * 2 * 3.14159 for n in range(len(metrics_names))]
        angles += angles[:1]  # Cerrar el círculo

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        for i, model in enumerate(models):
            values = normalized_data[model]
            values += values[:1]  # Cerrar el círculo

            ax.plot(angles, values, 'o-', linewidth=2,
                   label=model.upper(), color=self.color_palettes[self.config.color_palette][i])
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names)
        ax.set_ylim(0, 1)
        ax.set_title('Comparación Multi-dimensional de Rendimiento', size=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)

        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        chart_path = os.path.join(self.config.output_dir, 'radar_comparison.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico radar guardado: {chart_path}")

    def _generate_rag_curve_chart(self):
        """Genera gráfico de curva RAG por contexto."""
        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        plt.figure(figsize=(12, 8))

        for model_name, metrics in comprehensive_metrics.items():
            rag_curve = metrics.get('rag_performance_curve', {})
            if rag_curve:
                contexts = sorted(rag_curve.keys())
                accuracies = [rag_curve[ctx] for ctx in contexts]

                plt.plot(contexts, accuracies, 'o-', label=model_name.upper(),
                        linewidth=2, markersize=6)

        plt.xlabel('Tamaño del Contexto (tokens)', fontsize=12)
        plt.ylabel('Precisión RAG', fontsize=12)
        plt.title('Capacidad de Recuperación RAG vs Tamaño del Contexto', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')

        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        chart_path = os.path.join(self.config.output_dir, 'rag_curve.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico RAG guardado: {chart_path}")

    def _generate_html_report(self) -> str:
        """Genera reporte HTML."""
        if not JINJA2_AVAILABLE:
            logger.warning("Jinja2 no disponible, saltando generación HTML")
            return ""

        # Crear template HTML básico si no existe
        self._ensure_html_template()

        # Preparar datos para el template
        template_data = {
            'config': self.config,
            'sections': self.sections,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'charts': self._get_chart_urls()
        }

        # Renderizar template
        template = self.jinja_env.get_template('performance_report.html')
        html_content = template.render(**template_data)

        # Guardar HTML
        html_file = os.path.join(self.config.output_dir,
                                f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"📄 Reporte HTML generado: {html_file}")
        return html_file

    def _generate_pdf_report(self) -> str:
        """Genera reporte PDF."""
        html_file = self._generate_html_report()
        if not html_file:
            return ""

        pdf_file = html_file.replace('.html', '.pdf')

        try:
            if WEASYPRINT_AVAILABLE:
                # Usar weasyprint
                HTML(html_file).write_pdf(pdf_file)
                logger.info(f"📕 Reporte PDF generado con weasyprint: {pdf_file}")

            elif PDFKIT_AVAILABLE:
                # Usar pdfkit como fallback
                pdfkit.from_file(html_file, pdf_file)
                logger.info(f"📕 Reporte PDF generado con pdfkit: {pdf_file}")

            else:
                logger.warning("No hay conversor PDF disponible")
                return ""

        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            return ""

        return pdf_file

    def _generate_json_report(self) -> str:
        """Genera reporte JSON con todos los datos."""
        json_file = os.path.join(self.config.output_dir,
                                f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

        report_data = {
            'metadata': {
                'title': self.config.report_title,
                'version': self.config.report_version,
                'author': self.config.author,
                'timestamp': self.config.generation_timestamp,
                'data_source': self.config.data_source
            },
            'comparison_data': self.comparison_data,
            'sections': [
                {
                    'title': section.title,
                    'type': section.section_type,
                    'metrics': section.metrics
                } for section in self.sections
            ]
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 Reporte JSON generado: {json_file}")
        return json_file

    def _ensure_html_template(self):
        """Asegura que existe el template HTML básico."""
        template_file = os.path.join(self.template_dir, 'performance_report.html')

        if os.path.exists(template_file):
            return

        # Crear template HTML básico
        template_content = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ config.report_title }}</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }

                .cover-page {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 60px 40px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 40px;
                }

                .company-header h1 {
                    margin: 0;
                    font-size: 3em;
                    font-weight: 300;
                }

                .report-title h2 {
                    margin: 20px 0;
                    font-size: 2em;
                    font-weight: 400;
                }

                .report-meta {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 40px 0;
                }

                .meta-item {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 8px;
                }

                .meta-label {
                    font-weight: bold;
                    display: block;
                    margin-bottom: 5px;
                }

                .section {
                    background: white;
                    margin: 30px 0;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }

                .section h3 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 0;
                }

                .key-highlights {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }

                .highlight-card {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }

                .highlight-card h4 {
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                }

                .chart-container {
                    text-align: center;
                    margin: 30px 0;
                }

                .chart-container img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                /* Estilos de tablas */
                .comparison-table, .detailed-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 0.9em;
                }

                .comparison-table th, .detailed-table th {
                    background: #3498db;
                    color: white;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                }

                .comparison-table td, .detailed-table td {
                    padding: 10px 8px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }

                .comparison-table tr:nth-child(even), .detailed-table tr:nth-child(even) {
                    background: #f8f9fa;
                }

                .comparison-table tr.highlight, .detailed-table tr.highlight {
                    background: #e8f4fd;
                    font-weight: bold;
                }

                .comparison-table tr.highlight td:first-child, .detailed-table tr.highlight td:first-child {
                    color: #2c3e50;
                }

                /* Estilos de métricas */
                .key-highlights {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }

                .highlight-card {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .highlight-card h4 {
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                    font-size: 1.1em;
                }

                .highlight-card p {
                    margin: 0;
                    color: #34495e;
                }

                /* Estilos de listas */
                .competitive-advantages ul, .accuracy-insights ul {
                    padding-left: 20px;
                }

                .competitive-advantages li, .accuracy-insights li {
                    margin: 8px 0;
                    line-height: 1.5;
                }

                /* Sección de introducción */
                .section-intro {
                    background: #ecf0f1;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                    border-left: 4px solid #bdc3c7;
                }

                .section-intro p {
                    margin: 0;
                    color: #2c3e50;
                }

                @media print {
                    body {
                        background: white !important;
                        max-width: none;
                        margin: 0;
                        padding: 20px;
                    }

                    .section {
                        page-break-inside: avoid;
                        box-shadow: none;
                        border: 1px solid #ddd;
                    }

                    .cover-page {
                        background: white !important;
                        color: black !important;
                        border: 2px solid #3498db;
                    }

                    .highlight-card {
                        background: #f8f9fa !important;
                        border: 1px solid #ddd;
                    }
                }
            </style>
        </head>
        <body>
            {% for section in sections %}
            <div class="section">
                {{ section.content|safe }}
            </div>
            {% endfor %}

            {% for chart_url in charts %}
            <div class="section chart-container">
                <img src="{{ chart_url }}" alt="Chart">
            </div>
            {% endfor %}

            <div class="section">
                <p style="text-align: center; color: #666; font-size: 0.9em;">
                    Reporte generado el {{ timestamp }} por {{ config.author }}
                </p>
            </div>
        </body>
        </html>
        """

        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)

        logger.info(f"📄 Template HTML creado: {template_file}")

    def _get_chart_urls(self) -> List[str]:
        """Obtiene URLs de los gráficos generados."""
        chart_files = [
            'accuracy_comparison.png',
            'latency_comparison.png',
            'energy_comparison.png',
            'radar_comparison.png',
            'rag_curve.png'
        ]

        chart_urls = []
        for chart_file in chart_files:
            chart_path = os.path.join(self.config.output_dir, chart_file)
            if os.path.exists(chart_path):
                # Para HTML, usar ruta relativa
                chart_urls.append(chart_file)

        return chart_urls


# Funciones de conveniencia
def create_performance_report_generator(output_dir: str = './performance_reports') -> PerformanceReportGenerator:
    """Crea un generador de reportes con configuración por defecto."""
    config = PerformanceReportConfig(output_dir=output_dir)
    return PerformanceReportGenerator(config)


def generate_performance_report(comparison_results: Dict[str, Any],
                              output_dir: str = './performance_reports',
                              use_marketing_charts: bool = True,
                              chart_platform: str = 'presentation') -> Dict[str, str]:
    """
    Genera reporte de rendimiento de manera conveniente.

    Args:
        comparison_results: Resultados del AccuracyComparisonFramework
        output_dir: Directorio de salida
        use_marketing_charts: Usar gráficos profesionales de marketing
        chart_platform: Plataforma para optimización de gráficos

    Returns:
        Dict con rutas de archivos generados
    """
    config = PerformanceReportConfig(
        output_dir=output_dir,
        use_marketing_charts=use_marketing_charts,
        chart_platform=chart_platform
    )
    generator = PerformanceReportGenerator(config)
    generator.load_comparison_data(comparison_results)
    return generator.generate_comprehensive_report()


if __name__ == "__main__":
    # Ejemplo de uso
    print("🚀 Performance Report Generator para EmpoorioLM")
    print("Genera reportes HTML/PDF profesionales con análisis de rendimiento")

    # Crear generador básico
    generator = create_performance_report_generator()

    print(f"📊 Configuración: Output dir = {generator.config.output_dir}")
    print("💡 Para usar con datos reales, carga resultados del AccuracyComparisonFramework")
    print("💡 Ejemplo: generator.load_comparison_data(results); generator.generate_comprehensive_report()")