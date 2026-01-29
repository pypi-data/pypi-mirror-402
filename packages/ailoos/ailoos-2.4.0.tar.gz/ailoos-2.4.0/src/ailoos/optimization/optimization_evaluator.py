import torch
import torch.nn as nn
import time
import psutil
import os
from typing import Dict, List, Optional, Union, Callable, Any
import logging
import numpy as np

logger = logging.getLogger(__name__)

class OptimizationEvaluator:
    """
    Comprehensive evaluator for model optimization trade-offs.
    Measures accuracy, latency, memory usage, model size, and other metrics.
    """

    def __init__(self, test_loader: torch.utils.data.DataLoader,
                 device: str = 'cpu', num_warmup_runs: int = 5):
        """
        Initialize the evaluator.

        Args:
            test_loader: Test data loader for accuracy evaluation
            device: Device to run evaluations on
            num_warmup_runs: Number of warmup runs for latency measurement
        """
        self.test_loader = test_loader
        self.device = device
        self.num_warmup_runs = num_warmup_runs

    def evaluate_model(self, model: nn.Module, detailed: bool = True) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a model.

        Args:
            model: Model to evaluate
            detailed: Whether to perform detailed evaluation

        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Starting comprehensive model evaluation")

        model.to(self.device).eval()

        metrics = {}

        # Basic metrics
        metrics.update(self._evaluate_accuracy(model))
        metrics.update(self._evaluate_model_size(model))

        if detailed:
            # Performance metrics
            metrics.update(self._evaluate_latency(model))
            metrics.update(self._evaluate_memory_usage(model))
            metrics.update(self._evaluate_throughput(model))

        # Compute derived metrics
        metrics.update(self._compute_derived_metrics(metrics))

        accuracy = metrics.get('accuracy', 'N/A')
        latency = metrics.get('avg_latency_ms', 'N/A')
        size = metrics.get('model_size_mb', 'N/A')

        logger.info(f"Evaluation completed: Accuracy={accuracy}, "
                   f"Latency={latency}ms, "
                   f"Size={size}MB")

        return metrics

    def _evaluate_accuracy(self, model: nn.Module) -> Dict[str, Any]:
        """
        Evaluate model accuracy.

        Args:
            model: Model to evaluate

        Returns:
            Accuracy metrics
        """
        correct = 0
        total = 0
        losses = []

        criterion = nn.CrossEntropyLoss()
        total_loss = 0.0

        with torch.no_grad():
            for inputs, targets in self.test_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = model(inputs)

                loss = criterion(outputs, targets)
                total_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                total += targets.size(0)
                correct += (predicted == targets).sum().item()

        accuracy = 100 * correct / total
        avg_loss = total_loss / len(self.test_loader)

        return {
            'accuracy': accuracy,
            'avg_loss': avg_loss,
            'correct_predictions': correct,
            'total_predictions': total
        }

    def _evaluate_model_size(self, model: nn.Module) -> Dict[str, Any]:
        """
        Evaluate model size and parameter count.

        Args:
            model: Model to evaluate

        Returns:
            Size metrics
        """
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        # Calculate model size in bytes
        param_size = 0
        for param in model.parameters():
            param_size += param.numel() * param.element_size()

        buffer_size = 0
        for buffer in model.buffers():
            buffer_size += buffer.numel() * buffer.element_size()

        total_size_bytes = param_size + buffer_size
        total_size_mb = total_size_bytes / (1024 * 1024)

        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_bytes': total_size_bytes,
            'model_size_mb': total_size_mb,
            'param_size_mb': param_size / (1024 * 1024),
            'buffer_size_mb': buffer_size / (1024 * 1024)
        }

    def _evaluate_latency(self, model: nn.Module) -> Dict[str, Any]:
        """
        Evaluate model inference latency.

        Args:
            model: Model to evaluate

        Returns:
            Latency metrics
        """
        # Get a sample input
        sample_input, _ = next(iter(self.test_loader))
        sample_input = sample_input[:1].to(self.device)  # Use batch size 1

        # Warmup runs
        with torch.no_grad():
            for _ in range(self.num_warmup_runs):
                _ = model(sample_input)

        # Measure latency
        latencies = []
        num_runs = 100

        with torch.no_grad():
            for _ in range(num_runs):
                start_time = time.time()
                _ = model(sample_input)
                if self.device == 'cuda':
                    torch.cuda.synchronize()
                end_time = time.time()
                latencies.append((end_time - start_time) * 1000)  # Convert to ms

        latencies = np.array(latencies)
        avg_latency = np.mean(latencies)
        std_latency = np.std(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)

        return {
            'avg_latency_ms': avg_latency,
            'std_latency_ms': std_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency,
            'p95_latency_ms': p95_latency,
            'p99_latency_ms': p99_latency,
            'num_runs': num_runs
        }

    def _evaluate_memory_usage(self, model: nn.Module) -> Dict[str, Any]:
        """
        Evaluate model memory usage.

        Args:
            model: Model to evaluate

        Returns:
            Memory metrics
        """
        # Get memory before inference
        if self.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
            memory_before = torch.cuda.memory_allocated() / (1024 * 1024)  # MB
        else:
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Perform inference
        sample_input, _ = next(iter(self.test_loader))
        sample_input = sample_input[:1].to(self.device)

        with torch.no_grad():
            _ = model(sample_input)

        # Get memory after inference
        if self.device == 'cuda':
            memory_after = torch.cuda.memory_allocated() / (1024 * 1024)
            peak_memory = torch.cuda.max_memory_allocated() / (1024 * 1024)
        else:
            process = psutil.Process(os.getpid())
            memory_after = process.memory_info().rss / (1024 * 1024)
            peak_memory = memory_after  # Approximation for CPU

        memory_used = memory_after - memory_before

        return {
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_used_mb': memory_used,
            'peak_memory_mb': peak_memory
        }

    def _evaluate_throughput(self, model: nn.Module, batch_sizes: List[int] = [1, 4, 16, 32]) -> Dict[str, Any]:
        """
        Evaluate model throughput for different batch sizes.

        Args:
            model: Model to evaluate
            batch_sizes: List of batch sizes to test

        Returns:
            Throughput metrics
        """
        throughput_results = {}

        for batch_size in batch_sizes:
            try:
                # Create batch input
                sample_input, _ = next(iter(self.test_loader))
                if sample_input.shape[0] >= batch_size:
                    batch_input = sample_input[:batch_size].to(self.device)
                else:
                    # Repeat to make batch
                    repeats = (batch_size + sample_input.shape[0] - 1) // sample_input.shape[0]
                    batch_input = sample_input.repeat(repeats, 1, 1, 1)[:batch_size].to(self.device)

                # Warmup
                with torch.no_grad():
                    for _ in range(self.num_warmup_runs):
                        _ = model(batch_input)

                # Measure throughput
                num_runs = 50
                start_time = time.time()

                with torch.no_grad():
                    for _ in range(num_runs):
                        _ = model(batch_input)
                    if self.device == 'cuda':
                        torch.cuda.synchronize()

                end_time = time.time()
                total_time = end_time - start_time
                total_samples = num_runs * batch_size
                throughput = total_samples / total_time  # samples per second

                throughput_results[f'batch_{batch_size}'] = {
                    'throughput_samples_per_sec': throughput,
                    'latency_per_sample_ms': (total_time / total_samples) * 1000
                }

            except Exception as e:
                logger.warning(f"Failed to evaluate batch size {batch_size}: {e}")
                throughput_results[f'batch_{batch_size}'] = None

        return {'throughput': throughput_results}

    def _compute_derived_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute derived metrics from basic metrics.

        Args:
            metrics: Basic metrics dictionary

        Returns:
            Derived metrics
        """
        derived = {}

        # Efficiency score (accuracy per parameter)
        if 'accuracy' in metrics and 'total_parameters' in metrics:
            derived['accuracy_per_param'] = metrics['accuracy'] / metrics['total_parameters']

        # Efficiency score (accuracy per MB)
        if 'accuracy' in metrics and 'model_size_mb' in metrics:
            derived['accuracy_per_mb'] = metrics['accuracy'] / metrics['model_size_mb']

        # Performance score (throughput per latency)
        if 'throughput' in metrics and 'avg_latency_ms' in metrics:
            batch_1_throughput = metrics['throughput'].get('batch_1', {}).get('throughput_samples_per_sec', 0)
            if batch_1_throughput > 0:
                derived['performance_score'] = batch_1_throughput / metrics['avg_latency_ms']

        # Memory efficiency
        if 'accuracy' in metrics and 'peak_memory_mb' in metrics:
            derived['memory_efficiency'] = metrics['accuracy'] / metrics['peak_memory_mb']

        return derived

    def compare_models(self, models: Dict[str, nn.Module]) -> Dict[str, Any]:
        """
        Compare multiple models.

        Args:
            models: Dictionary of model names to models

        Returns:
            Comparison results
        """
        logger.info(f"Comparing {len(models)} models")

        results = {}
        for name, model in models.items():
            results[name] = self.evaluate_model(model, detailed=True)

        # Add comparison metrics
        comparison = self._create_comparison_table(results)
        results['_comparison'] = comparison

        return results

    def _create_comparison_table(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Create a comparison table from evaluation results.

        Args:
            results: Evaluation results for each model

        Returns:
            Comparison table
        """
        comparison = {}

        # Extract common metrics
        metrics_to_compare = [
            'accuracy', 'model_size_mb', 'avg_latency_ms', 'peak_memory_mb',
            'accuracy_per_param', 'accuracy_per_mb', 'performance_score'
        ]

        for metric in metrics_to_compare:
            comparison[metric] = {}
            values = []
            for model_name, model_results in results.items():
                if model_name.startswith('_'):
                    continue
                value = model_results.get(metric)
                if value is not None:
                    comparison[metric][model_name] = value
                    values.append(value)

            if values:
                comparison[metric]['best'] = max(values) if metric in ['accuracy', 'accuracy_per_param', 'accuracy_per_mb', 'performance_score'] else min(values)
                comparison[metric]['worst'] = min(values) if metric in ['accuracy', 'accuracy_per_param', 'accuracy_per_mb', 'performance_score'] else max(values)

        return comparison

    def save_evaluation_results(self, results: Dict[str, Any], path: str) -> None:
        """
        Save evaluation results to file.

        Args:
            results: Evaluation results
            path: Path to save results
        """
        import json
        with open(path, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            def convert_to_serializable(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.float32) or isinstance(obj, np.float64):
                    return float(obj)
                elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
                    return int(obj)
                elif isinstance(obj, dict):
                    return {k: convert_to_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_serializable(item) for item in obj]
                else:
                    return obj

            json.dump(convert_to_serializable(results), f, indent=2)
        logger.info(f"Evaluation results saved to {path}")

    def load_evaluation_results(self, path: str) -> Dict[str, Any]:
        """
        Load evaluation results from file.

        Args:
            path: Path to load results from

        Returns:
            Evaluation results
        """
        import json
        with open(path, 'r') as f:
            results = json.load(f)
        logger.info(f"Evaluation results loaded from {path}")
        return results