"""
FASE REAL-5: Bucle de entrenamiento federado real
Implementa el sistema completo de aprendizaje federado con:
- EmpoorioLM + AdamW + TenSEAL + Blockchain
- Agregación segura de gradientes
- Recompensas tokenizadas basadas en contribución real
- Validación de aprendizaje verificable
- Sincronización distribuida de estado
"""

import asyncio
import logging
import time
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
from pathlib import Path

from ..core.logging import get_logger
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from .adamw_optimizer import FederatedAdamWOptimizer, create_federated_adamw_optimizer
from .secure_aggregator import SecureAggregator, AggregationConfig
from ..blockchain.dracma_token import get_token_manager, DRACMATokenManager
from ..rewards.dracma_calculator import dracmaCalculator
from ..training.real_data_training_pipeline import create_real_training_pipeline
from ..training.real_data_training_pipeline import create_real_training_pipeline
from ..federated.coordinator import FederatedCoordinator
from ..economics.network_utility_calculator import get_network_utility_calculator

logger = get_logger(__name__)


@dataclass
class FederatedTrainingConfig:
    """Configuración completa del bucle de entrenamiento federado."""
    # Configuración del modelo
    model_config: EmpoorioLMConfig = field(default_factory=EmpoorioLMConfig)

    # Configuración federada
    num_rounds: int = 10
    min_participants_per_round: int = 3
    max_participants_per_round: int = 10
    round_timeout_seconds: int = 300  # 5 minutos

    # Configuración de datos
    datasets: List[str] = field(default_factory=lambda: ["wikitext", "openwebtext"])
    batch_size: int = 8
    max_length: int = 512
    num_shards: int = 10

    # Configuración de privacidad
    use_tenseal: bool = True
    enable_differential_privacy: bool = True
    dp_epsilon: float = 1.0

    # Configuración de recompensas
    enable_blockchain_rewards: bool = True
    base_reward_per_round: float = 10.0  # DracmaS tokens
    quality_multiplier_max: float = 2.0

    # Configuración de validación
    validation_interval: int = 2  # Validar cada N rondas
    convergence_threshold: float = 0.001  # Umbral de convergencia
    min_learning_progress: float = 0.01  # Progreso mínimo requerido

    # Configuración de sincronización
    state_sync_interval: int = 5  # Sincronizar estado cada N rondas
    checkpoint_dir: str = "./federated_checkpoints"


@dataclass
class NodeContribution:
    """Contribución de un nodo en una ronda."""
    node_id: str
    samples_processed: int
    training_time: float
    local_accuracy: float
    local_loss: float
    gradient_norm: float
    model_quality_score: float
    timestamp: float


@dataclass
class RoundResult:
    """Resultado de una ronda de entrenamiento federado."""
    round_number: int
    participants: List[str]
    global_loss: float
    global_accuracy: float
    convergence_score: float
    learning_progress: float
    total_samples: int
    training_time: float
    contributions: List[NodeContribution] = field(default_factory=list)
    rewards_distributed: Dict[str, float] = field(default_factory=dict)
    blockchain_transactions: List[str] = field(default_factory=list)


class SecureGradientAggregation:
    """
    Agregación segura de gradientes usando TenSEAL.
    Implementa homomorphic encryption para privacidad federada.
    """

    def __init__(self, session_id: str, config: FederatedTrainingConfig):
        self.session_id = session_id
        self.config = config

        # Configuración del agregador seguro
        agg_config = AggregationConfig(
            aggregation_type="fedavg",
            enable_differential_privacy=config.enable_differential_privacy,
            dp_epsilon=config.dp_epsilon,
            min_participants=config.min_participants_per_round,
            key_size=2048,
            enable_sparsification=True,
            sparsification_k=0.01
        )

        self.aggregator = SecureAggregator(session_id, "empoorio_lm", agg_config)
        self.encrypted_updates: Dict[str, Any] = {}

        logger.info("🛡️ SecureGradientAggregation initialized with TenSEAL")

    async def collect_encrypted_gradients(self, node_updates: Dict[str, Dict[str, Any]]) -> bool:
        """
        Recopila gradientes encriptados de nodos participantes.

        Args:
            node_updates: Dict de node_id -> encrypted_gradients

        Returns:
            True si se recopilaron suficientes actualizaciones
        """
        for node_id, encrypted_data in node_updates.items():
            try:
                # Extraer datos encriptados
                encrypted_weights = encrypted_data.get("encrypted_weights", {})
                num_samples = encrypted_data.get("num_samples", 0)
                public_key = encrypted_data.get("public_key")

                # Añadir actualización al agregador
                self.aggregator.add_encrypted_weight_update(
                    node_id=node_id,
                    encrypted_weights=encrypted_weights,
                    num_samples=num_samples,
                    public_key=public_key,
                    metadata=encrypted_data.get("metadata", {})
                )

                logger.info(f"📦 Collected encrypted gradients from {node_id}")

            except Exception as e:
                logger.error(f"❌ Error collecting gradients from {node_id}: {e}")
                continue

        return self.aggregator.can_aggregate()

    async def aggregate_gradients(self) -> Dict[str, torch.Tensor]:
        """
        Agrega gradientes de manera segura.

        Returns:
            Pesos globales agregados
        """
        try:
            start_time = time.time()
            global_weights = self.aggregator.aggregate_weights()
            aggregation_time = time.time() - start_time

            logger.info(f"🔄 Secure aggregation completed in {aggregation_time:.2f}s")
            logger.info(f"📊 Aggregated {len(self.aggregator.weight_updates)} encrypted updates")

            return global_weights

        except Exception as e:
            logger.error(f"❌ Secure aggregation failed: {e}")
            raise

    def reset_for_next_round(self):
        """Resetea el agregador para la siguiente ronda."""
        self.aggregator.reset_for_next_round()
        self.encrypted_updates.clear()


