"""
Unlearning Scheduler - Programador automático de unlearning basado en políticas de retención.

Programa y ejecuta operaciones de unlearning automáticamente según políticas de retención,
cumplimiento normativo, y triggers de eventos del sistema.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
import logging
from dataclasses import dataclass, field
from enum import Enum
import json

from ...utils.logging import get_logger
from ...compliance.unlearning import ZeroShotUnlearningSystem, UnlearningTarget
from ...compliance.privacy_auditor import PrivacyAuditor
from .miras_block import MIRASBlock

logger = get_logger(__name__)


class UnlearningTrigger(Enum):
    """Triggers para activar unlearning automático."""
    TIME_BASED = "time_based"  # Basado en tiempo de retención
    GDPR_RETENTION = "gdpr_retention"  # Cumplimiento GDPR
    DATA_QUALITY = "data_quality"  # Calidad de datos baja
    MEMORY_PRESSURE = "memory_pressure"  # Presión de memoria
    USER_REQUEST = "user_request"  # Solicitud de usuario
    COMPLIANCE_AUDIT = "compliance_audit"  # Auditoría de compliance
    MANUAL = "manual"  # Manual


class RetentionPolicy(Enum):
    """Políticas de retención de datos."""
    GDPR_DEFAULT = "gdpr_default"  # 2 años para datos personales
    FINANCIAL_RECORDS = "financial_records"  # 7 años
    HEALTH_DATA = "health_data"  # 10 años o más
    SESSION_DATA = "session_data"  # 30 días
    TEMPORARY_CACHE = "temporary_cache"  # 24 horas
    INDEFINITE = "indefinite"  # Sin límite


@dataclass
class UnlearningJob:
    """Trabajo de unlearning programado."""
    job_id: str
    target_id: str
    trigger: UnlearningTrigger
    retention_policy: RetentionPolicy
    scheduled_time: datetime
    data_samples: List[Any]  # Datos a olvidar
    labels: Optional[List[Any]] = None
    user_id: Optional[str] = None
    priority: int = 1  # 1-5, 5 es más alta
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = None
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class RetentionRule:
    """Regla de retención de datos."""
    rule_id: str
    name: str
    retention_policy: RetentionPolicy
    data_categories: List[str]
    trigger_conditions: Dict[str, Any]
    auto_unlearning: bool = True
    notification_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnlearningScheduler:
    """
    Programador automático de operaciones de unlearning.

    Gestiona la programación, ejecución y monitoreo de operaciones de unlearning
    basadas en políticas de retención y triggers del sistema.
    """

    def __init__(
        self,
        unlearning_system: ZeroShotUnlearningSystem,
        miras_blocks: Optional[List[MIRASBlock]] = None,
        privacy_auditor: Optional[PrivacyAuditor] = None,
        check_interval_seconds: int = 300  # 5 minutos
    ):
        self.unlearning_system = unlearning_system
        self.miras_blocks = miras_blocks or []
        self.privacy_auditor = privacy_auditor
        self.check_interval_seconds = check_interval_seconds

        # Gestión de trabajos
        self.pending_jobs: Dict[str, UnlearningJob] = {}
        self.completed_jobs: List[UnlearningJob] = []
        self.failed_jobs: List[UnlearningJob] = []

        # Reglas de retención
        self.retention_rules: Dict[str, RetentionRule] = {}
        self._initialize_default_retention_rules()

        # Estado del scheduler
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_check_time = datetime.now()

        # Estadísticas
        self.stats = {
            "jobs_scheduled": 0,
            "jobs_executed": 0,
            "jobs_failed": 0,
            "data_points_forgotten": 0,
            "average_execution_time": 0.0,
            "uptime_seconds": 0
        }

        logger.info("🚀 UnlearningScheduler inicializado")

    def start(self):
        """Iniciar el scheduler."""
        if self.running:
            logger.warning("Scheduler ya está ejecutándose")
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        logger.info("✅ UnlearningScheduler iniciado")

    def stop(self):
        """Detener el scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        logger.info("🛑 UnlearningScheduler detenido")

    def schedule_unlearning_job(
        self,
        target_id: str,
        data_samples: List[Any],
        trigger: UnlearningTrigger,
        retention_policy: RetentionPolicy,
        scheduled_time: Optional[datetime] = None,
        labels: Optional[List[Any]] = None,
        user_id: Optional[str] = None,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Programar un trabajo de unlearning.

        Args:
            target_id: ID único del target
            data_samples: Datos a olvidar
            trigger: Trigger que activa el unlearning
            retention_policy: Política de retención
            scheduled_time: Tiempo programado (opcional, default: inmediato)
            labels: Labels correspondientes
            user_id: ID del usuario
            priority: Prioridad del trabajo
            metadata: Metadatos adicionales

        Returns:
            ID del trabajo programado
        """
        if scheduled_time is None:
            scheduled_time = datetime.now()

        job_id = f"job_{target_id}_{datetime.now().timestamp()}"

        job = UnlearningJob(
            job_id=job_id,
            target_id=target_id,
            trigger=trigger,
            retention_policy=retention_policy,
            scheduled_time=scheduled_time,
            data_samples=data_samples,
            labels=labels,
            user_id=user_id,
            priority=priority,
            metadata=metadata or {}
        )

        self.pending_jobs[job_id] = job
        self.stats["jobs_scheduled"] += 1

        logger.info(f"📅 Trabajo de unlearning programado: {job_id} para {scheduled_time}")
        return job_id

    def schedule_retention_based_unlearning(
        self,
        data_category: str,
        user_id: Optional[str] = None,
        custom_retention_days: Optional[int] = None
    ) -> List[str]:
        """
        Programar unlearning basado en políticas de retención.

        Args:
            data_category: Categoría de datos
            user_id: ID del usuario (opcional)
            custom_retention_days: Días de retención personalizados

        Returns:
            Lista de IDs de trabajos programados
        """
        job_ids = []

        # Encontrar reglas aplicables
        applicable_rules = [
            rule for rule in self.retention_rules.values()
            if data_category in rule.data_categories
        ]

        for rule in applicable_rules:
            # Calcular tiempo de ejecución basado en política
            retention_days = custom_retention_days
            if retention_days is None:
                retention_days = self._get_retention_days(rule.retention_policy)

            scheduled_time = datetime.now() + timedelta(days=retention_days)

            # Crear datos dummy (en producción, recuperar datos reales)
            dummy_samples = [f"data_{data_category}_{user_id or 'system'}_{i}" for i in range(5)]

            job_id = self.schedule_unlearning_job(
                target_id=f"retention_{data_category}_{user_id or 'system'}_{datetime.now().timestamp()}",
                data_samples=dummy_samples,
                trigger=UnlearningTrigger.TIME_BASED,
                retention_policy=rule.retention_policy,
                scheduled_time=scheduled_time,
                user_id=user_id,
                priority=2,
                metadata={
                    "data_category": data_category,
                    "retention_rule": rule.rule_id,
                    "retention_days": retention_days
                }
            )

            job_ids.append(job_id)

        logger.info(f"📅 Programados {len(job_ids)} trabajos de retención para {data_category}")
        return job_ids

    def trigger_immediate_unlearning(
        self,
        target_id: str,
        data_samples: List[Any],
        trigger: UnlearningTrigger,
        user_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Trigger unlearning inmediato (alta prioridad).

        Args:
            target_id: ID del target
            data_samples: Datos a olvidar
            trigger: Trigger que activa el unlearning
            user_id: ID del usuario
            priority: Prioridad (default: máxima)

        Returns:
            ID del trabajo
        """
        return self.schedule_unlearning_job(
            target_id=target_id,
            data_samples=data_samples,
            trigger=trigger,
            retention_policy=RetentionPolicy.SESSION_DATA,  # Irrelevante para inmediato
            scheduled_time=datetime.now(),  # Inmediato
            user_id=user_id,
            priority=priority,
            metadata={"immediate": True, "trigger_reason": trigger.value}
        )

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un trabajo."""
        # Buscar en pendientes
        if job_id in self.pending_jobs:
            job = self.pending_jobs[job_id]
            return {
                "job_id": job.job_id,
                "status": job.status,
                "scheduled_time": job.scheduled_time.isoformat(),
                "priority": job.priority,
                "created_at": job.created_at.isoformat()
            }

        # Buscar en completados
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return {
                    "job_id": job.job_id,
                    "status": job.status,
                    "executed_at": job.executed_at.isoformat() if job.executed_at else None,
                    "result": job.result,
                    "created_at": job.created_at.isoformat()
                }

        # Buscar en fallidos
        for job in self.failed_jobs:
            if job.job_id == job_id:
                return {
                    "job_id": job.job_id,
                    "status": job.status,
                    "executed_at": job.executed_at.isoformat() if job.executed_at else None,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat()
                }

        return None

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del scheduler."""
        return {
            **self.stats,
            "pending_jobs": len(self.pending_jobs),
            "completed_jobs": len(self.completed_jobs),
            "failed_jobs": len(self.failed_jobs),
            "active_retention_rules": len(self.retention_rules),
            "miras_blocks_monitored": len(self.miras_blocks),
            "last_check_time": self.last_check_time.isoformat(),
            "scheduler_running": self.running
        }

    def add_retention_rule(
        self,
        rule_id: str,
        name: str,
        retention_policy: RetentionPolicy,
        data_categories: List[str],
        trigger_conditions: Dict[str, Any],
        auto_unlearning: bool = True
    ) -> bool:
        """
        Agregar regla de retención personalizada.

        Args:
            rule_id: ID único de la regla
            name: Nombre descriptivo
            retention_policy: Política de retención
            data_categories: Categorías de datos aplicables
            trigger_conditions: Condiciones para activar
            auto_unlearning: Si activar unlearning automático

        Returns:
            True si se agregó exitosamente
        """
        if rule_id in self.retention_rules:
            logger.warning(f"Regla de retención {rule_id} ya existe")
            return False

        rule = RetentionRule(
            rule_id=rule_id,
            name=name,
            retention_policy=retention_policy,
            data_categories=data_categories,
            trigger_conditions=trigger_conditions,
            auto_unlearning=auto_unlearning
        )

        self.retention_rules[rule_id] = rule
        logger.info(f"📋 Regla de retención agregada: {rule_id}")
        return True

    def _scheduler_loop(self):
        """Loop principal del scheduler."""
        logger.info("🔄 Iniciando loop del scheduler")

        while self.running:
            try:
                self._check_pending_jobs()
                self._check_retention_triggers()
                self._cleanup_old_jobs()

                self.last_check_time = datetime.now()
                time.sleep(self.check_interval_seconds)

            except Exception as e:
                logger.error(f"Error en loop del scheduler: {str(e)}")
                time.sleep(self.check_interval_seconds)

        logger.info("🔄 Loop del scheduler terminado")

    def _check_pending_jobs(self):
        """Verificar y ejecutar trabajos pendientes."""
        current_time = datetime.now()
        jobs_to_execute = []

        # Encontrar trabajos listos para ejecutar
        for job_id, job in list(self.pending_jobs.items()):
            if job.scheduled_time <= current_time:
                jobs_to_execute.append((job_id, job))

        # Ordenar por prioridad (mayor primero)
        jobs_to_execute.sort(key=lambda x: x[1].priority, reverse=True)

        # Ejecutar trabajos
        for job_id, job in jobs_to_execute:
            try:
                job.status = "running"
                job.executed_at = current_time

                logger.info(f"⚡ Ejecutando trabajo de unlearning: {job_id}")

                # Ejecutar unlearning
                result = self._execute_unlearning_job(job)

                # Actualizar estado
                job.status = "completed"
                job.result = result
                self.completed_jobs.append(job)
                del self.pending_jobs[job_id]

                self.stats["jobs_executed"] += 1
                self.stats["data_points_forgotten"] += len(job.data_samples)

                logger.info(f"✅ Trabajo completado: {job_id}")

            except Exception as e:
                job.status = "failed"
                job.error_message = str(e)
                self.failed_jobs.append(job)
                del self.pending_jobs[job_id]

                self.stats["jobs_failed"] += 1
                logger.error(f"❌ Trabajo fallido {job_id}: {str(e)}")

    def _execute_unlearning_job(self, job: UnlearningJob) -> Dict[str, Any]:
        """Ejecutar un trabajo de unlearning."""
        start_time = time.time()

        # Enviar a sistema de unlearning
        request_id = self.unlearning_system.submit_unlearning_request(
            target_id=job.target_id,
            data_samples=job.data_samples,
            labels=job.labels,
            user_id=job.user_id,
            metadata={
                **job.metadata,
                "job_id": job.job_id,
                "trigger": job.trigger.value,
                "retention_policy": job.retention_policy.value
            }
        )

        # Esperar resultado (en producción, esto sería asíncrono)
        result = self.unlearning_system.get_unlearning_status(request_id)

        execution_time = time.time() - start_time

        # Actualizar estadísticas de tiempo
        if self.stats["jobs_executed"] > 0:
            self.stats["average_execution_time"] = (
                (self.stats["average_execution_time"] * (self.stats["jobs_executed"] - 1)) +
                execution_time
            ) / self.stats["jobs_executed"]

        return {
            "request_id": request_id,
            "success": result.success if result else False,
            "effectiveness_score": result.effectiveness_score if result else 0.0,
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }

    def _check_retention_triggers(self):
        """Verificar triggers de retención automática."""
        # Esta implementación verificaría bases de datos y logs
        # para encontrar datos que excedan sus períodos de retención

        # Por ahora, simular algunos triggers
        current_time = datetime.now()

        # Simular trigger de datos antiguos
        if current_time.second % 30 == 0:  # Cada 30 segundos aproximadamente
            self._trigger_retention_cleanup("session_data")

    def _trigger_retention_cleanup(self, data_category: str):
        """Trigger limpieza de retención para una categoría."""
        logger.info(f"🧹 Triggering retention cleanup for {data_category}")

        # Programar trabajos de limpieza
        job_ids = self.schedule_retention_based_unlearning(
            data_category=data_category,
            custom_retention_days=0  # Inmediato
        )

        if job_ids:
            logger.info(f"📅 Programados {len(job_ids)} trabajos de limpieza para {data_category}")

    def _cleanup_old_jobs(self):
        """Limpiar trabajos antiguos completados/fallidos."""
        cutoff_date = datetime.now() - timedelta(days=30)  # Mantener 30 días

        # Limpiar completados antiguos
        self.completed_jobs = [
            job for job in self.completed_jobs
            if job.executed_at and job.executed_at > cutoff_date
        ]

        # Limpiar fallidos antiguos
        self.failed_jobs = [
            job for job in self.failed_jobs
            if job.executed_at and job.executed_at > cutoff_date
        ]

    def _initialize_default_retention_rules(self):
        """Inicializar reglas de retención por defecto."""
        default_rules = [
            RetentionRule(
                rule_id="gdpr_personal_data",
                name="GDPR Personal Data Retention",
                retention_policy=RetentionPolicy.GDPR_DEFAULT,
                data_categories=["personal_data", "contact_info", "user_profile"],
                trigger_conditions={"retention_days": 730},  # 2 años
                auto_unlearning=True
            ),
            RetentionRule(
                rule_id="session_data_cleanup",
                name="Session Data Cleanup",
                retention_policy=RetentionPolicy.SESSION_DATA,
                data_categories=["session_logs", "temporary_cache", "user_sessions"],
                trigger_conditions={"retention_days": 30},
                auto_unlearning=True
            ),
            RetentionRule(
                rule_id="financial_records",
                name="Financial Records Retention",
                retention_policy=RetentionPolicy.FINANCIAL_RECORDS,
                data_categories=["financial_data", "transaction_logs", "payment_info"],
                trigger_conditions={"retention_days": 2555},  # 7 años
                auto_unlearning=True
            ),
            RetentionRule(
                rule_id="health_data_retention",
                name="Health Data Retention",
                retention_policy=RetentionPolicy.HEALTH_DATA,
                data_categories=["health_records", "medical_data", "diagnosis_info"],
                trigger_conditions={"retention_days": 3650},  # 10 años
                auto_unlearning=True
            )
        ]

        for rule in default_rules:
            self.retention_rules[rule.rule_id] = rule

        logger.info(f"📋 Inicializadas {len(default_rules)} reglas de retención por defecto")

    def _get_retention_days(self, policy: RetentionPolicy) -> int:
        """Obtener días de retención para una política."""
        policy_days = {
            RetentionPolicy.GDPR_DEFAULT: 730,  # 2 años
            RetentionPolicy.FINANCIAL_RECORDS: 2555,  # 7 años
            RetentionPolicy.HEALTH_DATA: 3650,  # 10 años
            RetentionPolicy.SESSION_DATA: 30,  # 30 días
            RetentionPolicy.TEMPORARY_CACHE: 1,  # 24 horas
            RetentionPolicy.INDEFINITE: 99999  # Efectivamente infinito
        }

        return policy_days.get(policy, 730)  # Default a 2 años


def create_unlearning_scheduler(
    unlearning_system: ZeroShotUnlearningSystem,
    miras_blocks: Optional[List[MIRASBlock]] = None,
    privacy_auditor: Optional[PrivacyAuditor] = None,
    check_interval_seconds: int = 300
) -> UnlearningScheduler:
    """
    Factory function para crear scheduler de unlearning.

    Args:
        unlearning_system: Sistema de unlearning
        miras_blocks: Bloques MIRAS a monitorear
        privacy_auditor: Auditor de privacidad
        check_interval_seconds: Intervalo de verificación

    Returns:
        UnlearningScheduler configurado
    """
    return UnlearningScheduler(
        unlearning_system=unlearning_system,
        miras_blocks=miras_blocks,
        privacy_auditor=privacy_auditor,
        check_interval_seconds=check_interval_seconds
    )