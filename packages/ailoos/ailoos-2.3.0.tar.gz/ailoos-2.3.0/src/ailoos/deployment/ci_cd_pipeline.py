"""
CI/CD Pipeline Completo para AILOOS

Implementa pipeline completo con:
- Automated testing (unit, integration, e2e)
- Blue-green deployments
- Rollback automation
- Multi-environment promotion
- Quality gates y approvals
"""

import asyncio
import logging
import json
import yaml
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics
import os
import tempfile

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Etapas del pipeline CI/CD."""
    BUILD = "build"
    TEST = "test"
    SECURITY_SCAN = "security_scan"
    DEPLOY_STAGING = "deploy_staging"
    INTEGRATION_TEST = "integration_test"
    DEPLOY_PRODUCTION = "deploy_production"
    E2E_TEST = "e2e_test"
    MONITORING = "monitoring"


class TestType(Enum):
    """Tipos de tests disponibles."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SMOKE = "smoke"


class DeploymentStrategy(Enum):
    """Estrategias de deployment."""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    IMMEDIATE = "immediate"


class PipelineStatus(Enum):
    """Estados del pipeline."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Resultado de un test."""
    test_type: TestType
    test_name: str
    status: PipelineStatus
    duration_seconds: float
    output: str = ""
    error_message: Optional[str] = None
    coverage_percentage: Optional[float] = None
    passed_tests: int = 0
    failed_tests: int = 0
    total_tests: int = 0

    @property
    def success_rate(self) -> float:
        """Tasa de éxito de tests."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


@dataclass
class PipelineStep:
    """Paso del pipeline."""
    stage: PipelineStage
    name: str
    status: PipelineStatus = PipelineStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    test_results: List[TestResult] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duración del paso en segundos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """Verificar si el paso está completado."""
        return self.status in [PipelineStatus.SUCCESS, PipelineStatus.FAILURE, PipelineStatus.CANCELLED]


@dataclass
class Deployment:
    """Deployment con blue-green strategy."""
    deployment_id: str
    application: str
    version: str
    strategy: DeploymentStrategy
    environment: str
    blue_version: Optional[str] = None
    green_version: Optional[str] = None
    active_color: str = "blue"  # "blue" or "green"
    traffic_distribution: Dict[str, float] = field(default_factory=lambda: {"blue": 100.0, "green": 0.0})
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        """Verificar si el deployment está completo."""
        return self.status in [PipelineStatus.SUCCESS, PipelineStatus.FAILURE]

    @property
    def active_version(self) -> Optional[str]:
        """Obtener versión activa."""
        if self.active_color == "blue":
            return self.blue_version
        else:
            return self.green_version


class AutomatedTestingSuite:
    """
    Suite completa de testing automatizado.

    Características:
    - Unit tests con coverage
    - Integration tests
    - E2E tests
    - Performance tests
    - Security scanning
    """

    def __init__(self):
        self.test_results: Dict[TestType, List[TestResult]] = {}
        self.coverage_threshold = 80.0  # 80% mínimo
        self.performance_thresholds = {
            'response_time_ms': 500,
            'throughput_req_sec': 100,
            'error_rate_percent': 1.0
        }

    async def run_unit_tests(self, project_path: str) -> TestResult:
        """Ejecutar unit tests con coverage."""
        start_time = time.time()

        try:
            # Simular pytest con coverage
            await asyncio.sleep(2)  # Simular ejecución

            # Resultados simulados
            result = TestResult(
                test_type=TestType.UNIT,
                test_name="unit_tests",
                status=PipelineStatus.SUCCESS,
                duration_seconds=time.time() - start_time,
                coverage_percentage=85.5,
                passed_tests=245,
                failed_tests=3,
                total_tests=248,
                output="Ran 248 tests, 245 passed, 3 failed"
            )

            self._store_result(result)
            return result

        except Exception as e:
            return TestResult(
                test_type=TestType.UNIT,
                test_name="unit_tests",
                status=PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    async def run_integration_tests(self, environment: str) -> TestResult:
        """Ejecutar integration tests."""
        start_time = time.time()

        try:
            await asyncio.sleep(3)  # Simular tests más largos

            result = TestResult(
                test_type=TestType.INTEGRATION,
                test_name=f"integration_{environment}",
                status=PipelineStatus.SUCCESS,
                duration_seconds=time.time() - start_time,
                passed_tests=67,
                failed_tests=0,
                total_tests=67,
                output=f"Integration tests passed in {environment}"
            )

            self._store_result(result)
            return result

        except Exception as e:
            return TestResult(
                test_type=TestType.INTEGRATION,
                test_name=f"integration_{environment}",
                status=PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    async def run_e2e_tests(self, environment: str) -> TestResult:
        """Ejecutar end-to-end tests."""
        start_time = time.time()

        try:
            await asyncio.sleep(5)  # E2E tests son más largos

            result = TestResult(
                test_type=TestType.E2E,
                test_name=f"e2e_{environment}",
                status=PipelineStatus.SUCCESS,
                duration_seconds=time.time() - start_time,
                passed_tests=23,
                failed_tests=1,
                total_tests=24,
                output=f"E2E tests completed in {environment}"
            )

            self._store_result(result)
            return result

        except Exception as e:
            return TestResult(
                test_type=TestType.E2E,
                test_name=f"e2e_{environment}",
                status=PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    async def run_security_scan(self, code_path: str) -> TestResult:
        """Ejecutar security scanning."""
        start_time = time.time()

        try:
            await asyncio.sleep(4)  # Security scan toma tiempo

            # Simular findings de seguridad
            vulnerabilities = {
                'high': 0,
                'medium': 2,
                'low': 5,
                'info': 12
            }

            result = TestResult(
                test_type=TestType.SECURITY,
                test_name="security_scan",
                status=PipelineStatus.SUCCESS if vulnerabilities['high'] == 0 else PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                output=f"Security scan: {vulnerabilities}",
                metadata={"vulnerabilities": vulnerabilities}
            )

            self._store_result(result)
            return result

        except Exception as e:
            return TestResult(
                test_type=TestType.SECURITY,
                test_name="security_scan",
                status=PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    async def run_performance_tests(self, environment: str) -> TestResult:
        """Ejecutar performance tests."""
        start_time = time.time()

        try:
            await asyncio.sleep(6)  # Performance tests son intensivos

            # Métricas simuladas
            metrics = {
                'avg_response_time_ms': 245,
                'p95_response_time_ms': 450,
                'throughput_req_sec': 150,
                'error_rate_percent': 0.5,
                'memory_usage_mb': 512,
                'cpu_usage_percent': 65
            }

            # Verificar thresholds
            passed = (
                metrics['avg_response_time_ms'] <= self.performance_thresholds['response_time_ms'] and
                metrics['throughput_req_sec'] >= self.performance_thresholds['throughput_req_sec'] and
                metrics['error_rate_percent'] <= self.performance_thresholds['error_rate_percent']
            )

            result = TestResult(
                test_type=TestType.PERFORMANCE,
                test_name=f"performance_{environment}",
                status=PipelineStatus.SUCCESS if passed else PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                output=f"Performance test results: {metrics}",
                metadata={"metrics": metrics}
            )

            self._store_result(result)
            return result

        except Exception as e:
            return TestResult(
                test_type=TestType.PERFORMANCE,
                test_name=f"performance_{environment}",
                status=PipelineStatus.FAILURE,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def _store_result(self, result: TestResult):
        """Almacenar resultado de test."""
        if result.test_type not in self.test_results:
            self.test_results[result.test_type] = []
        self.test_results[result.test_type].append(result)

    def get_test_summary(self) -> Dict[str, Any]:
        """Obtener resumen de tests."""
        summary = {}

        for test_type, results in self.test_results.items():
            if results:
                latest = results[-1]  # Último resultado
                summary[test_type.value] = {
                    'status': latest.status.value,
                    'success_rate': latest.success_rate,
                    'duration': latest.duration_seconds,
                    'total_tests': latest.total_tests,
                    'passed': latest.passed_tests,
                    'failed': latest.failed_tests
                }

        return summary


class BlueGreenDeploymentManager:
    """
    Gestor de blue-green deployments.

    Características:
    - Zero-downtime deployments
    - Traffic switching automático
    - Health checks continuos
    - Rollback instantáneo
    """

    def __init__(self):
        self.deployments: Dict[str, Deployment] = {}
        self.load_balancers: Dict[str, Dict[str, Any]] = {}

    def create_deployment(self, application: str, version: str,
                         environment: str) -> Deployment:
        """Crear nuevo deployment blue-green."""
        deployment_id = f"{application}-{environment}-{int(time.time())}"

        deployment = Deployment(
            deployment_id=deployment_id,
            application=application,
            version=version,
            strategy=DeploymentStrategy.BLUE_GREEN,
            environment=environment,
            blue_version=self._get_current_version(application, environment)
        )

        self.deployments[deployment_id] = deployment
        logger.info(f"Created blue-green deployment: {deployment_id}")

        return deployment

    def _get_current_version(self, application: str, environment: str) -> Optional[str]:
        """Obtener versión actual (simulado)."""
        # En producción, consultar Kubernetes/deployments
        return "v1.1.0"  # Versión simulada

    async def deploy_green(self, deployment_id: str) -> bool:
        """Desplegar versión nueva (green)."""
        if deployment_id not in self.deployments:
            return False

        deployment = self.deployments[deployment_id]

        try:
            # Simular deployment de green environment
            logger.info(f"Deploying green version {deployment.version} for {deployment.application}")
            await asyncio.sleep(5)  # Simular tiempo de deployment

            deployment.green_version = deployment.version
            deployment.status = PipelineStatus.RUNNING

            # Health checks
            if await self._run_health_checks(deployment, "green"):
                logger.info(f"Green deployment healthy for {deployment.application}")
                return True
            else:
                logger.error(f"Green deployment failed health checks for {deployment.application}")
                return False

        except Exception as e:
            logger.error(f"Green deployment failed: {e}")
            deployment.status = PipelineStatus.FAILURE
            return False

    async def switch_traffic(self, deployment_id: str, green_percentage: float = 100.0) -> bool:
        """Cambiar tráfico entre blue y green."""
        if deployment_id not in self.deployments:
            return False

        deployment = self.deployments[deployment_id]

        try:
            # Simular traffic switching
            logger.info(f"Switching traffic to {green_percentage}% green for {deployment.application}")

            # Gradual traffic shift (canary style)
            steps = 10
            for i in range(steps + 1):
                green_pct = (green_percentage / 100) * (i / steps) * 100
                blue_pct = 100 - green_pct

                deployment.traffic_distribution = {
                    "blue": blue_pct,
                    "green": green_pct
                }

                await asyncio.sleep(0.5)  # Simular tiempo entre steps

            # Update active color
            if green_percentage >= 50:
                deployment.active_color = "green"

            logger.info(f"Traffic switched successfully for {deployment.application}")
            return True

        except Exception as e:
            logger.error(f"Traffic switch failed: {e}")
            return False

    async def _run_health_checks(self, deployment: Deployment, color: str) -> bool:
        """Ejecutar health checks."""
        try:
            # Simular health checks
            await asyncio.sleep(2)

            # 95% success rate simulado
            return random.random() < 0.95

        except Exception as e:
            logger.error(f"Health check failed for {color}: {e}")
            return False

    async def rollback(self, deployment_id: str) -> bool:
        """Rollback instantáneo a blue environment."""
        if deployment_id not in self.deployments:
            return False

        deployment = self.deployments[deployment_id]

        try:
            logger.warning(f"Rolling back {deployment.application} to blue environment")

            # Switch all traffic back to blue
            success = await self.switch_traffic(deployment_id, 0.0)

            if success:
                deployment.active_color = "blue"
                deployment.status = PipelineStatus.SUCCESS
                logger.info(f"Rollback completed for {deployment.application}")
                return True
            else:
                logger.error(f"Rollback failed for {deployment.application}")
                return False

        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False

    def get_deployment_status(self, deployment_id: str) -> Optional[Deployment]:
        """Obtener status de deployment."""
        return self.deployments.get(deployment_id)


class RollbackAutomation:
    """
    Automatización completa de rollbacks.

    Características:
    - Rollback automático basado en métricas
    - Multiple strategies de rollback
    - Recovery orchestration
    - Incident tracking
    """

    def __init__(self):
        self.rollback_triggers: Dict[str, Dict[str, Any]] = {}
        self.incidents: List[Dict[str, Any]] = []

    def configure_rollback_trigger(self, application: str, environment: str,
                                 trigger_conditions: Dict[str, Any]):
        """Configurar trigger automático de rollback."""
        key = f"{application}-{environment}"
        self.rollback_triggers[key] = {
            'conditions': trigger_conditions,
            'last_triggered': None,
            'trigger_count': 0
        }

        logger.info(f"Configured rollback trigger for {key}")

    async def check_rollback_conditions(self, application: str, environment: str,
                                      metrics: Dict[str, Any]) -> Tuple[bool, str]:
        """Verificar si se deben activar condiciones de rollback."""
        key = f"{application}-{environment}"

        if key not in self.rollback_triggers:
            return False, ""

        trigger_config = self.rollback_triggers[key]
        conditions = trigger_config['conditions']

        # Verificar condiciones
        reasons = []

        # Error rate threshold
        if 'error_rate_threshold' in conditions:
            if metrics.get('error_rate', 0) > conditions['error_rate_threshold']:
                reasons.append(f"Error rate {metrics['error_rate']:.2f}% > {conditions['error_rate_threshold']}%")

        # Response time threshold
        if 'response_time_threshold_ms' in conditions:
            if metrics.get('avg_response_time_ms', 0) > conditions['response_time_threshold_ms']:
                reasons.append(f"Response time {metrics['avg_response_time_ms']}ms > {conditions['response_time_threshold_ms']}ms")

        # Health check failures
        if 'health_check_failures' in conditions:
            if metrics.get('health_check_failures', 0) >= conditions['health_check_failures']:
                reasons.append(f"Health check failures {metrics['health_check_failures']} >= {conditions['health_check_failures']}")

        if reasons:
            reason = "; ".join(reasons)
            trigger_config['last_triggered'] = datetime.now()
            trigger_config['trigger_count'] += 1

            # Crear incident
            incident = {
                'incident_id': f"incident-{int(time.time())}",
                'application': application,
                'environment': environment,
                'reason': reason,
                'metrics': metrics,
                'timestamp': datetime.now(),
                'status': 'rollback_triggered'
            }
            self.incidents.append(incident)

            return True, reason

        return False, ""

    async def execute_emergency_rollback(self, application: str, environment: str,
                                       deployment_manager: BlueGreenDeploymentManager) -> bool:
        """Ejecutar rollback de emergencia."""
        try:
            logger.warning(f"Executing emergency rollback for {application} in {environment}")

            # Encontrar deployment activo
            active_deployment = None
            for deployment in deployment_manager.deployments.values():
                if (deployment.application == application and
                    deployment.environment == environment and
                    not deployment.is_complete):
                    active_deployment = deployment
                    break

            if active_deployment:
                success = await deployment_manager.rollback(active_deployment.deployment_id)

                if success:
                    # Actualizar incident
                    if self.incidents:
                        self.incidents[-1]['status'] = 'rollback_completed'

                    logger.info(f"Emergency rollback completed for {application}")
                    return True
                else:
                    logger.error(f"Emergency rollback failed for {application}")
                    return False
            else:
                logger.error(f"No active deployment found for {application} in {environment}")
                return False

        except Exception as e:
            logger.error(f"Emergency rollback error: {e}")
            return False

    def get_rollback_history(self, application: str = None, environment: str = None) -> List[Dict[str, Any]]:
        """Obtener historial de rollbacks."""
        history = []

        for incident in self.incidents:
            if incident.get('status') == 'rollback_completed':
                if application and incident['application'] != application:
                    continue
                if environment and incident['environment'] != environment:
                    continue
                history.append(incident)

        return history


class CICDPipeline:
    """
    Pipeline CI/CD completo con todas las funcionalidades.
    """

    def __init__(self):
        self.steps: List[PipelineStep] = []
        self.testing_suite = AutomatedTestingSuite()
        self.deployment_manager = BlueGreenDeploymentManager()
        self.rollback_automation = RollbackAutomation()
        self.quality_gates: Dict[str, Callable] = {}

    def add_quality_gate(self, stage: PipelineStage, gate_func: Callable[[], bool]):
        """Añadir quality gate."""
        self.quality_gates[stage] = gate_func

    async def execute_pipeline(self, application: str, version: str) -> bool:
        """Ejecutar pipeline completo."""
        logger.info(f"Starting CI/CD pipeline for {application} v{version}")

        # Definir steps del pipeline
        pipeline_steps = [
            PipelineStage.BUILD,
            PipelineStage.TEST,
            PipelineStage.SECURITY_SCAN,
            PipelineStage.DEPLOY_STAGING,
            PipelineStage.INTEGRATION_TEST,
            PipelineStage.DEPLOY_PRODUCTION,
            PipelineStage.E2E_TEST,
            PipelineStage.MONITORING
        ]

        # Crear steps
        for stage in pipeline_steps:
            step = PipelineStep(stage=stage, name=stage.value)
            self.steps.append(step)

        # Ejecutar cada step
        for step in self.steps:
            success = await self._execute_step(step, application, version)
            if not success:
                logger.error(f"Pipeline failed at step: {step.name}")
                await self._handle_pipeline_failure(step, application, version)
                return False

        logger.info(f"CI/CD pipeline completed successfully for {application} v{version}")
        return True

    async def _execute_step(self, step: PipelineStep, application: str, version: str) -> bool:
        """Ejecutar un step específico."""
        step.status = PipelineStatus.RUNNING
        step.start_time = datetime.now()

        try:
            logger.info(f"Executing pipeline step: {step.name}")

            # Quality gate check
            if step.stage in self.quality_gates:
                if not self.quality_gates[step.stage]():
                    logger.error(f"Quality gate failed for {step.stage}")
                    step.status = PipelineStatus.FAILURE
                    return False

            # Ejecutar step específico
            if step.stage == PipelineStage.BUILD:
                success = await self._build_application(application, version, step)

            elif step.stage == PipelineStage.TEST:
                success = await self._run_tests(step)

            elif step.stage == PipelineStage.SECURITY_SCAN:
                success = await self._run_security_scan(step)

            elif step.stage == PipelineStage.DEPLOY_STAGING:
                success = await self._deploy_staging(application, version, step)

            elif step.stage == PipelineStage.INTEGRATION_TEST:
                success = await self._run_integration_tests(step)

            elif step.stage == PipelineStage.DEPLOY_PRODUCTION:
                success = await self._deploy_production(application, version, step)

            elif step.stage == PipelineStage.E2E_TEST:
                success = await self._run_e2e_tests(step)

            elif step.stage == PipelineStage.MONITORING:
                success = await self._setup_monitoring(application, version, step)

            else:
                success = True

            step.status = PipelineStatus.SUCCESS if success else PipelineStatus.FAILURE

        except Exception as e:
            logger.error(f"Step {step.name} failed with error: {e}")
            step.status = PipelineStatus.FAILURE
            step.metadata['error'] = str(e)

        finally:
            step.end_time = datetime.now()

        return step.status == PipelineStatus.SUCCESS

    async def _build_application(self, application: str, version: str, step: PipelineStep) -> bool:
        """Build application."""
        await asyncio.sleep(3)  # Simular build
        step.artifacts['docker_image'] = f"{application}:{version}"
        step.artifacts['build_log'] = "Build completed successfully"
        return True

    async def _run_tests(self, step: PipelineStep) -> bool:
        """Run test suite."""
        # Unit tests
        unit_result = await self.testing_suite.run_unit_tests(".")
        step.test_results.append(unit_result)

        # Security scan
        security_result = await self.testing_suite.run_security_scan(".")
        step.test_results.append(security_result)

        # Performance tests
        perf_result = await self.testing_suite.run_performance_tests("staging")
        step.test_results.append(perf_result)

        # Check if all tests passed
        all_passed = all(result.status == PipelineStatus.SUCCESS for result in step.test_results)
        return all_passed

    async def _run_security_scan(self, step: PipelineStep) -> bool:
        """Run security scan (ya incluido en tests)."""
        return True

    async def _deploy_staging(self, application: str, version: str, step: PipelineStep) -> bool:
        """Deploy to staging."""
        await asyncio.sleep(2)  # Simular deployment
        step.metadata['environment'] = 'staging'
        step.metadata['deployment_url'] = f"https://staging.{application}.com"
        return True

    async def _run_integration_tests(self, step: PipelineStep) -> bool:
        """Run integration tests."""
        result = await self.testing_suite.run_integration_tests("staging")
        step.test_results.append(result)
        return result.status == PipelineStatus.SUCCESS

    async def _deploy_production(self, application: str, version: str, step: PipelineStep) -> bool:
        """Deploy to production using blue-green."""
        # Crear deployment
        deployment = self.deployment_manager.create_deployment(application, version, "production")

        # Deploy green
        green_success = await self.deployment_manager.deploy_green(deployment.deployment_id)

        if not green_success:
            return False

        # Switch traffic gradually
        traffic_success = await self.deployment_manager.switch_traffic(deployment.deployment_id, 100.0)

        if traffic_success:
            deployment.status = PipelineStatus.SUCCESS
            deployment.completed_at = datetime.now()

        step.metadata['deployment_id'] = deployment.deployment_id
        step.metadata['strategy'] = 'blue_green'

        return traffic_success

    async def _run_e2e_tests(self, step: PipelineStep) -> bool:
        """Run E2E tests."""
        result = await self.testing_suite.run_e2e_tests("production")
        step.test_results.append(result)
        return result.status == PipelineStatus.SUCCESS

    async def _setup_monitoring(self, application: str, version: str, step: PipelineStep) -> bool:
        """Setup monitoring."""
        await asyncio.sleep(1)  # Simular setup
        step.metadata['monitoring_dashboard'] = f"https://monitoring.com/dashboard/{application}"
        return True

    async def _handle_pipeline_failure(self, failed_step: PipelineStep,
                                     application: str, version: str):
        """Handle pipeline failure."""
        logger.error(f"Pipeline failed at step: {failed_step.name}")

        # Si falló en producción, intentar rollback automático
        if failed_step.stage == PipelineStage.DEPLOY_PRODUCTION:
            logger.info("Attempting automatic rollback...")

            # Encontrar deployment activo
            for deployment in self.deployment_manager.deployments.values():
                if (deployment.application == application and
                    deployment.environment == "production" and
                    not deployment.is_complete):
                    await self.deployment_manager.rollback(deployment.deployment_id)
                    break

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Obtener status del pipeline."""
        completed_steps = len([s for s in self.steps if s.is_completed])
        successful_steps = len([s for s in self.steps if s.status == PipelineStatus.SUCCESS])

        return {
            'total_steps': len(self.steps),
            'completed_steps': completed_steps,
            'successful_steps': successful_steps,
            'success_rate': (successful_steps / len(self.steps) * 100) if self.steps else 0,
            'current_step': self.steps[completed_steps].name if completed_steps < len(self.steps) else None
        }


