"""
MIRAS Fine-Tuning Module
========================

Módulo especializado para fine-tuning de capacidades MIRAS (Memoria Inteligente y Adaptativa en Tiempo Real).
Entrena componentes específicos de MIRAS para mejorar retención, recuperación y adaptación de memoria.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from ..inference.memory.miras_block import MIRASBlock, MIRASState, SurpriseMetrics
from ..inference.memory.surprise_encoder import SurpriseEncoder
from .curriculum_learning import CurriculumScheduler

logger = logging.getLogger(__name__)


@dataclass
class MIRASFineTuningConfig:
    """Configuración específica para fine-tuning MIRAS."""

    # Dataset configuration
    memory_sequence_length: int = 512
    num_memory_tasks: int = 10000
    surprise_threshold: float = 0.5
    adaptation_steps: int = 10

    # Model configuration
    hidden_size: int = 768
    num_heads: int = 12
    memory_size: int = 1024
    dropout: float = 0.1

    # Training configuration
    batch_size: int = 4
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    max_steps: int = 10000
    warmup_steps: int = 1000
    save_steps: int = 2000
    eval_steps: int = 500

    # MIRAS-specific objectives
    retention_loss_weight: float = 1.0
    surprise_loss_weight: float = 0.5
    memory_consistency_weight: float = 0.3
    adaptation_loss_weight: float = 0.2

    # Curriculum learning
    use_curriculum: bool = True
    curriculum_phases: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "basic_memory", "complexity": 0.3, "duration": 3000},
        {"name": "surprise_adaptation", "complexity": 0.6, "duration": 4000},
        {"name": "complex_reasoning", "complexity": 0.9, "duration": 3000}
    ])

    # Output
    output_dir: str = "./miras_fine_tuned"
    logging_steps: int = 100


@dataclass
class MIRASTrainingMetrics:
    """Métricas específicas de entrenamiento MIRAS."""
    step: int = 0
    total_loss: float = 0.0
    retention_loss: float = 0.0
    surprise_loss: float = 0.0
    memory_consistency_loss: float = 0.0
    adaptation_loss: float = 0.0
    learning_rate: float = 0.0
    memory_utilization: float = 0.0
    surprise_accuracy: float = 0.0
    retention_accuracy: float = 0.0
    curriculum_phase: str = "initial"


class MIRASMemoryTask:
    """Tarea de memoria para entrenamiento MIRAS."""

    def __init__(self, sequence_length: int = 512, surprise_threshold: float = 0.5):
        self.sequence_length = sequence_length
        self.surprise_threshold = surprise_threshold

    def generate_task(self) -> Dict[str, Any]:
        """Generar una tarea de memoria con elementos sorpresa."""
        # Crear secuencia base
        base_sequence = self._generate_base_sequence()

        # Insertar elementos sorpresa
        surprise_positions, surprise_elements = self._inject_surprises(base_sequence)

        # Crear máscara de atención
        attention_mask = self._create_attention_mask(len(base_sequence))

        # Crear etiquetas de retención (qué recordar)
        retention_labels = self._create_retention_labels(base_sequence, surprise_positions)

        # Crear etiquetas de sorpresa
        surprise_labels = self._create_surprise_labels(surprise_positions)

        return {
            'input_sequence': base_sequence,
            'attention_mask': attention_mask,
            'surprise_positions': surprise_positions,
            'surprise_elements': surprise_elements,
            'retention_labels': retention_labels,
            'surprise_labels': surprise_labels,
            'task_metadata': {
                'sequence_length': len(base_sequence),
                'num_surprises': len(surprise_positions),
                'surprise_density': len(surprise_positions) / len(base_sequence)
            }
        }

    def _generate_base_sequence(self) -> List[int]:
        """Generar secuencia base con patrones repetitivos."""
        sequence = []

        # Patrón repetitivo básico
        pattern = [1, 2, 3, 4, 5]
        repetitions = self.sequence_length // len(pattern)

        for _ in range(repetitions):
            sequence.extend(pattern)

        # Rellenar hasta sequence_length
        while len(sequence) < self.sequence_length:
            sequence.append(np.random.randint(1, 10))

        return sequence[:self.sequence_length]

    def _inject_surprises(self, sequence: List[int]) -> Tuple[List[int], List[int]]:
        """Inyectar elementos sorpresa en la secuencia."""
        surprise_positions = []
        surprise_elements = []

        # Determinar posiciones para sorpresas (10-20% de la secuencia)
        num_surprises = max(1, int(len(sequence) * np.random.uniform(0.1, 0.2)))

        positions = np.random.choice(len(sequence), num_surprises, replace=False)
        positions = sorted(positions)

        for pos in positions:
            # Elemento sorpresa: valor fuera del patrón normal
            surprise_value = np.random.randint(100, 200)  # Valores altos para sorpresa
            original_value = sequence[pos]

            sequence[pos] = surprise_value
            surprise_positions.append(pos)
            surprise_elements.append((original_value, surprise_value))

        return surprise_positions, surprise_elements

    def _create_attention_mask(self, seq_len: int) -> List[int]:
        """Crear máscara de atención."""
        return [1] * seq_len

    def _create_retention_labels(self, sequence: List[int], surprise_positions: List[int]) -> List[float]:
        """Crear etiquetas de retención basadas en importancia."""
        labels = []

        for i, token in enumerate(sequence):
            if i in surprise_positions:
                # Alta retención para elementos sorpresa
                labels.append(1.0)
            elif self._is_pattern_token(token, i):
                # Media retención para tokens de patrón
                labels.append(0.7)
            else:
                # Baja retención para ruido
                labels.append(0.3)

        return labels

    def _create_surprise_labels(self, surprise_positions: List[int]) -> List[float]:
        """Crear etiquetas de sorpresa."""
        labels = [0.0] * self.sequence_length

        for pos in surprise_positions:
            labels[pos] = 1.0
            # Efecto de propagación de sorpresa
            start = max(0, pos - 2)
            end = min(self.sequence_length, pos + 3)
            for i in range(start, end):
                if i != pos:
                    labels[i] = 0.5  # Sorpresa reducida

        return labels

    def _is_pattern_token(self, token: int, position: int) -> bool:
        """Determinar si un token es parte de un patrón."""
        pattern_cycle = position % 5
        expected_token = pattern_cycle + 1
        return token == expected_token


class MIRASDataset(Dataset):
    """Dataset para entrenamiento MIRAS."""

    def __init__(self, config: MIRASFineTuningConfig):
        self.config = config
        self.task_generator = MIRASMemoryTask(
            sequence_length=config.memory_sequence_length,
            surprise_threshold=config.surprise_threshold
        )
        self.samples = []

        # Generar tareas
        self._generate_dataset()

    def _generate_dataset(self):
        """Generar dataset de tareas MIRAS."""
        logger.info(f"Generating {self.config.num_memory_tasks} MIRAS memory tasks...")

        for i in range(self.config.num_memory_tasks):
            task = self.task_generator.generate_task()
            self.samples.append(task)

        logger.info(f"Generated {len(self.samples)} MIRAS training samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Convertir a tensores
        return {
            'input_sequence': torch.tensor(sample['input_sequence'], dtype=torch.long),
            'attention_mask': torch.tensor(sample['attention_mask'], dtype=torch.long),
            'retention_labels': torch.tensor(sample['retention_labels'], dtype=torch.float),
            'surprise_labels': torch.tensor(sample['surprise_labels'], dtype=torch.float),
            'task_metadata': sample['task_metadata']
        }


class MIRASFineTuner:
    """
    Fine-tuner especializado para capacidades MIRAS.
    Entrena componentes de memoria inteligente y adaptativa.
    """

    def __init__(self, config: MIRASFineTuningConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Componentes MIRAS
        self.miras_block = None
        self.surprise_encoder = None
        self.curriculum_scheduler = None

        # Optimización
        self.optimizer = None
        self.scheduler = None

        # Datasets
        self.train_dataset = None
        self.eval_dataset = None
        self.train_dataloader = None
        self.eval_dataloader = None

        # Métricas
        self.metrics_history = []
        self.best_memory_score = 0.0

    def initialize(self) -> bool:
        """Inicializar el sistema de fine-tuning MIRAS."""
        try:
            logger.info("🚀 Initializing MIRAS Fine-Tuning System...")

            # Inicializar componentes MIRAS
            self._initialize_miras_components()

            # Preparar datasets
            self._prepare_datasets()

            # Configurar optimización
            self._setup_optimizer()

            # Inicializar curriculum si está habilitado
            if self.config.use_curriculum:
                self._initialize_curriculum()

            logger.info("✅ MIRAS Fine-Tuning system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize MIRAS fine-tuning: {e}")
            return False

    def _initialize_miras_components(self):
        """Inicializar componentes MIRAS para fine-tuning."""
        # Surprise Encoder
        self.surprise_encoder = SurpriseEncoder(
            vocab_size=50257,  # GPT-2 vocab
            hidden_size=self.config.hidden_size,
            device=self.device
        )

        # MIRAS Block
        self.miras_block = MIRASBlock(
            hidden_size=self.config.hidden_size,
            num_heads=self.config.num_heads,
            memory_size=self.config.memory_size,
            dropout=self.config.dropout,
            surprise_encoder=self.surprise_encoder
        ).to(self.device)

        # Poner en modo entrenamiento
        self.miras_block.train()

        logger.info(f"🧠 MIRAS components initialized: hidden_size={self.config.hidden_size}, memory_size={self.config.memory_size}")

    def _prepare_datasets(self):
        """Preparar datasets de entrenamiento y evaluación."""
        logger.info("📚 Preparing MIRAS datasets...")

        # Dataset completo
        full_dataset = MIRASDataset(self.config)

        # Split train/eval
        eval_size = min(1000, len(full_dataset) // 10)
        train_size = len(full_dataset) - eval_size

        self.train_dataset = torch.utils.data.Subset(full_dataset, range(train_size))
        self.eval_dataset = torch.utils.data.Subset(full_dataset, range(train_size, len(full_dataset)))

        # DataLoaders
        self.train_dataloader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )

        self.eval_dataloader = DataLoader(
            self.eval_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True
        )

        logger.info(f"✅ Datasets prepared: {train_size} train, {eval_size} eval samples")

    def _setup_optimizer(self):
        """Configurar optimizador y scheduler."""
        # Parámetros entrenables
        miras_params = list(self.miras_block.parameters())
        surprise_params = list(self.surprise_encoder.parameters())

        trainable_params = miras_params + surprise_params

        # Optimizador
        self.optimizer = torch.optim.AdamW(
            trainable_params,
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        # Scheduler con warmup
        def lr_lambda(step):
            if step < self.config.warmup_steps:
                return step / max(1, self.config.warmup_steps)
            return max(0.1, 0.5 * (1 + torch.cos(torch.pi * (step - self.config.warmup_steps) /
                                                (self.config.max_steps - self.config.warmup_steps))))

        self.scheduler = torch.optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)

    def _initialize_curriculum(self):
        """Inicializar curriculum learning para MIRAS."""
        self.curriculum_scheduler = CurriculumScheduler(
            phases=self.config.curriculum_phases
        )

    def train(self) -> Dict[str, Any]:
        """Ejecutar entrenamiento de fine-tuning MIRAS."""
        logger.info("🎯 Starting MIRAS Fine-Tuning Training...")

        global_step = 0
        best_memory_score = 0.0

        while global_step < self.config.max_steps:
            for batch in self.train_dataloader:
                # Obtener complejidad del curriculum
                complexity = 1.0
                if self.curriculum_scheduler:
                    complexity = self.curriculum_scheduler.get_current_difficulty(global_step)

                # Paso de entrenamiento
                metrics = self._training_step(batch, global_step, complexity)
                self.metrics_history.append(metrics)

                # Logging
                if global_step % self.config.logging_steps == 0:
                    self._log_metrics(metrics)

                # Evaluación
                if global_step % self.config.eval_steps == 0:
                    eval_metrics = self.evaluate()
                    self._log_eval_metrics(eval_metrics, global_step)

                    # Guardar mejor modelo
                    memory_score = eval_metrics.get('memory_consistency', 0.0)
                    if memory_score > best_memory_score:
                        best_memory_score = memory_score
                        self.save_checkpoint(f"best_miras_step_{global_step}")

                # Guardar checkpoint
                if global_step % self.config.save_steps == 0:
                    self.save_checkpoint(f"miras_checkpoint_step_{global_step}")

                global_step += 1
                if global_step >= self.config.max_steps:
                    break

        # Evaluación final
        final_metrics = self.evaluate()
        logger.info(f"🏁 MIRAS Fine-tuning completed. Final memory score: {final_metrics.get('memory_consistency', 0.0):.4f}")

        return {
            "final_metrics": final_metrics,
            "best_memory_score": best_memory_score,
            "total_steps": global_step,
            "training_history": self.metrics_history
        }

    def _training_step(self, batch: Dict[str, torch.Tensor], step: int, complexity: float) -> MIRASTrainingMetrics:
        """Ejecutar un paso de entrenamiento MIRAS."""
        # Mover batch a device
        batch = {k: v.to(self.device) for k, v in batch.items()}

        # Convertir secuencia de entrada a embeddings (simulación)
        # En implementación real, esto vendría del modelo principal
        input_embeddings = self._create_input_embeddings(batch['input_sequence'])

        # Forward pass MIRAS
        miras_output, aux_info = self.miras_block(
            hidden_states=input_embeddings,
            attention_mask=batch.get('attention_mask'),
            input_ids=batch['input_sequence']
        )

        # Calcular pérdidas
        losses = self._compute_losses(miras_output, aux_info, batch, complexity)

        # Backward pass
        total_loss = sum(losses.values())
        total_loss.backward()

        # Optimizer step
        torch.nn.utils.clip_grad_norm_(self.miras_block.parameters(), max_norm=1.0)
        self.optimizer.step()
        self.optimizer.zero_grad()
        self.scheduler.step()

        # Métricas
        metrics = MIRASTrainingMetrics(
            step=step,
            total_loss=total_loss.item(),
            retention_loss=losses.get('retention', 0.0),
            surprise_loss=losses.get('surprise', 0.0),
            memory_consistency_loss=losses.get('consistency', 0.0),
            adaptation_loss=losses.get('adaptation', 0.0),
            learning_rate=self.scheduler.get_last_lr()[0],
            memory_utilization=aux_info.get('memory_utilization', 0.0),
            curriculum_phase=self.curriculum_scheduler.get_current_phase(step) if self.curriculum_scheduler else "standard"
        )

        return metrics

    def _create_input_embeddings(self, input_sequence: torch.Tensor) -> torch.Tensor:
        """Crear embeddings de entrada (simulación para fine-tuning MIRAS)."""
        batch_size, seq_len = input_sequence.shape

        # Embedding simple para tokens (en implementación real vendría del modelo)
        vocab_size = 50257  # GPT-2 vocab
        embedding = nn.Embedding(vocab_size, self.config.hidden_size).to(self.device)

        # Mapear tokens altos a rango de vocabulario
        mapped_sequence = input_sequence % vocab_size

        return embedding(mapped_sequence)

    def _compute_losses(self, miras_output: torch.Tensor, aux_info: Dict[str, Any],
                       batch: Dict[str, torch.Tensor], complexity: float) -> Dict[str, torch.Tensor]:
        """Calcular pérdidas específicas de MIRAS."""
        losses = {}

        # Pérdida de retención
        if 'retention_scores' in aux_info and 'retention_labels' in batch:
            retention_pred = aux_info['retention_scores']  # [batch_size, seq_len]
            retention_target = batch['retention_labels']    # [batch_size, seq_len]

            retention_loss = F.mse_loss(retention_pred, retention_target)
            losses['retention'] = self.config.retention_loss_weight * retention_loss

        # Pérdida de sorpresa
        if 'surprise_metrics' in aux_info and 'surprise_labels' in batch:
            surprise_metrics = aux_info['surprise_metrics']
            surprise_pred = torch.full_like(batch['surprise_labels'], surprise_metrics.surprise_score)
            surprise_target = batch['surprise_labels']

            surprise_loss = F.mse_loss(surprise_pred, surprise_target)
            losses['surprise'] = self.config.surprise_loss_weight * surprise_loss

        # Pérdida de consistencia de memoria
        if 'memory_attention' in aux_info:
            memory_attention = aux_info['memory_attention']  # [batch_size, seq_len, memory_size]

            # Penalizar atención dispersa (debería ser concentrada)
            attention_entropy = -torch.sum(memory_attention * torch.log(memory_attention + 1e-10), dim=-1)
            consistency_loss = attention_entropy.mean()

            losses['consistency'] = self.config.memory_consistency_weight * consistency_loss

        # Pérdida de adaptación (cambio en bias de atención)
        if 'attention_bias' in aux_info:
            attention_bias = aux_info['attention_bias']

            # Penalizar cambios demasiado grandes en bias
            bias_change_penalty = torch.norm(attention_bias, dim=-1).mean()
            adaptation_loss = 0.01 * bias_change_penalty  # Peso pequeño

            losses['adaptation'] = self.config.adaptation_loss_weight * adaptation_loss

        # Aplicar complejidad del curriculum
        for key in losses:
            losses[key] = losses[key] * complexity

        return losses

    def evaluate(self) -> Dict[str, float]:
        """Evaluar capacidades MIRAS."""
        self.miras_block.eval()
        total_metrics = {
            'retention_accuracy': 0.0,
            'surprise_accuracy': 0.0,
            'memory_consistency': 0.0,
            'adaptation_score': 0.0
        }

        num_batches = 0

        with torch.no_grad():
            for batch in self.eval_dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                input_embeddings = self._create_input_embeddings(batch['input_sequence'])

                miras_output, aux_info = self.miras_block(
                    hidden_states=input_embeddings,
                    attention_mask=batch.get('attention_mask'),
                    input_ids=batch['input_sequence']
                )

                # Calcular métricas por batch
                batch_metrics = self._compute_evaluation_metrics(aux_info, batch)
                for key in total_metrics:
                    total_metrics[key] += batch_metrics.get(key, 0.0)

                num_batches += 1

        # Promediar
        for key in total_metrics:
            total_metrics[key] /= num_batches

        self.miras_block.train()
        return total_metrics

    def _compute_evaluation_metrics(self, aux_info: Dict[str, Any], batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Calcular métricas de evaluación."""
        metrics = {}

        # Accuracy de retención
        if 'retention_scores' in aux_info and 'retention_labels' in batch:
            retention_pred = aux_info['retention_scores']
            retention_target = batch['retention_labels']

            # Threshold en 0.5
            pred_binary = (retention_pred > 0.5).float()
            target_binary = (retention_target > 0.5).float()

            retention_acc = (pred_binary == target_binary).float().mean().item()
            metrics['retention_accuracy'] = retention_acc

        # Accuracy de sorpresa
        if 'surprise_metrics' in aux_info and 'surprise_labels' in batch:
            surprise_score = aux_info['surprise_metrics'].surprise_score
            surprise_target = batch['surprise_labels']

            # Comparar con threshold
            pred_surprise = (surprise_score > self.config.surprise_threshold)
            target_surprise = (surprise_target > 0.5).any(dim=-1)

            surprise_acc = (pred_surprise == target_surprise).float().mean().item()
            metrics['surprise_accuracy'] = surprise_acc

        # Consistencia de memoria
        if 'memory_attention' in aux_info:
            memory_attention = aux_info['memory_attention']

            # Medir concentración de atención (menos entropía = mejor)
            attention_entropy = -torch.sum(memory_attention * torch.log(memory_attention + 1e-10), dim=-1)
            avg_entropy = attention_entropy.mean().item()

            # Convertir a score (menos entropía = mejor consistencia)
            consistency_score = max(0, 1.0 - avg_entropy / 5.0)  # Normalizar
            metrics['memory_consistency'] = consistency_score

        # Score de adaptación
        if 'attention_bias' in aux_info:
            attention_bias = aux_info['attention_bias']

            # Medir adaptabilidad (cambio en bias)
            bias_magnitude = torch.norm(attention_bias, dim=-1).mean().item()
            adaptation_score = min(1.0, bias_magnitude / 2.0)  # Normalizar
            metrics['adaptation_score'] = adaptation_score

        return metrics

    def save_checkpoint(self, name: str):
        """Guardar checkpoint del modelo MIRAS."""
        output_path = Path(self.config.output_dir) / name
        output_path.mkdir(parents=True, exist_ok=True)

        # Guardar componentes MIRAS
        miras_path = output_path / "miras_block.pt"
        torch.save(self.miras_block.state_dict(), miras_path)

        surprise_path = output_path / "surprise_encoder.pt"
        torch.save(self.surprise_encoder.state_dict(), surprise_path)

        # Guardar configuración y estado
        config_path = output_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config.__dict__, f, indent=2, default=str)

        training_state = {
            'step': len(self.metrics_history),
            'best_memory_score': self.best_memory_score,
            'timestamp': datetime.now().isoformat()
        }

        state_path = output_path / "training_state.json"
        with open(state_path, 'w') as f:
            json.dump(training_state, f, indent=2)

        logger.info(f"💾 MIRAS checkpoint saved: {output_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """Cargar checkpoint MIRAS."""
        checkpoint_path = Path(checkpoint_path)

        # Cargar componentes
        miras_path = checkpoint_path / "miras_block.pt"
        if miras_path.exists():
            self.miras_block.load_state_dict(torch.load(miras_path, map_location=self.device))

        surprise_path = checkpoint_path / "surprise_encoder.pt"
        if surprise_path.exists():
            self.surprise_encoder.load_state_dict(torch.load(surprise_path, map_location=self.device))

        logger.info(f"📥 MIRAS checkpoint loaded: {checkpoint_path}")

    def _log_metrics(self, metrics: MIRASTrainingMetrics):
        """Log de métricas de entrenamiento."""
        logger.info(
            f"Step {metrics.step}: Total Loss={metrics.total_loss:.4f}, "
            f"Retention={metrics.retention_loss:.4f}, Surprise={metrics.surprise_loss:.4f}, "
            f"Memory={metrics.memory_consistency_loss:.4f}, LR={metrics.learning_rate:.6f}, "
            f"Phase={metrics.curriculum_phase}"
        )

    def _log_eval_metrics(self, metrics: Dict[str, float], step: int):
        """Log de métricas de evaluación."""
        logger.info(
            f"Eval Step {step}: Retention Acc={metrics.get('retention_accuracy', 0):.4f}, "
            f"Surprise Acc={metrics.get('surprise_accuracy', 0):.4f}, "
            f"Memory Consistency={metrics.get('memory_consistency', 0):.4f}, "
            f"Adaptation Score={metrics.get('adaptation_score', 0):.4f}"
        )


async def run_miras_fine_tuning(
    memory_size: int = 1024,
    max_steps: int = 10000,
    target_memory_score: float = 0.8
) -> Dict[str, Any]:
    """
    Función principal para ejecutar fine-tuning MIRAS.

    Args:
        memory_size: Tamaño de la memoria MIRAS
        max_steps: Máximo número de pasos de entrenamiento
        target_memory_score: Score objetivo de memoria

    Returns:
        Resultados del fine-tuning MIRAS
    """
    logger.info("🚀 Starting MIRAS Fine-Tuning")
    logger.info(f"🧠 Memory Size: {memory_size}")
    logger.info(f"🎯 Target Memory Score: {target_memory_score}")
    logger.info(f"📊 Max Steps: {max_steps}")

    # Configuración
    config = MIRASFineTuningConfig(
        memory_size=memory_size,
        max_steps=max_steps,
        use_curriculum=True,
        batch_size=4,
        learning_rate=1e-4,
        retention_loss_weight=1.0,
        surprise_loss_weight=0.5,
        memory_consistency_weight=0.3,
        adaptation_loss_weight=0.2
    )

    # Inicializar fine-tuner
    miras_tuner = MIRASFineTuner(config)

    if not miras_tuner.initialize():
        raise RuntimeError("Failed to initialize MIRAS fine-tuning system")

    # Ejecutar entrenamiento
    results = miras_tuner.train()

    # Verificar objetivo alcanzado
    final_memory_score = results['final_metrics'].get('memory_consistency', 0.0)
    target_achieved = final_memory_score >= target_memory_score

    logger.info("🏁 MIRAS Fine-tuning completed!")
    logger.info(f"🧠 Final Memory Score: {final_memory_score:.4f}")
    logger.info(f"🎯 Target Achieved: {target_achieved}")

    if target_achieved:
        logger.info("🎉 SUCCESS: MIRAS capabilities successfully fine-tuned!")
    else:
        logger.warning(f"⚠️ Target not achieved. Current: {final_memory_score:.4f}, Target: {target_memory_score}")

    return {
        **results,
        'target_achieved': target_achieved,
        'improvement_needed': max(0, target_memory_score - final_memory_score)
    }


if __name__ == "__main__":
    import asyncio

    # Ejemplo de uso
    asyncio.run(run_miras_fine_tuning(
        memory_size=1024,
        max_steps=5000,
        target_memory_score=0.8
    ))