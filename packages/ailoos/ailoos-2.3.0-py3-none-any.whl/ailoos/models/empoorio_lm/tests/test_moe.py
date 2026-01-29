"""
Unit Tests for MoE Components
Tests completos para componentes de Mixture of Experts.
"""

import torch
import torch.nn as nn
import pytest
import numpy as np
from pathlib import Path
import sys

# Add models directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.empoorio_lm.config import EmpoorioLMConfig
from models.empoorio_lm.moe import (
    NoisyTopKRouter,
    MoEExpert,
    MoELayer,
    compute_moe_loss,
    get_moe_statistics
)


class TestNoisyTopKRouter:
    """Test suite for NoisyTopKRouter."""

    def setup_method(self):
        """Setup test fixtures."""
        self.input_dim = 768
        self.num_experts = 8
        self.top_k = 2
        self.batch_size = 4
        self.seq_len = 10

        self.router = NoisyTopKRouter(
            input_dim=self.input_dim,
            num_experts=self.num_experts,
            top_k=self.top_k
        )

    def test_initialization(self):
        """Test router initialization."""
        assert self.router.input_dim == self.input_dim
        assert self.router.num_experts == self.num_experts
        assert self.router.top_k == self.top_k

    def test_forward_pass(self):
        """Test forward pass routing."""
        # Create test input
        hidden_states = torch.randn(self.batch_size * self.seq_len, self.input_dim)

        # Forward pass
        routing_weights, expert_mask, aux_info = self.router(hidden_states)

        # Check shapes
        assert routing_weights.shape == (self.batch_size * self.seq_len, self.num_experts)
        assert expert_mask.shape == (self.batch_size * self.seq_len, self.num_experts)

        # Check that only top_k experts are selected per token
        expert_counts = expert_mask.sum(dim=-1)
        assert torch.all(expert_counts == self.top_k)

        # Check routing weights sum to 1 for selected experts
        weighted_sum = (routing_weights * expert_mask).sum(dim=-1)
        assert torch.allclose(weighted_sum, torch.ones_like(weighted_sum))

    def test_load_balance_loss(self):
        """Test load balancing loss calculation."""
        hidden_states = torch.randn(self.batch_size * self.seq_len, self.input_dim)

        # Get routing weights
        routing_weights, _, aux_info = self.router(hidden_states)

        # Check load balance loss exists and is reasonable
        assert 'load_balance_loss' in aux_info
        loss = aux_info['load_balance_loss']
        assert loss >= 0
        assert not torch.isnan(loss)
        assert not torch.isinf(loss)

    def test_expert_usage_tracking(self):
        """Test expert usage statistics."""
        hidden_states = torch.randn(self.batch_size * self.seq_len, self.input_dim)

        # Forward pass
        _, _, aux_info = self.router(hidden_states)

        # Check expert usage
        assert 'expert_usage' in aux_info
        usage = aux_info['expert_usage']
        assert usage.shape == (self.num_experts,)
        assert torch.all(usage >= 0)

    def test_training_vs_eval(self):
        """Test different behavior in training vs evaluation."""
        hidden_states = torch.randn(self.batch_size * self.seq_len, self.input_dim)

        # Training mode
        self.router.train()
        weights_train, _, _ = self.router(hidden_states)

        # Eval mode
        self.router.eval()
        weights_eval, _, _ = self.router(hidden_states)

        # Should be different due to noise in training
        assert not torch.allclose(weights_train, weights_eval)


class TestMoEExpert:
    """Test suite for MoEExpert."""

    def setup_method(self):
        """Setup test fixtures."""
        self.input_dim = 768
        self.hidden_dim = 3072
        self.output_dim = 768
        self.batch_size = 4

        self.expert = MoEExpert(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        )

    def test_initialization(self):
        """Test expert initialization."""
        assert self.expert.input_dim == self.input_dim
        assert self.expert.hidden_dim == self.hidden_dim
        assert self.expert.output_dim == self.output_dim

    def test_forward_pass(self):
        """Test expert forward pass."""
        # Create test input
        hidden_states = torch.randn(self.batch_size, self.input_dim)

        # Forward pass
        output = self.expert(hidden_states)

        # Check output shape
        assert output.shape == (self.batch_size, self.output_dim)

        # Check no NaN or Inf values
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()

    def test_swiglu_activation(self):
        """Test SwiGLU activation function."""
        hidden_states = torch.randn(self.batch_size, self.input_dim)

        # Get intermediate values
        gate = self.expert.activation(self.expert.w3(hidden_states))
        hidden = self.expert.w1(hidden_states) * gate

        # SwiGLU should be applied
        assert hidden.shape == (self.batch_size, self.hidden_dim)
        assert not torch.isnan(hidden).any()


