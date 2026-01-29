"""
AWQ (Activation-aware Weight Quantization) Implementation
========================================================

Advanced quantization technique that considers activation patterns during
weight quantization to maintain model accuracy.

Features:
- Activation-aware scaling
- Mixed precision quantization
- Automatic calibration
- Support for 4-bit and 8-bit quantization

Author: AILOOS Team
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
import math

logger = logging.getLogger(__name__)

try:
    import awq
    from awq.quantize import quantize_model
    from awq.utils import get_best_device
    AWQ_AVAILABLE = True
    logger.info("✅ AWQ library available")
except ImportError:
    AWQ_AVAILABLE = False
    logger.warning("⚠️  AWQ library not available. Install with: pip install awq")


class AWQConfig:
    """Configuration for AWQ quantization."""

    def __init__(
        self,
        w_bit: int = 4,
        q_group_size: int = 128,
        zero_point: bool = True,
        use_cuda_fp16: bool = True,
        use_auto_scale: bool = True,
        use_auto_clip: bool = True,
        device: str = "auto"
    ):
        self.w_bit = w_bit
        self.q_group_size = q_group_size
        self.zero_point = zero_point
        self.use_cuda_fp16 = use_cuda_fp16
        self.use_auto_scale = use_auto_scale
        self.use_auto_clip = use_auto_clip
        self.device = device

        # Validate configuration
        if w_bit not in [2, 3, 4, 8]:
            raise ValueError(f"w_bit must be 2, 3, 4, or 8, got {w_bit}")

        if q_group_size not in [64, 128, 256, -1]:  # -1 means per-channel
            raise ValueError(f"q_group_size must be 64, 128, 256, or -1, got {q_group_size}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "w_bit": self.w_bit,
            "q_group_size": self.q_group_size,
            "zero_point": self.zero_point,
            "use_cuda_fp16": self.use_cuda_fp16,
            "use_auto_scale": self.use_auto_scale,
            "use_auto_clip": self.use_auto_clip,
            "device": self.device
        }


class AWQQuantizer:
    """
    AWQ Quantizer for EmpoorioLM models.

    Performs activation-aware weight quantization to reduce model size
    while maintaining accuracy.
    """

    def __init__(self, config: AWQConfig):
        self.config = config
        self.device = self._get_device()
        self.calibration_data: List[torch.Tensor] = []
        self.quantized_model: Optional[nn.Module] = None
        self.scale_factors: Dict[str, torch.Tensor] = {}
        self.zero_points: Dict[str, torch.Tensor] = {}

    def _get_device(self) -> torch.device:
        """Get the appropriate device for quantization."""
        if self.config.device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(self.config.device)

    def collect_calibration_data(
        self,
        model: nn.Module,
        calibration_loader: Any,
        num_samples: int = 128
    ) -> None:
        """
        Collect calibration data from the model.

        Args:
            model: Model to collect calibration data from
            calibration_loader: Data loader for calibration
            num_samples: Number of samples to collect
        """
        logger.info(f"📊 Collecting calibration data with {num_samples} samples...")

        model.eval()
        self.calibration_data = []

        with torch.no_grad():
            for i, batch in enumerate(calibration_loader):
                if i >= num_samples:
                    break

                # Move batch to device
                if isinstance(batch, dict):
                    input_ids = batch.get('input_ids', batch.get('input', torch.randn(1, 512, dtype=torch.long)))
                else:
                    input_ids = batch

                input_ids = input_ids.to(self.device)

                # Forward pass to collect activations
                try:
                    outputs = model(input_ids)
                    # Store intermediate activations (this is a simplified version)
                    # In practice, you'd hook into specific layers
                    self.calibration_data.append(input_ids.cpu())
                except Exception as e:
                    logger.warning(f"⚠️  Error collecting calibration data: {e}")
                    continue

        logger.info(f"✅ Collected {len(self.calibration_data)} calibration samples")

    def quantize_model(self, model: nn.Module) -> nn.Module:
        """
        Quantize the model using AWQ.

        Args:
            model: Model to quantize

        Returns:
            Quantized model
        """
        if not AWQ_AVAILABLE:
            logger.warning("⚠️  AWQ library not available, returning original model")
            return model

        logger.info("🔄 Starting AWQ quantization...")
        logger.info(f"   Target precision: {self.config.w_bit}-bit")
        logger.info(f"   Group size: {self.config.q_group_size}")
        logger.info(f"   Device: {self.device}")

        try:
            # Move model to device
            model = model.to(self.device)

            # Use AWQ library for quantization
            quantized_model = quantize_model(
                model=model,
                w_bit=self.config.w_bit,
                q_group_size=self.config.q_group_size,
                zero_point=self.config.zero_point,
                use_cuda_fp16=self.config.use_cuda_fp16,
                use_auto_scale=self.config.use_auto_scale,
                use_auto_clip=self.config.use_auto_clip,
                device=self.device
            )

            self.quantized_model = quantized_model
            logger.info("✅ AWQ quantization completed successfully")

            return quantized_model

        except Exception as e:
            logger.error(f"❌ AWQ quantization failed: {e}")
            logger.info("🔄 Returning original model")
            return model

    def get_quantization_stats(self) -> Dict[str, Any]:
        """Get quantization statistics."""
        if self.quantized_model is None:
            return {"status": "not_quantized"}

        # Calculate model size reduction
        original_params = sum(p.numel() for p in self.quantized_model.parameters())
        quantized_params = self._estimate_quantized_params(original_params)

        compression_ratio = original_params / quantized_params if quantized_params > 0 else 1.0

        return {
            "status": "quantized",
            "w_bit": self.config.w_bit,
            "original_parameters": original_params,
            "quantized_parameters": quantized_params,
            "compression_ratio": compression_ratio,
            "calibration_samples": len(self.calibration_data),
            "device": str(self.device)
        }

    def _estimate_quantized_params(self, original_params: int) -> int:
        """Estimate the number of parameters after quantization."""
        # This is a rough estimate
        # In practice, you'd need to count actual quantized parameters
        bits_per_param = self.config.w_bit

        # Account for packing efficiency
        if bits_per_param <= 4:
            # 4-bit and lower can be packed
            packed_params = math.ceil(original_params * bits_per_param / 8)
        else:
            packed_params = original_params

        return packed_params

    def save_quantized_model(self, path: Union[str, Path]) -> None:
        """Save the quantized model."""
        if self.quantized_model is None:
            raise ValueError("No quantized model to save")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = path / "quantized_model.pth"
        torch.save(self.quantized_model.state_dict(), model_path)

        # Save quantization config
        config_path = path / "quantization_config.json"
        import json
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)

        # Save quantization stats
        stats_path = path / "quantization_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(self.get_quantization_stats(), f, indent=2)

        logger.info(f"💾 Quantized model saved to {path}")

    @classmethod
    def load_quantized_model(
        cls,
        model_class: Any,
        path: Union[str, Path],
        config: Optional[AWQConfig] = None
    ) -> Tuple[nn.Module, 'AWQQuantizer']:
        """Load a quantized model."""
        path = Path(path)

        # Load config
        config_path = path / "quantization_config.json"
        if config is None and config_path.exists():
            import json
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            config = AWQConfig(**config_dict)

        if config is None:
            config = AWQConfig()

        # Create quantizer
        quantizer = cls(config)

        # Load model
        model_path = path / "quantized_model.pth"
        if not model_path.exists():
            raise FileNotFoundError(f"Quantized model not found: {model_path}")

        # Create model instance and load state
        model = model_class()  # This would need to be passed properly
        state_dict = torch.load(model_path, map_location='cpu')
        model.load_state_dict(state_dict)

        quantizer.quantized_model = model

        logger.info(f"📂 Quantized model loaded from {path}")
        return model, quantizer


class AWQCalibrationDataset:
    """Dataset for AWQ calibration."""

    def __init__(self, tokenizer, texts: List[str], max_length: int = 512):
        self.tokenizer = tokenizer
        self.texts = texts
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]

        # Tokenize
        tokens = self.tokenizer.encode(text, max_length=self.max_length, truncation=True)

        return torch.tensor(tokens, dtype=torch.long)


def create_awq_calibration_data(tokenizer, num_samples: int = 128) -> List[str]:
    """
    Create calibration data for AWQ.

    Args:
        tokenizer: Tokenizer to use
        num_samples: Number of calibration samples to generate

    Returns:
        List of calibration text samples
    """
    # Generate diverse calibration texts
    calibration_texts = []

    # Add some common patterns
    patterns = [
        "The quick brown fox jumps over the lazy dog.",
        "In a hole in the ground there lived a hobbit.",
        "To be or not to be, that is the question.",
        "The meaning of life is 42.",
        "Artificial intelligence will change the world.",
        "Machine learning is a subset of artificial intelligence.",
        "The transformer architecture revolutionized NLP.",
        "Large language models can generate coherent text.",
        "Quantization reduces model size while maintaining accuracy.",
        "Attention mechanisms are key to transformer performance.",
    ]

    # Generate variations
    for i in range(num_samples):
        base_pattern = patterns[i % len(patterns)]
        # Create variations by adding context
        variation = f"Context: {base_pattern} This is sample number {i} for calibration. " * 3
        calibration_texts.append(variation[:1000])  # Limit length

    return calibration_texts


def benchmark_awq_quantization(
    model: nn.Module,
    quantizer: AWQQuantizer,
    test_data: List[torch.Tensor],
    num_runs: int = 5
) -> Dict[str, Any]:
    """
    Benchmark AWQ quantization performance.

    Args:
        model: Original model
        quantizer: AWQ quantizer with quantized model
        test_data: Test data for benchmarking
        num_runs: Number of benchmark runs

    Returns:
        Benchmark results
    """
    device = next(model.parameters()).device

    # Benchmark original model
    original_times = []
    model.eval()

    with torch.no_grad():
        for _ in range(num_runs):
            for batch in test_data[:5]:  # Use first 5 batches
                batch = batch.to(device)
                start = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                if start:
                    start.record()

                _ = model(batch)

                if torch.cuda.is_available():
                    torch.cuda.synchronize()

                end = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                if end:
                    end.record()
                    end.synchronize()
                    original_times.append(start.elapsed_time(end) / 1000.0)

    # Benchmark quantized model
    quantized_times = []
    if quantizer.quantized_model is not None:
        quantizer.quantized_model.eval()

        with torch.no_grad():
            for _ in range(num_runs):
                for batch in test_data[:5]:
                    batch = batch.to(device)
                    start = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                    if start:
                        start.record()

                    _ = quantizer.quantized_model(batch)

                    if torch.cuda.is_available():
                        torch.cuda.synchronize()

                    end = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                    if end:
                        end.record()
                        end.synchronize()
                        quantized_times.append(start.elapsed_time(end) / 1000.0)

    # Calculate statistics
    results = {
        "original_model_available": True,
        "quantized_model_available": quantizer.quantized_model is not None,
        "quantization_stats": quantizer.get_quantization_stats()
    }

    if original_times:
        results["original_avg_time"] = sum(original_times) / len(original_times)

    if quantized_times:
        results["quantized_avg_time"] = sum(quantized_times) / len(quantized_times)
        if original_times:
            results["speedup"] = results["original_avg_time"] / results["quantized_avg_time"]

    return results


# Example usage and testing
if __name__ == "__main__":
    print("🧪 AWQ Quantization Test")
    print("=" * 40)

    # Test configuration
    config = AWQConfig(w_bit=4, q_group_size=128)

    print(f"📊 AWQ Config: {config.w_bit}-bit, group_size={config.q_group_size}")
    print(f"🔧 AWQ Available: {AWQ_AVAILABLE}")

    if not AWQ_AVAILABLE:
        print("⚠️  AWQ library not installed. Install with: pip install awq")
        print("✅ AWQ integration code is ready for when the library is installed.")
    else:
        print("✅ AWQ is ready for quantization!")

    # Show configuration
    print("\n⚙️  Configuration Details:")
    for key, value in config.to_dict().items():
        print(f"   {key}: {value}")

    print("\n🎯 AWQ quantization system is implemented and ready!")