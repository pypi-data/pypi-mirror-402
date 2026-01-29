"""
Quality Assurance Pipeline para validación y aseguramiento de calidad.
Implementa integración con QualityAssurance para validar conocimiento.
"""

import time
from typing import Dict, List, Any, Optional

from ...core.logging import get_logger
from ..quality import get_quality_assurance, QualityMetrics, QualityReport
from .base import PipelineProcessor, PipelineConfig, PipelineResult, PipelineStatus, PipelineType

logger = get_logger(__name__)


class QAPipeline(PipelineProcessor):
    """
    Pipeline para Quality Assurance del conocimiento.
    Utiliza QualityAssurance para validar calidad, consistencia y detectar inconsistencias.
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.quality_assurance = get_quality_assurance()

    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> PipelineResult:
        """
        Procesar validación de calidad.

        Args:
            input_data: Datos de entrada con triples a validar
            user_id: ID del usuario

        Returns:
            Resultado del procesamiento de QA
        """
        pipeline_id = f"qa_{int(time.time())}_{hash(str(input_data)) % 10000}"
        start_time = time.time()

        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_type=PipelineType.QUALITY_ASSURANCE,
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
            qa_config = self._extract_qa_config(input_data)

            # Determinar tipo de operación
            operation = input_data.get('operation', 'validate_quality')

            if operation == 'validate_quality':
                # Validación básica de calidad
                metrics = await self.quality_assurance.validate_quality(
                    triples=input_data.get('triples'),
                    ontology_ids=input_data.get('ontology_ids'),
                    rules_to_apply=input_data.get('rules_to_apply'),
                    user_id=user_id
                )

                result.output_data = {
                    'operation': 'validate_quality',
                    'metrics': metrics.to_dict(),
                    'overall_score': metrics.overall_score,
                    'issues_count': metrics.issues_count
                }

            elif operation == 'detect_inconsistencies':
                # Detección de inconsistencias
                issues = await self.quality_assurance.detect_inconsistencies(
                    triples=input_data.get('triples'),
                    ontology_ids=input_data.get('ontology_ids'),
                    user_id=user_id
                )

                result.output_data = {
                    'operation': 'detect_inconsistencies',
                    'issues_count': len(issues),
                    'issues': [issue.to_dict() for issue in issues]
                }

            elif operation == 'generate_report':
                # Generar reporte completo
                report = await self.quality_assurance.generate_report(
                    triples=input_data.get('triples'),
                    ontology_ids=input_data.get('ontology_ids'),
                    include_inconsistencies=qa_config.get('include_inconsistencies', True),
                    user_id=user_id
                )

                result.output_data = {
                    'operation': 'generate_report',
                    'report': report.to_dict(),
                    'overall_score': report.metrics.overall_score,
                    'issues_count': len(report.issues)
                }

            else:
                raise ValueError(f"Unknown QA operation: {operation}")

            # Preparar resultado
            result.status = PipelineStatus.COMPLETED
            result.success = True

            # Métricas adicionales
            result.metrics = {
                'operation': operation,
                'triples_processed': len(input_data.get('triples', [])),
                'ontologies_used': len(input_data.get('ontology_ids', [])),
                'processing_time_ms': (time.time() - start_time) * 1000
            }

            # Agregar información específica según operación
            if operation == 'validate_quality' and 'metrics' in locals():
                result.metrics.update({
                    'completeness_score': metrics.completeness_score,
                    'consistency_score': metrics.consistency_score,
                    'accuracy_score': metrics.accuracy_score,
                    'validity_score': metrics.validity_score
                })

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.success = False
            result.error_message = f"QA pipeline error: {str(e)}"
            logger.error(f"QA pipeline failed: {e}", exc_info=True)

        finally:
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - result.start_time) * 1000

            # Logging y métricas
            await self._log_pipeline_execution(result, user_id)
            self._record_metrics(result)

        return result

    async def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de entrada para QA.

        Args:
            input_data: Datos a validar

        Returns:
            Lista de errores de validación
        """
        errors = []

        operation = input_data.get('operation', 'validate_quality')
        valid_operations = ['validate_quality', 'detect_inconsistencies', 'generate_report']

        if operation not in valid_operations:
            errors.append(f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}")
            return errors

        # Validar triples si se proporcionan
        if 'triples' in input_data:
            triples = input_data['triples']
            if not isinstance(triples, list):
                errors.append("'triples' must be a list")
            else:
                # Validar estructura básica de triples
                for i, triple in enumerate(triples):
                    if not isinstance(triple, dict):
                        errors.append(f"Triple {i} must be a dictionary")
                        continue
                    required_fields = ['subject', 'predicate', 'object']
                    for field in required_fields:
                        if field not in triple:
                            errors.append(f"Triple {i} missing required field '{field}'")

        # Validar ontology_ids si se proporcionan
        if 'ontology_ids' in input_data:
            ontology_ids = input_data['ontology_ids']
            if not isinstance(ontology_ids, list):
                errors.append("'ontology_ids' must be a list")
            else:
                for i, oid in enumerate(ontology_ids):
                    if not isinstance(oid, str):
                        errors.append(f"Ontology ID {i} must be a string")

        return errors

    def _extract_qa_config(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer configuración de QA de los datos de entrada."""
        config = {}

        # Usar configuración del pipeline como base
        config.update(self.config.parameters)

        # Sobrescribir con parámetros específicos de la entrada
        if 'qa_config' in input_data:
            input_config = input_data['qa_config']
            if isinstance(input_config, dict):
                config.update(input_config)

        return config