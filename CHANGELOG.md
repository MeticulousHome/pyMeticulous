# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-01-15

### Fixed
- `execute_action()` now correctly uses `ActionType.value` for URL construction instead of the enum's string representation, fixing issue where valid actions would incorrectly return error responses.

## [0.3.0] - 2026-01-10

### Added
- API: `import_profiles()`, `get_profile_changes()`, `load_legacy_profile()`
- API: `check_for_updates()`, `perform_os_update()`, `cancel_update()`, `reboot_machine()`, `get_debug_log()`, `list_logs()`, `get_log_file()`
- API: `get_wifi_qr_data()`
- API: `delete_history_entry()`, `export_history()`, `get_timezone()`, `set_timezone()`, `get_timezones()`
- Socket.IO: helper emissions (`send_action_socketio()`, `acknowledge_notification_socketio()`, `send_profile_hover()`, `trigger_calibration()`)
- Socket.IO: connection retries with backoff (`connect_to_socket(retries, backoff, max_backoff)`)
- Actions: `HOME`, `PURGE`, `ABORT` added to `ActionType` enum

### Changed
- Options: support global/per-event throttling via `ApiOptions.throttle`
- WiFi: `get_wifi_config()` can return `WiFiConfigResponse` (wrapped) or `WiFiConfig` (bare)
- Docs: consolidated into README, API_SPEC, and CHANGELOG; removed generated analysis docs

### Fixed
- Socket.IO throttling handler closure binding bug (correct parameter capture)
- Robust REST error handling for non-JSON server responses
- Squiggle cleanup across tests/examples; union handling in tests
- Expanded unit test coverage across REST and Socket.IO paths

## [0.2.0] - 2026-01-08

### Added
- Device info: `get_device_info()`
- Display: `set_brightness()` with interpolation and animation
- Profiles: `get_default_profiles()` and profile image helpers
- History: short listing, search, historical profile search
- History logs: dates, files, log retrieval (with `.zst` decompression), last-shot convenience
- History stats; shot rating (`rate_shot()`, `get_shot_rating()`)
- OS update status: `get_os_status()`
- Time & timezone: `set_time()`, `get_timezone_region()`
- Real-time models (`StatusData`, `SensorData`, `SetpointData`); extended `Settings`
- New actions: `CONTINUE`, `PREHEAT`, `SCALE_MASTER_CALIBRATION`

### Changed
- Added `zstandard` dependency for shot log decompression
- Broadened `WiFiNetwork` with `type` and `security`

### Fixed
- Pydantic v2 compatibility and type checking cleanups
- Tests updated; passing suite

[0.3.0]: https://github.com/MeticulousHome/pyMeticulous/releases/tag/v0.3.0
[0.2.0]: https://github.com/MeticulousHome/pyMeticulous/releases/tag/v0.2.0