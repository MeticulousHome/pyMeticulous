from dataclasses import dataclass
from typing import IO, Any, Callable, Dict, List, Optional, Self, Union, get_args
from datetime import datetime

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
    ButtonEvent,
    ChangeProfileResponse,
    Communication,
    HistoryFile,
    LastProfile,
    MachineInfo,
    Notification,
    NotificationData,
    PartialProfile,
    PartialSettings,
    PartialWiFiConfig,
    Profile,
    ProfileEvent,
    Settings,
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
    ) -> Self:
        self.base_url = base_url
        self.options = options or ApiOptions()
        self.sio = socketio.Client()
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

        # Register socketio event handlers if options provided
        self.options.register_handlers(self.sio)

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

    def list_profiles(self) -> Union[List[PartialProfile], APIError]:
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

    def load_profile_from_json(self, data: Profile) -> Union[PartialProfile, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/load",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def load_profile_by_id(self, id: str) -> Union[PartialProfile, APIError]:
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

    def update_setting(self, setting: PartialSettings) -> Union[Settings, APIError]:
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
            return TypeAdapter(WiFiConfig).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def set_wifi_config(self, data: PartialWiFiConfig) -> Union[WiFiConfig, APIError]:
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

    def get_history_dates(self) -> Union[List[HistoryFile], APIError]:
        """Get list of dates available in history."""
        response = self.session.get(f"{self.base_url}/api/v1/history/files/")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_shot_files(self, date_str: str) -> Union[List[HistoryFile], APIError]:
        """Get list of shot files for a specific date (YYYY-MM-DD)."""
        response = self.session.get(f"{self.base_url}/api/v1/history/files/{date_str}")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return TypeAdapter(APIError).validate_python(response.json())

    def get_shot_log(self, date_str: str, filename: str) -> Union[Dict[str, Any], APIError]:
        """Get and parse a specific shot log file.
        
        Handles .zst decompression if needed.
        """
        # The filename in the list might differ from the URL suffix
        # We construct the URL. If the file list says url is "21:04:06.shot.json.zst", use that.
        # Ideally the user passes the 'url' field from the get_shot_files result.
        # But if they pass just the name "21:04:06.shot.json", we might need to check extension.
        
        # We will assume 'filename' is the one to append to the URL path.
        # If it comes from get_shot_files(), use the 'url' field.
        
        url = f"{self.base_url}/api/v1/history/files/{date_str}/{filename}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            # Try to handle APIError if json, otherwise return generic error
            try:
                return TypeAdapter(APIError).validate_python(response.json())
            except Exception:
                 return APIError(status=str(response.status_code), error=f"Failed to fetch log: {response.text}")

        content = response.content
        
        # Check if it is zstd compressed (magic number 0xFD2FB528)
        if content.startswith(b'\x28\xb5\x2f\xfd'):
            try:
                dctx = zstd.ZstdDecompressor()
                content = dctx.decompress(content)
            except zstd.ZstdError as e:
                 return APIError(status="Decompression Error", error=str(e))
        
        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError as e:
            return APIError(status="JSON Parse Error", error=str(e))

    def get_last_shot_log(self) -> Union[Dict[str, Any], APIError]:
        """Convenience method to get the absolutely latest shot log."""
        # 1. Get dates
        dates = self.get_history_dates()
        if isinstance(dates, APIError):
            return dates
        if not dates:
            return APIError(status="No Data", error="No history dates found")
            
        # Sort dates descending (names are YYYY-MM-DD so string sort works)
        dates.sort(key=lambda x: x.name, reverse=True)
        latest_date = dates[0].name
        
        # 2. Get files for latest date
        files = self.get_shot_files(latest_date)
        if isinstance(files, APIError):
            return files
        if not files:
            return APIError(status="No Data", error=f"No shot files found for {latest_date}")
            
        # Sort files descending (names are HH:MM:SS.shot.json)
        files.sort(key=lambda x: x.name, reverse=True)
        latest_file = files[0]
        
        # 3. Fetch log
        # Use 'url' field which includes .zst extension usually
        return self.get_shot_log(latest_date, latest_file.url)
