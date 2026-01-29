import asyncio
import logging
import requests
from typing import Dict, Optional
from kubernetes import client, config

logger = logging.getLogger(__name__)

class FluxIntegration:
    """
    Integración con Flux CD para gestión de aplicaciones GitOps.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.namespace = config.get('namespace', 'flux-system')
        self.session = requests.Session()
        self.session.verify = config.get('verify_ssl', True)
        self.k8s_client = None

    async def initialize(self) -> bool:
        """Inicializa la conexión con Flux."""
        try:
            # Configurar cliente Kubernetes
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()
            self.custom_client = client.CustomObjectsApi()

            # Verificar que Flux esté instalado
            if not await self._check_flux_installed():
                logger.error("Flux is not installed in the cluster")
                return False

            logger.info("Flux integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Flux integration: {e}")
            return False

    async def _check_flux_installed(self) -> bool:
        """Verifica si Flux está instalado en el cluster."""
        try:
            # Verificar namespace flux-system
            self.k8s_client.read_namespace(self.namespace)
            return True
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return False
            raise

    async def create_application(self, app_name: str, repo_url: str, path: str,
                               target_namespace: str) -> bool:
        """
        Crea una aplicación usando Flux (GitRepository + Kustomization).

        Args:
            app_name: Nombre de la aplicación
            repo_url: URL del repositorio Git
            path: Ruta en el repositorio
            target_namespace: Namespace de destino
        """
        try:
            # Crear GitRepository
            repo_created = await self._create_git_repository(app_name, repo_url)
            if not repo_created:
                return False

            # Crear Kustomization
            kustomization_created = await self._create_kustomization(
                app_name, path, target_namespace
            )
            if not kustomization_created:
                # Limpiar GitRepository si falla
                await self._delete_git_repository(app_name)
                return False

            logger.info(f"Application {app_name} created in Flux")
            return True
        except Exception as e:
            logger.error(f"Error creating application {app_name}: {e}")
            return False

    async def _create_git_repository(self, name: str, url: str) -> bool:
        """Crea un GitRepository en Flux."""
        try:
            git_repo = {
                'apiVersion': 'source.toolkit.fluxcd.io/v1beta2',
                'kind': 'GitRepository',
                'metadata': {
                    'name': name,
                    'namespace': self.namespace
                },
                'spec': {
                    'interval': '1m0s',
                    'url': url,
                    'ref': {
                        'branch': 'main'
                    }
                }
            }

            self.custom_client.create_namespaced_custom_object(
                group='source.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='gitrepositories',
                body=git_repo
            )
            return True
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to create GitRepository {name}: {e}")
            return False

    async def _create_kustomization(self, name: str, path: str, target_namespace: str) -> bool:
        """Crea una Kustomization en Flux."""
        try:
            kustomization = {
                'apiVersion': 'kustomize.toolkit.fluxcd.io/v1beta2',
                'kind': 'Kustomization',
                'metadata': {
                    'name': name,
                    'namespace': self.namespace
                },
                'spec': {
                    'interval': '1m0s',
                    'path': path,
                    'prune': True,
                    'sourceRef': {
                        'kind': 'GitRepository',
                        'name': name
                    },
                    'targetNamespace': target_namespace
                }
            }

            self.custom_client.create_namespaced_custom_object(
                group='kustomize.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='kustomizations',
                body=kustomization
            )
            return True
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to create Kustomization {name}: {e}")
            return False

    async def get_application_status(self, app_name: str) -> Optional[Dict]:
        """Obtiene el estado de una aplicación en Flux."""
        try:
            # Obtener estado de Kustomization
            kustomization = self.custom_client.get_namespaced_custom_object(
                group='kustomize.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='kustomizations',
                name=app_name
            )

            status = kustomization.get('status', {})
            conditions = status.get('conditions', [])

            # Encontrar condición Ready
            ready_condition = None
            for condition in conditions:
                if condition.get('type') == 'Ready':
                    ready_condition = condition
                    break

            return {
                'status': ready_condition.get('status', 'Unknown') if ready_condition else 'Unknown',
                'message': ready_condition.get('message', '') if ready_condition else '',
                'last_sync': status.get('lastAppliedRevision', ''),
                'observed_generation': status.get('observedGeneration', 0)
            }
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.warning(f"Application {app_name} not found in Flux")
                return None
            logger.error(f"Error getting status for application {app_name}: {e}")
            return None

    async def sync_application(self, app_name: str) -> bool:
        """Sincroniza una aplicación en Flux (reconciliación manual)."""
        try:
            # Forzar reconciliación anotando la Kustomization
            patch = {
                'metadata': {
                    'annotations': {
                        'reconcile.fluxcd.io/requestedAt': str(asyncio.get_event_loop().time())
                    }
                }
            }

            self.custom_client.patch_namespaced_custom_object(
                group='kustomize.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='kustomizations',
                name=app_name,
                body=patch
            )

            logger.info(f"Application {app_name} sync initiated in Flux")
            return True
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to sync application {app_name}: {e}")
            return False

    async def delete_application(self, app_name: str) -> bool:
        """Elimina una aplicación de Flux."""
        try:
            # Eliminar Kustomization
            self.custom_client.delete_namespaced_custom_object(
                group='kustomize.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='kustomizations',
                name=app_name
            )

            # Eliminar GitRepository
            await self._delete_git_repository(app_name)

            logger.info(f"Application {app_name} deleted from Flux")
            return True
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to delete application {app_name}: {e}")
            return False

    async def _delete_git_repository(self, name: str) -> bool:
        """Elimina un GitRepository."""
        try:
            self.custom_client.delete_namespaced_custom_object(
                group='source.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='gitrepositories',
                name=name
            )
            return True
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to delete GitRepository {name}: {e}")
            return False

    async def list_applications(self) -> list:
        """Lista todas las aplicaciones en Flux."""
        try:
            kustomizations = self.custom_client.list_namespaced_custom_object(
                group='kustomize.toolkit.fluxcd.io',
                version='v1beta2',
                namespace=self.namespace,
                plural='kustomizations'
            )

            apps = kustomizations.get('items', [])
            return [app['metadata']['name'] for app in apps]
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to list applications: {e}")
            return []

    async def close(self):
        """Cierra la conexión."""
        pass  # No hay sesión HTTP para cerrar