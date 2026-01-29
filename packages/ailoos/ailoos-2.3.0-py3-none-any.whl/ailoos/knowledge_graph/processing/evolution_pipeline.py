"""
Evolution Pipeline para evolución y actualización del conocimiento.
Implementa integración con KnowledgeEvolution para gestionar cambios temporales y ontológicos.
"""

import time
from typing import Dict, List, Any, Optional

from ...core.logging import get_logger
from ..evolution import get_knowledge_evolution, EvolutionType
from .base import PipelineProcessor, PipelineConfig, PipelineResult, PipelineStatus, PipelineType

logger = get_logger(__name__)


class EvolutionPipeline(PipelineProcessor):
    """
    Pipeline para evolución del conocimiento.
    Utiliza KnowledgeEvolution para gestionar cambios temporales, ontológicos y obsolescencia.
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.knowledge_evolution = get_knowledge_evolution()

    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> PipelineResult:
        """
        Procesar evolución del conocimiento.

        Args:
            input_data: Datos de entrada con parámetros de evolución
            user_id: ID del usuario

        Returns:
            Resultado del procesamiento de evolución
        """
        pipeline_id = f"evolution_{int(time.time())}_{hash(str(input_data)) % 10000}"
        start_time = time.time()

        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_type=PipelineType.EVOLUTION,
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
            evolution_config = self._extract_evolution_config(input_data)

            # Determinar tipo de evolución
            evolution_type_str = input_data.get('evolution_type', 'temporal')
            try:
                evolution_type = EvolutionType(evolution_type_str.upper())
            except ValueError:
                raise ValueError(f"Invalid evolution type: {evolution_type_str}")

            # Ejecutar evolución según tipo
            if evolution_type == EvolutionType.TEMPORAL:
                evolution_result = await self._process_temporal_evolution(evolution_config, user_id)
            elif evolution_type == EvolutionType.ONTOLOGICAL:
                evolution_result = await self._process_ontological_evolution(input_data, evolution_config, user_id)
            elif evolution_type == EvolutionType.RULE_BASED:
                evolution_result = await self._process_rule_based_evolution(evolution_config, user_id)
            elif evolution_type == EvolutionType.OBSOLESCENCE:
                evolution_result = await self._process_obsolescence_evolution(evolution_config, user_id)
            else:
                raise ValueError(f"Evolution type {evolution_type} not supported")

            # Preparar resultado
            result.status = PipelineStatus.COMPLETED
            result.success = True
            result.output_data = evolution_result

            # Métricas adicionales
            result.metrics = {
                'evolution_type': evolution_type.value,
                'processing_time_ms': (time.time() - start_time) * 1000
            }

            if 'changes_applied' in evolution_result:
                result.metrics['changes_applied'] = evolution_result['changes_applied']
            if 'concepts_updated' in evolution_result:
                result.metrics['concepts_updated'] = evolution_result['concepts_updated']

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.success = False
            result.error_message = f"Evolution pipeline error: {str(e)}"
            logger.error(f"Evolution pipeline failed: {e}", exc_info=True)

        finally:
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - result.start_time) * 1000

            # Logging y métricas
            await self._log_pipeline_execution(result, user_id)
            self._record_metrics(result)

        return result

    async def _process_temporal_evolution(self, config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar evolución temporal."""
        evolution_result = await self.knowledge_evolution.evolve_knowledge(
            EvolutionType.TEMPORAL,
            parameters=config,
            user_id=user_id
        )

        return {
            'evolution_id': evolution_result.get('evolution_id'),
            'changes_applied': evolution_result.get('changes_applied', 0),
            'pre_snapshot': evolution_result.get('pre_snapshot'),
            'post_snapshot': evolution_result.get('post_snapshot'),
            'processing_time_ms': evolution_result.get('processing_time_ms', 0)
        }

    async def _process_ontological_evolution(self, input_data: Dict[str, Any], config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar evolución ontológica."""
        # Si hay actualizaciones de conceptos específicas
        if 'concept_updates' in input_data:
            update_result = await self.knowledge_evolution.update_concepts(
                concept_updates=input_data['concept_updates'],
                ontology_id=input_data.get('ontology_id'),
                user_id=user_id
            )

            return {
                'operation': 'concept_updates',
                'total_updates': update_result.get('total_updates', 0),
                'successful_updates': update_result.get('successful_updates', 0),
                'failed_updates': update_result.get('failed_updates', []),
                'processing_time_ms': update_result.get('processing_time_ms', 0)
            }
        else:
            # Evolución ontológica general
            evolution_result = await self.knowledge_evolution.evolve_knowledge(
                EvolutionType.ONTOLOGICAL,
                parameters=config,
                user_id=user_id
            )

            return {
                'evolution_id': evolution_result.get('evolution_id'),
                'changes_applied': evolution_result.get('changes_applied', 0),
                'pre_snapshot': evolution_result.get('pre_snapshot'),
                'post_snapshot': evolution_result.get('post_snapshot'),
                'processing_time_ms': evolution_result.get('processing_time_ms', 0)
            }

    async def _process_rule_based_evolution(self, config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar evolución basada en reglas."""
        evolution_result = await self.knowledge_evolution.evolve_knowledge(
            EvolutionType.RULE_BASED,
            parameters=config,
            user_id=user_id
        )

        return {
            'evolution_id': evolution_result.get('evolution_id'),
            'changes_applied': evolution_result.get('changes_applied', 0),
            'pre_snapshot': evolution_result.get('pre_snapshot'),
            'post_snapshot': evolution_result.get('post_snapshot'),
            'processing_time_ms': evolution_result.get('processing_time_ms', 0)
        }

    async def _process_obsolescence_evolution(self, config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar gestión de obsolescencia."""
        evolution_result = await self.knowledge_evolution.evolve_knowledge(
            EvolutionType.OBSOLESCENCE,
            parameters=config,
            user_id=user_id
        )

        return {
            'evolution_id': evolution_result.get('evolution_id'),
            'changes_applied': evolution_result.get('changes_applied', 0),
            'pre_snapshot': evolution_result.get('pre_snapshot'),
            'post_snapshot': evolution_result.get('post_snapshot'),
            'processing_time_ms': evolution_result.get('processing_time_ms', 0)
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de entrada para evolución.

        Args:
            input_data: Datos a validar

        Returns:
            Lista de errores de validación
        """
        errors = []

        evolution_type = input_data.get('evolution_type', 'temporal')
        valid_types = ['temporal', 'ontological', 'rule_based', 'obsolescence']

        if evolution_type not in valid_types:
            errors.append(f"Invalid evolution_type '{evolution_type}'. Must be one of: {', '.join(valid_types)}")
            return errors

        # Validaciones específicas por tipo
        if evolution_type == 'ontological' and 'concept_updates' in input_data:
            concept_updates = input_data['concept_updates']
            if not isinstance(concept_updates, list):
                errors.append("'concept_updates' must be a list")
            else:
                for i, update in enumerate(concept_updates):
                    if not isinstance(update, dict):
                        errors.append(f"Concept update {i} must be a dictionary")
                        continue
                    required_fields = ['concept_uri', 'update_type']
                    for field in required_fields:
                        if field not in update:
                            errors.append(f"Concept update {i} missing required field '{field}'")

        return errors

    def _extract_evolution_config(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer configuración de evolución de los datos de entrada."""
        config = {}

        # Usar configuración del pipeline como base
        config.update(self.config.parameters)

        # Sobrescribir con parámetros específicos de la entrada
        if 'evolution_config' in input_data:
            input_config = input_data['evolution_config']
            if isinstance(input_config, dict):
                config.update(input_config)

        return config