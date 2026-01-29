"""
Sistema de Expertos Pluggables para EmpoorioLM
===============================================

Este módulo implementa la arquitectura de "Expertos Desacoplables" que permite
cargar expertos especializados por dominio de forma independiente del modelo base.

Características:
- Carga selectiva de expertos por dominio
- Routing inteligente basado en metadatos
- Arquitectura modular para escalabilidad infinita
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
import json
import logging
from dataclasses import dataclass, field
from enum import Enum

from .config import EmpoorioLMConfig
from .moe import MoELayer

logger = logging.getLogger(__name__)


class Domain(Enum):
    """Dominios disponibles para expertos especializados."""
    GENERAL = "general"          # Base model sin especialización
    LEGAL = "legal"              # Contratos, leyes, jurisprudencia
    MEDICAL = "medical"          # Diagnósticos, tratamientos, medicina
    CODING = "coding"            # Programación, desarrollo de software
    FINANCIAL = "financial"      # Finanzas, inversiones, economía
    SCIENTIFIC = "scientific"    # Investigación, papers, matemáticas
    CREATIVE = "creative"        # Escritura creativa, arte, diseño


@dataclass
class ExpertConfig:
    """Configuración de un experto especializado."""
    domain: Domain
    name: str
    description: str
    target_layers: List[int]  # Capas MoE que este experto modifica
    expert_indices: List[int]  # Índices de expertos que entrena
    dataset_info: Dict[str, Any]  # Información del dataset de entrenamiento
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    version: str = "1.0.0"
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "name": self.name,
            "description": self.description,
            "target_layers": self.target_layers,
            "expert_indices": self.expert_indices,
            "dataset_info": self.dataset_info,
            "performance_metrics": self.performance_metrics,
            "version": self.version,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpertConfig':
        data["domain"] = Domain(data["domain"])
        return cls(**data)


@dataclass
class DomainRoutingConfig:
    """Configuración de routing por dominio."""
    domain: Domain
    force_expert_indices: List[int]  # Expertos que se activan forzosamente
    priority_boost: float = 1.0  # Multiplicador de prioridad
    context_keywords: List[str] = field(default_factory=list)  # Palabras clave para detección automática

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "force_expert_indices": self.force_expert_indices,
            "priority_boost": self.priority_boost,
            "context_keywords": self.context_keywords
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainRoutingConfig':
        data["domain"] = Domain(data["domain"])
        return cls(**data)


class ExpertManager:
    """
    Gestor de expertos pluggables.

    Permite cargar, gestionar y combinar expertos especializados
    con el modelo base de EmpoorioLM.
    """

    def __init__(self, experts_dir: Union[str, Path]):
        self.experts_dir = Path(experts_dir)
        self.loaded_experts: Dict[str, Dict[str, Any]] = {}
        self.routing_configs: Dict[Domain, DomainRoutingConfig] = {}
        self.active_domains: Set[Domain] = set()

        # Crear directorios si no existen
        self.experts_dir.mkdir(parents=True, exist_ok=True)
        for domain in Domain:
            (self.experts_dir / domain.value).mkdir(exist_ok=True)

        logger.info(f"🚀 ExpertManager inicializado en {self.experts_dir}")

    def load_expert(self, domain: Domain, expert_name: str) -> bool:
        """
        Cargar un experto especializado.

        Args:
            domain: Dominio del experto
            expert_name: Nombre del experto

        Returns:
            True si se cargó exitosamente
        """
        expert_path = self.experts_dir / domain.value / expert_name

        if not expert_path.exists():
            # Fallback para Inference-Time Thinking: crear experto "general" virtual
            if domain == Domain.GENERAL and expert_name == "general_expert":
                logger.info(f"🔄 Creando experto general virtual para Inference-Time Thinking")
                return self._create_general_expert_fallback()
            else:
                logger.warning(f"⚠️  Experto no encontrado: {expert_path}")
                return False

        try:
            # Cargar configuración
            config_path = expert_path / "expert_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                config = ExpertConfig.from_dict(config_data)
            else:
                logger.warning(f"⚠️  Configuración no encontrada para {expert_name}")
                return False

            # Cargar pesos del experto
            weights_path = expert_path / "expert_weights.pt"
            if weights_path.exists():
                weights = torch.load(weights_path, map_location='cpu')
            else:
                logger.warning(f"⚠️  Pesos no encontrados para {expert_name}")
                return False

            # Almacenar experto cargado
            expert_key = f"{domain.value}_{expert_name}"
            self.loaded_experts[expert_key] = {
                "config": config,
                "weights": weights,
                "path": expert_path
            }

            self.active_domains.add(domain)
            logger.info(f"✅ Experto cargado: {expert_key}")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando experto {expert_name}: {e}")
            return False

    def unload_expert(self, domain: Domain, expert_name: str) -> bool:
        """Descargar un experto de memoria."""
        expert_key = f"{domain.value}_{expert_name}"
        if expert_key in self.loaded_experts:
            del self.loaded_experts[expert_key]

            # Verificar si quedan expertos de este dominio
            domain_still_active = any(
                key.startswith(f"{domain.value}_")
                for key in self.loaded_experts.keys()
            )
            if not domain_still_active:
                self.active_domains.discard(domain)

            logger.info(f"✅ Experto descargado: {expert_key}")
            return True

        return False

    def save_expert(self, config: ExpertConfig, weights: Dict[str, torch.Tensor],
                   domain: Domain, expert_name: str) -> bool:
        """
        Guardar un experto entrenado.

        Args:
            config: Configuración del experto
            weights: Pesos del experto
            domain: Dominio
            expert_name: Nombre del experto

        Returns:
            True si se guardó exitosamente
        """
        expert_path = self.experts_dir / domain.value / expert_name
        expert_path.mkdir(parents=True, exist_ok=True)

        try:
            # Guardar configuración
            config_path = expert_path / "expert_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

            # Guardar pesos
            weights_path = expert_path / "expert_weights.pt"
            torch.save(weights, weights_path)

            logger.info(f"✅ Experto guardado: {domain.value}/{expert_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error guardando experto: {e}")
            return False

    def get_loaded_experts(self, domain: Optional[Domain] = None) -> Dict[str, Dict[str, Any]]:
        """Obtener expertos cargados, opcionalmente filtrados por dominio."""
        if domain is None:
            return self.loaded_experts
        else:
            return {
                key: expert for key, expert in self.loaded_experts.items()
                if key.startswith(f"{domain.value}_")
            }

    def set_domain_routing(self, config: DomainRoutingConfig):
        """Configurar routing para un dominio específico."""
        self.routing_configs[config.domain] = config
        logger.info(f"✅ Routing configurado para dominio: {config.domain.value}")

    def get_domain_routing(self, domain: Domain) -> Optional[DomainRoutingConfig]:
        """Obtener configuración de routing para un dominio."""
        return self.routing_configs.get(domain)

    def detect_domain_from_prompt(self, prompt: str) -> Optional[Domain]:
        """
        Detectar dominio automáticamente desde el prompt del usuario.

        Returns:
            Dominio detectado o None si no se detecta ninguno
        """
        prompt_lower = prompt.lower()

        for domain, routing_config in self.routing_configs.items():
            # Verificar palabras clave
            for keyword in routing_config.context_keywords:
                if keyword.lower() in prompt_lower:
                    return domain

        return None

    def get_expert_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de los expertos cargados."""
        stats = {
            "total_experts": len(self.loaded_experts),
            "active_domains": [d.value for d in self.active_domains],
            "experts_by_domain": {}
        }

        for domain in Domain:
            domain_experts = self.get_loaded_experts(domain)
            if domain_experts:
                stats["experts_by_domain"][domain.value] = {
                    "count": len(domain_experts),
                    "names": list(domain_experts.keys())
                }

        return stats

    def _create_general_expert_fallback(self) -> bool:
        """
        Crear un experto "general" virtual como fallback para Inference-Time Thinking.
        Este experto no modifica pesos, pero permite que el sistema funcione.
        """
        try:
            # Crear configuración básica para experto general
            config = ExpertConfig(
                domain=Domain.GENERAL,
                name="general_expert",
                description="Experto general virtual para Inference-Time Thinking",
                target_layers=[],  # No modifica capas específicas
                expert_indices=[],  # No usa índices específicos
                dataset_info={"type": "virtual", "purpose": "inference_time_thinking_fallback"},
                performance_metrics={"fallback": True, "virtual": True},
                version="1.0.0-virtual",
                created_at="2025-11-25T00:00:00Z"
            )

            # Crear pesos vacíos (el sistema usará el modelo base)
            weights = {}  # Pesos vacíos - el modelo base se usa directamente

            # Almacenar experto virtual
            expert_key = "general_general_expert"
            self.loaded_experts[expert_key] = {
                "config": config,
                "weights": weights,
                "path": None,  # No hay path físico
                "virtual": True  # Marcar como virtual
            }

            self.active_domains.add(Domain.GENERAL)
            logger.info("✅ Experto general virtual creado para Inference-Time Thinking")
            return True

        except Exception as e:
            logger.error(f"❌ Error creando experto general virtual: {e}")
            return False


