"""
Integración principal Ailoos-DracmaS.

Clase principal que combina todos los módulos de integración
para proporcionar una interfaz unificada de alto nivel.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
import time

from .bridge_client import get_bridge_client, BridgeClient, BridgeClientError
from .dracmas_config import get_dracmas_config, DracmaSConfig
from .ailoos_nodes import get_ailoos_nodes_manager, AiloosNodesManager, NodeInfo
from .work_reporting import get_work_reporting_manager, WorkReportingManager, WorkReport
from .quantum_integration import get_quantum_integration_manager, QuantumIntegrationManager, TrainingProof, ValidationResult
from .rewards_manager import get_rewards_manager, RewardsManager, PendingRewards, RewardClaim
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IntegrationStatus:
    """Estado general de la integración."""
    bridge_connected: bool
    nodes_registered: int
    pending_rewards: float
    last_sync: int
    errors: Optional[List[str]] = None


@dataclass
class NodeRegistrationResult:
    """Resultado de registro de nodo."""
    success: bool
    node_info: Optional[NodeInfo] = None
    error: Optional[str] = None


@dataclass
class WorkSubmissionResult:
    """Resultado de envío de trabajo."""
    success: bool
    work_report: Optional[WorkReport] = None
    validation_result: Optional[ValidationResult] = None
    error: Optional[str] = None


class AiloosDracmasIntegrationError(Exception):
    """Error en integración Ailoos-DracmaS."""
    pass


class AiloosDracmasIntegration:
    """
    Integración principal Ailoos-DracmaS.

    Combina todos los módulos de integración para proporcionar
    operaciones de alto nivel con manejo unificado de errores y logging.
    """

    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """
        Inicializar integración principal.

        Args:
            bridge_client: Cliente del puente opcional
        """
        self.bridge_client = bridge_client or get_bridge_client()
        self.config = get_dracmas_config()

        # Inicializar gestores
        self.nodes_manager = get_ailoos_nodes_manager()
        self.work_reporting = get_work_reporting_manager()
        self.quantum_integration = get_quantum_integration_manager()
        self.rewards_manager = get_rewards_manager()

        # Estado interno
        self._last_status_check = 0
        self._cached_status: Optional[IntegrationStatus] = None

        logger.info("🚀 AiloosDracmasIntegration initialized")

    async def get_integration_status(self, force_refresh: bool = False) -> IntegrationStatus:
        """
        Obtener estado general de la integración.

        Args:
            force_refresh: Forzar actualización del estado

        Returns:
            Estado de la integración
        """
        try:
            current_time = int(time.time())

            # Usar cache si no ha expirado (5 minutos)
            if not force_refresh and self._cached_status and (current_time - self._last_status_check) < 300:
                return self._cached_status

            logger.info("📊 Checking integration status...")

            errors = []

            # Verificar conexión con puente
            bridge_connected = False
            try:
                status = await self.bridge_client.get_bridge_status()
                bridge_connected = status.get('success', False)
            except Exception as e:
                errors.append(f"Bridge connection error: {e}")
                logger.warning(f"Bridge status check failed: {e}")

            # Contar nodos registrados (simulado - en producción vendria de BD)
            nodes_registered = 0  # Placeholder

            # Calcular recompensas pendientes para el nodo configurado
            node_id = os.getenv('AILOOS_NODE_ID', 'default_node')
            pending_rewards = 0.0
            try:
                pending = await self.rewards_manager.get_pending_rewards(node_id)
                pending_rewards = pending.amount
            except Exception as e:
                errors.append(f"Pending rewards error: {e}")
                logger.warning(f"Pending rewards check failed: {e}")

            status = IntegrationStatus(
                bridge_connected=bridge_connected,
                nodes_registered=nodes_registered,
                pending_rewards=pending_rewards,
                last_sync=current_time,
                errors=errors if errors else None
            )

            # Cachear resultado
            self._cached_status = status
            self._last_status_check = current_time

            logger.info(f"✅ Integration status checked: bridge={bridge_connected}, nodes={nodes_registered}")
            return status

        except Exception as e:
            logger.error(f"❌ Error checking integration status: {e}")
            raise AiloosDracmasIntegrationError(f"Status check error: {e}")

    async def register_node_high_level(
        self,
        node_id: str,
        hardware_specs: Dict[str, Any],
        location: str
    ) -> NodeRegistrationResult:
        """
        Registrar nodo con interfaz de alto nivel.

        Args:
            node_id: ID único del nodo
            hardware_specs: Especificaciones de hardware
            location: Ubicación del nodo

        Returns:
            Resultado del registro
        """
        try:
            logger.info(f"🔧 High-level node registration for {node_id}")

            # Extraer especificaciones de hardware
            cpu_score = hardware_specs.get('cpu_score', 50)
            gpu_score = hardware_specs.get('gpu_score', 0)
            ram_gb = hardware_specs.get('ram_gb', 8)

            # Registrar nodo
            result = await self.nodes_manager.register_ailoos_node(
                node_id=node_id,
                cpu_score=cpu_score,
                gpu_score=gpu_score,
                ram_gb=ram_gb,
                location=location
            )

            if result.get('success'):
                # Obtener información del nodo registrado
                node_info = await self.nodes_manager.get_node_info(node_id)

                return NodeRegistrationResult(
                    success=True,
                    node_info=node_info
                )
            else:
                return NodeRegistrationResult(
                    success=False,
                    error=result.get('error', 'Registration failed')
                )

        except Exception as e:
            logger.error(f"❌ Error in high-level node registration for {node_id}: {e}")
            return NodeRegistrationResult(
                success=False,
                error=str(e)
            )

    async def submit_training_work_high_level(
        self,
        node_id: str,
        dataset_id: str,
        model_weights: bytes,
        training_metrics: Dict[str, Any],
        quantum_entropy: Optional[bytes] = None
    ) -> WorkSubmissionResult:
        """
        Enviar trabajo de entrenamiento con interfaz de alto nivel.

        Args:
            node_id: ID del nodo
            dataset_id: ID del dataset
            model_weights: Pesos del modelo entrenado
            training_metrics: Métricas de entrenamiento
            quantum_entropy: Entropía cuántica opcional

        Returns:
            Resultado del envío de trabajo
        """
        try:
            logger.info(f"🚀 High-level work submission for node {node_id}")

            # Calcular poder computacional basado en métricas
            compute_power = self._calculate_compute_power(training_metrics)

            # Generar proof
            proof = await self.quantum_integration.generate_training_proof(
                node_id=node_id,
                dataset_id=dataset_id,
                compute_power=compute_power,
                model_weights=model_weights,
                training_metrics=training_metrics,
                quantum_entropy=quantum_entropy
            )

            # Validar localmente
            validation_result = await self.quantum_integration.validate_training_locally(proof)

            if not validation_result.is_valid:
                return WorkSubmissionResult(
                    success=False,
                    error=f"Local validation failed: {validation_result.errors}"
                )

            # Enviar trabajo validado
            submission_result = await self.quantum_integration.submit_validated_work(
                proof=proof,
                validation_result=validation_result
            )

            if submission_result.get('success'):
                # Crear reporte de trabajo
                work_report = WorkReport(
                    node_id=node_id,
                    units=compute_power,
                    dataset_id=dataset_id,
                    timestamp=int(time.time()),
                    proof_hash=proof.model_hash,
                    validated=True
                )

                return WorkSubmissionResult(
                    success=True,
                    work_report=work_report,
                    validation_result=validation_result
                )
            else:
                return WorkSubmissionResult(
                    success=False,
                    error=submission_result.get('error', 'Submission failed')
                )

        except Exception as e:
            logger.error(f"❌ Error in high-level work submission for node {node_id}: {e}")
            return WorkSubmissionResult(
                success=False,
                error=str(e)
            )

    async def claim_all_pending_rewards(self) -> Dict[str, Any]:
        """
        Reclamar todas las recompensas pendientes (simulado).

        En producción, esto obtendría la lista de nodos activos
        y reclamaría recompensas para todos ellos.

        Returns:
            Resultado del reclamo masivo
        """
        try:
            logger.info("💰 Claiming all pending rewards...")

            # Simular lista de nodos activos
            active_nodes = [f"node_{i}" for i in range(1, 11)]  # 10 nodos de ejemplo

            # Reclamar en lote
            result = await self.rewards_manager.batch_claim_rewards(active_nodes)

            logger.info(f"✅ Mass reward claim completed: {result['successful_count']} successful")
            return result

        except Exception as e:
            logger.error(f"❌ Error in mass reward claim: {e}")
            raise AiloosDracmasIntegrationError(f"Mass claim error: {e}")

    async def get_node_dashboard(self, node_id: str) -> Dict[str, Any]:
        """
        Obtener dashboard completo de un nodo.

        Args:
            node_id: ID del nodo

        Returns:
            Información completa del dashboard
        """
        try:
            logger.info(f"📊 Getting dashboard for node {node_id}")

            # Obtener información del nodo
            node_info = await self.nodes_manager.get_node_info(node_id)

            # Obtener recompensas pendientes
            pending_rewards = await self.rewards_manager.get_pending_rewards(node_id)

            # Simular estadísticas adicionales
            stats = {
                "total_work_units": 1250,
                "successful_validations": 45,
                "uptime_percentage": 98.5,
                "last_activity": int(time.time()) - 3600
            }

            dashboard = {
                "node_info": node_info,
                "pending_rewards": pending_rewards,
                "statistics": stats,
                "generated_at": int(time.time())
            }

            logger.info(f"✅ Dashboard generated for node {node_id}")
            return dashboard

        except Exception as e:
            logger.error(f"❌ Error getting dashboard for node {node_id}: {e}")
            raise AiloosDracmasIntegrationError(f"Dashboard error: {e}")

    async def perform_system_health_check(self) -> Dict[str, Any]:
        """
        Realizar verificación de salud del sistema.

        Returns:
            Resultado de la verificación de salud
        """
        try:
            logger.info("🏥 Performing system health check...")

            health_checks = []

            # Verificar conexión con puente
            try:
                bridge_status = await self.bridge_client.get_bridge_status()
                health_checks.append({
                    "component": "bridge",
                    "status": "healthy" if bridge_status.get('success') else "unhealthy",
                    "details": bridge_status
                })
            except Exception as e:
                health_checks.append({
                    "component": "bridge",
                    "status": "unhealthy",
                    "error": str(e)
                })

            # Verificar configuración
            try:
                config_valid = self.config.contracts.validate_addresses() and \
                              self.config.network.validate_rpc_url() and \
                              self.config.bridge.validate_bridge_url()
                health_checks.append({
                    "component": "configuration",
                    "status": "healthy" if config_valid else "unhealthy"
                })
            except Exception as e:
                health_checks.append({
                    "component": "configuration",
                    "status": "unhealthy",
                    "error": str(e)
                })

            # Verificar gestores
            managers_status = [
                ("nodes_manager", self.nodes_manager),
                ("work_reporting", self.work_reporting),
                ("quantum_integration", self.quantum_integration),
                ("rewards_manager", self.rewards_manager)
            ]

            for name, manager in managers_status:
                health_checks.append({
                    "component": name,
                    "status": "healthy",  # Asumir healthy si se inicializó
                    "details": f"{name} initialized"
                })

            overall_status = "healthy" if all(
                check["status"] == "healthy" for check in health_checks
            ) else "degraded"

            result = {
                "overall_status": overall_status,
                "checks": health_checks,
                "timestamp": int(time.time())
            }

            logger.info(f"✅ Health check completed: {overall_status}")
            return result

        except Exception as e:
            logger.error(f"❌ Error in health check: {e}")
            raise AiloosDracmasIntegrationError(f"Health check error: {e}")

    def _calculate_compute_power(self, training_metrics: Dict[str, Any]) -> int:
        """Calcular poder computacional basado en métricas."""
        # Lógica simplificada - en producción sería más sofisticada
        epochs = training_metrics.get('epochs', 1)
        batch_size = training_metrics.get('batch_size', 32)
        accuracy = training_metrics.get('accuracy', 0.5)

        # Fórmula básica: epochs * batch_size * (accuracy * 100)
        compute_power = int(epochs * batch_size * (accuracy * 100))
        return max(compute_power, 1)  # Mínimo 1

    @asynccontextmanager
    async def managed_operation(self, operation_name: str):
        """
        Context manager para operaciones gestionadas.

        Args:
            operation_name: Nombre de la operación
        """
        start_time = time.time()
        logger.info(f"▶️ Starting operation: {operation_name}")

        try:
            yield
            duration = time.time() - start_time
            logger.info(f"✅ Operation completed: {operation_name} ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Operation failed: {operation_name} ({duration:.2f}s) - {e}")
            raise


# Instancia global de la integración
_integration_instance: Optional[AiloosDracmasIntegration] = None


def get_ailoos_dracmas_integration() -> AiloosDracmasIntegration:
    """Obtener instancia global de la integración Ailoos-DracmaS."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = AiloosDracmasIntegration()
    return _integration_instance


def create_ailoos_dracmas_integration(bridge_client: Optional[BridgeClient] = None) -> AiloosDracmasIntegration:
    """Crear nueva instancia de la integración Ailoos-DracmaS."""
    return AiloosDracmasIntegration(bridge_client)
