"""Button platform for the Vault integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VaultApiError, VaultConnectionError
from .api.models import BackupJob
from .const import DOMAIN
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultJobEntity, async_prune_orphan_entities, async_remove_stale_entities

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class VaultButtonEntityDescription(ButtonEntityDescription):
    """Describes a Vault button entity."""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VaultConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vault button entities — one per backup job."""
    coordinator = entry.runtime_data.coordinator
    known_jobs: set[int] = set()

    # One-time prune of registry entries left over from jobs deleted while
    # Home Assistant was not running, or from older integration versions with
    # name-based unique IDs. Runs before adding entities so freed entity_ids
    # can be reclaimed.
    valid_uids = {f"{entry.entry_id}_job_{job.id}_run_now" for job in coordinator.data.jobs}
    async_prune_orphan_entities(hass, entry.entry_id, "button", valid_uids)

    @callback
    def _check_jobs() -> None:
        current = {job.id for job in coordinator.data.jobs}

        # Drop entities for deleted jobs
        removed = known_jobs - current
        if removed:
            known_jobs.difference_update(removed)
            stale_uids = {f"{entry.entry_id}_job_{job_id}_run_now" for job_id in removed}
            async_remove_stale_entities(hass, "button", stale_uids)

        new_jobs = current - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[VaultJobButton] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                description = VaultButtonEntityDescription(
                    key=f"job_{job.id}_run_now",
                    translation_key="run_backup",
                )
                entities.append(VaultJobButton(coordinator, description, job))
            async_add_entities(entities)

    _check_jobs()
    entry.async_on_unload(coordinator.async_add_listener(_check_jobs))


class VaultJobButton(ButtonEntity, VaultJobEntity):
    """Button that triggers a specific backup job."""

    entity_description: VaultButtonEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultButtonEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description, job, "run now")
        self.entity_description = description

    async def async_press(self) -> None:
        """Trigger the backup job via POST /jobs/{id}/run."""
        try:
            await self.coordinator.client.async_run_job(self._job_id)
        except VaultConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
        except VaultApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err
        await self.coordinator.async_request_refresh()
