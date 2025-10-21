from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


DB_PATH = Path("data/globelog.sqlite")
ROW_LIMIT = 10


def query_rows(cursor: sqlite3.Cursor, table: str, columns: Iterable[str] | None = None) -> list[sqlite3.Row]:
    if table.startswith("airport_search"):
        return []

    cols = ", ".join(columns) if columns else "*"
    if table == "airport":
        cols = "iata, name, municipality, country_code, timezone, latitude, longitude"
    elif table == "country":
        cols = "code, name, continent_code"
    elif table == "continent":
        cols = "code, name"

    return cursor.execute(f"SELECT {cols} FROM {table} LIMIT {ROW_LIMIT}").fetchall()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Run build_sqlite.py first to generate data/globelog.sqlite")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        tables = [
            row["name"]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]

        print(f"Database: {DB_PATH}")
        print(f"Tables ({len(tables)}): {', '.join(tables)}")
        print()

        for table in tables:
            rows = query_rows(cur, table)
            print(f"Table: {table} (columns: {', '.join(rows[0].keys()) if rows else 'n/a'})")
            if not rows:
                print("  [no preview shown]")
                print()
                continue
            for row in rows:
                formatted = ", ".join(f"{k}={row[k]}" for k in row.keys())
                print(f"  {formatted}")
            print()


if __name__ == "__main__":
    main()
