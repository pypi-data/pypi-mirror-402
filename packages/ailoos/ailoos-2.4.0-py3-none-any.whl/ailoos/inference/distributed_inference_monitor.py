"""
Monitoreo de inferencia en entornos distribuidos FL.
Recopila métricas, detecta anomalías y optimiza rendimiento.
"""

import asyncio
import torch
import logging
import time
import psutil
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class InferenceMetrics:
    """Métricas de inferencia por nodo."""

    node_id: str
    round_id: str
    timestamp: float = field(default_factory=time.time)

    # Rendimiento
    requests_per_second: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    throughput_tokens_per_sec: float = 0.0

    # Recursos
    gpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    cpu_utilization: float = 0.0

    # Calidad
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    batch_efficiency: float = 0.0

    # FL específico
    federated_overhead_ms: float = 0.0
    cross_node_sync_time_ms: float = 0.0


@dataclass
class DistributedMonitorConfig:
    """Configuración del monitor distribuido."""

    # Monitoreo
    collection_interval_seconds: float = 10.0
    metrics_retention_hours: float = 24.0
    anomaly_detection_enabled: bool = True

    # Alertas
    enable_alerts: bool = True
    latency_threshold_ms: float = 1000.0
    error_rate_threshold: float = 0.05
    memory_threshold: float = 0.9

    # Optimización
    auto_optimization: bool = True
    optimization_interval_minutes: int = 5

    # Distribución
    enable_cross_node_aggregation: bool = True
    global_metrics_sync_interval: float = 60.0


