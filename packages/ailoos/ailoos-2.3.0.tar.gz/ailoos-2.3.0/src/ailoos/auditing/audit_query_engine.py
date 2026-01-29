"""
Advanced Audit Query Engine with complex filtering and analytics.
Supports SQL-like queries, aggregations, and real-time analytics.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import operator

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity
from .audit_storage import AuditStorage


class QueryOperator(Enum):
    """Query operators for filtering."""
    EQ = "="
    NE = "!="
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="
    IN = "IN"
    NOT_IN = "NOT_IN"
    LIKE = "LIKE"
    NOT_LIKE = "NOT_LIKE"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"


class AggregationFunction(Enum):
    """Aggregation functions for analytics."""
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    DISTINCT = "DISTINCT"


@dataclass
class QueryCondition:
    """A single query condition."""
    field: str
    operator: QueryOperator
    value: Any
    case_sensitive: bool = True

    def matches(self, event: AuditEvent) -> bool:
        """Check if event matches this condition."""
        try:
            field_value = self._get_field_value(event, self.field)
            return self._evaluate_condition(field_value, self.operator, self.value)
        except (AttributeError, KeyError, TypeError):
            return False

    def _get_field_value(self, event: AuditEvent, field: str) -> Any:
        """Get field value from event, supporting nested fields."""
        if '.' in field:
            # Handle nested fields like 'details.key'
            parts = field.split('.')
            value = event
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    raise KeyError(f"Field {field} not found")
            return value
        else:
            # Direct field access
            if hasattr(event, field):
                return getattr(event, field)
            elif field in event.details:
                return event.details[field]
            else:
                raise KeyError(f"Field {field} not found")

    def _evaluate_condition(self, field_value: Any, op: QueryOperator, expected_value: Any) -> bool:
        """Evaluate condition based on operator."""
        if op == QueryOperator.IS_NULL:
            return field_value is None
        elif op == QueryOperator.IS_NOT_NULL:
            return field_value is not None

        if field_value is None:
            return False

        # Type conversion for comparison
        if isinstance(field_value, datetime) and isinstance(expected_value, str):
            expected_value = datetime.fromisoformat(expected_value)
        elif isinstance(expected_value, datetime) and isinstance(field_value, str):
            field_value = datetime.fromisoformat(field_value)

        # String case sensitivity
        if isinstance(field_value, str) and isinstance(expected_value, str) and not self.case_sensitive:
            field_value = field_value.lower()
            expected_value = expected_value.lower()

        if op == QueryOperator.EQ:
            return field_value == expected_value
        elif op == QueryOperator.NE:
            return field_value != expected_value
        elif op == QueryOperator.GT:
            return field_value > expected_value
        elif op == QueryOperator.GE:
            return field_value >= expected_value
        elif op == QueryOperator.LT:
            return field_value < expected_value
        elif op == QueryOperator.LE:
            return field_value <= expected_value
        elif op == QueryOperator.IN:
            return field_value in expected_value
        elif op == QueryOperator.NOT_IN:
            return field_value not in expected_value
        elif op == QueryOperator.LIKE:
            return re.search(expected_value.replace('%', '.*'), str(field_value)) is not None
        elif op == QueryOperator.NOT_LIKE:
            return re.search(expected_value.replace('%', '.*'), str(field_value)) is None
        elif op == QueryOperator.CONTAINS:
            return expected_value in str(field_value)
        elif op == QueryOperator.NOT_CONTAINS:
            return expected_value not in str(field_value)
        elif op == QueryOperator.BETWEEN:
            return expected_value[0] <= field_value <= expected_value[1]

        return False


@dataclass
class QueryFilter:
    """Complex query filter with multiple conditions."""
    conditions: List[QueryCondition]
    logic: str = "AND"  # AND, OR

    def matches(self, event: AuditEvent) -> bool:
        """Check if event matches the filter."""
        if not self.conditions:
            return True

        results = [condition.matches(event) for condition in self.conditions]

        if self.logic == "AND":
            return all(results)
        elif self.logic == "OR":
            return any(results)
        else:
            return False


@dataclass
class QuerySort:
    """Sorting specification."""
    field: str
    ascending: bool = True

    def sort_key(self, event: AuditEvent) -> Any:
        """Get sort key for event."""
        try:
            value = getattr(event, self.field, None)
            if value is None and self.field in event.details:
                value = event.details[self.field]
            return value if value is not None else ""
        except:
            return ""


@dataclass
class AggregationSpec:
    """Aggregation specification."""
    function: AggregationFunction
    field: Optional[str] = None
    alias: Optional[str] = None


@dataclass
class QuerySpec:
    """Complete query specification."""
    filters: Optional[QueryFilter] = None
    sort: Optional[List[QuerySort]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    aggregations: Optional[List[AggregationSpec]] = None
    group_by: Optional[List[str]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None


@dataclass
class QueryResult:
    """Query result with metadata."""
    events: List[AuditEvent]
    total_count: int
    execution_time_ms: float
    aggregations: Optional[Dict[str, Any]] = None
    groups: Optional[Dict[str, List[AuditEvent]]] = None


class AuditQueryEngine:
    """
    Advanced query engine for audit events.
    Supports complex filtering, aggregations, and analytics.
    """

    def __init__(self, storage: AuditStorage):
        self.storage = storage
        self.logger = get_logger("audit_query_engine")

        # Query cache for performance
        self.query_cache: Dict[str, Tuple[QueryResult, datetime]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes

        # Statistics
        self.stats = {
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_execution_time': 0.0
        }

    async def execute_query(self, query_spec: QuerySpec) -> QueryResult:
        """Execute a complex query."""
        start_time = datetime.now()

        # Generate cache key
        cache_key = self._generate_cache_key(query_spec)

        # Check cache
        if cache_key in self.query_cache:
            cached_result, cache_time = self.query_cache[cache_key]
            if (datetime.now() - cache_time).seconds < self.cache_ttl_seconds:
                self.stats['cache_hits'] += 1
                return cached_result

        self.stats['cache_misses'] += 1

        try:
            # Get candidate events from storage
            candidates = await self._get_candidate_events(query_spec)

            # Apply filters
            filtered_events = self._apply_filters(candidates, query_spec.filters)

            # Apply time range filter
            if query_spec.time_range:
                filtered_events = self._apply_time_range(filtered_events, query_spec.time_range)

            # Apply sorting
            if query_spec.sort:
                filtered_events = self._apply_sorting(filtered_events, query_spec.sort)

            # Apply pagination
            total_count = len(filtered_events)
            if query_spec.offset:
                filtered_events = filtered_events[query_spec.offset:]
            if query_spec.limit:
                filtered_events = filtered_events[:query_spec.limit]

            # Calculate aggregations
            aggregations = None
            if query_spec.aggregations:
                aggregations = self._calculate_aggregations(filtered_events, query_spec.aggregations)

            # Group results
            groups = None
            if query_spec.group_by:
                groups = self._group_events(filtered_events, query_spec.group_by)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            result = QueryResult(
                events=filtered_events,
                total_count=total_count,
                execution_time_ms=execution_time,
                aggregations=aggregations,
                groups=groups
            )

            # Cache result
            self.query_cache[cache_key] = (result, datetime.now())

            # Update stats
            self.stats['queries_executed'] += 1
            self.stats['avg_execution_time'] = (
                (self.stats['avg_execution_time'] * (self.stats['queries_executed'] - 1)) + execution_time
            ) / self.stats['queries_executed']

            return result

        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            raise

    async def _get_candidate_events(self, query_spec: QuerySpec) -> List[AuditEvent]:
        """Get candidate events from storage using indexes."""
        # Use storage indexes for efficient filtering
        filters = {}
        if query_spec.filters:
            # Extract simple equality filters for index usage
            for condition in query_spec.filters.conditions:
                if condition.operator == QueryOperator.EQ:
                    filters[condition.field] = condition.value

        # Query storage with filters
        return await self.storage.query_events(filters, limit=10000)  # High limit for candidates

    def _apply_filters(self, events: List[AuditEvent], filters: Optional[QueryFilter]) -> List[AuditEvent]:
        """Apply complex filters to events."""
        if not filters:
            return events

        return [event for event in events if filters.matches(event)]

    def _apply_time_range(self, events: List[AuditEvent], time_range: Tuple[datetime, datetime]) -> List[AuditEvent]:
        """Apply time range filter."""
        start_time, end_time = time_range
        return [event for event in events if start_time <= event.timestamp <= end_time]

    def _apply_sorting(self, events: List[AuditEvent], sort_specs: List[QuerySort]) -> List[AuditEvent]:
        """Apply sorting to events."""
        if not sort_specs:
            return events

        # Multi-level sorting
        def sort_key(event):
            keys = []
            for sort_spec in sort_specs:
                key = sort_spec.sort_key(event)
                keys.append(key if sort_spec.ascending else (-key if isinstance(key, (int, float)) else key))
            return tuple(keys)

        return sorted(events, key=sort_key)

    def _calculate_aggregations(self, events: List[AuditEvent], aggregations: List[AggregationSpec]) -> Dict[str, Any]:
        """Calculate aggregations on events."""
        results = {}

        for agg in aggregations:
            alias = agg.alias or f"{agg.function.value}_{agg.field or 'count'}"

            if agg.function == AggregationFunction.COUNT:
                results[alias] = len(events)
            elif agg.function == AggregationFunction.DISTINCT and agg.field:
                values = set()
                for event in events:
                    try:
                        value = getattr(event, agg.field, None)
                        if value is not None:
                            values.add(value)
                    except:
                        pass
                results[alias] = len(values)
            elif agg.field:
                values = []
                for event in events:
                    try:
                        value = getattr(event, agg.field, None)
                        if value is not None and isinstance(value, (int, float)):
                            values.append(value)
                    except:
                        pass

                if values:
                    if agg.function == AggregationFunction.SUM:
                        results[alias] = sum(values)
                    elif agg.function == AggregationFunction.AVG:
                        results[alias] = sum(values) / len(values)
                    elif agg.function == AggregationFunction.MIN:
                        results[alias] = min(values)
                    elif agg.function == AggregationFunction.MAX:
                        results[alias] = max(values)

        return results

    def _group_events(self, events: List[AuditEvent], group_fields: List[str]) -> Dict[str, List[AuditEvent]]:
        """Group events by specified fields."""
        groups = {}

        for event in events:
            group_key_parts = []
            for field in group_fields:
                try:
                    value = getattr(event, field, None)
                    if value is None and field in event.details:
                        value = event.details[field]
                    group_key_parts.append(str(value or 'null'))
                except:
                    group_key_parts.append('null')

            group_key = '|'.join(group_key_parts)

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(event)

        return groups

    def _generate_cache_key(self, query_spec: QuerySpec) -> str:
        """Generate cache key for query."""
        # Simple hash of query specification
        import hashlib
        import json

        # Convert query spec to serializable dict
        spec_dict = {
            'filters': str(query_spec.filters) if query_spec.filters else None,
            'sort': str(query_spec.sort) if query_spec.sort else None,
            'limit': query_spec.limit,
            'offset': query_spec.offset,
            'aggregations': str(query_spec.aggregations) if query_spec.aggregations else None,
            'group_by': str(query_spec.group_by) if query_spec.group_by else None,
            'time_range': str(query_spec.time_range) if query_spec.time_range else None
        }

        spec_str = json.dumps(spec_dict, sort_keys=True, default=str)
        return hashlib.md5(spec_str.encode()).hexdigest()

    async def execute_sql_like_query(self, query_string: str) -> QueryResult:
        """Execute SQL-like query string."""
        # Parse simple SQL-like syntax
        # This is a basic implementation - production would need proper SQL parser

        query_lower = query_string.lower().strip()

        # Parse basic SELECT queries
        if not query_lower.startswith('select'):
            raise ValueError("Only SELECT queries are supported")

        # Extract basic components (simplified parsing)
        parts = query_lower.replace('select', '').replace('from', '|').replace('where', '|').replace('order by', '|').replace('limit', '|').split('|')

        if len(parts) < 2:
            raise ValueError("Invalid query format")

        # Build query spec from parsed components
        query_spec = QuerySpec()

        # Parse WHERE clause if present
        if len(parts) > 2:
            where_clause = parts[2].strip()
            query_spec.filters = self._parse_where_clause(where_clause)

        # Parse ORDER BY if present
        if len(parts) > 3:
            order_clause = parts[3].strip()
            query_spec.sort = self._parse_order_clause(order_clause)

        # Parse LIMIT if present
        if len(parts) > 4:
            limit_clause = parts[4].strip()
            try:
                query_spec.limit = int(limit_clause)
            except ValueError:
                pass

        return await self.execute_query(query_spec)

    def _parse_where_clause(self, where_clause: str) -> QueryFilter:
        """Parse simple WHERE clause."""
        # Very basic parsing - production needs proper parser
        conditions = []

        # Split by AND/OR (simplified)
        parts = re.split(r'\s+(and|or)\s+', where_clause, flags=re.IGNORECASE)

        logic = "AND"
        i = 0
        while i < len(parts):
            part = parts[i].strip()

            if part.lower() in ['and', 'or']:
                logic = part.upper()
                i += 1
                continue

            # Parse condition like "field = value" or "field > value"
            condition_match = re.match(r'(\w+)\s*([=!<>]+|like|in)\s*(.+)', part, re.IGNORECASE)
            if condition_match:
                field, op, value = condition_match.groups()
                operator = self._parse_operator(op.strip())

                # Clean value
                value = value.strip().strip("'\"")

                # Convert value types
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)

                conditions.append(QueryCondition(field, operator, value))

            i += 1

        return QueryFilter(conditions, logic)

    def _parse_operator(self, op: str) -> QueryOperator:
        """Parse string operator to QueryOperator."""
        op_map = {
            '=': QueryOperator.EQ,
            '!=': QueryOperator.NE,
            '>': QueryOperator.GT,
            '>=': QueryOperator.GE,
            '<': QueryOperator.LT,
            '<=': QueryOperator.LE,
            'like': QueryOperator.LIKE,
            'in': QueryOperator.IN
        }
        return op_map.get(op.lower(), QueryOperator.EQ)

    def _parse_order_clause(self, order_clause: str) -> List[QuerySort]:
        """Parse ORDER BY clause."""
        sorts = []
        parts = [p.strip() for p in order_clause.split(',')]

        for part in parts:
            field_parts = part.split()
            field = field_parts[0]
            ascending = True

            if len(field_parts) > 1 and field_parts[1].lower() == 'desc':
                ascending = False

            sorts.append(QuerySort(field, ascending))

        return sorts

    async def get_query_analytics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get analytics about query patterns and performance."""
        if time_range is None:
            time_range = (datetime.now() - timedelta(days=7), datetime.now())

        # Query for events in time range
        query_spec = QuerySpec(
            time_range=time_range,
            aggregations=[
                AggregationSpec(AggregationFunction.COUNT, alias="total_events"),
                AggregationSpec(AggregationFunction.DISTINCT, "event_type", "unique_event_types"),
                AggregationSpec(AggregationFunction.DISTINCT, "user_id", "unique_users"),
                AggregationSpec(AggregationFunction.DISTINCT, "resource", "unique_resources")
            ],
            group_by=["event_type"]
        )

        result = await self.execute_query(query_spec)

        return {
            'query_performance': {
                'total_queries': self.stats['queries_executed'],
                'cache_hit_rate': self.stats['cache_hits'] / max(self.stats['queries_executed'], 1),
                'avg_execution_time_ms': self.stats['avg_execution_time']
            },
            'event_analytics': {
                'total_events': result.aggregations.get('total_events', 0),
                'unique_event_types': result.aggregations.get('unique_event_types', 0),
                'unique_users': result.aggregations.get('unique_users', 0),
                'unique_resources': result.aggregations.get('unique_resources', 0),
                'events_by_type': {k: len(v) for k, v in result.groups.items()} if result.groups else {}
            }
        }

    def clear_cache(self):
        """Clear query cache."""
        self.query_cache.clear()
        self.logger.info("Query cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get query engine statistics."""
        return {
            **self.stats,
            'cache_size': len(self.query_cache),
            'cache_ttl_seconds': self.cache_ttl_seconds
        }