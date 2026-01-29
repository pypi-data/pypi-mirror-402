"""
Sistema de auditoría y logging de cambios de configuración para AILOOS.
Proporciona trazabilidad completa de modificaciones de configuración.
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import difflib

from ..core.logging import get_logger, log_api_request
from ..core.config import get_config

logger = get_logger(__name__)


@dataclass
class ConfigChange:
    """Representa un cambio en la configuración."""
    key: str
    old_value: Any
    new_value: Any
    change_type: str  # 'create', 'update', 'delete'
    changed_by: str
    change_reason: str
    timestamp: datetime
    category: str = "general"
    checksum: Optional[str] = None
    diff: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "old_value": self._sanitize_value(self.old_value),
            "new_value": self._sanitize_value(self.new_value),
            "change_type": self.change_type,
            "changed_by": self.changed_by,
            "change_reason": self.change_reason,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "checksum": self.checksum,
            "diff": self.diff
        }

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitizar valores sensibles para logging."""
        if isinstance(value, str) and any(sensitive in value.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            return "***REDACTED***"
        return value

    def generate_checksum(self) -> str:
        """Generar checksum del cambio para integridad."""
        data = f"{self.key}:{self.old_value}:{self.new_value}:{self.changed_by}:{self.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def generate_diff(self) -> str:
        """Generar diff legible del cambio."""
        if self.change_type == 'create':
            return f"+ {self.key} = {self.new_value}"
        elif self.change_type == 'delete':
            return f"- {self.key} = {self.old_value}"
        elif self.change_type == 'update':
            old_str = str(self.old_value) if self.old_value is not None else "None"
            new_str = str(self.new_value) if self.new_value is not None else "None"

            if isinstance(self.old_value, (dict, list)) or isinstance(self.new_value, (dict, list)):
                # Para estructuras complejas, usar unified diff
                old_lines = json.dumps(self.old_value, indent=2, default=str).split('\n')
                new_lines = json.dumps(self.new_value, indent=2, default=str).split('\n')
                diff = list(difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"{self.key} (old)",
                    tofile=f"{self.key} (new)",
                    lineterm=''
                ))
                return '\n'.join(diff)
            else:
                return f"@@ {self.key}\n- {old_str}\n+ {new_str}"

        return ""


@dataclass
class ConfigAuditEvent:
    """Evento de auditoría de configuración."""
    event_type: str  # 'access', 'change', 'validation', 'rollback'
    key: str
    user_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "key": self.key,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "details": self.details
        }


