"""
Integration tests for the Flask REST API (backend/api.py), using
MockParkingStore so no PostgreSQL/psycopg2 is required. This is what
proves Stage 4's "integration" actually works end-to-end: HTTP request
-> Flask route -> ParkingManager -> data structures -> HTTP response.

Run with:
  python3 -m unittest discover -s backend/tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api import create_app
from mock_parking_store import MockParkingStore


class TestApiIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app(store=MockParkingStore())
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_status_lists_10_seed_slots(self):
        r = self.client.get("/api/status")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["slots"]), 10)

    def test_entry_then_search_finds_vehicle(self):
        r = self.client.post("/api/entry", json={
            "vehicle_number": "PB08AB1234", "owner_name": "Aman Sharma", "vehicle_type": "Car",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "PARKED")

        r = self.client.get("/api/search/PB08AB1234")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["found"])
        self.assertTrue(body["currently_parked"])

    def test_entry_rejects_invalid_vehicle_number(self):
        r = self.client.post("/api/entry", json={
            "vehicle_number": "??", "owner_name": "Bad Plate", "vehicle_type": "Car",
        })
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.get_json())

    def test_full_lot_then_overflow_then_promotion(self):
        for i in range(6):
            r = self.client.post("/api/entry", json={
                "vehicle_number": f"CAR00{i}", "owner_name": "Owner", "vehicle_type": "Car",
            })
            self.assertEqual(r.get_json()["status"], "PARKED")

        r = self.client.post("/api/entry", json={
            "vehicle_number": "CAR007", "owner_name": "Waiting", "vehicle_type": "Car",
        })
        self.assertEqual(r.get_json()["status"], "QUEUED")

        r = self.client.post("/api/exit", json={"vehicle_number": "CAR000"})
        body = r.get_json()
        self.assertEqual(body["status"], "SUCCESS")
        self.assertEqual(body["promoted_vehicle_number"], "CAR007")

    def test_exit_unparked_vehicle_returns_404(self):
        r = self.client.post("/api/exit", json={"vehicle_number": "GHOST999"})
        self.assertEqual(r.status_code, 404)

    def test_search_unknown_vehicle_returns_404(self):
        r = self.client.get("/api/search/GHOST999")
        self.assertEqual(r.status_code, 404)
        self.assertFalse(r.get_json()["found"])

    def test_admin_login_unsupported_on_mock_store(self):
        r = self.client.post("/api/admin/login", json={"username": "admin", "password": "x"})
        self.assertEqual(r.status_code, 501)  # mock store has no admin table

    def test_slot_update_rejects_invalid_status(self):
        r = self.client.patch("/api/slots/A1", json={"status": "Banana"})
        self.assertEqual(r.status_code, 400)

    def test_slot_update_rejects_occupied_slot(self):
        self.client.post("/api/entry", json={
            "vehicle_number": "CAR001", "owner_name": "Owner", "vehicle_type": "Car",
        })
        r = self.client.patch("/api/slots/A1", json={"status": "OutOfService"})
        self.assertEqual(r.status_code, 409)  # can't override an occupied slot

    def test_static_frontend_served(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        r.close()
        r = self.client.get("/js/app.js")
        self.assertEqual(r.status_code, 200)
        r.close()


if __name__ == "__main__":
    unittest.main()
