import sqlite3
import time
from contextlib import closing
from database.db_connection import get_connection

MAX_ROWS = 100
TIMEOUT_SECONDS = 5

def execute_sql(query):
    query = (query or "").strip()

    if not query:
        return {"success": False, "error": "Empty query"}

    if not query.lower().startswith(("select", "with")):
        return {"success": False, "error": "Only SELECT queries are permitted"}

    try:
        with closing(get_connection(read_only=True)) as conn:
            deadline = time.monotonic() + TIMEOUT_SECONDS
            # runs every 10,000 VM steps; a truthy return aborts the query
            conn.set_progress_handler(lambda: time.monotonic() > deadline, 10_000)

            cursor = conn.execute(query)
            columns = [d[0] for d in cursor.description or []]
            rows = cursor.fetchmany(MAX_ROWS + 1)   # one extra to detect truncation

        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]

        return {
            "success": True,
            "columns": columns,
            "rows": [dict(r) for r in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }

    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            return {"success": False,
                    "error": f"Query exceeded {TIMEOUT_SECONDS}s. Simplify it or add filters/LIMIT."}
        return {"success": False, "error": str(e)}
    except sqlite3.Error as e:
        return {"success": False, "error": str(e)}
