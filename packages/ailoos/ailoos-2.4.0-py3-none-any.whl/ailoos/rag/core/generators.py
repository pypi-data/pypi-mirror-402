"""
Concrete Generator Implementations

This module contains concrete implementations of the Generator component
for different language models and generation strategies.
"""

from typing import List, Dict, Any, Optional, Union, Iterator
import logging
import asyncio
import time
import hashlib
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
from dataclasses import dataclass, field

from .generator import Generator

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Rate limiter for API calls."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10

    _minute_calls: deque = field(default_factory=lambda: deque(maxlen=60))
    _hour_calls: deque = field(default_factory=lambda: deque(maxlen=100))
    _burst_calls: int = 0
    _last_burst_reset: float = field(default_factory=time.time)

    def can_make_request(self) -> bool:
        """Check if a request can be made."""
        now = time.time()

        # Reset burst counter if needed
        if now - self._last_burst_reset >= 1.0:  # 1 second window
            self._burst_calls = 0
            self._last_burst_reset = now

        # Check burst limit
        if self._burst_calls >= self.burst_limit:
            return False

        # Clean old calls
        self._clean_old_calls()

        # Check rate limits
        if len(self._minute_calls) >= self.requests_per_minute:
            return False
        if len(self._hour_calls) >= self.requests_per_hour:
            return False

        return True

    def record_request(self):
        """Record a made request."""
        now = time.time()
        self._minute_calls.append(now)
        self._hour_calls.append(now)
        self._burst_calls += 1

    def _clean_old_calls(self):
        """Clean calls older than time windows."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        while self._minute_calls and self._minute_calls[0] < minute_ago:
            self._minute_calls.popleft()
        while self._hour_calls and self._hour_calls[0] < hour_ago:
            self._hour_calls.popleft()

    def get_remaining_requests(self) -> Dict[str, int]:
        """Get remaining requests for each time window."""
        self._clean_old_calls()
        return {
            'minute': max(0, self.requests_per_minute - len(self._minute_calls)),
            'hour': max(0, self.requests_per_hour - len(self._hour_calls)),
            'burst': max(0, self.burst_limit - self._burst_calls)
        }


@dataclass
class ResponseCache:
    """Intelligent response caching system."""
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour
    similarity_threshold: float = 0.85

    _cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _access_times: Dict[str, float] = field(default_factory=dict)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                self._access_times[key] = time.time()
                return entry['data']
            else:
                del self._cache[key]
                del self._access_times[key]
        return None

    def put(self, key: str, data: Dict[str, Any]):
        """Store response in cache."""
        # Evict old entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        self._access_times[key] = time.time()

    def generate_key(self, query: str, context: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Generate cache key from query, context, and config."""
        # Create a simplified representation for caching
        context_hash = hashlib.md5(
            json.dumps([doc.get('content', '')[:200] for doc in context], sort_keys=True).encode()
        ).hexdigest()[:8]

        config_hash = hashlib.md5(
            json.dumps({k: v for k, v in config.items() if k in ['temperature', 'max_tokens', 'top_p']}, sort_keys=True).encode()
        ).hexdigest()[:8]

        return f"{hashlib.md5(query.encode()).hexdigest()[:16]}_{context_hash}_{config_hash}"

    def find_similar(self, query: str, context: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find similar cached responses using fuzzy matching."""
        # Simple implementation - in production, use embeddings for better similarity
        query_words = set(query.lower().split())
        for key, entry in self._cache.items():
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                cached_query = entry['data'].get('query', '')
                cached_words = set(cached_query.lower().split())
                similarity = len(query_words & cached_words) / len(query_words | cached_words)
                if similarity >= self.similarity_threshold:
                    return entry['data']
        return None

    def _evict_oldest(self):
        """Evict least recently used entries."""
        if not self._access_times:
            return

        oldest_key = min(self._access_times, key=self._access_times.get)
        del self._cache[oldest_key]
        del self._access_times[oldest_key]


@dataclass
class QualityMetrics:
    """Quality metrics collector for generated responses."""
    response_length: int = 0
    context_relevance: float = 0.0
    factual_accuracy: float = 0.0
    coherence: float = 0.0
    helpfulness: float = 0.0
    generation_time: float = 0.0
    cache_hit: bool = False
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'response_length': self.response_length,
            'context_relevance': self.context_relevance,
            'factual_accuracy': self.factual_accuracy,
            'coherence': self.coherence,
            'helpfulness': self.helpfulness,
            'generation_time': self.generation_time,
            'cache_hit': self.cache_hit,
            'fallback_used': self.fallback_used
        }


@dataclass
class ConversationContext:
    """Context manager for multi-turn conversations."""
    max_turns: int = 10
    context_window: int = 5

    _conversation_history: List[Dict[str, str]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_turn(self, user_query: str, assistant_response: str):
        """Add a conversation turn."""
        with self._lock:
            self._conversation_history.append({
                'user': user_query,
                'assistant': assistant_response,
                'timestamp': datetime.now().isoformat()
            })

            # Keep only recent turns
            if len(self._conversation_history) > self.max_turns:
                self._conversation_history = self._conversation_history[-self.max_turns:]

    def get_recent_context(self, current_query: str) -> str:
        """Get recent conversation context for the current query."""
        with self._lock:
            if not self._conversation_history:
                return ""

            # Get last N turns
            recent_turns = self._conversation_history[-self.context_window:]
            context_parts = []

            for turn in recent_turns:
                context_parts.append(f"Usuario: {turn['user']}")
                context_parts.append(f"Asistente: {turn['assistant']}")

            return "\n".join(context_parts)

    def clear(self):
        """Clear conversation history."""
        with self._lock:
            self._conversation_history.clear()


class EmpoorioLMGenerator(Generator):
    """
    Advanced EmpoorioLM Generator with comprehensive RAG integration.

    This generator provides complete integration with EmpoorioLM API including:
    - Rate limiting and request management
    - Intelligent response caching
    - Multi-turn conversation context
    - Fallback systems for reliability
    - Quality metrics and monitoring
    - A/B testing capabilities
    - Streaming support
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize advanced EmpoorioLM generator.

        Args:
            config (Dict[str, Any]): Configuration containing:
                - empoorio_api_config: Configuration for EmpoorioLM API
                - generation_config: Generation parameters
                - prompt_config: Prompt templates
                - rate_limiting: Rate limiting settings
                - caching: Cache configuration
                - conversation: Multi-turn conversation settings
                - fallback: Fallback system configuration
                - ab_testing: A/B testing parameters
        """
        super().__init__(config)

        # Import here to avoid circular dependencies
        try:
            from ...api.empoorio_api import EmpoorioLMApi, EmpoorioLMApiConfig
            from ...api.empoorio_api import GenerationConfig as EmpoorioGenerationConfig
        except ImportError:
            # Fallback for standalone usage
            from ...inference.api import EmpoorioLMInferenceAPI, InferenceConfig
            EmpoorioLMApi = EmpoorioLMInferenceAPI
            EmpoorioLMApiConfig = InferenceConfig
            EmpoorioGenerationConfig = None

        # Initialize EmpoorioLM API
        api_config = config.get('empoorio_api_config', {})
        self.api_config = EmpoorioLMApiConfig(**api_config)
        self.empoorio_api = EmpoorioLMApi(self.api_config)

        # Set up generation config class
        self.GenerationConfig = EmpoorioGenerationConfig or type('GenerationConfig', (), {
            'max_new_tokens': 512,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'do_sample': True,
            'repetition_penalty': 1.1
        })

        # Initialize advanced features
        self._setup_advanced_features(config)

        logger.info("Advanced EmpoorioLMGenerator initialized with all features")

    def _setup_advanced_features(self, config: Dict[str, Any]):
        """Setup advanced features like caching, rate limiting, etc."""
        # Rate limiting
        rate_config = config.get('rate_limiting', {})
        self.rate_limiter = RateLimiter(
            requests_per_minute=rate_config.get('requests_per_minute', 60),
            requests_per_hour=rate_config.get('requests_per_hour', 1000),
            burst_limit=rate_config.get('burst_limit', 10)
        )

        # Response caching
        cache_config = config.get('caching', {})
        self.cache = ResponseCache(
            max_size=cache_config.get('max_size', 1000),
            ttl_seconds=cache_config.get('ttl_seconds', 3600),
            similarity_threshold=cache_config.get('similarity_threshold', 0.85)
        )

        # Conversation context
        conv_config = config.get('conversation', {})
        self.conversation = ConversationContext(
            max_turns=conv_config.get('max_turns', 10),
            context_window=conv_config.get('context_window', 5)
        )

        # Fallback system
        self.fallback_enabled = config.get('fallback', {}).get('enabled', True)
        self.fallback_generators = config.get('fallback', {}).get('generators', [])

        # A/B testing
        ab_config = config.get('ab_testing', {})
        self.ab_testing_enabled = ab_config.get('enabled', False)
        self.ab_variants = ab_config.get('variants', {})
        self.ab_current_variant = ab_config.get('default_variant', 'default')

        # Quality metrics
        self.metrics_enabled = config.get('metrics', {}).get('enabled', True)
        self.metrics_history = []

        # Model selection
        self.available_models = config.get('models', ['empoorio-lm-v1', 'empoorio-lm-v2'])
        self.current_model = config.get('current_model', 'empoorio-lm-v1')

    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate response with advanced features.

        Args:
            query (str): Input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Returns:
            str: Generated response
        """
        start_time = time.time()
        metrics = QualityMetrics()

        try:
            # Check rate limits
            if not self.rate_limiter.can_make_request():
                if self.fallback_enabled:
                    return self._generate_fallback(query, context, **kwargs)
                raise RuntimeError("Rate limit exceeded")

            # Try cache first
            cache_key = self.cache.generate_key(query, context, self.get_generation_config(**kwargs))
            cached_result = self.cache.get(cache_key)
            if cached_result:
                metrics.cache_hit = True
                logger.debug("Cache hit for query")
                return cached_result['response']

            # Add conversation context if available
            conversation_context = self.conversation.get_recent_context(query)
            if conversation_context:
                context.append({
                    'content': f"Contexto de conversación anterior:\n{conversation_context}",
                    'source': 'conversation_history',
                    'score': 1.0
                })

            # Apply A/B testing variant
            if self.ab_testing_enabled:
                variant_config = self._get_ab_variant_config()
                kwargs.update(variant_config)

            # Format prompt with context
            prompt = self.format_prompt(query, context)

            # Get generation config
            gen_config = self.get_generation_config(**kwargs)
            generation_config = self.GenerationConfig(**gen_config)

            # Record API call
            self.rate_limiter.record_request()

            # Generate response
            result = self.empoorio_api.generate_text(
                prompt=prompt,
                generation_config=generation_config
            )

            response = result.get('generated_text', '')

            # Post-process response
            response = self.post_process_response(response)

            # Update conversation context
            self.conversation.add_turn(query, response)

            # Cache the result
            cache_data = {
                'response': response,
                'query': query,
                'config': gen_config,
                'timestamp': time.time()
            }
            self.cache.put(cache_key, cache_data)

            # Collect metrics
            metrics.response_length = len(response)
            metrics.generation_time = time.time() - start_time
            self._collect_metrics(metrics, query, response, context)

            logger.debug(f"Generated response with EmpoorioLM: {len(response)} chars")
            return response

        except Exception as e:
            logger.error(f"Error generating with EmpoorioLM: {str(e)}")
            metrics.fallback_used = True

            if self.fallback_enabled:
                return self._generate_fallback(query, context, **kwargs)
            raise

    def generate_stream(self, query: str, context: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """
        Generate response with streaming using EmpoorioLM.

        Args:
            query (str): Input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Yields:
            str: Chunks of generated text
        """
        try:
            # Format prompt with context
            prompt = self.format_prompt(query, context)

            # Get generation config
            gen_config = self.get_generation_config(**kwargs)
            # Map max_tokens to max_new_tokens for compatibility
            if 'max_tokens' in gen_config:
                gen_config['max_new_tokens'] = gen_config.pop('max_tokens')
            generation_config = self.GenerationConfig(**gen_config)

            # For now, generate complete response and simulate streaming
            # TODO: Implement true streaming when EmpoorioLM API supports it
            result = self.empoorio_api.generate_text(
                prompt=prompt,
                generation_config=generation_config
            )

            response = result.get('generated_text', '')
            response = self.post_process_response(response)

            # Simulate streaming by yielding chunks
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                yield response[i:i + chunk_size]

        except Exception as e:
            logger.error(f"Error streaming with EmpoorioLM: {str(e)}")
            raise

    def format_prompt(self, query: str, context: List[Dict[str, Any]],
                      template: Optional[str] = None) -> str:
        """
        Format query and context into optimized RAG prompt for EmpoorioLM.

        Args:
            query (str): Input query
            context (List[Dict[str, Any]]): Retrieved context
            template (Optional[str]): Custom template

        Returns:
            str: Formatted prompt
        """
        if template is None:
            template = self.config.get('prompt_template',
                "Eres un asistente de IA especializado en proporcionar respuestas precisas y fundamentadas. "
                "Utiliza únicamente la información proporcionada en el contexto para responder la pregunta del usuario.\n\n"
                "CONTEXTO DISPONIBLE:\n{context}\n\n"
                "PREGUNTA DEL USUARIO: {query}\n\n"
                "INSTRUCCIONES:\n"
                "- Responde de manera directa y concisa\n"
                "- Si la información no está en el contexto, indica que no puedes responder basado en la información disponible\n"
                "- Mantén un tono profesional y helpful\n"
                "- Si hay múltiples perspectivas, preséntalas claramente\n\n"
                "RESPUESTA:"
            )

        # Format context with enhanced metadata
        context_parts = []
        for i, doc in enumerate(context):
            content = doc.get('content', doc.get('text', ''))
            score = doc.get('score', 0.0)
            source = doc.get('source', f'Documento {i+1}')
            doc_type = doc.get('type', 'texto')

            # Add relevance indicator
            relevance_indicator = "🔴" if score < 0.3 else "🟡" if score < 0.7 else "🟢"

            context_parts.append(
                f"{relevance_indicator} [{source}] Tipo: {doc_type} | Relevancia: {score:.3f}\n{content}"
            )

        context_text = "\n\n---\n\n".join(context_parts)

        return template.format(query=query, context=context_text)

    def post_process_response(self, response: str) -> str:
        """
        Advanced post-processing for EmpoorioLM responses.

        Args:
            response (str): Raw response

        Returns:
            str: Processed response
        """
        # Call parent post-processing
        response = super().post_process_response(response)

        # Additional EmpoorioLM-specific cleaning
        response = response.strip()

        # Remove common artifacts
        artifacts_to_remove = [
            "Respuesta:", "Answer:", "RESPUESTA:", "ANSWER:",
            "Según el contexto:", "Based on the context:",
            "Como asistente de IA:", "As an AI assistant:"
        ]

        for artifact in artifacts_to_remove:
            if response.startswith(artifact):
                response = response[len(artifact):].strip()

        # Clean up formatting
        response = re.sub(r'\n{3,}', '\n\n', response)  # Max 2 consecutive newlines
        response = re.sub(r' {2,}', ' ', response)  # Max 1 consecutive space

        # Ensure proper sentence endings
        if response and not response.endswith(('.', '!', '?', ':')):
            response += '.'

        return response

    def generate_stream(self, query: str, context: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """
        Generate response with streaming and advanced features.

        Args:
            query (str): Input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Yields:
            str: Chunks of generated text
        """
        try:
            # Check rate limits
            if not self.rate_limiter.can_make_request():
                if self.fallback_enabled:
                    yield from self._generate_fallback_stream(query, context, **kwargs)
                    return
                raise RuntimeError("Rate limit exceeded")

            # Try cache first
            cache_key = self.cache.generate_key(query, context, self.get_generation_config(**kwargs))
            cached_result = self.cache.get(cache_key)
            if cached_result:
                # Stream cached response
                response = cached_result['response']
                chunk_size = 50
                for i in range(0, len(response), chunk_size):
                    yield response[i:i + chunk_size]
                return

            # Add conversation context
            conversation_context = self.conversation.get_recent_context(query)
            if conversation_context:
                context.append({
                    'content': f"Contexto de conversación anterior:\n{conversation_context}",
                    'source': 'conversation_history',
                    'score': 1.0
                })

            # Apply A/B testing
            if self.ab_testing_enabled:
                variant_config = self._get_ab_variant_config()
                kwargs.update(variant_config)

            # Format prompt
            prompt = self.format_prompt(query, context)

            # Get generation config
            gen_config = self.get_generation_config(**kwargs)
            if 'max_tokens' in gen_config:
                gen_config['max_new_tokens'] = gen_config.pop('max_tokens')
            generation_config = self.GenerationConfig(**gen_config)

            # Record API call
            self.rate_limiter.record_request()

            # For now, generate complete response and simulate streaming
            # TODO: Implement true streaming when EmpoorioLM API supports it
            result = self.empoorio_api.generate_text(
                prompt=prompt,
                generation_config=generation_config
            )

            response = result.get('generated_text', '')
            response = self.post_process_response(response)

            # Update conversation and cache
            self.conversation.add_turn(query, response)
            cache_data = {
                'response': response,
                'query': query,
                'config': gen_config,
                'timestamp': time.time()
            }
            self.cache.put(cache_key, cache_data)

            # Stream response
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                yield response[i:i + chunk_size]

        except Exception as e:
            logger.error(f"Error streaming with EmpoorioLM: {str(e)}")
            if self.fallback_enabled:
                yield from self._generate_fallback_stream(query, context, **kwargs)
            else:
                raise

    def _generate_fallback(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """Generate using advanced fallback system."""
        logger.warning("Using advanced fallback generation system")

        try:
            from .fallback_system import FallbackSystem, FallbackType

            # Initialize fallback system with current config
            fallback_config = {
                'custom_strategies': self.fallback_generators
            }
            fallback_system = FallbackSystem(fallback_config)

            # Execute with fallback
            result = fallback_system.execute_with_fallback(
                FallbackType.GENERATOR,
                self._primary_generate,
                query, context, **kwargs
            )

            if result.success:
                return result.data
            else:
                logger.error(f"All fallback strategies failed: {result.error_message}")
                raise RuntimeError(result.error_message)

        except ImportError:
            # Fallback to simple system if advanced system not available
            return self._simple_fallback_generate(query, context, **kwargs)

    def _simple_fallback_generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """Simple fallback generation when advanced system is not available."""
        # Try fallback generators
        for fallback_config in self.fallback_generators:
            try:
                generator_class = fallback_config.get('class', MockGenerator)
                generator = generator_class(fallback_config.get('config', {}))
                return generator.generate(query, context, **kwargs)
            except Exception as e:
                logger.error(f"Fallback generator failed: {str(e)}")
                continue

        # Ultimate fallback: mock response
        mock_gen = MockGenerator({})
        return mock_gen.generate(query, context, **kwargs)

    def _primary_generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """Primary generation method for fallback system."""
        # This would be the original generate logic, but simplified for fallback
        return f"Respuesta básica para: {query}"

    def _generate_fallback_stream(self, query: str, context: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """Generate streaming using fallback system."""
        response = self._generate_fallback(query, context, **kwargs)
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]

    def _get_ab_variant_config(self) -> Dict[str, Any]:
        """Get A/B testing variant configuration."""
        try:
            from .ab_testing import get_ab_testing_manager

            # Get A/B testing manager
            ab_manager = get_ab_testing_manager(self.config.get('ab_testing_manager_config'))

            if ab_manager and self.ab_testing_enabled:
                # Use manager for variant selection and configuration
                user_id = self._get_user_id_for_ab_test()
                variant = ab_manager.get_variant('empoorio_lm_test', user_id, 'generator')
                return ab_manager.get_variant_config('empoorio_lm_test', variant)

        except ImportError:
            # Fallback to simple A/B testing
            pass

        # Simple fallback implementation
        if not self.ab_testing_enabled or self.ab_current_variant not in self.ab_variants:
            return {}

        return self.ab_variants[self.ab_current_variant]

    def _get_user_id_for_ab_test(self) -> str:
        """Generate a user ID for A/B testing."""
        # In a real implementation, this would come from session/user context
        # For now, use a simple hash of current time for consistent testing
        import time
        return str(int(time.time()) // 3600)  # Hourly buckets for testing

    def _collect_metrics(self, metrics: QualityMetrics, query: str, response: str, context: List[Dict[str, Any]]):
        """Collect quality metrics for the response."""
        if not self.metrics_enabled:
            return

        # Simple heuristics for quality metrics
        metrics.context_relevance = self._calculate_context_relevance(query, context)
        metrics.factual_accuracy = self._estimate_factual_accuracy(response, context)
        metrics.coherence = self._calculate_coherence(response)
        metrics.helpfulness = self._calculate_helpfulness(query, response)

        # Store metrics
        self.metrics_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics.to_dict(),
            'query_length': len(query),
            'context_count': len(context)
        })

        # Keep only recent metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

    def _calculate_context_relevance(self, query: str, context: List[Dict[str, Any]]) -> float:
        """Calculate how relevant the context is to the query."""
        query_words = set(query.lower().split())
        total_relevance = 0.0

        for doc in context:
            content = doc.get('content', '').lower()
            content_words = set(content.split())
            overlap = len(query_words & content_words)
            relevance = overlap / len(query_words) if query_words else 0.0
            total_relevance += relevance * doc.get('score', 1.0)

        return min(total_relevance / len(context) if context else 0.0, 1.0)

    def _estimate_factual_accuracy(self, response: str, context: List[Dict[str, Any]]) -> float:
        """Estimate factual accuracy based on context coverage."""
        response_words = set(response.lower().split())
        context_words = set()

        for doc in context:
            content = doc.get('content', '').lower()
            context_words.update(content.split())

        overlap = len(response_words & context_words)
        return min(overlap / len(response_words) if response_words else 0.0, 1.0)

    def _calculate_coherence(self, response: str) -> float:
        """Calculate response coherence based on sentence structure."""
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) < 2:
            return 0.5

        # Simple coherence based on sentence transitions
        coherence_score = 0.0
        for i in range(len(sentences) - 1):
            current_words = set(sentences[i].split())
            next_words = set(sentences[i + 1].split())
            transition_score = len(current_words & next_words) / len(current_words | next_words)
            coherence_score += transition_score

        return coherence_score / (len(sentences) - 1)

    def _calculate_helpfulness(self, query: str, response: str) -> float:
        """Calculate how helpful the response is."""
        # Simple heuristics
        score = 0.0

        # Length appropriateness
        if 50 <= len(response) <= 1000:
            score += 0.3

        # Contains question words if query has them
        question_words = ['qué', 'como', 'cuál', 'cuándo', 'dónde', 'por qué', 'what', 'how', 'which', 'when', 'where', 'why']
        query_has_questions = any(word in query.lower() for word in question_words)
        response_has_answers = any(word in response.lower() for word in ['es', 'son', 'está', 'is', 'are'])

        if query_has_questions and response_has_answers:
            score += 0.4

        # Completeness
        if response.endswith(('.', '!', '?', ':')):
            score += 0.3

        return min(score, 1.0)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self.metrics_history:
            return {}

        recent_metrics = self.metrics_history[-100:]  # Last 100 requests

        return {
            'total_requests': len(self.metrics_history),
            'avg_response_length': sum(m['metrics']['response_length'] for m in recent_metrics) / len(recent_metrics),
            'avg_generation_time': sum(m['metrics']['generation_time'] for m in recent_metrics) / len(recent_metrics),
            'cache_hit_rate': sum(1 for m in recent_metrics if m['metrics']['cache_hit']) / len(recent_metrics),
            'fallback_rate': sum(1 for m in recent_metrics if m['metrics']['fallback_used']) / len(recent_metrics),
            'avg_quality_score': sum(
                (m['metrics']['context_relevance'] + m['metrics']['factual_accuracy'] +
                 m['metrics']['coherence'] + m['metrics']['helpfulness']) / 4
                for m in recent_metrics
            ) / len(recent_metrics)
        }

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()

    def set_ab_variant(self, variant: str):
        """Set A/B testing variant."""
        if variant in self.ab_variants:
            self.ab_current_variant = variant
            logger.info(f"Switched to A/B variant: {variant}")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limiting status."""
        return {
            'can_make_request': self.rate_limiter.can_make_request(),
            'remaining_requests': self.rate_limiter.get_remaining_requests(),
            'current_model': self.current_model,
            'cache_size': len(self.cache._cache),
            'conversation_turns': len(self.conversation._conversation_history)
        }


class MockGenerator(Generator):
    """
    Mock generator for testing and development.

    This generator provides deterministic responses for testing purposes
    without requiring actual language model inference.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.response_templates = config.get('response_templates', [
            "Basándome en la información proporcionada, la respuesta es: {query}",
            "Según el contexto, puedo afirmar que: {query}",
            "La información relevante indica que: {query}"
        ])

    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """Generate mock response."""
        template = self.response_templates[len(query) % len(self.response_templates)]
        return template.format(query=query)

    def generate_stream(self, query: str, context: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """Generate mock streaming response."""
        response = self.generate(query, context, **kwargs)
        for chunk in response.split():
            yield chunk + " "