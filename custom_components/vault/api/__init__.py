"""
API package for vault.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    VaultApiClientError (base)
    ├── VaultApiClientCommunicationError (network/timeout)
    └── VaultApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    VaultApiClient,
    VaultApiClientAuthenticationError,
    VaultApiClientCommunicationError,
    VaultApiClientError,
)

__all__ = [
    "VaultApiClient",
    "VaultApiClientAuthenticationError",
    "VaultApiClientCommunicationError",
    "VaultApiClientError",
]
