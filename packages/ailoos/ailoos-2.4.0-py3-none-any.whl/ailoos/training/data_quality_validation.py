"""
Data Quality Validation para EmpoorioLM - FASE REAL-5
Validación de calidad y diversidad de datos para datasets reales.
Incluye métricas de calidad, diversidad lingüística y detección de anomalías.
"""

import os
import logging
import re
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import hashlib

import torch
from datasets import Dataset
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Descargar recursos de NLTK si no están disponibles
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


@dataclass
class QualityValidationConfig:
    """Configuración de validación de calidad."""
    min_text_length: int = 10
    max_text_length: int = 10000
    min_words_per_sample: int = 5
    max_repetition_ratio: float = 0.3  # Máximo ratio de repetición de palabras
    min_vocab_diversity: float = 0.1  # Mínima diversidad de vocabulario
    max_duplicate_ratio: float = 0.05  # Máximo ratio de duplicados
    language_check: bool = True
    toxicity_check: bool = False  # Requeriría modelo adicional
    sample_size: int = 10000  # Tamaño de muestra para validación
    num_proc: int = mp.cpu_count()


@dataclass
class QualityMetrics:
    """Métricas de calidad del dataset."""
    total_samples: int = 0
    valid_samples: int = 0
    invalid_samples: int = 0
    duplicate_samples: int = 0
    avg_text_length: float = 0.0
    avg_words_per_sample: float = 0.0
    vocab_size: int = 0
    vocab_diversity: float = 0.0
    language_distribution: Dict[str, int] = field(default_factory=dict)
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)


