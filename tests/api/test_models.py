"""Tests for Vault API Pydantic models."""

# ruff: noqa: SLF001

from __future__ import annotations

from typing import Any, cast

from pydantic import ValidationError
import pytest

from custom_components.vault.api.models import (
    ActivityEntry,
    ActivityLevel,
    Anomaly,
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
        assert h.mode == ""

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

    def test_unknown_storage_type_is_tolerated(self) -> None:
        """Test unknown storage type values do not fail validation."""
        s = StorageDestination.model_validate({"id": 1, "name": "Custom", "type": "rclone"})
        assert s.type == "rclone"

    def test_storage_type_enum_value_passes_through(self) -> None:
        """Test enum storage type values are preserved by validator pass-through."""
        s = StorageDestination(id=1, name="NFS", type=StorageType.NFS)
        assert s.type == StorageType.NFS

    def test_storage_type_validator_non_string_passthrough(self) -> None:
        """Test storage type validator returns non-string values as-is."""
        assert StorageDestination._normalize_storage_type(cast(Any, 123)) == 123


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
        assert j.source_id == 0
        assert j.defer_remote_upload is False


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
        assert str(getattr(r.status, "value", r.status)) == "running"

    def test_unknown_status_is_tolerated(self) -> None:
        """Test unknown status values do not fail validation."""
        r = JobRun.model_validate({"id": 1, "job_id": 1, "status": "queued"})
        assert r.status == "queued"

    def test_status_enum_value_passes_through(self) -> None:
        """Test enum status values are preserved by validator pass-through."""
        r = JobRun(id=1, job_id=1, status=JobRunStatus.PARTIAL)
        assert r.status == JobRunStatus.PARTIAL

    def test_status_validator_non_string_passthrough(self) -> None:
        """Test status validator returns non-string values as-is."""
        assert JobRun._normalize_status(cast(Any, 999)) == 999


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

    def test_warn_level_alias_normalized(self) -> None:
        """Test API 'warn' level alias normalizes to warning enum."""
        a = ActivityEntry.model_validate({"id": 1, "level": "warn", "message": "Test"})
        assert a.level == ActivityLevel.WARNING

    def test_level_enum_value_passes_through(self) -> None:
        """Test enum activity levels are preserved by validator pass-through."""
        a = ActivityEntry(id=1, level=ActivityLevel.ERROR, message="Bad")
        assert a.level == ActivityLevel.ERROR


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


class TestNullTolerance:
    """Explicit nulls from the API must fall back to field defaults.

    Vault sends ``null`` for fields that have no value yet — e.g.
    ``duration_seconds`` and ``completed_at`` while a run is in progress.
    A poll during a running job previously crashed the whole coordinator
    update, taking every entity unavailable (issue #27 stress test).
    """

    def test_job_run_with_nulls_while_running(self) -> None:
        """A running job's history entry validates with nulled fields."""
        run = JobRun.model_validate(
            {
                "id": 170,
                "job_id": 73,
                "status": "running",
                "completed_at": None,
                "log": None,
                "items_total": None,
                "items_done": None,
                "items_failed": None,
                "size_bytes": None,
                "duration_seconds": None,
            }
        )
        assert run.status == JobRunStatus.RUNNING
        assert run.duration_seconds == 0
        assert run.items_total == 0
        assert run.size_bytes == 0
        assert run.completed_at is None
        assert run.log == ""

    def test_backup_job_with_nulls(self) -> None:
        """Nulled optional job fields fall back to defaults."""
        job = BackupJob.model_validate(
            {"id": 1, "name": "Job", "schedule": None, "retention_count": None, "enabled": None}
        )
        assert job.schedule == ""
        assert job.retention_count == 5
        assert job.enabled is True

    def test_required_fields_still_required(self) -> None:
        """Nulls on required fields still fail validation."""
        with pytest.raises(ValidationError):
            JobRun.model_validate({"id": None, "job_id": 1})


class TestAnomaly:
    """Tests for the Anomaly model."""

    def test_basic(self) -> None:
        """An anomaly record from the REST API validates."""
        anomaly = Anomaly.model_validate(
            {
                "id": 13,
                "detector": "reliability",
                "severity": "critical",
                "scope_kind": "job",
                "scope_id": 32,
                "metric": "failure_streak",
                "summary": "job has failed 5 runs in a row",
                "state": "open",
            }
        )
        assert anomaly.id == 13
        assert anomaly.scope_id == 32
        assert anomaly.severity == "critical"


class TestWebSocketEventPayloads:
    """WS payload fields used by alert events must survive parsing."""

    def test_stale_items_payload(self) -> None:
        """stale_items_detected events keep count and items."""
        e = WebSocketEvent.model_validate(
            {
                "type": "stale_items_detected",
                "job_id": 75,
                "count": 1,
                "items": [{"item_id": 104, "item_name": "jackett", "item_type": "container"}],
            }
        )
        assert e.count == 1
        assert e.items is not None
        assert e.items[0]["item_name"] == "jackett"

    def test_anomaly_payload(self) -> None:
        """anomaly.* events keep the structured data payload."""
        e = WebSocketEvent.model_validate(
            {
                "type": "anomaly.updated",
                "data": {"ID": 11, "Severity": "critical", "Summary": "backup shrank to 0 B"},
            }
        )
        assert e.data is not None
        assert e.data["Severity"] == "critical"

    def test_activity_payload(self) -> None:
        """activity events keep the embedded entry."""
        e = WebSocketEvent.model_validate(
            {
                "type": "activity",
                "entry": {"id": 810, "level": "info", "message": "Backup started"},
            }
        )
        assert e.entry is not None
        assert e.entry["message"] == "Backup started"
