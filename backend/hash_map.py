"""
VehicleHashMap — a hand-written hash map (separate chaining), mapping
vehicle_number -> Vehicle. This is what makes "Search Vehicle" close to
O(1) instead of scanning the parked-vehicle linked list or hitting the
database on every keystroke.

Deliberately NOT a Python dict — the whole point of this module (mirrors
the README's "Data Structures" requirement) is to implement the hashing
and collision handling by hand. Resizes automatically once the load
factor gets too high, so performance doesn't degrade as more vehicles
are added.
"""

from dataclasses import dataclass
from typing import Optional
from models import Vehicle


@dataclass
class _HashMapNode:
    key: str
    value: Vehicle
    next: Optional["_HashMapNode"] = None


class VehicleHashMap:
    _INITIAL_CAPACITY = 16
    _MAX_LOAD_FACTOR = 0.75

    def __init__(self):
        self._capacity = self._INITIAL_CAPACITY
        self._buckets: list[Optional[_HashMapNode]] = [None] * self._capacity
        self._num_entries = 0

    def _hash(self, key: str) -> int:
        """Polynomial rolling hash (djb2-style) — good spread for
        alphanumeric registration numbers such as 'PB08AB1234'."""
        h = 5381
        for ch in key:
            h = ((h << 5) + h) + ord(ch)  # h * 33 + c
        return h % self._capacity

    def _resize(self) -> None:
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity

        for head in old_buckets:
            current = head
            while current is not None:
                next_node = current.next
                idx = self._hash(current.key)
                current.next = self._buckets[idx]
                self._buckets[idx] = current
                current = next_node

    def insert(self, vehicle_number: str, vehicle: Vehicle) -> None:
        if (self._num_entries + 1) / self._capacity > self._MAX_LOAD_FACTOR:
            self._resize()

        idx = self._hash(vehicle_number)
        current = self._buckets[idx]
        while current is not None:
            if current.key == vehicle_number:
                current.value = vehicle  # update in place
                return
            current = current.next

        node = _HashMapNode(vehicle_number, vehicle, self._buckets[idx])
        self._buckets[idx] = node
        self._num_entries += 1

    def search(self, vehicle_number: str) -> Optional[Vehicle]:
        idx = self._hash(vehicle_number)
        current = self._buckets[idx]
        while current is not None:
            if current.key == vehicle_number:
                return current.value
            current = current.next
        return None

    def remove(self, vehicle_number: str) -> bool:
        idx = self._hash(vehicle_number)
        prev, current = None, self._buckets[idx]
        while current is not None:
            if current.key == vehicle_number:
                if prev is None:
                    self._buckets[idx] = current.next
                else:
                    prev.next = current.next
                self._num_entries -= 1
                return True
            prev, current = current, current.next
        return False

    def contains(self, vehicle_number: str) -> bool:
        return self.search(vehicle_number) is not None

    def size(self) -> int:
        return self._num_entries

    def display_all(self) -> None:
        if self._num_entries == 0:
            print("  (no vehicles registered yet)")
            return
        for head in self._buckets:
            current = head
            while current is not None:
                v = current.value
                print(f"  {current.key} -> {v.owner_name} ({v.vehicle_type})")
                current = current.next
