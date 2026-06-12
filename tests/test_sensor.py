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
from custom_components.vault.sensor import _job_last_failure_reason, _job_last_size, _job_restore_points
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

    # Global: vault_status, vault_version, vault_mode, jobs_total, jobs_enabled,
    # encryption_status, runner_queue_length, runner_current_job_id (8)
    # Per-job: 3 jobs x 8 sensors = 24
    # Per-job progress: 3 jobs x 1 = 3
    # Per-storage: 2 storage x 6 sensors = 12
    # Total: 47
    assert len(sensor_entries) == 47


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
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_job_1_status"),
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
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_job_1_status"),
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
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_job_1_progress"),
        None,
    )
    assert progress_entry is not None

    # Initially no progress in store — idle jobs report 0
    state = hass.states.get(progress_entry.entity_id)
    assert state is not None
    assert state.state == "0"

    # Set progress in the runtime data store
    mock_setup_entry.runtime_data.progress[1] = 42
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
    # 2 storage destinations x 6 sensors each = 12
    assert len(storage_entries) == 12


async def test_storage_sensor_name_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage name sensor has correct value."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    name_entry = next(
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_storage_1_name"),
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
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_storage_2_type"),
        None,
    )
    assert type_entry is not None
    state = hass.states.get(type_entry.entity_id)
    assert state is not None
    assert state.state == "s3"


async def test_storage_sensor_removed_when_storage_removed(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage sensor entities are removed when the storage destination disappears."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)

    name_entry = next(
        (e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_storage_1_name"),
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

    # Stale entity cleanup removes the registry entry and its state
    assert registry.async_get(name_entry.entity_id) is None
    assert hass.states.get(name_entry.entity_id) is None


async def test_dynamic_storage_detection(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that new storage destinations detected on coordinator update get sensors."""
    registry = er.async_get(hass)

    # Initially 2 storage * 6 sensors = 12 storage sensors
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    storage_entries = [e for e in entries if "storage_" in e.unique_id]
    assert len(storage_entries) == 12

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
    # 3 storage * 6 sensors = 18
    assert len(storage_entries) == 18


async def test_job_last_failure_reason_from_dict(mock_vault_data: VaultApiData) -> None:
    """Test failure reason extraction from dict-shaped JSON logs."""
    failed_run = JobRun(id=500, job_id=9, status=JobRunStatus.FAILED, log='{"error":"disk full"}')
    data = mock_vault_data.model_copy(update={"job_runs": {9: [failed_run]}})

    assert _job_last_failure_reason(data, 9) == "disk full"


async def test_job_last_failure_reason_from_list_items(mock_vault_data: VaultApiData) -> None:
    """Test failure reason extraction from list-shaped JSON logs."""
    failed_log = (
        '[{"status":"completed","name":"ok"},{"status":"failed","name":"db"},{"status":"error","item_name":"cache"}]'
    )
    failed_run = JobRun(id=501, job_id=10, status=JobRunStatus.FAILED, log=failed_log)
    data = mock_vault_data.model_copy(update={"job_runs": {10: [failed_run]}})

    assert _job_last_failure_reason(data, 10) == "Failed items: db, cache"


async def test_job_last_failure_reason_invalid_json(mock_vault_data: VaultApiData) -> None:
    """Test fallback to raw truncated log when JSON decoding fails."""
    long_log = "x" * 300
    failed_run = JobRun(id=502, job_id=11, status=JobRunStatus.FAILED, log=long_log)
    data = mock_vault_data.model_copy(update={"job_runs": {11: [failed_run]}})

    assert _job_last_failure_reason(data, 11) == long_log[:255]


async def test_storage_type_string_passthrough(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test storage type sensor stringifies unknown non-enum storage types."""
    coordinator = mock_setup_entry.runtime_data.coordinator
    custom_storage = StorageDestination(id=77, name="Custom", type="rclone")

    coordinator.data = VaultApiData(
        health=coordinator.data.health,
        settings=coordinator.data.settings,
        encryption=coordinator.data.encryption,
        storage=[custom_storage],
        jobs=coordinator.data.jobs,
        job_runs=coordinator.data.job_runs,
        restore_point_counts=coordinator.data.restore_point_counts,
        activity=coordinator.data.activity,
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    type_entry = next((e for e in entries if e.unique_id == f"{mock_setup_entry.entry_id}_storage_77_type"), None)
    assert type_entry is not None

    state = hass.states.get(type_entry.entity_id)
    assert state is not None
    assert state.state == "rclone"


async def test_job_last_failure_reason_no_run(mock_vault_data: VaultApiData) -> None:
    """Test no-run branch for last failure reason helper."""
    assert _job_last_failure_reason(mock_vault_data, 9999) == "No failures"


async def test_job_last_failure_reason_completed(mock_vault_data: VaultApiData) -> None:
    """Test completed/running status branch reports no failures."""
    completed_run = JobRun(id=600, job_id=12, status=JobRunStatus.COMPLETED, log="{}")
    data = mock_vault_data.model_copy(update={"job_runs": {12: [completed_run]}})
    assert _job_last_failure_reason(data, 12) == "No failures"


async def test_job_last_failure_reason_fallback_status_text(mock_vault_data: VaultApiData) -> None:
    """Test fallback reason when parsed list has no failed dict items."""
    failed_run = JobRun(id=601, job_id=13, status=JobRunStatus.FAILED, log='[1,{"status":"ok","name":"x"}]')
    data = mock_vault_data.model_copy(update={"job_runs": {13: [failed_run]}})
    assert _job_last_failure_reason(data, 13) == "Last run status: failed"
