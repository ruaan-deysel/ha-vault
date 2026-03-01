"""Tests for the Vault API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.vault.api.client import VaultApiClient
from custom_components.vault.api.exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError
from custom_components.vault.api.models import (
    ActivityEntry,
    AuthStatus,
    BackupJob,
    EncryptionStatus,
    HealthStatus,
    JobDetail,
    JobRun,
    RestorePoint,
    Settings,
    StorageDestination,
    StorageTestResult,
)

MOCK_HOST = "192.168.1.100"
MOCK_PORT = 24085
BASE_URL = f"http://{MOCK_HOST}:{MOCK_PORT}"


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp session."""
    return MagicMock(spec=aiohttp.ClientSession)


@pytest.fixture
def client(mock_session: MagicMock) -> VaultApiClient:
    """Create a VaultApiClient with a mock session."""
    return VaultApiClient(host=MOCK_HOST, port=MOCK_PORT, session=mock_session)


def _mock_response(*, status: int = 200, json_data: dict | list | None = None, text: str = "") -> AsyncMock:
    """Create a mock response object."""
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data)
    response.text = AsyncMock(return_value=text)
    return response


class TestClientInit:
    """Test client initialization."""

    def test_base_url(self, client: VaultApiClient) -> None:
        """Test base_url property."""
        assert client.base_url == BASE_URL


