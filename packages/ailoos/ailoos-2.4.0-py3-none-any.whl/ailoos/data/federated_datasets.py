"""
Pipeline de Datasets Federados para EmpoorioLM
Sistema de gestión de datos masivos para entrenamiento federado distribuido.
"""

import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Any, Optional, Tuple, Iterator
import json
import os
import hashlib
from pathlib import Path
import asyncio
import aiohttp
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class FederatedDatasetConfig:
    """Configuración para datasets federados."""

    # Configuración básica
    max_seq_length: int = 512
    vocab_size: int = 50257  # GPT-2 vocab size
    batch_size: int = 8
    num_workers: int = 2

    # Configuración federada
    min_samples_per_node: int = 1000
    max_samples_per_node: int = 10000
    data_sharding_strategy: str = "random"  # random, stratified, sequential

    # Configuración de calidad
    min_text_length: int = 10
    max_text_length: int = 10000
    quality_filter_enabled: bool = True

    # Configuración de privacidad
    enable_differential_privacy: bool = False
    dp_epsilon: float = 1.0
    dp_delta: float = 1e-5


class FederatedTextDataset(Dataset):
    """
    Dataset de texto para entrenamiento federado.
    Maneja particiones de datos para nodos individuales.
    """

    def __init__(
        self,
        texts: List[str],
        tokenizer=None,
        max_length: int = 512,
        node_id: Optional[str] = None
    ):
        """
        Args:
            texts: Lista de textos para este nodo
            tokenizer: Tokenizador (None para raw text)
            max_length: Longitud máxima de secuencia
            node_id: ID del nodo (para logging)
        """
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.node_id = node_id or "unknown"

        # Estadísticas del dataset
        self.stats = {
            "total_samples": len(texts),
            "avg_text_length": sum(len(t.split()) for t in texts) / len(texts) if texts else 0,
            "node_id": self.node_id
        }

        logger.info(f"📊 Dataset creado para nodo {self.node_id}: {self.stats['total_samples']} muestras")

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        text = self.texts[idx]

        if self.tokenizer:
            # Tokenizar el texto
            tokens = self.tokenizer.encode(text, max_length=self.max_length, truncation=True)

            # Crear input_ids y labels (para causal LM)
            input_ids = torch.tensor(tokens, dtype=torch.long)
            labels = input_ids.clone()

            # Padding si es necesario
            if len(input_ids) < self.max_length:
                pad_length = self.max_length - len(input_ids)
                input_ids = torch.cat([input_ids, torch.zeros(pad_length, dtype=torch.long)])
                labels = torch.cat([labels, torch.full((pad_length,), -100, dtype=torch.long)])

            return {
                "input_ids": input_ids,
                "labels": labels,
                "attention_mask": (input_ids != 0).long(),
                "text": text
            }
        else:
            # Retornar texto crudo
            return {"text": text}


