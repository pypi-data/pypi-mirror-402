"""
Dataset Sharding para EmpoorioLM - FASE REAL-5
Particionamiento de datasets para entrenamiento federado.
Soporta sharding por nodos, estratificación y balanceo.
"""

import os
import logging
import hashlib
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import random

import torch
from datasets import Dataset, DatasetDict
import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


@dataclass
class ShardingConfig:
    """Configuración del sharding de datasets."""
    num_shards: int = 10
    shard_size: Optional[int] = None  # Si None, dividir equitativamente
    random_seed: int = 42
    stratify_column: Optional[str] = None  # Columna para estratificación
    balance_shards: bool = True  # Balancear tamaños de shards
    overlap_factor: float = 0.0  # Factor de overlap entre shards (0.0 = sin overlap)
    validation_split: float = 0.1  # Proporción para validación
    test_split: float = 0.05  # Proporción para test
    shard_dir: str = "./shards"
    save_metadata: bool = True


class DatasetShard:
    """
    Representa un shard individual del dataset.
    """

    def __init__(self, data: Dataset, shard_id: int, metadata: Dict[str, Any]):
        self.data = data
        self.shard_id = shard_id
        self.metadata = metadata

    @property
    def size(self) -> int:
        """Tamaño del shard."""
        return len(self.data)

    def save(self, output_dir: str):
        """Guardar shard en disco."""
        output_path = Path(output_dir) / f"shard_{self.shard_id}"
        output_path.mkdir(parents=True, exist_ok=True)

        # Guardar datos
        self.data.save_to_disk(str(output_path / "data"))

        # Guardar metadata
        with open(output_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"💾 Shard {self.shard_id} guardado en {output_path}")

    @classmethod
    def load(cls, shard_path: str) -> 'DatasetShard':
        """Cargar shard desde disco."""
        shard_path = Path(shard_path)

        # Cargar datos
        data_path = shard_path / "data"
        data = Dataset.load_from_disk(str(data_path))

        # Cargar metadata
        metadata_path = shard_path / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        shard_id = metadata["shard_id"]
        return cls(data, shard_id, metadata)


