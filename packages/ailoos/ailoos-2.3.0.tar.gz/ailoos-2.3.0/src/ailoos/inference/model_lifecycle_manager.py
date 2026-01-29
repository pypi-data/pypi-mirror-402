"""
ModelLifecycleManager - Gestión del ciclo de vida de modelos
Orquesta la transición de modelos entre entornos y estados.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from .model_registry import ModelRegistry, ModelStatus, ModelMetadata, ModelType

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Entornos disponibles para deployment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"


class LifecycleStage(Enum):
    """Etapas del ciclo de vida."""
    CREATED = "created"
    VALIDATING = "validating"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    MONITORING = "monitoring"
    DEGRADING = "degrading"
    ROLLING_BACK = "rolling_back"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class DeploymentConfig:
    """Configuración de deployment por entorno."""
    environment: Environment
    replicas: int = 1
    cpu_limit: str = "2"
    memory_limit: str = "4Gi"
    gpu_limit: int = 0
    auto_scaling: bool = False
    min_replicas: int = 1
    max_replicas: int = 5
    target_cpu_utilization: int = 70

    # Configuración específica
    endpoint_prefix: str = ""
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    enable_caching: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'environment': self.environment.value,
            'replicas': self.replicas,
            'cpu_limit': self.cpu_limit,
            'memory_limit': self.memory_limit,
            'gpu_limit': self.gpu_limit,
            'auto_scaling': self.auto_scaling,
            'min_replicas': self.min_replicas,
            'max_replicas': self.max_replicas,
            'target_cpu_utilization': self.target_cpu_utilization,
            'endpoint_prefix': self.endpoint_prefix,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'timeout_seconds': self.timeout_seconds,
            'enable_caching': self.enable_caching
        }


@dataclass
class LifecycleEvent:
    """Evento en el ciclo de vida de un modelo."""
    event_id: str
    model_id: str
    stage: LifecycleStage
    environment: Optional[Environment]
    timestamp: datetime
    triggered_by: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'model_id': self.model_id,
            'stage': self.stage.value,
            'environment': self.environment.value if self.environment else None,
            'timestamp': self.timestamp.isoformat(),
            'triggered_by': self.triggered_by,
            'description': self.description,
            'metadata': self.metadata
        }


@dataclass
class PromotionRequest:
    """Solicitud de promoción de modelo."""
    request_id: str
    model_id: str
    from_environment: Environment
    to_environment: Environment
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, rejected, completed
    validation_results: Dict[str, Any] = field(default_factory=dict)
    deployment_config: Optional[DeploymentConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'model_id': self.model_id,
            'from_environment': self.from_environment.value,
            'to_environment': self.to_environment.value,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at.isoformat(),
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'status': self.status,
            'validation_results': self.validation_results,
            'deployment_config': self.deployment_config.to_dict() if self.deployment_config else None
        }


class ModelLifecycleManager:
    """
    Gestor del ciclo de vida completo de modelos EmpoorioLM.

    Características:
    - Promoción automática entre entornos
    - Rollback inteligente
    - Validación por etapas
    - Monitoreo continuo de calidad
    - Aprobaciones y governance
    """

    def __init__(
        self,
        model_registry: ModelRegistry,
        lifecycle_path: str = "./model_lifecycle"
    ):
        self.registry = model_registry
        self.lifecycle_path = Path(lifecycle_path)
        self.lifecycle_path.mkdir(parents=True, exist_ok=True)

        # Archivos de estado
        self.events_file = self.lifecycle_path / "lifecycle_events.json"
        self.promotions_file = self.lifecycle_path / "promotion_requests.json"
        self.deployments_file = self.lifecycle_path / "deployments.json"

        # Estado en memoria
        self.lifecycle_events: Dict[str, List[LifecycleEvent]] = {}
        self.promotion_requests: Dict[str, PromotionRequest] = {}
        self.active_deployments: Dict[str, Dict[str, Any]] = {}  # model_id -> env -> deployment_info

        # Configuración por defecto para entornos
        self.environment_configs = self._get_default_environment_configs()

        # Callbacks
        self.on_stage_change: Optional[Callable[[str, LifecycleStage, LifecycleStage], Awaitable[None]]] = None
        self.on_promotion_request: Optional[Callable[[PromotionRequest], Awaitable[None]]] = None
        self.on_deployment_complete: Optional[Callable[[str, Environment], Awaitable[None]]] = None

        # Locks
        self._lock = asyncio.Lock()

        logger.info(f"🔄 ModelLifecycleManager inicializado en {lifecycle_path}")

    def _get_default_environment_configs(self) -> Dict[Environment, DeploymentConfig]:
        """Obtener configuraciones por defecto para cada entorno."""
        return {
            Environment.DEVELOPMENT: DeploymentConfig(
                environment=Environment.DEVELOPMENT,
                replicas=1,
                cpu_limit="1",
                memory_limit="2Gi",
                endpoint_prefix="/dev",
                rate_limit_per_minute=10
            ),
            Environment.STAGING: DeploymentConfig(
                environment=Environment.STAGING,
                replicas=2,
                cpu_limit="2",
                memory_limit="4Gi",
                auto_scaling=True,
                endpoint_prefix="/staging",
                rate_limit_per_minute=100
            ),
            Environment.PRODUCTION: DeploymentConfig(
                environment=Environment.PRODUCTION,
                replicas=3,
                cpu_limit="4",
                memory_limit="8Gi",
                gpu_limit=1,
                auto_scaling=True,
                min_replicas=2,
                max_replicas=10,
                endpoint_prefix="/api",
                rate_limit_per_minute=1000
            ),
            Environment.CANARY: DeploymentConfig(
                environment=Environment.CANARY,
                replicas=1,
                cpu_limit="2",
                memory_limit="4Gi",
                endpoint_prefix="/canary",
                rate_limit_per_minute=50
            )
        }

    async def register_model_lifecycle(self, model_id: str, created_by: str) -> bool:
        """Registrar inicio del ciclo de vida de un modelo."""
        async with self._lock:
            # Verificar que el modelo existe
            model = await self.registry.get_model(model_id)
            if not model:
                logger.error(f"❌ Modelo {model_id} no encontrado en registry")
                return False

            # Crear evento inicial
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.CREATED,
                environment=None,
                triggered_by=created_by,
                description=f"Modelo {model.name} registrado en ciclo de vida"
            )

            # Cambiar estado del modelo
            await self.registry.update_model_status(model_id, ModelStatus.REGISTERING)

            logger.info(f"📋 Ciclo de vida registrado para modelo {model_id}")
            return True

    async def request_promotion(
        self,
        model_id: str,
        from_environment: Environment,
        to_environment: Environment,
        requested_by: str,
        deployment_config: Optional[DeploymentConfig] = None
    ) -> str:
        """
        Solicitar promoción de modelo entre entornos.

        Args:
            model_id: ID del modelo
            from_environment: Entorno origen
            to_environment: Entorno destino
            requested_by: Usuario que solicita
            deployment_config: Configuración de deployment (opcional)

        Returns:
            ID de la solicitud de promoción
        """
        async with self._lock:
            import uuid
            request_id = f"promo_{uuid.uuid4().hex[:16]}"

            # Usar configuración por defecto si no se proporciona
            if not deployment_config:
                deployment_config = self.environment_configs.get(to_environment)

            request = PromotionRequest(
                request_id=request_id,
                model_id=model_id,
                from_environment=from_environment,
                to_environment=to_environment,
                requested_by=requested_by,
                requested_at=datetime.now(),
                deployment_config=deployment_config
            )

            self.promotion_requests[request_id] = request
            await self._save_promotion_requests()

            # Evento de solicitud
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.VALIDATING,
                environment=to_environment,
                triggered_by=requested_by,
                description=f"Solicitud de promoción de {from_environment.value} a {to_environment.value}",
                metadata={'promotion_request_id': request_id}
            )

            # Callback
            if self.on_promotion_request:
                await self.on_promotion_request(request)

            logger.info(f"📤 Solicitud de promoción {request_id} creada para modelo {model_id}")
            return request_id

    async def approve_promotion(
        self,
        request_id: str,
        approved_by: str,
        validation_results: Dict[str, Any] = None
    ) -> bool:
        """Aprobar solicitud de promoción."""
        async with self._lock:
            if request_id not in self.promotion_requests:
                return False

            request = self.promotion_requests[request_id]
            request.approved_by = approved_by
            request.approved_at = datetime.now()
            request.status = "approved"
            request.validation_results = validation_results or {}

            await self._save_promotion_requests()

            # Evento de aprobación
            await self._add_lifecycle_event(
                model_id=request.model_id,
                stage=LifecycleStage.APPROVED,
                environment=request.to_environment,
                triggered_by=approved_by,
                description=f"Promoción aprobada a {request.to_environment.value}",
                metadata={'promotion_request_id': request_id}
            )

            # Iniciar deployment
            await self._deploy_model(request)

            logger.info(f"✅ Promoción {request_id} aprobada por {approved_by}")
            return True

    async def reject_promotion(self, request_id: str, rejected_by: str, reason: str) -> bool:
        """Rechazar solicitud de promoción."""
        async with self._lock:
            if request_id not in self.promotion_requests:
                return False

            request = self.promotion_requests[request_id]
            request.status = "rejected"

            await self._save_promotion_requests()

            # Evento de rechazo
            await self._add_lifecycle_event(
                model_id=request.model_id,
                stage=LifecycleStage.VALIDATING,
                environment=request.to_environment,
                triggered_by=rejected_by,
                description=f"Promoción rechazada: {reason}",
                metadata={'promotion_request_id': request_id, 'rejection_reason': reason}
            )

            logger.info(f"❌ Promoción {request_id} rechazada por {rejected_by}: {reason}")
            return True

    async def _deploy_model(self, promotion_request: PromotionRequest) -> None:
        """Desplegar modelo en el entorno destino."""
        model_id = promotion_request.model_id
        environment = promotion_request.to_environment
        config = promotion_request.deployment_config

        try:
            # Evento de inicio de deployment
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.DEPLOYING,
                environment=environment,
                triggered_by=promotion_request.approved_by,
                description=f"Iniciando deployment en {environment.value}"
            )

            # Simular deployment (en producción sería integración con Kubernetes/Docker)
            deployment_info = {
                'model_id': model_id,
                'environment': environment.value,
                'config': config.to_dict() if config else {},
                'deployed_at': datetime.now().isoformat(),
                'status': 'running',
                'endpoint': f"{config.endpoint_prefix}/models/{model_id}" if config else f"/models/{model_id}"
            }

            # Registrar deployment activo
            if model_id not in self.active_deployments:
                self.active_deployments[model_id] = {}
            self.active_deployments[model_id][environment.value] = deployment_info

            await self._save_deployments()

            # Actualizar estado del modelo
            await self.registry.update_model_status(model_id, ModelStatus.DEPLOYED)

            # Evento de deployment completado
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.DEPLOYED,
                environment=environment,
                triggered_by="system",
                description=f"Deployment completado en {environment.value}",
                metadata={'endpoint': deployment_info['endpoint']}
            )

            # Marcar promoción como completada
            promotion_request.status = "completed"
            await self._save_promotion_requests()

            # Callback
            if self.on_deployment_complete:
                await self.on_deployment_complete(model_id, environment)

            logger.info(f"🚀 Modelo {model_id} desplegado en {environment.value}")

        except Exception as e:
            logger.error(f"❌ Error en deployment de {model_id}: {e}")

            # Evento de error
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.DEPLOYING,
                environment=environment,
                triggered_by="system",
                description=f"Error en deployment: {str(e)}",
                metadata={'error': str(e)}
            )

    async def rollback_model(
        self,
        model_id: str,
        environment: Environment,
        triggered_by: str,
        rollback_to_version: Optional[str] = None
    ) -> bool:
        """
        Hacer rollback de un modelo a versión anterior.

        Args:
            model_id: ID del modelo
            environment: Entorno donde hacer rollback
            rollback_to_version: Versión específica (opcional, usa anterior por defecto)
            triggered_by: Usuario que inicia rollback

        Returns:
            True si rollback exitoso
        """
        async with self._lock:
            # Evento de inicio de rollback
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.ROLLING_BACK,
                environment=environment,
                triggered_by=triggered_by,
                description=f"Iniciando rollback en {environment.value}"
            )

            try:
                # Lógica de rollback (simulada)
                # En producción: detener pods actuales, iniciar versión anterior

                # Actualizar deployment info
                if model_id in self.active_deployments and environment.value in self.active_deployments[model_id]:
                    deployment = self.active_deployments[model_id][environment.value]
                    deployment['rolled_back_at'] = datetime.now().isoformat()
                    deployment['previous_version'] = deployment.get('version', 'unknown')
                    deployment['version'] = rollback_to_version or 'previous'

                await self._save_deployments()

                # Evento de rollback completado
                await self._add_lifecycle_event(
                    model_id=model_id,
                    stage=LifecycleStage.DEPLOYED,
                    environment=environment,
                    triggered_by=triggered_by,
                    description=f"Rollback completado a versión {rollback_to_version or 'anterior'}",
                    metadata={'rollback_version': rollback_to_version}
                )

                logger.info(f"🔄 Rollback completado para modelo {model_id} en {environment.value}")
                return True

            except Exception as e:
                logger.error(f"❌ Error en rollback de {model_id}: {e}")

                # Evento de error en rollback
                await self._add_lifecycle_event(
                    model_id=model_id,
                    stage=LifecycleStage.ROLLING_BACK,
                    environment=environment,
                    triggered_by="system",
                    description=f"Error en rollback: {str(e)}",
                    metadata={'error': str(e)}
                )

                return False

    async def monitor_model_health(self, model_id: str, environment: Environment) -> Dict[str, Any]:
        """Monitorear salud de un modelo desplegado."""
        async with self._lock:
            if (model_id not in self.active_deployments or
                environment.value not in self.active_deployments[model_id]):
                return {'status': 'not_deployed'}

            deployment = self.active_deployments[model_id][environment.value]

            # Simular verificación de salud
            # En producción: consultar métricas reales de Prometheus/Kubernetes
            health_status = {
                'status': 'healthy',
                'uptime_seconds': (datetime.now() - datetime.fromisoformat(deployment['deployed_at'])).total_seconds(),
                'requests_per_minute': 45.2,  # Simulado
                'avg_response_time': 0.234,  # Simulado
                'error_rate': 0.001,  # Simulado
                'cpu_usage': 65.3,  # Simulado
                'memory_usage': 72.1,  # Simulado
                'last_health_check': datetime.now().isoformat()
            }

            # Verificar si necesita atención
            if health_status['error_rate'] > 0.05:  # 5% error rate
                await self._add_lifecycle_event(
                    model_id=model_id,
                    stage=LifecycleStage.DEGRADING,
                    environment=environment,
                    triggered_by="system",
                    description=f"Modelo degradándose - error rate: {health_status['error_rate']:.3f}",
                    metadata={'health_metrics': health_status}
                )

            return health_status

    async def deprecate_model(self, model_id: str, deprecated_by: str, reason: str) -> bool:
        """Marcar modelo como deprecado."""
        async with self._lock:
            # Evento de deprecación
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.DEPRECATED,
                environment=None,
                triggered_by=deprecated_by,
                description=f"Modelo deprecado: {reason}",
                metadata={'deprecation_reason': reason}
            )

            # Actualizar estado
            await self.registry.update_model_status(model_id, ModelStatus.DEPRECATED)

            logger.info(f"⚠️ Modelo {model_id} marcado como deprecado")
            return True

    async def archive_model(self, model_id: str, archived_by: str) -> bool:
        """Archivar modelo."""
        async with self._lock:
            # Verificar que esté deprecado primero
            model = await self.registry.get_model(model_id)
            if model and model.status != ModelStatus.DEPRECATED:
                logger.warning(f"⚠️ Modelo {model_id} debe estar deprecado antes de archivar")
                return False

            # Evento de archivado
            await self._add_lifecycle_event(
                model_id=model_id,
                stage=LifecycleStage.ARCHIVED,
                environment=None,
                triggered_by=archived_by,
                description="Modelo archivado"
            )

            # Archivar en registry
            await self.registry.archive_model(model_id)

            logger.info(f"📦 Modelo {model_id} archivado")
            return True

    async def get_lifecycle_history(self, model_id: str) -> List[LifecycleEvent]:
        """Obtener historial completo del ciclo de vida."""
        async with self._lock:
            return self.lifecycle_events.get(model_id, [])

    async def get_promotion_requests(
        self,
        model_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PromotionRequest]:
        """Obtener solicitudes de promoción."""
        async with self._lock:
            requests = list(self.promotion_requests.values())

            if model_id:
                requests = [r for r in requests if r.model_id == model_id]

            if status:
                requests = [r for r in requests if r.status == status]

            return requests

    async def get_active_deployments(self) -> Dict[str, Dict[str, Any]]:
        """Obtener deployments activos."""
        async with self._lock:
            return self.active_deployments.copy()

    async def _add_lifecycle_event(
        self,
        model_id: str,
        stage: LifecycleStage,
        environment: Optional[Environment],
        triggered_by: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Agregar evento al historial del ciclo de vida."""
        import uuid
        event = LifecycleEvent(
            event_id=f"event_{uuid.uuid4().hex[:16]}",
            model_id=model_id,
            stage=stage,
            environment=environment,
            timestamp=datetime.now(),
            triggered_by=triggered_by,
            description=description,
            metadata=metadata or {}
        )

        if model_id not in self.lifecycle_events:
            self.lifecycle_events[model_id] = []
        self.lifecycle_events[model_id].append(event)

        await self._save_lifecycle_events()

        # Callback de cambio de etapa
        if self.on_stage_change:
            # Obtener etapa anterior
            events = self.lifecycle_events[model_id]
            prev_stage = events[-2].stage if len(events) > 1 else LifecycleStage.CREATED
            await self.on_stage_change(model_id, prev_stage, stage)

    async def _save_lifecycle_events(self) -> None:
        """Guardar eventos del ciclo de vida."""
        data = {
            mid: [e.to_dict() for e in events]
            for mid, events in self.lifecycle_events.items()
        }

        def save():
            with open(self.events_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(data, f, indent=2, ensure_ascii=False)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, save)

    async def _save_promotion_requests(self) -> None:
        """Guardar solicitudes de promoción."""
        data = {rid: r.to_dict() for rid, r in self.promotion_requests.items()}

        def save():
            with open(self.promotions_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(data, f, indent=2, ensure_ascii=False)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, save)

    async def _save_deployments(self) -> None:
        """Guardar información de deployments."""
        def save():
            with open(self.deployments_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.active_deployments, f, indent=2, ensure_ascii=False)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, save)

    async def load_state(self) -> None:
        """Cargar estado desde disco."""
        async with self._lock:
            # Cargar eventos
            if self.events_file.exists():
                def load_events():
                    with open(self.events_file, 'r', encoding='utf-8') as f:
                        import json
                        return json.load(f)

                loop = asyncio.get_event_loop()
                events_data = await loop.run_in_executor(None, load_events)

                for mid, events_list in events_data.items():
                    self.lifecycle_events[mid] = []
                    for e_data in events_list:
                        e_data['stage'] = LifecycleStage(e_data['stage'])
                        if e_data['environment']:
                            e_data['environment'] = Environment(e_data['environment'])
                        e_data['timestamp'] = datetime.fromisoformat(e_data['timestamp'])
                        self.lifecycle_events[mid].append(LifecycleEvent(**e_data))

            # Cargar promociones (simplificado)
            if self.promotions_file.exists():
                def load_promotions():
                    with open(self.promotions_file, 'r', encoding='utf-8') as f:
                        import json
                        return json.load(f)

                promotions_data = await loop.run_in_executor(None, load_promotions)
                # Restaurar PromotionRequest objects (simplificado)

            # Cargar deployments
            if self.deployments_file.exists():
                def load_deployments():
                    with open(self.deployments_file, 'r', encoding='utf-8') as f:
                        import json
                        return json.load(f)

                self.active_deployments = await loop.run_in_executor(None, load_deployments)

            logger.info(f"📂 Estado del lifecycle manager cargado: {len(self.lifecycle_events)} modelos con historial")

    async def get_lifecycle_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del lifecycle manager."""
        async with self._lock:
            total_models = len(self.lifecycle_events)
            total_events = sum(len(events) for events in self.lifecycle_events.values())
            active_deployments = sum(
                len(envs) for envs in self.active_deployments.values()
            )
            pending_promotions = sum(
                1 for r in self.promotion_requests.values()
                if r.status == "pending"
            )

            return {
                'total_models_tracked': total_models,
                'total_lifecycle_events': total_events,
                'active_deployments': active_deployments,
                'pending_promotions': pending_promotions,
                'lifecycle_path': str(self.lifecycle_path)
            }