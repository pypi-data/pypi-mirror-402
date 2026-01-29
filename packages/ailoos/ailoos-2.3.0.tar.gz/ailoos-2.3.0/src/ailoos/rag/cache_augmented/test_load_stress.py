"""
Load and Stress Tests for Cache Augmented RAG (CAG) System

This module provides comprehensive load and stress testing for the CAG system,
focusing on high concurrency, memory limits, eviction policies under pressure,
and system stability validation under extreme load conditions.

Tests include:
- High concurrency scenarios with multiple simultaneous requests
- Memory limit testing with constrained cache sizes
- Eviction policy validation (LRU/LFU) under pressure
- System stability testing with sustained extreme load
- Resource monitoring and performance metrics
"""

import time
import json
import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
import statistics
import random
import os
import psutil
import gc
from contextlib import contextmanager

import unittest
from unittest.mock import Mock, patch

# Import CAG components
from .cache_augmented_rag import CacheAugmentedRAG
from ..techniques.naive_rag import NaiveRAG

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage during tests."""

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def get_memory_delta(self) -> float:
        """Get memory usage delta from baseline in MB."""
        return self.get_memory_usage() - self.baseline_memory

    def reset_baseline(self):
        """Reset memory baseline."""
        self.baseline_memory = self.get_memory_usage()


class LoadStressTestBase(unittest.TestCase):
    """Base class for load and stress tests."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock base RAG
        self.mock_base_rag_class = Mock()
        self.mock_base_rag_instance = Mock()

        # Configure mock responses - make retrieve return different content for different queries
        def mock_retrieve(query, **kwargs):
            return [
                {'content': f'document content for {query}', 'score': 0.9, 'metadata': {'title': f'Doc for {query[:20]}'}}
            ]

        self.mock_base_rag_instance.retrieve.side_effect = mock_retrieve
        self.mock_base_rag_instance.generate.return_value = 'Generated response for the query'
        self.mock_base_rag_instance.evaluate.return_value = {'accuracy': 0.85, 'relevance': 0.8}

        self.mock_base_rag_class.return_value = self.mock_base_rag_instance

        # Test queries for load testing
        self.test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks",
            "What are the benefits of RAG systems?",
            "How to implement caching in RAG?",
            "What is retrieval-augmented generation?",
            "Explain deep learning concepts",
            "What are transformers in AI?",
            "How to optimize RAG performance?",
            "What is semantic caching?",
            "Explain vector embeddings",
            "What are large language models?",
            "How does RAG improve LLM responses?",
            "What is context retrieval?",
            "How to evaluate RAG systems?",
            "What are the limitations of RAG?",
            "How does caching improve performance?",
            "What is similarity search?",
            "How to implement LRU cache?",
            "What is LFU cache eviction?"
        ] * 5  # Repeat for more test data

        self.memory_monitor = MemoryMonitor()

    def create_cag_instance(self, cache_config: Optional[Dict] = None) -> CacheAugmentedRAG:
        """Create a CAG instance with specified cache configuration."""
        default_cache_config = {
            'model_name': 'all-MiniLM-L6-v2',
            'similarity_threshold': 0.95,  # Higher threshold to reduce false positives
            'max_size': 100,
            'eviction_policy': 'LRU'
        }

        if cache_config:
            default_cache_config.update(cache_config)

        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_config': default_cache_config,
            'cache_enabled': True
        }

        return CacheAugmentedRAG(config)

    def run_concurrent_queries(self, rag_instance: CacheAugmentedRAG, queries: List[str],
                              num_workers: int = 10, timeout: int = 60) -> Dict[str, Any]:
        """Run queries concurrently and collect metrics."""

        def worker_task(query: str) -> Tuple[str, float, float]:
            start_time = time.time()
            start_memory = self.memory_monitor.get_memory_usage()

            try:
                result = rag_instance.run(query, top_k=3)
                response = result.get('response', '')
            except Exception as e:
                response = f"Error: {str(e)}"

            end_time = time.time()
            end_memory = self.memory_monitor.get_memory_usage()

            latency = end_time - start_time
            memory_delta = end_memory - start_memory

            return response, latency, memory_delta

        results = []
        errors = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_query = {executor.submit(worker_task, query): query for query in queries}

            for future in as_completed(future_to_query, timeout=timeout):
                query = future_to_query[future]
                try:
                    response, latency, memory_delta = future.result()
                    results.append({
                        'query': query,
                        'response': response,
                        'latency': latency,
                        'memory_delta': memory_delta
                    })
                except Exception as e:
                    errors.append({
                        'query': query,
                        'error': str(e)
                    })

        # Calculate aggregate metrics
        if results:
            latencies = [r['latency'] for r in results]
            memory_deltas = [r['memory_delta'] for r in results]

            metrics = {
                'total_queries': len(results),
                'successful_queries': len(results),
                'failed_queries': len(errors),
                'avg_latency': statistics.mean(latencies),
                'median_latency': statistics.median(latencies),
                'min_latency': min(latencies),
                'max_latency': max(latencies),
                'p95_latency': statistics.quantiles(latencies, n=20)[18],  # 95th percentile
                'p99_latency': statistics.quantiles(latencies, n=100)[98],  # 99th percentile
                'avg_memory_delta': statistics.mean(memory_deltas),
                'throughput': len(results) / sum(latencies) if latencies else 0,
                'errors': errors
            }
        else:
            metrics = {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': len(errors),
                'errors': errors
            }

        return metrics


