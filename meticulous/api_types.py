# pyright: reportCallIssue=false, reportUnusedVariable=false
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
    CONTINUE = "continue"
    RESET = "reset"
    TARE = "tare"
    PREHEAT = "preheat"
    CALIBRATION = "calibration"
    SCALE_MASTER_CALIBRATION = "scale_master_calibration"


class APIError(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    error: Optional[str] = None
    status: Optional[str] = None


class AcknowledgeNotificationRequest(BaseModel):
    id: str
    response: str


class ActionResponse(BaseModel):
    status: Optional[str] = None
    action: Optional[str] = None
    allowed_actions: Optional[List[str]] = None


class Notification(BaseModel):
    id: str
    message: str
    image: Optional[str] = None
    response_options: Optional[List[str]] = None
    timestamp: str


# Generate PartialProfile dynamically from Settings
PartialProfile = create_model(  # type: ignore[call-overload]
    "PartialProfile",
    **{  # type: ignore[arg-type]
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


class ReverseScrolling(BaseModel):
    home: bool
    keyboard: bool
    menus: bool


class Settings(BaseModel):
    allow_debug_sending: Optional[bool] = None
    auto_preheat: int
    auto_purge_after_shot: bool
    auto_start_shot: bool
    partial_retraction: int
    disallow_firmware_flashing: bool
    disable_ui_features: bool
    enable_sounds: bool
    debug_shot_data_retention_days: int
    idle_screen: str
    reverse_scrolling: ReverseScrolling
    heating_timeout: int
    timezone_sync: str
    time_zone: str
    usb_mode: str  # 'client' | 'host' | 'dual_role'
    update_channel: str
    ssh_enabled: bool


# Generate PartialSettings dynamically from Settings
PartialSettings = create_model(  # type: ignore[call-overload]
    "PartialSettings",
    **{  # type: ignore[arg-type]
        name: (Optional[field.annotation], None)
        for name, field in Settings.model_fields.items()
    },
)


class APMode(str, Enum):
    AP = "AP"
    CLIENT = "CLIENT"


class WiFiConfig(BaseModel):
    mode: str  # APMode
    apName: str
    apPassword: str


class WifiSystemStatus(BaseModel):
    connected: bool
    connection_name: str
    gateway: str
    routes: List[str]
    ips: List[str]
    dns: List[str]
    mac: str
    hostname: str
    domains: List[str]


# Generate PartialWiFiConfig dynamically from WiFiConfig
PartialWiFiConfig = create_model(  # type: ignore[call-overload]
    "PartialWiFiConfig",
    **{  # type: ignore[arg-type]
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
    type: Optional[str] = None  # 'PSK' | '802.1X' | 'OPEN' | 'WEP'
    security: Optional[str] = None


class SensorData(BaseModel):
    p: float
    f: float
    w: float
    t: float
    g: float


class SetpointData(BaseModel):
    active: Optional[str] = None
    temperature: Optional[float] = None
    flow: Optional[float] = None
    pressure: Optional[float] = None
    power: Optional[float] = None
    piston: Optional[float] = None


@on_event("status")
class StatusData(BaseModel):
    name: str
    sensors: Union[Dict[str, Union[int, float]], SensorData]
    time: int
    profile_time: Optional[int] = None
    profile: str
    loaded_profile: Optional[str] = None
    id: Optional[str] = None
    state: Optional[str] = None
    extracting: Optional[bool] = None
    setpoints: Optional[SetpointData] = None


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


class DeviceInfo(BaseModel):
    name: str
    hostname: str
    firmware: str
    mainVoltage: float
    color: str
    model_version: str
    serial: str
    batch_number: str
    build_date: str
    software_version: Optional[str] = None
    image_build_channel: str
    image_version: str
    manufacturing: bool
    upgrade_first_boot: bool
    version_history: List[str]


class HistoryProfile(Profile):
    db_key: int


class HistorySensorData(BaseModel):
    external_1: float
    external_2: float
    bar_up: float
    bar_mid_up: float
    bar_mid_down: float
    bar_down: float
    tube: float
    valve: float
    motor_position: float
    motor_speed: float
    motor_power: float
    motor_current: float
    bandheater_power: float
    preassure_sensor: float
    adc_0: float
    adc_1: float
    adc_2: float
    adc_3: float
    water_status: bool


class HistoryShotData(BaseModel):
    pressure: float
    flow: float
    weight: float
    temperature: float
    gravimetric_flow: float


class HistoryDataPoint(BaseModel):
    shot: HistoryShotData
    time: int
    status: str
    sensors: HistorySensorData


class ShotRating(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "null"


class HistoryBaseEntry(BaseModel):
    id: str
    db_key: Optional[int] = None
    time: int
    file: Optional[str] = None
    name: str
    profile: HistoryProfile
    rating: Optional[str] = None  # ShotRating
    debug_file: Optional[str] = None


class HistoryEntry(HistoryBaseEntry):
    data: List[HistoryDataPoint]


class HistoryListingEntry(HistoryBaseEntry):
    data: None = None


class HistoryResponse(BaseModel):
    history: List[HistoryEntry]


class HistoryListingResponse(BaseModel):
    history: List[HistoryListingEntry]


class HistoryQueryParams(BaseModel):
    query: Optional[str] = None
    ids: Optional[List[Union[int, str]]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    order_by: Optional[List[str]] = None  # 'profile' | 'date'
    sort: Optional[str] = None  # 'asc' | 'desc'
    max_results: Optional[int] = None
    dump_data: Optional[bool] = None


class ProfileByCount(BaseModel):
    name: str
    count: int
    profileVersions: int


class HistoryStats(BaseModel):
    totalSavedShots: int
    byProfile: List[ProfileByCount]


class BrightnessRequest(BaseModel):
    brightness: int
    interpolation: Optional[str] = None  # 'curve' | 'linear'
    animation_time: Optional[int] = None


class Regions(BaseModel):
    countries: Optional[List[str]] = None
    cities: Optional[List[Dict[str, str]]] = None


class OSStatusResponse(BaseModel):
    progress: Optional[int] = None
    status: Optional[str] = None
    info: Optional[str] = None


class ShotRatingResponse(BaseModel):
    shot_id: int
    rating: Optional[str] = None


class RateShotResponse(BaseModel):
    status: str
    shot_id: int
    rating: Optional[str] = None


class DefaultProfiles(BaseModel):
    default: List[Profile]
    community: List[Profile]
