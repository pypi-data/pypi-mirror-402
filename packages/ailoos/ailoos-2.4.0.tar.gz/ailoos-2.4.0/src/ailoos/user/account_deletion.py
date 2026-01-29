"""
Proceso de eliminación de cuenta de usuario para AILOOS
======================================================

Este módulo proporciona funcionalidades para eliminar cuentas de usuario de manera segura
y conforme a GDPR, incluyendo período de gracia, eliminación en cascada de datos relacionados,
y notificaciones de eliminación.

Características principales:
- Período de gracia configurable antes de eliminación permanente
- Eliminación en cascada de datos relacionados (sesiones, contribuciones, tokens, etc.)
- Notificaciones automáticas al usuario durante el proceso
- Logging completo y auditoría de todas las operaciones
- Integración con el sistema de configuraciones
- Estados de eliminación para tracking del proceso
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..settings import get_settings_manager
from ..notifications.service import NotificationService
from ..coordinator.database.connection import get_db
from ..coordinator.models.base import (
    User, FederatedSession, SessionParticipant, Contribution, RewardTransaction,
    RefreshToken, RevokedToken, OAuthToken, EmailVerificationToken,
    PasswordResetToken, AccessLog, AuditLog, Node
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DeletionStatus(Enum):
    """Estados del proceso de eliminación de cuenta."""
    REQUESTED = "requested"
    GRACE_PERIOD = "grace_period"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class DeletionReason(Enum):
    """Razones para eliminación de cuenta."""
    USER_REQUEST = "user_request"
    INACTIVITY = "inactivity"
    VIOLATION = "violation"
    ADMIN_ACTION = "admin_action"
    GDPR_REQUEST = "gdpr_request"


@dataclass
class DeletionRequest:
    """Solicitud de eliminación de cuenta."""
    user_id: str
    reason: DeletionReason
    requested_by: str  # ID del usuario que solicita o 'system'/'admin'
    requested_at: datetime
    grace_period_days: int
    scheduled_deletion_at: datetime
    status: DeletionStatus
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeletionResult:
    """Resultado del proceso de eliminación."""
    success: bool
    user_id: str
    status: DeletionStatus
    deleted_at: datetime
    data_removed: Dict[str, int]  # Conteo de registros eliminados por tabla
    errors: List[str]
    audit_log_id: Optional[int] = None


class AccountDeletionConfig:
    """Configuración para el proceso de eliminación de cuentas."""

    def __init__(self, settings_manager=None):
        self.settings = settings_manager or get_settings_manager()

        # Configuraciones por defecto
        self.default_grace_period_days = self.settings.get(
            'account_deletion.grace_period_days', 30
        )
        self.max_grace_period_days = self.settings.get(
            'account_deletion.max_grace_period_days', 90
        )
        self.min_grace_period_days = self.settings.get(
            'account_deletion.min_grace_period_days', 7
        )

        # Configuraciones de eliminación
        self.enable_grace_period = self.settings.get(
            'account_deletion.enable_grace_period', True
        )
        self.enable_notifications = self.settings.get(
            'account_deletion.enable_notifications', True
        )
        self.enable_audit_logging = self.settings.get(
            'account_deletion.enable_audit_logging', True
        )

        # Configuraciones de cascada
        self.cascade_delete_sessions = self.settings.get(
            'account_deletion.cascade_delete_sessions', False
        )
        self.cascade_delete_contributions = self.settings.get(
            'account_deletion.cascade_delete_contributions', False
        )
        self.cascade_delete_rewards = self.settings.get(
            'account_deletion.cascade_delete_rewards', False
        )

        # Configuraciones de retención
        self.retain_audit_logs_days = self.settings.get(
            'account_deletion.retain_audit_logs_days', 2555  # 7 años
        )


class AccountDeletionService:
    """
    Servicio principal para gestión de eliminación de cuentas de usuario.

    Proporciona funcionalidades para:
    - Solicitar eliminación de cuenta con período de gracia
    - Procesar eliminación automática después del período de gracia
    - Cancelar solicitudes de eliminación
    - Eliminar datos relacionados de manera segura
    - Enviar notificaciones durante el proceso
    - Mantener logs de auditoría completos
    """

    def __init__(self,
                 db: Session = None,
                 notification_service: NotificationService = None,
                 config: AccountDeletionConfig = None):
        """
        Inicializa el servicio de eliminación de cuentas.

        Args:
            db: Sesión de base de datos
            notification_service: Servicio de notificaciones
            config: Configuración del servicio
        """
        self.db = db
        self.notification_service = notification_service
        self.config = config or AccountDeletionConfig()

        # Cache de solicitudes activas
        self._active_requests: Dict[str, DeletionRequest] = {}

        logger.info("Servicio de eliminación de cuentas inicializado")

    def request_account_deletion(self,
                               user_id: str,
                               reason: DeletionReason = DeletionReason.USER_REQUEST,
                               requested_by: str = None,
                               grace_period_days: int = None,
                               notes: str = None) -> DeletionRequest:
        """
        Solicita la eliminación de una cuenta de usuario.

        Args:
            user_id: ID del usuario a eliminar
            reason: Razón de la eliminación
            requested_by: ID del usuario que solicita (None para auto-solicitud)
            grace_period_days: Días de período de gracia
            notes: Notas adicionales

        Returns:
            DeletionRequest: Solicitud creada

        Raises:
            ValueError: Si la configuración es inválida
            Exception: Si hay error en la base de datos
        """
        try:
            # Validar usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")

            # Determinar quién solicita
            if not requested_by:
                requested_by = user_id  # Auto-solicitud
            elif requested_by != user_id and user.role != 'admin':
                # Solo admin puede solicitar eliminación de otros
                raise ValueError("No autorizado para solicitar eliminación de esta cuenta")

            # Validar período de gracia
            if grace_period_days is None:
                grace_period_days = self.config.default_grace_period_days
    
            if grace_period_days < self.config.min_grace_period_days or grace_period_days > self.config.max_grace_period_days:
                raise ValueError(f"Período de gracia debe estar entre {self.config.min_grace_period_days} y {self.config.max_grace_period_days} días")

            # Calcular fecha de eliminación programada
            requested_at = datetime.utcnow()
            if self.config.enable_grace_period:
                scheduled_deletion_at = requested_at + timedelta(days=grace_period_days)
                status = DeletionStatus.GRACE_PERIOD
            else:
                scheduled_deletion_at = requested_at + timedelta(minutes=5)  # Eliminación inmediata
                status = DeletionStatus.SCHEDULED

            # Crear solicitud
            request = DeletionRequest(
                user_id=user_id,
                reason=reason,
                requested_by=requested_by,
                requested_at=requested_at,
                grace_period_days=grace_period_days,
                scheduled_deletion_at=scheduled_deletion_at,
                status=status,
                notes=notes,
                metadata={
                    'user_email': user.email,
                    'user_role': user.role,
                    'request_source': 'api'
                }
            )

            # Almacenar en cache
            self._active_requests[user_id] = request

            # Log de auditoría
            self._log_deletion_action(
                user_id=user_id,
                action="deletion_requested",
                old_values=None,
                new_values={
                    "reason": reason.value,
                    "requested_by": requested_by,
                    "grace_period_days": grace_period_days,
                    "scheduled_deletion_at": scheduled_deletion_at.isoformat()
                },
                notes=notes
            )

            # Enviar notificación
            if self.config.enable_notifications and self.notification_service:
                try:
                    import asyncio
                    asyncio.create_task(self._send_deletion_notification(request, "requested"))
                except RuntimeError:
                    # No event loop running, skip notification for now
                    pass

            logger.info(f"Solicitud de eliminación creada para usuario {user_id}")
            return request

        except Exception as e:
            logger.error(f"Error creando solicitud de eliminación para {user_id}: {e}")
            raise

    def cancel_deletion_request(self, user_id: str, cancelled_by: str = None) -> bool:
        """
        Cancela una solicitud de eliminación activa.

        Args:
            user_id: ID del usuario
            cancelled_by: ID de quien cancela (None para auto-cancelación)

        Returns:
            bool: True si se canceló exitosamente
        """
        try:
            request = self._active_requests.get(user_id)
            if not request or request.status in [DeletionStatus.COMPLETED, DeletionStatus.CANCELLED]:
                return False

            # Validar permisos
            if cancelled_by and cancelled_by != user_id:
                user = self.db.query(User).filter(User.id == cancelled_by).first()
                if not user or user.role != 'admin':
                    raise ValueError("No autorizado para cancelar esta solicitud")

            # Actualizar estado
            request.status = DeletionStatus.CANCELLED
            request.metadata = request.metadata or {}
            request.metadata['cancelled_at'] = datetime.utcnow().isoformat()
            request.metadata['cancelled_by'] = cancelled_by or user_id

            # Log de auditoría
            self._log_deletion_action(
                user_id=user_id,
                action="deletion_cancelled",
                old_values={"status": request.status.value},
                new_values={"status": DeletionStatus.CANCELLED.value}
            )

            # Enviar notificación
            if self.config.enable_notifications and self.notification_service:
                try:
                    import asyncio
                    asyncio.create_task(self._send_deletion_notification(request, "cancelled"))
                except RuntimeError:
                    # No event loop running, skip notification for now
                    pass

            logger.info(f"Solicitud de eliminación cancelada para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelando solicitud de eliminación para {user_id}: {e}")
            raise

    def process_scheduled_deletions(self) -> List[DeletionResult]:
        """
        Procesa todas las eliminaciones programadas que han expirado.

        Returns:
            List[DeletionResult]: Resultados de las eliminaciones procesadas
        """
        results = []
        now = datetime.utcnow()

        try:
            # Procesar solicitudes en cache que han expirado
            expired_requests = [
                req for req in self._active_requests.values()
                if req.scheduled_deletion_at <= now and req.status == DeletionStatus.GRACE_PERIOD
            ]

            for request in expired_requests:
                try:
                    # Cambiar estado a programado
                    request.status = DeletionStatus.SCHEDULED

                    # Procesar eliminación
                    result = self._execute_account_deletion(request)
                    results.append(result)

                    # Remover de cache si completado
                    if result.success:
                        del self._active_requests[request.user_id]

                except Exception as e:
                    logger.error(f"Error procesando eliminación para {request.user_id}: {e}")
                    request.status = DeletionStatus.FAILED
                    results.append(DeletionResult(
                        success=False,
                        user_id=request.user_id,
                        status=DeletionStatus.FAILED,
                        deleted_at=now,
                        data_removed={},
                        errors=[str(e)]
                    ))

            return results

        except Exception as e:
            logger.error(f"Error procesando eliminaciones programadas: {e}")
            return results

    def force_delete_account(self,
                           user_id: str,
                           reason: DeletionReason = DeletionReason.ADMIN_ACTION,
                           requested_by: str = None) -> DeletionResult:
        """
        Fuerza la eliminación inmediata de una cuenta (para administradores).

        Args:
            user_id: ID del usuario a eliminar
            reason: Razón de la eliminación
            requested_by: ID del administrador que solicita

        Returns:
            DeletionResult: Resultado de la eliminación
        """
        try:
            # Validar permisos
            if requested_by:
                admin = self.db.query(User).filter(User.id == requested_by).first()
                if not admin or admin.role != 'admin':
                    raise ValueError("Solo administradores pueden forzar eliminación")

            # Crear solicitud de eliminación inmediata
            request = DeletionRequest(
                user_id=user_id,
                reason=reason,
                requested_by=requested_by or "admin",
                requested_at=datetime.utcnow(),
                grace_period_days=0,
                scheduled_deletion_at=datetime.utcnow(),
                status=DeletionStatus.SCHEDULED,
                metadata={'force_delete': True}
            )

            # Ejecutar eliminación
            return self._execute_account_deletion(request)

        except Exception as e:
            logger.error(f"Error en eliminación forzada para {user_id}: {e}")
            raise

    def get_deletion_status(self, user_id: str) -> Optional[DeletionRequest]:
        """
        Obtiene el estado actual de eliminación para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[DeletionRequest]: Solicitud de eliminación si existe
        """
        return self._active_requests.get(user_id)

    def _execute_account_deletion(self, request: DeletionRequest) -> DeletionResult:
        """
        Ejecuta la eliminación física de la cuenta y datos relacionados.

        Args:
            request: Solicitud de eliminación

        Returns:
            DeletionResult: Resultado de la eliminación
        """
        data_removed = {}
        errors = []

        try:
            logger.info(f"Iniciando eliminación de cuenta para usuario {request.user_id}")

            # Cambiar estado
            request.status = DeletionStatus.IN_PROGRESS

            # 1. Eliminar datos relacionados en cascada
            data_removed.update(self._delete_related_data(request.user_id))

            # 2. Eliminar la cuenta de usuario
            user_deleted = self._delete_user_account(request.user_id)
            data_removed['users'] = 1 if user_deleted else 0

            # 3. Limpiar tokens y sesiones
            tokens_removed = self._revoke_user_tokens(request.user_id)
            data_removed['tokens_revoked'] = tokens_removed

            # 4. Log final de auditoría
            audit_id = self._log_deletion_completion(request, data_removed)

            # 5. Actualizar estado
            request.status = DeletionStatus.COMPLETED

            # 6. Enviar notificación final
            if self.config.enable_notifications and self.notification_service:
                try:
                    import asyncio
                    asyncio.create_task(self._send_deletion_notification(request, "completed"))
                except RuntimeError:
                    # No event loop running, skip notification for now
                    pass

            result = DeletionResult(
                success=True,
                user_id=request.user_id,
                status=DeletionStatus.COMPLETED,
                deleted_at=datetime.utcnow(),
                data_removed=data_removed,
                errors=errors,
                audit_log_id=audit_id
            )

            logger.info(f"Eliminación completada para usuario {request.user_id}: {data_removed}")
            return result

        except Exception as e:
            error_msg = f"Error durante eliminación: {str(e)}"
            logger.error(f"Eliminación fallida para {request.user_id}: {error_msg}")
            errors.append(error_msg)

            request.status = DeletionStatus.FAILED

            return DeletionResult(
                success=False,
                user_id=request.user_id,
                status=DeletionStatus.FAILED,
                deleted_at=datetime.utcnow(),
                data_removed=data_removed,
                errors=errors
            )

    def _delete_related_data(self, user_id: str) -> Dict[str, int]:
        """
        Elimina datos relacionados del usuario de manera segura.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, int]: Conteo de registros eliminados por tabla
        """
        data_removed = {}

        try:
            # 1. Eliminar logs de acceso (excepto auditoría)
            access_logs_deleted = self.db.query(AccessLog).filter(
                AccessLog.user_id == user_id
            ).delete()
            data_removed['access_logs'] = access_logs_deleted

            # 2. Eliminar tokens OAuth
            oauth_tokens_deleted = self.db.query(OAuthToken).filter(
                OAuthToken.user_id == user_id
            ).delete()
            data_removed['oauth_tokens'] = oauth_tokens_deleted

            # 3. Eliminar tokens de verificación de email
            email_tokens_deleted = self.db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_id
            ).delete()
            data_removed['email_verification_tokens'] = email_tokens_deleted

            # 4. Eliminar tokens de reset de contraseña
            reset_tokens_deleted = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user_id
            ).delete()
            data_removed['password_reset_tokens'] = reset_tokens_deleted

            # 5. Eliminar sesiones federadas si está habilitado
            if self.config.cascade_delete_sessions:
                # Obtener sesiones donde el usuario es coordinador
                coordinator_sessions = self.db.query(FederatedSession).filter(
                    FederatedSession.coordinator_node_id == user_id
                ).all()

                sessions_deleted = 0
                for session in coordinator_sessions:
                    # Eliminar participantes
                    participants_deleted = self.db.query(SessionParticipant).filter(
                        SessionParticipant.session_id == session.id
                    ).delete()
                    data_removed['session_participants'] = data_removed.get('session_participants', 0) + participants_deleted

                    # Eliminar contribuciones
                    contributions_deleted = self.db.query(Contribution).filter(
                        Contribution.session_id == session.id
                    ).delete()
                    data_removed['contributions'] = data_removed.get('contributions', 0) + contributions_deleted

                    # Eliminar la sesión
                    self.db.delete(session)
                    sessions_deleted += 1

                data_removed['federated_sessions'] = sessions_deleted

            # 6. Eliminar contribuciones del usuario si está habilitado
            if self.config.cascade_delete_contributions:
                contributions_deleted = self.db.query(Contribution).filter(
                    Contribution.node_id == user_id
                ).delete()
                data_removed['user_contributions'] = contributions_deleted

            # 7. Eliminar transacciones de recompensa si está habilitado
            if self.config.cascade_delete_rewards:
                rewards_deleted = self.db.query(RewardTransaction).filter(
                    RewardTransaction.node_id == user_id
                ).delete()
                data_removed['reward_transactions'] = rewards_deleted

            # Commit de los cambios
            self.db.commit()

            logger.info(f"Datos relacionados eliminados para {user_id}: {data_removed}")
            return data_removed

        except Exception as e:
            logger.error(f"Error eliminando datos relacionados para {user_id}: {e}")
            self.db.rollback()
            raise

    def _delete_user_account(self, user_id: str) -> bool:
        """
        Elimina la cuenta de usuario de la base de datos.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            # Verificar que el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Usuario {user_id} no encontrado para eliminación")
                return False

            # Eliminar usuario
            self.db.delete(user)
            self.db.commit()

            logger.info(f"Cuenta de usuario {user_id} eliminada exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error eliminando cuenta de usuario {user_id}: {e}")
            self.db.rollback()
            raise

    def _revoke_user_tokens(self, user_id: str) -> int:
        """
        Revoca todos los tokens activos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            int: Número de tokens revocados
        """
        try:
            # Revocar refresh tokens
            refresh_tokens = self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            ).all()

            revoked_count = 0
            for token in refresh_tokens:
                token.is_revoked = True
                # Crear entrada en revoked tokens para JWT validation
                revoked_entry = RevokedToken(
                    token_jti=token.token_jti,
                    token_type=token.token_type,
                    revoked_by="account_deletion",
                    revocation_reason="Account deletion",
                    expires_at=token.expires_at
                )
                self.db.add(revoked_entry)
                revoked_count += 1

            self.db.commit()

            logger.info(f"Revocados {revoked_count} tokens para usuario {user_id}")
            return revoked_count

        except Exception as e:
            logger.error(f"Error revocando tokens para {user_id}: {e}")
            self.db.rollback()
            raise

    def _log_deletion_action(self,
                           user_id: str,
                           action: str,
                           old_values: Dict = None,
                           new_values: Dict = None,
                           notes: str = None) -> int:
        """
        Registra una acción de eliminación en el log de auditoría.

        Args:
            user_id: ID del usuario
            action: Acción realizada
            old_values: Valores anteriores
            new_values: Valores nuevos
            notes: Notas adicionales

        Returns:
            int: ID del log creado
        """
        if not self.config.enable_audit_logging:
            return None

        try:
            audit_log = AuditLog(
                entity_type="user",
                entity_id=user_id,
                action=action,
                user_id=user_id,
                old_values=old_values,
                new_values=new_values,
                audit_proof=json.dumps({
                    "action": action,
                    "timestamp": datetime.utcnow().isoformat(),
                    "notes": notes
                })
            )

            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)

            logger.info(f"Audit log creado: {audit_log.id} para acción '{action}' en usuario {user_id}")
            return audit_log.id

        except Exception as e:
            logger.error(f"Error creando audit log para {user_id}: {e}")
            return None

    def _log_deletion_completion(self, request: DeletionRequest, data_removed: Dict) -> int:
        """
        Registra la finalización del proceso de eliminación.

        Args:
            request: Solicitud de eliminación
            data_removed: Datos eliminados

        Returns:
            int: ID del log de auditoría
        """
        return self._log_deletion_action(
            user_id=request.user_id,
            action="account_deletion_completed",
            old_values=None,
            new_values={
                "reason": request.reason.value,
                "requested_by": request.requested_by,
                "grace_period_days": request.grace_period_days,
                "data_removed": data_removed,
                "deletion_timestamp": datetime.utcnow().isoformat()
            },
            notes=f"Account deletion completed. Data removed: {json.dumps(data_removed)}"
        )

    async def _send_deletion_notification(self, request: DeletionRequest, event: str):
        """
        Envía notificación sobre el proceso de eliminación.

        Args:
            request: Solicitud de eliminación
            event: Tipo de evento ('requested', 'cancelled', 'completed')
        """
        if not self.notification_service:
            return

        try:
            template_name = f"account_deletion_{event}"
            variables = {
                "user_id": request.user_id,
                "reason": request.reason.value,
                "grace_period_days": request.grace_period_days,
                "scheduled_deletion_at": request.scheduled_deletion_at.isoformat(),
                "requested_at": request.requested_at.isoformat()
            }

            # Intentar enviar notificación
            await self.notification_service.send_realtime_notification(
                user_id=request.user_id,
                event_type=f"account.deletion.{event}",
                title=f"Eliminación de cuenta - {event.title()}",
                message=f"Tu solicitud de eliminación de cuenta ha sido {event}.",
                data=variables
            )

            logger.info(f"Notificación de eliminación '{event}' enviada a usuario {request.user_id}")

        except Exception as e:
            logger.error(f"Error enviando notificación de eliminación: {e}")


