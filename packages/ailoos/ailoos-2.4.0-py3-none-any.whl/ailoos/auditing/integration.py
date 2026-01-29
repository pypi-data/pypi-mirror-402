"""
Integración del sistema de auditoría con componentes existentes de AILOOS.
Configura hooks y middlewares para logging automático.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from ..core.config import get_config
from .audit_manager import get_audit_manager
from .security_monitor import get_security_monitor
from .metrics_collector import get_metrics_collector
from .structured_logger import get_structured_logger
from ..coordinator.websocket.notification_service import NotificationService

logger = get_structured_logger("audit_integration")


class AuditIntegration:
    """
    Integrador del sistema de auditoría con componentes existentes.
    Configura hooks automáticos para logging y monitoreo.
    """

    def __init__(self):
        self.config = get_config()
        self.audit_manager = get_audit_manager()
        self.security_monitor = get_security_monitor()
        self.metrics_collector = get_metrics_collector()
        self.notification_service: Optional[NotificationService] = None

        # Hooks registrados
        self.hooks: Dict[str, list] = {
            'config_change': [],
            'user_action': [],
            'api_request': [],
            'security_event': [],
            'federated_event': [],
            'marketplace_event': []
        }

    async def initialize(self):
        """Inicializar integración de auditoría."""
        logger.info("Initializing audit integration")

        # Configurar notificaciones
        await self._setup_notifications()

        # Registrar hooks en componentes existentes
        await self._register_component_hooks()

        # Configurar alertas automáticas
        self._setup_alert_callbacks()

        logger.info("Audit integration initialized successfully")

    async def _setup_notifications(self):
        """Configurar servicio de notificaciones para alertas."""
        try:
            # Intentar importar y configurar servicio de notificaciones
            from ..coordinator.websocket.notification_service import get_notification_service
            self.notification_service = get_notification_service()

            # Conectar servicios
            self.audit_manager.set_notification_service(self.notification_service)

            logger.info("Notification service connected to audit system")

        except ImportError:
            logger.warning("Notification service not available, alerts will be logged only")

    async def _register_component_hooks(self):
        """Registrar hooks en componentes existentes."""
        # Hook para cambios de configuración
        await self._register_config_hooks()

        # Hook para API requests
        await self._register_api_hooks()

        # Hook para eventos federados
        await self._register_federated_hooks()

        # Hook para marketplace
        await self._register_marketplace_hooks()

        # Hook para eventos de usuario
        await self._register_user_hooks()

    async def _register_config_hooks(self):
        """Registrar hooks para cambios de configuración."""
        try:
            from ..core.config import config

            # Monkey patch del método set_async para agregar auditoría
            original_set_async = config.set_async

            async def audited_set_async(key, value, description="", category="general",
                                      changed_by="system", change_reason=""):
                # Ejecutar cambio original
                result = await original_set_async(key, value, description, category, changed_by, change_reason)

                # Registrar en auditoría
                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.CONFIG_CHANGE,
                    resource=f"config:{key}",
                    action="change",
                    user_id=changed_by,
                    details={
                        "key": key,
                        "new_value": str(value)[:200],
                        "description": description,
                        "category": category,
                        "change_reason": change_reason
                    },
                    severity=self.audit_manager.SecurityAlertLevel.LOW,
                    success=True
                )

                # Ejecutar hooks personalizados
                await self._execute_hooks('config_change', {
                    'key': key,
                    'value': value,
                    'changed_by': changed_by,
                    'change_reason': change_reason
                })

                return result

            config.set_async = audited_set_async
            logger.info("Config change hooks registered")

        except Exception as e:
            logger.error(f"Error registering config hooks: {e}")

    async def _register_api_hooks(self):
        """Registrar hooks para requests API."""
        try:
            # Esto se haría en el middleware FastAPI
            # Por ahora, solo registramos que está disponible
            logger.info("API request hooks available for middleware integration")

        except Exception as e:
            logger.error(f"Error registering API hooks: {e}")

    async def _register_federated_hooks(self):
        """Registrar hooks para eventos federados."""
        try:
            from ..federated.coordinator import get_federated_coordinator

            coordinator = get_federated_coordinator()

            # Hook para eventos de rondas
            original_start_round = coordinator.start_round

            async def audited_start_round(*args, **kwargs):
                result = await original_start_round(*args, **kwargs)

                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.SYSTEM_OPERATION,
                    resource="federated_learning",
                    action="round_started",
                    details={"round_id": result.get('round_id') if isinstance(result, dict) else str(result)},
                    severity=self.audit_manager.SecurityAlertLevel.LOW,
                    success=True
                )

                await self._execute_hooks('federated_event', {
                    'event_type': 'round_started',
                    'round_id': result.get('round_id') if isinstance(result, dict) else str(result)
                })

                return result

            coordinator.start_round = audited_start_round
            logger.info("Federated learning hooks registered")

        except ImportError:
            logger.warning("Federated coordinator not available for hooks")
        except Exception as e:
            logger.error(f"Error registering federated hooks: {e}")

    async def _register_marketplace_hooks(self):
        """Registrar hooks para marketplace."""
        try:
            from ..marketplace.marketplace import get_marketplace

            marketplace = get_marketplace()

            # Hook para transacciones
            original_create_transaction = marketplace.create_transaction

            async def audited_create_transaction(*args, **kwargs):
                result = await original_create_transaction(*args, **kwargs)

                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.USER_ACTION,
                    resource="marketplace",
                    action="transaction_created",
                    user_id=kwargs.get('buyer_id'),
                    details={
                        "transaction_id": result.get('transaction_id'),
                        "amount": result.get('amount'),
                        "seller_id": result.get('seller_id')
                    },
                    severity=self.audit_manager.SecurityAlertLevel.LOW,
                    success=True
                )

                await self._execute_hooks('marketplace_event', {
                    'event_type': 'transaction_created',
                    'transaction': result
                })

                return result

            marketplace.create_transaction = audited_create_transaction
            logger.info("Marketplace hooks registered")

        except ImportError:
            logger.warning("Marketplace not available for hooks")
        except Exception as e:
            logger.error(f"Error registering marketplace hooks: {e}")

    async def _register_user_hooks(self):
        """Registrar hooks para acciones de usuario."""
        try:
            # Esto se integraría con el sistema de autenticación
            logger.info("User action hooks available for auth integration")

        except Exception as e:
            logger.error(f"Error registering user hooks: {e}")

    def _setup_alert_callbacks(self):
        """Configurar callbacks para alertas de seguridad."""
        async def security_alert_callback(severity, title, description, context):
            """Callback para alertas de seguridad."""
            # Log adicional
            logger.log_security_event(
                "alert_triggered",
                {
                    "severity": severity.value if hasattr(severity, 'value') else str(severity),
                    "title": title,
                    "description": description,
                    "context": context
                },
                severity if hasattr(severity, 'value') else self.audit_manager.SecurityAlertLevel.MEDIUM
            )

            # Notificación en tiempo real si disponible
            if self.notification_service:
                await self.notification_service.send_security_notification(
                    node_id="system",
                    event_type="security_alert",
                    details=f"{title}: {description}"
                )

        async def metrics_callback(metrics_data):
            """Callback para nuevas métricas."""
            # Verificar umbrales de rendimiento
            resource_metrics = metrics_data.get('resource', {})
            cpu_usage = resource_metrics.get('cpu_usage_percent', 0)
            memory_usage = resource_metrics.get('memory_usage_percent', 0)

            if cpu_usage > 90:
                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.PERFORMANCE_ISSUE,
                    resource="system",
                    action="high_cpu_usage",
                    details={"cpu_usage": cpu_usage},
                    severity=self.audit_manager.SecurityAlertLevel.HIGH,
                    success=False
                )

            if memory_usage > 95:
                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.PERFORMANCE_ISSUE,
                    resource="system",
                    action="high_memory_usage",
                    details={"memory_usage": memory_usage},
                    severity=self.audit_manager.SecurityAlertLevel.CRITICAL,
                    success=False
                )

        self.security_monitor.add_alert_callback(security_alert_callback)
        self.metrics_collector.add_metrics_callback(metrics_callback)

    async def _execute_hooks(self, hook_type: str, data: Dict[str, Any]):
        """Ejecutar hooks registrados para un tipo."""
        if hook_type in self.hooks:
            for hook_func in self.hooks[hook_type]:
                try:
                    await hook_func(data)
                except Exception as e:
                    logger.error(f"Error executing {hook_type} hook: {e}")

    def register_hook(self, hook_type: str, hook_func: Callable):
        """Registrar un hook personalizado."""
        if hook_type not in self.hooks:
            self.hooks[hook_type] = []

        self.hooks[hook_type].append(hook_func)
        logger.info(f"Custom hook registered: {hook_type}")

    async def log_custom_event(self, event_type: str, resource: str, action: str,
                             user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                             severity=None):
        """Registrar evento personalizado."""
        if severity is None:
            severity = self.audit_manager.SecurityAlertLevel.LOW

        await self.audit_manager.log_event(
            event_type=self.audit_manager.AuditEventType.SYSTEM_OPERATION,
            resource=resource,
            action=action,
            user_id=user_id,
            details=details or {},
            severity=severity,
            success=True
        )

    def create_audit_middleware(self):
        """Crear middleware para auditoría automática de requests."""
        from fastapi import Request, Response
        import time

        async def audit_middleware(request: Request, call_next):
            start_time = time.time()

            # Extraer información de la request
            user_id = None
            if hasattr(request.state, 'user') and request.state.user:
                user_id = request.state.user.get('sub')

            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get('user-agent')

            try:
                # Procesar request
                response = await call_next(request)

                # Calcular duración
                duration_ms = (time.time() - start_time) * 1000

                # Registrar en métricas
                self.metrics_collector.record_response_time(duration_ms)
                self.metrics_collector.record_request(f"{request.method} {request.url.path}")

                # Registrar en auditoría si es request importante
                if response.status_code >= 400 or duration_ms > 5000:
                    severity = self.audit_manager.SecurityAlertLevel.MEDIUM if response.status_code >= 500 else self.audit_manager.SecurityAlertLevel.LOW

                    await self.audit_manager.log_event(
                        event_type=self.audit_manager.AuditEventType.SYSTEM_OPERATION,
                        resource=f"api:{request.url.path}",
                        action=f"{request.method.lower()}_request",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                            "query_params": dict(request.query_params),
                            "user_agent": user_agent
                        },
                        severity=severity,
                        success=response.status_code < 400,
                        processing_time_ms=duration_ms
                    )

                # Procesar en monitor de seguridad
                await self.security_monitor.process_event({
                    "event_type": "API_REQUEST",
                    "resource": f"api:{request.url.path}",
                    "action": f"{request.method.lower()}_request",
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "details": {
                        "status_code": response.status_code,
                        "duration_ms": duration_ms
                    },
                    "timestamp": datetime.now().isoformat(),
                    "success": response.status_code < 400
                })

                return response

            except Exception as e:
                # Error en la request
                duration_ms = (time.time() - start_time) * 1000

                self.metrics_collector.record_error(f"{request.method} {request.url.path}", type(e).__name__)

                await self.audit_manager.log_event(
                    event_type=self.audit_manager.AuditEventType.SYSTEM_OPERATION,
                    resource=f"api:{request.url.path}",
                    action=f"{request.method.lower()}_request",
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": duration_ms
                    },
                    severity=self.audit_manager.SecurityAlertLevel.HIGH,
                    success=False,
                    processing_time_ms=duration_ms
                )

                raise

        return audit_middleware

    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema de auditoría."""
        return {
            "audit_manager": {
                "events_count": len(self.audit_manager.audit_events),
                "alerts_count": len(self.audit_manager.security_alerts),
                "active_sessions": len(self.audit_manager.active_sessions)
            },
            "security_monitor": self.security_monitor.get_security_status(),
            "metrics_collector": {
                "latest_metrics": self.metrics_collector.get_latest_metrics(),
                "health_status": self.metrics_collector.get_health_status()
            },
            "hooks_registered": {hook_type: len(hooks) for hook_type, hooks in self.hooks.items()},
            "timestamp": datetime.now().isoformat()
        }


# Instancia global
audit_integration = AuditIntegration()


async def initialize_audit_integration():
    """Inicializar integración de auditoría."""
    await audit_integration.initialize()


def get_audit_integration() -> AuditIntegration:
    """Obtener instancia global de integración de auditoría."""
    return audit_integration