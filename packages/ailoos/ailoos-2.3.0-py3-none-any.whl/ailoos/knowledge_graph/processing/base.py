"""
Clases base para el sistema de Processing Layer.
Define las interfaces y tipos comunes para todos los pipelines.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures

from ...core.logging import get_logger
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector


class PipelineType(Enum):
    """Tipos de pipelines disponibles."""
    FUSION = "fusion"
    QUALITY_ASSURANCE = "quality_assurance"
    EVOLUTION = "evolution"
    ONTOLOGY = "ontology"


class PipelineStatus(Enum):
    """Estados de ejecución de pipeline."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineConfig:
    """Configuración de un pipeline."""
    pipeline_type: PipelineType
    name: str
    description: str = ""
    enabled: bool = True
    priority: int = 1
    max_concurrent_tasks: int = 4
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_type": self.pipeline_type.value,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "parameters": self.parameters
        }


@dataclass
class PipelineResult:
    """Resultado de ejecución de un pipeline."""
    pipeline_id: str
    pipeline_type: PipelineType
    status: PipelineStatus
    start_time: float
    end_time: Optional[float] = None
    execution_time_ms: Optional[float] = None
    success: bool = False
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_type": self.pipeline_type.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "warnings": self.warnings
        }


class PipelineProcessor(ABC):
    """
    Clase base abstracta para procesadores de pipeline.
    Define la interfaz común para todos los pipelines.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.logger = get_logger(f"pipeline.{config.pipeline_type.value}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> PipelineResult:
        """
        Procesar datos usando el pipeline.

        Args:
            input_data: Datos de entrada para el procesamiento
            user_id: ID del usuario que ejecuta el pipeline

        Returns:
            Resultado del procesamiento
        """
        pass

    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de entrada.

        Args:
            input_data: Datos a validar

        Returns:
            Lista de errores de validación (vacía si válido)
        """
        pass

    async def _execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Ejecutar operación con reintentos."""
        last_error = None

        for attempt in range(self.config.retry_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_attempts:
                    delay = self.config.retry_delay_seconds * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Operation failed after {self.config.retry_attempts + 1} attempts: {e}")
                    raise last_error

    async def _log_pipeline_execution(self, result: PipelineResult, user_id: Optional[str]):
        """Registrar ejecución del pipeline en auditoría."""
        await self.audit_manager.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            resource="knowledge_graph_processing",
            action=f"pipeline_{result.pipeline_type.value}_execution",
            user_id=user_id,
            details={
                "pipeline_id": result.pipeline_id,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
                "success": result.success,
                "metrics": result.metrics
            },
            success=result.success,
            processing_time_ms=result.execution_time_ms
        )

    def _record_metrics(self, result: PipelineResult):
        """Registrar métricas del pipeline."""
        self.metrics_collector.record_request(f"pipeline.{result.pipeline_type.value}")
        if result.execution_time_ms:
            self.metrics_collector.record_response_time(result.execution_time_ms)