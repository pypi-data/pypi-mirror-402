"""
Knowledge Ingestion Pipeline para AILOOS.
Implementa ingesta, transformación y validación de conocimiento con soporte para múltiples formatos y fuentes.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Callable, AsyncGenerator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib

from ..core.logging import get_logger
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from .core import get_knowledge_graph_core, FormatType, Triple
from .ontology import get_ontology_manager

logger = get_logger(__name__)


class IngestionFormat(Enum):
    """Formatos soportados para ingesta."""
    JSON_LD = "json_ld"
    RDF = "rdf"
    OWL = "owl"
    CSV = "csv"
    XML = "xml"
    TEXT = "text"


class PipelineStage(Enum):
    """Etapas del pipeline de ingesta."""
    PARSING = "parsing"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    STORAGE = "storage"


@dataclass
class IngestionConfig:
    """Configuración del pipeline de ingesta."""
    format_type: IngestionFormat
    validate_against_ontology: bool = True
    ontology_ids: Optional[List[str]] = None
    auto_transform: bool = True
    normalize_data: bool = True
    deduplicate: bool = True
    batch_size: int = 100
    enable_streaming: bool = False
    custom_transformers: Optional[List[Callable]] = None


@dataclass
class IngestionResult:
    """Resultado de una operación de ingesta."""
    success: bool
    triples_processed: int
    triples_stored: int
    errors: List[str]
    warnings: List[str]
    processing_time_ms: float
    ingestion_id: str


class PipelineStep(ABC):
    """Paso base del pipeline de ingesta."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    async def execute(self, data: Any, context: Dict[str, Any]) -> Any:
        """Ejecutar el paso del pipeline."""
        pass


