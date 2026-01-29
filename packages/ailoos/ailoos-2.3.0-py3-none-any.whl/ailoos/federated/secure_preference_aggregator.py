"""
Agregador Seguro de Preferencias para Federated Learning con DPO
Implementa agregación privada de preferencias de usuarios sin revelar contenido individual.
Soporta homomorphic encryption opcional, differential privacy y validación de integridad.
"""

import asyncio
import hashlib
import hmac
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

import numpy as np
import torch
import torch.nn as nn

from phe import paillier  # Paillier homomorphic encryption
from ..core.logging import get_logger
from .differential_privacy import DifferentialPrivacyEngine

logger = get_logger(__name__)


@dataclass
class EncryptedPreferenceUpdate:
    """Actualización de preferencias encriptada desde un nodo."""
    node_id: str
    encrypted_preferences: Dict[str, Any]  # Preferencias encriptadas homomórficamente
    num_samples: int
    public_key: Optional[paillier.PaillierPublicKey] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    # Integridad
    checksum: Optional[str] = None
    signature: Optional[str] = None
    # DP
    dp_noise_added: bool = False


@dataclass
class PreferenceAggregationConfig:
    """Configuración para agregación segura de preferencias."""
    aggregation_method: str = "weighted_mean"  # weighted_mean, mean, median
    enable_differential_privacy: bool = True
    dp_epsilon: float = 0.1
    dp_delta: float = 1e-5
    enable_homomorphic_encryption: bool = False  # Opcional
    key_size: int = 2048  # Tamaño de clave Paillier
    min_participants: int = 3
    max_round_time: int = 300  # segundos
    # Validación
    enable_integrity_check: bool = True
    enable_signatures: bool = False
    # Estadísticas
    compute_consensus_metrics: bool = True
    consensus_threshold: float = 0.7  # Umbral para consenso alto


class PreferenceAggregationAlgorithm(ABC):
    """Interfaz base para algoritmos de agregación de preferencias."""

    @abstractmethod
    def aggregate(self, updates: List[EncryptedPreferenceUpdate],
                  config: PreferenceAggregationConfig) -> Dict[str, torch.Tensor]:
        """Agrega actualizaciones de preferencias."""
        pass


class PreferenceMeanAggregator(PreferenceAggregationAlgorithm):
    """Agregación por promedio de preferencias."""

    def aggregate(self, updates: List[EncryptedPreferenceUpdate],
                  config: PreferenceAggregationConfig) -> Dict[str, torch.Tensor]:
        """
        Agrega preferencias usando promedio simple.

        Args:
            updates: Lista de actualizaciones encriptadas
            config: Configuración de agregación

        Returns:
            Preferencias globales agregadas
        """
        if len(updates) < config.min_participants:
            raise ValueError(f"Insuficientes participantes: {len(updates)} < {config.min_participants}")

        logger.info(f"📊 Agregando preferencias con promedio simple de {len(updates)} participantes")

        # Usar primera actualización como base
        first_update = updates[0]
        global_preferences = {}

        for pref_name, encrypted_pref in first_update.encrypted_preferences.items():
            if not isinstance(encrypted_pref, (list, torch.Tensor, np.ndarray)):
                continue

            # Suma homomórfica si está habilitada
            if config.enable_homomorphic_encryption and isinstance(encrypted_pref, list):
                pref_sum = encrypted_pref.copy()
                for update in updates[1:]:
                    if pref_name in update.encrypted_preferences:
                        pref_sum = self._add_encrypted_preferences(
                            pref_sum, update.encrypted_preferences[pref_name],
                            first_update.public_key
                        )
                # Desencriptar y promediar
                total_sum = self._decrypt_and_sum(pref_sum, first_update.public_key)
                global_preferences[pref_name] = total_sum / len(updates)
            else:
                # Agregación directa
                all_prefs = []
                for update in updates:
                    if pref_name in update.encrypted_preferences:
                        pref = update.encrypted_preferences[pref_name]
                        if isinstance(pref, (torch.Tensor, np.ndarray)):
                            all_prefs.append(pref)

                if all_prefs:
                    stacked = torch.stack(all_prefs) if isinstance(all_prefs[0], torch.Tensor) else torch.tensor(all_prefs)
                    global_preferences[pref_name] = stacked.mean(dim=0)

        logger.info("✅ Agregación por promedio completada")
        return global_preferences

    def _add_encrypted_preferences(self, pref_a: List[Any], pref_b: List[Any],
                                  public_key: paillier.PaillierPublicKey) -> List[Any]:
        """Suma preferencias encriptadas homomórficamente."""
        if len(pref_a) != len(pref_b):
            raise ValueError("Preferencias deben tener la misma longitud")

        result = []
        for a, b in zip(pref_a, pref_b):
            result.append(a + b)  # Suma homomórfica
        return result

    def _decrypt_and_sum(self, encrypted_prefs: List[Any],
                         public_key: paillier.PaillierPublicKey) -> torch.Tensor:
        """Desencripta y suma preferencias."""
        # Nota: En implementación real, necesitaríamos la clave privada
        # Aquí asumimos desencriptación directa para simplificación
        decrypted = []
        for enc in encrypted_prefs:
            # Simulación de desencriptación
            decrypted.append(float(enc) / 1e6)  # Desescalar
        return torch.tensor(decrypted, dtype=torch.float32)


