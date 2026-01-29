"""
Sistema de Correlación de Logs y Métricas para AILOOS

Proporciona correlation IDs únicos para tracing completo de requests
a través de todos los componentes del sistema federado.
"""

import uuid
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextvars import ContextVar
import logging

logger = logging.getLogger(__name__)

# Context variables para correlation IDs
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class CorrelationTracker:
    """
    Rastreador de correlación para requests distribuidos.

    Proporciona correlation IDs únicos que siguen requests a través
    de todos los componentes: API Gateway, Federated Coordinator,
    Worker Nodes, Database, IPFS, etc.
    """

    def __init__(self):
        self.active_correlations: Dict[str, Dict[str, Any]] = {}
        self.correlation_history: List[Dict[str, Any]] = []
        self.max_history = 10000
        self._lock = threading.Lock()

        # Métricas de correlación
        self.metrics = {
            'total_correlations_created': 0,
            'active_correlations': 0,
            'completed_correlations': 0,
            'failed_correlations': 0,
            'avg_request_duration': 0.0,
            'longest_request_duration': 0.0
        }

    def create_correlation(self,
                          request_type: str = "api_request",
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Crear un nuevo correlation ID para un request.

        Args:
            request_type: Tipo de request (api_request, federated_training, etc.)
            user_id: ID del usuario si aplica
            session_id: ID de sesión si aplica
            metadata: Metadata adicional

        Returns:
            Correlation ID único
        """
        correlation_id = f"corr_{uuid.uuid4().hex[:16]}"

        correlation_data = {
            'correlation_id': correlation_id,
            'request_type': request_type,
            'user_id': user_id,
            'session_id': session_id,
            'start_time': time.time(),
            'start_datetime': datetime.now().isoformat(),
            'status': 'active',
            'components_traversed': [],
            'events': [],
            'metadata': metadata or {},
            'performance_metrics': {
                'total_duration': 0.0,
                'db_queries': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'external_calls': 0,
                'federated_nodes': 0
            }
        }

        with self._lock:
            self.active_correlations[correlation_id] = correlation_data
            self.metrics['total_correlations_created'] += 1
            self.metrics['active_correlations'] = len(self.active_correlations)

        logger.info(f"Created correlation: {correlation_id} for {request_type}")
        return correlation_id

    def add_event(self,
                  correlation_id: str,
                  event_type: str,
                  component: str,
                  message: str,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Añadir un evento al correlation tracking.

        Args:
            correlation_id: ID de correlación
            event_type: Tipo de evento (request_start, db_query, cache_hit, etc.)
            component: Componente que genera el evento
            message: Mensaje descriptivo
            metadata: Metadata adicional del evento
        """
        if correlation_id not in self.active_correlations:
            logger.warning(f"Correlation ID not found: {correlation_id}")
            return

        event = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'event_type': event_type,
            'component': component,
            'message': message,
            'metadata': metadata or {}
        }

        with self._lock:
            correlation = self.active_correlations[correlation_id]
            correlation['events'].append(event)

            # Track components traversed
            if component not in correlation['components_traversed']:
                correlation['components_traversed'].append(component)

            # Update performance metrics based on event type
            perf_metrics = correlation['performance_metrics']
            if event_type == 'db_query':
                perf_metrics['db_queries'] += 1
            elif event_type == 'cache_hit':
                perf_metrics['cache_hits'] += 1
            elif event_type == 'cache_miss':
                perf_metrics['cache_misses'] += 1
            elif event_type in ['ipfs_call', 'blockchain_call', 'external_api']:
                perf_metrics['external_calls'] += 1
            elif event_type == 'federated_node_selected':
                perf_metrics['federated_nodes'] += 1

    def complete_correlation(self,
                           correlation_id: str,
                           status: str = "completed",
                           result: Optional[Any] = None,
                           error: Optional[str] = None):
        """
        Completar un correlation tracking.

        Args:
            correlation_id: ID de correlación
            status: Estado final (completed, failed, timeout)
            result: Resultado del request si aplica
            error: Mensaje de error si aplica
        """
        if correlation_id not in self.active_correlations:
            logger.warning(f"Correlation ID not found for completion: {correlation_id}")
            return

        with self._lock:
            correlation = self.active_correlations[correlation_id]
            end_time = time.time()
            duration = end_time - correlation['start_time']

            # Update correlation data
            correlation.update({
                'end_time': end_time,
                'end_datetime': datetime.now().isoformat(),
                'status': status,
                'duration': duration,
                'result': result,
                'error': error
            })

            # Update performance metrics
            correlation['performance_metrics']['total_duration'] = duration

            # Move to history
            self.correlation_history.append(correlation.copy())
            del self.active_correlations[correlation_id]

            # Update metrics
            self.metrics['active_correlations'] = len(self.active_correlations)
            if status == 'completed':
                self.metrics['completed_correlations'] += 1
            elif status in ['failed', 'error']:
                self.metrics['failed_correlations'] += 1

            # Update average duration
            total_completed = self.metrics['completed_correlations'] + self.metrics['failed_correlations']
            if total_completed > 0:
                # Simple moving average
                self.metrics['avg_request_duration'] = (
                    (self.metrics['avg_request_duration'] * (total_completed - 1)) + duration
                ) / total_completed

            # Update longest duration
            if duration > self.metrics['longest_request_duration']:
                self.metrics['longest_request_duration'] = duration

            # Maintain history size
            if len(self.correlation_history) > self.max_history:
                self.correlation_history.pop(0)

        logger.info(f"Completed correlation: {correlation_id} ({status}) in {duration:.3f}s")

    def get_correlation_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un correlation ID."""
        with self._lock:
            if correlation_id in self.active_correlations:
                return self.active_correlations[correlation_id].copy()
            else:
                # Check history
                for correlation in self.correlation_history:
                    if correlation['correlation_id'] == correlation_id:
                        return correlation.copy()
        return None

    def get_active_correlations(self) -> List[Dict[str, Any]]:
        """Obtener todas las correlaciones activas."""
        with self._lock:
            return list(self.active_correlations.values())

    def get_correlation_history(self,
                              limit: int = 100,
                              status_filter: Optional[str] = None,
                              component_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener historial de correlaciones con filtros."""
        with self._lock:
            history = self.correlation_history.copy()

            # Apply filters
            if status_filter:
                history = [c for c in history if c.get('status') == status_filter]

            if component_filter:
                history = [c for c in history if component_filter in c.get('components_traversed', [])]

            # Sort by end time (most recent first)
            history.sort(key=lambda x: x.get('end_time', 0), reverse=True)

            return history[:limit]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento."""
        with self._lock:
            stats = self.metrics.copy()

            # Add real-time stats
            stats.update({
                'current_active_correlations': len(self.active_correlations),
                'history_size': len(self.correlation_history),
                'components_coverage': self._get_component_coverage(),
                'error_rate': self._calculate_error_rate(),
                'timestamp': datetime.now().isoformat()
            })

            return stats

    def _get_component_coverage(self) -> Dict[str, int]:
        """Obtener cobertura de componentes en correlaciones."""
        component_counts = {}
        with self._lock:
            for correlation in self.correlation_history[-1000:]:  # Last 1000 correlations
                for component in correlation.get('components_traversed', []):
                    component_counts[component] = component_counts.get(component, 0) + 1

        return dict(sorted(component_counts.items(), key=lambda x: x[1], reverse=True))

    def _calculate_error_rate(self) -> float:
        """Calcular tasa de error."""
        total = self.metrics['completed_correlations'] + self.metrics['failed_correlations']
        if total == 0:
            return 0.0
        return (self.metrics['failed_correlations'] / total) * 100

    def cleanup_old_correlations(self, max_age_seconds: int = 3600):
        """Limpiar correlaciones antiguas completadas."""
        cutoff_time = time.time() - max_age_seconds
        with self._lock:
            self.correlation_history = [
                c for c in self.correlation_history
                if c.get('end_time', 0) > cutoff_time
            ]


# Instancia global del correlation tracker
_correlation_tracker = CorrelationTracker()


def get_correlation_tracker() -> CorrelationTracker:
    """Obtener instancia global del correlation tracker."""
    return _correlation_tracker


# Context managers y decoradores para facilitar el uso

class CorrelationContext:
    """Context manager para correlation tracking."""

    def __init__(self,
                 request_type: str = "api_request",
                 user_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.request_type = request_type
        self.user_id = user_id
        self.session_id = session_id
        self.metadata = metadata or {}
        self.correlation_id = None

    async def __aenter__(self):
        self.correlation_id = _correlation_tracker.create_correlation(
            self.request_type, self.user_id, self.session_id, self.metadata
        )

        # Set context variables
        correlation_id.set(self.correlation_id)
        session_id.set(self.session_id)
        user_id.set(self.user_id)

        _correlation_tracker.add_event(
            self.correlation_id, 'request_start', 'correlation_tracker',
            f'Started {self.request_type} request'
        )

        return self.correlation_id

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        status = 'completed'
        error = None

        if exc_type:
            status = 'failed'
            error = str(exc_val)

        _correlation_tracker.complete_correlation(
            self.correlation_id, status, error=error
        )

        # Clear context variables
        correlation_id.set(None)
        session_id.set(None)
        user_id.set(None)


def correlation_event(event_type: str, component: str, message: str):
    """Decorador para añadir eventos de correlación a funciones."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            corr_id = correlation_id.get()
            if corr_id:
                _correlation_tracker.add_event(
                    corr_id, event_type, component, message,
                    {'function': func.__name__}
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Funciones de conveniencia

def get_current_correlation_id() -> Optional[str]:
    """Obtener correlation ID actual del contexto."""
    return correlation_id.get()


def add_correlation_event(event_type: str, component: str, message: str, metadata: Optional[Dict[str, Any]] = None):
    """Añadir evento a la correlación actual."""
    corr_id = correlation_id.get()
    if corr_id:
        _correlation_tracker.add_event(corr_id, event_type, component, message, metadata)


def start_correlation_tracking(request_type: str = "api_request",
                              user_id: Optional[str] = None,
                              session_id: Optional[str] = None) -> str:
    """Iniciar tracking de correlación."""
    return _correlation_tracker.create_correlation(request_type, user_id, session_id)


def end_correlation_tracking(correlation_id: str, status: str = "completed", result: Optional[Any] = None):
    """Finalizar tracking de correlación."""
    _correlation_tracker.complete_correlation(correlation_id, status, result)