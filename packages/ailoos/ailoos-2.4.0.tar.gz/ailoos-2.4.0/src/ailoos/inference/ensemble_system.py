"""
Ensemble System - FASE 9: Sistema Avanzado de Ensemble Learning
Sistema completo de ensemble methods para mejorar la precisión y robustez de modelos.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.ensemble import VotingClassifier, VotingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class VotingType(Enum):
    """Tipos de votación disponibles."""
    HARD = "hard"
    SOFT = "soft"


class EnsembleType(Enum):
    """Tipos de ensemble disponibles."""
    VOTING = "voting"
    BAGGING = "bagging"
    BOOSTING = "boosting"
    STACKING = "stacking"
    WEIGHTED = "weighted"


@dataclass
class ModelPrediction:
    """Representa una predicción de un modelo individual."""
    model_id: str
    prediction: Union[np.ndarray, torch.Tensor]
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EnsembleResult:
    """Resultado final del ensemble."""
    final_prediction: Union[np.ndarray, torch.Tensor]
    confidence: float
    model_contributions: Dict[str, float]
    ensemble_type: EnsembleType
    metadata: Optional[Dict[str, Any]] = None


class BaseEnsemble(ABC):
    """Clase base para todos los métodos de ensemble."""

    def __init__(self, models: List[Any], model_ids: Optional[List[str]] = None):
        """
        Inicializa el ensemble base.

        Args:
            models: Lista de modelos a ensamblar
            model_ids: IDs opcionales para los modelos
        """
        self.models = models
        self.model_ids = model_ids or [f"model_{i}" for i in range(len(models))]
        self.is_fitted = False
        self.ensemble_type = None

    @abstractmethod
    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena el ensemble."""
        pass

    @abstractmethod
    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicciones con el ensemble."""
        pass

    @abstractmethod
    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones de cada modelo."""
        pass


