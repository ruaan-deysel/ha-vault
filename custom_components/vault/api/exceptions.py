"""Exceptions for the Vault API client."""

from __future__ import annotations


class VaultApiError(Exception):
    """Base exception for Vault API errors."""


class VaultConnectionError(VaultApiError):
    """Exception for connection/network errors (timeout, DNS, unreachable)."""


class VaultAuthenticationError(VaultApiError):
    """Exception for authentication failures (401, 403)."""
