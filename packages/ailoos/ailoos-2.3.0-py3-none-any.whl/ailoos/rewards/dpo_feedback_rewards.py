"""
Sistema de Recompensas para Feedback DPO (Direct Preference Optimization).

Este módulo implementa un sistema de recompensas tokenizadas para incentivar
la participación de calidad en el feedback de DPO, incluyendo:

- Recompensas basadas en calidad y consistencia de votos
- Penalizaciones por votos fraudulentos
- Estadísticas de participación y calidad
- Dashboard de recompensas por usuario
- Distribución automática de tokens DRACMA
- Integración con dracmaCalculator existente

Beneficio clave: Incentivos tokenizados para participación de calidad en DPO.
Nota: modulo legacy/off-chain; EmpoorioChain via bridge es la fuente real.
"""

import asyncio
import hashlib
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

from ..core.config import get_config
from ..core.logging import get_logger
from .dracma_calculator import dracmaCalculator, RewardCalculation


@dataclass
class FeedbackVote:
    """Representa un voto de feedback en una contribución DPO."""
    voter_id: str
    contribution_id: str
    vote_type: str  # 'quality', 'preference', 'relevance', 'consistency'
    vote_value: int  # 1-5 scale
    timestamp: datetime
    voter_reputation: float = 1.0
    consistency_score: float = 0.0  # Puntaje de consistencia con otros votos
    quality_impact: float = 0.0  # Impacto en la calidad general
    blockchain_hash: Optional[str] = None
    fraud_detected: bool = False


@dataclass
class UserFeedbackStats:
    """Estadísticas de feedback por usuario."""
    user_id: str
    total_votes_cast: int = 0
    quality_score_avg: float = 0.0
    consistency_score_avg: float = 0.0
    total_rewards_earned: float = 0.0
    fraud_incidents: int = 0
    reputation_score: float = 1.0
    last_vote_timestamp: Optional[datetime] = None
    vote_streak: int = 0  # Racha de votos consistentes
    participation_rate: float = 0.0  # Tasa de participación semanal
    leaderboard_rank: int = 0


@dataclass
class FeedbackRewardCalculation:
    """Resultado del cálculo de recompensa por feedback."""
    voter_id: str
    contribution_id: str
    session_id: str
    base_reward: float
    quality_multiplier: float
    consistency_bonus: float
    reputation_multiplier: float
    total_reward: float
    dracma_amount: float
    calculation_hash: str
    timestamp: datetime
    fraud_penalty: float = 0.0


@dataclass
class FeedbackDashboard:
    """Dashboard de recompensas para un usuario."""
    user_id: str
    total_earned: float
    weekly_earned: float
    monthly_earned: float
    current_rank: int
    reputation_score: float
    vote_streak: int
    recent_votes: List[Dict[str, Any]] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    next_milestone: Optional[Dict[str, Any]] = None


