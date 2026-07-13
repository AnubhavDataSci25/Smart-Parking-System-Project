"""
Shared input validation for vehicle entry/exit/search — used by both
backend/api.py and backend/main.py so the two front doors to the system
(REST API and CLI) enforce identical rules.

Each validate_* function returns (True, "") on success, or
(False, "human-readable reason") on failure — callers decide how to
surface that (HTTP 400 JSON for the API, a printed message for the CLI).
"""

import re
from typing import Tuple

VALID_VEHICLE_TYPES = ("Car", "Bike", "Truck", "Other")

# Loosely matches real-world plate formats (e.g. "PB08AB1234", "DL3CAB1234")
# while staying permissive enough for a demo: 4-12 uppercase letters/digits.
_VEHICLE_NUMBER_RE = re.compile(r"^[A-Z0-9]{4,12}$")

_OWNER_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")


def validate_vehicle_number(value: str) -> Tuple[bool, str]:
    if not value or not isinstance(value, str):
        return False, "Vehicle number is required."
    normalized = value.strip().upper()
    if not _VEHICLE_NUMBER_RE.match(normalized):
        return False, "Vehicle number must be 4-12 letters/digits (e.g. PB08AB1234)."
    return True, ""


def validate_owner_name(value: str) -> Tuple[bool, str]:
    if not value or not isinstance(value, str):
        return False, "Owner name is required."
    if not _OWNER_NAME_RE.match(value.strip()):
        return False, "Owner name must be 2-50 letters (spaces, apostrophes, hyphens allowed)."
    return True, ""


def validate_vehicle_type(value: str) -> Tuple[bool, str]:
    if not value or value not in VALID_VEHICLE_TYPES:
        return False, f"Vehicle type must be one of: {', '.join(VALID_VEHICLE_TYPES)}."
    return True, ""


def validate_entry_payload(vehicle_number: str, owner_name: str, vehicle_type: str) -> Tuple[bool, str]:
    for ok, msg in (
        validate_vehicle_number(vehicle_number),
        validate_owner_name(owner_name),
        validate_vehicle_type(vehicle_type),
    ):
        if not ok:
            return False, msg
    return True, ""
