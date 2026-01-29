"""

Emergency Reset - Sistema de recuperación automática para model drift.

Monitorea entropía y estabilidad del modelo, detecta drift y activa

recuperación automática a estados estables.

"""

import torch

import torch.nn as nn

import torch.nn.functional as F

from typing import Dict, List, Optional, Any, Union, Callable

import logging

import numpy as np

from datetime import datetime, timedelta

from collections import deque

from ..core.logging import get_logger

logger = get_logger(__name__)


class DriftMetrics:

    """Métricas de drift del modelo."""

    def __init__(self):

        self.entropy_history: deque = deque(maxlen=1000)

        self.stability_scores: deque = deque(maxlen=100)

        self.output_distributions: deque = deque(maxlen=100)

        self.drift_detected: bool = False

        self.last_reset_time: Optional[datetime] = None

        self.reset_count: int = 0


class EmergencyReset:

    """

    Sistema de recuperación automática para model drift.

    Monitorea entropía de outputs y estabilidad para detectar drift

    y activa recuperación automática.

    """

    def __init__(

        self,

        model: nn.Module,

        entropy_threshold: float = 2.0,  # Umbral de entropía alta

        stability_threshold: float = 0.8,  # Umbral de estabilidad baja

        reset_cooldown_minutes: int = 30,  # Cooldown entre resets

        max_resets_per_hour: int = 3,

        device: str = "cuda" if torch.cuda.is_available() else "cpu"

    ):

        self.model = model

        self.device = device

        self.entropy_threshold = entropy_threshold

        self.stability_threshold = stability_threshold

        self.reset_cooldown = timedelta(minutes=reset_cooldown_minutes)

        self.max_resets_per_hour = max_resets_per_hour

        # Estado de monitoreo

        self.metrics = DriftMetrics()

        # Estado estable guardado

        self.stable_state: Optional[Dict[str, torch.Tensor]] = None

        # Callbacks

        self.reset_callbacks: List[Callable] = []

        # Estadísticas

        self.stats = {

            "total_monitoring_calls": 0,

            "drift_events": 0,

            "successful_resets": 0,

            "failed_resets": 0,

            "false_positives": 0

        }

        logger.info(f"🚨 EmergencyReset inicializado: entropy_threshold={entropy_threshold}, stability_threshold={stability_threshold}")

    def monitor_outputs(self, outputs: torch.Tensor, inputs: Optional[torch.Tensor] = None) -> Dict[str, Any]:

        """

        Monitorear outputs del modelo para detectar drift.

        Args:

            outputs: Outputs del modelo [batch_size, seq_len, vocab_size]

            inputs: Inputs correspondientes (opcional)

        Returns:

            Resultados del monitoreo

        """

        self.stats["total_monitoring_calls"] += 1

        # Calcular entropía

        entropy = self._calculate_entropy(outputs)

        self.metrics.entropy_history.append(entropy)

        # Calcular estabilidad

        stability = self._calculate_stability(outputs)

        self.metrics.stability_scores.append(stability)

        # Almacenar distribución de outputs

        output_dist = self._extract_output_distribution(outputs)

        self.metrics.output_distributions.append(output_dist)

        # Detectar drift

        drift_detected = self._detect_drift(entropy, stability)

        monitoring_result = {

            "entropy": entropy,

            "stability": stability,

            "drift_detected": drift_detected,

            "entropy_trend": self._calculate_entropy_trend(),

            "stability_trend": self._calculate_stability_trend(),

            "should_reset": self._should_trigger_reset(drift_detected)

        }

        if drift_detected:

            self.metrics.drift_detected = True

            self.stats["drift_events"] += 1

            logger.warning(f"⚠️ Drift detectado: entropy={entropy:.4f}, stability={stability:.4f}")

            if monitoring_result["should_reset"]:

                success = self.trigger_emergency_reset()

                monitoring_result["reset_triggered"] = success

        return monitoring_result

    def _calculate_entropy(self, outputs: torch.Tensor) -> float:

        """Calcular entropía promedio de los outputs."""

        # Para secuencias, calcular entropía por token y promediar

        if len(outputs.shape) == 3:  # [batch_size, seq_len, vocab_size]

            probs = F.softmax(outputs, dim=-1)

            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)  # [batch_size, seq_len]

            avg_entropy = entropy.mean().item()

        else:

            probs = F.softmax(outputs, dim=-1)

            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)

            avg_entropy = entropy.mean().item()

        return avg_entropy

    def _calculate_stability(self, outputs: torch.Tensor) -> float:

        """Calcular estabilidad de los outputs."""

        if len(self.metrics.output_distributions) < 2:

            return 1.0  # Estabilidad máxima si no hay historial

        # Comparar con distribución anterior

        current_dist = self._extract_output_distribution(outputs)

        previous_dist = self.metrics.output_distributions[-1]

        # Calcular similitud coseno entre distribuciones

        stability = F.cosine_similarity(

            current_dist.unsqueeze(0),

            previous_dist.unsqueeze(0),

            dim=-1

        ).item()

        return stability

    def _extract_output_distribution(self, outputs: torch.Tensor) -> torch.Tensor:

        """Extraer distribución representativa de outputs."""

        # Promedio de logits normalizados

        if len(outputs.shape) == 3:

            dist = outputs.mean(dim=1)  # [batch_size, vocab_size]

        else:

            dist = outputs

        # Normalizar

        dist = F.normalize(dist.mean(dim=0), p=2, dim=-1)  # [vocab_size]

        return dist

    def _detect_drift(self, current_entropy: float, current_stability: float) -> bool:

        """Detectar si hay drift basado en entropía y estabilidad."""

        entropy_drift = current_entropy > self.entropy_threshold

        stability_drift = current_stability < self.stability_threshold

        return entropy_drift or stability_drift

    def _calculate_entropy_trend(self) -> float:

        """Calcular tendencia de entropía."""

        if len(self.metrics.entropy_history) < 10:

            return 0.0

        recent = list(self.metrics.entropy_history)[-10:]

        # Tendencia simple: diferencia entre promedio reciente y anterior

        mid = len(recent) // 2

        recent_avg = np.mean(recent[mid:])

        older_avg = np.mean(recent[:mid])

        trend = recent_avg - older_avg

        return trend

    def _calculate_stability_trend(self) -> float:

        """Calcular tendencia de estabilidad."""

        if len(self.metrics.stability_scores) < 10:

            return 0.0

        recent = list(self.metrics.stability_scores)[-10:]

        mid = len(recent) // 2

        recent_avg = np.mean(recent[mid:])

        older_avg = np.mean(recent[:mid])

        trend = recent_avg - older_avg  # Positivo = más estable

        return trend

    def _should_trigger_reset(self, drift_detected: bool) -> bool:

        """Determinar si se debe activar reset de emergencia."""

        if not drift_detected:

            return False

        # Verificar cooldown

        if self.metrics.last_reset_time is not None:

            time_since_reset = datetime.now() - self.metrics.last_reset_time

            if time_since_reset < self.reset_cooldown:

                return False

        # Verificar límite de resets por hora

        recent_resets = self._count_recent_resets()

        if recent_resets >= self.max_resets_per_hour:

            return False

        # Verificar tendencias

        entropy_trend = self._calculate_entropy_trend()

        stability_trend = self._calculate_stability_trend()

        # Activar si tendencias negativas y drift detectado

        should_reset = entropy_trend > 0.1 or stability_trend < -0.1

        return should_reset

    def _count_recent_resets(self) -> int:

        """Contar resets en la última hora."""

        # En implementación real, trackear timestamps de resets

        # Por simplicidad, usar contador

        return 0  # Placeholder

    def trigger_emergency_reset(self) -> bool:

        """

        Activar reset de emergencia.

        Returns:

            Éxito del reset

        """

        logger.warning("🚨 Activando reset de emergencia")

        try:

            # Guardar estado actual como stable si no existe

            if self.stable_state is None:

                self.save_stable_state()

            # Resetear a estado estable

            success = self.reset_to_stable_state()

            if success:

                self.metrics.last_reset_time = datetime.now()

                self.metrics.reset_count += 1

                self.stats["successful_resets"] += 1

                # Ejecutar callbacks

                for callback in self.reset_callbacks:

                    try:

                        callback()

                    except Exception as e:

                        logger.error(f"Error en callback de reset: {e}")

                logger.info("✅ Reset de emergencia completado exitosamente")

            else:

                self.stats["failed_resets"] += 1

                logger.error("❌ Reset de emergencia falló")

            return success

        except Exception as e:

            logger.error(f"❌ Error en reset de emergencia: {e}")

            self.stats["failed_resets"] += 1

            return False

    def save_stable_state(self):

        """Guardar estado actual como estado estable."""

        logger.info("💾 Guardando estado estable")

        self.stable_state = {}

        for name, param in self.model.named_parameters():

            self.stable_state[name] = param.data.clone()

        logger.info(f"✅ Estado estable guardado con {len(self.stable_state)} parámetros")

    def reset_to_stable_state(self) -> bool:

        """

        Resetear modelo a estado estable.

        Returns:

            Éxito del reset

        """

        if self.stable_state is None:

            logger.error("❌ No hay estado estable guardado")

            return False

        logger.info("🔄 Reseteando a estado estable")

        try:

            with torch.no_grad():

                for name, param in self.model.named_parameters():

                    if name in self.stable_state:

                        param.copy_(self.stable_state[name])

            # Resetear métricas

            self.metrics.drift_detected = False

            logger.info("✅ Reset a estado estable completado")

            return True

        except Exception as e:

            logger.error(f"❌ Error reseteando a estado estable: {e}")

            return False

    def add_reset_callback(self, callback: Callable):

        """Agregar callback para eventos de reset."""

        self.reset_callbacks.append(callback)

    def get_drift_stats(self) -> Dict[str, Any]:

        """Obtener estadísticas de drift."""

        return {

            "total_monitoring_calls": self.stats["total_monitoring_calls"],

            "drift_events": self.stats["drift_events"],

            "successful_resets": self.stats["successful_resets"],

            "failed_resets": self.stats["failed_resets"],

            "current_entropy": self.metrics.entropy_history[-1] if self.metrics.entropy_history else None,

            "current_stability": self.metrics.stability_scores[-1] if self.metrics.stability_scores else None,

            "drift_detected": self.metrics.drift_detected,

            "last_reset_time": self.metrics.last_reset_time.isoformat() if self.metrics.last_reset_time else None,

            "reset_count": self.metrics.reset_count,

            "stable_state_saved": self.stable_state is not None

        }

    def manual_reset(self) -> bool:

        """Reset manual (para debugging/testing)."""

        logger.info("🔧 Reset manual activado")

        return self.trigger_emergency_reset()


def create_emergency_reset(

    model: nn.Module,

    entropy_threshold: float = 2.0,

    stability_threshold: float = 0.8,

    reset_cooldown_minutes: int = 30,

    max_resets_per_hour: int = 3,

    device: str = "cuda" if torch.cuda.is_available() else "cpu"

) -> EmergencyReset:

    """

    Factory function para crear sistema de emergency reset.

    Args:

        model: Modelo a monitorear

        entropy_threshold: Umbral de entropía

        stability_threshold: Umbral de estabilidad

        reset_cooldown_minutes: Cooldown entre resets

        max_resets_per_hour: Máximo resets por hora

        device: Dispositivo

    Returns:

        Sistema configurado

    """

    return EmergencyReset(

        model=model,

        entropy_threshold=entropy_threshold,

        stability_threshold=stability_threshold,

        reset_cooldown_minutes=reset_cooldown_minutes,

        max_resets_per_hour=max_resets_per_hour,

        device=device

    )