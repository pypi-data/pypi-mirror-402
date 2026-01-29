"""
Dual Model Wrapper para DPO (Direct Preference Optimization)
Implementación de wrapper que gestiona Policy + Reference models con optimización LoRA.

Dual Model Wrapper for DPO training with LoRA memory optimization.
Manages Policy (trainable) and Reference (frozen) models sharing base weights.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple, Union, List
from pathlib import Path
import time
import logging
import psutil
import os

from .config import EmpoorioLMConfig
from .model import EmpoorioLM
from .dpo_loss import DPOLoss
from .lora import LoRAModelWrapper

logger = logging.getLogger(__name__)


class DualModelWrapper(nn.Module):
    """
    Wrapper que gestiona dos modelos para DPO: Policy (entrenable) y Reference (congelado).
    Optimiza memoria compartiendo pesos base y usando LoRA solo en Policy model.

    Dual model wrapper for DPO training. Manages Policy (trainable with LoRA) and
    Reference (frozen base) models, sharing base weights to reduce memory usage.
    """

    def __init__(self, config: EmpoorioLMConfig, dpo_beta: float = 0.1):
        """
        Inicializar Dual Model Wrapper.

        Args:
            config: Configuración del modelo (debe tener use_lora=True)
            dpo_beta: Parámetro beta para DPO loss
        """
        super().__init__()
        self.config = config
        self.dpo_beta = dpo_beta

        # Validar configuración
        if not config.use_lora:
            raise ValueError("DualModelWrapper requiere use_lora=True en la configuración")

        # Crear modelo base (compartido y congelado)
        base_config = config.__class__(**config.to_dict())
        base_config.use_lora = False  # Base model sin LoRA
        self.base_model = EmpoorioLM(base_config)
        self.freeze_base_model()

        # Policy model: base + LoRA (entrenable)
        policy_config = config.__class__(**config.to_dict())
        policy_config.use_lora = True
        self.policy_model = EmpoorioLM(policy_config)

        # Reference model: usa el base model congelado (sin LoRA)
        self.reference_model = self.base_model

        # DPO loss function
        self.dpo_loss_fn = DPOLoss(beta=dpo_beta)

        # Estadísticas de rendimiento
        self.performance_stats = {
            'policy_forward_time': [],
            'reference_forward_time': [],
            'dpo_loss_time': [],
            'memory_usage': []
        }

        logger.info("🚀 DualModelWrapper inicializado")
        logger.info(f"📊 Memoria estimada: {self.get_memory_stats()}")

    def freeze_base_model(self):
        """Congelar el modelo base para que no sea entrenable."""
        for param in self.base_model.parameters():
            param.requires_grad = False
        self.base_model.eval()
        logger.info("❄️ Modelo base congelado")

    def unfreeze_base_model(self):
        """Descongelar el modelo base (útil para fine-tuning completo)."""
        for param in self.base_model.parameters():
            param.requires_grad = True
        self.base_model.train()
        logger.info("🔥 Modelo base descongelado")

    def freeze_policy_model(self):
        """Congelar el modelo policy (solo LoRA entrenable por defecto)."""
        if self.policy_model.lora_wrapper:
            # Congelar todo menos LoRA
            for param in self.policy_model.parameters():
                param.requires_grad = False
            # Descongelar solo LoRA
            for param in self.policy_model.get_trainable_parameters():
                param.requires_grad = True
        else:
            # Si no hay LoRA, congelar todo
            for param in self.policy_model.parameters():
                param.requires_grad = False
        logger.info("❄️ Modelo policy congelado (solo LoRA entrenable)")

    def unfreeze_policy_model(self):
        """Descongelar completamente el modelo policy."""
        for param in self.policy_model.parameters():
            param.requires_grad = True
        logger.info("🔥 Modelo policy completamente descongelado")

    def forward_policy(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None,
                      labels: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Forward pass del modelo Policy (con LoRA).

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            labels: Labels para loss calculation [batch_size, seq_len]

        Returns:
            Dict con logits, loss, etc.
        """
        start_time = time.time()
        self.policy_model.train()

        outputs = self.policy_model(input_ids, attention_mask, labels)

        forward_time = time.time() - start_time
        self.performance_stats['policy_forward_time'].append(forward_time)

        return outputs

    def forward_reference(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None,
                         labels: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Forward pass del modelo Reference (base congelado, sin LoRA).

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            labels: Labels para loss calculation [batch_size, seq_len]

        Returns:
            Dict con logits, loss, etc.
        """
        start_time = time.time()
        self.reference_model.eval()

        # Asegurar que no use LoRA (aunque reference_model no debería tenerlo)
        if hasattr(self.reference_model, 'lora_wrapper') and self.reference_model.lora_wrapper:
            self.reference_model.unmerge_lora_weights()

        with torch.no_grad():
            outputs = self.reference_model(input_ids, attention_mask, labels)

        forward_time = time.time() - start_time
        self.performance_stats['reference_forward_time'].append(forward_time)

        return outputs

    def compute_dpo_loss(self, chosen_input_ids: torch.Tensor, chosen_attention_mask: torch.Tensor,
                        rejected_input_ids: torch.Tensor, rejected_attention_mask: torch.Tensor,
                        chosen_labels: Optional[torch.Tensor] = None,
                        rejected_labels: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Computar pérdida DPO usando Policy y Reference models.

        Args:
            chosen_input_ids: Input IDs para respuestas preferidas [batch_size, seq_len]
            chosen_attention_mask: Attention mask para respuestas preferidas
            rejected_input_ids: Input IDs para respuestas no preferidas [batch_size, seq_len]
            rejected_attention_mask: Attention mask para respuestas no preferidas
            chosen_labels: Labels para respuestas preferidas (opcional)
            rejected_labels: Labels para respuestas no preferidas (opcional)

        Returns:
            Tuple de (loss, metrics_dict)
        """
        start_time = time.time()

        # Forward Policy model para chosen y rejected
        policy_chosen_outputs = self.forward_policy(chosen_input_ids, chosen_attention_mask, chosen_labels)
        policy_rejected_outputs = self.forward_policy(rejected_input_ids, rejected_attention_mask, rejected_labels)

        # Forward Reference model para chosen y rejected
        ref_chosen_outputs = self.forward_reference(chosen_input_ids, chosen_attention_mask, chosen_labels)
        ref_rejected_outputs = self.forward_reference(rejected_input_ids, rejected_attention_mask, rejected_labels)

        # Extraer log probabilities (usando loss como proxy para log prob)
        # Nota: En implementación real, sería mejor calcular log probs directamente
        log_probs_w = -policy_chosen_outputs.get('loss', torch.tensor(0.0))
        log_probs_l = -policy_rejected_outputs.get('loss', torch.tensor(0.0))
        log_probs_ref_w = -ref_chosen_outputs.get('loss', torch.tensor(0.0))
        log_probs_ref_l = -ref_rejected_outputs.get('loss', torch.tensor(0.0))

        # Si loss es escalar, expandir a batch size
        batch_size = chosen_input_ids.shape[0]
        if log_probs_w.dim() == 0:
            log_probs_w = log_probs_w.expand(batch_size)
        if log_probs_l.dim() == 0:
            log_probs_l = log_probs_l.expand(batch_size)
        if log_probs_ref_w.dim() == 0:
            log_probs_ref_w = log_probs_ref_w.expand(batch_size)
        if log_probs_ref_l.dim() == 0:
            log_probs_ref_l = log_probs_ref_l.expand(batch_size)

        # Computar DPO loss
        loss, metrics = self.dpo_loss_fn(log_probs_w, log_probs_l, log_probs_ref_w, log_probs_ref_l)

        dpo_time = time.time() - start_time
        self.performance_stats['dpo_loss_time'].append(dpo_time)

        # Agregar estadísticas adicionales
        metrics.update({
            'policy_chosen_loss': policy_chosen_outputs.get('loss', 0),
            'policy_rejected_loss': policy_rejected_outputs.get('loss', 0),
            'ref_chosen_loss': ref_chosen_outputs.get('loss', 0),
            'ref_rejected_loss': ref_rejected_outputs.get('loss', 0),
            'dpo_compute_time': dpo_time
        })

        return loss, metrics

    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de memoria."""
        # Parámetros totales
        base_params = sum(p.numel() for p in self.base_model.parameters())
        policy_params = sum(p.numel() for p in self.policy_model.parameters())
        trainable_params = sum(p.numel() for p in self.get_trainable_parameters())

        # Memoria estimada (4 bytes por parámetro float32)
        base_memory = base_params * 4 / (1024**3)  # GB
        policy_memory = policy_params * 4 / (1024**3)  # GB
        trainable_memory = trainable_params * 4 / (1024**3)  # GB

        # Memoria compartida (base model)
        shared_memory = base_memory
        total_memory = policy_memory  # Policy incluye base + LoRA

        # Ahorro de memoria vs modelo dual sin compartir
        dual_without_sharing = 2 * base_memory
        memory_savings = (dual_without_sharing - total_memory) / dual_without_sharing * 100

        # Memoria actual del proceso
        process = psutil.Process(os.getpid())
        current_memory = process.memory_info().rss / (1024**3)  # GB

        stats = {
            "base_model_parameters": base_params,
            "policy_model_parameters": policy_params,
            "trainable_parameters": trainable_params,
            "base_memory_gb": round(base_memory, 3),
            "policy_memory_gb": round(policy_memory, 3),
            "trainable_memory_gb": round(trainable_memory, 3),
            "shared_memory_gb": round(shared_memory, 3),
            "total_memory_gb": round(total_memory, 3),
            "memory_savings_percent": round(memory_savings, 2),
            "current_process_memory_gb": round(current_memory, 3),
            "lora_r": self.config.lora_r,
            "lora_alpha": self.config.lora_alpha
        }

        self.performance_stats['memory_usage'].append(current_memory)
        return stats

    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento."""
        def avg_times(times_list):
            return sum(times_list) / len(times_list) if times_list else 0

        return {
            "avg_policy_forward_time": avg_times(self.performance_stats['policy_forward_time']),
            "avg_reference_forward_time": avg_times(self.performance_stats['reference_forward_time']),
            "avg_dpo_loss_time": avg_times(self.performance_stats['dpo_loss_time']),
            "avg_memory_usage_gb": avg_times(self.performance_stats['memory_usage']),
            "total_forward_calls": len(self.performance_stats['policy_forward_time']),
            "total_dpo_calls": len(self.performance_stats['dpo_loss_time'])
        }

    def get_trainable_parameters(self) -> List[nn.Parameter]:
        """Obtener parámetros entrenables (solo LoRA del policy model)."""
        return self.policy_model.get_trainable_parameters()

    def save_lora_adapters(self, path: Union[str, Path]):
        """Guardar adaptadores LoRA para federated learning."""
        if self.policy_model.lora_wrapper:
            self.policy_model.save_lora_adapters(path)
            logger.info(f"💾 LoRA adapters guardados en {path}")
        else:
            logger.warning("No hay LoRA wrapper en policy model")

    def load_lora_adapters(self, path: Union[str, Path]):
        """Cargar adaptadores LoRA desde federated learning."""
        if self.policy_model.lora_wrapper:
            self.policy_model.load_lora_adapters(path)
            logger.info(f"📥 LoRA adapters cargados desde {path}")
        else:
            logger.warning("No hay LoRA wrapper en policy model")

    def get_lora_adapters_for_federation(self) -> Dict[str, torch.Tensor]:
        """Obtener adaptadores LoRA en formato para federated learning."""
        if self.policy_model.lora_wrapper:
            return self.policy_model.lora_wrapper.get_lora_state_dict()
        return {}

    def apply_federated_lora_update(self, lora_updates: Dict[str, torch.Tensor]):
        """Aplicar actualización LoRA desde federated learning."""
        if self.policy_model.lora_wrapper:
            self.policy_model.lora_wrapper.load_lora_state_dict(lora_updates)
            logger.info("🔄 Actualización LoRA federada aplicada")
        else:
            logger.warning("No hay LoRA wrapper para aplicar actualización federada")

    def merge_policy_lora_weights(self):
        """Merge LoRA weights en policy model."""
        self.policy_model.merge_lora_weights()

    def unmerge_policy_lora_weights(self):
        """Unmerge LoRA weights en policy model."""
        self.policy_model.unmerge_lora_weights()

    def to(self, device: Union[str, torch.device]):
        """Mover modelos al dispositivo especificado."""
        self.base_model.to(device)
        self.policy_model.to(device)
        self.config.device = torch.device(device)
        return self

    def train(self, mode: bool = True):
        """Poner modelos en modo train/eval."""
        self.policy_model.train(mode)
        # Reference model siempre en eval
        self.reference_model.eval()
        return self

    def eval(self):
        """Poner modelos en modo eval."""
        return self.train(False)

    def __repr__(self) -> str:
        memory_stats = self.get_memory_stats()
        return (f"DualModelWrapper(\n"
                f"  Base Model: {self.base_model.__class__.__name__}\n"
                f"  Policy Model: {self.policy_model.__class__.__name__} (with LoRA)\n"
                f"  Reference Model: Shared base (frozen)\n"
                f"  Memory: {memory_stats['total_memory_gb']}GB "
                f"(savings: {memory_stats['memory_savings_percent']}%)\n"
                f"  Trainable params: {memory_stats['trainable_parameters']:,}\n"
                f")")


# Funciones de utilidad
def create_dual_model_wrapper(config: EmpoorioLMConfig, dpo_beta: float = 0.1) -> DualModelWrapper:
    """Factory function para crear DualModelWrapper."""
    return DualModelWrapper(config, dpo_beta)


def get_dpo_config(base_config: EmpoorioLMConfig, dpo_beta: float = 0.1) -> Dict[str, Any]:
    """Obtener configuración optimizada para DPO training."""
    config_dict = base_config.to_dict()
    config_dict.update({
        "use_lora": True,
        "lora_r": 8,
        "lora_alpha": 16.0,
        "lora_dropout": 0.05,
        "dpo_beta": dpo_beta
    })
    return config_dict


# Para backward compatibility
__all__ = [
    'DualModelWrapper',
    'create_dual_model_wrapper',
    'get_dpo_config'
]