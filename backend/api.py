"""
api.py — Stage 4 integration layer.

Serves the frontend (frontend/) as static files AND exposes a small REST
API backed by the real ParkingManager + PostgreSQL, so the frontend that
used to talk to localStorage now talks to the real backend instead — same
origin, so no CORS configuration is needed.

Run:  python3 backend/api.py
Then open http://localhost:5000 in a browser.

Requires PostgreSQL + psycopg2 configured (see docs/SETUP.md). For a
version that runs with zero setup (in-memory mock data, no DB), run:
  python3 backend/api.py --mock
"""

import sys
import os
from dataclasses import asdict

from flask import Flask, jsonify, request, send_from_directory

from db_config import connection_kwargs
from mock_parking_store import MockParkingStore
from linked_list import ParkedVehicleList
from waiting_queue import WaitingQueue
from history_stack import HistoryStack
from hash_map import VehicleHashMap
from parking_manager import ParkingManager
from validation import validate_entry_payload, validate_vehicle_number
from reports import generate_summary_report

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def create_app(store=None):
    """
    App factory. If `store` isn't provided, connects to real PostgreSQL.
    Passing a MockParkingStore (or any IParkingStore) here — as the
    automated tests do — lets the whole API be exercised with no
    database at all.
    """
    app = Flask(__name__, static_folder=None)

    if store is None:
        from database import Database  # deferred: only needs psycopg2 when actually used
        store = Database(connection_kwargs())

    vehicle_index = VehicleHashMap()
    parked_list = ParkedVehicleList()
    waiting_line = WaitingQueue()
    history = HistoryStack()
    manager = ParkingManager(store, vehicle_index, parked_list, waiting_line, history)

    # Warm the hash map with vehicles already on file (real DB only —
    # MockParkingStore starts empty, which is fine for tests).
    if hasattr(store, "get_all_vehicles"):
        for v in store.get_all_vehicles():
            vehicle_index.insert(v.vehicle_number, v)

    app.config["MANAGER"] = manager
    app.config["STORE"] = store
    app.config["PARKED_LIST"] = parked_list
    app.config["WAITING_LINE"] = waiting_line
    app.config["HISTORY"] = history

    # ---------------- Static frontend ----------------
    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    # ---------------- API: health ----------------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------------- API: status / slots ----------------
    @app.get("/api/status")
    def status():
        slots = [asdict(s) for s in manager.store.get_all_slots()]
        return jsonify({
            "slots": slots,
            "parked": parked_list.to_list(),
            "waiting": waiting_line.to_list(),
            "parked_count": parked_list.size(),
            "waiting_count": waiting_line.size(),
        })

    @app.patch("/api/slots/<slot_number>")
    def update_slot(slot_number):
        body = request.get_json(silent=True) or {}
        new_status = body.get("status")
        if new_status not in ("Empty", "OutOfService"):
            return jsonify({"error": "status must be 'Empty' or 'OutOfService'"}), 400

        target = next((s for s in manager.store.get_all_slots() if s.slot_number == slot_number), None)
        if target is None:
            return jsonify({"error": f"No such slot: {slot_number}"}), 404
        if target.status == "Occupied":
            return jsonify({"error": "Cannot change status of an occupied slot."}), 409

        if hasattr(manager.store, "update_slot_status"):
            manager.store.update_slot_status(target.slot_id, new_status)
            return jsonify({"slot_number": slot_number, "status": new_status})
        return jsonify({"error": "This store does not support manual slot updates."}), 501

    # ---------------- API: entry / exit / search ----------------
    @app.post("/api/entry")
    def entry():
        body = request.get_json(silent=True) or {}
        vehicle_number = (body.get("vehicle_number") or "").strip().upper()
        owner_name = (body.get("owner_name") or "").strip()
        vehicle_type = (body.get("vehicle_type") or "").strip().title()

        ok, error = validate_entry_payload(vehicle_number, owner_name, vehicle_type)
        if not ok:
            return jsonify({"error": error}), 400

        result = manager.vehicle_entry(vehicle_number, owner_name, vehicle_type)
        status_code = 200 if result.status in ("PARKED", "QUEUED") else 409
        return jsonify(asdict(result)), status_code

    @app.post("/api/exit")
    def exit_vehicle():
        body = request.get_json(silent=True) or {}
        vehicle_number = (body.get("vehicle_number") or "").strip().upper()

        ok, error = validate_vehicle_number(vehicle_number)
        if not ok:
            return jsonify({"error": error}), 400

        result = manager.vehicle_exit(vehicle_number)
        status_code = 200 if result.status == "SUCCESS" else 404
        return jsonify(asdict(result)), status_code

    @app.get("/api/search/<vehicle_number>")
    def search(vehicle_number):
        vehicle_number = vehicle_number.strip().upper()
        ok, error = validate_vehicle_number(vehicle_number)
        if not ok:
            return jsonify({"error": error}), 400

        v = manager.search_vehicle(vehicle_number)
        if v is None:
            return jsonify({"found": False}), 404

        parked = parked_list.find_by_vehicle_number(vehicle_number)
        return jsonify({
            "found": True,
            "vehicle": asdict(v),
            "currently_parked": parked is not None,
            "slot_number": parked.slot_number if parked else None,
            "entry_time": parked.entry_time if parked else None,
        })

    # ---------------- API: history / reports ----------------
    @app.get("/api/history")
    def get_history():
        limit = request.args.get("limit", default=50, type=int)
        return jsonify(history.to_list(limit=limit))

    @app.get("/api/report")
    def get_report():
        if not hasattr(manager.store, "get_history_detailed"):
            return jsonify({"error": "Reports require the real database (not the mock store)."}), 501
        return jsonify(generate_summary_report(manager.store))

    # ---------------- API: admin login ----------------
    @app.post("/api/admin/login")
    def admin_login():
        body = request.get_json(silent=True) or {}
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""

        if not hasattr(manager.store, "verify_admin_login"):
            return jsonify({"error": "Admin login requires the real database."}), 501

        ok = manager.store.verify_admin_login(username, password)
        if not ok:
            return jsonify({"error": "Invalid username or password."}), 401
        return jsonify({"status": "ok", "username": username})

    return app


if __name__ == "__main__":
    use_mock = "--mock" in sys.argv
    app = create_app(store=MockParkingStore() if use_mock else None)
    if use_mock:
        print("Running with an in-memory MOCK store (no PostgreSQL needed, data resets on restart).")
    app.run(host="0.0.0.0", port=5000, debug=True)
