import json

import zstandard as zstd


MOCK_PROFILE_LIST_RESPONSE = [
    {
        "name": "Italian limbus",
        "id": "05051ed3-9996-43e8-9da6-963f2b31d481",
        "author": "meticulous",
        "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
        "previous_authors": [
            {
                "name": "mimoja",
                "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
                "profile_id": "0cdf18ca-d72e-4776-8e25-7b3279907dce",
            }
        ],
        "temperature": 90.5,
        "final_weight": 40,
        "variables": [
            {
                "name": "Pressure",
                "key": "pressure_1",
                "type": "pressure",
                "value": "$pressure_var",
            }
        ],
        "display": {
            "image": "/api/v1/profile/image/ed03e12bb34fc419c5adfd7d993b50e7.png"
        },
        "last_changed": 1716585650.3912911,
    },
    {
        "name": "Spring",
        "id": "8d2de185-34c9-4ead-a46d-4ab056de1806",
        "author": "meticulous",
        "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
        "display": {
            "accentColor": "#FF5733",
            "image": "/api/v1/profile/image/95a071cc55559eebced28b113b813d72.png",
        },
        "previous_authors": [
            {
                "name": "mimoja",
                "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
                "profile_id": "0cdf18ca-d72e-4776-8e25-7b3279907dce",
            },
            {
                "name": "mimojas fiánce",
                "author_id": "ee86a777-fdd6-46d6-8cf7-099a9fb609a1",
                "profile_id": "58036fd5-7d5b-4647-9ab6-2832014bb9be",
            },
        ],
        "temperature": 90.5,
        "final_weight": 40,
        "variables": [
            {
                "name": "Pressure",
                "key": "pressure_1",
                "type": "pressure",
                "value": "$pressure_var",
            }
        ],
        "last_changed": 1717635853.8201907,
    },
    {
        "name": "New Profile",
        "id": "06050134-0680-408e-8fe4-60e7d329b136",
        "author": "web-app",
        "author_id": "00000000-0000-0000-0000-000000000000",
        "previous_authors": [],
        "variables": [],
        "temperature": 90,
        "final_weight": 42,
        "display": {
            "image": "/api/v1/profile/image/f9e16abcc19c1a34deaa9c2ac3bc7653.png"
        },
        "last_changed": 1716934358.5006423,
    },
]


MOCK_PROFILE_RESPONSE = {
    "name": "Italian limbus",
    "id": "05051ed3-9996-43e8-9da6-963f2b31d481",
    "author": "meticulous",
    "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
    "previous_authors": [
        {
            "name": "mimoja",
            "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
            "profile_id": "0cdf18ca-d72e-4776-8e25-7b3279907dce",
        },
        {
            "name": "decentespresso",
            "author_id": "ee86a777-fdd6-46d6-8cf7-099a9fb609a1",
            "profile_id": "58036fd5-7d5b-4647-9ab6-2832014bb9be",
        },
    ],
    "temperature": 90.5,
    "final_weight": 40,
    "variables": [
        {
            "name": "Pressure",
            "key": "pressure_1",
            "type": "pressure",
            "value": "$pressure_var",
        }
    ],
    "stages": [
        {
            "name": "Preinfusion",
            "key": "preinfusion_1",
            "type": "flow",
            "dynamics": {
                "points": [[0, "${flow_start}"], [5, "$flow_mid"]],
                "over": "time",
                "interpolation": "linear",
            },
            "exit_triggers": [
                {
                    "type": "time",
                    "value": "${time_exit}",
                    "relative": True,
                    "comparison": ">=",
                },
                {
                    "type": "weight",
                    "value": "$weight_exit",
                    "relative": True,
                    "comparison": ">=",
                },
                {
                    "type": "pressure",
                    "value": "$pressure_exit",
                    "relative": False,
                    "comparison": ">=",
                },
            ],
            "limits": [],
        },
        {
            "name": "Infusion",
            "key": "infusion_1",
            "type": "pressure",
            "dynamics": {
                "points": [[0, 0], [10, "$pressure_ramp"], [20, "$pressure_hold"]],
                "over": "time",
                "interpolation": "curve",
            },
            "exit_triggers": [],
            "limits": [{"type": "flow", "value": "$flow_limit"}],
        },
    ],
    "display": {"image": "/api/v1/profile/image/ed03e12bb34fc419c5adfd7d993b50e7.png"},
    "last_changed": 1716585650.3912911,
}


