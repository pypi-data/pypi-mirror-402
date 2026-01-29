"""
Federated Fine-Tuning System - Sistema completo de fine-tuning federado para EmpoorioLM
Integra todos los componentes para aprendizaje automático distribuido y continuo.
"""

import asyncio
import json
import os
import time
from collections import defaultdict
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.logging import get_logger
from ..core.config import get_config
from .federated_fine_tuner import FederatedFineTuner, FineTuningConfig
from .adaptive_domain_adapter import AdaptiveDomainAdapter, analyze_and_adapt
from .continuous_learning_coordinator import ContinuousLearningCoordinator, LearningTrigger, ContinuousLearningConfig, setup_learning_triggers
from .precision_maintenance import PrecisionMaintenance, apply_precision_protection
from .federated_curriculum_learning import FederatedCurriculumLearning, FederatedCurriculumConfig
from .model_evolution_tracker import ModelEvolutionTracker, track_model_evolution
from .node_communicator import NodeCommunicator, NodeUpdate

logger = get_logger(__name__)


class FederatedSystemError(Exception):
    """Base exception for federated system errors."""
    pass


class NodeRegistrationError(FederatedSystemError):
    """Error during node registration."""
    pass


class ComponentInitializationError(FederatedSystemError):
    """Error during component initialization."""
    pass


class CommunicationError(FederatedSystemError):
    """Error in node communication."""
    pass


class LearningSessionError(FederatedSystemError):
    """Error during learning session."""
    pass


class SystemStatus(Enum):
    """Estados del sistema."""
    INITIALIZING = "initializing"
    READY = "ready"
    LEARNING = "learning"
    ADAPTING = "adapting"
    MAINTAINING = "maintaining"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class FederatedFineTuningSystemConfig:
    """Configuración completa del sistema."""
    session_id: str
    base_model_name: str = "microsoft/DialoGPT-medium"
    enable_continuous_learning: bool = True
    enable_domain_adaptation: bool = True
    enable_precision_maintenance: bool = True
    enable_curriculum_learning: bool = True
    enable_evolution_tracking: bool = True
    enable_node_communication: bool = True

    # Configuraciones de componentes
    fine_tuning_config: FineTuningConfig = field(default_factory=FineTuningConfig)
    adaptation_threshold: float = 0.3
    degradation_threshold: float = 0.05
    learning_budget_per_day: float = 10.0
    max_concurrent_tasks: int = 3

    # Configuración de privacidad
    privacy_budget: float = 1.0
    use_differential_privacy: bool = True
    use_homomorphic_encryption: bool = False


@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    total_learning_sessions: int = 0
    total_adaptations: int = 0
    total_maintenance_actions: int = 0
    system_uptime: float = 0.0
    average_learning_efficiency: float = 0.0
    privacy_budget_used: float = 0.0
    domains_adapted: int = 0
    curriculum_completions: int = 0


