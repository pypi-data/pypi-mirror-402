"""
Federated Learning Aggregator - Algoritmo FedAvg
Coordina la agregación de pesos desde múltiples nodos.
"""

import asyncio
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WeightUpdate:
    """Actualización de pesos desde un nodo."""
    node_id: str
    weights: Dict[str, Any]  # Pesos del modelo
    num_samples: int  # Número de muestras locales
    metrics: Dict[str, Any]  # Métricas de entrenamiento local
    timestamp: float
    memory_capabilities: Optional[Dict[str, Any]] = None  # Capacidades de memoria del nodo


@dataclass
class MemoryMetaLearningUpdate:
    """Actualización de meta-learning para capacidades de memoria."""
    node_id: str
    memory_metrics: Dict[str, Any]  # Métricas de memoria (capacidad, latencia, uptime, etc.)
    memory_performance: Dict[str, Any]  # Rendimiento en tareas de memoria
    adaptation_weights: Dict[str, Any]  # Pesos de adaptación meta-learning
    timestamp: float


class FedAvgAggregator:
    """Alias para compatibilidad."""
    pass


class FederatedAggregator:
    """
    Agregador FedAvg para federated learning.
    Recibe actualizaciones de pesos de nodos participantes y calcula el modelo global.
    """

    def __init__(self, session_id: str, model_name: str):
        self.session_id = session_id
        self.model_name = model_name

        # Estado de la ronda actual
        self.current_round = 0
        self.weight_updates: List[WeightUpdate] = []
        self.expected_participants: List[str] = []

        # Meta-learning de capacidades de memoria
        self.memory_meta_updates: List[MemoryMetaLearningUpdate] = []
        self.memory_capability_models: Dict[str, Dict[str, Any]] = {}  # Modelos de capacidad por nodo
        self.global_memory_meta_model: Dict[str, Any] = {}  # Modelo meta-learning global

        # Estadísticas
        self.round_stats = {
            "start_time": None,
            "end_time": None,
            "total_samples": 0,
            "avg_accuracy": 0.0,
            "avg_loss": 0.0,
            "memory_capability_score": 0.0,
            "meta_learning_convergence": 0.0
        }

        logger.info(f"🚀 FederatedAggregator initialized for session {session_id}")

    def set_expected_participants(self, participant_ids: List[str]):
        """Establecer lista de participantes esperados para esta ronda."""
        self.expected_participants = participant_ids.copy()
        logger.info(f"📋 Expected participants for round {self.current_round}: {participant_ids}")

    def add_weight_update(self, node_id: str, weights: Dict[str, Any],
                         num_samples: int, metrics: Dict[str, Any],
                         memory_capabilities: Optional[Dict[str, Any]] = None):
        """
        Añadir actualización de pesos desde un nodo.

        Args:
            node_id: ID del nodo que envía la actualización
            weights: Pesos del modelo entrenado localmente
            num_samples: Número de muestras usadas en entrenamiento local
            metrics: Métricas de entrenamiento (accuracy, loss, etc.)
            memory_capabilities: Capacidades de memoria del nodo (opcional)
        """
        # Verificar que el nodo está en la lista esperada
        if node_id not in self.expected_participants:
            logger.warning(f"⚠️ Unexpected weight update from node {node_id}")
            return

        # Verificar que no hemos recibido ya una actualización de este nodo
        existing_updates = [u for u in self.weight_updates if u.node_id == node_id]
        if existing_updates:
            logger.warning(f"⚠️ Duplicate weight update from node {node_id}, ignoring")
            return

        # Crear actualización
        update = WeightUpdate(
            node_id=node_id,
            weights=weights,
            num_samples=num_samples,
            metrics=metrics,
            timestamp=time.time(),
            memory_capabilities=memory_capabilities
        )

        self.weight_updates.append(update)

        # Actualizar estadísticas
        self.round_stats["total_samples"] += num_samples

        # Actualizar modelo de capacidades de memoria si se proporciona
        if memory_capabilities:
            self._update_memory_capability_model(node_id, memory_capabilities)

        logger.info(f"📦 Weight update received from {node_id} ({num_samples} samples)"
                   f"{' with memory capabilities' if memory_capabilities else ''}")

    def can_aggregate(self) -> bool:
        """
        Verificar si tenemos suficientes actualizaciones para agregar.

        Returns:
            True si podemos proceder con la agregación
        """
        received_count = len(self.weight_updates)
        expected_count = len(self.expected_participants)

        # Necesitamos al menos 50% de los participantes para una agregación válida
        min_required = max(1, expected_count // 2)

        can_proceed = received_count >= min_required

        if can_proceed:
            logger.info(f"✅ Ready to aggregate: {received_count}/{expected_count} updates received")
        else:
            logger.info(f"⏳ Waiting for updates: {received_count}/{expected_count} received (need {min_required})")

        return can_proceed

    def aggregate_weights(self) -> Dict[str, Any]:
        """
        Agregar pesos usando algoritmo FedAvg con meta-learning de capacidades de memoria.

        Returns:
            Pesos globales agregados
        """
        if not self.can_aggregate():
            raise ValueError("Not enough weight updates to perform aggregation")

        if not self.weight_updates:
            raise ValueError("No weight updates available for aggregation")

        logger.info(f"🔄 Starting FedAvg aggregation with memory meta-learning for {len(self.weight_updates)} updates")

        # Inicializar estadísticas de ronda
        self.round_stats["start_time"] = time.time()

        # Calcular pesos FedAvg (weighted average por número de muestras)
        total_samples = sum(update.num_samples for update in self.weight_updates)

        # Aplicar meta-learning de capacidades de memoria para ajustar pesos
        memory_adjusted_weights = self._apply_memory_meta_learning()

        # Inicializar pesos globales con la primera actualización
        global_weights = {}
        first_update = self.weight_updates[0]

        for layer_name, layer_weights in first_update.weights.items():
            if isinstance(layer_weights, np.ndarray):
                global_weights[layer_name] = np.zeros_like(layer_weights, dtype=np.float32)
            elif isinstance(layer_weights, (int, float)):
                global_weights[layer_name] = 0.0
            elif isinstance(layer_weights, list):
                global_weights[layer_name] = [0.0] * len(layer_weights)
            else:
                # Para otros tipos, copiar directamente
                global_weights[layer_name] = layer_weights

        # Agregar pesos de manera ponderada con ajustes de memoria
        for update in self.weight_updates:
            # Calcular factor de peso base
            weight_factor = update.num_samples / total_samples

            # Aplicar ajuste de meta-learning de memoria
            memory_boost = self._calculate_memory_boost_factor(update)
            adjusted_weight_factor = weight_factor * (1.0 + memory_boost)

            for layer_name, layer_weights in update.weights.items():
                if layer_name not in global_weights:
                    continue

                if isinstance(layer_weights, np.ndarray):
                    global_weights[layer_name] += layer_weights * adjusted_weight_factor
                elif isinstance(layer_weights, (int, float)):
                    global_weights[layer_name] += layer_weights * adjusted_weight_factor
                elif isinstance(layer_weights, list):
                    for i, w in enumerate(layer_weights):
                        if i < len(global_weights[layer_name]):
                            global_weights[layer_name][i] += w * adjusted_weight_factor

        # Calcular métricas promedio
        accuracies = [u.metrics.get("accuracy", 0) for u in self.weight_updates]
        losses = [u.metrics.get("loss", 0) for u in self.weight_updates]

        self.round_stats["avg_accuracy"] = np.mean(accuracies) if accuracies else 0.0
        self.round_stats["avg_loss"] = np.mean(losses) if losses else 0.0

        # Calcular puntuación de capacidad de memoria
        memory_scores = [self._calculate_memory_capability_score(u) for u in self.weight_updates if u.memory_capabilities]
        self.round_stats["memory_capability_score"] = np.mean(memory_scores) if memory_scores else 0.0

        # Actualizar modelo meta-learning global
        self._update_global_memory_meta_model()

        self.round_stats["end_time"] = time.time()
        aggregation_time = self.round_stats["end_time"] - self.round_stats["start_time"]

        logger.info(f"✅ FedAvg aggregation with memory meta-learning completed in {aggregation_time:.2f}s")
        logger.info(f"📊 Average accuracy: {self.round_stats['avg_accuracy']:.4f}")
        logger.info(f"📊 Average loss: {self.round_stats['avg_loss']:.4f}")
        logger.info(f"🧠 Memory capability score: {self.round_stats['memory_capability_score']:.4f}")

        return global_weights

    def reset_for_next_round(self):
        """Resetear el agregador para la siguiente ronda."""
        self.current_round += 1
        self.weight_updates.clear()
        self.memory_meta_updates.clear()  # Reset memory meta-learning updates

        # Resetear estadísticas
        self.round_stats = {
            "start_time": None,
            "end_time": None,
            "total_samples": 0,
            "avg_accuracy": 0.0,
            "avg_loss": 0.0,
            "memory_capability_score": 0.0,
            "meta_learning_convergence": 0.0
        }

        logger.info(f"🔄 Aggregator reset for round {self.current_round} (with memory meta-learning)")

    def get_round_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de la ronda actual.

        Returns:
            Estadísticas y métricas de la ronda
        """
        return {
            "round_num": self.current_round,
            "updates_received": len(self.weight_updates),
            "expected_updates": len(self.expected_participants),
            "total_samples": self.round_stats["total_samples"],
            "avg_accuracy": self.round_stats["avg_accuracy"],
            "avg_loss": self.round_stats["avg_loss"],
            "completion_percentage": (len(self.weight_updates) / max(1, len(self.expected_participants))) * 100,
            "can_aggregate": self.can_aggregate(),
            "participants": [u.node_id for u in self.weight_updates]
        }

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas de agregación.

        Returns:
            Estadísticas detalladas del proceso de agregación
        """
        return {
            "session_id": self.session_id,
            "model_name": self.model_name,
            "current_round": self.current_round,
            "total_updates_processed": len(self.weight_updates),
            "total_samples_processed": self.round_stats["total_samples"],
            "avg_accuracy_trend": self.round_stats["avg_accuracy"],
            "avg_loss_trend": self.round_stats["avg_loss"],
            "memory_capability_score": self.round_stats["memory_capability_score"],
            "meta_learning_convergence": self.round_stats["meta_learning_convergence"],
            "last_aggregation_time": self.round_stats.get("end_time"),
            "aggregation_efficiency": len(self.weight_updates) / max(1, len(self.expected_participants))
        }

    # ===== MEMORY META-LEARNING METHODS =====

    def add_memory_meta_update(self, node_id: str, memory_metrics: Dict[str, Any],
                              memory_performance: Dict[str, Any],
                              adaptation_weights: Dict[str, Any]):
        """
        Añadir actualización de meta-learning de capacidades de memoria.

        Args:
            node_id: ID del nodo
            memory_metrics: Métricas de memoria del nodo
            memory_performance: Rendimiento en tareas de memoria
            adaptation_weights: Pesos de adaptación meta-learning
        """
        meta_update = MemoryMetaLearningUpdate(
            node_id=node_id,
            memory_metrics=memory_metrics,
            memory_performance=memory_performance,
            adaptation_weights=adaptation_weights,
            timestamp=time.time()
        )

        self.memory_meta_updates.append(meta_update)
        logger.info(f"🧠 Memory meta-learning update received from {node_id}")

    def _update_memory_capability_model(self, node_id: str, memory_capabilities: Dict[str, Any]):
        """Actualizar modelo de capacidades de memoria para un nodo."""
        if node_id not in self.memory_capability_models:
            self.memory_capability_models[node_id] = {
                'capacity_gb': 0.0,
                'bandwidth_mbps': 0.0,
                'latency_ms': 0.0,
                'uptime_score': 1.0,
                'performance_score': 0.0,
                'last_updated': time.time()
            }

        # Actualizar con promedio móvil
        current = self.memory_capability_models[node_id]
        alpha = 0.3  # Factor de aprendizaje

        current['capacity_gb'] = (1 - alpha) * current['capacity_gb'] + alpha * memory_capabilities.get('capacity_gb', current['capacity_gb'])
        current['bandwidth_mbps'] = (1 - alpha) * current['bandwidth_mbps'] + alpha * memory_capabilities.get('bandwidth_mbps', current['bandwidth_mbps'])
        current['latency_ms'] = (1 - alpha) * current['latency_ms'] + alpha * memory_capabilities.get('latency_ms', current['latency_ms'])
        current['uptime_score'] = (1 - alpha) * current['uptime_score'] + alpha * memory_capabilities.get('uptime_score', current['uptime_score'])
        current['performance_score'] = (1 - alpha) * current['performance_score'] + alpha * memory_capabilities.get('performance_score', current['performance_score'])
        current['last_updated'] = time.time()

    def _calculate_memory_capability_score(self, weight_update: WeightUpdate) -> float:
        """Calcular puntuación de capacidad de memoria para una actualización."""
        if not weight_update.memory_capabilities:
            return 0.0

        caps = weight_update.memory_capabilities
        metrics = weight_update.metrics

        # Puntuación basada en capacidad, ancho de banda, latencia y rendimiento
        capacity_score = min(caps.get('capacity_gb', 0) / 100, 1.0)  # Normalizado a 100GB
        bandwidth_score = min(caps.get('bandwidth_mbps', 0) / 1000, 1.0)  # Normalizado a 1000Mbps
        latency_score = max(0, 1.0 - (caps.get('latency_ms', 100) / 500))  # Penalización por latencia alta
        uptime_score = caps.get('uptime_score', 1.0)
        performance_score = metrics.get('memory_efficiency', 0.5)

        # Puntuación compuesta
        total_score = (capacity_score * 0.2 + bandwidth_score * 0.2 +
                      latency_score * 0.2 + uptime_score * 0.2 +
                      performance_score * 0.2)

        return total_score

    def _calculate_memory_boost_factor(self, weight_update: WeightUpdate) -> float:
        """Calcular factor de boost de memoria para el peso de agregación."""
        if not weight_update.memory_capabilities:
            return 0.0

        capability_score = self._calculate_memory_capability_score(weight_update)

        # El boost es proporcional a la puntuación de capacidad de memoria
        # Máximo boost del 50% para nodos con capacidades excepcionales
        max_boost = 0.5
        boost_factor = capability_score * max_boost

        return boost_factor

    def _apply_memory_meta_learning(self) -> Dict[str, Any]:
        """
        Aplicar meta-learning de capacidades de memoria para ajustar la agregación.

        Returns:
            Ajustes de pesos basados en meta-learning
        """
        if not self.memory_meta_updates:
            return {}

        # Agregar pesos de adaptación de todos los nodos
        total_adaptation_weights = {}

        for update in self.memory_meta_updates:
            for key, weights in update.adaptation_weights.items():
                if key not in total_adaptation_weights:
                    total_adaptation_weights[key] = {}

                # Agregar pesos de manera ponderada por rendimiento de memoria
                performance_weight = update.memory_performance.get('overall_score', 1.0)

                for layer_name, layer_weights in weights.items():
                    if layer_name not in total_adaptation_weights[key]:
                        if isinstance(layer_weights, np.ndarray):
                            total_adaptation_weights[key][layer_name] = np.zeros_like(layer_weights, dtype=np.float32)
                        else:
                            total_adaptation_weights[key][layer_name] = 0.0

                    if isinstance(layer_weights, np.ndarray):
                        total_adaptation_weights[key][layer_name] += layer_weights * performance_weight
                    else:
                        total_adaptation_weights[key][layer_name] += layer_weights * performance_weight

        # Normalizar pesos de adaptación
        num_updates = len(self.memory_meta_updates)
        for key in total_adaptation_weights:
            for layer_name in total_adaptation_weights[key]:
                if isinstance(total_adaptation_weights[key][layer_name], np.ndarray):
                    total_adaptation_weights[key][layer_name] /= num_updates
                else:
                    total_adaptation_weights[key][layer_name] /= num_updates

        logger.info(f"🧠 Applied memory meta-learning adjustments from {num_updates} nodes")
        return total_adaptation_weights

    def _update_global_memory_meta_model(self):
        """Actualizar modelo meta-learning global de capacidades de memoria."""
        if not self.memory_capability_models:
            return

        # Calcular estadísticas globales de capacidades de memoria
        total_capacity = sum(model['capacity_gb'] for model in self.memory_capability_models.values())
        avg_capacity = total_capacity / len(self.memory_capability_models)

        total_bandwidth = sum(model['bandwidth_mbps'] for model in self.memory_capability_models.values())
        avg_bandwidth = total_bandwidth / len(self.memory_capability_models)

        total_uptime = sum(model['uptime_score'] for model in self.memory_capability_models.values())
        avg_uptime = total_uptime / len(self.memory_capability_models)

        # Actualizar modelo global
        self.global_memory_meta_model.update({
            'avg_capacity_gb': avg_capacity,
            'avg_bandwidth_mbps': avg_bandwidth,
            'avg_uptime_score': avg_uptime,
            'total_memory_nodes': len(self.memory_capability_models),
            'last_updated': time.time()
        })

        # Calcular convergencia del meta-learning
        if len(self.memory_meta_updates) > 1:
            # Medida simple de convergencia basada en varianza de puntuaciones
            performance_scores = [u.memory_performance.get('overall_score', 0) for u in self.memory_meta_updates]
            if performance_scores:
                mean_score = np.mean(performance_scores)
                variance = np.var(performance_scores)
                convergence = 1.0 / (1.0 + variance)  # Mayor convergencia = menor varianza
                self.round_stats["meta_learning_convergence"] = convergence

        logger.info(f"🧠 Updated global memory meta-model: {len(self.memory_capability_models)} nodes, "
                   f"avg capacity: {avg_capacity:.1f}GB, convergence: {self.round_stats['meta_learning_convergence']:.3f}")

    def get_memory_meta_learning_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de meta-learning de capacidades de memoria.

        Returns:
            Estadísticas del meta-learning de memoria
        """
        return {
            'total_memory_nodes': len(self.memory_capability_models),
            'active_memory_meta_updates': len(self.memory_meta_updates),
            'global_memory_model': self.global_memory_meta_model,
            'memory_capability_distribution': {
                node_id: {
                    'capacity_gb': model['capacity_gb'],
                    'uptime_score': model['uptime_score'],
                    'performance_score': model['performance_score']
                }
                for node_id, model in self.memory_capability_models.items()
            },
            'meta_learning_convergence': self.round_stats.get('meta_learning_convergence', 0.0)
        }


# Funciones de conveniencia
def create_aggregator(session_id: str, model_name: str) -> FederatedAggregator:
    """Crear un nuevo agregador federado."""
    return FederatedAggregator(session_id, model_name)


async def aggregate_weights_async(aggregator: FederatedAggregator) -> Dict[str, Any]:
    """
    Agregar pesos de manera asíncrona.

    Args:
        aggregator: Instancia del agregador

    Returns:
        Pesos globales agregados
    """
    # Ejecutar agregación en thread pool para no bloquear
    loop = asyncio.get_event_loop()
    global_weights = await loop.run_in_executor(None, aggregator.aggregate_weights)
    return global_weights