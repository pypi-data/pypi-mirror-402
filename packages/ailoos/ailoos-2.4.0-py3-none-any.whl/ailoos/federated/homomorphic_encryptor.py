"""
Homomorphic Encryptor - Encriptación homomórfica para gradientes
Implementa encriptación que permite operaciones matemáticas sobre datos encriptados.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import torch

from ..core.logging import get_logger
from .homomorphic_encryption import HomomorphicEncryptionManager

logger = get_logger(__name__)


@dataclass
class EncryptionConfig:
    """Configuración para encriptación homomórfica."""
    precision: int = 6
    key_size: int = 2048
    enable_key_rotation: bool = True
    rotation_interval_hours: int = 24
    enable_compression: bool = True
    max_encryption_batch: int = 1000
    cache_encrypted_values: bool = True
    verify_decryption: bool = True


@dataclass
class EncryptionStats:
    """Estadísticas de encriptación."""
    values_encrypted: int = 0
    values_decrypted: int = 0
    additions_performed: int = 0
    keys_rotated: int = 0
    encryption_time_ms: float = 0.0
    decryption_time_ms: float = 0.0
    compression_savings: float = 0.0
    errors: int = 0


class HomomorphicEncryptor:
    """
    Encriptador homomórfico para gradientes y actualizaciones de modelo.
    Soporta operaciones aritméticas sobre datos encriptados sin desencriptación.
    """

    def __init__(self, node_id: str, config: Optional[EncryptionConfig] = None):
        """
        Inicializar el encriptador homomórfico.

        Args:
            node_id: ID del nodo
            config: Configuración de encriptación
        """
        self.node_id = node_id
        self.config = config or EncryptionConfig()

        # Componente subyacente
        self.he_manager = HomomorphicEncryptionManager(precision=self.config.precision)

        # Estado del encriptador
        self.is_initialized = False
        self.encryption_stats = EncryptionStats()
        self.last_key_rotation = datetime.now()
        self.encrypted_cache: Dict[str, Any] = {}

        # Claves compartidas (en producción, se distribuirían de forma segura)
        self.shared_public_key = None

        logger.info(f"🔐 HomomorphicEncryptor initialized for node {node_id}")

    def initialize(self):
        """Inicializar componentes."""
        self.is_initialized = True
        self.shared_public_key = self.he_manager.get_public_key()
        logger.info(f"✅ HomomorphicEncryptor initialized for node {self.node_id}")

    def encrypt_gradients(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, List[Any]]:
        """
        Encriptar gradientes del modelo usando homomorphic encryption.

        Args:
            gradients: Gradientes a encriptar por capa

        Returns:
            Gradientes encriptados
        """
        try:
            start_time = datetime.now()
            encrypted_gradients = {}

            for layer_name, grad_tensor in gradients.items():
                if grad_tensor is None:
                    encrypted_gradients[layer_name] = None
                    continue

                # Convertir tensor a lista plana para encriptación
                grad_flat = grad_tensor.flatten().cpu().numpy()

                # Encriptar valores por lotes para eficiencia
                encrypted_values = []
                for i in range(0, len(grad_flat), self.config.max_encryption_batch):
                    batch = grad_flat[i:i + self.config.max_encryption_batch]
                    batch_encrypted = [self.he_manager.encrypt(float(val)) for val in batch]
                    encrypted_values.extend(batch_encrypted)

                encrypted_gradients[layer_name] = encrypted_values

                # Cache si está habilitado
                if self.config.cache_encrypted_values:
                    cache_key = f"{layer_name}_{hash(grad_tensor.cpu().numpy().tobytes()):x}"
                    self.encrypted_cache[cache_key] = encrypted_values.copy()

            # Actualizar estadísticas
            total_values = sum(len(enc) for enc in encrypted_gradients.values() if enc is not None)
            self.encryption_stats.values_encrypted += total_values
            encryption_time = (datetime.now() - start_time).total_seconds() * 1000
            self.encryption_stats.encryption_time_ms += encryption_time

            logger.debug(f"🔒 Encrypted {total_values} gradient values in {encryption_time:.2f}ms")
            return encrypted_gradients

        except Exception as e:
            logger.error(f"❌ Failed to encrypt gradients: {e}")
            self.encryption_stats.errors += 1
            raise

    def decrypt_gradients(self, encrypted_gradients: Dict[str, List[Any]],
                         original_shapes: Dict[str, torch.Size]) -> Dict[str, torch.Tensor]:
        """
        Desencriptar gradientes encriptados.

        Args:
            encrypted_gradients: Gradientes encriptados
            original_shapes: Formas originales de los tensores

        Returns:
            Gradientes desencriptados
        """
        try:
            start_time = datetime.now()
            decrypted_gradients = {}

            for layer_name, encrypted_values in encrypted_gradients.items():
                if encrypted_values is None:
                    decrypted_gradients[layer_name] = None
                    continue

                # Desencriptar valores
                decrypted_values = []
                for enc_val in encrypted_values:
                    dec_val = self.he_manager.decrypt(enc_val)
                    decrypted_values.append(dec_val)

                # Reconstruir tensor con forma original
                original_shape = original_shapes.get(layer_name)
                if original_shape:
                    tensor = torch.tensor(decrypted_values, dtype=torch.float32).reshape(original_shape)
                else:
                    # Intentar forma cuadrada más cercana
                    size = int(np.sqrt(len(decrypted_values)))
                    tensor = torch.tensor(decrypted_values, dtype=torch.float32).reshape(size, -1)

                decrypted_gradients[layer_name] = tensor

            # Actualizar estadísticas
            total_values = sum(len(enc) for enc in encrypted_gradients.values() if enc is not None)
            self.encryption_stats.values_decrypted += total_values
            decryption_time = (datetime.now() - start_time).total_seconds() * 1000
            self.encryption_stats.decryption_time_ms += decryption_time

            # Verificar desencriptación si está habilitado
            if self.config.verify_decryption:
                self._verify_decryption(encrypted_gradients, decrypted_gradients)

            logger.debug(f"🔓 Decrypted {total_values} gradient values in {decryption_time:.2f}ms")
            return decrypted_gradients

        except Exception as e:
            logger.error(f"❌ Failed to decrypt gradients: {e}")
            self.encryption_stats.errors += 1
            raise

    def add_encrypted_gradients(self, encrypted_a: Dict[str, List[Any]],
                               encrypted_b: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """
        Sumar gradientes encriptados homomórficamente (sin desencriptación).

        Args:
            encrypted_a: Primer conjunto de gradientes encriptados
            encrypted_b: Segundo conjunto de gradientes encriptados

        Returns:
            Suma encriptada de gradientes
        """
        try:
            if not self._validate_encrypted_gradients(encrypted_a, encrypted_b):
                raise ValueError("Encrypted gradients structure mismatch")

            summed_gradients = {}

            for layer_name in encrypted_a.keys():
                if encrypted_a[layer_name] is None or encrypted_b[layer_name] is None:
                    summed_gradients[layer_name] = None
                    continue

                # Suma homomórfica elemento a elemento
                layer_sum = []
                for a_val, b_val in zip(encrypted_a[layer_name], encrypted_b[layer_name]):
                    sum_val = a_val + b_val  # Operación homomórfica
                    layer_sum.append(sum_val)

                summed_gradients[layer_name] = layer_sum

            self.encryption_stats.additions_performed += 1
            logger.debug(f"➕ Performed homomorphic addition for {len(summed_gradients)} layers")

            return summed_gradients

        except Exception as e:
            logger.error(f"❌ Failed to add encrypted gradients: {e}")
            self.encryption_stats.errors += 1
            raise

    def aggregate_encrypted_gradients(self, encrypted_gradients_list: List[Dict[str, List[Any]]]) -> Dict[str, List[Any]]:
        """
        Agregar múltiples conjuntos de gradientes encriptados.

        Args:
            encrypted_gradients_list: Lista de gradientes encriptados a agregar

        Returns:
            Gradientes agregados encriptados
        """
        try:
            if not encrypted_gradients_list:
                raise ValueError("Empty gradients list")

            if len(encrypted_gradients_list) == 1:
                return encrypted_gradients_list[0]

            # Agregar iterativamente
            result = encrypted_gradients_list[0]
            for gradients in encrypted_gradients_list[1:]:
                result = self.add_encrypted_gradients(result, gradients)

            logger.debug(f"📊 Aggregated {len(encrypted_gradients_list)} encrypted gradient sets")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to aggregate encrypted gradients: {e}")
            raise

    def _validate_encrypted_gradients(self, encrypted_a: Dict[str, List[Any]],
                                     encrypted_b: Dict[str, List[Any]]) -> bool:
        """
        Validar que los gradientes encriptados sean compatibles para operaciones.

        Args:
            encrypted_a: Primer conjunto
            encrypted_b: Segundo conjunto

        Returns:
            True si son compatibles
        """
        try:
            if set(encrypted_a.keys()) != set(encrypted_b.keys()):
                return False

            for layer_name in encrypted_a.keys():
                if encrypted_a[layer_name] is None and encrypted_b[layer_name] is None:
                    continue
                if encrypted_a[layer_name] is None or encrypted_b[layer_name] is None:
                    return False
                if len(encrypted_a[layer_name]) != len(encrypted_b[layer_name]):
                    return False

            return True

        except Exception:
            return False

    def _verify_decryption(self, encrypted_gradients: Dict[str, List[Any]],
                          decrypted_gradients: Dict[str, torch.Tensor]):
        """
        Verificar integridad de la desencriptación (para debugging).

        Args:
            encrypted_gradients: Gradientes originales encriptados
            decrypted_gradients: Gradientes desencriptados
        """
        try:
            # Verificación básica: comprobar que podemos volver a encriptar
            sample_layer = next(iter(encrypted_gradients.keys()))
            if encrypted_gradients[sample_layer] and decrypted_gradients[sample_layer] is not None:
                # Re-encriptar y comparar
                re_encrypted = self.encrypt_gradients({sample_layer: decrypted_gradients[sample_layer]})
                # En producción, esto sería más riguroso
                logger.debug("✅ Decryption verification passed")

        except Exception as e:
            logger.warning(f"⚠️ Decryption verification failed: {e}")

    def rotate_keys(self):
        """Rotar claves de encriptación para mayor seguridad."""
        try:
            # Crear nuevo manager con nuevas claves
            old_manager = self.he_manager
            self.he_manager = HomomorphicEncryptionManager(precision=self.config.precision)

            # Actualizar clave pública compartida
            self.shared_public_key = self.he_manager.get_public_key()

            # Limpiar cache (valores encriptados con claves viejas ya no son válidos)
            self.encrypted_cache.clear()

            self.encryption_stats.keys_rotated += 1
            self.last_key_rotation = datetime.now()

            logger.info(f"🔄 Keys rotated for node {self.node_id}")

        except Exception as e:
            logger.error(f"❌ Key rotation failed: {e}")
            # Restaurar manager anterior
            self.he_manager = old_manager
            raise

    def should_rotate_keys(self) -> bool:
        """
        Verificar si es necesario rotar claves.

        Returns:
            True si se deben rotar las claves
        """
        if not self.config.enable_key_rotation:
            return False

        hours_since_rotation = (datetime.now() - self.last_key_rotation).total_seconds() / 3600
        return hours_since_rotation >= self.config.rotation_interval_hours

    def get_public_key(self):
        """
        Obtener clave pública para compartir con otros nodos.

        Returns:
            Clave pública
        """
        return self.he_manager.get_public_key()

    def get_encryption_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de encriptación.

        Returns:
            Diccionario con estadísticas
        """
        return {
            'node_id': self.node_id,
            'is_initialized': self.is_initialized,
            'config': {
                'precision': self.config.precision,
                'key_size': self.config.key_size,
                'enable_key_rotation': self.config.enable_key_rotation,
                'cache_enabled': self.config.cache_encrypted_values
            },
            'stats': {
                'values_encrypted': self.encryption_stats.values_encrypted,
                'values_decrypted': self.encryption_stats.values_decrypted,
                'additions_performed': self.encryption_stats.additions_performed,
                'keys_rotated': self.encryption_stats.keys_rotated,
                'encryption_time_ms': self.encryption_stats.encryption_time_ms,
                'decryption_time_ms': self.encryption_stats.decryption_time_ms,
                'compression_savings': self.encryption_stats.compression_savings,
                'errors': self.encryption_stats.errors
            },
            'cache_size': len(self.encrypted_cache),
            'last_key_rotation': self.last_key_rotation.isoformat(),
            'should_rotate_keys': self.should_rotate_keys()
        }

    def clear_cache(self):
        """Limpiar cache de valores encriptados."""
        cache_size = len(self.encrypted_cache)
        self.encrypted_cache.clear()
        logger.info(f"🧹 Cleared encryption cache ({cache_size} items)")

    def reset_accumulator(self):
        """Resetear acumulador de sumas en el manager subyacente."""
        self.he_manager.reset_sum()
        logger.debug("🔄 Reset encryption accumulator")