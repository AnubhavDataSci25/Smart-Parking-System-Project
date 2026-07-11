# Smart Parking Management System

A full-stack parking management system combining **Python**, **Data
Structures**, **HTML/CSS/Bootstrap**, **JavaScript**, and **PostgreSQL**.

> **Note:** The original project brief suggested C++ and SQLite/MySQL.
> This build uses **Python** (`Flask` + `psycopg2`) and **PostgreSQL** instead.

📄 **Start here:** [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) — full write-up for submission.
🛠️ **Setup:** [`docs/SETUP.md`](docs/SETUP.md) · 🔌 **API reference:** [`docs/API.md`](docs/API.md) · 🏗️ **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Build Stages — all complete ✅
1. **Foundation** — project structure, Git, PostgreSQL schema
2. **Backend Core** — models, DB connection layer, CRUD, data structures
3. **Business Logic + UI** — parking allocation, billing, Bootstrap frontend
4. **Integration + Polish** — REST API wiring, validation, automated tests, reports, docs

## Quick start (no PostgreSQL required)

```bash
pip install -r requirements.txt
python3 backend/demo_datastructures.py     # the 4 data structures, standalone
python3 backend/demo_parking_manager.py    # the allocation algorithm, standalone
python3 -m unittest discover -s backend/tests -v   # 54 automated tests
python3 backend/api.py --mock              # full web app, in-memory data
# open http://localhost:5000
```

## Full setup (with PostgreSQL)

See [`docs/SETUP.md`](docs/SETUP.md) for the complete walkthrough. Short version:

```bash
pip install -r requirements.txt
psql -U parking_user -d smart_parking -h localhost -f database/schema.sql
python3 backend/api.py       # web app: http://localhost:5000
# — or —
python3 backend/main.py      # interactive CLI
```

## Tech Stack
| Layer    | Technology |
|----------|------------|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend  | Python 3, Flask (REST API) |
| Database | PostgreSQL (`psycopg2`) |
| Testing  | `unittest` (54 tests) |
| VCS      | Git & GitHub |

## Project structure

```
SmartParking/
├── backend/
│   ├── models.py                # Vehicle, ParkingSlot, ParkingRecord, Admin
│   ├── security.py               # PBKDF2-HMAC-SHA256 password hashing
│   ├── i_parking_store.py        # abstract interface (dependency inversion)
│   ├── database.py               # real PostgreSQL implementation (psycopg2)
│   ├── mock_parking_store.py     # in-memory implementation — no DB needed
│   ├── db_config.py              # connection settings (env vars supported)
│   ├── linked_list.py            # ParkedVehicleList
│   ├── waiting_queue.py          # WaitingQueue (FIFO)
│   ├── history_stack.py          # HistoryStack (LIFO)
│   ├── hash_map.py               # VehicleHashMap (chaining + auto-resize)
│   ├── parking_manager.py        # allocation algorithm, billing, workflows
│   ├── validation.py             # shared input validation (API + CLI)
│   ├── reports.py                # revenue/occupancy report generation
│   ├── main.py                   # CLI application
│   ├── api.py                    # Flask REST API + static frontend server
│   ├── demo_datastructures.py    # standalone DS demo, no DB needed
│   ├── demo_parking_manager.py   # standalone allocation algorithm demo, no DB needed
│   └── tests/                    # 54 automated tests (unittest)
├── frontend/
│   ├── index.html                # attendant console (entry/exit/search/status)
│   ├── dashboard.html             # admin dashboard (slots/history/reports)
│   ├── css/style.css              # garage/ticket-stub design system
│   └── js/
│       ├── api.js                 # fetch()-based client for the REST API
│       ├── app.js                 # console page rendering + form wiring
│       └── dashboard.js           # dashboard rendering + wiring
├── database/schema.sql            # PostgreSQL schema + seed data
├── docs/
│   ├── SETUP.md                   # environment setup walkthrough
│   ├── API.md                     # REST API reference
│   ├── ARCHITECTURE.md            # design write-up
│   └── PROJECT_REPORT.md          # submission-ready project report
└── requirements.txt
```

## Verified without a database (this environment has no network access)

Everything that doesn't require PostgreSQL has been run and confirmed working:
- All 4 data structures (`demo_datastructures.py`)
- The full allocation algorithm, including auto-promotion (`demo_parking_manager.py`)
- All 54 automated tests (`unittest discover`)
- The entire REST API, live, over real HTTP (`api.py --mock` + `curl`)

`database.py`, `main.py`, and the non-mock path of `api.py` are written
against the standard `psycopg2` API and syntax-checked, but need to be
run against a real PostgreSQL instance on your machine — see
[`docs/SETUP.md`](docs/SETUP.md).
