"""Tests for the Vault API client."""

# ruff: noqa: SLF001, S108

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
    response.read = AsyncMock(return_value=b"")
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

    async def test_get_storage_non_list_raises(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /storage raises on a non-list response (protects entity pruning)."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        with pytest.raises(VaultApiError, match="Unexpected response for storage list"):
            await client.async_get_storage()

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

    async def test_get_jobs_non_list_raises(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test GET /jobs raises on a non-list response (protects entity pruning)."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        with pytest.raises(VaultApiError, match="Unexpected response for jobs list"):
            await client.async_get_jobs()

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
        """Test that API key headers are sent when an API key is configured."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={}))
        await auth_client.async_get_settings()
        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers is not None
        assert headers["X-API-Key"] == "test-key-123"
        assert headers["Authorization"] == "Bearer test-key-123"

    async def test_auth_header_sent_on_health_endpoint(
        self, auth_client: VaultApiClient, mock_session: MagicMock
    ) -> None:
        """Test that API key headers are also sent to health endpoint."""
        mock_session.request = AsyncMock(return_value=_mock_response(json_data={"status": "ok"}))
        await auth_client.async_get_health()
        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers is not None
        assert headers["X-API-Key"] == "test-key-123"
        assert headers["Authorization"] == "Bearer test-key-123"

    def test_tls_url(self, mock_session: MagicMock) -> None:
        """Test TLS client uses https scheme."""
        tls_client = VaultApiClient(host=MOCK_HOST, port=MOCK_PORT, session=mock_session, tls=True)
        assert tls_client.base_url == f"https://{MOCK_HOST}:{MOCK_PORT}"


class TestExpandedEndpointCoverage:
    """Cover the expanded endpoint surface added to the API client."""

    async def test_with_query_helper(self, client: VaultApiClient) -> None:
        """Test query helper handles empty and populated params."""
        assert client._with_query("/api/v1/test") == "/api/v1/test"
        assert client._with_query("/api/v1/test", {"a": 1, "b": None}) == "/api/v1/test?a=1"

    async def test_core_extended_methods(self, client: VaultApiClient) -> None:
        """Test additional core endpoint wrappers."""
        client._request = AsyncMock(return_value={"ok": True})

        await client.async_get_health_summary()
        await client.async_get_runner_status()
        await client.async_get_release_changelog()
        await client.async_get_release_latest()

        assert client._request.await_count == 4

    async def test_settings_extended_methods(self, client: VaultApiClient) -> None:
        """Test additional settings endpoint wrappers."""
        client._request = AsyncMock(return_value={"ok": True})

        await client.async_set_encryption({"passphrase": "abc"})
        await client.async_verify_encryption({"passphrase": "abc"})
        await client.async_get_encryption_passphrase()
        await client.async_get_staging_info()
        await client.async_set_staging_override({"path": "/tmp/stage"})
        await client.async_get_database_settings()
        await client.async_update_database_settings({"snapshot_path": "/tmp/db"})
        await client.async_test_discord_webhook({"webhook": "https://example.invalid"})
        await client.async_get_api_key_status()
        await client.async_get_api_key()
        await client.async_generate_api_key()
        await client.async_rotate_api_key()
        await client.async_revoke_api_key()

        assert client._request.await_count == 13

    async def test_download_diagnostics_uses_bytes(self, client: VaultApiClient) -> None:
        """Test diagnostics endpoint requests byte response mode."""
        client._request = AsyncMock(return_value=b"zip-bytes")
        result = await client.async_download_diagnostics()
        assert result == b"zip-bytes"
        call = client._request.await_args
        assert call is not None
        assert call.args[0] == "GET"
        assert call.args[1].endswith("/settings/diagnostics")
        assert call.kwargs["expect_json"] is False
        assert call.kwargs["expect_bytes"] is True

    async def test_storage_extended_methods(self, client: VaultApiClient) -> None:
        """Test additional storage endpoint wrappers."""
        client._request = AsyncMock(return_value={"ok": True})

        await client.async_create_storage({"name": "S3"})
        client._request.return_value = {"id": 1, "name": "Local", "type": "local"}
        destination = await client.async_get_storage_destination(1)
        assert destination.id == 1

        client._request.return_value = {"ok": True}
        await client.async_update_storage_destination(1, {"name": "Renamed"})
        await client.async_delete_storage_destination(1, force=True, delete_files=True)
        await client.async_health_check_storage(1)
        await client.async_capacity_check_storage(1)
        await client.async_close_storage_breaker(1)
        await client.async_scan_storage_orphans(1)
        await client.async_delete_storage_orphans(1, {"paths": ["a"]})
        await client.async_get_storage_dedup_stats(1)
        await client.async_run_storage_gc(1)
        await client.async_scan_storage(1)
        await client.async_import_storage(1)
        await client.async_restore_storage_database(1, {"confirm": True})
        await client.async_get_storage_jobs(1)
        await client.async_list_storage_files(1, path="vault")

        client._request.return_value = b"file-bytes"
        downloaded = await client.async_download_storage_file(1, path="vault/file.tar")
        assert downloaded == b"file-bytes"

    async def test_job_extended_methods(self, client: VaultApiClient) -> None:
        """Test additional job endpoint wrappers."""
        client._request = AsyncMock(return_value={"ok": True})

        await client.async_create_job({"name": "New Job"})
        await client.async_update_job(1, {"name": "Updated"})
        await client.async_delete_job(1)
        await client.async_get_next_runs()
        await client.async_get_next_run(1)

        client._request.return_value = [{"id": 1}]
        assert await client.async_get_retention_preview(1, limit=10) == [{"id": 1}]

        client._request.return_value = {}
        assert await client.async_get_retention_preview(1) == []

        client._request.return_value = "ok"
        await client.async_delete_restore_point(1, 10)

        client._request.return_value = {"files": []}
        assert await client.async_get_restore_point_contents(1, 10, item="myapp") == {"files": []}

        client._request.return_value = [{"name": "a"}]
        assert await client.async_get_restore_point_contents(1, 10, item="myapp") == [{"name": "a"}]

        client._request.return_value = None
        assert await client.async_get_restore_point_contents(1, 10, item="myapp") == []

        client._request.return_value = {"ok": True}
        await client.async_verify_restore_point(1, 10)

        client._request.return_value = [{"id": 1}]
        assert await client.async_get_restore_point_verify_runs(1, 10) == [{"id": 1}]

        client._request.return_value = {}
        assert await client.async_get_restore_point_verify_runs(1, 10) == []

        client._request.return_value = {"id": 99}
        await client.async_get_verify_run(1, 99)
        await client.async_cancel_job(1)

        client._request.return_value = [{"id": 1}]
        assert await client.async_get_stale_items(1) == [{"id": 1}]

        client._request.return_value = {}
        assert await client.async_get_stale_items(1) == []

        client._request.return_value = {"ok": True}
        await client.async_remove_stale_items(1, {"items": [1]})
        await client.async_delete_job_item(1, 2)

    async def test_activity_discovery_replication_and_recovery_methods(self, client: VaultApiClient) -> None:
        """Test remaining endpoint wrapper groups and list fallbacks."""
        client._request = AsyncMock(return_value={"ok": True})

        await client.async_purge_activity()
        await client.async_purge_history()
        await client.async_browse(path="/mnt")
        await client.async_path_exists(path="/mnt")

        client._request.return_value = [{"id": 1}]
        assert await client.async_get_containers() == [{"id": 1}]
        assert await client.async_get_vms() == [{"id": 1}]
        assert await client.async_get_folders() == [{"id": 1}]
        assert await client.async_get_plugins() == [{"id": 1}]
        assert await client.async_get_zfs_datasets() == [{"id": 1}]
        assert await client.async_get_presets_exclusions(image="x") == [{"id": 1}]
        assert await client.async_get_replication_sources() == [{"id": 1}]

        client._request.return_value = {}
        assert await client.async_get_containers() == []
        assert await client.async_get_vms() == []
        assert await client.async_get_folders() == []
        assert await client.async_get_plugins() == []
        assert await client.async_get_zfs_datasets() == []
        assert await client.async_get_presets_exclusions() == []
        assert await client.async_get_replication_sources() == []

        client._request.return_value = {"ok": True}
        await client.async_create_replication_source({"name": "source"})
        await client.async_test_replication_url({"url": "http://example.invalid"})
        await client.async_get_replication_source(1)
        await client.async_update_replication_source(1, {"name": "x"})
        await client.async_delete_replication_source(1)
        await client.async_test_replication_source(1)
        await client.async_sync_replication_source(1)

        client._request.return_value = [{"id": 1}]
        assert await client.async_get_replication_jobs(1) == [{"id": 1}]

        client._request.return_value = {}
        assert await client.async_get_replication_jobs(1) == []

        client._request.return_value = {"anomalies": [{"id": 1, "detector": "size_drift", "state": "open"}]}
        anomalies = await client.async_get_anomalies(limit=10)
        assert len(anomalies) == 1
        assert anomalies[0].id == 1
        assert anomalies[0].detector == "size_drift"
        assert anomalies[0].state == "open"

        client._request.return_value = {}
        assert await client.async_get_anomalies() == []

        client._request.return_value = {"anomalies": None}
        assert await client.async_get_anomalies() == []

        client._request.return_value = {"ok": True}
        await client.async_ack_bulk_anomalies({"ids": [1]})
        await client.async_get_anomaly(1)
        await client.async_ack_anomaly(1)
        await client.async_get_job_baseline(1)
        await client.async_get_destination_capacity_trajectory(1)
        await client.async_get_recovery_plan()

    async def test_request_returns_bytes_when_requested(self, client: VaultApiClient, mock_session: MagicMock) -> None:
        """Test internal _request helper returns raw bytes when expected."""
        resp = _mock_response(json_data=None)
        resp.read = AsyncMock(return_value=b"raw")
        mock_session.request = AsyncMock(return_value=resp)

        result = await client._request("GET", "/api/v1/file", expect_json=False, expect_bytes=True)
        assert result == b"raw"
