"""
Sistema de Knowledge Fusion para AILOOS.
Implementa fusión de conocimiento de múltiples fuentes con resolución de conflictos,
alineación ontológica y métricas de confianza.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from ..core.logging import get_logger
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from .core import get_knowledge_graph_core, Triple
from .ingestion import get_knowledge_ingestion
from .ontology import get_ontology_manager

logger = get_logger(__name__)


class FusionStrategy(Enum):
    """Estrategias de fusión disponibles."""
    UNION = "union"  # Unión de todos los triples
    INTERSECTION = "intersection"  # Solo triples comunes
    VOTING = "voting"  # Basado en votos/confianza
    PRIORITY = "priority"  # Basado en prioridad de fuente


class ConflictResolution(Enum):
    """Estrategias de resolución de conflictos."""
    LATEST_WINS = "latest_wins"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MAJORITY_VOTE = "majority_vote"
    MERGE_VALUES = "merge_values"
    MANUAL_REVIEW = "manual_review"


@dataclass
class SourceMetadata:
    """Metadata de una fuente de conocimiento."""
    source_id: str
    name: str
    confidence_score: float
    priority: int
    ontology_id: Optional[str] = None
    last_updated: Optional[float] = None
    triple_count: int = 0


@dataclass
class FusionResult:
    """Resultado de una operación de fusión."""
    fusion_id: str
    success: bool
    fused_triples: int
    conflicts_resolved: int
    inconsistencies_detected: int
    processing_time_ms: float
    strategy_used: FusionStrategy
    sources_used: List[str]
    errors: List[str]
    warnings: List[str]


@dataclass
class ConfidenceMetrics:
    """Métricas de confianza para triples."""
    triple_hash: str
    confidence_score: float
    source_count: int
    last_updated: float
    conflict_history: List[Dict[str, Any]]


class KnowledgeFusion:
    """
    Sistema de fusión de conocimiento para combinar información de múltiples fuentes.
    Maneja resolución de conflictos, alineación ontológica y métricas de confianza.
    """

    def __init__(self):
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.knowledge_graph = get_knowledge_graph_core()
        self.knowledge_ingestion = get_knowledge_ingestion()
        self.ontology_manager = get_ontology_manager()

        # Almacenamiento de métricas de confianza
        self.confidence_metrics: Dict[str, ConfidenceMetrics] = {}

        # Configuración por defecto
        self.default_config = {
            'fusion_strategy': FusionStrategy.UNION,
            'conflict_resolution': ConflictResolution.HIGHEST_CONFIDENCE,
            'min_confidence_threshold': 0.5,
            'max_conflicts_per_triple': 5,
            'ontology_alignment_required': True,
            'consistency_check_enabled': True
        }

    async def fuse_sources(
        self,
        sources: List[Dict[str, Any]],
        fusion_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> FusionResult:
        """
        Fusionar conocimiento de múltiples fuentes.

        Args:
            sources: Lista de fuentes con datos y metadata
            fusion_config: Configuración de fusión
            user_id: ID del usuario que realiza la fusión

        Returns:
            Resultado de la fusión
        """
        start_time = time.time()
        fusion_id = str(uuid.uuid4())

        try:
            # Configuración por defecto
            config = {**self.default_config, **(fusion_config or {})}

            # Preparar metadata de fuentes
            source_metadata = await self._prepare_source_metadata(sources)

            # Alinear ontologías si es necesario
            if config.get('ontology_alignment_required', True):
                alignment_result = await self.align_ontologies(source_metadata, user_id)
                if not alignment_result['success']:
                    logger.warning(f"Ontology alignment failed: {alignment_result['errors']}")

            # Recopilar triples de todas las fuentes
            all_triples = await self._collect_triples_from_sources(sources, source_metadata)

            # Aplicar estrategia de fusión
            strategy = config.get('fusion_strategy', FusionStrategy.UNION)
            fused_triples = await self._apply_fusion_strategy(all_triples, source_metadata, strategy)

            # Resolver conflictos
            conflict_resolution = config.get('conflict_resolution', ConflictResolution.HIGHEST_CONFIDENCE)
            resolved_triples, conflicts_resolved = await self.resolve_conflicts(
                fused_triples, conflict_resolution, config
            )

            # Detectar inconsistencias
            inconsistencies = await self._detect_inconsistencies(resolved_triples, source_metadata)

            # Aplicar umbral de confianza
            min_confidence = config.get('min_confidence_threshold', 0.5)
            final_triples = await self._filter_by_confidence(resolved_triples, min_confidence)

            # Almacenar triples fusionados
            stored_count = await self._store_fused_triples(final_triples, fusion_id, user_id)

            # Actualizar métricas de confianza
            await self._update_confidence_metrics(final_triples, source_metadata)

            processing_time = (time.time() - start_time) * 1000

            result = FusionResult(
                fusion_id=fusion_id,
                success=True,
                fused_triples=stored_count,
                conflicts_resolved=conflicts_resolved,
                inconsistencies_detected=len(inconsistencies),
                processing_time_ms=processing_time,
                strategy_used=strategy,
                sources_used=[s.source_id for s in source_metadata],
                errors=[],
                warnings=[f"Inconsistency detected: {inc}" for inc in inconsistencies]
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_fusion",
                action="fuse_sources",
                user_id=user_id,
                details={
                    'fusion_id': fusion_id,
                    'sources_count': len(sources),
                    'strategy': strategy.value,
                    'fused_triples': stored_count,
                    'conflicts_resolved': conflicts_resolved,
                    'inconsistencies_detected': len(inconsistencies),
                    'processing_time_ms': processing_time
                },
                success=True,
                processing_time_ms=processing_time
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_fusion.fuse_sources")
            self.metrics_collector.record_response_time(processing_time)

            logger.info(f"Knowledge fusion completed: {fusion_id}, {stored_count} triples fused from {len(sources)} sources")
            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_fusion",
                action="fuse_sources",
                user_id=user_id,
                details={
                    'fusion_id': fusion_id,
                    'sources_count': len(sources),
                    'error': str(e)
                },
                success=False,
                processing_time_ms=processing_time
            )

            self.metrics_collector.record_error("knowledge_fusion.fuse_sources", "fusion_error")
            logger.error(f"Knowledge fusion failed: {fusion_id}, error: {e}")

            return FusionResult(
                fusion_id=fusion_id,
                success=False,
                fused_triples=0,
                conflicts_resolved=0,
                inconsistencies_detected=0,
                processing_time_ms=processing_time,
                strategy_used=config.get('fusion_strategy', FusionStrategy.UNION),
                sources_used=[],
                errors=[str(e)],
                warnings=[]
            )

    async def resolve_conflicts(
        self,
        triples: List[Triple],
        resolution_strategy: ConflictResolution,
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Triple], int]:
        """
        Resolver conflictos entre triples.

        Args:
            triples: Lista de triples con posibles conflictos
            resolution_strategy: Estrategia de resolución
            config: Configuración adicional

        Returns:
            Tupla de (triples_resueltos, conflictos_resueltos)
        """
        if config is None:
            config = {}

        # Agrupar triples por clave (subject + predicate)
        triple_groups = self._group_triples_by_key(triples)
        resolved_triples = []
        conflicts_resolved = 0

        for key, group_triples in triple_groups.items():
            if len(group_triples) == 1:
                # No hay conflicto
                resolved_triples.extend(group_triples)
                continue

            # Resolver conflicto
            resolved, count = await self._resolve_conflict_group(
                group_triples, resolution_strategy, config
            )
            resolved_triples.extend(resolved)
            conflicts_resolved += count

        return resolved_triples, conflicts_resolved

    async def align_ontologies(
        self,
        source_metadata: List[SourceMetadata],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Alinear ontologías entre fuentes.

        Args:
            source_metadata: Metadata de las fuentes
            user_id: ID del usuario

        Returns:
            Resultado de la alineación
        """
        start_time = time.time()

        try:
            alignment_result = {
                'success': True,
                'mappings_created': 0,
                'ontologies_aligned': [],
                'errors': [],
                'warnings': []
            }

            # Identificar ontologías únicas
            ontology_ids = list(set(
                s.ontology_id for s in source_metadata
                if s.ontology_id is not None
            ))

            if len(ontology_ids) <= 1:
                # No hay necesidad de alineación
                return alignment_result

            # Crear mapeos entre ontologías
            for i, source_ontology in enumerate(ontology_ids):
                for target_ontology in ontology_ids[i+1:]:
                    try:
                        mapping_result = await self.ontology_manager.map_concepts(
                            source_ontology, target_ontology, user_id=user_id
                        )

                        if mapping_result.get('mappings_found', 0) > 0:
                            alignment_result['mappings_created'] += mapping_result['mappings_found']
                            alignment_result['ontologies_aligned'].append({
                                'source': source_ontology,
                                'target': target_ontology,
                                'mappings': mapping_result['mappings']
                            })

                    except Exception as e:
                        alignment_result['errors'].append(
                            f"Failed to map {source_ontology} to {target_ontology}: {e}"
                        )

            processing_time = (time.time() - start_time) * 1000

            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_fusion",
                action="align_ontologies",
                user_id=user_id,
                details={
                    'ontologies_count': len(ontology_ids),
                    'mappings_created': alignment_result['mappings_created'],
                    'processing_time_ms': processing_time
                },
                success=alignment_result['success'],
                processing_time_ms=processing_time
            )

            return alignment_result

        except Exception as e:
            logger.error(f"Ontology alignment failed: {e}")
            return {
                'success': False,
                'mappings_created': 0,
                'ontologies_aligned': [],
                'errors': [str(e)],
                'warnings': []
            }

    async def _prepare_source_metadata(self, sources: List[Dict[str, Any]]) -> List[SourceMetadata]:
        """Preparar metadata de fuentes."""
        metadata = []

        for source in sources:
            source_id = source.get('id', str(uuid.uuid4()))
            metadata.append(SourceMetadata(
                source_id=source_id,
                name=source.get('name', f'Source_{source_id}'),
                confidence_score=source.get('confidence', 1.0),
                priority=source.get('priority', 1),
                ontology_id=source.get('ontology_id'),
                last_updated=source.get('last_updated', time.time()),
                triple_count=0  # Se actualizará después
            ))

        return metadata

    async def _collect_triples_from_sources(
        self,
        sources: List[Dict[str, Any]],
        source_metadata: List[SourceMetadata]
    ) -> List[Tuple[Triple, SourceMetadata]]:
        """Recopilar triples de todas las fuentes."""
        all_triples = []

        for source, metadata in zip(sources, source_metadata):
            try:
                # Procesar fuente usando KnowledgeIngestion
                ingestion_result = await self.knowledge_ingestion.ingest_document(
                    source.get('data', ''),
                    source.get('format', 'json_ld'),
                    user_id=None  # TODO: pasar user_id si está disponible
                )

                if ingestion_result.success:
                    # Obtener triples del grafo (simplificado)
                    # En implementación real, consultar triples por fuente
                    triples = []  # TODO: implementar recuperación de triples

                    # Agregar triples con metadata de fuente
                    for triple in triples:
                        all_triples.append((triple, metadata))

                    metadata.triple_count = len(triples)

            except Exception as e:
                logger.warning(f"Failed to process source {metadata.source_id}: {e}")

        return all_triples

    async def _apply_fusion_strategy(
        self,
        triples: List[Tuple[Triple, SourceMetadata]],
        source_metadata: List[SourceMetadata],
        strategy: FusionStrategy
    ) -> List[Tuple[Triple, SourceMetadata]]:
        """Aplicar estrategia de fusión."""
        if strategy == FusionStrategy.UNION:
            return triples  # Todos los triples

        elif strategy == FusionStrategy.INTERSECTION:
            # Solo triples presentes en todas las fuentes
            triple_counts = {}
            for triple, metadata in triples:
                key = triple.to_tuple()
                if key not in triple_counts:
                    triple_counts[key] = []
                triple_counts[key].append(metadata)

            # Filtrar triples presentes en todas las fuentes
            intersected = []
            for key, sources in triple_counts.items():
                if len(sources) == len(source_metadata):
                    # Elegir la fuente con mayor confianza
                    best_source = max(sources, key=lambda s: s.confidence_score)
                    triple = Triple(key[0], key[1], key[2])
                    intersected.append((triple, best_source))

            return intersected

        elif strategy == FusionStrategy.VOTING:
            # Basado en votos ponderados por confianza
            triple_votes = {}
            for triple, metadata in triples:
                key = triple.to_tuple()
                weight = metadata.confidence_score * metadata.priority
                if key not in triple_votes:
                    triple_votes[key] = {'votes': 0, 'sources': []}
                triple_votes[key]['votes'] += weight
                triple_votes[key]['sources'].append(metadata)

            # Filtrar por votos mínimos (mayoría simple)
            min_votes = sum(s.confidence_score for s in source_metadata) / 2
            voted = []
            for key, vote_data in triple_votes.items():
                if vote_data['votes'] >= min_votes:
                    # Elegir fuente con mayor contribución
                    best_source = max(vote_data['sources'], key=lambda s: s.confidence_score)
                    triple = Triple(key[0], key[1], key[2])
                    voted.append((triple, best_source))

            return voted

        elif strategy == FusionStrategy.PRIORITY:
            # Basado en prioridad de fuente
            # Mantener solo triples de fuentes con mayor prioridad
            max_priority = max(s.priority for s in source_metadata)
            high_priority_sources = [s for s in source_metadata if s.priority == max_priority]

            prioritized = []
            for triple, metadata in triples:
                if metadata in high_priority_sources:
                    prioritized.append((triple, metadata))

            return prioritized

        return triples  # Default: union

    async def _resolve_conflict_group(
        self,
        group_triples: List[Tuple[Triple, SourceMetadata]],
        resolution_strategy: ConflictResolution,
        config: Dict[str, Any]
    ) -> Tuple[List[Tuple[Triple, SourceMetadata]], int]:
        """Resolver un grupo de triples conflictivos."""
        if len(group_triples) <= 1:
            return group_triples, 0

        if resolution_strategy == ConflictResolution.LATEST_WINS:
            # Elegir el más reciente
            latest = max(group_triples, key=lambda t: t[1].last_updated or 0)
            return [latest], 1

        elif resolution_strategy == ConflictResolution.HIGHEST_CONFIDENCE:
            # Elegir el de mayor confianza
            highest = max(group_triples, key=lambda t: t[1].confidence_score)
            return [highest], 1

        elif resolution_strategy == ConflictResolution.MAJORITY_VOTE:
            # Voto mayoritario por valor
            value_counts = {}
            for triple, metadata in group_triples:
                value = triple.object
                weight = metadata.confidence_score
                if value not in value_counts:
                    value_counts[value] = {'count': 0, 'sources': []}
                value_counts[value]['count'] += weight
                value_counts[value]['sources'].append(metadata)

            # Elegir valor con más votos
            best_value = max(value_counts.keys(), key=lambda v: value_counts[v]['count'])
            best_source = max(value_counts[best_value]['sources'], key=lambda s: s.confidence_score)

            # Crear triple con valor ganador
            subject = group_triples[0][0].subject
            predicate = group_triples[0][0].predicate
            resolved_triple = Triple(subject, predicate, best_value)

            return [(resolved_triple, best_source)], 1

        elif resolution_strategy == ConflictResolution.MERGE_VALUES:
            # Intentar fusionar valores (para listas o sets)
            subject = group_triples[0][0].subject
            predicate = group_triples[0][0].predicate

            values = [t[0].object for t in group_triples]
            merged_value = self._merge_values(values)

            if merged_value is not None:
                # Elegir fuente con mayor confianza
                best_source = max(group_triples, key=lambda t: t[1].confidence_score)[1]
                resolved_triple = Triple(subject, predicate, merged_value)
                return [(resolved_triple, best_source)], 1
            else:
                # No se pudo fusionar, usar highest_confidence
                highest = max(group_triples, key=lambda t: t[1].confidence_score)
                return [highest], 1

        elif resolution_strategy == ConflictResolution.MANUAL_REVIEW:
            # Marcar para revisión manual (por ahora, usar highest_confidence)
            highest = max(group_triples, key=lambda t: t[1].confidence_score)
            return [highest], 1

        # Default: highest_confidence
        highest = max(group_triples, key=lambda t: t[1].confidence_score)
        return [highest], 1

    def _merge_values(self, values: List[Any]) -> Optional[Any]:
        """Intentar fusionar valores conflictivos."""
        # Si todos son iguales, retornar ese valor
        if len(set(str(v) for v in values)) == 1:
            return values[0]

        # Si son listas, intentar combinar
        if all(isinstance(v, list) for v in values):
            combined = []
            for v in values:
                combined.extend(v)
            return list(set(combined))  # Remover duplicados

        # Si son números, calcular promedio
        if all(isinstance(v, (int, float)) for v in values):
            return sum(values) / len(values)

        # No se puede fusionar
        return None

    def _group_triples_by_key(self, triples: List[Tuple[Triple, SourceMetadata]]) -> Dict[Tuple[str, str], List[Tuple[Triple, SourceMetadata]]]:
        """Agrupar triples por clave (subject, predicate)."""
        groups = {}
        for triple, metadata in triples:
            key = (triple.subject, triple.predicate)
            if key not in groups:
                groups[key] = []
            groups[key].append((triple, metadata))
        return groups

    async def _detect_inconsistencies(
        self,
        triples: List[Tuple[Triple, SourceMetadata]],
        source_metadata: List[SourceMetadata]
    ) -> List[str]:
        """Detectar inconsistencias en los triples."""
        inconsistencies = []

        # Verificar reglas ontológicas
        triple_list = [t[0] for t in triples]
        for ontology_id in set(s.ontology_id for s in source_metadata if s.ontology_id):
            try:
                validation_result = await self.ontology_manager.validate_schema(
                    triple_list, [ontology_id]
                )
                if not validation_result.get('valid', True):
                    inconsistencies.extend(validation_result.get('errors', []))
            except Exception as e:
                inconsistencies.append(f"Ontology validation error for {ontology_id}: {e}")

        # Verificar consistencia lógica básica
        # (Ejemplo: verificar que no haya el mismo sujeto-predicado con valores contradictorios)

        return inconsistencies

    async def _filter_by_confidence(
        self,
        triples: List[Tuple[Triple, SourceMetadata]],
        min_confidence: float
    ) -> List[Tuple[Triple, SourceMetadata]]:
        """Filtrar triples por umbral de confianza."""
        filtered = []
        for triple, metadata in triples:
            if metadata.confidence_score >= min_confidence:
                filtered.append((triple, metadata))
        return filtered

    async def _store_fused_triples(
        self,
        triples: List[Tuple[Triple, SourceMetadata]],
        fusion_id: str,
        user_id: Optional[str]
    ) -> int:
        """Almacenar triples fusionados."""
        stored_count = 0
        for triple, metadata in triples:
            # Agregar metadata de fusión al triple
            enriched_triple = Triple(
                subject=triple.subject,
                predicate=triple.predicate,
                object={
                    'value': triple.object,
                    'fusion_id': fusion_id,
                    'source_id': metadata.source_id,
                    'confidence': metadata.confidence_score
                } if isinstance(triple.object, dict) else triple.object
            )

            if await self.knowledge_graph.add_triple(enriched_triple, user_id):
                stored_count += 1

        return stored_count

    async def _update_confidence_metrics(
        self,
        triples: List[Tuple[Triple, SourceMetadata]],
        source_metadata: List[SourceMetadata]
    ):
        """Actualizar métricas de confianza."""
        for triple, metadata in triples:
            triple_hash = hashlib.md5(str(triple.to_tuple()).encode()).hexdigest()

            if triple_hash not in self.confidence_metrics:
                self.confidence_metrics[triple_hash] = ConfidenceMetrics(
                    triple_hash=triple_hash,
                    confidence_score=metadata.confidence_score,
                    source_count=1,
                    last_updated=time.time(),
                    conflict_history=[]
                )
            else:
                # Actualizar confianza basada en nueva fuente
                existing = self.confidence_metrics[triple_hash]
                existing.confidence_score = (existing.confidence_score + metadata.confidence_score) / 2
                existing.source_count += 1
                existing.last_updated = time.time()

    def get_confidence_metrics(self, triple: Triple) -> Optional[ConfidenceMetrics]:
        """Obtener métricas de confianza para un triple."""
        triple_hash = hashlib.md5(str(triple.to_tuple()).encode()).hexdigest()
        return self.confidence_metrics.get(triple_hash)


# Instancia global
_knowledge_fusion = None

def get_knowledge_fusion() -> KnowledgeFusion:
    """Obtener instancia global del sistema de fusión."""
    global _knowledge_fusion
    if _knowledge_fusion is None:
        _knowledge_fusion = KnowledgeFusion()
    return _knowledge_fusion