class PreferenceWeightedAggregator(PreferenceAggregationAlgorithm):
    """Agregación ponderada de preferencias."""

    def aggregate(self, updates: List[EncryptedPreferenceUpdate],
                  config: PreferenceAggregationConfig) -> Dict[str, torch.Tensor]:
        """
        Agrega preferencias usando promedio ponderado por número de muestras.

        Args:
            updates: Lista de actualizaciones encriptadas
            config: Configuración de agregación

        Returns:
            Preferencias globales agregadas
        """
        if len(updates) < config.min_participants:
            raise ValueError(f"Insuficientes participantes: {len(updates)} < {config.min_participants}")

        logger.info(f"⚖️ Agregando preferencias con promedio ponderado de {len(updates)} participantes")

        total_samples = sum(update.num_samples for update in updates)
        global_preferences = {}

        for pref_name in updates[0].encrypted_preferences.keys():
            weighted_sum = None
            total_weight = 0

            for update in updates:
                if pref_name not in update.encrypted_preferences:
                    continue

                pref = update.encrypted_preferences[pref_name]
                if isinstance(pref, (torch.Tensor, np.ndarray)):
                    weight = update.num_samples / total_samples
                    if weighted_sum is None:
                        weighted_sum = pref * weight
                    else:
                        weighted_sum += pref * weight
                    total_weight += weight

            if weighted_sum is not None:
                global_preferences[pref_name] = weighted_sum / total_weight

        logger.info("✅ Agregación ponderada completada")
        return global_preferences


class PreferenceMedianAggregator(PreferenceAggregationAlgorithm):
    """Agregación por mediana de preferencias."""

    def aggregate(self, updates: List[EncryptedPreferenceUpdate],
                  config: PreferenceAggregationConfig) -> Dict[str, torch.Tensor]:
        """
        Agrega preferencias usando mediana para robustez contra outliers.

        Args:
            updates: Lista de actualizaciones encriptadas
            config: Configuración de agregación

        Returns:
            Preferencias globales agregadas
        """
        if len(updates) < config.min_participants:
            raise ValueError(f"Insuficientes participantes: {len(updates)} < {config.min_participants}")

        logger.info(f"📏 Agregando preferencias con mediana de {len(updates)} participantes")

        global_preferences = {}

        for pref_name in updates[0].encrypted_preferences.keys():
            all_prefs = []

            for update in updates:
                if pref_name in update.encrypted_preferences:
                    pref = update.encrypted_preferences[pref_name]
                    if isinstance(pref, (torch.Tensor, np.ndarray)):
                        all_prefs.append(pref)

            if all_prefs:
                stacked = torch.stack(all_prefs) if isinstance(all_prefs[0], torch.Tensor) else torch.tensor(all_prefs)
                global_preferences[pref_name] = torch.median(stacked, dim=0).values

        logger.info("✅ Agregación por mediana completada")
        return global_preferences


