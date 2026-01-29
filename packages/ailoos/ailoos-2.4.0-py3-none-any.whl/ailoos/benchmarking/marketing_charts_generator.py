"""
Generador de Gráficos Profesionales para Marketing de EmpoorioLM
Crea visualizaciones atractivas y listas para marketing comparando EmpoorioLM vs gigantes.
Incluye estilos de marca AILOOS, optimizaciones para redes sociales y presentaciones.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import base64
import io

# Imports para gráficos
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Backend no interactivo
    import seaborn as sns
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️ matplotlib/seaborn/numpy no disponibles, gráficos deshabilitados")

# Añadir src al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MarketingChartConfig:
    """Configuración del generador de gráficos de marketing."""
    # Configuración general
    output_dir: str = './marketing_charts'
    brand_name: str = 'Ailoos'
    product_name: str = 'EmpoorioLM'

    # Configuración de estilos
    color_palette: str = 'ailoos'  # 'ailoos', 'professional', 'vibrant', 'minimal'
    chart_style: str = 'modern'  # 'modern', 'classic', 'bold', 'clean'

    # Configuración de optimización
    target_platform: str = 'presentation'  # 'presentation', 'social_media', 'web', 'print'
    dpi: int = 300
    figsize: Tuple[int, int] = (12, 8)

    # Configuración de contenido
    highlight_empoorio: bool = True
    show_values_on_bars: bool = True
    include_watermark: bool = True
    auto_generate_titles: bool = True

    # Configuración específica de plataforma
    social_media_formats: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'instagram_post': (1080, 1080),
        'instagram_story': (1080, 1920),
        'twitter_post': (1200, 675),
        'linkedin_post': (1200, 627),
        'facebook_post': (1200, 630),
        'tiktok': (1080, 1920)
    })


@dataclass
class ChartMetadata:
    """Metadata de un gráfico generado."""
    filename: str
    title: str
    chart_type: str
    metrics: List[str]
    models: List[str]
    platform_optimized: str
    created_at: str


class MarketingChartsGenerator:
    """
    Generador de gráficos profesionales para marketing de EmpoorioLM.
    Crea visualizaciones atractivas comparando rendimiento vs gigantes.
    """

    def __init__(self, config: MarketingChartConfig = None):
        self.config = config or MarketingChartConfig()
        self.comparison_data = None
        self.generated_charts: List[ChartMetadata] = []

        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)

        # Configurar estilos y colores
        self._setup_brand_styling()

        logger.info("🚀 MarketingChartsGenerator inicializado")

    def _setup_brand_styling(self):
        """Configura estilos de marca AILOOS."""
        if not PLOTTING_AVAILABLE:
            return

        # Paletas de colores AILOOS
        self.color_palettes = {
            'ailoos': {
                'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
                'accent': ['#17becf', '#bcbd22', '#7f7f7f', '#e377c2', '#8c564b'],
                'gradient': ['#667eea', '#764ba2'],
                'highlight': '#ff7f0e',  # Naranja para destacar EmpoorioLM
                'secondary': '#1f77b4'   # Azul para competidores
            },
            'professional': {
                'primary': ['#2E3440', '#5E81AC', '#A3BE8C', '#EBCB8B', '#BF616A', '#B48EAD'],
                'accent': ['#88C0D0', '#81A1C1', '#5E81AC'],
                'highlight': '#A3BE8C',
                'secondary': '#5E81AC'
            },
            'vibrant': {
                'primary': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
                'accent': ['#BB8FCE', '#85C1E9', '#F8C471'],
                'highlight': '#FF6B6B',
                'secondary': '#4ECDC4'
            },
            'minimal': {
                'primary': ['#2C3E50', '#34495E', '#7F8C8D', '#BDC3C7', '#ECF0F1'],
                'accent': ['#3498DB', '#E74C3C', '#2ECC71'],
                'highlight': '#3498DB',
                'secondary': '#2C3E50'
            }
        }

        # Configurar matplotlib
        plt.style.use('seaborn-v0_8-whitegrid' if hasattr(plt.style, 'available') and 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

        # Configurar fuentes y tamaños
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 14
        plt.rcParams['xtick.labelsize'] = 12
        plt.rcParams['ytick.labelsize'] = 12
        plt.rcParams['legend.fontsize'] = 12
        plt.rcParams['figure.titlesize'] = 18

        # Configurar seaborn
        sns.set_palette(self.color_palettes[self.config.color_palette]['primary'])

    def load_comparison_data(self, comparison_results: Dict[str, Any]):
        """
        Carga datos del AccuracyComparisonFramework.

        Args:
            comparison_results: Resultados del framework de comparación
        """
        self.comparison_data = comparison_results
        logger.info("✅ Datos de comparación cargados para gráficos de marketing")

    def optimize_for_platform(self, platform: str):
        """
        Optimiza configuración para una plataforma específica.

        Args:
            platform: 'presentation', 'social_media', 'web', 'print'
        """
        self.config.target_platform = platform

        if platform == 'social_media':
            # Optimizaciones para redes sociales
            self.config.dpi = 150  # Suficiente para pantalla
            self.config.figsize = (10, 10)  # Cuadrado para Instagram
            plt.rcParams['font.size'] = 14
            plt.rcParams['axes.titlesize'] = 18

        elif platform == 'presentation':
            # Optimizaciones para presentaciones
            self.config.dpi = 200
            self.config.figsize = (13.33, 7.5)  # 16:9 ratio
            plt.rcParams['font.size'] = 16
            plt.rcParams['axes.titlesize'] = 20

        elif platform == 'web':
            # Optimizaciones para web
            self.config.dpi = 100
            self.config.figsize = (12, 8)
            plt.rcParams['font.size'] = 12

        elif platform == 'print':
            # Optimizaciones para impresión
            self.config.dpi = 600
            self.config.figsize = (11.69, 8.27)  # A4 landscape
            plt.rcParams['font.size'] = 10

        logger.info(f"🎯 Optimizado para plataforma: {platform}")

    def set_social_media_format(self, format_name: str):
        """
        Configura tamaño específico para formato de red social.

        Args:
            format_name: Nombre del formato (instagram_post, twitter_post, etc.)
        """
        if format_name in self.config.social_media_formats:
            width, height = self.config.social_media_formats[format_name]
            # Convertir pixels a inches (asumiendo 100 DPI base)
            self.config.figsize = (width/100, height/100)
            self.config.dpi = 100
            logger.info(f"📱 Configurado para formato: {format_name} ({width}x{height})")

    def generate_accuracy_comparison_chart(self, chart_type: str = 'bar',
                                         title: str = None, filename: str = None) -> str:
        """
        Genera gráfico de comparación de precisión.

        Args:
            chart_type: 'bar', 'line', 'radar', 'histogram'
            title: Título personalizado
            filename: Nombre de archivo personalizado

        Returns:
            Ruta del archivo generado
        """
        if not self.comparison_data or not PLOTTING_AVAILABLE:
            return ""

        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        if chart_type == 'bar':
            return self._generate_accuracy_bar_chart(comprehensive_metrics, title, filename)
        elif chart_type == 'line':
            return self._generate_accuracy_line_chart(comprehensive_metrics, title, filename)
        elif chart_type == 'radar':
            return self._generate_accuracy_radar_chart(comprehensive_metrics, title, filename)
        elif chart_type == 'histogram':
            return self._generate_accuracy_histogram_chart(comprehensive_metrics, title, filename)
        else:
            logger.warning(f"Tipo de gráfico no soportado: {chart_type}")
            return ""

    def _generate_accuracy_bar_chart(self, metrics: Dict, title: str = None, filename: str = None) -> str:
        """Genera gráfico de barras de precisión."""
        models = []
        accuracies = []
        colors = []

        palette = self.color_palettes[self.config.color_palette]['primary']

        for model_name, model_metrics in metrics.items():
            models.append(model_name.upper())
            accuracies.append(model_metrics.get('accuracy_overall', 0))

            # Colores: destacar EmpoorioLM
            if self.config.highlight_empoorio and model_name.lower() == 'empoorio':
                colors.append(self.color_palettes[self.config.color_palette]['highlight'])
            else:
                colors.append(self.color_palettes[self.config.color_palette]['secondary'])

        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        bars = ax.bar(models, accuracies, color=colors, alpha=0.8, edgecolor='black', linewidth=1)

        # Título automático si no se proporciona
        if not title and self.config.auto_generate_titles:
            empoorio_acc = metrics.get('empoorio', {}).get('accuracy_overall', 0)
            best_competitor = max(
                [(name, m.get('accuracy_overall', 0)) for name, m in metrics.items() if name.lower() != 'empoorio'],
                key=lambda x: x[1], default=('', 0)
            )
            if best_competitor[1] > 0:
                improvement = ((empoorio_acc - best_competitor[1]) / best_competitor[1]) * 100
                title = f"EmpoorioLM: {improvement:+.1f}% más preciso que {best_competitor[0].upper()}"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)

        ax.set_ylabel('Precisión en Benchmarks', fontsize=14, fontweight='bold')
        ax.set_xlabel('Modelo', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1)

        # Añadir valores en las barras
        if self.config.show_values_on_bars:
            for bar, acc in zip(bars, accuracies):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{acc:.3f}', ha='center', va='bottom',
                       fontsize=12, fontweight='bold')

        # Grid sutil
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        # Añadir marca de agua
        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        # Guardar
        if not filename:
            filename = f'accuracy_comparison_bar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        # Registrar metadata
        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or "Comparación de Precisión",
            chart_type='bar',
            metrics=['accuracy_overall'],
            models=list(metrics.keys()),
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"📊 Gráfico de barras de precisión guardado: {filepath}")
        return filepath

    def _generate_accuracy_line_chart(self, metrics: Dict, title: str = None, filename: str = None) -> str:
        """Genera gráfico de líneas de precisión por dataset."""
        # Para línea, necesitamos datos por dataset (MMLU, GSM8K, etc.)
        datasets = ['mmlu', 'gsm8k']
        models = list(metrics.keys())

        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        palette = self.color_palettes[self.config.color_palette]['primary']

        for i, model_name in enumerate(models):
            model_metrics = metrics[model_name]
            dataset_scores = []

            for dataset in datasets:
                if dataset == 'mmlu':
                    score = model_metrics.get('accuracy_mmlu', 0)
                elif dataset == 'gsm8k':
                    score = model_metrics.get('accuracy_gsm8k', 0)
                else:
                    score = 0
                dataset_scores.append(score)

            color = self.color_palettes[self.config.color_palette]['highlight'] if self.config.highlight_empoorio and model_name.lower() == 'empoorio' else palette[i % len(palette)]
            ax.plot(datasets, dataset_scores, 'o-', linewidth=3, markersize=8,
                   label=model_name.upper(), color=color)

        if not title and self.config.auto_generate_titles:
            title = "Precisión por Tipo de Benchmark: MMLU vs GSM8K"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)

        ax.set_ylabel('Precisión', fontsize=14, fontweight='bold')
        ax.set_xlabel('Dataset de Benchmark', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        if not filename:
            filename = f'accuracy_line_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or "Precisión por Dataset",
            chart_type='line',
            metrics=['accuracy_mmlu', 'accuracy_gsm8k'],
            models=models,
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"📈 Gráfico de líneas de precisión guardado: {filepath}")
        return filepath

    def _generate_accuracy_radar_chart(self, metrics: Dict, title: str = None, filename: str = None) -> str:
        """Genera gráfico radar de precisión multi-dimensional."""
        if len(metrics) < 3:
            logger.warning("Se necesitan al menos 3 modelos para gráfico radar")
            return ""

        # Métricas para radar
        radar_metrics = ['accuracy_overall', 'accuracy_mmlu', 'accuracy_gsm8k']
        metric_labels = ['Precisión General', 'MMLU', 'GSM8K']

        # Normalizar valores
        normalized_data = {}
        for model_name, model_metrics in metrics.items():
            normalized = []
            for metric in radar_metrics:
                value = model_metrics.get(metric, 0)
                # Normalizar al rango 0-1
                normalized.append(min(value, 1.0))
            normalized_data[model_name] = normalized

        # Crear radar
        angles = np.linspace(0, 2 * np.pi, len(radar_metrics), endpoint=False).tolist()
        angles += angles[:1]  # Cerrar el círculo

        fig, ax = plt.subplots(figsize=self.config.figsize, subplot_kw=dict(projection='polar'), dpi=self.config.dpi)

        palette = self.color_palettes[self.config.color_palette]['primary']

        for i, (model_name, values) in enumerate(normalized_data.items()):
            values += values[:1]  # Cerrar el círculo

            color = self.color_palettes[self.config.color_palette]['highlight'] if self.config.highlight_empoorio and model_name.lower() == 'empoorio' else palette[i % len(palette)]
            ax.plot(angles, values, 'o-', linewidth=3, label=model_name.upper(),
                   color=color, markersize=8)
            ax.fill(angles, values, alpha=0.25, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

        if not title and self.config.auto_generate_titles:
            title = "Perfil de Precisión: Visión Multi-dimensional"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=30)

        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))

        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        if not filename:
            filename = f'accuracy_radar_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or "Radar de Precisión",
            chart_type='radar',
            metrics=radar_metrics,
            models=list(metrics.keys()),
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"🎯 Gráfico radar de precisión guardado: {filepath}")
        return filepath

    def _generate_accuracy_histogram_chart(self, metrics: Dict, title: str = None, filename: str = None) -> str:
        """Genera histograma de distribución de precisión."""
        # Recopilar todas las precisiones individuales si disponibles
        all_accuracies = []
        model_labels = []

        for model_name, model_metrics in metrics.items():
            # Si hay datos crudos de benchmarks, usarlos
            raw_benchmarks = model_metrics.get('raw_data', {}).get('benchmark_results', [])
            if raw_benchmarks:
                accuracies = [r.get('accuracy', model_metrics.get('accuracy_overall', 0)) for r in raw_benchmarks]
            else:
                # Usar solo el promedio
                accuracies = [model_metrics.get('accuracy_overall', 0)]

            all_accuracies.extend(accuracies)
            model_labels.extend([model_name.upper()] * len(accuracies))

        if not all_accuracies:
            logger.warning("No hay datos suficientes para histograma")
            return ""

        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Crear histograma con colores por modelo
        palette = self.color_palettes[self.config.color_palette]['primary']
        colors = [self.color_palettes[self.config.color_palette]['highlight'] if label == 'EMPOORIO' else palette[i % len(palette)]
                 for i, label in enumerate(set(model_labels))]

        ax.hist(all_accuracies, bins=20, alpha=0.7, edgecolor='black', linewidth=1)

        if not title and self.config.auto_generate_titles:
            title = "Distribución de Precisión en Benchmarks"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)

        ax.set_xlabel('Precisión', fontsize=14, fontweight='bold')
        ax.set_ylabel('Frecuencia', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        if not filename:
            filename = f'accuracy_histogram_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or "Histograma de Precisión",
            chart_type='histogram',
            metrics=['accuracy_overall'],
            models=list(metrics.keys()),
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"📊 Histograma de precisión guardado: {filepath}")
        return filepath

    def generate_performance_comparison_chart(self, metric: str = 'latency',
                                            chart_type: str = 'bar', title: str = None,
                                            filename: str = None) -> str:
        """
        Genera gráfico de comparación de rendimiento para cualquier métrica.

        Args:
            metric: 'latency', 'energy', 'efficiency', 'rag_accuracy'
            chart_type: 'bar', 'line', 'radar'
            title: Título personalizado
            filename: Nombre de archivo personalizado

        Returns:
            Ruta del archivo generado
        """
        if not self.comparison_data or not PLOTTING_AVAILABLE:
            return ""

        comprehensive_metrics = self.comparison_data.get('comprehensive_metrics', {})

        # Mapear métricas a atributos
        metric_mapping = {
            'latency': 'avg_latency',
            'energy': 'total_energy_joules',
            'efficiency': 'efficiency_score',
            'rag_accuracy': 'rag_accuracy'
        }

        if metric not in metric_mapping:
            logger.warning(f"Métrica no soportada: {metric}")
            return ""

        attr_name = metric_mapping[metric]

        if chart_type == 'bar':
            return self._generate_performance_bar_chart(comprehensive_metrics, metric, attr_name, title, filename)
        elif chart_type == 'radar':
            return self._generate_performance_radar_chart(comprehensive_metrics, title, filename)
        else:
            logger.warning(f"Tipo de gráfico no soportado para rendimiento: {chart_type}")
            return ""

    def _generate_performance_bar_chart(self, metrics: Dict, metric_name: str,
                                      attr_name: str, title: str = None, filename: str = None) -> str:
        """Genera gráfico de barras para métricas de rendimiento."""
        models = []
        values = []
        colors = []

        palette = self.color_palettes[self.config.color_palette]['primary']

        for model_name, model_metrics in metrics.items():
            models.append(model_name.upper())
            value = model_metrics.get(attr_name, 0)
            values.append(value)

            # Colores: destacar EmpoorioLM
            if self.config.highlight_empoorio and model_name.lower() == 'empoorio':
                colors.append(self.color_palettes[self.config.color_palette]['highlight'])
            else:
                colors.append(self.color_palettes[self.config.color_palette]['secondary'])

        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        bars = ax.bar(models, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1)

        # Título automático
        if not title and self.config.auto_generate_titles:
            if metric_name == 'latency':
                empoorio_val = metrics.get('empoorio', {}).get('avg_latency', 0)
                best_competitor = min(
                    [(name, m.get('avg_latency', float('inf'))) for name, m in metrics.items() if name.lower() != 'empoorio'],
                    key=lambda x: x[1], default=('', float('inf'))
                )
                if best_competitor[1] < float('inf') and best_competitor[1] > 0:
                    improvement = ((best_competitor[1] - empoorio_val) / best_competitor[1]) * 100
                    title = f"EmpoorioLM: {improvement:.1f}% más rápido que {best_competitor[0].upper()}"
            elif metric_name == 'energy':
                title = "Eficiencia Energética: Comparación de Consumo"
            elif metric_name == 'efficiency':
                title = "Score de Eficiencia Global"
            elif metric_name == 'rag_accuracy':
                title = "Capacidad de Recuperación RAG"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)

        # Labels según métrica
        if metric_name == 'latency':
            ax.set_ylabel('Latencia Promedio (segundos)', fontsize=14, fontweight='bold')
        elif metric_name == 'energy':
            ax.set_ylabel('Energía Consumida (Joules)', fontsize=14, fontweight='bold')
        elif metric_name == 'efficiency':
            ax.set_ylabel('Score de Eficiencia', fontsize=14, fontweight='bold')
        elif metric_name == 'rag_accuracy':
            ax.set_ylabel('Precisión RAG', fontsize=14, fontweight='bold')
            ax.set_ylim(0, 1)

        ax.set_xlabel('Modelo', fontsize=14, fontweight='bold')

        # Añadir valores en las barras
        if self.config.show_values_on_bars:
            for bar, val in zip(bars, values):
                height = bar.get_height()
                if metric_name == 'latency':
                    text = f'{val:.2f}s'
                elif metric_name == 'energy':
                    text = f'{val:.1f}J'
                elif metric_name == 'rag_accuracy':
                    text = f'{val:.3f}'
                else:
                    text = f'{val:.2f}'

                ax.text(bar.get_x() + bar.get_width()/2., height + (height * 0.02),
                       text, ha='center', va='bottom',
                       fontsize=12, fontweight='bold')

        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        if not filename:
            filename = f'{metric_name}_comparison_bar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or f"Comparación de {metric_name.capitalize()}",
            chart_type='bar',
            metrics=[attr_name],
            models=list(metrics.keys()),
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"📊 Gráfico de barras de {metric_name} guardado: {filepath}")
        return filepath

    def _generate_performance_radar_chart(self, metrics: Dict, title: str = None, filename: str = None) -> str:
        """Genera gráfico radar de rendimiento multi-dimensional."""
        if len(metrics) < 3:
            logger.warning("Se necesitan al menos 3 modelos para gráfico radar")
            return ""

        # Métricas para radar de rendimiento
        radar_metrics = ['avg_latency', 'total_energy_joules', 'efficiency_score', 'rag_accuracy']
        metric_labels = ['Latencia', 'Energía', 'Eficiencia', 'RAG']

        # Normalizar valores (menor es mejor para latencia y energía)
        normalized_data = {}
        for model_name, model_metrics in metrics.items():
            normalized = []
            for metric in radar_metrics:
                value = model_metrics.get(metric, 0)

                if metric in ['avg_latency', 'total_energy_joules']:
                    # Normalizar inversamente (menor = mejor)
                    max_val = max(m.get(metric, 0) for m in metrics.values())
                    if max_val > 0:
                        normalized.append(1 - (value / max_val))
                    else:
                        normalized.append(0.5)
                else:
                    # Normalizar normalmente (mayor = mejor)
                    max_val = max(m.get(metric, 0) for m in metrics.values())
                    if max_val > 0:
                        normalized.append(value / max_val)
                    else:
                        normalized.append(0.5)

            normalized_data[model_name] = normalized

        # Crear radar
        angles = np.linspace(0, 2 * np.pi, len(radar_metrics), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=self.config.figsize, subplot_kw=dict(projection='polar'), dpi=self.config.dpi)

        palette = self.color_palettes[self.config.color_palette]['primary']

        for i, (model_name, values) in enumerate(normalized_data.items()):
            values += values[:1]

            color = self.color_palettes[self.config.color_palette]['highlight'] if self.config.highlight_empoorio and model_name.lower() == 'empoorio' else palette[i % len(palette)]
            ax.plot(angles, values, 'o-', linewidth=3, label=model_name.upper(),
                   color=color, markersize=8)
            ax.fill(angles, values, alpha=0.25, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

        if not title and self.config.auto_generate_titles:
            title = "Rendimiento Multi-dimensional: Eficiencia vs Velocidad"

        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=30)

        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))

        if self.config.include_watermark:
            ax.text(0.02, 0.02, f'{self.config.brand_name} - {self.config.product_name}',
                   transform=ax.transAxes, alpha=0.5, fontsize=10)

        plt.tight_layout()

        if not filename:
            filename = f'performance_radar_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(self.config.output_dir, filename)
        plt.savefig(filepath, dpi=self.config.dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        self.generated_charts.append(ChartMetadata(
            filename=filename,
            title=title or "Radar de Rendimiento",
            chart_type='radar',
            metrics=radar_metrics,
            models=list(metrics.keys()),
            platform_optimized=self.config.target_platform,
            created_at=datetime.now().isoformat()
        ))

        logger.info(f"🎯 Gráfico radar de rendimiento guardado: {filepath}")
        return filepath

    def generate_marketing_chart_suite(self) -> Dict[str, str]:
        """
        Genera una suite completa de gráficos para marketing.

        Returns:
            Dict con rutas de archivos generados
        """
        if not self.comparison_data:
            logger.warning("No hay datos de comparación cargados")
            return {}

        logger.info("🚀 Generando suite completa de gráficos de marketing")

        generated_files = {}

        # Gráfico principal de precisión
        accuracy_chart = self.generate_accuracy_comparison_chart('bar')
        if accuracy_chart:
            generated_files['accuracy_bar'] = accuracy_chart

        # Gráfico de líneas de precisión
        accuracy_line = self.generate_accuracy_comparison_chart('line')
        if accuracy_line:
            generated_files['accuracy_line'] = accuracy_line

        # Gráfico radar de precisión
        accuracy_radar = self.generate_accuracy_comparison_chart('radar')
        if accuracy_radar:
            generated_files['accuracy_radar'] = accuracy_radar

        # Gráficos de rendimiento
        latency_chart = self.generate_performance_comparison_chart('latency', 'bar')
        if latency_chart:
            generated_files['latency_bar'] = latency_chart

        energy_chart = self.generate_performance_comparison_chart('energy', 'bar')
        if energy_chart:
            generated_files['energy_bar'] = energy_chart

        efficiency_chart = self.generate_performance_comparison_chart('efficiency', 'bar')
        if efficiency_chart:
            generated_files['efficiency_bar'] = efficiency_chart

        rag_chart = self.generate_performance_comparison_chart('rag_accuracy', 'bar')
        if rag_chart:
            generated_files['rag_bar'] = rag_chart

        # Gráfico radar de rendimiento
        performance_radar = self.generate_performance_comparison_chart('latency', 'radar')
        if performance_radar:
            generated_files['performance_radar'] = performance_radar

        logger.info(f"✅ Suite de gráficos generada: {len(generated_files)} archivos")
        return generated_files

    def get_chart_metadata(self) -> List[ChartMetadata]:
        """Obtiene metadata de todos los gráficos generados."""
        return self.generated_charts.copy()

    def export_chart_metadata(self, filename: str = None) -> str:
        """Exporta metadata de gráficos a JSON."""
        if not filename:
            filename = f'chart_metadata_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        filepath = os.path.join(self.config.output_dir, filename)

        metadata_dicts = [vars(meta) for meta in self.generated_charts]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata_dicts, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 Metadata de gráficos exportada: {filepath}")
        return filepath


# Funciones de conveniencia
def create_marketing_charts_generator(output_dir: str = './marketing_charts',
                                    platform: str = 'presentation') -> MarketingChartsGenerator:
    """Crea un generador de gráficos de marketing con configuración por defecto."""
    config = MarketingChartConfig(output_dir=output_dir, target_platform=platform)
    generator = MarketingChartsGenerator(config)
    generator.optimize_for_platform(platform)
    return generator


def generate_marketing_charts(comparison_results: Dict[str, Any],
                            output_dir: str = './marketing_charts',
                            platform: str = 'presentation') -> Dict[str, str]:
    """
    Genera gráficos de marketing de manera conveniente.

    Args:
        comparison_results: Resultados del AccuracyComparisonFramework
        output_dir: Directorio de salida
        platform: Plataforma objetivo ('presentation', 'social_media', etc.)

    Returns:
        Dict con rutas de archivos generados
    """
    generator = create_marketing_charts_generator(output_dir, platform)
    generator.load_comparison_data(comparison_results)
    return generator.generate_marketing_chart_suite()


if __name__ == "__main__":
    # Ejemplo de uso
    print("🚀 Marketing Charts Generator para EmpoorioLM")
    print("Genera gráficos profesionales listos para marketing")

    # Crear generador básico
    generator = create_marketing_charts_generator()

    print(f"📊 Configuración: Output dir = {generator.config.output_dir}")
    print("💡 Para usar con datos reales, carga resultados del AccuracyComparisonFramework")
    print("💡 Ejemplo: generator.load_comparison_data(results); generator.generate_marketing_chart_suite()")