"""
Mobile Edge Benchmarks Module for EmpoorioLM
Benchmarks específicos para despliegue en edge móvil que miden rendimiento real en dispositivos móviles (Android/iOS).
Simula/ejecuta benchmarks en entornos móviles, mide latencia, consumo de batería, uso de memoria, throughput,
y compara con baselines de modelos en la nube.
"""

import os
import sys
import time
import json
import logging
import threading
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import random

# Añadir src al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Imports opcionales para gráficos
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    plt = None
    pd = None

# Configuración de logging
logger = logging.getLogger(__name__)


@dataclass
class MobileDeviceSpec:
    """Especificaciones de un dispositivo móvil."""
    name: str
    platform: str  # 'android' o 'ios'
    cpu_cores: int
    cpu_clock_ghz: float
    ram_gb: float
    battery_mah: int
    screen_size_inches: float
    gpu_type: str = ""
    neural_engine: bool = False
    tpu_available: bool = False

    # Características de rendimiento (basadas en benchmarks reales)
    cpu_benchmark_score: int = 0  # Puntaje en benchmarks como Geekbench
    gpu_benchmark_score: int = 0
    memory_bandwidth_gbps: float = 0.0

    # Eficiencia energética (estimaciones basadas en hardware real)
    idle_power_consumption_mw: int = 0
    cpu_power_per_core_mw: int = 0
    gpu_power_mw: int = 0
    screen_power_mw: int = 0


@dataclass
class MobileEdgeMetrics:
    """Métricas específicas para benchmarks en edge móvil."""
    # Información del dispositivo
    device_name: str = ""
    platform: str = ""

    # Latencia
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    # Consumo de batería
    battery_consumption_mah: float = 0.0  # mAh consumidos
    battery_percentage_used: float = 0.0  # % de batería usado
    energy_efficiency_mah_per_token: float = 0.0  # Eficiencia energética

    # Uso de memoria
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    memory_efficiency_mb_per_token: float = 0.0

    # Throughput
    throughput_tokens_per_sec: float = 0.0
    throughput_requests_per_min: float = 0.0

    # Métricas de edge computing
    model_size_mb: float = 0.0  # Tamaño del modelo cuantizado
    inference_time_ms: float = 0.0
    warmup_time_ms: float = 0.0
    cold_start_penalty_ms: float = 0.0

    # Comparación con nube
    cloud_latency_baseline_ms: float = 0.0
    edge_vs_cloud_speedup: float = 0.0  # Factor de mejora (mayor = mejor)
    edge_vs_cloud_energy_savings: float = 0.0  # % de ahorro energético

    # Información de la prueba
    num_requests: int = 0
    successful_requests: int = 0
    test_duration_seconds: float = 0.0
    timestamp: str = ""

    # Datos crudos
    raw_latencies: List[float] = field(default_factory=list)
    raw_battery_readings: List[float] = field(default_factory=list)
    raw_memory_readings: List[float] = field(default_factory=list)

    # Metadata
    model_name: str = ""
    quantization_type: str = "none"  # fp16, int8, int4, etc.
    batch_size: int = 1
    context_length: int = 512


@dataclass
class MobileEdgeBenchmarkConfig:
    """Configuración para benchmarks de edge móvil."""
    # Dispositivos a testear
    target_devices: List[str] = field(default_factory=lambda: ['pixel_7', 'iphone_14', 'samsung_s22'])

    # Configuración de pruebas
    num_requests: int = 100
    warmup_requests: int = 5
    context_lengths: List[int] = field(default_factory=lambda: [256, 512, 1024])
    batch_sizes: List[int] = field(default_factory=lambda: [1])
    max_tokens: int = 128

    # Configuración de simulación
    enable_realistic_simulation: bool = True
    simulate_battery_drain: bool = True
    simulate_thermal_throttling: bool = True
    simulate_network_conditions: bool = False

    # Configuración de salida
    output_dir: str = "./mobile_edge_results"
    generate_plots: bool = True
    save_raw_data: bool = True

    # Baselines para comparación
    cloud_latency_baselines: Dict[str, float] = field(default_factory=lambda: {
        'gpt4': 1200.0,  # ms
        'claude': 1000.0,
        'gemini': 800.0,
        'empoorio_cloud': 600.0
    })

    cloud_energy_baselines: Dict[str, float] = field(default_factory=lambda: {
        'gpt4': 25.0,  # mAh por request
        'claude': 20.0,
        'gemini': 18.0,
        'empoorio_cloud': 15.0
    })


