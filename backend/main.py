"""
Smart Parking Management System — CLI entry point.

Run: python3 backend/main.py
Requires a running PostgreSQL server configured via backend/db_config.py
(or the PARKING_DB_* environment variables). See docs/SETUP.md.
"""

import sys

from database import Database
from db_config import connection_kwargs
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack
from hash_map import VehicleHashMap
from parking_manager import ParkingManager
from validation import validate_entry_payload, validate_vehicle_number
from reports import generate_summary_report, print_report


def print_menu() -> None:
    print(
        "\n========= SMART PARKING MANAGEMENT =========\n"
        " 1. Vehicle Entry\n"
        " 2. Vehicle Exit\n"
        " 3. Search Vehicle\n"
        " 4. View Parking Status\n"
        " 5. View Action History\n"
        " 6. Daily Report\n"
        " 0. Exit Program\n"
        "============================================="
    )


def main() -> int:
    print("=== Smart Parking Management System ===\n")

    try:
        db = Database(connection_kwargs())
    except Exception as e:  # psycopg2.OperationalError etc.
        print(f"Failed to connect to database: {e}", file=sys.stderr)
        print("Check backend/db_config.py and docs/SETUP.md, then try again.", file=sys.stderr)
        return 1

    vehicle_index = VehicleHashMap()
    parked_list = ParkedVehicleList()
    waiting_line = WaitingQueue()
    history = HistoryStack()
    manager = ParkingManager(db, vehicle_index, parked_list, waiting_line, history)

    # Warm the hash map with vehicles already on file.
    for v in db.get_all_vehicles():
        vehicle_index.insert(v.vehicle_number, v)
    print(f"Loaded {vehicle_index.size()} known vehicle(s) from the database.")

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            number = input("Vehicle number: ").strip().upper()
            owner = input("Owner name: ").strip()
            vtype = input("Vehicle type (Car/Bike/Truck/Other): ").strip().title()

            ok, error = validate_entry_payload(number, owner, vtype)
            if not ok:
                print(f"-> Invalid input: {error}")
                continue

            r = manager.vehicle_entry(number, owner, vtype)
            print(f"-> {r.message}")

        elif choice == "2":
            number = input("Vehicle number: ").strip().upper()

            ok, error = validate_vehicle_number(number)
            if not ok:
                print(f"-> Invalid input: {error}")
                continue

            r = manager.vehicle_exit(number)
            print(f"-> {r.message}")
            if r.status == "SUCCESS":
                print(ParkingManager.format_receipt(number, r.slot_freed_number, "-", "-", r.amount))
                if r.promoted_vehicle_number:
                    print(f"(Slot {r.slot_freed_number} automatically given to "
                          f"{r.promoted_vehicle_number} from the waiting queue.)")

        elif choice == "3":
            number = input("Vehicle number: ").strip().upper()

            ok, error = validate_vehicle_number(number)
            if not ok:
                print(f"-> Invalid input: {error}")
                continue

            v = manager.search_vehicle(number)
            if v is not None:
                print(f"-> Found: {v.owner_name} ({v.vehicle_type})")
                if parked_list.find_by_vehicle_number(number) is not None:
                    print("   Currently parked.")
                else:
                    print("   Not currently parked.")
            else:
                print("-> No vehicle found with that number.")

        elif choice == "4":
            manager.print_status()

        elif choice == "5":
            print("\n--- Action History (most recent first) ---")
            history.display_all()

        elif choice == "6":
            report = generate_summary_report(db)
            print_report(report)

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option, try again.")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
