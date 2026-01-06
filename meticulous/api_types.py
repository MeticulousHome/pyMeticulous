from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Type, Union
from .profile import Profile
from pydantic import AnyUrl, BaseModel, create_model, ConfigDict


def on_event(event_name: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        cls._socketio_event = event_name
        return cls

    return decorator


class ActionType(str, Enum):
    START = "start"
    STOP = "stop"
    RESET = "reset"
    TARE = "tare"
    CALIBRATION = "calibration"


class APIError(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    error: Optional[str] = None
    status: Optional[str] = None


class AcknowledgeNotificationRequest(BaseModel):
    id: str
    response: str


class ActionResponse(BaseModel):
    status: str
    action: Optional[str] = None
    allowed_actions: Optional[List[str]] = None


class Notification(BaseModel):
    id: str
    message: str
    image: Optional[str] = None
    response_options: Optional[List[str]] = None
    timestamp: str


# Generate PartialProfile dynamically from Settings
PartialProfile = create_model(
    "PartialProfile",
    **{
        name: (Optional[field.annotation], None)
        for name, field in Profile.model_fields.items()
    },
)


class ChangeProfileResponse(BaseModel):
    change_id: str
    profile: Profile


class LastProfile(BaseModel):
    load_time: int
    profile: Profile


SettingsKey = Union[bool, int]


class Settings(BaseModel):
    auto_preheat: int
    auto_purge_after_shot: bool
    auto_start_shot: bool
    disallow_firmware_flashing: bool
    enable_sounds: bool
    save_debug_shot_data: bool


# Generate PartialSettings dynamically from Settings
PartialSettings = create_model(
    "PartialSettings",
    **{
        name: (Optional[field.annotation], None)
        for name, field in Settings.model_fields.items()
    },
)


class WiFiConfig(BaseModel):
    mode: str
    apName: str
    apPassword: str


# Generate PartialWiFiConfig dynamically from WiFiConfig
PartialWiFiConfig = create_model(
    "PartialWiFiConfig",
    **{
        name: (Optional[field.annotation], None)
        for name, field in WiFiConfig.model_fields.items()
    },
)


class WiFiConnectRequest(BaseModel):
    ssid: str
    password: str


class WiFiNetwork(BaseModel):
    ssid: str
    signal: int
    rate: int
    in_use: bool


@on_event("status")
class StatusData(BaseModel):
    name: str
    sensors: Dict[str, Union[int, float]]
    time: int
    profile: str
    state: Optional[str] = None
    extrcting: Optional[bool] = None


@on_event("sensors")
class Temperatures(BaseModel):
    t_ext_1: float
    t_ext_2: float
    t_bar_up: float
    t_bar_mu: float
    t_bar_md: float
    t_bar_down: float
    t_tube: float
    t_valv: float


@on_event("communication")
class Communication(BaseModel):
    p: int
    a_0: int
    a_1: int
    a_2: int
    a_3: int


@on_event("actuators")
class Actuators(BaseModel):
    m_pos: int
    m_spd: int
    m_pwr: int
    m_cur: int
    bh_pwr: int


@on_event("button")
class ButtonEvent(BaseModel):
    type: str
    time_since_last_event: int


@on_event("notification")
class NotificationData(BaseModel):
    id: str
    message: str
    image: Optional[AnyUrl] = None
    responses: List[str]
    timestamp: datetime


@on_event("profile")
class ProfileEvent(BaseModel):
    change: str
    profile_id: Optional[str] = None
    change_id: Optional[str] = None


@on_event("info")
class MachineInfo(BaseModel):
    software_info: Dict[str, Union[str, int, float]]
    esp_info: Dict[str, Union[str, int, float]]


class HistoryFile(BaseModel):
    name: str
    url: str
