import torch
import torch.nn as nn
from typing import Dict, List, Optional, Union, Callable, Any, Tuple
import logging
import time
import copy
try:
    from .optimization_pipeline import OptimizationPipeline
    from .optimization_evaluator import OptimizationEvaluator
except ImportError:
    # For standalone testing
    OptimizationPipeline = None
    OptimizationEvaluator = None
import itertools

logger = logging.getLogger(__name__)

class OptimizationConstraint:
    """
    Represents a constraint for optimization scheduling.
    """

    def __init__(self, metric: str, operator: str, value: float, weight: float = 1.0):
        """
        Initialize a constraint.

        Args:
            metric: Metric name (e.g., 'accuracy', 'latency', 'model_size_mb')
            operator: Comparison operator ('>=', '<=', '>', '<', '==')
            value: Target value
            weight: Importance weight for multi-objective optimization
        """
        self.metric = metric
        self.operator = operator
        self.value = value
        self.weight = weight

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Evaluate if metrics satisfy the constraint.

        Args:
            metrics: Evaluation metrics

        Returns:
            (satisfied, distance) - satisfied is True if constraint met,
            distance is the absolute difference from target
        """
        if self.metric not in metrics:
            return False, float('inf')

        actual_value = metrics[self.metric]

        if self.operator == '>=':
            satisfied = actual_value >= self.value
            distance = max(0, self.value - actual_value)
        elif self.operator == '<=':
            satisfied = actual_value <= self.value
            distance = max(0, actual_value - self.value)
        elif self.operator == '>':
            satisfied = actual_value > self.value
            distance = max(0, self.value - actual_value)
        elif self.operator == '<':
            satisfied = actual_value < self.value
            distance = max(0, actual_value - self.value)
        elif self.operator == '==':
            satisfied = abs(actual_value - self.value) < 1e-6
            distance = abs(actual_value - self.value)
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")

        return satisfied, distance

class OptimizationScheduler:
    """
    Automatic scheduler for model optimization that finds optimal configurations
    based on constraints and objectives.
    """

    def __init__(self, model: nn.Module, evaluator: OptimizationEvaluator):
        """
        Initialize the optimization scheduler.

        Args:
            model: Model to optimize
            evaluator: Evaluator for assessing optimization results
        """
        self.model = model
        self.evaluator = evaluator
        self.constraints = []
        self.search_space = {}
        self.best_configurations = []

    def add_constraint(self, metric: str, operator: str, value: float, weight: float = 1.0) -> None:
        """
        Add an optimization constraint.

        Args:
            metric: Metric name
            operator: Comparison operator
            value: Target value
            weight: Constraint weight
        """
        constraint = OptimizationConstraint(metric, operator, value, weight)
        self.constraints.append(constraint)
        logger.info(f"Added constraint: {metric} {operator} {value} (weight={weight})")

    def set_search_space(self, search_space: Dict[str, List[Any]]) -> None:
        """
        Set the search space for optimization parameters.

        Args:
            search_space: Dictionary mapping parameter names to lists of values
        """
        self.search_space = search_space
        logger.info(f"Set search space with {len(search_space)} parameters")

    def default_search_space(self) -> Dict[str, List[Any]]:
        """
        Get a default search space for common optimization techniques.

        Returns:
            Default search space
        """
        return {
            'pruning_method': ['l1_unstructured', 'l2_unstructured'],
            'pruning_amount': [0.1, 0.2, 0.3, 0.4, 0.5],
            'quantization_method': ['dynamic', 'static', 'fp16'],
            'distillation_method': ['response', 'feature'],
            'distillation_epochs': [5, 10, 15],
            'temperature': [1.0, 2.0, 3.0],
            'alpha': [0.3, 0.5, 0.7]
        }

    def grid_search_optimization(self, max_evaluations: int = 50) -> Dict[str, Any]:
        """
        Perform grid search over the search space to find optimal configuration.

        Args:
            max_evaluations: Maximum number of configurations to evaluate

        Returns:
            Best configuration found
        """
        logger.info("Starting grid search optimization")

        if not self.search_space:
            self.search_space = self.default_search_space()

        # Generate all possible combinations
        param_names = list(self.search_space.keys())
        param_values = list(self.search_space.values())
        all_configs = list(itertools.product(*param_values))

        # Limit evaluations
        configs_to_evaluate = all_configs[:max_evaluations]
        logger.info(f"Evaluating {len(configs_to_evaluate)} configurations out of {len(all_configs)}")

        best_score = float('-inf')
        best_config = None
        best_metrics = None

        for i, config_values in enumerate(configs_to_evaluate):
            config = dict(zip(param_names, config_values))
            logger.info(f"Evaluating configuration {i+1}/{len(configs_to_evaluate)}: {config}")

            try:
                # Create pipeline with this configuration
                pipeline = self._create_pipeline_from_config(config)

                # Execute pipeline
                optimized_model = pipeline.execute_pipeline(
                    train_loader=None,  # Would need to be provided
                    calibration_loader=None,
                    teacher_model=None
                )

                # Evaluate
                metrics = self.evaluator.evaluate_model(optimized_model)

                # Score configuration
                score = self._score_configuration(metrics)

                if score > best_score:
                    best_score = score
                    best_config = config
                    best_metrics = metrics

                logger.info(f"Configuration score: {score:.4f}")

            except Exception as e:
                logger.warning(f"Configuration evaluation failed: {e}")
                continue

        result = {
            'best_config': best_config,
            'best_score': best_score,
            'best_metrics': best_metrics,
            'evaluations_performed': len(configs_to_evaluate)
        }

        self.best_configurations.append(result)
        logger.info(f"Grid search completed. Best score: {best_score:.4f}")
        return result

    def bayesian_optimization(self, max_evaluations: int = 20,
                            acquisition_function: str = 'expected_improvement') -> Dict[str, Any]:
        """
        Perform Bayesian optimization to find optimal configuration.

        Args:
            max_evaluations: Maximum number of evaluations
            acquisition_function: Acquisition function for BO

        Returns:
            Best configuration found
        """
        logger.info("Starting Bayesian optimization")

        try:
            from skopt import gp_minimize
            from skopt.space import Real, Integer, Categorical
        except ImportError:
            logger.error("scikit-optimize not installed. Install with: pip install scikit-optimize")
            return self.grid_search_optimization(max_evaluations)

        if not self.search_space:
            self.search_space = self.default_search_space()

        # Convert search space to skopt format
        skopt_space = []
        param_names = []
        param_types = {}

        for param_name, values in self.search_space.items():
            param_names.append(param_name)

            if isinstance(values[0], str):
                skopt_space.append(Categorical(values))
                param_types[param_name] = 'categorical'
            elif isinstance(values[0], int):
                skopt_space.append(Integer(min(values), max(values)))
                param_types[param_name] = 'integer'
            elif isinstance(values[0], float):
                skopt_space.append(Real(min(values), max(values)))
                param_types[param_name] = 'real'

        def objective_function(x):
            # Convert skopt parameters back to config
            config = {}
            for i, param_name in enumerate(param_names):
                if param_types[param_name] == 'categorical':
                    config[param_name] = x[i]
                else:
                    config[param_name] = x[i]

            try:
                pipeline = self._create_pipeline_from_config(config)
                optimized_model = pipeline.execute_pipeline()
                metrics = self.evaluator.evaluate_model(optimized_model)
                score = self._score_configuration(metrics)
                return -score  # Minimize negative score
            except Exception as e:
                logger.warning(f"Configuration evaluation failed: {e}")
                return 1000  # High penalty

        # Run Bayesian optimization
        result = gp_minimize(
            objective_function,
            skopt_space,
            n_calls=max_evaluations,
            n_random_starts=5,
            acq_func=acquisition_function,
            random_state=42
        )

        # Convert best result back to config
        best_config = {}
        for i, param_name in enumerate(param_names):
            if param_types[param_name] == 'categorical':
                best_config[param_name] = result.x[i]
            else:
                best_config[param_name] = result.x[i]

        # Evaluate best configuration
        pipeline = self._create_pipeline_from_config(best_config)
        optimized_model = pipeline.execute_pipeline()
        best_metrics = self.evaluator.evaluate_model(optimized_model)
        best_score = self._score_configuration(best_metrics)

        optimization_result = {
            'best_config': best_config,
            'best_score': best_score,
            'best_metrics': best_metrics,
            'evaluations_performed': max_evaluations,
            'method': 'bayesian'
        }

        self.best_configurations.append(optimization_result)
        logger.info(f"Bayesian optimization completed. Best score: {best_score:.4f}")
        return optimization_result

    def _create_pipeline_from_config(self, config: Dict[str, Any]) -> OptimizationPipeline:
        """
        Create an optimization pipeline from a configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configured pipeline
        """
        pipeline = OptimizationPipeline(self.model, evaluator=self.evaluator.evaluate_model)

        # Add stages based on config
        if 'pruning_method' in config:
            pipeline.add_stage(
                'pruning',
                'pruning',
                {
                    'method': config['pruning_method'],
                    'amount': config.get('pruning_amount', 0.2)
                }
            )

        if 'quantization_method' in config:
            pipeline.add_stage(
                'quantization',
                'quantization',
                {
                    'method': config['quantization_method'],
                    'qconfig': 'default'
                }
            )

        if 'distillation_method' in config:
            pipeline.add_stage(
                'distillation',
                'distillation',
                {
                    'method': config['distillation_method'],
                    'epochs': config.get('distillation_epochs', 10),
                    'temperature': config.get('temperature', 2.0),
                    'alpha': config.get('alpha', 0.5)
                }
            )

        return pipeline

    def _score_configuration(self, metrics: Dict[str, Any]) -> float:
        """
        Score a configuration based on constraints and metrics.

        Args:
            metrics: Evaluation metrics

        Returns:
            Configuration score (higher is better)
        """
        if not self.constraints:
            # Default scoring: balance accuracy and efficiency
            accuracy_score = metrics.get('accuracy', 0) / 100.0
            efficiency_score = 1.0 / (1.0 + metrics.get('avg_latency_ms', 100) / 100.0)
            size_score = 1.0 / (1.0 + metrics.get('model_size_mb', 100) / 100.0)
            return (accuracy_score + efficiency_score + size_score) / 3.0

        # Constraint-based scoring
        total_score = 0.0
        total_weight = 0.0

        for constraint in self.constraints:
            satisfied, distance = constraint.evaluate(metrics)

            if satisfied:
                score = 1.0 / (1.0 + distance)  # Higher score for closer to target
            else:
                score = 0.0  # Penalty for not satisfying constraint

            total_score += score * constraint.weight
            total_weight += constraint.weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def find_pareto_optimal_configs(self, configurations: List[Dict[str, Any]],
                                  metrics_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find Pareto-optimal configurations for multi-objective optimization.

        Args:
            configurations: List of configurations
            metrics_list: Corresponding metrics

        Returns:
            Pareto-optimal configurations
        """
        if len(configurations) != len(metrics_list):
            raise ValueError("Configurations and metrics lists must have same length")

        pareto_configs = []

        for i, (config, metrics) in enumerate(zip(configurations, metrics_list)):
            is_pareto = True

            for j, (other_config, other_metrics) in enumerate(zip(configurations, metrics_list)):
                if i == j:
                    continue

                # Check if other configuration dominates this one
                dominates = True
                for constraint in self.constraints:
                    if constraint.metric in metrics and constraint.metric in other_metrics:
                        self_val = metrics[constraint.metric]
                        other_val = other_metrics[constraint.metric]

                        if constraint.operator in ['>=', '>']:
                            # Higher is better
                            if other_val > self_val:
                                dominates = False
                                break
                        elif constraint.operator in ['<=', '<']:
                            # Lower is better
                            if other_val < self_val:
                                dominates = False
                                break

                if dominates:
                    is_pareto = False
                    break

            if is_pareto:
                pareto_configs.append({
                    'config': config,
                    'metrics': metrics
                })

        logger.info(f"Found {len(pareto_configs)} Pareto-optimal configurations")
        return pareto_configs

    def schedule_optimization(self, method: str = 'grid', max_evaluations: int = 50,
                            time_budget: Optional[float] = None) -> Dict[str, Any]:
        """
        Schedule and execute optimization.

        Args:
            method: Optimization method ('grid', 'bayesian', 'random')
            max_evaluations: Maximum evaluations
            time_budget: Time budget in seconds

        Returns:
            Optimization results
        """
        start_time = time.time()

        if method == 'grid':
            result = self.grid_search_optimization(max_evaluations)
        elif method == 'bayesian':
            result = self.bayesian_optimization(max_evaluations)
        elif method == 'random':
            result = self.random_search_optimization(max_evaluations)
        else:
            raise ValueError(f"Unsupported optimization method: {method}")

        execution_time = time.time() - start_time
        result['execution_time'] = execution_time
        result['method'] = method

        logger.info(f"Optimization completed in {execution_time:.2f}s using {method} method")
        return result

    def random_search_optimization(self, max_evaluations: int = 50) -> Dict[str, Any]:
        """
        Perform random search over the search space.

        Args:
            max_evaluations: Maximum number of evaluations

        Returns:
            Best configuration found
        """
        logger.info("Starting random search optimization")

        import random

        if not self.search_space:
            self.search_space = self.default_search_space()

        param_names = list(self.search_space.keys())
        param_values = list(self.search_space.values())

        best_score = float('-inf')
        best_config = None
        best_metrics = None

        for i in range(max_evaluations):
            # Sample random configuration
            config = {}
            for name, values in self.search_space.items():
                config[name] = random.choice(values)

            logger.info(f"Evaluating random configuration {i+1}/{max_evaluations}: {config}")

            try:
                pipeline = self._create_pipeline_from_config(config)
                optimized_model = pipeline.execute_pipeline()
                metrics = self.evaluator.evaluate_model(optimized_model)
                score = self._score_configuration(metrics)

                if score > best_score:
                    best_score = score
                    best_config = config
                    best_metrics = metrics

                logger.info(f"Configuration score: {score:.4f}")

            except Exception as e:
                logger.warning(f"Configuration evaluation failed: {e}")
                continue

        result = {
            'best_config': best_config,
            'best_score': best_score,
            'best_metrics': best_metrics,
            'evaluations_performed': max_evaluations,
            'method': 'random'
        }

        self.best_configurations.append(result)
        logger.info(f"Random search completed. Best score: {best_score:.4f}")
        return result

    def save_scheduler_state(self, path: str) -> None:
        """
        Save scheduler state to file.

        Args:
            path: Path to save state
        """
        state = {
            'constraints': [
                {
                    'metric': c.metric,
                    'operator': c.operator,
                    'value': c.value,
                    'weight': c.weight
                }
                for c in self.constraints
            ],
            'search_space': self.search_space,
            'best_configurations': self.best_configurations
        }

        torch.save(state, path)
        logger.info(f"Scheduler state saved to {path}")

    def load_scheduler_state(self, path: str) -> None:
        """
        Load scheduler state from file.

        Args:
            path: Path to load state from
        """
        state = torch.load(path)

        self.constraints = [
            OptimizationConstraint(c['metric'], c['operator'], c['value'], c['weight'])
            for c in state['constraints']
        ]

        self.search_space = state['search_space']
        self.best_configurations = state.get('best_configurations', [])

        logger.info(f"Scheduler state loaded from {path}")