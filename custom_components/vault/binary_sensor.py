"""Binary sensor platform for the Vault integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

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
from .entity import VaultEntity, VaultJobEntity, async_prune_orphan_entities, async_remove_stale_entities

PARALLEL_UPDATES = 0


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
    attributes_fn: Callable[[VaultApiData, int], dict[str, object] | None] | None = None


_JOB_BINARY_SENSOR_LABELS: dict[str, str] = {
    "job_running": "Running",
    "job_last_success": "Last run successful",
    "job_problem": "Problem",
}


def _is_job_running(data: VaultApiData, job_id: int) -> bool:
    """Return True if the most recent run for this job is running."""
    runs = data.job_runs.get(job_id, [])
    if not runs:
        return False
    status_text = str(getattr(runs[0].status, "value", runs[0].status)).lower()
    return status_text == "running"


def _is_job_last_success(data: VaultApiData, job_id: int) -> bool:
    """Return True if the most recent run for this job completed successfully."""
    runs = data.job_runs.get(job_id, [])
    if not runs:
        return False
    status_text = str(getattr(runs[0].status, "value", runs[0].status)).lower()
    return status_text == "completed"


def _job_anomalies(data: VaultApiData, job_id: int) -> list:
    """Return open anomalies scoped to this job."""
    return [a for a in data.anomalies if a.scope_kind == "job" and a.scope_id == job_id]


def _job_has_problem(data: VaultApiData, job_id: int) -> bool:
    """Return True when Vault reports an open anomaly for this job."""
    return bool(_job_anomalies(data, job_id))


def _job_problem_attributes(data: VaultApiData, job_id: int) -> dict[str, object] | None:
    """Expose the anomaly details behind a job problem state."""
    anomalies = _job_anomalies(data, job_id)
    if not anomalies:
        return None
    return {
        "anomalies": [
            {
                "detector": a.detector,
                "severity": a.severity,
                "summary": a.summary,
                "first_seen_at": a.first_seen_at.isoformat() if a.first_seen_at else None,
                "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
            }
            for a in anomalies
        ]
    }


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
    VaultJobBinarySensorEntityDescription(
        key="problem",
        translation_key="job_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_job_has_problem,
        attributes_fn=_job_problem_attributes,
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

    # One-time prune of registry entries left over from jobs deleted while
    # Home Assistant was not running, or from older integration versions with
    # name-based unique IDs. Runs before adding entities so freed entity_ids
    # can be reclaimed.
    valid_uids = {f"{entry.entry_id}_{desc.key}" for desc in GLOBAL_BINARY_SENSOR_DESCRIPTIONS}
    valid_uids.update(
        f"{entry.entry_id}_job_{job.id}_{tmpl.key}"
        for job in coordinator.data.jobs
        for tmpl in PER_JOB_BINARY_SENSOR_TEMPLATES
    )
    async_prune_orphan_entities(hass, entry.entry_id, "binary_sensor", valid_uids)

    # Add global binary sensors once
    async_add_entities([VaultBinarySensor(coordinator, desc) for desc in GLOBAL_BINARY_SENSOR_DESCRIPTIONS])

    # Per-job binary sensors with dynamic detection
    @callback
    def _check_jobs() -> None:
        current = {job.id for job in coordinator.data.jobs}

        # Drop entities for deleted jobs
        removed = known_jobs - current
        if removed:
            known_jobs.difference_update(removed)
            stale_uids = {
                f"{entry.entry_id}_job_{job_id}_{tmpl.key}"
                for job_id in removed
                for tmpl in PER_JOB_BINARY_SENSOR_TEMPLATES
            }
            async_remove_stale_entities(hass, "binary_sensor", stale_uids)

        new_jobs = current - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities: list[BinarySensorEntity] = []
            for job in coordinator.data.jobs:
                if job.id not in new_jobs:
                    continue
                entities.extend(
                    VaultJobBinarySensor(coordinator, replace(tmpl, key=f"job_{job.id}_{tmpl.key}"), job)
                    for tmpl in PER_JOB_BINARY_SENSOR_TEMPLATES
                )
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


class VaultJobBinarySensor(BinarySensorEntity, VaultJobEntity):
    """Representation of a per-job Vault binary sensor."""

    entity_description: VaultJobBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        description: VaultJobBinarySensorEntityDescription,
        job: BackupJob,
    ) -> None:
        """Initialize the per-job binary sensor."""
        label = _JOB_BINARY_SENSOR_LABELS.get(description.translation_key or "", description.key)
        super().__init__(coordinator, description, job, label)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on for this job."""
        return self.entity_description.is_on_fn(self.coordinator.data, self._job_id)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return extra attributes for this job, if the description provides them."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data, self._job_id)
