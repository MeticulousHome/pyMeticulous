# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - TBD

### Added
- Device management: `get_device_info()`
- Display control: `set_brightness()` with interpolation and animation
- Default profiles: `get_default_profiles()` and profile image helpers
- History: `get_history_short_listing()`, `search_history()`, `search_historical_profiles()`
- History logs: `get_history_dates()`, `get_shot_files()`, `get_shot_log()`, `get_last_shot_log()` (with `.zst` decompression)
- History stats: `get_history_statistics()`
- Shot rating: `rate_shot()`, `get_shot_rating()`
- OS update: `get_os_status()`
- Time & timezone: `set_time()`, `get_timezone_region()`
- Variable profiles: string values supported in variables, dynamics, limits, and triggers
- Real-time models expanded (`StatusData`, `SensorData`, `SetpointData`)
- Extended `Settings` model (reverse scrolling, timeouts, timezone, update channel, SSH, etc.)
- New `ActionType`s: `CONTINUE`, `PREHEAT`, `SCALE_MASTER_CALIBRATION`

### Changed
- `get_wifi_config()` returns basic WiFi configuration
- Broadened `WiFiNetwork` with `type` and `security`
- Added `zstandard` dependency for shot log decompression
- Version bumped to `0.2.0`

### Fixed
- Pydantic v2 compatibility (removed `__root__` usage; structured types accordingly)
- Type checking warnings for Pydantic dynamic model creation
- `__init__` return type corrected from `Self` to `None`
- Tests updated; 17 tests passing

### Security
- No security-specific changes in this release

[0.2.0]: https://github.com/MeticulousHome/pyMeticulous/releases/tag/v0.2.0