"""
Secure Data Preprocessor - Preprocesamiento que mantiene privacidad
Implementa técnicas de privacidad diferencial y sanitización de datos.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import torch
import torch.nn as nn

from ..core.logging import get_logger
from .differential_privacy import DifferentialPrivacyEngine

logger = get_logger(__name__)


@dataclass
class PreprocessingConfig:
    """Configuración para preprocesamiento seguro."""
    enable_differential_privacy: bool = True
    dp_epsilon: float = 1.0
    dp_delta: float = 1e-5
    max_grad_norm: float = 1.0
    dp_threshold: float = 0.1
    enable_data_sanitization: bool = True
    enable_feature_scaling: bool = True
    enable_outlier_removal: bool = False
    outlier_threshold: float = 3.0
    enable_data_augmentation: bool = False
    augmentation_probability: float = 0.1
    batch_normalization: bool = True


@dataclass
class PreprocessingStats:
    """Estadísticas de preprocesamiento."""
    samples_processed: int = 0
    outliers_removed: int = 0
    dp_applied: int = 0
    features_scaled: int = 0
    augmentation_applied: int = 0
    processing_time_ms: float = 0.0
    errors: int = 0


class SecureDataPreprocessor:
    """
    Preprocesador de datos que mantiene privacidad usando técnicas de DP
    y sanitización de datos sensibles.
    """

    def __init__(self, node_id: str, config: Optional[PreprocessingConfig] = None):
        """
        Inicializar el preprocesador seguro.

        Args:
            node_id: ID del nodo
            config: Configuración de preprocesamiento
        """
        self.node_id = node_id
        self.config = config or PreprocessingConfig()

        # Componentes de privacidad
        self.dp_engine = DifferentialPrivacyEngine(
            epsilon=self.config.dp_epsilon,
            delta=self.config.dp_delta,
            max_grad_norm=self.config.max_grad_norm,
            threshold=self.config.dp_threshold
        ) if self.config.enable_differential_privacy else None

        # Estado del preprocesador
        self.is_initialized = False
        self.feature_stats: Dict[str, Dict[str, float]] = {}
        self.preprocessing_stats = PreprocessingStats()

        # Componentes de normalización
        self.batch_norm_layers: Dict[str, nn.BatchNorm1d] = {}

        logger.info(f"🔒 SecureDataPreprocessor initialized for node {node_id}")

    def initialize(self):
        """Inicializar componentes."""
        self.is_initialized = True
        logger.info(f"✅ SecureDataPreprocessor initialized for node {self.node_id}")

    def preprocess_batch(self, batch_data: torch.Tensor,
                        targets: Optional[torch.Tensor] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Tuple[torch.Tensor, Optional[torch.Tensor], Dict[str, Any]]:
        """
        Preprocesar un lote de datos manteniendo privacidad.

        Args:
            batch_data: Datos del lote (batch_size, features)
            targets: Etiquetas/objectivos (opcional)
            metadata: Metadatos adicionales

        Returns:
            Tuple de (datos_preprocesados, targets_procesados, metadata_actualizada)
        """
        try:
            start_time = datetime.now()
            metadata = metadata or {}

            # 1. Sanitización de datos
            if self.config.enable_data_sanitization:
                batch_data, targets = self._sanitize_data(batch_data, targets)

            # 2. Eliminación de outliers
            if self.config.enable_outlier_removal:
                batch_data, targets = self._remove_outliers(batch_data, targets)

            # 3. Escalado de características
            if self.config.enable_feature_scaling:
                batch_data = self._scale_features(batch_data)

            # 4. Normalización por lotes
            if self.config.batch_normalization:
                batch_data = self._apply_batch_normalization(batch_data)

            # 5. Aumento de datos (si está habilitado)
            if self.config.enable_data_augmentation and targets is not None:
                batch_data, targets = self._apply_data_augmentation(batch_data, targets)

            # 6. Aplicar privacidad diferencial a gradientes (simulado para datos)
            if self.config.enable_differential_privacy and self.dp_engine:
                batch_data = self._apply_differential_privacy_to_data(batch_data)

            # Actualizar estadísticas
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.preprocessing_stats.samples_processed += batch_data.size(0)
            self.preprocessing_stats.processing_time_ms += processing_time

            # Actualizar metadata
            metadata.update({
                'preprocessing_applied': True,
                'dp_applied': self.config.enable_differential_privacy,
                'batch_size': batch_data.size(0),
                'feature_dim': batch_data.size(-1),
                'processing_time_ms': processing_time
            })

            logger.debug(f"🔄 Preprocessed batch of {batch_data.size(0)} samples in {processing_time:.2f}ms")
            return batch_data, targets, metadata

        except Exception as e:
            logger.error(f"❌ Failed to preprocess batch: {e}")
            self.preprocessing_stats.errors += 1
            # Retornar datos originales en caso de error
            return batch_data, targets, metadata

    def _sanitize_data(self, data: torch.Tensor,
                      targets: Optional[torch.Tensor]) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Sanitizar datos removiendo valores inválidos.

        Args:
            data: Datos a sanitizar
            targets: Targets correspondientes

        Returns:
            Datos sanitizados
        """
        try:
            # Remover NaN e infinitos
            valid_mask = torch.isfinite(data).all(dim=-1)

            if not valid_mask.any():
                logger.warning("⚠️ All data contains invalid values, keeping original")
                return data, targets

            sanitized_data = data[valid_mask]

            if targets is not None:
                sanitized_targets = targets[valid_mask]
            else:
                sanitized_targets = None

            removed_count = data.size(0) - sanitized_data.size(0)
            if removed_count > 0:
                logger.debug(f"🧹 Sanitized {removed_count} invalid samples")

            return sanitized_data, sanitized_targets

        except Exception as e:
            logger.warning(f"⚠️ Data sanitization failed: {e}")
            return data, targets

    def _remove_outliers(self, data: torch.Tensor,
                        targets: Optional[torch.Tensor]) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Remover outliers usando z-score.

        Args:
            data: Datos de entrada
            targets: Targets correspondientes

        Returns:
            Datos sin outliers
        """
        try:
            # Calcular z-score por característica
            mean = data.mean(dim=0, keepdim=True)
            std = data.std(dim=0, keepdim=True) + 1e-8  # Evitar división por cero

            z_scores = torch.abs((data - mean) / std)
            max_z_scores = z_scores.max(dim=-1)[0]

            # Mantener muestras dentro del threshold
            valid_mask = max_z_scores <= self.config.outlier_threshold

            if not valid_mask.any():
                logger.warning("⚠️ All samples are outliers, keeping original")
                return data, targets

            filtered_data = data[valid_mask]

            if targets is not None:
                filtered_targets = targets[valid_mask]
            else:
                filtered_targets = None

            removed_count = data.size(0) - filtered_data.size(0)
            self.preprocessing_stats.outliers_removed += removed_count

            if removed_count > 0:
                logger.debug(f"🚮 Removed {removed_count} outlier samples")

            return filtered_data, filtered_targets

        except Exception as e:
            logger.warning(f"⚠️ Outlier removal failed: {e}")
            return data, targets

    def _scale_features(self, data: torch.Tensor) -> torch.Tensor:
        """
        Escalar características usando normalización min-max o z-score.

        Args:
            data: Datos a escalar

        Returns:
            Datos escalados
        """
        try:
            # Usar z-score normalization
            mean = data.mean(dim=0, keepdim=True)
            std = data.std(dim=0, keepdim=True) + 1e-8

            scaled_data = (data - mean) / std

            self.preprocessing_stats.features_scaled += data.size(0)
            logger.debug(f"📏 Scaled features for {data.size(0)} samples")

            return scaled_data

        except Exception as e:
            logger.warning(f"⚠️ Feature scaling failed: {e}")
            return data

    def _apply_batch_normalization(self, data: torch.Tensor) -> torch.Tensor:
        """
        Aplicar normalización por lotes.

        Args:
            data: Datos de entrada

        Returns:
            Datos normalizados
        """
        try:
            # Crear o usar capa de batch norm
            feature_dim = data.size(-1)
            layer_key = f"batch_norm_{feature_dim}"

            if layer_key not in self.batch_norm_layers:
                self.batch_norm_layers[layer_key] = nn.BatchNorm1d(feature_dim)

            batch_norm = self.batch_norm_layers[layer_key]

            # Aplicar normalización
            # Reordenar para (batch, features) si es necesario
            original_shape = data.shape
            if len(original_shape) > 2:
                data_flat = data.view(-1, feature_dim)
                normalized = batch_norm(data_flat)
                normalized = normalized.view(original_shape)
            else:
                normalized = batch_norm(data)

            return normalized

        except Exception as e:
            logger.warning(f"⚠️ Batch normalization failed: {e}")
            return data

    def _apply_data_augmentation(self, data: torch.Tensor,
                               targets: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Aplicar aumento de datos básico.

        Args:
            data: Datos de entrada
            targets: Targets correspondientes

        Returns:
            Datos aumentados
        """
        try:
            if torch.rand(1).item() > self.config.augmentation_probability:
                return data, targets

            # Aumento simple: añadir ruido gaussiano pequeño
            noise = torch.normal(0, 0.01, data.shape, device=data.device)
            augmented_data = data + noise

            self.preprocessing_stats.augmentation_applied += 1
            logger.debug("🎨 Applied data augmentation")

            return augmented_data, targets

        except Exception as e:
            logger.warning(f"⚠️ Data augmentation failed: {e}")
            return data, targets

    def _apply_differential_privacy_to_data(self, data: torch.Tensor) -> torch.Tensor:
        """
        Aplicar privacidad diferencial a los datos (simulado).

        Args:
            data: Datos de entrada

        Returns:
            Datos con DP aplicado
        """
        try:
            if not self.dp_engine:
                return data

            # Para datos, aplicamos DP de manera diferente que para gradientes
            # Aquí simulamos añadiendo ruido calibrado a las características sensibles

            # Calcular sensibilidad (basada en el rango de datos)
            data_range = data.max() - data.min()
            sensitivity = float(data_range.item()) if data_range > 0 else 1.0

            # Generar ruido para cada característica
            noise = self.dp_engine.generate_noise(data.shape, sensitivity)

            # Aplicar ruido
            dp_data = data + noise

            self.preprocessing_stats.dp_applied += 1
            logger.debug("🔒 Applied differential privacy to data")

            return dp_data

        except Exception as e:
            logger.warning(f"⚠️ DP application to data failed: {e}")
            return data

    def preprocess_gradients(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Preprocesar gradientes con privacidad diferencial.

        Args:
            gradients: Gradientes del modelo

        Returns:
            Gradientes procesados
        """
        try:
            if self.dp_engine:
                dp_gradients = self.dp_engine.apply_differential_privacy(gradients)
                logger.debug("🔒 Applied DP to gradients")
                return dp_gradients
            else:
                return gradients

        except Exception as e:
            logger.warning(f"⚠️ Gradient preprocessing failed: {e}")
            return gradients

    def update_feature_stats(self, data: torch.Tensor):
        """
        Actualizar estadísticas de características para normalización futura.

        Args:
            data: Datos para calcular estadísticas
        """
        try:
            # Calcular estadísticas básicas
            self.feature_stats.update({
                'mean': data.mean(dim=0).tolist(),
                'std': data.std(dim=0).tolist(),
                'min': data.min(dim=0)[0].tolist(),
                'max': data.max(dim=0)[0].tolist(),
                'samples_seen': data.size(0)
            })

            logger.debug("📊 Updated feature statistics")

        except Exception as e:
            logger.warning(f"⚠️ Failed to update feature stats: {e}")

    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de preprocesamiento.

        Returns:
            Diccionario con estadísticas
        """
        dp_status = None
        if self.dp_engine:
            dp_status = self.dp_engine.get_privacy_status()

        return {
            'node_id': self.node_id,
            'is_initialized': self.is_initialized,
            'config': {
                'enable_dp': self.config.enable_differential_privacy,
                'enable_sanitization': self.config.enable_data_sanitization,
                'enable_scaling': self.config.enable_feature_scaling,
                'enable_outlier_removal': self.config.enable_outlier_removal,
                'batch_normalization': self.config.batch_normalization
            },
            'stats': {
                'samples_processed': self.preprocessing_stats.samples_processed,
                'outliers_removed': self.preprocessing_stats.outliers_removed,
                'dp_applied': self.preprocessing_stats.dp_applied,
                'features_scaled': self.preprocessing_stats.features_scaled,
                'augmentation_applied': self.preprocessing_stats.augmentation_applied,
                'processing_time_ms': self.preprocessing_stats.processing_time_ms,
                'errors': self.preprocessing_stats.errors
            },
            'feature_stats': self.feature_stats.copy(),
            'differential_privacy': dp_status
        }

    def reset_stats(self):
        """Resetear estadísticas."""
        self.preprocessing_stats = PreprocessingStats()
        logger.info("🔄 Preprocessing stats reset")

    def is_privacy_budget_available(self) -> bool:
        """
        Verificar si hay presupuesto de privacidad disponible.

        Returns:
            True si hay presupuesto suficiente
        """
        if self.dp_engine:
            return self.dp_engine.is_privacy_budget_available()
        return True