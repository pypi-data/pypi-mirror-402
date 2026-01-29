"""
Advanced Threat Detection para AILOOS

Implementa detección avanzada de amenazas con:
- AI-powered anomaly detection
- Behavioral analysis
- Automated response
- Threat intelligence integration
"""

import asyncio
import logging
import json
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import pickle

logger = logging.getLogger(__name__)


class ThreatSeverity(Enum):
    """Severidad de amenazas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Tipos de amenazas."""
    ANOMALY = "anomaly"
    BRUTE_FORCE = "brute_force"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE = "malware"
    INSIDER_THREAT = "insider_threat"
    DDoS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"


class ResponseAction(Enum):
    """Acciones de respuesta automatizada."""
    ALERT = "alert"
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    LOGOUT_SESSION = "logout_session"
    QUARANTINE = "quarantine"
    SHUTDOWN_SERVICE = "shutdown_service"
    NOTIFY_SECURITY = "notify_security"


@dataclass
class ThreatIndicator:
    """Indicador de amenaza."""
    indicator_id: str
    threat_type: ThreatType
    severity: ThreatSeverity
    confidence: float  # 0-1
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def risk_score(self) -> float:
        """Calcular risk score basado en severidad y confianza."""
        severity_multiplier = {
            ThreatSeverity.LOW: 1,
            ThreatSeverity.MEDIUM: 2,
            ThreatSeverity.HIGH: 3,
            ThreatSeverity.CRITICAL: 4
        }[self.severity]

        return min(100, severity_multiplier * self.confidence * 25)


@dataclass
class BehavioralProfile:
    """Perfil behavioral de usuario/servicio."""
    entity_id: str
    entity_type: str  # "user", "service", "ip"
    baseline_metrics: Dict[str, float] = field(default_factory=dict)
    historical_data: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    anomaly_threshold: float = 0.1

    def update_baseline(self, new_metrics: Dict[str, float]):
        """Actualizar baseline con nuevas métricas."""
        # Weighted average with historical data
        weight_new = 0.3
        weight_old = 0.7

        for metric, value in new_metrics.items():
            if metric in self.baseline_metrics:
                self.baseline_metrics[metric] = (
                    weight_old * self.baseline_metrics[metric] +
                    weight_new * value
                )
            else:
                self.baseline_metrics[metric] = value

        self.last_updated = datetime.now()

    def detect_anomaly(self, current_metrics: Dict[str, float]) -> Tuple[bool, float, Dict[str, float]]:
        """Detectar anomalías en métricas actuales."""
        anomalies = {}
        anomaly_score = 0.0
        anomaly_count = 0

        for metric, current_value in current_metrics.items():
            if metric in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric]

                # Calculate deviation
                if baseline_value != 0:
                    deviation = abs(current_value - baseline_value) / baseline_value
                else:
                    deviation = abs(current_value)

                if deviation > self.anomaly_threshold:
                    anomalies[metric] = {
                        'current': current_value,
                        'baseline': baseline_value,
                        'deviation': deviation
                    }
                    anomaly_score += deviation
                    anomaly_count += 1

        is_anomaly = anomaly_count > 0
        avg_anomaly_score = anomaly_score / max(1, anomaly_count)

        return is_anomaly, avg_anomaly_score, anomalies


