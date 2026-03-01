"""Pydantic v2 models for Vault API responses."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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
    S3 = "s3"
    SFTP = "sftp"


class ActivityLevel(StrEnum):
    """Level of an activity log entry."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# --- Auth ---


class AuthStatus(BaseModel):
    """Response from GET /api/v1/auth/status."""

    auth_required: bool = False


# --- Health ---


class HealthStatus(BaseModel):
    """Response from GET /api/v1/health."""

    status: str
    version: str = ""


# --- Settings ---


class Settings(BaseModel):
    """Response from GET /api/v1/settings."""

    model_config = {"extra": "allow"}


class EncryptionStatus(BaseModel):
    """Response from GET /api/v1/settings/encryption."""

    encryption_enabled: bool = False


# --- Storage ---


class StorageDestination(BaseModel):
    """A single storage destination from GET /api/v1/storage."""

    id: int
    name: str
    type: StorageType = StorageType.LOCAL
    config: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StorageTestResult(BaseModel):
    """Response from POST /api/v1/storage/{id}/test."""

    success: bool
    error: str = ""


# --- Jobs ---


class BackupJob(BaseModel):
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
    pre_script: str = ""
    post_script: str = ""
    notify_on: str = "failure"
    verify_backup: bool = True
    storage_dest_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobItem(BaseModel):
    """An item within a job from GET /api/v1/jobs/{id}."""

    id: int
    job_id: int
    item_type: str = ""
    item_name: str = ""
    item_id: str = ""
    settings: str = ""
    sort_order: int = 0


class JobDetail(BaseModel):
    """Response from GET /api/v1/jobs/{id}."""

    job: BackupJob
    items: list[JobItem] = Field(default_factory=list)


class JobRun(BaseModel):
    """A single job run from GET /api/v1/jobs/{id}/history."""

    id: int
    job_id: int
    status: JobRunStatus = JobRunStatus.COMPLETED
    backup_type: str = "full"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    log: str = ""
    items_total: int = 0
    items_done: int = 0
    items_failed: int = 0
    size_bytes: int = Field(default=0, description="Backup size in bytes")


class RestorePoint(BaseModel):
    """A single restore point from GET /api/v1/jobs/{id}/restore-points."""

    id: int
    job_run_id: int = 0
    job_id: int = 0
    backup_type: str = "full"
    storage_path: str = ""
    metadata: str = ""
    size_bytes: int = Field(default=0, description="Backup size in bytes")
    created_at: datetime | None = None


# --- Activity ---


class ActivityEntry(BaseModel):
    """A single activity log entry from GET /api/v1/activity."""

    id: int
    level: ActivityLevel = ActivityLevel.INFO
    category: str = ""
    message: str = ""
    details: str = ""
    created_at: datetime | None = None


# --- Aggregated coordinator data ---


class VaultApiData(BaseModel):
    """Aggregated data returned by the coordinator after polling all endpoints."""

    health: HealthStatus = Field(default_factory=HealthStatus.model_construct)
    settings: Settings = Field(default_factory=Settings.model_construct)
    encryption: EncryptionStatus = Field(default_factory=EncryptionStatus.model_construct)
    storage: list[StorageDestination] = Field(default_factory=list)
    jobs: list[BackupJob] = Field(default_factory=list)
    job_runs: dict[int, list[JobRun]] = Field(default_factory=dict)
    restore_point_counts: dict[int, int] = Field(default_factory=dict)
    activity: list[ActivityEntry] = Field(default_factory=list)


# --- WebSocket events ---


class WebSocketEvent(BaseModel):
    """A WebSocket event from WS /api/v1/ws."""

    type: str
    job_id: int | None = None
    run_id: int | None = None
    item_name: str | None = None
    item_type: str | None = None
    status: str | None = None
    percent: int | None = None
    message: str | None = None
    size_bytes: int | None = None
    items_done: int | None = None
    items_failed: int | None = None
    verified: bool | None = None
    error: str | None = None
