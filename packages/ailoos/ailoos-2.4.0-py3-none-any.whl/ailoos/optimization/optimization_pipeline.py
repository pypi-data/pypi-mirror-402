import torch
import torch.nn as nn
from typing import Dict, List, Optional, Union, Callable, Any
import logging
import time
import copy
try:
    from .pruning_engine import PruningEngine
    from .quantization_engine import QuantizationEngine
    from .distillation_engine import DistillationEngine
except ImportError:
    # For standalone testing
    PruningEngine = None
    QuantizationEngine = None
    DistillationEngine = None

logger = logging.getLogger(__name__)

class OptimizationStage:
    """
    Represents a single optimization stage in the pipeline.
    """

    def __init__(self, name: str, technique: str, config: Dict[str, Any]):
        """
        Initialize optimization stage.

        Args:
            name: Stage name
            technique: Optimization technique ('pruning', 'quantization', 'distillation')
            config: Configuration for the technique
        """
        self.name = name
        self.technique = technique
        self.config = config
        self.executed = False
        self.execution_time = 0.0
        self.metrics_before = {}
        self.metrics_after = {}

class OptimizationPipeline:
    """
    Complete pipeline for model optimization combining pruning, quantization, and distillation.
    Supports configurable optimization stages with automatic evaluation.
    """

    def __init__(self, model: nn.Module, evaluator: Optional[Callable] = None):
        """
        Initialize the optimization pipeline.

        Args:
            model: The model to optimize
            evaluator: Optional evaluation function
        """
        self.original_model = model
        self.current_model = copy.deepcopy(model)
        self.stages = []
        self.pipeline_history = []
        self.evaluator = evaluator

    def add_stage(self, name: str, technique: str, config: Dict[str, Any]) -> None:
        """
        Add an optimization stage to the pipeline.

        Args:
            name: Stage name
            technique: Technique ('pruning', 'quantization', 'distillation')
            config: Configuration for the technique
        """
        stage = OptimizationStage(name, technique, config)
        self.stages.append(stage)
        logger.info(f"Added stage '{name}' with technique '{technique}'")

    def insert_stage(self, position: int, name: str, technique: str, config: Dict[str, Any]) -> None:
        """
        Insert an optimization stage at a specific position.

        Args:
            position: Position to insert the stage
            name: Stage name
            technique: Technique
            config: Configuration
        """
        stage = OptimizationStage(name, technique, config)
        self.stages.insert(position, stage)
        logger.info(f"Inserted stage '{name}' at position {position}")

    def remove_stage(self, name: str) -> bool:
        """
        Remove a stage by name.

        Args:
            name: Stage name to remove

        Returns:
            True if stage was removed, False otherwise
        """
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                self.stages.pop(i)
                logger.info(f"Removed stage '{name}'")
                return True
        return False

    def execute_pipeline(self, train_loader: Optional[torch.utils.data.DataLoader] = None,
                        calibration_loader: Optional[torch.utils.data.DataLoader] = None,
                        teacher_model: Optional[nn.Module] = None,
                        device: str = 'cpu') -> nn.Module:
        """
        Execute the complete optimization pipeline.

        Args:
            train_loader: Training data loader (for distillation)
            calibration_loader: Calibration data loader (for quantization)
            teacher_model: Teacher model (for distillation)
            device: Device to run on

        Returns:
            Optimized model
        """
        logger.info(f"Starting optimization pipeline with {len(self.stages)} stages")

        total_start_time = time.time()

        for i, stage in enumerate(self.stages):
            logger.info(f"Executing stage {i+1}/{len(self.stages)}: {stage.name} ({stage.technique})")

            start_time = time.time()

            # Evaluate before optimization
            if self.evaluator:
                stage.metrics_before = self.evaluator(self.current_model)

            # Execute the stage
            self.current_model = self._execute_stage(stage, train_loader, calibration_loader, teacher_model, device)

            stage.execution_time = time.time() - start_time
            stage.executed = True

            # Evaluate after optimization
            if self.evaluator:
                stage.metrics_after = self.evaluator(self.current_model)

            logger.info(f"Stage '{stage.name}' completed in {stage.execution_time:.2f}s")

        total_time = time.time() - total_start_time
        logger.info(f"Pipeline completed in {total_time:.2f}s")

        self.pipeline_history.append({
            'stages': len(self.stages),
            'total_time': total_time,
            'executed_stages': [s.name for s in self.stages if s.executed]
        })

        return self.current_model

    def _execute_stage(self, stage: OptimizationStage,
                      train_loader: Optional[torch.utils.data.DataLoader],
                      calibration_loader: Optional[torch.utils.data.DataLoader],
                      teacher_model: Optional[nn.Module],
                      device: str) -> nn.Module:
        """
        Execute a single optimization stage.

        Args:
            stage: Stage to execute
            train_loader: Training data loader
            calibration_loader: Calibration data loader
            teacher_model: Teacher model
            device: Device

        Returns:
            Optimized model
        """
        if stage.technique == 'pruning':
            return self._execute_pruning(stage, device)
        elif stage.technique == 'quantization':
            return self._execute_quantization(stage, calibration_loader, device)
        elif stage.technique == 'distillation':
            return self._execute_distillation(stage, train_loader, teacher_model, device)
        else:
            raise ValueError(f"Unknown technique: {stage.technique}")

    def _execute_pruning(self, stage: OptimizationStage, device: str) -> nn.Module:
        """
        Execute pruning stage.

        Args:
            stage: Pruning stage
            device: Device

        Returns:
            Pruned model
        """
        engine = PruningEngine(self.current_model)

        method = stage.config.get('method', 'l1_unstructured')
        amount = stage.config.get('amount', 0.2)

        if method in ['l1_unstructured', 'l2_unstructured', 'random_unstructured']:
            self.current_model = engine.magnitude_pruning(amount=amount, method=method)
        elif method == 'structured':
            dim = stage.config.get('dim', 0)
            self.current_model = engine.structured_pruning(amount=amount, dim=dim)
        elif method == 'global':
            self.current_model = engine.global_pruning(amount=amount, method='l1_unstructured')
        elif method == 'iterative':
            initial_amount = stage.config.get('initial_amount', 0.1)
            final_amount = stage.config.get('final_amount', 0.5)
            iterations = stage.config.get('iterations', 5)
            self.current_model = engine.iterative_pruning(
                initial_amount=initial_amount,
                final_amount=final_amount,
                iterations=iterations,
                method='l1_unstructured'
            )

        # Remove pruning reparametrization if specified
        if stage.config.get('remove_pruning', True):
            self.current_model = engine.remove_pruning()

        return self.current_model

    def _execute_quantization(self, stage: OptimizationStage,
                            calibration_loader: Optional[torch.utils.data.DataLoader],
                            device: str) -> nn.Module:
        """
        Execute quantization stage.

        Args:
            stage: Quantization stage
            calibration_loader: Calibration data
            device: Device

        Returns:
            Quantized model
        """
        engine = QuantizationEngine(self.current_model)

        method = stage.config.get('method', 'dynamic')

        if method == 'dynamic':
            dtype = stage.config.get('dtype', torch.qint8)
            self.current_model = engine.dynamic_quantization(dtype=dtype)
        elif method == 'static':
            if calibration_loader is None:
                raise ValueError("Calibration data required for static quantization")
            qconfig_name = stage.config.get('qconfig', 'default')
            self.current_model = engine.static_quantization(
                calibration_data=calibration_loader,
                qconfig_name=qconfig_name
            )
        elif method == 'qat':
            qconfig_name = stage.config.get('qconfig', 'default')
            self.current_model = engine.quantization_aware_training(qconfig_name=qconfig_name)
        elif method == 'fp16':
            self.current_model = engine.fp16_quantization()

        return self.current_model

    def _execute_distillation(self, stage: OptimizationStage,
                            train_loader: Optional[torch.utils.data.DataLoader],
                            teacher_model: Optional[nn.Module],
                            device: str) -> nn.Module:
        """
        Execute distillation stage.

        Args:
            stage: Distillation stage
            train_loader: Training data
            teacher_model: Teacher model
            device: Device

        Returns:
            Distilled model
        """
        if teacher_model is None:
            raise ValueError("Teacher model required for distillation")
        if train_loader is None:
            raise ValueError("Training data required for distillation")

        engine = DistillationEngine(teacher_model, self.current_model)

        method = stage.config.get('method', 'response')
        epochs = stage.config.get('epochs', 10)
        optimizer = stage.config.get('optimizer', torch.optim.Adam(self.current_model.parameters()))

        if method == 'response':
            temperature = stage.config.get('temperature', 2.0)
            alpha = stage.config.get('alpha', 0.5)
            self.current_model = engine.response_distillation(
                train_loader=train_loader,
                optimizer=optimizer,
                epochs=epochs,
                temperature=temperature,
                alpha=alpha,
                device=device
            )
        elif method == 'feature':
            teacher_layers = stage.config.get('teacher_layers', [])
            student_layers = stage.config.get('student_layers', [])
            feature_weight = stage.config.get('feature_weight', 0.5)
            self.current_model = engine.feature_distillation(
                train_loader=train_loader,
                optimizer=optimizer,
                teacher_layers=teacher_layers,
                student_layers=student_layers,
                epochs=epochs,
                feature_weight=feature_weight,
                device=device
            )
        elif method == 'relation':
            relation_weight = stage.config.get('relation_weight', 0.5)
            self.current_model = engine.relation_distillation(
                train_loader=train_loader,
                optimizer=optimizer,
                epochs=epochs,
                relation_weight=relation_weight,
                device=device
            )

        return self.current_model

    def get_pipeline_stats(self) -> Dict:
        """
        Get statistics about the pipeline execution.

        Returns:
            Pipeline statistics
        """
        total_time = sum(stage.execution_time for stage in self.stages)
        executed_stages = [s for s in self.stages if s.executed]

        return {
            'total_stages': len(self.stages),
            'executed_stages': len(executed_stages),
            'total_execution_time': total_time,
            'average_stage_time': total_time / len(executed_stages) if executed_stages else 0,
            'stages': [
                {
                    'name': s.name,
                    'technique': s.technique,
                    'executed': s.executed,
                    'execution_time': s.execution_time,
                    'metrics_before': s.metrics_before,
                    'metrics_after': s.metrics_after
                }
                for s in self.stages
            ],
            'pipeline_history': self.pipeline_history
        }

    def save_pipeline(self, path: str) -> None:
        """
        Save the optimization pipeline configuration and history.

        Args:
            path: Path to save the pipeline
        """
        pipeline_data = {
            'stages': [
                {
                    'name': s.name,
                    'technique': s.technique,
                    'config': s.config,
                    'executed': s.executed,
                    'execution_time': s.execution_time,
                    'metrics_before': s.metrics_before,
                    'metrics_after': s.metrics_after
                }
                for s in self.stages
            ],
            'pipeline_history': self.pipeline_history
        }

        torch.save(pipeline_data, path)
        logger.info(f"Pipeline saved to {path}")

    def load_pipeline(self, path: str) -> None:
        """
        Load a pipeline configuration.

        Args:
            path: Path to load from
        """
        pipeline_data = torch.load(path)

        self.stages = []
        for stage_data in pipeline_data['stages']:
            stage = OptimizationStage(
                stage_data['name'],
                stage_data['technique'],
                stage_data['config']
            )
            stage.executed = stage_data['executed']
            stage.execution_time = stage_data['execution_time']
            stage.metrics_before = stage_data['metrics_before']
            stage.metrics_after = stage_data['metrics_after']
            self.stages.append(stage)

        self.pipeline_history = pipeline_data.get('pipeline_history', [])
        logger.info(f"Pipeline loaded from {path}")

    def reset_pipeline(self) -> None:
        """
        Reset the pipeline to initial state.
        """
        self.current_model = copy.deepcopy(self.original_model)
        for stage in self.stages:
            stage.executed = False
            stage.execution_time = 0.0
            stage.metrics_before = {}
            stage.metrics_after = {}
        self.pipeline_history = []
        logger.info("Pipeline reset to initial state")