@dataclass
class AIModel:
    """Modelo de IA para detección de anomalías."""
    model_id: str
    model_type: str  # "isolation_forest", "autoencoder", etc.
    trained_at: Optional[datetime] = None
    accuracy_score: float = 0.0
    feature_columns: List[str] = field(default_factory=list)
    model_data: Optional[bytes] = None  # Serialized model

    @property
    def is_trained(self) -> bool:
        """Verificar si el modelo está entrenado."""
        return self.trained_at is not None and self.model_data is not None

    def predict_anomaly(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """Predecir anomalía usando el modelo."""
        if not self.is_trained:
            return False, 0.0

        try:
            # Deserialize model
            model = pickle.loads(self.model_data)

            # Prepare features
            feature_vector = [features.get(col, 0.0) for col in self.feature_columns]

            # Predict
            if self.model_type == "isolation_forest":
                # Isolation Forest returns -1 for anomalies, 1 for normal
                prediction = model.predict([feature_vector])[0]
                anomaly_score = model.decision_function([feature_vector])[0]

                is_anomaly = prediction == -1
                confidence = abs(anomaly_score)  # Higher absolute value = more anomalous

            else:
                # Default: simple threshold-based
                is_anomaly = False
                confidence = 0.0

            return is_anomaly, confidence

        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return False, 0.0


class AnomalyDetectionEngine:
    """
    Motor de detección de anomalías basado en IA.

    Características:
    - Machine learning para detección de patrones
    - Behavioral analysis
    - Real-time scoring
    - Model training y actualización automática
    """

    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.behavioral_profiles: Dict[str, BehavioralProfile] = {}
        self.training_data: List[Dict[str, Any]] = []
        self.anomaly_threshold = 0.7

    def create_ai_model(self, model_id: str, model_type: str, feature_columns: List[str]) -> AIModel:
        """Crear nuevo modelo de IA."""
        model = AIModel(
            model_id=model_id,
            model_type=model_type,
            feature_columns=feature_columns
        )

        self.models[model_id] = model
        logger.info(f"Created AI model: {model_id} ({model_type})")

        return model

    async def train_model(self, model_id: str, training_data: List[Dict[str, Any]]) -> bool:
        """Entrenar modelo de IA."""
        if model_id not in self.models:
            return False

        model = self.models[model_id]

        try:
            # Prepare training data
            X = []
            for data_point in training_data:
                features = [data_point.get(col, 0.0) for col in model.feature_columns]
                X.append(features)

            X = np.array(X)

            # Train model based on type
            if model.model_type == "isolation_forest":
                ml_model = IsolationForest(
                    contamination=0.1,  # Expected percentage of anomalies
                    random_state=42
                )
                ml_model.fit(X)

                # Evaluate on training data
                predictions = ml_model.predict(X)
                anomaly_score = ml_model.decision_function(X)

                # Calculate accuracy (simplified)
                accuracy = 1.0 - (sum(predictions == -1) / len(predictions))

            else:
                logger.warning(f"Unsupported model type: {model.model_type}")
                return False

            # Serialize and store model
            model.model_data = pickle.dumps(ml_model)
            model.trained_at = datetime.now()
            model.accuracy_score = accuracy

            logger.info(f"Trained AI model {model_id}: accuracy={accuracy:.3f}")
            return True

        except Exception as e:
            logger.error(f"Model training failed for {model_id}: {e}")
            return False

    async def detect_anomalies(self, entity_id: str, current_metrics: Dict[str, float],
                              context: Dict[str, Any]) -> List[ThreatIndicator]:
        """Detectar anomalías usando IA y análisis behavioral."""
        indicators = []

        # 1. AI-powered anomaly detection
        ai_indicators = await self._ai_anomaly_detection(entity_id, current_metrics)
        indicators.extend(ai_indicators)

        # 2. Behavioral analysis
        behavioral_indicators = await self._behavioral_anomaly_detection(entity_id, current_metrics)
        indicators.extend(behavioral_indicators)

        # 3. Rule-based detection
        rule_indicators = await self._rule_based_detection(entity_id, current_metrics, context)
        indicators.extend(rule_indicators)

        # Update behavioral profile
        if entity_id not in self.behavioral_profiles:
            self.behavioral_profiles[entity_id] = BehavioralProfile(
                entity_id=entity_id,
                entity_type=context.get('entity_type', 'unknown')
            )

        profile = self.behavioral_profiles[entity_id]
        profile.update_baseline(current_metrics)

        # Store training data
        training_point = {
            'entity_id': entity_id,
            'timestamp': datetime.now(),
            'metrics': current_metrics,
            'context': context,
            'anomalies_detected': len(indicators)
        }
        self.training_data.append(training_point)

        # Keep only last 10000 training points
        if len(self.training_data) > 10000:
            self.training_data = self.training_data[-10000:]

        return indicators

    async def _ai_anomaly_detection(self, entity_id: str,
                                   metrics: Dict[str, float]) -> List[ThreatIndicator]:
        """Detección de anomalías usando IA."""
        indicators = []

        # Use available AI models
        for model in self.models.values():
            if model.is_trained:
                is_anomaly, confidence = model.predict_anomaly(metrics)

                if is_anomaly and confidence > self.anomaly_threshold:
                    indicator = ThreatIndicator(
                        indicator_id=f"ai_anomaly_{entity_id}_{int(time.time())}",
                        threat_type=ThreatType.ANOMALY,
                        severity=self._confidence_to_severity(confidence),
                        confidence=confidence,
                        description=f"AI-detected anomaly in {entity_id} metrics",
                        user_id=entity_id if entity_id.startswith('user_') else None,
                        metadata={
                            'model_id': model.model_id,
                            'metrics': metrics,
                            'anomaly_score': confidence
                        }
                    )
                    indicators.append(indicator)

        return indicators

    async def _behavioral_anomaly_detection(self, entity_id: str,
                                          metrics: Dict[str, float]) -> List[ThreatIndicator]:
        """Detección de anomalías usando análisis behavioral."""
        indicators = []

        if entity_id in self.behavioral_profiles:
            profile = self.behavioral_profiles[entity_id]
            is_anomaly, anomaly_score, anomalies = profile.detect_anomaly(metrics)

            if is_anomaly:
                severity = ThreatSeverity.MEDIUM
                if anomaly_score > 0.5:
                    severity = ThreatSeverity.HIGH
                if anomaly_score > 0.8:
                    severity = ThreatSeverity.CRITICAL

                indicator = ThreatIndicator(
                    indicator_id=f"behavioral_anomaly_{entity_id}_{int(time.time())}",
                    threat_type=ThreatType.ANOMALY,
                    severity=severity,
                    confidence=min(1.0, anomaly_score),
                    description=f"Behavioral anomaly detected for {entity_id}",
                    user_id=entity_id if entity_id.startswith('user_') else None,
                    metadata={
                        'anomaly_score': anomaly_score,
                        'anomalous_metrics': anomalies
                    }
                )
                indicators.append(indicator)

        return indicators

    async def _rule_based_detection(self, entity_id: str, metrics: Dict[str, float],
                                  context: Dict[str, Any]) -> List[ThreatIndicator]:
        """Detección basada en reglas."""
        indicators = []

        # Rule 1: Brute force detection
        failed_login_attempts = metrics.get('failed_login_attempts', 0)
        if failed_login_attempts > 5:
            severity = ThreatSeverity.MEDIUM if failed_login_attempts > 10 else ThreatSeverity.LOW

            indicator = ThreatIndicator(
                indicator_id=f"brute_force_{entity_id}_{int(time.time())}",
                threat_type=ThreatType.BRUTE_FORCE,
                severity=severity,
                confidence=min(1.0, failed_login_attempts / 20.0),
                description=f"Potential brute force attack: {failed_login_attempts} failed attempts",
                source_ip=context.get('source_ip'),
                user_id=entity_id if entity_id.startswith('user_') else None
            )
            indicators.append(indicator)

        # Rule 2: Data exfiltration detection
        data_transferred = metrics.get('data_transferred_mb', 0)
        if data_transferred > 100:  # 100MB threshold
            indicator = ThreatIndicator(
                indicator_id=f"data_exfil_{entity_id}_{int(time.time())}",
                threat_type=ThreatType.DATA_EXFILTRATION,
                severity=ThreatSeverity.HIGH,
                confidence=min(1.0, data_transferred / 1000.0),
                description=f"Suspicious data transfer: {data_transferred}MB",
                source_ip=context.get('source_ip'),
                user_id=entity_id if entity_id.startswith('user_') else None,
                metadata={'data_transferred_mb': data_transferred}
            )
            indicators.append(indicator)

        # Rule 3: DDoS detection
        requests_per_second = metrics.get('requests_per_second', 0)
        if requests_per_second > 1000:
            indicator = ThreatIndicator(
                indicator_id=f"ddos_{entity_id}_{int(time.time())}",
                threat_type=ThreatType.DDoS,
                severity=ThreatSeverity.CRITICAL,
                confidence=min(1.0, requests_per_second / 10000.0),
                description=f"Potential DDoS attack: {requests_per_second} req/sec",
                source_ip=context.get('source_ip'),
                service_name=entity_id if entity_id.startswith('service_') else None
            )
            indicators.append(indicator)

        return indicators

    def _confidence_to_severity(self, confidence: float) -> ThreatSeverity:
        """Convertir confianza a severidad."""
        if confidence > 0.8:
            return ThreatSeverity.CRITICAL
        elif confidence > 0.6:
            return ThreatSeverity.HIGH
        elif confidence > 0.4:
            return ThreatSeverity.MEDIUM
        else:
            return ThreatSeverity.LOW

    async def retrain_models(self) -> Dict[str, bool]:
        """Re-entrenar modelos con nuevos datos."""
        results = {}

        # Group training data by model features
        for model in self.models.values():
            if len(self.training_data) >= 100:  # Minimum training data
                # Filter relevant training data
                relevant_data = [
                    data for data in self.training_data
                    if all(col in data.get('metrics', {}) for col in model.feature_columns)
                ]

                if len(relevant_data) >= 50:
                    success = await self.train_model(model.model_id, relevant_data)
                    results[model.model_id] = success
                else:
                    results[model.model_id] = False
            else:
                results[model.model_id] = False

        return results


class AutomatedResponseEngine:
    """
    Motor de respuesta automatizada a amenazas.

    Características:
    - Response playbooks
    - Automated actions
    - Escalation policies
    - Integration con herramientas de seguridad
    """

    def __init__(self):
        self.response_playbooks: Dict[str, Dict[str, Any]] = {}
        self.active_responses: Dict[str, Dict[str, Any]] = {}
        self.response_history: List[Dict[str, Any]] = []

    def create_response_playbook(self, threat_type: ThreatType,
                               severity: ThreatSeverity,
                               actions: List[ResponseAction]) -> str:
        """Crear playbook de respuesta."""
        playbook_id = f"playbook_{threat_type.value}_{severity.value}"

        playbook = {
            'playbook_id': playbook_id,
            'threat_type': threat_type.value,
            'severity': severity.value,
            'actions': [action.value for action in actions],
            'created_at': datetime.now(),
            'auto_execute': severity in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]
        }

        self.response_playbooks[playbook_id] = playbook
        logger.info(f"Created response playbook: {playbook_id}")

        return playbook_id

    async def execute_response(self, threat_indicator: ThreatIndicator) -> Dict[str, Any]:
        """Ejecutar respuesta automatizada para amenaza."""
        response_id = f"response_{threat_indicator.indicator_id}"

        # Find appropriate playbook
        playbook = self._find_playbook(threat_indicator.threat_type, threat_indicator.severity)

        if not playbook:
            return {'error': 'No playbook found for threat'}

        # Check if auto-execution is enabled
        if not playbook.get('auto_execute', False):
            return {'message': 'Manual review required'}

        # Execute actions
        executed_actions = []
        failed_actions = []

        for action_str in playbook['actions']:
            action = ResponseAction(action_str)
            success = await self._execute_action(action, threat_indicator)

            if success:
                executed_actions.append(action_str)
            else:
                failed_actions.append(action_str)

        # Record response
        response_record = {
            'response_id': response_id,
            'threat_indicator_id': threat_indicator.indicator_id,
            'playbook_id': playbook['playbook_id'],
            'executed_actions': executed_actions,
            'failed_actions': failed_actions,
            'timestamp': datetime.now(),
            'success': len(failed_actions) == 0
        }

        self.active_responses[response_id] = response_record
        self.response_history.append(response_record)

        # Keep only last 1000 responses
        if len(self.response_history) > 1000:
            self.response_history = self.response_history[-1000:]

        return {
            'response_id': response_id,
            'actions_executed': len(executed_actions),
            'actions_failed': len(failed_actions),
            'success': len(failed_actions) == 0
        }

    def _find_playbook(self, threat_type: ThreatType,
                      severity: ThreatSeverity) -> Optional[Dict[str, Any]]:
        """Encontrar playbook apropiado."""
        # Try exact match first
        exact_key = f"playbook_{threat_type.value}_{severity.value}"
        if exact_key in self.response_playbooks:
            return self.response_playbooks[exact_key]

        # Try threat type match
        threat_key = f"playbook_{threat_type.value}_any"
        if threat_key in self.response_playbooks:
            return self.response_playbooks[threat_key]

        # Try severity match
        severity_key = f"playbook_any_{severity.value}"
        if severity_key in self.response_playbooks:
            return self.response_playbooks[severity_key]

        return None

    async def _execute_action(self, action: ResponseAction,
                            threat_indicator: ThreatIndicator) -> bool:
        """Ejecutar acción específica."""
        try:
            if action == ResponseAction.ALERT:
                await self._send_alert(threat_indicator)
            elif action == ResponseAction.BLOCK_IP:
                await self._block_ip(threat_indicator.source_ip)
            elif action == ResponseAction.RATE_LIMIT:
                await self._apply_rate_limit(threat_indicator)
            elif action == ResponseAction.LOGOUT_SESSION:
                await self._logout_session(threat_indicator.user_id)
            elif action == ResponseAction.QUARANTINE:
                await self._quarantine_resource(threat_indicator)
            elif action == ResponseAction.SHUTDOWN_SERVICE:
                await self._shutdown_service(threat_indicator.service_name)
            elif action == ResponseAction.NOTIFY_SECURITY:
                await self._notify_security_team(threat_indicator)
            else:
                logger.warning(f"Unsupported action: {action}")
                return False

            logger.info(f"Executed response action: {action.value} for threat {threat_indicator.indicator_id}")
            return True

        except Exception as e:
            logger.error(f"Action execution failed: {action.value} - {e}")
            return False

    async def _send_alert(self, threat: ThreatIndicator) -> bool:
        """Enviar alerta (simulado)."""
        await asyncio.sleep(0.1)
        logger.info(f"Alert sent for threat: {threat.indicator_id}")
        return True

    async def _block_ip(self, ip: Optional[str]) -> bool:
        """Bloquear IP (simulado)."""
        if not ip:
            return False
        await asyncio.sleep(0.2)
        logger.info(f"IP blocked: {ip}")
        return True

    async def _apply_rate_limit(self, threat: ThreatIndicator) -> bool:
        """Aplicar rate limiting (simulado)."""
        await asyncio.sleep(0.1)
        logger.info(f"Rate limit applied for: {threat.indicator_id}")
        return True

    async def _logout_session(self, user_id: Optional[str]) -> bool:
        """Logout session (simulado)."""
        if not user_id:
            return False
        await asyncio.sleep(0.1)
        logger.info(f"Session logged out for user: {user_id}")
        return True

    async def _quarantine_resource(self, threat: ThreatIndicator) -> bool:
        """Quarantine resource (simulado)."""
        await asyncio.sleep(0.5)
        logger.info(f"Resource quarantined for threat: {threat.indicator_id}")
        return True

    async def _shutdown_service(self, service_name: Optional[str]) -> bool:
        """Shutdown service (simulado)."""
        if not service_name:
            return False
        await asyncio.sleep(1.0)
        logger.info(f"Service shutdown: {service_name}")
        return True

    async def _notify_security_team(self, threat: ThreatIndicator) -> bool:
        """Notificar equipo de seguridad (simulado)."""
        await asyncio.sleep(0.1)
        logger.info(f"Security team notified for threat: {threat.indicator_id}")
        return True


