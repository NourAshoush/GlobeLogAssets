from __future__ import annotations

import csv
import random
import sqlite3
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CURATED_AIRPORTS = DATA_DIR / "curated_airports.csv"
CURATED_COUNTRIES = DATA_DIR / "curated_countries.csv"
DB_PATH = DATA_DIR / "globelog.sqlite"


def load_curated_airports() -> Dict[str, Dict[str, str]]:
    with CURATED_AIRPORTS.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row["iata"]: row for row in reader}


def load_curated_countries() -> Dict[str, Dict[str, str]]:
    with CURATED_COUNTRIES.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row["code"]: row for row in reader}


def verify_database() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Database not found. Run build_sqlite.py first.")

    airports_csv = load_curated_airports()
    countries_csv = load_curated_countries()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    db_airports = {
        row["iata"]: row for row in cur.execute("SELECT * FROM airport")
    }
    db_countries = {
        row["code"]: row for row in cur.execute("SELECT * FROM country")
    }

    missing_in_db = sorted(set(airports_csv) - set(db_airports))
    extra_in_db = sorted(set(db_airports) - set(airports_csv))

    mismatches: List[str] = []
    fields_to_compare = [
        "name",
        "municipality",
        "continent",
        "iso_country",
        "icao_code",
        "gps_code",
    ]

    for iata, csv_row in airports_csv.items():
        db_row = db_airports.get(iata)
        if not db_row:
            continue
        for field in fields_to_compare:
            csv_value = (csv_row.get(field) or "").strip()
            if field == "continent":
                db_value = db_row["continent_code"]
            elif field == "iso_country":
                db_value = db_row["country_code"]
            else:
                db_value = (db_row[field] or "").strip()
            if csv_value != db_value:
                mismatches.append(f"{iata}: {field} mismatch CSV='{csv_value}' DB='{db_value}'")

    missing_countries = sorted(set(countries_csv) - set(db_countries))
    extra_countries = sorted(set(db_countries) - set(countries_csv))

    print(f"Curated airports CSV rows: {len(airports_csv)}")
    print(f"Airports in database: {len(db_airports)}")
    print(f"Missing airports in database: {missing_in_db}")
    print(f"Extra airports in database: {extra_in_db}")
    print(f"Mismatched airport fields: {len(mismatches)}")
    if mismatches:
        for line in mismatches[:10]:
            print(f"  {line}")

    print(f"Curated countries CSV rows: {len(countries_csv)}")
    print(f"Countries in database: {len(db_countries)}")
    print(f"Missing countries in database: {missing_countries}")
    print(f"Extra countries in database: {extra_countries}")

    sample_terms = random.sample(list(airports_csv.keys()), k=min(5, len(airports_csv)))
    print("FTS sample searches:")
    for iata in sample_terms:
        airport_name = airports_csv[iata]["name"]
        query = airport_name.split()[0]
        results = list(
            cur.execute(
                "SELECT iata, name FROM airport_search WHERE airport_search MATCH ? LIMIT 3",
                (query,),
            )
        )
        formatted = ", ".join(f"{row['iata']}:{row['name']}" for row in results) or "no hits"
        print(f"  '{query}' -> {formatted}")

    conn.close()


if __name__ == "__main__":
    verify_database()
