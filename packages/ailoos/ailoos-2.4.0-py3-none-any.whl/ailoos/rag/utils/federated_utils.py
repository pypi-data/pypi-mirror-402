"""
Federated Learning Utilities

This module provides utilities for federated RAG operations,
enabling privacy-preserving collaborative learning across distributed nodes.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FederatedUtils:
    """
    Utilities for federated RAG operations.

    This class provides methods for coordinating RAG operations across
    multiple nodes while preserving data privacy.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize federated utilities.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - node_id: Unique identifier for this node
                - coordinator_address: Address of the coordinator node
                - privacy_config: Privacy preservation settings
                - aggregation_config: Model aggregation settings
        """
        self.config = config
        self.node_id = config.get('node_id', 'node_1')
        self.coordinator_address = config.get('coordinator_address')
        self.privacy_config = config.get('privacy_config', {})
        self.aggregation_config = config.get('aggregation_config', {})

    def aggregate_embeddings(self, local_embeddings: List[List[float]],
                           other_embeddings: List[List[List[float]]]) -> List[List[float]]:
        """
        Aggregate embeddings from multiple nodes using federated averaging.

        Args:
            local_embeddings (List[List[float]]): Local node embeddings
            other_embeddings (List[List[List[float]]]): Embeddings from other nodes

        Returns:
            List[List[float]]: Aggregated embeddings
        """
        if not other_embeddings:
            return local_embeddings

        # Simple federated averaging
        all_embeddings = [local_embeddings] + other_embeddings
        num_nodes = len(all_embeddings)

        # Transpose to aggregate by embedding dimension
        aggregated = []
        max_len = max(len(emb) for emb in all_embeddings)

        for i in range(max_len):
            embedding_sum = []
            for node_emb in all_embeddings:
                if i < len(node_emb):
                    if not embedding_sum:
                        embedding_sum = [0.0] * len(node_emb[i])
                    embedding_sum = [s + v for s, v in zip(embedding_sum, node_emb[i])]

            if embedding_sum:
                # Average across nodes
                averaged = [s / num_nodes for s in embedding_sum]
                aggregated.append(averaged)

        return aggregated

    def differentially_private_update(self, gradients: List[float],
                                    privacy_budget: float) -> List[float]:
        """
        Apply differential privacy to gradient updates.

        Args:
            gradients (List[float]): Raw gradients
            privacy_budget (float): Privacy budget (epsilon)

        Returns:
            List[float]: Privacy-preserving gradients
        """
        import random
        import math

        # Simple Laplace mechanism for differential privacy
        sensitivity = self.privacy_config.get('sensitivity', 1.0)
        scale = sensitivity / privacy_budget

        noisy_gradients = []
        for grad in gradients:
            noise = random.laplace(0, scale)
            noisy_gradients.append(grad + noise)

        return noisy_gradients

    def secure_aggregation(self, local_models: Dict[str, Any],
                          participant_keys: List[str]) -> Dict[str, Any]:
        """
        Perform secure aggregation of model updates.

        Args:
            local_models (Dict[str, Any]): Local model parameters
            participant_keys (List[str]): Keys of participating nodes

        Returns:
            Dict[str, Any]: Securely aggregated model
        """
        # Placeholder for secure aggregation
        # In practice, this would use cryptographic techniques

        aggregated_model = {}

        # Simple averaging for demonstration
        for key in local_models.keys():
            values = [local_models[key]]  # Only local for now
            aggregated_model[key] = sum(values) / len(values)

        return aggregated_model

    def federated_retrieval(self, query: str, node_results: List[List[Dict[str, Any]]],
                           aggregation_method: str = 'rank_fusion') -> List[Dict[str, Any]]:
        """
        Perform federated retrieval across multiple nodes.

        Args:
            query (str): Search query
            node_results (List[List[Dict[str, Any]]]): Results from each node
            aggregation_method (str): Method for aggregating results

        Returns:
            List[Dict[str, Any]]: Aggregated retrieval results
        """
        if aggregation_method == 'rank_fusion':
            return self._rank_fusion_aggregation(node_results)
        elif aggregation_method == 'score_fusion':
            return self._score_fusion_aggregation(node_results)
        else:
            # Simple concatenation
            all_results = []
            for node_result in node_results:
                all_results.extend(node_result)
            return all_results

    def _rank_fusion_aggregation(self, node_results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Aggregate results using rank fusion."""
        # Simplified rank fusion (CombMNZ)
        doc_scores = {}

        for node_result in node_results:
            for rank, doc in enumerate(node_result):
                doc_id = doc.get('id', str(hash(str(doc))))
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'scores': []}
                # Higher score for higher rank
                doc_scores[doc_id]['scores'].append(len(node_result) - rank)

        # Calculate final scores
        for doc_id, data in doc_scores.items():
            scores = data['scores']
            # CombMNZ: sum of scores * number of occurrences
            data['final_score'] = sum(scores) * len(scores)

        # Sort by final score
        sorted_docs = sorted(doc_scores.values(),
                           key=lambda x: x['final_score'],
                           reverse=True)

        return [data['doc'] for data in sorted_docs]

    def _score_fusion_aggregation(self, node_results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Aggregate results using score fusion."""
        doc_scores = {}

        for node_result in node_results:
            for doc in node_result:
                doc_id = doc.get('id', str(hash(str(doc))))
                score = doc.get('score', 0.0)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'total_score': 0.0, 'count': 0}

                doc_scores[doc_id]['total_score'] += score
                doc_scores[doc_id]['count'] += 1

        # Average scores
        for data in doc_scores.values():
            data['avg_score'] = data['total_score'] / data['count']

        # Sort by average score
        sorted_docs = sorted(doc_scores.values(),
                           key=lambda x: x['avg_score'],
                           reverse=True)

        return [data['doc'] for data in sorted_docs]

    def get_federated_stats(self) -> Dict[str, Any]:
        """Get statistics about federated operations."""
        return {
            'node_id': self.node_id,
            'coordinator_address': self.coordinator_address,
            'privacy_config': self.privacy_config,
            'aggregation_config': self.aggregation_config
        }