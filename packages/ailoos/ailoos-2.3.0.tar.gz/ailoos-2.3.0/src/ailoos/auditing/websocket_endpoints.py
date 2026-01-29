"""
WebSocket endpoints para monitoreo en tiempo real de auditoría.
Proporciona conexiones en vivo para dashboard y alertas.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any, Optional
import asyncio

from ..core.config import get_config
from .realtime_monitor import get_realtime_monitor, get_websocket_handler
from .structured_logger import get_structured_logger
from ..coordinator.auth.dependencies import get_current_admin

router = APIRouter()
logger = get_structured_logger("websocket_audit")
realtime_monitor = get_realtime_monitor()
websocket_handler = get_websocket_handler()


@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para actualizaciones del dashboard en tiempo real.

    - **token**: Token de autenticación (opcional para desarrollo)
    """
    await websocket.accept()

    try:
        # Autenticación básica (en producción usar JWT)
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Dashboard WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "dashboard")

    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket connection closed")
    except Exception as e:
        logger.error("Dashboard WebSocket error", error=str(e))
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para alertas de seguridad en tiempo real.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Alerts WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "alerts")

    except WebSocketDisconnect:
        logger.info("Alerts WebSocket connection closed")
    except Exception as e:
        logger.error("Alerts WebSocket error", error=str(e))


@router.websocket("/metrics")
async def metrics_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para métricas del sistema en tiempo real.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Metrics WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "metrics")

    except WebSocketDisconnect:
        logger.info("Metrics WebSocket connection closed")
    except Exception as e:
        logger.error("Metrics WebSocket error", error=str(e))


@router.websocket("/security")
async def security_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para actualizaciones de seguridad en tiempo real.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Security WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "security")

    except WebSocketDisconnect:
        logger.info("Security WebSocket connection closed")
    except Exception as e:
        logger.error("Security WebSocket error", error=str(e))


@router.websocket("/federated/nodes")
async def federated_nodes_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real de nodos federados.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Federated Nodes WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "federated_nodes")

    except WebSocketDisconnect:
        logger.info("Federated Nodes WebSocket connection closed")
    except Exception as e:
        logger.error("Federated Nodes WebSocket error", error=str(e))


@router.websocket("/federated/registry")
async def federated_registry_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real del registro de nodos federados.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Federated Registry WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "federated_registry")

    except WebSocketDisconnect:
        logger.info("Federated Registry WebSocket connection closed")
    except Exception as e:
        logger.error("Federated Registry WebSocket error", error=str(e))


@router.websocket("/federated/health")
async def federated_health_websocket(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real de la salud de la red federada.

    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info("Federated Health WebSocket connection established")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "federated_health")

    except WebSocketDisconnect:
        logger.info("Federated Health WebSocket connection closed")
    except Exception as e:
        logger.error("Federated Health WebSocket error", error=str(e))


@router.websocket("/federated/training/{session_id}")
async def training_progress_websocket(websocket: WebSocket, session_id: str, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real del progreso de entrenamiento.

    - **session_id**: ID de la sesión de entrenamiento
    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info(f"Training Progress WebSocket connection established for session {session_id}")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "training_progress")

    except WebSocketDisconnect:
        logger.info(f"Training Progress WebSocket connection closed for session {session_id}")
    except Exception as e:
        logger.error("Training Progress WebSocket error", error=str(e))


@router.websocket("/federated/training/{session_id}/participants")
async def training_participants_websocket(websocket: WebSocket, session_id: str, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real de participantes.

    - **session_id**: ID de la sesión de entrenamiento
    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info(f"Training Participants WebSocket connection established for session {session_id}")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "training_participants")

    except WebSocketDisconnect:
        logger.info(f"Training Participants WebSocket connection closed for session {session_id}")
    except Exception as e:
        logger.error("Training Participants WebSocket error", error=str(e))


@router.websocket("/federated/training/{session_id}/metrics")
async def training_metrics_websocket(websocket: WebSocket, session_id: str, token: Optional[str] = None):
    """
    WebSocket para actualizaciones en tiempo real de métricas de entrenamiento.

    - **session_id**: ID de la sesión de entrenamiento
    - **token**: Token de autenticación
    """
    await websocket.accept()

    try:
        if token != "dev_token" and not await _authenticate_websocket(websocket, token):
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return

        logger.info(f"Training Metrics WebSocket connection established for session {session_id}")

        # Manejar conexión
        await websocket_handler.handle_connection(websocket, "training_metrics")

    except WebSocketDisconnect:
        logger.info(f"Training Metrics WebSocket connection closed for session {session_id}")
    except Exception as e:
        logger.error("Training Metrics WebSocket error", error=str(e))


async def _authenticate_websocket(websocket: WebSocket, token: str) -> bool:
    """
    Autenticar conexión WebSocket.

    En producción, esto debería validar JWT tokens.
    """
    try:
        # Para desarrollo, aceptar token simple
        if token == "dev_token":
            return True

        # En producción, validar JWT
        # from ..coordinator.auth.jwt import verify_token
        # payload = verify_token(token)
        # return payload is not None

        return False

    except Exception as e:
        logger.error("WebSocket authentication error", error=str(e))
        return False


@router.get("/ws/status", response_model=Dict[str, Any])
async def get_websocket_status(current_admin: Dict = Depends(get_current_admin)):
    """Obtener estado de conexiones WebSocket."""
    try:
        connection_counts = realtime_monitor.get_connection_counts()
        snapshot = await realtime_monitor.get_realtime_snapshot()

        return {
            "active_connections": connection_counts,
            "total_connections": sum(connection_counts.values()),
            "monitoring_active": realtime_monitor.is_running,
            "snapshot": snapshot
        }

    except Exception as e:
        logger.error("Error getting WebSocket status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving WebSocket status: {str(e)}")


@router.post("/ws/broadcast", response_model=Dict[str, Any])
async def broadcast_message(
    message: Dict[str, Any],
    target_types: Optional[list] = None,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Broadcast mensaje personalizado a conexiones WebSocket.

    - **message**: Mensaje a broadcast
    - **target_types**: Tipos de conexión objetivo (opcional)
    """
    try:
        event_type = message.get('type', 'custom_broadcast')

        await realtime_monitor.broadcast_custom_event(
            event_type=event_type,
            data=message,
            target_types=target_types
        )

        logger.log_user_action(
            "broadcast_message",
            current_admin.get('sub', 'unknown'),
            "websocket_broadcast",
            {"message_type": event_type, "target_types": target_types}
        )

        return {
            "success": True,
            "message": "Broadcast sent successfully",
            "target_types": target_types or list(realtime_monitor.active_connections.keys())
        }

    except Exception as e:
        logger.error("Error broadcasting message", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error broadcasting message: {str(e)}")


# Funciones de utilidad para integración con FastAPI
async def setup_websocket_audit_integration(app):
    """
    Configurar integración de WebSocket para auditoría.
    Esta función debe ser llamada al iniciar la aplicación.
    """
    try:
        # Iniciar monitoreo en tiempo real
        await realtime_monitor.start_monitoring()

        logger.info("WebSocket audit integration configured")

    except Exception as e:
        logger.error("Error setting up WebSocket audit integration", error=str(e))
        raise


async def cleanup_websocket_audit_integration():
    """
    Limpiar integración de WebSocket para auditoría.
    Esta función debe ser llamada al cerrar la aplicación.
    """
    try:
        await realtime_monitor.stop_monitoring()
        logger.info("WebSocket audit integration cleaned up")

    except Exception as e:
        logger.error("Error cleaning up WebSocket audit integration", error=str(e))