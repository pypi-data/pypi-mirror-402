"""
TenSEAL Encryptor - Encriptación homomórfica avanzada con TenSEAL
Implementa BFV/BGV schemes para suma y multiplicación homomórfica en federated learning.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import torch

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    ts = None

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TenSEALConfig:
    """Configuración avanzada para TenSEAL."""
    scheme: str = "bfv"  # bfv o ckks
    poly_modulus_degree: int = 8192
    coeff_mod_bit_sizes: List[int] = field(default_factory=lambda: [60, 40, 40, 60])
    scale_bits: int = 40  # Para CKKS
    global_scale: float = 2**40  # Para CKKS
    enable_compression: bool = True
    max_vector_size: int = 4096
    cache_encrypted_vectors: bool = True
    verify_operations: bool = True
    precision_bits: int = 24  # Para CKKS


@dataclass
class TenSEALStats:
    """Estadísticas de operaciones TenSEAL."""
    vectors_encrypted: int = 0
    vectors_decrypted: int = 0
    additions_performed: int = 0
    multiplications_performed: int = 0
    rotations_performed: int = 0
    encryption_time_ms: float = 0.0
    decryption_time_ms: float = 0.0
    operation_time_ms: float = 0.0
    compression_savings: float = 0.0
    errors: int = 0
    cache_hits: int = 0


class TenSEALContextManager:
    """
    Gestor de contexto TenSEAL con configuración optimizada.
    """

    def __init__(self, config: TenSEALConfig):
        if not TENSEAL_AVAILABLE:
            raise ImportError("TenSEAL not available. Install with: pip install tenseal")

        self.config = config
        self.context: Optional[ts.Context] = None
        self.public_key: Optional[ts.PublicKey] = None
        self.secret_key: Optional[ts.SecretKey] = None
        self.relin_keys: Optional[ts.RelinKeys] = None
        self.galois_keys: Optional[ts.GaloisKeys] = None

        self._create_context()

    def _create_context(self):
        """Crear contexto TenSEAL optimizado."""
        if self.config.scheme.lower() == "bfv":
            # BFV scheme para operaciones exactas
            self.context = ts.context(
                ts.SCHEME_TYPE.BFV,
                poly_modulus_degree=self.config.poly_modulus_degree,
                coeff_mod_bit_sizes=self.config.coeff_mod_bit_sizes
            )
        elif self.config.scheme.lower() == "ckks":
            # CKKS scheme para aproximaciones
            self.context = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=self.config.poly_modulus_degree,
                coeff_mod_bit_sizes=self.config.coeff_mod_bit_sizes
            )
            self.context.global_scale = self.config.global_scale
        else:
            raise ValueError(f"Unsupported scheme: {self.config.scheme}")

        # Generar claves
        self.secret_key = self.context.secret_key()
        self.public_key = self.context.public_key()
        self.relin_keys = self.context.relin_keys()
        self.galois_keys = self.context.galois_keys()

        # Configurar contexto para evaluación
        self.context.make_context_public()

        logger.info(f"🔐 TenSEAL context created with {self.config.scheme.upper()} scheme")

    def get_context(self):
        """Obtener contexto TenSEAL."""
        if not TENSEAL_AVAILABLE:
            raise ImportError("TenSEAL not available")
        return self.context

    def get_public_keys(self) -> Dict[str, Any]:
        """Obtener claves públicas para compartir."""
        return {
            'context': self.context.serialize(),
            'public_key': self.public_key.serialize(),
            'relin_keys': self.relin_keys.serialize(),
            'galois_keys': self.galois_keys.serialize()
        }

    def load_public_keys(self, keys_data: Dict[str, Any]):
        """Cargar claves públicas."""
        self.context = ts.context_from(keys_data['context'])
        self.public_key = ts.public_key_from(keys_data['public_key'])
        self.relin_keys = ts.relin_keys_from(keys_data['relin_keys'])
        self.galois_keys = ts.galois_keys_from(keys_data['galois_keys'])


class TenSEALEncryptor:
    """
    Encriptador homomórfico avanzado usando TenSEAL.

    Soporta:
    - BFV: Suma y multiplicación exactas
    - CKKS: Aritmética aproximada de punto flotante
    - Operaciones vectoriales eficientes
    - Rotaciones y otras operaciones avanzadas
    """

    def __init__(self, node_id: str, config: Optional[TenSEALConfig] = None):
        if not TENSEAL_AVAILABLE:
            raise ImportError("TenSEAL not available. Install with: pip install tenseal")

        self.node_id = node_id
        self.config = config or TenSEALConfig()
        self.context_manager = TenSEALContextManager(self.config)
        self.stats = TenSEALStats()

        # Cache para vectores encriptados
        self.encrypted_cache: Dict[str, Any] = {}

        # Estado de evaluación
        self.evaluator_context = None
        self._setup_evaluator()

        logger.info(f"🚀 TenSEALEncryptor initialized for node {node_id} with {self.config.scheme.upper()}")

    def _setup_evaluator(self):
        """Configurar contexto de evaluación."""
        keys = self.context_manager.get_public_keys()
        self.evaluator_context = ts.context_from(keys['context'])
        self.evaluator_context.make_context_public()

    def encrypt_vector(self, vector: Union[np.ndarray, torch.Tensor, List[float]]) -> ts.CKKSVector:
        """
        Encriptar vector usando TenSEAL.

        Args:
            vector: Vector a encriptar

        Returns:
            Vector encriptado
        """
        try:
            start_time = time.time()

            # Convertir a numpy array
            if isinstance(vector, torch.Tensor):
                vector = vector.detach().cpu().numpy()
            elif isinstance(vector, list):
                vector = np.array(vector)

            # Asegurar que no exceda el tamaño máximo
            if len(vector) > self.config.max_vector_size:
                # Dividir en chunks si es necesario
                chunks = []
                for i in range(0, len(vector), self.config.max_vector_size):
                    chunk = vector[i:i + self.config.max_vector_size]
                    # Pad to max size if needed
                    if len(chunk) < self.config.max_vector_size:
                        chunk = np.pad(chunk, (0, self.config.max_vector_size - len(chunk)))
                    chunks.append(chunk)
                vector = chunks[0]  # Por simplicidad, usar solo el primer chunk

            # Encriptar
            if self.config.scheme.lower() == "ckks":
                encrypted_vector = ts.ckks_vector(self.context_manager.context, vector)
            else:  # BFV
                # Convertir a enteros para BFV
                scaled_vector = (vector * (2 ** self.config.precision_bits)).astype(int)
                encrypted_vector = ts.bfv_vector(self.context_manager.context, scaled_vector)

            encryption_time = (time.time() - start_time) * 1000
            self.stats.encryption_time_ms += encryption_time
            self.stats.vectors_encrypted += 1

            # Cache si está habilitado
            if self.config.cache_encrypted_vectors:
                cache_key = f"vec_{hash(vector.tobytes()):x}"
                self.encrypted_cache[cache_key] = encrypted_vector.copy()

            logger.debug(f"🔒 Encrypted vector of size {len(vector)} in {encryption_time:.2f}ms")
            return encrypted_vector

        except Exception as e:
            logger.error(f"❌ Vector encryption failed: {e}")
            self.stats.errors += 1
            raise

    def decrypt_vector(self, encrypted_vector: Union[ts.CKKSVector, ts.BFVVector]) -> np.ndarray:
        """
        Desencriptar vector.

        Args:
            encrypted_vector: Vector encriptado

        Returns:
            Vector desencriptado
        """
        try:
            start_time = time.time()

            # Desencriptar
            decrypted = encrypted_vector.decrypt(secret_key=self.context_manager.secret_key)

            # Convertir de vuelta si es BFV
            if self.config.scheme.lower() == "bfv":
                decrypted = np.array(decrypted, dtype=float) / (2 ** self.config.precision_bits)

            decryption_time = (time.time() - start_time) * 1000
            self.stats.decryption_time_ms += decryption_time
            self.stats.vectors_decrypted += 1

            logger.debug(f"🔓 Decrypted vector in {decryption_time:.2f}ms")
            return np.array(decrypted)

        except Exception as e:
            logger.error(f"❌ Vector decryption failed: {e}")
            self.stats.errors += 1
            raise

    def add_encrypted_vectors(self, vec_a: Union[ts.CKKSVector, ts.BFVVector],
                             vec_b: Union[ts.CKKSVector, ts.BFVVector]) -> Union[ts.CKKSVector, ts.BFVVector]:
        """
        Suma homomórfica de dos vectores encriptados.

        Args:
            vec_a: Primer vector encriptado
            vec_b: Segundo vector encriptado

        Returns:
            Suma encriptada
        """
        try:
            start_time = time.time()

            result = vec_a + vec_b

            operation_time = (time.time() - start_time) * 1000
            self.stats.operation_time_ms += operation_time
            self.stats.additions_performed += 1

            logger.debug(f"➕ Homomorphic addition completed in {operation_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"❌ Homomorphic addition failed: {e}")
            self.stats.errors += 1
            raise

    def multiply_encrypted_vectors(self, vec_a: Union[ts.CKKSVector, ts.BFVVector],
                                  vec_b: Union[ts.CKKSVector, ts.BFVVector]) -> Union[ts.CKKSVector, ts.BFVVector]:
        """
        Multiplicación homomórfica de dos vectores encriptados.

        Args:
            vec_a: Primer vector encriptado
            vec_b: Segundo vector encriptado

        Returns:
            Producto encriptado
        """
        try:
            start_time = time.time()

            result = vec_a * vec_b

            # Relinearización para BFV
            if self.config.scheme.lower() == "bfv":
                result = result.relinearize(relin_keys=self.context_manager.relin_keys)

            operation_time = (time.time() - start_time) * 1000
            self.stats.operation_time_ms += operation_time
            self.stats.multiplications_performed += 1

            logger.debug(f"✖️ Homomorphic multiplication completed in {operation_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"❌ Homomorphic multiplication failed: {e}")
            self.stats.errors += 1
            raise

    def aggregate_encrypted_gradients(self, encrypted_gradients_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agregar gradientes encriptados de múltiples nodos.

        Args:
            encrypted_gradients_list: Lista de gradientes encriptados por nodo

        Returns:
            Gradientes agregados encriptados
        """
        try:
            if not encrypted_gradients_list:
                raise ValueError("Empty gradients list")

            start_time = time.time()

            # Usar el primer conjunto como base
            aggregated = encrypted_gradients_list[0].copy()

            # Agregar los demás
            for gradients in encrypted_gradients_list[1:]:
                for layer_name, enc_vec in gradients.items():
                    if layer_name in aggregated and enc_vec is not None:
                        aggregated[layer_name] = self.add_encrypted_vectors(
                            aggregated[layer_name], enc_vec
                        )

            # Calcular promedio dividiendo por número de nodos
            num_nodes = len(encrypted_gradients_list)
            if num_nodes > 1:
                # Para división, multiplicar por el inverso
                inv_num_nodes = 1.0 / num_nodes
                for layer_name in aggregated:
                    if aggregated[layer_name] is not None:
                        # Crear vector constante con el inverso
                        const_vec = np.full(self.config.max_vector_size, inv_num_nodes)
                        inv_vec = self.encrypt_vector(const_vec)
                        aggregated[layer_name] = self.multiply_encrypted_vectors(
                            aggregated[layer_name], inv_vec
                        )

            operation_time = (time.time() - start_time) * 1000
            self.stats.operation_time_ms += operation_time

            logger.info(f"📊 Aggregated gradients from {num_nodes} nodes in {operation_time:.2f}ms")
            return aggregated

        except Exception as e:
            logger.error(f"❌ Gradient aggregation failed: {e}")
            self.stats.errors += 1
            raise

    def encrypt_model_gradients(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Encriptar gradientes del modelo para federated learning.

        Args:
            gradients: Gradientes por capa

        Returns:
            Gradientes encriptados
        """
        try:
            encrypted_gradients = {}

            for layer_name, grad_tensor in gradients.items():
                if grad_tensor is None:
                    encrypted_gradients[layer_name] = None
                    continue

                # Aplanar gradientes
                grad_flat = grad_tensor.flatten()

                # Encriptar
                encrypted_vector = self.encrypt_vector(grad_flat)
                encrypted_gradients[layer_name] = encrypted_vector

                # Guardar forma original para desencriptación
                encrypted_gradients[f"{layer_name}_shape"] = grad_tensor.shape

            logger.info(f"🔒 Encrypted gradients for {len(gradients)} layers")
            return encrypted_gradients

        except Exception as e:
            logger.error(f"❌ Model gradient encryption failed: {e}")
            raise

    def decrypt_model_gradients(self, encrypted_gradients: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        Desencriptar gradientes del modelo.

        Args:
            encrypted_gradients: Gradientes encriptados

        Returns:
            Gradientes desencriptados
        """
        try:
            decrypted_gradients = {}

            for key, value in encrypted_gradients.items():
                if key.endswith("_shape") or value is None:
                    continue

                layer_name = key
                encrypted_vector = value
                shape_key = f"{layer_name}_shape"

                if shape_key not in encrypted_gradients:
                    logger.warning(f"Shape not found for {layer_name}, skipping")
                    continue

                # Desencriptar
                decrypted_flat = self.decrypt_vector(encrypted_vector)

                # Reconstruir tensor con forma original
                original_shape = encrypted_gradients[shape_key]
                tensor = torch.tensor(decrypted_flat[:np.prod(original_shape)], dtype=torch.float32)
                tensor = tensor.reshape(original_shape)

                decrypted_gradients[layer_name] = tensor

            logger.info(f"🔓 Decrypted gradients for {len(decrypted_gradients)} layers")
            return decrypted_gradients

        except Exception as e:
            logger.error(f"❌ Model gradient decryption failed: {e}")
            raise

    def perform_privacy_preserving_operations(self, operation: str, *args) -> Any:
        """
        Realizar operaciones de preservación de privacidad avanzadas.

        Args:
            operation: Tipo de operación ('dot_product', 'matrix_mult', 'conv2d', etc.)
            *args: Argumentos encriptados

        Returns:
            Resultado encriptado
        """
        try:
            if operation == "dot_product":
                return self._homomorphic_dot_product(*args)
            elif operation == "matrix_mult":
                return self._homomorphic_matrix_mult(*args)
            elif operation == "conv2d":
                return self._homomorphic_conv2d(*args)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            logger.error(f"❌ Privacy-preserving operation failed: {e}")
            raise

    def _homomorphic_dot_product(self, vec_a: ts.CKKSVector, vec_b: ts.CKKSVector) -> ts.CKKSVector:
        """Producto punto homomórfico."""
        # Para CKKS: sum(a_i * b_i)
        product = vec_a * vec_b

        # Suma todos los elementos (esto requiere rotaciones)
        # En una implementación completa, usaríamos rotaciones para sumar eficientemente
        # Por simplicidad, asumimos que los vectores están alineados

        return product.sum()  # TenSEAL tiene método sum()

    def _homomorphic_matrix_mult(self, matrix: ts.CKKSVector, vector: ts.CKKSVector) -> ts.CKKSVector:
        """Multiplicación matriz-vector homomórfica."""
        # Implementación simplificada
        # En producción, esto sería más complejo con rotaciones
        return matrix * vector

    def _homomorphic_conv2d(self, input_enc: ts.CKKSVector, kernel_enc: ts.CKKSVector) -> ts.CKKSVector:
        """Convolución 2D homomórfica."""
        # Implementación simplificada para demostración
        # Convoluciones reales requerirían rotaciones complejas
        return input_enc * kernel_enc

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de operaciones."""
        return {
            'node_id': self.node_id,
            'scheme': self.config.scheme.upper(),
            'poly_modulus_degree': self.config.poly_modulus_degree,
            'stats': {
                'vectors_encrypted': self.stats.vectors_encrypted,
                'vectors_decrypted': self.stats.vectors_decrypted,
                'additions_performed': self.stats.additions_performed,
                'multiplications_performed': self.stats.multiplications_performed,
                'rotations_performed': self.stats.rotations_performed,
                'encryption_time_ms': self.stats.encryption_time_ms,
                'decryption_time_ms': self.stats.decryption_time_ms,
                'operation_time_ms': self.stats.operation_time_ms,
                'compression_savings': self.stats.compression_savings,
                'errors': self.stats.errors,
                'cache_hits': self.stats.cache_hits
            },
            'cache_size': len(self.encrypted_cache),
            'tenseal_available': TENSEAL_AVAILABLE
        }

    def clear_cache(self):
        """Limpiar cache de vectores encriptados."""
        cache_size = len(self.encrypted_cache)
        self.encrypted_cache.clear()
        logger.info(f"🧹 Cleared TenSEAL cache ({cache_size} items)")

    def get_public_context(self) -> Dict[str, Any]:
        """Obtener contexto público para compartir con otros nodos."""
        return self.context_manager.get_public_keys()


# Funciones de conveniencia
def create_tenseal_encryptor(node_id: str, scheme: str = "ckks") -> TenSEALEncryptor:
    """
    Crear encriptador TenSEAL con configuración optimizada.

    Args:
        node_id: ID del nodo
        scheme: Esquema a usar ('bfv' o 'ckks')

    Returns:
        Encriptador configurado
    """
    config = TenSEALConfig(scheme=scheme)

    # Configuración optimizada para federated learning
    if scheme.lower() == "ckks":
        config.coeff_mod_bit_sizes = [60, 40, 40, 60]
        config.global_scale = 2**40
    elif scheme.lower() == "bfv":
        config.coeff_mod_bit_sizes = [60, 40, 60]
        config.poly_modulus_degree = 4096  # Más pequeño para BFV

    return TenSEALEncryptor(node_id, config)


def benchmark_tenseal_operations():
    """Benchmark de operaciones TenSEAL para comparación de rendimiento."""
    if not TENSEAL_AVAILABLE:
        logger.warning("TenSEAL not available for benchmarking")
        return

    logger.info("🏃 Running TenSEAL benchmark...")

    encryptor = create_tenseal_encryptor("benchmark_node", "ckks")

    # Benchmark de encriptación
    test_vector = np.random.randn(1024)

    start_time = time.time()
    encrypted = encryptor.encrypt_vector(test_vector)
    encryption_time = time.time() - start_time

    start_time = time.time()
    decrypted = encryptor.decrypt_vector(encrypted)
    decryption_time = time.time() - start_time

    # Benchmark de operaciones homomórficas
    vec_a = encryptor.encrypt_vector(np.random.randn(1024))
    vec_b = encryptor.encrypt_vector(np.random.randn(1024))

    start_time = time.time()
    sum_result = encryptor.add_encrypted_vectors(vec_a, vec_b)
    addition_time = time.time() - start_time

    start_time = time.time()
    mul_result = encryptor.multiply_encrypted_vectors(vec_a, vec_b)
    multiplication_time = time.time() - start_time

    logger.info("📊 TenSEAL Benchmark Results:")
    logger.info(f"  Encryption (1024 elements): {encryption_time:.4f}s")
    logger.info(f"  Decryption (1024 elements): {decryption_time:.4f}s")
    logger.info(f"  Homomorphic Addition: {addition_time:.4f}s")
    logger.info(f"  Homomorphic Multiplication: {multiplication_time:.4f}s")

    return {
        'encryption_time': encryption_time,
        'decryption_time': decryption_time,
        'addition_time': addition_time,
        'multiplication_time': multiplication_time
    }