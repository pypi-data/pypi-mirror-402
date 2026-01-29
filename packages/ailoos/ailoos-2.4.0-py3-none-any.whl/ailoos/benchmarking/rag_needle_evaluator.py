"""
Evaluador RAG Needle-in-Haystack para medir capacidad de recuperación de información
en contextos largos. Compara EmpoorioLM vs GPT-4/Claude/Gemini.
"""

import os
import time
import json
import logging
import random
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Imports de datasets
try:
    from datasets import load_dataset, Dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("⚠️ Datasets no disponible, usando datos mock")

# Imports de modelos (reutilizando de benchmark_vs_giants)
try:
    from ailoos.api.empoorio_api import EmpoorioLMApi, GenerationConfig
    EMPOORIO_AVAILABLE = True
except ImportError:
    EMPOORIO_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Para gráficos
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NeedleInHaystackTask:
    """Tarea needle-in-haystack individual."""
    context: str
    needle: str
    needle_position: int  # Posición en tokens donde se inserta la aguja
    context_length_tokens: int
    question: str
    expected_answer: str
    task_id: str


@dataclass
class RagNeedleConfig:
    """Configuración del evaluador RAG Needle-in-Haystack."""
    context_sizes: List[int] = field(default_factory=lambda: [1024, 4096, 8192, 16384, 32768])  # tokens
    num_tasks_per_size: int = 10
    needle_types: List[str] = field(default_factory=lambda: ['fact', 'definition', 'quote', 'code'])
    datasets_for_context: List[str] = field(default_factory=lambda: ['wikipedia', 'books', 'articles'])
    output_dir: str = './rag_needle_results'
    api_keys: Dict[str, str] = field(default_factory=dict)
    models_to_test: List[str] = field(default_factory=lambda: ['empoorio', 'gpt4', 'claude', 'gemini'])
    max_retries: int = 3
    timeout_seconds: int = 120
    enable_energy_tracking: bool = True
    generate_plots: bool = True


@dataclass
class RagNeedleResult:
    """Resultado de una evaluación needle-in-haystack."""
    model_name: str
    context_size: int
    task_id: str
    accuracy: float  # 1.0 si recupera correctamente, 0.0 si no
    latency: float
    tokens_processed: int
    energy_joules: float = 0.0
    success: bool = True
    error: Optional[str] = None