class ThreatDetectionOrchestrator:
    """
    Orchestrator principal para advanced threat detection.

    Coordina detección, análisis y respuesta.
    """

    def __init__(self):
        self.anomaly_engine = AnomalyDetectionEngine()
        self.response_engine = AutomatedResponseEngine()
        self.threat_indicators: List[ThreatIndicator] = []
        self.threat_intelligence: Dict[str, Any] = {}

    async def initialize_threat_detection(self):
        """Inicializar sistema de detección de amenazas."""
        # Create default AI models
        await self._create_default_models()

        # Create default response playbooks
        self._create_default_playbooks()

        logger.info("Advanced threat detection system initialized")

    async def _create_default_models(self):
        """Crear modelos de IA por defecto."""
        # User behavior model
        user_model = self.anomaly_engine.create_ai_model(
            model_id="user_behavior_model",
            model_type="isolation_forest",
            feature_columns=[
                "login_attempts", "session_duration", "data_accessed",
                "api_calls", "location_changes", "device_changes"
            ]
        )

        # Network traffic model
        network_model = self.anomaly_engine.create_ai_model(
            model_id="network_traffic_model",
            model_type="isolation_forest",
            feature_columns=[
                "requests_per_second", "bytes_transferred",
                "error_rate", "connection_count", "response_time"
            ]
        )

        # Train models with synthetic data
        await self._train_models_with_synthetic_data()

    def _create_default_playbooks(self):
        """Crear playbooks de respuesta por defecto."""
        # Brute force response
        self.response_engine.create_response_playbook(
            ThreatType.BRUTE_FORCE,
            ThreatSeverity.MEDIUM,
            [ResponseAction.BLOCK_IP, ResponseAction.ALERT, ResponseAction.NOTIFY_SECURITY]
        )

        # DDoS response
        self.response_engine.create_response_playbook(
            ThreatType.DDoS,
            ThreatSeverity.CRITICAL,
            [ResponseAction.RATE_LIMIT, ResponseAction.ALERT, ResponseAction.NOTIFY_SECURITY]
        )

        # Data exfiltration response
        self.response_engine.create_response_playbook(
            ThreatType.DATA_EXFILTRATION,
            ThreatSeverity.HIGH,
            [ResponseAction.QUARANTINE, ResponseAction.LOGOUT_SESSION, ResponseAction.ALERT]
        )

    async def _train_models_with_synthetic_data(self):
        """Entrenar modelos con datos sintéticos."""
        # Generate synthetic training data
        training_data = []

        for _ in range(1000):
            data_point = {
                'login_attempts': random.randint(1, 10),
                'session_duration': random.randint(60, 3600),
                'data_accessed': random.randint(1, 100),
                'api_calls': random.randint(10, 500),
                'location_changes': random.randint(0, 5),
                'device_changes': random.randint(0, 3),
                'requests_per_second': random.randint(1, 100),
                'bytes_transferred': random.randint(1000, 100000),
                'error_rate': random.uniform(0, 0.1),
                'connection_count': random.randint(1, 50),
                'response_time': random.uniform(0.1, 2.0)
            }
            training_data.append(data_point)

        # Train models
        for model_id in ["user_behavior_model", "network_traffic_model"]:
            await self.anomaly_engine.train_model(model_id, training_data)

    async def analyze_traffic(self, entity_id: str, metrics: Dict[str, float],
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar tráfico y detectar amenazas."""
        # Detect anomalies
        indicators = await self.anomaly_engine.detect_anomalies(entity_id, metrics, context)

        # Store indicators
        self.threat_indicators.extend(indicators)

        # Keep only last 5000 indicators
        if len(self.threat_indicators) > 5000:
            self.threat_indicators = self.threat_indicators[-5000:]

        # Execute automated responses
        responses = []
        for indicator in indicators:
            if indicator.severity in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]:
                response = await self.response_engine.execute_response(indicator)
                responses.append(response)

        return {
            'entity_id': entity_id,
            'threats_detected': len(indicators),
            'automated_responses': len(responses),
            'indicators': [
                {
                    'threat_type': i.threat_type.value,
                    'severity': i.severity.value,
                    'confidence': i.confidence,
                    'description': i.description
                } for i in indicators
            ]
        }

    async def get_threat_intelligence(self) -> Dict[str, Any]:
        """Obtener inteligencia de amenazas."""
        # Aggregate threat data
        threat_counts = {}
        severity_counts = {}
        recent_threats = []

        # Analyze last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        recent_indicators = [i for i in self.threat_indicators if i.timestamp > cutoff]

        for indicator in recent_indicators:
            # Count by threat type
            threat_type = indicator.threat_type.value
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

            # Count by severity
            severity = indicator.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Recent threats
            if len(recent_threats) < 10:
                recent_threats.append({
                    'threat_type': threat_type,
                    'severity': severity,
                    'description': indicator.description,
                    'timestamp': indicator.timestamp.isoformat()
                })

        return {
            'threat_counts': threat_counts,
            'severity_counts': severity_counts,
            'recent_threats': recent_threats,
            'total_threats_24h': len(recent_indicators),
            'most_common_threat': max(threat_counts.keys(), key=lambda k: threat_counts[k]) if threat_counts else None
        }

    def get_detection_status(self) -> Dict[str, Any]:
        """Obtener status del sistema de detección."""
        ai_models = len([m for m in self.anomaly_engine.models.values() if m.is_trained])
        total_models = len(self.anomaly_engine.models)

        behavioral_profiles = len(self.anomaly_engine.behavioral_profiles)
        response_playbooks = len(self.response_engine.response_playbooks)

        recent_responses = len([
            r for r in self.response_engine.response_history
            if (datetime.now() - r['timestamp']).seconds < 3600  # Last hour
        ])

        return {
            'ai_models_trained': ai_models,
            'ai_models_total': total_models,
            'behavioral_profiles': behavioral_profiles,
            'response_playbooks': response_playbooks,
            'threat_indicators': len(self.threat_indicators),
            'recent_responses': recent_responses,
            'system_health': "healthy" if ai_models > 0 else "degraded"
        }


# Funciones de conveniencia

async def demonstrate_advanced_threat_detection():
    """Demostrar advanced threat detection completo."""
    print("🛡️ Inicializando Advanced Threat Detection...")

    # Crear orchestrator
    orchestrator = ThreatDetectionOrchestrator()

    # Inicializar sistema
    await orchestrator.initialize_threat_detection()

    print("📊 Estado inicial del sistema:")
    status = orchestrator.get_detection_status()
    print(f"   Modelos IA entrenados: {status['ai_models_trained']}/{status['ai_models_total']}")
    print(f"   Perfiles behavioral: {status['behavioral_profiles']}")
    print(f"   Playbooks de respuesta: {status['response_playbooks']}")

    # Simular análisis de tráfico
    test_scenarios = [
        {
            'entity_id': 'user_alice',
            'metrics': {
                'login_attempts': 1,
                'session_duration': 1800,
                'data_accessed': 50,
                'api_calls': 100,
                'location_changes': 0,
                'device_changes': 0
            },
            'context': {'entity_type': 'user', 'source_ip': '192.168.1.100'}
        },
        {
            'entity_id': 'service_api',
            'metrics': {
                'requests_per_second': 1500,  # Alto - posible DDoS
                'bytes_transferred': 50000,
                'error_rate': 0.02,
                'connection_count': 200,
                'response_time': 0.5
            },
            'context': {'entity_type': 'service', 'source_ip': '10.0.0.1'}
        },
        {
            'entity_id': 'user_bob',
            'metrics': {
                'login_attempts': 15,  # Alto - posible brute force
                'session_duration': 300,
                'data_accessed': 10,
                'api_calls': 20,
                'location_changes': 3,
                'device_changes': 2
            },
            'context': {'entity_type': 'user', 'source_ip': '203.0.113.1'}
        }
    ]

    print("\n🔍 Analizando escenarios de amenaza:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"   Escenario {i}: {scenario['entity_id']}")

        result = await orchestrator.analyze_traffic(
            scenario['entity_id'],
            scenario['metrics'],
            scenario['context']
        )

        threats = result['threats_detected']
        responses = result['automated_responses']
        print(f"      Amenazas detectadas: {threats}")
        print(f"      Respuestas automáticas: {responses}")

        if threats > 0:
            print("      Detalles de amenazas:")
            for indicator in result['indicators']:
                print(f"         - {indicator['threat_type']} ({indicator['severity']}): {indicator['description']}")

    # Obtener inteligencia de amenazas
    print("\n🧠 Inteligencia de Amenazas:")
    intelligence = await orchestrator.get_threat_intelligence()
    print(f"   Amenazas en 24h: {intelligence['total_threats_24h']}")
    print(f"   Amenaza más común: {intelligence.get('most_common_threat', 'Ninguna')}")
    print(f"   Conteo por severidad: {intelligence['severity_counts']}")

    # Mostrar amenazas recientes
    if intelligence['recent_threats']:
        print("   Amenazas recientes:")
        for threat in intelligence['recent_threats'][:3]:
            print(f"      - {threat['threat_type']} ({threat['severity']}): {threat['description']}")

    # Status final
    print("\n📈 Status Final de Threat Detection:")
    final_status = orchestrator.get_detection_status()
    print(f"   Salud del sistema: {final_status['system_health']}")
    print(f"   Indicadores de amenaza: {final_status['threat_indicators']}")
    print(f"   Respuestas recientes: {final_status['recent_responses']}")

    print("✅ Advanced Threat Detection demostrado correctamente")

    return orchestrator


if __name__ == "__main__":
    asyncio.run(demonstrate_advanced_threat_detection())