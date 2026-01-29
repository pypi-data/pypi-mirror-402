"""
NIAH Visualizer - Professional Heatmap Generation and Reporting
===============================================================

Advanced visualization system for NIAH benchmark results.
Generates industry-standard heatmaps showing model performance across
context lengths and needle depths.

Features:
- Professional heatmaps (RdYlGn color scheme)
- Statistical analysis and reporting
- Comparative visualizations
- Export to multiple formats (PNG, PDF, HTML)
- Interactive web-based reports
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import statistics

# Optional dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class NIAHVisualizer:
    """
    Professional visualizer for NIAH benchmark results.

    Generates heatmaps, statistical reports, and comparative analyses
    following industry standards used by Google, OpenAI, and Anthropic.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NIAH visualizer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()

        # Set up matplotlib/seaborn style
        plt.style.use('default')
        sns.set_palette("husl")

        # Create output directory
        os.makedirs(self.config['output_dir'], exist_ok=True)

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for visualization."""
        return {
            'output_dir': 'reports/niah',
            'heatmap_cmap': 'RdYlGn',  # Red-Yellow-Green
            'heatmap_figsize': (12, 8),
            'dpi': 300,
            'font_size': 12,
            'title_font_size': 14,
            'enable_interactive': PLOTLY_AVAILABLE,
            'generate_pdf_report': REPORTLAB_AVAILABLE,
            'confidence_intervals': True,
            'statistical_analysis': True
        }

    def generate_heatmap(
        self,
        results: List[Dict[str, Any]],
        model_name: str = "EmpoorioLM",
        save_formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Generate the signature NIAH heatmap visualization.

        Args:
            results: List of result dictionaries with keys:
                    'context_length', 'depth_percent', 'score', 'success'
            model_name: Name of the model being evaluated
            save_formats: List of formats to save ('png', 'pdf', 'html')

        Returns:
            Dictionary mapping format names to file paths
        """
        if save_formats is None:
            save_formats = ['png']

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Ensure we have the required columns
        required_cols = ['context_length', 'depth_percent', 'score']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Results must contain columns: {required_cols}")

        # Create pivot table for heatmap
        pivot_table = df.pivot_table(
            index='depth_percent',
            columns='context_length',
            values='score',
            aggfunc='mean'
        )

        # Sort by depth (0% at top, 100% at bottom)
        pivot_table = pivot_table.sort_index(ascending=True)

        # Generate matplotlib heatmap
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if 'png' in save_formats or 'pdf' in save_formats:
            saved_files.update(self._generate_matplotlib_heatmap(
                pivot_table, model_name, timestamp, save_formats
            ))

        if 'html' in save_formats and PLOTLY_AVAILABLE:
            saved_files.update(self._generate_plotly_heatmap(
                pivot_table, model_name, timestamp
            ))

        # Generate statistical summary
        stats_file = self._generate_statistical_report(df, model_name, timestamp)
        saved_files['stats'] = stats_file

        return saved_files

    def _generate_matplotlib_heatmap(
        self,
        pivot_table: pd.DataFrame,
        model_name: str,
        timestamp: str,
        save_formats: List[str]
    ) -> Dict[str, str]:
        """Generate matplotlib/seaborn heatmap."""
        saved_files = {}

        plt.figure(figsize=self.config['heatmap_figsize'])

        # Create heatmap
        ax = sns.heatmap(
            pivot_table,
            annot=True,
            fmt=".1f",
            cmap=self.config['heatmap_cmap'],
            vmin=0,
            vmax=10,
            cbar_kws={
                'label': 'Retrieval Score (0-10)',
                'shrink': 0.8
            },
            linewidths=0.5,
            linecolor='white'
        )

        # Customize appearance
        plt.title(f"{model_name} - Needle In A Haystack Benchmark\n{timestamp}",
                 fontsize=self.config['title_font_size'], pad=20)
        plt.xlabel("Context Length (Tokens)", fontsize=self.config['font_size'])
        plt.ylabel("Needle Depth (%)", fontsize=self.config['font_size'])

        # Improve tick labels
        ax.set_xticklabels([f"{int(x):,}" for x in pivot_table.columns],
                          rotation=45, ha='right')
        ax.set_yticklabels([f"{int(y)}%" for y in pivot_table.index])

        plt.tight_layout()

        # Save in requested formats
        base_filename = f"{self.config['output_dir']}/niah_heatmap_{timestamp}"

        if 'png' in save_formats:
            png_file = f"{base_filename}.png"
            plt.savefig(png_file, dpi=self.config['dpi'], bbox_inches='tight')
            saved_files['png'] = png_file

        if 'pdf' in save_formats:
            pdf_file = f"{base_filename}.pdf"
            plt.savefig(pdf_file, dpi=self.config['dpi'], bbox_inches='tight')
            saved_files['pdf'] = pdf_file

        plt.close()

        return saved_files

    def _generate_plotly_heatmap(
        self,
        pivot_table: pd.DataFrame,
        model_name: str,
        timestamp: str
    ) -> Dict[str, str]:
        """Generate interactive plotly heatmap."""
        if not PLOTLY_AVAILABLE:
            return {}

        # Create interactive heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=[f"{int(col):,}" for col in pivot_table.columns],
            y=[f"{int(idx)}%" for idx in pivot_table.index],
            colorscale='RdYlGn',
            zmin=0,
            zmax=10,
            hoverongaps=False,
            hovertemplate=
            'Context: %{x} tokens<br>' +
            'Depth: %{y}<br>' +
            'Score: %{z:.1f}<extra></extra>'
        ))

        fig.update_layout(
            title=f"{model_name} - Needle In A Haystack Benchmark<br><sub>{timestamp}</sub>",
            xaxis_title="Context Length (Tokens)",
            yaxis_title="Needle Depth (%)",
            width=1000,
            height=700
        )

        # Save as HTML
        html_file = f"{self.config['output_dir']}/niah_heatmap_{timestamp}_interactive.html"
        fig.write_html(html_file)

        return {'html': html_file}

    def _generate_statistical_report(
        self,
        df: pd.DataFrame,
        model_name: str,
        timestamp: str
    ) -> str:
        """Generate comprehensive statistical report."""
        stats_file = f"{self.config['output_dir']}/niah_stats_{timestamp}.json"

        # Calculate comprehensive statistics
        stats = {
            'model_name': model_name,
            'timestamp': timestamp,
            'total_tests': len(df),
            'overall_metrics': {
                'mean_score': df['score'].mean(),
                'median_score': df['score'].median(),
                'std_dev_score': df['score'].std(),
                'min_score': df['score'].min(),
                'max_score': df['score'].max(),
                'success_rate': (df['score'] >= 9.0).mean(),
                'excellent_rate': (df['score'] >= 9.0).mean(),
                'good_rate': ((df['score'] >= 7.0) & (df['score'] < 9.0)).mean(),
                'fair_rate': ((df['score'] >= 5.0) & (df['score'] < 7.0)).mean(),
                'poor_rate': (df['score'] < 5.0).mean()
            },
            'by_context_length': self._analyze_by_dimension(df, 'context_length'),
            'by_depth': self._analyze_by_dimension(df, 'depth_percent'),
            'correlation_analysis': self._calculate_correlations(df),
            'performance_zones': self._identify_performance_zones(df)
        }

        # Save to JSON
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

        return stats_file

    def _analyze_by_dimension(self, df: pd.DataFrame, dimension: str) -> Dict[str, Any]:
        """Analyze performance by a specific dimension."""
        grouped = df.groupby(dimension)['score'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ])

        result = {}
        for dim_value, metrics in grouped.iterrows():
            result[str(dim_value)] = {
                'count': int(metrics['count']),
                'mean_score': metrics['mean'],
                'median_score': metrics['median'],
                'std_dev': metrics['std'],
                'success_rate': (df[df[dimension] == dim_value]['score'] >= 9.0).mean()
            }

        return result

    def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate correlations between variables."""
        correlations = {}

        try:
            correlations['context_length_vs_score'] = df['context_length'].corr(df['score'])
            correlations['depth_vs_score'] = df['depth_percent'].corr(df['score'])
            correlations['context_length_vs_depth'] = df['context_length'].corr(df['depth_percent'])
        except:
            correlations = {'error': 'Could not calculate correlations'}

        return correlations

    def _identify_performance_zones(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify performance zones and patterns."""
        # Define performance zones
        zones = {
            'perfect_memory': df[df['score'] >= 9.5],  # Near-perfect recall
            'good_memory': df[(df['score'] >= 7.0) & (df['score'] < 9.5)],
            'fair_memory': df[(df['score'] >= 5.0) & (df['score'] < 7.0)],
            'poor_memory': df[df['score'] < 5.0]
        }

        zone_analysis = {}
        for zone_name, zone_data in zones.items():
            if len(zone_data) > 0:
                zone_analysis[zone_name] = {
                    'count': len(zone_data),
                    'percentage': len(zone_data) / len(df) * 100,
                    'avg_score': zone_data['score'].mean(),
                    'context_range': {
                        'min': zone_data['context_length'].min(),
                        'max': zone_data['context_length'].max()
                    },
                    'depth_range': {
                        'min': zone_data['depth_percent'].min(),
                        'max': zone_data['depth_percent'].max()
                    }
                }

        return zone_analysis

    def generate_comparative_analysis(
        self,
        results_list: List[Tuple[str, List[Dict[str, Any]]]],
        save_formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Generate comparative analysis between multiple models/runs.

        Args:
            results_list: List of (model_name, results) tuples
            save_formats: Formats to save

        Returns:
            Dictionary of saved file paths
        """
        if save_formats is None:
            save_formats = ['png']

        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create comparison DataFrame
        comparison_data = []
        for model_name, results in results_list:
            df = pd.DataFrame(results)
            summary = {
                'model': model_name,
                'mean_score': df['score'].mean(),
                'success_rate': (df['score'] >= 9.0).mean(),
                'std_dev': df['score'].std(),
                'perfect_recall_rate': (df['score'] >= 9.5).mean()
            }
            comparison_data.append(summary)

        comparison_df = pd.DataFrame(comparison_data)

        # Generate comparison bar chart
        plt.figure(figsize=(12, 6))

        x = np.arange(len(comparison_df))
        width = 0.35

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Mean score comparison
        bars1 = ax1.bar(x - width/2, comparison_df['mean_score'], width,
                       label='Mean Score', color='skyblue', alpha=0.8)
        ax1.set_ylabel('Mean Retrieval Score (0-10)')
        ax1.set_title('Mean Retrieval Scores')
        ax1.set_xticks(x)
        ax1.set_xticklabels(comparison_df['model'], rotation=45, ha='right')

        # Success rate comparison
        bars2 = ax2.bar(x + width/2, comparison_df['success_rate'] * 100, width,
                       label='Success Rate', color='lightgreen', alpha=0.8)
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_title('Perfect Retrieval Rate (Score ≥ 9.0)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(comparison_df['model'], rotation=45, ha='right')

        plt.suptitle(f'NIAH Benchmark Comparison - {timestamp}', fontsize=14)
        plt.tight_layout()

        # Save comparison chart
        comp_file = f"{self.config['output_dir']}/niah_comparison_{timestamp}.png"
        plt.savefig(comp_file, dpi=self.config['dpi'], bbox_inches='tight')
        saved_files['comparison_png'] = comp_file

        plt.close()

        return saved_files

    def generate_pdf_report(
        self,
        results: List[Dict[str, Any]],
        model_name: str = "EmpoorioLM",
        stats_file: str = None
    ) -> Optional[str]:
        """
        Generate a comprehensive PDF report.

        Args:
            results: Benchmark results
            model_name: Name of the model
            stats_file: Path to statistics JSON file

        Returns:
            Path to generated PDF file or None if not available
        """
        if not REPORTLAB_AVAILABLE:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_file = f"{self.config['output_dir']}/niah_report_{timestamp}.pdf"

        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"{model_name} - NIAH Benchmark Report", title_style))
        story.append(Spacer(1, 12))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 6))

        df = pd.DataFrame(results)
        mean_score = df['score'].mean()
        success_rate = (df['score'] >= 9.0).mean()

        summary_text = f"""
        This report presents the results of the Needle In A Haystack (NIAH) benchmark
        for {model_name}. The benchmark evaluates the model's ability to retrieve specific
        information from documents of varying lengths and needle positions.

        Key Findings:
        • Mean Retrieval Score: {mean_score:.2f}/10.0
        • Perfect Retrieval Rate: {success_rate:.1%}
        • Total Tests Performed: {len(results)}
        • Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Methodology
        story.append(Paragraph("Methodology", styles['Heading2']))
        story.append(Spacer(1, 6))

        methodology_text = """
        The NIAH benchmark tests a model's long-context understanding by:

        1. Generating synthetic documents (haystacks) of varying lengths
        2. Inserting specific facts (needles) at different depths within the documents
        3. Querying the model to retrieve the needle information
        4. Scoring retrieval accuracy on a 0-10 scale

        Higher scores indicate better long-context understanding and retrieval capabilities.
        """

        story.append(Paragraph(methodology_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Try to include heatmap image if available
        heatmap_path = f"{self.config['output_dir']}/niah_heatmap_{timestamp}.png"
        if os.path.exists(heatmap_path):
            story.append(Paragraph("Performance Heatmap", styles['Heading2']))
            story.append(Spacer(1, 6))
            story.append(Image(heatmap_path, width=500, height=350))
            story.append(Spacer(1, 12))

        # Build and save PDF
        doc.build(story)

        return pdf_file

    def create_interactive_dashboard(
        self,
        results: List[Dict[str, Any]],
        model_name: str = "EmpoorioLM"
    ) -> Optional[str]:
        """
        Create an interactive HTML dashboard.

        Args:
            results: Benchmark results
            model_name: Name of the model

        Returns:
            Path to HTML dashboard or None
        """
        if not PLOTLY_AVAILABLE:
            return None

        df = pd.DataFrame(results)

        # Create interactive dashboard with multiple charts
        fig = go.Figure()

        # Add heatmap
        pivot_table = df.pivot_table(
            index='depth_percent',
            columns='context_length',
            values='score',
            aggfunc='mean'
        ).sort_index(ascending=True)

        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=[f"{int(col):,}" for col in pivot_table.columns],
            y=[f"{int(idx)}%" for idx in pivot_table.index],
            colorscale='RdYlGn',
            zmin=0,
            zmax=10,
            name='Retrieval Score'
        )

        fig.add_trace(heatmap)

        # Update layout
        fig.update_layout(
            title=f"{model_name} - NIAH Interactive Dashboard",
            xaxis_title="Context Length (Tokens)",
            yaxis_title="Needle Depth (%)",
            width=1000,
            height=700
        )

        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_file = f"{self.config['output_dir']}/niah_dashboard_{timestamp}.html"
        fig.write_html(dashboard_file)

        return dashboard_file

    def export_results_to_csv(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Export results to CSV format."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"niah_results_{timestamp}.csv"

        filepath = f"{self.config['output_dir']}/{filename}"
        df = pd.DataFrame(results)
        df.to_csv(filepath, index=False)

        return filepath