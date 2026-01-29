"""
Team Training para AILOOS

Implementa sistema completo de training para equipos con:
- Security awareness training automatizado
- Incident response training con simulaciones
- Compliance training con tracking
- Knowledge assessment y certification
"""

import asyncio
import logging
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class TrainingType(Enum):
    """Tipos de training disponibles."""
    SECURITY_AWARENESS = "security_awareness"
    INCIDENT_RESPONSE = "incident_response"
    COMPLIANCE = "compliance"
    TECHNICAL_SKILLS = "technical_skills"


class TrainingLevel(Enum):
    """Niveles de training."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CertificationStatus(Enum):
    """Estados de certificación."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class TrainingModule:
    """Módulo de training."""
    module_id: str
    title: str
    description: str
    training_type: TrainingType
    level: TrainingLevel
    estimated_duration_minutes: int = 60
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    content_sections: List[Dict[str, Any]] = field(default_factory=list)
    assessment_questions: List[Dict[str, Any]] = field(default_factory=list)
    passing_score: int = 80  # percentage
    validity_months: int = 12  # certification validity
    version: str = "1.0"  # module version for compliance tracking

    @property
    def is_comprehensive(self) -> bool:
        """Verificar si el módulo es comprensivo."""
        return (len(self.content_sections) >= 5 and
                len(self.assessment_questions) >= 10 and
                len(self.learning_objectives) >= 3)


