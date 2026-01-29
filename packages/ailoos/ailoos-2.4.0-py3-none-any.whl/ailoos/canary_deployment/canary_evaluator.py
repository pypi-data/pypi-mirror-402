import logging
import statistics
from typing import Dict, List, Any, Optional


class CanaryEvaluator:
    """
    Clase para evaluar automáticamente el desempeño del canary basado en métricas.
    Incluye métodos para definir criterios de éxito, evaluar umbrales, y decidir promoción o rollback.
    Soporta evaluación basada en reglas configurables, análisis estadístico básico, y logging de decisiones.
    """

    def __init__(self, criteria: Optional[Dict[str, Dict[str, Any]]] = None,
                 thresholds: Optional[Dict[str, float]] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Inicializa el evaluador de canary.

        :param criteria: Diccionario de criterios configurables. Ej: {'latency': {'operator': '<', 'value': 100}}
        :param thresholds: Diccionario de umbrales simples. Ej: {'latency': 100}
        :param logger: Logger opcional para logging.
        """
        self.criteria = criteria or {}
        self.thresholds = thresholds or {}
        self.logger = logger or logging.getLogger(__name__)

    def set_criteria(self, criteria: Dict[str, Dict[str, Any]]):
        """
        Define los criterios de éxito para la evaluación.

        :param criteria: Diccionario de criterios. Ej: {'latency': {'operator': '<', 'value': 100}}
        """
        self.criteria = criteria
        self.logger.info(f"Criterios de éxito actualizados: {criteria}")

    def evaluate(self, metrics: Dict[str, List[float]]) -> str:
        """
        Evalúa las métricas del canary y decide promoción, rollback o continuar.

        :param metrics: Diccionario con listas de valores métricos. Ej: {'latency': [100, 95, 105]}
        :return: 'promote', 'rollback', o 'continue'
        """
        evaluation_results = {}
        for metric_name, values in metrics.items():
            if not values:
                self.logger.warning(f"No hay valores para la métrica {metric_name}")
                continue

            # Análisis estadístico básico
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values) if len(values) > 1 else 0.0

            evaluation_results[metric_name] = {
                'mean': mean_val,
                'stdev': stdev_val,
                'passes': self._check_metric_against_criteria(metric_name, mean_val, stdev_val)
            }

        decision = self._decide(evaluation_results)
        self.logger.info(f"Evaluación completada. Resultados: {evaluation_results}. Decisión: {decision}")
        return decision

    def check_thresholds(self, metrics: Dict[str, List[float]]) -> Dict[str, bool]:
        """
        Verifica si las métricas cumplen con los umbrales definidos.

        :param metrics: Diccionario con listas de valores métricos.
        :return: Diccionario con booleanos indicando si cada métrica pasa el umbral.
        """
        results = {}
        for metric_name, values in metrics.items():
            if not values:
                results[metric_name] = False
                continue
            mean_val = statistics.mean(values)
            threshold = self.thresholds.get(metric_name)
            if threshold is not None:
                results[metric_name] = mean_val <= threshold  # Asumiendo umbral máximo
            else:
                results[metric_name] = True  # Sin umbral definido, pasa por defecto
        self.logger.debug(f"Verificación de umbrales: {results}")
        return results

    def _check_metric_against_criteria(self, metric_name: str, mean_val: float, stdev_val: float) -> bool:
        """
        Verifica una métrica específica contra sus criterios.

        :param metric_name: Nombre de la métrica.
        :param mean_val: Valor medio.
        :param stdev_val: Desviación estándar.
        :return: True si pasa, False si no.
        """
        criterion = self.criteria.get(metric_name)
        if not criterion:
            return True  # Sin criterio, pasa

        operator = criterion.get('operator')
        value = criterion.get('value')

        if operator == '<':
            return mean_val < value
        elif operator == '<=':
            return mean_val <= value
        elif operator == '>':
            return mean_val > value
        elif operator == '>=':
            return mean_val >= value
        elif operator == '==':
            return mean_val == value
        else:
            self.logger.warning(f"Operador desconocido {operator} para {metric_name}")
            return False

    def _decide(self, evaluation_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Decide promoción, rollback o continuar basado en resultados de evaluación.

        :param evaluation_results: Resultados de evaluación por métrica.
        :return: 'promote', 'rollback', o 'continue'
        """
        all_pass = all(result['passes'] for result in evaluation_results.values())
        any_fail = any(not result['passes'] for result in evaluation_results.values())

        if all_pass:
            return 'promote'
        elif any_fail:
            return 'rollback'
        else:
            return 'continue'