class FederatedDatasetManager:
    """
    Gestor central de datasets federados para EmpoorioLM.
    Coordina la distribución de datos entre nodos.
    """

    def __init__(self, config: FederatedDatasetConfig):
        self.config = config
        self.datasets = {}
        self.node_partitions = {}
        self.global_stats = {}

        # Crear directorio de datos si no existe
        self.data_dir = Path("./data/federated")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("🎯 FederatedDatasetManager inicializado")

    def load_global_dataset(self, data_source: str) -> List[str]:
        """
        Carga dataset global desde diferentes fuentes.

        Args:
            data_source: URL, path local, o identificador de dataset

        Returns:
            Lista de textos
        """
        logger.info(f"📥 Cargando dataset global desde: {data_source}")

        if data_source.startswith("http"):
            # Cargar desde URL
            return self._load_from_url(data_source)
        elif os.path.isfile(data_source):
            # Cargar desde archivo local
            return self._load_from_file(data_source)
        elif data_source.startswith("huggingface://"):
            # Cargar desde HuggingFace
            return self._load_from_huggingface(data_source)
        else:
            raise ValueError(f"Fuente de datos no soportada: {data_source}")

    def _load_from_file(self, file_path: str) -> List[str]:
        """Carga datos desde archivo local."""
        texts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.jsonl'):
                for line in f:
                    data = json.loads(line.strip())
                    if 'text' in data:
                        texts.append(data['text'])
            else:
                # Asumir archivo de texto plano
                content = f.read()
                # Dividir en párrafos o oraciones
                paragraphs = content.split('\n\n')
                texts = [p.strip() for p in paragraphs if len(p.strip()) > self.config.min_text_length]

        logger.info(f"✅ Cargado {len(texts)} textos desde archivo")
        return texts

    async def _load_from_url_async(self, url: str) -> List[str]:
        """Carga datos desde URL de forma asíncrona."""
        try:
            logger.info(f"🌐 Descargando datos desde: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status != 200:
                        raise ValueError(f"Error HTTP {response.status} al descargar {url}")

                    content = await response.text()

                    # Determinar tipo de contenido
                    content_type = response.headers.get('content-type', '').lower()

                    if 'json' in content_type:
                        # JSON array de textos
                        data = json.loads(content)
                        if isinstance(data, list):
                            texts = [item.get('text', str(item)) if isinstance(item, dict) else str(item) for item in data]
                        else:
                            raise ValueError("JSON debe ser un array")

                    elif url.endswith('.jsonl'):
                        # JSON Lines format
                        texts = []
                        for line in content.strip().split('\n'):
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if 'text' in data:
                                        texts.append(data['text'])
                                except json.JSONDecodeError:
                                    continue

                    else:
                        # Texto plano - dividir en párrafos
                        paragraphs = content.split('\n\n')
                        texts = [p.strip() for p in paragraphs if len(p.strip()) > self.config.min_text_length]

                    # Aplicar filtros de calidad
                    if self.config.quality_filter_enabled:
                        texts = [
                            t for t in texts
                            if self.config.min_text_length <= len(t) <= self.config.max_text_length
                        ]

                    logger.info(f"✅ Descargados {len(texts)} textos desde {url}")
                    return texts

        except Exception as e:
            logger.error(f"❌ Error descargando desde {url}: {e}")
            return []

    def _load_from_url(self, url: str) -> List[str]:
        """Carga datos desde URL (wrapper síncrono)."""
        # Ejecutar la versión asíncrona en un loop de eventos
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._load_from_url_async(url))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ Error en carga síncrona desde URL: {e}")
            return []

    def _load_from_huggingface(self, hf_path: str) -> List[str]:
        """Carga datos desde HuggingFace."""
        try:
            from datasets import load_dataset
            import tempfile
            import os

            # Parsear path de HuggingFace (huggingface://dataset_name/config/split)
            path_parts = hf_path.replace("huggingface://", "").split("/")
            dataset_name = path_parts[0]
            config = path_parts[1] if len(path_parts) > 1 else None
            split = path_parts[2] if len(path_parts) > 2 else "train"

            logger.info(f"🤗 Cargando dataset HuggingFace: {dataset_name}")

            # Cargar dataset
            if config:
                dataset = load_dataset(dataset_name, config, split=split)
            else:
                dataset = load_dataset(dataset_name, split=split)

            texts = []

            # Extraer textos del dataset
            if hasattr(dataset, 'column_names'):
                # Determinar columna de texto
                text_column = None
                for col in ['text', 'content', 'document', 'body']:
                    if col in dataset.column_names:
                        text_column = col
                        break

                if text_column:
                    logger.info(f"📝 Usando columna de texto: {text_column}")

                    # Procesar en lotes para eficiencia
                    batch_size = 1000
                    for i in range(0, len(dataset), batch_size):
                        batch = dataset[i:i+batch_size]
                        batch_texts = batch[text_column]

                        # Filtrar y validar textos
                        for text in batch_texts:
                            if isinstance(text, str) and self.config.min_text_length <= len(text) <= self.config.max_text_length:
                                texts.append(text)

                        if len(texts) >= 10000:  # Límite para evitar datasets demasiado grandes
                            logger.warning("⚠️ Dataset limitado a 10,000 muestras")
                            break
                else:
                    logger.warning(f"⚠️ No se encontró columna de texto en {dataset.column_names}")
            else:
                logger.warning("⚠️ Dataset no tiene estructura esperada")

            logger.info(f"✅ Cargados {len(texts)} textos desde HuggingFace dataset {dataset_name}")
            return texts

        except ImportError:
            logger.error("❌ Librería 'datasets' no instalada. Instala con: pip install datasets")
            return []
        except Exception as e:
            logger.error(f"❌ Error cargando desde HuggingFace {hf_path}: {e}")
            return []

    def create_node_partitions(
        self,
        global_texts: List[str],
        num_nodes: int,
        strategy: str = "random"
    ) -> Dict[str, List[str]]:
        """
        Crea particiones de datos para cada nodo.

        Args:
            global_texts: Dataset global completo
            num_nodes: Número de nodos
            strategy: Estrategia de partición

        Returns:
            Diccionario de node_id -> lista de textos
        """
        logger.info(f"🔀 Creando particiones para {num_nodes} nodos usando estrategia: {strategy}")

        if strategy == "random":
            partitions = self._partition_random(global_texts, num_nodes)
        elif strategy == "stratified":
            partitions = self._partition_stratified(global_texts, num_nodes)
        elif strategy == "sequential":
            partitions = self._partition_sequential(global_texts, num_nodes)
        else:
            raise ValueError(f"Estrategia no soportada: {strategy}")

        # Validar particiones
        self._validate_partitions(partitions)

        self.node_partitions = partitions
        logger.info(f"✅ Particiones creadas: {[f'{k}:{len(v)}' for k,v in partitions.items()]}")
        return partitions

    def _partition_random(self, texts: List[str], num_nodes: int) -> Dict[str, List[str]]:
        """Partición aleatoria."""
        import random
        random.shuffle(texts)

        partition_size = len(texts) // num_nodes
        partitions = {}

        for i in range(num_nodes):
            start_idx = i * partition_size
            end_idx = start_idx + partition_size if i < num_nodes - 1 else len(texts)

            node_id = f"node_{i+1}"
            partitions[node_id] = texts[start_idx:end_idx]

        return partitions

    def _partition_stratified(self, texts: List[str], num_nodes: int) -> Dict[str, List[str]]:
        """Partición estratificada por longitud de texto."""
        # Ordenar por longitud
        sorted_texts = sorted(texts, key=len)

        partition_size = len(sorted_texts) // num_nodes
        partitions = {}

        for i in range(num_nodes):
            start_idx = i * partition_size
            end_idx = start_idx + partition_size if i < num_nodes - 1 else len(sorted_texts)

            node_id = f"node_{i+1}"
            partitions[node_id] = sorted_texts[start_idx:end_idx]

        return partitions

    def _partition_sequential(self, texts: List[str], num_nodes: int) -> Dict[str, List[str]]:
        """Partición secuencial."""
        partition_size = len(texts) // num_nodes
        partitions = {}

        for i in range(num_nodes):
            start_idx = i * partition_size
            end_idx = start_idx + partition_size if i < num_nodes - 1 else len(texts)

            node_id = f"node_{i+1}"
            partitions[node_id] = texts[start_idx:end_idx]

        return partitions

    def _validate_partitions(self, partitions: Dict[str, List[str]]):
        """Valida que las particiones cumplan con requisitos mínimos."""
        for node_id, texts in partitions.items():
            if len(texts) < self.config.min_samples_per_node:
                logger.warning(f"⚠️ Nodo {node_id} tiene pocos datos: {len(texts)} < {self.config.min_samples_per_node}")

            # Filtrar textos demasiado cortos o largos
            if self.config.quality_filter_enabled:
                filtered_texts = [
                    t for t in texts
                    if self.config.min_text_length <= len(t) <= self.config.max_text_length
                ]
                partitions[node_id] = filtered_texts

    def create_node_dataset(
        self,
        node_id: str,
        tokenizer=None
    ) -> FederatedTextDataset:
        """
        Crea dataset específico para un nodo.

        Args:
            node_id: ID del nodo
            tokenizer: Tokenizador opcional

        Returns:
            Dataset del nodo
        """
        if node_id not in self.node_partitions:
            raise ValueError(f"Nodo {node_id} no tiene partición asignada")

        texts = self.node_partitions[node_id]
        dataset = FederatedTextDataset(
            texts=texts,
            tokenizer=tokenizer,
            max_length=self.config.max_seq_length,
            node_id=node_id
        )

        self.datasets[node_id] = dataset
        return dataset

    def create_node_dataloader(
        self,
        node_id: str,
        tokenizer=None,
        shuffle: bool = True
    ) -> DataLoader:
        """
        Crea DataLoader para un nodo específico.

        Args:
            node_id: ID del nodo
            tokenizer: Tokenizador
            shuffle: Si barajar datos

        Returns:
            DataLoader configurado
        """
        dataset = self.create_node_dataset(node_id, tokenizer)

        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=self.config.num_workers,
            pin_memory=torch.cuda.is_available()
        )

        return dataloader

    def get_partition_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de las particiones."""
        stats = {
            "total_nodes": len(self.node_partitions),
            "total_samples": sum(len(texts) for texts in self.node_partitions.values()),
            "node_stats": {}
        }

        for node_id, texts in self.node_partitions.items():
            stats["node_stats"][node_id] = {
                "samples": len(texts),
                "avg_length": sum(len(t) for t in texts) / len(texts) if texts else 0,
                "min_length": min(len(t) for t in texts) if texts else 0,
                "max_length": max(len(t) for t in texts) if texts else 0
            }

        return stats

    def save_partitions(self, save_path: str):
        """Guarda las particiones en disco."""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "config": self.config.__dict__,
            "partitions": self.node_partitions,
            "stats": self.get_partition_stats()
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Particiones guardadas en {save_path}")

    def load_partitions(self, load_path: str):
        """Carga particiones desde disco."""
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.node_partitions = data["partitions"]
        logger.info(f"📂 Particiones cargadas desde {load_path}")


# Funciones de conveniencia
def create_federated_datasets(
    data_source: str,
    num_nodes: int,
    config: Optional[FederatedDatasetConfig] = None,
    strategy: str = "random"
) -> Tuple[FederatedDatasetManager, Dict[str, List[str]]]:
    """
    Función de conveniencia para crear datasets federados.

    Args:
        data_source: Fuente de datos
        num_nodes: Número de nodos
        config: Configuración opcional
        strategy: Estrategia de partición

    Returns:
        Tupla de (manager, partitions)
    """
    if config is None:
        config = FederatedDatasetConfig()

    manager = FederatedDatasetManager(config)

    # Cargar datos globales
    global_texts = manager.load_global_dataset(data_source)

    # Crear particiones
    partitions = manager.create_node_partitions(global_texts, num_nodes, strategy)

    return manager, partitions


if __name__ == "__main__":
    # Test del sistema de datasets federados
    print("🧪 Probando FederatedDatasetManager...")

    config = FederatedDatasetConfig()
    manager = FederatedDatasetManager(config)

    # Crear datos de prueba
    test_texts = [
        "Este es un texto de prueba para el nodo 1.",
        "Otro texto más largo con más contenido para probar el sistema.",
        "Texto corto.",
        "Un texto muy largo que contiene mucha información sobre diversos temas como inteligencia artificial, machine learning, deep learning, transformers, y otras tecnologías emergentes en el campo de la computación y la ciencia de datos." * 3
    ] * 100  # Multiplicar para tener más datos

    print(f"📊 Datos de prueba creados: {len(test_texts)} textos")

    # Crear particiones para 2 nodos
    partitions = manager.create_node_partitions(test_texts, 2, "random")

    # Mostrar estadísticas
    stats = manager.get_partition_stats()
    print(f"📈 Estadísticas: {stats}")

    print("✅ Sistema de datasets federados funcionando correctamente")