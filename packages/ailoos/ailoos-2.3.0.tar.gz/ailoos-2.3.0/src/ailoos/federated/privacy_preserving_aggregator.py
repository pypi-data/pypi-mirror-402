"""
Privacy Preserving Aggregator - Agregación segura de actualizaciones del modelo
Implementa agregación federada con privacidad diferencial y encriptación homomórfica.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import torch
import numpy as np

from ..core.logging import get_logger
from .secure_aggregator import SecureAggregator, AggregationConfig, EncryptedWeightUpdate
from .homomorphic_encryptor import HomomorphicEncryptor

logger = get_logger(__name__)


@dataclass
class AggregationResult:
    """Resultado de una agregación."""
    global_weights: Dict[str, torch.Tensor]
    num_participants: int
    aggregation_method: str
    privacy_level: str
    computation_time: float
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeUpdate:
    """Actualización de un nodo."""
    node_id: str
    weights: Dict[str, torch.Tensor]
    num_samples: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class PrivacyPreservingAggregator:
    """
    Agregador que preserva privacidad usando encriptación homomórfica
    y privacidad diferencial para federated learning.
    """

    def __init__(self, session_id: str, model_name: str,
                 config: Optional[AggregationConfig] = None,
                 encryptor: Optional[HomomorphicEncryptor] = None):
        """
        Inicializar el agregador con preservación de privacidad.

        Args:
            session_id: ID de la sesión federada
            model_name: Nombre del modelo
            config: Configuración de agregación
            encryptor: Encriptador homomórfico (opcional)
        """
        self.session_id = session_id
        self.model_name = model_name
        self.config = config or AggregationConfig()

        # Componentes subyacentes
        self.secure_aggregator = SecureAggregator(session_id, model_name, self.config)
        self.encryptor = encryptor

        # Estado del agregador
        self.is_initialized = False
        self.pending_updates: List[NodeUpdate] = []
        self.aggregation_history: List[AggregationResult] = []
        self.current_round = 0

        # Estadísticas
        self.stats = {
            'total_aggregations': 0,
            'total_participants': 0,
            'avg_computation_time': 0.0,
            'privacy_violations': 0,
            'encryption_failures': 0,
            'success_rate': 1.0
        }

        logger.info(f"🛡️ PrivacyPreservingAggregator initialized for session {session_id}")

    def initialize(self):
        """Inicializar componentes."""
        self.secure_aggregator.set_expected_participants([])  # Se configurará dinámicamente
        if self.encryptor:
            self.encryptor.initialize()
        self.is_initialized = True
        logger.info(f"✅ PrivacyPreservingAggregator initialized for session {self.session_id}")

    async def submit_node_update(self, node_id: str, weights: Dict[str, torch.Tensor],
                               num_samples: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enviar actualización de un nodo para agregación.

        Args:
            node_id: ID del nodo
            weights: Pesos del modelo actualizados
            num_samples: Número de muestras locales
            metadata: Metadatos adicionales

        Returns:
            True si la actualización fue aceptada
        """
        try:
            # Validar actualización
            if not self._validate_update(weights, num_samples):
                logger.warning(f"⚠️ Invalid update from node {node_id}")
                return False

            # Crear objeto de actualización
            update = NodeUpdate(
                node_id=node_id,
                weights=weights,
                num_samples=num_samples,
                metadata=metadata or {},
                timestamp=datetime.now().timestamp()
            )

            self.pending_updates.append(update)

            # Si tenemos suficientes actualizaciones, proceder con agregación
            if self._should_aggregate():
                await self._perform_aggregation()

            logger.info(f"📨 Accepted update from node {node_id} ({num_samples} samples)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to submit update from node {node_id}: {e}")
            return False

    def _validate_update(self, weights: Dict[str, torch.Tensor], num_samples: int) -> bool:
        """
        Validar una actualización de nodo.

        Args:
            weights: Pesos del modelo
            num_samples: Número de muestras

        Returns:
            True si la actualización es válida
        """
        try:
            # Validaciones básicas
            if not weights:
                return False

            if num_samples <= 0:
                return False

            # Verificar que los tensores sean válidos
            for name, weight in weights.items():
                if weight is None:
                    continue
                if not isinstance(weight, torch.Tensor):
                    return False
                if not torch.isfinite(weight).all():
                    return False

            return True

        except Exception:
            return False

    def _should_aggregate(self) -> bool:
        """
        Determinar si se debe proceder con la agregación.

        Returns:
            True si se debe agregar
        """
        # Lógica simple: agregar cuando tengamos al menos el mínimo requerido
        return len(self.pending_updates) >= self.config.min_participants

    async def _perform_aggregation(self):
        """Realizar agregación de actualizaciones pendientes."""
        try:
            start_time = datetime.now()

            # Preparar participantes
            participant_ids = [update.node_id for update in self.pending_updates]
            self.secure_aggregator.set_expected_participants(participant_ids)

            # Convertir actualizaciones a formato del secure aggregator
            encrypted_updates = []
            for update in self.pending_updates:
                # Encriptar pesos si tenemos encriptador
                if self.encryptor:
                    try:
                        encrypted_weights = self.encryptor.encrypt_gradients(update.weights)
                        public_key = self.encryptor.get_public_key()
                    except Exception as e:
                        logger.warning(f"⚠️ Encryption failed for node {update.node_id}: {e}")
                        self.stats['encryption_failures'] += 1
                        # Continuar sin encriptación
                        encrypted_weights = update.weights
                        public_key = None
                else:
                    encrypted_weights = update.weights
                    public_key = None

                # Crear actualización encriptada
                enc_update = EncryptedWeightUpdate(
                    node_id=update.node_id,
                    encrypted_weights=encrypted_weights,
                    num_samples=update.num_samples,
                    public_key=public_key,
                    metadata=update.metadata,
                    timestamp=update.timestamp
                )
                encrypted_updates.append(enc_update)

            # Enviar actualizaciones al secure aggregator
            for enc_update in encrypted_updates:
                self.secure_aggregator.add_encrypted_weight_update(
                    node_id=enc_update.node_id,
                    encrypted_weights=enc_update.encrypted_weights,
                    num_samples=enc_update.num_samples,
                    public_key=enc_update.public_key,
                    metadata=enc_update.metadata
                )

            # Realizar agregación
            if self.secure_aggregator.can_aggregate():
                global_weights = self.secure_aggregator.aggregate_weights()

                # Calcular tiempo de computación
                computation_time = (datetime.now() - start_time).total_seconds()

                # Crear resultado
                result = AggregationResult(
                    global_weights=global_weights,
                    num_participants=len(self.pending_updates),
                    aggregation_method=self.config.aggregation_type,
                    privacy_level="encrypted_dp" if self.encryptor else "differential_privacy",
                    computation_time=computation_time,
                    success=True,
                    metadata={
                        'round': self.current_round,
                        'session_id': self.session_id,
                        'participants': participant_ids
                    }
                )

                self.aggregation_history.append(result)

                # Actualizar estadísticas
                self.stats['total_aggregations'] += 1
                self.stats['total_participants'] += len(self.pending_updates)
                self.stats['avg_computation_time'] = (
                    (self.stats['avg_computation_time'] * (self.stats['total_aggregations'] - 1)) +
                    computation_time
                ) / self.stats['total_aggregations']

                # Limpiar actualizaciones procesadas
                self.pending_updates.clear()
                self.secure_aggregator.reset_for_next_round()
                self.current_round += 1

                logger.info(f"✅ Aggregation completed: {len(participant_ids)} participants, {computation_time:.2f}s")

            else:
                logger.info("⏳ Waiting for more updates before aggregation")

        except Exception as e:
            logger.error(f"❌ Aggregation failed: {e}")

            # Crear resultado de error
            error_result = AggregationResult(
                global_weights={},
                num_participants=len(self.pending_updates),
                aggregation_method=self.config.aggregation_type,
                privacy_level="failed",
                computation_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=str(e)
            )
            self.aggregation_history.append(error_result)

            # Limpiar actualizaciones fallidas
            self.pending_updates.clear()

    async def get_global_model(self) -> Optional[Dict[str, torch.Tensor]]:
        """
        Obtener el modelo global más reciente.

        Returns:
            Pesos del modelo global o None si no hay resultados
        """
        if not self.aggregation_history:
            return None

        latest_result = self.aggregation_history[-1]
        return latest_result.global_weights if latest_result.success else None

    def get_aggregation_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la agregación.

        Returns:
            Diccionario con estado
        """
        latest_result = self.aggregation_history[-1] if self.aggregation_history else None

        return {
            'session_id': self.session_id,
            'model_name': self.model_name,
            'current_round': self.current_round,
            'pending_updates': len(self.pending_updates),
            'min_participants': self.config.min_participants,
            'can_aggregate': self._should_aggregate(),
            'is_initialized': self.is_initialized,
            'latest_aggregation': {
                'success': latest_result.success if latest_result else None,
                'num_participants': latest_result.num_participants if latest_result else 0,
                'computation_time': latest_result.computation_time if latest_result else 0,
                'timestamp': latest_result.metadata.get('timestamp') if latest_result else None
            } if latest_result else None,
            'config': {
                'aggregation_type': self.config.aggregation_type,
                'enable_dp': self.config.enable_differential_privacy,
                'min_participants': self.config.min_participants,
                'encryption_enabled': self.encryptor is not None
            }
        }

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas de agregación.

        Returns:
            Diccionario con estadísticas
        """
        return {
            'session_id': self.session_id,
            'total_aggregations': self.stats['total_aggregations'],
            'total_participants': self.stats['total_participants'],
            'avg_computation_time': self.stats['avg_computation_time'],
            'privacy_violations': self.stats['privacy_violations'],
            'encryption_failures': self.stats['encryption_failures'],
            'success_rate': self.stats['success_rate'],
            'current_round': self.current_round,
            'pending_updates': len(self.pending_updates),
            'aggregation_history_length': len(self.aggregation_history),
            'secure_aggregator_stats': self.secure_aggregator.get_aggregation_stats() if hasattr(self.secure_aggregator, 'get_aggregation_stats') else {}
        }

    def get_aggregation_history(self) -> List[Dict[str, Any]]:
        """
        Obtener historial de agregaciones.

        Returns:
            Lista de resultados de agregación
        """
        return [
            {
                'round': i,
                'success': result.success,
                'num_participants': result.num_participants,
                'computation_time': result.computation_time,
                'method': result.aggregation_method,
                'privacy_level': result.privacy_level,
                'error_message': result.error_message,
                'timestamp': result.metadata.get('timestamp', result.metadata.get('round_start_time'))
            }
            for i, result in enumerate(self.aggregation_history)
        ]

    async def force_aggregation(self) -> Optional[AggregationResult]:
        """
        Forzar agregación incluso si no se cumple el mínimo de participantes.

        Returns:
            Resultado de agregación o None si falla
        """
        try:
            if not self.pending_updates:
                logger.warning("⚠️ No pending updates to aggregate")
                return None

            # Temporarily reduce min participants
            original_min = self.config.min_participants
            self.config.min_participants = len(self.pending_updates)

            await self._perform_aggregation()

            # Restore original minimum
            self.config.min_participants = original_min

            # Return latest result
            return self.aggregation_history[-1] if self.aggregation_history else None

        except Exception as e:
            logger.error(f"❌ Forced aggregation failed: {e}")
            return None

    def reset_for_new_session(self, new_session_id: Optional[str] = None):
        """
        Resetear agregador para nueva sesión.

        Args:
            new_session_id: Nuevo ID de sesión (opcional)
        """
        if new_session_id:
            self.session_id = new_session_id

        self.pending_updates.clear()
        self.aggregation_history.clear()
        self.current_round = 0
        self.secure_aggregator.reset_for_next_round()

        # Resetear estadísticas
        self.stats = {
            'total_aggregations': 0,
            'total_participants': 0,
            'avg_computation_time': 0.0,
            'privacy_violations': 0,
            'encryption_failures': 0,
            'success_rate': 1.0
        }

        logger.info(f"🔄 Aggregator reset for session {self.session_id}")

    def set_encryption_enabled(self, enabled: bool):
        """
        Habilitar/deshabilitar encriptación.

        Args:
            enabled: True para habilitar encriptación
        """
        if enabled and not self.encryptor:
            logger.warning("⚠️ Cannot enable encryption: no encryptor provided")
        elif not enabled:
            self.encryptor = None
            logger.info("🔓 Encryption disabled")

        logger.info(f"🔐 Encryption {'enabled' if enabled else 'disabled'}")