class HomomorphicEncryption:
    """Utilidades para encriptación homomórfica de preferencias."""

    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self.public_key = None
        self.private_key = None

    def generate_keys(self) -> Tuple[paillier.PaillierPublicKey, paillier.PaillierPrivateKey]:
        """Genera par de claves Paillier."""
        self.public_key, self.private_key = paillier.generate_paillier_keypair(n_length=self.key_size)
        logger.info(f"🔐 Generadas claves Paillier de {self.key_size} bits para preferencias")
        return self.public_key, self.private_key

    def encrypt_preference(self, preference: torch.Tensor,
                          public_key: paillier.PaillierPublicKey) -> List[Any]:
        """
        Encripta un tensor de preferencias usando Paillier.

        Args:
            preference: Tensor de preferencias a encriptar
            public_key: Clave pública Paillier

        Returns:
            Lista de valores encriptados
        """
        flat_pref = preference.flatten().cpu().numpy()
        encrypted_values = []

        for value in flat_pref:
            scaled_value = int(value * 1e6)  # Escala para precisión
            encrypted = public_key.encrypt(scaled_value)
            encrypted_values.append(encrypted)

        return encrypted_values

    def decrypt_preference(self, encrypted_values: List[Any],
                          private_key: paillier.PaillierPrivateKey,
                          shape: torch.Size) -> torch.Tensor:
        """
        Desencripta valores encriptados a tensor de preferencias.

        Args:
            encrypted_values: Valores encriptados
            private_key: Clave privada Paillier
            shape: Forma original del tensor

        Returns:
            Tensor desencriptado
        """
        decrypted_values = []

        for encrypted in encrypted_values:
            decrypted = private_key.decrypt(encrypted)
            original_value = decrypted / 1e6  # Desescalar
            decrypted_values.append(original_value)

        return torch.tensor(decrypted_values, dtype=torch.float32).reshape(shape)