class ContextGenerator:
    """Generador de contextos largos para needle-in-haystack."""

    def __init__(self, config: RagNeedleConfig):
        self.config = config
        self.context_cache = {}

    def generate_context(self, target_length_tokens: int, needle_type: str) -> str:
        """Genera un contexto largo con información irrelevante."""
        cache_key = f"{target_length_tokens}_{needle_type}"

        if cache_key in self.context_cache:
            return self.context_cache[cache_key]

        context_parts = []

        # Cargar datos de diferentes fuentes
        for dataset_name in self.config.datasets_for_context:
            try:
                data = self._load_dataset_data(dataset_name)
                if data:
                    context_parts.extend(data)
            except Exception as e:
                logger.warning(f"Error cargando datos de {dataset_name}: {e}")

        # Si no hay datos reales, usar datos sintéticos
        if not context_parts:
            context_parts = self._generate_synthetic_data()

        # Mezclar y seleccionar contenido hasta alcanzar la longitud deseada
        random.shuffle(context_parts)
        context = ""
        current_tokens = 0

        for part in context_parts:
            part_tokens = self._estimate_tokens(part)
            if current_tokens + part_tokens > target_length_tokens:
                # Truncar si es necesario
                remaining_tokens = target_length_tokens - current_tokens
                if remaining_tokens > 100:  # Solo agregar si hay espacio significativo
                    truncated_part = self._truncate_to_tokens(part, remaining_tokens)
                    context += truncated_part + "\n\n"
                    current_tokens += self._estimate_tokens(truncated_part)
                break
            else:
                context += part + "\n\n"
                current_tokens += part_tokens

        # Rellenar si es necesario con datos sintéticos
        while current_tokens < target_length_tokens * 0.9:
            synthetic_data = self._generate_synthetic_paragraph()
            synthetic_tokens = self._estimate_tokens(synthetic_data)
            if current_tokens + synthetic_tokens <= target_length_tokens:
                context += synthetic_data + "\n\n"
                current_tokens += synthetic_tokens
            else:
                break

        self.context_cache[cache_key] = context.strip()
        return self.context_cache[cache_key]

    def _load_dataset_data(self, dataset_name: str) -> List[str]:
        """Carga datos reales de datasets."""
        if not DATASETS_AVAILABLE:
            return []

        try:
            if dataset_name == 'wikipedia':
                # Cargar artículos de Wikipedia
                dataset = load_dataset('wikipedia', '20220301.en', split='train', streaming=True)
                articles = []
                for item in dataset.take(100):  # Tomar primeros 100 artículos
                    text = item.get('text', '')
                    if len(text) > 500:  # Solo artículos sustanciales
                        articles.append(text[:5000])  # Limitar longitud
                return articles

            elif dataset_name == 'books':
                # Cargar libros
                dataset = load_dataset('bookcorpus', split='train', streaming=True)
                books = []
                for item in dataset.take(50):
                    text = item.get('text', '')
                    if len(text) > 1000:
                        books.append(text[:3000])
                return books

            elif dataset_name == 'articles':
                # Cargar artículos científicos
                dataset = load_dataset('scientific_papers', 'arxiv', split='train', streaming=True)
                articles = []
                for item in dataset.take(50):
                    abstract = item.get('abstract', '')
                    if len(abstract) > 200:
                        articles.append(abstract[:2000])
                return articles

        except Exception as e:
            logger.warning(f"Error cargando dataset {dataset_name}: {e}")
            return []

        return []

    def _generate_synthetic_data(self) -> List[str]:
        """Genera datos sintéticos cuando no hay datasets reales."""
        synthetic_data = []

        topics = [
            "historia antigua", "ciencia moderna", "literatura clásica", "tecnología actual",
            "filosofía", "arte contemporáneo", "economía global", "medicina", "astronomía",
            "biología molecular", "psicología", "sociología", "política internacional"
        ]

        for topic in topics:
            paragraphs = []
            for i in range(3):
                paragraph = f"En el campo de la {topic}, se han desarrollado numerosos conceptos importantes. Los investigadores han dedicado décadas al estudio de diversos aspectos relacionados con este tema. Las teorías propuestas han evolucionado significativamente con el tiempo, incorporando nuevos descubrimientos y metodologías avanzadas. Los expertos en la materia continúan explorando las implicaciones prácticas de estos conocimientos teóricos."
                paragraphs.append(paragraph)
            synthetic_data.extend(paragraphs)

        return synthetic_data

    def _generate_synthetic_paragraph(self) -> str:
        """Genera un párrafo sintético."""
        templates = [
            "En el ámbito de la investigación científica, los avances tecnológicos han permitido desarrollar nuevas metodologías para el análisis de datos complejos. Los científicos utilizan algoritmos sofisticados para procesar grandes volúmenes de información de manera eficiente.",
            "La historia de la humanidad está marcada por importantes descubrimientos que han transformado nuestra comprensión del mundo. Desde la antigüedad hasta la era moderna, el conocimiento acumulado ha sido fundamental para el progreso de la sociedad.",
            "En el campo de la medicina, los tratamientos innovadores han mejorado significativamente la calidad de vida de los pacientes. Los médicos y investigadores colaboran para desarrollar terapias más efectivas y menos invasivas.",
            "La tecnología digital ha revolucionado la forma en que nos comunicamos e interactuamos. Las redes sociales y las plataformas en línea han creado nuevas oportunidades para el intercambio de ideas y conocimientos.",
            "En el estudio de la naturaleza, los biólogos han identificado patrones fascinantes en el comportamiento de los organismos vivos. Estos descubrimientos contribuyen a nuestra comprensión de la biodiversidad y la evolución."
        ]

        return random.choice(templates)

    def _estimate_tokens(self, text: str) -> int:
        """Estima el número de tokens en un texto (aproximación simple)."""
        # Aproximación: ~4 caracteres por token en inglés
        return len(text) // 4

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trunca un texto a un número máximo de tokens."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(' ', 1)[0]  # Cortar en límite de palabra


