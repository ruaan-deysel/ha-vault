"""Tests for Vault sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.models import (
    BackupJob,
    JobRun,
    JobRunStatus,
    StorageDestination,
    StorageType,
    VaultApiData,
)
from custom_components.vault.const import DOMAIN
from custom_components.vault.sensor import _job_last_size, _job_restore_points
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_global_sensors_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that global sensor entities are created."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    sensor_entries = [e for e in entries if e.domain == "sensor"]

    # Global: vault_status, vault_version, jobs_total, jobs_enabled, encryption_status (5)
    # Per-job: 3 jobs x 8 sensors = 24
    # Per-job progress: 3 jobs x 1 = 3
    # Per-storage: 2 storage x 2 sensors = 4
    # Total: 36
    assert len(sensor_entries) == 36


async def test_vault_status_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test vault_status sensor has correct state."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    status_entry = next(
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_vault_status"),
        None,
    )
    assert status_entry is not None
    state = hass.states.get(status_entry.entity_id)
    assert state is not None
    assert state.state == "ok"


async def test_vault_version_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test vault_version sensor shows version."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    version_entry = next(
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_vault_version"),
        None,
    )
    assert version_entry is not None
    state = hass.states.get(version_entry.entity_id)
    assert state is not None
    assert state.state == "1.0.0"


async def test_disabled_by_default_sensors(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that noisy sensors are disabled by default."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    disabled_keys = {"jobs_total", "jobs_enabled", "encryption_status"}
    for entry in entries:
        uid = entry.unique_id.replace(f"{mock_setup_entry.entry_id}_", "")
        if uid in disabled_keys:
            assert entry.disabled_by is not None, f"{uid} should be disabled by default"


async def test_per_job_sensors_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test per-job sensors are created."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    daily_status = next(
        (e for e in entries if "daily_backup_status" in e.unique_id),
        None,
    )
    assert daily_status is not None


async def test_job_status_sensor_state(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that per-job status sensor returns correct state."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    daily_status = next(
        (e for e in entries if "daily_backup_status" in e.unique_id),
        None,
    )
    assert daily_status is not None
    state = hass.states.get(daily_status.entity_id)
    assert state is not None
    # Job 1 (Daily Backup) — mock_api_client returns COMPLETED for job_id=1
    assert state.state == "completed"


async def test_job_last_size_no_runs(mock_vault_data: VaultApiData) -> None:
    """Test _job_last_size returns None when job has no runs."""
    # Job 3 has empty runs list
    result = _job_last_size(mock_vault_data, 3)
    assert result is None


async def test_job_restore_points(mock_vault_data: VaultApiData) -> None:
    """Test _job_restore_points returns correct count."""
    assert _job_restore_points(mock_vault_data, 1) == 5
    assert _job_restore_points(mock_vault_data, 3) == 0
    # Unknown job ID defaults to 0
    assert _job_restore_points(mock_vault_data, 999) == 0


async def test_dynamic_job_detection_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_api_client: MagicMock,
) -> None:
    """Test that new jobs appearing via coordinator update create new sensor entities."""
    registry = er.async_get(hass)
    entries_before = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    sensor_count_before = len([e for e in entries_before if e.domain == "sensor"])

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
    sensor_count_after = len([e for e in entries_after if e.domain == "sensor"])

    # Should have 9 new entities for the new job (8 sensors + 1 progress)
    assert sensor_count_after == sensor_count_before + 9


async def test_progress_sensor_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test progress sensor returns value from hass.data store."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    progress_entry = next(
        (e for e in entries if "daily_backup_progress" in e.unique_id),
        None,
    )
    assert progress_entry is not None

    # Initially no progress in store — should be unknown/None
    state = hass.states.get(progress_entry.entity_id)
    assert state is not None
    assert state.state == "unknown"

    # Set progress in hass.data
    hass.data[DOMAIN]["progress"][1] = 42
    # Trigger state write by refreshing coordinator
    coordinator = mock_setup_entry.runtime_data.coordinator
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(progress_entry.entity_id)
    assert state is not None
    assert state.state == "42"


async def test_storage_sensors_created(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage sensors are created for each storage destination."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    storage_entries = [e for e in entries if "storage_" in e.unique_id]
    # 2 storage destinations x 2 sensors each = 4
    assert len(storage_entries) == 4


async def test_storage_sensor_name_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage name sensor has correct value."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    name_entry = next(
        (e for e in entries if "local_backup_name" in e.unique_id),
        None,
    )
    assert name_entry is not None
    state = hass.states.get(name_entry.entity_id)
    assert state is not None
    assert state.state == "Local Backup"


async def test_storage_sensor_type_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage type sensor has correct value."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    type_entry = next(
        (e for e in entries if "s3_bucket_type" in e.unique_id),
        None,
    )
    assert type_entry is not None
    state = hass.states.get(type_entry.entity_id)
    assert state is not None
    assert state.state == "s3"


async def test_storage_sensor_returns_none_when_removed(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage sensor returns None when storage destination is removed."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    name_entry = next(
        (e for e in entries if "local_backup_name" in e.unique_id),
        None,
    )
    assert name_entry is not None

    # Remove all storage destinations from coordinator data
    coordinator = mock_setup_entry.runtime_data.coordinator
    coordinator.data = VaultApiData(
        health=coordinator.data.health,
        settings=coordinator.data.settings,
        encryption=coordinator.data.encryption,
        storage=[],
        jobs=coordinator.data.jobs,
        job_runs=coordinator.data.job_runs,
        restore_point_counts=coordinator.data.restore_point_counts,
        activity=coordinator.data.activity,
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = hass.states.get(name_entry.entity_id)
    assert state is not None
    assert state.state == "unknown"


async def test_dynamic_storage_detection(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that new storage destinations detected on coordinator update get sensors."""
    registry = er.async_get(hass)

    # Initially 2 storage * 2 sensors = 4 storage sensors
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    storage_entries = [e for e in entries if "storage_" in e.unique_id]
    assert len(storage_entries) == 4

    # Add a third storage destination to coordinator data
    coordinator = mock_setup_entry.runtime_data.coordinator
    new_storage = StorageDestination(id=3, name="NFS Share", type=StorageType.LOCAL)
    original_storage = list(coordinator.data.storage)
    coordinator.data = VaultApiData(
        health=coordinator.data.health,
        settings=coordinator.data.settings,
        encryption=coordinator.data.encryption,
        storage=[*original_storage, new_storage],
        jobs=coordinator.data.jobs,
        job_runs=coordinator.data.job_runs,
        restore_point_counts=coordinator.data.restore_point_counts,
        activity=coordinator.data.activity,
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    storage_entries = [e for e in entries if "storage_" in e.unique_id]
    # 3 storage * 2 sensors = 6
    assert len(storage_entries) == 6
