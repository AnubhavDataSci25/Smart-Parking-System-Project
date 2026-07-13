"""
Database — thin wrapper around a psycopg2 connection giving CRUD access
to the 4 tables defined in database/schema.sql. Every public method
commits before returning, so callers don't need to think about
transaction management for simple operations.

Requires: psycopg2 (or psycopg2-binary) installed locally.
See docs/SETUP.md.
"""

from typing import Optional

import psycopg2
import psycopg2.extras

from models import Vehicle, ParkingSlot, ParkingRecord
from i_parking_store import IParkingStore
from security import hash_password, verify_password


class Database(IParkingStore):
    def __init__(self, connection_kwargs: dict):
        self._conn = psycopg2.connect(**connection_kwargs)
        print(f"Connected to PostgreSQL database: {connection_kwargs.get('dbname')}")

    def is_open(self) -> bool:
        return self._conn is not None and self._conn.closed == 0

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()

    def _dict_cursor(self):
        return self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ---------------- Vehicles ----------------
    def add_or_get_vehicle(self, vehicle: Vehicle) -> int:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT vehicle_id FROM vehicles WHERE vehicle_number = %s",
                (vehicle.vehicle_number,),
            )
            existing = cur.fetchone()
            if existing is not None:
                return existing["vehicle_id"]

            cur.execute(
                "INSERT INTO vehicles (vehicle_number, owner_name, vehicle_type) "
                "VALUES (%s, %s, %s) RETURNING vehicle_id",
                (vehicle.vehicle_number, vehicle.owner_name, vehicle.vehicle_type),
            )
            new_id = cur.fetchone()["vehicle_id"]
            self._conn.commit()
            return new_id

    def find_vehicle_by_number(self, vehicle_number: str) -> Optional[Vehicle]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT vehicle_id, vehicle_number, owner_name, vehicle_type "
                "FROM vehicles WHERE vehicle_number = %s",
                (vehicle_number,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return Vehicle(
                vehicle_number=row["vehicle_number"],
                owner_name=row["owner_name"],
                vehicle_type=row["vehicle_type"],
                vehicle_id=row["vehicle_id"],
            )

    def get_all_vehicles(self) -> list[Vehicle]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT vehicle_id, vehicle_number, owner_name, vehicle_type "
                "FROM vehicles ORDER BY vehicle_id"
            )
            rows = cur.fetchall()
            return [
                Vehicle(
                    vehicle_number=r["vehicle_number"],
                    owner_name=r["owner_name"],
                    vehicle_type=r["vehicle_type"],
                    vehicle_id=r["vehicle_id"],
                )
                for r in rows
            ]

    # ---------------- Parking Slots ----------------
    def get_all_slots(self) -> list[ParkingSlot]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT slot_id, slot_number, slot_type, status "
                "FROM parking_slots ORDER BY slot_number"
            )
            rows = cur.fetchall()
            return [
                ParkingSlot(
                    slot_number=r["slot_number"],
                    slot_type=r["slot_type"],
                    status=r["status"],
                    slot_id=r["slot_id"],
                )
                for r in rows
            ]

    def find_first_available_slot(self, slot_type: str = "General") -> Optional[ParkingSlot]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT slot_id, slot_number, slot_type, status FROM parking_slots "
                "WHERE status = 'Empty' AND slot_type = %s ORDER BY slot_number LIMIT 1",
                (slot_type,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return ParkingSlot(
                slot_number=row["slot_number"],
                slot_type=row["slot_type"],
                status=row["status"],
                slot_id=row["slot_id"],
            )

    def update_slot_status(self, slot_id: int, new_status: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE parking_slots SET status = %s WHERE slot_id = %s",
                (new_status, slot_id),
            )
            affected = cur.rowcount
            self._conn.commit()
            return affected > 0

    # ---------------- Parking Records ----------------
    def create_entry_record(self, vehicle_id: int, slot_id: int) -> int:
        with self._dict_cursor() as cur:
            cur.execute(
                "INSERT INTO parking_records (vehicle_id, slot_id, entry_time) "
                "VALUES (%s, %s, NOW()) RETURNING record_id",
                (vehicle_id, slot_id),
            )
            record_id = cur.fetchone()["record_id"]

            cur.execute(
                "UPDATE parking_slots SET status = 'Occupied' WHERE slot_id = %s",
                (slot_id,),
            )
            self._conn.commit()
            return record_id

    def close_exit_record(self, vehicle_number: str, rate_per_hour: float) -> float:
        with self._dict_cursor() as cur:
            # Find the open record for this vehicle (exit_time IS NULL).
            cur.execute(
                "SELECT pr.record_id, pr.slot_id, pr.entry_time "
                "FROM parking_records pr "
                "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
                "WHERE v.vehicle_number = %s AND pr.exit_time IS NULL "
                "ORDER BY pr.entry_time DESC LIMIT 1",
                (vehicle_number,),
            )
            open_rec = cur.fetchone()
            if open_rec is None:
                self._conn.commit()
                return -1.0  # this vehicle isn't currently parked

            record_id = open_rec["record_id"]
            slot_id = open_rec["slot_id"]

            # Let PostgreSQL compute the duration and bill directly —
            # avoids clock drift/timezone bugs from doing it in Python.
            cur.execute(
                "UPDATE parking_records SET exit_time = NOW(), "
                "amount = ROUND(CEIL(EXTRACT(EPOCH FROM (NOW() - entry_time)) / 3600.0) * %s, 2) "
                "WHERE record_id = %s RETURNING amount",
                (rate_per_hour, record_id),
            )
            amount = float(cur.fetchone()["amount"])

            cur.execute(
                "UPDATE parking_slots SET status = 'Empty' WHERE slot_id = %s",
                (slot_id,),
            )
            self._conn.commit()
            return amount

    def get_open_records(self) -> list[ParkingRecord]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT record_id, vehicle_id, slot_id, entry_time "
                "FROM parking_records WHERE exit_time IS NULL ORDER BY entry_time"
            )
            rows = cur.fetchall()
            return [
                ParkingRecord(
                    record_id=r["record_id"],
                    vehicle_id=r["vehicle_id"],
                    slot_id=r["slot_id"],
                    entry_time=str(r["entry_time"]),
                )
                for r in rows
            ]

    def get_history(self, limit: int = 50) -> list[ParkingRecord]:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT record_id, vehicle_id, slot_id, entry_time, exit_time, amount "
                "FROM parking_records WHERE exit_time IS NOT NULL "
                "ORDER BY exit_time DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                ParkingRecord(
                    record_id=r["record_id"],
                    vehicle_id=r["vehicle_id"],
                    slot_id=r["slot_id"],
                    entry_time=str(r["entry_time"]),
                    exit_time=str(r["exit_time"]),
                    amount=float(r["amount"]) if r["amount"] is not None else 0.0,
                )
                for r in rows
            ]

    def get_history_detailed(self, limit: int = 200) -> list[dict]:
        """Like get_history(), but joined with vehicles/slots for reporting
        (vehicle_number, vehicle_type, slot_number instead of raw ids)."""
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT v.vehicle_number, v.vehicle_type, s.slot_number, "
                "pr.entry_time, pr.exit_time, pr.amount "
                "FROM parking_records pr "
                "JOIN vehicles v ON v.vehicle_id = pr.vehicle_id "
                "JOIN parking_slots s ON s.slot_id = pr.slot_id "
                "WHERE pr.exit_time IS NOT NULL "
                "ORDER BY pr.exit_time DESC LIMIT %s",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ---------------- Admin ----------------
    def verify_admin_login(self, username: str, plain_password: str) -> bool:
        with self._dict_cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM admins WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
            if row is None:
                return False
            return verify_password(plain_password, row["password_hash"])

    def create_admin(self, username: str, plain_password: str) -> bool:
        with self._conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
                    (username, hash_password(plain_password)),
                )
                self._conn.commit()
                return True
            except psycopg2.errors.UniqueViolation:
                self._conn.rollback()
                return False  # username already exists