class VotingEnsemble(BaseEnsemble):
    """
    Ensemble por votación (hard/soft) con múltiples modelos.
    Soporta clasificación y regresión.
    """

    def __init__(self, models: List[Any], voting_type: VotingType = VotingType.SOFT,
                 weights: Optional[List[float]] = None, model_ids: Optional[List[str]] = None):
        """
        Inicializa VotingEnsemble.

        Args:
            models: Lista de modelos
            voting_type: Tipo de votación (hard/soft)
            weights: Pesos opcionales para cada modelo
            model_ids: IDs de los modelos
        """
        super().__init__(models, model_ids)
        self.voting_type = voting_type
        self.weights = weights
        self.ensemble_type = EnsembleType.VOTING
        self._sklearn_voter = None

    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena todos los modelos del ensemble."""
        logger.info(f"Entrenando VotingEnsemble con {len(self.models)} modelos")

        # Entrenar modelos en paralelo
        tasks = []
        for i, model in enumerate(self.models):
            task = asyncio.get_event_loop().run_in_executor(
                None, self._fit_single_model, model, X, y, i
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        self.is_fitted = True

        # Crear voter de sklearn para compatibilidad
        if self.voting_type == VotingType.SOFT:
            self._sklearn_voter = VotingClassifier(
                estimators=list(zip(self.model_ids, self.models)),
                voting='soft',
                weights=self.weights
            )
        else:
            self._sklearn_voter = VotingClassifier(
                estimators=list(zip(self.model_ids, self.models)),
                voting='hard',
                weights=self.weights
            )

        logger.info("VotingEnsemble entrenado exitosamente")

    def _fit_single_model(self, model: Any, X: Union[np.ndarray, torch.Tensor],
                         y: Union[np.ndarray, torch.Tensor], idx: int) -> None:
        """Entrena un modelo individual."""
        try:
            if hasattr(model, 'fit'):
                model.fit(X, y)
            elif hasattr(model, '__call__'):  # Para funciones
                pass  # Asumir que ya está entrenado
            logger.debug(f"Modelo {self.model_ids[idx]} entrenado")
        except Exception as e:
            logger.error(f"Error entrenando modelo {self.model_ids[idx]}: {e}")
            raise

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción por votación."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        # Obtener predicciones de todos los modelos
        predictions = []
        confidences = []

        for i, model in enumerate(self.models):
            try:
                if hasattr(model, 'predict_proba') and self.voting_type == VotingType.SOFT:
                    pred = model.predict_proba(X)
                    predictions.append(pred)
                    # Calcular confianza como la probabilidad máxima
                    conf = np.max(pred, axis=1).mean()
                    confidences.append(conf)
                elif hasattr(model, 'predict'):
                    pred = model.predict(X)
                    predictions.append(pred)
                    confidences.append(0.5)  # Confianza neutral para hard voting
                else:
                    raise ValueError(f"Modelo {self.model_ids[i]} no tiene método predict")
            except Exception as e:
                logger.error(f"Error prediciendo con modelo {self.model_ids[i]}: {e}")
                raise

        # Aplicar votación
        if self.voting_type == VotingType.SOFT:
            final_pred = self._soft_voting(predictions)
        else:
            final_pred = self._hard_voting(predictions)

        # Calcular confianza del ensemble
        ensemble_confidence = np.mean(confidences)

        # Calcular contribuciones
        contributions = self.get_model_contributions()

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=ensemble_confidence,
            model_contributions=contributions,
            ensemble_type=self.ensemble_type,
            metadata={
                'voting_type': self.voting_type.value,
                'num_models': len(self.models),
                'weights': self.weights
            }
        )

    def _soft_voting(self, predictions: List[np.ndarray]) -> np.ndarray:
        """Aplica votación soft (promedio de probabilidades)."""
        if self.weights is None:
            return np.mean(predictions, axis=0)
        else:
            weighted_sum = np.zeros_like(predictions[0])
            total_weight = sum(self.weights)
            for pred, weight in zip(predictions, self.weights):
                weighted_sum += pred * (weight / total_weight)
            return weighted_sum

    def _hard_voting(self, predictions: List[np.ndarray]) -> np.ndarray:
        """Aplica votación hard (mayoría de votos)."""
        # Convertir a array numpy
        pred_array = np.array(predictions)  # Shape: (n_models, n_samples) o (n_models, n_samples, n_classes)

        if len(pred_array.shape) == 3:  # Probabilidades - convertir a clases
            pred_array = np.argmax(pred_array, axis=2)  # Shape: (n_models, n_samples)

        # Ahora pred_array tiene shape (n_models, n_samples) con las clases predichas
        n_samples = pred_array.shape[1]
        unique_classes = np.unique(pred_array)

        # Contar votos por muestra y clase
        vote_counts = np.zeros((n_samples, len(unique_classes)))

        for i, cls in enumerate(unique_classes):
            vote_counts[:, i] = np.sum(pred_array == cls, axis=0)

        # Aplicar pesos si existen
        if self.weights is not None:
            vote_counts = vote_counts * np.array(self.weights).reshape(-1, 1)

        # Clase con más votos para cada muestra
        final_classes = unique_classes[np.argmax(vote_counts, axis=1)]
        return final_classes

    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones de cada modelo."""
        if self.weights is None:
            return {model_id: 1.0 / len(self.models) for model_id in self.model_ids}
        else:
            total_weight = sum(self.weights)
            return {model_id: weight / total_weight
                   for model_id, weight in zip(self.model_ids, self.weights)}