class TestHighConcurrencyLoad(LoadStressTestBase):
    """Test high concurrency scenarios."""

    def test_concurrent_load_10_workers(self):
        """Test with 10 concurrent workers."""
        rag = self.create_cag_instance()
        queries = self.test_queries[:50]  # 50 queries

        start_time = time.time()
        metrics = self.run_concurrent_queries(rag, queries, num_workers=10)
        total_time = time.time() - start_time

        # Assertions
        self.assertGreater(metrics['successful_queries'], 0)
        self.assertLess(metrics['avg_latency'], 5.0)  # Should complete within reasonable time
        self.assertLess(metrics['p95_latency'], 10.0)  # 95th percentile should be reasonable

        print(f"10 workers test - Total time: {total_time:.2f}s, Throughput: {metrics['throughput']:.2f} qps")

    def test_concurrent_load_50_workers(self):
        """Test with 50 concurrent workers (high concurrency)."""
        rag = self.create_cag_instance()
        queries = self.test_queries[:100]  # 100 queries

        start_time = time.time()
        metrics = self.run_concurrent_queries(rag, queries, num_workers=50, timeout=120)
        total_time = time.time() - start_time

        # Assertions
        self.assertGreater(metrics['successful_queries'], 0)
        self.assertLess(metrics['failed_queries'], len(queries) * 0.1)  # Less than 10% failure rate

        print(f"50 workers test - Total time: {total_time:.2f}s, Throughput: {metrics['throughput']:.2f} qps")

    def test_concurrent_load_100_workers(self):
        """Test with 100 concurrent workers (extreme concurrency)."""
        rag = self.create_cag_instance()
        queries = self.test_queries[:200]  # 200 queries

        start_time = time.time()
        metrics = self.run_concurrent_queries(rag, queries, num_workers=100, timeout=180)
        total_time = time.time() - start_time

        # Assertions - extreme load may have some failures but should handle most
        self.assertGreater(metrics['successful_queries'], len(queries) * 0.5)  # At least 50% success

        print(f"100 workers test - Total time: {total_time:.2f}s, Throughput: {metrics['throughput']:.2f} qps")


