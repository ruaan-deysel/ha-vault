"""Tests for the Vault event platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.models import WebSocketEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


def _event_entity_id(hass: HomeAssistant, entry: MockConfigEntry, job_id: int) -> str:
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    reg_entry = next(e for e in entries if e.unique_id == f"{entry.entry_id}_job_{job_id}_last_event")
    return reg_entry.entity_id


def _ws_callbacks(mock_websocket: MagicMock) -> list:
    return [call[0][0] for call in mock_websocket.register_listener.call_args_list]


def _dispatch(mock_websocket: MagicMock, event: WebSocketEvent) -> None:
    for callback in _ws_callbacks(mock_websocket):
        callback(event)


async def test_event_entities_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """One event entity is created per job."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    event_entries = [e for e in entries if e.domain == "event"]
    assert len(event_entries) == 3


async def test_event_backup_failed(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A job_run_completed event with failed status triggers backup_failed."""
    entity_id = _event_entity_id(hass, mock_setup_entry, 1)

    _dispatch(
        mock_websocket,
        WebSocketEvent(type="job_run_completed", job_id=1, run_id=10, status="failed", items_failed=1),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["event_type"] == "backup_failed"
    assert state.attributes["status"] == "failed"
    assert state.attributes["items_failed"] == 1


async def test_event_backup_partial_maps_to_failed(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A partial run is reported as backup_failed."""
    entity_id = _event_entity_id(hass, mock_setup_entry, 1)

    _dispatch(
        mock_websocket,
        WebSocketEvent(type="job_run_completed", job_id=1, run_id=10, status="partial"),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["event_type"] == "backup_failed"


async def test_event_backup_completed(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A successful run triggers backup_completed."""
    entity_id = _event_entity_id(hass, mock_setup_entry, 1)

    _dispatch(
        mock_websocket,
        WebSocketEvent(type="job_run_completed", job_id=1, run_id=10, status="completed", size_bytes=1024),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["event_type"] == "backup_completed"


async def test_event_missing_items_detected(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """A stale_items_detected event triggers missing_items_detected with details."""
    entity_id = _event_entity_id(hass, mock_setup_entry, 1)

    _dispatch(
        mock_websocket,
        WebSocketEvent(
            type="stale_items_detected",
            job_id=1,
            count=1,
            items=[{"item_id": 104, "item_name": "jackett", "item_type": "container"}],
        ),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["event_type"] == "missing_items_detected"
    assert state.attributes["count"] == 1
    assert state.attributes["items"][0]["item_name"] == "jackett"


async def test_event_ignores_other_jobs(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_websocket: MagicMock,
) -> None:
    """Events for one job do not touch entities of other jobs."""
    entity_id_job2 = _event_entity_id(hass, mock_setup_entry, 2)

    _dispatch(
        mock_websocket,
        WebSocketEvent(type="job_run_completed", job_id=1, run_id=10, status="failed"),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_job2)
    assert state is not None
    assert state.state == "unknown"