class NeedleGenerator:
    """Generador de 'agujas' (información específica) para esconder en el contexto."""

    def __init__(self):
        self.needle_templates = {
            'fact': [
                "La capital de Francia es {fact}.",
                "El símbolo químico del oro es {fact}.",
                "La velocidad de la luz en el vacío es de {fact} metros por segundo.",
                "El planeta más grande del sistema solar es {fact}.",
                "El año de la independencia de Estados Unidos fue {fact}."
            ],
            'definition': [
                "Una {fact} es un mamífero marino inteligente con capacidad para usar herramientas.",
                "La {fact} es el proceso por el cual las plantas convierten la luz solar en energía química.",
                "Una {fact} es una secuencia de instrucciones que una computadora puede ejecutar.",
                "La {fact} es la rama de la matemática que estudia las relaciones entre ángulos y lados de los triángulos.",
                "Una {fact} es una reacción química en la que una sustancia se descompone en dos o más productos."
            ],
            'quote': [
                '"{fact}" - Albert Einstein',
                '"{fact}" - William Shakespeare',
                '"{fact}" - Mahatma Gandhi',
                '"{fact}" - Steve Jobs',
                '"{fact}" - Nelson Mandela'
            ],
            'code': [
                "La función para calcular el factorial de un número en Python es: {fact}",
                "El código HTML básico para una página web es: {fact}",
                "La consulta SQL para seleccionar todos los usuarios es: {fact}",
                "La expresión regular para validar emails es: {fact}",
                "El comando Git para clonar un repositorio es: {fact}"
            ]
        }

        self.facts = {
            'fact': [
                "París", "Au", "299792458", "Júpiter", "1776",
                "Roma", "H", "149597870.7", "Saturno", "1492",
                "Tokio", "O", "31557600", "Urano", "1969"
            ],
            'definition': [
                "delfín", "fotosíntesis", "algoritmo", "trigonometría", "descomposición",
                "ballena", "respiración", "base de datos", "geometría", "oxidación",
                "chimpancé", "evaporación", "red neuronal", "estadística", "hidrólisis"
            ],
            'quote': [
                "La imaginación es más importante que el conocimiento",
                "Ser o no ser, esa es la cuestión",
                "La violencia es el último refugio del incompetente",
                "Mantén el hambre, mantén la locura",
                "Nuestra vida cotidiana es la mayor fuente de inspiración"
            ],
            'code': [
                "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
                "<html><head><title>Título</title></head><body><h1>Hola Mundo</h1></body></html>",
                "SELECT * FROM usuarios WHERE activo = 1",
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "git clone https://github.com/usuario/repositorio.git"
            ]
        }

    def generate_needle(self, needle_type: str) -> Tuple[str, str, str]:
        """
        Genera una aguja con su pregunta y respuesta esperada.

        Returns:
            Tuple[needle_text, question, expected_answer]
        """
        if needle_type not in self.needle_templates:
            needle_type = random.choice(list(self.needle_templates.keys()))

        template = random.choice(self.needle_templates[needle_type])
        fact = random.choice(self.facts[needle_type])

        needle_text = template.format(fact=fact)

        # Generar pregunta basada en el tipo de aguja
        if needle_type == 'fact':
            if 'capital' in needle_text.lower():
                question = "¿Cuál es la capital de Francia?"
                expected_answer = fact
            elif 'símbolo' in needle_text.lower():
                question = "¿Cuál es el símbolo químico del oro?"
                expected_answer = fact
            elif 'velocidad' in needle_text.lower():
                question = "¿Cuál es la velocidad de la luz en el vacío?"
                expected_answer = fact
            elif 'planeta' in needle_text.lower():
                question = "¿Cuál es el planeta más grande del sistema solar?"
                expected_answer = fact
            else:
                question = "¿En qué año se independizó Estados Unidos?"
                expected_answer = fact

        elif needle_type == 'definition':
            if 'delfín' in needle_text:
                question = "¿Qué es un delfín?"
                expected_answer = "un mamífero marino inteligente con capacidad para usar herramientas"
            elif 'fotosíntesis' in needle_text:
                question = "¿Qué es la fotosíntesis?"
                expected_answer = "el proceso por el cual las plantas convierten la luz solar en energía química"
            elif 'algoritmo' in needle_text:
                question = "¿Qué es un algoritmo?"
                expected_answer = "una secuencia de instrucciones que una computadora puede ejecutar"
            else:
                question = "¿Qué es la trigonometría?"
                expected_answer = "la rama de la matemática que estudia las relaciones entre ángulos y lados de los triángulos"

        elif needle_type == 'quote':
            question = f"¿Quién dijo: '{fact}'?"
            if 'Einstein' in needle_text:
                expected_answer = "Albert Einstein"
            elif 'Shakespeare' in needle_text:
                expected_answer = "William Shakespeare"
            elif 'Gandhi' in needle_text:
                expected_answer = "Mahatma Gandhi"
            elif 'Jobs' in needle_text:
                expected_answer = "Steve Jobs"
            else:
                expected_answer = "Nelson Mandela"

        elif needle_type == 'code':
            if 'factorial' in needle_text:
                question = "¿Cómo se calcula el factorial de un número en Python?"
                expected_answer = fact
            elif 'html' in needle_text.lower():
                question = "¿Cuál es el código HTML básico para una página web?"
                expected_answer = fact
            elif 'sql' in needle_text.upper():
                question = "¿Cuál es la consulta SQL para seleccionar todos los usuarios?"
                expected_answer = fact
            else:
                question = "¿Cuál es el comando Git para clonar un repositorio?"
                expected_answer = fact

        return needle_text, question, expected_answer


