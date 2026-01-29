#!/usr/bin/env python3
"""
Empoorio-Vision - Independent Vision Encoder for EmpoorioLM
Completely original implementation with our own copyright.
Inspired by open research, not dependent on any other vision models.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, List, Dict, Any, Union
from dataclasses import dataclass
from PIL import Image
import logging

from ...core.config import Config
from ...utils.logging import AiloosLogger


@dataclass
class EmpoorioVisionConfig:
    """Configuration for Empoorio-Vision encoder."""

    # Model dimensions
    hidden_size: int = 1024
    num_hidden_layers: int = 24
    num_attention_heads: int = 16
    intermediate_size: int = 4096

    # Vision specific
    image_size: int = 224
    patch_size: int = 16
    num_channels: int = 3
    num_patches: int = (224 // 16) ** 2  # 196 for 224x224 with 16x16 patches

    # Architecture
    layer_norm_eps: float = 1e-6
    hidden_dropout_prob: float = 0.0
    attention_probs_dropout_prob: float = 0.0

    # Position embeddings
    use_2d_position_embeddings: bool = True

    # Output
    projection_dim: int = 512  # Dimension to project to for multimodal fusion

    def __post_init__(self):
        if self.num_patches != (self.image_size // self.patch_size) ** 2:
            self.num_patches = (self.image_size // self.patch_size) ** 2


class EmpoorioPatchEmbedding(nn.Module):
    """Patch embedding layer for vision input."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.config = config

        # Convolutional projection of patches
        self.projection = nn.Conv2d(
            config.num_channels,
            config.hidden_size,
            kernel_size=config.patch_size,
            stride=config.patch_size,
            bias=True
        )

        # Position embeddings
        if config.use_2d_position_embeddings:
            # 2D position embeddings for spatial understanding
            self.position_embeddings = nn.Parameter(
                torch.zeros(1, config.num_patches, config.hidden_size)
            )
        else:
            # 1D position embeddings
            self.position_embeddings = nn.Parameter(
                torch.zeros(1, config.num_patches + 1, config.hidden_size)  # +1 for CLS token
            )

        # CLS token (optional, for classification-like tasks)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, config.hidden_size))

        self.dropout = nn.Dropout(config.hidden_dropout_prob)

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pixel_values: [batch_size, num_channels, height, width]
        Returns:
            embeddings: [batch_size, num_patches + 1, hidden_size]
        """
        batch_size = pixel_values.shape[0]

        # Patch embedding via convolution
        patch_embeddings = self.projection(pixel_values)  # [batch, hidden_size, h//patch, w//patch]
        patch_embeddings = patch_embeddings.flatten(2).transpose(1, 2)  # [batch, num_patches, hidden_size]

        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)  # [batch, 1, hidden_size]
        embeddings = torch.cat([cls_tokens, patch_embeddings], dim=1)  # [batch, num_patches + 1, hidden_size]

        # Add position embeddings
        if self.config.use_2d_position_embeddings:
            # For 2D position embeddings, we add to all tokens including CLS
            embeddings = embeddings + self.position_embeddings
        else:
            embeddings = embeddings + self.position_embeddings

        embeddings = self.dropout(embeddings)

        return embeddings


class EmpoorioVisionAttention(nn.Module):
    """Multi-head self-attention for vision."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.num_attention_heads = config.num_attention_heads
        self.attention_head_size = config.hidden_size // config.num_attention_heads
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(config.hidden_size, self.all_head_size, bias=True)
        self.key = nn.Linear(config.hidden_size, self.all_head_size, bias=True)
        self.value = nn.Linear(config.hidden_size, self.all_head_size, bias=True)

        self.dropout = nn.Dropout(config.attention_probs_dropout_prob)

    def transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        """Transpose tensor for attention computation."""
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(new_x_shape)
        return x.permute(0, 2, 1, 3)  # [batch, heads, seq, head_dim]

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Args:
            hidden_states: [batch_size, seq_length, hidden_size]
            attention_mask: [batch_size, 1, 1, seq_length]
        Returns:
            context_layer: [batch_size, seq_length, hidden_size]
            attention_probs: [batch_size, num_heads, seq_length, seq_length] (optional)
        """
        mixed_query_layer = self.query(hidden_states)
        mixed_key_layer = self.key(hidden_states)
        mixed_value_layer = self.value(hidden_states)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities
        attention_probs = nn.functional.softmax(attention_scores, dim=-1)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(new_context_layer_shape)

        outputs = (context_layer, attention_probs) if output_attentions else (context_layer,)

        return outputs


class EmpoorioVisionMLP(nn.Module):
    """MLP for vision transformer."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.fc1 = nn.Linear(config.hidden_size, config.intermediate_size)
        self.fc2 = nn.Linear(config.intermediate_size, config.hidden_size)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(config.hidden_dropout_prob)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.fc1(hidden_states)
        hidden_states = self.activation(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.fc2(hidden_states)
        hidden_states = self.dropout(hidden_states)
        return hidden_states


class EmpoorioVisionLayer(nn.Module):
    """Single transformer layer for vision."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.attention = EmpoorioVisionAttention(config)
        self.mlp = EmpoorioVisionMLP(config)

        self.layernorm_before = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.layernorm_after = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        # Pre-norm architecture
        attention_output = self.layernorm_before(hidden_states)
        attention_output, attention_probs = self.attention(
            attention_output, attention_mask, output_attentions=output_attentions
        )
        hidden_states = hidden_states + attention_output

        # MLP
        layer_output = self.layernorm_after(hidden_states)
        layer_output = self.mlp(layer_output)
        hidden_states = hidden_states + layer_output

        outputs = (hidden_states, attention_probs) if output_attentions else (hidden_states,)

        return outputs


class EmpoorioVisionEncoder(nn.Module):
    """Vision encoder backbone."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.config = config

        self.embeddings = EmpoorioPatchEmbedding(config)
        self.layers = nn.ModuleList([
            EmpoorioVisionLayer(config) for _ in range(config.num_hidden_layers)
        ])

        self.layernorm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

    def forward(
        self,
        pixel_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        """
        Args:
            pixel_values: [batch_size, num_channels, height, width]
        Returns:
            Dict with last_hidden_state and optional hidden_states/attentions
        """
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        hidden_states = self.embeddings(pixel_values)

        for i, layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            layer_outputs = layer(hidden_states, attention_mask, output_attentions)

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_attentions = all_attentions + (layer_outputs[1],)

        # Final layer norm
        hidden_states = self.layernorm(hidden_states)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        return {
            "last_hidden_state": hidden_states,
            "hidden_states": all_hidden_states,
            "attentions": all_attentions,
        }


class EmpoorioVisionModel(nn.Module):
    """Complete vision model with projection head."""

    def __init__(self, config: EmpoorioVisionConfig):
        super().__init__()
        self.config = config

        self.vision_encoder = EmpoorioVisionEncoder(config)

        # Projection head to align with text embedding space
        self.vision_projection = nn.Linear(config.hidden_size, config.projection_dim, bias=True)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        """Initialize weights following vision transformer conventions."""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Conv2d):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def forward(
        self,
        pixel_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        """
        Args:
            pixel_values: [batch_size, num_channels, height, width]
        Returns:
            Dict with projected vision embeddings and optional outputs
        """
        vision_outputs = self.vision_encoder(
            pixel_values=pixel_values,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )

        # Project to common embedding space
        last_hidden_state = vision_outputs["last_hidden_state"]
        projected_embeddings = self.vision_projection(last_hidden_state)

        return {
            "vision_embeddings": projected_embeddings,
            "last_hidden_state": last_hidden_state,
            "hidden_states": vision_outputs["hidden_states"],
            "attentions": vision_outputs["attentions"],
        }


class EmpoorioImageProcessor:
    """Image preprocessing for Empoorio-Vision."""

    def __init__(self, config: EmpoorioVisionConfig):
        self.config = config
        self.image_size = config.image_size
        self.patch_size = config.patch_size

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess a single image for the vision encoder.

        Args:
            image: PIL Image
        Returns:
            pixel_values: [1, num_channels, height, width]
        """
        # Resize image
        image = image.resize((self.image_size, self.image_size), Image.BILINEAR)

        # Convert to tensor and normalize
        pixel_values = torch.tensor(list(image.getdata())).float()
        pixel_values = pixel_values.view(image.size[1], image.size[0], 3)  # [H, W, C]
        pixel_values = pixel_values.permute(2, 0, 1)  # [C, H, W]

        # Normalize to [0, 1]
        pixel_values = pixel_values / 255.0

        # Normalize with ImageNet mean/std (optional, can be trained)
        # mean = torch.tensor([0.485, 0.456, 0.406]).view(-1, 1, 1)
        # std = torch.tensor([0.229, 0.224, 0.225]).view(-1, 1, 1)
        # pixel_values = (pixel_values - mean) / std

        # Add batch dimension
        pixel_values = pixel_values.unsqueeze(0)  # [1, C, H, W]

        return pixel_values

    def preprocess_batch(self, images: List[Image.Image]) -> torch.Tensor:
        """
        Preprocess a batch of images.

        Args:
            images: List of PIL Images
        Returns:
            pixel_values: [batch_size, num_channels, height, width]
        """
        batch_tensors = []
        for image in images:
            tensor = self.preprocess_image(image)
            batch_tensors.append(tensor.squeeze(0))  # Remove batch dim temporarily

        return torch.stack(batch_tensors, dim=0)  # [batch, C, H, W]


# Factory functions
def create_empoorio_vision_base() -> EmpoorioVisionModel:
    """Create base Empoorio-Vision model."""
    config = EmpoorioVisionConfig(
        hidden_size=768,
        num_hidden_layers=12,
        num_attention_heads=12,
        intermediate_size=3072,
        projection_dim=512,
    )
    return EmpoorioVisionModel(config)


def create_empoorio_vision_large() -> EmpoorioVisionModel:
    """Create large Empoorio-Vision model."""
    config = EmpoorioVisionConfig(
        hidden_size=1024,
        num_hidden_layers=24,
        num_attention_heads=16,
        intermediate_size=4096,
        projection_dim=512,
    )
    return EmpoorioVisionModel(config)


def create_empoorio_vision_huge() -> EmpoorioVisionModel:
    """Create huge Empoorio-Vision model."""
    config = EmpoorioVisionConfig(
        hidden_size=1280,
        num_hidden_layers=32,
        num_attention_heads=20,
        intermediate_size=5120,
        projection_dim=512,
    )
    return EmpoorioVisionModel(config)