from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Iterable, Tuple


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CURATED_COUNTRIES = DATA_DIR / "curated_countries.csv"
CURATED_CONTINENTS = DATA_DIR / "curated_continents.csv"
CURATED_AIRPORTS = DATA_DIR / "curated_airports.csv"
OUTPUT_DB = DATA_DIR / "globelog.sqlite"


def read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS airport_search;
        DROP TABLE IF EXISTS airport;
        DROP TABLE IF EXISTS country;
        DROP TABLE IF EXISTS continent;

        CREATE TABLE continent (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE country (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            continent_code TEXT NOT NULL REFERENCES continent(code) ON UPDATE CASCADE
        );

        CREATE TABLE airport (
            iata TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            municipality TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            continent_code TEXT NOT NULL REFERENCES continent(code),
            country_code TEXT NOT NULL REFERENCES country(code),
            icao_code TEXT,
            gps_code TEXT
        );

        CREATE INDEX idx_airport_country ON airport(country_code);
        CREATE INDEX idx_airport_municipality ON airport(municipality);
        """
    )


def populate_continents(conn: sqlite3.Connection) -> None:
    rows = [(row["code"], row["name"]) for row in read_csv(CURATED_CONTINENTS)]
    conn.executemany("INSERT INTO continent(code, name) VALUES (?, ?)", rows)


def populate_countries(conn: sqlite3.Connection) -> None:
    rows = [
        (
            row["code"],
            row["name"],
            row["continent"],
        )
        for row in read_csv(CURATED_COUNTRIES)
    ]
    conn.executemany(
        "INSERT INTO country(code, name, continent_code) VALUES (?, ?, ?)", rows
    )


def coerce_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def populate_airports(conn: sqlite3.Connection) -> None:
    rows: Iterable[Tuple[str, str, str | None, float, float, str, str, str | None, str | None]] = (
        (
            row["iata"],
            row["name"],
            row.get("municipality") or None,
            coerce_float(row.get("latitude_deg", "0")),
            coerce_float(row.get("longitude_deg", "0")),
            row.get("continent", ""),
            row.get("iso_country", ""),
            row.get("icao_code") or None,
            row.get("gps_code") or None,
        )
        for row in read_csv(CURATED_AIRPORTS)
    )
    conn.executemany(
        """
        INSERT INTO airport(
            iata,
            name,
            municipality,
            latitude,
            longitude,
            continent_code,
            country_code,
            icao_code,
            gps_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        list(rows),
    )


def populate_fts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE VIRTUAL TABLE airport_search USING fts5(
            name,
            municipality,
            iata,
            icao_code,
            country_code,
            content='airport',
            content_rowid='rowid'
        )
        """
    )

    conn.execute(
        """
        INSERT INTO airport_search(rowid, name, municipality, iata, icao_code, country_code)
        SELECT rowid, name, IFNULL(municipality, ''), iata, IFNULL(icao_code, ''), country_code
        FROM airport
        """
    )


def build_database() -> None:
    if not CURATED_COUNTRIES.exists() or not CURATED_AIRPORTS.exists():
        raise FileNotFoundError("Run the processing scripts before building the database.")

    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()

    with sqlite3.connect(OUTPUT_DB) as conn:
        create_schema(conn)
        populate_continents(conn)
        populate_countries(conn)
        populate_airports(conn)
        populate_fts(conn)
        conn.commit()
        conn.execute("VACUUM")


if __name__ == "__main__":
    build_database()
