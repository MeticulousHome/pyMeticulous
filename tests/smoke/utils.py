import os
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import requests
from meticulous.api import Api, ApiOptions
from meticulous.api_types import (
    StatusData,
    Temperatures,
    NotificationData,
    ProfileEvent,
)


def get_base_url() -> str:
    env_url = os.environ.get("METICULOUS_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    # Default to the provided machine IP
    return "http://192.168.0.115:8080"


class EventCollector:
    def __init__(self) -> None:
        self.status_events: List[StatusData] = []
        self.temperature_events: List[Temperatures] = []
        self.notification_events: List[NotificationData] = []
        self.profile_events: List[ProfileEvent] = []

    def on_status(self, data: StatusData) -> None:
        self.status_events.append(data)

    def on_temperatures(self, data: Temperatures) -> None:
        self.temperature_events.append(data)

    def on_notification(self, data: NotificationData) -> None:
        self.notification_events.append(data)

    def on_profile(self, data: ProfileEvent) -> None:
        self.profile_events.append(data)


def make_api_with_events() -> Tuple[Api, EventCollector]:
    collector = EventCollector()
    options = ApiOptions(
        onStatus=collector.on_status,
        onTemperatureSensors=collector.on_temperatures,
        onNotification=collector.on_notification,
        onProfileChange=collector.on_profile,
    )
    api = Api(base_url=get_base_url(), options=options)
    return api, collector


def wait_for_events(
    collector: EventCollector,
    timeout_sec: float = 5.0,
    expect_profile_change: bool = False,
) -> Dict[str, Any]:
    """Wait briefly for events to arrive and return counts.

    If expect_profile_change is True, wait slightly longer for profile events.
    """
    deadline = time.time() + (
        timeout_sec if not expect_profile_change else timeout_sec + 5
    )
    while time.time() < deadline:
        time.sleep(0.1)
    return {
        "status": len(collector.status_events),
        "temperatures": len(collector.temperature_events),
        "notifications": len(collector.notification_events),
        "profiles": len(collector.profile_events),
    }


def choose_random_different_profile_id(
    api: Api, current_profile_id: Optional[str]
) -> Optional[str]:
    profiles = api.list_profiles()
    from meticulous.api_types import APIError

    if isinstance(profiles, APIError):
        return None
    # profiles may be APIError; the caller should assert type
    try:
        candidates = [
            p for p in profiles if getattr(p, "id", None) and p.id != current_profile_id
        ]
    except Exception:
        return None
    if not candidates:
        return None
    return random.choice(candidates).id


def get_current_weight_from_status(status: Any) -> Optional[float]:
    # status may be a dict or StatusData object depending on how socketio delivers it
    sensors = (
        status.get("sensors")
        if isinstance(status, dict)
        else getattr(status, "sensors", None)
    )
    if isinstance(sensors, dict):
        # expect 'w' field for weight
        w = sensors.get("w")
        return float(w) if isinstance(w, (int, float)) else None
    try:
        return float(getattr(sensors, "w"))
    except Exception:
        return None


def server_reachable(base_url: str) -> bool:
    try:
        resp = requests.get(f"{base_url}/api/v1/machine", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