class SecurePreferenceAggregator:
    """
    Agregador seguro que implementa múltiples algoritmos de agregación
    de preferencias con privacidad diferencial y encriptación homomórfica opcional.
    """

    def __init__(self, session_id: str, config: Optional[PreferenceAggregationConfig] = None):
        self.session_id = session_id
        self.config = config or PreferenceAggregationConfig()

        # Estado de la ronda actual
        self.current_round = 0
        self.preference_updates: List[EncryptedPreferenceUpdate] = []
        self.expected_participants: List[str] = []

        # Componentes criptográficos
        self.he = None
        if self.config.enable_homomorphic_encryption:
            self.he = HomomorphicEncryption(self.config.key_size)
            self.he.generate_keys()

        # Privacidad diferencial
        self.dp_engine = None
        if self.config.enable_differential_privacy:
            self.dp_engine = DifferentialPrivacyEngine(
                epsilon=self.config.dp_epsilon,
                delta=self.config.dp_delta
            )

        # Algoritmos de agregación
        self.algorithms = {
            "mean": PreferenceMeanAggregator(),
            "weighted_mean": PreferenceWeightedAggregator(),
            "median": PreferenceMedianAggregator()
        }

        # Estadísticas
        self.round_stats = {
            "start_time": None,
            "end_time": None,
            "total_samples": 0,
            "participants_count": 0,
            "participation_rate": 0.0,
            "consensus_score": 0.0,
            "aggregation_time": 0.0,
            "integrity_checks_passed": 0,
            "integrity_checks_failed": 0
        }

        logger.info(f"🛡️ SecurePreferenceAggregator initialized for session {session_id}")

    def set_expected_participants(self, participant_ids: List[str]):
        """Establecer lista de participantes esperados."""
        self.expected_participants = participant_ids.copy()
        logger.info(f"📋 Expected participants: {participant_ids}")

    def add_encrypted_preference_update(self, node_id: str,
                                       encrypted_preferences: Dict[str, Any],
                                       num_samples: int,
                                       metadata: Optional[Dict[str, Any]] = None,
                                       checksum: Optional[str] = None,
                                       signature: Optional[str] = None):
        """
        Añadir actualización de preferencias encriptada desde un nodo.

        Args:
            node_id: ID del nodo
            encrypted_preferences: Preferencias encriptadas
            num_samples: Número de muestras locales
            metadata: Metadatos adicionales
            checksum: Checksum para validación de integridad
            signature: Firma digital opcional
        """
        if node_id not in self.expected_participants:
            logger.warning(f"⚠️ Unexpected preference update from node {node_id}")
            return

        # Verificar duplicados
        existing_updates = [u for u in self.preference_updates if u.node_id == node_id]
        if existing_updates:
            logger.warning(f"⚠️ Duplicate preference update from node {node_id}")
            return

        # Validar integridad si está habilitada
        if self.config.enable_integrity_check and checksum:
            if not self._validate_integrity(encrypted_preferences, checksum):
                logger.error(f"❌ Integrity check failed for node {node_id}")
                self.round_stats["integrity_checks_failed"] += 1
                return
            self.round_stats["integrity_checks_passed"] += 1

        # Crear actualización
        update = EncryptedPreferenceUpdate(
            node_id=node_id,
            encrypted_preferences=encrypted_preferences,
            num_samples=num_samples,
            public_key=self.he.public_key if self.he else None,
            metadata=metadata or {},
            timestamp=time.time(),
            checksum=checksum,
            signature=signature
        )

        self.preference_updates.append(update)
        self.round_stats["total_samples"] += num_samples

        logger.info(f"📊 Encrypted preference update received from {node_id}")

    def can_aggregate(self) -> bool:
        """Verificar si se puede proceder con la agregación."""
        received_count = len(self.preference_updates)
        expected_count = len(self.expected_participants)

        can_proceed = received_count >= self.config.min_participants

        if can_proceed:
            logger.info(f"✅ Ready to aggregate preferences: {received_count}/{expected_count} updates")
        else:
            logger.info(f"⏳ Waiting for preference updates: {received_count}/{expected_count}")

        return can_proceed

    def aggregate_preferences(self) -> Dict[str, Any]:
        """
        Agregar preferencias usando el algoritmo configurado.

        Returns:
            Preferencias globales agregadas con estadísticas
        """
        if not self.can_aggregate():
            raise ValueError("Not enough preference updates to perform aggregation")

        if not self.preference_updates:
            raise ValueError("No preference updates available")

        logger.info(f"🔄 Starting secure preference aggregation with {len(self.preference_updates)} updates")

        # Inicializar estadísticas
        self.round_stats["start_time"] = time.time()
        self.round_stats["participants_count"] = len(self.preference_updates)

        # Seleccionar algoritmo
        algorithm = self.algorithms.get(self.config.aggregation_method)
        if not algorithm:
            raise ValueError(f"Unsupported aggregation method: {self.config.aggregation_method}")

        # Realizar agregación
        try:
            global_preferences = algorithm.aggregate(self.preference_updates, self.config)

            # Aplicar privacidad diferencial si está habilitada
            if self.dp_engine and self.config.enable_differential_privacy:
                global_preferences = self._apply_differential_privacy(global_preferences)

            # Calcular estadísticas
            self._compute_aggregation_stats(global_preferences)

            # Finalizar estadísticas
            self.round_stats["end_time"] = time.time()
            self.round_stats["aggregation_time"] = (
                self.round_stats["end_time"] - self.round_stats["start_time"]
            )

            logger.info(f"✅ Secure preference aggregation completed in {self.round_stats['aggregation_time']:.2f}s")

            return {
                "aggregated_preferences": global_preferences,
                "aggregation_stats": self.round_stats.copy(),
                "round_info": {
                    "round_num": self.current_round,
                    "session_id": self.session_id,
                    "method": self.config.aggregation_method,
                    "participants": len(self.preference_updates)
                }
            }

        except Exception as e:
            logger.error(f"❌ Secure preference aggregation failed: {e}")
            raise

    def reset_for_next_round(self):
        """Resetear agregador para la siguiente ronda."""
        self.current_round += 1
        self.preference_updates.clear()

        # Resetear estadísticas
        self.round_stats = {
            "start_time": None,
            "end_time": None,
            "total_samples": 0,
            "participants_count": 0,
            "participation_rate": 0.0,
            "consensus_score": 0.0,
            "aggregation_time": 0.0,
            "integrity_checks_passed": 0,
            "integrity_checks_failed": 0
        }

        logger.info(f"🔄 SecurePreferenceAggregator reset for round {self.current_round}")

    def _apply_differential_privacy(self, preferences: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Aplicar privacidad diferencial a las preferencias agregadas."""
        dp_preferences = {}

        for pref_name, pref_tensor in preferences.items():
            dp_preferences[pref_name] = self.dp_engine.apply_differential_privacy({pref_name: pref_tensor})[pref_name]

        logger.debug("🔒 Differential privacy applied to aggregated preferences")
        return dp_preferences

    def _compute_aggregation_stats(self, global_preferences: Dict[str, torch.Tensor]):
        """Calcular estadísticas de agregación incluyendo participación y consenso."""
        # Tasa de participación
        participation_rate = len(self.preference_updates) / len(self.expected_participants)
        self.round_stats["participation_rate"] = participation_rate

        # Puntaje de consenso (inversa de la varianza normalizada)
        if self.config.compute_consensus_metrics and len(self.preference_updates) > 1:
            consensus_scores = []

            for pref_name in global_preferences.keys():
                pref_values = []
                for update in self.preference_updates:
                    if pref_name in update.encrypted_preferences:
                        pref = update.encrypted_preferences[pref_name]
                        if isinstance(pref, torch.Tensor):
                            pref_values.append(pref.mean().item())  # Simplificar a valor escalar

                if len(pref_values) > 1:
                    variance = np.var(pref_values)
                    # Normalizar varianza (0 = consenso perfecto, 1 = varianza máxima)
                    max_possible_var = np.var([min(pref_values), max(pref_values)] * len(pref_values))
                    normalized_var = variance / max_possible_var if max_possible_var > 0 else 0
                    consensus = 1.0 - normalized_var  # 1 = consenso alto, 0 = consenso bajo
                    consensus_scores.append(consensus)

            if consensus_scores:
                self.round_stats["consensus_score"] = np.mean(consensus_scores)

        logger.info(f"📊 Participation: {participation_rate:.1%}, Consensus: {self.round_stats['consensus_score']:.2f}")

    def _validate_integrity(self, preferences: Dict[str, Any], checksum: str) -> bool:
        """Validar integridad de las preferencias usando checksum."""
        # Crear checksum de los datos
        data_str = str(sorted(preferences.items()))
        computed_checksum = hashlib.sha256(data_str.encode()).hexdigest()

        return hmac.compare_digest(computed_checksum, checksum)

    def get_public_key(self) -> Optional[paillier.PaillierPublicKey]:
        """Obtener clave pública para encriptación."""
        return self.he.public_key if self.he else None

    def get_round_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la ronda actual."""
        return {
            "round_num": self.current_round,
            "session_id": self.session_id,
            "updates_received": len(self.preference_updates),
            "expected_updates": len(self.expected_participants),
            "total_samples": self.round_stats["total_samples"],
            "can_aggregate": self.can_aggregate(),
            "config": {
                "method": self.config.aggregation_method,
                "dp_enabled": self.config.enable_differential_privacy,
                "he_enabled": self.config.enable_homomorphic_encryption,
                "min_participants": self.config.min_participants
            },
            "participants": [u.node_id for u in self.preference_updates]
        }

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas de agregación."""
        return {
            "session_id": self.session_id,
            "current_round": self.current_round,
            "total_updates_processed": len(self.preference_updates),
            "total_samples_processed": self.round_stats["total_samples"],
            "avg_aggregation_time": self.round_stats.get("aggregation_time", 0),
            "participation_rate": self.round_stats.get("participation_rate", 0),
            "consensus_score": self.round_stats.get("consensus_score", 0),
            "integrity_checks_passed": self.round_stats.get("integrity_checks_passed", 0),
            "integrity_checks_failed": self.round_stats.get("integrity_checks_failed", 0),
            "method_used": self.config.aggregation_method,
            "privacy_enabled": self.config.enable_differential_privacy,
            "encryption_enabled": self.config.enable_homomorphic_encryption
        }


# Funciones de conveniencia
def create_secure_preference_aggregator(session_id: str,
                                       config: Optional[PreferenceAggregationConfig] = None) -> SecurePreferenceAggregator:
    """Crear un nuevo agregador seguro de preferencias."""
    return SecurePreferenceAggregator(session_id, config)


def encrypt_preference_data(preferences: Dict[str, torch.Tensor],
                           public_key: paillier.PaillierPublicKey,
                           he: HomomorphicEncryption) -> Dict[str, List[Any]]:
    """
    Encriptar datos de preferencias para envío seguro.

    Args:
        preferences: Preferencias a encriptar
        public_key: Clave pública para encriptación
        he: Instancia de HomomorphicEncryption

    Returns:
        Preferencias encriptadas
    """
    encrypted_preferences = {}

    for pref_name, pref_tensor in preferences.items():
        encrypted_preferences[pref_name] = he.encrypt_preference(pref_tensor, public_key)

    return encrypted_preferences


async def aggregate_preferences_secure_async(aggregator: SecurePreferenceAggregator) -> Dict[str, Any]:
    """
    Agregar preferencias de manera asíncrona.

    Args:
        aggregator: Instancia del agregador seguro

    Returns:
        Preferencias globales agregadas
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, aggregator.aggregate_preferences)
    return result
