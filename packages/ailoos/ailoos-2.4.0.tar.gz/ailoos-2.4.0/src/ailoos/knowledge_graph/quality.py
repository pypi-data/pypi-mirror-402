"""
Sistema de Quality Assurance para validación y aseguramiento de calidad del grafo de conocimiento.
Implementa validación de calidad, detección de inconsistencias y generación de reportes.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ..core.logging import get_logger
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from .ontology import get_ontology_manager, OntologyManager
from .inference import get_inference_engine, InferenceEngine
from .core import get_knowledge_graph_core, Triple

logger = get_logger(__name__)


class QualityMetric(Enum):
    """Métricas de calidad soportadas."""
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"


class QualityRuleType(Enum):
    """Tipos de reglas de calidad."""
    SCHEMA_VALIDATION = "schema_validation"
    LOGICAL_CONSISTENCY = "logical_consistency"
    DATA_INTEGRITY = "data_integrity"
    ONTOLOGY_COMPLIANCE = "ontology_compliance"
    INFERENCE_VALIDATION = "inference_validation"


class QualitySeverity(Enum):
    """Niveles de severidad para problemas de calidad."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityRule:
    """Regla de calidad configurable."""
    rule_id: str
    rule_type: QualityRuleType
    name: str
    description: str
    metric: QualityMetric
    threshold: float
    severity: QualitySeverity
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "metric": self.metric.value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "parameters": self.parameters
        }


@dataclass
class QualityIssue:
    """Problema de calidad identificado."""
    issue_id: str
    rule_id: str
    severity: QualitySeverity
    title: str
    description: str
    affected_triples: List[Triple]
    suggested_fix: Optional[str] = None
    confidence_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "affected_triples": [t.to_dict() for t in self.affected_triples],
            "suggested_fix": self.suggested_fix,
            "confidence_score": self.confidence_score
        }


@dataclass
class QualityMetrics:
    """Métricas de calidad calculadas."""
    completeness_score: float
    consistency_score: float
    accuracy_score: float
    timeliness_score: float
    validity_score: float
    overall_score: float
    total_triples: int
    issues_count: int
    issues_by_severity: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness_score": self.completeness_score,
            "consistency_score": self.consistency_score,
            "accuracy_score": self.accuracy_score,
            "timeliness_score": self.timeliness_score,
            "validity_score": self.validity_score,
            "overall_score": self.overall_score,
            "total_triples": self.total_triples,
            "issues_count": self.issues_count,
            "issues_by_severity": self.issues_by_severity
        }


@dataclass
class QualityReport:
    """Reporte completo de calidad."""
    report_id: str
    timestamp: float
    execution_time_ms: float
    metrics: QualityMetrics
    issues: List[QualityIssue]
    rules_applied: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
            "metrics": self.metrics.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "rules_applied": self.rules_applied,
            "recommendations": self.recommendations
        }


