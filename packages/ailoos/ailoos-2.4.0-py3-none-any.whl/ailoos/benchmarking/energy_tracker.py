"""
Energy Tracker Module for EmpoorioLM
Mide consumo energético real usando codecarbon y pynvml para calcular "inteligencia por watt".
"""

import os
import sys
import time
import logging
import platform
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
import psutil

# Imports opcionales con fallbacks
try:
    from codecarbon import EmissionsTracker
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False
    EmissionsTracker = None

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None

# Configuración de logging
logger = logging.getLogger(__name__)


@dataclass
class EnergyMetrics:
    """Métricas de consumo energético."""
    # Energía total (joules)
    total_energy_joules: float = 0.0

    # Energía por componente
    cpu_energy_joules: float = 0.0
    gpu_energy_joules: float = 0.0
    ram_energy_joules: float = 0.0

    # Emisiones de carbono (kg CO2)
    carbon_emissions_kg: float = 0.0

    # Métricas de eficiencia
    joules_per_token: float = 0.0
    tokens_per_watt: float = 0.0
    intelligence_per_watt: float = 0.0  # Basado en accuracy * tokens_per_watt

    # Métricas de rendimiento
    power_consumption_watts: float = 0.0
    avg_power_draw: float = 0.0
    peak_power_draw: float = 0.0

    # Información del sistema
    system_info: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0

    # Metadata adicional
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnergyTrackerConfig:
    """Configuración del energy tracker."""
    enable_codecarbon: bool = True
    enable_gpu_monitoring: bool = True
    enable_cpu_monitoring: bool = True
    enable_ram_monitoring: bool = True
    tracking_interval_seconds: float = 1.0
    tracking_interval: float = 1.0  # Alias para compatibilidad
    gpu_device_ids: List[int] = field(default_factory=lambda: [0])  # GPUs a monitorear
    output_dir: str = "./energy_logs"
    log_energy_data: bool = True
    calculate_efficiency_metrics: bool = True


class GPUManager:
    """Gestor de GPUs usando pynvml."""

    def __init__(self, device_ids: List[int] = None):
        self.device_ids = device_ids or [0]
        self.initialized = False
        self.handles = {}
        self.gpu_count = 0

        if PYNVML_AVAILABLE:
            self._initialize_nvml()
        else:
            logger.warning("pynvml no disponible, monitoreo de GPU deshabilitado")

    def _initialize_nvml(self):
        """Inicializar NVML."""
        try:
            pynvml.nvmlInit()
            self.gpu_count = pynvml.nvmlDeviceGetCount()

            for device_id in self.device_ids:
                if device_id < self.gpu_count:
                    self.handles[device_id] = pynvml.nvmlDeviceGetHandleByIndex(device_id)

            self.initialized = True
            logger.info(f"✅ NVML inicializado, {len(self.handles)} GPUs disponibles")
        except Exception as e:
            logger.warning(f"❌ Error inicializando NVML: {e}")
            self.initialized = False

    def get_gpu_power_usage(self, device_id: int = 0) -> float:
        """Obtener consumo de energía de GPU en watts."""
        if not self.initialized or device_id not in self.handles:
            return 0.0

        try:
            handle = self.handles[device_id]
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)
            # Convertir de milliwatts a watts
            return power_usage / 1000.0
        except Exception as e:
            logger.debug(f"Error obteniendo power usage GPU {device_id}: {e}")
            return 0.0

    def get_gpu_memory_info(self, device_id: int = 0) -> Tuple[int, int]:
        """Obtener información de memoria GPU (usado, total en MB)."""
        if not self.initialized or device_id not in self.handles:
            return 0, 0

        try:
            handle = self.handles[device_id]
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            used_mb = info.used / 1024 / 1024
            total_mb = info.total / 1024 / 1024
            return int(used_mb), int(total_mb)
        except Exception as e:
            logger.debug(f"Error obteniendo memoria GPU {device_id}: {e}")
            return 0, 0

    def get_total_gpu_power(self) -> float:
        """Obtener consumo total de todas las GPUs monitoreadas."""
        total_power = 0.0
        for device_id in self.device_ids:
            total_power += self.get_gpu_power_usage(device_id)
        return total_power

    def shutdown(self):
        """Cerrar NVML."""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                self.initialized = False
                logger.info("✅ NVML cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando NVML: {e}")