class ParsingStep(PipelineStep):
    """Paso de parsing de datos."""

    async def execute(self, data: Any, context: Dict[str, Any]) -> List[Triple]:
        """Parsear datos crudos a triples."""
        format_type = context.get('format_type')

        if format_type == IngestionFormat.JSON_LD:
            return self._parse_json_ld(data)
        elif format_type in [IngestionFormat.RDF, IngestionFormat.OWL]:
            return self._parse_rdf_owl(data, format_type)
        elif format_type == IngestionFormat.CSV:
            return self._parse_csv(data)
        elif format_type == IngestionFormat.TEXT:
            return self._parse_text(data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _parse_json_ld(self, data: str) -> List[Triple]:
        """Parsear JSON-LD."""
        try:
            json_data = json.loads(data)
            triples = []

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

    def _parse_rdf_owl(self, data: str, format_type: IngestionFormat) -> List[Triple]:
        """Parsear RDF/OWL usando rdflib."""
        try:
            from rdflib import Graph, URIRef, Literal

            graph = Graph()
            format_map = {
                IngestionFormat.RDF: "turtle",
                IngestionFormat.OWL: "xml"
            }

            graph.parse(data=data, format=format_map.get(format_type, "turtle"))

            triples = []
            for subj, pred, obj in graph:
                subj_str = str(subj)
                pred_str = str(pred)
                obj_val = obj.toPython() if hasattr(obj, 'toPython') else str(obj)
                triples.append(Triple(subj_str, pred_str, obj_val))

            return triples
        except ImportError:
            raise ImportError("rdflib required for RDF/OWL parsing")
        except Exception as e:
            raise ValueError(f"Invalid RDF/OWL: {e}")

    def _parse_csv(self, data: str) -> List[Triple]:
        """Parsear CSV (implementación simplificada)."""
        # Implementación básica - en producción usar pandas o similar
        lines = data.strip().split('\n')
        if not lines:
            return []

        headers = lines[0].split(',')
        triples = []

        for line in lines[1:]:
            values = line.split(',')
            if len(values) == len(headers):
                subject = f"entity_{hash(line)}"  # ID único simple
                for i, value in enumerate(values):
                    if i < len(headers):
                        triples.append(Triple(subject, headers[i], value))

        return triples

    def _parse_text(self, data: str) -> List[Triple]:
        """Parsear texto plano (implementación básica)."""
        # Implementación simplificada - en producción usar NLP
        subject = f"text_{hash(data)}"
        return [Triple(subject, "content", data)]


class TransformationStep(PipelineStep):
    """Paso de transformación de datos."""

    async def execute(self, triples: List[Triple], context: Dict[str, Any]) -> List[Triple]:
        """Transformar triples."""
        config = context.get('config', {})

        if config.get('normalize_data', True):
            triples = self._normalize_triples(triples)

        if config.get('deduplicate', True):
            triples = self._deduplicate_triples(triples)

        # Aplicar transformadores personalizados
        custom_transformers = config.get('custom_transformers', [])
        for transformer in custom_transformers:
            triples = await transformer(triples, context)

        return triples

    def _normalize_triples(self, triples: List[Triple]) -> List[Triple]:
        """Normalizar triples."""
        normalized = []
        for triple in triples:
            # Normalizar URIs
            subject = self._normalize_uri(triple.subject)
            predicate = self._normalize_uri(triple.predicate)
            object_val = triple.object

            # Normalizar valores de objeto
            if isinstance(object_val, str):
                object_val = object_val.strip()

            normalized.append(Triple(subject, predicate, object_val))

        return normalized

    def _normalize_uri(self, uri: str) -> str:
        """Normalizar URI."""
        if uri.startswith('http://') or uri.startswith('https://'):
            return uri
        # Convertir a URI completo si es necesario
        return uri

    def _deduplicate_triples(self, triples: List[Triple]) -> List[Triple]:
        """Eliminar triples duplicados."""
        seen = set()
        deduplicated = []

        for triple in triples:
            triple_tuple = triple.to_tuple()
            if triple_tuple not in seen:
                seen.add(triple_tuple)
                deduplicated.append(triple)

        return deduplicated


class ValidationStep(PipelineStep):
    """Paso de validación ontológica."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.ontology_manager = get_ontology_manager()

    async def execute(self, triples: List[Triple], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validar triples contra ontologías."""
        config = context.get('config', {})
        ontology_ids = config.get('ontology_ids', [])

        if not config.get('validate_against_ontology', True) or not ontology_ids:
            return {
                'triples': triples,
                'validation_result': {'valid': True, 'errors': [], 'warnings': []}
            }

        # Validar contra ontologías
        validation_result = await self.ontology_manager.validate_schema(triples, ontology_ids)

        # Filtrar triples inválidos si es necesario
        if not validation_result['valid']:
            logger.warning(f"Validation failed: {len(validation_result['errors'])} errors")

        return {
            'triples': triples,  # Mantener todos los triples por ahora
            'validation_result': validation_result
        }


class EnrichmentStep(PipelineStep):
    """Paso de enriquecimiento de datos."""

    async def execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer datos (implementación básica)."""
        # En producción, aquí se podrían agregar:
        # - Inferencia de relaciones
        # - Enriquecimiento con datos externos
        # - Linking de entidades

        return data


class StorageStep(PipelineStep):
    """Paso de almacenamiento."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.knowledge_graph = get_knowledge_graph_core()

    async def execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Almacenar triples en el grafo de conocimiento."""
        triples = data.get('triples', [])
        user_id = context.get('user_id')

        stored_count = 0
        for triple in triples:
            if await self.knowledge_graph.add_triple(triple, user_id):
                stored_count += 1

        data['stored_count'] = stored_count
        return data


class KnowledgeIngestion:
    """
    Pipeline de ingesta de conocimiento para AILOOS.
    Maneja ingesta de documentos, streams y fusión de conocimiento.
    """

    def __init__(self):
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.knowledge_graph = get_knowledge_graph_core()
        self.ontology_manager = get_ontology_manager()

        # Pipelines por defecto
        self._setup_default_pipeline()

    def _setup_default_pipeline(self):
        """Configurar pipeline por defecto."""
        self.default_pipeline = {
            PipelineStage.PARSING: ParsingStep("default_parser", {}),
            PipelineStage.TRANSFORMATION: TransformationStep("default_transformer", {}),
            PipelineStage.VALIDATION: ValidationStep("default_validator", {}),
            PipelineStage.ENRICHMENT: EnrichmentStep("default_enricher", {}),
            PipelineStage.STORAGE: StorageStep("default_storage", {})
        }

    async def ingest_document(
        self,
        document: Union[str, bytes],
        format_type: IngestionFormat,
        config: Optional[IngestionConfig] = None,
        user_id: Optional[str] = None
    ) -> IngestionResult:
        """
        Ingestar un documento individual.

        Args:
            document: Contenido del documento
            format_type: Formato del documento
            config: Configuración del pipeline
            user_id: ID del usuario que realiza la ingesta

        Returns:
            Resultado de la ingesta
        """
        start_time = time.time()
        ingestion_id = str(uuid.uuid4())

        try:
            # Configuración por defecto
            if config is None:
                config = IngestionConfig(format_type=format_type)

            # Convertir documento a string si es necesario
            if isinstance(document, bytes):
                document = document.decode('utf-8')

            # Ejecutar pipeline
            context = {
                'format_type': format_type,
                'config': config.__dict__,
                'user_id': user_id,
                'ingestion_id': ingestion_id
            }

            # Parsing
            triples = await self.default_pipeline[PipelineStage.PARSING].execute(document, context)

            # Transformation
            triples = await self.default_pipeline[PipelineStage.TRANSFORMATION].execute(triples, context)

            # Validation
            validation_data = await self.default_pipeline[PipelineStage.VALIDATION].execute(triples, context)
            triples = validation_data['triples']
            validation_result = validation_data['validation_result']

            # Enrichment
            enriched_data = await self.default_pipeline[PipelineStage.ENRICHMENT].execute(
                {'triples': triples, 'validation_result': validation_result}, context
            )

            # Storage
            storage_result = await self.default_pipeline[PipelineStage.STORAGE].execute(enriched_data, context)

            # Resultado
            processing_time = (time.time() - start_time) * 1000
            result = IngestionResult(
                success=True,
                triples_processed=len(triples),
                triples_stored=storage_result.get('stored_count', 0),
                errors=validation_result.get('errors', []),
                warnings=validation_result.get('warnings', []),
                processing_time_ms=processing_time,
                ingestion_id=ingestion_id
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_ingestion",
                action="ingest_document",
                user_id=user_id,
                details={
                    'ingestion_id': ingestion_id,
                    'format': format_type.value,
                    'triples_processed': result.triples_processed,
                    'triples_stored': result.triples_stored,
                    'processing_time_ms': processing_time
                },
                success=True,
                processing_time_ms=processing_time
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_ingestion.ingest_document")
            self.metrics_collector.record_response_time(processing_time)

            logger.info(f"Document ingested: {ingestion_id}, {result.triples_stored}/{result.triples_processed} triples stored")
            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_ingestion",
                action="ingest_document",
                user_id=user_id,
                details={
                    'ingestion_id': ingestion_id,
                    'format': format_type.value,
                    'error': str(e)
                },
                success=False,
                processing_time_ms=processing_time
            )

            self.metrics_collector.record_error("knowledge_ingestion.ingest_document", "ingestion_error")
            logger.error(f"Document ingestion failed: {ingestion_id}, error: {e}")

            return IngestionResult(
                success=False,
                triples_processed=0,
                triples_stored=0,
                errors=[str(e)],
                warnings=[],
                processing_time_ms=processing_time,
                ingestion_id=ingestion_id
            )

    async def ingest_stream(
        self,
        data_stream: AsyncGenerator[Union[str, bytes], None],
        format_type: IngestionFormat,
        config: Optional[IngestionConfig] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[IngestionResult, None]:
        """
        Procesar un stream de datos.

        Args:
            data_stream: Stream asíncrono de datos
            format_type: Formato de los datos
            config: Configuración del pipeline
            user_id: ID del usuario

        Yields:
            Resultados de ingesta por batch
        """
        if config is None:
            config = IngestionConfig(format_type=format_type, enable_streaming=True)

        batch = []
        batch_size = config.batch_size

        async for data_item in data_stream:
            batch.append(data_item)

            if len(batch) >= batch_size:
                # Procesar batch
                combined_data = self._combine_batch(batch, format_type)
                result = await self.ingest_document(combined_data, format_type, config, user_id)
                yield result
                batch = []

        # Procesar batch final
        if batch:
            combined_data = self._combine_batch(batch, format_type)
            result = await self.ingest_document(combined_data, format_type, config, user_id)
            yield result

    def _combine_batch(self, batch: List[Union[str, bytes]], format_type: IngestionFormat) -> str:
        """Combinar batch de datos para procesamiento."""
        if format_type == IngestionFormat.JSON_LD:
            # Combinar en un grafo JSON-LD
            combined = {"@graph": []}
            for item in batch:
                if isinstance(item, bytes):
                    item = item.decode('utf-8')
                try:
                    data = json.loads(item)
                    if "@graph" in data:
                        combined["@graph"].extend(data["@graph"])
                    else:
                        combined["@graph"].append(data)
                except:
                    # Si no es JSON válido, crear entrada simple
                    combined["@graph"].append({"content": item})
            return json.dumps(combined)

        elif format_type in [IngestionFormat.RDF, IngestionFormat.OWL]:
            # Concatenar RDF/OWL
            return "\n".join(item.decode('utf-8') if isinstance(item, bytes) else item for item in batch)

        else:
            # Para otros formatos, concatenar
            return "\n".join(item.decode('utf-8') if isinstance(item, bytes) else item for item in batch)

    async def fuse_knowledge(
        self,
        sources: List[Dict[str, Any]],
        fusion_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> IngestionResult:
        """
        Fusionar conocimiento de múltiples fuentes.

        Args:
            sources: Lista de fuentes de conocimiento
            fusion_config: Configuración de fusión
            user_id: ID del usuario

        Returns:
            Resultado de la fusión
        """
        start_time = time.time()
        ingestion_id = str(uuid.uuid4())

        try:
            if fusion_config is None:
                fusion_config = {
                    'conflict_resolution': 'latest_wins',  # latest_wins, merge, prioritize_source
                    'deduplication': True,
                    'consistency_check': True
                }

            all_triples = []
            source_metadata = []

            # Recopilar triples de todas las fuentes
            for source in sources:
                source_format = source.get('format', IngestionFormat.JSON_LD)
                source_data = source.get('data', '')
                source_weight = source.get('weight', 1.0)

                # Ingestar fuente individual
                result = await self.ingest_document(source_data, source_format, user_id=user_id)
                if result.success:
                    # Obtener triples almacenados (simplificado - en producción consultar grafo)
                    # Por ahora, re-parsear para obtener triples
                    context = {'format_type': source_format}
                    triples = await self.default_pipeline[PipelineStage.PARSING].execute(source_data, context)
                    all_triples.extend(triples)

                    source_metadata.append({
                        'source_id': source.get('id', str(uuid.uuid4())),
                        'weight': source_weight,
                        'triples_count': len(triples)
                    })

            # Aplicar fusión
            fused_triples = await self._apply_fusion_logic(all_triples, fusion_config, source_metadata)

            # Almacenar triples fusionados
            stored_count = 0
            for triple in fused_triples:
                if await self.knowledge_graph.add_triple(triple, user_id):
                    stored_count += 1

            processing_time = (time.time() - start_time) * 1000
            result = IngestionResult(
                success=True,
                triples_processed=len(all_triples),
                triples_stored=stored_count,
                errors=[],
                warnings=[],
                processing_time_ms=processing_time,
                ingestion_id=ingestion_id
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_ingestion",
                action="fuse_knowledge",
                user_id=user_id,
                details={
                    'ingestion_id': ingestion_id,
                    'sources_count': len(sources),
                    'total_triples': len(all_triples),
                    'fused_triples': len(fused_triples),
                    'stored_triples': stored_count,
                    'fusion_config': fusion_config
                },
                success=True,
                processing_time_ms=processing_time
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_ingestion.fuse_knowledge")
            self.metrics_collector.record_response_time(processing_time)

            logger.info(f"Knowledge fused: {ingestion_id}, {stored_count} triples stored from {len(sources)} sources")
            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_ingestion",
                action="fuse_knowledge",
                user_id=user_id,
                details={
                    'ingestion_id': ingestion_id,
                    'sources_count': len(sources),
                    'error': str(e)
                },
                success=False,
                processing_time_ms=processing_time
            )

            self.metrics_collector.record_error("knowledge_ingestion.fuse_knowledge", "fusion_error")
            logger.error(f"Knowledge fusion failed: {ingestion_id}, error: {e}")

            return IngestionResult(
                success=False,
                triples_processed=0,
                triples_stored=0,
                errors=[str(e)],
                warnings=[],
                processing_time_ms=processing_time,
                ingestion_id=ingestion_id
            )

    async def _apply_fusion_logic(
        self,
        triples: List[Triple],
        config: Dict[str, Any],
        source_metadata: List[Dict[str, Any]]
    ) -> List[Triple]:
        """Aplicar lógica de fusión."""
        conflict_resolution = config.get('conflict_resolution', 'latest_wins')

        if config.get('deduplication', True):
            # Eliminar duplicados exactos
            seen = set()
            deduplicated = []
            for triple in triples:
                triple_tuple = triple.to_tuple()
                if triple_tuple not in seen:
                    seen.add(triple_tuple)
                    deduplicated.append(triple)
            triples = deduplicated

        # Aplicar resolución de conflictos
        if conflict_resolution == 'merge':
            # Merge valores cuando sea posible
            triples = self._merge_conflicting_triples(triples)
        elif conflict_resolution == 'prioritize_source':
            # Mantener triples de fuentes con mayor peso
            triples = self._prioritize_by_source_weight(triples, source_metadata)

        # Verificación de consistencia
        if config.get('consistency_check', True):
            triples = await self._check_consistency(triples)

        return triples

    def _merge_conflicting_triples(self, triples: List[Triple]) -> List[Triple]:
        """Fusionar triples conflictivos."""
        # Implementación simplificada - en producción más sofisticada
        return triples

    def _prioritize_by_source_weight(self, triples: List[Triple], source_metadata: List[Dict[str, Any]]) -> List[Triple]:
        """Priorizar triples por peso de fuente."""
        # Implementación simplificada
        return triples

    async def _check_consistency(self, triples: List[Triple]) -> List[Triple]:
        """Verificar consistencia de triples."""
        # Implementación básica - en producción validar reglas ontológicas
        return triples


# Instancia global
_knowledge_ingestion = None

def get_knowledge_ingestion() -> KnowledgeIngestion:
    """Obtener instancia global del ingestion pipeline."""
    global _knowledge_ingestion
    if _knowledge_ingestion is None:
        _knowledge_ingestion = KnowledgeIngestion()
    return _knowledge_ingestion