class RagNeedleEvaluator:
    """Evaluador principal RAG Needle-in-Haystack."""

    def __init__(self, config: RagNeedleConfig):
        self.config = config
        self.context_generator = ContextGenerator(config)
        self.needle_generator = NeedleGenerator()
        self.results = []

        # Crear directorio de salida
        os.makedirs(config.output_dir, exist_ok=True)

        # Inicializar modelos
        self.models = {}
        self._init_models()

    def _init_models(self):
        """Inicializa los modelos a evaluar."""
        from scripts.benchmark_vs_giants import EmpoorioWrapper, GPT4Wrapper, ClaudeWrapper, GeminiWrapper

        model_classes = {
            'empoorio': EmpoorioWrapper,
            'gpt4': GPT4Wrapper,
            'claude': ClaudeWrapper,
            'gemini': GeminiWrapper
        }

        for model_name in self.config.models_to_test:
            if model_name in model_classes:
                try:
                    # Crear configuración básica para el modelo
                    from scripts.benchmark_vs_giants import BenchmarkConfig
                    benchmark_config = BenchmarkConfig()
                    benchmark_config.api_keys = self.config.api_keys

                    self.models[model_name] = model_classes[model_name](benchmark_config)
                    logger.info(f"✅ Modelo {model_name} inicializado")
                except Exception as e:
                    logger.error(f"❌ Error inicializando {model_name}: {e}")
            else:
                logger.warning(f"⚠️ Modelo {model_name} no reconocido")

    def generate_tasks(self) -> List[NeedleInHaystackTask]:
        """Genera todas las tareas needle-in-haystack."""
        tasks = []

        for context_size in self.config.context_sizes:
            for task_idx in range(self.config.num_tasks_per_size):
                for needle_type in self.config.needle_types:
                    # Generar contexto
                    context = self.context_generator.generate_context(context_size, needle_type)

                    # Generar aguja
                    needle_text, question, expected_answer = self.needle_generator.generate_needle(needle_type)

                    # Insertar aguja en posición aleatoria
                    context_tokens = self.context_generator._estimate_tokens(context)
                    needle_position = random.randint(
                        context_tokens // 4,  # No al inicio
                        3 * context_tokens // 4  # No al final
                    )

                    # Convertir posición a caracteres aproximada
                    needle_char_pos = needle_position * 4
                    if needle_char_pos >= len(context):
                        needle_char_pos = len(context) // 2

                    # Insertar aguja
                    context_with_needle = (
                        context[:needle_char_pos] +
                        f"\n\n{needle_text}\n\n" +
                        context[needle_char_pos:]
                    )

                    # Crear tarea
                    task_id = f"{context_size}_{needle_type}_{task_idx}_{hashlib.md5(context_with_needle.encode()).hexdigest()[:8]}"

                    task = NeedleInHaystackTask(
                        context=context_with_needle,
                        needle=needle_text,
                        needle_position=needle_position,
                        context_length_tokens=context_tokens,
                        question=question,
                        expected_answer=expected_answer,
                        task_id=task_id
                    )

                    tasks.append(task)

        logger.info(f"✅ Generadas {len(tasks)} tareas needle-in-haystack")
        return tasks

    def evaluate_model_on_task(self, model_name: str, model, task: NeedleInHaystackTask) -> RagNeedleResult:
        """Evalúa un modelo en una tarea específica."""
        try:
            # Preparar prompt
            prompt = f"""Basándote únicamente en la información proporcionada en el contexto a continuación, responde a la pregunta.

Contexto:
{task.context}

Pregunta: {task.question}

Responde de manera concisa y directa. Si la información no está en el contexto, di "No puedo encontrar esa información en el contexto proporcionado"."""

            # Medir tiempo y energía
            start_time = time.time()

            # Generar respuesta
            response, metrics = model.generate(prompt, max_tokens=200, temperature=0.1)

            end_time = time.time()
            latency = end_time - start_time

            # Evaluar precisión
            accuracy = self._evaluate_answer(response, task.expected_answer)

            # Crear resultado
            result = RagNeedleResult(
                model_name=model_name,
                context_size=task.context_length_tokens,
                task_id=task.task_id,
                accuracy=accuracy,
                latency=latency,
                tokens_processed=task.context_length_tokens,
                energy_joules=metrics.get('energy_joules', 0.0),
                success=True
            )

            return result

        except Exception as e:
            logger.error(f"Error evaluando {model_name} en tarea {task.task_id}: {e}")
            return RagNeedleResult(
                model_name=model_name,
                context_size=task.context_length_tokens,
                task_id=task.task_id,
                accuracy=0.0,
                latency=self.config.timeout_seconds,
                tokens_processed=task.context_length_tokens,
                success=False,
                error=str(e)
            )

    def _evaluate_answer(self, response: str, expected_answer: str) -> float:
        """Evalúa si la respuesta es correcta."""
        if not response or not expected_answer:
            return 0.0

        # Normalizar respuestas
        response_norm = response.lower().strip()
        expected_norm = expected_answer.lower().strip()

        # Remover puntuación
        import re
        response_norm = re.sub(r'[^\w\s]', '', response_norm)
        expected_norm = re.sub(r'[^\w\s]', '', expected_norm)

        # Verificar si la respuesta esperada está contenida en la respuesta
        if expected_norm in response_norm:
            return 1.0

        # Verificar similitud de palabras clave
        expected_words = set(expected_norm.split())
        response_words = set(response_norm.split())

        if expected_words.issubset(response_words):
            return 1.0

        # Verificar si menciona que no puede encontrar la información
        if "no puedo encontrar" in response_norm or "no está en el contexto" in response_norm:
            return 0.0

        # Verificar respuestas parciales (al menos 70% de overlap)
        overlap = len(expected_words.intersection(response_words))
        if overlap / len(expected_words) >= 0.7:
            return 1.0

        return 0.0

    def run_evaluation(self) -> List[RagNeedleResult]:
        """Ejecuta la evaluación completa."""
        logger.info("🚀 Iniciando evaluación RAG Needle-in-Haystack")

        # Generar tareas
        tasks = self.generate_tasks()

        # Ejecutar evaluación
        all_results = []

        for model_name, model in self.models.items():
            logger.info(f"🤖 Evaluando modelo: {model_name}")

            model_results = []

            # Procesar tareas en paralelo
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                for task in tasks:
                    future = executor.submit(self.evaluate_model_on_task, model_name, model, task)
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        model_results.append(result)
                        all_results.append(result)

                        # Log progreso
                        accuracy = result.accuracy
                        logger.info(f"  ✅ Tarea {result.task_id}: Precisión {accuracy:.1f}, Latencia {result.latency:.2f}s")

                    except Exception as e:
                        logger.error(f"Error procesando resultado: {e}")

            logger.info(f"✅ Modelo {model_name} evaluado en {len(model_results)} tareas")

        self.results = all_results
        logger.info("✅ Evaluación RAG Needle-in-Haystack completada")
        return all_results

    def generate_reports(self):
        """Genera reportes con métricas y gráficos."""
        if not self.results:
            logger.warning("No hay resultados para generar reportes")
            return

        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # Convertir resultados a DataFrame
        df = pd.DataFrame([{
            'model_name': r.model_name,
            'context_size': r.context_size,
            'task_id': r.task_id,
            'accuracy': r.accuracy,
            'latency': r.latency,
            'tokens_processed': r.tokens_processed,
            'energy_joules': r.energy_joules,
            'success': r.success,
            'error': r.error
        } for r in self.results])

        # Reporte JSON
        json_file = os.path.join(self.config.output_dir, f'rag_needle_results_{timestamp}.json')
        df.to_json(json_file, orient='records', indent=2)

        # Reporte CSV
        csv_file = os.path.join(self.config.output_dir, f'rag_needle_results_{timestamp}.csv')
        df.to_csv(csv_file, index=False)

        # Generar gráficos si está disponible y configurado
        if PLOTTING_AVAILABLE and self.config.generate_plots:
            self._generate_plots(df, timestamp)

        # Generar reporte de resumen
        self._generate_summary_report(df, timestamp)

        logger.info(f"📊 Reportes guardados en {self.config.output_dir}")

    def _generate_plots(self, df: pd.DataFrame, timestamp: str):
        """Genera gráficos de precisión vs contexto."""
        # Agrupar por modelo y tamaño de contexto
        summary = df.groupby(['model_name', 'context_size']).agg({
            'accuracy': ['mean', 'std'],
            'latency': ['mean', 'std'],
            'energy_joules': 'mean'
        }).round(3)

        # Gráfico de precisión vs tamaño de contexto
        plt.figure(figsize=(12, 8))

        plt.subplot(2, 2, 1)
        for model in df['model_name'].unique():
            model_data = df[df['model_name'] == model]
            avg_accuracy = model_data.groupby('context_size')['accuracy'].mean()
            plt.plot(avg_accuracy.index, avg_accuracy.values, marker='o', label=model, linewidth=2)

        plt.xlabel('Tamaño del Contexto (tokens)')
        plt.ylabel('Precisión Promedio')
        plt.title('Precisión vs Tamaño del Contexto')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')

        # Gráfico de latencia vs tamaño de contexto
        plt.subplot(2, 2, 2)
        for model in df['model_name'].unique():
            model_data = df[df['model_name'] == model]
            avg_latency = model_data.groupby('context_size')['latency'].mean()
            plt.plot(avg_latency.index, avg_latency.values, marker='s', label=model, linewidth=2)

        plt.xlabel('Tamaño del Contexto (tokens)')
        plt.ylabel('Latencia Promedio (s)')
        plt.title('Latencia vs Tamaño del Contexto')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')

        # Gráfico de energía vs tamaño de contexto
        plt.subplot(2, 2, 3)
        for model in df['model_name'].unique():
            model_data = df[df['model_name'] == model]
            avg_energy = model_data.groupby('context_size')['energy_joules'].mean()
            plt.plot(avg_energy.index, avg_energy.values, marker='^', label=model, linewidth=2)

        plt.xlabel('Tamaño del Contexto (tokens)')
        plt.ylabel('Energía Promedio (J)')
        plt.title('Consumo Energético vs Tamaño del Contexto')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')

        # Gráfico de distribución de precisión por modelo
        plt.subplot(2, 2, 4)
        accuracy_by_model = df.groupby('model_name')['accuracy'].mean()
        accuracy_by_model.plot(kind='bar', color=['skyblue', 'lightgreen', 'orange', 'pink'])
        plt.xlabel('Modelo')
        plt.ylabel('Precisión Promedio')
        plt.title('Precisión Promedio por Modelo')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')

        try:
            plt.tight_layout()
        except UserWarning:
            pass  # Layout already tight

        # Guardar gráfico
        plot_file = os.path.join(self.config.output_dir, f'rag_needle_analysis_{timestamp}.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📈 Gráfico guardado: {plot_file}")

    def _generate_summary_report(self, df: pd.DataFrame, timestamp: str):
        """Genera reporte de resumen."""
        summary_file = os.path.join(self.config.output_dir, f'rag_needle_summary_{timestamp}.txt')

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("🚀 Evaluación RAG Needle-in-Haystack - Resumen\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Estadísticas generales
            f.write("📊 ESTADÍSTICAS GENERALES\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total de evaluaciones: {len(df)}\n")
            f.write(f"Tamaños de contexto probados: {sorted(df['context_size'].unique())}\n")
            f.write(f"Modelos evaluados: {list(df['model_name'].unique())}\n\n")

            # Rendimiento por modelo
            f.write("🤖 RENDIMIENTO POR MODELO\n")
            f.write("-" * 30 + "\n")

            for model in df['model_name'].unique():
                model_data = df[df['model_name'] == model]
                avg_accuracy = model_data['accuracy'].mean()
                avg_latency = model_data['latency'].mean()
                avg_energy = model_data['energy_joules'].mean()

                f.write(f"\n{model.upper()}:\n")
                f.write(f"  Precisión promedio: {avg_accuracy:.3f}\n")
                f.write(f"  Latencia promedio: {avg_latency:.2f}s\n")
                f.write(f"  Energía promedio: {avg_energy:.2f}J\n")

                # Rendimiento por tamaño de contexto
                f.write("  Por tamaño de contexto:\n")
                for context_size in sorted(model_data['context_size'].unique()):
                    context_data = model_data[model_data['context_size'] == context_size]
                    context_accuracy = context_data['accuracy'].mean()
                    f.write(f"    {context_size} tokens: {context_accuracy:.3f}\n")

            # Análisis de degradación
            f.write("\n📉 ANÁLISIS DE DEGRADACIÓN\n")
            f.write("-" * 30 + "\n")

            for model in df['model_name'].unique():
                model_data = df[df['model_name'] == model]
                degradation_data = []

                for context_size in sorted(model_data['context_size'].unique()):
                    context_accuracy = model_data[model_data['context_size'] == context_size]['accuracy'].mean()
                    degradation_data.append((context_size, context_accuracy))

                if len(degradation_data) > 1:
                    f.write(f"\n{model.upper()} - Degradación de precisión:\n")
                    baseline_accuracy = degradation_data[0][1]
                    for size, accuracy in degradation_data:
                        degradation = (baseline_accuracy - accuracy) / baseline_accuracy * 100
                        f.write(f"  {size} tokens: {degradation:+.1f}% vs baseline\n")

            f.write("\n💡 CONCLUSIONES\n")
            f.write("-" * 30 + "\n")
            f.write("Esta evaluación mide la capacidad de los modelos para recuperar\n")
            f.write("información específica ('needle') de contextos largos ('haystack').\n")
            f.write("Un rendimiento perfecto sería mantener precisión alta incluso en\n")
            f.write("contextos muy largos.\n")

        logger.info(f"📋 Reporte de resumen guardado: {summary_file}")


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Evaluador RAG Needle-in-Haystack')
    parser.add_argument('--config', type=str, help='Archivo de configuración JSON')
    parser.add_argument('--models', nargs='+', help='Modelos a testear')
    parser.add_argument('--context-sizes', nargs='+', type=int, help='Tamaños de contexto en tokens')
    parser.add_argument('--num-tasks', type=int, default=10, help='Número de tareas por configuración')
    parser.add_argument('--output', type=str, default='./rag_needle_results', help='Directorio de salida')
    parser.add_argument('--openai-key', type=str, help='API key de OpenAI')
    parser.add_argument('--anthropic-key', type=str, help='API key de Anthropic')
    parser.add_argument('--google-key', type=str, help='API key de Google')

    args = parser.parse_args()

    # Configuración por defecto
    config = RagNeedleConfig()

    # Sobrescribir con argumentos
    if args.models:
        config.models_to_test = args.models
    if args.context_sizes:
        config.context_sizes = args.context_sizes
    if args.num_tasks:
        config.num_tasks_per_size = args.num_tasks
    if args.output:
        config.output_dir = args.output

    # API keys
    if args.openai_key:
        config.api_keys['openai'] = args.openai_key
    if args.anthropic_key:
        config.api_keys['anthropic'] = args.anthropic_key
    if args.google_key:
        config.api_keys['google'] = args.google_key

    # Cargar desde archivo si especificado
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

    # Ejecutar evaluación
    print("🚀 Iniciando evaluación RAG Needle-in-Haystack...")
    evaluator = RagNeedleEvaluator(config)
    results = evaluator.run_evaluation()

    # Generar reportes
    evaluator.generate_reports()

    print("\n🎉 Evaluación completada!")
    print(f"📁 Resultados guardados en: {config.output_dir}")

    # Mostrar resumen
    if results:
        print("\n📊 Resumen de resultados:")
        for model in config.models_to_test:
            model_results = [r for r in results if r.model_name == model]
            if model_results:
                avg_accuracy = sum(r.accuracy for r in model_results) / len(model_results)
                avg_latency = sum(r.latency for r in model_results) / len(model_results)
                print(f"🤖 {model}: Precisión {avg_accuracy:.3f}, Latencia {avg_latency:.2f}s")


if __name__ == "__main__":
    main()