"""
Processing Layer para el Grafo de Conocimiento AILOOS.
Implementa pipelines configurables para procesamiento de conocimiento con soporte para ejecución paralela y métricas.
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
from ..fusion import get_knowledge_fusion
from ..quality import get_quality_assurance
from ..evolution import get_knowledge_evolution
from ..ontology import get_ontology_manager

# Import base classes and pipelines
from .base import (
    PipelineType,
    PipelineStatus,
    PipelineConfig,
    PipelineResult,
    PipelineProcessor
)
from .fusion_pipeline import FusionPipeline
from .qa_pipeline import QAPipeline
from .evolution_pipeline import EvolutionPipeline
from .ontology_pipeline import OntologyPipeline

logger = get_logger(__name__)


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


class PipelineManager:
    """
    Gestor central de pipelines para el procesamiento de conocimiento.
    Maneja configuración, ejecución paralela y monitoreo de pipelines.
    """

    def __init__(self):
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.logger = get_logger("pipeline_manager")

        # Configuraciones de pipelines
        self.pipeline_configs: Dict[str, PipelineConfig] = {}
        self.pipeline_instances: Dict[str, PipelineProcessor] = {}

        # Executor para ejecución paralela
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

        # Estado de ejecución
        self.active_pipelines: Dict[str, PipelineResult] = {}
        self.pipeline_history: List[PipelineResult] = []

        # Configuración por defecto
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Inicializar configuraciones por defecto de pipelines."""

        # Pipeline de fusión
        fusion_config = PipelineConfig(
            pipeline_type=PipelineType.FUSION,
            name="Knowledge Fusion Pipeline",
            description="Fusiona conocimiento de múltiples fuentes",
            parameters={
                "fusion_strategy": "union",
                "conflict_resolution": "highest_confidence",
                "min_confidence_threshold": 0.5
            }
        )
        self.pipeline_configs["fusion"] = fusion_config

        # Pipeline de QA
        qa_config = PipelineConfig(
            pipeline_type=PipelineType.QUALITY_ASSURANCE,
            name="Quality Assurance Pipeline",
            description="Valida calidad y consistencia del conocimiento",
            parameters={
                "completeness_threshold": 0.8,
                "consistency_threshold": 0.9,
                "validity_threshold": 0.95
            }
        )
        self.pipeline_configs["qa"] = qa_config

        # Pipeline de evolución
        evolution_config = PipelineConfig(
            pipeline_type=PipelineType.EVOLUTION,
            name="Knowledge Evolution Pipeline",
            description="Evoluciona y actualiza el conocimiento",
            parameters={
                "evolution_type": "temporal",
                "auto_evolution_enabled": True
            }
        )
        self.pipeline_configs["evolution"] = evolution_config

        # Pipeline de ontología
        ontology_config = PipelineConfig(
            pipeline_type=PipelineType.ONTOLOGY,
            name="Ontology Processing Pipeline",
            description="Procesa y valida ontologías",
            parameters={
                "validation_enabled": True,
                "mapping_enabled": True
            }
        )
        self.pipeline_configs["ontology"] = ontology_config

    def register_pipeline_config(self, config: PipelineConfig) -> bool:
        """
        Registrar configuración de pipeline.

        Args:
            config: Configuración del pipeline

        Returns:
            True si se registró exitosamente
        """
        if config.name in self.pipeline_configs:
            self.logger.warning(f"Pipeline config '{config.name}' already exists, overwriting")

        self.pipeline_configs[config.name] = config
        self.logger.info(f"Registered pipeline config: {config.name}")
        return True

    def get_pipeline_config(self, name: str) -> Optional[PipelineConfig]:
        """Obtener configuración de pipeline."""
        return self.pipeline_configs.get(name)

    def list_pipeline_configs(self) -> Dict[str, Dict[str, Any]]:
        """Listar todas las configuraciones de pipelines."""
        return {name: config.to_dict() for name, config in self.pipeline_configs.items()}

    async def execute_pipeline(
        self,
        pipeline_name: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        async_execution: bool = False
    ) -> Union[PipelineResult, str]:
        """
        Ejecutar un pipeline.

        Args:
            pipeline_name: Nombre del pipeline a ejecutar
            input_data: Datos de entrada
            user_id: ID del usuario
            async_execution: Si ejecutar de forma asíncrona

        Returns:
            Resultado del pipeline o ID si asíncrono
        """
        if pipeline_name not in self.pipeline_configs:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")

        config = self.pipeline_configs[pipeline_name]

        if not config.enabled:
            raise ValueError(f"Pipeline '{pipeline_name}' is disabled")

        # Crear instancia del pipeline si no existe
        if pipeline_name not in self.pipeline_instances:
            await self._create_pipeline_instance(pipeline_name, config)

        pipeline = self.pipeline_instances[pipeline_name]

        if async_execution:
            # Ejecutar de forma asíncrona
            task_id = f"pipeline_{pipeline_name}_{int(time.time())}"
            asyncio.create_task(self._execute_pipeline_async(task_id, pipeline, input_data, user_id))
            return task_id
        else:
            # Ejecutar de forma síncrona
            return await self._execute_pipeline_sync(pipeline, input_data, user_id)

    async def _create_pipeline_instance(self, name: str, config: PipelineConfig):
        """Crear instancia de pipeline."""
        if config.pipeline_type == PipelineType.FUSION:
            self.pipeline_instances[name] = FusionPipeline(config)
        elif config.pipeline_type == PipelineType.QUALITY_ASSURANCE:
            self.pipeline_instances[name] = QAPipeline(config)
        elif config.pipeline_type == PipelineType.EVOLUTION:
            self.pipeline_instances[name] = EvolutionPipeline(config)
        elif config.pipeline_type == PipelineType.ONTOLOGY:
            self.pipeline_instances[name] = OntologyPipeline(config)
        else:
            raise ValueError(f"Unknown pipeline type: {config.pipeline_type}")

    async def _execute_pipeline_sync(
        self,
        pipeline: PipelineProcessor,
        input_data: Dict[str, Any],
        user_id: Optional[str]
    ) -> PipelineResult:
        """Ejecutar pipeline de forma síncrona."""
        return await pipeline.process(input_data, user_id)

    async def _execute_pipeline_async(
        self,
        task_id: str,
        pipeline: PipelineProcessor,
        input_data: Dict[str, Any],
        user_id: Optional[str]
    ):
        """Ejecutar pipeline de forma asíncrona."""
        try:
            result = await pipeline.process(input_data, user_id)
            self.active_pipelines[task_id] = result
            self.pipeline_history.append(result)
        except Exception as e:
            self.logger.error(f"Async pipeline execution failed for {task_id}: {e}")
            # Crear resultado de error
            error_result = PipelineResult(
                pipeline_id=task_id,
                pipeline_type=pipeline.config.pipeline_type,
                status=PipelineStatus.FAILED,
                start_time=time.time(),
                end_time=time.time(),
                execution_time_ms=0.0,
                success=False,
                error_message=str(e)
            )
            self.active_pipelines[task_id] = error_result
            self.pipeline_history.append(error_result)

    async def execute_pipeline_chain(
        self,
        pipeline_names: List[str],
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        parallel_execution: bool = False
    ) -> Dict[str, PipelineResult]:
        """
        Ejecutar una cadena de pipelines.

        Args:
            pipeline_names: Lista de nombres de pipelines a ejecutar en orden
            input_data: Datos de entrada iniciales
            user_id: ID del usuario
            parallel_execution: Si ejecutar en paralelo (donde sea posible)

        Returns:
            Diccionario con resultados de cada pipeline
        """
        results = {}
        current_data = input_data

        if parallel_execution:
            # Ejecutar pipelines independientes en paralelo
            independent_pipelines = [name for name in pipeline_names if self._is_independent_pipeline(name)]

            if independent_pipelines:
                # Ejecutar en paralelo
                parallel_results = await asyncio.gather(*[
                    self.execute_pipeline(name, current_data, user_id)
                    for name in independent_pipelines
                ])

                for name, result in zip(independent_pipelines, parallel_results):
                    results[name] = result
                    # Combinar outputs para siguientes pipelines
                    if result.success and result.output_data:
                        current_data.update(result.output_data)

                # Remover de la lista
                pipeline_names = [name for name in pipeline_names if name not in independent_pipelines]

        # Ejecutar pipelines restantes en secuencia
        for pipeline_name in pipeline_names:
            result = await self.execute_pipeline(pipeline_name, current_data, user_id)
            results[pipeline_name] = result

            if result.success and result.output_data:
                current_data.update(result.output_data)
            elif not result.success:
                # Detener cadena si un pipeline falla
                break

        return results

    def _is_independent_pipeline(self, pipeline_name: str) -> bool:
        """Verificar si un pipeline puede ejecutarse independientemente."""
        # Por simplicidad, considerar que QA y Ontology pueden ser independientes
        config = self.pipeline_configs.get(pipeline_name)
        if config:
            return config.pipeline_type in [PipelineType.QUALITY_ASSURANCE, PipelineType.ONTOLOGY]
        return False

    def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineResult]:
        """Obtener estado de un pipeline en ejecución."""
        return self.active_pipelines.get(pipeline_id)

    def get_pipeline_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de ejecuciones de pipelines."""
        return [result.to_dict() for result in self.pipeline_history[-limit:]]

    def get_active_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Obtener pipelines actualmente en ejecución."""
        return {pid: result.to_dict() for pid, result in self.active_pipelines.items()}

    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancelar ejecución de un pipeline."""
        # Implementación simplificada - en producción necesitaría manejo de cancellation tokens
        if pipeline_id in self.active_pipelines:
            result = self.active_pipelines[pipeline_id]
            result.status = PipelineStatus.CANCELLED
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - result.start_time) * 1000
            self.logger.info(f"Cancelled pipeline: {pipeline_id}")
            return True
        return False

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Obtener métricas generales de pipelines."""
        total_executions = len(self.pipeline_history)
        successful_executions = len([r for r in self.pipeline_history if r.success])
        failed_executions = total_executions - successful_executions

        if total_executions > 0:
            success_rate = successful_executions / total_executions
        else:
            success_rate = 0.0

        # Calcular tiempos promedio por tipo
        execution_times_by_type = {}
        for result in self.pipeline_history:
            if result.execution_time_ms:
                ptype = result.pipeline_type.value
                if ptype not in execution_times_by_type:
                    execution_times_by_type[ptype] = []
                execution_times_by_type[ptype].append(result.execution_time_ms)

        avg_times = {}
        for ptype, times in execution_times_by_type.items():
            avg_times[ptype] = sum(times) / len(times) if times else 0.0

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": success_rate,
            "active_pipelines": len(self.active_pipelines),
            "average_execution_times_ms": avg_times
        }


# Instancia global del gestor de pipelines
_pipeline_manager = None

def get_pipeline_manager() -> PipelineManager:
    """Obtener instancia global del gestor de pipelines."""
    global _pipeline_manager
    if _pipeline_manager is None:
        _pipeline_manager = PipelineManager()
    return _pipeline_manager

# Exportar clases principales
__all__ = [
    'PipelineType',
    'PipelineStatus',
    'PipelineConfig',
    'PipelineResult',
    'PipelineProcessor',
    'PipelineManager',
    'get_pipeline_manager'
]