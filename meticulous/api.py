# pyright: reportGeneralTypeIssues=false
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Any, Callable, Dict, List, Optional, Union, get_args

import json
import requests
import socketio
import zstandard as zstd
from pydantic import TypeAdapter

from .api_types import (
    AcknowledgeNotificationRequest,
    ActionResponse,
    ActionType,
    Actuators,
    APIError,
    BrightnessRequest,
    ButtonEvent,
    ChangeProfileResponse,
    Communication,
    DefaultProfiles,
    DeviceInfo,
    HistoryEntry,
    HistoryListingResponse,
    HistoryQueryParams,
    HistoryResponse,
    HistoryStats,
    HistoryFile,
    LastProfile,
    MachineInfo,
    Notification,
    NotificationData,
    OSStatusResponse,
    PartialProfile,
    PartialSettings,
    PartialWiFiConfig,
    Profile,
    ProfileEvent,
    RateShotResponse,
    Regions,
    Settings,
    ShotRatingResponse,
    StatusData,
    Temperatures,
    WiFiConfig,
    WiFiConnectRequest,
    WiFiNetwork,
)


@dataclass
class ApiOptions:
    onStatus: Optional[Callable[[StatusData], None]] = None
    onTemperatureSensors: Optional[Callable[[Temperatures], None]] = None
    onCommunication: Optional[Callable[[Communication], None]] = None
    onActuators: Optional[Callable[[Actuators], None]] = None
    onMachineInfo: Optional[Callable[[MachineInfo], None]] = None
    onButton: Optional[Callable[[ButtonEvent], None]] = None
    onSettingsChange: Optional[Callable[[Dict], None]] = None
    onNotification: Optional[Callable[[NotificationData], None]] = None
    onProfileChange: Optional[Callable[[ProfileEvent], None]] = None

    # Fetch the events name from the Callbacks parameter and save it
    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__.values():
            handler = getattr(self, field.name)
            if handler:
                # Get the field type from the Options of the Dataclass
                field_args = get_args(field.type)
                if field_args:
                    # Step into the Optional
                    handler_args = get_args(field_args[0])
                    if handler_args:
                        # Get the callbacks parameters
                        parameter_types = handler_args[0]
                        # Check the first parameters type to have a class variable _socketio_event
                        if hasattr(parameter_types[0], "_socketio_event"):
                            event_name = getattr(parameter_types[0], "_socketio_event")
                            setattr(self, f"_{field.name}_event_name", event_name)

    def register_handlers(self, sio: socketio.Client) -> None:
        for field in self.__dataclass_fields__.values():
            handler = getattr(self, field.name)
            if handler:
                event_name = getattr(self, f"_{field.name}_event_name", None)
                if event_name:
                    sio.on(event_name, handler)


