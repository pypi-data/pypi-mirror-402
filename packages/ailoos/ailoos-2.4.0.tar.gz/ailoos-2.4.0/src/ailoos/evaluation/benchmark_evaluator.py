#!/usr/bin/env python3
"""
Sistema completo de evaluación de benchmarks NLP para EmpoorioLM.

Este módulo proporciona evaluación completa en benchmarks estándar de NLP como:
- GLUE (General Language Understanding Evaluation)
- MMLU (Massive Multitask Language Understanding)
- Y otros benchmarks relevantes

Características principales:
- Evaluación automática en múltiples tareas
- Cálculo de métricas específicas por tarea
- Integración con Hugging Face datasets
- Soporte para diferentes formatos de modelo
- Logging y reporting detallado
- Comparación con baselines

Uso básico:
    from src.ailoos.evaluation.benchmark_evaluator import BenchmarkEvaluator

    evaluator = BenchmarkEvaluator()
    results = evaluator.evaluate_model_on_glue(model, tokenizer)
    mmlu_results = evaluator.evaluate_model_on_mmlu(model, tokenizer)

Integración con sistema de métricas existente:
    from src.ailoos.training.metrics import MetricsEvaluator

    # Los resultados de benchmark se pueden integrar con el sistema de métricas
    benchmark_results = evaluator.evaluate_model_on_glue(model, tokenizer)
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from pathlib import Path
import time

try:
    from datasets import load_dataset, load_metric
    from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
    from scipy.stats import pearsonr, spearmanr
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("Advertencia: datasets y scikit-learn no disponibles. Funcionalidad de benchmarks limitada.")

from ..core.logging import get_logger
from ..models.empoorio_lm.tokenizer import EmpoorioLMTokenizer

logger = get_logger(__name__)


@dataclass
class BenchmarkTask:
    """Configuración de una tarea de benchmark."""
    name: str
    dataset_name: str
    task_type: str  # 'classification', 'regression', 'multiple_choice'
    num_labels: int
    metric_names: List[str]
    description: str = ""


@dataclass
class BenchmarkResult:
    """Resultado de evaluación en una tarea específica."""
    task_name: str
    dataset_name: str
    metric_name: str
    metric_value: float
    num_samples: int
    execution_time: float
    model_name: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class BenchmarkReport:
    """Reporte completo de evaluación en benchmarks."""
    model_name: str
    benchmark_name: str
    tasks_completed: int
    total_execution_time: float
    average_score: float
    results: List[BenchmarkResult] = field(default_factory=list)
    task_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class BenchmarkEvaluator:
    """
    Evaluador principal para benchmarks NLP.

    Soporta evaluación en GLUE, MMLU y otros benchmarks estándar.
    """

    def __init__(self, cache_dir: str = "./benchmark_cache",
                 max_eval_samples: int = None):
        if not DATASETS_AVAILABLE:
            raise ImportError("BenchmarkEvaluator requiere datasets y scikit-learn. Instale con: pip install datasets scikit-learn")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_eval_samples = max_eval_samples

        # Configuración de tareas GLUE
        self.glue_tasks = self._setup_glue_tasks()

        # Configuración de tareas MMLU
        self.mmlu_tasks = self._setup_mmlu_tasks()

        logger.info("🏆 BenchmarkEvaluator initialized")
        logger.info(f"   Cache dir: {self.cache_dir}")
        logger.info(f"   GLUE tasks: {len(self.glue_tasks)}")
        logger.info(f"   MMLU tasks: {len(self.mmlu_tasks)}")

    def _setup_glue_tasks(self) -> Dict[str, BenchmarkTask]:
        """Configura las tareas del benchmark GLUE."""
        return {
            "cola": BenchmarkTask(
                name="cola",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["matthews_correlation"],
                description="Corpus of Linguistic Acceptability - Binary classification"
            ),
            "sst2": BenchmarkTask(
                name="sst2",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy"],
                description="Stanford Sentiment Treebank - Binary sentiment classification"
            ),
            "mrpc": BenchmarkTask(
                name="mrpc",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy", "f1"],
                description="Microsoft Research Paraphrase Corpus - Paraphrase detection"
            ),
            "stsb": BenchmarkTask(
                name="stsb",
                dataset_name="glue",
                task_type="regression",
                num_labels=1,
                metric_names=["pearson", "spearmanr"],
                description="Semantic Textual Similarity Benchmark - Regression"
            ),
            "qqp": BenchmarkTask(
                name="qqp",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy", "f1"],
                description="Quora Question Pairs - Paraphrase detection"
            ),
            "mnli": BenchmarkTask(
                name="mnli",
                dataset_name="glue",
                task_type="classification",
                num_labels=3,
                metric_names=["accuracy"],
                description="Multi-Genre Natural Language Inference - 3-class classification"
            ),
            "mnli-mm": BenchmarkTask(
                name="mnli-mm",
                dataset_name="glue",
                task_type="classification",
                num_labels=3,
                metric_names=["accuracy"],
                description="Multi-Genre Natural Language Inference (mismatched) - 3-class classification"
            ),
            "qnli": BenchmarkTask(
                name="qnli",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy"],
                description="Question-answering NLI - Binary classification"
            ),
            "rte": BenchmarkTask(
                name="rte",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy"],
                description="Recognizing Textual Entailment - Binary classification"
            ),
            "wnli": BenchmarkTask(
                name="wnli",
                dataset_name="glue",
                task_type="classification",
                num_labels=2,
                metric_names=["accuracy"],
                description="Winograd NLI - Binary classification"
            )
        }

    def _setup_mmlu_tasks(self) -> Dict[str, BenchmarkTask]:
        """Configura las tareas del benchmark MMLU."""
        # MMLU tiene 57 subtasks, pero podemos agruparlas por categoría
        mmlu_categories = [
            "abstract_algebra", "anatomy", "astronomy", "business_ethics", "clinical_knowledge",
            "college_biology", "college_chemistry", "college_computer_science", "college_mathematics",
            "college_medicine", "college_physics", "computer_security", "conceptual_physics",
            "econometrics", "electrical_engineering", "elementary_mathematics", "formal_logic",
            "global_facts", "high_school_biology", "high_school_chemistry", "high_school_computer_science",
            "high_school_european_history", "high_school_geography", "high_school_government_and_politics",
            "high_school_macroeconomics", "high_school_mathematics", "high_school_microeconomics",
            "high_school_physics", "high_school_psychology", "high_school_statistics", "high_school_us_history",
            "high_school_world_history", "human_aging", "human_sexuality", "international_law",
            "jurisprudence", "logical_fallacies", "machine_learning", "management", "marketing",
            "medical_genetics", "miscellaneous", "moral_disputes", "moral_scenarios", "nutrition",
            "philosophy", "prehistory", "professional_accounting", "professional_law",
            "professional_medicine", "professional_psychology", "public_relations", "security_studies",
            "sociology", "us_foreign_policy", "virology", "world_religions"
        ]

        tasks = {}
        for category in mmlu_categories:
            tasks[category] = BenchmarkTask(
                name=category,
                dataset_name="cais/mmlu",
                task_type="multiple_choice",
                num_labels=4,  # MMLU siempre tiene 4 opciones
                metric_names=["accuracy"],
                description=f"MMLU {category.replace('_', ' ').title()} - Multiple choice QA"
            )

        return tasks

    def evaluate_model_on_glue(self, model: nn.Module, tokenizer: EmpoorioLMTokenizer,
                              tasks: List[str] = None, batch_size: int = 8,
                              max_seq_length: int = 512) -> BenchmarkReport:
        """
        Evalúa el modelo en el benchmark GLUE.

        Args:
            model: Modelo a evaluar
            tokenizer: Tokenizador del modelo
            tasks: Lista de tareas GLUE a evaluar (None = todas)
            batch_size: Tamaño del batch para evaluación
            max_seq_length: Longitud máxima de secuencia

        Returns:
            Reporte completo de evaluación GLUE
        """
        if tasks is None:
            tasks = list(self.glue_tasks.keys())

        logger.info(f"🏆 Starting GLUE evaluation on tasks: {tasks}")

        start_time = time.time()
        results = []

        model.eval()
        device = next(model.parameters()).device

        for task_name in tasks:
            if task_name not in self.glue_tasks:
                logger.warning(f"Task {task_name} not found in GLUE tasks, skipping")
                continue

            task_config = self.glue_tasks[task_name]
            logger.info(f"📋 Evaluating {task_name}: {task_config.description}")

            try:
                task_results = self._evaluate_glue_task(
                    model, tokenizer, task_config, device,
                    batch_size, max_seq_length
                )
                results.extend(task_results)

            except Exception as e:
                logger.error(f"Error evaluating {task_name}: {e}")
                continue

        total_time = time.time() - start_time

        # Calcular promedio GLUE
        glue_score = self._calculate_glue_score(results)

        report = BenchmarkReport(
            model_name=getattr(model, 'config', {}).get('model_name', 'unknown'),
            benchmark_name="GLUE",
            tasks_completed=len([r for r in results if r.task_name in tasks]),
            total_execution_time=total_time,
            average_score=glue_score,
            results=results
        )

        logger.info(f"🏆 GLUE evaluation completed in {total_time:.2f}s")
        logger.info(f"   Average GLUE score: {glue_score:.4f}")
        logger.info(f"   Tasks completed: {report.tasks_completed}/{len(tasks)}")

        return report

    def _evaluate_glue_task(self, model: nn.Module, tokenizer: EmpoorioLMTokenizer,
                           task: BenchmarkTask, device: torch.device,
                           batch_size: int, max_seq_length: int) -> List[BenchmarkResult]:
        """Evalúa una tarea específica de GLUE."""
        results = []

        try:
            # Cargar dataset
            if task.name in ["mnli-mm"]:
                # MNLI mismatched usa configuración diferente
                dataset = load_dataset(task.dataset_name, "mnli", cache_dir=str(self.cache_dir))
                eval_dataset = dataset["validation_mismatched"]
            else:
                dataset = load_dataset(task.dataset_name, task.name, cache_dir=str(self.cache_dir))
                eval_dataset = dataset["validation"]

            # Limitar muestras si especificado
            if self.max_eval_samples:
                eval_dataset = eval_dataset.select(range(min(self.max_eval_samples, len(eval_dataset))))

            logger.info(f"   Loaded {len(eval_dataset)} samples for {task.name}")

            # Preparar datos
            processed_dataset = self._preprocess_glue_dataset(
                eval_dataset, tokenizer, task, max_seq_length
            )

            # Crear dataloader
            dataloader = torch.utils.data.DataLoader(
                processed_dataset, batch_size=batch_size, shuffle=False
            )

            # Evaluar
            start_time = time.time()
            predictions, labels = self._evaluate_model_on_dataset(
                model, dataloader, device, task
            )
            eval_time = time.time() - start_time

            # Calcular métricas
            task_metrics = self._calculate_glue_metrics(predictions, labels, task)

            # Crear resultados
            for metric_name, metric_value in task_metrics.items():
                result = BenchmarkResult(
                    task_name=task.name,
                    dataset_name=task.dataset_name,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    num_samples=len(eval_dataset),
                    execution_time=eval_time,
                    model_name=getattr(model, 'config', {}).get('model_name', 'unknown')
                )
                results.append(result)

        except Exception as e:
            logger.error(f"Error in {task.name} evaluation: {e}")
            raise

        return results

    def _preprocess_glue_dataset(self, dataset, tokenizer: EmpoorioLMTokenizer,
                                task: BenchmarkTask, max_seq_length: int):
        """Preprocesa el dataset GLUE para una tarea específica."""

        def tokenize_function(examples):
            # Preparar inputs según el tipo de tarea
            if task.name in ["cola", "sst2"]:
                # Single sentence tasks
                inputs = tokenizer(
                    examples["sentence"],
                    truncation=True,
                    padding="max_length",
                    max_length=max_seq_length,
                    return_tensors="pt"
                )
            elif task.name in ["mrpc", "stsb", "qqp", "rte", "wnli"]:
                # Sentence pair tasks
                inputs = tokenizer(
                    examples["sentence1"],
                    examples["sentence2"],
                    truncation=True,
                    padding="max_length",
                    max_length=max_seq_length,
                    return_tensors="pt"
                )
            elif task.name in ["mnli", "mnli-mm", "qnli"]:
                # NLI tasks
                inputs = tokenizer(
                    examples["premise"],
                    examples["hypothesis"],
                    truncation=True,
                    padding="max_length",
                    max_length=max_seq_length,
                    return_tensors="pt"
                )
            else:
                raise ValueError(f"Unknown GLUE task: {task.name}")

            # Convertir labels
            if task.task_type == "classification":
                labels = torch.tensor(examples["label"], dtype=torch.long)
            elif task.task_type == "regression":
                labels = torch.tensor(examples["label"], dtype=torch.float)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")

            inputs["labels"] = labels
            return inputs

        # Aplicar tokenización
        processed_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )

        # Convertir a formato PyTorch
        processed_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

        return processed_dataset

    def _evaluate_model_on_dataset(self, model: nn.Module, dataloader,
                                  device: torch.device, task: BenchmarkTask) -> Tuple[List, List]:
        """Evalúa el modelo en un dataset y retorna predicciones y labels."""
        model.eval()
        predictions = []
        labels = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                batch_labels = batch["labels"].to(device)

                # Forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)

                if task.task_type == "classification":
                    # Para clasificación, usar argmax de logits
                    logits = outputs["logits"]
                    if task.num_labels == 1:
                        # Binary classification con sigmoid
                        preds = (torch.sigmoid(logits.squeeze()) > 0.5).long().cpu().numpy()
                    else:
                        # Multi-class classification
                        preds = torch.argmax(logits, dim=-1).cpu().numpy()
                elif task.task_type == "regression":
                    # Para regresión, usar los logits directamente
                    preds = outputs["logits"].squeeze().cpu().numpy()
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")

                predictions.extend(preds)
                labels.extend(batch_labels.cpu().numpy())

        return predictions, labels

    def _calculate_glue_metrics(self, predictions: List, labels: List,
                               task: BenchmarkTask) -> Dict[str, float]:
        """Calcula métricas específicas para una tarea GLUE."""
        metrics = {}

        predictions = np.array(predictions)
        labels = np.array(labels)

        for metric_name in task.metric_names:
            if metric_name == "accuracy":
                metrics["accuracy"] = accuracy_score(labels, predictions)
            elif metric_name == "f1":
                metrics["f1"] = f1_score(labels, predictions, average="macro")
            elif metric_name == "matthews_correlation":
                metrics["matthews_correlation"] = matthews_corrcoef(labels, predictions)
            elif metric_name == "pearson":
                metrics["pearson"] = pearsonr(predictions, labels)[0]
            elif metric_name == "spearmanr":
                metrics["spearmanr"] = spearmanr(predictions, labels)[0]
            else:
                logger.warning(f"Unknown metric: {metric_name}")

        return metrics

    def _calculate_glue_score(self, results: List[BenchmarkResult]) -> float:
        """Calcula el score promedio de GLUE."""
        # GLUE score es el promedio de las métricas principales de cada tarea
        task_scores = {}

        for result in results:
            task_name = result.task_name
            if task_name not in task_scores:
                task_scores[task_name] = []

            # Usar la métrica principal de cada tarea
            if result.metric_name in ["accuracy", "matthews_correlation", "pearson", "spearmanr"]:
                task_scores[task_name].append(result.metric_value)

        # Promediar las métricas de cada tarea
        final_scores = []
        for task_name, scores in task_scores.items():
            if scores:
                # Para STS-B, usar promedio de Pearson y Spearman
                if task_name == "stsb":
                    final_scores.append(np.mean(scores))
                else:
                    final_scores.append(scores[0])  # Usar primera métrica disponible

        return np.mean(final_scores) if final_scores else 0.0

    def evaluate_model_on_mmlu(self, model: nn.Module, tokenizer: EmpoorioLMTokenizer,
                              categories: List[str] = None, batch_size: int = 4,
                              max_seq_length: int = 512) -> BenchmarkReport:
        """
        Evalúa el modelo en el benchmark MMLU.

        Args:
            model: Modelo a evaluar
            tokenizer: Tokenizador del modelo
            categories: Lista de categorías MMLU a evaluar (None = todas)
            batch_size: Tamaño del batch para evaluación
            max_seq_length: Longitud máxima de secuencia

        Returns:
            Reporte completo de evaluación MMLU
        """
        if categories is None:
            categories = list(self.mmlu_tasks.keys())

        logger.info(f"🧠 Starting MMLU evaluation on {len(categories)} categories")

        start_time = time.time()
        results = []

        model.eval()
        device = next(model.parameters()).device

        for category in categories:
            if category not in self.mmlu_tasks:
                logger.warning(f"Category {category} not found in MMLU tasks, skipping")
                continue

            task_config = self.mmlu_tasks[category]
            logger.info(f"📚 Evaluating {category}")

            try:
                task_results = self._evaluate_mmlu_task(
                    model, tokenizer, task_config, device,
                    batch_size, max_seq_length
                )
                results.extend(task_results)

            except Exception as e:
                logger.error(f"Error evaluating {category}: {e}")
                continue

        total_time = time.time() - start_time

        # Calcular promedio MMLU
        mmlu_score = np.mean([r.metric_value for r in results if r.metric_name == "accuracy"])

        report = BenchmarkReport(
            model_name=getattr(model, 'config', {}).get('model_name', 'unknown'),
            benchmark_name="MMLU",
            tasks_completed=len(results),
            total_execution_time=total_time,
            average_score=mmlu_score,
            results=results
        )

        logger.info(f"🧠 MMLU evaluation completed in {total_time:.2f}s")
        logger.info(f"   Average MMLU score: {mmlu_score:.4f}")
        logger.info(f"   Categories completed: {len(results)}")

        return report

    def _evaluate_mmlu_task(self, model: nn.Module, tokenizer: EmpoorioLMTokenizer,
                           task: BenchmarkTask, device: torch.device,
                           batch_size: int, max_seq_length: int) -> List[BenchmarkResult]:
        """Evalúa una categoría específica de MMLU."""
        results = []

        try:
            # Cargar dataset MMLU
            dataset = load_dataset(task.dataset_name, task.name, cache_dir=str(self.cache_dir))
            eval_dataset = dataset["test"]  # MMLU usa 'test' para evaluación

            # Limitar muestras si especificado
            if self.max_eval_samples:
                eval_dataset = eval_dataset.select(range(min(self.max_eval_samples, len(eval_dataset))))

            logger.info(f"   Loaded {len(eval_dataset)} samples for {task.name}")

            # Preparar datos
            processed_dataset = self._preprocess_mmlu_dataset(
                eval_dataset, tokenizer, max_seq_length
            )

            # Crear dataloader
            dataloader = torch.utils.data.DataLoader(
                processed_dataset, batch_size=batch_size, shuffle=False
            )

            # Evaluar
            start_time = time.time()
            predictions, labels = self._evaluate_model_on_mmlu_dataset(
                model, dataloader, device
            )
            eval_time = time.time() - start_time

            # Calcular métricas
            accuracy = accuracy_score(labels, predictions)

            # Crear resultado
            result = BenchmarkResult(
                task_name=task.name,
                dataset_name=task.dataset_name,
                metric_name="accuracy",
                metric_value=accuracy,
                num_samples=len(eval_dataset),
                execution_time=eval_time,
                model_name=getattr(model, 'config', {}).get('model_name', 'unknown')
            )
            results.append(result)

        except Exception as e:
            logger.error(f"Error in {task.name} evaluation: {e}")
            raise

        return results

    def _preprocess_mmlu_dataset(self, dataset, tokenizer: EmpoorioLMTokenizer,
                                max_seq_length: int):
        """Preprocesa el dataset MMLU."""

        def tokenize_function(examples):
            # MMLU formato: pregunta + opciones A, B, C, D
            questions = examples["question"]
            choices = examples["choices"]  # Lista de 4 opciones
            answers = examples["answer"]   # Índice de la respuesta correcta (0-3)

            # Formatear como multiple choice
            formatted_inputs = []
            for q, opts in zip(questions, choices):
                # Crear prompt con pregunta y opciones
                prompt = f"Question: {q}\n\n"
                for i, opt in enumerate(opts):
                    prompt += f"{chr(65+i)}. {opt}\n"  # A, B, C, D
                prompt += "\nAnswer:"

                formatted_inputs.append(prompt)

            # Tokenizar
            inputs = tokenizer(
                formatted_inputs,
                truncation=True,
                padding="max_length",
                max_length=max_seq_length,
                return_tensors="pt"
            )

            # Labels son los índices de respuesta correcta
            inputs["labels"] = torch.tensor(answers, dtype=torch.long)
            return inputs

        # Aplicar tokenización
        processed_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )

        # Convertir a formato PyTorch
        processed_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

        return processed_dataset

    def _evaluate_model_on_mmlu_dataset(self, model: nn.Module, dataloader,
                                       device: torch.device) -> Tuple[List[int], List[int]]:
        """Evalúa el modelo en dataset MMLU y retorna predicciones y labels."""
        model.eval()
        predictions = []
        labels = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                batch_labels = batch["labels"].to(device)

                # Forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]

                # Para MMLU, necesitamos predecir cuál opción es correcta
                # Los logits representan la likelihood de cada opción
                # En este caso simplificado, asumimos que el modelo predice directamente el índice
                # En un setup real, necesitaríamos un approach más sofisticado

                # Por simplicidad, usar argmax (esto es una aproximación)
                preds = torch.argmax(logits, dim=-1).cpu().numpy()

                predictions.extend(preds)
                labels.extend(batch_labels.cpu().numpy())

        return predictions, labels

    def save_benchmark_report(self, report: BenchmarkReport, output_path: str = None):
        """Guarda un reporte de benchmark en formato JSON."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"benchmark_{report.benchmark_name}_{report.model_name}_{timestamp}.json"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convertir a diccionario serializable
        report_dict = {
            "model_name": report.model_name,
            "benchmark_name": report.benchmark_name,
            "tasks_completed": report.tasks_completed,
            "total_execution_time": report.total_execution_time,
            "average_score": report.average_score,
            "results": [r.__dict__ for r in report.results],
            "task_summaries": report.task_summaries,
            "timestamp": datetime.now().isoformat()
        }

        with open(output_file, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"💾 Benchmark report saved to {output_file}")

    def get_available_tasks(self, benchmark: str) -> List[str]:
        """Retorna lista de tareas disponibles para un benchmark."""
        if benchmark.lower() == "glue":
            return list(self.glue_tasks.keys())
        elif benchmark.lower() == "mmlu":
            return list(self.mmlu_tasks.keys())
        else:
            return []

    def get_task_info(self, benchmark: str, task_name: str) -> Optional[BenchmarkTask]:
        """Retorna información de una tarea específica."""
        if benchmark.lower() == "glue":
            return self.glue_tasks.get(task_name)
        elif benchmark.lower() == "mmlu":
            return self.mmlu_tasks.get(task_name)
        return None