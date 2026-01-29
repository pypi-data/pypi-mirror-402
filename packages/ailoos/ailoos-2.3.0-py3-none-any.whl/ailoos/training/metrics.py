#!/usr/bin/env python3
"""
Sistema completo de métricas para evaluación del entrenamiento de EmpoorioLM.

Este módulo proporciona un sistema modular y extensible de métricas para evaluar
el progreso del entrenamiento de modelos de lenguaje. Incluye métricas estándar
como loss, perplexity y accuracy, así como métricas avanzadas de generación
de texto como BLEU y ROUGE.

Características principales:
- Arquitectura modular con clases base Metric
- Métricas específicas para modelos de lenguaje
- Evaluador unificado (MetricsEvaluator)
- Integración con sistemas de entrenamiento existentes
- Soporte para métricas personalizadas
- Evaluación automática en datasets de validación

Uso básico:
    from src.ailoos.training.metrics import MetricsEvaluator, create_default_metrics_config

    # Crear configuración
    config = create_default_metrics_config()

    # Crear evaluador
    evaluator = MetricsEvaluator(config)

    # Actualizar con datos de batch
    evaluator.update_batch(
        loss=0.5,
        logits=logits,
        targets=targets,
        num_tokens=100,
        lr=0.001
    )

    # Obtener resultados
    results = evaluator.compute_all()
    for name, result in results.items():
        print(f"{name}: {result.value:.4f} {result.unit}")

Integración con TrainingProgressTracker:
    tracker = TrainingProgressTracker()
    tracker.set_metrics_evaluator(evaluator)

    # El tracker automáticamente actualizará las métricas avanzadas
    await tracker.update_batch_progress(batch_idx, batch_time, loss, accuracy, lr,
                                       logits=logits, targets=targets, num_tokens=num_tokens)
"""

import torch
import torch.nn as nn
import math
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
import statistics
from collections import defaultdict

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    from rouge_score import rouge_scorer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("Advertencia: nltk y rouge_score no disponibles. Algunas métricas de generación estarán deshabilitadas.")

from ..utils.logging import AiloosLogger


@dataclass
class MetricResult:
    """Resultado de una métrica individual."""
    name: str
    value: float
    unit: str = ""
    higher_is_better: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class Metric(ABC):
    """Clase base para todas las métricas."""

    def __init__(self, name: str, unit: str = "", higher_is_better: bool = False):
        self.name = name
        self.unit = unit
        self.higher_is_better = higher_is_better
        self.reset()

    @abstractmethod
    def update(self, *args, **kwargs) -> None:
        """Actualizar la métrica con nuevos datos."""
        pass

    @abstractmethod
    def compute(self) -> float:
        """Calcular el valor final de la métrica."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reiniciar el estado de la métrica."""
        pass

    def get_result(self) -> MetricResult:
        """Obtener resultado formateado."""
        return MetricResult(
            name=self.name,
            value=self.compute(),
            unit=self.unit,
            higher_is_better=self.higher_is_better
        )


class LossMetric(Metric):
    """Métrica de loss (pérdida)."""

    def __init__(self):
        super().__init__("loss", "value", higher_is_better=False)
        self.total_loss = 0.0
        self.num_samples = 0

    def update(self, loss: Union[float, torch.Tensor], batch_size: int = 1) -> None:
        """Actualizar con nuevo valor de loss."""
        if isinstance(loss, torch.Tensor):
            loss = loss.item()
        self.total_loss += loss * batch_size
        self.num_samples += batch_size

    def compute(self) -> float:
        """Calcular loss promedio."""
        return self.total_loss / self.num_samples if self.num_samples > 0 else 0.0

    def reset(self) -> None:
        """Reiniciar acumuladores."""
        self.total_loss = 0.0
        self.num_samples = 0


class PerplexityMetric(Metric):
    """Métrica de perplexity para modelos de lenguaje."""

    def __init__(self):
        super().__init__("perplexity", "value", higher_is_better=False)
        self.total_log_prob = 0.0
        self.num_tokens = 0

    def update(self, loss: Union[float, torch.Tensor], num_tokens: int) -> None:
        """Actualizar con loss y número de tokens."""
        if isinstance(loss, torch.Tensor):
            loss = loss.item()
        self.total_log_prob += loss * num_tokens
        self.num_tokens += num_tokens

    def compute(self) -> float:
        """Calcular perplexity."""
        if self.num_tokens == 0:
            return float('inf')
        avg_loss = self.total_log_prob / self.num_tokens
        return math.exp(avg_loss)

    def reset(self) -> None:
        """Reiniciar acumuladores."""
        self.total_log_prob = 0.0
        self.num_tokens = 0


