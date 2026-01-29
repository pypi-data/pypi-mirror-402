"""
Text Splitter Utilities

This module provides utilities for splitting and chunking text documents
for efficient processing in RAG systems.
"""

from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class TextSplitter:
    """
    Text splitter for chunking documents into manageable pieces.

    This class provides various strategies for splitting text while
    preserving semantic meaning and context.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize text splitter.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - chunk_size: Target chunk size in characters
                - chunk_overlap: Overlap between chunks
                - separators: List of separators to use for splitting
                - preserve_metadata: Whether to preserve document metadata
        """
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.separators = config.get('separators', ['\n\n', '\n', '. ', ' ', ''])
        self.preserve_metadata = config.get('preserve_metadata', True)

    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks.

        Args:
            text (str): Text to split
            metadata (Optional[Dict[str, Any]]): Document metadata

        Returns:
            List[Dict[str, Any]]: List of text chunks with metadata
        """
        if not text:
            return []

        # Try different splitting strategies
        chunks = self._recursive_split(text)

        # Create chunk objects
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_length': len(chunk)
            }

            if self.preserve_metadata and metadata:
                chunk_metadata.update(metadata)

            chunk_objects.append({
                'content': chunk,
                'metadata': chunk_metadata
            })

        logger.debug(f"Split text into {len(chunk_objects)} chunks")
        return chunk_objects

    def _recursive_split(self, text: str) -> List[str]:
        """
        Recursively split text using separators.

        Args:
            text (str): Text to split

        Returns:
            List[str]: Text chunks
        """
        return self._split_with_separators(text, self.separators)

    def _split_with_separators(self, text: str, separators: List[str]) -> List[str]:
        """
        Split text using a hierarchy of separators.

        Args:
            text (str): Text to split
            separators (List[str]): List of separators to try

        Returns:
            List[str]: Text chunks
        """
        final_chunks = []

        for separator in separators:
            if separator == '':
                # Final split by character count
                chunks = self._split_by_length(text)
                final_chunks.extend(chunks)
                break

            if separator in text:
                # Split by separator
                parts = text.split(separator)

                good_splits = []
                current_chunk = ''

                for part in parts:
                    # Add separator back (except for last part in some cases)
                    candidate = part + separator if part else separator

                    if len(current_chunk + candidate) > self.chunk_size and current_chunk:
                        # Current chunk is full
                        good_splits.append(current_chunk.rstrip())
                        current_chunk = candidate
                    else:
                        current_chunk += candidate

                if current_chunk:
                    good_splits.append(current_chunk.rstrip())

                # Recursively split large chunks
                for chunk in good_splits:
                    if len(chunk) > self.chunk_size:
                        sub_chunks = self._split_with_separators(chunk, separators[separators.index(separator) + 1:])
                        final_chunks.extend(sub_chunks)
                    else:
                        final_chunks.append(chunk)

                break

        return final_chunks

    def _split_by_length(self, text: str) -> List[str]:
        """
        Split text by character length with overlap.

        Args:
            text (str): Text to split

        Returns:
            List[str]: Text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Adjust end to not cut words
            if end < len(text):
                # Find last space before chunk_size
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap

            # Ensure progress
            if start >= end:
                break

        return chunks

    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split multiple documents.

        Args:
            documents (List[Dict[str, Any]]): Documents to split

        Returns:
            List[Dict[str, Any]]: Split document chunks
        """
        all_chunks = []

        for doc in documents:
            text = doc.get('content', doc.get('text', ''))
            metadata = {k: v for k, v in doc.items() if k not in ['content', 'text']}

            chunks = self.split_text(text, metadata)
            all_chunks.extend(chunks)

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

    def get_splitter_stats(self) -> Dict[str, Any]:
        """Get statistics about the splitter configuration."""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'separators': self.separators,
            'preserve_metadata': self.preserve_metadata
        }


class SemanticTextSplitter(TextSplitter):
    """
    Semantic text splitter that considers meaning and context.

    This splitter uses semantic understanding to create more meaningful chunks.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.semantic_config = config.get('semantic_config', {})

    def _recursive_split(self, text: str) -> List[str]:
        """
        Semantic-aware text splitting.

        Args:
            text (str): Text to split

        Returns:
            List[str]: Semantically meaningful chunks
        """
        # For now, fall back to basic splitting
        # In practice, this would use NLP models for semantic segmentation
        return super()._recursive_split(text)


class MarkdownSplitter(TextSplitter):
    """
    Specialized splitter for Markdown documents.

    This splitter respects Markdown structure (headers, lists, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Markdown-specific separators
        self.separators = ['\n# ', '\n## ', '\n### ', '\n\n', '\n', '. ', ' ', '']

    def _recursive_split(self, text: str) -> List[str]:
        """
        Markdown-aware text splitting.

        Args:
            text (str): Markdown text to split

        Returns:
            List[str]: Markdown-aware chunks
        """
        return self._split_with_separators(text, self.separators)