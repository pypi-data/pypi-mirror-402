"""
LVLM Wrapper for Empoorio-Vision
Large Vision-Language Model wrapper que integra EmpoorioLM con capacidades visuales.

Implementa Visual Token Injection (estilo LLaVA) para combinar texto e imágenes.
"""

import torch
import torch.nn as nn
from torch.amp import autocast
from PIL import Image
import logging
from typing import Optional, Union, Dict, Any, List, Tuple
from dataclasses import dataclass

from .encoder import VisionEncoder
from .projector import MultiModalProjector, VisionTokenInjector
from .image_processing import AnyResImageProcessor, ImageTokenizer

# Import EmpoorioLM components
try:
    from ..empoorio_lm import EmpoorioLM, EmpoorioLMConfig
    from ..moe import MoEEmpoorioLM
except ImportError:
    # Fallback for testing
    EmpoorioLM = None
    EmpoorioLMConfig = None
    MoEEmpoorioLM = None

logger = logging.getLogger(__name__)


@dataclass
class VisionConfig:
    """Configuration for vision components."""
    vision_model_name: str = "openai/clip-vit-base-patch32"
    vision_dim: int = 768  # CLIP ViT-Base hidden size
    num_visual_tokens: int = 256
    freeze_vision_encoder: bool = True
    projector_dropout: float = 0.1

    # AnyRes configuration
    use_anyres: bool = True
    base_patch_size: int = 336
    max_patches: int = 16
    overlap_ratio: float = 0.1
    global_context_scale: float = 0.25

    # Quantization configuration
    use_mixed_precision: bool = True
    autocast_dtype: str = "bfloat16"  # "float16", "bfloat16", or "float32"


