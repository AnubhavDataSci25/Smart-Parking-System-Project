"""
demo_datastructures.py
A standalone demo/test of the 4 data structures with NO database
dependency — runs anywhere with just `python3`.

Run: python3 backend/demo_datastructures.py
"""

from models import Vehicle
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack, HistoryAction
from hash_map import VehicleHashMap


def main():
    print("=== Data Structures Demo (no database needed) ===\n")

    # ---------------- Hash Map ----------------
    print("--- Hash Map: register + search vehicles ---")
    vehicle_index = VehicleHashMap()
    vehicle_index.insert("PB08AB1234", Vehicle("PB08AB1234", "Aman Sharma", "Car"))
    vehicle_index.insert("PB10CD5678", Vehicle("PB10CD5678", "Riya Kapoor", "Bike"))
    vehicle_index.insert("PB65EF9999", Vehicle("PB65EF9999", "Test Fleet", "Truck"))
    vehicle_index.display_all()

    result = vehicle_index.search("PB10CD5678")
    print(f"Search 'PB10CD5678' -> {result.owner_name if result else 'NOT FOUND'}")
    vehicle_index.remove("PB65EF9999")
    print(f"After removing PB65EF9999, size = {vehicle_index.size()}\n")

    # ---------------- Linked List ----------------
    print("--- Linked List: currently parked vehicles ---")
    parked = ParkedVehicleList()
    parked.insert_front(1, "PB08AB1234", "A1", "2026-07-07 09:00:00")
    parked.insert_front(2, "PB10CD5678", "B1", "2026-07-07 09:15:00")
    parked.display_all()
    print(f"Size: {parked.size()}")
    parked.remove_by_vehicle_number("PB08AB1234")
    print("After PB08AB1234 exits:")
    parked.display_all()
    print()

    # ---------------- Queue ----------------
    print("--- Queue: waiting line when lot is full ---")
    waiting = WaitingQueue()
    waiting.enqueue("PB77ZZ1111", "Neha Verma", "Car", "2026-07-07 10:00:00")
    waiting.enqueue("PB77ZZ2222", "Karan Mehta", "Car", "2026-07-07 10:02:00")
    waiting.display_all()

    next_up = waiting.dequeue()
    if next_up:
        print(f"Next slot goes to: {next_up.vehicle_number} ({next_up.owner_name})")
    print(f"Remaining in queue: {waiting.size()}\n")

    # ---------------- Stack ----------------
    print("--- Stack: action history / undo ---")
    history = HistoryStack()
    history.push(HistoryAction("ENTRY", "PB08AB1234", "A1", "2026-07-07 09:00:00"))
    history.push(HistoryAction("ENTRY", "PB10CD5678", "B1", "2026-07-07 09:15:00"))
    history.push(HistoryAction("EXIT", "PB08AB1234", "A1", "2026-07-07 11:00:00", 40.0))
    history.display_all()

    last_action = history.pop()
    if last_action:
        print(f"Undo -> reverting: {last_action.action_type} for {last_action.vehicle_number}")
    print(f"History size after undo: {history.size()}")

    print("\n=== Demo complete: all 4 data structures working correctly ===")


if __name__ == "__main__":
    main()
