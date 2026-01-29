"""
Sistema de Knowledge Evolution para evolución y actualización del conocimiento basado en el diseño arquitectónico.
Implementa evolución temporal del conocimiento, actualización incremental de conceptos, y seguimiento de cambios.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import get_logger
from .core import KnowledgeGraphCore, Triple, FormatType
from .versioning import get_version_manager, VersionManager
from .ontology import get_ontology_manager, OntologyManager
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


class EvolutionType(Enum):
    """Tipos de evolución del conocimiento."""
    TEMPORAL = "temporal"
    ONTOLOGICAL = "ontological"
    RULE_BASED = "rule_based"
    OBSOLESCENCE = "obsolescence"


class ObsolescenceStrategy(Enum):
    """Estrategias para gestión de obsolescencia."""
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based"
    ACCURACY_BASED = "accuracy_based"
    MANUAL = "manual"


@dataclass
class EvolutionRule:
    """Regla de evolución del conocimiento."""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int = 1
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class ConceptUpdate:
    """Actualización de concepto."""
    concept_uri: str
    update_type: str  # 'add', 'modify', 'remove', 'obsolete'
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    confidence: float = 1.0


@dataclass
class EvolutionHistory:
    """Historial de evolución."""
    evolution_id: str
    evolution_type: EvolutionType
    timestamp: datetime
    changes: List[ConceptUpdate] = field(default_factory=list)
    version_snapshot: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeEvolution:
    """
    Sistema de evolución del conocimiento para AILOOS.
    Maneja evolución temporal, ontológica, basada en reglas y gestión de obsolescencia.
    """

    def __init__(self, knowledge_graph_core: Optional[KnowledgeGraphCore] = None):
        """
        Inicializar KnowledgeEvolution.

        Args:
            knowledge_graph_core: Instancia de KnowledgeGraphCore
        """
        self.kg_core = knowledge_graph_core or KnowledgeGraphCore()

        # Integraciones
        self.version_manager = get_version_manager(self.kg_core)
        self.ontology_manager = get_ontology_manager(self.kg_core)
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Estado de evolución
        self.evolution_rules: Dict[str, EvolutionRule] = {}
        self.evolution_history: List[EvolutionHistory] = []
        self.obsolescence_tracker: Dict[str, Dict[str, Any]] = {}

        # Configuración
        self.obsolescence_threshold_days = 365  # 1 año
        self.auto_evolution_enabled = True
        self.evolution_interval_minutes = 60  # Ejecutar evolución cada hora

        # Estadísticas
        self.stats = {
            "total_evolutions": 0,
            "concepts_updated": 0,
            "rules_triggered": 0,
            "obsolete_concepts": 0
        }

        logger.info("KnowledgeEvolution initialized")

    async def evolve_knowledge(
        self,
        evolution_type: EvolutionType,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecutar evolución del conocimiento.

        Args:
            evolution_type: Tipo de evolución a ejecutar
            parameters: Parámetros específicos para la evolución
            user_id: ID del usuario que inicia la evolución

        Returns:
            Resultado de la evolución
        """
        start_time = time.time()
        parameters = parameters or {}

        try:
            evolution_id = f"evolution_{int(time.time())}_{evolution_type.value}"

            # Crear snapshot antes de la evolución
            snapshot_id = await self.version_manager.create_version(
                user_id=user_id,
                description=f"Pre-evolution snapshot for {evolution_type.value}",
                tags=["evolution", "snapshot"]
            )

            changes = []

            # Ejecutar evolución según tipo
            if evolution_type == EvolutionType.TEMPORAL:
                changes = await self._evolve_temporal(parameters)
            elif evolution_type == EvolutionType.ONTOLOGICAL:
                changes = await self._evolve_ontological(parameters)
            elif evolution_type == EvolutionType.RULE_BASED:
                changes = await self._evolve_rule_based(parameters)
            elif evolution_type == EvolutionType.OBSOLESCENCE:
                changes = await self._evolve_obsolescence(parameters)

            # Crear snapshot después de la evolución
            post_snapshot_id = await self.version_manager.create_version(
                user_id=user_id,
                description=f"Post-evolution snapshot for {evolution_type.value}",
                tags=["evolution", "result"]
            )

            # Registrar historial
            history = EvolutionHistory(
                evolution_id=evolution_id,
                evolution_type=evolution_type,
                timestamp=datetime.now(),
                changes=changes,
                version_snapshot=post_snapshot_id,
                metadata={
                    "pre_snapshot": snapshot_id,
                    "parameters": parameters,
                    "changes_count": len(changes)
                }
            )
            self.evolution_history.append(history)

            # Actualizar estadísticas
            self.stats["total_evolutions"] += 1
            self.stats["concepts_updated"] += len(changes)

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="evolve_knowledge",
                user_id=user_id,
                details={
                    "evolution_id": evolution_id,
                    "evolution_type": evolution_type.value,
                    "changes_count": len(changes),
                    "pre_snapshot": snapshot_id,
                    "post_snapshot": post_snapshot_id
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_evolution.evolve_knowledge")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            result = {
                "evolution_id": evolution_id,
                "evolution_type": evolution_type.value,
                "changes_applied": len(changes),
                "pre_snapshot": snapshot_id,
                "post_snapshot": post_snapshot_id,
                "processing_time_ms": (time.time() - start_time) * 1000
            }

            logger.info(f"Knowledge evolution completed: {evolution_type.value}, changes: {len(changes)}")
            return result

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="evolve_knowledge",
                user_id=user_id,
                details={
                    "error": str(e),
                    "evolution_type": evolution_type.value,
                    "parameters": parameters
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_evolution.evolve_knowledge", "evolution_error")
            logger.error(f"Knowledge evolution failed: {e}")
            raise

    async def update_concepts(
        self,
        concept_updates: List[ConceptUpdate],
        ontology_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualizar conceptos de manera incremental.

        Args:
            concept_updates: Lista de actualizaciones de conceptos
            ontology_id: ID de la ontología a actualizar (opcional)
            user_id: ID del usuario

        Returns:
            Resultado de las actualizaciones
        """
        start_time = time.time()

        try:
            successful_updates = 0
            failed_updates = []

            for update in concept_updates:
                try:
                    # Aplicar actualización según tipo
                    if update.update_type == "add":
                        success = await self._add_concept_property(update)
                    elif update.update_type == "modify":
                        success = await self._modify_concept_property(update)
                    elif update.update_type == "remove":
                        success = await self._remove_concept_property(update)
                    elif update.update_type == "obsolete":
                        success = await self._obsolete_concept(update)
                    else:
                        raise ValueError(f"Unknown update type: {update.update_type}")

                    if success:
                        successful_updates += 1

                        # Actualizar ontología si especificada
                        if ontology_id:
                            await self.ontology_manager.evolve_concept(
                                ontology_id,
                                update.concept_uri,
                                {"property_updates": [update]},
                                user_id
                            )
                    else:
                        failed_updates.append({
                            "concept": update.concept_uri,
                            "error": "Update failed"
                        })

                except Exception as e:
                    failed_updates.append({
                        "concept": update.concept_uri,
                        "error": str(e)
                    })

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="update_concepts",
                user_id=user_id,
                details={
                    "total_updates": len(concept_updates),
                    "successful_updates": successful_updates,
                    "failed_updates": len(failed_updates),
                    "ontology_id": ontology_id
                },
                success=successful_updates > 0,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_evolution.update_concepts")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            result = {
                "total_updates": len(concept_updates),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "processing_time_ms": (time.time() - start_time) * 1000
            }

            logger.info(f"Concept updates completed: {successful_updates}/{len(concept_updates)} successful")
            return result

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="update_concepts",
                user_id=user_id,
                details={"error": str(e), "total_updates": len(concept_updates)},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_evolution.update_concepts", "update_error")
            logger.error(f"Concept updates failed: {e}")
            raise

    async def track_changes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        concept_filter: Optional[str] = None,
        evolution_type_filter: Optional[EvolutionType] = None
    ) -> Dict[str, Any]:
        """
        Obtener historial de cambios con seguimiento detallado.

        Args:
            start_date: Fecha de inicio del seguimiento
            end_date: Fecha de fin del seguimiento
            concept_filter: Filtro por concepto específico
            evolution_type_filter: Filtro por tipo de evolución

        Returns:
            Historial de cambios
        """
        start_time = time.time()

        try:
            # Filtrar historial
            filtered_history = self.evolution_history

            if start_date:
                filtered_history = [h for h in filtered_history if h.timestamp >= start_date]
            if end_date:
                filtered_history = [h for h in filtered_history if h.timestamp <= end_date]
            if evolution_type_filter:
                filtered_history = [h for h in filtered_history if h.evolution_type == evolution_type_filter]

            # Filtrar cambios por concepto si especificado
            if concept_filter:
                for history in filtered_history:
                    history.changes = [c for c in history.changes if concept_filter in c.concept_uri]

            # Calcular estadísticas
            total_changes = sum(len(h.changes) for h in filtered_history)
            evolution_types = {}
            for history in filtered_history:
                ev_type = history.evolution_type.value
                evolution_types[ev_type] = evolution_types.get(ev_type, 0) + 1

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="track_changes",
                details={
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "concept_filter": concept_filter,
                    "evolution_type_filter": evolution_type_filter.value if evolution_type_filter else None,
                    "total_changes": total_changes,
                    "evolution_count": len(filtered_history)
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("knowledge_evolution.track_changes")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            result = {
                "total_evolutions": len(filtered_history),
                "total_changes": total_changes,
                "evolution_types": evolution_types,
                "history": [
                    {
                        "evolution_id": h.evolution_id,
                        "evolution_type": h.evolution_type.value,
                        "timestamp": h.timestamp.isoformat(),
                        "changes_count": len(h.changes),
                        "version_snapshot": h.version_snapshot,
                        "metadata": h.metadata
                    }
                    for h in sorted(filtered_history, key=lambda x: x.timestamp, reverse=True)
                ],
                "processing_time_ms": (time.time() - start_time) * 1000
            }

            logger.info(f"Change tracking completed: {total_changes} changes across {len(filtered_history)} evolutions")
            return result

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_evolution",
                action="track_changes",
                details={"error": str(e)},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("knowledge_evolution.track_changes", "tracking_error")
            logger.error(f"Change tracking failed: {e}")
            raise

    # Métodos de evolución específicos

    async def _evolve_temporal(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Evolución temporal del conocimiento."""
        changes = []

        # Verificar conceptos con timestamps antiguos
        cutoff_date = datetime.now() - timedelta(days=parameters.get("days_threshold", 30))

        # En implementación real, consultar triples con timestamps
        # Por ahora, simular algunos cambios
        temporal_concepts = [
            "http://example.org/concept1",
            "http://example.org/concept2"
        ]

        for concept in temporal_concepts:
            # Simular actualización temporal
            update = ConceptUpdate(
                concept_uri=concept,
                update_type="modify",
                old_value="old_temporal_data",
                new_value="updated_temporal_data",
                reason="Temporal evolution",
                confidence=0.8
            )
            changes.append(update)

        return changes

    async def _evolve_ontological(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Evolución ontológica."""
        changes = []
        ontology_id = parameters.get("ontology_id")

        if ontology_id and ontology_id in self.ontology_manager.loaded_ontologies:
            # Usar OntologyManager para evolución
            evolution_changes = parameters.get("changes", [])

            for change in evolution_changes:
                concept_uri = change.get("concept_uri")
                evolution_data = change.get("evolution_data", {})

                success = await self.ontology_manager.evolve_concept(
                    ontology_id,
                    concept_uri,
                    evolution_data
                )

                if success:
                    update = ConceptUpdate(
                        concept_uri=concept_uri,
                        update_type="modify",
                        new_value=evolution_data,
                        reason="Ontological evolution",
                        confidence=0.9
                    )
                    changes.append(update)

        return changes

    async def _evolve_rule_based(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Evolución basada en reglas."""
        changes = []

        # Ejecutar reglas activas
        for rule in self.evolution_rules.values():
            if not rule.enabled:
                continue

            try:
                # Verificar condiciones de la regla
                if await self._check_rule_conditions(rule):
                    # Ejecutar acciones de la regla
                    rule_changes = await self._execute_rule_actions(rule)
                    changes.extend(rule_changes)

                    # Actualizar estadísticas de la regla
                    rule.last_triggered = datetime.now()
                    rule.trigger_count += 1
                    self.stats["rules_triggered"] += 1

            except Exception as e:
                logger.error(f"Error executing rule {rule.rule_id}: {e}")

        return changes

    async def _evolve_obsolescence(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Gestión de obsolescencia."""
        changes = []
        strategy = ObsolescenceStrategy(parameters.get("strategy", "time_based"))

        if strategy == ObsolescenceStrategy.TIME_BASED:
            changes = await self._obsolete_time_based(parameters)
        elif strategy == ObsolescenceStrategy.USAGE_BASED:
            changes = await self._obsolete_usage_based(parameters)
        elif strategy == ObsolescenceStrategy.ACCURACY_BASED:
            changes = await self._obsolete_accuracy_based(parameters)

        # Actualizar estadísticas
        self.stats["obsolete_concepts"] += len(changes)

        return changes

    # Métodos auxiliares para actualizaciones de conceptos

    async def _add_concept_property(self, update: ConceptUpdate) -> bool:
        """Agregar propiedad a concepto."""
        try:
            triple = Triple(
                subject=update.concept_uri,
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#property",
                object=update.new_value
            )
            return await self.kg_core.add_triple(triple)
        except Exception as e:
            logger.error(f"Failed to add concept property: {e}")
            return False

    async def _modify_concept_property(self, update: ConceptUpdate) -> bool:
        """Modificar propiedad de concepto."""
        try:
            # Remover valor antiguo
            if update.old_value is not None:
                old_triple = Triple(
                    subject=update.concept_uri,
                    predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#property",
                    object=update.old_value
                )
                await self.kg_core.remove_triple(old_triple)

            # Agregar nuevo valor
            new_triple = Triple(
                subject=update.concept_uri,
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#property",
                object=update.new_value
            )
            return await self.kg_core.add_triple(new_triple)
        except Exception as e:
            logger.error(f"Failed to modify concept property: {e}")
            return False

    async def _remove_concept_property(self, update: ConceptUpdate) -> bool:
        """Remover propiedad de concepto."""
        try:
            triple = Triple(
                subject=update.concept_uri,
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#property",
                object=update.old_value
            )
            return await self.kg_core.remove_triple(triple)
        except Exception as e:
            logger.error(f"Failed to remove concept property: {e}")
            return False

    async def _obsolete_concept(self, update: ConceptUpdate) -> bool:
        """Marcar concepto como obsoleto."""
        try:
            # Agregar triple de obsolescencia
            obsolete_triple = Triple(
                subject=update.concept_uri,
                predicate="http://www.w3.org/2002/07/owl#deprecated",
                object=True
            )
            return await self.kg_core.add_triple(obsolete_triple)
        except Exception as e:
            logger.error(f"Failed to obsolete concept: {e}")
            return False

    # Métodos para reglas de evolución

    def add_evolution_rule(self, rule: EvolutionRule) -> bool:
        """Agregar regla de evolución."""
        if rule.rule_id in self.evolution_rules:
            return False

        self.evolution_rules[rule.rule_id] = rule
        logger.info(f"Evolution rule added: {rule.rule_id}")
        return True

    def remove_evolution_rule(self, rule_id: str) -> bool:
        """Remover regla de evolución."""
        if rule_id not in self.evolution_rules:
            return False

        del self.evolution_rules[rule_id]
        logger.info(f"Evolution rule removed: {rule_id}")
        return True

    async def _check_rule_conditions(self, rule: EvolutionRule) -> bool:
        """Verificar condiciones de una regla."""
        # Implementación simplificada - en producción verificar consultas SPARQL o patrones
        conditions = rule.conditions

        # Ejemplo: verificar si existen ciertos triples
        if "required_triples" in conditions:
            for triple_pattern in conditions["required_triples"]:
                # Simular verificación
                pass

        return True  # Por simplicidad, siempre verdadero

    async def _execute_rule_actions(self, rule: EvolutionRule) -> List[ConceptUpdate]:
        """Ejecutar acciones de una regla."""
        changes = []

        for action in rule.actions:
            action_type = action.get("type")

            if action_type == "add_triple":
                # Agregar triple
                triple_data = action.get("triple", {})
                triple = Triple(**triple_data)
                await self.kg_core.add_triple(triple)

                update = ConceptUpdate(
                    concept_uri=triple.subject,
                    update_type="add",
                    new_value=triple.object,
                    reason=f"Rule {rule.rule_id} execution"
                )
                changes.append(update)

            elif action_type == "update_concept":
                # Actualizar concepto
                concept_uri = action.get("concept_uri")
                new_value = action.get("new_value")

                update = ConceptUpdate(
                    concept_uri=concept_uri,
                    update_type="modify",
                    new_value=new_value,
                    reason=f"Rule {rule.rule_id} execution"
                )
                changes.append(update)

        return changes

    # Métodos para gestión de obsolescencia

    async def _obsolete_time_based(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Obsolescencia basada en tiempo."""
        changes = []
        days_threshold = parameters.get("days_threshold", self.obsolescence_threshold_days)

        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        # En implementación real, consultar triples con timestamps
        # Por ahora, simular conceptos obsoletos
        obsolete_concepts = [
            "http://example.org/old_concept1",
            "http://example.org/old_concept2"
        ]

        for concept in obsolete_concepts:
            update = ConceptUpdate(
                concept_uri=concept,
                update_type="obsolete",
                reason=f"Time-based obsolescence (>{days_threshold} days)",
                confidence=0.95
            )
            changes.append(update)

        return changes

    async def _obsolete_usage_based(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Obsolescencia basada en uso."""
        changes = []
        usage_threshold = parameters.get("usage_threshold", 0)  # consultas en período

        # Simular conceptos poco usados
        unused_concepts = [
            "http://example.org/unused_concept1"
        ]

        for concept in unused_concepts:
            update = ConceptUpdate(
                concept_uri=concept,
                update_type="obsolete",
                reason=f"Usage-based obsolescence (<{usage_threshold} queries)",
                confidence=0.85
            )
            changes.append(update)

        return changes

    async def _obsolete_accuracy_based(self, parameters: Dict[str, Any]) -> List[ConceptUpdate]:
        """Obsolescencia basada en precisión."""
        changes = []
        accuracy_threshold = parameters.get("accuracy_threshold", 0.5)

        # Simular conceptos con baja precisión
        inaccurate_concepts = [
            "http://example.org/inaccurate_concept1"
        ]

        for concept in inaccurate_concepts:
            update = ConceptUpdate(
                concept_uri=concept,
                update_type="obsolete",
                reason=f"Accuracy-based obsolescence (<{accuracy_threshold} accuracy)",
                confidence=0.9
            )
            changes.append(update)

        return changes

    # Métodos de consulta y estadísticas

    def get_evolution_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de evolución."""
        return {
            "total_evolutions": self.stats["total_evolutions"],
            "concepts_updated": self.stats["concepts_updated"],
            "rules_triggered": self.stats["rules_triggered"],
            "obsolete_concepts": self.stats["obsolete_concepts"],
            "active_rules": len([r for r in self.evolution_rules.values() if r.enabled]),
            "evolution_history_count": len(self.evolution_history)
        }

    def get_evolution_rules(self) -> List[Dict[str, Any]]:
        """Obtener reglas de evolución."""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            }
            for rule in self.evolution_rules.values()
        ]

    async def start_auto_evolution(self):
        """Iniciar evolución automática periódica."""
        if not self.auto_evolution_enabled:
            return

        while True:
            try:
                await asyncio.sleep(self.evolution_interval_minutes * 60)

                # Ejecutar evolución automática
                await self.evolve_knowledge(
                    EvolutionType.RULE_BASED,
                    {"auto": True}
                )

                # Verificar obsolescencia
                await self.evolve_knowledge(
                    EvolutionType.OBSOLESCENCE,
                    {"strategy": "time_based", "auto": True}
                )

            except Exception as e:
                logger.error(f"Auto evolution failed: {e}")


# Instancia global
_knowledge_evolution = None

def get_knowledge_evolution(knowledge_graph_core: Optional[KnowledgeGraphCore] = None) -> KnowledgeEvolution:
    """Obtener instancia global del sistema de evolución del conocimiento."""
    global _knowledge_evolution
    if _knowledge_evolution is None:
        _knowledge_evolution = KnowledgeEvolution(knowledge_graph_core)
    return _knowledge_evolution