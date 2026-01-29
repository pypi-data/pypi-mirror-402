#!/usr/bin/env python3
"""
AILOOS Data Registry - Registro Central de Datasets
==================================================

Este módulo mantiene el inventario central de todos los datasets disponibles
en la red AILOOS. Actúa como el "catálogo" de datos que los nodos pueden
descubrir y utilizar para entrenamiento federado.

Funciones principales:
- Registro de nuevos datasets con metadatos completos
- Búsqueda y filtrado de datasets por dominio/categoría
- Seguimiento de calidad y disponibilidad
- Estadísticas de red y uso
- Validación de integridad de datasets

El registro es la "memoria institucional" de AILOOS.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

_data_registry: Optional["DataRegistry"] = None


def get_dataset_registry() -> "DataRegistry":
    """Return a shared dataset registry instance."""
    global _data_registry
    if _data_registry is None:
        _data_registry = DataRegistry()
    return _data_registry

class DataRegistry:
    """
    Registro central de datasets disponibles en la red AILOOS.
    Mantiene el inventario de qué datos existen, dónde están (IPFS CIDs)
    y sus metadatos (dominio, tamaño, precio).
    """

    def __init__(self, registry_path: str = "./config/dataset_registry.json"):
        """
        Inicializa el registro de datos.

        Args:
            registry_path: Ruta al archivo de registro
        """
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_registry()

        # Estadísticas de red
        self.network_stats = {
            "total_datasets": 0,
            "total_shards": 0,
            "total_size_gb": 0.0,
            "active_nodes": 0,
            "data_providers": 0,
            "quality_score_avg": 0.0,
            "last_updated": None
        }

        self._update_network_stats()

    def _load_registry(self):
        """Carga el registro desde disco."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    self.datasets = json.load(f)
                logger.info(f"✅ Registro cargado: {len(self.datasets)} datasets")
            except json.JSONDecodeError as e:
                logger.error(f"Error cargando registro: {e}")
                self.datasets = {}
        else:
            self.datasets = {}
            logger.info("📝 Registro nuevo creado")

    def _save_registry(self):
        """Guarda el registro en disco."""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.datasets, f, indent=2, ensure_ascii=False)
            logger.debug("💾 Registro guardado")
        except Exception as e:
            logger.error(f"Error guardando registro: {e}")

    def _update_network_stats(self):
        """Actualiza estadísticas de red basadas en el registro."""
        if not self.datasets:
            self.network_stats.update({
                "total_datasets": 0,
                "total_shards": 0,
                "total_size_gb": 0.0,
                "quality_score_avg": 0.0
            })
            return

        total_datasets = len(self.datasets)
        total_shards = sum(ds.get("meta", {}).get("num_shards", 0) for ds in self.datasets.values())
        total_size_mb = sum(ds.get("meta", {}).get("total_size_mb", 0) for ds in self.datasets.values())
        total_size_gb = total_size_mb / 1024

        quality_scores = [ds.get("meta", {}).get("quality_score", 0)
                         for ds in self.datasets.values()
                         if ds.get("meta", {}).get("quality_score", 0) > 0]

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        self.network_stats.update({
            "total_datasets": total_datasets,
            "total_shards": total_shards,
            "total_size_gb": round(total_size_gb, 2),
            "quality_score_avg": round(avg_quality, 2),
            "last_updated": datetime.now().isoformat()
        })

    def register_dataset(self, manifest: Dict) -> bool:
        """
        Registra un nuevo dataset en la red.

        Args:
            manifest: Manifest completo del dataset

        Returns:
            True si se registró correctamente
        """
        dataset_id = manifest.get("id")
        if not dataset_id:
            logger.error("❌ Intento de registrar dataset sin ID")
            return False

        # Validar manifest
        required_fields = ["name", "type", "total_size_mb", "num_shards", "shard_cids"]
        missing_fields = [field for field in required_fields if field not in manifest]

        if missing_fields:
            logger.error(f"❌ Manifest incompleto, faltan: {missing_fields}")
            return False

        # Verificar que no existe ya
        if dataset_id in self.datasets:
            logger.warning(f"⚠️ Dataset {dataset_id} ya existe, actualizando...")

        # Crear entrada de registro
        registry_entry = {
            "meta": manifest,
            "status": "active",
            "registered_at": datetime.now().isoformat(),
            "node_count": 0,  # Nodos que tienen este dataset
            "download_count": 0,  # Veces descargado
            "last_accessed": None,
            "quality_verified": self._verify_dataset_quality(manifest)
        }

        self.datasets[dataset_id] = registry_entry
        self._save_registry()
        self._update_network_stats()

        logger.info(f"✅ Dataset registrado: {manifest.get('name')} ({dataset_id})")
        logger.info(f"   📊 Shards: {manifest.get('num_shards')} | Tamaño: {manifest.get('total_size_mb'):.2f}MB")
        logger.info(f"   ⭐ Calidad: {manifest.get('quality_score', 0):.2f}/1.0")

        return True

    def _verify_dataset_quality(self, manifest: Dict) -> bool:
        """
        Verifica la calidad básica de un dataset.

        Args:
            manifest: Manifest del dataset

        Returns:
            True si pasa verificación básica
        """
        # Verificaciones básicas
        checks = [
            manifest.get("num_shards", 0) > 0,
            manifest.get("total_size_mb", 0) > 0,
            len(manifest.get("shard_cids", [])) > 0,
            manifest.get("quality_score", 0) >= 0.1  # Mínimo aceptable
        ]

        return all(checks)

    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """
        Obtiene información completa de un dataset.

        Args:
            dataset_id: ID del dataset

        Returns:
            Información del dataset o None si no existe
        """
        dataset = self.datasets.get(dataset_id)
        if dataset:
            # Actualizar último acceso
            dataset["last_accessed"] = datetime.now().isoformat()
            dataset["download_count"] += 1
            self._save_registry()

        return dataset

    def list_datasets(self, domain_filter: str = None, quality_min: float = 0.0,
                     type_filter: str = None) -> List[Dict]:
        """
        Lista datasets con filtros opcionales.

        Args:
            domain_filter: Filtrar por dominio/tag
            quality_min: Calidad mínima requerida
            type_filter: Tipo de dataset ("text_file", "json_dataset", etc.)

        Returns:
            Lista de datasets filtrados
        """
        results = []

        for dataset_id, dataset_info in self.datasets.items():
            meta = dataset_info.get("meta", {})

            # Aplicar filtros
            if quality_min > 0 and meta.get("quality_score", 0) < quality_min:
                continue

            if type_filter and meta.get("type") != type_filter:
                continue

            if domain_filter:
                # Buscar en metadatos o descripción
                searchable = json.dumps(meta).lower()
                if domain_filter.lower() not in searchable:
                    continue

            results.append({
                "id": dataset_id,
                **meta,
                "status": dataset_info.get("status"),
                "downloads": dataset_info.get("download_count", 0)
            })

        # Ordenar por calidad descendente
        results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        return results

    def search_datasets(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Búsqueda de texto completo en datasets.

        Args:
            query: Término de búsqueda
            limit: Máximo número de resultados

        Returns:
            Lista de datasets que coinciden
        """
        query_lower = query.lower()
        results = []

        for dataset_id, dataset_info in self.datasets.items():
            meta = dataset_info.get("meta", {})

            # Buscar en nombre, descripción y metadatos
            searchable_text = json.dumps(meta, default=str).lower()

            if query_lower in searchable_text:
                results.append({
                    "id": dataset_id,
                    **meta,
                    "relevance_score": self._calculate_relevance(query_lower, searchable_text)
                })

        # Ordenar por relevancia
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return results[:limit]

    def _calculate_relevance(self, query: str, text: str) -> float:
        """
        Calcula una puntuación de relevancia simple.

        Args:
            query: Término de búsqueda
            text: Texto donde buscar

        Returns:
            Puntuación de relevancia (0.0 a 1.0)
        """
        if not query or not text:
            return 0.0

        # Conteo simple de ocurrencias
        occurrences = text.count(query)

        # Bonus por aparecer en el nombre
        name_bonus = 0.5 if query in text.split('"name":')[1].split('"')[1].lower() else 0.0

        # Normalizar a 0-1
        relevance = min(occurrences * 0.1 + name_bonus, 1.0)

        return round(relevance, 2)

    def update_dataset_stats(self, dataset_id: str, node_count: int = None):
        """
        Actualiza estadísticas de un dataset.

        Args:
            dataset_id: ID del dataset
            node_count: Número de nodos que lo tienen
        """
        if dataset_id in self.datasets:
            if node_count is not None:
                self.datasets[dataset_id]["node_count"] = node_count
            self._save_registry()
            self._update_network_stats()

    def get_network_stats(self) -> Dict:
        """
        Obtiene estadísticas generales de la red.

        Returns:
            Dict con estadísticas de red
        """
        self._update_network_stats()
        return self.network_stats.copy()

    def deactivate_dataset(self, dataset_id: str) -> bool:
        """
        Desactiva un dataset (lo marca como no disponible).

        Args:
            dataset_id: ID del dataset

        Returns:
            True si se desactivó correctamente
        """
        if dataset_id in self.datasets:
            self.datasets[dataset_id]["status"] = "inactive"
            self._save_registry()
            logger.info(f"📴 Dataset desactivado: {dataset_id}")
            return True

        return False

    def cleanup_expired_datasets(self, max_age_days: int = 90) -> int:
        """
        Limpia datasets antiguos que no han sido accedidos.

        Args:
            max_age_days: Días máximos de inactividad

        Returns:
            Número de datasets limpiados
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        datasets_to_remove = []

        for dataset_id, dataset_info in self.datasets.items():
            last_accessed = dataset_info.get("last_accessed")
            if last_accessed:
                try:
                    last_accessed_date = datetime.fromisoformat(last_accessed)
                    if last_accessed_date < cutoff_date:
                        datasets_to_remove.append(dataset_id)
                except ValueError:
                    # Fecha inválida, considerar para limpieza
                    datasets_to_remove.append(dataset_id)

        # Remover datasets expirados
        for dataset_id in datasets_to_remove:
            del self.datasets[dataset_id]
            cleaned_count += 1

        if cleaned_count > 0:
            self._save_registry()
            self._update_network_stats()
            logger.info(f"🧹 {cleaned_count} datasets expirados limpiados")

        return cleaned_count

    def export_registry(self, export_path: str) -> bool:
        """
        Exporta el registro completo a un archivo.

        Args:
            export_path: Ruta donde exportar

        Returns:
            True si se exportó correctamente
        """
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "network_stats": self.network_stats,
                "datasets": self.datasets
            }

            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"📤 Registro exportado a: {export_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando registro: {e}")
            return False

# Instancia global del registro
data_registry = DataRegistry()
