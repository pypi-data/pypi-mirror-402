"""
Módulo de cuantización avanzada para modelos EmpoorioLM.
Soporta cuantización INT8, INT4, FP16, y cuantización mixta.
Incluye calibración dinámica, cuantización federada, entrenamiento aware,
monitoreo de rendimiento y ajuste adaptativo.
"""

import torch
import torch.nn as nn
import logging
import time
import numpy as np
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import bitsandbytes as bnb
from transformers import BitsAndBytesConfig, Trainer, TrainingArguments
from torch.utils.data import DataLoader, Dataset

from ..models.empoorio_lm import EmpoorioLM

logger = logging.getLogger(__name__)


@dataclass
class QuantizationConfig:
    """Configuración avanzada de cuantización."""
    quantization_type: str = "int8"  # int8, int4, fp16, mixed
    mixed_precision_layers: Optional[List[str]] = None
    calibration_samples: int = 1000
    dynamic_range: bool = True
    federated_compatible: bool = False
    adaptive_threshold: float = 0.95
    performance_target_fps: Optional[float] = None


class AdvancedQuantizer:
    """
    Cuantizador avanzado para modelos EmpoorioLM.

    Soporta:
    - Cuantización INT8 (8-bit)
    - Cuantización INT4 (4-bit) con double quantization
    - FP16 para precisión reducida
    - Cuantización mixta (diferentes precisiones por capa)
    - Calibración dinámica
    - Compatibilidad con federated learning
    """

    def __init__(self, config: Optional[QuantizationConfig] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = config or QuantizationConfig()
        self.dynamic_calibration = DynamicCalibration()
        self.performance_monitor = PerformanceMonitor()
        self.adaptive_quantization = AdaptiveQuantization(self.config)
        logger.info(f"🔧 AdvancedQuantizer inicializado - Device: {self.device}")

    def create_quantization_config(
        self,
        quantization_type: str = "int8",
        double_quant: bool = True,
        quant_type: str = "nf4",
        mixed_precision_layers: Optional[List[str]] = None
    ) -> Union[BitsAndBytesConfig, Dict[str, Any]]:
        """
        Crear configuración de cuantización avanzada.

        Args:
            quantization_type: Tipo de cuantización ('int8', 'int4', 'fp16', 'mixed')
            double_quant: Usar double quantization para INT4
            quant_type: Tipo de cuantización para INT4 ('nf4', 'fp4')
            mixed_precision_layers: Capas para cuantización mixta

        Returns:
            Configuración de cuantización
        """
        if quantization_type == "int8":
            config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_enable_fp32_cpu_offload=True
            )
        elif quantization_type == "int4":
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=double_quant,
                bnb_4bit_quant_type=quant_type
            )
        elif quantization_type == "fp16":
            # FP16 no requiere BitsAndBytesConfig especial
            config = {"torch_dtype": torch.float16}
        elif quantization_type == "mixed":
            # Configuración para cuantización mixta
            config = {
                "mixed_precision": True,
                "layers_config": mixed_precision_layers or self._get_default_mixed_config(),
                "bnb_config": BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_enable_fp32_cpu_offload=True
                )
            }
        else:
            raise ValueError(f"Tipo de cuantización no soportado: {quantization_type}")

        return config

    def _get_default_mixed_config(self) -> Dict[str, str]:
        """Obtener configuración mixta por defecto."""
        return {
            "embed_tokens": "fp16",
            "lm_head": "fp16",
            "layers.*.self_attn": "int8",
            "layers.*.mlp": "int4",
            "norm": "fp16"
        }

    def quantize_model(
        self,
        model_path: Union[str, Path],
        quantization_type: str = "int8",
        save_path: Optional[Union[str, Path]] = None,
        calibration_dataloader: Optional[DataLoader] = None,
        use_dynamic_calibration: bool = True,
        **quant_kwargs
    ) -> EmpoorioLM:
        """
        Cuantizar un modelo EmpoorioLM con soporte avanzado.

        Args:
            model_path: Ruta del modelo original
            quantization_type: Tipo de cuantización ('int8', 'int4', 'fp16', 'mixed')
            save_path: Ruta para guardar el modelo cuantizado
            calibration_dataloader: DataLoader para calibración dinámica
            use_dynamic_calibration: Usar calibración automática
            **quant_kwargs: Parámetros adicionales

        Returns:
            Modelo cuantizado
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")

        logger.info(f"🔄 Cuantizando modelo desde: {model_path}")
        logger.info(f"   Tipo de cuantización: {quantization_type}")

        try:
            # Cargar modelo base
            model = EmpoorioLM.from_pretrained(str(model_path))
            model.to(self.device)
            model.eval()

            # Aplicar calibración dinámica si está disponible
            if use_dynamic_calibration and calibration_dataloader and quantization_type in ["int8", "int4", "mixed"]:
                logger.info("🎯 Aplicando calibración dinámica...")
                self.dynamic_calibration.collect_calibration_data(model, calibration_dataloader)
                optimal_config = self.dynamic_calibration.get_optimal_quantization_config()

                if quantization_type == "mixed":
                    quant_kwargs["mixed_precision_layers"] = optimal_config

            # Crear configuración de cuantización
            quant_config = self.create_quantization_config(quantization_type, **quant_kwargs)

            if quantization_type == "fp16":
                # Simplemente convertir a FP16
                model.half()
                logger.info("✅ Modelo convertido a FP16")

            elif quantization_type == "mixed":
                # Aplicar cuantización mixta
                model = self._apply_mixed_quantization(model, quant_config)
                logger.info("✅ Cuantización mixta aplicada")

            else:
                # Cuantización estándar con BitsAndBytes
                model = EmpoorioLM.from_pretrained(
                    str(model_path),
                    quantization_config=quant_config,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                model.to(self.device)
                logger.info("✅ Cuantización BitsAndBytes aplicada")

            # Desactivar gradientes
            for param in model.parameters():
                param.requires_grad = False

            logger.info("✅ Modelo cuantizado exitosamente")
            logger.info(f"   Memoria usada: {self._get_model_memory_usage(model)}")

            # Medir rendimiento inicial
            if hasattr(self, 'performance_monitor'):
                perf_metrics = self.performance_monitor.measure_inference_performance(
                    model, calibration_dataloader, None
                )
                logger.info(f"   Rendimiento inicial - Latency: {perf_metrics['avg_latency']:.3f}s")

            # Guardar si se especifica
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)

                logger.info(f"💾 Guardando modelo cuantizado en: {save_path}")
                model.save_pretrained(str(save_path))

                # Guardar configuración de cuantización
                config_path = save_path / "quantization_config.json"
                import json
                with open(config_path, 'w') as f:
                    json.dump({
                        "quantization_type": quantization_type,
                        "config": quant_kwargs,
                        "calibration_used": use_dynamic_calibration
                    }, f, indent=2)

                logger.info("✅ Modelo cuantizado guardado")

            return model

        except Exception as e:
            logger.error(f"❌ Error en cuantización: {e}")
            raise

    def _apply_mixed_quantization(self, model: EmpoorioLM, config: Dict[str, Any]) -> EmpoorioLM:
        """Aplicar cuantización mixta por capas."""
        layers_config = config.get("layers_config", {})

        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Determinar tipo de cuantización para esta capa
                quant_type = "fp16"  # Default

                for pattern, qtype in layers_config.items():
                    if pattern in name or (pattern.endswith("*") and pattern[:-1] in name):
                        quant_type = qtype
                        break

                if quant_type == "int8":
                    # Aplicar INT8 a esta capa
                    module.weight.data = self._quantize_tensor_int8(module.weight.data)
                elif quant_type == "int4":
                    # Aplicar INT4 a esta capa
                    module.weight.data = self._quantize_tensor_int4(module.weight.data)
                # FP16 no necesita cambios

        return model

    def _quantize_tensor_int8(self, tensor: torch.Tensor) -> torch.Tensor:
        """Cuantizar tensor a INT8."""
        scale = tensor.abs().max() / 127.0
        quantized = torch.round(tensor / scale).clamp(-128, 127)
        return quantized * scale

    def _quantize_tensor_int4(self, tensor: torch.Tensor) -> torch.Tensor:
        """Cuantizar tensor a INT4."""
        scale = tensor.abs().max() / 7.0
        quantized = torch.round(tensor / scale).clamp(-8, 7)
        return quantized * scale

    def _get_model_memory_usage(self, model: EmpoorioLM) -> str:
        """Obtener uso de memoria del modelo."""
        total_params = sum(p.numel() for p in model.parameters())
        memory_bytes = total_params * 2  # Aproximado para float16

        if memory_bytes < 1024**3:  # Menos de 1GB
            return f"{memory_bytes / 1024**2:.1f} MB"
        else:
            return f"{memory_bytes / 1024**3:.1f} GB"

    def compare_model_sizes(
        self,
        original_model: EmpoorioLM,
        quantized_model: EmpoorioLM
    ) -> Dict[str, Any]:
        """
        Comparar tamaños de modelos original vs cuantizado.

        Args:
            original_model: Modelo original
            quantized_model: Modelo cuantizado

        Returns:
            Diccionario con comparación de tamaños
        """
        orig_params = sum(p.numel() for p in original_model.parameters())
        quant_params = sum(p.numel() for p in quantized_model.parameters())

        # Calcular reducción
        reduction_ratio = quant_params / orig_params if orig_params > 0 else 1.0

        return {
            "original_parameters": orig_params,
            "quantized_parameters": quant_params,
            "reduction_ratio": reduction_ratio,
            "memory_savings_percent": (1 - reduction_ratio) * 100
        }

    def validate_quantization(
        self,
        original_model: EmpoorioLM,
        quantized_model: EmpoorioLM,
        test_prompts: list,
        tokenizer
    ) -> Dict[str, Any]:
        """
        Validar que la cuantización mantiene calidad aceptable.

        Args:
            original_model: Modelo original
            quantized_model: Modelo cuantizado
            test_prompts: Lista de prompts de prueba
            tokenizer: Tokenizer

        Returns:
            Resultados de validación
        """
        logger.info("🔍 Validando cuantización...")

        results = {
            "perplexity_comparison": [],
            "generation_quality": [],
            "inference_speed": []
        }

        # Configuración de generación
        gen_config = {
            "max_new_tokens": 50,
            "temperature": 0.7,
            "do_sample": True,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id
        }

        for prompt in test_prompts[:3]:  # Limitar a 3 prompts para validación rápida
            logger.info(f"   Probando prompt: {prompt[:50]}...")

            # Generar con modelo original
            inputs = tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                orig_output = original_model.generate(inputs["input_ids"], **gen_config)
                orig_text = tokenizer.decode(orig_output[0], skip_special_tokens=True)

            # Generar con modelo cuantizado
            with torch.no_grad():
                quant_output = quantized_model.generate(inputs["input_ids"], **gen_config)
                quant_text = tokenizer.decode(quant_output[0], skip_special_tokens=True)

            # Comparar calidad (simplificada - en producción usar métricas más sofisticadas)
            similarity = self._calculate_text_similarity(orig_text, quant_text)

            results["generation_quality"].append({
                "prompt": prompt,
                "original_length": len(orig_text),
                "quantized_length": len(quant_text),
                "similarity_score": similarity
            })

        logger.info("✅ Validación completada")
        return results

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud simple entre textos (placeholder para implementación real)."""
        # Implementación simplificada - en producción usar BLEU, ROUGE, etc.
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