class TestHealthEndpoints:
    """Test health-related endpoints."""

    async def test_get_health(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /health."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"status": "ok", "version": "1.0.0"}))
        result = await client.async_get_health()
        assert isinstance(result, HealthStatus)
        assert result.status == "ok"
        assert result.version == "1.0.0"

    async def test_ping_success(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /ping success."""
        mock_session.request = AsyncMock(return_value=_mock_response(status=200, json_data=None, text="pong"))
        result = await client.async_ping()
        assert result is True

    async def test_ping_failure(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /ping failure returns False."""
        mock_session.request = AsyncMock(return_value=_mock_response(status=500, text="error"))
        result = await client.async_ping()
        assert result is False


class TestSettingsEndpoints:
    """Test settings-related endpoints."""

    async def test_get_settings(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /settings."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_settings()
        assert isinstance(result, Settings)

    async def test_update_settings(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test PUT /settings."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"theme": "dark"}))
        result = await client.async_update_settings({"theme": "dark"})
        assert isinstance(result, Settings)

    async def test_get_encryption_status(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /settings/encryption."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"encryption_enabled": True}))
        result = await client.async_get_encryption_status()
        assert isinstance(result, EncryptionStatus)
        assert result.encryption_enabled is True


class TestStorageEndpoints:
    """Test storage-related endpoints."""

    async def test_get_storage(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /storage."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data=[
                    {"id": 1, "name": "Local", "type": "local"},
                ]
            )
        )
        result = await client.async_get_storage()
        assert len(result) == 1
        assert isinstance(result[0], StorageDestination)

    async def test_get_storage_empty(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /storage with non-list response."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_storage()
        assert result == []

    async def test_test_storage(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test POST /storage/{id}/test."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"success": True, "error": ""}))
        result = await client.async_test_storage(1)
        assert isinstance(result, StorageTestResult)
        assert result.success is True


class TestJobEndpoints:
    """Test job-related endpoints."""

    async def test_get_jobs(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data=[
                    {"id": 1, "name": "Daily Backup"},
                ]
            )
        )
        result = await client.async_get_jobs()
        assert len(result) == 1
        assert isinstance(result[0], BackupJob)

    async def test_get_jobs_empty(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs with non-list response."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_jobs()
        assert result == []

    async def test_get_job(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs/{id}."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data={
                    "job": {"id": 1, "name": "Test"},
                    "items": [{"id": 1, "job_id": 1, "item_type": "container", "item_name": "app"}],
                }
            )
        )
        result = await client.async_get_job(1)
        assert isinstance(result, JobDetail)
        assert len(result.items) == 1

    async def test_run_job(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test POST /jobs/{id}/run."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"status": "started"}))
        result = await client.async_run_job(1)
        assert result["status"] == "started"

    async def test_get_job_history(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs/{id}/history."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data=[
                    {"id": 1, "job_id": 1, "status": "completed"},
                ]
            )
        )
        result = await client.async_get_job_history(1)
        assert len(result) == 1
        assert isinstance(result[0], JobRun)

    async def test_get_restore_points(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs/{id}/restore-points."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data=[
                    {"id": 1, "job_id": 1},
                ]
            )
        )
        result = await client.async_get_restore_points(1)
        assert len(result) == 1
        assert isinstance(result[0], RestorePoint)

    async def test_restore(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test POST /jobs/{id}/restore."""
        payload = {"restore_point_id": 1, "item_name": "app", "item_type": "container"}
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"status": "started"}))
        result = await client.async_restore(1, payload)
        assert result["status"] == "started"


class TestActivityEndpoints:
    """Test activity-related endpoints."""

    async def test_get_activity(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /activity."""
        mock_session.request = AsyncMock(
            return_value=_mock_response(
                json_data=[
                    {"id": 1, "message": "Backup done"},
                ]
            )
        )
        result = await client.async_get_activity()
        assert len(result) == 1
        assert isinstance(result[0], ActivityEntry)

    async def test_get_activity_empty(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /activity with non-list response."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_activity()
        assert result == []


class TestErrorHandling:
    """Test error handling in the API client."""

    async def test_timeout_raises_connection_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test timeout raises VaultConnectionError."""
        mock_session.request = AsyncMock(side_effect=TimeoutError())
        with pytest.raises(VaultConnectionError, match="Timeout"):
            await client.async_get_health()

    async def test_client_error_raises_connection_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test aiohttp ClientError raises VaultConnectionError."""
        mock_session.request = AsyncMock(side_effect=aiohttp.ClientError("connection refused"))
        with pytest.raises(VaultConnectionError, match="Error connecting"):
            await client.async_get_health()

    async def test_401_raises_auth_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test 401 response raises VaultAuthenticationError."""
        mock_session.request = AsyncMock(return_value=_mock_response(status=401))
        with pytest.raises(VaultAuthenticationError, match="Authentication failed"):
            await client.async_get_health()

    async def test_403_raises_auth_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test 403 response raises VaultAuthenticationError."""
        mock_session.request = AsyncMock(return_value=_mock_response(status=403))
        with pytest.raises(VaultAuthenticationError, match="Authentication failed"):
            await client.async_get_health()

    async def test_500_raises_api_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test 500 response raises VaultApiError."""
        mock_session.request = AsyncMock(return_value=_mock_response(status=500, text="Internal Server Error"))
        with pytest.raises(VaultApiError, match="Vault API error"):
            await client.async_get_health()

    async def test_invalid_json_raises_api_error(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test invalid JSON response raises VaultApiError."""
        resp = _mock_response(status=200)
        resp.json = AsyncMock(side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock()))
        mock_session.request = AsyncMock(return_value=resp)
        with pytest.raises(VaultApiError, match="Invalid JSON"):
            await client.async_get_health()


class TestAuthEndpoints:
    """Test auth-related endpoints."""

    async def test_get_auth_status(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /auth/status."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"auth_required": True}))
        result = await client.async_get_auth_status()
        assert isinstance(result, AuthStatus)
        assert result.auth_required is True


class TestNonListFallbacks:
    """Test that endpoints returning non-list data fall back to empty lists."""

    async def test_get_job_history_non_list(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs/{id}/history with non-list response."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_job_history(1)
        assert result == []

    async def test_get_restore_points_non_list(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs/{id}/restore-points with non-list response."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        result = await client.async_get_restore_points(1)
        assert result == []


class TestAuthHeaders:
    """Test authentication header injection."""

    @pytest.fixture
    def auth_client(self, mock_session: MagicMock) -> VaultApiClient:
        """Create a VaultApiClient with an API key."""
        return VaultApiClient(host=MOCK_HOST, port=MOCK_PORT, session=mock_session, api_key="test-key-123")

    async def test_auth_header_sent_on_protected_endpoint(
        self, auth_client: VaultApiClient, mock_session: MagicMock
    ) -> None:
        """Test that Authorization header is sent on non-public endpoints."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        await auth_client.async_get_settings()
        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers is not None
        assert headers["Authorization"] == "Bearer test-key-123"

    async def test_no_auth_header_on_public_endpoint(
        self, auth_client: VaultApiClient, mock_session: MagicMock
    ) -> None:
        """Test that Authorization header is NOT sent on public endpoints."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"status": "ok"}))
        await auth_client.async_get_health()
        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        # No headers or empty headers for public paths
        assert headers is None

    def test_tls_url(self, mock_session: MagicMock) -> None:
        """Test TLS client uses https scheme."""
        tls_client = VaultApiClient(host=MOCK_HOST, port=MOCK_PORT, session=mock_session, tls=True)
        assert tls_client.base_url == f"https://{MOCK_HOST}:{MOCK_PORT}"
