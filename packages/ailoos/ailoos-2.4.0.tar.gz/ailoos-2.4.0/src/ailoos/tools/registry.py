"""
Tool Registry - Sistema de registro y gestión de herramientas para Function Calling
Permite a EmpoorioLM ejecutar herramientas externas de forma segura y estructurada.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Definición de un parámetro de herramienta."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class Tool:
    """Definición completa de una herramienta."""
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    function: Callable
    category: str = "general"
    version: str = "1.0.0"
    author: str = "AILOOS"
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la herramienta a diccionario para serialización."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                name: {
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default,
                    "enum": param.enum
                }
                for name, param in self.parameters.items()
            },
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "examples": self.examples
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], function: Callable) -> 'Tool':
        """Crea una herramienta desde un diccionario."""
        parameters = {}
        for name, param_data in data.get("parameters", {}).items():
            parameters[name] = ToolParameter(
                name=name,
                type=param_data["type"],
                description=param_data["description"],
                required=param_data.get("required", True),
                default=param_data.get("default"),
                enum=param_data.get("enum")
            )

        return cls(
            name=data["name"],
            description=data["description"],
            parameters=parameters,
            function=function,
            category=data.get("category", "general"),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "AILOOS"),
            tags=data.get("tags", []),
            examples=data.get("examples", [])
        )


class ToolRegistry:
    """
    Registro centralizado de herramientas para Function Calling.

    Gestiona el ciclo de vida completo de las herramientas:
    - Registro y validación
    - Descubrimiento por categorías/tags
    - Ejecución segura
    - Métricas de uso
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[str, List[str]] = {}
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def register_tool(self, tool: Tool) -> bool:
        """
        Registra una nueva herramienta en el registry.

        Args:
            tool: Instancia de Tool a registrar

        Returns:
            bool: True si se registró exitosamente
        """
        async with self._lock:
            if tool.name in self.tools:
                logger.warning(f"Tool {tool.name} already registered, overwriting")

            # Validar herramienta
            if not self._validate_tool(tool):
                logger.error(f"Tool {tool.name} validation failed")
                return False

            # Registrar
            self.tools[tool.name] = tool

            # Actualizar categorías
            if tool.category not in self.categories:
                self.categories[tool.category] = []
            if tool.name not in self.categories[tool.category]:
                self.categories[tool.category].append(tool.name)

            # Inicializar métricas
            self.metrics[tool.name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "avg_execution_time": 0.0,
                "last_used": None
            }

            logger.info(f"✅ Tool registered: {tool.name} (category: {tool.category})")
            return True

    async def unregister_tool(self, tool_name: str) -> bool:
        """Elimina una herramienta del registro."""
        async with self._lock:
            if tool_name not in self.tools:
                logger.warning(f"Tool {tool_name} not found")
                return False

            tool = self.tools[tool_name]

            # Remover de categorías
            if tool.category in self.categories and tool_name in self.categories[tool.category]:
                self.categories[tool.category].remove(tool_name)
                if not self.categories[tool.category]:
                    del self.categories[tool.category]

            # Remover herramienta y métricas
            del self.tools[tool_name]
            del self.metrics[tool_name]

            logger.info(f"✅ Tool unregistered: {tool_name}")
            return True

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Obtiene una herramienta por nombre."""
        return self.tools.get(tool_name)

    def list_tools(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Tool]:
        """Lista herramientas con filtros opcionales."""
        tools = list(self.tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return tools

    def get_available_tools_json(self) -> str:
        """
        Genera la especificación JSON de herramientas disponibles para el modelo.
        Este JSON se incluye en el prompt del modelo para que sepa qué herramientas puede usar.
        """
        tools_spec = []
        for tool in self.tools.values():
            tool_spec = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }

            for param_name, param in tool.parameters.items():
                tool_spec["parameters"]["properties"][param_name] = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    tool_spec["parameters"]["properties"][param_name]["enum"] = param.enum
                if param.default is not None:
                    tool_spec["parameters"]["properties"][param_name]["default"] = param.default

                if param.required:
                    tool_spec["parameters"]["required"].append(param_name)

            tools_spec.append(tool_spec)

        return json.dumps(tools_spec, indent=2)

    def get_categories(self) -> Dict[str, List[str]]:
        """Obtiene el mapa de categorías a herramientas."""
        return self.categories.copy()

    def get_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene métricas de uso de herramientas."""
        if tool_name:
            return self.metrics.get(tool_name, {})
        return self.metrics.copy()

    def _validate_tool(self, tool: Tool) -> bool:
        """Valida que una herramienta esté correctamente definida."""
        if not tool.name or not tool.description:
            return False

        if not tool.parameters and not callable(tool.function):
            return False

        # Validar parámetros
        for param_name, param in tool.parameters.items():
            if not param.name or not param.type or not param.description:
                return False

        return True

    async def update_metrics(self, tool_name: str, execution_time: float, success: bool):
        """Actualiza métricas de uso de una herramienta."""
        if tool_name not in self.metrics:
            return

        metrics = self.metrics[tool_name]
        metrics["calls"] += 1

        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1

        # Actualizar tiempo promedio de ejecución
        if metrics["calls"] == 1:
            metrics["avg_execution_time"] = execution_time
        else:
            metrics["avg_execution_time"] = (
                (metrics["avg_execution_time"] * (metrics["calls"] - 1)) + execution_time
            ) / metrics["calls"]

        metrics["last_used"] = asyncio.get_event_loop().time()


# Instancia global del registry
tool_registry = ToolRegistry()


async def get_tool_registry() -> ToolRegistry:
    """Obtiene la instancia global del tool registry."""
    return tool_registry