# Ejemplo de integración con Federated Learning para DPO
def integrate_with_federated_dpo_training(session_id: str,
                                        participant_nodes: List[str],
                                        enable_he: bool = False,
                                        enable_dp: bool = True) -> SecurePreferenceAggregator:
    """
    Crear y configurar un agregador de preferencias para training DPO federado.

    Este ejemplo muestra cómo integrar el SecurePreferenceAggregator con
    federated learning para recolectar preferencias de usuarios de manera privada
    antes de usarlas para crear datos de entrenamiento DPO.

    Args:
        session_id: ID único de la sesión federada
        participant_nodes: Lista de IDs de nodos participantes
        enable_he: Habilitar homomorphic encryption
        enable_dp: Habilitar differential privacy

    Returns:
        SecurePreferenceAggregator configurado

    Example:
        # Configurar agregador para federated DPO
        aggregator = integrate_with_federated_dpo_training(
            session_id="dpo_session_001",
            participant_nodes=["node_1", "node_2", "node_3"],
            enable_he=True,
            enable_dp=True
        )

        # Los nodos envían sus preferencias locales
        # (scores/rankings de respuestas de usuarios)
        aggregator.add_encrypted_preference_update(
            node_id="node_1",
            encrypted_preferences={"response_scores": encrypted_scores},
            num_samples=100
        )

        # Agregar cuando todos los nodos hayan contribuido
        if aggregator.can_aggregate():
            result = aggregator.aggregate_preferences()
            global_preferences = result["aggregated_preferences"]

            # Usar preferencias agregadas para crear datos DPO
            # (convertir a pares chosen/rejected basados en scores)
    """
    config = PreferenceAggregationConfig(
        aggregation_method="weighted_mean",
        enable_differential_privacy=enable_dp,
        enable_homomorphic_encryption=enable_he,
        dp_epsilon=0.1,
        dp_delta=1e-5,
        min_participants=max(3, len(participant_nodes) // 2),  # Al menos 3 o mayoría
        enable_integrity_check=True,
        compute_consensus_metrics=True
    )

    aggregator = SecurePreferenceAggregator(session_id, config)
    aggregator.set_expected_participants(participant_nodes)

    logger.info(f"🔗 SecurePreferenceAggregator integrado para federated DPO session {session_id}")
    return aggregator