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
            {"name": "Pressure", "key": "pressure_1", "type": "pressure", "value": 8}
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
            {"name": "Pressure", "key": "pressure_1", "type": "pressure", "value": 8}
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
        {"name": "Pressure", "key": "pressure_1", "type": "pressure", "value": 8}
    ],
    "stages": [
        {
            "name": "Preinfusion",
            "key": "preinfusion_1",
            "type": "flow",
            "dynamics": {"points": [[0, 4]], "over": "time", "interpolation": "linear"},
            "exit_triggers": [
                {"type": "time", "value": 30, "relative": True, "comparison": ">="},
                {"type": "weight", "value": 0.3, "relative": True, "comparison": ">="},
                {"type": "pressure", "value": 8, "relative": False, "comparison": ">="},
            ],
            "limits": [],
        },
        {
            "name": "Infusion",
            "key": "infusion_1",
            "type": "pressure",
            "dynamics": {
                "points": [[0, 0], [10, 8], [20, 8]],
                "over": "time",
                "interpolation": "curve",
            },
            "exit_triggers": [],
            "limits": [{"type": "flow", "value": 3}],
        },
    ],
    "display": {"image": "/api/v1/profile/image/ed03e12bb34fc419c5adfd7d993b50e7.png"},
    "last_changed": 1716585650.3912911,
}
