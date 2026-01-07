# pyMeticulous API Specification

This document provides a complete reference for the pyMeticulous API wrapper.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Class](#api-class)
- [Profile Management](#profile-management)
- [Action Control](#action-control)
- [Settings Management](#settings-management)
- [WiFi Configuration](#wifi-configuration)
- [Sound Management](#sound-management)
- [Device Information](#device-information)
- [History & Shot Tracking](#history--shot-tracking)
- [Notification Management](#notification-management)
- [Firmware & Updates](#firmware--updates)
- [Real-time Events (Socket.IO)](#real-time-events-socketio)
- [Type Reference](#type-reference)

## Installation

```bash
pip install pyMeticulous
```

## Quick Start

```python
from meticulous.api import Api

# Initialize the API client
api = Api(base_url="http://localhost:8080/")

# Fetch device information
device_info = api.get_device_info()
print(f"Connected to: {device_info.name}")

# List available profiles
profiles = api.list_profiles()
for profile in profiles:
    print(f"Profile: {profile.name} (ID: {profile.id})")
```

## API Class

### Constructor

```python
Api(base_url: str = "http://localhost:8080/", options: Optional[Dict[str, Callable]] = None)
```

**Parameters:**
- `base_url` (str): The base URL of the Meticulous API server
- `options` (ApiOptions, optional): Event handler configuration for Socket.IO events

**Example:**
```python
from meticulous.api import Api, ApiOptions

def on_status(data):
    print(f"Status: {data.state}")

options = ApiOptions(onStatus=on_status)
api = Api(base_url="http://192.168.1.100:8080/", options=options)
```

### Socket.IO Connection

#### `connect_to_socket() -> None`

Establishes a Socket.IO connection for real-time events.

```python
api.connect_to_socket()
```

#### `disconnect_socket() -> None`

Closes the Socket.IO connection.

```python
api.disconnect_socket()
```

## Profile Management

### `list_profiles() -> Union[List[PartialProfile], APIError]`

Retrieves a list of all saved profiles (partial information).

**Returns:** List of PartialProfile objects or APIError

**Example:**
```python
profiles = api.list_profiles()
if not isinstance(profiles, APIError):
    for profile in profiles:
        print(f"{profile.name}: {profile.id}")
```

### `fetch_all_profiles() -> Union[List[Profile], APIError]`

Retrieves complete information for all profiles.

**Returns:** List of complete Profile objects or APIError

**Example:**
```python
profiles = api.fetch_all_profiles()
if not isinstance(profiles, APIError):
    for profile in profiles:
        print(f"{profile.name} - {len(profile.stages)} stages")
```

### `get_profile(profile_id: str) -> Union[Profile, APIError]`

Retrieves a specific profile by ID.

**Parameters:**
- `profile_id` (str): The unique identifier of the profile

**Returns:** Profile object or APIError

**Example:**
```python
profile = api.get_profile("05051ed3-9996-43e8-9da6-963f2b31d481")
if not isinstance(profile, APIError):
    print(f"Temperature: {profile.temperature}°C")
```

### `save_profile(data: Profile) -> Union[ChangeProfileResponse, APIError]`

Saves a profile to the machine.

**Parameters:**
- `data` (Profile): Complete profile object to save

**Returns:** ChangeProfileResponse with change_id or APIError

**Example:**
```python
from meticulous.profile import Profile

profile = Profile(
    name="My Custom Profile",
    id="new-profile-id",
    author="user",
    author_id="user-id",
    temperature=92.0,
    final_weight=36.0,
    stages=[...]
)

response = api.save_profile(profile)
if not isinstance(response, APIError):
    print(f"Saved with change_id: {response.change_id}")
```

### `load_profile_from_json(data: Profile) -> Union[PartialProfile, APIError]`

Loads a profile into the machine for immediate use without saving.

**Parameters:**
- `data` (Profile): Profile object to load

**Returns:** PartialProfile or APIError

### `load_profile_by_id(id: str) -> Union[PartialProfile, APIError]`

Loads a saved profile by its ID.

**Parameters:**
- `id` (str): Profile identifier

**Returns:** PartialProfile or APIError

**Example:**
```python
result = api.load_profile_by_id("05051ed3-9996-43e8-9da6-963f2b31d481")
if not isinstance(result, APIError):
    print(f"Loaded: {result.name}")
```

### `delete_profile(profile_id: str) -> Union[ChangeProfileResponse, APIError]`

Deletes a profile from the machine.

**Parameters:**
- `profile_id` (str): Profile identifier

**Returns:** ChangeProfileResponse or APIError

### `get_last_profile() -> Union[LastProfile, APIError]`

Gets the most recently loaded profile.

**Returns:** LastProfile with load time and profile data, or APIError

**Example:**
```python
last = api.get_last_profile()
if not isinstance(last, APIError):
    print(f"Last profile: {last.profile.name} at {last.load_time}")
```

### `get_default_profiles() -> Union[List[Profile], DefaultProfiles, APIError]`

Retrieves default and community profiles.

**Returns:** DefaultProfiles object with `default` and `community` lists, or APIError

**Example:**
```python
defaults = api.get_default_profiles()
if isinstance(defaults, DefaultProfiles):
    print(f"Default profiles: {len(defaults.default)}")
    print(f"Community profiles: {len(defaults.community)}")
```

### `get_profile_default_images() -> Union[List[str], APIError]`

Gets a list of available default profile images.

**Returns:** List of image filenames or APIError

### `get_profile_image_url(image: str) -> str`

Constructs the full URL for a profile image.

**Parameters:**
- `image` (str): Image filename or URL

**Returns:** Complete image URL

### `get_profile_image(image: str) -> Union[bytes, APIError]`

Downloads a profile image.

**Parameters:**
- `image` (str): Image filename or URL

**Returns:** Image bytes or APIError

## Action Control

### `execute_action(action: ActionType) -> Union[ActionResponse, APIError]`

Executes a machine action.

**Parameters:**
- `action` (ActionType): One of: `START`, `STOP`, `CONTINUE`, `RESET`, `TARE`, `PREHEAT`, `CALIBRATION`, `SCALE_MASTER_CALIBRATION`

**Returns:** ActionResponse with status and allowed actions, or APIError

**Example:**
```python
from meticulous.api_types import ActionType

# Start brewing
response = api.execute_action(ActionType.START)
if not isinstance(response, APIError):
    print(f"Status: {response.status}")
    print(f"Allowed actions: {response.allowed_actions}")

# Tare the scale
api.execute_action(ActionType.TARE)

# Preheat the machine
api.execute_action(ActionType.PREHEAT)
```

## Settings Management

### `get_settings(setting_name: Optional[str] = None) -> Union[Settings, APIError]`

Retrieves machine settings.

**Parameters:**
- `setting_name` (str, optional): Specific setting name to retrieve

**Returns:** Settings object or APIError

**Example:**
```python
settings = api.get_settings()
if not isinstance(settings, APIError):
    print(f"Auto preheat: {settings.auto_preheat} minutes")
    print(f"Sounds enabled: {settings.enable_sounds}")
```

### `update_setting(setting: PartialSettings) -> Union[Settings, APIError]`

Updates machine settings.

**Parameters:**
- `setting` (PartialSettings): Settings to update (partial object)

**Returns:** Updated Settings object or APIError

**Example:**
```python
from meticulous.api_types import PartialSettings

settings = PartialSettings(
    enable_sounds=True,
    auto_preheat=5
)

result = api.update_setting(settings)
if not isinstance(result, APIError):
    print("Settings updated successfully")
```

## WiFi Configuration

### `get_wifi_config() -> Union[WiFiConfig, APIError]`

Gets WiFi configuration.

**Returns:** WiFiConfig or APIError

### `set_wifi_config(data: PartialWiFiConfig) -> Union[WiFiConfig, APIError]`

Updates WiFi configuration (AP mode settings).

**Parameters:**
- `data` (PartialWiFiConfig): Configuration to update

**Returns:** Updated WiFiConfig or APIError

### `get_wifi_qr_url() -> str`

Gets the URL for the WiFi configuration QR code.

**Returns:** QR code URL string

### `get_wifi_qr() -> Union[bytes, APIError]`

Downloads the WiFi configuration QR code image.

**Returns:** PNG image bytes or APIError

### `list_available_wifi() -> Union[List[WiFiNetwork], APIError]`

Scans and lists available WiFi networks.

**Returns:** List of WiFiNetwork objects or APIError

**Example:**
```python
networks = api.list_available_wifi()
if not isinstance(networks, APIError):
    for net in networks:
        print(f"{net.ssid} - Signal: {net.signal}% - Type: {net.type}")
```

### `connect_to_wifi(data: WiFiConnectRequest) -> Union[None, APIError]`

Connects to a WiFi network.

**Parameters:**
- `data` (WiFiConnectRequest): WiFi credentials

**Returns:** None on success, or APIError

**Example:**
```python
from meticulous.api_types import WiFiConnectRequest

wifi = WiFiConnectRequest(ssid="HomeNetwork", password="password123")
result = api.connect_to_wifi(wifi)
if result is None:
    print("Connected successfully")
```

### `delete_wifi(ssid: str) -> Union[None, APIError]`

Removes a saved WiFi network.

**Parameters:**
- `ssid` (str): Network name to remove

**Returns:** None on success, or APIError

## Sound Management

### `play_sound(sound: str) -> Union[None, APIError]`

Plays a specific sound.

**Parameters:**
- `sound` (str): Sound name

**Returns:** None on success, or APIError

### `list_sounds() -> Union[List[str], APIError]`

Lists all available sounds.

**Returns:** List of sound names or APIError

### `list_sound_themes() -> Union[List[str], APIError]`

Lists available sound themes.

**Returns:** List of theme names or APIError

### `get_sound_theme() -> Union[str, APIError]`

Gets the current sound theme.

**Returns:** Theme name or APIError

### `set_sound_theme(theme: str) -> Union[None, APIError]`

Sets the sound theme.

**Parameters:**
- `theme` (str): Theme name

**Returns:** None on success, or APIError

**Example:**
```python
# List available themes
themes = api.list_sound_themes()
print(f"Available themes: {themes}")

# Set a theme
api.set_sound_theme("meticulous")

# Play a sound
api.play_sound("start_brew")
```

## Device Information

### `get_device_info() -> Union[DeviceInfo, APIError]`

Retrieves comprehensive device information.

**Returns:** DeviceInfo object or APIError

**Example:**
```python
info = api.get_device_info()
if not isinstance(info, APIError):
    print(f"Device: {info.name}")
    print(f"Model: {info.model_version}")
    print(f"Serial: {info.serial}")
    print(f"Firmware: {info.firmware}")
    print(f"Software: {info.software_version}")
    print(f"Voltage: {info.mainVoltage}V")
    print(f"Manufacturing mode: {info.manufacturing}")
```

### `set_brightness(brightness: BrightnessRequest) -> Union[None, APIError]`

Sets the display brightness.

**Parameters:**
- `brightness` (BrightnessRequest): Brightness configuration

**Returns:** None on success, or APIError

**Example:**
```python
from meticulous.api_types import BrightnessRequest

brightness = BrightnessRequest(
    brightness=75,
    interpolation="curve",
    animation_time=500
)
api.set_brightness(brightness)
```

### `set_time(date_time: datetime) -> Union[Regions, APIError]`

Sets the machine's date and time.

**Parameters:**
- `date_time` (datetime): Date/time to set

**Returns:** Regions object or APIError

**Example:**
```python
from datetime import datetime

api.set_time(datetime.now())
```

### `get_timezone_region(region_type: str, conditional: str) -> Union[Regions, APIError]`

Gets timezone region information.

**Parameters:**
- `region_type` (str): Type of region ("countries" or "cities")
- `conditional` (str): Filter string

**Returns:** Regions object or APIError

## History & Shot Tracking

### `get_history_short_listing() -> Union[HistoryListingResponse, APIError]`

Gets a short listing of shot history (without detailed data).

**Returns:** HistoryListingResponse with shot metadata or APIError

**Example:**
```python
history = api.get_history_short_listing()
if not isinstance(history, APIError):
    for shot in history.history:
        print(f"Shot {shot.id}: {shot.name} - {shot.profile.name}")
```

### `search_history(query: HistoryQueryParams) -> Union[HistoryResponse, APIError]`

Searches shot history with detailed data.

**Parameters:**
- `query` (HistoryQueryParams): Search parameters

**Returns:** HistoryResponse with full shot data or APIError

**Example:**
```python
from meticulous.api_types import HistoryQueryParams

query = HistoryQueryParams(
    query="morning",
    max_results=10,
    sort="desc",
    order_by=["date"],
    dump_data=True
)

result = api.search_history(query)
if not isinstance(result, APIError):
    for shot in result.history:
        print(f"{shot.name}: {len(shot.data)} data points")
```

### `search_historical_profiles(query: str) -> Union[HistoryListingResponse, APIError]`

Searches for shots by profile name.

**Parameters:**
- `query` (str): Profile name search query

**Returns:** HistoryListingResponse or APIError

### `get_current_shot() -> Union[HistoryEntry, None, APIError]`

Gets the currently brewing shot (if any).

**Returns:** HistoryEntry, None if no active shot, or APIError

### `get_last_shot() -> Union[HistoryEntry, None, APIError]`

Gets the most recent completed shot.

**Returns:** HistoryEntry, None if no shots exist, or APIError

**Example:**
```python
last_shot = api.get_last_shot()
if last_shot and not isinstance(last_shot, APIError):
    print(f"Last shot: {last_shot.name}")
    print(f"Profile: {last_shot.profile.name}")
    print(f"Data points: {len(last_shot.data)}")
```

### `get_history_statistics() -> Union[HistoryStats, APIError]`

Gets statistics about shot history.

**Returns:** HistoryStats object or APIError

**Example:**
```python
stats = api.get_history_statistics()
if not isinstance(stats, APIError):
    print(f"Total shots: {stats.totalSavedShots}")
    for profile_stat in stats.byProfile:
        print(f"{profile_stat.name}: {profile_stat.count} shots")
```

### `rate_shot(shot_id: int, rating: str) -> Union[RateShotResponse, APIError]`

Rates a shot.

**Parameters:**
- `shot_id` (int): Shot database key
- `rating` (str): Rating ("like", "dislike", or "null")

**Returns:** RateShotResponse or APIError

**Example:**
```python
response = api.rate_shot(1, "like")
if not isinstance(response, APIError):
    print(f"Rated shot {response.shot_id}: {response.rating}")
```

### `get_shot_rating(shot_id: int) -> Union[ShotRatingResponse, APIError]`

Gets the rating for a shot.

**Parameters:**
- `shot_id` (int): Shot database key

**Returns:** ShotRatingResponse or APIError

## Notification Management

### `get_notifications(acknowledged: bool) -> Union[List[Notification], APIError]`

Gets notifications.

**Parameters:**
- `acknowledged` (bool): Filter by acknowledgment status

**Returns:** List of Notification objects or APIError

**Example:**
```python
# Get unacknowledged notifications
notifications = api.get_notifications(acknowledged=False)
if not isinstance(notifications, APIError):
    for notif in notifications:
        print(f"{notif.message} - Options: {notif.response_options}")
```

### `acknowledge_notification(data: AcknowledgeNotificationRequest) -> Union[None, APIError]`

Acknowledges a notification.

**Parameters:**
- `data` (AcknowledgeNotificationRequest): Notification ID and response

**Returns:** None on success, or APIError

**Example:**
```python
from meticulous.api_types import AcknowledgeNotificationRequest

ack = AcknowledgeNotificationRequest(
    id="notification-id",
    response="acknowledged"
)
api.acknowledge_notification(ack)
```

## Firmware & Updates

### `update_firmware(form_data: Dict[str, IO], esp_type: str = "esp32-s3") -> Union[None, APIError]`

Uploads and installs firmware update.

**Parameters:**
- `form_data` (Dict): Form data containing firmware files
- `esp_type` (str): ESP chip type (default: "esp32-s3")

**Returns:** None on success, or APIError

### `get_os_status() -> Union[OSStatusResponse, APIError]`

Gets OS update status.

**Returns:** OSStatusResponse with progress information or APIError

**Example:**
```python
status = api.get_os_status()
if not isinstance(status, APIError):
    if status.progress:
        print(f"Update progress: {status.progress}%")
    print(f"Status: {status.status}")
```

## Real-time Events (Socket.IO)

The API supports real-time event streaming via Socket.IO. Configure event handlers when creating the API instance:

```python
from meticulous.api import Api, ApiOptions

def on_status(data):
    print(f"State: {data.state}, Time: {data.time}ms")

def on_temperatures(data):
    print(f"Boiler: {data.t_bar_up}°C")

def on_notification(data):
    print(f"Notification: {data.message}")

options = ApiOptions(
    onStatus=on_status,
    onTemperatureSensors=on_temperatures,
    onNotification=on_notification
)

api = Api(options=options)
api.connect_to_socket()

# Events will now be received automatically
# ... do work ...

api.disconnect_socket()
```

### Available Event Handlers

- `onStatus`: Receives StatusData during brewing
- `onTemperatureSensors`: Receives Temperatures data
- `onCommunication`: Receives Communication data
- `onActuators`: Receives Actuators data
- `onMachineInfo`: Receives MachineInfo updates
- `onButton`: Receives ButtonEvent data
- `onSettingsChange`: Receives settings changes
- `onNotification`: Receives NotificationData
- `onProfileChange`: Receives ProfileEvent updates

## Type Reference

### Key Data Types

#### Profile
Complete espresso profile with stages, temperature, and metadata.

**Fields:**
- `name` (str): Profile name
- `id` (str): Unique identifier
- `author` (str): Author name
- `author_id` (str): Author identifier
- `temperature` (float): Target temperature in Celsius
- `final_weight` (float): Target shot weight in grams
- `stages` (List[Stage]): Profile stages
- `variables` (List[Variable], optional): Custom variables
- `display` (Display, optional): Display settings
- `previous_authors` (List[PreviousAuthor], optional): Author history

#### StatusData
Real-time machine status during brewing.

**Fields:**
- `name` (str): Status name
- `sensors` (SensorData): Current sensor readings
- `time` (int): Time in milliseconds
- `profile_time` (int, optional): Profile elapsed time
- `profile` (str): Profile ID
- `loaded_profile` (str, optional): Profile name
- `state` (str, optional): Machine state (idle, brewing, etc.)
- `extracting` (bool, optional): Whether actively extracting
- `setpoints` (SetpointData, optional): Current setpoints

#### DeviceInfo
Comprehensive device information.

**Fields:**
- `name`, `hostname`, `firmware`, `serial`, `model_version`
- `mainVoltage` (float): Main voltage
- `software_version`, `image_version`, `image_build_channel`
- `manufacturing` (bool): Manufacturing mode status
- `version_history` (List[str]): Software version history

#### HistoryEntry
Complete shot record with all data points.

**Fields:**
- `id` (str): Shot identifier
- `db_key` (int): Database key
- `time` (int): Unix timestamp
- `name` (str): Shot name
- `profile` (HistoryProfile): Profile used
- `data` (List[HistoryDataPoint]): Time-series data
- `rating` (str, optional): User rating

#### Settings
Machine configuration settings.

**Fields:**
- `auto_preheat` (int): Auto preheat time
- `auto_purge_after_shot` (bool): Auto purge enabled
- `auto_start_shot` (bool): Auto start enabled
- `enable_sounds` (bool): Sounds enabled
- `update_channel` (str): Update channel
- `ssh_enabled` (bool): SSH access enabled
- And many more...

### Enumerations

#### ActionType
- `START`, `STOP`, `CONTINUE`, `RESET`, `TARE`, `PREHEAT`, `CALIBRATION`, `SCALE_MASTER_CALIBRATION`

#### APMode
- `AP` (Access Point mode)
- `CLIENT` (Client mode)

#### ShotRating
- `LIKE`, `DISLIKE`, `NONE`

### Error Handling

All API methods return either the expected type or an `APIError` object. Always check the return type:

```python
result = api.get_profile("some-id")

if isinstance(result, APIError):
    print(f"Error: {result.error}")
    if result.description:
        print(f"Description: {result.description}")
else:
    # result is a Profile object
    print(f"Profile: {result.name}")
```

## Complete Example

```python
from meticulous.api import Api, ApiOptions
from meticulous.api_types import ActionType, BrightnessRequest

# Setup with event handlers
def on_status(data):
    if data.extracting:
        print(f"Brewing: {data.profile_time}ms")

api = Api(
    base_url="http://192.168.1.100:8080/",
    options=ApiOptions(onStatus=on_status)
)

# Connect to events
api.connect_to_socket()

# Get device info
device = api.get_device_info()
print(f"Connected to {device.name} ({device.serial})")

# List profiles
profiles = api.list_profiles()
print(f"Available profiles: {len(profiles)}")

# Load a profile
api.load_profile_by_id(profiles[0].id)

# Tare the scale
api.execute_action(ActionType.TARE)

# Start brewing
api.execute_action(ActionType.START)

# Wait for shot to complete...
# (events will fire via onStatus callback)

# Get history
stats = api.get_history_statistics()
print(f"Total shots: {stats.totalSavedShots}")

# Cleanup
api.disconnect_socket()
```

## Support

For issues, questions, or contributions, visit:
- GitHub: https://github.com/MeticulousHome/pyMeticulous
- TypeScript API: https://github.com/MeticulousHome/meticulous-typescript-api

## License

GPL-3.0
