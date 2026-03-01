"""Binary sensor platform for the Vault integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.models import BackupJob, VaultApiData
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultEntity

PARALLEL_UPDATES = 1


def _slugify_job_name(name: str) -> str:
    """Convert a job name to a slug suitable for entity IDs."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Global binary sensor descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Vault binary sensor entity."""

    is_on_fn: Callable[[VaultApiData], bool]


def _is_online(data: VaultApiData) -> bool:
    """Return True when the Vault service reports healthy status."""
    return data.health.status.lower() in ("ok", "healthy", "running")


GLOBAL_BINARY_SENSOR_DESCRIPTIONS: tuple[VaultBinarySensorEntityDescription, ...] = (
    VaultBinarySensorEntityDescription(
        key="vault_online",
        translation_key="vault_online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_is_online,
    ),
)


# ---------------------------------------------------------------------------
# Per-job binary sensor descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultJobBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a per-job Vault binary sensor entity."""

    is_on_fn: Callable[[VaultApiData, int], bool]


def _is_job_running(data: VaultApiData, job_id: int) -> bool:
    """Return True if the most recent run for this job is running."""
    runs = data.job_runs.get(job_id, [])
    if not runs:
        return False
    return runs[0].status.value == "running"


def _is_job_last_success(data: VaultApiData, job_id: int) -> bool:
    """Return True if the most recent run for this job completed successfully."""
    runs = data.job_runs.get(job_id, [])
    if not runs:
        return False
    return runs[0].status.value == "completed"


PER_JOB_BINARY_SENSOR_TEMPLATES: tuple[VaultJobBinarySensorEntityDescription, ...] = (
    VaultJobBinarySensorEntityDescription(
        key="running",
        translation_key="job_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_is_job_running,
    ),
    VaultJobBinarySensorEntityDescription(
        key="last_success",
        translation_key="job_last_success",
        is_on_fn=_is_job_last_success,
    ),
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VaultConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vault binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    known_jobs: set[int] = set()

    # Add global binary sensors once
    async_add_entities([VaultBinarySensor(coordinator, desc) for desc in GLOBAL_BINARY_SENSOR_DESCRIPTIONS])

    # Per-job binary sensors with dynamic detection
    @callback
    def _check_jobs() -> None:
        current_jobs = {job.id for job in coordinator.data.jobs}
        new_jobs = current_jobs - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[BinarySensorEntity] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                slug = _slugify_job_name(job.name)
                for tmpl in PER_JOB_BINARY_SENSOR_TEMPLATES:
                    desc = VaultJobBinarySensorEntityDescription(
                        key=f"{slug}_{tmpl.key}",
                        translation_key=tmpl.translation_key,
                        device_class=tmpl.device_class,
                        is_on_fn=tmpl.is_on_fn,
                    )
                    entities.append(VaultJobBinarySensor(coordinator, desc, job))
            async_add_entities(entities)

    _check_jobs()
    entry.async_on_unload(coordinator.async_add_listener(_check_jobs))


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------


class VaultBinarySensor(BinarySensorEntity, VaultEntity):
    """Representation of a global Vault binary sensor."""

    entity_description: VaultBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)


class VaultJobBinarySensor(BinarySensorEntity, VaultEntity):
    """Representation of a per-job Vault binary sensor."""

    entity_description: VaultJobBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultJobBinarySensorEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the per-job binary sensor."""
        super().__init__(coordinator, description)
        self.entity_description = description
        self._job_id = job.id
        self._attr_name = f"{job.name} {description.translation_key or description.key}"

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on for this job."""
        return self.entity_description.is_on_fn(self.coordinator.data, self._job_id)
