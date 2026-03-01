"""Vault API client package.

Provides:
- VaultApiClient: Async REST client for all Vault endpoints.
- VaultWebSocketClient: Persistent WebSocket connection for real-time events.
- Pydantic v2 models for typed API responses.
- Exception hierarchy for structured error handling.
"""

from .client import VaultApiClient
from .exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError
from .websocket import VaultWebSocketClient

__all__ = [
    "VaultApiClient",
    "VaultApiError",
    "VaultAuthenticationError",
    "VaultConnectionError",
    "VaultWebSocketClient",
]
