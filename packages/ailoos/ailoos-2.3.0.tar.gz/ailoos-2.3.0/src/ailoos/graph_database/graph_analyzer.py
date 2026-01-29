"""
Graph Analyzer Module
Analyzes graph structure and patterns.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, deque
from .neo4j_integration import Neo4jIntegration
import logging

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """
    Graph analysis and pattern detection class.
    """

    def __init__(self, neo4j_integration: Neo4jIntegration):
        """
        Initialize graph analyzer.

        Args:
            neo4j_integration: Neo4j integration instance
        """
        self.neo4j = neo4j_integration

    def get_degree_centrality(self, node_id: Optional[int] = None,
                             direction: str = "both") -> Dict[int, int]:
        """
        Calculate degree centrality for nodes.

        Args:
            node_id: Specific node ID, or None for all nodes
            direction: Direction ('incoming', 'outgoing', 'both')

        Returns:
            Dictionary mapping node IDs to degree centrality scores
        """
        if node_id:
            # Single node degree
            if direction == "incoming":
                query = "MATCH (n)<-[r]-() WHERE id(n) = $node_id RETURN count(r) as degree"
            elif direction == "outgoing":
                query = "MATCH (n)-[r]->() WHERE id(n) = $node_id RETURN count(r) as degree"
            else:  # both
                query = "MATCH (n)-[r]-() WHERE id(n) = $node_id RETURN count(r) as degree"

            result = self.neo4j.execute_query(query, {"node_id": node_id})
            return {node_id: result[0]['degree'] if result else 0}
        else:
            # All nodes degree
            if direction == "incoming":
                query = "MATCH (n)<-[r]-() RETURN id(n) as node_id, count(r) as degree"
            elif direction == "outgoing":
                query = "MATCH (n)-[r]->() RETURN id(n) as node_id, count(r) as degree"
            else:  # both
                query = "MATCH (n)-[r]-() RETURN id(n) as node_id, count(r) as degree"

            result = self.neo4j.execute_query(query)
            return {record['node_id']: record['degree'] for record in result}

    def get_betweenness_centrality(self, sample_size: Optional[int] = None) -> Dict[int, float]:
        """
        Calculate betweenness centrality using Neo4j Graph Data Science.

        Args:
            sample_size: Number of nodes to sample (for large graphs)

        Returns:
            Dictionary mapping node IDs to betweenness centrality scores
        """
        try:
            # Try using Neo4j GDS if available
            limit_clause = f" LIMIT {sample_size}" if sample_size else ""

            query = f"""
            CALL gds.betweenness.stream({{
                nodeProjection: '*',
                relationshipProjection: '*'
            }})
            YIELD nodeId, score
            RETURN nodeId, score{limit_clause}
            """

            result = self.neo4j.execute_query(query)
            return {int(record['nodeId']): float(record['score']) for record in result}
        except Exception:
            # Fallback to basic implementation (simplified)
            logger.warning("Neo4j GDS not available, using simplified betweenness calculation")
            return self._calculate_basic_betweenness(sample_size)

    def _calculate_basic_betweenness(self, sample_size: Optional[int] = None) -> Dict[int, float]:
        """Basic betweenness centrality calculation for small graphs."""
        # Get all nodes
        nodes_query = "MATCH (n) RETURN id(n) as id"
        if sample_size:
            nodes_query += f" LIMIT {sample_size}"

        nodes_result = self.neo4j.execute_query(nodes_query)
        node_ids = [record['id'] for record in nodes_result]

        betweenness = defaultdict(float)

        # For each pair of nodes, find shortest paths
        for i, start_id in enumerate(node_ids):
            for end_id in node_ids[i+1:]:
                paths = self._find_all_shortest_paths(start_id, end_id)
                if not paths:
                    continue

                # Count how many times each node appears in shortest paths
                node_counts = defaultdict(int)
                total_paths = len(paths)

                for path in paths:
                    for node_id in path[1:-1]:  # Exclude start and end
                        node_counts[node_id] += 1

                # Update betweenness scores
                for node_id, count in node_counts.items():
                    betweenness[node_id] += count / total_paths

        return dict(betweenness)

    def _find_all_shortest_paths(self, start_id: int, end_id: int, max_depth: int = 5) -> List[List[int]]:
        """Find all shortest paths between two nodes."""
        # Simplified implementation - in practice would use more efficient algorithms
        query = f"""
        MATCH path = shortestPath((start)-[*1..{max_depth}]-(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN nodes(path) as path_nodes
        """

        result = self.neo4j.execute_query(query, {"start_id": start_id, "end_id": end_id})

        paths = []
        for record in result:
            nodes = record['path_nodes']
            if nodes:
                path_ids = [node.id for node in nodes]  # Assuming nodes have id attribute
                paths.append(path_ids)

        return paths

    def detect_communities(self, algorithm: str = "louvain") -> Dict[int, int]:
        """
        Detect communities in the graph.

        Args:
            algorithm: Community detection algorithm ('louvain', 'label_propagation')

        Returns:
            Dictionary mapping node IDs to community IDs
        """
        try:
            if algorithm == "louvain":
                query = """
                CALL gds.louvain.stream({
                    nodeProjection: '*',
                    relationshipProjection: '*'
                })
                YIELD nodeId, communityId
                RETURN nodeId, communityId
                """
            elif algorithm == "label_propagation":
                query = """
                CALL gds.labelPropagation.stream({
                    nodeProjection: '*',
                    relationshipProjection: '*'
                })
                YIELD nodeId, communityId
                RETURN nodeId, communityId
                """
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            result = self.neo4j.execute_query(query)
            return {int(record['nodeId']): int(record['communityId']) for record in result}
        except Exception:
            logger.warning(f"GDS {algorithm} not available, using basic community detection")
            return self._basic_community_detection()

    def _basic_community_detection(self) -> Dict[int, int]:
        """Basic community detection using connected components."""
        # Simple connected components as communities
        query = """
        MATCH (n)
        WITH n, id(n) as nodeId
        MATCH path = (n)-[*0..]-(connected)
        WITH nodeId, collect(DISTINCT id(connected)) as component
        RETURN nodeId, component[0] as communityId
        ORDER BY communityId
        """

        result = self.neo4j.execute_query(query)
        return {record['nodeId']: record['communityId'] for record in result}

    def find_cliques(self, min_size: int = 3) -> List[List[int]]:
        """
        Find cliques in the graph.

        Args:
            min_size: Minimum clique size

        Returns:
            List of cliques (each clique is a list of node IDs)
        """
        # Using Neo4j's triangle finding as basis for clique detection
        query = f"""
        CALL gds.triangle.stream({{
            nodeProjection: '*',
            relationshipProjection: '*'
        }})
        YIELD nodeA, nodeB, nodeC
        RETURN [nodeA, nodeB, nodeC] as clique
        """

        try:
            result = self.neo4j.execute_query(query)
            cliques = []
            for record in result:
                clique = [int(record['clique'][0]), int(record['clique'][1]), int(record['clique'][2])]
                if len(clique) >= min_size:
                    cliques.append(sorted(clique))
            return cliques
        except Exception:
            logger.warning("GDS triangle detection not available")
            return []

    def calculate_clustering_coefficient(self, node_id: Optional[int] = None) -> Dict[int, float]:
        """
        Calculate clustering coefficient for nodes.

        Args:
            node_id: Specific node ID, or None for all nodes

        Returns:
            Dictionary mapping node IDs to clustering coefficients
        """
        try:
            if node_id:
                query = f"""
                CALL gds.localClusteringCoefficient.stream({{
                    nodeProjection: '*',
                    relationshipProjection: '*'
                }})
                YIELD nodeId, localClusteringCoefficient
                WHERE nodeId = $node_id
                RETURN nodeId, localClusteringCoefficient
                """
                params = {"node_id": node_id}
            else:
                query = """
                CALL gds.localClusteringCoefficient.stream({
                    nodeProjection: '*',
                    relationshipProjection: '*'
                })
                YIELD nodeId, localClusteringCoefficient
                RETURN nodeId, localClusteringCoefficient
                """
                params = {}

            result = self.neo4j.execute_query(query, params)
            return {int(record['nodeId']): float(record['localClusteringCoefficient']) for record in result}
        except Exception:
            logger.warning("GDS clustering coefficient not available, using basic calculation")
            return self._calculate_basic_clustering_coefficient(node_id)

    def _calculate_basic_clustering_coefficient(self, node_id: Optional[int] = None) -> Dict[int, float]:
        """Basic clustering coefficient calculation."""
        if node_id:
            nodes = [node_id]
        else:
            # Get all nodes
            result = self.neo4j.execute_query("MATCH (n) RETURN id(n) as id")
            nodes = [record['id'] for record in result]

        coefficients = {}

        for nid in nodes:
            # Get neighbors
            neighbors_query = """
            MATCH (n)-[r]-(neighbor)
            WHERE id(n) = $node_id AND id(neighbor) <> id(n)
            RETURN DISTINCT id(neighbor) as neighbor_id
            """
            neighbors_result = self.neo4j.execute_query(neighbors_query, {"node_id": nid})
            neighbors = [record['neighbor_id'] for record in neighbors_result]

            if len(neighbors) < 2:
                coefficients[nid] = 0.0
                continue

            # Count connections between neighbors
            connected_pairs = 0
            possible_pairs = len(neighbors) * (len(neighbors) - 1) / 2

            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i+1:]:
                    # Check if n1 and n2 are connected
                    connection_query = """
                    MATCH (a)-[r]-(b)
                    WHERE id(a) = $n1 AND id(b) = $n2
                    RETURN count(r) > 0 as connected
                    """
                    conn_result = self.neo4j.execute_query(connection_query, {"n1": n1, "n2": n2})
                    if conn_result and conn_result[0]['connected']:
                        connected_pairs += 1

            coefficients[nid] = connected_pairs / possible_pairs if possible_pairs > 0 else 0.0

        return coefficients

    def find_shortest_path(self, start_node_id: int, end_node_id: int,
                          relationship_types: Optional[List[str]] = None) -> Optional[List[int]]:
        """
        Find shortest path between two nodes.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            relationship_types: Allowed relationship types

        Returns:
            List of node IDs in the path, or None if no path exists
        """
        types_filter = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            types_filter = f"[:{types_str}*]"

        query = f"""
        MATCH path = shortestPath((start)-{types_filter}->(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN [node IN nodes(path) | id(node)] as path_ids
        """

        result = self.neo4j.execute_query(query, {"start_id": start_node_id, "end_id": end_node_id})

        if result and result[0]['path_ids']:
            return result[0]['path_ids']
        return None

    def get_graph_density(self) -> float:
        """
        Calculate graph density.

        Returns:
            Graph density (0.0 to 1.0)
        """
        # Get node and relationship counts
        node_count = self.neo4j.get_node_count()
        rel_count = self.neo4j.get_relationship_count()

        if node_count < 2:
            return 0.0

        # Density = 2 * |E| / (|V| * (|V| - 1))
        max_possible_edges = node_count * (node_count - 1)
        return (2 * rel_count) / max_possible_edges if max_possible_edges > 0 else 0.0

    def detect_cycles(self, max_length: int = 10) -> List[List[int]]:
        """
        Detect cycles in the graph.

        Args:
            max_length: Maximum cycle length to detect

        Returns:
            List of cycles (each cycle is a list of node IDs)
        """
        query = f"""
        MATCH path = (n)-[*1..{max_length}]-(n)
        WHERE length(path) > 2
        RETURN [node IN nodes(path) | id(node)] as cycle
        LIMIT 100
        """

        result = self.neo4j.execute_query(query)
        cycles = []

        for record in result:
            cycle = record['cycle']
            if cycle and len(cycle) > 2:
                # Remove duplicate start/end and ensure it's a cycle
                if cycle[0] == cycle[-1]:
                    cycle = cycle[:-1]
                cycles.append(cycle)

        return cycles

    def get_node_similarity(self, node_id1: int, node_id2: int) -> float:
        """
        Calculate similarity between two nodes based on common neighbors.

        Args:
            node_id1: First node ID
            node_id2: Second node ID

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Get neighbors of both nodes
        neighbors1_query = """
        MATCH (n)-[r]-(neighbor)
        WHERE id(n) = $node_id
        RETURN DISTINCT id(neighbor) as neighbor_id
        """
        neighbors1 = set()
        result1 = self.neo4j.execute_query(neighbors1_query, {"node_id": node_id1})
        for record in result1:
            neighbors1.add(record['neighbor_id'])

        neighbors2 = set()
        result2 = self.neo4j.execute_query(neighbors1_query, {"node_id": node_id2})
        for record in result2:
            neighbors2.add(record['neighbor_id'])

        # Jaccard similarity
        intersection = len(neighbors1 & neighbors2)
        union = len(neighbors1 | neighbors2)

        return intersection / union if union > 0 else 0.0

    def analyze_graph_structure(self) -> Dict[str, Any]:
        """
        Comprehensive graph structure analysis.

        Returns:
            Dictionary with various graph metrics
        """
        analysis = {
            'node_count': self.neo4j.get_node_count(),
            'relationship_count': self.neo4j.get_relationship_count(),
            'density': self.get_graph_density(),
        }

        # Degree distribution
        degrees = self.get_degree_centrality()
        if degrees:
            analysis['avg_degree'] = sum(degrees.values()) / len(degrees)
            analysis['max_degree'] = max(degrees.values())
            analysis['min_degree'] = min(degrees.values())

        # Try to get clustering coefficient for a sample
        try:
            clustering = self.calculate_clustering_coefficient()
            if clustering:
                analysis['avg_clustering_coefficient'] = sum(clustering.values()) / len(clustering)
        except Exception:
            analysis['avg_clustering_coefficient'] = None

        # Community detection
        try:
            communities = self.detect_communities()
            analysis['community_count'] = len(set(communities.values())) if communities else 0
        except Exception:
            analysis['community_count'] = None

        return analysis