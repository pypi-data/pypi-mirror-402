#!/usr/bin/env python3
"""
Adaptive Chunking para EmpoorioLM
Implementa chunking dinámico basado en memoria GPU disponible.
Optimización automática de chunk_size para mejor performance en diferentes hardware.
"""

import torch
import psutil
import GPUtil
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuración para adaptive chunking."""
    min_chunk_size: int = 128
    max_chunk_size: int = 4096
    memory_safety_margin: float = 0.8  # Usar solo 80% de memoria disponible
    adaptation_interval: int = 10  # Adaptar cada N pasos
    enable_memory_monitoring: bool = True
    target_memory_usage: float = 0.7  # Objetivo: 70% de memoria


class MemoryMonitor:
    """Monitor de memoria del sistema y GPU."""

    def __init__(self):
        self.gpu_available = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.gpu_available else 0

    def get_system_memory(self) -> Dict[str, float]:
        """Obtener información de memoria del sistema."""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_percent": memory.percent,
            "available_percent": 100 - memory.percent
        }

    def get_gpu_memory(self, device: int = 0) -> Dict[str, float]:
        """Obtener información de memoria GPU."""
        if not self.gpu_available:
            return {"error": "GPU no disponible"}

        try:
            gpu = GPUtil.getGPUs()[device]
            return {
                "total_gb": gpu.memoryTotal / 1024,
                "used_gb": gpu.memoryUsed / 1024,
                "free_gb": gpu.memoryFree / 1024,
                "used_percent": gpu.memoryUtil * 100,
                "free_percent": 100 - (gpu.memoryUtil * 100)
            }
        except Exception as e:
            # Fallback usando PyTorch
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(device).total_memory / (1024**3)
                allocated = torch.cuda.memory_allocated(device) / (1024**3)
                reserved = torch.cuda.memory_reserved(device) / (1024**3)
                free = total - reserved

                return {
                    "total_gb": total,
                    "used_gb": allocated,
                    "free_gb": free,
                    "used_percent": (allocated / total) * 100,
                    "free_percent": (free / total) * 100
                }
            else:
                return {"error": str(e)}

    def get_optimal_chunk_size(self, model_size_gb: float, sequence_length: int,
                              config: ChunkingConfig) -> int:
        """
        Calcular tamaño óptimo de chunk basado en memoria disponible.

        Args:
            model_size_gb: Tamaño del modelo en GB
            sequence_length: Longitud de secuencia objetivo
            config: Configuración de chunking

        Returns:
            Tamaño óptimo de chunk
        """
        if not self.gpu_available:
            # Para CPU, usar chunking conservador
            return min(config.max_chunk_size, max(config.min_chunk_size, sequence_length // 4))

        gpu_mem = self.get_gpu_memory()
        if "error" in gpu_mem:
            logger.warning(f"Error obteniendo memoria GPU: {gpu_mem['error']}")
            return config.min_chunk_size

        available_gb = gpu_mem["free_gb"] * config.memory_safety_margin

        # Estimar memoria necesaria por token
        # Esto es una aproximación simplificada
        memory_per_token_gb = model_size_gb / 1000  # Aproximación rough

        # Calcular chunk size máximo que cabe en memoria
        max_chunk_by_memory = int(available_gb / memory_per_token_gb)

        # Aplicar límites
        optimal_chunk = min(
            config.max_chunk_size,
            max(config.min_chunk_size, max_chunk_by_memory)
        )

        # Ajustar basado en longitud de secuencia
        if sequence_length < optimal_chunk:
            optimal_chunk = sequence_length

        return optimal_chunk


class AdaptiveChunking:
    """
    Sistema de chunking dinámico que se adapta a la memoria disponible.

    Características:
    - Monitoreo continuo de memoria GPU/CPU
    - Ajuste automático de chunk_size
    - Optimización para diferentes hardware
    - Modo de aprendizaje para encontrar óptimos
    """

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.memory_monitor = MemoryMonitor()
        self.current_chunk_size = config.min_chunk_size
        self.step_counter = 0
        self.performance_history = []
        self.model_size_gb = None

    def initialize(self, model_size_gb: float, sequence_length: int):
        """Inicializar con información del modelo."""
        self.model_size_gb = model_size_gb
        self.current_chunk_size = self.memory_monitor.get_optimal_chunk_size(
            model_size_gb, sequence_length, self.config
        )
        logger.info(f"Chunking inicializado: chunk_size={self.current_chunk_size}")

    def get_chunk_size(self, sequence_length: int) -> int:
        """Obtener tamaño de chunk actual, adaptándolo si es necesario."""
        if self.model_size_gb is None:
            return self.config.min_chunk_size

        # Adaptar periódicamente
        self.step_counter += 1
        if self.step_counter % self.config.adaptation_interval == 0:
            self._adapt_chunk_size(sequence_length)

        # Asegurar que no exceda la secuencia
        return min(self.current_chunk_size, sequence_length)

    def _adapt_chunk_size(self, sequence_length: int):
        """Adaptar tamaño de chunk basado en rendimiento y memoria."""
        if not self.config.enable_memory_monitoring:
            return

        # Obtener nuevo chunk size óptimo
        optimal_size = self.memory_monitor.get_optimal_chunk_size(
            self.model_size_gb, sequence_length, self.config
        )

        # Aplicar cambio gradual
        if optimal_size != self.current_chunk_size:
            # Cambiar en incrementos para estabilidad
            change_factor = 1.2 if optimal_size > self.current_chunk_size else 0.8
            new_size = int(self.current_chunk_size * change_factor)

            # Aplicar límites
            new_size = max(self.config.min_chunk_size,
                          min(self.config.max_chunk_size, new_size))

            if new_size != self.current_chunk_size:
                logger.info(f"Adaptando chunk_size: {self.current_chunk_size} -> {new_size}")
                self.current_chunk_size = new_size

    def record_performance(self, chunk_size: int, processing_time: float,
                          memory_usage: float, success: bool):
        """Registrar métricas de rendimiento para aprendizaje."""
        self.performance_history.append({
            "chunk_size": chunk_size,
            "time": processing_time,
            "memory": memory_usage,
            "success": success,
            "timestamp": torch.cuda.Event(enable_timing=True).elapsed_time() if torch.cuda.is_available() else 0
        })

        # Mantener historial limitado
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-50:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento."""
        if not self.performance_history:
            return {}

        successful_runs = [r for r in self.performance_history if r["success"]]
        if not successful_runs:
            return {"error": "No successful runs"}

        avg_time = sum(r["time"] for r in successful_runs) / len(successful_runs)
        avg_memory = sum(r["memory"] for r in successful_runs) / len(successful_runs)

        return {
            "total_runs": len(self.performance_history),
            "successful_runs": len(successful_runs),
            "success_rate": len(successful_runs) / len(self.performance_history),
            "avg_processing_time": avg_time,
            "avg_memory_usage": avg_memory,
            "current_chunk_size": self.current_chunk_size
        }

    def chunk_sequence(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> Tuple[list, list]:
        """
        Dividir secuencia en chunks.

        Args:
            input_ids: Tensor de input IDs (batch_size, seq_len)
            attention_mask: Máscara de atención opcional

        Returns:
            Tupla de (chunks_input, chunks_attention)
        """
        batch_size, seq_len = input_ids.shape
        chunk_size = self.get_chunk_size(seq_len)

        chunks_input = []
        chunks_attention = []

        for i in range(0, seq_len, chunk_size):
            end_idx = min(i + chunk_size, seq_len)

            chunk_input = input_ids[:, i:end_idx]
            chunks_input.append(chunk_input)

            if attention_mask is not None:
                chunk_attention = attention_mask[:, i:end_idx]
                chunks_attention.append(chunk_attention)
            else:
                chunks_attention.append(None)

        return chunks_input, chunks_attention

    def __repr__(self) -> str:
        stats = self.get_performance_stats()
        return (f"AdaptiveChunking("
                f"current_chunk_size={self.current_chunk_size}, "
                f"model_size={self.model_size_gb:.2f}GB, "
                f"success_rate={stats.get('success_rate', 0):.2f})")


def create_adaptive_chunking(config: Optional[ChunkingConfig] = None) -> AdaptiveChunking:
    """
    Factory function para crear sistema de adaptive chunking.

    Args:
        config: Configuración opcional (usa defaults si None)

    Returns:
        Instancia de AdaptiveChunking
    """
    if config is None:
        config = ChunkingConfig()

    return AdaptiveChunking(config)


# Función de conveniencia para integración con modelo
def setup_adaptive_chunking_for_model(model_config, model_size_gb: float) -> AdaptiveChunking:
    """
    Configurar adaptive chunking para un modelo específico.

    Args:
        model_config: Configuración del modelo
        model_size_gb: Tamaño del modelo en GB

    Returns:
        Sistema de chunking configurado
    """
    chunking_config = ChunkingConfig(
        min_chunk_size=getattr(model_config, 'min_chunk_size', 128),
        max_chunk_size=getattr(model_config, 'max_chunk_size', 4096),
        memory_safety_margin=getattr(model_config, 'memory_safety_margin', 0.8),
        enable_memory_monitoring=getattr(model_config, 'enable_adaptive_chunking', True)
    )

    chunking = AdaptiveChunking(chunking_config)
    chunking.initialize(model_size_gb, getattr(model_config, 'max_context_size', 2048))

    return chunking