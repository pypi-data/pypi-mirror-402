"""
Sistema de destilación de memoria neural a vectores RAG eficientes.
Convierte estados neurales persistentes a representaciones vectoriales optimizadas para RAG.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import threading

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel
except ImportError:
    torch = None
    nn = None
    F = None
    AutoTokenizer = None
    AutoModel = None

from ...utils.logging import get_logger
from ..memory_manager import get_memory_manager
from ...core.state_manager import get_tensor_state_manager


@dataclass
class DistilledMemory:
    """Memoria destilada en formato vectorial."""
    memory_id: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    importance_score: float
    consolidation_timestamp: datetime
    original_size: int
    compressed_size: int
    compression_ratio: float


@dataclass
class DistillationMetrics:
    """Métricas de destilación."""
    total_memories_processed: int
    total_compression_ratio: float
    average_importance_score: float
    distillation_time_seconds: float
    memory_saved_mb: float
    errors: List[str]


class MemoryDistiller:
    """
    Destilador inteligente que convierte memoria neural a vectores RAG eficientes.
    Utiliza técnicas de compresión, importancia scoring y embeddings semánticos.
    """

    def __init__(self,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 compression_threshold: float = 0.7,
                 importance_threshold: float = 0.3,
                 max_vector_dim: int = 384):
        self.logger = get_logger(__name__)

        self.embedding_model_name = embedding_model
        self.compression_threshold = compression_threshold
        self.importance_threshold = importance_threshold
        self.max_vector_dim = max_vector_dim

        # Modelos y tokenizers
        self.tokenizer = None
        self.embedding_model = None
        self.device = torch.device('cuda' if torch and torch.cuda.is_available() else 'cpu')

        # Dependencias
        self.memory_manager = get_memory_manager()
        self.tensor_state_manager = get_tensor_state_manager()

        # Estado de destilación
        self.distilled_memories: Dict[str, DistilledMemory] = {}
        self.distillation_history: List[DistillationMetrics] = []
        self.lock = threading.RLock()

        # Inicializar modelo de embeddings
        self._initialize_embedding_model()

        self.logger.info("MemoryDistiller inicializado")

    def _initialize_embedding_model(self):
        """Inicializar modelo de embeddings para vectorización semántica."""
        if not torch or not AutoTokenizer or not AutoModel:
            self.logger.warning("Transformers no disponible, usando embeddings dummy")
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.embedding_model_name)
            self.embedding_model = AutoModel.from_pretrained(self.embedding_model_name)
            self.embedding_model.to(self.device)
            self.embedding_model.eval()
            self.logger.info(f"Modelo de embeddings cargado: {self.embedding_model_name}")
        except Exception as e:
            self.logger.error(f"Error cargando modelo de embeddings: {e}")

    async def distill_memory_batch(self,
                                 memory_ids: List[str],
                                 batch_size: int = 10) -> DistillationMetrics:
        """
        Destilar un lote de memorias neurales a vectores RAG.

        Args:
            memory_ids: IDs de las memorias a destilar
            batch_size: Tamaño del lote para procesamiento

        Returns:
            Métricas de la destilación
        """
        start_time = datetime.now()
        metrics = DistillationMetrics(
            total_memories_processed=0,
            total_compression_ratio=0.0,
            average_importance_score=0.0,
            distillation_time_seconds=0.0,
            memory_saved_mb=0.0,
            errors=[]
        )

        try:
            # Procesar en lotes
            for i in range(0, len(memory_ids), batch_size):
                batch_ids = memory_ids[i:i + batch_size]
                batch_metrics = await self._process_distillation_batch(batch_ids)

                metrics.total_memories_processed += batch_metrics.total_memories_processed
                metrics.total_compression_ratio += batch_metrics.total_compression_ratio
                metrics.average_importance_score += batch_metrics.average_importance_score
                metrics.memory_saved_mb += batch_metrics.memory_saved_mb
                metrics.errors.extend(batch_metrics.errors)

            # Calcular promedios
            if metrics.total_memories_processed > 0:
                metrics.total_compression_ratio /= metrics.total_memories_processed
                metrics.average_importance_score /= metrics.total_memories_processed

            metrics.distillation_time_seconds = (datetime.now() - start_time).total_seconds()

            # Guardar en historial
            with self.lock:
                self.distillation_history.append(metrics)
                if len(self.distillation_history) > 50:  # Mantener últimas 50
                    self.distillation_history = self.distillation_history[-50:]

            self.logger.info(f"Destilación completada: {metrics.total_memories_processed} memorias procesadas")

        except Exception as e:
            metrics.errors.append(str(e))
            self.logger.error(f"Error en destilación batch: {e}")

        return metrics

    async def _process_distillation_batch(self, memory_ids: List[str]) -> DistillationMetrics:
        """Procesar un lote específico de memorias."""
        metrics = DistillationMetrics(
            total_memories_processed=0,
            total_compression_ratio=0.0,
            average_importance_score=0.0,
            distillation_time_seconds=0.0,
            memory_saved_mb=0.0,
            errors=[]
        )

        # Recopilar datos de memoria
        memory_data = []
        for memory_id in memory_ids:
            try:
                # Obtener datos de memoria del memory_manager
                memory_info = await self._extract_memory_data(memory_id)
                if memory_info:
                    memory_data.append(memory_info)
            except Exception as e:
                metrics.errors.append(f"Error extrayendo {memory_id}: {e}")

        if not memory_data:
            return metrics

        # Calcular importancia y filtrar
        important_memories = []
        for memory_info in memory_data:
            importance = self._calculate_importance_score(memory_info)
            if importance >= self.importance_threshold:
                memory_info['importance'] = importance
                important_memories.append(memory_info)
            else:
                self.logger.debug(f"Memoria {memory_info['id']} descartada por baja importancia: {importance}")

        # Destilar memorias importantes
        for memory_info in important_memories:
            try:
                distilled = await self._distill_single_memory(memory_info)
                if distilled:
                    with self.lock:
                        self.distilled_memories[distilled.memory_id] = distilled

                    metrics.total_memories_processed += 1
                    metrics.total_compression_ratio += distilled.compression_ratio
                    metrics.average_importance_score += distilled.importance_score
                    metrics.memory_saved_mb += (distilled.original_size - distilled.compressed_size) / (1024 * 1024)

            except Exception as e:
                metrics.errors.append(f"Error destilando {memory_info['id']}: {e}")

        return metrics

    async def _extract_memory_data(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Extraer datos de memoria del sistema de gestión de memoria."""
        try:
            # Intentar obtener del memory_manager
            memory_pages = self.memory_manager.list_pages()
            if memory_id in memory_pages:
                page = memory_pages[memory_id]
                tensor = self.memory_manager.access_tensor(memory_id, 'cpu')
                if tensor is not None:
                    return {
                        'id': memory_id,
                        'tensor': tensor,
                        'metadata': page.metadata if hasattr(page, 'metadata') else {},
                        'last_accessed': page.last_accessed if hasattr(page, 'last_accessed') else datetime.now(),
                        'access_count': page.access_count if hasattr(page, 'access_count') else 1,
                        'size': tensor.numel() * tensor.element_size()
                    }

            # Intentar obtener del tensor_state_manager
            tensor = await self.tensor_state_manager.async_deserialize_tensor(memory_id)
            if tensor is not None:
                return {
                    'id': memory_id,
                    'tensor': tensor,
                    'metadata': {},
                    'last_accessed': datetime.now(),
                    'access_count': 1,
                    'size': tensor.numel() * tensor.element_size()
                }

            return None

        except Exception as e:
            self.logger.warning(f"Error extrayendo datos de memoria {memory_id}: {e}")
            return None

    def _calculate_importance_score(self, memory_info: Dict[str, Any]) -> float:
        """Calcular puntuación de importancia de una memoria."""
        try:
            # Factores de importancia
            recency_weight = 0.3
            frequency_weight = 0.4
            size_weight = 0.2
            semantic_weight = 0.1

            # Recency score (más reciente = más importante)
            days_since_access = (datetime.now() - memory_info['last_accessed']).days
            recency_score = max(0, 1.0 - (days_since_access / 30.0))  # Decae en 30 días

            # Frequency score (más accesos = más importante)
            access_count = memory_info.get('access_count', 1)
            frequency_score = min(1.0, access_count / 10.0)  # Máximo a 10 accesos

            # Size score (tamaño moderado = más importante)
            size_mb = memory_info['size'] / (1024 * 1024)
            if size_mb < 1:
                size_score = 0.8  # Pequeño pero útil
            elif size_mb < 10:
                size_score = 1.0  # Tamaño óptimo
            elif size_mb < 100:
                size_score = 0.6  # Grande pero manejable
            else:
                size_score = 0.2  # Muy grande, menos importante

            # Semantic score (placeholder - requiere análisis de contenido)
            semantic_score = 0.5  # Valor por defecto

            importance = (recency_weight * recency_score +
                         frequency_weight * frequency_score +
                         size_weight * size_score +
                         semantic_weight * semantic_score)

            return importance

        except Exception as e:
            self.logger.warning(f"Error calculando importancia: {e}")
            return 0.1  # Valor bajo por defecto

    async def _distill_single_memory(self, memory_info: Dict[str, Any]) -> Optional[DistilledMemory]:
        """Destilar una memoria individual a vector."""
        try:
            tensor = memory_info['tensor']
            memory_id = memory_info['id']

            # Generar representación vectorial
            vector = await self._tensor_to_vector(tensor, memory_info)

            # Comprimir vector si es necesario
            compressed_vector = self._compress_vector(vector)

            # Calcular métricas
            original_size = memory_info['size']
            compressed_size = len(compressed_vector.tobytes()) if hasattr(compressed_vector, 'tobytes') else len(compressed_vector) * 4
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

            # Crear metadata enriquecida
            metadata = {
                'original_shape': tensor.shape,
                'original_dtype': str(tensor.dtype),
                'compression_method': 'pca' if len(compressed_vector) < len(vector) else 'none',
                'importance_factors': {
                    'recency': (datetime.now() - memory_info['last_accessed']).days,
                    'frequency': memory_info.get('access_count', 1),
                    'size_mb': original_size / (1024 * 1024)
                },
                'distillation_timestamp': datetime.now().isoformat(),
                'source': 'neural_memory'
            }

            distilled = DistilledMemory(
                memory_id=memory_id,
                vector=compressed_vector,
                metadata=metadata,
                importance_score=memory_info['importance'],
                consolidation_timestamp=datetime.now(),
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio
            )

            return distilled

        except Exception as e:
            self.logger.error(f"Error destilando memoria {memory_info['id']}: {e}")
            return None

    async def _tensor_to_vector(self, tensor: torch.Tensor, memory_info: Dict[str, Any]) -> np.ndarray:
        """Convertir tensor a vector representativo."""
        try:
            # Si el tensor es pequeño, aplanar directamente
            if tensor.numel() <= self.max_vector_dim:
                vector = tensor.flatten().cpu().numpy()
                # Pad o truncate a dimensión máxima
                if len(vector) < self.max_vector_dim:
                    vector = np.pad(vector, (0, self.max_vector_dim - len(vector)))
                else:
                    vector = vector[:self.max_vector_dim]
                return vector

            # Para tensores grandes, usar reducción dimensional
            if tensor.dim() >= 3:  # CNN features, etc.
                # Average pooling sobre dimensiones espaciales
                while tensor.dim() > 2:
                    tensor = torch.mean(tensor, dim=-1)
                vector = tensor.flatten().cpu().numpy()
            else:
                # Para matrices grandes, usar SVD para reducción
                if tensor.dim() == 2 and min(tensor.shape) > self.max_vector_dim:
                    # Descomposición SVD
                    U, s, V = torch.svd(tensor)
                    # Tomar componentes principales
                    k = min(self.max_vector_dim, min(tensor.shape))
                    vector = (U[:, :k] @ torch.diag(s[:k])).flatten().cpu().numpy()
                else:
                    vector = tensor.flatten().cpu().numpy()

            # Normalizar a dimensión objetivo
            if len(vector) > self.max_vector_dim:
                # Usar PCA simple para reducción
                vector = self._pca_reduce(vector, self.max_vector_dim)
            elif len(vector) < self.max_vector_dim:
                vector = np.pad(vector, (0, self.max_vector_dim - len(vector)))

            # Normalizar vector
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            return vector

        except Exception as e:
            self.logger.warning(f"Error convirtiendo tensor a vector: {e}")
            # Fallback: hash simple del tensor
            tensor_bytes = tensor.cpu().numpy().tobytes()
            hash_obj = hashlib.sha256(tensor_bytes)
            hash_bytes = hash_obj.digest()
            vector = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32) / 255.0
            return np.pad(vector, (0, self.max_vector_dim - len(vector)))[:self.max_vector_dim]

    def _pca_reduce(self, vector: np.ndarray, target_dim: int) -> np.ndarray:
        """Reducción PCA simple para vectores."""
        try:
            # Implementación PCA simple
            mean = np.mean(vector)
            centered = vector - mean
            cov = np.cov(centered.reshape(-1, 1))
            eigenvalues, eigenvectors = np.linalg.eigh(cov)

            # Tomar componentes principales
            k = min(target_dim, len(eigenvalues))
            top_components = eigenvectors[:, -k:]
            reduced = centered @ top_components
            return reduced.flatten()
        except:
            # Fallback: subsample
            indices = np.linspace(0, len(vector)-1, target_dim, dtype=int)
            return vector[indices]

    def _compress_vector(self, vector: np.ndarray) -> np.ndarray:
        """Comprimir vector si excede threshold de compresión."""
        if len(vector) <= self.max_vector_dim * self.compression_threshold:
            return vector

        # Aplicar compresión PCA
        return self._pca_reduce(vector, int(self.max_vector_dim * self.compression_threshold))

    def get_distilled_memories(self, min_importance: float = 0.0) -> Dict[str, DistilledMemory]:
        """Obtener memorias destiladas filtradas por importancia."""
        with self.lock:
            return {
                k: v for k, v in self.distilled_memories.items()
                if v.importance_score >= min_importance
            }

    def get_distillation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de destilación."""
        with self.lock:
            if not self.distillation_history:
                return {}

            latest = self.distillation_history[-1]
            return {
                'total_processed': sum(m.total_memories_processed for m in self.distillation_history),
                'avg_compression_ratio': np.mean([m.total_compression_ratio for m in self.distillation_history if m.total_memories_processed > 0]),
                'avg_importance_score': np.mean([m.average_importance_score for m in self.distillation_history if m.total_memories_processed > 0]),
                'total_memory_saved_mb': sum(m.memory_saved_mb for m in self.distillation_history),
                'latest_metrics': {
                    'processed': latest.total_memories_processed,
                    'compression_ratio': latest.total_compression_ratio,
                    'importance_score': latest.average_importance_score,
                    'time_seconds': latest.distillation_time_seconds,
                    'memory_saved_mb': latest.memory_saved_mb
                }
            }

    def clear_old_distilled_memories(self, days: int = 30) -> int:
        """Limpiar memorias destiladas antiguas."""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []

        with self.lock:
            for memory_id, distilled in self.distilled_memories.items():
                if distilled.consolidation_timestamp < cutoff:
                    to_remove.append(memory_id)

            for memory_id in to_remove:
                del self.distilled_memories[memory_id]

        self.logger.info(f"Eliminadas {len(to_remove)} memorias destiladas antiguas")
        return len(to_remove)


# Instancia global
_memory_distiller: Optional[MemoryDistiller] = None


def get_memory_distiller(embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2") -> MemoryDistiller:
    """Obtener instancia global del destilador de memoria."""
    global _memory_distiller
    if _memory_distiller is None:
        _memory_distiller = MemoryDistiller(embedding_model)
    return _memory_distiller