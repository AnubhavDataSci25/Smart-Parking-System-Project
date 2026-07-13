"""
IParkingStore — the subset of persistence operations ParkingManager
actually needs, as an abstract base class.

Database (real PostgreSQL, via psycopg2) implements this interface, and
so does MockParkingStore (pure in-memory, no DB required) — which is
what lets the allocation algorithm be tested in an environment without
PostgreSQL/psycopg2 installed.
"""

from abc import ABC, abstractmethod
from typing import Optional
from models import Vehicle, ParkingSlot


class IParkingStore(ABC):
    @abstractmethod
    def add_or_get_vehicle(self, vehicle: Vehicle) -> int:
        """Insert if new, or return the existing vehicle_id."""
        raise NotImplementedError

    @abstractmethod
    def find_first_available_slot(self, slot_type: str) -> Optional[ParkingSlot]:
        raise NotImplementedError

    @abstractmethod
    def create_entry_record(self, vehicle_id: int, slot_id: int) -> int:
        """Creates an open record and marks the slot Occupied. Returns record_id."""
        raise NotImplementedError

    @abstractmethod
    def close_exit_record(self, vehicle_number: str, rate_per_hour: float) -> float:
        """Closes the open record for this vehicle, frees the slot, returns
        the billed amount, or -1.0 if no open record existed."""
        raise NotImplementedError

    @abstractmethod
    def get_all_slots(self) -> list[ParkingSlot]:
        raise NotImplementedError
