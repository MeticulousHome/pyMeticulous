# pyMeticulous

A comprehensive Python wrapper for the Meticulous espresso machine API.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

pyMeticulous provides a complete Python interface to the [Meticulous TypeScript API](https://github.com/MeticulousHome/meticulous-typescript-api), enabling programmatic control and monitoring of Meticulous espresso machines.

**Version 0.3.0** adds complete backend API alignment with comprehensive testing, event throttling, robust error handling, and extensive machine management endpoints.

## Features

- **Profile Management**: Create, load, save, and manage espresso profiles
- **Real-time Monitoring**: Socket.IO integration for live brewing data
- **Shot History**: Search, track, rate, and retrieve shot logs (with .zst decompression)
- **Device Control**: Execute actions (start, stop, tare, preheat, calibration)
- **WiFi Management**: Configure network settings and scan available networks
- **Settings Control**: Manage machine settings and preferences
- **Firmware Updates**: Upload and install firmware updates
- **Sound Themes**: Control sound playback and themes
- **Type Safety**: Pydantic models with full validation
- **Comprehensive Error Handling**: All methods return typed responses or errors

## Installation

You can install the `pyMeticulous` package using pip:

```bash
pip install pyMeticulous
```

## Quick Start

```python
from meticulous.api import Api
from meticulous.api_types import ActionType

# Initialize the API client
api = Api(base_url="http://localhost:8080/")

# Get device information
device = api.get_device_info()
print(f"Connected to: {device.name}")

# List available profiles
profiles = api.list_profiles()
for profile in profiles:
    print(f"Profile: {profile.name}")

# Load and start a profile
api.load_profile_by_id(profiles[0].id)
api.execute_action(ActionType.START)
```

## API Reference

For complete API documentation including all endpoints, parameters, and return types, see the [API Specification](https://github.com/MeticulousHome/pyMeticulous/blob/main/API_SPEC.md).

Key capabilities:
- Profile management (list, load, save, delete)
- Real-time brewing data via Socket.IO
- Shot history search, logs (.zst decompression), and statistics
- Machine control (start, stop, tare, preheat, calibration)
- WiFi configuration and network scanning
- Settings management
- Firmware updates
- Device information and diagnostics

## Examples

The `examples/` directory contains several demonstration scripts:

### Basic Profile Management
```python
# examples/load_change_and_execute.py
# Demonstrates loading profiles, modifying them, and executing brewing
```

### Socket.IO Real-time Events
```python
# examples/connect_socketio.py
# Shows how to connect to real-time brewing events
```

### Device Information and Statistics
```python
# examples/device_info_and_stats.py
# Get device details and shot history statistics
```

### History Search and Rating
```python
# examples/history_search_and_rating.py
# Search shot history, filter by date, and rate shots
```

### WiFi Management
```python
# examples/wifi_management.py
# Manage WiFi connections and scan networks
```

## Real-time Events

Subscribe to real-time brewing events using Socket.IO:

```python
from meticulous.api import Api, ApiOptions

def on_status(data):
    print(f"State: {data.state}, Time: {data.profile_time}ms")

def on_temperatures(data):
    print(f"Boiler: {data.t_bar_up}°C")

# Configure event handlers
options = ApiOptions(
    onStatus=on_status,
    onTemperatureSensors=on_temperatures
)

api = Api(base_url="http://localhost:8080/", options=options)
api.connect_to_socket()

# Events will now fire automatically
# ... do work ...

api.disconnect_socket()
```

### Event Throttling

To avoid overloading your handlers with high-frequency events, enable simple throttling via `ApiOptions.throttle`:

```python
from meticulous.api import Api, ApiOptions

def on_status(data):
    # Will be called at most once every 250ms
    print(f"State: {data.state}, Time: {data.profile_time}ms")

# Throttle all events globally to 250ms
api = Api(
    base_url="http://localhost:8080/",
    options=ApiOptions(onStatus=on_status, throttle=0.25)
)

# Or throttle individual events by name
api = Api(
    options=ApiOptions(
        onStatus=on_status,
        throttle={"status": 0.25, "temperature": 0.5}
    )
)
```

### Socket.IO Helpers

Convenience helpers are available for emitting common actions over Socket.IO:

```python
from meticulous.api_types import ActionType

api.send_action_socketio(ActionType.START)
api.acknowledge_notification_socketio("notif-id", "acknowledged")
api.send_profile_hover({"id": "profile-id", "name": "My Profile"})
api.trigger_calibration(True)
```

## Error Handling

All API methods return either the expected type or an `APIError` object:

```python
from meticulous.api_types import APIError

result = api.get_profile("some-id")

if isinstance(result, APIError):
    print(f"Error: {result.error}")
    if result.description:
        print(f"Details: {result.description}")
else:
    # Success - result is a Profile object
    print(f"Profile loaded: {result.name}")
```

### Union Returns

Some methods can return more than one success shape depending on firmware version or endpoint:
- **WiFi config**: `get_wifi_config()` → `WiFiConfigResponse` (wrapped with status) or `WiFiConfig` (bare config)
- **Default profiles**: `get_default_profiles()` → `DefaultProfiles` (grouped) or `List[Profile]`
- **Current/last shot**: `get_current_shot()` / `get_last_shot()` → `HistoryEntry` or `None`

Always guard with `isinstance(...)` checks in your code and tests.

## Type Safety

pyMeticulous uses Pydantic v2 for complete data validation and type safety. All API methods accept and return fully typed models. See the [Type Reference](./API_SPEC.md#type-reference) section in the API specification for complete model documentation.

## Development

### Running Tests

pyMeticulous includes both **unit tests** (fast, using mocks) and **integration tests** (require real hardware).

```bash
# Install test dependencies
pip install -e ".[test]"

# Run only unit tests (fast, no hardware needed)
pytest -m "not integration"

# Run only integration tests (requires real machine)
export METICULOUS_HOST=192.168.1.100:8080  # Set your machine address
pytest -m integration

# Run all tests
pytest

# Run with coverage (unit tests only)
pytest --cov=meticulous -m "not integration"
```

### Test Organization

- **Unit Tests** (`tests/test_*.py`) - Fast tests using mocks, run on every change
  - `test_models.py` - Type model validation
  - `test_rest_api.py` - REST endpoint tests
  - `test_socketio.py` - Socket.IO functionality
  
- **Integration Tests** (`tests/integration/`) - Validate against real hardware
  - `test_api_endpoints.py` - REST API validation
  - `test_safe_posts.py` - Safe POST operations
  - `test_socketio.py` - Real-time event streaming
  
See [tests/integration/README.md](tests/integration/README.md) for integration test details.

### Project Structure

```
pyMeticulous/
├── meticulous/
│   ├── __init__.py
│   ├── api.py              # Main API client
│   ├── api_types.py        # Type definitions
│   └── profile.py          # Profile model
├── tests/
│   ├── test_models.py      # Model/type tests
│   ├── test_rest_api.py    # REST API tests
│   ├── test_socketio.py    # Socket.IO tests
│   ├── integration/        # Integration tests (require real machine)
│   └── mock_responses.py   # Test fixtures
├── examples/               # Example scripts
├── API_SPEC.md            # Complete API documentation
├── README.md
└── pyproject.toml
```

## Requirements

- Python >= 3.11
- requests >= 2.32.3
- pydantic >= 2.7.3
- python-socketio >= 5.11.2
- websocket-client >= 1.8.0
- zstandard >= 0.22.0 (for shot log decompression)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [Meticulous TypeScript API](https://github.com/MeticulousHome/meticulous-typescript-api) - The official TypeScript API this wrapper is based on
- [Meticulous Home](https://meticuloushome.com) - Official Meticulous website

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/MeticulousHome/pyMeticulous/issues
- API Documentation: [API_SPEC.md](./API_SPEC.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release notes.

## Acknowledgments

This project is a Python wrapper for the Meticulous espresso machine API. Thanks to the Meticulous team for creating an open and well-documented API.
