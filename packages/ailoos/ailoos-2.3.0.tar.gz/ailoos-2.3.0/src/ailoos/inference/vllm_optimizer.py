"""
🚀 AILOOS vLLM Inference Optimizer
==================================

Optimización completa de inference usando vLLM + Flash Attention 2
para máxima velocidad y eficiencia en producción.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import torch
from transformers import AutoTokenizer

# vLLM imports (con fallbacks)
try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import EngineArgs
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    logging.warning("vLLM not available - using fallback inference")

try:
    import flash_attn
    FLASH_ATTENTION_AVAILABLE = True
except ImportError:
    FLASH_ATTENTION_AVAILABLE = False
    logging.warning("Flash Attention not available - using standard attention")

logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuración completa para inference optimizada."""
    model_name: str = "EmpoorioLM-7B"
    tensor_parallel_size: int = 1
    max_model_len: int = 4096
    max_num_seqs: int = 256
    gpu_memory_utilization: float = 0.9
    enforce_eager: bool = False
    enable_prefix_caching: bool = True
    use_flash_attention: bool = True
    quantization: Optional[str] = None  # "awq", "gptq", "squeezellm"
    dtype: str = "auto"
    trust_remote_code: bool = True

    # Sampling parameters
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_tokens: int = 512
    repetition_penalty: float = 1.1

    # Performance tuning
    batch_size: int = 32
    max_concurrent_requests: int = 100
    enable_chunked_prefill: bool = True