class TestMemoryLimitsAndEviction(LoadStressTestBase):
    """Test memory limits and eviction policies."""

    def test_small_cache_under_pressure(self):
        """Test small cache (size 5) under pressure."""
        rag = self.create_cag_instance({'max_size': 5})

        # Add more queries than cache size - use very different queries
        queries = [
            "What is the capital of France?",
            "How to bake a chocolate cake?",
            "Explain quantum physics",
            "What are the symptoms of diabetes?",
            "How to change a car tire?",
            "What is photosynthesis?",
            "How to play guitar?",
            "What are black holes?",
            "How to make coffee?",
            "What is machine learning?",
            "How to swim freestyle?",
            "What are volcanoes?",
            "How to write a novel?",
            "What is the periodic table?",
            "How to meditate?",
            "What are dinosaurs?",
            "How to code in Python?",
            "What is climate change?",
            "How to garden vegetables?",
            "What are constellations?"
        ]

        for i, query in enumerate(queries):
            context = [{'content': f'Context for {query}'}]
            rag.generate(query, context)
            if i % 5 == 0:  # Print every 5 iterations
                print(f"After {i+1} queries - Cache size: {len(rag.cache_manager)}, Evictions: {rag.cache_manager.metrics['evictions']}")

        # Cache should not exceed max size
        self.assertLessEqual(len(rag.cache_manager), 5)

        # Should have evictions
        self.assertGreater(rag.cache_manager.metrics['evictions'], 0)

        print(f"Small cache test - Final cache size: {len(rag.cache_manager)}, Evictions: {rag.cache_manager.metrics['evictions']}")

    def test_lru_eviction_under_load(self):
        """Test LRU eviction policy under concurrent load."""
        rag = self.create_cag_instance({
            'max_size': 10,
            'eviction_policy': 'LRU'
        })

        # Fill cache
        for i in range(10):
            query = f"Initial query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        self.assertEqual(len(rag.cache_manager), 10)

        # Access first 5 queries to make them recently used
        for i in range(5):
            query = f"Initial query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Add 5 more queries - should evict least recently used (queries 5-9)
        for i in range(10, 15):
            query = f"New query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Cache should still be at max size
        self.assertEqual(len(rag.cache_manager), 10)

        # Check that recently used queries (0-4) are still in cache
        cache_queries = [entry.query for entry in rag.cache_manager.cache.values()]
        for i in range(5):
            self.assertIn(f"Initial query {i}", cache_queries)

        print("LRU eviction test passed")

    def test_lfu_eviction_under_load(self):
        """Test LFU eviction policy under concurrent load."""
        rag = self.create_cag_instance({
            'max_size': 10,
            'eviction_policy': 'LFU'
        })

        # Fill cache
        for i in range(10):
            query = f"Query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Access first 3 queries many times (high frequency)
        for _ in range(10):
            for i in range(3):
                query = f"Query {i}"
                context = [{'content': f'Context {i}'}]
                rag.generate(query, context)

        # Add 5 more queries - should evict least frequently used
        for i in range(10, 15):
            query = f"New query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Cache should still be at max size
        self.assertEqual(len(rag.cache_manager), 10)

        # Check that frequently used queries (0-2) are still in cache
        cache_queries = [entry.query for entry in rag.cache_manager.cache.values()]
        for i in range(3):
            self.assertIn(f"Query {i}", cache_queries)

        print("LFU eviction test passed")

    def test_memory_usage_under_load(self):
        """Test memory usage patterns under load."""
        rag = self.create_cag_instance({'max_size': 50})

        initial_memory = self.memory_monitor.get_memory_usage()

        # Run many queries
        queries = self.test_queries[:200]
        metrics = self.run_concurrent_queries(rag, queries, num_workers=20)

        final_memory = self.memory_monitor.get_memory_usage()
        memory_delta = final_memory - initial_memory

        # Memory usage should be reasonable (less than 500MB increase)
        self.assertLess(memory_delta, 500.0)

        print(f"Memory test - Initial: {initial_memory:.2f}MB, Final: {final_memory:.2f}MB, Delta: {memory_delta:.2f}MB")


