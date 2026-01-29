"""
Cypher Query Processor for Knowledge Graph

This module provides advanced query processing capabilities using Cypher
for complex graph traversals and relationship queries.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re

from .neo4j_graph import Neo4jGraph

logger = logging.getLogger(__name__)


class CypherQueryProcessor:
    """
    Advanced query processor using Cypher for complex graph operations.

    This class provides methods to generate and execute Cypher queries
    for various graph retrieval and analysis tasks.
    """

    def __init__(self, graph: Neo4jGraph):
        """
        Initialize the query processor.

        Args:
            graph (Neo4jGraph): Neo4j graph instance
        """
        self.graph = graph

    def execute_cypher_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw Cypher query.

        Args:
            query (str): Cypher query string
            parameters (Optional[Dict[str, Any]]): Query parameters

        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            with self.graph.driver.session(database=self.graph.database) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error executing Cypher query: {str(e)}")
            raise

    def find_shortest_path(self, start_entity: str, end_entity: str,
                          max_length: int = 10) -> Optional[Dict[str, Any]]:
        """
        Find the shortest path between two entities.

        Args:
            start_entity (str): Starting entity ID
            end_entity (str): Ending entity ID
            max_length (int): Maximum path length

        Returns:
            Optional[Dict[str, Any]]: Path information or None
        """
        query = f"""
        MATCH path = shortestPath(
            (start {{id: $start_id}})-[*..{max_length}]-(end {{id: $end_id}})
        )
        WHERE start <> end
        RETURN path,
               length(path) as path_length,
               [node in nodes(path) | node.id] as node_ids,
               [rel in relationships(path) | rel.type] as relationship_types
        """

        try:
            results = self.execute_cypher_query(query, {
                'start_id': start_entity,
                'end_id': end_entity
            })

            if results:
                result = results[0]
                return {
                    'path_length': result['path_length'],
                    'node_ids': result['node_ids'],
                    'relationship_types': result['relationship_types'],
                    'nodes': [dict(node) for node in result['path'].nodes],
                    'relationships': [dict(rel) for rel in result['path'].relationships]
                }
        except Exception as e:
            logger.error(f"Error finding shortest path: {str(e)}")

        return None

    def find_all_paths(self, start_entity: str, end_entity: str,
                      max_length: int = 5, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find all paths between two entities up to a maximum length.

        Args:
            start_entity (str): Starting entity ID
            end_entity (str): Ending entity ID
            max_length (int): Maximum path length
            max_results (int): Maximum number of paths to return

        Returns:
            List[Dict[str, Any]]: List of paths
        """
        query = f"""
        MATCH path = (start {{id: $start_id}})-[*..{max_length}]-(end {{id: $end_id}})
        WHERE start <> end
        RETURN path,
               length(path) as path_length,
               [node in nodes(path) | node.id] as node_ids,
               [rel in relationships(path) | rel.type] as relationship_types
        ORDER BY length(path)
        LIMIT {max_results}
        """

        try:
            results = self.execute_cypher_query(query, {
                'start_id': start_entity,
                'end_id': end_entity
            })

            paths = []
            for result in results:
                paths.append({
                    'path_length': result['path_length'],
                    'node_ids': result['node_ids'],
                    'relationship_types': result['relationship_types'],
                    'nodes': [dict(node) for node in result['path'].nodes],
                    'relationships': [dict(rel) for rel in result['path'].relationships]
                })

            return paths
        except Exception as e:
            logger.error(f"Error finding all paths: {str(e)}")
            return []

    def find_related_entities_with_depth(self, entity_id: str, depth: int = 2,
                                       relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Find entities related to the given entity with specified depth.

        Args:
            entity_id (str): Central entity ID
            depth (int): Traversal depth
            relationship_types (Optional[List[str]]): Types of relationships to follow

        Returns:
            Dict[str, Any]: Related entities organized by depth
        """
        rel_filter = ""
        if relationship_types:
            rel_types_str = "|".join(f"`{rt}`" for rt in relationship_types)
            rel_filter = f"WHERE type(r) IN [{rel_types_str}]"

        query = f"""
        MATCH path = (start {{id: $entity_id}})-[r*..{depth}]-(end)
        {rel_filter}
        WHERE start <> end
        RETURN DISTINCT end,
               min(length(path)) as min_distance,
               collect(DISTINCT type(r)) as relationship_types
        ORDER BY min_distance, end.id
        """

        try:
            results = self.execute_cypher_query(query, {'entity_id': entity_id})

            entities_by_depth = {}
            for result in results:
                distance = result['min_distance']
                if distance not in entities_by_depth:
                    entities_by_depth[distance] = []

                entities_by_depth[distance].append({
                    'entity': dict(result['end']),
                    'relationship_types': result['relationship_types']
                })

            return entities_by_depth
        except Exception as e:
            logger.error(f"Error finding related entities with depth: {str(e)}")
            return {}

    def calculate_centrality_measures(self, entity_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """
        Calculate various centrality measures for entities.

        Args:
            entity_ids (Optional[List[str]]): Specific entities to analyze, or all if None

        Returns:
            Dict[str, Dict[str, float]]: Centrality measures by entity
        """
        # Degree centrality
        degree_query = """
        MATCH (n)
        WHERE $entity_ids IS NULL OR n.id IN $entity_ids
        OPTIONAL MATCH (n)-[r]-()
        RETURN n.id as entity_id, count(r) as degree
        """

        # Betweenness centrality (simplified)
        betweenness_query = """
        MATCH (n)
        WHERE $entity_ids IS NULL OR n.id IN $entity_ids
        MATCH p = shortestPath((a)-[*]-(b))
        WHERE a <> b AND n IN nodes(p) AND a <> n AND b <> n
        RETURN n.id as entity_id, count(p) as betweenness
        """

        try:
            centrality = {}

            # Degree centrality
            degree_results = self.execute_cypher_query(degree_query, {'entity_ids': entity_ids})
            for result in degree_results:
                entity_id = result['entity_id']
                centrality[entity_id] = {'degree': result['degree'], 'betweenness': 0.0}

            # Betweenness centrality
            betweenness_results = self.execute_cypher_query(betweenness_query, {'entity_ids': entity_ids})
            for result in betweenness_results:
                entity_id = result['entity_id']
                if entity_id in centrality:
                    centrality[entity_id]['betweenness'] = result['betweenness']

            return centrality
        except Exception as e:
            logger.error(f"Error calculating centrality measures: {str(e)}")
            return {}

    def find_communities(self, algorithm: str = 'louvain') -> Dict[str, List[str]]:
        """
        Detect communities using graph algorithms.

        Args:
            algorithm (str): Community detection algorithm ('louvain', 'label_propagation')

        Returns:
            Dict[str, List[str]]: Community assignments
        """
        if algorithm == 'louvain':
            query = """
            CALL gds.louvain.stream({
                nodeProjection: '*',
                relationshipProjection: '*'
            })
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).id as entity_id, communityId
            ORDER BY communityId, entity_id
            """
        elif algorithm == 'label_propagation':
            query = """
            CALL gds.labelPropagation.stream({
                nodeProjection: '*',
                relationshipProjection: '*'
            })
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).id as entity_id, communityId
            ORDER BY communityId, entity_id
            """
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        try:
            results = self.execute_cypher_query(query)

            communities = {}
            for result in results:
                community_id = f"community_{result['communityId']}"
                entity_id = result['entity_id']

                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(entity_id)

            return communities
        except Exception as e:
            logger.error(f"Error detecting communities with {algorithm}: {str(e)}")
            # Fallback to simple connected components
            return self._simple_connected_components()

    def _simple_connected_components(self) -> Dict[str, List[str]]:
        """Simple connected components as fallback."""
        query = """
        MATCH (n)
        MATCH (n)-[r*]-(m)
        WITH n, collect(DISTINCT m.id) + n.id as component
        RETURN DISTINCT component
        """

        try:
            results = self.execute_cypher_query(query)
            communities = {}
            for i, result in enumerate(results):
                community_id = f"component_{i}"
                communities[community_id] = result['component']
            return communities
        except Exception as e:
            logger.error(f"Error in simple connected components: {str(e)}")
            return {}

    def semantic_search(self, query_embedding: List[float], top_k: int = 10,
                       entity_types: Optional[List[str]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform semantic search using vector similarity.

        Args:
            query_embedding (List[float]): Query embedding vector
            top_k (int): Number of results
            entity_types (Optional[List[str]]): Entity types to search

        Returns:
            List[Tuple[Dict[str, Any], float]]: Similar entities with scores
        """
        # This would require vector similarity functions in Neo4j
        # For now, return mock results
        type_filter = ""
        if entity_types:
            type_filter = "WHERE n.type IN $entity_types"

        query = f"""
        MATCH (n)
        {type_filter}
        RETURN n, rand() as similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """

        try:
            results = self.execute_cypher_query(query, {
                'entity_types': entity_types,
                'top_k': top_k
            })

            return [(dict(result['n']), result['similarity']) for result in results]
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    def generate_subgraph(self, center_entity: str, radius: int = 2) -> Dict[str, Any]:
        """
        Generate a subgraph around a central entity.

        Args:
            center_entity (str): Central entity ID
            radius (int): Subgraph radius

        Returns:
            Dict[str, Any]: Subgraph data
        """
        query = f"""
        MATCH path = (center {{id: $center_id}})-[*..{radius}]-(connected)
        WHERE center <> connected
        RETURN DISTINCT
               center as center_node,
               collect(DISTINCT connected) as connected_nodes,
               collect(DISTINCT relationships(path)) as all_relationships
        """

        try:
            results = self.execute_cypher_query(query, {'center_id': center_entity})

            if results:
                result = results[0]
                return {
                    'center': dict(result['center_node']),
                    'nodes': [dict(node) for node in result['connected_nodes']],
                    'relationships': [dict(rel) for rel_list in result['all_relationships']
                                    for rel in rel_list]
                }
        except Exception as e:
            logger.error(f"Error generating subgraph: {str(e)}")

        return {'center': None, 'nodes': [], 'relationships': []}