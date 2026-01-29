"""
Pruebas básicas para la Processing Layer de grafos de conocimiento.
Verifica la funcionalidad de pipelines configurables y ejecución paralela.
"""

import asyncio
import time
from typing import Dict, List, Any

from ..core.logging import get_logger
from . import (
    get_pipeline_manager,
    PipelineConfig,
    PipelineType,
    PipelineResult,
    PipelineStatus
)

logger = get_logger(__name__)


async def test_pipeline_creation():
    """Prueba la creación y configuración de pipelines."""
    logger.info("Testing pipeline creation...")

    manager = get_pipeline_manager()

    # Verificar configuraciones por defecto
    configs = manager.list_pipeline_configs()
    assert len(configs) == 4, f"Expected 4 default configs, got {len(configs)}"

    # Verificar tipos de pipeline
    expected_types = {'fusion', 'qa', 'evolution', 'ontology'}
    actual_types = set(configs.keys())
    assert actual_types == expected_types, f"Expected {expected_types}, got {actual_types}"

    logger.info("✅ Pipeline creation test passed")


async def test_fusion_pipeline():
    """Prueba el pipeline de fusión."""
    logger.info("Testing fusion pipeline...")

    manager = get_pipeline_manager()

    # Datos de prueba para fusión
    test_data = {
        'sources': [
            {
                'id': 'source1',
                'name': 'Test Source 1',
                'data': '{"@graph": [{"@id": "test:entity1", "rdfs:label": "Entity 1"}]}',
                'format': 'json_ld',
                'confidence': 0.9,
                'priority': 1
            },
            {
                'id': 'source2',
                'name': 'Test Source 2',
                'data': '{"@graph": [{"@id": "test:entity2", "rdfs:label": "Entity 2"}]}',
                'format': 'json_ld',
                'confidence': 0.8,
                'priority': 2
            }
        ]
    }

    # Ejecutar pipeline
    result = await manager.execute_pipeline('fusion', test_data)

    # Verificar resultado
    assert isinstance(result, PipelineResult), "Expected PipelineResult"
    assert result.pipeline_type == PipelineType.FUSION, f"Expected FUSION type, got {result.pipeline_type}"
    assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status: {result.status}"

    if result.success:
        assert 'fusion_id' in result.output_data, "Missing fusion_id in output"
        assert 'fused_triples' in result.output_data, "Missing fused_triples in output"

    logger.info(f"✅ Fusion pipeline test completed with status: {result.status.value}")


async def test_qa_pipeline():
    """Prueba el pipeline de Quality Assurance."""
    logger.info("Testing QA pipeline...")

    manager = get_pipeline_manager()

    # Datos de prueba para QA
    test_data = {
        'operation': 'validate_quality',
        'triples': [
            {'subject': 'test:entity1', 'predicate': 'rdfs:label', 'object': 'Entity 1'},
            {'subject': 'test:entity1', 'predicate': 'rdf:type', 'object': 'owl:Class'}
        ]
    }

    # Ejecutar pipeline
    result = await manager.execute_pipeline('qa', test_data)

    # Verificar resultado
    assert isinstance(result, PipelineResult), "Expected PipelineResult"
    assert result.pipeline_type == PipelineType.QUALITY_ASSURANCE, f"Expected QUALITY_ASSURANCE type, got {result.pipeline_type}"
    assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status: {result.status}"

    if result.success:
        assert 'operation' in result.output_data, "Missing operation in output"
        assert result.output_data['operation'] == 'validate_quality', "Wrong operation in output"

    logger.info(f"✅ QA pipeline test completed with status: {result.status.value}")


async def test_evolution_pipeline():
    """Prueba el pipeline de evolución."""
    logger.info("Testing evolution pipeline...")

    manager = get_pipeline_manager()

    # Datos de prueba para evolución
    test_data = {
        'evolution_type': 'temporal'
    }

    # Ejecutar pipeline
    result = await manager.execute_pipeline('evolution', test_data)

    # Verificar resultado
    assert isinstance(result, PipelineResult), "Expected PipelineResult"
    assert result.pipeline_type == PipelineType.EVOLUTION, f"Expected EVOLUTION type, got {result.pipeline_type}"
    assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status: {result.status}"

    logger.info(f"✅ Evolution pipeline test completed with status: {result.status.value}")


