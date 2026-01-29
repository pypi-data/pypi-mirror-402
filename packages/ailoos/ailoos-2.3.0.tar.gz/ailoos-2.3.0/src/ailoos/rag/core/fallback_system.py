"""
Fallback System for RAG Operations

This module provides a comprehensive fallback system for RAG operations,
ensuring reliability and graceful degradation when primary systems fail.
"""

from typing import List, Dict, Any, Optional, Callable, Iterator
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FallbackLevel(Enum):
    """Enumeration of fallback levels."""
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    CRITICAL = "critical"


class FallbackType(Enum):
    """Types of fallback operations."""
    GENERATOR = "generator"
    RETRIEVER = "retriever"
    EVALUATOR = "evaluator"
    FULL_RAG = "full_rag"


@dataclass
class FallbackResult:
    """Result of a fallback operation."""
    success: bool
    data: Any
    fallback_level: FallbackLevel
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackStrategy:
    """Configuration for a fallback strategy."""
    name: str
    fallback_type: FallbackType
    priority: int
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: float = 30.0
    conditions: List[Callable[[Exception], bool]] = field(default_factory=list)
    implementation: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)


class FallbackSystem:
    """
    Advanced fallback system for RAG operations.

    This system provides multiple levels of fallback strategies to ensure
    RAG operations continue functioning even when primary components fail.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the fallback system.

        Args:
            config (Dict[str, Any]): Configuration for fallback strategies
        """
        self.config = config
        self.strategies: Dict[FallbackType, List[FallbackStrategy]] = {}
        self.fallback_history: List[Dict[str, Any]] = []

        self._setup_default_strategies()
        self._load_custom_strategies(config)

        logger.info("Fallback system initialized")

    def _setup_default_strategies(self):
        """Setup default fallback strategies."""
        # Generator fallbacks
        self.strategies[FallbackType.GENERATOR] = [
            FallbackStrategy(
                name="mock_generator",
                fallback_type=FallbackType.GENERATOR,
                priority=1,
                conditions=[self._is_api_error, self._is_rate_limit_error],
                config={'response_templates': [
                    "Basándome en la información disponible, {query}",
                    "Según el contexto proporcionado: {query}",
                    "La respuesta es: {query}"
                ]}
            ),
            FallbackStrategy(
                name="simplified_generator",
                fallback_type=FallbackType.GENERATOR,
                priority=2,
                conditions=[self._is_complexity_error],
                config={'simplify_prompts': True, 'reduce_context': True}
            )
        ]

        # Retriever fallbacks
        self.strategies[FallbackType.RETRIEVER] = [
            FallbackStrategy(
                name="basic_retriever",
                fallback_type=FallbackType.RETRIEVER,
                priority=1,
                conditions=[self._is_index_error, self._is_connection_error],
                config={'use_basic_search': True}
            ),
            FallbackStrategy(
                name="mock_retriever",
                fallback_type=FallbackType.RETRIEVER,
                priority=2,
                conditions=[self._is_any_error],
                config={'return_empty_context': True}
            )
        ]

        # Full RAG fallbacks
        self.strategies[FallbackType.FULL_RAG] = [
            FallbackStrategy(
                name="basic_rag",
                fallback_type=FallbackType.FULL_RAG,
                priority=1,
                conditions=[self._is_system_error],
                config={'use_naive_rag': True, 'disable_advanced_features': True}
            ),
            FallbackStrategy(
                name="minimal_response",
                fallback_type=FallbackType.FULL_RAG,
                priority=2,
                conditions=[self._is_any_error],
                config={'return_static_response': True}
            )
        ]

    def _load_custom_strategies(self, config: Dict[str, Any]):
        """Load custom fallback strategies from configuration."""
        custom_strategies = config.get('custom_strategies', [])

        for strategy_config in custom_strategies:
            strategy = FallbackStrategy(**strategy_config)
            if strategy.fallback_type not in self.strategies:
                self.strategies[strategy.fallback_type] = []
            self.strategies[strategy.fallback_type].append(strategy)

        # Sort strategies by priority
        for fallback_type in self.strategies:
            self.strategies[fallback_type].sort(key=lambda s: s.priority)

    def execute_with_fallback(self, operation_type: FallbackType,
                             primary_operation: Callable,
                             *args, **kwargs) -> FallbackResult:
        """
        Execute an operation with fallback support.

        Args:
            operation_type (FallbackType): Type of operation
            primary_operation (Callable): Primary operation to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            FallbackResult: Result of the operation (primary or fallback)
        """
        start_time = time.time()

        try:
            # Try primary operation first
            result = primary_operation(*args, **kwargs)
            return FallbackResult(
                success=True,
                data=result,
                fallback_level=FallbackLevel.NONE,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            logger.warning(f"Primary {operation_type.value} operation failed: {str(e)}")

            # Try fallback strategies
            return self._execute_fallbacks(operation_type, e, args, kwargs, start_time)

    def _execute_fallbacks(self, operation_type: FallbackType, original_error: Exception,
                          args: tuple, kwargs: dict, start_time: float) -> FallbackResult:
        """Execute fallback strategies for a failed operation."""
        strategies = self.strategies.get(operation_type, [])

        for strategy in strategies:
            if not strategy.enabled:
                continue

            # Check if strategy conditions match the error
            if not self._matches_conditions(strategy, original_error):
                continue

            try:
                logger.info(f"Attempting fallback strategy: {strategy.name}")

                # Execute fallback strategy
                result = self._execute_strategy(strategy, args, kwargs)

                execution_time = time.time() - start_time

                # Record successful fallback
                self._record_fallback(strategy, True, execution_time, None)

                return FallbackResult(
                    success=True,
                    data=result,
                    fallback_level=self._get_fallback_level(strategy.priority),
                    execution_time=execution_time,
                    metadata={'strategy': strategy.name}
                )

            except Exception as fallback_error:
                logger.error(f"Fallback strategy {strategy.name} failed: {str(fallback_error)}")
                self._record_fallback(strategy, False, time.time() - start_time, str(fallback_error))
                continue

        # All fallbacks failed
        execution_time = time.time() - start_time
        self._record_fallback(None, False, execution_time, str(original_error))

        return FallbackResult(
            success=False,
            data=None,
            fallback_level=FallbackLevel.CRITICAL,
            error_message=f"All {operation_type.value} operations failed. Original error: {str(original_error)}",
            execution_time=execution_time
        )

    def _execute_strategy(self, strategy: FallbackStrategy, args: tuple, kwargs: dict) -> Any:
        """Execute a specific fallback strategy."""
        if strategy.implementation:
            return strategy.implementation(*args, **kwargs)

        # Default implementations based on strategy name
        if strategy.name == "mock_generator":
            return self._mock_generator_response(args, kwargs, strategy.config)
        elif strategy.name == "basic_retriever":
            return self._basic_retriever_response(args, kwargs, strategy.config)
        elif strategy.name == "mock_retriever":
            return self._mock_retriever_response(args, kwargs, strategy.config)
        elif strategy.name == "minimal_response":
            return self._minimal_rag_response(args, kwargs, strategy.config)
        else:
            raise NotImplementedError(f"No implementation for strategy: {strategy.name}")

    def _mock_generator_response(self, args: tuple, kwargs: dict, config: Dict[str, Any]) -> str:
        """Generate a mock response."""
        query = args[0] if args else kwargs.get('query', '')
        templates = config.get('response_templates', ["Respuesta básica para: {query}"])

        import random
        template = random.choice(templates)
        return template.format(query=query)

    def _basic_retriever_response(self, args: tuple, kwargs: dict, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return basic retrieval results."""
        query = args[0] if args else kwargs.get('query', '')
        # Return a basic context document
        return [{
            'content': f"Información básica relacionada con: {query}",
            'source': 'fallback_retriever',
            'score': 0.5
        }]

    def _mock_retriever_response(self, args: tuple, kwargs: dict, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return empty context."""
        return []

    def _minimal_rag_response(self, args: tuple, kwargs: dict, config: Dict[str, Any]) -> Dict[str, Any]:
        """Return a minimal RAG response."""
        query = args[0] if args else kwargs.get('query', '')
        return {
            'response': f"Lo siento, no pude procesar completamente tu consulta: '{query}'. Por favor, intenta reformularla.",
            'context': [],
            'metadata': {'fallback': True, 'error': 'system_unavailable'}
        }

    def _matches_conditions(self, strategy: FallbackStrategy, error: Exception) -> bool:
        """Check if error matches strategy conditions."""
        if not strategy.conditions:
            return True  # No conditions means always applicable

        return any(condition(error) for condition in strategy.conditions)

    def _is_api_error(self, error: Exception) -> bool:
        """Check if error is API-related."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['api', 'connection', 'timeout', 'network'])

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is rate limit related."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['rate limit', 'too many requests', 'quota'])

    def _is_index_error(self, error: Exception) -> bool:
        """Check if error is index/vector store related."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['index', 'vector', 'embedding', 'store'])

    def _is_connection_error(self, error: Exception) -> bool:
        """Check if error is connection related."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['connection', 'unreachable', 'timeout'])

    def _is_complexity_error(self, error: Exception) -> bool:
        """Check if error is due to complexity."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['complex', 'length', 'token limit'])

    def _is_system_error(self, error: Exception) -> bool:
        """Check if error is system-level."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in ['system', 'internal', 'unexpected'])

    def _is_any_error(self, error: Exception) -> bool:
        """Match any error (catch-all condition)."""
        return True

    def _get_fallback_level(self, priority: int) -> FallbackLevel:
        """Get fallback level based on priority."""
        if priority == 1:
            return FallbackLevel.BASIC
        elif priority == 2:
            return FallbackLevel.ADVANCED
        else:
            return FallbackLevel.CRITICAL

    def _record_fallback(self, strategy: Optional[FallbackStrategy], success: bool,
                        execution_time: float, error: Optional[str]):
        """Record a fallback attempt in history."""
        record = {
            'timestamp': time.time(),
            'strategy': strategy.name if strategy else 'none',
            'success': success,
            'execution_time': execution_time,
            'error': error
        }

        self.fallback_history.append(record)

        # Keep only recent history
        if len(self.fallback_history) > 1000:
            self.fallback_history = self.fallback_history[-1000:]

    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get statistics about fallback usage."""
        if not self.fallback_history:
            return {'total_fallbacks': 0}

        total_fallbacks = len(self.fallback_history)
        successful_fallbacks = sum(1 for r in self.fallback_history if r['success'])
        avg_execution_time = sum(r['execution_time'] for r in self.fallback_history) / total_fallbacks

        strategy_counts = {}
        for record in self.fallback_history:
            strategy = record['strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            'total_fallbacks': total_fallbacks,
            'success_rate': successful_fallbacks / total_fallbacks if total_fallbacks > 0 else 0,
            'avg_execution_time': avg_execution_time,
            'strategy_usage': strategy_counts
        }

    def reset_fallback_history(self):
        """Reset fallback history."""
        self.fallback_history.clear()
        logger.info("Fallback history reset")

    def enable_strategy(self, strategy_name: str, enabled: bool = True):
        """Enable or disable a fallback strategy."""
        for strategies in self.strategies.values():
            for strategy in strategies:
                if strategy.name == strategy_name:
                    strategy.enabled = enabled
                    logger.info(f"Strategy {strategy_name} {'enabled' if enabled else 'disabled'}")
                    return

        logger.warning(f"Strategy {strategy_name} not found")

    def add_custom_strategy(self, strategy: FallbackStrategy):
        """Add a custom fallback strategy."""
        if strategy.fallback_type not in self.strategies:
            self.strategies[strategy.fallback_type] = []

        self.strategies[strategy.fallback_type].append(strategy)
        self.strategies[strategy.fallback_type].sort(key=lambda s: s.priority)

        logger.info(f"Custom strategy {strategy.name} added")


# Convenience functions for easy fallback usage
def with_generator_fallback(primary_func: Callable) -> Callable:
    """Decorator to add generator fallback to a function."""
    def wrapper(*args, **kwargs):
        system = FallbackSystem({})
        return system.execute_with_fallback(FallbackType.GENERATOR, primary_func, *args, **kwargs)
    return wrapper


def with_retriever_fallback(primary_func: Callable) -> Callable:
    """Decorator to add retriever fallback to a function."""
    def wrapper(*args, **kwargs):
        system = FallbackSystem({})
        return system.execute_with_fallback(FallbackType.RETRIEVER, primary_func, *args, **kwargs)
    return wrapper


def with_rag_fallback(primary_func: Callable) -> Callable:
    """Decorator to add full RAG fallback to a function."""
    def wrapper(*args, **kwargs):
        system = FallbackSystem({})
        return system.execute_with_fallback(FallbackType.FULL_RAG, primary_func, *args, **kwargs)
    return wrapper