class BaggingEnsemble(BaseEnsemble):
    """
    Ensemble bagging con bootstrap sampling.
    Crea múltiples versiones del dataset mediante muestreo con reemplazo.
    """

    def __init__(self, base_model_class: Any, n_estimators: int = 10,
                 max_samples: float = 1.0, bootstrap: bool = True,
                 random_state: Optional[int] = None, model_ids: Optional[List[str]] = None):
        """
        Inicializa BaggingEnsemble.

        Args:
            base_model_class: Clase del modelo base
            n_estimators: Número de modelos en el ensemble
            max_samples: Fracción máxima de muestras por modelo
            bootstrap: Si usar bootstrap sampling
            random_state: Semilla para reproducibilidad
            model_ids: IDs de los modelos
        """
        models = [base_model_class() for _ in range(n_estimators)]
        super().__init__(models, model_ids)
        self.base_model_class = base_model_class
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.bootstrap = bootstrap
        self.random_state = random_state
        self.ensemble_type = EnsembleType.BAGGING
        self.bootstrap_indices = []

    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena el ensemble con bagging."""
        logger.info(f"Entrenando BaggingEnsemble con {self.n_estimators} modelos")

        X = np.array(X)
        y = np.array(y)
        n_samples = len(X)

        rng = np.random.RandomState(self.random_state)

        # Entrenar cada modelo con bootstrap sample
        tasks = []
        for i in range(self.n_estimators):
            # Generar índices bootstrap
            if self.bootstrap:
                indices = rng.choice(n_samples, size=int(n_samples * self.max_samples),
                                   replace=True)
            else:
                indices = rng.choice(n_samples, size=int(n_samples * self.max_samples),
                                   replace=False)

            self.bootstrap_indices.append(indices)

            # Crear subset
            X_subset = X[indices]
            y_subset = y[indices]

            task = asyncio.get_event_loop().run_in_executor(
                None, self._fit_single_model, self.models[i], X_subset, y_subset, i
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        self.is_fitted = True
        logger.info("BaggingEnsemble entrenado exitosamente")

    def _fit_single_model(self, model: Any, X: np.ndarray, y: np.ndarray, idx: int) -> None:
        """Entrena un modelo individual con subset bootstrap."""
        try:
            model.fit(X, y)
            logger.debug(f"Modelo bagging {idx} entrenado")
        except Exception as e:
            logger.error(f"Error entrenando modelo bagging {idx}: {e}")
            raise

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción promediando todas las predicciones."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        X = np.array(X)
        predictions = []

        # Obtener predicciones de todos los modelos
        for i, model in enumerate(self.models):
            try:
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X)
                elif hasattr(model, 'predict'):
                    pred = model.predict(X)
                else:
                    raise ValueError(f"Modelo {i} no tiene método predict")
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Error prediciendo con modelo bagging {i}: {e}")
                raise

        # Promediar predicciones
        if hasattr(predictions[0], 'shape') and len(predictions[0].shape) > 1:
            # Probabilidades - promedio
            final_pred = np.mean(predictions, axis=0)
            confidence = np.max(final_pred, axis=1).mean()
        else:
            # Predicciones directas - promedio
            final_pred = np.mean(predictions, axis=0)
            confidence = 0.5  # Confianza neutral

        contributions = self.get_model_contributions()

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=confidence,
            model_contributions=contributions,
            ensemble_type=self.ensemble_type,
            metadata={
                'n_estimators': self.n_estimators,
                'max_samples': self.max_samples,
                'bootstrap': self.bootstrap
            }
        )

    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones de cada modelo (iguales en bagging)."""
        return {model_id: 1.0 / len(self.models) for model_id in self.model_ids}


