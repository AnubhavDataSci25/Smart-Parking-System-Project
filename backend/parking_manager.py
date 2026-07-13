"""
ParkingManager — this is where the "parking allocation algorithm" and
billing rules live. It ties together an IParkingStore (source of truth:
either the real PostgreSQL Database, or MockParkingStore for testing)
and the 4 in-memory data structures:

  Entry -> HashMap (register/find vehicle) + pick a slot (allocation
           algorithm) -> LinkedList (track as parked) or Queue (if full)
           -> Stack (log the action)
  Exit  -> LinkedList (remove) -> bill via the store -> Stack (log) ->
           if the Queue has someone waiting for that slot type, they are
           AUTOMATICALLY promoted into the freshly-freed slot.

This auto-promotion on exit is the main "algorithm" piece: it's what
makes the waiting queue actually useful instead of just a holding pen.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models import Vehicle
from i_parking_store import IParkingStore
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack, HistoryAction
from hash_map import VehicleHashMap


@dataclass
class EntryResult:
    status: str            # "PARKED" | "QUEUED" | "ERROR"
    message: str
    slot_number: str = ""
    queue_position: int = 0


@dataclass
class ExitResult:
    status: str             # "SUCCESS" | "NOT_FOUND" | "ERROR"
    message: str
    amount: float = 0.0
    slot_freed_number: str = ""
    promoted_vehicle_number: str = ""


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ParkingManager:
    def __init__(self, store: IParkingStore, vehicle_index: VehicleHashMap,
                 parked_list: ParkedVehicleList, waiting_line: WaitingQueue, history: HistoryStack):
        self.store = store
        self.vehicle_index = vehicle_index
        self.parked_list = parked_list
        self.waiting_line = waiting_line
        self.history = history

    # ---- Allocation algorithm ----
    @staticmethod
    def preferred_slot_type(vehicle_type: str) -> str:
        """Maps a vehicle type to the slot type it should be parked in.
        Cars/Trucks/Other fall back to 'General' if their ideal type is
        full; Bikes never spill into General (bike slots are physically
        smaller in most real lots, so this mirrors that constraint)."""
        return "Bike" if vehicle_type == "Bike" else "General"

    # ---- Billing ----
    @staticmethod
    def rate_per_hour(vehicle_type: str) -> float:
        """Rate per hour by vehicle type (Rs). Truck costs more, Bike less."""
        return {"Bike": 10.0, "Truck": 40.0}.get(vehicle_type, 20.0)

    def _try_seat_vehicle(self, vehicle_number: str, owner_name: str, vehicle_type: str) -> Optional[str]:
        """Attempts to physically seat a vehicle into a free slot of the
        preferred type (with the General fallback rule). Returns the
        slot_number if successful, else None."""
        wanted_type = self.preferred_slot_type(vehicle_type)
        slot = self.store.find_first_available_slot(wanted_type)

        if slot is None and wanted_type not in ("Bike", "General"):
            slot = self.store.find_first_available_slot("General")

        if slot is None:
            return None

        vehicle = Vehicle(vehicle_number=vehicle_number, owner_name=owner_name, vehicle_type=vehicle_type)
        vehicle_id = self.store.add_or_get_vehicle(vehicle)
        vehicle.vehicle_id = vehicle_id

        record_id = self.store.create_entry_record(vehicle_id, slot.slot_id)
        self.parked_list.insert_front(record_id, vehicle_number, slot.slot_number, _now_string())
        self.vehicle_index.insert(vehicle_number, vehicle)

        return slot.slot_number

    # ---- Vehicle Entry ----
    def vehicle_entry(self, vehicle_number: str, owner_name: str, vehicle_type: str) -> EntryResult:
        if self.parked_list.find_by_vehicle_number(vehicle_number) is not None:
            return EntryResult(status="ERROR", message="This vehicle is already parked.")

        slot_number = self._try_seat_vehicle(vehicle_number, owner_name, vehicle_type)
        if slot_number is not None:
            self.history.push(HistoryAction("ENTRY", vehicle_number, slot_number, _now_string()))
            return EntryResult(status="PARKED", slot_number=slot_number,
                                message=f"Vehicle parked in slot {slot_number}.")

        # Lot (of the relevant type) is full -> join the waiting queue.
        self.vehicle_index.insert(vehicle_number, Vehicle(vehicle_number, owner_name, vehicle_type))
        self.waiting_line.enqueue(vehicle_number, owner_name, vehicle_type, _now_string())
        self.history.push(HistoryAction("QUEUED", vehicle_number, "-", _now_string()))

        position = self.waiting_line.size()
        return EntryResult(status="QUEUED", queue_position=position,
                            message=f"Lot is full. Added to waiting queue at position {position}.")

    # ---- Vehicle Exit ----
    def vehicle_exit(self, vehicle_number: str) -> ExitResult:
        node = self.parked_list.find_by_vehicle_number(vehicle_number)
        if node is None:
            return ExitResult(status="NOT_FOUND", message="This vehicle is not currently parked.")

        freed_slot_number = node.slot_number
        vehicle = self.vehicle_index.search(vehicle_number)
        vehicle_type = vehicle.vehicle_type if vehicle else "Car"

        amount = self.store.close_exit_record(vehicle_number, self.rate_per_hour(vehicle_type))
        if amount < 0.0:
            return ExitResult(status="ERROR", message="Could not close an open parking record for this vehicle.")

        self.parked_list.remove_by_vehicle_number(vehicle_number)
        self.history.push(HistoryAction("EXIT", vehicle_number, freed_slot_number, _now_string(), amount))

        result = ExitResult(status="SUCCESS", amount=amount, slot_freed_number=freed_slot_number,
                             message=f"Vehicle exited. Amount due: Rs {amount:.2f}")

        # ---- Auto-promotion: give the freed slot to whoever's been
        #      waiting longest for a matching slot type. ----
        if not self.waiting_line.is_empty():
            freed_slot_type = "General"
            for s in self.store.get_all_slots():
                if s.slot_number == freed_slot_number:
                    freed_slot_type = s.slot_type
                    break

            front = self.waiting_line.peek_front()
            if front is not None and self.preferred_slot_type(front.vehicle_type) == freed_slot_type:
                promoted = self.waiting_line.dequeue()
                new_slot = self._try_seat_vehicle(promoted.vehicle_number, promoted.owner_name, promoted.vehicle_type)
                if new_slot is not None:
                    self.history.push(HistoryAction("ENTRY", promoted.vehicle_number, new_slot, _now_string()))
                    result.promoted_vehicle_number = promoted.vehicle_number

        return result

    # ---- Search Vehicle ----
    def search_vehicle(self, vehicle_number: str) -> Optional[Vehicle]:
        return self.vehicle_index.search(vehicle_number)

    # ---- View Parking Status ----
    def print_status(self) -> None:
        print("\n--- Slot Status ---")
        for s in self.store.get_all_slots():
            print(f"  {s.slot_number:<4} [{s.slot_type:<9}] {s.status}")

        print(f"\n--- Currently Parked ({self.parked_list.size()}) ---")
        self.parked_list.display_all()

        print(f"\n--- Waiting Queue ({self.waiting_line.size()}) ---")
        self.waiting_line.display_all()

    # ---- Parking Receipt ("ticket stub" style) ----
    @staticmethod
    def format_receipt(vehicle_number: str, slot_number: str, entry_time: str,
                        exit_time: str, amount: float) -> str:
        return (
            "===============================\n"
            "      SMART PARKING RECEIPT\n"
            "===============================\n"
            f" Vehicle : {vehicle_number}\n"
            f" Slot    : {slot_number}\n"
            f" Entry   : {entry_time}\n"
            f" Exit    : {exit_time}\n"
            "-------------------------------\n"
            f" AMOUNT DUE: Rs {amount:.2f}\n"
            "===============================\n"
            "        Thank you - drive safe!\n"
        )
