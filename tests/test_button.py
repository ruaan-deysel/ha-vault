"""Tests for Vault button platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.exceptions import VaultApiError, VaultConnectionError
from custom_components.vault.api.models import BackupJob, JobRun, JobRunStatus
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er


async def test_buttons_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that button entities are created for each job."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    button_entries = [e for e in entries if e.domain == "button"]

    # One button per job = 3
    assert len(button_entries) == 3


async def test_button_press(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test pressing a button triggers the API call."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    daily_button = next(
        (e for e in entries if "daily_backup_run_now" in e.unique_id),
        None,
    )
    assert daily_button is not None

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": daily_button.entity_id},
        blocking=True,
    )
    mock_api_client.async_run_job.assert_awaited()


async def test_button_press_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test button press raises HomeAssistantError on connection error."""
    mock_api_client.async_run_job = AsyncMock(side_effect=VaultConnectionError("timeout"))

    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    daily_button = next(
        (e for e in entries if "daily_backup_run_now" in e.unique_id),
        None,
    )
    assert daily_button is not None

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": daily_button.entity_id},
            blocking=True,
        )


async def test_button_press_api_error(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test button press raises HomeAssistantError on API error."""
    mock_api_client.async_run_job = AsyncMock(side_effect=VaultApiError("server error"))

    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    daily_button = next(
        (e for e in entries if "daily_backup_run_now" in e.unique_id),
        None,
    )
    assert daily_button is not None

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": daily_button.entity_id},
            blocking=True,
        )


async def test_dynamic_job_detection_button(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test that new jobs appearing via coordinator update create new button entities."""
    registry = er.async_get(hass)
    entries_before = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    button_count_before = len([e for e in entries_before if e.domain == "button"])

    # Add a new job to the mock client
    new_job = BackupJob(id=99, name="New Dynamic Job", enabled=True)
    original_jobs = list(mock_api_client.async_get_jobs.return_value)
    mock_api_client.async_get_jobs.return_value = [*original_jobs, new_job]
    mock_api_client.async_get_job_history.side_effect = (
        lambda job_id, **kwargs: [
            JobRun(
                id=100 + job_id,
                job_id=job_id,
                status=JobRunStatus.COMPLETED,
                items_total=10,
                items_done=10,
                items_failed=0,
                size_bytes=1048576,
            )
        ]
        if job_id not in (3,)
        else []
    )

    # Trigger coordinator refresh
    coordinator = mock_setup_entry.runtime_data.coordinator
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entries_after = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    button_count_after = len([e for e in entries_after if e.domain == "button"])

    # Should have 1 new button for the new job
    assert button_count_after == button_count_before + 1
