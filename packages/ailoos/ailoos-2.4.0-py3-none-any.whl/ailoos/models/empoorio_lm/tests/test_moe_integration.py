"""
Integration Tests for MoE EmpoorioLM
Tests de integración completa para el modelo MoE con el sistema base.
"""

import torch
import torch.nn as nn
import pytest
import numpy as np
from pathlib import Path
import tempfile
import sys
import os

# Add models directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.empoorio_lm.config import EmpoorioLMConfig, get_config_for_model_size
from models.empoorio_lm.model import EmpoorioLM
from models.empoorio_lm.moe import compute_moe_loss, get_moe_statistics


class TestMoEModelIntegration:
    """Integration tests for complete MoE model."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.config = EmpoorioLMConfig(
            vocab_size=1000,  # Small vocab for testing
            hidden_size=128,
            num_layers=4,
            num_heads=8,
            max_position_embeddings=64,
            use_moe=True,
            num_experts=4,
            top_k=2,
            moe_layers=[1, 2],  # Middle layers are MoE
            load_balance_weight=0.01,
            device="cpu"
        )

        self.model = EmpoorioLM(self.config)

    def test_model_initialization(self):
        """Test MoE model initializes correctly."""
        # Check model structure
        assert len(self.model.blocks) == self.config.num_layers

        # Check MoE layers
        moe_layers = [i for i, block in enumerate(self.model.blocks) if hasattr(block.ffn, 'router')]
        assert moe_layers == self.config.moe_layers

        # Check dense layers
        dense_layers = [i for i, block in enumerate(self.model.blocks) if not hasattr(block.ffn, 'router')]
        expected_dense = [i for i in range(self.config.num_layers) if i not in self.config.moe_layers]
        assert dense_layers == expected_dense

    def test_forward_pass_with_moe(self):
        """Test complete forward pass with MoE layers."""
        batch_size, seq_len = 2, 16
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))

        # Forward pass
        outputs = self.model(input_ids)

        # Check outputs
        assert 'logits' in outputs
        assert outputs['logits'].shape == (batch_size, seq_len, self.config.vocab_size)

        # Check MoE auxiliary info
        assert 'moe_aux_loss' in outputs
        assert 'moe_aux_info' in outputs

        # Check MoE statistics
        moe_info = outputs['moe_aux_info']
        assert len(moe_info) == len(self.config.moe_layers)  # Only MoE layers have aux info

        for layer_key, layer_info in moe_info.items():
            assert 'router_info' in layer_info
            router_info = layer_info['router_info']
            assert 'load_balance_loss' in router_info
            assert 'expert_usage' in router_info

    def test_generation_with_moe(self):
        """Test text generation with MoE model."""
        batch_size, seq_len = 1, 8
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))

        # Generate text
        generated = self.model.generate(
            input_ids=input_ids,
            max_length=16,
            temperature=0.8,
            top_k=10,
            do_sample=True
        )

        # Check generation
        assert generated.shape[0] == batch_size
        assert generated.shape[1] >= seq_len  # Should be extended
        assert torch.all(generated[:, :seq_len] == input_ids)  # Input should be preserved

    def test_loss_calculation_with_moe(self):
        """Test loss calculation includes MoE auxiliary loss."""
        batch_size, seq_len = 2, 12
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))
        labels = input_ids.clone()

        # Forward pass with labels
        outputs = self.model(input_ids, labels=labels)

        # Check losses
        assert 'loss' in outputs
        assert 'moe_aux_loss' in outputs

        # Total loss should include MoE loss
        total_loss = outputs['loss']
        moe_loss = outputs['moe_aux_loss']

        assert total_loss >= moe_loss  # Total loss includes MoE loss
        assert not torch.isnan(total_loss)
        assert not torch.isinf(total_loss)

    def test_gradient_flow_with_moe(self):
        """Test gradients flow correctly through MoE layers."""
        batch_size, seq_len = 2, 8
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))
        labels = input_ids.clone()

        # Forward pass
        self.model.train()
        outputs = self.model(input_ids, labels=labels)
        loss = outputs['loss']

        # Backward pass
        loss.backward()

        # Check gradients exist for key components
        assert self.model.embed_tokens.weight.grad is not None
        assert self.model.lm_head.weight.grad is not None

        # Check gradients in MoE layers
        for layer_idx in self.config.moe_layers:
            block = self.model.blocks[layer_idx]
            moe_layer = block.ffn

            # Check router gradients
            assert moe_layer.router.router_net.weight.grad is not None

            # Check expert gradients
            for expert in moe_layer.experts:
                assert expert.w1.weight.grad is not None
                assert expert.w2.weight.grad is not None

            # Check shared expert gradients
            assert moe_layer.shared_expert.w1.weight.grad is not None
            assert moe_layer.shared_expert.w2.weight.grad is not None


class TestDenseToMoEConversion:
    """Integration tests for dense to MoE conversion."""

    def setup_method(self):
        """Setup conversion test fixtures."""
        self.dense_config = EmpoorioLMConfig(
            vocab_size=1000,
            hidden_size=128,
            num_layers=4,
            num_heads=8,
            max_position_embeddings=64,
            use_moe=False,  # Dense model
            device="cpu"
        )

        self.moe_config = EmpoorioLMConfig(
            vocab_size=1000,
            hidden_size=128,
            num_layers=4,
            num_heads=8,
            max_position_embeddings=64,
            use_moe=True,
            num_experts=4,
            top_k=2,
            moe_layers=[1, 2],
            load_balance_weight=0.01,
            device="cpu"
        )

    def test_conversion_pipeline(self):
        """Test complete conversion from dense to MoE."""
        from scripts.upcycle_dense_to_moe import DenseToMoEConverter

        # Create dense model
        dense_model = EmpoorioLM(self.dense_config)

        # Create converter
        converter = DenseToMoEConverter(self.dense_config, self.moe_config)

        # Convert model
        moe_model = converter.convert_model(dense_model)

        # Verify conversion
        assert isinstance(moe_model, EmpoorioLM)
        assert moe_model.config.use_moe == True

        # Check MoE layers
        moe_layers = [i for i, block in enumerate(moe_model.blocks) if hasattr(block.ffn, 'router')]
        assert moe_layers == self.moe_config.moe_layers

    def test_weight_preservation(self):
        """Test that dense weights are properly copied to MoE."""
        from scripts.upcycle_dense_to_moe import DenseToMoEConverter

        # Create and train dense model briefly
        dense_model = EmpoorioLM(self.dense_config)
        dense_model.train()

        # Small training step to change weights from initialization
        optimizer = torch.optim.Adam(dense_model.parameters(), lr=0.01)
        batch_size, seq_len = 2, 8
        input_ids = torch.randint(0, self.dense_config.vocab_size, (batch_size, seq_len))
        labels = input_ids.clone()

        outputs = dense_model(input_ids, labels=labels)
        loss = outputs['loss']
        loss.backward()
        optimizer.step()

        # Convert to MoE
        converter = DenseToMoEConverter(self.dense_config, self.moe_config)
        moe_model = converter.convert_model(dense_model)

        # Check that embeddings are copied
        assert torch.allclose(
            dense_model.embed_tokens.weight,
            moe_model.embed_tokens.weight
        )

        # Check that attention weights are copied for dense layers
        dense_block = dense_model.blocks[0]  # Dense layer
        moe_block = moe_model.blocks[0]     # Dense layer
        assert torch.allclose(
            dense_block.attn.q_proj.weight,
            moe_block.attn.q_proj.weight
        )


class TestMoEWithFederatedLearning:
    """Test MoE compatibility with federated learning scenarios."""

    def setup_method(self):
        """Setup federated learning test fixtures."""
        self.config = get_config_for_model_size("small", use_moe=True)
        self.config.device = "cpu"
        self.model = EmpoorioLM(self.config)

    def test_model_serialization(self):
        """Test MoE model can be serialized/deserialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "moe_model"

            # Save model
            self.model.save_pretrained(model_path)

            # Load model
            loaded_model = EmpoorioLM.from_pretrained(model_path)

            # Check configuration
            assert loaded_model.config.use_moe == self.config.use_moe
            assert loaded_model.config.num_experts == self.config.num_experts
            assert loaded_model.config.moe_layers == self.config.moe_layers

    def test_gradient_accumulation(self):
        """Test gradient accumulation works with MoE (important for FL)."""
        batch_size, seq_len = 2, 8
        num_accumulation_steps = 3

        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

        total_loss = 0
        for step in range(num_accumulation_steps):
            input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))
            labels = input_ids.clone()

            outputs = self.model(input_ids, labels=labels)
            loss = outputs['loss'] / num_accumulation_steps  # Normalize for accumulation
            total_loss += loss.item()

            loss.backward()

        # Apply accumulated gradients
        optimizer.step()
        optimizer.zero_grad()

        # Check that gradients were applied
        assert total_loss > 0

    def test_memory_efficiency(self):
        """Test MoE memory efficiency compared to dense."""
        # Create dense config
        dense_config = EmpoorioLMConfig(
            vocab_size=1000,
            hidden_size=128,
            num_layers=4,
            num_heads=8,
            use_moe=False
        )

        dense_model = EmpoorioLM(dense_config)
        moe_model = EmpoorioLM(self.config)

        # Count parameters
        dense_params = sum(p.numel() for p in dense_model.parameters())
        moe_params = sum(p.numel() for p in moe_model.parameters())

        # MoE should have more parameters due to experts
        assert moe_params > dense_params

        # But parameter efficiency should be better (more parameters, but potentially better performance)
        efficiency_ratio = moe_params / dense_params
        assert efficiency_ratio > 1.0  # Should have more parameters


