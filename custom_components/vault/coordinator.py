"""DataUpdateCoordinator and runtime data for the Vault integration."""

from __future__ import annotations

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

            # Fetch most recent run + restore points per job
            job_runs: dict[int, list] = {}
            restore_point_counts: dict[int, int] = {}
            for job in jobs:
                runs = await self.client.async_get_job_history(job.id, limit=1)
                job_runs[job.id] = runs
                rps = await self.client.async_get_restore_points(job.id)
                restore_point_counts[job.id] = len(rps)

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
        has_running = any(runs and runs[0].status.value == "running" for runs in job_runs.values())
        new_interval = ACTIVE_UPDATE_INTERVAL_SECONDS if has_running else DEFAULT_UPDATE_INTERVAL_SECONDS
        self.update_interval = timedelta(seconds=new_interval)

        return data