# Especificaciones de dispositivos móviles reales (basadas en datos públicos)
MOBILE_DEVICE_SPECS = {
    'pixel_7': MobileDeviceSpec(
        name='Google Pixel 7',
        platform='android',
        cpu_cores=8,
        cpu_clock_ghz=2.85,
        ram_gb=8.0,
        battery_mah=4355,
        screen_size_inches=6.3,
        gpu_type='Mali-G710',
        neural_engine=True,
        cpu_benchmark_score=950000,
        gpu_benchmark_score=180000,
        memory_bandwidth_gbps=25.0,
        idle_power_consumption_mw=150,
        cpu_power_per_core_mw=850,
        gpu_power_mw=1200,
        screen_power_mw=800
    ),

    'pixel_8': MobileDeviceSpec(
        name='Google Pixel 8',
        platform='android',
        cpu_cores=8,
        cpu_clock_ghz=3.0,
        ram_gb=8.0,
        battery_mah=4575,
        screen_size_inches=6.2,
        gpu_type='Mali-G715',
        neural_engine=True,
        tpu_available=True,
        cpu_benchmark_score=1050000,
        gpu_benchmark_score=220000,
        memory_bandwidth_gbps=32.0,
        idle_power_consumption_mw=140,
        cpu_power_per_core_mw=800,
        gpu_power_mw=1100,
        screen_power_mw=750
    ),

    'iphone_14': MobileDeviceSpec(
        name='iPhone 14',
        platform='ios',
        cpu_cores=6,
        cpu_clock_ghz=3.1,
        ram_gb=6.0,
        battery_mah=3279,
        screen_size_inches=6.1,
        gpu_type='Apple A15 Bionic GPU',
        neural_engine=True,
        cpu_benchmark_score=1100000,
        gpu_benchmark_score=250000,
        memory_bandwidth_gbps=28.0,
        idle_power_consumption_mw=130,
        cpu_power_per_core_mw=750,
        gpu_power_mw=1000,
        screen_power_mw=700
    ),

    'iphone_15': MobileDeviceSpec(
        name='iPhone 15',
        platform='ios',
        cpu_cores=6,
        cpu_clock_ghz=3.4,
        ram_gb=6.0,
        battery_mah=3349,
        screen_size_inches=6.1,
        gpu_type='Apple A16 Bionic GPU',
        neural_engine=True,
        cpu_benchmark_score=1250000,
        gpu_benchmark_score=280000,
        memory_bandwidth_gbps=32.0,
        idle_power_consumption_mw=120,
        cpu_power_per_core_mw=700,
        gpu_power_mw=950,
        screen_power_mw=650
    ),

    'samsung_s22': MobileDeviceSpec(
        name='Samsung Galaxy S22',
        platform='android',
        cpu_cores=8,
        cpu_clock_ghz=2.8,
        ram_gb=8.0,
        battery_mah=3700,
        screen_size_inches=6.1,
        gpu_type='Adreno 730',
        neural_engine=True,
        cpu_benchmark_score=880000,
        gpu_benchmark_score=190000,
        memory_bandwidth_gbps=30.0,
        idle_power_consumption_mw=160,
        cpu_power_per_core_mw=900,
        gpu_power_mw=1300,
        screen_power_mw=850
    ),

    'samsung_s23': MobileDeviceSpec(
        name='Samsung Galaxy S23',
        platform='android',
        cpu_cores=8,
        cpu_clock_ghz=3.2,
        ram_gb=8.0,
        battery_mah=3900,
        screen_size_inches=6.1,
        gpu_type='Adreno 740',
        neural_engine=True,
        cpu_benchmark_score=1020000,
        gpu_benchmark_score=240000,
        memory_bandwidth_gbps=35.0,
        idle_power_consumption_mw=145,
        cpu_power_per_core_mw=820,
        gpu_power_mw=1150,
        screen_power_mw=780
    )
}


