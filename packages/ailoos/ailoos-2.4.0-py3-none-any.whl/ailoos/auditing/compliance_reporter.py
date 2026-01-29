"""
Generación automática de reportes de compliance para AILOOS.
Crea reportes periódicos y bajo demanda sobre el estado de compliance.
"""

import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available - PDF export disabled")
import threading
import os

from .blockchain_auditor import get_blockchain_auditor
from .hash_chain_manager import get_hash_chain_manager
from .audit_smart_contracts import get_smart_contract_manager
from .immutable_log_storage import get_immutable_log_storage
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ComplianceReport:
    """Reporte de compliance."""
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    total_operations: int
    compliant_operations: int
    compliance_rate: float
    violations: List[Dict[str, Any]]
    risk_assessments: Dict[str, Any]
    recommendations: List[str]
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


class ComplianceReporter:
    """
    Generador automático de reportes de compliance.
    Crea reportes periódicos y bajo demanda con métricas de compliance.
    """

    def __init__(self):
        self.reports_dir = os.path.join(os.getcwd(), "reports", "compliance")
        os.makedirs(self.reports_dir, exist_ok=True)
        self.lock = threading.Lock()

        logger.info("📊 ComplianceReporter initialized")

    def generate_compliance_report(self, report_type: str = "monthly",
                                  days: int = 30) -> ComplianceReport:
        """
        Genera un reporte de compliance.

        Args:
            report_type: Tipo de reporte ('daily', 'weekly', 'monthly', 'quarterly')
            days: Número de días a cubrir

        Returns:
            Reporte de compliance generado
        """
        with self.lock:
            # Calcular período
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            report_id = f"compliance_{report_type}_{int(end_date.timestamp())}"

            # Recopilar datos de todas las fuentes
            blockchain_data = self._gather_blockchain_data(start_date, end_date)
            hash_chain_data = self._gather_hash_chain_data(start_date, end_date)
            contract_data = self._gather_contract_data(start_date, end_date)
            storage_data = self._gather_storage_data(start_date, end_date)

            # Calcular métricas de compliance
            total_operations = blockchain_data["total_operations"]
            compliant_operations = blockchain_data["compliant_operations"]
            compliance_rate = (compliant_operations / total_operations * 100) if total_operations > 0 else 100

            # Identificar violaciones
            violations = self._identify_violations(blockchain_data, contract_data)

            # Evaluar riesgos
            risk_assessments = self._assess_risks(contract_data, days)

            # Generar recomendaciones
            recommendations = self._generate_recommendations(
                compliance_rate, violations, risk_assessments
            )

            # Compilar datos del reporte
            report_data = {
                "blockchain_metrics": blockchain_data,
                "hash_chain_integrity": hash_chain_data,
                "contract_executions": contract_data,
                "storage_stats": storage_data,
                "violation_details": violations,
                "risk_breakdown": risk_assessments
            }

            # Crear reporte
            report = ComplianceReport(
                report_id=report_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                generated_at=end_date,
                total_operations=total_operations,
                compliant_operations=compliant_operations,
                compliance_rate=round(compliance_rate, 2),
                violations=violations,
                risk_assessments=risk_assessments,
                recommendations=recommendations,
                data=report_data
            )

            logger.info("📋 Generated compliance report: %s (%.1f%% compliance)",
                       report_id, compliance_rate)

            return report

    def _gather_blockchain_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Recopila datos de la blockchain de auditoría."""
        auditor = get_blockchain_auditor()

        # Buscar operaciones en el período
        operations = auditor.search_operations({
            "date_from": start_date.timestamp(),
            "date_to": end_date.timestamp()
        })

        total_operations = len(operations)
        compliant_operations = 0
        operation_types = {}
        user_activity = {}

        for op in operations:
            # Contar tipos de operación
            op_type = op.get("operation_type", "unknown")
            operation_types[op_type] = operation_types.get(op_type, 0) + 1

            # Contar actividad por usuario
            user_id = op.get("user_id", "unknown")
            user_activity[user_id] = user_activity.get(user_id, 0) + 1

            # Verificar compliance
            compliance_flags = op.get("compliance_flags", [])
            if not any("violation" in flag.lower() for flag in compliance_flags):
                compliant_operations += 1

        return {
            "total_operations": total_operations,
            "compliant_operations": compliant_operations,
            "operation_types": operation_types,
            "user_activity": user_activity,
            "blockchain_integrity": auditor.validate_chain()
        }

    def _gather_hash_chain_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Recopila datos de integridad de hash chains."""
        manager = get_hash_chain_manager()

        integrity_status = manager.verify_all_chains()
        chain_info = manager.get_all_chains_info()

        # Contar entradas recientes por cadena
        recent_entries = {}
        for chain_id in chain_info.keys():
            entries = manager.search_entries(chain_id, {
                "timestamp_from": start_date.timestamp(),
                "timestamp_to": end_date.timestamp()
            })
            recent_entries[chain_id] = len(entries)

        return {
            "chains_integrity": integrity_status,
            "chains_info": chain_info,
            "recent_entries": recent_entries,
            "total_chains": len(chain_info)
        }

    def _gather_contract_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Recopila datos de ejecución de contratos inteligentes."""
        manager = get_smart_contract_manager()

        executions = manager.get_execution_history(limit=10000)
        recent_executions = [e for e in executions if e["timestamp"] >= start_date.timestamp()]

        contract_stats = {}
        for exec in recent_executions:
            contract_id = exec["contract_id"]
            if contract_id not in contract_stats:
                contract_stats[contract_id] = {
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_gas": 0
                }

            contract_stats[contract_id]["executions"] += 1
            contract_stats[contract_id]["total_gas"] += exec.get("gas_used", 0)

            if exec.get("success", False):
                contract_stats[contract_id]["successes"] += 1
            else:
                contract_stats[contract_id]["failures"] += 1

        return {
            "total_executions": len(recent_executions),
            "contract_stats": contract_stats,
            "success_rate": (sum(s["successes"] for s in contract_stats.values()) /
                           sum(s["executions"] for s in contract_stats.values()) * 100)
                           if contract_stats else 100
        }

    def _gather_storage_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Recopila datos del almacenamiento inmutable."""
        storage = get_immutable_log_storage()

        # Estadísticas generales
        stats = storage.get_storage_stats()

        # Logs en el período
        recent_logs = storage.search_logs({
            "date_from": start_date,
            "date_to": end_date
        }, limit=10000)

        # Verificación de integridad
        integrity_check = storage.verify_all_logs_integrity()

        return {
            "storage_stats": stats,
            "recent_logs": len(recent_logs),
            "integrity_check": integrity_check
        }

    def _identify_violations(self, blockchain_data: Dict, contract_data: Dict) -> List[Dict[str, Any]]:
        """Identifica violaciones de compliance."""
        violations = []

        # Violaciones de contratos
        for contract_id, stats in contract_data.get("contract_stats", {}).items():
            failure_rate = (stats["failures"] / stats["executions"] * 100) if stats["executions"] > 0 else 0
            if failure_rate > 10:  # Más del 10% de fallos
                violations.append({
                    "type": "contract_failure_rate",
                    "contract_id": contract_id,
                    "severity": "high" if failure_rate > 25 else "medium",
                    "description": f"High failure rate in {contract_id}: {failure_rate:.1f}%",
                    "failure_rate": failure_rate
                })

        # Violaciones de integridad de blockchain
        if not blockchain_data.get("blockchain_integrity", True):
            violations.append({
                "type": "blockchain_integrity",
                "severity": "critical",
                "description": "Blockchain integrity validation failed"
            })

        # Violaciones de integridad de logs
        integrity_check = contract_data.get("integrity_check", {})
        invalid_logs = integrity_check.get("invalid_logs", 0)
        if invalid_logs > 0:
            violations.append({
                "type": "log_integrity",
                "severity": "high",
                "description": f"{invalid_logs} logs with integrity violations",
                "invalid_count": invalid_logs
            })

        return violations

    def _assess_risks(self, contract_data: Dict, days: int) -> Dict[str, Any]:
        """Evalúa riesgos basados en datos de contratos."""
        # Obtener evaluaciones de riesgo del contrato de riesgo
        manager = get_smart_contract_manager()
        risk_executions = manager.get_execution_history("risk_assessor", limit=1000)

        # Filtrar por período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        recent_risks = [e for e in risk_executions if e["timestamp"] >= start_date.timestamp()]

        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0, "minimal": 0}
        total_risk_score = 0

        for exec in recent_risks:
            result = exec.get("result", {})
            level = result.get("risk_level", "unknown")
            score = result.get("risk_score", 0)

            if level in risk_levels:
                risk_levels[level] += 1
            total_risk_score += score

        avg_risk_score = total_risk_score / len(recent_risks) if recent_risks else 0

        return {
            "total_assessments": len(recent_risks),
            "average_risk_score": round(avg_risk_score, 2),
            "risk_distribution": risk_levels,
            "high_risk_operations": risk_levels.get("critical", 0) + risk_levels.get("high", 0)
        }

    def _generate_recommendations(self, compliance_rate: float, violations: List[Dict],
                                risk_assessments: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []

        # Recomendaciones basadas en tasa de compliance
        if compliance_rate < 80:
            recommendations.append("Implement additional automated compliance checks")
        if compliance_rate < 60:
            recommendations.append("URGENT: Review and strengthen compliance policies")

        # Recomendaciones basadas en violaciones
        for violation in violations:
            if violation["type"] == "contract_failure_rate":
                recommendations.append(f"Investigate high failure rate in contract {violation['contract_id']}")
            elif violation["type"] == "blockchain_integrity":
                recommendations.append("CRITICAL: Restore blockchain integrity immediately")
            elif violation["type"] == "log_integrity":
                recommendations.append("Review log storage integrity and backup procedures")

        # Recomendaciones basadas en riesgos
        high_risk_count = risk_assessments.get("high_risk_operations", 0)
        if high_risk_count > 10:
            recommendations.append("Implement additional risk mitigation measures")
        if high_risk_count > 50:
            recommendations.append("URGENT: Comprehensive risk assessment required")

        # Recomendaciones generales
        if not recommendations:
            recommendations.append("Compliance status is satisfactory - continue monitoring")

        return recommendations

    def export_report_pdf(self, report: ComplianceReport, filename: Optional[str] = None) -> str:
        """
        Exporta reporte a PDF.

        Args:
            report: Reporte a exportar
            filename: Nombre del archivo (opcional)

        Returns:
            Ruta del archivo generado
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export")

        if not filename:
            filename = f"compliance_report_{report.report_id}.pdf"

        filepath = os.path.join(self.reports_dir, filename)

        # Crear documento PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
        )
        story.append(Paragraph(f"Compliance Report - {report.report_type.title()}", title_style))
        story.append(Spacer(1, 12))

        # Información básica
        story.append(Paragraph(f"Report ID: {report.report_id}", styles['Normal']))
        story.append(Paragraph(f"Period: {report.period_start.date()} to {report.period_end.date()}", styles['Normal']))
        story.append(Paragraph(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Métricas principales
        story.append(Paragraph("Compliance Metrics", styles['Heading2']))
        metrics_data = [
            ["Metric", "Value"],
            ["Total Operations", str(report.total_operations)],
            ["Compliant Operations", str(report.compliant_operations)],
            ["Compliance Rate", f"{report.compliance_rate}%"],
        ]

        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))

        # Violaciones
        if report.violations:
            story.append(Paragraph("Compliance Violations", styles['Heading2']))
            for violation in report.violations:
                story.append(Paragraph(f"• {violation['description']} (Severity: {violation['severity']})", styles['Normal']))
            story.append(Spacer(1, 20))

        # Recomendaciones
        story.append(Paragraph("Recommendations", styles['Heading2']))
        for rec in report.recommendations:
            story.append(Paragraph(f"• {rec}", styles['Normal']))

        # Generar PDF
        doc.build(story)

        logger.info(f"📄 Exported compliance report to PDF: {filepath}")

        return filepath

    def export_report_json(self, report: ComplianceReport, filename: Optional[str] = None) -> str:
        """
        Exporta reporte a JSON.

        Args:
            report: Reporte a exportar
            filename: Nombre del archivo (opcional)

        Returns:
            Ruta del archivo generado
        """
        if not filename:
            filename = f"compliance_report_{report.report_id}.json"

        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)

        logger.info(f"📄 Exported compliance report to JSON: {filepath}")

        return filepath

    def export_report_csv(self, report: ComplianceReport, filename: Optional[str] = None) -> str:
        """
        Exporta datos del reporte a CSV.

        Args:
            report: Reporte a exportar
            filename: Nombre del archivo (opcional)

        Returns:
            Ruta del archivo generado
        """
        if not filename:
            filename = f"compliance_data_{report.report_id}.csv"

        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Cabeceras
            writer.writerow(["Metric", "Value"])

            # Datos principales
            writer.writerow(["Report ID", report.report_id])
            writer.writerow(["Report Type", report.report_type])
            writer.writerow(["Period Start", report.period_start.isoformat()])
            writer.writerow(["Period End", report.period_end.isoformat()])
            writer.writerow(["Total Operations", report.total_operations])
            writer.writerow(["Compliant Operations", report.compliant_operations])
            writer.writerow(["Compliance Rate", f"{report.compliance_rate}%"])

            # Violaciones
            writer.writerow([])
            writer.writerow(["Violations"])
            for violation in report.violations:
                writer.writerow([violation.get("description", ""), violation.get("severity", "")])

            # Recomendaciones
            writer.writerow([])
            writer.writerow(["Recommendations"])
            for rec in report.recommendations:
                writer.writerow([rec])

        logger.info("📄 Exported compliance data to CSV: %s", filepath)

        return filepath

    def schedule_automatic_reports(self, interval_days: int = 7):
        """
        Programa generación automática de reportes.

        Args:
            interval_days: Intervalo en días entre reportes
        """
        def report_task():
            while True:
                try:
                    # Generar reporte semanal
                    report = self.generate_compliance_report("weekly", 7)

                    # Exportar en múltiples formatos
                    self.export_report_pdf(report)
                    self.export_report_json(report)

                    logger.info("✅ Automatic compliance report generated")

                except Exception as e:
                    logger.error("Error generating automatic report: %s", e)

                # Esperar al próximo intervalo
                import time
                time.sleep(interval_days * 24 * 60 * 60)

        # Iniciar tarea en background
        thread = threading.Thread(target=report_task, daemon=True)
        thread.start()

        logger.info(f"⏰ Scheduled automatic compliance reports every {interval_days} days")


# Instancia global del generador de reportes
compliance_reporter = ComplianceReporter()


def get_compliance_reporter() -> ComplianceReporter:
    """Obtiene instancia global del generador de reportes."""
    return compliance_reporter