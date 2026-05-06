"""Async API client for the Vault backup manager."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError
from .models import (
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

API_BASE = "/api/v1"


class VaultApiClient:
    """Async API client for Vault on Unraid.

    Wraps all REST endpoints at /api/v1/*.
    Accepts an aiohttp.ClientSession from Home Assistant — never creates its own.
    """

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
        *,
        api_key: str | None = None,
        tls: bool = False,
    ) -> None:
        """Initialize the API client.

        Args:
            host: Hostname or IP of the Vault instance.
            port: Port number of the Vault API.
            session: aiohttp session provided by Home Assistant.
            api_key: Optional API key for authentication.
            tls: Whether to use HTTPS instead of HTTP.
        """
        scheme = "https" if tls else "http"
        self._base_url = f"{scheme}://{host}:{port}"
        self._session = session
        self._api_key = api_key

    @property
    def base_url(self) -> str:
        """Return the base URL of the Vault instance."""
        return self._base_url

    # --- Auth ---

    async def async_get_auth_status(self) -> AuthStatus:
        """GET /api/v1/auth/status — check if auth is required (public endpoint)."""
        data = await self._request("GET", f"{API_BASE}/auth/status")
        return AuthStatus.model_validate(data)

    # --- Health / Ping ---

    async def async_get_health(self) -> HealthStatus:
        """GET /api/v1/health — health check + version."""
        data = await self._request("GET", f"{API_BASE}/health")
        return HealthStatus.model_validate(data)

    async def async_ping(self) -> bool:
        """GET /api/v1/ping — fast liveness check.

        Returns True if the server responds 200.
        """
        try:
            await self._request("GET", f"{API_BASE}/ping", expect_json=False)
        except VaultApiError:
            return False
        return True

    # --- Settings ---

    async def async_get_settings(self) -> Settings:
        """GET /api/v1/settings — retrieve current settings."""
        data = await self._request("GET", f"{API_BASE}/settings")
        return Settings.model_validate(data)

    async def async_update_settings(self, payload: dict[str, Any]) -> Settings:
        """PUT /api/v1/settings — update settings."""
        data = await self._request("PUT", f"{API_BASE}/settings", json_data=payload)
        return Settings.model_validate(data)

    async def async_get_encryption_status(self) -> EncryptionStatus:
        """GET /api/v1/settings/encryption — encryption status."""
        data = await self._request("GET", f"{API_BASE}/settings/encryption")
        return EncryptionStatus.model_validate(data)

    # --- Storage ---

    async def async_get_storage(self) -> list[StorageDestination]:
        """GET /api/v1/storage — list storage destinations."""
        data = await self._request("GET", f"{API_BASE}/storage")
        if isinstance(data, list):
            return [StorageDestination.model_validate(item) for item in data]
        return []

    async def async_test_storage(self, storage_id: int) -> StorageTestResult:
        """POST /api/v1/storage/{id}/test — test storage connection."""
        data = await self._request("POST", f"{API_BASE}/storage/{storage_id}/test")
        return StorageTestResult.model_validate(data)

    # --- Jobs ---

    async def async_get_jobs(self) -> list[BackupJob]:
        """GET /api/v1/jobs — list all backup jobs."""
        data = await self._request("GET", f"{API_BASE}/jobs")
        if isinstance(data, list):
            return [BackupJob.model_validate(item) for item in data]
        return []

    async def async_get_job(self, job_id: int) -> JobDetail:
        """GET /api/v1/jobs/{id} — get job details with items."""
        data = await self._request("GET", f"{API_BASE}/jobs/{job_id}")
        return JobDetail.model_validate(data)

    async def async_run_job(self, job_id: int) -> dict[str, Any]:
        """POST /api/v1/jobs/{id}/run — trigger an immediate backup."""
        return await self._request("POST", f"{API_BASE}/jobs/{job_id}/run")  # type: ignore[return-value]

    async def async_get_job_history(self, job_id: int, *, limit: int = 50) -> list[JobRun]:
        """GET /api/v1/jobs/{id}/history — job run history."""
        data = await self._request("GET", f"{API_BASE}/jobs/{job_id}/history?limit={limit}")
        if isinstance(data, list):
            return [JobRun.model_validate(item) for item in data]
        return []

    async def async_get_restore_points(self, job_id: int) -> list[RestorePoint]:
        """GET /api/v1/jobs/{id}/restore-points — list restore points."""
        data = await self._request("GET", f"{API_BASE}/jobs/{job_id}/restore-points")
        if isinstance(data, list):
            return [RestorePoint.model_validate(item) for item in data]
        return []

    async def async_restore(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/jobs/{id}/restore — trigger a restore."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/jobs/{job_id}/restore", json_data=payload
        )

    # --- Activity ---

    async def async_get_activity(self) -> list[ActivityEntry]:
        """GET /api/v1/activity — recent activity log."""
        data = await self._request("GET", f"{API_BASE}/activity")
        if isinstance(data, list):
            return [ActivityEntry.model_validate(item) for item in data]
        return []

    # --- Internal ---

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> Any:
        """Execute an HTTP request against the Vault API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.).
            path: URL path (appended to base_url).
            json_data: Optional JSON body payload.
            expect_json: Whether to parse the response as JSON.

        Returns:
            Parsed JSON response, or the raw response text.

        Raises:
            VaultAuthenticationError: On 401/403 responses.
            VaultConnectionError: On network/timeout errors.
            VaultApiError: On other HTTP or parsing errors.
        """
        url = f"{self._base_url}{path}"

        # Build headers — send both header styles for compatibility across Vault plugin versions.
        headers: dict[str, str] = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method,
                    url,
                    json=json_data,
                    headers=headers or None,
                )
        except TimeoutError as err:
            msg = f"Timeout connecting to Vault at {self._base_url}"
            raise VaultConnectionError(msg) from err
        except aiohttp.ClientError as err:
            msg = f"Error connecting to Vault at {self._base_url}: {err}"
            raise VaultConnectionError(msg) from err

        if response.status in (401, 403):
            msg = f"Authentication failed ({response.status})"
            raise VaultAuthenticationError(msg)

        if response.status >= 400:
            msg = f"Vault API error ({response.status}): {await response.text()}"
            raise VaultApiError(msg)

        if not expect_json:
            return await response.text()

        try:
            return await response.json()
        except (aiohttp.ContentTypeError, ValueError) as err:
            msg = f"Invalid JSON response from Vault: {err}"
            raise VaultApiError(msg) from err
