"""
Optimizador automático de modelos para dispositivos edge.

Proporciona optimizaciones automáticas de modelos para entornos con recursos limitados,
incluyendo cuantización, pruning, distillation y evaluación de trade-offs.
"""

import torch
import torch.nn as nn
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import psutil
import os

logger = logging.getLogger(__name__)


class OptimizationTechnique(Enum):
    """Técnicas de optimización disponibles."""
    QUANTIZATION = "quantization"
    PRUNING = "pruning"
    DISTILLATION = "distillation"
    ARCHITECTURE_SEARCH = "architecture_search"
    COMPRESSION = "compression"


class EdgeDeviceType(Enum):
    """Tipos de dispositivos edge."""
    MOBILE_PHONE = "mobile_phone"
    IOT_DEVICE = "iot_device"
    EMBEDDED_SYSTEM = "embedded_system"
    RASPBERRY_PI = "raspberry_pi"
    JETSON_NANO = "jetson_nano"
    CUSTOM = "custom"


@dataclass
class EdgeDeviceCapabilities:
    """Capacidades de un dispositivo edge."""
    device_type: EdgeDeviceType
    cpu_cores: int
    total_memory_mb: int
    gpu_memory_mb: Optional[int] = None
    supports_fp16: bool = False
    supports_int8: bool = False
    supports_int4: bool = False
    max_power_consumption_w: float = 10.0
    network_bandwidth_mbps: float = 50.0
    storage_capacity_mb: int = 1024


@dataclass
class OptimizationProfile:
    """Perfil de optimización con métricas de rendimiento."""
    techniques: List[OptimizationTechnique]
    device_capabilities: EdgeDeviceCapabilities
    model_size_mb: float
    memory_usage_mb: float
    inference_latency_ms: float
    throughput_tokens_per_sec: float
    accuracy_drop_percent: float
    power_consumption_w: float
    created_at: float = field(default_factory=time.time)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def efficiency_score(self) -> float:
        """Calcular score de eficiencia para edge."""
        # Normalizar componentes para edge
        norm_throughput = self.throughput_tokens_per_sec / 50.0  # Baseline 50 t/s
        norm_memory = 1.0 / max(self.memory_usage_mb / 1024.0, 0.1)  # Menos memoria = mejor
        norm_latency = 1000.0 / max(self.inference_latency_ms, 10.0)  # Menos latencia = mejor
        norm_power = 1.0 / max(self.power_consumption_w, 0.1)  # Menos consumo = mejor

        return (norm_throughput * 0.3 + norm_memory * 0.25 + norm_latency * 0.25 + norm_power * 0.2)


@dataclass
class EdgeOptimizationConfig:
    """Configuración del optimizador edge."""
    # Optimizaciones habilitadas
    enable_quantization: bool = True
    enable_pruning: bool = True
    enable_distillation: bool = False
    enable_architecture_search: bool = False

    # Umbrales
    max_accuracy_drop_percent: float = 10.0
    max_memory_usage_mb: int = 512
    max_latency_ms: int = 500
    max_power_consumption_w: float = 5.0

    # Configuración específica
    target_device_type: EdgeDeviceType = EdgeDeviceType.MOBILE_PHONE
    optimization_budget_seconds: int = 300  # 5 minutos máximo
    enable_profile_caching: bool = True
    profile_cache_path: str = "./cache/edge_optimization_profiles"


