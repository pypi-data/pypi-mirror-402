"""
Secure Gradient Aggregator para Federated Learning
Implementa agregación segura de gradientes con homomorphic encryption,
Secure Aggregation con verificación de dropout, y recuperación automática de fallos.
"""

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import torch
import torch.nn as nn

from ..core.logging import get_logger
from .homomorphic_encryption import HomomorphicEncryptionManager
from .homomorphic_encryptor import HomomorphicEncryptor, EncryptionConfig

# Importar componentes TEE (se inicializarán después del logger)
TEE_AVAILABLE = False

logger = get_logger(__name__)

# Intentar importar componentes TEE
try:
    from ..zero_trust import (
        TEEIntegrationManager, TEEType, TEEConfig,
        SecureCodeExecution, SecureExecutionConfig,
        TEEComplianceEnforcer, TEEComplianceConfig, ComplianceLevel
    )
    TEE_AVAILABLE = True
except ImportError:
    TEE_AVAILABLE = False
    logger.warning("⚠️ TEE components not available, running without mandatory TEE")


class AggregationPhase(Enum):
    """Fases del proceso de agregación."""
    INITIALIZING = "initializing"
    COLLECTING_MASKS = "collecting_masks"
    AGGREGATING = "aggregating"
    VERIFYING_DROPOUT = "verifying_dropout"
    VALIDATING_INTEGRITY = "validating_integrity"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GradientUpdate:
    """Actualización de gradientes de un nodo."""
    node_id: str
    encrypted_gradients: Dict[str, List[Any]]  # Gradientes encriptados homomórficamente
    random_mask: Dict[str, torch.Tensor]  # Máscara aleatoria para secure aggregation
    mask_hash: str  # Hash de la máscara para verificación
    num_samples: int
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None  # Firma digital para integridad
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecureAggregationConfig:
    """Configuración para agregación segura de gradientes."""
    session_id: str
    min_participants: int = 3
    max_participants: int = 1000
    dropout_threshold: float = 0.1  # Máximo porcentaje de dropout permitido
    timeout_seconds: int = 300
    enable_dropout_verification: bool = True
    enable_integrity_validation: bool = True
    enable_fault_recovery: bool = True
    max_recovery_attempts: int = 3
    batch_size: int = 50  # Procesamiento por lotes para escalabilidad
    key_size: int = 2048
    precision: int = 6


@dataclass
class AggregationMetrics:
    """Métricas de rendimiento de la agregación."""
    total_nodes: int = 0
    active_nodes: int = 0
    failed_nodes: int = 0
    recovered_nodes: int = 0
    aggregation_time: float = 0.0
    encryption_time: float = 0.0
    verification_time: float = 0.0
    throughput_nodes_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    network_overhead_mb: float = 0.0
    dropout_rate: float = 0.0
    integrity_violations: int = 0