async def test_ontology_pipeline():
    """Prueba el pipeline de ontología."""
    logger.info("Testing ontology pipeline...")

    manager = get_pipeline_manager()

    # Datos de prueba para ontología (validación de esquema)
    test_data = {
        'operation': 'validate_schema',
        'data': [
            {'subject': 'test:entity1', 'predicate': 'rdfs:label', 'object': 'Entity 1'},
            {'subject': 'test:entity1', 'predicate': 'rdf:type', 'object': 'owl:Class'}
        ],
        'ontology_ids': []  # Sin ontologías específicas para prueba básica
    }

    # Ejecutar pipeline
    result = await manager.execute_pipeline('ontology', test_data)

    # Verificar resultado
    assert isinstance(result, PipelineResult), "Expected PipelineResult"
    assert result.pipeline_type == PipelineType.ONTOLOGY, f"Expected ONTOLOGY type, got {result.pipeline_type}"
    assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status: {result.status}"

    if result.success:
        assert 'operation' in result.output_data, "Missing operation in output"
        assert result.output_data['operation'] == 'validate_schema', "Wrong operation in output"

    logger.info(f"✅ Ontology pipeline test completed with status: {result.status.value}")


async def test_pipeline_chain():
    """Prueba la ejecución en cadena de pipelines."""
    logger.info("Testing pipeline chain execution...")

    manager = get_pipeline_manager()

    # Datos de entrada para la cadena
    test_data = {
        'triples': [
            {'subject': 'test:entity1', 'predicate': 'rdfs:label', 'object': 'Entity 1'},
            {'subject': 'test:entity1', 'predicate': 'rdf:type', 'object': 'owl:Class'}
        ]
    }

    # Ejecutar cadena: QA -> Ontology
    pipeline_names = ['qa', 'ontology']
    results = await manager.execute_pipeline_chain(pipeline_names, test_data)

    # Verificar resultados
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert 'qa' in results, "Missing QA result"
    assert 'ontology' in results, "Missing Ontology result"

    for name, result in results.items():
        assert isinstance(result, PipelineResult), f"Expected PipelineResult for {name}"
        assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status for {name}: {result.status}"

    logger.info("✅ Pipeline chain test completed")


async def test_parallel_execution():
    """Prueba la ejecución paralela de pipelines."""
    logger.info("Testing parallel pipeline execution...")

    manager = get_pipeline_manager()

    # Datos de entrada
    test_data = {
        'triples': [
            {'subject': 'test:entity1', 'predicate': 'rdfs:label', 'object': 'Entity 1'}
        ]
    }

    # Ejecutar en paralelo (QA y Ontology pueden ser independientes)
    pipeline_names = ['qa', 'ontology']
    results = await manager.execute_pipeline_chain(pipeline_names, test_data, parallel_execution=True)

    # Verificar resultados
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"

    for name, result in results.items():
        assert isinstance(result, PipelineResult), f"Expected PipelineResult for {name}"
        assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED], f"Unexpected status for {name}: {result.status}"

    logger.info("✅ Parallel execution test completed")


async def test_pipeline_metrics():
    """Prueba las métricas de pipelines."""
    logger.info("Testing pipeline metrics...")

    manager = get_pipeline_manager()

    # Obtener métricas iniciales
    initial_metrics = manager.get_pipeline_metrics()

    # Ejecutar algunos pipelines
    test_data = {
        'operation': 'validate_quality',
        'triples': [
            {'subject': 'test:entity1', 'predicate': 'rdfs:label', 'object': 'Entity 1'}
        ]
    }

    await manager.execute_pipeline('qa', test_data)
    await manager.execute_pipeline('qa', test_data)

    # Obtener métricas después
    final_metrics = manager.get_pipeline_metrics()

    # Verificar que las métricas se actualizaron
    assert final_metrics['total_executions'] >= initial_metrics['total_executions'], "Executions count should increase"

    logger.info("✅ Pipeline metrics test completed")


async def run_all_tests():
    """Ejecutar todas las pruebas."""
    logger.info("🚀 Starting Processing Layer tests...")

    start_time = time.time()

    try:
        await test_pipeline_creation()
        await test_fusion_pipeline()
        await test_qa_pipeline()
        await test_evolution_pipeline()
        await test_ontology_pipeline()
        await test_pipeline_chain()
        await test_parallel_execution()
        await test_pipeline_metrics()

        total_time = time.time() - start_time
        logger.info(f"✅ All tests passed in {total_time:.2f} seconds")
        return True

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Ejecutar pruebas
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)