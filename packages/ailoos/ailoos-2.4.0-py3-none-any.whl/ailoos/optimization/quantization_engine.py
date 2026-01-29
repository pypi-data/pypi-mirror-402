import torch
import torch.nn as nn
from torch.quantization import QuantStub, DeQuantStub, prepare, convert
from torch.quantization import prepare_qat, quantize_qat
import torch.quantization as quant
from typing import Dict, List, Optional, Union, Callable
import logging
import copy

logger = logging.getLogger(__name__)

class QuantizationEngine:
    """
    Advanced quantization engine supporting INT8, FP16, and dynamic quantization.
    Includes quantization-aware training (QAT) capabilities.
    """

    def __init__(self, model: nn.Module):
        """
        Initialize the quantization engine with a PyTorch model.

        Args:
            model: The PyTorch model to be quantized
        """
        self.original_model = model
        self.quantized_model = None
        self.qconfig = None
        self.quantization_history = []

    def set_qconfig(self, qconfig_name: str = 'default') -> None:
        """
        Set the quantization configuration.

        Args:
            qconfig_name: Name of the quantization config ('default', 'fbgemm', 'qnnpack', 'custom')
        """
        if qconfig_name == 'default':
            self.qconfig = quant.default_qconfig
        elif qconfig_name == 'fbgemm':
            self.qconfig = quant.get_default_qconfig('fbgemm')
        elif qconfig_name == 'qnnpack':
            self.qconfig = quant.get_default_qconfig('qnnpack')
        elif qconfig_name == 'custom':
            # Custom config for higher precision
            self.qconfig = quant.QConfig(
                activation=quant.MinMaxObserver.with_args(dtype=torch.quint8),
                weight=quant.MinMaxObserver.with_args(dtype=torch.qint8)
            )
        else:
            raise ValueError(f"Unsupported qconfig: {qconfig_name}")

        logger.info(f"Set quantization config to {qconfig_name}")

    def dynamic_quantization(self, dtype: torch.dtype = torch.qint8) -> nn.Module:
        """
        Apply dynamic quantization to the model.

        Args:
            dtype: Quantization dtype (torch.qint8 or torch.float16)

        Returns:
            Dynamically quantized model
        """
        logger.info(f"Applying dynamic quantization with dtype {dtype}")

        # Dynamic quantization works best for LSTM, RNN, and linear layers
        qconfig_spec = {nn.Linear: dtype, nn.LSTM: dtype, nn.RNN: dtype}
        self.quantized_model = torch.ao.quantization.quantize_dynamic(
            self.original_model, qconfig_spec, dtype=dtype
        )

        self.quantization_history.append({
            'method': 'dynamic',
            'dtype': str(dtype),
            'qconfig': None
        })

        return self.quantized_model

    def static_quantization(self, calibration_data: torch.utils.data.DataLoader,
                           qconfig_name: str = 'default') -> nn.Module:
        """
        Apply static quantization with calibration.

        Args:
            calibration_data: DataLoader for calibration
            qconfig_name: Quantization config name

        Returns:
            Statically quantized model
        """
        logger.info(f"Applying static quantization with config {qconfig_name}")

        # Set qconfig
        self.set_qconfig(qconfig_name)

        # Prepare model for quantization
        model_to_quantize = copy.deepcopy(self.original_model)

        # Fuse layers if possible (Conv + BN + ReLU)
        model_to_quantize = self._fuse_layers(model_to_quantize)

        # Add quantization stubs
        model_to_quantize = self._add_quant_stubs(model_to_quantize)

        # Prepare for quantization
        model_to_quantize.qconfig = self.qconfig
        prepare(model_to_quantize, inplace=True)

        # Calibrate with data
        self._calibrate(model_to_quantize, calibration_data)

        # Convert to quantized model
        self.quantized_model = convert(model_to_quantize, inplace=True)

        self.quantization_history.append({
            'method': 'static',
            'qconfig': qconfig_name,
            'calibration_samples': len(calibration_data.dataset) if hasattr(calibration_data, 'dataset') else 'unknown'
        })

        return self.quantized_model

    def quantization_aware_training(self, qconfig_name: str = 'default') -> nn.Module:
        """
        Prepare model for quantization-aware training (QAT).

        Args:
            qconfig_name: Quantization config name

        Returns:
            Model prepared for QAT
        """
        logger.info(f"Preparing model for quantization-aware training with config {qconfig_name}")

        # Set qconfig
        self.set_qconfig(qconfig_name)

        # Prepare model for QAT
        model_qat = copy.deepcopy(self.original_model)

        # Fuse layers
        model_qat = self._fuse_layers(model_qat)

        # Add quantization stubs
        model_qat = self._add_quant_stubs(model_qat)

        # Prepare for QAT
        model_qat.qconfig = self.qconfig
        prepare_qat(model_qat, inplace=True)

        self.quantization_history.append({
            'method': 'qat_prepared',
            'qconfig': qconfig_name
        })

        return model_qat

    def convert_qat_model(self, qat_model: nn.Module) -> nn.Module:
        """
        Convert a QAT-trained model to quantized model.

        Args:
            qat_model: QAT-trained model

        Returns:
            Quantized model
        """
        logger.info("Converting QAT model to quantized model")

        self.quantized_model = quantize_qat(qat_model, inplace=True)

        self.quantization_history.append({
            'method': 'qat_converted'
        })

        return self.quantized_model

    def fp16_quantization(self) -> nn.Module:
        """
        Convert model to FP16 (half precision).

        Returns:
            FP16 model
        """
        logger.info("Converting model to FP16")

        self.quantized_model = copy.deepcopy(self.original_model).half()

        self.quantization_history.append({
            'method': 'fp16'
        })

        return self.quantized_model

    def _fuse_layers(self, model: nn.Module) -> nn.Module:
        """
        Fuse Conv2d + BatchNorm2d + ReLU layers for better quantization.

        Args:
            model: Model to fuse layers in

        Returns:
            Model with fused layers
        """
        fused_modules = []
        for name, module in model.named_modules():
            if isinstance(module, nn.Sequential):
                # Look for Conv2d -> BatchNorm2d -> ReLU pattern
                layers = list(module.children())
                for i in range(len(layers) - 2):
                    if (isinstance(layers[i], nn.Conv2d) and
                        isinstance(layers[i+1], nn.BatchNorm2d) and
                        isinstance(layers[i+2], nn.ReLU)):
                        fused_modules.append([f"{name}.{i}", f"{name}.{i+1}", f"{name}.{i+2}"])

        if fused_modules:
            torch.quantization.fuse_modules(model, fused_modules, inplace=True)
            logger.info(f"Fused {len(fused_modules)} layer groups")

        return model

    def _add_quant_stubs(self, model: nn.Module) -> nn.Module:
        """
        Add QuantStub and DeQuantStub to the model.

        Args:
            model: Model to add stubs to

        Returns:
            Model with quantization stubs
        """
        # Add QuantStub at the beginning
        model.quant = QuantStub()

        # Add DeQuantStub at the end (for models with single output)
        if hasattr(model, 'fc') or hasattr(model, 'classifier'):
            model.dequant = DeQuantStub()
        else:
            # For models with multiple outputs, add dequant stubs as needed
            pass

        return model

    def _calibrate(self, model: nn.Module, calibration_data: torch.utils.data.DataLoader) -> None:
        """
        Calibrate the quantized model with calibration data.

        Args:
            model: Model to calibrate
            calibration_data: Calibration data loader
        """
        model.eval()
        with torch.no_grad():
            for i, (inputs, _) in enumerate(calibration_data):
                if i >= 100:  # Limit calibration samples
                    break
                if isinstance(inputs, torch.Tensor):
                    model(inputs)
                elif isinstance(inputs, (list, tuple)):
                    model(*inputs)

        logger.info("Calibration completed")

    def get_quantization_stats(self) -> Dict:
        """
        Get statistics about the quantized model.

        Returns:
            Dictionary with quantization statistics
        """
        if self.quantized_model is None:
            return {'status': 'not_quantized'}

        total_params = sum(p.numel() for p in self.quantized_model.parameters())
        quantized_params = 0

        for name, module in self.quantized_model.named_modules():
            if hasattr(module, 'weight') and hasattr(module.weight, 'dtype'):
                if module.weight.dtype in [torch.qint8, torch.quint8]:
                    quantized_params += module.weight.numel()

        compression_ratio = quantized_params / total_params if total_params > 0 else 0

        return {
            'total_parameters': total_params,
            'quantized_parameters': quantized_params,
            'compression_ratio': compression_ratio,
            'quantization_history': self.quantization_history
        }

    def save_quantized_model(self, path: str) -> None:
        """
        Save the quantized model to disk.

        Args:
            path: Path to save the model
        """
        if self.quantized_model is None:
            raise ValueError("No quantized model to save")

        torch.save({
            'model_state_dict': self.quantized_model.state_dict(),
            'quantization_history': self.quantization_history,
            'quantization_stats': self.get_quantization_stats()
        }, path)
        logger.info(f"Quantized model saved to {path}")

    def load_quantized_model(self, path: str, model_class: Callable) -> nn.Module:
        """
        Load a quantized model from disk.

        Args:
            path: Path to load the model from
            model_class: Model class to instantiate

        Returns:
            Loaded quantized model
        """
        checkpoint = torch.load(path)
        self.quantized_model = model_class()
        self.quantized_model.load_state_dict(checkpoint['model_state_dict'])
        self.quantization_history = checkpoint.get('quantization_history', [])
        logger.info(f"Quantized model loaded from {path}")
        return self.quantized_model