class BoostingEnsemble(BaseEnsemble):
    """
    Ensemble boosting adaptativo.
    Cada modelo se enfoca en corregir los errores del anterior.
    """

    def __init__(self, base_model_class: Any, n_estimators: int = 10,
                 learning_rate: float = 0.1, random_state: Optional[int] = None,
                 model_ids: Optional[List[str]] = None):
        """
        Inicializa BoostingEnsemble.

        Args:
            base_model_class: Clase del modelo base
            n_estimators: Número de modelos
            learning_rate: Tasa de aprendizaje para boosting
            random_state: Semilla para reproducibilidad
            model_ids: IDs de los modelos
        """
        models = [base_model_class() for _ in range(n_estimators)]
        super().__init__(models, model_ids)
        self.base_model_class = base_model_class
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.ensemble_type = EnsembleType.BOOSTING
        self.model_weights = np.ones(n_estimators) / n_estimators

    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena el ensemble con boosting adaptativo."""
        logger.info(f"Entrenando BoostingEnsemble con {self.n_estimators} modelos")

        X = np.array(X)
        y = np.array(y)

        # Inicializar pesos de muestras
        sample_weights = np.ones(len(X)) / len(X)

        rng = np.random.RandomState(self.random_state)

        for i in range(self.n_estimators):
            # Entrenar modelo con pesos actuales
            self.models[i].fit(X, y, sample_weight=sample_weights)

            # Calcular error
            predictions = self.models[i].predict(X)
            errors = (predictions != y).astype(float)

            # Calcular error ponderado
            weighted_error = np.sum(sample_weights * errors)

            if weighted_error >= 0.5:
                logger.warning(f"Modelo {i} tiene error >= 0.5, deteniendo boosting temprano")
                break

            # Calcular peso del modelo
            beta = self.learning_rate * np.log((1 - weighted_error) / max(weighted_error, 1e-10))
            self.model_weights[i] = beta

            # Actualizar pesos de muestras
            sample_weights *= np.exp(beta * errors)
            sample_weights /= np.sum(sample_weights)  # Normalizar

            logger.debug(f"Modelo boosting {i} entrenado, error ponderado: {weighted_error:.4f}")

        self.is_fitted = True
        logger.info("BoostingEnsemble entrenado exitosamente")

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción con boosting."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        X = np.array(X)

        # Obtener predicciones ponderadas
        weighted_predictions = []

        for i, model in enumerate(self.models):
            try:
                pred = model.predict(X)
                weighted_predictions.append(pred * self.model_weights[i])
            except Exception as e:
                logger.error(f"Error prediciendo con modelo boosting {i}: {e}")
                raise

        # Combinar predicciones
        final_pred = np.sum(weighted_predictions, axis=0) / np.sum(self.model_weights)

        # Para clasificación binaria, convertir a clases
        if len(np.unique(final_pred)) == 2:
            final_pred = (final_pred > 0.5).astype(int)

        confidence = 0.5  # Placeholder

        contributions = self.get_model_contributions()

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=confidence,
            model_contributions=contributions,
            ensemble_type=self.ensemble_type,
            metadata={
                'n_estimators': self.n_estimators,
                'learning_rate': self.learning_rate,
                'model_weights': self.model_weights.tolist()
            }
        )

    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones de cada modelo basadas en sus pesos."""
        total_weight = np.sum(self.model_weights)
        return {model_id: weight / total_weight
               for model_id, weight in zip(self.model_ids, self.model_weights)}


