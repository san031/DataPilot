"""
load.py — Step 1.9: create the tables and insert the records into SQLite.
"""

import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

# Parents before children, so every foreign key points at a row that exists.
LOAD_ORDER = [
    "categories", "products",
    "warehouses", "inventory",
    "customers",
    "orders", "order_items", "payments", "shipments", "returns",
]


def load(db_path: Path, data: dict) -> None:
    """Build a fresh database at db_path from {table: [rows]}."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()                        # fresh build every run

    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        con.execute("PRAGMA foreign_keys = ON")
        for table in LOAD_ORDER:
            rows = data[table]
            placeholders = ",".join("?" * len(rows[0]))
            con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        con.commit()
    finally:
        con.close()