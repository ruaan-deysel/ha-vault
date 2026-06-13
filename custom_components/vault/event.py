"""Event platform for the Vault integration."""

from __future__ import annotations

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.models import BackupJob, WebSocketEvent
from .coordinator import VaultConfigEntry, VaultDataUpdateCoordinator
from .entity import VaultJobEntity, async_prune_orphan_entities, async_remove_stale_entities

PARALLEL_UPDATES = 0

EVENT_BACKUP_STARTED = "backup_started"
EVENT_BACKUP_COMPLETED = "backup_completed"
EVENT_BACKUP_FAILED = "backup_failed"
EVENT_MISSING_ITEMS = "missing_items_detected"

_EVENT_ATTRIBUTE_FIELDS = (
    "run_id",
    "status",
    "items_total",
    "items_done",
    "items_failed",
    "size_bytes",
    "message",
    "error",
    "count",
    "items",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VaultConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vault event entities — one per backup job."""
    coordinator = entry.runtime_data.coordinator
    known_jobs: set[int] = set()

    # One-time prune of registry entries left over from jobs deleted while
    # Home Assistant was not running, or from older integration versions with
    # name-based unique IDs. Runs before adding entities so freed entity_ids
    # can be reclaimed.
    valid_uids = {f"{entry.entry_id}_job_{job.id}_last_event" for job in coordinator.data.jobs}
    async_prune_orphan_entities(hass, entry.entry_id, "event", valid_uids)

    @callback
    def _check_jobs() -> None:
        current = {job.id for job in coordinator.data.jobs}

        # Drop entities for deleted jobs
        removed = known_jobs - current
        if removed:
            known_jobs.difference_update(removed)
            stale_uids = {f"{entry.entry_id}_job_{job_id}_last_event" for job_id in removed}
            async_remove_stale_entities(hass, "event", stale_uids)

        new_jobs = current - known_jobs
        if new_jobs:
            known_jobs.update(new_jobs)
            entities = [VaultJobEventEntity(coordinator, job) for job in coordinator.data.jobs if job.id in new_jobs]
            async_add_entities(entities)

    _check_jobs()
    entry.async_on_unload(coordinator.async_add_listener(_check_jobs))


class VaultJobEventEntity(EventEntity, VaultJobEntity):
    """Event entity exposing the backup lifecycle of a single job."""

    _attr_event_types = [
        EVENT_BACKUP_STARTED,
        EVENT_BACKUP_COMPLETED,
        EVENT_BACKUP_FAILED,
        EVENT_MISSING_ITEMS,
    ]

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        job: BackupJob,
    ) -> None:
        """Initialize the per-job event entity."""
        description = EventEntityDescription(
            key=f"job_{job.id}_last_event",
            translation_key="job_last_event",
        )
        super().__init__(coordinator, description, job, "Last event")

    async def async_added_to_hass(self) -> None:
        """Subscribe to WebSocket events for this job."""
        await super().async_added_to_hass()
        websocket = self.coordinator.config_entry.runtime_data.websocket
        self.async_on_remove(websocket.register_listener(self._handle_ws_event))

    @callback
    def _handle_ws_event(self, event: WebSocketEvent) -> None:
        """Translate a job lifecycle WebSocket event into an entity event."""
        if event.job_id != self._job_id:
            return

        if event.type == "job_run_started":
            event_type = EVENT_BACKUP_STARTED
        elif event.type == "job_run_completed":
            status = (event.status or "").lower()
            event_type = EVENT_BACKUP_FAILED if status in ("failed", "partial") else EVENT_BACKUP_COMPLETED
        elif event.type == "stale_items_detected":
            # Vault skips items that no longer exist on the server and still
            # reports the run as completed — surface the alert separately.
            event_type = EVENT_MISSING_ITEMS
        else:
            return

        attributes = {
            field: value for field in _EVENT_ATTRIBUTE_FIELDS if (value := getattr(event, field, None)) is not None
        }
        self._trigger_event(event_type, attributes)
        self.async_write_ha_state()