class TestMoELayer:
    """Test suite for MoELayer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = EmpoorioLMConfig(
            hidden_size=768,
            num_experts=4,
            top_k=2,
            moe_layers=[0, 1, 2],
            load_balance_weight=0.01,
            device="cpu"
        )
        self.batch_size = 2
        self.seq_len = 8
        self.layer_idx = 0

        self.moe_layer = MoELayer(self.config, self.layer_idx)

    def test_initialization(self):
        """Test MoE layer initialization."""
        assert self.moe_layer.config == self.config
        assert self.moe_layer.layer_idx == self.layer_idx
        assert len(self.moe_layer.experts) == self.config.num_experts
        assert self.moe_layer.router.num_experts == self.config.num_experts

    def test_forward_pass(self):
        """Test MoE layer forward pass."""
        # Create test input
        hidden_states = torch.randn(self.batch_size, self.seq_len, self.config.hidden_size)

        # Forward pass
        output, aux_info = self.moe_layer(hidden_states)

        # Check output shape
        assert output.shape == (self.batch_size, self.seq_len, self.config.hidden_size)

        # Check auxiliary info
        assert 'router_info' in aux_info
        assert 'total_experts' in aux_info
        assert 'active_experts' in aux_info
        assert aux_info['total_experts'] == self.config.num_experts + 1  # +1 for shared
        assert aux_info['active_experts'] == self.config.top_k + 1  # +1 for shared

    def test_routing_statistics(self):
        """Test routing statistics collection."""
        hidden_states = torch.randn(self.batch_size, self.seq_len, self.config.hidden_size)

        _, aux_info = self.moe_layer(hidden_states)

        router_info = aux_info['router_info']
        required_keys = ['routing_probs', 'expert_mask', 'top_k_indices', 'load_balance_loss', 'expert_usage']
        for key in required_keys:
            assert key in router_info

    def test_expert_usage_stats(self):
        """Test expert usage statistics."""
        stats = self.moe_layer.get_expert_usage_stats()

        assert 'expert_usage' in stats
        assert 'total_experts' in stats
        assert 'shared_expert_active' in stats

        assert len(stats['expert_usage']) == self.config.num_experts
        assert stats['total_experts'] == self.config.num_experts
        assert stats['shared_expert_active'] == True


class TestMoEUtilities:
    """Test suite for MoE utility functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = EmpoorioLMConfig(
            hidden_size=768,
            num_experts=4,
            top_k=2,
            moe_layers=[0, 1],
            device="cpu"
        )

    def test_compute_moe_loss(self):
        """Test MoE loss computation."""
        # Create mock auxiliary info
        aux_info = {
            'layer_0': {
                'router_info': {
                    'load_balance_loss': torch.tensor(0.1)
                }
            },
            'layer_1': {
                'router_info': {
                    'load_balance_loss': torch.tensor(0.2)
                }
            }
        }

        total_loss = compute_moe_loss(aux_info)
        expected_loss = 0.1 + 0.2
        assert abs(total_loss.item() - expected_loss) < 1e-6

    def test_get_moe_statistics(self):
        """Test MoE statistics extraction."""
        # Create mock auxiliary info
        aux_info = {
            'layer_0': {
                'router_info': {
                    'expert_usage': torch.tensor([0.1, 0.2, 0.3, 0.4]),
                    'load_balance_loss': torch.tensor(0.1)
                }
            },
            'layer_1': {
                'router_info': {
                    'expert_usage': torch.tensor([0.15, 0.25, 0.35, 0.45]),
                    'load_balance_loss': torch.tensor(0.2)
                }
            }
        }

        stats = get_moe_statistics(aux_info)

        assert stats['total_layers'] == 2
        assert len(stats['expert_usage']) == 2
        assert len(stats['load_balance_losses']) == 2
        assert torch.allclose(torch.tensor(stats['load_balance_losses']), torch.tensor([0.1, 0.2]))


class TestMoEIntegration:
    """Integration tests for MoE components working together."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.config = EmpoorioLMConfig(
            hidden_size=768,
            num_layers=4,
            num_experts=8,
            top_k=2,
            moe_layers=[1, 2],  # Only middle layers are MoE
            use_moe=True,
            device="cpu"
        )

    def test_moe_layer_in_transformer_block(self):
        """Test MoE layer integrated in transformer block."""
        from models.empoorio_lm.model import GPT2Block

        # Create transformer block with MoE
        block = GPT2Block(self.config, layer_idx=1)  # This should be MoE

        # Verify it's using MoE
        assert hasattr(block.ffn, 'router')
        assert hasattr(block.ffn, 'experts')

        # Test forward pass
        batch_size, seq_len = 2, 10
        hidden_states = torch.randn(batch_size, seq_len, self.config.hidden_size)
        attention_mask = None

        output, aux_info = block(hidden_states, attention_mask)

        assert output.shape == (batch_size, seq_len, self.config.hidden_size)
        assert aux_info is not None
        assert 'router_info' in aux_info

    def test_dense_layer_in_transformer_block(self):
        """Test dense layer in transformer block."""
        from models.empoorio_lm.model import GPT2Block

        # Create transformer block without MoE
        block = GPT2Block(self.config, layer_idx=0)  # This should be dense

        # Verify it's using dense FFN
        assert not hasattr(block.ffn, 'router')
        assert not hasattr(block.ffn, 'experts')

        # Test forward pass
        batch_size, seq_len = 2, 10
        hidden_states = torch.randn(batch_size, seq_len, self.config.hidden_size)
        attention_mask = None

        output, aux_info = block(hidden_states, attention_mask)

        assert output.shape == (batch_size, seq_len, self.config.hidden_size)
        assert aux_info is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])