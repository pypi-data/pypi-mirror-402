"""
Módulo de monitoreo de deriva del modelo.
Monitorea cambios en el rendimiento del modelo a lo largo del tiempo.
"""

import torch
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..models.empoorio_lm import EmpoorioLM

logger = logging.getLogger(__name__)


@dataclass
class DriftMetrics:
    """Métricas de deriva del modelo."""

    timestamp: datetime
    perplexity: float
    bleu_score: float
    rouge_score: float
    semantic_similarity: float
    response_length: float
    generation_time: float
    memory_usage: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "perplexity": self.perplexity,
            "bleu_score": self.bleu_score,
            "rouge_score": self.rouge_score,
            "semantic_similarity": self.semantic_similarity,
            "response_length": self.response_length,
            "generation_time": self.generation_time,
            "memory_usage": self.memory_usage
        }


@dataclass
class DriftThresholds:
    """Umbrales para detectar deriva."""

    perplexity_threshold: float = 0.1  # Cambio relativo en perplexity
    bleu_threshold: float = 0.05       # Cambio mínimo en BLEU
    rouge_threshold: float = 0.05      # Cambio mínimo en ROUGE
    similarity_threshold: float = 0.1  # Cambio en similitud semántica
    consecutive_alerts: int = 3        # Alertas consecutivas para confirmar deriva


