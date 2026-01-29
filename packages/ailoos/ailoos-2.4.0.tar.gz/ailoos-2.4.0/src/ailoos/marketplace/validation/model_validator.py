import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import logging
import json
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import time
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccuracyTest:
    def __init__(self, model: nn.Module, test_data: DataLoader, device: str = 'cpu'):
        self.model = model.to(device)
        self.test_data = test_data
        self.device = device

    def run_test(self) -> Dict[str, Any]:
        try:
            self.model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for inputs, labels in self.test_data:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    outputs = self.model(inputs)
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            accuracy = correct / total
            logger.info(f"Accuracy test completed: {accuracy:.4f}")
            return {"accuracy": accuracy, "status": "passed"}
        except Exception as e:
            logger.error(f"Accuracy test failed: {str(e)}")
            return {"accuracy": 0.0, "status": "failed", "error": str(e)}

class RobustnessTest:
    def __init__(self, model: nn.Module, test_data: DataLoader, device: str = 'cpu', noise_std: float = 0.1):
        self.model = model.to(device)
        self.test_data = test_data
        self.device = device
        self.noise_std = noise_std

    def run_test(self) -> Dict[str, Any]:
        try:
            self.model.eval()
            original_correct = 0
            robust_correct = 0
            total = 0
            with torch.no_grad():
                for inputs, labels in self.test_data:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    # Original
                    outputs = self.model(inputs)
                    _, predicted = torch.max(outputs.data, 1)
                    original_correct += (predicted == labels).sum().item()

                    # With noise
                    noisy_inputs = inputs + torch.randn_like(inputs) * self.noise_std
                    outputs = self.model(noisy_inputs)
                    _, predicted = torch.max(outputs.data, 1)
                    robust_correct += (predicted == labels).sum().item()

                    total += labels.size(0)
            original_acc = original_correct / total
            robust_acc = robust_correct / total
            robustness_score = robust_acc / original_acc if original_acc > 0 else 0
            logger.info(f"Robustness test completed: {robustness_score:.4f}")
            return {"robustness_score": robustness_score, "status": "passed" if robustness_score > 0.8 else "warning"}
        except Exception as e:
            logger.error(f"Robustness test failed: {str(e)}")
            return {"robustness_score": 0.0, "status": "failed", "error": str(e)}

class FairnessTest:
    def __init__(self, model: nn.Module, test_data: DataLoader, sensitive_attr: torch.Tensor, device: str = 'cpu'):
        self.model = model.to(device)
        self.test_data = test_data
        self.sensitive_attr = sensitive_attr
        self.device = device

    def run_test(self) -> Dict[str, Any]:
        try:
            self.model.eval()
            group_accuracies = {}
            with torch.no_grad():
                for i, (inputs, labels) in enumerate(self.test_data):
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    outputs = self.model(inputs)
                    _, predicted = torch.max(outputs.data, 1)
                    correct = (predicted == labels).float()
                    for group in torch.unique(self.sensitive_attr):
                        mask = self.sensitive_attr == group
                        if mask.sum() > 0:
                            group_acc = correct[mask].mean().item()
                            if group.item() not in group_accuracies:
                                group_accuracies[group.item()] = []
                            group_accuracies[group.item()].append(group_acc)
            avg_accuracies = {k: np.mean(v) for k, v in group_accuracies.items()}
            fairness_score = 1 - np.std(list(avg_accuracies.values()))
            logger.info(f"Fairness test completed: {fairness_score:.4f}")
            return {"fairness_score": fairness_score, "group_accuracies": avg_accuracies, "status": "passed" if fairness_score > 0.9 else "warning"}
        except Exception as e:
            logger.error(f"Fairness test failed: {str(e)}")
            return {"fairness_score": 0.0, "status": "failed", "error": str(e)}

class PrivacyTest:
    def __init__(self, model: nn.Module, train_data: DataLoader, test_data: DataLoader, device: str = 'cpu'):
        self.model = model.to(device)
        self.train_data = train_data
        self.test_data = test_data
        self.device = device

    def run_test(self) -> Dict[str, Any]:
        try:
            # Simple membership inference: train shadow model or use loss difference
            self.model.eval()
            train_losses = []
            test_losses = []
            criterion = nn.CrossEntropyLoss()
            with torch.no_grad():
                for inputs, labels in self.train_data:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    outputs = self.model(inputs)
                    loss = criterion(outputs, labels)
                    train_losses.append(loss.item())
                for inputs, labels in self.test_data:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)
                    outputs = self.model(inputs)
                    loss = criterion(outputs, labels)
                    test_losses.append(loss.item())
            avg_train_loss = np.mean(train_losses)
            avg_test_loss = np.mean(test_losses)
            privacy_score = abs(avg_train_loss - avg_test_loss)  # Lower difference means better privacy
            logger.info(f"Privacy test completed: {privacy_score:.4f}")
            return {"privacy_score": privacy_score, "status": "passed" if privacy_score < 0.1 else "warning"}
        except Exception as e:
            logger.error(f"Privacy test failed: {str(e)}")
            return {"privacy_score": 1.0, "status": "failed", "error": str(e)}

class ModelValidator:
    def __init__(self, private_key_path: Optional[str] = None):
        self.private_key = None
        if private_key_path:
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            # Generate a simple key for demo
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def validate_model(self, model: nn.Module, test_data: DataLoader, train_data: Optional[DataLoader] = None,
                       sensitive_attr: Optional[torch.Tensor] = None, device: str = 'auto') -> Dict[str, Any]:
        if device == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Starting model validation on device: {device}")

        start_time = time.time()

        results = {}

        # Accuracy
        acc_test = AccuracyTest(model, test_data, device)
        results['accuracy'] = acc_test.run_test()

        # Robustness
        rob_test = RobustnessTest(model, test_data, device)
        results['robustness'] = rob_test.run_test()

        # Fairness
        if sensitive_attr is not None:
            fair_test = FairnessTest(model, test_data, sensitive_attr, device)
            results['fairness'] = fair_test.run_test()
        else:
            results['fairness'] = {"status": "skipped", "reason": "No sensitive attributes provided"}

        # Privacy
        if train_data is not None:
            priv_test = PrivacyTest(model, train_data, test_data, device)
            results['privacy'] = priv_test.run_test()
        else:
            results['privacy'] = {"status": "skipped", "reason": "No train data provided"}

        validation_time = time.time() - start_time
        results['validation_time'] = validation_time
        logger.info(f"Validation completed in {validation_time:.2f} seconds")

        # Overall status
        statuses = [r.get('status', 'failed') for r in results.values() if isinstance(r, dict)]
        overall_status = "passed" if all(s in ["passed", "skipped"] for s in statuses) else "failed"

        results['overall_status'] = overall_status
        return results

    def generate_certificate(self, validation_results: Dict[str, Any]) -> str:
        try:
            # Create certificate data
            cert_data = {
                "validation_results": validation_results,
                "timestamp": time.time(),
                "validator": "Ailoos ModelValidator"
            }
            cert_json = json.dumps(cert_data, sort_keys=True)
            cert_hash = hashlib.sha256(cert_json.encode()).hexdigest()

            # Sign the hash
            signature = self.private_key.sign(
                cert_hash.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )

            certificate = {
                "data": cert_data,
                "hash": cert_hash,
                "signature": signature.hex()
            }

            logger.info("Certificate generated successfully")
            return json.dumps(certificate)
        except Exception as e:
            logger.error(f"Certificate generation failed: {str(e)}")
            return json.dumps({"error": str(e)})