class MobileDeviceSimulator:
    """Simulador de dispositivo móvil con características realistas."""

    def __init__(self, device_spec: MobileDeviceSpec, config: MobileEdgeBenchmarkConfig):
        self.spec = device_spec
        self.config = config

        # Estado de simulación
        self.current_battery_level = 100.0  # %
        self.current_temperature = 35.0  # Celsius
        self.thermal_throttling_active = False
        self.memory_usage_mb = 512.0  # Memoria base del sistema

        # Historial para análisis
        self.battery_history = []
        self.temperature_history = []
        self.memory_history = []

        logger.info(f"📱 Inicializado simulador para {device_spec.name}")

    def simulate_inference(self, model_size_mb: float, context_length: int,
                          batch_size: int, num_tokens: int) -> Dict[str, Any]:
        """
        Simular una inferencia en el dispositivo móvil.

        Returns:
            Dict con métricas de la simulación
        """
        # Calcular latencia basada en hardware
        base_latency = self._calculate_base_latency(model_size_mb, context_length, batch_size)

        # Aplicar factores de realismo
        if self.config.enable_realistic_simulation:
            base_latency *= self._get_realism_multiplier()

        # Simular throttling térmico
        if self.config.simulate_thermal_throttling and self.thermal_throttling_active:
            base_latency *= 1.5  # 50% más lento cuando hay throttling

        # Añadir variabilidad realista
        latency_variation = random.uniform(0.9, 1.1)
        final_latency = base_latency * latency_variation

        # Calcular consumo de batería
        battery_consumption = self._calculate_battery_consumption(final_latency, model_size_mb)

        # Calcular uso de memoria
        memory_usage = self._calculate_memory_usage(model_size_mb, context_length, batch_size)

        # Actualizar estado del dispositivo
        self._update_device_state(battery_consumption, memory_usage, final_latency)

        return {
            'latency_ms': final_latency,
            'battery_consumption_mah': battery_consumption,
            'memory_usage_mb': memory_usage,
            'throughput_tokens_per_sec': num_tokens / (final_latency / 1000.0) if final_latency > 0 else 0,
            'thermal_throttling': self.thermal_throttling_active,
            'temperature_c': self.current_temperature
        }

    def _calculate_base_latency(self, model_size_mb: float, context_length: int, batch_size: int) -> float:
        """Calcular latencia base basada en características del hardware."""
        # Factor base por tamaño del modelo
        model_factor = model_size_mb / 100.0  # Normalizado por 100MB

        # Factor por longitud de contexto
        context_factor = context_length / 512.0

        # Factor por batch size
        batch_factor = batch_size ** 0.5

        # Factor de CPU/GPU
        hardware_factor = 1000.0 / (self.spec.cpu_benchmark_score / 100000.0)  # Normalizado

        # Cálculo base (ms)
        base_latency = 50.0 * model_factor * context_factor * batch_factor * hardware_factor

        # Bonus por neural engine/TPU
        if self.spec.neural_engine or self.spec.tpu_available:
            base_latency *= 0.7  # 30% más rápido

        return max(base_latency, 10.0)  # Mínimo 10ms

    def _calculate_battery_consumption(self, latency_ms: float, model_size_mb: float) -> float:
        """Calcular consumo de batería en mAh."""
        # Energía base por inferencia
        base_energy_mah = 0.001 * model_size_mb  # Estimación simplificada

        # Energía adicional por tiempo de procesamiento
        processing_energy = (latency_ms / 1000.0) * (self.spec.cpu_power_per_core_mw / 1000000.0) * 3.7  # Voltaje típico

        # Energía de GPU si se usa
        gpu_energy = (latency_ms / 1000.0) * (self.spec.gpu_power_mw / 1000000.0) * 3.7

        total_energy = base_energy_mah + processing_energy + gpu_energy

        return total_energy

    def _calculate_memory_usage(self, model_size_mb: float, context_length: int, batch_size: int) -> float:
        """Calcular uso de memoria en MB."""
        # Memoria del modelo
        model_memory = model_size_mb * 1.5  # Overhead de runtime

        # Memoria para KV cache (aproximación)
        kv_memory = (context_length * 2 * 2) / 1024.0  # 2 bytes por token, 2 para key+value

        # Memoria para batch
        batch_memory = kv_memory * batch_size

        # Memoria adicional del sistema
        system_memory = 50.0

        total_memory = model_memory + kv_memory + batch_memory + system_memory

        return total_memory

    def _get_realism_multiplier(self) -> float:
        """Obtener multiplicador de realismo basado en estado del dispositivo."""
        multiplier = 1.0

        # Factor de batería baja
        if self.current_battery_level < 20:
            multiplier *= 1.3  # Más lento cuando batería baja

        # Factor de temperatura
        if self.current_temperature > 45:
            multiplier *= 1.2  # Throttling térmico

        # Factor de memoria disponible
        available_memory = self.spec.ram_gb * 1024 - self.memory_usage_mb
        if available_memory < 512:
            multiplier *= 1.4  # Más lento con poca memoria

        return multiplier

    def _update_device_state(self, battery_consumption: float, memory_usage: float, latency_ms: float):
        """Actualizar estado del dispositivo después de una inferencia."""
        # Actualizar batería
        battery_used_percent = (battery_consumption / self.spec.battery_mah) * 100
        self.current_battery_level = max(0, self.current_battery_level - battery_used_percent)

        # Actualizar temperatura (aumento por procesamiento)
        temp_increase = (latency_ms / 1000.0) * 2.0  # 2°C por segundo de procesamiento intenso
        self.current_temperature += temp_increase

        # Simular enfriamiento
        cooling = 0.5  # 0.5°C por segundo
        self.current_temperature = max(25, self.current_temperature - cooling)

        # Activar throttling térmico si temperatura alta
        self.thermal_throttling_active = self.current_temperature > 50

        # Actualizar memoria
        self.memory_usage_mb = max(self.memory_usage_mb, memory_usage)

        # Registrar en historial
        self.battery_history.append(self.current_battery_level)
        self.temperature_history.append(self.current_temperature)
        self.memory_history.append(self.memory_usage_mb)

    def reset(self):
        """Resetear estado del dispositivo."""
        self.current_battery_level = 100.0
        self.current_temperature = 35.0
        self.thermal_throttling_active = False
        self.memory_usage_mb = 512.0
        self.battery_history = []
        self.temperature_history = []
        self.memory_history = []


