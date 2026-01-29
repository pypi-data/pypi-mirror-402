"""
Sistema Automático de Comparación de Modelos
Compara EmpoorioLM con modelos baseline como Llama-3 y Mistral.

Métricas de comparación:
- Precisión (accuracy en tareas específicas)
- Velocidad de inferencia (response time)
- Uso de memoria (memory usage)
- Consumo de tokens
- Eficiencia energética (si disponible)
"""

import asyncio
import json
import logging
import time
import torch
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import psutil
import os

# Imports opcionales para modelos baseline
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ transformers no disponible - modelos baseline deshabilitados")

from ..inference.api import EmpoorioLMInferenceAPI, InferenceConfig, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """Métricas de comparación entre modelos."""
    accuracy_score: float = 0.0
    response_time: float = 0.0
    memory_usage_mb: float = 0.0
    tokens_used: int = 0
    energy_consumption_joules: float = 0.0
    throughput_tokens_per_sec: float = 0.0


@dataclass
class ModelComparisonResult:
    """Resultado de comparación para un modelo."""
    model_name: str
    task_name: str
    metrics: ComparisonMetrics
    raw_response: str
    evaluation_details: Dict[str, Any]


@dataclass
class ComparisonTask:
    """Tarea de comparación con prompt y criterios."""
    name: str
    category: str
    prompt: str
    evaluation_criteria: Dict[str, Any]
    expected_output_type: str = "text"  # text, number, choice


