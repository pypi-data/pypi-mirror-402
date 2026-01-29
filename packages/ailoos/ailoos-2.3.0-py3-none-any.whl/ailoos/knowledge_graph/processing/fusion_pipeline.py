"""
Fusion Pipeline para procesamiento de fusión de conocimiento.
Implementa integración con KnowledgeFusion para combinar conocimiento de múltiples fuentes.
"""

import time
from typing import Dict, List, Any, Optional

from ...core.logging import get_logger
from ..fusion import get_knowledge_fusion, FusionResult
from .base import PipelineProcessor, PipelineConfig, PipelineResult, PipelineStatus, PipelineType

logger = get_logger(__name__)


class FusionPipeline(PipelineProcessor):
    """
    Pipeline para fusión de conocimiento de múltiples fuentes.
    Utiliza KnowledgeFusion para combinar y resolver conflictos.
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.knowledge_fusion = get_knowledge_fusion()

    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> PipelineResult:
        """
        Procesar fusión de conocimiento.

        Args:
            input_data: Datos de entrada con fuentes a fusionar
            user_id: ID del usuario

        Returns:
            Resultado del procesamiento de fusión
        """
        pipeline_id = f"fusion_{int(time.time())}_{hash(str(input_data)) % 10000}"
        start_time = time.time()

        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_type=PipelineType.FUSION,
            status=PipelineStatus.RUNNING,
            start_time=start_time
        )

        try:
            # Validar entrada
            validation_errors = await self.validate_input(input_data)
            if validation_errors:
                result.status = PipelineStatus.FAILED
                result.error_message = f"Validation errors: {', '.join(validation_errors)}"
                result.end_time = time.time()
                result.execution_time_ms = (result.end_time - result.start_time) * 1000
                await self._log_pipeline_execution(result, user_id)
                self._record_metrics(result)
                return result

            # Extraer parámetros de configuración
            fusion_config = self._extract_fusion_config(input_data)

            # Ejecutar fusión
            fusion_result = await self.knowledge_fusion.fuse_sources(
                sources=input_data.get('sources', []),
                fusion_config=fusion_config,
                user_id=user_id
            )

            # Preparar resultado
            result.status = PipelineStatus.COMPLETED if fusion_result.success else PipelineStatus.FAILED
            result.success = fusion_result.success
            result.output_data = {
                'fusion_id': fusion_result.fusion_id,
                'fused_triples': fusion_result.fused_triples,
                'conflicts_resolved': fusion_result.conflicts_resolved,
                'inconsistencies_detected': fusion_result.inconsistencies_detected,
                'processing_time_ms': fusion_result.processing_time_ms,
                'strategy_used': fusion_result.strategy_used.value if fusion_result.strategy_used else None,
                'sources_used': fusion_result.sources_used
            }

            if not fusion_result.success:
                result.error_message = f"Fusion failed: {', '.join(fusion_result.errors)}"
                result.warnings = fusion_result.warnings

            # Métricas adicionales
            result.metrics = {
                'sources_count': len(input_data.get('sources', [])),
                'fusion_strategy': fusion_config.get('fusion_strategy', 'union'),
                'conflict_resolution': fusion_config.get('conflict_resolution', 'highest_confidence'),
                'triples_processed': fusion_result.fused_triples,
                'conflicts_handled': fusion_result.conflicts_resolved
            }

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.success = False
            result.error_message = f"Fusion pipeline error: {str(e)}"
            logger.error(f"Fusion pipeline failed: {e}", exc_info=True)

        finally:
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - result.start_time) * 1000

            # Logging y métricas
            await self._log_pipeline_execution(result, user_id)
            self._record_metrics(result)

        return result

    async def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de entrada para fusión.

        Args:
            input_data: Datos a validar

        Returns:
            Lista de errores de validación
        """
        errors = []

        if 'sources' not in input_data:
            errors.append("Missing 'sources' field in input data")
            return errors

        sources = input_data['sources']
        if not isinstance(sources, list):
            errors.append("'sources' must be a list")
            return errors

        if len(sources) < 2:
            errors.append("At least 2 sources required for fusion")
            return errors

        # Validar estructura de cada fuente
        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"Source {i} must be a dictionary")
                continue

            if 'id' not in source:
                errors.append(f"Source {i} missing 'id' field")
            if 'data' not in source and 'format' not in source:
                errors.append(f"Source {i} missing 'data' or 'format' field")

        return errors

    def _extract_fusion_config(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer configuración de fusión de los datos de entrada."""
        config = {}

        # Usar configuración del pipeline como base
        config.update(self.config.parameters)

        # Sobrescribir con parámetros específicos de la entrada
        if 'fusion_config' in input_data:
            input_config = input_data['fusion_config']
            if isinstance(input_config, dict):
                config.update(input_config)

        return config