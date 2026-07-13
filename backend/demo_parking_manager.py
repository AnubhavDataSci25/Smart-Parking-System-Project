"""
demo_parking_manager.py
Exercises the FULL allocation algorithm — fallback rules, queueing when
full, and auto-promotion on exit — using MockParkingStore, so it needs
NO PostgreSQL/psycopg2 to run.

Run: python3 backend/demo_parking_manager.py
"""

from mock_parking_store import MockParkingStore
from parking_manager import ParkingManager, EntryResult, ExitResult
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack
from hash_map import VehicleHashMap


def main():
    print("=== Parking Manager / Allocation Algorithm Demo (mock store, no DB) ===\n")

    store = MockParkingStore()
    vehicle_index = VehicleHashMap()
    parked_list = ParkedVehicleList()
    waiting_line = WaitingQueue()
    history = HistoryStack()
    manager = ParkingManager(store, vehicle_index, parked_list, waiting_line, history)

    # --- Fill all 6 General slots with cars ---
    print("-- Filling all 6 General slots --")
    plates = ["CAR001", "CAR002", "CAR003", "CAR004", "CAR005", "CAR006"]
    for plate in plates:
        r = manager.vehicle_entry(plate, "Owner", "Car")
        print(f"{plate} -> {r.message}")
        assert r.status == "PARKED"

    # --- 7th car should be queued (General is full) ---
    print("\n-- 7th car arrives (lot full) --")
    overflow = manager.vehicle_entry("CAR007", "Waiting Owner", "Car")
    print(f"CAR007 -> {overflow.message}")
    assert overflow.status == "QUEUED"
    assert overflow.queue_position == 1

    # --- A bike should NOT spill into General; Bike slots still free ---
    print("\n-- A bike arrives (Bike slots still free) --")
    bike = manager.vehicle_entry("BIKE001", "Biker", "Bike")
    print(f"BIKE001 -> {bike.message}")
    assert bike.status == "PARKED"
    assert bike.slot_number == "B1"  # first free bike slot

    # --- CAR001 exits -> its General slot should be auto-given to CAR007 ---
    print("\n-- CAR001 exits (should auto-promote CAR007 from queue) --")
    exit1 = manager.vehicle_exit("CAR001")
    print(f"CAR001 -> {exit1.message}")
    assert exit1.status == "SUCCESS"
    assert exit1.promoted_vehicle_number == "CAR007"
    print(f"Promoted vehicle: {exit1.promoted_vehicle_number}")

    # --- Search should find CAR007 now marked as parked ---
    found = manager.search_vehicle("CAR007")
    assert found is not None
    print(f"\nSearch CAR007 -> {found.owner_name} ({found.vehicle_type})")
    assert parked_list.find_by_vehicle_number("CAR007") is not None

    # --- Exiting a vehicle that was never parked should fail cleanly ---
    bad_exit = manager.vehicle_exit("GHOST999")
    assert bad_exit.status == "NOT_FOUND"
    print(f"\nExit GHOST999 (never parked) -> {bad_exit.message} (correctly rejected)")

    manager.print_status()

    print("\n=== All allocation algorithm assertions passed ===")


if __name__ == "__main__":
    main()
