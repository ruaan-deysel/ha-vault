"""Async API client for the Vault backup manager."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

import aiohttp

from .exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError
from .models import (
    ActivityEntry,
    Anomaly,
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

    @staticmethod
    def _with_query(path: str, params: dict[str, Any] | None = None) -> str:
        """Build a URL path with query parameters, skipping unset values."""
        if not params:
            return path
        filtered = {key: value for key, value in params.items() if value is not None}
        if not filtered:
            return path
        return f"{path}?{urlencode(filtered, doseq=True)}"

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

    async def async_get_health_summary(self) -> dict[str, Any]:
        """GET /api/v1/health/summary — aggregated dashboard health metrics."""
        return await self._request("GET", f"{API_BASE}/health/summary")  # type: ignore[return-value]

    async def async_ping(self) -> bool:
        """GET /api/v1/ping — fast liveness check.

        Returns True if the server responds 200.
        """
        try:
            await self._request("GET", f"{API_BASE}/ping", expect_json=False)
        except VaultApiError:
            return False
        return True

    async def async_get_runner_status(self) -> dict[str, Any]:
        """GET /api/v1/runner/status — current runner state and queue."""
        return await self._request("GET", f"{API_BASE}/runner/status")  # type: ignore[return-value]

    async def async_get_release_changelog(self) -> dict[str, Any]:
        """GET /api/v1/release/changelog — parsed changelog metadata."""
        return await self._request("GET", f"{API_BASE}/release/changelog")  # type: ignore[return-value]

    async def async_get_release_latest(self) -> dict[str, Any]:
        """GET /api/v1/release/latest — latest release metadata."""
        return await self._request("GET", f"{API_BASE}/release/latest")  # type: ignore[return-value]

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

    async def async_set_encryption(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/settings/encryption — set encryption passphrase."""
        return await self._request("POST", f"{API_BASE}/settings/encryption", json_data=payload)  # type: ignore[return-value]

    async def async_verify_encryption(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/settings/encryption/verify — verify passphrase."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/settings/encryption/verify", json_data=payload
        )

    async def async_get_encryption_passphrase(self) -> dict[str, Any]:
        """GET /api/v1/settings/encryption/passphrase — read configured passphrase."""
        return await self._request("GET", f"{API_BASE}/settings/encryption/passphrase")  # type: ignore[return-value]

    async def async_get_staging_info(self) -> dict[str, Any]:
        """GET /api/v1/settings/staging — staging directory info."""
        return await self._request("GET", f"{API_BASE}/settings/staging")  # type: ignore[return-value]

    async def async_set_staging_override(self, payload: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/v1/settings/staging — set staging directory override."""
        return await self._request("PUT", f"{API_BASE}/settings/staging", json_data=payload)  # type: ignore[return-value]

    async def async_get_database_settings(self) -> dict[str, Any]:
        """GET /api/v1/settings/database — database snapshot settings."""
        return await self._request("GET", f"{API_BASE}/settings/database")  # type: ignore[return-value]

    async def async_update_database_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/v1/settings/database — update database snapshot settings."""
        return await self._request("PUT", f"{API_BASE}/settings/database", json_data=payload)  # type: ignore[return-value]

    async def async_test_discord_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/settings/discord/test — test Discord webhook."""
        return await self._request("POST", f"{API_BASE}/settings/discord/test", json_data=payload)  # type: ignore[return-value]

    async def async_get_api_key_status(self) -> dict[str, Any]:
        """GET /api/v1/settings/api-key — API key status."""
        return await self._request("GET", f"{API_BASE}/settings/api-key")  # type: ignore[return-value]

    async def async_get_api_key(self) -> dict[str, Any]:
        """GET /api/v1/settings/api-key/key — read current API key."""
        return await self._request("GET", f"{API_BASE}/settings/api-key/key")  # type: ignore[return-value]

    async def async_generate_api_key(self) -> dict[str, Any]:
        """POST /api/v1/settings/api-key/generate — generate a new API key."""
        return await self._request("POST", f"{API_BASE}/settings/api-key/generate")  # type: ignore[return-value]

    async def async_rotate_api_key(self) -> dict[str, Any]:
        """POST /api/v1/settings/api-key/rotate — rotate existing API key."""
        return await self._request("POST", f"{API_BASE}/settings/api-key/rotate")  # type: ignore[return-value]

    async def async_revoke_api_key(self) -> str:
        """DELETE /api/v1/settings/api-key — revoke API key."""
        return await self._request("DELETE", f"{API_BASE}/settings/api-key", expect_json=False)

    async def async_download_diagnostics(self) -> bytes:
        """GET /api/v1/settings/diagnostics — download diagnostics ZIP."""
        return await self._request("GET", f"{API_BASE}/settings/diagnostics", expect_json=False, expect_bytes=True)

    # --- Storage ---

    async def async_get_storage(self) -> list[StorageDestination]:
        """GET /api/v1/storage — list storage destinations."""
        data = await self._request("GET", f"{API_BASE}/storage")
        if not isinstance(data, list):
            # Entities are pruned for storage missing from this list — never
            # silently treat a malformed payload as "no storage".
            msg = f"Unexpected response for storage list: {type(data).__name__}"
            raise VaultApiError(msg)
        return [StorageDestination.model_validate(item) for item in data]

    async def async_test_storage(self, storage_id: int) -> StorageTestResult:
        """POST /api/v1/storage/{id}/test — test storage connection."""
        data = await self._request("POST", f"{API_BASE}/storage/{storage_id}/test")
        return StorageTestResult.model_validate(data)

    async def async_create_storage(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/storage — create storage destination."""
        return await self._request("POST", f"{API_BASE}/storage", json_data=payload)  # type: ignore[return-value]

    async def async_get_storage_destination(self, storage_id: int) -> StorageDestination:
        """GET /api/v1/storage/{id} — fetch one storage destination."""
        data = await self._request("GET", f"{API_BASE}/storage/{storage_id}")
        return StorageDestination.model_validate(data)

    async def async_update_storage_destination(self, storage_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/v1/storage/{id} — update storage destination."""
        return await self._request("PUT", f"{API_BASE}/storage/{storage_id}", json_data=payload)  # type: ignore[return-value]

    async def async_delete_storage_destination(
        self,
        storage_id: int,
        *,
        force: bool | None = None,
        delete_files: bool | None = None,
    ) -> str:
        """DELETE /api/v1/storage/{id} — delete storage destination."""
        path = self._with_query(
            f"{API_BASE}/storage/{storage_id}",
            {
                "force": force,
                "deleteFiles": delete_files,
            },
        )
        return await self._request("DELETE", path, expect_json=False)

    async def async_health_check_storage(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/health-check — run storage health probe."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/health-check")  # type: ignore[return-value]

    async def async_capacity_check_storage(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/capacity-check — refresh capacity metrics."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/capacity-check")  # type: ignore[return-value]

    async def async_close_storage_breaker(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/breaker/close — close circuit breaker."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/breaker/close")  # type: ignore[return-value]

    async def async_scan_storage_orphans(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/scan-orphans — scan for orphaned files."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/scan-orphans")  # type: ignore[return-value]

    async def async_delete_storage_orphans(self, storage_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/delete-orphans — delete orphaned files."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/storage/{storage_id}/delete-orphans", json_data=payload
        )

    async def async_get_storage_dedup_stats(self, storage_id: int) -> dict[str, Any]:
        """GET /api/v1/storage/{id}/dedup-stats — dedup repository statistics."""
        return await self._request("GET", f"{API_BASE}/storage/{storage_id}/dedup-stats")  # type: ignore[return-value]

    async def async_run_storage_gc(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/gc — run dedup mark-and-sweep GC."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/gc")  # type: ignore[return-value]

    async def async_scan_storage(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/scan — scan storage for importable backups."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/scan")  # type: ignore[return-value]

    async def async_import_storage(self, storage_id: int) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/import — import scanned backups."""
        return await self._request("POST", f"{API_BASE}/storage/{storage_id}/import")  # type: ignore[return-value]

    async def async_restore_storage_database(self, storage_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/storage/{id}/restore-db — restore Vault DB snapshot."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/storage/{storage_id}/restore-db", json_data=payload
        )

    async def async_get_storage_jobs(self, storage_id: int) -> dict[str, Any]:
        """GET /api/v1/storage/{id}/jobs — list dependent jobs."""
        return await self._request("GET", f"{API_BASE}/storage/{storage_id}/jobs")  # type: ignore[return-value]

    async def async_list_storage_files(self, storage_id: int, *, path: str | None = None) -> dict[str, Any]:
        """GET /api/v1/storage/{id}/list — list files under a storage path."""
        endpoint = self._with_query(f"{API_BASE}/storage/{storage_id}/list", {"path": path})
        return await self._request("GET", endpoint)  # type: ignore[return-value]

    async def async_download_storage_file(self, storage_id: int, *, path: str) -> bytes:
        """GET /api/v1/storage/{id}/files — download a file from storage."""
        endpoint = self._with_query(f"{API_BASE}/storage/{storage_id}/files", {"path": path})
        return await self._request("GET", endpoint, expect_json=False, expect_bytes=True)

    # --- Jobs ---

    async def async_get_jobs(self) -> list[BackupJob]:
        """GET /api/v1/jobs — list all backup jobs."""
        data = await self._request("GET", f"{API_BASE}/jobs")
        if not isinstance(data, list):
            # Entities are pruned for jobs missing from this list — never
            # silently treat a malformed payload as "no jobs".
            msg = f"Unexpected response for jobs list: {type(data).__name__}"
            raise VaultApiError(msg)
        return [BackupJob.model_validate(item) for item in data]

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

    async def async_create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/jobs — create a backup job."""
        return await self._request("POST", f"{API_BASE}/jobs", json_data=payload)  # type: ignore[return-value]

    async def async_update_job(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/v1/jobs/{id} — update an existing backup job."""
        return await self._request("PUT", f"{API_BASE}/jobs/{job_id}", json_data=payload)  # type: ignore[return-value]

    async def async_delete_job(self, job_id: int) -> str:
        """DELETE /api/v1/jobs/{id} — delete a job."""
        return await self._request("DELETE", f"{API_BASE}/jobs/{job_id}", expect_json=False)

    async def async_get_next_runs(self) -> dict[str, Any]:
        """GET /api/v1/jobs/next-runs — next scheduled run for all jobs."""
        return await self._request("GET", f"{API_BASE}/jobs/next-runs")  # type: ignore[return-value]

    async def async_get_next_run(self, job_id: int) -> dict[str, Any]:
        """GET /api/v1/jobs/{id}/next-run — next scheduled run for one job."""
        return await self._request("GET", f"{API_BASE}/jobs/{job_id}/next-run")  # type: ignore[return-value]

    async def async_get_retention_preview(self, job_id: int, **params: Any) -> list[dict[str, Any]]:
        """GET /api/v1/jobs/{id}/retention-preview — preview retention pruning."""
        endpoint = self._with_query(f"{API_BASE}/jobs/{job_id}/retention-preview", params)
        data = await self._request("GET", endpoint)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    async def async_delete_restore_point(self, job_id: int, restore_point_id: int) -> str:
        """DELETE /api/v1/jobs/{id}/restore-points/{rpid} — delete restore point."""
        return await self._request(
            "DELETE",
            f"{API_BASE}/jobs/{job_id}/restore-points/{restore_point_id}",
            expect_json=False,
        )

    async def async_get_restore_point_contents(
        self,
        job_id: int,
        restore_point_id: int,
        *,
        item: str,
        file_name: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """GET /api/v1/jobs/{id}/restore-points/{rpid}/contents — list archive contents."""
        endpoint = self._with_query(
            f"{API_BASE}/jobs/{job_id}/restore-points/{restore_point_id}/contents",
            {"item": item, "file": file_name},
        )
        data = await self._request("GET", endpoint)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_verify_restore_point(self, job_id: int, restore_point_id: int) -> dict[str, Any]:
        """POST /api/v1/jobs/{id}/restore-points/{rpid}/verify — trigger verification."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/jobs/{job_id}/restore-points/{restore_point_id}/verify"
        )

    async def async_get_restore_point_verify_runs(self, job_id: int, restore_point_id: int) -> list[dict[str, Any]]:
        """GET /api/v1/jobs/{id}/restore-points/{rpid}/verify-runs — list verify runs."""
        data = await self._request("GET", f"{API_BASE}/jobs/{job_id}/restore-points/{restore_point_id}/verify-runs")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_verify_run(self, job_id: int, verify_run_id: int) -> dict[str, Any]:
        """GET /api/v1/jobs/{id}/verify-runs/{vrid} — fetch one verify run."""
        return await self._request("GET", f"{API_BASE}/jobs/{job_id}/verify-runs/{verify_run_id}")  # type: ignore[return-value]

    async def async_cancel_job(self, job_id: int) -> dict[str, Any]:
        """POST /api/v1/jobs/{id}/cancel — cancel running backup job."""
        return await self._request("POST", f"{API_BASE}/jobs/{job_id}/cancel")  # type: ignore[return-value]

    async def async_get_stale_items(self, job_id: int) -> list[dict[str, Any]]:
        """GET /api/v1/jobs/{id}/stale-items — list stale job items."""
        data = await self._request("GET", f"{API_BASE}/jobs/{job_id}/stale-items")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_remove_stale_items(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/jobs/{id}/stale-items/remove — remove stale items."""
        return await self._request(  # type: ignore[return-value]
            "POST", f"{API_BASE}/jobs/{job_id}/stale-items/remove", json_data=payload
        )

    async def async_delete_job_item(self, job_id: int, item_id: int) -> str:
        """DELETE /api/v1/jobs/{id}/items/{itemId} — remove one item from a job."""
        return await self._request("DELETE", f"{API_BASE}/jobs/{job_id}/items/{item_id}", expect_json=False)

    # --- Activity ---

    async def async_get_activity(self) -> list[ActivityEntry]:
        """GET /api/v1/activity — recent activity log."""
        data = await self._request("GET", f"{API_BASE}/activity")
        if isinstance(data, list):
            return [ActivityEntry.model_validate(item) for item in data]
        return []

    async def async_purge_activity(self) -> str:
        """DELETE /api/v1/activity — purge activity log."""
        return await self._request("DELETE", f"{API_BASE}/activity", expect_json=False)

    async def async_purge_history(self) -> str:
        """DELETE /api/v1/history — purge all job history records."""
        return await self._request("DELETE", f"{API_BASE}/history", expect_json=False)

    # --- Discovery ---

    async def async_browse(self, *, path: str) -> dict[str, Any]:
        """GET /api/v1/browse?path=... — browse filesystem paths."""
        endpoint = self._with_query(f"{API_BASE}/browse", {"path": path})
        return await self._request("GET", endpoint)  # type: ignore[return-value]

    async def async_path_exists(self, *, path: str) -> dict[str, Any]:
        """GET /api/v1/path-exists?path=... — check path existence."""
        endpoint = self._with_query(f"{API_BASE}/path-exists", {"path": path})
        return await self._request("GET", endpoint)  # type: ignore[return-value]

    async def async_get_containers(self) -> list[dict[str, Any]]:
        """GET /api/v1/containers — discover Docker containers."""
        data = await self._request("GET", f"{API_BASE}/containers")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_vms(self) -> list[dict[str, Any]]:
        """GET /api/v1/vms — discover VMs."""
        data = await self._request("GET", f"{API_BASE}/vms")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_folders(self) -> list[dict[str, Any]]:
        """GET /api/v1/folders — discover folder presets."""
        data = await self._request("GET", f"{API_BASE}/folders")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_plugins(self) -> list[dict[str, Any]]:
        """GET /api/v1/plugins — discover installed plugins."""
        data = await self._request("GET", f"{API_BASE}/plugins")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_zfs_datasets(self) -> list[dict[str, Any]]:
        """GET /api/v1/zfs — discover ZFS datasets."""
        data = await self._request("GET", f"{API_BASE}/zfs")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_get_presets_exclusions(
        self,
        *,
        image: str | None = None,
        container: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /api/v1/presets/exclusions — fetch exclusion presets."""
        endpoint = self._with_query(f"{API_BASE}/presets/exclusions", {"image": image, "container": container})
        data = await self._request("GET", endpoint)
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    # --- Replication ---

    async def async_get_replication_sources(self) -> list[dict[str, Any]]:
        """GET /api/v1/replication — list replication sources."""
        data = await self._request("GET", f"{API_BASE}/replication")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    async def async_create_replication_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/replication — create replication source."""
        return await self._request("POST", f"{API_BASE}/replication", json_data=payload)  # type: ignore[return-value]

    async def async_test_replication_url(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/replication/test-url — validate remote URL."""
        return await self._request("POST", f"{API_BASE}/replication/test-url", json_data=payload)  # type: ignore[return-value]

    async def async_get_replication_source(self, source_id: int) -> dict[str, Any]:
        """GET /api/v1/replication/{id} — fetch one replication source."""
        return await self._request("GET", f"{API_BASE}/replication/{source_id}")  # type: ignore[return-value]

    async def async_update_replication_source(self, source_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/v1/replication/{id} — update replication source."""
        return await self._request("PUT", f"{API_BASE}/replication/{source_id}", json_data=payload)  # type: ignore[return-value]

    async def async_delete_replication_source(self, source_id: int) -> str:
        """DELETE /api/v1/replication/{id} — delete replication source."""
        return await self._request("DELETE", f"{API_BASE}/replication/{source_id}", expect_json=False)

    async def async_test_replication_source(self, source_id: int) -> dict[str, Any]:
        """POST /api/v1/replication/{id}/test — test replication source."""
        return await self._request("POST", f"{API_BASE}/replication/{source_id}/test")  # type: ignore[return-value]

    async def async_sync_replication_source(self, source_id: int) -> dict[str, Any]:
        """POST /api/v1/replication/{id}/sync — trigger replication now."""
        return await self._request("POST", f"{API_BASE}/replication/{source_id}/sync")  # type: ignore[return-value]

    async def async_get_replication_jobs(self, source_id: int) -> list[dict[str, Any]]:
        """GET /api/v1/replication/{id}/jobs — list replicated jobs."""
        data = await self._request("GET", f"{API_BASE}/replication/{source_id}/jobs")
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    # --- Anomalies / Recovery ---

    async def async_get_anomalies(
        self,
        *,
        severity: str | None = None,
        state: str | None = None,
        limit: int | None = None,
    ) -> list[Anomaly]:
        """GET /api/v1/anomalies — list anomaly records."""
        endpoint = self._with_query(
            f"{API_BASE}/anomalies",
            {
                "severity": severity,
                "state": state,
                "limit": limit,
            },
        )
        data = await self._request("GET", endpoint)
        # The endpoint wraps the list: {"anomalies": [...]}
        if isinstance(data, dict):
            data = data.get("anomalies")
        if isinstance(data, list):
            return [Anomaly.model_validate(entry) for entry in data if isinstance(entry, dict)]
        return []

    async def async_ack_bulk_anomalies(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /api/v1/anomalies/ack-bulk — bulk-ack anomalies."""
        return await self._request("POST", f"{API_BASE}/anomalies/ack-bulk", json_data=payload)  # type: ignore[return-value]

    async def async_get_anomaly(self, anomaly_id: int) -> dict[str, Any]:
        """GET /api/v1/anomalies/{id} — fetch one anomaly."""
        return await self._request("GET", f"{API_BASE}/anomalies/{anomaly_id}")  # type: ignore[return-value]

    async def async_ack_anomaly(self, anomaly_id: int) -> dict[str, Any]:
        """POST /api/v1/anomalies/{id}/ack — acknowledge one anomaly."""
        return await self._request("POST", f"{API_BASE}/anomalies/{anomaly_id}/ack")  # type: ignore[return-value]

    async def async_get_job_baseline(self, job_id: int) -> dict[str, Any]:
        """GET /api/v1/jobs/{id}/baseline — get job anomaly baseline."""
        return await self._request("GET", f"{API_BASE}/jobs/{job_id}/baseline")  # type: ignore[return-value]

    async def async_get_destination_capacity_trajectory(self, destination_id: int) -> dict[str, Any]:
        """GET /api/v1/destinations/{id}/capacity-trajectory — capacity trajectory."""
        return await self._request("GET", f"{API_BASE}/destinations/{destination_id}/capacity-trajectory")  # type: ignore[return-value]

    async def async_get_recovery_plan(self) -> dict[str, Any]:
        """GET /api/v1/recovery/plan — disaster recovery plan."""
        return await self._request("GET", f"{API_BASE}/recovery/plan")  # type: ignore[return-value]

    # --- Internal ---

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        expect_json: bool = True,
        expect_bytes: bool = False,
    ) -> Any:
        """Execute an HTTP request against the Vault API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.).
            path: URL path (appended to base_url).
            json_data: Optional JSON body payload.
            expect_json: Whether to parse the response as JSON.
            expect_bytes: Whether to return raw bytes when JSON parsing is disabled.

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
            # The timeout must cover the body read too — a stalled response
            # body would otherwise hang the coordinator indefinitely.
            async with asyncio.timeout(30):
                response = await self._session.request(
                    method,
                    url,
                    json=json_data,
                    headers=headers or None,
                )

                if response.status in (401, 403):
                    msg = f"Authentication failed ({response.status})"
                    raise VaultAuthenticationError(msg)

                if response.status >= 400:
                    msg = f"Vault API error ({response.status}): {await response.text()}"
                    raise VaultApiError(msg)

                if not expect_json and expect_bytes:
                    return await response.read()

                if not expect_json:
                    return await response.text()

                try:
                    return await response.json()
                except (aiohttp.ContentTypeError, ValueError) as err:
                    msg = f"Invalid JSON response from Vault: {err}"
                    raise VaultApiError(msg) from err
        except TimeoutError as err:
            msg = f"Timeout connecting to Vault at {self._base_url}"
            raise VaultConnectionError(msg) from err
        except aiohttp.ClientError as err:
            msg = f"Error connecting to Vault at {self._base_url}: {err}"
            raise VaultConnectionError(msg) from err
