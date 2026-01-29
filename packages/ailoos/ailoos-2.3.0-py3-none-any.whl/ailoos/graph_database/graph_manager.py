"""
Graph Manager Module
Main manager for graph database operations.
"""

from typing import Dict, List, Any, Optional, Union
from .neo4j_integration import Neo4jIntegration
import logging

logger = logging.getLogger(__name__)


class GraphManager:
    """
    Main graph database manager that orchestrates all graph operations.
    """

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize the graph manager.

        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
            database: Database name
        """
        self.neo4j = Neo4jIntegration(uri, user, password, database)
        self._initialized = True
        logger.info("GraphManager initialized successfully")

    def close(self) -> None:
        """Close all connections and cleanup resources."""
        if hasattr(self, 'neo4j') and self.neo4j:
            self.neo4j.close()
        self._initialized = False
        logger.info("GraphManager closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_node(self, labels: Union[str, List[str]], properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new node in the graph.

        Args:
            labels: Node labels
            properties: Node properties

        Returns:
            Created node data
        """
        return self.neo4j.create_node(labels, properties)

    def create_relationship(self, start_node_id: int, end_node_id: int,
                          relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            relationship_type: Relationship type
            properties: Relationship properties

        Returns:
            Created relationship data
        """
        return self.neo4j.create_relationship(start_node_id, end_node_id, relationship_type, properties)

    def find_nodes(self, labels: Optional[Union[str, List[str]]] = None,
                  properties: Optional[Dict[str, Any]] = None,
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find nodes matching specified criteria.

        Args:
            labels: Node labels to match
            properties: Properties to match
            limit: Maximum number of results

        Returns:
            List of matching nodes
        """
        return self.neo4j.find_nodes(labels, properties, limit)

    def find_relationships(self, relationship_type: Optional[str] = None,
                          properties: Optional[Dict[str, Any]] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find relationships matching specified criteria.

        Args:
            relationship_type: Relationship type to match
            properties: Properties to match
            limit: Maximum number of results

        Returns:
            List of matching relationships
        """
        return self.neo4j.find_relationships(relationship_type, properties, limit)

    def delete_node(self, node_id: int) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Node ID to delete

        Returns:
            True if deletion was successful
        """
        return self.neo4j.delete_node(node_id)

    def delete_relationship(self, relationship_id: int) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: Relationship ID to delete

        Returns:
            True if deletion was successful
        """
        return self.neo4j.delete_relationship(relationship_id)

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results
        """
        return self.neo4j.execute_query(query, parameters)

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about the graph.

        Returns:
            Dictionary with graph statistics
        """
        stats = {
            'node_count': self.neo4j.get_node_count(),
            'relationship_count': self.neo4j.get_relationship_count(),
        }

        # Get node counts by label
        label_counts = self.execute_query("""
        CALL db.labels() YIELD label
        CALL {
            WITH label
            MATCH (n:`label`)
            RETURN count(n) as count
        }
        RETURN label, count
        """)

        stats['nodes_by_label'] = {record['label']: record['count'] for record in label_counts}

        # Get relationship counts by type
        rel_counts = self.execute_query("""
        CALL db.relationshipTypes() YIELD relationshipType
        CALL {
            WITH relationshipType
            MATCH ()-[r:`relationshipType`]->()
            RETURN count(r) as count
        }
        RETURN relationshipType, count
        """)

        stats['relationships_by_type'] = {record['relationshipType']: record['count'] for record in rel_counts}

        return stats

    def clear_database(self) -> None:
        """Clear all data from the database."""
        self.neo4j.clear_database()

    def batch_create_nodes(self, nodes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple nodes in batch.

        Args:
            nodes_data: List of node data dictionaries with 'labels' and 'properties' keys

        Returns:
            List of created nodes
        """
        created_nodes = []
        for node_data in nodes_data:
            labels = node_data.get('labels', [])
            properties = node_data.get('properties', {})
            node = self.create_node(labels, properties)
            created_nodes.append(node)
        return created_nodes

    def batch_create_relationships(self, relationships_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple relationships in batch.

        Args:
            relationships_data: List of relationship data dictionaries

        Returns:
            List of created relationships
        """
        created_relationships = []
        for rel_data in relationships_data:
            start_id = rel_data['start_node_id']
            end_id = rel_data['end_node_id']
            rel_type = rel_data['type']
            properties = rel_data.get('properties', {})
            rel = self.create_relationship(start_id, end_id, rel_type, properties)
            created_relationships.append(rel)
        return created_relationships

    def find_path(self, start_node_id: int, end_node_id: int,
                 relationship_types: Optional[List[str]] = None,
                 max_depth: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Find shortest path between two nodes.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            relationship_types: Allowed relationship types
            max_depth: Maximum path depth

        Returns:
            Path as list of nodes and relationships, or None if no path found
        """
        types_filter = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            types_filter = f"[:{types_str}*1..{max_depth}]"

        query = f"""
        MATCH path = shortestPath(
            (start)-{types_filter}->(end)
        )
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN path
        """

        result = self.execute_query(query, {"start_id": start_node_id, "end_id": end_node_id})
        if result and result[0]['path']:
            # Parse path into nodes and relationships
            path = result[0]['path']
            return self._parse_path(path)
        return None

    def _parse_path(self, path: Any) -> List[Dict[str, Any]]:
        """
        Parse Neo4j path object into list of nodes and relationships.

        Args:
            path: Neo4j path object

        Returns:
            List containing nodes and relationships in order
        """
        # This is a simplified parsing - in real implementation would need to handle Neo4j path structure
        return []  # Placeholder

    def get_neighbors(self, node_id: int, relationship_types: Optional[List[str]] = None,
                     direction: str = "both", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get neighboring nodes of a given node.

        Args:
            node_id: Central node ID
            relationship_types: Filter by relationship types
            direction: Direction ('outgoing', 'incoming', 'both')
            limit: Maximum number of neighbors

        Returns:
            List of neighboring nodes
        """
        direction_map = {
            'outgoing': '->',
            'incoming': '<-',
            'both': '-'
        }

        arrow = direction_map.get(direction, '-')
        types_filter = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            types_filter = f":{types_str}"

        limit_clause = f" LIMIT {limit}" if limit else ""

        query = f"""
        MATCH (n){arrow}(neighbor)
        WHERE id(n) = $node_id
        RETURN neighbor{limit_clause}
        """

        result = self.execute_query(query, {"node_id": node_id})
        return [record['neighbor'] for record in result]