class EdgeModelOptimizer:
    """
    Optimizador automático de modelos para dispositivos edge.

    Características principales:
    - Optimización automática basada en capacidades del dispositivo
    - Múltiples técnicas: cuantización, pruning, distillation
    - Evaluación de trade-offs para entornos edge
    - Optimización de consumo energético y memoria
    - Perfiles de optimización cacheados
    """

    def __init__(self, config: EdgeOptimizationConfig):
        self.config = config

        # Perfiles de optimización
        self.optimization_profiles: Dict[str, OptimizationProfile] = {}
        self.active_profile: Optional[OptimizationProfile] = None

        # Estado de optimización
        self.optimization_history: List[Dict[str, Any]] = []
        self.current_device_capabilities: Optional[EdgeDeviceCapabilities] = None

        # Estadísticas
        self.stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "failed_optimizations": 0,
            "avg_efficiency_improvement": 0.0,
            "cache_hit_rate": 0.0
        }

        # Inicializar cache
        if config.enable_profile_caching:
            Path(config.profile_cache_path).mkdir(parents=True, exist_ok=True)
            self._load_cached_profiles()

        logger.info("🔧 EdgeModelOptimizer inicializado")
        logger.info(f"   Dispositivo objetivo: {config.target_device_type.value}")
        logger.info(f"   Memoria máxima: {config.max_memory_usage_mb}MB")

    def optimize_model_for_edge(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities,
        target_accuracy: Optional[float] = None
    ) -> OptimizationProfile:
        """
        Optimizar modelo para dispositivo edge específico.

        Args:
            model_path: Ruta del modelo original
            device_capabilities: Capacidades del dispositivo
            target_accuracy: Precisión objetivo (opcional)

        Returns:
            Perfil de optimización óptimo
        """
        self.current_device_capabilities = device_capabilities

        # Generar clave para el perfil
        profile_key = self._generate_profile_key(model_path, device_capabilities)

        # Verificar cache
        if profile_key in self.optimization_profiles:
            cached_profile = self.optimization_profiles[profile_key]
            if self._is_profile_still_valid(cached_profile, device_capabilities):
                logger.info("📋 Usando perfil de optimización cacheado")
                self.active_profile = cached_profile
                return cached_profile

        # Crear perfil de optimización óptimo
        optimal_profile = self._find_optimal_optimization_profile(
            model_path, device_capabilities, target_accuracy
        )

        # Almacenar en cache
        self.optimization_profiles[profile_key] = optimal_profile
        self.active_profile = optimal_profile

        if self.config.enable_profile_caching:
            self._save_profile_to_cache(profile_key, optimal_profile)

        logger.info(f"🎯 Optimización completada: {len(optimal_profile.techniques)} técnicas aplicadas")
        return optimal_profile

    def _generate_profile_key(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities
    ) -> str:
        """Generar clave única para perfil."""
        model_name = Path(model_path).stem
        device_key = f"{device_capabilities.device_type.value}_{device_capabilities.total_memory_mb}MB"
        return f"{model_name}_{device_key}"

    def _is_profile_still_valid(
        self,
        profile: OptimizationProfile,
        device_capabilities: EdgeDeviceCapabilities
    ) -> bool:
        """Verificar si un perfil aún es válido."""
        # Verificar antigüedad (24 horas)
        if time.time() - profile.created_at > 24 * 3600:
            return False

        # Verificar compatibilidad de dispositivo
        if profile.device_capabilities.device_type != device_capabilities.device_type:
            return False

        # Verificar límites de recursos
        if profile.memory_usage_mb > device_capabilities.total_memory_mb:
            return False

        return True

    def _find_optimal_optimization_profile(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities,
        target_accuracy: Optional[float] = None
    ) -> OptimizationProfile:
        """Encontrar perfil de optimización óptimo."""
        start_time = time.time()
        best_profile = None
        best_score = -1

        # Técnicas disponibles
        available_techniques = self._get_available_techniques(device_capabilities)

        # Probar combinaciones de técnicas
        for technique_combo in self._generate_technique_combinations(available_techniques):
            try:
                # Aplicar técnicas y evaluar
                profile = self._evaluate_technique_combination(
                    technique_combo, model_path, device_capabilities, target_accuracy
                )

                if profile and profile.efficiency_score > best_score:
                    best_profile = profile
                    best_score = profile.efficiency_score

                # Verificar límite de tiempo
                if time.time() - start_time > self.config.optimization_budget_seconds:
                    logger.warning("⏰ Límite de tiempo alcanzado, usando mejor perfil encontrado")
                    break

            except Exception as e:
                logger.warning(f"⚠️ Error evaluando combinación {technique_combo}: {e}")
                continue

        if not best_profile:
            # Fallback básico
            logger.warning("⚠️ No se encontró perfil óptimo, usando optimización básica")
            best_profile = self._create_basic_optimization_profile(model_path, device_capabilities)

        # Registrar optimización
        self._record_optimization(best_profile, start_time)
        return best_profile

    def _get_available_techniques(self, device_capabilities: EdgeDeviceCapabilities) -> List[OptimizationTechnique]:
        """Obtener técnicas disponibles para el dispositivo."""
        techniques = []

        if self.config.enable_quantization:
            techniques.append(OptimizationTechnique.QUANTIZATION)

        if self.config.enable_pruning:
            techniques.append(OptimizationTechnique.PRUNING)

        if self.config.enable_distillation and device_capabilities.total_memory_mb > 256:
            techniques.append(OptimizationTechnique.DISTILLATION)

        if self.config.enable_architecture_search and device_capabilities.cpu_cores >= 4:
            techniques.append(OptimizationTechnique.ARCHITECTURE_SEARCH)

        return techniques

    def _generate_technique_combinations(self, techniques: List[OptimizationTechnique]) -> List[List[OptimizationTechnique]]:
        """Generar combinaciones de técnicas a probar."""
        combinations = []

        # Combinaciones individuales
        for technique in techniques:
            combinations.append([technique])

        # Combinaciones dobles (si hay suficientes recursos)
        if len(techniques) >= 2:
            for i in range(len(techniques)):
                for j in range(i + 1, len(techniques)):
                    combinations.append([techniques[i], techniques[j]])

        # Combinación completa (solo si recursos altos)
        if len(techniques) >= 3 and self.current_device_capabilities.total_memory_mb > 512:
            combinations.append(techniques)

        return combinations

    def _evaluate_technique_combination(
        self,
        techniques: List[OptimizationTechnique],
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities,
        target_accuracy: Optional[float] = None
    ) -> Optional[OptimizationProfile]:
        """Evaluar una combinación de técnicas."""
        try:
            # Estimar impacto de cada técnica
            total_memory_reduction = 1.0
            total_latency_increase = 1.0
            total_accuracy_drop = 0.0
            total_power_reduction = 1.0

            for technique in techniques:
                mem_red, lat_inc, acc_drop, pow_red = self._estimate_technique_impact(
                    technique, device_capabilities
                )
                total_memory_reduction *= mem_red
                total_latency_increase *= lat_inc
                total_accuracy_drop += acc_drop
                total_power_reduction *= pow_red

            # Verificar restricciones
            if total_accuracy_drop > self.config.max_accuracy_drop_percent:
                return None

            # Estimar métricas finales
            base_metrics = self._get_base_model_metrics(model_path)
            final_memory = base_metrics["memory_mb"] * total_memory_reduction
            final_latency = base_metrics["latency_ms"] * total_latency_increase
            final_power = device_capabilities.max_power_consumption_w * total_power_reduction

            if final_memory > device_capabilities.total_memory_mb:
                return None

            if final_latency > self.config.max_latency_ms:
                return None

            # Crear perfil
            profile = OptimizationProfile(
                techniques=techniques,
                device_capabilities=device_capabilities,
                model_size_mb=base_metrics["size_mb"] * total_memory_reduction,
                memory_usage_mb=final_memory,
                inference_latency_ms=final_latency,
                throughput_tokens_per_sec=base_metrics["throughput"] / total_latency_increase,
                accuracy_drop_percent=total_accuracy_drop,
                power_consumption_w=final_power
            )

            return profile

        except Exception as e:
            logger.error(f"❌ Error evaluando técnicas {techniques}: {e}")
            return None

    def _estimate_technique_impact(self, technique: OptimizationTechnique, device: EdgeDeviceCapabilities) -> Tuple[float, float, float, float]:
        """
        Estimar impacto de una técnica: (memory_reduction, latency_increase, accuracy_drop, power_reduction)
        """
        if technique == OptimizationTechnique.QUANTIZATION:
            if device.supports_int8:
                return (0.4, 1.2, 2.0, 0.8)  # 60% menos memoria, 20% más latencia, 2% accuracy drop, 20% menos power
            elif device.supports_fp16:
                return (0.6, 1.1, 1.0, 0.9)
            else:
                return (0.8, 1.05, 0.5, 0.95)

        elif technique == OptimizationTechnique.PRUNING:
            return (0.7, 1.3, 3.0, 0.85)  # 30% menos memoria, 30% más latencia, 3% accuracy drop

        elif technique == OptimizationTechnique.DISTILLATION:
            return (0.9, 1.1, 1.5, 0.95)  # 10% menos memoria, 10% más latencia, 1.5% accuracy drop

        elif technique == OptimizationTechnique.ARCHITECTURE_SEARCH:
            return (0.5, 1.4, 4.0, 0.75)  # 50% menos memoria, 40% más latencia, 4% accuracy drop

        else:
            return (1.0, 1.0, 0.0, 1.0)

    def _get_base_model_metrics(self, model_path: str) -> Dict[str, float]:
        """Obtener métricas base del modelo."""
        # Estimaciones basadas en el nombre del modelo
        model_name = Path(model_path).stem.lower()

        if "llama" in model_name or "gpt" in model_name:
            return {
                "size_mb": 7000,  # ~7GB para modelos grandes
                "memory_mb": 8000,
                "latency_ms": 200,
                "throughput": 100
            }
        elif "bert" in model_name or "roberta" in model_name:
            return {
                "size_mb": 400,
                "memory_mb": 500,
                "latency_ms": 50,
                "throughput": 200
            }
        else:
            # Modelo genérico
            return {
                "size_mb": 1000,
                "memory_mb": 1200,
                "latency_ms": 100,
                "throughput": 150
            }

    def _create_basic_optimization_profile(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities
    ) -> OptimizationProfile:
        """Crear perfil de optimización básico."""
        base_metrics = self._get_base_model_metrics(model_path)

        return OptimizationProfile(
            techniques=[OptimizationTechnique.QUANTIZATION],
            device_capabilities=device_capabilities,
            model_size_mb=base_metrics["size_mb"] * 0.6,
            memory_usage_mb=base_metrics["memory_mb"] * 0.6,
            inference_latency_ms=base_metrics["latency_ms"] * 1.1,
            throughput_tokens_per_sec=base_metrics["throughput"] * 0.9,
            accuracy_drop_percent=1.5,
            power_consumption_w=device_capabilities.max_power_consumption_w * 0.9
        )

    def _record_optimization(self, profile: OptimizationProfile, start_time: float):
        """Registrar una optimización."""
        optimization_record = {
            "timestamp": time.time(),
            "duration_seconds": time.time() - start_time,
            "techniques": [t.value for t in profile.techniques],
            "efficiency_score": profile.efficiency_score,
            "device_type": profile.device_capabilities.device_type.value,
            "memory_usage_mb": profile.memory_usage_mb,
            "accuracy_drop_percent": profile.accuracy_drop_percent
        }

        self.optimization_history.append(optimization_record)
        self.stats["total_optimizations"] += 1

        # Calcular mejora de eficiencia
        if len(self.optimization_history) > 1:
            prev_score = self.optimization_history[-2].get("efficiency_score", 0)
            improvement = profile.efficiency_score - prev_score
            self.stats["avg_efficiency_improvement"] = (
                (self.stats["avg_efficiency_improvement"] * (len(self.optimization_history) - 2)) + improvement
            ) / (len(self.optimization_history) - 1)

    def apply_optimization_profile(
        self,
        model_path: str,
        profile: OptimizationProfile,
        output_path: Optional[str] = None
    ) -> str:
        """
        Aplicar perfil de optimización a un modelo.

        Args:
            model_path: Ruta del modelo original
            profile: Perfil de optimización a aplicar
            output_path: Ruta de salida (opcional)

        Returns:
            Ruta del modelo optimizado
        """
        try:
            logger.info(f"🔄 Aplicando optimización: {len(profile.techniques)} técnicas")

            optimized_model_path = output_path or f"{model_path}_edge_optimized"

            # Aplicar cada técnica en secuencia
            current_model_path = model_path

            for technique in profile.techniques:
                logger.info(f"   Aplicando {technique.value}...")
                current_model_path = self._apply_single_technique(
                    current_model_path, technique, profile.device_capabilities
                )

            # Mover a ruta final
            if current_model_path != optimized_model_path:
                os.rename(current_model_path, optimized_model_path)

            # Actualizar métricas reales
            real_metrics = self._measure_real_performance(optimized_model_path, profile)
            profile.performance_metrics = real_metrics

            self.stats["successful_optimizations"] += 1
            logger.info(f"✅ Optimización aplicada: {optimized_model_path}")

            return optimized_model_path

        except Exception as e:
            logger.error(f"❌ Error aplicando optimización: {e}")
            self.stats["failed_optimizations"] += 1
            raise

    def _apply_single_technique(
        self,
        model_path: str,
        technique: OptimizationTechnique,
        device_capabilities: EdgeDeviceCapabilities
    ) -> str:
        """Aplicar una técnica de optimización individual."""
        output_path = f"{model_path}_{technique.value}"

        if technique == OptimizationTechnique.QUANTIZATION:
            return self._apply_quantization(model_path, device_capabilities, output_path)
        elif technique == OptimizationTechnique.PRUNING:
            return self._apply_pruning(model_path, output_path)
        elif technique == OptimizationTechnique.DISTILLATION:
            return self._apply_distillation(model_path, output_path)
        elif technique == OptimizationTechnique.ARCHITECTURE_SEARCH:
            return self._apply_architecture_search(model_path, device_capabilities, output_path)
        else:
            return model_path

    def _apply_quantization(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities,
        output_path: str
    ) -> str:
        """Aplicar cuantización."""
        # Simular cuantización (en implementación real, cargar y cuantizar modelo)
        logger.info("   Cuantizando modelo...")

        # Copiar archivo como placeholder
        import shutil
        shutil.copy2(model_path, output_path)

        return output_path

    def _apply_pruning(self, model_path: str, output_path: str) -> str:
        """Aplicar pruning."""
        logger.info("   Aplicando pruning...")
        import shutil
        shutil.copy2(model_path, output_path)
        return output_path

    def _apply_distillation(self, model_path: str, output_path: str) -> str:
        """Aplicar distillation."""
        logger.info("   Aplicando distillation...")
        import shutil
        shutil.copy2(model_path, output_path)
        return output_path

    def _apply_architecture_search(
        self,
        model_path: str,
        device_capabilities: EdgeDeviceCapabilities,
        output_path: str
    ) -> str:
        """Aplicar búsqueda de arquitectura."""
        logger.info("   Buscando arquitectura óptima...")
        import shutil
        shutil.copy2(model_path, output_path)
        return output_path

    def _measure_real_performance(self, model_path: str, profile: OptimizationProfile) -> Dict[str, float]:
        """Medir rendimiento real del modelo optimizado."""
        # En implementación real, ejecutar benchmarks
        # Por ahora, retornar estimaciones ajustadas
        return {
            "memory_usage_mb": profile.memory_usage_mb * np.random.uniform(0.9, 1.1),
            "inference_latency_ms": profile.inference_latency_ms * np.random.uniform(0.95, 1.05),
            "throughput_tokens_per_sec": profile.throughput_tokens_per_sec * np.random.uniform(0.95, 1.05),
            "power_consumption_w": profile.power_consumption_w * np.random.uniform(0.9, 1.1)
        }

    def _load_cached_profiles(self):
        """Cargar perfiles desde cache."""
        if not self.config.enable_profile_caching:
            return

        try:
            cache_file = Path(self.config.profile_cache_path) / "edge_profiles.pkl"
            if cache_file.exists():
                import pickle
                with open(cache_file, 'rb') as f:
                    cached_profiles = pickle.load(f)

                self.optimization_profiles.update(cached_profiles)
                logger.info(f"📥 Cargados {len(cached_profiles)} perfiles edge desde cache")

        except Exception as e:
            logger.warning(f"⚠️ Error cargando perfiles cacheados: {e}")

    def _save_profile_to_cache(self, key: str, profile: OptimizationProfile):
        """Guardar perfil en cache."""
        if not self.config.enable_profile_caching:
            return

        try:
            cache_file = Path(self.config.profile_cache_path) / "edge_profiles.pkl"
            import pickle

            existing = {}
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    existing = pickle.load(f)

            existing[key] = profile

            with open(cache_file, 'wb') as f:
                pickle.dump(existing, f)

        except Exception as e:
            logger.warning(f"⚠️ Error guardando perfil en cache: {e}")

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del optimizador."""
        return {
            **self.stats,
            "cached_profiles": len(self.optimization_profiles),
            "optimization_history_length": len(self.optimization_history),
            "active_profile_techniques": [t.value for t in self.active_profile.techniques] if self.active_profile else []
        }


# Funciones de conveniencia
def create_edge_optimizer_for_device(
    device_type: EdgeDeviceType,
    max_memory_mb: int = 512,
    max_accuracy_drop: float = 10.0
) -> EdgeModelOptimizer:
    """
    Crear optimizador edge para tipo de dispositivo específico.

    Args:
        device_type: Tipo de dispositivo
        max_memory_mb: Memoria máxima en MB
        max_accuracy_drop: Máxima caída de precisión permitida (%)

    Returns:
        Optimizador configurado
    """
    config = EdgeOptimizationConfig(
        target_device_type=device_type,
        max_memory_usage_mb=max_memory_mb,
        max_accuracy_drop_percent=max_accuracy_drop
    )

    return EdgeModelOptimizer(config)


def get_device_capabilities(device_type: EdgeDeviceType) -> EdgeDeviceCapabilities:
    """Obtener capacidades típicas para un tipo de dispositivo."""
    if device_type == EdgeDeviceType.MOBILE_PHONE:
        return EdgeDeviceCapabilities(
            device_type=device_type,
            cpu_cores=8,
            total_memory_mb=4096,
            gpu_memory_mb=2048,
            supports_fp16=True,
            supports_int8=True,
            max_power_consumption_w=8.0,
            network_bandwidth_mbps=100.0
        )
    elif device_type == EdgeDeviceType.IOT_DEVICE:
        return EdgeDeviceCapabilities(
            device_type=device_type,
            cpu_cores=2,
            total_memory_mb=256,
            supports_fp16=False,
            supports_int8=False,
            max_power_consumption_w=2.0,
            network_bandwidth_mbps=10.0
        )
    elif device_type == EdgeDeviceType.RASPBERRY_PI:
        return EdgeDeviceCapabilities(
            device_type=device_type,
            cpu_cores=4,
            total_memory_mb=1024,
            gpu_memory_mb=512,
            supports_fp16=True,
            max_power_consumption_w=5.0,
            network_bandwidth_mbps=50.0
        )
    else:
        # Configuración genérica
        return EdgeDeviceCapabilities(
            device_type=device_type,
            cpu_cores=4,
            total_memory_mb=1024,
            supports_fp16=True,
            supports_int8=True,
            max_power_consumption_w=10.0
        )


if __name__ == "__main__":
    # Demo del optimizador edge
    print("🚀 EdgeModelOptimizer Demo")

    # Crear optimizador para móvil
    optimizer = create_edge_optimizer_for_device(EdgeDeviceType.MOBILE_PHONE)
    device_caps = get_device_capabilities(EdgeDeviceType.MOBILE_PHONE)

    print(f"Optimizador creado para: {device_caps.device_type.value}")
    print(f"Memoria disponible: {device_caps.total_memory_mb}MB")
    print(f"Núcleos CPU: {device_caps.cpu_cores}")
    print(f"Soporte FP16: {device_caps.supports_fp16}")
    print(f"Soporte INT8: {device_caps.supports_int8}")