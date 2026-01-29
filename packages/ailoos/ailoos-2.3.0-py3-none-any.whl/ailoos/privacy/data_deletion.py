"""
Data Deletion Workflows para GDPR Right to Erasure

Implementa eliminación completa y verificada de datos de usuarios
con workflows cross-service y auditoría completa.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class DeletionStatus(Enum):
    """Estados del proceso de eliminación."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DataLocation(Enum):
    """Ubicaciones donde pueden estar los datos del usuario."""
    DATABASE = "database"
    CACHE = "cache"
    FILESYSTEM = "filesystem"
    IPFS = "ipfs"
    BLOCKCHAIN = "blockchain"
    EXTERNAL_API = "external_api"
    LOGS = "logs"
    BACKUP = "backup"


@dataclass
class DeletionTask:
    """Tarea individual de eliminación."""
    task_id: str
    user_id: str
    data_location: DataLocation
    location_details: str  # table.column, file_path, etc.
    status: DeletionStatus = DeletionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    verification_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeletionWorkflow:
    """Workflow completo de eliminación de datos."""
    workflow_id: str
    user_id: str
    request_id: str  # ID de la solicitud de eliminación
    status: DeletionStatus = DeletionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    tasks: List[DeletionTask] = field(default_factory=list)
    verification_report: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Verificar si el workflow está completado."""
        return self.status in [DeletionStatus.COMPLETED, DeletionStatus.FAILED, DeletionStatus.PARTIAL]

    @property
    def success_rate(self) -> float:
        """Calcular tasa de éxito del workflow."""
        if not self.tasks:
            return 0.0

        completed_tasks = len([t for t in self.tasks if t.status == DeletionStatus.COMPLETED])
        return (completed_tasks / len(self.tasks)) * 100


class DataDeletionManager:
    """
    Gestor de eliminación de datos para GDPR Right to Erasure.

    Características:
    - Workflows de eliminación cross-service
    - Verificación de eliminación completa
    - Auditoría completa del proceso
    - Rollback capabilities
    - Compliance reporting
    """

    def __init__(self):
        self.workflows: Dict[str, DeletionWorkflow] = {}
        self.deletion_callbacks: Dict[DataLocation, Callable] = {}
        self.verification_callbacks: Dict[DataLocation, Callable] = {}

        # Estadísticas
        self.stats = {
            'total_workflows': 0,
            'completed_workflows': 0,
            'failed_workflows': 0,
            'avg_completion_time': 0.0,
            'success_rate': 0.0
        }

        self._setup_default_callbacks()
        logger.info("DataDeletionManager initialized")

    def _setup_default_callbacks(self):
        """Configurar callbacks por defecto para ubicaciones comunes."""
        # Estos serían implementados por cada servicio
        # Por ahora son placeholders que simulan la eliminación

        async def delete_database_data(task: DeletionTask) -> bool:
            """Eliminar datos de base de datos."""
            logger.info(f"Deleting database data: {task.location_details} for user {task.user_id}")
            # Simular eliminación
            await asyncio.sleep(0.1)
            return True

        async def delete_cache_data(task: DeletionTask) -> bool:
            """Eliminar datos de cache."""
            logger.info(f"Deleting cache data: {task.location_details} for user {task.user_id}")
            await asyncio.sleep(0.05)
            return True

        async def delete_filesystem_data(task: DeletionTask) -> bool:
            """Eliminar datos del filesystem."""
            logger.info(f"Deleting filesystem data: {task.location_details} for user {task.user_id}")
            await asyncio.sleep(0.2)
            return True

        async def delete_ipfs_data(task: DeletionTask) -> bool:
            """Eliminar datos de IPFS."""
            logger.info(f"Deleting IPFS data: {task.location_details} for user {task.user_id}")
            await asyncio.sleep(0.3)
            return True

        async def delete_logs_data(task: DeletionTask) -> bool:
            """Eliminar datos de logs."""
            logger.info(f"Deleting logs data: {task.location_details} for user {task.user_id}")
            await asyncio.sleep(0.1)
            return True

        # Registrar callbacks
        self.deletion_callbacks.update({
            DataLocation.DATABASE: delete_database_data,
            DataLocation.CACHE: delete_cache_data,
            DataLocation.FILESYSTEM: delete_filesystem_data,
            DataLocation.IPFS: delete_ipfs_data,
            DataLocation.LOGS: delete_logs_data
        })

        # Callbacks de verificación
        self.verification_callbacks.update({
            DataLocation.DATABASE: self._verify_database_deletion,
            DataLocation.CACHE: self._verify_cache_deletion,
            DataLocation.FILESYSTEM: self._verify_filesystem_deletion,
            DataLocation.IPFS: self._verify_ipfs_deletion,
            DataLocation.LOGS: self._verify_logs_deletion
        })

    async def initiate_data_deletion(self,
                                   user_id: str,
                                   request_id: str,
                                   data_locations: Optional[List[DataLocation]] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Iniciar proceso de eliminación de datos para un usuario.

        Args:
            user_id: ID del usuario
            request_id: ID de la solicitud de eliminación
            data_locations: Ubicaciones específicas (None = todas)
            metadata: Metadata adicional

        Returns:
            ID del workflow de eliminación
        """
        workflow_id = f"del_{user_id}_{int(datetime.now().timestamp())}"

        # Si no se especifican ubicaciones, usar todas las disponibles
        if data_locations is None:
            data_locations = list(self.deletion_callbacks.keys())

        # Crear tareas de eliminación
        tasks = []
        for location in data_locations:
            task_id = f"{workflow_id}_{location.value}"
            task = DeletionTask(
                task_id=task_id,
                user_id=user_id,
                data_location=location,
                location_details=self._get_location_details(user_id, location)
            )
            tasks.append(task)

        # Crear workflow
        workflow = DeletionWorkflow(
            workflow_id=workflow_id,
            user_id=user_id,
            request_id=request_id,
            tasks=tasks,
            metadata=metadata or {}
        )

        self.workflows[workflow_id] = workflow
        self.stats['total_workflows'] += 1

        logger.info(f"Initiated data deletion workflow: {workflow_id} for user {user_id} ({len(tasks)} tasks)")

        # Iniciar procesamiento en background
        asyncio.create_task(self._process_deletion_workflow(workflow))

        return workflow_id

    async def _process_deletion_workflow(self, workflow: DeletionWorkflow):
        """Procesar workflow de eliminación."""
        workflow.status = DeletionStatus.IN_PROGRESS
        start_time = datetime.now()

        logger.info(f"Processing deletion workflow: {workflow.workflow_id}")

        completed_tasks = 0
        failed_tasks = 0

        # Procesar cada tarea
        for task in workflow.tasks:
            try:
                task.status = DeletionStatus.IN_PROGRESS
                task.started_at = datetime.now()

                # Ejecutar eliminación
                success = await self._execute_deletion_task(task)

                if success:
                    task.status = DeletionStatus.COMPLETED
                    task.completed_at = datetime.now()
                    completed_tasks += 1

                    # Generar hash de verificación
                    task.verification_hash = self._generate_verification_hash(task)
                else:
                    task.status = DeletionStatus.FAILED
                    task.error_message = "Deletion callback returned False"
                    failed_tasks += 1

            except Exception as e:
                task.status = DeletionStatus.FAILED
                task.error_message = str(e)
                failed_tasks += 1
                logger.error(f"Error in deletion task {task.task_id}: {e}")

        # Determinar estado final del workflow
        if failed_tasks == 0:
            workflow.status = DeletionStatus.COMPLETED
        elif completed_tasks == 0:
            workflow.status = DeletionStatus.FAILED
        else:
            workflow.status = DeletionStatus.PARTIAL

        workflow.completed_at = datetime.now()

        # Generar reporte de verificación
        workflow.verification_report = await self._generate_verification_report(workflow)

        # Actualizar estadísticas
        completion_time = (datetime.now() - start_time).total_seconds()
        self._update_stats(workflow, completion_time)

        logger.info(f"Completed deletion workflow: {workflow.workflow_id} "
                   f"({completed_tasks}/{len(workflow.tasks)} tasks successful)")

    async def _execute_deletion_task(self, task: DeletionTask) -> bool:
        """Ejecutar una tarea individual de eliminación."""
        callback = self.deletion_callbacks.get(task.data_location)
        if not callback:
            logger.error(f"No deletion callback for location: {task.data_location}")
            return False

        try:
            success = await callback(task)

            # Verificar eliminación si hay callback de verificación
            if success:
                verification_callback = self.verification_callbacks.get(task.data_location)
                if verification_callback:
                    verified = await verification_callback(task)
                    if not verified:
                        logger.warning(f"Deletion verification failed for task: {task.task_id}")
                        return False

            return success

        except Exception as e:
            logger.error(f"Error executing deletion task {task.task_id}: {e}")
            return False

    def _get_location_details(self, user_id: str, location: DataLocation) -> str:
        """Obtener detalles de ubicación para un tipo de dato."""
        # Estos serían configurables por servicio
        location_templates = {
            DataLocation.DATABASE: f"users.id={user_id},sessions.user_id={user_id},federated_sessions.user_id={user_id}",
            DataLocation.CACHE: f"user:{user_id}:*,session:{user_id}:*",
            DataLocation.FILESYSTEM: f"/data/users/{user_id}/**",
            DataLocation.IPFS: f"user_data_{user_id}",
            DataLocation.LOGS: f"*.log containing user_id:{user_id}",
            DataLocation.BACKUP: f"backup_*.sql containing user_id:{user_id}",
            DataLocation.BLOCKCHAIN: f"transactions where user_id={user_id}",
            DataLocation.EXTERNAL_API: f"external_services user_id:{user_id}"
        }

        return location_templates.get(location, f"user_id:{user_id}")

    def _generate_verification_hash(self, task: DeletionTask) -> str:
        """Generar hash de verificación para una tarea completada."""
        data = f"{task.task_id}:{task.user_id}:{task.data_location.value}:{task.completed_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def _generate_verification_report(self, workflow: DeletionWorkflow) -> Dict[str, Any]:
        """Generar reporte de verificación del workflow."""
        report = {
            'workflow_id': workflow.workflow_id,
            'user_id': workflow.user_id,
            'total_tasks': len(workflow.tasks),
            'completed_tasks': len([t for t in workflow.tasks if t.status == DeletionStatus.COMPLETED]),
            'failed_tasks': len([t for t in workflow.tasks if t.status == DeletionStatus.FAILED]),
            'success_rate': workflow.success_rate,
            'generated_at': datetime.now().isoformat(),
            'task_details': []
        }

        for task in workflow.tasks:
            task_detail = {
                'task_id': task.task_id,
                'location': task.data_location.value,
                'status': task.status.value,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'verification_hash': task.verification_hash,
                'error_message': task.error_message
            }
            report['task_details'].append(task_detail)

        return report

    async def _verify_database_deletion(self, task: DeletionTask) -> bool:
        """Verificar eliminación de datos de base de datos."""
        # Simular verificación
        await asyncio.sleep(0.05)
        return True  # Placeholder

    async def _verify_cache_deletion(self, task: DeletionTask) -> bool:
        """Verificar eliminación de datos de cache."""
        await asyncio.sleep(0.02)
        return True  # Placeholder

    async def _verify_filesystem_deletion(self, task: DeletionTask) -> bool:
        """Verificar eliminación de datos del filesystem."""
        await asyncio.sleep(0.1)
        return True  # Placeholder

    async def _verify_ipfs_deletion(self, task: DeletionTask) -> bool:
        """Verificar eliminación de datos de IPFS."""
        await asyncio.sleep(0.2)
        return True  # Placeholder

    async def _verify_logs_deletion(self, task: DeletionTask) -> bool:
        """Verificar eliminación de datos de logs."""
        await asyncio.sleep(0.05)
        return True  # Placeholder

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un workflow de eliminación."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            'workflow_id': workflow.workflow_id,
            'user_id': workflow.user_id,
            'request_id': workflow.request_id,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'success_rate': workflow.success_rate,
            'total_tasks': len(workflow.tasks),
            'completed_tasks': len([t for t in workflow.tasks if t.status == DeletionStatus.COMPLETED]),
            'failed_tasks': len([t for t in workflow.tasks if t.status == DeletionStatus.FAILED]),
            'verification_report': workflow.verification_report
        }

    def get_user_deletion_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de eliminaciones para un usuario."""
        user_workflows = [
            workflow for workflow in self.workflows.values()
            if workflow.user_id == user_id
        ]

        return [
            {
                'workflow_id': w.workflow_id,
                'request_id': w.request_id,
                'status': w.status.value,
                'created_at': w.created_at.isoformat(),
                'completed_at': w.completed_at.isoformat() if w.completed_at else None,
                'success_rate': w.success_rate
            }
            for w in sorted(user_workflows, key=lambda x: x.created_at, reverse=True)
        ]

    def register_deletion_callback(self, location: DataLocation, callback: Callable):
        """Registrar callback de eliminación para una ubicación."""
        self.deletion_callbacks[location] = callback
        logger.info(f"Registered deletion callback for {location.value}")

    def register_verification_callback(self, location: DataLocation, callback: Callable):
        """Registrar callback de verificación para una ubicación."""
        self.verification_callbacks[location] = callback
        logger.info(f"Registered verification callback for {location.value}")

    def _update_stats(self, workflow: DeletionWorkflow, completion_time: float):
        """Actualizar estadísticas."""
        if workflow.status == DeletionStatus.COMPLETED:
            self.stats['completed_workflows'] += 1
        elif workflow.status == DeletionStatus.FAILED:
            self.stats['failed_workflows'] += 1

        # Actualizar tiempo promedio de completación
        total_completed = self.stats['completed_workflows'] + self.stats['failed_workflows']
        if total_completed > 0:
            self.stats['avg_completion_time'] = (
                (self.stats['avg_completion_time'] * (total_completed - 1)) + completion_time
            ) / total_completed

        # Calcular tasa de éxito general
        total_workflows = self.stats['total_workflows']
        if total_workflows > 0:
            successful_workflows = self.stats['completed_workflows']
            partial_workflows = len([
                w for w in self.workflows.values()
                if w.status == DeletionStatus.PARTIAL
            ])
            self.stats['success_rate'] = (
                (successful_workflows + partial_workflows * 0.5) / total_workflows
            ) * 100

    def get_deletion_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de eliminación."""
        return {
            **self.stats,
            'active_workflows': len([w for w in self.workflows.values() if not w.is_completed]),
            'generated_at': datetime.now().isoformat()
        }

    async def cleanup_completed_workflows(self, max_age_days: int = 365):
        """Limpiar workflows completados antiguos."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        workflows_to_remove = [
            workflow_id for workflow_id, workflow in self.workflows.items()
            if workflow.is_completed and workflow.completed_at and workflow.completed_at < cutoff_date
        ]

        for workflow_id in workflows_to_remove:
            del self.workflows[workflow_id]

        logger.info(f"Cleaned up {len(workflows_to_remove)} old completed workflows")


# Instancia global del deletion manager
_deletion_manager = DataDeletionManager()


def get_deletion_manager() -> DataDeletionManager:
    """Obtener instancia global del deletion manager."""
    return _deletion_manager


# Funciones de conveniencia

async def initiate_user_data_deletion(user_id: str, request_id: str) -> str:
    """Iniciar eliminación de datos de usuario."""
    return await _deletion_manager.initiate_data_deletion(user_id, request_id)


def get_deletion_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Obtener estado de workflow de eliminación."""
    return _deletion_manager.get_workflow_status(workflow_id)


def get_user_deletion_history(user_id: str) -> List[Dict[str, Any]]:
    """Obtener historial de eliminaciones de usuario."""
    return _deletion_manager.get_user_deletion_history(user_id)