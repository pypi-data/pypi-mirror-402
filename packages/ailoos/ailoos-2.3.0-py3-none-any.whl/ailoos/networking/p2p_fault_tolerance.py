#!/usr/bin/env python3
"""
Tolerancia a Fallos P2P para AILOOS
Implementa detección de fallos, recuperación automática, consenso PBFT-like ligero,
quorum para decisiones críticas, optimizado para redes masivas.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Tipos de fallos soportados."""
    TIMEOUT = "timeout"
    DISCONNECTION = "disconnection"
    NETWORK_ERROR = "network_error"


@dataclass
class PeerInfo:
    """Información de un peer en la red."""
    peer_id: str
    address: Tuple[str, int]
    last_seen: float
    status: str = "active"  # active, failed, recovering
    redundancy_level: int = 1


class P2PFaultTolerance:
    """
    Maneja tolerancia a fallos en red P2P con detección automática,
    recuperación desde peers redundantes, consenso PBFT-like y quorum.
    Optimizado para recuperación <30s en redes masivas.
    """

    def __init__(self, node_id: str, peers: List[PeerInfo], quorum_size: int = 3, recovery_timeout: float = 30.0):
        """
        Inicializar tolerancia a fallos P2P.

        Args:
            node_id: ID único del nodo
            peers: Lista de peers en la red
            quorum_size: Tamaño mínimo del quorum para decisiones
            recovery_timeout: Timeout máximo para recuperación (segundos)
        """
        self.node_id = node_id
        self.peers = {p.peer_id: p for p in peers}
        self.quorum_size = quorum_size
        self.recovery_timeout = recovery_timeout

        # Estado del consenso PBFT
        self.sequence_number = 0
        self.prepared_messages: Dict[int, Set[str]] = defaultdict(set)
        self.committed_messages: Dict[int, Set[str]] = defaultdict(set)

        # Estadísticas
        self.stats = {
            'failures_detected': 0,
            'recoveries_completed': 0,
            'consensus_rounds': 0,
            'quorum_achieved': 0
        }

        # Semaphore para concurrencia en red masiva
        self.concurrency_semaphore = asyncio.Semaphore(50)

        logger.info(f"🔧 P2PFaultTolerance inicializado para nodo {node_id}")

    async def handle_failure(self, peer_id: str, failure_type: FailureType) -> bool:
        """
        Maneja un fallo detectado en un peer.

        Args:
            peer_id: ID del peer fallido
            failure_type: Tipo de fallo detectado

        Returns:
            True si la recuperación fue exitosa
        """
        try:
            logger.warning(f"🚨 Fallo detectado en peer {peer_id}: {failure_type.value}")
            self.stats['failures_detected'] += 1

            # Marcar peer como fallido
            if peer_id in self.peers:
                self.peers[peer_id].status = "failed"

            # Iniciar recuperación
            success = await self._start_recovery(peer_id)

            if success:
                self.peers[peer_id].status = "active"
                self.stats['recoveries_completed'] += 1
                logger.info(f"✅ Recuperación exitosa para peer {peer_id}")
            else:
                logger.error(f"❌ Recuperación fallida para peer {peer_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error manejando fallo en {peer_id}: {e}")
            return False

    async def _start_recovery(self, peer_id: str) -> bool:
        """
        Inicia proceso de recuperación con timeout <30s.
        """
        try:
            start_time = time.time()

            # Encontrar peers redundantes
            redundant_peers = self._get_redundant_peers(peer_id)
            if not redundant_peers:
                logger.error(f"No hay peers redundantes para {peer_id}")
                return False

            # Recuperación concurrente desde múltiples peers
            tasks = []
            for rp in redundant_peers[:5]:  # Limitar a 5 para no sobrecargar
                tasks.append(self._sync_from_redundant_peer(peer_id, rp))

            # Esperar primera exitosa o timeout
            done, pending = await asyncio.wait(tasks, timeout=self.recovery_timeout, return_when=asyncio.FIRST_COMPLETED)

            # Cancelar pendientes
            for p in pending:
                p.cancel()

            # Verificar si alguna tarea completó exitosamente
            for task in done:
                try:
                    if task.result():
                        elapsed = time.time() - start_time
                        logger.info(f"Recuperación completada en {elapsed:.2f}s")
                        return True
                except Exception as e:
                    logger.debug(f"Tarea fallida: {e}")

            logger.warning(f"Recuperación timeout después de {self.recovery_timeout}s")
            return False

        except Exception as e:
            logger.error(f"Error en recuperación: {e}")
            return False

    def _get_redundant_peers(self, failed_peer_id: str) -> List[PeerInfo]:
        """
        Encuentra peers redundantes para recuperación.
        """
        redundant = []
        for p in self.peers.values():
            if p.peer_id != failed_peer_id and p.status == "active" and p.redundancy_level > 0:
                redundant.append(p)

        # Ordenar por nivel de redundancia
        redundant.sort(key=lambda p: p.redundancy_level, reverse=True)
        return redundant

    async def _sync_from_redundant_peer(self, failed_peer_id: str, redundant_peer: PeerInfo) -> bool:
        """
        Sincroniza estado desde un peer redundante.
        """
        async with self.concurrency_semaphore:
            try:
                # Simular sincronización (en implementación real, P2P sync)
                await asyncio.sleep(0.5)  # Simular latencia
                logger.debug(f"Sincronizando desde {redundant_peer.peer_id} para {failed_peer_id}")
                # Simular éxito
                return True
            except Exception as e:
                logger.error(f"Error sincronizando desde {redundant_peer.peer_id}: {e}")
                return False

    async def validate_update_with_consensus(self, update_data: Any, is_critical: bool = False) -> bool:
        """
        Valida una actualización usando consenso PBFT-like.
        Para decisiones críticas, requiere quorum.

        Args:
            update_data: Datos de la actualización
            is_critical: Si es una decisión crítica que requiere quorum

        Returns:
            True si el consenso fue alcanzado
        """
        try:
            self.sequence_number += 1
            seq = self.sequence_number
            self.stats['consensus_rounds'] += 1

            # Fase Prepare
            prepare_votes = await self._pbft_prepare(seq, update_data)

            if len(prepare_votes) < self.quorum_size:
                logger.warning(f"Quorum no alcanzado en prepare: {len(prepare_votes)}/{self.quorum_size}")
                if is_critical:
                    return False

            # Fase Commit
            commit_votes = await self._pbft_commit(seq, update_data)

            quorum_achieved = len(commit_votes) >= self.quorum_size
            if quorum_achieved:
                self.stats['quorum_achieved'] += 1
                logger.info(f"✅ Consenso alcanzado para secuencia {seq}")
            else:
                logger.warning(f"❌ Consenso fallido para secuencia {seq}")

            return quorum_achieved

        except Exception as e:
            logger.error(f"Error en consenso: {e}")
            return False

    async def _pbft_prepare(self, seq: int, data: Any) -> Set[str]:
        """
        Fase Prepare del PBFT ligero.
        """
        votes = set()

        # Enviar prepare a peers activos
        tasks = []
        for peer in self.peers.values():
            if peer.status == "active":
                tasks.append(self._send_prepare(peer, seq, data))

        # Esperar respuestas
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                peer_id = list(self.peers.keys())[i]
                votes.add(peer_id)

        self.prepared_messages[seq] = votes
        return votes

    async def _pbft_commit(self, seq: int, data: Any) -> Set[str]:
        """
        Fase Commit del PBFT ligero.
        """
        votes = set()

        # Solo si prepare tuvo quorum
        if len(self.prepared_messages[seq]) < self.quorum_size:
            return votes

        # Enviar commit
        tasks = []
        for peer in self.peers.values():
            if peer.status == "active":
                tasks.append(self._send_commit(peer, seq, data))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                peer_id = list(self.peers.keys())[i]
                votes.add(peer_id)

        self.committed_messages[seq] = votes
        return votes

    async def _send_prepare(self, peer: PeerInfo, seq: int, data: Any) -> bool:
        """
        Envía mensaje prepare a un peer.
        """
        async with self.concurrency_semaphore:
            try:
                # Simular envío P2P
                await asyncio.sleep(0.1)
                logger.debug(f"Prepare enviado a {peer.peer_id} para seq {seq}")
                return True
            except Exception as e:
                logger.error(f"Error enviando prepare a {peer.peer_id}: {e}")
                return False

    async def _send_commit(self, peer: PeerInfo, seq: int, data: Any) -> bool:
        """
        Envía mensaje commit a un peer.
        """
        async with self.concurrency_semaphore:
            try:
                # Simular envío P2P
                await asyncio.sleep(0.1)
                logger.debug(f"Commit enviado a {peer.peer_id} para seq {seq}")
                return True
            except Exception as e:
                logger.error(f"Error enviando commit a {peer.peer_id}: {e}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de tolerancia a fallos.
        """
        return {
            **self.stats,
            'node_id': self.node_id,
            'active_peers': len([p for p in self.peers.values() if p.status == "active"]),
            'failed_peers': len([p for p in self.peers.values() if p.status == "failed"])
        }


# Función de conveniencia
def create_p2p_fault_tolerance(node_id: str, peers: List[PeerInfo], quorum_size: int = 3) -> P2PFaultTolerance:
    """
    Crea instancia de tolerancia a fallos P2P.
    """
    return P2PFaultTolerance(node_id, peers, quorum_size)