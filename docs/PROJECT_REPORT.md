# Smart Parking Management System — Project Report

## Overview

A full-stack parking management system built as a college software
engineering project. It demonstrates object-oriented design, four
hand-implemented data structures, relational database design, a REST
API, a responsive web frontend, and an automated test suite.

**Tech stack:** Python 3 (backend + CLI), Flask (REST API), PostgreSQL
(database, via `psycopg2`), HTML5/CSS3/Bootstrap 5/JavaScript (frontend).

## Objectives (from the original brief) — status

| Objective | Status |
|---|---|
| Practice real-world problem solving in a general-purpose language | ✅ Python |
| Implement core data structures | ✅ Linked List, Queue, Stack, Hash Map (all hand-written) |
| Build a responsive frontend | ✅ Bootstrap 5, custom design system |
| Persistent database storage | ✅ PostgreSQL, 4 tables, seeded schema |
| CRUD operations | ✅ Full CRUD for vehicles, slots, records, admins |
| Modular software design | ✅ Interface-based (`IParkingStore`), dependency inversion |

## Architecture summary

See `docs/ARCHITECTURE.md` for full detail. In short:

- **`parking_manager.py`** holds the allocation algorithm and billing
  rules, and is the single source of truth used by both the CLI
  (`main.py`) and the REST API (`api.py`).
- It depends on an abstract **`IParkingStore`** interface rather than
  PostgreSQL directly, implemented by both the real `Database` class
  (`psycopg2`) and an in-memory `MockParkingStore` — which is what made
  it possible to build and test the entire allocation algorithm without
  ever needing a live database connection.
- Four hand-written data structures back the runtime state: a **linked
  list** of currently parked vehicles, a **FIFO queue** for the waiting
  line, a **LIFO stack** for the action history/undo log, and a **hash
  map with separate chaining and auto-resize** for fast registration-
  number lookup.

## Data structures — design rationale

| Structure | Used for | Why this structure |
|---|---|---|
| Linked List | Currently parked vehicles | Size changes constantly, no random access needed, O(1) insert |
| Queue (FIFO) | Waiting line when lot is full | First-come-first-served fairness is the whole point |
| Stack (LIFO) | Action history / undo | Most recent action is exactly what you'd want to undo first |
| Hash Map (chaining) | Search vehicle by plate number | ~O(1) average lookup instead of scanning a list |

## The allocation algorithm

1. A vehicle's type maps to a **preferred slot type** (`Bike` → `Bike`,
   everything else → `General`).
2. Bikes **never spill into General** slots (mirrors real lots where bike
   bays are physically smaller); Cars/Trucks/Other fall back to General
   if their exact type (e.g. `EV`) happens to be full.
3. If no matching slot is free, the vehicle joins the **waiting queue**.
4. On exit, if the freed slot's type matches the type the front of the
   queue is waiting for, that vehicle is **automatically promoted** into
   the freed slot — the queue isn't just a holding pen, it actually gets
   drained as slots free up.

This is exercised end-to-end by `backend/demo_parking_manager.py` and by
`backend/tests/test_parking_manager.py`.

## Billing

Rates are ₹10/hour (Bike), ₹20/hour (Car/Other), ₹40/hour (Truck).
The real database computes elapsed time and rounds up to the next full
hour using PostgreSQL's own `NOW()` (avoiding clock-drift bugs that can
happen computing durations in application code).

## Security

Admin passwords are hashed with **PBKDF2-HMAC-SHA256** (100,000
iterations, random salt per password) using Python's `hashlib` — no
external dependency needed, and constant-time comparison
(`hmac.compare_digest`) to resist timing attacks.

## Testing

54 automated tests (`python3 -m unittest discover -s backend/tests -v`),
covering:
- All 4 data structures (insertion, removal, FIFO/LIFO ordering, hash
  map resizing under load, edge cases like operating on an empty
  structure)
- The allocation algorithm (slot matching, fallback rules, queueing,
  auto-promotion, duplicate-entry rejection, billing rates)
- Input validation (vehicle number format, owner name format, vehicle
  type whitelist)
- The REST API (11 integration tests using Flask's test client against
  the mock store — health check, full CRUD-style workflows, validation
  error codes, HTTP status codes for conflict/not-found cases)

All 54 tests pass. The full entry → overflow → exit → auto-promotion
workflow was also verified against a **live running Flask server** using
real HTTP requests (`curl`), not just the test client.

## What needs your local machine to verify

This was built and tested in a sandboxed environment with no internet
access, so anything requiring PostgreSQL or installing `psycopg2` could
not be executed directly:
- `database.py` (the real PostgreSQL CRUD layer) — syntax-checked, and
  structurally identical to the `MockParkingStore` implementation that
  *has* been tested, but not run against a live Postgres instance.
- `backend/main.py` and `backend/api.py` in their non-`--mock` mode.
- `/api/report` and `/api/admin/login`, which require real database
  tables.

Everything else — all 4 data structures, the full allocation algorithm,
input validation, and the entire REST API surface (except the two
DB-only endpoints above) — has been run and verified directly.

## Known limitations / possible future enhancements

- In-memory state (waiting queue, history, hash map) is per-process; running
  multiple API workers would need a shared store (see `docs/ARCHITECTURE.md`).
- No authentication/session on the admin dashboard UI yet (the
  `/api/admin/login` endpoint exists but the dashboard doesn't gate access
  behind it).
- QR code entry, online reservation, and analytics dashboards were listed
  as "Future Enhancements" in the original brief and are intentionally
  out of scope here.
- The REST API's in-memory session history (`/api/history`) resets on
  restart; `/api/report` (persisted, DB-backed) is the durable source of
  truth for revenue/occupancy reporting.

## How to run everything

See `docs/SETUP.md` for full setup, `docs/API.md` for the REST API
reference, and `docs/ARCHITECTURE.md` for the design writeup.

```bash
# Zero-setup verification (no PostgreSQL needed):
python3 backend/demo_datastructures.py
python3 backend/demo_parking_manager.py
python3 -m unittest discover -s backend/tests -v
python3 backend/api.py --mock   # then open http://localhost:5000

# Full production setup (needs PostgreSQL — see docs/SETUP.md):
psql -U parking_user -d smart_parking -f database/schema.sql
python3 backend/main.py         # CLI
python3 backend/api.py          # Web app, http://localhost:5000
```
