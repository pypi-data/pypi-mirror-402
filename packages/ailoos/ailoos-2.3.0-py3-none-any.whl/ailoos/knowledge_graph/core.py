"""
Knowledge Graph Core para AILOOS.
Implementa operaciones CRUD para grafos de conocimiento con soporte para múltiples backends y formatos.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

try:
    import rdflib
    from rdflib import Graph, URIRef, Literal, BNode
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


from ..core.logging import get_logger
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from .storage import StorageManager, StorageConfig, StorageBackendType, get_storage_manager

logger = get_logger(__name__)


class BackendType(Enum):
    """Tipos de backend soportados."""
    IN_MEMORY = "in_memory"
    NEO4J = "neo4j"
    RDF_STORE = "rdf_store"
    REDIS = "redis"


class FormatType(Enum):
    """Formatos de datos soportados."""
    RDF = "rdf"
    OWL = "owl"
    JSON_LD = "json_ld"


@dataclass
class Triple:
    """Representa un triple RDF (sujeto, predicado, objeto)."""
    subject: str
    predicate: str
    object: Union[str, int, float, bool]

    def __post_init__(self):
        """Validación básica del triple."""
        if not self.subject or not isinstance(self.subject, str):
            raise ValueError("Subject must be a non-empty string")
        if not self.predicate or not isinstance(self.predicate, str):
            raise ValueError("Predicate must be a non-empty string")
        if self.object is None:
            raise ValueError("Object cannot be None")

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object
        }

    def to_tuple(self) -> Tuple[str, str, Union[str, int, float, bool]]:
        """Convertir a tupla."""
        return (self.subject, self.predicate, self.object)




class KnowledgeGraphCore:
    """
    Núcleo del sistema de grafos de conocimiento para AILOOS.
    Gestiona operaciones CRUD con soporte para múltiples backends y formatos.
    """

    def __init__(self, backend_type: BackendType = BackendType.IN_MEMORY, **backend_config):
        self.backend_type = backend_type
        self.backend_config = backend_config

        # Integración con auditoría y métricas
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Inicializar storage manager con nueva layer
        self._initialize_storage_manager()

    def _initialize_storage_manager(self):
        """Inicializar el storage manager con configuración."""
        try:
            # Mapear tipos de backend antiguos a nuevos
            backend_type_mapping = {
                BackendType.IN_MEMORY: StorageBackendType.MEMORY,
                BackendType.NEO4J: StorageBackendType.NEO4J,
                BackendType.RDF_STORE: StorageBackendType.RDF,
                BackendType.REDIS: StorageBackendType.REDIS
            }

            storage_backend_type = backend_type_mapping.get(self.backend_type, StorageBackendType.MEMORY)

            # Configurar failover si está disponible
            failover_backends = []
            if self.backend_type != BackendType.IN_MEMORY:
                failover_backends = [StorageBackendType.MEMORY]  # Fallback a memoria

            # Crear configuración de storage
            storage_config = StorageConfig(
                backend_type=storage_backend_type,
                connection_params=self.backend_config,
                failover_enabled=True,
                failover_backends=failover_backends,
                metrics_enabled=True,
                audit_enabled=True
            )

            # Inicializar storage manager
            self.storage_manager = StorageManager(storage_config)

            logger.info(f"Initialized storage manager with {storage_backend_type.value} backend")

        except Exception as e:
            logger.error(f"Failed to initialize storage manager: {e}")
            # Fallback a configuración básica
            storage_config = StorageConfig(backend_type=StorageBackendType.MEMORY)
            self.storage_manager = StorageManager(storage_config)
            logger.warning("Fallback to memory storage backend")

    async def add_triple(self, triple: Triple, user_id: Optional[str] = None) -> bool:
        """
        Agregar un triple al grafo.

        Args:
            triple: El triple a agregar
            user_id: ID del usuario que realiza la operación

        Returns:
            True si se agregó exitosamente
        """
        start_time = time.time()

        try:
            # Validar triple
            self._validate_triple(triple)

            # Agregar usando storage manager
            success = await self.storage_manager.add_triple(triple)

            if success:
                # Logging de auditoría
                await self.audit_manager.log_event(
                    event_type=AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                    resource="knowledge_graph",
                    action="add_triple",
                    user_id=user_id,
                    details=triple.to_dict(),
                    success=True,
                    processing_time_ms=(time.time() - start_time) * 1000
                )

                # Métricas
                self.metrics_collector.record_request("knowledge_graph.add_triple")
                self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

                logger.info(f"Added triple: {triple}")
                return True
            else:
                raise Exception("Backend failed to add triple")

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="add_triple",
                user_id=user_id,
                details={"error": str(e), "triple": triple.to_dict()},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_graph.add_triple", "validation_error")
            logger.error(f"Failed to add triple: {e}")
            return False

    async def remove_triple(self, triple: Triple, user_id: Optional[str] = None) -> bool:
        """
        Remover un triple del grafo.

        Args:
            triple: El triple a remover
            user_id: ID del usuario que realiza la operación

        Returns:
            True si se removió exitosamente
        """
        start_time = time.time()

        try:
            # Validar triple
            self._validate_triple(triple)

            # Remover usando storage manager
            success = await self.storage_manager.remove_triple(triple)

            if success:
                # Logging de auditoría
                await self.audit_manager.log_event(
                    event_type=AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                    resource="knowledge_graph",
                    action="remove_triple",
                    user_id=user_id,
                    details=triple.to_dict(),
                    success=True,
                    processing_time_ms=(time.time() - start_time) * 1000
                )

                # Métricas
                self.metrics_collector.record_request("knowledge_graph.remove_triple")
                self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

                logger.info(f"Removed triple: {triple}")
                return True
            else:
                raise Exception("Backend failed to remove triple")

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="remove_triple",
                user_id=user_id,
                details={"error": str(e), "triple": triple.to_dict()},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_graph.remove_triple", "validation_error")
            logger.error(f"Failed to remove triple: {e}")
            return False

    async def query(self, query: str, user_id: Optional[str] = None, **kwargs) -> List[Triple]:
        """
        Ejecutar una consulta en el grafo.

        Args:
            query: La consulta a ejecutar
            user_id: ID del usuario que realiza la consulta
            **kwargs: Parámetros adicionales para la consulta

        Returns:
            Lista de triples que coinciden con la consulta
        """
        start_time = time.time()

        try:
            # Ejecutar consulta usando storage manager
            results = await self.storage_manager.query(query, **kwargs)

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_QUERY,
                resource="knowledge_graph",
                action="query",
                user_id=user_id,
                details={"query": query, "results_count": len(results)},
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_graph.query")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Query executed: {query}, results: {len(results)}")
            return results

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="query",
                user_id=user_id,
                details={"error": str(e), "query": query},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_graph.query", "query_error")
            logger.error(f"Query failed: {e}")
            return []

    async def load_from_format(self, data: str, format_type: FormatType, user_id: Optional[str] = None) -> bool:
        """
        Cargar datos desde un formato específico.

        Args:
            data: Los datos en el formato especificado
            format_type: El tipo de formato
            user_id: ID del usuario

        Returns:
            True si se cargaron exitosamente
        """
        start_time = time.time()

        try:
            triples = self._parse_format(data, format_type)

            # Agregar triples
            success_count = 0
            for triple in triples:
                if await self.add_triple(triple, user_id):
                    success_count += 1

            # Logging
            await self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                resource="knowledge_graph",
                action="load_from_format",
                user_id=user_id,
                details={"format": format_type.value, "total_triples": len(triples), "success_count": success_count},
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            logger.info(f"Loaded {success_count}/{len(triples)} triples from {format_type.value}")
            return success_count == len(triples)

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="load_from_format",
                user_id=user_id,
                details={"error": str(e), "format": format_type.value},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            logger.error(f"Failed to load from format: {e}")
            return False

    async def export_to_format(self, format_type: FormatType) -> Optional[str]:
        """
        Exportar el grafo a un formato específico.

        Args:
            format_type: El tipo de formato

        Returns:
            Los datos en el formato especificado o None si falla
        """
        try:
            triples = await self.storage_manager.get_all_triples()
            return self._serialize_format(triples, format_type)

        except Exception as e:
            logger.error(f"Failed to export to format: {e}")
            return None

    def _validate_triple(self, triple: Triple):
        """Validar un triple."""
        if not isinstance(triple, Triple):
            raise ValueError("Must be a Triple instance")

        # Validaciones adicionales
        if len(triple.subject) > 1000:
            raise ValueError("Subject too long")
        if len(triple.predicate) > 1000:
            raise ValueError("Predicate too long")

        # Validar tipos de objeto
        if not isinstance(triple.object, (str, int, float, bool)):
            raise ValueError("Object must be string, int, float, or bool")

    def _parse_format(self, data: str, format_type: FormatType) -> List[Triple]:
        """Parsear datos desde un formato específico."""
        if format_type == FormatType.JSON_LD:
            return self._parse_json_ld(data)
        elif format_type in [FormatType.RDF, FormatType.OWL]:
            return self._parse_rdf(data, format_type)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _parse_json_ld(self, data: str) -> List[Triple]:
        """Parsear JSON-LD."""
        try:
            json_data = json.loads(data)
            triples = []

            # Implementación simplificada - en producción usar json-ld library
            if "@graph" in json_data:
                for item in json_data["@graph"]:
                    if "@id" in item:
                        subject = item["@id"]
                        for key, value in item.items():
                            if key != "@id":
                                if isinstance(value, list):
                                    for v in value:
                                        triples.append(Triple(subject, key, v))
                                else:
                                    triples.append(Triple(subject, key, value))

            return triples

        except Exception as e:
            raise ValueError(f"Invalid JSON-LD: {e}")

    def _parse_rdf(self, data: str, format_type: FormatType) -> List[Triple]:
        """Parsear RDF/OWL usando rdflib."""
        if not RDFLIB_AVAILABLE:
            raise ImportError("rdflib required for RDF parsing")

        try:
            graph = Graph()
            format_map = {
                FormatType.RDF: "turtle",  # o xml, etc.
                FormatType.OWL: "xml"
            }

            graph.parse(data=data, format=format_map.get(format_type, "turtle"))

            triples = []
            for subj, pred, obj in graph:
                subj_str = str(subj)
                pred_str = str(pred)
                obj_val = obj.toPython() if hasattr(obj, 'toPython') else str(obj)
                triples.append(Triple(subj_str, pred_str, obj_val))

            return triples

        except Exception as e:
            raise ValueError(f"Invalid RDF/OWL: {e}")

    def _serialize_format(self, triples: List[Triple], format_type: FormatType) -> str:
        """Serializar triples a un formato específico."""
        if format_type == FormatType.JSON_LD:
            return self._serialize_json_ld(triples)
        elif format_type in [FormatType.RDF, FormatType.OWL]:
            return self._serialize_rdf(triples, format_type)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _serialize_json_ld(self, triples: List[Triple]) -> str:
        """Serializar a JSON-LD."""
        # Implementación simplificada
        graph = []
        subjects = {}

        for triple in triples:
            if triple.subject not in subjects:
                subjects[triple.subject] = {"@id": triple.subject}
            subjects[triple.subject][triple.predicate] = triple.object

        graph = list(subjects.values())

        return json.dumps({"@graph": graph}, indent=2)

    def _serialize_rdf(self, triples: List[Triple], format_type: FormatType) -> str:
        """Serializar a RDF/OWL usando rdflib."""
        if not RDFLIB_AVAILABLE:
            raise ImportError("rdflib required for RDF serialization")

        graph = Graph()

        for triple in triples:
            subj = URIRef(triple.subject) if triple.subject.startswith('http') else BNode(triple.subject)
            pred = URIRef(triple.predicate)
            obj = Literal(triple.object) if isinstance(triple.object, (str, int, float, bool)) else URIRef(str(triple.object))
            graph.add((subj, pred, obj))

        format_map = {
            FormatType.RDF: "turtle",
            FormatType.OWL: "xml"
        }

        return graph.serialize(format=format_map.get(format_type, "turtle"))

    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del grafo."""
        try:
            triples = await self.storage_manager.get_all_triples()
            subjects = set()
            predicates = set()

            for triple in triples:
                subjects.add(triple.subject)
                predicates.add(triple.predicate)

            # Obtener métricas del storage manager
            storage_health = await self.storage_manager.health_check()

            return {
                "total_triples": len(triples),
                "unique_subjects": len(subjects),
                "unique_predicates": len(predicates),
                "backend_type": self.backend_type.value,
                "storage_health": storage_health,
                "storage_metrics": self.storage_manager.get_metrics()
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    async def clear(self, user_id: Optional[str] = None) -> bool:
        """Limpiar todo el grafo."""
        try:
            success = await self.storage_manager.clear()

            if success:
                await self.audit_manager.log_event(
                    event_type=AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                    resource="knowledge_graph",
                    action="clear",
                    user_id=user_id,
                    details={"cleared": True},
                    success=True
                )

            return success

        except Exception as e:
            logger.error(f"Failed to clear graph: {e}")
            return False

    async def close(self):
        """Cerrar el storage manager."""
        if hasattr(self, 'storage_manager'):
            await self.storage_manager.close()


# Instancia global
_knowledge_graph_core = None

def get_knowledge_graph_core(backend_type: BackendType = BackendType.IN_MEMORY, **backend_config) -> KnowledgeGraphCore:
    """Obtener instancia global del núcleo del grafo de conocimiento."""
    global _knowledge_graph_core
    if _knowledge_graph_core is None:
        _knowledge_graph_core = KnowledgeGraphCore(backend_type, **backend_config)
    return _knowledge_graph_core