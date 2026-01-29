"""
Federated Pipeline - Pipeline completo de datos federados para AILOOS
Integra todos los componentes para un sistema de federated learning production-ready.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import torch
import torch.nn as nn

from ..core.logging import get_logger
from ..core.config import get_config
from .federated_data_loader import FederatedDataLoader, DataLoadConfig
from .secure_data_preprocessor import SecureDataPreprocessor, PreprocessingConfig
from .homomorphic_encryptor import HomomorphicEncryptor, EncryptionConfig
from .privacy_preserving_aggregator import PrivacyPreservingAggregator
from .data_coordinator import FederatedDataCoordinator
from .secure_aggregator import AggregationConfig
from .federated_versioning_system import FederatedVersioningSystem, SystemConfig

logger = get_logger(__name__)


class PipelinePhase(Enum):
    """Fases del pipeline federado."""
    INITIALIZING = "initializing"
    LOADING_DATA = "loading_data"
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    ENCRYPTING = "encrypting"
    AGGREGATING = "aggregating"
    UPDATING_MODEL = "updating_model"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Configuración completa del pipeline federado."""
    session_id: str
    model_name: str = "federated_model"

    # Configuraciones de componentes
    data_config: DataLoadConfig = field(default_factory=DataLoadConfig)
    preprocessing_config: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    encryption_config: EncryptionConfig = field(default_factory=EncryptionConfig)
    aggregation_config: AggregationConfig = field(default_factory=AggregationConfig)

    # Configuración del pipeline
    max_rounds: int = 10
    target_participants: int = 5
    convergence_threshold: float = 0.001
    enable_monitoring: bool = True
    checkpoint_interval: int = 5

    # Recursos
    max_memory_gb: float = 8.0
    max_concurrent_nodes: int = 10

    # Configuración de versionado
    enable_versioning: bool = True
    versioning_config: SystemConfig = field(default_factory=SystemConfig)
    auto_version_registration: bool = True  # Registrar versiones automáticamente después de rondas
    version_registration_interval: int = 5  # Registrar versión cada N rondas

    # Configuración de Privacidad Diferencial
    enable_differential_privacy: bool = False
    dp_epsilon: float = 1.0  # Presupuesto de privacidad
    dp_delta: float = 1e-5   # Probabilidad de fallo
    dp_max_grad_norm: float = 1.0  # Clipping threshold

    # Configuración de Encriptación Homomórfica
    enable_homomorphic_encryption: bool = False


