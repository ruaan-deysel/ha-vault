"""Pydantic v2 models for Vault API responses."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from pydantic_core import PydanticUndefined


class VaultModel(BaseModel):
    """Base model that treats explicit nulls as missing values.

    The Vault API sends explicit ``null`` for fields that have no value yet
    (e.g. ``duration_seconds`` while a run is still in progress). Pydantic
    only applies defaults for *missing* keys, so nulls would otherwise fail
    validation and take down the whole coordinator update.
    """

    @field_validator("*", mode="before")
    @classmethod
    def _null_uses_default(cls, value: object, info: ValidationInfo) -> object:
        if value is None and info.field_name is not None:
            field = cls.model_fields[info.field_name]
            if field.default is not PydanticUndefined or field.default_factory is not None:
                return field.get_default(call_default_factory=True)
        return value


class JobRunStatus(StrEnum):
    """Status of a job run (from history)."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class StorageType(StrEnum):
    """Type of storage destination."""

    LOCAL = "local"
    SMB = "smb"
    NFS = "nfs"
    S3 = "s3"
    SFTP = "sftp"
    WEBDAV = "webdav"


class ActivityLevel(StrEnum):
    """Level of an activity log entry."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# --- Auth ---


class AuthStatus(VaultModel):
    """Response from GET /api/v1/auth/status."""

    auth_required: bool = False


# --- Health ---


class HealthStatus(VaultModel):
    """Response from GET /api/v1/health."""

    status: str
    version: str = ""
    mode: str = ""


# --- Settings ---


class Settings(VaultModel):
    """Response from GET /api/v1/settings."""

    model_config = {"extra": "allow"}


class EncryptionStatus(VaultModel):
    """Response from GET /api/v1/settings/encryption."""

    encryption_enabled: bool = False


# --- Storage ---


class StorageCapacity(VaultModel):
    """Capacity metrics embedded in a storage destination."""

    free_bytes: int | None = None
    total_bytes: int | None = None
    used_bytes: int | None = None
    error: str = ""
    probed_at: datetime | None = None


class StorageDestination(VaultModel):
    """A single storage destination from GET /api/v1/storage."""

    id: int
    name: str
    type: StorageType | str = StorageType.LOCAL
    config: str = ""
    capacity: StorageCapacity | None = None
    last_health_check_status: str = ""
    last_health_check_error: str = ""
    last_health_check_at: datetime | None = None
    breaker_state: str = ""
    dedup_enabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _normalize_storage_type(cls, value: StorageType | str) -> StorageType | str:
        """Normalize storage type and tolerate unknown future values."""
        if isinstance(value, str):
            normalized = value.lower()
            try:
                return StorageType(normalized)
            except ValueError:
                return normalized
        return value


class StorageTestResult(VaultModel):
    """Response from POST /api/v1/storage/{id}/test."""

    success: bool
    error: str = ""


# --- Jobs ---


class BackupJob(VaultModel):
    """A single backup job from GET /api/v1/jobs."""

    id: int
    name: str
    description: str = ""
    enabled: bool = True
    schedule: str = ""
    backup_type_chain: str = "full"
    retention_count: int = 5
    retention_days: int = 30
    compression: str = "none"
    encryption: str = "none"
    container_mode: str = ""
    vm_mode: str = ""
    pre_script: str = ""
    post_script: str = ""
    notify_on: str = "failure"
    verify_backup: bool = True
    storage_dest_id: int = 0
    source_id: int = 0
    defer_remote_upload: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobItem(VaultModel):
    """An item within a job from GET /api/v1/jobs/{id}."""

    id: int
    job_id: int
    item_type: str = ""
    item_name: str = ""
    item_id: str = ""
    settings: str = ""
    sort_order: int = 0


class JobDetail(VaultModel):
    """Response from GET /api/v1/jobs/{id}."""

    job: BackupJob
    items: list[JobItem] = Field(default_factory=list)


class JobRun(VaultModel):
    """A single job run from GET /api/v1/jobs/{id}/history."""

    id: int
    job_id: int
    status: JobRunStatus | str = JobRunStatus.COMPLETED
    backup_type: str = "full"
    run_type: str = "backup"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    log: str = ""
    items_total: int = 0
    items_done: int = 0
    items_failed: int = 0
    size_bytes: int = Field(default=0, description="Backup size in bytes")
    duration_seconds: int = 0

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value: JobRunStatus | str) -> JobRunStatus | str:
        """Normalize status and tolerate unknown future values."""
        if isinstance(value, str):
            normalized = value.lower()
            try:
                return JobRunStatus(normalized)
            except ValueError:
                return normalized
        return value


class RestorePoint(VaultModel):
    """A single restore point from GET /api/v1/jobs/{id}/restore-points."""

    id: int
    job_run_id: int = 0
    job_id: int = 0
    backup_type: str = "full"
    storage_path: str = ""
    metadata: str = ""
    size_bytes: int = Field(default=0, description="Backup size in bytes")
    parent_restore_point_id: int = 0
    source_id: int = 0
    chain_status: str = ""
    chain_depth: int = 0
    created_at: datetime | None = None


# --- Activity ---


class ActivityEntry(VaultModel):
    """A single activity log entry from GET /api/v1/activity."""

    id: int
    level: ActivityLevel = ActivityLevel.INFO
    category: str = ""
    message: str = ""
    details: str = ""
    created_at: datetime | None = None

    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, value: str | ActivityLevel) -> str | ActivityLevel:
        """Normalize API level aliases used by newer Vault plugin versions."""
        if isinstance(value, str) and value.lower() == "warn":
            return "warning"
        return value


# --- Anomalies ---


class Anomaly(VaultModel):
    """A single anomaly record from GET /api/v1/anomalies."""

    id: int
    fingerprint: str = ""
    detector: str = ""
    severity: str = ""
    scope_kind: str = ""
    scope_id: int = 0
    metric: str = ""
    summary: str = ""
    details: str = ""
    state: str = ""
    job_run_id: int = 0
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


# --- Aggregated coordinator data ---


class VaultApiData(VaultModel):
    """Aggregated data returned by the coordinator after polling all endpoints."""

    health: HealthStatus = Field(default_factory=HealthStatus.model_construct)
    runner_status: dict[str, object] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings.model_construct)
    encryption: EncryptionStatus = Field(default_factory=EncryptionStatus.model_construct)
    storage: list[StorageDestination] = Field(default_factory=list)
    jobs: list[BackupJob] = Field(default_factory=list)
    job_runs: dict[int, list[JobRun]] = Field(default_factory=dict)
    restore_point_counts: dict[int, int] = Field(default_factory=dict)
    activity: list[ActivityEntry] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)


# --- WebSocket events ---


class WebSocketEvent(VaultModel):
    """A WebSocket event from WS /api/v1/ws."""

    type: str
    job_id: int | None = None
    job_name: str | None = None
    run_id: int | None = None
    run_type: str | None = None
    item_name: str | None = None
    item_type: str | None = None
    status: str | None = None
    percent: int | None = None
    done_bytes: int | None = None
    total_bytes: int | None = None
    rate_bytes_per_second: float | None = None
    message: str | None = None
    size_bytes: int | None = None
    items_total: int | None = None
    items_done: int | None = None
    items_failed: int | None = None
    queue: list[dict[str, object]] | None = None
    phase: str | None = None
    passed: bool | None = None
    bytes_freed: int | None = None
    verified: bool | None = None
    error: str | None = None
    count: int | None = None
    """Item count carried by stale_items_detected events."""
    items: list[dict[str, object]] | None = None
    """Item details carried by stale_items_detected events."""
    entry: dict[str, object] | None = None
    """Activity log entry carried by activity events."""
    data: dict[str, object] | None = None
    """Structured payload carried by anomaly.* and baseline.* events."""
