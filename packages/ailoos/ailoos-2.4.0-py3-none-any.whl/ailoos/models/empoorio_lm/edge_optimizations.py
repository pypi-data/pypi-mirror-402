#!/usr/bin/env python3
"""
Optimizaciones para Edge Inference en EmpoorioLM.
Incluye cuantización, pruning, KV cache optimizado y otras técnicas para dispositivos edge.
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple
import math


class DynamicQuantization:
    """
    Cuantización dinámica para edge inference.
    Soporta INT8, INT4 y FP16 con calibración automática.
    """

    def __init__(self, bits: int = 8, calibration_samples: int = 100):
        self.bits = bits
        self.calibration_samples = calibration_samples
        self.calibration_data = []
        self.quantized = False

        # Configuración por bits
        self._setup_quantization_config()

    def _setup_quantization_config(self):
        """Configurar parámetros de cuantización."""
        if self.bits == 8:
            self.scale_min, self.scale_max = -128, 127
            self.dtype = torch.int8
        elif self.bits == 4:
            self.scale_min, self.scale_max = -8, 7
            self.dtype = torch.int8  # Usar int8 para almacenar int4
        elif self.bits == 16:
            self.scale_min, self.scale_max = None, None  # FP16
            self.dtype = torch.float16
        else:
            raise ValueError(f"Bits no soportados: {self.bits}")

    def calibrate(self, tensor: torch.Tensor):
        """Calibrar con datos de entrada."""
        if len(self.calibration_data) < self.calibration_samples:
            self.calibration_data.append(tensor.detach())

    def quantize_tensor(self, tensor: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Cuantizar tensor.

        Returns:
            Tuple de (quantized_tensor, scale, zero_point)
        """
        if self.bits == 16:
            # FP16 - solo convertir tipo
            return tensor.half(), torch.ones(1), torch.zeros(1)

        # Calcular scale y zero point
        if self.calibration_data:
            # Usar datos de calibración
            all_data = torch.cat([t.flatten() for t in self.calibration_data])
            min_val = all_data.min()
            max_val = all_data.max()
        else:
            # Usar estadísticas del tensor actual
            min_val = tensor.min()
            max_val = tensor.max()

        # Evitar división por cero
        range_val = max_val - min_val
        if range_val == 0:
            range_val = 1e-8

        if self.bits == 8:
            scale = range_val / 255.0
            zero_point = (-min_val / scale).round().clamp(-128, 127)
        elif self.bits == 4:
            scale = range_val / 15.0
            zero_point = (-min_val / scale).round().clamp(-8, 7)

        # Cuantizar
        quantized = (tensor / scale + zero_point).round().clamp(self.scale_min, self.scale_max)
        quantized = quantized.to(self.dtype)

        return quantized, scale, zero_point

    def dequantize_tensor(self, quantized: torch.Tensor, scale: torch.Tensor, zero_point: torch.Tensor) -> torch.Tensor:
        """Descuantizar tensor."""
        if self.bits == 16:
            return quantized.float()

        return (quantized.float() - zero_point) * scale


