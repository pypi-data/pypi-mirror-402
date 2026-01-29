"""
Graph RAG Implementation

This module implements the Graph RAG technique, which leverages knowledge
graphs for enhanced retrieval and reasoning capabilities.
"""

from typing import List, Dict, Any, Optional
import logging
import time

from .naive_rag import NaiveRAG
from ...knowledge_graph.core import get_knowledge_graph_core, KnowledgeGraphCore
from ...knowledge_graph.query_engine import get_query_engine, QueryEngine
from ...knowledge_graph.ontology import get_ontology_manager, OntologyManager
from ...knowledge_graph.inference import get_inference_engine, InferenceEngine
from ...auditing.audit_manager import get_audit_manager, AuditEventType, SecurityAlertLevel

logger = logging.getLogger(__name__)


class GraphRAG(NaiveRAG):
    """
    Graph-based RAG implementation.

    This technique integrates knowledge graphs to provide structured reasoning
    and relationship-aware retrieval for more comprehensive answers.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.graph_config = config.get('graph_config', {})

        # Initialize audit manager
        self.audit_manager = get_audit_manager()

        # Initialize Knowledge Graph components
        kg_backend = self.graph_config.get('backend_type', 'in_memory')
        kg_config = self.graph_config.get('backend_config', {})

        self.kg_core = get_knowledge_graph_core(kg_backend, **kg_config)
        self.query_engine = get_query_engine()
        self.ontology_manager = get_ontology_manager()
        self.inference_engine = get_inference_engine()

        # Configuration for inference and ontology
        self.enable_inference = self.graph_config.get('enable_inference', True)
        self.enable_ontology_enrichment = self.graph_config.get('enable_ontology_enrichment', True)
        self.sparql_queries = self.graph_config.get('sparql_queries', {})

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents using graph-based reasoning with SPARQL and ontological enrichment.

        Args:
            query (str): Search query
            top_k (int): Number of documents to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters

        Returns:
            List[Dict[str, Any]]: Graph-enhanced retrieved documents
        """
        start_time = time.time()

        try:
            # Get vector-based results
            vector_results = super().retrieve(query, top_k=top_k//2, filters=filters)

            # Get graph-based results using SPARQL queries
            import asyncio
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we need to handle differently
                    # For now, create a new thread with its own loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._retrieve_with_sparql(query, top_k=top_k//2, filters=filters))
                        graph_documents = future.result()
                else:
                    graph_documents = asyncio.run(self._retrieve_with_sparql(query, top_k=top_k//2, filters=filters))
            except RuntimeError:
                # No event loop, create one
                graph_documents = asyncio.run(self._retrieve_with_sparql(query, top_k=top_k//2, filters=filters))

            # Combine results with simple weighted aggregation
            all_results = vector_results + graph_documents
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            aggregated_results = all_results[:top_k]

            # Apply ontological enrichment if enabled
            if self.enable_ontology_enrichment:
                try:
                    if asyncio.get_event_loop().is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._enrich_with_ontology(query, aggregated_results))
                            aggregated_results = future.result()
                    else:
                        aggregated_results = asyncio.run(self._enrich_with_ontology(query, aggregated_results))
                except RuntimeError:
                    aggregated_results = asyncio.run(self._enrich_with_ontology(query, aggregated_results))

            # Apply automatic inference if enabled
            if self.enable_inference:
                try:
                    if asyncio.get_event_loop().is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._apply_inference_enrichment(query, aggregated_results))
                            aggregated_results = future.result()
                    else:
                        aggregated_results = asyncio.run(self._apply_inference_enrichment(query, aggregated_results))
                except RuntimeError:
                    aggregated_results = asyncio.run(self._apply_inference_enrichment(query, aggregated_results))

            # Log successful retrieval
            processing_time = (time.time() - start_time) * 1000
            try:
                # Try async logging if in async context
                import asyncio
                if asyncio.iscoroutinefunction(self.audit_manager.log_event):
                    asyncio.create_task(self.audit_manager.log_event(
                        event_type=AuditEventType.SYSTEM_OPERATION,
                        resource="graph_rag",
                        action="retrieve",
                        details={
                            "query": query,
                            "top_k": top_k,
                            "vector_results": len(vector_results),
                            "graph_results": len(graph_documents),
                            "total_results": len(aggregated_results),
                            "filters": filters,
                            "ontology_enrichment": self.enable_ontology_enrichment,
                            "inference_applied": self.enable_inference
                        },
                        processing_time_ms=processing_time,
                        success=True
                    ))
                else:
                    self.audit_manager.log_event(
                        event_type=AuditEventType.SYSTEM_OPERATION,
                        resource="graph_rag",
                        action="retrieve",
                        details={
                            "query": query,
                            "top_k": top_k,
                            "vector_results": len(vector_results),
                            "graph_results": len(graph_documents),
                            "total_results": len(aggregated_results),
                            "filters": filters,
                            "ontology_enrichment": self.enable_ontology_enrichment,
                            "inference_applied": self.enable_inference
                        },
                        processing_time_ms=processing_time,
                        success=True
                    )
            except Exception as log_error:
                logger.debug(f"Could not log audit event: {log_error}")

            # Track response time
            self.audit_manager.track_response_time(processing_time)

            return aggregated_results

        except Exception as e:
            # Log error
            processing_time = (time.time() - start_time) * 1000
            try:
                import asyncio
                if asyncio.iscoroutinefunction(self.audit_manager.log_event):
                    asyncio.create_task(self.audit_manager.log_event(
                        event_type=AuditEventType.SYSTEM_OPERATION,
                        resource="graph_rag",
                        action="retrieve",
                        details={
                            "query": query,
                            "error": str(e),
                            "top_k": top_k
                        },
                        processing_time_ms=processing_time,
                        success=False,
                        severity=SecurityAlertLevel.MEDIUM
                    ))
                else:
                    self.audit_manager.log_event(
                        event_type=AuditEventType.SYSTEM_OPERATION,
                        resource="graph_rag",
                        action="retrieve",
                        details={
                            "query": query,
                            "error": str(e),
                            "top_k": top_k
                        },
                        processing_time_ms=processing_time,
                        success=False,
                        severity=SecurityAlertLevel.MEDIUM
                    )
            except Exception as log_error:
                logger.debug(f"Could not log error audit event: {log_error}")

            logger.error(f"Error in graph retrieval: {str(e)}")
            # Fallback to vector retrieval
            return super().retrieve(query, top_k=top_k, filters=filters)

    def _enhance_with_graph(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance retrieval results with graph-based relationships.

        Args:
            query (str): Original query
            documents (List[Dict[str, Any]]): Initial retrieved documents

        Returns:
            List[Dict[str, Any]]: Enhanced documents
        """
        enhanced_documents = []

        for doc in documents:
            enhanced_doc = doc.copy()

            # Extract entities from document content
            content = doc.get('content', '')
            if content:
                try:
                    # Find related entities in the graph
                    entities = self.graph_builder._extract_entities(content)
                    related_info = []

                    for entity in entities[:3]:  # Limit to top 3 entities
                        entity_id = f"{entity['type']}_{entity['text'].replace(' ', '_').lower()}"

                        # Find related entities
                        related = self.graph_builder.graph.find_related_entities(entity_id, limit=2)
                        if related:
                            related_info.append({
                                'entity': entity['text'],
                                'type': entity['type'],
                                'related': [r['entity'].get('name', r['entity']['id']) for r in related]
                            })

                    if related_info:
                        enhanced_doc['graph_context'] = related_info
                        enhanced_doc['content'] += f"\n\nGraph Context: {len(related_info)} related entities found."

                except Exception as e:
                    logger.debug(f"Could not enhance document with graph: {str(e)}")

            enhanced_documents.append(enhanced_doc)

        return enhanced_documents

    async def _retrieve_with_sparql(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents using SPARQL queries on the knowledge graph.

        Args:
            query (str): Search query
            top_k (int): Number of documents to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters

        Returns:
            List[Dict[str, Any]]: Retrieved documents from graph
        """
        try:
            # Use configured SPARQL query or generate a basic one
            sparql_query = self.sparql_queries.get('retrieval_query',
                """
                SELECT ?subject ?predicate ?object
                WHERE {
                    ?subject ?predicate ?object .
                    FILTER(CONTAINS(LCASE(STR(?object)), LCASE(?query)))
                }
                LIMIT ?
                """)

            # Execute SPARQL query
            parameters = {'query': query, 'limit': top_k}
            if filters:
                parameters.update(filters)

            result = await self.query_engine.execute_query(sparql_query, parameters=parameters)

            # Convert results to document format
            documents = []
            for triple in result.results[:top_k]:
                content = f"{triple.subject} {triple.predicate} {triple.object}"
                documents.append({
                    'id': f"graph_{hash(content)}",
                    'content': content,
                    'metadata': {
                        'subject': triple.subject,
                        'predicate': triple.predicate,
                        'object': triple.object,
                        'source': 'sparql'
                    },
                    'score': 0.8,  # Default score for graph results
                    'source': 'graph'
                })

            return documents

        except Exception as e:
            logger.warning(f"SPARQL retrieval failed: {e}")
            return []

    async def _enrich_with_ontology(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich documents with ontological information.

        Args:
            query (str): Original query
            documents (List[Dict[str, Any]]): Documents to enrich

        Returns:
            List[Dict[str, Any]]: Ontology-enriched documents
        """
        if not self.ontology_manager:
            return documents

        enriched_documents = []

        for doc in documents:
            enriched_doc = doc.copy()

            try:
                # Extract entities from content
                content = doc.get('content', '')
                entities = self._extract_entities_from_text(content)

                # Get ontological enrichment for each entity
                ontology_context = []
                for entity in entities[:3]:  # Limit to top 3 entities
                    # Query ontology for related concepts
                    related_query = f"""
                    SELECT ?related ?label
                    WHERE {{
                        <{entity}> ?relation ?related .
                        OPTIONAL {{ ?related <http://www.w3.org/2000/01/rdf-schema#label> ?label }}
                    }}
                    LIMIT 5
                    """

                    try:
                        result = await self.query_engine.execute_query(related_query)
                        if result.results:
                            ontology_context.append({
                                'entity': entity,
                                'related_concepts': [
                                    {
                                        'uri': triple.object,
                                        'label': triple.object if len(result.results) < 2 else result.results[1].object
                                    } for triple in result.results
                                ]
                            })
                    except Exception as e:
                        logger.debug(f"Ontology query failed for entity {entity}: {e}")

                if ontology_context:
                    enriched_doc['ontology_context'] = ontology_context
                    enriched_doc['content'] += f"\n\nOntology Context: {len(ontology_context)} enriched entities."

            except Exception as e:
                logger.debug(f"Ontology enrichment failed for document: {e}")

            enriched_documents.append(enriched_doc)

        return enriched_documents

    async def _apply_inference_enrichment(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply automatic inference to enrich documents.

        Args:
            query (str): Original query
            documents (List[Dict[str, Any]]): Documents to enrich

        Returns:
            List[Dict[str, Any]]: Inference-enriched documents
        """
        if not self.inference_engine:
            return documents

        try:
            # Run inference on the knowledge graph
            inference_result = await self.inference_engine.infer(max_depth=3)

            if inference_result.inferred_triples:
                # Add inference context to documents
                inference_context = {
                    'inferred_triples_count': len(inference_result.inferred_triples),
                    'rules_applied': inference_result.rules_applied,
                    'confidence': inference_result.confidence_score
                }

                for doc in documents:
                    doc['inference_context'] = inference_context
                    doc['content'] += f"\n\nInference Context: {len(inference_result.inferred_triples)} inferred relationships."

        except Exception as e:
            logger.debug(f"Inference enrichment failed: {e}")

        return documents

    def _extract_entities_from_text(self, text: str) -> List[str]:
        """
        Extract potential entity URIs from text.

        Args:
            text (str): Text to analyze

        Returns:
            List[str]: Potential entity URIs
        """
        # Simple extraction - look for URI patterns
        import re
        uri_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        uris = re.findall(uri_pattern, text)

        # Also extract potential entity names (capitalized words)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        potential_entities = words[:5]  # Limit to avoid noise

        return uris + potential_entities

    async def build_graph_from_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build knowledge graph from documents using KnowledgeGraphCore.

        Args:
            documents (List[Dict[str, Any]]): Documents to process
        """
        start_time = time.time()

        try:
            # Convert documents to triples and add to knowledge graph
            triples_added = 0
            for doc in documents:
                content = doc.get('content', '')
                doc_id = doc.get('id', f"doc_{hash(content)}")

                # Create basic triples from document content
                # This is a simplified implementation - in production, use NLP for entity extraction
                sentences = content.split('.')
                for sentence in sentences:
                    if sentence.strip():
                        # Create subject-predicate-object triples
                        subject = f"doc:{doc_id}"
                        predicate = "content:hasText"
                        obj = sentence.strip()

                        from ..knowledge_graph.core import Triple
                        triple = Triple(subject, predicate, obj)
                        success = await self.kg_core.add_triple(triple)
                        if success:
                            triples_added += 1

            # Log successful graph building
            processing_time = (time.time() - start_time) * 1000
            try:
                import asyncio
                asyncio.create_task(self.audit_manager.log_event(
                    event_type=AuditEventType.SYSTEM_OPERATION,
                    resource="graph_rag",
                    action="build_graph",
                    details={
                        "documents_processed": len(documents),
                        "triples_added": triples_added,
                        "graph_stats": await self.kg_core.get_stats()
                    },
                    processing_time_ms=processing_time,
                    success=True
                ))
            except Exception as log_error:
                logger.debug(f"Could not log graph building event: {log_error}")

            logger.info(f"Built knowledge graph from {len(documents)} documents: {triples_added} triples added")

        except Exception as e:
            # Log error
            processing_time = (time.time() - start_time) * 1000
            try:
                import asyncio
                asyncio.create_task(self.audit_manager.log_event(
                    event_type=AuditEventType.SYSTEM_OPERATION,
                    resource="graph_rag",
                    action="build_graph",
                    details={
                        "documents_attempted": len(documents),
                        "error": str(e)
                    },
                    processing_time_ms=processing_time,
                    success=False,
                    severity=SecurityAlertLevel.HIGH
                ))
            except Exception as log_error:
                logger.debug(f"Could not log graph building error: {log_error}")

            logger.error(f"Error building graph: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None) -> None:
        """
        Add documents to the RAG system and update the knowledge graph.

        Args:
            documents (List[Dict[str, Any]]): Documents to add
            embeddings (Optional[List[List[float]]]): Pre-computed embeddings
        """
        # Add to vector store
        super().add_documents(documents, embeddings)

        # Add to knowledge graph
        import asyncio
        try:
            if asyncio.get_event_loop().is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.build_graph_from_documents(documents))
                    future.result()
            else:
                asyncio.run(self.build_graph_from_documents(documents))
        except RuntimeError:
            asyncio.run(self.build_graph_from_documents(documents))

    def get_pipeline_info(self) -> Dict[str, Any]:
        info = super().get_pipeline_info()

        # Get stats from new components
        graph_stats = {}
        try:
            import asyncio
            # Since get_stats is async, we need to handle it carefully
            # For now, provide basic info
            graph_stats = {
                'backend_type': self.kg_core.backend_type.value if hasattr(self.kg_core, 'backend_type') else 'unknown',
                'components': ['KnowledgeGraphCore', 'QueryEngine', 'OntologyManager', 'InferenceEngine']
            }
        except Exception as e:
            logger.debug(f"Could not get graph stats: {e}")

        info.update({
            'technique': 'GraphRAG',
            'description': 'Graph-based RAG with SPARQL queries, ontological enrichment, and automatic inference',
            'graph_config': self.graph_config,
            'graph_stats': graph_stats,
            'features': [
                'SPARQL query support',
                'Ontological enrichment',
                'Automatic inference with OWL rules',
                'Multi-hop reasoning',
                'Hybrid vector-graph search',
                'Knowledge graph integration'
            ],
            'components': {
                'knowledge_graph_core': 'KnowledgeGraphCore',
                'query_engine': 'QueryEngine',
                'ontology_manager': 'OntologyManager',
                'inference_engine': 'InferenceEngine'
            },
            'capabilities': {
                'sparql_queries': bool(self.sparql_queries),
                'ontology_enrichment': self.enable_ontology_enrichment,
                'automatic_inference': self.enable_inference
            }
        })
        return info