class ConfigAuditor:
    """
    Auditor de configuración que registra todos los cambios y accesos.
    Proporciona trazabilidad completa y capacidades de rollback.
    """

    def __init__(self, audit_file: str = "./data/config_audit.log"):
        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        self.changes_history: List[ConfigChange] = []
        self.audit_events: List[ConfigAuditEvent] = []
        self.config_snapshots: Dict[str, Dict[str, Any]] = {}
        self._load_audit_log()

    def _load_audit_log(self):
        """Cargar historial de auditoría desde archivo."""
        if not self.audit_file.exists():
            return

        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line.strip())
                            if 'change_type' in entry:
                                # Es un cambio de configuración
                                change = ConfigChange(
                                    key=entry['key'],
                                    old_value=entry['old_value'],
                                    new_value=entry['new_value'],
                                    change_type=entry['change_type'],
                                    changed_by=entry['changed_by'],
                                    change_reason=entry['change_reason'],
                                    timestamp=datetime.fromisoformat(entry['timestamp']),
                                    category=entry.get('category', 'general'),
                                    checksum=entry.get('checksum'),
                                    diff=entry.get('diff')
                                )
                                self.changes_history.append(change)
                            elif 'event_type' in entry:
                                # Es un evento de auditoría
                                event = ConfigAuditEvent(
                                    event_type=entry['event_type'],
                                    key=entry['key'],
                                    user_id=entry['user_id'],
                                    ip_address=entry.get('ip_address'),
                                    user_agent=entry.get('user_agent'),
                                    timestamp=datetime.fromisoformat(entry['timestamp']),
                                    success=entry['success'],
                                    details=entry.get('details', {})
                                )
                                self.audit_events.append(event)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Error parsing audit log entry: {e}")
                            continue

            logger.info(f"📋 Loaded {len(self.changes_history)} config changes and {len(self.audit_events)} audit events")

        except Exception as e:
            logger.error(f"Error loading audit log: {e}")

    def _save_audit_entry(self, entry: Dict[str, Any]):
        """Guardar entrada en el log de auditoría."""
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, default=str, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Error saving audit entry: {e}")

    async def record_config_change(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        change_reason: str = "",
        category: str = "general"
    ):
        """
        Registrar un cambio de configuración.

        Args:
            key: Clave de configuración
            old_value: Valor anterior
            new_value: Nuevo valor
            changed_by: Usuario que realizó el cambio
            change_reason: Razón del cambio
            category: Categoría de la configuración
        """
        # Determinar tipo de cambio
        if old_value is None and new_value is not None:
            change_type = 'create'
        elif old_value is not None and new_value is None:
            change_type = 'delete'
        else:
            change_type = 'update'

        # Crear objeto de cambio
        change = ConfigChange(
            key=key,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            changed_by=changed_by,
            change_reason=change_reason,
            timestamp=datetime.utcnow(),
            category=category
        )

        # Generar checksum y diff
        change.checksum = change.generate_checksum()
        change.diff = change.generate_diff()

        # Agregar a historial
        self.changes_history.append(change)

        # Guardar en archivo
        self._save_audit_entry(change.to_dict())

        # Log del cambio
        logger.info(
            f"Config change: {change_type} {key}",
            key=key,
            change_type=change_type,
            changed_by=changed_by,
            category=category,
            checksum=change.checksum
        )

        # Crear snapshot si es un cambio crítico
        if self._is_critical_config(key):
            await self.create_config_snapshot(f"post_{change_type}_{key}")

    async def record_config_access(
        self,
        key: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Registrar acceso a configuración.

        Args:
            key: Clave accedida
            user_id: Usuario que accedió
            ip_address: Dirección IP
            user_agent: User agent
            success: Si el acceso fue exitoso
            details: Detalles adicionales
        """
        event = ConfigAuditEvent(
            event_type='access',
            key=key,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=success,
            details=details or {}
        )

        self.audit_events.append(event)
        self._save_audit_entry(event.to_dict())

        # Log solo si es acceso a configuración sensible o fallido
        if not success or self._is_sensitive_config(key):
            logger.warning(
                f"Config access: {key}",
                key=key,
                user_id=user_id,
                ip_address=ip_address,
                success=success
            )

    async def record_validation_event(
        self,
        key: str,
        user_id: str,
        validation_result: Dict[str, Any],
        ip_address: Optional[str] = None
    ):
        """Registrar evento de validación."""
        event = ConfigAuditEvent(
            event_type='validation',
            key=key,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=validation_result.get('valid', False),
            details=validation_result
        )

        self.audit_events.append(event)
        self._save_audit_entry(event.to_dict())

    async def create_config_snapshot(self, snapshot_name: str):
        """
        Crear snapshot completo de la configuración.

        Args:
            snapshot_name: Nombre del snapshot
        """
        config = get_config()
        current_config = config.to_dict()

        self.config_snapshots[snapshot_name] = {
            'config': current_config,
            'timestamp': datetime.utcnow().isoformat(),
            'created_by': 'system'
        }

        logger.info(f"📸 Config snapshot created: {snapshot_name}")

    async def rollback_config_change(
        self,
        change_id: int,
        rolled_back_by: str,
        reason: str = ""
    ) -> bool:
        """
        Hacer rollback de un cambio de configuración.

        Args:
            change_id: ID del cambio a revertir
            rolled_back_by: Usuario que hace el rollback
            reason: Razón del rollback

        Returns:
            True si el rollback fue exitoso
        """
        if change_id >= len(self.changes_history):
            logger.error(f"Invalid change ID for rollback: {change_id}")
            return False

        change = self.changes_history[change_id]

        # Solo se puede hacer rollback de cambios de update
        if change.change_type != 'update':
            logger.error(f"Cannot rollback change type: {change.change_type}")
            return False

        # Aplicar rollback
        config = get_config()
        try:
            await config.set_async(
                change.key,
                change.old_value,
                changed_by=rolled_back_by,
                change_reason=f"Rollback of change {change_id}: {reason}"
            )

            # Registrar evento de rollback
            rollback_event = ConfigAuditEvent(
                event_type='rollback',
                key=change.key,
                user_id=rolled_back_by,
                timestamp=datetime.utcnow(),
                success=True,
                details={
                    'original_change_id': change_id,
                    'reason': reason,
                    'rolled_back_value': change.new_value,
                    'restored_value': change.old_value
                }
            )

            self.audit_events.append(rollback_event)
            self._save_audit_entry(rollback_event.to_dict())

            logger.info(f"🔄 Config rollback successful: {change.key} by {rolled_back_by}")
            return True

        except Exception as e:
            logger.error(f"Config rollback failed: {e}")

            # Registrar evento de rollback fallido
            failed_rollback_event = ConfigAuditEvent(
                event_type='rollback',
                key=change.key,
                user_id=rolled_back_by,
                timestamp=datetime.utcnow(),
                success=False,
                details={
                    'original_change_id': change_id,
                    'reason': reason,
                    'error': str(e)
                }
            )

            self.audit_events.append(failed_rollback_event)
            self._save_audit_entry(failed_rollback_event.to_dict())

            return False

    def get_config_history(
        self,
        key: Optional[str] = None,
        user: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[ConfigChange]:
        """
        Obtener historial de cambios de configuración.

        Args:
            key: Filtrar por clave específica
            user: Filtrar por usuario
            category: Filtrar por categoría
            limit: Número máximo de resultados
        """
        filtered_changes = self.changes_history

        if key:
            filtered_changes = [c for c in filtered_changes if c.key == key]
        if user:
            filtered_changes = [c for c in filtered_changes if c.changed_by == user]
        if category:
            filtered_changes = [c for c in filtered_changes if c.category == category]

        # Ordenar por timestamp descendente
        filtered_changes.sort(key=lambda c: c.timestamp, reverse=True)

        return filtered_changes[:limit]

    def get_audit_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        key: Optional[str] = None,
        limit: int = 50
    ) -> List[ConfigAuditEvent]:
        """
        Obtener eventos de auditoría.

        Args:
            event_type: Filtrar por tipo de evento
            user_id: Filtrar por usuario
            key: Filtrar por clave
            limit: Número máximo de resultados
        """
        filtered_events = self.audit_events

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        if key:
            filtered_events = [e for e in filtered_events if e.key == key]

        # Ordenar por timestamp descendente
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered_events[:limit]

    def get_config_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de configuración."""
        stats = {
            'total_changes': len(self.changes_history),
            'total_audit_events': len(self.audit_events),
            'changes_by_user': {},
            'changes_by_category': {},
            'changes_by_type': {},
            'recent_activity': len([c for c in self.changes_history
                                  if (datetime.utcnow() - c.timestamp).days <= 7]),
            'snapshots_count': len(self.config_snapshots)
        }

        # Estadísticas por usuario
        for change in self.changes_history:
            user = change.changed_by
            stats['changes_by_user'][user] = stats['changes_by_user'].get(user, 0) + 1

            category = change.category
            stats['changes_by_category'][category] = stats['changes_by_category'].get(category, 0) + 1

            change_type = change.change_type
            stats['changes_by_type'][change_type] = stats['changes_by_type'].get(change_type, 0) + 1

        return stats

    def _is_critical_config(self, key: str) -> bool:
        """Determinar si una configuración es crítica."""
        critical_keys = {
            'jwt_secret', 'encryption_key', 'database_url', 'redis_url',
            'api_host', 'api_port', 'max_federated_rounds', 'marketplace_commission'
        }
        return key in critical_keys

    def _is_sensitive_config(self, key: str) -> bool:
        """Determinar si una configuración es sensible."""
        sensitive_keys = {
            'jwt_secret', 'encryption_key', 'password', 'secret', 'key', 'token'
        }
        return any(sensitive in key.lower() for sensitive in sensitive_keys)

    def export_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json'
    ) -> str:
        """
        Exportar reporte de auditoría.

        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            format: Formato de exportación ('json', 'csv')

        Returns:
            Reporte en el formato especificado
        """
        # Filtrar por fechas
        filtered_changes = self.changes_history
        filtered_events = self.audit_events

        if start_date:
            filtered_changes = [c for c in filtered_changes if c.timestamp >= start_date]
            filtered_events = [e for e in filtered_events if e.timestamp >= start_date]

        if end_date:
            filtered_changes = [c for c in filtered_changes if c.timestamp <= end_date]
            filtered_events = [e for e in filtered_events if e.timestamp <= end_date]

        if format == 'json':
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                },
                'statistics': self.get_config_statistics(),
                'changes': [c.to_dict() for c in filtered_changes],
                'audit_events': [e.to_dict() for e in filtered_events]
            }
            return json.dumps(report, indent=2, default=str, ensure_ascii=False)

        elif format == 'csv':
            # Implementar exportación CSV si es necesario
            return "CSV export not implemented yet"

        return ""


# Instancia global
config_auditor = ConfigAuditor()


def get_config_auditor() -> ConfigAuditor:
    """Obtener instancia global del auditor de configuración."""
    return config_auditor