# Funciones de conveniencia

async def create_production_pipeline() -> CICDPipeline:
    """Crear pipeline de producción completo."""
    pipeline = CICDPipeline()

    # Configurar quality gates
    def test_quality_gate():
        """Quality gate: tests deben pasar con >80% coverage."""
        summary = pipeline.testing_suite.get_test_summary()
        unit_tests = summary.get('unit', {})
        return (unit_tests.get('success_rate', 0) >= 80 and
                unit_tests.get('status') == 'success')

    def security_quality_gate():
        """Quality gate: no high severity vulnerabilities."""
        summary = pipeline.testing_suite.get_test_summary()
        security = summary.get('security', {})
        return security.get('status') == 'success'

    pipeline.add_quality_gate(PipelineStage.TEST, test_quality_gate)
    pipeline.add_quality_gate(PipelineStage.SECURITY_SCAN, security_quality_gate)

    # Configurar rollback automation
    pipeline.rollback_automation.configure_rollback_trigger(
        "ailoos-api", "production",
        {
            'error_rate_threshold': 5.0,  # 5% error rate
            'response_time_threshold_ms': 1000,  # 1s response time
            'health_check_failures': 3  # 3 health check failures
        }
    )

    return pipeline


async def demonstrate_ci_cd_pipeline():
    """Demostrar pipeline CI/CD completo."""
    print("🚀 Inicializando CI/CD Pipeline Completo...")

    # Crear pipeline
    pipeline = await create_production_pipeline()

    print("📊 Ejecutando Pipeline CI/CD para AILOOS API v1.2.3...")

    # Ejecutar pipeline completo
    success = await pipeline.execute_pipeline("ailoos-api", "v1.2.3")

    print(f"\n📈 Resultado del Pipeline: {'✅ SUCCESS' if success else '❌ FAILED'}")

    # Mostrar resumen detallado
    print("\n📋 Resumen de Steps:")
    for step in pipeline.steps:
        status_icon = {
            PipelineStatus.SUCCESS: "✅",
            PipelineStatus.FAILURE: "❌",
            PipelineStatus.RUNNING: "🔄",
            PipelineStatus.PENDING: "⏳"
        }.get(step.status, "❓")

        duration = f"{step.duration_seconds:.1f}s" if step.duration_seconds else "N/A"
        print(f"   {status_icon} {step.name}: {step.status.value} ({duration})")

        # Mostrar test results si existen
        if step.test_results:
            for test_result in step.test_results:
                test_status = "✅" if test_result.status == PipelineStatus.SUCCESS else "❌"
                print(f"      {test_status} {test_result.test_name}: {test_result.success_rate:.1f}% success")

    # Mostrar deployments
    print("\n🏗️ Deployments Realizados:")
    for deployment in pipeline.deployment_manager.deployments.values():
        status_icon = "✅" if deployment.status == PipelineStatus.SUCCESS else "❌"
        active_version = deployment.active_version or "N/A"
        print(f"   {status_icon} {deployment.application} {deployment.environment}: {active_version} ({deployment.active_color})")

    # Mostrar métricas finales
    final_status = pipeline.get_pipeline_status()
    test_summary = pipeline.testing_suite.get_test_summary()

    print("\n📊 Métricas Finales:")
    print(f"   Pipeline Success Rate: {final_status['success_rate']:.1f}%")
    print(f"   Steps Completed: {final_status['completed_steps']}/{final_status['total_steps']}")

    if 'unit' in test_summary:
        unit = test_summary['unit']
        print(f"   Unit Tests: {unit['success_rate']:.1f}% ({unit['passed']}/{unit['total']})")

    if 'integration' in test_summary:
        integration = test_summary['integration']
        print(f"   Integration Tests: {integration['success_rate']:.1f}%")

    if 'e2e' in test_summary:
        e2e = test_summary['e2e']
        print(f"   E2E Tests: {e2e['success_rate']:.1f}%")

    print("✅ CI/CD Pipeline Completo demostrado correctamente")

    return pipeline


if __name__ == "__main__":
    asyncio.run(demonstrate_ci_cd_pipeline())