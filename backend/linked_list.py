"""
ParkedVehicleList — a hand-written singly linked list tracking every
vehicle CURRENTLY inside the lot (rows in parking_records where
exit_time IS NULL).

Why a linked list here: vehicles enter/exit in no particular order and
the list size changes constantly, so O(1) insertion at the head and no
need for random access is a textbook fit for a linked list (rather than
a Python list/array).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParkedVehicleNode:
    record_id: int
    vehicle_number: str
    slot_number: str
    entry_time: str
    next: Optional["ParkedVehicleNode"] = None


class ParkedVehicleList:
    def __init__(self):
        self._head: Optional[ParkedVehicleNode] = None
        self._count = 0

    def insert_front(self, record_id: int, vehicle_number: str, slot_number: str, entry_time: str) -> None:
        """Insert a newly parked vehicle at the head. O(1)."""
        node = ParkedVehicleNode(record_id, vehicle_number, slot_number, entry_time, self._head)
        self._head = node
        self._count += 1

    def remove_by_vehicle_number(self, vehicle_number: str) -> bool:
        """Remove a vehicle when it exits. Returns True if found and removed. O(n)."""
        prev, current = None, self._head
        while current is not None:
            if current.vehicle_number == vehicle_number:
                if prev is None:
                    self._head = current.next
                else:
                    prev.next = current.next
                self._count -= 1
                return True
            prev, current = current, current.next
        return False

    def find_by_vehicle_number(self, vehicle_number: str) -> Optional[ParkedVehicleNode]:
        """Search for a currently-parked vehicle. Returns None if not found. O(n)."""
        current = self._head
        while current is not None:
            if current.vehicle_number == vehicle_number:
                return current
            current = current.next
        return None

    def size(self) -> int:
        return self._count

    def is_empty(self) -> bool:
        return self._head is None

    def display_all(self) -> None:
        """Print all currently parked vehicles (Admin dashboard / CLI)."""
        if self.is_empty():
            print("  (no vehicles currently parked)")
            return
        current = self._head
        while current is not None:
            print(f"  Slot {current.slot_number} | {current.vehicle_number} | entered: {current.entry_time}")
            current = current.next

    def to_list(self) -> list[dict]:
        """Non-destructive snapshot as plain dicts, for JSON API responses."""
        result = []
        current = self._head
        while current is not None:
            result.append({
                "record_id": current.record_id,
                "vehicle_number": current.vehicle_number,
                "slot_number": current.slot_number,
                "entry_time": current.entry_time,
            })
            current = current.next
        return result
