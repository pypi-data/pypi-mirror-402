"""
Version History Tracker - Historial completo de versiones con auditoría
Sistema de trazabilidad y auditoría para versiones federadas.
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict

from ..core.logging import get_logger
from .federated_version_manager import FederatedVersionManager, ModelVersion, VersionStatus
from .version_validator import VersionValidator, ValidationResult
from .ipfs_version_distributor import IPFSVersionDistributor, DistributionTask
from .rollback_coordinator import RollbackCoordinator, RollbackExecution
from .version_conflict_resolver import VersionConflictResolver, VersionConflict

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Tipos de eventos de auditoría."""
    VERSION_CREATED = "version_created"
    VERSION_VALIDATED = "version_validated"
    VERSION_ACTIVATED = "version_activated"
    VERSION_DEPRECATED = "version_deprecated"
    VERSION_DISTRIBUTED = "version_distributed"
    VALIDATION_PERFORMED = "validation_performed"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    ROLLBACK_INITIATED = "rollback_initiated"
    ROLLBACK_COMPLETED = "rollback_completed"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"


class ComplianceStatus(Enum):
    """Estados de compliance."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    EXEMPTED = "exempted"


@dataclass
class AuditEvent:
    """Evento de auditoría."""
    event_id: str
    event_type: AuditEventType
    timestamp: int
    actor: str  # Nodo o sistema que realizó la acción
    target: str  # Versión, conflicto, etc. afectado
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    risk_level: str = "low"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'actor': self.actor,
            'target': self.target,
            'action': self.action,
            'details': self.details,
            'evidence': self.evidence,
            'compliance_status': self.compliance_status.value,
            'risk_level': self.risk_level
        }


@dataclass
class VersionLineage:
    """Linaje de una versión (historial de evolución)."""
    version_id: str
    parent_versions: List[str] = field(default_factory=list)
    child_versions: List[str] = field(default_factory=list)
    branch_name: str = "main"
    created_at: int = field(default_factory=lambda: int(time.time()))
    merged_at: Optional[int] = None
    merge_commit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'version_id': self.version_id,
            'parent_versions': self.parent_versions,
            'child_versions': self.child_versions,
            'branch_name': self.branch_name,
            'created_at': self.created_at,
            'merged_at': self.merged_at,
            'merge_commit': self.merge_commit
        }


@dataclass
class ComplianceRecord:
    """Registro de compliance."""
    record_id: str
    version_id: str
    regulation: str  # GDPR, HIPAA, etc.
    requirement: str
    status: ComplianceStatus
    assessment_date: int
    assessor: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    expiry_date: Optional[int] = None
    remediation_plan: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'record_id': self.record_id,
            'version_id': self.version_id,
            'regulation': self.regulation,
            'requirement': self.requirement,
            'status': self.status.value,
            'assessment_date': self.assessment_date,
            'assessor': self.assessor,
            'evidence': self.evidence,
            'expiry_date': self.expiry_date,
            'remediation_plan': self.remediation_plan
        }


class VersionHistoryTracker:
    """
    Rastreador de historial de versiones con auditoría completa.
    Mantiene trazabilidad, compliance y análisis forense.
    """

    def __init__(self, version_manager: FederatedVersionManager,
                 validator: VersionValidator,
                 distributor: IPFSVersionDistributor,
                 rollback_coordinator: RollbackCoordinator,
                 conflict_resolver: VersionConflictResolver,
                 audit_log_path: str = "version_audit.log",
                 retention_days: int = 365):
        """
        Inicializar el rastreador de historial.

        Args:
            version_manager: Gestor de versiones
            validator: Validador de versiones
            distributor: Distribuidor de versiones
            rollback_coordinator: Coordinador de rollbacks
            conflict_resolver: Resolvedor de conflictos
            audit_log_path: Ruta del log de auditoría
            retention_days: Días de retención de logs
        """
        self.version_manager = version_manager
        self.validator = validator
        self.distributor = distributor
        self.rollback_coordinator = rollback_coordinator
        self.conflict_resolver = conflict_resolver

        self.audit_log_path = audit_log_path
        self.retention_seconds = retention_days * 24 * 3600

        # Estado del historial
        self.audit_events: List[AuditEvent] = []
        self.version_lineages: Dict[str, VersionLineage] = {}
        self.compliance_records: Dict[str, List[ComplianceRecord]] = defaultdict(list)

        # Índices para búsqueda eficiente
        self.events_by_version: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.events_by_actor: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.events_by_type: Dict[AuditEventType, List[AuditEvent]] = defaultdict(list)

        # Callbacks para integración
        self.audit_callbacks: List[Callable] = []

        # Tarea de limpieza
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Estadísticas
        self.stats = {
            'total_events': 0,
            'compliance_violations': 0,
            'security_events': 0,
            'audit_queries': 0
        }

        # Configurar callbacks de integración
        self._setup_integration_callbacks()

        logger.info(f"🚀 VersionHistoryTracker initialized with audit log at {audit_log_path}")

    def _setup_integration_callbacks(self):
        """Configurar callbacks para integrar con otros componentes."""

        # Callback para version manager
        async def version_event_handler(event_type, version_id):
            await self._record_version_event(event_type, version_id)

        self.version_manager.add_version_callback(version_event_handler)

        # Callback para rollback coordinator
        async def rollback_event_handler(event_type, rollback_id):
            await self._record_rollback_event(event_type, rollback_id)

        self.rollback_coordinator.add_rollback_callback(rollback_event_handler)

        # Callback para conflict resolver
        async def conflict_event_handler(event_type, conflict_id):
            await self._record_conflict_event(event_type, conflict_id)

        self.conflict_resolver.add_conflict_callback(conflict_event_handler)

    async def start(self):
        """Iniciar el rastreador."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar tarea de limpieza periódica
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

        # Cargar historial existente
        await self._load_audit_history()

        logger.info("✅ VersionHistoryTracker started")

    async def stop(self):
        """Detener el rastreador."""
        if not self.is_running:
            return

        self.is_running = False

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # Guardar historial final
        await self._save_audit_history()

        logger.info("🛑 VersionHistoryTracker stopped")

    async def record_event(self, event_type: AuditEventType, actor: str, target: str,
                          action: str, details: Optional[Dict[str, Any]] = None,
                          evidence: Optional[Dict[str, Any]] = None) -> str:
        """
        Registrar un evento de auditoría.

        Args:
            event_type: Tipo de evento
            actor: Actor que realizó la acción
            target: Objetivo de la acción
            action: Descripción de la acción
            details: Detalles adicionales
            evidence: Evidencia del evento

        Returns:
            ID del evento
        """
        event_id = f"audit_{int(time.time())}_{len(self.audit_events)}"

        # Evaluar compliance y riesgo
        compliance_status, risk_level = self._assess_event_compliance(event_type, details or {})

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=int(time.time()),
            actor=actor,
            target=target,
            action=action,
            details=details or {},
            evidence=evidence or {},
            compliance_status=compliance_status,
            risk_level=risk_level
        )

        # Agregar a colecciones
        self.audit_events.append(event)
        self.events_by_version[target].append(event)
        self.events_by_actor[actor].append(event)
        self.events_by_type[event_type].append(event)

        self.stats['total_events'] += 1

        # Actualizar estadísticas específicas
        if compliance_status == ComplianceStatus.NON_COMPLIANT:
            self.stats['compliance_violations'] += 1
        if event_type == AuditEventType.SECURITY_EVENT:
            self.stats['security_events'] += 1

        # Notificar callbacks
        await self._notify_audit_event(event)

        # Log del evento
        logger.info(f"📝 Audit event: {event_type.value} by {actor} on {target}")

        # Persistir inmediatamente eventos críticos
        if risk_level in ['high', 'critical']:
            await self._save_audit_history()

        return event_id

    def _assess_event_compliance(self, event_type: AuditEventType, details: Dict[str, Any]) -> Tuple[ComplianceStatus, str]:
        """Evaluar compliance y riesgo de un evento."""
        # Lógica básica de evaluación
        if event_type == AuditEventType.SECURITY_EVENT:
            return ComplianceStatus.NON_COMPLIANT, "critical"
        elif event_type in [AuditEventType.VERSION_DEPRECATED, AuditEventType.ROLLBACK_INITIATED]:
            return ComplianceStatus.UNDER_REVIEW, "high"
        elif event_type == AuditEventType.CONFLICT_DETECTED:
            return ComplianceStatus.UNDER_REVIEW, "medium"
        else:
            return ComplianceStatus.COMPLIANT, "low"

    async def _record_version_event(self, event_type: str, version_id: str):
        """Registrar evento relacionado con versiones."""
        event_map = {
            'version_registered': AuditEventType.VERSION_CREATED,
            'version_validated': AuditEventType.VERSION_VALIDATED,
            'version_activated': AuditEventType.VERSION_ACTIVATED,
            'version_deprecated': AuditEventType.VERSION_DEPRECATED,
            'version_force_activated': AuditEventType.VERSION_ACTIVATED
        }

        if event_type in event_map:
            await self.record_event(
                event_type=event_map[event_type],
                actor="system",
                target=version_id,
                action=f"Version {event_type}",
                details={'version_id': version_id}
            )

    async def _record_rollback_event(self, event_type: str, rollback_id: str):
        """Registrar evento de rollback."""
        event_map = {
            'rollback_triggered': AuditEventType.ROLLBACK_INITIATED,
            'rollback_completed': AuditEventType.ROLLBACK_COMPLETED
        }

        if event_type in event_map:
            await self.record_event(
                event_type=event_map[event_type],
                actor="rollback_coordinator",
                target=rollback_id,
                action=f"Rollback {event_type}",
                details={'rollback_id': rollback_id}
            )

    async def _record_conflict_event(self, event_type: str, conflict_id: str):
        """Registrar evento de conflicto."""
        event_map = {
            'conflict_detected': AuditEventType.CONFLICT_DETECTED,
            'conflict_resolved': AuditEventType.CONFLICT_RESOLVED
        }

        if event_type in event_map:
            await self.record_event(
                event_type=event_map[event_type],
                actor="conflict_resolver",
                target=conflict_id,
                action=f"Conflict {event_type}",
                details={'conflict_id': conflict_id}
            )

    async def add_compliance_record(self, version_id: str, regulation: str, requirement: str,
                                  status: ComplianceStatus, assessor: str,
                                  evidence: Optional[Dict[str, Any]] = None) -> str:
        """
        Agregar registro de compliance.

        Args:
            version_id: ID de la versión
            regulation: Regulación (GDPR, HIPAA, etc.)
            requirement: Requisito específico
            status: Estado de compliance
            assessor: Evaluador
            evidence: Evidencia de compliance

        Returns:
            ID del registro
        """
        record_id = f"compliance_{int(time.time())}_{len(self.compliance_records[version_id])}"

        record = ComplianceRecord(
            record_id=record_id,
            version_id=version_id,
            regulation=regulation,
            requirement=requirement,
            status=status,
            assessment_date=int(time.time()),
            assessor=assessor,
            evidence=evidence or {}
        )

        self.compliance_records[version_id].append(record)

        # Registrar evento de auditoría
        await self.record_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            actor=assessor,
            target=version_id,
            action=f"Compliance assessment: {regulation} - {requirement}",
            details={'compliance_record_id': record_id, 'status': status.value},
            evidence=evidence
        )

        logger.info(f"📋 Compliance record added for {version_id}: {regulation} - {status.value}")
        return record_id

    async def create_version_lineage(self, version_id: str, parent_versions: List[str] = None,
                                   branch_name: str = "main") -> bool:
        """
        Crear linaje para una versión.

        Args:
            version_id: ID de la versión
            parent_versions: Versiones padre
            branch_name: Nombre de la rama

        Returns:
            True si se creó correctamente
        """
        if version_id in self.version_lineages:
            return False

        lineage = VersionLineage(
            version_id=version_id,
            parent_versions=parent_versions or [],
            branch_name=branch_name
        )

        self.version_lineages[version_id] = lineage

        # Actualizar linajes de padres
        for parent_id in parent_versions or []:
            if parent_id in self.version_lineages:
                self.version_lineages[parent_id].child_versions.append(version_id)

        logger.info(f"🌳 Version lineage created for {version_id} from {parent_versions}")
        return True

    async def get_version_history(self, version_id: str, include_lineage: bool = True) -> Dict[str, Any]:
        """
        Obtener historial completo de una versión.

        Args:
            version_id: ID de la versión
            include_lineage: Incluir información de linaje

        Returns:
            Diccionario con historial completo
        """
        self.stats['audit_queries'] += 1

        # Obtener eventos de la versión
        events = self.events_by_version.get(version_id, [])
        events_data = [event.to_dict() for event in sorted(events, key=lambda e: e.timestamp)]

        # Obtener registros de compliance
        compliance = [record.to_dict() for record in self.compliance_records.get(version_id, [])]

        # Obtener linaje
        lineage = None
        if include_lineage and version_id in self.version_lineages:
            lineage = self.version_lineages[version_id].to_dict()

        # Calcular métricas de la versión
        metrics = self._calculate_version_metrics(version_id, events)

        return {
            'version_id': version_id,
            'events': events_data,
            'compliance_records': compliance,
            'lineage': lineage,
            'metrics': metrics,
            'total_events': len(events_data),
            'compliance_status': self._get_overall_compliance_status(compliance)
        }

    def _calculate_version_metrics(self, version_id: str, events: List[AuditEvent]) -> Dict[str, Any]:
        """Calcular métricas de una versión."""
        metrics = {
            'creation_time': None,
            'validation_time': None,
            'activation_time': None,
            'total_lifetime': None,
            'event_count_by_type': defaultdict(int),
            'risk_events': 0,
            'compliance_violations': 0
        }

        for event in events:
            metrics['event_count_by_type'][event.event_type.value] += 1

            if event.risk_level in ['high', 'critical']:
                metrics['risk_events'] += 1

            if event.compliance_status == ComplianceStatus.NON_COMPLIANT:
                metrics['compliance_violations'] += 1

            # Tiempos importantes
            if event.event_type == AuditEventType.VERSION_CREATED:
                metrics['creation_time'] = event.timestamp
            elif event.event_type == AuditEventType.VERSION_VALIDATED:
                metrics['validation_time'] = event.timestamp
            elif event.event_type == AuditEventType.VERSION_ACTIVATED:
                metrics['activation_time'] = event.timestamp

        # Calcular tiempo total de vida
        if metrics['creation_time'] and metrics['activation_time']:
            metrics['total_lifetime'] = metrics['activation_time'] - metrics['creation_time']

        return dict(metrics)

    def _get_overall_compliance_status(self, compliance_records: List[Dict[str, Any]]) -> str:
        """Obtener estado general de compliance."""
        if not compliance_records:
            return "unknown"

        statuses = [ComplianceStatus(record['status']) for record in compliance_records]

        if any(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return "non_compliant"
        elif any(s == ComplianceStatus.UNDER_REVIEW for s in statuses):
            return "under_review"
        else:
            return "compliant"

    async def audit_query(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Realizar consulta de auditoría con filtros.

        Args:
            filters: Filtros a aplicar
            limit: Límite de resultados

        Returns:
            Lista de eventos que coinciden
        """
        self.stats['audit_queries'] += 1

        # Aplicar filtros
        matching_events = self.audit_events

        if 'event_type' in filters:
            event_types = [AuditEventType(t) for t in filters['event_type']] if isinstance(filters['event_type'], list) else [AuditEventType(filters['event_type'])]
            matching_events = [e for e in matching_events if e.event_type in event_types]

        if 'actor' in filters:
            actors = filters['actor'] if isinstance(filters['actor'], list) else [filters['actor']]
            matching_events = [e for e in matching_events if e.actor in actors]

        if 'target' in filters:
            targets = filters['target'] if isinstance(filters['target'], list) else [filters['target']]
            matching_events = [e for e in matching_events if e.target in targets]

        if 'start_time' in filters:
            matching_events = [e for e in matching_events if e.timestamp >= filters['start_time']]

        if 'end_time' in filters:
            matching_events = [e for e in matching_events if e.timestamp <= filters['end_time']]

        if 'risk_level' in filters:
            risk_levels = filters['risk_level'] if isinstance(filters['risk_level'], list) else [filters['risk_level']]
            matching_events = [e for e in matching_events if e.risk_level in risk_levels]

        # Ordenar por timestamp descendente y limitar
        sorted_events = sorted(matching_events, key=lambda e: e.timestamp, reverse=True)
        limited_events = sorted_events[:limit]

        return [event.to_dict() for event in limited_events]

    async def generate_audit_report(self, start_time: int, end_time: int,
                                  report_type: str = "summary") -> Dict[str, Any]:
        """
        Generar reporte de auditoría.

        Args:
            start_time: Timestamp de inicio
            end_time: Timestamp de fin
            report_type: Tipo de reporte

        Returns:
            Diccionario con reporte
        """
        # Obtener eventos en el período
        events = [e for e in self.audit_events if start_time <= e.timestamp <= end_time]

        if report_type == "summary":
            return self._generate_summary_report(events, start_time, end_time)
        elif report_type == "compliance":
            return self._generate_compliance_report(events, start_time, end_time)
        elif report_type == "security":
            return self._generate_security_report(events, start_time, end_time)
        else:
            return self._generate_detailed_report(events, start_time, end_time)

    def _generate_summary_report(self, events: List[AuditEvent], start_time: int, end_time: int) -> Dict[str, Any]:
        """Generar reporte resumen."""
        event_counts = defaultdict(int)
        risk_counts = defaultdict(int)
        compliance_counts = defaultdict(int)

        for event in events:
            event_counts[event.event_type.value] += 1
            risk_counts[event.risk_level] += 1
            compliance_counts[event.compliance_status.value] += 1

        return {
            'report_type': 'summary',
            'period': {'start': start_time, 'end': end_time},
            'total_events': len(events),
            'events_by_type': dict(event_counts),
            'events_by_risk': dict(risk_counts),
            'events_by_compliance': dict(compliance_counts),
            'generated_at': int(time.time())
        }

    def _generate_compliance_report(self, events: List[AuditEvent], start_time: int, end_time: int) -> Dict[str, Any]:
        """Generar reporte de compliance."""
        compliance_events = [e for e in events if e.event_type == AuditEventType.COMPLIANCE_CHECK]

        regulations = defaultdict(lambda: defaultdict(int))
        for event in compliance_events:
            reg = event.details.get('regulation', 'unknown')
            status = event.compliance_status.value
            regulations[reg][status] += 1

        return {
            'report_type': 'compliance',
            'period': {'start': start_time, 'end': end_time},
            'compliance_events': len(compliance_events),
            'regulations': dict(regulations),
            'generated_at': int(time.time())
        }

    def _generate_security_report(self, events: List[AuditEvent], start_time: int, end_time: int) -> Dict[str, Any]:
        """Generar reporte de seguridad."""
        security_events = [e for e in events if e.event_type == AuditEventType.SECURITY_EVENT or e.risk_level in ['high', 'critical']]

        return {
            'report_type': 'security',
            'period': {'start': start_time, 'end': end_time},
            'security_events': len(security_events),
            'events': [event.to_dict() for event in security_events],
            'generated_at': int(time.time())
        }

    def _generate_detailed_report(self, events: List[AuditEvent], start_time: int, end_time: int) -> Dict[str, Any]:
        """Generar reporte detallado."""
        return {
            'report_type': 'detailed',
            'period': {'start': start_time, 'end': end_time},
            'events': [event.to_dict() for event in events],
            'total_events': len(events),
            'generated_at': int(time.time())
        }

    async def _periodic_cleanup(self):
        """Limpieza periódica de logs antiguos."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Una vez por hora
                await self._cleanup_old_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")

    async def _cleanup_old_events(self):
        """Limpiar eventos antiguos."""
        cutoff_time = int(time.time()) - self.retention_seconds
        old_events = [e for e in self.audit_events if e.timestamp < cutoff_time]

        if old_events:
            # Remover de todas las colecciones
            self.audit_events = [e for e in self.audit_events if e.timestamp >= cutoff_time]

            # Limpiar índices
            for version_events in self.events_by_version.values():
                version_events[:] = [e for e in version_events if e.timestamp >= cutoff_time]

            for actor_events in self.events_by_actor.values():
                actor_events[:] = [e for e in actor_events if e.timestamp >= cutoff_time]

            for type_events in self.events_by_type.values():
                type_events[:] = [e for e in type_events if e.timestamp >= cutoff_time]

            logger.info(f"🧹 Cleaned up {len(old_events)} old audit events")

    async def _load_audit_history(self):
        """Cargar historial de auditoría desde archivo."""
        try:
            import aiofiles
            if await aiofiles.os.path.exists(self.audit_log_path):
                async with aiofiles.open(self.audit_log_path, 'r') as f:
                    data = json.loads(await f.read())

                # Reconstruir eventos
                for event_data in data.get('events', []):
                    event = AuditEvent(
                        event_id=event_data['event_id'],
                        event_type=AuditEventType(event_data['event_type']),
                        timestamp=event_data['timestamp'],
                        actor=event_data['actor'],
                        target=event_data['target'],
                        action=event_data['action'],
                        details=event_data.get('details', {}),
                        evidence=event_data.get('evidence', {}),
                        compliance_status=ComplianceStatus(event_data.get('compliance_status', 'compliant')),
                        risk_level=event_data.get('risk_level', 'low')
                    )
                    self.audit_events.append(event)

                logger.info(f"📂 Loaded {len(self.audit_events)} audit events from history")

        except Exception as e:
            logger.warning(f"Failed to load audit history: {e}")

    async def _save_audit_history(self):
        """Guardar historial de auditoría a archivo."""
        try:
            import aiofiles
            data = {
                'events': [event.to_dict() for event in self.audit_events[-1000:]],  # Últimos 1000 eventos
                'saved_at': int(time.time())
            }

            async with aiofiles.open(self.audit_log_path, 'w') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as e:
            logger.error(f"❌ Failed to save audit history: {e}")

    async def _notify_audit_event(self, event: AuditEvent):
        """Notificar evento de auditoría a callbacks."""
        for callback in self.audit_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.warning(f"Audit callback failed: {e}")

    def add_audit_callback(self, callback: Callable):
        """Agregar callback para eventos de auditoría."""
        self.audit_callbacks.append(callback)

    def get_audit_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de auditoría."""
        return {
            'total_events': self.stats['total_events'],
            'compliance_violations': self.stats['compliance_violations'],
            'security_events': self.stats['security_events'],
            'audit_queries': self.stats['audit_queries'],
            'events_by_type': {k.value: len(v) for k, v in self.events_by_type.items()},
            'active_versions_tracked': len(self.events_by_version),
            'compliance_records': sum(len(records) for records in self.compliance_records.values())
        }