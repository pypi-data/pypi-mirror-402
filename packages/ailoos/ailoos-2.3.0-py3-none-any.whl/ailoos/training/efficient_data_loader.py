"""
Efficient DataLoader para EmpoorioLM - FASE REAL-5
DataLoader optimizado para entrenamiento distribuido con prefetching y caching.
Soporta datasets grandes y entrenamiento federado.
"""

import os
import logging
import threading
from typing import Dict, List, Optional, Iterator, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import time

import torch
from torch.utils.data import DataLoader, DistributedSampler, Dataset
import torch.distributed as dist
from datasets import Dataset as HFDataset
import numpy as np
from cachetools import LRUCache, cached

logger = logging.getLogger(__name__)


@dataclass
class DataLoaderConfig:
    """Configuración del DataLoader eficiente."""
    batch_size: int = 8
    max_length: int = 512
    prefetch_factor: int = 2
    num_workers: int = 4
    pin_memory: bool = True
    persistent_workers: bool = True
    cache_size: int = 1000  # Tamaño del cache LRU
    shuffle: bool = True
    drop_last: bool = True
    distributed: bool = False
    world_size: int = 1
    rank: int = 0


class CachedDataset(Dataset):
    """
    Dataset con caching LRU para evitar recálculos.
    """

    def __init__(self, hf_dataset: HFDataset, tokenizer: Any, config: DataLoaderConfig):
        self.hf_dataset = hf_dataset
        self.tokenizer = tokenizer
        self.config = config
        self.cache = LRUCache(maxsize=config.cache_size)

        # Estadísticas
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"📦 CachedDataset inicializado con cache_size={config.cache_size}")

    def __len__(self):
        return len(self.hf_dataset)

    def __getitem__(self, idx):
        # Verificar cache
        if idx in self.cache:
            self.cache_hits += 1
            return self.cache[idx]

        self.cache_misses += 1

        # Obtener texto del dataset
        text = self.hf_dataset[idx]["text"]

        # Tokenizar
        tokens = self.tokenizer.encode(
            text,
            max_length=self.config.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )

        # Crear labels (para causal LM, labels = input_ids)
        labels = tokens.clone()

        # Crear máscara de atención (1 para tokens reales, 0 para padding)
        attention_mask = (tokens != self.tokenizer.pad_token_id).long()

        sample = {
            "input_ids": tokens.squeeze(),
            "attention_mask": attention_mask.squeeze(),
            "labels": labels.squeeze()
        }

        # Cachear
        self.cache[idx] = sample

        return sample

    def get_cache_stats(self) -> Dict[str, int]:
        """Obtener estadísticas del cache."""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }


class PrefetchDataLoader:
    """
    DataLoader con prefetching avanzado para datasets grandes.
    """

    def __init__(self, dataset: CachedDataset, config: DataLoaderConfig):
        self.dataset = dataset
        self.config = config
        self.prefetch_buffer = []
        self.prefetch_thread = None
        self.stop_prefetch = False
        self.buffer_lock = threading.Lock()

        # Inicializar prefetch
        self._start_prefetch()

    def _prefetch_worker(self):
        """Worker thread para prefetching."""
        batch_idx = 0
        while not self.stop_prefetch:
            try:
                with self.buffer_lock:
                    buffer_size = len(self.prefetch_buffer)

                # Si buffer no está lleno, prefetch más batches
                if buffer_size < self.config.prefetch_factor:
                    # Obtener índices del próximo batch
                    start_idx = batch_idx * self.config.batch_size
                    end_idx = min(start_idx + self.config.batch_size, len(self.dataset))

                    if start_idx >= len(self.dataset):
                        break

                    batch_indices = list(range(start_idx, end_idx))

                    # Prefetch batch
                    batch = []
                    for idx in batch_indices:
                        sample = self.dataset[idx]
                        batch.append(sample)

                    # Convertir a batch tensors
                    batch_data = self._collate_batch(batch)

                    with self.buffer_lock:
                        self.prefetch_buffer.append(batch_data)

                    batch_idx += 1

                else:
                    # Buffer lleno, esperar un poco
                    time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error en prefetch worker: {e}")
                break

    def _collate_batch(self, batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """Collate function para batches."""
        input_ids = torch.stack([item["input_ids"] for item in batch])
        attention_mask = torch.stack([item["attention_mask"] for item in batch])
        labels = torch.stack([item["labels"] for item in batch])

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }

    def _start_prefetch(self):
        """Iniciar prefetching."""
        self.prefetch_thread = threading.Thread(target=self._prefetch_worker, daemon=True)
        self.prefetch_thread.start()
        logger.info("🚀 Prefetching iniciado")

    def __iter__(self):
        return self

    def __next__(self):
        """Obtener próximo batch del buffer."""
        while True:
            with self.buffer_lock:
                if self.prefetch_buffer:
                    return self.prefetch_buffer.pop(0)

            # Buffer vacío, esperar
            time.sleep(0.001)

    def __len__(self):
        return len(self.dataset) // self.config.batch_size

    def stop(self):
        """Detener prefetching."""
        self.stop_prefetch = True
        if self.prefetch_thread:
            self.prefetch_thread.join(timeout=1.0)
        logger.info("🛑 Prefetching detenido")


