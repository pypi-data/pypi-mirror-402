"""
Function Calling Layer para EmpoorioLM
Capa especializada que integra function calling nativo en el modelo de lenguaje.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import json
import re
import logging

from .empoorio_lm import EmpoorioLMConfig

logger = logging.getLogger(__name__)


@dataclass
class FunctionCallingConfig:
    """Configuración para la capa de function calling."""
    tool_call_token: str = "<tool_call>"
    tool_call_end_token: str = "</tool_call>"
    max_tool_calls_per_response: int = 5
    enable_tool_validation: bool = True
    tool_embedding_dim: int = 256
    use_tool_attention: bool = True
    tool_context_window: int = 512


class ToolEmbeddings(nn.Module):
    """
    Embeddings especializados para herramientas.
    Crea representaciones vectoriales de herramientas disponibles.
    """

    def __init__(self, vocab_size: int, embedding_dim: int, tool_config: FunctionCallingConfig):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.tool_config = tool_config

        # Embeddings base
        self.token_embeddings = nn.Embedding(vocab_size, embedding_dim)

        # Tool-specific embeddings
        self.tool_embeddings = nn.Embedding(1000, tool_config.tool_embedding_dim)  # Max 1000 tools
        self.tool_projection = nn.Linear(tool_config.tool_embedding_dim, embedding_dim)

        # Special tokens
        self.tool_call_start_emb = nn.Parameter(torch.randn(embedding_dim))
        self.tool_call_end_emb = nn.Parameter(torch.randn(embedding_dim))

    def forward(self, input_ids: torch.Tensor, tool_specs: Optional[List[Dict[str, Any]]] = None) -> torch.Tensor:
        """
        Forward pass con integración de herramientas.

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            tool_specs: Especificaciones de herramientas disponibles

        Returns:
            Embeddings con tool context [batch_size, seq_len, embedding_dim]
        """
        # Base token embeddings
        embeddings = self.token_embeddings(input_ids)

        if tool_specs:
            # Add tool context embeddings
            tool_context = self._create_tool_context_embeddings(tool_specs, input_ids.device)
            embeddings = embeddings + tool_context.unsqueeze(0).expand(embeddings.shape[0], -1, -1)

        return embeddings

    def _create_tool_context_embeddings(self, tool_specs: List[Dict[str, Any]], device) -> torch.Tensor:
        """Crea embeddings de contexto para herramientas."""
        tool_embeddings = []

        for tool_spec in tool_specs[:100]:  # Limit to 100 tools
            # Create tool signature embedding
            tool_name = tool_spec.get('name', '')
            tool_desc = tool_spec.get('description', '')

            # Simple hash-based embedding for tool name
            name_hash = hash(tool_name) % 1000
            desc_hash = hash(tool_desc) % 1000

            tool_emb = self.tool_embeddings(torch.tensor([name_hash, desc_hash], device=device)).mean(dim=0)
            tool_embeddings.append(self.tool_projection(tool_emb))

        if tool_embeddings:
            return torch.stack(tool_embeddings).mean(dim=0)
        else:
            return torch.zeros(self.embedding_dim, device=device)


class FunctionCallingHead(nn.Module):
    """
    Head especializada para predecir llamadas a funciones.
    Detecta cuándo el modelo debe hacer una tool call.
    """

    def __init__(self, hidden_dim: int, config: FunctionCallingConfig):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.config = config

        # Tool call detection
        self.tool_call_detector = nn.Linear(hidden_dim, 1)  # Binary classification
        self.tool_call_classifier = nn.Linear(hidden_dim, 1000)  # Tool type classification

        # Tool parameter generation
        self.parameter_generator = nn.Linear(hidden_dim, hidden_dim)

        # Special token predictors
        self.start_token_predictor = nn.Linear(hidden_dim, 1)
        self.end_token_predictor = nn.Linear(hidden_dim, 1)

    def forward(self, hidden_states: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Predice llamadas a funciones desde hidden states.

        Args:
            hidden_states: Hidden states del modelo [batch_size, seq_len, hidden_dim]

        Returns:
            Diccionario con predicciones de tool calls
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape

        # Tool call detection (sigmoid for probability)
        tool_call_logits = self.tool_call_detector(hidden_states)  # [B, T, 1]
        tool_call_probs = torch.sigmoid(tool_call_logits)

        # Tool type classification (when tool call is detected)
        tool_type_logits = self.tool_call_classifier(hidden_states)  # [B, T, 1000]
        tool_type_probs = F.softmax(tool_type_logits, dim=-1)

        # Special token detection
        start_token_logits = self.start_token_predictor(hidden_states)  # [B, T, 1]
        end_token_logits = self.end_token_predictor(hidden_states)    # [B, T, 1]

        return {
            'tool_call_probs': tool_call_probs.squeeze(-1),      # [B, T]
            'tool_type_probs': tool_type_probs,                  # [B, T, 1000]
            'start_token_logits': start_token_logits.squeeze(-1), # [B, T]
            'end_token_logits': end_token_logits.squeeze(-1),    # [B, T]
        }


class FunctionCallingLayer(nn.Module):
    """
    Capa completa de function calling integrada en el modelo.
    Maneja detección, parsing y ejecución de tool calls.
    """

    def __init__(self, config: EmpoorioLMConfig, fc_config: FunctionCallingConfig):
        super().__init__()
        self.config = config
        self.fc_config = fc_config

        # Tool embeddings
        self.tool_embeddings = ToolEmbeddings(
            vocab_size=config.vocab_size,
            embedding_dim=config.n_embd,
            tool_config=fc_config
        )

        # Function calling head
        self.fc_head = FunctionCallingHead(config.n_embd, fc_config)

        # Tool call parsing patterns
        self._setup_tool_patterns()

        logger.info("FunctionCallingLayer initialized")

    def _setup_tool_patterns(self):
        """Configura patrones regex para parsing de tool calls."""
        escaped_start = re.escape(self.fc_config.tool_call_token)
        escaped_end = re.escape(self.fc_config.tool_call_end_token)
        self.tool_call_pattern = re.compile(
            f'{escaped_start}(.*?){escaped_end}',
            re.DOTALL
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        hidden_states: torch.Tensor,
        available_tools: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass de la capa de function calling.

        Args:
            input_ids: Input token IDs [batch_size, seq_len]
            hidden_states: Hidden states del modelo [batch_size, seq_len, hidden_dim]
            available_tools: Lista de herramientas disponibles

        Returns:
            Tuple de (updated_embeddings, fc_predictions)
        """
        # Create embeddings with tool context
        embeddings = self.tool_embeddings(input_ids, available_tools)

        # Generate function calling predictions
        fc_predictions = self.fc_head(hidden_states)

        return embeddings, fc_predictions

    def parse_tool_calls_from_text(self, generated_text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls desde texto generado.

        Args:
            generated_text: Texto generado por el modelo

        Returns:
            Lista de tool calls parseados
        """
        tool_calls = []

        # Find all tool call matches
        matches = self.tool_call_pattern.findall(generated_text)

        for match in matches[:self.fc_config.max_tool_calls_per_response]:
            try:
                # Parse JSON
                tool_call_data = json.loads(match.strip())

                # Validate structure
                if isinstance(tool_call_data, dict):
                    tool_call = {
                        'tool_name': tool_call_data.get('name') or tool_call_data.get('tool_name'),
                        'parameters': tool_call_data.get('parameters') or tool_call_data.get('args', {}),
                        'raw_call': match.strip()
                    }

                    if tool_call['tool_name']:
                        tool_calls.append(tool_call)

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool call: {match}")
                continue

        return tool_calls

    def generate_tool_call_prompt(self, base_prompt: str, available_tools: List[Dict[str, Any]]) -> str:
        """
        Genera un prompt enriquecido con información de herramientas.

        Args:
            base_prompt: Prompt base del usuario
            available_tools: Herramientas disponibles

        Returns:
            Prompt con instrucciones de function calling
        """
        # Create tool specifications
        tool_specs = []
        for tool in available_tools:
            tool_spec = {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {})
            }
            tool_specs.append(tool_spec)

        tools_json = json.dumps(tool_specs, indent=2)

        # Create enhanced prompt
        enhanced_prompt = f"""
You are EmpoorioLM, an AI assistant with access to various tools and functions.

AVAILABLE TOOLS:
{tools_json}

TOOL CALLING INSTRUCTIONS:
- To use a tool, generate a tool call in this exact format:
  {self.fc_config.tool_call_token}{{"name": "tool_name", "parameters": {{"param1": "value1"}}}}{self.fc_config.tool_call_end_token}
- You can make multiple tool calls if needed
- Always use valid JSON format
- After tool execution, you will receive results and can provide a final answer

USER QUERY: {base_prompt}

ASSISTANT:"""

        return enhanced_prompt

    def should_generate_tool_call(self, fc_predictions: Dict[str, torch.Tensor], threshold: float = 0.5) -> bool:
        """
        Decide si generar una tool call basada en las predicciones.

        Args:
            fc_predictions: Predicciones del function calling head
            threshold: Umbral de probabilidad

        Returns:
            True si debe generar tool call
        """
        # Check if any token has high tool call probability
        tool_call_probs = fc_predictions['tool_call_probs']
        max_prob = torch.max(tool_call_probs).item()

        return max_prob > threshold


class FunctionCallingEmpoorioLM(nn.Module):
    """
    EmpoorioLM con function calling nativo integrado.
    Extiende el modelo base con capacidades de tool calling.
    """

    def __init__(self, base_model, fc_config: Optional[FunctionCallingConfig] = None):
        super().__init__()
        self.base_model = base_model
        self.fc_config = fc_config or FunctionCallingConfig()

        # Add function calling layer
        self.fc_layer = FunctionCallingLayer(base_model.config, self.fc_config)

        # Tool registry integration
        self.available_tools = []

        logger.info("FunctionCallingEmpoorioLM initialized")

    def set_available_tools(self, tools: List[Dict[str, Any]]):
        """Configura las herramientas disponibles."""
        self.available_tools = tools

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Forward pass con function calling.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            labels: Labels for training
            **kwargs: Additional arguments

        Returns:
            Model outputs with function calling predictions
        """
        # Get base model outputs
        base_outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            **kwargs
        )

        # Get hidden states for function calling
        hidden_states = base_outputs.get('hidden_states', base_outputs['logits'])
        if isinstance(hidden_states, list):
            hidden_states = hidden_states[-1]  # Last layer

        # Apply function calling layer
        updated_embeddings, fc_predictions = self.fc_layer(
            input_ids, hidden_states, self.available_tools
        )

        # Add FC predictions to outputs
        base_outputs['fc_predictions'] = fc_predictions
        base_outputs['tool_call_detected'] = self.fc_layer.should_generate_tool_call(fc_predictions)

        return base_outputs

    def generate_with_tools(
        self,
        input_ids: torch.Tensor,
        max_length: int = 100,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        **generate_kwargs
    ) -> Tuple[torch.Tensor, List[Dict[str, Any]]]:
        """
        Genera texto con soporte para tool calls.

        Args:
            input_ids: Input token IDs
            max_length: Maximum generation length
            available_tools: Available tools for function calling
            **generate_kwargs: Additional generation arguments

        Returns:
            Tuple of (generated_tokens, detected_tool_calls)
        """
        if available_tools:
            self.set_available_tools(available_tools)

        # Generate text
        generated = self.base_model.generate(
            input_ids=input_ids,
            max_length=max_length,
            **generate_kwargs
        )

        # Decode generated text
        generated_text = self._decode_tokens(generated[0])

        # Parse tool calls
        tool_calls = self.fc_layer.parse_tool_calls_from_text(generated_text)

        return generated, tool_calls

    def _decode_tokens(self, token_ids: torch.Tensor) -> str:
        """Decode token IDs to text (simplified)."""
        # This would use the actual tokenizer in a real implementation
        # For now, return placeholder
        return f"<decoded_text_with_{len(token_ids)}_tokens>"

    def create_enhanced_prompt(self, user_query: str) -> str:
        """Crea un prompt enriquecido con tool calling instructions."""
        return self.fc_layer.generate_tool_call_prompt(user_query, self.available_tools)


# Función de conveniencia para crear modelo con function calling
def create_function_calling_empoorio_lm(
    base_model,
    fc_config: Optional[FunctionCallingConfig] = None
) -> FunctionCallingEmpoorioLM:
    """
    Crea una instancia de EmpoorioLM con function calling integrado.

    Args:
        base_model: Modelo base de EmpoorioLM
        fc_config: Configuración de function calling

    Returns:
        Modelo con function calling
    """
    return FunctionCallingEmpoorioLM(base_model, fc_config)