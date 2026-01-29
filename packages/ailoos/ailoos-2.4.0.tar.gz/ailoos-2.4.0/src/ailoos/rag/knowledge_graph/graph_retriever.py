"""
Knowledge Graph Retriever

This module provides retrieval capabilities based on knowledge graph
relationships and structured queries for RAG systems.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import heapq

from .neo4j_graph import Neo4jGraph
from .query_processor import CypherQueryProcessor
from ..core.retriever import Retriever

logger = logging.getLogger(__name__)


class GraphRetriever(Retriever):
    """
    Retriever that uses knowledge graph for structured information retrieval.

    This class combines graph traversal, relationship queries, and semantic
    search to provide comprehensive retrieval capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the graph retriever.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - graph_config: Configuration for the graph database
                - retrieval_config: Settings for retrieval strategies
                - embedding_config: Configuration for semantic search
        """
        super().__init__(config)
        self.graph_config = config.get('graph_config', {})
        self.retrieval_config = config.get('retrieval_config', {})

        # Initialize graph connection
        self.graph = Neo4jGraph(self.graph_config)

        # Initialize query processor
        self.query_processor = CypherQueryProcessor(self.graph)

        # Retrieval strategies
        self.strategies = {
            'entity_focused': self._retrieve_entity_focused,
            'relationship_based': self._retrieve_relationship_based,
            'path_based': self._retrieve_path_based,
            'semantic_graph': self._retrieve_semantic_graph,
            'multi_hop': self._retrieve_multi_hop,
            'centrality_based': self._retrieve_centrality_based,
            'cypher_query': self._retrieve_with_cypher
        }

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None,
               threshold: Optional[float] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search the knowledge graph for relevant information.

        Args:
            query (str): Search query
            top_k (int): Number of top results to return
            filters (Optional[Dict[str, Any]]): Metadata filters
            threshold (Optional[float]): Relevance threshold

        Returns:
            List[Tuple[Dict[str, Any], float]]: List of (document, score) pairs
        """
        try:
            # Determine retrieval strategy
            strategy = self._choose_strategy(query)

            # Execute retrieval
            results = self.strategies[strategy](query, top_k, filters)

            # Apply threshold filtering
            if threshold is not None:
                results = [(doc, score) for doc, score in results if score >= threshold]

            # Sort by score and limit
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]

            logger.debug(f"Graph retrieval returned {len(results)} results using {strategy} strategy")
            return results

        except Exception as e:
            logger.error(f"Error during graph retrieval: {str(e)}")
            raise

    def _choose_strategy(self, query: str) -> str:
        """
        Choose the most appropriate retrieval strategy for the query.

        Args:
            query (str): Search query

        Returns:
            str: Strategy name
        """
        # Strategy selection based on query characteristics
        query_lower = query.lower()

        if query.strip().upper().startswith(('MATCH', 'CREATE', 'MERGE', 'RETURN')):
            return 'cypher_query'
        elif any(word in query_lower for word in ['multi-hop', 'reasoning', 'inference']):
            return 'multi_hop'
        elif any(word in query_lower for word in ['central', 'important', 'key']):
            return 'centrality_based'
        elif any(word in query_lower for word in ['relationship', 'connected', 'related']):
            return 'relationship_based'
        elif any(word in query_lower for word in ['path', 'route', 'connection']):
            return 'path_based'
        elif len(query.split()) <= 3:
            return 'entity_focused'
        else:
            return 'semantic_graph'

    def _retrieve_entity_focused(self, query: str, top_k: int,
                               filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve information focused on specific entities.

        Args:
            query (str): Entity-focused query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Search for entities matching the query
        entities = self.graph.search_by_text(query)

        results = []
        for entity in entities[:top_k]:
            # Get related information
            related = self.graph.find_related_entities(entity['id'])

            # Create document from entity and relationships
            content = f"Entity: {entity.get('name', entity['id'])}\n"
            content += f"Type: {entity.get('type', 'Unknown')}\n"
            content += f"Related entities: {len(related)}\n"

            document = {
                'id': entity['id'],
                'content': content,
                'type': 'entity',
                'metadata': entity
            }

            results.append((document, 0.9))  # High confidence for direct matches

        return results

    def _retrieve_relationship_based(self, query: str, top_k: int,
                                   filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve based on relationship patterns.

        Args:
            query (str): Relationship query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Parse relationship query (simplified)
        # In practice, this would use NLP to extract entities and relationship types

        # Mock: find all relationships
        entities = self.graph.query_entities(limit=20)

        results = []
        for entity in entities:
            related = self.graph.find_related_entities(entity['id'])
            if related:
                content = f"Entity {entity['id']} has {len(related)} relationships:\n"
                for rel in related[:5]:
                    rel_entity = rel['entity']
                    content += f"- {rel['relationship'].get('type', 'RELATED')} {rel_entity.get('name', rel_entity['id'])}\n"

                document = {
                    'id': f"rel_{entity['id']}",
                    'content': content,
                    'type': 'relationships'
                }

                results.append((document, 0.8))

        return results[:top_k]

    def _retrieve_path_based(self, query: str, top_k: int,
                           filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve based on graph paths between entities.

        Args:
            query (str): Path-based query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Find paths between entities mentioned in query
        # This is a simplified implementation

        entities = self.graph.search_by_text(query, limit=5)

        if len(entities) >= 2:
            # Find connections between first two entities
            entity1, entity2 = entities[0], entities[1]

            # Check if they're directly related
            related_to_1 = self.graph.find_related_entities(entity1['id'])
            related_ids = {rel['entity']['id'] for rel in related_to_1}

            if entity2['id'] in related_ids:
                content = f"Direct relationship found between {entity1.get('name', entity1['id'])} and {entity2.get('name', entity2['id'])}"
                document = {
                    'id': f"path_{entity1['id']}_{entity2['id']}",
                    'content': content,
                    'type': 'path'
                }
                return [(document, 0.95)]

        # Fallback: return entity information
        return self._retrieve_entity_focused(query, top_k, filters)

    def _retrieve_semantic_graph(self, query: str, top_k: int,
                               filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve using semantic understanding of the graph.

        Args:
            query (str): Semantic query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Use embeddings to find semantically similar content in the graph
        query_embedding = self.get_embedding(query)

        # Search entities by semantic similarity
        entities = self.graph.query_entities(limit=50)

        # Mock semantic scoring
        results = []
        for entity in entities:
            # In practice, compare embeddings
            semantic_score = 0.7  # Mock score

            content = f"Semantic match: {entity.get('name', entity['id'])}"
            if 'description' in entity:
                content += f"\nDescription: {entity['description']}"

            document = {
                'id': entity['id'],
                'content': content,
                'type': 'semantic'
            }

            results.append((document, semantic_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _retrieve_multi_hop(self, query: str, top_k: int,
                           filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve using multi-hop reasoning through the graph.

        Args:
            query (str): Multi-hop query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Extract entities from query
        entities = self.graph.search_by_text(query, limit=3)

        if len(entities) >= 2:
            # Find multi-hop paths between entities
            start_entity = entities[0]
            end_entity = entities[1]

            # Find paths with length 2-3 hops
            paths = self._find_multi_hop_paths(start_entity['id'], end_entity['id'], max_hops=3)

            results = []
            for path in paths[:top_k]:
                content = f"Multi-hop path: {' -> '.join([p['name'] for p in path['nodes']])}"
                content += f"\nRelationships: {' -> '.join([r['type'] for r in path['relationships']])}"

                document = {
                    'id': f"multihop_{path['id']}",
                    'content': content,
                    'type': 'multi_hop',
                    'path': path
                }

                results.append((document, 0.85))

            return results

        # Fallback to entity-focused retrieval
        return self._retrieve_entity_focused(query, top_k, filters)

    def _retrieve_centrality_based(self, query: str, top_k: int,
                                 filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve based on graph centrality measures.

        Args:
            query (str): Centrality query
            top_k (int): Number of results
            filters (Optional[Dict[str, Any]]): Filters

        Returns:
            List[Tuple[Dict[str, Any], float]]: Retrieved results
        """
        # Calculate centrality for entities related to the query
        related_entities = self.graph.search_by_text(query, limit=10)

        centrality_scores = {}
        for entity in related_entities:
            score = self._calculate_centrality(entity['id'])
            centrality_scores[entity['id']] = score

        # Sort by centrality
        sorted_entities = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for entity_id, centrality in sorted_entities[:top_k]:
            entity = next(e for e in related_entities if e['id'] == entity_id)
            content = f"High centrality entity: {entity.get('name', entity['id'])}"
            content += f"\nCentrality score: {centrality:.3f}"

            document = {
                'id': f"central_{entity_id}",
                'content': content,
                'type': 'centrality',
                'centrality': centrality
            }

            results.append((document, centrality))

        return results

    def _find_multi_hop_paths(self, start_id: str, end_id: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        Find multi-hop paths between two entities.

        Args:
            start_id (str): Starting entity ID
            end_id (str): Ending entity ID
            max_hops (int): Maximum path length

        Returns:
            List[Dict[str, Any]]: Found paths
        """
        # This would use Cypher queries for path finding
        # For now, return mock paths
        return [{
            'id': f"path_{start_id}_{end_id}",
            'nodes': [
                {'id': start_id, 'name': 'Start Entity'},
                {'id': 'intermediate', 'name': 'Intermediate Entity'},
                {'id': end_id, 'name': 'End Entity'}
            ],
            'relationships': [
                {'type': 'RELATED_TO'},
                {'type': 'CONNECTED_TO'}
            ]
        }]

    def _calculate_centrality(self, entity_id: str) -> float:
        """
        Calculate centrality score for an entity.

        Args:
            entity_id (str): Entity ID

        Returns:
            float: Centrality score
        """
        # Simple degree centrality
        related = self.graph.find_related_entities(entity_id, limit=50)
        return len(related) / 50.0  # Normalize

    def _retrieve_with_cypher(self, query: str, top_k: int,
                             filters: Optional[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Execute a Cypher query directly.

        Args:
            query (str): Cypher query string
            top_k (int): Number of results (applied to query results)
            filters (Optional[Dict[str, Any]]): Not used for Cypher queries

        Returns:
            List[Tuple[Dict[str, Any], float]]: Query results
        """
        try:
            results = self.query_processor.execute_cypher_query(query)

            # Convert results to document format
            documents = []
            for i, result in enumerate(results[:top_k]):
                content = "\n".join([f"{k}: {v}" for k, v in result.items()])

                document = {
                    'id': f"cypher_result_{i}",
                    'content': content,
                    'type': 'cypher_result',
                    'cypher_data': result
                }

                documents.append((document, 0.95))  # High confidence for direct queries

            return documents

        except Exception as e:
            logger.error(f"Error executing Cypher query: {str(e)}")
            # Return error as document
            error_doc = {
                'id': 'cypher_error',
                'content': f"Cypher query error: {str(e)}",
                'type': 'error'
            }
            return [(error_doc, 0.0)]

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None) -> None:
        """
        Add documents to the graph retriever.

        Note: Graph retriever typically works with pre-built graphs rather than
        adding individual documents. This method is for compatibility.
        """
        logger.warning("GraphRetriever does not support direct document addition. Use GraphBuilder instead.")

    def remove_documents(self, document_ids: List[str]) -> None:
        """
        Remove documents from the graph retriever.

        Note: This would require graph database operations to remove nodes and relationships.
        """
        logger.warning("Document removal from graph retriever not implemented.")

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about retrieval operations."""
        graph_stats = self.graph.get_graph_stats()
        return {
            'graph_stats': graph_stats,
            'available_strategies': list(self.strategies.keys()),
            'retrieval_config': self.retrieval_config
        }

    def __repr__(self) -> str:
        """String representation of the graph retriever."""
        return f"GraphRetriever(strategies={list(self.strategies.keys())})"