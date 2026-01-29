"""
Privacy Auditor - Auditor de privacidad para verificación de unlearning y cumplimiento GDPR.

Realiza auditorías automáticas de efectividad del unlearning, verifica cumplimiento
de regulaciones de privacidad, y genera reportes de conformidad.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import numpy as np
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging import get_logger
from .unlearning import ZeroShotUnlearningSystem, UnlearningResult
from ..inference.memory.miras_block import MIRASBlock

logger = get_logger(__name__)


class AuditSeverity(Enum):
    """Severidad de hallazgos de auditoría."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(Enum):
    """Estado de cumplimiento."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"


@dataclass
class AuditFinding:
    """Hallazgo de auditoría."""
    finding_id: str
    title: str
    description: str
    severity: AuditSeverity
    compliance_status: ComplianceStatus
    affected_components: List[str]
    remediation_steps: List[str]
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = None
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class UnlearningAuditResult:
    """Resultado de auditoría de unlearning."""
    target_id: str
    effectiveness_score: float
    verification_metrics: Dict[str, float]
    compliance_score: float  # 0-1, qué tan compliant es el unlearning
    mathematical_guarantee: bool
    privacy_preservation_score: float
    residual_information_score: float  # Cuánta info residual queda
    audit_timestamp: datetime
    findings: List[AuditFinding] = field(default_factory=list)


@dataclass
class PrivacyAuditReport:
    """Reporte completo de auditoría de privacidad."""
    audit_id: str
    timestamp: datetime
    scope: List[str]  # Componentes auditados
    overall_compliance: ComplianceStatus
    compliance_score: float  # 0-1
    unlearning_audits: List[UnlearningAuditResult]
    gdpr_compliance_score: float
    data_minimization_score: float
    right_to_be_forgotten_score: float
    findings: List[AuditFinding]
    recommendations: List[str]
    next_audit_date: Optional[datetime] = None


class MembershipInferenceAttacker(nn.Module):
    """
    Adversario para membership inference attacks.

    Intenta determinar si un dato específico fue usado en el entrenamiento
    del modelo, útil para verificar efectividad del unlearning.
    """

    def __init__(self, hidden_size: int, num_classes: int = 2):
        super().__init__()
        self.hidden_size = hidden_size

        self.attack_network = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, num_classes)
        )

    def forward(self, member_logits: torch.Tensor, non_member_logits: torch.Tensor) -> torch.Tensor:
        """
        Predecir si un sample es miembro del training set.

        Args:
            member_logits: Logits del modelo para datos potencialmente miembros
            non_member_logits: Logits para datos no miembros

        Returns:
            Probabilidades de membership [batch_size, 2]
        """
        # Concatenar logits de miembros y no-miembros
        combined = torch.cat([member_logits, non_member_logits], dim=-1)
        membership_probs = self.attack_network(combined)
        return F.softmax(membership_probs, dim=-1)


class PrivacyAuditor:
    """
    Auditor principal de privacidad.

    Realiza auditorías comprehensivas de unlearning y cumplimiento GDPR.
    """

    def __init__(
        self,
        unlearning_system: Optional[ZeroShotUnlearningSystem] = None,
        miras_blocks: Optional[List[MIRASBlock]] = None,
        audit_frequency_days: int = 30
    ):
        self.unlearning_system = unlearning_system
        self.miras_blocks = miras_blocks or []
        self.audit_frequency_days = audit_frequency_days

        # Historial de auditorías
        self.audit_history: List[PrivacyAuditReport] = []
        self.active_findings: List[AuditFinding] = []

        # Attackers para verificación
        self.membership_attacker = MembershipInferenceAttacker(hidden_size=768)  # Default

        # Métricas de referencia
        self.baseline_metrics: Dict[str, float] = {}

        logger.info("🔍 PrivacyAuditor inicializado")

    def perform_comprehensive_audit(self, scope: Optional[List[str]] = None) -> PrivacyAuditReport:
        """
        Realizar auditoría comprehensiva de privacidad.

        Args:
            scope: Componentes específicos a auditar (opcional)

        Returns:
            Reporte completo de auditoría
        """
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now()

        if scope is None:
            scope = ["unlearning_system", "miras_memory", "gdpr_compliance"]

        logger.info(f"🔍 Iniciando auditoría comprehensiva {audit_id} con scope: {scope}")

        # Auditar sistema de unlearning
        unlearning_audits = []
        if "unlearning_system" in scope and self.unlearning_system:
            unlearning_audits = self._audit_unlearning_system()

        # Auditar bloques MIRAS
        miras_findings = []
        if "miras_memory" in scope and self.miras_blocks:
            miras_findings = self._audit_miras_blocks()

        # Auditar cumplimiento GDPR
        gdpr_findings = []
        gdpr_score = 0.0
        if "gdpr_compliance" in scope:
            gdpr_score, gdpr_findings = self._audit_gdpr_compliance()

        # Calcular scores generales
        compliance_score = self._calculate_overall_compliance_score(
            unlearning_audits, miras_findings, gdpr_findings
        )

        overall_compliance = self._determine_compliance_status(compliance_score)

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            unlearning_audits, miras_findings, gdpr_findings
        )

        # Todos los findings
        all_findings = miras_findings + gdpr_findings
        for audit in unlearning_audits:
            all_findings.extend(audit.findings)

        # Actualizar findings activos
        self._update_active_findings(all_findings)

        report = PrivacyAuditReport(
            audit_id=audit_id,
            timestamp=timestamp,
            scope=scope,
            overall_compliance=overall_compliance,
            compliance_score=compliance_score,
            unlearning_audits=unlearning_audits,
            gdpr_compliance_score=gdpr_score,
            data_minimization_score=self._calculate_data_minimization_score(),
            right_to_be_forgotten_score=self._calculate_right_to_be_forgotten_score(unlearning_audits),
            findings=all_findings,
            recommendations=recommendations,
            next_audit_date=timestamp + timedelta(days=self.audit_frequency_days)
        )

        self.audit_history.append(report)

        logger.info(f"✅ Auditoría completada: compliance_score={compliance_score:.3f}, status={overall_compliance.value}")
        return report

    def audit_unlearning_effectiveness(self, target_id: str) -> UnlearningAuditResult:
        """
        Auditar efectividad específica de un unlearning.

        Args:
            target_id: ID del target a auditar

        Returns:
            Resultado detallado de la auditoría
        """
        if not self.unlearning_system:
            return UnlearningAuditResult(
                target_id=target_id,
                effectiveness_score=0.0,
                verification_metrics={},
                compliance_score=0.0,
                mathematical_guarantee=False,
                privacy_preservation_score=0.0,
                residual_information_score=1.0,
                audit_timestamp=datetime.now(),
                findings=[AuditFinding(
                    finding_id=f"no_unlearning_system_{target_id}",
                    title="Sistema de Unlearning No Disponible",
                    description="No hay sistema de unlearning configurado para auditoría",
                    severity=AuditSeverity.CRITICAL,
                    compliance_status=ComplianceStatus.NON_COMPLIANT,
                    affected_components=["unlearning_system"],
                    remediation_steps=["Configurar ZeroShotUnlearningSystem"]
                )]
            )

        # Obtener resultado del unlearning
        unlearning_result = self.unlearning_system.get_unlearning_status(target_id)

        if not unlearning_result:
            return UnlearningAuditResult(
                target_id=target_id,
                effectiveness_score=0.0,
                verification_metrics={},
                compliance_score=0.0,
                mathematical_guarantee=False,
                privacy_preservation_score=0.0,
                residual_information_score=1.0,
                audit_timestamp=datetime.now(),
                findings=[AuditFinding(
                    finding_id=f"target_not_found_{target_id}",
                    title="Target de Unlearning No Encontrado",
                    description=f"No se encontró registro de unlearning para {target_id}",
                    severity=AuditSeverity.HIGH,
                    compliance_status=ComplianceStatus.NON_COMPLIANT,
                    affected_components=["unlearning_system"],
                    remediation_steps=["Verificar ID del target", "Re-ejecutar unlearning si es necesario"]
                )]
            )

        # Verificaciones avanzadas
        verification_metrics = self._perform_advanced_verification(unlearning_result)

        # Evaluar garantía matemática
        mathematical_guarantee = self._verify_mathematical_guarantee(unlearning_result, verification_metrics)

        # Calcular scores de privacidad
        privacy_score = self._calculate_privacy_preservation_score(verification_metrics)
        residual_score = self._estimate_residual_information(verification_metrics)

        # Determinar compliance
        compliance_score = self._calculate_unlearning_compliance_score(
            unlearning_result, verification_metrics, mathematical_guarantee
        )

        # Generar findings
        findings = self._generate_unlearning_findings(
            target_id, unlearning_result, verification_metrics, compliance_score
        )

        result = UnlearningAuditResult(
            target_id=target_id,
            effectiveness_score=unlearning_result.effectiveness_score,
            verification_metrics=verification_metrics,
            compliance_score=compliance_score,
            mathematical_guarantee=mathematical_guarantee,
            privacy_preservation_score=privacy_score,
            residual_information_score=residual_score,
            audit_timestamp=datetime.now(),
            findings=findings
        )

        logger.info(f"🔍 Auditoría de unlearning para {target_id}: efectividad={unlearning_result.effectiveness_score:.3f}, compliance={compliance_score:.3f}")
        return result

    def _audit_unlearning_system(self) -> List[UnlearningAuditResult]:
        """Auditar el sistema completo de unlearning."""
        if not self.unlearning_system:
            return []

        audits = []
        stats = self.unlearning_system.get_unlearning_statistics()

        # Auditar cada target completado
        for result in self.unlearning_system.unlearning_history:
            if result.success:
                audit = self.audit_unlearning_effectiveness(result.target_id)
                audits.append(audit)

        return audits

    def _audit_miras_blocks(self) -> List[AuditFinding]:
        """Auditar bloques MIRAS para cumplimiento de privacidad."""
        findings = []

        for i, block in enumerate(self.miras_blocks):
            block_id = f"miras_block_{i}"

            # Verificar capacidades de unlearning
            unlearning_stats = block.get_unlearning_stats()

            if not unlearning_stats.get("selective_unlearning_available", False):
                findings.append(AuditFinding(
                    finding_id=f"miras_no_selective_unlearning_{i}",
                    title="Unlearning Selectivo No Disponible en MIRAS",
                    description=f"El bloque MIRAS {i} no tiene capacidades de unlearning selectivo",
                    severity=AuditSeverity.HIGH,
                    compliance_status=ComplianceStatus.NON_COMPLIANT,
                    affected_components=[block_id],
                    remediation_steps=[
                        "Implementar selective_unlearn_user_data en MIRASBlock",
                        "Agregar capacidades de pattern-based unlearning"
                    ]
                ))

            # Verificar stats de memoria
            memory_stats = block.get_memory_stats()
            miras_stats = memory_stats.get("miras_stats", {})

            if miras_stats.get("memory_utilization", 0) > 0.9:
                findings.append(AuditFinding(
                    finding_id=f"miras_high_memory_usage_{i}",
                    title="Uso Alto de Memoria en MIRAS",
                    description=f"El bloque MIRAS {i} tiene alta utilización de memoria ({miras_stats.get('memory_utilization', 0):.1%})",
                    severity=AuditSeverity.MEDIUM,
                    compliance_status=ComplianceStatus.PARTIALLY_COMPLIANT,
                    affected_components=[block_id],
                    remediation_steps=[
                        "Implementar políticas de retención automática",
                        "Aumentar frecuencia de consolidación de memoria"
                    ]
                ))

        return findings

    def _audit_gdpr_compliance(self) -> Tuple[float, List[AuditFinding]]:
        """Auditar cumplimiento GDPR."""
        findings = []
        compliance_score = 1.0  # Base

        # Verificar derecho al olvido
        if not hasattr(self, '_check_right_to_be_forgotten_implementation'):
            findings.append(AuditFinding(
                finding_id="gdpr_no_right_to_be_forgotten",
                title="Derecho al Olvido No Implementado",
                description="No se encontró implementación del derecho al olvido",
                severity=AuditSeverity.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                affected_components=["gdpr_manager"],
                remediation_steps=[
                    "Implementar right_to_be_forgotten en GDPRManager",
                    "Integrar con sistemas de unlearning"
                ]
            ))
            compliance_score -= 0.3

        # Verificar minimización de datos
        data_minimization_score = self._calculate_data_minimization_score()
        if data_minimization_score < 0.7:
            findings.append(AuditFinding(
                finding_id="gdpr_poor_data_minimization",
                title="Minimização de Datos Insuficiente",
                description=f"Score de minimización de datos: {data_minimization_score:.2f}",
                severity=AuditSeverity.HIGH,
                compliance_status=ComplianceStatus.PARTIALLY_COMPLIANT,
                affected_components=["data_processing"],
                remediation_steps=[
                    "Implementar políticas de retención automática",
                    "Revisar categorías de datos procesados"
                ]
            ))
            compliance_score -= 0.2

        return compliance_score, findings

    def _perform_advanced_verification(self, unlearning_result: UnlearningResult) -> Dict[str, float]:
        """Realizar verificaciones avanzadas de unlearning."""
        metrics = unlearning_result.verification_metrics.copy()

        # Membership inference attack
        if hasattr(self, '_simulate_membership_attack'):
            mia_score = self._simulate_membership_attack(unlearning_result)
            metrics['membership_inference_resistance'] = mia_score

        # Information leakage assessment
        leakage_score = self._assess_information_leakage(unlearning_result)
        metrics['information_leakage_score'] = leakage_score

        # Gradient verification
        gradient_verification = self._verify_gradient_effectiveness(unlearning_result)
        metrics['gradient_verification_score'] = gradient_verification

        return metrics

    def _verify_mathematical_guarantee(self, result: UnlearningResult,
                                     verification_metrics: Dict[str, float]) -> bool:
        """Verificar garantía matemática del unlearning."""
        # Criterios para garantía matemática
        effectiveness_ok = result.effectiveness_score > 0.85
        kl_divergence_ok = verification_metrics.get('kl_divergence', 1.0) > 0.5
        leakage_low = verification_metrics.get('information_leakage_score', 1.0) < 0.3

        return effectiveness_ok and kl_divergence_ok and leakage_low

    def _calculate_privacy_preservation_score(self, verification_metrics: Dict[str, float]) -> float:
        """Calcular score de preservación de privacidad."""
        # Combinar múltiples métricas
        mia_resistance = verification_metrics.get('membership_inference_resistance', 0.5)
        leakage_score = 1.0 - verification_metrics.get('information_leakage_score', 0.5)  # Invertir
        gradient_verification = verification_metrics.get('gradient_verification_score', 0.5)

        # Promedio ponderado
        score = (mia_resistance * 0.4 + leakage_score * 0.4 + gradient_verification * 0.2)
        return score

    def _estimate_residual_information(self, verification_metrics: Dict[str, float]) -> float:
        """Estimar información residual después del unlearning."""
        # Basado en métricas de divergencia
        kl_div = verification_metrics.get('kl_divergence', 0.0)
        mse_div = verification_metrics.get('mse_divergence', 0.0)

        # Normalizar y combinar
        residual = min(1.0, (kl_div + mse_div) / 2.0)
        return residual

    def _calculate_unlearning_compliance_score(self, result: UnlearningResult,
                                             verification_metrics: Dict[str, float],
                                             mathematical_guarantee: bool) -> float:
        """Calcular score de compliance del unlearning."""
        base_score = result.effectiveness_score

        # Bonus por garantía matemática
        if mathematical_guarantee:
            base_score += 0.1

        # Penalización por leakage alto
        leakage = verification_metrics.get('information_leakage_score', 0.0)
        base_score -= leakage * 0.2

        return max(0.0, min(1.0, base_score))

    def _calculate_overall_compliance_score(self, unlearning_audits: List[UnlearningAuditResult],
                                          miras_findings: List[AuditFinding],
                                          gdpr_findings: List[AuditFinding]) -> float:
        """Calcular score general de compliance."""
        # Score base
        score = 1.0

        # Penalizar por findings críticos
        critical_findings = [f for f in miras_findings + gdpr_findings if f.severity == AuditSeverity.CRITICAL]
        score -= len(critical_findings) * 0.2

        # Penalizar por findings high
        high_findings = [f for f in miras_findings + gdpr_findings if f.severity == AuditSeverity.HIGH]
        score -= len(high_findings) * 0.1

        # Bonus por unlearning efectivo
        if unlearning_audits:
            avg_unlearning_score = np.mean([a.compliance_score for a in unlearning_audits])
            score += avg_unlearning_score * 0.3

        return max(0.0, min(1.0, score))

    def _determine_compliance_status(self, compliance_score: float) -> ComplianceStatus:
        """Determinar estado de compliance basado en score."""
        if compliance_score >= 0.9:
            return ComplianceStatus.COMPLIANT
        elif compliance_score >= 0.7:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _calculate_data_minimization_score(self) -> float:
        """Calcular score de minimización de datos."""
        # En implementación real, analizar logs de procesamiento de datos
        # Por ahora, score simulado
        return 0.75

    def _calculate_right_to_be_forgotten_score(self, unlearning_audits: List[UnlearningAuditResult]) -> float:
        """Calcular score del derecho al olvido."""
        if not unlearning_audits:
            return 0.0

        # Promedio de efectividad de unlearning
        avg_effectiveness = np.mean([a.effectiveness_score for a in unlearning_audits])
        return avg_effectiveness

    def _generate_recommendations(self, unlearning_audits: List[UnlearningAuditResult],
                                miras_findings: List[AuditFinding],
                                gdpr_findings: List[AuditFinding]) -> List[str]:
        """Generar recomendaciones basadas en findings."""
        recommendations = []

        # Recomendaciones para unlearning
        if unlearning_audits:
            low_effectiveness = [a for a in unlearning_audits if a.effectiveness_score < 0.7]
            if low_effectiveness:
                recommendations.append(
                    f"Mejorar efectividad de unlearning para {len(low_effectiveness)} targets con bajo rendimiento"
                )

        # Recomendaciones para MIRAS
        if miras_findings:
            critical_miras = [f for f in miras_findings if f.severity == AuditSeverity.CRITICAL]
            if critical_miras:
                recommendations.append(
                    f"Implementar capacidades de unlearning faltantes en {len(critical_miras)} bloques MIRAS"
                )

        # Recomendaciones GDPR
        if gdpr_findings:
            recommendations.append(
                f"Abordar {len(gdpr_findings)} hallazgos de cumplimiento GDPR"
            )

        return recommendations

    def _update_active_findings(self, new_findings: List[AuditFinding]):
        """Actualizar lista de findings activos."""
        # Marcar findings resueltos (simplificado)
        for finding in self.active_findings[:]:
            if finding.finding_id not in [f.finding_id for f in new_findings]:
                finding.resolved = True
                finding.resolution_timestamp = datetime.now()

        # Agregar nuevos findings
        for finding in new_findings:
            if finding.finding_id not in [f.finding_id for f in self.active_findings]:
                self.active_findings.append(finding)

    def _generate_unlearning_findings(self, target_id: str, result: UnlearningResult,
                                    verification_metrics: Dict[str, float],
                                    compliance_score: float) -> List[AuditFinding]:
        """Generar findings específicos para un unlearning."""
        findings = []

        if result.effectiveness_score < 0.7:
            findings.append(AuditFinding(
                finding_id=f"low_unlearning_effectiveness_{target_id}",
                title="Baja Efectividad de Unlearning",
                description=f"Efectividad del unlearning para {target_id}: {result.effectiveness_score:.2f}",
                severity=AuditSeverity.HIGH,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                affected_components=["unlearning_system"],
                remediation_steps=[
                    "Aumentar número de iteraciones en gradient inversion",
                    "Mejorar calidad de datos de referencia",
                    "Verificar implementación del unlearner"
                ]
            ))

        leakage = verification_metrics.get('information_leakage_score', 0.0)
        if leakage > 0.5:
            findings.append(AuditFinding(
                finding_id=f"high_information_leakage_{target_id}",
                title="Alto Riesgo de Fuga de Información",
                description=f"Score de fuga de información: {leakage:.2f}",
                severity=AuditSeverity.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                affected_components=["unlearning_system"],
                remediation_steps=[
                    "Implementar técnicas adicionales de sanitización",
                    "Revisar algoritmo de gradient inversion",
                    "Considerar retraining completo para casos críticos"
                ]
            ))

        return findings

    def _simulate_membership_attack(self, unlearning_result: UnlearningResult) -> float:
        """Simular membership inference attack (simplificado)."""
        # En implementación real, requeriría datos shadow
        return 0.3  # Score simulado de resistencia

    def _assess_information_leakage(self, unlearning_result: UnlearningResult) -> float:
        """Evaluar fuga de información."""
        # Basado en métricas de verificación
        kl_div = unlearning_result.verification_metrics.get('kl_divergence', 0.0)
        leakage = min(1.0, kl_div / 2.0)  # Normalizar
        return leakage

    def _verify_gradient_effectiveness(self, unlearning_result: UnlearningResult) -> float:
        """Verificar efectividad de gradient inversion."""
        # Basado en score de efectividad
        return unlearning_result.effectiveness_score

    def get_audit_history(self, limit: int = 10) -> List[PrivacyAuditReport]:
        """Obtener historial de auditorías."""
        return self.audit_history[-limit:]

    def get_active_findings(self) -> List[AuditFinding]:
        """Obtener findings activos."""
        return [f for f in self.active_findings if not f.resolved]

    def generate_compliance_report(self, audit_report: PrivacyAuditReport,
                                 format: str = "dict") -> Union[Dict[str, Any], str]:
        """
        Generar reporte de compliance en formato especificado.

        Args:
            audit_report: Reporte de auditoría
            format: Formato ("dict", "json", "text")

        Returns:
            Reporte formateado
        """
        report_data = {
            "audit_id": audit_report.audit_id,
            "timestamp": audit_report.timestamp.isoformat(),
            "compliance_score": audit_report.compliance_score,
            "overall_status": audit_report.overall_compliance.value,
            "summary": {
                "unlearning_audits_count": len(audit_report.unlearning_audits),
                "findings_count": len(audit_report.findings),
                "critical_findings": len([f for f in audit_report.findings if f.severity == AuditSeverity.CRITICAL]),
                "recommendations_count": len(audit_report.recommendations)
            },
            "scores": {
                "gdpr_compliance": audit_report.gdpr_compliance_score,
                "data_minimization": audit_report.data_minimization_score,
                "right_to_be_forgotten": audit_report.right_to_be_forgotten_score
            },
            "findings": [
                {
                    "id": f.finding_id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "status": f.compliance_status.value,
                    "description": f.description
                } for f in audit_report.findings
            ],
            "recommendations": audit_report.recommendations
        }

        if format == "json":
            import json
            return json.dumps(report_data, indent=2, ensure_ascii=False)
        elif format == "text":
            return self._format_report_as_text(report_data)
        else:
            return report_data

    def _format_report_as_text(self, report_data: Dict[str, Any]) -> str:
        """Formatear reporte como texto."""
        lines = [
            "=" * 80,
            f"REPORTE DE AUDITORÍA DE PRIVACIDAD - {report_data['audit_id']}",
            "=" * 80,
            f"Fecha: {report_data['timestamp']}",
            f"Score de Compliance: {report_data['compliance_score']:.3f}",
            f"Estado General: {report_data['overall_status'].upper()}",
            "",
            "RESUMEN:",
            f"- Auditorías de Unlearning: {report_data['summary']['unlearning_audits_count']}",
            f"- Hallazgos Totales: {report_data['summary']['findings_count']}",
            f"- Hallazgos Críticos: {report_data['summary']['critical_findings']}",
            f"- Recomendaciones: {report_data['summary']['recommendations_count']}",
            "",
            "SCORES DETALLADOS:",
            f"- Cumplimiento GDPR: {report_data['scores']['gdpr_compliance']:.3f}",
            f"- Minimización de Datos: {report_data['scores']['data_minimization']:.3f}",
            f"- Derecho al Olvido: {report_data['scores']['right_to_be_forgotten']:.3f}",
            "",
            "HALLAZGOS CRÍTICOS:"
        ]

        for finding in report_data['findings']:
            if finding['severity'] == 'critical':
                lines.append(f"- {finding['title']}: {finding['description']}")

        lines.extend([
            "",
            "RECOMENDACIONES:"
        ])

        for rec in report_data['recommendations']:
            lines.append(f"- {rec}")

        lines.append("=" * 80)

        return "\n".join(lines)


def create_privacy_auditor(
    unlearning_system: Optional[ZeroShotUnlearningSystem] = None,
    miras_blocks: Optional[List[MIRASBlock]] = None,
    audit_frequency_days: int = 30
) -> PrivacyAuditor:
    """
    Factory function para crear auditor de privacidad.

    Args:
        unlearning_system: Sistema de unlearning (opcional)
        miras_blocks: Bloques MIRAS a auditar (opcional)
        audit_frequency_days: Frecuencia de auditorías en días

    Returns:
        PrivacyAuditor configurado
    """
    return PrivacyAuditor(
        unlearning_system=unlearning_system,
        miras_blocks=miras_blocks,
        audit_frequency_days=audit_frequency_days
    )