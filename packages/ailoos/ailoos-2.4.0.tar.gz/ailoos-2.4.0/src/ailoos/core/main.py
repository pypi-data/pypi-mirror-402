"""
Script principal de inicio para AILOOS completamente integrado.
Inicia todos los servicios del sistema de manera coordinada.
"""

import asyncio
import signal
import sys
from typing import List, Dict, Any
import time

from .config import get_config
from .state_manager import get_state_manager, ComponentStatus
from .event_system import get_event_bus
from .notification_system import get_notification_manager
from .api_gateway import get_api_gateway, start_api_gateway
from ..utils.logging import get_logger
from ..monitoring.unified_dashboard import start_unified_dashboard


logger = get_logger(__name__)


class AiloosSystem:
    """
    Sistema principal de AILOOS que coordina todos los componentes.
    """

    def __init__(self):
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.event_bus = get_event_bus()
        self.notification_manager = get_notification_manager()
        self.api_gateway = get_api_gateway()

        self.running_tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

        logger.info("🚀 AILOOS System inicializado")

    async def initialize_system(self):
        """Inicializar todos los componentes del sistema."""
        try:
            logger.info("🔧 Inicializando componentes del sistema...")

            # Registrar componentes principales en el state manager
            self.state_manager.register_component("system_core", {
                "type": "core",
                "components": ["config", "state_manager", "event_bus", "notifications"]
            })

            # Iniciar event bus
            await self.event_bus.start()
            self.state_manager.update_component_status("event_bus", ComponentStatus.RUNNING)

            # Iniciar notification manager
            await self.notification_manager.start_listening()
            self.state_manager.update_component_status("notification_manager", ComponentStatus.RUNNING)

            # Iniciar monitoreo del state manager
            await self.state_manager.start_monitoring()

            logger.info("✅ Sistema inicializado correctamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            raise

    async def start_services(self):
        """Iniciar todos los servicios."""
        try:
            logger.info("🌟 Iniciando servicios de AILOOS...")

            # Iniciar API Gateway
            gateway_task = asyncio.create_task(
                start_api_gateway(
                    host=self.config.api.compliance_host,
                    port=self.config.api.dashboard_port
                )
            )
            self.running_tasks.append(gateway_task)
            self.state_manager.update_component_status("api_gateway", ComponentStatus.RUNNING)

            # Iniciar Dashboard Unificado
            dashboard_task = asyncio.create_task(
                start_unified_dashboard(
                    host=self.config.api.compliance_host,
                    port=self.config.api.dashboard_port + 1  # Puerto siguiente
                )
            )
            self.running_tasks.append(dashboard_task)
            self.state_manager.update_component_status("unified_dashboard", ComponentStatus.RUNNING)

            # Aquí se podrían iniciar otros servicios como:
            # - API de Compliance
            # - API Federada
            # - API de Marketplace
            # - API de Wallet
            # - Servicios de monitoreo
            # - etc.

            logger.info("✅ Servicios iniciados correctamente")
            logger.info(f"📊 Dashboard disponible en: http://localhost:{self.config.api.dashboard_port + 1}")
            logger.info(f"🚪 API Gateway disponible en: http://localhost:{self.config.api.dashboard_port}")

        except Exception as e:
            logger.error(f"❌ Error iniciando servicios: {e}")
            raise

    async def monitor_system_health(self):
        """Monitorear salud del sistema."""
        while not self.shutdown_event.is_set():
            try:
                # Verificar salud del sistema
                system_health = self.state_manager.get_system_health()

                if system_health.value == "critical":
                    logger.critical("🚨 Sistema en estado CRÍTICO")
                    await self.notification_manager.send_custom_notification(
                        "🚨 SISTEMA CRÍTICO",
                        "El sistema AILOOS está en estado crítico. Requiere atención inmediata.",
                        channels=["discord", "telegram", "email"]
                    )
                elif system_health.value == "degraded":
                    logger.warning("⚠️ Sistema degradado")
                    await self.notification_manager.send_custom_notification(
                        "⚠️ SISTEMA DEGRADADO",
                        "El sistema AILOOS está funcionando de manera degradada.",
                        channels=["discord"]
                    )

                # Log de estado periódico
                status = self.state_manager.get_system_status()
                logger.info(
                    f"📊 Estado del sistema: {system_health.value} | "
                    f"Componentes: {status['components_running']}/{status['total_components']} | "
                    f"Uptime: {status['system_uptime_seconds']:.0f}s"
                )

                await asyncio.sleep(60)  # Verificar cada minuto

            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {e}")
                await asyncio.sleep(30)

    async def graceful_shutdown(self):
        """Apagar el sistema de manera graceful."""
        logger.info("🛑 Iniciando apagado graceful del sistema...")

        # Señalar shutdown
        self.shutdown_event.set()

        # Cancelar tareas en ejecución
        for task in self.running_tasks:
            if not task.done():
                task.cancel()

        # Esperar a que las tareas terminen
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)

        # Apagar componentes
        await self.state_manager.stop_monitoring()
        await self.event_bus.stop()

        # Guardar estado final
        self.state_manager.save_state_to_file("data/system_shutdown_state.json")

        logger.info("✅ Sistema apagado correctamente")

    async def run(self):
        """Ejecutar el sistema completo."""
        # Configurar signal handlers
        def signal_handler(signum, frame):
            logger.info(f"📡 Señal {signum} recibida, iniciando shutdown...")
            asyncio.create_task(self.graceful_shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Inicializar sistema
            await self.initialize_system()

            # Iniciar servicios
            await self.start_services()

            # Iniciar monitoreo de salud
            monitor_task = asyncio.create_task(self.monitor_system_health())
            self.running_tasks.append(monitor_task)

            # Publicar evento de sistema iniciado
            await self.event_bus.publish("system.started", {
                "timestamp": time.time(),
                "version": self.config.version,
                "environment": self.config.environment
            }, "system_core")

            # Mantener el sistema corriendo
            logger.info("🎉 AILOOS está ejecutándose completamente integrado!")
            logger.info("💡 Presiona Ctrl+C para detener")

            # Esperar señal de shutdown
            await self.shutdown_event.wait()

        except Exception as e:
            logger.critical(f"❌ Error crítico en sistema AILOOS: {e}")
            await self.graceful_shutdown()
            sys.exit(1)


async def main():
    """Función principal."""
    system = AiloosSystem()
    await system.run()


if __name__ == "__main__":
    # Ejecutar AILOOS completamente integrado
    print("🚀 Iniciando AILOOS - Sistema Completamente Integrado")
    print("=" * 60)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 AILOOS detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)