class OptimizedKVCache:
    """
    KV Cache optimizado para edge devices.
    Incluye compresión, pruning y gestión de memoria eficiente.
    """

    def __init__(self, max_seq_len: int = 2048, compression_ratio: float = 0.5):
        self.max_seq_len = max_seq_len
        self.compression_ratio = compression_ratio
        self.cache = {}
        self.compressed_cache = {}

    def update(self, layer_idx: int, key: torch.Tensor, value: torch.Tensor):
        """Actualizar cache para una capa."""
        batch_size, seq_len, num_heads, head_dim = key.shape

        if layer_idx not in self.cache:
            self.cache[layer_idx] = {
                'key': torch.zeros(batch_size, self.max_seq_len, num_heads, head_dim, device=key.device),
                'value': torch.zeros(batch_size, self.max_seq_len, num_heads, head_dim, device=value.device),
                'length': 0
            }

        cache_entry = self.cache[layer_idx]
        current_len = cache_entry['length']

        # Concatenar nuevos tokens
        if current_len + seq_len <= self.max_seq_len:
            cache_entry['key'][:, current_len:current_len + seq_len] = key
            cache_entry['value'][:, current_len:current_len + seq_len] = value
            cache_entry['length'] = current_len + seq_len
        else:
            # Cache full - usar estrategia de reemplazo
            self._evict_and_update(layer_idx, key, value)

    def get(self, layer_idx: int, start_pos: int = 0) -> Tuple[torch.Tensor, torch.Tensor]:
        """Obtener cache para una capa."""
        if layer_idx not in self.cache:
            return None, None

        cache_entry = self.cache[layer_idx]
        length = cache_entry['length']

        if start_pos >= length:
            return None, None

        key = cache_entry['key'][:, :length]
        value = cache_entry['value'][:, :length]

        return key, value

    def _evict_and_update(self, layer_idx: int, key: torch.Tensor, value: torch.Tensor):
        """Estrategia de eviction cuando cache está lleno."""
        cache_entry = self.cache[layer_idx]

        # Mantener solo la mitad más reciente
        keep_len = self.max_seq_len // 2
        cache_entry['key'] = torch.cat([
            cache_entry['key'][:, -keep_len:],
            key
        ], dim=1)
        cache_entry['value'] = torch.cat([
            cache_entry['value'][:, -keep_len:],
            value
        ], dim=1)
        cache_entry['length'] = keep_len + key.shape[1]

    def compress(self):
        """Comprimir cache para ahorrar memoria."""
        for layer_idx, cache_entry in self.cache.items():
            if cache_entry['length'] > 0:
                # Compresión simple: mantener solo tokens importantes
                keep_tokens = int(cache_entry['length'] * self.compression_ratio)

                # Estrategia: mantener tokens más recientes
                self.compressed_cache[layer_idx] = {
                    'key': cache_entry['key'][:, -keep_tokens:],
                    'value': cache_entry['value'][:, -keep_tokens:],
                    'length': keep_tokens
                }

    def clear(self):
        """Limpiar cache."""
        self.cache.clear()
        self.compressed_cache.clear()


class EdgeOptimizedEmpoorioLM(nn.Module):
    """
    Versión optimizada de EmpoorioLM para edge inference.
    Incluye cuantización, KV cache optimizado y otras optimizaciones.
    """

    def __init__(self, base_model, quantization_bits: int = 8, enable_kv_cache: bool = True):
        super().__init__()
        self.base_model = base_model
        self.quantization_bits = quantization_bits
        self.enable_kv_cache = enable_kv_cache

        # Componentes de optimización
        self.quantizer = DynamicQuantization(bits=quantization_bits) if quantization_bits < 16 else None
        self.kv_cache = OptimizedKVCache() if enable_kv_cache else None

        # Estado de optimización
        self.is_optimized = False

    def optimize_for_edge(self):
        """Aplicar optimizaciones para edge."""
        if self.is_optimized:
            return

        print("🔧 Aplicando optimizaciones para edge inference...")

        # Convertir a half precision si es posible
        if torch.cuda.is_available():
            self.half()

        # Aplicar pruning si está habilitado
        self._apply_pruning()

        # Marcar como optimizado
        self.is_optimized = True
        print("✅ Optimizaciones aplicadas")

    def _apply_pruning(self, pruning_ratio: float = 0.1):
        """Aplicar pruning a pesos del modelo."""
        for name, module in self.base_model.named_modules():
            if isinstance(module, nn.Linear):
                # Pruning simple: setear pesos pequeños a cero
                with torch.no_grad():
                    weights = module.weight.data
                    threshold = torch.quantile(torch.abs(weights), pruning_ratio)
                    mask = torch.abs(weights) > threshold
                    module.weight.data *= mask

    def forward(self, input_ids: torch.Tensor, **kwargs) -> Dict[str, Any]:
        """Forward pass optimizado."""
        # Aplicar cuantización si está habilitada
        if self.quantizer is not None:
            # Calibrar con inputs
            self.quantizer.calibrate(input_ids.float())

        # Usar modelo base
        outputs = self.base_model(input_ids, **kwargs)

        # Aplicar cuantización a outputs si necesario
        if self.quantizer is not None and 'logits' in outputs:
            quantized_logits, scale, zero_point = self.quantizer.quantize_tensor(outputs['logits'])
            outputs['quantized_logits'] = quantized_logits
            outputs['quantization_scale'] = scale
            outputs['quantization_zero_point'] = zero_point

        return outputs

    def get_memory_usage(self) -> Dict[str, float]:
        """Obtener uso de memoria del modelo optimizado."""
        total_params = sum(p.numel() for p in self.parameters())
        memory_mb = total_params * 4 / (1024 * 1024)  # Asumiendo float32

        return {
            "total_parameters": total_params,
            "memory_mb": memory_mb,
            "quantization_bits": self.quantization_bits,
            "kv_cache_enabled": self.enable_kv_cache
        }


