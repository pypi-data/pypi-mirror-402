"""
Built-in Tools - Herramientas básicas incluidas con AILOOS
Conjunto de herramientas esenciales para function calling.
"""

import math
import datetime
import os
import json
from typing import Dict, Any, List, Optional
import logging

from .registry import Tool, ToolParameter

logger = logging.getLogger(__name__)


class CalculatorTool:
    """Herramienta de calculadora básica con operaciones matemáticas."""

    @staticmethod
    def execute(operation: str, x: float, y: Optional[float] = None) -> Dict[str, Any]:
        """
        Ejecuta operaciones matemáticas básicas.

        Args:
            operation: Operación a realizar (+, -, *, /, sqrt, pow, sin, cos, tan, log, exp)
            x: Primer operando
            y: Segundo operando (opcional para operaciones unarias)

        Returns:
            Dict con resultado y metadatos
        """
        try:
            if operation == "+":
                result = x + y
            elif operation == "-":
                result = x - y
            elif operation == "*":
                result = x * y
            elif operation == "/":
                if y == 0:
                    raise ValueError("Division by zero")
                result = x / y
            elif operation == "sqrt":
                if x < 0:
                    raise ValueError("Cannot take square root of negative number")
                result = math.sqrt(x)
            elif operation == "pow":
                result = math.pow(x, y)
            elif operation == "sin":
                result = math.sin(math.radians(x))
            elif operation == "cos":
                result = math.cos(math.radians(x))
            elif operation == "tan":
                result = math.tan(math.radians(x))
            elif operation == "log":
                if x <= 0:
                    raise ValueError("Cannot take logarithm of non-positive number")
                result = math.log(x)
            elif operation == "exp":
                result = math.exp(x)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return {
                "result": result,
                "operation": operation,
                "inputs": [x, y] if y is not None else [x]
            }

        except Exception as e:
            raise ValueError(f"Calculator error: {str(e)}")


# Definición de la herramienta Calculator
calculator_tool = Tool(
    name="calculator",
    description="Perform basic mathematical calculations including arithmetic, trigonometry, and exponential functions",
    parameters={
        "operation": ToolParameter(
            name="operation",
            type="string",
            description="Mathematical operation to perform",
            required=True,
            enum=["+", "-", "*", "/", "sqrt", "pow", "sin", "cos", "tan", "log", "exp"]
        ),
        "x": ToolParameter(
            name="x",
            type="number",
            description="First operand",
            required=True
        ),
        "y": ToolParameter(
            name="y",
            type="number",
            description="Second operand (optional for unary operations)",
            required=False
        )
    },
    function=CalculatorTool.execute,
    category="mathematics",
    tags=["math", "calculator", "arithmetic"],
    examples=[
        {"operation": "+", "x": 5, "y": 3},
        {"operation": "sqrt", "x": 16},
        {"operation": "sin", "x": 45}
    ]
)


