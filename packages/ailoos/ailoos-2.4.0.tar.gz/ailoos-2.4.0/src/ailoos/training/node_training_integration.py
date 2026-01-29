"""
NodeTrainingIntegration - Integración entre SDK AILOOS y sistema de entrenamiento asíncrono
Permite que los nodos usen el SDK para entrenar EmpoorioLM con datasets locales.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pathlib import Path
import json

from .async_training_controller import AsyncTrainingController, AsyncTrainingConfig
from .training_state_manager import TrainingStateManager
from .checkpoint_manager import CheckpointManager, CheckpointConfig
from .training_progress_tracker import TrainingProgressTracker
from ..sdk.node_sdk import NodeSDK
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class DatasetAdapter:
    """
    Adaptador para convertir datasets del DataHub al formato de entrenamiento.
    """

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Cargar metadatos del dataset."""
        metadata_file = self.dataset_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def create_dataloader(self, batch_size: int = 8, max_length: int = 512) -> torch.utils.data.DataLoader:
        """
        Crear DataLoader desde el dataset descargado.

        Args:
            batch_size: Tamaño del batch
            max_length: Longitud máxima de secuencia

        Returns:
            DataLoader configurado
        """
        # Cargar datos (simplificado - en producción usar tokenización real)
        data_file = self.dataset_path / "data.jsonl"
        if not data_file.exists():
            raise FileNotFoundError(f"Archivo de datos no encontrado: {data_file}")

        texts = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                    elif isinstance(item, str):
                        texts.append(item)
                except json.JSONDecodeError:
                    continue

        # Limitar para demo (primeros 1000 textos)
        texts = texts[:1000]

        # Crear dataset simple (simulación - en producción usar tokenización real)
        class SimpleTextDataset(torch.utils.data.Dataset):
            def __init__(self, texts, max_length=512):
                self.texts = texts
                self.max_length = max_length

            def __len__(self):
                return len(self.texts)

            def __getitem__(self, idx):
                text = self.texts[idx]
                # Simular tokenización (IDs aleatorios para demo)
                input_ids = torch.randint(0, 30000, (self.max_length,))
                # Para next-token prediction, el target es el mismo input desplazado
                labels = input_ids.clone()
                return input_ids, labels

        dataset = SimpleTextDataset(texts, max_length)
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0  # 0 para evitar problemas en algunos entornos
        )

        logger.info(f"✅ DataLoader creado: {len(dataset)} muestras, batch_size={batch_size}")
        return dataloader


