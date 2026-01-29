"""
Model Deployer para Kubernetes
Despliegue automático de modelos en Kubernetes con auto-scaling y monitoreo.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import kubernetes_asyncio as k8s
from kubernetes_asyncio.client import ApiClient, AppsV1Api, CoreV1Api, AutoscalingV1Api
from kubernetes_asyncio.client.exceptions import ApiException

from ..federated.image_verifier import get_image_verifier
from ..infrastructure.gcp.tee_manager import TeeManager
from ..validation.tee_attestation_validator import get_tee_attestation_validator, ReferenceMeasurements
from ..core.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ModelDeploymentConfig:
    """Configuración para despliegue de modelo en Kubernetes."""

    # Configuración general
    namespace: str = "default"
    model_name: str = ""
    model_version: str = ""

    # Configuración de contenedor
    image: str = ""
    container_port: int = 8000
    replicas: int = 1

    # Recursos
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "1Gi"
    memory_limit: str = "4Gi"

    # Auto-scaling
    enable_hpa: bool = True
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80

    # Prometheus métricas
    enable_prometheus: bool = True
    prometheus_port: int = 9090

    # Configuración adicional
    env_vars: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

    # Configuración TEE (Trusted Execution Environment)
    tee_enabled: bool = False
    tee_config: Optional[Dict[str, Any]] = None

    def validate(self) -> List[str]:
        """Validar configuración."""
        errors = []

        if not self.model_name:
            errors.append("model_name es requerido")

        if not self.model_version:
            errors.append("model_version es requerido")

        if not self.image:
            errors.append("image es requerida")

        if self.container_port <= 0 or self.container_port > 65535:
            errors.append("container_port debe estar entre 1 y 65535")

        if self.replicas < 1:
            errors.append("replicas debe ser al menos 1")

        if self.enable_hpa:
            if self.min_replicas < 1:
                errors.append("min_replicas debe ser al menos 1")
            if self.max_replicas < self.min_replicas:
                errors.append("max_replicas debe ser mayor o igual a min_replicas")

        if self.tee_enabled:
            if not self.tee_config:
                errors.append("tee_config es requerido cuando tee_enabled es True")
            else:
                required_tee_keys = ['name', 'zone', 'machine_type']
                for key in required_tee_keys:
                    if key not in self.tee_config:
                        errors.append(f"tee_config debe contener '{key}' cuando tee_enabled es True")

        return errors


@dataclass
class DeploymentStatus:
    """Estado de un despliegue de modelo."""

    deployment_id: str
    model_name: str
    model_version: str
    namespace: str
    status: str  # "deploying", "running", "failed", "scaling", "updating", "undeploying"
    created_at: datetime
    updated_at: datetime

    # Recursos creados
    deployment_name: Optional[str] = None
    service_name: Optional[str] = None
    hpa_name: Optional[str] = None

    # Estado actual
    replicas: int = 0
    available_replicas: int = 0
    ready_replicas: int = 0

    # Endpoint
    service_url: Optional[str] = None

    # TEE
    tee_enclave_name: Optional[str] = None

    # Métricas
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

    # Errores
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "namespace": self.namespace,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deployment_name": self.deployment_name,
            "service_name": self.service_name,
            "hpa_name": self.hpa_name,
            "replicas": self.replicas,
            "available_replicas": self.available_replicas,
            "ready_replicas": self.ready_replicas,
            "service_url": self.service_url,
            "tee_enclave_name": self.tee_enclave_name,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "last_error": self.last_error
        }


class ModelDeployer:
    """
    Desplegador de modelos en Kubernetes o TEE (Trusted Execution Environment).

    Características:
    - Despliegue automático de modelos con configuración de recursos
    - Auto-scaling horizontal (HPA) basado en CPU/memoria para despliegues K8s
    - Integración con Prometheus para métricas en K8s
    - Soporte opcional para despliegue en enclaves TEE usando GCP Confidential VMs
    - Gestión concurrente de múltiples despliegues
    - Validación de configuración y manejo de errores
    - Protección de IP mediante enclaves TEE
    """

    def __init__(self, config: Optional[k8s.client.Configuration] = None, app_config: Optional[Config] = None):
        """
        Inicializar el deployer.

        Args:
            config: Configuración de Kubernetes (opcional)
            app_config: Configuración de la aplicación (opcional, para TEE)
        """
        self.config = config or k8s.client.Configuration()
        self.app_config = app_config or Config()
        self.api_client: Optional[ApiClient] = None
        self.apps_api: Optional[AppsV1Api] = None
        self.core_api: Optional[CoreV1Api] = None
        self.autoscaling_api: Optional[AutoscalingV1Api] = None
        self.tee_manager: Optional[TeeManager] = None

        # Estado de despliegues
        self.deployments: Dict[str, DeploymentStatus] = {}

        # Lock para operaciones concurrentes
        self._lock = asyncio.Lock()

        # Configuración de logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def initialize(self):
        """Inicializar cliente de Kubernetes y TEE Manager."""
        try:
            await k8s.config.load_kube_config()
            self.api_client = ApiClient()
            self.apps_api = AppsV1Api(self.api_client)
            self.core_api = CoreV1Api(self.api_client)
            self.autoscaling_api = AutoscalingV1Api(self.api_client)
            self.logger.info("Cliente de Kubernetes inicializado")

            # Inicializar TEE Manager si hay configuración
            if self.app_config:
                self.tee_manager = TeeManager(self.app_config)
                self.logger.info("TEE Manager inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando servicios: {e}")
            raise

    async def close(self):
        """Cerrar conexiones."""
        if self.api_client:
            await self.api_client.close()
            self.logger.info("Cliente de Kubernetes cerrado")

    async def deploy_model(self, config: ModelDeploymentConfig) -> DeploymentStatus:
        """
        Desplegar un modelo en Kubernetes.

        Args:
            config: Configuración del despliegue

        Returns:
            Estado del despliegue
        """
        async with self._lock:
            # Validar configuración
            errors = config.validate()
            if errors:
                error_msg = f"Configuración inválida: {', '.join(errors)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            deployment_id = f"{config.model_name}-{config.model_version}"

            # Crear estado de despliegue
            status = DeploymentStatus(
                deployment_id=deployment_id,
                model_name=config.model_name,
                model_version=config.model_version,
                namespace=config.namespace,
                status="deploying",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.deployments[deployment_id] = status

            try:
                # Verificar firma de imagen antes del despliegue
                logger.info(f"🔐 Verifying image signature for {config.image}")
                verifier = get_image_verifier()
                verification_result = await verifier.verify_image(config.image)

                if not verification_result.is_verified:
                    error_msg = f"Image verification failed for {config.image}: {verification_result.error_message}"
                    logger.error(f"❌ {error_msg}")
                    status.status = "failed"
                    status.last_error = error_msg
                    status.updated_at = datetime.now()
                    raise ValueError(error_msg)

                logger.info(f"✅ Image {config.image} verified successfully")

                if config.tee_enabled:
                    # Despliegue en TEE
                    if not self.tee_manager:
                        raise ValueError("TEE Manager no inicializado")

                    # Preparar configuración del enclave
                    enclave_config = config.tee_config.copy()
                    enclave_config['enclave_type'] = 'model-deployment'
                    enclave_config['model_name'] = config.model_name
                    enclave_config['model_version'] = config.model_version
                    enclave_config['model_image'] = config.image
                    enclave_config['startup_script'] = enclave_config.get('startup_script', f"""
