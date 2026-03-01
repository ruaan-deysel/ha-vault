"""Tests for Vault API Pydantic models."""

from __future__ import annotations

from custom_components.vault.api.models import (
    ActivityEntry,
    ActivityLevel,
    BackupJob,
    EncryptionStatus,
    HealthStatus,
    JobDetail,
    JobItem,
    JobRun,
    JobRunStatus,
    RestorePoint,
    Settings,
    StorageDestination,
    StorageTestResult,
    StorageType,
    VaultApiData,
    WebSocketEvent,
)


class TestHealthStatus:
    """Tests for HealthStatus model."""

    def test_basic(self) -> None:
        """Test basic HealthStatus creation."""
        h = HealthStatus(status="ok", version="1.0.0")
        assert h.status == "ok"
        assert h.version == "1.0.0"

    def test_defaults(self) -> None:
        """Test HealthStatus defaults."""
        h = HealthStatus(status="ok")
        assert h.version == ""

    def test_from_dict(self) -> None:
        """Test model_validate from dict."""
        h = HealthStatus.model_validate({"status": "running", "version": "2.1.0"})
        assert h.status == "running"
        assert h.version == "2.1.0"


class TestSettings:
    """Tests for Settings model."""

    def test_allows_extra_fields(self) -> None:
        """Test that Settings accepts arbitrary extra fields."""
        s = Settings.model_validate({"theme": "dark", "retention": 30})
        assert s.model_extra is not None
        assert s.model_extra["theme"] == "dark"


class TestEncryptionStatus:
    """Tests for EncryptionStatus model."""

    def test_enabled(self) -> None:
        """Test encryption enabled."""
        e = EncryptionStatus(encryption_enabled=True)
        assert e.encryption_enabled is True

    def test_default_disabled(self) -> None:
        """Test encryption defaults to disabled."""
        e = EncryptionStatus()
        assert e.encryption_enabled is False


class TestStorageDestination:
    """Tests for StorageDestination model."""

    def test_basic(self) -> None:
        """Test basic creation."""
        s = StorageDestination(id=1, name="Local", type=StorageType.LOCAL)
        assert s.id == 1
        assert s.name == "Local"
        assert s.type == StorageType.LOCAL

    def test_timestamps_optional(self) -> None:
        """Test timestamps are optional."""
        s = StorageDestination(id=1, name="Test")
        assert s.created_at is None
        assert s.updated_at is None


class TestStorageTestResult:
    """Tests for StorageTestResult model."""

    def test_success(self) -> None:
        """Test successful result."""
        r = StorageTestResult(success=True)
        assert r.success is True
        assert r.error == ""

    def test_failure(self) -> None:
        """Test failure with error message."""
        r = StorageTestResult(success=False, error="Connection refused")
        assert r.success is False
        assert r.error == "Connection refused"


class TestBackupJob:
    """Tests for BackupJob model."""

    def test_basic(self) -> None:
        """Test basic job creation."""
        j = BackupJob(id=1, name="Daily Backup")
        assert j.id == 1
        assert j.name == "Daily Backup"
        assert j.enabled is True

    def test_all_defaults(self) -> None:
        """Test all default values."""
        j = BackupJob(id=1, name="Test")
        assert j.description == ""
        assert j.schedule == ""
        assert j.retention_count == 5
        assert j.retention_days == 30
        assert j.compression == "none"
        assert j.encryption == "none"
        assert j.verify_backup is True


class TestJobRun:
    """Tests for JobRun model."""

    def test_basic(self) -> None:
        """Test basic run creation."""
        r = JobRun(id=1, job_id=1, status=JobRunStatus.COMPLETED)
        assert r.status == JobRunStatus.COMPLETED
        assert r.size_bytes == 0

    def test_running_status(self) -> None:
        """Test running status."""
        r = JobRun(id=1, job_id=1, status=JobRunStatus.RUNNING)
        assert r.status.value == "running"


class TestJobDetail:
    """Tests for JobDetail model."""

    def test_with_items(self) -> None:
        """Test job detail with items."""
        d = JobDetail(
            job=BackupJob(id=1, name="Test"),
            items=[JobItem(id=1, job_id=1, item_type="container", item_name="myapp")],
        )
        assert len(d.items) == 1
        assert d.items[0].item_name == "myapp"


class TestRestorePoint:
    """Tests for RestorePoint model."""

    def test_basic(self) -> None:
        """Test basic creation."""
        rp = RestorePoint(id=1, job_run_id=10, job_id=1)
        assert rp.id == 1
        assert rp.size_bytes == 0


class TestActivityEntry:
    """Tests for ActivityEntry model."""

    def test_basic(self) -> None:
        """Test basic creation."""
        a = ActivityEntry(id=1, message="Job completed")
        assert a.level == ActivityLevel.INFO
        assert a.message == "Job completed"


class TestVaultApiData:
    """Tests for aggregated VaultApiData model."""

    def test_defaults(self) -> None:
        """Test all defaults."""
        d = VaultApiData()
        assert d.jobs == []
        assert d.job_runs == {}
        assert d.restore_point_counts == {}

    def test_with_data(self, mock_vault_data: VaultApiData) -> None:
        """Test with full mock data."""
        assert mock_vault_data.health.status == "ok"
        assert len(mock_vault_data.jobs) == 3
        assert mock_vault_data.encryption.encryption_enabled is True


class TestWebSocketEvent:
    """Tests for WebSocketEvent model."""

    def test_minimal(self) -> None:
        """Test minimal event."""
        e = WebSocketEvent(type="job_run_started")
        assert e.type == "job_run_started"
        assert e.job_id is None

    def test_full_event(self) -> None:
        """Test event with all fields."""
        e = WebSocketEvent(
            type="backup_progress",
            job_id=1,
            run_id=10,
            status="running",
            percent=50,
            items_done=5,
            items_failed=0,
            size_bytes=1024,
        )
        assert e.percent == 50
        assert e.items_done == 5

    def test_model_dump_excludes_none(self) -> None:
        """Test model_dump with exclude_none removes optional fields."""
        e = WebSocketEvent(type="test", job_id=1)
        dumped = e.model_dump(exclude_none=True)
        assert "run_id" not in dumped
        assert dumped["job_id"] == 1