@dataclass
class PipelineStatus:
    """Estado del pipeline."""
    phase: PipelinePhase
    current_round: int = 0
    total_rounds: int = 0
    active_nodes: List[str] = field(default_factory=list)
    completed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    last_update: Optional[float] = None
    progress: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class TrainingResult:
    """Resultado de una ronda de entrenamiento."""
    node_id: str
    gradients: Dict[str, torch.Tensor]
    loss: float
    accuracy: float
    num_samples: int
    training_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class FederatedPipeline:
    """
    Pipeline completo para federated learning con privacidad preservada.
    Coordina todos los componentes para un flujo de trabajo end-to-end.
    """

    def __init__(self, config: PipelineConfig):
        """
        Inicializar el pipeline federado.

        Args:
            config: Configuración completa del pipeline
        """
        self.config = config
        self.allow_mocks = self._resolve_allow_mocks()

        # Estado del pipeline
        self.status = PipelineStatus(phase=PipelinePhase.INITIALIZING)
        self.is_initialized = False

        # Componentes del pipeline
        self.data_coordinator: Optional[FederatedDataCoordinator] = None
        self.node_components: Dict[str, Dict[str, Any]] = {}  # Componentes por nodo

        # Sistema de versionado
        self.versioning_system: Optional[FederatedVersioningSystem] = None

        # Modelo global
        self.global_model: Optional[nn.Module] = None
        self.model_state: Dict[str, torch.Tensor] = {}

        # Historial y métricas
        self.training_history: List[Dict[str, Any]] = []
        self.metrics_history: List[Dict[str, Any]] = []

        # Control de concurrencia
        self.node_semaphore = asyncio.Semaphore(self.config.max_concurrent_nodes)

        logger.info(f"🚀 FederatedPipeline initialized for session {config.session_id}")

    async def initialize(self) -> bool:
        """
        Inicializar todos los componentes del pipeline.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.status.phase = PipelinePhase.INITIALIZING
            self.status.start_time = datetime.now().timestamp()

            # Inicializar coordinador de datos
            try:
                from ..core.config import Config
                core_config = Config()
                self.data_coordinator = FederatedDataCoordinator(core_config)
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize full data coordinator: {e}")
                self.data_coordinator = None
                if not self.allow_mocks:
                    self.status.phase = PipelinePhase.FAILED
                    self.status.errors.append("data_coordinator_unavailable")
                    return False

            # Inicializar sistema de versionado si está habilitado
            if self.config.enable_versioning:
                try:
                    self.versioning_system = FederatedVersioningSystem(self.config.versioning_config)
                    success = await self.versioning_system.initialize()
                    if success:
                        logger.info("✅ Versioning system initialized")
                    else:
                        logger.warning("⚠️ Versioning system initialization failed")
                        self.versioning_system = None
                except Exception as e:
                    logger.warning(f"⚠️ Could not initialize versioning system: {e}")
                    self.versioning_system = None

            # Marcar como inicializado
            self.is_initialized = True
            self.status.phase = PipelinePhase.LOADING_DATA

            logger.info(f"✅ FederatedPipeline initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Pipeline initialization failed: {e}")
            self.status.phase = PipelinePhase.FAILED
            self.status.errors.append(str(e))
            return False

    async def register_node(self, node_id: str, data_cids: List[str],
                          ipfs_endpoint: str = "http://localhost:5001/api/v0") -> bool:
        """
        Registrar un nuevo nodo en el pipeline.

        Args:
            node_id: ID único del nodo
            data_cids: CIDs de datos del nodo
            ipfs_endpoint: Endpoint de IPFS

        Returns:
            True si el registro fue exitoso
        """
        try:
            async with self.node_semaphore:
                # Crear componentes para el nodo
                node_components = await self._create_node_components(node_id, ipfs_endpoint)

                # Cargar datos del nodo
                data_loader = node_components['data_loader']
                success = await data_loader.load_local_dataset(data_cids)

                if success:
                    self.node_components[node_id] = node_components
                    self.status.active_nodes.append(node_id)
                    logger.info(f"📝 Node {node_id} registered successfully")
                    return True
                else:
                    logger.error(f"❌ Failed to load data for node {node_id}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to register node {node_id}: {e}")
            self.status.failed_nodes.append(node_id)
            return False

    async def _create_node_components(self, node_id: str, ipfs_endpoint: str) -> Dict[str, Any]:
        """
        Crear componentes para un nodo específico.

        Args:
            node_id: ID del nodo
            ipfs_endpoint: Endpoint de IPFS

        Returns:
            Diccionario con componentes del nodo
        """
        # Data Loader
        data_loader = FederatedDataLoader(
            node_id=node_id,
            ipfs_endpoint=ipfs_endpoint,
            config=self.config.data_config
        )
        await data_loader.initialize()

        # Preprocesador seguro
        preprocessor = SecureDataPreprocessor(
            node_id=node_id,
            config=self.config.preprocessing_config
        )
        preprocessor.initialize()

        # Encriptador homomórfico
        encryptor = HomomorphicEncryptor(
            node_id=node_id,
            config=self.config.encryption_config
        )
        encryptor.initialize()

        return {
            'data_loader': data_loader,
            'preprocessor': preprocessor,
            'encryptor': encryptor,
            'registered_at': datetime.now().timestamp()
        }

    async def start_training_round(self, round_num: int) -> Dict[str, Any]:
        """
        Iniciar una ronda de entrenamiento federado.

        Args:
            round_num: Número de la ronda

        Returns:
            Resultado de la ronda
        """
        try:
            self.status.phase = PipelinePhase.TRAINING
            self.status.current_round = round_num
            self.status.last_update = datetime.now().timestamp()

            logger.info(f"🎯 Starting training round {round_num}")

            # Configurar encriptador si está habilitado
            encryptor = None
            if self.config.enable_homomorphic_encryption:
                encryptor = HomomorphicEncryptor(
                    node_id="aggregator",
                    config=self.config.encryption_config
                )
                encryptor.initialize()
                logger.info("🔐 Homomorphic Encryption enabled for aggregation")

            # Crear agregador para esta ronda
            aggregator = PrivacyPreservingAggregator(
                session_id=f"{self.config.session_id}_round_{round_num}",
                model_name=self.config.model_name,
                config=self.config.aggregation_config,
                encryptor=encryptor
            )
            aggregator.initialize()

            # Ejecutar entrenamiento en nodos
            training_tasks = []
            for node_id in self.status.active_nodes:
                if node_id in self.node_components:
                    task = self._train_on_node(node_id, round_num)
                    training_tasks.append(task)

            # Esperar resultados de entrenamiento
            training_results = await asyncio.gather(*training_tasks, return_exceptions=True)

            # Procesar resultados
            successful_results = []
            for i, result in enumerate(training_results):
                node_id = self.status.active_nodes[i]
                if isinstance(result, Exception):
                    logger.error(f"❌ Training failed on node {node_id}: {result}")
                    self.status.failed_nodes.append(node_id)
                else:
                    successful_results.append((node_id, result))

            # Agregar actualizaciones
            for node_id, training_result in successful_results:
                await aggregator.submit_node_update(
                    node_id=node_id,
                    weights=training_result.gradients,
                    num_samples=training_result.num_samples,
                    metadata={
                        'loss': training_result.loss,
                        'accuracy': training_result.accuracy,
                        'training_time': training_result.training_time
                    }
                )

            # Forzar agregación si tenemos suficientes resultados
            if len(successful_results) >= self.config.aggregation_config.min_participants:
                aggregation_result = await aggregator.force_aggregation()

                if aggregation_result and aggregation_result.success:
                    # Actualizar modelo global
                    self.model_state = aggregation_result.global_weights
                    self.status.completed_nodes.extend([node_id for node_id, _ in successful_results])

                    # Registrar métricas
                    round_metrics = {
                        'round': round_num,
                        'participants': len(successful_results),
                        'computation_time': aggregation_result.computation_time,
                        'avg_loss': np.mean([r.loss for _, r in successful_results]),
                        'avg_accuracy': np.mean([r.accuracy for _, r in successful_results]),
                        'total_samples': sum([r.num_samples for _, r in successful_results])
                    }
                    self.metrics_history.append(round_metrics)

                    self.status.phase = PipelinePhase.COMPLETED
                    self.status.progress = (round_num / self.config.max_rounds) * 100

                    # Registrar versión automáticamente si está habilitado
                    if (self.config.enable_versioning and self.versioning_system and
                        self.config.auto_version_registration and
                        round_num % self.config.version_registration_interval == 0):
                        await self._register_model_version(round_num, round_metrics)

                    logger.info(f"✅ Round {round_num} completed: {len(successful_results)} participants")

                    return {
                        'success': True,
                        'round': round_num,
                        'participants': len(successful_results),
                        'global_model_updated': True,
                        'metrics': round_metrics,
                        'version_registered': (self.config.enable_versioning and
                                             self.versioning_system and
                                             self.config.auto_version_registration and
                                             round_num % self.config.version_registration_interval == 0)
                    }
                else:
                    logger.error(f"❌ Aggregation failed for round {round_num}")
                    self.status.phase = PipelinePhase.FAILED
                    return {
                        'success': False,
                        'round': round_num,
                        'error': 'Aggregation failed'
                    }
            else:
                logger.warning(f"⚠️ Insufficient participants for round {round_num}: {len(successful_results)} < {self.config.aggregation_config.min_participants}")
                return {
                    'success': False,
                    'round': round_num,
                    'error': 'Insufficient participants'
                }

        except Exception as e:
            logger.error(f"❌ Training round {round_num} failed: {e}")
            self.status.phase = PipelinePhase.FAILED
            self.status.errors.append(str(e))
            return {
                'success': False,
                'round': round_num,
                'error': str(e)
            }

    async def _train_on_node(self, node_id: str, round_num: int) -> TrainingResult:
        """
        Entrenar en un nodo específico.

        Args:
            node_id: ID del nodo
            round_num: Número de ronda

        Returns:
            Resultado del entrenamiento
        """
        try:
            components = self.node_components[node_id]
            data_loader = components['data_loader']
            preprocessor = components['preprocessor']
            encryptor = components['encryptor']

            start_time = datetime.now()

            # Obtener datos del lote
            batch = await data_loader.get_next_batch()
            if not batch:
                raise ValueError(f"No data available for node {node_id}")

            # Preprocesar datos
            processed_data, processed_targets, metadata = preprocessor.preprocess_batch(
                batch.inputs, batch.targets
            )

            # Realizar entrenamiento real
            gradients, loss, accuracy = await self._perform_local_training(
                processed_data, processed_targets, self.model_state
            )

            # Preprocesar gradientes
            secure_gradients = preprocessor.preprocess_gradients(gradients)

            training_time = (datetime.now() - start_time).total_seconds()

            return TrainingResult(
                node_id=node_id,
                gradients=secure_gradients,
                loss=loss,
                accuracy=accuracy,
                num_samples=processed_data.size(0),
                training_time=training_time,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"❌ Training failed on node {node_id}: {e}")
            raise

    async def _perform_local_training(self, data: torch.Tensor, targets: torch.Tensor,
                                    global_weights: Dict[str, torch.Tensor]) -> Tuple[Dict[str, torch.Tensor], float, float]:
        """
        Realizar entrenamiento local real en un nodo (simulado o real).
        
        Args:
            data: Datos de entrada
            targets: Etiquetas
            global_weights: Pesos globales actuales
            
        Returns:
            Tuple de (gradientes, pérdida, precisión)
        """
        try:
            # Crear modelo temporal para entrenamiento local
            # En una implementación real distribuida, esto ya estaría en el nodo
            # Aquí creamos una instancia para simular el nodo aislado
            from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
            
            # Usar configuración del pipeline si está disponible, sino default
            model_config = EmpoorioLMConfig() 
            local_model = EmpoorioLM(model_config)
            
            # Cargar pesos globales si existen
            if global_weights:
                local_model.load_state_dict(global_weights)
                
            local_model.train()
            optimizer = torch.optim.AdamW(local_model.parameters(), lr=5e-5)
            criterion = nn.CrossEntropyLoss()
            
            # Entrenamiento (1 epoch sobre el batch proporcionado)
            optimizer.zero_grad()
            
            outputs = local_model(data)
            logits = outputs["logits"]
            
            # Calcular loss
            loss = criterion(logits.view(-1, logits.size(-1)), targets.view(-1))
            
            # Backward pass
            loss.backward()
            
            # Obtener gradientes
            gradients = {}
            
            # Differential Privacy: Gradient Clipping
            if self.config.enable_differential_privacy:
                # Calculate total norm for global clipping
                total_norm = torch.norm(torch.stack([torch.norm(p.grad.detach(), 2) for p in local_model.parameters() if p.grad is not None]), 2)
                clip_coef = self.config.dp_max_grad_norm / (total_norm + 1e-6)
                clip_coef = torch.clamp(clip_coef, max=1.0)
            
            for name, param in local_model.named_parameters():
                if param.grad is not None:
                    grad = param.grad.clone().detach()
                    
                    if self.config.enable_differential_privacy:
                        # Apply clipping
                        grad.mul_(clip_coef)
                        
                        # Add Gaussian Noise
                        # Sigma calculation (simplified for basic DP)
                        # sigma = sqrt(2 * log(1.25/delta)) / epsilon
                        sigma = np.sqrt(2 * np.log(1.25 / self.config.dp_delta)) / self.config.dp_epsilon
                        noise = torch.normal(0, sigma * self.config.dp_max_grad_norm, size=grad.shape).to(grad.device)
                        grad.add_(noise)
                        
                    gradients[name] = grad
            
            # Calcular accuracy
            with torch.no_grad():
                predictions = logits.argmax(dim=-1)
                correct = (predictions == targets).float().sum()
                accuracy = (correct / targets.numel()).item()
                
            return gradients, loss.item(), accuracy

        except Exception as e:
            logger.error(f"❌ Local training failed: {e}")
            raise

    async def _register_model_version(self, round_num: int, round_metrics: Dict[str, Any]):
        """
        Registrar una nueva versión del modelo después de una ronda exitosa.

        Args:
            round_num: Número de ronda
            round_metrics: Métricas de la ronda
        """
        if not self.versioning_system or not self.model_state:
            return

        try:
            # Serializar el estado del modelo (simplificado para demo)
            # En producción, esto sería una serialización completa del modelo PyTorch
            import pickle
            model_data = pickle.dumps(self.model_state)

            # Crear metadatos de la versión
            metadata = {
                'model_name': self.config.model_name,
                'version': f"1.{round_num}.0",
                'variant': 'federated',
                'description': f'Model after federated round {round_num}',
                'federated_info': {
                    'round_number': round_num,
                    'participants': round_metrics['participants'],
                    'total_samples': round_metrics['total_samples'],
                    'computation_time': round_metrics['computation_time'],
                    'session_id': self.config.session_id
                },
                'quality_metrics': {
                    'accuracy': round_metrics['avg_accuracy'],
                    'loss': round_metrics['avg_loss'],
                    'total_samples': round_metrics['total_samples'],
                    'participants': round_metrics['participants']
                },
                'config': {
                    'max_rounds': self.config.max_rounds,
                    'convergence_threshold': self.config.convergence_threshold,
                    'aggregation_config': {
                        'min_participants': self.config.aggregation_config.min_participants,
                        'max_participants': self.config.aggregation_config.max_participants
                    }
                }
            }

            # Ejecutar transacción de registro de versión
            operations = [{
                'type': 'register_version',
                'data': {
                    'model_data': model_data,
                    'metadata': metadata,
                    'creator_node': 'pipeline_coordinator',
                    'validator_nodes': self.status.active_nodes.copy()
                }
            }]

            txn_id = await self.versioning_system.execute_transaction(
                operations,
                f"Auto-register version after round {round_num}"
            )

            logger.info(f"📝 Model version registered after round {round_num}: transaction {txn_id}")

        except Exception as e:
            logger.error(f"❌ Failed to register model version after round {round_num}: {e}")

    async def run_pipeline(self) -> Dict[str, Any]:
        """
        Ejecutar el pipeline completo de federated learning.

        Returns:
            Resultado final del pipeline
        """
        try:
            if not self.is_initialized:
                success = await self.initialize()
                if not success:
                    return {'success': False, 'error': 'Initialization failed'}

            logger.info(f"🎯 Starting federated pipeline with {len(self.status.active_nodes)} nodes")

            # Ejecutar rondas de entrenamiento
            for round_num in range(1, self.config.max_rounds + 1):
                round_result = await self.start_training_round(round_num)

                if not round_result['success']:
                    logger.warning(f"⚠️ Round {round_num} failed, continuing...")

                # Verificar convergencia (simplificada)
                if round_num >= 3:  # Verificar convergencia después de unas rondas
                    if self._check_convergence():
                        logger.info(f"🎉 Convergence reached at round {round_num}")
                        break

            # Resultado final
            final_result = {
                'success': True,
                'total_rounds': self.status.current_round,
                'final_model': self.model_state,
                'metrics_history': self.metrics_history,
                'active_nodes': len(self.status.active_nodes),
                'completed_nodes': len(self.status.completed_nodes),
                'failed_nodes': len(self.status.failed_nodes),
                'total_time': datetime.now().timestamp() - (self.status.start_time or datetime.now().timestamp())
            }

            logger.info(f"✅ Federated pipeline completed: {final_result['total_rounds']} rounds")
            return final_result

        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_rounds': self.status.current_round,
                'active_nodes': len(self.status.active_nodes)
            }

    def _check_convergence(self) -> bool:
        """
        Verificar si el modelo ha convergido.

        Returns:
            True si ha convergido
        """
        if len(self.metrics_history) < 3:
            return False

        # Verificar si la pérdida ha convergido
        recent_losses = [m['avg_loss'] for m in self.metrics_history[-3:]]
        loss_change = abs(recent_losses[-1] - recent_losses[0]) / max(recent_losses[0], 1e-8)

        return loss_change < self.config.convergence_threshold

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del pipeline.

        Returns:
            Diccionario con estado del pipeline
        """
        status = {
            'phase': self.status.phase.value,
            'current_round': self.status.current_round,
            'total_rounds': self.config.max_rounds,
            'progress': self.status.progress,
            'active_nodes': self.status.active_nodes.copy(),
            'completed_nodes': self.status.completed_nodes.copy(),
            'failed_nodes': self.status.failed_nodes.copy(),
            'is_initialized': self.is_initialized,
            'start_time': self.status.start_time,
            'last_update': self.status.last_update,
            'errors': self.status.errors.copy(),
            'metrics': self.metrics_history[-1] if self.metrics_history else None,
            'versioning_enabled': self.config.enable_versioning,
            'versioning_active': self.versioning_system is not None
        }

        # Agregar información del sistema de versionado si está activo
        if self.versioning_system:
            try:
                # Obtener información básica sin llamadas async
                total_versions = len(self.versioning_system.version_manager.registry.versions) if self.versioning_system.version_manager else 0
                active_transactions = len(self.versioning_system.active_transactions) if hasattr(self.versioning_system, 'active_transactions') else 0

                status['versioning'] = {
                    'health': self.versioning_system.system_health.value if hasattr(self.versioning_system, 'system_health') else 'unknown',
                    'active_transactions': active_transactions,
                    'total_versions': total_versions
                }
            except Exception as e:
                logger.warning(f"⚠️ Could not get versioning status: {e}")
                status['versioning'] = {'error': str(e)}

        return status

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas completas del pipeline.

        Returns:
            Diccionario con métricas
        """
        if not self.metrics_history:
            return {}

        # Calcular métricas agregadas
        total_samples = sum(m['total_samples'] for m in self.metrics_history)
        avg_loss = np.mean([m['avg_loss'] for m in self.metrics_history])
        avg_accuracy = np.mean([m['avg_accuracy'] for m in self.metrics_history])
        total_computation_time = sum(m['computation_time'] for m in self.metrics_history)

        return {
            'total_rounds': len(self.metrics_history),
            'total_samples': total_samples,
            'avg_loss': avg_loss,
            'avg_accuracy': avg_accuracy,
            'total_computation_time': total_computation_time,
            'avg_participants_per_round': np.mean([m['participants'] for m in self.metrics_history]),
            'convergence_achieved': self._check_convergence(),
            'rounds_history': self.metrics_history.copy()
        }

    def _resolve_allow_mocks(self) -> bool:
        """Resolver si se permiten mocks/simulaciones según entorno."""
        allow_env = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
        try:
            environment = get_config().environment
        except Exception:
            environment = "development"
        return allow_env or environment != "production"

    async def shutdown(self):
        """Apagar el pipeline y liberar recursos."""
        try:
            # Apagar sistema de versionado
            if self.versioning_system:
                await self.versioning_system.stop()

            # Apagar componentes de nodos
            shutdown_tasks = []
            for node_components in self.node_components.values():
                for component_name, component in node_components.items():
                    if hasattr(component, 'shutdown') and asyncio.iscoroutinefunction(component.shutdown):
                        shutdown_tasks.append(component.shutdown())
                    elif hasattr(component, 'stop') and asyncio.iscoroutinefunction(component.stop):
                        shutdown_tasks.append(component.stop())

            if shutdown_tasks:
                await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            logger.info("🛑 FederatedPipeline shutdown")
        except Exception as e:
            logger.error(f"❌ Error during pipeline shutdown: {e}")


# Funciones de conveniencia

async def create_federated_pipeline(session_id: str, enable_versioning: bool = True, **config_kwargs) -> FederatedPipeline:
    """
    Crear un pipeline federado con configuración predeterminada.

    Args:
        session_id: ID de la sesión
        enable_versioning: Habilitar sistema de versionado
        **config_kwargs: Argumentos de configuración adicionales

    Returns:
        Pipeline federado configurado
    """
    config = PipelineConfig(session_id=session_id, enable_versioning=enable_versioning, **config_kwargs)
    pipeline = FederatedPipeline(config)
    await pipeline.initialize()
    return pipeline


async def run_federated_training(session_id: str, node_configs: List[Dict[str, Any]],
                               max_rounds: int = 5) -> Dict[str, Any]:
    """
    Ejecutar entrenamiento federado completo.

    Args:
        session_id: ID de la sesión
        node_configs: Configuraciones de nodos
        max_rounds: Máximo número de rondas

    Returns:
        Resultado del entrenamiento
    """
    # Crear pipeline
    pipeline = await create_federated_pipeline(session_id, max_rounds=max_rounds)

    # Registrar nodos
    for node_config in node_configs:
        await pipeline.register_node(**node_config)

    # Ejecutar pipeline
    result = await pipeline.run_pipeline()

    # Apagar
    await pipeline.shutdown()

    return result