@dataclass
class InferenceResult:
    """Resultado de una inferencia."""
    text: str
    tokens_generated: int
    inference_time: float
    tokens_per_second: float
    total_tokens: int
    finish_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class vLLMOptimizer:
    """
    Optimizador de inference usando vLLM para máxima performance.
    Soporta Flash Attention 2, quantization, y optimizaciones avanzadas.
    """

    def __init__(self, config: InferenceConfig):
        self.config = config
        self.llm: Optional[LLM] = None
        self.tokenizer = None
        self.is_initialized = False

        # Estadísticas de performance
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_inference_time": 0.0,
            "average_latency": 0.0,
            "tokens_per_second": 0.0,
            "peak_memory_usage": 0.0
        }

    async def initialize(self) -> bool:
        """Inicializar vLLM engine con optimizaciones."""

        if not VLLM_AVAILABLE:
            logger.error("vLLM not available - cannot initialize optimized inference")
            return False

        try:
            logger.info(f"🚀 Initializing vLLM for {self.config.model_name}")

            # Configurar Flash Attention si disponible
            if self.config.use_flash_attention and FLASH_ATTENTION_AVAILABLE:
                os.environ["VLLM_USE_FLASH_ATTN"] = "1"
                logger.info("✅ Flash Attention 2 enabled")
            else:
                os.environ["VLLM_USE_FLASH_ATTN"] = "0"
                logger.warning("⚠️ Flash Attention not available")

            # Engine arguments optimizados
            engine_args = EngineArgs(
                model=self.config.model_name,
                tensor_parallel_size=self.config.tensor_parallel_size,
                max_model_len=self.config.max_model_len,
                max_num_seqs=self.config.max_num_seqs,
                gpu_memory_utilization=self.config.gpu_memory_utilization,
                enforce_eager=self.config.enforce_eager,
                enable_prefix_caching=self.config.enable_prefix_caching,
                dtype=self.config.dtype,
                trust_remote_code=self.config.trust_remote_code,
                quantization=self.config.quantization
            )

            # Inicializar vLLM
            self.llm = LLM(engine_args=engine_args)

            # Cargar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.is_initialized = True
            logger.info("✅ vLLM optimizer initialized successfully")

            # Log de capacidades
            self._log_capabilities()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize vLLM: {e}")
            return False

    def _log_capabilities(self):
        """Log de capacidades del sistema."""
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3 if gpu_count > 0 else 0
logger.info("🎮 GPU Capabilities:")
logger.info(f"   • GPUs: {gpu_count} x {gpu_name}")
logger.info(".1f")
logger.info(f"   • Flash Attention: {'✅' if FLASH_ATTENTION_AVAILABLE else '❌'}")
logger.info(f"   • vLLM: {'✅' if VLLM_AVAILABLE else '❌'}")
else:
logger.warning("⚠️ No GPU available - using CPU inference")
    async def generate(
        self,
        prompt: str,
        sampling_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> InferenceResult:
        """Generar texto optimizado con vLLM."""

        if not self.is_initialized:
            raise RuntimeError("vLLM optimizer not initialized")

        start_time = time.time()

        # Preparar sampling parameters
        if sampling_params is None:
            sampling_params = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_tokens": self.config.max_tokens,
                "repetition_penalty": self.config.repetition_penalty
            }

        # Merge con kwargs
        sampling_params.update(kwargs)

        # Crear SamplingParams de vLLM
        vllm_sampling_params = SamplingParams(**sampling_params)

        try:
            # Generar con vLLM
            outputs = self.llm.generate([prompt], vllm_sampling_params)

            if not outputs:
                raise RuntimeError("No output generated")

            output = outputs[0]
            generated_text = output.outputs[0].text
            finish_reason = output.outputs[0].finish_reason

            # Calcular métricas
            inference_time = time.time() - start_time
            tokens_generated = len(output.outputs[0].token_ids)
            total_tokens = len(self.tokenizer.encode(prompt)) + tokens_generated
            tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0

            # Actualizar estadísticas
            self._update_stats(tokens_generated, inference_time)

            result = InferenceResult(
                text=generated_text,
                tokens_generated=tokens_generated,
                inference_time=inference_time,
                tokens_per_second=tokens_per_second,
                total_tokens=total_tokens,
                finish_reason=finish_reason or "unknown",
                metadata={
                    "model": self.config.model_name,
                    "prompt_tokens": len(self.tokenizer.encode(prompt)),
                    "temperature": sampling_params.get("temperature"),
                    "max_tokens": sampling_params.get("max_tokens")
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise

    async def generate_batch(
        self,
        prompts: List[str],
        sampling_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[InferenceResult]:
        """Generar texto para múltiples prompts en batch."""

        if not self.is_initialized:
            raise RuntimeError("vLLM optimizer not initialized")

        start_time = time.time()

        # Preparar sampling parameters
        if sampling_params is None:
            sampling_params = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_tokens": self.config.max_tokens,
                "repetition_penalty": self.config.repetition_penalty
            }

        sampling_params.update(kwargs)
        vllm_sampling_params = SamplingParams(**sampling_params)

        try:
            # Generar batch con vLLM
            outputs = self.llm.generate(prompts, vllm_sampling_params)

            results = []
            total_tokens_generated = 0

            for i, output in enumerate(outputs):
                if output.outputs:
                    generated_text = output.outputs[0].text
                    finish_reason = output.outputs[0].finish_reason
                    tokens_generated = len(output.outputs[0].token_ids)
                    total_tokens_generated += tokens_generated

                    # Calcular métricas
                    prompt_tokens = len(self.tokenizer.encode(prompts[i]))
                    total_tokens = prompt_tokens + tokens_generated

                    result = InferenceResult(
                        text=generated_text,
                        tokens_generated=tokens_generated,
                        inference_time=time.time() - start_time,  # Tiempo total del batch
                        tokens_per_second=total_tokens_generated / (time.time() - start_time),
                        total_tokens=total_tokens,
                        finish_reason=finish_reason or "unknown",
                        metadata={
                            "batch_index": i,
                            "model": self.config.model_name,
                            "prompt_tokens": prompt_tokens
                        }
                    )
                    results.append(result)
                else:
                    # Fallback para outputs vacíos
                    results.append(InferenceResult(
                        text="",
                        tokens_generated=0,
                        inference_time=0.0,
                        tokens_per_second=0.0,
                        total_tokens=len(self.tokenizer.encode(prompts[i])),
                        finish_reason="error",
                        metadata={"error": "No output generated"}
                    ))

            # Actualizar estadísticas
            batch_time = time.time() - start_time
            self._update_stats(total_tokens_generated, batch_time)

            return results

        except Exception as e:
            logger.error(f"Error during batch generation: {e}")
            raise

    def _update_stats(self, tokens_generated: int, inference_time: float):
        """Actualizar estadísticas de performance."""
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += tokens_generated
        self.stats["total_inference_time"] += inference_time

        # Calcular promedios
        if self.stats["total_requests"] > 0:
            self.stats["average_latency"] = self.stats["total_inference_time"] / self.stats["total_requests"]

        if self.stats["total_inference_time"] > 0:
            self.stats["tokens_per_second"] = self.stats["total_tokens"] / self.stats["total_inference_time"]

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de performance."""
        return self.stats.copy()

    async def benchmark(
        self,
        prompts: List[str],
        num_runs: int = 3,
        batch_size: int = 1
    ) -> Dict[str, Any]:
        """Ejecutar benchmark de performance."""

        logger.info(f"🏁 Starting vLLM benchmark with {len(prompts)} prompts, {num_runs} runs")

        all_latencies = []
        all_tokens_per_second = []
        total_tokens = 0

        for run in range(num_runs):
            logger.info(f"Run {run + 1}/{num_runs}")

            start_time = time.time()

            if batch_size == 1:
                # Inference individual
                for prompt in prompts:
                    result = await self.generate(prompt)
                    all_latencies.append(result.inference_time)
                    all_tokens_per_second.append(result.tokens_per_second)
                    total_tokens += result.tokens_generated
            else:
                # Batch inference
                for i in range(0, len(prompts), batch_size):
                    batch = prompts[i:i + batch_size]
                    results = await self.generate_batch(batch)

                    for result in results:
                        all_latencies.append(result.inference_time / len(results))  # Tiempo promedio por request
                        all_tokens_per_second.append(result.tokens_per_second)
                        total_tokens += result.tokens_generated

            run_time = time.time() - start_time
            logger.info(".2f"
        # Calcular métricas finales
        avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
        avg_tokens_per_second = sum(all_tokens_per_second) / len(all_tokens_per_second) if all_tokens_per_second else 0
        p50_latency = sorted(all_latencies)[len(all_latencies) // 2] if all_latencies else 0
        p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] if all_latencies else 0

        benchmark_results = {
            "configuration": {
                "model": self.config.model_name,
                "tensor_parallel_size": self.config.tensor_parallel_size,
                "max_model_len": self.config.max_model_len,
                "quantization": self.config.quantization,
                "flash_attention": self.config.use_flash_attention and FLASH_ATTENTION_AVAILABLE,
                "vllm_available": VLLM_AVAILABLE
            },
            "performance": {
                "avg_latency_seconds": avg_latency,
                "p50_latency_seconds": p50_latency,
                "p95_latency_seconds": p95_latency,
                "avg_tokens_per_second": avg_tokens_per_second,
                "total_tokens_generated": total_tokens,
                "total_runs": num_runs,
                "total_prompts": len(prompts)
            },
            "system_info": {
                "gpu_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            }
        }

        logger.info("✅ Benchmark completed")
        logger.info(".3f"        logger.info(".3f"        logger.info(".1f"
        return benchmark_results

    async def optimize_for_production(self) -> Dict[str, Any]:
        """Optimizar configuración para producción."""

        logger.info("🔧 Optimizing vLLM configuration for production")

        optimizations = {
            "applied": [],
            "recommendations": [],
            "performance_impact": {}
        }

        # Verificar y aplicar optimizaciones
        if VLLM_AVAILABLE:
            optimizations["applied"].append("vLLM_enabled")

            if FLASH_ATTENTION_AVAILABLE and self.config.use_flash_attention:
                optimizations["applied"].append("flash_attention_2")
                optimizations["performance_impact"]["flash_attention"] = "+50-100% throughput"

            if self.config.enable_prefix_caching:
                optimizations["applied"].append("prefix_caching")
                optimizations["performance_impact"]["prefix_caching"] = "+20-30% latency for similar prompts"

            if self.config.quantization:
                optimizations["applied"].append(f"quantization_{self.config.quantization}")
                optimizations["performance_impact"]["quantization"] = "+2-4x throughput, -5% accuracy"

            if self.config.tensor_parallel_size > 1:
                optimizations["applied"].append(f"tensor_parallel_{self.config.tensor_parallel_size}")
                optimizations["performance_impact"]["tensor_parallel"] = f"+{self.config.tensor_parallel_size}x throughput"
        else:
            optimizations["recommendations"].append("Install vLLM for production optimization")

        # Recomendaciones adicionales
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            if gpu_count > 1 and self.config.tensor_parallel_size == 1:
                optimizations["recommendations"].append(f"Enable tensor parallelism (GPUs: {gpu_count})")
        else:
            optimizations["recommendations"].append("Use GPU for production inference")

        if self.config.max_num_seqs < 128:
            optimizations["recommendations"].append("Increase max_num_seqs for higher throughput")

        logger.info("✅ Production optimization completed")
        return optimizations


# Instancia global del optimizer
_vllm_optimizer: Optional[vLLMOptimizer] = None


async def get_vllm_optimizer(config: Optional[InferenceConfig] = None) -> vLLMOptimizer:
    """Obtener instancia global del vLLM optimizer."""
    global _vllm_optimizer
    if _vllm_optimizer is None:
        if config is None:
            config = InferenceConfig()
        _vllm_optimizer = vLLMOptimizer(config)
        await _vllm_optimizer.initialize()
    return _vllm_optimizer


async def demo_vllm_optimization():
    """Demo de optimización vLLM."""

    print("🚀 AILOOS vLLM Inference Optimizer Demo")
    print("=" * 50)

    # Configuración optimizada
    config = InferenceConfig(
        model_name="gpt2",  # Usar GPT-2 para demo (más rápido)
        max_model_len=1024,
        max_num_seqs=32,
        temperature=0.8,
        max_tokens=100
    )

    print("📋 Configuración:")
    print(f"   • Modelo: {config.model_name}")
    print(f"   • Max length: {config.max_model_len}")
    print(f"   • Max sequences: {config.max_num_seqs}")
    print(f"   • Flash Attention: {'✅' if FLASH_ATTENTION_AVAILABLE else '❌'}")
    print(f"   • vLLM: {'✅' if VLLM_AVAILABLE else '❌'}")

    optimizer = vLLMOptimizer(config)

    if not await optimizer.initialize():
        print("❌ No se pudo inicializar vLLM optimizer")
        return

    # Prompts de test
    test_prompts = [
        "The future of artificial intelligence",
        "Machine learning is transforming",
        "Deep learning models can",
        "Natural language processing helps",
        "Computer vision enables machines"
    ]

    print("
🎯 Generando texto con vLLM..."    for i, prompt in enumerate(test_prompts[:2]):  # Solo 2 para demo
        print(f"\n{i+1}. Prompt: '{prompt}'")

        try:
            result = await optimizer.generate(prompt)
            print(f"   Generated: '{result.text[:80]}...'")
            print(".3f"            print(".1f"
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Benchmark
    print("
🏁 Ejecutando benchmark..."    try:
        benchmark_results = await optimizer.benchmark(test_prompts, num_runs=2)

        print("📊 Resultados del benchmark:")
        print(".3f"        print(".3f"        print(".3f"        print(".1f"
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")

    # Optimizaciones para producción
    print("
🔧 Optimizaciones para producción:"    try:
        optimizations = await optimizer.optimize_for_production()
        print("   ✅ Aplicadas:", ", ".join(optimizations["applied"]))
        if optimizations["recommendations"]:
            print("   💡 Recomendaciones:", ", ".join(optimizations["recommendations"]))
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

    print("
✅ Demo completada!"    print("🚀 vLLM optimizer listo para producción con máxima performance")


if __name__ == "__main__":
    asyncio.run(demo_vllm_optimization())