class StackingEnsemble(BaseEnsemble):
    """
    Ensemble stacking con meta-modelo.
    Usa un meta-modelo para combinar las predicciones de los modelos base.
    """

    def __init__(self, base_models: List[Any], meta_model: Any,
                 cv_folds: int = 5, model_ids: Optional[List[str]] = None,
                 meta_model_id: str = "meta_model"):
        """
        Inicializa StackingEnsemble.

        Args:
            base_models: Lista de modelos base
            meta_model: Modelo meta para combinar predicciones
            cv_folds: Número de folds para cross-validation
            model_ids: IDs de los modelos base
            meta_model_id: ID del meta-modelo
        """
        super().__init__(base_models, model_ids)
        self.meta_model = meta_model
        self.cv_folds = cv_folds
        self.meta_model_id = meta_model_id
        self.ensemble_type = EnsembleType.STACKING
        self.base_predictions_train = None

    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena el ensemble con stacking."""
        logger.info(f"Entrenando StackingEnsemble con {len(self.models)} modelos base")

        X = np.array(X)
        y = np.array(y)

        # Generar predicciones de modelos base usando cross-validation
        self.base_predictions_train = self._get_base_predictions_cv(X, y)

        # Entrenar modelos base en todo el dataset
        tasks = []
        for i, model in enumerate(self.models):
            task = asyncio.get_event_loop().run_in_executor(
                None, model.fit, X, y
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Entrenar meta-modelo
        self.meta_model.fit(self.base_predictions_train, y)

        self.is_fitted = True
        logger.info("StackingEnsemble entrenado exitosamente")

    def _get_base_predictions_cv(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Genera predicciones de modelos base usando cross-validation."""
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        base_predictions = np.zeros((len(X), len(self.models)))

        for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train = y[train_idx]

            for i, model in enumerate(self.models):
                # Entrenar modelo en fold de entrenamiento
                model_copy = type(model)()  # Crear copia fresca
                model_copy.fit(X_train, y_train)

                # Predecir en fold de validación
                if hasattr(model_copy, 'predict_proba'):
                    pred = model_copy.predict_proba(X_val)
                    if len(pred.shape) > 1:
                        pred = pred[:, 1]  # Para clasificación binaria
                else:
                    pred = model_copy.predict(X_val)

                base_predictions[val_idx, i] = pred

        return base_predictions

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción con stacking."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        X = np.array(X)

        # Obtener predicciones de modelos base
        base_predictions = np.zeros((len(X), len(self.models)))

        for i, model in enumerate(self.models):
            try:
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X)
                    if len(pred.shape) > 1:
                        pred = pred[:, 1]
                else:
                    pred = model.predict(X)
                base_predictions[:, i] = pred
            except Exception as e:
                logger.error(f"Error prediciendo con modelo base {i}: {e}")
                raise

        # Predecir con meta-modelo
        final_pred = self.meta_model.predict(base_predictions)

        confidence = 0.5  # Placeholder

        contributions = self.get_model_contributions()

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=confidence,
            model_contributions=contributions,
            ensemble_type=self.ensemble_type,
            metadata={
                'cv_folds': self.cv_folds,
                'meta_model': self.meta_model_id
            }
        )

    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones (iguales para stacking básico)."""
        contributions = {model_id: 1.0 / len(self.models) for model_id in self.model_ids}
        contributions[self.meta_model_id] = 1.0  # Meta-modelo tiene peso igual
        return contributions


class WeightedEnsemble(BaseEnsemble):
    """
    Ensemble con pesos dinámicos.
    Ajusta pesos basados en el rendimiento histórico de cada modelo.
    """

    def __init__(self, models: List[Any], initial_weights: Optional[List[float]] = None,
                 adaptation_rate: float = 0.1, model_ids: Optional[List[str]] = None):
        """
        Inicializa WeightedEnsemble.

        Args:
            models: Lista de modelos
            initial_weights: Pesos iniciales
            adaptation_rate: Tasa de adaptación de pesos
            model_ids: IDs de los modelos
        """
        super().__init__(models, model_ids)
        self.weights = initial_weights or [1.0 / len(models)] * len(models)
        self.adaptation_rate = adaptation_rate
        self.ensemble_type = EnsembleType.WEIGHTED
        self.performance_history = []

    async def fit(self, X: Union[np.ndarray, torch.Tensor],
                  y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena el ensemble con pesos dinámicos."""
        logger.info(f"Entrenando WeightedEnsemble con {len(self.models)} modelos")

        # Entrenar todos los modelos
        tasks = []
        for i, model in enumerate(self.models):
            task = asyncio.get_event_loop().run_in_executor(
                None, model.fit, X, y
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        self.is_fitted = True
        logger.info("WeightedEnsemble entrenado exitosamente")

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción con pesos dinámicos."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        X = np.array(X)

        # Obtener predicciones de todos los modelos
        predictions = []
        for i, model in enumerate(self.models):
            try:
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X)
                elif hasattr(model, 'predict'):
                    pred = model.predict(X)
                else:
                    raise ValueError(f"Modelo {i} no tiene método predict")
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Error prediciendo con modelo weighted {i}: {e}")
                raise

        # Aplicar pesos
        if hasattr(predictions[0], 'shape') and len(predictions[0].shape) > 1:
            # Probabilidades
            weighted_pred = np.zeros_like(predictions[0])
            for pred, weight in zip(predictions, self.weights):
                weighted_pred += pred * weight
            final_pred = weighted_pred
            confidence = np.max(final_pred, axis=1).mean()
        else:
            # Predicciones directas
            weighted_pred = np.zeros_like(predictions[0], dtype=float)
            for pred, weight in zip(predictions, self.weights):
                weighted_pred += pred * weight
            final_pred = weighted_pred
            confidence = 0.5

        contributions = self.get_model_contributions()

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=confidence,
            model_contributions=contributions,
            ensemble_type=self.ensemble_type,
            metadata={
                'adaptation_rate': self.adaptation_rate,
                'current_weights': self.weights
            }
        )

    def update_weights(self, X_val: np.ndarray, y_val: np.ndarray) -> None:
        """Actualiza pesos basados en rendimiento en datos de validación."""
        if not self.is_fitted:
            raise ValueError("El ensemble no ha sido entrenado")

        # Calcular rendimiento de cada modelo
        performances = []
        for model in self.models:
            try:
                if hasattr(model, 'predict_proba'):
                    # Intentar usar probabilidades para clasificación
                    try:
                        pred = model.predict_proba(X_val)
                        if len(pred.shape) > 1:
                            pred_classes = np.argmax(pred, axis=1)
                            acc = accuracy_score(y_val, pred_classes)
                            performances.append(acc)
                        else:
                            # Probabilidades 1D - asumir clasificación binaria
                            pred_classes = (pred > 0.5).astype(int)
                            acc = accuracy_score(y_val, pred_classes)
                            performances.append(acc)
                    except:
                        # Fallback a predict normal
                        pred = model.predict(X_val)
                        acc = accuracy_score(y_val, pred)
                        performances.append(acc)
                else:
                    # Usar predict directo
                    pred = model.predict(X_val)
                    # Verificar si es clasificación o regresión
                    if len(np.unique(y_val)) <= 10:  # Asumir clasificación
                        acc = accuracy_score(y_val, pred)
                        performances.append(acc)
                    else:  # Regresión
                        mse = mean_squared_error(y_val, pred)
                        performances.append(-mse)
            except Exception as e:
                logger.error(f"Error evaluando modelo: {e}")
                performances.append(0.0)

        # Actualizar pesos usando regla de actualización
        total_perf = sum(performances)
        if total_perf > 0:
            new_weights = []
            for perf in performances:
                new_weight = self.weights[len(new_weights)] + self.adaptation_rate * (perf / total_perf - self.weights[len(new_weights)])
                new_weights.append(max(0.01, new_weight))  # Peso mínimo

            # Normalizar
            total_weight = sum(new_weights)
            self.weights = [w / total_weight for w in new_weights]

        self.performance_history.append(performances)

    def get_model_contributions(self) -> Dict[str, float]:
        """Obtiene las contribuciones actuales de cada modelo."""
        return {model_id: weight for model_id, weight in zip(self.model_ids, self.weights)}


