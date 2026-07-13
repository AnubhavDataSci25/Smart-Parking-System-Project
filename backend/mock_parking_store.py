"""
MockParkingStore — a pure in-memory stand-in for Database, implementing
IParkingStore. Lets ParkingManager's allocation algorithm, fallback
rules, and auto-promotion logic be exercised and tested with zero
external dependencies (no PostgreSQL, no psycopg2) — useful for quick
local testing and for the project demo/viva.
"""

from copy import deepcopy
from typing import Optional
from models import Vehicle, ParkingSlot
from i_parking_store import IParkingStore

_SEED_SLOTS = [
    ("A1", "General"), ("A2", "General"), ("A3", "General"),
    ("A4", "General"), ("A5", "General"), ("A6", "General"),
    ("B1", "Bike"), ("B2", "Bike"),
    ("C1", "Handicap"), ("C2", "EV"),
]


class MockParkingStore(IParkingStore):
    def __init__(self):
        self._next_vehicle_id = 1
        self._next_slot_id = 1
        self._next_record_id = 1

        self._vehicles: dict[str, Vehicle] = {}       # vehicle_number -> Vehicle
        self._slots: list[ParkingSlot] = []
        for number, slot_type in _SEED_SLOTS:
            slot = ParkingSlot(slot_number=number, slot_type=slot_type, status="Empty", slot_id=self._next_slot_id)
            self._next_slot_id += 1
            self._slots.append(slot)

        self._open_records: dict[int, int] = {}  # vehicle_id -> slot_id

    def add_or_get_vehicle(self, vehicle: Vehicle) -> int:
        existing = self._vehicles.get(vehicle.vehicle_number)
        if existing is not None:
            return existing.vehicle_id

        v = deepcopy(vehicle)
        v.vehicle_id = self._next_vehicle_id
        self._next_vehicle_id += 1
        self._vehicles[v.vehicle_number] = v
        return v.vehicle_id

    def find_first_available_slot(self, slot_type: str) -> Optional[ParkingSlot]:
        for s in self._slots:
            if s.slot_type == slot_type and s.status == "Empty":
                return deepcopy(s)
        return None

    def create_entry_record(self, vehicle_id: int, slot_id: int) -> int:
        for s in self._slots:
            if s.slot_id == slot_id:
                s.status = "Occupied"
        record_id = self._next_record_id
        self._next_record_id += 1
        self._open_records[vehicle_id] = slot_id
        return record_id

    def close_exit_record(self, vehicle_number: str, rate_per_hour: float) -> float:
        vehicle = self._vehicles.get(vehicle_number)
        if vehicle is None or vehicle.vehicle_id not in self._open_records:
            return -1.0

        slot_id = self._open_records.pop(vehicle.vehicle_id)
        for s in self._slots:
            if s.slot_id == slot_id:
                s.status = "Empty"

        # Flat 1-hour charge for this mock (no real elapsed time to measure).
        return rate_per_hour * 1.0

    def get_all_slots(self) -> list[ParkingSlot]:
        return deepcopy(self._slots)
