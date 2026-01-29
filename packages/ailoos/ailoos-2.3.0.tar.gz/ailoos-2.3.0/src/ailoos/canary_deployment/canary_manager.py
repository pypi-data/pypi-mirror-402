"""
Canary Deployment Manager

Gestor principal para despliegues canary, manejando el ciclo completo
de despliegue, monitoreo y finalización de versiones canary.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from .traffic_splitter import TrafficSplitter
from .metrics_analyzer import MetricsAnalyzer


class DeploymentStatus(Enum):
    """Estados posibles de un despliegue canary."""
    INITIATED = "initiated"
    TRAFFIC_SPLITTING = "traffic_splitting"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class CanaryDeployment:
    """Representa un despliegue canary."""
    deployment_id: str
    version_id: str
    target_percentage: float
    current_percentage: float = 0.0
    status: DeploymentStatus = DeploymentStatus.INITIATED
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    health_checks: List[Dict[str, Any]] = field(default_factory=list)
    rollback_triggered: bool = False


class CanaryManager:
    """
    Gestor principal de despliegues canary.

    Maneja el ciclo completo de despliegues canary incluyendo:
    - Inicio de despliegues
    - División gradual de tráfico
    - Monitoreo de métricas
    - Toma de decisiones de promoción o rollback
    - Finalización de despliegues
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el CanaryManager.

        Args:
            config: Configuración del manager
        """
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)

        # Componentes
        self.traffic_splitter = TrafficSplitter(self.config.get('traffic_splitter_config', {}))
        self.metrics_analyzer = MetricsAnalyzer(self.config.get('metrics_analyzer_config', {}))

        # Estado
        self.active_deployments: Dict[str, CanaryDeployment] = {}
        self.completed_deployments: List[CanaryDeployment] = []

        # Callbacks
        self.on_deployment_complete: Optional[Callable[[CanaryDeployment], None]] = None
        self.on_deployment_failed: Optional[Callable[[CanaryDeployment], None]] = None

        # Tareas en ejecución
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto."""
        return {
            'initial_traffic_percentage': 0.1,  # 10%
            'max_traffic_percentage': 1.0,      # 100%
            'traffic_increment_step': 0.1,      # 10% por paso
            'monitoring_interval': 30,          # segundos
            'health_check_timeout': 60,         # segundos
            'success_threshold': 0.95,          # 95% de éxito
            'failure_threshold': 0.85,          # 85% de fallo
            'auto_promotion_enabled': True,
            'auto_rollback_enabled': True,
            'traffic_splitter_config': {},
            'metrics_analyzer_config': {}
        }

    async def start_deployment(self, deployment_id: str, version_id: str,
                             target_percentage: Optional[float] = None) -> bool:
        """
        Iniciar un nuevo despliegue canary.

        Args:
            deployment_id: ID único del despliegue
            version_id: ID de la versión a desplegar
            target_percentage: Porcentaje objetivo de tráfico (opcional)

        Returns:
            True si el despliegue se inició correctamente
        """
        try:
            if deployment_id in self.active_deployments:
                self.logger.warning(f"Deployment {deployment_id} already exists")
                return False

            target_pct = target_percentage or self.config['max_traffic_percentage']
            deployment = CanaryDeployment(
                deployment_id=deployment_id,
                version_id=version_id,
                target_percentage=target_pct
            )

            self.active_deployments[deployment_id] = deployment
            self.logger.info(f"Started canary deployment {deployment_id} for version {version_id}")

            # Iniciar división de tráfico
            success = await self._start_traffic_splitting(deployment)
            if not success:
                deployment.status = DeploymentStatus.FAILED
                await self._cleanup_deployment(deployment_id)
                return False

            # Iniciar monitoreo
            await self._start_monitoring(deployment)

            return True

        except Exception as e:
            self.logger.error(f"Failed to start deployment {deployment_id}: {e}")
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id].status = DeploymentStatus.FAILED
                await self._cleanup_deployment(deployment_id)
            return False

    async def _start_traffic_splitting(self, deployment: CanaryDeployment) -> bool:
        """
        Iniciar la división gradual de tráfico.

        Args:
            deployment: El despliegue canary

        Returns:
            True si la división se inició correctamente
        """
        try:
            deployment.status = DeploymentStatus.TRAFFIC_SPLITTING

            # Configurar splitter para la versión
            await self.traffic_splitter.configure_version(
                deployment.version_id,
                initial_percentage=self.config['initial_traffic_percentage']
            )

            # Iniciar división gradual
            await self.traffic_splitter.start_gradual_split(
                deployment.version_id,
                target_percentage=deployment.target_percentage,
                step=self.config['traffic_increment_step']
            )

            deployment.current_percentage = self.config['initial_traffic_percentage']
            self.logger.info(f"Started traffic splitting for deployment {deployment.deployment_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start traffic splitting: {e}")
            return False

    async def _start_monitoring(self, deployment: CanaryDeployment):
        """
        Iniciar el monitoreo del despliegue.

        Args:
            deployment: El despliegue canary
        """
        deployment.status = DeploymentStatus.MONITORING

        # Crear tarea de monitoreo
        task = asyncio.create_task(self._monitor_deployment(deployment.deployment_id))
        self.monitoring_tasks[deployment.deployment_id] = task

        self.logger.info(f"Started monitoring for deployment {deployment.deployment_id}")

    async def _monitor_deployment(self, deployment_id: str):
        """
        Monitorear un despliegue canary.

        Args:
            deployment_id: ID del despliegue
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return

        try:
            while deployment.status == DeploymentStatus.MONITORING:
                # Obtener métricas actuales
                metrics = await self.metrics_analyzer.analyze_version(deployment.version_id)

                # Actualizar métricas del despliegue
                deployment.metrics = metrics
                deployment.health_checks.append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })

                # Evaluar estado
                health_score = self._evaluate_health(metrics)

                if health_score >= self.config['success_threshold']:
                    # Promoción automática si está habilitada
                    if self.config['auto_promotion_enabled']:
                        await self._promote_deployment(deployment)
                        break
                elif health_score <= self.config['failure_threshold']:
                    # Rollback automático si está habilitado
                    if self.config['auto_rollback_enabled']:
                        await self._rollback_deployment(deployment)
                        break

                # Actualizar porcentaje de tráfico si es necesario
                await self._adjust_traffic(deployment, health_score)

                # Esperar al siguiente intervalo
                await asyncio.sleep(self.config['monitoring_interval'])

        except Exception as e:
            self.logger.error(f"Error monitoring deployment {deployment_id}: {e}")
            deployment.status = DeploymentStatus.FAILED
            await self._cleanup_deployment(deployment_id)

    def _evaluate_health(self, metrics: Dict[str, Any]) -> float:
        """
        Evaluar la salud basada en métricas.

        Args:
            metrics: Métricas de la versión

        Returns:
            Puntaje de salud (0.0 a 1.0)
        """
        # Lógica básica de evaluación
        success_rate = metrics.get('success_rate', 0.0)
        error_rate = metrics.get('error_rate', 1.0)
        latency_score = min(1.0, 1000.0 / max(metrics.get('avg_latency', 1000.0), 1.0))

        # Puntaje compuesto
        health_score = (success_rate * 0.5) + ((1.0 - error_rate) * 0.3) + (latency_score * 0.2)
        return min(1.0, max(0.0, health_score))

    async def _promote_deployment(self, deployment: CanaryDeployment):
        """
        Promocionar un despliegue canary.

        Args:
            deployment: El despliegue a promocionar
        """
        try:
            # Aumentar tráfico al 100%
            await self.traffic_splitter.set_traffic_percentage(
                deployment.version_id,
                1.0
            )

            deployment.current_percentage = 1.0
            deployment.status = DeploymentStatus.COMPLETED
            deployment.end_time = datetime.now()

            self.logger.info(f"Promoted deployment {deployment.deployment_id}")

            # Callback
            if self.on_deployment_complete:
                self.on_deployment_complete(deployment)

            await self._cleanup_deployment(deployment.deployment_id)

        except Exception as e:
            self.logger.error(f"Failed to promote deployment {deployment.deployment_id}: {e}")
            await self._rollback_deployment(deployment)

    async def _rollback_deployment(self, deployment: CanaryDeployment):
        """
        Hacer rollback de un despliegue canary.

        Args:
            deployment: El despliegue a rollback
        """
        try:
            # Reducir tráfico a 0
            await self.traffic_splitter.set_traffic_percentage(
                deployment.version_id,
                0.0
            )

            deployment.current_percentage = 0.0
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.rollback_triggered = True
            deployment.end_time = datetime.now()

            self.logger.warning(f"Rolled back deployment {deployment.deployment_id}")

            # Callback
            if self.on_deployment_failed:
                self.on_deployment_failed(deployment)

            await self._cleanup_deployment(deployment.deployment_id)

        except Exception as e:
            self.logger.error(f"Failed to rollback deployment {deployment.deployment_id}: {e}")

    async def _adjust_traffic(self, deployment: CanaryDeployment, health_score: float):
        """
        Ajustar el porcentaje de tráfico basado en la salud.

        Args:
            deployment: El despliegue
            health_score: Puntaje de salud actual
        """
        try:
            current_pct = deployment.current_percentage
            target_pct = deployment.target_percentage

            if health_score >= self.config['success_threshold'] and current_pct < target_pct:
                # Aumentar tráfico gradualmente
                new_pct = min(current_pct + self.config['traffic_increment_step'], target_pct)
                await self.traffic_splitter.set_traffic_percentage(
                    deployment.version_id,
                    new_pct
                )
                deployment.current_percentage = new_pct
                self.logger.info(f"Increased traffic for {deployment.deployment_id} to {new_pct:.1%}")

            elif health_score <= self.config['failure_threshold'] and current_pct > 0:
                # Reducir tráfico si hay problemas
                new_pct = max(current_pct - self.config['traffic_increment_step'], 0.0)
                await self.traffic_splitter.set_traffic_percentage(
                    deployment.version_id,
                    new_pct
                )
                deployment.current_percentage = new_pct
                self.logger.warning(f"Decreased traffic for {deployment.deployment_id} to {new_pct:.1%}")

        except Exception as e:
            self.logger.error(f"Failed to adjust traffic for {deployment.deployment_id}: {e}")

    async def complete_deployment(self, deployment_id: str, success: bool = True) -> bool:
        """
        Completar manualmente un despliegue canary.

        Args:
            deployment_id: ID del despliegue
            success: Si el despliegue fue exitoso

        Returns:
            True si se completó correctamente
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            self.logger.warning(f"Deployment {deployment_id} not found")
            return False

        try:
            if success:
                await self._promote_deployment(deployment)
            else:
                await self._rollback_deployment(deployment)

            return True

        except Exception as e:
            self.logger.error(f"Failed to complete deployment {deployment_id}: {e}")
            return False

    async def _cleanup_deployment(self, deployment_id: str):
        """
        Limpiar recursos de un despliegue.

        Args:
            deployment_id: ID del despliegue
        """
        # Cancelar tarea de monitoreo
        if deployment_id in self.monitoring_tasks:
            self.monitoring_tasks[deployment_id].cancel()
            del self.monitoring_tasks[deployment_id]

        # Mover a completados
        if deployment_id in self.active_deployments:
            deployment = self.active_deployments[deployment_id]
            self.completed_deployments.append(deployment)
            del self.active_deployments[deployment_id]

            # Mantener solo los últimos N despliegues
            if len(self.completed_deployments) > 100:
                self.completed_deployments = self.completed_deployments[-100:]

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener el estado de un despliegue.

        Args:
            deployment_id: ID del despliegue

        Returns:
            Estado del despliegue o None si no existe
        """
        deployment = self.active_deployments.get(deployment_id)
        if deployment:
            return {
                'deployment_id': deployment.deployment_id,
                'version_id': deployment.version_id,
                'status': deployment.status.value,
                'current_percentage': deployment.current_percentage,
                'target_percentage': deployment.target_percentage,
                'start_time': deployment.start_time.isoformat(),
                'end_time': deployment.end_time.isoformat() if deployment.end_time else None,
                'metrics': deployment.metrics,
                'health_checks_count': len(deployment.health_checks),
                'rollback_triggered': deployment.rollback_triggered
            }

        # Buscar en completados
        for dep in self.completed_deployments:
            if dep.deployment_id == deployment_id:
                return {
                    'deployment_id': dep.deployment_id,
                    'version_id': dep.version_id,
                    'status': dep.status.value,
                    'current_percentage': dep.current_percentage,
                    'target_percentage': dep.target_percentage,
                    'start_time': dep.start_time.isoformat(),
                    'end_time': dep.end_time.isoformat() if dep.end_time else None,
                    'metrics': dep.metrics,
                    'health_checks_count': len(dep.health_checks),
                    'rollback_triggered': dep.rollback_triggered
                }

        return None

    def get_active_deployments(self) -> List[Dict[str, Any]]:
        """
        Obtener lista de despliegues activos.

        Returns:
            Lista de despliegues activos
        """
        return [
            self.get_deployment_status(dep_id)
            for dep_id in self.active_deployments.keys()
        ]

    async def shutdown(self):
        """
        Apagar el manager y cancelar todas las tareas.
        """
        self.logger.info("Shutting down CanaryManager")

        # Cancelar todas las tareas de monitoreo
        for task in self.monitoring_tasks.values():
            task.cancel()

        # Esperar a que terminen
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)

        # Limpiar estado
        self.monitoring_tasks.clear()
        self.active_deployments.clear()

        self.logger.info("CanaryManager shutdown complete")