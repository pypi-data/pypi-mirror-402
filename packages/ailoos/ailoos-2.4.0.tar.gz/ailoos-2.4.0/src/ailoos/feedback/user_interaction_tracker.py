"""
UserInteractionTracker - Seguimiento de interacciones usuario-modelo
===================================================================

Este módulo proporciona funcionalidades para rastrear y analizar
interacciones entre usuarios y el modelo EmpoorioLM, recopilando
datos para feedback automático y análisis de comportamiento.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
import json

logger = logging.getLogger(__name__)


@dataclass
class UserInteraction:
    """Interacción individual usuario-modelo."""
    interaction_id: str
    user_id: Optional[int]
    session_id: str
    timestamp: datetime

    # Datos de entrada
    user_query: str
    query_type: str  # 'text', 'voice', 'image', etc.
    query_length: int
    query_complexity: float  # 0.0 - 1.0

    # Datos de respuesta
    model_response: str
    response_time: float  # segundos
    response_length: int
    model_version: Optional[str]
    tokens_used: Optional[int]

    # Feedback automático
    user_satisfaction_score: Optional[float]  # 0.0 - 1.0, basado en heurísticas
    interaction_quality_score: Optional[float]  # 0.0 - 1.0

    # Metadatos
    channel: str  # 'api', 'web', 'mobile', etc.
    user_agent: Optional[str]
    ip_hash: Optional[str]  # Anonimizado
    error_occurred: bool = False
    error_type: Optional[str] = None

    # Análisis adicional
    topics_identified: List[str] = field(default_factory=list)
    sentiment_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la interacción a diccionario."""
        return {
            "interaction_id": self.interaction_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "user_query": self.user_query,
            "query_type": self.query_type,
            "query_length": self.query_length,
            "query_complexity": self.query_complexity,
            "model_response": self.model_response,
            "response_time": self.response_time,
            "response_length": self.response_length,
            "model_version": self.model_version,
            "tokens_used": self.tokens_used,
            "user_satisfaction_score": self.user_satisfaction_score,
            "interaction_quality_score": self.interaction_quality_score,
            "channel": self.channel,
            "user_agent": self.user_agent,
            "ip_hash": self.ip_hash,
            "error_occurred": self.error_occurred,
            "error_type": self.error_type,
            "topics_identified": self.topics_identified,
            "sentiment_analysis": self.sentiment_analysis
        }


@dataclass
class SessionSummary:
    """Resumen de una sesión de usuario."""
    session_id: str
    user_id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    total_interactions: int
    average_response_time: float
    average_satisfaction: Optional[float]
    topics_discussed: List[str]
    channel: str
    total_tokens_used: int
    errors_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resumen a diccionario."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_interactions": self.total_interactions,
            "average_response_time": self.average_response_time,
            "average_satisfaction": self.average_satisfaction,
            "topics_discussed": self.topics_discussed,
            "channel": self.channel,
            "total_tokens_used": self.total_tokens_used,
            "errors_count": self.errors_count
        }


