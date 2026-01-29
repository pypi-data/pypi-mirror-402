"""
Google Cloud Secret Manager Integration for AILOOS
Gestión segura de secrets con rotación automática y políticas de acceso.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import base64

# Google Cloud imports (opcionales)
try:
    from google.cloud import secretmanager
    from google.api_core.exceptions import NotFound, PermissionDenied
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    secretmanager = None
    service_account = None

from ..core.logging import get_logger

logger = get_logger(__name__)


class GCPSecretManager:
    """
    Google Cloud Secret Manager para gestión segura de secrets en AILOOS.

    Características:
    - Migración automática de .env files
    - Rotación automática de secrets
    - Políticas de acceso least-privilege
    - Encriptación en tránsito y en reposo
    - Auditoría completa de acceso
    """

    def __init__(self, project_id: str, service_account_key: Optional[str] = None):
        """
        Inicializar GCP Secret Manager.

        Args:
            project_id: ID del proyecto GCP
            service_account_key: JSON key del service account (opcional, usa ADC si no se proporciona)
        """
        self.project_id = project_id
        self.service_account_key = service_account_key
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializar cliente de GCP Secret Manager."""
        if not GCP_AVAILABLE:
            logger.warning("⚠️ Google Cloud libraries no disponibles. Instalar con: pip install google-cloud-secret-manager")
            return

        try:
            if self.service_account_key:
                # Usar service account key proporcionada
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(self.service_account_key)
                )
                self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)
            else:
                # Usar Application Default Credentials (ADC)
                self.client = secretmanager.SecretManagerServiceClient()

            logger.info(f"✅ GCP Secret Manager inicializado para proyecto: {self.project_id}")

        except Exception as e:
            logger.error(f"❌ Error inicializando GCP Secret Manager: {e}")
            self.client = None

    async def migrate_env_file(self, env_file_path: str, env_name: str = "default") -> Dict[str, str]:
        """
        Migrar secrets desde archivo .env a GCP Secret Manager.

        Args:
            env_file_path: Ruta al archivo .env
            env_name: Nombre del entorno (default, production, staging)

        Returns:
            Dict con resultados de migración
        """
        if not self.client:
            return {"error": "GCP Secret Manager no inicializado"}

        try:
            migrated = {}
            errors = []

            # Leer archivo .env
            with open(env_file_path, 'r') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # No migrar valores vacíos o placeholders
                    if not value or value.startswith('your_') or value == '':
                        continue

                    try:
                        # Crear secret en GCP
                        secret_id = f"ailoos-{env_name}-{key.lower()}"
                        await self._create_or_update_secret(secret_id, value, key)

                        migrated[key] = secret_id
                        logger.info(f"✅ Migrado: {key} → {secret_id}")

                    except Exception as e:
                        error_msg = f"Error migrando {key}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(f"❌ {error_msg}")

            return {
                "migrated_count": len(migrated),
                "errors_count": len(errors),
                "migrated_secrets": migrated,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            return {"error": str(e)}

    async def _create_or_update_secret(self, secret_id: str, value: str, description: str):
        """Crear o actualizar secret en GCP."""
        parent = f"projects/{self.project_id}"

        try:
            # Verificar si el secret ya existe
            secret_name = f"{parent}/secrets/{secret_id}"
            self.client.get_secret(request={"name": secret_name})

            # Si existe, añadir nueva versión
            self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )
            logger.info(f"✅ Actualizada versión de secret: {secret_id}")

        except NotFound:
            # Crear nuevo secret
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                        "labels": {
                            "environment": "ailoos",
                            "managed_by": "secret_manager"
                        }
                    }
                }
            )

            # Añadir primera versión
            self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )
            logger.info(f"✅ Creado nuevo secret: {secret_id}")

    async def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Obtener valor de secret desde GCP.

        Args:
            secret_id: ID del secret
            version: Versión del secret ('latest' por defecto)

        Returns:
            Valor del secret o None si no encontrado
        """
        if not self.client:
            logger.warning("⚠️ GCP Secret Manager no disponible")
            return None

        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})

            # Decodificar payload
            payload = response.payload.data.decode("UTF-8")
            return payload

        except NotFound:
            logger.warning(f"⚠️ Secret no encontrado: {secret_id}")
            return None
        except PermissionDenied:
            logger.error(f"❌ Permiso denegado para acceder a secret: {secret_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo secret {secret_id}: {e}")
            return None

    async def rotate_secret(self, secret_id: str, new_value: str) -> bool:
        """
        Rotar secret con nuevo valor.

        Args:
            secret_id: ID del secret a rotar
            new_value: Nuevo valor del secret

        Returns:
            True si la rotación fue exitosa
        """
        if not self.client:
            return False

        try:
            await self._create_or_update_secret(secret_id, new_value, f"Rotated at {datetime.now().isoformat()}")
            logger.info(f"✅ Secret rotado: {secret_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error rotando secret {secret_id}: {e}")
            return False

    async def list_secrets(self, filter_prefix: str = "ailoos-") -> List[Dict[str, Any]]:
        """
        Listar secrets de AILOOS en GCP.

        Args:
            filter_prefix: Prefijo para filtrar secrets

        Returns:
            Lista de secrets con metadata
        """
        if not self.client:
            return []

        try:
            parent = f"projects/{self.project_id}"
            secrets = []

            # Listar todos los secrets
            for secret in self.client.list_secrets(request={"parent": parent}):
                if filter_prefix in secret.name:
                    # Obtener última versión
                    versions = list(self.client.list_secret_versions(request={"parent": secret.name}))
                    latest_version = versions[0] if versions else None

                    secrets.append({
                        "name": secret.name.split('/')[-1],
                        "create_time": secret.create_time.isoformat() if secret.create_time else None,
                        "labels": dict(secret.labels),
                        "latest_version": latest_version.name.split('/')[-1] if latest_version else None,
                        "state": secret.state.name if hasattr(secret.state, 'name') else str(secret.state)
                    })

            return secrets

        except Exception as e:
            logger.error(f"❌ Error listando secrets: {e}")
            return []

    async def setup_iam_policy(self, secret_id: str, service_accounts: List[str]) -> bool:
        """
        Configurar política IAM para acceso least-privilege.

        Args:
            secret_id: ID del secret
            service_accounts: Lista de service accounts con acceso

        Returns:
            True si la configuración fue exitosa
        """
        if not self.client:
            return False

        try:
            from google.iam.v1 import policy_pb2

            secret_name = f"projects/{self.project_id}/secrets/{secret_id}"

            # Obtener política actual
            policy = self.client.get_iam_policy(request={"resource": secret_name})

            # Limpiar bindings existentes de AILOOS
            new_bindings = []
            for binding in policy.bindings:
                if not any("ailoos" in member for member in binding.members):
                    new_bindings.append(binding)

            # Añadir nuevos bindings con least-privilege
            for service_account in service_accounts:
                new_binding = policy_pb2.Binding()
                new_binding.role = "roles/secretmanager.secretAccessor"
                new_binding.members.append(f"serviceAccount:{service_account}")
                new_bindings.append(new_binding)

            policy.bindings[:] = new_bindings

            # Actualizar política
            self.client.set_iam_policy(request={"resource": secret_name, "policy": policy})

            logger.info(f"✅ IAM policy configurada para secret: {secret_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error configurando IAM policy para {secret_id}: {e}")
            return False


class SecretManagerConfig:
    """Configuración para el sistema de gestión de secrets."""

    def __init__(self, project_id: str, environment: str = "development"):
        self.project_id = project_id
        self.environment = environment
        self.secret_manager = None

    async def initialize(self, service_account_key: Optional[str] = None) -> bool:
        """Inicializar secret manager."""
        try:
            self.secret_manager = GCPSecretManager(self.project_id, service_account_key)
            return self.secret_manager.client is not None
        except Exception as e:
            logger.error(f"❌ Error inicializando secret manager: {e}")
            return False

    async def get_secret(self, key: str) -> Optional[str]:
        """Obtener secret por clave."""
        if not self.secret_manager:
            return None

        secret_id = f"ailoos-{self.environment}-{key.lower()}"
        return await self.secret_manager.get_secret(secret_id)

    async def migrate_all_env_files(self) -> Dict[str, Any]:
        """Migrar todos los archivos .env encontrados."""
        if not self.secret_manager:
            return {"error": "Secret manager no inicializado"}

        import os
        from pathlib import Path

        results = {}

        # Buscar archivos .env
        env_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.startswith('.env') and not file.endswith('.example'):
                    env_files.append(os.path.join(root, file))

        for env_file in env_files:
            env_name = "default"
            if "production" in env_file:
                env_name = "production"
            elif "staging" in env_file:
                env_name = "staging"

            logger.info(f"🔄 Migrando {env_file} para entorno {env_name}")
            result = await self.secret_manager.migrate_env_file(env_file, env_name)
            results[env_file] = result

        return results


# Instancia global
_secret_manager: Optional[SecretManagerConfig] = None


async def get_secret_manager(project_id: str = None, environment: str = "development") -> Optional[SecretManagerConfig]:
    """Obtener instancia global del secret manager."""
    global _secret_manager

    if _secret_manager is None and project_id:
        _secret_manager = SecretManagerConfig(project_id, environment)
        await _secret_manager.initialize()

    return _secret_manager


async def migrate_all_secrets_to_gcp(project_id: str) -> Dict[str, Any]:
    """
    Función de conveniencia para migrar todos los secrets a GCP.

    Args:
        project_id: ID del proyecto GCP

    Returns:
        Resultados de la migración
    """
    logger.info("🚀 Iniciando migración completa de secrets a GCP Secret Manager...")

    config = SecretManagerConfig(project_id)
    if not await config.initialize():
        return {"error": "No se pudo inicializar GCP Secret Manager"}

    results = await config.migrate_all_env_files()

    # Resumen
    total_migrated = sum(r.get("migrated_count", 0) for r in results.values() if isinstance(r, dict))
    total_errors = sum(r.get("errors_count", 0) for r in results.values() if isinstance(r, dict))

    logger.info(f"✅ Migración completada: {total_migrated} secrets migrados, {total_errors} errores")

    return {
        "total_migrated": total_migrated,
        "total_errors": total_errors,
        "details": results
    }