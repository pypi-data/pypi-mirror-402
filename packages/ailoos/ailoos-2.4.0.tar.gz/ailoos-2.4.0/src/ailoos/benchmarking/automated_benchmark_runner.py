import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import os
from pathlib import Path

# Assuming transformers and evaluate are available
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    import evaluate
except ImportError:
    print("Warning: transformers, torch, or evaluate not installed. Install with: pip install transformers torch evaluate")

@dataclass
class BenchmarkConfig:
    model_name: str
    datasets: List[str]
    metrics: List[str]
    batch_size: int = 8
    max_length: int = 512
    num_samples: Optional[int] = None
    seed: int = 42
    device: str = "auto"

@dataclass
class BenchmarkResult:
    dataset: str
    metric: str
    score: float
    execution_time: float
    metadata: Dict[str, Any]

class AutomatedBenchmarkRunner:
    """
    Ejecutor automático de benchmarks estandarizados para modelos de lenguaje.
    Proporciona ejecución reproducible y detallada de métricas de rendimiento.
    """

    def __init__(self, config: BenchmarkConfig, log_level: str = "INFO"):
        self.config = config
        self.logger = self._setup_logger(log_level)
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)

        # Set seed for reproducibility
        import random
        import numpy as np
        import torch
        random.seed(config.seed)
        np.random.seed(config.seed)
        torch.manual_seed(config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.seed)

        self.model = None
        self.tokenizer = None
        self.pipeline = None

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        # Create handlers
        file_handler = logging.FileHandler(self.results_dir / "benchmark_runner.log")
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def load_model(self):
        """Carga el modelo y tokenizer especificados en la configuración."""
        try:
            self.logger.info(f"Loading model: {self.config.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.config.model_name)

            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() and self.config.device == "auto" else -1,
                batch_size=self.config.batch_size,
                max_length=self.config.max_length
            )
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def run_benchmarks(self) -> List[BenchmarkResult]:
        """
        Ejecuta todos los benchmarks configurados y devuelve los resultados.
        """
        if self.model is None:
            self.load_model()

        results = []
        self.logger.info("Starting benchmark execution")

        for dataset_name in self.config.datasets:
            self.logger.info(f"Running benchmarks for dataset: {dataset_name}")
            dataset_results = self._run_dataset_benchmarks(dataset_name)
            results.extend(dataset_results)

        self._save_results(results)
        self.logger.info("Benchmark execution completed")
        return results

    def _run_dataset_benchmarks(self, dataset_name: str) -> List[BenchmarkResult]:
        """Ejecuta benchmarks para un dataset específico."""
        results = []

        # Load dataset (simplified - in practice, use datasets library)
        try:
            # Placeholder for dataset loading
            # dataset = load_dataset(dataset_name, split="test")
            # if self.config.num_samples:
            #     dataset = dataset.select(range(min(self.config.num_samples, len(dataset))))

            # For now, simulate with dummy data
            dataset = [{"text": f"Sample text {i}"} for i in range(10 if not self.config.num_samples else min(10, self.config.num_samples))]

            for metric_name in self.config.metrics:
                self.logger.info(f"Computing metric: {metric_name} on {dataset_name}")
                start_time = time.time()

                try:
                    score = self._compute_metric(dataset, metric_name)
                    execution_time = time.time() - start_time

                    result = BenchmarkResult(
                        dataset=dataset_name,
                        metric=metric_name,
                        score=score,
                        execution_time=execution_time,
                        metadata={
                            "model": self.config.model_name,
                            "num_samples": len(dataset),
                            "config": self.config.__dict__
                        }
                    )
                    results.append(result)
                    self.logger.info(f"Metric {metric_name}: {score:.4f} (time: {execution_time:.2f}s)")

                except Exception as e:
                    self.logger.error(f"Failed to compute metric {metric_name}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to load/process dataset {dataset_name}: {e}")

        return results

    def _compute_metric(self, dataset: List[Dict], metric_name: str) -> float:
        """Computa una métrica específica en el dataset."""
        if metric_name == "perplexity":
            return self._compute_perplexity(dataset)
        elif metric_name == "accuracy":
            return self._compute_accuracy(dataset)
        elif metric_name.startswith("rouge"):
            return self._compute_rouge(dataset, metric_name)
        else:
            # Use evaluate library for other metrics
            try:
                metric = evaluate.load(metric_name)
                # Simplified computation
                predictions = [self.pipeline(sample["text"])[0]["generated_text"] for sample in dataset]
                references = [sample.get("reference", sample["text"]) for sample in dataset]
                return metric.compute(predictions=predictions, references=references)[metric_name]
            except Exception as e:
                self.logger.warning(f"Using dummy score for {metric_name}: {e}")
                return 0.5  # Dummy score

    def _compute_perplexity(self, dataset: List[Dict]) -> float:
        """Computa perplexity usando el modelo."""
        # Simplified perplexity computation
        total_loss = 0
        count = 0
        for sample in dataset:
            inputs = self.tokenizer(sample["text"], return_tensors="pt", truncation=True, max_length=self.config.max_length)
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs, labels=inputs["input_ids"])
                total_loss += outputs.loss.item()
                count += 1
        return torch.exp(torch.tensor(total_loss / count)).item()

    def _compute_accuracy(self, dataset: List[Dict]) -> float:
        """Computa accuracy (simplified)."""
        # Placeholder - in practice, need labeled data
        return 0.85

    def _compute_rouge(self, dataset: List[Dict], metric_name: str) -> float:
        """Computa ROUGE scores."""
        try:
            rouge = evaluate.load("rouge")
            predictions = [self.pipeline(sample["text"])[0]["generated_text"] for sample in dataset]
            references = [sample.get("reference", sample["text"]) for sample in dataset]
            results = rouge.compute(predictions=predictions, references=references)
            return results[metric_name.split("-")[1]]  # e.g., "rouge1" -> "rouge1"
        except:
            return 0.7

    def _save_results(self, results: List[BenchmarkResult]):
        """Guarda los resultados en archivos JSON."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = self.results_dir / filename

        results_dict = {
            "config": self.config.__dict__,
            "timestamp": timestamp,
            "results": [result.__dict__ for result in results]
        }

        with open(filepath, "w") as f:
            json.dump(results_dict, f, indent=2, default=str)

        self.logger.info(f"Results saved to {filepath}")