class CarbonTracker:
    """Tracker de emisiones de carbono usando codecarbon."""

    def __init__(self, output_dir: str = "./energy_logs", tracking_interval: float = 1.0):
        self.output_dir = output_dir
        self.tracking_interval = tracking_interval
        self.tracker = None
        self.is_tracking = False
        self.emissions_data = []

        if CODECARBON_AVAILABLE:
            self._initialize_tracker()
        else:
            logger.warning("codecarbon no disponible, tracking de carbono deshabilitado")

    def _initialize_tracker(self):
        """Inicializar EmissionsTracker."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.tracker = EmissionsTracker(
                output_dir=self.output_dir,
                output_file="emissions.csv",
                measure_power_secs=self.tracking_interval,
                save_to_file=True
            )
            logger.info("✅ CodeCarbon EmissionsTracker inicializado")
        except Exception as e:
            logger.warning(f"❌ Error inicializando CodeCarbon: {e}")
            self.tracker = None

    def start_tracking(self):
        """Iniciar tracking de emisiones."""
        if self.tracker:
            try:
                self.tracker.start()
                self.is_tracking = True
                logger.info("🚀 Tracking de carbono iniciado")
            except Exception as e:
                logger.warning(f"Error iniciando tracking de carbono: {e}")

    def stop_tracking(self) -> float:
        """Detener tracking y retornar emisiones totales en kg CO2."""
        if not self.tracker or not self.is_tracking:
            return 0.0

        try:
            emissions = self.tracker.stop()
            self.is_tracking = False
            logger.info(f"⏹️ Tracking de carbono detenido, emisiones: {emissions:.6f} kg CO2")
            return emissions
        except Exception as e:
            logger.warning(f"Error deteniendo tracking de carbono: {e}")
            return 0.0


class EnergyTracker:
    """
    Tracker principal de consumo energético para EmpoorioLM.
    Integra codecarbon, pynvml y métricas del sistema.
    """

    def __init__(self, config: EnergyTrackerConfig = None):
        self.config = config or EnergyTrackerConfig()

        # Componentes
        self.gpu_manager = GPUManager(self.config.gpu_device_ids) if self.config.enable_gpu_monitoring and PYNVML_AVAILABLE else None
        self.carbon_tracker = CarbonTracker(self.config.output_dir, self.config.tracking_interval) if self.config.enable_codecarbon and CODECARBON_AVAILABLE else None

        # Estado de monitoreo
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_data = []
        self.start_time = 0.0

        # Información del sistema
        self.system_info = self._collect_system_info()

        logger.info("🚀 EnergyTracker inicializado")

    def _collect_system_info(self) -> Dict[str, Any]:
        """Recopilar información del sistema."""
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "gpu_available": self.gpu_manager and self.gpu_manager.initialized,
            "gpu_count": self.gpu_manager.gpu_count if self.gpu_manager else 0,
            "codecarbon_available": CODECARBON_AVAILABLE,
            "pynvml_available": PYNVML_AVAILABLE,
        }

        # Información detallada de GPUs
        if self.gpu_manager and self.gpu_manager.initialized:
            gpu_info = {}
            for device_id in self.config.gpu_device_ids:
                if device_id in self.gpu_manager.handles:
                    try:
                        handle = self.gpu_manager.handles[device_id]
                        name = pynvml.nvmlDeviceGetName(handle)
                        gpu_info[f"gpu_{device_id}"] = name.decode() if isinstance(name, bytes) else str(name)
                    except:
                        gpu_info[f"gpu_{device_id}"] = "Unknown"
            info["gpu_info"] = gpu_info

        # Convertir gpu_available a boolean explícitamente
        info["gpu_available"] = bool(self.gpu_manager and self.gpu_manager.initialized)

        return info

    def start_monitoring(self):
        """Iniciar monitoreo de consumo energético."""
        if self.is_monitoring:
            logger.warning("Monitoreo ya está activo")
            return

        self.start_time = time.time()
        self.monitoring_data = []
        self.is_monitoring = True

        # Iniciar carbon tracking
        if self.carbon_tracker:
            self.carbon_tracker.start_tracking()

        # Iniciar thread de monitoreo continuo
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("📊 Monitoreo de energía iniciado")

    def stop_monitoring(self, tokens_generated: int = 0, accuracy: float = 0.0) -> EnergyMetrics:
        """Detener monitoreo y calcular métricas finales."""
        if not self.is_monitoring:
            logger.warning("Monitoreo no está activo")
            return EnergyMetrics()

        end_time = time.time()
        duration = end_time - self.start_time
        self.is_monitoring = False

        # Esperar a que termine el thread de monitoreo
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

        # Detener carbon tracking
        carbon_emissions = 0.0
        if self.carbon_tracker:
            carbon_emissions = self.carbon_tracker.stop_tracking()

        # Calcular métricas
        metrics = self._calculate_final_metrics(duration, tokens_generated, accuracy, carbon_emissions)

        logger.info(f"📊 Monitoreo detenido. Energía total: {metrics.total_energy_joules:.2f}J, "
                   f"Carbono: {metrics.carbon_emissions_kg:.6f}kg CO2")

        return metrics

    def _monitoring_loop(self):
        """Loop continuo de monitoreo."""
        while self.is_monitoring:
            try:
                timestamp = time.time()
                data_point = {
                    "timestamp": timestamp,
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                    "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
                }

                # Datos de GPU
                if self.gpu_manager:
                    gpu_power = self.gpu_manager.get_total_gpu_power()
                    data_point["gpu_power_watts"] = gpu_power

                    gpu_memory = {}
                    for device_id in self.config.gpu_device_ids:
                        used, total = self.gpu_manager.get_gpu_memory_info(device_id)
                        gpu_memory[f"gpu_{device_id}_memory_used_mb"] = used
                        gpu_memory[f"gpu_{device_id}_memory_total_mb"] = total
                    data_point.update(gpu_memory)

                self.monitoring_data.append(data_point)

                # Log cada 10 segundos
                if len(self.monitoring_data) % 10 == 0:
                    logger.debug(f"📊 Punto de datos #{len(self.monitoring_data)} recopilado")

            except Exception as e:
                logger.debug(f"Error en monitoring loop: {e}")

            time.sleep(self.config.tracking_interval)

    def _calculate_final_metrics(self, duration: float, tokens_generated: int,
                               accuracy: float, carbon_emissions: float) -> EnergyMetrics:
        """Calcular métricas finales de energía."""
        metrics = EnergyMetrics()
        metrics.start_time = self.start_time
        metrics.end_time = self.start_time + duration
        metrics.duration_seconds = duration
        metrics.system_info = self.system_info
        metrics.carbon_emissions_kg = carbon_emissions

        # Calcular energía de CPU (estimación basada en uso)
        if self.monitoring_data:
            avg_cpu_percent = sum(d["cpu_percent"] for d in self.monitoring_data) / len(self.monitoring_data)
            # Estimación: CPU moderno consume ~65W TDP, escalado por uso
            cpu_tdp_watts = 65.0
            metrics.cpu_energy_joules = (avg_cpu_percent / 100.0) * cpu_tdp_watts * duration

            # Energía de RAM (estimación simple)
            avg_memory_percent = sum(d["memory_percent"] for d in self.monitoring_data) / len(self.monitoring_data)
            ram_power_watts = 5.0  # Estimación conservadora para RAM
            metrics.ram_energy_joules = (avg_memory_percent / 100.0) * ram_power_watts * duration

        # Energía de GPU
        if self.gpu_manager and self.monitoring_data:
            gpu_power_readings = [d.get("gpu_power_watts", 0) for d in self.monitoring_data if "gpu_power_watts" in d]
            if gpu_power_readings:
                avg_gpu_power = sum(gpu_power_readings) / len(gpu_power_readings)
                peak_gpu_power = max(gpu_power_readings)
                metrics.gpu_energy_joules = avg_gpu_power * duration
                metrics.avg_power_draw = avg_gpu_power
                metrics.peak_power_draw = peak_gpu_power
                metrics.power_consumption_watts = avg_gpu_power

        # Energía total
        metrics.total_energy_joules = (
            metrics.cpu_energy_joules +
            metrics.gpu_energy_joules +
            metrics.ram_energy_joules
        )

        # Métricas de eficiencia
        if tokens_generated > 0:
            metrics.joules_per_token = metrics.total_energy_joules / tokens_generated
            metrics.tokens_per_watt = tokens_generated / (metrics.total_energy_joules / duration) if duration > 0 and metrics.total_energy_joules > 0 else 0

            # "Inteligencia por watt" = accuracy * tokens_per_watt
            metrics.intelligence_per_watt = accuracy * metrics.tokens_per_watt

        # Metadata adicional
        metrics.metadata = {
            "data_points_collected": len(self.monitoring_data),
            "tokens_generated": tokens_generated,
            "accuracy": accuracy,
            "config": self.config.__dict__,
        }

        return metrics

    @contextmanager
    def track_inference(self, tokens_expected: int = 0):
        """
        Context manager para trackear una inferencia completa.

        Args:
            tokens_expected: Número aproximado de tokens esperados

        Yields:
            Función para actualizar métricas durante la inferencia
        """
        self.start_monitoring()

        update_func = lambda tokens=0, accuracy=0.0: None  # Placeholder

        try:
            yield update_func
        finally:
            # En un uso real, update_func sería llamada para actualizar tokens/accuracy
            metrics = self.stop_monitoring(tokens_expected, 0.0)
            logger.info(f"🔋 Inferencia completada: {metrics.total_energy_joules:.2f}J, "
                       f"{metrics.joules_per_token:.4f}J/token")

    def get_current_power_draw(self) -> float:
        """Obtener consumo de energía actual en watts."""
        power_draw = 0.0

        # CPU (estimación)
        cpu_percent = psutil.cpu_percent(interval=None)
        power_draw += (cpu_percent / 100.0) * 65.0  # TDP estimado

        # GPU
        if self.gpu_manager:
            power_draw += self.gpu_manager.get_total_gpu_power()

        # RAM (estimación)
        ram_percent = psutil.virtual_memory().percent
        power_draw += (ram_percent / 100.0) * 5.0

        return power_draw

    def cleanup(self):
        """Limpiar recursos."""
        if self.gpu_manager:
            self.gpu_manager.shutdown()

        if self.carbon_tracker and self.carbon_tracker.is_tracking:
            self.carbon_tracker.stop_tracking()

        logger.info("🧹 EnergyTracker limpiado")


# Funciones de conveniencia
def create_energy_tracker(enable_gpu: bool = True, enable_carbon: bool = True) -> EnergyTracker:
    """Crear un EnergyTracker con configuración por defecto."""
    config = EnergyTrackerConfig(
        enable_gpu_monitoring=enable_gpu,
        enable_codecarbon=enable_carbon
    )
    return EnergyTracker(config)


def track_function_energy(func, *args, tokens_expected: int = 0, **kwargs) -> Tuple[Any, EnergyMetrics]:
    """
    Decorador/wrapper para trackear energía de una función.

    Args:
        func: Función a trackear
        tokens_expected: Tokens esperados
        *args, **kwargs: Argumentos de la función

    Returns:
        Tupla (resultado, métricas_energía)
    """
    tracker = create_energy_tracker()

    with tracker.track_inference(tokens_expected):
        result = func(*args, **kwargs)

    # Calcular métricas finales (esto sería mejor si se pudiera actualizar dinámicamente)
    metrics = tracker.stop_monitoring(tokens_expected, 0.0)
    tracker.cleanup()

    return result, metrics


# Compatibilidad con sistemas sin dependencias
if not CODECARBON_AVAILABLE:
    logger.warning("⚠️ codecarbon no instalado. Instale con: pip install codecarbon")

if not PYNVML_AVAILABLE:
    logger.warning("⚠️ pynvml no instalado. Instale con: pip install pynvml")
    if platform.system() == "Darwin":  # macOS
        logger.info("💡 En macOS, considere usar Intel Power Gadget para mediciones de energía más precisas")