class QualityAssurance:
    """
    Sistema de Quality Assurance para el grafo de conocimiento.
    Valida calidad, detecta inconsistencias y genera reportes.
    """

    def __init__(
        self,
        knowledge_graph_core=None,
        ontology_manager: Optional[OntologyManager] = None,
        inference_engine: Optional[InferenceEngine] = None,
        audit_manager=None,
        metrics_collector=None
    ):
        """
        Inicializar QualityAssurance.

        Args:
            knowledge_graph_core: Instancia de KnowledgeGraphCore
            ontology_manager: Instancia de OntologyManager
            inference_engine: Instancia de InferenceEngine
            audit_manager: Instancia de AuditManager
            metrics_collector: Instancia de MetricsCollector
        """
        self.kg_core = knowledge_graph_core or get_knowledge_graph_core()
        self.ontology_manager = ontology_manager or get_ontology_manager()
        self.inference_engine = inference_engine or get_inference_engine()
        self.audit_manager = audit_manager or get_audit_manager()
        self.metrics_collector = metrics_collector or get_metrics_collector()

        # Reglas de calidad
        self.quality_rules: Dict[str, QualityRule] = {}
        self._initialize_default_rules()

        # Configuración
        self.max_issues_per_report = 1000
        self.quality_thresholds = {
            QualityMetric.COMPLETENESS: 0.8,
            QualityMetric.CONSISTENCY: 0.9,
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.TIMELINESS: 0.7,
            QualityMetric.VALIDITY: 0.95
        }

    def _initialize_default_rules(self):
        """Inicializar reglas de calidad por defecto."""

        # Regla de completitud: verificar triples con propiedades requeridas
        completeness_rule = QualityRule(
            rule_id="completeness_required_properties",
            rule_type=QualityRuleType.DATA_INTEGRITY,
            name="Required Properties Check",
            description="Verificar que entidades tengan propiedades requeridas",
            metric=QualityMetric.COMPLETENESS,
            threshold=0.8,
            severity=QualitySeverity.MEDIUM,
            parameters={
                "required_properties": ["rdfs:label", "rdf:type"],
                "entity_types": ["owl:Class", "owl:NamedIndividual"]
            }
        )
        self.quality_rules[completeness_rule.rule_id] = completeness_rule

        # Regla de consistencia: verificar referencias a entidades inexistentes
        consistency_rule = QualityRule(
            rule_id="consistency_entity_references",
            rule_type=QualityRuleType.LOGICAL_CONSISTENCY,
            name="Entity Reference Consistency",
            description="Verificar que todas las referencias a entidades existan",
            metric=QualityMetric.CONSISTENCY,
            threshold=0.95,
            severity=QualitySeverity.HIGH,
            parameters={}
        )
        self.quality_rules[consistency_rule.rule_id] = consistency_rule

        # Regla de validez ontológica
        ontology_rule = QualityRule(
            rule_id="ontology_schema_validation",
            rule_type=QualityRuleType.ONTOLOGY_COMPLIANCE,
            name="Ontology Schema Validation",
            description="Validar triples contra esquemas ontológicos",
            metric=QualityMetric.VALIDITY,
            threshold=0.9,
            severity=QualitySeverity.HIGH,
            parameters={
                "validate_domains_ranges": True,
                "validate_cardinalities": True
            }
        )
        self.quality_rules[ontology_rule.rule_id] = ontology_rule

        # Regla de inferencia: verificar consistencia con inferencias
        inference_rule = QualityRule(
            rule_id="inference_consistency_check",
            rule_type=QualityRuleType.INFERENCE_VALIDATION,
            name="Inference Consistency Check",
            description="Verificar consistencia con reglas de inferencia",
            metric=QualityMetric.CONSISTENCY,
            threshold=0.85,
            severity=QualitySeverity.MEDIUM,
            parameters={
                "max_inference_depth": 3,
                "check_conflicts": True
            }
        )
        self.quality_rules[inference_rule.rule_id] = inference_rule

    async def validate_quality(
        self,
        triples: Optional[List[Triple]] = None,
        ontology_ids: Optional[List[str]] = None,
        rules_to_apply: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> QualityMetrics:
        """
        Validar calidad del grafo de conocimiento.

        Args:
            triples: Triples específicos a validar (None = todos)
            ontology_ids: IDs de ontologías para validación
            rules_to_apply: IDs de reglas a aplicar (None = todas)
            user_id: ID del usuario

        Returns:
            QualityMetrics con resultados de validación
        """
        start_time = time.time()

        try:
            # Obtener triples a validar
            if triples is None:
                triples = await self.kg_core.get_all_triples()

            # Seleccionar reglas
            rules = self._select_rules(rules_to_apply)

            # Ejecutar validaciones
            issues = []
            for rule in rules:
                if rule.enabled:
                    rule_issues = await self._execute_quality_rule(rule, triples, ontology_ids, user_id)
                    issues.extend(rule_issues)

            # Calcular métricas
            metrics = self._calculate_quality_metrics(triples, issues)

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="validate_quality",
                user_id=user_id,
                details={
                    "total_triples": len(triples),
                    "rules_applied": len(rules),
                    "issues_found": len(issues),
                    "overall_score": metrics.overall_score
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("quality_assurance.validate_quality")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Quality validation completed: {len(issues)} issues found, score: {metrics.overall_score:.2f}")
            return metrics

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="validate_quality",
                user_id=user_id,
                details={"error": str(e)},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("quality_assurance.validate_quality", "validation_error")
            logger.error(f"Quality validation failed: {e}")

            # Retornar métricas con score 0
            return QualityMetrics(
                completeness_score=0.0,
                consistency_score=0.0,
                accuracy_score=0.0,
                timeliness_score=0.0,
                validity_score=0.0,
                overall_score=0.0,
                total_triples=len(triples) if triples else 0,
                issues_count=0,
                issues_by_severity={}
            )

    async def detect_inconsistencies(
        self,
        triples: Optional[List[Triple]] = None,
        ontology_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> List[QualityIssue]:
        """
        Detectar inconsistencias lógicas en el grafo.

        Args:
            triples: Triples a analizar (None = todos)
            ontology_ids: IDs de ontologías para validación
            user_id: ID del usuario

        Returns:
            Lista de inconsistencias encontradas
        """
        start_time = time.time()

        try:
            # Obtener triples
            if triples is None:
                triples = await self.kg_core.get_all_triples()

            inconsistencies = []

            # Verificar referencias rotas
            broken_refs = await self._detect_broken_references(triples)
            inconsistencies.extend(broken_refs)

            # Verificar contradicciones lógicas
            logical_conflicts = await self._detect_logical_conflicts(triples)
            inconsistencies.extend(logical_conflicts)

            # Verificar inconsistencias ontológicas
            if ontology_ids:
                ontology_issues = await self._detect_ontology_inconsistencies(triples, ontology_ids)
                inconsistencies.extend(ontology_issues)

            # Verificar inconsistencias de inferencia
            inference_issues = await self._detect_inference_inconsistencies(triples)
            inconsistencies.extend(inference_issues)

            # Limitar número de issues
            if len(inconsistencies) > self.max_issues_per_report:
                inconsistencies = inconsistencies[:self.max_issues_per_report]

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="detect_inconsistencies",
                user_id=user_id,
                details={
                    "total_triples": len(triples),
                    "inconsistencies_found": len(inconsistencies)
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("quality_assurance.detect_inconsistencies")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Inconsistency detection completed: {len(inconsistencies)} inconsistencies found")
            return inconsistencies

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="detect_inconsistencies",
                user_id=user_id,
                details={"error": str(e)},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("quality_assurance.detect_inconsistencies", "detection_error")
            logger.error(f"Inconsistency detection failed: {e}")
            return []

    async def generate_report(
        self,
        triples: Optional[List[Triple]] = None,
        ontology_ids: Optional[List[str]] = None,
        include_inconsistencies: bool = True,
        user_id: Optional[str] = None
    ) -> QualityReport:
        """
        Generar reporte completo de calidad.

        Args:
            triples: Triples a analizar (None = todos)
            ontology_ids: IDs de ontologías para validación
            include_inconsistencies: Incluir detección de inconsistencias
            user_id: ID del usuario

        Returns:
            QualityReport completo
        """
        start_time = time.time()
        import secrets

        try:
            # Validar calidad
            metrics = await self.validate_quality(triples, ontology_ids, user_id=user_id)

            # Detectar inconsistencias si solicitado
            issues = []
            if include_inconsistencies:
                issues = await self.detect_inconsistencies(triples, ontology_ids, user_id=user_id)

            # Generar recomendaciones
            recommendations = self._generate_recommendations(metrics, issues)

            # Crear reporte
            report = QualityReport(
                report_id=secrets.token_hex(8),
                timestamp=time.time(),
                execution_time_ms=(time.time() - start_time) * 1000,
                metrics=metrics,
                issues=issues,
                rules_applied=list(self.quality_rules.keys()),
                recommendations=recommendations
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="generate_report",
                user_id=user_id,
                details={
                    "report_id": report.report_id,
                    "overall_score": metrics.overall_score,
                    "issues_count": len(issues),
                    "execution_time_ms": report.execution_time_ms
                },
                success=True,
                processing_time_ms=report.execution_time_ms
            )

            # Métricas
            self.metrics_collector.record_request("quality_assurance.generate_report")
            self.metrics_collector.record_response_time(report.execution_time_ms)

            logger.info(f"Quality report generated: {report.report_id}, score: {metrics.overall_score:.2f}")
            return report

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="generate_report",
                user_id=user_id,
                details={"error": str(e)},
                success=False,
                processing_time_ms=execution_time
            )

            self.metrics_collector.record_error("quality_assurance.generate_report", "report_error")
            logger.error(f"Report generation failed: {e}")

            # Retornar reporte vacío
            return QualityReport(
                report_id=secrets.token_hex(8),
                timestamp=time.time(),
                execution_time_ms=execution_time,
                metrics=QualityMetrics(
                    completeness_score=0.0,
                    consistency_score=0.0,
                    accuracy_score=0.0,
                    timeliness_score=0.0,
                    validity_score=0.0,
                    overall_score=0.0,
                    total_triples=0,
                    issues_count=0,
                    issues_by_severity={}
                ),
                issues=[],
                rules_applied=[],
                recommendations=["Error generating report"]
            )

    def _select_rules(self, rules_to_apply: Optional[List[str]]) -> List[QualityRule]:
        """Seleccionar reglas a aplicar."""
        if rules_to_apply:
            return [self.quality_rules[rule_id] for rule_id in rules_to_apply
                   if rule_id in self.quality_rules and self.quality_rules[rule_id].enabled]
        else:
            return [rule for rule in self.quality_rules.values() if rule.enabled]

    async def _execute_quality_rule(
        self,
        rule: QualityRule,
        triples: List[Triple],
        ontology_ids: Optional[List[str]],
        user_id: Optional[str]
    ) -> List[QualityIssue]:
        """Ejecutar una regla de calidad."""
        issues = []

        try:
            if rule.rule_type == QualityRuleType.DATA_INTEGRITY:
                issues = await self._check_data_integrity(rule, triples)
            elif rule.rule_type == QualityRuleType.LOGICAL_CONSISTENCY:
                issues = await self._check_logical_consistency(rule, triples)
            elif rule.rule_type == QualityRuleType.ONTOLOGY_COMPLIANCE:
                issues = await self._check_ontology_compliance(rule, triples, ontology_ids)
            elif rule.rule_type == QualityRuleType.INFERENCE_VALIDATION:
                issues = await self._check_inference_validation(rule, triples)

        except Exception as e:
            logger.warning(f"Error executing quality rule {rule.rule_id}: {e}")

        return issues

    async def _check_data_integrity(self, rule: QualityRule, triples: List[Triple]) -> List[QualityIssue]:
        """Verificar integridad de datos."""
        issues = []
        import secrets

        # Verificar propiedades requeridas
        required_props = rule.parameters.get("required_properties", [])
        entity_types = rule.parameters.get("entity_types", [])

        if required_props:
            # Agrupar triples por sujeto
            subjects = defaultdict(list)
            for triple in triples:
                subjects[triple.subject].append(triple)

            for subject, subject_triples in subjects.items():
                # Verificar si es un tipo de entidad relevante
                has_relevant_type = any(
                    t.predicate == "rdf:type" and t.object in entity_types
                    for t in subject_triples
                ) if entity_types else True

                if has_relevant_type:
                    for required_prop in required_props:
                        has_property = any(t.predicate == required_prop for t in subject_triples)
                        if not has_property:
                            issues.append(QualityIssue(
                                issue_id=secrets.token_hex(4),
                                rule_id=rule.rule_id,
                                severity=rule.severity,
                                title=f"Missing required property: {required_prop}",
                                description=f"Entity {subject} is missing required property {required_prop}",
                                affected_triples=subject_triples,
                                suggested_fix=f"Add triple: {subject} {required_prop} <value>"
                            ))

        return issues

    async def _check_logical_consistency(self, rule: QualityRule, triples: List[Triple]) -> List[QualityIssue]:
        """Verificar consistencia lógica."""
        issues = []
        import secrets

        # Verificar referencias a entidades inexistentes
        entities = set()
        for triple in triples:
            entities.add(triple.subject)
            # Solo agregar objetos si parecen URIs
            if isinstance(triple.object, str) and (triple.object.startswith('http') or ':' in triple.object):
                entities.add(triple.object)

        for triple in triples:
            if triple.object in entities and triple.object not in entities:
                issues.append(QualityIssue(
                    issue_id=secrets.token_hex(4),
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    title="Reference to non-existent entity",
                    description=f"Triple references entity {triple.object} which does not exist",
                    affected_triples=[triple],
                    suggested_fix=f"Create entity {triple.object} or correct the reference"
                ))

        return issues

    async def _check_ontology_compliance(
        self,
        rule: QualityRule,
        triples: List[Triple],
        ontology_ids: Optional[List[str]]
    ) -> List[QualityIssue]:
        """Verificar cumplimiento ontológico."""
        issues = []

        if not ontology_ids:
            return issues

        # Usar OntologyManager para validación
        data_dict = {}
        for triple in triples:
            if triple.subject not in data_dict:
                data_dict[triple.subject] = {}
            data_dict[triple.subject][triple.predicate] = triple.object

        validation_result = await self.ontology_manager.validate_schema(data_dict, ontology_ids)

        if not validation_result['valid']:
            import secrets
            for error in validation_result['errors']:
                issues.append(QualityIssue(
                    issue_id=secrets.token_hex(4),
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    title="Ontology validation error",
                    description=error,
                    affected_triples=[],  # Podría mapear a triples específicos
                    suggested_fix="Review and correct the data according to ontology constraints"
                ))

        return issues

    async def _check_inference_validation(self, rule: QualityRule, triples: List[Triple]) -> List[QualityIssue]:
        """Verificar validación de inferencias."""
        issues = []

        # Ejecutar inferencia para verificar consistencia
        max_depth = rule.parameters.get("max_inference_depth", 3)
        inference_result = await self.inference_engine.infer(max_depth=max_depth)

        # Verificar conflictos con hechos existentes
        if rule.parameters.get("check_conflicts", True):
            existing_facts = {(t.subject, t.predicate, t.object) for t in triples}
            for inferred_triple in inference_result.inferred_triples:
                fact_tuple = (inferred_triple.subject, inferred_triple.predicate, inferred_triple.object)
                if fact_tuple in existing_facts:
                    # Esto podría ser normal, pero verificar contradicciones
                    pass

        return issues

    async def _detect_broken_references(self, triples: List[Triple]) -> List[QualityIssue]:
        """Detectar referencias rotas."""
        issues = []
        import secrets

        # Crear conjunto de entidades existentes
        entities = set()
        for triple in triples:
            entities.add(triple.subject)
            if isinstance(triple.object, str) and (triple.object.startswith('http') or ':' in triple.object):
                entities.add(triple.object)

        for triple in triples:
            if triple.object not in entities:
                issues.append(QualityIssue(
                    issue_id=secrets.token_hex(4),
                    rule_id="consistency_entity_references",
                    severity=QualitySeverity.HIGH,
                    title="Broken entity reference",
                    description=f"Reference to non-existent entity: {triple.object}",
                    affected_triples=[triple],
                    suggested_fix=f"Create entity {triple.object} or remove this triple"
                ))

        return issues

    async def _detect_logical_conflicts(self, triples: List[Triple]) -> List[QualityIssue]:
        """Detectar conflictos lógicos."""
        issues = []
        import secrets

        # Verificar contradicciones simples (ej: A subclassOf B y B subclassOf A)
        subclass_relations = defaultdict(set)
        for triple in triples:
            if triple.predicate == "rdfs:subClassOf":
                subclass_relations[triple.subject].add(triple.object)

        for subject, parents in subclass_relations.items():
            for parent in parents:
                if subject in subclass_relations.get(parent, set()):
                    issues.append(QualityIssue(
                        issue_id=secrets.token_hex(4),
                        rule_id="logical_consistency_subclass_cycle",
                        severity=QualitySeverity.CRITICAL,
                        title="Subclass cycle detected",
                        description=f"Cycle in subclass hierarchy: {subject} -> {parent} -> {subject}",
                        affected_triples=[
                            t for t in triples
                            if (t.subject == subject and t.object == parent and t.predicate == "rdfs:subClassOf") or
                               (t.subject == parent and t.object == subject and t.predicate == "rdfs:subClassOf")
                        ],
                        suggested_fix="Remove one of the conflicting subclass relations"
                    ))

        return issues

    async def _detect_ontology_inconsistencies(
        self,
        triples: List[Triple],
        ontology_ids: List[str]
    ) -> List[QualityIssue]:
        """Detectar inconsistencias ontológicas."""
        # Usar OntologyManager para validación
        data_dict = {}
        for triple in triples:
            if triple.subject not in data_dict:
                data_dict[triple.subject] = {}
            data_dict[triple.subject][triple.predicate] = triple.object

        validation_result = await self.ontology_manager.validate_schema(data_dict, ontology_ids)

        issues = []
        import secrets

        for error in validation_result['errors']:
            issues.append(QualityIssue(
                issue_id=secrets.token_hex(4),
                rule_id="ontology_schema_validation",
                severity=QualitySeverity.HIGH,
                title="Ontology inconsistency",
                description=error,
                affected_triples=[],
                suggested_fix="Correct the data to comply with ontology constraints"
            ))

        return issues

    async def _detect_inference_inconsistencies(self, triples: List[Triple]) -> List[QualityIssue]:
        """Detectar inconsistencias de inferencia."""
        issues = []

        # Ejecutar inferencia y verificar si genera contradicciones
        inference_result = await self.inference_engine.infer()

        # Verificar si alguna inferencia contradice hechos existentes
        existing_facts = {(t.subject, t.predicate, t.object) for t in triples}
        contradictory_facts = {(t.subject, t.predicate, f"not_{t.object}") for t in triples}

        import secrets
        for inferred_triple in inference_result.inferred_triples:
            fact_tuple = (inferred_triple.subject, inferred_triple.predicate, inferred_triple.object)
            if fact_tuple in contradictory_facts:
                issues.append(QualityIssue(
                    issue_id=secrets.token_hex(4),
                    rule_id="inference_consistency_check",
                    severity=QualitySeverity.CRITICAL,
                    title="Inference contradiction",
                    description=f"Inferred fact contradicts existing data: {inferred_triple}",
                    affected_triples=[inferred_triple],
                    suggested_fix="Review the inference rules or correct the conflicting data"
                ))

        return issues

    def _calculate_quality_metrics(self, triples: List[Triple], issues: List[QualityIssue]) -> QualityMetrics:
        """Calcular métricas de calidad."""
        total_triples = len(triples)

        # Contar issues por severidad
        issues_by_severity = defaultdict(int)
        for issue in issues:
            issues_by_severity[issue.severity.value] += 1

        # Calcular scores (simplificado - en producción sería más complejo)
        base_score = 1.0 - (len(issues) / max(total_triples, 1))

        # Ajustar por severidad
        severity_penalty = {
            QualitySeverity.LOW.value: 0.1,
            QualitySeverity.MEDIUM.value: 0.3,
            QualitySeverity.HIGH.value: 0.6,
            QualitySeverity.CRITICAL.value: 1.0
        }

        total_penalty = sum(
            issues_by_severity[sev] * penalty
            for sev, penalty in severity_penalty.items()
        )

        adjusted_score = max(0.0, base_score - (total_penalty / max(total_triples, 1)))

        # Scores por métrica (simplificado)
        completeness_score = adjusted_score
        consistency_score = max(0.0, 1.0 - (issues_by_severity[QualitySeverity.CRITICAL.value] * 0.5))
        accuracy_score = adjusted_score
        timeliness_score = 0.8  # Placeholder
        validity_score = max(0.0, 1.0 - (issues_by_severity[QualitySeverity.HIGH.value] * 0.3))

        overall_score = (
            completeness_score * 0.2 +
            consistency_score * 0.3 +
            accuracy_score * 0.25 +
            timeliness_score * 0.15 +
            validity_score * 0.1
        )

        return QualityMetrics(
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            accuracy_score=accuracy_score,
            timeliness_score=timeliness_score,
            validity_score=validity_score,
            overall_score=overall_score,
            total_triples=total_triples,
            issues_count=len(issues),
            issues_by_severity=dict(issues_by_severity)
        )

    def _generate_recommendations(self, metrics: QualityMetrics, issues: List[QualityIssue]) -> List[str]:
        """Generar recomendaciones basadas en métricas e issues."""
        recommendations = []

        if metrics.overall_score < 0.7:
            recommendations.append("Overall quality score is low. Consider comprehensive data cleanup.")

        if metrics.consistency_score < 0.8:
            recommendations.append("Consistency issues detected. Review entity references and logical constraints.")

        if metrics.validity_score < 0.9:
            recommendations.append("Ontology compliance issues found. Validate data against schemas.")

        if metrics.completeness_score < 0.8:
            recommendations.append("Missing required properties. Complete entity definitions.")

        # Recomendaciones específicas por issues
        critical_issues = [i for i in issues if i.severity == QualitySeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately.")

        return recommendations

    def add_quality_rule(
        self,
        rule_id: str,
        rule_type: QualityRuleType,
        name: str,
        description: str,
        metric: QualityMetric,
        threshold: float,
        severity: QualitySeverity,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Agregar una regla de calidad personalizada."""
        if rule_id in self.quality_rules:
            return False

        rule = QualityRule(
            rule_id=rule_id,
            rule_type=rule_type,
            name=name,
            description=description,
            metric=metric,
            threshold=threshold,
            severity=severity,
            parameters=parameters or {}
        )

        self.quality_rules[rule_id] = rule
        logger.info(f"Added custom quality rule: {rule_id}")
        return True

    def get_quality_rules(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todas las reglas de calidad."""
        return {rule_id: rule.to_dict() for rule_id, rule in self.quality_rules.items()}

    def enable_rule(self, rule_id: str) -> bool:
        """Habilitar una regla de calidad."""
        if rule_id in self.quality_rules:
            self.quality_rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Deshabilitar una regla de calidad."""
        if rule_id in self.quality_rules:
            self.quality_rules[rule_id].enabled = False
            return True
        return False


# Instancia global
_quality_assurance = None


def get_quality_assurance() -> QualityAssurance:
    """Obtener instancia global del sistema de Quality Assurance."""
    global _quality_assurance
    if _quality_assurance is None:
        _quality_assurance = QualityAssurance()
    return _quality_assurance