class EnsembleManager:
    """
    Gestor completo que combina todas las estrategias de ensemble.
    Permite crear, entrenar y usar múltiples tipos de ensemble.
    """

    def __init__(self):
        self.ensembles: Dict[str, BaseEnsemble] = {}
        self.active_ensemble: Optional[str] = None
        self.performance_metrics: Dict[str, Dict] = {}

    async def create_ensemble(self, ensemble_id: str, ensemble_type: EnsembleType,
                             **kwargs) -> BaseEnsemble:
        """
        Crea un nuevo ensemble.

        Args:
            ensemble_id: ID único del ensemble
            ensemble_type: Tipo de ensemble a crear
            **kwargs: Parámetros específicos del ensemble

        Returns:
            Ensemble creado
        """
        if ensemble_type == EnsembleType.VOTING:
            ensemble = VotingEnsemble(**kwargs)
        elif ensemble_type == EnsembleType.BAGGING:
            ensemble = BaggingEnsemble(**kwargs)
        elif ensemble_type == EnsembleType.BOOSTING:
            ensemble = BoostingEnsemble(**kwargs)
        elif ensemble_type == EnsembleType.STACKING:
            ensemble = StackingEnsemble(**kwargs)
        elif ensemble_type == EnsembleType.WEIGHTED:
            ensemble = WeightedEnsemble(**kwargs)
        else:
            raise ValueError(f"Tipo de ensemble no soportado: {ensemble_type}")

        self.ensembles[ensemble_id] = ensemble
        logger.info(f"Ensemble {ensemble_id} creado: {ensemble_type.value}")
        return ensemble

    async def train_ensemble(self, ensemble_id: str, X: Union[np.ndarray, torch.Tensor],
                           y: Union[np.ndarray, torch.Tensor]) -> None:
        """Entrena un ensemble específico."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} no existe")

        ensemble = self.ensembles[ensemble_id]
        await ensemble.fit(X, y)
        logger.info(f"Ensemble {ensemble_id} entrenado")

    async def predict_with_ensemble(self, ensemble_id: str,
                                  X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción con un ensemble específico."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} no existe")

        ensemble = self.ensembles[ensemble_id]
        result = await ensemble.predict(X)

        # Registrar métricas si es la primera vez
        if ensemble_id not in self.performance_metrics:
            self.performance_metrics[ensemble_id] = {
                'predictions_count': 0,
                'avg_confidence': 0.0
            }

        # Actualizar métricas
        metrics = self.performance_metrics[ensemble_id]
        metrics['predictions_count'] += 1
        metrics['avg_confidence'] = (metrics['avg_confidence'] * (metrics['predictions_count'] - 1) +
                                   result.confidence) / metrics['predictions_count']

        return result

    def set_active_ensemble(self, ensemble_id: str) -> None:
        """Establece el ensemble activo para predicciones rápidas."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} no existe")
        self.active_ensemble = ensemble_id
        logger.info(f"Ensemble activo establecido: {ensemble_id}")

    async def predict(self, X: Union[np.ndarray, torch.Tensor]) -> EnsembleResult:
        """Realiza predicción con el ensemble activo."""
        if self.active_ensemble is None:
            raise ValueError("No hay ensemble activo")
        return await self.predict_with_ensemble(self.active_ensemble, X)

    def get_ensemble_info(self, ensemble_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene información sobre ensembles."""
        if ensemble_id:
            if ensemble_id not in self.ensembles:
                raise ValueError(f"Ensemble {ensemble_id} no existe")
            ensemble = self.ensembles[ensemble_id]
            return {
                'type': ensemble.ensemble_type.value,
                'num_models': len(ensemble.models),
                'is_fitted': ensemble.is_fitted,
                'contributions': ensemble.get_model_contributions(),
                'performance': self.performance_metrics.get(ensemble_id, {})
            }
        else:
            return {
                ensemble_id: self.get_ensemble_info(ensemble_id)
                for ensemble_id in self.ensembles.keys()
            }

    async def compare_ensembles(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Dict]:
        """Compara el rendimiento de todos los ensembles entrenados."""
        results = {}

        for ensemble_id, ensemble in self.ensembles.items():
            if not ensemble.is_fitted:
                continue

            try:
                pred_result = await ensemble.predict(X_test)

                # Calcular métricas
                if hasattr(y_test, '__len__') and len(np.unique(y_test)) > 2:
                    # Regresión
                    mse = mean_squared_error(y_test, pred_result.final_prediction)
                    mae = np.mean(np.abs(y_test - pred_result.final_prediction))
                    results[ensemble_id] = {
                        'type': ensemble.ensemble_type.value,
                        'mse': mse,
                        'mae': mae,
                        'confidence': pred_result.confidence
                    }
                else:
                    # Clasificación
                    accuracy = accuracy_score(y_test, np.argmax(pred_result.final_prediction, axis=1)
                                            if len(pred_result.final_prediction.shape) > 1 else pred_result.final_prediction)
                    results[ensemble_id] = {
                        'type': ensemble.ensemble_type.value,
                        'accuracy': accuracy,
                        'confidence': pred_result.confidence
                    }

            except Exception as e:
                logger.error(f"Error evaluando ensemble {ensemble_id}: {e}")
                results[ensemble_id] = {'error': str(e)}

        return results

    def save_ensemble(self, ensemble_id: str, filepath: str) -> None:
        """Guarda un ensemble en disco."""
        import pickle
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} no existe")

        ensemble = self.ensembles[ensemble_id]
        with open(filepath, 'wb') as f:
            pickle.dump(ensemble, f)
        logger.info(f"Ensemble {ensemble_id} guardado en {filepath}")

    def load_ensemble(self, ensemble_id: str, filepath: str) -> None:
        """Carga un ensemble desde disco."""
        import pickle
        with open(filepath, 'rb') as f:
            ensemble = pickle.load(f)
        self.ensembles[ensemble_id] = ensemble
        logger.info(f"Ensemble {ensemble_id} cargado desde {filepath}")