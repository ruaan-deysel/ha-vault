# Changelog

All notable changes to this project will be documented in this file.

The changelog uses date sections in `YYYY.MM.DD` format.

## [Unreleased]

## [2024.06.00] - Initial release

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
