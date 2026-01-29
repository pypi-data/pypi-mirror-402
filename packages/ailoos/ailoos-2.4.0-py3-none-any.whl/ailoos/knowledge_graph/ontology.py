"""
Ontology Management para AILOOS.
Implementa gestión de ontologías con carga, validación, evolución y mapeo semántico.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from enum import Enum
import hashlib

try:
    import rdflib
    from rdflib import Graph, URIRef, Literal, BNode, Namespace
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False

from ..core.logging import get_logger
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from .core import get_knowledge_graph_core, FormatType, Triple

logger = get_logger(__name__)


class OntologyFormat(Enum):
    """Formatos de ontología soportados."""
    OWL = "owl"
    RDF = "rdf"
    TTL = "ttl"  # Turtle
    NT = "nt"    # N-Triples


class OntologyManager:
    """
    Gestor de ontologías para el sistema de grafos de conocimiento.
    Maneja carga, validación, evolución y mapeo de ontologías.
    """

    def __init__(self, knowledge_graph_core=None, audit_manager=None, metrics_collector=None):
        """
        Inicializar OntologyManager.

        Args:
            knowledge_graph_core: Instancia de KnowledgeGraphCore
            audit_manager: Instancia de AuditManager
            metrics_collector: Instancia de MetricsCollector
        """
        self.knowledge_graph = knowledge_graph_core or get_knowledge_graph_core()
        self.audit_manager = audit_manager or get_audit_manager()
        self.metrics_collector = metrics_collector or get_metrics_collector()

        # Ontologías cargadas
        self.loaded_ontologies: Dict[str, Any] = {}
        self.ontology_metadata: Dict[str, Dict[str, Any]] = {}

        # Namespaces comunes
        if RDFLIB_AVAILABLE:
            self.namespaces = {
                'owl': Namespace('http://www.w3.org/2002/07/owl#'),
                'rdf': Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
                'rdfs': Namespace('http://www.w3.org/2000/01/rdf-schema#'),
                'xsd': Namespace('http://www.w3.org/2001/XMLSchema#')
            }
        else:
            # Fallback namespaces como strings
            self.namespaces = {
                'owl': 'http://www.w3.org/2002/07/owl#',
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'xsd': 'http://www.w3.org/2001/XMLSchema#',
                'label': 'http://www.w3.org/2000/01/rdf-schema#label'
            }

        if not RDFLIB_AVAILABLE:
            logger.warning("rdflib no está disponible. Funcionalidad de ontologías limitada.")

    async def load_ontology(
        self,
        source: Union[str, Path],
        ontology_id: str,
        format_type: Optional[OntologyFormat] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Cargar una ontología desde archivo o string.

        Args:
            source: Ruta al archivo o contenido de la ontología
            ontology_id: ID único para la ontología
            format_type: Formato de la ontología (auto-detectado si None)
            user_id: ID del usuario que realiza la operación

        Returns:
            True si se cargó exitosamente
        """
        start_time = time.time()

        try:
            if not RDFLIB_AVAILABLE:
                raise ImportError("rdflib es requerido para cargar ontologías")

            # Detectar formato si no se especifica
            if format_type is None:
                format_type = self._detect_format(source)

            # Crear grafo RDF
            graph = Graph()

            # Agregar namespaces comunes
            for prefix, ns in self.namespaces.items():
                graph.bind(prefix, ns)

            # Cargar ontología
            if isinstance(source, (str, Path)) and Path(source).exists():
                # Cargar desde archivo
                file_path = Path(source)
                format_map = {
                    OntologyFormat.OWL: 'xml',
                    OntologyFormat.RDF: 'xml',
                    OntologyFormat.TTL: 'turtle',
                    OntologyFormat.NT: 'nt'
                }

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                graph.parse(data=content, format=format_map.get(format_type, 'xml'))

            elif isinstance(source, str):
                # Cargar desde string
                format_map = {
                    OntologyFormat.OWL: 'xml',
                    OntologyFormat.RDF: 'xml',
                    OntologyFormat.TTL: 'turtle',
                    OntologyFormat.NT: 'nt'
                }

                graph.parse(data=source, format=format_map.get(format_type, 'xml'))
            else:
                raise ValueError("Source debe ser una ruta válida o contenido string")

            # Validar ontología básica
            await self._validate_ontology_basic(graph)

            # Almacenar ontología
            self.loaded_ontologies[ontology_id] = graph

            # Metadata
            self.ontology_metadata[ontology_id] = {
                'format': format_type.value,
                'triples_count': len(graph),
                'loaded_at': time.time(),
                'source': str(source) if isinstance(source, Path) else 'string',
                'namespaces': dict(graph.namespaces())
            }

            # Agregar triples al knowledge graph core para validación automática
            triples = []
            for subj, pred, obj in graph:
                subj_str = str(subj)
                pred_str = str(pred)
                obj_val = obj.toPython() if hasattr(obj, 'toPython') else str(obj)
                triples.append(Triple(subj_str, pred_str, obj_val))

            # Cargar triples en el grafo de conocimiento
            success_count = 0
            for triple in triples:
                if await self.knowledge_graph.add_triple(triple, user_id):
                    success_count += 1

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="load_ontology",
                user_id=user_id,
                details={
                    'ontology_id': ontology_id,
                    'format': format_type.value,
                    'total_triples': len(triples),
                    'success_count': success_count,
                    'source': str(source) if isinstance(source, Path) else 'string'
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("ontology.load_ontology")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Ontología '{ontology_id}' cargada exitosamente: {success_count}/{len(triples)} triples")
            return True

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="load_ontology",
                user_id=user_id,
                details={
                    'ontology_id': ontology_id,
                    'error': str(e),
                    'source': str(source) if isinstance(source, Path) else 'string'
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("ontology.load_ontology", "load_error")
            logger.error(f"Error cargando ontología '{ontology_id}': {e}")
            return False

    async def validate_schema(
        self,
        data: Union[Dict[str, Any], List[Triple]],
        ontology_ids: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validar datos contra ontologías cargadas.

        Args:
            data: Datos a validar (dict o lista de triples)
            ontology_ids: IDs de ontologías a usar para validación
            user_id: ID del usuario

        Returns:
            Resultado de validación con errores y warnings
        """
        start_time = time.time()

        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'checked_triples': 0,
                'ontologies_used': ontology_ids
            }

            # Convertir datos a triples si es necesario
            triples = self._data_to_triples(data)

            # Validar contra cada ontología
            for ontology_id in ontology_ids:
                if ontology_id not in self.loaded_ontologies:
                    validation_result['errors'].append(f"Ontología '{ontology_id}' no encontrada")
                    validation_result['valid'] = False
                    continue

                ontology_graph = self.loaded_ontologies[ontology_id]

                # Validar triples contra ontología
                for triple in triples:
                    validation_result['checked_triples'] += 1

                    # Verificar restricciones de dominio/rango
                    domain_errors = await self._validate_domain_range(triple, ontology_graph)
                    validation_result['errors'].extend(domain_errors)

                    # Verificar cardinalidad
                    cardinality_errors = await self._validate_cardinality(triple, ontology_graph, triples)
                    validation_result['errors'].extend(cardinality_errors)

                    # Verificar tipos de datos
                    type_warnings = await self._validate_data_types(triple, ontology_graph)
                    validation_result['warnings'].extend(type_warnings)

            validation_result['valid'] = len(validation_result['errors']) == 0

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="validate_schema",
                user_id=user_id,
                details={
                    'ontologies_used': ontology_ids,
                    'checked_triples': validation_result['checked_triples'],
                    'errors_count': len(validation_result['errors']),
                    'warnings_count': len(validation_result['warnings']),
                    'valid': validation_result['valid']
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("ontology.validate_schema")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Validación de esquema completada: {validation_result['checked_triples']} triples, "
                       f"{len(validation_result['errors'])} errores, {len(validation_result['warnings'])} warnings")

            return validation_result

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="validate_schema",
                user_id=user_id,
                details={
                    'ontologies_used': ontology_ids,
                    'error': str(e)
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("ontology.validate_schema", "validation_error")
            logger.error(f"Error en validación de esquema: {e}")

            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'checked_triples': 0,
                'ontologies_used': ontology_ids
            }

    async def evolve_concept(
        self,
        ontology_id: str,
        concept_uri: str,
        changes: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Evolucionar un concepto en la ontología.

        Args:
            ontology_id: ID de la ontología
            concept_uri: URI del concepto a evolucionar
            changes: Cambios a aplicar (agregar propiedades, restricciones, etc.)
            user_id: ID del usuario

        Returns:
            True si se evolucionó exitosamente
        """
        start_time = time.time()

        try:
            if ontology_id not in self.loaded_ontologies:
                raise ValueError(f"Ontología '{ontology_id}' no encontrada")

            graph = self.loaded_ontologies[ontology_id]
            concept_node = URIRef(concept_uri)

            # Aplicar cambios
            triples_added = 0

            # Agregar nuevas propiedades
            if 'properties' in changes:
                for prop_uri, prop_value in changes['properties'].items():
                    prop_node = URIRef(prop_uri)
                    if isinstance(prop_value, str) and prop_value.startswith('http'):
                        obj_node = URIRef(prop_value)
                    else:
                        obj_node = Literal(prop_value)

                    graph.add((concept_node, prop_node, obj_node))
                    triples_added += 1

            # Agregar restricciones
            if 'restrictions' in changes:
                for restriction in changes['restrictions']:
                    # Implementación simplificada de restricciones OWL
                    if RDFLIB_AVAILABLE:
                        restriction_node = BNode()
                        graph.add((restriction_node, self.namespaces['rdf'].type, self.namespaces['owl'].Restriction))
                        graph.add((restriction_node, self.namespaces['owl'].onProperty, URIRef(restriction['property'])))
                        graph.add((restriction_node, URIRef(restriction['type']), URIRef(restriction['value'])))
                        graph.add((concept_node, self.namespaces['rdfs'].subClassOf, restriction_node))
                    triples_added += 1

            # Actualizar metadata
            self.ontology_metadata[ontology_id]['last_modified'] = time.time()
            self.ontology_metadata[ontology_id]['triples_count'] = len(graph)

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="evolve_concept",
                user_id=user_id,
                details={
                    'ontology_id': ontology_id,
                    'concept_uri': concept_uri,
                    'changes': changes,
                    'triples_added': triples_added
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("ontology.evolve_concept")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Concepto '{concept_uri}' evolucionado en ontología '{ontology_id}': {triples_added} triples agregados")
            return True

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="evolve_concept",
                user_id=user_id,
                details={
                    'ontology_id': ontology_id,
                    'concept_uri': concept_uri,
                    'changes': changes,
                    'error': str(e)
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("ontology.evolve_concept", "evolution_error")
            logger.error(f"Error evolucionando concepto '{concept_uri}': {e}")
            return False

    async def map_concepts(
        self,
        source_ontology_id: str,
        target_ontology_id: str,
        mapping_rules: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mapear conceptos entre dos ontologías.

        Args:
            source_ontology_id: ID de ontología fuente
            target_ontology_id: ID de ontología destino
            mapping_rules: Reglas de mapeo opcionales
            user_id: ID del usuario

        Returns:
            Mapeos encontrados con confianza
        """
        start_time = time.time()

        try:
            if source_ontology_id not in self.loaded_ontologies:
                raise ValueError(f"Ontología fuente '{source_ontology_id}' no encontrada")
            if target_ontology_id not in self.loaded_ontologies:
                raise ValueError(f"Ontología destino '{target_ontology_id}' no encontrada")

            source_graph = self.loaded_ontologies[source_ontology_id]
            target_graph = self.loaded_ontologies[target_ontology_id]

            mappings = []

            # Mapeo por etiquetas similares (implementación simplificada)
            source_labels = self._extract_labels(source_graph)
            target_labels = self._extract_labels(target_graph)

            for source_uri, source_label in source_labels.items():
                for target_uri, target_label in target_labels.items():
                    # Calcular similitud simple (puede mejorarse con embeddings)
                    similarity = self._calculate_string_similarity(source_label.lower(), target_label.lower())

                    if similarity > 0.8:  # Umbral de similitud
                        mappings.append({
                            'source_uri': source_uri,
                            'target_uri': target_uri,
                            'source_label': source_label,
                            'target_label': target_label,
                            'similarity': similarity,
                            'confidence': similarity
                        })

            # Aplicar reglas de mapeo personalizadas si se proporcionan
            if mapping_rules:
                custom_mappings = await self._apply_mapping_rules(
                    source_graph, target_graph, mapping_rules
                )
                mappings.extend(custom_mappings)

            # Remover duplicados y ordenar por confianza
            unique_mappings = self._deduplicate_mappings(mappings)

            mapping_result = {
                'mappings_found': len(unique_mappings),
                'mappings': unique_mappings[:100],  # Limitar resultados
                'source_ontology': source_ontology_id,
                'target_ontology': target_ontology_id
            }

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="map_concepts",
                user_id=user_id,
                details={
                    'source_ontology': source_ontology_id,
                    'target_ontology': target_ontology_id,
                    'mappings_found': len(unique_mappings)
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("ontology.map_concepts")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Mapeo de conceptos completado: {len(unique_mappings)} mapeos encontrados")
            return mapping_result

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="ontology",
                action="map_concepts",
                user_id=user_id,
                details={
                    'source_ontology': source_ontology_id,
                    'target_ontology': target_ontology_id,
                    'error': str(e)
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("ontology.map_concepts", "mapping_error")
            logger.error(f"Error en mapeo de conceptos: {e}")

            return {
                'mappings_found': 0,
                'mappings': [],
                'source_ontology': source_ontology_id,
                'target_ontology': target_ontology_id,
                'error': str(e)
            }

    def _detect_format(self, source: Union[str, Path]) -> OntologyFormat:
        """Detectar formato de ontología."""
        if isinstance(source, Path):
            extension = source.suffix.lower()
            if extension in ['.owl', '.rdf', '.xml']:
                return OntologyFormat.OWL if extension == '.owl' else OntologyFormat.RDF
            elif extension == '.ttl':
                return OntologyFormat.TTL
            elif extension == '.nt':
                return OntologyFormat.NT
        else:
            # Detectar por contenido
            content = source[:200].lower()
            if 'owl:' in content or 'ontology' in content:
                return OntologyFormat.OWL
            elif '@prefix' in content:
                return OntologyFormat.TTL

        return OntologyFormat.RDF  # Default

    async def _validate_ontology_basic(self, graph):
        """Validación básica de ontología."""
        if len(graph) == 0:
            raise ValueError("Ontología vacía")

        # Verificar que tenga al menos una declaración de ontología OWL
        has_ontology_declaration = False
        for subj, pred, obj in graph:
            if RDFLIB_AVAILABLE:
                rdf_type = self.namespaces['rdf'].type
                owl_ontology = self.namespaces['owl'].Ontology
            else:
                rdf_type = self.namespaces['rdf'] + "type"
                owl_ontology = self.namespaces['owl'] + "Ontology"
            if str(pred) == rdf_type and str(obj) == owl_ontology:
                has_ontology_declaration = True
                break

        if not has_ontology_declaration:
            logger.warning("Ontología sin declaración OWL formal")

    def _data_to_triples(self, data: Union[Dict[str, Any], List[Triple]]) -> List[Triple]:
        """Convertir datos a triples."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            triples = []
            for key, value in data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        triples.append(Triple(key, sub_key, sub_value))
                else:
                    triples.append(Triple(key, 'value', value))
            return triples
        else:
            raise ValueError("Formato de datos no soportado")

    async def _validate_domain_range(self, triple: Triple, ontology) -> List[str]:
        """Validar dominio y rango de propiedades."""
        errors = []
        pred_uri = URIRef(triple.predicate)

        # Consultar dominio
        domain_query = f"""
        SELECT ?domain WHERE {{
            <{pred_uri}> <http://www.w3.org/2000/01/rdf-schema#domain> ?domain .
        }}
        """

        try:
            domain_results = list(ontology.query(domain_query))
            if domain_results:
                expected_domain = str(domain_results[0][0])
                # Validación simplificada - en producción verificar jerarquía de clases
                logger.debug(f"Propiedad {triple.predicate} tiene dominio {expected_domain}")
        except Exception as e:
            errors.append(f"Error validando dominio de {triple.predicate}: {e}")

        return errors

    async def _validate_cardinality(self, triple: Triple, ontology, all_triples: List[Triple]) -> List[str]:
        """Validar restricciones de cardinalidad."""
        errors = []
        # Implementación simplificada - contar ocurrencias
        pred_count = sum(1 for t in all_triples if t.predicate == triple.predicate and t.subject == triple.subject)

        # Verificar restricciones OWL
        cardinality_query = f"""
        SELECT ?min ?max WHERE {{
            ?restriction <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> .
            ?restriction <http://www.w3.org/2002/07/owl#onProperty> <{triple.predicate}> .
            OPTIONAL {{ ?restriction <http://www.w3.org/2002/07/owl#minCardinality> ?min . }}
            OPTIONAL {{ ?restriction <http://www.w3.org/2002/07/owl#maxCardinality> ?max . }}
        }}
        """

        try:
            results = list(ontology.query(cardinality_query))
            for result in results:
                min_card = result[0].toPython() if result[0] else None
                max_card = result[1].toPython() if result[1] else None

                if min_card and pred_count < min_card:
                    errors.append(f"Violación de cardinalidad mínima: {pred_count} < {min_card} para {triple.predicate}")
                if max_card and pred_count > max_card:
                    errors.append(f"Violación de cardinalidad máxima: {pred_count} > {max_card} para {triple.predicate}")
        except Exception as e:
            logger.debug(f"Error en validación de cardinalidad: {e}")

        return errors

    async def _validate_data_types(self, triple: Triple, ontology) -> List[str]:
        """Validar tipos de datos."""
        warnings = []
        pred_uri = URIRef(triple.predicate)

        # Consultar rango
        range_query = f"""
        SELECT ?range WHERE {{
            <{pred_uri}> <http://www.w3.org/2000/01/rdf-schema#range> ?range .
        }}
        """

        try:
            range_results = list(ontology.query(range_query))
            if range_results:
                expected_range = str(range_results[0][0])
                # Validación simplificada de tipos
                if expected_range == 'http://www.w3.org/2001/XMLSchema#integer' and not isinstance(triple.object, int):
                    warnings.append(f"Tipo esperado integer para {triple.predicate}, recibido {type(triple.object)}")
                elif expected_range == 'http://www.w3.org/2001/XMLSchema#string' and not isinstance(triple.object, str):
                    warnings.append(f"Tipo esperado string para {triple.predicate}, recibido {type(triple.object)}")
        except Exception as e:
            logger.debug(f"Error en validación de tipos: {e}")

        return warnings

    def _extract_labels(self, graph) -> Dict[str, str]:
        """Extraer etiquetas de conceptos de la ontología."""
        labels = {}

        for subj, pred, obj in graph:
            if RDFLIB_AVAILABLE:
                rdfs_label = self.namespaces['rdfs'].label
            else:
                rdfs_label = self.namespaces['label']
            if str(pred) == rdfs_label or str(pred) == 'http://www.w3.org/2000/01/rdf-schema#label':
                if RDFLIB_AVAILABLE and isinstance(obj, Literal):
                    labels[str(subj)] = str(obj)
                elif not RDFLIB_AVAILABLE:
                    labels[str(subj)] = str(obj)

        return labels

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calcular similitud simple entre strings."""
        # Implementación básica de Jaccard similarity
        set1 = set(str1.split())
        set2 = set(str2.split())

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    async def _apply_mapping_rules(self, source_graph, target_graph, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aplicar reglas de mapeo personalizadas."""
        mappings = []

        # Implementación simplificada - ejecutar queries SPARQL personalizadas
        if 'sparql_mappings' in rules:
            for mapping_rule in rules['sparql_mappings']:
                try:
                    source_query = mapping_rule.get('source_query', '')
                    target_query = mapping_rule.get('target_query', '')

                    source_results = list(source_graph.query(source_query))
                    target_results = list(target_graph.query(target_query))

                    # Crear mapeos basados en resultados
                    for source_result in source_results:
                        for target_result in target_results:
                            if len(source_result) > 0 and len(target_result) > 0:
                                mappings.append({
                                    'source_uri': str(source_result[0]),
                                    'target_uri': str(target_result[0]),
                                    'similarity': 1.0,
                                    'confidence': 0.9,
                                    'rule_based': True
                                })
                except Exception as e:
                    logger.debug(f"Error aplicando regla de mapeo: {e}")

        return mappings

    def _deduplicate_mappings(self, mappings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remover mapeos duplicados."""
        seen = set()
        unique_mappings = []

        for mapping in mappings:
            key = (mapping['source_uri'], mapping['target_uri'])
            if key not in seen:
                seen.add(key)
                unique_mappings.append(mapping)

        return sorted(unique_mappings, key=lambda x: x.get('confidence', 0), reverse=True)

    def get_loaded_ontologies(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de ontologías cargadas."""
        return self.ontology_metadata.copy()

    async def unload_ontology(self, ontology_id: str, user_id: Optional[str] = None) -> bool:
        """Descargar una ontología."""
        try:
            if ontology_id in self.loaded_ontologies:
                del self.loaded_ontologies[ontology_id]
                del self.ontology_metadata[ontology_id]

                await self.audit_manager.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource="ontology",
                    action="unload_ontology",
                    user_id=user_id,
                    details={'ontology_id': ontology_id},
                    success=True
                )

                logger.info(f"Ontología '{ontology_id}' descargada")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error descargando ontología '{ontology_id}': {e}")
            return False


# Instancia global
_ontology_manager = None

def get_ontology_manager() -> OntologyManager:
    """Obtener instancia global del gestor de ontologías."""
    global _ontology_manager
    if _ontology_manager is None:
        _ontology_manager = OntologyManager()
    return _ontology_manager