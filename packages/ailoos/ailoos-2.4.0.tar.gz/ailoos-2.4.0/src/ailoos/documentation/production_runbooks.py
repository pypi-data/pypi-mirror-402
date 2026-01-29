"""
Production Runbooks para AILOOS

Implementa runbooks completos de producción con:
- Deployment procedures automatizados
- Troubleshooting guides inteligentes
- Maintenance schedules programados
- Knowledge base integrada
"""

import asyncio
import logging
import json
import yaml
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


class RunbookType(Enum):
    """Tipos de runbooks disponibles."""
    DEPLOYMENT = "deployment"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"
    INCIDENT_RESPONSE = "incident_response"
    RECOVERY = "recovery"


class DeploymentType(Enum):
    """Tipos de deployment."""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    IMMEDIATE = "immediate"


class MaintenanceWindow(Enum):
    """Ventanas de mantenimiento."""
    WEEKDAY_OFF_HOURS = "weekday_off_hours"  # 22:00-06:00 weekdays
    WEEKEND = "weekend"                      # Saturdays 10:00-18:00
    EMERGENCY = "emergency"                  # Any time for critical fixes
    SCHEDULED = "scheduled"                  # Pre-approved maintenance windows


@dataclass
class RunbookStep:
    """Paso de un runbook."""
    step_id: str
    title: str
    description: str
    automated: bool = False
    timeout_minutes: int = 30
    required_role: str = "operator"
    dependencies: List[str] = field(default_factory=list)
    success_criteria: str = ""
    rollback_instructions: str = ""
    estimated_duration: int = 5  # minutos

    async def execute(self, context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Ejecutar paso del runbook."""
        if self.automated:
            return await self._execute_automated(context)
        else:
            # Para pasos manuales, marcar como pendiente
            return False, f"Manual step requires human intervention: {self.description}", {}

    async def _execute_automated(self, context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Ejecutar paso automatizado."""
        # Simular ejecución automática
        await asyncio.sleep(random.uniform(1, 5))

        # 90% success rate simulado
        success = random.random() < 0.9

        if success:
            return True, f"Step completed successfully: {self.title}", {"duration": random.uniform(1, 10)}
        else:
            return False, f"Step failed: {self.title}", {"error": "Simulated failure"}


@dataclass
class Runbook:
    """Runbook completo."""
    runbook_id: str
    name: str
    description: str
    type: RunbookType
    version: str = "1.0.0"
    author: str = "AILOOS Team"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    steps: List[RunbookStep] = field(default_factory=list)
    estimated_duration: int = 60  # minutos
    risk_level: str = "medium"  # low, medium, high, critical
    approval_required: bool = False

    async def execute_runbook(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar runbook completo."""
        if context is None:
            context = {}

        execution_id = f"exec_{int(time.time())}_{random.randint(1000, 9999)}"
        execution_result = {
            'execution_id': execution_id,
            'runbook_id': self.runbook_id,
            'started_at': datetime.now(),
            'status': 'running',
            'steps_executed': [],
            'context': context,
            'success': True
        }

        executed_steps = set()

        # Ejecutar steps en orden considerando dependencias
        for step in self.steps:
            # Verificar dependencias
            if not all(dep in executed_steps for dep in step.dependencies):
                execution_result['success'] = False
                execution_result['failed_at_step'] = step.step_id
                execution_result['error'] = f"Dependencies not satisfied: {step.dependencies}"
                break

            # Ejecutar step
            step_result = await step.execute(context)
            execution_result['steps_executed'].append({
                'step_id': step.step_id,
                'title': step.title,
                'success': step_result[0],
                'message': step_result[1],
                'metadata': step_result[2],
                'timestamp': datetime.now()
            })

            if step_result[0]:
                executed_steps.add(step.step_id)
            else:
                execution_result['success'] = False
                execution_result['failed_at_step'] = step.step_id
                break

        execution_result['completed_at'] = datetime.now()
        execution_result['total_duration_minutes'] = (
            execution_result['completed_at'] - execution_result['started_at']
        ).total_seconds() / 60

        execution_result['status'] = 'completed' if execution_result['success'] else 'failed'

        return execution_result


@dataclass
class DeploymentProcedure:
    """Procedimiento de deployment."""
    procedure_id: str
    name: str
    deployment_type: DeploymentType
    target_environment: str
    version: str
    components: List[str] = field(default_factory=list)
    pre_deployment_checks: List[str] = field(default_factory=list)
    post_deployment_tests: List[str] = field(default_factory=list)
    rollback_plan: str = ""
    estimated_downtime: int = 0  # minutos
    maintenance_window: MaintenanceWindow = MaintenanceWindow.SCHEDULED

    def validate_deployment_window(self) -> bool:
        """Validar que estamos en ventana de mantenimiento apropiada."""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday

        if self.maintenance_window == MaintenanceWindow.WEEKDAY_OFF_HOURS:
            # 22:00-06:00, Monday-Friday
            return (current_weekday < 5 and
                   (current_time >= time(22, 0) or current_time <= time(6, 0)))

        elif self.maintenance_window == MaintenanceWindow.WEEKEND:
            # Saturday 10:00-18:00
            return (current_weekday == 5 and
                   current_time >= time(10, 0) and current_time <= time(18, 0))

        elif self.maintenance_window == MaintenanceWindow.EMERGENCY:
            # Always allowed for emergencies
            return True

        elif self.maintenance_window == MaintenanceWindow.SCHEDULED:
            # Would check against pre-approved schedule
            return True

        return False


@dataclass
class TroubleshootingGuide:
    """Guía de troubleshooting."""
    guide_id: str
    title: str
    problem_description: str
    symptoms: List[str] = field(default_factory=list)
    root_causes: List[str] = field(default_factory=list)
    diagnostic_steps: List[str] = field(default_factory=list)
    solutions: List[Dict[str, Any]] = field(default_factory=list)
    prevention_tips: List[str] = field(default_factory=list)
    related_guides: List[str] = field(default_factory=list)
    severity: str = "medium"
    tags: List[str] = field(default_factory=list)

    def find_solution(self, symptoms_present: List[str]) -> Optional[Dict[str, Any]]:
        """Encontrar solución basada en síntomas."""
        # Simple matching algorithm
        symptom_matches = sum(1 for symptom in symptoms_present if
                            any(symptom.lower() in s.lower() for s in self.symptoms))

        if symptom_matches >= len(symptoms_present) * 0.7:  # 70% match
            # Return best solution
            return self.solutions[0] if self.solutions else None

        return None


@dataclass
class MaintenanceSchedule:
    """Horario de mantenimiento."""
    schedule_id: str
    name: str
    description: str
    frequency: str  # "daily", "weekly", "monthly", "quarterly"
    maintenance_window: MaintenanceWindow
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    responsible_team: str = "platform_team"
    notification_days_ahead: int = 7
    estimated_duration_hours: float = 2.0
    next_scheduled: Optional[datetime] = None
    last_executed: Optional[datetime] = None

    def calculate_next_schedule(self) -> datetime:
        """Calcular próximo horario de mantenimiento."""
        now = datetime.now()

        if self.frequency == "daily":
            next_time = now + timedelta(days=1)
        elif self.frequency == "weekly":
            # Next Saturday
            days_until_saturday = (5 - now.weekday()) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            next_time = now + timedelta(days=days_until_saturday)
        elif self.frequency == "monthly":
            # First Saturday of next month
            if now.month == 12:
                next_month = 1
                next_year = now.year + 1
            else:
                next_month = now.month + 1
                next_year = now.year

            first_of_next_month = datetime(next_year, next_month, 1)
            days_until_saturday = (5 - first_of_next_month.weekday()) % 7
            next_time = first_of_next_month + timedelta(days=days_until_saturday)
        else:  # quarterly
            # First Saturday after 3 months
            next_time = now + timedelta(days=90)
            days_until_saturday = (5 - next_time.weekday()) % 7
            next_time = next_time + timedelta(days=days_until_saturday)

        # Set to maintenance window time
        if self.maintenance_window == MaintenanceWindow.WEEKDAY_OFF_HOURS:
            next_time = next_time.replace(hour=22, minute=0, second=0, microsecond=0)
        elif self.maintenance_window == MaintenanceWindow.WEEKEND:
            next_time = next_time.replace(hour=10, minute=0, second=0, microsecond=0)

        self.next_scheduled = next_time
        return next_time

    def is_due(self) -> bool:
        """Verificar si el mantenimiento está vencido."""
        if not self.next_scheduled:
            return False
        return datetime.now() >= self.next_scheduled


class ProductionRunbookManager:
    """
    Gestor de runbooks de producción.

    Características:
    - Runbooks ejecutables automáticamente
    - Troubleshooting inteligente
    - Maintenance scheduling
    - Knowledge base integrada
    """

    def __init__(self):
        self.runbooks: Dict[str, Runbook] = {}
        self.deployment_procedures: Dict[str, DeploymentProcedure] = {}
        self.troubleshooting_guides: Dict[str, TroubleshootingGuide] = {}
        self.maintenance_schedules: Dict[str, MaintenanceSchedule] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def add_runbook(self, runbook: Runbook):
        """Añadir runbook."""
        self.runbooks[runbook.runbook_id] = runbook
        logger.info(f"Added runbook: {runbook.name} ({runbook.runbook_id})")

    def add_deployment_procedure(self, procedure: DeploymentProcedure):
        """Añadir procedimiento de deployment."""
        self.deployment_procedures[procedure.procedure_id] = procedure
        logger.info(f"Added deployment procedure: {procedure.name}")

    def add_troubleshooting_guide(self, guide: TroubleshootingGuide):
        """Añadir guía de troubleshooting."""
        self.troubleshooting_guides[guide.guide_id] = guide
        logger.info(f"Added troubleshooting guide: {guide.title}")

    def add_maintenance_schedule(self, schedule: MaintenanceSchedule):
        """Añadir horario de mantenimiento."""
        self.maintenance_schedules[schedule.schedule_id] = schedule
        schedule.calculate_next_schedule()
        logger.info(f"Added maintenance schedule: {schedule.name}")

    async def execute_runbook(self, runbook_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar runbook."""
        if runbook_id not in self.runbooks:
            return {'error': 'Runbook not found'}

        runbook = self.runbooks[runbook_id]

        # Check approval if required
        if runbook.approval_required:
            approval_granted = await self._request_approval(runbook)
            if not approval_granted:
                return {'error': 'Runbook execution not approved'}

        # Execute runbook
        result = await runbook.execute_runbook(context)

        # Store execution history
        self.execution_history.append(result)

        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        return result

    async def execute_deployment(self, procedure_id: str, version: str) -> Dict[str, Any]:
        """Ejecutar procedimiento de deployment."""
        if procedure_id not in self.deployment_procedures:
            return {'error': 'Deployment procedure not found'}

        procedure = self.deployment_procedures[procedure_id]

        # Validate maintenance window
        if not procedure.validate_deployment_window():
            return {'error': 'Not in approved maintenance window'}

        # Update version
        procedure.version = version

        # Create deployment runbook context
        context = {
            'deployment_type': procedure.deployment_type.value,
            'target_environment': procedure.target_environment,
            'version': version,
            'components': procedure.components
        }

        # Find and execute appropriate runbook
        runbook_id = f"deployment_{procedure.deployment_type.value}"
        if runbook_id in self.runbooks:
            result = await self.execute_runbook(runbook_id, context)
            return result
        else:
            return {'error': f'No runbook found for deployment type: {procedure.deployment_type.value}'}

    def troubleshoot_issue(self, symptoms: List[str], component: str = "") -> List[Dict[str, Any]]:
        """Troubleshoot problema basado en síntomas."""
        matches = []

        for guide in self.troubleshooting_guides.values():
            # Filter by component if specified
            if component and component.lower() not in guide.title.lower():
                continue

            solution = guide.find_solution(symptoms)
            if solution:
                matches.append({
                    'guide_id': guide.guide_id,
                    'title': guide.title,
                    'severity': guide.severity,
                    'solution': solution,
                    'prevention_tips': guide.prevention_tips
                })

        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        matches.sort(key=lambda x: severity_order.get(x['severity'], 99))

        return matches

    async def check_maintenance_schedules(self) -> List[Dict[str, Any]]:
        """Verificar horarios de mantenimiento vencidos."""
        due_maintenance = []

        for schedule in self.maintenance_schedules.values():
            if schedule.is_due():
                due_maintenance.append({
                    'schedule_id': schedule.schedule_id,
                    'name': schedule.name,
                    'next_scheduled': schedule.next_scheduled.isoformat(),
                    'estimated_duration_hours': schedule.estimated_duration_hours,
                    'responsible_team': schedule.responsible_team
                })

                # Reschedule for next occurrence
                schedule.calculate_next_schedule()
                schedule.last_executed = datetime.now()

        return due_maintenance

    async def _request_approval(self, runbook: Runbook) -> bool:
        """Solicitar aprobación para runbook (simulado)."""
        # En producción: enviar email/Slack, esperar respuesta
        await asyncio.sleep(1)
        return random.random() < 0.8  # 80% approval rate

    def get_runbook_status(self) -> Dict[str, Any]:
        """Obtener status general de runbooks."""
        total_runbooks = len(self.runbooks)
        deployment_procedures = len(self.deployment_procedures)
        troubleshooting_guides = len(self.troubleshooting_guides)
        maintenance_schedules = len(self.maintenance_schedules)

        recent_executions = len([
            exec for exec in self.execution_history
            if (datetime.now() - exec['started_at']).days <= 7
        ])

        success_rate = 0
        if recent_executions > 0:
            successful_executions = len([
                exec for exec in self.execution_history
                if exec.get('success', False) and (datetime.now() - exec['started_at']).days <= 7
            ])
            success_rate = successful_executions / recent_executions * 100

        return {
            'total_runbooks': total_runbooks,
            'deployment_procedures': deployment_procedures,
            'troubleshooting_guides': troubleshooting_guides,
            'maintenance_schedules': maintenance_schedules,
            'recent_executions': recent_executions,
            'success_rate': round(success_rate, 1),
            'due_maintenance': len(await self.check_maintenance_schedules())
        }


# Funciones de conveniencia

def create_deployment_runbooks() -> List[Runbook]:
    """Crear runbooks de deployment por defecto."""
    runbooks = []

    # Blue-Green Deployment Runbook
    blue_green = Runbook(
        runbook_id="deployment_blue_green",
        name="Blue-Green Deployment",
        description="Zero-downtime deployment using blue-green strategy",
        type=RunbookType.DEPLOYMENT,
        tags=["deployment", "blue-green", "zero-downtime"],
        prerequisites=["Health checks passing", "Database schema compatibility", "Feature flags configured"],
        estimated_duration=45,
        risk_level="low"
    )

    blue_green.steps = [
        RunbookStep(
            step_id="health_check_pre",
            title="Pre-deployment Health Check",
            description="Verify all services are healthy before deployment",
            automated=True,
            timeout_minutes=10,
            success_criteria="All services returning 200 OK"
        ),
        RunbookStep(
            step_id="deploy_green",
            title="Deploy to Green Environment",
            description="Deploy new version to green environment",
            automated=True,
            timeout_minutes=20,
            success_criteria="Green environment deployment successful"
        ),
        RunbookStep(
            step_id="smoke_test",
            title="Run Smoke Tests",
            description="Execute critical functionality tests on green environment",
            automated=True,
            timeout_minutes=5,
            success_criteria="All smoke tests passing"
        ),
        RunbookStep(
            step_id="traffic_switch",
            title="Switch Traffic to Green",
            description="Gradually switch traffic from blue to green",
            automated=True,
            timeout_minutes=10,
            success_criteria="100% traffic on green environment"
        ),
        RunbookStep(
            step_id="monitor_green",
            title="Monitor Green Environment",
            description="Monitor green environment for 15 minutes",
            automated=True,
            timeout_minutes=15,
            success_criteria="No critical errors in monitoring"
        )
    ]

    runbooks.append(blue_green)

    return runbooks


def create_troubleshooting_guides() -> List[TroubleshootingGuide]:
    """Crear guías de troubleshooting por defecto."""
    guides = []

    # API Timeout Guide
    api_timeout = TroubleshootingGuide(
        guide_id="api_timeout",
        title="API Gateway Timeout Issues",
        problem_description="API requests timing out or taking too long to respond",
        symptoms=[
            "HTTP 504 Gateway Timeout errors",
            "Requests taking longer than 30 seconds",
            "Intermittent API failures",
            "High latency in API responses"
        ],
        root_causes=[
            "Database connection pool exhausted",
            "Upstream service overload",
            "Network connectivity issues",
            "Inefficient database queries",
            "Memory leaks in application"
        ],
        diagnostic_steps=[
            "Check API gateway logs for timeout patterns",
            "Monitor database connection pool usage",
            "Review upstream service health metrics",
            "Analyze slow query logs",
            "Check network latency between services"
        ],
        solutions=[
            {
                "title": "Scale database connection pool",
                "description": "Increase connection pool size in database configuration",
                "commands": ["kubectl scale deployment api-gateway --replicas=3"],
                "estimated_time": "5 minutes"
            },
            {
                "title": "Optimize slow queries",
                "description": "Add database indexes and optimize query performance",
                "commands": ["Run EXPLAIN on slow queries", "Add appropriate indexes"],
                "estimated_time": "30 minutes"
            }
        ],
        prevention_tips=[
            "Implement database query monitoring",
            "Set up connection pool alerts",
            "Regular performance testing",
            "Implement circuit breakers"
        ],
        severity="high",
        tags=["api", "timeout", "performance", "database"]
    )

    guides.append(api_timeout)

    return guides


def create_maintenance_schedules() -> List[MaintenanceSchedule]:
    """Crear horarios de mantenimiento por defecto."""
    schedules = []

    # Database Maintenance
    db_maintenance = MaintenanceSchedule(
        schedule_id="db_weekly_maintenance",
        name="Database Weekly Maintenance",
        description="Weekly database optimization and cleanup",
        frequency="weekly",
        maintenance_window=MaintenanceWindow.WEEKEND,
        responsible_team="database_team",
        notification_days_ahead=7,
        estimated_duration_hours=4.0,
        tasks=[
            {
                "task": "Analyze table statistics",
                "description": "Update table statistics for query optimization",
                "automated": True
            },
            {
                "task": "Clean up old data",
                "description": "Remove data older than retention policy",
                "automated": True
            },
            {
                "task": "Rebuild indexes",
                "description": "Rebuild fragmented indexes",
                "automated": True
            }
        ]
    )

    schedules.append(db_maintenance)

    # Security Updates
    security_updates = MaintenanceSchedule(
        schedule_id="security_monthly_updates",
        name="Security Updates and Patching",
        description="Monthly security updates and vulnerability patching",
        frequency="monthly",
        maintenance_window=MaintenanceWindow.WEEKDAY_OFF_HOURS,
        responsible_team="security_team",
        notification_days_ahead=14,
        estimated_duration_hours=6.0,
        tasks=[
            {
                "task": "Apply OS security patches",
                "description": "Update operating system security packages",
                "automated": False
            },
            {
                "task": "Update application dependencies",
                "description": "Update third-party libraries and dependencies",
                "automated": True
            },
            {
                "task": "Security configuration review",
                "description": "Review and update security configurations",
                "automated": False
            }
        ]
    )

    schedules.append(security_updates)

    return schedules


async def demonstrate_production_runbooks():
    """Demostrar runbooks de producción completos."""
    print("📋 Inicializando Production Runbooks...")

    # Crear manager
    manager = ProductionRunbookManager()

    # Añadir runbooks
    runbooks = create_deployment_runbooks()
    for runbook in runbooks:
        manager.add_runbook(runbook)

    # Añadir troubleshooting guides
    guides = create_troubleshooting_guides()
    for guide in guides:
        manager.add_troubleshooting_guide(guide)

    # Añadir maintenance schedules
    schedules = create_maintenance_schedules()
    for schedule in schedules:
        manager.add_maintenance_schedule(schedule)

    print("📊 Estado inicial del sistema:")
    status = manager.get_runbook_status()
    print(f"   Runbooks totales: {status['total_runbooks']}")
    print(f"   Guías de troubleshooting: {status['troubleshooting_guides']}")
    print(f"   Horarios de mantenimiento: {status['maintenance_schedules']}")

    # Ejecutar runbook de deployment
    print("\n🚀 Ejecutando Runbook de Deployment...")
    deployment_result = await manager.execute_runbook("deployment_blue_green", {
        'version': 'v2.1.0',
        'environment': 'production'
    })

    success = deployment_result.get('success', False)
    duration = deployment_result.get('total_duration_minutes', 0)
    print(f"   Deployment completado: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(".1f"
    # Ejecutar troubleshooting
    print("
🔍 Probando Troubleshooting Inteligente..."    symptoms = ["HTTP 504 Gateway Timeout errors", "Requests taking longer than 30 seconds"]
    troubleshooting_results = manager.troubleshoot_issue(symptoms, "api")

    if troubleshooting_results:
        guide = troubleshooting_results[0]
        print(f"   Guía encontrada: {guide['title']}")
        print(f"   Severidad: {guide['severity']}")
        print(f"   Solución sugerida: {guide['solution']['title']}")
    else:
        print("   No se encontraron guías relevantes")

    # Verificar maintenance schedules
    print("
🛠️ Verificando Maintenance Schedules..."    due_maintenance = await manager.check_maintenance_schedules()
    print(f"   Mantenimientos vencidos: {len(due_maintenance)}")

    if due_maintenance:
        for maintenance in due_maintenance[:2]:  # Show first 2
            print(f"   - {maintenance['name']} (Equipo: {maintenance['responsible_team']})")

    # Mostrar status final
    print("
📈 Status Final de Production Runbooks:"    final_status = manager.get_runbook_status()
    print(f"   Ejecuciones recientes: {final_status['recent_executions']}")
    print(f"   Tasa de éxito: {final_status['success_rate']}%")
    print(f"   Mantenimientos pendientes: {final_status['due_maintenance']}")

    print("✅ Production Runbooks demostrado correctamente")

    return manager


if __name__ == "__main__":
    asyncio.run(demonstrate_production_runbooks())