class AccuracyMetric(Metric):
    """Métrica de accuracy (precisión)."""

    def __init__(self):
        super().__init__("accuracy", "%", higher_is_better=True)
        self.correct = 0
        self.total = 0

    def update(self, predictions: torch.Tensor, targets: torch.Tensor) -> None:
        """Actualizar con predicciones y objetivos."""
        if predictions.dim() > 1:
            predictions = predictions.argmax(dim=-1)

        self.correct += (predictions == targets).sum().item()
        self.total += targets.numel()

    def compute(self) -> float:
        """Calcular accuracy."""
        return (self.correct / self.total) * 100.0 if self.total > 0 else 0.0

    def reset(self) -> None:
        """Reiniciar contadores."""
        self.correct = 0
        self.total = 0


class TokenAccuracyMetric(AccuracyMetric):
    """Accuracy a nivel de token para modelos de lenguaje."""

    def __init__(self):
        super().__init__()
        self.name = "token_accuracy"

    def update(self, logits: torch.Tensor, targets: torch.Tensor, ignore_index: int = -100) -> None:
        """Actualizar con logits y targets, ignorando padding."""
        predictions = logits.argmax(dim=-1)

        # Crear máscara para ignorar tokens
        mask = targets != ignore_index
        predictions = predictions[mask]
        targets = targets[mask]

        if targets.numel() > 0:
            self.correct += (predictions == targets).sum().item()
            self.total += targets.numel()


class BLEUMetric(Metric):
    """Métrica BLEU para evaluación de generación de texto."""

    def __init__(self, n_gram: int = 4):
        super().__init__(f"bleu_{n_gram}", "score", higher_is_better=True)
        if not NLTK_AVAILABLE:
            raise ImportError("BLEU metric requires nltk. Install with: pip install nltk")
        self.n_gram = n_gram
        self.smooth_fn = SmoothingFunction().method1
        self.scores = []

    def update(self, hypothesis: List[str], reference: List[str]) -> None:
        """Actualizar con texto generado y referencia."""
        try:
            score = sentence_bleu([reference], hypothesis,
                                weights=self._get_weights(),
                                smoothing_function=self.smooth_fn)
            self.scores.append(score)
        except Exception as e:
            print(f"Error calculating BLEU: {e}")

    def _get_weights(self) -> List[float]:
        """Obtener pesos para n-gram."""
        if self.n_gram == 1:
            return [1.0]
        elif self.n_gram == 2:
            return [0.5, 0.5]
        elif self.n_gram == 3:
            return [0.33, 0.33, 0.33]
        else:  # 4-gram
            return [0.25, 0.25, 0.25, 0.25]

    def compute(self) -> float:
        """Calcular BLEU promedio."""
        return statistics.mean(self.scores) if self.scores else 0.0

    def reset(self) -> None:
        """Reiniciar lista de scores."""
        self.scores = []


class ROUGEMetric(Metric):
    """Métrica ROUGE para evaluación de generación de texto."""

    def __init__(self, rouge_type: str = 'rougeL'):
        super().__init__(f"rouge_{rouge_type}", "f1", higher_is_better=True)
        if not NLTK_AVAILABLE:
            raise ImportError("ROUGE metric requires rouge-score. Install with: pip install rouge-score")
        self.rouge_type = rouge_type
        self.scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=True)
        self.scores = []

    def update(self, hypothesis: str, reference: str) -> None:
        """Actualizar con texto generado y referencia."""
        try:
            scores = self.scorer.score(reference, hypothesis)
            self.scores.append(scores[self.rouge_type].fmeasure)
        except Exception as e:
            print(f"Error calculating ROUGE: {e}")

    def compute(self) -> float:
        """Calcular ROUGE promedio."""
        return statistics.mean(self.scores) if self.scores else 0.0

    def reset(self) -> None:
        """Reiniciar lista de scores."""
        self.scores = []


class GradientNormMetric(Metric):
    """Métrica de norma del gradiente."""

    def __init__(self):
        super().__init__("gradient_norm", "value", higher_is_better=False)
        self.norms = []

    def update(self, model: nn.Module) -> None:
        """Actualizar con gradientes del modelo."""
        total_norm = 0.0
        param_count = 0
        for param in model.parameters():
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                param_count += 1

        if param_count > 0:
            total_norm = total_norm ** (1. / 2)
            self.norms.append(total_norm)

    def compute(self) -> float:
        """Calcular norma promedio del gradiente."""
        return statistics.mean(self.norms) if self.norms else 0.0

    def reset(self) -> None:
        """Reiniciar lista de normas."""
        self.norms = []


