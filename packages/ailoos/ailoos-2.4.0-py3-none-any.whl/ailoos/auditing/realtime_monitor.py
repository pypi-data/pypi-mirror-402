"""
Sistema de monitoreo en tiempo real para AILOOS.
Proporciona actualizaciones en vivo de métricas, alertas y eventos.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from collections import deque
import threading

from ..core.config import get_config
from .audit_manager import get_audit_manager
from .security_monitor import get_security_monitor
from .metrics_collector import get_metrics_collector
from .dashboard import get_audit_dashboard
from .structured_logger import get_structured_logger

logger = get_structured_logger("realtime_monitor")


class RealtimeMonitor:
    """
    Monitor en tiempo real que distribuye actualizaciones a clientes conectados.
    Maneja WebSocket connections y broadcasting de eventos.
    """

    def __init__(self):
        self.config = get_config()
        self.audit_manager = get_audit_manager()
        self.security_monitor = get_security_monitor()
        self.metrics_collector = get_metrics_collector()
        self.dashboard = get_audit_dashboard()

        # Conexiones activas
        self.active_connections: Dict[str, Set] = {
            'dashboard': set(),
            'alerts': set(),
            'metrics': set(),
            'security': set(),
            'kg_metrics': set(),
            'federated_nodes': set(),
            'federated_registry': set(),
            'federated_health': set(),
            'training_progress': set(),
            'training_participants': set(),
            'training_metrics': set(),
            'system_security_alerts': set(),
            'system_log_updates': set(),
            'system_config_changes': set()
        }

        # Buffers de eventos recientes
        self.recent_events: deque = deque(maxlen=100)
        self.recent_alerts: deque = deque(maxlen=50)
        self.recent_metrics: deque = deque(maxlen=20)

        # Configuración
        self.update_intervals = {
            'dashboard': getattr(self.config, 'realtime_dashboard_interval', 30),
            'alerts': getattr(self.config, 'realtime_alerts_interval', 10),
            'metrics': getattr(self.config, 'realtime_metrics_interval', 15),
            'security': getattr(self.config, 'realtime_security_interval', 20)
        }

        # Estado del monitor
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """Iniciar monitoreo en tiempo real."""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Registrar callbacks para eventos
        self._register_event_callbacks()

        logger.info("Realtime monitoring started")

    async def stop_monitoring(self):
        """Detener monitoreo en tiempo real."""
        self.is_running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # Cerrar todas las conexiones
        for connection_type, connections in self.active_connections.items():
            for connection in list(connections):
                try:
                    await connection.close()
                except:
                    pass
            connections.clear()

        logger.info("Realtime monitoring stopped")

    def _register_event_callbacks(self):
        """Registrar callbacks para eventos del sistema."""

        async def alert_callback(severity, title, description, context):
            """Callback para nuevas alertas."""
            alert_data = {
                "type": "new_alert",
                "timestamp": datetime.now().isoformat(),
                "severity": severity.value if hasattr(severity, 'value') else str(severity),
                "title": title,
                "description": description,
                "context": context
            }

            self.recent_alerts.append(alert_data)

            # Broadcast a conexiones de alertas
            await self._broadcast_to_type('alerts', alert_data)

        async def metrics_callback(metrics_data):
            """Callback para nuevas métricas."""
            metrics_update = {
                "type": "metrics_update",
                "timestamp": datetime.now().isoformat(),
                "data": metrics_data
            }

            self.recent_metrics.append(metrics_update)

            # Broadcast a conexiones de métricas
            await self._broadcast_to_type('metrics', metrics_update)

        # Registrar callbacks
        self.security_monitor.add_alert_callback(alert_callback)
        self.metrics_collector.add_metrics_callback(metrics_callback)

        # Callback para eventos de auditoría
        async def audit_event_callback(event):
            """Callback para nuevos eventos de auditoría."""
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "resource": event.resource,
                "action": event.action,
                "user_id": event.user_id,
                "severity": event.severity.value,
                "success": event.success,
                "details": event.details
            }

            # Agregar a buffer de eventos recientes
            self.recent_events.append(event_data)

            # Broadcast a conexiones de log updates
            await self._broadcast_to_type('system_log_updates', {
                "type": "audit_event",
                "data": event_data
            })

        self.audit_manager.add_event_callback(audit_event_callback)

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.is_running:
            try:
                # Actualizar datos del dashboard
                dashboard_data = await self.dashboard.get_dashboard_data()

                # Broadcast a conexiones de dashboard
                await self._broadcast_to_type('dashboard', {
                    "type": "dashboard_update",
                    "data": dashboard_data
                })

                # Broadcast actualizaciones de seguridad
                security_data = await self.dashboard.get_security_overview()
                await self._broadcast_to_type('security', {
                    "type": "security_update",
                    "data": security_data
                })

                # Broadcast actualizaciones de métricas KG
                kg_metrics = self.metrics_collector.get_latest_metrics().get('knowledge_graph')
                if kg_metrics:
                    await self._broadcast_to_type('kg_metrics', {
                        "type": "kg_metrics_update",
                        "data": kg_metrics
                    })

                # Esperar al siguiente ciclo
                await asyncio.sleep(min(self.update_intervals.values()))

            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(5)  # Esperar antes de reintentar

    async def _broadcast_to_type(self, connection_type: str, message: Dict[str, Any]):
        """Broadcast mensaje a un tipo de conexiones."""
        if connection_type not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[connection_type]:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Conexión cerrada o error
                disconnected.add(connection)
                logger.debug(f"Connection error in {connection_type}", error=str(e))

        # Limpiar conexiones desconectadas
        self.active_connections[connection_type] -= disconnected

    async def add_connection(self, connection_type: str, websocket_connection):
        """Agregar una nueva conexión WebSocket."""
        if connection_type not in self.active_connections:
            logger.warning(f"Unknown connection type: {connection_type}")
            return False

        self.active_connections[connection_type].add(websocket_connection)

        # Enviar datos iniciales
        try:
            if connection_type == 'dashboard':
                initial_data = await self.dashboard.get_dashboard_data()
                await websocket_connection.send_json({
                    "type": "initial_data",
                    "data": initial_data
                })

            elif connection_type == 'alerts':
                # Enviar alertas recientes
                recent_alerts = list(self.recent_alerts)[-10:]  # Últimas 10
                await websocket_connection.send_json({
                    "type": "recent_alerts",
                    "data": recent_alerts
                })

            elif connection_type == 'metrics':
                # Enviar métricas recientes
                recent_metrics = list(self.recent_metrics)[-5:]  # Últimas 5
                await websocket_connection.send_json({
                    "type": "recent_metrics",
                    "data": recent_metrics
                })

            elif connection_type == 'security':
                security_data = await self.dashboard.get_security_overview()
                await websocket_connection.send_json({
                    "type": "initial_security",
                    "data": security_data
                })

            elif connection_type == 'kg_metrics':
                kg_metrics = self.metrics_collector.get_latest_metrics().get('knowledge_graph')
                if kg_metrics:
                    await websocket_connection.send_json({
                        "type": "initial_kg_metrics",
                        "data": kg_metrics
                    })

            elif connection_type == 'system_security_alerts':
                # Enviar alertas recientes de seguridad del sistema
                recent_alerts = list(self.recent_alerts)[-10:]  # Últimas 10
                await websocket_connection.send_json({
                    "type": "recent_system_security_alerts",
                    "data": recent_alerts
                })

            elif connection_type == 'system_log_updates':
                # Enviar logs recientes del sistema
                recent_logs = list(self.recent_events)[-10:]  # Últimas 10
                await websocket_connection.send_json({
                    "type": "recent_system_logs",
                    "data": recent_logs
                })

            elif connection_type == 'system_config_changes':
                # Enviar cambios recientes de configuración
                # Por ahora, enviar datos vacíos ya que no tenemos buffer específico
                await websocket_connection.send_json({
                    "type": "recent_config_changes",
                    "data": []
                })

            logger.info(f"New {connection_type} connection added")
            return True

        except Exception as e:
            logger.error(f"Error adding {connection_type} connection", error=str(e))
            self.active_connections[connection_type].discard(websocket_connection)
            return False

    async def remove_connection(self, connection_type: str, websocket_connection):
        """Remover una conexión WebSocket."""
        if connection_type in self.active_connections:
            self.active_connections[connection_type].discard(websocket_connection)
            logger.info(f"{connection_type} connection removed")

    def get_connection_counts(self) -> Dict[str, int]:
        """Obtener conteo de conexiones por tipo."""
        return {
            conn_type: len(connections)
            for conn_type, connections in self.active_connections.items()
        }

    async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any],
                                   target_types: Optional[List[str]] = None):
        """Broadcast evento personalizado a tipos específicos de conexiones."""
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        if target_types is None:
            target_types = list(self.active_connections.keys())

        for conn_type in target_types:
            if conn_type in self.active_connections:
                await self._broadcast_to_type(conn_type, message)

    async def broadcast_federated_node_update(self, node_data: Dict[str, Any]):
        """Broadcast actualización de nodo federado."""
        message = {
            "type": "federated_node_update",
            "timestamp": datetime.now().isoformat(),
            "data": node_data
        }
        await self._broadcast_to_type('federated_nodes', message)

    async def broadcast_federated_registry_update(self, registry_data: Dict[str, Any]):
        """Broadcast actualización del registro de nodos federados."""
        message = {
            "type": "federated_registry_update",
            "timestamp": datetime.now().isoformat(),
            "data": registry_data
        }
        await self._broadcast_to_type('federated_registry', message)

    async def broadcast_federated_health_update(self, health_data: Dict[str, Any]):
        """Broadcast actualización de salud de la red federada."""
        message = {
            "type": "federated_health_update",
            "timestamp": datetime.now().isoformat(),
            "data": health_data
        }
        await self._broadcast_to_type('federated_health', message)

    async def broadcast_training_progress_update(self, session_id: str, progress_data: Dict[str, Any]):
        """Broadcast actualización de progreso de entrenamiento."""
        message = {
            "type": "training_progress_update",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": progress_data
        }
        await self._broadcast_to_type('training_progress', message)

    async def broadcast_training_participants_update(self, session_id: str, participants_data: Dict[str, Any]):
        """Broadcast actualización de participantes de entrenamiento."""
        message = {
            "type": "training_participants_update",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": participants_data
        }
        await self._broadcast_to_type('training_participants', message)

    async def broadcast_training_metrics_update(self, session_id: str, metrics_data: Dict[str, Any]):
        """Broadcast actualización de métricas de entrenamiento."""
        message = {
            "type": "training_metrics_update",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": metrics_data
        }
        await self._broadcast_to_type('training_metrics', message)

    async def broadcast_system_security_alert(self, alert_data: Dict[str, Any]):
        """Broadcast alerta de seguridad del sistema."""
        message = {
            "type": "system_security_alert",
            "timestamp": datetime.now().isoformat(),
            "data": alert_data
        }
        await self._broadcast_to_type('system_security_alerts', message)

    async def broadcast_system_log_update(self, log_data: Dict[str, Any]):
        """Broadcast actualización de logs del sistema."""
        message = {
            "type": "system_log_update",
            "timestamp": datetime.now().isoformat(),
            "data": log_data
        }
        await self._broadcast_to_type('system_log_updates', message)

    async def broadcast_system_config_change(self, config_data: Dict[str, Any]):
        """Broadcast cambio de configuración del sistema."""
        message = {
            "type": "system_config_change",
            "timestamp": datetime.now().isoformat(),
            "data": config_data
        }
        await self._broadcast_to_type('system_config_changes', message)

    async def get_realtime_snapshot(self) -> Dict[str, Any]:
        """Obtener snapshot completo del estado en tiempo real."""
        return {
            "timestamp": datetime.now().isoformat(),
            "connections": self.get_connection_counts(),
            "recent_events": list(self.recent_events),
            "recent_alerts": list(self.recent_alerts),
            "recent_metrics": list(self.recent_metrics),
            "system_status": {
                "monitoring_active": self.is_running,
                "active_connections_total": sum(len(conns) for conns in self.active_connections.values())
            }
        }


class RealtimeWebSocketHandler:
    """
    Manejador de WebSocket connections para monitoreo en tiempo real.
    """

    def __init__(self, realtime_monitor: RealtimeMonitor):
        self.monitor = realtime_monitor
        self.logger = get_structured_logger("websocket_handler")

    async def handle_connection(self, websocket, connection_type: str):
        """Manejar una nueva conexión WebSocket."""
        try:
            # Agregar conexión
            success = await self.monitor.add_connection(connection_type, websocket)
            if not success:
                await websocket.close(code=1008)  # Policy violation
                return

            # Mantener conexión viva y manejar mensajes
            while True:
                try:
                    # Esperar mensajes del cliente (ping/pong, etc.)
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                    # Procesar mensaje si es necesario
                    await self._handle_client_message(websocket, connection_type, message)

                except asyncio.TimeoutError:
                    # Enviar ping para mantener viva la conexión
                    await websocket.send_json({"type": "ping"})
                    continue

                except Exception as e:
                    # Error en la conexión
                    self.logger.debug(f"Connection error for {connection_type}", error=str(e))
                    break

        except Exception as e:
            self.logger.error(f"Error handling {connection_type} connection", error=str(e))

        finally:
            # Limpiar conexión
            await self.monitor.remove_connection(connection_type, websocket)

    async def _handle_client_message(self, websocket, connection_type: str, message: str):
        """Manejar mensajes del cliente."""
        try:
            data = json.loads(message)

            message_type = data.get('type')

            if message_type == 'subscribe':
                # Cliente quiere suscribirse a eventos adicionales
                subscriptions = data.get('subscriptions', [])
                # Aquí podríamos manejar suscripciones específicas
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "subscriptions": subscriptions
                })

            elif message_type == 'unsubscribe':
                # Cliente quiere desuscribirse
                subscriptions = data.get('subscriptions', [])
                await websocket.send_json({
                    "type": "unsubscription_confirmed",
                    "subscriptions": subscriptions
                })

            elif message_type == 'ping':
                # Responder pong
                await websocket.send_json({"type": "pong"})

            else:
                # Mensaje desconocido
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON message"
            })
        except Exception as e:
            self.logger.error("Error handling client message", error=str(e))
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })


# Instancias globales
realtime_monitor = RealtimeMonitor()
websocket_handler = RealtimeWebSocketHandler(realtime_monitor)


async def start_realtime_monitoring():
    """Iniciar monitoreo en tiempo real."""
    await realtime_monitor.start_monitoring()


async def stop_realtime_monitoring():
    """Detener monitoreo en tiempo real."""
    await realtime_monitor.stop_monitoring()


def get_realtime_monitor() -> RealtimeMonitor:
    """Obtener instancia global del monitor en tiempo real."""
    return realtime_monitor


def get_websocket_handler() -> RealtimeWebSocketHandler:
    """Obtener instancia global del manejador WebSocket."""
    return websocket_handler