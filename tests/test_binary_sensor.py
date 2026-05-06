"""Tests for Vault binary sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.models import BackupJob, JobRun, JobRunStatus
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_global_binary_sensors_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that global binary sensor entities are created."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    binary_entries = [e for e in entries if e.domain == "binary_sensor"]

    # Global: vault_online (1)
    # Per-job: 3 jobs x 2 templates = 6
    # Total: 7
    assert len(binary_entries) == 7


async def test_vault_online_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test vault_online binary sensor state."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    online_entry = next(
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_vault_online"),
        None,
    )
    assert online_entry is not None
    state = hass.states.get(online_entry.entity_id)
    assert state is not None
    # Health status is "ok" which is in the _is_online check
    assert state.state == "on"


async def test_per_job_running_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test per-job running binary sensor — idle job is off."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    # Job 1 "Daily Backup" — mock_api_client returns COMPLETED, not running
    daily_running = next(
        (e for e in entries if "daily_backup_running" in e.unique_id),
        None,
    )
    assert daily_running is not None
    state = hass.states.get(daily_running.entity_id)
    assert state is not None
    assert state.state == "off"


async def test_per_job_last_success_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test per-job last_success binary sensor."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    daily_success = next(
        (e for e in entries if "daily_backup_last_success" in e.unique_id),
        None,
    )
    assert daily_success is not None
    state = hass.states.get(daily_success.entity_id)
    assert state is not None
    # Job 1 has COMPLETED run — last run was success
    assert state.state == "on"


async def test_disabled_job_has_no_run(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that disabled job with no runs has correct sensor state."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    disabled_running = next(
        (e for e in entries if "disabled_job_running" in e.unique_id),
        None,
    )
    assert disabled_running is not None
    state = hass.states.get(disabled_running.entity_id)
    assert state is not None
    # Job 3 "Disabled Job" has empty runs list
    assert state.state == "off"


async def test_dynamic_job_detection_binary_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test that new jobs appearing via coordinator update create new binary sensor entities."""
    registry = er.async_get(hass)
    entries_before = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    binary_count_before = len([e for e in entries_before if e.domain == "binary_sensor"])

    # Add a new job to the mock client
    new_job = BackupJob(id=99, name="New Dynamic Job", enabled=True)
    original_jobs = list(mock_api_client.async_get_jobs.return_value)
    mock_api_client.async_get_jobs.return_value = [*original_jobs, new_job]
    mock_api_client.async_get_job_history.side_effect = lambda job_id, **kwargs: (
        [
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
        if job_id != 3
        else []
    )

    # Trigger coordinator refresh
    coordinator = mock_setup_entry.runtime_data.coordinator
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entries_after = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    binary_count_after = len([e for e in entries_after if e.domain == "binary_sensor"])

    # Should have 2 new per-job binary sensors for the new job
    assert binary_count_after == binary_count_before + 2
