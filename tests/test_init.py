"""Tests for Vault integration setup and services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault import async_setup
from custom_components.vault.api.exceptions import VaultApiError, VaultConnectionError
from custom_components.vault.api.models import StorageTestResult, WebSocketEvent
from custom_components.vault.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError


async def test_setup_and_unload(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test successful setup and unload of a config entry."""
    assert mock_setup_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_setup_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_creates_platforms(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that setup creates sensor, binary_sensor, and button platforms."""
    states = hass.states.async_all()
    assert len(states) > 0


async def test_service_registration(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that services are registered."""
    assert hass.services.has_service(DOMAIN, "run_backup")
    assert hass.services.has_service(DOMAIN, "restore")
    assert hass.services.has_service(DOMAIN, "test_storage")


async def test_service_run_backup(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test run_backup service call."""
    await hass.services.async_call(DOMAIN, "run_backup", {"job_id": 1}, blocking=True)
    mock_api_client.async_run_job.assert_awaited_once_with(1)


async def test_service_run_backup_invalid_job(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test run_backup with invalid job_id raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "run_backup", {"job_id": 9999}, blocking=True)


async def test_service_run_backup_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test run_backup raises HomeAssistantError on connection error."""
    mock_api_client.async_run_job = AsyncMock(side_effect=VaultConnectionError("timeout"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "run_backup", {"job_id": 1}, blocking=True)


async def test_service_run_backup_api_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test run_backup raises HomeAssistantError on API error."""
    mock_api_client.async_run_job = AsyncMock(side_effect=VaultApiError("server error"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "run_backup", {"job_id": 1}, blocking=True)


async def test_service_restore(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test restore service call."""
    await hass.services.async_call(
        DOMAIN,
        "restore",
        {
            "job_id": 1,
            "restore_point_id": 1,
            "item_name": "myapp",
            "item_type": "container",
        },
        blocking=True,
    )
    mock_api_client.async_restore.assert_awaited_once()


async def test_service_restore_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test restore raises HomeAssistantError on connection error."""
    mock_api_client.async_restore = AsyncMock(side_effect=VaultConnectionError("timeout"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "restore",
            {
                "job_id": 1,
                "restore_point_id": 1,
                "item_name": "myapp",
                "item_type": "container",
            },
            blocking=True,
        )


async def test_service_test_storage(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test test_storage service call."""
    await hass.services.async_call(DOMAIN, "test_storage", {"storage_id": 1}, blocking=True)
    mock_api_client.async_test_storage.assert_awaited_once_with(1)


async def test_service_test_storage_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test test_storage raises HomeAssistantError on connection error."""
    mock_api_client.async_test_storage = AsyncMock(side_effect=VaultConnectionError("timeout"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "test_storage", {"storage_id": 1}, blocking=True)


async def test_unload_disconnects_websocket(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Test that unloading disconnects the websocket."""
    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()
    mock_websocket.async_disconnect.assert_awaited_once()


async def test_service_no_entries(hass: HomeAssistant) -> None:
    """Test service call with no config entries raises ServiceValidationError."""
    await async_setup(hass, {})
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "run_backup", {"job_id": 1}, blocking=True)


async def test_service_restore_with_optional_params(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test restore service with passphrase and destination optional fields."""
    await hass.services.async_call(
        DOMAIN,
        "restore",
        {
            "job_id": 1,
            "restore_point_id": 1,
            "item_name": "myapp",
            "item_type": "container",
            "passphrase": "secret",
            "destination": "/mnt/restore",
        },
        blocking=True,
    )
    call_args = mock_api_client.async_restore.call_args
    payload = call_args[0][1]
    assert payload["passphrase"] == "secret"
    assert payload["destination"] == "/mnt/restore"


async def test_service_restore_api_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test restore raises HomeAssistantError on API error."""
    mock_api_client.async_restore = AsyncMock(side_effect=VaultApiError("server error"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "restore",
            {
                "job_id": 1,
                "restore_point_id": 1,
                "item_name": "myapp",
                "item_type": "container",
            },
            blocking=True,
        )


async def test_service_test_storage_api_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test test_storage raises HomeAssistantError on API error."""
    mock_api_client.async_test_storage = AsyncMock(side_effect=VaultApiError("server error"))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "test_storage", {"storage_id": 1}, blocking=True)


async def test_service_test_storage_failure(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test test_storage when storage test fails (success=False)."""
    mock_api_client.async_test_storage = AsyncMock(
        return_value=StorageTestResult(success=False, error="Connection timed out")
    )
    # Should not raise — just log a warning
    await hass.services.async_call(DOMAIN, "test_storage", {"storage_id": 1}, blocking=True)


async def test_ws_event_callback(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Test WebSocket event callback fires HA event."""
    # Extract the _on_ws_event callback that was registered with the websocket
    ws_callback = mock_websocket.register_listener.call_args[0][0]

    events: list = []
    hass.bus.async_listen("vault_backup_started", lambda e: events.append(e))

    ws_callback(WebSocketEvent(type="job_run_started", job_id=1))
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["type"] == "job_run_started"
    assert events[0].data["job_id"] == 1


async def test_service_run_backup_by_name(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test run_backup service call by job_name."""
    await hass.services.async_call(DOMAIN, "run_backup", {"job_name": "Daily Backup"}, blocking=True)
    mock_api_client.async_run_job.assert_awaited_once_with(1)


async def test_service_run_backup_by_name_case_insensitive(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test run_backup service call by job_name is case insensitive."""
    await hass.services.async_call(DOMAIN, "run_backup", {"job_name": "daily backup"}, blocking=True)
    mock_api_client.async_run_job.assert_awaited_once_with(1)


async def test_service_run_backup_invalid_name(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test run_backup with non-existent job_name raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "run_backup", {"job_name": "Nonexistent Job"}, blocking=True)


async def test_service_run_backup_no_id_or_name(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test run_backup with neither job_id nor job_name raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "run_backup", {}, blocking=True)


async def test_ws_event_progress_tracking(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Test WebSocket events update progress tracking in hass.data."""
    ws_callback = mock_websocket.register_listener.call_args[0][0]

    # backup_progress event should set progress
    ws_callback(WebSocketEvent(type="backup_progress", job_id=1, percent=50))
    assert hass.data[DOMAIN]["progress"][1] == 50

    # job_run_completed should remove progress
    ws_callback(WebSocketEvent(type="job_run_completed", job_id=1))
    assert 1 not in hass.data[DOMAIN]["progress"]


async def test_ws_event_progress_started(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Test job_run_started sets initial progress to 0."""
    ws_callback = mock_websocket.register_listener.call_args[0][0]

    ws_callback(WebSocketEvent(type="job_run_started", job_id=5))
    assert hass.data[DOMAIN]["progress"][5] == 0


async def test_unload_cleans_hass_data(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that unloading the last entry cleans up hass.data."""
    assert DOMAIN in hass.data

    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()

    # After unloading the only entry, hass.data[DOMAIN] should be cleaned up
    assert DOMAIN not in hass.data
