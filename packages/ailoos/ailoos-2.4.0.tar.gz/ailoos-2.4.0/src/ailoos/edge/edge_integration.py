"""
Integración completa del sistema de edge computing con AILOOS.

Proporciona una interfaz unificada para usar todos los componentes
de edge computing juntos, integrados con el sistema federated existente.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from .edge_model_optimizer import EdgeModelOptimizer, EdgeDeviceCapabilities, EdgeDeviceType, create_edge_optimizer_for_device
from .lightweight_runtime import LightweightRuntime, create_lightweight_runtime_for_mobile, create_lightweight_runtime_for_iot
from .edge_synchronization import EdgeSynchronization, create_edge_sync_for_mobile, create_edge_sync_for_iot
from .resource_manager import ResourceManager, create_resource_manager_for_mobile, create_resource_manager_for_iot
from .offline_capabilities import OfflineCapabilities, create_offline_capabilities_for_mobile, create_offline_capabilities_for_iot
from .edge_federated_learning import EdgeFederatedLearning, create_edge_fl_for_mobile, create_edge_fl_for_iot

logger = logging.getLogger(__name__)


@dataclass
class EdgeSystemConfig:
    """Configuración completa del sistema edge."""
    device_id: str
    device_type: EdgeDeviceType
    central_node_url: str
    auth_token: Optional[str] = None

    # Rutas de almacenamiento
    model_storage_path: str = "./edge_models"
    offline_storage_path: str = "./edge_offline"
    resource_cache_path: str = "./edge_cache"

    # Límites de recursos
    max_memory_mb: int = 512
    max_storage_mb: int = 500

    # Configuración de conectividad
    enable_offline_mode: bool = True
    sync_interval_seconds: int = 1800

    # FL configuration
    enable_federated_learning: bool = True
    fl_rounds_per_day: int = 3


class EdgeSystem:
    """
    Sistema completo de edge computing integrado.

    Proporciona una interfaz unificada para todos los componentes edge,
    con integración automática entre ellos y con el sistema federated de AILOOS.
    """

    def __init__(self, config: EdgeSystemConfig):
        self.config = config

        # Crear directorios necesarios
        Path(config.model_storage_path).mkdir(parents=True, exist_ok=True)
        Path(config.offline_storage_path).mkdir(parents=True, exist_ok=True)
        Path(config.resource_cache_path).mkdir(parents=True, exist_ok=True)

        # Inicializar componentes
        self._init_components()

        # Estado del sistema
        self.is_running = False
        self.start_time = time.time()

        logger.info("🔧 EdgeSystem inicializado")
        logger.info(f"   Device ID: {config.device_id}")
        logger.info(f"   Device Type: {config.device_type.value}")

    def _init_components(self):
        """Inicializar todos los componentes del sistema."""
        # 1. Resource Manager
        self.resource_manager = self._create_resource_manager()

        # 2. Offline Capabilities
        self.offline_capabilities = self._create_offline_capabilities()

        # 3. Edge Synchronization
        self.edge_sync = self._create_edge_sync()

        # 4. Lightweight Runtime
        self.runtime = self._create_runtime()

        # 5. Edge Model Optimizer
        self.model_optimizer = self._create_model_optimizer()

        # 6. Edge Federated Learning (opcional)
        self.edge_fl = None
        if self.config.enable_federated_learning:
            self.edge_fl = self._create_edge_fl()

        # Configurar integraciones entre componentes
        self._setup_component_integrations()

    def _create_resource_manager(self) -> ResourceManager:
        """Crear ResourceManager según tipo de dispositivo."""
        if self.config.device_type in [EdgeDeviceType.MOBILE_PHONE, EdgeDeviceType.IOT_DEVICE]:
            return create_resource_manager_for_mobile()
        else:
            return create_resource_manager_for_iot()

    def _create_offline_capabilities(self) -> OfflineCapabilities:
        """Crear OfflineCapabilities según tipo de dispositivo."""
        if self.config.device_type == EdgeDeviceType.MOBILE_PHONE:
            return create_offline_capabilities_for_mobile(self.config.offline_storage_path)
        else:
            return create_offline_capabilities_for_iot(self.config.offline_storage_path)

    def _create_edge_sync(self) -> EdgeSynchronization:
        """Crear EdgeSynchronization según tipo de dispositivo."""
        if self.config.device_type == EdgeDeviceType.MOBILE_PHONE:
            return create_edge_sync_for_mobile(
                central_url=self.config.central_node_url,
                device_id=self.config.device_id,
                auth_token=self.config.auth_token
            )
        else:
            return create_edge_sync_for_iot(
                central_url=self.config.central_node_url,
                device_id=self.config.device_id,
                auth_token=self.config.auth_token
            )

    def _create_runtime(self) -> LightweightRuntime:
        """Crear LightweightRuntime según tipo de dispositivo."""
        if self.config.device_type == EdgeDeviceType.MOBILE_PHONE:
            return create_lightweight_runtime_for_mobile(
                max_memory_mb=self.config.max_memory_mb,
                max_concurrent_requests=2
            )
        else:
            return create_lightweight_runtime_for_iot(
                max_memory_mb=self.config.max_memory_mb,
                max_concurrent_requests=1
            )

    def _create_model_optimizer(self) -> EdgeModelOptimizer:
        """Crear EdgeModelOptimizer."""
        from .edge_model_optimizer import EdgeOptimizationConfig
        config = EdgeOptimizationConfig(
            target_device_type=self.config.device_type,
            max_memory_usage_mb=self.config.max_memory_mb
        )
        return EdgeModelOptimizer(config)

    def _create_edge_fl(self) -> EdgeFederatedLearning:
        """Crear EdgeFederatedLearning."""
        if self.config.device_type == EdgeDeviceType.MOBILE_PHONE:
            return create_edge_fl_for_mobile(
                device_id=self.config.device_id,
                resource_manager=self.resource_manager,
                offline_capabilities=self.offline_capabilities,
                edge_sync=self.edge_sync
            )
        else:
            return create_edge_fl_for_iot(
                device_id=self.config.device_id,
                resource_manager=self.resource_manager,
                offline_capabilities=self.offline_capabilities,
                edge_sync=self.edge_sync
            )

    def _setup_component_integrations(self):
        """Configurar integraciones entre componentes."""
        # ResourceManager -> OfflineCapabilities
        self.offline_capabilities.add_connectivity_callback(
            lambda connected, state: self._on_connectivity_change(connected, state)
        )

        # EdgeSync -> OfflineCapabilities
        self.edge_sync.add_sync_callback(
            lambda task_id, status, result: self._on_sync_event(task_id, status, result)
        )

        # ResourceManager -> Runtime
        self.runtime.add_request_callback(
            lambda result: self._on_inference_request(result)
        )

        # EdgeFL -> ResourceManager
        if self.edge_fl:
            self.edge_fl.add_training_callback(
                lambda metrics: self._on_training_event(metrics)
            )

    def start(self):
        """Iniciar el sistema edge completo."""
        if self.is_running:
            logger.warning("⚠️ EdgeSystem ya está ejecutándose")
            return

        try:
            # Iniciar componentes en orden
            self.resource_manager.start()
            logger.info("✅ ResourceManager iniciado")

            self.offline_capabilities.start()
            logger.info("✅ OfflineCapabilities iniciado")

            self.edge_sync.start()
            logger.info("✅ EdgeSynchronization iniciado")

            self.runtime.start()
            logger.info("✅ LightweightRuntime iniciado")

            if self.edge_fl:
                self.edge_fl.start()
                logger.info("✅ EdgeFederatedLearning iniciado")

            self.is_running = True
            self.start_time = time.time()

            logger.info("🚀 EdgeSystem completamente operativo")

        except Exception as e:
            logger.error(f"❌ Error iniciando EdgeSystem: {e}")
            self.stop()
            raise

    def stop(self):
        """Detener el sistema edge completo."""
        if not self.is_running:
            return

        try:
            # Detener componentes en orden inverso
            if self.edge_fl:
                self.edge_fl.stop()

            self.runtime.stop()
            self.edge_sync.stop()
            self.offline_capabilities.stop()
            self.resource_manager.stop()

            self.is_running = False
            logger.info("🛑 EdgeSystem detenido")

        except Exception as e:
            logger.error(f"❌ Error deteniendo EdgeSystem: {e}")

    def optimize_and_deploy_model(self, model_path: str, model_name: str) -> str:
        """
        Optimizar modelo para edge y desplegarlo en el runtime.

        Args:
            model_path: Ruta del modelo original
            model_name: Nombre del modelo

        Returns:
            ID del modelo optimizado
        """
        try:
            logger.info(f"🔄 Optimizando modelo {model_name} para edge...")

            # Obtener capacidades del dispositivo
            device_caps = self._get_device_capabilities()

            # Optimizar modelo
            optimization_profile = self.model_optimizer.optimize_model_for_edge(
                model_path=model_path,
                device_capabilities=device_caps
            )

            # Aplicar optimización
            optimized_path = self.model_optimizer.apply_optimization_profile(
                model_path=model_path,
                profile=optimization_profile,
                output_path=f"{self.config.model_storage_path}/{model_name}_optimized"
            )

            # Cargar en runtime
            model_loaded = self.runtime.load_model(
                model_path=optimized_path,
                model_id=model_name,
                model_format=self._detect_model_format(optimized_path)
            )

            if model_loaded:
                logger.info(f"✅ Modelo {model_name} optimizado y desplegado")
                return model_name
            else:
                logger.error(f"❌ Error cargando modelo optimizado {model_name}")
                return ""

        except Exception as e:
            logger.error(f"❌ Error optimizando modelo {model_name}: {e}")
            return ""

    def run_inference(self, model_id: str, input_data: Any, **kwargs) -> Any:
        """
        Ejecutar inferencia usando el runtime optimizado.

        Args:
            model_id: ID del modelo
            input_data: Datos de entrada
            **kwargs: Argumentos adicionales

        Returns:
            Resultado de inferencia
        """
        try:
            # Verificar recursos antes de inferencia
            if not self._check_inference_resources():
                # Usar offline capabilities si no hay recursos
                if self.offline_capabilities:
                    op_id = self.offline_capabilities.queue_operation(
                        operation_type=self.offline_capabilities.OfflineOperation.INFERENCE,
                        data={"model_id": model_id, "input": input_data, **kwargs}
                    )
                    return {"offline_operation_id": op_id, "status": "queued"}
                else:
                    raise RuntimeError("Recursos insuficientes y sin capacidades offline")

            # Ejecutar inferencia
            result = self.runtime.run_inference(
                model_id=model_id,
                input_data=input_data,
                async_mode=False,
                **kwargs
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error en inferencia: {e}")
            raise

    def participate_in_federated_round(self, round_id: str, global_model: Any) -> bool:
        """
        Participar en ronda de federated learning.

        Args:
            round_id: ID de la ronda
            global_model: Modelo global

        Returns:
            True si se acepta la participación
        """
        if not self.edge_fl:
            logger.warning("⚠️ Federated Learning no está habilitado")
            return False

        try:
            # Establecer modelo global
            self.edge_fl.set_global_model(global_model, f"round_{round_id}")

            # Iniciar ronda
            accepted = self.edge_fl.start_round(round_id)

            if accepted:
                logger.info(f"🎯 Participando en ronda FL {round_id}")
            else:
                logger.info(f"⏭️ Saltando ronda FL {round_id}")

            return accepted

        except Exception as e:
            logger.error(f"❌ Error participando en ronda FL {round_id}: {e}")
            return False

    def sync_system_status(self) -> str:
        """
        Sincronizar estado del sistema con nodo central.

        Returns:
            ID de tarea de sincronización
        """
        try:
            system_status = self.get_system_status()

            task_id = self.edge_sync.sync_metrics(
                metrics_data={
                    "system_status": system_status,
                    "timestamp": time.time()
                },
                priority=self.edge_sync.SyncPriority.NORMAL
            )

            logger.info(f"📤 Estado del sistema sincronizado: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"❌ Error sincronizando estado: {e}")
            return ""

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        return {
            "device_id": self.config.device_id,
            "device_type": self.config.device_type.value,
            "is_running": self.is_running,
            "uptime_seconds": time.time() - self.start_time if self.is_running else 0,

            "resource_status": self.resource_manager.get_resource_status() if self.resource_manager else {},
            "offline_status": self.offline_capabilities.get_offline_status() if self.offline_capabilities else {},
            "sync_status": self.edge_sync.get_sync_status() if self.edge_sync else {},
            "runtime_status": self.runtime.get_metrics() if self.runtime else {},
            "fl_status": self.edge_fl.get_fl_status() if self.edge_fl else {},

            "loaded_models": self.runtime.get_loaded_models() if self.runtime else {},
            "optimizer_stats": self.model_optimizer.get_optimizer_stats() if self.model_optimizer else {}
        }

    def _get_device_capabilities(self) -> EdgeDeviceCapabilities:
        """Obtener capacidades del dispositivo actual."""
        # Obtener info del sistema
        import psutil
        cpu_count = psutil.cpu_count()
        total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB

        # Mapear tipo de dispositivo a capacidades
        if self.config.device_type == EdgeDeviceType.MOBILE_PHONE:
            return EdgeDeviceCapabilities(
                device_type=EdgeDeviceType.MOBILE_PHONE,
                cpu_cores=min(cpu_count, 8),
                total_memory_mb=min(int(total_memory), 4096),
                gpu_memory_mb=2048,
                supports_fp16=True,
                supports_int8=True,
                max_power_consumption_w=8.0
            )
        elif self.config.device_type == EdgeDeviceType.IOT_DEVICE:
            return EdgeDeviceCapabilities(
                device_type=EdgeDeviceType.IOT_DEVICE,
                cpu_cores=min(cpu_count, 2),
                total_memory_mb=min(int(total_memory), 256),
                supports_fp16=False,
                supports_int8=False,
                max_power_consumption_w=2.0
            )
        else:
            # Configuración genérica
            return EdgeDeviceCapabilities(
                device_type=self.config.device_type,
                cpu_cores=cpu_count,
                total_memory_mb=int(total_memory),
                supports_fp16=True,
                supports_int8=True
            )

    def _detect_model_format(self, model_path: str):
        """Detectar formato del modelo."""
        from .lightweight_runtime import ModelFormat

        if model_path.endswith('.onnx'):
            return ModelFormat.ONNX
        elif model_path.endswith('.pt') or model_path.endswith('.pth'):
            return ModelFormat.PYTORCH
        else:
            return ModelFormat.PYTORCH  # Default

    def _check_inference_resources(self) -> bool:
        """Verificar recursos disponibles para inferencia."""
        if not self.resource_manager:
            return True

        status = self.resource_manager.get_resource_status()
        cpu_usage = status['current_usage']['cpu_percent']
        memory_usage = status['current_usage']['memory_percent']

        return cpu_usage < 80.0 and memory_usage < 85.0

    def _on_connectivity_change(self, connected: bool, state: str):
        """Callback para cambios de conectividad."""
        logger.info(f"📡 Conectividad cambiada: {state}")

        if connected and self.offline_capabilities:
            # Forzar sincronización cuando se restaure conectividad
            self.offline_capabilities.force_sync_now()

    def _on_sync_event(self, task_id: str, status: str, result: Any):
        """Callback para eventos de sincronización."""
        logger.debug(f"🔄 Sync event: {task_id} - {status}")

    def _on_inference_request(self, result: Any):
        """Callback para solicitudes de inferencia."""
        # Actualizar métricas de recursos después de inferencia
        if self.resource_manager:
            self.resource_manager.get_resource_status()

    def _on_training_event(self, metrics: Dict[str, Any]):
        """Callback para eventos de entrenamiento FL."""
        logger.info(f"🏋️ Evento de entrenamiento: {metrics.get('state', 'unknown')}")


# Funciones de conveniencia para crear sistemas completos
def create_mobile_edge_system(
    device_id: str,
    central_url: str,
    auth_token: Optional[str] = None
) -> EdgeSystem:
    """
    Crear sistema edge completo optimizado para móviles.

    Args:
        device_id: ID único del dispositivo
        central_url: URL del nodo central
        auth_token: Token de autenticación opcional

    Returns:
        Sistema edge configurado
    """
    config = EdgeSystemConfig(
        device_id=device_id,
        device_type=EdgeDeviceType.MOBILE_PHONE,
        central_node_url=central_url,
        auth_token=auth_token,
        max_memory_mb=1024,
        max_storage_mb=200,
        enable_federated_learning=True
    )

    return EdgeSystem(config)


def create_iot_edge_system(
    device_id: str,
    central_url: str,
    auth_token: Optional[str] = None
) -> EdgeSystem:
    """
    Crear sistema edge completo optimizado para IoT.

    Args:
        device_id: ID único del dispositivo
        central_url: URL del nodo central
        auth_token: Token de autenticación opcional

    Returns:
        Sistema edge configurado
    """
    config = EdgeSystemConfig(
        device_id=device_id,
        device_type=EdgeDeviceType.IOT_DEVICE,
        central_node_url=central_url,
        auth_token=auth_token,
        max_memory_mb=128,
        max_storage_mb=50,
        enable_federated_learning=True,
        fl_rounds_per_day=1  # Limitado para IoT
    )

    return EdgeSystem(config)


# Integración con sistema federated existente
def integrate_with_federated_system(
    edge_system: EdgeSystem,
    federated_node_id: str,
    federated_data_cids: List[str]
):
    """
    Integrar sistema edge con el sistema federated existente de AILOOS.

    Args:
        edge_system: Sistema edge a integrar
        federated_node_id: ID del nodo en el sistema federated
        federated_data_cids: CIDs de datos federated
    """
    try:
        logger.info("🔗 Integrando con sistema federated existente...")

        # Aquí se integraría con componentes como:
        # - FederatedDataLoader
        # - SecureGradientAggregator
        # - VersionManager
        # etc.

        # Por ahora, simular integración
        if edge_system.edge_fl:
            # Configurar datos locales para FL
            edge_system.edge_fl.set_local_data(
                data_loader=federated_data_cids,  # Simulado
                dataset_size=len(federated_data_cids) * 100  # Estimación
            )

        logger.info("✅ Integración con sistema federated completada")

    except Exception as e:
        logger.error(f"❌ Error en integración federated: {e}")


if __name__ == "__main__":
    # Demo del sistema edge integrado
    print("🚀 EdgeSystem Integration Demo")

    # Crear sistema para móvil
    edge_system = create_mobile_edge_system(
        device_id="demo_mobile_001",
        central_url="https://federated.ailoos.example.com"
    )

    print("Sistema edge creado")
    print(f"Device ID: {edge_system.config.device_id}")
    print(f"Device Type: {edge_system.config.device_type.value}")

    # Iniciar sistema
    edge_system.start()
    print("Sistema iniciado")

    # Obtener estado
    status = edge_system.get_system_status()
    print(f"Estado del sistema: {status['is_running']}")
    print(f"Componentes activos: {len([k for k, v in status.items() if isinstance(v, dict) and v])}")

    # Simular optimización de modelo
    # model_id = edge_system.optimize_and_deploy_model("/fake/model.pt", "test_model")
    # print(f"Modelo optimizado: {model_id}")

    # Simular sincronización de estado
    sync_id = edge_system.sync_system_status()
    print(f"Sincronización de estado: {sync_id}")

    # Detener sistema
    edge_system.stop()
    print("Sistema detenido")