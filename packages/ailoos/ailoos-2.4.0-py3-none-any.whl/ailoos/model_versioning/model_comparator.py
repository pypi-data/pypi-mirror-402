import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class ComparisonResult:
    """Resultado de la comparación entre dos versiones de modelo."""
    version_a: str
    version_b: str
    parameter_differences: Dict[str, float]
    architecture_changes: List[str]
    performance_metrics_diff: Dict[str, float]
    hash_a: str
    hash_b: str
    similarity_score: float  # 0-1, 1 siendo idéntico
    breaking_changes: bool


class ModelComparator:
    """
    Comparador avanzado entre versiones de modelos.
    Analiza diferencias en parámetros, arquitectura y rendimiento.
    """

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance

    def compare_models(self,
                      model_a: Dict[str, Any],
                      model_b: Dict[str, Any],
                      version_a: str,
                      version_b: str,
                      metrics_a: Optional[Dict[str, float]] = None,
                      metrics_b: Optional[Dict[str, float]] = None) -> ComparisonResult:
        """
        Compara dos modelos representados como diccionarios.

        Args:
            model_a: Diccionario con parámetros del modelo A
            model_b: Diccionario con parámetros del modelo B
            version_a: Versión del modelo A
            version_b: Versión del modelo B
            metrics_a: Métricas de rendimiento del modelo A
            metrics_b: Métricas de rendimiento del modelo B

        Returns:
            ComparisonResult con detalles de las diferencias
        """

        # Calcular hashes para identificación única
        hash_a = self._compute_model_hash(model_a)
        hash_b = self._compute_model_hash(model_b)

        # Comparar parámetros
        param_diffs = self._compare_parameters(model_a, model_b)

        # Detectar cambios en arquitectura
        arch_changes = self._detect_architecture_changes(model_a, model_b)

        # Comparar métricas de rendimiento
        metrics_diff = {}
        if metrics_a and metrics_b:
            metrics_diff = self._compare_metrics(metrics_a, metrics_b)

        # Calcular score de similitud
        similarity = self._calculate_similarity_score(param_diffs, arch_changes, metrics_diff)

        # Determinar si hay cambios breaking
        breaking_changes = self._has_breaking_changes(arch_changes, param_diffs)

        return ComparisonResult(
            version_a=version_a,
            version_b=version_b,
            parameter_differences=param_diffs,
            architecture_changes=arch_changes,
            performance_metrics_diff=metrics_diff,
            hash_a=hash_a,
            hash_b=hash_b,
            similarity_score=similarity,
            breaking_changes=breaking_changes
        )

    def _compute_model_hash(self, model: Dict[str, Any]) -> str:
        """Computa un hash único para el modelo."""
        # Serializar parámetros para hashing
        param_str = str(sorted(model.items()))
        return hashlib.sha256(param_str.encode()).hexdigest()

    def _compare_parameters(self, model_a: Dict[str, Any], model_b: Dict[str, Any]) -> Dict[str, float]:
        """Compara parámetros numéricos entre modelos."""
        differences = {}

        all_keys = set(model_a.keys()) | set(model_b.keys())

        for key in all_keys:
            val_a = model_a.get(key)
            val_b = model_b.get(key)

            if val_a is None or val_b is None:
                differences[key] = float('inf')  # Parámetro faltante
                continue

            if isinstance(val_a, np.ndarray) and isinstance(val_b, np.ndarray):
                if val_a.shape != val_b.shape:
                    differences[key] = float('inf')
                else:
                    diff = np.linalg.norm(val_a - val_b)
                    differences[key] = diff if diff > self.tolerance else 0.0
            elif isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                diff = abs(val_a - val_b)
                differences[key] = diff if diff > self.tolerance else 0.0
            else:
                # Para tipos no numéricos, marcar como diferente si no son iguales
                differences[key] = 0.0 if val_a == val_b else float('inf')

        return differences

    def _detect_architecture_changes(self, model_a: Dict[str, Any], model_b: Dict[str, Any]) -> List[str]:
        """Detecta cambios en la arquitectura del modelo."""
        changes = []

        # Verificar capas faltantes o agregadas
        keys_a = set(model_a.keys())
        keys_b = set(model_b.keys())

        added = keys_b - keys_a
        removed = keys_a - keys_b

        if added:
            changes.append(f"Capas agregadas: {', '.join(added)}")
        if removed:
            changes.append(f"Capas removidas: {', '.join(removed)}")

        # Verificar cambios en shapes de parámetros
        for key in keys_a & keys_b:
            val_a = model_a[key]
            val_b = model_b[key]

            if isinstance(val_a, np.ndarray) and isinstance(val_b, np.ndarray):
                if val_a.shape != val_b.shape:
                    changes.append(f"Cambio de shape en '{key}': {val_a.shape} -> {val_b.shape}")

        return changes

    def _compare_metrics(self, metrics_a: Dict[str, float], metrics_b: Dict[str, float]) -> Dict[str, float]:
        """Compara métricas de rendimiento."""
        differences = {}

        all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())

        for metric in all_metrics:
            val_a = metrics_a.get(metric, 0.0)
            val_b = metrics_b.get(metric, 0.0)
            differences[metric] = val_b - val_a  # Diferencia (nuevo - antiguo)

        return differences

    def _calculate_similarity_score(self,
                                  param_diffs: Dict[str, float],
                                  arch_changes: List[str],
                                  metrics_diff: Dict[str, float]) -> float:
        """Calcula un score de similitud entre 0 y 1."""
        if not param_diffs:
            return 1.0

        # Penalizar cambios infinitos (parámetros faltantes o shapes diferentes)
        infinite_changes = sum(1 for diff in param_diffs.values() if diff == float('inf'))
        total_params = len(param_diffs)

        # Penalizar cambios en arquitectura
        arch_penalty = len(arch_changes) * 0.1

        # Calcular promedio de diferencias normalizadas
        finite_diffs = [diff for diff in param_diffs.values() if diff != float('inf')]
        if finite_diffs:
            avg_diff = np.mean(finite_diffs)
            # Normalizar (asumiendo que diffs > 1 son significativas)
            normalized_diff = min(avg_diff, 1.0)
        else:
            normalized_diff = 0.0

        # Score base
        similarity = 1.0 - normalized_diff - (infinite_changes / total_params) - arch_penalty

        return max(0.0, min(1.0, similarity))

    def _has_breaking_changes(self, arch_changes: List[str], param_diffs: Dict[str, float]) -> bool:
        """Determina si hay cambios que rompen compatibilidad."""
        # Cambios en arquitectura generalmente son breaking
        if arch_changes:
            return True

        # Cambios infinitos en parámetros son breaking
        if any(diff == float('inf') for diff in param_diffs.values()):
            return True

        return False