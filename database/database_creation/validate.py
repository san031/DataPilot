"""
validate.py — Step 1.10: verify foreign keys and relationships.

Run on its own:  python database/validate.py
Returns True only if every check passes.
"""

import sqlite3
from pathlib import Path

TABLES = ["categories", "products", "warehouses", "inventory", "customers",
          "orders", "order_items", "payments", "shipments", "returns"]

# Each check is a query that counts rows that BREAK a rule. 0 = pass.
CHECKS = {
    "payment != order items total": """
        SELECT COUNT(*) FROM payments p
        JOIN (SELECT order_id, ROUND(SUM(quantity * unit_price), 2) AS t
              FROM order_items GROUP BY order_id) i USING(order_id)
        WHERE ABS(p.amount - i.t) > 0.01""",
    "delivery before order": """
        SELECT COUNT(*) FROM shipments s JOIN orders o USING(order_id)
        WHERE s.delivery_date < o.order_date""",
    "order without items": """
        SELECT COUNT(*) FROM orders o
        WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)""",
    "order placed before customer registered": """
        SELECT COUNT(*) FROM orders o JOIN customers c USING(customer_id)
        WHERE o.order_date < c.registration_date""",
    "returned item not in that order": """
        SELECT COUNT(*) FROM returns r
        WHERE NOT EXISTS (SELECT 1 FROM order_items i
                          WHERE i.order_id = r.order_id AND i.product_id = r.product_id)""",
    "return for undelivered order": """
        SELECT COUNT(*) FROM returns r JOIN orders o USING(order_id)
        WHERE o.order_status <> 'delivered'""",
}


def validate(db_path: Path) -> bool:
    con = sqlite3.connect(db_path)
    try:
        print(f"Database: {db_path}\n")
        for t in TABLES:
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:<12} {n:>6} rows")

        print()
        fk_errors = len(con.execute("PRAGMA foreign_key_check").fetchall())
        results = {"foreign-key violations": fk_errors}
        for name, sql in CHECKS.items():
            results[name] = con.execute(sql).fetchone()[0]

        for name, bad in results.items():
            print(f"  {'PASS' if bad == 0 else 'FAIL'}  {name:<42} {bad}")

        ok = all(v == 0 for v in results.values())
        print("\nAll checks passed." if ok else "\nSome checks FAILED.")
        return ok
    finally:
        con.close()


if __name__ == "__main__":
    from database.build_db import DB_PATH
    raise SystemExit(0 if validate(DB_PATH) else 1)