class TestExtremeLoadStability(LoadStressTestBase):
    """Test system stability under extreme load."""

    def test_sustained_high_load(self):
        """Test sustained high load for extended period."""
        rag = self.create_cag_instance({'max_size': 100})

        duration = 30  # 30 seconds
        num_workers = 20
        start_time = time.time()
        end_time = start_time + duration

        query_count = 0
        errors = 0

        def load_worker(worker_id: int):
            nonlocal query_count, errors
            local_count = 0
            local_errors = 0

            while time.time() < end_time:
                try:
                    query = random.choice(self.test_queries)
                    result = rag.run(query, top_k=3)
                    local_count += 1
                except Exception as e:
                    local_errors += 1
                    if local_errors < 5:  # Log first few errors
                        logger.warning(f"Worker {worker_id} error: {e}")

            with threading.Lock():
                query_count += local_count
                errors += local_errors

        # Start workers
        threads = []
        for i in range(num_workers):
            t = threading.Thread(target=load_worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        actual_duration = time.time() - start_time
        throughput = query_count / actual_duration

        # Assertions
        self.assertGreater(query_count, 100)  # Should handle reasonable load
        self.assertLess(errors, query_count * 0.05)  # Less than 5% error rate

        print(f"Sustained load test - Duration: {actual_duration:.2f}s, Queries: {query_count}, Throughput: {throughput:.2f} qps, Errors: {errors}")

    def test_memory_stress_with_gc_pressure(self):
        """Test memory stability with garbage collection pressure."""
        rag = self.create_cag_instance({'max_size': 200})

        # Force garbage collection before test
        gc.collect()
        initial_memory = self.memory_monitor.get_memory_usage()

        # Run intensive load test
        queries = self.test_queries * 10  # 1000 queries
        metrics = self.run_concurrent_queries(rag, queries, num_workers=50, timeout=300)

        # Force garbage collection after test
        gc.collect()
        final_memory = self.memory_monitor.get_memory_usage()

        memory_delta = final_memory - initial_memory

        # Memory should not grow excessively
        self.assertLess(memory_delta, 1000.0)  # Less than 1GB increase

        # Should have processed most queries successfully
        self.assertGreater(metrics['successful_queries'], len(queries) * 0.8)  # 80% success rate

        print(f"Memory stress test - Memory delta: {memory_delta:.2f}MB, Success rate: {metrics['successful_queries']/len(queries)*100:.1f}%")

    def test_cache_integrity_under_load(self):
        """Test cache integrity and consistency under load."""
        rag = self.create_cag_instance({'max_size': 50})

        # Pre-populate cache with known data
        known_queries = {}
        for i in range(20):
            query = f"Known query {i}"
            context = [{'content': f'Context {i}'}]
            response = rag.generate(query, context)
            known_queries[query] = response

        # Run concurrent load that includes known queries
        test_queries = list(known_queries.keys()) * 5 + self.test_queries[:100]
        random.shuffle(test_queries)

        metrics = self.run_concurrent_queries(rag, test_queries, num_workers=30)

        # Verify cache integrity - re-run known queries and check responses match
        for query, expected_response in known_queries.items():
            actual_response = rag.generate(query, [{'content': f'Context for {query}'}])
            self.assertEqual(actual_response, expected_response,
                           f"Cache inconsistency for query: {query}")

        print(f"Cache integrity test - Verified {len(known_queries)} cached responses under load")

    def test_error_handling_under_load(self):
        """Test error handling and recovery under load."""
        # Create RAG that will sometimes fail
        failing_rag_class = Mock()
        failing_instance = Mock()

        call_count = 0
        def failing_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 10 == 0:  # Fail every 10th call
                raise Exception("Simulated failure")
            return "Normal response"

        failing_instance.retrieve.return_value = [{'content': 'test', 'score': 0.9}]
        failing_instance.generate.side_effect = failing_generate
        failing_instance.evaluate.return_value = {'accuracy': 0.8}

        failing_rag_class.return_value = failing_instance

        config = {
            'base_rag_class': failing_rag_class,
            'base_rag_config': {},
            'cache_config': {'max_size': 50},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Run load test with failures
        queries = self.test_queries[:200]
        metrics = self.run_concurrent_queries(rag, queries, num_workers=20)

        # Should handle failures gracefully
        self.assertGreater(metrics['successful_queries'], 0)
        self.assertGreater(metrics['failed_queries'], 0)  # Should have some failures
        self.assertLess(metrics['failed_queries'], len(queries) * 0.2)  # But not too many

        print(f"Error handling test - Success: {metrics['successful_queries']}, Failures: {metrics['failed_queries']}")


class LoadStressTestRunner:
    """Runner for comprehensive load and stress testing."""

    def __init__(self):
        self.results = {}
        self.memory_monitor = MemoryMonitor()

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all load and stress tests."""

        logger.info("Starting comprehensive CAG load and stress testing")

        # Load test suites
        test_suites = [
            TestHighConcurrencyLoad,
            TestMemoryLimitsAndEviction,
            TestExtremeLoadStability
        ]

        overall_start_time = time.time()
        overall_start_memory = self.memory_monitor.get_memory_usage()

        for test_suite_class in test_suites:
            suite_name = test_suite_class.__name__
            logger.info(f"Running test suite: {suite_name}")

            suite = unittest.TestLoader().loadTestsFromTestCase(test_suite_class)
            runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))

            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()

            self.results[suite_name] = {
                'duration': end_time - start_time,
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
            }

        overall_end_time = time.time()
        overall_end_memory = self.memory_monitor.get_memory_usage()

        self.results['summary'] = {
            'total_duration': overall_end_time - overall_start_time,
            'total_memory_delta': overall_end_memory - overall_start_memory,
            'timestamp': time.time()
        }

        logger.info("Load and stress testing completed")
        return self.results

    def save_results(self, filename: str = 'cag_load_stress_results.json'):
        """Save test results to file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "="*80)
        print("CAG LOAD AND STRESS TEST RESULTS")
        print("="*80)

        summary = self.results.get('summary', {})
        print(f"Total Duration: {summary.get('total_duration', 0):.2f} seconds")
        print(f"Memory Delta: {summary.get('total_memory_delta', 0):.2f} MB")

        print("\nTEST SUITE RESULTS:")
        print("-" * 60)

        for suite_name, suite_results in self.results.items():
            if suite_name != 'summary':
                print(f"{suite_name}:")
                print(f"  Duration: {suite_results['duration']:.2f}s")
                print(f"  Tests Run: {suite_results['tests_run']}")
                print(f"  Success Rate: {suite_results['success_rate']*100:.1f}%")
                if suite_results['failures'] > 0 or suite_results['errors'] > 0:
                    print(f"  Failures: {suite_results['failures']}, Errors: {suite_results['errors']}")
                print()

        print("Detailed results saved to cag_load_stress_results.json")


def main():
    """Main entry point for load and stress testing."""
    logging.basicConfig(level=logging.INFO)

    runner = LoadStressTestRunner()
    results = runner.run_all_tests()
    runner.save_results()
    runner.print_summary()

    return results


if __name__ == '__main__':
    main()