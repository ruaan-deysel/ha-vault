"""Tests for Vault integration setup and services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault import _get_entry_from_call, async_setup
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
    # Extract the _on_ws_event callback (first registered listener) from the websocket
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    events: list = []

    def _capture_event(event) -> None:
        events.append(event)

    hass.bus.async_listen("vault_backup_started", _capture_event)

    ws_callback(WebSocketEvent(type="job_run_started", job_id=1))
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["type"] == "job_run_started"
    assert events[0].data["job_id"] == 1


async def test_ws_failed_run_fires_backup_failed_event(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A failed/partial run must fire vault_backup_failed, never vault_backup_completed."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    completed_events: list = []
    failed_events: list = []
    hass.bus.async_listen("vault_backup_completed", completed_events.append)
    hass.bus.async_listen("vault_backup_failed", failed_events.append)

    ws_callback(WebSocketEvent(type="job_run_completed", job_id=1, status="failed", items_failed=1))
    ws_callback(WebSocketEvent(type="job_run_completed", job_id=2, status="partial", items_failed=1))
    await hass.async_block_till_done()

    assert len(completed_events) == 0
    assert len(failed_events) == 2
    assert failed_events[0].data["status"] == "failed"
    assert failed_events[1].data["status"] == "partial"


async def test_ws_successful_run_fires_backup_completed_event(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A successful run still fires vault_backup_completed."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    completed_events: list = []
    hass.bus.async_listen("vault_backup_completed", completed_events.append)

    ws_callback(WebSocketEvent(type="job_run_completed", job_id=1, status="completed"))
    await hass.async_block_till_done()

    assert len(completed_events) == 1


async def test_ws_state_change_triggers_coordinator_refresh(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """State-changing WS events request an immediate coordinator refresh."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]
    coordinator = mock_setup_entry.runtime_data.coordinator

    with patch.object(coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh:
        ws_callback(WebSocketEvent(type="job_run_completed", job_id=1, status="failed"))
        await hass.async_block_till_done()
        assert mock_refresh.await_count == 1

        # Progress events are high-frequency noise — no refresh
        ws_callback(WebSocketEvent(type="backup_progress", job_id=1, percent=50))
        await hass.async_block_till_done()
        assert mock_refresh.await_count == 1

        ws_callback(WebSocketEvent(type="anomaly.raised", data={"ID": 1}))
        await hass.async_block_till_done()
        assert mock_refresh.await_count == 2


async def test_ws_stale_items_event_carries_payload(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """stale_items_detected events expose count and items on the HA bus."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    events: list = []
    hass.bus.async_listen("vault_stale_items_detected", events.append)

    ws_callback(
        WebSocketEvent(
            type="stale_items_detected",
            job_id=75,
            count=1,
            items=[{"item_id": 104, "item_name": "jackett", "item_type": "container"}],
        )
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["count"] == 1
    assert events[0].data["items"][0]["item_name"] == "jackett"


async def test_ws_anomaly_event_fires_on_bus(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """anomaly.* WS events are mapped to HA bus events with their payload."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    events: list = []
    hass.bus.async_listen("vault_anomaly_updated", events.append)

    ws_callback(
        WebSocketEvent(
            type="anomaly.updated",
            data={"ID": 11, "Severity": "critical", "Summary": "backup shrank to 0 B"},
        )
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["data"]["Summary"] == "backup shrank to 0 B"


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
    """Test WebSocket events update progress tracking in runtime data."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    # backup_progress event should set progress
    ws_callback(WebSocketEvent(type="backup_progress", job_id=1, percent=50))
    assert mock_setup_entry.runtime_data.progress[1] == 50

    # job_run_completed should remove progress
    ws_callback(WebSocketEvent(type="job_run_completed", job_id=1))
    assert 1 not in mock_setup_entry.runtime_data.progress


async def test_ws_event_progress_started(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Test job_run_started sets initial progress to 0."""
    ws_callback = mock_websocket.register_listener.call_args_list[0][0][0]

    ws_callback(WebSocketEvent(type="job_run_started", job_id=5))
    assert mock_setup_entry.runtime_data.progress[5] == 0


async def test_no_hass_data_used(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that the integration stores everything in runtime_data, not hass.data."""
    assert DOMAIN not in hass.data

    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN not in hass.data


async def test_get_entry_from_call_unknown_config_entry_id(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test resolving unknown config_entry_id raises ServiceValidationError."""
    call = MagicMock()
    call.data = {"config_entry_id": "does-not-exist"}

    with pytest.raises(ServiceValidationError, match="No Vault config entry found"):
        _get_entry_from_call(hass, call)


async def test_get_entry_from_call_multiple_entries_requires_id(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test resolving without config_entry_id fails when multiple entries exist."""
    second_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Vault (2.0.0)",
        data={"host": "192.168.1.101", "port": 24085},
        unique_id="192.168.1.101:24085",
    )
    second_entry.add_to_hass(hass)

    call = MagicMock()
    call.data = {}

    with pytest.raises(ServiceValidationError, match="Multiple Vault config entries found"):
        _get_entry_from_call(hass, call)


async def test_get_entry_from_call_with_matching_config_entry_id(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test resolving explicit config_entry_id returns the matching entry."""
    call = MagicMock()
    call.data = {"config_entry_id": mock_setup_entry.entry_id}

    resolved = _get_entry_from_call(hass, call)
    assert resolved.entry_id == mock_setup_entry.entry_id
