"""Tests for Vault API exception hierarchy."""

from __future__ import annotations

from custom_components.vault.api.exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError


class TestExceptionHierarchy:
    """Test the Vault exception class hierarchy."""

    def test_base_exception(self) -> None:
        """Test VaultApiError is the base exception."""
        err = VaultApiError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)

    def test_connection_error_inherits_from_api_error(self) -> None:
        """Test VaultConnectionError inherits from VaultApiError."""
        err = VaultConnectionError("connection failed")
        assert isinstance(err, VaultApiError)
        assert isinstance(err, Exception)

    def test_authentication_error_inherits_from_api_error(self) -> None:
        """Test VaultAuthenticationError inherits from VaultApiError."""
        err = VaultAuthenticationError("auth failed")
        assert isinstance(err, VaultApiError)
        assert isinstance(err, Exception)

    def test_catch_api_error_catches_subclasses(self) -> None:
        """Test that catching VaultApiError catches all subclasses."""
        for exc_class in (VaultConnectionError, VaultAuthenticationError):
            try:
                raise exc_class("test")
            except VaultApiError:
                pass  # Expected
