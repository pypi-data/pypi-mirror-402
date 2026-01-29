"""
API REST para Herramientas del Sistema (System Tools) de AILOOS.
Proporciona endpoints para configuración de seguridad, gestión de claves API, logs de auditoría y configuración del sistema.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..auditing.audit_manager import get_audit_manager, AuditEventType, SecurityAlertLevel
from ..auditing.security_monitor import SecurityMonitor
from ..auditing.structured_logger import get_structured_logger
from ..auditing.realtime_monitor import get_realtime_monitor, get_websocket_handler
from ..core.config import get_config, reload_config
from ..core.logging import get_logger

logger = get_logger(__name__)


class SecuritySettingsRequest(BaseModel):
    """Configuración de seguridad."""
    enable_encryption: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    enable_audit_logging: bool = True
    audit_log_retention_days: int = Field(365, ge=1, le=3650)
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = Field(100, ge=1, le=10000)
    enable_ip_whitelisting: bool = False
    allowed_ips: List[str] = Field(default_factory=list)


class APIKeyRequest(BaseModel):
    """Solicitud para crear clave API."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    permissions: List[str] = Field(default_factory=lambda: ["read"])
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650)


class APIKeyUpdateRequest(BaseModel):
    """Solicitud para actualizar clave API."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    active: Optional[bool] = None


class SystemConfigRequest(BaseModel):
    """Configuración del sistema."""
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    debug_mode: bool = False
    enable_telemetry: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = Field(24, ge=1, le=168)
    backup_retention_days: int = Field(30, ge=1, le=3650)


class APIKey:
    """Modelo de clave API."""
    def __init__(self, key_id: str, name: str, description: str, permissions: List[str], created_by: str, expires_at: Optional[datetime] = None):
        self.key_id = key_id
        self.name = name
        self.description = description
        self.permissions = permissions
        self.created_by = created_by
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.last_used = None
        self.active = True
        self.usage_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "active": self.active,
            "usage_count": self.usage_count,
            "is_expired": self.is_expired()
        }

    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.now() > self.expires_at


class SystemToolsAPI:
    """
    API REST completa para herramientas del sistema.
    Maneja configuración de seguridad, claves API, logs de auditoría y configuración del sistema.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS System Tools API",
            description="API REST para herramientas de administración del sistema AILOOS",
            version="1.0.0"
        )

        # Componentes del sistema
        self.audit_manager = get_audit_manager()
        self.security_monitor = SecurityMonitor()
        self.logger = get_structured_logger("system_tools_api")
        self.config = get_config()
        self.realtime_monitor = get_realtime_monitor()
        self.websocket_handler = get_websocket_handler()

        # Almacenamiento de claves API (en memoria - en producción usar base de datos)
        self.api_keys: Dict[str, APIKey] = {}
        self.api_key_secrets: Dict[str, str] = {}  # key_id -> secret

        # Inicializar componentes
        self._initialize_components()

        # Configurar rutas
        self._setup_routes()

        logger.info("🔧 System Tools API initialized")

    def _initialize_components(self):
        """Inicializar componentes del sistema."""
        try:
            # Cargar claves API existentes desde configuración o archivo
            self._load_api_keys()
        except Exception as e:
            logger.warning(f"Error loading API keys: {e}")

    def _load_api_keys(self):
        """Cargar claves API existentes."""
        # En producción, cargar desde base de datos o archivo seguro
        # Por ahora, inicializar vacío
        pass

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check de la API de herramientas del sistema."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {
                    "audit_manager": "active",
                    "security_monitor": "active",
                    "config": "loaded"
                }
            }

        # ===== SECURITY SETTINGS ENDPOINTS =====

        @self.app.get("/security/settings")
        async def get_security_settings():
            """Obtener configuración de seguridad actual."""
            try:
                config = get_config()
                return {
                    "enable_encryption": config.security.enable_encryption,
                    "encryption_algorithm": config.security.encryption_algorithm,
                    "enable_audit_logging": config.security.enable_audit_logging,
                    "audit_log_retention_days": config.security.audit_log_retention_days,
                    "enable_rate_limiting": config.security.enable_rate_limiting,
                    "rate_limit_requests_per_minute": config.security.rate_limit_requests_per_minute,
                    "enable_ip_whitelisting": config.security.enable_ip_whitelisting,
                    "allowed_ips": config.security.allowed_ips,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting security settings: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving security settings: {str(e)}")

        @self.app.options("/security/settings")
        async def options_security_settings():
            """OPTIONS handler for security settings."""
            return {"Allow": "GET, PUT, OPTIONS"}

        @self.app.put("/security/settings")
        async def update_security_settings(settings: SecuritySettingsRequest):
            """Actualizar configuración de seguridad."""
            try:
                config = get_config()

                # Actualizar configuración
                config.security.enable_encryption = settings.enable_encryption
                config.security.encryption_algorithm = settings.encryption_algorithm
                config.security.enable_audit_logging = settings.enable_audit_logging
                config.security.audit_log_retention_days = settings.audit_log_retention_days
                config.security.enable_rate_limiting = settings.enable_rate_limiting
                config.security.rate_limit_requests_per_minute = settings.rate_limit_requests_per_minute
                config.security.enable_ip_whitelisting = settings.enable_ip_whitelisting
                config.security.allowed_ips = settings.allowed_ips

                # Guardar configuración
                config.save_to_file("./config/security_config.json")

                # Registrar cambio en auditoría
                await self.audit_manager.log_event(
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource="security_settings",
                    action="update",
                    user_id="system_admin",  # En producción, obtener del contexto de autenticación
                    details=settings.dict(),
                    severity=SecurityAlertLevel.MEDIUM
                )

                # Log del cambio
                self.logger.log_config_change(
                    key="security_settings",
                    old_value="previous",
                    new_value=settings.dict(),
                    changed_by="system_admin"
                )

                # Broadcast cambio de configuración
                await self.realtime_monitor.broadcast_system_config_change({
                    "config_type": "security_settings",
                    "old_settings": "previous",
                    "new_settings": settings.dict(),
                    "changed_by": "system_admin"
                })

                return {
                    "message": "Security settings updated successfully",
                    "settings": settings.dict(),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error updating security settings: {e}")
                raise HTTPException(status_code=500, detail=f"Error updating security settings: {str(e)}")

        # ===== API KEYS ENDPOINTS =====

        @self.app.get("/keys")
        async def get_api_keys():
            """Obtener todas las claves API."""
            try:
                keys = []
                for key_id, api_key in self.api_keys.items():
                    key_data = api_key.to_dict()
                    key_data["secret"] = None  # No devolver el secreto
                    keys.append(key_data)

                return {
                    "keys": keys,
                    "total": len(keys),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting API keys: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving API keys: {str(e)}")

        @self.app.post("/keys")
        async def create_api_key(key_request: APIKeyRequest):
            """Crear nueva clave API."""
            try:
                import secrets

                key_id = secrets.token_hex(8)
                secret = secrets.token_hex(32)

                expires_at = None
                if key_request.expires_in_days:
                    expires_at = datetime.now() + timedelta(days=key_request.expires_in_days)

                api_key = APIKey(
                    key_id=key_id,
                    name=key_request.name,
                    description=key_request.description,
                    permissions=key_request.permissions,
                    created_by="system_admin",  # En producción, obtener del contexto
                    expires_at=expires_at
                )

                self.api_keys[key_id] = api_key
                self.api_key_secrets[key_id] = secret

                # Registrar en auditoría
                await self.audit_manager.log_event(
                    event_type=AuditEventType.SECURITY_ALERT,
                    resource=f"api_key:{key_id}",
                    action="create",
                    user_id="system_admin",
                    details={
                        "key_name": key_request.name,
                        "permissions": key_request.permissions,
                        "expires_in_days": key_request.expires_in_days
                    },
                    severity=SecurityAlertLevel.LOW
                )

                return {
                    "message": "API key created successfully",
                    "key": api_key.to_dict(),
                    "secret": secret,  # Solo devolver en la creación
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error creating API key: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")

        @self.app.get("/keys/{key_id}")
        async def get_api_key(key_id: str):
            """Obtener detalles de una clave API específica."""
            try:
                if key_id not in self.api_keys:
                    raise HTTPException(status_code=404, detail="API key not found")

                api_key = self.api_keys[key_id]
                key_data = api_key.to_dict()
                key_data["secret"] = None  # No devolver el secreto

                return key_data
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting API key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving API key: {str(e)}")

        @self.app.put("/keys/{key_id}")
        async def update_api_key(key_id: str, update_request: APIKeyUpdateRequest):
            """Actualizar clave API."""
            try:
                if key_id not in self.api_keys:
                    raise HTTPException(status_code=404, detail="API key not found")

                api_key = self.api_keys[key_id]
                old_values = api_key.to_dict()

                # Actualizar campos
                if update_request.name is not None:
                    api_key.name = update_request.name
                if update_request.description is not None:
                    api_key.description = update_request.description
                if update_request.permissions is not None:
                    api_key.permissions = update_request.permissions
                if update_request.active is not None:
                    api_key.active = update_request.active

                # Registrar cambio
                await self.audit_manager.log_event(
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource=f"api_key:{key_id}",
                    action="update",
                    user_id="system_admin",
                    details={
                        "old_values": old_values,
                        "new_values": api_key.to_dict()
                    },
                    severity=SecurityAlertLevel.LOW
                )

                key_data = api_key.to_dict()
                key_data["secret"] = None

                return {
                    "message": "API key updated successfully",
                    "key": key_data,
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating API key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Error updating API key: {str(e)}")

        @self.app.delete("/keys/{key_id}")
        async def delete_api_key(key_id: str):
            """Eliminar clave API."""
            try:
                if key_id not in self.api_keys:
                    raise HTTPException(status_code=404, detail="API key not found")

                api_key = self.api_keys[key_id]
                old_values = api_key.to_dict()

                # Eliminar
                del self.api_keys[key_id]
                if key_id in self.api_key_secrets:
                    del self.api_key_secrets[key_id]

                # Registrar eliminación
                await self.audit_manager.log_event(
                    event_type=AuditEventType.SECURITY_ALERT,
                    resource=f"api_key:{key_id}",
                    action="delete",
                    user_id="system_admin",
                    details=old_values,
                    severity=SecurityAlertLevel.MEDIUM
                )

                return {
                    "message": "API key deleted successfully",
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting API key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Error deleting API key: {str(e)}")

        # ===== AUDIT LOGS ENDPOINTS =====

        @self.app.get("/logs")
        async def get_audit_logs(
            event_type: Optional[str] = None,
            user_id: Optional[str] = None,
            resource: Optional[str] = None,
            severity: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Obtener logs de auditoría."""
            try:
                # Convertir parámetros
                event_type_filter = None
                if event_type:
                    try:
                        event_type_filter = AuditEventType(event_type)
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")

                severity_filter = None
                if severity:
                    try:
                        severity_filter = SecurityAlertLevel(severity)
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

                start_dt = None
                if start_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")

                end_dt = None
                if end_date:
                    try:
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

                # Obtener eventos
                events = self.audit_manager.get_audit_events(
                    event_type=event_type_filter,
                    user_id=user_id,
                    resource=resource,
                    start_date=start_dt,
                    end_date=end_dt,
                    limit=limit
                )

                # Filtrar por severidad si se especifica
                if severity_filter:
                    events = [e for e in events if e.severity == severity_filter]

                return {
                    "logs": [event.to_dict() for event in events],
                    "total": len(events),
                    "filters": {
                        "event_type": event_type,
                        "user_id": user_id,
                        "resource": resource,
                        "severity": severity,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit
                    },
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting audit logs: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving audit logs: {str(e)}")

        @self.app.get("/logs/statistics")
        async def get_audit_statistics():
            """Obtener estadísticas de logs de auditoría."""
            try:
                stats = self.audit_manager.get_audit_statistics()
                return {
                    "statistics": stats,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting audit statistics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving audit statistics: {str(e)}")

        # ===== SYSTEM CONFIGURATION ENDPOINTS =====

        @self.app.get("/config")
        async def get_system_config():
            """Obtener configuración del sistema."""
            try:
                config = get_config()
                return {
                    "log_level": config.log_level,
                    "debug_mode": config.debug_mode,
                    "enable_telemetry": config.enable_telemetry,
                    "telemetry_endpoint": config.telemetry_endpoint,
                    "backup_enabled": config.backup_enabled,
                    "backup_interval_hours": config.backup_interval_hours,
                    "backup_retention_days": config.backup_retention_days,
                    "environment": config.environment,
                    "version": config.version,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting system config: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving system config: {str(e)}")

        @self.app.put("/config")
        async def update_system_config(config_request: SystemConfigRequest):
            """Actualizar configuración del sistema."""
            try:
                config = get_config()
                old_config = {
                    "log_level": config.log_level,
                    "debug_mode": config.debug_mode,
                    "enable_telemetry": config.enable_telemetry,
                    "backup_enabled": config.backup_enabled,
                    "backup_interval_hours": config.backup_interval_hours,
                    "backup_retention_days": config.backup_retention_days
                }

                # Actualizar configuración
                config.log_level = config_request.log_level
                config.debug_mode = config_request.debug_mode
                config.enable_telemetry = config_request.enable_telemetry
                config.backup_enabled = config_request.backup_enabled
                config.backup_interval_hours = config_request.backup_interval_hours
                config.backup_retention_days = config_request.backup_retention_days

                # Guardar configuración
                config.save_to_file("./config/system_config.json")

                # Recargar configuración
                reload_config()

                # Registrar cambio
                await self.audit_manager.log_event(
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource="system_config",
                    action="update",
                    user_id="system_admin",
                    details={
                        "old_config": old_config,
                        "new_config": config_request.dict()
                    },
                    severity=SecurityAlertLevel.HIGH
                )

                self.logger.log_config_change(
                    key="system_config",
                    old_value=old_config,
                    new_value=config_request.dict(),
                    changed_by="system_admin"
                )

                # Broadcast cambio de configuración
                await self.realtime_monitor.broadcast_system_config_change({
                    "config_type": "system_config",
                    "old_config": old_config,
                    "new_config": config_request.dict(),
                    "changed_by": "system_admin"
                })

                return {
                    "message": "System configuration updated successfully",
                    "config": config_request.dict(),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error updating system config: {e}")
                raise HTTPException(status_code=500, detail=f"Error updating system config: {str(e)}")

        @self.app.post("/config/reload")
        async def reload_system_config():
            """Recargar configuración del sistema."""
            try:
                old_config = get_config()
                new_config = reload_config()

                # Registrar recarga
                await self.audit_manager.log_event(
                    event_type=AuditEventType.CONFIG_CHANGE,
                    resource="system_config",
                    action="reload",
                    user_id="system_admin",
                    details={
                        "old_version": old_config.version,
                        "new_version": new_config.version
                    },
                    severity=SecurityAlertLevel.MEDIUM
                )

                return {
                    "message": "System configuration reloaded successfully",
                    "config": {
                        "log_level": new_config.log_level,
                        "debug_mode": new_config.debug_mode,
                        "environment": new_config.environment,
                        "version": new_config.version
                    },
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error reloading system config: {e}")
                raise HTTPException(status_code=500, detail=f"Error reloading system config: {str(e)}")

        # ===== WEBSOCKET ENDPOINTS =====

        @self.app.websocket("/ws/security-alerts")
        async def websocket_security_alerts(websocket: WebSocket, token: str = None):
            """
            WebSocket para alertas de seguridad en tiempo real.

            - **token**: Token de autenticación (opcional para desarrollo)
            """
            await websocket.accept()

            try:
                # Autenticación básica (en producción usar JWT)
                if token != "dev_token" and not await self._authenticate_websocket(websocket, token):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication failed"
                    })
                    await websocket.close(code=1008)
                    return

                self.logger.info("Security Alerts WebSocket connection established")

                # Manejar conexión
                await self.websocket_handler.handle_connection(websocket, "system_security_alerts")

            except WebSocketDisconnect:
                self.logger.info("Security Alerts WebSocket connection closed")
            except Exception as e:
                self.logger.error("Security Alerts WebSocket error", error=str(e))
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Internal server error"
                    })
                except:
                    pass

        @self.app.websocket("/ws/log-updates")
        async def websocket_log_updates(websocket: WebSocket, token: str = None):
            """
            WebSocket para actualizaciones de logs en tiempo real.

            - **token**: Token de autenticación
            """
            await websocket.accept()

            try:
                if token != "dev_token" and not await self._authenticate_websocket(websocket, token):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication failed"
                    })
                    await websocket.close(code=1008)
                    return

                self.logger.info("Log Updates WebSocket connection established")

                # Manejar conexión
                await self.websocket_handler.handle_connection(websocket, "system_log_updates")

            except WebSocketDisconnect:
                self.logger.info("Log Updates WebSocket connection closed")
            except Exception as e:
                self.logger.error("Log Updates WebSocket error", error=str(e))

        @self.app.websocket("/ws/config-changes")
        async def websocket_config_changes(websocket: WebSocket, token: str = None):
            """
            WebSocket para cambios de configuración en tiempo real.

            - **token**: Token de autenticación
            """
            await websocket.accept()

            try:
                if token != "dev_token" and not await self._authenticate_websocket(websocket, token):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication failed"
                    })
                    await websocket.close(code=1008)
                    return

                self.logger.info("Config Changes WebSocket connection established")

                # Manejar conexión
                await self.websocket_handler.handle_connection(websocket, "system_config_changes")

            except WebSocketDisconnect:
                self.logger.info("Config Changes WebSocket connection closed")
            except Exception as e:
                self.logger.error("Config Changes WebSocket error", error=str(e))

    async def _authenticate_websocket(self, websocket: WebSocket, token: str) -> bool:
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
            self.logger.error("WebSocket authentication error", error=str(e))
            return False

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8005):
        """Iniciar servidor FastAPI."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API
system_tools_api = SystemToolsAPI()


def create_system_tools_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI de herramientas del sistema."""
    return system_tools_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🔧 Iniciando AILOOS System Tools API...")
    system_tools_api.start_server()