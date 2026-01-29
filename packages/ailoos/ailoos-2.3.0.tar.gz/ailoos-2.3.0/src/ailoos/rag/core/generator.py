"""
Generator Component

This module defines the Generator component responsible for generating responses
in RAG systems. It provides the interface for different generation strategies
and language model integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class Generator(ABC):
    """
    Abstract base class for generation components in RAG systems.

    The Generator is responsible for producing coherent and relevant responses
    based on the input query and retrieved context. It can integrate with
    various language models and generation strategies.

    Attributes:
        config (Dict[str, Any]): Configuration for the generator
        model: Underlying language model
        tokenizer: Tokenizer for the model
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the generator with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - model_config: Settings for the language model
                - generation_config: Generation parameters (temperature, max_tokens, etc.)
                - prompt_config: Prompt templates and formatting
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        logger.info(f"Initialized {self.__class__.__name__} generator")

    @abstractmethod
    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate a response based on query and context.

        Args:
            query (str): The input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Returns:
            str: Generated response text

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def generate_stream(self, query: str, context: List[Dict[str, Any]], **kwargs):
        """
        Generate a response with streaming output.

        Args:
            query (str): The input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Yields:
            str: Chunks of generated text

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def format_prompt(self, query: str, context: List[Dict[str, Any]],
                     template: Optional[str] = None) -> str:
        """
        Format the query and context into a prompt for the model.

        Args:
            query (str): The input query
            context (List[Dict[str, Any]]): Retrieved context documents
            template (Optional[str]): Custom prompt template

        Returns:
            str: Formatted prompt
        """
        if template is None:
            template = self.config.get('prompt_template',
                "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:")

        # Format context
        context_text = "\n\n".join([
            f"Document {i+1}: {doc.get('content', doc.get('text', ''))}"
            for i, doc in enumerate(context)
        ])

        return template.format(query=query, context=context_text)

    def post_process_response(self, response: str) -> str:
        """
        Post-process the generated response.

        Args:
            response (str): Raw generated response

        Returns:
            str: Post-processed response
        """
        # Default implementation: basic cleaning
        response = response.strip()

        # Remove common artifacts
        if response.startswith("Answer:"):
            response = response[7:].strip()
        if response.startswith("Response:"):
            response = response[9:].strip()

        return response

    def get_generation_config(self, **kwargs) -> Dict[str, Any]:
        """
        Get generation configuration combining defaults and overrides.

        Args:
            **kwargs: Override parameters

        Returns:
            Dict[str, Any]: Complete generation configuration
        """
        default_config = self.config.get('generation_config', {
            'temperature': 0.7,
            'max_tokens': 512,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1
        })

        # Override with kwargs
        config = {**default_config, **kwargs}
        return config

    def __repr__(self) -> str:
        """String representation of the generator."""
        return f"{self.__class__.__name__}(config={self.config})"