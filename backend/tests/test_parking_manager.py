"""
Unit tests for ParkingManager (the allocation algorithm + billing rules),
using MockParkingStore so no database is required. Run with:
  python3 -m unittest discover -s backend/tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mock_parking_store import MockParkingStore
from parking_manager import ParkingManager
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack
from hash_map import VehicleHashMap


def make_manager():
    store = MockParkingStore()
    vehicle_index = VehicleHashMap()
    parked_list = ParkedVehicleList()
    waiting_line = WaitingQueue()
    history = HistoryStack()
    manager = ParkingManager(store, vehicle_index, parked_list, waiting_line, history)
    return manager, store, vehicle_index, parked_list, waiting_line, history


class TestVehicleEntry(unittest.TestCase):
    def test_parks_in_first_available_general_slot(self):
        manager, *_ = make_manager()
        r = manager.vehicle_entry("CAR001", "Owner", "Car")
        self.assertEqual(r.status, "PARKED")
        self.assertEqual(r.slot_number, "A1")

    def test_bike_goes_to_bike_slot(self):
        manager, *_ = make_manager()
        r = manager.vehicle_entry("BIKE001", "Owner", "Bike")
        self.assertEqual(r.status, "PARKED")
        self.assertEqual(r.slot_number, "B1")

    def test_duplicate_entry_rejected(self):
        manager, *_ = make_manager()
        manager.vehicle_entry("CAR001", "Owner", "Car")
        r = manager.vehicle_entry("CAR001", "Owner", "Car")
        self.assertEqual(r.status, "ERROR")

    def test_general_full_queues_new_arrival(self):
        manager, *_ = make_manager()
        for i in range(6):  # fills all 6 General slots
            manager.vehicle_entry(f"CAR{i}", "Owner", "Car")
        r = manager.vehicle_entry("OVERFLOW", "Owner", "Car")
        self.assertEqual(r.status, "QUEUED")
        self.assertEqual(r.queue_position, 1)

    def test_bike_never_spills_into_general(self):
        manager, store, *_ = make_manager()
        # Fill both Bike slots.
        manager.vehicle_entry("BIKE001", "Owner", "Bike")
        manager.vehicle_entry("BIKE002", "Owner", "Bike")
        # General slots are still wide open, but a 3rd bike must NOT take one.
        r = manager.vehicle_entry("BIKE003", "Owner", "Bike")
        self.assertEqual(r.status, "QUEUED")


class TestVehicleExit(unittest.TestCase):
    def test_exit_unparked_vehicle_fails_cleanly(self):
        manager, *_ = make_manager()
        r = manager.vehicle_exit("GHOST")
        self.assertEqual(r.status, "NOT_FOUND")

    def test_exit_bills_correct_rate_by_type(self):
        manager, *_ = make_manager()
        manager.vehicle_entry("BIKE001", "Owner", "Bike")
        r = manager.vehicle_exit("BIKE001")
        self.assertEqual(r.status, "SUCCESS")
        self.assertAlmostEqual(r.amount, ParkingManager.rate_per_hour("Bike"))  # mock = flat 1 hr

    def test_exit_frees_the_slot(self):
        manager, store, *_ = make_manager()
        manager.vehicle_entry("CAR001", "Owner", "Car")
        manager.vehicle_exit("CAR001")
        slot_a1 = next(s for s in store.get_all_slots() if s.slot_number == "A1")
        self.assertEqual(slot_a1.status, "Empty")

    def test_auto_promotion_on_exit(self):
        manager, store, vehicle_index, parked_list, waiting_line, history = make_manager()
        for i in range(6):
            manager.vehicle_entry(f"CAR{i}", "Owner", "Car")
        manager.vehicle_entry("WAITING1", "Waiting Owner", "Car")  # queued

        r = manager.vehicle_exit("CAR0")
        self.assertEqual(r.status, "SUCCESS")
        self.assertEqual(r.promoted_vehicle_number, "WAITING1")
        self.assertIsNotNone(parked_list.find_by_vehicle_number("WAITING1"))
        self.assertTrue(waiting_line.is_empty())

    def test_no_promotion_when_type_mismatch(self):
        """A freed Bike slot should NOT be given to a Car waiting in the queue."""
        manager, store, vehicle_index, parked_list, waiting_line, history = make_manager()
        manager.vehicle_entry("BIKE001", "Owner", "Bike")
        manager.vehicle_entry("BIKE002", "Owner", "Bike")  # fills both bike slots
        manager.vehicle_entry("BIKE003", "Owner", "Bike")  # queued (bike doesn't spill to General)

        # Fill General fully too, then queue a car.
        for i in range(6):
            manager.vehicle_entry(f"CAR{i}", "Owner", "Car")

        # Exiting a Car frees a General slot; front of queue is BIKE003 (queued first),
        # whose preferred type is Bike, not General -> should NOT be promoted.
        r = manager.vehicle_exit("CAR0")
        self.assertEqual(r.promoted_vehicle_number, "")


class TestBillingRates(unittest.TestCase):
    def test_rates_by_type(self):
        self.assertEqual(ParkingManager.rate_per_hour("Bike"), 10.0)
        self.assertEqual(ParkingManager.rate_per_hour("Car"), 20.0)
        self.assertEqual(ParkingManager.rate_per_hour("Truck"), 40.0)
        self.assertEqual(ParkingManager.rate_per_hour("Other"), 20.0)
        self.assertEqual(ParkingManager.rate_per_hour("UnknownType"), 20.0)  # safe default


class TestSearchVehicle(unittest.TestCase):
    def test_search_finds_parked_vehicle(self):
        manager, *_ = make_manager()
        manager.vehicle_entry("CAR001", "Owner", "Car")
        found = manager.search_vehicle("CAR001")
        self.assertIsNotNone(found)
        self.assertEqual(found.owner_name, "Owner")

    def test_search_missing_returns_none(self):
        manager, *_ = make_manager()
        self.assertIsNone(manager.search_vehicle("GHOST"))


if __name__ == "__main__":
    unittest.main()
