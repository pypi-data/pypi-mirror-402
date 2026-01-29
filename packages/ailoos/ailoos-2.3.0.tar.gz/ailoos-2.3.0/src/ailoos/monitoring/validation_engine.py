#!/usr/bin/env python3
"""
Validation Engine - Integra resultados de pruebas federadas con arquitectura general de Ailoos
Compara métricas en tiempo real con benchmarks validados de 62 pruebas federadas
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import aiohttp

logger = logging.getLogger(__name__)

class ValidationEngine:
    """
    Motor de validación que integra benchmarks de pruebas federadas
    con métricas en tiempo real del sistema Ailoos
    """

    def __init__(self, federated_test_results_path: str = None, coordinator_url: str = None):
        """
        Inicializa el motor de validación

        Args:
            federated_test_results_path: Ruta al archivo JSON con resultados de pruebas
            coordinator_url: URL del coordinador federado para métricas en tiempo real
        """
        self.federated_test_results_path = federated_test_results_path or Path(__file__).parent.parent / "federated_test" / "federated_test_summary.json"
        self.coordinator_url = coordinator_url or "http://localhost:5002"

        # Cargar benchmarks validados
        self.benchmarks = self._load_benchmarks()

        # Estado de validación
        self.validation_history = []
        self.alerts_queue = []

        logger.info("Validation Engine inicializado con benchmarks de pruebas federadas")

    def _load_benchmarks(self) -> Dict:
        """Carga y procesa los benchmarks de las pruebas federadas"""
        try:
            with open(self.federated_test_results_path, 'r') as f:
                data = json.load(f)

            # Calcular estadísticas agregadas de las 62 pruebas
            results = data.get('results', [])

            if not results:
                logger.warning("No se encontraron resultados de pruebas federadas")
                return {}

            # Calcular métricas promedio por tipo de hardware
            hardware_stats = {}
            all_accuracies = []

            for result in results:
                hardware = result.get('hardware_type', 'unknown')
                accuracy = result.get('final_accuracy', 0)
                loss = result.get('final_loss', 1.0)
                total_time = result.get('total_time', 0)

                all_accuracies.append(accuracy)

                if hardware not in hardware_stats:
                    hardware_stats[hardware] = {
                        'accuracies': [],
                        'losses': [],
                        'times': [],
                        'count': 0
                    }

                hardware_stats[hardware]['accuracies'].append(accuracy)
                hardware_stats[hardware]['losses'].append(loss)
                hardware_stats[hardware]['times'].append(total_time)
                hardware_stats[hardware]['count'] += 1

            # Calcular promedios por hardware
            benchmarks = {
                'global': {
                    'avg_accuracy': sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0,
                    'min_accuracy_threshold': min(all_accuracies) * 0.9 if all_accuracies else 0,  # 90% del mínimo
                    'max_concurrent_nodes': 20,  # Validado en pruebas
                    'total_tests_run': len(results),
                    'successful_tests': len([r for r in results if r.get('status') == 'success'])
                },
                'hardware': {}
            }

            for hardware, stats in hardware_stats.items():
                accuracies = stats['accuracies']
                losses = stats['losses']
                times = stats['times']

                benchmarks['hardware'][hardware] = {
                    'avg_accuracy': sum(accuracies) / len(accuracies),
                    'avg_loss': sum(losses) / len(losses),
                    'avg_time': sum(times) / len(times),
                    'min_accuracy': min(accuracies),
                    'max_accuracy': max(accuracies),
                    'sample_size': len(accuracies),
                    'accuracy_threshold': min(accuracies) * 0.95  # 95% del mínimo validado
                }

            logger.info(f"Benchmarks cargados: {benchmarks['global']['total_tests_run']} pruebas, "
                       f"accuracy promedio: {benchmarks['global']['avg_accuracy']:.1f}%")
            return benchmarks

        except Exception as e:
            logger.error(f"Error cargando benchmarks: {e}")
            return {}

    async def validate_current_performance(self, current_metrics: Dict) -> Dict:
        """
        Valida métricas actuales contra benchmarks federados

        Args:
            current_metrics: Métricas actuales del sistema

        Returns:
            Dict con resultados de validación y alertas
        """
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'is_valid': True,
            'alerts': [],
            'benchmark_comparison': {},
            'recommendations': []
        }

        try:
            # Validar accuracy global
            current_accuracy = current_metrics.get('avg_accuracy', 0)
            benchmark_accuracy = self.benchmarks.get('global', {}).get('avg_accuracy', 0)

            if current_accuracy < benchmark_accuracy * 0.95:  # 5% por debajo del benchmark
                validation_result['is_valid'] = False
                validation_result['alerts'].append({
                    'level': 'CRITICAL',
                    'message': f'Accuracy actual ({current_accuracy:.1f}%) por debajo del benchmark validado ({benchmark_accuracy:.1f}%)',
                    'recommendation': 'Revisar configuración de entrenamiento federado'
                })

            # Validar número de nodos concurrentes
            current_nodes = current_metrics.get('active_nodes', 0)
            max_validated_nodes = self.benchmarks.get('global', {}).get('max_concurrent_nodes', 0)

            if current_nodes > max_validated_nodes:
                validation_result['alerts'].append({
                    'level': 'WARNING',
                    'message': f'Nodos concurrentes ({current_nodes}) supera límite validado ({max_validated_nodes})',
                    'recommendation': 'Monitorear estabilidad del sistema'
                })

            # Validar por tipo de hardware si está disponible
            hardware_metrics = current_metrics.get('hardware_breakdown', {})
            for hardware, metrics in hardware_metrics.items():
                if hardware in self.benchmarks.get('hardware', {}):
                    hw_benchmark = self.benchmarks['hardware'][hardware]
                    hw_accuracy = metrics.get('accuracy', 0)

                    if hw_accuracy < hw_benchmark['accuracy_threshold']:
                        validation_result['is_valid'] = False
                        validation_result['alerts'].append({
                            'level': 'WARNING',
                            'message': f'Accuracy de {hardware} ({hw_accuracy:.1f}%) por debajo del threshold validado',
                            'recommendation': f'Optimizar configuración para hardware {hardware}'
                        })

            # Comparación con benchmarks
            validation_result['benchmark_comparison'] = {
                'current_accuracy': current_accuracy,
                'benchmark_accuracy': benchmark_accuracy,
                'accuracy_diff_percent': ((current_accuracy - benchmark_accuracy) / benchmark_accuracy * 100) if benchmark_accuracy > 0 else 0,
                'current_nodes': current_nodes,
                'max_validated_nodes': max_validated_nodes,
                'validation_status': 'PASS' if validation_result['is_valid'] else 'FAIL'
            }

            # Recomendaciones basadas en validación
            if not validation_result['is_valid']:
                validation_result['recommendations'].extend([
                    "Ejecutar pruebas federadas adicionales para nuevos benchmarks",
                    "Revisar configuración de agregación FedAvg",
                    "Verificar conectividad de nodos problemáticos",
                    "Considerar optimización de hardware específico"
                ])

            # Guardar en historial
            self.validation_history.append(validation_result)

            logger.info(f"Validación completada: {'PASS' if validation_result['is_valid'] else 'FAIL'} "
                       f"({len(validation_result['alerts'])} alertas)")

            return validation_result

        except Exception as e:
            logger.error(f"Error en validación: {e}")
            validation_result['alerts'].append({
                'level': 'ERROR',
                'message': f'Error en motor de validación: {str(e)}',
                'recommendation': 'Revisar logs del sistema'
            })
            return validation_result

    async def get_realtime_metrics(self) -> Dict:
        """Obtiene métricas en tiempo real del coordinador"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.coordinator_url}/api/stats", timeout=5) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Error obteniendo métricas del coordinador: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error conectando al coordinador: {e}")
            return {}

    async def continuous_validation(self, interval_seconds: int = 60):
        """
        Ejecuta validación continua en background

        Args:
            interval_seconds: Intervalo entre validaciones
        """
        logger.info(f"Iniciando validación continua cada {interval_seconds} segundos")

        while True:
            try:
                # Obtener métricas actuales
                current_metrics = await self.get_realtime_metrics()

                if current_metrics:
                    # Validar contra benchmarks
                    validation = await self.validate_current_performance(current_metrics)

                    # Procesar alertas
                    for alert in validation['alerts']:
                        await self._process_alert(alert)

                    # Log de validación
                    if not validation['is_valid']:
                        logger.warning(f"Validación FALLIDA: {len(validation['alerts'])} alertas detectadas")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error en validación continua: {e}")
                await asyncio.sleep(interval_seconds)

    async def _process_alert(self, alert: Dict):
        """Procesa una alerta generada por el motor de validación"""
        # Aquí se integraría con el sistema de alertas
        # Por ahora solo logueamos
        level = alert.get('level', 'INFO')
        message = alert.get('message', '')

        if level == 'CRITICAL':
            logger.critical(f"VALIDATION ALERT: {message}")
        elif level == 'WARNING':
            logger.warning(f"VALIDATION ALERT: {message}")
        else:
            logger.info(f"VALIDATION ALERT: {message}")

        # Agregar a cola de alertas para dashboard
        self.alerts_queue.append({
            **alert,
            'timestamp': datetime.now().isoformat()
        })

        # Mantener solo últimas 100 alertas
        if len(self.alerts_queue) > 100:
            self.alerts_queue = self.alerts_queue[-100:]

    def get_validation_status(self) -> Dict:
        """Obtiene estado actual de validación"""
        latest_validation = self.validation_history[-1] if self.validation_history else {}

        return {
            'benchmarks_loaded': bool(self.benchmarks),
            'total_validations': len(self.validation_history),
            'latest_validation': latest_validation,
            'active_alerts': len([a for a in self.alerts_queue if a.get('level') in ['CRITICAL', 'WARNING']]),
            'validation_uptime': 'OK' if self.benchmarks else 'NO_BENCHMARKS'
        }

    def get_benchmark_summary(self) -> Dict:
        """Obtiene resumen de benchmarks cargados"""
        if not self.benchmarks:
            return {'status': 'NO_BENCHMARKS_LOADED'}

        global_bm = self.benchmarks.get('global', {})
        hardware_bm = self.benchmarks.get('hardware', {})

        return {
            'global_benchmarks': global_bm,
            'hardware_benchmarks': hardware_bm,
            'validation_ready': True,
            'last_updated': datetime.fromtimestamp(self.benchmarks.get('timestamp', time.time())).isoformat()
        }


# Instancia global del motor de validación
validation_engine = ValidationEngine()


async def start_validation_engine():
    """Inicia el motor de validación en background"""
    await validation_engine.continuous_validation()


if __name__ == "__main__":
    # Test del motor de validación
    async def test():
        engine = ValidationEngine()

        # Simular métricas actuales
        test_metrics = {
            'avg_accuracy': 75.0,  # Por debajo del benchmark (81%)
            'active_nodes': 15,
            'hardware_breakdown': {
                'macbook_m4': {'accuracy': 78.0}
            }
        }

        result = await engine.validate_current_performance(test_metrics)
        print("Resultado de validación:", json.dumps(result, indent=2))

    asyncio.run(test())