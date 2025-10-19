from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Set


DATA_DIR = Path(__file__).parent / "data"
CURATED_COUNTRIES = DATA_DIR / "curated_countries.csv"
CURATED_AIRPORTS = DATA_DIR / "curated_airports.csv"


def load_countries(path: Path) -> Dict[str, str]:
    countries: Dict[str, str] = {}
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("code", "").strip()
            if not code:
                continue
            countries[code] = row.get("name", "").strip() or code
    return countries


def load_airport_countries(path: Path) -> Counter:
    counts: Counter = Counter()
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("iso_country", "").strip()
            if code:
                counts[code] += 1
    return counts


def validate() -> int:
    if not CURATED_COUNTRIES.exists():
        print(f"Missing {CURATED_COUNTRIES.name}. Run process_countries.py first.")
        return 1
    if not CURATED_AIRPORTS.exists():
        print(f"Missing {CURATED_AIRPORTS.name}. Run process_airports.py first.")
        return 1

    countries = load_countries(CURATED_COUNTRIES)
    airport_country_counts = load_airport_countries(CURATED_AIRPORTS)

    country_codes: Set[str] = set(countries)
    airport_codes: Set[str] = set(airport_country_counts)

    missing_in_countries = sorted(airport_codes - country_codes)
    countries_without_airports = sorted(country_codes - airport_codes)

    country_total = len(countries)
    airport_total = sum(airport_country_counts.values())

    print(f"Loaded {country_total} countries and {airport_total} airports.")

    if missing_in_countries:
        print("Countries referenced by airports but missing from curated countries:")
        for code in missing_in_countries:
            print(f"  {code}")
    else:
        print("All airport country codes are present in curated countries.")

    if countries_without_airports:
        print("Countries with no curated airports:")
        for code in countries_without_airports:
            name = countries.get(code, code)
            print(f"  {code} – {name}")
        print(f"Total without airports: {len(countries_without_airports)}")
    else:
        print("Every curated country has at least one curated airport.")

    return 0


def main() -> None:
    sys.exit(validate())


if __name__ == "__main__":
    main()