class FederatedFineTuningSystem:
    """
    Sistema completo de fine-tuning federado para EmpoorioLM.
    Integra todos los componentes para aprendizaje automático distribuido y continuo.
    """

    def __init__(self, config: FederatedFineTuningSystemConfig):
        self.config = config
        self.status = SystemStatus.INITIALIZING
        self.start_time = time.time()
        self.allow_mocks = self._resolve_allow_mocks()

        # Componentes del sistema
        self.fine_tuner: Optional[FederatedFineTuner] = None
        self.domain_adapter: Optional[AdaptiveDomainAdapter] = None
        self.learning_coordinator: Optional[ContinuousLearningCoordinator] = None
        self.precision_maintenance: Optional[PrecisionMaintenance] = None
        self.curriculum_learning: Optional[FederatedCurriculumLearning] = None
        self.evolution_tracker: Optional[ModelEvolutionTracker] = None
        self.node_communicator: Optional[NodeCommunicator] = None

        # Estado del sistema
        self.active_nodes: Dict[str, Dict[str, Any]] = {}
        self.current_task: Optional[Dict[str, Any]] = None
        self.system_metrics = SystemMetrics()

        # Callbacks de integración
        self.event_callbacks: Dict[str, List[Any]] = defaultdict(list)

        # Historial de eficiencia para cálculos
        self._learning_efficiency_history: List[float] = []

        logger.info(f"🚀 Initializing Federated Fine-Tuning System for session {config.session_id}")

        # Inicializar componentes
        self._initialize_components()

    def _initialize_components(self):
        """Inicializar todos los componentes del sistema."""
        try:
            # Fine-tuner federado
            if True:  # Siempre habilitado
                self.fine_tuner = FederatedFineTuner(
                    session_id=self.config.session_id,
                    base_model_name=self.config.base_model_name,
                    config=self.config.fine_tuning_config
                )

            # Adaptador de dominio
            if self.config.enable_domain_adaptation:
                self.domain_adapter = AdaptiveDomainAdapter(
                    model_name=self.config.base_model_name,
                    adaptation_threshold=self.config.adaptation_threshold
                )

            # Coordinador de aprendizaje continuo
            if self.config.enable_continuous_learning:
                cl_config = ContinuousLearningConfig(
                    learning_budget_per_day=self.config.learning_budget_per_day,
                    max_concurrent_tasks=self.config.max_concurrent_tasks
                )
                self.learning_coordinator = ContinuousLearningCoordinator(
                    session_id=self.config.session_id,
                    config=cl_config
                )

            # Mantenimiento de precisión
            if self.config.enable_precision_maintenance:
                self.precision_maintenance = PrecisionMaintenance(
                    model_name=self.config.base_model_name,
                    degradation_threshold=self.config.degradation_threshold
                )

            # Aprendizaje curriculado
            if self.config.enable_curriculum_learning:
                self.curriculum_learning = FederatedCurriculumLearning(
                    session_id=self.config.session_id
                )

            # Rastreador de evolución
            if self.config.enable_evolution_tracking:
                self.evolution_tracker = ModelEvolutionTracker(
                    model_name=self.config.base_model_name,
                    session_id=self.config.session_id
                )

            # Comunicador de nodos
            if self.config.enable_node_communication:
                self.node_communicator = NodeCommunicator(
                    node_id=f"coordinator_{self.config.session_id}",
                    host="0.0.0.0",
                    port=8443
                )
                # Inicializar de manera síncrona para compatibilidad
                if not self.node_communicator.initialize_sync():
                    logger.warning("Failed to initialize node communicator")
                    self.node_communicator = None

            # Configurar integraciones entre componentes
            self._setup_component_integrations()

            self.status = SystemStatus.READY
            logger.info("✅ All system components initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing system components: {e}")
            self.status = SystemStatus.ERROR
            raise ComponentInitializationError(f"Failed to initialize components: {e}") from e

    def _setup_component_integrations(self):
        """Configurar integraciones entre componentes."""
        # Integrar coordinador de aprendizaje con otros componentes
        if self.learning_coordinator:
            # Trigger para fine-tuning
            self.learning_coordinator.register_trigger_callback(
                LearningTrigger.DATA_VOLUME,
                self._handle_learning_trigger
            )

            # Trigger para adaptación de dominio
            self.learning_coordinator.register_trigger_callback(
                LearningTrigger.DOMAIN_SHIFT,
                self._handle_domain_adaptation_trigger
            )

            # Trigger para caída de rendimiento
            self.learning_coordinator.register_trigger_callback(
                LearningTrigger.PERFORMANCE_DROP,
                self._handle_performance_maintenance_trigger
            )

            # Callback para completación de tareas
            self.learning_coordinator.register_task_completion_callback(
                self._handle_task_completion
            )

    async def _handle_learning_trigger(self, trigger_type: LearningTrigger, metadata: Dict[str, Any]):
        """Manejar trigger de aprendizaje."""
        logger.info(f"🎯 Learning trigger activated: {trigger_type.value}")

        if self.fine_tuner and self.active_nodes:
            # Crear tarea de fine-tuning
            task_id = f"auto_ft_{int(time.time())}"
            await self.initiate_federated_fine_tuning(
                dataset_name=f"triggered_{trigger_type.value}",
                domain="auto",
                node_updates=metadata.get("node_updates", [])
            )

    async def _handle_domain_adaptation_trigger(self, trigger_type: LearningTrigger, metadata: Dict[str, Any]):
        """Manejar trigger de adaptación de dominio."""
        logger.info("🎯 Domain adaptation trigger activated")

        if self.domain_adapter:
            # Realizar análisis de dominio
            await self.analyze_and_adapt_domains(
                source_domain=metadata.get("source_domain", "unknown"),
                target_domain=metadata.get("target_domain", "unknown"),
                training_data=metadata.get("training_data", [])
            )

    async def _handle_performance_maintenance_trigger(self, trigger_type: LearningTrigger, metadata: Dict[str, Any]):
        """Manejar trigger de mantenimiento de rendimiento."""
        logger.info("🎯 Performance maintenance trigger activated")

        if self.precision_maintenance:
            # Aplicar medidas de mantenimiento
            await self.apply_precision_maintenance(
                maintenance_method="knowledge_distillation",
                training_data=metadata.get("training_data", [])
            )

    def _handle_task_completion(self, task: Any):
        """Manejar completación de tarea."""
        logger.info(f"✅ Task completed: {task.task_id if hasattr(task, 'task_id') else 'unknown'}")

        # Actualizar métricas del sistema
        self.system_metrics.total_learning_sessions += 1

        # Notificar evolución si está habilitado
        if self.evolution_tracker:
            # Registrar nueva versión del modelo
            version_data = {
                "version_id": f"v_{int(time.time())}",
                "model_cid": f"cid_{int(time.time())}",
                "metrics": {"accuracy": 0.85, "loss": 0.3},  # Placeholder
                "metadata": {"task_completed": task.task_id if hasattr(task, 'task_id') else 'unknown'}
            }
            asyncio.create_task(self._async_track_evolution(version_data))

    async def _async_track_evolution(self, version_data: Dict[str, Any]):
        """Rastrear evolución de manera asíncrona."""
        if self.evolution_tracker:
            await track_model_evolution(self.evolution_tracker, version_data)

    async def start_system(self):
        """Iniciar el sistema completo."""
        if self.status != SystemStatus.READY:
            raise ValueError(f"System not ready. Current status: {self.status.value}")

        logger.info("🚀 Starting Federated Fine-Tuning System")

        # Iniciar coordinador de aprendizaje continuo
        if self.learning_coordinator:
            self.learning_coordinator.start_coordinator()

        # Configurar integraciones asíncronas
        await self._setup_async_integrations()

        self.status = SystemStatus.LEARNING
        logger.info("✅ System started successfully")

    async def _setup_async_integrations(self):
        """Configurar integraciones asíncronas."""
        # Configurar triggers automáticos
        if self.learning_coordinator:
            await setup_learning_triggers(
                self.learning_coordinator,
                fine_tuner=self.fine_tuner,
                domain_adapter=self.domain_adapter
            )

    async def stop_system(self):
        """Detener el sistema completo."""
        logger.info("🛑 Stopping Federated Fine-Tuning System")

        # Detener coordinador
        if self.learning_coordinator:
            self.learning_coordinator.stop_coordinator()

        # Limpiar estado
        self.active_nodes.clear()
        self.current_task = None

        self.status = SystemStatus.STOPPED
        logger.info("✅ System stopped successfully")

    def register_node(self, node_id: str, node_info: Dict[str, Any] = None) -> bool:
        """
        Registrar un nodo en el sistema.

        Args:
            node_id: ID del nodo
            node_info: Información adicional del nodo

        Returns:
            True si se registró correctamente
        """
        # Validaciones de entrada
        if not isinstance(node_id, str) or not node_id.strip():
            raise NodeRegistrationError("Invalid node_id: must be non-empty string")

        if node_info is not None and not isinstance(node_info, dict):
            raise NodeRegistrationError("Invalid node_info: must be dict or None")

        if node_id in self.active_nodes:
            logger.warning(f"⚠️ Node {node_id} already registered")
            return False

        self.active_nodes[node_id] = {
            "node_id": node_id,
            "registered_at": time.time(),
            "status": "active",
            "info": node_info or {},
            "curriculum_enrolled": False,
            "fine_tuning_ready": False
        }

        # Registrar en componentes individuales
        if self.fine_tuner:
            self.fine_tuner.register_node(node_id)

        if self.curriculum_learning:
            self.curriculum_learning.enroll_node(node_id)
            self.active_nodes[node_id]["curriculum_enrolled"] = True

        logger.info(f"✅ Node {node_id} registered in federated system")
        return True

    async def initiate_federated_fine_tuning(self, dataset_name: str, domain: str,
                                           node_updates: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Iniciar sesión de fine-tuning federado.

        Args:
            dataset_name: Nombre del dataset
            domain: Dominio del dataset
            node_updates: Actualizaciones de nodos (opcional)

        Returns:
            Resultados de la sesión
        """
        if not self.fine_tuner:
            raise ValueError("Fine-tuner not available")

        self.status = SystemStatus.LEARNING

        try:
            # Crear tarea de fine-tuning
            task_id = self.fine_tuner.create_fine_tuning_task(dataset_name, domain, 1000)

            # Preparar actualizaciones de nodos
            if not node_updates:
                node_updates = await self._collect_node_updates(round_num=task_id)

            # Ejecutar fine-tuning federado
            result = await self.fine_tuner.execute_federated_fine_tuning_round(node_updates)

            # Completar tarea
            completion_result = self.fine_tuner.complete_fine_tuning_task()

            # Actualizar métricas del sistema
            self.system_metrics.total_learning_sessions += 1
            self._update_system_metrics()
            self.system_metrics.domains_adapted = len(set(
                self.system_metrics.domains_adapted + [domain]
            ))

            # Notificar evolución
            if self.evolution_tracker:
                version_data = {
                    "version_id": f"ft_{task_id}_{int(time.time())}",
                    "model_cid": result.get("model_cid", "unknown"),
                    "metrics": result.get("evaluation_metrics", {}),
                    "metadata": {
                        "task_id": task_id,
                        "domain": domain,
                        "fine_tuning_round": True
                    }
                }
                await self._async_track_evolution(version_data)

            self.status = SystemStatus.READY
            logger.info(f"✅ Federated fine-tuning session completed for {dataset_name}")

            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "completion": completion_result
            }

        except Exception as e:
            logger.error(f"❌ Error in federated fine-tuning: {e}")
            self.status = SystemStatus.ERROR
            return {
                "success": False,
                "error": str(e)
            }

    async def _collect_node_updates(self, round_num: int = 0) -> List[Dict[str, Any]]:
        """
        Recopilar actualizaciones reales de nodos vía comunicación P2P.

        Args:
            round_num: Número de ronda para la actualización

        Returns:
            Lista de actualizaciones de nodos
        """
        if not self.node_communicator:
            if not self.allow_mocks:
                raise FederatedSystemError("Node communicator unavailable in production mode")
            logger.warning("No node communicator available, using mock updates")
            return self._generate_fallback_node_updates()

        try:
            # Iniciar ronda de recolección
            active_node_ids = [node_id for node_id, info in self.active_nodes.items()
                             if info.get("status") == "active"]

            if not active_node_ids:
                logger.warning("No active nodes to collect updates from")
                return []

            # Iniciar ronda
            if not self.node_communicator.start_round_sync(round_num, active_node_ids, deadline_seconds=60):
                logger.error("Failed to start collection round")
                if not self.allow_mocks:
                    raise FederatedSystemError("Failed to start collection round")
                return self._generate_fallback_node_updates()

            # Esperar actualizaciones (simplificado - en producción usar eventos)
            await asyncio.sleep(5)  # Esperar 5 segundos para actualizaciones

            # Obtener información de ronda
            round_info = self.node_communicator.get_current_round_info()
            if not round_info or not round_info.get("collected_updates"):
                logger.warning("No updates collected in round")
                if not self.allow_mocks:
                    return []
                return self._generate_fallback_node_updates()

            # Convertir NodeUpdate a formato esperado
            updates = []
            # Nota: En implementación completa, acceder a collected_updates del comunicador
            # Por ahora, usar fallback ya que el acceso directo no está expuesto
            if not self.allow_mocks:
                raise FederatedSystemError("Collected updates not accessible in production mode")
            return self._generate_fallback_node_updates()

        except Exception as e:
            logger.error(f"Error collecting node updates: {e}")
            if not self.allow_mocks:
                raise
            return self._generate_fallback_node_updates()

    def _generate_fallback_node_updates(self) -> List[Dict[str, Any]]:
        """Generar actualizaciones fallback cuando falla la comunicación real."""
        if not self.allow_mocks:
            raise FederatedSystemError("Fallback node updates are disabled in production mode")
        updates = []
        for node_id in self.active_nodes.keys():
            updates.append({
                "node_id": node_id,
                "lora_weights": {"layer_1": [0.1, 0.2, 0.3]},  # Placeholder
                "metrics": {"accuracy": 0.8, "loss": 0.4},  # Placeholder
                "num_samples": 100
            })
        return updates

    def _resolve_allow_mocks(self) -> bool:
        """Resolver si se permiten mocks/simulaciones según entorno."""
        allow_env = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
        try:
            environment = get_config().environment
        except Exception:
            environment = "development"
        return allow_env or environment != "production"

    async def analyze_and_adapt_domains(self, source_domain: str, target_domain: str,
                                      training_data: List[str]) -> Dict[str, Any]:
        """
        Analizar y adaptar a nuevos dominios.

        Args:
            source_domain: Dominio fuente
            target_domain: Dominio objetivo
            training_data: Datos de entrenamiento

        Returns:
            Resultados de la adaptación
        """
        if not self.domain_adapter:
            return {"success": False, "reason": "domain_adapter_not_enabled"}

        self.status = SystemStatus.ADAPTING

        try:
            # Analizar dominios
            self.domain_adapter.analyze_domain(source_domain, training_data)
            self.domain_adapter.analyze_domain(target_domain, training_data)

            # Detectar shift
            shift = self.domain_adapter.detect_domain_shift(source_domain, target_domain)

            if shift and shift.adaptation_needed:
                # Aplicar adaptación
                result = await analyze_and_adapt(
                    None, self.domain_adapter, source_domain, target_domain, training_data
                )

                self.system_metrics.total_adaptations += 1

                logger.info(f"✅ Domain adaptation completed: {source_domain} -> {target_domain}")
                self.status = SystemStatus.READY

                return {
                    "success": True,
                    "shift_detected": True,
                    "adaptation_performed": True,
                    "result": result
                }
            else:
                self.status = SystemStatus.READY
                return {
                    "success": True,
                    "shift_detected": False,
                    "adaptation_performed": False
                }

        except Exception as e:
            logger.error(f"❌ Error in domain adaptation: {e}")
            self.status = SystemStatus.ERROR
            return {"success": False, "error": str(e)}

    async def apply_precision_maintenance(self, maintenance_method: str,
                                        training_data: List[Tuple[Any, Any]]) -> Dict[str, Any]:
        """
        Aplicar mantenimiento de precisión.

        Args:
            maintenance_method: Método de mantenimiento
            training_data: Datos de entrenamiento

        Returns:
            Resultados del mantenimiento
        """
        if not self.precision_maintenance:
            return {"success": False, "reason": "precision_maintenance_not_enabled"}

        self.status = SystemStatus.MAINTAINING

        try:
            # Establecer modelo teacher si está disponible
            if self.fine_tuner and hasattr(self.fine_tuner, 'global_model'):
                self.precision_maintenance.set_teacher_model(self.fine_tuner.global_model)

            # Aplicar mantenimiento
            result = await apply_precision_protection(
                self.fine_tuner.global_model if self.fine_tuner else None,
                self.precision_maintenance,
                training_data,
                maintenance_method
            )

            self.system_metrics.total_maintenance_actions += 1

            logger.info(f"✅ Precision maintenance applied: {maintenance_method}")
            self.status = SystemStatus.READY

            return {
                "success": True,
                "method": maintenance_method,
                "result": result
            }

        except Exception as e:
            logger.error(f"❌ Error in precision maintenance: {e}")
            self.status = SystemStatus.ERROR
            return {"success": False, "error": str(e)}

    def evaluate_curriculum_progress(self, node_id: str,
                                   evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluar progreso en el currículo de aprendizaje.

        Args:
            node_id: ID del nodo
            evaluation_results: Resultados de evaluación

        Returns:
            Resultados de evaluación del currículo
        """
        if not self.curriculum_learning:
            return {"success": False, "reason": "curriculum_learning_not_enabled"}

        try:
            result = self.curriculum_learning.evaluate_node_progress(node_id, evaluation_results)

            if result.get("stage_completed"):
                self.system_metrics.curriculum_completions += 1
                logger.info(f"🎓 Node {node_id} completed curriculum stage")

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"❌ Error evaluating curriculum progress: {e}")
            return {"success": False, "error": str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        uptime = time.time() - self.start_time

        # Recopilar estados de componentes
        component_status = {}

        if self.fine_tuner:
            component_status["fine_tuner"] = self.fine_tuner.get_fine_tuning_status()

        if self.domain_adapter:
            component_status["domain_adapter"] = self.domain_adapter.get_adaptation_stats()

        if self.learning_coordinator:
            component_status["learning_coordinator"] = self.learning_coordinator.get_coordinator_status()

        if self.precision_maintenance:
            component_status["precision_maintenance"] = self.precision_maintenance.get_precision_status()

        if self.curriculum_learning:
            component_status["curriculum_learning"] = self.curriculum_learning.get_curriculum_status()

        if self.evolution_tracker:
            component_status["evolution_tracker"] = self.evolution_tracker.get_evolution_summary()

        return {
            "system_status": self.status.value,
            "session_id": self.config.session_id,
            "uptime_seconds": uptime,
            "active_nodes": len(self.active_nodes),
            "current_task": self.current_task,
            "system_metrics": {
                "total_learning_sessions": self.system_metrics.total_learning_sessions,
                "total_adaptations": self.system_metrics.total_adaptations,
                "total_maintenance_actions": self.system_metrics.total_maintenance_actions,
                "domains_adapted": self.system_metrics.domains_adapted,
                "curriculum_completions": self.system_metrics.curriculum_completions,
                "average_learning_efficiency": self.system_metrics.average_learning_efficiency,
                "privacy_budget_used": self.system_metrics.privacy_budget_used
            },
            "component_status": component_status,
            "config": {
                "enable_continuous_learning": self.config.enable_continuous_learning,
                "enable_domain_adaptation": self.config.enable_domain_adaptation,
                "enable_precision_maintenance": self.config.enable_precision_maintenance,
                "enable_curriculum_learning": self.config.enable_curriculum_learning,
                "enable_evolution_tracking": self.config.enable_evolution_tracking
            }
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Obtener evaluación de salud del sistema."""
        health_indicators = []

        # Verificar componentes activos
        components_active = sum([
            self.fine_tuner is not None,
            self.domain_adapter is not None,
            self.learning_coordinator is not None,
            self.precision_maintenance is not None,
            self.curriculum_learning is not None,
            self.evolution_tracker is not None
        ])

        health_indicators.append({
            "name": "component_integrity",
            "value": components_active / 6.0,
            "status": "healthy" if components_active >= 4 else "warning"
        })

        # Verificar nodos activos
        nodes_active = len([n for n in self.active_nodes.values() if n["status"] == "active"])
        health_indicators.append({
            "name": "node_participation",
            "value": min(nodes_active / 10.0, 1.0),  # Normalizar
            "status": "healthy" if nodes_active >= 3 else "warning"
        })

        # Verificar estado del sistema
        system_healthy = self.status in [SystemStatus.READY, SystemStatus.LEARNING]
        health_indicators.append({
            "name": "system_status",
            "value": 1.0 if system_healthy else 0.0,
            "status": "healthy" if system_healthy else "critical"
        })

        # Calcular salud general
        avg_health = sum(ind["value"] for ind in health_indicators) / len(health_indicators)
        critical_indicators = sum(1 for ind in health_indicators if ind["status"] == "critical")

        overall_status = "healthy"
        if critical_indicators > 0:
            overall_status = "critical"
        elif avg_health < 0.7:
            overall_status = "warning"

        return {
            "overall_health": avg_health,
            "overall_status": overall_status,
            "indicators": health_indicators,
            "recommendations": self._generate_health_recommendations(health_indicators)
        }

    def _generate_health_recommendations(self, indicators: List[Dict[str, Any]]) -> List[str]:
        """Generar recomendaciones basadas en indicadores de salud."""
        recommendations = []

        for indicator in indicators:
            if indicator["status"] == "critical":
                if indicator["name"] == "system_status":
                    recommendations.append("restart_system")
                elif indicator["name"] == "component_integrity":
                    recommendations.append("check_component_initialization")
                elif indicator["name"] == "node_participation":
                    recommendations.append("recruit_more_nodes")

            elif indicator["status"] == "warning":
                if indicator["name"] == "node_participation":
                    recommendations.append("increase_node_engagement")
                elif indicator["name"] == "component_integrity":
                    recommendations.append("verify_component_configuration")

        if not recommendations:
            recommendations.append("system_operating_normally")

        return recommendations

    def _update_system_metrics(self):
        """Actualizar métricas calculadas dinámicamente."""
        # Calcular eficiencia de aprendizaje promedio
        if self.system_metrics.total_learning_sessions > 0:
            # Simular eficiencia basada en sesiones (en producción usar métricas reales)
            current_efficiency = 0.8 + (self.system_metrics.total_learning_sessions * 0.01)
            self._learning_efficiency_history.append(current_efficiency)
            self.system_metrics.average_learning_efficiency = sum(self._learning_efficiency_history) / len(self._learning_efficiency_history)

        # Calcular uptime
        self.system_metrics.system_uptime = time.time() - self.start_time

        # Calcular presupuesto de privacidad usado (simulado)
        if self.config.use_differential_privacy:
            self.system_metrics.privacy_budget_used = min(1.0, self.system_metrics.total_learning_sessions * 0.05)


# Funciones de conveniencia
# NOTA: Las siguientes funciones (initialize_system_with_nodes, run_autonomous_learning_cycle)
# deberían refactorizarse a un módulo de testing separado como test_federated_system.py

def create_federated_fine_tuning_system(config: FederatedFineTuningSystemConfig) -> FederatedFineTuningSystem:
    """Crear un nuevo sistema completo de fine-tuning federado."""
    return FederatedFineTuningSystem(config)


async def initialize_system_with_nodes(system: FederatedFineTuningSystem,
                                     node_ids: List[str]) -> Dict[str, Any]:
    """
    Inicializar sistema con nodos específicos.

    Args:
        system: Sistema de fine-tuning
        node_ids: IDs de nodos a registrar

    Returns:
        Resultados de inicialización
    """
    registered_nodes = 0

    for node_id in node_ids:
        if system.register_node(node_id):
            registered_nodes += 1

    # Iniciar sistema
    await system.start_system()

    return {
        "system_initialized": True,
        "nodes_registered": registered_nodes,
        "total_nodes": len(node_ids),
        "system_status": system.get_system_status()
    }


async def run_autonomous_learning_cycle(system: FederatedFineTuningSystem,
                                       cycles: int = 5) -> Dict[str, Any]:
    """
    Ejecutar ciclo de aprendizaje autónomo.

    Args:
        system: Sistema de fine-tuning
        cycles: Número de ciclos a ejecutar

    Returns:
        Resultados del ciclo de aprendizaje
    """
    results = []

    for cycle in range(cycles):
        logger.info(f"🔄 Starting autonomous learning cycle {cycle + 1}/{cycles}")

        # Cargar datos de entrenamiento reales
        try:
            from datasets import load_dataset
            # Usar un dataset de ejemplo para fine-tuning de lenguaje
            dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")
            training_data = dataset["text"][:100]  # Primeros 100 ejemplos
        except ImportError:
            if not system.allow_mocks:
                raise
            logger.warning("datasets library not available, using mock data")
            training_data = [f"Sample text {i}" for i in range(100)]
        except Exception as e:
            if not system.allow_mocks:
                raise
            logger.error(f"Error loading dataset: {e}, using mock data")
            training_data = [f"Sample text {i}" for i in range(100)]

        # Ejecutar fine-tuning
        ft_result = await system.initiate_federated_fine_tuning(
            dataset_name=f"cycle_{cycle}",
            domain="autonomous",
            node_updates=None  # Dejar que _collect_node_updates maneje
        )

        # Evaluar currículo para nodos
        curriculum_results = []
        for node_id in system.active_nodes.keys():
            eval_result = system.evaluate_curriculum_progress(
                node_id,
                {"accuracy": 0.8 + cycle * 0.02, "f1_score": 0.75 + cycle * 0.02}
            )
            curriculum_results.append(eval_result)

        # Verificar salud del sistema
        health = system.get_system_health()

        cycle_result = {
            "cycle": cycle + 1,
            "fine_tuning": ft_result,
            "curriculum_evaluations": curriculum_results,
            "system_health": health
        }

        results.append(cycle_result)

        # Pequeña pausa entre ciclos
        await asyncio.sleep(0.1)

    return {
        "cycles_completed": cycles,
        "results": results,
        "final_system_status": system.get_system_status()
    }