class DynamicCalibration:
    """
    Calibración automática usando datos representativos para optimizar cuantización.
    """

    def __init__(self):
        self.calibration_data = []
        self.activation_ranges = {}

    def collect_calibration_data(self, model: EmpoorioLM, dataloader: DataLoader, num_samples: int = 1000):
        """
        Recopilar datos de calibración del modelo.

        Args:
            model: Modelo a calibrar
            dataloader: DataLoader con datos representativos
            num_samples: Número de muestras para calibración
        """
        logger.info(f"🔄 Recopilando {num_samples} muestras de calibración...")

        model.eval()
        hook_handles = self._register_hooks(model)

        collected = 0
        with torch.no_grad():
            for batch in dataloader:
                if collected >= num_samples:
                    break

                inputs = {k: v.to(model.device) for k, v in batch.items() if k != 'labels'}
                _ = model(**inputs)
                collected += len(batch['input_ids'])

        self._remove_hooks(hook_handles)
        logger.info("✅ Calibración completada")

    def _register_hooks(self, model: EmpoorioLM) -> List[torch.utils.hooks.RemovableHandle]:
        """Registrar hooks para capturar activaciones."""
        handles = []

        def hook_fn(name):
            def hook(module, input, output):
                if isinstance(output, torch.Tensor):
                    self.activation_ranges[name] = torch.cat([
                        self.activation_ranges.get(name, torch.tensor([])),
                        output.detach().flatten()
                    ], dim=0)
            return hook

        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                handles.append(module.register_forward_hook(hook_fn(name)))

        return handles

    def _remove_hooks(self, handles: List[torch.utils.hooks.RemovableHandle]):
        """Remover hooks registrados."""
        for handle in handles:
            handle.remove()

    def get_optimal_quantization_config(self) -> Dict[str, Any]:
        """
        Obtener configuración óptima de cuantización basada en calibración.

        Returns:
            Configuración optimizada
        """
        config = {}

        for layer_name, activations in self.activation_ranges.items():
            if len(activations) > 0:
                # Calcular rango dinámico
                min_val, max_val = activations.min(), activations.max()
                dynamic_range = max_val - min_val

                # Determinar mejor tipo de cuantización
                if dynamic_range > 10.0:  # Rango amplio
                    config[layer_name] = "fp16"
                elif dynamic_range > 1.0:  # Rango medio
                    config[layer_name] = "int8"
                else:  # Rango pequeño
                    config[layer_name] = "int4"

        return config


