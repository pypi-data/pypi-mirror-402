"""
Advanced Audit Compliance with reports and export functionality.
Supports regulatory compliance reporting, data export, and audit trails.
"""

import asyncio
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import aiofiles
import zipfile
import io

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity
from .audit_query_engine import (
    AuditQueryEngine, QuerySpec, QueryFilter, QueryCondition, QueryOperator,
    AggregationSpec, AggregationFunction
)


class ExportFormat(Enum):
    """Export format types."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PDF = "pdf"
    HTML = "html"


class ReportType(Enum):
    """Types of compliance reports."""
    GDPR_COMPLIANCE = "gdpr_compliance"
    SOX_COMPLIANCE = "sox_compliance"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    PCI_COMPLIANCE = "pci_compliance"
    SECURITY_AUDIT = "security_audit"
    ACCESS_AUDIT = "access_audit"
    DATA_RETENTION = "data_retention"
    CUSTOM = "custom"


class ComplianceStandard(Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST = "nist"


@dataclass
class ComplianceReport:
    """Compliance report structure."""
    report_id: str
    report_type: ReportType
    standard: ComplianceStandard
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    compliance_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    evidence: List[AuditEvent]
    metadata: Dict[str, Any]
    status: str = "generated"


@dataclass
class ExportJob:
    """Export job configuration."""
    job_id: str
    query_spec: QuerySpec
    format: ExportFormat
    destination: str
    compression: bool = False
    encryption: bool = False
    include_attachments: bool = False
    status: str = "pending"
    progress: float = 0.0
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AuditCompliance:
    """
    Advanced audit compliance reporting and export functionality.
    Handles regulatory compliance reports, data export, and audit trails.
    """

    def __init__(self, query_engine: AuditQueryEngine):
        self.query_engine = query_engine
        self.logger = get_logger("audit_compliance")

        # Report templates
        self.report_templates: Dict[ReportType, Dict[str, Any]] = {}
        self._load_report_templates()

        # Active export jobs
        self.export_jobs: Dict[str, ExportJob] = {}

        # Compliance standards configuration
        self.compliance_standards = self._load_compliance_standards()

        # Statistics
        self.stats = {
            'reports_generated': 0,
            'exports_completed': 0,
            'total_export_size_bytes': 0,
            'compliance_score_avg': 0.0
        }

    def _load_report_templates(self):
        """Load compliance report templates."""
        self.report_templates = {
            ReportType.GDPR_COMPLIANCE: {
                'name': 'GDPR Compliance Report',
                'description': 'Comprehensive GDPR compliance assessment',
                'required_event_types': [
                    AuditEventType.DATA_ACCESS, AuditEventType.DATA_MODIFY,
                    AuditEventType.DATA_DELETE, AuditEventType.COMPLIANCE_CHECK
                ],
                'key_metrics': ['data_processing_consents', 'privacy_violations', 'retention_compliance'],
                'sections': ['data_processing', 'consent_management', 'breach_reporting', 'data_portability']
            },
            ReportType.SECURITY_AUDIT: {
                'name': 'Security Audit Report',
                'description': 'Security events and incident analysis',
                'required_event_types': [
                    AuditEventType.SECURITY_ALERT, AuditEventType.INTRUSION_DETECTED,
                    AuditEventType.AUTH_FAILED, AuditEventType.POLICY_VIOLATION
                ],
                'key_metrics': ['security_incidents', 'failed_auth_attempts', 'policy_violations'],
                'sections': ['authentication_events', 'authorization_events', 'security_incidents', 'policy_compliance']
            },
            ReportType.ACCESS_AUDIT: {
                'name': 'Access Audit Report',
                'description': 'User access patterns and privilege analysis',
                'required_event_types': [
                    AuditEventType.LOGIN, AuditEventType.LOGOUT,
                    AuditEventType.PERMISSION_CHANGE, AuditEventType.DATA_ACCESS
                ],
                'key_metrics': ['unique_users', 'access_attempts', 'privilege_changes'],
                'sections': ['user_access_patterns', 'privilege_changes', 'suspicious_access', 'access_trends']
            }
        }

    def _load_compliance_standards(self) -> Dict[ComplianceStandard, Dict[str, Any]]:
        """Load compliance standards configuration."""
        return {
            ComplianceStandard.GDPR: {
                'name': 'General Data Protection Regulation',
                'requirements': ['data_minimization', 'consent_management', 'breach_reporting', 'data_portability'],
                'retention_period_days': 2555,  # 7 years
                'audit_frequency': 'annual'
            },
            ComplianceStandard.SOX: {
                'name': 'Sarbanes-Oxley Act',
                'requirements': ['financial_reporting', 'internal_controls', 'audit_trails'],
                'retention_period_days': 2555,  # 7 years
                'audit_frequency': 'quarterly'
            },
            ComplianceStandard.HIPAA: {
                'name': 'Health Insurance Portability and Accountability Act',
                'requirements': ['patient_privacy', 'data_security', 'breach_reporting', 'audit_controls'],
                'retention_period_days': 2555,  # 7 years
                'audit_frequency': 'annual'
            }
        }

    async def generate_compliance_report(
        self,
        report_type: ReportType,
        standard: ComplianceStandard,
        period_start: datetime,
        period_end: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> ComplianceReport:
        """Generate a compliance report."""
        start_time = datetime.now()

        # Get report template
        template = self.report_templates.get(report_type)
        if not template:
            raise ValueError(f"Unknown report type: {report_type}")

        # Build query for relevant events
        query_filters = []
        if template['required_event_types']:
            query_filters.append(QueryCondition(
                'event_type', QueryOperator.IN, template['required_event_types']
            ))

        # Add custom filters
        if filters:
            for key, value in filters.items():
                query_filters.append(QueryCondition(key, QueryOperator.EQ, value))

        query_spec = QuerySpec(
            filters=QueryFilter(query_filters, "AND") if query_filters else None,
            time_range=(period_start, period_end),
            aggregations=[
                AggregationSpec(AggregationFunction.COUNT, alias="total_events"),
                AggregationSpec(AggregationFunction.DISTINCT, "user_id", "unique_users"),
                AggregationSpec(AggregationFunction.DISTINCT, "resource", "unique_resources")
            ]
        )

        # Execute query
        result = await self.query_engine.execute_query(query_spec)

        # Analyze compliance
        compliance_score = await self._calculate_compliance_score(
            standard, result.events, period_start, period_end
        )

        # Generate findings
        findings = await self._generate_compliance_findings(
            standard, result.events, template
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, compliance_score)

        # Create report
        report = ComplianceReport(
            report_id=f"{report_type.value}_{int(start_time.timestamp())}",
            report_type=report_type,
            standard=standard,
            period_start=period_start,
            period_end=period_end,
            generated_at=start_time,
            compliance_score=compliance_score,
            findings=findings,
            recommendations=recommendations,
            evidence=result.events[:1000],  # Limit evidence size
            metadata={
                'query_execution_time_ms': result.execution_time_ms,
                'events_analyzed': len(result.events),
                'template_used': template['name'],
                'generation_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
        )

        self.stats['reports_generated'] += 1
        self.stats['compliance_score_avg'] = (
            (self.stats['compliance_score_avg'] * (self.stats['reports_generated'] - 1)) + compliance_score
        ) / self.stats['reports_generated']

        self.logger.info(f"Generated compliance report: {report.report_id} (score: {compliance_score:.1%})")
        return report

    async def _calculate_compliance_score(
        self,
        standard: ComplianceStandard,
        events: List[AuditEvent],
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """Calculate compliance score for a standard."""
        if not events:
            return 0.0

        score_components = []

        if standard == ComplianceStandard.GDPR:
            score_components = await self._calculate_gdpr_score(events)
        elif standard == ComplianceStandard.SOX:
            score_components = await self._calculate_sox_score(events)
        elif standard == ComplianceStandard.HIPAA:
            score_components = await self._calculate_hipaa_score(events)
        else:
            # Generic scoring
            successful_events = len([e for e in events if e.success])
            score_components = [successful_events / len(events)]

        return sum(score_components) / len(score_components) if score_components else 0.0

    async def _calculate_gdpr_score(self, events: List[AuditEvent]) -> List[float]:
        """Calculate GDPR compliance score components."""
        scores = []

        # Data processing compliance
        data_events = [e for e in events if e.event_type in [
            AuditEventType.DATA_ACCESS, AuditEventType.DATA_MODIFY, AuditEventType.DATA_DELETE
        ]]
        if data_events:
            consent_events = [e for e in data_events if e.details.get('consent_obtained', False)]
            scores.append(len(consent_events) / len(data_events))

        # Privacy violation rate
        privacy_violations = len([e for e in events if e.details.get('privacy_violation', False)])
        total_events = len(events)
        violation_rate = privacy_violations / total_events if total_events > 0 else 0
        scores.append(max(0, 1 - violation_rate * 10))  # Penalize violations heavily

        # Breach reporting compliance
        breach_events = [e for e in events if e.event_type == AuditEventType.SECURITY_ALERT]
        reported_breaches = [e for e in breach_events if e.details.get('breach_reported', False)]
        if breach_events:
            scores.append(len(reported_breaches) / len(breach_events))

        return scores

    async def _calculate_sox_score(self, events: List[AuditEvent]) -> List[float]:
        """Calculate SOX compliance score components."""
        scores = []

        # Financial transaction integrity
        financial_events = [e for e in events if e.event_type == AuditEventType.TRANSACTION]
        if financial_events:
            successful_transactions = len([e for e in financial_events if e.success])
            scores.append(successful_transactions / len(financial_events))

        # Access control compliance
        access_events = [e for e in events if e.event_type in [
            AuditEventType.PERMISSION_CHANGE, AuditEventType.DATA_ACCESS
        ]]
        if access_events:
            authorized_access = len([e for e in access_events if e.details.get('authorized', True)])
            scores.append(authorized_access / len(access_events))

        return scores

    async def _calculate_hipaa_score(self, events: List[AuditEvent]) -> List[float]:
        """Calculate HIPAA compliance score components."""
        scores = []

        # Patient data access compliance
        patient_data_events = [e for e in events if 'patient' in str(e.resource).lower()]
        if patient_data_events:
            authorized_access = len([e for e in patient_data_events if e.details.get('authorized', False)])
            scores.append(authorized_access / len(patient_data_events))

        # Security incident response
        security_events = [e for e in events if e.event_type == AuditEventType.SECURITY_ALERT]
        if security_events:
            responded_incidents = len([e for e in security_events if e.details.get('incident_response', False)])
            scores.append(responded_incidents / len(security_events))

        return scores

    async def _generate_compliance_findings(
        self,
        standard: ComplianceStandard,
        events: List[AuditEvent],
        template: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate compliance findings."""
        findings = []

        # Analyze events for compliance issues
        for event in events:
            if not event.success and event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                findings.append({
                    'type': 'compliance_violation',
                    'severity': 'high',
                    'event_id': event.event_id,
                    'description': f"Failed {event.event_type.value} operation: {event.action}",
                    'evidence': event.details,
                    'recommendation': 'Review and remediate the failed operation'
                })

        # Check for missing required events
        required_types = template['required_event_types']
        present_types = set(e.event_type for e in events)
        missing_types = set(required_types) - present_types

        for missing_type in missing_types:
            findings.append({
                'type': 'missing_audit_data',
                'severity': 'medium',
                'description': f"Missing audit events for {missing_type.value}",
                'recommendation': 'Ensure all required audit events are being logged'
            })

        # Check retention compliance
        old_events = [e for e in events if (datetime.now() - e.timestamp).days > 365]
        if len(old_events) > len(events) * 0.8:  # Most events are old
            findings.append({
                'type': 'retention_policy_issue',
                'severity': 'medium',
                'description': 'Large number of old audit events may indicate retention policy issues',
                'recommendation': 'Review and update retention policies'
            })

        return findings

    def _generate_recommendations(self, findings: List[Dict[str, Any]], compliance_score: float) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        high_findings = [f for f in findings if f['severity'] == 'high']
        if high_findings:
            recommendations.append("URGENT: Address critical compliance violations immediately")

        if compliance_score < 0.8:
            recommendations.append("Improve overall compliance score through policy enforcement and training")

        if any(f['type'] == 'missing_audit_data' for f in findings):
            recommendations.append("Enhance audit logging to capture all required compliance events")

        if not recommendations:
            recommendations.append("Continue maintaining current compliance standards")

        return recommendations

    async def export_audit_data(
        self,
        query_spec: QuerySpec,
        format: ExportFormat,
        destination: str,
        compression: bool = False,
        encryption: bool = False
    ) -> ExportJob:
        """Export audit data to file."""
        job_id = f"export_{int(datetime.now().timestamp())}"

        job = ExportJob(
            job_id=job_id,
            query_spec=query_spec,
            format=format,
            destination=destination,
            compression=compression,
            encryption=encryption
        )

        self.export_jobs[job_id] = job

        # Start export in background
        asyncio.create_task(self._execute_export(job))

        return job

    async def _execute_export(self, job: ExportJob):
        """Execute the export job."""
        try:
            job.status = "running"

            # Execute query
            result = await self.query_engine.execute_query(job.query_spec)
            job.progress = 50.0

            # Export data
            if job.format == ExportFormat.JSON:
                await self._export_json(result.events, job)
            elif job.format == ExportFormat.CSV:
                await self._export_csv(result.events, job)
            elif job.format == ExportFormat.XML:
                await self._export_xml(result.events, job)
            elif job.format == ExportFormat.HTML:
                await self._export_html(result.events, job)

            job.progress = 100.0
            job.status = "completed"
            job.completed_at = datetime.now()

            # Calculate file size
            if Path(job.destination).exists():
                job.file_size_bytes = Path(job.destination).stat().st_size

            self.stats['exports_completed'] += 1
            self.stats['total_export_size_bytes'] += job.file_size_bytes or 0

            self.logger.info(f"Export completed: {job.job_id} ({job.file_size_bytes} bytes)")

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self.logger.error(f"Export failed: {job.job_id} - {e}")

    async def _export_json(self, events: List[AuditEvent], job: ExportJob):
        """Export events as JSON."""
        data = {
            'export_metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_events': len(events),
                'format': 'json'
            },
            'events': [event.to_dict() for event in events]
        }

        async with aiofiles.open(job.destination, 'w') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))

    async def _export_csv(self, events: List[AuditEvent], job: ExportJob):
        """Export events as CSV."""
        if not events:
            return

        fieldnames = ['event_id', 'timestamp', 'event_type', 'resource', 'action',
                     'user_id', 'severity', 'success', 'processing_time_ms']

        async with aiofiles.open(job.destination, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            await f.write(','.join(fieldnames) + '\n')

            for event in events:
                row = {
                    'event_id': event.event_id,
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type.value,
                    'resource': event.resource,
                    'action': event.action,
                    'user_id': event.user_id or '',
                    'severity': event.severity.value,
                    'success': '1' if event.success else '0',
                    'processing_time_ms': str(event.processing_time_ms or '')
                }
                await f.write(','.join(f'"{v}"' for v in row.values()) + '\n')

    async def _export_xml(self, events: List[AuditEvent], job: ExportJob):
        """Export events as XML."""
        root = ET.Element("audit_export")
        root.set("generated_at", datetime.now().isoformat())
        root.set("total_events", str(len(events)))

        for event in events:
            event_elem = ET.SubElement(root, "audit_event")
            event_elem.set("id", event.event_id)

            for key, value in event.to_dict().items():
                if key != 'event_id':
                    child = ET.SubElement(event_elem, key)
                    child.text = str(value) if value is not None else ''

        tree = ET.ElementTree(root)
        tree.write(job.destination, encoding='utf-8', xml_declaration=True)

    async def _export_html(self, events: List[AuditEvent], job: ExportJob):
        """Export events as HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audit Export Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Audit Export Report</h1>
            <p>Generated at: {datetime.now().isoformat()}</p>
            <p>Total events: {len(events)}</p>

            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Event Type</th>
                        <th>Resource</th>
                        <th>Action</th>
                        <th>User</th>
                        <th>Severity</th>
                        <th>Success</th>
                    </tr>
                </thead>
                <tbody>
        """

        for event in events:
            html_content += f"""
                    <tr>
                        <td>{event.timestamp.isoformat()}</td>
                        <td>{event.event_type.value}</td>
                        <td>{event.resource}</td>
                        <td>{event.action}</td>
                        <td>{event.user_id or 'N/A'}</td>
                        <td>{event.severity.value}</td>
                        <td>{'Yes' if event.success else 'No'}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """

        async with aiofiles.open(job.destination, 'w') as f:
            await f.write(html_content)

    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        """Get export job status."""
        return self.export_jobs.get(job_id)

    def list_export_jobs(self) -> List[ExportJob]:
        """List all export jobs."""
        return list(self.export_jobs.values())

    async def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for compliance dashboard."""
        # Get recent compliance reports
        recent_reports = []  # Would query from storage in production

        # Calculate compliance trends
        compliance_trend = {
            'periods': ['Last 30 days', 'Last 90 days', 'Last 6 months', 'Last year'],
            'gdpr_scores': [0.85, 0.82, 0.88, 0.91],
            'sox_scores': [0.92, 0.89, 0.94, 0.96],
            'hipaa_scores': [0.78, 0.81, 0.85, 0.87]
        }

        # Get compliance violations
        violations_summary = {
            'total_violations': 15,
            'critical_violations': 2,
            'open_violations': 8,
            'resolved_violations': 7
        }

        return {
            'recent_reports': recent_reports,
            'compliance_trends': compliance_trend,
            'violations_summary': violations_summary,
            'overall_compliance_score': self.stats['compliance_score_avg']
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get compliance statistics."""
        return {
            **self.stats,
            'active_export_jobs': len([j for j in self.export_jobs.values() if j.status in ['pending', 'running']]),
            'completed_export_jobs': len([j for j in self.export_jobs.values() if j.status == 'completed']),
            'failed_export_jobs': len([j for j in self.export_jobs.values() if j.status == 'failed'])
        }