"""
Graph Query Builder Module
Advanced Cypher query builder with fluent interface.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueryType(Enum):
    MATCH = "MATCH"
    CREATE = "CREATE"
    MERGE = "MERGE"
    DELETE = "DELETE"
    SET = "SET"
    REMOVE = "REMOVE"
    RETURN = "RETURN"
    WITH = "WITH"
    UNWIND = "UNWIND"
    CALL = "CALL"


class Direction(Enum):
    OUTGOING = "->"
    INCOMING = "<-"
    BOTH = "-"


class GraphQueryBuilder:
    """
    Fluent Cypher query builder for complex graph queries.
    """

    def __init__(self):
        self._query_parts: List[str] = []
        self._parameters: Dict[str, Any] = {}
        self._param_counter = 0
        self._current_clause: Optional[QueryType] = None

    def match(self, pattern: str = "", **kwargs) -> 'GraphQueryBuilder':
        """
        Add MATCH clause.

        Args:
            pattern: Cypher pattern
            **kwargs: Additional parameters

        Returns:
            Self for chaining
        """
        self._add_clause(QueryType.MATCH, pattern, **kwargs)
        return self

    def create(self, pattern: str = "", **kwargs) -> 'GraphQueryBuilder':
        """
        Add CREATE clause.

        Args:
            pattern: Cypher pattern
            **kwargs: Additional parameters

        Returns:
            Self for chaining
        """
        self._add_clause(QueryType.CREATE, pattern, **kwargs)
        return self

    def merge(self, pattern: str = "", **kwargs) -> 'GraphQueryBuilder':
        """
        Add MERGE clause.

        Args:
            pattern: Cypher pattern
            **kwargs: Additional parameters

        Returns:
            Self for chaining
        """
        self._add_clause(QueryType.MERGE, pattern, **kwargs)
        return self

    def delete(self, variables: Union[str, List[str]], detach: bool = False) -> 'GraphQueryBuilder':
        """
        Add DELETE clause.

        Args:
            variables: Variables to delete
            detach: Whether to detach relationships

        Returns:
            Self for chaining
        """
        if isinstance(variables, str):
            variables = [variables]

        vars_str = ", ".join(variables)
        clause = "DETACH DELETE" if detach else "DELETE"
        self._query_parts.append(f"{clause} {vars_str}")
        return self

    def set(self, properties: Dict[str, Any]) -> 'GraphQueryBuilder':
        """
        Add SET clause.

        Args:
            properties: Properties to set

        Returns:
            Self for chaining
        """
        sets = []
        for var_prop, value in properties.items():
            param_name = self._add_parameter(value)
            sets.append(f"{var_prop} = ${param_name}")

        self._query_parts.append(f"SET {', '.join(sets)}")
        return self

    def remove(self, properties: List[str]) -> 'GraphQueryBuilder':
        """
        Add REMOVE clause.

        Args:
            properties: Properties to remove

        Returns:
            Self for chaining
        """
        self._query_parts.append(f"REMOVE {', '.join(properties)}")
        return self

    def where(self, condition: str, **kwargs) -> 'GraphQueryBuilder':
        """
        Add WHERE clause.

        Args:
            condition: Where condition
            **kwargs: Parameters for the condition

        Returns:
            Self for chaining
        """
        # Replace parameter placeholders with actual parameter names
        for key, value in kwargs.items():
            param_name = self._add_parameter(value)
            condition = condition.replace(f"${key}", f"${param_name}")

        self._query_parts.append(f"WHERE {condition}")
        return self

    def return_(self, items: Union[str, List[str]]) -> 'GraphQueryBuilder':
        """
        Add RETURN clause.

        Args:
            items: Items to return

        Returns:
            Self for chaining
        """
        if isinstance(items, str):
            items = [items]

        self._query_parts.append(f"RETURN {', '.join(items)}")
        return self

    def with_(self, items: Union[str, List[str]]) -> 'GraphQueryBuilder':
        """
        Add WITH clause.

        Args:
            items: Items for WITH clause

        Returns:
            Self for chaining
        """
        if isinstance(items, str):
            items = [items]

        self._query_parts.append(f"WITH {', '.join(items)}")
        return self

    def order_by(self, items: Union[str, List[str]]) -> 'GraphQueryBuilder':
        """
        Add ORDER BY clause.

        Args:
            items: Items to order by

        Returns:
            Self for chaining
        """
        if isinstance(items, str):
            items = [items]

        self._query_parts.append(f"ORDER BY {', '.join(items)}")
        return self

    def limit(self, count: int) -> 'GraphQueryBuilder':
        """
        Add LIMIT clause.

        Args:
            count: Limit count

        Returns:
            Self for chaining
        """
        self._query_parts.append(f"LIMIT {count}")
        return self

    def skip(self, count: int) -> 'GraphQueryBuilder':
        """
        Add SKIP clause.

        Args:
            count: Skip count

        Returns:
            Self for chaining
        """
        self._query_parts.append(f"SKIP {count}")
        return self

    def unwind(self, list_expr: str, as_var: str) -> 'GraphQueryBuilder':
        """
        Add UNWIND clause.

        Args:
            list_expr: List expression
            as_var: Variable name

        Returns:
            Self for chaining
        """
        self._query_parts.append(f"UNWIND {list_expr} AS {as_var}")
        return self

    def call(self, procedure: str, args: Optional[List[Any]] = None,
             yields: Optional[List[str]] = None) -> 'GraphQueryBuilder':
        """
        Add CALL clause for procedures.

        Args:
            procedure: Procedure name
            args: Procedure arguments
            yields: Variables to yield

        Returns:
            Self for chaining
        """
        args_str = ""
        if args:
            arg_names = []
            for arg in args:
                param_name = self._add_parameter(arg)
                arg_names.append(f"${param_name}")
            args_str = f"({', '.join(arg_names)})"

        call_str = f"CALL {procedure}{args_str}"

        if yields:
            call_str += f" YIELD {', '.join(yields)}"

        self._query_parts.append(call_str)
        return self

    def build(self) -> str:
        """
        Build the final Cypher query string.

        Returns:
            Complete Cypher query
        """
        return " ".join(self._query_parts)

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the query parameters.

        Returns:
            Dictionary of parameters
        """
        return self._parameters.copy()

    def _add_clause(self, clause_type: QueryType, pattern: str = "", **kwargs) -> None:
        """Add a clause to the query."""
        clause_str = clause_type.value

        if pattern:
            clause_str += f" {pattern}"

        # Add parameters
        for key, value in kwargs.items():
            param_name = self._add_parameter(value)
            # Replace in pattern if needed
            pattern = pattern.replace(f"${key}", f"${param_name}")

        self._query_parts.append(clause_str)
        self._current_clause = clause_type

    def _add_parameter(self, value: Any) -> str:
        """Add a parameter and return its name."""
        param_name = f"param_{self._param_counter}"
        self._parameters[param_name] = value
        self._param_counter += 1
        return param_name

    # Convenience methods for common patterns

    def find_nodes_by_label(self, label: str, properties: Optional[Dict[str, Any]] = None,
                           limit: Optional[int] = None) -> 'GraphQueryBuilder':
        """
        Build query to find nodes by label and properties.

        Args:
            label: Node label
            properties: Properties to match
            limit: Result limit

        Returns:
            Self for chaining
        """
        pattern = f"(n:{label})"
        self.match(pattern)

        if properties:
            conditions = []
            for prop, value in properties.items():
                param_name = self._add_parameter(value)
                conditions.append(f"n.{prop} = ${param_name}")

            self.where(" AND ".join(conditions))

        if limit:
            self.limit(limit)

        self.return_("n")
        return self

    def find_relationships_by_type(self, rel_type: str, properties: Optional[Dict[str, Any]] = None,
                                  limit: Optional[int] = None) -> 'GraphQueryBuilder':
        """
        Build query to find relationships by type and properties.

        Args:
            rel_type: Relationship type
            properties: Properties to match
            limit: Result limit

        Returns:
            Self for chaining
        """
        pattern = f"()-[r:{rel_type}]->()"
        self.match(pattern)

        if properties:
            conditions = []
            for prop, value in properties.items():
                param_name = self._add_parameter(value)
                conditions.append(f"r.{prop} = ${param_name}")

            self.where(" AND ".join(conditions))

        if limit:
            self.limit(limit)

        self.return_("r")
        return self

    def shortest_path(self, start_label: Optional[str] = None, end_label: Optional[str] = None,
                     rel_types: Optional[List[str]] = None, max_length: int = 10) -> 'GraphQueryBuilder':
        """
        Build shortest path query.

        Args:
            start_label: Start node label
            end_label: End node label
            rel_types: Allowed relationship types
            max_length: Maximum path length

        Returns:
            Self for chaining
        """
        start_pattern = f":{start_label}" if start_label else ""
        end_pattern = f":{end_label}" if end_label else ""

        rel_pattern = ""
        if rel_types:
            types_str = "|".join(rel_types)
            rel_pattern = f"[:{types_str}*1..{max_length}]"
        else:
            rel_pattern = f"[*1..{max_length}]"

        pattern = f"shortestPath((start{start_pattern})-{rel_pattern}->(end{end_pattern}))"
        self.match(pattern)
        self.return_("path")
        return self

    def create_node(self, labels: Union[str, List[str]], properties: Dict[str, Any]) -> 'GraphQueryBuilder':
        """
        Build query to create a node.

        Args:
            labels: Node labels
            properties: Node properties

        Returns:
            Self for chaining
        """
        if isinstance(labels, str):
            labels = [labels]

        labels_str = ":".join(labels)
        props_str = ", ".join([f"{k}: ${self._add_parameter(v)}" for k, v in properties.items()])

        pattern = f"(n:{labels_str} {{{props_str}}})"
        self.create(pattern)
        self.return_("n")
        return self

    def create_relationship(self, start_node_id: int, end_node_id: int, rel_type: str,
                           properties: Optional[Dict[str, Any]] = None) -> 'GraphQueryBuilder':
        """
        Build query to create a relationship.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            rel_type: Relationship type
            properties: Relationship properties

        Returns:
            Self for chaining
        """
        start_param = self._add_parameter(start_node_id)
        end_param = self._add_parameter(end_node_id)

        props_str = ""
        if properties:
            props_list = [f"{k}: ${self._add_parameter(v)}" for k, v in properties.items()]
            props_str = f" {{{', '.join(props_list)}}}"

        pattern = f"(a)-[r:{rel_type}{props_str}]->(b)"
        self.match(f"(a), (b)")
        self.where(f"id(a) = ${start_param} AND id(b) = ${end_param}")
        self.create(pattern)
        self.return_("r")
        return self

    def update_node_properties(self, node_id: int, properties: Dict[str, Any]) -> 'GraphQueryBuilder':
        """
        Build query to update node properties.

        Args:
            node_id: Node ID
            properties: Properties to update

        Returns:
            Self for chaining
        """
        id_param = self._add_parameter(node_id)
        self.match("(n)")
        self.where(f"id(n) = ${id_param}")
        self.set({f"n.{k}": v for k, v in properties.items()})
        self.return_("n")
        return self

    def delete_node(self, node_id: int) -> 'GraphQueryBuilder':
        """
        Build query to delete a node.

        Args:
            node_id: Node ID to delete

        Returns:
            Self for chaining
        """
        id_param = self._add_parameter(node_id)
        self.match("(n)")
        self.where(f"id(n) = ${id_param}")
        self.delete("n", detach=True)
        return self

    def get_neighbors(self, node_id: int, direction: Direction = Direction.BOTH,
                     rel_types: Optional[List[str]] = None, limit: Optional[int] = None) -> 'GraphQueryBuilder':
        """
        Build query to get node neighbors.

        Args:
            node_id: Central node ID
            direction: Relationship direction
            rel_types: Relationship types to include
            limit: Result limit

        Returns:
            Self for chaining
        """
        id_param = self._add_parameter(node_id)

        rel_pattern = ""
        if rel_types:
            types_str = "|".join(rel_types)
            rel_pattern = f":{types_str}"

        arrow = direction.value

        pattern = f"(n){arrow}(neighbor)"
        self.match(pattern)
        self.where(f"id(n) = ${id_param}")

        if limit:
            self.limit(limit)

        self.return_("neighbor")
        return self