import asyncio
import logging
import requests
from typing import Dict, Optional
from kubernetes import client, config

logger = logging.getLogger(__name__)

class ArgoCDIntegration:
    """
    Integración completa con ArgoCD para gestión de aplicaciones GitOps.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.server_url = config.get('server_url', 'https://argocd-server.argocd.svc.cluster.local')
        self.username = config.get('username', 'admin')
        self.password = config.get('password', '')
        self.token = config.get('token', '')
        self.session = requests.Session()
        self.session.verify = config.get('verify_ssl', True)
        self.k8s_client = None

    async def initialize(self) -> bool:
        """Inicializa la conexión con ArgoCD."""
        try:
            # Configurar cliente Kubernetes
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()

            # Autenticar con ArgoCD
            if self.token:
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            elif self.username and self.password:
                await self._authenticate()
            else:
                logger.error("No authentication method provided for ArgoCD")
                return False

            # Verificar conexión
            response = self.session.get(f"{self.server_url}/api/version")
            if response.status_code == 200:
                logger.info("ArgoCD integration initialized successfully")
                return True
            else:
                logger.error(f"Failed to connect to ArgoCD: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error initializing ArgoCD integration: {e}")
            return False

    async def _authenticate(self):
        """Autentica con ArgoCD usando username/password."""
        try:
            auth_data = {
                'username': self.username,
                'password': self.password
            }
            response = self.session.post(f"{self.server_url}/api/login", json=auth_data)
            if response.status_code == 200:
                token = response.json().get('token')
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                logger.info("Authenticated with ArgoCD successfully")
            else:
                raise Exception(f"Authentication failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Error authenticating with ArgoCD: {e}")
            raise

    async def create_application(self, app_name: str, repo_url: str, path: str,
                               target_namespace: str) -> bool:
        """
        Crea una aplicación en ArgoCD.

        Args:
            app_name: Nombre de la aplicación
            repo_url: URL del repositorio Git
            path: Ruta en el repositorio
            target_namespace: Namespace de destino
        """
        try:
            app_data = {
                'metadata': {
                    'name': app_name,
                    'namespace': 'argocd'
                },
                'spec': {
                    'project': 'default',
                    'source': {
                        'repoURL': repo_url,
                        'path': path,
                        'targetRevision': 'HEAD'
                    },
                    'destination': {
                        'server': 'https://kubernetes.default.svc',
                        'namespace': target_namespace
                    },
                    'syncPolicy': {
                        'automated': {
                            'prune': True,
                            'selfHeal': True
                        }
                    }
                }
            }

            response = self.session.post(
                f"{self.server_url}/api/v1/applications",
                json=app_data
            )

            if response.status_code in [200, 201]:
                logger.info(f"Application {app_name} created in ArgoCD")
                return True
            else:
                logger.error(f"Failed to create application {app_name}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating application {app_name}: {e}")
            return False

    async def get_application_status(self, app_name: str) -> Optional[Dict]:
        """Obtiene el estado de una aplicación."""
        try:
            response = self.session.get(f"{self.server_url}/api/v1/applications/{app_name}")
            if response.status_code == 200:
                app_data = response.json()
                return {
                    'status': app_data.get('status', {}).get('sync', {}).get('status', 'unknown'),
                    'health': app_data.get('status', {}).get('health', {}).get('status', 'unknown'),
                    'last_sync': app_data.get('status', {}).get('operationState', {}).get('finishedAt'),
                    'message': app_data.get('status', {}).get('operationState', {}).get('message', '')
                }
            else:
                logger.error(f"Failed to get status for application {app_name}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting status for application {app_name}: {e}")
            return None

    async def sync_application(self, app_name: str) -> bool:
        """Sincroniza una aplicación manualmente."""
        try:
            sync_data = {
                'revision': 'HEAD',
                'prune': True,
                'dryRun': False
            }

            response = self.session.post(
                f"{self.server_url}/api/v1/applications/{app_name}/sync",
                json=sync_data
            )

            if response.status_code == 200:
                logger.info(f"Application {app_name} sync initiated")
                return True
            else:
                logger.error(f"Failed to sync application {app_name}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error syncing application {app_name}: {e}")
            return False

    async def delete_application(self, app_name: str) -> bool:
        """Elimina una aplicación de ArgoCD."""
        try:
            response = self.session.delete(f"{self.server_url}/api/v1/applications/{app_name}")
            if response.status_code == 200:
                logger.info(f"Application {app_name} deleted from ArgoCD")
                return True
            else:
                logger.error(f"Failed to delete application {app_name}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting application {app_name}: {e}")
            return False

    async def list_applications(self) -> list:
        """Lista todas las aplicaciones en ArgoCD."""
        try:
            response = self.session.get(f"{self.server_url}/api/v1/applications")
            if response.status_code == 200:
                apps = response.json().get('items', [])
                return [app['metadata']['name'] for app in apps]
            else:
                logger.error(f"Failed to list applications: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing applications: {e}")
            return []

    async def close(self):
        """Cierra la sesión."""
        self.session.close()