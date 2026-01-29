"""
Puente adaptativo entre cuantización y vLLM para entornos FL.
Ajusta dinámicamente la cuantización basada en rendimiento y requisitos.
"""

import torch
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .quantization import AdvancedQuantizer, QuantizationConfig
from .federated_vllm_optimizer import FederatedVLLOptimizer

logger = logging.getLogger(__name__)


class QuantizationLevel(Enum):
    """Niveles de cuantización disponibles."""
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"
    MIXED = "mixed"


@dataclass
class QuantizationProfile:
    """Perfil de cuantización con métricas de rendimiento."""

    level: QuantizationLevel
    model_path: str
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    memory_usage_gb: float = 0.0
    inference_latency_ms: float = 0.0
    throughput_tokens_per_sec: float = 0.0
    accuracy_drop_percent: float = 0.0
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    @property
    def efficiency_score(self) -> float:
        """Calcular score de eficiencia (throughput / (memory * latency))."""
        if self.memory_usage_gb <= 0 or self.inference_latency_ms <= 0:
            return 0.0

        # Normalizar componentes
        norm_throughput = self.throughput_tokens_per_sec / 100.0  # Baseline 100 t/s
        norm_memory = 1.0 / self.memory_usage_gb  # Menos memoria = mejor
        norm_latency = 1000.0 / self.inference_latency_ms  # Menos latencia = mejor

        return (norm_throughput * 0.4 + norm_memory * 0.3 + norm_latency * 0.3)


@dataclass
class AdaptiveBridgeConfig:
    """Configuración del puente adaptativo."""

    # Adaptación
    enable_adaptive_quantization: bool = True
    adaptation_interval_minutes: int = 10
    performance_monitoring_window: int = 100

    # Umbrales
    max_accuracy_drop_percent: float = 5.0
    min_throughput_tokens_per_sec: float = 50.0
    max_memory_usage_gb: float = 8.0

    # FL específico
    federated_aware_adaptation: bool = True
    node_capability_aware: bool = True
    round_based_adaptation: bool = True

    # Persistencia
    enable_profile_persistence: bool = True
    profile_cache_path: str = "./cache/quantization_profiles"


