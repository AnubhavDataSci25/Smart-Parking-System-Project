"""
Unit tests for the 4 hand-written data structures. Run with:
  python3 -m unittest discover -s backend/tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack, HistoryAction
from hash_map import VehicleHashMap
from models import Vehicle


class TestParkedVehicleList(unittest.TestCase):
    def test_insert_and_find(self):
        lst = ParkedVehicleList()
        lst.insert_front(1, "CAR001", "A1", "t1")
        lst.insert_front(2, "CAR002", "A2", "t2")
        self.assertEqual(lst.size(), 2)
        node = lst.find_by_vehicle_number("CAR002")
        self.assertIsNotNone(node)
        self.assertEqual(node.slot_number, "A2")

    def test_remove(self):
        lst = ParkedVehicleList()
        lst.insert_front(1, "CAR001", "A1", "t1")
        self.assertTrue(lst.remove_by_vehicle_number("CAR001"))
        self.assertTrue(lst.is_empty())
        self.assertFalse(lst.remove_by_vehicle_number("CAR001"))  # already gone

    def test_find_missing_returns_none(self):
        lst = ParkedVehicleList()
        self.assertIsNone(lst.find_by_vehicle_number("GHOST"))

    def test_to_list_snapshot(self):
        lst = ParkedVehicleList()
        lst.insert_front(1, "CAR001", "A1", "t1")
        snapshot = lst.to_list()
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["vehicle_number"], "CAR001")


class TestWaitingQueue(unittest.TestCase):
    def test_fifo_order(self):
        q = WaitingQueue()
        q.enqueue("A", "Owner A", "Car", "t1")
        q.enqueue("B", "Owner B", "Car", "t2")
        first = q.dequeue()
        second = q.dequeue()
        self.assertEqual(first.vehicle_number, "A")   # first in, first out
        self.assertEqual(second.vehicle_number, "B")
        self.assertTrue(q.is_empty())

    def test_dequeue_empty_returns_none(self):
        q = WaitingQueue()
        self.assertIsNone(q.dequeue())

    def test_peek_does_not_remove(self):
        q = WaitingQueue()
        q.enqueue("A", "Owner", "Car", "t1")
        peeked = q.peek_front()
        self.assertEqual(peeked.vehicle_number, "A")
        self.assertEqual(q.size(), 1)  # still there


class TestHistoryStack(unittest.TestCase):
    def test_lifo_order(self):
        s = HistoryStack()
        s.push(HistoryAction("ENTRY", "A", "A1", "t1"))
        s.push(HistoryAction("EXIT", "A", "A1", "t2", 20.0))
        top = s.pop()
        self.assertEqual(top.action_type, "EXIT")  # last in, first out
        second = s.pop()
        self.assertEqual(second.action_type, "ENTRY")

    def test_pop_empty_returns_none(self):
        s = HistoryStack()
        self.assertIsNone(s.pop())

    def test_to_list_most_recent_first(self):
        s = HistoryStack()
        s.push(HistoryAction("ENTRY", "A", "A1", "t1"))
        s.push(HistoryAction("EXIT", "A", "A1", "t2", 20.0))
        snapshot = s.to_list()
        self.assertEqual(snapshot[0]["action_type"], "EXIT")
        self.assertEqual(snapshot[1]["action_type"], "ENTRY")


class TestVehicleHashMap(unittest.TestCase):
    def test_insert_and_search(self):
        hm = VehicleHashMap()
        hm.insert("CAR001", Vehicle("CAR001", "Owner", "Car"))
        found = hm.search("CAR001")
        self.assertIsNotNone(found)
        self.assertEqual(found.owner_name, "Owner")

    def test_search_missing_returns_none(self):
        hm = VehicleHashMap()
        self.assertIsNone(hm.search("GHOST"))

    def test_update_in_place(self):
        hm = VehicleHashMap()
        hm.insert("CAR001", Vehicle("CAR001", "Old Owner", "Car"))
        hm.insert("CAR001", Vehicle("CAR001", "New Owner", "Car"))
        self.assertEqual(hm.size(), 1)  # not duplicated
        self.assertEqual(hm.search("CAR001").owner_name, "New Owner")

    def test_remove(self):
        hm = VehicleHashMap()
        hm.insert("CAR001", Vehicle("CAR001", "Owner", "Car"))
        self.assertTrue(hm.remove("CAR001"))
        self.assertIsNone(hm.search("CAR001"))
        self.assertFalse(hm.remove("CAR001"))  # already gone

    def test_resize_preserves_all_entries(self):
        hm = VehicleHashMap()
        # Insert enough entries to force at least one resize
        # (initial capacity 16, max load factor 0.75 -> resizes after ~12).
        for i in range(50):
            hm.insert(f"CAR{i:03d}", Vehicle(f"CAR{i:03d}", f"Owner {i}", "Car"))

        self.assertEqual(hm.size(), 50)
        for i in range(50):
            found = hm.search(f"CAR{i:03d}")
            self.assertIsNotNone(found, f"CAR{i:03d} lost after resize")
            self.assertEqual(found.owner_name, f"Owner {i}")


if __name__ == "__main__":
    unittest.main()
