# pyright: reportGeneralTypeIssues=false
from dataclasses import dataclass
from datetime import datetime
import time
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
    LogFile,
    LastProfile,
    MachineInfo,
    Notification,
    ProfileChange,
    WiFiQRData,
    NotificationData,
    OSStatusResponse,
    ProfileImportResponse,
    PartialProfile,
    PartialSettings,
    PartialWiFiConfig,
    MachineState,
    Profile,
    ProfileEvent,
    RateShotResponse,
    Regions,
    HeaterStatus,
    OSUpdateEvent,
    TimezoneResponse,
    UpdateCheckResponse,
    UpdateStatus,
    SensorsEvent,
    Settings,
    ShotRatingResponse,
    StatusData,
    WiFiConfig,
    WiFiConfigResponse,
    WiFiConnectRequest,
    WiFiNetwork,
    WifiSystemStatus,
)


@dataclass
class ApiOptions:
    onStatus: Optional[Callable[[StatusData], None]] = None
    onSensors: Optional[Callable[[SensorsEvent], None]] = None
    onTemperatureSensors: Optional[Callable[[SensorsEvent], None]] = None
    onCommunication: Optional[Callable[[Communication], None]] = None
    onActuators: Optional[Callable[[Actuators], None]] = None
    onMachineInfo: Optional[Callable[[MachineInfo], None]] = None
    onButton: Optional[Callable[[ButtonEvent], None]] = None
    onSettingsChange: Optional[Callable[[Dict], None]] = None
    onNotification: Optional[Callable[[NotificationData], None]] = None
    onProfileChange: Optional[Callable[[ProfileEvent], None]] = None
    onHeaterStatus: Optional[Callable[[HeaterStatus], None]] = None
    onOSUpdate: Optional[Callable[[OSUpdateEvent], None]] = None
    throttle: Optional[Union[float, Dict[str, float]]] = None

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
                    interval = None
                    if isinstance(self.throttle, (int, float)):
                        interval = float(self.throttle)
                    elif isinstance(self.throttle, dict):
                        interval = self.throttle.get(event_name)

                    if interval and interval > 0:
                        gate = EventThrottle(interval=interval)
                        current_handler = handler

                        def throttled_handler(
                            *args: tuple[object, ...],
                            _handler: Callable[..., None] = current_handler,
                            _gate: EventThrottle = gate,
                            **kwargs: dict[str, object],
                        ) -> None:
                            if _gate.should_process():
                                return _handler(*args, **kwargs)
                            return None

                        sio.on(event_name, throttled_handler)
                    else:
                        sio.on(event_name, handler)


class EventThrottle:
    """Helper to throttle high-frequency Socket.IO events.

    Usage:
        throttle = EventThrottle(interval=0.25)  # process at most every 250ms

        def on_status(data: StatusData):
            if not throttle.should_process():
                return
            # handle event
    """

    def __init__(self, interval: float = 0.1) -> None:
        self.interval = interval
        self._last_emit = 0.0

    def should_process(self) -> bool:
        now = time.time()
        if now - self._last_emit >= self.interval:
            self._last_emit = now
            return True
        return False


