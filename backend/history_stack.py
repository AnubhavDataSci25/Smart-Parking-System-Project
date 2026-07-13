"""
HistoryStack — a hand-written linked-list-based LIFO stack. Every
entry/exit action gets pushed here as it happens, so:
  1. The Admin "View History" screen can walk the stack most-recent-first.
  2. "Undo last checkout" is just a pop() + reversing that one action —
     exactly the LIFO behaviour a stack is designed for.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HistoryAction:
    action_type: str        # "ENTRY" | "EXIT" | "QUEUED"
    vehicle_number: str
    slot_number: str
    timestamp: str
    amount: float = 0.0     # only meaningful for EXIT actions


@dataclass
class _HistoryStackNode:
    action: HistoryAction
    next: Optional["_HistoryStackNode"] = None


class HistoryStack:
    def __init__(self):
        self._top: Optional[_HistoryStackNode] = None
        self._count = 0

    def push(self, action: HistoryAction) -> None:
        """Record a new action (call after every entry/exit). O(1)."""
        node = _HistoryStackNode(action, self._top)
        self._top = node
        self._count += 1

    def pop(self) -> Optional[HistoryAction]:
        """Remove and return the most recent action (used for undo). O(1)."""
        if self._top is None:
            return None
        node = self._top
        self._top = node.next
        self._count -= 1
        return node.action

    def peek(self) -> Optional[HistoryAction]:
        return self._top.action if self._top is not None else None

    def size(self) -> int:
        return self._count

    def is_empty(self) -> bool:
        return self._top is None

    def display_all(self) -> None:
        """Print the full history, most recent first."""
        if self.is_empty():
            print("  (no history yet)")
            return
        current = self._top
        while current is not None:
            a = current.action
            line = f"  [{a.timestamp}] {a.action_type}  {a.vehicle_number} @ slot {a.slot_number}"
            if a.action_type == "EXIT":
                line += f"  amount: Rs {a.amount:.2f}"
            print(line)
            current = current.next

    def to_list(self, limit: Optional[int] = None) -> list[dict]:
        """Non-destructive snapshot (most recent first) as plain dicts,
        for JSON API responses."""
        result = []
        current = self._top
        while current is not None and (limit is None or len(result) < limit):
            a = current.action
            result.append({
                "action_type": a.action_type,
                "vehicle_number": a.vehicle_number,
                "slot_number": a.slot_number,
                "timestamp": a.timestamp,
                "amount": a.amount,
            })
            current = current.next
        return result
