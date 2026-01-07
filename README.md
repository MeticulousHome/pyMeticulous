# pyMeticulous

A comprehensive Python wrapper for the Meticulous espresso machine API.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

pyMeticulous provides a complete Python interface to the [Meticulous TypeScript API](https://github.com/MeticulousHome/meticulous-typescript-api), enabling programmatic control and monitoring of Meticulous espresso machines.

## Features

- **Profile Management**: Create, load, save, and manage espresso profiles
- **Real-time Monitoring**: Socket.IO integration for live brewing data
- **Shot History**: Search, track, and rate espresso shots
- **Device Control**: Execute actions (start, stop, tare, preheat, calibration)
- **WiFi Management**: Configure network settings and scan available networks
- **Settings Control**: Manage machine settings and preferences
- **Firmware Updates**: Upload and install firmware updates
- **Sound Themes**: Control sound playback and themes
- **Manufacturing Features**: Access manufacturing settings and calibration
- **Comprehensive Error Handling**: All methods return typed responses or errors

## Installation

You can install the `pyMeticulous` package using pip:

```bash
pip install pyMeticulous
```

## Quick Start

```python
from meticulous.api import Api

# Initialize the API client
api = Api(base_url="http://localhost:8080/")

# Get device information
device = api.get_device_info()
print(f"Connected to: {device.name} (Serial: {device.serial})")

# List available profiles
profiles = api.list_profiles()
for profile in profiles:
    print(f"Profile: {profile.name}")

# Load and start a profile
api.load_profile_by_id(profiles[0].id)
api.execute_action("start")
```

## Documentation

For complete API documentation, see the [API Specification](./API_SPEC.md).

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

## Key Features

### Profile Management
- List all profiles (partial or full)
- Load profiles by ID or from JSON
- Save and delete profiles
- Get default and community profiles
- Manage profile images

### Action Control
Execute machine actions:
- `START`, `STOP`, `CONTINUE` - Control brewing
- `TARE` - Zero the scale
- `RESET` - Reset the machine
- `PREHEAT` - Preheat to target temperature
- `CALIBRATION`, `SCALE_MASTER_CALIBRATION` - Calibration modes

### History & Shot Tracking
- Search shot history with filters
- Get statistics by profile
- Rate shots (like/dislike)
- Access detailed shot data with sensor readings

### Device Management
- Get comprehensive device information
- Control display brightness
- Manage timezone settings
- Update firmware
- Access root password for SSH

### WiFi Configuration
- Scan available networks
- Connect to WiFi
- Manage saved networks
- Get connection status and IP information
- Generate WiFi QR codes

### Settings
Configure machine behavior:
- Auto-preheat duration
- Auto-purge after shot
- Auto-start shot
- Sound settings
- Update channel
- SSH access
- And many more...

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

## Type Safety

pyMeticulous uses Pydantic for data validation and type safety:

```python
from meticulous.api_types import BrightnessRequest, WiFiConnectRequest

# All request types are validated
brightness = BrightnessRequest(
    brightness=80,
    interpolation="curve",
    animation_time=500
)
api.set_brightness(brightness)

# Connect to WiFi with type-safe credentials
wifi_creds = WiFiConnectRequest(
    ssid="HomeNetwork",
    password="password123"
)
api.connect_to_wifi(wifi_creds)
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=meticulous tests/
```

### Project Structure

```
pyMeticulous/
├── meticulous/
│   ├── __init__.py
│   ├── api.py              # Main API client
│   ├── api_types.py        # Type definitions
│   └── profile.py          # Profile model
├── tests/
│   ├── test_api.py         # API tests
│   ├── test_profiles.py    # Profile tests
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