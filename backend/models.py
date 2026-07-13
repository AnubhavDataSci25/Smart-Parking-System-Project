"""
Data models mirroring the PostgreSQL tables in database/schema.sql.
Plain dataclasses — no ORM — so the mapping to SQL stays explicit and
easy to reason about for a college project.
"""

from dataclasses import dataclass


@dataclass
class Vehicle:
    vehicle_number: str
    owner_name: str
    vehicle_type: str          # "Car" | "Bike" | "Truck" | "Other"
    vehicle_id: int = -1        # -1 == not yet persisted


@dataclass
class ParkingSlot:
    slot_number: str            # e.g. "A1"
    slot_type: str              # "General" | "Bike" | "Handicap" | "EV"
    status: str = "Empty"       # "Empty" | "Occupied" | "Reserved" | "OutOfService"
    slot_id: int = -1

    def is_available(self) -> bool:
        return self.status == "Empty"


@dataclass
class ParkingRecord:
    vehicle_id: int
    slot_id: int
    entry_time: str
    exit_time: str = ""         # empty string == still parked
    amount: float = 0.0
    record_id: int = -1

    def is_open(self) -> bool:
        return self.exit_time == ""


@dataclass
class Admin:
    username: str
    password_hash: str
    admin_id: int = -1
