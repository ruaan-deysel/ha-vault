"""DataUpdateCoordinator and runtime data for the Vault integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VaultApiClient, VaultApiError, VaultAuthenticationError, VaultConnectionError, VaultWebSocketClient
from .api.models import VaultApiData
from .const import ACTIVE_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


type VaultConfigEntry = ConfigEntry[VaultData]


@dataclass
class VaultData:
    """Runtime data stored in config entry."""

    client: VaultApiClient
    coordinator: VaultDataUpdateCoordinator
    websocket: VaultWebSocketClient


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
            except VaultApiError as err:
                LOGGER.warning("Failed fetching per-job data for job_id=%s: %s", job_id, err)
                return job_id, [], 0

        return job_id, runs, len(restore_points)

    async def _async_update_data(self) -> VaultApiData:
        """Fetch data from all Vault API endpoints.

        Returns:
            Aggregated VaultApiData.

        Raises:
            UpdateFailed: On communication errors.
        """
        try:
            health = await self.client.async_get_health()
            settings = await self.client.async_get_settings()
            encryption = await self.client.async_get_encryption_status()
            storage = await self.client.async_get_storage()
            jobs = await self.client.async_get_jobs()
            activity = await self.client.async_get_activity()

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

        data = VaultApiData(
            health=health,
            settings=settings,
            encryption=encryption,
            storage=storage,
            jobs=jobs,
            job_runs=job_runs,
            restore_point_counts=restore_point_counts,
            activity=activity,
        )

        # Adjust polling rate: faster when a job is running
        has_running = any(runs and self._job_run_status_text(runs[0].status) == "running" for runs in job_runs.values())
        new_interval = ACTIVE_UPDATE_INTERVAL_SECONDS if has_running else DEFAULT_UPDATE_INTERVAL_SECONDS
        self.update_interval = timedelta(seconds=new_interval)

        return data
