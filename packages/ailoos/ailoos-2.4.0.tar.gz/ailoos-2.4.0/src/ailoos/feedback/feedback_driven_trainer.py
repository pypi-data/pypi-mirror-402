"""
FeedbackDrivenTrainer - Entrenador que usa feedback para mejorar el modelo
==========================================================================

Este módulo proporciona funcionalidades para usar feedback de usuarios
y análisis inteligente para mejorar el rendimiento del modelo EmpoorioLM
mediante re-entrenamiento selectivo y generación de datos adicionales.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import asyncio
import torch
import torch.nn as nn

from .feedback_analyzer import FeedbackInsight, FeedbackAnalyzer
from ..training.massive_federated_trainer import MassiveFederatedTrainer
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig

logger = logging.getLogger(__name__)


@dataclass
class TrainingTask:
    """Tarea de entrenamiento basada en feedback."""
    task_id: str
    insight_id: str
    problem_type: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    description: str
    training_data: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # 'pending', 'in_progress', 'completed', 'failed'
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la tarea a diccionario."""
        return {
            "task_id": self.task_id,
            "insight_id": self.insight_id,
            "problem_type": self.problem_type,
            "priority": self.priority,
            "description": self.description,
            "training_data_count": len(self.training_data),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results
        }


class FeedbackDataGenerator:
    """
    Generador de datos de entrenamiento basado en feedback.

    Crea datos sintéticos o ejemplos adicionales para abordar
    problemas identificados en el feedback.
    """

    def __init__(self):
        """Inicializa el generador de datos."""
        self.templates = {
            "low_rating": [
                "Por favor, explica {topic} de manera más clara y detallada.",
                "¿Puedes darme más información sobre {topic}?",
                "Necesito ayuda con {topic}, ¿puedes asistirme?",
                "Estoy confundido con {topic}, explica mejor por favor."
            ],
            "error_responses": [
                "Lo siento, no entendí tu pregunta sobre {topic}.",
                "Parece que hay un problema con mi respuesta sobre {topic}.",
                "Mi explicación sobre {topic} no fue clara.",
                "Hubo un error procesando tu consulta sobre {topic}."
            ],
            "negative_sentiment": [
                "Tu respuesta sobre {topic} fue insatisfactoria.",
                "No me gusta cómo explicaste {topic}.",
                "La información sobre {topic} no es útil.",
                "Prefiero respuestas más directas sobre {topic}."
            ],
            "performance_issues": [
                "La respuesta sobre {topic} tardó demasiado.",
                "El sistema fue lento al responder sobre {topic}.",
                "Hubo demoras en procesar la consulta sobre {topic}.",
                "La velocidad de respuesta para {topic} necesita mejorar."
            ]
        }

        self.topics = [
            "programación", "matemáticas", "ciencia", "historia",
            "tecnología", "medicina", "arte", "literatura",
            "economía", "política", "deportes", "entretenimiento"
        ]

    def generate_training_data(self, problem_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Genera datos de entrenamiento basados en tipo de problema.

        Args:
            problem_type: Tipo de problema identificado
            count: Número de ejemplos a generar

        Returns:
            Lista de datos de entrenamiento
        """
        if problem_type not in self.templates:
            logger.warning(f"Tipo de problema desconocido: {problem_type}")
            return []

        template_list = self.templates[problem_type]
        training_data = []

        for i in range(count):
            # Seleccionar template aleatoriamente
            template = template_list[i % len(template_list)]

            # Seleccionar topic aleatoriamente
            topic = self.topics[i % len(self.topics)]

            # Generar input y output esperado
            input_text = template.format(topic=topic)

            # Para simplificar, el output es una respuesta mejorada
            if problem_type == "low_rating":
                output_text = f"Claro, te explicaré {topic} de manera detallada. [Respuesta detallada sobre {topic}]"
            elif problem_type == "error_responses":
                output_text = f"Entiendo tu consulta sobre {topic}. Déjame darte una explicación clara. [Explicación correcta sobre {topic}]"
            elif problem_type == "negative_sentiment":
                output_text = f"Disculpa si mi respuesta anterior no fue satisfactoria. Aquí tienes información precisa sobre {topic}. [Información útil sobre {topic}]"
            elif problem_type == "performance_issues":
                output_text = f"Aquí tienes información concisa sobre {topic}. [Respuesta rápida y directa sobre {topic}]"
            else:
                output_text = f"Aquí tienes información sobre {topic}. [Contenido relevante]"

            training_data.append({
                "input": input_text,
                "output": output_text,
                "problem_type": problem_type,
                "topic": topic,
                "generated": True
            })

        logger.info(f"Generados {len(training_data)} ejemplos de entrenamiento para {problem_type}")
        return training_data


class FeedbackDrivenTrainer:
    """
    Entrenador que utiliza feedback para mejorar el modelo.

    Analiza insights de feedback y genera tareas de entrenamiento
    específicas para abordar problemas identificados.
    """

    def __init__(self, coordinator_url: str = "http://localhost:8000"):
        """
        Inicializa el entrenador basado en feedback.

        Args:
            coordinator_url: URL del coordinador federado
        """
        self.coordinator_url = coordinator_url
        self.data_generator = FeedbackDataGenerator()
        self.training_tasks: List[TrainingTask] = []
        self.task_counter = 0

        # Configuración
        self.min_confidence_threshold = 0.7
        self.max_training_tasks = 5
        self.training_batch_size = 8

        logger.info("FeedbackDrivenTrainer inicializado")

    def analyze_and_create_tasks(self, insights: List[FeedbackInsight]) -> List[TrainingTask]:
        """
        Analiza insights y crea tareas de entrenamiento apropiadas.

        Args:
            insights: Lista de insights del analizador

        Returns:
            Lista de tareas de entrenamiento creadas
        """
        new_tasks = []

        # Filtrar insights con alta confianza y severidad
        relevant_insights = [
            insight for insight in insights
            if insight.confidence >= self.min_confidence_threshold and
            insight.severity in ['high', 'critical']
        ]

        logger.info(f"Insights relevantes para entrenamiento: {len(relevant_insights)}")

        for insight in relevant_insights:
            if len(self.training_tasks) >= self.max_training_tasks:
                logger.warning("Límite máximo de tareas alcanzado")
                break

            task = self._create_training_task_from_insight(insight)
            if task:
                new_tasks.append(task)
                self.training_tasks.append(task)

        logger.info(f"Tareas de entrenamiento creadas: {len(new_tasks)}")
        return new_tasks

    def _create_training_task_from_insight(self, insight: FeedbackInsight) -> Optional[TrainingTask]:
        """
        Crea una tarea de entrenamiento desde un insight.

        Args:
            insight: Insight del analizador

        Returns:
            Tarea de entrenamiento o None si no es aplicable
        """
        self.task_counter += 1
        task_id = f"fb_task_{self.task_counter}_{int(datetime.now().timestamp())}"

        # Mapear categorías de insight a tipos de problema
        problem_mapping = {
            "ratings": "low_rating",
            "errors": "error_responses",
            "comments": "negative_sentiment",
            "metrics": "performance_issues"
        }

        problem_type = problem_mapping.get(insight.category, "general_improvement")

        # Determinar prioridad basada en severidad
        priority_mapping = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'critical': 'critical'
        }
        priority = priority_mapping.get(insight.severity, 'medium')

        # Generar datos de entrenamiento
        data_count = self._determine_data_count(insight)
        training_data = self.data_generator.generate_training_data(problem_type, data_count)

        if not training_data:
            return None

        task = TrainingTask(
            task_id=task_id,
            insight_id=f"{insight.category}_{insight.timestamp.isoformat()}",
            problem_type=problem_type,
            priority=priority,
            description=f"Entrenamiento para abordar: {insight.title}",
            training_data=training_data
        )

        logger.info(f"Tarea creada: {task_id} ({problem_type}, prioridad: {priority})")
        return task

    def _determine_data_count(self, insight: FeedbackInsight) -> int:
        """
        Determina cuántos ejemplos generar basado en el insight.

        Args:
            insight: Insight del analizador

        Returns:
            Número de ejemplos a generar
        """
        base_count = 10

        # Ajustar basado en severidad
        if insight.severity == 'critical':
            base_count *= 3
        elif insight.severity == 'high':
            base_count *= 2

        # Ajustar basado en confianza
        confidence_multiplier = min(insight.confidence * 2, 2.0)
        base_count = int(base_count * confidence_multiplier)

        return min(base_count, 50)  # Máximo 50 ejemplos por tarea

    async def execute_training_tasks(self) -> Dict[str, Any]:
        """
        Ejecuta las tareas de entrenamiento pendientes.

        Returns:
            Resultados del entrenamiento
        """
        pending_tasks = [task for task in self.training_tasks if task.status == "pending"]

        if not pending_tasks:
            logger.info("No hay tareas de entrenamiento pendientes")
            return {"message": "No pending tasks"}

        # Ordenar por prioridad
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t.priority, 3))

        logger.info(f"Ejecutando {len(pending_tasks)} tareas de entrenamiento")

        results = {
            "total_tasks": len(pending_tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "task_results": []
        }

        for task in pending_tasks:
            try:
                task.status = "in_progress"
                logger.info(f"Iniciando tarea: {task.task_id}")

                # Ejecutar entrenamiento para esta tarea
                task_result = await self._execute_single_task(task)

                if task_result.get("success", False):
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    task.results = task_result
                    results["completed_tasks"] += 1
                else:
                    task.status = "failed"
                    results["failed_tasks"] += 1

                results["task_results"].append({
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": task_result
                })

            except Exception as e:
                logger.error(f"Error ejecutando tarea {task.task_id}: {e}")
                task.status = "failed"
                results["failed_tasks"] += 1

        logger.info(f"Entrenamiento completado: {results['completed_tasks']}/{results['total_tasks']} tareas exitosas")
        return results

    async def _execute_single_task(self, task: TrainingTask) -> Dict[str, Any]:
        """
        Ejecuta una tarea de entrenamiento individual.

        Args:
            task: Tarea a ejecutar

        Returns:
            Resultados del entrenamiento
        """
        try:
            # Crear entrenador federado para esta tarea
            trainer = MassiveFederatedTrainer(self.coordinator_url)

            # Configurar nodos (simplificado - usar nodos disponibles)
            trainer.add_node("feedback_node_1", "cpu", "generated_data")
            trainer.add_node("feedback_node_2", "cpu", "generated_data")

            # Preparar datos de entrenamiento
            # En producción, esto convertiría los datos generados a formato del modelo
            training_samples = len(task.training_data)

            # Simular creación de sesión
            session_created = await trainer.create_session(f"feedback_training_{task.task_id}")

            if not session_created:
                return {"success": False, "error": "Failed to create training session"}

            # Simular inicialización de nodos
            nodes_initialized = await trainer.initialize_nodes()

            if not nodes_initialized:
                return {"success": False, "error": "Failed to initialize nodes"}

            # Ejecutar entrenamiento
            training_results = await trainer.run_federated_training()

            # Verificar si el entrenamiento fue exitoso
            success = training_results.get("completed_rounds", 0) > 0

            result = {
                "success": success,
                "training_samples": training_samples,
                "federated_results": training_results,
                "improvement_metrics": self._calculate_improvement_metrics(task, training_results)
            }

            return result

        except Exception as e:
            logger.error(f"Error en ejecución de tarea: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_improvement_metrics(self, task: TrainingTask, training_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas de mejora basadas en los resultados del entrenamiento.

        Args:
            task: Tarea ejecutada
            training_results: Resultados del entrenamiento federado

        Returns:
            Métricas de mejora
        """
        metrics = {
            "problem_type": task.problem_type,
            "training_samples_used": len(task.training_data),
            "federated_rounds_completed": training_results.get("completed_rounds", 0),
            "average_accuracy_improvement": 0.0,  # Placeholder
            "convergence_speed": 0.0  # Placeholder
        }

        # En producción, comparar con métricas baseline
        global_stats = training_results.get("global_stats", {})
        avg_accuracy = global_stats.get("average_accuracy", 0.0)

        # Estimación simple de mejora
        if task.problem_type == "low_rating":
            metrics["expected_rating_improvement"] = min(avg_accuracy / 10, 1.0)  # 0-1 scale
        elif task.problem_type == "error_responses":
            metrics["expected_error_reduction"] = min(avg_accuracy / 20, 0.5)  # 0-50% reduction
        elif task.problem_type == "performance_issues":
            metrics["expected_speed_improvement"] = min(avg_accuracy / 15, 0.8)  # 0-80% faster

        return metrics

    def get_pending_tasks(self) -> List[TrainingTask]:
        """
        Obtiene tareas de entrenamiento pendientes.

        Returns:
            Lista de tareas pendientes
        """
        return [task for task in self.training_tasks if task.status == "pending"]

    def get_completed_tasks(self) -> List[TrainingTask]:
        """
        Obtiene tareas de entrenamiento completadas.

        Returns:
            Lista de tareas completadas
        """
        return [task for task in self.training_tasks if task.status == "completed"]

    def get_task_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las tareas de entrenamiento.

        Returns:
            Estadísticas de tareas
        """
        total = len(self.training_tasks)
        pending = len(self.get_pending_tasks())
        completed = len(self.get_completed_tasks())
        failed = len([t for t in self.training_tasks if t.status == "failed"])

        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "completion_rate": completed / total if total > 0 else 0.0
        }

    def save_tasks_to_file(self, filename: str = "feedback_training_tasks.json"):
        """
        Guarda las tareas de entrenamiento a archivo.

        Args:
            filename: Nombre del archivo
        """
        try:
            tasks_data = [task.to_dict() for task in self.training_tasks]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Tareas guardadas en {filename}")
        except Exception as e:
            logger.error(f"Error guardando tareas: {e}")

    def load_tasks_from_file(self, filename: str = "feedback_training_tasks.json"):
        """
        Carga tareas de entrenamiento desde archivo.

        Args:
            filename: Nombre del archivo
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)

            for data in tasks_data:
                # Reconstruir tarea (simplificado)
                task = TrainingTask(
                    task_id=data["task_id"],
                    insight_id=data["insight_id"],
                    problem_type=data["problem_type"],
                    priority=data["priority"],
                    description=data["description"],
                    status=data["status"],
                    results=data.get("results", {})
                )
                self.training_tasks.append(task)

            logger.info(f"Tareas cargadas desde {filename}: {len(self.training_tasks)}")

        except FileNotFoundError:
            logger.info(f"Archivo {filename} no encontrado, empezando con tareas vacías")
        except Exception as e:
            logger.error(f"Error cargando tareas: {e}")