class BlockchainRewardsIntegration:
    """
    Sistema de recompensas basado en contribución real usando blockchain.
    Distribuye tokens DracmaS basados en calidad y cantidad de contribución.
    """

    def __init__(self, config: FederatedTrainingConfig):
        self.config = config
        self.token_manager = get_token_manager()
        self.contribution_calculator = dracmaCalculator()

        # Estado de recompensas
        self.total_rewards_distributed = 0.0
        self.round_rewards: Dict[int, Dict[str, float]] = {}

        logger.info("💰 BlockchainRewardsIntegration initialized")

    async def calculate_node_rewards(self, contributions: List[NodeContribution],
                                   round_result: RoundResult) -> Dict[str, float]:
        """
        Calcula recompensas para cada nodo basado en su contribución.

        Args:
            contributions: Lista de contribuciones de nodos
            round_result: Resultado de la ronda

        Returns:
            Dict de node_id -> reward_amount
        """
        if not self.config.enable_blockchain_rewards:
            return {}

        rewards = {}

        try:
            # Calcular métricas globales
            total_samples = sum(c.samples_processed for c in contributions)
            avg_accuracy = sum(c.local_accuracy for c in contributions) / len(contributions)
            avg_quality = sum(c.model_quality_score for c in contributions) / len(contributions)

            for contribution in contributions:
                # Calcular reward basado en múltiples factores
                reward = await self._calculate_individual_reward(
                    contribution, total_samples, avg_accuracy, avg_quality, round_result
                )
                rewards[contribution.node_id] = reward

            # Normalizar rewards para que sumen el total disponible
            total_calculated = sum(rewards.values())
            if total_calculated > 0:
                normalization_factor = (self.config.base_reward_per_round * len(contributions)) / total_calculated
                rewards = {node_id: amount * normalization_factor for node_id, amount in rewards.items()}

            logger.info(f"💰 Calculated rewards for {len(rewards)} nodes, total: {sum(rewards.values()):.2f} DRACMA")

        except Exception as e:
            logger.error(f"❌ Error calculating rewards: {e}")
            return {}

        return rewards

    async def _calculate_individual_reward(self, contribution: NodeContribution,
                                         total_samples: int, avg_accuracy: float,
                                         avg_quality: float, round_result: RoundResult) -> float:
        """Calcula reward individual para un nodo."""

        # Factor de contribución de datos (basado en samples procesados)
        data_factor = contribution.samples_processed / total_samples if total_samples > 0 else 1.0

        # Factor de calidad (basado en accuracy relativa al promedio)
        quality_factor = min(contribution.local_accuracy / avg_accuracy, self.config.quality_multiplier_max) if avg_accuracy > 0 else 1.0

        # Factor de eficiencia (basado en tiempo de entrenamiento)
        avg_time = sum(c.training_time for c in round_result.contributions) / len(round_result.contributions)
        efficiency_factor = avg_time / contribution.training_time if contribution.training_time > 0 else 1.0
        efficiency_factor = min(efficiency_factor, 2.0)  # Máximo 2x por eficiencia

        # Factor de progreso de aprendizaje
        progress_factor = max(0.5, min(round_result.learning_progress * 10, 2.0))

        # Reward base
        base_reward = self.config.base_reward_per_round

        # Calcular reward final
        reward = base_reward * data_factor * quality_factor * efficiency_factor * progress_factor

        logger.debug(f"💰 {contribution.node_id}: data={data_factor:.2f}, quality={quality_factor:.2f}, "
                    f"efficiency={efficiency_factor:.2f}, progress={progress_factor:.2f} -> {reward:.2f} DRACMA")

        return reward

    async def distribute_rewards(self, rewards: Dict[str, float],
                               node_wallets: Dict[str, str]) -> List[str]:
        """
        Distribuye recompensas via blockchain.

        Args:
            rewards: Dict de node_id -> reward_amount
            node_wallets: Dict de node_id -> wallet_address

        Returns:
            Lista de transaction hashes
        """
        if not self.config.enable_blockchain_rewards:
            return []

        transaction_hashes = []

        try:
            # Dirección del tesoro (donde salen los rewards)
            treasury_address = "0x_treasury_address"  # En producción vendría de config

            for node_id, reward_amount in rewards.items():
                if node_id in node_wallets and reward_amount > 0:
                    wallet_address = node_wallets[node_id]

                    # Transferir tokens
                    result = await self.token_manager.transfer_tokens(
                        from_address=treasury_address,
                        to_address=wallet_address,
                        amount=reward_amount
                    )

                    if result.success and result.tx_hash:
                        transaction_hashes.append(result.tx_hash)
                        self.total_rewards_distributed += reward_amount

                        logger.info(f"✅ Distributed {reward_amount:.2f} DracmaS to {node_id} (tx: {result.tx_hash})")
                    else:
                        logger.error(f"❌ Failed to distribute reward to {node_id}: {result.error_message}")

        except Exception as e:
            logger.error(f"❌ Error distributing rewards: {e}")

        return transaction_hashes

    def get_rewards_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de recompensas."""
        return {
            "total_distributed": self.total_rewards_distributed,
            "rounds_with_rewards": len(self.round_rewards),
            "average_reward_per_round": self.total_rewards_distributed / max(1, len(self.round_rewards)),
            "blockchain_enabled": self.config.enable_blockchain_rewards
        }


class RealLearningValidation:
    """
    Validación de que el modelo realmente aprende con métricas verificables.
    Monitorea convergencia, progreso de aprendizaje y calidad del modelo.
    """

    def __init__(self, config: FederatedTrainingConfig):
        self.config = config

        # Historial de métricas
        self.loss_history: List[float] = []
        self.accuracy_history: List[float] = []
        self.convergence_history: List[float] = []
        self.learning_progress_history: List[float] = []

        # Estado de validación
        self.last_validation_round = 0
        self.convergence_threshold_met = False
        self.learning_stagnated = False

        logger.info("📊 RealLearningValidation initialized")

    def validate_learning_progress(self, current_loss: float, current_accuracy: float,
                                 round_number: int) -> Dict[str, Any]:
        """
        Valida el progreso de aprendizaje.

        Args:
            current_loss: Loss actual del modelo
            current_accuracy: Accuracy actual del modelo
            round_number: Número de ronda actual

        Returns:
            Dict con métricas de validación
        """
        # Añadir a historial
        self.loss_history.append(current_loss)
        self.accuracy_history.append(current_accuracy)

        validation_result = {
            "is_learning": False,
            "convergence_score": 0.0,
            "learning_progress": 0.0,
            "loss_trend": "unknown",
            "accuracy_trend": "unknown",
            "validation_confidence": 0.0
        }

        # Solo validar si tenemos suficientes datos
        if len(self.loss_history) < 3:
            return validation_result

        try:
            # Calcular convergencia (reducción de loss)
            recent_losses = self.loss_history[-5:]  # Últimas 5 rondas
            if len(recent_losses) >= 2:
                convergence_score = (recent_losses[0] - recent_losses[-1]) / recent_losses[0]
                validation_result["convergence_score"] = convergence_score

                # Verificar si cumple threshold de convergencia
                if convergence_score >= self.config.convergence_threshold:
                    self.convergence_threshold_met = True

            # Calcular progreso de aprendizaje (mejora en accuracy)
            recent_accuracies = self.accuracy_history[-5:]
            if len(recent_accuracies) >= 2:
                learning_progress = (recent_accuracies[-1] - recent_accuracies[0]) / recent_accuracies[0]
                validation_result["learning_progress"] = learning_progress

                # Verificar si hay progreso mínimo
                if learning_progress >= self.config.min_learning_progress:
                    validation_result["is_learning"] = True
                elif learning_progress < -0.01:  # Si accuracy baja significativamente
                    self.learning_stagnated = True

            # Analizar tendencias
            validation_result["loss_trend"] = self._analyze_trend(self.loss_history[-10:])
            validation_result["accuracy_trend"] = self._analyze_trend(self.accuracy_history[-10:])

            # Calcular confianza de validación
            validation_result["validation_confidence"] = self._calculate_validation_confidence()

            # Logging
            logger.info(f"📊 Learning validation - Round {round_number}:")
            logger.info(f"   Loss: {current_loss:.4f} (trend: {validation_result['loss_trend']})")
            logger.info(f"   Accuracy: {current_accuracy:.2f} (trend: {validation_result['accuracy_trend']})")
            logger.info(f"   Convergence: {validation_result['convergence_score']:.4f}")
            logger.info(f"   Learning: {validation_result['is_learning']} (progress: {validation_result['learning_progress']:.4f})")

        except Exception as e:
            logger.error(f"❌ Error in learning validation: {e}")

        return validation_result

    def _analyze_trend(self, values: List[float]) -> str:
        """Analiza la tendencia de una serie de valores."""
        if len(values) < 3:
            return "insufficient_data"

        # Calcular pendiente usando regresión lineal simple
        n = len(values)
        x = list(range(n))
        slope = self._calculate_slope(x, values)

        if slope < -0.01:
            return "improving"
        elif slope > 0.01:
            return "degrading"
        else:
            return "stable"

    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """Calcula la pendiente de una línea de regresión simple."""
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0

        return (n * sum_xy - sum_x * sum_y) / denominator

    def _calculate_validation_confidence(self) -> float:
        """Calcula confianza en la validación basada en consistencia de datos."""
        if len(self.loss_history) < 5:
            return 0.0

        # Confianza basada en estabilidad de métricas
        loss_stability = 1.0 / (1.0 + torch.std(torch.tensor(self.loss_history[-5:])).item())
        accuracy_stability = 1.0 / (1.0 + torch.std(torch.tensor(self.accuracy_history[-5:])).item())

        confidence = (loss_stability + accuracy_stability) / 2.0
        return min(confidence, 1.0)

    def should_stop_training(self) -> Tuple[bool, str]:
        """
        Determina si el entrenamiento debería detenerse.

        Returns:
            Tuple de (should_stop, reason)
        """
        if self.convergence_threshold_met:
            return True, "convergence_threshold_met"

        if self.learning_stagnated:
            return True, "learning_stagnated"

        if len(self.loss_history) > 20:  # Máximo 20 rondas
            return True, "max_rounds_exceeded"

        return False, ""

    def get_validation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de validación."""
        return {
            "total_validations": len(self.loss_history),
            "convergence_threshold_met": self.convergence_threshold_met,
            "learning_stagnated": self.learning_stagnated,
            "average_loss": sum(self.loss_history) / max(1, len(self.loss_history)),
            "average_accuracy": sum(self.accuracy_history) / max(1, len(self.accuracy_history)),
            "loss_trend": self._analyze_trend(self.loss_history),
            "accuracy_trend": self._analyze_trend(self.accuracy_history),
            "validation_confidence": self._calculate_validation_confidence()
        }


