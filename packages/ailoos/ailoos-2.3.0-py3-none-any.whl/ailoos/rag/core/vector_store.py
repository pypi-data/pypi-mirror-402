"""
Vector Store para RAG con integración de memoria destilada.
Almacena y recupera vectores de documentos y memorias neurales consolidadas.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import json
import threading
from pathlib import Path
import hashlib

try:
    import faiss
    import torch
except ImportError:
    faiss = None
    torch = None

from ...utils.logging import get_logger


@dataclass
class VectorDocument:
    """Documento vectorizado para RAG."""
    id: str
    content: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    timestamp: datetime
    source: str  # 'document', 'neural_memory', 'distilled_memory'


@dataclass
class SearchResult:
    """Resultado de búsqueda vectorial."""
    document: VectorDocument
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """
    Almacén vectorial para RAG con soporte para memoria destilada.
    Utiliza FAISS para búsqueda eficiente de similitud vectorial.
    """

    def __init__(self,
                 dimension: int = 384,
                 index_type: str = "IndexFlatIP",  # Inner product para coseno
                 storage_path: str = "./vector_store",
                 normalize_vectors: bool = True):
        self.logger = get_logger(__name__)

        self.dimension = dimension
        self.index_type = index_type
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.normalize_vectors = normalize_vectors

        # Índice FAISS
        self.index = None
        self._initialize_index()

        # Almacenamiento de documentos
        self.documents: Dict[str, VectorDocument] = {}
        self.id_to_idx: Dict[str, int] = {}  # ID -> índice en FAISS
        self.idx_to_id: Dict[int, str] = {}  # índice en FAISS -> ID

        # Estadísticas
        self.total_documents = 0
        self.total_neural_memories = 0
        self.total_distilled_memories = 0

        # Locks
        self.lock = threading.RLock()

        # Cargar estado existente
        self._load_state()

        self.logger.info(f"VectorStore inicializado con dimensión {dimension}")

    def _initialize_index(self):
        """Inicializar índice FAISS."""
        if faiss is None:
            self.logger.warning("FAISS no disponible, usando implementación dummy")
            self.index = None
            return

        try:
            if self.index_type == "IndexFlatIP":
                self.index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IndexIVFFlat":
                # Índice con cuantización para escalabilidad
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)  # 100 centroids
                self.index.train(np.random.random((1000, self.dimension)).astype(np.float32))
            else:
                self.index = faiss.IndexFlatIP(self.dimension)

            self.logger.info(f"Índice FAISS {self.index_type} inicializado")

        except Exception as e:
            self.logger.error(f"Error inicializando índice FAISS: {e}")
            self.index = None

    async def add_document(self, document: Dict[str, Any]) -> bool:
        """Añadir documento al vector store."""
        try:
            doc_id = document['id']
            content = document.get('content', '')
            vector = document.get('vector')
            metadata = document.get('metadata', {})
            source = document.get('source', 'document')

            if vector is None:
                self.logger.error(f"Documento {doc_id} no tiene vector")
                return False

            # Convertir vector a numpy array
            if isinstance(vector, list):
                vector = np.array(vector, dtype=np.float32)
            elif torch and isinstance(vector, torch.Tensor):
                vector = vector.cpu().numpy().astype(np.float32)

            # Normalizar si es necesario
            if self.normalize_vectors:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm

            # Verificar dimensión
            if len(vector) != self.dimension:
                self.logger.warning(f"Vector dimensión {len(vector)} != {self.dimension}, ajustando")
                if len(vector) > self.dimension:
                    vector = vector[:self.dimension]
                else:
                    vector = np.pad(vector, (0, self.dimension - len(vector)))

            # Crear documento vectorizado
            vector_doc = VectorDocument(
                id=doc_id,
                content=content,
                vector=vector,
                metadata=metadata,
                timestamp=datetime.now(),
                source=source
            )

            # Añadir a índice FAISS
            await self._add_to_index(vector_doc)

            # Actualizar estadísticas
            with self.lock:
                self.documents[doc_id] = vector_doc
                if source == 'neural_memory':
                    self.total_neural_memories += 1
                elif source == 'distilled_memory':
                    self.total_distilled_memories += 1
                else:
                    self.total_documents += 1

            # Guardar estado periódicamente
            if (self.total_documents + self.total_neural_memories + self.total_distilled_memories) % 100 == 0:
                await self._save_state_async()

            self.logger.debug(f"Documento {doc_id} añadido al vector store")
            return True

        except Exception as e:
            self.logger.error(f"Error añadiendo documento {document.get('id', 'unknown')}: {e}")
            return False

    async def _add_to_index(self, document: VectorDocument):
        """Añadir documento al índice FAISS."""
        if self.index is None:
            return

        try:
            # Añadir vector al índice
            vector_reshaped = document.vector.reshape(1, -1).astype(np.float32)
            idx = self.index.ntotal

            self.index.add(vector_reshaped)

            # Actualizar mappings
            with self.lock:
                self.id_to_idx[document.id] = idx
                self.idx_to_id[idx] = document.id

        except Exception as e:
            self.logger.error(f"Error añadiendo a índice FAISS: {e}")

    async def search(self,
                    query_vector: np.ndarray,
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Buscar documentos similares al vector de consulta.

        Args:
            query_vector: Vector de consulta
            top_k: Número de resultados a retornar
            filters: Filtros opcionales (source, metadata, etc.)

        Returns:
            Lista de resultados de búsqueda ordenados por similitud
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                return []

            # Preparar vector de consulta
            if isinstance(query_vector, list):
                query_vector = np.array(query_vector, dtype=np.float32)
            elif torch and isinstance(query_vector, torch.Tensor):
                query_vector = query_vector.cpu().numpy().astype(np.float32)

            # Normalizar si es necesario
            if self.normalize_vectors:
                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    query_vector = query_vector / norm

            # Ajustar dimensión
            if len(query_vector) != self.dimension:
                if len(query_vector) > self.dimension:
                    query_vector = query_vector[:self.dimension]
                else:
                    query_vector = np.pad(query_vector, (0, self.dimension - len(query_vector)))

            # Buscar en FAISS
            query_reshaped = query_vector.reshape(1, -1).astype(np.float32)
            scores, indices = self.index.search(query_reshaped, min(top_k * 2, self.index.ntotal))  # Buscar más para filtrar

            # Convertir resultados
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No más resultados
                    continue

                doc_id = self.idx_to_id.get(idx)
                if doc_id and doc_id in self.documents:
                    document = self.documents[doc_id]

                    # Aplicar filtros
                    if filters and not self._matches_filters(document, filters):
                        continue

                    result = SearchResult(
                        document=document,
                        score=float(score),
                        metadata=document.metadata
                    )
                    results.append(result)

                    if len(results) >= top_k:
                        break

            # Ordenar por score descendente (más similar primero)
            results.sort(key=lambda x: x.score, reverse=True)

            self.logger.debug(f"Búsqueda completada: {len(results)} resultados para top_k={top_k}")
            return results

        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}")
            return []

    def _matches_filters(self, document: VectorDocument, filters: Dict[str, Any]) -> bool:
        """Verificar si un documento cumple con los filtros."""
        try:
            # Filtro por source
            if 'source' in filters:
                if document.source != filters['source']:
                    return False

            # Filtros por metadata
            if 'metadata' in filters:
                metadata_filters = filters['metadata']
                for key, value in metadata_filters.items():
                    if key not in document.metadata or document.metadata[key] != value:
                        return False

            # Filtro por importancia mínima (para memorias destiladas)
            if 'min_importance' in filters:
                importance = document.metadata.get('importance_score', 0)
                if importance < filters['min_importance']:
                    return False

            return True

        except Exception:
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """Eliminar documento del vector store."""
        try:
            with self.lock:
                if doc_id not in self.documents:
                    return False

                # No podemos eliminar directamente de FAISS IndexFlatIP
                # En su lugar, marcamos como eliminado y reconstruimos periódicamente
                # Para esta implementación, simplemente removemos de nuestros mappings

                if doc_id in self.id_to_idx:
                    idx = self.id_to_idx[doc_id]
                    del self.idx_to_id[idx]
                    del self.id_to_idx[doc_id]

                del self.documents[doc_id]

                # Actualizar estadísticas
                document = self.documents.get(doc_id)
                if document:
                    if document.source == 'neural_memory':
                        self.total_neural_memories -= 1
                    elif document.source == 'distilled_memory':
                        self.total_distilled_memories -= 1
                    else:
                        self.total_documents -= 1

            self.logger.debug(f"Documento {doc_id} eliminado")
            return True

        except Exception as e:
            self.logger.error(f"Error eliminando documento {doc_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del vector store."""
        with self.lock:
            return {
                'total_documents': self.total_documents,
                'total_neural_memories': self.total_neural_memories,
                'total_distilled_memories': self.total_distilled_memories,
                'total_vectors': len(self.documents),
                'index_size': self.index.ntotal if self.index else 0,
                'dimension': self.dimension,
                'index_type': self.index_type
            }

    async def _save_state_async(self):
        """Guardar estado de forma asíncrona."""
        try:
            # Ejecutar en thread pool para no bloquear
            await asyncio.get_event_loop().run_in_executor(None, self._save_state)
        except Exception as e:
            self.logger.error(f"Error guardando estado: {e}")

    def _save_state(self):
        """Guardar estado del vector store."""
        try:
            state = {
                'documents': {},
                'stats': self.get_stats(),
                'timestamp': datetime.now().isoformat()
            }

            # Guardar documentos (metadata, no vectores - estos están en FAISS)
            for doc_id, doc in self.documents.items():
                state['documents'][doc_id] = {
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'timestamp': doc.timestamp.isoformat(),
                    'source': doc.source
                }

            state_path = self.storage_path / "vector_store_state.json"
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, default=str)

            self.logger.debug("Estado del vector store guardado")

        except Exception as e:
            self.logger.error(f"Error guardando estado: {e}")

    def _load_state(self):
        """Cargar estado del vector store."""
        try:
            state_path = self.storage_path / "vector_store_state.json"
            if not state_path.exists():
                return

            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Restaurar estadísticas
            stats = state.get('stats', {})
            self.total_documents = stats.get('total_documents', 0)
            self.total_neural_memories = stats.get('total_neural_memories', 0)
            self.total_distilled_memories = stats.get('total_distilled_memories', 0)

            # Nota: Los vectores y el índice FAISS tendrían que reconstruirse
            # desde los documentos. Para simplificar, por ahora solo cargamos metadata.

            self.logger.info("Estado del vector store cargado")

        except Exception as e:
            self.logger.error(f"Error cargando estado: {e}")

    async def rebuild_index(self):
        """Reconstruir índice FAISS desde documentos almacenados."""
        try:
            if self.index is None:
                return

            # Crear nuevo índice
            old_index = self.index
            self._initialize_index()

            # Re-añadir todos los documentos
            for doc in self.documents.values():
                await self._add_to_index(doc)

            self.logger.info("Índice FAISS reconstruido")

        except Exception as e:
            self.logger.error(f"Error reconstruyendo índice: {e}")


# Instancia global
_vector_store: Optional[VectorStore] = None


def get_vector_store(dimension: int = 384) -> VectorStore:
    """Obtener instancia global del vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(dimension=dimension)
    return _vector_store