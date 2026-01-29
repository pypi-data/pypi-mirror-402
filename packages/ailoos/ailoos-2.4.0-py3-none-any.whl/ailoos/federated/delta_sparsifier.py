"""
Implementación de sparsificación top-k para deltas de pesos en protocolos federados P2P.
Reduce el ancho de banda enviando solo los pesos más cambiados (1% superior) en lugar de deltas completos.
"""

import torch
import numpy as np
import logging
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import pickle
import zlib

logger = logging.getLogger(__name__)


@dataclass
class SparsifiedDelta:
    """Estructura para deltas sparsificados."""
    layer_name: str
    indices: torch.Tensor  # Índices de los pesos sparsificados
    values: torch.Tensor   # Valores sparsificados
    original_shape: torch.Size
    sparsity_ratio: float  # Ratio de sparsificación (0.01 = 1%)
    total_elements: int
    sparsified_elements: int


@dataclass
class SparsificationConfig:
    """Configuración para sparsificación de deltas."""
    k: float = 0.01  # Fracción de pesos a mantener (0.01 = 1%)
    enable_compression: bool = True  # Habilitar compresión adicional
    compression_level: int = 6  # Nivel de compresión zlib
    min_sparsity_ratio: float = 0.005  # Sparsity mínimo (0.5%)
    max_sparsity_ratio: float = 0.1  # Sparsity máximo (10%)


