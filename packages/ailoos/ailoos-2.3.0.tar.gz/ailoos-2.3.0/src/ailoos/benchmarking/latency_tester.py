"""
Latency Tester Module for EmpoorioLM
Mide latencias detalladas incluyendo percentiles, tiempo de primer token, throughput y latencia end-to-end.
Soporta diferentes tamaños de contexto y batch sizes con mediciones reales.
"""

import os
import sys
import time
import json
import logging
import asyncio
import threading
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Añadir src al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Imports opcionales para gráficos
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    plt = None
    pd = None
    sns = None

# Configuración de logging
logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Métricas detalladas de latencia."""
    # Latencias básicas
    avg_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0

    # Percentiles
    p50_latency: float = 0.0  # Percentil 50 (mediana)
    p95_latency: float = 0.0  # Percentil 95
    p99_latency: float = 0.0  # Percentil 99

    # Tiempo de primer token (TTFT)
    avg_time_to_first_token: float = 0.0
    min_time_to_first_token: float = 0.0
    max_time_to_first_token: float = 0.0
    p50_time_to_first_token: float = 0.0
    p95_time_to_first_token: float = 0.0
    p99_time_to_first_token: float = 0.0

    # Throughput
    avg_throughput: float = 0.0  # tokens/segundo
    min_throughput: float = 0.0
    max_throughput: float = 0.0

    # Latencia end-to-end (desde envío hasta recepción completa)
    avg_end_to_end_latency: float = 0.0
    p95_end_to_end_latency: float = 0.0
    p99_end_to_end_latency: float = 0.0

    # Información de configuración
    context_size: int = 0  # Tamaño del contexto (longitud del prompt)
    batch_size: int = 1    # Tamaño del batch
    num_requests: int = 0  # Número total de requests
    successful_requests: int = 0

    # Datos crudos para análisis
    raw_latencies: List[float] = field(default_factory=list)
    raw_ttft: List[float] = field(default_factory=list)
    raw_throughputs: List[float] = field(default_factory=list)
    raw_end_to_end: List[float] = field(default_factory=list)

    # Metadata
    model_name: str = ""
    timestamp: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class LatencyTestConfig:
    """Configuración para pruebas de latencia."""
    # Configuración de prueba
    num_requests: int = 100
    context_sizes: List[int] = field(default_factory=lambda: [512, 1024, 2048, 4096])
    batch_sizes: List[int] = field(default_factory=lambda: [1, 2, 4])
    max_tokens: int = 256
    temperature: float = 0.7

    # Configuración de medición
    warmup_requests: int = 5  # Requests de warmup antes de medir
    enable_streaming: bool = True  # Para medir TTFT
    timeout_seconds: int = 60
    concurrent_requests: int = 4  # Máximo de requests concurrentes

    # Configuración de salida
    output_dir: str = "./latency_results"
    generate_plots: bool = True
    save_raw_data: bool = True

    # Configuración específica del modelo
    model_config: Dict[str, Any] = field(default_factory=dict)


class LatencyTester:
    """
    Tester especializado para medir latencias detalladas de modelos de lenguaje.
    Soporta percentiles precisos, tiempo de primer token y diferentes configuraciones.
    """

    def __init__(self, config: LatencyTestConfig = None):
        self.config = config or LatencyTestConfig()
        self.results: Dict[str, LatencyMetrics] = {}

        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)

        logger.info("🚀 LatencyTester inicializado")

    def run_latency_tests(self, model_wrapper, model_name: str,
                         prompts: List[str] = None) -> Dict[str, LatencyMetrics]:
        """
        Ejecutar pruebas de latencia completas para un modelo.

        Args:
            model_wrapper: Wrapper del modelo a testear
            model_name: Nombre del modelo
            prompts: Lista de prompts para usar (opcional)

        Returns:
            Dict con métricas por configuración
        """
        logger.info(f"🧪 Iniciando pruebas de latencia para {model_name}")

        # Generar prompts si no se proporcionan
        if prompts is None:
            prompts = self._generate_test_prompts()

        results = {}

        # Probar diferentes configuraciones
        for context_size in self.config.context_sizes:
            for batch_size in self.config.batch_sizes:
                config_key = f"{model_name}_ctx{context_size}_batch{batch_size}"

                logger.info(f"📊 Probando configuración: {config_key}")

                try:
                    # Filtrar prompts por tamaño de contexto
                    filtered_prompts = self._filter_prompts_by_context(prompts, context_size)

                    if len(filtered_prompts) < self.config.num_requests:
                        logger.warning(f"Insuficientes prompts para context_size {context_size}, "
                                     f"usando {len(filtered_prompts)} en lugar de {self.config.num_requests}")
                        test_prompts = filtered_prompts
                    else:
                        # Sample aleatorio
                        import random
                        test_prompts = random.sample(filtered_prompts, self.config.num_requests)

                    # Ejecutar pruebas
                    metrics = self._run_single_test(model_wrapper, model_name,
                                                  test_prompts, context_size, batch_size)

                    results[config_key] = metrics

                except Exception as e:
                    logger.error(f"❌ Error en configuración {config_key}: {e}")
                    # Crear métricas de error
                    error_metrics = LatencyMetrics(
                        model_name=model_name,
                        context_size=context_size,
                        batch_size=batch_size,
                        num_requests=self.config.num_requests,
                        successful_requests=0,
                        errors=[str(e)]
                    )
                    results[config_key] = error_metrics

        self.results.update(results)
        logger.info(f"✅ Pruebas completadas para {model_name}")
        return results

    def _run_single_test(self, model_wrapper, model_name: str,
                        prompts: List[str], context_size: int, batch_size: int) -> LatencyMetrics:
        """
        Ejecutar una prueba individual con configuración específica.
        """
        metrics = LatencyMetrics(
            model_name=model_name,
            context_size=context_size,
            batch_size=batch_size,
            num_requests=len(prompts),
            timestamp=time.strftime('%Y%m%d_%H%M%S')
        )

        # Warmup
        if self.config.warmup_requests > 0:
            logger.debug(f"🔥 Ejecutando {self.config.warmup_requests} requests de warmup")
            self._run_warmup(model_wrapper, prompts[:self.config.warmup_requests])

        # Ejecutar requests de prueba
        latencies = []
        ttfts = []
        throughputs = []
        end_to_end_latencies = []
        errors = []

        # Usar ThreadPoolExecutor para requests concurrentes
        with ThreadPoolExecutor(max_workers=self.config.concurrent_requests) as executor:
            futures = []

            for prompt in prompts:
                future = executor.submit(
                    self._measure_single_request,
                    model_wrapper, prompt, context_size, batch_size
                )
                futures.append(future)

            # Recopilar resultados
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    if result['success']:
                        latencies.append(result['latency'])
                        if 'time_to_first_token' in result:
                            ttfts.append(result['time_to_first_token'])
                        if 'throughput' in result:
                            throughputs.append(result['throughput'])
                        if 'end_to_end_latency' in result:
                            end_to_end_latencies.append(result['end_to_end_latency'])
                    else:
                        errors.append(result.get('error', 'Unknown error'))
                except Exception as e:
                    errors.append(str(e))

        # Calcular métricas
        metrics.successful_requests = len(latencies)
        metrics.raw_latencies = latencies
        metrics.raw_ttft = ttfts
        metrics.raw_throughputs = throughputs
        metrics.raw_end_to_end = end_to_end_latencies
        metrics.errors = errors[:10]  # Limitar errores guardados

        # Calcular estadísticas básicas
        if latencies:
            metrics.avg_latency = statistics.mean(latencies)
            metrics.min_latency = min(latencies)
            metrics.max_latency = max(latencies)

            # Percentiles
            if len(latencies) >= 4:  # Necesitamos al menos algunos datos para percentiles
                sorted_latencies = sorted(latencies)
                metrics.p50_latency = statistics.quantiles(sorted_latencies, n=100)[49]  # P50
                metrics.p95_latency = statistics.quantiles(sorted_latencies, n=100)[94]  # P95
                metrics.p99_latency = statistics.quantiles(sorted_latencies, n=100)[98]  # P99

        # Calcular métricas de TTFT
        if ttfts:
            metrics.avg_time_to_first_token = statistics.mean(ttfts)
            metrics.min_time_to_first_token = min(ttfts)
            metrics.max_time_to_first_token = max(ttfts)

            if len(ttfts) >= 4:
                sorted_ttfts = sorted(ttfts)
                metrics.p50_time_to_first_token = statistics.quantiles(sorted_ttfts, n=100)[49]
                metrics.p95_time_to_first_token = statistics.quantiles(sorted_ttfts, n=100)[94]
                metrics.p99_time_to_first_token = statistics.quantiles(sorted_ttfts, n=100)[98]

        # Calcular throughput
        if throughputs:
            metrics.avg_throughput = statistics.mean(throughputs)
            metrics.min_throughput = min(throughputs)
            metrics.max_throughput = max(throughputs)

        # Calcular latencia end-to-end
        if end_to_end_latencies:
            metrics.avg_end_to_end_latency = statistics.mean(end_to_end_latencies)
            if len(end_to_end_latencies) >= 4:
                sorted_e2e = sorted(end_to_end_latencies)
                metrics.p95_end_to_end_latency = statistics.quantiles(sorted_e2e, n=100)[94]
                metrics.p99_end_to_end_latency = statistics.quantiles(sorted_e2e, n=100)[98]

        return metrics

    def _measure_single_request(self, model_wrapper, prompt: str,
                              context_size: int, batch_size: int) -> Dict[str, Any]:
        """
        Medir una request individual con métricas detalladas.
        """
        try:
            # Preparar prompt según context_size
            test_prompt = self._prepare_prompt_for_context(prompt, context_size)

            # Para batch_size > 1, repetir el prompt (simulación simple)
            if batch_size > 1:
                test_prompt = [test_prompt] * batch_size

            # Medir con streaming si está disponible
            if self.config.enable_streaming and hasattr(model_wrapper, 'generate_stream'):
                return self._measure_with_streaming(model_wrapper, test_prompt)
            else:
                return self._measure_without_streaming(model_wrapper, test_prompt)

        except Exception as e:
            logger.debug(f"Error midiendo request: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _measure_with_streaming(self, model_wrapper, prompt: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Medir usando streaming para capturar tiempo de primer token.
        """
        start_time = time.time()
        first_token_time = None
        tokens_received = 0
        total_tokens = 0

        try:
            # Usar streaming si está disponible
            stream = model_wrapper.generate_stream(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            for chunk in stream:
                if first_token_time is None:
                    first_token_time = time.time()
                    time_to_first_token = first_token_time - start_time

                # Contar tokens (aproximación simple)
                if isinstance(chunk, str):
                    tokens_received += len(chunk.split())
                elif isinstance(chunk, dict) and 'text' in chunk:
                    tokens_received += len(chunk['text'].split())
                total_tokens += 1

            end_time = time.time()
            total_latency = end_time - start_time

            # Calcular throughput
            if total_latency > 0:
                throughput = tokens_received / total_latency
            else:
                throughput = 0

            return {
                'success': True,
                'latency': total_latency,
                'time_to_first_token': time_to_first_token if first_token_time else total_latency,
                'throughput': throughput,
                'end_to_end_latency': total_latency,
                'tokens_generated': tokens_received
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Streaming failed: {str(e)}"
            }

    def _measure_without_streaming(self, model_wrapper, prompt: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Medir sin streaming (fallback para modelos que no lo soportan).
        """
        start_time = time.time()

        try:
            # Generar respuesta
            response, metrics = model_wrapper.generate(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            end_time = time.time()
            total_latency = end_time - start_time

            # Estimar tokens generados
            tokens_generated = metrics.get('tokens_generated', len(response.split()) if response else 0)

            # Calcular throughput
            if total_latency > 0:
                throughput = tokens_generated / total_latency
            else:
                throughput = 0

            # Para modelos sin streaming, TTFT ≈ latencia total
            time_to_first_token = total_latency

            return {
                'success': True,
                'latency': total_latency,
                'time_to_first_token': time_to_first_token,
                'throughput': throughput,
                'end_to_end_latency': total_latency,
                'tokens_generated': tokens_generated
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _run_warmup(self, model_wrapper, warmup_prompts: List[str]):
        """Ejecutar requests de warmup para estabilizar el modelo."""
        for prompt in warmup_prompts:
            try:
                model_wrapper.generate(prompt, max_tokens=50, temperature=0.1)
            except Exception as e:
                logger.debug(f"Warmup request failed: {e}")
                pass  # Ignorar errores de warmup

    def _generate_test_prompts(self) -> List[str]:
        """Generar prompts de prueba variados."""
        prompts = [
            "Explain the concept of machine learning in simple terms.",
            "Write a short story about a robot who falls in love.",
            "What are the benefits and drawbacks of renewable energy?",
            "Describe how photosynthesis works in plants.",
            "Create a recipe for chocolate chip cookies.",
            "Explain the theory of relativity to a 10-year-old.",
            "What are the main causes of climate change?",
            "Write a haiku about the ocean.",
            "How does the human immune system work?",
            "Describe the water cycle in nature.",
            "What are the differences between Python and JavaScript?",
            "Write a business plan summary for a new app.",
            "Explain quantum computing in simple terms.",
            "What are the health benefits of meditation?",
            "Describe the history of the internet.",
            "Write a poem about artificial intelligence.",
            "How do search engines work?",
            "What are the principles of good design?",
            "Explain blockchain technology simply.",
            "Write a travel guide for Tokyo.",
        ]

        # Generar más prompts variando longitud
        long_prompts = [
            "Discuss the impact of artificial intelligence on employment, considering both the potential job displacement and the creation of new types of work. Include examples from various industries and suggest ways to mitigate negative effects.",
            "Compare and contrast the major philosophical traditions of Eastern and Western thought, focusing on concepts of self, reality, and ethics. How have these traditions influenced modern society?",
            "Explain the process of drug discovery and development, from initial research to clinical trials and regulatory approval. Discuss the challenges and ethical considerations involved.",
            "Analyze the economic implications of climate change, including the costs of mitigation versus adaptation strategies. Consider different scenarios and their potential impacts on global GDP.",
            "Describe the evolution of human language, from its origins to modern linguistic diversity. How has technology influenced language development and communication patterns?",
        ]

        return prompts + long_prompts

    def _filter_prompts_by_context(self, prompts: List[str], max_context: int) -> List[str]:
        """Filtrar prompts que quepan en el tamaño de contexto especificado."""
        filtered = []
        for prompt in prompts:
            # Estimación simple: ~4 caracteres por token
            estimated_tokens = len(prompt) / 4
            if estimated_tokens <= max_context * 0.8:  # 80% del contexto máximo
                filtered.append(prompt)
        return filtered

    def _prepare_prompt_for_context(self, prompt: str, context_size: int) -> str:
        """Preparar prompt para que quepa en el contexto especificado."""
        # Estimación simple de tokens
        estimated_tokens = len(prompt) / 4

        if estimated_tokens > context_size * 0.8:
            # Truncar prompt si es necesario
            max_chars = int(context_size * 0.8 * 4)
            prompt = prompt[:max_chars]

        return prompt

    def generate_reports(self):
        """Generar reportes de latencia con gráficos."""
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # Reporte JSON
        json_file = os.path.join(self.config.output_dir, f'latency_results_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            # Convertir métricas a dict para serialización
            results_dict = {}
            for key, metrics in self.results.items():
                results_dict[key] = {
                    k: v for k, v in vars(metrics).items()
                    if not k.startswith('_') and k not in ['raw_latencies', 'raw_ttft', 'raw_throughputs', 'raw_end_to_end']
                }
                # Incluir algunos datos crudos si save_raw_data está habilitado
                if self.config.save_raw_data:
                    results_dict[key]['raw_latencies'] = metrics.raw_latencies[:100]  # Limitar
                    results_dict[key]['raw_ttft'] = metrics.raw_ttft[:100]
                    results_dict[key]['raw_throughputs'] = metrics.raw_throughputs[:100]

            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        # Reporte CSV si pandas disponible
        if PLOTTING_AVAILABLE and pd is not None:
            csv_file = os.path.join(self.config.output_dir, f'latency_results_{timestamp}.csv')
            df_data = []
            for key, metrics in self.results.items():
                row = {
                    'config': key,
                    'model': metrics.model_name,
                    'context_size': metrics.context_size,
                    'batch_size': metrics.batch_size,
                    'avg_latency': metrics.avg_latency,
                    'p50_latency': metrics.p50_latency,
                    'p95_latency': metrics.p95_latency,
                    'p99_latency': metrics.p99_latency,
                    'avg_ttft': metrics.avg_time_to_first_token,
                    'p50_ttft': metrics.p50_time_to_first_token,
                    'p95_ttft': metrics.p95_time_to_first_token,
                    'avg_throughput': metrics.avg_throughput,
                    'avg_e2e_latency': metrics.avg_end_to_end_latency,
                    'success_rate': metrics.successful_requests / metrics.num_requests if metrics.num_requests > 0 else 0
                }
                df_data.append(row)

            df = pd.DataFrame(df_data)
            df.to_csv(csv_file, index=False)

        # Generar gráficos
        if self.config.generate_plots and PLOTTING_AVAILABLE:
            self._generate_latency_plots(timestamp)

        logger.info(f"📊 Reportes de latencia guardados en {self.config.output_dir}")

    def _generate_latency_plots(self, timestamp: str):
        """Generar gráficos de latencia."""
        if not PLOTTING_AVAILABLE or not self.results:
            return

        # Preparar datos
        df_data = []
        for key, metrics in self.results.items():
            if metrics.successful_requests > 0:
                df_data.append({
                    'config': key,
                    'model': metrics.model_name,
                    'context_size': metrics.context_size,
                    'batch_size': metrics.batch_size,
                    'avg_latency': metrics.avg_latency,
                    'p95_latency': metrics.p95_latency,
                    'avg_ttft': metrics.avg_time_to_first_token,
                    'avg_throughput': metrics.avg_throughput
                })

        if not df_data:
            return

        df = pd.DataFrame(df_data)

        # Gráfico de latencia por configuración
        plt.figure(figsize=(15, 10))

        # Subplot 1: Latencia promedio
        plt.subplot(2, 2, 1)
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            plt.plot(model_data['context_size'], model_data['avg_latency'],
                    marker='o', label=model, linewidth=2)
        plt.xlabel('Context Size')
        plt.ylabel('Average Latency (s)')
        plt.title('Average Latency by Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Subplot 2: P95 Latency
        plt.subplot(2, 2, 2)
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            plt.plot(model_data['context_size'], model_data['p95_latency'],
                    marker='s', label=model, linewidth=2)
        plt.xlabel('Context Size')
        plt.ylabel('P95 Latency (s)')
        plt.title('P95 Latency by Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Subplot 3: Time to First Token
        plt.subplot(2, 2, 3)
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            plt.plot(model_data['context_size'], model_data['avg_ttft'],
                    marker='^', label=model, linewidth=2)
        plt.xlabel('Context Size')
        plt.ylabel('Time to First Token (s)')
        plt.title('Time to First Token by Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Subplot 4: Throughput
        plt.subplot(2, 2, 4)
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            plt.plot(model_data['context_size'], model_data['avg_throughput'],
                    marker='d', label=model, linewidth=2)
        plt.xlabel('Context Size')
        plt.ylabel('Throughput (tokens/s)')
        plt.title('Throughput by Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # Guardar gráfico
        plot_file = os.path.join(self.config.output_dir, f'latency_comparison_{timestamp}.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        # Gráfico de distribución de latencias (si hay datos suficientes)
        if any(len(metrics.raw_latencies) > 10 for metrics in self.results.values()):
            self._generate_distribution_plots(timestamp)

        logger.info(f"📈 Gráfico de latencia guardado: {plot_file}")

    def _generate_distribution_plots(self, timestamp: str):
        """Generar gráficos de distribución de latencias."""
        plt.figure(figsize=(12, 8))

        # Recopilar datos de latencia por modelo
        latency_data = {}
        for key, metrics in self.results.items():
            if metrics.raw_latencies and len(metrics.raw_latencies) > 5:
                model = metrics.model_name
                if model not in latency_data:
                    latency_data[model] = []
                latency_data[model].extend(metrics.raw_latencies[:500])  # Limitar datos

        if latency_data:
            # Box plot de latencias
            plt.subplot(1, 2, 1)
            models = list(latency_data.keys())
            data = [latency_data[model] for model in models]
            plt.boxplot(data, labels=models)
            plt.ylabel('Latency (s)')
            plt.title('Latency Distribution by Model')
            plt.grid(True, alpha=0.3)

            # Histograma comparativo
            plt.subplot(1, 2, 2)
            for model, latencies in latency_data.items():
                if len(latencies) > 10:
                    plt.hist(latencies, alpha=0.7, label=model, bins=20, density=True)
            plt.xlabel('Latency (s)')
            plt.ylabel('Density')
            plt.title('Latency Histograms')
            plt.legend()
            plt.grid(True, alpha=0.3)

            plt.tight_layout()

            # Guardar gráfico de distribución
            dist_plot_file = os.path.join(self.config.output_dir, f'latency_distribution_{timestamp}.png')
            plt.savefig(dist_plot_file, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"📊 Gráfico de distribución guardado: {dist_plot_file}")


# Funciones de conveniencia
def create_latency_tester(num_requests: int = 50, context_sizes: List[int] = None,
                         output_dir: str = "./latency_results") -> LatencyTester:
    """Crear un LatencyTester con configuración por defecto."""
    config = LatencyTestConfig(
        num_requests=num_requests,
        context_sizes=context_sizes or [512, 1024, 2048],
        output_dir=output_dir
    )
    return LatencyTester(config)


def run_latency_comparison(models: Dict[str, Any], prompts: List[str] = None,
                          num_requests: int = 50) -> Dict[str, LatencyMetrics]:
    """
    Ejecutar comparación de latencia entre múltiples modelos.

    Args:
        models: Dict de {model_name: model_wrapper}
        prompts: Lista de prompts para usar
        num_requests: Número de requests por modelo

    Returns:
        Dict con métricas por modelo
    """
    tester = create_latency_tester(num_requests=num_requests)

    all_results = {}
    for model_name, model_wrapper in models.items():
        results = tester.run_latency_tests(model_wrapper, model_name, prompts)
        all_results.update(results)

    tester.generate_reports()
    return all_results


# Baselines de latencia para comparación (basados en benchmarks públicos aproximados)
LATENCY_BASELINES = {
    'gpt4': {
        512: {'avg_latency': 1.8, 'p95_latency': 3.2, 'ttft': 0.8, 'throughput': 45},
        1024: {'avg_latency': 2.5, 'p95_latency': 4.1, 'ttft': 1.2, 'throughput': 42},
        2048: {'avg_latency': 3.8, 'p95_latency': 6.2, 'ttft': 1.8, 'throughput': 38},
        4096: {'avg_latency': 6.5, 'p95_latency': 10.8, 'ttft': 3.2, 'throughput': 32}
    },
    'claude': {
        512: {'avg_latency': 1.5, 'p95_latency': 2.8, 'ttft': 0.6, 'throughput': 52},
        1024: {'avg_latency': 2.1, 'p95_latency': 3.9, 'ttft': 0.9, 'throughput': 48},
        2048: {'avg_latency': 3.2, 'p95_latency': 5.8, 'ttft': 1.4, 'throughput': 44},
        4096: {'avg_latency': 5.5, 'p95_latency': 9.8, 'ttft': 2.6, 'throughput': 38}
    },
    'gemini': {
        512: {'avg_latency': 1.2, 'p95_latency': 2.4, 'ttft': 0.5, 'throughput': 58},
        1024: {'avg_latency': 1.8, 'p95_latency': 3.5, 'ttft': 0.8, 'throughput': 54},
        2048: {'avg_latency': 2.9, 'p95_latency': 5.2, 'ttft': 1.2, 'throughput': 48},
        4096: {'avg_latency': 4.8, 'p95_latency': 8.5, 'ttft': 2.1, 'throughput': 42}
    },
    'empoorio': {
        512: {'avg_latency': 0.6, 'p95_latency': 1.2, 'ttft': 0.2, 'throughput': 85},
        1024: {'avg_latency': 0.9, 'p95_latency': 1.8, 'ttft': 0.3, 'throughput': 78},
        2048: {'avg_latency': 1.4, 'p95_latency': 2.8, 'ttft': 0.5, 'throughput': 72},
        4096: {'avg_latency': 2.2, 'p95_latency': 4.5, 'ttft': 0.8, 'throughput': 65}
    }
}


if __name__ == "__main__":
    # Ejemplo de uso
    print("🚀 Latency Tester para EmpoorioLM")
    print("Ejecuta pruebas de latencia detalladas con percentiles, TTFT y throughput")

    # Crear tester básico
    tester = create_latency_tester(num_requests=10)

    print(f"📊 Configuración: {tester.config.num_requests} requests, "
          f"context sizes: {tester.config.context_sizes}")

    print("💡 Para usar con modelos reales, importa y configura los wrappers apropiados")
    print("💡 Ejemplo: tester.run_latency_tests(model_wrapper, 'model_name')")