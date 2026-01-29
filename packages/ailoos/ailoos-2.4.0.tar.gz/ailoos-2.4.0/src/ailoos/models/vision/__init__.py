"""
Empoorio-Vision: Multimodal Vision Module for EmpoorioLM
Módulo de visión multimodal para dotar a EmpoorioLM de capacidad visual.

Este módulo implementa:
- VisionEncoder: Codificador visual basado en SigLIP (Apache 2.0)
- MultiModalProjector: Proyector que alinea embeddings visuales con texto
- LVLMWrapper: Wrapper completo para Large Vision-Language Model
"""

from .encoder import VisionEncoder, SigLIPEncoder
from .projector import MultiModalProjector
from .lvlm_wrapper import LVLMWrapper, EmpoorioVision, create_empoorio_vision, VisionConfig
from .image_processing import AnyResImageProcessor, ImageTokenizer, create_test_image_with_text

__all__ = [
    'VisionEncoder',
    'SigLIPEncoder',
    'MultiModalProjector',
    'LVLMWrapper',
    'EmpoorioVision',
    'create_empoorio_vision',
    'VisionConfig',
    'AnyResImageProcessor',
    'ImageTokenizer',
    'create_test_image_with_text'
]