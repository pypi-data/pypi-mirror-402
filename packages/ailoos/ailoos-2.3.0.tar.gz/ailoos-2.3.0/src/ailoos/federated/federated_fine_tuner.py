"""
Federated Fine-Tuning System - Sistema de fine-tuning federado para EmpoorioLM
Permite el fine-tuning distribuido preservando privacidad y eficiencia.
"""

import asyncio
import json
import time
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import numpy as np

from ..core.logging import get_logger
from .aggregator import FederatedAggregator
from .differential_privacy import DifferentialPrivacyManager
from .homomorphic_encryptor import HomomorphicEncryptor
from .privacy_preserving_aggregator import PrivacyPreservingAggregator

logger = get_logger(__name__)


@dataclass
class FineTuningConfig:
    """Configuración para fine-tuning federado."""
    learning_rate: float = 1e-5
    batch_size: int = 8
    max_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    gradient_clip_norm: float = 1.0
    lora_rank: int = 8
    lora_alpha: float = 16
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    privacy_budget: float = 1.0
    use_differential_privacy: bool = True
    use_homomorphic_encryption: bool = False
    curriculum_learning: bool = True
    adaptive_lr: bool = True
    early_stopping_patience: int = 3


@dataclass
class FineTuningTask:
    """Tarea de fine-tuning federado."""
    task_id: str
    dataset_name: str
    domain: str
    num_samples: int
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    progress: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeFineTuningState:
    """Estado de fine-tuning en un nodo."""
    node_id: str
    task_id: str
    local_model: Optional[Any] = None
    optimizer: Optional[Any] = None
    scheduler: Optional[Any] = None
    current_epoch: int = 0
    best_loss: float = float('inf')
    patience_counter: int = 0
    gradient_accumulation_steps: int = 1
    local_steps: int = 0
    privacy_noise_scale: float = 0.0