class DataQualityValidator:
    """
    Validador de calidad de datos para datasets de entrenamiento.
    """

    def __init__(self, config: QualityValidationConfig):
        self.config = config
        self.stop_words = set(stopwords.words('english')) if config.language_check else set()

        logger.info("🔍 DataQualityValidator inicializado")

    def validate_dataset(self, dataset: Dataset, sample_size: Optional[int] = None) -> QualityMetrics:
        """
        Validar calidad del dataset completo.
        """
        logger.info("🔍 Validando calidad del dataset...")

        sample_size = sample_size or self.config.sample_size
        sample_size = min(sample_size, len(dataset))

        # Tomar muestra
        indices = np.random.choice(len(dataset), size=sample_size, replace=False)
        sample_dataset = dataset.select(indices)

        # Extraer textos
        texts = []
        for i in range(len(sample_dataset)):
            text = sample_dataset[i].get("text", "")
            if isinstance(text, str):
                texts.append(text)

        logger.info(f"   Muestra: {len(texts)} textos")

        # Calcular métricas
        metrics = self._calculate_quality_metrics(texts)

        # Validar contra thresholds
        self._validate_thresholds(metrics)

        logger.info("✅ Validación completada")
        logger.info(f"   Score de calidad: {metrics.quality_score:.3f}")
        if metrics.issues:
            logger.warning(f"   Issues encontrados: {len(metrics.issues)}")

        return metrics

    def _calculate_quality_metrics(self, texts: List[str]) -> QualityMetrics:
        """Calcular métricas de calidad."""
        metrics = QualityMetrics()
        metrics.total_samples = len(texts)

        # Texto básico
        text_lengths = []
        word_counts = []
        all_words = []

        for text in texts:
            length = len(text.strip())
            text_lengths.append(length)

            words = self._tokenize_words(text)
            word_counts.append(len(words))
            all_words.extend(words)

        # Estadísticas básicas
        metrics.avg_text_length = np.mean(text_lengths) if text_lengths else 0
        metrics.avg_words_per_sample = np.mean(word_counts) if word_counts else 0

        # Vocabulario
        vocab = Counter(all_words)
        metrics.vocab_size = len(vocab)
        metrics.vocab_diversity = self._calculate_vocab_diversity(vocab, len(all_words))

        # Validación individual
        valid_count = 0
        issues = []

        for i, text in enumerate(texts):
            is_valid, text_issues = self._validate_single_text(text)
            if is_valid:
                valid_count += 1
            issues.extend(text_issues)

        metrics.valid_samples = valid_count
        metrics.invalid_samples = len(texts) - valid_count
        metrics.issues = issues[:100]  # Limitar issues reportados

        # Duplicados
        unique_texts = set(texts)
        metrics.duplicate_samples = len(texts) - len(unique_texts)

        # Calcular score de calidad
        metrics.quality_score = self._calculate_quality_score(metrics)

        return metrics

    def _validate_single_text(self, text: str) -> Tuple[bool, List[str]]:
        """Validar un texto individual."""
        issues = []
        is_valid = True

        # Longitud
        if len(text.strip()) < self.config.min_text_length:
            issues.append(f"Texto demasiado corto: {len(text)} chars")
            is_valid = False

        if len(text.strip()) > self.config.max_text_length:
            issues.append(f"Texto demasiado largo: {len(text)} chars")
            is_valid = False

        # Palabras
        words = self._tokenize_words(text)
        if len(words) < self.config.min_words_per_sample:
            issues.append(f"Demasiadas palabras: {len(words)}")
            is_valid = False

        # Repetición
        if words:
            word_counts = Counter(words)
            most_common = word_counts.most_common(1)
            if most_common:
                repetition_ratio = most_common[0][1] / len(words)
                if repetition_ratio > self.config.max_repetition_ratio:
                    issues.append(f"Alta repetición: {repetition_ratio:.2f}")
                    is_valid = False

        # Contenido no textual
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        if alpha_ratio < 0.1:
            issues.append("Contenido mayoritariamente no alfanumérico")
            is_valid = False

        return is_valid, issues

    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenizar texto en palabras."""
        try:
            words = word_tokenize(text.lower())
            # Remover stop words y puntuación
            words = [w for w in words if w.isalnum() and w not in self.stop_words]
            return words
        except:
            # Fallback simple
            return re.findall(r'\b\w+\b', text.lower())

    def _calculate_vocab_diversity(self, vocab: Counter, total_words: int) -> float:
        """Calcular diversidad de vocabulario (entropía normalizada)."""
        if total_words == 0:
            return 0.0

        entropy = 0.0
        for count in vocab.values():
            p = count / total_words
            if p > 0:
                entropy -= p * np.log2(p)

        # Normalizar por log del vocab size
        max_entropy = np.log2(len(vocab)) if vocab else 0
        return entropy / max_entropy if max_entropy > 0 else 0

    def _validate_thresholds(self, metrics: QualityMetrics):
        """Validar métricas contra thresholds."""
        # Ratio de válidos
        valid_ratio = metrics.valid_samples / metrics.total_samples if metrics.total_samples > 0 else 0
        if valid_ratio < 0.8:
            metrics.issues.append(f"Bajo ratio de textos válidos: {valid_ratio:.2f}")

        # Duplicados
        duplicate_ratio = metrics.duplicate_samples / metrics.total_samples if metrics.total_samples > 0 else 0
        if duplicate_ratio > self.config.max_duplicate_ratio:
            metrics.issues.append(f"Alto ratio de duplicados: {duplicate_ratio:.2f}")

        # Diversidad de vocabulario
        if metrics.vocab_diversity < self.config.min_vocab_diversity:
            metrics.issues.append(f"Baja diversidad de vocabulario: {metrics.vocab_diversity:.3f}")

    def _calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """Calcular score de calidad global."""
        if metrics.total_samples == 0:
            return 0.0

        # Componentes del score
        valid_ratio = metrics.valid_samples / metrics.total_samples
        duplicate_ratio = metrics.duplicate_samples / metrics.total_samples
        diversity_score = min(metrics.vocab_diversity / self.config.min_vocab_diversity, 1.0)

        # Penalizar duplicados
        duplicate_penalty = max(0, duplicate_ratio - self.config.max_duplicate_ratio) * 2

        # Score final
        score = (valid_ratio * 0.6 + diversity_score * 0.3 + (1 - duplicate_penalty) * 0.1)
        return max(0.0, min(1.0, score))

    def detect_anomalies(self, dataset: Dataset) -> Dict[str, Any]:
        """Detectar anomalías en el dataset."""
        logger.info("🔍 Detectando anomalías...")

        # Tomar muestra
        sample_size = min(self.config.sample_size, len(dataset))
        indices = np.random.choice(len(dataset), size=sample_size, replace=False)
        sample_dataset = dataset.select(indices)

        texts = [sample_dataset[i]["text"] for i in range(len(sample_dataset))]

        anomalies = {
            "outlier_lengths": self._detect_length_outliers(texts),
            "near_duplicates": self._detect_near_duplicates(texts),
            "suspicious_patterns": self._detect_suspicious_patterns(texts)
        }

        logger.info(f"   Anomalías detectadas: {sum(len(v) for v in anomalies.values())}")

        return anomalies

    def _detect_length_outliers(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Detectar outliers en longitud de textos."""
        lengths = [len(text) for text in texts]
        if not lengths:
            return []

        q1 = np.percentile(lengths, 25)
        q3 = np.percentile(lengths, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for i, length in enumerate(lengths):
            if length < lower_bound or length > upper_bound:
                outliers.append({
                    "index": i,
                    "length": length,
                    "text_preview": texts[i][:100] + "..."
                })

        return outliers[:50]  # Limitar

    def _detect_near_duplicates(self, texts: List[str], threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Detectar textos casi duplicados."""
        if len(texts) < 2:
            return []

        # Vectorizar textos
        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Calcular similitud
            similarity_matrix = cosine_similarity(tfidf_matrix)

            duplicates = []
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    if similarity_matrix[i, j] > threshold:
                        duplicates.append({
                            "text1_index": i,
                            "text2_index": j,
                            "similarity": similarity_matrix[i, j],
                            "text1_preview": texts[i][:100] + "...",
                            "text2_preview": texts[j][:100] + "..."
                        })

            return duplicates[:20]  # Limitar

        except Exception as e:
            logger.warning(f"Error en detección de duplicados: {e}")
            return []

    def _detect_suspicious_patterns(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Detectar patrones sospechosos."""
        patterns = []

        # Patrón de repetición excesiva
        for i, text in enumerate(texts):
            words = self._tokenize_words(text)
            if not words:
                continue

            word_counts = Counter(words)
            for word, count in word_counts.items():
                if count > len(words) * 0.5:  # Más del 50% de las palabras
                    patterns.append({
                        "type": "excessive_repetition",
                        "index": i,
                        "word": word,
                        "count": count,
                        "total_words": len(words),
                        "text_preview": text[:100] + "..."
                    })

        # Patrón de caracteres repetidos
        repeated_chars = re.compile(r'(.)\1{10,}')  # 10+ caracteres repetidos
        for i, text in enumerate(texts):
            if repeated_chars.search(text):
                patterns.append({
                    "type": "repeated_characters",
                    "index": i,
                    "text_preview": text[:100] + "..."
                })

        return patterns[:50]  # Limitar


def create_quality_validator(
    min_text_length: int = 10,
    max_duplicate_ratio: float = 0.05,
    sample_size: int = 10000
) -> DataQualityValidator:
    """
    Factory function para crear validador de calidad.
    """
    config = QualityValidationConfig(
        min_text_length=min_text_length,
        max_duplicate_ratio=max_duplicate_ratio,
        sample_size=sample_size
    )

    return DataQualityValidator(config)


def validate_real_dataset_quality(
    dataset: Dataset,
    output_report: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para validar calidad de dataset real.
    """
    validator = create_quality_validator()

    # Validación de calidad
    metrics = validator.validate_dataset(dataset)

    # Detección de anomalías
    anomalies = validator.detect_anomalies(dataset)

    report = {
        "metrics": {
            "total_samples": metrics.total_samples,
            "valid_samples": metrics.valid_samples,
            "quality_score": metrics.quality_score,
            "vocab_size": metrics.vocab_size,
            "avg_text_length": metrics.avg_text_length
        },
        "issues": metrics.issues,
        "anomalies": anomalies
    }

    if output_report:
        import json
        with open(output_report, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"📋 Reporte guardado en {output_report}")

    return report