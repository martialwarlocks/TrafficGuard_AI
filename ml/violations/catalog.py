"""All supported traffic violation categories."""

VIOLATION_CATALOG = [
    {
        "id": "red_light",
        "label": "Red Light / Signal Jump",
        "description": "Vehicle crossing intersection during red signal",
        "icon": "traffic-light",
        "fine_inr": 1000,
    },
    {
        "id": "stop_line",
        "label": "Stop Line / Crosswalk Violation",
        "description": "Vehicle stopped beyond stop line or on pedestrian crossing",
        "icon": "minus-square",
        "fine_inr": 500,
    },
    {
        "id": "helmet",
        "label": "No Helmet",
        "description": "Two-wheeler rider without helmet",
        "icon": "hard-hat",
        "fine_inr": 1000,
    },
    {
        "id": "seatbelt",
        "label": "No Seatbelt",
        "description": "Car occupant without seatbelt fastened",
        "icon": "shield",
        "fine_inr": 1000,
    },
    {
        "id": "triple_riding",
        "label": "Triple Riding",
        "description": "More than two persons on a two-wheeler",
        "icon": "users",
        "fine_inr": 1000,
    },
    {
        "id": "wrong_side",
        "label": "Wrong Side Driving",
        "description": "Vehicle traveling against traffic flow",
        "icon": "arrow-left-right",
        "fine_inr": 1000,
    },
    {
        "id": "parking",
        "label": "Illegal Parking",
        "description": "Vehicle parked in no-parking zone beyond time limit",
        "icon": "parking-circle",
        "fine_inr": 500,
    },
]

VIOLATION_PRIORITY = [
    "red_light",
    "stop_line",
    "wrong_side",
    "triple_riding",
    "helmet",
    "seatbelt",
    "parking",
]

FRIENDLY_VIOLATION_LABELS = {v["id"]: v["label"] for v in VIOLATION_CATALOG}
