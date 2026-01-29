"""
Function Calling Integration for EmpoorioLM
Sistema completo de integración de function calling con parsing JSON y ejecución segura.
"""

import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging

from .registry import ToolRegistry, get_tool_registry
from .executor import ToolExecutor, ExecutionResult, create_tool_executor

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Representa una llamada a herramienta parseada."""
    tool_name: str
    parameters: Dict[str, Any]
    raw_call: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "raw_call": self.raw_call,
            "confidence": self.confidence
        }


@dataclass
class FunctionCallingResult:
    """Resultado completo del proceso de function calling."""
    original_response: str
    tool_calls: List[ToolCall]
    execution_results: List[ExecutionResult]
    final_response: str
    processing_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "original_response": self.original_response,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "execution_results": [er.to_dict() for er in self.execution_results],
            "final_response": self.final_response,
            "processing_time": self.processing_time
        }


class FunctionCallingProcessor:
    """
    Procesador completo de function calling para EmpoorioLM.

    Maneja:
    - Detección de tool calls en respuestas del modelo
    - Parsing JSON de llamadas a herramientas
    - Validación y ejecución segura
    - Formateo de resultados para el modelo
    """

    def __init__(self, registry: Optional[ToolRegistry] = None, executor: Optional[ToolExecutor] = None):
        self.registry = registry
        self.executor = executor
        self._tool_call_pattern = None

    async def initialize(self):
        """Inicializa componentes asíncronos."""
        if self.registry is None:
            self.registry = await get_tool_registry()

        if self.executor is None:
            self.executor = await create_tool_executor(self.registry)

    def set_tool_tokens(self, tool_call_token: str, tool_call_end_token: str):
        """Configura los tokens especiales para tool calls."""
        # Crear patrón regex para detectar tool calls
        escaped_start = re.escape(tool_call_token)
        escaped_end = re.escape(tool_call_end_token)
        self._tool_call_pattern = re.compile(
            f'{escaped_start}(.*?){escaped_end}',
            re.DOTALL
        )

    def detect_tool_calls(self, response: str) -> List[ToolCall]:
        """
        Detecta y parsea llamadas a herramientas en la respuesta del modelo.

        Args:
            response: Respuesta del modelo que puede contener tool calls

        Returns:
            Lista de ToolCall objects parseados
        """
        if not self._tool_call_pattern:
            logger.warning("Tool call pattern not configured")
            return []

        tool_calls = []

        # Buscar todas las coincidencias del patrón
        matches = self._tool_call_pattern.findall(response)

        for match in matches:
            try:
                # Intentar parsear como JSON
                tool_call_data = json.loads(match.strip())

                # Validar estructura
                if not isinstance(tool_call_data, dict):
                    logger.warning(f"Invalid tool call format: {match}")
                    continue

                # Extraer nombre de herramienta y parámetros
                tool_name = tool_call_data.get("name") or tool_call_data.get("tool_name")
                parameters = tool_call_data.get("parameters") or tool_call_data.get("args", {})

                if not tool_name:
                    logger.warning(f"Tool call missing name: {match}")
                    continue

                tool_call = ToolCall(
                    tool_name=tool_name,
                    parameters=parameters,
                    raw_call=match.strip()
                )

                tool_calls.append(tool_call)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call JSON: {match}, error: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing tool call: {match}, error: {e}")
                continue

        return tool_calls

    async def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ExecutionResult]:
        """
        Ejecuta una lista de llamadas a herramientas de forma segura.

        Args:
            tool_calls: Lista de ToolCall a ejecutar

        Returns:
            Lista de ExecutionResult con los resultados
        """
        if not self.executor:
            raise RuntimeError("Tool executor not initialized")

        execution_results = []

        # Ejecutar tool calls en paralelo para mejor rendimiento
        tasks = []
        for tool_call in tool_calls:
            task = self.executor.execute_tool(tool_call.tool_name, tool_call.parameters)
            tasks.append(task)

        # Esperar a que todas las ejecuciones terminen
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Error en la ejecución
                error_result = ExecutionResult(
                    tool_name=tool_calls[i].tool_name,
                    success=False,
                    result=None,
                    error=str(result)
                )
                execution_results.append(error_result)
            else:
                execution_results.append(result)

        return execution_results

    def format_execution_results(self, execution_results: List[ExecutionResult]) -> str:
        """
        Formatea los resultados de ejecución para que el modelo pueda procesarlos.

        Args:
            execution_results: Resultados de ejecución de herramientas

        Returns:
            String formateado con los resultados
        """
        formatted_results = []

        for result in execution_results:
            if result.success:
                result_str = f"✅ Tool '{result.tool_name}' executed successfully:\n{json.dumps(result.result, indent=2)}"
            else:
                result_str = f"❌ Tool '{result.tool_name}' failed:\n{result.error}"

            # Incluir métricas si están disponibles
            if result.execution_time > 0:
                result_str += f"\n⏱️ Execution time: {result.execution_time:.2f}s"

            formatted_results.append(result_str)

        return "\n\n".join(formatted_results)

    async def process_response_with_tools(self, model_response: str) -> FunctionCallingResult:
        """
        Procesa una respuesta completa del modelo que puede contener tool calls.

        Args:
            model_response: Respuesta completa del modelo

        Returns:
            FunctionCallingResult con todo el procesamiento
        """
        import time
        start_time = time.time()

        # Detectar tool calls
        tool_calls = self.detect_tool_calls(model_response)

        execution_results = []
        final_response = model_response

        if tool_calls:
            logger.info(f"Detected {len(tool_calls)} tool calls")

            # Ejecutar tool calls
            execution_results = await self.execute_tool_calls(tool_calls)

            # Formatear resultados para el modelo
            tool_results_text = self.format_execution_results(execution_results)

            # Crear respuesta final combinando respuesta original + resultados
            final_response = f"{model_response}\n\n--- Tool Execution Results ---\n\n{tool_results_text}"
        else:
            logger.debug("No tool calls detected in response")

        processing_time = time.time() - start_time

        return FunctionCallingResult(
            original_response=model_response,
            tool_calls=tool_calls,
            execution_results=execution_results,
            final_response=final_response,
            processing_time=processing_time
        )

    def create_tool_calling_prompt(self, base_prompt: str, available_tools: Optional[List[str]] = None) -> str:
        """
        Crea un prompt enriquecido con información de herramientas disponibles.

        Args:
            base_prompt: Prompt base del usuario
            available_tools: Lista de nombres de herramientas disponibles (opcional)

        Returns:
            Prompt enriquecido con información de tools
        """
        if not self.registry:
            return base_prompt

        # Obtener especificación JSON de herramientas
        tools_json = self.registry.get_available_tools_json()

        # Crear prompt con instrucciones de function calling
        tool_prompt = f"""
