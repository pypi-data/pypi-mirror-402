"""
A/B Testing System for RAG Components

This module provides comprehensive A/B testing capabilities for RAG systems,
enabling comparison of different configurations, models, and strategies.
"""

from typing import Dict, Any, List, Optional, Callable
import logging
import random
import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ABTestVariant:
    """Configuration for an A/B test variant."""
    name: str
    config: Dict[str, Any]
    weight: float = 1.0  # Relative weight for random selection
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTest:
    """A/B test configuration and state."""
    name: str
    component: str  # 'generator', 'retriever', 'evaluator'
    variants: List[ABTestVariant]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    enabled: bool = True
    target_metric: str = 'overall_score'
    min_samples: int = 100
    confidence_threshold: float = 0.95

    # Runtime state
    results: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    assignments: Dict[str, str] = field(default_factory=dict)  # user/query -> variant

    def is_active(self) -> bool:
        """Check if the test is currently active."""
        if not self.enabled:
            return False

        now = datetime.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False

        return True

    def assign_variant(self, user_id: str) -> str:
        """Assign a variant to a user based on consistent hashing."""
        if user_id in self.assignments:
            return self.assignments[user_id]

        # Use consistent hashing for variant assignment
        hash_value = int(hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest()[:8], 16)
        total_weight = sum(v.weight for v in self.variants if v.enabled)
        cumulative_weight = 0

        for variant in self.variants:
            if not variant.enabled:
                continue
            cumulative_weight += variant.weight
            if hash_value % int(total_weight * 1000) < cumulative_weight * 1000:
                self.assignments[user_id] = variant.name
                return variant.name

        # Fallback to first enabled variant
        enabled_variants = [v for v in self.variants if v.enabled]
        if enabled_variants:
            variant_name = enabled_variants[0].name
            self.assignments[user_id] = variant_name
            return variant_name

        return self.variants[0].name if self.variants else 'default'

    def record_result(self, user_id: str, variant: str, metrics: Dict[str, Any]):
        """Record test results for analysis."""
        if variant not in self.results:
            self.results[variant] = []

        result = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }

        self.results[variant].append(result)

        # Keep only recent results
        if len(self.results[variant]) > 10000:
            self.results[variant] = self.results[variant][-5000:]

    def get_variant_config(self, variant_name: str) -> Dict[str, Any]:
        """Get configuration for a specific variant."""
        for variant in self.variants:
            if variant.name == variant_name:
                return variant.config
        return {}

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze A/B test results and determine winner."""
        if not self.is_active() or len(self.assignments) < self.min_samples:
            return {'status': 'insufficient_data'}

        analysis = {
            'test_name': self.name,
            'total_samples': len(self.assignments),
            'variant_performance': {},
            'winner': None,
            'confidence': 0.0,
            'recommendation': 'continue_testing'
        }

        # Calculate performance for each variant
        for variant_name, results in self.results.items():
            if not results:
                continue

            metrics = [r['metrics'].get(self.target_metric, 0) for r in results]
            avg_score = sum(metrics) / len(metrics) if metrics else 0

            analysis['variant_performance'][variant_name] = {
                'sample_size': len(results),
                'avg_score': avg_score,
                'min_score': min(metrics) if metrics else 0,
                'max_score': max(metrics) if metrics else 0
            }

        # Simple winner determination (could be enhanced with statistical tests)
        if len(analysis['variant_performance']) >= 2:
            best_variant = max(analysis['variant_performance'].items(),
                             key=lambda x: x[1]['avg_score'])
            analysis['winner'] = best_variant[0]

            # Check if we have enough confidence (simple threshold)
            best_score = best_variant[1]['avg_score']
            others = [v for v in analysis['variant_performance'].values() if v != best_variant[1]]
            if others:
                avg_other = sum(o['avg_score'] for o in others) / len(others)
                improvement = (best_score - avg_other) / avg_other if avg_other > 0 else 0

                if improvement > 0.05 and len(self.assignments) >= self.min_samples:
                    analysis['recommendation'] = 'implement_winner'
                    analysis['confidence'] = min(0.95, improvement * 20)  # Rough confidence estimate

        return analysis


class ABTestingManager:
    """
    Manager for multiple A/B tests across RAG components.

    This class coordinates A/B testing across different RAG components
    and provides centralized result analysis.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize A/B testing manager.

        Args:
            config (Dict[str, Any]): Configuration for A/B tests
        """
        self.config = config
        self.tests: Dict[str, ABTest] = {}
        self.global_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)

        self._load_tests(config)

        logger.info(f"A/B Testing Manager initialized with {len(self.tests)} tests")

    def _load_tests(self, config: Dict[str, Any]):
        """Load A/B tests from configuration."""
        test_configs = config.get('tests', [])

        for test_config in test_configs:
            test = ABTest(**test_config)
            self.tests[test.name] = test

    def get_variant(self, test_name: str, user_id: str, component: str) -> str:
        """
        Get the assigned variant for a user in a specific test.

        Args:
            test_name (str): Name of the A/B test
            user_id (str): Unique user identifier
            component (str): Component being tested

        Returns:
            str: Assigned variant name
        """
        if test_name not in self.tests:
            return 'default'

        test = self.tests[test_name]
        if not test.is_active():
            return 'default'

        # Check if user is already assigned to this component
        if user_id in self.global_assignments and component in self.global_assignments[user_id]:
            return self.global_assignments[user_id][component]

        # Assign variant
        variant = test.assign_variant(user_id)
        self.global_assignments[user_id][component] = variant

        return variant

    def get_variant_config(self, test_name: str, variant_name: str) -> Dict[str, Any]:
        """Get configuration for a test variant."""
        if test_name in self.tests:
            return self.tests[test_name].get_variant_config(variant_name)
        return {}

    def record_result(self, test_name: str, user_id: str, variant: str,
                     component: str, metrics: Dict[str, Any]):
        """Record test results."""
        if test_name in self.tests:
            self.tests[test_name].record_result(user_id, variant, metrics)

            # Also record in global assignments for tracking
            if user_id not in self.global_assignments:
                self.global_assignments[user_id] = {}
            self.global_assignments[user_id][component] = variant

    def get_test_analysis(self, test_name: str) -> Dict[str, Any]:
        """Get analysis for a specific test."""
        if test_name in self.tests:
            return self.tests[test_name].analyze_results()
        return {'error': 'test_not_found'}

    def get_all_analyses(self) -> Dict[str, Dict[str, Any]]:
        """Get analysis for all active tests."""
        analyses = {}
        for test_name, test in self.tests.items():
            if test.is_active():
                analyses[test_name] = test.analyze_results()
        return analyses

    def create_test(self, test_config: Dict[str, Any]) -> bool:
        """Create a new A/B test."""
        try:
            test = ABTest(**test_config)
            self.tests[test.name] = test
            logger.info(f"Created A/B test: {test.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create A/B test: {str(e)}")
            return False

    def stop_test(self, test_name: str) -> bool:
        """Stop an A/B test."""
        if test_name in self.tests:
            self.tests[test_name].enabled = False
            logger.info(f"Stopped A/B test: {test_name}")
            return True
        return False

    def get_active_tests(self) -> List[str]:
        """Get list of active test names."""
        return [name for name, test in self.tests.items() if test.is_active()]

    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all tests."""
        return {
            'total_tests': len(self.tests),
            'active_tests': len(self.get_active_tests()),
            'total_assignments': len(self.global_assignments),
            'test_details': {
                name: {
                    'component': test.component,
                    'variants': len(test.variants),
                    'samples': len(test.assignments),
                    'active': test.is_active()
                }
                for name, test in self.tests.items()
            }
        }