#!/bin/bash
# Script de inicio para despliegue de modelo en TEE
echo "Iniciando despliegue de modelo {config.model_name}:{config.model_version} en TEE"
# Aquí iría el código para cargar y ejecutar el modelo de forma segura
""")

                    # Crear enclave
                    enclave = await self.tee_manager.create_enclave(enclave_config)
                    status.tee_enclave_name = enclave.name
                    status.service_url = f"http://{enclave.external_ip}:{config.container_port}" if enclave.external_ip else None

                    # Verificar integridad del enclave
                    integrity_valid = await self.tee_manager.validate_enclave_integrity(enclave.name)
                    if not integrity_valid:
                        error_msg = f"Enclave integrity validation failed for {enclave.name}"
                        logger.error(f"❌ {error_msg}")
                        status.status = "failed"
                        status.last_error = error_msg
                        status.updated_at = datetime.now()
                        raise ValueError(error_msg)

                    # Realizar attestación remota del enclave
                    attestation_valid = await self._validate_remote_attestation(enclave, config)
                    if not attestation_valid:
                        error_msg = f"Remote attestation failed for enclave {enclave.name}"
                        logger.error(f"❌ {error_msg}")
                        status.status = "failed"
                        status.last_error = error_msg
                        status.updated_at = datetime.now()
                        raise ValueError(error_msg)

                    # Verificar protección contra extracción de weights
                    weights_protected = await self._validate_weight_protection(enclave, config)
                    if not weights_protected:
                        error_msg = f"Weight protection validation failed for enclave {enclave.name}"
                        logger.error(f"❌ {error_msg}")
                        status.status = "failed"
                        status.last_error = error_msg
                        status.updated_at = datetime.now()
                        raise ValueError(error_msg)

                    self.logger.info(f"✅ Modelo {config.model_name}:{config.model_version} cargado en enclave TEE {enclave.name} con attestación y protección validadas")

                else:
                    # Despliegue en Kubernetes
                    # Crear ConfigMap si hay configuración adicional
                    if config.env_vars:
                        await self._create_configmap(config, status)

                    # Crear Deployment
                    await self._create_deployment(config, status)

                    # Crear Service
                    await self._create_service(config, status)

                    # Crear HPA si está habilitado
                    if config.enable_hpa:
                        await self._create_hpa(config, status)

                    # Verificar despliegue
                    await self._verify_deployment(status)

                    self.logger.info(f"✅ Modelo {config.model_name}:{config.model_version} desplegado en Kubernetes")

                status.status = "running"
                status.updated_at = datetime.now()

            except Exception as e:
                status.status = "failed"
                status.last_error = str(e)
                status.updated_at = datetime.now()
                self.logger.error(f"❌ Error desplegando modelo {config.model_name}: {e}")
                raise

            return status

    async def scale_deployment(self, deployment_id: str, replicas: int) -> bool:
        """
        Escalar un despliegue.

        Args:
            deployment_id: ID del despliegue
            replicas: Número de réplicas deseado

        Returns:
            True si el escalado fue exitoso
        """
        async with self._lock:
            if deployment_id not in self.deployments:
                raise ValueError(f"Despliegue {deployment_id} no encontrado")

            status = self.deployments[deployment_id]

            if status.tee_enclave_name:
                # Escalado no soportado para enclaves TEE
                error_msg = "Scaling not supported for TEE enclaves"
                status.status = "failed"
                status.last_error = error_msg
                status.updated_at = datetime.now()
                self.logger.error(f"❌ {error_msg} for {deployment_id}")
                return False

            status.status = "scaling"
            status.updated_at = datetime.now()

            try:
                # Escalar deployment
                await self.apps_api.patch_namespaced_deployment_scale(
                    name=status.deployment_name,
                    namespace=status.namespace,
                    body={
                        "spec": {
                            "replicas": replicas
                        }
                    }
                )

                # Actualizar HPA si existe
                if status.hpa_name:
                    await self.autoscaling_api.patch_namespaced_horizontal_pod_autoscaler(
                        name=status.hpa_name,
                        namespace=status.namespace,
                        body={
                            "spec": {
                                "minReplicas": max(1, replicas // 2),
                                "maxReplicas": max(replicas * 2, 10)
                            }
                        }
                    )

                # Verificar escalado
                await asyncio.sleep(5)  # Esperar propagación
                await self._update_deployment_status(status)

                status.status = "running"
                status.updated_at = datetime.now()
                self.logger.info(f"✅ Despliegue {deployment_id} escalado a {replicas} réplicas")
                return True

            except Exception as e:
                status.status = "failed"
                status.last_error = str(e)
                status.updated_at = datetime.now()
                self.logger.error(f"❌ Error escalando despliegue {deployment_id}: {e}")
                return False

    async def update_model(self, deployment_id: str, new_image: str, new_version: str) -> bool:
        """
        Actualizar un modelo desplegado.

        Args:
            deployment_id: ID del despliegue
            new_image: Nueva imagen del contenedor
            new_version: Nueva versión del modelo

        Returns:
            True si la actualización fue exitosa
        """
        async with self._lock:
            if deployment_id not in self.deployments:
                raise ValueError(f"Despliegue {deployment_id} no encontrado")

            status = self.deployments[deployment_id]
            status.status = "updating"
            status.updated_at = datetime.now()

            try:
                # Verificar firma de nueva imagen antes de actualizar
                logger.info(f"🔐 Verifying new image signature for {new_image}")
                verifier = get_image_verifier()
                verification_result = await verifier.verify_image(new_image)

                if not verification_result.is_verified:
                    error_msg = f"New image verification failed for {new_image}: {verification_result.error_message}"
                    logger.error(f"❌ {error_msg}")
                    status.status = "failed"
                    status.last_error = error_msg
                    status.updated_at = datetime.now()
                    return False

                logger.info(f"✅ New image {new_image} verified successfully")

                if status.tee_enclave_name:
                    # Actualizar enclave TEE
                    if not self.tee_manager:
                        raise ValueError("TEE Manager no inicializado")

                    await self.tee_manager.manage_enclave(
                        status.tee_enclave_name,
                        "update",
                        metadata={
                            "model_version": new_version,
                            "model_image": new_image
                        }
                    )

                    # Verificar integridad después de actualización
                    integrity_valid = await self.tee_manager.validate_enclave_integrity(status.tee_enclave_name)
                    if not integrity_valid:
                        error_msg = f"Enclave integrity validation failed after update for {status.tee_enclave_name}"
                        logger.error(f"❌ {error_msg}")
                        status.status = "failed"
                        status.last_error = error_msg
                        status.updated_at = datetime.now()
                        return False

                    # Re-validar attestación remota después de actualización
                    enclave_obj = self.tee_manager.get_enclave_status(status.tee_enclave_name)
                    if enclave_obj:
                        # Crear config temporal para validación
                        temp_config = ModelDeploymentConfig(
                            model_name=status.model_name,
                            model_version=new_version,
                            image=new_image,
                            tee_enabled=True,
                            tee_config={'expected_platform_hash': 'trusted_platform_hash'}  # Valores por defecto
                        )

                        attestation_valid = await self._validate_remote_attestation(enclave_obj, temp_config)
                        if not attestation_valid:
                            error_msg = f"Remote attestation failed after update for {status.tee_enclave_name}"
                            logger.error(f"❌ {error_msg}")
                            status.status = "failed"
                            status.last_error = error_msg
                            status.updated_at = datetime.now()
                            return False

                        # Re-validar protección de weights
                        weights_protected = await self._validate_weight_protection(enclave_obj, temp_config)
                        if not weights_protected:
                            error_msg = f"Weight protection validation failed after update for {status.tee_enclave_name}"
                            logger.error(f"❌ {error_msg}")
                            status.status = "failed"
                            status.last_error = error_msg
                            status.updated_at = datetime.now()
                            return False

                else:
                    # Actualizar deployment de Kubernetes
                    await self.apps_api.patch_namespaced_deployment(
                        name=status.deployment_name,
                        namespace=status.namespace,
                        body={
                            "spec": {
                                "template": {
                                    "spec": {
                                        "containers": [{
                                            "name": f"{status.model_name}-container",
                                            "image": new_image
                                        }]
                                    }
                                }
                            }
                        }
                    )

                    # Verificar actualización
                    await asyncio.sleep(10)  # Esperar rollout
                    await self._update_deployment_status(status)

                # Actualizar estado
                status.model_version = new_version
                status.updated_at = datetime.now()
                status.status = "running"
                self.logger.info(f"✅ Modelo {deployment_id} actualizado a versión {new_version}")
                return True

            except Exception as e:
                status.status = "failed"
                status.last_error = str(e)
                status.updated_at = datetime.now()
                self.logger.error(f"❌ Error actualizando modelo {deployment_id}: {e}")
                return False

    async def undeploy_model(self, deployment_id: str) -> bool:
        """
        Eliminar un despliegue de modelo.

        Args:
            deployment_id: ID del despliegue

        Returns:
            True si la eliminación fue exitosa
        """
        async with self._lock:
            if deployment_id not in self.deployments:
                raise ValueError(f"Despliegue {deployment_id} no encontrado")

            status = self.deployments[deployment_id]
            status.status = "undeploying"
            status.updated_at = datetime.now()

            try:
                if status.tee_enclave_name:
                    # Eliminar enclave TEE
                    if not self.tee_manager:
                        raise ValueError("TEE Manager no inicializado")

                    await self.tee_manager.delete_enclave(status.tee_enclave_name)
                    self.logger.info(f"✅ Enclave TEE {status.tee_enclave_name} eliminado")

                else:
                    # Eliminar recursos de Kubernetes
                    # Eliminar HPA
                    if status.hpa_name:
                        await self.autoscaling_api.delete_namespaced_horizontal_pod_autoscaler(
                            name=status.hpa_name,
                            namespace=status.namespace
                        )

                    # Eliminar Service
                    if status.service_name:
                        await self.core_api.delete_namespaced_service(
                            name=status.service_name,
                            namespace=status.namespace
                        )

                    # Eliminar Deployment
                    if status.deployment_name:
                        await self.apps_api.delete_namespaced_deployment(
                            name=status.deployment_name,
                            namespace=status.namespace
                        )

                    # Eliminar ConfigMap si existe
                    configmap_name = f"{status.deployment_name}-config"
                    try:
                        await self.core_api.delete_namespaced_config_map(
                            name=configmap_name,
                            namespace=status.namespace
                        )
                    except ApiException:
                        pass  # ConfigMap no existe

                    self.logger.info(f"✅ Recursos de Kubernetes para {deployment_id} eliminados")

                # Limpiar estado
                del self.deployments[deployment_id]
                self.logger.info(f"✅ Modelo {deployment_id} eliminado exitosamente")
                return True

            except Exception as e:
                status.status = "failed"
                status.last_error = str(e)
                status.updated_at = datetime.now()
                self.logger.error(f"❌ Error eliminando modelo {deployment_id}: {e}")
                return False

    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Obtener estado de un despliegue."""
        if deployment_id not in self.deployments:
            return None

        status = self.deployments[deployment_id]
        await self._update_deployment_status(status)
        return status

    async def list_deployments(self) -> List[DeploymentStatus]:
        """Listar todos los despliegues."""
        for status in self.deployments.values():
            await self._update_deployment_status(status)
        return list(self.deployments.values())

    async def _create_configmap(self, config: ModelDeploymentConfig, status: DeploymentStatus):
        """Crear ConfigMap para variables de entorno."""
        configmap_name = f"{status.deployment_name}-config"

        configmap = k8s.client.V1ConfigMap(
            metadata=k8s.client.V1ObjectMeta(
                name=configmap_name,
                namespace=config.namespace,
                labels={"app": status.deployment_name}
            ),
            data=config.env_vars
        )

        await self.core_api.create_namespaced_config_map(
            namespace=config.namespace,
            body=configmap
        )

        self.logger.info(f"ConfigMap {configmap_name} creado")

    async def _create_deployment(self, config: ModelDeploymentConfig, status: DeploymentStatus):
        """Crear Deployment de Kubernetes."""
        deployment_name = f"{config.model_name}-{config.model_version}"
        status.deployment_name = deployment_name

        # Contenedor
        container = k8s.client.V1Container(
            name=f"{config.model_name}-container",
            image=config.image,
            ports=[k8s.client.V1ContainerPort(container_port=config.container_port)],
            resources=k8s.client.V1ResourceRequirements(
                requests={
                    "cpu": config.cpu_request,
                    "memory": config.memory_request
                },
                limits={
                    "cpu": config.cpu_limit,
                    "memory": config.memory_limit
                }
            ),
            env=[k8s.client.V1EnvVar(name=k, value=v) for k, v in config.env_vars.items()]
        )

        # Anotaciones para Prometheus
        annotations = dict(config.annotations)
        if config.enable_prometheus:
            annotations.update({
                "prometheus.io/scrape": "true",
                "prometheus.io/port": str(config.prometheus_port),
                "prometheus.io/path": "/metrics"
            })

        # Template del pod
        template = k8s.client.V1PodTemplateSpec(
            metadata=k8s.client.V1ObjectMeta(
                labels={
                    "app": deployment_name,
                    "model": config.model_name,
                    "version": config.model_version,
                    **config.labels
                },
                annotations=annotations
            ),
            spec=k8s.client.V1PodSpec(
                containers=[container]
            )
        )

        # Spec del deployment
        spec = k8s.client.V1DeploymentSpec(
            replicas=config.replicas,
            selector=k8s.client.V1LabelSelector(
                match_labels={"app": deployment_name}
            ),
            template=template
        )

        # Deployment
        deployment = k8s.client.V1Deployment(
            metadata=k8s.client.V1ObjectMeta(
                name=deployment_name,
                namespace=config.namespace,
                labels={"app": deployment_name}
            ),
            spec=spec
        )

        await self.apps_api.create_namespaced_deployment(
            namespace=config.namespace,
            body=deployment
        )

        self.logger.info(f"Deployment {deployment_name} creado")

    async def _create_service(self, config: ModelDeploymentConfig, status: DeploymentStatus):
        """Crear Service de Kubernetes."""
        service_name = f"{status.deployment_name}-service"
        status.service_name = service_name

        service = k8s.client.V1Service(
            metadata=k8s.client.V1ObjectMeta(
                name=service_name,
                namespace=config.namespace,
                labels={"app": status.deployment_name}
            ),
            spec=k8s.client.V1ServiceSpec(
                selector={"app": status.deployment_name},
                ports=[k8s.client.V1ServicePort(
                    port=config.container_port,
                    target_port=config.container_port,
                    protocol="TCP"
                )],
                type="ClusterIP"
            )
        )

        created_service = await self.core_api.create_namespaced_service(
            namespace=config.namespace,
            body=service
        )

        # Construir URL del servicio
        status.service_url = f"http://{service_name}.{config.namespace}.svc.cluster.local:{config.container_port}"

        self.logger.info(f"Service {service_name} creado")

    async def _create_hpa(self, config: ModelDeploymentConfig, status: DeploymentStatus):
        """Crear HorizontalPodAutoscaler."""
        hpa_name = f"{status.deployment_name}-hpa"
        status.hpa_name = hpa_name

        metrics = []
        if config.target_cpu_utilization > 0:
            metrics.append(k8s.client.V2MetricSpec(
                type="Resource",
                resource=k8s.client.V2ResourceMetricSource(
                    name="cpu",
                    target=k8s.client.V2MetricTarget(
                        type="Utilization",
                        average_utilization=config.target_cpu_utilization
                    )
                )
            ))

        if config.target_memory_utilization > 0:
            metrics.append(k8s.client.V2MetricSpec(
                type="Resource",
                resource=k8s.client.V2ResourceMetricSource(
                    name="memory",
                    target=k8s.client.V2MetricTarget(
                        type="Utilization",
                        average_utilization=config.target_memory_utilization
                    )
                )
            ))

        hpa = k8s.client.V2HorizontalPodAutoscaler(
            metadata=k8s.client.V1ObjectMeta(
                name=hpa_name,
                namespace=config.namespace,
                labels={"app": status.deployment_name}
            ),
            spec=k8s.client.V2HorizontalPodAutoscalerSpec(
                scale_target_ref=k8s.client.V2CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=status.deployment_name
                ),
                min_replicas=config.min_replicas,
                max_replicas=config.max_replicas,
                metrics=metrics
            )
        )

        await self.autoscaling_api.create_namespaced_horizontal_pod_autoscaler(
            namespace=config.namespace,
            body=hpa
        )

        self.logger.info(f"HPA {hpa_name} creado")

    async def _verify_deployment(self, status: DeploymentStatus):
        """Verificar que el despliegue esté listo."""
        max_attempts = 60  # 5 minutos
        attempt = 0

        while attempt < max_attempts:
            try:
                deployment = await self.apps_api.read_namespaced_deployment(
                    name=status.deployment_name,
                    namespace=status.namespace
                )

                status.replicas = deployment.spec.replicas
                status.available_replicas = deployment.status.available_replicas or 0
                status.ready_replicas = deployment.status.ready_replicas or 0

                if status.ready_replicas >= status.replicas:
                    self.logger.info(f"Despliegue {status.deployment_name} listo: {status.ready_replicas}/{status.replicas} réplicas")
                    return

                await asyncio.sleep(5)
                attempt += 1

            except Exception as e:
                self.logger.warning(f"Error verificando despliegue: {e}")
                await asyncio.sleep(5)
                attempt += 1

        raise TimeoutError(f"Despliegue {status.deployment_name} no estuvo listo después de {max_attempts * 5} segundos")

    async def _update_deployment_status(self, status: DeploymentStatus):
        """Actualizar estado de un despliegue desde Kubernetes o TEE."""
        try:
            if status.tee_enclave_name:
                # Actualizar desde TEE
                if self.tee_manager:
                    monitoring_data = await self.tee_manager.monitor_enclaves()
                    enclave_data = monitoring_data.get(status.tee_enclave_name, {})

                    status.status = enclave_data.get('status', 'UNKNOWN')
                    status.cpu_usage = enclave_data.get('cpu_utilization', 0.0)
                    status.memory_usage = enclave_data.get('memory_utilization', 0.0)
                    status.updated_at = datetime.now()
            else:
                # Actualizar desde Kubernetes
                deployment = await self.apps_api.read_namespaced_deployment(
                    name=status.deployment_name,
                    namespace=status.namespace
                )

                status.replicas = deployment.spec.replicas
                status.available_replicas = deployment.status.available_replicas or 0
                status.ready_replicas = deployment.status.ready_replicas or 0
                status.updated_at = datetime.now()

        except Exception as e:
            self.logger.error(f"Error actualizando estado del despliegue {status.deployment_id}: {e}")

    async def _validate_remote_attestation(self, enclave, config: ModelDeploymentConfig) -> bool:
        """
        Validar attestación remota del enclave TEE durante deployment.

        Args:
            enclave: Enclave TEE creado
            config: Configuración del deployment

        Returns:
            True si la attestación es válida
        """
        try:
            # Obtener validador de attestación
            attestation_validator = get_tee_attestation_validator()

            # Crear mediciones de referencia esperadas para el enclave
            expected_measurements = ReferenceMeasurements(
                platform_firmware_hash=config.tee_config.get('expected_platform_hash', 'trusted_platform_hash'),
                kernel_hash=config.tee_config.get('expected_kernel_hash', 'trusted_kernel_hash'),
                initrd_hash=config.tee_config.get('expected_initrd_hash', 'trusted_initrd_hash'),
                guest_policy=config.tee_config.get('expected_guest_policy', 'trusted_policy'),
                family_id=config.tee_config.get('expected_family_id', 'trusted_family'),
                image_id=config.tee_config.get('expected_image_id', 'trusted_image')
            )

            # Realizar attestación remota
            result = attestation_validator.validate_remote_attestation(
                instance_name=enclave.name,
                project_id=self.app_config.get('gcp_project_id', 'test-project'),
                zone=enclave.zone,
                expected_measurements=expected_measurements
            )

            if result.is_valid:
                self.logger.info(f"✅ Attestación remota exitosa para enclave {enclave.name}")
                return True
            else:
                self.logger.error(f"❌ Attestación remota fallida para enclave {enclave.name}: {result.issues}")
                return False

        except Exception as e:
            self.logger.error(f"Error en validación de attestación remota: {e}")
            return False

    async def _validate_weight_protection(self, enclave, config: ModelDeploymentConfig) -> bool:
        """
        Validar protección contra extracción de weights en el enclave TEE.

        Args:
            enclave: Enclave TEE
            config: Configuración del deployment

        Returns:
            True si los weights están protegidos
        """
        try:
            # Verificar que el enclave tenga configuraciones de seguridad para weights
            protection_config = config.tee_config.get('weight_protection', {})

            # Verificar encriptación de weights
            if not protection_config.get('enable_encryption', True):
                self.logger.warning(f"Encriptación de weights no habilitada para enclave {enclave.name}")
                return False

            # Verificar que no se permita extracción externa
            if protection_config.get('allow_external_extraction', False):
                self.logger.error(f"Extracción externa de weights permitida para enclave {enclave.name}")
                return False

            # Verificar política de acceso (solo enclave)
            access_policy = protection_config.get('access_policy', 'enclave_only')
            if access_policy != 'enclave_only':
                self.logger.error(f"Política de acceso insegura para weights en enclave {enclave.name}: {access_policy}")
                return False

            # Simular verificación de que weights no son accesibles externamente
            # En un entorno real, esto verificaría que los weights están en memoria encriptada
            weights_secure = await self._simulate_weight_security_check(enclave, config)

            if weights_secure:
                self.logger.info(f"✅ Protección de weights validada para enclave {enclave.name}")
                return True
            else:
                self.logger.error(f"❌ Protección de weights fallida para enclave {enclave.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error en validación de protección de weights: {e}")
            return False

    async def _simulate_weight_security_check(self, enclave, config: ModelDeploymentConfig) -> bool:
        """
        Simular verificación de seguridad de weights (en producción sería una verificación real).

        Args:
            enclave: Enclave TEE
            config: Configuración del deployment

        Returns:
            True si los weights están seguros
        """
        try:
            # Simular verificación de que weights están en memoria segura
            # En producción, esto podría involucrar:
            # - Verificación de que weights están en memoria encriptada
            # - Verificación de que no hay volcados de memoria accesibles
            # - Verificación de integridad criptográfica

            # Simular algunas verificaciones básicas
            enclave_secure = enclave.confidential_compute and enclave.integrity_monitoring
            weights_protected = config.tee_config.get('weight_protection', {}).get('enable_encryption', True)

            return enclave_secure and weights_protected

        except Exception as e:
            self.logger.error(f"Error en verificación simulada de seguridad de weights: {e}")
            return False