MOCK_HISTORY_DATES_RESPONSE = [
    {"name": "2024-01-02", "url": "2024-01-02"},
    {"name": "2024-01-01", "url": "2024-01-01"},
]


MOCK_SHOT_FILES_RESPONSE = [
    {"name": "21:04:06.shot.json", "url": "21:04:06.shot.json"},
    {"name": "20:55:00.shot.json.zst", "url": "20:55:00.shot.json.zst"},
]


MOCK_SHOT_LOG_RESPONSE = {"shot": "latest", "value": 1}


def _build_zst_payload(payload: dict) -> bytes:
    compressor = zstd.ZstdCompressor()
    return compressor.compress(json.dumps(payload).encode("utf-8"))


MOCK_SHOT_LOG_ZST = _build_zst_payload(MOCK_SHOT_LOG_RESPONSE)


MOCK_DEVICE_INFO_RESPONSE = {
    "name": "meticulous",
    "hostname": "meticulous-12345",
    "firmware": "v1.2.3",
    "mainVoltage": 230.5,
    "color": "black",
    "model_version": "v1",
    "serial": "MT12345678",
    "batch_number": "B001",
    "build_date": "2024-01-15",
    "software_version": "1.2.3",
    "image_build_channel": "stable",
    "image_version": "1.2.3",
    "manufacturing": False,
    "upgrade_first_boot": False,
    "version_history": ["1.0.0", "1.1.0", "1.2.0", "1.2.3"],
}


MOCK_HISTORY_LISTING_RESPONSE = {
    "history": [
        {
            "id": "shot-001",
            "db_key": 1,
            "time": 1704067200,
            "file": "/data/shots/shot-001.json",
            "name": "Morning espresso",
            "profile": {
                "db_key": 1,
                "name": "Italian limbus",
                "id": "05051ed3-9996-43e8-9da6-963f2b31d481",
                "author": "meticulous",
                "author_id": "d9123a0a-d3d7-40fd-a548-b81376e43f23",
                "temperature": 90.5,
                "final_weight": 40,
                "stages": [],
            },
            "rating": "like",
            "data": None,
        }
    ]
}


MOCK_HISTORY_STATS_RESPONSE = {
    "totalSavedShots": 150,
    "byProfile": [
        {"name": "Italian limbus", "count": 75, "profileVersions": 3},
        {"name": "Spring", "count": 50, "profileVersions": 2},
        {"name": "Turbo", "count": 25, "profileVersions": 1},
    ],
}


MOCK_SETTINGS_RESPONSE = {
    "allow_debug_sending": True,
    "auto_preheat": 5,
    "auto_purge_after_shot": True,
    "auto_start_shot": False,
    "partial_retraction": 0,
    "disallow_firmware_flashing": False,
    "disable_ui_features": False,
    "enable_sounds": True,
    "debug_shot_data_retention_days": 30,
    "idle_screen": "clock",
    "reverse_scrolling": {"home": False, "keyboard": False, "menus": False},
    "heating_timeout": 300,
    "timezone_sync": "auto",
    "time_zone": "America/New_York",
    "usb_mode": "client",
    "update_channel": "stable",
    "ssh_enabled": False,
}


MOCK_DEFAULT_PROFILES_RESPONSE = {
    "default": [MOCK_PROFILE_RESPONSE],
    "community": [MOCK_PROFILE_RESPONSE],
}


MOCK_SHOT_RATING_RESPONSE = {"shot_id": 1, "rating": "like"}


MOCK_RATE_SHOT_RESPONSE = {"status": "success", "shot_id": 1, "rating": "like"}


MOCK_OS_STATUS_RESPONSE = {
    "progress": 75,
    "status": "updating",
    "info": "Installing system updates",
}


MOCK_REGIONS_RESPONSE = {"countries": ["US", "CA", "MX"], "cities": None}
