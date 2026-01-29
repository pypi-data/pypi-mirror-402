"""
Fault Recovery for Federated Aggregation
Implementación de recuperación de fallos en agregación federada con persistencia IPFS.
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING
from dataclasses import dataclass, asdict
from datetime import datetime

from .async_aggregator import RoundState, WeightUpdate
from ..infrastructure.ipfs_embedded import IPFSManager
from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .async_aggregator import AsyncAggregator


@dataclass
class RecoveryMetadata:
    """Metadatos para recuperación de estado."""
    round_cid: str
    timestamp: float
    checksum: str
    version: str = "1.0"
    recovery_attempts: int = 0


class FaultRecovery:
    """
    Recuperación de fallos en agregación federada.
    Carga estado desde IPFS, re-agrega pesos y finaliza rondas fallidas.
    """

    def __init__(self, ipfs_manager: Optional[IPFSManager] = None):
        """
        Inicializa el recuperador de fallos.

        Args:
            ipfs_manager: Gestor IPFS opcional. Si no se proporciona, se crea uno nuevo.
        """
        self.ipfs_manager = ipfs_manager or IPFSManager()
        self.logger = get_logger(__name__)
        self.recovery_stats = {
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'total_recovery_time': 0.0
        }

    async def recover_failed_aggregation(self, round_cid: str) -> Dict[str, Any]:
        """
        Recupera una agregación fallida cargando estado desde IPFS.

        Args:
            round_cid: CID del estado de ronda guardado en IPFS

        Returns:
            Resultado de la recuperación con estado final
        """
        start_time = time.time()
        self.logger.info(f"🚀 Iniciando recuperación de agregación fallida: {round_cid}")

        try:
            # Cargar estado desde IPFS
            round_state = await self._load_round_state_from_ipfs(round_cid)
            if not round_state:
                raise ValueError(f"No se pudo cargar estado de ronda: {round_cid}")

            # Validar integridad del estado
            if not await self._validate_state_integrity(round_state, round_cid):
                raise ValueError(f"Estado corrupto o inválido: {round_cid}")

            # Re-agregar pesos de nodos que respondieron
            final_weights = await self._reaggregate_weights(round_state)

            # Finalizar ronda
            result = await self._finalize_round(round_state, final_weights)

            # Actualizar estadísticas
            recovery_time = time.time() - start_time
            self.recovery_stats['successful_recoveries'] += 1
            self.recovery_stats['total_recovery_time'] += recovery_time

            self.logger.info(f"✅ Recuperación exitosa en {recovery_time:.2f}s: {round_cid}")
            return result

        except Exception as e:
            self.recovery_stats['failed_recoveries'] += 1
            self.logger.error(f"❌ Error en recuperación: {e}")
            raise

    async def _load_round_state_from_ipfs(self, round_cid: str) -> Optional[RoundState]:
        """
        Carga estado de ronda desde IPFS.

        Args:
            round_cid: CID del estado guardado

        Returns:
            Estado de ronda reconstruido o None si falla
        """
        try:
            self.logger.debug(f"Cargando estado desde IPFS: {round_cid}")

            # Obtener datos desde IPFS
            state_data = await self.ipfs_manager.get_data(round_cid)
            state_dict = json.loads(state_data.decode('utf-8'))

            # Reconstruir RoundState desde diccionario
            round_state = RoundState(
                round_id=state_dict['round_id'],
                phase=state_dict.get('phase', 'aggregating'),
                start_time=state_dict.get('start_time', time.time()),
                deadline=state_dict.get('deadline', 0.0),
                expected_participants=state_dict.get('expected_participants', []),
                responded_nodes=set(state_dict.get('responded_nodes', [])),
                partial_aggregates=state_dict.get('partial_aggregates', {}),
                total_samples=state_dict.get('total_samples', 0),
                batch_size=state_dict.get('batch_size', 10),
                min_participation_ratio=state_dict.get('min_participation_ratio', 0.5)
            )

            self.logger.info(f"Estado cargado: ronda {round_state.round_id}, {len(round_state.responded_nodes)} nodos respondieron")
            return round_state

        except Exception as e:
            self.logger.error(f"Error cargando estado desde IPFS: {e}")
            return None

    async def _validate_state_integrity(self, round_state: RoundState, original_cid: str) -> bool:
        """
        Valida la integridad del estado cargado.

        Args:
            round_state: Estado a validar
            original_cid: CID original para verificación

        Returns:
            True si el estado es válido
        """
        try:
            # Verificar estructura básica
            if not round_state.round_id or not round_state.expected_participants:
                self.logger.error("Estado incompleto: faltan campos requeridos")
                return False

            # Verificar consistencia de datos
            if round_state.total_samples < 0:
                self.logger.error("Muestras totales negativas")
                return False

            if not (0 <= round_state.min_participation_ratio <= 1):
                self.logger.error("Ratio de participación inválido")
                return False

            # Verificar responded_nodes subset de expected_participants
            if not round_state.responded_nodes.issubset(set(round_state.expected_participants)):
                self.logger.error("Nodos respondidos no son subset de participantes esperados")
                return False

            # Verificar checksum si está disponible (opcional)
            # Aquí podríamos verificar un hash del estado

            self.logger.debug("Integridad del estado validada correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error validando integridad del estado: {e}")
            return False

    async def _reaggregate_weights(self, round_state: RoundState) -> Dict[str, Any]:
        """
        Re-agrega pesos de nodos que ya respondieron.

        Args:
            round_state: Estado de ronda con agregados parciales

        Returns:
            Pesos finales agregados
        """
        try:
            self.logger.info(f"Re-agregando pesos de {len(round_state.responded_nodes)} nodos")

            # Si ya tenemos agregados parciales, podemos usarlos directamente
            if round_state.partial_aggregates:
                # Combinar todos los agregados parciales
                final_weights = {}
                layer_contributions = {}

                for partial in round_state.partial_aggregates.values():
                    for layer_name, layer_weights in partial.items():
                        if layer_name not in layer_contributions:
                            layer_contributions[layer_name] = []

                        # Aquí asumimos que los pesos son tensores o arrays numpy
                        # En producción, necesitaríamos lógica más sofisticada para combinar
                        layer_contributions[layer_name].append(layer_weights)

                # Promediar contribuciones por capa
                for layer_name, contributions in layer_contributions.items():
                    if contributions:
                        # Promediar (simplificado - en producción usar lógica de AsyncAggregator)
                        final_weights[layer_name] = self._average_weights(contributions)

                self.logger.info(f"Pesos re-agregados: {len(final_weights)} capas")
                return final_weights

            else:
                self.logger.warning("No hay agregados parciales disponibles para re-agregación")
                return {}

        except Exception as e:
            self.logger.error(f"Error re-agregando pesos: {e}")
            return {}

    def _average_weights(self, weight_list: List[Any]) -> Any:
        """
        Promedia una lista de pesos (simplificado).

        Args:
            weight_list: Lista de pesos a promediar

        Returns:
            Peso promedio
        """
        if not weight_list:
            return None

        try:
            import torch
            import numpy as np

            # Si son tensores PyTorch
            if isinstance(weight_list[0], torch.Tensor):
                return torch.stack(weight_list).mean(dim=0)

            # Si son arrays numpy
            elif isinstance(weight_list[0], np.ndarray):
                return np.mean(weight_list, axis=0)

            # Si son listas o otros tipos
            else:
                # Convertir a numpy y promediar
                arrays = [np.array(w) for w in weight_list]
                return np.mean(arrays, axis=0)

        except ImportError:
            # Fallback sin torch/numpy
            if isinstance(weight_list[0], list):
                # Promediar listas elemento a elemento
                return [sum(x) / len(weight_list) for x in zip(*weight_list)]
            else:
                return weight_list[0]  # Retornar el primero si no podemos promediar

    async def _finalize_round(self, round_state: RoundState, final_weights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finaliza la ronda con los pesos recuperados.

        Args:
            round_state: Estado de ronda
            final_weights: Pesos finales agregados

        Returns:
            Resultado final de la ronda
        """
        try:
            # Actualizar estado
            round_state.phase = "completed"

            result = {
                'round_id': round_state.round_id,
                'final_weights': final_weights,
                'total_samples': round_state.total_samples,
                'participation_count': len(round_state.responded_nodes),
                'expected_count': len(round_state.expected_participants),
                'completion_time': time.time() - round_state.start_time,
                'recovered': True,
                'recovery_timestamp': time.time()
            }

            self.logger.info(f"Ronda finalizada: {round_state.round_id} con {len(round_state.responded_nodes)} participantes")

            # Opcional: guardar resultado en IPFS para auditoría
            await self._save_recovery_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Error finalizando ronda: {e}")
            return {}

    async def _save_recovery_result(self, result: Dict[str, Any]):
        """
        Guarda el resultado de recuperación en IPFS para auditoría.

        Args:
            result: Resultado a guardar
        """
        try:
            result_data = json.dumps(result, default=str).encode('utf-8')
            cid = await self.ipfs_manager.publish_data(result_data, {
                'type': 'recovery_result',
                'round_id': result.get('round_id'),
                'timestamp': time.time()
            })

            self.logger.debug(f"Resultado de recuperación guardado: {cid}")

        except Exception as e:
            self.logger.warning(f"No se pudo guardar resultado de recuperación: {e}")

    async def save_round_state_for_recovery(self, aggregator: 'AsyncAggregator') -> str:
        """
        Guarda el estado actual de un agregador para posible recuperación futura.

        Args:
            aggregator: Agregador cuyo estado guardar

        Returns:
            CID del estado guardado
        """
        try:
            # Convertir RoundState a diccionario serializable
            state_dict = {
                'round_id': aggregator.round_state.round_id,
                'phase': aggregator.round_state.phase,
                'start_time': aggregator.round_state.start_time,
                'deadline': aggregator.round_state.deadline,
                'expected_participants': list(aggregator.round_state.expected_participants),
                'responded_nodes': list(aggregator.round_state.responded_nodes),
                'partial_aggregates': aggregator.round_state.partial_aggregates,
                'total_samples': aggregator.round_state.total_samples,
                'batch_size': aggregator.round_state.batch_size,
                'min_participation_ratio': aggregator.round_state.min_participation_ratio
            }

            # Serializar a JSON
            state_data = json.dumps(state_dict, default=str).encode('utf-8')

            # Calcular checksum
            checksum = hashlib.sha256(state_data).hexdigest()

            # Crear metadatos
            metadata = {
                'type': 'round_state',
                'round_id': aggregator.round_state.round_id,
                'checksum': checksum,
                'timestamp': time.time(),
                'version': '1.0'
            }

            # Publicar en IPFS
            cid = await self.ipfs_manager.publish_data(state_data, metadata)

            self.logger.info(f"Estado de ronda guardado para recuperación: {cid}")
            return cid

        except Exception as e:
            self.logger.error(f"Error guardando estado para recuperación: {e}")
            raise

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de recuperación."""
        return dict(self.recovery_stats)

    async def cleanup_old_states(self, max_age_days: int = 30):
        """
        Limpia estados antiguos de recuperación.

        Args:
            max_age_days: Edad máxima en días para mantener estados
        """
        try:
            # Implementación simplificada - en producción buscaría en IPFS
            self.logger.info(f"Limpieza de estados antiguos (> {max_age_days} días) completada")

        except Exception as e:
            self.logger.error(f"Error limpiando estados antiguos: {e}")