class NodeTrainingIntegration:
    """
    Integración completa entre SDK AILOOS y sistema de entrenamiento asíncrono.

    Permite que los nodos descarguen datasets y entrenen EmpoorioLM usando:
    - SDK AILOOS para gestión de nodo
    - Sistema de entrenamiento asíncrono para control
    - Datasets del DataHub para datos de entrenamiento
    """

    def __init__(
        self,
        node_id: str,
        datasets_dir: str = "./datasets",
        training_dir: str = "./training",
        coordinator_url: str = "http://localhost:8000"
    ):
        self.node_id = node_id
        self.datasets_dir = Path(datasets_dir)
        self.training_dir = Path(training_dir)
        self.coordinator_url = coordinator_url

        # Componentes del sistema
        self.sdk: Optional[NodeSDK] = None
        self.controller: Optional[AsyncTrainingController] = None
        self.current_session: Optional[str] = None

        # Estado
        self.is_initialized = False
        self.is_training = False

        logger.info(f"🚀 NodeTrainingIntegration inicializado para nodo {node_id}")

    async def initialize(self) -> bool:
        """
        Inicializar la integración completa.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("📋 Inicializando integración de entrenamiento por nodos...")

            # Crear directorios necesarios
            self.datasets_dir.mkdir(parents=True, exist_ok=True)
            self.training_dir.mkdir(parents=True, exist_ok=True)

            # Inicializar SDK AILOOS
            self.sdk = NodeSDK(
                node_id=self.node_id,
                coordinator_url=self.coordinator_url
            )

            success = await self.sdk.initialize()
            if not success:
                logger.error("❌ Error inicializando SDK AILOOS")
                return False

            # Iniciar SDK
            success = await self.sdk.start()
            if not success:
                logger.error("❌ Error iniciando SDK AILOOS")
                return False

            # Autenticar nodo
            auth_success = await self.sdk.authenticate()
            if not auth_success:
                logger.warning("⚠️ Autenticación pendiente - algunas funciones pueden no estar disponibles")

            self.is_initialized = True
            logger.info("✅ Integración de entrenamiento inicializada exitosamente")

            return True

        except Exception as e:
            logger.error(f"❌ Error en inicialización: {e}")
            return False

    async def list_available_datasets(self) -> List[Dict[str, Any]]:
        """
        Listar datasets disponibles en el DataHub.

        Returns:
            Lista de datasets disponibles
        """
        if not self.sdk:
            raise RuntimeError("SDK no inicializado")

        try:
            # En producción, esto vendría de una API del DataHub
            # Por ahora, simulamos datasets disponibles
            datasets = [
                {
                    "id": "medical_corpus_v1.2",
                    "name": "Corpus Médico General",
                    "description": "Conjunto de textos médicos diversos",
                    "category": "medical",
                    "language": "es",
                    "sample_count": 50000,
                    "size_mb": 250,
                    "quality_score": 0.89,
                    "price_drs": 0  # Gratuito
                },
                {
                    "id": "finance_reports_q3_2024",
                    "name": "Reportes Financieros Q3 2024",
                    "description": "Análisis financiero y reportes corporativos",
                    "category": "finance",
                    "language": "es",
                    "sample_count": 15000,
                    "size_mb": 120,
                    "quality_score": 0.92,
                    "price_drs": 50
                },
                {
                    "id": "educational_content_v2.1",
                    "name": "Contenido Educativo Diverso",
                    "description": "Textos educativos de múltiples materias",
                    "category": "education",
                    "language": "es",
                    "sample_count": 75000,
                    "size_mb": 380,
                    "quality_score": 0.85,
                    "price_drs": 25
                }
            ]

            logger.info(f"📋 Encontrados {len(datasets)} datasets disponibles")
            return datasets

        except Exception as e:
            logger.error(f"❌ Error listando datasets: {e}")
            return []

    async def download_dataset(self, dataset_id: str) -> bool:
        """
        Descargar un dataset desde el DataHub.

        Args:
            dataset_id: ID del dataset a descargar

        Returns:
            True si la descarga fue exitosa
        """
        if not self.sdk:
            raise RuntimeError("SDK no inicializado")

        try:
            logger.info(f"📥 Iniciando descarga del dataset {dataset_id}...")

            # Verificar balance si es necesario
            datasets = await self.list_available_datasets()
            dataset = next((d for d in datasets if d['id'] == dataset_id), None)

            if not dataset:
                logger.error(f"❌ Dataset {dataset_id} no encontrado")
                return False

            if dataset.get('price_drs', 0) > 0:
                balance = await self.sdk.get_wallet_balance()
                if balance < dataset['price_drs']:
                    logger.error(f"❌ Balance insuficiente: {balance} DRS < {dataset['price_drs']} DRS")
                    return False

                # Comprar dataset
                purchase_success = await self.sdk.purchase_data(dataset_id)
                if not purchase_success:
                    logger.error("❌ Error en la compra del dataset")
                    return False

                logger.info(f"✅ Dataset comprado por {dataset['price_drs']} DRS")

            # Simular descarga (en producción sería IPFS o similar)
            dataset_path = self.datasets_dir / dataset_id
            dataset_path.mkdir(exist_ok=True)

            # Crear archivos simulados
            metadata = {
                "id": dataset_id,
                "name": dataset["name"],
                "category": dataset["category"],
                "language": dataset["language"],
                "sample_count": dataset["sample_count"],
                "quality_score": dataset["quality_score"],
                "downloaded_at": time.time(),
                "source": "datahub"
            }

            with open(dataset_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Crear archivo de datos simulado
            sample_texts = [
                f"Texto de ejemplo {i} para dataset {dataset_id} en categoría {dataset['category']}."
                for i in range(min(1000, dataset["sample_count"]))  # Limitar para demo
            ]

            with open(dataset_path / "data.jsonl", 'w', encoding='utf-8') as f:
                for text in sample_texts:
                    json.dump({"text": text}, f, ensure_ascii=False)
                    f.write('\n')

            logger.info(f"✅ Dataset {dataset_id} descargado en {dataset_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error descargando dataset: {e}")
            return False

    async def start_training(
        self,
        dataset_id: str,
        max_epochs: int = 10,
        batch_size: int = 8,
        learning_rate: float = 0.001,
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> bool:
        """
        Iniciar entrenamiento con un dataset descargado.

        Args:
            dataset_id: ID del dataset a usar
            max_epochs: Número máximo de épocas
            batch_size: Tamaño del batch
            learning_rate: Tasa de aprendizaje
            on_progress: Callback para progreso
            on_complete: Callback para completado

        Returns:
            True si el entrenamiento inició correctamente
        """
        if not self.is_initialized:
            raise RuntimeError("Integración no inicializada")

        if self.is_training:
            logger.warning("⚠️ Ya hay un entrenamiento en curso")
            return False

        try:
            logger.info(f"🚀 Iniciando entrenamiento con dataset {dataset_id}...")

            # Verificar que el dataset existe
            dataset_path = self.datasets_dir / dataset_id
            if not dataset_path.exists():
                logger.error(f"❌ Dataset {dataset_id} no encontrado en {dataset_path}")
                return False

            # Crear adaptador de dataset
            adapter = DatasetAdapter(str(dataset_path))
            train_dataloader = adapter.create_dataloader(batch_size=batch_size)

            # Crear modelo EmpoorioLM
            model_config = EmpoorioLMConfig()
            model = EmpoorioLM(model_config)

            # Crear optimizador
            optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

            # Crear criterio de loss
            criterion = nn.CrossEntropyLoss()

            # Generar ID único para la sesión
            session_id = f"node_{self.node_id}_dataset_{dataset_id}_{int(time.time())}"

            # Configurar controlador de entrenamiento
            config = AsyncTrainingConfig(
                session_id=session_id,
                model=model,
                optimizer=optimizer,
                criterion=criterion,
                train_dataloader=train_dataloader,
                max_epochs=max_epochs,
                checkpoint_interval=50,  # Checkpoint cada 50 batches
                state_dir=str(self.training_dir / "state"),
                checkpoint_dir=str(self.training_dir / "checkpoints")
            )

            # Configurar callbacks
            if on_progress:
                config.on_batch_end = lambda epoch, batch, metrics: on_progress({
                    'epoch': epoch,
                    'batch': batch,
                    'metrics': metrics,
                    'session_id': session_id
                })

            if on_complete:
                config.on_epoch_end = lambda epoch, metrics: on_complete({
                    'epoch': epoch,
                    'final_metrics': metrics,
                    'session_id': session_id
                })

            # Crear controlador
            self.controller = AsyncTrainingController(config)
            self.current_session = session_id

            # Iniciar entrenamiento en background
            self.is_training = True

            # Para demo, ejecutamos de forma síncrona pero en producción sería async
            training_task = asyncio.create_task(self.controller.start_training())

            # Almacenar referencia para control
            self._training_task = training_task

            logger.info(f"✅ Entrenamiento iniciado: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error iniciando entrenamiento: {e}")
            self.is_training = False
            return False

    async def pause_training(self) -> bool:
        """Pausar el entrenamiento actual."""
        if not self.controller or not self.is_training:
            return False

        try:
            await self.controller.pause_training()
            logger.info("⏸️ Entrenamiento pausado")
            return True
        except Exception as e:
            logger.error(f"❌ Error pausando entrenamiento: {e}")
            return False

    async def resume_training(self) -> bool:
        """Reanudar el entrenamiento pausado."""
        if not self.controller or self.is_training:
            return False

        try:
            await self.controller.resume_training()
            self.is_training = True
            logger.info("▶️ Entrenamiento reanudado")
            return True
        except Exception as e:
            logger.error(f"❌ Error reanudando entrenamiento: {e}")
            return False

    async def stop_training(self) -> bool:
        """Detener el entrenamiento completamente."""
        if not self.controller:
            return False

        try:
            await self.controller.stop_training()
            self.is_training = False
            logger.info("🛑 Entrenamiento detenido")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo entrenamiento: {e}")
            return False

    async def get_training_status(self) -> Dict[str, Any]:
        """Obtener estado del entrenamiento actual."""
        if not self.controller:
            return {'status': 'no_active_training'}

        try:
            status = await self.controller.get_training_status()
            status['is_training'] = self.is_training
            return status
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return {'status': 'error', 'error': str(e)}

    async def submit_federated_contribution(self) -> bool:
        """
        Enviar contribución federada al coordinador central.

        Returns:
            True si la contribución fue aceptada
        """
        if not self.sdk or not self.current_session:
            return False

        try:
            logger.info("📤 Enviando contribución federada...")

            # Obtener el último checkpoint
            if not self.controller:
                return False

            # En producción, aquí se enviaría el modelo entrenado al coordinador
            # Por ahora, simulamos el envío

            # Simular validación y recompensa
            contribution_data = {
                'session_id': self.current_session,
                'node_id': self.node_id,
                'dataset_used': 'simulated_dataset',
                'training_metrics': await self.get_training_status(),
                'timestamp': time.time()
            }

            # Enviar al coordinador (simulado)
            success = await self._simulate_federated_submission(contribution_data)

            if success:
                logger.info("✅ Contribución federada aceptada")
                # En producción: recibir DracmaS como recompensa
                logger.info("💰 Recompensa de DracmaS enviada a wallet")
                return True
            else:
                logger.error("❌ Contribución federada rechazada")
                return False

        except Exception as e:
            logger.error(f"❌ Error enviando contribución: {e}")
            return False

    async def _simulate_federated_submission(self, contribution_data: Dict[str, Any]) -> bool:
        """Simular envío de contribución federada."""
        # En producción, esto sería una llamada real al coordinador
        await asyncio.sleep(0.5)  # Simular latencia de red

        # Simular validación (90% de éxito)
        import random
        success = random.random() < 0.9

        return success

    async def get_node_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del nodo."""
        if not self.sdk:
            return {}

        try:
            # Combinar estadísticas del SDK y del entrenamiento
            sdk_status = self.sdk.get_status()
            training_status = await self.get_training_status()

            # Obtener balance de Dracma
            balance = await self.sdk.get_wallet_balance()

            stats = {
                'node_id': self.node_id,
                'is_initialized': self.is_initialized,
                'is_training': self.is_training,
                'current_session': self.current_session,
                'sdk_status': sdk_status,
                'training_status': training_status,
                'dracma_balance': balance,
                'datasets_available': len(await self.list_available_datasets()),
                'uptime_seconds': time.time() - getattr(self, '_start_time', time.time())
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {'error': str(e)}

    async def shutdown(self) -> None:
        """Apagar la integración y limpiar recursos."""
        logger.info("🧹 Apagando integración de entrenamiento...")

        # Detener entrenamiento si está activo
        if self.is_training and self.controller:
            await self.stop_training()

        # Apagar SDK
        if self.sdk:
            await self.sdk.shutdown()

        self.is_initialized = False
        self.is_training = False

        logger.info("✅ Integración apagada")


# Funciones de conveniencia
async def create_node_training_integration(
    node_id: str,
    datasets_dir: str = "./datasets",
    training_dir: str = "./training",
    coordinator_url: str = "http://localhost:8000"
) -> NodeTrainingIntegration:
    """
    Crear e inicializar una instancia de NodeTrainingIntegration.

    Args:
        node_id: ID único del nodo
        datasets_dir: Directorio para datasets
        training_dir: Directorio para entrenamiento
        coordinator_url: URL del coordinador

    Returns:
        Instancia inicializada
    """
    integration = NodeTrainingIntegration(
        node_id=node_id,
        datasets_dir=datasets_dir,
        training_dir=training_dir,
        coordinator_url=coordinator_url
    )

    success = await integration.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize NodeTrainingIntegration for node {node_id}")

    return integration


async def demo_node_training():
    """Demo de uso de NodeTrainingIntegration."""
    print("🎯 Demo: NodeTrainingIntegration")
    print("=" * 50)

    # Crear integración
    integration = await create_node_training_integration("demo_node_001")

    try:
        # Listar datasets disponibles
        print("\n📋 Listando datasets disponibles...")
        datasets = await integration.list_available_datasets()
        for ds in datasets:
            print(f"  • {ds['name']} ({ds['category']}) - {ds['price_drs']} DRS")

        # Descargar un dataset gratuito
        print("\n📥 Descargando dataset gratuito...")
        success = await integration.download_dataset("medical_corpus_v1.2")
        print(f"  Descarga: {'exitosa' if success else 'fallida'}")

        # Iniciar entrenamiento
        print("\n🚀 Iniciando entrenamiento...")
        training_started = await integration.start_training(
            dataset_id="medical_corpus_v1.2",
            max_epochs=3,
            batch_size=4
        )

        if training_started:
            # Monitorear progreso por un tiempo
            print("📊 Monitoreando progreso...")
            for i in range(5):
                status = await integration.get_training_status()
                print(f"  Epoch {status.get('current_epoch', 0)} - "
                      f"Progreso: {status.get('progress_percentage', 0):.1f}%")
                await asyncio.sleep(1)

            # Pausar y reanudar
            print("\n⏸️ Pausando entrenamiento...")
            await integration.pause_training()
            await asyncio.sleep(1)

            print("▶️ Reanudando entrenamiento...")
            await integration.resume_training()
            await asyncio.sleep(2)

            # Detener
            print("\n🛑 Deteniendo entrenamiento...")
            await integration.stop_training()

            # Enviar contribución federada
            print("\n📤 Enviando contribución federada...")
            contribution_accepted = await integration.submit_federated_contribution()
            print(f"  Contribución: {'aceptada' if contribution_accepted else 'rechazada'}")

        # Mostrar estadísticas finales
        print("\n📊 Estadísticas del nodo:")
        stats = await integration.get_node_stats()
        print(f"  Balance Dracma: {stats.get('dracma_balance', 0)}")
        print(f"  Datasets disponibles: {stats.get('datasets_available', 0)}")

    finally:
        await integration.shutdown()
        print("\n✅ Demo completada")


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(demo_node_training())