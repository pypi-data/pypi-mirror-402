import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import concurrent.futures
import torch
import numpy as np

from .delta_sparsifier import DeltaSparsifier, SparsificationConfig, sparsify_model_update, deserialize_model_update

@dataclass
class WeightUpdate:
    """Actualización de pesos de un nodo."""
    node_id: str
    weights: Dict[str, Any]
    num_samples: int
    timestamp: float
    signature: Optional[str] = None
    # Sparsificación
    sparsified_data: Optional[bytes] = None
    sparsifier: Optional[DeltaSparsifier] = None
    is_sparsified: bool = False

@dataclass
class RoundState:
    """Estado de la ronda de agregación asíncrona."""
    round_id: str
    phase: str = "collecting"  # collecting, aggregating, distributing, completed
    start_time: float = field(default_factory=time.time)
    deadline: float = 0.0
    expected_participants: List[str] = field(default_factory=list)
    responded_nodes: Set[str] = field(default_factory=set)
    partial_aggregates: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_samples: int = 0
    batch_size: int = 10
    min_participation_ratio: float = 0.5

class AsyncAggregator:
    """
    Agregador asíncrono para escalabilidad en federated learning.
    Procesa actualizaciones de pesos en lotes sin esperar quorum completo.
    Optimizado para miles de nodos con asyncio y concurrencia.
    """

    def __init__(self, session_id: str, model_name: str,
                 expected_participants: List[str],
                 min_participation_ratio: float = 0.5,
                 batch_size: int = 10,
                 round_timeout: float = 300.0,
                 enable_sparsification: bool = True,
                 sparsification_k: float = 0.01):
        """
        Inicializa el agregador asíncrono.

        Args:
            session_id: ID de la sesión federada
            model_name: Nombre del modelo
            expected_participants: Lista de IDs de nodos participantes
            min_participation_ratio: Ratio mínimo de participación (0.5 = 50%)
            batch_size: Tamaño del lote para procesamiento incremental
            round_timeout: Timeout en segundos para la ronda
            enable_sparsification: Habilitar sparsificación de deltas
            sparsification_k: Fracción de pesos a mantener en sparsification (0.01 = 1%)
        """
        self.session_id = session_id
        self.model_name = model_name
        self.expected_participants = expected_participants
        self.min_participation_ratio = min_participation_ratio
        self.batch_size = batch_size
        self.round_timeout = round_timeout
        self.enable_sparsification = enable_sparsification
        self.sparsification_k = sparsification_k

        # Estado de la ronda
        self.round_state = RoundState(
            round_id=f"{session_id}_round_{int(time.time())}",
            expected_participants=expected_participants.copy(),
            batch_size=batch_size,
            min_participation_ratio=min_participation_ratio
        )

        # Componentes asíncronos
        self.update_queue = asyncio.Queue(maxsize=10000)  # Cola para actualizaciones entrantes
        self.processing_task: Optional[asyncio.Task] = None
        self.distribution_tasks: List[asyncio.Task] = []

        # Locks para thread safety
        self.lock = asyncio.Lock()

        # Sparsificación
        self.previous_global_weights: Optional[Dict[str, torch.Tensor]] = None
        if self.enable_sparsification:
            sparsification_config = SparsificationConfig(k=self.sparsification_k)
            self.sparsifier = DeltaSparsifier(sparsification_config)
        else:
            self.sparsifier = None

        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Executor para procesamiento paralelo
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        self.logger.info(f"AsyncAggregator initialized for session {session_id} with {len(expected_participants)} expected participants "
                        f"(sparsification: {enable_sparsification})")

    async def aggregate_incrementally(self) -> Dict[str, Any]:
        """
        Procesa lotes de actualizaciones entrantes de manera incremental.
        No espera quorum completo, procesa tan pronto como hay suficientes actualizaciones.

        Returns:
            Diccionario con el resultado de la agregación final
        """
        try:
            self.logger.info(f"Starting incremental aggregation for round {self.round_state.round_id}")

            # Iniciar tarea de procesamiento
            self.processing_task = asyncio.create_task(self._process_updates())

            # Esperar a que se complete la ronda
            while not self._is_round_complete():
                await asyncio.sleep(1.0)

                # Verificar timeouts y extender deadlines si necesario
                await self._check_and_extend_deadline()

            # Finalizar ronda
            return await self._finalize_round()

        except Exception as e:
            self.logger.error(f"Error in incremental aggregation: {e}")
            raise

    async def _process_updates(self):
        """Procesa actualizaciones en lotes de manera continua."""
        try:
            while not self._is_round_complete():
                # Obtener siguiente lote
                batch = await self._get_next_weight_batch()
                if not batch:
                    await asyncio.sleep(0.1)
                    continue

                # Verificar participación suficiente
                if self._has_sufficient_participation():
                    # Computar agregación parcial
                    partial_aggregate = await self._compute_partial_aggregate(batch)

                    # Distribuir a nodos que ya respondieron
                    await self._distribute_partial_aggregate(partial_aggregate)

                    self.logger.info(f"Processed batch of {len(batch)} updates, distributed partial aggregate")

        except Exception as e:
            self.logger.error(f"Error processing updates: {e}")

    def _has_sufficient_participation(self) -> bool:
        """
        Verifica si hay participación suficiente para proceder con agregación.

        Returns:
            True si hay suficiente participación
        """
        responded_count = len(self.round_state.responded_nodes)
        expected_count = len(self.round_state.expected_participants)
        participation_ratio = responded_count / expected_count if expected_count > 0 else 0

        sufficient = participation_ratio >= self.min_participation_ratio
        if sufficient:
            self.logger.info(f"Sufficient participation: {responded_count}/{expected_count} ({participation_ratio:.2%})")
        else:
            self.logger.debug(f"Insufficient participation: {responded_count}/{expected_count} ({participation_ratio:.2%})")

        return sufficient

    async def _compute_partial_aggregate(self, batch: List[WeightUpdate]) -> Dict[str, Any]:
        """
        Computa agregación parcial de un lote de actualizaciones.

        Args:
            batch: Lista de actualizaciones de pesos

        Returns:
            Agregación parcial
        """
        try:
            if not batch:
                return {}

            # Procesar datos sparsificados si es necesario
            processed_batch = self._process_sparsified_batch(batch)

            # Usar executor para procesamiento paralelo
            loop = asyncio.get_event_loop()
            partial_aggregate = await loop.run_in_executor(
                self.executor,
                self._compute_aggregate_sync,
                processed_batch
            )

            # Actualizar estado
            async with self.lock:
                self.round_state.partial_aggregates.update(partial_aggregate)
                for update in batch:
                    self.round_state.total_samples += update.num_samples

            return partial_aggregate

        except Exception as e:
            self.logger.error(f"Error computing partial aggregate: {e}")
            return {}

    def _process_sparsified_batch(self, batch: List[WeightUpdate]) -> List[WeightUpdate]:
        """
        Procesa un lote de actualizaciones, deserializando datos sparsificados.

        Args:
            batch: Lote de actualizaciones (posiblemente sparsificadas)

        Returns:
            Lote procesado con pesos completos
        """
        processed_batch = []

        for update in batch:
            if update.is_sparsified and update.sparsified_data and self.sparsifier:
                try:
                    # Deserializar deltas sparsificados
                    deltas = deserialize_model_update(update.sparsified_data, self.sparsifier)

                    # Convertir deltas a pesos completos
                    if self.previous_global_weights:
                        full_weights = {}
                        for layer_name, delta in deltas.items():
                            if layer_name in self.previous_global_weights:
                                full_weights[layer_name] = self.previous_global_weights[layer_name] + delta
                            else:
                                self.logger.warning(f"Layer {layer_name} not found in previous weights")
                                full_weights[layer_name] = delta
                    else:
                        # Primera ronda, usar deltas como pesos
                        full_weights = deltas

                    # Crear actualización procesada
                    processed_update = WeightUpdate(
                        node_id=update.node_id,
                        weights=full_weights,
                        num_samples=update.num_samples,
                        timestamp=update.timestamp,
                        signature=update.signature,
                        sparsified_data=None,
                        sparsifier=None,
                        is_sparsified=False
                    )

                    processed_batch.append(processed_update)
                    self.logger.debug(f"Desparsified update from {update.node_id}")

                except Exception as e:
                    self.logger.error(f"Error processing sparsified update from {update.node_id}: {e}")
                    # Fallback: usar actualización original
                    processed_batch.append(update)
            else:
                # Actualización no sparsificada
                processed_batch.append(update)

        return processed_batch

    def prepare_sparsified_update(self, current_weights: Dict[str, torch.Tensor],
                                 previous_weights: Optional[Dict[str, torch.Tensor]] = None) -> Tuple[bytes, DeltaSparsifier]:
        """
        Prepara una actualización sparsificada para envío.

        Args:
            current_weights: Pesos actuales del modelo
            previous_weights: Pesos anteriores (opcional, usa self.previous_global_weights si no se proporciona)

        Returns:
            Tuple de (datos comprimidos sparsificados, sparsifier usado)
        """
        if not self.enable_sparsification or not self.sparsifier:
            raise ValueError("Sparsification is not enabled in this aggregator")

        prev_weights = previous_weights or self.previous_global_weights
        if not prev_weights:
            raise ValueError("Previous weights required for sparsification")

        return sparsify_model_update(current_weights, prev_weights, self.sparsification_k)

    def _compute_aggregate_sync(self, batch: List[WeightUpdate]) -> Dict[str, Any]:
        """Computa agregación de manera síncrona (para executor)."""
        if not batch:
            return {}

        # Inicializar acumuladores
        layer_accumulators = defaultdict(lambda: {'weights': None, 'total_samples': 0})

        for update in batch:
            weight_contribution = update.num_samples

            for layer_name, layer_weights in update.weights.items():
                if isinstance(layer_weights, torch.Tensor):
                    if layer_accumulators[layer_name]['weights'] is None:
                        layer_accumulators[layer_name]['weights'] = layer_weights.clone() * weight_contribution
                    else:
                        layer_accumulators[layer_name]['weights'] += layer_weights * weight_contribution

                    layer_accumulators[layer_name]['total_samples'] += weight_contribution
                else:
                    # Manejar otros tipos (numpy arrays, etc.)
                    if layer_accumulators[layer_name]['weights'] is None:
                        layer_accumulators[layer_name]['weights'] = np.array(layer_weights) * weight_contribution
                    else:
                        layer_accumulators[layer_name]['weights'] += np.array(layer_weights) * weight_contribution

                    layer_accumulators[layer_name]['total_samples'] += weight_contribution

        # Promediar
        aggregated_weights = {}
        for layer_name, accumulator in layer_accumulators.items():
            if accumulator['total_samples'] > 0:
                if isinstance(accumulator['weights'], torch.Tensor):
                    aggregated_weights[layer_name] = accumulator['weights'] / accumulator['total_samples']
                else:
                    aggregated_weights[layer_name] = accumulator['weights'] / accumulator['total_samples']

        return aggregated_weights

    async def _distribute_partial_aggregate(self, partial_aggregate: Dict[str, Any]):
        """
        Distribuye la agregación parcial a nodos que ya han respondido.

        Args:
            partial_aggregate: Agregación parcial a distribuir
        """
        try:
            # Crear tareas de distribución para cada nodo respondido
            tasks = []
            for node_id in self.round_state.responded_nodes:
                task = asyncio.create_task(self._send_partial_to_node(node_id, partial_aggregate))
                tasks.append(task)

            # Esperar a que se complete la distribución (con timeout)
            if tasks:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=30.0)

            self.logger.info(f"Distributed partial aggregate to {len(tasks)} nodes")

        except asyncio.TimeoutError:
            self.logger.warning("Partial aggregate distribution timed out")
        except Exception as e:
            self.logger.error(f"Error distributing partial aggregate: {e}")

    async def _send_partial_to_node(self, node_id: str, partial_aggregate: Dict[str, Any]):
        """
        Envía agregación parcial a un nodo específico.
        (Implementación mock - en producción usaría P2P o comunicación real)
        """
        try:
            # Simular envío
            await asyncio.sleep(0.01)  # Simular latencia de red
            self.logger.debug(f"Sent partial aggregate to node {node_id}")

        except Exception as e:
            self.logger.error(f"Error sending partial aggregate to {node_id}: {e}")

    async def _extend_round_deadline(self):
        """Extiende el deadline de la ronda para nodos tardíos."""
        try:
            extension = self.round_timeout * 0.5  # Extender 50% del timeout original
            self.round_state.deadline += extension

            self.logger.info(f"Extended round deadline by {extension}s to {self.round_state.deadline}")

            # Notificar a nodos tardíos
            late_nodes = set(self.round_state.expected_participants) - self.round_state.responded_nodes
            for node_id in late_nodes:
                await self._notify_deadline_extension(node_id, self.round_state.deadline)

        except Exception as e:
            self.logger.error(f"Error extending round deadline: {e}")

    async def _notify_deadline_extension(self, node_id: str, new_deadline: float):
        """
        Notifica extensión de deadline a un nodo.
        (Implementación mock)
        """
        try:
            await asyncio.sleep(0.01)
            self.logger.debug(f"Notified deadline extension to node {node_id}")

        except Exception as e:
            self.logger.error(f"Error notifying deadline extension to {node_id}: {e}")

    async def _get_next_weight_batch(self) -> List[WeightUpdate]:
        """
        Obtiene el siguiente lote de actualizaciones de pesos.

        Returns:
            Lista de actualizaciones para el lote
        """
        try:
            batch = []
            timeout = 1.0  # Timeout para esperar actualizaciones

            for _ in range(self.batch_size):
                try:
                    update = await asyncio.wait_for(self.update_queue.get(), timeout=timeout)
                    batch.append(update)

                    # Marcar nodo como respondido
                    async with self.lock:
                        self.round_state.responded_nodes.add(update.node_id)

                except asyncio.TimeoutError:
                    break

            if batch:
                self.logger.debug(f"Collected batch of {len(batch)} weight updates")

            return batch

        except Exception as e:
            self.logger.error(f"Error getting next weight batch: {e}")
            return []

    async def _finalize_round(self) -> Dict[str, Any]:
        """
        Finaliza la ronda y retorna el resultado final.

        Returns:
            Resultado de la agregación final
        """
        try:
            # Cancelar tareas en ejecución
            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()

            for task in self.distribution_tasks:
                if not task.done():
                    task.cancel()

            # Computar agregación final
            final_aggregate = dict(self.round_state.partial_aggregates)

            # Actualizar pesos anteriores para sparsificación en siguiente ronda
            self.previous_global_weights = final_aggregate.copy()

            # Actualizar estado
            self.round_state.phase = "completed"

            # Calcular estadísticas de sparsificación
            sparsification_stats = {}
            if self.sparsifier:
                bandwidth_stats = self.sparsifier.get_bandwidth_stats()
                sparsification_stats = {
                    'enabled': True,
                    'bandwidth_reduction': bandwidth_stats.get('avg_bandwidth_reduction', 0.0),
                    'sparsity_ratio': bandwidth_stats.get('avg_sparsity_ratio', 0.0)
                }

            result = {
                'round_id': self.round_state.round_id,
                'final_weights': final_aggregate,
                'total_samples': self.round_state.total_samples,
                'participation_count': len(self.round_state.responded_nodes),
                'expected_count': len(self.round_state.expected_participants),
                'completion_time': time.time() - self.round_state.start_time,
                'sparsification_stats': sparsification_stats
            }

            self.logger.info(f"Round {self.round_state.round_id} finalized with {len(self.round_state.responded_nodes)} participants")
            if sparsification_stats.get('enabled'):
                self.logger.info(f"✂️ Sparsification: {sparsification_stats['bandwidth_reduction']:.1%} bandwidth reduction")

            return result

        except Exception as e:
            self.logger.error(f"Error finalizing round: {e}")
            return {}

    async def _check_and_extend_deadline(self):
        """Verifica si es necesario extender el deadline."""
        current_time = time.time()

        if current_time > self.round_state.deadline:
            # Verificar si hay progreso reciente
            recent_responses = any(
                update.timestamp > current_time - 60  # Respuestas en último minuto
                for update in list(self.update_queue._queue)  # Acceso interno (no recomendado en producción)
                if hasattr(update, 'timestamp')
            )

            if recent_responses and not self._has_sufficient_participation():
                await self._extend_round_deadline()

    def _is_round_complete(self) -> bool:
        """Verifica si la ronda está completa."""
        return (self.round_state.phase == "completed" or
                time.time() > self.round_state.deadline or
                len(self.round_state.responded_nodes) == len(self.round_state.expected_participants))

    async def add_weight_update(self, update: WeightUpdate):
        """
        Agrega una actualización de pesos a la cola de procesamiento.

        Args:
            update: Actualización de pesos
        """
        try:
            await self.update_queue.put(update)
            self.logger.debug(f"Added weight update from node {update.node_id}")

        except Exception as e:
            self.logger.error(f"Error adding weight update: {e}")

    async def shutdown(self):
        """Apaga el agregador asíncrono."""
        try:
            # Cancelar tareas
            if self.processing_task:
                self.processing_task.cancel()

            for task in self.distribution_tasks:
                task.cancel()

            # Cerrar executor
            self.executor.shutdown(wait=True)

            self.logger.info("AsyncAggregator shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def get_round_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual de la ronda."""
        return {
            'round_id': self.round_state.round_id,
            'phase': self.round_state.phase,
            'responded_nodes': len(self.round_state.responded_nodes),
            'expected_nodes': len(self.round_state.expected_participants),
            'participation_ratio': len(self.round_state.responded_nodes) / len(self.round_state.expected_participants) if self.round_state.expected_participants else 0,
            'total_samples': self.round_state.total_samples,
            'queue_size': self.update_queue.qsize(),
            'deadline': self.round_state.deadline
        }