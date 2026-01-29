import logging
from datetime import datetime
from typing import Dict, Any, List, Optional


class CanaryRollback:
    """
    Clase para manejar rollback automático en despliegues canary basado en métricas.
    Detecta condiciones de rollback, ejecuta rollback gradual o inmediato, y restaura el estado anterior.
    """

    def __init__(self, thresholds: Dict[str, float], logger: Optional[logging.Logger] = None):
        """
        Inicializa la clase CanaryRollback.

        Args:
            thresholds: Diccionario con umbrales de métricas (ej. {'error_rate': 0.05, 'latency': 1000})
            logger: Logger opcional para logging detallado
        """
        self.thresholds = thresholds
        self.logger = logger or logging.getLogger(__name__)
        self.versions: List[Dict[str, Any]] = []  # Lista de versiones con timestamp y estado
        self.current_version: Optional[str] = None
        self.rollback_in_progress = False

    def deploy_version(self, version: str, state: Dict[str, Any] = None):
        """
        Registra una nueva versión desplegada.

        Args:
            version: Identificador de la versión
            state: Estado opcional asociado a la versión
        """
        # Marcar versiones anteriores como inactivas
        for v in self.versions:
            v['active'] = False

        version_entry = {
            'version': version,
            'timestamp': datetime.now(),
            'state': state or {},
            'active': True
        }
        self.versions.append(version_entry)
        self.current_version = version
        self.logger.info(f"Versión {version} desplegada exitosamente en {version_entry['timestamp']}")

    def detect_rollback_condition(self, metrics: Dict[str, float]) -> bool:
        """
        Detecta si se debe ejecutar un rollback basado en las métricas actuales y los umbrales.

        Args:
            metrics: Diccionario con métricas actuales (ej. {'error_rate': 0.03, 'latency': 800})

        Returns:
            True si se detecta condición de rollback, False en caso contrario
        """
        for metric_name, metric_value in metrics.items():
            if metric_name in self.thresholds and metric_value > self.thresholds[metric_name]:
                self.logger.warning(
                    f"Condición de rollback detectada: {metric_name} = {metric_value} > {self.thresholds[metric_name]}"
                )
                return True
        self.logger.debug("No se detectó condición de rollback")
        return False

    def execute_rollback(self, gradual: bool = False, traffic_reduction_steps: int = 5) -> bool:
        """
        Ejecuta un rollback a la versión anterior.

        Args:
            gradual: Si True, ejecuta rollback gradual reduciendo tráfico paso a paso
            traffic_reduction_steps: Número de pasos para reducción gradual de tráfico

        Returns:
            True si el rollback se ejecutó exitosamente, False en caso contrario
        """
        if self.rollback_in_progress:
            self.logger.warning("Rollback ya en progreso")
            return False

        if len(self.versions) < 2:
            self.logger.error("No hay versión anterior disponible para rollback")
            return False

        previous_version_entry = self.versions[-2]  # La penúltima es la anterior
        previous_version = previous_version_entry['version']

        self.rollback_in_progress = True
        try:
            if gradual:
                self.logger.info(f"Iniciando rollback gradual a versión {previous_version}")
                success = self._execute_gradual_rollback(previous_version, traffic_reduction_steps)
            else:
                self.logger.info(f"Iniciando rollback inmediato a versión {previous_version}")
                success = self._execute_immediate_rollback(previous_version)

            if success:
                self.logger.info(f"Rollback a versión {previous_version} completado exitosamente")
                # Marcar versión actual como inactiva
                if self.versions:
                    self.versions[-1]['active'] = False
                # Marcar versión anterior como activa
                previous_version_entry['active'] = True
                self.current_version = previous_version
            else:
                self.logger.error("Rollback fallido")
            return success
        finally:
            self.rollback_in_progress = False

    def _execute_immediate_rollback(self, target_version: str) -> bool:
        """
        Ejecuta rollback inmediato cambiando directamente a la versión objetivo.

        Args:
            target_version: Versión a la que hacer rollback

        Returns:
            True si exitoso
        """
        try:
            self.restore_previous_state(target_version)
            self.logger.info(f"Rollback inmediato completado a versión {target_version}")
            return True
        except Exception as e:
            self.logger.error(f"Error en rollback inmediato: {e}")
            return False

    def _execute_gradual_rollback(self, target_version: str, steps: int) -> bool:
        """
        Ejecuta rollback gradual reduciendo tráfico a la versión actual y aumentando a la anterior.

        Args:
            target_version: Versión a la que hacer rollback
            steps: Número de pasos para la transición

        Returns:
            True si exitoso
        """
        try:
            traffic_per_step = 1.0 / steps
            for step in range(1, steps + 1):
                current_traffic = 1.0 - (step * traffic_per_step)
                target_traffic = step * traffic_per_step
                self.logger.info(
                    f"Paso {step}/{steps}: Tráfico versión actual: {current_traffic:.2f}, "
                    f"Tráfico versión objetivo: {target_traffic:.2f}"
                )
                # Aquí iría la lógica real para ajustar tráfico (ej. actualizar balanceadores de carga)
                # Por simplicidad, simulamos con un sleep o solo logging
                # time.sleep(1)  # Simular tiempo entre pasos

            self.restore_previous_state(target_version)
            self.logger.info(f"Rollback gradual completado a versión {target_version}")
            return True
        except Exception as e:
            self.logger.error(f"Error en rollback gradual: {e}")
            return False

    def restore_previous_state(self, version: str):
        """
        Restaura el estado de la versión especificada.

        Args:
            version: Versión a restaurar
        """
        version_entry = next((v for v in self.versions if v['version'] == version), None)
        if not version_entry:
            raise ValueError(f"Versión {version} no encontrada")

        # Lógica para restaurar estado (ej. cargar configuración, modelos, etc.)
        # Esto dependería de la implementación específica del sistema
        self.logger.info(f"Estado restaurado para versión {version} desde {version_entry['timestamp']}")
        # Aquí iría código para restaurar bases de datos, configuraciones, etc.

    def get_version_history(self) -> List[Dict[str, Any]]:
        """
        Retorna el historial de versiones.

        Returns:
            Lista de entradas de versiones
        """
        return self.versions.copy()

    def get_current_version(self) -> Optional[str]:
        """
        Retorna la versión actualmente activa.

        Returns:
            Versión actual o None
        """
        return self.current_version