class DeltaSparsifier:
    """
    Implementa sparsificación top-k para deltas de pesos en federated learning.
    Solo envía los pesos más cambiados, reduciendo el ancho de banda en 90-99%.
    """

    def __init__(self, config: Optional[SparsificationConfig] = None):
        self.config = config or SparsificationConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Estadísticas de sparsificación
        self.stats = {
            'total_deltas_processed': 0,
            'total_bandwidth_saved': 0,
            'avg_sparsity_ratio': 0.0,
            'compression_ratios': []
        }

        self.logger.info(f"🗜️ DeltaSparsifier initialized with k={self.config.k} (top {self.config.k*100:.1f}%)")

    def sparsify_deltas(self, current_weights: Dict[str, torch.Tensor],
                       previous_weights: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Calcula deltas y aplica sparsificación top-k.

        Args:
            current_weights: Pesos actuales del modelo
            previous_weights: Pesos anteriores del modelo

        Returns:
            Diccionario con deltas sparsificados por capa
        """
        try:
            sparsified_deltas = {}
            total_original_elements = 0
            total_sparsified_elements = 0

            for layer_name in current_weights.keys():
                if layer_name not in previous_weights:
                    self.logger.warning(f"Layer {layer_name} not found in previous weights, skipping sparsification")
                    continue

                current_layer = current_weights[layer_name]
                previous_layer = previous_weights[layer_name]

                # Calcular delta
                delta = current_layer - previous_layer

                # Aplicar sparsificación top-k
                sparsified_delta = self._sparsify_layer_delta(delta, layer_name)

                if sparsified_delta:
                    sparsified_deltas[layer_name] = sparsified_delta
                    total_original_elements += sparsified_delta.total_elements
                    total_sparsified_elements += sparsified_delta.sparsified_elements

            # Calcular estadísticas globales
            if total_original_elements > 0:
                global_sparsity_ratio = total_sparsified_elements / total_original_elements
                bandwidth_reduction = 1.0 - global_sparsity_ratio

                self.stats['total_deltas_processed'] += 1
                self.stats['avg_sparsity_ratio'] = (
                    (self.stats['avg_sparsity_ratio'] * (self.stats['total_deltas_processed'] - 1)) +
                    global_sparsity_ratio
                ) / self.stats['total_deltas_processed']

                self.logger.info(f"✂️ Sparsified deltas: {total_sparsified_elements}/{total_original_elements} "
                               f"elements ({global_sparsity_ratio:.3f} ratio, "
                               f"{bandwidth_reduction:.1%} bandwidth reduction)")

            return {
                'sparsified_deltas': sparsified_deltas,
                'metadata': {
                    'sparsity_config': {
                        'k': self.config.k,
                        'compression_enabled': self.config.enable_compression
                    },
                    'stats': {
                        'total_original_elements': total_original_elements,
                        'total_sparsified_elements': total_sparsified_elements,
                        'global_sparsity_ratio': global_sparsity_ratio if total_original_elements > 0 else 0.0
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"Error in sparsify_deltas: {e}")
            raise

    def _sparsify_layer_delta(self, delta: torch.Tensor, layer_name: str) -> Optional[SparsifiedDelta]:
        """
        Aplica sparsificación top-k a una capa específica.

        Args:
            delta: Tensor de deltas para la capa
            layer_name: Nombre de la capa

        Returns:
            SparsifiedDelta o None si no se puede sparsificar
        """
        try:
            # Aplanar el tensor para trabajar con 1D
            flat_delta = delta.flatten()
            total_elements = flat_delta.numel()

            # Calcular número de elementos a mantener
            k_elements = max(1, int(total_elements * self.config.k))

            # Asegurar que k_elements esté dentro de límites razonables
            k_elements = min(k_elements, total_elements)
            k_elements = max(k_elements, int(total_elements * self.config.min_sparsity_ratio))

            # Encontrar los índices de los valores absolutos más grandes
            abs_delta = torch.abs(flat_delta)
            _, topk_indices = torch.topk(abs_delta, k_elements, largest=True)

            # Extraer valores sparsificados
            sparsified_values = flat_delta[topk_indices]

            # Crear objeto SparsifiedDelta
            sparsified_delta = SparsifiedDelta(
                layer_name=layer_name,
                indices=topk_indices,
                values=sparsified_values,
                original_shape=delta.shape,
                sparsity_ratio=k_elements / total_elements,
                total_elements=total_elements,
                sparsified_elements=k_elements
            )

            self.logger.debug(f"Layer {layer_name}: sparsified {k_elements}/{total_elements} elements "
                            f"({sparsified_delta.sparsity_ratio:.3f} ratio)")

            return sparsified_delta

        except Exception as e:
            self.logger.error(f"Error sparsifying layer {layer_name}: {e}")
            return None

    def deserialize_deltas(self, sparsified_data: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Reconstruye deltas completos desde datos sparsificados.

        Args:
            sparsified_data: Datos sparsificados retornados por sparsify_deltas

        Returns:
            Deltas reconstruidos por capa
        """
        try:
            reconstructed_deltas = {}

            for layer_name, sparsified_delta in sparsified_data['sparsified_deltas'].items():
                # Reconstruir tensor completo inicializado en cero
                reconstructed = torch.zeros(sparsified_delta.total_elements, dtype=sparsified_delta.values.dtype)

                # Colocar valores sparsificados en sus posiciones originales
                reconstructed[sparsified_delta.indices] = sparsified_delta.values

                # Reshape al tamaño original
                reconstructed = reconstructed.view(sparsified_delta.original_shape)

                reconstructed_deltas[layer_name] = reconstructed

            self.logger.debug(f"Reconstructed {len(reconstructed_deltas)} layer deltas")
            return reconstructed_deltas

        except Exception as e:
            self.logger.error(f"Error deserializing deltas: {e}")
            raise

    def compress_sparsified_data(self, sparsified_data: Dict[str, Any]) -> bytes:
        """
        Comprime datos sparsificados para transmisión eficiente.

        Args:
            sparsified_data: Datos sparsificados

        Returns:
            Datos comprimidos como bytes
        """
        try:
            if not self.config.enable_compression:
                return pickle.dumps(sparsified_data)

            # Serializar y comprimir
            serialized = pickle.dumps(sparsified_data)
            compressed = zlib.compress(serialized, level=self.config.compression_level)

            compression_ratio = len(compressed) / len(serialized) if serialized else 1.0
            self.stats['compression_ratios'].append(compression_ratio)

            self.logger.debug(f"Compressed sparsified data: {compression_ratio:.3f} compression ratio")
            return compressed

        except Exception as e:
            self.logger.error(f"Error compressing sparsified data: {e}")
            raise

    def decompress_sparsified_data(self, compressed_data: bytes) -> Dict[str, Any]:
        """
        Descomprime datos sparsificados.

        Args:
            compressed_data: Datos comprimidos

        Returns:
            Datos sparsificados descomprimidos
        """
        try:
            if not self.config.enable_compression:
                return pickle.loads(compressed_data)

            # Descomprimir y deserializar
            decompressed = zlib.decompress(compressed_data)
            sparsified_data = pickle.loads(decompressed)

            self.logger.debug("Decompressed sparsified data successfully")
            return sparsified_data

        except Exception as e:
            self.logger.error(f"Error decompressing sparsified data: {e}")
            raise

    def get_bandwidth_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de reducción de ancho de banda."""
        return {
            'total_deltas_processed': self.stats['total_deltas_processed'],
            'avg_sparsity_ratio': self.stats['avg_sparsity_ratio'],
            'avg_bandwidth_reduction': 1.0 - self.stats['avg_sparsity_ratio'],
            'compression_stats': {
                'avg_compression_ratio': np.mean(self.stats['compression_ratios']) if self.stats['compression_ratios'] else 1.0,
                'total_compressions': len(self.stats['compression_ratios'])
            }
        }


def create_topk_sparsifier(k: float = 0.01) -> DeltaSparsifier:
    """
    Crea un sparsifier configurado para top-k sparsification.

    Args:
        k: Fracción de pesos a mantener (0.01 = 1%)

    Returns:
        DeltaSparsifier configurado
    """
    config = SparsificationConfig(k=k)
    return DeltaSparsifier(config)


def sparsify_model_update(current_weights: Dict[str, torch.Tensor],
                         previous_weights: Dict[str, torch.Tensor],
                         k: float = 0.01) -> Tuple[bytes, DeltaSparsifier]:
    """
    Función de conveniencia para sparsificar una actualización de modelo completa.

    Args:
        current_weights: Pesos actuales
        previous_weights: Pesos anteriores
        k: Fracción para sparsification

    Returns:
        Tuple de (datos comprimidos, sparsifier usado)
    """
    sparsifier = create_topk_sparsifier(k)
    sparsified_data = sparsifier.sparsify_deltas(current_weights, previous_weights)
    compressed_data = sparsifier.compress_sparsified_data(sparsified_data)

    return compressed_data, sparsifier


def deserialize_model_update(compressed_data: bytes,
                           sparsifier: DeltaSparsifier) -> Dict[str, torch.Tensor]:
    """
    Función de conveniencia para deserializar una actualización sparsificada.

    Args:
        compressed_data: Datos comprimidos
        sparsifier: Sparsifier usado para comprimir

    Returns:
        Deltas reconstruidos
    """
    sparsified_data = sparsifier.decompress_sparsified_data(compressed_data)
    return sparsifier.deserialize_deltas(sparsified_data)