import time
import logging
from collections import deque
from statistics import mean, stdev

logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    """
    Clase para analizar métricas en tiempo real para despliegues canary.
    Recopila datos de rendimiento, calcula KPIs, detecta anomalías,
    compara versiones y genera alertas básicas.
    """

    def __init__(self, window_size=100, alert_thresholds=None):
        """
        Inicializa el analizador de métricas.

        :param window_size: Tamaño de la ventana deslizante para métricas.
        :param alert_thresholds: Diccionario con umbrales para alertas (e.g., {'latency': 200, 'error_rate': 0.05}).
        """
        self.window_size = window_size
        self.alert_thresholds = alert_thresholds or {'latency': 200, 'error_rate': 0.05}
        self.metrics = {
            'stable': {
                'latencies': deque(maxlen=window_size),
                'errors': 0,
                'total_requests': 0,
                'timestamps': deque(maxlen=window_size)
            },
            'canary': {
                'latencies': deque(maxlen=window_size),
                'errors': 0,
                'total_requests': 0,
                'timestamps': deque(maxlen=window_size)
            }
        }
        self.baseline = {'latency': None, 'error_rate': None}

    def collect_metric(self, version, latency=None, error=False):
        """
        Recopila una métrica para una versión específica.

        :param version: 'stable' o 'canary'.
        :param latency: Tiempo de latencia en ms (opcional).
        :param error: Booleano indicando si fue un error.
        """
        if version not in self.metrics:
            raise ValueError("Versión debe ser 'stable' o 'canary'")

        current_time = time.time()
        self.metrics[version]['timestamps'].append(current_time)
        self.metrics[version]['total_requests'] += 1

        if latency is not None:
            self.metrics[version]['latencies'].append(latency)

        if error:
            self.metrics[version]['errors'] += 1

    def calculate_kpis(self, version):
        """
        Calcula KPIs para una versión: latencia promedio, tasa de error, throughput.

        :param version: 'stable' o 'canary'.
        :return: Diccionario con KPIs.
        """
        if version not in self.metrics:
            raise ValueError("Versión debe ser 'stable' o 'canary'")

        data = self.metrics[version]
        latencies = list(data['latencies'])
        total_requests = data['total_requests']
        errors = data['errors']

        latency_avg = mean(latencies) if latencies else 0
        error_rate = errors / total_requests if total_requests > 0 else 0

        # Throughput: requests por segundo en la ventana
        if len(data['timestamps']) > 1:
            time_span = data['timestamps'][-1] - data['timestamps'][0]
            throughput = len(data['timestamps']) / time_span if time_span > 0 else 0
        else:
            throughput = 0

        return {
            'latency_avg': latency_avg,
            'error_rate': error_rate,
            'throughput': throughput
        }

    def aggregate_metrics(self):
        """
        Agrega métricas globales (promedio de ambas versiones).

        :return: Diccionario con métricas agregadas.
        """
        stable_kpis = self.calculate_kpis('stable')
        canary_kpis = self.calculate_kpis('canary')

        return {
            'global_latency_avg': (stable_kpis['latency_avg'] + canary_kpis['latency_avg']) / 2,
            'global_error_rate': (stable_kpis['error_rate'] + canary_kpis['error_rate']) / 2,
            'global_throughput': stable_kpis['throughput'] + canary_kpis['throughput']
        }

    def detect_anomalies(self, version):
        """
        Detecta anomalías comparando con baseline.

        :param version: 'stable' o 'canary'.
        :return: Lista de anomalías detectadas.
        """
        kpis = self.calculate_kpis(version)
        anomalies = []

        if self.baseline['latency'] is not None:
            if kpis['latency_avg'] > self.baseline['latency'] * 1.5:
                anomalies.append(f"Latencia alta en {version}: {kpis['latency_avg']} > {self.baseline['latency'] * 1.5}")

        if self.baseline['error_rate'] is not None:
            if kpis['error_rate'] > self.baseline['error_rate'] * 2:
                anomalies.append(f"Tasa de error alta en {version}: {kpis['error_rate']} > {self.baseline['error_rate'] * 2}")

        return anomalies

    def compare_versions(self):
        """
        Compara KPIs entre versiones stable y canary.

        :return: Diccionario con diferencias.
        """
        stable_kpis = self.calculate_kpis('stable')
        canary_kpis = self.calculate_kpis('canary')

        return {
            'latency_diff': canary_kpis['latency_avg'] - stable_kpis['latency_avg'],
            'error_rate_diff': canary_kpis['error_rate'] - stable_kpis['error_rate'],
            'throughput_diff': canary_kpis['throughput'] - stable_kpis['throughput']
        }

    def trigger_alerts(self):
        """
        Genera alertas si se exceden umbrales o se detectan anomalías.
        """
        for version in ['stable', 'canary']:
            kpis = self.calculate_kpis(version)
            anomalies = self.detect_anomalies(version)

            if kpis['latency_avg'] > self.alert_thresholds['latency']:
                logger.warning(f"Alerta: Latencia alta en {version} - {kpis['latency_avg']} ms")

            if kpis['error_rate'] > self.alert_thresholds['error_rate']:
                logger.warning(f"Alerta: Tasa de error alta en {version} - {kpis['error_rate']}")

            for anomaly in anomalies:
                logger.warning(f"Alerta de anomalía: {anomaly}")

    def set_baseline(self, latency, error_rate):
        """
        Establece el baseline para detección de anomalías.

        :param latency: Latencia baseline.
        :param error_rate: Tasa de error baseline.
        """
        self.baseline['latency'] = latency
        self.baseline['error_rate'] = error_rate