import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
from typing import Dict, List, Optional, Union, Callable
import logging

logger = logging.getLogger(__name__)

class PruningEngine:
    """
    Intelligent pruning engine with multiple pruning strategies for model optimization.
    Supports magnitude-based, structured, and custom pruning techniques.
    """

    def __init__(self, model: nn.Module):
        """
        Initialize the pruning engine with a PyTorch model.

        Args:
            model: The PyTorch model to be pruned
        """
        self.model = model
        self.pruned_modules = {}
        self.pruning_history = []

    def magnitude_pruning(self, amount: float = 0.2, method: str = 'l1_unstructured') -> nn.Module:
        """
        Apply magnitude-based pruning to the model.

        Args:
            amount: Fraction of weights to prune (0.0 to 1.0)
            method: Pruning method ('l1_unstructured', 'l2_unstructured', 'random_unstructured')

        Returns:
            Pruned model
        """
        logger.info(f"Applying magnitude pruning with method {method} and amount {amount}")

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                if method == 'l1_unstructured':
                    prune.l1_unstructured(module, name='weight', amount=amount)
                elif method == 'l2_unstructured':
                    prune.l2_unstructured(module, name='weight', amount=amount)
                elif method == 'random_unstructured':
                    prune.random_unstructured(module, name='weight', amount=amount)
                else:
                    raise ValueError(f"Unsupported pruning method: {method}")

                self.pruned_modules[name] = module
                self.pruning_history.append({
                    'layer': name,
                    'method': method,
                    'amount': amount,
                    'type': 'magnitude'
                })

        return self.model

    def structured_pruning(self, amount: float = 0.2, dim: int = 0) -> nn.Module:
        """
        Apply structured pruning (prune entire channels/filters).

        Args:
            amount: Fraction of channels/filters to prune
            dim: Dimension to prune (0 for output channels, 1 for input channels)

        Returns:
            Pruned model
        """
        logger.info(f"Applying structured pruning with amount {amount} on dim {dim}")

        for name, module in self.model.named_modules():
            if isinstance(module, nn.Conv2d):
                prune.ln_structured(module, name='weight', amount=amount, n=1, dim=dim)
                self.pruned_modules[name] = module
                self.pruning_history.append({
                    'layer': name,
                    'method': 'ln_structured',
                    'amount': amount,
                    'dim': dim,
                    'type': 'structured'
                })

        return self.model

    def global_pruning(self, amount: float = 0.2, method: str = 'l1_unstructured') -> nn.Module:
        """
        Apply global pruning across all prunable parameters.

        Args:
            amount: Global fraction of weights to prune
            method: Pruning method

        Returns:
            Pruned model
        """
        logger.info(f"Applying global pruning with method {method} and amount {amount}")

        parameters_to_prune = []
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                parameters_to_prune.append((module, 'weight'))

        if method == 'l1_unstructured':
            prune.global_unstructured(parameters_to_prune, pruning_method=prune.L1Unstructured, amount=amount)
        elif method == 'l2_unstructured':
            prune.global_unstructured(parameters_to_prune, pruning_method=prune.L2Unstructured, amount=amount)
        else:
            raise ValueError(f"Unsupported global pruning method: {method}")

        for module, _ in parameters_to_prune:
            self.pruned_modules[str(module)] = module

        self.pruning_history.append({
            'method': f'global_{method}',
            'amount': amount,
            'type': 'global'
        })

        return self.model

    def iterative_pruning(self, initial_amount: float = 0.1, final_amount: float = 0.5,
                         iterations: int = 5, method: str = 'l1_unstructured') -> nn.Module:
        """
        Apply iterative pruning with increasing sparsity.

        Args:
            initial_amount: Starting pruning amount
            final_amount: Final pruning amount
            iterations: Number of pruning iterations
            method: Pruning method

        Returns:
            Iteratively pruned model
        """
        logger.info(f"Applying iterative pruning from {initial_amount} to {final_amount} over {iterations} iterations")

        amount_step = (final_amount - initial_amount) / (iterations - 1)

        for i in range(iterations):
            current_amount = initial_amount + i * amount_step
            self.magnitude_pruning(amount=current_amount, method=method)

            # Optional: Fine-tune here (placeholder for training)
            logger.info(f"Iteration {i+1}/{iterations}: Pruned {current_amount:.2%}")

        return self.model

    def remove_pruning(self, reparametrize: bool = True) -> nn.Module:
        """
        Remove pruning reparameterization from the model.

        Args:
            reparametrize: Whether to make pruning permanent

        Returns:
            Model with pruning removed
        """
        logger.info("Removing pruning reparameterization")

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                try:
                    prune.remove(module, 'weight')
                except ValueError:
                    pass  # Module might not be pruned

        self.pruned_modules.clear()
        return self.model

    def get_pruning_stats(self) -> Dict:
        """
        Get statistics about the current pruning state.

        Returns:
            Dictionary with pruning statistics
        """
        total_params = 0
        pruned_params = 0

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                weight = module.weight
                mask = getattr(module, 'weight_mask', torch.ones_like(weight))
                total_params += weight.numel()
                pruned_params += (mask == 0).sum().item()

        sparsity = pruned_params / total_params if total_params > 0 else 0

        return {
            'total_parameters': total_params,
            'pruned_parameters': pruned_params,
            'sparsity': sparsity,
            'pruning_history': self.pruning_history
        }

    def save_pruned_model(self, path: str) -> None:
        """
        Save the pruned model to disk.

        Args:
            path: Path to save the model
        """
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'pruning_history': self.pruning_history,
            'pruning_stats': self.get_pruning_stats()
        }, path)
        logger.info(f"Pruned model saved to {path}")

    def load_pruned_model(self, path: str) -> nn.Module:
        """
        Load a pruned model from disk.

        Args:
            path: Path to load the model from

        Returns:
            Loaded pruned model
        """
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.pruning_history = checkpoint.get('pruning_history', [])
        logger.info(f"Pruned model loaded from {path}")
        return self.model