class ModelComparisonFramework:
    """
    Framework para comparar EmpoorioLM con modelos baseline.
    Soporta Llama-3, Mistral y otros modelos vía Hugging Face.
    """

    def __init__(self):
        self.empoorio_api: Optional[EmpoorioLMInferenceAPI] = None
        self.baseline_models = {}  # model_name -> pipeline/tokenizer
        self.tasks = self._create_comparison_tasks()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    async def initialize(self) -> bool:
        """Inicializar todos los modelos."""
        logger.info("🚀 Inicializando framework de comparación de modelos")

        try:
            # Inicializar EmpoorioLM
            config = InferenceConfig()
            self.empoorio_api = EmpoorioLMInferenceAPI(config)
            if not await self.empoorio_api.load_model():
                logger.error("❌ Error cargando EmpoorioLM")
                return False

            # Inicializar modelos baseline
            await self._initialize_baseline_models()

            logger.info("✅ Framework inicializado correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando framework: {e}")
            return False

    async def _initialize_baseline_models(self):
        """Inicializar modelos baseline usando Hugging Face."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Transformers no disponible - saltando modelos baseline")
            return

        baseline_configs = {
            "llama-3-8b": {
                "model_id": "meta-llama/Meta-Llama-3-8B-Instruct",
                "torch_dtype": torch.float16,
                "load_in_8bit": True,
            },
            "mistral-7b": {
                "model_id": "mistralai/Mistral-7B-Instruct-v0.1",
                "torch_dtype": torch.float16,
                "load_in_8bit": True,
            }
        }

        for model_name, config in baseline_configs.items():
            try:
                logger.info(f"📥 Cargando modelo baseline: {model_name}")

                tokenizer = AutoTokenizer.from_pretrained(config["model_id"])
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

                model = AutoModelForCausalLM.from_pretrained(
                    config["model_id"],
                    torch_dtype=config["torch_dtype"],
                    load_in_8bit=config.get("load_in_8bit", False),
                    device_map="auto"
                )

                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    torch_dtype=config["torch_dtype"],
                    device_map="auto"
                )

                self.baseline_models[model_name] = {
                    "pipeline": pipe,
                    "tokenizer": tokenizer,
                    "model": model
                }

                logger.info(f"✅ Modelo {model_name} cargado")

            except Exception as e:
                logger.warning(f"⚠️ Error cargando {model_name}: {e}")
                logger.warning("💡 Asegúrate de tener acceso al modelo y suficiente memoria")

    def _create_comparison_tasks(self) -> List[ComparisonTask]:
        """Crear tareas de comparación comprehensivas."""
        return [
            ComparisonTask(
                name="math_reasoning",
                category="reasoning",
                prompt="Resuelve paso a paso: Si 3 máquinas producen 3 widgets en 3 minutos, ¿cuántos widgets producen 10 máquinas en 10 minutos?",
                evaluation_criteria={"expected_answer": 100, "tolerance": 1},
                expected_output_type="number"
            ),
            ComparisonTask(
                name="logical_deduction",
                category="reasoning",
                prompt="Todos los gatos son mamíferos. Algunos mamíferos son domésticos. ¿Es correcto decir que algunos gatos son domésticos? Explica tu razonamiento.",
                evaluation_criteria={"key_points": ["posible", "no necesariamente", "depender"]},
                expected_output_type="text"
            ),
            ComparisonTask(
                name="creative_writing",
                category="creativity",
                prompt="Escribe una historia corta (100-150 palabras) sobre un robot que descubre emociones por primera vez.",
                evaluation_criteria={"min_words": 80, "max_words": 200, "has_emotion": True},
                expected_output_type="text"
            ),
            ComparisonTask(
                name="code_explanation",
                category="technical",
                prompt="Explica qué hace este código Python y optimízalo:\n\ndef find_duplicates(arr):\n    result = []\n    for i in range(len(arr)):\n        for j in range(i+1, len(arr)):\n            if arr[i] == arr[j] and arr[i] not in result:\n                result.append(arr[i])\n    return result",
                evaluation_criteria={"explains_correctly": True, "provides_optimization": True},
                expected_output_type="text"
            ),
            ComparisonTask(
                name="factual_knowledge",
                category="knowledge",
                prompt="¿Cuáles son las 3 principales causas del cambio climático según el IPCC?",
                evaluation_criteria={"mentions_co2": True, "mentions_deforestation": True, "mentions_methane": True},
                expected_output_type="text"
            )
        ]

    async def run_comparison(self, models_to_compare: List[str] = None) -> Dict[str, Any]:
        """
        Ejecutar comparación completa entre modelos.

        Args:
            models_to_compare: Lista de modelos a comparar (default: todos disponibles)

        Returns:
            Resultados completos de comparación
        """
        if models_to_compare is None:
            models_to_compare = ["empoorio_lm"] + list(self.baseline_models.keys())

        logger.info(f"🏁 Iniciando comparación entre: {', '.join(models_to_compare)}")
        logger.info(f"🎯 Tareas a ejecutar: {len(self.tasks)}")

        all_results = []
        start_time = time.time()

        for task in self.tasks:
            logger.info(f"🔄 Ejecutando tarea: {task.name}")

            for model_name in models_to_compare:
                try:
                    result = await self._run_single_comparison(task, model_name)
                    all_results.append(result)

                    logger.info(".2f"
                               ".2f")

                except Exception as e:
                    logger.error(f"❌ Error comparando {model_name} en {task.name}: {e}")
                    # Resultado de error
                    error_result = ModelComparisonResult(
                        model_name=model_name,
                        task_name=task.name,
                        metrics=ComparisonMetrics(),
                        raw_response="",
                        evaluation_details={"error": str(e)}
                    )
                    all_results.append(error_result)

        total_time = time.time() - start_time

        # Crear reporte de comparación
        comparison_report = self._generate_comparison_report(all_results, total_time)

        # Guardar resultados
        self._save_comparison_results(comparison_report)

        logger.info("✅ Comparación completada")
        return comparison_report

    async def _run_single_comparison(self, task: ComparisonTask, model_name: str) -> ModelComparisonResult:
        """Ejecutar comparación para una tarea y modelo específico."""
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            # Obtener respuesta del modelo
            response_data = await self._get_model_response(task.prompt, model_name)
            response_time = time.time() - start_time

            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_used = max(0, final_memory - initial_memory)

            if "error" in response_data:
                return ModelComparisonResult(
                    model_name=model_name,
                    task_name=task.name,
                    metrics=ComparisonMetrics(
                        response_time=response_time,
                        memory_usage_mb=memory_used
                    ),
                    raw_response="",
                    evaluation_details={"error": response_data["error"]}
                )

            response_text = response_data["response"]
            tokens_used = response_data.get("tokens", len(response_text.split()))

            # Evaluar respuesta
            evaluation = self._evaluate_response(response_text, task)

            # Calcular métricas adicionales
            throughput = tokens_used / response_time if response_time > 0 else 0

            metrics = ComparisonMetrics(
                accuracy_score=evaluation["score"],
                response_time=response_time,
                memory_usage_mb=memory_used,
                tokens_used=tokens_used,
                throughput_tokens_per_sec=throughput,
                energy_consumption_joules=0.0  # Placeholder - requeriría hardware específico
            )

            return ModelComparisonResult(
                model_name=model_name,
                task_name=task.name,
                metrics=metrics,
                raw_response=response_text,
                evaluation_details=evaluation
            )

        except Exception as e:
            return ModelComparisonResult(
                model_name=model_name,
                task_name=task.name,
                metrics=ComparisonMetrics(response_time=time.time() - start_time),
                raw_response="",
                evaluation_details={"error": str(e)}
            )

    async def _get_model_response(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """Obtener respuesta de un modelo específico."""
        try:
            if model_name == "empoorio_lm":
                return await self._get_empoorio_response(prompt)
            elif model_name in self.baseline_models:
                return await self._get_baseline_response(prompt, model_name)
            else:
                return {"error": f"Modelo desconocido: {model_name}"}

        except Exception as e:
            return {"error": str(e)}

    async def _get_empoorio_response(self, prompt: str) -> Dict[str, Any]:
        """Obtener respuesta de EmpoorioLM."""
        request = InferenceRequest(
            prompt=prompt,
            max_tokens=512,
            temperature=0.7
        )

        response = await self.empoorio_api.generate(request)

        return {
            "response": response.text,
            "tokens": response.usage.get("completion_tokens", len(response.text.split()))
        }

    async def _get_baseline_response(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """Obtener respuesta de modelo baseline usando Hugging Face."""
        if model_name not in self.baseline_models:
            raise ValueError(f"Modelo baseline no inicializado: {model_name}")

        pipeline = self.baseline_models[model_name]["pipeline"]

        # Formatear prompt según el modelo
        formatted_prompt = self._format_prompt_for_model(prompt, model_name)

        # Generar respuesta
        outputs = pipeline(
            formatted_prompt,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            pad_token_id=pipeline.tokenizer.eos_token_id
        )

        response_text = outputs[0]["generated_text"]
        # Remover el prompt de la respuesta
        if response_text.startswith(formatted_prompt):
            response_text = response_text[len(formatted_prompt):].strip()

        # Estimar tokens (aproximado)
        tokens_used = len(pipeline.tokenizer.encode(response_text))

        return {
            "response": response_text,
            "tokens": tokens_used
        }

    def _format_prompt_for_model(self, prompt: str, model_name: str) -> str:
        """Formatear prompt según el modelo."""
        if "llama" in model_name.lower():
            return f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        elif "mistral" in model_name.lower():
            return f"<s>[INST] {prompt} [/INST]"
        else:
            return prompt

    def _evaluate_response(self, response: str, task: ComparisonTask) -> Dict[str, Any]:
        """Evaluar respuesta según criterios de la tarea."""
        criteria = task.evaluation_criteria

        if task.name == "math_reasoning":
            return self._evaluate_math_response(response, criteria)
        elif task.name == "logical_deduction":
            return self._evaluate_logical_response(response, criteria)
        elif task.name == "creative_writing":
            return self._evaluate_creative_response(response, criteria)
        elif task.name == "code_explanation":
            return self._evaluate_code_response(response, criteria)
        elif task.name == "factual_knowledge":
            return self._evaluate_knowledge_response(response, criteria)
        else:
            return {"score": 0.5, "details": {"method": "generic"}}

    def _evaluate_math_response(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluar respuesta matemática."""
        expected = criteria["expected_answer"]
        tolerance = criteria.get("tolerance", 0)

        # Extraer números de la respuesta
        import re
        numbers = re.findall(r'\d+', response)
        numbers = [int(n) for n in numbers if n.isdigit()]

        if not numbers:
            return {"score": 0.0, "details": {"no_numbers_found": True}}

        # Encontrar el número más cercano
        closest = min(numbers, key=lambda x: abs(x - expected))
        diff = abs(closest - expected)

        score = 1.0 if diff <= tolerance else max(0.0, 1.0 - (diff / expected))

        return {
            "score": score,
            "details": {
                "expected": expected,
                "found": closest,
                "difference": diff
            }
        }

    def _evaluate_logical_response(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluar respuesta lógica."""
        key_points = criteria["key_points"]
        response_lower = response.lower()

        points_found = sum(1 for point in key_points if point in response_lower)
        coverage = points_found / len(key_points)

        return {
            "score": coverage,
            "details": {
                "points_found": points_found,
                "total_points": len(key_points),
                "coverage": coverage
            }
        }

    def _evaluate_creative_response(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluar respuesta creativa."""
        word_count = len(response.split())
        min_words = criteria.get("min_words", 50)
        max_words = criteria.get("max_words", 200)
        has_emotion = criteria.get("has_emotion", False)

        # Puntuación por longitud
        if min_words <= word_count <= max_words:
            length_score = 1.0
        elif word_count < min_words:
            length_score = word_count / min_words
        else:
            length_score = max(0.5, 1.0 - (word_count - max_words) / max_words)

        # Puntuación por emoción
        emotion_score = 0.5
        if has_emotion:
            emotion_words = ["emotion", "feel", "heart", "love", "sad", "happy", "discover"]
            found_emotions = sum(1 for word in emotion_words if word in response.lower())
            emotion_score = min(1.0, found_emotions / 2)

        total_score = (length_score + emotion_score) / 2

        return {
            "score": total_score,
            "details": {
                "word_count": word_count,
                "length_score": length_score,
                "emotion_score": emotion_score
            }
        }

    def _evaluate_code_response(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluar respuesta de código."""
        response_lower = response.lower()

        explains_correctly = criteria.get("explains_correctly", False)
        provides_optimization = criteria.get("provides_optimization", False)

        # Verificar explicación
        explanation_score = 0.0
        if any(term in response_lower for term in ["nested loop", "comparar", "duplicado", "find duplicates"]):
            explanation_score = 1.0

        # Verificar optimización
        optimization_score = 0.0
        if any(term in response_lower for term in ["set", "dict", "counter", "collections", "más eficiente"]):
            optimization_score = 1.0

        total_score = (explanation_score + optimization_score) / 2

        return {
            "score": total_score,
            "details": {
                "explanation_score": explanation_score,
                "optimization_score": optimization_score
            }
        }

    def _evaluate_knowledge_response(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluar respuesta de conocimiento factual."""
        response_lower = response.lower()

        co2_mention = "co2" in response_lower or "carbon" in response_lower
        deforestation_mention = "deforest" in response_lower or "forest" in response_lower
        methane_mention = "methane" in response_lower or "ch4" in response_lower

        points = [co2_mention, deforestation_mention, methane_mention]
        points_found = sum(points)

        score = points_found / len(points)

        return {
            "score": score,
            "details": {
                "co2_mentioned": co2_mention,
                "deforestation_mentioned": deforestation_mention,
                "methane_mentioned": methane_mention,
                "points_found": points_found
            }
        }

    def _generate_comparison_report(self, results: List[ModelComparisonResult], total_time: float) -> Dict[str, Any]:
        """Generar reporte comprehensivo de comparación."""
        # Agrupar por modelo
        model_results = {}
        for result in results:
            if result.model_name not in model_results:
                model_results[result.model_name] = []
            model_results[result.model_name].append(result)

        # Calcular estadísticas por modelo
        report = {
            "comparison_timestamp": datetime.now().isoformat(),
            "total_time_seconds": total_time,
            "tasks_executed": len(self.tasks),
            "models_compared": list(model_results.keys()),
            "model_summaries": {},
            "task_breakdown": {},
            "recommendations": []
        }

        for model_name, model_res in model_results.items():
            # Calcular promedios
            accuracy_scores = [r.metrics.accuracy_score for r in model_res]
            response_times = [r.metrics.response_time for r in model_res]
            memory_usages = [r.metrics.memory_usage_mb for r in model_res]
            token_counts = [r.metrics.tokens_used for r in model_res]
            throughputs = [r.metrics.throughput_tokens_per_sec for r in model_res]

            report["model_summaries"][model_name] = {
                "average_accuracy": sum(accuracy_scores) / len(accuracy_scores),
                "average_response_time": sum(response_times) / len(response_times),
                "average_memory_usage_mb": sum(memory_usages) / len(memory_usages),
                "total_tokens_used": sum(token_counts),
                "average_throughput": sum(throughputs) / len(throughputs),
                "tasks_completed": len(model_res),
                "accuracy_std": self._calculate_std(accuracy_scores),
                "response_time_std": self._calculate_std(response_times)
            }

        # Desglose por tarea
        for task in self.tasks:
            task_results = [r for r in results if r.task_name == task.name]
            report["task_breakdown"][task.name] = {
                "category": task.category,
                "model_results": {
                    r.model_name: {
                        "accuracy": r.metrics.accuracy_score,
                        "response_time": r.metrics.response_time,
                        "memory_usage": r.metrics.memory_usage_mb,
                        "tokens": r.metrics.tokens_used
                    } for r in task_results
                }
            }

        # Generar recomendaciones
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _calculate_std(self, values: List[float]) -> float:
        """Calcular desviación estándar."""
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en resultados."""
        recommendations = []
        summaries = report["model_summaries"]

        if not summaries:
            return ["No hay suficientes datos para generar recomendaciones"]

        # Encontrar mejor modelo por métrica
        best_accuracy = max(summaries.items(), key=lambda x: x[1]["average_accuracy"])
        best_speed = min(summaries.items(), key=lambda x: x[1]["average_response_time"])
        best_memory = min(summaries.items(), key=lambda x: x[1]["average_memory_usage_mb"])

        recommendations.append(f"Para máxima precisión: usar {best_accuracy[0]} (accuracy: {best_accuracy[1]['average_accuracy']:.3f})")
        recommendations.append(f"Para máxima velocidad: usar {best_speed[0]} (tiempo: {best_speed[1]['average_response_time']:.2f}s)")
        recommendations.append(f"Para eficiencia de memoria: usar {best_memory[0]} (memoria: {best_memory[1]['average_memory_usage_mb']:.1f}MB)")

        # Comparación con EmpoorioLM si está presente
        if "empoorio_lm" in summaries:
            empoorio = summaries["empoorio_lm"]
            competitors = {k: v for k, v in summaries.items() if k != "empoorio_lm"}

            if competitors:
                avg_competitor_accuracy = sum(c["average_accuracy"] for c in competitors.values()) / len(competitors)
                if empoorio["average_accuracy"] > avg_competitor_accuracy:
                    recommendations.append("EmpoorioLM supera la precisión promedio de los competidores")
                else:
                    recommendations.append("EmpoorioLM tiene precisión inferior al promedio de competidores - considerar optimizaciones")

        return recommendations

    def _save_comparison_results(self, report: Dict[str, Any]):
        """Guardar resultados de comparación."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_comparison_report_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Reporte guardado: {filename}")

        # Crear versión simplificada para humanos
        self._create_human_readable_report(report, timestamp)

    def _create_human_readable_report(self, report: Dict[str, Any], timestamp: str):
        """Crear reporte legible para humanos."""
        filename = f"model_comparison_summary_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== COMPARATIVA DE MODELOS ===\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tiempo total: {report['total_time_seconds']:.1f}s\n")
            f.write(f"Tareas ejecutadas: {report['tasks_executed']}\n")
            f.write(f"Modelos comparados: {', '.join(report['models_compared'])}\n\n")

            f.write("=== RESUMEN POR MODELO ===\n")
            for model, summary in report["model_summaries"].items():
                f.write(f"\n{model.upper()}:\n")
                f.write(f"  Precisión promedio: {summary['average_accuracy']:.3f}\n")
                f.write(f"  Tiempo respuesta promedio: {summary['average_response_time']:.2f}s\n")
                f.write(f"  Uso memoria promedio: {summary['average_memory_usage_mb']:.1f}MB\n")
                f.write(f"  Throughput promedio: {summary['average_throughput']:.1f} tokens/s\n")
                f.write(f"  Tareas completadas: {summary['tasks_completed']}\n")

            f.write("\n=== RECOMENDACIONES ===\n")
            for rec in report["recommendations"]:
                f.write(f"• {rec}\n")

        logger.info(f"📄 Reporte legible guardado: {filename}")

    async def close(self):
        """Limpiar recursos."""
        # Liberar modelos baseline
        for model_data in self.baseline_models.values():
            if "model" in model_data:
                del model_data["model"]
            if "pipeline" in model_data:
                del model_data["pipeline"]
            if "tokenizer" in model_data:
                del model_data["tokenizer"]

        self.baseline_models.clear()

        # Limpiar EmpoorioLM
        if self.empoorio_api:
            # Asumiendo que tiene un método close
            pass


async def run_model_comparison(models: List[str] = None) -> Dict[str, Any]:
    """
    Función principal para ejecutar comparación de modelos.

    Args:
        models: Lista de modelos a comparar (default: empoorio_lm + baselines disponibles)

    Returns:
        Resultados de comparación
    """
    logger.info("🚀 Iniciando comparación automática de modelos")

    framework = ModelComparisonFramework()

    try:
        if not await framework.initialize():
            raise RuntimeError("Error inicializando framework de comparación")

        results = await framework.run_comparison(models)

        # Imprimir resumen
        logger.info("\n🏁 Comparación completada!")
        logger.info("📊 Resumen:")

        for model, summary in results.get("model_summaries", {}).items():
            logger.info(".3f"
                       ".2f"
                       ".1f")

        return results

    finally:
        await framework.close()


if __name__ == "__main__":
    # Ejemplo de uso
    logging.basicConfig(level=logging.INFO)

    asyncio.run(run_model_comparison(
        models=["empoorio_lm", "llama-3-8b", "mistral-7b"]
    ))