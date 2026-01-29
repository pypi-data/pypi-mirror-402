"""
Contextual RAG Implementation

This module implements the Contextual RAG technique, which considers
conversation history and context for more relevant retrieval and generation.
"""

from typing import List, Dict, Any, Optional
import logging

from .naive_rag import NaiveRAG

logger = logging.getLogger(__name__)


class ContextualRAG(NaiveRAG):
    """
    Contextual RAG implementation with conversation history awareness.

    This technique maintains and utilizes conversation context to improve
    retrieval relevance and response coherence in multi-turn interactions.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.context_config = config.get('context_config', {})
        self.conversation_history = []

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents considering conversation context.

        Args:
            query (str): Current query
            top_k (int): Number of documents to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters

        Returns:
            List[Dict[str, Any]]: Context-aware retrieved documents
        """
        # Augment query with conversation context
        contextual_query = self._augment_query_with_context(query)

        # Retrieve with augmented query
        documents = super().retrieve(contextual_query, top_k=top_k, filters=filters)

        return documents

    def _augment_query_with_context(self, query: str) -> str:
        """Augment query with relevant conversation history."""
        # Placeholder: simple concatenation of recent history
        recent_history = self.conversation_history[-3:]  # Last 3 exchanges
        context_parts = [f"Previous: {turn}" for turn in recent_history]
        context_parts.append(f"Current: {query}")

        return " | ".join(context_parts)

    def update_conversation_history(self, query: str, response: str):
        """Update conversation history with new exchange."""
        self.conversation_history.append(f"Q: {query} A: {response}")

        # Limit history length
        max_history = self.context_config.get('max_history', 10)
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]

    def get_pipeline_info(self) -> Dict[str, Any]:
        info = super().get_pipeline_info()
        info.update({
            'technique': 'ContextualRAG',
            'description': 'Context-aware RAG with conversation history',
            'context_config': self.context_config,
            'conversation_length': len(self.conversation_history)
        })
        return info