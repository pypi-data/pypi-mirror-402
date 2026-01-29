# Changelog

## Unreleased

### Added
- Multi-car synchronized extraction using a main vehicle reference time.
- Optional GPS export alongside point clouds with sync metadata.
- Optional camera extraction with multi-topic support (per-camera output folders).
- Prefer non-_slave camera topics with automatic fallback to _slave variants.
- Config file support (JSON/TOML) for CLI arguments.
- Parallel saving (`save_workers`) and parallel bag indexing (`index_threads`).
- VS Code launch configurations for local debugging.
- Batch image undistortion tool with external camera config.

### Changed
- Packaging uses `setuptools_scm` for versioning from git tags.

### Fixed
- Clearer summary output with matched/saved/failed counts and failure reasons.