# Convenience functions for easy A/B testing integration
def create_generator_ab_test() -> Dict[str, Any]:
    """Create a standard A/B test for generators."""
    return {
        'name': 'generator_temperature_test',
        'component': 'generator',
        'variants': [
            ABTestVariant(name='conservative', config={'temperature': 0.3}, weight=1.0),
            ABTestVariant(name='balanced', config={'temperature': 0.7}, weight=1.0),
            ABTestVariant(name='creative', config={'temperature': 0.9}, weight=1.0)
        ],
        'target_metric': 'coherence',
        'min_samples': 200
    }


def create_retriever_ab_test() -> Dict[str, Any]:
    """Create a standard A/B test for retrievers."""
    return {
        'name': 'retriever_top_k_test',
        'component': 'retriever',
        'variants': [
            ABTestVariant(name='minimal', config={'top_k': 3}, weight=1.0),
            ABTestVariant(name='standard', config={'top_k': 5}, weight=1.0),
            ABTestVariant(name='extensive', config={'top_k': 10}, weight=1.0)
        ],
        'target_metric': 'context_relevance',
        'min_samples': 150
    }


# Global instance
ab_testing_manager = None

def get_ab_testing_manager(config: Optional[Dict[str, Any]] = None) -> ABTestingManager:
    """Get or create global A/B testing manager instance."""
    global ab_testing_manager
    if ab_testing_manager is None and config:
        ab_testing_manager = ABTestingManager(config)
    return ab_testing_manager