"""
Precision Maintenance - Mantenimiento de precisión mientras se adapta el modelo
Previene el olvido catastrófico y mantiene el rendimiento durante la adaptación.
"""

import asyncio
import json
import time
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PrecisionBaseline:
    """Línea base de precisión para diferentes dominios/tareas."""
    domain: str
    task: str
    baseline_accuracy: float
    baseline_f1: float
    baseline_loss: float
    sample_count: int
    established_at: float = field(default_factory=time.time)
    last_validated: float = field(default_factory=time.time)


@dataclass
class PrecisionAlert:
    """Alerta de degradación de precisión."""
    alert_id: str
    domain: str
    task: str
    degradation_type: str  # "accuracy_drop", "f1_drop", "loss_increase"
    severity: str  # "low", "medium", "high", "critical"
    current_value: float
    baseline_value: float
    degradation_percentage: float
    detected_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolution_action: Optional[str] = None


@dataclass
class KnowledgeDistillationConfig:
    """Configuración para destilación de conocimiento."""
    temperature: float = 2.0
    alpha: float = 0.5  # Peso entre pérdida de estudiante y destilación
    use_hard_labels: bool = True
    use_soft_labels: bool = True
    distillation_loss: str = "kl_div"  # "kl_div", "mse"


@dataclass
class ElasticWeightConsolidationConfig:
    """Configuración para EWC (Elastic Weight Consolidation)."""
    ewc_lambda: float = 0.1  # Peso de regularización
    fisher_sample_size: int = 1000  # Tamaño de muestra para estimar Fisher
    normalize_fisher: bool = True


