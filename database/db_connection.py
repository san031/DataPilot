import sqlite3
from pathlib import Path

DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "ecommerce.db")


def get_connection(read_only=False):
    if read_only:
        # OS-level read-only: writes fail even if a query slips past validation
        conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