class EfficientDataLoader:
    """
    DataLoader eficiente optimizado para entrenamiento distribuido.
    Combina caching, prefetching y soporte distribuido.
    """

    def __init__(self, hf_dataset: HFDataset, tokenizer: Any, config: DataLoaderConfig):
        self.config = config
        self.tokenizer = tokenizer

        # Crear dataset con cache
        self.cached_dataset = CachedDataset(hf_dataset, tokenizer, config)

        # Configurar sampler distribuido si es necesario
        self.sampler = None
        if config.distributed:
            self.sampler = DistributedSampler(
                self.cached_dataset,
                num_replicas=config.world_size,
                rank=config.rank,
                shuffle=config.shuffle,
                drop_last=config.drop_last
            )

        # Crear DataLoader base de PyTorch
        self.base_dataloader = DataLoader(
            self.cached_dataset,
            batch_size=config.batch_size,
            sampler=self.sampler,
            shuffle=config.shuffle if not config.distributed else False,
            num_workers=config.num_workers,
            pin_memory=config.pin_memory,
            persistent_workers=config.persistent_workers,
            prefetch_factor=config.prefetch_factor,
            drop_last=config.drop_last
        )

        # Crear prefetch loader avanzado
        self.prefetch_loader = PrefetchDataLoader(self.cached_dataset, config)

        logger.info("⚡ EfficientDataLoader inicializado")
        logger.info(f"   Batch size: {config.batch_size}")
        logger.info(f"   Distributed: {config.distributed}")
        logger.info(f"   Workers: {config.num_workers}")
        logger.info(f"   Prefetch: {config.prefetch_factor}")

    def __iter__(self):
        """Iterar usando prefetch loader."""
        return iter(self.prefetch_loader)

    def __len__(self):
        return len(self.prefetch_loader)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        return self.cached_dataset.get_cache_stats()

    def get_dataloader_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del dataloader."""
        return {
            "dataset_size": len(self.cached_dataset),
            "batch_size": self.config.batch_size,
            "num_batches": len(self),
            "distributed": self.config.distributed,
            "world_size": self.config.world_size,
            "rank": self.config.rank,
            "cache_stats": self.get_cache_stats()
        }


def create_efficient_dataloader(
    hf_dataset: HFDataset,
    tokenizer: Any,
    batch_size: int = 8,
    max_length: int = 512,
    distributed: bool = False,
    world_size: int = 1,
    rank: int = 0,
    num_workers: int = 4,
    cache_size: int = 1000
) -> EfficientDataLoader:
    """
    Factory function para crear DataLoader eficiente.
    """
    config = DataLoaderConfig(
        batch_size=batch_size,
        max_length=max_length,
        distributed=distributed,
        world_size=world_size,
        rank=rank,
        num_workers=num_workers,
        cache_size=cache_size
    )

    return EfficientDataLoader(hf_dataset, tokenizer, config)


def setup_distributed_dataloader(
    hf_dataset: HFDataset,
    tokenizer: Any,
    batch_size: int = 8
) -> EfficientDataLoader:
    """
    Configurar DataLoader para entrenamiento distribuido.
    Detecta automáticamente configuración distribuida.
    """
    if not dist.is_initialized():
        raise RuntimeError("Distributed training not initialized")

    world_size = dist.get_world_size()
    rank = dist.get_rank()

    return create_efficient_dataloader(
        hf_dataset=hf_dataset,
        tokenizer=tokenizer,
        batch_size=batch_size,
        distributed=True,
        world_size=world_size,
        rank=rank
    )