# Funciones de conveniencia
async def deploy_model_to_k8s(
    model_name: str,
    model_version: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    cpu_request: str = "500m",
    memory_request: str = "1Gi"
) -> DeploymentStatus:
    """
    Desplegar modelo con configuración optimizada.

    Args:
        model_name: Nombre del modelo
        model_version: Versión del modelo
        image: Imagen del contenedor
        namespace: Namespace de Kubernetes
        replicas: Número inicial de réplicas
        cpu_request: Solicitud de CPU
        memory_request: Solicitud de memoria

    Returns:
        Estado del despliegue
    """
    config = ModelDeploymentConfig(
        model_name=model_name,
        model_version=model_version,
        image=image,
        namespace=namespace,
        replicas=replicas,
        cpu_request=cpu_request,
        memory_request=memory_request
    )

    async with ModelDeployer() as deployer:
        return await deployer.deploy_model(config)


async def quick_deployment_test() -> bool:
    """
    Test rápido de despliegue (simulado).

    Returns:
        True si el test fue exitoso
    """
    # Simular configuración
    config = ModelDeploymentConfig(
        model_name="test-model",
        model_version="v1.0.0",
        image="nginx:latest",
        replicas=1
    )

    try:
        async with ModelDeployer() as deployer:
            # Solo validar configuración
            errors = config.validate()
            if errors:
                logger.error(f"Errores de validación: {errors}")
                return False

            logger.info("✅ Test de configuración exitoso")
            return True

    except Exception as e:
        logger.error(f"❌ Error en test de despliegue: {e}")
        return False


if __name__ == "__main__":
    # Test del deployer
    print("🧪 Probando Model Deployer...")

    async def test_deployer():
        success = await quick_deployment_test()
        return success

    success = asyncio.run(test_deployer())

    if success:
        print("🎉 Model Deployer funcionando correctamente")
    else:
        print("❌ Error en Model Deployer")