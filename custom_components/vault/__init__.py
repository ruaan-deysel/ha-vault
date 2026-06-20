"""The Vault integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntry

from .api import VaultApiClient, VaultApiError, VaultConnectionError, VaultWebSocketClient
from .api.models import WebSocketEvent
from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_TLS, DEFAULT_PORT, DOMAIN, LOGGER
from .coordinator import VaultData, VaultDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import VaultConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# WS events that change state shown by coordinator-backed entities. Each one
# triggers a (debounced) refresh so the UI syncs immediately instead of
# waiting for the next poll.
REFRESH_WS_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "job_run_started",
        "job_run_completed",
        "verify_complete",
        "stale_items_detected",
        "anomaly.raised",
        "anomaly.updated",
        "anomaly.resolved",
        "anomaly.acknowledged",
        "storage_health",
        "storage_capacity_updated",
        "config_changed",
        "import_completed",
    }
)

# Service schemas
SERVICE_RUN_BACKUP = "run_backup"
SERVICE_RESTORE = "restore"
SERVICE_TEST_STORAGE = "test_storage"

SCHEMA_RUN_BACKUP = vol.Schema(
    {
        vol.Optional("job_id"): cv.positive_int,
        vol.Optional("job_name"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SCHEMA_RESTORE = vol.Schema(
    {
        vol.Required("job_id"): cv.positive_int,
        vol.Required("restore_point_id"): cv.positive_int,
        vol.Required("item_name"): cv.string,
        vol.Required("item_type"): vol.In(["container", "vm", "folder"]),
        vol.Optional("passphrase"): cv.string,
        vol.Optional("destination"): cv.string,
        vol.Optional("config_entry_id"): cv.string,
    }
)

SCHEMA_TEST_STORAGE = vol.Schema(
    {
        vol.Required("storage_id"): cv.positive_int,
        vol.Optional("config_entry_id"): cv.string,
    }
)


def _validate_entry_loaded(entry: VaultConfigEntry) -> VaultConfigEntry:
    """Raise unless the config entry is loaded (runtime_data is only set then)."""
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            f"Vault config entry '{entry.title}' is not loaded",
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"title": entry.title},
        )
    return entry


def _get_entry_from_call(hass: HomeAssistant, call: ServiceCall) -> VaultConfigEntry:
    """Resolve target config entry from service call context."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ServiceValidationError(
            "No Vault config entries found",
            translation_domain=DOMAIN,
            translation_key="no_config_entries",
        )

    requested_entry_id: str | None = call.data.get("config_entry_id")
    if requested_entry_id:
        for entry in entries:
            if entry.entry_id == requested_entry_id:
                return _validate_entry_loaded(entry)  # type: ignore[arg-type]
        raise ServiceValidationError(
            f"No Vault config entry found for config_entry_id '{requested_entry_id}'",
            translation_domain=DOMAIN,
            translation_key="entry_not_found",
            translation_placeholders={"entry_id": requested_entry_id},
        )

    if len(entries) > 1:
        raise ServiceValidationError(
            "Multiple Vault config entries found; provide config_entry_id",
            translation_domain=DOMAIN,
            translation_key="multiple_config_entries",
        )

    return _validate_entry_loaded(entries[0])  # type: ignore[arg-type]