class Api:
    def __init__(
        self,
        base_url: str = "http://localhost:8080/",
        options: Optional[Dict[str, Callable[[Any], None]]] = None,
    ) -> None:
        self.base_url = base_url
        self.options = options or ApiOptions()
        self.sio = socketio.Client()
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

        # Register socketio event handlers if options provided
        self.options.register_handlers(self.sio)  # type: ignore[attr-defined]

    def connect_to_socket(self) -> None:
        self.sio.connect(self.base_url)

    def disconnect_socket(self) -> None:
        self.sio.disconnect()

    def execute_action(self, action: ActionType) -> Union[ActionResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/action/{action}")
        if response.status_code == 200:
            return TypeAdapter(ActionResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def list_profiles(self) -> Union[List[PartialProfile], APIError]:  # type: ignore[valid-type]
        response = self.session.get(f"{self.base_url}/api/v1/profile/list")
        if response.status_code == 200:
            return TypeAdapter(List[PartialProfile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def fetch_all_profiles(self) -> Union[List[Profile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/list?full=true")
        if response.status_code == 200:
            return TypeAdapter(List[Profile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def save_profile(self, data: Profile) -> Union[ChangeProfileResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/save",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(ChangeProfileResponse).validate_python(response.json())
        else:
            print(response.json())
            return TypeAdapter(APIError).validate_python(response.json())

    def load_profile_from_json(self, data: Profile) -> Union[PartialProfile, APIError]:  # type: ignore[valid-type]
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/load",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def load_profile_by_id(self, id: str) -> Union[PartialProfile, APIError]:  # type: ignore[valid-type]
        response = self.session.get(f"{self.base_url}/api/v1/profile/load/{id}")
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_profile(self, profile_id: str) -> Union[Profile, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/get/{profile_id}")
        if response.status_code == 200:
            return TypeAdapter(Profile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def delete_profile(self, profile_id: str) -> Union[ChangeProfileResponse, APIError]:
        response = self.session.delete(
            f"{self.base_url}/api/v1/profile/delete/{profile_id}"
        )
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_last_profile(self) -> Union[LastProfile, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/last")
        if response.status_code == 200:
            return TypeAdapter(LastProfile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_notifications(
        self, acknowledged: bool
    ) -> Union[List[Notification], APIError]:
        response = self.session.get(
            f"{self.base_url}/api/v1/notifications?acknowledged={acknowledged}"
        )
        if response.status_code == 200:
            return TypeAdapter(List[Notification]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def acknowledge_notification(
        self, data: AcknowledgeNotificationRequest
    ) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/notifications/acknowledge",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_settings(
        self, setting_name: Optional[str] = None
    ) -> Union[Settings, APIError]:
        url = f"{self.base_url}/api/v1/settings" + (
            f"/{setting_name}" if setting_name else ""
        )
        response = self.session.get(url)
        if response.status_code == 200:
            return TypeAdapter(Settings).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def update_setting(self, setting: PartialSettings) -> Union[Settings, APIError]:  # type: ignore[valid-type]
        response = self.session.post(
            f"{self.base_url}/api/v1/settings",
            json=setting.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(Settings).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def update_firmware(
        self, form_data: Dict[str, IO], esp_type: str = "esp32-s3"
    ) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/update/firmware?chip={esp_type}", files=form_data
        )
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_wifi_config(self) -> Union[WiFiConfig, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/config")
        if response.status_code == 200:
            json_data = response.json()
            # Extract just the config part for backward compatibility
            if "config" in json_data:
                return TypeAdapter(WiFiConfig).validate_python(json_data["config"])
            return TypeAdapter(WiFiConfig).validate_python(json_data)
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def set_wifi_config(self, data: PartialWiFiConfig) -> Union[WiFiConfig, APIError]:  # type: ignore[valid-type]
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/config",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(WiFiConfig).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_wifi_qr_url(self) -> str:
        return f"{self.base_url}/api/v1/wifi/config/qr.png"

    def get_wifi_qr(self) -> Union[bytes, APIError]:
        response = self.session.get(self.get_wifi_qr_url(), stream=True)

        if response.headers.get("Content-Type") == "image/png":
            return response.content
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def list_available_wifi(self) -> Union[List[WiFiNetwork], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/list")
        if response.status_code == 200:
            return TypeAdapter(List[WiFiNetwork]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def connect_to_wifi(self, data: WiFiConnectRequest) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/connect",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def delete_wifi(self, ssid: str) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/delete", json={"ssid": ssid}
        )
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def play_sound(self, sound: str) -> Union[None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/play/{sound}")
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def list_sounds(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/list")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def list_sound_themes(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/theme/list")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_sound_theme(self) -> Union[str, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/theme/get")
        if response.status_code == 200:
            return TypeAdapter(str).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def set_sound_theme(self, theme: str) -> Union[None, APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/sounds/theme/set/{theme}")
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_device_info(self) -> Union[DeviceInfo, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine")
        if response.status_code == 200:
            return TypeAdapter(DeviceInfo).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def set_brightness(self, brightness: BrightnessRequest) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/backlight",
            json=brightness.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return None
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_default_profiles(self) -> Union[List[Profile], DefaultProfiles, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/defaults")
        if response.status_code == 200:
            json_data = response.json()
            # Check if it's a DefaultProfiles structure or just a list
            if isinstance(json_data, dict) and (
                "default" in json_data or "community" in json_data
            ):
                return TypeAdapter(DefaultProfiles).validate_python(json_data)
            else:
                return TypeAdapter(List[Profile]).validate_python(json_data)
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_profile_default_images(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/image")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_profile_image_url(self, image: str) -> str:
        if image.startswith("data:"):
            return image
        url = "/api/v1/profile/image/"
        if not image.startswith(url):
            image = url + image
        return image

    def get_profile_image(self, image: str) -> Union[bytes, APIError]:
        response = self.session.get(self.get_profile_image_url(image), stream=True)
        if response.headers.get("Content-Type", "").startswith("image/"):
            return response.content
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_history_short_listing(self) -> Union[HistoryListingResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history")
        if response.status_code == 200:
            return TypeAdapter(HistoryListingResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def search_history(
        self, query: HistoryQueryParams
    ) -> Union[HistoryResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/history",
            json=query.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(HistoryResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def search_historical_profiles(
        self, query: str
    ) -> Union[HistoryListingResponse, APIError]:
        response = self.session.get(
            f"{self.base_url}/api/v1/history/search?query={query}"
        )
        if response.status_code == 200:
            return TypeAdapter(HistoryListingResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_current_shot(self) -> Union[HistoryEntry, None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/current")
        if response.status_code == 200:
            json_data = response.json()
            if json_data is None:
                return None
            return TypeAdapter(HistoryEntry).validate_python(json_data)
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_last_shot(self) -> Union[HistoryEntry, None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/last")
        if response.status_code == 200:
            json_data = response.json()
            if json_data is None:
                return None
            return TypeAdapter(HistoryEntry).validate_python(json_data)
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_history_statistics(self) -> Union[HistoryStats, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/stats")
        if response.status_code == 200:
            return TypeAdapter(HistoryStats).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_history_dates(self) -> Union[List[HistoryFile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/files/")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_shot_files(self, date_str: str) -> Union[List[HistoryFile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/files/{date_str}")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_shot_log(
        self, date_str: str, filename: str
    ) -> Union[Dict[str, Any], APIError]:
        url = f"{self.base_url}/api/v1/history/files/{date_str}/{filename}"
        response = self.session.get(url)

        if response.status_code != 200:
            try:
                return TypeAdapter(APIError).validate_python(response.json())
            except Exception:
                return APIError(
                    status=str(response.status_code),
                    error=f"Failed to fetch log: {response.text}",
                )

        content = response.content

        # zstd magic number: 0xFD2FB528, stored little-endian in the byte stream
        if content.startswith(b"\x28\xb5\x2f\xfd"):
            try:
                content = zstd.ZstdDecompressor().decompress(content)
            except zstd.ZstdError as exc:
                return APIError(status="Decompression Error", error=str(exc))

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            return APIError(status="JSON Parse Error", error=str(exc))

    def get_last_shot_log(self) -> Union[Dict[str, Any], APIError]:
        dates = self.get_history_dates()
        if isinstance(dates, APIError):
            return dates
        if not dates:
            return APIError(status="No Data", error="No history dates found")

        dates.sort(key=lambda date: date.name, reverse=True)
        latest_date = dates[0].name

        files = self.get_shot_files(latest_date)
        if isinstance(files, APIError):
            return files
        if not files:
            return APIError(
                status="No Data", error=f"No shot files found for {latest_date}"
            )

        files.sort(key=lambda file: file.name, reverse=True)
        latest_file = files[0]

        return self.get_shot_log(latest_date, latest_file.url)

    def get_os_status(self) -> Union[OSStatusResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/OS_update_status")
        if response.status_code == 200:
            return TypeAdapter(OSStatusResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_timezone_region(
        self, region_type: str, conditional: str
    ) -> Union[Regions, APIError]:
        response = self.session.get(
            f"{self.base_url}/api/v1/timezones/{region_type}",
            params={"filter": conditional},
        )
        if response.status_code == 200:
            return TypeAdapter(Regions).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def set_time(self, date_time: datetime) -> Union[Regions, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/time",
            json={"date": date_time.isoformat()},
        )
        if response.status_code == 200:
            return TypeAdapter(Regions).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def rate_shot(self, shot_id: int, rating: str) -> Union[RateShotResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/history/rating/{shot_id}",
            json={"rating": rating},
        )
        if response.status_code == 200:
            return TypeAdapter(RateShotResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_shot_rating(self, shot_id: int) -> Union[ShotRatingResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/rating/{shot_id}")
        if response.status_code == 200:
            return TypeAdapter(ShotRatingResponse).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())