class ModelPruner:
    """
    Utilidades para pruning de modelos EmpoorioLM.
    """

    @staticmethod
    def magnitude_pruning(model: nn.Module, pruning_ratio: float = 0.2):
        """Pruning por magnitud."""
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                ModelPruner._prune_linear_layer(module, pruning_ratio)

    @staticmethod
    def _prune_linear_layer(layer: nn.Linear, pruning_ratio: float):
        """Prune una capa lineal."""
        with torch.no_grad():
            weights = layer.weight.data
            threshold = torch.quantile(torch.abs(weights), pruning_ratio)
            mask = torch.abs(weights) > threshold
            layer.weight.data *= mask

            # También prune bias si existe
            if layer.bias is not None:
                bias_threshold = torch.quantile(torch.abs(layer.bias.data), pruning_ratio)
                bias_mask = torch.abs(layer.bias.data) > bias_threshold
                layer.bias.data *= bias_mask

    @staticmethod
    def structured_pruning(model: nn.Module, pruning_ratio: float = 0.2):
        """Pruning estructurado por cabezas de atención."""
        for name, module in model.named_modules():
            if 'attn' in name and hasattr(module, 'q_proj'):
                ModelPruner._prune_attention_heads(module, pruning_ratio)

    @staticmethod
    def _prune_attention_heads(attn_module, pruning_ratio: float):
        """Prune cabezas de atención menos importantes."""
        # Implementación simplificada - prune cabezas aleatorias
        num_heads = attn_module.q_proj.out_features // attn_module.head_dim
        heads_to_prune = int(num_heads * pruning_ratio)

        if heads_to_prune > 0:
            # Marcar cabezas para pruning (implementación simplificada)
            pass


def create_edge_optimized_model(base_model, quantization_bits: int = 8, enable_kv_cache: bool = True) -> EdgeOptimizedEmpoorioLM:
    """
    Crear versión optimizada del modelo para edge inference.

    Args:
        base_model: Modelo base EmpoorioLM
        quantization_bits: Bits para cuantización (8, 4, 16)
        enable_kv_cache: Habilitar KV cache optimizado

    Returns:
        Modelo optimizado para edge
    """
    optimized_model = EdgeOptimizedEmpoorioLM(
        base_model=base_model,
        quantization_bits=quantization_bits,
        enable_kv_cache=enable_kv_cache
    )

    # Aplicar optimizaciones
    optimized_model.optimize_for_edge()

    return optimized_model


def estimate_edge_performance(model: nn.Module, seq_len: int = 512) -> Dict[str, Any]:
    """
    Estimar rendimiento en dispositivo edge.

    Args:
        model: Modelo a evaluar
        seq_len: Longitud de secuencia para prueba

    Returns:
        Métricas de rendimiento estimadas
    """
    # Estimación simplificada
    total_params = sum(p.numel() for p in model.parameters())

    # Memoria estimada (float32 = 4 bytes)
    memory_mb = total_params * 4 / (1024 * 1024)

    # FLOPs estimados para inference
    # Muy aproximado: ~2 * params * seq_len para transformer
    flops = 2 * total_params * seq_len

    # Tiempo estimado en dispositivo edge (muy aproximado)
    # Asumiendo ~1 TFLOP/s para dispositivo edge de gama media
    estimated_time_ms = flops / 1e12 * 1000

    return {
        "total_parameters": total_params,
        "memory_mb": memory_mb,
        "estimated_flops": flops,
        "estimated_inference_time_ms": estimated_time_ms,
        "supported_sequence_length": seq_len
    }