You are EmpoorioLM, an AI assistant with access to various tools. When you need to perform actions or get information that requires external tools, use the following format:

<tool_call>{{"name": "tool_name", "parameters": {{"param1": "value1", "param2": "value2"}}}}</tool_call>

Available tools:
{tools_json}

Guidelines:
1. Use tools when you need real-time information, calculations, or external actions
2. Always use valid JSON format for tool calls
3. You can make multiple tool calls in a single response if needed
4. After receiving tool results, provide a helpful response to the user

User query: {base_prompt}
"""

        return tool_prompt

    async def validate_tool_call(self, tool_call: ToolCall) -> Tuple[bool, Optional[str]]:
        """
        Valida que una tool call sea correcta y segura.

        Args:
            tool_call: ToolCall a validar

        Returns:
            Tuple de (is_valid, error_message)
        """
        # Verificar que la herramienta existe
        tool = self.registry.get_tool(tool_call.tool_name)
        if not tool:
            return False, f"Tool '{tool_call.tool_name}' not found"

        # Validar parámetros
        for param_name, param_value in tool_call.parameters.items():
            if param_name not in tool.parameters:
                return False, f"Unknown parameter '{param_name}' for tool '{tool_call.tool_name}'"

            param_def = tool.parameters[param_name]

            # Validar tipo básico
            expected_type = param_def.type
            if expected_type == "string" and not isinstance(param_value, str):
                return False, f"Parameter '{param_name}' must be string"
            elif expected_type == "number" and not isinstance(param_value, (int, float)):
                return False, f"Parameter '{param_name}' must be number"
            elif expected_type == "boolean" and not isinstance(param_value, bool):
                return False, f"Parameter '{param_name}' must be boolean"
            elif expected_type == "array" and not isinstance(param_value, list):
                return False, f"Parameter '{param_name}' must be array"
            elif expected_type == "object" and not isinstance(param_value, dict):
                return False, f"Parameter '{param_name}' must be object"

            # Validar enums
            if param_def.enum and param_value not in param_def.enum:
                return False, f"Parameter '{param_name}' must be one of {param_def.enum}"

        return True, None


async def create_function_calling_processor(registry: Optional[ToolRegistry] = None,
                                          executor: Optional[ToolExecutor] = None) -> FunctionCallingProcessor:
    """
    Factory function para crear un FunctionCallingProcessor.

    Args:
        registry: ToolRegistry a usar
        executor: ToolExecutor a usar

    Returns:
        FunctionCallingProcessor configurado
    """
    processor = FunctionCallingProcessor(registry, executor)
    await processor.initialize()
    return processor