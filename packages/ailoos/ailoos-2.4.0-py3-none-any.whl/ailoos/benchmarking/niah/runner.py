"""
NIAH Runner - Professional Benchmark Orchestration
==================================================

Complete orchestration system for running NIAH benchmarks.
Combines generator, evaluator, and visualizer into a seamless
benchmarking pipeline following industry standards.

Features:
- Automated benchmark execution
- Progress tracking and logging
- Comprehensive result analysis
- Multiple output formats
- Comparative analysis capabilities
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json
import os

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from tqdm import tqdm
from .generator import NIAHGenerator
from .evaluator import NIAHEvaluator, EvaluationResult
from .visualizer import NIAHVisualizer

logger = logging.getLogger(__name__)


class NIAHBenchmark:
    """
    Professional NIAH benchmark orchestrator.

    Runs complete benchmarking campaigns with industry-standard methodology,
    combining generation, evaluation, and visualization into a seamless pipeline.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NIAH benchmark orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()

        # Initialize components
        self.generator = NIAHGenerator(config=self.config.get('generator', {}))
        self.evaluator = NIAHEvaluator(config=self.config.get('evaluator', {}))
        self.visualizer = NIAHVisualizer(config=self.config.get('visualizer', {}))

        # Benchmark state
        self.current_results: List[Dict[str, Any]] = []
        self.benchmark_metadata: Dict[str, Any] = {}

        logger.info("🏃 NIAH Benchmark orchestrator initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the benchmark."""
        return {
            'generator': {
                'filler_complexity': 'medium',
                'domain_mixing': True
            },
            'evaluator': {
                'exact_match_threshold': 0.95,
                'fuzzy_match_threshold': 0.7,
                'enable_confidence_estimation': True
            },
            'visualizer': {
                'output_dir': 'reports/niah',
                'heatmap_cmap': 'RdYlGn',
                'enable_interactive': True
            },
            'benchmark': {
                'max_concurrent_tests': 4,
                'progress_tracking': True,
                'save_intermediate_results': True,
                'timeout_per_test': 30,  # seconds
                'retry_failed_tests': True,
                'max_retries': 2
            }
        }

    async def run_comprehensive_benchmark(
        self,
        model,
        context_lengths: List[int] = None,
        depths: List[float] = None,
        domains: List[str] = None,
        needle_types: List[str] = None,
        num_tests_per_config: int = 1
    ) -> Dict[str, Any]:
        """
        Run a comprehensive NIAH benchmark.

        Args:
            model: The model to benchmark (must have generate method)
            context_lengths: List of context lengths to test
            depths: List of needle depths (0.0-1.0)
            domains: List of content domains
            needle_types: List of needle types
            num_tests_per_config: Number of tests per configuration

        Returns:
            Complete benchmark results and metadata
        """
        if context_lengths is None:
            context_lengths = [1024, 2048, 4096, 8192]

        if depths is None:
            depths = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        if domains is None:
            domains = ['technical', 'business', 'academic']

        if needle_types is None:
            needle_types = ['fact']

        # Initialize benchmark metadata
        self.benchmark_metadata = {
            'start_time': datetime.now().isoformat(),
            'model_name': getattr(model, '__name__', str(type(model).__name__)),
            'config': {
                'context_lengths': context_lengths,
                'depths': depths,
                'domains': domains,
                'needle_types': needle_types,
                'num_tests_per_config': num_tests_per_config
            },
            'total_tests': len(context_lengths) * len(depths) * len(domains) * len(needle_types) * num_tests_per_config
        }

        logger.info("🚀 Starting comprehensive NIAH benchmark")
        logger.info(f"📊 Total tests: {self.benchmark_metadata['total_tests']}")
        logger.info(f"📏 Context lengths: {context_lengths}")
        logger.info(f"📍 Depths: {[f'{d:.1f}' for d in depths]}")
        logger.info(f"🏷️  Domains: {domains}")

        # Reset results
        self.current_results = []

        # Create test configurations
        test_configs = self._generate_test_configs(
            context_lengths, depths, domains, needle_types, num_tests_per_config
        )

        # Run benchmark
        results = await self._execute_benchmark(model, test_configs)

        # Complete metadata
        self.benchmark_metadata.update({
            'end_time': datetime.now().isoformat(),
            'actual_tests_run': len(results),
            'duration_seconds': (datetime.now() - datetime.fromisoformat(self.benchmark_metadata['start_time'])).total_seconds()
        })

        # Generate analysis and visualizations
        analysis = await self._generate_analysis_and_visualizations(results)

        # Compile final report
        final_report = {
            'metadata': self.benchmark_metadata,
            'results': results,
            'analysis': analysis,
            'recommendations': self._generate_recommendations(results)
        }

        logger.info("✅ Comprehensive NIAH benchmark completed")
        logger.info(f"📈 Overall success rate: {analysis['overall_metrics']['success_rate']:.1%}")

        return final_report

    def _generate_test_configs(
        self,
        context_lengths: List[int],
        depths: List[float],
        domains: List[str],
        needle_types: List[str],
        num_tests_per_config: int
    ) -> List[Dict[str, Any]]:
        """Generate all test configurations."""
        configs = []

        for context_len in context_lengths:
            for depth in depths:
                for domain in domains:
                    for needle_type in needle_types:
                        for test_idx in range(num_tests_per_config):
                            config = {
                                'context_length': context_len,
                                'depth_percent': depth * 100,  # Convert to percentage for display
                                'depth': depth,  # Keep as fraction for processing
                                'domain': domain,
                                'needle_type': needle_type,
                                'test_id': f"{context_len}_{int(depth*100)}_{domain}_{needle_type}_{test_idx}",
                                'seed': hash(f"{context_len}_{depth}_{domain}_{needle_type}_{test_idx}") % 2**32
                            }
                            configs.append(config)

        return configs

    async def _execute_benchmark(
        self,
        model,
        test_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute the benchmark with progress tracking."""
        results = []

        if self.config['benchmark']['progress_tracking']:
            pbar = tqdm(total=len(test_configs), desc="Running NIAH Tests")

        # Use thread pool for concurrent execution
        max_concurrent = self.config['benchmark']['max_concurrent_tests']

        for i in range(0, len(test_configs), max_concurrent):
            batch_configs = test_configs[i:i + max_concurrent]
            batch_results = await self._execute_batch(model, batch_configs)

            results.extend(batch_results)

            if self.config['benchmark']['progress_tracking']:
                pbar.update(len(batch_configs))

            # Save intermediate results if requested
            if self.config['benchmark']['save_intermediate_results']:
                self._save_intermediate_results(results)

        if self.config['benchmark']['progress_tracking']:
            pbar.close()

        return results

    async def _execute_batch(self, model, batch_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a batch of tests concurrently."""
        tasks = []

        for config in batch_configs:
            task = self._execute_single_test(model, config)
            tasks.append(task)

        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Test {batch_configs[i]['test_id']} failed: {result}")
                # Create failure result
                failure_result = batch_configs[i].copy()
                failure_result.update({
                    'success': False,
                    'score': 0.0,
                    'error': str(result),
                    'response': '',
                    'expected': '',
                    'retrieval_time': 0.0
                })
                processed_results.append(failure_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_single_test(self, model, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single NIAH test."""
        try:
            start_time = time.time()

            # Generate test case
            context, question, expected, needle_spec = self.generator.generate_test_case(
                context_length=config['context_length'],
                depth_percent=config['depth'],
                domain=config['domain'],
                needle_type=config['needle_type']
            )

            # Execute model inference
            prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer the question directly using the context above.\nAnswer:"

            response = await self._safe_model_generate(model, prompt)

            # Evaluate response
            evaluation = self.evaluator.evaluate_response(
                model_response=response,
                expected_answer=expected,
                needle_type=config['needle_type']
            )

            retrieval_time = time.time() - start_time

            # Compile result
            result = config.copy()
            result.update({
                'success': evaluation.success,
                'score': evaluation.score,
                'response': response,
                'expected': expected,
                'retrieval_time': retrieval_time,
                'confidence': evaluation.confidence,
                'evaluation_details': evaluation.evaluation_details,
                'needle_content': needle_spec.content if needle_spec else None
            })

            return result

        except Exception as e:
            logger.error(f"❌ Error in test {config['test_id']}: {e}")
            result = config.copy()
            result.update({
                'success': False,
                'score': 0.0,
                'error': str(e),
                'response': '',
                'expected': '',
                'retrieval_time': time.time() - start_time if 'start_time' in locals() else 0.0
            })
            return result

    async def _safe_model_generate(self, model, prompt: str) -> str:
        """Safely generate response from model with timeout."""
        try:
            # Try different model interfaces
            if hasattr(model, 'generate_with_thinking'):
                # AILOOS reasoning generator
                result = await model.generate_with_thinking(
                    request=type('Request', (), {'prompt': prompt, 'max_tokens': 100})()
                )
                return result.response.text

            elif hasattr(model, 'generate'):
                # Standard model interface
                if asyncio.iscoroutinefunction(model.generate):
                    response = await asyncio.wait_for(
                        model.generate(prompt, max_new_tokens=100, temperature=0.1, do_sample=False),
                        timeout=self.config['benchmark']['timeout_per_test']
                    )
                else:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: model.generate(prompt, max_new_tokens=100, temperature=0.1, do_sample=False)
                    )

                # Extract text from response
                if hasattr(response, 'text'):
                    return response.text
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)

            else:
                raise AttributeError("Model must have 'generate' or 'generate_with_thinking' method")

        except asyncio.TimeoutError:
            logger.warning(f"⏰ Model generation timed out after {self.config['benchmark']['timeout_per_test']}s")
            return "[TIMEOUT]"
        except Exception as e:
            logger.error(f"❌ Model generation error: {e}")
            return "[ERROR]"

    async def _generate_analysis_and_visualizations(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analysis and visualizations."""
        logger.info("📊 Generating analysis and visualizations...")

        # Generate heatmap
        heatmap_files = self.visualizer.generate_heatmap(
            results=results,
            model_name=self.benchmark_metadata['model_name'],
            save_formats=['png', 'pdf', 'html']
        )

        # Calculate statistical analysis
        analysis = self._calculate_detailed_analysis(results)

        # Generate comparative analysis if we have baseline data
        comparison_files = {}
        if self._has_baseline_data():
            comparison_files = self.visualizer.generate_comparative_analysis([
                (self.benchmark_metadata['model_name'], results),
                ("Baseline Model", self._get_baseline_results())
            ])

        # Generate PDF report
        pdf_report = self.visualizer.generate_pdf_report(
            results=results,
            model_name=self.benchmark_metadata['model_name']
        )

        return {
            'heatmap_files': heatmap_files,
            'comparison_files': comparison_files,
            'pdf_report': pdf_report,
            'statistical_analysis': analysis
        }

    def _calculate_detailed_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed statistical analysis."""
        if not PANDAS_AVAILABLE:
            return self._calculate_basic_analysis(results)

        df = pd.DataFrame(results)

        analysis = {
            'overall_metrics': {
                'total_tests': len(results),
                'success_rate': (df['score'] >= 9.0).mean(),
                'mean_score': df['score'].mean(),
                'median_score': df['score'].median(),
                'std_dev_score': df['score'].std(),
                'min_score': df['score'].min(),
                'max_score': df['score'].max(),
                'mean_retrieval_time': df['retrieval_time'].mean()
            },
            'performance_by_context': self._analyze_by_group(df, 'context_length'),
            'performance_by_depth': self._analyze_by_group(df, 'depth_percent'),
            'performance_by_domain': self._analyze_by_group(df, 'domain'),
            'performance_by_needle_type': self._analyze_by_group(df, 'needle_type'),
            'correlation_analysis': self._calculate_result_correlations(df)
        }

        return analysis

    def _analyze_by_group(self, df, group_column: str) -> Dict[str, Any]:
        """Analyze performance grouped by a specific column."""
        grouped = df.groupby(group_column)['score'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ])

        result = {}
        for group_value, metrics in grouped.iterrows():
            success_rate = (df[df[group_column] == group_value]['score'] >= 9.0).mean()
            result[str(group_value)] = {
                'count': int(metrics['count']),
                'mean_score': metrics['mean'],
                'median_score': metrics['median'],
                'std_dev': metrics['std'] if not (pd and pd.isna(metrics['std'])) else 0.0,
                'success_rate': success_rate,
                'perfect_recall_rate': (df[df[group_column] == group_value]['score'] >= 9.5).mean()
            }

        return result

    def _calculate_result_correlations(self, df) -> Dict[str, float]:
        """Calculate correlations between test parameters and scores."""
        correlations = {}

        try:
            correlations['context_length_vs_score'] = df['context_length'].corr(df['score'])
            correlations['depth_vs_score'] = df['depth_percent'].corr(df['score'])
            correlations['retrieval_time_vs_score'] = df['retrieval_time'].corr(df['score'])
        except Exception as e:
            logger.warning(f"Could not calculate correlations: {e}")
            correlations = {'error': str(e)}

        return correlations

    def _calculate_basic_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistical analysis without pandas."""
        if not results:
            return {'error': 'No results to analyze'}

        # Basic statistics
        scores = [r.get('score', 0) for r in results]
        success_count = sum(1 for r in results if r.get('success', False))

        analysis = {
            'overall_metrics': {
                'total_tests': len(results),
                'success_rate': success_count / len(results) if results else 0,
                'mean_score': statistics.mean(scores) if scores else 0,
                'median_score': statistics.median(scores) if scores else 0,
                'std_dev_score': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0
            },
            'performance_by_context': {},
            'performance_by_depth': {},
            'performance_by_domain': {},
            'performance_by_needle_type': {},
            'correlation_analysis': {'basic_analysis_only': True}
        }

        # Group by context length
        context_groups = {}
        for r in results:
            ctx = r.get('context_length', 'unknown')
            if ctx not in context_groups:
                context_groups[ctx] = []
            context_groups[ctx].append(r.get('score', 0))

        for ctx, scores_list in context_groups.items():
            success_rate = sum(1 for s in scores_list if s >= 9.0) / len(scores_list)
            analysis['performance_by_context'][str(ctx)] = {
                'count': len(scores_list),
                'mean_score': statistics.mean(scores_list),
                'success_rate': success_rate
            }

        return analysis

    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on benchmark results."""
        recommendations = []

        # Analyze results to generate insights
        df = pd.DataFrame(results)
        success_rate = (df['score'] >= 9.0).mean()
        mean_score = df['score'].mean()

        if success_rate > 0.9:
            recommendations.append("🎉 Excellent performance! The model demonstrates near-perfect long context understanding.")
        elif success_rate > 0.7:
            recommendations.append("✅ Good performance with room for improvement in deeper contexts.")
        else:
            recommendations.append("⚠️ Performance needs improvement, especially for longer contexts and deeper needle positions.")

        # Context length analysis
        context_analysis = self._analyze_by_group(df, 'context_length')
        max_context = max([int(k) for k in context_analysis.keys()])
        max_success = max([v['success_rate'] for v in context_analysis.values()])

        if max_success < 0.8:
            recommendations.append(f"📏 Consider optimizing attention mechanisms for contexts longer than {max_context} tokens.")
        else:
            recommendations.append(f"🚀 Model scales well to {max_context}+ tokens with high accuracy.")

        # Depth analysis
        depth_analysis = self._analyze_by_group(df, 'depth_percent')
        deep_positions = [k for k, v in depth_analysis.items() if float(k) > 50]
        if deep_positions:
            deep_success = statistics.mean([depth_analysis[k]['success_rate'] for k in deep_positions if k in depth_analysis])
            if deep_success < 0.7:
                recommendations.append("📍 Improve retrieval accuracy for information positioned deeply in long contexts.")

        return recommendations

    def _save_intermediate_results(self, results: List[Dict[str, Any]]):
        """Save intermediate results for recovery."""
        if not results:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        intermediate_file = f"{self.visualizer.config['output_dir']}/intermediate_results_{timestamp}.json"

        with open(intermediate_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results_count': len(results),
                'results': results[-100:]  # Save last 100 results
            }, f, indent=2, default=str)

    def _has_baseline_data(self) -> bool:
        """Check if baseline comparison data is available."""
        # This would check for stored baseline results
        return False

    def _get_baseline_results(self) -> List[Dict[str, Any]]:
        """Get baseline results for comparison."""
        # This would load stored baseline results
        return []

    def export_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Export complete benchmark results to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"niah_benchmark_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📊 Results exported to {output_file}")
        return output_file


# Convenience functions
async def run_niah_benchmark(
    model,
    context_lengths: List[int] = None,
    depths: List[float] = None,
    domains: List[str] = None,
    needle_types: List[str] = None,
    output_dir: str = "reports/niah"
) -> Dict[str, Any]:
    """
    Convenience function to run a complete NIAH benchmark.

    Args:
        model: The model to benchmark
        context_lengths: Context lengths to test
        depths: Needle depths to test (0.0-1.0)
        domains: Content domains to test
        needle_types: Types of needles to test
        output_dir: Output directory for results

    Returns:
        Complete benchmark results
    """
    config = {
        'visualizer': {'output_dir': output_dir}
    }

    benchmark = NIAHBenchmark(config=config)

    results = await benchmark.run_comprehensive_benchmark(
        model=model,
        context_lengths=context_lengths,
        depths=depths,
        domains=domains,
        needle_types=needle_types
    )

    # Export results
    benchmark.export_results(results)

    return results