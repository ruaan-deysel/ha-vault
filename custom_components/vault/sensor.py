"""Sensor platform for the Vault integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.models import BackupJob, JobRun, StorageDestination, VaultApiData
from .const import DOMAIN
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultEntity

PARALLEL_UPDATES = 1


def _slugify_job_name(name: str) -> str:
    """Convert a job name to a slug suitable for entity IDs."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Static (global) sensor descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultSensorEntityDescription(SensorEntityDescription):
    """Describes a Vault sensor entity."""

    value_fn: Callable[[VaultApiData], Any]


GLOBAL_SENSOR_DESCRIPTIONS: tuple[VaultSensorEntityDescription, ...] = (
    VaultSensorEntityDescription(
        key="vault_status",
        translation_key="vault_status",
        value_fn=lambda d: d.health.status,
    ),
    VaultSensorEntityDescription(
        key="vault_version",
        translation_key="vault_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.health.version,
    ),
    VaultSensorEntityDescription(
        key="jobs_total",
        translation_key="jobs_total",
        native_unit_of_measurement="jobs",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: len(d.jobs),
    ),
    VaultSensorEntityDescription(
        key="jobs_enabled",
        translation_key="jobs_enabled",
        native_unit_of_measurement="jobs",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: sum(1 for j in d.jobs if j.enabled),
    ),
    VaultSensorEntityDescription(
        key="encryption_status",
        translation_key="encryption_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: "enabled" if d.encryption.encryption_enabled else "disabled",
    ),
)


# ---------------------------------------------------------------------------
# Per-job sensor descriptions (created dynamically for each backup job)
# ---------------------------------------------------------------------------


def _latest_run(data: VaultApiData, job_id: int) -> JobRun | None:
    """Return the most recent run for a job, or None."""
    runs = data.job_runs.get(job_id, [])
    return runs[0] if runs else None


@dataclass(frozen=True, kw_only=True)
class VaultJobSensorEntityDescription(SensorEntityDescription):
    """Describes a per-job Vault sensor entity."""

    value_fn: Callable[[VaultApiData, int], Any]


def _job_status(data: VaultApiData, job_id: int) -> str:
    """Return the status string of the most recent run for a job."""
    run = _latest_run(data, job_id)
    return run.status.value if run else "idle"


def _job_last_run(data: VaultApiData, job_id: int) -> Any:
    """Return the completion timestamp of the most recent run."""
    run = _latest_run(data, job_id)
    return run.completed_at if run else None


def _job_last_size(data: VaultApiData, job_id: int) -> int | None:
    """Return the size in bytes of the most recent run."""
    run = _latest_run(data, job_id)
    return run.size_bytes if run else None


def _job_items_backed_up(data: VaultApiData, job_id: int) -> int:
    """Return the number of items done in the most recent run."""
    run = _latest_run(data, job_id)
    return run.items_done if run else 0


def _job_items_failed(data: VaultApiData, job_id: int) -> int:
    """Return the number of items failed in the most recent run."""
    run = _latest_run(data, job_id)
    return run.items_failed if run else 0


def _job_restore_points(data: VaultApiData, job_id: int) -> int:
    """Return the restore point count for a job."""
    return data.restore_point_counts.get(job_id, 0)


def _job_sensor_descriptions() -> tuple[VaultJobSensorEntityDescription, ...]:
    """Return per-job sensor description templates."""
    return (
        VaultJobSensorEntityDescription(
            key="status",
            translation_key="job_status",
            value_fn=_job_status,
        ),
        VaultJobSensorEntityDescription(
            key="last_run",
            translation_key="job_last_run",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=_job_last_run,
        ),
        VaultJobSensorEntityDescription(
            key="last_size",
            translation_key="job_last_size",
            device_class=SensorDeviceClass.DATA_SIZE,
            native_unit_of_measurement=UnitOfInformation.BYTES,
            suggested_display_precision=0,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=_job_last_size,
        ),
        VaultJobSensorEntityDescription(
            key="items_backed_up",
            translation_key="job_items_backed_up",
            native_unit_of_measurement="items",
            value_fn=_job_items_backed_up,
        ),
        VaultJobSensorEntityDescription(
            key="items_failed",
            translation_key="job_items_failed",
            native_unit_of_measurement="items",
            value_fn=_job_items_failed,
        ),
        VaultJobSensorEntityDescription(
            key="restore_points",
            translation_key="job_restore_points",
            native_unit_of_measurement="points",
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=_job_restore_points,
        ),
    )


# ---------------------------------------------------------------------------
# Storage sensor descriptions (created dynamically per storage destination)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultStorageSensorEntityDescription(SensorEntityDescription):
    """Describes a per-storage Vault sensor entity."""

    value_fn: Callable[[StorageDestination], Any]


