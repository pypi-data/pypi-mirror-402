"""
Cache de KV compartido entre rondas de federated learning.
Optimización de memoria para reutilización de contextos similares.
"""

import torch
import logging
import time
import hashlib
import pickle
import lzma
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from ..utils.cache import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class KVCacheEntry:
    """Entrada del cache KV con metadatos."""

    key: str  # Hash del prompt/contexto
    kv_cache: torch.Tensor
    prompt_tokens: List[int]
    attention_mask: Optional[torch.Tensor] = None
    round_id: str = ""
    node_id: str = ""
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    compressed: bool = False
    compression_ratio: float = 1.0
    memory_usage_bytes: int = 0

    def update_access(self):
        """Actualizar estadísticas de acceso."""
        self.last_accessed = time.time()
        self.access_count += 1

    def calculate_memory_usage(self):
        """Calcular uso de memoria de la entrada."""
        if self.kv_cache is not None:
            self.memory_usage_bytes = self.kv_cache.numel() * self.kv_cache.element_size()
        return self.memory_usage_bytes


@dataclass
class SharedKVCacheConfig:
    """Configuración del cache KV compartido."""

    # Límites de memoria
    max_cache_memory_gb: float = 2.0
    max_entries: int = 1000
    max_entry_age_hours: float = 24.0

    # Compresión
    enable_compression: bool = True
    compression_threshold_mb: float = 50.0  # Comprimir entradas > 50MB
    compression_level: int = 6  # Nivel de compresión LZMA

    # Políticas de reemplazo
    eviction_policy: str = "lru"  # lru, lfu, size_based
    min_access_count_for_persistence: int = 3

    # Persistencia
    enable_persistence: bool = True
    persistence_path: str = "./cache/kv_cache"
    sync_interval_seconds: float = 300.0  # 5 minutos

    # Similitud y reutilización
    enable_similarity_search: bool = True
    similarity_threshold: float = 0.85
    max_similarity_candidates: int = 10

    # Federación
    enable_cross_round_sharing: bool = True
    enable_cross_node_sharing: bool = False  # Solo si es seguro
    privacy_preserve_hashes: bool = True


