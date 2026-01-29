"""
Real Data Pipeline para EmpoorioLM - FASE REAL-5
Pipeline de datos reales con datasets sustanciales para entrenamiento real.
Soporta WikiText, OpenWebText y otros datasets de calidad.
"""

import os
import logging
from typing import Dict, List, Optional, Union, Iterator, Any
from pathlib import Path
import tempfile
import hashlib
from dataclasses import dataclass, field

import torch
from datasets import load_dataset, Dataset, DatasetDict, concatenate_datasets
from torch.utils.data import DataLoader, DistributedSampler
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DataPipelineConfig:
    """Configuración del pipeline de datos reales."""
    datasets: List[str] = field(default_factory=lambda: ["wikitext", "openwebtext"])
    dataset_configs: Dict[str, str] = field(default_factory=lambda: {
        "wikitext": "wikitext-103-raw-v1",
        "openwebtext": None
    })
    cache_dir: Optional[str] = None
    max_samples_per_dataset: Optional[int] = None
    text_column: str = "text"
    min_text_length: int = 10
    max_text_length: int = 10000
    streaming: bool = False  # Para datasets muy grandes
    num_proc: int = 4  # Procesos paralelos para preprocessing
    batch_size: int = 1000  # Batch size para procesamiento


class RealDataPipeline:
    """
    Pipeline de datos reales para entrenamiento de EmpoorioLM.
    Carga y preprocesa datasets sustanciales como WikiText y OpenWebText.
    """

    def __init__(self, config: DataPipelineConfig):
        self.config = config
        self.datasets: Dict[str, Dataset] = {}
        self.combined_dataset: Optional[Dataset] = None
        self._setup_cache_dir()

        logger.info("🚀 Inicializando RealDataPipeline")
        logger.info(f"   Datasets: {self.config.datasets}")
        logger.info(f"   Cache dir: {self.config.cache_dir}")
        logger.info(f"   Streaming: {self.config.streaming}")

    def _setup_cache_dir(self):
        """Configurar directorio de cache."""
        if self.config.cache_dir is None:
            self.config.cache_dir = os.path.join(tempfile.gettempdir(), "ailoos_real_data_cache")
        os.makedirs(self.config.cache_dir, exist_ok=True)

    def load_datasets(self) -> Dict[str, Dataset]:
        """
        Cargar datasets reales desde Hugging Face.
        Returns:
            Dict con datasets cargados
        """
        logger.info("📥 Cargando datasets reales...")

        for dataset_name in self.config.datasets:
            try:
                logger.info(f"   Cargando {dataset_name}...")

                # Configuración específica del dataset
                config_name = self.config.dataset_configs.get(dataset_name)

                # Cargar dataset
                if config_name:
                    dataset = load_dataset(
                        dataset_name,
                        config_name,
                        cache_dir=self.config.cache_dir,
                        streaming=self.config.streaming
                    )
                else:
                    dataset = load_dataset(
                        dataset_name,
                        cache_dir=self.config.cache_dir,
                        streaming=self.config.streaming
                    )

                # Si es DatasetDict, tomar el split de train
                if isinstance(dataset, DatasetDict):
                    if "train" in dataset:
                        dataset = dataset["train"]
                    else:
                        # Concatenar todos los splits disponibles
                        splits = list(dataset.keys())
                        logger.info(f"   Concatenando splits: {splits}")
                        dataset = concatenate_datasets([dataset[split] for split in splits])

                # Limitar muestras si especificado
                if self.config.max_samples_per_dataset and not self.config.streaming:
                    dataset = dataset.select(range(min(self.config.max_samples_per_dataset, len(dataset))))

                self.datasets[dataset_name] = dataset
                logger.info(f"   ✅ {dataset_name}: {len(dataset) if not self.config.streaming else 'streaming'} muestras")

            except Exception as e:
                logger.error(f"❌ Error cargando {dataset_name}: {e}")
                continue

        logger.info(f"✅ Cargados {len(self.datasets)} datasets")
        return self.datasets

    def preprocess_dataset(self, dataset: Dataset) -> Dataset:
        """
        Preprocesar dataset: filtrar y limpiar texto.
        """
        def filter_function(example):
            text = example.get(self.config.text_column, "")
            if not isinstance(text, str):
                return False
            length = len(text.strip())
            return self.config.min_text_length <= length <= self.config.max_text_length

        def clean_function(example):
            text = example.get(self.config.text_column, "")
            # Limpieza básica
            text = text.strip()
            # Remover líneas vacías múltiples
            text = "\n".join([line for line in text.split("\n") if line.strip()])
            example[self.config.text_column] = text
            return example

        logger.info("🧹 Preprocesando dataset...")

        # Filtrar
        original_size = len(dataset) if not self.config.streaming else "streaming"
        dataset = dataset.filter(filter_function, num_proc=self.config.num_proc)
        filtered_size = len(dataset) if not self.config.streaming else "streaming"
        logger.info(f"   Filtrado: {original_size} -> {filtered_size}")

        # Limpiar
        dataset = dataset.map(clean_function, num_proc=self.config.num_proc)
        logger.info("   ✅ Preprocesamiento completado")

        return dataset

    def combine_datasets(self) -> Dataset:
        """
        Combinar todos los datasets cargados en uno solo.
        """
        if not self.datasets:
            raise ValueError("No hay datasets cargados. Ejecuta load_datasets() primero.")

        logger.info("🔗 Combinando datasets...")

        datasets_list = list(self.datasets.values())

        if len(datasets_list) == 1:
            self.combined_dataset = datasets_list[0]
        else:
            self.combined_dataset = concatenate_datasets(datasets_list)

        logger.info(f"✅ Dataset combinado: {len(self.combined_dataset) if not self.config.streaming else 'streaming'} muestras")
        return self.combined_dataset

    def get_dataset_info(self) -> Dict[str, Any]:
        """Obtener información del dataset."""
        info = {
            "num_datasets": len(self.datasets),
            "datasets": list(self.datasets.keys()),
            "streaming": self.config.streaming,
            "cache_dir": self.config.cache_dir
        }

        if self.combined_dataset and not self.config.streaming:
            info["total_samples"] = len(self.combined_dataset)
            info["sample_text"] = self.combined_dataset[0][self.config.text_column][:200] + "..."

        return info

    def save_dataset(self, output_path: str, format: str = "parquet"):
        """
        Guardar el dataset combinado en disco.
        """
        if not self.combined_dataset:
            raise ValueError("No hay dataset combinado. Ejecuta combine_datasets() primero.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"💾 Guardando dataset en {output_path}")

        if format == "parquet":
            self.combined_dataset.to_parquet(str(output_path))
        elif format == "json":
            self.combined_dataset.to_json(str(output_path))
        else:
            raise ValueError(f"Formato no soportado: {format}")

        logger.info("✅ Dataset guardado")

    def load_from_disk(self, input_path: str) -> Dataset:
        """
        Cargar dataset desde disco.
        """
        from datasets import load_from_disk as hf_load_from_disk

        logger.info(f"📂 Cargando dataset desde {input_path}")
        dataset = hf_load_from_disk(input_path)
        self.combined_dataset = dataset
        logger.info(f"✅ Dataset cargado: {len(dataset)} muestras")
        return dataset


def create_real_data_pipeline(
    datasets: List[str] = None,
    cache_dir: str = None,
    max_samples: int = None,
    streaming: bool = False
) -> RealDataPipeline:
    """
    Factory function para crear pipeline de datos reales.
    """
    if datasets is None:
        datasets = ["wikitext", "openwebtext"]

    config = DataPipelineConfig(
        datasets=datasets,
        cache_dir=cache_dir,
        max_samples_per_dataset=max_samples,
        streaming=streaming
    )

    return RealDataPipeline(config)


# Función de conveniencia para uso rápido
def load_real_datasets(
    output_dir: str = "./real_datasets",
    datasets: List[str] = None,
    max_samples: int = 10000
) -> Dataset:
    """
    Cargar y guardar datasets reales de forma conveniente.
    """
    pipeline = create_real_data_pipeline(
        datasets=datasets,
        max_samples=max_samples,
        streaming=False
    )

    # Cargar
    pipeline.load_datasets()

    # Preprocesar individualmente
    for name, dataset in pipeline.datasets.items():
        pipeline.datasets[name] = pipeline.preprocess_dataset(dataset)

    # Combinar
    combined = pipeline.combine_datasets()

    # Guardar
    output_path = Path(output_dir) / "combined_dataset.parquet"
    pipeline.save_dataset(str(output_path))

    return combined