import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Union, Callable, Tuple
import logging
import copy

logger = logging.getLogger(__name__)

class DistillationLoss(nn.Module):
    """
    Custom distillation loss combining hard and soft targets.
    """

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5):
        """
        Initialize distillation loss.

        Args:
            temperature: Temperature for softening probabilities
            alpha: Weight for distillation loss vs hard loss
        """
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, student_logits: torch.Tensor, teacher_logits: torch.Tensor,
                targets: torch.Tensor) -> torch.Tensor:
        """
        Compute distillation loss.

        Args:
            student_logits: Student model outputs
            teacher_logits: Teacher model outputs
            targets: Ground truth labels

        Returns:
            Combined loss
        """
        # Hard loss (cross-entropy with ground truth)
        hard_loss = self.criterion(student_logits, targets)

        # Soft loss (KL divergence between softened predictions)
        teacher_probs = F.softmax(teacher_logits / self.temperature, dim=1)
        student_probs = F.log_softmax(student_logits / self.temperature, dim=1)
        soft_loss = F.kl_div(student_probs, teacher_probs, reduction='batchmean') * (self.temperature ** 2)

        # Combined loss
        loss = self.alpha * soft_loss + (1 - self.alpha) * hard_loss
        return loss

class DistillationEngine:
    """
    Knowledge distillation engine for transferring knowledge from teacher to student models.
    Supports response-based, feature-based, and relation-based distillation.
    """

    def __init__(self, teacher_model: nn.Module, student_model: nn.Module):
        """
        Initialize the distillation engine.

        Args:
            teacher_model: Pre-trained teacher model
            student_model: Student model to be trained
        """
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.distillation_history = []
        self.feature_hooks = {}

    def response_distillation(self, train_loader: torch.utils.data.DataLoader,
                            optimizer: torch.optim.Optimizer,
                            epochs: int = 10, temperature: float = 2.0,
                            alpha: float = 0.5, device: str = 'cpu') -> nn.Module:
        """
        Perform response-based distillation (logit distillation).

        Args:
            train_loader: Training data loader
            optimizer: Optimizer for student model
            epochs: Number of distillation epochs
            temperature: Temperature for softening
            alpha: Distillation loss weight
            device: Device to run on

        Returns:
            Distilled student model
        """
        logger.info(f"Starting response-based distillation for {epochs} epochs")

        self.teacher_model.to(device).eval()
        self.student_model.to(device).train()

        criterion = DistillationLoss(temperature=temperature, alpha=alpha)

        for epoch in range(epochs):
            epoch_loss = 0.0
            for inputs, targets in train_loader:
                inputs, targets = inputs.to(device), targets.to(device)

                optimizer.zero_grad()

                # Teacher forward pass
                with torch.no_grad():
                    teacher_logits = self.teacher_model(inputs)

                # Student forward pass
                student_logits = self.student_model(inputs)

                # Compute distillation loss
                loss = criterion(student_logits, teacher_logits, targets)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        self.distillation_history.append({
            'method': 'response',
            'epochs': epochs,
            'temperature': temperature,
            'alpha': alpha,
            'final_loss': avg_loss
        })

        return self.student_model

    def feature_distillation(self, train_loader: torch.utils.data.DataLoader,
                           optimizer: torch.optim.Optimizer,
                           teacher_layers: List[str], student_layers: List[str],
                           epochs: int = 10, feature_weight: float = 0.5,
                           device: str = 'cpu') -> nn.Module:
        """
        Perform feature-based distillation using intermediate features.

        Args:
            train_loader: Training data loader
            optimizer: Optimizer for student model
            teacher_layers: Names of teacher layers to distill from
            student_layers: Names of student layers to distill to
            epochs: Number of distillation epochs
            feature_weight: Weight for feature distillation loss
            device: Device to run on

        Returns:
            Distilled student model
        """
        logger.info(f"Starting feature-based distillation for {epochs} epochs")

        self.teacher_model.to(device).eval()
        self.student_model.to(device).train()

        # Register hooks to capture intermediate features
        teacher_features = {}
        student_features = {}

        def get_hook(storage_dict, layer_name):
            def hook(module, input, output):
                storage_dict[layer_name] = output.detach()
            return hook

        # Register hooks
        for layer_name in teacher_layers:
            layer = dict(self.teacher_model.named_modules())[layer_name]
            layer.register_forward_hook(get_hook(teacher_features, layer_name))

        for layer_name in student_layers:
            layer = dict(self.student_model.named_modules())[layer_name]
            layer.register_forward_hook(get_hook(student_features, layer_name))

        criterion_ce = nn.CrossEntropyLoss()
        criterion_mse = nn.MSELoss()

        for epoch in range(epochs):
            epoch_loss = 0.0
            for inputs, targets in train_loader:
                inputs, targets = inputs.to(device), targets.to(device)

                optimizer.zero_grad()

                # Forward passes
                with torch.no_grad():
                    _ = self.teacher_model(inputs)
                student_logits = self.student_model(inputs)

                # Task loss
                task_loss = criterion_ce(student_logits, targets)

                # Feature distillation loss
                feature_loss = 0.0
                for t_layer, s_layer in zip(teacher_layers, student_layers):
                    if t_layer in teacher_features and s_layer in student_features:
                        t_feat = teacher_features[t_layer]
                        s_feat = student_features[s_layer]
                        # Align feature dimensions if needed
                        if t_feat.shape != s_feat.shape:
                            # Simple pooling to match dimensions
                            if len(t_feat.shape) > len(s_feat.shape):
                                t_feat = F.adaptive_avg_pool2d(t_feat, s_feat.shape[2:])
                            elif len(s_feat.shape) > len(t_feat.shape):
                                s_feat = F.adaptive_avg_pool2d(s_feat, t_feat.shape[2:])
                        feature_loss += criterion_mse(s_feat, t_feat)

                # Combined loss
                loss = task_loss + feature_weight * feature_loss
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        self.distillation_history.append({
            'method': 'feature',
            'epochs': epochs,
            'teacher_layers': teacher_layers,
            'student_layers': student_layers,
            'feature_weight': feature_weight,
            'final_loss': avg_loss
        })

        return self.student_model

    def relation_distillation(self, train_loader: torch.utils.data.DataLoader,
                            optimizer: torch.optim.Optimizer,
                            epochs: int = 10, relation_weight: float = 0.5,
                            device: str = 'cpu') -> nn.Module:
        """
        Perform relation-based distillation preserving feature relationships.

        Args:
            train_loader: Training data loader
            optimizer: Optimizer for student model
            epochs: Number of distillation epochs
            relation_weight: Weight for relation distillation loss
            device: Device to run on

        Returns:
            Distilled student model
        """
        logger.info(f"Starting relation-based distillation for {epochs} epochs")

        self.teacher_model.to(device).eval()
        self.student_model.to(device).train()

        criterion_ce = nn.CrossEntropyLoss()
        criterion_mse = nn.MSELoss()

        for epoch in range(epochs):
            epoch_loss = 0.0
            for inputs, targets in train_loader:
                inputs, targets = inputs.to(device), targets.to(device)

                optimizer.zero_grad()

                # Get features from both models
                with torch.no_grad():
                    teacher_features = self._get_features(self.teacher_model, inputs)
                student_features = self._get_features(self.student_model, inputs)

                # Task loss
                student_logits = self.student_model(inputs)
                task_loss = criterion_ce(student_logits, targets)

                # Relation distillation loss (FSP matrix)
                relation_loss = 0.0
                for t_feat, s_feat in zip(teacher_features, student_features):
                    if len(teacher_features) > 1 and len(student_features) > 1:
                        # Compute FSP matrices
                        t_fsp = self._compute_fsp_matrix(t_feat, teacher_features[teacher_features.index(t_feat) + 1])
                        s_fsp = self._compute_fsp_matrix(s_feat, student_features[student_features.index(s_feat) + 1])
                        relation_loss += criterion_mse(s_fsp, t_fsp)

                # Combined loss
                loss = task_loss + relation_weight * relation_loss
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        self.distillation_history.append({
            'method': 'relation',
            'epochs': epochs,
            'relation_weight': relation_weight,
            'final_loss': avg_loss
        })

        return self.student_model

    def _get_features(self, model: nn.Module, inputs: torch.Tensor) -> List[torch.Tensor]:
        """
        Extract intermediate features from model.

        Args:
            model: Model to extract features from
            inputs: Input tensor

        Returns:
            List of feature tensors
        """
        features = []
        x = inputs

        for name, module in model.named_children():
            x = module(x)
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                features.append(x)

        return features

    def _compute_fsp_matrix(self, feat1: torch.Tensor, feat2: torch.Tensor) -> torch.Tensor:
        """
        Compute Flow of Solution Procedure (FSP) matrix.

        Args:
            feat1: First feature map
            feat2: Second feature map

        Returns:
            FSP matrix
        """
        # Reshape features to (batch, channels, hw)
        if len(feat1.shape) == 4:  # Conv features
            b1, c1, h1, w1 = feat1.shape
            feat1 = feat1.view(b1, c1, -1)
        if len(feat2.shape) == 4:
            b2, c2, h2, w2 = feat2.shape
            feat2 = feat2.view(b2, c2, -1)

        # Compute FSP matrix: correlation between channels
        fsp = torch.matmul(feat1.transpose(1, 2), feat2) / feat1.shape[-1]
        return fsp.mean(dim=0)  # Average over batch

    def evaluate_distillation(self, test_loader: torch.utils.data.DataLoader,
                            device: str = 'cpu') -> Dict:
        """
        Evaluate the distilled student model.

        Args:
            test_loader: Test data loader
            device: Device to run on

        Returns:
            Evaluation metrics
        """
        self.student_model.to(device).eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in test_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = self.student_model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += targets.size(0)
                correct += (predicted == targets).sum().item()

        accuracy = 100 * correct / total

        return {
            'accuracy': accuracy,
            'distillation_history': self.distillation_history
        }

    def save_distilled_model(self, path: str) -> None:
        """
        Save the distilled student model.

        Args:
            path: Path to save the model
        """
        torch.save({
            'student_state_dict': self.student_model.state_dict(),
            'distillation_history': self.distillation_history
        }, path)
        logger.info(f"Distilled model saved to {path}")

    def load_distilled_model(self, path: str) -> nn.Module:
        """
        Load a distilled model.

        Args:
            path: Path to load from

        Returns:
            Loaded student model
        """
        checkpoint = torch.load(path)
        self.student_model.load_state_dict(checkpoint['student_state_dict'])
        self.distillation_history = checkpoint.get('distillation_history', [])
        logger.info(f"Distilled model loaded from {path}")
        return self.student_model