class SharedKVCache:
    """
    Cache de KV compartido para federated learning.

    Características principales:
    - Almacenamiento eficiente de caches KV entre rondas
    - Compresión automática para ahorro de memoria
    - Políticas de reemplazo inteligentes (LRU, LFU)
    - Búsqueda de similitud para reutilización de contextos
    - Persistencia opcional en disco
    - Sincronización entre nodos FL (si es seguro)
    """

    def __init__(self, config: SharedKVCacheConfig):
        self.config = config

        # Almacenamiento principal
        self.cache: Dict[str, KVCacheEntry] = {}
        self.cache_lock = threading.RLock()

        # Índices para búsqueda eficiente
        self.prompt_to_key: Dict[str, str] = {}  # prompt_hash -> cache_key
        self.round_entries: Dict[str, Set[str]] = {}  # round_id -> set of keys
        self.node_entries: Dict[str, Set[str]] = {}  # node_id -> set of keys

        # Estadísticas
        self.stats = {
            "total_entries": 0,
            "total_memory_bytes": 0,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "cache_hits": 0,
            "similarity_hits": 0
        }

        # Componentes auxiliares
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cache_manager = CacheManager()
        self.persistence_thread: Optional[threading.Thread] = None
        self.running = False

        # Inicializar directorio de persistencia
        if config.enable_persistence:
            Path(config.persistence_path).mkdir(parents=True, exist_ok=True)

        logger.info("🔧 SharedKVCache inicializado")
        logger.info(f"   Memoria máxima: {config.max_cache_memory_gb}GB")
        logger.info(f"   Entradas máximas: {config.max_entries}")
        logger.info(f"   Política de reemplazo: {config.eviction_policy}")

    def start(self):
        """Iniciar el cache (persistencia, limpieza automática)."""
        self.running = True

        # Cargar cache persistido si existe
        if self.config.enable_persistence:
            self._load_persistent_cache()

        # Iniciar thread de sincronización
        if self.config.enable_persistence:
            self.persistence_thread = threading.Thread(
                target=self._persistence_worker,
                daemon=True
            )
            self.persistence_thread.start()

        # Iniciar limpieza automática
        self._schedule_cleanup()

        logger.info("▶️ SharedKVCache iniciado")

    def stop(self):
        """Detener el cache y persistir estado."""
        self.running = False

        if self.config.enable_persistence:
            self._save_persistent_cache()

        self.executor.shutdown(wait=True)
        logger.info("⏹️ SharedKVCache detenido")

    def store_kv_cache(
        self,
        prompt_tokens: List[int],
        kv_cache: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        round_id: str = "",
        node_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Almacenar cache KV en el cache compartido.

        Args:
            prompt_tokens: Tokens del prompt
            kv_cache: Tensor del cache KV
            attention_mask: Máscara de atención opcional
            round_id: ID de la ronda FL
            node_id: ID del nodo
            metadata: Metadatos adicionales

        Returns:
            Clave del cache almacenado
        """
        with self.cache_lock:
            # Generar clave única
            prompt_hash = self._hash_prompt_tokens(prompt_tokens)
            cache_key = f"{prompt_hash}_{round_id}_{node_id}"

            # Verificar si ya existe
            if cache_key in self.cache:
                # Actualizar acceso
                self.cache[cache_key].update_access()
                return cache_key

            # Crear entrada
            entry = KVCacheEntry(
                key=cache_key,
                kv_cache=kv_cache.detach().cpu(),
                prompt_tokens=prompt_tokens.copy(),
                attention_mask=attention_mask.detach().cpu() if attention_mask is not None else None,
                round_id=round_id,
                node_id=node_id
            )

            # Calcular uso de memoria
            entry.calculate_memory_usage()

            # Comprimir si es necesario
            if self.config.enable_compression and entry.memory_usage_bytes > self.config.compression_threshold_mb * 1024 * 1024:
                self._compress_entry(entry)

            # Verificar límites antes de almacenar
            self._enforce_memory_limits()
            self._enforce_entry_limits()

            # Almacenar
            self.cache[cache_key] = entry
            self.prompt_to_key[prompt_hash] = cache_key

            # Actualizar índices
            if round_id:
                if round_id not in self.round_entries:
                    self.round_entries[round_id] = set()
                self.round_entries[round_id].add(cache_key)

            if node_id:
                if node_id not in self.node_entries:
                    self.node_entries[node_id] = set()
                self.node_entries[node_id].add(cache_key)

            # Actualizar estadísticas
            self.stats["total_entries"] = len(self.cache)
            self.stats["total_memory_bytes"] += entry.memory_usage_bytes

            logger.debug(f"💾 Cache KV almacenado: {cache_key} ({entry.memory_usage_bytes / 1024**2:.1f}MB)")
            return cache_key

    def retrieve_kv_cache(
        self,
        prompt_tokens: List[int],
        round_id: str = "",
        node_id: str = "",
        allow_similarity: bool = True
    ) -> Optional[Tuple[torch.Tensor, Optional[torch.Tensor], Dict[str, Any]]]:
        """
        Recuperar cache KV del cache compartido.

        Args:
            prompt_tokens: Tokens del prompt
            round_id: ID de la ronda FL
            node_id: ID del nodo
            allow_similarity: Permitir búsqueda por similitud

        Returns:
            Tuple de (kv_cache, attention_mask, metadata) o None si no encontrado
        """
        with self.cache_lock:
            prompt_hash = self._hash_prompt_tokens(prompt_tokens)

            # Búsqueda exacta primero
            cache_key = f"{prompt_hash}_{round_id}_{node_id}"
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                entry.update_access()
                self.stats["hits"] += 1
                self.stats["cache_hits"] += 1

                kv_cache, attention_mask = self._decompress_entry(entry)
                metadata = {
                    "source": "exact_match",
                    "round_id": entry.round_id,
                    "node_id": entry.node_id,
                    "reuse_count": entry.access_count
                }
                return kv_cache, attention_mask, metadata

            # Búsqueda por similitud si está habilitada
            if allow_similarity and self.config.enable_similarity_search:
                similar_entry = self._find_similar_cache(prompt_tokens, round_id, node_id)
                if similar_entry:
                    entry = self.cache[similar_entry]
                    entry.update_access()
                    self.stats["hits"] += 1
                    self.stats["similarity_hits"] += 1

                    kv_cache, attention_mask = self._decompress_entry(entry)
                    metadata = {
                        "source": "similarity_match",
                        "similarity_score": self._calculate_similarity(prompt_tokens, entry.prompt_tokens),
                        "round_id": entry.round_id,
                        "node_id": entry.node_id,
                        "reuse_count": entry.access_count
                    }
                    return kv_cache, attention_mask, metadata

            self.stats["misses"] += 1
            return None

    def _find_similar_cache(
        self,
        prompt_tokens: List[int],
        round_id: str,
        node_id: str
    ) -> Optional[str]:
        """Encontrar cache similar usando búsqueda de similitud."""
        if not self.config.enable_similarity_search:
            return None

        candidates = []

        # Buscar en la misma ronda primero
        if round_id and round_id in self.round_entries:
            for cache_key in self.round_entries[round_id]:
                if cache_key in self.cache:
                    entry = self.cache[cache_key]
                    similarity = self._calculate_similarity(prompt_tokens, entry.prompt_tokens)
                    if similarity >= self.config.similarity_threshold:
                        candidates.append((cache_key, similarity))

        # Buscar en otras rondas si no hay suficientes candidatos
        if len(candidates) < self.config.max_similarity_candidates:
            for r_id, keys in self.round_entries.items():
                if r_id == round_id:
                    continue
                for cache_key in keys:
                    if cache_key in self.cache:
                        entry = self.cache[cache_key]
                        similarity = self._calculate_similarity(prompt_tokens, entry.prompt_tokens)
                        if similarity >= self.config.similarity_threshold:
                            candidates.append((cache_key, similarity))

                        if len(candidates) >= self.config.max_similarity_candidates:
                            break
                if len(candidates) >= self.config.max_similarity_candidates:
                    break

        # Ordenar por similitud y retornar el mejor
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    def _calculate_similarity(self, tokens1: List[int], tokens2: List[int]) -> float:
        """Calcular similitud entre dos secuencias de tokens."""
        # Similitud de Jaccard simplificada
        set1, set2 = set(tokens1), set(tokens2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _compress_entry(self, entry: KVCacheEntry):
        """Comprimir entrada del cache."""
        if entry.compressed:
            return

        try:
            # Serializar tensor
            tensor_bytes = pickle.dumps(entry.kv_cache)

            # Comprimir
            compressed_bytes = lzma.compress(
                tensor_bytes,
                preset=self.config.compression_level
            )

            # Calcular ratio de compresión
            original_size = len(tensor_bytes)
            compressed_size = len(compressed_bytes)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

            # Reemplazar tensor con bytes comprimidos
            entry.kv_cache = compressed_bytes  # Almacenar como bytes
            entry.compressed = True
            entry.compression_ratio = compression_ratio

            # Actualizar uso de memoria
            entry.memory_usage_bytes = compressed_size

            self.stats["compressions"] += 1
            logger.debug(f"🗜️ Entrada comprimida: {compression_ratio:.2f} ratio")

        except Exception as e:
            logger.warning(f"⚠️ Error comprimiendo entrada: {e}")

    def _decompress_entry(self, entry: KVCacheEntry) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Descomprimir entrada del cache."""
        if not entry.compressed:
            return entry.kv_cache, entry.attention_mask

        try:
            # Descomprimir
            tensor_bytes = lzma.decompress(entry.kv_cache)
            kv_cache = pickle.loads(tensor_bytes)

            # Descomprimir attention_mask si existe
            attention_mask = None
            if entry.attention_mask is not None and isinstance(entry.attention_mask, bytes):
                attention_mask = pickle.loads(lzma.decompress(entry.attention_mask))

            return kv_cache, attention_mask

        except Exception as e:
            logger.error(f"❌ Error descomprimiendo entrada: {e}")
            return entry.kv_cache, entry.attention_mask  # Retornar como está

    def _enforce_memory_limits(self):
        """Forzar límites de memoria mediante eviction."""
        max_memory_bytes = int(self.config.max_cache_memory_gb * 1024**3)

        while self.stats["total_memory_bytes"] > max_memory_bytes and self.cache:
            self._evict_entry()

    def _enforce_entry_limits(self):
        """Forzar límites de número de entradas."""
        while len(self.cache) >= self.config.max_entries and self.cache:
            self._evict_entry()

    def _evict_entry(self):
        """Evadir una entrada según la política configurada."""
        if not self.cache:
            return

        entry_to_evict = None

        if self.config.eviction_policy == "lru":
            # Least Recently Used
            entry_to_evict = min(self.cache.values(), key=lambda x: x.last_accessed)
        elif self.config.eviction_policy == "lfu":
            # Least Frequently Used
            entry_to_evict = min(self.cache.values(), key=lambda x: x.access_count)
        elif self.config.eviction_policy == "size_based":
            # Más grande primero
            entry_to_evict = max(self.cache.values(), key=lambda x: x.memory_usage_bytes)
        else:
            # Default: LRU
            entry_to_evict = min(self.cache.values(), key=lambda x: x.last_accessed)

        if entry_to_evict:
            # Remover de índices
            self._remove_from_indices(entry_to_evict.key)

            # Remover del cache
            memory_freed = entry_to_evict.memory_usage_bytes
            del self.cache[entry_to_evict.key]

            # Actualizar estadísticas
            self.stats["total_memory_bytes"] -= memory_freed
            self.stats["evictions"] += 1
            self.stats["total_entries"] = len(self.cache)

            logger.debug(f"🗑️ Entrada evadida: {entry_to_evict.key} ({memory_freed / 1024**2:.1f}MB liberados)")

    def _remove_from_indices(self, cache_key: str):
        """Remover entrada de todos los índices."""
        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # Remover de índices de ronda y nodo
            if entry.round_id and entry.round_id in self.round_entries:
                self.round_entries[entry.round_id].discard(cache_key)
                if not self.round_entries[entry.round_id]:
                    del self.round_entries[entry.round_id]

            if entry.node_id and entry.node_id in self.node_entries:
                self.node_entries[entry.node_id].discard(cache_key)
                if not self.node_entries[entry.node_id]:
                    del self.node_entries[entry.node_id]

            # Remover de índice de prompts
            for prompt_hash, key in self.prompt_to_key.items():
                if key == cache_key:
                    del self.prompt_to_key[prompt_hash]
                    break

    def clear_round_cache(self, round_id: str):
        """Limpiar cache específico de una ronda."""
        with self.cache_lock:
            if round_id in self.round_entries:
                keys_to_remove = self.round_entries[round_id].copy()

                for cache_key in keys_to_remove:
                    if cache_key in self.cache:
                        entry = self.cache[cache_key]
                        self.stats["total_memory_bytes"] -= entry.memory_usage_bytes
                        del self.cache[cache_key]

                del self.round_entries[round_id]
                self.stats["total_entries"] = len(self.cache)

                logger.info(f"🧹 Cache de ronda {round_id} limpiado: {len(keys_to_remove)} entradas")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        with self.cache_lock:
            hit_ratio = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0

            return {
                **self.stats,
                "hit_ratio": hit_ratio,
                "cache_utilization_percent": (self.stats["total_memory_bytes"] / (self.config.max_cache_memory_gb * 1024**3)) * 100,
                "entries_by_round": {r: len(keys) for r, keys in self.round_entries.items()},
                "entries_by_node": {n: len(keys) for n, keys in self.node_entries.items()},
                "oldest_entry_age_hours": self._get_oldest_entry_age(),
                "newest_entry_age_hours": self._get_newest_entry_age()
            }

    def _get_oldest_entry_age(self) -> float:
        """Obtener edad de la entrada más antigua."""
        if not self.cache:
            return 0.0
        oldest = min(self.cache.values(), key=lambda x: x.created_at)
        return (time.time() - oldest.created_at) / 3600

    def _get_newest_entry_age(self) -> float:
        """Obtener edad de la entrada más nueva."""
        if not self.cache:
            return 0.0
        newest = max(self.cache.values(), key=lambda x: x.created_at)
        return (time.time() - newest.created_at) / 3600

    def _hash_prompt_tokens(self, tokens: List[int]) -> str:
        """Generar hash de tokens del prompt."""
        if self.config.privacy_preserve_hashes:
            # Hash con sal para preservar privacidad
            token_str = ",".join(map(str, tokens))
            return hashlib.sha256(f"kv_cache_{token_str}".encode()).hexdigest()[:16]
        else:
            # Hash simple
            return hashlib.md5(str(tokens).encode()).hexdigest()[:16]

    def _schedule_cleanup(self):
        """Programar limpieza automática de entradas viejas."""
        def cleanup_worker():
            while self.running:
                try:
                    time.sleep(3600)  # Limpiar cada hora
                    self._cleanup_old_entries()
                except Exception as e:
                    logger.warning(f"⚠️ Error en limpieza automática: {e}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _cleanup_old_entries(self):
        """Limpiar entradas viejas según configuración."""
        with self.cache_lock:
            max_age_seconds = self.config.max_entry_age_hours * 3600
            current_time = time.time()

            keys_to_remove = []
            memory_freed = 0

            for cache_key, entry in self.cache.items():
                if current_time - entry.created_at > max_age_seconds:
                    keys_to_remove.append(cache_key)
                    memory_freed += entry.memory_usage_bytes

            # Remover entradas viejas
            for cache_key in keys_to_remove:
                self._remove_from_indices(cache_key)
                del self.cache[cache_key]

            if keys_to_remove:
                self.stats["total_memory_bytes"] -= memory_freed
                self.stats["total_entries"] = len(self.cache)
                logger.info(f"🧹 Limpiadas {len(keys_to_remove)} entradas viejas ({memory_freed / 1024**2:.1f}MB liberados)")

    def _persistence_worker(self):
        """Worker para persistencia periódica."""
        while self.running:
            try:
                time.sleep(self.config.sync_interval_seconds)
                self._save_persistent_cache()
            except Exception as e:
                logger.warning(f"⚠️ Error en persistencia: {e}")

    def _save_persistent_cache(self):
        """Guardar cache en disco."""
        if not self.config.enable_persistence:
            return

        try:
            cache_path = Path(self.config.persistence_path) / "kv_cache.pkl"

            # Solo guardar entradas con acceso mínimo
            persistent_entries = {
                k: v for k, v in self.cache.items()
                if v.access_count >= self.config.min_access_count_for_persistence
            }

            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'entries': persistent_entries,
                    'stats': self.stats,
                    'config': self.config
                }, f)

            logger.debug(f"💾 Cache persistido: {len(persistent_entries)} entradas")

        except Exception as e:
            logger.warning(f"⚠️ Error guardando cache persistente: {e}")

    def _load_persistent_cache(self):
        """Cargar cache desde disco."""
        if not self.config.enable_persistence:
            return

        try:
            cache_path = Path(self.config.persistence_path) / "kv_cache.pkl"

            if cache_path.exists():
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)

                # Restaurar entradas
                loaded_entries = data.get('entries', {})
                for cache_key, entry in loaded_entries.items():
                    if cache_key not in self.cache:  # No sobrescribir entradas existentes
                        self.cache[cache_key] = entry
                        self._restore_indices(entry)

                # Actualizar estadísticas
                self.stats.update(data.get('stats', {}))

                logger.info(f"📥 Cache persistente cargado: {len(loaded_entries)} entradas")

        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache persistente: {e}")

    def _restore_indices(self, entry: KVCacheEntry):
        """Restaurar índices para una entrada cargada."""
        # Restaurar índices de prompt
        prompt_hash = self._hash_prompt_tokens(entry.prompt_tokens)
        self.prompt_to_key[prompt_hash] = entry.key

        # Restaurar índices de ronda y nodo
        if entry.round_id:
            if entry.round_id not in self.round_entries:
                self.round_entries[entry.round_id] = set()
            self.round_entries[entry.round_id].add(entry.key)

        if entry.node_id:
            if entry.node_id not in self.node_entries:
                self.node_entries[entry.node_id] = set()
            self.node_entries[entry.node_id].add(entry.key)


# Funciones de conveniencia
def create_shared_kv_cache(
    max_memory_gb: float = 2.0,
    enable_compression: bool = True,
    enable_persistence: bool = True
) -> SharedKVCache:
    """
    Crear cache KV compartido con configuración optimizada.

    Args:
        max_memory_gb: Memoria máxima en GB
        enable_compression: Habilitar compresión
        enable_persistence: Habilitar persistencia

    Returns:
        Cache configurado
    """
    config = SharedKVCacheConfig(
        max_cache_memory_gb=max_memory_gb,
        enable_compression=enable_compression,
        enable_persistence=enable_persistence
    )

    cache = SharedKVCache(config)
    cache.start()

    return cache


if __name__ == "__main__":
    # Demo del cache KV compartido
    print("🚀 SharedKVCache Demo")
    print("Para uso completo, inicializar con configuración específica")