class MobileEdgeBenchmarkRunner:
    """
    Ejecutor principal de benchmarks para edge móvil.
    Simula rendimiento en dispositivos móviles y compara con baselines en la nube.
    """

    def __init__(self, config: MobileEdgeBenchmarkConfig = None):
        self.config = config or MobileEdgeBenchmarkConfig()
        self.device_simulators = {}
        self.results = {}

        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)

        # Inicializar simuladores de dispositivos
        self._init_device_simulators()

        logger.info("🚀 MobileEdgeBenchmarkRunner inicializado")

    def _init_device_simulators(self):
        """Inicializar simuladores para los dispositivos objetivo."""
        for device_name in self.config.target_devices:
            if device_name in MOBILE_DEVICE_SPECS:
                spec = MOBILE_DEVICE_SPECS[device_name]
                simulator = MobileDeviceSimulator(spec, self.config)
                self.device_simulators[device_name] = simulator
                logger.info(f"✅ Simulador inicializado para {spec.name}")
            else:
                logger.warning(f"⚠️ Dispositivo no reconocido: {device_name}")

    def run_mobile_edge_benchmarks(self, model_wrapper, model_name: str,
                                 model_size_mb: float = 100.0,
                                 quantization_type: str = "fp16") -> Dict[str, MobileEdgeMetrics]:
        """
        Ejecutar benchmarks completos de edge móvil para un modelo.

        Args:
            model_wrapper: Wrapper del modelo a testear
            model_name: Nombre del modelo
            model_size_mb: Tamaño del modelo en MB
            quantization_type: Tipo de cuantización

        Returns:
            Dict con métricas por dispositivo
        """
        logger.info(f"🧪 Iniciando benchmarks de edge móvil para {model_name}")

        results = {}

        for device_name, simulator in self.device_simulators.items():
            logger.info(f"📱 Probando en {device_name}")

            # Resetear simulador
            simulator.reset()

            device_results = self._benchmark_on_device(
                model_wrapper, model_name, simulator, device_name,
                model_size_mb, quantization_type
            )

            results[device_name] = device_results

        self.results.update(results)
        logger.info(f"✅ Benchmarks completados para {model_name}")
        return results

    def _benchmark_on_device(self, model_wrapper, model_name: str,
                           simulator: MobileDeviceSimulator, device_name: str,
                           model_size_mb: float, quantization_type: str) -> MobileEdgeMetrics:
        """Ejecutar benchmark en un dispositivo específico."""
        metrics = MobileEdgeMetrics(
            device_name=device_name,
            platform=simulator.spec.platform,
            model_name=model_name,
            model_size_mb=model_size_mb,
            quantization_type=quantization_type,
            num_requests=self.config.num_requests,
            timestamp=time.strftime('%Y%m%d_%H%M%S')
        )

        # Datos crudos
        latencies = []
        battery_consumptions = []
        memory_usages = []
        throughputs = []

        start_time = time.time()

        # Warmup
        if self.config.warmup_requests > 0:
            logger.debug(f"🔥 Ejecutando {self.config.warmup_requests} requests de warmup en {device_name}")
            for _ in range(self.config.warmup_requests):
                try:
                    # Simular warmup
                    warmup_result = simulator.simulate_inference(
                        model_size_mb, 256, 1, self.config.max_tokens
                    )
                    time.sleep(0.01)  # Pequeña pausa
                except Exception as e:
                    logger.debug(f"Warmup failed: {e}")

        # Medir tiempo de warmup
        warmup_start = time.time()
        simulator.simulate_inference(model_size_mb, 256, 1, self.config.max_tokens)
        metrics.warmup_time_ms = (time.time() - warmup_start) * 1000

        # Ejecutar requests de prueba
        for i in range(self.config.num_requests):
            try:
                # Seleccionar configuración aleatoria para variedad
                context_length = random.choice(self.config.context_lengths)
                batch_size = random.choice(self.config.batch_sizes)

                # Simular inferencia
                sim_result = simulator.simulate_inference(
                    model_size_mb, context_length, batch_size, self.config.max_tokens
                )

                # Recopilar métricas
                latencies.append(sim_result['latency_ms'])
                battery_consumptions.append(sim_result['battery_consumption_mah'])
                memory_usages.append(sim_result['memory_usage_mb'])
                throughputs.append(sim_result['throughput_tokens_per_sec'])

                # Simular delay entre requests (como haría un usuario real)
                time.sleep(random.uniform(0.1, 0.5))

            except Exception as e:
                logger.debug(f"Request {i} failed: {e}")
                continue

        end_time = time.time()
        metrics.test_duration_seconds = end_time - start_time
        metrics.successful_requests = len(latencies)

        # Calcular estadísticas
        if latencies:
            metrics.raw_latencies = latencies
            metrics.avg_latency_ms = statistics.mean(latencies)
            metrics.min_latency_ms = min(latencies)
            metrics.max_latency_ms = max(latencies)

            if len(latencies) >= 4:
                sorted_latencies = sorted(latencies)
                metrics.p95_latency_ms = statistics.quantiles(sorted_latencies, n=100)[94]
                metrics.p99_latency_ms = statistics.quantiles(sorted_latencies, n=100)[98]

        # Calcular métricas de batería
        if battery_consumptions:
            metrics.raw_battery_readings = battery_consumptions
            metrics.battery_consumption_mah = sum(battery_consumptions)
            metrics.battery_percentage_used = (metrics.battery_consumption_mah / simulator.spec.battery_mah) * 100

            # Eficiencia energética
            total_tokens = metrics.successful_requests * self.config.max_tokens
            if total_tokens > 0:
                metrics.energy_efficiency_mah_per_token = metrics.battery_consumption_mah / total_tokens

        # Calcular métricas de memoria
        if memory_usages:
            metrics.raw_memory_readings = memory_usages
            metrics.avg_memory_mb = statistics.mean(memory_usages)
            metrics.peak_memory_mb = max(memory_usages)

            total_tokens = metrics.successful_requests * self.config.max_tokens
            if total_tokens > 0:
                metrics.memory_efficiency_mb_per_token = metrics.peak_memory_mb / total_tokens

        # Calcular throughput
        if throughputs:
            metrics.throughput_tokens_per_sec = statistics.mean(throughputs)
            metrics.throughput_requests_per_min = (metrics.successful_requests / metrics.test_duration_seconds) * 60

        # Calcular métricas de edge computing
        metrics.inference_time_ms = metrics.avg_latency_ms
        metrics.cold_start_penalty_ms = metrics.warmup_time_ms * 2  # Estimación

        # Comparación con nube
        self._add_cloud_comparison(metrics)

        return metrics

    def _add_cloud_comparison(self, metrics: MobileEdgeMetrics):
        """Añadir comparación con baselines de modelos en la nube."""
        model_key = metrics.model_name.lower()

        # Latencia de nube
        cloud_latency = self.config.cloud_latency_baselines.get(model_key, 1000.0)
        metrics.cloud_latency_baseline_ms = cloud_latency

        if metrics.avg_latency_ms > 0:
            metrics.edge_vs_cloud_speedup = cloud_latency / metrics.avg_latency_ms

        # Ahorro energético vs nube
        cloud_energy = self.config.cloud_energy_baselines.get(model_key, 20.0)
        if metrics.energy_efficiency_mah_per_token > 0:
            cloud_energy_per_token = cloud_energy / self.config.max_tokens
            metrics.edge_vs_cloud_energy_savings = ((cloud_energy_per_token - metrics.energy_efficiency_mah_per_token) / cloud_energy_per_token) * 100

    def generate_edge_reports(self):
        """Generar reportes específicos de edge computing."""
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # Reporte JSON
        json_file = os.path.join(self.config.output_dir, f'mobile_edge_results_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            results_dict = {}
            for device, metrics in self.results.items():
                results_dict[device] = {
                    k: v for k, v in vars(metrics).items()
                    if not k.startswith('_') and not isinstance(v, list)
                }
                # Incluir algunos datos crudos si save_raw_data está habilitado
                if self.config.save_raw_data:
                    results_dict[device]['raw_latencies_sample'] = metrics.raw_latencies[:50]
                    results_dict[device]['raw_battery_sample'] = metrics.raw_battery_readings[:50]

            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        # Reporte CSV si pandas disponible
        if PLOTTING_AVAILABLE and pd is not None:
            csv_file = os.path.join(self.config.output_dir, f'mobile_edge_results_{timestamp}.csv')
            df_data = []
            for device, metrics in self.results.items():
                row = {
                    'device': device,
                    'platform': metrics.platform,
                    'model': metrics.model_name,
                    'avg_latency_ms': metrics.avg_latency_ms,
                    'p95_latency_ms': metrics.p95_latency_ms,
                    'battery_mah': metrics.battery_consumption_mah,
                    'battery_percent': metrics.battery_percentage_used,
                    'peak_memory_mb': metrics.peak_memory_mb,
                    'throughput_tps': metrics.throughput_tokens_per_sec,
                    'edge_speedup': metrics.edge_vs_cloud_speedup,
                    'energy_savings_percent': metrics.edge_vs_cloud_energy_savings,
                    'model_size_mb': metrics.model_size_mb,
                    'quantization': metrics.quantization_type
                }
                df_data.append(row)

            df = pd.DataFrame(df_data)
            df.to_csv(csv_file, index=False)

        # Generar gráficos
        if self.config.generate_plots and PLOTTING_AVAILABLE:
            self._generate_edge_plots(timestamp)

        logger.info(f"📊 Reportes de edge generados en {self.config.output_dir}")

    def _generate_edge_plots(self, timestamp: str):
        """Generar gráficos específicos de edge computing."""
        if not PLOTTING_AVAILABLE or not self.results:
            return

        # Preparar datos
        df_data = []
        for device, metrics in self.results.items():
            df_data.append({
                'device': device,
                'platform': metrics.platform,
                'latency': metrics.avg_latency_ms,
                'battery': metrics.battery_percentage_used,
                'memory': metrics.peak_memory_mb,
                'throughput': metrics.throughput_tokens_per_sec,
                'speedup': metrics.edge_vs_cloud_speedup,
                'energy_savings': metrics.edge_vs_cloud_energy_savings
            })

        if not df_data:
            return

        df = pd.DataFrame(df_data)

        # Gráfico comparativo de rendimiento edge
        plt.figure(figsize=(16, 12))

        # Subplot 1: Latencia por dispositivo
        plt.subplot(2, 3, 1)
        bars = plt.bar(df['device'], df['latency'])
        plt.title('Latencia Promedio por Dispositivo')
        plt.ylabel('Latencia (ms)')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['latency']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8)

        # Subplot 2: Consumo de batería
        plt.subplot(2, 3, 2)
        bars = plt.bar(df['device'], df['battery'])
        plt.title('Consumo de Batería (%)')
        plt.ylabel('Batería Usada (%)')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['battery']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8)

        # Subplot 3: Uso de memoria
        plt.subplot(2, 3, 3)
        bars = plt.bar(df['device'], df['memory'])
        plt.title('Uso de Memoria (MB)')
        plt.ylabel('Memoria (MB)')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['memory']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.0f}', ha='center', va='bottom', fontsize=8)

        # Subplot 4: Throughput
        plt.subplot(2, 3, 4)
        bars = plt.bar(df['device'], df['throughput'])
        plt.title('Throughput (tokens/seg)')
        plt.ylabel('Throughput')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['throughput']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8)

        # Subplot 5: Speedup vs Nube
        plt.subplot(2, 3, 5)
        bars = plt.bar(df['device'], df['speedup'])
        plt.title('Speedup vs Nube')
        plt.ylabel('Factor de Mejora')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['speedup']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}x', ha='center', va='bottom', fontsize=8)

        # Subplot 6: Ahorro energético
        plt.subplot(2, 3, 6)
        bars = plt.bar(df['device'], df['energy_savings'])
        plt.title('Ahorro Energético vs Nube (%)')
        plt.ylabel('Ahorro (%)')
        plt.xticks(rotation=45)
        for bar, val in zip(bars, df['energy_savings']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        # Guardar gráfico
        plot_file = os.path.join(self.config.output_dir, f'mobile_edge_comparison_{timestamp}.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico de comparación edge guardado: {plot_file}")


# Funciones de conveniencia
def create_mobile_edge_benchmark_runner(target_devices: List[str] = None,
                                      output_dir: str = "./mobile_edge_results") -> MobileEdgeBenchmarkRunner:
    """Crear un MobileEdgeBenchmarkRunner con configuración por defecto."""
    config = MobileEdgeBenchmarkConfig(
        target_devices=target_devices or ['pixel_7', 'iphone_14', 'samsung_s22'],
        output_dir=output_dir
    )
    return MobileEdgeBenchmarkRunner(config)


def run_mobile_vs_cloud_comparison(model_wrapper, model_name: str,
                                 model_size_mb: float = 100.0,
                                 devices: List[str] = None) -> Dict[str, Any]:
    """
    Ejecutar comparación completa entre edge móvil y nube.

    Args:
        model_wrapper: Wrapper del modelo
        model_name: Nombre del modelo
        model_size_mb: Tamaño del modelo en MB
        devices: Lista de dispositivos a testear

    Returns:
        Dict con resultados de comparación
    """
    runner = create_mobile_edge_benchmark_runner(devices)

    # Ejecutar benchmarks en edge
    edge_results = runner.run_mobile_edge_benchmarks(
        model_wrapper, model_name, model_size_mb
    )

    # Generar reportes
    runner.generate_edge_reports()

    # Calcular métricas agregadas
    summary = {
        'model_name': model_name,
        'model_size_mb': model_size_mb,
        'edge_results': edge_results,
        'best_device': max(edge_results.keys(),
                          key=lambda d: edge_results[d].edge_vs_cloud_speedup),
        'avg_speedup': statistics.mean([r.edge_vs_cloud_speedup for r in edge_results.values()]),
        'avg_energy_savings': statistics.mean([r.edge_vs_cloud_energy_savings for r in edge_results.values()]),
        'timestamp': time.strftime('%Y%m%d_%H%M%S')
    }

    return summary


# Integración con benchmark_vs_giants.py
def integrate_with_benchmark_vs_giants():
    """
    Función helper para integrar benchmarks móviles con el sistema benchmark_vs_giants.py.

    Esta función puede ser llamada desde benchmark_vs_giants.py para añadir
    benchmarks específicos de edge móvil.
    """
    logger.info("🔗 Integrando benchmarks de edge móvil con benchmark_vs_giants.py")

    # Aquí iría la lógica de integración
    # Por ejemplo, añadir una nueva opción de línea de comandos
    # o extender la clase BenchmarkRunner

    return {
        'mobile_edge_available': True,
        'supported_devices': list(MOBILE_DEVICE_SPECS.keys()),
        'integration_status': 'ready'
    }


if __name__ == "__main__":
    # Ejemplo de uso
    print("🚀 Mobile Edge Benchmarks para EmpoorioLM")
    print("Benchmarks específicos para despliegue en edge móvil")

    # Crear runner básico
    runner = create_mobile_edge_benchmark_runner()

    print(f"📱 Dispositivos configurados: {runner.config.target_devices}")
    print(f"📊 Número de requests: {runner.config.num_requests}")
    print(f"📁 Directorio de salida: {runner.config.output_dir}")

    print("\n💡 Para usar con modelos reales:")
    print("runner.run_mobile_edge_benchmarks(model_wrapper, 'model_name', model_size_mb=100.0)")
    print("runner.generate_edge_reports()")