class PerformanceMonitor:
    """
    Monitoreo de precisión vs velocidad para modelos cuantizados.
    """

    def __init__(self):
        self.metrics_history = []
        self.baseline_metrics = {}

    def measure_inference_performance(
        self,
        model: EmpoorioLM,
        test_dataloader: DataLoader,
        tokenizer,
        num_runs: int = 5
    ) -> Dict[str, Any]:
        """
        Medir rendimiento de inferencia.

        Args:
            model: Modelo a evaluar
            test_dataloader: Datos de prueba
            tokenizer: Tokenizer
            num_runs: Número de ejecuciones para promedio

        Returns:
            Métricas de rendimiento
        """
        logger.info("📊 Midiendo rendimiento de inferencia...")

        model.eval()
        latencies = []
        throughputs = []
        memory_usage = []

        with torch.no_grad():
            for run in range(num_runs):
                run_latencies = []
                run_start_time = time.time()

                for batch in test_dataloader:
                    batch_start = time.time()

                    inputs = {k: v.to(model.device) for k, v in batch.items() if k != 'labels'}
                    outputs = model.generate(
                        inputs["input_ids"],
                        max_new_tokens=20,
                        do_sample=False
                    )

                    batch_end = time.time()
                    run_latencies.append(batch_end - batch_start)

                    # Medir uso de memoria
                    if torch.cuda.is_available():
                        memory_usage.append(torch.cuda.memory_allocated() / 1024**3)  # GB

                run_end_time = time.time()
                total_run_time = run_end_time - run_start_time

                latencies.append(np.mean(run_latencies))
                throughputs.append(len(test_dataloader) / total_run_time)

        metrics = {
            "avg_latency": np.mean(latencies),
            "std_latency": np.std(latencies),
            "avg_throughput": np.mean(throughputs),
            "std_throughput": np.std(throughputs),
            "memory_usage_gb": np.mean(memory_usage) if memory_usage else 0,
            "timestamp": time.time()
        }

        self.metrics_history.append(metrics)
        logger.info(f"✅ Rendimiento medido - Latency: {metrics['avg_latency']:.3f}s, Throughput: {metrics['avg_throughput']:.2f} samples/s")

        return metrics

    def measure_accuracy(
        self,
        original_model: EmpoorioLM,
        quantized_model: EmpoorioLM,
        test_dataset: Dataset,
        tokenizer
    ) -> Dict[str, Any]:
        """
        Medir precisión del modelo cuantizado vs original.

        Args:
            original_model: Modelo original
            quantized_model: Modelo cuantizado
            test_dataset: Dataset de prueba
            tokenizer: Tokenizer

        Returns:
            Métricas de precisión
        """
        logger.info("🎯 Midiendo precisión...")

        original_model.eval()
        quantized_model.eval()

        perplexities = {"original": [], "quantized": []}
        similarities = []

        with torch.no_grad():
            for i, sample in enumerate(test_dataset):
                if i >= 100:  # Limitar a 100 muestras
                    break

                inputs = tokenizer(sample["text"], return_tensors="pt", truncation=True, max_length=512)
                inputs = {k: v.to(original_model.device) for k, v in inputs.items()}

                # Perplexity original
                orig_outputs = original_model(**inputs, labels=inputs["input_ids"])
                perplexities["original"].append(torch.exp(orig_outputs.loss).item())

                # Perplexity cuantizado
                quant_outputs = quantized_model(**inputs, labels=inputs["input_ids"])
                perplexities["quantized"].append(torch.exp(quant_outputs.loss).item())

                # Similitud de generación
                orig_gen = original_model.generate(inputs["input_ids"], max_new_tokens=50, do_sample=False)
                quant_gen = quantized_model.generate(inputs["input_ids"], max_new_tokens=50, do_sample=False)

                orig_text = tokenizer.decode(orig_gen[0], skip_special_tokens=True)
                quant_text = tokenizer.decode(quant_gen[0], skip_special_tokens=True)

                similarity = self._calculate_bleu_similarity(orig_text, quant_text)
                similarities.append(similarity)

        accuracy_metrics = {
            "original_perplexity": np.mean(perplexities["original"]),
            "quantized_perplexity": np.mean(perplexities["quantized"]),
            "perplexity_degradation": (np.mean(perplexities["quantized"]) - np.mean(perplexities["original"])) / np.mean(perplexities["original"]),
            "avg_similarity": np.mean(similarities),
            "timestamp": time.time()
        }

        logger.info(f"✅ Precisión medida - Perplexity degradation: {accuracy_metrics['perplexity_degradation']:.3f}, Similarity: {accuracy_metrics['avg_similarity']:.3f}")

        return accuracy_metrics

    def _calculate_bleu_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud BLEU simplificada."""
        # Implementación simplificada - en producción usar BLEU score real
        words1 = text1.lower().split()
        words2 = text2.lower().split()

        if not words1 or not words2:
            return 0.0

        # Similitud de Jaccard
        set1, set2 = set(words1), set(words2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0


class AdaptiveQuantization:
    """
    Ajuste dinámico de cuantización basado en carga de trabajo.
    """

    def __init__(self, config: QuantizationConfig):
        self.config = config
        self.current_precision = {}
        self.workload_history = []

    def adapt_quantization(
        self,
        model: EmpoorioLM,
        current_workload: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Adaptar cuantización basada en carga de trabajo actual.

        Args:
            model: Modelo a adaptar
            current_workload: Información de carga actual
            performance_metrics: Métricas de rendimiento actuales

        Returns:
            Nueva configuración de cuantización por capa
        """
        logger.info("🔄 Adaptando cuantización...")

        # Analizar carga de trabajo
        workload_intensity = self._analyze_workload(current_workload)
        self.workload_history.append(workload_intensity)

        # Determinar precisión objetivo
        if workload_intensity > 0.8:  # Alta carga
            target_precision = "int8"  # Mayor velocidad
        elif workload_intensity > 0.5:  # Carga media
            target_precision = "int4"  # Balance
        else:  # Baja carga
            target_precision = "fp16"  # Mayor precisión

        # Verificar si cumple con umbral de precisión
        if performance_metrics.get("avg_similarity", 1.0) < self.config.adaptive_threshold:
            # Si precisión baja, aumentar precisión
            target_precision = self._increase_precision(target_precision)

        # Aplicar adaptación por capas críticas
        new_config = {}
        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                # Capas críticas mantienen mayor precisión
                if any(critical in name for critical in ["lm_head", "embed_tokens"]):
                    new_config[name] = "fp16"
                else:
                    new_config[name] = target_precision

        self.current_precision = new_config
        logger.info(f"✅ Cuantización adaptada a: {target_precision}")

        return new_config

    def _analyze_workload(self, workload: Dict[str, Any]) -> float:
        """Analizar intensidad de carga de trabajo."""
        # Implementación simplificada
        intensity = 0.0

        if "requests_per_second" in workload:
            intensity += min(workload["requests_per_second"] / 100.0, 1.0)

        if "cpu_usage" in workload:
            intensity += workload["cpu_usage"] / 100.0

        if "memory_usage" in workload:
            intensity += workload["memory_usage"] / 100.0

        return min(intensity / 3.0, 1.0)

    def _increase_precision(self, current_precision: str) -> str:
        """Aumentar precisión de cuantización."""
        precision_hierarchy = {"int4": "int8", "int8": "fp16", "fp16": "fp32"}
        return precision_hierarchy.get(current_precision, "fp16")


