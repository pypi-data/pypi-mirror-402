"""
Neo4j Integration Module
Provides complete integration with Neo4j graph database.
"""

from neo4j import GraphDatabase, Driver
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Neo4jIntegration:
    """
    Complete Neo4j integration class for graph database operations.
    """

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
            database: Database name (default: neo4j)
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                database=self.database
            )
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        if not self._driver:
            raise ConnectionError("No active database connection")
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a write Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.session() as session:
            result = session.write_transaction(lambda tx: tx.run(query, parameters or {}).data())
            return result

    def create_node(self, labels: Union[str, List[str]], properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new node.

        Args:
            labels: Node labels
            properties: Node properties

        Returns:
            Created node data
        """
        if isinstance(labels, str):
            labels = [labels]

        labels_str = ":".join(labels)
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{labels_str} {{{props_str}}}) RETURN n"

        result = self.execute_write_query(query, properties)
        return result[0]['n'] if result else {}

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
        properties = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        props_part = f" {{{props_str}}}" if props_str else ""

        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $start_id AND id(b) = $end_id
        CREATE (a)-[r:{relationship_type}{props_part}]->(b)
        RETURN r
        """

        params = {"start_id": start_node_id, "end_id": end_node_id, **properties}
        result = self.execute_write_query(query, params)
        return result[0]['r'] if result else {}

    def find_nodes(self, labels: Optional[Union[str, List[str]]] = None,
                  properties: Optional[Dict[str, Any]] = None,
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find nodes matching criteria.

        Args:
            labels: Node labels to match
            properties: Properties to match
            limit: Maximum number of results

        Returns:
            List of matching nodes
        """
        if isinstance(labels, str):
            labels = [labels]

        labels_str = ":".join(labels) if labels else ""
        labels_part = f":{labels_str}" if labels_str else ""

        where_parts = []
        params = {}

        if properties:
            for key, value in properties.items():
                where_parts.append(f"n.{key} = ${key}")
                params[key] = value

        where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
        limit_clause = f" LIMIT {limit}" if limit else ""

        query = f"MATCH (n{labels_part}){where_clause} RETURN n{limit_clause}"

        result = self.execute_query(query, params)
        return [record['n'] for record in result]

    def find_relationships(self, relationship_type: Optional[str] = None,
                          properties: Optional[Dict[str, Any]] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find relationships matching criteria.

        Args:
            relationship_type: Relationship type to match
            properties: Properties to match
            limit: Maximum number of results

        Returns:
            List of matching relationships
        """
        type_part = f":{relationship_type}" if relationship_type else ""

        where_parts = []
        params = {}

        if properties:
            for key, value in properties.items():
                where_parts.append(f"r.{key} = ${key}")
                params[key] = value

        where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
        limit_clause = f" LIMIT {limit}" if limit else ""

        query = f"MATCH ()-[r{type_part}]->(){where_clause} RETURN r{limit_clause}"

        result = self.execute_query(query, params)
        return [record['r'] for record in result]

    def delete_node(self, node_id: int) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Node ID to delete

        Returns:
            True if deletion was successful
        """
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        DETACH DELETE n
        """

        try:
            self.execute_write_query(query, {"node_id": node_id})
            return True
        except Exception:
            return False

    def delete_relationship(self, relationship_id: int) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: Relationship ID to delete

        Returns:
            True if deletion was successful
        """
        query = """
        MATCH ()-[r]->()
        WHERE id(r) = $rel_id
        DELETE r
        """

        try:
            self.execute_write_query(query, {"rel_id": relationship_id})
            return True
        except Exception:
            return False

    def get_node_count(self, labels: Optional[Union[str, List[str]]] = None) -> int:
        """
        Get count of nodes.

        Args:
            labels: Optional labels to filter by

        Returns:
            Number of nodes
        """
        if isinstance(labels, str):
            labels = [labels]

        labels_str = ":".join(labels) if labels else ""
        labels_part = f":{labels_str}" if labels_str else ""

        query = f"MATCH (n{labels_part}) RETURN count(n) as count"

        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def get_relationship_count(self, relationship_type: Optional[str] = None) -> int:
        """
        Get count of relationships.

        Args:
            relationship_type: Optional relationship type to filter by

        Returns:
            Number of relationships
        """
        type_part = f":{relationship_type}" if relationship_type else ""

        query = f"MATCH ()-[r{type_part}]->() RETURN count(r) as count"

        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def clear_database(self) -> None:
        """Clear all data from the database."""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_write_query(query)
        logger.info("Database cleared")