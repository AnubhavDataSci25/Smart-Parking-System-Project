"""
WaitingQueue — a hand-written linked-list-based FIFO queue. When the lot
is full, new arrivals join this queue; when a slot frees up, whoever's
been waiting longest (front of the queue) gets it first. Classic FIFO
fairness — a real-world "first come, first served" waiting list.

(Named waiting_queue / WaitingQueue, not Queue, to avoid clashing with
Python's own queue module.)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WaitingQueueNode:
    vehicle_number: str
    owner_name: str
    vehicle_type: str
    requested_time: str
    next: Optional["WaitingQueueNode"] = None


class WaitingQueue:
    def __init__(self):
        self._front: Optional[WaitingQueueNode] = None
        self._rear: Optional[WaitingQueueNode] = None
        self._count = 0

    def enqueue(self, vehicle_number: str, owner_name: str, vehicle_type: str, requested_time: str) -> None:
        """Add a vehicle to the back of the line. O(1)."""
        node = WaitingQueueNode(vehicle_number, owner_name, vehicle_type, requested_time)
        if self._rear is None:
            self._front = self._rear = node
        else:
            self._rear.next = node
            self._rear = node
        self._count += 1

    def dequeue(self) -> Optional[WaitingQueueNode]:
        """Remove and return whoever's been waiting longest. O(1). None if empty."""
        if self._front is None:
            return None
        node = self._front
        self._front = self._front.next
        if self._front is None:
            self._rear = None
        self._count -= 1
        node.next = None
        return node

    def peek_front(self) -> Optional[WaitingQueueNode]:
        return self._front

    def size(self) -> int:
        return self._count

    def is_empty(self) -> bool:
        return self._front is None

    def display_all(self) -> None:
        if self.is_empty():
            print("  (no one waiting)")
            return
        position, current = 1, self._front
        while current is not None:
            print(f"  #{position} {current.vehicle_number} ({current.owner_name}) since {current.requested_time}")
            current = current.next
            position += 1

    def to_list(self) -> list[dict]:
        """Non-destructive snapshot as plain dicts, for JSON API responses."""
        result = []
        current = self._front
        while current is not None:
            result.append({
                "vehicle_number": current.vehicle_number,
                "owner_name": current.owner_name,
                "vehicle_type": current.vehicle_type,
                "requested_time": current.requested_time,
            })
            current = current.next
        return result