class ModelDriftMonitor:
    """
    Monitor de deriva del modelo EmpoorioLM.

    Características:
    - Monitoreo continuo de métricas de calidad
    - Detección automática de deriva
    - Alertas configurables
    - Historial de métricas
    - Benchmarks de referencia
    """

    def __init__(
        self,
        model: EmpoorioLM,
        tokenizer,
        reference_dataset: List[str],
        thresholds: Optional[DriftThresholds] = None,
        history_file: str = "./drift_history.json"
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.reference_dataset = reference_dataset
        self.thresholds = thresholds or DriftThresholds()
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        self.metrics_history: List[DriftMetrics] = []
        self.baseline_metrics: Optional[DriftMetrics] = None
        self.consecutive_alerts = 0

        self.executor = ThreadPoolExecutor(max_workers=2)
        self.device = next(model.parameters()).device

        logger.info("📊 ModelDriftMonitor inicializado")
        logger.info(f"   Dataset de referencia: {len(reference_dataset)} muestras")
        logger.info(f"   Archivo de historial: {history_file}")

    async def load_history(self) -> bool:
        """Cargar historial de métricas desde archivo."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.metrics_history = [
                    DriftMetrics(
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        perplexity=item['perplexity'],
                        bleu_score=item['bleu_score'],
                        rouge_score=item['rouge_score'],
                        semantic_similarity=item['semantic_similarity'],
                        response_length=item['response_length'],
                        generation_time=item['generation_time'],
                        memory_usage=item['memory_usage']
                    )
                    for item in data.get('history', [])
                ]

                if data.get('baseline'):
                    baseline_data = data['baseline']
                    self.baseline_metrics = DriftMetrics(
                        timestamp=datetime.fromisoformat(baseline_data['timestamp']),
                        perplexity=baseline_data['perplexity'],
                        bleu_score=baseline_data['bleu_score'],
                        rouge_score=baseline_data['rouge_score'],
                        semantic_similarity=baseline_data['semantic_similarity'],
                        response_length=baseline_data['response_length'],
                        generation_time=baseline_data['generation_time'],
                        memory_usage=baseline_data['memory_usage']
                    )

                logger.info(f"✅ Historial cargado: {len(self.metrics_history)} entradas")
                return True
            else:
                logger.info("📝 No existe historial previo")
                return True

        except Exception as e:
            logger.error(f"❌ Error cargando historial: {e}")
            return False

    async def save_history(self) -> bool:
        """Guardar historial de métricas a archivo."""
        try:
            data = {
                "history": [m.to_dict() for m in self.metrics_history],
                "baseline": self.baseline_metrics.to_dict() if self.baseline_metrics else None,
                "last_updated": datetime.now().isoformat()
            }

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("💾 Historial guardado")
            return True

        except Exception as e:
            logger.error(f"❌ Error guardando historial: {e}")
            return False

    async def establish_baseline(self, num_samples: int = 100) -> bool:
        """Establecer métricas de referencia."""
        logger.info("🎯 Estableciendo baseline de métricas...")

        try:
            # Calcular métricas en subconjunto del dataset
            sample_dataset = self.reference_dataset[:min(num_samples, len(self.reference_dataset))]

            metrics = await self._calculate_metrics(sample_dataset)
            self.baseline_metrics = metrics

            logger.info("✅ Baseline establecido:")
            logger.info(f"   Perplexity: {metrics.perplexity:.3f}")
            logger.info(f"   BLEU: {metrics.bleu_score:.3f}")
            logger.info(f"   ROUGE: {metrics.rouge_score:.3f}")

            await self.save_history()
            return True

        except Exception as e:
            logger.error(f"❌ Error estableciendo baseline: {e}")
            return False

    async def check_drift(self, current_metrics: Optional[DriftMetrics] = None) -> Dict[str, Any]:
        """
        Verificar si hay deriva en el modelo.

        Args:
            current_metrics: Métricas actuales (opcional)

        Returns:
            Resultado del análisis de deriva
        """
        if not self.baseline_metrics:
            logger.warning("⚠️ No hay baseline establecido")
            return {"drift_detected": False, "reason": "no_baseline"}

        # Calcular métricas actuales si no se proporcionan
        if current_metrics is None:
            sample_dataset = self.reference_dataset[:50]  # Muestra pequeña para checks rápidos
            current_metrics = await self._calculate_metrics(sample_dataset)

        # Comparar con baseline
        drift_analysis = self._analyze_drift(current_metrics)

        # Actualizar historial
        self.metrics_history.append(current_metrics)
        await self.save_history()

        # Verificar alertas consecutivas
        if drift_analysis["drift_detected"]:
            self.consecutive_alerts += 1
        else:
            self.consecutive_alerts = 0

        drift_analysis["consecutive_alerts"] = self.consecutive_alerts
        drift_analysis["alert_triggered"] = self.consecutive_alerts >= self.thresholds.consecutive_alerts

        if drift_analysis["alert_triggered"]:
            logger.warning("🚨 ALERTA: Deriva del modelo detectada!")
            logger.warning(f"   Razón: {drift_analysis['reason']}")

        return drift_analysis

    def _analyze_drift(self, current: DriftMetrics) -> Dict[str, Any]:
        """Analizar si hay deriva comparando con baseline."""
        baseline = self.baseline_metrics

        # Calcular cambios relativos
        perplexity_change = abs(current.perplexity - baseline.perplexity) / baseline.perplexity
        bleu_change = abs(current.bleu_score - baseline.bleu_score)
        rouge_change = abs(current.rouge_score - baseline.rouge_score)
        similarity_change = abs(current.semantic_similarity - baseline.semantic_similarity)

        # Verificar umbrales
        drift_reasons = []

        if perplexity_change > self.thresholds.perplexity_threshold:
            drift_reasons.append(f"perplexity_change_{perplexity_change:.3f}")

        if bleu_change > self.thresholds.bleu_threshold:
            drift_reasons.append(f"bleu_change_{bleu_change:.3f}")

        if rouge_change > self.thresholds.rouge_threshold:
            drift_reasons.append(f"rouge_change_{rouge_change:.3f}")

        if similarity_change > self.thresholds.similarity_threshold:
            drift_reasons.append(f"similarity_change_{similarity_change:.3f}")

        return {
            "drift_detected": len(drift_reasons) > 0,
            "reasons": drift_reasons,
            "reason": "; ".join(drift_reasons) if drift_reasons else "none",
            "changes": {
                "perplexity": perplexity_change,
                "bleu": bleu_change,
                "rouge": rouge_change,
                "similarity": similarity_change
            },
            "current_metrics": current.to_dict(),
            "baseline_metrics": baseline.to_dict()
        }

    async def _calculate_metrics(self, dataset: List[str]) -> DriftMetrics:
        """Calcular métricas de calidad en un dataset."""
        start_time = datetime.now()

        # Preparar datos
        perplexities = []
        bleu_scores = []
        rouge_scores = []
        similarities = []
        response_lengths = []
        generation_times = []

        for prompt in dataset:
            try:
                # Generar respuesta
                gen_start = datetime.now()

                inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs["input_ids"],
                        max_new_tokens=50,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id
                    )

                gen_time = (datetime.now() - gen_start).total_seconds()
                generation_times.append(gen_time)

                # Decodificar respuesta
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                response_lengths.append(len(response))

                # Calcular perplexity (simplificada)
                # En producción, calcular en lotes para eficiencia
                perplexity = self._calculate_perplexity(prompt, response)
                perplexities.append(perplexity)

                # Calcular métricas de calidad (simplificadas)
                bleu = self._calculate_bleu(prompt, response)
                rouge = self._calculate_rouge(prompt, response)
                similarity = self._calculate_semantic_similarity(prompt, response)

                bleu_scores.append(bleu)
                rouge_scores.append(rouge)
                similarities.append(similarity)

            except Exception as e:
                logger.warning(f"Error procesando prompt '{prompt[:50]}...': {e}")
                continue

        # Calcular promedios
        avg_perplexity = np.mean(perplexities) if perplexities else 0.0
        avg_bleu = np.mean(bleu_scores) if bleu_scores else 0.0
        avg_rouge = np.mean(rouge_scores) if rouge_scores else 0.0
        avg_similarity = np.mean(similarities) if similarities else 0.0
        avg_length = np.mean(response_lengths) if response_lengths else 0.0
        avg_gen_time = np.mean(generation_times) if generation_times else 0.0

        # Memoria usada
        memory_usage = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

        return DriftMetrics(
            timestamp=datetime.now(),
            perplexity=avg_perplexity,
            bleu_score=avg_bleu,
            rouge_score=avg_rouge,
            semantic_similarity=avg_similarity,
            response_length=avg_length,
            generation_time=avg_gen_time,
            memory_usage=memory_usage
        )

    def _calculate_perplexity(self, prompt: str, response: str) -> float:
        """Calcular perplexity simplificada."""
        # Implementación simplificada - en producción usar cálculo completo
        return np.random.uniform(10, 50)  # Placeholder

    def _calculate_bleu(self, reference: str, candidate: str) -> float:
        """Calcular BLEU score simplificado."""
        # Implementación simplificada
        ref_words = set(reference.lower().split())
        cand_words = set(candidate.lower().split())
        overlap = len(ref_words.intersection(cand_words))
        return overlap / len(ref_words) if ref_words else 0.0

    def _calculate_rouge(self, reference: str, candidate: str) -> float:
        """Calcular ROUGE score simplificado."""
        # Similar a BLEU para simplificación
        return self._calculate_bleu(reference, candidate)

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud semántica simplificada."""
        # Placeholder - en producción usar embeddings
        return np.random.uniform(0.5, 1.0)

    async def get_drift_report(self, days: int = 7) -> Dict[str, Any]:
        """Generar reporte de deriva para los últimos días."""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_date
        ]

        if not recent_metrics:
            return {"error": "No hay métricas recientes"}

        # Análisis de tendencias
        timestamps = [m.timestamp for m in recent_metrics]
        perplexities = [m.perplexity for m in recent_metrics]

        # Tendencia simple
        if len(perplexities) > 1:
            trend = "increasing" if perplexities[-1] > perplexities[0] else "decreasing"
        else:
            trend = "stable"

        return {
            "period_days": days,
            "total_measurements": len(recent_metrics),
            "trend": trend,
            "latest_metrics": recent_metrics[-1].to_dict() if recent_metrics else None,
            "baseline_comparison": self._analyze_drift(recent_metrics[-1]) if recent_metrics else None
        }

    def cleanup_old_history(self, days_to_keep: int = 90):
        """Limpiar historial antiguo."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.metrics_history)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_date
        ]

        removed_count = original_count - len(self.metrics_history)
        if removed_count > 0:
            logger.info(f"🧹 Limpiados {removed_count} registros antiguos")
            asyncio.create_task(self.save_history())


# Funciones de conveniencia
async def create_drift_monitor(
    model: EmpoorioLM,
    tokenizer,
    reference_dataset: List[str],
    history_file: str = "./drift_history.json"
) -> ModelDriftMonitor:
    """
    Crear monitor de deriva con configuración por defecto.

    Args:
        model: Modelo EmpoorioLM
        tokenizer: Tokenizer
        reference_dataset: Dataset de referencia
        history_file: Archivo para historial

    Returns:
        Monitor configurado
    """
    monitor = ModelDriftMonitor(model, tokenizer, reference_dataset, history_file=history_file)

    # Cargar historial existente
    await monitor.load_history()

    # Establecer baseline si no existe
    if not monitor.baseline_metrics:
        await monitor.establish_baseline()

    return monitor


if __name__ == "__main__":
    # Ejemplo de uso
    print("📊 Model Drift Monitor - Demo")
    print("Para usar completamente, integrar con modelo EmpoorioLM cargado")