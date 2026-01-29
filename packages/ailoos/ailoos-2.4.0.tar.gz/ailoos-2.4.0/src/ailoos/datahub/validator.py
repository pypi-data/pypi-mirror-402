"""
DatasetValidator - Validación de integridad y calidad de datasets
================================================================

Componente para validar la integridad y calidad de datasets descargados,
incluyendo verificación de hashes, análisis estadístico y detección de anomalías.
"""

import hashlib
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ..core.logging import get_logger
from .registry import DatasetRegistry
from .models import DatasetValidation, Dataset

logger = get_logger(__name__)


class ValidationConfig:
    """Configuración para validación de datasets."""
    def __init__(self,
                 enable_integrity_check: bool = True,
                 enable_quality_check: bool = True,
                 max_sample_size: int = 10000,
                 statistical_tests: bool = True,
                 anomaly_detection: bool = True,
                 format_validation: bool = True,
                 compression_check: bool = True):
        self.enable_integrity_check = enable_integrity_check
        self.enable_quality_check = enable_quality_check
        self.max_sample_size = max_sample_size
        self.statistical_tests = statistical_tests
        self.anomaly_detection = anomaly_detection
        self.format_validation = format_validation
        self.compression_check = compression_check


class DatasetValidator:
    """
    Validador de integridad y calidad de datasets.

    Realiza validaciones exhaustivas incluyendo:
    - Verificación de integridad (hashes)
    - Validación de formato
    - Análisis estadístico básico
    - Detección de anomalías y datos corruptos
    """

    def __init__(self,
                 registry: DatasetRegistry,
                 config: Optional[ValidationConfig] = None):
        """
        Inicializar el DatasetValidator.

        Args:
            registry: Registro de datasets para almacenar resultados
            config: Configuración de validación
        """
        self.registry = registry
        self.config = config or ValidationConfig()

        # Estadísticas de validación
        self.validation_stats = {
            'total_validations': 0,
            'integrity_checks': 0,
            'quality_checks': 0,
            'passed_validations': 0,
            'failed_validations': 0
        }

        logger.info("🚀 DatasetValidator initialized")

    async def validate_dataset(self,
                              dataset_id: int,
                              file_path: str,
                              validator_version: str = "1.0.0",
                              validated_by: Optional[str] = None) -> DatasetValidation:
        """
        Validar un dataset completo.

        Args:
            dataset_id: ID del dataset
            file_path: Ruta del archivo a validar
            validator_version: Versión del validador
            validated_by: Sistema/usuario que realiza la validación

        Returns:
            Resultado de la validación
        """
        start_time = datetime.now()

        try:
            # Obtener información del dataset
            dataset = self.registry.get_dataset(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            logger.info(f"🔍 Starting validation of dataset: {dataset.name}")

            # Verificar que el archivo existe
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Dataset file not found: {file_path}")

            # Realizar validaciones
            integrity_result = await self._validate_integrity(file_path, dataset.sha256_hash)
            quality_result = await self._validate_quality(file_path, dataset)

            # Calcular score general
            integrity_score = 1.0 if integrity_result['valid'] else 0.0
            quality_score = quality_result.get('score', 0.0) if quality_result['valid'] else 0.0
            overall_score = (integrity_score + quality_score) / 2

            # Determinar si pasa la validación
            integrity_valid = integrity_result['valid']
            quality_valid = quality_result['valid']
            overall_valid = integrity_valid and quality_valid

            # Crear registro de validación
            validation = DatasetValidation(
                dataset_id=dataset_id,
                is_integrity_valid=integrity_valid,
                is_quality_valid=quality_valid,
                validation_score=overall_score,
                integrity_errors=integrity_result.get('errors', []),
                quality_metrics=quality_result.get('metrics', {}),
                validation_report={
                    'integrity_check': integrity_result,
                    'quality_check': quality_result,
                    'validation_duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
                    'file_size_bytes': Path(file_path).stat().st_size,
                    'validator_config': {
                        'version': validator_version,
                        'integrity_check_enabled': self.config.enable_integrity_check,
                        'quality_check_enabled': self.config.enable_quality_check,
                        'max_sample_size': self.config.max_sample_size
                    }
                },
                validator_version=validator_version,
                validated_by=validated_by
            )

            # Guardar en la base de datos
            self.registry.db.add(validation)
            self.registry.db.commit()
            self.registry.db.refresh(validation)

            # Actualizar estado del dataset si es válido
            if overall_valid and overall_score >= 0.8:  # Threshold del 80%
                self.registry.update_dataset(dataset_id, is_verified=True)

            # Actualizar estadísticas
            self.validation_stats['total_validations'] += 1
            if self.config.enable_integrity_check:
                self.validation_stats['integrity_checks'] += 1
            if self.config.enable_quality_check:
                self.validation_stats['quality_checks'] += 1

            if overall_valid:
                self.validation_stats['passed_validations'] += 1
            else:
                self.validation_stats['failed_validations'] += 1

            logger.info(f"✅ Dataset validation completed: {dataset.name} "
                       f"(integrity: {integrity_valid}, quality: {quality_valid}, score: {overall_score:.2f})")

            return validation

        except Exception as e:
            logger.error(f"❌ Dataset validation failed: {e}")

            # Crear validación de error
            error_validation = DatasetValidation(
                dataset_id=dataset_id,
                is_integrity_valid=False,
                is_quality_valid=False,
                validation_score=0.0,
                integrity_errors=[str(e)],
                quality_metrics={},
                validation_report={
                    'error': str(e),
                    'validation_duration_ms': (datetime.now() - start_time).total_seconds() * 1000
                },
                validator_version=validator_version,
                validated_by=validated_by
            )

            # Intentar guardar el error
            try:
                self.registry.db.add(error_validation)
                self.registry.db.commit()
                self.registry.db.refresh(error_validation)
            except Exception as db_e:
                logger.error(f"❌ Failed to save validation error: {db_e}")

            return error_validation

    async def _validate_integrity(self, file_path: str, expected_hash: str) -> Dict[str, Any]:
        """
        Validar integridad del archivo mediante hash.

        Args:
            file_path: Ruta del archivo
            expected_hash: Hash SHA256 esperado

        Returns:
            Resultado de la validación de integridad
        """
        try:
            # Calcular hash del archivo
            sha256 = hashlib.sha256()
            file_size = 0

            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
                    file_size += len(chunk)

            actual_hash = sha256.hexdigest()

            is_valid = actual_hash == expected_hash
            errors = [] if is_valid else [f"Hash mismatch: expected {expected_hash}, got {actual_hash}"]

            return {
                'valid': is_valid,
                'expected_hash': expected_hash,
                'actual_hash': actual_hash,
                'file_size_bytes': file_size,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"❌ Integrity validation failed: {e}")
            return {
                'valid': False,
                'error': str(e),
                'errors': [str(e)]
            }

    async def _validate_quality(self, file_path: str, dataset: Dataset) -> Dict[str, Any]:
        """
        Validar calidad del dataset basado en su tipo.

        Args:
            file_path: Ruta del archivo
            dataset: Información del dataset

        Returns:
            Resultado de la validación de calidad
        """
        try:
            quality_result = {
                'valid': True,
                'score': 1.0,
                'metrics': {},
                'warnings': [],
                'errors': []
            }

            # Validar basado en el tipo de dataset
            if dataset.dataset_type == 'tabular':
                quality_result = await self._validate_tabular_quality(file_path, dataset)
            elif dataset.dataset_type == 'image':
                quality_result = await self._validate_image_quality(file_path, dataset)
            elif dataset.dataset_type == 'text':
                quality_result = await self._validate_text_quality(file_path, dataset)
            else:
                # Validación genérica
                quality_result = await self._validate_generic_quality(file_path, dataset)

            return quality_result

        except Exception as e:
            logger.error(f"❌ Quality validation failed: {e}")
            return {
                'valid': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }

    async def _validate_tabular_quality(self, file_path: str, dataset: Dataset) -> Dict[str, Any]:
        """Validar calidad de dataset tabular."""
        if not PANDAS_AVAILABLE:
            return {
                'valid': False,
                'score': 0.5,
                'metrics': {},
                'warnings': ['Pandas not available for tabular validation'],
                'errors': []
            }

        try:
            # Leer dataset (limitando tamaño para performance)
            if dataset.format == 'csv':
                df = pd.read_csv(file_path, nrows=self.config.max_sample_size)
            elif dataset.format == 'json':
                df = pd.read_json(file_path)
                if len(df) > self.config.max_sample_size:
                    df = df.head(self.config.max_sample_size)
            else:
                return {
                    'valid': False,
                    'score': 0.0,
                    'metrics': {},
                    'errors': [f"Unsupported tabular format: {dataset.format}"]
                }

            metrics = {}

            # Estadísticas básicas
            metrics['num_rows'] = len(df)
            metrics['num_columns'] = len(df.columns)
            metrics['column_names'] = df.columns.tolist()

            # Verificar valores faltantes
            missing_data = df.isnull().sum()
            metrics['missing_values'] = missing_data.to_dict()
            metrics['missing_percentage'] = (missing_data / len(df) * 100).to_dict()

            # Estadísticas por tipo de columna
            column_stats = {}
            for col in df.columns:
                col_stats = {
                    'dtype': str(df[col].dtype),
                    'unique_values': df[col].nunique(),
                    'null_count': df[col].isnull().sum()
                }

                if df[col].dtype in ['int64', 'float64']:
                    col_stats.update({
                        'mean': df[col].mean(),
                        'std': df[col].std(),
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'quartiles': df[col].quantile([0.25, 0.5, 0.75]).to_dict()
                    })

                    # Detección de outliers usando IQR
                    if self.config.anomaly_detection:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                        col_stats['outliers_iqr'] = outliers

                column_stats[col] = col_stats

            metrics['column_stats'] = column_stats

            # Calcular score de calidad
            score = self._calculate_tabular_score(metrics)

            # Verificar problemas críticos
            errors = []
            warnings = []

            # Columnas con muchos valores faltantes
            high_missing_cols = [col for col, pct in metrics['missing_percentage'].items() if pct > 50]
            if high_missing_cols:
                warnings.append(f"High missing values in columns: {high_missing_cols}")

            # Columnas sin varianza
            no_variance_cols = [col for col, stats in column_stats.items() if stats.get('unique_values', 0) <= 1]
            if no_variance_cols:
                errors.append(f"No variance in columns: {no_variance_cols}")

            return {
                'valid': len(errors) == 0,
                'score': score,
                'metrics': metrics,
                'warnings': warnings,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"❌ Tabular quality validation failed: {e}")
            return {
                'valid': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }

    async def _validate_image_quality(self, file_path: str, dataset: Dataset) -> Dict[str, Any]:
        """Validar calidad de dataset de imágenes."""
        if not PIL_AVAILABLE:
            return {
                'valid': False,
                'score': 0.5,
                'metrics': {},
                'warnings': ['PIL not available for image validation'],
                'errors': []
            }

        try:
            metrics = {}

            if dataset.format in ['png', 'jpg', 'jpeg']:
                # Validar imagen única
                img = Image.open(file_path)
                metrics = self._analyze_image(img)
            else:
                # Para datasets comprimidos, intentar analizar algunas imágenes
                # (simplificado - en producción sería más complejo)
                metrics = {
                    'format': dataset.format,
                    'note': 'Compressed image dataset - detailed analysis requires decompression'
                }

            return {
                'valid': True,
                'score': 0.9,  # Imágenes son más difíciles de validar automáticamente
                'metrics': metrics,
                'warnings': [],
                'errors': []
            }

        except Exception as e:
            logger.error(f"❌ Image quality validation failed: {e}")
            return {
                'valid': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }

    def _analyze_image(self, img: 'Image') -> Dict[str, Any]:
        """Analizar una imagen individual."""
        return {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height,
            'has_alpha': 'A' in img.mode,
            'is_animated': getattr(img, 'is_animated', False)
        }

    async def _validate_text_quality(self, file_path: str, dataset: Dataset) -> Dict[str, Any]:
        """Validar calidad de dataset de texto."""
        try:
            metrics = {}

            with open(file_path, 'r', encoding='utf-8') as f:
                # Leer muestra del texto
                sample_size = min(self.config.max_sample_size, 1000)  # Limitar para texto
                content = f.read(sample_size)

            # Estadísticas básicas de texto
            metrics['total_chars'] = len(content)
            metrics['total_lines'] = content.count('\n') + 1

            # Análisis de caracteres
            char_counts = {}
            for char in content:
                char_counts[char] = char_counts.get(char, 0) + 1

            metrics['unique_chars'] = len(char_counts)
            metrics['most_common_chars'] = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            # Verificar encoding y caracteres especiales
            try:
                content.encode('utf-8')
                metrics['encoding_valid'] = True
            except UnicodeEncodeError:
                metrics['encoding_valid'] = False

            # Detectar posibles problemas
            errors = []
            warnings = []

            if not metrics.get('encoding_valid', True):
                errors.append("Invalid UTF-8 encoding detected")

            if metrics['unique_chars'] < 10:
                warnings.append("Very low character diversity - possible encoding issues")

            return {
                'valid': len(errors) == 0,
                'score': 0.8 if len(warnings) == 0 else 0.6,
                'metrics': metrics,
                'warnings': warnings,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"❌ Text quality validation failed: {e}")
            return {
                'valid': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }

    async def _validate_generic_quality(self, file_path: str, dataset: Dataset) -> Dict[str, Any]:
        """Validación genérica para tipos de datos no específicos."""
        try:
            file_stats = Path(file_path).stat()
            metrics = {
                'file_size_bytes': file_stats.st_size,
                'format': dataset.format,
                'dataset_type': dataset.dataset_type
            }

            # Verificaciones básicas
            errors = []
            warnings = []

            if file_stats.st_size == 0:
                errors.append("File is empty")

            return {
                'valid': len(errors) == 0,
                'score': 0.7,  # Score conservador para validación genérica
                'metrics': metrics,
                'warnings': warnings,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"❌ Generic quality validation failed: {e}")
            return {
                'valid': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }

    def _calculate_tabular_score(self, metrics: Dict[str, Any]) -> float:
        """Calcular score de calidad para datasets tabulares."""
        score = 1.0

        # Penalizar valores faltantes
        total_missing_pct = sum(metrics.get('missing_percentage', {}).values()) / len(metrics.get('missing_percentage', {}))
        if total_missing_pct > 10:
            score -= min(0.3, total_missing_pct / 100 * 3)

        # Penalizar columnas sin varianza
        no_variance_cols = sum(1 for stats in metrics.get('column_stats', {}).values()
                             if stats.get('unique_values', 1) <= 1)
        if no_variance_cols > 0:
            score -= min(0.2, no_variance_cols * 0.1)

        # Penalizar outliers extremos
        if self.config.anomaly_detection:
            total_outliers = sum(stats.get('outliers_iqr', 0)
                               for stats in metrics.get('column_stats', {}).values()
                               if isinstance(stats.get('outliers_iqr'), (int, float)))
            if total_outliers > len(metrics.get('column_stats', {})) * 10:  # Más de 10 outliers por columna
                score -= 0.1

        return max(0.0, score)

    def get_validation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de validación."""
        return dict(self.validation_stats)

    def get_validation_history(self, dataset_id: int, limit: int = 10) -> List[DatasetValidation]:
        """
        Obtener historial de validaciones para un dataset.

        Args:
            dataset_id: ID del dataset
            limit: Número máximo de registros

        Returns:
            Lista de validaciones ordenadas por fecha (más recientes primero)
        """
        try:
            return self.registry.db.query(DatasetValidation).filter(
                DatasetValidation.dataset_id == dataset_id
            ).order_by(DatasetValidation.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"❌ Failed to get validation history: {e}")
            return []