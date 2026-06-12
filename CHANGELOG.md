# Changelog

All notable changes to this project will be documented in this file.

The changelog uses date sections in `YYYY.MM.DD` format.

## [Unreleased]

## [2026.06.01] - 2026-06-13

### Added

- **Event platform**: New per-job event entities (`event.<job>_last_event`) exposing the backup lifecycle (`backup_started`, `backup_completed`, `backup_failed`) driven by WebSocket push events
- **Storage health and capacity sensors**: Per-destination health status, free/used/total space sensors (used/total disabled by default), populated from data already polled by the coordinator
- **Repair issues**: A repair issue is raised when a storage destination reports an unhealthy health check or an open circuit breaker, and cleared automatically when it recovers
- **Stale entity cleanup**: Entities belonging to jobs or storage destinations that are deleted or renamed (while running or while Home Assistant was offline) are now removed from the entity registry automatically
- **Live progress updates**: Per-job progress sensors now update instantly from WebSocket progress events instead of waiting for the next poll
- WebSocket events fired on the Home Assistant bus now include the `entry_id`, so automations can distinguish multiple Vault instances

### Fixed

- **API client timeout now covers response body reads** — a stalled response could previously hang the coordinator indefinitely
- **Authentication failures during per-job data fetches now trigger the reauth flow** instead of being silently logged as warnings
- **Backup progress tracking moved from `hass.data` to config entry runtime data**, fixing job-ID collisions when multiple Vault instances are configured (Quality Scale `runtime-data` rule)
- **WebSocket listener is now registered before connecting**, so events arriving immediately after connect are no longer dropped
- **Service calls now validate that the target config entry is loaded** and raise translated `ServiceValidationError`s instead of failing with an internal error
- **Reconfigure flow updates the config entry unique ID** when host/port changes and aborts on collision with another entry
- **Device "Visit" link now opens the Unraid web UI** (`http://<host>`) instead of the non-browsable Vault API port
- **Diagnostics now redact the full payload** including settings keys that may contain secrets (webhook URLs, passphrases, tokens)
- Jobs/storage list API responses with unexpected shapes now raise an error instead of being treated as empty (protects entity cleanup from wiping entities on malformed payloads)
- Added `CONFIG_SCHEMA = config_entry_only_config_schema` for hassfest compliance

### Changed

- **Human-friendly entity values across the board:**
  - Job durations show as adaptive text (`51s`, `3m 29s`, `1h 12m`) instead of raw seconds; the raw value remains available in the `duration_seconds` attribute
  - Data sizes auto-scale their display unit (MB/GB/TB) to the value instead of always showing bytes or GB
  - "Runner current job ID" became "Runner active job" and shows the running job's name (or `idle`) instead of a numeric ID
  - Progress sensors report `0 %` when no backup is running instead of `unknown`
  - "Last failure reason" reports `No failures` after a successful run instead of `unknown`
  - Capacity sensors report `unknown` (instead of a misleading `0 GB`) for remote destinations that don't support capacity probing (S3, WebDAV)
- **BREAKING: Entity unique IDs are now derived from immutable job/storage IDs** (`job_<id>_<key>`, `storage_<id>_<key>`) instead of name slugs. Jobs with names that slugify identically no longer collide, and renaming a job no longer orphans its entities — entity names now follow renames automatically. Entities registered by previous versions are removed and re-created on first start (friendly entity IDs are unchanged since they derive from names)
- Sensor, binary sensor, and event platforms set `PARALLEL_UPDATES = 0` (recommended for read-only coordinator platforms); progress sensors use the shared `PERCENTAGE` constant

## [2026.06.00] - Initial release

### Added

- **Core Integration**: Full Vault backup plugin integration for Home Assistant with secure API client
- **Configuration Flow**: Setup wizard with connection validation and multiple config entry support
- **Coordinator Pattern**: DataUpdateCoordinator for efficient data fetching with configurable intervals
- **WebSocket Real-time Events**: Direct event streaming from Vault with 20+ event types mapped to Home Assistant event bus
- **Entities**:
  - Sensors: Current job status, queue length, storage metrics, runner status
  - Binary Sensors: Connection status, runner active status
  - Buttons: Quick-trigger backup jobs
- **Service Actions**:
  - `vault.run_backup` - Trigger immediate backup of any Vault job
  - `vault.restore` - Restore items from backup restore points
  - `vault.test_storage` - Test connectivity to storage destinations
- **Diagnostics**: Sensitive data redaction for troubleshooting
- **Repairs**: Issue detection and guided repair flows
- **Automation Support**: Comprehensive automation examples for:
  - Backup before Home Assistant updates
  - Daily automatic backups
  - Critical addon backup triggers
  - Storage maintenance workflows
- **Documentation**:
  - Getting Started guide
  - Configuration reference
  - Automation ideas and examples with best practices

### Fixed

- Runner status null safety in sensor queries
- DevContainer configuration JSON structure

### Dependencies

- aiohttp for async HTTP client
- Pydantic v2 for data validation
- Home Assistant 2025.7.0+
