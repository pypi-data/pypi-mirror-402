#!/usr/bin/env python3
"""
Loss Detection Engine - Motor de detección de pérdida de datos en entornos federados
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from ..utils.logging import get_logger

logger = get_logger(__name__)


class LossType(Enum):
    """Tipos de pérdida de datos."""
    NODE_DISCONNECT = "node_disconnect"
    DATA_UNAVAILABLE = "data_unavailable"
    REPLICATION_FAILURE = "replication_failure"
    SESSION_PARTICIPANT_MISSING = "session_participant_missing"
    NETWORK_PARTITION = "network_partition"


@dataclass
class LossEvent:
    """Evento de pérdida de datos."""
    event_id: str
    loss_type: LossType
    affected_data: List[str]
    affected_nodes: List[str]
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    recovery_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeStatus:
    """Estado de un nodo."""
    node_id: str
    last_seen: datetime
    is_online: bool
    data_availability: Dict[str, bool] = field(default_factory=dict)
    connectivity_score: float = 1.0  # 0.0 a 1.0


class LossDetectionEngine:
    """
    Motor de detección de pérdida de datos en entornos federados P2P.

    Características:
    - Monitoreo de conectividad de nodos
    - Detección de datos faltantes
    - Análisis de particiones de red
    - Alertas automáticas
    - Recomendaciones de recuperación
    """

    def __init__(self,
                 heartbeat_interval: int = 60,  # 1 minuto
                 timeout_threshold: int = 300,  # 5 minutos
                 alert_callback: Optional[Callable] = None,
                 min_replication_factor: int = 3):
        """
        Inicializar motor de detección de pérdida.

        Args:
            heartbeat_interval: Intervalo entre heartbeats (segundos)
            timeout_threshold: Umbral de timeout para considerar nodo offline
            alert_callback: Función para alertas
            min_replication_factor: Factor mínimo de replicación
        """
        self.heartbeat_interval = heartbeat_interval
        self.timeout_threshold = timeout_threshold
        self.alert_callback = alert_callback
        self.min_replication_factor = min_replication_factor

        # Estado de nodos
        self.node_status: Dict[str, NodeStatus] = {}
        self.expected_nodes: Set[str] = set()

        # Eventos de pérdida
        self.loss_events: List[LossEvent] = []
        self.event_counter = 0

        # Estado del motor
        self.is_detecting = False
        self.detection_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Estadísticas
        self.stats = {
            'total_heartbeats': 0,
            'offline_nodes': 0,
            'data_loss_events': 0,
            'network_partitions': 0,
            'last_detection_time': None
        }

        logger.info("🔍 Loss Detection Engine initialized")

    def register_node(self, node_id: str, expected_data: List[str] = None):
        """
        Registrar un nodo para monitoreo.

        Args:
            node_id: ID del nodo
            expected_data: Lista de IDs de datos que debería tener el nodo
        """
        if node_id not in self.node_status:
            self.node_status[node_id] = NodeStatus(
                node_id=node_id,
                last_seen=datetime.now(),
                is_online=True,
                data_availability={data_id: True for data_id in (expected_data or [])}
            )

        self.expected_nodes.add(node_id)
        logger.info(f"📝 Registered node {node_id} for loss detection")

    def unregister_node(self, node_id: str):
        """Desregistrar un nodo."""
        if node_id in self.node_status:
            del self.node_status[node_id]
        self.expected_nodes.discard(node_id)
        logger.info(f"🗑️ Unregistered node {node_id} from loss detection")

    def update_heartbeat(self, node_id: str, data_status: Dict[str, bool] = None):
        """
        Actualizar heartbeat de un nodo.

        Args:
            node_id: ID del nodo
            data_status: Estado de disponibilidad de datos
        """
        if node_id not in self.node_status:
            self.register_node(node_id)

        node = self.node_status[node_id]
        node.last_seen = datetime.now()
        node.is_online = True

        if data_status:
            node.data_availability.update(data_status)

        # Recalcular score de conectividad
        node.connectivity_score = min(1.0, node.connectivity_score + 0.1)

        self.stats['total_heartbeats'] += 1
        logger.debug(f"💓 Heartbeat received from node {node_id}")

    def check_node_connectivity(self) -> List[str]:
        """
        Verificar conectividad de nodos.

        Returns:
            Lista de nodos offline
        """
        now = datetime.now()
        offline_nodes = []

        for node_id, node in self.node_status.items():
            time_since_last_seen = (now - node.last_seen).total_seconds()

            if time_since_last_seen > self.timeout_threshold:
                if node.is_online:  # Solo loguear transición
                    logger.warning(f"⚠️ Node {node_id} went offline (last seen: {node.last_seen})")
                    node.is_online = False
                    self.stats['offline_nodes'] += 1

                    # Crear evento de pérdida
                    self._create_loss_event(
                        loss_type=LossType.NODE_DISCONNECT,
                        affected_data=list(node.data_availability.keys()),
                        affected_nodes=[node_id],
                        severity='high',
                        description=f"Node {node_id} disconnected from network",
                        recovery_actions=[
                            f"Attempt reconnection to node {node_id}",
                            "Check network connectivity",
                            "Redistribute data to other nodes"
                        ]
                    )

                offline_nodes.append(node_id)
            else:
                # Reducir score gradualmente si no está completamente offline
                node.connectivity_score = max(0.0, node.connectivity_score - 0.01)

        return offline_nodes

    def check_data_availability(self) -> Dict[str, List[str]]:
        """
        Verificar disponibilidad de datos.

        Returns:
            Dict con data_id -> lista de nodos que lo tienen disponible
        """
        data_availability = {}

        for node_id, node in self.node_status.items():
            if not node.is_online:
                continue

            for data_id, available in node.data_availability.items():
                if data_id not in data_availability:
                    data_availability[data_id] = []

                if available:
                    data_availability[data_id].append(node_id)

        # Detectar datos con baja replicación
        for data_id, available_nodes in data_availability.items():
            if len(available_nodes) < self.min_replication_factor:
                self._create_loss_event(
                    loss_type=LossType.REPLICATION_FAILURE,
                    affected_data=[data_id],
                    affected_nodes=available_nodes,
                    severity='medium' if len(available_nodes) > 0 else 'critical',
                    description=f"Data {data_id} has insufficient replication ({len(available_nodes)}/{self.min_replication_factor})",
                    recovery_actions=[
                        f"Replicate data {data_id} to additional nodes",
                        "Check data integrity on available nodes",
                        "Trigger backup recovery if needed"
                    ]
                )

        return data_availability

    def detect_session_losses(self, active_sessions: Dict[str, Any]) -> List[LossEvent]:
        """
        Detectar pérdidas en sesiones federadas.

        Args:
            active_sessions: Sesiones activas con participantes

        Returns:
            Lista de eventos de pérdida detectados
        """
        events = []

        for session_id, session_info in active_sessions.items():
            expected_participants = set(session_info.get('participants', []))
            online_participants = set()

            # Verificar qué participantes están online
            for node_id in expected_participants:
                if node_id in self.node_status and self.node_status[node_id].is_online:
                    online_participants.add(node_id)

            missing_participants = expected_participants - online_participants

            if missing_participants:
                event = self._create_loss_event(
                    loss_type=LossType.SESSION_PARTICIPANT_MISSING,
                    affected_data=[],  # Los datos de la sesión
                    affected_nodes=list(missing_participants),
                    severity='high',
                    description=f"Session {session_id} missing {len(missing_participants)} participants",
                    recovery_actions=[
                        f"Wait for reconnection of nodes: {list(missing_participants)}",
                        f"Continue session {session_id} with remaining participants",
                        "Trigger session recovery procedures"
                    ],
                    metadata={
                        'session_id': session_id,
                        'expected_participants': len(expected_participants),
                        'online_participants': len(online_participants),
                        'missing_participants': list(missing_participants)
                    }
                )
                events.append(event)

        return events

    def detect_network_partition(self) -> Optional[LossEvent]:
        """
        Detectar particiones de red.

        Returns:
            Evento de partición si se detecta
        """
        online_nodes = [node_id for node_id, node in self.node_status.items() if node.is_online]
        offline_nodes = [node_id for node_id, node in self.node_status.items() if not node.is_online]

        # Algoritmo simple: si más del 50% de nodos están offline, posible partición
        if len(offline_nodes) > len(online_nodes) and len(offline_nodes) > 2:
            self.stats['network_partitions'] += 1

            return self._create_loss_event(
                loss_type=LossType.NETWORK_PARTITION,
                affected_data=[],  # Todos los datos potencialmente afectados
                affected_nodes=offline_nodes,
                severity='critical',
                description=f"Network partition detected: {len(offline_nodes)} nodes offline, {len(online_nodes)} online",
                recovery_actions=[
                    "Investigate network connectivity issues",
                    "Attempt to restore connectivity to offline nodes",
                    "Activate disaster recovery procedures",
                    "Consider session suspension if partition persists"
                ],
                metadata={
                    'offline_count': len(offline_nodes),
                    'online_count': len(online_nodes),
                    'partition_ratio': len(offline_nodes) / (len(offline_nodes) + len(online_nodes))
                }
            )

        return None

    def start_detection(self):
        """Iniciar detección continua de pérdidas."""
        if self.is_detecting:
            logger.warning("⚠️ Loss detection already running")
            return

        self.is_detecting = True
        self.stop_event.clear()
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()

        logger.info("🚀 Started continuous loss detection")

    def stop_detection(self):
        """Detener detección continua."""
        if not self.is_detecting:
            return

        self.is_detecting = False
        self.stop_event.set()

        if self.detection_thread:
            self.detection_thread.join(timeout=5)

        logger.info("⏹️ Stopped loss detection")

    def _detection_loop(self):
        """Bucle principal de detección."""
        while not self.stop_event.is_set():
            try:
                # Realizar verificaciones
                offline_nodes = self.check_node_connectivity()
                data_availability = self.check_data_availability()
                partition_event = self.detect_network_partition()

                self.stats['last_detection_time'] = datetime.now()

                # Log de resumen
                logger.info(f"🔍 Loss detection cycle: {len(offline_nodes)} offline nodes, "
                          f"{len(data_availability)} data items monitored")

            except Exception as e:
                logger.error(f"❌ Detection loop error: {e}")

            # Esperar hasta el próximo ciclo
            self.stop_event.wait(self.heartbeat_interval)

    def _create_loss_event(self, loss_type: LossType, affected_data: List[str],
                          affected_nodes: List[str], severity: str, description: str,
                          recovery_actions: List[str] = None, metadata: Dict[str, Any] = None) -> LossEvent:
        """Crear un evento de pérdida."""
        self.event_counter += 1
        event = LossEvent(
            event_id=f"loss_{self.event_counter}",
            loss_type=loss_type,
            affected_data=affected_data,
            affected_nodes=affected_nodes,
            timestamp=datetime.now(),
            severity=severity,
            description=description,
            recovery_actions=recovery_actions or [],
            metadata=metadata or {}
        )

        self.loss_events.append(event)

        # Mantener límite de eventos (últimos 1000)
        if len(self.loss_events) > 1000:
            self.loss_events = self.loss_events[-1000:]

        # Alertar
        if self.alert_callback:
            self.alert_callback('loss_detected', {
                'event_id': event.event_id,
                'loss_type': event.loss_type.value,
                'severity': event.severity,
                'description': event.description,
                'affected_nodes': event.affected_nodes,
                'affected_data': event.affected_data,
                'timestamp': event.timestamp.isoformat()
            })

        logger.warning(f"🚨 Loss event: {event.description} (severity: {event.severity})")
        return event

    def get_loss_events(self, limit: int = 50, severity_filter: List[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener eventos de pérdida recientes.

        Args:
            limit: Número máximo de eventos
            severity_filter: Filtrar por severidad

        Returns:
            Lista de eventos como dicts
        """
        events = self.loss_events[-limit:] if limit else self.loss_events

        if severity_filter:
            events = [e for e in events if e.severity in severity_filter]

        return [self._event_to_dict(e) for e in events]

    def get_node_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen de estado de nodos."""
        online_count = sum(1 for node in self.node_status.values() if node.is_online)
        offline_count = len(self.node_status) - online_count

        return {
            'total_nodes': len(self.node_status),
            'online_nodes': online_count,
            'offline_nodes': offline_count,
            'expected_nodes': len(self.expected_nodes),
            'online_percentage': (online_count / len(self.node_status)) * 100 if self.node_status else 0
        }

    def get_detection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de detección."""
        return {
            **self.stats,
            'is_detecting': self.is_detecting,
            'heartbeat_interval': self.heartbeat_interval,
            'timeout_threshold': self.timeout_threshold,
            'loss_events_count': len(self.loss_events),
            'active_loss_events': len([e for e in self.loss_events if e.timestamp > datetime.now() - timedelta(hours=1)])
        }

    def _event_to_dict(self, event: LossEvent) -> Dict[str, Any]:
        """Convertir evento a dict."""
        return {
            'event_id': event.event_id,
            'loss_type': event.loss_type.value,
            'affected_data': event.affected_data,
            'affected_nodes': event.affected_nodes,
            'timestamp': event.timestamp.isoformat(),
            'severity': event.severity,
            'description': event.description,
            'recovery_actions': event.recovery_actions,
            'metadata': event.metadata
        }

    def clear_old_events(self, max_age_hours: int = 24):
        """
        Limpiar eventos antiguos.

        Args:
            max_age_hours: Edad máxima en horas
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        self.loss_events = [e for e in self.loss_events if e.timestamp > cutoff]
        logger.info("🧹 Cleared old loss events")