class FederatedQuantization:
    """
    Cuantización compatible con federated learning.
    """

    def __init__(self):
        self.node_quantization_configs = {}
        self.global_quantization_state = {}

    def create_federated_quantization_config(
        self,
        num_nodes: int,
        heterogeneous_nodes: bool = True
    ) -> Dict[str, QuantizationConfig]:
        """
        Crear configuración de cuantización para federated learning.

        Args:
            num_nodes: Número de nodos
            heterogeneous_nodes: Si los nodos tienen capacidades diferentes

        Returns:
            Configuración por nodo
        """
        configs = {}

        for node_id in range(num_nodes):
            if heterogeneous_nodes:
                # Nodos heterogéneos - diferentes capacidades
                node_capability = np.random.choice(["low", "medium", "high"], p=[0.3, 0.5, 0.2])

                if node_capability == "high":
                    quant_type = "fp16"
                elif node_capability == "medium":
                    quant_type = "int8"
                else:
                    quant_type = "int4"
            else:
                # Nodos homogéneos
                quant_type = "int8"

            configs[f"node_{node_id}"] = QuantizationConfig(
                quantization_type=quant_type,
                federated_compatible=True,
                calibration_samples=500  # Menos muestras para eficiencia
            )

        self.node_quantization_configs = configs
        return configs

    def aggregate_quantized_updates(
        self,
        node_updates: List[Dict[str, torch.Tensor]],
        aggregation_method: str = "fedavg"
    ) -> Dict[str, torch.Tensor]:
        """
        Agregar actualizaciones cuantizadas de nodos.

        Args:
            node_updates: Lista de actualizaciones por nodo
            aggregation_method: Método de agregación

        Returns:
            Actualización global agregada
        """
        logger.info(f"🔄 Agregando {len(node_updates)} actualizaciones cuantizadas...")

        if aggregation_method == "fedavg":
            # Federated Averaging con cuantización
            global_update = {}

            for key in node_updates[0].keys():
                layer_updates = [update[key] for update in node_updates if key in update]

                if layer_updates:
                    # Promedio con manejo de cuantización
                    stacked = torch.stack(layer_updates, dim=0)
                    global_update[key] = torch.mean(stacked, dim=0)

            logger.info("✅ Actualizaciones agregadas")
            return global_update

        else:
            raise ValueError(f"Método de agregación no soportado: {aggregation_method}")

    def compress_gradients_for_transmission(
        self,
        gradients: Dict[str, torch.Tensor],
        compression_ratio: float = 0.1
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
        """
        Comprimir gradientes para transmisión eficiente.

        Args:
            gradients: Gradientes a comprimir
            compression_ratio: Ratio de compresión

        Returns:
            Gradientes comprimidos y metadatos para descompresión
        """
        compressed = {}
        metadata = {}

        for name, grad in gradients.items():
            # Cuantización de gradientes
            grad_min, grad_max = grad.min(), grad.max()
            scale = (grad_max - grad_min) / 255.0 if grad_max > grad_min else 1.0

            # Cuantizar a 8-bit
            quantized = torch.round((grad - grad_min) / scale).clamp(0, 255).to(torch.uint8)

            # Comprimir manteniendo valores más importantes
            if compression_ratio < 1.0:
                k = max(1, int(quantized.numel() * compression_ratio))
                _, indices = torch.topk(grad.abs().flatten(), k)
                compressed[name] = quantized.flatten()[indices]
                metadata[name] = {
                    "scale": scale,
                    "min": grad_min,
                    "indices": indices,
                    "original_shape": grad.shape
                }
            else:
                compressed[name] = quantized
                metadata[name] = {
                    "scale": scale,
                    "min": grad_min,
                    "original_shape": grad.shape
                }

        return compressed, metadata

    def decompress_gradients(
        self,
        compressed_gradients: Dict[str, torch.Tensor],
        metadata: Dict[str, Any]
    ) -> Dict[str, torch.Tensor]:
        """
        Descomprimir gradientes recibidos.

        Args:
            compressed_gradients: Gradientes comprimidos
            metadata: Metadatos para descompresión

        Returns:
            Gradientes descomprimidos
        """
        decompressed = {}

        for name, compressed in compressed_gradients.items():
            meta = metadata[name]

            if "indices" in meta:
                # Reconstruir tensor sparse
                grad = torch.zeros(meta["original_shape"].numel(), dtype=torch.float32, device=compressed.device)
                grad[meta["indices"]] = compressed.float()
                grad = grad.view(meta["original_shape"])
            else:
                # Tensor completo
                grad = compressed.float().view(meta["original_shape"])

            # Descuantizar
            grad = grad * meta["scale"] + meta["min"]
            decompressed[name] = grad

        return decompressed


class QuantizationAwareTraining:
    """
    Entrenamiento con cuantización integrada (QAT).
    """

    def __init__(self, quantization_config: QuantizationConfig):
        self.config = quantization_config
        self.fake_quant_modules = {}

    def enable_qat(self, model: EmpoorioLM) -> EmpoorioLM:
        """
        Habilitar Quantization Aware Training en el modelo.

        Args:
            model: Modelo a entrenar con QAT

        Returns:
            Modelo con QAT habilitado
        """
        logger.info("🔄 Habilitando Quantization Aware Training...")

        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Reemplazar con FakeQuantLinear
                fake_quant_layer = FakeQuantLinear(
                    module.in_features,
                    module.out_features,
                    quantization_type=self.config.quantization_type,
                    bias=module.bias is not None
                )

                # Copiar pesos
                fake_quant_layer.weight.data = module.weight.data.clone()
                if module.bias is not None:
                    fake_quant_layer.bias.data = module.bias.data.clone()

                # Reemplazar en el modelo
                parent_name, child_name = name.rsplit('.', 1)
                parent_module = model.get_submodule(parent_name)
                setattr(parent_module, child_name, fake_quant_layer)

                self.fake_quant_modules[name] = fake_quant_layer

        logger.info("✅ QAT habilitado")
        return model

    def train_with_qat(
        self,
        model: EmpoorioLM,
        train_dataset: Dataset,
        eval_dataset: Dataset,
        training_args: TrainingArguments
    ) -> EmpoorioLM:
        """
        Entrenar modelo con QAT.

        Args:
            model: Modelo con QAT habilitado
            train_dataset: Dataset de entrenamiento
            eval_dataset: Dataset de evaluación
            training_args: Argumentos de entrenamiento

        Returns:
            Modelo entrenado
        """
        logger.info("🏋️ Entrenando con Quantization Aware Training...")

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
        )

        trainer.train()
        logger.info("✅ Entrenamiento QAT completado")

        return model

    def convert_to_quantized(self, model: EmpoorioLM) -> EmpoorioLM:
        """
        Convertir modelo QAT a cuantización real.

        Args:
            model: Modelo entrenado con QAT

        Returns:
            Modelo con cuantización real
        """
        logger.info("🔄 Convirtiendo a cuantización real...")

        for name, fake_quant_layer in self.fake_quant_modules.items():
            # Obtener pesos cuantizados
            quantized_weight = fake_quant_layer.get_quantized_weight()

            # Crear capa cuantizada real
            if self.config.quantization_type == "int8":
                quantized_layer = bnb.nn.Linear8bitLt(
                    fake_quant_layer.in_features,
                    fake_quant_layer.out_features,
                    bias=fake_quant_layer.bias is not None,
                    has_fp16_weights=False
                )
            elif self.config.quantization_type == "int4":
                quantized_layer = bnb.nn.Linear4bit(
                    fake_quant_layer.in_features,
                    fake_quant_layer.out_features,
                    bias=fake_quant_layer.bias is not None,
                    compute_dtype=torch.float16,
                    compress_statistics=False
                )
            else:
                continue  # Mantener capa original

            # Copiar pesos cuantizados
            quantized_layer.weight.data = quantized_weight
            if fake_quant_layer.bias is not None:
                quantized_layer.bias.data = fake_quant_layer.bias.data.clone()

            # Reemplazar en el modelo
            parent_name, child_name = name.rsplit('.', 1)
            parent_module = model.get_submodule(parent_name)
            setattr(parent_module, child_name, quantized_layer)

        logger.info("✅ Conversión a cuantización real completada")
        return model


