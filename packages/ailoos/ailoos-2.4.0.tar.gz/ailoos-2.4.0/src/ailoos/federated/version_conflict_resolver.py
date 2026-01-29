"""
Version Conflict Resolver - Resolución de conflictos de versiones
Sistema de resolución automática y manual de conflictos en entornos federados.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.logging import get_logger
from .federated_version_manager import FederatedVersionManager, ModelVersion, ValidationStatus
from .version_validator import VersionValidator, ValidationResult, ValidationType

logger = get_logger(__name__)


class ConflictType(Enum):
    """Tipos de conflictos de versión."""
    VALIDATION_DISAGREEMENT = "validation_disagreement"
    COMPETING_VERSIONS = "competing_versions"
    FORKED_DEVELOPMENT = "forked_development"
    METADATA_INCONSISTENCY = "metadata_inconsistency"
    SECURITY_CONFLICT = "security_conflict"
    PERFORMANCE_REGRESSION = "performance_regression"


class ResolutionStrategy(Enum):
    """Estrategias de resolución."""
    AUTOMATIC_MERGE = "automatic_merge"
    PRIORITY_BASED = "priority_based"
    CONSENSUS_BASED = "consensus_based"
    MANUAL_ARBITRATION = "manual_arbitration"
    ROLLBACK_TO_STABLE = "rollback_to_stable"
    FORK_MAINTENANCE = "fork_maintenance"


class ConflictStatus(Enum):
    """Estados de conflicto."""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


@dataclass
class VersionConflict:
    """Representa un conflicto de versiones."""
    conflict_id: str
    conflict_type: ConflictType
    affected_versions: List[str]
    description: str
    detected_at: int = field(default_factory=lambda: int(time.time()))
    severity: str = "medium"  # low, medium, high, critical
    status: ConflictStatus = ConflictStatus.DETECTED
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_version: Optional[str] = None
    resolution_details: Dict[str, Any] = field(default_factory=dict)
    involved_nodes: Set[str] = field(default_factory=set)
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'conflict_id': self.conflict_id,
            'conflict_type': self.conflict_type.value,
            'affected_versions': self.affected_versions,
            'description': self.description,
            'detected_at': self.detected_at,
            'severity': self.severity,
            'status': self.status.value,
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'resolved_version': self.resolved_version,
            'resolution_details': self.resolution_details,
            'involved_nodes': list(self.involved_nodes),
            'evidence': self.evidence
        }


@dataclass
class ConflictResolution:
    """Resolución de un conflicto."""
    conflict: VersionConflict
    strategy: ResolutionStrategy
    proposed_solution: Dict[str, Any]
    confidence_score: float  # 0.0 a 1.0
    estimated_risk: str  # low, medium, high
    execution_plan: List[Dict[str, Any]]
    created_at: int = field(default_factory=lambda: int(time.time()))
    executed_at: Optional[int] = None
    success: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'conflict': self.conflict.to_dict(),
            'strategy': self.strategy.value,
            'proposed_solution': self.proposed_solution,
            'confidence_score': self.confidence_score,
            'estimated_risk': self.estimated_risk,
            'execution_plan': self.execution_plan,
            'created_at': self.created_at,
            'executed_at': self.executed_at,
            'success': self.success
        }


class VersionConflictResolver:
    """
    Resolvedor de conflictos de versiones.
    Detecta, analiza y resuelve conflictos automáticamente o con intervención manual.
    """

    def __init__(self, version_manager: FederatedVersionManager,
                 validator: VersionValidator,
                 auto_resolution_enabled: bool = True,
                 conflict_timeout_hours: int = 24):
        """
        Inicializar el resolvedor de conflictos.

        Args:
            version_manager: Gestor de versiones
            validator: Validador de versiones
            auto_resolution_enabled: Habilitar resolución automática
            conflict_timeout_hours: Timeout para resolución de conflictos
        """
        self.version_manager = version_manager
        self.validator = validator
        self.auto_resolution_enabled = auto_resolution_enabled
        self.conflict_timeout_seconds = conflict_timeout_hours * 3600

        # Estado de conflictos
        self.active_conflicts: Dict[str, VersionConflict] = {}
        self.resolved_conflicts: List[ConflictResolution] = []
        self.conflict_queue: asyncio.Queue[VersionConflict] = asyncio.Queue()

        # Configuración de estrategias
        self.resolution_strategies: Dict[ConflictType, List[ResolutionStrategy]] = {
            ConflictType.VALIDATION_DISAGREEMENT: [
                ResolutionStrategy.CONSENSUS_BASED,
                ResolutionStrategy.PRIORITY_BASED,
                ResolutionStrategy.MANUAL_ARBITRATION
            ],
            ConflictType.COMPETING_VERSIONS: [
                ResolutionStrategy.PRIORITY_BASED,
                ResolutionStrategy.AUTOMATIC_MERGE,
                ResolutionStrategy.MANUAL_ARBITRATION
            ],
            ConflictType.FORKED_DEVELOPMENT: [
                ResolutionStrategy.FORK_MAINTENANCE,
                ResolutionStrategy.MANUAL_ARBITRATION
            ],
            ConflictType.METADATA_INCONSISTENCY: [
                ResolutionStrategy.AUTOMATIC_MERGE,
                ResolutionStrategy.MANUAL_ARBITRATION
            ],
            ConflictType.SECURITY_CONFLICT: [
                ResolutionStrategy.ROLLBACK_TO_STABLE,
                ResolutionStrategy.MANUAL_ARBITRATION
            ],
            ConflictType.PERFORMANCE_REGRESSION: [
                ResolutionStrategy.ROLLBACK_TO_STABLE,
                ResolutionStrategy.PRIORITY_BASED
            ]
        }

        # Callbacks
        self.conflict_callbacks: List[Callable] = []

        # Workers
        self.resolution_workers: List[asyncio.Task] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Estadísticas
        self.stats = {
            'total_conflicts': 0,
            'resolved_conflicts': 0,
            'escalated_conflicts': 0,
            'auto_resolved_conflicts': 0
        }

        logger.info("🚀 VersionConflictResolver initialized")

    async def start(self):
        """Iniciar el resolvedor."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar workers de resolución
        self.resolution_workers = [
            asyncio.create_task(self._conflict_resolution_worker())
        ]

        # Iniciar monitoreo de conflictos
        self.monitoring_task = asyncio.create_task(self._conflict_monitoring())

        logger.info("✅ VersionConflictResolver started")

    async def stop(self):
        """Detener el resolvedor."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar tareas
        tasks_to_cancel = [self.monitoring_task] + self.resolution_workers
        for task in tasks_to_cancel:
            if task:
                task.cancel()

        # Esperar finalización
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

        logger.info("🛑 VersionConflictResolver stopped")

    async def detect_conflict(self, conflict_type: ConflictType,
                            affected_versions: List[str], description: str,
                            evidence: Optional[List[Dict[str, Any]]] = None,
                            involved_nodes: Optional[Set[str]] = None) -> str:
        """
        Detectar y reportar un conflicto.

        Args:
            conflict_type: Tipo de conflicto
            affected_versions: Versiones afectadas
            description: Descripción del conflicto
            evidence: Evidencia del conflicto
            involved_nodes: Nodos involucrados

        Returns:
            ID del conflicto
        """
        conflict_id = f"conflict_{int(time.time())}_{len(self.active_conflicts)}"

        conflict = VersionConflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            affected_versions=affected_versions,
            description=description,
            evidence=evidence or [],
            involved_nodes=involved_nodes or set()
        )

        # Determinar severidad
        conflict.severity = self._assess_conflict_severity(conflict)

        self.active_conflicts[conflict_id] = conflict
        self.stats['total_conflicts'] += 1

        # Agregar a cola de resolución
        await self.conflict_queue.put(conflict)

        # Notificar detección
        await self._notify_conflict_event('conflict_detected', conflict_id)

        logger.info(f"⚠️ Conflict detected: {conflict_type.value} affecting {len(affected_versions)} versions")
        return conflict_id

    async def _conflict_resolution_worker(self):
        """Worker que procesa conflictos."""
        while self.is_running:
            try:
                conflict = await self.conflict_queue.get()

                try:
                    await self._resolve_conflict(conflict.conflict_id)
                except Exception as e:
                    logger.error(f"❌ Conflict resolution failed for {conflict.conflict_id}: {e}")
                    conflict.status = ConflictStatus.ESCALATED
                finally:
                    self.conflict_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Conflict worker error: {e}")

    async def _resolve_conflict(self, conflict_id: str):
        """Resolver un conflicto específico."""
        conflict = self.active_conflicts.get(conflict_id)
        if not conflict:
            return

        conflict.status = ConflictStatus.ANALYZING

        logger.info(f"🔍 Analyzing conflict {conflict_id}: {conflict.conflict_type.value}")

        try:
            # Analizar conflicto
            analysis = await self._analyze_conflict(conflict)

            # Seleccionar estrategia de resolución
            strategy = self._select_resolution_strategy(conflict, analysis)

            # Crear resolución
            resolution = ConflictResolution(
                conflict=conflict,
                strategy=strategy,
                proposed_solution=analysis['proposed_solution'],
                confidence_score=analysis['confidence_score'],
                estimated_risk=analysis['estimated_risk'],
                execution_plan=analysis['execution_plan']
            )

            conflict.status = ConflictStatus.RESOLVING
            conflict.resolution_strategy = strategy

            # Ejecutar resolución automática si está habilitada
            if self.auto_resolution_enabled and resolution.confidence_score >= 0.8:
                success = await self._execute_resolution(resolution)
                resolution.success = success
                resolution.executed_at = int(time.time())

                if success:
                    conflict.status = ConflictStatus.RESOLVED
                    conflict.resolved_version = resolution.proposed_solution.get('selected_version')
                    self.stats['auto_resolved_conflicts'] += 1
                    await self._notify_conflict_event('conflict_auto_resolved', conflict_id)
                else:
                    conflict.status = ConflictStatus.ESCALATED
                    await self._notify_conflict_event('conflict_escalated', conflict_id)
            else:
                # Requerir arbitraje manual
                conflict.status = ConflictStatus.ESCALATED
                await self._notify_conflict_event('conflict_needs_arbitration', conflict_id)

            # Mover a resueltos
            self.resolved_conflicts.append(resolution)
            del self.active_conflicts[conflict_id]

            self.stats['resolved_conflicts'] += 1

        except Exception as e:
            logger.error(f"❌ Conflict resolution failed for {conflict_id}: {e}")
            conflict.status = ConflictStatus.ESCALATED

    async def _analyze_conflict(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar un conflicto en detalle."""
        analysis = {
            'proposed_solution': {},
            'confidence_score': 0.0,
            'estimated_risk': 'medium',
            'execution_plan': []
        }

        if conflict.conflict_type == ConflictType.VALIDATION_DISAGREEMENT:
            analysis = await self._analyze_validation_disagreement(conflict)
        elif conflict.conflict_type == ConflictType.COMPETING_VERSIONS:
            analysis = await self._analyze_competing_versions(conflict)
        elif conflict.conflict_type == ConflictType.METADATA_INCONSISTENCY:
            analysis = await self._analyze_metadata_inconsistency(conflict)
        elif conflict.conflict_type == ConflictType.SECURITY_CONFLICT:
            analysis = await self._analyze_security_conflict(conflict)
        elif conflict.conflict_type == ConflictType.PERFORMANCE_REGRESSION:
            analysis = await self._analyze_performance_regression(conflict)

        return analysis

    async def _analyze_validation_disagreement(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar desacuerdo de validación."""
        # Obtener reportes de validación para las versiones
        validation_reports = {}
        for version_id in conflict.affected_versions:
            try:
                report = await self.validator.get_validation_report(version_id)
                validation_reports[version_id] = report
            except:
                validation_reports[version_id] = None

        # Calcular consensos
        approved_versions = []
        rejected_versions = []

        for version_id, report in validation_reports.items():
            if report and report.get('overall_status') == 'approved':
                approved_versions.append((version_id, report.get('average_score', 0)))
            elif report and report.get('overall_status') == 'rejected':
                rejected_versions.append((version_id, report.get('average_score', 0)))

        # Seleccionar versión con mejor consenso
        if approved_versions:
            selected_version = max(approved_versions, key=lambda x: x[1])[0]
            confidence = 0.8
        elif rejected_versions:
            # Si todas son rechazadas, seleccionar la menos mala
            selected_version = max(rejected_versions, key=lambda x: x[1])[0]
            confidence = 0.5
        else:
            selected_version = conflict.affected_versions[0]
            confidence = 0.3

        return {
            'proposed_solution': {'selected_version': selected_version},
            'confidence_score': confidence,
            'estimated_risk': 'low',
            'execution_plan': [
                {'action': 'select_version', 'version': selected_version},
                {'action': 'deprecate_others', 'versions': [v for v in conflict.affected_versions if v != selected_version]}
            ]
        }

    async def _analyze_competing_versions(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar versiones competidoras."""
        # Comparar métricas de calidad
        version_metrics = {}
        for version_id in conflict.affected_versions:
            version = await self.version_manager.get_version(version_id)
            if version:
                version_metrics[version_id] = version.quality_metrics

        # Seleccionar versión con mejores métricas
        best_version = None
        best_score = -1

        for version_id, metrics in version_metrics.items():
            # Calcular score compuesto
            accuracy = metrics.get('accuracy', 0)
            loss = metrics.get('loss', 1)
            score = accuracy / max(loss, 0.1)  # Accuracy/loss ratio

            if score > best_score:
                best_score = score
                best_version = version_id

        return {
            'proposed_solution': {'selected_version': best_version or conflict.affected_versions[0]},
            'confidence_score': 0.7,
            'estimated_risk': 'medium',
            'execution_plan': [
                {'action': 'select_best_version', 'version': best_version},
                {'action': 'merge_metadata', 'versions': conflict.affected_versions}
            ]
        }

    async def _analyze_metadata_inconsistency(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar inconsistencia de metadatos."""
        # Intentar fusionar metadatos conflictivos
        merged_metadata = {}
        conflicts_found = []

        versions_data = []
        for version_id in conflict.affected_versions:
            version = await self.version_manager.get_version(version_id)
            if version:
                versions_data.append(version)

        if len(versions_data) >= 2:
            # Comparar metadatos
            base_metadata = versions_data[0].federated_info
            for version in versions_data[1:]:
                for key, value in version.federated_info.items():
                    if key in base_metadata and base_metadata[key] != value:
                        conflicts_found.append({
                            'key': key,
                            'values': [base_metadata[key], value],
                            'versions': [versions_data[0].version_id, version.version_id]
                        })

            # Resolver conflictos simples
            for conflict_item in conflicts_found:
                key = conflict_item['key']
                values = conflict_item['values']
                # Usar el valor más reciente o promedio
                if isinstance(values[0], (int, float)) and isinstance(values[1], (int, float)):
                    merged_metadata[key] = (values[0] + values[1]) / 2
                else:
                    merged_metadata[key] = values[0]  # Mantener el primero

        return {
            'proposed_solution': {'merged_metadata': merged_metadata},
            'confidence_score': 0.6,
            'estimated_risk': 'low',
            'execution_plan': [
                {'action': 'merge_metadata', 'conflicts_resolved': len(conflicts_found)}
            ]
        }

    async def _analyze_security_conflict(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar conflicto de seguridad."""
        # Para conflictos de seguridad, siempre recomendar rollback
        stable_version = await self._find_most_stable_version(conflict.affected_versions)

        return {
            'proposed_solution': {'rollback_to': stable_version},
            'confidence_score': 0.9,
            'estimated_risk': 'high',
            'execution_plan': [
                {'action': 'security_audit', 'versions': conflict.affected_versions},
                {'action': 'rollback', 'to_version': stable_version}
            ]
        }

    async def _analyze_performance_regression(self, conflict: VersionConflict) -> Dict[str, Any]:
        """Analizar regresión de rendimiento."""
        # Comparar rendimiento con versiones anteriores
        current_metrics = {}
        for version_id in conflict.affected_versions:
            version = await self.version_manager.get_version(version_id)
            if version:
                current_metrics[version_id] = version.quality_metrics

        # Encontrar versión con mejor rendimiento
        best_performing = None
        best_accuracy = -1

        for version_id, metrics in current_metrics.items():
            accuracy = metrics.get('accuracy', 0)
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_performing = version_id

        return {
            'proposed_solution': {'best_version': best_performing},
            'confidence_score': 0.8,
            'estimated_risk': 'medium',
            'execution_plan': [
                {'action': 'performance_test', 'versions': conflict.affected_versions},
                {'action': 'select_best', 'version': best_performing}
            ]
        }

    def _select_resolution_strategy(self, conflict: VersionConflict, analysis: Dict[str, Any]) -> ResolutionStrategy:
        """Seleccionar estrategia de resolución."""
        available_strategies = self.resolution_strategies.get(conflict.conflict_type, [])

        # Seleccionar basado en confianza y riesgo
        confidence = analysis['confidence_score']
        risk = analysis['estimated_risk']

        if confidence >= 0.8 and risk == 'low':
            return ResolutionStrategy.AUTOMATIC_MERGE
        elif confidence >= 0.6:
            return ResolutionStrategy.PRIORITY_BASED
        else:
            return ResolutionStrategy.MANUAL_ARBITRATION

    async def _execute_resolution(self, resolution: ConflictResolution) -> bool:
        """Ejecutar una resolución."""
        try:
            for step in resolution.execution_plan:
                action = step.get('action')

                if action == 'select_version':
                    version_id = step['version']
                    await self.version_manager.force_activate_version(version_id, "Conflict resolution")

                elif action == 'deprecate_others':
                    for version_id in step['versions']:
                        await self.version_manager.deprecate_version(version_id, "Conflict resolution - deprecated")

                elif action == 'merge_metadata':
                    # Implementar fusión de metadatos
                    pass

                elif action == 'rollback':
                    # Implementar rollback
                    pass

                # Agregar más acciones según sea necesario

            return True

        except Exception as e:
            logger.error(f"❌ Resolution execution failed: {e}")
            return False

    async def _find_most_stable_version(self, version_ids: List[str]) -> Optional[str]:
        """Encontrar la versión más estable."""
        # Por simplicidad, devolver la más antigua validada
        versions = []
        for vid in version_ids:
            version = await self.version_manager.get_version(vid)
            if version:
                versions.append(version)

        if versions:
            # Ordenar por antigüedad y estado
            stable_versions = [v for v in versions if v.status.name == 'VALIDATED']
            if stable_versions:
                return min(stable_versions, key=lambda v: v.created_at).version_id

        return version_ids[0] if version_ids else None

    def _assess_conflict_severity(self, conflict: VersionConflict) -> str:
        """Evaluar severidad del conflicto."""
        if conflict.conflict_type == ConflictType.SECURITY_CONFLICT:
            return "critical"
        elif conflict.conflict_type in [ConflictType.PERFORMANCE_REGRESSION, ConflictType.FORKED_DEVELOPMENT]:
            return "high"
        elif len(conflict.affected_versions) > 2:
            return "high"
        else:
            return "medium"

    async def _conflict_monitoring(self):
        """Monitoreo continuo de conflictos."""
        while self.is_running:
            try:
                await self._detect_system_conflicts()
                await asyncio.sleep(300)  # Verificar cada 5 minutos

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Conflict monitoring error: {e}")
                await asyncio.sleep(60)

    async def _detect_system_conflicts(self):
        """Detectar conflictos en el sistema."""
        try:
            # Verificar versiones con validaciones divididas
            versions = await self.version_manager.list_versions()
            validating_versions = [v for v in versions if v.status.name == 'VALIDATING']

            for version in validating_versions:
                validation_status = await self.version_manager.get_validation_status(version.version_id)
                if validation_status:
                    votes = validation_status.get('votes', {})
                    approved = sum(1 for v in votes.values() if v == 'approved')
                    rejected = sum(1 for v in votes.values() if v == 'rejected')

                    if approved > 0 and rejected > 0 and abs(approved - rejected) <= 1:
                        # Conflicto de validación
                        await self.detect_conflict(
                            conflict_type=ConflictType.VALIDATION_DISAGREEMENT,
                            affected_versions=[version.version_id],
                            description=f"Split validation votes: {approved} approved, {rejected} rejected",
                            involved_nodes=set(votes.keys())
                        )

            # Verificar versiones competidoras activas
            active_versions = [v for v in versions if v.is_active]
            if len(active_versions) > 1:
                await self.detect_conflict(
                    conflict_type=ConflictType.COMPETING_VERSIONS,
                    affected_versions=[v.version_id for v in active_versions],
                    description=f"Multiple active versions: {len(active_versions)}",
                    involved_nodes=set()  # Todos los nodos
                )

        except Exception as e:
            logger.error(f"❌ Conflict detection failed: {e}")

    async def _notify_conflict_event(self, event_type: str, conflict_id: str):
        """Notificar eventos de conflicto."""
        for callback in self.conflict_callbacks:
            try:
                await callback(event_type, conflict_id)
            except Exception as e:
                logger.warning(f"Conflict callback failed: {e}")

    def add_conflict_callback(self, callback: Callable):
        """Agregar callback para eventos de conflicto."""
        self.conflict_callbacks.append(callback)

    async def get_conflict_status(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un conflicto."""
        conflict = self.active_conflicts.get(conflict_id)
        if conflict:
            return conflict.to_dict()

        # Buscar en resueltos
        for resolution in self.resolved_conflicts:
            if resolution.conflict.conflict_id == conflict_id:
                return resolution.to_dict()

        return None

    async def manual_resolution(self, conflict_id: str, selected_version: str,
                              resolution_notes: str = "") -> bool:
        """Resolución manual de conflicto."""
        conflict = self.active_conflicts.get(conflict_id)
        if not conflict:
            return False

        try:
            # Forzar activación de la versión seleccionada
            await self.version_manager.force_activate_version(
                selected_version,
                f"Manual conflict resolution: {resolution_notes}"
            )

            # Deprecar otras versiones
            for version_id in conflict.affected_versions:
                if version_id != selected_version:
                    await self.version_manager.deprecate_version(
                        version_id,
                        f"Manual conflict resolution - deprecated in favor of {selected_version}"
                    )

            # Marcar como resuelto
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolved_version = selected_version
            conflict.resolution_details = {
                'manual_resolution': True,
                'selected_version': selected_version,
                'notes': resolution_notes
            }

            # Mover a resueltos
            resolution = ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.MANUAL_ARBITRATION,
                proposed_solution={'selected_version': selected_version},
                confidence_score=1.0,
                estimated_risk='low',
                execution_plan=[],
                executed_at=int(time.time()),
                success=True
            )

            self.resolved_conflicts.append(resolution)
            del self.active_conflicts[conflict_id]

            await self._notify_conflict_event('conflict_manually_resolved', conflict_id)

            logger.info(f"✅ Manual conflict resolution: {conflict_id} -> {selected_version}")
            return True

        except Exception as e:
            logger.error(f"❌ Manual resolution failed: {e}")
            return False

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de conflictos."""
        return {
            'total_conflicts': self.stats['total_conflicts'],
            'resolved_conflicts': self.stats['resolved_conflicts'],
            'escalated_conflicts': self.stats['escalated_conflicts'],
            'auto_resolved_conflicts': self.stats['auto_resolved_conflicts'],
            'active_conflicts': len(self.active_conflicts),
            'resolution_rate': self.stats['resolved_conflicts'] / max(1, self.stats['total_conflicts']),
            'auto_resolution_rate': self.stats['auto_resolved_conflicts'] / max(1, self.stats['resolved_conflicts'])
        }