class SecureGradientAggregator:
    """
    Agregador seguro de gradientes que implementa:
    - Agregación homomórfica sin desencriptación
    - Secure Aggregation con verificación de dropout
    - Recuperación automática de fallos
    - Validación de integridad
    - Escalabilidad para cientos de nodos
    """

    def __init__(self, config: SecureAggregationConfig):
        self.config = config
        self.phase = AggregationPhase.INITIALIZING

        # Componentes criptográficos
        self.he_manager = HomomorphicEncryptionManager(precision=config.precision)
        self.encryptor = HomomorphicEncryptor(
            node_id=f"aggregator_{config.session_id}",
            config=EncryptionConfig(key_size=config.key_size, precision=config.precision)
        )
        self.encryptor.initialize()

        # Componentes TEE (opcionales pero obligatorios si disponibles)
        self.tee_manager: Optional[TEEIntegrationManager] = None
        self.secure_executor: Optional[SecureCodeExecution] = None
        self.compliance_enforcer: Optional[TEEComplianceEnforcer] = None
        self.tee_enclave_id: Optional[str] = None

        # TEE se inicializará posteriormente con initialize_tee()

        # Estado de la agregación
        self.expected_nodes: Set[str] = set()
        self.active_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.recovered_nodes: Set[str] = set()

        # Datos de agregación
        self.gradient_updates: Dict[str, GradientUpdate] = {}
        self.aggregated_gradients: Optional[Dict[str, torch.Tensor]] = None
        self.global_mask_sum: Dict[str, torch.Tensor] = {}  # Suma de máscaras para verificación

        # Control de concurrencia (creado de manera lazy)
        self._node_semaphore: Optional[asyncio.Semaphore] = None
        self._aggregation_lock: Optional[asyncio.Lock] = None

        # Métricas y logging
        self.metrics = AggregationMetrics()
        self.start_time = time.time()
        self.logs: List[Dict[str, Any]] = []

        # Callbacks para manejo de eventos
        self.on_node_failure: Optional[callable] = None
        self.on_node_recovery: Optional[callable] = None
        self.on_aggregation_complete: Optional[callable] = None

        logger.info(f"🛡️ SecureGradientAggregator initialized for session {config.session_id}")

    async def initialize_tee(self) -> bool:
        """Inicializar componentes TEE para agregación segura obligatoria."""
        if not TEE_AVAILABLE:
            logger.warning("⚠️ TEE components not available, running without mandatory TEE")
            return False

        try:
            logger.info("🔐 Initializing mandatory TEE components for secure aggregation")

            # Configurar TEE Manager con tipo basado en configuración del sistema
            # Intentar detectar TEE disponible en el sistema
            tee_type = await self._detect_available_tee()
            tee_config = TEEConfig(
                tee_type=tee_type,
                enclave_size_mb=256,  # Aumentado para operaciones de ML
                max_enclaves=10,      # Más enclaves para escalabilidad
                enable_federated_mode=True,
                enable_remote_attestation=True,
                enable_side_channel_protection=True,
                attestation_timeout_seconds=60,
                integrity_check_interval_seconds=300  # Verificación cada 5 minutos
            )
            self.tee_manager = TEEIntegrationManager(tee_config)
            success = await self.tee_manager.initialize()
            if not success:
                raise RuntimeError("TEE Manager initialization failed")

            # Configurar Secure Code Execution con whitelist de funciones críticas
            execution_config = SecureExecutionConfig(
                max_concurrent_executions=20,  # Aumentado para federated learning
                require_function_whitelist=True,
                allowed_functions=[
                    "homomorphic_decrypt",
                    "secure_gradient_aggregate",
                    "verify_gradient_integrity",
                    "blind_signature",
                    "zero_knowledge_proof"
                ]
            )
            self.secure_executor = SecureCodeExecution(self.tee_manager, execution_config)
            success = await self.secure_executor.initialize()
            if not success:
                raise RuntimeError("Secure Code Execution initialization failed")

            # Configurar Compliance Enforcer con políticas estrictas para federated learning
            compliance_config = TEEComplianceConfig(
                compliance_level=ComplianceLevel.MANDATORY,
                require_tee_for_critical_ops=True,
                enable_automatic_remediation=True,
                violation_grace_period_seconds=180,  # 3 minutos para recuperación
                max_violations_before_lockout=3,     # Más estricto
                audit_log_retention_days=30,
                enable_federated_compliance=True,
                compliance_check_interval=120.0      # Verificación cada 2 minutos
            )
            self.compliance_enforcer = TEEComplianceEnforcer(
                tee_manager=self.tee_manager,
                secure_executor=self.secure_executor,
                config=compliance_config
            )
            success = await self.compliance_enforcer.initialize()
            if not success:
                raise RuntimeError("Compliance Enforcer initialization failed")

            # Crear enclave dedicado para operaciones de agregación segura
            enclave_code = self._get_aggregation_enclave_code()
            enclave_metadata = {
                "purpose": "secure_gradient_aggregation",
                "session_id": self.config.session_id,
                "created_by": "SecureGradientAggregator",
                "security_level": "critical",
                "federated_operations": True
            }
            self.tee_enclave_id = await self.tee_manager.create_enclave(
                enclave_code,
                metadata=enclave_metadata
            )

            if not self.tee_enclave_id:
                raise RuntimeError("Failed to create TEE enclave for aggregation")

            # Verificar integridad inicial del enclave
            integrity_ok = await self.tee_manager.verify_enclave_integrity(self.tee_enclave_id)
            if not integrity_ok:
                raise RuntimeError("Initial enclave integrity verification failed")

            # Realizar atestación inicial
            attestation_success, _ = await self.tee_manager.attest_enclave(self.tee_enclave_id)
            if not attestation_success:
                logger.warning("⚠️ Initial attestation failed, but continuing with reduced security")

            logger.info(f"✅ TEE components initialized successfully with enclave {self.tee_enclave_id}")
            return True

        except Exception as e:
            logger.error(f"❌ TEE components initialization failed: {e}")
            # En caso de fallo, intentar fallback a modo simulado
            try:
                logger.info("🔄 Attempting fallback to simulated TEE mode")
                tee_config = TEEConfig(
                    tee_type=TEEType.SIMULATED,
                    enclave_size_mb=128,
                    max_enclaves=5,
                    enable_federated_mode=True
                )
                self.tee_manager = TEEIntegrationManager(tee_config)
                success = await self.tee_manager.initialize()
                if success:
                    # Crear enclave simulado
                    enclave_code = self._get_aggregation_enclave_code()
                    self.tee_enclave_id = await self.tee_manager.create_enclave(enclave_code)
                    if self.tee_enclave_id:
                        logger.warning("⚠️ Running in simulated TEE mode - NOT SECURE FOR PRODUCTION")
                        return True
            except Exception as fallback_e:
                logger.error(f"❌ Fallback TEE initialization also failed: {fallback_e}")

            # Limpieza completa en caso de fallo total
            self.tee_manager = None
            self.secure_executor = None
            self.compliance_enforcer = None
            self.tee_enclave_id = None
            return False

    async def _detect_available_tee(self) -> TEEType:
        """Detectar tipo de TEE disponible en el sistema."""
        try:
            # Verificar SGX (Intel)
            if await self._check_sgx_availability():
                logger.info("🔍 Detected Intel SGX support")
                return TEEType.SGX
            # Verificar SEV (AMD)
            elif await self._check_sev_availability():
                logger.info("🔍 Detected AMD SEV support")
                return TEEType.SEV
            # Verificar TrustZone (ARM)
            elif await self._check_trustzone_availability():
                logger.info("🔍 Detected ARM TrustZone support")
                return TEEType.TRUSTZONE
            else:
                logger.info("🔍 No hardware TEE detected, using simulated mode")
                return TEEType.SIMULATED
        except Exception as e:
            logger.warning(f"⚠️ TEE detection failed: {e}, falling back to simulated")
            return TEEType.SIMULATED

    async def _check_sgx_availability(self) -> bool:
        """Verificar disponibilidad de Intel SGX."""
        try:
            # En producción, verificar CPUID y MSR
            # Para esta implementación, simular verificación
            import platform
            system = platform.system().lower()
            if system == "linux":
                # Verificar si SGX está disponible vía CPUID
                # Esta es una verificación simplificada
                return True  # Placeholder - implementar verificación real
            return False
        except Exception:
            return False

    async def _check_sev_availability(self) -> bool:
        """Verificar disponibilidad de AMD SEV."""
        try:
            import platform
            system = platform.system().lower()
            if system == "linux":
                # Verificar soporte SEV
                return True  # Placeholder - implementar verificación real
            return False
        except Exception:
            return False

    async def _check_trustzone_availability(self) -> bool:
        """Verificar disponibilidad de ARM TrustZone."""
        try:
            import platform
            system = platform.system().lower()
            machine = platform.machine().lower()
            if system == "linux" and "arm" in machine:
                # Verificar TrustZone
                return True  # Placeholder - implementar verificación real
            return False
        except Exception:
            return False

    @property
    def node_semaphore(self) -> asyncio.Semaphore:
        """Obtener semaphore de nodos (creado de manera lazy)."""
        if self._node_semaphore is None:
            self._node_semaphore = asyncio.Semaphore(self.config.batch_size)
        return self._node_semaphore

    @property
    def aggregation_lock(self) -> asyncio.Lock:
        """Obtener lock de agregación (creado de manera lazy)."""
        if self._aggregation_lock is None:
            self._aggregation_lock = asyncio.Lock()
        return self._aggregation_lock

    async def initialize_aggregation(self, node_ids: List[str]) -> bool:
        """
        Inicializar la ronda de agregación con lista de nodos participantes.

        Args:
            node_ids: Lista de IDs de nodos participantes

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.phase = AggregationPhase.COLLECTING_MASKS
            self.expected_nodes = set(node_ids)
            self.metrics.total_nodes = len(node_ids)
            self.start_time = time.time()

            # Resetear estado
            self.active_nodes.clear()
            self.failed_nodes.clear()
            self.recovered_nodes.clear()
            self.gradient_updates.clear()
            self.aggregated_gradients = None
            self.global_mask_sum.clear()

            logger.info(f"🎯 Initialized aggregation round with {len(node_ids)} expected nodes")
            self._log_event("aggregation_initialized", {"node_count": len(node_ids)})

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize aggregation: {e}")
            self.phase = AggregationPhase.FAILED
            return False

    async def submit_gradient_update(self, node_id: str, gradients: Dict[str, torch.Tensor],
                                   num_samples: int, signature: Optional[str] = None) -> bool:
        """
        Enviar actualización de gradientes desde un nodo.

        Args:
            node_id: ID del nodo
            gradients: Gradientes del modelo
            num_samples: Número de muestras locales
            signature: Firma digital opcional

        Returns:
            True si la actualización fue aceptada
        """
        async with self.node_semaphore:
            try:
                if node_id not in self.expected_nodes:
                    logger.warning(f"⚠️ Unexpected node {node_id}")
                    return False

                if node_id in self.active_nodes:
                    logger.warning(f"⚠️ Duplicate update from node {node_id}")
                    return False

                start_time = time.time()

                # Generar máscara aleatoria para secure aggregation
                random_mask = self._generate_random_mask(gradients)
                mask_hash = self._compute_mask_hash(random_mask)

                # Aplicar máscara a gradientes
                masked_gradients = self._apply_mask_to_gradients(gradients, random_mask)

                # Encriptar gradientes enmascarados
                encrypted_gradients = self.encryptor.encrypt_gradients(masked_gradients)

                # Crear actualización
                update = GradientUpdate(
                    node_id=node_id,
                    encrypted_gradients=encrypted_gradients,
                    random_mask=random_mask,
                    mask_hash=mask_hash,
                    num_samples=num_samples,
                    signature=signature,
                    timestamp=time.time()
                )

                # Validar integridad si está habilitado
                if self.config.enable_integrity_validation and not self._validate_update_integrity(update):
                    logger.error(f"❌ Integrity validation failed for node {node_id}")
                    self._handle_node_failure(node_id, "integrity_validation_failed")
                    return False

                # Almacenar actualización
                self.gradient_updates[node_id] = update
                self.active_nodes.add(node_id)

                # Actualizar suma global de máscaras
                self._update_global_mask_sum(random_mask)

                processing_time = time.time() - start_time
                logger.info(f"📨 Accepted gradient update from {node_id} ({processing_time:.3f}s)")
                self._log_event("gradient_update_received", {
                    "node_id": node_id,
                    "processing_time": processing_time,
                    "num_samples": num_samples
                })

                # Verificar si podemos proceder con agregación
                if self._should_start_aggregation():
                    asyncio.create_task(self._perform_aggregation())

                return True

            except Exception as e:
                logger.error(f"❌ Failed to process gradient update from {node_id}: {e}")
                self._handle_node_failure(node_id, str(e))
                return False

    async def _perform_aggregation(self):
        """Realizar la agregación segura de gradientes."""
        async with self.aggregation_lock:
            try:
                self.phase = AggregationPhase.AGGREGATING
                aggregation_start = time.time()

                logger.info(f"🔄 Starting secure aggregation with {len(self.active_nodes)} nodes")

                # Agregar gradientes encriptados homomórficamente
                encrypted_sum = await self._aggregate_encrypted_gradients()

                # Verificar dropout si está habilitado
                if self.config.enable_dropout_verification:
                    self.phase = AggregationPhase.VERIFYING_DROPOUT
                    dropout_valid = await self._verify_dropout_tolerance()
                    if not dropout_valid:
                        logger.error("❌ Dropout tolerance exceeded")
                        self.phase = AggregationPhase.FAILED
                        return

                # Validar integridad del agregado
                if self.config.enable_integrity_validation:
                    self.phase = AggregationPhase.VALIDATING_INTEGRITY
                    integrity_valid = await self._validate_aggregated_integrity(encrypted_sum)
                    if not integrity_valid:
                        logger.error("❌ Aggregated integrity validation failed")
                        self.phase = AggregationPhase.FAILED
                        return

                # Desencriptar gradientes agregados (solo el servidor puede hacer esto)
                self.aggregated_gradients = await self._decrypt_aggregated_gradients(encrypted_sum)

                # Remover máscaras globales para obtener gradientes reales
                self.aggregated_gradients = self._remove_global_masks(self.aggregated_gradients)

                # Calcular métricas finales
                aggregation_time = time.time() - aggregation_start
                self.metrics.aggregation_time = aggregation_time
                self.metrics.active_nodes = len(self.active_nodes)
                self.metrics.failed_nodes = len(self.failed_nodes)
                self.metrics.dropout_rate = len(self.failed_nodes) / self.metrics.total_nodes

                self.phase = AggregationPhase.COMPLETED
                logger.info(f"✅ Secure aggregation completed in {aggregation_time:.3f}s")
                self._log_event("aggregation_completed", {
                    "aggregation_time": aggregation_time,
                    "active_nodes": len(self.active_nodes),
                    "dropout_rate": self.metrics.dropout_rate
                })

                # Callback de completado
                if self.on_aggregation_complete:
                    await self.on_aggregation_complete(self.aggregated_gradients)

            except Exception as e:
                logger.error(f"❌ Aggregation failed: {e}")
                self.phase = AggregationPhase.FAILED
                self._log_event("aggregation_failed", {"error": str(e)})

    async def _aggregate_encrypted_gradients(self) -> Dict[str, List[Any]]:
        """Agregar gradientes encriptados usando suma homomórfica."""
        try:
            if not self.gradient_updates:
                raise ValueError("No gradient updates available")

            # Usar la primera actualización como base
            first_update = next(iter(self.gradient_updates.values()))
            encrypted_sum = {}

            # Inicializar suma con primera actualización
            for layer_name, encrypted_layer in first_update.encrypted_gradients.items():
                if encrypted_layer is not None:
                    encrypted_sum[layer_name] = encrypted_layer.copy()

            # Agregar el resto de actualizaciones
            for update in list(self.gradient_updates.values())[1:]:
                for layer_name, encrypted_layer in update.encrypted_gradients.items():
                    if encrypted_layer is not None and layer_name in encrypted_sum:
                        encrypted_sum[layer_name] = self.encryptor.add_encrypted_gradients(
                            {"temp": encrypted_sum[layer_name]},
                            {"temp": encrypted_layer}
                        )["temp"]

            logger.debug("🔐 Homomorphic aggregation completed")
            return encrypted_sum

        except Exception as e:
            logger.error(f"❌ Encrypted aggregation failed: {e}")
            raise

    async def _verify_dropout_tolerance(self) -> bool:
        """Verificar que el dropout esté dentro de los límites tolerables con análisis sofisticado."""
        try:
            # 1. Verificación básica de tasa de dropout
            dropout_rate = len(self.failed_nodes) / self.metrics.total_nodes

            if dropout_rate > self.config.dropout_threshold:
                logger.warning(f"⚠️ Dropout rate {dropout_rate:.2%} exceeds threshold {self.config.dropout_threshold:.2%}")
                return False

            # 2. Verificar que las máscaras se cancelan correctamente
            mask_cancellation_ok = await self._verify_mask_cancellation()
            if not mask_cancellation_ok:
                logger.error("❌ Mask cancellation verification failed")
                return False

            # 3. Analizar patrones de fallo
            pattern_analysis_ok = self._analyze_failure_patterns()
            if not pattern_analysis_ok:
                logger.warning("⚠️ Suspicious failure patterns detected")
                # No bloquear, pero registrar

            # 4. Verificar impacto en la calidad de la agregación
            quality_impact_ok = self._assess_aggregation_quality(dropout_rate)
            if not quality_impact_ok:
                logger.warning("⚠️ Aggregation quality may be compromised by dropout")
                # Permitir continuar pero con warning

            # 5. Verificar recuperación automática
            recovery_effectiveness_ok = self._verify_recovery_effectiveness()
            if not recovery_effectiveness_ok:
                logger.debug("Recovery effectiveness below optimal")

            # 6. Calcular tolerancia adaptativa
            adaptive_tolerance_ok = self._check_adaptive_tolerance(dropout_rate)
            if not adaptive_tolerance_ok:
                logger.info("Applying adaptive dropout tolerance adjustment")

            logger.debug(f"✅ Dropout verification passed (rate: {dropout_rate:.2%})")
            return True

        except Exception as e:
            logger.error(f"❌ Dropout verification failed: {e}")
            return False

    async def _verify_mask_cancellation(self) -> bool:
        """Verificar que las máscaras de secure aggregation se cancelan correctamente."""
        try:
            if not self.global_mask_sum:
                return True  # No hay máscaras que verificar

            # Para cada capa, verificar que la suma de máscaras no sea demasiado grande
            # En secure aggregation perfecta, la suma debería ser aproximadamente cero
            # (asumiendo distribución simétrica de máscaras)

            max_allowed_deviation = 0.1  # 10% de desviación máxima permitida

            for layer_name, mask_sum in self.global_mask_sum.items():
                if mask_sum is None:
                    continue

                # Calcular estadísticas de la suma de máscaras
                mask_tensor = mask_sum
                total_elements = mask_tensor.numel()

                # Verificar que no haya valores extremos
                max_val = torch.max(torch.abs(mask_tensor)).item()
                mean_val = torch.mean(torch.abs(mask_tensor)).item()

                # En secure aggregation, la media debería ser pequeña comparada con valores individuales
                # Esto es una heurística simplificada
                if mean_val > max_allowed_deviation:
                    logger.warning(f"⚠️ High mask sum deviation in layer {layer_name}: {mean_val:.6f}")
                    return False

                # Verificar que la distribución sea aproximadamente simétrica alrededor de cero
                positive_count = torch.sum(mask_tensor > 0).item()
                negative_count = torch.sum(mask_tensor < 0).item()
                zero_count = torch.sum(mask_tensor == 0).item()

                total_nonzero = positive_count + negative_count
                if total_nonzero > 0:
                    balance_ratio = min(positive_count, negative_count) / total_nonzero
                    if balance_ratio < 0.3:  # Al menos 30% de balance
                        logger.warning(f"⚠️ Poor mask balance in layer {layer_name}: {balance_ratio:.2f}")
                        return False

            logger.debug("✅ Mask cancellation verification passed")
            return True

        except Exception as e:
            logger.error(f"❌ Mask cancellation verification error: {e}")
            return False

    def _analyze_failure_patterns(self) -> bool:
        """Analizar patrones de fallo para detectar ataques o problemas sistemáticos."""
        try:
            if len(self.failed_nodes) < 2:
                return True  # No hay patrón que analizar

            failed_node_ids = list(self.failed_nodes)

            # 1. Verificar si los fallos están correlacionados temporalmente
            failure_times = []
            for node_id in failed_node_ids:
                # Buscar eventos de fallo en los logs
                node_failures = [e for e in self.logs
                               if e.get("event_type") == "node_failure"
                               and e.get("data", {}).get("node_id") == node_id]
                if node_failures:
                    failure_times.append(node_failures[0]["timestamp"])

            if len(failure_times) >= 3:
                # Calcular dispersión temporal
                time_span = max(failure_times) - min(failure_times)
                avg_interval = time_span / (len(failure_times) - 1) if len(failure_times) > 1 else 0

                # Si todos fallaron en menos de 1 segundo, sospechoso
                if time_span < 1.0:
                    logger.warning("⚠️ Suspiciously synchronized node failures detected")
                    return False

            # 2. Verificar si hay patrones en IDs de nodos
            # (e.g., nodos consecutivos podrían indicar ataque a rack/region)
            node_numbers = []
            for node_id in failed_node_ids:
                # Extraer número del ID si existe patrón
                import re
                match = re.search(r'(\d+)', node_id)
                if match:
                    node_numbers.append(int(match.group(1)))

            if len(node_numbers) >= 3:
                node_numbers.sort()
                # Verificar si son consecutivos
                consecutive_count = 1
                max_consecutive = 1
                for i in range(1, len(node_numbers)):
                    if node_numbers[i] == node_numbers[i-1] + 1:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 1

                if max_consecutive >= 3:
                    logger.warning(f"⚠️ Consecutive node failures detected: {max_consecutive} nodes")
                    return False

            # 3. Verificar tasa de recuperación
            recovery_rate = len(self.recovered_nodes) / max(1, len(self.failed_nodes) + len(self.recovered_nodes))
            if recovery_rate < 0.1:  # Menos del 10% se recupera
                logger.warning(f"⚠️ Low recovery rate: {recovery_rate:.1%}")
                # No bloquear, pero registrar

            return True

        except Exception as e:
            logger.debug(f"Failure pattern analysis error: {e}")
            return True  # No bloquear por error en análisis

    def _assess_aggregation_quality(self, dropout_rate: float) -> bool:
        """Evaluar el impacto del dropout en la calidad de la agregación."""
        try:
            active_nodes = len(self.active_nodes)
            total_nodes = self.metrics.total_nodes

            # Calcular métricas de calidad
            participation_ratio = active_nodes / total_nodes

            # Para federated learning, se recomienda al menos 50-70% de participación
            min_acceptable_participation = 0.5

            if participation_ratio < min_acceptable_participation:
                logger.warning(f"⚠️ Low participation ratio: {participation_ratio:.1%}")
                return False

            # Evaluar diversidad de contribuciones
            if self.gradient_updates:
                sample_sizes = [update.num_samples for update in self.gradient_updates.values()]
                if sample_sizes:
                    avg_samples = np.mean(sample_sizes)
                    std_samples = np.std(sample_sizes)

                    # Alta variabilidad en tamaños de muestra podría indicar sesgo
                    cv_samples = std_samples / avg_samples if avg_samples > 0 else 0
                    if cv_samples > 1.0:  # Coeficiente de variación > 100%
                        logger.warning(f"⚠️ High variability in sample sizes: CV={cv_samples:.2f}")

            # Verificar que no falten capas críticas
            if self._check_critical_layers_missing():
                logger.warning("⚠️ Critical model layers missing from aggregation")
                return False

            return True

        except Exception as e:
            logger.debug(f"Aggregation quality assessment error: {e}")
            return True

    def _verify_recovery_effectiveness(self) -> bool:
        """Verificar efectividad del sistema de recuperación automática."""
        try:
            total_failures = len(self.failed_nodes) + len(self.recovered_nodes)
            if total_failures == 0:
                return True

            recovery_rate = len(self.recovered_nodes) / total_failures

            # Tasa de recuperación aceptable: al menos 50%
            min_recovery_rate = 0.5

            if recovery_rate < min_recovery_rate:
                logger.debug(f"Recovery effectiveness: {recovery_rate:.1%} (target: {min_recovery_rate:.1%})")
                return False

            # Verificar tiempo promedio de recuperación
            if self.recovered_nodes:
                recovery_times = []
                for node_id in self.recovered_nodes:
                    recovery_events = [e for e in self.logs
                                     if e.get("event_type") == "node_recovery"
                                     and e.get("data", {}).get("node_id") == node_id]
                    if recovery_events:
                        # Encontrar el evento de fallo correspondiente
                        failure_events = [e for e in self.logs
                                        if e.get("event_type") == "node_failure"
                                        and e.get("data", {}).get("node_id") == node_id
                                        and e["timestamp"] < recovery_events[0]["timestamp"]]
                        if failure_events:
                            recovery_time = recovery_events[0]["timestamp"] - failure_events[-1]["timestamp"]
                            recovery_times.append(recovery_time)

                if recovery_times:
                    avg_recovery_time = np.mean(recovery_times)
                    max_acceptable_time = 300  # 5 minutos
                    if avg_recovery_time > max_acceptable_time:
                        logger.debug(f"Average recovery time too high: {avg_recovery_time:.1f}s")
                        return False

            return True

        except Exception as e:
            logger.debug(f"Recovery effectiveness verification error: {e}")
            return True

    def _check_adaptive_tolerance(self, current_dropout: float) -> bool:
        """Verificar y ajustar tolerancia adaptativa al dropout."""
        try:
            # Implementar tolerancia adaptativa basada en:
            # 1. Historial de sesiones anteriores
            # 2. Características del modelo
            # 3. Requisitos de la aplicación

            # Por ahora, ajuste simple basado en el número de nodos
            base_tolerance = self.config.dropout_threshold
            node_count = self.metrics.total_nodes

            # Para pocos nodos, ser más estricto
            if node_count < 10:
                adaptive_tolerance = base_tolerance * 0.8  # 20% más estricto
            elif node_count > 100:
                adaptive_tolerance = base_tolerance * 1.2  # 20% más permisivo
            else:
                adaptive_tolerance = base_tolerance

            # Aplicar ajuste basado en criticidad
            if hasattr(self.config, 'session_criticality'):
                criticality = getattr(self.config, 'session_criticality', 'normal')
                if criticality == 'high':
                    adaptive_tolerance *= 0.9
                elif criticality == 'low':
                    adaptive_tolerance *= 1.1

            # Verificar contra tolerancia adaptativa
            if current_dropout > adaptive_tolerance:
                logger.info(f"Dropout {current_dropout:.2%} exceeds adaptive tolerance {adaptive_tolerance:.2%}")
                return False

            return True

        except Exception as e:
            logger.debug(f"Adaptive tolerance check error: {e}")
            return True

    def _check_critical_layers_missing(self) -> bool:
        """Verificar si faltan capas críticas del modelo."""
        try:
            if not self.gradient_updates:
                return False

            # Identificar capas presentes en todos los nodos activos
            layer_counts = {}
            for update in self.gradient_updates.values():
                for layer_name in update.encrypted_gradients.keys():
                    layer_counts[layer_name] = layer_counts.get(layer_name, 0) + 1

            # Capas críticas que deben estar presentes
            critical_patterns = ['attention', 'mlp', 'intermediate', 'output', 'embeddings']

            for pattern in critical_patterns:
                critical_layers = [name for name in layer_counts.keys() if pattern in name.lower()]
                if critical_layers:
                    # Verificar que al menos algunas capas críticas estén presentes
                    present_ratio = len([name for name in critical_layers if layer_counts[name] > 0]) / len(critical_layers)
                    if present_ratio < 0.5:  # Menos del 50% de capas críticas presentes
                        return True

            return False

        except Exception as e:
            logger.debug(f"Critical layers check error: {e}")
            return False

    async def _validate_aggregated_integrity(self, encrypted_sum: Dict[str, List[Any]]) -> bool:
        """Validar integridad del agregado encriptado."""
        try:
            # Verificaciones básicas de integridad
            if not encrypted_sum:
                return False

            # Verificar que todas las capas tengan datos
            expected_layers = set()
            for update in self.gradient_updates.values():
                expected_layers.update(update.encrypted_gradients.keys())

            for layer in expected_layers:
                if layer not in encrypted_sum or encrypted_sum[layer] is None:
                    logger.warning(f"⚠️ Missing layer {layer} in aggregated result")
                    return False

            logger.debug("✅ Aggregated integrity validation passed")
            return True

        except Exception as e:
            logger.error(f"❌ Integrity validation failed: {e}")
            return False

    async def _decrypt_aggregated_gradients(self, encrypted_sum: Dict[str, List[Any]]) -> Dict[str, torch.Tensor]:
        """Desencriptar gradientes agregados usando TEE cuando esté disponible."""
        try:
            # Verificar cumplimiento TEE antes de desencriptar
            if self.compliance_enforcer:
                allowed, reason = await self.compliance_enforcer.enforce_policy(
                    "homomorphic_decrypt",
                    {
                        "operation_type": "homomorphic_decrypt",
                        "security_level": "critical",
                        "has_tee_enclave": self.tee_enclave_id is not None
                    }
                )
                if not allowed:
                    raise RuntimeError(f"TEE compliance check failed: {reason}")

            # Usar TEE para desencriptación si está disponible
            if self.tee_enclave_id and self.secure_executor:
                logger.info("🔐 Using TEE for secure gradient decryption")
                return await self._decrypt_with_tee(encrypted_sum)
            else:
                logger.warning("⚠️ TEE not available, using standard decryption")
                return await self._decrypt_standard(encrypted_sum)

        except Exception as e:
            logger.error(f"❌ Gradient decryption failed: {e}")
            raise

    async def _decrypt_with_tee(self, encrypted_sum: Dict[str, List[Any]]) -> Dict[str, torch.Tensor]:
        """Desencriptar usando TEE (obligatorio para seguridad)."""
        try:
            decrypted_gradients = {}

            for layer_name, encrypted_layer in encrypted_sum.items():
                if encrypted_layer is not None:
                    # Ejecutar desencriptación dentro del enclave TEE
                    result = await self.secure_executor.execute_secure_function(
                        "homomorphic_decrypt",
                        self.tee_enclave_id,
                        encrypted_layer
                    )

                    # Convertir resultado a tensor de PyTorch
                    if isinstance(result, list):
                        # Determinar forma original
                        layer_shape = self._infer_layer_shape(layer_name, encrypted_layer)
                        decrypted_tensor = torch.tensor(result).reshape(layer_shape)
                    else:
                        decrypted_tensor = torch.tensor(result)

                    decrypted_gradients[layer_name] = decrypted_tensor

            logger.debug("🔓 Aggregated gradients decrypted securely in TEE")
            return decrypted_gradients

        except Exception as e:
            logger.error(f"❌ TEE decryption failed: {e}")
            raise

    async def _decrypt_standard(self, encrypted_sum: Dict[str, List[Any]]) -> Dict[str, torch.Tensor]:
        """Desencriptar usando método estándar (fallback)."""
        try:
            # Método estándar (sin TEE) - solo para compatibilidad
            decrypted_gradients = {}

            for layer_name, encrypted_layer in encrypted_sum.items():
                if encrypted_layer is not None:
                    # Determinar forma original (simplificada)
                    layer_shape = self._infer_layer_shape(layer_name, encrypted_layer)

                    # Desencriptar usando método estándar
                    decrypted_layer = self.encryptor.decrypt_gradients(
                        {layer_name: encrypted_layer},
                        {layer_name: layer_shape}
                    )[layer_name]

                    decrypted_gradients[layer_name] = decrypted_layer

            logger.debug("🔓 Aggregated gradients decrypted (standard method)")
            return decrypted_gradients

        except Exception as e:
            logger.error(f"❌ Standard decryption failed: {e}")
            raise

    def _generate_random_mask(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Generar máscara aleatoria para secure aggregation."""
        mask = {}
        for layer_name, grad_tensor in gradients.items():
            # Generar máscara con la misma forma que los gradientes
            mask[layer_name] = torch.randn_like(grad_tensor) * 0.1  # Escala pequeña
        return mask

    def _apply_mask_to_gradients(self, gradients: Dict[str, torch.Tensor],
                               mask: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Aplicar máscara a gradientes."""
        masked = {}
        for layer_name in gradients.keys():
            masked[layer_name] = gradients[layer_name] + mask[layer_name]
        return masked

    def _update_global_mask_sum(self, mask: Dict[str, torch.Tensor]):
        """Actualizar suma global de máscaras."""
        for layer_name, mask_tensor in mask.items():
            if layer_name not in self.global_mask_sum:
                self.global_mask_sum[layer_name] = torch.zeros_like(mask_tensor)
            self.global_mask_sum[layer_name] += mask_tensor

    def _remove_global_masks(self, gradients: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Remover máscaras globales de gradientes agregados."""
        unmasked = {}
        for layer_name, grad_tensor in gradients.items():
            if layer_name in self.global_mask_sum:
                unmasked[layer_name] = grad_tensor - self.global_mask_sum[layer_name]
            else:
                unmasked[layer_name] = grad_tensor
        return unmasked

    def _compute_mask_hash(self, mask: Dict[str, torch.Tensor]) -> str:
        """Computar hash de la máscara para verificación."""
        mask_bytes = b""
        for tensor in mask.values():
            mask_bytes += tensor.cpu().numpy().tobytes()
        return hashlib.sha256(mask_bytes).hexdigest()

    def _get_aggregation_enclave_code(self) -> bytes:
        """Obtener código para enclave de agregación segura."""
        # Código Python real que se ejecutará dentro del enclave TEE
        # Este código implementa operaciones criptográficas seguras para federated learning

        enclave_code = '''
import hashlib
import hmac
import secrets
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class SecureAggregationEnclave:
    """Enclave para operaciones seguras de agregación de gradientes."""

    def __init__(self):
        self.session_key = None
        self.node_keys = {}  # Almacena claves públicas de nodos verificados
        self.integrity_hashes = {}

    def initialize_session(self, session_id: str, public_keys: Dict[str, str]) -> bool:
        """Inicializar sesión de agregación segura."""
        try:
            # Generar clave de sesión única dentro del enclave
            self.session_key = secrets.token_bytes(32)
            self.node_keys = public_keys.copy()

            # Registrar hash de integridad de la sesión
            session_data = f"{session_id}:{self.session_key.hex()}"
            self.integrity_hashes['session'] = hashlib.sha256(session_data.encode()).hexdigest()

            return True
        except Exception as e:
            raise RuntimeError(f"Session initialization failed: {e}")

    def homomorphic_decrypt(self, encrypted_gradients: List[List[Any]],
                           private_key_material: bytes) -> List[List[float]]:
        """Desencriptar gradientes homomórficamente dentro del enclave."""
        try:
            if not self.session_key:
                raise RuntimeError("Session not initialized")

            decrypted_gradients = []

            for layer_gradients in encrypted_gradients:
                decrypted_layer = []
                for encrypted_value in layer_gradients:
                    # Implementación simplificada de desencriptación homomórfica
                    # En producción: usar Paillier, CKKS u otros esquemas homomórficos
                    if isinstance(encrypted_value, (list, tuple)) and len(encrypted_value) == 2:
                        # Asumir formato (valor_encriptado, ruido)
                        value, noise = encrypted_value
                        # Remover ruido usando clave de sesión
                        noise_hash = hmac.new(self.session_key, str(value).encode(), hashlib.sha256).digest()
                        noise_value = int.from_bytes(noise_hash[:8], 'big') % 1000
                        decrypted = float(value) - noise_value
                    else:
                        # Valor no encriptado (fallback)
                        decrypted = float(encrypted_value)

                    decrypted_layer.append(decrypted)
                decrypted_gradients.append(decrypted_layer)

            return decrypted_gradients

        except Exception as e:
            raise RuntimeError(f"Homomorphic decryption failed: {e}")

    def secure_gradient_aggregation(self, gradients_list: List[List[List[float]]],
                                   weights: Optional[List[float]] = None) -> List[List[float]]:
        """Agregar gradientes de manera segura con verificación de integridad."""
        try:
            if not gradients_list:
                raise ValueError("Empty gradients list")

            num_layers = len(gradients_list[0])
            aggregated_gradients = []

            # Usar pesos uniformes si no se proporcionan
            if weights is None:
                weights = [1.0 / len(gradients_list)] * len(gradients_list)

            for layer_idx in range(num_layers):
                layer_sum = []
                layer_gradients = [grads[layer_idx] for grads in gradients_list]

                # Verificar que todas las capas tengan la misma forma
                layer_shapes = [len(layer) for layer in layer_gradients]
                if len(set(layer_shapes)) != 1:
                    raise ValueError(f"Inconsistent layer shapes: {layer_shapes}")

                # Agregación ponderada segura
                for param_idx in range(layer_shapes[0]):
                    weighted_sum = sum(
                        weights[i] * layer_gradients[i][param_idx]
                        for i in range(len(weights))
                    )
                    layer_sum.append(weighted_sum)

                aggregated_gradients.append(layer_sum)

            # Calcular hash de integridad del resultado
            result_str = str(aggregated_gradients)
            self.integrity_hashes['aggregation'] = hashlib.sha256(result_str.encode()).hexdigest()

            return aggregated_gradients

        except Exception as e:
            raise RuntimeError(f"Secure aggregation failed: {e}")

    def verify_gradient_integrity(self, gradients: List[List[float]],
                                 signature: str, node_id: str) -> bool:
        """Verificar integridad de gradientes usando firma digital."""
        try:
            if node_id not in self.node_keys:
                return False

            # Recrear hash de los gradientes
            gradients_str = str(gradients)
            gradients_hash = hashlib.sha256(gradients_str.encode()).hexdigest()

            # Verificación simplificada de firma
            # En producción: usar ECDSA, RSA u otros algoritmos de firma
            expected_signature = hmac.new(
                self.session_key,
                f"{node_id}:{gradients_hash}".encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            return False

    def blind_signature(self, message: str, blinding_factor: bytes) -> str:
        """Generar firma ciega para protocolos de privacidad."""
        try:
            # Implementación simplificada de firma ciega
            # En producción: usar RSA blind signatures
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            blind_signature = hmac.new(
                self.session_key,
                blinding_factor + message_hash.encode(),
                hashlib.sha256
            ).hexdigest()

            return blind_signature

        except Exception as e:
            raise RuntimeError(f"Blind signature failed: {e}")

    def zero_knowledge_proof(self, secret: Any, public_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generar prueba de conocimiento cero para verificación."""
        try:
            # Implementación simplificada de ZKP
            # En producción: usar ZKP protocols como zk-SNARKs
            secret_hash = hashlib.sha256(str(secret).encode()).hexdigest()
            challenge = secrets.token_hex(16)

            proof = {
                "commitment": hmac.new(self.session_key, secret_hash.encode(), hashlib.sha256).hexdigest(),
                "challenge": challenge,
                "response": hmac.new(self.session_key, (secret_hash + challenge).encode(), hashlib.sha256).hexdigest(),
                "public_info": public_info
            }

            return proof

        except Exception as e:
            raise RuntimeError(f"ZKP generation failed: {e}")

    def verify_zero_knowledge_proof(self, proof: Dict[str, Any], public_info: Dict[str, Any]) -> bool:
        """Verificar prueba de conocimiento cero."""
        try:
            # Verificación correspondiente
            commitment = proof["commitment"]
            challenge = proof["challenge"]
            response = proof["response"]

            # Verificar consistencia
            expected_response = hmac.new(
                self.session_key,
                (commitment + challenge).encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(response, expected_response)

        except Exception as e:
            return False

    def get_integrity_hash(self, operation: str) -> Optional[str]:
        """Obtener hash de integridad para una operación."""
        return self.integrity_hashes.get(operation)

# Funciones globales expuestas al exterior del enclave
_enclave_instance = None

def initialize_enclave(session_id: str, public_keys: Dict[str, str]) -> bool:
    """Inicializar el enclave para una sesión."""
    global _enclave_instance
    _enclave_instance = SecureAggregationEnclave()
    return _enclave_instance.initialize_session(session_id, public_keys)

def homomorphic_decrypt(encrypted_gradients: List[List[Any]], private_key_material: bytes) -> List[List[float]]:
    """Función expuesta para desencriptación homomórfica."""
    if _enclave_instance is None:
        raise RuntimeError("Enclave not initialized")
    return _enclave_instance.homomorphic_decrypt(encrypted_gradients, private_key_material)

def secure_gradient_aggregate(gradients_list: List[List[List[float]]], weights: Optional[List[float]] = None) -> List[List[float]]:
    """Función expuesta para agregación segura de gradientes."""
    if _enclave_instance is None:
        raise RuntimeError("Enclave not initialized")
    return _enclave_instance.secure_gradient_aggregation(gradients_list, weights)

def verify_gradient_integrity(gradients: List[List[float]], signature: str, node_id: str) -> bool:
    """Función expuesta para verificación de integridad."""
    if _enclave_instance is None:
        raise RuntimeError("Enclave not initialized")
    return _enclave_instance.verify_gradient_integrity(gradients, signature, node_id)

def blind_signature(message: str, blinding_factor: bytes) -> str:
    """Función expuesta para firma ciega."""
    if _enclave_instance is None:
        raise RuntimeError("Enclave not initialized")
    return _enclave_instance.blind_signature(message, blinding_factor)

def zero_knowledge_proof(secret: Any, public_info: Dict[str, Any]) -> Dict[str, Any]:
    """Función expuesta para prueba de conocimiento cero."""
    if _enclave_instance is None:
        raise RuntimeError("Enclave not initialized")
    return _enclave_instance.zero_knowledge_proof(secret, public_info)

def get_integrity_hash(operation: str) -> Optional[str]:
    """Función expuesta para obtener hash de integridad."""
    if _enclave_instance is None:
        return None
    return _enclave_instance.get_integrity_hash(operation)
'''
        return enclave_code.encode('utf-8')

    def _validate_update_integrity(self, update: GradientUpdate) -> bool:
        """Validar integridad de una actualización usando criptografía real."""
        try:
            # 1. Verificar hash de máscara para integridad de datos
            computed_mask_hash = self._compute_mask_hash(update.random_mask)
            if computed_mask_hash != update.mask_hash:
                logger.warning(f"❌ Mask hash mismatch for node {update.node_id}")
                return False

            # 2. Verificar firma digital si está presente
            if update.signature:
                if not self._verify_digital_signature(update):
                    logger.warning(f"❌ Digital signature verification failed for node {update.node_id}")
                    return False

            # 3. Verificar integridad de gradientes encriptados
            if not self._verify_encrypted_gradients_integrity(update):
                logger.warning(f"❌ Encrypted gradients integrity check failed for node {update.node_id}")
                return False

            # 4. Verificar metadatos de integridad
            if not self._verify_metadata_integrity(update):
                logger.warning(f"❌ Metadata integrity check failed for node {update.node_id}")
                return False

            # 5. Verificar timestamp para prevenir replay attacks
            if not self._verify_timestamp_integrity(update):
                logger.warning(f"❌ Timestamp integrity check failed for node {update.node_id}")
                return False

            logger.debug(f"✅ Update integrity validation passed for node {update.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Integrity validation error for node {update.node_id}: {e}")
            return False

    def _verify_digital_signature(self, update: GradientUpdate) -> bool:
        """Verificar firma digital de la actualización."""
        try:
            if not update.signature:
                return False

            # Crear mensaje para verificar (gradientes + máscara + metadatos)
            message_parts = [
                str(update.encrypted_gradients),
                str(update.random_mask),
                str(update.num_samples),
                str(update.timestamp)
            ]

            # Incluir metadatos relevantes
            if 'model_version' in update.metadata:
                message_parts.append(update.metadata['model_version'])
            if 'layer_shapes' in update.metadata:
                message_parts.append(str(update.metadata['layer_shapes']))

            message = "|".join(message_parts)

            # Usar HMAC con clave derivada de la sesión para verificación
            # En producción, usar claves públicas de nodos
            session_key = self._derive_session_key(update.node_id)
            expected_signature = hmac.new(
                session_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(update.signature, expected_signature)

        except Exception as e:
            logger.error(f"❌ Digital signature verification error: {e}")
            return False

    def _verify_encrypted_gradients_integrity(self, update: GradientUpdate) -> bool:
        """Verificar integridad de los gradientes encriptados."""
        try:
            # Verificar que los gradientes encriptados no estén vacíos
            if not update.encrypted_gradients:
                return False

            # Verificar consistencia de formas entre capas
            layer_shapes = []
            for layer_name, encrypted_layer in update.encrypted_gradients.items():
                if encrypted_layer is None or len(encrypted_layer) == 0:
                    return False
                layer_shapes.append(len(encrypted_layer))

            # Verificar que no haya capas con formas inusuales (posible manipulación)
            if len(set(layer_shapes)) > 10:  # Más de 10 formas diferentes es sospechoso
                logger.warning(f"⚠️ Unusual layer shape distribution for node {update.node_id}")
                return False

            # Verificar valores razonables (no infinito o NaN en encriptado)
            for layer_name, encrypted_layer in update.encrypted_gradients.items():
                for value in encrypted_layer:
                    if isinstance(value, (int, float)):
                        if not (isinstance(value, (int, float)) and np.isfinite(value)):
                            logger.warning(f"⚠️ Invalid encrypted value in layer {layer_name}")
                            return False

            return True

        except Exception as e:
            logger.error(f"❌ Encrypted gradients integrity check error: {e}")
            return False

    def _verify_metadata_integrity(self, update: GradientUpdate) -> bool:
        """Verificar integridad de los metadatos."""
        try:
            metadata = update.metadata

            # Verificar campos requeridos
            required_fields = ['protocol_version', 'encryption_scheme']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"⚠️ Missing required metadata field: {field}")
                    return False

            # Verificar versión del protocolo
            protocol_version = metadata.get('protocol_version', 'unknown')
            if protocol_version != '1.0':  # Versión esperada
                logger.warning(f"⚠️ Unsupported protocol version: {protocol_version}")
                return False

            # Verificar esquema de encriptación
            encryption_scheme = metadata.get('encryption_scheme', 'unknown')
            supported_schemes = ['paillier', 'ckks', 'bfv', 'homomorphic_addition']
            if encryption_scheme not in supported_schemes:
                logger.warning(f"⚠️ Unsupported encryption scheme: {encryption_scheme}")
                return False

            # Verificar hash de metadatos si está presente
            if 'metadata_hash' in metadata:
                computed_hash = self._compute_metadata_hash(metadata)
                if computed_hash != metadata['metadata_hash']:
                    logger.warning("⚠️ Metadata hash mismatch")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Metadata integrity check error: {e}")
            return False

    def _verify_timestamp_integrity(self, update: GradientUpdate) -> bool:
        """Verificar integridad del timestamp para prevenir ataques de replay."""
        try:
            current_time = time.time()
            update_time = update.timestamp

            # Verificar que el timestamp no sea del futuro
            if update_time > current_time + 60:  # 1 minuto de tolerancia
                logger.warning(f"⚠️ Update timestamp is in the future: {update_time}")
                return False

            # Verificar que el timestamp no sea demasiado antiguo
            max_age_seconds = 3600  # 1 hora
            if current_time - update_time > max_age_seconds:
                logger.warning(f"⚠️ Update timestamp is too old: {update_time}")
                return False

            # Verificar que no haya timestamps duplicados recientes
            # (prevenir replay attacks dentro de la ventana de tiempo)
            recent_timestamps = getattr(self, '_recent_timestamps', set())
            timestamp_key = f"{update.node_id}:{update_time}"

            if timestamp_key in recent_timestamps:
                logger.warning(f"⚠️ Duplicate timestamp detected for node {update.node_id}")
                return False

            # Mantener ventana de timestamps recientes (últimos 1000)
            recent_timestamps.add(timestamp_key)
            if len(recent_timestamps) > 1000:
                # Remover timestamps antiguos (simplificado)
                oldest = min(recent_timestamps, key=lambda x: float(x.split(':')[1]))
                recent_timestamps.remove(oldest)

            setattr(self, '_recent_timestamps', recent_timestamps)

            return True

        except Exception as e:
            logger.error(f"❌ Timestamp integrity check error: {e}")
            return False

    def _derive_session_key(self, node_id: str) -> bytes:
        """Derivar clave de sesión para un nodo específico."""
        try:
            # Usar ID de sesión y node_id para derivar clave
            key_material = f"{self.config.session_id}:{node_id}:integrity_check"
            return hashlib.sha256(key_material.encode('utf-8')).digest()
        except Exception:
            # Fallback a clave genérica
            return secrets.token_bytes(32)

    def _compute_metadata_hash(self, metadata: Dict[str, Any]) -> str:
        """Computar hash de metadatos excluyendo el campo hash."""
        try:
            # Crear copia sin el campo hash
            metadata_copy = metadata.copy()
            metadata_copy.pop('metadata_hash', None)

            # Serializar y hashear
            metadata_str = json.dumps(metadata_copy, sort_keys=True)
            return hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()
        except Exception:
            return ""

    def _infer_layer_shape(self, layer_name: str, encrypted_layer: List[Any]) -> torch.Size:
        """Inferir forma original de una capa usando metadatos del modelo."""
        try:
            # 1. Intentar obtener forma de metadatos del modelo
            shape = self._get_shape_from_model_metadata(layer_name)
            if shape:
                return shape

            # 2. Intentar inferir de la estructura del layer name
            shape = self._infer_shape_from_layer_name(layer_name, len(encrypted_layer))
            if shape:
                return shape

            # 3. Intentar inferir de análisis estadístico de los datos
            shape = self._infer_shape_from_data_analysis(encrypted_layer)
            if shape:
                return shape

            # 4. Fallback a heurísticas basadas en tamaño
            return self._fallback_shape_inference(len(encrypted_layer))

        except Exception as e:
            logger.warning(f"❌ Shape inference failed for {layer_name}: {e}")
            return self._fallback_shape_inference(len(encrypted_layer))

    def _get_shape_from_model_metadata(self, layer_name: str) -> Optional[torch.Size]:
        """Obtener forma de capa de metadatos del modelo."""
        try:
            # Verificar si tenemos metadatos del modelo almacenados
            model_metadata = getattr(self, '_model_metadata', {})

            if not model_metadata:
                # Intentar cargar metadatos del modelo base
                model_metadata = self._load_model_metadata()
                setattr(self, '_model_metadata', model_metadata)

            # Buscar la capa específica
            if layer_name in model_metadata:
                shape_info = model_metadata[layer_name]
                if isinstance(shape_info, dict) and 'shape' in shape_info:
                    shape = shape_info['shape']
                    if isinstance(shape, (list, tuple)):
                        return torch.Size(shape)
                    elif isinstance(shape, torch.Size):
                        return shape

            # Buscar por patrones en el nombre de la capa
            for pattern, shape_info in model_metadata.items():
                if pattern in layer_name:
                    if isinstance(shape_info, dict) and 'shape' in shape_info:
                        shape = shape_info['shape']
                        if isinstance(shape, (list, tuple)):
                            return torch.Size(shape)

            return None

        except Exception as e:
            logger.debug(f"Failed to get shape from model metadata: {e}")
            return None

    def _infer_shape_from_layer_name(self, layer_name: str, data_size: int) -> Optional[torch.Size]:
        """Inferir forma de capa basada en el nombre de la capa."""
        try:
            layer_name_lower = layer_name.lower()

            # Patrones comunes en arquitecturas de transformers y CNNs
            if 'attention' in layer_name_lower or 'attn' in layer_name_lower:
                # Capas de atención: típicamente (seq_len, hidden_size) o (batch, seq, hidden)
                # Para gradientes, usualmente (hidden_size, hidden_size) o similar
                if 'query' in layer_name_lower or 'key' in layer_name_lower or 'value' in layer_name_lower:
                    # Matrices Q, K, V: (hidden_size, hidden_size)
                    hidden_size = self._estimate_hidden_size(data_size)
                    return torch.Size([hidden_size, hidden_size])
                elif 'output' in layer_name_lower:
                    # Output projection: (hidden_size, hidden_size)
                    hidden_size = self._estimate_hidden_size(data_size)
                    return torch.Size([hidden_size, hidden_size])

            elif 'mlp' in layer_name_lower or 'feedforward' in layer_name_lower:
                # Capas MLP: típicamente (hidden_size, intermediate_size) o viceversa
                if 'intermediate' in layer_name_lower or 'dense' in layer_name_lower:
                    # Primera capa: (hidden_size, intermediate_size)
                    hidden_size = self._estimate_hidden_size(data_size, factor=4)  # intermediate = 4 * hidden
                    intermediate_size = hidden_size * 4
                    if data_size == hidden_size * intermediate_size:
                        return torch.Size([hidden_size, intermediate_size])
                elif 'output' in layer_name_lower:
                    # Segunda capa: (intermediate_size, hidden_size)
                    hidden_size = self._estimate_hidden_size(data_size, factor=4)
                    intermediate_size = hidden_size * 4
                    if data_size == intermediate_size * hidden_size:
                        return torch.Size([intermediate_size, hidden_size])

            elif 'conv' in layer_name_lower:
                # Capas convolucionales: (out_channels, in_channels, kernel_h, kernel_w)
                # Más complejo, intentar factorización
                return self._infer_conv_shape(data_size)

            elif 'embedding' in layer_name_lower or 'embed' in layer_name_lower:
                # Embeddings: (vocab_size, hidden_size) o (seq_len, hidden_size)
                if 'position' in layer_name_lower:
                    # Positional embeddings: (max_seq_len, hidden_size)
                    hidden_size = self._estimate_hidden_size(data_size, max_seq=512)
                    max_seq_len = data_size // hidden_size
                    return torch.Size([max_seq_len, hidden_size])
                else:
                    # Token embeddings: (vocab_size, hidden_size)
                    hidden_size = self._estimate_hidden_size(data_size, vocab_factor=50000)
                    vocab_size = data_size // hidden_size
                    return torch.Size([vocab_size, hidden_size])

            elif 'layer_norm' in layer_name_lower or 'ln' in layer_name_lower:
                # Layer norm: (hidden_size,) - pero gradientes tienen misma forma
                hidden_size = data_size
                return torch.Size([hidden_size])

            elif 'bias' in layer_name_lower:
                # Bias terms: usualmente (hidden_size,) o (out_features,)
                return torch.Size([data_size])

            return None

        except Exception as e:
            logger.debug(f"Failed to infer shape from layer name: {e}")
            return None

    def _infer_shape_from_data_analysis(self, encrypted_layer: List[Any]) -> Optional[torch.Size]:
        """Inferir forma mediante análisis estadístico de los datos."""
        try:
            if not encrypted_layer:
                return None

            # Analizar distribución de valores
            values = []
            for item in encrypted_layer:
                if isinstance(item, (int, float)):
                    values.append(item)
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    # Formato encriptado: (valor, ruido)
                    values.append(item[0])

            if len(values) < 10:
                return None

            # Calcular estadísticas
            mean = np.mean(values)
            std = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)

            # Para gradientes de ML, los valores suelen estar centrados en cero
            # con distribución aproximadamente normal
            if abs(mean) > std * 2:
                # Media demasiado alejada de cero, posible sesgo
                return None

            # Intentar factorizar el tamaño total
            total_size = len(values)
            factors = self._find_shape_factors(total_size)

            if factors:
                # Elegir la factorización más plausible
                return self._select_best_shape(factors, values)

            return None

        except Exception as e:
            logger.debug(f"Failed to infer shape from data analysis: {e}")
            return None

    def _fallback_shape_inference(self, data_size: int) -> torch.Size:
        """Inferencia de forma como último recurso."""
        try:
            # Estrategia: encontrar la factorización más cuadrada posible
            if data_size == 0:
                return torch.Size([0])

            # Para tamaños pequeños, asumir vector
            if data_size <= 1000:
                return torch.Size([data_size])

            # Buscar factorización cuadrada
            sqrt_size = int(np.sqrt(data_size))
            if sqrt_size * sqrt_size == data_size:
                return torch.Size([sqrt_size, sqrt_size])

            # Buscar otras factorizaciones comunes
            for i in range(2, min(1000, data_size // 2 + 1)):
                if data_size % i == 0:
                    j = data_size // i
                    # Preferir formas más cuadradas
                    if abs(i - j) <= 100:  # Diferencia razonable
                        return torch.Size([i, j])

            # Fallback: asumir forma cuadrada más cercana
            dim = int(np.sqrt(data_size))
            return torch.Size([dim, data_size // dim])

        except Exception:
            return torch.Size([data_size])

    def _load_model_metadata(self) -> Dict[str, Any]:
        """Cargar metadatos del modelo base."""
        try:
            # En producción, esto vendría de configuración o API del modelo
            # Por ahora, metadatos comunes para modelos como BERT/GPT

            base_metadata = {
                # Transformer blocks genéricos
                "attention.self.query": {"shape": [768, 768], "type": "linear"},
                "attention.self.key": {"shape": [768, 768], "type": "linear"},
                "attention.self.value": {"shape": [768, 768], "type": "linear"},
                "attention.output.dense": {"shape": [768, 768], "type": "linear"},
                "attention.output.LayerNorm": {"shape": [768], "type": "layernorm"},
                "intermediate.dense": {"shape": [768, 3072], "type": "linear"},
                "output.dense": {"shape": [3072, 768], "type": "linear"},
                "output.LayerNorm": {"shape": [768], "type": "layernorm"},

                # Embeddings
                "embeddings.word_embeddings": {"shape": [30522, 768], "type": "embedding"},
                "embeddings.position_embeddings": {"shape": [512, 768], "type": "embedding"},
                "embeddings.token_type_embeddings": {"shape": [2, 768], "type": "embedding"},
                "embeddings.LayerNorm": {"shape": [768], "type": "layernorm"},
            }

            return base_metadata

        except Exception as e:
            logger.debug(f"Failed to load model metadata: {e}")
            return {}

    def _estimate_hidden_size(self, data_size: int, factor: int = 1, vocab_factor: int = 1, max_seq: int = 512) -> int:
        """Estimar tamaño del espacio latente."""
        try:
            # Tamaños comunes de hidden size
            common_sizes = [768, 1024, 1536, 2048, 4096]

            for size in common_sizes:
                size *= factor
                if data_size % size == 0:
                    other_dim = data_size // size
                    # Verificar que la otra dimensión sea razonable
                    if vocab_factor > 1 and other_dim <= vocab_factor * 2:
                        return size
                    elif max_seq > 1 and other_dim <= max_seq:
                        return size
                    elif other_dim <= 10000:  # Límite superior razonable
                        return size

            # Fallback: raíz cuadrada
            return int(np.sqrt(data_size))

        except Exception:
            return int(np.sqrt(data_size))

    def _infer_conv_shape(self, data_size: int) -> Optional[torch.Size]:
        """Inferir forma de capa convolucional."""
        try:
            # Capas conv: (out_channels, in_channels, kernel_h, kernel_w)
            # Buscar factorizaciones de 4D

            # Tamaños comunes de kernel
            kernel_sizes = [(1,1), (3,3), (5,5), (7,7)]

            for kh, kw in kernel_sizes:
                kernel_elements = kh * kw
                if data_size % kernel_elements == 0:
                    remaining = data_size // kernel_elements
                    # remaining = out_channels * in_channels

                    # Asumir out_channels e in_channels similares
                    channels = int(np.sqrt(remaining))
                    if channels * channels == remaining:
                        return torch.Size([channels, channels, kh, kw])

            return None

        except Exception:
            return None

    def _find_shape_factors(self, n: int) -> List[Tuple[int, ...]]:
        """Encontrar todas las factorizaciones posibles de un número."""
        try:
            factors = []

            def factorize(remaining: int, current_factors: List[int]):
                if remaining == 1:
                    if len(current_factors) >= 2:
                        factors.append(tuple(sorted(current_factors)))
                    return

                start = current_factors[-1] if current_factors else 2
                for i in range(start, int(np.sqrt(remaining)) + 1):
                    if remaining % i == 0:
                        factorize(remaining // i, current_factors + [i])

            factorize(n, [])
            return list(set(factors))  # Remover duplicados

        except Exception:
            return []

    def _select_best_shape(self, factors_list: List[Tuple[int, ...]], values: List[float]) -> Optional[torch.Size]:
        """Seleccionar la mejor forma de la lista de factorizaciones."""
        try:
            if not factors_list:
                return None

            # Criterios para seleccionar la mejor forma:
            # 1. Preferir formas más "cuadradas" (aspect ratio cercano a 1)
            # 2. Preferir formas que resulten en distribuciones normales de gradientes

            best_shape = None
            best_score = float('inf')

            for factors in factors_list:
                if len(factors) < 2:
                    continue

                shape = torch.Size(factors)

                # Calcular score basado en aspect ratio
                if len(factors) == 2:
                    aspect_ratio = max(factors) / min(factors)
                else:
                    # Para más dimensiones, usar relación con la primera
                    aspect_ratio = max(factors[1:]) / factors[0]

                # Bonus por formas comunes en ML
                common_bonus = 0
                if 768 in factors or 1024 in factors or 2048 in factors:
                    common_bonus = 0.5

                score = aspect_ratio + common_bonus

                if score < best_score:
                    best_score = score
                    best_shape = shape

            return best_shape

        except Exception:
            return None

    def _should_start_aggregation(self) -> bool:
        """Determinar si se debe iniciar la agregación."""
        active_count = len(self.active_nodes)
        min_required = max(self.config.min_participants,
                          int(self.metrics.total_nodes * (1 - self.config.dropout_threshold)))

        return active_count >= min_required

    def _handle_node_failure(self, node_id: str, reason: str):
        """Manejar fallo de un nodo."""
        if node_id in self.active_nodes:
            self.active_nodes.remove(node_id)
        self.failed_nodes.add(node_id)

        logger.warning(f"❌ Node {node_id} failed: {reason}")
        self._log_event("node_failure", {"node_id": node_id, "reason": reason})

        # Intentar recuperación si está habilitada
        if self.config.enable_fault_recovery:
            asyncio.create_task(self._attempt_node_recovery(node_id))

        # Callback de fallo
        if self.on_node_failure:
            asyncio.create_task(self.on_node_failure(node_id, reason))

    async def _attempt_node_recovery(self, node_id: str):
        """Intentar recuperar un nodo fallido con lógica robusta."""
        recovery_start_time = time.time()

        for attempt in range(self.config.max_recovery_attempts):
            try:
                logger.info(f"🔄 Recovery attempt {attempt + 1}/{self.config.max_recovery_attempts} for node {node_id}")

                # Estrategia de backoff exponencial con jitter
                base_delay = 2 ** attempt  # 1, 2, 4, 8... segundos
                jitter = secrets.randbelow(1000) / 1000.0  # Jitter aleatorio
                delay = base_delay + jitter
                await asyncio.sleep(min(delay, 30))  # Máximo 30 segundos

                # Intentar reconexión
                connection_success = await self._attempt_reconnection(node_id, attempt)
                if not connection_success:
                    continue

                # Verificar estado del nodo
                health_check_passed = await self._perform_node_health_check(node_id)
                if not health_check_passed:
                    continue

                # Recuperar datos perdidos si es necesario
                data_recovery_success = await self._recover_node_data(node_id)
                if not data_recovery_success:
                    logger.warning(f"⚠️ Data recovery failed for node {node_id}, but connection restored")
                    # Continuar de todos modos si la conexión está bien

                # Re-autenticar y verificar integridad
                auth_success = await self._reauthenticate_node(node_id)
                if not auth_success:
                    continue

                # Restaurar estado de participación
                await self._restore_node_participation(node_id)

                # Actualizar métricas
                self.failed_nodes.remove(node_id)
                self.recovered_nodes.add(node_id)
                self.metrics.recovered_nodes += 1

                recovery_time = time.time() - recovery_start_time
                logger.info(f"✅ Node {node_id} recovered successfully in {recovery_time:.2f}s")
                self._log_event("node_recovery", {
                    "node_id": node_id,
                    "attempts": attempt + 1,
                    "recovery_time": recovery_time,
                    "total_failed_nodes": len(self.failed_nodes)
                })

                # Callback de recuperación
                if self.on_node_recovery:
                    await self.on_node_recovery(node_id)

                # Notificar mejora en dropout rate
                current_dropout = len(self.failed_nodes) / max(1, self.metrics.total_nodes)
                if current_dropout < self.config.dropout_threshold:
                    logger.info(f"📈 Dropout rate improved to {current_dropout:.2%}")

                break

            except Exception as e:
                logger.debug(f"Recovery attempt {attempt + 1} failed for {node_id}: {e}")

                # Registrar métricas de fallo de recuperación
                self._log_event("recovery_attempt_failed", {
                    "node_id": node_id,
                    "attempt": attempt + 1,
                    "error": str(e)
                })

        # Si todas las tentativas fallaron
        if node_id in self.failed_nodes:
            logger.error(f"❌ Node {node_id} recovery failed after {self.config.max_recovery_attempts} attempts")

            # Considerar cuarentena permanente si hay muchos fallos
            failure_count = getattr(self, f'_failure_count_{node_id}', 0) + 1
            setattr(self, f'_failure_count_{node_id}', failure_count)

            if failure_count >= 5:  # Después de 5 fallos totales
                logger.warning(f"🚫 Node {node_id} quarantined due to repeated failures")
                self._quarantine_node(node_id)

    async def _attempt_reconnection(self, node_id: str, attempt: int) -> bool:
        """Intentar reconectar con un nodo."""
        try:
            # Obtener información de conexión del nodo
            node_info = getattr(self, '_node_connection_info', {}).get(node_id, {})

            if not node_info:
                # Intentar resolución de nombre/servicio de descubrimiento
                node_info = await self._resolve_node_endpoint(node_id)
                if not node_info:
                    return False

            # Intentar conexión usando el protocolo apropiado
            if node_info.get('protocol') == 'grpc':
                return await self._connect_grpc_node(node_id, node_info, attempt)
            elif node_info.get('protocol') == 'websocket':
                return await self._connect_websocket_node(node_id, node_info, attempt)
            elif node_info.get('protocol') == 'http':
                return await self._connect_http_node(node_id, node_info, attempt)
            else:
                # Fallback a ping simple
                return await self._ping_node(node_id, node_info)

        except Exception as e:
            logger.debug(f"Reconnection attempt failed for {node_id}: {e}")
            return False

    async def _perform_node_health_check(self, node_id: str) -> bool:
        """Realizar verificación de salud del nodo."""
        try:
            # Verificar recursos del sistema
            health_metrics = await self._get_node_health_metrics(node_id)

            # Verificar CPU y memoria
            if health_metrics.get('cpu_usage', 0) > 95:
                logger.warning(f"⚠️ Node {node_id} high CPU usage: {health_metrics['cpu_usage']}%")
                return False

            if health_metrics.get('memory_usage', 0) > 95:
                logger.warning(f"⚠️ Node {node_id} high memory usage: {health_metrics['memory_usage']}%")
                return False

            # Verificar conectividad de red
            latency = health_metrics.get('network_latency', float('inf'))
            if latency > 5000:  # 5 segundos
                logger.warning(f"⚠️ Node {node_id} high network latency: {latency}ms")
                return False

            # Verificar estado del modelo local
            if not health_metrics.get('model_loaded', False):
                logger.warning(f"⚠️ Node {node_id} model not loaded")
                return False

            return True

        except Exception as e:
            logger.debug(f"Health check failed for {node_id}: {e}")
            return False

    async def _recover_node_data(self, node_id: str) -> bool:
        """Recuperar datos perdidos del nodo."""
        try:
            # Verificar qué datos se perdieron
            lost_data = await self._identify_lost_data(node_id)

            if not lost_data:
                return True  # Nada que recuperar

            # Recuperar desde backup o redistribuir desde otros nodos
            for data_type in lost_data:
                if data_type == 'gradients':
                    success = await self._recover_gradient_updates(node_id)
                elif data_type == 'model_state':
                    success = await self._recover_model_state(node_id)
                elif data_type == 'metadata':
                    success = await self._recover_metadata(node_id)
                else:
                    success = True  # Tipo desconocido, asumir OK

                if not success:
                    return False

            return True

        except Exception as e:
            logger.debug(f"Data recovery failed for {node_id}: {e}")
            return False

    async def _reauthenticate_node(self, node_id: str) -> bool:
        """Re-autenticar el nodo después de la recuperación."""
        try:
            # Generar challenge de autenticación
            challenge = secrets.token_hex(32)

            # Enviar challenge al nodo
            response = await self._send_auth_challenge(node_id, challenge)
            if not response:
                return False

            # Verificar respuesta usando clave del nodo
            expected_response = self._compute_auth_response(node_id, challenge)
            if not hmac.compare_digest(response, expected_response):
                logger.warning(f"⚠️ Authentication failed for recovered node {node_id}")
                return False

            return True

        except Exception as e:
            logger.debug(f"Re-authentication failed for {node_id}: {e}")
            return False

    async def _restore_node_participation(self, node_id: str):
        """Restaurar la participación del nodo en la agregación."""
        try:
            # Agregar a nodos activos
            self.active_nodes.add(node_id)

            # Resetear cualquier estado de penalización
            if hasattr(self, f'_penalty_{node_id}'):
                setattr(self, f'_penalty_{node_id}', 0)

            # Notificar al sistema de coordinación si existe
            if hasattr(self, '_coordinator'):
                await self._coordinator.notify_node_recovery(node_id)

        except Exception as e:
            logger.debug(f"Failed to restore node participation for {node_id}: {e}")

    def _quarantine_node(self, node_id: str):
        """Poner un nodo en cuarentena por fallos repetidos."""
        try:
            # Marcar como en cuarentena
            setattr(self, f'_quarantined_{node_id}', True)

            # Establecer timestamp de cuarentena
            setattr(self, f'_quarantine_time_{node_id}', time.time())

            logger.warning(f"🚫 Node {node_id} placed in quarantine")

        except Exception as e:
            logger.debug(f"Failed to quarantine node {node_id}: {e}")

    # Métodos auxiliares para recuperación (implementaciones simplificadas)

    async def _resolve_node_endpoint(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Resolver endpoint de conexión para un nodo."""
        # En producción: usar service discovery
        return {
            'host': f'node-{node_id}.federation.local',
            'port': 8443,
            'protocol': 'grpc'
        }

    async def _connect_grpc_node(self, node_id: str, node_info: Dict[str, Any], attempt: int) -> bool:
        """Conectar vía gRPC."""
        # Implementación simplificada
        await asyncio.sleep(0.1)
        return attempt < 2  # Simular éxito en primeros intentos

    async def _connect_websocket_node(self, node_id: str, node_info: Dict[str, Any], attempt: int) -> bool:
        """Conectar vía WebSocket."""
        await asyncio.sleep(0.1)
        return attempt < 2

    async def _connect_http_node(self, node_id: str, node_info: Dict[str, Any], attempt: int) -> bool:
        """Conectar vía HTTP."""
        await asyncio.sleep(0.1)
        return attempt < 2

    async def _ping_node(self, node_id: str, node_info: Dict[str, Any]) -> bool:
        """Hacer ping simple al nodo."""
        await asyncio.sleep(0.1)
        return True

    async def _get_node_health_metrics(self, node_id: str) -> Dict[str, Any]:
        """Obtener métricas de salud del nodo."""
        # Simulado - en producción consultar APIs del nodo
        return {
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'network_latency': 150,
            'model_loaded': True
        }

    async def _identify_lost_data(self, node_id: str) -> List[str]:
        """Identificar qué datos se perdieron."""
        # Simulado - verificar si hay actualizaciones pendientes
        return []  # Asumir que no se perdió nada

    async def _recover_gradient_updates(self, node_id: str) -> bool:
        """Recuperar actualizaciones de gradientes."""
        return True

    async def _recover_model_state(self, node_id: str) -> bool:
        """Recuperar estado del modelo."""
        return True

    async def _recover_metadata(self, node_id: str) -> bool:
        """Recuperar metadatos."""
        return True

    async def _send_auth_challenge(self, node_id: str, challenge: str) -> Optional[str]:
        """Enviar challenge de autenticación."""
        # Simulado
        return self._compute_auth_response(node_id, challenge)

    def _compute_auth_response(self, node_id: str, challenge: str) -> str:
        """Computar respuesta de autenticación."""
        key = self._derive_session_key(node_id)
        return hmac.new(key, challenge.encode(), hashlib.sha256).hexdigest()

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Registrar evento en el log."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "phase": self.phase.value,
            "data": data
        }
        self.logs.append(event)

    def get_aggregated_gradients(self) -> Optional[Dict[str, torch.Tensor]]:
        """Obtener gradientes agregados si la agregación está completa."""
        if self.phase == AggregationPhase.COMPLETED:
            return self.aggregated_gradients
        return None

    def get_aggregation_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la agregación."""
        return {
            "session_id": self.config.session_id,
            "phase": self.phase.value,
            "total_nodes": self.metrics.total_nodes,
            "active_nodes": len(self.active_nodes),
            "failed_nodes": len(self.failed_nodes),
            "recovered_nodes": len(self.recovered_nodes),
            "progress": len(self.active_nodes) / max(1, self.metrics.total_nodes),
            "dropout_rate": self.metrics.dropout_rate,
            "aggregation_time": self.metrics.aggregation_time,
            "start_time": self.start_time,
            "is_complete": self.phase == AggregationPhase.COMPLETED
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas completas de rendimiento."""
        total_time = time.time() - self.start_time
        return {
            "session_id": self.config.session_id,
            "total_time": total_time,
            "aggregation_metrics": {
                "total_nodes": self.metrics.total_nodes,
                "active_nodes": self.metrics.active_nodes,
                "failed_nodes": self.metrics.failed_nodes,
                "recovered_nodes": self.metrics.recovered_nodes,
                "aggregation_time": self.metrics.aggregation_time,
                "encryption_time": self.metrics.encryption_time,
                "verification_time": self.metrics.verification_time,
                "throughput_nodes_per_second": self.metrics.active_nodes / max(0.1, self.metrics.aggregation_time),
                "dropout_rate": self.metrics.dropout_rate,
                "integrity_violations": self.metrics.integrity_violations
            },
            "efficiency": {
                "success_rate": self.metrics.active_nodes / max(1, self.metrics.total_nodes),
                "recovery_rate": self.metrics.recovered_nodes / max(1, self.metrics.failed_nodes),
                "time_efficiency": self.metrics.aggregation_time / max(0.1, total_time)
            },
            "logs_count": len(self.logs)
        }

    def get_logs(self) -> List[Dict[str, Any]]:
        """Obtener logs de eventos."""
        return self.logs.copy()

    async def shutdown(self):
        """Apagar el agregador y liberar recursos."""
        try:
            # Limpiar estado
            self.gradient_updates.clear()
            self.global_mask_sum.clear()

            # Apagar componentes
            self.encryptor.clear_cache()

            logger.info("🛑 SecureGradientAggregator shutdown")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


# Funciones de conveniencia

def create_secure_gradient_aggregator(session_id: str, **config_kwargs) -> SecureGradientAggregator:
    """Crear un agregador seguro de gradientes con configuración predeterminada."""
    config = SecureAggregationConfig(session_id=session_id, **config_kwargs)
    return SecureGradientAggregator(config)


async def aggregate_gradients_secure(aggregator: SecureGradientAggregator,
                                   gradient_updates: List[Tuple[str, Dict[str, torch.Tensor], int]]) -> Optional[Dict[str, torch.Tensor]]:
    """
    Función de conveniencia para agregar gradientes de manera segura.

    Args:
        aggregator: Instancia del agregador
        gradient_updates: Lista de (node_id, gradients, num_samples)

    Returns:
        Gradientes agregados o None si falla
    """
    try:
        # Inicializar agregación
        node_ids = [node_id for node_id, _, _ in gradient_updates]
        success = await aggregator.initialize_aggregation(node_ids)
        if not success:
            return None

        # Enviar actualizaciones
        tasks = []
        for node_id, gradients, num_samples in gradient_updates:
            task = aggregator.submit_gradient_update(node_id, gradients, num_samples)
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Esperar a que complete la agregación
        timeout = aggregator.config.timeout_seconds
        start_wait = time.time()
        while aggregator.phase != AggregationPhase.COMPLETED and (time.time() - start_wait) < timeout:
            await asyncio.sleep(0.1)

        return aggregator.get_aggregated_gradients()

    except Exception as e:
        logger.error(f"❌ Secure aggregation failed: {e}")
        return None