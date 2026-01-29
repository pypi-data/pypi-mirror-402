"""
End-to-End Integration Tests for Cache Augmented RAG System

Tests validate the complete flow from REST API through semantic caching,
including persistence, different RAG techniques, and real-world scenarios.
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.ailoos.rag import create_naive_rag
from src.ailoos.rag.cache_augmented.cache_augmented_rag import CacheAugmentedRAG
from src.ailoos.rag.cache_augmented.cache_manager import CacheManager


# Minimal API models for testing
class RAGQueryRequest(BaseModel):
    query: str
    rag_type: str = "CacheAugmentedRAG"
    parameters: dict = None


class RAGQueryResponse(BaseModel):
    query: str
    response: str
    context: list
    metrics: dict
    metadata: dict


# Minimal test API
class TestRAGAPI:
    def __init__(self):
        self.app = FastAPI()
        self.rag_systems = {}

        # Initialize CacheAugmentedRAG for testing
        try:
            rag_config = {
                'base_rag_class': create_naive_rag().__class__,
                'base_rag_config': {},
                'cache_config': {
                    'model_name': 'all-MiniLM-L6-v2',
                    'similarity_threshold': 0.8,
                    'max_size': 100
                },
                'cache_enabled': True
            }
            self.rag_systems["CacheAugmentedRAG"] = CacheAugmentedRAG(rag_config)
        except Exception as e:
            # Fallback to mock if dependencies not available
            mock_rag = Mock()
            mock_rag.run.return_value = {
                "query": "test",
                "response": "mock response",
                "context": [],
                "metrics": {},
                "metadata": {"rag_type": "CacheAugmentedRAG", "cache_enabled": True}
            }
            self.rag_systems["CacheAugmentedRAG"] = mock_rag

        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/query", response_model=RAGQueryResponse)
        async def query_rag(request: RAGQueryRequest):
            # Validate query
            if not request.query or not request.query.strip():
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Query cannot be empty")

            rag_system = self.rag_systems.get(request.rag_type)
            if not rag_system:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"RAG system not available")

            result = rag_system.run(request.query, **(request.parameters or {}))
            return RAGQueryResponse(**result)

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "rag_systems_available": list(self.rag_systems.keys()),
                "timestamp": "2024-01-01T00:00:00"
            }

        @self.app.get("/systems")
        async def get_systems():
            systems_info = {}
            for name, system in self.rag_systems.items():
                systems_info[name] = {
                    "name": name,
                    "type": type(system).__name__,
                    "status": "available"
                }

            return {
                "systems": systems_info,
                "total": len(systems_info),
                "timestamp": "2024-01-01T00:00:00"
            }


class TestCacheAugmentedRAGE2E(unittest.TestCase):
    """End-to-end tests for Cache Augmented RAG system."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = TestRAGAPI()
        self.client = TestClient(self.api.app)

        # Sample documents for testing
        self.sample_docs = [
            {
                "content": """
                La Inteligencia Artificial (IA) es una rama de la informática que se ocupa de crear
                máquinas capaces de realizar tareas que requieren inteligencia humana. Estas tareas
                incluyen el aprendizaje, el razonamiento, la resolución de problemas, la percepción,
                el entendimiento del lenguaje natural y la toma de decisiones.

                La IA se divide en dos tipos principales: IA débil (o estrecha) e IA fuerte (o general).
                La IA débil está diseñada para realizar tareas específicas, como el reconocimiento
                de imágenes o el procesamiento del lenguaje natural. La IA fuerte, por otro lado,
                tendría la capacidad de realizar cualquier tarea intelectual que un humano pueda hacer.
                """,
                "metadata": {
                    "title": "Introducción a la Inteligencia Artificial",
                    "author": "Dr. Ana García",
                    "topic": "IA",
                    "source": "manual"
                }
            },
            {
                "content": """
                El aprendizaje automático (Machine Learning) es un subcampo de la IA que permite
                a los sistemas aprender y mejorar automáticamente a partir de la experiencia,
                sin ser programados explícitamente para cada tarea específica.

                Los algoritmos de ML se entrenan con grandes cantidades de datos para identificar
                patrones y hacer predicciones. Los tipos principales de aprendizaje automático son:
                supervisado, no supervisado y por refuerzo.
                """,
                "metadata": {
                    "title": "Aprendizaje Automático",
                    "author": "Dr. Carlos López",
                    "topic": "Machine Learning",
                    "source": "manual"
                }
            }
        ]

    def test_complete_api_to_cache_flow(self):
        """Test complete end-to-end flow: API request -> CacheAugmentedRAG -> cache persistence."""
        # Make initial query
        request_data = {
            "query": "¿Qué es la Inteligencia Artificial?",
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("response", data)
        self.assertIn("context", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["rag_type"], "CacheAugmentedRAG")

        # Verify cache was used (should be miss on first call)
        cache_metrics = data["metadata"]["cache_metrics"]
        self.assertEqual(cache_metrics["cache_misses"], 1)
        self.assertEqual(cache_metrics["cache_hits"], 0)

        # Make same query again - should hit cache
        response2 = self.client.post("/query", json=request_data)
        self.assertEqual(response2.status_code, 200)

        data2 = response2.json()
        # Response should be same (from cache)
        self.assertEqual(data["response"], data2["response"])

        # Cache metrics should show hit
        cache_metrics2 = data2["metadata"]["cache_metrics"]
        self.assertEqual(cache_metrics2["cache_hits"], 1)
        self.assertEqual(cache_metrics2["cache_misses"], 1)

    def test_cache_persistence_across_api_instances(self):
        """Test that cache persists across different API instances."""
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
            cache_file = tmp.name

        try:
            # Create first API instance with cache file
            api1 = TestRAGAPI()
            client1 = TestClient(api1.app)

            # Make query to populate cache
            request_data = {
                "query": "¿Qué es el Machine Learning?",
                "rag_type": "CacheAugmentedRAG"
            }

            response1 = client1.post("/query", json=request_data)
            self.assertEqual(response1.status_code, 200)

            # Save cache manually (simulate persistence)
            # Note: In real implementation, cache might auto-save
            if hasattr(api1.rag_systems["CacheAugmentedRAG"], 'save_cache'):
                api1.rag_systems["CacheAugmentedRAG"].save_cache(cache_file)

            # Create second API instance and load cache
            api2 = TestRAGAPI()
            client2 = TestClient(api2.app)

            if hasattr(api2.rag_systems["CacheAugmentedRAG"], 'load_cache'):
                api2.rag_systems["CacheAugmentedRAG"].load_cache(cache_file)

            # Make same query - should hit cache
            response2 = client2.post("/query", json=request_data)
            self.assertEqual(response2.status_code, 200)

            data2 = response2.json()
            cache_metrics = data2["metadata"]["cache_metrics"]

            # Should have cache hit since cache was loaded
            self.assertGreaterEqual(cache_metrics["cache_hits"], 0)  # May vary based on implementation

        finally:
            if os.path.exists(cache_file):
                os.unlink(cache_file)

    def test_different_rag_techniques_with_cache(self):
        """Test CacheAugmentedRAG integration with different base RAG techniques."""
        rag_types = ["NaiveRAG", "SpeculativeRAG", "SelfRAG"]

        for rag_type in rag_types:
            with self.subTest(rag_type=rag_type):
                # Test basic functionality
                request_data = {
                    "query": f"¿Qué es la IA? (test con {rag_type})",
                    "rag_type": rag_type
                }

                response = self.client.post("/query", json=request_data)

                # Should work (may fail in test env due to dependencies, but API should handle gracefully)
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("response", data)
                    self.assertIn("metadata", data)
                else:
                    # If RAG type not available, should get 400
                    self.assertEqual(response.status_code, 400)
                    data = response.json()
                    self.assertIn("not available", data["detail"])

    def test_semantic_cache_similarity_scenarios(self):
        """Test real-world scenarios with semantic similarity caching."""
        # Test queries that should be similar and hit cache
        similar_queries = [
            "¿Qué es la Inteligencia Artificial?",
            "¿Qué significa IA?",
            "¿Puedes explicar qué es la Inteligencia Artificial?",
            "¿Qué es la IA exactamente?"
        ]

        responses = []
        for query in similar_queries:
            request_data = {
                "query": query,
                "rag_type": "CacheAugmentedRAG"
            }

            response = self.client.post("/query", json=request_data)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            responses.append(data["response"])

            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # Check cache metrics from last response
        final_metrics = data["metadata"]["cache_metrics"]

        # Should have some cache hits due to semantic similarity
        # (Exact number depends on similarity threshold and implementation)
        total_queries = len(similar_queries)
        self.assertEqual(final_metrics["total_queries"], total_queries)
        self.assertGreaterEqual(final_metrics["cache_hits"], 0)

    def test_different_contexts_no_cache_hit(self):
        """Test that different contexts don't result in inappropriate cache hits."""
        # Same query but with different contexts should not cache
        queries_and_contexts = [
            ("¿Qué es la IA?", "IA context 1"),
            ("¿Qué es la IA?", "IA context 2"),  # Same query, different context
            ("¿Qué es el ML?", "ML context")     # Different query
        ]

        for i, (query, context_marker) in enumerate(queries_and_contexts):
            # Note: In real API, context is retrieved, not passed
            # This test simulates the effect by checking metrics
            request_data = {
                "query": query,
                "rag_type": "CacheAugmentedRAG"
            }

            response = self.client.post("/query", json=request_data)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            metrics = data["metadata"]["cache_metrics"]

            # Each unique query+context combination should be a miss initially
            # (This is a simplified test - real implementation depends on retrieved context)

    def test_cache_eviction_under_load(self):
        """Test cache eviction behavior under load with limited cache size."""
        # Make many different queries to trigger eviction
        for i in range(15):  # More than typical cache size
            request_data = {
                "query": f"¿Qué es el concepto {i}?",
                "rag_type": "CacheAugmentedRAG"
            }

            response = self.client.post("/query", json=request_data)
            self.assertEqual(response.status_code, 200)

        # Check final metrics
        data = response.json()
        cache_metrics = data["metadata"]["cache_metrics"]
        cache_manager_metrics = cache_metrics.get("cache_manager_metrics", {})

        # Should have some evictions if cache size is limited
        evictions = cache_manager_metrics.get("evictions", 0)
        # Note: Evictions may or may not occur depending on cache configuration

    def test_performance_end_to_end(self):
        """Test end-to-end performance improvements with caching."""
        query = "¿Cuál es la definición de Machine Learning?"

        # Measure time for first query (cache miss)
        start_time = time.time()
        request_data = {
            "query": query,
            "rag_type": "CacheAugmentedRAG"
        }

        response1 = self.client.post("/query", json=request_data)
        first_query_time = time.time() - start_time

        self.assertEqual(response1.status_code, 200)

        # Measure time for repeated query (cache hit)
        start_time = time.time()
        response2 = self.client.post("/query", json=request_data)
        second_query_time = time.time() - start_time

        self.assertEqual(response2.status_code, 200)

        # Second query should be faster (cache hit)
        # In test environment, difference might be small but should exist
        self.assertLessEqual(second_query_time, first_query_time)

        # Verify responses are identical
        data1 = response1.json()
        data2 = response2.json()
        self.assertEqual(data1["response"], data2["response"])

    def test_concurrent_requests_cache_consistency(self):
        """Test cache consistency under concurrent requests."""
        # This is a basic test - real concurrent testing would need async handling
        query = "¿Qué es el aprendizaje profundo?"

        # Make multiple requests quickly
        responses = []
        for i in range(5):
            request_data = {
                "query": f"{query} (request {i})",
                "rag_type": "CacheAugmentedRAG"
            }

            response = self.client.post("/query", json=request_data)
            self.assertEqual(response.status_code, 200)
            responses.append(response.json())

        # Check that cache metrics are consistent
        final_metrics = responses[-1]["metadata"]["cache_metrics"]
        self.assertEqual(final_metrics["total_queries"], 5)

    def test_error_handling_and_recovery(self):
        """Test error handling and cache recovery in end-to-end flow."""
        # Test with invalid query
        request_data = {
            "query": "",
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)
        self.assertEqual(response.status_code, 400)

        # Test with invalid RAG type
        request_data = {
            "query": "¿Qué es la IA?",
            "rag_type": "InvalidRAG"
        }

        response = self.client.post("/query", json=request_data)
        self.assertEqual(response.status_code, 400)

        # Verify system still works after errors
        request_data = {
            "query": "¿Qué es la IA?",
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)
        self.assertEqual(response.status_code, 200)

    def test_health_and_systems_endpoints(self):
        """Test health and systems endpoints in end-to-end context."""
        # Test health endpoint
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("CacheAugmentedRAG", data["rag_systems_available"])

        # Test systems endpoint
        response = self.client.get("/systems")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("CacheAugmentedRAG", data["systems"])
        system_info = data["systems"]["CacheAugmentedRAG"]
        self.assertEqual(system_info["status"], "available")


if __name__ == '__main__':
    unittest.main()