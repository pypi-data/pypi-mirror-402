#!/usr/bin/env python3
"""
Distributed Database Queries for Ailoos
Implementa consultas a base de datos distribuidas con sharding y replicación
"""

import asyncio
import logging
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import random
from collections import defaultdict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Tipos de consultas disponibles"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    JOIN = "join"

class ConsistencyLevel(Enum):
    """Niveles de consistencia"""
    STRONG = "strong"          # Consistencia fuerte (espera a todos los nodos)
    EVENTUAL = "eventual"      # Consistencia eventual
    QUORUM = "quorum"          # Mayoría de nodos

@dataclass
class ShardInfo:
    """Información de un shard"""
    shard_id: str
    node_ids: List[str]
    primary_node: str
    range_start: str
    range_end: str
    status: str = "active"

@dataclass
class QueryPlan:
    """Plan de ejecución de consulta"""
    query_id: str
    query_type: QueryType
    shards_involved: List[str]
    nodes_involved: List[str]
    consistency_level: ConsistencyLevel
    estimated_cost: float
    execution_steps: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class QueryResult:
    """Resultado de una consulta"""
    query_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    nodes_queried: List[str] = field(default_factory=list)
    consistency_achieved: ConsistencyLevel = ConsistencyLevel.EVENTUAL

class DistributedQueryEngine:
    """
    Motor de consultas distribuidas con sharding automático y replicación
    """

    def __init__(self, node_endpoints: Dict[str, str]):
        self.node_endpoints = node_endpoints  # node_id -> endpoint_url
        self.shards: Dict[str, ShardInfo] = {}
        self.query_history: List[QueryPlan] = []
        self.active_queries: Dict[str, QueryPlan] = {}

        # Sharding configuration
        self.shard_count = 8
        self.replication_factor = 3
        self.consistency_timeout = 5.0  # seconds

        # Query optimization
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(minutes=5)

        # Load balancing
        self.node_load: Dict[str, float] = defaultdict(float)
        self.node_health: Dict[str, bool] = {}

        # Initialize shards
        self._initialize_shards()

        logger.info(f"🗄️ Distributed Query Engine initialized with {len(node_endpoints)} nodes")

    def _initialize_shards(self):
        """Initialize shard distribution"""
        nodes = list(self.node_endpoints.keys())

        if len(nodes) < self.replication_factor:
            logger.warning(f"Insufficient nodes for replication factor {self.replication_factor}")

        # Create shards with hash-based distribution
        for i in range(self.shard_count):
            shard_id = f"shard_{i:02d}"

            # Select nodes for this shard (with replication)
            available_nodes = nodes.copy()
            random.shuffle(available_nodes)

            shard_nodes = available_nodes[:min(self.replication_factor, len(available_nodes))]
            primary_node = shard_nodes[0] if shard_nodes else None

            # Calculate hash range for this shard
            range_start = f"{i/self.shard_count:.3f}"
            range_end = f"{(i+1)/self.shard_count:.3f}"

            self.shards[shard_id] = ShardInfo(
                shard_id=shard_id,
                node_ids=shard_nodes,
                primary_node=primary_node,
                range_start=range_start,
                range_end=range_end
            )

        logger.info(f"Created {len(self.shards)} shards with replication factor {self.replication_factor}")

    def _get_shard_for_key(self, key: str) -> str:
        """Get shard for a given key using consistent hashing"""
        # Simple hash-based sharding
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        shard_index = hash_value % self.shard_count
        return f"shard_{shard_index:02d}"

    def _get_shards_for_query(self, query: Dict[str, Any]) -> List[str]:
        """Determine which shards are needed for a query"""
        shards_needed = set()

        # Analyze query to determine key ranges
        if 'where' in query:
            where_clause = query['where']

            # Simple key extraction (in production, this would be more sophisticated)
            if 'id' in where_clause:
                key = str(where_clause['id'])
                shard = self._get_shard_for_key(key)
                shards_needed.add(shard)
            elif 'id_range' in where_clause:
                # Range query - might span multiple shards
                start_key = str(where_clause['id_range']['start'])
                end_key = str(where_clause['id_range']['end'])

                # For simplicity, include all shards (in production, calculate exact ranges)
                shards_needed.update(self.shards.keys())
            else:
                # Scan query - all shards
                shards_needed.update(self.shards.keys())
        else:
            # Full table scan
            shards_needed.update(self.shards.keys())

        return list(shards_needed)

    async def execute_query(self, query: Dict[str, Any],
                          consistency: ConsistencyLevel = ConsistencyLevel.QUORUM) -> QueryResult:
        """
        Execute a distributed query
        """
        query_id = f"query_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        start_time = time.time()

        try:
            # Determine query type
            query_type = self._classify_query(query)

            # Get involved shards
            shards_involved = self._get_shards_for_query(query)

            # Get involved nodes
            nodes_involved = []
            for shard_id in shards_involved:
                if shard_id in self.shards:
                    nodes_involved.extend(self.shards[shard_id].node_ids)

            nodes_involved = list(set(nodes_involved))  # Remove duplicates

            # Create query plan
            query_plan = QueryPlan(
                query_id=query_id,
                query_type=query_type,
                shards_involved=shards_involved,
                nodes_involved=nodes_involved,
                consistency_level=consistency,
                estimated_cost=self._estimate_query_cost(query, shards_involved),
                execution_steps=self._plan_query_execution(query, shards_involved, consistency)
            )

            self.active_queries[query_id] = query_plan
            self.query_history.append(query_plan)

            # Execute query
            result = await self._execute_distributed_query(query_plan, query)

            # Update execution time
            result.execution_time = time.time() - start_time
            result.consistency_achieved = consistency

            # Clean up
            if query_id in self.active_queries:
                del self.active_queries[query_id]

            logger.info(f"✅ Query {query_id} completed in {result.execution_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                query_id=query_id,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _classify_query(self, query: Dict[str, Any]) -> QueryType:
        """Classify query type"""
        if 'select' in query or 'find' in query:
            return QueryType.SELECT
        elif 'insert' in query:
            return QueryType.INSERT
        elif 'update' in query:
            return QueryType.UPDATE
        elif 'delete' in query:
            return QueryType.DELETE
        elif 'aggregate' in query or 'group_by' in query:
            return QueryType.AGGREGATE
        elif 'join' in query:
            return QueryType.JOIN
        else:
            return QueryType.SELECT  # Default

    def _estimate_query_cost(self, query: Dict[str, Any], shards: List[str]) -> float:
        """Estimate query execution cost"""
        base_cost = 1.0

        # Cost factors
        if len(shards) > 1:
            base_cost *= len(shards)  # Cross-shard queries are more expensive

        query_type = self._classify_query(query)
        if query_type in [QueryType.JOIN, QueryType.AGGREGATE]:
            base_cost *= 2.0  # Complex queries cost more

        # Data size estimation
        if 'limit' in query:
            base_cost *= min(query['limit'] / 1000, 1.0)
        else:
            base_cost *= 1.5  # Assume larger result set

        return base_cost

    def _plan_query_execution(self, query: Dict[str, Any], shards: List[str],
                            consistency: ConsistencyLevel) -> List[str]:
        """Plan query execution steps"""
        steps = []

        if len(shards) == 1:
            # Single shard query
            steps.append(f"Query single shard: {shards[0]}")
        else:
            # Multi-shard query
            steps.append(f"Coordinate query across {len(shards)} shards")
            steps.append("Gather partial results from each shard")

            if consistency == ConsistencyLevel.STRONG:
                steps.append("Wait for all nodes to acknowledge")
            elif consistency == ConsistencyLevel.QUORUM:
                steps.append("Wait for quorum acknowledgment")
            else:
                steps.append("Allow eventual consistency")

        if 'aggregate' in query or 'join' in query:
            steps.append("Perform distributed aggregation/join")

        steps.append("Return consolidated results")

        return steps

    async def _execute_distributed_query(self, query_plan: QueryPlan,
                                       original_query: Dict[str, Any]) -> QueryResult:
        """Execute query across distributed nodes"""
        query_id = query_plan.query_id

        # Check cache first
        cache_key = self._get_cache_key(original_query)
        if cache_key in self.query_cache:
            cached_result, cache_time = self.query_cache[cache_key]
            if datetime.now() - cache_time < self.cache_ttl:
                logger.info(f"Cache hit for query {query_id}")
                return cached_result

        # Execute on each involved node
        node_results = await self._query_nodes_parallel(query_plan, original_query)

        # Merge results based on consistency level
        merged_result = await self._merge_query_results(
            node_results, query_plan.consistency_level, query_plan.query_type
        )

        result = QueryResult(
            query_id=query_id,
            success=merged_result['success'],
            data=merged_result['data'],
            nodes_queried=query_plan.nodes_involved
        )

        if merged_result['success']:
            # Cache successful results
            self.query_cache[cache_key] = (result, datetime.now())

        return result

    async def _query_nodes_parallel(self, query_plan: QueryPlan,
                                  query: Dict[str, Any]) -> Dict[str, Any]:
        """Query nodes in parallel"""
        node_results = {}

        # Create tasks for each node
        tasks = []
        for node_id in query_plan.nodes_involved:
            if node_id in self.node_endpoints:
                task = self._query_single_node(node_id, query, query_plan.consistency_level)
                tasks.append((node_id, task))

        # Execute queries with timeout
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        # Process results
        for (node_id, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.warning(f"Query failed on node {node_id}: {result}")
                node_results[node_id] = {'success': False, 'error': str(result)}
            else:
                node_results[node_id] = result

        return node_results

    async def _query_single_node(self, node_id: str, query: Dict[str, Any],
                               consistency: ConsistencyLevel) -> Dict[str, Any]:
        """Query a single node"""
        endpoint = self.node_endpoints.get(node_id)
        if not endpoint:
            raise ValueError(f"No endpoint for node {node_id}")

        # Update node load
        self.node_load[node_id] += 1.0

        try:
            async with aiohttp.ClientSession() as session:
                # Add consistency requirement to query
                query_with_consistency = query.copy()
                query_with_consistency['_consistency'] = consistency.value
                query_with_consistency['_query_id'] = f"query_{int(time.time() * 1000)}"

                async with session.post(
                    f"{endpoint}/db/query",
                    json=query_with_consistency,
                    timeout=self.consistency_timeout
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        self.node_health[node_id] = True
                        return result
                    else:
                        error_text = await response.text()
                        self.node_health[node_id] = False
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}"
                        }

        except asyncio.TimeoutError:
            self.node_health[node_id] = False
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            self.node_health[node_id] = False
            return {'success': False, 'error': str(e)}
        finally:
            # Reduce load
            self.node_load[node_id] = max(0, self.node_load[node_id] - 1.0)

    async def _merge_query_results(self, node_results: Dict[str, Any],
                                 consistency: ConsistencyLevel,
                                 query_type: QueryType) -> Dict[str, Any]:
        """Merge results from multiple nodes"""
        successful_results = [
            result for result in node_results.values()
            if result.get('success', False)
        ]

        if not successful_results:
            return {
                'success': False,
                'error': 'No successful responses from any node'
            }

        # Apply consistency requirements
        if consistency == ConsistencyLevel.STRONG:
            # Need all nodes to agree
            if len(successful_results) < len(node_results):
                return {
                    'success': False,
                    'error': 'Strong consistency not achieved - not all nodes responded'
                }
        elif consistency == ConsistencyLevel.QUORUM:
            # Need majority
            quorum_size = len(node_results) // 2 + 1
            if len(successful_results) < quorum_size:
                return {
                    'success': False,
                    'error': f'Quorum not achieved - need {quorum_size}, got {len(successful_results)}'
                }

        # Merge data based on query type
        if query_type == QueryType.SELECT:
            merged_data = self._merge_select_results(successful_results)
        elif query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]:
            merged_data = self._merge_write_results(successful_results)
        elif query_type == QueryType.AGGREGATE:
            merged_data = self._merge_aggregate_results(successful_results)
        else:
            merged_data = successful_results[0]['data']  # Take first result

        return {
            'success': True,
            'data': merged_data
        }

    def _merge_select_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge SELECT query results"""
        all_data = []
        seen_ids = set()

        # Collect all unique records
        for result in results:
            data = result.get('data', [])
            if isinstance(data, list):
                for record in data:
                    record_id = record.get('id') or record.get('_id')
                    if record_id and record_id not in seen_ids:
                        all_data.append(record)
                        seen_ids.add(record_id)

        return all_data

    def _merge_write_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge write operation results"""
        # For writes, return success if majority succeeded
        success_count = sum(1 for r in results if r.get('success', False))

        return {
            'affected_rows': sum(r.get('affected_rows', 0) for r in results),
            'success_count': success_count,
            'total_nodes': len(results)
        }

    def _merge_aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge aggregate query results"""
        if not results:
            return {}

        # Combine aggregates from different shards
        combined = {}
        for result in results:
            data = result.get('data', {})
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    combined[key] = combined.get(key, 0) + value
                elif key not in combined:
                    combined[key] = value

        return combined

    def _get_cache_key(self, query: Dict[str, Any]) -> str:
        """Generate cache key for query"""
        query_str = json.dumps(query, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()

    def get_query_status(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running query"""
        if query_id in self.active_queries:
            plan = self.active_queries[query_id]
            return {
                'query_id': query_id,
                'status': 'running',
                'shards_involved': len(plan.shards_involved),
                'nodes_involved': len(plan.nodes_involved),
                'estimated_cost': plan.estimated_cost,
                'started_at': plan.created_at.isoformat()
            }

        # Check history
        for plan in self.query_history:
            if plan.query_id == query_id:
                return {
                    'query_id': query_id,
                    'status': 'completed',
                    'completed_at': plan.created_at.isoformat()
                }

        return None

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status"""
        return {
            'total_shards': len(self.shards),
            'total_nodes': len(self.node_endpoints),
            'active_queries': len(self.active_queries),
            'node_health': dict(self.node_health),
            'node_load': dict(self.node_load),
            'cache_size': len(self.query_cache),
            'query_history_size': len(self.query_history)
        }

    def rebalance_shards(self):
        """Rebalance shards across nodes"""
        logger.info("🔄 Starting shard rebalancing...")

        # Simple rebalancing: redistribute nodes across shards
        nodes = list(self.node_endpoints.keys())
        random.shuffle(nodes)

        for i, shard in enumerate(self.shards.values()):
            # Reassign nodes to shard
            start_idx = (i * self.replication_factor) % len(nodes)
            shard_nodes = []

            for j in range(self.replication_factor):
                node_idx = (start_idx + j) % len(nodes)
                shard_nodes.append(nodes[node_idx])

            shard.node_ids = shard_nodes
            if shard_nodes:
                shard.primary_node = shard_nodes[0]

        logger.info("✅ Shard rebalancing completed")

# Global query engine instance
query_engine_instance = None

def get_distributed_query_engine(node_endpoints: Dict[str, str]) -> DistributedQueryEngine:
    """Get global distributed query engine instance"""
    global query_engine_instance
    if query_engine_instance is None:
        query_engine_instance = DistributedQueryEngine(node_endpoints)
    return query_engine_instance

if __name__ == '__main__':
    # Demo
    node_endpoints = {
        'node_1': 'http://localhost:8001',
        'node_2': 'http://localhost:8002',
        'node_3': 'http://localhost:8003',
        'node_4': 'http://localhost:8004'
    }

    engine = get_distributed_query_engine(node_endpoints)

    print("🗄️ Distributed Query Engine Demo")
    print("=" * 50)

    # Show cluster status
    status = engine.get_cluster_status()
    print(f"📊 Cluster: {status['total_nodes']} nodes, {status['total_shards']} shards")

    # Example query
    sample_query = {
        'select': ['id', 'name', 'value'],
        'from': 'transactions',
        'where': {'status': 'active'},
        'limit': 100
    }

    print(f"🔍 Executing sample query: {sample_query}")

    # Note: This would normally execute against real nodes
    # For demo, we'll just show the query planning
    shards = engine._get_shards_for_query(sample_query)
    print(f"🎯 Query would involve shards: {shards}")

    print("🎉 Distributed Query Engine Demo completed!")