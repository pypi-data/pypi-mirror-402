"""
EmpoorioLM - GPT-2 Style Transformer Model with Nested Learning Support
========================================================================

REAL IMPLEMENTATION: Complete GPT-2 style transformer with modern optimizations
PLUS Nested Learning capabilities based on Google Research's Nested Learning paradigm.

This module imports the real implementation from models/empoorio_lm/ which includes:
- Rotary Position Embeddings (RoPE)
- Parallel residual connections
- Flash attention support
- Gradient checkpointing
- Mixed precision training
- BPE tokenizer integration

NESTED LEARNING EXTENSIONS:
- Continuum Memory System (CMS) blocks
- Associative Memory integration
- Context Flow Management
- Multi-frequency optimization
- Self-modifying recurrent layers

For backward compatibility, this file re-exports the real implementation with Nested Learning extensions.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import torch
import torch.nn as nn

# Add the models directory to Python path
models_dir = Path(__file__).parent.parent.parent.parent / "models"
if str(models_dir) not in sys.path:
    sys.path.insert(0, str(models_dir))

# Nested Learning imports
try:
    from .hope.associative_memory import AssociativeMemory
    from .hope.cms_block import CMSBlock, AdaptiveCMSBlock
    from .hope.hope_architecture import SelfModifyingRecurrent
    from ..memory.context_flow_manager import ContextFlowManager
    from ..optimizers.multi_frequency_scheduler import MultiFrequencyScheduler
    _NESTED_LEARNING_AVAILABLE = True
except ImportError:
    _NESTED_LEARNING_AVAILABLE = False

class EmpoorioLMNested(nn.Module):
    """
    EmpoorioLM with Nested Learning Extensions

    Extends the base EmpoorioLM with full Nested Learning capabilities:
    - Continuum Memory System (CMS) blocks
    - Associative Memory integration
    - Context Flow Management
    - Self-modifying recurrent layers
    - Multi-frequency optimization support
    """

    def __init__(self, base_model: nn.Module, config: Any, enable_nested_learning: bool = True):
        super().__init__()
        self.base_model = base_model
        self.config = config
        self.enable_nested_learning = enable_nested_learning and _NESTED_LEARNING_AVAILABLE

        if self.enable_nested_learning:
            # Nested Learning components
            embed_dim = getattr(config, 'hidden_size', getattr(config, 'embed_dim', 768))

            # Continuum Memory System blocks
            self.cms_blocks = nn.ModuleList([
                AdaptiveCMSBlock(embed_dim, num_memory_modules=3)
                for _ in range(2)  # 2 CMS blocks for balance
            ])

            # Associative memory for pattern matching
            self.associative_memory = AssociativeMemory(
                input_dim=embed_dim,
                memory_size=1024
            )

            # Self-modifying recurrent layer
            self.self_modifying_recurrent = SelfModifyingRecurrent(embed_dim)

            # Context flow manager
            self.context_flow_manager = ContextFlowManager(
                embed_dims=[embed_dim] * 3,
                max_flows_per_level=50
            )

            # Multi-frequency scheduler
            self.frequency_scheduler = MultiFrequencyScheduler()

            # Nested learning statistics
            self.nested_stats = {
                'forward_steps': 0,
                'memory_updates': 0,
                'context_flows_created': 0,
                'adaptation_events': 0
            }
        else:
            print("⚠️  Nested Learning components not available, running base EmpoorioLM")

    def forward(self, input_ids: torch.Tensor, **kwargs) -> Dict[str, Any]:
        """Forward pass with Nested Learning extensions."""
        # Base model forward pass
        outputs = self.base_model(input_ids, **kwargs)

        if not self.enable_nested_learning:
            return outputs

        self.nested_stats['forward_steps'] += 1

        # Extract hidden states from base model
        hidden_states = outputs.get('last_hidden_state', outputs.get('hidden_states', outputs['logits']))

        # Apply Nested Learning extensions
        batch_size, seq_len, embed_dim = hidden_states.shape

        # 1. Continuum Memory System processing
        cms_outputs = []
        for cms_block in self.cms_blocks:
            hidden_states = cms_block(hidden_states.unsqueeze(0)).squeeze(0)
            cms_outputs.append(hidden_states)

        # 2. Self-modifying recurrent processing
        # Reshape for recurrent processing
        recurrent_input = hidden_states.mean(dim=1)  # Sequence-level representation
        recurrent_output = self.self_modifying_recurrent(recurrent_input.unsqueeze(0)).squeeze(0)

        # 3. Associative memory integration
        memory_output = self.associative_memory(recurrent_output.unsqueeze(0)).squeeze(0)

        # 4. Context flow management
        context_type = kwargs.get('context_type', 'general')
        flow_id = self.context_flow_manager.create_nested_flow(
            context_type=context_type,
            initial_context=recurrent_output
        )
        self.nested_stats['context_flows_created'] += 1

        # Update outputs with Nested Learning enhancements
        enhanced_outputs = outputs.copy()
        enhanced_outputs.update({
            'nested_hidden_states': hidden_states,
            'cms_outputs': cms_outputs,
            'memory_output': memory_output,
            'context_flow_id': flow_id,
            'nested_stats': self.nested_stats.copy()
        })

        return enhanced_outputs

    def adapt_to_context(self, context_type: str, context_data: torch.Tensor):
        """Adapt model to specific context using Nested Learning."""
        if not self.enable_nested_learning:
            return

        # Update associative memory
        self.associative_memory.update(context_data, torch.tensor([1.0]))

        # Create/update context flow
        self.context_flow_manager.update_flow_hierarchy(
            f"{context_type}_root",
            context_data,
            {'context_type': context_type}
        )

        # Adapt CMS blocks
        for cms_block in self.cms_blocks:
            if hasattr(cms_block, 'adapt_to_task'):
                cms_block.adapt_to_task(0.5, 0.7)  # Default adaptation

        self.nested_stats['adaptation_events'] += 1

    def consolidate_knowledge(self):
        """Consolidate learned knowledge across Nested Learning components."""
        if not self.enable_nested_learning:
            return

        # Consolidate associative memory
        self.associative_memory.consolidate_memory()

        # Consolidate context flows
        self.context_flow_manager.consolidate_flows()

        # Consolidate CMS memories
        for cms_block in self.cms_blocks:
            cms_block.consolidate_all_memories()

    def get_nested_stats(self) -> Dict[str, Any]:
        """Get comprehensive Nested Learning statistics."""
        if not self.enable_nested_learning:
            return {'nested_learning': False}

        context_stats = self.context_flow_manager.get_flow_statistics()
        cms_stats = [cms_block.get_cms_stats() for cms_block in self.cms_blocks]

        return {
            'nested_learning': True,
            'forward_steps': self.nested_stats['forward_steps'],
            'adaptation_events': self.nested_stats['adaptation_events'],
            'context_flows_created': self.nested_stats['context_flows_created'],
            'associative_memory': self.associative_memory.get_memory_stats(),
            'context_flow_manager': context_stats,
            'cms_blocks': cms_stats,
            'frequency_scheduler': self.frequency_scheduler.get_scheduler_statistics()
        }

    def save_nested_state(self, path: str):
        """Save Nested Learning state."""
        if not self.enable_nested_learning:
            return

        state = {
            'nested_stats': self.nested_stats,
            'associative_memory': {
                'memory_matrix': self.associative_memory.memory_matrix,
                'memory_values': self.associative_memory.memory_values,
                'memory_age': self.associative_memory.memory_age,
                'memory_strength': self.associative_memory.memory_strength
            },
            'context_flow_manager': 'Use context_flow_manager.save_flow_state()',
            'cms_blocks': [cms_block.get_cms_stats() for cms_block in self.cms_blocks]
        }
        torch.save(state, path)

    def load_nested_state(self, path: str):
        """Load Nested Learning state."""
        if not self.enable_nested_learning:
            return

        state = torch.load(path)
        self.nested_stats = state['nested_stats']

        # Load associative memory
        memory_state = state['associative_memory']
        self.associative_memory.memory_matrix.data = memory_state['memory_matrix']
        self.associative_memory.memory_values.data = memory_state['memory_values']
        self.associative_memory.memory_age = memory_state['memory_age']
        self.associative_memory.memory_strength = memory_state['memory_strength']


try:
    # Import the real implementation
    from .empoorio_lm_real import (
        EmpoorioLM,
        EmpoorioLMConfig,
        EmpoorioLMTokenizer,
        get_config_for_model_size,
        load_trained_tokenizer,
    )
    _REAL_IMPLEMENTATION_LOADED = True
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not load real EmpoorioLM implementation: {e}")
    logger.warning("Falling back to basic implementation")

    # Fallback to basic implementation if real one is not available
    _REAL_IMPLEMENTATION_LOADED = False

    import torch
    import torch.nn as nn
    from typing import Optional, Dict, Any, Union
    from dataclasses import dataclass
    from pathlib import Path
    import json

    @dataclass
    class EmpoorioLMConfig:
        """Basic configuration for fallback."""
        vocab_size: int = 30000
        hidden_size: int = 768
        num_layers: int = 12
        num_heads: int = 12
        max_position_embeddings: int = 1024
        dropout: float = 0.1
        activation_function: str = "gelu"

        def to_dict(self) -> Dict[str, Any]:
            return {
                "vocab_size": self.vocab_size,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
                "num_heads": self.num_heads,
                "max_position_embeddings": self.max_position_embeddings,
                "dropout": self.dropout,
                "activation_function": self.activation_function,
            }

        @classmethod
        def from_dict(cls, config_dict: Dict[str, Any]) -> 'EmpoorioLMConfig':
            return cls(**config_dict)

    class EmpoorioLM(nn.Module):
        """Basic fallback implementation."""
        def __init__(self, config: EmpoorioLMConfig):
            super().__init__()
            self.config = config
            self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
            self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
            self.lm_head.weight = self.embed_tokens.weight

        def forward(self, input_ids: torch.Tensor, **kwargs) -> Dict[str, Any]:
            # Very basic implementation
            embeds = self.embed_tokens(input_ids)
            logits = self.lm_head(embeds)
            return {"logits": logits}

        def get_model_info(self) -> Dict[str, Any]:
            return {"fallback": True, "message": "Using basic fallback implementation"}

    class EmpoorioLMTokenizer:
        """Basic tokenizer fallback."""
        def __init__(self, **kwargs):
            self.vocab_size = 30000

        def encode(self, text: str) -> list:
            return [1] + [ord(c) % 30000 for c in text] + [2]

        def decode(self, ids: list) -> str:
            return "".join(chr(i % 256) for i in ids if i > 2)

    def get_config_for_model_size(size: str):
        return EmpoorioLMConfig()

    def load_trained_tokenizer():
        return EmpoorioLMTokenizer()

# Helper function to create EmpoorioLM with Nested Learning
def create_nested_empiorio_lm(config: Any = None, enable_nested: bool = True) -> Union[EmpoorioLM, EmpoorioLMNested]:
    """
    Create EmpoorioLM model with optional Nested Learning extensions.

    Args:
        config: Model configuration
        enable_nested: Whether to enable Nested Learning extensions

    Returns:
        EmpoorioLM model with or without Nested Learning
    """
    if config is None:
        config = get_config_for_model_size('base')

    # Create base model
    base_model = EmpoorioLM(config)

    if enable_nested and _NESTED_LEARNING_AVAILABLE:
        # Wrap with Nested Learning extensions
        nested_model = EmpoorioLMNested(base_model, config, enable_nested=True)
        print("🧬 EmpoorioLM with NESTED LEARNING activated!")
        print("   ✅ Continuum Memory System (CMS)")
        print("   ✅ Associative Memory integration")
        print("   ✅ Context Flow Management")
        print("   ✅ Self-modifying recurrent layers")
        return nested_model
    else:
        if enable_nested and not _NESTED_LEARNING_AVAILABLE:
            print("⚠️  Nested Learning requested but components not available")
            print("   → Using base EmpoorioLM")
        return base_model


# Re-export for backward compatibility
__all__ = [
    'EmpoorioLM',
    'EmpoorioLMConfig',
    'EmpoorioLMTokenizer',
    'EmpoorioLMNested',
    'get_config_for_model_size',
    'load_trained_tokenizer',
    'create_nested_empiorio_lm',
]

# Log which implementation is being used
if _REAL_IMPLEMENTATION_LOADED:
    print("✅ Using REAL EmpoorioLM implementation with GPT-2 architecture")
    if _NESTED_LEARNING_AVAILABLE:
        print("🧬 NESTED LEARNING components available - use create_nested_empiorio_lm() for full capabilities")
    else:
        print("⚠️  Nested Learning components not available")
else:
    print("⚠️  Using FALLBACK EmpoorioLM implementation (basic)")
    if _NESTED_LEARNING_AVAILABLE:
        print("🧬 Nested Learning components available for fallback model")