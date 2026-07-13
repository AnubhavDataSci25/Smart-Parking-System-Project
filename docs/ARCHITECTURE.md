# Architecture

## Layers

```
frontend/ (HTML + Bootstrap + JS)
      │  fetch() — same-origin, no CORS
      ▼
backend/api.py (Flask)        ─┐
backend/main.py (CLI)         ─┤  both call into the same business logic
      │                        │
      ▼                        │
backend/parking_manager.py ────┘   allocation algorithm, billing, entry/exit workflows
      │
      ├──► backend/hash_map.py, linked_list.py, waiting_queue.py, history_stack.py
      │      (in-memory, hand-written data structures — fast runtime access)
      │
      └──► backend/i_parking_store.py  (abstract interface)
                 ▲                  ▲
                 │                  │
        backend/database.py   backend/mock_parking_store.py
        (real PostgreSQL,      (pure in-memory, no DB —
         via psycopg2)          used for tests / --mock mode)
```

## Why an interface between ParkingManager and the database?

`ParkingManager` depends on `IParkingStore` (an abstract base class), not
directly on `Database`. `Database` (PostgreSQL/psycopg2) and
`MockParkingStore` (plain Python dicts/lists) both implement that same
interface. This is what let the entire allocation algorithm — slot
matching, fallback rules, FIFO queueing, auto-promotion — be built,
tested, and debugged **without ever needing a running PostgreSQL server**,
and it's why the automated test suite (54 tests) runs in under a tenth of
a second with zero external dependencies.

The real `Database` class is still exactly as "real" as it needs to be:
it does true CRUD against PostgreSQL, computes billing with the
database's own `NOW()` (avoiding clock-drift bugs from doing that in
application code), and is the only thing swapped in for `main.py`/`api.py`
in production.

## Why two front doors (CLI and REST API) to the same logic?

Both `backend/main.py` (interactive CLI) and `backend/api.py` (Flask,
serving the web frontend) construct a `ParkingManager` wired to the same
four data structures and hand it the *same* `Database` instance. Neither
duplicates the allocation/billing rules — they're both just different
ways of calling into `parking_manager.py`. This matches how the original
project brief separated "User" and "Admin" console features from the web
UI, while keeping a single source of truth for the business logic.

## Request flow: parking a vehicle from the web UI

1. Attendant fills the Entry form in `frontend/index.html`, submits.
2. `frontend/js/app.js` calls `vehicleEntry()` in `frontend/js/api.js`,
   which does `POST /api/entry`.
3. `backend/api.py`'s `/api/entry` route validates the payload
   (`backend/validation.py`), then calls
   `manager.vehicle_entry(vehicle_number, owner_name, vehicle_type)`.
4. `ParkingManager` (`backend/parking_manager.py`) works out the
   preferred slot type, asks the store (`Database`, hitting Postgres) for
   the first available slot of that type, and either seats the vehicle
   or queues it.
5. On success, the vehicle is recorded in `parked_list` (linked list),
   `vehicle_index` (hash map) for fast future search, and the action is
   pushed onto `history` (stack).
6. The Flask route serializes the `EntryResult` dataclass to JSON and
   returns it.
7. The frontend re-fetches `/api/status` and `/api/history` to refresh
   the slot map, waiting queue, and activity feed.

## In-memory state and multiple processes

The four data structures (`vehicle_index`, `parked_list`, `waiting_line`,
`history`) are created once per running process (in `create_app()` /
`main()`), not persisted to the database. This is intentional and
appropriate for a single-process college project demo: the database
(`parking_records`, `parking_slots`, etc.) is always the source of truth
for what's actually parked, while the in-memory structures exist purely
to make searches and the waiting queue fast without hitting Postgres on
every keystroke. Running multiple `api.py` worker processes (e.g. behind
gunicorn with `--workers > 1`) would give each worker its own queue/
history, which would need a shared store (Redis, or moving the queue
into Postgres) to fix — out of scope for this project, but worth
understanding as a limitation.
