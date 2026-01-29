"""
AdamW Optimizer integrado con sistema federado - FASE REAL-5
Implementa optimizador AdamW completo con scheduler, gradient clipping,
gestión de estado y adaptación para contexto federado con TenSEAL.
"""

import logging
import math
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json

import torch
import torch.nn as nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    ts = None

from ..core.logging import get_logger
# TenSEAL imports are handled in __init__.py
from . import TENSEAL_AVAILABLE as TENSEAL_AVAILABLE_IN_OPTIMIZER
if TENSEAL_AVAILABLE_IN_OPTIMIZER:
    from . import TenSEALEncryptor, TenSEALConfig
else:
    TenSEALEncryptor = None
    TenSEALConfig = None

logger = get_logger(__name__)


@dataclass
class AdamWConfig:
    """Configuración optimizada para AdamW en transformers."""
    lr: float = 5e-5  # Learning rate optimizado para transformers
    betas: Tuple[float, float] = (0.9, 0.999)  # Beta1, Beta2 estándar
    eps: float = 1e-8  # Epsilon para estabilidad numérica
    weight_decay: float = 0.01  # Weight decay (L2 regularization)
    amsgrad: bool = False  # No usar AMSGrad por defecto
    maximize: bool = False  # Minimizar loss

    # Configuración específica para transformers
    correct_bias: bool = True  # Corregir bias en Adam
    no_deprecation_warning: bool = True  # Suprimir warnings de deprecación


@dataclass
class LRSchedulerConfig:
    """Configuración del Learning Rate Scheduler."""
    scheduler_type: str = "linear"  # "linear", "cosine", "polynomial"
    warmup_steps: int = 500  # Pasos de warmup
    total_steps: int = 10000  # Pasos totales de entrenamiento
    num_cycles: float = 0.5  # Para cosine annealing
    power: float = 1.0  # Para polynomial decay
    min_lr: float = 0.0  # Learning rate mínimo


@dataclass
class GradientClippingConfig:
    """Configuración para gradient clipping."""
    max_norm: float = 1.0  # Máxima norma de gradientes
    norm_type: float = 2.0  # Tipo de norma (2.0 = L2)
    clip_value: Optional[float] = None  # Clipping por valor (opcional)
    error_if_nonfinite: bool = False  # Error si gradientes no finitos


@dataclass
class FederatedAdamWConfig:
    """Configuración completa del optimizador federado."""
    adamw: AdamWConfig = field(default_factory=AdamWConfig)
    scheduler: LRSchedulerConfig = field(default_factory=LRSchedulerConfig)
    gradient_clipping: GradientClippingConfig = field(default_factory=GradientClippingConfig)

    # Configuración federada
    use_tenseal: bool = True  # Usar TenSEAL para privacidad
    tenseal_scheme: str = "ckks"  # Esquema TenSEAL
    encrypt_gradients: bool = True  # Encriptar gradientes
    encrypt_optimizer_state: bool = False  # Encriptar estado del optimizador

    # Checkpointing
    checkpoint_dir: str = "./checkpoints"
    save_optimizer_state: bool = True
    save_frequency: int = 1000  # Guardar cada N pasos


