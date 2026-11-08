from contextlib import closing
from database.db_connection import get_connection

def get_schema():
    result = {}
    with closing(get_connection(read_only=True)) as conn:
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\'
        """).fetchall()

        for t in tables:
            name = t["name"]
            cols = conn.execute(f"PRAGMA table_info('{name}')").fetchall()
            fks = conn.execute(f"PRAGMA foreign_key_list('{name}')").fetchall()

            result[name] = {
                "columns": [
                    {"column": c["name"], "type": c["type"], "primary_key": bool(c["pk"])}
                    for c in cols
                ],
                "foreign_keys": [
                    {"column": f["from"], "references": f"{f['table']}.{f['to']}"}
                    for f in fks
                ],
            }
    return result
