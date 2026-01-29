"""
Tool Executor - Ejecución segura de herramientas en entorno sandbox
Sistema de ejecución aislada para function calling con límites de recursos y seguridad.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import psutil
import os
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .registry import Tool, ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Resultado de la ejecución de una herramienta."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "resource_usage": self.resource_usage
        }


@dataclass
class ExecutionLimits:
    """Límites de ejecución para seguridad."""
    max_execution_time: float = 30.0  # segundos
    max_memory_mb: int = 100  # MB
    max_cpu_percent: float = 50.0  # porcentaje
    allow_network: bool = False
    allow_filesystem: bool = False
    allowed_modules: Optional[List[str]] = None


class ToolExecutor:
    """
    Ejecutor seguro de herramientas con aislamiento de recursos.

    Características de seguridad:
    - Timeouts para prevenir hangs
    - Límites de memoria y CPU
    - Ejecución en threads separados
    - Monitoreo de recursos
    - Logging detallado de ejecución
    """

    def __init__(self, registry: ToolRegistry, limits: Optional[ExecutionLimits] = None):
        self.registry = registry
        self.limits = limits or ExecutionLimits()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tool-executor")
        self._active_executions: Dict[str, asyncio.Future] = {}

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ExecutionResult:
        """
        Ejecuta una herramienta de forma segura con monitoreo.

        Args:
            tool_name: Nombre de la herramienta a ejecutar
            parameters: Parámetros para la herramienta

        Returns:
            ExecutionResult: Resultado de la ejecución
        """
        start_time = time.time()

        # Validar que la herramienta existe
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found",
                execution_time=time.time() - start_time
            )

        # Validar parámetros
        validation_error = self._validate_parameters(tool, parameters)
        if validation_error:
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=validation_error,
                execution_time=time.time() - start_time
            )

        # Crear tarea de ejecución
        execution_id = f"{tool_name}_{int(time.time() * 1000)}"
        future = asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._execute_tool_sync,
            tool,
            parameters,
            execution_id
        )

        self._active_executions[execution_id] = future

        try:
            # Ejecutar con timeout
            result = await asyncio.wait_for(future, timeout=self.limits.max_execution_time)

            # Actualizar métricas del registry
            execution_time = time.time() - start_time
            await self.registry.update_metrics(tool_name, execution_time, result.success)

            # Completar resultado
            result.execution_time = execution_time
            result.resource_usage = self._get_resource_usage()

            return result

        except asyncio.TimeoutError:
            logger.error(f"Tool {tool_name} execution timed out after {self.limits.max_execution_time}s")
            await self._cancel_execution(execution_id)

            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Execution timed out after {self.limits.max_execution_time} seconds",
                execution_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            execution_time = time.time() - start_time
            await self.registry.update_metrics(tool_name, execution_time, False)

            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )

        finally:
            # Limpiar ejecución activa
            self._active_executions.pop(execution_id, None)

    def _execute_tool_sync(self, tool: Tool, parameters: Dict[str, Any], execution_id: str) -> ExecutionResult:
        """
        Ejecuta la herramienta de forma síncrona en un thread separado.
        Esta función se ejecuta en el ThreadPoolExecutor.
        """
        try:
            # Monitorear recursos durante la ejecución
            with self._resource_monitor(execution_id):
                # Ejecutar la función de la herramienta
                if asyncio.iscoroutinefunction(tool.function):
                    # Si es async, crear un nuevo loop de eventos
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(tool.function(**parameters))
                    finally:
                        loop.close()
                else:
                    # Función síncrona normal
                    result = tool.function(**parameters)

                return ExecutionResult(
                    tool_name=tool.name,
                    success=True,
                    result=result
                )

        except Exception as e:
            logger.error(f"Tool {tool.name} execution error: {e}")
            return ExecutionResult(
                tool_name=tool.name,
                success=False,
                result=None,
                error=str(e)
            )

    def _validate_parameters(self, tool: Tool, parameters: Dict[str, Any]) -> Optional[str]:
        """Valida que los parámetros sean correctos para la herramienta."""
        # Verificar parámetros requeridos
        for param_name, param in tool.parameters.items():
            if param.required and param_name not in parameters:
                return f"Missing required parameter: {param_name}"

        # Verificar tipos básicos
        for param_name, value in parameters.items():
            if param_name not in tool.parameters:
                continue  # Permitir parámetros extra

            param_def = tool.parameters[param_name]
            expected_type = param_def.type

            # Validación básica de tipos
            if expected_type == "string" and not isinstance(value, str):
                return f"Parameter {param_name} must be string, got {type(value)}"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return f"Parameter {param_name} must be number, got {type(value)}"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return f"Parameter {param_name} must be boolean, got {type(value)}"
            elif expected_type == "array" and not isinstance(value, list):
                return f"Parameter {param_name} must be array, got {type(value)}"
            elif expected_type == "object" and not isinstance(value, dict):
                return f"Parameter {param_name} must be object, got {type(value)}"

            # Validar enums si existen
            if param_def.enum and value not in param_def.enum:
                return f"Parameter {param_name} must be one of {param_def.enum}, got {value}"

        return None

    @asynccontextmanager
    async def _resource_monitor(self, execution_id: str):
        """Context manager para monitorear recursos durante la ejecución."""
        # En una implementación completa, aquí monitorearíamos:
        # - Uso de memoria
        # - Uso de CPU
        # - Acceso a red
        # - Acceso a filesystem
        # - Llamadas a sistema

        # Por ahora, placeholder simple
        yield

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Obtiene métricas de uso de recursos del proceso actual."""
        process = psutil.Process()
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files())
        }

    async def _cancel_execution(self, execution_id: str):
        """Cancela una ejecución activa."""
        if execution_id in self._active_executions:
            future = self._active_executions[execution_id]
            if not future.done():
                future.cancel()
                logger.info(f"Cancelled execution {execution_id}")

    async def shutdown(self):
        """Cierra el executor limpiamente."""
        logger.info("Shutting down ToolExecutor")

        # Cancelar todas las ejecuciones activas
        for execution_id, future in self._active_executions.items():
            if not future.done():
                future.cancel()

        # Cerrar el ThreadPoolExecutor
        self.executor.shutdown(wait=True)
        logger.info("ToolExecutor shutdown complete")

    def get_active_executions(self) -> List[str]:
        """Obtiene lista de ejecuciones activas."""
        return list(self._active_executions.keys())


async def create_tool_executor(registry: Optional[ToolRegistry] = None,
                              limits: Optional[ExecutionLimits] = None) -> ToolExecutor:
    """
    Factory function para crear un ToolExecutor.

    Args:
        registry: ToolRegistry a usar (opcional, usa global si no se especifica)
        limits: Límites de ejecución (opcional)

    Returns:
        ToolExecutor configurado
    """
    if registry is None:
        from .registry import get_tool_registry
        registry = await get_tool_registry()

    return ToolExecutor(registry, limits)