class LearningRateMetric(Metric):
    """Métrica del learning rate."""

    def __init__(self):
        super().__init__("learning_rate", "value", higher_is_better=False)
        self.lr_values = []

    def update(self, lr: float) -> None:
        """Actualizar con nuevo valor de learning rate."""
        self.lr_values.append(lr)

    def compute(self) -> float:
        """Obtener último learning rate."""
        return self.lr_values[-1] if self.lr_values else 0.0

    def reset(self) -> None:
        """Reiniciar lista de valores."""
        self.lr_values = []


class CustomMetric(Metric):
    """Métrica personalizada definida por función."""

    def __init__(self, name: str, compute_fn: Callable[[], float],
                 unit: str = "", higher_is_better: bool = False):
        super().__init__(name, unit, higher_is_better)
        self.compute_fn = compute_fn
        self.value = 0.0

    def update(self, *args, **kwargs) -> None:
        """No se usa para métricas personalizadas."""
        pass

    def compute(self) -> float:
        """Calcular usando función personalizada."""
        try:
            self.value = self.compute_fn()
        except Exception as e:
            print(f"Error computing custom metric {self.name}: {e}")
            self.value = 0.0
        return self.value

    def reset(self) -> None:
        """Reiniciar valor."""
        self.value = 0.0


@dataclass
class MetricsConfig:
    """Configuración del sistema de métricas."""
    enabled_metrics: List[str] = field(default_factory=lambda: [
        "loss", "perplexity", "token_accuracy", "gradient_norm", "learning_rate"
    ])
    compute_bleu: bool = False
    compute_rouge: bool = False
    rouge_types: List[str] = field(default_factory=lambda: ["rouge1", "rougeL"])
    bleu_n_grams: List[int] = field(default_factory=lambda: [1, 2, 4])
    custom_metrics: Dict[str, Callable[[], float]] = field(default_factory=dict)
    log_interval: int = 10  # batches
    eval_interval: int = 100  # batches


