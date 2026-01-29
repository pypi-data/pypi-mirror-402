"""
Sistema de rotación automática de secrets para AILOOS
Implementa políticas de rotación basadas en tiempo y eventos.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .gcp_secret_manager import GCPSecretManager

logger = logging.getLogger(__name__)


class RotationTrigger(Enum):
    """Triggers para rotación de secrets."""
    TIME_BASED = "time_based"          # Rotación por tiempo
    USAGE_BASED = "usage_based"        # Rotación por uso
    COMPROMISE_DETECTED = "compromise" # Compromiso detectado
    MANUAL = "manual"                  # Rotación manual


class RotationPolicy(Enum):
    """Políticas de rotación."""
    DAILY = "daily"                    # Rotación diaria
    WEEKLY = "weekly"                  # Rotación semanal
    MONTHLY = "monthly"                # Rotación mensual
    ON_USE = "on_use"                  # Al usar
    NEVER = "never"                    # Nunca rotar


@dataclass
class SecretRotationConfig:
    """Configuración de rotación para un secret."""
    secret_id: str
    policy: RotationPolicy
    last_rotation: Optional[datetime] = None
    rotation_count: int = 0
    enabled: bool = True
    custom_trigger: Optional[Callable] = None


class SecretRotationManager:
    """
    Gestor de rotación automática de secrets.

    Características:
    - Rotación automática basada en políticas
    - Triggers personalizables
    - Historial de rotaciones
    - Notificaciones de rotación
    """

    def __init__(self, gcp_secret_manager: GCPSecretManager):
        self.gcp_manager = gcp_secret_manager
        self.rotation_configs: Dict[str, SecretRotationConfig] = {}
        self.rotation_history: List[Dict[str, Any]] = []
        self._setup_default_policies()

    def _setup_default_policies(self):
        """Configurar políticas de rotación por defecto."""
        # Políticas críticas - rotación frecuente
        critical_secrets = [
            "auth_secret", "database_url", "ai_gateway_api_key",
            "auth_google_secret", "auth_github_secret"
        ]

        for secret in critical_secrets:
            self.add_rotation_policy(
                secret_id=f"ailoos-production-{secret}",
                policy=RotationPolicy.MONTHLY
            )

        # Políticas moderadas
        moderate_secrets = [
            "blob_read_write_token", "langfuse_secret_key",
            "cron_secret", "redis_url"
        ]

        for secret in moderate_secrets:
            self.add_rotation_policy(
                secret_id=f"ailoos-production-{secret}",
                policy=RotationPolicy.WEEKLY
            )

        # Políticas opcionales - rotación menos frecuente
        optional_secrets = [
            "e2b_api_key", "openai_api_key", "tavily_api_key",
            "exa_api_key", "firecrawl_api_key"
        ]

        for secret in optional_secrets:
            self.add_rotation_policy(
                secret_id=f"ailoos-production-{secret}",
                policy=RotationPolicy.DAILY
            )

    def add_rotation_policy(
        self,
        secret_id: str,
        policy: RotationPolicy,
        custom_trigger: Optional[Callable] = None
    ):
        """Añadir política de rotación para un secret."""
        config = SecretRotationConfig(
            secret_id=secret_id,
            policy=policy,
            custom_trigger=custom_trigger
        )

        self.rotation_configs[secret_id] = config
        logger.info(f"✅ Política de rotación añadida: {secret_id} → {policy.value}")

    async def check_and_rotate_secrets(self) -> Dict[str, Any]:
        """
        Verificar y rotar secrets según políticas.

        Returns:
            Resultados de la verificación de rotación
        """
        rotated = []
        skipped = []
        errors = []

        for secret_id, config in self.rotation_configs.items():
            if not config.enabled:
                continue

            try:
                should_rotate = await self._should_rotate_secret(config)

                if should_rotate:
                    success = await self._rotate_secret(secret_id)
                    if success:
                        rotated.append(secret_id)
                        config.last_rotation = datetime.now()
                        config.rotation_count += 1

                        # Registrar en historial
                        self.rotation_history.append({
                            "secret_id": secret_id,
                            "timestamp": datetime.now(),
                            "trigger": "automatic",
                            "policy": config.policy.value
                        })
                    else:
                        errors.append(f"Error rotando {secret_id}")
                else:
                    skipped.append(secret_id)

            except Exception as e:
                error_msg = f"Error procesando {secret_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")

        return {
            "rotated_count": len(rotated),
            "skipped_count": len(skipped),
            "errors_count": len(errors),
            "rotated_secrets": rotated,
            "skipped_secrets": skipped,
            "errors": errors
        }

    async def _should_rotate_secret(self, config: SecretRotationConfig) -> bool:
        """Determinar si un secret debe rotarse."""
        if config.custom_trigger:
            return await config.custom_trigger()

        now = datetime.now()

        if config.policy == RotationPolicy.NEVER:
            return False

        if config.policy == RotationPolicy.ON_USE:
            # Para ON_USE, rotar después de cierto número de usos
            # Esto requeriría tracking de uso, por ahora usar weekly
            return self._check_time_based_rotation(config, timedelta(days=7))

        # Time-based rotation
        if config.policy == RotationPolicy.DAILY:
            return self._check_time_based_rotation(config, timedelta(days=1))
        elif config.policy == RotationPolicy.WEEKLY:
            return self._check_time_based_rotation(config, timedelta(weeks=1))
        elif config.policy == RotationPolicy.MONTHLY:
            return self._check_time_based_rotation(config, timedelta(days=30))

        return False

    def _check_time_based_rotation(self, config: SecretRotationConfig, interval: timedelta) -> bool:
        """Verificar si ha pasado el intervalo de rotación."""
        if not config.last_rotation:
            return True  # Primera rotación

        now = datetime.now()
        time_since_rotation = now - config.last_rotation

        return time_since_rotation >= interval

    async def _rotate_secret(self, secret_id: str) -> bool:
        """Rotar un secret específico."""
        try:
            # Generar nuevo valor basado en el tipo de secret
            new_value = self._generate_new_secret_value(secret_id)

            # Rotar en GCP
            success = await self.gcp_manager.rotate_secret(secret_id, new_value)

            if success:
                logger.info(f"🔄 Secret rotado exitosamente: {secret_id}")
                # Aquí se podría enviar notificación
                # await self._notify_rotation(secret_id)
            else:
                logger.error(f"❌ Error rotando secret: {secret_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error en rotación de {secret_id}: {e}")
            return False

    def _generate_new_secret_value(self, secret_id: str) -> str:
        """Generar nuevo valor para un secret."""
        import secrets
        import string

        # Determinar tipo de secret por nombre
        if "auth_secret" in secret_id or "cron_secret" in secret_id:
            # Secrets de 32 bytes en base64
            return secrets.token_urlsafe(32)

        elif "api_key" in secret_id or "secret" in secret_id:
            # API keys - 64 caracteres alfanuméricos
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(64))

        elif "token" in secret_id:
            # Tokens - 128 caracteres
            return secrets.token_hex(64)

        elif "password" in secret_id:
            # Passwords - complejas
            return self._generate_secure_password()

        else:
            # Default: token URL-safe
            return secrets.token_urlsafe(32)

    def _generate_secure_password(self) -> str:
        """Generar password segura."""
        import secrets
        import string

        # Al menos 16 caracteres con mayúsculas, minúsculas, números y símbolos
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*"

        # Garantizar al menos uno de cada tipo
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]

        # Rellenar hasta 16 caracteres
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(secrets.choice(all_chars) for _ in range(12))

        # Mezclar
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    async def force_rotate_secret(self, secret_id: str) -> bool:
        """Forzar rotación manual de un secret."""
        if secret_id not in self.rotation_configs:
            logger.warning(f"⚠️ Secret no encontrado en configuración: {secret_id}")
            return False

        success = await self._rotate_secret(secret_id)
        if success:
            config = self.rotation_configs[secret_id]
            config.last_rotation = datetime.now()
            config.rotation_count += 1

            self.rotation_history.append({
                "secret_id": secret_id,
                "timestamp": datetime.now(),
                "trigger": "manual",
                "policy": config.policy.value
            })

        return success

    def get_rotation_status(self) -> Dict[str, Any]:
        """Obtener estado de rotaciones."""
        status = {}

        for secret_id, config in self.rotation_configs.items():
            next_rotation = None
            if config.last_rotation:
                if config.policy == RotationPolicy.DAILY:
                    next_rotation = config.last_rotation + timedelta(days=1)
                elif config.policy == RotationPolicy.WEEKLY:
                    next_rotation = config.last_rotation + timedelta(weeks=1)
                elif config.policy == RotationPolicy.MONTHLY:
                    next_rotation = config.last_rotation + timedelta(days=30)

            status[secret_id] = {
                "policy": config.policy.value,
                "last_rotation": config.last_rotation.isoformat() if config.last_rotation else None,
                "next_rotation": next_rotation.isoformat() if next_rotation else None,
                "rotation_count": config.rotation_count,
                "enabled": config.enabled
            }

        return status

    def get_rotation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de rotaciones."""
        return self.rotation_history[-limit:] if limit > 0 else self.rotation_history


# Función de conveniencia para rotación automática
async def setup_secret_rotation(project_id: str) -> SecretRotationManager:
    """
    Configurar sistema de rotación automática de secrets.

    Args:
        project_id: ID del proyecto GCP

    Returns:
        Gestor de rotación configurado
    """
    from .gcp_secret_manager import GCPSecretManager

    gcp_manager = GCPSecretManager(project_id)
    rotation_manager = SecretRotationManager(gcp_manager)

    logger.info("✅ Sistema de rotación automática de secrets configurado")

    return rotation_manager