class TestMoEPerformance:
    """Performance tests for MoE model."""

    def setup_method(self):
        """Setup performance test fixtures."""
        self.config = EmpoorioLMConfig(
            vocab_size=1000,
            hidden_size=128,
            num_layers=4,
            num_heads=8,
            use_moe=True,
            num_experts=4,
            top_k=2,
            moe_layers=[1, 2],
            device="cpu"
        )
        self.model = EmpoorioLM(self.config)

    def test_inference_speed(self):
        """Test inference speed with MoE."""
        import time

        self.model.eval()
        batch_size, seq_len = 4, 16
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))

        # Warm up
        with torch.no_grad():
            for _ in range(3):
                _ = self.model(input_ids)

        # Measure inference time
        num_runs = 10
        start_time = time.time()

        with torch.no_grad():
            for _ in range(num_runs):
                _ = self.model(input_ids)

        end_time = time.time()
        avg_time = (end_time - start_time) / num_runs

        # Should be reasonable (less than 1 second per batch)
        assert avg_time < 1.0

    def test_memory_usage(self):
        """Test memory usage during training."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available for memory tests")

        self.model.cuda()
        batch_size, seq_len = 2, 16
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len)).cuda()
        labels = input_ids.clone()

        # Clear cache
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

        # Training step
        self.model.train()
        outputs = self.model(input_ids, labels=labels)
        loss = outputs['loss']
        loss.backward()

        # Check memory usage
        memory_used = torch.cuda.memory_allocated() / 1024**2  # MB
        assert memory_used > 0
        assert memory_used < 1000  # Should be reasonable (< 1GB)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])