STORAGE_SENSOR_DESCRIPTIONS: tuple[VaultStorageSensorEntityDescription, ...] = (
    VaultStorageSensorEntityDescription(
        key="name",
        translation_key="storage_name",
        value_fn=lambda s: s.name,
    ),
    VaultStorageSensorEntityDescription(
        key="type",
        translation_key="storage_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.type.value,
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
    """Set up Vault sensor entities."""
    coordinator = entry.runtime_data.coordinator
    known_jobs: set[int] = set()
    known_storage: set[int] = set()

    # Add global sensors once
    async_add_entities([VaultSensor(coordinator, desc) for desc in GLOBAL_SENSOR_DESCRIPTIONS])

    # Per-job sensors with dynamic detection
    job_templates = _job_sensor_descriptions()

    @callback
    def _check_jobs() -> None:
        current_jobs = {job.id for job in coordinator.data.jobs}
        new_jobs = current_jobs - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[SensorEntity] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                slug = _slugify_job_name(job.name)
                for tmpl in job_templates:
                    job_desc = VaultJobSensorEntityDescription(
                        key=f"{slug}_{tmpl.key}",
                        translation_key=tmpl.translation_key,
                        device_class=tmpl.device_class,
                        native_unit_of_measurement=tmpl.native_unit_of_measurement,
                        suggested_display_precision=tmpl.suggested_display_precision,
                        entity_category=tmpl.entity_category,
                        entity_registry_enabled_default=tmpl.entity_registry_enabled_default,
                        value_fn=tmpl.value_fn,
                    )
                    entities.append(VaultJobSensor(coordinator, job_desc, job))

                # Add progress sensor per job
                entities.append(VaultJobProgressSensor(coordinator, hass, job))

            async_add_entities(entities)

    @callback
    def _check_storage() -> None:
        current_storage = {s.id for s in coordinator.data.storage}
        new_storage = current_storage - known_storage
        if new_storage:
            known_storage.update(new_storage)
            entities: list[SensorEntity] = []
            for storage in coordinator.data.storage:
                if storage.id not in new_storage:
                    continue
                slug = _slugify_job_name(storage.name)
                for tmpl in STORAGE_SENSOR_DESCRIPTIONS:
                    storage_desc = VaultStorageSensorEntityDescription(
                        key=f"storage_{slug}_{tmpl.key}",
                        translation_key=tmpl.translation_key,
                        entity_category=tmpl.entity_category,
                        value_fn=tmpl.value_fn,
                    )
                    entities.append(VaultStorageSensor(coordinator, storage_desc, storage))
            async_add_entities(entities)

    _check_jobs()
    _check_storage()
    entry.async_on_unload(coordinator.async_add_listener(_check_jobs))
    entry.async_on_unload(coordinator.async_add_listener(_check_storage))


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------


class VaultSensor(SensorEntity, VaultEntity):
    """Representation of a global Vault sensor."""

    entity_description: VaultSensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)


class VaultJobSensor(SensorEntity, VaultEntity):
    """Representation of a per-job Vault sensor."""

    entity_description: VaultJobSensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultJobSensorEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the per-job sensor."""
        super().__init__(coordinator, description)
        self.entity_description = description
        self._job_id = job.id
        self._attr_name = f"{job.name} {description.translation_key or description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value for this job."""
        return self.entity_description.value_fn(self.coordinator.data, self._job_id)


class VaultJobProgressSensor(SensorEntity, VaultEntity):
    """Representation of a per-job backup progress sensor (WebSocket-driven)."""

    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        hass: HomeAssistant,
        job: BackupJob,
    ) -> None:
        """Initialize the progress sensor."""
        slug = _slugify_job_name(job.name)
        desc = SensorEntityDescription(
            key=f"{slug}_progress",
            translation_key="job_progress",
        )
        super().__init__(coordinator, desc)
        self._job_id = job.id
        self._hass = hass
        self._attr_name = f"{job.name} Progress"

    @property
    def native_value(self) -> int | None:
        """Return the current progress percentage from hass.data store."""
        progress_store: dict[int, int] = self._hass.data.get(DOMAIN, {}).get("progress", {})
        return progress_store.get(self._job_id)


class VaultStorageSensor(SensorEntity, VaultEntity):
    """Representation of a per-storage Vault sensor."""

    entity_description: VaultStorageSensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultStorageSensorEntityDescription,
        storage: StorageDestination,
    ) -> None:
        """Initialize the per-storage sensor."""
        super().__init__(coordinator, description)
        self.entity_description = description
        self._storage_id = storage.id
        self._attr_name = f"Storage {storage.name} {description.translation_key or description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value for this storage destination."""
        for storage in self.coordinator.data.storage:
            if storage.id == self._storage_id:
                return self.entity_description.value_fn(storage)
        return None
