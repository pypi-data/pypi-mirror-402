import logging
import random
import hashlib

class TrafficSplitter:
    """
    Clase para dividir inteligentemente el tráfico entre versiones estables y canary.
    Incluye configuración de distribución, enrutamiento de solicitudes, ajuste dinámico
    basado en reglas, balanceo de carga simple y manejo de sesiones sticky.
    """

    def __init__(self, stable_endpoint, canary_endpoint, stable_percent=90, canary_percent=10, sticky_sessions=False):
        """
        Inicializa el TrafficSplitter.

        :param stable_endpoint: Endpoint de la versión estable
        :param canary_endpoint: Endpoint de la versión canary
        :param stable_percent: Porcentaje de tráfico a la versión estable (default 90)
        :param canary_percent: Porcentaje de tráfico a la versión canary (default 10)
        :param sticky_sessions: Si habilitar sesiones sticky (default False)
        """
        if stable_percent + canary_percent != 100:
            raise ValueError("Los porcentajes deben sumar 100")
        self.stable_endpoint = stable_endpoint
        self.canary_endpoint = canary_endpoint
        self.stable_percent = stable_percent
        self.canary_percent = canary_percent
        self.sticky_sessions = sticky_sessions
        self.logger = logging.getLogger(__name__)
        self.logger.info("TrafficSplitter inicializado con distribución: stable %d%%, canary %d%%", stable_percent, canary_percent)

    def set_distribution(self, stable_percent, canary_percent):
        """
        Configura la distribución de tráfico.

        :param stable_percent: Nuevo porcentaje para versión estable
        :param canary_percent: Nuevo porcentaje para versión canary
        """
        if stable_percent + canary_percent != 100:
            raise ValueError("Los porcentajes deben sumar 100")
        self.stable_percent = stable_percent
        self.canary_percent = canary_percent
        self.logger.info("Distribución de tráfico actualizada: stable %d%%, canary %d%%", stable_percent, canary_percent)

    def route_request(self, request):
        """
        Enruta una solicitud basada en la distribución configurada.
        Soporta balanceo de carga simple (aleatorio) y sesiones sticky.

        :param request: Diccionario con datos de la solicitud (debe incluir 'session_id' si sticky_sessions=True)
        :return: Endpoint al que enrutar la solicitud
        """
        if self.sticky_sessions and 'session_id' in request:
            # Usar hash consistente para sesiones sticky
            hash_val = int(hashlib.md5(request['session_id'].encode()).hexdigest(), 16) % 100
            if hash_val < self.stable_percent:
                endpoint = self.stable_endpoint
            else:
                endpoint = self.canary_endpoint
        else:
            # Balanceo de carga simple: aleatorio basado en porcentajes
            if random.randint(1, 100) <= self.stable_percent:
                endpoint = self.stable_endpoint
            else:
                endpoint = self.canary_endpoint

        self.logger.info("Solicitud enrutada a: %s", endpoint)
        return endpoint

    def adjust_based_on_rules(self, metrics):
        """
        Ajusta dinámicamente la distribución basada en reglas y métricas.

        :param metrics: Diccionario con métricas (ej. 'canary_success_rate')
        """
        # Regla simple: si tasa de éxito de canary > 95%, aumentar a 20%
        if 'canary_success_rate' in metrics and metrics['canary_success_rate'] > 95 and self.canary_percent < 20:
            self.set_distribution(80, 20)
            self.logger.info("Distribución ajustada automáticamente por regla de éxito")
        # Se pueden agregar más reglas según sea necesario