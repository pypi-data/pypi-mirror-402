"""
Vision Encoder for Empoorio-Vision
Codificador visual basado en SigLIP (Apache 2.0) para mantener soberanía total.

SigLIP (Sigmoid Loss for Language-Image Pre-training) es un modelo de Google
con licencia permisiva que proporciona embeddings visuales de alta calidad.
"""

import torch
import torch.nn as nn
from transformers import CLIPVisionModel, CLIPImageProcessor
from PIL import Image
import logging
from typing import Optional, Tuple, Union, List
import numpy as np

logger = logging.getLogger(__name__)


class VisionEncoder(nn.Module):
    """
    Vision Encoder basado en CLIP.
    Congela todos los pesos del modelo pre-entrenado y solo extrae características.
    """

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        freeze_weights: bool = True,
        device: str = "auto"
    ):
        super().__init__()

        # Auto-detect device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device)
        self.model_name = model_name
        self.freeze_weights = freeze_weights

        logger.info(f"Loading CLIP Vision Encoder: {model_name}")

        # Load CLIP vision model
        self.vision_model = CLIPVisionModel.from_pretrained(model_name)
        self.image_processor = CLIPImageProcessor.from_pretrained(model_name)

        # Move to device
        self.vision_model.to(self.device)

        # Freeze weights if requested
        if freeze_weights:
            for param in self.vision_model.parameters():
                param.requires_grad = False
            self.vision_model.eval()
            logger.info("✅ Vision encoder weights frozen")

        # Get model dimensions
        self.hidden_size = self.vision_model.config.hidden_size  # Typically 768 for CLIP ViT-Base
        self.num_patches = (self.vision_model.config.image_size // self.vision_model.config.patch_size) ** 2

        logger.info(f"Vision Encoder initialized: {self.hidden_size}d embeddings, {self.num_patches} patches")

    def preprocess_image(self, image: Union[Image.Image, torch.Tensor, np.ndarray]) -> torch.Tensor:
        """
        Preprocess image for SigLIP.

        Args:
            image: PIL Image, torch tensor, or numpy array

        Returns:
            Preprocessed pixel values tensor [1, 3, H, W]
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        elif isinstance(image, torch.Tensor):
            # Assume it's already preprocessed
            return image.to(self.device)

        # Use SigLIP processor
        inputs = self.image_processor(image, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)

        return pixel_values

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """
        Extract visual features from preprocessed images.

        Args:
            pixel_values: Preprocessed pixel values [batch_size, 3, H, W]

        Returns:
            Visual embeddings [batch_size, num_patches, hidden_size]
        """
        with torch.no_grad() if self.freeze_weights else torch.enable_grad():
            outputs = self.vision_model(pixel_values)
            # Use last hidden state as visual embeddings
            visual_embeddings = outputs.last_hidden_state  # [batch_size, num_patches+1, hidden_size]

            # Remove CLS token (first token) - similar to ViT
            visual_embeddings = visual_embeddings[:, 1:, :]  # [batch_size, num_patches, hidden_size]

        return visual_embeddings

    def get_image_features(self, image: Union[Image.Image, torch.Tensor, np.ndarray]) -> torch.Tensor:
        """
        Convenience method: preprocess + extract features in one call.

        Args:
            image: Input image

        Returns:
            Visual embeddings [num_patches, hidden_size]
        """
        pixel_values = self.preprocess_image(image)
        features = self.forward(pixel_values)
        return features.squeeze(0)  # Remove batch dimension for single image

    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_type": "SigLIP Vision Encoder",
            "model_name": self.model_name,
            "hidden_size": self.hidden_size,
            "num_patches": self.num_patches,
            "freeze_weights": self.freeze_weights,
            "device": str(self.device)
        }


# Alias for backward compatibility
SigLIPEncoder = VisionEncoder


def create_vision_encoder(
    model_name: str = "google/siglip-so400m-patch14-384",
    freeze_weights: bool = True,
    device: str = "auto"
) -> VisionEncoder:
    """
    Factory function to create vision encoder.

    Args:
        model_name: HuggingFace model name
        freeze_weights: Whether to freeze encoder weights
        device: Device to run on

    Returns:
        Initialized VisionEncoder
    """
    return VisionEncoder(
        model_name=model_name,
        freeze_weights=freeze_weights,
        device=device
    )