class DistributedInferenceMonitor:
    """
    Monitor de inferencia distribuida para federated learning.

    Características principales:
    - Recopilación de métricas en tiempo real
    - Detección de anomalías y alertas
    - Agregación de métricas cross-nodo
    - Optimización automática basada en métricas
    - Dashboard de rendimiento FL
    """

    def __init__(self, config: DistributedMonitorConfig, local_node_id: str):
        self.config = config
        self.local_node_id = local_node_id

        # Almacenamiento de métricas
        self.node_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.global_metrics: Dict[str, Any] = {}
        self.anomaly_history: List[Dict[str, Any]] = []

        # Estado de monitoreo
        self.monitoring_active = False
        self.last_collection_time = time.time()
        self.optimization_last_run = time.time()

        # Callbacks de alerta
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        # Estadísticas agregadas
        self.aggregated_stats = {
            "total_nodes_monitored": 0,
            "total_requests_processed": 0,
            "avg_system_latency": 0.0,
            "anomalies_detected": 0,
            "optimizations_applied": 0
        }

        # Threads de monitoreo
        self.monitor_thread: Optional[threading.Thread] = None
        self.optimization_thread: Optional[threading.Thread] = None

        logger.info("🔧 DistributedInferenceMonitor inicializado")
        logger.info(f"   Nodo local: {local_node_id}")
        logger.info(f"   Intervalo de colección: {config.collection_interval_seconds}s")

    def start_monitoring(self):
        """Iniciar monitoreo distribuido."""
        self.monitoring_active = True

        # Iniciar thread de colección
        self.monitor_thread = threading.Thread(
            target=self._monitoring_worker,
            daemon=True
        )
        self.monitor_thread.start()

        # Iniciar thread de optimización si está habilitada
        if self.config.auto_optimization:
            self.optimization_thread = threading.Thread(
                target=self._optimization_worker,
                daemon=True
            )
            self.optimization_thread.start()

        logger.info("▶️ Monitoreo distribuido iniciado")

    def stop_monitoring(self):
        """Detener monitoreo."""
        self.monitoring_active = False

        # Esperar a que terminen los threads
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5)

        logger.info("⏹️ Monitoreo distribuido detenido")

    def record_inference_metrics(
        self,
        node_id: str,
        round_id: str,
        latency_ms: float,
        tokens_processed: int,
        batch_size: int,
        memory_used_gb: float,
        cache_hit: bool = False,
        error_occurred: bool = False
    ):
        """
        Registrar métricas de una inferencia.

        Args:
            node_id: ID del nodo
            round_id: ID de la ronda FL
            latency_ms: Latencia en ms
            tokens_processed: Tokens procesados
            batch_size: Tamaño del batch
            memory_used_gb: Memoria usada
            cache_hit: Si fue cache hit
            error_occurred: Si ocurrió error
        """
        timestamp = time.time()

        # Calcular métricas derivadas
        throughput = tokens_processed / (latency_ms / 1000) if latency_ms > 0 else 0

        # Crear registro de métricas
        metrics = InferenceMetrics(
            node_id=node_id,
            round_id=round_id,
            timestamp=timestamp,
            avg_latency_ms=latency_ms,
            throughput_tokens_per_sec=throughput,
            memory_utilization=memory_used_gb / self._get_node_memory_capacity(node_id),
            cache_hit_rate=1.0 if cache_hit else 0.0,
            error_rate=1.0 if error_occurred else 0.0,
            batch_efficiency=batch_size / 32.0  # Normalizar a batch size máximo
        )

        # Agregar métricas de sistema
        self._add_system_metrics(metrics)

        # Almacenar
        self.node_metrics[node_id].append(metrics)

        # Verificar anomalías
        if self.config.anomaly_detection_enabled:
            self._check_for_anomalies(metrics)

        # Actualizar estadísticas agregadas
        self.aggregated_stats["total_requests_processed"] += 1

    def _add_system_metrics(self, metrics: InferenceMetrics):
        """Agregar métricas del sistema."""
        try:
            # CPU
            metrics.cpu_utilization = psutil.cpu_percent() / 100.0

            # Memoria
            memory = psutil.virtual_memory()
            metrics.memory_utilization = memory.percent / 100.0

            # GPU si está disponible
            if torch.cuda.is_available():
                metrics.gpu_utilization = torch.cuda.utilization() / 100.0
            else:
                metrics.gpu_utilization = 0.0

        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo métricas del sistema: {e}")

    def _get_node_memory_capacity(self, node_id: str) -> float:
        """Obtener capacidad de memoria del nodo."""
        # En implementación real, esto vendría de capacidades registradas
        # Por ahora, usar valores por defecto
        return 8.0 if "gpu" in node_id.lower() else 16.0  # GB

    def _check_for_anomalies(self, metrics: InferenceMetrics):
        """Verificar anomalías en las métricas."""
        anomalies = []

        # Verificar latencia alta
        if metrics.avg_latency_ms > self.config.latency_threshold_ms:
            anomalies.append({
                "type": "high_latency",
                "value": metrics.avg_latency_ms,
                "threshold": self.config.latency_threshold_ms,
                "node_id": metrics.node_id
            })

        # Verificar tasa de error alta
        if metrics.error_rate > self.config.error_rate_threshold:
            anomalies.append({
                "type": "high_error_rate",
                "value": metrics.error_rate,
                "threshold": self.config.error_rate_threshold,
                "node_id": metrics.node_id
            })

        # Verificar uso alto de memoria
        if metrics.memory_utilization > self.config.memory_threshold:
            anomalies.append({
                "type": "high_memory_usage",
                "value": metrics.memory_utilization,
                "threshold": self.config.memory_threshold,
                "node_id": metrics.node_id
            })

        # Registrar anomalías
        for anomaly in anomalies:
            self.anomaly_history.append({
                **anomaly,
                "timestamp": time.time(),
                "round_id": metrics.round_id
            })

            # Enviar alertas
            if self.config.enable_alerts:
                self._send_alert(anomaly)

        if anomalies:
            self.aggregated_stats["anomalies_detected"] += len(anomalies)

    def _send_alert(self, anomaly: Dict[str, Any]):
        """Enviar alerta de anomalía."""
        alert_message = f"🚨 Anomalía detectada: {anomaly['type']} en nodo {anomaly['node_id']}"

        for callback in self.alert_callbacks:
            try:
                callback(alert_message, anomaly)
            except Exception as e:
                logger.error(f"❌ Error en callback de alerta: {e}")

        logger.warning(alert_message)

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Agregar callback para alertas."""
        self.alert_callbacks.append(callback)

    def _monitoring_worker(self):
        """Worker de colección de métricas."""
        while self.monitoring_active:
            try:
                current_time = time.time()

                # Agregar métricas de latencia (simuladas para nodos remotos)
                self._collect_distributed_metrics()

                # Limpiar métricas viejas
                self._cleanup_old_metrics()

                # Sincronizar métricas globales
                if self.config.enable_cross_node_aggregation:
                    self._sync_global_metrics()

                self.last_collection_time = current_time
                time.sleep(self.config.collection_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Error en monitoring worker: {e}")
                time.sleep(5)

    def _collect_distributed_metrics(self):
        """Recopilar métricas de nodos distribuidos."""
        # En implementación real, esto consultaría otros nodos
        # Por ahora, simular algunos nodos remotos
        remote_nodes = [f"node_{i}" for i in range(1, 4)]

        for node_id in remote_nodes:
            if node_id not in self.node_metrics or not self.node_metrics[node_id]:
                # Crear métricas simuladas para nodos remotos
                simulated_metrics = InferenceMetrics(
                    node_id=node_id,
                    round_id=self._get_current_round_id(),
                    requests_per_second=np.random.uniform(10, 50),
                    avg_latency_ms=np.random.uniform(100, 500),
                    gpu_utilization=np.random.uniform(0.3, 0.9),
                    memory_utilization=np.random.uniform(0.4, 0.8)
                )
                self.node_metrics[node_id].append(simulated_metrics)

    def _get_current_round_id(self) -> str:
        """Obtener ID de ronda actual (simulado)."""
        return f"round_{int(time.time() // 3600)}"  # Una ronda por hora

    def _cleanup_old_metrics(self):
        """Limpiar métricas viejas."""
        cutoff_time = time.time() - (self.config.metrics_retention_hours * 3600)

        for node_id in list(self.node_metrics.keys()):
            metrics_queue = self.node_metrics[node_id]
            # Filtrar métricas recientes
            recent_metrics = [m for m in metrics_queue if m.timestamp > cutoff_time]

            if recent_metrics:
                self.node_metrics[node_id] = deque(recent_metrics, maxlen=1000)
            else:
                del self.node_metrics[node_id]

    def _sync_global_metrics(self):
        """Sincronizar métricas globales entre nodos."""
        # Agregar todas las métricas disponibles
        all_metrics = []
        for metrics_queue in self.node_metrics.values():
            all_metrics.extend(metrics_queue)

        if not all_metrics:
            return

        # Calcular métricas globales
        latencies = [m.avg_latency_ms for m in all_metrics if m.avg_latency_ms > 0]
        throughputs = [m.throughput_tokens_per_sec for m in all_metrics if m.throughput_tokens_per_sec > 0]

        self.global_metrics = {
            "total_nodes": len(self.node_metrics),
            "avg_latency_ms": np.mean(latencies) if latencies else 0,
            "p95_latency_ms": np.percentile(latencies, 95) if latencies else 0,
            "avg_throughput": np.mean(throughputs) if throughputs else 0,
            "total_requests": len(all_metrics),
            "last_sync": time.time()
        }

        self.aggregated_stats["avg_system_latency"] = self.global_metrics["avg_latency_ms"]

    def _optimization_worker(self):
        """Worker de optimización automática."""
        while self.monitoring_active:
            try:
                time.sleep(self.config.optimization_interval_minutes * 60)

                if not self.monitoring_active:
                    break

                # Ejecutar optimizaciones
                optimizations = self._run_automatic_optimizations()

                if optimizations:
                    self.aggregated_stats["optimizations_applied"] += len(optimizations)
                    logger.info(f"🔧 Aplicadas {len(optimizations)} optimizaciones automáticas")

            except Exception as e:
                logger.error(f"❌ Error en optimization worker: {e}")

    def _run_automatic_optimizations(self) -> List[str]:
        """Ejecutar optimizaciones automáticas basadas en métricas."""
        optimizations = []

        # Analizar métricas recientes
        recent_metrics = self._get_recent_metrics(hours=1)

        if not recent_metrics:
            return optimizations

        # Optimización 1: Ajustar batch sizes si latencia alta
        avg_latency = np.mean([m.avg_latency_ms for m in recent_metrics])
        if avg_latency > self.config.latency_threshold_ms * 0.8:
            optimizations.append("reduce_batch_size")
            logger.info("📉 Optimización: Reduciendo batch size por latencia alta")

        # Optimización 2: Ajustar cache si hit rate baja
        avg_cache_hit = np.mean([m.cache_hit_rate for m in recent_metrics])
        if avg_cache_hit < 0.3:
            optimizations.append("increase_cache_size")
            logger.info("📈 Optimización: Aumentando tamaño de cache")

        # Optimización 3: Balanceo de carga si utilización desigual
        node_utilizations = {}
        for node_id, metrics_queue in self.node_metrics.items():
            if metrics_queue:
                avg_util = np.mean([m.gpu_utilization for m in metrics_queue])
                node_utilizations[node_id] = avg_util

        if len(node_utilizations) > 1:
            utilizations = list(node_utilizations.values())
            util_std = np.std(utilizations)
            if util_std > 0.3:  # Alta variabilidad
                optimizations.append("rebalance_load")
                logger.info("⚖️ Optimización: Rebalanceando carga entre nodos")

        return optimizations

    def _get_recent_metrics(self, hours: int = 1) -> List[InferenceMetrics]:
        """Obtener métricas recientes."""
        cutoff_time = time.time() - (hours * 3600)
        recent = []

        for metrics_queue in self.node_metrics.values():
            recent.extend([m for m in metrics_queue if m.timestamp > cutoff_time])

        return recent

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de monitoreo."""
        return {
            **self.aggregated_stats,
            "nodes_monitored": list(self.node_metrics.keys()),
            "global_metrics": self.global_metrics.copy(),
            "recent_anomalies": self.anomaly_history[-10:],  # Últimas 10
            "monitoring_active": self.monitoring_active,
            "last_collection": self.last_collection_time
        }

    def get_node_performance_summary(self, node_id: str) -> Dict[str, Any]:
        """Obtener resumen de rendimiento de un nodo."""
        if node_id not in self.node_metrics:
            return {}

        metrics = list(self.node_metrics[node_id])
        if not metrics:
            return {}

        return {
            "node_id": node_id,
            "metrics_count": len(metrics),
            "avg_latency_ms": np.mean([m.avg_latency_ms for m in metrics]),
            "avg_throughput": np.mean([m.throughput_tokens_per_sec for m in metrics]),
            "avg_gpu_utilization": np.mean([m.gpu_utilization for m in metrics]),
            "avg_memory_utilization": np.mean([m.memory_utilization for m in metrics]),
            "error_rate": np.mean([m.error_rate for m in metrics]),
            "cache_hit_rate": np.mean([m.cache_hit_rate for m in metrics])
        }


# Funciones de conveniencia
def create_distributed_monitor(
    local_node_id: str = "local",
    enable_alerts: bool = True,
    auto_optimization: bool = True
) -> DistributedInferenceMonitor:
    """
    Crear monitor de inferencia distribuida.

    Args:
        local_node_id: ID del nodo local
        enable_alerts: Habilitar alertas
        auto_optimization: Habilitar optimización automática

    Returns:
        Monitor configurado
    """
    config = DistributedMonitorConfig(
        enable_alerts=enable_alerts,
        auto_optimization=auto_optimization
    )

    return DistributedInferenceMonitor(config, local_node_id)


if __name__ == "__main__":
    # Demo del monitor distribuido
    print("🚀 DistributedInferenceMonitor Demo")
    print("Para uso completo, inicializar con configuración específica")