# Modelos Pydantic para API

class AccountDeletionRequest(BaseModel):
    """Modelo para solicitud de eliminación de cuenta."""
    reason: DeletionReason = Field(..., description="Razón de la eliminación")
    grace_period_days: Optional[int] = Field(None, description="Días de período de gracia")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")

    @validator('grace_period_days')
    def validate_grace_period(cls, v):
        if v is not None and (v < 1 or v > 365):
            raise ValueError('Período de gracia debe estar entre 1 y 365 días')
        return v


class AccountDeletionStatus(BaseModel):
    """Modelo para estado de eliminación de cuenta."""
    user_id: str
    status: DeletionStatus
    reason: DeletionReason
    requested_at: datetime
    scheduled_deletion_at: datetime
    grace_period_days: int
    can_cancel: bool

    @property
    def days_remaining(self) -> int:
        """Días restantes hasta la eliminación."""
        if self.status != DeletionStatus.GRACE_PERIOD:
            return 0
        remaining = self.scheduled_deletion_at - datetime.utcnow()
        return max(0, remaining.days)


class AccountDeletionResult(BaseModel):
    """Modelo para resultado de eliminación de cuenta."""
    success: bool
    user_id: str
    status: DeletionStatus
    deleted_at: datetime
    data_removed: Dict[str, int]
    errors: List[str]
    audit_log_id: Optional[int]


