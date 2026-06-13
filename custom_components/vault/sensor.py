"""Sensor platform for the Vault integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
import json
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.models import BackupJob, JobRun, StorageDestination, StorageType, VaultApiData, WebSocketEvent
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultEntity, VaultJobEntity, async_prune_orphan_entities, async_remove_stale_entities

PARALLEL_UPDATES = 0


# ---------------------------------------------------------------------------
# Static (global) sensor descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultSensorEntityDescription(SensorEntityDescription):
    """Describes a Vault sensor entity."""

    value_fn: Callable[[VaultApiData], Any]
    attributes_fn: Callable[[VaultApiData], dict[str, Any] | None] | None = None


def _runner_queue_length(data: VaultApiData) -> int:
    """Return current runner queue length."""
    runner_status = data.runner_status or {}
    queue = runner_status.get("queue")
    return len(queue) if isinstance(queue, list) else 0


def _runner_current_job(data: VaultApiData) -> str:
    """Return the name of the currently running job, or "idle" when none."""
    runner_status = data.runner_status or {}
    job_id = runner_status.get("job_id")
    if not isinstance(job_id, int):
        return "idle"
    job = next((j for j in data.jobs if j.id == job_id), None)
    return job.name if job else str(job_id)


def _open_anomalies_attributes(data: VaultApiData) -> dict[str, Any] | None:
    """List the open anomalies (Vault alerts) behind the count."""
    if not data.anomalies:
        return None
    job_names = {job.id: job.name for job in data.jobs}
    return {
        "anomalies": [
            {
                "detector": a.detector,
                "severity": a.severity,
                "summary": a.summary,
                "job": job_names.get(a.scope_id) if a.scope_kind == "job" else None,
                "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
            }
            for a in data.anomalies
        ]
    }


def _auto_data_size_unit(num_bytes: float | None) -> UnitOfInformation | None:
    """Pick a display unit so a byte count reads naturally (TB/GB/MB)."""
    if not num_bytes or num_bytes <= 0:
        return None
    if num_bytes >= 1_000_000_000_000:
        return UnitOfInformation.TERABYTES
    if num_bytes >= 1_000_000_000:
        return UnitOfInformation.GIGABYTES
    if num_bytes >= 1_000_000:
        return UnitOfInformation.MEGABYTES
    return UnitOfInformation.KILOBYTES


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
        key="vault_mode",
        translation_key="vault_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.health.mode or "daemon",
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
    VaultSensorEntityDescription(
        key="runner_queue_length",
        translation_key="runner_queue_length",
        native_unit_of_measurement="jobs",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_runner_queue_length,
    ),
    VaultSensorEntityDescription(
        key="runner_current_job_id",
        translation_key="runner_current_job_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_runner_current_job,
    ),
    VaultSensorEntityDescription(
        key="open_anomalies",
        translation_key="open_anomalies",
        native_unit_of_measurement="anomalies",
        value_fn=lambda d: len(d.anomalies),
        attributes_fn=_open_anomalies_attributes,
    ),
)


# ---------------------------------------------------------------------------
# Per-job sensor descriptions (created dynamically for each backup job)
# ---------------------------------------------------------------------------


def _latest_run(data: VaultApiData, job_id: int) -> JobRun | None:
    """Return the most recent run for a job, or None."""
    runs = data.job_runs.get(job_id, [])
    return runs[0] if runs else None


def _status_text(value: object) -> str:
    """Return normalized lowercase status text for enum/string values."""
    return str(getattr(value, "value", value)).lower()


@dataclass(frozen=True, kw_only=True)
class VaultJobSensorEntityDescription(SensorEntityDescription):
    """Describes a per-job Vault sensor entity."""

    value_fn: Callable[[VaultApiData, int], Any]
    attributes_fn: Callable[[VaultApiData, int], dict[str, Any] | None] | None = None


_JOB_SENSOR_LABELS: dict[str, str] = {
    "job_status": "Status",
    "job_last_run": "Last run",
    "job_last_size": "Last size",
    "job_last_duration": "Last duration",
    "job_items_backed_up": "Items backed up",
    "job_items_failed": "Items failed",
    "job_restore_points": "Restore points",
    "job_last_failure_reason": "Last failure reason",
}


def _job_status(data: VaultApiData, job_id: int) -> str:
    """Return the status string of the most recent run for a job."""
    run = _latest_run(data, job_id)
    return _status_text(run.status) if run else "idle"


def _job_last_run(data: VaultApiData, job_id: int) -> Any:
    """Return the completion timestamp of the most recent run."""
    run = _latest_run(data, job_id)
    return run.completed_at if run else None


def _job_last_size(data: VaultApiData, job_id: int) -> int | None:
    """Return the size in bytes of the most recent run."""
    run = _latest_run(data, job_id)
    return run.size_bytes if run else None


def _format_duration(seconds: int) -> str:
    """Format a duration in seconds as a compact human-readable string.

    Examples: "45s", "3m 29s", "1h 12m".
    """
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def _job_last_duration(data: VaultApiData, job_id: int) -> str | None:
    """Return the duration of the most recent run as a human-readable string."""
    run = _latest_run(data, job_id)
    return _format_duration(run.duration_seconds) if run else None


def _job_last_duration_attributes(data: VaultApiData, job_id: int) -> dict[str, Any] | None:
    """Expose the raw duration in seconds for automations and templates."""
    run = _latest_run(data, job_id)
    return {"duration_seconds": run.duration_seconds} if run else None


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


def _job_last_failure_reason(data: VaultApiData, job_id: int) -> str:
    """Return a compact failure reason for the latest run, or "No failures"."""
    run = _latest_run(data, job_id)
    if not run:
        return "No failures"

    status = _status_text(run.status)
    if status in {"completed", "running"}:
        return "No failures"

    if run.log:
        try:
            parsed = json.loads(run.log)
        except json.JSONDecodeError:
            return run.log[:255]

        if isinstance(parsed, dict):
            for key in ("error", "message", "reason", "details"):
                value = parsed.get(key)
                if value:
                    return str(value)[:255]

        if isinstance(parsed, list):
            failed_items: list[str] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                item_status = _status_text(item.get("status", ""))
                if item_status and item_status not in {"ok", "completed", "success"}:
                    name = item.get("name") or item.get("item_name") or "item"
                    failed_items.append(str(name))
            if failed_items:
                return f"Failed items: {', '.join(failed_items[:5])}"

    return f"Last run status: {status}"


def _storage_type_text(storage: StorageDestination) -> str:
    """Return storage type as a displayable string for enum/string values."""
    if isinstance(storage.type, StorageType):
        return storage.type.value
    return str(storage.type)


def _storage_capacity_value(storage: StorageDestination, field: str) -> int | None:
    """Return a capacity metric, or None when the destination reports no capacity.

    Remote destinations (S3, WebDAV, ...) may not support capacity probing —
    showing "0 bytes free" there would be misleading.
    """
    capacity = storage.capacity
    if capacity is None or not capacity.total_bytes:
        return None
    return getattr(capacity, field)


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
            suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
            suggested_display_precision=2,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=_job_last_size,
        ),
        VaultJobSensorEntityDescription(
            key="last_duration",
            translation_key="job_last_duration",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_job_last_duration,
            attributes_fn=_job_last_duration_attributes,
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
        VaultJobSensorEntityDescription(
            key="last_failure_reason",
            translation_key="job_last_failure_reason",
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=_job_last_failure_reason,
        ),
    )


# ---------------------------------------------------------------------------
# Storage sensor descriptions (created dynamically per storage destination)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class VaultStorageSensorEntityDescription(SensorEntityDescription):
    """Describes a per-storage Vault sensor entity."""

    value_fn: Callable[[StorageDestination], Any]


_STORAGE_SENSOR_LABELS: dict[str, str] = {
    "storage_name": "Name",
    "storage_type": "Type",
    "storage_health": "Health",
    "storage_free_space": "Free space",
    "storage_used_space": "Used space",
    "storage_total_space": "Total space",
}


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
        value_fn=_storage_type_text,
    ),
    VaultStorageSensorEntityDescription(
        key="health",
        translation_key="storage_health",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: (s.last_health_check_status or "unknown").lower(),
    ),
    VaultStorageSensorEntityDescription(
        key="free_space",
        translation_key="storage_free_space",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=1,
        value_fn=lambda s: _storage_capacity_value(s, "free_bytes"),
    ),
    VaultStorageSensorEntityDescription(
        key="used_space",
        translation_key="storage_used_space",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: _storage_capacity_value(s, "used_bytes"),
    ),
    VaultStorageSensorEntityDescription(
        key="total_space",
        translation_key="storage_total_space",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: _storage_capacity_value(s, "total_bytes"),
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
    job_keys = [tmpl.key for tmpl in job_templates] + ["progress"]

    # One-time prune of registry entries left over from jobs/storage deleted
    # while Home Assistant was not running, or from older integration versions
    # with name-based unique IDs. Runs before adding entities so freed
    # entity_ids can be reclaimed.
    valid_uids = {f"{entry.entry_id}_{desc.key}" for desc in GLOBAL_SENSOR_DESCRIPTIONS}
    valid_uids.update(f"{entry.entry_id}_job_{job.id}_{key}" for job in coordinator.data.jobs for key in job_keys)
    valid_uids.update(
        f"{entry.entry_id}_storage_{storage.id}_{tmpl.key}"
        for storage in coordinator.data.storage
        for tmpl in STORAGE_SENSOR_DESCRIPTIONS
    )
    async_prune_orphan_entities(hass, entry.entry_id, "sensor", valid_uids)

    @callback
    def _check_jobs() -> None:
        current = {job.id for job in coordinator.data.jobs}

        # Drop entities for deleted jobs
        removed = known_jobs - current
        if removed:
            known_jobs.difference_update(removed)
            stale_uids = {f"{entry.entry_id}_job_{job_id}_{key}" for job_id in removed for key in job_keys}
            async_remove_stale_entities(hass, "sensor", stale_uids)

        new_jobs = current - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[SensorEntity] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                entities.extend(
                    VaultJobSensor(coordinator, replace(tmpl, key=f"job_{job.id}_{tmpl.key}"), job)
                    for tmpl in job_templates
                )
                # Add progress sensor per job
                entities.append(VaultJobProgressSensor(coordinator, job))
            async_add_entities(entities)

    @callback
    def _check_storage() -> None:
        current = {storage.id for storage in coordinator.data.storage}

        # Drop entities for deleted storage destinations
        removed = known_storage - current
        if removed:
            known_storage.difference_update(removed)
            stale_uids = {
                f"{entry.entry_id}_storage_{storage_id}_{tmpl.key}"
                for storage_id in removed
                for tmpl in STORAGE_SENSOR_DESCRIPTIONS
            }
            async_remove_stale_entities(hass, "sensor", stale_uids)

        new_storage = current - known_storage
        if new_storage:
            known_storage.update(new_storage)
            entities: list[SensorEntity] = []
            for storage in coordinator.data.storage:
                if storage.id not in new_storage:
                    continue
                entities.extend(
                    VaultStorageSensor(coordinator, replace(tmpl, key=f"storage_{storage.id}_{tmpl.key}"), storage)
                    for tmpl in STORAGE_SENSOR_DESCRIPTIONS
                )
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes, if the description provides them."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)


class VaultJobSensor(SensorEntity, VaultJobEntity):
    """Representation of a per-job Vault sensor."""

    entity_description: VaultJobSensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultJobSensorEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the per-job sensor."""
        label = _JOB_SENSOR_LABELS.get(description.translation_key or "", description.key)
        super().__init__(coordinator, description, job, label)
        self.entity_description = description
        if description.device_class is SensorDeviceClass.DATA_SIZE:
            # Scale the display unit to the current value (MB/GB/TB)
            unit = _auto_data_size_unit(description.value_fn(coordinator.data, job.id))
            if unit is not None:
                self._attr_suggested_unit_of_measurement = unit

    @property
    def native_value(self) -> Any:
        """Return the sensor value for this job."""
        return self.entity_description.value_fn(self.coordinator.data, self._job_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes for this job sensor, if any."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data, self._job_id)


class VaultJobProgressSensor(SensorEntity, VaultJobEntity):
    """Representation of a per-job backup progress sensor (WebSocket-driven)."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        job: BackupJob,
    ) -> None:
        """Initialize the progress sensor."""
        desc = SensorEntityDescription(
            key=f"job_{job.id}_progress",
            translation_key="job_progress",
        )
        super().__init__(coordinator, desc, job, "Progress")

    async def async_added_to_hass(self) -> None:
        """Subscribe to WebSocket events for live progress updates."""
        await super().async_added_to_hass()
        websocket = self.coordinator.config_entry.runtime_data.websocket
        self.async_on_remove(websocket.register_listener(self._handle_ws_event))

    @callback
    def _handle_ws_event(self, event: WebSocketEvent) -> None:
        """Write state immediately when a progress-related event arrives for this job."""
        if event.job_id == self._job_id and event.type in ("backup_progress", "job_run_started", "job_run_completed"):
            self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Return the current progress percentage, or 0 when no backup is running."""
        return self.coordinator.config_entry.runtime_data.progress.get(self._job_id, 0)


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
        self._storage_name = storage.name
        self._name_label = _STORAGE_SENSOR_LABELS.get(description.translation_key or "", description.key)
        if description.device_class is SensorDeviceClass.DATA_SIZE:
            # Scale the display unit to the destination size (MB/GB/TB)
            total = storage.capacity.total_bytes if storage.capacity else None
            unit = _auto_data_size_unit(total)
            if unit is not None:
                self._attr_suggested_unit_of_measurement = unit

    @property
    def name(self) -> str:
        """Return the entity name, tracking storage renames."""
        storage = self._current_storage()
        if storage is not None:
            self._storage_name = storage.name
        return f"Storage {self._storage_name} {self._name_label}"

    def _current_storage(self) -> StorageDestination | None:
        """Return the storage destination for this sensor, if it still exists."""
        return next((s for s in self.coordinator.data.storage if s.id == self._storage_id), None)

    @property
    def native_value(self) -> Any:
        """Return the sensor value for this storage destination."""
        storage = self._current_storage()
        return self.entity_description.value_fn(storage) if storage is not None else None
