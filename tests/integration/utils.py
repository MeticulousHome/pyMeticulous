import os
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import requests
from meticulous.api import Api, ApiOptions
from meticulous.api_types import (
    StatusData,
    SensorsEvent,
    NotificationData,
    ProfileEvent,
)


def get_base_url() -> str:
    """Get base URL from local config file, environment variable, or default.

    Priority order:
    1. local_config.py file (gitignored, for local development)
    2. METICULOUS_HOST environment variable
    3. Default localhost:8080

    To set up local config:
        cp tests/integration/local_config.example.py tests/integration/local_config.py
        # Edit local_config.py and set your machine's IP address

    Or use environment variable:
        export METICULOUS_HOST=192.168.1.100:8080  # Linux/Mac
        $env:METICULOUS_HOST="192.168.1.100:8080"  # PowerShell
    """
    # Try local config file first (gitignored)
    try:
        from . import local_config

        host = getattr(local_config, "METICULOUS_HOST", None)
        if host:
            if not host.startswith(("http://", "https://")):
                host = f"http://{host}"
            return host.rstrip("/")
    except ImportError:
        pass

    # Fall back to environment variable
    env_host = os.environ.get("METICULOUS_HOST")
    if env_host:
        # Add http:// if not present
        if not env_host.startswith(("http://", "https://")):
            env_host = f"http://{env_host}"
        return env_host.rstrip("/")

    # Default fallback
    return "http://localhost:8080"


class EventCollector:
    def __init__(self) -> None:
        self.status_events: List[StatusData] = []
        self.sensor_events: List[SensorsEvent] = []
        self.notification_events: List[NotificationData] = []
        self.profile_events: List[ProfileEvent] = []

    def on_status(self, data: StatusData) -> None:
        self.status_events.append(data)

    def on_sensors(self, data: SensorsEvent) -> None:
        self.sensor_events.append(data)

    def on_notification(self, data: NotificationData) -> None:
        self.notification_events.append(data)

    def on_profile(self, data: ProfileEvent) -> None:
        self.profile_events.append(data)


def make_api_with_events() -> Tuple[Api, EventCollector]:
    collector = EventCollector()
    options = ApiOptions(
        onStatus=collector.on_status,
        onSensors=collector.on_sensors,
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
        "sensors": len(collector.sensor_events),
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


def get_current_weight_from_status(status: object) -> Optional[float]:
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