class DateTimeTool:
    """Herramienta para operaciones de fecha y hora."""

    @staticmethod
    def execute(operation: str, timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecuta operaciones relacionadas con fecha y hora.

        Args:
            operation: Operación (now, today, weekday, timestamp)
            timezone: Zona horaria (opcional)

        Returns:
            Dict con información de fecha/hora
        """
        try:
            now = datetime.datetime.now()

            if operation == "now":
                result = now.strftime("%Y-%m-%d %H:%M:%S")
            elif operation == "today":
                result = now.strftime("%Y-%m-%d")
            elif operation == "weekday":
                result = now.strftime("%A")
            elif operation == "timestamp":
                result = now.timestamp()
            elif operation == "iso":
                result = now.isoformat()
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return {
                "result": result,
                "operation": operation,
                "timezone": timezone or "local",
                "timestamp": now.timestamp()
            }

        except Exception as e:
            raise ValueError(f"DateTime error: {str(e)}")


# Definición de la herramienta DateTime
datetime_tool = Tool(
    name="datetime",
    description="Get current date and time information",
    parameters={
        "operation": ToolParameter(
            name="operation",
            type="string",
            description="Date/time operation to perform",
            required=True,
            enum=["now", "today", "weekday", "timestamp", "iso"]
        ),
        "timezone": ToolParameter(
            name="timezone",
            type="string",
            description="Timezone (optional, defaults to local)",
            required=False
        )
    },
    function=DateTimeTool.execute,
    category="utilities",
    tags=["time", "date", "datetime"],
    examples=[
        {"operation": "now"},
        {"operation": "today"},
        {"operation": "weekday"}
    ]
)


class WebSearchTool:
    """Herramienta de búsqueda web (simulada para desarrollo)."""

    @staticmethod
    def execute(query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Realiza una búsqueda web (versión de desarrollo con datos mock).

        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados

        Returns:
            Dict con resultados de búsqueda simulados
        """
        # En producción, esto se conectaría a APIs reales como Google, Bing, etc.
        # Para desarrollo, devolvemos resultados simulados

        mock_results = [
            {
                "title": f"Result 1 for '{query}'",
                "url": f"https://example.com/result1?q={query}",
                "snippet": f"This is a mock search result for the query '{query}'. In production, this would be real search data."
            },
            {
                "title": f"Result 2 for '{query}'",
                "url": f"https://example.com/result2?q={query}",
                "snippet": f"Another mock result showing information about '{query}' from web sources."
            }
        ]

        return {
            "query": query,
            "results": mock_results[:max_results],
            "total_results": len(mock_results),
            "search_engine": "mock_search",
            "note": "This is mock data for development. In production, connects to real search APIs."
        }


# Definición de la herramienta WebSearch
web_search_tool = Tool(
    name="web_search",
    description="Search the web for information (development version with mock data)",
    parameters={
        "query": ToolParameter(
            name="query",
            type="string",
            description="Search query",
            required=True
        ),
        "max_results": ToolParameter(
            name="max_results",
            type="number",
            description="Maximum number of results to return",
            required=False,
            default=5
        )
    },
    function=WebSearchTool.execute,
    category="search",
    tags=["web", "search", "information"],
    examples=[
        {"query": "Python programming"},
        {"query": "machine learning", "max_results": 3}
    ]
)


class FileSystemTool:
    """Herramienta para operaciones básicas del sistema de archivos."""

    @staticmethod
    def execute(operation: str, path: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecuta operaciones básicas del sistema de archivos.

        Args:
            operation: Operación (list, read, write, exists, mkdir)
            path: Ruta del archivo/directorio
            content: Contenido para escribir (solo para write)

        Returns:
            Dict con resultado de la operación
        """
        try:
            if operation == "list":
                if not path:
                    path = "."
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return {
                        "operation": "list",
                        "path": path,
                        "items": items,
                        "count": len(items)
                    }
                else:
                    raise ValueError(f"Path is not a directory: {path}")

            elif operation == "read":
                if not path:
                    raise ValueError("Path required for read operation")
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    return {
                        "operation": "read",
                        "path": path,
                        "content": file_content,
                        "size": len(file_content)
                    }
                else:
                    raise ValueError(f"File not found: {path}")

            elif operation == "write":
                if not path or content is None:
                    raise ValueError("Path and content required for write operation")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "operation": "write",
                    "path": path,
                    "size": len(content),
                    "success": True
                }

            elif operation == "exists":
                if not path:
                    raise ValueError("Path required for exists operation")
                exists = os.path.exists(path)
                return {
                    "operation": "exists",
                    "path": path,
                    "exists": exists,
                    "type": "file" if os.path.isfile(path) else "directory" if os.path.isdir(path) else "unknown"
                }

            elif operation == "mkdir":
                if not path:
                    raise ValueError("Path required for mkdir operation")
                os.makedirs(path, exist_ok=True)
                return {
                    "operation": "mkdir",
                    "path": path,
                    "success": True
                }

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            raise ValueError(f"FileSystem error: {str(e)}")


# Definición de la herramienta FileSystem
filesystem_tool = Tool(
    name="filesystem",
    description="Perform basic file system operations",
    parameters={
        "operation": ToolParameter(
            name="operation",
            type="string",
            description="File system operation to perform",
            required=True,
            enum=["list", "read", "write", "exists", "mkdir"]
        ),
        "path": ToolParameter(
            name="path",
            type="string",
            description="File or directory path",
            required=False
        ),
        "content": ToolParameter(
            name="content",
            type="string",
            description="Content to write (for write operation)",
            required=False
        )
    },
    function=FileSystemTool.execute,
    category="system",
    tags=["files", "filesystem", "io"],
    examples=[
        {"operation": "list", "path": "."},
        {"operation": "read", "path": "example.txt"},
        {"operation": "write", "path": "output.txt", "content": "Hello World"}
    ]
)


# Función para registrar todas las herramientas built-in
async def register_builtin_tools(registry):
    """Registra todas las herramientas built-in en el registry."""
    tools = [calculator_tool, datetime_tool, web_search_tool, filesystem_tool]

    for tool in tools:
        success = await registry.register_tool(tool)
        if success:
            logger.info(f"✅ Registered built-in tool: {tool.name}")
        else:
            logger.error(f"❌ Failed to register tool: {tool.name}")

    return tools