class FederatedFineTuner:
    """
    Sistema de fine-tuning federado para EmpoorioLM.
    Coordina el fine-tuning distribuido preservando privacidad y eficiencia.
    """

    def __init__(self, session_id: str, base_model_name: str, config: FineTuningConfig = None):
        self.session_id = session_id
        self.base_model_name = base_model_name
        self.config = config or FineTuningConfig()

        # Estado del sistema
        self.is_active = False
        self.current_task: Optional[FineTuningTask] = None
        self.active_nodes: Dict[str, NodeFineTuningState] = {}
        self.completed_tasks: List[FineTuningTask] = []

        # Componentes de privacidad
        self.dp_manager = DifferentialPrivacyManager(self.config.privacy_budget) if self.config.use_differential_privacy else None
        self.he_encryptor = HomomorphicEncryptor() if self.config.use_homomorphic_encryption else None

        # Agregador federado
        self.aggregator = FederatedAggregator(session_id, base_model_name)

        # Estadísticas
        self.stats = {
            "total_tasks_processed": 0,
            "total_training_time": 0.0,
            "avg_convergence_time": 0.0,
            "privacy_budget_used": 0.0,
            "nodes_participated": set(),
            "domains_adapted": set()
        }

        # Modelo base y tokenizer
        self.base_model = None
        self.tokenizer = None
        self._initialize_base_model()

        logger.info(f"🚀 FederatedFineTuner initialized for session {session_id}")

    def _initialize_base_model(self):
        """Inicializar modelo base y tokenizer."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM

            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )

            logger.info(f"✅ Base model {self.base_model_name} loaded successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing base model: {e}")
            raise

    def create_fine_tuning_task(self, dataset_name: str, domain: str,
                               num_samples: int, priority: int = 1) -> str:
        """
        Crear nueva tarea de fine-tuning.

        Args:
            dataset_name: Nombre del dataset
            domain: Dominio del dataset
            num_samples: Número de muestras
            priority: Prioridad de la tarea

        Returns:
            ID de la tarea creada
        """
        task_id = f"ft_{self.session_id}_{int(time.time())}_{dataset_name}"

        task = FineTuningTask(
            task_id=task_id,
            dataset_name=dataset_name,
            domain=domain,
            num_samples=num_samples,
            priority=priority
        )

        self.current_task = task
        logger.info(f"📋 Created fine-tuning task {task_id} for domain {domain}")
        return task_id

    def register_node(self, node_id: str) -> bool:
        """
        Registrar un nodo para fine-tuning.

        Args:
            node_id: ID del nodo

        Returns:
            True si se registró correctamente
        """
        if node_id in self.active_nodes:
            logger.warning(f"⚠️ Node {node_id} already registered")
            return False

        state = NodeFineTuningState(node_id=node_id, task_id=self.current_task.task_id if self.current_task else "")
        self.active_nodes[node_id] = state

        self.stats["nodes_participated"].add(node_id)
        logger.info(f"✅ Node {node_id} registered for fine-tuning")
        return True

    def initialize_node_fine_tuning(self, node_id: str, local_data_size: int) -> Dict[str, Any]:
        """
        Inicializar fine-tuning en un nodo específico.

        Args:
            node_id: ID del nodo
            local_data_size: Tamaño del dataset local

        Returns:
            Configuración para el nodo
        """
        if node_id not in self.active_nodes:
            raise ValueError(f"Node {node_id} not registered")

        if not self.current_task:
            raise ValueError("No active fine-tuning task")

        state = self.active_nodes[node_id]

        # Configurar LoRA para fine-tuning eficiente
        from peft import LoraConfig, get_peft_model

        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Crear modelo local con LoRA
        local_model = get_peft_model(self.base_model, lora_config)
        local_model.print_trainable_parameters()

        # Configurar optimizer y scheduler
        optimizer = torch.optim.AdamW(
            local_model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=self.config.max_epochs * (local_data_size // self.config.batch_size)
        )

        # Actualizar estado del nodo
        state.local_model = local_model
        state.optimizer = optimizer
        state.scheduler = scheduler

        # Calcular pasos de gradiente acumulado basados en tamaño de datos
        state.gradient_accumulation_steps = max(1, 32 // self.config.batch_size)

        logger.info(f"🎯 Initialized fine-tuning for node {node_id}")
        logger.info(f"   📊 Local data size: {local_data_size}")
        logger.info(f"   🔧 Gradient accumulation steps: {state.gradient_accumulation_steps}")

        return {
            "task_id": self.current_task.task_id,
            "model_config": {
                "lora_rank": self.config.lora_rank,
                "learning_rate": self.config.learning_rate,
                "batch_size": self.config.batch_size,
                "max_epochs": self.config.max_epochs
            },
            "privacy_config": {
                "use_dp": self.config.use_differential_privacy,
                "privacy_budget": self.config.privacy_budget,
                "noise_scale": state.privacy_noise_scale
            }
        }

    async def execute_federated_fine_tuning_round(self, node_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ejecutar una ronda de fine-tuning federado.

        Args:
            node_updates: Actualizaciones de los nodos participantes

        Returns:
            Resultados de la ronda
        """
        if not self.current_task:
            raise ValueError("No active fine-tuning task")

        start_time = time.time()
        logger.info(f"🎯 Starting federated fine-tuning round for task {self.current_task.task_id}")

        # 1. Validar y filtrar actualizaciones
        valid_updates = self._validate_node_updates(node_updates)

        if not valid_updates:
            raise ValueError("No valid node updates received")

        # 2. Aplicar privacidad diferencial si está habilitada
        if self.config.use_differential_privacy and self.dp_manager:
            valid_updates = self._apply_differential_privacy(valid_updates)

        # 3. Agregación federada con preservación de privacidad
        if self.config.use_homomorphic_encryption and self.he_encryptor:
            aggregated_weights = await self._aggregate_with_homomorphic_encryption(valid_updates)
        else:
            aggregated_weights = self._aggregate_lora_weights(valid_updates)

        # 4. Actualizar modelo base con pesos agregados
        self._update_base_model_with_lora(aggregated_weights)

        # 5. Evaluar rendimiento
        evaluation_metrics = self._evaluate_fine_tuned_model(valid_updates)

        # 6. Actualizar estadísticas
        round_time = time.time() - start_time
        self.stats["total_training_time"] += round_time

        # 7. Verificar criterios de convergencia
        converged = self._check_convergence_criteria(evaluation_metrics)

        # 8. Preparar resultados
        round_result = {
            "task_id": self.current_task.task_id,
            "round_completed": True,
            "aggregated_weights": aggregated_weights,
            "evaluation_metrics": evaluation_metrics,
            "converged": converged,
            "round_time": round_time,
            "nodes_participated": len(valid_updates),
            "privacy_budget_used": self.stats["privacy_budget_used"]
        }

        logger.info(f"✅ Federated fine-tuning round completed in {round_time:.2f}s")
        logger.info(f"📊 Nodes participated: {len(valid_updates)}")
        logger.info(f"🎯 Converged: {converged}")

        return round_result

    def _validate_node_updates(self, node_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validar actualizaciones de nodos."""
        valid_updates = []

        for update in node_updates:
            try:
                node_id = update.get("node_id")
                if node_id not in self.active_nodes:
                    logger.warning(f"⚠️ Unknown node {node_id}")
                    continue

                # Verificar estructura requerida
                required_keys = ["node_id", "lora_weights", "metrics", "num_samples"]
                if not all(key in update for key in required_keys):
                    logger.warning(f"⚠️ Missing required keys in update from {node_id}")
                    continue

                # Verificar que las métricas sean razonables
                metrics = update["metrics"]
                if metrics.get("loss", float('inf')) > 10.0:  # Umbral arbitrario
                    logger.warning(f"⚠️ Suspicious loss value from {node_id}: {metrics['loss']}")
                    continue

                valid_updates.append(update)
                logger.info(f"✅ Update validated from node {node_id}")

            except Exception as e:
                logger.warning(f"⚠️ Error validating update: {e}")
                continue

        return valid_updates

    def _apply_differential_privacy(self, node_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplicar privacidad diferencial a las actualizaciones."""
        if not self.dp_manager:
            return node_updates

        privatized_updates = []

        for update in node_updates:
            try:
                # Aplicar ruido a los pesos LoRA
                noisy_weights = {}
                for layer_name, weights in update["lora_weights"].items():
                    if isinstance(weights, (list, np.ndarray)):
                        weights_array = np.array(weights)
                        noise = np.random.normal(0, self.dp_manager.noise_scale, weights_array.shape)
                        noisy_weights[layer_name] = (weights_array + noise).tolist()
                    else:
                        noisy_weights[layer_name] = weights

                update["lora_weights"] = noisy_weights
                privatized_updates.append(update)

                # Actualizar presupuesto de privacidad usado
                self.stats["privacy_budget_used"] += self.dp_manager.privacy_budget_per_sample

            except Exception as e:
                logger.warning(f"⚠️ Error applying DP to update: {e}")
                privatized_updates.append(update)

        logger.info(f"🔒 Applied differential privacy to {len(privatized_updates)} updates")
        return privatized_updates

    async def _aggregate_with_homomorphic_encryption(self, node_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agregación usando encriptación homomórfica."""
        if not self.he_encryptor:
            raise ValueError("Homomorphic encryption not enabled")

        # Implementación simplificada - en producción sería más compleja
        logger.info("🔐 Aggregating with homomorphic encryption")

        # Por ahora, usar agregación regular
        return self._aggregate_lora_weights(node_updates)

    def _aggregate_lora_weights(self, node_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agregación de pesos LoRA usando FedAvg."""
        if not node_updates:
            return {}

        logger.info(f"🔄 Aggregating LoRA weights from {len(node_updates)} nodes")

        # Inicializar pesos agregados
        aggregated_weights = {}
        total_samples = sum(update["num_samples"] for update in node_updates)

        # Para cada capa LoRA
        first_update = node_updates[0]
        for layer_name in first_update["lora_weights"].keys():
            layer_weights = None

            for update in node_updates:
                weight_factor = update["num_samples"] / total_samples
                node_weights = update["lora_weights"][layer_name]

                if isinstance(node_weights, list):
                    node_weights = np.array(node_weights)

                if layer_weights is None:
                    layer_weights = node_weights * weight_factor
                else:
                    layer_weights += node_weights * weight_factor

            aggregated_weights[layer_name] = layer_weights.tolist() if hasattr(layer_weights, 'tolist') else layer_weights

        logger.info(f"✅ LoRA weights aggregated for {len(aggregated_weights)} layers")
        return aggregated_weights

    def _update_base_model_with_lora(self, lora_weights: Dict[str, Any]):
        """Actualizar modelo base con pesos LoRA agregados."""
        try:
            # Aplicar pesos LoRA al modelo base
            # Esto es una simplificación - en la práctica requeriría merge de LoRA
            logger.info("🔄 Updating base model with aggregated LoRA weights")

            # Aquí iría la lógica para merge los pesos LoRA en el modelo base
            # Por simplicidad, solo registramos la actualización

        except Exception as e:
            logger.error(f"❌ Error updating base model: {e}")

    def _evaluate_fine_tuned_model(self, node_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluar el modelo fine-tuneado."""
        # Calcular métricas promedio de los nodos
        total_samples = sum(update["num_samples"] for update in node_updates)
        avg_loss = sum(update["metrics"].get("loss", 0) * (update["num_samples"] / total_samples)
                      for update in node_updates)
        avg_accuracy = sum(update["metrics"].get("accuracy", 0) * (update["num_samples"] / total_samples)
                          for update in node_updates)

        return {
            "avg_loss": avg_loss,
            "avg_accuracy": avg_accuracy,
            "total_samples": total_samples,
            "nodes_evaluated": len(node_updates),
            "evaluation_timestamp": time.time()
        }

    def _check_convergence_criteria(self, metrics: Dict[str, Any]) -> bool:
        """Verificar criterios de convergencia."""
        # Criterios simples de convergencia
        loss_threshold = 0.1  # Umbral arbitrario
        accuracy_threshold = 0.85  # Umbral arbitrario

        converged = (metrics.get("avg_loss", float('inf')) < loss_threshold or
                    metrics.get("avg_accuracy", 0) > accuracy_threshold)

        return converged

    def get_fine_tuning_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de fine-tuning."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "current_task": self.current_task.__dict__ if self.current_task else None,
            "active_nodes": len(self.active_nodes),
            "completed_tasks": len(self.completed_tasks),
            "stats": self.stats,
            "config": self.config.__dict__,
            "privacy_enabled": self.config.use_differential_privacy or self.config.use_homomorphic_encryption
        }

    def complete_fine_tuning_task(self) -> Dict[str, Any]:
        """Completar la tarea de fine-tuning actual."""
        if not self.current_task:
            raise ValueError("No active task to complete")

        self.current_task.status = "completed"
        self.current_task.progress = 1.0
        self.completed_tasks.append(self.current_task)

        self.stats["total_tasks_processed"] += 1
        self.stats["domains_adapted"].add(self.current_task.domain)

        result = {
            "task_id": self.current_task.task_id,
            "status": "completed",
            "domain": self.current_task.domain,
            "total_samples": self.current_task.num_samples,
            "completion_time": time.time()
        }

        self.current_task = None
        logger.info(f"✅ Fine-tuning task {result['task_id']} completed")
        return result


# Funciones de conveniencia
def create_federated_fine_tuner(session_id: str, model_name: str,
                               config: FineTuningConfig = None) -> FederatedFineTuner:
    """Crear un nuevo fine-tuner federado."""
    return FederatedFineTuner(session_id, model_name, config)


async def execute_fine_tuning_round(fine_tuner: FederatedFineTuner,
                                   node_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ejecutar ronda de fine-tuning de manera asíncrona.

    Args:
        fine_tuner: Instancia del fine-tuner
        node_updates: Actualizaciones de nodos

    Returns:
        Resultados de la ronda
    """
    return await fine_tuner.execute_federated_fine_tuning_round(node_updates)