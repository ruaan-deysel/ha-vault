"""Tests for the Vault data update coordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.vault.api.exceptions import VaultApiError, VaultAuthenticationError, VaultConnectionError
from custom_components.vault.api.models import JobRun, JobRunStatus, VaultApiData
from custom_components.vault.const import ACTIVE_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS
from custom_components.vault.coordinator import VaultDataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed


@pytest.fixture
def coordinator(
    hass: HomeAssistant,
    mock_api_client: MagicMock,
    mock_config_entry: MagicMock,
) -> VaultDataUpdateCoordinator:
    """Create a coordinator with a mock client."""
    mock_config_entry.add_to_hass(hass)
    coord = VaultDataUpdateCoordinator(hass, mock_api_client)
    coord.config_entry = mock_config_entry
    return coord


async def test_first_refresh(
    coordinator: VaultDataUpdateCoordinator,
) -> None:
    """Test that first refresh populates data."""
    await coordinator.async_refresh()
    assert coordinator.data is not None
    assert coordinator.data.health.status == "ok"


async def test_data_contains_all_fields(
    coordinator: VaultDataUpdateCoordinator,
) -> None:
    """Test that coordinator data contains all expected fields."""
    await coordinator.async_refresh()
    data = coordinator.data
    assert isinstance(data, VaultApiData)
    assert data.health.version == "1.0.0"
    assert len(data.jobs) == 3
    assert isinstance(data.storage, list)
    assert isinstance(data.activity, list)


async def test_job_runs_populated(
    coordinator: VaultDataUpdateCoordinator,
) -> None:
    """Test that job runs are fetched for each job."""
    await coordinator.async_refresh()
    data = coordinator.data
    # Jobs 1 and 2 have runs, job 3 is empty
    assert len(data.job_runs[1]) == 1
    assert len(data.job_runs[2]) == 1
    assert len(data.job_runs[3]) == 0


async def test_restore_point_counts(
    coordinator: VaultDataUpdateCoordinator,
) -> None:
    """Test that restore point counts are calculated correctly."""
    await coordinator.async_refresh()
    data = coordinator.data
    assert data.restore_point_counts[1] == 5
    assert data.restore_point_counts[2] == 3
    assert data.restore_point_counts[3] == 0


async def test_connection_error_raises_update_failed(
    coordinator: VaultDataUpdateCoordinator,
    mock_api_client: MagicMock,
) -> None:
    """Test that VaultConnectionError raises UpdateFailed."""
    mock_api_client.async_get_health = AsyncMock(side_effect=VaultConnectionError("timeout"))
    with pytest.raises(UpdateFailed, match="Error communicating"):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_api_error_raises_update_failed(
    coordinator: VaultDataUpdateCoordinator,
    mock_api_client: MagicMock,
) -> None:
    """Test that VaultApiError raises UpdateFailed."""
    mock_api_client.async_get_health = AsyncMock(side_effect=VaultApiError("server error"))
    with pytest.raises(UpdateFailed, match="Vault API error"):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_active_polling_when_running(
    coordinator: VaultDataUpdateCoordinator,
    mock_api_client: MagicMock,
) -> None:
    """Test polling interval decreases when a job is running."""
    mock_api_client.async_get_job_history = AsyncMock(
        side_effect=lambda job_id, **kwargs: [JobRun(id=100 + job_id, job_id=job_id, status=JobRunStatus.RUNNING)]
    )
    await coordinator.async_refresh()
    assert coordinator.update_interval == timedelta(seconds=ACTIVE_UPDATE_INTERVAL_SECONDS)


async def test_default_polling_when_idle(
    coordinator: VaultDataUpdateCoordinator,
) -> None:
    """Test polling interval is default when no jobs are running."""
    await coordinator.async_refresh()
    # Mock returns COMPLETED for jobs 1 & 2, empty for 3 — none running
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS)


async def test_authentication_error_raises_config_entry_auth_failed(
    coordinator: VaultDataUpdateCoordinator,
    mock_api_client: MagicMock,
) -> None:
    """Test that VaultAuthenticationError raises ConfigEntryAuthFailed."""
    mock_api_client.async_get_health = AsyncMock(side_effect=VaultAuthenticationError("expired"))
    with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_fetch_job_data_api_error_returns_empty_defaults(
    coordinator: VaultDataUpdateCoordinator,
    mock_api_client: MagicMock,
) -> None:
    """Test per-job fetch returns empty defaults when job-specific API calls fail."""
    mock_api_client.async_get_job_history = AsyncMock(side_effect=VaultApiError("boom"))
    semaphore = asyncio.Semaphore(1)

    job_id, runs, restore_count = await coordinator._fetch_job_data(123, semaphore)  # noqa: SLF001

    assert job_id == 123
    assert runs == []
    assert restore_count == 0
