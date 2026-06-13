"""DataUpdateCoordinator and runtime data for the Vault integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from pydantic import ValidationError

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VaultApiClient, VaultApiError, VaultAuthenticationError, VaultConnectionError, VaultWebSocketClient
from .api.models import Anomaly, StorageDestination, VaultApiData
from .const import ACTIVE_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


type VaultConfigEntry = ConfigEntry[VaultData]


@dataclass
class VaultData:
    """Runtime data stored in config entry."""

    client: VaultApiClient
    coordinator: VaultDataUpdateCoordinator
    websocket: VaultWebSocketClient
    progress: dict[int, int] = field(default_factory=dict)
    """Live backup progress per job id, fed by WebSocket events."""


class VaultDataUpdateCoordinator(DataUpdateCoordinator[VaultApiData]):
    """Coordinator that polls the Vault API for all data."""

    config_entry: VaultConfigEntry

    def __init__(self, hass: HomeAssistant, client: VaultApiClient) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: Vault API client.
        """
        super().__init__(
            hass,
            LOGGER,
            name="vault",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )
        self.client = client
        self._storage_issue_ids: set[str] = set()
        self._anomaly_issue_ids: set[str] = set()

    @staticmethod
    def _job_run_status_text(status: object) -> str:
        """Return normalized lowercase status text for enum/string values."""
        return str(getattr(status, "value", status)).lower()

    async def _fetch_job_data(self, job_id: int, semaphore: asyncio.Semaphore) -> tuple[int, list, int]:
        """Fetch latest runs and restore point count for one job."""
        async with semaphore:
            try:
                runs = await self.client.async_get_job_history(job_id, limit=1)
                restore_points = await self.client.async_get_restore_points(job_id)
            except VaultAuthenticationError:
                # Must propagate so the reauth flow is triggered.
                raise
            except VaultApiError as err:
                LOGGER.warning("Failed fetching per-job data for job_id=%s: %s", job_id, err)
                return job_id, [], 0

        return job_id, runs, len(restore_points)

    def _update_storage_repair_issues(self, storage: list[StorageDestination]) -> None:
        """Create or clear repair issues for unhealthy storage destinations."""
        current_issue_ids: set[str] = set()
        for dest in storage:
            issue_id = f"storage_unhealthy_{dest.id}"
            status = (dest.last_health_check_status or "").lower()
            unhealthy = (status and status != "ok") or dest.breaker_state == "open"
            if unhealthy:
                current_issue_ids.add(issue_id)
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="storage_unhealthy",
                    translation_placeholders={
                        "name": dest.name,
                        "error": dest.last_health_check_error or dest.breaker_state or status or "unknown",
                    },
                )
        stale_issue_ids = self._storage_issue_ids - current_issue_ids
        for issue_id in stale_issue_ids:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        self._storage_issue_ids = current_issue_ids

    def _update_anomaly_repair_issues(self, anomalies: list[Anomaly], job_names: dict[int, str]) -> None:
        """Create or clear repair issues for open anomalies (Vault alerts)."""
        current_issue_ids: set[str] = set()
        for anomaly in anomalies:
            issue_id = f"anomaly_{anomaly.id}"
            current_issue_ids.add(issue_id)
            if anomaly.scope_kind == "job":
                scope = job_names.get(anomaly.scope_id, f"job {anomaly.scope_id}")
            else:
                scope = f"{anomaly.scope_kind} {anomaly.scope_id}".strip()
            severity = ir.IssueSeverity.ERROR if anomaly.severity == "critical" else ir.IssueSeverity.WARNING
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=severity,
                translation_key="anomaly",
                translation_placeholders={
                    "scope": scope,
                    "summary": anomaly.summary or anomaly.metric or anomaly.detector,
                },
            )
        stale_issue_ids = self._anomaly_issue_ids - current_issue_ids
        for issue_id in stale_issue_ids:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        self._anomaly_issue_ids = current_issue_ids

    async def _async_update_data(self) -> VaultApiData:
        """Fetch data from all Vault API endpoints.

        Returns:
            Aggregated VaultApiData.

        Raises:
            UpdateFailed: On communication errors.
        """
        try:
            health = await self.client.async_get_health()
            runner_status = await self.client.async_get_runner_status()
            settings = await self.client.async_get_settings()
            encryption = await self.client.async_get_encryption_status()
            storage = await self.client.async_get_storage()
            jobs = await self.client.async_get_jobs()
            activity = await self.client.async_get_activity()
            anomalies = await self.client.async_get_anomalies(state="open")

            # Fetch most recent run + restore points per job (bounded parallelism)
            semaphore = asyncio.Semaphore(5)
            results = await asyncio.gather(*(self._fetch_job_data(job.id, semaphore) for job in jobs))
            job_runs: dict[int, list] = {job_id: runs for job_id, runs, _ in results}
            restore_point_counts: dict[int, int] = {job_id: rp_count for job_id, _, rp_count in results}

        except VaultConnectionError as err:
            raise UpdateFailed(f"Error communicating with Vault: {err}") from err
        except VaultAuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except VaultApiError as err:
            raise UpdateFailed(f"Vault API error: {err}") from err
        except ValidationError as err:
            # Defense in depth: a payload shape we don't handle yet must mark
            # the update failed, not crash with an unexpected-error traceback.
            raise UpdateFailed(f"Unexpected Vault API payload: {err}") from err

        data = VaultApiData(
            health=health,
            runner_status=runner_status,
            settings=settings,
            encryption=encryption,
            storage=storage,
            jobs=jobs,
            job_runs=job_runs,
            restore_point_counts=restore_point_counts,
            activity=activity,
            anomalies=anomalies,
        )

        self._update_storage_repair_issues(storage)
        self._update_anomaly_repair_issues(anomalies, {job.id: job.name for job in jobs})

        # Adjust polling rate: faster when a job is running
        has_running = any(runs and self._job_run_status_text(runs[0].status) == "running" for runs in job_runs.values())
        new_interval = ACTIVE_UPDATE_INTERVAL_SECONDS if has_running else DEFAULT_UPDATE_INTERVAL_SECONDS
        self.update_interval = timedelta(seconds=new_interval)

        return data
