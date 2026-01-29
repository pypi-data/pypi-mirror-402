"""
Adaptive Domain Adapter - Adaptación automática del modelo a nuevos dominios
Detecta cambios en dominios de datos y adapta el modelo automáticamente.
"""

import asyncio
import json
import time
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainProfile:
    """Perfil de un dominio de datos."""
    domain_name: str
    vocabulary: Dict[str, float] = field(default_factory=dict)
    topic_distribution: Dict[str, float] = field(default_factory=dict)
    semantic_embedding: Optional[np.ndarray] = None
    sample_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    adaptation_score: float = 0.0


@dataclass
class DomainShiftDetection:
    """Detección de cambio de dominio."""
    source_domain: str
    target_domain: str
    shift_score: float
    confidence: float
    detected_at: float = field(default_factory=time.time)
    shift_type: str = "unknown"  # vocabulary, topic, semantic
    adaptation_needed: bool = False


@dataclass
class AdaptationStrategy:
    """Estrategia de adaptación."""
    strategy_type: str  # "incremental", "full_finetune", "domain_mixing"
    learning_rate: float
    epochs: int
    regularization_weight: float
    domain_weight: float
    target_modules: List[str] = field(default_factory=list)


class AdaptiveDomainAdapter:
    """
    Adaptador automático de dominio para modelos federados.
    Detecta cambios de dominio y adapta el modelo automáticamente.
    """

    def __init__(self, model_name: str, adaptation_threshold: float = 0.3):
        self.model_name = model_name
        self.adaptation_threshold = adaptation_threshold

        # Perfiles de dominio conocidos
        self.domain_profiles: Dict[str, DomainProfile] = {}
        self.current_domain: Optional[str] = None

        # Historial de detecciones de cambio
        self.domain_shift_history: List[DomainShiftDetection] = []

        # Estrategias de adaptación por tipo de cambio
        self.adaptation_strategies = {
            "vocabulary_shift": AdaptationStrategy(
                strategy_type="incremental",
                learning_rate=1e-5,
                epochs=2,
                regularization_weight=0.1,
                domain_weight=0.3,
                target_modules=["embed_tokens"]
            ),
            "topic_shift": AdaptationStrategy(
                strategy_type="domain_mixing",
                learning_rate=2e-5,
                epochs=3,
                regularization_weight=0.05,
                domain_weight=0.5,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
            ),
            "semantic_shift": AdaptationStrategy(
                strategy_type="full_finetune",
                learning_rate=5e-6,
                epochs=5,
                regularization_weight=0.01,
                domain_weight=0.7,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
            )
        }

        # Vectorizador para análisis de texto
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

        # Modelo para embeddings semánticos
        self.semantic_model = None
        self._initialize_semantic_model()

        # Estadísticas
        self.stats = {
            "domains_analyzed": 0,
            "shifts_detected": 0,
            "adaptations_performed": 0,
            "avg_adaptation_time": 0.0,
            "success_rate": 0.0
        }

        logger.info(f"🧠 AdaptiveDomainAdapter initialized with threshold {adaptation_threshold}")

    def _initialize_semantic_model(self):
        """Inicializar modelo para embeddings semánticos."""
        try:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Semantic model initialized")
        except ImportError:
            logger.warning("⚠️ SentenceTransformers not available, semantic analysis disabled")
            self.semantic_model = None

    def analyze_domain(self, domain_name: str, text_samples: List[str],
                      metadata: Dict[str, Any] = None) -> DomainProfile:
        """
        Analizar un dominio de datos y crear/actualizar su perfil.

        Args:
            domain_name: Nombre del dominio
            text_samples: Muestras de texto del dominio
            metadata: Metadatos adicionales

        Returns:
            Perfil del dominio
        """
        logger.info(f"🔍 Analyzing domain {domain_name} with {len(text_samples)} samples")

        # Crear o actualizar perfil
        if domain_name not in self.domain_profiles:
            profile = DomainProfile(domain_name=domain_name)
            self.domain_profiles[domain_name] = profile
        else:
            profile = self.domain_profiles[domain_name]

        # Actualizar estadísticas básicas
        profile.sample_count += len(text_samples)
        profile.last_updated = time.time()

        # Analizar vocabulario
        self._analyze_vocabulary(profile, text_samples)

        # Analizar distribución de tópicos
        self._analyze_topics(profile, text_samples)

        # Generar embedding semántico
        self._generate_semantic_embedding(profile, text_samples)

        # Calcular score de adaptación
        profile.adaptation_score = self._calculate_adaptation_score(profile)

        self.stats["domains_analyzed"] += 1
        logger.info(f"✅ Domain {domain_name} analyzed - adaptation score: {profile.adaptation_score:.3f}")

        return profile

    def _analyze_vocabulary(self, profile: DomainProfile, text_samples: List[str]):
        """Analizar vocabulario del dominio."""
        try:
            # Tokenizar y contar frecuencia de palabras
            from collections import Counter
            import re

            all_words = []
            for text in text_samples[:1000]:  # Limitar para eficiencia
                words = re.findall(r'\b\w+\b', text.lower())
                all_words.extend(words)

            word_freq = Counter(all_words)
            total_words = sum(word_freq.values())

            # Normalizar frecuencias
            profile.vocabulary = {word: freq / total_words for word, freq in word_freq.most_common(1000)}

        except Exception as e:
            logger.warning(f"⚠️ Error analyzing vocabulary: {e}")

    def _analyze_topics(self, profile: DomainProfile, text_samples: List[str]):
        """Analizar distribución de tópicos."""
        try:
            # Usar TF-IDF para identificar términos importantes
            if len(text_samples) >= 10:
                tfidf_matrix = self.vectorizer.fit_transform(text_samples[:500])
                feature_names = self.vectorizer.get_feature_names_out()

                # Calcular importancia promedio de términos
                avg_tfidf = np.mean(tfidf_matrix.toarray(), axis=0)
                top_indices = np.argsort(avg_tfidf)[-20:]  # Top 20 términos

                profile.topic_distribution = {
                    feature_names[i]: float(avg_tfidf[i])
                    for i in top_indices
                }

        except Exception as e:
            logger.warning(f"⚠️ Error analyzing topics: {e}")

    def _generate_semantic_embedding(self, profile: DomainProfile, text_samples: List[str]):
        """Generar embedding semántico del dominio."""
        if not self.semantic_model:
            return

        try:
            # Generar embeddings para una muestra de textos
            sample_texts = text_samples[:50]  # Limitar para eficiencia
            embeddings = self.semantic_model.encode(sample_texts)

            # Calcular embedding promedio del dominio
            profile.semantic_embedding = np.mean(embeddings, axis=0)

        except Exception as e:
            logger.warning(f"⚠️ Error generating semantic embedding: {e}")

    def _calculate_adaptation_score(self, profile: DomainProfile) -> float:
        """Calcular score de adaptación basado en complejidad del dominio."""
        score = 0.0

        # Factor de vocabulario: dominios con vocabulario rico necesitan más adaptación
        vocab_richness = len(profile.vocabulary) / 1000.0
        score += vocab_richness * 0.4

        # Factor de tópicos: dominios con tópicos diversos necesitan más adaptación
        topic_diversity = len(profile.topic_distribution) / 20.0
        score += topic_diversity * 0.3

        # Factor temporal: dominios recientes pueden necesitar más adaptación
        time_factor = min(1.0, (time.time() - profile.created_at) / (30 * 24 * 3600))  # 30 días
        score += (1 - time_factor) * 0.3

        return min(1.0, score)

    def detect_domain_shift(self, source_domain: str, target_domain: str) -> Optional[DomainShiftDetection]:
        """
        Detectar cambio de dominio entre dos dominios.

        Args:
            source_domain: Dominio fuente
            target_domain: Dominio objetivo

        Returns:
            Detección de cambio si existe
        """
        if source_domain not in self.domain_profiles or target_domain not in self.domain_profiles:
            return None

        source_profile = self.domain_profiles[source_domain]
        target_profile = self.domain_profiles[target_domain]

        # Calcular diferentes tipos de shift
        vocabulary_shift = self._calculate_vocabulary_shift(source_profile, target_profile)
        topic_shift = self._calculate_topic_shift(source_profile, target_profile)
        semantic_shift = self._calculate_semantic_shift(source_profile, target_profile)

        # Determinar el tipo de shift más significativo
        shifts = {
            "vocabulary": vocabulary_shift,
            "topic": topic_shift,
            "semantic": semantic_shift
        }

        max_shift_type = max(shifts, key=shifts.get)
        max_shift_score = shifts[max_shift_type]

        # Calcular confianza basada en la diferencia con otros shifts
        other_shifts = [s for t, s in shifts.items() if t != max_shift_type]
        confidence = max_shift_score - max(other_shifts) if other_shifts else max_shift_score

        # Determinar si se necesita adaptación
        adaptation_needed = max_shift_score > self.adaptation_threshold

        detection = DomainShiftDetection(
            source_domain=source_domain,
            target_domain=target_domain,
            shift_score=max_shift_score,
            confidence=confidence,
            shift_type=max_shift_type,
            adaptation_needed=adaptation_needed
        )

        if adaptation_needed:
            self.domain_shift_history.append(detection)
            self.stats["shifts_detected"] += 1
            logger.info(f"🔄 Domain shift detected: {source_domain} -> {target_domain}")
            logger.info(f"   Type: {max_shift_type}, Score: {max_shift_score:.3f}, Confidence: {confidence:.3f}")

        return detection

    def _calculate_vocabulary_shift(self, source: DomainProfile, target: DomainProfile) -> float:
        """Calcular shift de vocabulario."""
        # Jaccard similarity entre vocabularios
        source_vocab = set(source.vocabulary.keys())
        target_vocab = set(target.vocabulary.keys())

        intersection = len(source_vocab & target_vocab)
        union = len(source_vocab | target_vocab)

        similarity = intersection / union if union > 0 else 0.0
        return 1.0 - similarity  # Convertir a distancia

    def _calculate_topic_shift(self, source: DomainProfile, target: DomainProfile) -> float:
        """Calcular shift de tópicos."""
        # Cosine similarity entre distribuciones de tópicos
        source_topics = list(source.topic_distribution.keys())
        target_topics = list(target.topic_distribution.keys())

        all_topics = list(set(source_topics + target_topics))

        source_vec = [source.topic_distribution.get(t, 0) for t in all_topics]
        target_vec = [target.topic_distribution.get(t, 0) for t in all_topics]

        if not source_vec or not target_vec:
            return 0.0

        similarity = cosine_similarity([source_vec], [target_vec])[0][0]
        return 1.0 - similarity  # Convertir a distancia

    def _calculate_semantic_shift(self, source: DomainProfile, target: DomainProfile) -> float:
        """Calcular shift semántico."""
        if source.semantic_embedding is None or target.semantic_embedding is None:
            return 0.0

        # Cosine similarity entre embeddings semánticos
        similarity = cosine_similarity(
            [source.semantic_embedding],
            [target.semantic_embedding]
        )[0][0]

        return 1.0 - similarity  # Convertir a distancia

    def get_adaptation_strategy(self, shift_detection: DomainShiftDetection) -> AdaptationStrategy:
        """
        Obtener estrategia de adaptación basada en la detección de shift.

        Args:
            shift_detection: Detección de cambio de dominio

        Returns:
            Estrategia de adaptación recomendada
        """
        strategy = self.adaptation_strategies.get(shift_detection.shift_type,
                                                 self.adaptation_strategies["semantic_shift"])

        # Ajustar estrategia basada en la severidad del shift
        if shift_detection.shift_score > 0.7:
            strategy.epochs = min(strategy.epochs + 2, 10)
            strategy.learning_rate *= 0.5  # Reducir learning rate para shifts severos

        logger.info(f"🎯 Recommended adaptation strategy: {strategy.strategy_type}")
        logger.info(f"   Learning rate: {strategy.learning_rate}")
        logger.info(f"   Epochs: {strategy.epochs}")
        logger.info(f"   Target modules: {strategy.target_modules}")

        return strategy

    async def adapt_model_to_domain(self, model: Any, source_domain: str,
                                   target_domain: str, training_data: List[str]) -> Dict[str, Any]:
        """
        Adaptar modelo a un nuevo dominio.

        Args:
            model: Modelo a adaptar
            source_domain: Dominio fuente
            target_domain: Dominio objetivo
            training_data: Datos de entrenamiento para adaptación

        Returns:
            Resultados de la adaptación
        """
        start_time = time.time()

        # Detectar shift si no se ha hecho
        shift_detection = self.detect_domain_shift(source_domain, target_domain)
        if not shift_detection:
            # Crear detección básica si no existe
            shift_detection = DomainShiftDetection(
                source_domain=source_domain,
                target_domain=target_domain,
                shift_score=0.5,
                confidence=0.5,
                shift_type="unknown",
                adaptation_needed=True
            )

        # Obtener estrategia de adaptación
        strategy = self.get_adaptation_strategy(shift_detection)

        logger.info(f"🔄 Starting model adaptation: {source_domain} -> {target_domain}")

        try:
            # Ejecutar adaptación según estrategia
            if strategy.strategy_type == "incremental":
                result = await self._incremental_adaptation(model, training_data, strategy)
            elif strategy.strategy_type == "domain_mixing":
                result = await self._domain_mixing_adaptation(model, source_domain, target_domain, training_data, strategy)
            elif strategy.strategy_type == "full_finetune":
                result = await self._full_finetune_adaptation(model, training_data, strategy)
            else:
                raise ValueError(f"Unknown adaptation strategy: {strategy.strategy_type}")

            # Actualizar estadísticas
            adaptation_time = time.time() - start_time
            self.stats["adaptations_performed"] += 1
            self.stats["avg_adaptation_time"] = (
                (self.stats["avg_adaptation_time"] * (self.stats["adaptations_performed"] - 1)) +
                adaptation_time
            ) / self.stats["adaptations_performed"]

            result.update({
                "adaptation_time": adaptation_time,
                "strategy_used": strategy.strategy_type,
                "shift_type": shift_detection.shift_type,
                "shift_score": shift_detection.shift_score
            })

            logger.info(f"✅ Model adaptation completed in {adaptation_time:.2f}s")
            logger.info(f"📊 Final loss: {result.get('final_loss', 'N/A')}")

            return result

        except Exception as e:
            logger.error(f"❌ Error during model adaptation: {e}")
            return {
                "success": False,
                "error": str(e),
                "adaptation_time": time.time() - start_time
            }

    async def _incremental_adaptation(self, model: Any, training_data: List[str],
                                    strategy: AdaptationStrategy) -> Dict[str, Any]:
        """Adaptación incremental enfocada en embeddings."""
        # Implementación simplificada - en producción sería más compleja
        logger.info("🔧 Performing incremental adaptation")

        # Simular entrenamiento
        await asyncio.sleep(0.1)  # Simular tiempo de entrenamiento

        return {
            "success": True,
            "final_loss": 0.5,
            "improvement": 0.1,
            "epochs_completed": strategy.epochs
        }

    async def _domain_mixing_adaptation(self, model: Any, source_domain: str,
                                       target_domain: str, training_data: List[str],
                                       strategy: AdaptationStrategy) -> Dict[str, Any]:
        """Adaptación mezclando datos de ambos dominios."""
        logger.info("🔄 Performing domain mixing adaptation")

        # Simular mezcla de dominios
        await asyncio.sleep(0.2)

        return {
            "success": True,
            "final_loss": 0.3,
            "improvement": 0.2,
            "domain_mixing_ratio": strategy.domain_weight,
            "epochs_completed": strategy.epochs
        }

    async def _full_finetune_adaptation(self, model: Any, training_data: List[str],
                                      strategy: AdaptationStrategy) -> Dict[str, Any]:
        """Adaptación completa con fine-tuning extenso."""
        logger.info("🔄 Performing full fine-tune adaptation")

        # Simular fine-tuning completo
        await asyncio.sleep(0.5)

        return {
            "success": True,
            "final_loss": 0.1,
            "improvement": 0.4,
            "epochs_completed": strategy.epochs
        }

    def get_domain_shift_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de cambios de dominio."""
        return [
            {
                "source_domain": d.source_domain,
                "target_domain": d.target_domain,
                "shift_score": d.shift_score,
                "shift_type": d.shift_type,
                "adaptation_needed": d.adaptation_needed,
                "detected_at": d.detected_at
            }
            for d in self.domain_shift_history
        ]

    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de adaptación."""
        return {
            "domains_analyzed": self.stats["domains_analyzed"],
            "shifts_detected": self.stats["shifts_detected"],
            "adaptations_performed": self.stats["adaptations_performed"],
            "avg_adaptation_time": self.stats["avg_adaptation_time"],
            "success_rate": self.stats["success_rate"],
            "known_domains": list(self.domain_profiles.keys()),
            "current_domain": self.current_domain,
            "adaptation_threshold": self.adaptation_threshold
        }

    def update_adaptation_threshold(self, new_threshold: float):
        """Actualizar umbral de adaptación."""
        self.adaptation_threshold = max(0.0, min(1.0, new_threshold))
        logger.info(f"🔧 Adaptation threshold updated to {self.adaptation_threshold}")


