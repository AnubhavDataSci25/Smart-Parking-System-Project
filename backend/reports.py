"""
reports.py — Admin "Daily Reports" feature (Phase 8 of the original brief).

Builds summary statistics from persisted database history: total revenue,
vehicles serviced, revenue broken down by vehicle type, and current slot
occupancy. Used by both the CLI (main.py) and the REST API (api.py), so
the numbers are always computed the same way regardless of which front
door asked for them.

All values returned are plain str/int/float — safe to json.dumps()
directly (Postgres NUMERIC/TIMESTAMP columns come back as Decimal/
datetime from psycopg2, which the stdlib json module can't serialize).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database


def generate_summary_report(db: "Database", history_limit: int = 200) -> dict:
    history = db.get_history_detailed(limit=history_limit)
    slots = db.get_all_slots()

    total_revenue = 0.0
    revenue_by_type: dict[str, float] = {}
    vehicles_serviced = 0

    for row in history:
        amount = float(row["amount"]) if row["amount"] is not None else 0.0
        total_revenue += amount
        vehicles_serviced += 1
        vtype = row["vehicle_type"]
        revenue_by_type[vtype] = revenue_by_type.get(vtype, 0.0) + amount

    occupied = sum(1 for s in slots if s.status == "Occupied")
    empty = sum(1 for s in slots if s.status == "Empty")
    out_of_service = sum(1 for s in slots if s.status == "OutOfService")

    return {
        "total_revenue": round(total_revenue, 2),
        "vehicles_serviced": vehicles_serviced,
        "revenue_by_type": {k: round(v, 2) for k, v in revenue_by_type.items()},
        "slot_occupancy": {
            "total": len(slots),
            "occupied": occupied,
            "empty": empty,
            "out_of_service": out_of_service,
        },
        "recent_transactions": [
            {
                "vehicle_number": row["vehicle_number"],
                "vehicle_type": row["vehicle_type"],
                "slot_number": row["slot_number"],
                "entry_time": str(row["entry_time"]),
                "exit_time": str(row["exit_time"]),
                "amount": float(row["amount"]) if row["amount"] is not None else 0.0,
            }
            for row in history[:20]
        ],
    }


def print_report(report: dict) -> None:
    """Pretty-print a report dict for the CLI."""
    print("\n========= DAILY REPORT =========")
    print(f" Total Revenue      : Rs {report['total_revenue']:.2f}")
    print(f" Vehicles Serviced  : {report['vehicles_serviced']}")
    print(" Revenue by Type    :")
    if report["revenue_by_type"]:
        for vtype, amount in report["revenue_by_type"].items():
            print(f"   {vtype:<8} Rs {amount:.2f}")
    else:
        print("   (no completed transactions yet)")

    occ = report["slot_occupancy"]
    print(" Slot Occupancy     :")
    print(f"   Total: {occ['total']}  Occupied: {occ['occupied']}  "
          f"Empty: {occ['empty']}  Out of Service: {occ['out_of_service']}")
    print("=================================")
