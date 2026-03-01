"""Shared fixtures for Vault integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.models import (
    ActivityEntry,
    AuthStatus,
    BackupJob,
    EncryptionStatus,
    HealthStatus,
    JobRun,
    JobRunStatus,
    RestorePoint,
    Settings,
    StorageDestination,
    StorageTestResult,
    StorageType,
    VaultApiData,
)
from custom_components.vault.const import DOMAIN
from homeassistant.core import HomeAssistant

MOCK_HOST = "192.168.1.100"
MOCK_PORT = 24085


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integration discovery in all tests."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Vault (1.0.0)",
        data={
            "host": MOCK_HOST,
            "port": MOCK_PORT,
        },
        unique_id=f"{MOCK_HOST}:{MOCK_PORT}",
    )


@pytest.fixture
def mock_health() -> HealthStatus:
    """Return a mock HealthStatus."""
    return HealthStatus(status="ok", version="1.0.0")


@pytest.fixture
def mock_settings() -> Settings:
    """Return a mock Settings."""
    return Settings()


@pytest.fixture
def mock_encryption() -> EncryptionStatus:
    """Return a mock EncryptionStatus."""
    return EncryptionStatus(encryption_enabled=True)


@pytest.fixture
def mock_storage() -> list[StorageDestination]:
    """Return mock storage destinations."""
    return [
        StorageDestination(id=1, name="Local Backup", type=StorageType.LOCAL),
        StorageDestination(id=2, name="S3 Bucket", type=StorageType.S3, config="s3://my-bucket"),
    ]


@pytest.fixture
def mock_jobs() -> list[BackupJob]:
    """Return mock backup jobs."""
    return [
        BackupJob(id=1, name="Daily Backup", enabled=True, schedule="0 2 * * *"),
        BackupJob(id=2, name="Weekly Full", enabled=True, schedule="0 3 * * 0"),
        BackupJob(id=3, name="Disabled Job", enabled=False),
    ]


@pytest.fixture
def mock_job_runs() -> dict[int, list[JobRun]]:
    """Return mock job runs keyed by job ID."""
    return {
        1: [
            JobRun(
                id=101,
                job_id=1,
                status=JobRunStatus.COMPLETED,
                items_total=10,
                items_done=10,
                items_failed=0,
                size_bytes=1048576,
            )
        ],
        2: [
            JobRun(
                id=102,
                job_id=2,
                status=JobRunStatus.RUNNING,
                items_total=5,
                items_done=3,
                items_failed=0,
                size_bytes=524288,
            )
        ],
        3: [],
    }


@pytest.fixture
def mock_restore_point_counts() -> dict[int, int]:
    """Return mock restore point counts."""
    return {1: 5, 2: 3, 3: 0}


@pytest.fixture
def mock_activity() -> list[ActivityEntry]:
    """Return mock activity entries."""
    return [
        ActivityEntry(id=1, message="Backup completed", category="backup"),
    ]


@pytest.fixture
def mock_vault_data(
    mock_health: HealthStatus,
    mock_settings: Settings,
    mock_encryption: EncryptionStatus,
    mock_storage: list[StorageDestination],
    mock_jobs: list[BackupJob],
    mock_job_runs: dict[int, list[JobRun]],
    mock_restore_point_counts: dict[int, int],
    mock_activity: list[ActivityEntry],
) -> VaultApiData:
    """Return aggregated mock VaultApiData."""
    return VaultApiData(
        health=mock_health,
        settings=mock_settings,
        encryption=mock_encryption,
        storage=mock_storage,
        jobs=mock_jobs,
        job_runs=mock_job_runs,
        restore_point_counts=mock_restore_point_counts,
        activity=mock_activity,
    )


@pytest.fixture
def mock_api_client(
    mock_health: HealthStatus,
    mock_settings: Settings,
    mock_encryption: EncryptionStatus,
    mock_storage: list[StorageDestination],
    mock_jobs: list[BackupJob],
    mock_activity: list[ActivityEntry],
) -> MagicMock:
    """Create a mocked VaultApiClient."""
    client = MagicMock()
    client.async_get_health = AsyncMock(return_value=mock_health)
    client.async_ping = AsyncMock(return_value=True)
    client.async_get_settings = AsyncMock(return_value=mock_settings)
    client.async_update_settings = AsyncMock(return_value=mock_settings)
    client.async_get_encryption_status = AsyncMock(return_value=mock_encryption)
    client.async_get_storage = AsyncMock(return_value=mock_storage)
    client.async_test_storage = AsyncMock(return_value=StorageTestResult(success=True))
    client.async_get_jobs = AsyncMock(return_value=mock_jobs)
    client.async_get_job = AsyncMock()
    client.async_run_job = AsyncMock(return_value={"status": "started"})
    client.async_get_job_history = AsyncMock(
        side_effect=lambda job_id, **kwargs: [
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
    client.async_get_restore_points = AsyncMock(
        side_effect=lambda job_id: [RestorePoint(id=i, job_run_id=100, job_id=job_id) for i in range(1, 6)]
        if job_id == 1
        else [RestorePoint(id=i, job_run_id=100, job_id=job_id) for i in range(1, 4)]
        if job_id == 2
        else []
    )
    client.async_restore = AsyncMock(return_value={"status": "started"})
    client.async_get_activity = AsyncMock(return_value=mock_activity)
    client.async_get_auth_status = AsyncMock(return_value=AuthStatus(auth_required=False))
    return client


@pytest.fixture
def mock_websocket() -> MagicMock:
    """Create a mocked VaultWebSocketClient."""
    ws = MagicMock()
    ws.async_connect = AsyncMock()
    ws.async_disconnect = AsyncMock()
    ws.connected = True
    ws.register_listener = MagicMock(return_value=MagicMock())
    return ws


@pytest.fixture
async def mock_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: MagicMock,
    mock_websocket: MagicMock,
) -> MockConfigEntry:
    """Set up a Vault config entry with mocked dependencies."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.vault.VaultApiClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.vault.VaultWebSocketClient",
            return_value=mock_websocket,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry
