"""
Image Processing Utilities for Empoorio-Vision
Utilidades avanzadas de procesamiento de imágenes con soporte AnyRes (Dynamic High-Resolution Patching).

AnyRes permite procesar imágenes de cualquier resolución dividiéndolas en parches
inteligentes mientras mantiene el contexto global.
"""

import torch
import torch.nn.functional as F
from PIL import Image
import math
from typing import List, Tuple, Optional, Dict, Any, Union
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AnyResImageProcessor:
    """
    AnyRes Image Processor: Dynamic High-Resolution Patching

    Divide imágenes grandes en parches inteligentes manteniendo contexto global.
    Inspirado en LLaVA 1.6 y GPT-4V.
    """

    def __init__(
        self,
        base_patch_size: int = 336,  # Tamaño base de parche (CLIP estándar)
        max_patches: int = 16,        # Máximo número de parches
        overlap_ratio: float = 0.1,   # Solapamiento entre parches
        global_context_scale: float = 0.25  # Escala para thumbnail global
    ):
        self.base_patch_size = base_patch_size
        self.max_patches = max_patches
        self.overlap_ratio = overlap_ratio
        self.global_context_scale = global_context_scale

    def process_image(
        self,
        image: Union[Image.Image, torch.Tensor, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Process image with AnyRes dynamic patching.

        Args:
            image: Input image

        Returns:
            Dictionary with processed patches and metadata
        """
        # Convertir a PIL si es necesario
        if isinstance(image, torch.Tensor):
            # Assume it's already a tensor, convert to PIL for processing
            if image.dim() == 4:  # [B, C, H, W]
                image = image.squeeze(0)
            if image.dim() == 3:  # [C, H, W]
                image = image.permute(1, 2, 0).cpu().numpy()
                image = Image.fromarray((image * 255).astype(np.uint8))
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        orig_width, orig_height = image.size

        # Determinar estrategia de patching
        patches_info = self._compute_patch_strategy(orig_width, orig_height)

        # Crear thumbnail global para contexto
        global_thumbnail = self._create_global_thumbnail(image)

        # Crear parches locales
        local_patches = self._create_local_patches(image, patches_info)

        return {
            'global_thumbnail': global_thumbnail,
            'local_patches': local_patches,
            'patches_info': patches_info,
            'original_size': (orig_width, orig_height),
            'strategy': 'anyres' if len(local_patches) > 1 else 'single'
        }

    def _compute_patch_strategy(
        self,
        width: int,
        height: int
    ) -> Dict[str, Any]:
        """
        Compute optimal patching strategy for the image.

        Returns grid layout that maximizes coverage while respecting max_patches.
        """
        # Calcular cuántos parches necesitamos
        width_ratio = width / self.base_patch_size
        height_ratio = height / self.base_patch_size

        # Determinar grid size
        grid_cols = math.ceil(math.sqrt(width_ratio))
        grid_rows = math.ceil(math.sqrt(height_ratio))

        # Ajustar para no exceder max_patches
        total_patches = grid_cols * grid_rows
        if total_patches > self.max_patches:
            # Reducir grid manteniendo proporción
            scale_factor = math.sqrt(self.max_patches / total_patches)
            grid_cols = max(1, int(grid_cols * scale_factor))
            grid_rows = max(1, int(grid_rows * scale_factor))

        # Calcular tamaño efectivo de cada parche (con solapamiento)
        effective_patch_size = int(self.base_patch_size * (1 + self.overlap_ratio))

        # Calcular stride para cubrir la imagen
        stride_x = max(1, (width - self.base_patch_size) // max(1, grid_cols - 1)) if grid_cols > 1 else width
        stride_y = max(1, (height - self.base_patch_size) // max(1, grid_rows - 1)) if grid_rows > 1 else height

        return {
            'grid_cols': grid_cols,
            'grid_rows': grid_rows,
            'stride_x': stride_x,
            'stride_y': stride_y,
            'effective_patch_size': effective_patch_size,
            'total_patches': grid_cols * grid_rows
        }

    def _create_global_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create global thumbnail for context understanding."""
        new_width = int(image.width * self.global_context_scale)
        new_height = int(image.height * self.global_context_scale)

        # Ensure minimum size
        new_width = max(new_width, self.base_patch_size // 4)
        new_height = max(new_height, self.base_patch_size // 4)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _create_local_patches(
        self,
        image: Image.Image,
        patches_info: Dict[str, Any]
    ) -> List[Image.Image]:
        """Create local patches according to the computed strategy."""
        patches = []
        grid_cols = patches_info['grid_cols']
        grid_rows = patches_info['grid_rows']
        stride_x = patches_info['stride_x']
        stride_y = patches_info['stride_y']

        for row in range(grid_rows):
            for col in range(grid_cols):
                # Calcular posición del parche
                x = min(col * stride_x, image.width - self.base_patch_size)
                y = min(row * stride_y, image.height - self.base_patch_size)

                # Extraer parche
                patch = image.crop((
                    x,
                    y,
                    x + self.base_patch_size,
                    y + self.base_patch_size
                ))
                patches.append(patch)

        return patches


class ImageTokenizer:
    """
    Image Tokenizer: Converts processed images into visual tokens.

    Handles the conversion from image patches to token sequences that
    can be fed into the language model.
    """

    def __init__(self, max_visual_tokens: int = 256):
        self.max_visual_tokens = max_visual_tokens

    def tokenize_image(
        self,
        processed_image: Dict[str, Any],
        vision_encoder
    ) -> Dict[str, torch.Tensor]:
        """
        Tokenize processed image into visual tokens.

        Args:
            processed_image: Output from AnyResImageProcessor
            vision_encoder: VisionEncoder instance

        Returns:
            Dictionary with visual tokens and metadata
        """
        global_thumbnail = processed_image['global_thumbnail']
        local_patches = processed_image['local_patches']

        # Process global thumbnail
        global_features = vision_encoder.get_image_features(global_thumbnail)

        # Process local patches
        local_features_list = []
        for patch in local_patches:
            patch_features = vision_encoder.get_image_features(patch)
            local_features_list.append(patch_features)

        # Concatenate all features
        if local_features_list:
            all_features = torch.cat([global_features] + local_features_list, dim=0)
        else:
            all_features = global_features

        # Truncate if too many tokens
        if all_features.shape[0] > self.max_visual_tokens:
            all_features = all_features[:self.max_visual_tokens]

        return {
            'visual_tokens': all_features,
            'num_tokens': all_features.shape[0],
            'global_tokens': global_features.shape[0],
            'local_tokens': sum(f.shape[0] for f in local_features_list),
            'patches_info': processed_image['patches_info']
        }


def create_test_image_with_text(width: int = 800, height: int = 600) -> Image.Image:
    """
    Create a test image with text for document analysis testing.

    Args:
        width: Image width
        height: Image height

    Returns:
        PIL Image with sample text content
    """
    # Create white background
    img_array = np.full((height, width, 3), 255, dtype=np.uint8)

    # Add some colored rectangles to simulate document elements
    # Header
    img_array[0:80, :, :] = [240, 248, 255]  # Light blue header

    # Content areas
    img_array[100:200, 50:300, :] = [255, 250, 240]  # Light orange box
    img_array[250:350, 400:700, :] = [240, 255, 240]  # Light green box
    img_array[400:500, 100:600, :] = [255, 240, 245]  # Light pink box

    # Add some "text" lines (thin horizontal lines)
    for y in range(120, 180, 15):
        img_array[y:y+2, 70:280, :] = [100, 100, 100]  # Dark gray lines

    for y in range(270, 330, 15):
        img_array[y:y+2, 420:680, :] = [100, 100, 100]

    for y in range(420, 480, 15):
        img_array[y:y+2, 120:580, :] = [100, 100, 100]

    return Image.fromarray(img_array)


def test_anyres_processing():
    """Test AnyRes image processing."""
    print("🧪 Testing AnyRes Image Processing...")

    try:
        # Create processor
        processor = AnyResImageProcessor()
        tokenizer = ImageTokenizer()

        # Create test image
        test_image = create_test_image_with_text(800, 600)
        print(f"✅ Created test image: {test_image.size}")

        # Process with AnyRes
        processed = processor.process_image(test_image)
        print(f"✅ AnyRes processing: {processed['strategy']} strategy")
        print(f"   - Global thumbnail: {processed['global_thumbnail'].size}")
        print(f"   - Local patches: {len(processed['local_patches'])}")
        print(f"   - Grid: {processed['patches_info']['grid_cols']}x{processed['patches_info']['grid_rows']}")

        # Test with vision encoder (mock)
        class MockVisionEncoder:
            def get_image_features(self, img):
                # Mock: return random features
                num_patches = (img.width // 32) * (img.height // 32)
                return torch.randn(num_patches, 768)

        mock_encoder = MockVisionEncoder()
        tokens = tokenizer.tokenize_image(processed, mock_encoder)

        print(f"✅ Tokenization: {tokens['num_tokens']} visual tokens")
        print(f"   - Global: {tokens['global_tokens']}, Local: {tokens['local_tokens']}")

        print("✅ AnyRes processing test passed!")
        return True

    except Exception as e:
        print(f"❌ AnyRes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_anyres_processing()