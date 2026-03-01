"""The Vault integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
    Platform.SENSOR,
]

# Service schemas
SERVICE_RUN_BACKUP = "run_backup"
SERVICE_RESTORE = "restore"
SERVICE_TEST_STORAGE = "test_storage"

SCHEMA_RUN_BACKUP = vol.Schema(
    {
        vol.Optional("job_id"): cv.positive_int,
        vol.Optional("job_name"): cv.string,
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
    }
)

SCHEMA_TEST_STORAGE = vol.Schema(
    {
        vol.Required("storage_id"): cv.positive_int,
    }
)


def _get_client_from_entry(hass: HomeAssistant, call: ServiceCall) -> VaultApiClient:
    """Return the API client from the first loaded config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        msg = "No Vault config entries found"
        raise ServiceValidationError(msg)
    entry: VaultConfigEntry = entries[0]  # type: ignore[assignment]
    return entry.runtime_data.client


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Vault integration — register services."""

    async def _handle_run_backup(call: ServiceCall) -> None:
        """Handle vault.run_backup service call."""
        client = _get_client_from_entry(hass, call)
        job_id: int | None = call.data.get("job_id")
        job_name: str | None = call.data.get("job_name")

        if job_id is None and job_name is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_job_id",
            )

        # Resolve job_name → job_id
        entry: VaultConfigEntry = hass.config_entries.async_entries(DOMAIN)[0]  # type: ignore[assignment]
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
    await websocket.async_connect()

    # Initialize progress tracking store
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("progress", {})

    # Fire HA events from WebSocket messages and track progress
    def _on_ws_event(event: WebSocketEvent) -> None:
        ha_event = VaultWebSocketClient.get_ha_event_type(event.type)
        if ha_event:
            hass.bus.async_fire(ha_event, event.model_dump(exclude_none=True))

        # Track backup progress from WebSocket events
        job_id = event.job_id
        if job_id is not None:
            if event.type == "backup_progress":
                hass.data[DOMAIN]["progress"][job_id] = event.percent or 0
            elif event.type == "job_run_completed":
                hass.data[DOMAIN]["progress"].pop(job_id, None)
            elif event.type == "job_run_started":
                hass.data[DOMAIN]["progress"][job_id] = 0

    websocket.register_listener(_on_ws_event)

    entry.runtime_data = VaultData(
        client=client,
        coordinator=coordinator,
        websocket=websocket,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VaultConfigEntry) -> bool:
    """Unload a Vault config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.websocket.async_disconnect()
        # Clean up progress tracking if no more loaded entries
        remaining = [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id != entry.entry_id]
        if not remaining:
            hass.data.pop(DOMAIN, None)
    return unload_ok
