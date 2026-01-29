#!/usr/bin/env python3
"""
EmpoorioLM Curriculum Learning System
Progressive training from Baby Titan → 7B with knowledge transfer
"""

import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import time
from copy import deepcopy

from ..models.empoorio_lm import (
    create_empoorio_baby_titan,
    create_empoorio_titan,
    create_empoorio_7b,
    EmpoorioForCausalLM,
    EmpoorioBPETokenizer
)
from ..utils.logging import AiloosLogger
from .data_loader import EmpoorioDataLoader, create_data_loader_config


@dataclass
class CurriculumStage:
    """Configuration for a curriculum learning stage."""
    name: str
    model_factory: callable
    epochs: int
    learning_rate: float
    batch_size: int
    max_seq_length: int
    data_complexity: str  # "simple", "medium", "complex"
    distillation_weight: float = 0.0  # Weight for knowledge distillation


@dataclass
class CurriculumConfig:
    """Configuration for curriculum learning."""
    stages: List[CurriculumStage]
    output_dir: str = "./curriculum_checkpoints"
    save_every_stage: bool = True
    use_distillation: bool = True
    distillation_temperature: float = 2.0
    device: str = "auto"


class CurriculumLearningManager:
    """
    Manages progressive training from small to large models.
    Implements curriculum learning with knowledge transfer.
    """

    def __init__(self, config: CurriculumConfig):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Setup device
        self.device = self._setup_device()

        # Training state
        self.current_stage_idx = 0
        self.models = {}
        self.optimizers = {}
        self.schedulers = {}
        self.best_losses = {}

        # Create output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_device(self) -> torch.device:
        """Setup training device."""
        if self.config.device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            return torch.device(self.config.device)

    def _get_stage_model(self, stage: CurriculumStage) -> EmpoorioForCausalLM:
        """Get or create model for a stage."""
        if stage.name not in self.models:
            self.logger.info(f"🧠 Creating {stage.name} model...")
            model = stage.model_factory()
            model.to(self.device)
            self.models[stage.name] = model
        return self.models[stage.name]

    def _initialize_model_weights(self, model: EmpoorioForCausalLM, teacher_model: Optional[EmpoorioForCausalLM] = None):
        """Initialize model weights, optionally from teacher."""
        if teacher_model is not None and self.config.use_distillation:
            self._distill_knowledge(teacher_model, model)
        else:
            # Standard initialization
            model.apply(model._init_weights)

    def _distill_knowledge(self, teacher: EmpoorioForCausalLM, student: EmpoorioForCausalLM):
        """Transfer knowledge from teacher to student model."""
        self.logger.info("🎓 Distilling knowledge from teacher to student...")

        teacher.eval()
        student.train()

        # For now, implement simple weight copying where dimensions match
        # In a full implementation, this would include proper distillation techniques
        teacher_state = teacher.state_dict()
        student_state = student.state_dict()

        # Copy matching layers
        for name, param in student_state.items():
            if name in teacher_state:
                teacher_param = teacher_state[name]
                if param.shape == teacher_param.shape:
                    param.data.copy_(teacher_param.data)
                    self.logger.debug(f"Copied weights for {name}")
                else:
                    self.logger.debug(f"Shape mismatch for {name}: {param.shape} vs {teacher_param.shape}")

        self.logger.info("✅ Knowledge distillation completed")

    def _create_data_loader(self, stage: CurriculumStage, tokenizer: EmpoorioBPETokenizer) -> torch.utils.data.DataLoader:
        """Create data loader for the current stage."""
        # Adjust data complexity based on stage
        if stage.data_complexity == "simple":
            # Use simpler, shorter sequences
            max_seq = min(stage.max_seq_length, 512)
            batch_size = stage.batch_size
        elif stage.data_complexity == "medium":
            max_seq = min(stage.max_seq_length, 2048)
            batch_size = max(1, stage.batch_size // 2)
        else:  # complex
            max_seq = stage.max_seq_length
            batch_size = max(1, stage.batch_size // 4)

        # Create sample data paths (in production, these would be real datasets)
        data_paths = self._get_data_paths_for_complexity(stage.data_complexity)

        config = create_data_loader_config(
            text_paths=data_paths,
            batch_size=batch_size,
            max_seq_length=max_seq
        )

        data_loader = EmpoorioDataLoader(config)
        data_loader.setup_tokenizer(tokenizer)
        return data_loader.create_text_dataloader()

    def _get_data_paths_for_complexity(self, complexity: str) -> List[str]:
        """Get data paths based on complexity level."""
        # This is a simplified version - in production, you'd have different datasets
        base_path = "/tmp/curriculum_data"

        if complexity == "simple":
            # Short, simple sentences
            return [f"{base_path}/simple_texts.jsonl"]
        elif complexity == "medium":
            # Medium complexity texts
            return [f"{base_path}/medium_texts.jsonl"]
        else:  # complex
            # Full complexity texts
            return [f"{base_path}/complex_texts.jsonl"]

    def _setup_optimizer(self, model: nn.Module, stage: CurriculumStage):
        """Setup optimizer for a stage."""
        return torch.optim.AdamW(
            model.parameters(),
            lr=stage.learning_rate,
            weight_decay=0.01,
            betas=(0.9, 0.999)
        )

    def _train_stage(self, stage: CurriculumStage, tokenizer: EmpoorioBPETokenizer) -> float:
        """Train a single curriculum stage."""
        self.logger.info(f"🚀 Training stage: {stage.name}")
        self.logger.info(f"📊 Epochs: {stage.epochs}, LR: {stage.learning_rate}, Batch size: {stage.batch_size}")

        # Get/create model
        model = self._get_stage_model(stage)

        # Initialize weights (with knowledge transfer if available)
        teacher_model = None
        if self.current_stage_idx > 0:
            prev_stage = self.config.stages[self.current_stage_idx - 1]
            teacher_model = self.models.get(prev_stage.name)

        self._initialize_model_weights(model, teacher_model)

        # Setup data and optimizer
        dataloader = self._create_data_loader(stage, tokenizer)
        optimizer = self._setup_optimizer(model, stage)

        # Training loop
        model.train()
        best_loss = float('inf')

        for epoch in range(stage.epochs):
            self.logger.info(f"🎯 Epoch {epoch + 1}/{stage.epochs}")

            epoch_loss = self._train_epoch(model, dataloader, optimizer, stage, teacher_model)

            self.logger.info(f"✅ Epoch {epoch + 1} completed. Loss: {epoch_loss:.4f}")

            if epoch_loss < best_loss:
                best_loss = epoch_loss
                self._save_checkpoint(model, optimizer, stage, epoch, epoch_loss, is_best=True)

        return best_loss

    def _train_epoch(self, model: nn.Module, dataloader: torch.utils.data.DataLoader,
                    optimizer: torch.optim.Optimizer, stage: CurriculumStage,
                    teacher_model: Optional[nn.Module] = None) -> float:
        """Train for one epoch."""
        total_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(dataloader):
            # Move batch to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs['loss']

            # Add distillation loss if teacher available
            if teacher_model is not None and stage.distillation_weight > 0:
                with torch.no_grad():
                    teacher_outputs = teacher_model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                distillation_loss = self._compute_distillation_loss(
                    outputs['logits'], teacher_outputs['logits'], labels, stage.distillation_weight
                )
                loss = (1 - stage.distillation_weight) * loss + stage.distillation_weight * distillation_loss

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 10 == 0:
                self.logger.info(f"📈 Batch {batch_idx}: Loss = {loss.item():.4f}")

        return total_loss / num_batches

    def _compute_distillation_loss(self, student_logits: torch.Tensor, teacher_logits: torch.Tensor,
                                 labels: torch.Tensor, weight: float) -> torch.Tensor:
        """Compute knowledge distillation loss."""
        # Simple distillation using KL divergence
        teacher_probs = torch.softmax(teacher_logits / self.config.distillation_temperature, dim=-1)
        student_log_probs = torch.log_softmax(student_logits / self.config.distillation_temperature, dim=-1)

        distillation_loss = torch.nn.functional.kl_div(
            student_log_probs, teacher_probs, reduction='batchmean'
        ) * (self.config.distillation_temperature ** 2)

        return distillation_loss

    def _save_checkpoint(self, model: nn.Module, optimizer: torch.optim.Optimizer,
                        stage: CurriculumStage, epoch: int, loss: float, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'stage': stage.name,
            'epoch': epoch,
            'loss': loss,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'config': self.config.__dict__,
        }

        if is_best:
            filename = f"{stage.name}_best.pt"
        else:
            filename = f"{stage.name}_epoch_{epoch}.pt"

        path = self.output_dir / filename
        torch.save(checkpoint, path)
        self.logger.info(f"💾 Checkpoint saved: {path}")

    def train_curriculum(self, tokenizer: EmpoorioBPETokenizer):
        """Execute the full curriculum learning pipeline."""
        self.logger.info("🚀 STARTING CURRICULUM LEARNING: Baby Titan → 7B")
        self.logger.info("=" * 60)

        start_time = time.time()

        for i, stage in enumerate(self.config.stages):
            self.current_stage_idx = i
            self.logger.info(f"🎯 Stage {i + 1}/{len(self.config.stages)}: {stage.name}")

            stage_start = time.time()
            best_loss = self._train_stage(stage, tokenizer)
            stage_time = time.time() - stage_start

            self.best_losses[stage.name] = best_loss
            self.logger.info(f"✅ Stage {stage.name} completed in {stage_time:.2f}s. Best loss: {best_loss:.4f}")

            if self.config.save_every_stage:
                # Keep model in memory for next stage
                pass

        total_time = time.time() - start_time
        self.logger.info(f"🎉 CURRICULUM LEARNING COMPLETE in {total_time:.2f}s!")
        self.logger.info("🌟 EmpoorioLM has evolved from Baby Titan to 7B!")

        # Save final curriculum results
        self._save_curriculum_results()

    def _save_curriculum_results(self):
        """Save curriculum learning results."""
        results = {
            'stages': [stage.name for stage in self.config.stages],
            'best_losses': self.best_losses,
            'config': self.config.__dict__,
            'completed_at': time.time()
        }

        results_path = self.output_dir / "curriculum_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"📊 Curriculum results saved to {results_path}")

    def load_checkpoint(self, stage_name: str, checkpoint_path: str):
        """Load a checkpoint for a specific stage."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        model = self._get_stage_model(next(s for s in self.config.stages if s.name == stage_name))
        model.load_state_dict(checkpoint['model_state_dict'])
        self.logger.info(f"📥 Loaded checkpoint for {stage_name} from {checkpoint_path}")


# Predefined curriculum configurations
def create_baby_to_7b_curriculum() -> CurriculumConfig:
    """Create curriculum from Baby Titan to 7B."""
    stages = [
        CurriculumStage(
            name="baby_titan",
            model_factory=create_empoorio_baby_titan,
            epochs=3,
            learning_rate=1e-3,
            batch_size=4,
            max_seq_length=512,
            data_complexity="simple",
            distillation_weight=0.0
        ),
        CurriculumStage(
            name="titan",
            model_factory=create_empoorio_titan,
            epochs=5,
            learning_rate=5e-4,
            batch_size=2,
            max_seq_length=1024,
            data_complexity="medium",
            distillation_weight=0.3
        ),
        CurriculumStage(
            name="7b",
            model_factory=create_empoorio_7b,
            epochs=10,
            learning_rate=1e-4,
            batch_size=1,
            max_seq_length=2048,
            data_complexity="complex",
            distillation_weight=0.5
        )
    ]

    return CurriculumConfig(
        stages=stages,
        output_dir="./curriculum_baby_to_7b",
        use_distillation=True
    )


class CurriculumScheduler:
    """
    Scheduler for curriculum learning phases.
    Manages progressive difficulty increase during training.
    """

    def __init__(self, phases: List[Dict[str, Any]]):
        """
        Initialize curriculum scheduler.

        Args:
            phases: List of phase dictionaries with 'name', 'complexity', 'duration'
        """
        self.phases = phases
        self.current_phase_idx = 0
        self.phase_start_step = 0
        self.total_steps = sum(phase['duration'] for phase in phases)

    def get_current_difficulty(self, global_step: int) -> float:
        """
        Get current difficulty level based on training progress.

        Args:
            global_step: Current training step

        Returns:
            Difficulty level (0.0 to 1.0)
        """
        # Find current phase
        cumulative_steps = 0
        for i, phase in enumerate(self.phases):
            cumulative_steps += phase['duration']
            if global_step < cumulative_steps:
                current_phase = phase
                phase_progress = (global_step - (cumulative_steps - phase['duration'])) / phase['duration']
                break
        else:
            # Past last phase
            current_phase = self.phases[-1]
            phase_progress = 1.0

        # Interpolate difficulty within phase
        base_difficulty = current_phase['complexity']
        # Add some variation within phase
        difficulty_variation = 0.1 * torch.sin(torch.tensor(phase_progress * 2 * torch.pi)).item()

        return min(1.0, max(0.1, base_difficulty + difficulty_variation))

    def get_current_phase(self, global_step: int) -> str:
        """
        Get current phase name.

        Args:
            global_step: Current training step

        Returns:
            Phase name
        """
        cumulative_steps = 0
        for phase in self.phases:
            cumulative_steps += phase['duration']
            if global_step < cumulative_steps:
                return phase['name']

        return self.phases[-1]['name']  # Last phase if beyond total steps

    def get_phase_info(self, global_step: int) -> Dict[str, Any]:
        """Get detailed phase information."""
        cumulative_steps = 0
        for i, phase in enumerate(self.phases):
            cumulative_steps += phase['duration']
            if global_step < cumulative_steps:
                phase_progress = (global_step - (cumulative_steps - phase['duration'])) / phase['duration']
                return {
                    'phase_name': phase['name'],
                    'phase_index': i,
                    'phase_progress': phase_progress,
                    'difficulty': phase['complexity'],
                    'remaining_steps_in_phase': cumulative_steps - global_step,
                    'total_phases': len(self.phases)
                }

        # Beyond last phase
        return {
            'phase_name': self.phases[-1]['name'],
            'phase_index': len(self.phases) - 1,
            'phase_progress': 1.0,
            'difficulty': self.phases[-1]['complexity'],
            'remaining_steps_in_phase': 0,
            'total_phases': len(self.phases)
        }


def run_curriculum_learning(tokenizer: EmpoorioBPETokenizer, curriculum_config: Optional[CurriculumConfig] = None):
    """Run curriculum learning with given tokenizer."""
    if curriculum_config is None:
        curriculum_config = create_baby_to_7b_curriculum()

    manager = CurriculumLearningManager(curriculum_config)
    manager.train_curriculum(tokenizer)

    return manager