def _get_client_from_entry(hass: HomeAssistant, call: ServiceCall) -> VaultApiClient:
    """Return the API client for the resolved config entry."""
    entry = _get_entry_from_call(hass, call)
    return entry.runtime_data.client


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Vault integration — register services."""

    async def _handle_run_backup(call: ServiceCall) -> None:
        """Handle vault.run_backup service call."""
        entry = _get_entry_from_call(hass, call)
        client = entry.runtime_data.client
        job_id: int | None = call.data.get("job_id")
        job_name: str | None = call.data.get("job_name")

        if job_id is None and job_name is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_job_id",
            )

        # Resolve job_name → job_id
        jobs = entry.runtime_data.coordinator.data.jobs

        if job_name is not None and job_id is None:
            matched = [j for j in jobs if j.name.lower() == job_name.lower()]
            if not matched:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_job_id",
                )
            job_id = matched[0].id

        # Validate job_id exists in loaded jobs
        if not any(job.id == job_id for job in jobs):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_job_id",
            )

        # At this point job_id is guaranteed to be set
        assert job_id is not None

        try:
            await client.async_run_job(job_id)
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

    async def _handle_restore(call: ServiceCall) -> None:
        """Handle vault.restore service call."""
        client = _get_client_from_entry(hass, call)
        payload: dict[str, Any] = {
            "restore_point_id": call.data["restore_point_id"],
            "item_name": call.data["item_name"],
            "item_type": call.data["item_type"],
        }
        if "passphrase" in call.data:
            payload["passphrase"] = call.data["passphrase"]
        if "destination" in call.data:
            payload["destination"] = call.data["destination"]
        try:
            await client.async_restore(call.data["job_id"], payload)
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

    async def _handle_test_storage(call: ServiceCall) -> None:
        """Handle vault.test_storage service call."""
        client = _get_client_from_entry(hass, call)
        try:
            result = await client.async_test_storage(call.data["storage_id"])
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
        if not result.success:
            LOGGER.warning("Storage test failed: %s", result.error)

    hass.services.async_register(DOMAIN, SERVICE_RUN_BACKUP, _handle_run_backup, schema=SCHEMA_RUN_BACKUP)
    hass.services.async_register(DOMAIN, SERVICE_RESTORE, _handle_restore, schema=SCHEMA_RESTORE)
    hass.services.async_register(DOMAIN, SERVICE_TEST_STORAGE, _handle_test_storage, schema=SCHEMA_TEST_STORAGE)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: VaultConfigEntry) -> bool:
    """Set up Vault from a config entry."""
    host: str = entry.data[CONF_HOST]
    port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
    api_key: str | None = entry.data.get(CONF_API_KEY)
    tls: bool = entry.data.get(CONF_TLS, False)
    session = async_get_clientsession(hass)

    client = VaultApiClient(host=host, port=port, session=session, api_key=api_key, tls=tls)
    websocket = VaultWebSocketClient(host=host, port=port, session=session, logger=LOGGER, api_key=api_key, tls=tls)
    coordinator = VaultDataUpdateCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    data = VaultData(
        client=client,
        coordinator=coordinator,
        websocket=websocket,
    )
    entry.runtime_data = data

    # Fire HA events from WebSocket messages and track progress
    def _on_ws_event(event: WebSocketEvent) -> None:
        ha_event = VaultWebSocketClient.get_ha_event_type(event.type)
        # A failed run must never fire vault_backup_completed — automations
        # keying on the event type would treat the failure as a success.
        if event.type == "job_run_completed" and (event.status or "").lower() in ("failed", "partial"):
            ha_event = "vault_backup_failed"
        if ha_event:
            hass.bus.async_fire(ha_event, {"entry_id": entry.entry_id, **event.model_dump(exclude_none=True)})

        # Track backup progress from WebSocket events
        job_id = event.job_id
        if job_id is not None:
            if event.type == "backup_progress":
                data.progress[job_id] = event.percent or 0
            elif event.type == "job_run_completed":
                data.progress.pop(job_id, None)
            elif event.type == "job_run_started":
                data.progress[job_id] = 0

        # Keep coordinator-backed entities in sync with Vault state changes
        # (job status, anomalies, storage health) without waiting for the
        # next poll. async_request_refresh is debounced, so event bursts
        # collapse into a single API round-trip.
        if event.type in REFRESH_WS_EVENT_TYPES:
            entry.async_create_background_task(
                hass,
                coordinator.async_request_refresh(),
                name=f"vault refresh after {event.type}",
            )

    # Register the listener before connecting so no early events are dropped
    websocket.register_listener(_on_ws_event)
    await websocket.async_connect()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VaultConfigEntry) -> bool:
    """Unload a Vault config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.websocket.async_disconnect()
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: VaultConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Return True if the device may be removed from the device registry.

    The main Vault device is protected from accidental UI deletion.
    Orphaned backup-job or storage-target devices that no longer appear in
    the coordinator data can be removed by the user.
    """
    host: str = config_entry.data[CONF_HOST]
    port: int = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
    main_identifier = (DOMAIN, f"{host}:{port}")
    return main_identifier not in device_entry.identifiers
