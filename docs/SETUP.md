# Environment Setup

You'll need **Python 3.10+**, a running **PostgreSQL server**, and the
**psycopg2** Python package to run the backend from Stage 2 onward.

## 1. Check Python

```bash
python3 --version
```
Needs to be 3.10 or newer (the code uses `list[...]` generic type hints).

## 2. Install PostgreSQL server + client

**Ubuntu / Debian / WSL:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Windows:**
- Download the installer from https://www.postgresql.org/download/windows/
  (this also installs `psql` and `pgAdmin`).

## 3. Create a virtual environment and install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

This installs `psycopg2-binary` (PostgreSQL driver) and `Flask` (the web
server that powers the REST API and serves the frontend).

## 4. Create the database and user

```bash
sudo -u postgres psql
```
Inside the `psql` prompt:
```sql
CREATE DATABASE smart_parking;
CREATE USER parking_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE smart_parking TO parking_user;
\q
```

## 5. Build the schema

From the project root:
```bash
psql -U parking_user -d smart_parking -h localhost -f database/schema.sql
```

This creates all 4 tables, indexes, and seed data (10 parking slots +
1 default admin).

## 6. Configure the connection

Edit `backend/db_config.py` if your credentials differ from the
defaults, or set environment variables instead:
```bash
export PARKING_DB_HOST=localhost
export PARKING_DB_PORT=5432
export PARKING_DB_NAME=smart_parking
export PARKING_DB_USER=parking_user
export PARKING_DB_PASSWORD=yourpassword
```

## 7. Run it

```bash
# Data structures only — no DB needed, works immediately:
python3 backend/demo_datastructures.py

# Allocation algorithm test — no DB needed (uses a mock store):
python3 backend/demo_parking_manager.py

# Automated test suite (54 tests) — no DB needed:
python3 -m unittest discover -s backend/tests -v

# CLI application — needs PostgreSQL running and configured:
python3 backend/main.py

# Web app (frontend + REST API together) — needs PostgreSQL:
python3 backend/api.py
# then open http://localhost:5000 in a browser

# Web app with NO database at all (in-memory mock data, resets on restart):
python3 backend/api.py --mock
# then open http://localhost:5000 in a browser
```

`backend/api.py` serves the frontend (`frontend/index.html`, `dashboard.html`,
etc.) as static files AND the `/api/...` endpoints from the same Flask
process, on the same origin — so there's no CORS configuration to worry
about. Opening `frontend/index.html` directly from disk (double-clicking
it) will NOT work, since the page's `fetch()` calls need a real server
behind them; always go through `http://localhost:5000`.

---

> **Why can't Claude run PostgreSQL or install psycopg2 for you right now?**
> Claude's sandbox has no network access, so it can't download or start
> a PostgreSQL server or install `psycopg2-binary` here. Everything that
> doesn't need a real database (`demo_datastructures.py`,
> `demo_parking_manager.py`, the full 54-test automated suite, and
> `backend/api.py --mock`) has already been run and verified in that
> sandbox — including live HTTP requests against the running Flask
> server. `database.py` and the non-mock path of `main.py`/`api.py` are
> written against the standard, documented `psycopg2` API and have been
> syntax-checked, but you'll need to run them against your own Postgres
> instance following the steps above — let me know if anything errors
> and I'll fix it immediately.
