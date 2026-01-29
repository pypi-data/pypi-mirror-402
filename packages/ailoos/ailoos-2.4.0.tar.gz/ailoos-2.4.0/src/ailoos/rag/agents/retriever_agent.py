"""
Retriever Agent

This module implements a retrieval agent that intelligently searches
and filters information for RAG systems.
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pybreaker import CircuitBreaker, CircuitBreakerError

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RetrieverAgent(BaseAgent):
    """
    Agent specialized in information retrieval.

    This agent analyzes queries and employs multiple retrieval strategies
    to find the most relevant information.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.retrieval_config = config.get('retrieval_config', {})
        self.vector_stores = []
        self.graph_stores = []

        # Configuración para nodos distribuidos
        self.nodes = self.retrieval_config.get('nodes', [])
        self.retry_config = self.retrieval_config.get('retry_config', {
            'max_attempts': 3,
            'min_wait': 1,
            'max_wait': 10
        })
        self.circuit_breaker_config = self.retrieval_config.get('circuit_breaker_config', {
            'fail_max': 5,
            'reset_timeout': 60,
            'expected_exception': Exception
        })

        # Inicializar circuit breakers para cada nodo
        self.circuit_breakers = {}
        for node in self.nodes:
            self.circuit_breakers[node['id']] = CircuitBreaker(
                fail_max=self.circuit_breaker_config['fail_max'],
                reset_timeout=self.circuit_breaker_config['reset_timeout'],
                expected_exception=self.circuit_breaker_config['expected_exception']
            )

    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the query and available data sources."""
        query = environment.get('query', '')
        available_sources = environment.get('data_sources', [])

        return {
            'query_type': self._classify_query(query),
            'available_sources': available_sources,
            'query_entities': self._extract_entities(query),
            'search_scope': environment.get('scope', 'broad')
        }

    def reason(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal retrieval strategy."""
        query_type = perception['query_type']
        sources = perception['available_sources']

        # Select retrieval methods
        methods = self._select_retrieval_methods(query_type, sources)

        # Plan search execution
        search_plan = self._create_search_plan(methods, perception)

        return {
            'retrieval_methods': methods,
            'search_plan': search_plan,
            'expected_results': self._estimate_result_count(perception)
        }

    def act(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the retrieval plan."""
        search_plan = reasoning['search_plan']

        results = []
        for step in search_plan:
            step_results = self._execute_search_step(step)
            results.extend(step_results)

        # Filter and rank results
        filtered_results = self._filter_and_rank_results(results)

        return {
            'retrieved_documents': filtered_results,
            'total_found': len(results),
            'filtered_count': len(filtered_results)
        }

    def _classify_query(self, query: str) -> str:
        """Classify the type of query."""
        query_lower = query.lower()

        if any(word in query_lower for word in ['what is', 'explain', 'how does']):
            return 'factual'
        elif any(word in query_lower for word in ['compare', 'versus', 'difference']):
            return 'comparative'
        elif any(word in query_lower for word in ['why', 'reason', 'cause']):
            return 'causal'
        else:
            return 'general'

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query (simplified)."""
        # Placeholder for entity extraction
        return []

    def _select_retrieval_methods(self, query_type: str, sources: List[str]) -> List[str]:
        """Select appropriate retrieval methods."""
        method_map = {
            'factual': ['vector_search', 'keyword_search'],
            'comparative': ['multi_source', 'vector_search'],
            'causal': ['graph_search', 'vector_search'],
            'general': ['vector_search']
        }

        return method_map.get(query_type, ['vector_search'])

    def _create_search_plan(self, methods: List[str], perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed search execution plan."""
        plan = []

        for method in methods:
            plan.append({
                'method': method,
                'query': perception.get('query', ''),
                'parameters': self._get_method_parameters(method)
            })

        return plan

    def _execute_search_step(self, step: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a single search step with resilient node querying."""
        method = step['method']
        query = step['query']

        results = []
        attempted_nodes = set()

        # Intentar nodos disponibles
        for node in self._select_nodes_for_method(method):
            if node['id'] in attempted_nodes:
                continue

            attempted_nodes.add(node['id'])

            try:
                node_results = self._query_node_with_resilience(node, query, method)
                results.extend(node_results)

                # Si tenemos suficientes resultados, parar
                if len(results) >= step.get('parameters', {}).get('top_k', 5):
                    break

            except (CircuitBreakerError, Exception) as e:
                logger.warning(f"Failed to query node {node['id']}: {e}")
                continue

        # Si no hay resultados, usar fallback local
        if not results:
            results = self._fallback_local_search(step)

        return results

    def _filter_and_rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and rank search results."""
        # Remove duplicates and rank by score
        seen = set()
        unique_results = []

        for result in results:
            content = result.get('content', '')
            if content not in seen:
                seen.add(content)
                unique_results.append(result)

        # Sort by score
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        return unique_results

    def _estimate_result_count(self, perception: Dict[str, Any]) -> int:
        """Estimate the number of results to expect."""
        query_type = perception.get('query_type', 'general')
        estimates = {
            'factual': 5,
            'comparative': 10,
            'causal': 3,
            'general': 7
        }

        return estimates.get(query_type, 5)

    def _get_method_parameters(self, method: str) -> Dict[str, Any]:
        """Get parameters for a specific retrieval method."""
        param_map = {
            'vector_search': {'top_k': 5, 'threshold': 0.7},
            'keyword_search': {'fuzzy': True},
            'graph_search': {'depth': 2},
            'multi_source': {'combine': 'fusion'}
        }

        return param_map.get(method, {})

    def _select_nodes_for_method(self, method: str) -> List[Dict[str, Any]]:
        """Select available nodes that support the given method."""
        available_nodes = []
        for node in self.nodes:
            if method in node.get('supported_methods', []):
                available_nodes.append(node)

        # Ordenar por prioridad o latencia (simplificado)
        return sorted(available_nodes, key=lambda x: x.get('priority', 1))

    def _query_node_with_retry(self, node: Dict[str, Any], query: str, method: str) -> List[Dict[str, Any]]:
        """Query a single node with retry logic."""
        @retry(
            stop=stop_after_attempt(self.retry_config['max_attempts']),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_config['min_wait'],
                max=self.retry_config['max_wait']
            ),
            retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, Exception))
        )
        def _do_query():
            url = f"{node['endpoint']}/search"
            payload = {
                'query': query,
                'method': method,
                'parameters': self._get_method_parameters(method)
            }

            # Usar requests para simplicidad (ya que aiohttp requiere async)
            import requests
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])

        return _do_query()

    def _query_node_with_resilience(self, node: Dict[str, Any], query: str, method: str) -> List[Dict[str, Any]]:
        """Query a node with circuit breaker protection."""
        breaker = self.circuit_breakers.get(node['id'])
        if not breaker:
            logger.error(f"No circuit breaker found for node {node['id']}")
            return []

        try:
            # Ejecutar con circuit breaker
            return breaker.call(self._query_node_with_retry, node, query, method)
        except CircuitBreakerError:
            logger.warning(f"Circuit breaker open for node {node['id']}")
            raise
        except Exception as e:
            logger.error(f"Error querying node {node['id']}: {e}")
            raise

    def _fallback_local_search(self, step: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to local search when all nodes fail."""
        logger.info("Using fallback local search")
        method = step['method']

        # Placeholder for local search implementation
        return [
            {'content': f'Fallback result from {method} (local)', 'score': 0.5, 'source': 'local_fallback'}
        ]