class FederatedDatasetSharder:
    """
    Sharder para datasets federados.
    Divide datasets en shards para nodos federados.
    """

    def __init__(self, config: ShardingConfig):
        self.config = config
        self.shards: List[DatasetShard] = []
        self.metadata: Dict[str, Any] = {}

        # Crear directorio de shards
        Path(self.config.shard_dir).mkdir(parents=True, exist_ok=True)

        logger.info("🔀 FederatedDatasetSharder inicializado")
        logger.info(f"   Num shards: {config.num_shards}")
        logger.info(f"   Shard dir: {config.shard_dir}")

    def _calculate_shard_sizes(self, total_size: int) -> List[int]:
        """Calcular tamaños de cada shard."""
        if self.config.shard_size is not None:
            # Tamaño fijo por shard
            shard_sizes = [self.config.shard_size] * self.config.num_shards
            # Ajustar último shard si es necesario
            total_assigned = sum(shard_sizes)
            if total_assigned > total_size:
                # Reducir proporcionalmente
                factor = total_size / total_assigned
                shard_sizes = [int(size * factor) for size in shard_sizes]
            elif total_assigned < total_size:
                # Añadir al último shard
                shard_sizes[-1] += total_size - total_assigned
        else:
            # Dividir equitativamente
            base_size = total_size // self.config.num_shards
            remainder = total_size % self.config.num_shards
            shard_sizes = [base_size] * self.config.num_shards
            for i in range(remainder):
                shard_sizes[i] += 1

        return shard_sizes

    def _stratified_split(self, dataset: Dataset) -> List[Dataset]:
        """Dividir dataset de forma estratificada."""
        if not self.config.stratify_column:
            # Split simple
            indices = list(range(len(dataset)))
            random.seed(self.config.random_seed)
            random.shuffle(indices)

            shard_sizes = self._calculate_shard_sizes(len(dataset))
            shards = []
            start_idx = 0

            for size in shard_sizes:
                end_idx = start_idx + size
                shard_indices = indices[start_idx:end_idx]
                shard_data = dataset.select(shard_indices)
                shards.append(shard_data)
                start_idx = end_idx

            return shards

        # Stratified split
        stratify_values = dataset[self.config.stratify_column]
        unique_values = list(set(stratify_values))

        shards = []
        for _ in range(self.config.num_shards):
            shards.append([])

        # Distribuir muestras por valor estratificado
        for value in unique_values:
            value_indices = [i for i, v in enumerate(stratify_values) if v == value]
            random.seed(self.config.random_seed)
            random.shuffle(value_indices)

            # Distribuir entre shards
            for i, idx in enumerate(value_indices):
                shard_idx = i % self.config.num_shards
                shards[shard_idx].append(idx)

        # Convertir índices a datasets
        shard_datasets = []
        for shard_indices in shards:
            if shard_indices:
                shard_data = dataset.select(shard_indices)
            else:
                # Shard vacío, crear dataset vacío
                shard_data = dataset.select([]) if len(dataset) > 0 else dataset
            shard_datasets.append(shard_data)

        return shard_datasets

    def _add_overlap(self, shards: List[Dataset]) -> List[Dataset]:
        """Añadir overlap entre shards."""
        if self.config.overlap_factor <= 0:
            return shards

        overlapped_shards = []
        total_size = sum(len(shard) for shard in shards)

        for i, shard in enumerate(shards):
            overlap_size = int(len(shard) * self.config.overlap_factor)

            # Obtener muestras de overlap de shards adyacentes
            overlap_samples = []

            # Overlap con shard anterior
            prev_idx = (i - 1) % len(shards)
            prev_shard = shards[prev_idx]
            if len(prev_shard) > 0:
                prev_overlap = min(overlap_size // 2, len(prev_shard))
                prev_samples = prev_shard.select(range(len(prev_shard) - prev_overlap, len(prev_shard)))
                overlap_samples.extend(prev_samples)

            # Overlap con shard siguiente
            next_idx = (i + 1) % len(shards)
            next_shard = shards[next_idx]
            if len(next_shard) > 0:
                next_overlap = min(overlap_size // 2, len(next_shard))
                next_samples = next_shard.select(range(next_overlap))
                overlap_samples.extend(next_samples)

            # Combinar shard original con overlap
            if overlap_samples:
                overlap_dataset = Dataset.from_list(overlap_samples)
                combined_shard = Dataset.concatenate([shard, overlap_dataset])
            else:
                combined_shard = shard

            overlapped_shards.append(combined_shard)

        return overlapped_shards

    def shard_dataset(self, dataset: Dataset) -> List[DatasetShard]:
        """
        Dividir dataset en shards.
        """
        logger.info("🔀 Shardeando dataset...")

        # Crear splits train/val/test si configurado
        if self.config.validation_split > 0 or self.config.test_split > 0:
            dataset = self._create_splits(dataset)

        # Sharding principal
        if self.config.stratify_column:
            shard_datasets = self._stratified_split(dataset)
        else:
            shard_datasets = self._stratified_split(dataset)

        # Añadir overlap si configurado
        if self.config.overlap_factor > 0:
            shard_datasets = self._add_overlap(shard_datasets)

        # Crear objetos DatasetShard
        self.shards = []
        for i, shard_data in enumerate(shard_datasets):
            metadata = {
                "shard_id": i,
                "size": len(shard_data),
                "total_shards": self.config.num_shards,
                "stratify_column": self.config.stratify_column,
                "overlap_factor": self.config.overlap_factor,
                "validation_split": self.config.validation_split,
                "test_split": self.config.test_split,
                "random_seed": self.config.random_seed
            }

            shard = DatasetShard(shard_data, i, metadata)
            self.shards.append(shard)

        # Guardar metadata global
        self._save_global_metadata(dataset)

        logger.info(f"✅ Sharding completado: {len(self.shards)} shards")
        for shard in self.shards:
            logger.info(f"   Shard {shard.shard_id}: {shard.size} muestras")

        return self.shards

    def _create_splits(self, dataset: Dataset) -> Dataset:
        """Crear splits train/val/test."""
        # Solo mantener train para sharding
        if "train" in dataset.column_names or isinstance(dataset, DatasetDict):
            if isinstance(dataset, DatasetDict):
                dataset = dataset["train"]

        # Crear split de validación y test
        if self.config.test_split > 0:
            train_val, test = train_test_split(
                range(len(dataset)),
                test_size=self.config.test_split,
                random_state=self.config.random_seed
            )
        else:
            train_val = range(len(dataset))
            test = []

        if self.config.validation_split > 0:
            val_size = self.config.validation_split / (1 - self.config.test_split)
            train_indices, val_indices = train_test_split(
                train_val,
                test_size=val_size,
                random_state=self.config.random_seed
            )
        else:
            train_indices = train_val
            val_indices = []

        # Guardar splits
        if val_indices:
            val_dataset = dataset.select(val_indices)
            val_dataset.save_to_disk(str(Path(self.config.shard_dir) / "validation"))

        if test:
            test_dataset = dataset.select(test)
            test_dataset.save_to_disk(str(Path(self.config.shard_dir) / "test"))

        # Retornar solo train para sharding
        train_dataset = dataset.select(train_indices)
        return train_dataset

    def _save_global_metadata(self, original_dataset: Dataset):
        """Guardar metadata global del sharding."""
        if not self.config.save_metadata:
            return

        metadata = {
            "num_shards": len(self.shards),
            "total_samples": sum(shard.size for shard in self.shards),
            "original_dataset_size": len(original_dataset),
            "config": {
                "num_shards": self.config.num_shards,
                "stratify_column": self.config.stratify_column,
                "balance_shards": self.config.balance_shards,
                "overlap_factor": self.config.overlap_factor,
                "validation_split": self.config.validation_split,
                "test_split": self.config.test_split,
                "random_seed": self.config.random_seed
            },
            "shards": [
                {
                    "id": shard.shard_id,
                    "size": shard.size,
                    "metadata": shard.metadata
                }
                for shard in self.shards
            ]
        }

        metadata_path = Path(self.config.shard_dir) / "sharding_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"📋 Metadata guardada en {metadata_path}")

    def save_all_shards(self):
        """Guardar todos los shards."""
        for shard in self.shards:
            shard.save(self.config.shard_dir)

    def load_shard(self, shard_id: int) -> DatasetShard:
        """Cargar un shard específico."""
        shard_path = Path(self.config.shard_dir) / f"shard_{shard_id}"
        return DatasetShard.load(str(shard_path))

    def get_sharding_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sharding."""
        if not self.shards:
            return {}

        sizes = [shard.size for shard in self.shards]
        return {
            "num_shards": len(self.shards),
            "total_samples": sum(sizes),
            "avg_shard_size": np.mean(sizes),
            "min_shard_size": np.min(sizes),
            "max_shard_size": np.max(sizes),
            "shard_sizes": sizes
        }


def create_federated_sharder(
    num_shards: int = 10,
    shard_dir: str = "./shards",
    stratify_column: Optional[str] = None,
    validation_split: float = 0.1
) -> FederatedDatasetSharder:
    """
    Factory function para crear sharder federado.
    """
    config = ShardingConfig(
        num_shards=num_shards,
        shard_dir=shard_dir,
        stratify_column=stratify_column,
        validation_split=validation_split
    )

    return FederatedDatasetSharder(config)


def shard_real_dataset(
    dataset: Dataset,
    num_shards: int = 10,
    output_dir: str = "./shards",
    save_shards: bool = True
) -> List[DatasetShard]:
    """
    Función de conveniencia para shardear dataset real.
    """
    sharder = create_federated_sharder(num_shards=num_shards, shard_dir=output_dir)
    shards = sharder.shard_dataset(dataset)

    if save_shards:
        sharder.save_all_shards()

    return shards