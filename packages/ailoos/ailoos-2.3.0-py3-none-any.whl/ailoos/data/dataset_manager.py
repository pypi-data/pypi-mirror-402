#!/usr/bin/env python3
"""
AILOOS Dataset Manager - Orquestador de Ciclo de Vida de Datasets
================================================================

Este módulo es el director de orquesta de la infraestructura de datos de AILOOS.
Coordina todo el flujo: desde archivos crudos hasta datasets listos para
entrenamiento federado distribuido.

Funciones principales:
- Procesamiento dual: archivos de texto y datasets JSON
- Fragmentación inteligente (sharding) por tamaño
- Sanitización integrada PII automática
- Subida automática a IPFS con registro
- Gestión completa del ciclo de vida
- Estadísticas detalladas y monitoreo

Arquitectura:
Archivo Crudo → PII Scrubber → Sharding → IPFS Upload → Registro → Dataset Listo
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import time
from datetime import datetime

from .ipfs_connector import ipfs_connector
from ..privacy.pii_scrubber import pii_scrubber
from .registry import DataRegistry, get_dataset_registry

# Instancia global del registro de datasets
data_registry = get_dataset_registry()

_dataset_manager: Optional["DatasetManager"] = None


def get_dataset_manager() -> "DatasetManager":
    """Return a shared dataset manager instance."""
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = DatasetManager()
    return _dataset_manager

logger = logging.getLogger(__name__)

class DatasetManager:
    """
    Orquestador completo del ciclo de vida de datasets.
    Gestiona desde archivos crudos hasta datasets federados.
    """

    def __init__(self):
        """Inicializa el Dataset Manager."""
        # Estadísticas del manager
        self.stats = {
            "datasets_processed": 0,
            "shards_created": 0,
            "total_data_size_mb": 0.0,
            "pii_instances_removed": 0,
            "processing_time_avg": 0.0,
            "last_activity": None
        }


    def process_text_file(self, file_path: str, dataset_name: str,
                         shard_size_mb: float = 10.0,
                         metadata: Optional[Dict] = None) -> Dict:
        """
        Procesa un archivo de texto completo.

        Args:
            file_path: Ruta al archivo de texto
            dataset_name: Nombre del dataset
            shard_size_mb: Tamaño máximo de cada shard en MB
            metadata: Metadatos adicionales

        Returns:
            Dict con información del procesamiento
        """
        start_time = time.time()

        logger.info(f"📄 Procesando archivo de texto: {file_path}")

        # Verificar que el archivo existe
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        # Leer archivo completo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_size = len(content.encode('utf-8'))

        # Paso 1: Sanitización PII
        logger.info("🧹 Aplicando sanitización PII...")
        scrubbed_content = pii_scrubber.scrub_text(content)
        pii_removed = content != scrubbed_content

        # Paso 2: Fragmentación (sharding)
        logger.info(f"✂️ Fragmentando en shards de {shard_size_mb}MB...")
        shards = self._create_text_shards(scrubbed_content, shard_size_mb)

        # Paso 3: Subida a IPFS y registro
        logger.info("📡 Subiendo shards a IPFS...")
        shard_cids = []
        total_size = 0

        for i, shard in enumerate(shards):
            # Crear manifest del shard
            shard_manifest = {
                "dataset_name": dataset_name,
                "shard_index": i,
                "total_shards": len(shards),
                "content": shard,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            # Subir a IPFS
            cid = ipfs_connector.add_json(shard_manifest)
            if cid:
                shard_cids.append(cid)
                logger.info(f"✅ Shard {i+1}/{len(shards)} subido: {cid}")
            else:
                logger.error(f"❌ Error subiendo shard {i+1}")
                continue

            total_size += len(shard.encode('utf-8'))

        # Paso 4: Crear registro maestro
        dataset_manifest = {
            "id": f"{dataset_name}_{int(time.time())}",
            "name": dataset_name,
            "type": "text_file",
            "original_file": file_path,
            "total_size_mb": total_size / (1024 * 1024),
            "num_shards": len(shard_cids),
            "shard_cids": shard_cids,
            "pii_scrubbed": pii_removed,
            "created_at": datetime.now().isoformat(),
            "quality_score": self._calculate_quality_score(scrubbed_content),
            "metadata": metadata or {},
            "processing_stats": {
                "original_size_bytes": original_size,
                "processed_size_bytes": total_size,
                "compression_ratio": total_size / max(original_size, 1),
                "processing_time_seconds": time.time() - start_time
            }
        }

        # Registrar dataset en el registro global
        data_registry.register_dataset(dataset_manifest)

        # Actualizar estadísticas
        processing_time = time.time() - start_time
        self.stats["datasets_processed"] += 1
        self.stats["shards_created"] += len(shard_cids)
        self.stats["total_data_size_mb"] += dataset_manifest["total_size_mb"]
        self.stats["processing_time_avg"] = (
            (self.stats["processing_time_avg"] * (self.stats["datasets_processed"] - 1)) +
            processing_time
        ) / self.stats["datasets_processed"]
        self.stats["last_activity"] = datetime.now().isoformat()

        result = {
            "dataset_name": dataset_name,
            "total_size_mb": dataset_manifest["total_size_mb"],
            "num_shards": len(shard_cids),
            "shard_cids": shard_cids,
            "pii_scrubbed": pii_removed,
            "quality_score": dataset_manifest["quality_score"],
            "processing_time": processing_time
        }

        logger.info(f"✅ Dataset procesado exitosamente: {dataset_name}")
        logger.info(f"   📊 Shards: {len(shard_cids)} | Tamaño: {dataset_manifest['total_size_mb']:.2f}MB")
        logger.info(f"   🧹 PII Scrubbed: {pii_removed} | Calidad: {dataset_manifest['quality_score']:.2f}")

        return result

    def process_json_dataset(self, data: List[Dict], dataset_name: str,
                           metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Procesa un dataset JSON (lista de registros).

        Args:
            data: Lista de diccionarios con los datos
            dataset_name: Nombre del dataset
            metadata: Metadatos adicionales

        Returns:
            Dict con información del procesamiento
        """
        start_time = time.time()

        logger.info(f"📊 Procesando dataset JSON: {dataset_name} ({len(data)} registros)")

        if not data:
            logger.warning("Dataset vacío, nada que procesar")
            return None

        # Paso 1: Sanitización PII
        logger.info("🧹 Aplicando sanitización PII al dataset...")
        scrubbed_data = pii_scrubber.scrub_dataset(data)

        # Paso 2: Crear shards por cantidad de registros
        logger.info("✂️ Organizando datos en shards...")
        shards = self._create_json_shards(scrubbed_data)

        # Paso 3: Subida a IPFS
        logger.info("📡 Subiendo shards a IPFS...")
        shard_cids = []
        total_size = 0

        for i, shard in enumerate(shards):
            shard_manifest = {
                "dataset_name": dataset_name,
                "shard_index": i,
                "total_shards": len(shards),
                "records": shard,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            cid = ipfs_connector.add_json(shard_manifest)
            if cid:
                shard_cids.append(cid)
                logger.info(f"✅ Shard {i+1}/{len(shards)} subido: {cid}")
            else:
                logger.error(f"❌ Error subiendo shard {i+1}")

            total_size += len(json.dumps(shard).encode('utf-8'))

        # Paso 4: Registro
        dataset_manifest = {
            "id": f"{dataset_name}_{int(time.time())}",
            "name": dataset_name,
            "type": "json_dataset",
            "total_records": len(data),
            "total_size_mb": total_size / (1024 * 1024),
            "num_shards": len(shard_cids),
            "shard_cids": shard_cids,
            "pii_scrubbed": True,  # JSON datasets siempre se limpian
            "created_at": datetime.now().isoformat(),
            "quality_score": self._calculate_json_quality_score(scrubbed_data),
            "metadata": metadata or {},
            "processing_stats": {
                "original_records": len(data),
                "processed_records": len(scrubbed_data),
                "processing_time_seconds": time.time() - start_time
            }
        }

        # Registrar dataset en el registro global
        data_registry.register_dataset(dataset_manifest)

        # Actualizar estadísticas
        processing_time = time.time() - start_time
        self.stats["datasets_processed"] += 1
        self.stats["shards_created"] += len(shard_cids)
        self.stats["total_data_size_mb"] += dataset_manifest["total_size_mb"]
        self.stats["processing_time_avg"] = (
            (self.stats["processing_time_avg"] * (self.stats["datasets_processed"] - 1)) +
            processing_time
        ) / self.stats["datasets_processed"]
        self.stats["last_activity"] = datetime.now().isoformat()

        result = {
            "dataset_name": dataset_name,
            "total_records": len(data),
            "total_size_mb": dataset_manifest["total_size_mb"],
            "num_shards": len(shard_cids),
            "shard_cids": shard_cids,
            "quality_score": dataset_manifest["quality_score"],
            "processing_time": processing_time
        }

        logger.info(f"✅ Dataset JSON procesado: {dataset_name}")
        logger.info(f"   📊 Registros: {len(data)} | Shards: {len(shard_cids)}")
        logger.info(f"   📏 Tamaño: {dataset_manifest['total_size_mb']:.2f}MB")

        return result

    def _create_text_shards(self, content: str, max_size_mb: float) -> List[str]:
        """
        Crea shards de texto por tamaño máximo.

        Args:
            content: Contenido completo
            max_size_mb: Tamaño máximo por shard en MB

        Returns:
            Lista de shards
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        shards = []

        # Dividir por párrafos o líneas para mantener coherencia
        paragraphs = content.split('\n\n')
        current_shard = ""

        for paragraph in paragraphs:
            # Calcular tamaño si añadimos este párrafo
            potential_size = len((current_shard + paragraph + '\n\n').encode('utf-8'))

            if potential_size > max_size_bytes and current_shard:
                # El shard actual está lleno
                shards.append(current_shard.strip())
                current_shard = paragraph + '\n\n'
            else:
                current_shard += paragraph + '\n\n'

        # Añadir el último shard
        if current_shard.strip():
            shards.append(current_shard.strip())

        # Si no se pudo dividir, crear al menos un shard
        if not shards:
            shards = [content]

        return shards

    def _create_json_shards(self, data: List[Dict], records_per_shard: int = 1000) -> List[List[Dict]]:
        """
        Crea shards de datos JSON por cantidad de registros.

        Args:
            data: Lista de registros
            records_per_shard: Registros por shard

        Returns:
            Lista de shards (cada uno es una lista de registros)
        """
        shards = []

        for i in range(0, len(data), records_per_shard):
            shard = data[i:i + records_per_shard]
            shards.append(shard)

        return shards

    def _calculate_quality_score(self, content: str) -> float:
        """
        Calcula una puntuación de calidad básica para contenido de texto.

        Args:
            content: Contenido a evaluar

        Returns:
            Puntuación de calidad (0.0 a 1.0)
        """
        if not content:
            return 0.0

        # Factores de calidad básicos
        length_score = min(len(content) / 10000, 1.0)  # Bonus por longitud
        diversity_score = len(set(content.split())) / len(content.split())  # Diversidad de vocabulario
        structure_score = 1.0 if '\n\n' in content else 0.5  # Bonus por estructura

        # Puntuación final (promedio ponderado)
        quality = (length_score * 0.4) + (diversity_score * 0.4) + (structure_score * 0.2)

        return round(min(max(quality, 0.0), 1.0), 2)

    def _calculate_json_quality_score(self, data: List[Dict]) -> float:
        """
        Calcula puntuación de calidad para datasets JSON.

        Args:
            data: Datos a evaluar

        Returns:
            Puntuación de calidad (0.0 a 1.0)
        """
        if not data:
            return 0.0

        # Factores para datasets JSON
        record_count = len(data)
        size_score = min(record_count / 1000, 1.0)  # Bonus por cantidad de registros

        # Verificar consistencia de campos
        if data:
            first_record = data[0]
            field_count = len(first_record.keys())
            consistency_score = sum(1 for record in data if len(record.keys()) == field_count) / len(data)
        else:
            consistency_score = 0.0

        # Puntuación final
        quality = (size_score * 0.6) + (consistency_score * 0.4)

        return round(min(max(quality, 0.0), 1.0), 2)


    def get_dataset_info(self, dataset_name: str) -> Optional[Dict]:
        """
        Obtiene información de un dataset registrado.

        Args:
            dataset_name: Nombre del dataset

        Returns:
            Información del dataset o None si no existe
        """
        # Buscar en el registro global
        datasets = data_registry.list_datasets()
        for dataset in datasets:
            if dataset.get("name") == dataset_name:
                return dataset
        return None

    def list_datasets(self) -> List[Dict]:
        """
        Lista todos los datasets registrados.

        Returns:
            Lista de datasets
        """
        return data_registry.list_datasets()

    def download_shard(self, cid: str, local_path: str) -> bool:
        """
        Descarga un shard específico a un archivo local.

        Args:
            cid: CID del shard en IPFS
            local_path: Ruta local donde guardar

        Returns:
            True si se descargó correctamente
        """
        try:
            data = ipfs_connector.get_json(cid)
            if data:
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Shard descargado: {cid} → {local_path}")
                return True
            else:
                logger.error(f"❌ Error descargando shard: {cid}")
                return False

        except Exception as e:
            logger.error(f"Error descargando shard {cid}: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del Dataset Manager.

        Returns:
            Dict con estadísticas
        """
        return self.stats.copy()

# Instancia global del manager
dataset_manager = DatasetManager()
