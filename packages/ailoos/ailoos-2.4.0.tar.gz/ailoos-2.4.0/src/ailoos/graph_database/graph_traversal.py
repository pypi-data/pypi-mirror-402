"""
Graph Traversal Module
Implements various graph traversal algorithms.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from collections import defaultdict, deque
from heapq import heappush, heappop
from .neo4j_integration import Neo4jIntegration
import logging

logger = logging.getLogger(__name__)


class GraphTraversal:
    """
    Graph traversal algorithms for Neo4j graphs.
    """

    def __init__(self, neo4j_integration: Neo4jIntegration):
        """
        Initialize graph traversal.

        Args:
            neo4j_integration: Neo4j integration instance
        """
        self.neo4j = neo4j_integration

    def breadth_first_search(self, start_node_id: int, max_depth: int = 10,
                           relationship_types: Optional[List[str]] = None,
                           direction: str = "outgoing") -> Dict[str, Any]:
        """
        Perform breadth-first search from a starting node.

        Args:
            start_node_id: Starting node ID
            max_depth: Maximum traversal depth
            relationship_types: Types of relationships to traverse
            direction: Traversal direction ('outgoing', 'incoming', 'both')

        Returns:
            BFS traversal result with levels and paths
        """
        # Build relationship pattern
        rel_pattern = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_pattern = f":{types_str}"

        # Direction arrows
        if direction == "outgoing":
            arrow = f"-[r{rel_pattern}]->"
        elif direction == "incoming":
            arrow = f"<-[r{rel_pattern}]-"
        else:  # both
            arrow = f"-[r{rel_pattern}]-"

        query = f"""
        MATCH path = (start){arrow}(node)
        WHERE id(start) = $start_id AND length(path) <= $max_depth
        WITH node, length(path) as depth, path
        ORDER BY depth, id(node)
        RETURN id(node) as node_id, depth, [n IN nodes(path) | id(n)] as path
        """

        result = self.neo4j.execute_query(query, {
            "start_id": start_node_id,
            "max_depth": max_depth
        })

        # Organize by levels
        levels = defaultdict(list)
        paths = {}

        for record in result:
            node_id = record['node_id']
            depth = record['depth']
            path = record['path']

            levels[depth].append(node_id)
            paths[node_id] = path

        return {
            'levels': dict(levels),
            'paths': paths,
            'visited_nodes': list(paths.keys()),
            'max_depth_reached': max(levels.keys()) if levels else 0
        }

    def depth_first_search(self, start_node_id: int, max_depth: int = 10,
                          relationship_types: Optional[List[str]] = None,
                          direction: str = "outgoing") -> Dict[str, Any]:
        """
        Perform depth-first search from a starting node.

        Args:
            start_node_id: Starting node ID
            max_depth: Maximum traversal depth
            relationship_types: Types of relationships to traverse
            direction: Traversal direction

        Returns:
            DFS traversal result
        """
        # For DFS in Cypher, we can use path patterns with ordering
        rel_pattern = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_pattern = f":{types_str}"

        if direction == "outgoing":
            arrow = f"-[r{rel_pattern}]->"
        elif direction == "incoming":
            arrow = f"<-[r{rel_pattern}]-"
        else:
            arrow = f"-[r{rel_pattern}]-"

        query = f"""
        MATCH path = (start){arrow}(node)
        WHERE id(start) = $start_id AND length(path) <= $max_depth
        WITH path, [n IN nodes(path) | id(n)] as nodeIds
        ORDER BY size(nodeIds) DESC, nodeIds
        RETURN nodeIds as path, size(nodeIds)-1 as depth
        """

        result = self.neo4j.execute_query(query, {
            "start_id": start_node_id,
            "max_depth": max_depth
        })

        # Process DFS-like ordering (longest paths first)
        visited_nodes = set()
        paths = []

        for record in result:
            path = record['path']
            if path:
                # Add new nodes to visited set
                for node_id in path:
                    if node_id not in visited_nodes:
                        visited_nodes.add(node_id)
                paths.append(path)

        return {
            'paths': paths,
            'visited_nodes': list(visited_nodes),
            'total_paths': len(paths)
        }

    def shortest_path_dijkstra(self, start_node_id: int, end_node_id: int,
                              weight_property: str = "weight",
                              relationship_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Find shortest path using Dijkstra's algorithm.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            weight_property: Property name for edge weights
            relationship_types: Allowed relationship types

        Returns:
            Shortest path information or None if no path exists
        """
        try:
            # Try using Neo4j GDS Dijkstra
            rel_config = "*"
            if relationship_types:
                rel_config = {"type": "|".join(relationship_types), "properties": weight_property}

            query = """
            MATCH (start), (end)
            WHERE id(start) = $start_id AND id(end) = $end_id
            CALL gds.shortestPath.dijkstra.stream({
                sourceNode: start,
                targetNode: end,
                nodeProjection: '*',
                relationshipProjection: $rel_config,
                relationshipWeightProperty: $weight_property
            })
            YIELD nodeIds, totalCost, path
            RETURN nodeIds, totalCost, path
            """

            result = self.neo4j.execute_query(query, {
                "start_id": start_node_id,
                "end_id": end_node_id,
                "rel_config": rel_config,
                "weight_property": weight_property
            })

            if result:
                record = result[0]
                return {
                    'path': [int(nid) for nid in record['nodeIds']],
                    'total_cost': float(record['totalCost']),
                    'path_details': record['path']
                }
        except Exception:
            logger.warning("GDS Dijkstra not available, using Cypher shortestPath")

        # Fallback to Cypher shortestPath (unweighted)
        rel_pattern = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_pattern = f"[:{types_str}*]"

        query = f"""
        MATCH path = shortestPath((start){rel_pattern}(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN [n IN nodes(path) | id(n)] as path, length(path) as length
        """

        result = self.neo4j.execute_query(query, {
            "start_id": start_node_id,
            "end_id": end_node_id
        })

        if result and result[0]['path']:
            return {
                'path': result[0]['path'],
                'total_cost': result[0]['length'],  # Unweighted length
                'path_details': None
            }

        return None

    def a_star_search(self, start_node_id: int, end_node_id: int,
                     heuristic_func: Optional[Callable[[int], float]] = None,
                     weight_property: str = "weight",
                     relationship_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        A* search algorithm for shortest path with heuristic.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            heuristic_func: Heuristic function (node_id -> estimated cost to end)
            weight_property: Edge weight property
            relationship_types: Allowed relationship types

        Returns:
            A* path result or None if no path exists
        """
        try:
            # Use Neo4j GDS A* if available
            rel_config = {"properties": weight_property}
            if relationship_types:
                rel_config["type"] = "|".join(relationship_types)

            query = """
            MATCH (start), (end)
            WHERE id(start) = $start_id AND id(end) = $end_id
            CALL gds.shortestPath.astar.stream({
                sourceNode: start,
                targetNode: end,
                nodeProjection: '*',
                relationshipProjection: $rel_config,
                relationshipWeightProperty: $weight_property,
                latitudeProperty: $lat_prop,
                longitudeProperty: $lon_prop
            })
            YIELD nodeIds, totalCost
            RETURN nodeIds, totalCost
            """

            # For geographic A*, we need lat/lon properties
            result = self.neo4j.execute_query(query, {
                "start_id": start_node_id,
                "end_id": end_node_id,
                "rel_config": rel_config,
                "weight_property": weight_property,
                "lat_prop": "latitude",
                "lon_prop": "longitude"
            })

            if result:
                record = result[0]
                return {
                    'path': [int(nid) for nid in record['nodeIds']],
                    'total_cost': float(record['totalCost'])
                }
        except Exception:
            logger.warning("GDS A* not available")

        # Fallback to basic implementation (would need to implement A* in Python)
        # For now, return Dijkstra result
        return self.shortest_path_dijkstra(start_node_id, end_node_id, weight_property, relationship_types)

    def traverse_with_conditions(self, start_node_id: int,
                               node_filter: Optional[str] = None,
                               relationship_filter: Optional[str] = None,
                               max_depth: int = 5,
                               traversal_type: str = "BFS") -> Dict[str, Any]:
        """
        Traverse graph with custom conditions.

        Args:
            start_node_id: Starting node ID
            node_filter: Cypher WHERE clause for nodes
            relationship_filter: Cypher WHERE clause for relationships
            max_depth: Maximum depth
            traversal_type: "BFS" or "DFS"

        Returns:
            Traversal results
        """
        node_where = f"AND ({node_filter})" if node_filter else ""
        rel_where = f"WHERE {relationship_filter}" if relationship_filter else ""

        order_by = "length(path), id(node)" if traversal_type == "BFS" else "length(path) DESC, id(node)"

        query = f"""
        MATCH path = (start)-[*1..{max_depth}]-(node)
        {rel_where}
        WHERE id(start) = $start_id {node_where}
        WITH path, node, length(path) as depth
        ORDER BY {order_by}
        RETURN id(node) as node_id, depth, [n IN nodes(path) | id(n)] as path
        """

        result = self.neo4j.execute_query(query, {"start_id": start_node_id})

        nodes = []
        paths = {}
        levels = defaultdict(list)

        for record in result:
            node_id = record['node_id']
            depth = record['depth']
            path = record['path']

            nodes.append(node_id)
            paths[node_id] = path
            levels[depth].append(node_id)

        return {
            'nodes': nodes,
            'paths': paths,
            'levels': dict(levels),
            'traversal_type': traversal_type
        }

    def find_all_paths(self, start_node_id: int, end_node_id: int,
                      max_length: int = 10,
                      relationship_types: Optional[List[str]] = None) -> List[List[int]]:
        """
        Find all paths between two nodes.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            max_length: Maximum path length
            relationship_types: Allowed relationship types

        Returns:
            List of all paths (each path is a list of node IDs)
        """
        rel_pattern = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_pattern = f"[:{types_str}*1..{max_length}]"

        query = f"""
        MATCH path = (start){rel_pattern}(end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN [n IN nodes(path) | id(n)] as path
        ORDER BY length(path)
        """

        result = self.neo4j.execute_query(query, {
            "start_id": start_node_id,
            "end_id": end_node_id
        })

        return [record['path'] for record in result if record['path']]

    def connected_components(self) -> List[List[int]]:
        """
        Find connected components in the graph.

        Returns:
            List of connected components (each is a list of node IDs)
        """
        try:
            # Use Neo4j GDS
            query = """
            CALL gds.connectedComponents.stream({
                nodeProjection: '*',
                relationshipProjection: '*'
            })
            YIELD nodeId, componentId
            RETURN componentId, collect(nodeId) as component
            ORDER BY size(component) DESC
            """

            result = self.neo4j.execute_query(query)
            return [record['component'] for record in result]
        except Exception:
            # Fallback to basic connected components using Cypher
            query = """
            MATCH (n)
            WITH n, id(n) as nodeId
            MATCH path = (n)-[*0..]-(connected)
            WITH nodeId, collect(DISTINCT id(connected)) as component
            RETURN component
            ORDER BY size(component) DESC
            """

            result = self.neo4j.execute_query(query)
            return [record['component'] for record in result]

    def minimum_spanning_tree(self, weight_property: str = "weight") -> List[Tuple[int, int, float]]:
        """
        Calculate minimum spanning tree.

        Args:
            weight_property: Edge weight property

        Returns:
            List of edges in MST (start_id, end_id, weight)
        """
        try:
            query = f"""
            CALL gds.minimumSpanningTree.stream({{
                nodeProjection: '*',
                relationshipProjection: {{
                    REL: {{
                        type: '*',
                        properties: '{weight_property}'
                    }}
                }},
                relationshipWeightProperty: '{weight_property}'
            }})
            YIELD sourceNodeId, targetNodeId, weight
            RETURN sourceNodeId, targetNodeId, weight
            ORDER BY weight
            """

            result = self.neo4j.execute_query(query)
            return [(int(record['sourceNodeId']), int(record['targetNodeId']), float(record['weight']))
                   for record in result]
        except Exception:
            logger.warning("GDS MST not available")
            return []

    def pagerank(self, iterations: int = 20, damping_factor: float = 0.85) -> Dict[int, float]:
        """
        Calculate PageRank centrality.

        Args:
            iterations: Number of iterations
            damping_factor: Damping factor

        Returns:
            Dictionary mapping node IDs to PageRank scores
        """
        try:
            query = f"""
            CALL gds.pageRank.stream({{
                nodeProjection: '*',
                relationshipProjection: '*',
                maxIterations: {iterations},
                dampingFactor: {damping_factor}
            }})
            YIELD nodeId, score
            RETURN nodeId, score
            """

            result = self.neo4j.execute_query(query)
            return {int(record['nodeId']): float(record['score']) for record in result}
        except Exception:
            logger.warning("GDS PageRank not available")
            # Return basic degree centrality as fallback
            degrees = self._get_basic_degrees()
            total_nodes = len(degrees)
            return {node_id: degree / total_nodes for node_id, degree in degrees.items()}

    def _get_basic_degrees(self) -> Dict[int, int]:
        """Get basic degree centrality."""
        query = "MATCH (n)-[r]-() RETURN id(n) as node_id, count(r) as degree"
        result = self.neo4j.execute_query(query)
        return {record['node_id']: record['degree'] for record in result}

    def random_walk(self, start_node_id: int, steps: int = 10,
                   relationship_types: Optional[List[str]] = None) -> List[int]:
        """
        Perform random walk from a starting node.

        Args:
            start_node_id: Start node ID
            steps: Number of steps
            relationship_types: Allowed relationship types

        Returns:
            List of node IDs visited during the walk
        """
        rel_pattern = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_pattern = f"[:{types_str}]"

        query = f"""
        MATCH path = (start){rel_pattern}->{'{steps}'}(end)
        WHERE id(start) = $start_id
        RETURN [n IN nodes(path) | id(n)] as walk
        LIMIT 1
        """

        result = self.neo4j.execute_query(query, {"start_id": start_node_id})

        if result and result[0]['walk']:
            return result[0]['walk']
        return [start_node_id]  # Return just start node if no walk found