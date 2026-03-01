"""Button platform for the Vault integration."""

from __future__ import annotations

from dataclasses import dataclass
import re

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VaultApiError, VaultConnectionError
from .api.models import BackupJob
from .const import DOMAIN
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultEntity

PARALLEL_UPDATES = 1


def _slugify_job_name(name: str) -> str:
    """Convert a job name to a slug suitable for entity IDs."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


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

    @callback
    def _check_jobs() -> None:
        current_jobs = {job.id for job in coordinator.data.jobs}
        new_jobs = current_jobs - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[VaultJobButton] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                slug = _slugify_job_name(job.name)
                description = VaultButtonEntityDescription(
                    key=f"{slug}_run_now",
                    translation_key="run_backup",
                )
                entities.append(VaultJobButton(coordinator, description, job))
            async_add_entities(entities)

    _check_jobs()
    entry.async_on_unload(coordinator.async_add_listener(_check_jobs))


class VaultJobButton(ButtonEntity, VaultEntity):
    """Button that triggers a specific backup job."""

    entity_description: VaultButtonEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultButtonEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description)
        self.entity_description = description
        self._job_id = job.id
        self._attr_name = f"{job.name} run now"

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
