"""
Planner Agent

This module implements a planning agent that creates execution strategies
for complex RAG operations.
"""

from typing import List, Dict, Any, Optional
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Agent specialized in planning RAG operations.

    This agent analyzes queries and creates detailed execution plans
    for optimal RAG performance.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.planning_config = config.get('planning_config', {})

    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the query and available resources."""
        query = environment.get('query', '')
        available_resources = environment.get('resources', {})

        return {
            'query_complexity': self._assess_complexity(query),
            'available_techniques': available_resources.get('techniques', []),
            'data_sources': available_resources.get('data_sources', []),
            'constraints': environment.get('constraints', {})
        }

    def reason(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan based on perception."""
        complexity = perception['query_complexity']
        techniques = perception['available_techniques']

        # Select appropriate techniques
        selected_techniques = self._select_techniques(complexity, techniques)

        # Create execution steps
        steps = self._create_execution_steps(selected_techniques, perception)

        return {
            'selected_techniques': selected_techniques,
            'execution_steps': steps,
            'estimated_complexity': complexity
        }

    def act(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planning action."""
        plan = {
            'techniques': reasoning['selected_techniques'],
            'steps': reasoning['execution_steps'],
            'metadata': {
                'planner': self.__class__.__name__,
                'complexity': reasoning['estimated_complexity']
            }
        }

        return {'plan': plan}

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity."""
        words = len(query.split())
        if words <= 3:
            return 'simple'
        elif words <= 10:
            return 'medium'
        else:
            return 'complex'

    def _select_techniques(self, complexity: str, available: List[str]) -> List[str]:
        """Select appropriate techniques based on complexity."""
        technique_map = {
            'simple': ['NaiveRAG'],
            'medium': ['CorrectiveRAG', 'ContextualRAG'],
            'complex': ['AgenticRAG', 'HybridRAG']
        }

        preferred = technique_map.get(complexity, ['NaiveRAG'])
        return [t for t in preferred if t in available] or ['NaiveRAG']

    def _create_execution_steps(self, techniques: List[str], perception: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed execution steps."""
        steps = []
        for i, technique in enumerate(techniques):
            steps.append({
                'step': i + 1,
                'technique': technique,
                'action': 'execute_rag',
                'parameters': {}
            })

        return steps