# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-01-06

### Added
- Device management: `get_device_info()`
- Display control: `set_brightness()` with interpolation and animation
- Default profiles: `get_default_profiles()` and profile image helpers
- History: `get_history_short_listing()`, `search_history()`, `search_historical_profiles()`
- History stats: `get_history_statistics()`
- Shot rating: `rate_shot()`, `get_shot_rating()`
- OS update: `get_os_status()`
- Time & timezone: `set_time()`, `get_timezone_region()`
- Root access: `get_root_password()`
- Manufacturing features: `get_manufacturing_menu_items()`, `update_manufacturing_settings()`
- WiFi status: `get_wifi_status()` with full system details
- Real-time models expanded (`StatusData`, `SensorData`, `SetpointData`)
- Extended `Settings` model (reverse scrolling, timeouts, timezone, update channel, SSH, etc.)
- New `ActionType`s: `CONTINUE`, `PREHEAT`, `SCALE_MASTER_CALIBRATION`

### Changed
- `get_wifi_config()` remains for compatibility but returns only the `config` portion when full status is provided
- Broadened `WiFiNetwork` with `type` and `security`
- Version bumped to `0.2.0`

### Deprecated
- `get_wifi_config()` is superseded by `get_wifi_status()`; prefer the latter

### Fixed
- Pydantic v2 compatibility (removed `__root__` usage; structured types accordingly)
- Tests expanded and stabilized; 19 tests passing

### Security
- No security-specific changes in this release

[0.2.0]: https://github.com/MeticulousHome/pyMeticulous/releases/tag/v0.2.0