class UserInteractionTracker:
    """
    Rastreador de interacciones usuario-modelo.

    Registra todas las interacciones, calcula métricas automáticas
    y proporciona insights sobre el comportamiento del usuario.
    """

    def __init__(self):
        """Inicializa el rastreador de interacciones."""
        self.interactions: List[UserInteraction] = []
        self.active_sessions: Dict[str, SessionSummary] = {}
        self.interaction_counter = 0

        # Configuración para análisis automático
        self.enable_auto_analysis = True
        self.max_interactions_stored = 10000  # Limitar memoria

        logger.info("UserInteractionTracker inicializado")

    def track_interaction(self, user_query: str, model_response: str,
                         response_time: float, user_id: Optional[int] = None,
                         session_id: Optional[str] = None, channel: str = "api",
                         query_type: str = "text", model_version: Optional[str] = None,
                         tokens_used: Optional[int] = None, user_agent: Optional[str] = None,
                         ip_hash: Optional[str] = None, error_occurred: bool = False,
                         error_type: Optional[str] = None) -> str:
        """
        Registra una nueva interacción usuario-modelo.

        Args:
            user_query: Consulta del usuario
            model_response: Respuesta del modelo
            response_time: Tiempo de respuesta en segundos
            user_id: ID del usuario (opcional)
            session_id: ID de sesión (opcional, se genera si no se proporciona)
            channel: Canal de interacción
            query_type: Tipo de consulta
            model_version: Versión del modelo
            tokens_used: Tokens utilizados
            user_agent: User agent del cliente
            ip_hash: Hash anonimizado de IP
            error_occurred: Si ocurrió un error
            error_type: Tipo de error

        Returns:
            ID único de la interacción
        """
        # Generar IDs si no se proporcionan
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        interaction_id = f"int_{self.interaction_counter}_{int(datetime.now().timestamp())}"
        self.interaction_counter += 1

        # Calcular métricas automáticas
        query_length = len(user_query)
        response_length = len(model_response)
        query_complexity = self._calculate_query_complexity(user_query)

        # Análisis automático si está habilitado
        user_satisfaction = None
        interaction_quality = None
        topics = []
        sentiment = {}

        if self.enable_auto_analysis:
            user_satisfaction = self._calculate_user_satisfaction(
                user_query, model_response, response_time, error_occurred
            )
            interaction_quality = self._calculate_interaction_quality(
                response_time, error_occurred, query_complexity
            )
            topics = self._identify_topics(user_query)
            sentiment = self._analyze_sentiment(user_query)

        # Crear interacción
        interaction = UserInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            user_query=user_query,
            query_type=query_type,
            query_length=query_length,
            query_complexity=query_complexity,
            model_response=model_response,
            response_time=response_time,
            response_length=response_length,
            model_version=model_version,
            tokens_used=tokens_used,
            user_satisfaction_score=user_satisfaction,
            interaction_quality_score=interaction_quality,
            channel=channel,
            user_agent=user_agent,
            ip_hash=ip_hash,
            error_occurred=error_occurred,
            error_type=error_type,
            topics_identified=topics,
            sentiment_analysis=sentiment
        )

        # Almacenar interacción
        self.interactions.append(interaction)

        # Actualizar resumen de sesión
        self._update_session_summary(interaction)

        # Limitar memoria
        if len(self.interactions) > self.max_interactions_stored:
            # Remover interacciones más antiguas
            remove_count = len(self.interactions) - self.max_interactions_stored
            self.interactions = self.interactions[remove_count:]
            logger.info(f"Removidas {remove_count} interacciones antiguas para limitar memoria")

        logger.info(f"Interacción registrada: {interaction_id} (usuario: {user_id}, sesión: {session_id})")

        return interaction_id

    def _calculate_query_complexity(self, query: str) -> float:
        """
        Calcula la complejidad de una consulta.

        Args:
            query: Consulta del usuario

        Returns:
            Puntuación de complejidad (0.0 - 1.0)
        """
        if not query:
            return 0.0

        # Factores de complejidad
        length_score = min(len(query) / 500, 1.0)  # Longitud máxima esperada

        # Palabras técnicas/complejas
        technical_words = ['algoritmo', 'implementar', 'optimizar', 'complejidad', 'paradigma',
                          'arquitectura', 'framework', 'biblioteca', 'deployment', 'escalabilidad']
        technical_count = sum(1 for word in technical_words if word.lower() in query.lower())
        technical_score = min(technical_count / 5, 1.0)

        # Preguntas complejas (¿cómo?, ¿por qué?, ¿cuál es?)
        question_words = ['cómo', 'por qué', 'cuál', 'qué', 'dónde', 'cuándo', 'quién']
        question_score = 0.5 if any(word in query.lower() for word in question_words) else 0.0

        # Puntuación combinada
        complexity = (length_score * 0.4 + technical_score * 0.4 + question_score * 0.2)

        return min(complexity, 1.0)

    def _calculate_user_satisfaction(self, query: str, response: str,
                                   response_time: float, error: bool) -> float:
        """
        Calcula satisfacción estimada del usuario basada en heurísticas.

        Args:
            query: Consulta del usuario
            response: Respuesta del modelo
            response_time: Tiempo de respuesta
            error: Si hubo error

        Returns:
            Puntuación de satisfacción (0.0 - 1.0)
        """
        if error:
            return 0.2  # Baja satisfacción si hay error

        score = 0.5  # Base neutral

        # Penalizar tiempos largos
        if response_time > 10:
            score -= 0.2
        elif response_time > 5:
            score -= 0.1
        elif response_time < 2:
            score += 0.1  # Bonus por rapidez

        # Evaluar calidad de respuesta
        response_length = len(response)
        if response_length < 10:
            score -= 0.3  # Respuestas muy cortas
        elif response_length > 1000:
            score -= 0.1  # Respuestas muy largas
        else:
            score += 0.1  # Longitud adecuada

        # Verificar si la respuesta parece relevante
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words.intersection(response_words))
        relevance_score = min(overlap / len(query_words), 1.0) if query_words else 0.0
        score += relevance_score * 0.2

        return max(0.0, min(1.0, score))

    def _calculate_interaction_quality(self, response_time: float,
                                     error: bool, query_complexity: float) -> float:
        """
        Calcula calidad de la interacción.

        Args:
            response_time: Tiempo de respuesta
            error: Si hubo error
            query_complexity: Complejidad de la consulta

        Returns:
            Puntuación de calidad (0.0 - 1.0)
        """
        if error:
            return 0.1

        # Base según tiempo de respuesta
        if response_time < 1:
            base_score = 1.0
        elif response_time < 3:
            base_score = 0.9
        elif response_time < 5:
            base_score = 0.8
        elif response_time < 10:
            base_score = 0.6
        else:
            base_score = 0.4

        # Ajustar por complejidad (consultas complejas pueden tomar más tiempo)
        complexity_adjustment = query_complexity * 0.1
        base_score += complexity_adjustment

        return min(1.0, base_score)

    def _identify_topics(self, query: str) -> List[str]:
        """
        Identifica temas/topics en la consulta.

        Args:
            query: Consulta del usuario

        Returns:
            Lista de temas identificados
        """
        query_lower = query.lower()
        topics = []

        # Mapas de palabras clave a temas
        topic_keywords = {
            "programación": ["programar", "código", "python", "javascript", "java", "algoritmo", "función"],
            "machine_learning": ["ml", "aprendizaje", "neurona", "entrenar", "modelo", "predicción"],
            "web_development": ["web", "html", "css", "javascript", "react", "frontend", "backend"],
            "data_science": ["datos", "estadística", "visualización", "pandas", "numpy", "matplotlib"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment", "aws", "azure", "cloud"],
            "seguridad": ["seguridad", "ciberseguridad", "encriptación", "autenticación", "vulnerabilidad"],
            "matemáticas": ["matemática", "álgebra", "cálculo", "geometría", "estadística", "probabilidad"],
            "ciencia": ["física", "química", "biología", "investigación", "experimento"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)

        return topics[:3]  # Máximo 3 temas por consulta

    def _analyze_sentiment(self, query: str) -> Dict[str, Any]:
        """
        Análisis simple de sentimiento de la consulta.

        Args:
            query: Consulta del usuario

        Returns:
            Diccionario con análisis de sentimiento
        """
        query_lower = query.lower()

        # Palabras positivas y negativas simples
        positive_words = ["bueno", "excelente", "genial", "ayuda", "gracias", "perfecto", "útil"]
        negative_words = ["malo", "terrible", "error", "problema", "falla", "lento", "confuso"]

        positive_count = sum(1 for word in positive_words if word in query_lower)
        negative_count = sum(1 for word in negative_words if word in query_lower)

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            sentiment = "neutral"
            score = 0.5
        else:
            sentiment_ratio = positive_count / total_sentiment_words
            if sentiment_ratio > 0.6:
                sentiment = "positive"
                score = sentiment_ratio
            elif sentiment_ratio < 0.4:
                sentiment = "negative"
                score = 1 - sentiment_ratio
            else:
                sentiment = "neutral"
                score = 0.5

        return {
            "sentiment": sentiment,
            "score": score,
            "positive_words": positive_count,
            "negative_words": negative_count
        }

    def _update_session_summary(self, interaction: UserInteraction):
        """
        Actualiza el resumen de la sesión con la nueva interacción.

        Args:
            interaction: Nueva interacción
        """
        session_id = interaction.session_id

        if session_id not in self.active_sessions:
            # Crear nuevo resumen de sesión
            self.active_sessions[session_id] = SessionSummary(
                session_id=session_id,
                user_id=interaction.user_id,
                start_time=interaction.timestamp,
                end_time=None,
                total_interactions=0,
                average_response_time=0.0,
                average_satisfaction=None,
                topics_discussed=[],
                channel=interaction.channel,
                total_tokens_used=0,
                errors_count=0
            )

        summary = self.active_sessions[session_id]

        # Actualizar estadísticas
        summary.total_interactions += 1
        summary.end_time = interaction.timestamp

        # Actualizar promedio de tiempo de respuesta
        old_avg = summary.average_response_time
        new_count = summary.total_interactions
        summary.average_response_time = ((old_avg * (new_count - 1)) + interaction.response_time) / new_count

        # Actualizar satisfacción promedio
        if interaction.user_satisfaction_score is not None:
            if summary.average_satisfaction is None:
                summary.average_satisfaction = interaction.user_satisfaction_score
            else:
                old_avg_sat = summary.average_satisfaction
                summary.average_satisfaction = ((old_avg_sat * (new_count - 1)) + interaction.user_satisfaction_score) / new_count

        # Agregar temas nuevos
        for topic in interaction.topics_identified:
            if topic not in summary.topics_discussed:
                summary.topics_discussed.append(topic)

        # Actualizar tokens y errores
        if interaction.tokens_used:
            summary.total_tokens_used += interaction.tokens_used

        if interaction.error_occurred:
            summary.errors_count += 1

    def end_session(self, session_id: str):
        """
        Marca una sesión como terminada.

        Args:
            session_id: ID de la sesión
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id].end_time = datetime.now()
            logger.info(f"Sesión terminada: {session_id}")

    def get_interactions(self, limit: Optional[int] = None,
                        user_id: Optional[int] = None,
                        session_id: Optional[str] = None) -> List[UserInteraction]:
        """
        Obtiene interacciones con filtros opcionales.

        Args:
            limit: Número máximo de interacciones
            user_id: Filtrar por usuario
            session_id: Filtrar por sesión

        Returns:
            Lista de interacciones
        """
        interactions = self.interactions

        if user_id is not None:
            interactions = [i for i in interactions if i.user_id == user_id]

        if session_id:
            interactions = [i for i in interactions if i.session_id == session_id]

        if limit:
            interactions = interactions[-limit:]

        return interactions.copy()

    def get_session_summaries(self, active_only: bool = False) -> List[SessionSummary]:
        """
        Obtiene resúmenes de sesiones.

        Args:
            active_only: Solo sesiones activas

        Returns:
            Lista de resúmenes de sesiones
        """
        summaries = list(self.active_sessions.values())

        if active_only:
            summaries = [s for s in summaries if s.end_time is None]

        return summaries

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un usuario específico.

        Args:
            user_id: ID del usuario

        Returns:
            Estadísticas del usuario
        """
        user_interactions = self.get_interactions(user_id=user_id)

        if not user_interactions:
            return {"error": "User not found"}

        total_interactions = len(user_interactions)
        avg_response_time = sum(i.response_time for i in user_interactions) / total_interactions
        avg_satisfaction = sum(i.user_satisfaction_score for i in user_interactions
                              if i.user_satisfaction_score is not None) / total_interactions

        # Sesiones del usuario
        user_sessions = set(i.session_id for i in user_interactions)
        total_sessions = len(user_sessions)

        # Temas más discutidos
        all_topics = []
        for interaction in user_interactions:
            all_topics.extend(interaction.topics_identified)

        topic_counts = defaultdict(int)
        for topic in all_topics:
            topic_counts[topic] += 1

        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "user_id": user_id,
            "total_interactions": total_interactions,
            "total_sessions": total_sessions,
            "average_response_time": avg_response_time,
            "average_satisfaction": avg_satisfaction,
            "top_topics": dict(top_topics),
            "channels_used": list(set(i.channel for i in user_interactions)),
            "error_rate": sum(1 for i in user_interactions if i.error_occurred) / total_interactions
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales de todas las interacciones.

        Returns:
            Estadísticas globales
        """
        if not self.interactions:
            return {"error": "No interactions recorded"}

        total_interactions = len(self.interactions)
        unique_users = len(set(i.user_id for i in self.interactions if i.user_id))
        unique_sessions = len(set(i.session_id for i in self.interactions))

        avg_response_time = sum(i.response_time for i in self.interactions) / total_interactions

        satisfactions = [i.user_satisfaction_score for i in self.interactions if i.user_satisfaction_score is not None]
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else None

        error_rate = sum(1 for i in self.interactions if i.error_occurred) / total_interactions

        # Canales más usados
        channel_counts = defaultdict(int)
        for interaction in self.interactions:
            channel_counts[interaction.channel] += 1

        # Tipos de consulta
        query_type_counts = defaultdict(int)
        for interaction in self.interactions:
            query_type_counts[interaction.query_type] += 1

        return {
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "average_response_time": avg_response_time,
            "average_satisfaction": avg_satisfaction,
            "error_rate": error_rate,
            "channels": dict(channel_counts),
            "query_types": dict(query_type_counts),
            "time_range": {
                "start": min(i.timestamp for i in self.interactions).isoformat(),
                "end": max(i.timestamp for i in self.interactions).isoformat()
            }
        }

    def export_interactions(self, filename: str = "user_interactions.json"):
        """
        Exporta todas las interacciones a un archivo JSON.

        Args:
            filename: Nombre del archivo
        """
        try:
            interactions_data = [interaction.to_dict() for interaction in self.interactions]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(interactions_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Interacciones exportadas a {filename}: {len(interactions_data)} registros")
        except Exception as e:
            logger.error(f"Error exportando interacciones: {e}")

    def clear_old_interactions(self, days_to_keep: int = 30):
        """
        Limpia interacciones antiguas.

        Args:
            days_to_keep: Días de interacciones a mantener
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        old_count = len(self.interactions)

        self.interactions = [i for i in self.interactions if i.timestamp > cutoff_date]

        removed_count = old_count - len(self.interactions)
        logger.info(f"Interacciones antiguas limpiadas: {removed_count} eliminadas, {len(self.interactions)} restantes")