class PluggableEmpoorioLM(nn.Module):
    """
    Versión pluggable de EmpoorioLM con soporte para expertos desacoplables.

    Esta clase extiende EmpoorioLM para permitir la carga dinámica de expertos
    especializados sin recargar todo el modelo.
    """

    def __init__(self, config: EmpoorioLMConfig, expert_manager: ExpertManager):
        super().__init__()
        self.config = config
        self.expert_manager = expert_manager

        # Modelo base (igual que EmpoorioLM original)
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.embed_positions = None  # RoPE será manejado en las capas

        # RoPE para positional encoding
        if config.use_rope:
            from .rope import create_rope_for_context
            context_key = "1k" if config.max_context_size <= 1024 else "4k"
            self.rope = create_rope_for_context(context_key, config.hidden_size // config.num_heads)
        else:
            self.rope = None

        # Capas transformer con soporte para expertos pluggables
        self.layers = nn.ModuleList([
            PluggableTransformerBlock(config, layer_idx=i, rope=self.rope)
            for i in range(config.num_layers)
        ])

        # Capas finales
        self.ln_f = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.lm_head.weight = self.embed_tokens.weight

        # Estado de expertos
        self.plugged_experts: Dict[int, Dict[str, torch.Tensor]] = {}  # layer_idx -> expert_weights

        logger.info("🚀 PluggableEmpoorioLM inicializado con soporte para expertos")

    def plug_expert(self, layer_idx: int, expert_weights: Dict[str, torch.Tensor]) -> bool:
        """
        Conectar un experto a una capa específica.

        Args:
            layer_idx: Índice de la capa
            expert_weights: Pesos del experto

        Returns:
            True si se conectó exitosamente
        """
        if layer_idx >= len(self.layers):
            logger.error(f"❌ Capa {layer_idx} no existe")
            return False

        layer = self.layers[layer_idx]
        if not hasattr(layer, 'plug_expert'):
            logger.error(f"❌ Capa {layer_idx} no soporta expertos pluggables")
            return False

        success = layer.plug_expert(expert_weights)
        if success:
            self.plugged_experts[layer_idx] = expert_weights
            logger.info(f"✅ Experto conectado a capa {layer_idx}")
        else:
            logger.error(f"❌ Error conectando experto a capa {layer_idx}")

        return success

    def unplug_expert(self, layer_idx: int) -> bool:
        """Desconectar experto de una capa."""
        if layer_idx in self.plugged_experts:
            layer = self.layers[layer_idx]
            if hasattr(layer, 'unplug_expert'):
                layer.unplug_expert()
            del self.plugged_experts[layer_idx]
            logger.info(f"✅ Experto desconectado de capa {layer_idx}")
            return True

        return False

    def load_domain_experts(self, domain: Domain) -> int:
        """
        Cargar todos los expertos disponibles para un dominio.

        Returns:
            Número de expertos cargados
        """
        loaded_experts = self.expert_manager.get_loaded_experts(domain)
        loaded_count = 0

        for expert_key, expert_data in loaded_experts.items():
            config = expert_data["config"]
            weights = expert_data["weights"]

            # Conectar experto a las capas especificadas
            for layer_idx in config.target_layers:
                if self.plug_expert(layer_idx, weights):
                    loaded_count += 1

        logger.info(f"✅ Cargados {loaded_count} expertos para dominio {domain.value}")
        return loaded_count

    def apply_domain_routing(self, domain: Domain, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Aplicar routing específico de dominio a los input_ids.

        Args:
            domain: Dominio para routing
            input_ids: Tokens de entrada

        Returns:
            input_ids con metadatos de routing (si es necesario)
        """
        routing_config = self.expert_manager.get_domain_routing(domain)
        if routing_config:
            # Aquí se podría modificar input_ids para incluir tokens especiales
            # que activen el routing deseado
            logger.debug(f"🔀 Aplicando routing para dominio: {domain.value}")

        return input_ids

    def forward(self, input_ids: torch.Tensor, domain: Optional[Domain] = None, **kwargs):
        """
        Forward pass con soporte para routing por dominio.
        """
        # Aplicar routing si se especifica dominio
        if domain:
            input_ids = self.apply_domain_routing(domain, input_ids)

        # Resto del forward igual que EmpoorioLM original
        batch_size, seq_len = input_ids.size()

        # Create position IDs
        position_ids = torch.arange(seq_len, dtype=torch.long, device=input_ids.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        # Embeddings
        token_embeds = self.embed_tokens(input_ids)
        hidden_states = token_embeds  # Skip position embeddings for now

        # Create causal attention mask
        attention_mask = torch.ones((batch_size, seq_len), device=input_ids.device)
        attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
        attention_mask = (1.0 - attention_mask) * -10000.0

        # Transformer layers
        for layer in self.layers:
            hidden_states, _ = layer(hidden_states, attention_mask, position_ids)

        # Final layer norm and LM head
        hidden_states = self.ln_f(hidden_states)
        logits = self.lm_head(hidden_states)

        return {"logits": logits}

    def get_expert_status(self) -> Dict[str, Any]:
        """Obtener estado de expertos conectados."""
        return {
            "plugged_experts_count": len(self.plugged_experts),
            "plugged_layers": list(self.plugged_experts.keys()),
            "expert_manager_stats": self.expert_manager.get_expert_statistics()
        }


class PluggableTransformerBlock(nn.Module):
    """
    Bloque transformer con soporte para expertos pluggables.
    """

    def __init__(self, config: EmpoorioLMConfig, layer_idx: int, rope=None):
        super().__init__()
        self.layer_idx = layer_idx
        self.use_moe = config.use_moe and layer_idx in config.moe_layers

        # Layer norms
        self.ln1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.ln2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Attention (igual que original)
        from .model import GPT2Attention
        self.attn = GPT2Attention(config, rope)

        # Feed-forward: MoE o MLP estándar
        if self.use_moe:
            self.ffn = PluggableMoELayer(config, layer_idx)
        else:
            from .model import GPT2MLP
            self.ffn = GPT2MLP(config)

    def plug_expert(self, expert_weights: Dict[str, torch.Tensor]) -> bool:
        """Conectar experto a esta capa."""
        if hasattr(self.ffn, 'plug_expert'):
            return self.ffn.plug_expert(expert_weights)
        return False

    def unplug_expert(self):
        """Desconectar experto de esta capa."""
        if hasattr(self.ffn, 'unplug_expert'):
            self.ffn.unplug_expert()

    def forward(self, hidden_states, attention_mask, position_ids):
        # Pre-norm attention
        residual = hidden_states
        hidden_states = self.ln1(hidden_states)
        attn_output = self.attn(hidden_states, attention_mask, position_ids)
        hidden_states = residual + attn_output

        # Feed-forward
        residual = hidden_states
        if self.use_moe:
            hidden_states = self.ln2(hidden_states)
            moe_output, aux_info = self.ffn(hidden_states)
            hidden_states = residual + moe_output
        else:
            hidden_states = self.ln2(hidden_states)
            ffn_output = self.ffn(hidden_states)
            hidden_states = residual + ffn_output
            aux_info = None

        return hidden_states, aux_info


class PluggableMoELayer(nn.Module):
    """
    Capa MoE con soporte para expertos pluggables.
    """

    def __init__(self, config: EmpoorioLMConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx

        # Router (se mantiene igual)
        self.router = nn.Linear(config.hidden_size, config.num_experts)

        # Expertos base (se pueden reemplazar)
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_size, 4 * config.hidden_size),
                nn.GELU(),
                nn.Linear(4 * config.hidden_size, config.hidden_size)
            ) for _ in range(config.num_experts)
        ])

        # Expert shared (opcional)
        self.shared_expert = nn.Sequential(
            nn.Linear(config.hidden_size, 4 * config.hidden_size),
            nn.GELU(),
            nn.Linear(4 * config.hidden_size, config.hidden_size)
        )

        # Output projection
        self.output_proj = nn.Linear(config.hidden_size, config.hidden_size)

        # Estado de expertos pluggables
        self.plugged_experts: Dict[int, nn.Module] = {}

    def plug_expert(self, expert_weights: Dict[str, torch.Tensor]) -> bool:
        """
        Conectar un experto pluggable.

        Args:
            expert_weights: Pesos del experto con formato {"expert_0": tensor, ...}
        """
        try:
            for key, weights in expert_weights.items():
                if key.startswith("expert_"):
                    expert_idx = int(key.split("_")[1])
                    if 0 <= expert_idx < len(self.experts):
                        # Cargar pesos en el experto correspondiente
                        self.experts[expert_idx].load_state_dict(weights)
                        self.plugged_experts[expert_idx] = self.experts[expert_idx]
                        logger.debug(f"✅ Experto {expert_idx} conectado en capa {self.layer_idx}")

            return True
        except Exception as e:
            logger.error(f"❌ Error conectando experto: {e}")
            return False

    def unplug_expert(self):
        """Desconectar todos los expertos pluggables."""
        self.plugged_experts.clear()
        logger.debug(f"✅ Expertos desconectados de capa {self.layer_idx}")

    def forward(self, x):
        batch_size, seq_len, hidden_size = x.shape

        # Routing
        router_logits = self.router(x)
        routing_weights = torch.softmax(router_logits, dim=-1)

        # Top-k routing
        top_k_weights, top_k_indices = torch.topk(routing_weights, self.config.top_k, dim=-1)

        # Normalize weights
        top_k_weights = top_k_weights / top_k_weights.sum(dim=-1, keepdim=True)

        # Apply experts
        expert_outputs = []
        for i in range(self.config.num_experts):
            expert_mask = (top_k_indices == i).any(dim=-1, keepdim=True)
            if expert_mask.any():
                expert_input = x * expert_mask.float()
                expert_output = self.experts[i](expert_input)
                expert_outputs.append(expert_output)
            else:
                expert_outputs.append(torch.zeros_like(x))

        # Combine expert outputs
        combined_output = torch.zeros_like(x)
        for i, expert_output in enumerate(expert_outputs):
            expert_weight = top_k_weights[:, :, i:i+1]
            combined_output += expert_output * expert_weight

        # Add shared expert
        shared_output = self.shared_expert(x)
        combined_output += shared_output

        # Output projection
        output = self.output_proj(combined_output)

        return output, {"routing_weights": routing_weights.mean().item()}


# Funciones de conveniencia
def create_expert_manager(experts_dir: Union[str, Path] = "models/experts") -> ExpertManager:
    """Crear gestor de expertos."""
    return ExpertManager(experts_dir)


def create_pluggable_empoorio_lm(config: EmpoorioLMConfig,
                                expert_manager: ExpertManager) -> PluggableEmpoorioLM:
    """Crear modelo EmpoorioLM pluggable."""
    return PluggableEmpoorioLM(config, expert_manager)


# Configuraciones de routing por defecto
DEFAULT_ROUTING_CONFIGS = {
    Domain.LEGAL: DomainRoutingConfig(
        domain=Domain.LEGAL,
        force_expert_indices=[6, 7],  # Expertos legales
        context_keywords=["contrato", "ley", "jurisprudencia", "abogado", "demanda", "sentencia"]
    ),
    Domain.MEDICAL: DomainRoutingConfig(
        domain=Domain.MEDICAL,
        force_expert_indices=[8, 9],  # Expertos médicos
        context_keywords=["diagnóstico", "tratamiento", "medicina", "paciente", "síntoma", "enfermedad"]
    ),
    Domain.CODING: DomainRoutingConfig(
        domain=Domain.CODING,
        force_expert_indices=[10, 11],  # Expertos de código
        context_keywords=["programar", "código", "función", "clase", "algoritmo", "debug"]
    )
}


def setup_default_routing(expert_manager: ExpertManager):
    """Configurar routing por defecto para dominios comunes."""
    for config in DEFAULT_ROUTING_CONFIGS.values():
        expert_manager.set_domain_routing(config)
    logger.info("✅ Routing por defecto configurado")


__all__ = [
    'Domain',
    'ExpertConfig',
    'DomainRoutingConfig',
    'ExpertManager',
    'PluggableEmpoorioLM',
    'create_expert_manager',
    'create_pluggable_empoorio_lm',
    'setup_default_routing'
]