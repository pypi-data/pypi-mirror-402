"""
Multi-Modal Projector for Empoorio-Vision
Proyector que alinea embeddings visuales con embeddings de texto.

Este componente es el único que se entrena en la fase multimodal.
Convierte las características visuales de SigLIP al espacio de embeddings de EmpoorioLM.
"""

import torch
import torch.nn as nn
import math
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MultiModalProjector(nn.Module):
    """
    Multi-Modal Projector: MLP de 2 capas que proyecta embeddings visuales al espacio textual.

    Arquitectura:
    - Capa 1: Linear(vision_dim, llm_hidden_size * 4) + GELU
    - Capa 2: Linear(llm_hidden_size * 4, llm_hidden_size)
    """

    def __init__(
        self,
        vision_dim: int = 768,  # CLIP ViT-Base hidden size
        llm_hidden_size: int = 768,  # EmpoorioLM hidden size
        dropout: float = 0.1
    ):
        super().__init__()

        self.vision_dim = vision_dim
        self.llm_hidden_size = llm_hidden_size

        # Two-layer MLP projector
        self.layers = nn.Sequential(
            nn.Linear(vision_dim, llm_hidden_size * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(llm_hidden_size * 4, llm_hidden_size),
            nn.Dropout(dropout)
        )

        # Initialize weights
        self.apply(self._init_weights)

        logger.info(f"MultiModalProjector initialized: {vision_dim}d -> {llm_hidden_size}d")

    def _init_weights(self, module):
        """Initialize projector weights."""
        if isinstance(module, nn.Linear):
            # Xavier/Glorot initialization
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, vision_features: torch.Tensor) -> torch.Tensor:
        """
        Project vision features to LLM embedding space.

        Args:
            vision_features: Visual embeddings [batch_size, num_patches, vision_dim]

        Returns:
            Projected features [batch_size, num_patches, llm_hidden_size]
        """
        batch_size, num_patches, vision_dim = vision_features.shape
        assert vision_dim == self.vision_dim, f"Expected vision_dim {self.vision_dim}, got {vision_dim}"

        # Flatten patches for linear layers
        vision_flat = vision_features.view(-1, vision_dim)  # [batch_size * num_patches, vision_dim]

        # Apply projection
        projected = self.layers(vision_flat)  # [batch_size * num_patches, llm_hidden_size]

        # Reshape back to patch dimension
        projected = projected.view(batch_size, num_patches, self.llm_hidden_size)

        return projected

    def get_projector_info(self) -> dict:
        """Get projector information."""
        return {
            "projector_type": "MLP-2Layer",
            "vision_dim": self.vision_dim,
            "llm_hidden_size": self.llm_hidden_size,
            "expansion_ratio": 4,
            "total_parameters": sum(p.numel() for p in self.parameters()),
            "trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad)
        }


def create_multimodal_projector(
    vision_dim: int = 1152,
    llm_hidden_size: int = 768,
    dropout: float = 0.1
) -> MultiModalProjector:
    """
    Factory function to create multimodal projector.

    Args:
        vision_dim: Dimension of vision embeddings
        llm_hidden_size: Hidden size of the LLM
        dropout: Dropout probability

    Returns:
        Initialized MultiModalProjector
    """
    return MultiModalProjector(
        vision_dim=vision_dim,
        llm_hidden_size=llm_hidden_size,
        dropout=dropout
    )


class VisionTokenInjector(nn.Module):
    """
    Injects visual tokens into text sequence (LLaVA-style).

    Converts projected vision features into visual tokens that can be
    concatenated with text tokens before feeding to the LLM.
    """

    def __init__(self, num_visual_tokens: int = 256):
        super().__init__()
        self.num_visual_tokens = num_visual_tokens

    def forward(
        self,
        vision_features: torch.Tensor,
        text_embeddings: torch.Tensor,
        vision_start_token: int = 1  # Special token indicating vision start
    ) -> torch.Tensor:
        """
        Inject visual tokens into text sequence.

        Args:
            vision_features: Projected vision features [batch_size, num_patches, llm_hidden_size]
            text_embeddings: Text embeddings [batch_size, seq_len, llm_hidden_size]
            vision_start_token: Token ID where to inject vision features

        Returns:
            Combined sequence [batch_size, seq_len + num_visual_tokens, llm_hidden_size]
        """
        batch_size, seq_len, hidden_size = text_embeddings.shape
        _, num_patches, _ = vision_features.shape

        # For simplicity, we'll prepend visual tokens to the sequence
        # In a full implementation, you'd find the vision_start_token position
        combined = torch.cat([vision_features, text_embeddings], dim=1)

        return combined

    def get_visual_token_length(self) -> int:
        """Get number of visual tokens added to sequence."""
        return self.num_visual_tokens