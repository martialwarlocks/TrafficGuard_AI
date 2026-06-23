"""Indian Motor Vehicles Act penalty reference for traffic violations."""

from ml.violations.catalog import VIOLATION_CATALOG

# Standard first-offence penalties (Motor Vehicles Act, 1988 — amended 2019/2020)
INDIAN_FINE_TABLE: dict[str, dict] = {
    "red_light": {
        "fine_inr": 1000,
        "legal_section": "Section 184 / Section 177, Motor Vehicles Act, 1988",
        "description": "Jumping a red traffic signal or disobeying traffic control device",
        "repeat_fine_inr": 5000,
    },
    "stop_line": {
        "fine_inr": 500,
        "legal_section": "Section 177, Motor Vehicles Act, 1988",
        "description": "Stopping beyond stop line or on pedestrian crossing (zebra crossing)",
    },
    "helmet": {
        "fine_inr": 1000,
        "legal_section": "Section 194D, Motor Vehicles Act, 1988",
        "description": "Riding a two-wheeler without protective headgear (helmet)",
    },
    "seatbelt": {
        "fine_inr": 1000,
        "legal_section": "Section 194B, Motor Vehicles Act, 1988",
        "description": "Driving or riding in a motor vehicle without seatbelt",
    },
    "triple_riding": {
        "fine_inr": 1000,
        "legal_section": "Section 194C, Motor Vehicles Act, 1988",
        "description": "Carrying more than one pillion rider on a two-wheeler",
    },
    "wrong_side": {
        "fine_inr": 1000,
        "legal_section": "Section 184, Motor Vehicles Act, 1988",
        "description": "Driving against the authorised flow of traffic (wrong-side driving)",
        "repeat_fine_inr": 5000,
    },
    "parking": {
        "fine_inr": 500,
        "legal_section": "Section 122 / Section 177, Motor Vehicles Act, 1988",
        "description": "Parking in a no-parking zone or causing obstruction",
    },
}

VALID_VIOLATION_TYPES = {v["id"] for v in VIOLATION_CATALOG}


def get_fine_for_violation(violation_type: str | None) -> dict:
    """Return fine details for a violation type, or zero if none."""
    if not violation_type or violation_type not in INDIAN_FINE_TABLE:
        return {
            "fine_inr": 0.0,
            "legal_section": None,
            "description": None,
        }
    entry = INDIAN_FINE_TABLE[violation_type]
    return {
        "fine_inr": float(entry["fine_inr"]),
        "legal_section": entry["legal_section"],
        "description": entry["description"],
    }


def build_fine_prompt_block() -> str:
    lines = []
    for v in VIOLATION_CATALOG:
        fine = INDIAN_FINE_TABLE.get(v["id"], {})
        lines.append(
            f"- {v['id']}: {v['label']} — ₹{fine.get('fine_inr', v.get('fine_inr', 0))} "
            f"({fine.get('legal_section', 'MV Act')})"
        )
    return "\n".join(lines)
