"""
build_db.py — builds data/ecommerce.db in one command.

Run from the lexsi folder:   python database/build_db.py

    schema.sql   1.3–1.7  table definitions
    generate.py  1.8      synthetic records
    load.py      1.9      create tables + insert
    validate.py  1.10     foreign-key and consistency checks

Uses only the Python standard library.
"""

import sys
from pathlib import Path
from database.db_connection import DB_PATH


from database.database_creation.generate import generate_all, SEED
from database.database_creation.load import load
from database.database_creation.validate import validate

# lexsi/data/ecommerce.db, no matter which folder you run this from
# DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"


def main() -> None:
    data = generate_all(SEED)
    load(DB_PATH, data)
    if not validate(DB_PATH):
        sys.exit(1)


if __name__ == "__main__":
    main()