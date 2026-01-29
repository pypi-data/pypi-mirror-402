"""
EmpoorioLM Advanced Generation System with Reasoning Integration
================================================================

Enhanced inference generation system that integrates advanced reasoning capabilities
with the EmpoorioLM model. Provides intelligent detection of complex queries and
automatic activation of deep thinking workflows.

Features:
- Automatic complexity detection for queries
- Deep thinking workflows with iterative reasoning
- Thinking budget controls and time management
- Integration with reasoning module components
- Backward compatibility with standard generation
- Configurable thresholds and strategies
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from .api import EmpoorioLMInferenceAPI, InferenceConfig, InferenceRequest, InferenceResponse
from ..workflows.engine import WorkflowEngine, ThinkingBudget, IterativeResult
from ..models.empoorio_lm.expert_system import ExpertManager
from ..reasoning import ProblemDecomposer, ResponseCritic, ReflectionEngine

logger = logging.getLogger(__name__)


@dataclass
class ReasoningConfig:
    """Configuration for reasoning-enhanced generation."""

    # Detection thresholds
    complexity_threshold: float = 0.7  # Minimum complexity score to trigger deep thinking
    min_query_length: int = 50  # Minimum query length for complexity analysis
    max_query_length: int = 2000  # Maximum query length to process

    # Thinking budget defaults
    default_max_time_seconds: int = 300  # 5 minutes
    default_max_iterations: int = 5
    default_min_confidence_threshold: float = 0.7
    default_time_per_iteration_seconds: int = 60

    # Reasoning strategies
    enabled_strategies: List[str] = field(default_factory=lambda: [
        "analytical", "creative", "technical", "general"
    ])
    default_strategy: str = "general"

    # Automatic activation
    auto_activate_reasoning: bool = True
    reasoning_success_threshold: float = 0.8  # Minimum success rate to continue using reasoning

    # Performance tuning
    cache_reasoning_results: bool = True
    max_cached_results: int = 100
    reasoning_timeout_buffer: int = 30  # Extra seconds for reasoning timeout

    # Output configuration
    include_reasoning_trace: bool = False  # Include hidden reasoning traces in response
    reasoning_trace_format: str = "structured"  # "structured", "text", "minimal"


@dataclass
class GenerationResult:
    """Enhanced generation result with reasoning information."""

    response: InferenceResponse
    used_reasoning: bool = False
    reasoning_metadata: Optional[Dict[str, Any]] = None
    thinking_time: float = 0.0
    confidence_score: float = 0.0
    reasoning_trace: Optional[Any] = None  # ReasoningTrace or similar

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        base_dict = self.response.to_dict()
        base_dict.update({
            "used_reasoning": self.used_reasoning,
            "thinking_time": self.thinking_time,
            "confidence_score": self.confidence_score,
            "reasoning_metadata": self.reasoning_metadata or {}
        })

        if self.include_reasoning_trace and self.reasoning_trace:
            base_dict["reasoning_trace"] = self.reasoning_trace.to_dict() if hasattr(self.reasoning_trace, 'to_dict') else str(self.reasoning_trace)

        return base_dict


class EmpoorioLMReasoningGenerator:
    """
    Advanced generation system with integrated reasoning capabilities.

    This class extends the basic EmpoorioLM inference with intelligent reasoning
    that automatically detects complex queries and applies appropriate thinking strategies.
    """

    def __init__(self, inference_api: Optional[EmpoorioLMInferenceAPI] = None,
                 expert_manager: Optional[ExpertManager] = None,
                 config: Optional[ReasoningConfig] = None):
        """
        Initialize the reasoning-enhanced generator.

        Args:
            inference_api: Base EmpoorioLM inference API instance
            expert_manager: Expert manager for domain-specific reasoning
            config: Reasoning configuration
        """
        self.inference_api = inference_api
        self.expert_manager = expert_manager or ExpertManager(experts_dir="./src/models/experts")
        self.config = config or ReasoningConfig()

        # Initialize reasoning components
        self.workflow_engine = WorkflowEngine(self.expert_manager, self.inference_api)
        self.problem_decomposer = ProblemDecomposer(self.inference_api)
        self.response_critic = ResponseCritic(self.inference_api)
        self.reflection_engine = ReflectionEngine(self.inference_api)

        # Caching and performance tracking
        self.reasoning_cache: Dict[str, Dict[str, Any]] = {}
        self.performance_stats = {
            "total_generations": 0,
            "reasoning_activations": 0,
            "average_thinking_time": 0.0,
            "cache_hit_rate": 0.0,
            "success_rate": 0.0
        }

        # Strategy configurations
        self.strategy_configs = self._initialize_strategy_configs()

        logger.info("🧠 EmpoorioLM Reasoning Generator initialized")

    def _initialize_strategy_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize configuration for different reasoning strategies."""
        return {
            "analytical": {
                "max_iterations": 6,
                "min_confidence_threshold": 0.8,
                "time_per_iteration_seconds": 60,
                "domain": "research",
                "description": "Analytical reasoning with evidence-based evaluation"
            },
            "creative": {
                "max_iterations": 5,
                "min_confidence_threshold": 0.6,
                "time_per_iteration_seconds": 70,
                "domain": "business_strategy",
                "description": "Creative reasoning with innovative approaches"
            },
            "technical": {
                "max_iterations": 7,
                "min_confidence_threshold": 0.75,
                "time_per_iteration_seconds": 60,
                "domain": "software_development",
                "description": "Technical reasoning for implementation and optimization"
            },
            "general": {
                "max_iterations": self.config.default_max_iterations,
                "min_confidence_threshold": self.config.default_min_confidence_threshold,
                "time_per_iteration_seconds": self.config.default_time_per_iteration_seconds,
                "domain": "general",
                "description": "General purpose reasoning for various domains"
            }
        }

    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Initialize inference API if not provided
            if self.inference_api is None:
                base_config = InferenceConfig(
                    model_path="./src/models/empoorio_lm/versions/empoorio_lm_v1.0.0-trained_267306",
                    enable_guidance=True,
                    guidance_output_format="inference"
                )
                self.inference_api = EmpoorioLMInferenceAPI(base_config)
                success = await self.inference_api.load_model()
                if not success:
                    logger.error("❌ Failed to initialize base inference API")
                    return False

            # Expert manager doesn't need initialization

            # Initialize reasoning components
            await self.problem_decomposer.initialize()
            await self.response_critic.initialize()
            await self.reflection_engine.initialize()

            logger.info("✅ Reasoning Generator fully initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing Reasoning Generator: {e}")
            return False

    def needs_deep_thinking(self, query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Determine if a query requires deep thinking based on complexity analysis.

        Args:
            query: The input query to analyze
            context: Additional context information

        Returns:
            Tuple of (needs_thinking, complexity_score, analysis_metadata)
        """
        if not self.config.auto_activate_reasoning:
            return False, 0.0, {"reason": "auto_activation_disabled"}

        # Basic length check
        query_length = len(query.strip())
        if query_length < self.config.min_query_length:
            return False, 0.0, {"reason": "query_too_short", "length": query_length}

        if query_length > self.config.max_query_length:
            return True, 1.0, {"reason": "query_too_long", "length": query_length}

        # Complexity analysis
        complexity_score = self._analyze_query_complexity(query, context or {})

        needs_thinking = complexity_score >= self.config.complexity_threshold

        metadata = {
            "complexity_score": complexity_score,
            "query_length": query_length,
            "threshold": self.config.complexity_threshold,
            "analysis_factors": self._get_complexity_factors(query)
        }

        logger.info(f"🧠 Complexity analysis: {complexity_score:.2f} {'→ Deep thinking' if needs_thinking else '→ Standard generation'}")

        return needs_thinking, complexity_score, metadata

    def _analyze_query_complexity(self, query: str, context: Dict[str, Any]) -> float:
        """Analyze the complexity of a query using multiple factors."""
        factors = self._get_complexity_factors(query)
        weights = {
            "length_factor": 0.2,
            "keyword_factor": 0.3,
            "structure_factor": 0.25,
            "domain_factor": 0.15,
            "context_factor": 0.1
        }

        # Calculate weighted score
        score = sum(factors[key] * weights[key] for key in factors.keys())
        return min(score, 1.0)  # Cap at 1.0

    def _get_complexity_factors(self, query: str) -> Dict[str, float]:
        """Extract complexity factors from the query."""
        query_lower = query.lower()

        # Length factor (normalized)
        length_factor = min(len(query) / 500, 1.0)

        # Keyword complexity
        complex_keywords = [
            "analyze", "evaluate", "compare", "explain", "design", "implement",
            "optimize", "solve", "create", "develop", "research", "strategy",
            "complex", "advanced", "multiple", "various", "comprehensive"
        ]
        keyword_matches = sum(1 for keyword in complex_keywords if keyword in query_lower)
        keyword_factor = min(keyword_matches / 5, 1.0)

        # Structural complexity
        structure_indicators = [
            re.search(r'\d+\.', query),  # Numbered lists
            re.search(r'[•\-\*]', query),  # Bullet points
            re.search(r'vs\.?|versus', query),  # Comparisons
            re.search(r'how.*\?|why.*\?|what.*\?', query),  # Complex questions
            len(re.findall(r',', query)) > 3,  # Multiple clauses
        ]
        structure_score = sum(1 for indicator in structure_indicators if indicator) / len(structure_indicators)
        structure_factor = min(structure_score, 1.0)

        # Domain complexity (placeholder - could be enhanced with domain detection)
        domain_factor = 0.5  # Default medium complexity

        # Context factor
        context_factor = 0.5  # Default medium complexity

        return {
            "length_factor": length_factor,
            "keyword_factor": keyword_factor,
            "structure_factor": structure_factor,
            "domain_factor": domain_factor,
            "context_factor": context_factor
        }

    async def generate_with_thinking(
        self,
        request: InferenceRequest,
        thinking_budget: Optional[ThinkingBudget] = None,
        reasoning_strategy: Optional[str] = None,
        force_reasoning: bool = False
    ) -> GenerationResult:
        """
        Generate response with intelligent reasoning when appropriate.

        Args:
            request: Standard inference request
            thinking_budget: Custom thinking budget (optional)
            reasoning_strategy: Specific reasoning strategy to use
            force_reasoning: Force use of reasoning regardless of complexity

        Returns:
            Enhanced generation result with reasoning information
        """
        start_time = time.time()
        self.performance_stats["total_generations"] += 1

        try:
            # Determine if reasoning is needed
            needs_thinking, complexity_score, analysis_metadata = self.needs_deep_thinking(
                request.prompt,
                {"context": request.schema, "output_format": request.output_format}
            )

            use_reasoning = force_reasoning or needs_thinking

            if not use_reasoning:
                # Standard generation
                response = await self.inference_api.generate(request)
                thinking_time = time.time() - start_time

                result = GenerationResult(
                    response=response,
                    used_reasoning=False,
                    thinking_time=thinking_time,
                    confidence_score=0.8,  # Default confidence for standard generation
                    reasoning_metadata={
                        "complexity_analysis": analysis_metadata,
                        "reason": "standard_generation"
                    }
                )

                logger.info(f"📝 Standard generation completed in {thinking_time:.2f}s")
                return result

            # Deep thinking generation
            self.performance_stats["reasoning_activations"] += 1

            # Determine strategy
            strategy = reasoning_strategy or self._select_reasoning_strategy(request.prompt, analysis_metadata)

            # Setup thinking budget
            budget = thinking_budget or self._create_thinking_budget(strategy)

            # Check cache first
            cache_key = self._generate_cache_key(request.prompt, strategy, budget)
            if self.config.cache_reasoning_results and cache_key in self.reasoning_cache:
                logger.info("📋 Using cached reasoning result")
                cached_result = self.reasoning_cache[cache_key]
                thinking_time = time.time() - start_time

                return GenerationResult(
                    response=cached_result["response"],
                    used_reasoning=True,
                    thinking_time=thinking_time,
                    confidence_score=cached_result["confidence"],
                    reasoning_metadata=cached_result["metadata"],
                    reasoning_trace=cached_result.get("trace")
                )

            # Execute deep thinking workflow
            logger.info(f"🧠 Executing deep thinking with strategy: {strategy}")

            iterative_result = await self.workflow_engine.execute_deep_thinking(
                workflow_id=f"reasoning_gen_{int(time.time())}",
                problem_statement=request.prompt,
                input_data={"request": request.to_dict()},
                thinking_budget=budget,
                domain=self.strategy_configs[strategy]["domain"]
            )

            thinking_time = time.time() - start_time

            # Convert iterative result to standard response format
            response = self._convert_iterative_result_to_response(iterative_result, request)

            # Create enhanced result
            result = GenerationResult(
                response=response,
                used_reasoning=True,
                thinking_time=thinking_time,
                confidence_score=iterative_result.final_confidence,
                reasoning_metadata={
                    "strategy": strategy,
                    "iterations": iterative_result.total_iterations,
                    "budget_used": iterative_result.total_time / budget.max_time_seconds,
                    "complexity_analysis": analysis_metadata,
                    "success": iterative_result.success,
                    "corrections_applied": len(iterative_result.corrections_applied)
                },
                reasoning_trace=iterative_result.reasoning_trace
            )

            # Cache result if successful
            if self.config.cache_reasoning_results and iterative_result.success:
                self.reasoning_cache[cache_key] = {
                    "response": response,
                    "confidence": iterative_result.final_confidence,
                    "metadata": result.reasoning_metadata,
                    "trace": iterative_result.reasoning_trace,
                    "timestamp": time.time()
                }

                # Maintain cache size limit
                if len(self.reasoning_cache) > self.config.max_cached_results:
                    oldest_key = min(self.reasoning_cache.keys(),
                                   key=lambda k: self.reasoning_cache[k]["timestamp"])
                    del self.reasoning_cache[oldest_key]

            # Update performance stats
            self._update_performance_stats(thinking_time, iterative_result.success)

            logger.info(f"🧠 Deep thinking completed: {iterative_result.total_iterations} iterations, "
                       f"{thinking_time:.2f}s, confidence: {iterative_result.final_confidence:.2f}")

            return result

        except Exception as e:
            logger.error(f"❌ Error in reasoning generation: {e}")
            thinking_time = time.time() - start_time

            # Fallback to standard generation
            try:
                response = await self.inference_api.generate(request)
                return GenerationResult(
                    response=response,
                    used_reasoning=False,
                    thinking_time=thinking_time,
                    confidence_score=0.5,
                    reasoning_metadata={
                        "error": str(e),
                        "fallback": "standard_generation",
                        "complexity_analysis": analysis_metadata if 'analysis_metadata' in locals() else {}
                    }
                )
            except Exception as fallback_error:
                logger.error(f"❌ Fallback generation also failed: {fallback_error}")
                raise

    def _select_reasoning_strategy(self, query: str, analysis_metadata: Dict[str, Any]) -> str:
        """Select the most appropriate reasoning strategy for the query."""
        query_lower = query.lower()

        # Strategy selection based on keywords and context
        strategy_indicators = {
            "analytical": ["analyze", "evaluate", "research", "evidence", "data", "study"],
            "creative": ["create", "design", "innovate", "strategy", "new", "idea"],
            "technical": ["implement", "code", "system", "optimize", "technical", "develop"],
        }

        best_strategy = self.config.default_strategy
        max_matches = 0

        for strategy, keywords in strategy_indicators.items():
            if strategy not in self.config.enabled_strategies:
                continue

            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches > max_matches:
                max_matches = matches
                best_strategy = strategy

        return best_strategy

    def _create_thinking_budget(self, strategy: str) -> ThinkingBudget:
        """Create thinking budget based on strategy configuration."""
        config = self.strategy_configs.get(strategy, self.strategy_configs["general"])

        return ThinkingBudget(
            max_time_seconds=self.config.default_max_time_seconds,
            max_iterations=config["max_iterations"],
            min_confidence_threshold=config["min_confidence_threshold"],
            time_per_iteration_seconds=config["time_per_iteration_seconds"]
        )

    def _generate_cache_key(self, prompt: str, strategy: str, budget: ThinkingBudget) -> str:
        """Generate cache key for reasoning results."""
        # Create a hash of key components
        key_components = f"{prompt[:100]}_{strategy}_{budget.max_iterations}_{budget.min_confidence_threshold}"
        return str(hash(key_components))

    def _convert_iterative_result_to_response(self, iterative_result: IterativeResult,
                                            original_request: InferenceRequest) -> InferenceResponse:
        """Convert iterative thinking result to standard InferenceResponse format."""
        # Calculate usage metrics
        prompt_tokens = len(self.inference_api.tokenizer.encode(original_request.prompt, add_special_tokens=True))
        completion_text = str(iterative_result.final_output) if iterative_result.final_output else ""
        completion_tokens = len(self.inference_api.tokenizer.encode(completion_text, add_special_tokens=False))

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "response_time_seconds": iterative_result.total_time,
            "reasoning_iterations": iterative_result.total_iterations
        }

        return InferenceResponse(
            text=completion_text,
            usage=usage,
            model_version="empoorio_lm_reasoning_v1.0",
            generated_at=time.time(),
            structured_output=False,
            guidance_used=False
        )

    def _update_performance_stats(self, thinking_time: float, success: bool):
        """Update performance statistics."""
        # Update average thinking time
        total_time = self.performance_stats["average_thinking_time"] * (self.performance_stats["reasoning_activations"] - 1)
        total_time += thinking_time
        self.performance_stats["average_thinking_time"] = total_time / self.performance_stats["reasoning_activations"]

        # Update success rate
        successes = self.performance_stats["success_rate"] * (self.performance_stats["reasoning_activations"] - 1)
        successes += 1 if success else 0
        self.performance_stats["success_rate"] = successes / self.performance_stats["reasoning_activations"]

    async def generate_stream_with_thinking(
        self,
        request: InferenceRequest,
        thinking_budget: Optional[ThinkingBudget] = None,
        reasoning_strategy: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response with reasoning when appropriate.

        Args:
            request: Inference request
            thinking_budget: Custom thinking budget
            reasoning_strategy: Reasoning strategy to use

        Yields:
            Streaming chunks with reasoning information
        """
        # For now, delegate to standard generation and simulate streaming
        # In production, this would integrate with the workflow engine's streaming

        result = await self.generate_with_thinking(request, thinking_budget, reasoning_strategy)

        # Simulate streaming by breaking the response into chunks
        response_text = result.response.text
        words = response_text.split()

        for i, word in enumerate(words):
            chunk = {
                "token": word + " ",
                "text_so_far": " ".join(words[:i+1]),
                "finished": i == len(words) - 1,
                "used_reasoning": result.used_reasoning,
                "confidence_score": result.confidence_score
            }

            if result.used_reasoning and i == len(words) - 1:
                chunk["reasoning_metadata"] = result.reasoning_metadata

            yield chunk
            await asyncio.sleep(0.01)  # Small delay to simulate real streaming

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            **self.performance_stats,
            "cache_size": len(self.reasoning_cache),
            "active_strategies": list(self.strategy_configs.keys()),
            "config": {
                "auto_activate_reasoning": self.config.auto_activate_reasoning,
                "complexity_threshold": self.config.complexity_threshold,
                "default_max_time": self.config.default_max_time_seconds
            }
        }

    def clear_reasoning_cache(self):
        """Clear the reasoning results cache."""
        self.reasoning_cache.clear()
        logger.info("🗑️ Reasoning cache cleared")

    def update_config(self, new_config: Dict[str, Any]):
        """Update reasoning configuration."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info(f"⚙️ Configuration updated: {new_config}")


# Convenience functions for backward compatibility
async def generate_text_with_reasoning(
    prompt: str,
    model_path: str = "./src/models/empoorio_lm/versions/empoorio_lm_v1.0.0-trained_267306",
    **kwargs
) -> GenerationResult:
    """
    Convenience function for generating text with reasoning capabilities.

    Args:
        prompt: Input prompt
        model_path: Path to the model
        **kwargs: Additional generation parameters

    Returns:
        Generation result with reasoning information
    """
    generator = EmpoorioLMReasoningGenerator()
    await generator.initialize()

    request = InferenceRequest(prompt=prompt, **kwargs)
    return await generator.generate_with_thinking(request)


# Configuration helpers
def create_reasoning_config(
    complexity_threshold: float = 0.7,
    max_time_seconds: int = 300,
    auto_activate: bool = True
) -> ReasoningConfig:
    """Create a reasoning configuration with common settings."""
    return ReasoningConfig(
        complexity_threshold=complexity_threshold,
        default_max_time_seconds=max_time_seconds,
        auto_activate_reasoning=auto_activate
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        print("🧠 Testing EmpoorioLM Reasoning Generator...")

        generator = EmpoorioLMReasoningGenerator()
        success = await generator.initialize()

        if success:
            # Test simple query
            simple_prompt = "Hello, how are you?"
            needs_thinking, score, metadata = generator.needs_deep_thinking(simple_prompt)
            print(f"Simple query - Needs thinking: {needs_thinking}, Score: {score:.2f}")

            # Test complex query
            complex_prompt = "Analyze the impact of artificial intelligence on job markets and propose strategies for workforce transition."
            needs_thinking, score, metadata = generator.needs_deep_thinking(complex_prompt)
            print(f"Complex query - Needs thinking: {needs_thinking}, Score: {score:.2f}")

            # Generate with reasoning
            request = InferenceRequest(prompt=complex_prompt, max_tokens=300)
            result = await generator.generate_with_thinking(request)

            print(f"Generation completed - Used reasoning: {result.used_reasoning}")
            print(f"Thinking time: {result.thinking_time:.2f}s")
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"Response: {result.response.text[:200]}...")

            print("✅ Reasoning Generator test completed")
        else:
            print("❌ Failed to initialize Reasoning Generator")

    asyncio.run(main())