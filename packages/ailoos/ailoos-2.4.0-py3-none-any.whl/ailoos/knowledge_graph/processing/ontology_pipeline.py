"""
Ontology Pipeline para procesamiento de ontologías.
Implementa integración con OntologyManager para carga, validación y mapeo de ontologías.
"""

import time
from typing import Dict, List, Any, Optional

from ...core.logging import get_logger
from ..ontology import get_ontology_manager, OntologyFormat
from .base import PipelineProcessor, PipelineConfig, PipelineResult, PipelineStatus, PipelineType

logger = get_logger(__name__)


class OntologyPipeline(PipelineProcessor):
    """
    Pipeline para procesamiento de ontologías.
    Utiliza OntologyManager para cargar, validar y mapear ontologías.
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.ontology_manager = get_ontology_manager()

    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> PipelineResult:
        """
        Procesar operaciones de ontología.

        Args:
            input_data: Datos de entrada con parámetros de ontología
            user_id: ID del usuario

        Returns:
            Resultado del procesamiento de ontología
        """
        pipeline_id = f"ontology_{int(time.time())}_{hash(str(input_data)) % 10000}"
        start_time = time.time()

        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_type=PipelineType.ONTOLOGY,
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
            ontology_config = self._extract_ontology_config(input_data)

            # Determinar tipo de operación
            operation = input_data.get('operation', 'load_ontology')

            if operation == 'load_ontology':
                # Cargar ontología
                load_result = await self._process_load_ontology(input_data, ontology_config, user_id)
                result.output_data = load_result

            elif operation == 'validate_schema':
                # Validar esquema
                validation_result = await self._process_validate_schema(input_data, ontology_config, user_id)
                result.output_data = validation_result

            elif operation == 'evolve_concept':
                # Evolucionar concepto
                evolution_result = await self._process_evolve_concept(input_data, ontology_config, user_id)
                result.output_data = evolution_result

            elif operation == 'map_concepts':
                # Mapear conceptos
                mapping_result = await self._process_map_concepts(input_data, ontology_config, user_id)
                result.output_data = mapping_result

            else:
                raise ValueError(f"Unknown ontology operation: {operation}")

            # Preparar resultado
            result.status = PipelineStatus.COMPLETED
            result.success = True

            # Métricas adicionales
            result.metrics = {
                'operation': operation,
                'processing_time_ms': (time.time() - start_time) * 1000
            }

            # Agregar métricas específicas según operación
            if operation == 'load_ontology' and result.output_data.get('success'):
                result.metrics['triples_loaded'] = result.output_data.get('triples_loaded', 0)
            elif operation == 'validate_schema':
                result.metrics['validation_passed'] = result.output_data.get('valid', False)
            elif operation == 'map_concepts':
                result.metrics['mappings_found'] = result.output_data.get('mappings_found', 0)

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.success = False
            result.error_message = f"Ontology pipeline error: {str(e)}"
            logger.error(f"Ontology pipeline failed: {e}", exc_info=True)

        finally:
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - result.start_time) * 1000

            # Logging y métricas
            await self._log_pipeline_execution(result, user_id)
            self._record_metrics(result)

        return result

    async def _process_load_ontology(self, input_data: Dict[str, Any], config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar carga de ontología."""
        source = input_data.get('source')
        ontology_id = input_data.get('ontology_id')
        format_type_str = input_data.get('format', 'owl')

        # Convertir formato a enum
        try:
            format_type = OntologyFormat(format_type_str.upper())
        except ValueError:
            raise ValueError(f"Invalid ontology format: {format_type_str}")

        # Cargar ontología
        success = await self.ontology_manager.load_ontology(
            source=source,
            ontology_id=ontology_id,
            format_type=format_type,
            user_id=user_id
        )

        # Obtener metadata
        metadata = self.ontology_manager.get_loaded_ontologies().get(ontology_id, {})

        return {
            'operation': 'load_ontology',
            'success': success,
            'ontology_id': ontology_id,
            'format': format_type.value,
            'triples_loaded': metadata.get('triples_count', 0),
            'source': str(source) if hasattr(source, '__str__') else 'string'
        }

    async def _process_validate_schema(self, input_data: Dict[str, Any], config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar validación de esquema."""
        data = input_data.get('data')
        ontology_ids = input_data.get('ontology_ids', [])

        # Validar esquema
        validation_result = await self.ontology_manager.validate_schema(
            data=data,
            ontology_ids=ontology_ids,
            user_id=user_id
        )

        return {
            'operation': 'validate_schema',
            'valid': validation_result.get('valid', False),
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', []),
            'checked_triples': validation_result.get('checked_triples', 0),
            'ontologies_used': validation_result.get('ontologies_used', [])
        }

    async def _process_evolve_concept(self, input_data: Dict[str, Any], config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar evolución de concepto."""
        ontology_id = input_data.get('ontology_id')
        concept_uri = input_data.get('concept_uri')
        changes = input_data.get('changes', {})

        # Evolucionar concepto
        success = await self.ontology_manager.evolve_concept(
            ontology_id=ontology_id,
            concept_uri=concept_uri,
            changes=changes,
            user_id=user_id
        )

        return {
            'operation': 'evolve_concept',
            'success': success,
            'ontology_id': ontology_id,
            'concept_uri': concept_uri,
            'changes_applied': bool(success)
        }

    async def _process_map_concepts(self, input_data: Dict[str, Any], config: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Procesar mapeo de conceptos."""
        source_ontology_id = input_data.get('source_ontology_id')
        target_ontology_id = input_data.get('target_ontology_id')
        mapping_rules = input_data.get('mapping_rules')

        # Mapear conceptos
        mapping_result = await self.ontology_manager.map_concepts(
            source_ontology_id=source_ontology_id,
            target_ontology_id=target_ontology_id,
            mapping_rules=mapping_rules,
            user_id=user_id
        )

        return {
            'operation': 'map_concepts',
            'mappings_found': mapping_result.get('mappings_found', 0),
            'mappings': mapping_result.get('mappings', []),
            'source_ontology': mapping_result.get('source_ontology'),
            'target_ontology': mapping_result.get('target_ontology')
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de entrada para ontología.

        Args:
            input_data: Datos a validar

        Returns:
            Lista de errores de validación
        """
        errors = []

        operation = input_data.get('operation', 'load_ontology')
        valid_operations = ['load_ontology', 'validate_schema', 'evolve_concept', 'map_concepts']

        if operation not in valid_operations:
            errors.append(f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}")
            return errors

        # Validaciones específicas por operación
        if operation == 'load_ontology':
            if 'source' not in input_data:
                errors.append("Missing 'source' field for load_ontology operation")
            if 'ontology_id' not in input_data:
                errors.append("Missing 'ontology_id' field for load_ontology operation")

        elif operation == 'validate_schema':
            if 'data' not in input_data:
                errors.append("Missing 'data' field for validate_schema operation")
            if 'ontology_ids' not in input_data:
                errors.append("Missing 'ontology_ids' field for validate_schema operation")

        elif operation == 'evolve_concept':
            required_fields = ['ontology_id', 'concept_uri', 'changes']
            for field in required_fields:
                if field not in input_data:
                    errors.append(f"Missing '{field}' field for evolve_concept operation")

        elif operation == 'map_concepts':
            required_fields = ['source_ontology_id', 'target_ontology_id']
            for field in required_fields:
                if field not in input_data:
                    errors.append(f"Missing '{field}' field for map_concepts operation")

        return errors

    def _extract_ontology_config(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer configuración de ontología de los datos de entrada."""
        config = {}

        # Usar configuración del pipeline como base
        config.update(self.config.parameters)

        # Sobrescribir con parámetros específicos de la entrada
        if 'ontology_config' in input_data:
            input_config = input_data['ontology_config']
            if isinstance(input_config, dict):
                config.update(input_config)

        return config