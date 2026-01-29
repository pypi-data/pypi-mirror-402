"""
Configuraciones centralizadas para el Sistema de Benchmarking Automático

Este archivo contiene todas las configuraciones por defecto y helpers
para asegurar reproducibilidad y consistencia en todo el sistema.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Configuraciones globales
DEFAULT_CONFIG = {
    # Rutas de directorios
    "results_dir": "benchmark_results",
    "reports_dir": "reports",
    "datasets_cache_dir": "benchmark_datasets",
    "logs_dir": "logs",

    # Configuración de reproducibilidad
    "global_seed": 42,
    "torch_seed": 42,
    "numpy_seed": 42,
    "random_seed": 42,

    # Configuración de logging
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_max_files": 10,
    "log_max_size_mb": 100,

    # Configuración de rendimiento
    "profiling_interval": 0.1,  # segundos
    "max_profiling_duration": 3600,  # segundos (1 hora)

    # Configuración de datasets
    "default_dataset_num_samples": 1000,
    "dataset_cache_expiry_days": 30,
    "max_dataset_cache_size_gb": 50,

    # Configuración de benchmarks
    "default_batch_size": 8,
    "default_max_length": 512,
    "benchmark_timeout_seconds": 1800,  # 30 minutos
    "max_concurrent_benchmarks": 4,

    # Configuración de regresiones
    "regression_threshold_default": 5.0,  # porcentaje
    "regression_min_samples": 3,
    "regression_stability_window": 5,
    "block_deployment_max_critical": 0,
    "block_deployment_max_severe": 1,

    # Configuración de reportes
    "report_formats": ["html", "json", "markdown"],
    "report_include_plots": True,
    "report_max_table_rows": 1000,

    # Configuración de versiones
    "version_comparison_min_overlap": 0.8,  # 80% de métricas en común
    "version_history_max_entries": 100,

    # Configuración de hardware
    "gpu_memory_fraction": 0.8,  # Usar 80% de GPU disponible
    "cpu_threads_limit": None,  # None = usar todos disponibles

    # Configuración de notificaciones (opcional)
    "enable_notifications": False,
    "notification_webhook_url": None,
    "alert_on_regression": True,
    "alert_severity_threshold": "moderate",
}

class BenchmarkingConfig:
    """
    Gestor centralizado de configuraciones para el sistema de benchmarking.

    Proporciona configuración por defecto, carga desde archivos,
    validación y helpers para reproducibilidad.
    """

    def __init__(self, config_file: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None):
        """
        Inicializar configuración.

        Args:
            config_file: Ruta a archivo JSON con configuraciones personalizadas
            overrides: Diccionario con configuraciones que sobrescriben las por defecto
        """
        self._config = DEFAULT_CONFIG.copy()

        # Cargar desde archivo si existe
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)

        # Aplicar overrides
        if overrides:
            self._config.update(overrides)

        # Validar configuración
        self._validate_config()

        # Configurar semillas globales
        self._setup_reproducibility()

    def _load_from_file(self, config_file: str):
        """Cargar configuración desde archivo JSON."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                self._config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")

    def _validate_config(self):
        """Validar que la configuración sea consistente."""
        # Validar rangos
        if not (0 < self._config["profiling_interval"] <= 10):
            raise ValueError("profiling_interval must be between 0.1 and 10 seconds")

        if self._config["regression_threshold_default"] <= 0:
            raise ValueError("regression_threshold_default must be positive")

        if self._config["gpu_memory_fraction"] > 1.0 or self._config["gpu_memory_fraction"] <= 0:
            raise ValueError("gpu_memory_fraction must be between 0 and 1")

        # Validar formatos de reporte
        valid_formats = ["html", "json", "markdown", "pdf"]
        for fmt in self._config["report_formats"]:
            if fmt not in valid_formats:
                raise ValueError(f"Invalid report format: {fmt}")

    def _setup_reproducibility(self):
        """Configurar semillas globales para reproducibilidad."""
        import random
        import numpy as np

        # Configurar semillas
        random.seed(self._config["random_seed"])
        np.random.seed(self._config["numpy_seed"])

        # Configurar PyTorch si está disponible
        try:
            import torch
            torch.manual_seed(self._config["torch_seed"])
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self._config["torch_seed"])
        except ImportError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Establecer valor de configuración."""
        self._config[key] = value

    def save_to_file(self, filepath: str):
        """Guardar configuración actual a archivo."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get_all(self) -> Dict[str, Any]:
        """Obtener toda la configuración."""
        return self._config.copy()

    # Helpers específicos
    def get_results_dir(self) -> Path:
        """Obtener directorio de resultados."""
        return Path(self._config["results_dir"])

    def get_reports_dir(self) -> Path:
        """Obtener directorio de reportes."""
        return Path(self._config["reports_dir"])

    def get_datasets_cache_dir(self) -> Path:
        """Obtener directorio de cache de datasets."""
        return Path(self._config["datasets_cache_dir"])

    def get_logs_dir(self) -> Path:
        """Obtener directorio de logs."""
        return Path(self._config["logs_dir"])

    def should_enable_gpu(self) -> bool:
        """Determinar si se debe usar GPU."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def get_optimal_batch_size(self, model_name: str = None) -> int:
        """Obtener tamaño de batch óptimo basado en el modelo y hardware."""
        base_batch_size = self._config["default_batch_size"]

        # Ajustar basado en GPU disponible
        if self.should_enable_gpu():
            try:
                import torch
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                if gpu_memory < 4:  # GPUs pequeñas
                    return min(base_batch_size, 2)
                elif gpu_memory < 8:  # GPUs medianas
                    return min(base_batch_size, 4)
                else:  # GPUs grandes
                    return base_batch_size
            except:
                pass

        return base_batch_size

    def get_regression_thresholds(self, metric: str) -> Dict[str, float]:
        """Obtener umbrales de regresión para una métrica específica."""
        base_threshold = self._config["regression_threshold_default"]

        # Umbrales específicos por métrica
        metric_thresholds = {
            "perplexity": base_threshold * 0.5,  # Más sensible
            "accuracy": base_threshold,
            "f1": base_threshold,
            "latency": base_threshold * 2,  # Menos sensible
            "throughput": base_threshold * 1.5,
        }

        threshold = metric_thresholds.get(metric.lower(), base_threshold)

        return {
            "minor": threshold * 0.5,
            "moderate": threshold,
            "severe": threshold * 2,
            "critical": threshold * 4
        }

# Instancia global de configuración
_global_config = None

def get_config(config_file: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> BenchmarkingConfig:
    """Obtener instancia global de configuración."""
    global _global_config
    if _global_config is None:
        _global_config = BenchmarkingConfig(config_file, overrides)
    return _global_config

def reset_config():
    """Resetear configuración global (útil para testing)."""
    global _global_config
    _global_config = None

# Configuración por defecto para desarrollo
DEV_CONFIG = {
    "log_level": "DEBUG",
    "default_dataset_num_samples": 100,  # Menos datos para desarrollo
    "benchmark_timeout_seconds": 300,  # 5 minutos para desarrollo
}

# Configuración para producción
PROD_CONFIG = {
    "log_level": "WARNING",
    "enable_notifications": True,
    "alert_on_regression": True,
    "max_concurrent_benchmarks": 8,
}

# Función helper para cargar configuración por entorno
def load_env_config(env: str = None) -> Dict[str, Any]:
    """Cargar configuración basada en el entorno."""
    if env is None:
        env = os.getenv("BENCHMARKING_ENV", "dev")

    env_configs = {
        "dev": DEV_CONFIG,
        "development": DEV_CONFIG,
        "prod": PROD_CONFIG,
        "production": PROD_CONFIG,
    }

    return env_configs.get(env.lower(), DEV_CONFIG)