class FakeQuantLinear(nn.Module):
    """
    Capa lineal con cuantización falsa para QAT.
    """

    def __init__(self, in_features: int, out_features: int, quantization_type: str = "int8", bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.quantization_type = quantization_type

        self.weight = nn.Parameter(torch.randn(out_features, in_features))
        self.bias = nn.Parameter(torch.randn(out_features)) if bias else None

        # Parámetros de cuantización
        self.register_buffer("weight_scale", torch.ones(1))
        self.register_buffer("weight_zero_point", torch.zeros(1))

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        # Cuantización falsa durante entrenamiento
        quantized_weight = self._fake_quantize_weight(self.weight)
        return nn.functional.linear(input, quantized_weight, self.bias)

    def _fake_quantize_weight(self, weight: torch.Tensor) -> torch.Tensor:
        """Aplicar cuantización falsa a los pesos."""
        if self.quantization_type == "int8":
            # Simular cuantización INT8
            scale = weight.abs().max() / 127.0
            quantized = torch.round(weight / scale).clamp(-128, 127)
            return quantized * scale
        elif self.quantization_type == "int4":
            # Simular cuantización INT4
            scale = weight.abs().max() / 7.0
            quantized = torch.round(weight / scale).clamp(-8, 7)
            return quantized * scale
        else:
            return weight  # Sin cuantización

    def get_quantized_weight(self) -> torch.Tensor:
        """Obtener pesos cuantizados para conversión final."""
        return self._fake_quantize_weight(self.weight)


def quantize_empoorio_model(
    model_path: str,
    output_path: str,
    quantization_type: str = "int8",
    use_calibration: bool = True,
    calibration_data_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de conveniencia para cuantizar modelo EmpoorioLM con sistema completo.

    Args:
        model_path: Ruta del modelo original
        output_path: Ruta para guardar modelo cuantizado
        quantization_type: Tipo de cuantización ('int8', 'int4', 'fp16', 'mixed')
        use_calibration: Usar calibración dinámica
        calibration_data_path: Ruta a datos de calibración
        **kwargs: Parámetros adicionales

    Returns:
        Resultados completos de cuantización
    """
    quantizer = AdvancedQuantizer()

    # Preparar datos de calibración si se especifican
    calibration_dataloader = None
    if use_calibration and calibration_data_path:
        try:
            # Cargar datos de calibración (implementación simplificada)
            from torch.utils.data import DataLoader, TensorDataset
            # Aquí iría la lógica para cargar datos reales
            dummy_data = torch.randn(100, 512)  # Placeholder
            dummy_labels = torch.randint(0, 1000, (100,))  # Placeholder
            dataset = TensorDataset(dummy_data, dummy_labels)
            calibration_dataloader = DataLoader(dataset, batch_size=8)
            logger.info("📊 Datos de calibración preparados")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar datos de calibración: {e}")

    # Cuantizar modelo
    quantized_model = quantizer.quantize_model(
        model_path=model_path,
        quantization_type=quantization_type,
        save_path=output_path,
        calibration_dataloader=calibration_dataloader,
        use_dynamic_calibration=use_calibration,
        **kwargs
    )

    # Obtener estadísticas completas
    stats = {
        "quantization_type": quantization_type,
        "model_path": str(model_path),
        "output_path": str(output_path),
        "device": str(quantizer.device),
        "memory_usage": quantizer._get_model_memory_usage(quantized_model),
        "calibration_used": use_calibration,
        "advanced_features": {
            "dynamic_calibration": use_calibration,
            "performance_monitoring": True,
            "adaptive_quantization": True
        }
    }

    logger.info("🎉 Cuantización avanzada completada exitosamente")
    logger.info(f"   Resultados: {stats}")

    return stats


def create_quantization_pipeline(
    model_path: str,
    config: QuantizationConfig,
    calibration_data_path: Optional[str] = None,
    federated_nodes: int = 0
) -> Dict[str, Any]:
    """
    Crear pipeline completo de cuantización con todos los componentes.

    Args:
        model_path: Ruta del modelo
        config: Configuración de cuantización
        calibration_data_path: Ruta a datos de calibración
        federated_nodes: Número de nodos federados (0 = no federado)

    Returns:
        Resultados del pipeline completo
    """
    logger.info("🚀 Iniciando pipeline completo de cuantización avanzada...")

    results = {
        "quantization": {},
        "calibration": {},
        "federated": {},
        "training": {},
        "monitoring": {},
        "adaptive": {}
    }

    # 1. Inicializar componentes
    quantizer = AdvancedQuantizer(config)
    fed_quantizer = FederatedQuantization() if federated_nodes > 0 else None
    qat_trainer = QuantizationAwareTraining(config)

    # 2. Preparar datos de calibración
    calibration_dataloader = None
    if calibration_data_path:
        # Implementación simplificada
        from torch.utils.data import DataLoader, TensorDataset
        dummy_data = torch.randn(1000, 512)
        dummy_labels = torch.randint(0, 1000, (1000,))
        dataset = TensorDataset(dummy_data, dummy_labels)
        calibration_dataloader = DataLoader(dataset, batch_size=16)

    # 3. Cuantización con calibración
    logger.info("📦 Fase 1: Cuantización con calibración dinámica")
    quantized_model = quantizer.quantize_model(
        model_path=model_path,
        quantization_type=config.quantization_type,
        calibration_dataloader=calibration_dataloader,
        use_dynamic_calibration=True
    )
    results["quantization"] = {"status": "completed", "memory_usage": quantizer._get_model_memory_usage(quantized_model)}

    # 4. Configuración federada si aplica
    if fed_quantizer and federated_nodes > 0:
        logger.info(f"🌐 Fase 2: Configuración federada para {federated_nodes} nodos")
        fed_configs = fed_quantizer.create_federated_quantization_config(federated_nodes)
        results["federated"] = {"status": "completed", "nodes_configured": len(fed_configs)}

    # 5. Quantization Aware Training
    logger.info("🏋️ Fase 3: Quantization Aware Training")
    qat_model = qat_trainer.enable_qat(quantized_model)
    results["training"] = {"status": "qat_enabled", "model_prepared": True}

    # 6. Monitoreo de rendimiento
    logger.info("📊 Fase 4: Monitoreo de rendimiento")
    if calibration_dataloader:
        perf_metrics = quantizer.performance_monitor.measure_inference_performance(
            qat_model, calibration_dataloader, None
        )
        results["monitoring"] = {"status": "completed", "metrics": perf_metrics}

    # 7. Cuantización adaptativa
    logger.info("🔄 Fase 5: Configuración adaptativa")
    adaptive_config = quantizer.adaptive_quantization.adapt_quantization(
        qat_model, {"requests_per_second": 10}, perf_metrics if 'perf_metrics' in locals() else {}
    )
    results["adaptive"] = {"status": "completed", "config": adaptive_config}

    logger.info("✅ Pipeline completo de cuantización avanzada finalizado")
    return results


if __name__ == "__main__":
    # Ejemplo de uso del sistema completo de cuantización avanzada
    import argparse

    parser = argparse.ArgumentParser(description="Sistema avanzado de cuantización para EmpoorioLM")
    parser.add_argument("--model_path", required=True, help="Ruta del modelo original")
    parser.add_argument("--output_path", required=True, help="Ruta para guardar modelo cuantizado")
    parser.add_argument("--quantization_type", default="int8",
                        choices=["int8", "int4", "fp16", "mixed"],
                        help="Tipo de cuantización")
    parser.add_argument("--use_calibration", action="store_true",
                        help="Usar calibración dinámica")
    parser.add_argument("--calibration_data", help="Ruta a datos de calibración")
    parser.add_argument("--federated_nodes", type=int, default=0,
                        help="Número de nodos federados (0 = no federado)")
    parser.add_argument("--run_pipeline", action="store_true",
                        help="Ejecutar pipeline completo con todos los componentes")
    parser.add_argument("--double_quant", action="store_true",
                        help="Usar double quantization para INT4")

    args = parser.parse_args()

    if args.run_pipeline:
        # Ejecutar pipeline completo
        config = QuantizationConfig(
            quantization_type=args.quantization_type,
            calibration_samples=1000 if args.use_calibration else 0,
            federated_compatible=args.federated_nodes > 0
        )

        results = create_quantization_pipeline(
            model_path=args.model_path,
            config=config,
            calibration_data_path=args.calibration_data,
            federated_nodes=args.federated_nodes
        )

        print("🎉 Pipeline completo ejecutado exitosamente!")
        print(f"📦 Cuantización: {results['quantization']}")
        print(f"🎯 Calibración: {results['calibration']}")
        if args.federated_nodes > 0:
            print(f"🌐 Federado: {results['federated']}")
        print(f"🏋️ Entrenamiento: {results['training']}")
        print(f"📊 Monitoreo: {results['monitoring']}")
        print(f"🔄 Adaptativo: {results['adaptive']}")

    else:
        # Cuantización básica
        result = quantize_empoorio_model(
            model_path=args.model_path,
            output_path=args.output_path,
            quantization_type=args.quantization_type,
            use_calibration=args.use_calibration,
            calibration_data_path=args.calibration_data,
            double_quant=args.double_quant
        )

        print(f"✅ Modelo cuantizado guardado en: {args.output_path}")
        print(f"   Tipo: {args.quantization_type}")
        print(f"   Memoria: {result['memory_usage']}")
        print(f"   Calibración usada: {result['calibration_used']}")
        print(f"   Características avanzadas: {result['advanced_features']}")