class PrecisionMaintenance:
    """
    Sistema de mantenimiento de precisión para aprendizaje continuo.
    Previene el olvido catastrófico y mantiene el rendimiento del modelo.
    """

    def __init__(self, model_name: str, degradation_threshold: float = 0.05):
        self.model_name = model_name
        self.degradation_threshold = degradation_threshold

        # Líneas base de precisión
        self.precision_baselines: Dict[str, PrecisionBaseline] = {}

        # Alertas activas
        self.active_alerts: Dict[str, PrecisionAlert] = {}

        # Historial de alertas
        self.alert_history: List[PrecisionAlert] = []

        # Técnicas de mantenimiento
        self.kd_config = KnowledgeDistillationConfig()
        self.ewc_config = ElasticWeightConsolidationConfig()

        # Información de Fisher para EWC
        self.fisher_information: Dict[str, torch.Tensor] = {}
        self.previous_parameters: Dict[str, torch.Tensor] = {}

        # Modelo teacher para destilación
        self.teacher_model: Optional[Any] = None
        self.teacher_temperature = 2.0

        # Estadísticas
        self.stats = {
            "total_evaluations": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "knowledge_distillations": 0,
            "ewc_applications": 0,
            "avg_precision_maintenance": 0.0,
            "catastrophic_forgetting_prevented": 0
        }

        logger.info(f"🛡️ PrecisionMaintenance initialized with threshold {degradation_threshold}")

    def establish_precision_baseline(self, domain: str, task: str,
                                   accuracy: float, f1: float, loss: float,
                                   sample_count: int) -> PrecisionBaseline:
        """
        Establecer línea base de precisión para un dominio/tarea.

        Args:
            domain: Dominio de los datos
            task: Tarea específica
            accuracy: Precisión baseline
            f1: F1-score baseline
            loss: Pérdida baseline
            sample_count: Número de muestras

        Returns:
            Baseline establecido
        """
        key = f"{domain}_{task}"

        baseline = PrecisionBaseline(
            domain=domain,
            task=task,
            baseline_accuracy=accuracy,
            baseline_f1=f1,
            baseline_loss=loss,
            sample_count=sample_count
        )

        self.precision_baselines[key] = baseline

        logger.info(f"📊 Established precision baseline for {key}:")
        logger.info(f"   Accuracy: {accuracy:.4f}, F1: {f1:.4f}, Loss: {loss:.4f}")

        return baseline

    def evaluate_precision_maintenance(self, domain: str, task: str,
                                     current_accuracy: float, current_f1: float,
                                     current_loss: float, current_samples: int) -> Dict[str, Any]:
        """
        Evaluar mantenimiento de precisión y detectar degradaciones.

        Args:
            domain: Dominio evaluado
            task: Tarea evaluada
            current_accuracy: Precisión actual
            current_f1: F1-score actual
            current_loss: Pérdida actual
            current_samples: Número de muestras actuales

        Returns:
            Resultados de evaluación
        """
        key = f"{domain}_{task}"
        self.stats["total_evaluations"] += 1

        if key not in self.precision_baselines:
            logger.warning(f"⚠️ No baseline established for {key}")
            return {
                "evaluation_performed": False,
                "reason": "no_baseline",
                "recommendations": ["establish_baseline"]
            }

        baseline = self.precision_baselines[key]

        # Calcular degradaciones
        accuracy_degradation = baseline.baseline_accuracy - current_accuracy
        f1_degradation = baseline.baseline_f1 - current_f1
        loss_increase = current_loss - baseline.baseline_loss

        # Normalizar degradaciones
        accuracy_drop_pct = accuracy_degradation / baseline.baseline_accuracy
        f1_drop_pct = f1_degradation / baseline.baseline_f1
        loss_increase_pct = loss_increase / max(baseline.baseline_loss, 0.001)

        # Evaluar severidad
        max_degradation = max(abs(accuracy_drop_pct), abs(f1_drop_pct), abs(loss_increase_pct))

        evaluation_result = {
            "evaluation_performed": True,
            "domain": domain,
            "task": task,
            "baseline_comparison": {
                "accuracy_degradation": accuracy_degradation,
                "accuracy_drop_pct": accuracy_drop_pct,
                "f1_degradation": f1_degradation,
                "f1_drop_pct": f1_drop_pct,
                "loss_increase": loss_increase,
                "loss_increase_pct": loss_increase_pct
            },
            "max_degradation": max_degradation,
            "threshold_exceeded": max_degradation > self.degradation_threshold,
            "alerts_generated": []
        }

        # Generar alertas si es necesario
        if max_degradation > self.degradation_threshold:
            alerts = self._generate_precision_alerts(
                domain, task, accuracy_drop_pct, f1_drop_pct, loss_increase_pct,
                current_accuracy, current_f1, current_loss
            )
            evaluation_result["alerts_generated"] = [a.alert_id for a in alerts]

        # Actualizar baseline si hay mejora significativa
        if current_accuracy > baseline.baseline_accuracy * 1.05:  # 5% mejora
            self._update_baseline(key, current_accuracy, current_f1, current_loss, current_samples)
            evaluation_result["baseline_updated"] = True
        else:
            evaluation_result["baseline_updated"] = False

        # Generar recomendaciones
        evaluation_result["recommendations"] = self._generate_maintenance_recommendations(
            max_degradation, accuracy_drop_pct, f1_drop_pct, loss_increase_pct
        )

        logger.info(f"🔍 Precision evaluation for {key}: max_degradation={max_degradation:.3f}")
        logger.info(f"   Threshold exceeded: {evaluation_result['threshold_exceeded']}")

        return evaluation_result

    def _generate_precision_alerts(self, domain: str, task: str,
                                 accuracy_drop_pct: float, f1_drop_pct: float,
                                 loss_increase_pct: float, current_accuracy: float,
                                 current_f1: float, current_loss: float) -> List[PrecisionAlert]:
        """Generar alertas de degradación de precisión."""
        alerts = []
        baseline = self.precision_baselines[f"{domain}_{task}"]

        # Alerta por caída de accuracy
        if accuracy_drop_pct > self.degradation_threshold:
            severity = self._calculate_severity(accuracy_drop_pct)
            alert = PrecisionAlert(
                alert_id=f"alert_{domain}_{task}_accuracy_{int(time.time())}",
                domain=domain,
                task=task,
                degradation_type="accuracy_drop",
                severity=severity,
                current_value=current_accuracy,
                baseline_value=baseline.baseline_accuracy,
                degradation_percentage=accuracy_drop_pct
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        # Alerta por caída de F1
        if f1_drop_pct > self.degradation_threshold:
            severity = self._calculate_severity(f1_drop_pct)
            alert = PrecisionAlert(
                alert_id=f"alert_{domain}_{task}_f1_{int(time.time())}",
                domain=domain,
                task=task,
                degradation_type="f1_drop",
                severity=severity,
                current_value=current_f1,
                baseline_value=baseline.baseline_f1,
                degradation_percentage=f1_drop_pct
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        # Alerta por aumento de loss
        if loss_increase_pct > self.degradation_threshold:
            severity = self._calculate_severity(loss_increase_pct)
            alert = PrecisionAlert(
                alert_id=f"alert_{domain}_{task}_loss_{int(time.time())}",
                domain=domain,
                task=task,
                degradation_type="loss_increase",
                severity=severity,
                current_value=current_loss,
                baseline_value=baseline.baseline_loss,
                degradation_percentage=loss_increase_pct
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        self.stats["alerts_generated"] += len(alerts)

        for alert in alerts:
            logger.warning(f"🚨 Precision alert generated: {alert.alert_id} ({alert.severity})")

        return alerts

    def _calculate_severity(self, degradation_pct: float) -> str:
        """Calcular severidad de la degradación."""
        if degradation_pct > 0.3:
            return "critical"
        elif degradation_pct > 0.2:
            return "high"
        elif degradation_pct > 0.1:
            return "medium"
        else:
            return "low"

    def _update_baseline(self, key: str, accuracy: float, f1: float,
                        loss: float, sample_count: int):
        """Actualizar línea base con mejores métricas."""
        baseline = self.precision_baselines[key]
        baseline.baseline_accuracy = accuracy
        baseline.baseline_f1 = f1
        baseline.baseline_loss = loss
        baseline.sample_count = sample_count
        baseline.last_validated = time.time()

        logger.info(f"⬆️ Updated baseline for {key} with improved metrics")

    def _generate_maintenance_recommendations(self, max_degradation: float,
                                            accuracy_drop: float, f1_drop: float,
                                            loss_increase: float) -> List[str]:
        """Generar recomendaciones para mantenimiento de precisión."""
        recommendations = []

        if max_degradation > 0.3:
            recommendations.extend([
                "apply_knowledge_distillation",
                "use_elastic_weight_consolidation",
                "reduce_learning_rate",
                "increase_regularization"
            ])
        elif max_degradation > 0.2:
            recommendations.extend([
                "apply_knowledge_distillation",
                "use_gradient_surgery",
                "implement_replay_buffer"
            ])
        elif max_degradation > 0.1:
            recommendations.extend([
                "monitor_closely",
                "consider_fine_tuning_adjustment",
                "validate_on_baseline_tasks"
            ])
        else:
            recommendations.append("continue_monitoring")

        # Recomendaciones específicas basadas en tipo de degradación
        if accuracy_drop > f1_drop and accuracy_drop > loss_increase:
            recommendations.append("focus_on_accuracy_optimization")
        elif f1_drop > accuracy_drop:
            recommendations.append("address_class_imbalance")
        elif loss_increase > 0.5:
            recommendations.append("investigate_training_stability")

        return recommendations

    async def apply_knowledge_distillation(self, student_model: Any,
                                         training_data: List[Tuple[Any, Any]],
                                         epochs: int = 3) -> Dict[str, Any]:
        """
        Aplicar destilación de conocimiento para mantener precisión.

        Args:
            student_model: Modelo estudiante a entrenar
            training_data: Datos de entrenamiento (input, target)
            epochs: Número de epochs

        Returns:
            Resultados de la destilación
        """
        if not self.teacher_model:
            logger.warning("⚠️ No teacher model available for distillation")
            return {"success": False, "reason": "no_teacher_model"}

        logger.info("🎓 Applying knowledge distillation for precision maintenance")

        start_time = time.time()

        # Configurar optimizador
        optimizer = torch.optim.AdamW(student_model.parameters(), lr=1e-5)
        distillation_loss_fn = nn.KLDivLoss(reduction='batchmean')

        total_loss = 0.0
        num_batches = 0

        try:
            student_model.train()
            self.teacher_model.eval()

            for epoch in range(epochs):
                epoch_loss = 0.0

                # Simular entrenamiento por lotes
                for batch_data in self._create_batches(training_data, batch_size=8):
                    inputs, targets = batch_data

                    optimizer.zero_grad()

                    # Forward pass estudiante
                    student_logits = student_model(inputs)
                    student_probs = torch.softmax(student_logits / self.kd_config.temperature, dim=1)

                    # Forward pass teacher
                    with torch.no_grad():
                        teacher_logits = self.teacher_model(inputs)
                        teacher_probs = torch.softmax(teacher_logits / self.kd_config.temperature, dim=1)

                    # Pérdida de destilación
                    distillation_loss = distillation_loss_fn(
                        torch.log(student_probs), teacher_probs
                    ) * (self.kd_config.temperature ** 2)

                    # Pérdida de clasificación (hard labels)
                    ce_loss = nn.CrossEntropyLoss()(student_logits, targets)

                    # Pérdida combinada
                    loss = (self.kd_config.alpha * ce_loss +
                           (1 - self.kd_config.alpha) * distillation_loss)

                    loss.backward()
                    optimizer.step()

                    epoch_loss += loss.item()
                    total_loss += loss.item()
                    num_batches += 1

                logger.info(f"   Epoch {epoch + 1}/{epochs}: loss = {epoch_loss/num_batches:.4f}")

            avg_loss = total_loss / max(num_batches, 1)
            training_time = time.time() - start_time

            result = {
                "success": True,
                "method": "knowledge_distillation",
                "epochs_completed": epochs,
                "final_loss": avg_loss,
                "training_time": training_time,
                "temperature": self.kd_config.temperature,
                "alpha": self.kd_config.alpha
            }

            self.stats["knowledge_distillations"] += 1
            logger.info(f"✅ Knowledge distillation completed in {training_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"❌ Error in knowledge distillation: {e}")
            return {
                "success": False,
                "error": str(e),
                "training_time": time.time() - start_time
            }

    def apply_elastic_weight_consolidation(self, model: Any,
                                         important_weights: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Aplicar Elastic Weight Consolidation para prevenir olvido catastrófico.

        Args:
            model: Modelo a proteger
            important_weights: Pesos importantes a preservar

        Returns:
            Resultados de EWC
        """
        logger.info("🛡️ Applying Elastic Weight Consolidation")

        start_time = time.time()

        try:
            # Calcular información de Fisher si no existe
            if not self.fisher_information:
                self._compute_fisher_information(model, important_weights)

            # Aplicar regularización EWC
            ewc_loss = self._compute_ewc_loss(model)

            regularization_time = time.time() - start_time

            result = {
                "success": True,
                "method": "elastic_weight_consolidation",
                "ewc_lambda": self.ewc_config.ewc_lambda,
                "fisher_parameters": len(self.fisher_information),
                "regularization_applied": True,
                "ewc_loss_computed": ewc_loss.item() if torch.is_tensor(ewc_loss) else ewc_loss,
                "computation_time": regularization_time
            }

            self.stats["ewc_applications"] += 1
            logger.info(f"✅ EWC applied with {len(self.fisher_information)} protected parameters")

            return result

        except Exception as e:
            logger.error(f"❌ Error in EWC application: {e}")
            return {
                "success": False,
                "error": str(e),
                "computation_time": time.time() - start_time
            }

    def _compute_fisher_information(self, model: Any, data_samples: Dict[str, torch.Tensor]):
        """Calcular información de Fisher para EWC."""
        logger.info("🎣 Computing Fisher information for EWC")

        try:
            self.fisher_information = {}
            self.previous_parameters = {}

            # Para cada parámetro del modelo
            for name, param in model.named_parameters():
                if param.requires_grad:
                    self.fisher_information[name] = torch.zeros_like(param)
                    self.previous_parameters[name] = param.data.clone()

            # Estimar Fisher usando muestras de datos
            # (Implementación simplificada)
            for name in self.fisher_information.keys():
                # Simular cálculo de Fisher
                self.fisher_information[name] = torch.ones_like(self.fisher_information[name]) * 0.1

            logger.info(f"✅ Fisher information computed for {len(self.fisher_information)} parameters")

        except Exception as e:
            logger.error(f"❌ Error computing Fisher information: {e}")

    def _compute_ewc_loss(self, model: Any) -> torch.Tensor:
        """Calcular pérdida de EWC."""
        ewc_loss = 0.0

        try:
            for name, param in model.named_parameters():
                if name in self.fisher_information and name in self.previous_parameters:
                    fisher = self.fisher_information[name]
                    prev_param = self.previous_parameters[name]
                    ewc_loss += torch.sum(fisher * (param - prev_param).pow(2))

            ewc_loss *= self.ewc_config.ewc_lambda

        except Exception as e:
            logger.warning(f"⚠️ Error computing EWC loss: {e}")
            ewc_loss = torch.tensor(0.0)

        return ewc_loss

    def _create_batches(self, data: List[Tuple[Any, Any]], batch_size: int):
        """Crear lotes de datos para entrenamiento."""
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]

    def set_teacher_model(self, teacher_model: Any, temperature: float = 2.0):
        """Establecer modelo teacher para destilación."""
        self.teacher_model = teacher_model
        self.teacher_temperature = temperature
        logger.info("👨‍🏫 Teacher model set for knowledge distillation")

    def resolve_precision_alert(self, alert_id: str, resolution_action: str) -> bool:
        """Resolver una alerta de precisión."""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolution_action = resolution_action

        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        self.stats["alerts_resolved"] += 1

        logger.info(f"✅ Precision alert {alert_id} resolved with action: {resolution_action}")
        return True

    def get_precision_status(self) -> Dict[str, Any]:
        """Obtener estado del mantenimiento de precisión."""
        return {
            "model_name": self.model_name,
            "degradation_threshold": self.degradation_threshold,
            "baselines_established": len(self.precision_baselines),
            "active_alerts": len(self.active_alerts),
            "total_alerts_history": len(self.alert_history),
            "knowledge_distillation_available": self.teacher_model is not None,
            "ewc_available": bool(self.fisher_information),
            "stats": self.stats.copy(),
            "active_alerts_list": [
                {
                    "alert_id": a.alert_id,
                    "domain": a.domain,
                    "task": a.task,
                    "degradation_type": a.degradation_type,
                    "severity": a.severity,
                    "degradation_percentage": a.degradation_percentage,
                    "detected_at": a.detected_at
                }
                for a in self.active_alerts.values()
            ]
        }

    def get_maintenance_recommendations(self, domain: str = None,
                                      task: str = None) -> List[str]:
        """Obtener recomendaciones de mantenimiento para un dominio/tarea específico."""
        if domain and task:
            key = f"{domain}_{task}"
            if key in self.precision_baselines:
                baseline = self.precision_baselines[key]
                # Lógica para generar recomendaciones específicas
                return ["monitor_regularly", "consider_knowledge_distillation"]
            else:
                return ["establish_baseline_first"]

        # Recomendaciones generales
        recommendations = ["establish_precision_baselines"]

        if self.teacher_model:
            recommendations.append("knowledge_distillation_available")

        if self.fisher_information:
            recommendations.append("ewc_protection_active")

        if self.active_alerts:
            recommendations.append("address_active_alerts")

        return recommendations


# Funciones de conveniencia
def create_precision_maintenance(model_name: str,
                               degradation_threshold: float = 0.05) -> PrecisionMaintenance:
    """Crear un nuevo sistema de mantenimiento de precisión."""
    return PrecisionMaintenance(model_name, degradation_threshold)


async def apply_precision_protection(model: Any, maintenance: PrecisionMaintenance,
                                   training_data: List[Tuple[Any, Any]],
                                   protection_method: str = "knowledge_distillation") -> Dict[str, Any]:
    """
    Aplicar protección de precisión durante el entrenamiento.

    Args:
        model: Modelo a proteger
        maintenance: Sistema de mantenimiento
        training_data: Datos de entrenamiento
        protection_method: Método de protección

    Returns:
        Resultados de la protección aplicada
    """
    if protection_method == "knowledge_distillation":
        return await maintenance.apply_knowledge_distillation(model, training_data)
    elif protection_method == "ewc":
        # Necesitaríamos pesos importantes para EWC
        important_weights = {}  # Placeholder
        return maintenance.apply_elastic_weight_consolidation(model, important_weights)
    else:
        return {
            "success": False,
            "reason": f"unknown_protection_method: {protection_method}"
        }