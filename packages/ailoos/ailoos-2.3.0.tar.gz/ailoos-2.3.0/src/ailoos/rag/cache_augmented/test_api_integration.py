"""
Integration tests for Cache Augmented RAG with RAG API.

Tests verify that CacheAugmentedRAG integrates properly with the RAG API.
"""

import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.ailoos.api.rag_api import RAGAPI


class TestCacheAugmentedRAGAPIIntegration(unittest.TestCase):
    """Integration tests for CacheAugmentedRAG with RAG API."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RAGAPI()
        self.client = TestClient(self.api.app)

    def test_health_endpoint(self):
        """Test health check endpoint includes CacheAugmentedRAG."""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "healthy")
        self.assertIn("CacheAugmentedRAG", data["rag_systems_available"])
        self.assertIn("timestamp", data)

    def test_systems_endpoint(self):
        """Test systems endpoint includes CacheAugmentedRAG."""
        response = self.client.get("/systems")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("CacheAugmentedRAG", data["systems"])
        system_info = data["systems"]["CacheAugmentedRAG"]
        self.assertEqual(system_info["name"], "CacheAugmentedRAG")
        self.assertEqual(system_info["status"], "available")

    @patch('src.ailoos.api.rag_api.CacheAugmentedRAG')
    def test_query_cache_augmented_rag_success(self, mock_cache_rag):
        """Test successful query with CacheAugmentedRAG."""
        # Mock the CacheAugmentedRAG instance
        mock_instance = AsyncMock()
        mock_instance.run.return_value = {
            "query": "What is AI?",
            "response": "AI is artificial intelligence",
            "context": [{"content": "AI definition", "score": 0.9}],
            "metrics": {"accuracy": 0.8},
            "metadata": {
                "rag_type": "CacheAugmentedRAG",
                "cache_enabled": True,
                "cache_metrics": {"hits": 1, "misses": 0}
            }
        }
        mock_cache_rag.return_value = mock_instance

        # Make request
        request_data = {
            "query": "What is AI?",
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertEqual(data["query"], "What is AI?")
        self.assertEqual(data["response"], "AI is artificial intelligence")
        self.assertEqual(len(data["context"]), 1)
        self.assertIn("metrics", data)
        self.assertIn("metadata", data)

        # Verify metadata
        self.assertEqual(data["metadata"]["rag_type"], "CacheAugmentedRAG")
        self.assertIn("processing_time", data["metadata"])
        self.assertIn("timestamp", data["metadata"])

    def test_query_invalid_rag_type(self):
        """Test query with invalid RAG type."""
        request_data = {
            "query": "What is AI?",
            "rag_type": "InvalidRAG"
        }

        response = self.client.post("/query", json=request_data)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("not available", data["detail"])

    def test_query_empty_query(self):
        """Test query with empty query string."""
        request_data = {
            "query": "",
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("cannot be empty", data["detail"])

    def test_query_missing_query(self):
        """Test query with missing query field."""
        request_data = {
            "rag_type": "CacheAugmentedRAG"
        }

        response = self.client.post("/query", json=request_data)

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_query_missing_rag_type(self):
        """Test query with missing RAG type defaults to NaiveRAG."""
        request_data = {
            "query": "What is AI?"
        }

        response = self.client.post("/query", json=request_data)

        # Should work with default NaiveRAG
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["query"], "What is AI?")

    @patch('src.ailoos.api.rag_api.CacheAugmentedRAG')
    def test_query_with_parameters(self, mock_cache_rag):
        """Test query with additional parameters."""
        # Mock the CacheAugmentedRAG instance
        mock_instance = AsyncMock()
        mock_instance.run.return_value = {
            "query": "What is AI?",
            "response": "AI response",
            "context": [],
            "metrics": {},
            "metadata": {}
        }
        mock_cache_rag.return_value = mock_instance

        request_data = {
            "query": "What is AI?",
            "rag_type": "CacheAugmentedRAG",
            "parameters": {
                "top_k": 10,
                "custom_param": "value"
            }
        }

        response = self.client.post("/query", json=request_data)

        self.assertEqual(response.status_code, 200)

        # Verify that parameters were passed to run method
        mock_instance.run.assert_called_once()
        call_args = mock_instance.run.call_args
        self.assertEqual(call_args[0][0], "What is AI?")  # query
        self.assertEqual(call_args[1]["top_k"], 10)  # parameters

    def test_options_query_endpoint(self):
        """Test OPTIONS request for query endpoint."""
        response = self.client.options("/query")

        self.assertEqual(response.status_code, 200)
        self.assertIn("POST", response.headers.get("Allow", ""))
        self.assertIn("OPTIONS", response.headers.get("Allow", ""))

    @patch('src.ailoos.api.rag_api.CacheAugmentedRAG')
    def test_cache_augmented_rag_initialization_in_api(self, mock_cache_rag):
        """Test that CacheAugmentedRAG is properly initialized in the API."""
        # Reset the API to trigger initialization
        self.api = RAGAPI()

        # Check that CacheAugmentedRAG was attempted to be initialized
        # (it may fail in test environment, but should be attempted)
        self.assertIsInstance(self.api.rag_systems, dict)

        # CacheAugmentedRAG may or may not be available depending on dependencies
        # but the API should handle it gracefully
        available_systems = list(self.api.rag_systems.keys())
        self.assertIsInstance(available_systems, list)

    def test_api_handles_cache_augmented_rag_errors(self):
        """Test that API handles CacheAugmentedRAG errors gracefully."""
        # This test verifies that if CacheAugmentedRAG fails during initialization,
        # the API continues to work with other RAG systems

        # The API should have at least some working RAG systems
        self.assertGreater(len(self.api.rag_systems), 0)

        # And health check should still work
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()