@dataclass
class TrainingSession:
    """Sesión de training."""
    session_id: str
    module_id: str
    trainee_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    current_section: int = 0
    progress_percentage: float = 0.0
    assessment_score: Optional[float] = None
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    responses: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Verificar si la sesión está completada."""
        return self.status == "completed"

    @property
    def time_spent_minutes(self) -> float:
        """Tiempo gastado en minutos."""
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds() / 60


@dataclass
class Certification:
    """Certificación de training."""
    certification_id: str
    trainee_id: str
    module_id: str
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: CertificationStatus = CertificationStatus.NOT_STARTED
    score_achieved: Optional[float] = None
    renewal_required: bool = False

    def __post_init__(self):
        if not self.expires_at:
            # Default 1 year validity
            self.expires_at = self.issued_at + timedelta(days=365)

    @property
    def is_valid(self) -> bool:
        """Verificar si la certificación es válida."""
        return (self.status == CertificationStatus.COMPLETED and
                datetime.now() <= self.expires_at)

    @property
    def days_until_expiry(self) -> int:
        """Días hasta expiración."""
        if not self.expires_at:
            return 999
        return max(0, (self.expires_at - datetime.now()).days)


@dataclass
class SecurityAwarenessCampaign:
    """Campaña de security awareness."""
    campaign_id: str
    name: str
    description: str
    target_audience: List[str] = field(default_factory=list)  # team names or "all"
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    modules: List[str] = field(default_factory=list)  # module_ids
    phishing_simulation: bool = False
    completion_target: int = 80  # percentage
    status: str = "active"  # "active", "completed", "cancelled"

    @property
    def is_active(self) -> bool:
        """Verificar si la campaña está activa."""
        now = datetime.now()
        return (self.status == "active" and
                self.start_date <= now and
                (not self.end_date or now <= self.end_date))


@dataclass
class IncidentSimulation:
    """Simulación de incidente para training."""
    simulation_id: str
    name: str
    description: str
    incident_type: str
    difficulty: str = "medium"  # "easy", "medium", "hard"
    estimated_duration_minutes: int = 30
    scenario_description: str = ""
    required_actions: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    debrief_questions: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)

    async def run_simulation(self, participants: List[str]) -> Dict[str, Any]:
        """Ejecutar simulación de incidente."""
        # Simular ejecución de simulación
        await asyncio.sleep(random.uniform(10, 30))  # Simular duración

        # Resultados simulados
        results = {
            'simulation_id': self.simulation_id,
            'participants': participants,
            'started_at': datetime.now() - timedelta(minutes=self.estimated_duration_minutes),
            'completed_at': datetime.now(),
            'success_rate': random.uniform(0.6, 0.95),
            'average_response_time': random.uniform(5, 15),  # minutes
            'actions_taken': random.randint(3, 8),
            'mistakes_made': random.randint(0, 3),
            'learning_outcomes': self.learning_objectives
        }

        return results


class SecurityAwarenessManager:
    """
    Gestor de security awareness training.

    Características:
    - Training modules interactivos
    - Phishing simulations
    - Progress tracking
    - Certification management
    """

    def __init__(self):
        self.modules: Dict[str, TrainingModule] = {}
        self.sessions: Dict[str, TrainingSession] = {}
        self.certifications: Dict[str, Certification] = {}
        self.campaigns: Dict[str, SecurityAwarenessCampaign] = {}

    def add_module(self, module: TrainingModule):
        """Añadir módulo de training."""
        self.modules[module.module_id] = module
        logger.info(f"Added training module: {module.title}")

    def add_campaign(self, campaign: SecurityAwarenessCampaign):
        """Añadir campaña de awareness."""
        self.campaigns[campaign.campaign_id] = campaign
        logger.info(f"Added awareness campaign: {campaign.name}")

    async def start_training_session(self, trainee_id: str, module_id: str) -> str:
        """Iniciar sesión de training."""
        if module_id not in self.modules:
            raise ValueError(f"Module {module_id} not found")

        session_id = f"session_{trainee_id}_{module_id}_{int(time.time())}"

        session = TrainingSession(
            session_id=session_id,
            module_id=module_id,
            trainee_id=trainee_id
        )

        self.sessions[session_id] = session

        # Initialize certification if not exists
        cert_key = f"{trainee_id}_{module_id}"
        if cert_key not in self.certifications:
            self.certifications[cert_key] = Certification(
                certification_id=f"cert_{cert_key}",
                trainee_id=trainee_id,
                module_id=module_id,
                status=CertificationStatus.IN_PROGRESS
            )

        logger.info(f"Started training session: {session_id}")
        return session_id

    async def submit_assessment(self, session_id: str, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar assessment para evaluación."""
        if session_id not in self.sessions:
            return {'error': 'Session not found'}

        session = self.sessions[session_id]
        module = self.modules[session.module_id]

        # Evaluate responses
        correct_answers = 0
        total_questions = len(module.assessment_questions)

        for question in module.assessment_questions:
            question_id = question['id']
            if question_id in responses:
                user_answer = responses[question_id]
                correct_answer = question['correct_answer']

                # Simple evaluation (in production: more sophisticated)
                if isinstance(correct_answer, list):
                    if set(user_answer) == set(correct_answer):
                        correct_answers += 1
                elif user_answer == correct_answer:
                    correct_answers += 1

        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        passed = score >= module.passing_score

        # Update session
        session.assessment_score = score
        session.completed_at = datetime.now()
        session.responses = responses
        session.status = "completed" if passed else "failed"
        session.progress_percentage = 100.0

        # Update certification
        cert_key = f"{session.trainee_id}_{session.module_id}"
        if cert_key in self.certifications:
            cert = self.certifications[cert_key]
            if passed:
                cert.status = CertificationStatus.COMPLETED
                cert.score_achieved = score
                cert.issued_at = datetime.now()
                cert.expires_at = datetime.now() + timedelta(days=module.validity_months * 30)

        result = {
            'session_id': session_id,
            'score': round(score, 1),
            'passed': passed,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'certification_issued': passed
        }

        logger.info(f"Assessment submitted for session {session_id}: {score:.1f}% ({'PASSED' if passed else 'FAILED'})")

        return result

    async def run_phishing_simulation(self, campaign_id: str, targets: List[str]) -> Dict[str, Any]:
        """Ejecutar simulación de phishing."""
        if campaign_id not in self.campaigns:
            return {'error': 'Campaign not found'}

        campaign = self.campaigns[campaign_id]

        # Simulate phishing emails sent
        simulation_results = {
            'campaign_id': campaign_id,
            'targets': targets,
            'emails_sent': len(targets),
            'phishing_clicks': random.randint(0, len(targets) // 4),  # 25% click rate max
            'reported_phishing': random.randint(0, len(targets) // 10),  # 10% report rate max
            'started_at': datetime.now(),
            'completed_at': datetime.now() + timedelta(hours=1)
        }

        # Calculate success metrics
        click_rate = (simulation_results['phishing_clicks'] / simulation_results['emails_sent']) * 100
        report_rate = (simulation_results['reported_phishing'] / simulation_results['emails_sent']) * 100

        simulation_results.update({
            'click_rate': round(click_rate, 1),
            'report_rate': round(report_rate, 1),
            'overall_score': round(100 - click_rate + report_rate, 1)  # Higher is better
        })

        logger.info(f"Phishing simulation completed for campaign {campaign_id}: {click_rate:.1f}% click rate")

        return simulation_results

    def get_training_status(self, trainee_id: str) -> Dict[str, Any]:
        """Obtener status de training para un trainee."""
        user_sessions = [s for s in self.sessions.values() if s.trainee_id == trainee_id]
        user_certs = [c for c in self.certifications.values() if c.trainee_id == trainee_id]

        completed_modules = len([s for s in user_sessions if s.is_completed])
        total_modules = len(set(s.module_id for s in user_sessions))

        valid_certs = len([c for c in user_certs if c.is_valid])
        expired_certs = len([c for c in user_certs if c.status == CertificationStatus.EXPIRED])

        return {
            'trainee_id': trainee_id,
            'completed_modules': completed_modules,
            'total_modules': total_modules,
            'completion_rate': (completed_modules / total_modules * 100) if total_modules > 0 else 0,
            'valid_certifications': valid_certs,
            'expired_certifications': expired_certs,
            'average_score': self._calculate_average_score(user_sessions)
        }

    def _calculate_average_score(self, sessions: List[TrainingSession]) -> float:
        """Calcular score promedio."""
        scores = [s.assessment_score for s in sessions if s.assessment_score is not None]
        return sum(scores) / len(scores) if scores else 0.0


class IncidentResponseTrainingManager:
    """
    Gestor de incident response training.

    Características:
    - Incident simulations
    - Response time tracking
    - Performance analytics
    - Debriefing sessions
    """

    def __init__(self):
        self.simulations: Dict[str, IncidentSimulation] = {}
        self.training_sessions: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = {}

    def add_simulation(self, simulation: IncidentSimulation):
        """Añadir simulación de incidente."""
        self.simulations[simulation.simulation_id] = simulation
        logger.info(f"Added incident simulation: {simulation.name}")

    async def run_training_session(self, simulation_id: str, participants: List[str]) -> Dict[str, Any]:
        """Ejecutar sesión de training con simulación."""
        if simulation_id not in self.simulations:
            return {'error': 'Simulation not found'}

        simulation = self.simulations[simulation_id]

        # Run simulation
        results = await simulation.run_simulation(participants)

        # Store training session
        training_session = {
            'session_id': f"training_{int(time.time())}_{random.randint(1000, 9999)}",
            'simulation_id': simulation_id,
            'participants': participants,
            'results': results,
            'conducted_at': datetime.now()
        }

        self.training_sessions.append(training_session)

        # Update performance metrics
        for participant in participants:
            if participant not in self.performance_metrics:
                self.performance_metrics[participant] = []

            self.performance_metrics[participant].append(results['success_rate'])

        logger.info(f"Incident response training completed: {simulation.name} with {len(participants)} participants")

        return training_session

    def get_performance_analytics(self, participant_id: str = None) -> Dict[str, Any]:
        """Obtener analytics de performance."""
        if participant_id:
            # Individual performance
            scores = self.performance_metrics.get(participant_id, [])
            if not scores:
                return {'error': 'No performance data found'}

            return {
                'participant_id': participant_id,
                'total_simulations': len(scores),
                'average_score': round(sum(scores) / len(scores) * 100, 1),
                'best_score': round(max(scores) * 100, 1),
                'worst_score': round(min(scores) * 100, 1),
                'improvement_trend': self._calculate_improvement_trend(scores)
            }
        else:
            # Team performance
            all_scores = []
            for scores in self.performance_metrics.values():
                all_scores.extend(scores)

            if not all_scores:
                return {'error': 'No performance data found'}

            return {
                'total_participants': len(self.performance_metrics),
                'total_simulations': len(all_scores),
                'average_team_score': round(sum(all_scores) / len(all_scores) * 100, 1),
                'participants_above_80': len([s for s in all_scores if s >= 0.8]),
                'simulation_success_rate': round(len([s for s in all_scores if s >= 0.7]) / len(all_scores) * 100, 1)
            }

    def _calculate_improvement_trend(self, scores: List[float]) -> str:
        """Calcular trend de mejora."""
        if len(scores) < 3:
            return "insufficient_data"

        # Simple linear trend
        recent_avg = sum(scores[-3:]) / 3
        earlier_avg = sum(scores[:3]) / 3

        if recent_avg > earlier_avg + 0.1:
            return "improving"
        elif recent_avg < earlier_avg - 0.1:
            return "declining"
        else:
            return "stable"


class ComplianceTrainingManager:
    """
    Gestor de compliance training.

    Características:
    - Regulatory compliance modules
    - Policy acknowledgment tracking
    - Audit trails
    - Compliance reporting
    """

    def __init__(self):
        self.compliance_modules: Dict[str, TrainingModule] = {}
        self.acknowledgments: Dict[str, Dict[str, Any]] = {}  # user_id -> {policy_id: acknowledgment}
        self.audit_trail: List[Dict[str, Any]] = []

    def add_compliance_module(self, module: TrainingModule):
        """Añadir módulo de compliance."""
        self.compliance_modules[module.module_id] = module
        logger.info(f"Added compliance module: {module.title}")

    async def record_policy_acknowledgment(self, user_id: str, policy_id: str,
                                          version: str, ip_address: str) -> bool:
        """Registrar acknowledgment de política."""
        if policy_id not in self.compliance_modules:
            return False

        if user_id not in self.acknowledgments:
            self.acknowledgments[user_id] = {}

        self.acknowledgments[user_id][policy_id] = {
            'acknowledged_at': datetime.now(),
            'version': version,
            'ip_address': ip_address,
            'status': 'acknowledged'
        }

        # Audit trail
        audit_entry = {
            'user_id': user_id,
            'policy_id': policy_id,
            'action': 'acknowledged',
            'timestamp': datetime.now(),
            'ip_address': ip_address,
            'version': version
        }

        self.audit_trail.append(audit_entry)

        logger.info(f"Policy acknowledgment recorded: {user_id} acknowledged {policy_id}")
        return True

    def get_compliance_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener status de compliance para usuario."""
        user_acks = self.acknowledgments.get(user_id, {})

        required_policies = list(self.compliance_modules.keys())
        acknowledged_policies = list(user_acks.keys())

        compliance_rate = len(acknowledged_policies) / len(required_policies) * 100 if required_policies else 0

        # Check for expired acknowledgments (policies updated)
        expired_acks = []
        for policy_id, ack in user_acks.items():
            if policy_id in self.compliance_modules:
                current_version = self.compliance_modules[policy_id].version
                if ack.get('version') != current_version:
                    expired_acks.append(policy_id)

        return {
            'user_id': user_id,
            'total_required_policies': len(required_policies),
            'acknowledged_policies': len(acknowledged_policies),
            'compliance_rate': round(compliance_rate, 1),
            'expired_acknowledgments': expired_acks,
            'is_compliant': compliance_rate >= 100 and len(expired_acks) == 0
        }

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generar reporte de compliance para toda la organización."""
        total_users = len(self.acknowledgments)
        compliant_users = 0
        total_acknowledgments = 0

        for user_acks in self.acknowledgments.values():
            user_compliant = True
            for policy_id, ack in user_acks.items():
                total_acknowledgments += 1
                if policy_id in self.compliance_modules:
                    current_version = self.compliance_modules[policy_id].version
                    if ack.get('version') != current_version:
                        user_compliant = False

            if user_compliant and len(user_acks) == len(self.compliance_modules):
                compliant_users += 1

        compliance_rate = (compliant_users / total_users * 100) if total_users > 0 else 0

        return {
            'total_users': total_users,
            'compliant_users': compliant_users,
            'compliance_rate': round(compliance_rate, 1),
            'total_acknowledgments': total_acknowledgments,
            'required_policies': len(self.compliance_modules),
            'generated_at': datetime.now()
        }


class TeamTrainingOrchestrator:
    """
    Orchestrator principal para team training.

    Coordina security awareness, incident response y compliance training.
    """

    def __init__(self):
        self.security_awareness = SecurityAwarenessManager()
        self.incident_response = IncidentResponseTrainingManager()
        self.compliance = ComplianceTrainingManager()
        self.training_schedule: Dict[str, List[Dict[str, Any]]] = {}

    async def initialize_training_program(self):
        """Inicializar programa completo de training."""
        # Create default training modules
        await self._create_default_modules()

        # Create default simulations
        self._create_default_simulations()

        logger.info("Team training program initialized")

    async def _create_default_modules(self):
        """Crear módulos de training por defecto."""
        # Security Awareness Module
        security_module = TrainingModule(
            module_id="security_awareness_basic",
            title="Basic Security Awareness",
            description="Fundamental security concepts and best practices",
            training_type=TrainingType.SECURITY_AWARENESS,
            level=TrainingLevel.BEGINNER,
            estimated_duration_minutes=45,
            learning_objectives=[
                "Understand basic security concepts",
                "Identify common security threats",
                "Apply security best practices",
                "Report security incidents"
            ],
            content_sections=[
                {
                    "title": "Password Security",
                    "content": "Best practices for creating and managing passwords",
                    "duration_minutes": 10
                },
                {
                    "title": "Phishing Awareness",
                    "content": "How to identify and avoid phishing attacks",
                    "duration_minutes": 15
                },
                {
                    "title": "Data Protection",
                    "content": "Handling sensitive data appropriately",
                    "duration_minutes": 10
                }
            ],
            assessment_questions=[
                {
                    "id": "q1",
                    "question": "What is phishing?",
                    "type": "multiple_choice",
                    "options": ["A type of fish", "A cyber attack", "A programming language"],
                    "correct_answer": "A cyber attack"
                },
                {
                    "id": "q2",
                    "question": "Which of these is a strong password?",
                    "type": "multiple_choice",
                    "options": ["password123", "P@ssw0rd!2024", "123456"],
                    "correct_answer": "P@ssw0rd!2024"
                }
            ]
        )

        # Incident Response Module
        incident_module = TrainingModule(
            module_id="incident_response_basic",
            title="Basic Incident Response",
            description="How to respond to security incidents",
            training_type=TrainingType.INCIDENT_RESPONSE,
            level=TrainingLevel.INTERMEDIATE,
            estimated_duration_minutes=60,
            prerequisites=["security_awareness_basic"],
            learning_objectives=[
                "Understand incident response process",
                "Know when to escalate incidents",
                "Document incident details properly",
                "Communicate during incidents"
            ]
        )

        # Compliance Module
        compliance_module = TrainingModule(
            module_id="gdpr_compliance",
            title="GDPR Compliance Training",
            description="Understanding GDPR requirements and compliance",
            training_type=TrainingType.COMPLIANCE,
            level=TrainingLevel.INTERMEDIATE,
            estimated_duration_minutes=90,
            learning_objectives=[
                "Understand GDPR principles",
                "Know data subject rights",
                "Implement data protection measures",
                "Handle data breaches properly"
            ]
        )

        self.security_awareness.add_module(security_module)
        self.security_awareness.add_module(incident_module)
        self.compliance.add_compliance_module(compliance_module)

    def _create_default_simulations(self):
        """Crear simulaciones por defecto."""
        # DDoS Attack Simulation
        ddos_sim = IncidentSimulation(
            simulation_id="ddos_attack_sim",
            name="DDoS Attack Response",
            description="Respond to a distributed denial of service attack",
            incident_type="ddos_attack",
            difficulty="medium",
            estimated_duration_minutes=25,
            scenario_description="""
            The monitoring system has detected unusual traffic patterns.
            Multiple services are showing increased response times and some are becoming unresponsive.
            Initial analysis suggests this might be a DDoS attack.
            """,
            required_actions=[
                "Assess the scope of the attack",
                "Implement rate limiting",
                "Contact upstream providers",
                "Communicate with stakeholders",
                "Document the incident"
            ],
            success_criteria=[
                "Attack mitigated within 30 minutes",
                "Services restored to normal operation",
                "Proper incident documentation",
                "Stakeholder communication maintained"
            ],
            learning_objectives=[
                "Understand DDoS attack patterns",
                "Know when to activate DDoS protection",
                "Practice stakeholder communication",
                "Learn incident documentation procedures"
            ]
        )

        # Data Breach Simulation
        breach_sim = IncidentSimulation(
            simulation_id="data_breach_sim",
            name="Data Breach Response",
            description="Respond to a suspected data breach",
            incident_type="data_breach",
            difficulty="hard",
            estimated_duration_minutes=45,
            scenario_description="""
            Security monitoring has detected unauthorized access to customer data.
            Logs show suspicious database queries from an unknown IP address.
            Initial assessment indicates potential data exfiltration.
            """,
            required_actions=[
                "Isolate affected systems",
                "Assess data exposure",
                "Notify affected customers",
                "Report to authorities if required",
                "Implement remediation measures"
            ],
            success_criteria=[
                "Affected systems isolated",
                "Data exposure assessed within 1 hour",
                "Required notifications sent",
                "Remediation plan implemented"
            ]
        )

        self.incident_response.add_simulation(ddos_sim)
        self.incident_response.add_simulation(breach_sim)

    async def schedule_training_session(self, trainee_id: str, module_id: str,
                                      scheduled_time: datetime) -> str:
        """Programar sesión de training."""
        if trainee_id not in self.training_schedule:
            self.training_schedule[trainee_id] = []

        session_info = {
            'module_id': module_id,
            'scheduled_time': scheduled_time,
            'status': 'scheduled',
            'reminders_sent': 0
        }

        self.training_schedule[trainee_id].append(session_info)

        logger.info(f"Training session scheduled for {trainee_id}: {module_id} at {scheduled_time}")
        return f"scheduled_{trainee_id}_{module_id}_{int(time.time())}"

    async def send_training_reminders(self) -> Dict[str, Any]:
        """Enviar recordatorios de training."""
        reminders_sent = 0
        upcoming_sessions = 0

        for trainee_id, sessions in self.training_schedule.items():
            for session in sessions:
                if session['status'] == 'scheduled':
                    time_until = session['scheduled_time'] - datetime.now()
                    hours_until = time_until.total_seconds() / 3600

                    # Send reminder 24 hours before
                    if 20 <= hours_until <= 28:  # 24h ± 4h window
                        # Send reminder (simulated)
                        await self._send_reminder_email(trainee_id, session)
                        session['reminders_sent'] += 1
                        reminders_sent += 1

                    if hours_until > 0:
                        upcoming_sessions += 1

        return {
            'reminders_sent': reminders_sent,
            'upcoming_sessions': upcoming_sessions
        }

    async def _send_reminder_email(self, trainee_id: str, session: Dict[str, Any]):
        """Enviar email de reminder (simulado)."""
        await asyncio.sleep(0.1)
        logger.info(f"Training reminder sent to {trainee_id} for {session['module_id']}")

    def get_team_training_status(self) -> Dict[str, Any]:
        """Obtener status general de training del equipo."""
        total_users = len(set(list(self.security_awareness.certifications.keys()) +
                            list(self.compliance.acknowledgments.keys())))

        # Security awareness stats
        awareness_completions = len([c for c in self.security_awareness.certifications.values()
                                   if c.status == CertificationStatus.COMPLETED])

        # Incident response stats
        incident_participants = len(self.incident_response.performance_metrics)
        incident_simulations = len(self.incident_response.training_sessions)

        # Compliance stats
        compliance_report = self.compliance.generate_compliance_report()

        return {
            'total_team_members': total_users,
            'security_awareness_completions': awareness_completions,
            'incident_response_participants': incident_participants,
            'incident_simulations_conducted': incident_simulations,
            'compliance_rate': compliance_report['compliance_rate'],
            'overall_training_score': self._calculate_overall_score()
        }

    def _calculate_overall_score(self) -> float:
        """Calcular score general de training."""
        awareness_score = 0
        compliance_score = 0
        incident_score = 0

        # Awareness score
        total_certs = len(self.security_awareness.certifications)
        valid_certs = len([c for c in self.security_awareness.certifications.values() if c.is_valid])
        awareness_score = (valid_certs / total_certs * 100) if total_certs > 0 else 0

        # Compliance score
        compliance_report = self.compliance.generate_compliance_report()
        compliance_score = compliance_report['compliance_rate']

        # Incident response score
        if self.incident_response.performance_metrics:
            all_scores = []
            for scores in self.incident_response.performance_metrics.values():
                all_scores.extend(scores)
            incident_score = (sum(all_scores) / len(all_scores) * 100) if all_scores else 0

        # Weighted average
        weights = [0.4, 0.4, 0.2]  # awareness, compliance, incident response
        scores = [awareness_score, compliance_score, incident_score]

        return sum(w * s for w, s in zip(weights, scores)) / sum(weights)


# Funciones de conveniencia

async def demonstrate_team_training():
    """Demostrar team training completo."""
    print("🎓 Inicializando Team Training System...")

    # Crear orchestrator
    orchestrator = TeamTrainingOrchestrator()

    # Inicializar programa de training
    await orchestrator.initialize_training_program()

    print("📊 Estado inicial del sistema:")
    status = orchestrator.get_team_training_status()
    print(f"   Módulos de training: {len(orchestrator.security_awareness.modules)}")
    print(f"   Simulaciones disponibles: {len(orchestrator.incident_response.simulations)}")
    print(f"   Políticas de compliance: {len(orchestrator.compliance.compliance_modules)}")

    # Simular training sessions
    trainees = ["alice", "bob", "charlie", "diana"]
    modules = ["security_awareness_basic", "incident_response_basic"]

    print("\n👥 Simulando Training Sessions:")
    for trainee in trainees:
        for module in modules:
            try:
                # Start session
                session_id = await orchestrator.security_awareness.start_training_session(trainee, module)
                print(f"   {trainee} inició {module}")

                # Simulate completion with random score
                score = random.uniform(75, 100)
                responses = {f"q{i}": f"answer_{i}" for i in range(1, 11)}

                result = await orchestrator.security_awareness.submit_assessment(session_id, responses)
                print(f"   {trainee} completó {module}: {result['score']:.1f}% ({'APROBADO' if result['passed'] else 'REPROBADO'})")

            except Exception as e:
                print(f"   Error con {trainee} en {module}: {e}")

    # Simular incident response training
    print("\n🚨 Simulando Incident Response Training:")
    simulation_results = await orchestrator.incident_response.run_training_session(
        "ddos_attack_sim", trainees[:3]  # First 3 trainees
    )

    print(f"   Simulación completada: {simulation_results['results']['success_rate']:.1%} tasa de éxito")
    print(f"   Tiempo promedio de respuesta: {simulation_results['results']['average_response_time']:.1f} minutos")

    # Simular compliance acknowledgments
    print("\n📋 Simulando Compliance Acknowledgments:")
    for trainee in trainees:
        for policy_id in orchestrator.compliance.compliance_modules.keys():
            success = await orchestrator.compliance.record_policy_acknowledgment(
                trainee, policy_id, "v1.0", "192.168.1.100"
            )
            if success:
                print(f"   {trainee} reconoció política {policy_id}")

    # Mostrar status final
    print("\n📈 Status Final de Team Training:")
    final_status = orchestrator.get_team_training_status()
    print(f"   Miembros del equipo: {final_status['total_team_members']}")
    print(f"   Tasa de compliance: {final_status['compliance_rate']}%")
    print(f"   Participantes en IR training: {final_status['incident_response_participants']}")
    print(f"   Score general: {final_status['overall_training_score']:.1f}%")

    # Mostrar performance individual
    print("\n🏃 Performance Individual:")
    for trainee in trainees[:2]:  # Show first 2
        perf = orchestrator.incident_response.get_performance_analytics(trainee)
        if 'average_score' in perf:
            print(f"   {trainee}: {perf['average_score']:.1f}% promedio en simulaciones")

    print("✅ Team Training demostrado correctamente")

    return orchestrator


if __name__ == "__main__":
    asyncio.run(demonstrate_team_training())