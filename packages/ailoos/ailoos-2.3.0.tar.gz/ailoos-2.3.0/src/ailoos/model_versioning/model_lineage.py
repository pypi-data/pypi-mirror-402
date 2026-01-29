from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import networkx as nx
from .semantic_versioning import SemanticVersion
from .model_registry import ModelRegistry


@dataclass
class LineageNode:
    """Nodo en el grafo de linaje."""
    id: str
    type: str  # 'model', 'dataset', 'experiment', 'deployment'
    name: str
    version: Optional[SemanticVersion] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'version': str(self.version) if self.version else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class LineageEdge:
    """Arista en el grafo de linaje."""
    source_id: str
    target_id: str
    relationship_type: str  # 'trained_on', 'derived_from', 'deployed_as', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class LineagePath:
    """Camino en el grafo de linaje."""
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    total_distance: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges],
            'total_distance': self.total_distance
        }


class ModelLineage:
    """
    Sistema de seguimiento de linaje y dependencias de modelos.
    Construye y analiza grafos de dependencias entre modelos, datasets y otros artefactos.
    """

    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        self.model_registry = model_registry
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []
        self.graph = nx.DiGraph()

    def add_node(self, node: LineageNode):
        """
        Agregar un nodo al grafo de linaje.

        Args:
            node: Nodo a agregar
        """
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.to_dict())

    def add_edge(self, edge: LineageEdge):
        """
        Agregar una arista al grafo de linaje.

        Args:
            edge: Arista a agregar
        """
        # Verificar que los nodos existen
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Los nodos source y target deben existir antes de agregar la arista")

        self.edges.append(edge)
        self.graph.add_edge(edge.source_id, edge.target_id,
                          relationship_type=edge.relationship_type,
                          **edge.to_dict())

    def create_model_node(self,
                         model_id: str,
                         name: str,
                         version: Optional[SemanticVersion] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> LineageNode:
        """
        Crear un nodo para un modelo.

        Args:
            model_id: ID del modelo
            name: Nombre del modelo
            version: Versión del modelo
            metadata: Metadata adicional

        Returns:
            Nodo creado
        """
        node = LineageNode(
            id=model_id,
            type='model',
            name=name,
            version=version,
            metadata=metadata or {}
        )
        self.add_node(node)
        return node

    def create_dataset_node(self,
                           dataset_id: str,
                           name: str,
                           metadata: Optional[Dict[str, Any]] = None) -> LineageNode:
        """
        Crear un nodo para un dataset.

        Args:
            dataset_id: ID del dataset
            name: Nombre del dataset
            metadata: Metadata adicional

        Returns:
            Nodo creado
        """
        node = LineageNode(
            id=dataset_id,
            type='dataset',
            name=name,
            metadata=metadata or {}
        )
        self.add_node(node)
        return node

    def create_experiment_node(self,
                              experiment_id: str,
                              name: str,
                              metadata: Optional[Dict[str, Any]] = None) -> LineageNode:
        """
        Crear un nodo para un experimento.

        Args:
            experiment_id: ID del experimento
            name: Nombre del experimento
            metadata: Metadata adicional

        Returns:
            Nodo creado
        """
        node = LineageNode(
            id=experiment_id,
            type='experiment',
            name=name,
            metadata=metadata or {}
        )
        self.add_node(node)
        return node

    def add_relationship(self,
                        source_id: str,
                        target_id: str,
                        relationship_type: str,
                        metadata: Optional[Dict[str, Any]] = None):
        """
        Agregar una relación entre dos nodos.

        Args:
            source_id: ID del nodo fuente
            target_id: ID del nodo destino
            relationship_type: Tipo de relación
            metadata: Metadata de la relación
        """
        edge = LineageEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {}
        )
        self.add_edge(edge)

    def get_ancestors(self, node_id: str, max_depth: Optional[int] = None) -> List[LineageNode]:
        """
        Obtener ancestros de un nodo.

        Args:
            node_id: ID del nodo
            max_depth: Profundidad máxima

        Returns:
            Lista de nodos ancestros
        """
        if node_id not in self.graph:
            return []

        ancestors = []
        visited = set()

        def dfs(current_id: str, depth: int = 0):
            if current_id in visited or (max_depth and depth > max_depth):
                return

            visited.add(current_id)

            for predecessor in self.graph.predecessors(current_id):
                if predecessor not in visited:
                    ancestors.append(self.nodes[predecessor])
                    dfs(predecessor, depth + 1)

        dfs(node_id)
        return ancestors

    def get_descendants(self, node_id: str, max_depth: Optional[int] = None) -> List[LineageNode]:
        """
        Obtener descendientes de un nodo.

        Args:
            node_id: ID del nodo
            max_depth: Profundidad máxima

        Returns:
            Lista de nodos descendientes
        """
        if node_id not in self.graph:
            return []

        descendants = []
        visited = set()

        def dfs(current_id: str, depth: int = 0):
            if current_id in visited or (max_depth and depth > max_depth):
                return

            visited.add(current_id)

            for successor in self.graph.successors(current_id):
                if successor not in visited:
                    descendants.append(self.nodes[successor])
                    dfs(successor, depth + 1)

        dfs(node_id)
        return descendants

    def find_paths(self, source_id: str, target_id: str, max_paths: int = 10) -> List[LineagePath]:
        """
        Encontrar caminos entre dos nodos.

        Args:
            source_id: ID del nodo fuente
            target_id: ID del nodo destino
            max_paths: Número máximo de caminos a retornar

        Returns:
            Lista de caminos encontrados
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []

        try:
            paths = list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=10))
        except nx.NetworkXNoPath:
            return []

        lineage_paths = []
        for path in paths[:max_paths]:
            nodes = [self.nodes[node_id] for node_id in path]
            edges = []

            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]

                # Encontrar la arista correspondiente
                edge_data = self.graph.get_edge_data(source, target)
                if edge_data:
                    edge = LineageEdge(
                        source_id=source,
                        target_id=target,
                        relationship_type=edge_data.get('relationship_type', 'unknown'),
                        metadata=edge_data
                    )
                    edges.append(edge)

            lineage_path = LineagePath(
                nodes=nodes,
                edges=edges,
                total_distance=len(path) - 1
            )
            lineage_paths.append(lineage_path)

        return lineage_paths

    def get_lineage_graph(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Obtener grafo de linaje completo para un nodo.

        Args:
            node_id: ID del nodo central
            depth: Profundidad del grafo

        Returns:
            Diccionario con nodos y aristas del grafo
        """
        if node_id not in self.graph:
            return {'nodes': [], 'edges': []}

        # Obtener subgrafo
        ancestors = self.get_ancestors(node_id, depth)
        descendants = self.get_descendants(node_id, depth)

        relevant_nodes = {node_id}
        relevant_nodes.update(n.id for n in ancestors)
        relevant_nodes.update(n.id for n in descendants)

        # Filtrar aristas relevantes
        relevant_edges = []
        for edge in self.edges:
            if edge.source_id in relevant_nodes and edge.target_id in relevant_nodes:
                relevant_edges.append(edge)

        return {
            'nodes': [self.nodes[node_id].to_dict() for node_id in relevant_nodes],
            'edges': [edge.to_dict() for edge in relevant_edges],
            'central_node': node_id
        }

    def detect_cycles(self) -> List[List[str]]:
        """
        Detectar ciclos en el grafo de linaje.

        Returns:
            Lista de ciclos encontrados
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except:
            return []

    def get_impact_analysis(self, node_id: str) -> Dict[str, Any]:
        """
        Análisis de impacto de cambios en un nodo.

        Args:
            node_id: ID del nodo a analizar

        Returns:
            Diccionario con análisis de impacto
        """
        if node_id not in self.graph:
            return {'affected_nodes': [], 'impact_score': 0}

        descendants = self.get_descendants(node_id)
        affected_models = [n for n in descendants if n.type == 'model']

        # Calcular score de impacto basado en número de descendientes
        impact_score = len(descendants)

        # Considerar tipos de nodos afectados
        model_count = len(affected_models)
        experiment_count = len([n for n in descendants if n.type == 'experiment'])
        dataset_count = len([n for n in descendants if n.type == 'dataset'])

        return {
            'affected_nodes': [n.to_dict() for n in descendants],
            'impact_score': impact_score,
            'affected_models': model_count,
            'affected_experiments': experiment_count,
            'affected_datasets': dataset_count,
            'critical_path': self._find_critical_path(node_id)
        }

    def get_data_provenance(self, model_id: str) -> Dict[str, Any]:
        """
        Obtener procedencia de datos para un modelo.

        Args:
            model_id: ID del modelo

        Returns:
            Diccionario con información de procedencia
        """
        if model_id not in self.nodes or self.nodes[model_id].type != 'model':
            return {'datasets': [], 'data_flow': []}

        # Encontrar datasets relacionados
        datasets = []
        data_flow = []

        # Buscar nodos de tipo dataset conectados
        for edge in self.edges:
            if edge.target_id == model_id and edge.relationship_type == 'trained_on':
                if edge.source_id in self.nodes:
                    source_node = self.nodes[edge.source_id]
                    if source_node.type == 'dataset':
                        datasets.append(source_node.to_dict())
                        data_flow.append({
                            'from': source_node.to_dict(),
                            'to': self.nodes[model_id].to_dict(),
                            'relationship': edge.relationship_type,
                            'metadata': edge.metadata
                        })

        return {
            'datasets': datasets,
            'data_flow': data_flow,
            'provenance_chain': self._build_provenance_chain(model_id)
        }

    def validate_lineage_integrity(self) -> List[str]:
        """
        Validar integridad del grafo de linaje.

        Returns:
            Lista de problemas encontrados
        """
        issues = []

        # Verificar nodos huérfanos
        for node_id in self.nodes:
            if self.graph.degree(node_id) == 0:
                issues.append(f"Nodo huérfano: {node_id}")

        # Verificar referencias rotas
        for edge in self.edges:
            if edge.source_id not in self.nodes:
                issues.append(f"Referencia rota en source: {edge.source_id}")
            if edge.target_id not in self.nodes:
                issues.append(f"Referencia rota en target: {edge.target_id}")

        # Verificar ciclos
        cycles = self.detect_cycles()
        if cycles:
            issues.append(f"Ciclos detectados: {len(cycles)}")

        # Verificar consistencia de versiones
        version_issues = self._check_version_consistency()
        issues.extend(version_issues)

        return issues

    def _find_critical_path(self, node_id: str) -> List[str]:
        """Encontrar camino crítico desde el nodo."""
        if node_id not in self.graph:
            return []

        # Usar longest path como aproximación de camino crítico
        try:
            # NetworkX no tiene longest_path directo, usar aproximación
            critical_path = [node_id]
            current = node_id

            while True:
                successors = list(self.graph.successors(current))
                if not successors:
                    break

                # Elegir el successor con más conexiones (heurística)
                next_node = max(successors, key=lambda x: self.graph.out_degree(x))
                critical_path.append(next_node)
                current = next_node

                # Evitar loops
                if len(critical_path) > len(self.nodes):
                    break

            return critical_path
        except:
            return [node_id]

    def _build_provenance_chain(self, model_id: str) -> List[Dict[str, Any]]:
        """Construir cadena de procedencia."""
        chain = []
        current = model_id

        while current:
            node = self.nodes.get(current)
            if not node:
                break

            chain.append(node.to_dict())

            # Encontrar predecesor de tipo dataset
            predecessors = list(self.graph.predecessors(current))
            dataset_pred = None
            for pred in predecessors:
                if self.nodes[pred].type == 'dataset':
                    dataset_pred = pred
                    break

            current = dataset_pred

        return chain

    def _check_version_consistency(self) -> List[str]:
        """Verificar consistencia de versiones."""
        issues = []

        # Agrupar nodos por nombre y tipo
        name_groups = defaultdict(list)
        for node in self.nodes.values():
            if node.type == 'model' and node.version:
                key = f"{node.type}:{node.name}"
                name_groups[key].append(node)

        # Verificar que las versiones sean consistentes
        for group_name, nodes in name_groups.items():
            versions = [n.version for n in nodes if n.version]
            if len(versions) > 1:
                # Verificar orden cronológico de versiones
                sorted_versions = sorted(versions)
                if versions != sorted_versions:
                    issues.append(f"Inconsistencia de versiones en {group_name}")

        return issues

    def export_lineage(self, file_path: str, format: str = 'json'):
        """
        Exportar grafo de linaje a archivo.

        Args:
            file_path: Ruta del archivo
            format: Formato de exportación
        """
        if format == 'json':
            data = {
                'nodes': [node.to_dict() for node in self.nodes.values()],
                'edges': [edge.to_dict() for edge in self.edges],
                'exported_at': datetime.now().isoformat()
            }

            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def import_lineage(self, file_path: str):
        """
        Importar grafo de linaje desde archivo.

        Args:
            file_path: Ruta del archivo
        """
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Importar nodos
        for node_data in data.get('nodes', []):
            node = LineageNode(
                id=node_data['id'],
                type=node_data['type'],
                name=node_data['name'],
                version=SemanticVersion(node_data['version']) if node_data.get('version') else None,
                metadata=node_data.get('metadata', {}),
                created_at=datetime.fromisoformat(node_data['created_at'])
            )
            self.add_node(node)

        # Importar aristas
        for edge_data in data.get('edges', []):
            edge = LineageEdge(
                source_id=edge_data['source_id'],
                target_id=edge_data['target_id'],
                relationship_type=edge_data['relationship_type'],
                metadata=edge_data.get('metadata', {}),
                created_at=datetime.fromisoformat(edge_data['created_at'])
            )
            self.add_edge(edge)