class LVLMWrapper(nn.Module):
    """
    Large Vision-Language Model Wrapper.

    Combina:
    - VisionEncoder (SigLIP congelado)
    - MultiModalProjector (MLP entrenable)
    - EmpoorioLM (LLM base)
    - VisionTokenInjector (para combinar secuencias)
    """

    def __init__(
        self,
        base_model: nn.Module,
        vision_config: Optional[VisionConfig] = None
    ):
        super().__init__()

        self.vision_config = vision_config or VisionConfig()

        # Vision components
        self.vision_encoder = VisionEncoder(
            model_name=self.vision_config.vision_model_name,
            freeze_weights=self.vision_config.freeze_vision_encoder
        )

        self.projector = MultiModalProjector(
            vision_dim=self.vision_config.vision_dim,
            llm_hidden_size=base_model.config.hidden_size if hasattr(base_model, 'config') else 768,
            dropout=self.vision_config.projector_dropout
        )

        self.token_injector = VisionTokenInjector(
            num_visual_tokens=self.vision_config.num_visual_tokens
        )

        # AnyRes components
        if self.vision_config.use_anyres:
            self.anyres_processor = AnyResImageProcessor(
                base_patch_size=self.vision_config.base_patch_size,
                max_patches=self.vision_config.max_patches,
                overlap_ratio=self.vision_config.overlap_ratio,
                global_context_scale=self.vision_config.global_context_scale
            )
            self.image_tokenizer = ImageTokenizer(
                max_visual_tokens=self.vision_config.num_visual_tokens
            )
        else:
            self.anyres_processor = None
            self.image_tokenizer = None

        # Base LLM
        self.base_model = base_model

        # Special tokens (would be added to tokenizer)
        self.vision_start_token = "<vision>"
        self.vision_end_token = "</vision>"

        logger.info("LVLMWrapper initialized with vision capabilities")

    def preprocess_inputs(
        self,
        text: str,
        image: Optional[Union[Image.Image, torch.Tensor]] = None,
        tokenizer = None
    ) -> Dict[str, torch.Tensor]:
        """
        Preprocess text and image inputs with AnyRes support.

        Args:
            text: Input text
            image: Optional input image
            tokenizer: Text tokenizer

        Returns:
            Dictionary with processed inputs
        """
        inputs = {}

        # Process text
        if tokenizer:
            # Add vision tokens if image is present
            if image is not None:
                text_with_vision = f"{self.vision_start_token} {text}"
            else:
                text_with_vision = text

            inputs['input_ids'] = tokenizer.encode(text_with_vision)
            inputs['input_ids'] = torch.tensor(inputs['input_ids']).unsqueeze(0)
        else:
            # Mock tokenization for testing
            inputs['input_ids'] = torch.randint(0, 1000, (1, 10))

        # Process image with AnyRes
        if image is not None:
            if self.vision_config.use_anyres and self.anyres_processor:
                # Use AnyRes processing
                processed_image = self.anyres_processor.process_image(image)
                visual_tokens = self.image_tokenizer.tokenize_image(
                    processed_image, self.vision_encoder
                )

                # Store processed visual features
                inputs['visual_features'] = visual_tokens['visual_tokens']
                inputs['image_patches_info'] = processed_image['patches_info']
                inputs['anyres_strategy'] = processed_image['strategy']
            else:
                # Fallback to single image processing
                pixel_values = self.vision_encoder.preprocess_image(image)
                inputs['pixel_values'] = pixel_values

            inputs['has_image'] = True
        else:
            inputs['has_image'] = False

        return inputs

    def forward(
        self,
        input_ids: torch.Tensor,
        pixel_values: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Forward pass combining vision and text with quantization-aware processing.

        Args:
            input_ids: Text token IDs [batch_size, seq_len]
            pixel_values: Preprocessed image pixels [batch_size, 3, H, W]
            attention_mask: Attention mask
            labels: Labels for training

        Returns:
            Model outputs dictionary
        """
        device = input_ids.device
        batch_size = input_ids.shape[0]

        # Determine autocast dtype
        autocast_dtype = None
        if self.vision_config.use_mixed_precision:
            try:
                requested_dtype = getattr(torch, self.vision_config.autocast_dtype)
                # Check if autocast is supported for this device/dtype combination
                if device.type == "cuda" or (device.type == "cpu" and requested_dtype == torch.bfloat16):
                    autocast_dtype = requested_dtype
                else:
                    logger.warning(f"Autocast {self.vision_config.autocast_dtype} not supported on {device.type}, falling back to full precision")
            except AttributeError:
                logger.warning(f"Unknown autocast dtype: {self.vision_config.autocast_dtype}, falling back to full precision")

        with autocast(device_type=device.type, dtype=autocast_dtype) if autocast_dtype else torch.no_grad():
            # Get text embeddings from base model
            if hasattr(self.base_model, 'wte'):
                text_embeddings = self.base_model.wte(input_ids)
            else:
                # Mock embeddings for testing
                text_embeddings = torch.randn(batch_size, input_ids.shape[1], 768, device=device)

            # Process vision if present
            if pixel_values is not None or 'visual_features' in kwargs:
                if 'visual_features' in kwargs:
                    # AnyRes mode: visual features already processed
                    # Ensure visual features are in correct dtype for projector
                    visual_features = kwargs['visual_features']
                    if autocast_dtype and visual_features.dtype != autocast_dtype:
                        visual_features = visual_features.to(autocast_dtype)
                    projected_vision = self.projector(visual_features)
                else:
                    # Traditional mode: process pixel values
                    vision_features = self.vision_encoder(pixel_values)  # [batch_size, num_patches, vision_dim]
                    # Ensure vision features are in correct dtype for projector
                    if autocast_dtype and vision_features.dtype != autocast_dtype:
                        vision_features = vision_features.to(autocast_dtype)
                    projected_vision = self.projector(vision_features)  # [batch_size, num_patches, llm_hidden_size]

                # Ensure projected vision matches text embeddings dtype
                if projected_vision.dtype != text_embeddings.dtype:
                    projected_vision = projected_vision.to(text_embeddings.dtype)

                # Inject visual tokens into text sequence
                combined_embeddings = self.token_injector(
                    projected_vision,
                    text_embeddings
                )  # [batch_size, seq_len + num_visual, llm_hidden_size]

                # Update input_ids for attention mask
                visual_tokens = torch.full(
                    (batch_size, projected_vision.shape[1]),  # Use actual number of visual tokens
                    -100,  # Ignore in loss computation
                    dtype=input_ids.dtype,
                    device=device
                )
                combined_input_ids = torch.cat([visual_tokens, input_ids], dim=1)

            else:
                combined_embeddings = text_embeddings
                combined_input_ids = input_ids

            # Forward through base model
            if hasattr(self.base_model, 'forward'):
                outputs = self.base_model(
                    input_ids=combined_input_ids,
                    inputs_embeds=combined_embeddings,
                    attention_mask=attention_mask,
                    labels=labels,
                    **kwargs
                )
            else:
                # Mock output for testing
                outputs = {
                    'logits': torch.randn(batch_size, combined_input_ids.shape[1], 1000, device=device),
                    'loss': torch.tensor(1.5, device=device) if labels is not None else None
                }

        # Add vision-specific outputs (outside autocast context)
        outputs['vision_features'] = projected_vision if pixel_values is not None or 'visual_features' in kwargs else None
        outputs['has_image'] = pixel_values is not None or 'visual_features' in kwargs
        outputs['quantization_info'] = {
            'mixed_precision': self.vision_config.use_mixed_precision,
            'autocast_dtype': self.vision_config.autocast_dtype,
            'device_type': device.type
        }

        return outputs

    def generate(
        self,
        text: str,
        image: Optional[Union[Image.Image, torch.Tensor]] = None,
        max_length: int = 100,
        **generate_kwargs
    ) -> str:
        """
        Generate text response given text and optional image with quantization support.

        Args:
            text: Input text prompt
            image: Optional input image
            max_length: Maximum generation length

        Returns:
            Generated text response
        """
        # Preprocess inputs
        inputs = self.preprocess_inputs(text, image)

        # Determine autocast dtype for generation
        device = inputs['input_ids'].device
        autocast_dtype = None
        if self.vision_config.use_mixed_precision:
            try:
                requested_dtype = getattr(torch, self.vision_config.autocast_dtype)
                # Check if autocast is supported for this device/dtype combination
                if device.type == "cuda" or (device.type == "cpu" and requested_dtype == torch.bfloat16):
                    autocast_dtype = requested_dtype
            except AttributeError:
                pass

        # Generate with appropriate precision
        with autocast(device_type=device.type, dtype=autocast_dtype) if autocast_dtype else torch.no_grad():
            if hasattr(self.base_model, 'generate'):
                generated_ids = self.base_model.generate(
                    inputs['input_ids'],
                    max_length=max_length,
                    **generate_kwargs
                )
            else:
                # Mock generation
                generated_ids = torch.randint(0, 1000, (1, max_length))

        # Decode (mock for now)
        # In real implementation, would use tokenizer.decode()
        response = f"Response to: '{text}'"
        if inputs['has_image']:
            response += " (with image analysis)"
            if 'anyres_strategy' in inputs:
                response += f" [{inputs['anyres_strategy']} processing]"

        return response

    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information."""
        base_info = {}
        if hasattr(self.base_model, 'get_model_info'):
            base_info = self.base_model.get_model_info()

        vision_info = self.vision_encoder.get_model_info()
        projector_info = self.projector.get_projector_info()

        return {
            **base_info,
            "vision_capabilities": True,
            "vision_encoder": vision_info,
            "multimodal_projector": projector_info,
            "visual_tokens": self.vision_config.num_visual_tokens,
            "total_parameters": (
                sum(p.numel() for p in self.parameters()) +
                vision_info.get('hidden_size', 0) * vision_info.get('num_patches', 0)
            ),
            "trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad)
        }


# Alias for the complete model
EmpoorioVision = LVLMWrapper


def create_empoorio_vision(
    base_model_name_or_path: str = "models/empoorio_lm/v1.0.0",
    vision_config: Optional[VisionConfig] = None,
    use_moe: bool = True,
    device: str = "auto"
) -> LVLMWrapper:
    """
    Factory function to create EmpoorioVision model with CLIP vision encoder.

    Args:
        base_model_name_or_path: Path to EmpoorioLM model
        vision_config: Vision configuration (uses CLIP by default)
        use_moe: Whether to use MoE version
        device: Device to run on

    Returns:
        Initialized EmpoorioVision model
    """
    """
    Factory function to create EmpoorioVision model.

    Args:
        base_model_name_or_path: Path to EmpoorioLM model
        vision_config: Vision configuration
        use_moe: Whether to use MoE version
        device: Device to run on

    Returns:
        Initialized EmpoorioVision model
    """
    vision_config = vision_config or VisionConfig()

    # Load base model
    try:
        if use_moe and MoEEmpoorioLM:
            # Try to load MoE version
            base_model = MoEEmpoorioLM.from_pretrained(base_model_name_or_path)
        elif EmpoorioLM:
            # Load standard version
            base_model = EmpoorioLM.from_pretrained(base_model_name_or_path)
        else:
            raise ImportError("EmpoorioLM models not available")
    except Exception as e:
        logger.warning(f"Could not load EmpoorioLM from {base_model_name_or_path}: {e}")
        logger.warning("Creating mock base model for testing")

        # Create mock base model for testing
        class MockBaseModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.wte = nn.Embedding(1000, 768)
                self.config = type('Config', (), {'n_embd': 768})()

            def forward(self, input_ids=None, inputs_embeds=None, **kwargs):
                seq_len = inputs_embeds.shape[1] if inputs_embeds is not None else input_ids.shape[1]
                return {
                    'logits': torch.randn(1, seq_len, 1000),
                    'loss': None
                }

        base_model = MockBaseModel()

    # Create vision wrapper
    model = LVLMWrapper(base_model, vision_config)

    logger.info("EmpoorioVision model created successfully")
    return model