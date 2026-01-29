"""
API Module

This module provides REST and WebSocket APIs for interacting with
RAG systems, enabling real-time and synchronous communication
with RAG services.

APIs:
- RAGAPI: REST API for RAG operations
- WebSocketAPI: Real-time WebSocket API for streaming responses
"""

from .rag_api import RAGAPI
from .websocket_api import WebSocketAPI

__all__ = [
    "RAGAPI",
    "WebSocketAPI",
]