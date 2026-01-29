import torch
import numpy as np
import logging
import zlib
import pickle
from typing import Dict, Any, Tuple

class WeightCompressor:
    """
    Clase para compresión de pesos de modelos federados.
    Implementa quantization a INT8, sparsification top-k, entropy coding y empaquetado.
    """

    def __init__(self, k: float = 0.1):
        """
        Inicializa el compresor de pesos.

        Args:
            k: Fracción de pesos a mantener en sparsification (0.1 = 10%)
        """
        self.k = k
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _quantize_to_int8(self, weights: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Quantiza los pesos a INT8.

        Args:
            weights: Tensor de pesos

        Returns:
            Tuple de (pesos quantizados, metadatos para dequantization)
        """
        try:
            # Calcular escala y offset para mapear a [-128, 127]
            min_val = weights.min().item()
            max_val = weights.max().item()
            scale = (max_val - min_val) / 255.0 if max_val != min_val else 1.0
            offset = min_val

            # Quantizar
            quantized = torch.round((weights - offset) / scale).clamp(-128, 127).to(torch.int8)

            metadata = {
                'scale': scale,
                'offset': offset,
                'original_dtype': weights.dtype,
                'original_shape': weights.shape
            }

            self.logger.info(f"Quantized weights to INT8, shape: {weights.shape}")
            return quantized, metadata

        except Exception as e:
            self.logger.error(f"Error in quantization: {e}")
            raise

    def _sparsify_topk(self, weights: torch.Tensor, k: float) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Aplica sparsification top-k manteniendo los k% de valores absolutos más grandes.

        Args:
            weights: Tensor de pesos
            k: Fracción a mantener

        Returns:
            Tuple de (pesos sparsificados, máscara de sparsificación)
        """
        try:
            # Calcular número de elementos a mantener
            total_elements = weights.numel()
            keep_elements = int(total_elements * k)

            # Encontrar índices de los top-k valores absolutos
            abs_weights = torch.abs(weights.view(-1))
            _, topk_indices = torch.topk(abs_weights, keep_elements, largest=True)

            # Crear máscara
            mask = torch.zeros_like(weights.view(-1), dtype=torch.bool)
            mask[topk_indices] = True
            mask = mask.view(weights.shape)

            # Aplicar sparsificación
            sparse_weights = weights * mask.to(weights.dtype)

            self.logger.info(f"Applied top-k sparsification with k={k}, kept {keep_elements}/{total_elements} elements")
            return sparse_weights, mask

        except Exception as e:
            self.logger.error(f"Error in sparsification: {e}")
            raise

    def _entropy_encode(self, data: bytes) -> bytes:
        """
        Aplica entropy coding usando zlib.

        Args:
            data: Datos en bytes

        Returns:
            Datos comprimidos
        """
        try:
            compressed = zlib.compress(data)
            compression_ratio = len(compressed) / len(data) if data else 1.0
            self.logger.info(f"Entropy encoded data, compression ratio: {compression_ratio:.3f}")
            return compressed

        except Exception as e:
            self.logger.error(f"Error in entropy encoding: {e}")
            raise

    def _create_compressed_package(self, sparse_weights: torch.Tensor, mask: torch.Tensor,
                                   quant_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea el paquete comprimido con metadatos.

        Args:
            sparse_weights: Pesos sparsificados y quantizados
            mask: Máscara de sparsificación
            quant_metadata: Metadatos de quantization

        Returns:
            Paquete comprimido
        """
        try:
            # Serializar datos
            sparse_bytes = pickle.dumps(sparse_weights.numpy())
            mask_bytes = pickle.dumps(mask.numpy())

            # Comprimir
            compressed_sparse = self._entropy_encode(sparse_bytes)
            compressed_mask = self._entropy_encode(mask_bytes)

            package = {
                'compressed_sparse_weights': compressed_sparse,
                'compressed_mask': compressed_mask,
                'quant_metadata': quant_metadata,
                'k': self.k,
                'version': '1.0'
            }

            self.logger.info("Created compressed package")
            return package

        except Exception as e:
            self.logger.error(f"Error creating compressed package: {e}")
            raise

    def compress_weights(self, weights: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Comprime los pesos aplicando quantization, sparsification, entropy coding y empaquetado.

        Args:
            weights: Diccionario de pesos del modelo

        Returns:
            Paquete comprimido
        """
        try:
            compressed_layers = {}

            for layer_name, layer_weights in weights.items():
                self.logger.info(f"Compressing layer: {layer_name}")

                # 1. Sparsification top-k
                sparse_weights, mask = self._sparsify_topk(layer_weights, self.k)

                # 2. Quantization a INT8
                quantized_weights, quant_metadata = self._quantize_to_int8(sparse_weights)

                # 3. Crear paquete comprimido para esta capa
                layer_package = self._create_compressed_package(quantized_weights, mask, quant_metadata)
                compressed_layers[layer_name] = layer_package

            # Paquete final
            final_package = {
                'compressed_layers': compressed_layers,
                'original_keys': list(weights.keys()),
                'compression_type': 'INT8_TOPK_ENTROPY'
            }

            self.logger.info(f"Compressed {len(weights)} layers successfully")
            return final_package

        except Exception as e:
            self.logger.error(f"Error in weight compression: {e}")
            raise

    def decompress_weights(self, compressed_package: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Descomprime los pesos reconstruyendo el proceso inverso.

        Args:
            compressed_package: Paquete comprimido

        Returns:
            Pesos originales reconstruidos
        """
        try:
            decompressed_weights = {}

            for layer_name, layer_package in compressed_package['compressed_layers'].items():
                self.logger.info(f"Decompressing layer: {layer_name}")

                # 1. Descomprimir datos
                sparse_bytes = zlib.decompress(layer_package['compressed_sparse_weights'])
                mask_bytes = zlib.decompress(layer_package['compressed_mask'])

                # 2. Deserializar
                sparse_weights_np = pickle.loads(sparse_bytes)
                mask_np = pickle.loads(mask_bytes)

                sparse_weights = torch.from_numpy(sparse_weights_np).to(torch.int8)
                mask = torch.from_numpy(mask_np).to(torch.bool)

                # 3. Dequantizar
                quant_metadata = layer_package['quant_metadata']
                scale = quant_metadata['scale']
                offset = quant_metadata['offset']
                original_dtype = quant_metadata['original_dtype']
                original_shape = quant_metadata['original_shape']

                dequantized = (sparse_weights.to(torch.float32) * scale) + offset
                dequantized = dequantized.to(original_dtype).view(original_shape)

                # 4. Aplicar máscara inversa (aunque ya está sparsificado, esto asegura consistencia)
                reconstructed = dequantized * mask.to(dequantized.dtype)

                decompressed_weights[layer_name] = reconstructed

            self.logger.info(f"Decompressed {len(decompressed_weights)} layers successfully")
            return decompressed_weights

        except Exception as e:
            self.logger.error(f"Error in weight decompression: {e}")
            raise