# Funciones de utilidad

def get_account_deletion_service(db: Session = None) -> AccountDeletionService:
    """
    Obtiene una instancia del servicio de eliminación de cuentas.

    Args:
        db: Sesión de base de datos (opcional)

    Returns:
        AccountDeletionService: Instancia del servicio
    """
    if db is None:
        db = next(get_db())

    # Aquí se podría inicializar el servicio de notificaciones si es necesario
    notification_service = None
    try:
        from ..notifications.service import NotificationService
        from ..settings.service import SettingsService
        settings_service = SettingsService()
        notification_service = NotificationService(settings_service)
    except ImportError:
        logger.warning("Servicio de notificaciones no disponible")

    return AccountDeletionService(
        db=db,
        notification_service=notification_service
    )


def create_default_deletion_templates():
    """
    Crea plantillas por defecto para notificaciones de eliminación de cuenta.
    Esta función debería ser llamada durante la inicialización del sistema.
    """
    from ..notifications.templates import notification_templates

    # Plantilla: Solicitud de eliminación
    notification_templates.add_template({
        "name": "account_deletion_requested",
        "type": "both",
        "subject": "Solicitud de eliminación de cuenta procesada",
        "title": "Solicitud de eliminación de cuenta",
        "body": "Tu solicitud de eliminación de cuenta ha sido procesada. Tienes {grace_period_days} días para cancelar esta acción.",
        "html_body": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">Solicitud de eliminación de cuenta</h2>
            <p>Tu solicitud de eliminación de cuenta ha sido procesada.</p>
            <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                <p><strong>Período de gracia:</strong> {grace_period_days} días</p>
                <p><strong>Fecha programada de eliminación:</strong> {scheduled_deletion_at}</p>
                <p><strong>Razón:</strong> {reason}</p>
            </div>
            <p>Durante este período puedes cancelar la eliminación iniciando sesión en tu cuenta.</p>
            <p>Si no cancelas, tu cuenta será eliminada permanentemente junto con todos tus datos.</p>
            <a href="{cancel_url}" style="background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Cancelar eliminación</a>
        </div>
        """,
        "variables": ["grace_period_days", "scheduled_deletion_at", "reason", "cancel_url"]
    })

    # Plantilla: Eliminación cancelada
    notification_templates.add_template({
        "name": "account_deletion_cancelled",
        "type": "both",
        "subject": "Eliminación de cuenta cancelada",
        "title": "Eliminación de cuenta cancelada",
        "body": "La solicitud de eliminación de tu cuenta ha sido cancelada. Tu cuenta permanece activa.",
        "html_body": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">✅ Eliminación de cuenta cancelada</h2>
            <p>La solicitud de eliminación de tu cuenta ha sido cancelada.</p>
            <p>Tu cuenta permanece activa y todos tus datos están seguros.</p>
            <div style="background-color: #f0fdf4; border-left: 4px solid #059669; padding: 15px; margin: 20px 0;">
                <p><strong>Estado:</strong> Cuenta activa</p>
                <p><strong>Cancelada en:</strong> {cancelled_at}</p>
            </div>
            <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
        </div>
        """,
        "variables": ["cancelled_at"]
    })

    # Plantilla: Eliminación completada
    notification_templates.add_template({
        "name": "account_deletion_completed",
        "type": "email",  # Solo email ya que la cuenta ya no existe
        "subject": "Cuenta eliminada exitosamente",
        "title": "Cuenta eliminada exitosamente",
        "body": "Tu cuenta ha sido eliminada exitosamente. Todos tus datos han sido removidos permanentemente.",
        "html_body": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6b7280;">Cuenta eliminada</h2>
            <p>Tu cuenta ha sido eliminada exitosamente conforme a tu solicitud.</p>
            <div style="background-color: #f9fafb; border-left: 4px solid #6b7280; padding: 15px; margin: 20px 0;">
                <p><strong>Datos eliminados:</strong></p>
                <ul>
                    <li>Información de perfil</li>
                    <li>Historial de sesiones</li>
                    <li>Contribuciones y recompensas</li>
                    <li>Tokens de acceso</li>
                    <li>Datos de configuración</li>
                </ul>
                <p><strong>Eliminada en:</strong> {deleted_at}</p>
            </div>
            <p>Esta es una confirmación final. Tu cuenta ya no existe en nuestro sistema.</p>
            <p>Gracias por haber sido parte de AILOOS.</p>
        </div>
        """,
        "variables": ["deleted_at"]
    })

    logger.info("Plantillas de eliminación de cuenta creadas")