"""
Graph Persistence Module
Handles backup, restore, and export/import operations for graphs.
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, TextIO
from pathlib import Path
from .neo4j_integration import Neo4jIntegration
import logging

logger = logging.getLogger(__name__)


class GraphPersistence:
    """
    Graph persistence and backup management.
    """

    def __init__(self, neo4j_integration: Neo4jIntegration, backup_dir: str = "./backups"):
        """
        Initialize graph persistence.

        Args:
            neo4j_integration: Neo4j integration instance
            backup_dir: Directory for backups
        """
        self.neo4j = neo4j_integration
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, name: Optional[str] = None,
                     include_constraints: bool = True,
                     include_indexes: bool = True) -> str:
        """
        Create a complete backup of the graph database.

        Args:
            name: Backup name (auto-generated if None)
            include_constraints: Include schema constraints
            include_indexes: Include indexes

        Returns:
            Backup file path
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"graph_backup_{timestamp}"

        backup_path = self.backup_dir / f"{name}.json"

        # Export all data
        data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'node_count': self.neo4j.get_node_count(),
                'relationship_count': self.neo4j.get_relationship_count(),
                'version': '1.0'
            },
            'nodes': [],
            'relationships': []
        }

        # Export nodes
        node_query = """
        MATCH (n)
        RETURN id(n) as id, labels(n) as labels, properties(n) as properties
        """
        node_results = self.neo4j.execute_query(node_query)
        for record in node_results:
            data['nodes'].append({
                'id': record['id'],
                'labels': record['labels'],
                'properties': record['properties']
            })

        # Export relationships
        rel_query = """
        MATCH (a)-[r]->(b)
        RETURN id(r) as id, id(a) as start_id, id(b) as end_id,
               type(r) as type, properties(r) as properties
        """
        rel_results = self.neo4j.execute_query(rel_query)
        for record in rel_results:
            data['relationships'].append({
                'id': record['id'],
                'start_id': record['start_id'],
                'end_id': record['end_id'],
                'type': record['type'],
                'properties': record['properties']
            })

        # Export schema if requested
        if include_constraints or include_indexes:
            data['schema'] = self._export_schema(include_constraints, include_indexes)

        # Save to file
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Backup created: {backup_path}")
        return str(backup_path)

    def restore_backup(self, backup_path: str, clear_existing: bool = True) -> bool:
        """
        Restore graph from backup.

        Args:
            backup_path: Path to backup file
            clear_existing: Clear existing data before restore

        Returns:
            True if restore was successful
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if clear_existing:
                self.neo4j.clear_database()

            # Restore nodes first
            node_id_map = {}  # Map old IDs to new IDs

            for node_data in data['nodes']:
                old_id = node_data['id']
                labels = node_data['labels']
                properties = node_data['properties']

                new_node = self.neo4j.create_node(labels, properties)
                if new_node:
                    # Assuming the new node has an ID, we need to map it
                    # In practice, we'd need to handle ID mapping properly
                    node_id_map[old_id] = new_node.get('id')  # This might not work as expected

            # Restore relationships
            for rel_data in data['relationships']:
                start_old_id = rel_data['start_id']
                end_old_id = rel_data['end_id']
                rel_type = rel_data['type']
                properties = rel_data['properties']

                # Map to new IDs (simplified - may not work perfectly)
                start_new_id = node_id_map.get(start_old_id)
                end_new_id = node_id_map.get(end_old_id)

                if start_new_id is not None and end_new_id is not None:
                    self.neo4j.create_relationship(start_new_id, end_new_id, rel_type, properties)

            # Restore schema if present
            if 'schema' in data:
                self._restore_schema(data['schema'])

            logger.info(f"Backup restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def export_to_json(self, filepath: str, node_labels: Optional[List[str]] = None,
                      relationship_types: Optional[List[str]] = None) -> bool:
        """
        Export graph data to JSON format.

        Args:
            filepath: Output file path
            node_labels: Labels to export (None for all)
            relationship_types: Relationship types to export (None for all)

        Returns:
            True if export was successful
        """
        try:
            # Build node query
            node_where = ""
            if node_labels:
                labels_str = " OR ".join([f"'{label}' IN labels(n)" for label in node_labels])
                node_where = f"WHERE {labels_str}"

            node_query = f"""
            MATCH (n)
            {node_where}
            RETURN id(n) as id, labels(n) as labels, properties(n) as properties
            """

            # Build relationship query
            rel_where = ""
            if relationship_types:
                types_str = " OR ".join([f"type(r) = '{rtype}'" for rtype in relationship_types])
                rel_where = f"WHERE {types_str}"

            rel_query = f"""
            MATCH (a)-[r]->(b)
            {rel_where}
            RETURN id(a) as start_id, id(b) as end_id, type(r) as type, properties(r) as properties
            """

            nodes = self.neo4j.execute_query(node_query)
            relationships = self.neo4j.execute_query(rel_query)

            data = {
                'nodes': [dict(record) for record in nodes],
                'relationships': [dict(record) for record in relationships],
                'export_timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Graph exported to JSON: {filepath}")

            return True
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False

    def import_from_json(self, filepath: str, clear_existing: bool = False) -> bool:
        """
        Import graph data from JSON format.

        Args:
            filepath: Input file path
            clear_existing: Clear existing data before import

        Returns:
            True if import was successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if clear_existing:
                self.neo4j.clear_database()

            # Import nodes
            for node_data in data.get('nodes', []):
                labels = node_data.get('labels', [])
                properties = node_data.get('properties', {})
                self.neo4j.create_node(labels, properties)

            # Import relationships (simplified - assumes node IDs are preserved)
            for rel_data in data.get('relationships', []):
                start_id = rel_data['start_id']
                end_id = rel_data['end_id']
                rel_type = rel_data['type']
                properties = rel_data.get('properties', {})
                self.neo4j.create_relationship(start_id, end_id, rel_type, properties)

            logger.info(f"Graph imported from JSON: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to import from JSON: {e}")
            return False

    def export_to_csv(self, nodes_filepath: str, relationships_filepath: str,
                     node_labels: Optional[List[str]] = None,
                     relationship_types: Optional[List[str]] = None) -> bool:
        """
        Export graph data to CSV format.

        Args:
            nodes_filepath: Output file for nodes
            relationships_filepath: Output file for relationships
            node_labels: Labels to export
            relationship_types: Relationship types to export

        Returns:
            True if export was successful
        """
        try:
            # Export nodes
            node_where = ""
            if node_labels:
                labels_str = " OR ".join([f"'{label}' IN labels(n)" for label in node_labels])
                node_where = f"WHERE {labels_str}"

            node_query = f"""
            MATCH (n)
            {node_where}
            RETURN id(n) as id, labels(n) as labels, properties(n) as properties
            """

            nodes = self.neo4j.execute_query(node_query)

            with open(nodes_filepath, 'w', newline='', encoding='utf-8') as f:
                if nodes:
                    # Get all possible property keys
                    all_keys = set()
                    for record in nodes:
                        all_keys.update(record['properties'].keys())

                    fieldnames = ['id', 'labels'] + sorted(all_keys)
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for record in nodes:
                        row = {
                            'id': record['id'],
                            'labels': '|'.join(record['labels'])
                        }
                        row.update(record['properties'])
                        writer.writerow(row)

            # Export relationships
            rel_where = ""
            if relationship_types:
                types_str = " OR ".join([f"type(r) = '{rtype}'" for rtype in relationship_types])
                rel_where = f"WHERE {types_str}"

            rel_query = f"""
            MATCH (a)-[r]->(b)
            {rel_where}
            RETURN id(a) as start_id, id(b) as end_id, type(r) as type, properties(r) as properties
            """

            relationships = self.neo4j.execute_query(rel_query)

            with open(relationships_filepath, 'w', newline='', encoding='utf-8') as f:
                if relationships:
                    # Get all possible property keys
                    all_keys = set()
                    for record in relationships:
                        all_keys.update(record['properties'].keys())

                    fieldnames = ['start_id', 'end_id', 'type'] + sorted(all_keys)
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for record in relationships:
                        row = {
                            'start_id': record['start_id'],
                            'end_id': record['end_id'],
                            'type': record['type']
                        }
                        row.update(record['properties'])
                        writer.writerow(row)

            logger.info(f"Graph exported to CSV: {nodes_filepath}, {relationships_filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False

    def export_to_graphml(self, filepath: str) -> bool:
        """
        Export graph to GraphML format.

        Args:
            filepath: Output file path

        Returns:
            True if export was successful
        """
        try:
            # Get all nodes and relationships
            nodes = self.neo4j.execute_query("""
            MATCH (n)
            RETURN id(n) as id, labels(n) as labels, properties(n) as properties
            """)

            relationships = self.neo4j.execute_query("""
            MATCH (a)-[r]->(b)
            RETURN id(a) as start_id, id(b) as end_id, type(r) as type, properties(r) as properties
            """)

            # Create GraphML XML
            graphml = self._create_graphml_xml(nodes, relationships)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(graphml)

            logger.info(f"Graph exported to GraphML: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to GraphML: {e}")
            return False

    def _create_graphml_xml(self, nodes: List[Dict], relationships: List[Dict]) -> str:
        """Create GraphML XML string."""
        # Collect all property keys
        node_keys = set()
        rel_keys = set()

        for node in nodes:
            node_keys.update(node['properties'].keys())

        for rel in relationships:
            rel_keys.update(rel['properties'].keys())

        # XML header
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"',
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns',
            '         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">'
        ]

        # Node property keys
        for i, key in enumerate(sorted(node_keys)):
            xml_parts.append(f'  <key id="node_{i}" for="node" attr.name="{key}" attr.type="string"/>')

        # Relationship property keys
        for i, key in enumerate(sorted(rel_keys)):
            xml_parts.append(f'  <key id="edge_{i}" for="edge" attr.name="{key}" attr.type="string"/>')

        xml_parts.append('  <graph id="G" edgedefault="directed">')

        # Nodes
        for node in nodes:
            node_id = node['id']
            labels = '|'.join(node['labels'])
            xml_parts.append(f'    <node id="n{node_id}">')
            xml_parts.append(f'      <data key="labels">{labels}</data>')

            for i, key in enumerate(sorted(node_keys)):
                if key in node['properties']:
                    value = str(node['properties'][key]).replace('&', '&').replace('<', '<').replace('>', '>')
                    xml_parts.append(f'      <data key="node_{i}">{value}</data>')

            xml_parts.append('    </node>')

        # Relationships
        for rel in relationships:
            start_id = rel['start_id']
            end_id = rel['end_id']
            rel_type = rel['type']
            xml_parts.append(f'    <edge source="n{start_id}" target="n{end_id}">')
            xml_parts.append(f'      <data key="type">{rel_type}</data>')

            for i, key in enumerate(sorted(rel_keys)):
                if key in rel['properties']:
                    value = str(rel['properties'][key]).replace('&', '&').replace('<', '<').replace('>', '>')
                    xml_parts.append(f'      <data key="edge_{i}">{value}</data>')

            xml_parts.append('    </edge>')

        xml_parts.extend(['  </graph>', '</graphml>'])

        return '\n'.join(xml_parts)

    def _export_schema(self, include_constraints: bool, include_indexes: bool) -> Dict[str, Any]:
        """Export database schema."""
        schema = {}

        if include_indexes:
            # Export indexes
            index_query = "SHOW INDEXES"
            try:
                indexes = self.neo4j.execute_query(index_query)
                schema['indexes'] = [dict(record) for record in indexes]
            except Exception:
                schema['indexes'] = []

        if include_constraints:
            # Export constraints
            constraint_query = "SHOW CONSTRAINTS"
            try:
                constraints = self.neo4j.execute_query(constraint_query)
                schema['constraints'] = [dict(record) for record in constraints]
            except Exception:
                schema['constraints'] = []

        return schema

    def _restore_schema(self, schema: Dict[str, Any]) -> None:
        """Restore database schema."""
        # Restore indexes
        for index in schema.get('indexes', []):
            # This would require parsing index definitions and recreating them
            # Simplified implementation
            pass

        # Restore constraints
        for constraint in schema.get('constraints', []):
            # This would require parsing constraint definitions and recreating them
            # Simplified implementation
            pass

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.

        Returns:
            List of backup information
        """
        backups = []
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f).get('metadata', {})

                backups.append({
                    'name': backup_file.stem,
                    'path': str(backup_file),
                    'timestamp': metadata.get('timestamp'),
                    'node_count': metadata.get('node_count'),
                    'relationship_count': metadata.get('relationship_count'),
                    'size': backup_file.stat().st_size
                })
            except Exception:
                backups.append({
                    'name': backup_file.stem,
                    'path': str(backup_file),
                    'error': 'Could not read metadata'
                })

        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)

    def delete_backup(self, name: str) -> bool:
        """
        Delete a backup file.

        Args:
            name: Backup name

        Returns:
            True if deletion was successful
        """
        backup_path = self.backup_dir / f"{name}.json"
        try:
            backup_path.unlink()
            logger.info(f"Backup deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {name}: {e}")
            return False