class MetricsEvaluator:
    """
    Evaluador principal que gestiona múltiples métricas.
    Integra con el sistema de entrenamiento para evaluación completa.
    """

    def __init__(self, config: MetricsConfig):
        self.config = config
        self.logger = AiloosLogger(__name__)
        self.metrics: Dict[str, Metric] = {}
        self._initialize_metrics()

        # Estado de evaluación
        self.batch_count = 0
        self.start_time = time.time()

    def _initialize_metrics(self) -> None:
        """Inicializar métricas habilitadas."""
        # Métricas estándar
        if "loss" in self.config.enabled_metrics:
            self.metrics["loss"] = LossMetric()

        if "perplexity" in self.config.enabled_metrics:
            self.metrics["perplexity"] = PerplexityMetric()

        if "token_accuracy" in self.config.enabled_metrics:
            self.metrics["token_accuracy"] = TokenAccuracyMetric()

        if "gradient_norm" in self.config.enabled_metrics:
            self.metrics["gradient_norm"] = GradientNormMetric()

        if "learning_rate" in self.config.enabled_metrics:
            self.metrics["learning_rate"] = LearningRateMetric()

        # Métricas de generación (si disponibles)
        if self.config.compute_bleu and NLTK_AVAILABLE:
            for n in self.config.bleu_n_grams:
                self.metrics[f"bleu_{n}"] = BLEUMetric(n)

        if self.config.compute_rouge and NLTK_AVAILABLE:
            for rouge_type in self.config.rouge_types:
                self.metrics[f"rouge_{rouge_type}"] = ROUGEMetric(rouge_type)

        # Métricas personalizadas
        for name, compute_fn in self.config.custom_metrics.items():
            self.metrics[name] = CustomMetric(name, compute_fn)

        self.logger.info(f"📊 Inicializadas {len(self.metrics)} métricas: {list(self.metrics.keys())}")

    def update_batch(self, **kwargs) -> None:
        """Actualizar métricas con datos de un batch."""
        self.batch_count += 1

        # Actualizar métricas disponibles
        if "loss" in self.metrics and "loss" in kwargs:
            batch_size = kwargs.get("batch_size", 1)
            self.metrics["loss"].update(kwargs["loss"], batch_size)

        if "perplexity" in self.metrics and "loss" in kwargs and "num_tokens" in kwargs:
            self.metrics["perplexity"].update(kwargs["loss"], kwargs["num_tokens"])

        if "token_accuracy" in self.metrics and "logits" in kwargs and "targets" in kwargs:
            ignore_index = kwargs.get("ignore_index", -100)
            self.metrics["token_accuracy"].update(kwargs["logits"], kwargs["targets"], ignore_index)

        if "gradient_norm" in self.metrics and "model" in kwargs:
            self.metrics["gradient_norm"].update(kwargs["model"])

        if "learning_rate" in self.metrics and "lr" in kwargs:
            self.metrics["learning_rate"].update(kwargs["lr"])

        # Logging periódico
        if self.batch_count % self.config.log_interval == 0:
            self._log_current_metrics()

    def update_generation(self, hypotheses: List[str], references: List[str]) -> None:
        """Actualizar métricas de generación de texto."""
        if not NLTK_AVAILABLE:
            return

        for hyp, ref in zip(hypotheses, references):
            # BLEU
            for n in self.config.bleu_n_grams:
                metric_name = f"bleu_{n}"
                if metric_name in self.metrics:
                    hyp_tokens = hyp.split()
                    ref_tokens = ref.split()
                    self.metrics[metric_name].update(hyp_tokens, ref_tokens)

            # ROUGE
            for rouge_type in self.config.rouge_types:
                metric_name = f"rouge_{rouge_type}"
                if metric_name in self.metrics:
                    self.metrics[metric_name].update(hyp, ref)

    def compute_all(self) -> Dict[str, MetricResult]:
        """Calcular todas las métricas."""
        results = {}
        for name, metric in self.metrics.items():
            results[name] = metric.get_result()
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas principales."""
        results = self.compute_all()

        summary = {
            "batch_count": self.batch_count,
            "elapsed_time": time.time() - self.start_time,
            "metrics": {}
        }

        for name, result in results.items():
            summary["metrics"][name] = {
                "value": result.value,
                "unit": result.unit,
                "higher_is_better": result.higher_is_better
            }

        return summary

    def reset(self) -> None:
        """Reiniciar todas las métricas."""
        for metric in self.metrics.values():
            metric.reset()
        self.batch_count = 0
        self.start_time = time.time()
        self.logger.info("🔄 Métricas reiniciadas")

    def _log_current_metrics(self) -> None:
        """Log de métricas actuales."""
        results = self.compute_all()
        log_msg = f"📈 Batch {self.batch_count}: "

        metrics_str = []
        for name, result in results.items():
            if hasattr(result, 'value') and not math.isnan(result.value):
                metrics_str.append(f"{name}={result.value:.4f}")

        log_msg += " | ".join(metrics_str)
        self.logger.info(log_msg)


# Funciones de conveniencia
def create_default_metrics_config() -> MetricsConfig:
    """Crear configuración de métricas por defecto."""
    return MetricsConfig()


def create_generation_metrics_config() -> MetricsConfig:
    """Crear configuración para métricas de generación."""
    return MetricsConfig(
        enabled_metrics=["loss", "perplexity", "token_accuracy", "gradient_norm", "learning_rate"],
        compute_bleu=True,
        compute_rouge=True,
        rouge_types=["rouge1", "rouge2", "rougeL"],
        bleu_n_grams=[1, 2, 4]
    )


def evaluate_model_on_dataset(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    tokenizer,
    device: str = "cpu",
    max_eval_samples: int = 1000
) -> Dict[str, MetricResult]:
    """
    Evaluar modelo en un dataset completo.

    Args:
        model: Modelo a evaluar
        dataloader: DataLoader con datos de evaluación
        tokenizer: Tokenizador
        device: Dispositivo para evaluación
        max_eval_samples: Máximo número de muestras a evaluar

    Returns:
        Diccionario con resultados de métricas
    """
    model.eval()
    evaluator = MetricsEvaluator(create_default_metrics_config())

    samples_evaluated = 0

    with torch.no_grad():
        for batch in dataloader:
            if samples_evaluated >= max_eval_samples:
                break

            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            batch_size = input_ids.size(0)
            num_tokens = (labels != -100).sum().item()

            evaluator.update_batch(
                loss=outputs['loss'],
                logits=outputs['logits'],
                targets=labels,
                batch_size=batch_size,
                num_tokens=num_tokens,
                model=model
            )

            samples_evaluated += batch_size

    return evaluator.compute_all()