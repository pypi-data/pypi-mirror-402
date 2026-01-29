"""
LoRA (Low-Rank Adaptation) implementation for EmpoorioLM
Implementación de LoRA para fine-tuning eficiente en DPO federado.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Union, Any
import math
from pathlib import Path
import json
import logging

from .model_config import EmpoorioLMConfig

logger = logging.getLogger(__name__)


class LoRALayer(nn.Module):
    """
    LoRA adapter layer that can be applied to any linear layer.
    Capa adaptadora LoRA que se puede aplicar a cualquier capa lineal.
    """

    def __init__(self, in_features: int, out_features: int, r: int = 8, alpha: float = 16.0,
                 dropout: float = 0.05, merge_weights: bool = True):
        super().__init__()
        self.r = r
        self.alpha = alpha
        self.dropout = dropout
        self.merge_weights = merge_weights
        self.scaling = self.alpha / self.r

        # LoRA matrices
        self.lora_A = nn.Linear(in_features, r, bias=False)
        self.lora_B = nn.Linear(r, out_features, bias=False)

        # Dropout
        self.dropout_layer = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # Initialize weights
        self.reset_parameters()

        # Training mode
        self.merged = False

    def reset_parameters(self):
        """Initialize LoRA parameters."""
        # Initialize A with random gaussian
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))

        # Initialize B with small random values instead of zeros
        nn.init.normal_(self.lora_B.weight, mean=0.0, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through LoRA adapter."""
        if self.merged:
            return x

        # Apply dropout to input
        x = self.dropout_layer(x)

        # LoRA computation: x -> A -> B -> scaling
        lora_output = self.lora_B(self.lora_A(x)) * self.scaling

        return lora_output


