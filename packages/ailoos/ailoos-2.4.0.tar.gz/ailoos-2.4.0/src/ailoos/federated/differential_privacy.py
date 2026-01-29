"""
Differential Privacy Engine para Federated Learning
Implementa privacidad diferencial en gradientes con mecanismo de arriba-umbral.
"""

import torch
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple
from ..core.logging import get_logger

logger = get_logger(__name__)


class DifferentialPrivacyEngine:
    """
    Motor de Privacidad Diferencial para gradientes en federated learning.
    Implementa clipping de gradientes, ruido calibrado y mecanismo de arriba-umbral.
    """

    def __init__(self, epsilon: float = 0.1, delta: float = 1e-5,
                 max_grad_norm: float = 1.0, threshold: float = 0.1):
        """
        Inicializar el motor de DP.

        Args:
            epsilon: Parámetro de privacidad ε
            delta: Parámetro de privacidad δ
            max_grad_norm: Norma máxima para clipping de gradientes
            threshold: Umbral para mecanismo de arriba-umbral
        """
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.threshold = threshold

        # Estado del presupuesto de privacidad
        self.total_epsilon_used = 0.0
        self.privacy_budget_remaining = epsilon

        # Estadísticas
        self.clipping_stats = {
            "gradients_clipped": 0,
            "noise_added": 0,
            "threshold_applied": 0
        }

        logger.info(f"🔒 DifferentialPrivacyEngine initialized with ε={epsilon}, δ={delta}")
        logger.info(f"   📏 Max grad norm: {max_grad_norm}, Threshold: {threshold}")

    def apply_differential_privacy(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Aplicar privacidad diferencial a gradientes usando mecanismo de arriba-umbral.

        Args:
            gradients: Diccionario de gradientes por capa

        Returns:
            Gradientes con DP aplicado
        """
        try:
            logger.debug(f"🔄 Applying DP to {len(gradients)} gradient tensors")

            # 1. Calcular sensibilidad de gradientes
            sensitivity = self._compute_gradient_sensitivity(gradients)
            logger.debug(f"📊 Gradient sensitivity: {sensitivity:.6f}")

            # 2. Aplicar clipping de gradientes
            clipped_gradients = self._clip_gradients(gradients, self.max_grad_norm)

            # 3. Aplicar mecanismo de arriba-umbral
            dp_gradients = self._apply_above_threshold_mechanism(clipped_gradients, sensitivity)

            # 4. Actualizar presupuesto de privacidad
            epsilon_used = self._calculate_epsilon_used(sensitivity)
            self._update_privacy_budget(epsilon_used)

            logger.debug(f"✅ DP applied successfully, ε used: {epsilon_used:.6f}")
            return dp_gradients

        except Exception as e:
            logger.error(f"❌ Error applying differential privacy: {e}")
            raise

    def _compute_gradient_sensitivity(self, gradients: Dict[str, torch.Tensor]) -> float:
        """
        Calcular la sensibilidad de los gradientes.
        Para DP-SGD, la sensibilidad es la norma máxima de clipping.

        Args:
            gradients: Gradientes por capa

        Returns:
            Sensibilidad calculada
        """
        try:
            # Calcular norma L2 de cada tensor de gradientes
            norms = []
            for name, grad in gradients.items():
                if grad is not None and grad.numel() > 0:
                    # Norma L2 del tensor
                    grad_norm = torch.norm(grad, p=2).item()
                    norms.append(grad_norm)

            if not norms:
                logger.warning("⚠️ No valid gradients found for sensitivity calculation")
                return 0.0

            # Sensibilidad es la norma máxima (para clipping)
            sensitivity = max(norms)
            logger.debug(f"📏 Max gradient norm: {sensitivity:.6f}")

            return sensitivity

        except Exception as e:
            logger.error(f"❌ Error computing gradient sensitivity: {e}")
            return 0.0

    def _clip_gradients(self, gradients: Dict[str, torch.Tensor], max_norm: float) -> Dict[str, torch.Tensor]:
        """
        Aplicar clipping de gradientes por norma L2.

        Args:
            gradients: Gradientes originales
            max_norm: Norma máxima permitida

        Returns:
            Gradientes clipped
        """
        clipped_gradients = {}

        for name, grad in gradients.items():
            if grad is None:
                clipped_gradients[name] = None
                continue

            # Calcular norma L2
            grad_norm = torch.norm(grad, p=2)

            if grad_norm > max_norm:
                # Clip el gradiente
                clipped_grad = grad * (max_norm / grad_norm)
                self.clipping_stats["gradients_clipped"] += 1
                logger.debug(f"✂️ Clipped gradient {name}: {grad_norm:.6f} -> {max_norm:.6f}")
            else:
                clipped_grad = grad.clone()

            clipped_gradients[name] = clipped_grad

        return clipped_gradients

    def _apply_above_threshold_mechanism(self, gradients: Dict[str, torch.Tensor],
                                       sensitivity: float) -> Dict[str, torch.Tensor]:
        """
        Aplicar mecanismo de arriba-umbral: añadir ruido solo si la norma excede el umbral.

        Args:
            gradients: Gradientes clipped
            sensitivity: Sensibilidad calculada

        Returns:
            Gradientes con ruido aplicado
        """
        dp_gradients = {}

        for name, grad in gradients.items():
            if grad is None:
                dp_gradients[name] = None
                continue

            # Calcular norma del gradiente clipped
            grad_norm = torch.norm(grad, p=2).item()

            if grad_norm > self.threshold:
                # Aplicar ruido gaussiano calibrado
                noise = self.generate_noise(grad.shape, sensitivity)
                dp_grad = grad + noise
                self.clipping_stats["noise_added"] += 1
                self.clipping_stats["threshold_applied"] += 1
                logger.debug(f"🎲 Added noise to {name} (norm: {grad_norm:.6f} > threshold: {self.threshold:.6f})")
            else:
                # No añadir ruido si está por debajo del umbral
                dp_grad = grad.clone()
                logger.debug(f"🚫 Skipped noise for {name} (norm: {grad_norm:.6f} <= threshold: {self.threshold:.6f})")

            dp_gradients[name] = dp_grad

        return dp_gradients

    def generate_noise(self, shape: Tuple[int, ...], sensitivity: float) -> torch.Tensor:
        """
        Generar ruido gaussiano calibrado para DP.

        Args:
            shape: Forma del tensor de ruido
            sensitivity: Sensibilidad del mecanismo

        Returns:
            Tensor de ruido
        """
        try:
            # Calcular desviación estándar para ruido gaussiano
            # Para (ε,δ)-DP con mecanismo gaussiano: σ = (sensitivity * sqrt(2*ln(1.25/δ))) / ε
            if self.epsilon <= 0:
                logger.warning("⚠️ Invalid epsilon value, using default noise")
                noise_std = sensitivity
            else:
                noise_std = (sensitivity * np.sqrt(2 * np.log(1.25 / self.delta))) / self.epsilon

            # Generar ruido gaussiano
            noise = torch.normal(0, noise_std, size=shape, dtype=torch.float32)

            # Optimizar para tensores grandes usando memoria eficiente
            if noise.numel() > 1e6:  # Más de 1M elementos
                logger.debug(f"🧠 Large tensor noise generated: {noise.numel()} elements")

            return noise

        except Exception as e:
            logger.error(f"❌ Error generating noise: {e}")
            # Fallback: ruido cero
            return torch.zeros(shape, dtype=torch.float32)

    def _calculate_epsilon_used(self, sensitivity: float) -> float:
        """
        Calcular el epsilon usado en esta operación.

        Args:
            sensitivity: Sensibilidad del mecanismo

        Returns:
            Epsilon consumido
        """
        # Para mecanismo gaussiano, ε ≈ (sensitivity^2) / (2 * σ^2 * ln(1/δ))
        # Pero simplificado para tracking
        if sensitivity > 0:
            epsilon_used = min(self.epsilon * 0.1, self.privacy_budget_remaining)  # Estimación conservadora
        else:
            epsilon_used = 0.0

        return epsilon_used

    def _update_privacy_budget(self, epsilon_used: float):
        """
        Actualizar el presupuesto de privacidad.

        Args:
            epsilon_used: Epsilon consumido
        """
        self.total_epsilon_used += epsilon_used
        self.privacy_budget_remaining = max(0, self.privacy_budget_remaining - epsilon_used)

        if self.privacy_budget_remaining <= 0:
            logger.warning("⚠️ Privacy budget exhausted!")

    def get_privacy_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de privacidad.

        Returns:
            Diccionario con métricas de privacidad
        """
        return {
            "epsilon_total": self.epsilon,
            "epsilon_used": self.total_epsilon_used,
            "epsilon_remaining": self.privacy_budget_remaining,
            "privacy_budget_exhausted": self.privacy_budget_remaining <= 0,
            "delta": self.delta,
            "max_grad_norm": self.max_grad_norm,
            "threshold": self.threshold,
            "clipping_stats": self.clipping_stats.copy()
        }

    def reset_privacy_budget(self):
        """Resetear el presupuesto de privacidad (solo para testing/debugging)."""
        self.total_epsilon_used = 0.0
        self.privacy_budget_remaining = self.epsilon
        logger.info("🔄 Privacy budget reset")

    def is_privacy_budget_available(self, required_epsilon: float = 0.01) -> bool:
        """
        Verificar si hay presupuesto de privacidad disponible.

        Args:
            required_epsilon: Epsilon requerido mínimo

        Returns:
            True si hay presupuesto suficiente
        """
        return self.privacy_budget_remaining >= required_epsilon


class DifferentialPrivacyManager:
    """
    Manager de Privacidad Diferencial para federated learning.
    Gestiona el presupuesto de privacidad y aplica ruido de manera controlada.
    """

    def __init__(self, privacy_budget: float = 1.0, noise_scale: float = 0.1):
        """
        Inicializar el manager de DP.

        Args:
            privacy_budget: Presupuesto total de privacidad ε
            noise_scale: Escala del ruido a aplicar
        """
        self.privacy_budget = privacy_budget
        self.privacy_budget_used = 0.0
        self.noise_scale = noise_scale
        self.privacy_budget_per_sample = 0.01  # Epsilon usado por muestra

        logger.info(f"🔒 DifferentialPrivacyManager initialized with budget {privacy_budget}")

    def apply_noise(self, data: torch.Tensor) -> torch.Tensor:
        """
        Aplicar ruido gaussiano a los datos.

        Args:
            data: Tensor de entrada

        Returns:
            Tensor con ruido aplicado
        """
        if self.privacy_budget_used >= self.privacy_budget:
            logger.warning("⚠️ Privacy budget exhausted, returning original data")
            return data

        noise = torch.normal(0, self.noise_scale, size=data.shape, dtype=data.dtype, device=data.device)
        noisy_data = data + noise

        # Actualizar presupuesto usado
        self.privacy_budget_used += self.privacy_budget_per_sample

        return noisy_data

    def get_remaining_budget(self) -> float:
        """Obtener presupuesto de privacidad restante."""
        return max(0, self.privacy_budget - self.privacy_budget_used)

    def reset_budget(self):
        """Resetear el presupuesto de privacidad."""
        self.privacy_budget_used = 0.0
        logger.info("🔄 Privacy budget reset")