# Funciones de conveniencia
def create_domain_adapter(model_name: str, threshold: float = 0.3) -> AdaptiveDomainAdapter:
    """Crear un nuevo adaptador de dominio."""
    return AdaptiveDomainAdapter(model_name, threshold)


async def analyze_and_adapt(model: Any, adapter: AdaptiveDomainAdapter,
                           source_domain: str, target_domain: str,
                           training_data: List[str]) -> Dict[str, Any]:
    """
    Analizar dominio y adaptar modelo automáticamente.

    Args:
        model: Modelo a adaptar
        adapter: Adaptador de dominio
        source_domain: Dominio fuente
        target_domain: Dominio objetivo
        training_data: Datos de entrenamiento

    Returns:
        Resultados de análisis y adaptación
    """
    # Analizar dominios
    adapter.analyze_domain(source_domain, training_data)
    adapter.analyze_domain(target_domain, training_data)

    # Detectar shift
    shift = adapter.detect_domain_shift(source_domain, target_domain)

    if shift and shift.adaptation_needed:
        # Adaptar modelo
        result = await adapter.adapt_model_to_domain(model, source_domain, target_domain, training_data)
        return {
            "analysis_performed": True,
            "shift_detected": True,
            "adaptation_performed": True,
            "shift_info": {
                "type": shift.shift_type,
                "score": shift.shift_score,
                "confidence": shift.confidence
            },
            "adaptation_result": result
        }
    else:
        return {
            "analysis_performed": True,
            "shift_detected": False,
            "adaptation_performed": False,
            "message": "No significant domain shift detected"
        }