class AdamWOptimizer(Optimizer):
    """
    AdamW Optimizer optimizado para transformers.
    Implementa la variante correcta de Adam con weight decay decoupling.
    """

    def __init__(self, params, config: AdamWConfig):
        if not 0.0 <= config.lr:
            raise ValueError(f"Invalid learning rate: {config.lr}")
        if not 0.0 <= config.eps:
            raise ValueError(f"Invalid epsilon value: {config.eps}")
        if not 0.0 <= config.betas[0] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 0: {config.betas[0]}")
        if not 0.0 <= config.betas[1] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 1: {config.betas[1]}")
        if not 0.0 <= config.weight_decay:
            raise ValueError(f"Invalid weight_decay value: {config.weight_decay}")

        defaults = dict(
            lr=config.lr,
            betas=config.betas,
            eps=config.eps,
            weight_decay=config.weight_decay,
            amsgrad=config.amsgrad,
            maximize=config.maximize,
            correct_bias=config.correct_bias
        )

        super(AdamWOptimizer, self).__init__(params, defaults)

        self.config = config

    def __setstate__(self, state):
        super(AdamWOptimizer, self).__setstate__(state)
        for group in self.param_groups:
            group.setdefault('amsgrad', False)
            group.setdefault('maximize', False)
            group.setdefault('correct_bias', True)

    @torch.no_grad()
    def step(self, closure: Optional[Callable] = None) -> Optional[float]:
        """
        Realizar un paso de optimización AdamW.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            params_with_grad = []
            grads = []
            exp_avgs = []
            exp_avg_sqs = []
            max_exp_avg_sqs = []
            state_steps = []

            for p in group['params']:
                if p.grad is not None:
                    params_with_grad.append(p)
                    grads.append(p.grad)

                    state = self.state[p]
                    # Lazy state initialization
                    if len(state) == 0:
                        state['step'] = 0
                        # Exponential moving average of gradient values
                        state['exp_avg'] = torch.zeros_like(p, memory_format=torch.preserve_format)
                        # Exponential moving average of squared gradient values
                        state['exp_avg_sq'] = torch.zeros_like(p, memory_format=torch.preserve_format)
                        if group['amsgrad']:
                            # Maintains max of all exp. moving avg. of sq. grad. values
                            state['max_exp_avg_sq'] = torch.zeros_like(p, memory_format=torch.preserve_format)

                    exp_avgs.append(state['exp_avg'])
                    exp_avg_sqs.append(state['exp_avg_sq'])

                    if group['amsgrad']:
                        max_exp_avg_sqs.append(state['max_exp_avg_sq'])

                    state['step'] += 1
                    state_steps.append(state['step'])

            self._adamw_step(
                params_with_grad,
                grads,
                exp_avgs,
                exp_avg_sqs,
                max_exp_avg_sqs,
                state_steps,
                group
            )

        return loss

    def _adamw_step(self, params, grads, exp_avgs, exp_avg_sqs, max_exp_avg_sqs, state_steps, group):
        """
        Función interna para el paso AdamW.
        """
        beta1, beta2 = group['betas']

        for i, param in enumerate(params):
            grad = grads[i]
            exp_avg = exp_avgs[i]
            exp_avg_sq = exp_avg_sqs[i]
            step = state_steps[i]

            # Apply weight decay (decoupled from gradient)
            if group['weight_decay'] != 0:
                param.mul_(1 - group['lr'] * group['weight_decay'])

            # Compute bias-corrected first moment estimate
            exp_avg.mul_(beta1).add_(grad, alpha=1 - beta1)
            if group['correct_bias']:
                bias_correction1 = 1 - beta1 ** step
                exp_avg.div_(bias_correction1)

            # Compute bias-corrected second moment estimate
            exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)
            if group['correct_bias']:
                bias_correction2 = 1 - beta2 ** step
                exp_avg_sq.div_(bias_correction2)

            # Compute step size
            step_size = group['lr']

            # Compute denominator
            if group['amsgrad']:
                max_exp_avg_sq = max_exp_avg_sqs[i]
                torch.maximum(max_exp_avg_sq, exp_avg_sq, out=max_exp_avg_sq)
                denom = max_exp_avg_sq.sqrt().add_(group['eps'])
            else:
                denom = exp_avg_sq.sqrt().add_(group['eps'])

            # Update parameters
            param.addcdiv_(exp_avg, denom, value=-step_size)


class WarmupLRScheduler(_LRScheduler):
    """
    Learning Rate Scheduler con warmup y decay.
    Soporta múltiples tipos de scheduling.
    """

    def __init__(self, optimizer, config: LRSchedulerConfig, last_epoch: int = -1):
        self.config = config
        self.warmup_steps = config.warmup_steps
        self.total_steps = config.total_steps
        self.scheduler_type = config.scheduler_type
        self.num_cycles = config.num_cycles
        self.power = config.power
        self.min_lr = config.min_lr

        super(WarmupLRScheduler, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        if not self._get_lr(self.last_epoch):
            return [self.min_lr for _ in self.optimizer.param_groups]

        return self._get_lr(self.last_epoch)

    def _get_lr(self, step):
        """
        Calcular learning rate para el paso dado.
        """
        if step < self.warmup_steps:
            # Warmup phase: linear increase
            return [base_lr * (step / max(1, self.warmup_steps))
                   for base_lr in self.base_lrs]
        else:
            # Decay phase
            progress = (step - self.warmup_steps) / max(1, self.total_steps - self.warmup_steps)

            if self.scheduler_type == "linear":
                decay_factor = max(0.0, 1.0 - progress)
            elif self.scheduler_type == "cosine":
                decay_factor = max(0.0, 0.5 * (1.0 + math.cos(math.pi * self.num_cycles * 2.0 * progress)))
            elif self.scheduler_type == "polynomial":
                decay_factor = max(0.0, (1.0 - progress) ** self.power)
            else:
                raise ValueError(f"Unknown scheduler type: {self.scheduler_type}")

            return [max(self.min_lr, base_lr * decay_factor)
                   for base_lr in self.base_lrs]


class GradientClipper:
    """
    Utilidad para clipping de gradientes.
    """

    def __init__(self, config: GradientClippingConfig):
        self.config = config

    def clip_gradients(self, model: nn.Module):
        """
        Aplicar gradient clipping al modelo.
        """
        if self.config.clip_value is not None:
            # Clip by value
            for param in model.parameters():
                if param.grad is not None:
                    param.grad.data.clamp_(-self.config.clip_value, self.config.clip_value)
        else:
            # Clip by norm
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=self.config.max_norm,
                norm_type=self.config.norm_type,
                error_if_nonfinite=self.config.error_if_nonfinite
            )


@dataclass
class OptimizerState:
    """Estado completo del optimizador para checkpointing."""
    step: int = 0
    optimizer_state_dict: Dict[str, Any] = field(default_factory=dict)
    scheduler_state_dict: Dict[str, Any] = field(default_factory=dict)
    model_state_dict: Dict[str, Any] = field(default_factory=dict)
    config: FederatedAdamWConfig = field(default_factory=FederatedAdamWConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FederatedAdamWOptimizer:
    """
    Optimizador AdamW integrado con sistema federado.
    Incluye scheduler, gradient clipping, gestión de estado y TenSEAL.
    """

    def __init__(self, model: nn.Module, node_id: str, config: Optional[FederatedAdamWConfig] = None):
        self.model = model
        self.node_id = node_id
        self.config = config or FederatedAdamWConfig()

        # Componentes del optimizador
        self.optimizer = AdamWOptimizer(model.parameters(), self.config.adamw)
        self.scheduler = WarmupLRScheduler(self.optimizer, self.config.scheduler)
        self.gradient_clipper = GradientClipper(self.config.gradient_clipping)

        # Estado del optimizador
        self.current_step = 0
        self.training_stats = {
            "total_steps": 0,
            "learning_rates": [],
            "gradient_norms": [],
            "loss_values": []
        }

        # TenSEAL para privacidad federada
        self.tenseal_encryptor = None
        if self.config.use_tenseal and TENSEAL_AVAILABLE_IN_OPTIMIZER:
            tenseal_config = TenSEALConfig(scheme=self.config.tenseal_scheme)
            self.tenseal_encryptor = TenSEALEncryptor(node_id, tenseal_config)
            logger.info(f"🔐 TenSEAL encryptor initialized for federated AdamW")

        # Directorio de checkpoints
        self.checkpoint_dir = Path(self.config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🚀 FederatedAdamWOptimizer initialized for node {node_id}")

    def step(self, loss: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Realizar un paso completo de optimización.
        Incluye gradient clipping, optimizer step y scheduler step.
        """
        start_time = time.time()

        # Aplicar gradient clipping
        self.gradient_clipper.clip_gradients(self.model)

        # Calcular norma de gradientes para monitoreo
        total_norm = 0
        param_count = 0
        for p in self.model.parameters():
            if p.grad is not None:
                param_norm = p.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                param_count += 1
        total_norm = total_norm ** (1. / 2) if param_count > 0 else 0.0

        # Optimizer step
        loss_value = None
        if loss is not None:
            loss_value = loss.item()
            self.optimizer.step(closure=lambda: loss)
        else:
            self.optimizer.step()

        # Scheduler step
        self.scheduler.step()

        # Actualizar estadísticas
        self.current_step += 1
        current_lr = self.scheduler.get_last_lr()[0]

        self.training_stats["total_steps"] = self.current_step
        self.training_stats["learning_rates"].append(current_lr)
        self.training_stats["gradient_norms"].append(total_norm)
        if loss_value is not None:
            self.training_stats["loss_values"].append(loss_value)

        # Checkpoint automático
        if self.config.save_optimizer_state and self.current_step % self.config.save_frequency == 0:
            self.save_checkpoint()

        step_time = time.time() - start_time

        return {
            "step": self.current_step,
            "learning_rate": current_lr,
            "gradient_norm": total_norm,
            "loss": loss_value,
            "step_time": step_time
        }

    def get_encrypted_gradients(self) -> Dict[str, Any]:
        """
        Obtener gradientes encriptados para federated learning.
        """
        if not self.tenseal_encryptor or not self.config.encrypt_gradients:
            # Retornar gradientes sin encriptar
            gradients = {}
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    gradients[name] = param.grad.clone()
            return gradients

        # Encriptar gradientes con TenSEAL
        gradients_dict = {}
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                gradients_dict[name] = param.grad

        encrypted_gradients = self.tenseal_encryptor.encrypt_model_gradients(gradients_dict)

        logger.debug(f"🔒 Encrypted gradients for {len(gradients_dict)} parameters")
        return encrypted_gradients

    def apply_encrypted_gradients_update(self, encrypted_updates: Dict[str, Any]):
        """
        Aplicar actualizaciones de gradientes encriptados.
        """
        if not self.tenseal_encryptor or not self.config.encrypt_gradients:
            # Aplicar actualizaciones sin desencriptar
            for name, update in encrypted_updates.items():
                if name in dict(self.model.named_parameters()):
                    param = dict(self.model.named_parameters())[name]
                    if param.grad is not None:
                        param.grad.copy_(update)
            return

        # Desencriptar y aplicar actualizaciones
        decrypted_updates = self.tenseal_encryptor.decrypt_model_gradients(encrypted_updates)

        for name, update in decrypted_updates.items():
            if name in dict(self.model.named_parameters()):
                param = dict(self.model.named_parameters())[name]
                if param.grad is not None:
                    param.grad.copy_(update)

        logger.debug(f"🔓 Applied encrypted gradient updates for {len(decrypted_updates)} parameters")

    def aggregate_federated_gradients(self, encrypted_gradients_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agregar gradientes encriptados de múltiples nodos.
        """
        if not self.tenseal_encryptor:
            raise RuntimeError("TenSEAL encryptor required for federated gradient aggregation")

        aggregated_gradients = self.tenseal_encryptor.aggregate_encrypted_gradients(encrypted_gradients_list)

        logger.info(f"📊 Aggregated gradients from {len(encrypted_gradients_list)} nodes")
        return aggregated_gradients

    def save_checkpoint(self, checkpoint_path: Optional[str] = None) -> str:
        """
        Guardar checkpoint completo del optimizador.
        """
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_dir / f"optimizer_checkpoint_step_{self.current_step}.pt"

        checkpoint_path = Path(checkpoint_path)

        optimizer_state = OptimizerState(
            step=self.current_step,
            optimizer_state_dict=self.optimizer.state_dict(),
            scheduler_state_dict=self.scheduler.state_dict(),
            model_state_dict=self.model.state_dict(),
            config=self.config,
            metadata={
                "node_id": self.node_id,
                "timestamp": time.time(),
                "training_stats": self.training_stats.copy()
            }
        )

        torch.save(optimizer_state, checkpoint_path)
        logger.info(f"💾 Checkpoint saved: {checkpoint_path}")

        return str(checkpoint_path)

    def load_checkpoint(self, checkpoint_path: str) -> bool:
        """
        Cargar checkpoint del optimizador.
        """
        checkpoint_path = Path(checkpoint_path)

        if not checkpoint_path.exists():
            logger.error(f"Checkpoint not found: {checkpoint_path}")
            return False

        try:
            optimizer_state: OptimizerState = torch.load(checkpoint_path)

            # Restaurar estado
            self.optimizer.load_state_dict(optimizer_state.optimizer_state_dict)
            self.scheduler.load_state_dict(optimizer_state.scheduler_state_dict)
            self.model.load_state_dict(optimizer_state.model_state_dict)

            self.current_step = optimizer_state.step
            self.training_stats = optimizer_state.metadata.get("training_stats", self.training_stats)

            logger.info(f"📂 Checkpoint loaded: {checkpoint_path} (step {self.current_step})")
            return True

        except Exception as e:
            logger.error(f"❌ Error loading checkpoint: {e}")
            return False

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas del optimizador.
        """
        stats = {
            "node_id": self.node_id,
            "current_step": self.current_step,
            "learning_rate": self.scheduler.get_last_lr()[0] if self.current_step > 0 else self.config.adamw.lr,
            "training_stats": self.training_stats,
            "config": {
                "adamw": self.config.adamw.__dict__,
                "scheduler": self.config.scheduler.__dict__,
                "gradient_clipping": self.config.gradient_clipping.__dict__,
                "federated": {
                    "use_tenseal": self.config.use_tenseal,
                    "encrypt_gradients": self.config.encrypt_gradients,
                    "tenseal_available": TENSEAL_AVAILABLE_IN_OPTIMIZER
                }
            }
        }

        if self.tenseal_encryptor:
            stats["tenseal_stats"] = self.tenseal_encryptor.get_stats()

        return stats

    def zero_grad(self):
        """Reset gradients."""
        self.optimizer.zero_grad()

    def state_dict(self) -> Dict[str, Any]:
        """Obtener state dict completo."""
        return {
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
            "model": self.model.state_dict(),
            "step": self.current_step,
            "training_stats": self.training_stats,
            "config": self.config
        }

    def load_state_dict(self, state_dict: Dict[str, Any]):
        """Cargar state dict completo."""
        self.optimizer.load_state_dict(state_dict["optimizer"])
        self.scheduler.load_state_dict(state_dict["scheduler"])
        self.model.load_state_dict(state_dict["model"])
        self.current_step = state_dict["step"]
        self.training_stats = state_dict.get("training_stats", self.training_stats)


# Funciones de conveniencia
def create_federated_adamw_optimizer(
    model: nn.Module,
    node_id: str,
    lr: float = 5e-5,
    warmup_steps: int = 500,
    total_steps: int = 10000,
    use_tenseal: bool = True
) -> FederatedAdamWOptimizer:
    """
    Crear optimizador AdamW federado con configuración optimizada.

    Args:
        model: Modelo PyTorch
        node_id: ID del nodo federado
        lr: Learning rate base
        warmup_steps: Pasos de warmup
        total_steps: Pasos totales de entrenamiento
        use_tenseal: Usar TenSEAL para privacidad

    Returns:
        Optimizador configurado
    """
    config = FederatedAdamWConfig()

    # Configuración AdamW optimizada para transformers
    config.adamw.lr = lr
    config.adamw.weight_decay = 0.01

    # Configuración scheduler
    config.scheduler.warmup_steps = warmup_steps
    config.scheduler.total_steps = total_steps

    # Configuración federada
    config.use_tenseal = use_tenseal and TENSEAL_AVAILABLE_IN_OPTIMIZER

    return FederatedAdamWOptimizer(model, node_id, config)


def benchmark_adamw_optimizer():
    """Benchmark del optimizador AdamW."""
    logger.info("🏃 Running AdamW optimizer benchmark...")

    # Crear modelo simple para benchmark
    model = nn.Sequential(
        nn.Linear(1000, 2000),
        nn.ReLU(),
        nn.Linear(2000, 1000),
        nn.ReLU(),
        nn.Linear(1000, 10)
    )

    optimizer = create_federated_adamw_optimizer(model, "benchmark_node", use_tenseal=False)

    # Benchmark de pasos de optimización
    model.train()
    criterion = nn.CrossEntropyLoss()

    times = []
    for i in range(100):
        # Generar datos dummy
        x = torch.randn(32, 1000)
        y = torch.randint(0, 10, (32,))

        optimizer.zero_grad()

        start_time = time.time()
        output = model(x)
        loss = criterion(output, y)
        loss.backward()

        stats = optimizer.step(loss)
        step_time = time.time() - start_time

        times.append(step_time)

        if (i + 1) % 20 == 0:
            logger.info(f"Step {i+1}: Loss={loss.item():.4f}, LR={stats['learning_rate']:.6f}, Time={step_time:.4f}s")

    avg_time = sum(times) / len(times)
    logger.info(f"📊 Benchmark completed: {len(times)} steps, avg time per step: {avg_time:.4f}s")

    return {
        "steps": len(times),
        "avg_step_time": avg_time,
        "total_time": sum(times),
        "final_loss": loss.item(),
        "final_lr": stats["learning_rate"]
    }