class DPOFeedbackRewardsSystem:
    """
    Sistema de recompensas para feedback DPO.

    Gestiona recompensas tokenizadas basadas en la calidad y consistencia
    de los votos de feedback en contribuciones DPO.
    """

    def __init__(self, config=None, dracma_calculator=None):
        """
        Inicializar el sistema de recompensas DPO.

        Args:
            config: Configuración del sistema
            dracma_calculator: Instancia de dracmaCalculator
        """
        self.config = config or get_config()
        self.logger = get_logger(__name__)

        # Componentes principales
        self.dracma_calculator = dracma_calculator or dracmaCalculator()

        # Almacenamiento de datos
        self.feedback_votes: Dict[str, List[FeedbackVote]] = {}  # contribution_id -> votes
        self.user_stats: Dict[str, UserFeedbackStats] = {}
        self.reward_calculations: List[FeedbackRewardCalculation] = []

        # Configuración de recompensas
        self.base_vote_reward = self.config.get('dpo_feedback_base_reward', 0.1)  # DracmaS por voto
        self.quality_bonus_max = self.config.get('dpo_feedback_quality_bonus', 2.0)  # Multiplicador máximo
        self.consistency_bonus_max = self.config.get('dpo_feedback_consistency_bonus', 1.5)
        self.reputation_multiplier_max = self.config.get('dpo_feedback_reputation_max', 3.0)
        self.fraud_penalty_factor = self.config.get('dpo_feedback_fraud_penalty', 0.5)  # 50% reducción

        # Umbrales de calidad
        self.min_consistency_threshold = self.config.get('dpo_feedback_min_consistency', 0.7)
        self.min_quality_threshold = self.config.get('dpo_feedback_min_quality', 0.6)
        self.fraud_detection_threshold = self.config.get('dpo_feedback_fraud_threshold', 0.8)

        # Estadísticas del sistema
        self.stats = {
            'total_votes_processed': 0,
            'total_rewards_distributed': 0.0,
            'fraud_cases_detected': 0,
            'active_voters': 0,
            'average_quality_score': 0.0,
            'average_consistency_score': 0.0
        }

        self.logger.info("🚀 DPO Feedback Rewards System inicializado")

    async def submit_feedback_vote(
        self,
        voter_id: str,
        contribution_id: str,
        session_id: str,
        vote_type: str,
        vote_value: int,
        voter_reputation: float = 1.0
    ) -> FeedbackRewardCalculation:
        """
        Enviar un voto de feedback y calcular recompensa.

        Args:
            voter_id: ID del votante
            contribution_id: ID de la contribución DPO
            session_id: ID de la sesión DPO
            vote_type: Tipo de voto ('quality', 'preference', 'relevance', 'consistency')
            vote_value: Valor del voto (1-5)
            voter_reputation: Reputación del votante

        Returns:
            Cálculo de recompensa por el voto
        """
        try:
            # Validar parámetros
            if vote_type not in ['quality', 'preference', 'relevance', 'consistency']:
                raise ValueError(f"Tipo de voto inválido: {vote_type}")
            if not (1 <= vote_value <= 5):
                raise ValueError(f"Valor de voto fuera de rango: {vote_value}")

            # Crear voto de feedback
            vote = FeedbackVote(
                voter_id=voter_id,
                contribution_id=contribution_id,
                vote_type=vote_type,
                vote_value=vote_value,
                timestamp=datetime.now(),
                voter_reputation=voter_reputation
            )

            # Calcular métricas de calidad y consistencia
            await self._calculate_vote_quality_metrics(vote)

            # Detectar fraude
            vote.fraud_detected = self._detect_vote_fraud(vote)

            # Almacenar voto
            if contribution_id not in self.feedback_votes:
                self.feedback_votes[contribution_id] = []
            self.feedback_votes[contribution_id].append(vote)

            # Calcular recompensa
            reward_calc = await self._calculate_feedback_reward(vote, session_id)

            # Aplicar penalización por fraude si detectado
            if vote.fraud_detected:
                reward_calc.fraud_penalty = reward_calc.total_reward * self.fraud_penalty_factor
                reward_calc.total_reward -= reward_calc.fraud_penalty
                reward_calc.dracma_amount = reward_calc.total_reward

                # Actualizar estadísticas de fraude
                self.stats['fraud_cases_detected'] += 1
                await self._handle_fraud_penalty(voter_id)

            # Almacenar cálculo
            self.reward_calculations.append(reward_calc)

            # Actualizar estadísticas del usuario
            await self._update_user_feedback_stats(voter_id, vote, reward_calc)

            # Actualizar estadísticas globales
            self.stats['total_votes_processed'] += 1
            self.stats['total_rewards_distributed'] += reward_calc.dracma_amount

            # Distribuir recompensa automáticamente
            await self._distribute_reward(reward_calc)

            self.logger.info(f"✅ Voto de feedback procesado: {voter_id} -> {contribution_id}, "
                           f"recompensa: {reward_calc.dracma_amount:.4f} DRACMA")

            return reward_calc

        except Exception as e:
            self.logger.error(f"Error procesando voto de feedback: {e}")
            raise

    async def get_user_feedback_dashboard(self, user_id: str) -> FeedbackDashboard:
        """
        Obtener dashboard de recompensas para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dashboard con estadísticas y recompensas
        """
        try:
            # Obtener estadísticas del usuario
            user_stats = await self._get_or_create_user_stats(user_id)

            # Calcular recompensas por período
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            weekly_rewards = sum(
                calc.dracma_amount
                for calc in self.reward_calculations
                if calc.voter_id == user_id and calc.timestamp >= week_ago
            )

            monthly_rewards = sum(
                calc.dracma_amount
                for calc in self.reward_calculations
                if calc.voter_id == user_id and calc.timestamp >= month_ago
            )

            # Obtener votos recientes
            recent_votes = []
            user_calculations = [
                calc for calc in self.reward_calculations
                if calc.voter_id == user_id
            ][-10:]  # Últimos 10

            for calc in user_calculations:
                recent_votes.append({
                    'contribution_id': calc.contribution_id,
                    'reward_amount': calc.dracma_amount,
                    'timestamp': calc.timestamp.isoformat(),
                    'quality_multiplier': calc.quality_multiplier
                })

            # Calcular logros
            achievements = self._calculate_user_achievements(user_stats)

            # Próximo hito
            next_milestone = self._calculate_next_milestone(user_stats)

            # Ranking (simplificado - en producción usaría una clasificación real)
            current_rank = await self._calculate_user_rank(user_id)

            return FeedbackDashboard(
                user_id=user_id,
                total_earned=user_stats.total_rewards_earned,
                weekly_earned=weekly_rewards,
                monthly_earned=monthly_rewards,
                current_rank=current_rank,
                reputation_score=user_stats.reputation_score,
                vote_streak=user_stats.vote_streak,
                recent_votes=recent_votes,
                achievements=achievements,
                next_milestone=next_milestone
            )

        except Exception as e:
            self.logger.error(f"Error obteniendo dashboard para {user_id}: {e}")
            return FeedbackDashboard(
                user_id=user_id,
                total_earned=0.0,
                weekly_earned=0.0,
                monthly_earned=0.0,
                current_rank=0,
                reputation_score=1.0,
                vote_streak=0
            )

    async def get_feedback_quality_stats(self, contribution_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de calidad para una contribución.

        Args:
            contribution_id: ID de la contribución

        Returns:
            Estadísticas de calidad del feedback
        """
        try:
            votes = self.feedback_votes.get(contribution_id, [])

            if not votes:
                return {
                    'contribution_id': contribution_id,
                    'total_votes': 0,
                    'average_quality': 0.0,
                    'average_consistency': 0.0,
                    'fraud_votes': 0,
                    'quality_distribution': {}
                }

            # Calcular métricas
            quality_scores = [v.quality_impact for v in votes]
            consistency_scores = [v.consistency_score for v in votes]
            fraud_votes = sum(1 for v in votes if v.fraud_detected)

            # Distribución de calidad
            quality_distribution = {}
            for vote in votes:
                key = f"quality_{vote.vote_value}"
                quality_distribution[key] = quality_distribution.get(key, 0) + 1

            return {
                'contribution_id': contribution_id,
                'total_votes': len(votes),
                'average_quality': statistics.mean(quality_scores) if quality_scores else 0.0,
                'average_consistency': statistics.mean(consistency_scores) if consistency_scores else 0.0,
                'fraud_votes': fraud_votes,
                'quality_distribution': quality_distribution,
                'quality_variance': statistics.variance(quality_scores) if len(quality_scores) > 1 else 0.0
            }

        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de calidad: {e}")
            return {}

    def get_system_feedback_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas globales del sistema de feedback.

        Returns:
            Estadísticas del sistema
        """
        try:
            stats = self.stats.copy()

            # Calcular métricas adicionales
            if stats['total_votes_processed'] > 0:
                stats['fraud_rate'] = stats['fraud_cases_detected'] / stats['total_votes_processed']
                stats['average_reward_per_vote'] = stats['total_rewards_distributed'] / stats['total_votes_processed']
            else:
                stats['fraud_rate'] = 0.0
                stats['average_reward_per_vote'] = 0.0

            # Estadísticas de usuarios activos
            active_users = len([u for u in self.user_stats.values() if u.total_votes_cast > 0])
            stats['active_voters'] = active_users

            # Calcular promedios de calidad y consistencia
            if self.reward_calculations:
                quality_scores = [calc.quality_multiplier for calc in self.reward_calculations]
                stats['average_quality_score'] = statistics.mean(quality_scores)

            return stats

        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del sistema: {e}")
            return self.stats.copy()

    # Métodos privados de implementación

    async def _calculate_vote_quality_metrics(self, vote: FeedbackVote):
        """Calcular métricas de calidad y consistencia para un voto."""
        try:
            contribution_votes = self.feedback_votes.get(vote.contribution_id, [])

            if not contribution_votes:
                # Primer voto - calidad máxima por defecto
                vote.quality_impact = 1.0
                vote.consistency_score = 1.0
                return

            # Calcular impacto en calidad
            # Basado en desviación del consenso
            vote_values = [v.vote_value for v in contribution_votes if v.vote_type == vote.vote_type]
            if vote_values:
                consensus = statistics.mean(vote_values)
                deviation = abs(vote.vote_value - consensus)
                max_deviation = 2.0  # Máxima desviación posible en escala 1-5
                vote.quality_impact = max(0.0, 1.0 - (deviation / max_deviation))
            else:
                vote.quality_impact = 0.8  # Valor por defecto para nuevos tipos de voto

            # Calcular consistencia con votos previos del mismo usuario
            user_previous_votes = []
            for contrib_votes in self.feedback_votes.values():
                for prev_vote in contrib_votes:
                    if prev_vote.voter_id == vote.voter_id and prev_vote.vote_type == vote.vote_type:
                        user_previous_votes.append(prev_vote.vote_value)

            if len(user_previous_votes) >= 3:
                # Calcular consistencia basada en varianza de votos previos
                if len(set(user_previous_votes)) == 1:
                    # Todos los votos previos iguales - alta consistencia
                    vote.consistency_score = 1.0
                else:
                    # Calcular consistencia basada en patrón
                    consistency = 1.0 - (statistics.variance(user_previous_votes) / 4.0)  # Normalizado
                    vote.consistency_score = max(0.0, min(1.0, consistency))
            else:
                vote.consistency_score = 0.7  # Valor por defecto para nuevos votantes

        except Exception as e:
            self.logger.error(f"Error calculando métricas de calidad: {e}")
            vote.quality_impact = 0.5
            vote.consistency_score = 0.5

    def _detect_vote_fraud(self, vote: FeedbackVote) -> bool:
        """Detectar posibles fraudes en un voto."""
        try:
            # Verificar si el votante ha votado consistentemente de manera sospechosa
            user_votes = []
            for contrib_votes in self.feedback_votes.values():
                user_votes.extend([v for v in contrib_votes if v.voter_id == vote.voter_id])

            if len(user_votes) < 5:
                return False  # No suficiente historial

            # Detectar patrones fraudulentos
            vote_values = [v.vote_value for v in user_votes]

            # 1. Todos los votos son idénticos (muy sospechoso)
            if len(set(vote_values)) == 1 and len(user_votes) > 10:
                return True

            # 2. Varianza extremadamente baja
            if len(vote_values) > 5 and statistics.variance(vote_values) < 0.1:
                return True

            # 3. Patrón repetitivo sospechoso
            if len(user_votes) > 20:
                # Verificar si los últimos 10 votos siguen un patrón muy predecible
                recent_votes = vote_values[-10:]
                if self._is_suspicious_pattern(recent_votes):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error detectando fraude: {e}")
            return False

    def _is_suspicious_pattern(self, votes: List[int]) -> bool:
        """Detectar patrones sospechosos en una secuencia de votos."""
        if len(votes) < 5:
            return False

        # Contar frecuencia de cada valor
        from collections import Counter
        freq = Counter(votes)

        # Si un valor aparece más del 80% del tiempo
        max_freq = max(freq.values())
        if max_freq / len(votes) > 0.8:
            return True

        # Verificar alternancia sospechosa (ej: 1,5,1,5,1,5...)
        if len(votes) >= 6:
            alternating = True
            for i in range(2, len(votes)):
                if votes[i] == votes[i-2]:
                    continue
                else:
                    alternating = False
                    break
            if alternating:
                return True

        return False

    async def _calculate_feedback_reward(
        self,
        vote: FeedbackVote,
        session_id: str
    ) -> FeedbackRewardCalculation:
        """Calcular recompensa por un voto de feedback."""
        try:
            # Recompensa base
            base_reward = self.base_vote_reward

            # Multiplicador de calidad
            quality_multiplier = 1.0 + (vote.quality_impact * (self.quality_bonus_max - 1.0))

            # Bonus de consistencia
            consistency_bonus = 1.0
            if vote.consistency_score >= self.min_consistency_threshold:
                consistency_bonus = 1.0 + (vote.consistency_score * (self.consistency_bonus_max - 1.0))

            # Multiplicador de reputación
            reputation_multiplier = min(self.reputation_multiplier_max,
                                      1.0 + (vote.voter_reputation - 1.0))

            # Calcular recompensa total
            total_reward = base_reward * quality_multiplier * consistency_bonus * reputation_multiplier

            # Aplicar límites
            total_reward = min(total_reward, self.base_vote_reward * 5.0)  # Máximo 5x la base

            # Convertir a DracmaS (1:1 por simplicidad)
            dracma_amount = total_reward

            # Crear hash de cálculo
            calculation_hash = self._generate_reward_calculation_hash(vote, total_reward)

            return FeedbackRewardCalculation(
                voter_id=vote.voter_id,
                contribution_id=vote.contribution_id,
                session_id=session_id,
                base_reward=base_reward,
                quality_multiplier=quality_multiplier,
                consistency_bonus=consistency_bonus,
                reputation_multiplier=reputation_multiplier,
                total_reward=total_reward,
                dracma_amount=dracma_amount,
                calculation_hash=calculation_hash,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error calculando recompensa: {e}")
            # Retornar cálculo mínimo en caso de error
            return FeedbackRewardCalculation(
                voter_id=vote.voter_id,
                contribution_id=vote.contribution_id,
                session_id=session_id,
                base_reward=0.0,
                quality_multiplier=1.0,
                consistency_bonus=1.0,
                reputation_multiplier=1.0,
                total_reward=0.0,
                dracma_amount=0.0,
                calculation_hash="",
                timestamp=datetime.now()
            )

    def _generate_reward_calculation_hash(self, vote: FeedbackVote, total_reward: float) -> str:
        """Generar hash criptográfico para el cálculo de recompensa."""
        data = {
            'voter_id': vote.voter_id,
            'contribution_id': vote.contribution_id,
            'vote_type': vote.vote_type,
            'vote_value': vote.vote_value,
            'quality_impact': vote.quality_impact,
            'consistency_score': vote.consistency_score,
            'total_reward': total_reward,
            'timestamp': vote.timestamp.isoformat()
        }

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    async def _handle_fraud_penalty(self, voter_id: str):
        """Manejar penalización por detección de fraude."""
        try:
            user_stats = await self._get_or_create_user_stats(voter_id)
            user_stats.fraud_incidents += 1
            user_stats.reputation_score *= (1 - self.fraud_penalty_factor)

            # Resetear racha de votos
            user_stats.vote_streak = 0

            self.logger.warning(f"🚨 Penalización aplicada por fraude a usuario {voter_id}")

        except Exception as e:
            self.logger.error(f"Error aplicando penalización por fraude: {e}")

    async def _update_user_feedback_stats(
        self,
        voter_id: str,
        vote: FeedbackVote,
        reward_calc: FeedbackRewardCalculation
    ):
        """Actualizar estadísticas de feedback del usuario."""
        try:
            user_stats = await self._get_or_create_user_stats(voter_id)

            # Actualizar contadores
            user_stats.total_votes_cast += 1
            user_stats.total_rewards_earned += reward_calc.dracma_amount
            user_stats.last_vote_timestamp = vote.timestamp

            # Actualizar promedios de calidad y consistencia
            if user_stats.total_votes_cast == 1:
                user_stats.quality_score_avg = vote.quality_impact
                user_stats.consistency_score_avg = vote.consistency_score
            else:
                user_stats.quality_score_avg = (
                    (user_stats.quality_score_avg * (user_stats.total_votes_cast - 1)) +
                    vote.quality_impact
                ) / user_stats.total_votes_cast

                user_stats.consistency_score_avg = (
                    (user_stats.consistency_score_avg * (user_stats.total_votes_cast - 1)) +
                    vote.consistency_score
                ) / user_stats.total_votes_cast

            # Actualizar racha de votos consistentes
            if vote.consistency_score >= self.min_consistency_threshold:
                user_stats.vote_streak += 1
            else:
                user_stats.vote_streak = 0

            # Actualizar tasa de participación (últimos 7 días)
            week_ago = datetime.now() - timedelta(days=7)
            recent_votes = sum(
                1 for calc in self.reward_calculations
                if calc.voter_id == voter_id and calc.timestamp >= week_ago
            )
            user_stats.participation_rate = recent_votes / 7.0  # votos por día

        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas de usuario: {e}")

    async def _get_or_create_user_stats(self, user_id: str) -> UserFeedbackStats:
        """Obtener o crear estadísticas para un usuario."""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = UserFeedbackStats(user_id=user_id)
        return self.user_stats[user_id]

    async def _distribute_reward(self, reward_calc: FeedbackRewardCalculation):
        """Distribuir recompensa usando dracmaCalculator."""
        try:
            # Crear contribución para el calculador (adaptada para feedback)
            node_contribution = type('NodeContribution', (), {
                'node_id': reward_calc.voter_id,
                'session_id': reward_calc.session_id,
                'round_number': 1,
                'parameters_trained': int(reward_calc.quality_multiplier * 100),
                'data_samples': 1,  # Un voto
                'training_time_seconds': 0.1,  # Tiempo mínimo
                'model_accuracy': reward_calc.quality_multiplier,
                'hardware_specs': {},
                'timestamp': reward_calc.timestamp,
                'proof_of_work': None
            })()

            # Usar el calculador existente para distribución
            await self.dracma_calculator.add_contribution(node_contribution)

            # Calcular y distribuir usando el sistema existente
            session_rewards = await self.dracma_calculator.calculate_session_rewards(reward_calc.session_id)
            if session_rewards:
                await self.dracma_calculator.distribute_rewards(session_rewards)

        except Exception as e:
            self.logger.error(f"Error distribuyendo recompensa: {e}")

    def _calculate_user_achievements(self, user_stats: UserFeedbackStats) -> List[str]:
        """Calcular logros del usuario."""
        achievements = []

        if user_stats.total_votes_cast >= 100:
            achievements.append("Votante Experto")
        if user_stats.total_votes_cast >= 1000:
            achievements.append("Votante Maestro")

        if user_stats.consistency_score_avg >= 0.9:
            achievements.append("Votante Consistente")
        if user_stats.quality_score_avg >= 0.85:
            achievements.append("Votante de Calidad")

        if user_stats.vote_streak >= 50:
            achievements.append("Racha Dorada")
        if user_stats.reputation_score >= 2.0:
            achievements.append("Reputación Elite")

        if user_stats.fraud_incidents == 0 and user_stats.total_votes_cast >= 50:
            achievements.append("Votante Confiable")

        return achievements

    def _calculate_next_milestone(self, user_stats: UserFeedbackStats) -> Optional[Dict[str, Any]]:
        """Calcular próximo hito para el usuario."""
        try:
            # Definir hitos por votos
            vote_milestones = [10, 50, 100, 500, 1000, 5000]
            current_votes = user_stats.total_votes_cast

            for milestone in vote_milestones:
                if current_votes < milestone:
                    remaining = milestone - current_votes
                    return {
                        'type': 'votes',
                        'target': milestone,
                        'remaining': remaining,
                        'description': f"Alcanza {milestone} votos totales"
                    }

            # Hito por recompensas acumuladas
            reward_milestones = [1.0, 5.0, 10.0, 50.0, 100.0]
            current_rewards = user_stats.total_rewards_earned

            for milestone in reward_milestones:
                if current_rewards < milestone:
                    remaining = milestone - current_rewards
                    return {
                        'type': 'rewards',
                        'target': milestone,
                        'remaining': remaining,
                        'description': f"Gana {milestone} DracmaS en total"
                    }

            # Hito por racha
            streak_milestones = [10, 25, 50, 100]
            current_streak = user_stats.vote_streak

            for milestone in streak_milestones:
                if current_streak < milestone:
                    remaining = milestone - current_streak
                    return {
                        'type': 'streak',
                        'target': milestone,
                        'remaining': remaining,
                        'description': f"Alcanza una racha de {milestone} votos consistentes"
                    }

            return None  # Todos los hitos completados

        except Exception as e:
            self.logger.error(f"Error calculando próximo hito: {e}")
            return None

    async def _calculate_user_rank(self, user_id: str) -> int:
        """Calcular ranking del usuario (simplificado)."""
        try:
            # En producción, esto sería más sofisticado con base de datos
            all_users = list(self.user_stats.values())
            sorted_users = sorted(all_users, key=lambda u: u.total_rewards_earned, reverse=True)

            for rank, user in enumerate(sorted_users, 1):
                if user.user_id == user_id:
                    return rank

            return len(sorted_users) + 1

        except Exception as e:
            self.logger.error(f"Error calculando ranking: {e}")
            return 0