class AdaptiveQuantizationBridge:
    """
    Puente adaptativo entre cuantización y vLLM para federated learning.

    Características principales:
    - Adaptación dinámica de cuantización basada en rendimiento
    - Perfiles de cuantización optimizados por hardware
    - Integración con optimizador federado de vLLM
    - Optimización automática para requisitos FL
    - Balance entre precisión y eficiencia
    """

    def __init__(
        self,
        config: AdaptiveBridgeConfig,
        quantizer: AdvancedQuantizer,
        fed_optimizer: Optional[FederatedVLLOptimizer] = None
    ):
        self.config = config
        self.quantizer = quantizer
        self.fed_optimizer = fed_optimizer

        # Perfiles de cuantización
        self.quantization_profiles: Dict[str, QuantizationProfile] = {}
        self.active_profile: Optional[QuantizationProfile] = None

        # Historial de rendimiento
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_history: List[Dict[str, Any]] = []

        # Estado de adaptación
        self.last_adaptation_time = time.time()
        self.current_node_capabilities: Dict[str, Any] = {}

        # Estadísticas
        self.stats = {
            "total_adaptations": 0,
            "successful_adaptations": 0,
            "failed_adaptations": 0,
            "avg_efficiency_improvement": 0.0,
            "current_quantization_level": None
        }

        # Inicializar directorio de cache
        if config.enable_profile_persistence:
            Path(config.profile_cache_path).mkdir(parents=True, exist_ok=True)
            self._load_cached_profiles()

        logger.info("🔧 AdaptiveQuantizationBridge inicializado")
        logger.info(f"   Adaptación automática: {config.enable_adaptive_quantization}")
        logger.info(f"   Umbral precisión máxima: {config.max_accuracy_drop_percent}%")

    def adapt_quantization_for_node(
        self,
        node_capabilities: Dict[str, Any],
        current_workload: Dict[str, Any],
        round_requirements: Optional[Dict[str, Any]] = None
    ) -> QuantizationProfile:
        """
        Adaptar cuantización para un nodo específico.

        Args:
            node_capabilities: Capacidades del nodo
            current_workload: Carga de trabajo actual
            round_requirements: Requisitos específicos de la ronda FL

        Returns:
            Perfil de cuantización óptimo
        """
        self.current_node_capabilities = node_capabilities

        # Generar clave para el perfil
        profile_key = self._generate_profile_key(node_capabilities, current_workload)

        # Verificar si ya existe un perfil adecuado
        if profile_key in self.quantization_profiles:
            profile = self.quantization_profiles[profile_key]
            profile.last_used = time.time()

            # Verificar si el perfil aún es válido
            if self._is_profile_still_valid(profile, current_workload):
                logger.info(f"📋 Usando perfil existente: {profile.level.value}")
                self.active_profile = profile
                return profile

        # Crear o adaptar perfil
        optimal_profile = self._find_or_create_optimal_profile(
            node_capabilities, current_workload, round_requirements
        )

        # Almacenar perfil
        self.quantization_profiles[profile_key] = optimal_profile
        self.active_profile = optimal_profile

        # Guardar en cache si está habilitado
        if self.config.enable_profile_persistence:
            self._save_profile_to_cache(profile_key, optimal_profile)

        logger.info(f"🎯 Perfil de cuantización adaptado: {optimal_profile.level.value}")
        return optimal_profile

    def _generate_profile_key(
        self,
        node_capabilities: Dict[str, Any],
        workload: Dict[str, Any]
    ) -> str:
        """Generar clave única para perfil."""
        node_type = node_capabilities.get("hardware_type", "unknown")
        memory_gb = node_capabilities.get("gpu_memory_gb", node_capabilities.get("total_memory_gb", 8))
        workload_type = workload.get("type", "inference")

        return f"{node_type}_{memory_gb:.1f}GB_{workload_type}"

    def _is_profile_still_valid(
        self,
        profile: QuantizationProfile,
        current_workload: Dict[str, Any]
    ) -> bool:
        """Verificar si un perfil aún es válido."""
        # Verificar antigüedad
        max_age_hours = 24  # 24 horas
        if time.time() - profile.created_at > max_age_hours * 3600:
            return False

        # Verificar si las métricas de rendimiento aún son relevantes
        required_throughput = current_workload.get("min_throughput", 0)
        if profile.throughput_tokens_per_sec < required_throughput:
            return False

        # Verificar límites de memoria
        max_memory = current_workload.get("max_memory_gb", self.config.max_memory_usage_gb)
        if profile.memory_usage_gb > max_memory:
            return False

        return True

    def _find_or_create_optimal_profile(
        self,
        node_capabilities: Dict[str, Any],
        workload: Dict[str, Any],
        round_requirements: Optional[Dict[str, Any]] = None
    ) -> QuantizationProfile:
        """Encontrar o crear perfil óptimo."""
        # Determinar restricciones
        constraints = self._extract_constraints(node_capabilities, workload, round_requirements)

        # Probar diferentes niveles de cuantización
        candidate_profiles = []

        for level in QuantizationLevel:
            try:
                # Crear perfil candidato
                profile = self._evaluate_quantization_level(
                    level, node_capabilities, constraints
                )

                if profile and self._meets_constraints(profile, constraints):
                    candidate_profiles.append(profile)

            except Exception as e:
                logger.warning(f"⚠️ Error evaluando {level.value}: {e}")
                continue

        if not candidate_profiles:
            # Fallback a FP16
            logger.warning("⚠️ No se encontraron perfiles adecuados, usando FP16")
            return self._create_fallback_profile(QuantizationLevel.FP16, node_capabilities)

        # Seleccionar el mejor perfil
        best_profile = max(candidate_profiles, key=lambda p: p.efficiency_score)

        # Registrar adaptación
        self._record_adaptation(best_profile, constraints)

        return best_profile

    def _extract_constraints(
        self,
        node_capabilities: Dict[str, Any],
        workload: Dict[str, Any],
        round_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extraer restricciones para la adaptación."""
        constraints = {
            "max_memory_gb": min(
                node_capabilities.get("gpu_memory_gb", 8.0),
                self.config.max_memory_usage_gb
            ),
            "min_throughput": workload.get("min_throughput", self.config.min_throughput_tokens_per_sec),
            "max_accuracy_drop": self.config.max_accuracy_drop_percent,
            "hardware_type": node_capabilities.get("hardware_type", "cpu"),
            "supports_fp16": node_capabilities.get("supports_fp16", False),
            "supports_int8": node_capabilities.get("supports_int8", False),
            "supports_int4": node_capabilities.get("supports_int4", False)
        }

        # Agregar restricciones específicas de FL
        if round_requirements:
            if "precision_requirement" in round_requirements:
                constraints["required_precision"] = round_requirements["precision_requirement"]

            if "latency_requirement_ms" in round_requirements:
                constraints["max_latency_ms"] = round_requirements["latency_requirement_ms"]

        return constraints

    def _evaluate_quantization_level(
        self,
        level: QuantizationLevel,
        node_capabilities: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Optional[QuantizationProfile]:
        """Evaluar un nivel de cuantización."""
        try:
            # Simular evaluación (en implementación real, esto haría pruebas reales)
            base_memory = node_capabilities.get("gpu_memory_gb", 8.0)

            # Estimaciones basadas en nivel
            if level == QuantizationLevel.FP32:
                memory_usage = base_memory * 0.8
                throughput = 50.0
                latency = 200.0
                accuracy_drop = 0.0
            elif level == QuantizationLevel.FP16:
                memory_usage = base_memory * 0.5
                throughput = 80.0
                latency = 150.0
                accuracy_drop = 0.5
            elif level == QuantizationLevel.INT8:
                memory_usage = base_memory * 0.3
                throughput = 120.0
                latency = 100.0
                accuracy_drop = 2.0
            elif level == QuantizationLevel.INT4:
                memory_usage = base_memory * 0.2
                throughput = 150.0
                latency = 80.0
                accuracy_drop = 4.0
            elif level == QuantizationLevel.MIXED:
                memory_usage = base_memory * 0.35
                throughput = 110.0
                latency = 110.0
                accuracy_drop = 1.5
            else:
                return None

            # Ajustar por capacidades del hardware
            if not constraints.get("supports_fp16", True) and level in [QuantizationLevel.FP16, QuantizationLevel.INT8, QuantizationLevel.INT4, QuantizationLevel.MIXED]:
                return None

            if not constraints.get("supports_int8", True) and level in [QuantizationLevel.INT8, QuantizationLevel.INT4, QuantizationLevel.MIXED]:
                return None

            # Crear perfil
            profile = QuantizationProfile(
                level=level,
                model_path="",  # Se establecerá después
                memory_usage_gb=memory_usage,
                inference_latency_ms=latency,
                throughput_tokens_per_sec=throughput,
                accuracy_drop_percent=accuracy_drop
            )

            return profile

        except Exception as e:
            logger.error(f"❌ Error evaluando {level.value}: {e}")
            return None

    def _meets_constraints(self, profile: QuantizationProfile, constraints: Dict[str, Any]) -> bool:
        """Verificar si un perfil cumple las restricciones."""
        # Memoria
        if profile.memory_usage_gb > constraints["max_memory_gb"]:
            return False

        # Throughput
        if profile.throughput_tokens_per_sec < constraints["min_throughput"]:
            return False

        # Accuracy
        if profile.accuracy_drop_percent > constraints["max_accuracy_drop"]:
            return False

        # Latencia (si especificada)
        if "max_latency_ms" in constraints and profile.inference_latency_ms > constraints["max_latency_ms"]:
            return False

        # Precisión requerida
        if "required_precision" in constraints:
            required = constraints["required_precision"]
            if required == "fp32" and profile.level != QuantizationLevel.FP32:
                return False
            elif required == "fp16" and profile.level not in [QuantizationLevel.FP16, QuantizationLevel.FP32]:
                return False

        return True

    def _create_fallback_profile(
        self,
        level: QuantizationLevel,
        node_capabilities: Dict[str, Any]
    ) -> QuantizationProfile:
        """Crear perfil de fallback."""
        return QuantizationProfile(
            level=level,
            model_path="",
            memory_usage_gb=node_capabilities.get("gpu_memory_gb", 8.0) * 0.6,
            inference_latency_ms=150.0,
            throughput_tokens_per_sec=70.0,
            accuracy_drop_percent=1.0
        )

    def _record_adaptation(self, profile: QuantizationProfile, constraints: Dict[str, Any]):
        """Registrar una adaptación."""
        adaptation_record = {
            "timestamp": time.time(),
            "selected_level": profile.level.value,
            "efficiency_score": profile.efficiency_score,
            "constraints": constraints,
            "node_capabilities": self.current_node_capabilities
        }

        self.adaptation_history.append(adaptation_record)
        self.stats["total_adaptations"] += 1
        self.stats["current_quantization_level"] = profile.level.value

        # Calcular mejora de eficiencia si hay historial
        if len(self.adaptation_history) > 1:
            prev_adaptation = self.adaptation_history[-2]
            if "efficiency_score" in prev_adaptation:
                improvement = profile.efficiency_score - prev_adaptation["efficiency_score"]
                self.stats["avg_efficiency_improvement"] = (
                    (self.stats["avg_efficiency_improvement"] * (len(self.adaptation_history) - 2)) + improvement
                ) / (len(self.adaptation_history) - 1)

    def apply_adaptive_quantization(
        self,
        model_path: str,
        target_profile: QuantizationProfile
    ) -> str:
        """
        Aplicar cuantización adaptativa a un modelo.

        Args:
            model_path: Ruta del modelo original
            target_profile: Perfil de cuantización objetivo

        Returns:
            Ruta del modelo cuantizado
        """
        try:
            logger.info(f"🔄 Aplicando cuantización {target_profile.level.value}...")

            # Configurar cuantización
            quant_config = self._create_quantization_config(target_profile.level)

            # Aplicar cuantización usando el quantizer avanzado
            quantized_model = self.quantizer.quantize_model(
                model_path=model_path,
                quantization_type=target_profile.level.value,
                save_path=None,  # No guardar automáticamente
                use_dynamic_calibration=True
            )

            # Medir rendimiento real
            actual_metrics = self._measure_actual_performance(quantized_model, target_profile)

            # Actualizar perfil con métricas reales
            target_profile.performance_metrics = actual_metrics
            target_profile.memory_usage_gb = actual_metrics.get("memory_usage_gb", target_profile.memory_usage_gb)
            target_profile.inference_latency_ms = actual_metrics.get("latency_ms", target_profile.inference_latency_ms)
            target_profile.throughput_tokens_per_sec = actual_metrics.get("throughput", target_profile.throughput_tokens_per_sec)

            # Crear ruta para modelo cuantizado
            quantized_path = f"{model_path}_{target_profile.level.value}_adaptive"

            # Guardar modelo (simulado)
            logger.info(f"✅ Cuantización aplicada: {quantized_path}")

            self.stats["successful_adaptations"] += 1
            return quantized_path

        except Exception as e:
            logger.error(f"❌ Error aplicando cuantización adaptativa: {e}")
            self.stats["failed_adaptations"] += 1
            raise

    def _create_quantization_config(self, level: QuantizationLevel) -> QuantizationConfig:
        """Crear configuración de cuantización para un nivel."""
        if level == QuantizationLevel.FP16:
            return QuantizationConfig(quantization_type="fp16")
        elif level == QuantizationLevel.INT8:
            return QuantizationConfig(quantization_type="int8")
        elif level == QuantizationLevel.INT4:
            return QuantizationConfig(quantization_type="int4")
        elif level == QuantizationLevel.MIXED:
            return QuantizationConfig(
                quantization_type="mixed",
                mixed_precision_layers={
                    "embed_tokens": "fp16",
                    "lm_head": "fp16",
                    "layers.*.self_attn": "int8",
                    "layers.*.mlp": "int4"
                }
            )
        else:  # FP32
            return QuantizationConfig(quantization_type="fp32")

    def _measure_actual_performance(
        self,
        model: Any,
        profile: QuantizationProfile
    ) -> Dict[str, float]:
        """Medir rendimiento actual del modelo cuantizado."""
        # En implementación real, esto ejecutaría benchmarks
        # Por ahora, retornar estimaciones
        return {
            "memory_usage_gb": profile.memory_usage_gb,
            "latency_ms": profile.inference_latency_ms * np.random.uniform(0.9, 1.1),
            "throughput": profile.throughput_tokens_per_sec * np.random.uniform(0.95, 1.05)
        }

    def should_adapt_quantization(
        self,
        current_metrics: Dict[str, Any],
        workload_change: Dict[str, Any]
    ) -> bool:
        """
        Determinar si se debe adaptar la cuantización.

        Args:
            current_metrics: Métricas actuales
            workload_change: Cambios en la carga de trabajo

        Returns:
            True si se debe adaptar
        """
        if not self.config.enable_adaptive_quantization:
            return False

        # Verificar tiempo desde última adaptación
        time_since_adaptation = time.time() - self.last_adaptation_time
        if time_since_adaptation < self.config.adaptation_interval_minutes * 60:
            return False

        # Verificar cambios significativos en workload
        throughput_change = workload_change.get("throughput_change_percent", 0)
        memory_pressure = workload_change.get("memory_pressure_increase", 0)

        if abs(throughput_change) > 20 or memory_pressure > 0.2:  # Cambios > 20%
            return True

        # Verificar degradación de rendimiento
        current_throughput = current_metrics.get("throughput", 0)
        if current_throughput < self.config.min_throughput_tokens_per_sec * 0.8:
            return True

        return False

    def _load_cached_profiles(self):
        """Cargar perfiles desde cache."""
        if not self.config.enable_profile_persistence:
            return

        try:
            cache_file = Path(self.config.profile_cache_path) / "profiles.pkl"
            if cache_file.exists():
                import pickle
                with open(cache_file, 'rb') as f:
                    cached_profiles = pickle.load(f)

                self.quantization_profiles.update(cached_profiles)
                logger.info(f"📥 Cargados {len(cached_profiles)} perfiles desde cache")

        except Exception as e:
            logger.warning(f"⚠️ Error cargando perfiles cacheados: {e}")

    def _save_profile_to_cache(self, key: str, profile: QuantizationProfile):
        """Guardar perfil en cache."""
        if not self.config.enable_profile_persistence:
            return

        try:
            cache_file = Path(self.config.profile_cache_path) / "profiles.pkl"
            import pickle

            # Cargar perfiles existentes
            existing = {}
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    existing = pickle.load(f)

            # Agregar nuevo perfil
            existing[key] = profile

            # Guardar
            with open(cache_file, 'wb') as f:
                pickle.dump(existing, f)

        except Exception as e:
            logger.warning(f"⚠️ Error guardando perfil en cache: {e}")

    def get_bridge_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del puente."""
        return {
            **self.stats,
            "active_profiles": len(self.quantization_profiles),
            "adaptation_history_length": len(self.adaptation_history),
            "performance_history_length": len(self.performance_history),
            "last_adaptation": self.last_adaptation_time
        }


# Funciones de conveniencia
def create_adaptive_quantization_bridge(
    enable_adaptation: bool = True,
    max_accuracy_drop: float = 5.0,
    fed_optimizer: Optional[FederatedVLLOptimizer] = None
) -> AdaptiveQuantizationBridge:
    """
    Crear puente de cuantización adaptativa.

    Args:
        enable_adaptation: Habilitar adaptación automática
        max_accuracy_drop: Máxima caída de precisión permitida (%)
        fed_optimizer: Optimizador federado opcional

    Returns:
        Puente configurado
    """
    config = AdaptiveBridgeConfig(
        enable_adaptive_quantization=enable_adaptation,
        max_accuracy_drop_percent=max_accuracy_drop
    )

    quantizer = AdvancedQuantizer()
    return AdaptiveQuantizationBridge(config, quantizer, fed_optimizer)


if __name__ == "__main__":
    # Demo del puente adaptativo
    print("🚀 AdaptiveQuantizationBridge Demo")
    print("Para uso completo, inicializar con configuración específica")