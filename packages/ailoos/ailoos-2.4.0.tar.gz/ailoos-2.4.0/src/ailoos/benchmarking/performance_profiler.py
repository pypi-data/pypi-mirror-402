import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json
from datetime import datetime
import statistics

# Optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. CPU/memory profiling will be limited.")

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False
    print("Warning: GPUtil not installed. GPU profiling will be disabled.")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

@dataclass
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    gpu_utilization: float = 0.0
    gpu_memory_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0

@dataclass
class ProfilingResult:
    operation: str
    start_time: float
    end_time: float
    duration: float
    metrics_over_time: List[PerformanceMetrics] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

class PerformanceProfiler:
    """
    Perfilado detallado de rendimiento y uso de recursos durante la ejecución de benchmarks.
    Monitorea CPU, memoria, GPU, disco y red en tiempo real.
    """

    def __init__(self, results_dir: str = "benchmark_results",
                 sampling_interval: float = 0.1, log_level: str = "INFO"):
        self.results_dir = Path(results_dir)
        self.sampling_interval = sampling_interval
        self.logger = self._setup_logger(log_level)

        self._profiling_active = False
        self._metrics_thread = None
        self._current_metrics = []
        self._start_time = None
        self._end_time = None

        # Get initial system info
        self.system_info = self._get_system_info()

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        file_handler = logging.FileHandler(self.results_dir / "performance_profiler.log")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema."""
        info = {
            "cpu_count": psutil.cpu_count() if PSUTIL_AVAILABLE else "N/A",
            "cpu_count_logical": psutil.cpu_count(logical=True) if PSUTIL_AVAILABLE else "N/A",
            "memory_total_gb": psutil.virtual_memory().total / (1024**3) if PSUTIL_AVAILABLE else "N/A",
        }

        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                info["gpu_count"] = len(gpus)
                info["gpu_info"] = [{"name": gpu.name, "memory_total_mb": gpu.memoryTotal}
                                   for gpu in gpus]
            except:
                info["gpu_count"] = 0
                info["gpu_info"] = []

        if TORCH_AVAILABLE:
            info["torch_available"] = True
            info["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info["cuda_device_count"] = torch.cuda.device_count()
        else:
            info["torch_available"] = False
            info["cuda_available"] = False

        return info

    def start_profiling(self, operation: str) -> str:
        """
        Inicia el perfilado de rendimiento para una operación específica.
        """
        if self._profiling_active:
            self.logger.warning("Profiling already active, stopping previous session")
            self.stop_profiling()

        self._profiling_active = True
        self._current_metrics = []
        self._start_time = time.time()
        self._operation = operation

        # Start metrics collection thread
        self._metrics_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self._metrics_thread.start()

        self.logger.info(f"Started profiling for operation: {operation}")
        return operation

    def stop_profiling(self) -> ProfilingResult:
        """
        Detiene el perfilado y devuelve los resultados.
        """
        if not self._profiling_active:
            self.logger.warning("No active profiling session to stop")
            return ProfilingResult("", 0, 0, 0)

        self._profiling_active = False
        self._end_time = time.time()

        # Wait for metrics thread to finish
        if self._metrics_thread and self._metrics_thread.is_alive():
            self._metrics_thread.join(timeout=1.0)

        duration = self._end_time - self._start_time

        # Generate summary
        summary = self._generate_summary()

        result = ProfilingResult(
            operation=self._operation,
            start_time=self._start_time,
            end_time=self._end_time,
            duration=duration,
            metrics_over_time=self._current_metrics.copy(),
            summary=summary
        )

        self._save_profiling_result(result)
        self.logger.info(f"Stopped profiling for operation: {self._operation} (duration: {duration:.2f}s)")
        return result

    def profile_function(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Perfilar una función específica.
        """
        operation = f"{func.__name__}"
        self.start_profiling(operation)

        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            return result, self.stop_profiling()
        except Exception as e:
            self.stop_profiling()
            raise e

    def _collect_metrics_loop(self):
        """Loop principal para recopilar métricas."""
        while self._profiling_active:
            metrics = self._collect_current_metrics()
            self._current_metrics.append(metrics)
            time.sleep(self.sampling_interval)

    def _collect_current_metrics(self) -> PerformanceMetrics:
        """Recopila métricas actuales del sistema."""
        timestamp = time.time()

        metrics = PerformanceMetrics(timestamp=timestamp)

        if PSUTIL_AVAILABLE:
            # CPU and Memory
            metrics.cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            metrics.memory_percent = memory.percent
            metrics.memory_mb = memory.used / (1024**2)

            # Disk I/O (simplified - would need initial counters for accurate rates)
            try:
                disk_io = psutil.disk_io_counters()
                metrics.disk_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
                metrics.disk_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0
            except:
                pass

            # Network I/O
            try:
                net_io = psutil.net_io_counters()
                metrics.network_sent_mb = net_io.bytes_sent / (1024**2) if net_io else 0
                metrics.network_recv_mb = net_io.bytes_recv / (1024**2) if net_io else 0
            except:
                pass

        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    # Average across all GPUs
                    gpu_utils = [gpu.load * 100 for gpu in gpus]
                    gpu_mem_utils = [gpu.memoryUtil * 100 for gpu in gpus]
                    gpu_mem_used = [gpu.memoryUsed for gpu in gpus]

                    metrics.gpu_utilization = statistics.mean(gpu_utils)
                    metrics.gpu_memory_percent = statistics.mean(gpu_mem_utils)
                    metrics.gpu_memory_mb = statistics.mean(gpu_mem_used)
            except:
                pass

        return metrics

    def _generate_summary(self) -> Dict[str, Any]:
        """Genera un resumen estadístico de las métricas recopiladas."""
        if not self._current_metrics:
            return {}

        # Extract values for each metric
        cpu_percents = [m.cpu_percent for m in self._current_metrics]
        memory_percents = [m.memory_percent for m in self._current_metrics]
        memory_mbs = [m.memory_mb for m in self._current_metrics]
        gpu_utils = [m.gpu_utilization for m in self._current_metrics]
        gpu_mem_percents = [m.gpu_memory_percent for m in self._current_metrics]

        summary = {
            "system_info": self.system_info,
            "total_samples": len(self._current_metrics),
            "sampling_interval": self.sampling_interval,
            "cpu_percent": {
                "mean": statistics.mean(cpu_percents) if cpu_percents else 0,
                "max": max(cpu_percents) if cpu_percents else 0,
                "min": min(cpu_percents) if cpu_percents else 0,
                "std": statistics.stdev(cpu_percents) if len(cpu_percents) > 1 else 0
            },
            "memory_percent": {
                "mean": statistics.mean(memory_percents) if memory_percents else 0,
                "max": max(memory_percents) if memory_percents else 0,
                "min": min(memory_percents) if memory_percents else 0,
                "std": statistics.stdev(memory_percents) if len(memory_percents) > 1 else 0
            },
            "memory_mb": {
                "mean": statistics.mean(memory_mbs) if memory_mbs else 0,
                "max": max(memory_mbs) if memory_mbs else 0,
                "min": min(memory_mbs) if memory_mbs else 0,
                "std": statistics.stdev(memory_mbs) if len(memory_mbs) > 1 else 0
            },
            "gpu_utilization": {
                "mean": statistics.mean(gpu_utils) if gpu_utils else 0,
                "max": max(gpu_utils) if gpu_utils else 0,
                "min": min(gpu_utils) if gpu_utils else 0,
                "std": statistics.stdev(gpu_utils) if len(gpu_utils) > 1 else 0
            },
            "gpu_memory_percent": {
                "mean": statistics.mean(gpu_mem_percents) if gpu_mem_percents else 0,
                "max": max(gpu_mem_percents) if gpu_mem_percents else 0,
                "min": min(gpu_mem_percents) if gpu_mem_percents else 0,
                "std": statistics.stdev(gpu_mem_percents) if len(gpu_mem_percents) > 1 else 0
            }
        }

        return summary

    def _save_profiling_result(self, result: ProfilingResult):
        """Guarda los resultados del perfilado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"profiling_{result.operation}_{timestamp}.json"
        filepath = self.results_dir / filename

        result_dict = {
            "operation": result.operation,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "duration": result.duration,
            "summary": result.summary,
            "metrics_over_time": [m.__dict__ for m in result.metrics_over_time]
        }

        with open(filepath, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)

        self.logger.info(f"Profiling result saved to {filepath}")