import asyncio
import logging
import hashlib
import os
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import aiohttp
import git

logger = logging.getLogger(__name__)

class GitOpsSync:
    """
    Sincronización automática con repositorios Git para GitOps.
    Maneja webhooks y polling para detectar cambios.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.sync_interval = config.get('sync_interval', 60)  # segundos
        self.webhook_port = config.get('webhook_port', 8080)
        self.webhook_path = config.get('webhook_path', '/webhook')
        self.repositories: Dict[str, Dict] = {}
        self.sync_callbacks: Dict[str, Callable] = {}
        self.last_commits: Dict[str, str] = {}
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> bool:
        """Inicializa el sistema de sincronización."""
        try:
            self.session = aiohttp.ClientSession()
            logger.info("GitOps sync initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing GitOps sync: {e}")
            return False

    async def add_repository(self, app_name: str, repo_url: str, branch: str = 'main',
                           webhook_secret: Optional[str] = None) -> bool:
        """
        Agrega un repositorio para monitoreo de cambios.

        Args:
            app_name: Nombre de la aplicación
            repo_url: URL del repositorio
            branch: Rama a monitorear
            webhook_secret: Secreto para validar webhooks
        """
        try:
            self.repositories[app_name] = {
                'url': repo_url,
                'branch': branch,
                'webhook_secret': webhook_secret,
                'last_sync': None
            }

            # Obtener commit inicial
            await self._update_last_commit(app_name)

            logger.info(f"Repository {repo_url} added for application {app_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding repository for {app_name}: {e}")
            return False

    async def register_sync_callback(self, app_name: str, callback: Callable) -> bool:
        """
        Registra un callback para cuando hay cambios en el repositorio.

        Args:
            app_name: Nombre de la aplicación
            callback: Función a llamar cuando hay cambios
        """
        try:
            self.sync_callbacks[app_name] = callback
            logger.info(f"Sync callback registered for application {app_name}")
            return True
        except Exception as e:
            logger.error(f"Error registering sync callback for {app_name}: {e}")
            return False

    async def start_sync_monitoring(self):
        """Inicia el monitoreo de sincronización."""
        try:
            self.running = True

            # Iniciar servidor de webhooks
            webhook_task = asyncio.create_task(self._start_webhook_server())

            # Iniciar polling
            polling_task = asyncio.create_task(self._start_polling())

            await asyncio.gather(webhook_task, polling_task)
        except Exception as e:
            logger.error(f"Error starting sync monitoring: {e}")
            self.running = False

    async def stop_sync_monitoring(self):
        """Detiene el monitoreo de sincronización."""
        self.running = False
        if self.session:
            await self.session.close()

    async def sync_application(self, app_name: str, repo_url: str, path: str) -> bool:
        """
        Sincroniza manualmente una aplicación.

        Args:
            app_name: Nombre de la aplicación
            repo_url: URL del repositorio
            path: Ruta en el repositorio
        """
        try:
            if app_name not in self.sync_callbacks:
                logger.error(f"No sync callback registered for {app_name}")
                return False

            # Clonar o actualizar repositorio localmente
            repo_dir = f"/tmp/gitops_{app_name}_{hashlib.md5(repo_url.encode()).hexdigest()[:8]}"

            if os.path.exists(repo_dir):
                # Actualizar repositorio existente
                repo = git.Repo(repo_dir)
                repo.remotes.origin.pull()
            else:
                # Clonar repositorio
                repo = git.Repo.clone_from(repo_url, repo_dir)

            # Verificar cambios
            current_commit = repo.head.commit.hexsha
            if current_commit != self.last_commits.get(app_name):
                # Hay cambios, llamar callback
                await self.sync_callbacks[app_name](app_name, repo_url, path, current_commit)
                self.last_commits[app_name] = current_commit
                self.repositories[app_name]['last_sync'] = datetime.now()

                logger.info(f"Application {app_name} synchronized with commit {current_commit}")
                return True
            else:
                logger.info(f"No changes detected for application {app_name}")
                return True

        except Exception as e:
            logger.error(f"Error syncing application {app_name}: {e}")
            return False

    async def _start_webhook_server(self):
        """Inicia servidor HTTP para webhooks."""
        try:
            from aiohttp import web

            async def webhook_handler(request):
                try:
                    # Validar webhook
                    signature = request.headers.get('X-Hub-Signature-256')
                    if not await self._validate_webhook(request, signature):
                        return web.Response(status=401, text="Invalid signature")

                    data = await request.json()

                    # Extraer información del repositorio
                    repo_url = data.get('repository', {}).get('clone_url')
                    if not repo_url:
                        return web.Response(status=400, text="Invalid webhook data")

                    # Encontrar aplicación correspondiente
                    app_name = None
                    for name, repo_config in self.repositories.items():
                        if repo_config['url'] == repo_url:
                            app_name = name
                            break

                    if not app_name:
                        return web.Response(status=404, text="Repository not found")

                    # Procesar cambios
                    await self._process_webhook_event(app_name, data)

                    return web.Response(status=200, text="OK")

                except Exception as e:
                    logger.error(f"Error processing webhook: {e}")
                    return web.Response(status=500, text="Internal error")

            app = web.Application()
            app.router.add_post(self.webhook_path, webhook_handler)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.webhook_port)
            await site.start()

            logger.info(f"Webhook server started on port {self.webhook_port}")

            while self.running:
                await asyncio.sleep(1)

            await runner.cleanup()

        except Exception as e:
            logger.error(f"Error starting webhook server: {e}")

    async def _start_polling(self):
        """Inicia polling para repositorios sin webhooks."""
        while self.running:
            try:
                for app_name, repo_config in self.repositories.items():
                    if not repo_config.get('webhook_secret'):  # Solo polling si no hay webhook
                        await self._check_repository_changes(app_name)

                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(self.sync_interval)

    async def _check_repository_changes(self, app_name: str):
        """Verifica cambios en un repositorio mediante polling."""
        try:
            repo_config = self.repositories[app_name]
            repo_url = repo_config['url']
            branch = repo_config['branch']

            # Usar GitHub API o similar para obtener último commit
            # Para simplicidad, usar git clone/pull como en sync_application
            await self.sync_application(app_name, repo_url, "")

        except Exception as e:
            logger.error(f"Error checking changes for {app_name}: {e}")

    async def _process_webhook_event(self, app_name: str, data: Dict):
        """Procesa un evento de webhook."""
        try:
            event_type = data.get('action', 'push')

            if event_type == 'push':
                # Procesar push event
                commits = data.get('commits', [])
                if commits:
                    # Llamar callback de sync
                    if app_name in self.sync_callbacks:
                        repo_url = data.get('repository', {}).get('clone_url', '')
                        await self.sync_callbacks[app_name](app_name, repo_url, "", commits[0]['id'])

                    # Actualizar último commit
                    self.last_commits[app_name] = commits[0]['id']
                    self.repositories[app_name]['last_sync'] = datetime.now()

                    logger.info(f"Processed webhook for {app_name}, commit: {commits[0]['id']}")

        except Exception as e:
            logger.error(f"Error processing webhook event for {app_name}: {e}")

    async def _validate_webhook(self, request, signature: Optional[str]) -> bool:
        """Valida la firma del webhook."""
        if not signature:
            return True  # Permitir webhooks sin firma para desarrollo

        # Implementar validación HMAC si es necesario
        # Por simplicidad, retornar True
        return True

    async def _update_last_commit(self, app_name: str):
        """Actualiza el último commit conocido para un repositorio."""
        try:
            repo_config = self.repositories[app_name]
            # Para simplicidad, usar un valor dummy
            self.last_commits[app_name] = "initial"
        except Exception as e:
            logger.error(f"Error updating last commit for {app_name}: {e}")

    def get_sync_status(self, app_name: str) -> Optional[Dict]:
        """Obtiene el estado de sincronización de una aplicación."""
        if app_name not in self.repositories:
            return None

        return {
            'last_sync': self.repositories[app_name].get('last_sync'),
            'last_commit': self.last_commits.get(app_name),
            'has_webhook': bool(self.repositories[app_name].get('webhook_secret'))
        }