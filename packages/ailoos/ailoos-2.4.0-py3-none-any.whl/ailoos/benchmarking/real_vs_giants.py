"""
Real Benchmarks vs GPT-4 and Giants
===================================

Sistema de benchmarking real que compara EmpoorioLM con GPT-4, Claude, Gemini.
Ejecuta evaluaciones objetivas en tareas reales para medir competitividad.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import openai
import anthropic
import google.generativeai as genai

from ..inference.api import EmpoorioLMInferenceAPI, InferenceConfig, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkTask:
    """Tarea de benchmark con prompt y criterios de evaluación."""
    name: str
    category: str
    prompt: str
    evaluation_criteria: Dict[str, Any]
    expected_complexity: str = "medium"  # simple, medium, complex


@dataclass
class ModelResponse:
    """Respuesta de un modelo en el benchmark."""
    model_name: str
    task_name: str
    response: str
    response_time: float
    token_count: int
    error: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Resultado de benchmark para un modelo."""
    model_name: str
    task_name: str
    score: float  # 0.0 to 1.0
    raw_score: float
    max_score: float
    evaluation_details: Dict[str, Any]
    response_time: float
    tokens_used: int


@dataclass
class BenchmarkSuite:
    """Suite completa de benchmarks."""
    name: str
    tasks: List[BenchmarkTask] = field(default_factory=list)
    models_to_test: List[str] = field(default_factory=list)
    results: List[BenchmarkResult] = field(default_factory=list)

    def add_task(self, task: BenchmarkTask):
        self.tasks.append(task)

    def add_model(self, model_name: str):
        if model_name not in self.models_to_test:
            self.models_to_test.append(model_name)