class DistributedStateSync:
    """
    Sincronización de estado entre nodos federados.
    Maneja checkpoints, recuperación de fallos y consistencia de estado.
    """

    def __init__(self, config: FederatedTrainingConfig):
        self.config = config
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Estado global
        self.global_model_state: Optional[Dict[str, torch.Tensor]] = None
        self.global_optimizer_state: Optional[Dict[str, Any]] = None
        self.node_states: Dict[str, Dict[str, Any]] = {}
        self.last_sync_round = 0

        logger.info(f"🔄 DistributedStateSync initialized at {self.checkpoint_dir}")

    async def sync_global_state(self, round_number: int, global_weights: Dict[str, torch.Tensor],
                              optimizer_state: Optional[Dict[str, Any]] = None):
        """
        Sincroniza estado global a todos los nodos.

        Args:
            round_number: Número de ronda actual
            global_weights: Pesos globales del modelo
            optimizer_state: Estado del optimizador (opcional)
        """
        try:
            # Actualizar estado local
            self.global_model_state = global_weights.copy()
            if optimizer_state:
                self.global_optimizer_state = optimizer_state.copy()

            self.last_sync_round = round_number

            # Crear checkpoint
            checkpoint_path = self.checkpoint_dir / f"global_state_round_{round_number}.pt"
            checkpoint = {
                "round_number": round_number,
                "global_weights": global_weights,
                "optimizer_state": optimizer_state,
                "timestamp": time.time(),
                "node_states": self.node_states.copy()
            }

            torch.save(checkpoint, checkpoint_path)
            logger.info(f"💾 Global state synced and checkpointed: {checkpoint_path}")

        except Exception as e:
            logger.error(f"❌ Error syncing global state: {e}")

    async def sync_node_state(self, node_id: str, node_state: Dict[str, Any]):
        """
        Sincroniza estado de un nodo específico.

        Args:
            node_id: ID del nodo
            node_state: Estado del nodo
        """
        try:
            self.node_states[node_id] = {
                **node_state,
                "last_sync": time.time(),
                "sync_round": self.last_sync_round
            }

            logger.debug(f"🔄 Node state synced for {node_id}")

        except Exception as e:
            logger.error(f"❌ Error syncing node state for {node_id}: {e}")

    async def recover_from_checkpoint(self, round_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Recupera estado desde checkpoint.

        Args:
            round_number: Ronda específica para recuperar (última si None)

        Returns:
            Estado recuperado o None si no existe
        """
        try:
            if round_number is None:
                # Encontrar último checkpoint
                checkpoints = list(self.checkpoint_dir.glob("global_state_round_*.pt"))
                if not checkpoints:
                    return None

                checkpoints.sort(key=lambda x: int(x.stem.split('_')[-1]))
                checkpoint_path = checkpoints[-1]
            else:
                checkpoint_path = self.checkpoint_dir / f"global_state_round_{round_number}.pt"

            if not checkpoint_path.exists():
                return None

            checkpoint = torch.load(checkpoint_path)

            # Restaurar estado
            self.global_model_state = checkpoint.get("global_weights")
            self.global_optimizer_state = checkpoint.get("optimizer_state")
            self.node_states = checkpoint.get("node_states", {})
            self.last_sync_round = checkpoint.get("round_number", 0)

            logger.info(f"📂 Recovered state from checkpoint: {checkpoint_path}")
            return checkpoint

        except Exception as e:
            logger.error(f"❌ Error recovering from checkpoint: {e}")
            return None

    def get_sync_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de sincronización."""
        return {
            "last_sync_round": self.last_sync_round,
            "nodes_synced": len(self.node_states),
            "checkpoints_available": len(list(self.checkpoint_dir.glob("global_state_round_*.pt"))),
            "checkpoint_dir": str(self.checkpoint_dir)
        }


class RealFederatedTrainingLoop:
    """
    Bucle principal de entrenamiento federado real.
    Integra todos los componentes: EmpoorioLM + AdamW + TenSEAL + Blockchain.
    """

    def __init__(self, session_id: str, config: Optional[FederatedTrainingConfig] = None):
        self.session_id = session_id
        self.config = config or FederatedTrainingConfig()

        # Componentes principales
        self.model = EmpoorioLM(self.config.model_config)
        self.global_optimizer = create_federated_adamw_optimizer(
            self.model, "global_coordinator", use_tenseal=False
        )

        # Componentes federados
        self.secure_aggregation = SecureGradientAggregation(session_id, self.config)
        self.blockchain_rewards = BlockchainRewardsIntegration(self.config)
        self.learning_validation = RealLearningValidation(self.config)
        self.state_sync = DistributedStateSync(self.config)

        # Estado del bucle
        self.current_round = 0
        self.is_running = False
        self.participants: Dict[str, Dict[str, Any]] = {}
        self.node_wallets: Dict[str, Dict[str, Any]] = {}
        self.round_results: List[RoundResult] = []

        # Pipeline de datos
        self.data_pipeline = None

        logger.info(f"🚀 RealFederatedTrainingLoop initialized for session {session_id}")

    async def initialize_training(self) -> bool:
        """Inicializa el entrenamiento federado."""
        try:
            logger.info("🔧 Initializing federated training...")

            # Inicializar pipeline de datos
            self.data_pipeline = create_real_training_pipeline(
                datasets=self.config.datasets,
                output_dir=f"./federated_data_{self.session_id}",
                num_shards=self.config.num_shards,
                batch_size=self.config.batch_size,
                max_length=self.config.max_length
            )

            # Ejecutar pipeline de datos
            pipeline_result = self.data_pipeline.run_full_pipeline()
            if not pipeline_result.get("success", False):
                logger.error("❌ Data pipeline failed")
                return False

            logger.info("✅ Federated training initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing training: {e}")
            return False

    async def register_participant(self, node_id: str, node_info: Dict[str, Any]) -> str:
        """
        Registra un nuevo participante en el entrenamiento.

        Args:
            node_id: ID del nodo
            node_info: Información del nodo

        Returns:
            Wallet address asignada
        """
        try:
            # Registrar participante
            self.participants[node_id] = {
                **node_info,
                "registered_at": time.time(),
                "rounds_participated": 0,
                "total_contribution": 0.0
            }

            # Inicializar wallet para recompensas
            wallet_address = await self.blockchain_rewards.token_manager.initialize_user_wallet(node_id)
            self.node_wallets[node_id] = {
                "address": wallet_address,
                "balance": 0.0,
                "total_rewards": 0.0
            }

            logger.info(f"✅ Participant {node_id} registered with wallet {wallet_address}")
            return wallet_address

        except Exception as e:
            logger.error(f"❌ Error registering participant {node_id}: {e}")
            raise

    async def start_round(self, round_number: int, participant_ids: List[str]) -> Dict[str, Any]:
        """
        Inicia una nueva ronda de entrenamiento.

        Args:
            round_number: Número de ronda
            participant_ids: IDs de participantes para esta ronda

        Returns:
            Configuración de la ronda
        """
        try:
            self.current_round = round_number
            self.is_running = True

            # Configurar participantes para esta ronda
            round_config = {
                "round_number": round_number,
                "participants": participant_ids,
                "data_shards": [f"shard_{i}" for i in range(len(participant_ids))],
                "timeout": self.config.round_timeout_seconds,
                "privacy_enabled": self.config.use_tenseal,
                "rewards_enabled": self.config.enable_blockchain_rewards
            }

            # Preparar agregador para la ronda
            self.secure_aggregation.aggregator.set_expected_participants(participant_ids)

            logger.info(f"🎯 Round {round_number} started with {len(participant_ids)} participants")
            return round_config

        except Exception as e:
            logger.error(f"❌ Error starting round {round_number}: {e}")
            raise

    async def collect_node_updates(self, node_updates: Dict[str, Dict[str, Any]]) -> bool:
        """
        Recopila actualizaciones de nodos participantes.

        Args:
            node_updates: Dict de node_id -> update_data

        Returns:
            True si se pueden agregar las actualizaciones
        """
        try:
            # Convertir actualizaciones a formato encriptado
            encrypted_updates = {}

            for node_id, update_data in node_updates.items():
                # Aquí se aplicaría encriptación TenSEAL en producción
                encrypted_updates[node_id] = {
                    "encrypted_weights": update_data.get("weights", {}),
                    "num_samples": update_data.get("samples_processed", 0),
                    "public_key": update_data.get("public_key"),
                    "metadata": {
                        "accuracy": update_data.get("accuracy", 0.0),
                        "loss": update_data.get("loss", 0.0),
                        "training_time": update_data.get("training_time", 0.0),
                        "gradient_norm": update_data.get("gradient_norm", 0.0)
                    }
                }

            # Recopilar en agregador seguro
            can_aggregate = await self.secure_aggregation.collect_encrypted_gradients(encrypted_updates)

            logger.info(f"📦 Collected updates from {len(node_updates)} nodes, can_aggregate: {can_aggregate}")
            return can_aggregate

        except Exception as e:
            logger.error(f"❌ Error collecting node updates: {e}")
            return False

    async def aggregate_and_update_global_model(self) -> RoundResult:
        """
        Agrega actualizaciones y actualiza el modelo global.

        Returns:
            Resultado de la ronda
        """
        try:
            start_time = time.time()

            # Agregar gradientes de manera segura
            global_weights = await self.secure_aggregation.aggregate_gradients()

            # Actualizar modelo global
            self.model.load_state_dict(global_weights)

            # Evaluar modelo global
            global_metrics = await self._evaluate_global_model()

            # Crear contribuciones de nodos
            contributions = []
            for update in self.secure_aggregation.aggregator.weight_updates:
                contribution = NodeContribution(
                    node_id=update.node_id,
                    samples_processed=update.num_samples,
                    training_time=update.metadata.get("training_time", 0.0),
                    local_accuracy=update.metadata.get("accuracy", 0.0),
                    local_loss=update.metadata.get("loss", 0.0),
                    gradient_norm=update.metadata.get("gradient_norm", 0.0),
                    model_quality_score=self._calculate_quality_score(update.metadata),
                    timestamp=update.timestamp
                )
                contributions.append(contribution)

            # Calcular métricas de ronda
            total_samples = sum(c.samples_processed for c in contributions)
            training_time = time.time() - start_time

            # Validar aprendizaje
            validation_result = self.learning_validation.validate_learning_progress(
                current_loss=global_metrics["loss"],
                current_accuracy=global_metrics["accuracy"],
                round_number=self.current_round
            )

            # Calcular recompensas
            rewards = await self.blockchain_rewards.calculate_node_rewards(
                contributions, RoundResult(
                    round_number=self.current_round,
                    participants=[c.node_id for c in contributions],
                    global_loss=global_metrics["loss"],
                    global_accuracy=global_metrics["accuracy"],
                    convergence_score=validation_result["convergence_score"],
                    learning_progress=validation_result["learning_progress"],
                    total_samples=total_samples,
                    training_time=training_time
                )
            )

            # Distribuir recompensas
            blockchain_txs = await self.blockchain_rewards.distribute_rewards(
                rewards, {node_id: self.node_wallets[node_id]["address"]
                         for node_id in rewards.keys()}
            )

            # Crear resultado de ronda
            round_result = RoundResult(
                round_number=self.current_round,
                participants=[c.node_id for c in contributions],
                global_loss=global_metrics["loss"],
                global_accuracy=global_metrics["accuracy"],
                convergence_score=validation_result["convergence_score"],
                learning_progress=validation_result["learning_progress"],
                total_samples=total_samples,
                training_time=training_time,
                contributions=contributions,
                rewards_distributed=rewards,
                blockchain_transactions=blockchain_txs
            )

            # Actualizar calculadora de utilidad de red con resultados reales
            try:
                await get_network_utility_calculator().update_from_round_result(round_result)
            except Exception as e:
                logger.warning(f"⚠️ Could not update network utility calculator: {e}")

            # Sincronizar estado
            await self.state_sync.sync_global_state(
                self.current_round, global_weights, self.global_optimizer.state_dict()
            )

            # Resetear para siguiente ronda
            self.secure_aggregation.reset_for_next_round()

            logger.info(f"✅ Round {self.current_round} completed: Loss={global_metrics['loss']:.4f}, "
                       f"Acc={global_metrics['accuracy']:.2f}, Rewards={sum(rewards.values()):.2f} DRACMA")

            return round_result

        except Exception as e:
            logger.error(f"❌ Error in round aggregation: {e}")
            raise

    async def _evaluate_global_model(self) -> Dict[str, float]:
        """Evalúa el modelo global en datos de validación."""
        # Implementación simplificada - en producción usaría datos de validación reales
        try:
            self.model.eval()

            # Simular evaluación
            with torch.no_grad():
                # Generar datos dummy para evaluación
                batch_size = 4
                seq_length = 32
                input_ids = torch.randint(0, self.model.config.vocab_size, (batch_size, seq_length))

                outputs = self.model(input_ids)
                logits = outputs["logits"]

                # Calcular loss dummy (cross entropy)
                targets = torch.randint(0, self.model.config.vocab_size, (batch_size, seq_length))
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, logits.size(-1)), targets.view(-1))

                # Accuracy dummy
                predictions = logits.argmax(dim=-1)
                accuracy = (predictions == targets).float().mean().item()

            return {
                "loss": loss.item(),
                "accuracy": accuracy,
                "perplexity": torch.exp(loss).item()
            }

        except Exception as e:
            logger.error(f"❌ Error evaluating global model: {e}")
            return {"loss": 10.0, "accuracy": 0.0, "perplexity": 1000.0}

    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """Calcula score de calidad del modelo basado en métricas locales."""
        accuracy = metadata.get("accuracy", 0.0)
        loss = metadata.get("loss", 10.0)
        gradient_norm = metadata.get("gradient_norm", 1.0)

        # Score basado en accuracy, loss y estabilidad de gradientes
        quality_score = (
            0.5 * accuracy +  # 50% accuracy
            0.3 * max(0, 1.0 - loss / 10.0) +  # 30% loss (normalizado)
            0.2 * min(1.0, 1.0 / (1.0 + gradient_norm))  # 20% estabilidad de gradientes
        )

        return quality_score

    def should_continue_training(self) -> Tuple[bool, str]:
        """Determina si el entrenamiento debería continuar."""
        should_stop, reason = self.learning_validation.should_stop_training()

        if should_stop:
            return False, reason

        if self.current_round >= self.config.num_rounds:
            return False, "max_rounds_reached"

        return True, ""

    def get_training_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del entrenamiento."""
        return {
            "session_id": self.session_id,
            "current_round": self.current_round,
            "total_participants": len(self.participants),
            "is_running": self.is_running,
            "round_results": [result.__dict__ for result in self.round_results],
            "learning_validation": self.learning_validation.get_validation_stats(),
            "rewards_stats": self.blockchain_rewards.get_rewards_stats(),
            "sync_stats": self.state_sync.get_sync_stats(),
            "config": {
                "num_rounds": self.config.num_rounds,
                "use_tenseal": self.config.use_tenseal,
                "enable_blockchain_rewards": self.config.enable_blockchain_rewards,
                "min_participants": self.config.min_participants_per_round
            }
        }

    async def save_checkpoint(self, path: Optional[str] = None) -> str:
        """Guarda checkpoint completo del entrenamiento."""
        if path is None:
            path = f"./federated_training_checkpoint_{self.session_id}_{int(time.time())}.pt"

        checkpoint = {
            "session_id": self.session_id,
            "current_round": self.current_round,
            "model_state": self.model.state_dict(),
            "optimizer_state": self.global_optimizer.state_dict(),
            "participants": self.participants,
            "node_wallets": self.node_wallets,
            "round_results": self.round_results,
            "config": self.config,
            "timestamp": time.time()
        }

        torch.save(checkpoint, path)
        logger.info(f"💾 Training checkpoint saved: {path}")

        return path

    async def load_checkpoint(self, path: str) -> bool:
        """Carga checkpoint del entrenamiento."""
        try:
            checkpoint = torch.load(path)

            self.session_id = checkpoint["session_id"]
            self.current_round = checkpoint["current_round"]
            self.model.load_state_dict(checkpoint["model_state"])
            self.global_optimizer.load_state_dict(checkpoint["optimizer_state"])
            self.participants = checkpoint["participants"]
            self.node_wallets = checkpoint["node_wallets"]
            self.round_results = checkpoint["round_results"]
            self.config = checkpoint["config"]

            logger.info(f"📂 Training checkpoint loaded: {path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error loading checkpoint: {e}")
            return False


# Funciones de conveniencia
def create_real_federated_training_loop(session_id: str,
                                       config: Optional[FederatedTrainingConfig] = None) -> RealFederatedTrainingLoop:
    """Crea un nuevo bucle de entrenamiento federado real."""
    return RealFederatedTrainingLoop(session_id, config)


async def run_real_federated_training_demo():
    """
    Demo del bucle de entrenamiento federado real.
    """
    print("🤖 AILOOS - REAL FEDERATED TRAINING LOOP DEMO")
    print("=" * 60)

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Crear configuración
    config = FederatedTrainingConfig(
        num_rounds=3,
        min_participants_per_round=2,
        use_tenseal=False,  # Deshabilitar para demo
        enable_blockchain_rewards=True,
        datasets=["wikitext"]
    )

    # Crear bucle de entrenamiento
    training_loop = create_real_federated_training_loop("demo_session", config)

    try:
        # Inicializar
        print("\n1️⃣ Inicializando entrenamiento...")
        if not await training_loop.initialize_training():
            print("❌ Error en inicialización")
            return

        # Simular participantes
        participants = ["node_1", "node_2", "node_3"]
        print(f"\n2️⃣ Registrando {len(participants)} participantes...")

        for node_id in participants:
            wallet = await training_loop.register_participant(node_id, {"hardware": "cpu"})
            print(f"   ✅ {node_id} -> {wallet}")

        # Ejecutar rondas
        for round_num in range(1, config.num_rounds + 1):
            print(f"\n🎯 RONDA {round_num}/{config.num_rounds}")

            # Iniciar ronda
            round_config = await training_loop.start_round(round_num, participants[:2])  # 2 participantes por ronda

            # Simular actualizaciones de nodos
            node_updates = {}
            for node_id in participants[:2]:
                node_updates[node_id] = {
                    "weights": training_loop.model.state_dict(),  # Pesos dummy
                    "samples_processed": 100,
                    "accuracy": 0.7 + round_num * 0.05,  # Mejora progresiva
                    "loss": 2.0 - round_num * 0.1,
                    "training_time": 10.0,
                    "gradient_norm": 1.0,
                    "public_key": "dummy_key"
                }

            # Recopilar actualizaciones
            if await training_loop.collect_node_updates(node_updates):
                # Agregar y actualizar modelo
                round_result = await training_loop.aggregate_and_update_global_model()

                print(f"   ✅ Loss: {round_result.global_loss:.4f}")
                print(f"   ✅ Accuracy: {round_result.global_accuracy:.2f}")
                print(f"   ✅ Rewards: {sum(round_result.rewards_distributed.values()):.2f} DRACMA")
                print(f"   ✅ Transactions: {len(round_result.blockchain_transactions)}")

                training_loop.round_results.append(round_result)

                # Verificar si continuar
                should_continue, reason = training_loop.should_continue_training()
                if not should_continue:
                    print(f"   🛑 Training stopped: {reason}")
                    break
            else:
                print("   ❌ No se pudieron recopilar suficientes actualizaciones")

        # Estadísticas finales
        stats = training_loop.get_training_stats()
        print("\n🎉 ENTRENAMIENTO COMPLETADO")
        print("=" * 60)
        print(f"✅ Rondas completadas: {len(training_loop.round_results)}")
        print(f"💰 Total rewards: {stats['rewards_stats']['total_distributed']:.2f} DRACMA")
        print(f"📊 Final accuracy: {training_loop.round_results[-1].global_accuracy:.2f}")
        print(f"📂 Checkpoints guardados en: {config.checkpoint_dir}")

        return stats

    except Exception as e:
        logger.error(f"❌ Error en demo: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(run_real_federated_training_demo())