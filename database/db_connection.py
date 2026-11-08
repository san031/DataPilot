
import sqlite3
from pathlib import Path

# Locate project root using this file's location.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database location relative to project root.
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.db"


def get_connection(read_only=False):

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            "Ensure ecommerce.db exists inside the project data folder."
        )

    if read_only:
        conn = sqlite3.connect(
            DB_PATH.as_uri() + "?mode=ro",
            uri=True
        )
    else:
        conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn
