import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import git
import os
import shutil

logger = logging.getLogger(__name__)

class RollbackStrategy:
    """Estrategias de rollback disponibles."""
    GIT_RESET = "git_reset"
    GIT_REVERT = "git_revert"
    TAG_ROLLBACK = "tag_rollback"
    BRANCH_ROLLBACK = "branch_rollback"

class GitOpsRollback:
    """
    Rollback automático de cambios en GitOps.
    Gestiona reversiones seguras a estados anteriores.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.max_rollback_history = config.get('max_rollback_history', 10)
        self.auto_rollback_on_failure = config.get('auto_rollback_on_failure', False)
        self.rollback_timeout = config.get('rollback_timeout', 300)  # segundos
        self.backup_dir = config.get('backup_dir', '/tmp/gitops_backups')
        self.rollback_history: Dict[str, List[Dict]] = {}
        self.current_rollbacks: Dict[str, Dict] = {}

    async def initialize(self) -> bool:
        """Inicializa el sistema de rollback."""
        try:
            # Crear directorio de backups
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.info("GitOps rollback initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing GitOps rollback: {e}")
            return False

    async def rollback_application(self, app_name: str, target_version: Optional[str] = None) -> bool:
        """
        Realiza rollback de una aplicación.

        Args:
            app_name: Nombre de la aplicación
            target_version: Versión/commit/tag a la que hacer rollback (None = último estado bueno)
        """
        try:
            if app_name in self.current_rollbacks:
                logger.warning(f"Rollback already in progress for {app_name}")
                return False

            # Iniciar rollback
            rollback_id = f"{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_rollbacks[app_name] = {
                'id': rollback_id,
                'start_time': datetime.now(),
                'status': 'in_progress',
                'target_version': target_version
            }

            success = False

            try:
                # Determinar estrategia de rollback
                strategy = await self._determine_rollback_strategy(app_name, target_version)

                # Ejecutar rollback según estrategia
                if strategy == RollbackStrategy.GIT_RESET:
                    success = await self._rollback_git_reset(app_name, target_version)
                elif strategy == RollbackStrategy.GIT_REVERT:
                    success = await self._rollback_git_revert(app_name, target_version)
                elif strategy == RollbackStrategy.TAG_ROLLBACK:
                    success = await self._rollback_to_tag(app_name, target_version)
                elif strategy == RollbackStrategy.BRANCH_ROLLBACK:
                    success = await self._rollback_to_branch(app_name, target_version)

                # Registrar resultado
                await self._record_rollback_result(app_name, success, strategy, target_version)

                if success:
                    logger.info(f"Rollback successful for application {app_name}")
                else:
                    logger.error(f"Rollback failed for application {app_name}")

            except Exception as e:
                logger.error(f"Error during rollback of {app_name}: {e}")
                success = False
            finally:
                # Limpiar estado de rollback
                if app_name in self.current_rollbacks:
                    self.current_rollbacks[app_name]['status'] = 'completed' if success else 'failed'
                    self.current_rollbacks[app_name]['end_time'] = datetime.now()

                # Limpiar después de timeout
                asyncio.create_task(self._cleanup_rollback_state(app_name))

            return success

        except Exception as e:
            logger.error(f"Error initiating rollback for {app_name}: {e}")
            return False

    async def _determine_rollback_strategy(self, app_name: str, target_version: Optional[str]) -> RollbackStrategy:
        """Determina la mejor estrategia de rollback."""
        try:
            # Si no hay versión específica, usar git reset al último commit bueno
            if not target_version:
                return RollbackStrategy.GIT_RESET

            # Si es un tag, usar rollback a tag
            if target_version.startswith('v') or '/' in target_version:
                return RollbackStrategy.TAG_ROLLBACK

            # Si es un commit hash, usar git reset
            if len(target_version) == 40:  # SHA-1 hash
                return RollbackStrategy.GIT_RESET

            # Si es una rama, usar branch rollback
            return RollbackStrategy.BRANCH_ROLLBACK

        except Exception as e:
            logger.error(f"Error determining rollback strategy for {app_name}: {e}")
            return RollbackStrategy.GIT_RESET

    async def _rollback_git_reset(self, app_name: str, target_commit: Optional[str]) -> bool:
        """Rollback usando git reset."""
        try:
            # Obtener repositorio local (asumiendo que existe de sync)
            repo_dir = f"/tmp/gitops_{app_name}_*"
            import glob
            repo_dirs = glob.glob(repo_dir)
            if not repo_dirs:
                logger.error(f"No local repository found for {app_name}")
                return False

            repo_path = repo_dirs[0]
            repo = git.Repo(repo_path)

            # Crear backup antes del rollback
            await self._create_backup(app_name, repo_path)

            # Determinar commit target
            if not target_commit:
                # Ir al commit anterior
                commits = list(repo.iter_commits('HEAD', max_count=2))
                if len(commits) < 2:
                    logger.error(f"Not enough commits for rollback in {app_name}")
                    return False
                target_commit = commits[1].hexsha

            # Ejecutar reset
            repo.git.reset('--hard', target_commit)

            # Push si es necesario (para repos remotos)
            try:
                repo.git.push('origin', repo.active_branch.name, force=True)
            except git.GitCommandError:
                logger.warning(f"Could not push reset for {app_name}, manual intervention may be needed")

            logger.info(f"Git reset rollback completed for {app_name} to {target_commit}")
            return True

        except Exception as e:
            logger.error(f"Error in git reset rollback for {app_name}: {e}")
            return False

    async def _rollback_git_revert(self, app_name: str, target_commit: str) -> bool:
        """Rollback usando git revert (más seguro que reset)."""
        try:
            repo_dir = f"/tmp/gitops_{app_name}_*"
            import glob
            repo_dirs = glob.glob(repo_dir)
            if not repo_dirs:
                return False

            repo_path = repo_dirs[0]
            repo = git.Repo(repo_path)

            # Crear backup
            await self._create_backup(app_name, repo_path)

            # Obtener commits desde target hasta HEAD
            commits_to_revert = []
            for commit in repo.iter_commits(f"{target_commit}..HEAD"):
                commits_to_revert.append(commit.hexsha)

            # Revertir commits en orden inverso
            for commit_hash in reversed(commits_to_revert):
                repo.git.revert(commit_hash, no_edit=True)

            # Push changes
            repo.git.push('origin', repo.active_branch.name)

            logger.info(f"Git revert rollback completed for {app_name}")
            return True

        except Exception as e:
            logger.error(f"Error in git revert rollback for {app_name}: {e}")
            return False

    async def _rollback_to_tag(self, app_name: str, tag: str) -> bool:
        """Rollback a un tag específico."""
        try:
            repo_dir = f"/tmp/gitops_{app_name}_*"
            import glob
            repo_dirs = glob.glob(repo_dir)
            if not repo_dirs:
                return False

            repo_path = repo_dirs[0]
            repo = git.Repo(repo_path)

            # Crear backup
            await self._create_backup(app_name, repo_path)

            # Checkout al tag
            repo.git.checkout(tag)

            # Push si es necesario
            try:
                repo.git.push('origin', tag, force=True)
            except git.GitCommandError:
                logger.warning(f"Could not push tag checkout for {app_name}")

            logger.info(f"Tag rollback completed for {app_name} to {tag}")
            return True

        except Exception as e:
            logger.error(f"Error in tag rollback for {app_name}: {e}")
            return False

    async def _rollback_to_branch(self, app_name: str, branch: str) -> bool:
        """Rollback a una rama específica."""
        try:
            repo_dir = f"/tmp/gitops_{app_name}_*"
            import glob
            repo_dirs = glob.glob(repo_dir)
            if not repo_dirs:
                return False

            repo_path = repo_dirs[0]
            repo = git.Repo(repo_path)

            # Crear backup
            await self._create_backup(app_name, repo_path)

            # Checkout a la rama
            repo.git.checkout(branch)

            # Pull latest changes
            repo.git.pull('origin', branch)

            logger.info(f"Branch rollback completed for {app_name} to {branch}")
            return True

        except Exception as e:
            logger.error(f"Error in branch rollback for {app_name}: {e}")
            return False

    async def _create_backup(self, app_name: str, repo_path: str):
        """Crea un backup del repositorio antes del rollback."""
        try:
            backup_name = f"{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Copiar directorio
            shutil.copytree(repo_path, backup_path)

            logger.info(f"Backup created for {app_name} at {backup_path}")

            # Limpiar backups antiguos
            await self._cleanup_old_backups(app_name)

        except Exception as e:
            logger.error(f"Error creating backup for {app_name}: {e}")

    async def _cleanup_old_backups(self, app_name: str):
        """Limpia backups antiguos."""
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith(app_name)]
            if len(backups) > self.max_rollback_history:
                # Ordenar por fecha (más antiguos primero)
                backups.sort()
                to_remove = backups[:-self.max_rollback_history]

                for backup in to_remove:
                    backup_path = os.path.join(self.backup_dir, backup)
                    shutil.rmtree(backup_path)
                    logger.info(f"Removed old backup: {backup}")

        except Exception as e:
            logger.error(f"Error cleaning up old backups for {app_name}: {e}")

    async def _record_rollback_result(self, app_name: str, success: bool,
                                    strategy: RollbackStrategy, target_version: Optional[str]):
        """Registra el resultado del rollback en el historial."""
        try:
            if app_name not in self.rollback_history:
                self.rollback_history[app_name] = []

            rollback_record = {
                'timestamp': datetime.now(),
                'success': success,
                'strategy': strategy.value,
                'target_version': target_version,
                'rollback_id': self.current_rollbacks.get(app_name, {}).get('id')
            }

            self.rollback_history[app_name].append(rollback_record)

            # Mantener solo el historial reciente
            if len(self.rollback_history[app_name]) > self.max_rollback_history:
                self.rollback_history[app_name] = self.rollback_history[app_name][-self.max_rollback_history:]

        except Exception as e:
            logger.error(f"Error recording rollback result for {app_name}: {e}")

    async def _cleanup_rollback_state(self, app_name: str):
        """Limpia el estado de rollback después del timeout."""
        try:
            await asyncio.sleep(self.rollback_timeout)
            if app_name in self.current_rollbacks:
                del self.current_rollbacks[app_name]
                logger.info(f"Cleaned up rollback state for {app_name}")
        except Exception as e:
            logger.error(f"Error cleaning up rollback state for {app_name}: {e}")

    def get_rollback_history(self, app_name: str) -> List[Dict]:
        """Obtiene el historial de rollbacks de una aplicación."""
        return self.rollback_history.get(app_name, [])

    def get_current_rollbacks(self) -> Dict[str, Dict]:
        """Obtiene los rollbacks actualmente en progreso."""
        return self.current_rollbacks.copy()

    async def cancel_rollback(self, app_name: str) -> bool:
        """Cancela un rollback en progreso."""
        try:
            if app_name not in self.current_rollbacks:
                return False

            self.current_rollbacks[app_name]['status'] = 'cancelled'
            logger.info(f"Rollback cancelled for {app_name}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling rollback for {app_name}: {e}")
            return False

    def can_rollback(self, app_name: str) -> bool:
        """Verifica si es posible hacer rollback de una aplicación."""
        # Verificar que no haya rollback en progreso
        if app_name in self.current_rollbacks:
            return False

        # Verificar que haya historial suficiente
        history = self.rollback_history.get(app_name, [])
        return len(history) > 0