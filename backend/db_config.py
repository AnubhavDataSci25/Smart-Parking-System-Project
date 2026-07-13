"""
Edit these to match your local PostgreSQL setup (see docs/SETUP.md).
In a real deployment these would come from environment variables
instead of being hard-coded — kept simple here for a college project.
"""

import os

HOST = os.environ.get("PARKING_DB_HOST", "localhost")
PORT = os.environ.get("PARKING_DB_PORT", "5432")
DBNAME = os.environ.get("PARKING_DB_NAME", "smart_parking")
USER = os.environ.get("PARKING_DB_USER", "parking_user")
PASSWORD = os.environ.get("PARKING_DB_PASSWORD", "PASSWORD")


def connection_kwargs() -> dict:
    """Returns kwargs ready to pass straight to psycopg2.connect(**kwargs)."""
    return {
        "host": HOST,
        "port": PORT,
        "dbname": DBNAME,
        "user": USER,
        "password": PASSWORD,
    }
