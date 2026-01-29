"""
Sistema de monitoreo de modelos con alertas para Ailoos.
Monitorea métricas de modelos en tiempo real con TimescaleDB y alertas automáticas.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import psycopg2
import psycopg2.extras
import requests
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelMetrics:
    """Métricas recolectadas de un modelo."""
    model_id: str
    timestamp: datetime
    accuracy: float
    latency_ms: float
    drift_score: float
    throughput: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    prediction_count: int


@dataclass
class AlertConfig:
    """Configuración de alertas para modelos."""
    alertmanager_url: str = "http://localhost:9093/api/v2/alerts"
    accuracy_drop_threshold: float = 0.05  # 5% drop
    latency_spike_threshold: float = 100.0  # 100ms spike
    drift_detection_threshold: float = 0.1  # 0.1 drift score
    cooldown_minutes: int = 5


class ModelMonitor:
    """
    Monitor avanzado de modelos con métricas continuas, alertas y análisis predictivo.

    Características:
    - Monitoreo continuo de cientos de modelos concurrentemente
    - Almacenamiento en TimescaleDB para series de tiempo
    - Alertas automáticas vía AlertManager
    - Análisis de tendencias y predicción de fallos
    - Optimización para alta concurrencia
    """

    def __init__(self,
                 timescale_db_url: str = "postgresql://user:password@localhost/ailoos_monitoring",
                 alert_config: AlertConfig = None,
                 monitoring_interval_seconds: int = 300):  # 5 minutos

        self.timescale_db_url = timescale_db_url
        self.alert_config = alert_config or AlertConfig()
        self.monitoring_interval = monitoring_interval_seconds

        # Estado del monitor
        self.monitoring_active = False
        self.model_tasks: Dict[str, asyncio.Task] = {}
        self.active_models: Dict[str, Dict[str, Any]] = {}

        # Caché para análisis
        self.metrics_cache: Dict[str, List[ModelMetrics]] = {}
        self.cache_size = 1000  # Mantener últimas 1000 métricas por modelo

        # Conexión a DB
        self.db_connection = None

        # Modelos de predicción
        self.prediction_models: Dict[str, LinearRegression] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        logger.info("ModelMonitor inicializado", extra={
            'timescale_url': timescale_db_url.replace('password', '***'),
            'monitoring_interval': monitoring_interval_seconds
        })

    async def start_monitoring(self):
        """Iniciar monitoreo continuo de todos los modelos registrados."""
        if self.monitoring_active:
            logger.warning("Monitoreo ya está activo")
            return

        self.monitoring_active = True
        logger.info("Iniciando monitoreo de modelos")

        # Conectar a TimescaleDB
        await self._connect_db()

        # Crear tabla si no existe
        await self._create_metrics_table()

        # Iniciar tarea principal de monitoreo
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Detener monitoreo de todos los modelos."""
        self.monitoring_active = False

        # Cancelar todas las tareas
        for task in self.model_tasks.values():
            task.cancel()

        self.model_tasks.clear()

        # Cerrar conexión DB
        if self.db_connection:
            self.db_connection.close()

        logger.info("Monitoreo de modelos detenido")

    def register_model(self, model_id: str, model_info: Dict[str, Any]):
        """Registrar un modelo para monitoreo."""
        self.active_models[model_id] = model_info
        self.metrics_cache[model_id] = []

        logger.info(f"Modelo registrado para monitoreo: {model_id}", extra={
            'model_id': model_id,
            'model_info': model_info
        })

    def unregister_model(self, model_id: str):
        """Remover un modelo del monitoreo."""
        if model_id in self.active_models:
            del self.active_models[model_id]

        if model_id in self.model_tasks:
            self.model_tasks[model_id].cancel()
            del self.model_tasks[model_id]

        if model_id in self.metrics_cache:
            del self.metrics_cache[model_id]

        logger.info(f"Modelo removido del monitoreo: {model_id}")

    async def monitor_model_performance(self, model_id: str) -> ModelMetrics:
        """
        Recolectar métricas continuas de un modelo específico.

        Args:
            model_id: ID del modelo a monitorear

        Returns:
            ModelMetrics: Métricas recolectadas
        """
        try:
            # Simular recolección de métricas (en implementación real, conectar con el modelo)
            metrics = await self._collect_model_metrics(model_id)

            # Almacenar en TimescaleDB
            await self._store_metrics(metrics)

            # Actualizar caché
            self._update_cache(model_id, metrics)

            # Verificar alertas
            await self._check_alerts(metrics)

            # Entrenar modelo predictivo si hay suficientes datos
            if len(self.metrics_cache[model_id]) > 50:
                await self._train_prediction_model(model_id)

            logger.debug(f"Métricas recolectadas para {model_id}", extra={
                'model_id': model_id,
                'accuracy': metrics.accuracy,
                'latency': metrics.latency_ms,
                'drift': metrics.drift_score
            })

            return metrics

        except Exception as e:
            logger.error(f"Error monitoreando modelo {model_id}: {e}", extra={
                'model_id': model_id,
                'error': str(e)
            })
            raise

    async def _collect_model_metrics(self, model_id: str) -> ModelMetrics:
        """Recolectar métricas del modelo (implementación simulada)."""
        # En implementación real, esto se conectaría con el endpoint del modelo
        # o usaría métricas de Prometheus/infraestructura

        # Simulación de métricas realistas
        import random

        base_accuracy = self.active_models.get(model_id, {}).get('baseline_accuracy', 0.85)
        accuracy = base_accuracy + random.uniform(-0.05, 0.02)  # Pequeña variación

        latency = random.uniform(50, 200)  # 50-200ms
        drift_score = random.uniform(0, 0.3)  # 0-0.3 drift score
        throughput = random.uniform(100, 1000)  # requests/second
        memory_usage = random.uniform(500, 2000)  # MB
        cpu_usage = random.uniform(10, 80)  # %
        error_rate = random.uniform(0, 0.05)  # 0-5%
        prediction_count = random.randint(1000, 10000)

        return ModelMetrics(
            model_id=model_id,
            timestamp=datetime.now(),
            accuracy=max(0, min(1, accuracy)),  # Clamp entre 0-1
            latency_ms=latency,
            drift_score=drift_score,
            throughput=throughput,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            error_rate=error_rate,
            prediction_count=prediction_count
        )

    async def _connect_db(self):
        """Conectar a TimescaleDB."""
        try:
            self.db_connection = psycopg2.connect(self.timescale_db_url)
            logger.info("Conectado a TimescaleDB")
        except Exception as e:
            logger.error(f"Error conectando a TimescaleDB: {e}")
            raise

    async def _create_metrics_table(self):
        """Crear tabla de métricas en TimescaleDB si no existe."""
        try:
            with self.db_connection.cursor() as cursor:
                # Crear tabla hypertable
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_metrics (
                        time TIMESTAMPTZ NOT NULL,
                        model_id TEXT NOT NULL,
                        accuracy DOUBLE PRECISION,
                        latency_ms DOUBLE PRECISION,
                        drift_score DOUBLE PRECISION,
                        throughput DOUBLE PRECISION,
                        memory_usage_mb DOUBLE PRECISION,
                        cpu_usage_percent DOUBLE PRECISION,
                        error_rate DOUBLE PRECISION,
                        prediction_count INTEGER
                    );

                    -- Convertir a hypertable si no lo es
                    SELECT create_hypertable('model_metrics', 'time', if_not_exists => TRUE);

                    -- Crear índices
                    CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON model_metrics (model_id);
                    CREATE INDEX IF NOT EXISTS idx_model_metrics_time ON model_metrics (time DESC);
                """)

                self.db_connection.commit()
                logger.info("Tabla model_metrics creada/verificada en TimescaleDB")

        except Exception as e:
            logger.error(f"Error creando tabla en TimescaleDB: {e}")
            raise

    async def _store_metrics(self, metrics: ModelMetrics):
        """Almacenar métricas en TimescaleDB."""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO model_metrics (
                        time, model_id, accuracy, latency_ms, drift_score,
                        throughput, memory_usage_mb, cpu_usage_percent,
                        error_rate, prediction_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    metrics.timestamp, metrics.model_id, metrics.accuracy,
                    metrics.latency_ms, metrics.drift_score, metrics.throughput,
                    metrics.memory_usage_mb, metrics.cpu_usage_percent,
                    metrics.error_rate, metrics.prediction_count
                ))

                self.db_connection.commit()

        except Exception as e:
            logger.error(f"Error almacenando métricas: {e}")
            # Reintentar conexión si falló
            await self._reconnect_db()

    async def _reconnect_db(self):
        """Reconectar a la base de datos."""
        try:
            if self.db_connection:
                self.db_connection.close()
            await self._connect_db()
        except Exception as e:
            logger.error(f"Error reconectando a DB: {e}")

    def _update_cache(self, model_id: str, metrics: ModelMetrics):
        """Actualizar caché de métricas."""
        cache = self.metrics_cache[model_id]
        cache.append(metrics)

        # Mantener tamaño máximo del caché
        if len(cache) > self.cache_size:
            cache.pop(0)

    async def _check_alerts(self, metrics: ModelMetrics):
        """Verificar condiciones de alerta."""
        alerts = []

        # Verificar accuracy drop
        if await self._check_accuracy_drop(metrics):
            alerts.append({
                'alertname': 'accuracy_drop',
                'severity': 'warning',
                'description': f'Accuracy dropped by >{self.alert_config.accuracy_drop_threshold*100:.1f}%',
                'model_id': metrics.model_id,
                'value': metrics.accuracy
            })

        # Verificar latency spike
        if await self._check_latency_spike(metrics):
            alerts.append({
                'alertname': 'latency_spike',
                'severity': 'warning',
                'description': f'Latency spiked by >{self.alert_config.latency_spike_threshold}ms',
                'model_id': metrics.model_id,
                'value': metrics.latency_ms
            })

        # Verificar drift detection
        if metrics.drift_score > self.alert_config.drift_detection_threshold:
            alerts.append({
                'alertname': 'drift_detection',
                'severity': 'warning',
                'description': f'Drift score > {self.alert_config.drift_detection_threshold}',
                'model_id': metrics.model_id,
                'value': metrics.drift_score
            })

        # Enviar alertas
        for alert in alerts:
            await self._send_alert(alert)

    async def _check_accuracy_drop(self, metrics: ModelMetrics) -> bool:
        """Verificar si hay una caída significativa en accuracy."""
        cache = self.metrics_cache.get(metrics.model_id, [])
        if len(cache) < 10:
            return False

        # Calcular accuracy promedio de las últimas 10 métricas vs actual
        recent_accuracies = [m.accuracy for m in cache[-10:]]
        avg_recent = np.mean(recent_accuracies)
        drop = avg_recent - metrics.accuracy

        return drop > self.alert_config.accuracy_drop_threshold

    async def _check_latency_spike(self, metrics: ModelMetrics) -> bool:
        """Verificar si hay un spike en latency."""
        cache = self.metrics_cache.get(metrics.model_id, [])
        if len(cache) < 5:
            return False

        # Calcular latency promedio de las últimas 5 métricas
        recent_latencies = [m.latency_ms for m in cache[-5:]]
        avg_recent = np.mean(recent_latencies)

        return metrics.latency_ms > avg_recent + self.alert_config.latency_spike_threshold

    async def _send_alert(self, alert: Dict[str, Any]):
        """Enviar alerta a AlertManager."""
        try:
            payload = [{
                'labels': {
                    'alertname': alert['alertname'],
                    'severity': alert['severity'],
                    'model_id': alert['model_id'],
                    'instance': 'model_monitor'
                },
                'annotations': {
                    'description': alert['description'],
                    'value': str(alert['value']),
                    'timestamp': datetime.now().isoformat()
                },
                'startsAt': datetime.now().isoformat()
            }]

            response = requests.post(
                self.alert_config.alertmanager_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.warning(f"Alerta enviada: {alert['alertname']} para {alert['model_id']}")
            else:
                logger.error(f"Error enviando alerta: {response.status_code}")

        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.monitoring_active:
            try:
                # Monitorear todos los modelos concurrentemente
                tasks = []
                for model_id in list(self.active_models.keys()):
                    task = asyncio.create_task(self.monitor_model_performance(model_id))
                    tasks.append(task)

                # Esperar a que todos terminen
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Esperar al siguiente intervalo
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                await asyncio.sleep(30)  # Esperar antes de reintentar

    # Métodos auxiliares para análisis de tendencias

    async def analyze_trends(self, model_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Analizar tendencias en las métricas del modelo.

        Args:
            model_id: ID del modelo
            hours: Horas de historial a analizar

        Returns:
            Dict con análisis de tendencias
        """
        try:
            # Obtener datos históricos
            metrics = await self._get_historical_metrics(model_id, hours)

            if not metrics:
                return {'error': 'No hay suficientes datos históricos'}

            # Convertir a DataFrame para análisis
            df = pd.DataFrame([asdict(m) for m in metrics])
            df['time'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('time').sort_index()

            # Análisis de tendencias
            trends = {}

            for metric in ['accuracy', 'latency_ms', 'drift_score', 'error_rate']:
                if metric in df.columns:
                    # Tendencia lineal
                    if len(df) > 10:
                        slope = self._calculate_trend_slope(df[metric])
                        trends[metric] = {
                            'current_value': df[metric].iloc[-1],
                            'trend_slope': slope,
                            'trend_direction': 'increasing' if slope > 0 else 'decreasing',
                            'volatility': df[metric].std(),
                            'min_value': df[metric].min(),
                            'max_value': df[metric].max()
                        }

            return {
                'model_id': model_id,
                'analysis_period_hours': hours,
                'data_points': len(metrics),
                'trends': trends,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analizando tendencias para {model_id}: {e}")
            return {'error': str(e)}

    def _calculate_trend_slope(self, series: pd.Series) -> float:
        """Calcular la pendiente de tendencia usando regresión lineal."""
        try:
            X = np.arange(len(series)).reshape(-1, 1)
            y = series.values

            model = LinearRegression()
            model.fit(X, y)

            return model.coef_[0]
        except Exception:
            return 0.0

    # Métodos auxiliares para predicción de fallos

    async def predict_failures(self, model_id: str, prediction_hours: int = 24) -> Dict[str, Any]:
        """
        Predecir posibles fallos del modelo usando machine learning.

        Args:
            model_id: ID del modelo
            prediction_hours: Horas hacia adelante para predecir

        Returns:
            Dict con predicciones de fallos
        """
        try:
            cache = self.metrics_cache.get(model_id, [])
            if len(cache) < 50:
                return {'error': 'Insuficientes datos para predicción (necesita al menos 50 puntos)'}

            # Preparar datos
            df = pd.DataFrame([asdict(m) for m in cache])
            df['time'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('time').sort_index()

            # Características para predicción
            features = ['accuracy', 'latency_ms', 'drift_score', 'error_rate', 'cpu_usage_percent', 'memory_usage_mb']

            # Predecir cada métrica
            predictions = {}
            for metric in features:
                if metric in df.columns and len(df) > 20:
                    pred_value, confidence = self._predict_metric(df[metric], prediction_hours)
                    predictions[metric] = {
                        'predicted_value': pred_value,
                        'confidence': confidence,
                        'current_value': df[metric].iloc[-1],
                        'prediction_hours': prediction_hours
                    }

            # Calcular riesgo de fallo compuesto
            failure_risk = self._calculate_failure_risk(predictions)

            return {
                'model_id': model_id,
                'predictions': predictions,
                'failure_risk_score': failure_risk,
                'risk_level': self._classify_risk_level(failure_risk),
                'recommendations': self._generate_recommendations(predictions, failure_risk),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error prediciendo fallos para {model_id}: {e}")
            return {'error': str(e)}

    def _predict_metric(self, series: pd.Series, hours_ahead: int) -> Tuple[float, float]:
        """Predecir valor futuro de una métrica usando regresión."""
        try:
            # Usar últimas 24 horas de datos
            recent_data = series.last('24H') if hasattr(series, 'last') else series.tail(100)

            if len(recent_data) < 10:
                return series.iloc[-1], 0.5

            # Preparar datos para regresión
            X = np.arange(len(recent_data)).reshape(-1, 1)
            y = recent_data.values

            # Escalar datos
            scaler = StandardScaler()
            y_scaled = scaler.fit_transform(y.reshape(-1, 1)).flatten()

            # Entrenar modelo
            model = LinearRegression()
            model.fit(X, y_scaled)

            # Predecir punto futuro
            future_point = np.array([[len(recent_data) + hours_ahead]])
            prediction_scaled = model.predict(future_point)[0]

            # Desescalar
            prediction = scaler.inverse_transform([[prediction_scaled]])[0][0]

            # Calcular confianza (basada en R²)
            r_squared = model.score(X, y_scaled)
            confidence = max(0, min(1, r_squared))

            return float(prediction), float(confidence)

        except Exception as e:
            logger.warning(f"Error prediciendo métrica: {e}")
            return series.iloc[-1], 0.5

    def _calculate_failure_risk(self, predictions: Dict[str, Any]) -> float:
        """Calcular riesgo compuesto de fallo."""
        risk_factors = []

        # Accuracy degradation
        if 'accuracy' in predictions:
            pred = predictions['accuracy']
            if pred['predicted_value'] < pred['current_value'] * 0.9:  # 10% drop
                risk_factors.append(0.3)

        # Latency increase
        if 'latency_ms' in predictions:
            pred = predictions['latency_ms']
            if pred['predicted_value'] > pred['current_value'] * 1.5:  # 50% increase
                risk_factors.append(0.25)

        # Drift increase
        if 'drift_score' in predictions:
            pred = predictions['drift_score']
            if pred['predicted_value'] > 0.2:
                risk_factors.append(0.2)

        # Error rate increase
        if 'error_rate' in predictions:
            pred = predictions['error_rate']
            if pred['predicted_value'] > pred['current_value'] * 2:
                risk_factors.append(0.15)

        # Resource usage
        if 'cpu_usage_percent' in predictions:
            pred = predictions['cpu_usage_percent']
            if pred['predicted_value'] > 90:
                risk_factors.append(0.1)

        return min(1.0, sum(risk_factors))

    def _classify_risk_level(self, risk_score: float) -> str:
        """Clasificar nivel de riesgo."""
        if risk_score >= 0.7:
            return 'CRITICAL'
        elif risk_score >= 0.4:
            return 'HIGH'
        elif risk_score >= 0.2:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _generate_recommendations(self, predictions: Dict[str, Any], risk_score: float) -> List[str]:
        """Generar recomendaciones basadas en predicciones."""
        recommendations = []

        if risk_score >= 0.7:
            recommendations.append("🚨 RIESGO CRÍTICO: Considere reentrenar el modelo inmediatamente")
            recommendations.append("📞 Alertar al equipo de ML para intervención urgente")

        elif risk_score >= 0.4:
            recommendations.append("⚠️ RIESGO ALTO: Monitorear closely las próximas horas")
            recommendations.append("🔄 Considerar actualización del modelo en las próximas 24h")

        # Recomendaciones específicas por métrica
        if 'accuracy' in predictions:
            pred = predictions['accuracy']
            if pred['predicted_value'] < pred['current_value'] * 0.95:
                recommendations.append("📉 Accuracy decay detectado: Revisar calidad de datos de entrada")

        if 'latency_ms' in predictions:
            pred = predictions['latency_ms']
            if pred['predicted_value'] > pred['current_value'] * 1.3:
                recommendations.append("⏱️ Latency increase: Optimizar infraestructura o reducir carga")

        if 'drift_score' in predictions:
            pred = predictions['drift_score']
            if pred['predicted_value'] > 0.15:
                recommendations.append("🔄 Data drift detectado: Recolectar nuevos datos de entrenamiento")

        return recommendations

    async def _get_historical_metrics(self, model_id: str, hours: int) -> List[ModelMetrics]:
        """Obtener métricas históricas de TimescaleDB."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM model_metrics
                    WHERE model_id = %s AND time >= %s
                    ORDER BY time DESC
                """, (model_id, cutoff_time))

                rows = cursor.fetchall()

                metrics = []
                for row in rows:
                    metrics.append(ModelMetrics(
                        model_id=row['model_id'],
                        timestamp=row['time'],
                        accuracy=row['accuracy'],
                        latency_ms=row['latency_ms'],
                        drift_score=row['drift_score'],
                        throughput=row['throughput'],
                        memory_usage_mb=row['memory_usage_mb'],
                        cpu_usage_percent=row['cpu_usage_percent'],
                        error_rate=row['error_rate'],
                        prediction_count=row['prediction_count']
                    ))

                return metrics

        except Exception as e:
            logger.error(f"Error obteniendo métricas históricas: {e}")
            return []

    async def _train_prediction_model(self, model_id: str):
        """Entrenar modelo de predicción para el modelo específico."""
        try:
            cache = self.metrics_cache.get(model_id, [])
            if len(cache) < 100:
                return

            # Preparar datos de entrenamiento
            df = pd.DataFrame([asdict(m) for m in cache[-200:]])  # Usar últimas 200 métricas
            df['time'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('time').sort_index()

            # Características: usar valores anteriores para predecir siguientes
            features = ['accuracy', 'latency_ms', 'drift_score', 'error_rate']
            target_feature = 'accuracy'  # Predecir accuracy como ejemplo

            if len(df) < 20:
                return

            # Crear secuencia de predicción (usar últimos N valores para predecir siguiente)
            sequence_length = 10
            X, y = [], []

            for i in range(len(df) - sequence_length):
                X.append(df[features].iloc[i:i+sequence_length].values.flatten())
                y.append(df[target_feature].iloc[i+sequence_length])

            if len(X) < 10:
                return

            X = np.array(X)
            y = np.array(y)

            # Entrenar modelo
            model = LinearRegression()
            model.fit(X, y)

            # Guardar modelo entrenado
            self.prediction_models[model_id] = model

            logger.debug(f"Modelo de predicción entrenado para {model_id}")

        except Exception as e:
            logger.warning(f"Error entrenando modelo de predicción para {model_id}: {e}")

    # Métodos públicos adicionales

    async def get_model_health_status(self, model_id: str) -> Dict[str, Any]:
        """Obtener estado de salud completo del modelo."""
        try:
            # Obtener últimas métricas
            cache = self.metrics_cache.get(model_id, [])
            if not cache:
                return {'error': 'No hay métricas disponibles'}

            latest = cache[-1]

            # Análisis de tendencias (últimas 24h)
            trends = await self.analyze_trends(model_id, 24)

            # Predicción de fallos (próximas 24h)
            predictions = await self.predict_failures(model_id, 24)

            return {
                'model_id': model_id,
                'current_metrics': asdict(latest),
                'trends': trends,
                'predictions': predictions,
                'overall_health': self._calculate_overall_health(latest, trends, predictions),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error obteniendo health status para {model_id}: {e}")
            return {'error': str(e)}

    def _calculate_overall_health(self, metrics: ModelMetrics, trends: Dict, predictions: Dict) -> str:
        """Calcular salud general del modelo."""
        score = 0

        # Accuracy (40% del score)
        if metrics.accuracy > 0.9:
            score += 40
        elif metrics.accuracy > 0.8:
            score += 30
        elif metrics.accuracy > 0.7:
            score += 20

        # Latency (20% del score)
        if metrics.latency_ms < 100:
            score += 20
        elif metrics.latency_ms < 200:
            score += 15
        elif metrics.latency_ms < 500:
            score += 10

        # Drift (20% del score)
        if metrics.drift_score < 0.1:
            score += 20
        elif metrics.drift_score < 0.2:
            score += 15
        elif metrics.drift_score < 0.3:
            score += 10

        # Error rate (10% del score)
        if metrics.error_rate < 0.01:
            score += 10
        elif metrics.error_rate < 0.05:
            score += 7
        elif metrics.error_rate < 0.1:
            score += 4

        # Predicciones (10% del score)
        if 'failure_risk_score' in predictions:
            risk = predictions['failure_risk_score']
            if risk < 0.2:
                score += 10
            elif risk < 0.4:
                score += 7
            elif risk < 0.6:
                score += 4

        # Clasificar salud
        if score >= 80:
            return 'EXCELLENT'
        elif score >= 60:
            return 'GOOD'
        elif score >= 40:
            return 'FAIR'
        elif score >= 20:
            return 'POOR'
        else:
            return 'CRITICAL'

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de monitoreo."""
        return {
            'monitoring_active': self.monitoring_active,
            'active_models_count': len(self.active_models),
            'total_metrics_collected': sum(len(cache) for cache in self.metrics_cache.values()),
            'models_with_predictions': len(self.prediction_models),
            'db_connection_status': 'CONNECTED' if self.db_connection else 'DISCONNECTED',
            'cache_size': sum(len(cache) for cache in self.metrics_cache.values()),
            'timestamp': datetime.now().isoformat()
        }


# Función de conveniencia para iniciar monitoreo
async def start_model_monitoring(
    timescale_url: str = "postgresql://user:password@localhost/ailoos_monitoring",
    alertmanager_url: str = "http://localhost:9093/api/v2/alerts",
    monitoring_interval: int = 300
) -> ModelMonitor:
    """Función de conveniencia para iniciar el sistema de monitoreo de modelos."""
    alert_config = AlertConfig(alertmanager_url=alertmanager_url)
    monitor = ModelMonitor(
        timescale_db_url=timescale_url,
        alert_config=alert_config,
        monitoring_interval_seconds=monitoring_interval
    )

    await monitor.start_monitoring()
    return monitor


# Ejemplo de uso
if __name__ == "__main__":
    async def demo():
        # Crear monitor
        monitor = ModelMonitor()

        # Registrar modelos de ejemplo
        monitor.register_model("model_001", {
            "name": "Fraud Detection Model",
            "version": "1.2.3",
            "baseline_accuracy": 0.92
        })

        monitor.register_model("model_002", {
            "name": "Recommendation Engine",
            "version": "2.1.0",
            "baseline_accuracy": 0.85
        })

        # Iniciar monitoreo
        await monitor.start_monitoring()

        # Monitorear por un tiempo
        await asyncio.sleep(10)

        # Obtener análisis
        for model_id in ["model_001", "model_002"]:
            health = await monitor.get_model_health_status(model_id)
            print(f"Health status for {model_id}: {health.get('overall_health', 'UNKNOWN')}")

            trends = await monitor.analyze_trends(model_id, 1)  # Última hora
            print(f"Trends for {model_id}: {len(trends.get('trends', {}))} metrics analyzed")

            predictions = await monitor.predict_failures(model_id, 6)  # Próximas 6 horas
            print(f"Predictions for {model_id}: Risk level {predictions.get('risk_level', 'UNKNOWN')}")

        # Detener monitoreo
        await monitor.stop_monitoring()

        print("Demo completado")

    asyncio.run(demo())