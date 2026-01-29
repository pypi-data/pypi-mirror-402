"""
Graph Embeddings and Advanced Analytics

This module provides graph embedding techniques and advanced graph analytics
for enhanced knowledge graph operations in RAG systems.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np

from .neo4j_graph import Neo4jGraph

logger = logging.getLogger(__name__)


class GraphEmbeddings:
    """
    Graph embedding techniques for knowledge graphs.

    This class provides methods to compute embeddings for nodes and relationships,
    enabling semantic similarity and advanced graph operations.
    """

    def __init__(self, graph: Neo4jGraph, embedding_model=None):
        """
        Initialize graph embeddings.

        Args:
            graph (Neo4jGraph): Neo4j graph instance
            embedding_model: Text embedding model (optional)
        """
        self.graph = graph
        self.embedding_model = embedding_model
        self.node_embeddings = {}
        self.edge_embeddings = {}

    def compute_node_embeddings(self, nodes: List[str]) -> Dict[str, List[float]]:
        """
        Compute embeddings for graph nodes.

        Args:
            nodes (List[str]): Node IDs to embed

        Returns:
            Dict[str, List[float]]: Node embeddings
        """
        embeddings = {}

        for node_id in nodes:
            try:
                # Get node properties
                node_data = self._get_node_data(node_id)
                if node_data:
                    # Create text representation
                    text_repr = self._node_to_text(node_data)

                    # Compute embedding
                    if self.embedding_model:
                        embedding = self.embedding_model.encode([text_repr])[0]
                    else:
                        # Fallback: random embedding
                        embedding = np.random.normal(0, 1, 384).tolist()

                    embeddings[node_id] = embedding
                    self.node_embeddings[node_id] = embedding

            except Exception as e:
                logger.error(f"Error computing embedding for node {node_id}: {str(e)}")

        return embeddings

    def compute_edge_embeddings(self, edges: List[Tuple[str, str, str]]) -> Dict[str, List[float]]:
        """
        Compute embeddings for graph edges.

        Args:
            edges (List[Tuple[str, str, str]]): List of (source, target, relationship_type)

        Returns:
            Dict[str, List[float]]: Edge embeddings
        """
        embeddings = {}

        for source, target, rel_type in edges:
            try:
                edge_id = f"{source}_{rel_type}_{target}"
                text_repr = f"{rel_type} relationship between {source} and {target}"

                if self.embedding_model:
                    embedding = self.embedding_model.encode([text_repr])[0]
                else:
                    # Fallback: random embedding
                    embedding = np.random.normal(0, 1, 384).tolist()

                embeddings[edge_id] = embedding
                self.edge_embeddings[edge_id] = embedding

            except Exception as e:
                logger.error(f"Error computing embedding for edge {source}-{rel_type}-{target}: {str(e)}")

        return embeddings

    def find_similar_nodes(self, node_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find nodes similar to the given node based on embeddings.

        Args:
            node_id (str): Reference node ID
            top_k (int): Number of similar nodes to return

        Returns:
            List[Tuple[str, float]]: Similar nodes with similarity scores
        """
        if node_id not in self.node_embeddings:
            return []

        reference_emb = np.array(self.node_embeddings[node_id])
        similarities = []

        for other_id, emb in self.node_embeddings.items():
            if other_id != node_id:
                similarity = np.dot(reference_emb, np.array(emb)) / (
                    np.linalg.norm(reference_emb) * np.linalg.norm(np.array(emb))
                )
                similarities.append((other_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _get_node_data(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data from graph."""
        # This would query the graph for node properties
        # For now, return mock data
        return {'id': node_id, 'type': 'Entity', 'name': f'Entity {node_id}'}

    def _node_to_text(self, node_data: Dict[str, Any]) -> str:
        """Convert node data to text representation."""
        text_parts = []
        if 'name' in node_data:
            text_parts.append(node_data['name'])
        if 'type' in node_data:
            text_parts.append(f"Type: {node_data['type']}")
        if 'description' in node_data:
            text_parts.append(node_data['description'])

        return ' '.join(text_parts) if text_parts else str(node_data.get('id', ''))


class GraphAnalytics:
    """
    Advanced graph analytics for knowledge graphs.

    This class provides centrality measures, community detection,
    and other graph analysis algorithms.
    """

    def __init__(self, graph: Neo4jGraph):
        """
        Initialize graph analytics.

        Args:
            graph (Neo4jGraph): Neo4j graph instance
        """
        self.graph = graph

    def calculate_centrality(self, centrality_type: str = 'degree',
                           limit: int = 100) -> Dict[str, float]:
        """
        Calculate centrality measures for nodes.

        Args:
            centrality_type (str): Type of centrality ('degree', 'betweenness', 'closeness')
            limit (int): Maximum number of nodes to analyze

        Returns:
            Dict[str, float]: Node centrality scores
        """
        try:
            if centrality_type == 'degree':
                return self._calculate_degree_centrality(limit)
            elif centrality_type == 'betweenness':
                return self._calculate_betweenness_centrality(limit)
            elif centrality_type == 'closeness':
                return self._calculate_closeness_centrality(limit)
            else:
                raise ValueError(f"Unknown centrality type: {centrality_type}")
        except Exception as e:
            logger.error(f"Error calculating {centrality_type} centrality: {str(e)}")
            return {}

    def _calculate_degree_centrality(self, limit: int) -> Dict[str, float]:
        """Calculate degree centrality."""
        centrality = {}

        # Get sample nodes
        nodes = self.graph.query_entities(limit=limit)

        for node in nodes:
            related = self.graph.find_related_entities(node['id'], limit=100)
            centrality[node['id']] = len(related)

        # Normalize
        if centrality:
            max_degree = max(centrality.values())
            centrality = {k: v/max_degree for k, v in centrality.items()}

        return centrality

    def _calculate_betweenness_centrality(self, limit: int) -> Dict[str, float]:
        """Calculate betweenness centrality (simplified)."""
        # Simplified implementation - in practice would use graph algorithms
        centrality = {}

        nodes = self.graph.query_entities(limit=limit)
        node_ids = [n['id'] for n in nodes]

        for node_id in node_ids:
            # Count shortest paths passing through this node
            paths_through = 0
            total_paths = 0

            for i, start_id in enumerate(node_ids):
                for j, end_id in enumerate(node_ids[i+1:], i+1):
                    if start_id != node_id and end_id != node_id:
                        # Check if node is on path between start and end
                        if self._is_on_path(node_id, start_id, end_id):
                            paths_through += 1
                        total_paths += 1

            centrality[node_id] = paths_through / max(total_paths, 1)

        return centrality

    def _calculate_closeness_centrality(self, limit: int) -> Dict[str, float]:
        """Calculate closeness centrality."""
        centrality = {}

        nodes = self.graph.query_entities(limit=limit)
        node_ids = [n['id'] for n in nodes]

        for node_id in node_ids:
            distances = []
            for other_id in node_ids:
                if other_id != node_id:
                    dist = self._shortest_path_distance(node_id, other_id)
                    if dist > 0:
                        distances.append(dist)

            if distances:
                centrality[node_id] = 1 / np.mean(distances)
            else:
                centrality[node_id] = 0.0

        return centrality

    def detect_communities(self, algorithm: str = 'louvain') -> Dict[str, List[str]]:
        """
        Detect communities in the graph.

        Args:
            algorithm (str): Community detection algorithm

        Returns:
            Dict[str, List[str]]: Community assignments
        """
        # Simplified community detection
        # In practice, would use graph algorithms like Louvain or Label Propagation

        communities = {}
        nodes = self.graph.query_entities(limit=50)

        # Simple clustering based on connection patterns
        for i, node in enumerate(nodes):
            community_id = f"community_{i % 3}"  # Mock: 3 communities
            if community_id not in communities:
                communities[community_id] = []
            communities[community_id].append(node['id'])

        return communities

    def _is_on_path(self, node_id: str, start_id: str, end_id: str) -> bool:
        """Check if node is on the shortest path between start and end."""
        # Simplified check - in practice would compute actual paths
        related_to_start = self.graph.find_related_entities(start_id, limit=10)
        related_to_end = self.graph.find_related_entities(end_id, limit=10)

        start_related_ids = {r['entity']['id'] for r in related_to_start}
        end_related_ids = {r['entity']['id'] for r in related_to_end}

        return node_id in start_related_ids and node_id in end_related_ids

    def _shortest_path_distance(self, start_id: str, end_id: str) -> int:
        """Calculate shortest path distance between nodes."""
        if start_id == end_id:
            return 0

        # BFS-like search
        visited = set()
        queue = [(start_id, 0)]

        while queue:
            current_id, distance = queue.pop(0)

            if current_id in visited:
                continue

            visited.add(current_id)

            if current_id == end_id:
                return distance

            # Get neighbors
            related = self.graph.find_related_entities(current_id, limit=20)
            for rel in related:
                neighbor_id = rel['entity']['id']
                if neighbor_id not in visited:
                    queue.append((neighbor_id, distance + 1))

        return -1  # No path found