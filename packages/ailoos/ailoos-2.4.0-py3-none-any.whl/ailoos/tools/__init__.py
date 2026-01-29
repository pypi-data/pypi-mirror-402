"""
AILOOS Tools Package - Function Calling System
Sistema completo de herramientas para EmpoorioLM con capacidad de function calling.
"""

# Importaciones directas para evitar dependencias circulares
try:
    from .registry import ToolRegistry, Tool, ToolParameter
    from .executor import ToolExecutor, ExecutionResult, ExecutionLimits
    from .builtin_tools import CalculatorTool, WebSearchTool, DateTimeTool, FileSystemTool
    from .function_calling import FunctionCallingProcessor, ToolCall, FunctionCallingResult, create_function_calling_processor

    __all__ = [
        'ToolRegistry',
        'Tool',
        'ToolParameter',
        'ToolExecutor',
        'ExecutionResult',
        'ExecutionLimits',
        'CalculatorTool',
        'WebSearchTool',
        'DateTimeTool',
        'FileSystemTool',
        'FunctionCallingProcessor',
        'ToolCall',
        'FunctionCallingResult',
        'create_function_calling_processor'
    ]

except ImportError as e:
    # Fallback para desarrollo
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Tools package import failed: {e}")
    logger.warning("Using fallback mode - some features may not be available")

    # Definiciones básicas para compatibilidad
    class ToolRegistry:
        pass

    class Tool:
        pass

    class ToolExecutor:
        pass

    __all__ = ['ToolRegistry', 'Tool', 'ToolExecutor']