class GiantsBenchmarkRunner:
    """
    Ejecuta benchmarks reales contra GPT-4, Claude, Gemini y EmpoorioLM.
    Mide rendimiento objetivo en tareas reales.
    """

    def __init__(self):
        self.empoorio_api: Optional[EmpoorioLMInferenceAPI] = None
        self.session = aiohttp.ClientSession()

        # API clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None

        # Benchmark suites
        self.suites = self._create_benchmark_suites()

    async def initialize(self) -> bool:
        """Initialize all model APIs."""
        try:
            logger.info("🚀 Initializing Real Benchmarks vs Giants...")

            # Initialize EmpoorioLM
            config = InferenceConfig()
            self.empoorio_api = EmpoorioLMInferenceAPI(config)
            if not await self.empoorio_api.load_model():
                logger.error("❌ Failed to load EmpoorioLM")
                return False

            # Initialize external APIs (with error handling)
            await self._initialize_external_apis()

            logger.info("✅ All APIs initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize benchmark runner: {e}")
            return False

    async def _initialize_external_apis(self):
        """Initialize external API clients."""
        # OpenAI
        try:
            if "OPENAI_API_KEY" in os.environ:
                self.openai_client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
                logger.info("✅ OpenAI API initialized")
            else:
                logger.warning("⚠️ OPENAI_API_KEY not found - GPT-4 benchmarks disabled")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI initialization failed: {e}")

        # Anthropic
        try:
            if "ANTHROPIC_API_KEY" in os.environ:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
                logger.info("✅ Anthropic API initialized")
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY not found - Claude benchmarks disabled")
        except Exception as e:
            logger.warning(f"⚠️ Anthropic initialization failed: {e}")

        # Google Gemini
        try:
            if "GOOGLE_API_KEY" in os.environ:
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Google Gemini API initialized")
            else:
                logger.warning("⚠️ GOOGLE_API_KEY not found - Gemini benchmarks disabled")
        except Exception as e:
            logger.warning(f"⚠️ Gemini initialization failed: {e}")

    def _create_benchmark_suites(self) -> Dict[str, BenchmarkSuite]:
        """Create comprehensive benchmark suites."""
        return {
            "reasoning": self._create_reasoning_suite(),
            "coding": self._create_coding_suite(),
            "knowledge": self._create_knowledge_suite(),
            "creativity": self._create_creativity_suite(),
            "analysis": self._create_analysis_suite()
        }

    def _create_reasoning_suite(self) -> BenchmarkSuite:
        """Create reasoning benchmark suite."""
        suite = BenchmarkSuite("reasoning")

        # Logical reasoning
        suite.add_task(BenchmarkTask(
            name="syllogism",
            category="logic",
            prompt="All roses are flowers. Some flowers fade quickly. Therefore: A) Some roses fade quickly B) All flowers are roses C) Some flowers are not roses D) No roses fade quickly",
            evaluation_criteria={
                "correct_answer": "C",
                "scoring": {"exact_match": 1.0, "partial": 0.5, "wrong": 0.0}
            }
        ))

        # Mathematical reasoning
        suite.add_task(BenchmarkTask(
            name="math_word_problem",
            category="math",
            prompt="A train travels at 80 km/h for 2 hours, then slows to 60 km/h for 1.5 hours. What is the average speed for the entire journey?",
            evaluation_criteria={
                "correct_answer": 72.0,
                "tolerance": 0.1,
                "scoring": {"exact": 1.0, "close": 0.7, "reasonable": 0.4, "wrong": 0.0}
            }
        ))

        # Causal reasoning
        suite.add_task(BenchmarkTask(
            name="causal_analysis",
            category="causality",
            prompt="If a company reduces prices by 10%, demand increases by 15%, but profit decreases by 5%. Explain why this might happen and suggest what the company should do.",
            evaluation_criteria={
                "key_points": ["cost of goods", "elasticity", "margins", "volume vs price"],
                "scoring": {"comprehensive": 1.0, "good": 0.8, "basic": 0.6, "poor": 0.3}
            }
        ))

        return suite

    def _create_coding_suite(self) -> BenchmarkSuite:
        """Create coding benchmark suite."""
        suite = BenchmarkSuite("coding")

        suite.add_task(BenchmarkTask(
            name="algorithm_explanation",
            category="algorithms",
            prompt="Explain how quicksort works and analyze its time complexity. Provide a Python implementation.",
            evaluation_criteria={
                "requirements": ["partition", "recursion", "pivot", "O(n log n)", "code"],
                "scoring": {"complete": 1.0, "good": 0.8, "partial": 0.6, "minimal": 0.3}
            }
        ))

        suite.add_task(BenchmarkTask(
            name="debugging",
            category="debugging",
            prompt="This Python function has a bug: def find_max(arr): return max(arr) if arr else None. It fails on [1, 2, '3']. Fix it to handle mixed types.",
            evaluation_criteria={
                "correct_fix": True,
                "handles_types": True,
                "scoring": {"perfect": 1.0, "good": 0.8, "partial": 0.5, "wrong": 0.0}
            }
        ))

        return suite

    def _create_knowledge_suite(self) -> BenchmarkSuite:
        """Create knowledge benchmark suite."""
        suite = BenchmarkSuite("knowledge")

        suite.add_task(BenchmarkTask(
            name="science_explanation",
            category="science",
            prompt="Explain quantum entanglement in simple terms that a high school student could understand.",
            evaluation_criteria={
                "key_concepts": ["spooky action", "measurement", "correlation", "no communication"],
                "accuracy": True,
                "clarity": True,
                "scoring": {"excellent": 1.0, "good": 0.8, "fair": 0.6, "poor": 0.4}
            }
        ))

        suite.add_task(BenchmarkTask(
            name="current_events",
            category="current_events",
            prompt="What are the main challenges facing renewable energy adoption globally in 2024?",
            evaluation_criteria={
                "relevance": True,
                "comprehensiveness": True,
                "current": True,
                "scoring": {"comprehensive": 1.0, "good": 0.8, "basic": 0.6, "outdated": 0.3}
            }
        ))

        return suite

    def _create_creativity_suite(self) -> BenchmarkSuite:
        """Create creativity benchmark suite."""
        suite = BenchmarkSuite("creativity")

        suite.add_task(BenchmarkTask(
            name="storytelling",
            category="creative_writing",
            prompt="Write a short story (200-300 words) about a robot who falls in love with a human. Include a surprising twist.",
            evaluation_criteria={
                "creativity": True,
                "coherence": True,
                "twist": True,
                "length_appropriate": True,
                "scoring": {"excellent": 1.0, "good": 0.8, "fair": 0.6, "poor": 0.4}
            }
        ))

        return suite

    def _create_analysis_suite(self) -> BenchmarkSuite:
        """Create analysis benchmark suite."""
        suite = BenchmarkSuite("analysis")

        suite.add_task(BenchmarkTask(
            name="data_analysis",
            category="analytics",
            prompt="Analyze this sales data trend: Q1: $100k, Q2: $120k, Q3: $90k, Q4: $140k. What insights can you draw? What recommendations would you make?",
            evaluation_criteria={
                "insights": ["seasonality", "growth", "q3_decline"],
                "recommendations": True,
                "scoring": {"comprehensive": 1.0, "good": 0.8, "basic": 0.6, "poor": 0.3}
            }
        ))

        return suite

    async def run_benchmark_suite(self, suite_name: str, models: List[str] = None) -> Dict[str, Any]:
        """
        Run a complete benchmark suite against specified models.

        Args:
            suite_name: Name of the benchmark suite
            models: List of models to test (default: all available)

        Returns:
            Complete benchmark results
        """
        if suite_name not in self.suites:
            raise ValueError(f"Unknown benchmark suite: {suite_name}")

        suite = self.suites[suite_name]

        # Determine which models to test
        if models is None:
            models = ["empoorio_lm"]
            if self.openai_client:
                models.append("gpt-4")
            if self.anthropic_client:
                models.append("claude-3")
            if self.gemini_client:
                models.append("gemini-pro")

        suite.models_to_test = models

        logger.info(f"🏁 Starting {suite_name} benchmark suite")
        logger.info(f"📊 Models to test: {', '.join(models)}")
        logger.info(f"🎯 Tasks: {len(suite.tasks)}")

        start_time = time.time()

        # Run all tasks for all models
        for task in suite.tasks:
            logger.info(f"🔄 Running task: {task.name}")

            for model_name in models:
                try:
                    result = await self._run_single_task(task, model_name)
                    suite.results.append(result)
                    logger.info(".2f"
                               ".2f")

                except Exception as e:
                    logger.error(f"❌ Error running {model_name} on {task.name}: {e}")
                    # Add failed result
                    suite.results.append(BenchmarkResult(
                        model_name=model_name,
                        task_name=task.name,
                        score=0.0,
                        raw_score=0.0,
                        max_score=1.0,
                        evaluation_details={"error": str(e)},
                        response_time=0.0,
                        tokens_used=0
                    ))

        total_time = time.time() - start_time

        # Aggregate results
        summary = self._create_summary_report(suite, total_time)

        logger.info(f"✅ Benchmark suite completed in {total_time:.1f}s")
        logger.info(f"📊 Results saved to benchmark_results_{suite_name}_{int(time.time())}.json")

        return summary

    async def _run_single_task(self, task: BenchmarkTask, model_name: str) -> BenchmarkResult:
        """Run a single task on a specific model."""
        start_time = time.time()

        try:
            # Get model response
            response_data = await self._get_model_response(task.prompt, model_name)
            response_time = time.time() - start_time

            if "error" in response_data:
                return BenchmarkResult(
                    model_name=model_name,
                    task_name=task.name,
                    score=0.0,
                    raw_score=0.0,
                    max_score=1.0,
                    evaluation_details={"error": response_data["error"]},
                    response_time=response_time,
                    tokens_used=0
                )

            response_text = response_data["response"]
            tokens_used = response_data.get("tokens", 0)

            # Evaluate response
            evaluation = self._evaluate_response(response_text, task)

            return BenchmarkResult(
                model_name=model_name,
                task_name=task.name,
                score=evaluation["score"],
                raw_score=evaluation["raw_score"],
                max_score=evaluation["max_score"],
                evaluation_details=evaluation["details"],
                response_time=response_time,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Error in _run_single_task: {e}")
            return BenchmarkResult(
                model_name=model_name,
                task_name=task.name,
                score=0.0,
                raw_score=0.0,
                max_score=1.0,
                evaluation_details={"error": str(e)},
                response_time=time.time() - start_time,
                tokens_used=0
            )

    async def _get_model_response(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """Get response from a specific model."""
        try:
            if model_name == "empoorio_lm":
                return await self._get_empoorio_response(prompt)
            elif model_name == "gpt-4":
                return await self._get_openai_response(prompt, "gpt-4")
            elif model_name == "claude-3":
                return await self._get_anthropic_response(prompt)
            elif model_name == "gemini-pro":
                return await self._get_gemini_response(prompt)
            else:
                return {"error": f"Unknown model: {model_name}"}

        except Exception as e:
            return {"error": str(e)}

    async def _get_empoorio_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from EmpoorioLM."""
        request = InferenceRequest(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7
        )

        response = await self.empoorio_api.generate(request)

        return {
            "response": response.text,
            "tokens": response.usage.get("completion_tokens", 0)
        }

    async def _get_openai_response(self, prompt: str, model: str) -> Dict[str, Any]:
        """Get response from OpenAI."""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7
        )

        return {
            "response": response.choices[0].message.content,
            "tokens": response.usage.completion_tokens
        }

    async def _get_anthropic_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from Anthropic."""
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")

        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "response": response.content[0].text,
            "tokens": response.usage.output_tokens
        }

    async def _get_gemini_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from Google Gemini."""
        if not self.gemini_client:
            raise Exception("Gemini client not initialized")

        response = await self.gemini_client.generate_content_async(prompt)

        return {
            "response": response.text,
            "tokens": len(response.text.split())  # Rough estimate
        }

    def _evaluate_response(self, response: str, task: BenchmarkTask) -> Dict[str, Any]:
        """Evaluate a model response against task criteria."""
        criteria = task.evaluation_criteria

        if task.name == "syllogism":
            return self._evaluate_syllogism(response, criteria)
        elif task.name == "math_word_problem":
            return self._evaluate_math_problem(response, criteria)
        elif task.name == "causal_analysis":
            return self._evaluate_causal_analysis(response, criteria)
        elif task.name == "algorithm_explanation":
            return self._evaluate_algorithm_explanation(response, criteria)
        elif task.name == "debugging":
            return self._evaluate_debugging(response, criteria)
        elif task.name == "science_explanation":
            return self._evaluate_science_explanation(response, criteria)
        elif task.name == "current_events":
            return self._evaluate_current_events(response, criteria)
        elif task.name == "storytelling":
            return self._evaluate_storytelling(response, criteria)
        elif task.name == "data_analysis":
            return self._evaluate_data_analysis(response, criteria)
        else:
            # Generic evaluation
            return {
                "score": 0.5,  # Neutral score for unknown tasks
                "raw_score": 0.5,
                "max_score": 1.0,
                "details": {"method": "generic", "response_length": len(response)}
            }

    def _evaluate_syllogism(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate syllogism response."""
        correct_answer = criteria["correct_answer"]
        response_lower = response.lower()

        if correct_answer.lower() in response_lower:
            score = 1.0
        elif any(ans in response_lower for ans in ["a)", "b)", "d)"]):
            score = 0.0  # Wrong answer
        else:
            score = 0.3  # Partial or unclear

        return {
            "score": score,
            "raw_score": score,
            "max_score": 1.0,
            "details": {
                "correct_answer": correct_answer,
                "found_correct": correct_answer.lower() in response_lower
            }
        }

    def _evaluate_math_problem(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate math word problem."""
        correct_answer = criteria["correct_answer"]
        tolerance = criteria.get("tolerance", 0.1)

        # Extract numbers from response
        import re
        numbers = re.findall(r'\d+\.?\d*', response)
        numbers = [float(n) for n in numbers if float(n) > 0]

        if not numbers:
            return {"score": 0.0, "raw_score": 0.0, "max_score": 1.0, "details": {"no_numbers_found": True}}

        closest = min(numbers, key=lambda x: abs(x - correct_answer))
        diff = abs(closest - correct_answer)

        if diff <= tolerance:
            score = 1.0
        elif diff <= tolerance * 3:
            score = 0.7
        elif diff <= tolerance * 10:
            score = 0.4
        else:
            score = 0.0

        return {
            "score": score,
            "raw_score": closest,
            "max_score": correct_answer,
            "details": {"closest_answer": closest, "difference": diff}
        }

    def _evaluate_causal_analysis(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate causal analysis response."""
        key_points = criteria["key_points"]
        response_lower = response.lower()

        points_found = sum(1 for point in key_points if point.lower() in response_lower)
        coverage = points_found / len(key_points)

        if coverage >= 0.8:
            score = 1.0
        elif coverage >= 0.6:
            score = 0.8
        elif coverage >= 0.4:
            score = 0.6
        elif coverage >= 0.2:
            score = 0.3
        else:
            score = 0.1

        return {
            "score": score,
            "raw_score": points_found,
            "max_score": len(key_points),
            "details": {"points_found": points_found, "coverage": coverage}
        }

    def _evaluate_algorithm_explanation(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate algorithm explanation."""
        requirements = criteria["requirements"]
        response_lower = response.lower()

        req_met = sum(1 for req in requirements if req.lower() in response_lower)
        coverage = req_met / len(requirements)

        # Bonus for code
        has_code = "def " in response_lower or "function" in response_lower

        score = coverage
        if has_code:
            score = min(1.0, score + 0.2)

        return {
            "score": score,
            "raw_score": req_met,
            "max_score": len(requirements),
            "details": {"requirements_met": req_met, "has_code": has_code}
        }

    def _evaluate_debugging(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate debugging task."""
        # Check if response contains type checking or conversion
        response_lower = response.lower()

        has_type_check = any(term in response_lower for term in ["isinstance", "type(", "int(", "str(", "try:", "except"])
        has_conversion = any(term in response_lower for term in ["int(", "float(", "str("])

        if has_type_check and has_conversion:
            score = 1.0
        elif has_type_check or has_conversion:
            score = 0.7
        else:
            score = 0.3

        return {
            "score": score,
            "raw_score": score,
            "max_score": 1.0,
            "details": {"type_checking": has_type_check, "conversion": has_conversion}
        }

    def _evaluate_science_explanation(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate science explanation."""
        key_concepts = criteria["key_concepts"]
        response_lower = response.lower()

        concepts_found = sum(1 for concept in key_concepts if concept.lower() in response_lower)
        coverage = concepts_found / len(key_concepts)

        # Check clarity (length and structure)
        word_count = len(response.split())
        has_structure = any(indicator in response_lower for indicator in ["first", "second", "example", "in other words"])

        clarity_bonus = 0.1 if (word_count > 50 and has_structure) else 0.0

        score = min(1.0, coverage + clarity_bonus)

        return {
            "score": score,
            "raw_score": concepts_found,
            "max_score": len(key_concepts),
            "details": {"concepts_found": concepts_found, "clarity_bonus": clarity_bonus}
        }

    def _evaluate_current_events(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate current events response."""
        # This is subjective - use length and coherence as proxy
        word_count = len(response.split())
        has_structure = len(response.split('.')) > 3  # Multiple sentences
        has_specifics = any(term in response.lower() for term in ["cost", "policy", "technology", "infrastructure"])

        if word_count > 100 and has_structure and has_specifics:
            score = 1.0
        elif word_count > 50 and (has_structure or has_specifics):
            score = 0.7
        elif word_count > 20:
            score = 0.5
        else:
            score = 0.3

        return {
            "score": score,
            "raw_score": word_count,
            "max_score": 200,  # Expected word count
            "details": {"word_count": word_count, "structured": has_structure, "specific": has_specifics}
        }

    def _evaluate_storytelling(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate creative storytelling."""
        word_count = len(response.split())

        # Check for story elements
        has_character = any(term in response.lower() for term in ["robot", "human", "love", "fell in love"])
        has_twist = any(term in response.lower() for term in ["but", "however", "surprisingly", "twist", "reveal"])
        has_emotion = any(term in response.lower() for term in ["felt", "emotion", "heart", "feelings"])

        # Length appropriate (200-300 words)
        length_score = 1.0 if 150 <= word_count <= 400 else 0.5

        element_score = (has_character + has_twist + has_emotion) / 3

        score = (length_score + element_score) / 2

        return {
            "score": score,
            "raw_score": word_count,
            "max_score": 300,
            "details": {
                "word_count": word_count,
                "has_character": has_character,
                "has_twist": has_twist,
                "has_emotion": has_emotion
            }
        }

    def _evaluate_data_analysis(self, response: str, criteria: Dict) -> Dict[str, Any]:
        """Evaluate data analysis response."""
        insights = criteria["insights"]
        response_lower = response.lower()

        insights_found = sum(1 for insight in insights if insight.lower() in response_lower)
        coverage = insights_found / len(insights)

        has_recommendations = any(term in response_lower for term in ["recommend", "suggest", "should", "could"])

        score = coverage
        if has_recommendations:
            score = min(1.0, score + 0.2)

        return {
            "score": score,
            "raw_score": insights_found,
            "max_score": len(insights),
            "details": {"insights_found": insights_found, "has_recommendations": has_recommendations}
        }

    def _create_summary_report(self, suite: BenchmarkSuite, total_time: float) -> Dict[str, Any]:
        """Create comprehensive summary report."""
        # Group results by model
        model_results = {}
        for result in suite.results:
            if result.model_name not in model_results:
                model_results[result.model_name] = []
            model_results[result.model_name].append(result)

        # Calculate averages per model
        summary = {
            "suite_name": suite.name,
            "total_tasks": len(suite.tasks),
            "models_tested": list(model_results.keys()),
            "total_time": total_time,
            "timestamp": datetime.now().isoformat(),
            "model_summaries": {}
        }

        for model_name, results in model_results.items():
            scores = [r.score for r in results]
            response_times = [r.response_time for r in results]
            tokens_used = [r.tokens_used for r in results]

            summary["model_summaries"][model_name] = {
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "average_response_time": sum(response_times) / len(response_times),
                "total_tokens": sum(tokens_used),
                "tasks_completed": len(results),
                "task_breakdown": [
                    {
                        "task": r.task_name,
                        "score": r.score,
                        "response_time": r.response_time,
                        "tokens": r.tokens_used
                    } for r in results
                ]
            }

        # Save detailed results
        filename = f"benchmark_results_{suite.name}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump({
                "summary": summary,
                "detailed_results": [
                    {
                        "model": r.model_name,
                        "task": r.task_name,
                        "score": r.score,
                        "response_time": r.response_time,
                        "tokens": r.tokens_used,
                        "evaluation": r.evaluation_details
                    } for r in suite.results
                ]
            }, f, indent=2)

        return summary

    async def run_all_suites(self, models: List[str] = None) -> Dict[str, Any]:
        """Run all benchmark suites."""
        all_results = {}

        for suite_name in self.suites.keys():
            logger.info(f"🏁 Running suite: {suite_name}")
            try:
                result = await self.run_benchmark_suite(suite_name, models)
                all_results[suite_name] = result
            except Exception as e:
                logger.error(f"❌ Failed to run suite {suite_name}: {e}")
                all_results[suite_name] = {"error": str(e)}

        # Create overall summary
        overall_summary = self._create_overall_summary(all_results)

        return {
            "individual_suites": all_results,
            "overall_summary": overall_summary
        }

    def _create_overall_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create overall summary across all suites."""
        # Collect all model performances
        model_overall_scores = {}

        for suite_name, suite_result in all_results.items():
            if "error" in suite_result:
                continue

            for model_name, model_summary in suite_result.get("model_summaries", {}).items():
                if model_name not in model_overall_scores:
                    model_overall_scores[model_name] = []

                model_overall_scores[model_name].append(model_summary["average_score"])

        # Calculate overall averages
        overall_summary = {}
        for model_name, scores in model_overall_scores.items():
            overall_summary[model_name] = {
                "overall_average_score": sum(scores) / len(scores),
                "suites_completed": len(scores),
                "score_range": f"{min(scores):.3f} - {max(scores):.3f}",
                "consistency": 1.0 - (max(scores) - min(scores))  # Lower variance = higher consistency
            }

        return overall_summary

    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()


async def run_real_benchmarks_vs_giants(
    suites: List[str] = None,
    models: List[str] = None
) -> Dict[str, Any]:
    """
    Función principal para ejecutar benchmarks reales vs modelos gigantes.

    Args:
        suites: Lista de suites a ejecutar (default: all)
        models: Lista de modelos a probar (default: available)

    Returns:
        Resultados completos de benchmarks
    """
    if suites is None:
        suites = ["reasoning", "coding", "knowledge", "creativity", "analysis"]

    logger.info("🚀 Starting Real Benchmarks vs GPT-4 and Giants")
    logger.info(f"🎯 Suites: {', '.join(suites)}")

    runner = GiantsBenchmarkRunner()

    try:
        # Initialize
        if not await runner.initialize():
            raise RuntimeError("Failed to initialize benchmark runner")

        # Run benchmarks
        if len(suites) == 1:
            results = await runner.run_benchmark_suite(suites[0], models)
        else:
            results = await runner.run_all_suites(models)

        # Print summary
        logger.info("🏁 Benchmarks completed!")
        logger.info("📊 Results Summary:")

        if "overall_summary" in results:
            for model, summary in results["overall_summary"].items():
                logger.info(".3f"
                           ".3f")
        else:
            # Single suite results
            for model, summary in results.get("model_summaries", {}).items():
                logger.info(".3f"
                           ".3f")

        return results

    finally:
        await runner.close()


if __name__ == "__main__":
    # Example usage
    import os

    # Set API keys if available
    # os.environ["OPENAI_API_KEY"] = "your-key"
    # os.environ["ANTHROPIC_API_KEY"] = "your-key"
    # os.environ["GOOGLE_API_KEY"] = "your-key"

    asyncio.run(run_real_benchmarks_vs_giants(
        suites=["reasoning"],  # Start with one suite
        models=["empoorio_lm"]  # Test EmpoorioLM first
    ))