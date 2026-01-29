"""
Neo4j Knowledge Graph Implementation

This module provides integration with Neo4j graph database for
knowledge representation and relationship-based queries in RAG systems.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jGraph:
    """
    Neo4j graph database integration for knowledge representation.

    This class provides methods to interact with a Neo4j database for
    storing and querying knowledge graphs in RAG applications.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Neo4j graph connection.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - uri: Neo4j connection URI
                - user: Database username
                - password: Database password
                - database: Database name (optional)
        """
        self.uri = config.get('uri', 'bolt://localhost:7687')
        self.user = config.get('user', 'neo4j')
        self.password = config.get('password')
        self.database = config.get('database', 'neo4j')

        # Initialize driver
        self.driver = None
        self._connect()

    def _connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    def add_entity(self, entity_id: str, labels: List[str], properties: Dict[str, Any]) -> None:
        """
        Add an entity (node) to the graph.

        Args:
            entity_id (str): Unique identifier for the entity
            labels (List[str]): Labels for the node
            properties (Dict[str, Any]): Node properties
        """
        try:
            labels_str = ':'.join(labels)
            props_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])

            query = f"""
            MERGE (n:{labels_str} {{id: $entity_id}})
            SET n += {{{props_str}}}
            """

            with self.driver.session(database=self.database) as session:
                session.run(query, entity_id=entity_id, **properties)

            logger.debug(f"Added entity {entity_id} to graph")

        except Exception as e:
            logger.error(f"Error adding entity to graph: {str(e)}")
            raise

    def add_relationship(self, from_id: str, to_id: str, relationship_type: str,
                        properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a relationship between entities.

        Args:
            from_id (str): ID of the source entity
            to_id (str): ID of the target entity
            relationship_type (str): Type of relationship
            properties (Optional[Dict[str, Any]]): Relationship properties
        """
        try:
            props = properties or {}
            props_str = ', '.join([f"{k}: ${k}" for k in props.keys()]) if props else ''

            query = f"""
            MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
            MERGE (a)-[r:{relationship_type}]->(b)
            """
            if props_str:
                query += f" SET r += {{{props_str}}}"

            with self.driver.session(database=self.database) as session:
                session.run(query, from_id=from_id, to_id=to_id, **props)

            logger.debug(f"Added relationship {relationship_type} between {from_id} and {to_id}")

        except Exception as e:
            logger.error(f"Error adding relationship: {str(e)}")
            raise

    def query_entities(self, entity_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query entities from the graph.

        Args:
            entity_type (Optional[str]): Type of entities to query
            limit (int): Maximum number of results

        Returns:
            List[Dict[str, Any]]: List of entity dictionaries
        """
        try:
            if entity_type:
                query = f"MATCH (n:{entity_type}) RETURN n LIMIT {limit}"
            else:
                query = f"MATCH (n) RETURN n LIMIT {limit}"

            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                return [dict(record['n']) for record in result]

        except Exception as e:
            logger.error(f"Error querying entities: {str(e)}")
            raise

    def find_related_entities(self, entity_id: str, relationship_type: Optional[str] = None,
                            direction: str = 'BOTH', depth: int = 2) -> List[Dict[str, Any]]:
        """
        Find entities related to a given entity.

        Args:
            entity_id (str): ID of the central entity
            relationship_type (Optional[str]): Type of relationship to follow
            direction (str): Direction of relationships ('OUTGOING', 'INCOMING', 'BOTH')
            depth (int): Maximum path depth

        Returns:
            List[Dict[str, Any]]: List of related entities
        """
        try:
            rel_pattern = f"-[r:{relationship_type}]->" if relationship_type else "-[r]->"
            if direction == 'INCOMING':
                rel_pattern = f"<-{rel_pattern[1:]}"
            elif direction == 'BOTH':
                rel_pattern = f"-[r:{relationship_type}]-" if relationship_type else "-[r]-"

            query = f"""
            MATCH (start {{id: $entity_id}}){rel_pattern}(end)
            WHERE start <> end
            RETURN DISTINCT end, r
            LIMIT 50
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, entity_id=entity_id)
                return [{'entity': dict(record['end']), 'relationship': dict(record['r'])} for record in result]

        except Exception as e:
            logger.error(f"Error finding related entities: {str(e)}")
            raise

    def search_by_text(self, search_text: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search entities by text content.

        Args:
            search_text (str): Text to search for
            entity_type (Optional[str]): Type of entities to search

        Returns:
            List[Dict[str, Any]]: Matching entities
        """
        try:
            label_filter = f":{entity_type}" if entity_type else ""
            query = f"""
            MATCH (n{label_filter})
            WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $search_text)
            RETURN n
            LIMIT 20
            """

            with self.driver.session(database=self.database) as session:
                result = session.run(query, search_text=search_text)
                return [dict(record['n']) for record in result]

        except Exception as e:
            logger.error(f"Error searching by text: {str(e)}")
            raise

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph."""
        try:
            with self.driver.session(database=self.database) as session:
                # Get node count
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()['node_count']

                # Get relationship count
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = rel_result.single()['rel_count']

                # Get node labels
                labels_result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                labels = labels_result.single()['labels']

                # Get relationship types
                types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
                types = types_result.single()['types']

                return {
                    'node_count': node_count,
                    'relationship_count': rel_count,
                    'node_labels': labels,
                    'relationship_types': types
                }
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            return {}

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()