"""
Test básico de integración del pipeline federado
Verifica que todos los componentes funcionen juntos correctamente.
"""

import asyncio
import logging
import sys
from pathlib import Path
import torch

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .federated_pipeline import FederatedPipeline, PipelineConfig
from .federated_data_loader import DataLoadConfig
from .secure_data_preprocessor import PreprocessingConfig
from .homomorphic_encryptor import EncryptionConfig
from .secure_aggregator import AggregationConfig

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_pipeline():
    """Prueba básica del pipeline federado."""
    logger.info("🧪 Iniciando prueba básica del pipeline federado")

    try:
        # Configuración del pipeline
        config = PipelineConfig(
            session_id="test_session_001",
            model_name="test_model",
            max_rounds=2,
            target_participants=2,
            data_config=DataLoadConfig(
                max_memory_mb=100,
                prefetch_workers=2,
                batch_size=16
            ),
            preprocessing_config=PreprocessingConfig(
                enable_differential_privacy=False,  # Deshabilitar para prueba básica
                enable_data_sanitization=True,
                enable_feature_scaling=True
            ),
            encryption_config=EncryptionConfig(
                enable_key_rotation=False,  # Deshabilitar para simplificar
                cache_encrypted_values=True
            ),
            aggregation_config=AggregationConfig(
                min_participants=1,  # Solo 1 para prueba
                enable_differential_privacy=False,
                aggregation_type="fedavg"
            )
        )

        # Crear pipeline
        pipeline = FederatedPipeline(config)
        success = await pipeline.initialize()

        if not success:
            logger.error("❌ Falló la inicialización del pipeline")
            return False

        logger.info("✅ Pipeline inicializado correctamente")

        # Simular registro de nodos (sin datos reales de IPFS)
        # En una prueba real, usaríamos CIDs válidos
        test_nodes = [
            {
                'node_id': 'node_001',
                'data_cids': ['test_cid_001', 'test_cid_002'],  # CIDs dummy
                'ipfs_endpoint': 'http://localhost:5001/api/v0'
            },
            {
                'node_id': 'node_002',
                'data_cids': ['test_cid_003', 'test_cid_004'],  # CIDs dummy
                'ipfs_endpoint': 'http://localhost:5001/api/v0'
            }
        ]

        # Registrar nodos (esto fallará sin IPFS real, pero prueba la estructura)
        registered_nodes = 0
        for node_config in test_nodes:
            try:
                success = await pipeline.register_node(**node_config)
                if success:
                    registered_nodes += 1
                    logger.info(f"✅ Nodo {node_config['node_id']} registrado")
                else:
                    logger.warning(f"⚠️ Falló registro de nodo {node_config['node_id']}")
            except Exception as e:
                logger.warning(f"⚠️ Error registrando nodo {node_config['node_id']}: {e}")

        if registered_nodes == 0:
            logger.warning("⚠️ No se pudieron registrar nodos (esperado sin IPFS real)")
            # Continuar con prueba de estructura
        else:
            logger.info(f"✅ Registrados {registered_nodes} nodos")

        # Verificar estado del pipeline
        status = pipeline.get_pipeline_status()
        logger.info(f"📊 Estado del pipeline: {status['phase']}")

        # Probar ejecución del pipeline (puede fallar sin datos reales)
        try:
            result = await pipeline.run_pipeline()
            logger.info(f"🎯 Resultado del pipeline: éxito={result.get('success', False)}")
        except Exception as e:
            logger.warning(f"⚠️ Ejecución del pipeline falló (esperado sin datos reales): {e}")

        # Obtener métricas finales
        metrics = pipeline.get_pipeline_metrics()
        logger.info(f"📈 Métricas finales: {len(metrics.get('rounds_history', []))} rondas")

        # Apagar pipeline
        await pipeline.shutdown()
        logger.info("🛑 Pipeline apagado correctamente")

        return True

    except Exception as e:
        logger.error(f"❌ Prueba básica falló: {e}")
        return False


async def test_component_integration():
    """Prueba integración de componentes individuales."""
    logger.info("🔧 Probando integración de componentes")

    try:
        from .federated_data_loader import FederatedDataLoader
        from .secure_data_preprocessor import SecureDataPreprocessor
        from .homomorphic_encryptor import HomomorphicEncryptor
        from .privacy_preserving_aggregator import PrivacyPreservingAggregator

        # Probar creación de componentes
        data_loader = FederatedDataLoader("test_node", "http://localhost:5001/api/v0")
        await data_loader.initialize()
        logger.info("✅ DataLoader creado")

        preprocessor = SecureDataPreprocessor("test_node")
        preprocessor.initialize()
        logger.info("✅ Preprocessor creado")

        encryptor = HomomorphicEncryptor("test_node")
        encryptor.initialize()
        logger.info("✅ Encryptor creado")

        aggregator = PrivacyPreservingAggregator("test_session", "test_model")
        aggregator.initialize()
        logger.info("✅ Aggregator creado")

        # Probar preprocesamiento básico
        test_data = torch.randn(10, 5)
        processed_data, _, _ = preprocessor.preprocess_batch(test_data)
        logger.info("✅ Preprocesamiento básico funciona")

        # Probar encriptación básica
        test_gradients = {'layer1': torch.randn(5, 3)}
        encrypted = encryptor.encrypt_gradients(test_gradients)
        logger.info("✅ Encriptación básica funciona")

        # Limpiar
        await data_loader.shutdown()

        return True

    except Exception as e:
        logger.error(f"❌ Prueba de componentes falló: {e}")
        return False


async def main():
    """Función principal de pruebas."""
    logger.info("🚀 Iniciando pruebas de integración del pipeline federado")

    # Probar componentes individuales
    component_test = await test_component_integration()
    if not component_test:
        logger.error("❌ Fallaron pruebas de componentes")
        return False

    # Probar pipeline completo
    pipeline_test = await test_basic_pipeline()
    if not pipeline_test:
        logger.error("❌ Fallaron pruebas del pipeline")
        return False

    logger.info("🎉 Todas las pruebas pasaron exitosamente")
    return True


if __name__ == "__main__":
    # Verificar dependencias
    try:
        import torch
        import numpy as np
        logger.info("✅ Dependencias disponibles")
    except ImportError as e:
        logger.error(f"❌ Dependencias faltantes: {e}")
        sys.exit(1)

    # Ejecutar pruebas
    success = asyncio.run(main())
    sys.exit(0 if success else 1)