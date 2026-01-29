"""
Advanced Curriculum Learning Trainer for EmpoorioLM.
Entrenador avanzado de curriculum learning para EmpoorioLM.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Subset
from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
import math
from pathlib import Path
import json
from datetime import datetime

from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..models.empoorio_lm.advanced_config import (
    AccuracyOptimizedConfig,
    get_curriculum_schedule,
    create_accuracy_optimizer,
    create_accuracy_scheduler,
    apply_accuracy_improvements
)

logger = logging.getLogger(__name__)


class CurriculumDataset(Dataset):
    """Dataset wrapper that implements curriculum learning sampling."""

    def __init__(self, base_dataset: Dataset, curriculum_phase: Dict[str, Any]):
        self.base_dataset = base_dataset
        self.phase = curriculum_phase
        self.max_length = curriculum_phase.get("max_length", 512)

        # Filter samples by length for this curriculum phase
        self.valid_indices = self._filter_by_length()

    def _filter_by_length(self) -> List[int]:
        """Filter dataset indices based on sequence length for current phase."""
        valid_indices = []

        for idx in range(len(self.base_dataset)):
            try:
                sample = self.base_dataset[idx]
                # Check if sample meets length criteria
                if self._sample_meets_criteria(sample):
                    valid_indices.append(idx)
            except Exception as e:
                logger.warning(f"Error checking sample {idx}: {e}")
                continue

        logger.info(f"Phase '{self.phase['name']}': {len(valid_indices)}/{len(self.base_dataset)} samples meet criteria")
        return valid_indices

    def _sample_meets_criteria(self, sample) -> bool:
        """Check if sample meets curriculum phase criteria."""
        # For text datasets, check sequence length
        if hasattr(sample, 'input_ids') and hasattr(sample.input_ids, '__len__'):
            return len(sample.input_ids) <= self.max_length
        elif isinstance(sample, dict) and 'input_ids' in sample:
            return len(sample['input_ids']) <= self.max_length
        elif isinstance(sample, (list, tuple)) and len(sample) > 0:
            # Assume first element is input_ids
            return len(sample[0]) <= self.max_length

        # If we can't determine length, include the sample
        return True

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        actual_idx = self.valid_indices[idx]
        return self.base_dataset[actual_idx]


class CurriculumTrainer:
    """
    Advanced curriculum learning trainer for EmpoorioLM.
    Entrenador avanzado de curriculum learning para EmpoorioLM.
    """

    def __init__(
        self,
        model: EmpoorioLM,
        config: AccuracyOptimizedConfig,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "./checkpoints"
    ):
        self.model = model
        self.config = config
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Curriculum state
        self.curriculum_schedule = get_curriculum_schedule(config)
        self.current_phase_idx = 0
        self.current_phase = self.curriculum_schedule[0]

        # Training state
        self.global_step = 0
        self.epoch = 0
        self.best_accuracy = 0.0

        # Setup optimizer and scheduler
        self.optimizer = create_accuracy_optimizer(model, config)
        self.warmup_scheduler, self.main_scheduler = create_accuracy_scheduler(
            self.optimizer, config, self._estimate_training_steps()
        )

        # Apply accuracy improvements
        self.model = apply_accuracy_improvements(model, config)

        # Setup logging
        self.setup_logging()

        logger.info(f"🎯 Curriculum Trainer initialized with {len(self.curriculum_schedule)} phases")

    def setup_logging(self):
        """Setup training logging."""
        log_file = self.output_dir / "curriculum_training.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    def _estimate_training_steps(self) -> int:
        """Estimate total training steps across all curriculum phases."""
        total_steps = 0
        for phase in self.curriculum_schedule:
            phase_steps = phase.get("epochs", 1) * (len(self.train_dataset) // self.config.batch_size)
            total_steps += phase_steps
        return max(total_steps, 1000)  # Minimum estimate

    def _create_phase_dataloader(self, phase: Dict[str, Any]) -> DataLoader:
        """Create dataloader for specific curriculum phase."""
        # Wrap dataset with curriculum filtering
        curriculum_dataset = CurriculumDataset(self.train_dataset, phase)

        # Phase-specific batch size (smaller for harder phases)
        batch_size = min(self.config.batch_size, max(1, self.config.batch_size // (self.current_phase_idx + 1)))

        dataloader = DataLoader(
            curriculum_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True,
            drop_last=True
        )

        return dataloader

    def _should_advance_phase(self, phase_metrics: Dict[str, Any]) -> bool:
        """Determine if we should advance to next curriculum phase."""
        # Advance criteria
        min_accuracy = 0.6 + (self.current_phase_idx * 0.1)  # Increasing accuracy threshold
        min_epochs = self.current_phase.get("epochs", 1)

        accuracy = phase_metrics.get("accuracy", 0.0)
        current_phase_epochs = self.epoch - sum(p.get("epochs", 1) for p in self.curriculum_schedule[:self.current_phase_idx])

        # Advance if accuracy is good enough and minimum epochs completed
        return accuracy >= min_accuracy and current_phase_epochs >= min_epochs

    def _advance_curriculum_phase(self):
        """Advance to next curriculum phase."""
        if self.current_phase_idx < len(self.curriculum_schedule) - 1:
            self.current_phase_idx += 1
            self.current_phase = self.curriculum_schedule[self.current_phase_idx]

            # Update learning rate for new phase
            new_lr = self.current_phase.get("lr", self.config.learning_rate)
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = new_lr

            logger.info(f"🚀 Advanced to curriculum phase: {self.current_phase['name']}")
            logger.info(f"   Max length: {self.current_phase['max_length']}")
            logger.info(f"   Learning rate: {new_lr}")
        else:
            logger.info("🎉 Curriculum learning completed - final phase reached")

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        epoch_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(dataloader):
            # Move batch to device
            if isinstance(batch, dict):
                batch = {k: v.to(self.config.device) for k, v in batch.items()}
            else:
                batch = batch.to(self.config.device)

            # Forward pass
            outputs = self.model(**batch)
            loss = outputs.get("loss")

            if loss is None:
                # Compute loss manually if not provided
                logits = outputs["logits"]
                labels = batch.get("labels", batch.get("input_ids"))
                loss = F.cross_entropy(
                    logits.view(-1, logits.size(-1)),
                    labels.view(-1),
                    ignore_index=-100
                )

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)

            # Optimizer step
            self.optimizer.step()

            # Scheduler step
            if self.global_step < self.config.warmup_steps:
                self.warmup_scheduler.step()
            else:
                self.main_scheduler.step()

            # Update metrics
            epoch_loss += loss.item()
            num_batches += 1
            self.global_step += 1

            # Log progress
            if batch_idx % 100 == 0:
                logger.info(f"Batch {batch_idx}/{len(dataloader)} - Loss: {loss.item():.4f}")

        return {"loss": epoch_loss / num_batches}

    def evaluate(self, dataloader: Optional[DataLoader] = None) -> Dict[str, float]:
        """Evaluate model performance."""
        if dataloader is None and self.eval_dataset is not None:
            dataloader = DataLoader(
                self.eval_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=4,
                pin_memory=True
            )

        if dataloader is None:
            return {}

        self.model.eval()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                # Move batch to device
                if isinstance(batch, dict):
                    batch = {k: v.to(self.config.device) for k, v in batch.items()}
                else:
                    batch = batch.to(self.config.device)

                # Forward pass
                outputs = self.model(**batch)
                logits = outputs["logits"]

                # Compute loss
                labels = batch.get("labels", batch.get("input_ids"))
                loss = F.cross_entropy(
                    logits.view(-1, logits.size(-1)),
                    labels.view(-1),
                    ignore_index=-100
                )

                # Compute accuracy (for next-token prediction)
                predictions = torch.argmax(logits, dim=-1)
                # Shift predictions and labels for next-token prediction
                pred_shifted = predictions[..., :-1].contiguous()
                label_shifted = labels[..., 1:].contiguous()

                correct = (pred_shifted == label_shifted).float().sum()
                total_correct += correct.item()
                total_samples += label_shifted.numel()
                total_loss += loss.item()
                num_batches += 1

        accuracy = total_correct / total_samples if total_samples > 0 else 0.0
        perplexity = math.exp(total_loss / num_batches) if num_batches > 0 else float('inf')

        return {
            "loss": total_loss / num_batches,
            "accuracy": accuracy,
            "perplexity": perplexity
        }

    def save_checkpoint(self, metrics: Dict[str, float], is_best: bool = False):
        """Save training checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": {
                "warmup": self.warmup_scheduler.state_dict() if hasattr(self.warmup_scheduler, 'state_dict') else None,
                "main": self.main_scheduler.state_dict() if hasattr(self.main_scheduler, 'state_dict') else None,
            },
            "config": self.config.to_dict(),
            "curriculum_state": {
                "current_phase_idx": self.current_phase_idx,
                "current_phase": self.current_phase,
                "global_step": self.global_step,
                "epoch": self.epoch,
                "best_accuracy": self.best_accuracy
            },
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }

        # Save regular checkpoint
        checkpoint_path = self.output_dir / f"checkpoint_epoch_{self.epoch}_phase_{self.current_phase_idx}.pt"
        torch.save(checkpoint, checkpoint_path)

        # Save best model
        if is_best:
            best_path = self.output_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            logger.info(f"💾 Saved best model checkpoint: {best_path}")

        # Save metrics
        metrics_path = self.output_dir / "training_metrics.json"
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                all_metrics = json.load(f)
        else:
            all_metrics = []

        all_metrics.append({
            "epoch": self.epoch,
            "phase": self.current_phase['name'],
            "global_step": self.global_step,
            **metrics,
            "timestamp": datetime.now().isoformat()
        })

        with open(metrics_path, 'w') as f:
            json.dump(all_metrics, f, indent=2)

    def train(self, max_epochs: Optional[int] = None) -> Dict[str, Any]:
        """Main training loop with curriculum learning."""
        logger.info("🎯 Starting curriculum learning training")

        if max_epochs is None:
            max_epochs = sum(phase.get("epochs", 1) for phase in self.curriculum_schedule)

        training_history = []

        while self.epoch < max_epochs:
            logger.info(f"📚 Epoch {self.epoch + 1}/{max_epochs} - Phase: {self.current_phase['name']}")

            # Create dataloader for current phase
            train_dataloader = self._create_phase_dataloader(self.current_phase)

            # Train epoch
            train_metrics = self.train_epoch(train_dataloader)
            logger.info(f"📈 Training metrics: {train_metrics}")

            # Evaluate
            eval_metrics = self.evaluate()
            if eval_metrics:
                logger.info(f"📊 Evaluation metrics: {eval_metrics}")

                # Update best accuracy
                current_accuracy = eval_metrics.get("accuracy", 0.0)
                if current_accuracy > self.best_accuracy:
                    self.best_accuracy = current_accuracy
                    self.save_checkpoint(eval_metrics, is_best=True)

            # Combine metrics
            epoch_metrics = {**train_metrics, **eval_metrics}
            training_history.append(epoch_metrics)

            # Save regular checkpoint
            self.save_checkpoint(epoch_metrics)

            # Check if should advance curriculum phase
            if self._should_advance_phase(epoch_metrics):
                self._advance_curriculum_phase()

            self.epoch += 1

        logger.info("🎉 Curriculum learning training completed!")
        logger.info(f"🏆 Best accuracy achieved: {self.best_accuracy:.4f}")

        return {
            "final_metrics": epoch_metrics,
            "best_accuracy": self.best_accuracy,
            "training_history": training_history,
            "curriculum_completed": self.current_phase_idx >= len(self.curriculum_schedule) - 1
        }


def create_curriculum_trainer(
    config: AccuracyOptimizedConfig,
    train_dataset: Dataset,
    eval_dataset: Optional[Dataset] = None,
    model_path: Optional[str] = None,
    output_dir: str = "./curriculum_checkpoints"
) -> CurriculumTrainer:
    """
    Factory function to create curriculum trainer.
    Función factory para crear entrenador de curriculum.
    """

    # Create model
    if model_path and Path(model_path).exists():
        model = EmpoorioLM.from_pretrained(model_path, config)
    else:
        model = EmpoorioLM(config)

    # Create trainer
    trainer = CurriculumTrainer(
        model=model,
        config=config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        output_dir=output_dir
    )

    return trainer


__all__ = [
    'CurriculumDataset',
    'CurriculumTrainer',
    'create_curriculum_trainer'
]