import asyncio
import logging
from typing import Dict, List, Optional
from .argocd_integration import ArgoCDIntegration
from .flux_integration import FluxIntegration
from .gitops_sync import GitOpsSync
from .gitops_monitoring import GitOpsMonitoring
from .gitops_rollback import GitOpsRollback

logger = logging.getLogger(__name__)

class GitOpsManager:
    """
    Gestor principal de GitOps para coordinar todas las operaciones
    de despliegue continuo y sincronización con repositorios Git.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.argocd = ArgoCDIntegration(config.get('argocd', {}))
        self.flux = FluxIntegration(config.get('flux', {}))
        self.sync = GitOpsSync(config.get('sync', {}))
        self.monitoring = GitOpsMonitoring(config.get('monitoring', {}))
        self.rollback = GitOpsRollback(config.get('rollback', {}))
        self.applications: Dict[str, Dict] = {}

    async def initialize(self) -> bool:
        """Inicializa todas las integraciones de GitOps."""
        try:
            # Inicializar ArgoCD
            if not await self.argocd.initialize():
                logger.error("Failed to initialize ArgoCD integration")
                return False

            # Inicializar Flux
            if not await self.flux.initialize():
                logger.error("Failed to initialize Flux integration")
                return False

            # Inicializar sincronización
            if not await self.sync.initialize():
                logger.error("Failed to initialize GitOps sync")
                return False

            # Inicializar monitoreo
            if not await self.monitoring.initialize():
                logger.error("Failed to initialize GitOps monitoring")
                return False

            # Inicializar rollback
            if not await self.rollback.initialize():
                logger.error("Failed to initialize GitOps rollback")
                return False

            logger.info("GitOps Manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing GitOps Manager: {e}")
            return False

    async def deploy_application(self, app_name: str, repo_url: str, path: str,
                               target_namespace: str, tool: str = 'argocd') -> bool:
        """
        Despliega una aplicación usando GitOps.

        Args:
            app_name: Nombre de la aplicación
            repo_url: URL del repositorio Git
            path: Ruta en el repositorio
            target_namespace: Namespace de destino
            tool: Herramienta a usar ('argocd' o 'flux')
        """
        try:
            self.applications[app_name] = {
                'repo_url': repo_url,
                'path': path,
                'namespace': target_namespace,
                'tool': tool,
                'status': 'deploying'
            }

            if tool == 'argocd':
                success = await self.argocd.create_application(
                    app_name, repo_url, path, target_namespace
                )
            elif tool == 'flux':
                success = await self.flux.create_application(
                    app_name, repo_url, path, target_namespace
                )
            else:
                logger.error(f"Unsupported GitOps tool: {tool}")
                return False

            if success:
                self.applications[app_name]['status'] = 'deployed'
                # Iniciar monitoreo
                await self.monitoring.start_monitoring(app_name)
                logger.info(f"Application {app_name} deployed successfully")
            else:
                self.applications[app_name]['status'] = 'failed'
                logger.error(f"Failed to deploy application {app_name}")

            return success
        except Exception as e:
            logger.error(f"Error deploying application {app_name}: {e}")
            if app_name in self.applications:
                self.applications[app_name]['status'] = 'error'
            return False

    async def sync_application(self, app_name: str) -> bool:
        """Sincroniza una aplicación con el repositorio."""
        try:
            if app_name not in self.applications:
                logger.error(f"Application {app_name} not found")
                return False

            app_config = self.applications[app_name]
            success = await self.sync.sync_application(
                app_name, app_config['repo_url'], app_config['path']
            )

            if success:
                logger.info(f"Application {app_name} synchronized successfully")
            else:
                logger.error(f"Failed to synchronize application {app_name}")

            return success
        except Exception as e:
            logger.error(f"Error syncing application {app_name}: {e}")
            return False

    async def rollback_application(self, app_name: str, version: Optional[str] = None) -> bool:
        """Hace rollback de una aplicación a una versión anterior."""
        try:
            if app_name not in self.applications:
                logger.error(f"Application {app_name} not found")
                return False

            success = await self.rollback.rollback_application(app_name, version)

            if success:
                logger.info(f"Application {app_name} rolled back successfully")
            else:
                logger.error(f"Failed to rollback application {app_name}")

            return success
        except Exception as e:
            logger.error(f"Error rolling back application {app_name}: {e}")
            return False

    async def get_application_status(self, app_name: str) -> Optional[Dict]:
        """Obtiene el estado de una aplicación."""
        try:
            if app_name not in self.applications:
                return None

            # Obtener estado de la herramienta correspondiente
            app_config = self.applications[app_name]
            if app_config['tool'] == 'argocd':
                status = await self.argocd.get_application_status(app_name)
            elif app_config['tool'] == 'flux':
                status = await self.flux.get_application_status(app_name)
            else:
                status = None

            if status:
                self.applications[app_name]['status'] = status.get('status', 'unknown')
                return {
                    **self.applications[app_name],
                    **status
                }
            return self.applications[app_name]
        except Exception as e:
            logger.error(f"Error getting status for application {app_name}: {e}")
            return None

    async def list_applications(self) -> List[Dict]:
        """Lista todas las aplicaciones gestionadas."""
        return list(self.applications.values())

    async def shutdown(self):
        """Cierra todas las integraciones."""
        try:
            await self.monitoring.stop_monitoring()
            await self.argocd.close()
            await self.flux.close()
            logger.info("GitOps Manager shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down GitOps Manager: {e}")