class Api:
    ALLOWED_SOCKETIO_ACTIONS = {
        ActionType.START.value,
        ActionType.STOP.value,
        ActionType.CONTINUE.value,
        ActionType.TARE.value,
        ActionType.PREHEAT.value,
        ActionType.SCALE_MASTER_CALIBRATION.value,
        ActionType.HOME.value,
        ActionType.PURGE.value,
        ActionType.ABORT.value,
    }

    def __init__(
        self,
        base_url: str = "http://localhost:8080/",
        options: Optional[ApiOptions] = None,
    ) -> None:
        self.base_url = base_url
        self.options: ApiOptions = options or ApiOptions()
        self.sio = socketio.Client()
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

        # Register socketio event handlers if options provided
        self.options.register_handlers(self.sio)

    def connect_to_socket(
        self,
        retries: int = 0,
        backoff: float = 0.5,
        max_backoff: float = 4.0,
    ) -> None:
        attempt = 0
        delay = backoff
        while True:
            try:
                self.sio.connect(self.base_url)
                return
            except Exception:
                attempt += 1
                if attempt > retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, max_backoff)

    def disconnect_socket(self) -> None:
        self.sio.disconnect()

    def _error_from_response(self, response: requests.Response) -> APIError:
        try:
            return TypeAdapter(APIError).validate_python(response.json())
        except Exception:
            return APIError(
                error=getattr(response, "reason", "HTTP Error"),
                status=str(response.status_code),
            )

    def send_action_socketio(self, action: ActionType) -> None:
        if action.value not in self.ALLOWED_SOCKETIO_ACTIONS:
            raise ValueError(f"Unsupported Socket.IO action: {action.value}")
        self.sio.emit("action", action.value)

    def acknowledge_notification_socketio(
        self, notification_id: str, response: str
    ) -> None:
        payload = json.dumps({"id": notification_id, "response": response})
        self.sio.emit("notification", payload)

    def send_profile_hover(self, profile_data: Dict[str, Any]) -> None:
        self.sio.emit("profileHover", profile_data)

    def trigger_calibration(self, enable: bool = True) -> None:
        self.sio.emit("calibrate", enable)

    def execute_action(self, action: ActionType) -> Union[ActionResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/action/{action}")
        try:
            # Always try to parse as ActionResponse first, since the server uses HTTP 400
            # even for valid action responses (e.g., when action is not allowed)
            return TypeAdapter(ActionResponse).validate_python(response.json())
        except Exception:
            # If ActionResponse parsing fails, try APIError
            return self._error_from_response(response)

    def list_profiles(self) -> Union[List[PartialProfile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/list")
        if response.status_code == 200:
            return TypeAdapter(List[PartialProfile]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def fetch_all_profiles(self) -> Union[List[Profile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/list?full=true")
        if response.status_code == 200:
            return TypeAdapter(List[Profile]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def save_profile(self, data: Profile) -> Union[ChangeProfileResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/save",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(ChangeProfileResponse).validate_python(response.json())
        else:
            print(response.json())
            return self._error_from_response(response)

    def import_profiles(self, file_path: str) -> Union[ProfileImportResponse, APIError]:
        with open(file_path, "rb") as f:
            response = self.session.post(
                f"{self.base_url}/api/v1/profile/import", files={"file": f}
            )
        if response.status_code == 200:
            return TypeAdapter(ProfileImportResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def load_profile_from_json(self, data: Profile) -> Union[PartialProfile, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/load",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def load_profile_by_id(self, id: str) -> Union[PartialProfile, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/load/{id}")
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_profile(self, profile_id: str) -> Union[Profile, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/get/{profile_id}")
        if response.status_code == 200:
            return TypeAdapter(Profile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def delete_profile(self, profile_id: str) -> Union[ChangeProfileResponse, APIError]:
        response = self.session.delete(
            f"{self.base_url}/api/v1/profile/delete/{profile_id}"
        )
        if response.status_code == 200:
            return TypeAdapter(PartialProfile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_last_profile(self) -> Union[LastProfile, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/last")
        if response.status_code == 200:
            return TypeAdapter(LastProfile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_profile_changes(self) -> Union[List[ProfileChange], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/changes")
        if response.status_code == 200:
            return TypeAdapter(List[ProfileChange]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def load_legacy_profile(self, data: Dict[str, Any]) -> Union[Profile, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/profile/legacy",
            json=data,
        )
        if response.status_code == 200:
            return TypeAdapter(Profile).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_notifications(
        self, acknowledged: bool
    ) -> Union[List[Notification], APIError]:
        response = self.session.get(
            f"{self.base_url}/api/v1/notifications?acknowledged={acknowledged}"
        )
        if response.status_code == 200:
            return TypeAdapter(List[Notification]).validate_python(response.json())
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def update_setting(self, setting: PartialSettings) -> Union[Settings, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/settings",
            json=setting.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(Settings).validate_python(response.json())
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def update_firmware(
        self, form_data: Dict[str, IO], esp_type: str = "esp32-s3"
    ) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/update/firmware?chip={esp_type}", files=form_data
        )
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def get_wifi_config(self) -> Union[WiFiConfigResponse, WiFiConfig, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/config")
        if response.status_code == 200:
            json_data = response.json()
            if isinstance(json_data, dict) and "config" in json_data:
                config = TypeAdapter(WiFiConfig).validate_python(json_data["config"])
                status_data = json_data.get("status")
                if status_data is not None:
                    status = TypeAdapter(WifiSystemStatus).validate_python(status_data)
                    return WiFiConfigResponse(config=config, status=status)
                return config
            return TypeAdapter(WiFiConfig).validate_python(json_data)
        else:
            return self._error_from_response(response)

    def get_wifi_status(self) -> Union[WifiSystemStatus, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/status")
        if response.status_code == 200:
            return TypeAdapter(WifiSystemStatus).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def set_wifi_config(self, data: PartialWiFiConfig) -> Union[WiFiConfig, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/config",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return TypeAdapter(WiFiConfig).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_wifi_qr_url(self) -> str:
        return f"{self.base_url}/api/v1/wifi/config/qr.png"

    def get_wifi_qr(self) -> Union[bytes, APIError]:
        response = self.session.get(self.get_wifi_qr_url(), stream=True)

        if response.headers.get("Content-Type") == "image/png":
            return response.content
        else:
            return self._error_from_response(response)

    def get_wifi_qr_data(self) -> Union[WiFiQRData, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/config/qr.json")
        if response.status_code == 200:
            return TypeAdapter(WiFiQRData).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def list_available_wifi(self) -> Union[List[WiFiNetwork], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/wifi/list")
        if response.status_code == 200:
            return TypeAdapter(List[WiFiNetwork]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def scan_wifi(self) -> Union[Dict[str, Any], APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/wifi/scan")
        if response.status_code == 200:
            return response.json()
        else:
            return self._error_from_response(response)

    def connect_to_wifi(self, data: WiFiConnectRequest) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/connect",
            json=data.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def delete_wifi(self, ssid: str) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/wifi/delete", json={"ssid": ssid}
        )
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def play_sound(self, sound: str) -> Union[None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/play/{sound}")
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def list_sounds(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/list")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def list_sound_themes(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/theme/list")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_sound_theme(self) -> Union[str, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/sounds/theme/get")
        if response.status_code == 200:
            # Server returns plain text, not JSON
            return response.text.strip()
        else:
            return self._error_from_response(response)

    def set_sound_theme(self, theme: str) -> Union[None, APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/sounds/theme/set/{theme}")
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def upload_sound_theme(self, file_path: str) -> Union[None, APIError]:
        with open(file_path, "rb") as f:
            response = self.session.post(
                f"{self.base_url}/api/v1/sounds/theme/upload",
                files={"file": f},
            )
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def get_device_info(self) -> Union[DeviceInfo, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine")
        if response.status_code == 200:
            return TypeAdapter(DeviceInfo).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_machine_state(self) -> Union[MachineState, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/state")
        if response.status_code == 200:
            return TypeAdapter(MachineState).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def set_brightness(self, brightness: BrightnessRequest) -> Union[None, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/backlight",
            json=brightness.model_dump(exclude_none=True),
        )
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def check_for_updates(self) -> Union[UpdateCheckResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/check_for_updates"
        )
        if response.status_code == 200:
            return TypeAdapter(UpdateCheckResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def perform_os_update(self) -> Union[UpdateStatus, APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/machine/perform_update")
        if response.status_code == 200:
            return TypeAdapter(UpdateStatus).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def cancel_update(self) -> Union[UpdateStatus, APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/machine/cancel_update")
        if response.status_code == 200:
            return TypeAdapter(UpdateStatus).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def reboot_machine(self) -> Union[UpdateStatus, APIError]:
        response = self.session.post(f"{self.base_url}/api/v1/machine/reboot")
        if response.status_code == 200:
            return TypeAdapter(UpdateStatus).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_debug_log(self) -> Union[str, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/debug_log")
        if response.status_code == 200:
            return response.text
        else:
            return self._error_from_response(response)

    def list_logs(self) -> Union[List[LogFile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/logs")
        if response.status_code == 200:
            return TypeAdapter(List[LogFile]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_log_file(self, filename: str) -> Union[bytes, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/logs/{filename}")
        if response.status_code == 200:
            return response.content
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def get_profile_default_images(self) -> Union[List[str], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/profile/image")
        if response.status_code == 200:
            return TypeAdapter(List[str]).validate_python(response.json())
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def get_history_short_listing(self) -> Union[HistoryListingResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history")
        if response.status_code == 200:
            return TypeAdapter(HistoryListingResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def search_historical_profiles(
        self, query: str
    ) -> Union[HistoryListingResponse, APIError]:
        response = self.session.get(
            f"{self.base_url}/api/v1/history/search?query={query}"
        )
        if response.status_code == 200:
            return TypeAdapter(HistoryListingResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_current_shot(self) -> Union[HistoryEntry, None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/current")
        if response.status_code == 200:
            json_data = response.json()
            if json_data is None:
                return None
            return TypeAdapter(HistoryEntry).validate_python(json_data)
        else:
            return self._error_from_response(response)

    def get_last_shot(self) -> Union[HistoryEntry, None, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/last")
        if response.status_code == 200:
            json_data = response.json()
            if json_data is None:
                return None
            return TypeAdapter(HistoryEntry).validate_python(json_data)
        else:
            return self._error_from_response(response)

    def get_history_statistics(self) -> Union[HistoryStats, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/stats")
        if response.status_code == 200:
            return TypeAdapter(HistoryStats).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def delete_history_entry(self, shot_id: str) -> Union[None, APIError]:
        response = self.session.delete(f"{self.base_url}/api/v1/history/{shot_id}")
        if response.status_code == 200:
            return None
        else:
            return self._error_from_response(response)

    def export_history(self) -> Union[bytes, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/export")
        if response.status_code == 200:
            return response.content
        else:
            return self._error_from_response(response)

    def get_history_dates(self) -> Union[List[HistoryFile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/files/")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_shot_files(self, date_str: str) -> Union[List[HistoryFile], APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/files/{date_str}")
        if response.status_code == 200:
            return TypeAdapter(List[HistoryFile]).validate_python(response.json())
        else:
            return self._error_from_response(response)

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
            return self._error_from_response(response)

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
            return self._error_from_response(response)

    def get_timezones(self) -> Union[Regions, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/timezones")
        if response.status_code == 200:
            return TypeAdapter(Regions).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_timezone(self) -> Union[TimezoneResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/machine/timezone")
        if response.status_code == 200:
            return TypeAdapter(TimezoneResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def set_timezone(self, timezone: str) -> Union[TimezoneResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/timezone",
            json={"timezone": timezone},
        )
        if response.status_code == 200:
            return TypeAdapter(TimezoneResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def set_time(self, date_time: datetime) -> Union[Regions, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/machine/time",
            json={"date": date_time.isoformat()},
        )
        if response.status_code == 200:
            return TypeAdapter(Regions).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def rate_shot(self, shot_id: int, rating: str) -> Union[RateShotResponse, APIError]:
        response = self.session.post(
            f"{self.base_url}/api/v1/history/rating/{shot_id}",
            json={"rating": rating},
        )
        if response.status_code == 200:
            return TypeAdapter(RateShotResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)

    def get_shot_rating(self, shot_id: int) -> Union[ShotRatingResponse, APIError]:
        response = self.session.get(f"{self.base_url}/api/v1/history/rating/{shot_id}")
        if response.status_code == 200:
            return TypeAdapter(ShotRatingResponse).validate_python(response.json())
        else:
            return self._error_from_response(response)
