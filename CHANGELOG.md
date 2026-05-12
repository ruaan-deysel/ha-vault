# Changelog

All notable changes to this project will be documented in this file.

The changelog uses date sections in `YYYY.MM.DD` format.

## [Unreleased]

### Added

- Automated GitHub release workflow that creates a tag and release from `custom_components/vault/manifest.json` version.
- Automatic extraction of the latest changelog section for release notes.

### Changed

- Updated Vault API compatibility for new auth/header behavior and activity payload normalization.
- Improved entity naming clarity to reduce user confusion.
- Added value-add job sensors:
  - Last duration
  - Last failure reason

### Fixed

- Activity level parsing for `warn` values.
- Compatibility handling for evolving API fields and status values.