class LinearWithLoRA(nn.Module):
    """
    Linear layer with optional LoRA adapter.
    Capa lineal con adaptador LoRA opcional.
    """

    def __init__(self, linear_layer: nn.Linear, r: int = 8, alpha: float = 16.0,
                 dropout: float = 0.05, merge_weights: bool = True):
        super().__init__()
        self.linear = linear_layer
        self.lora = LoRALayer(
            linear_layer.in_features,
            linear_layer.out_features,
            r=r,
            alpha=alpha,
            dropout=dropout,
            merge_weights=merge_weights
        )

        # Store original weights for merging/unmerging
        self.original_weight = linear_layer.weight.data.clone()
        self.original_bias = linear_layer.bias.data.clone() if linear_layer.bias is not None else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass combining linear layer and LoRA."""
        # Base linear output
        base_output = self.linear(x)

        # LoRA output
        lora_output = self.lora(x)

        return base_output + lora_output

    def merge_weights(self):
        """Merge LoRA weights into the base linear layer."""
        if self.lora.merged:
            return

        # Compute LoRA weight update
        lora_weight = self.lora.lora_B.weight @ self.lora.lora_A.weight
        lora_weight = lora_weight * self.lora.scaling

        # Merge into base weights (lora_weight is [out_features, in_features])
        self.linear.weight.data += lora_weight

        # Mark as merged
        self.lora.merged = True

    def unmerge_weights(self):
        """Unmerge LoRA weights from the base linear layer."""
        if not self.lora.merged:
            return

        # Restore original weights
        self.linear.weight.data = self.original_weight.clone()
        if self.original_bias is not None:
            self.linear.bias.data = self.original_bias.clone()

        # Mark as unmerged
        self.lora.merged = False


class LoRAModelWrapper:
    """
    Wrapper that applies LoRA to specified modules in a model.
    Wrapper que aplica LoRA a módulos específicos en un modelo.
    """

    def __init__(self, model: nn.Module, config: EmpoorioLMConfig):
        self.model = model
        self.config = config
        self.lora_layers = {}
        self.applied_modules = []

        if config.use_lora:
            self._apply_lora_to_modules()

    def _apply_lora_to_modules(self):
        """Apply LoRA to target modules."""
        for name, module in self.model.named_modules():
            # Check if this module should have LoRA
            module_name = name.split('.')[-1]
            if module_name in self.config.lora_target_modules and isinstance(module, nn.Linear):
                # Replace with LinearWithLoRA
                parent_name = '.'.join(name.split('.')[:-1])
                attr_name = name.split('.')[-1]

                # Get parent module
                parent = self.model
                if parent_name:
                    for part in parent_name.split('.'):
                        parent = getattr(parent, part)

                # Create LoRA wrapper
                lora_layer = LinearWithLoRA(
                    module,
                    r=self.config.lora_r,
                    alpha=self.config.lora_alpha,
                    dropout=self.config.lora_dropout
                )

                # Replace the module
                setattr(parent, attr_name, lora_layer)
                self.lora_layers[name] = lora_layer
                self.applied_modules.append(name)

                logger.info(f"✅ LoRA aplicado a: {name} (r={self.config.lora_r}, alpha={self.config.lora_alpha})")

    def merge_weights(self):
        """Merge all LoRA weights into base layers."""
        for name, lora_layer in self.lora_layers.items():
            lora_layer.merge_weights()
            logger.info(f"🔀 LoRA weights merged for: {name}")

    def unmerge_weights(self):
        """Unmerge all LoRA weights from base layers."""
        for name, lora_layer in self.lora_layers.items():
            lora_layer.unmerge_weights()
            logger.info(f"🔀 LoRA weights unmerged for: {name}")

    def get_lora_state_dict(self) -> Dict[str, torch.Tensor]:
        """Get state dict containing only LoRA parameters."""
        lora_state = {}
        for name, lora_layer in self.lora_layers.items():
            lora_state[f"{name}.lora.lora_A.weight"] = lora_layer.lora.lora_A.weight
            lora_state[f"{name}.lora.lora_B.weight"] = lora_layer.lora.lora_B.weight
        return lora_state

    def load_lora_state_dict(self, state_dict: Dict[str, torch.Tensor]):
        """Load LoRA parameters from state dict."""
        for name, lora_layer in self.lora_layers.items():
            a_key = f"{name}.lora.lora_A.weight"
            b_key = f"{name}.lora.lora_B.weight"

            if a_key in state_dict:
                lora_layer.lora.lora_A.weight.data = state_dict[a_key]
            if b_key in state_dict:
                lora_layer.lora.lora_B.weight.data = state_dict[b_key]

    def save_lora_adapters(self, path: Union[str, Path]):
        """Save only LoRA adapters to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save LoRA state
        lora_state = self.get_lora_state_dict()
        torch.save(lora_state, path / "lora_adapters.bin")

        # Save config
        config_dict = {
            "lora_r": self.config.lora_r,
            "lora_alpha": self.config.lora_alpha,
            "lora_dropout": self.config.lora_dropout,
            "lora_target_modules": self.config.lora_target_modules,
            "applied_modules": self.applied_modules
        }

        with open(path / "lora_config.json", 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 LoRA adapters saved to {path}")

    def load_lora_adapters(self, path: Union[str, Path]):
        """Load LoRA adapters from disk."""
        path = Path(path)

        # Load config
        config_path = path / "lora_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            # Verify compatibility
            if config_dict["lora_r"] != self.config.lora_r:
                logger.warning(f"LoRA r mismatch: {config_dict['lora_r']} vs {self.config.lora_r}")
            if config_dict["lora_alpha"] != self.config.lora_alpha:
                logger.warning(f"LoRA alpha mismatch: {config_dict['lora_alpha']} vs {self.config.lora_alpha}")

        # Load LoRA state
        lora_path = path / "lora_adapters.bin"
        if lora_path.exists():
            lora_state = torch.load(lora_path, map_location='cpu')
            self.load_lora_state_dict(lora_state)
            logger.info(f"📥 LoRA adapters loaded from {path}")
        else:
            logger.warning(f"LoRA adapters file not found: {lora_path}")

    def get_trainable_parameters(self) -> List[nn.Parameter]:
        """Get only the LoRA parameters for training."""
        trainable_params = []
        for lora_layer in self.lora_layers.values():
            trainable_params.extend([
                lora_layer.lora.lora_A.weight,
                lora_layer.lora.lora_B.weight
            ])
        return trainable_params

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics for LoRA vs full fine-tuning."""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.get_trainable_parameters())

        # Calculate memory savings
        memory_savings = (total_params - trainable_params) / total_params * 100

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "memory_savings_percent": memory_savings,
            "applied_modules_count": len(self.applied_modules),
            "lora_r": self.config.lora_r,
            "lora_alpha": self.config.lora_alpha
        }


def apply_lora_to_model(model: nn.Module, config: EmpoorioLMConfig) -> LoRAModelWrapper:
    """
    Apply LoRA to a model with given configuration.
    Aplicar LoRA a un modelo con configuración dada.
    """
    return LoRAModelWrapper(model, config)


def create_lora_config(r: int = 8, alpha: float = 16.0, dropout: float = 0.05,
                      target_modules: List[str] = None) -> Dict[str, Any]:
    """
    Create LoRA configuration dictionary.
    Crear diccionario de configuración LoRA.
    """
    if target_modules is None:
        target_modules = ["q_proj", "k_proj", "v_proj", "out_proj"]

    return {
        "use_lora": True,
        "lora_r": r,
        "lora_alpha": alpha,
        "lora_dropout": dropout,
        "lora_target_modules": target_modules
    }


# Utility functions for federated learning
def get_lora_adapters_for_federation(lora_wrapper: LoRAModelWrapper) -> Dict[str, torch.Tensor]:
    """
    Get LoRA adapters in format suitable for federated learning.
    Obtener adaptadores LoRA en formato adecuado para aprendizaje federado.
    """
    return lora_wrapper.get_lora_state_dict()


def apply_federated_lora_update(model: nn.Module, lora_updates: Dict[str, torch.Tensor],
                               config: EmpoorioLMConfig):
    """
    Apply federated LoRA updates to model.
    Aplicar actualizaciones LoRA federadas al modelo.
    """
    wrapper = LoRAModelWrapper(model, config)
    wrapper.load_lora_state_dict(lora_updates)


# For backward compatibility
__all__ = [
    'LoRALayer',
    'LinearWithLoRA',
    'LoRAModelWrapper',
    'apply_lora_to_model',
    'create_lora_config',
    'get_lora_adapters_for_federation',
    'apply_federated_lora_update'
]