from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List


DATA_DIR = Path(__file__).parent / "data"
INPUT_COUNTRIES_CSV = DATA_DIR / "countries.csv"
OUTPUT_CURATED_COUNTRIES_CSV = DATA_DIR / "curated_countries.csv"
OUTPUT_CURATED_CONTINENTS_CSV = DATA_DIR / "curated_continents.csv"

# Non-ISO alpha-2 codes we omit from the curated export.
EXCLUDED_COUNTRY_CODES = {"XP"}

# Friendly display names for specific ISO codes.
NAME_OVERRIDES: Dict[str, str] = {
    "CC": "Cocos Islands",
    "EH": "Western Sahara",
    "PS": "Palestine",
    "SH": "Saint Helena & Tristan da Cunha",
}


# Basic mapping from OurAirports continent codes to human-friendly names
CONTINENT_CODE_TO_NAME: Dict[str, str] = {
    "AF": "Africa",
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America",
}


def clean_country_name(code: str, name: str) -> str:
    if code in NAME_OVERRIDES:
        return NAME_OVERRIDES[code]
    # Remove parenthetical descriptors and collapse whitespace.
    cleaned = re.sub(r"\s*\(.*?\)", "", name).strip()
    return re.sub(r"\s{2,}", " ", cleaned)


def load_countries(path: Path) -> List[Dict[str, str]]:
    """Load countries from OurAirports countries.csv and return simplified rows.

    Output rows include: code, name, continent (2-letter code).
    """
    countries: List[Dict[str, str]] = []
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("code", "").strip()
            if not code or code in EXCLUDED_COUNTRY_CODES:
                continue
            name = row.get("name", "").strip()
            countries.append(
                {
                    "code": code,
                    "name": clean_country_name(code, name),
                    "continent": row.get("continent", "").strip(),
                }
            )
    return countries


def write_curated_countries(path: Path, countries: List[Dict[str, str]]) -> None:
    """Write curated countries with columns: code, name, continent."""
    with path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "continent"])
        writer.writeheader()
        writer.writerows(countries)


def derive_continents(countries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Derive unique continents from countries with code and name.

    Returns a list of dicts with keys: code, name. Only includes
    continents referenced by at least one country in the input.
    """
    seen = set()
    continents: List[Dict[str, str]] = []
    for c in countries:
        code = c.get("continent", "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        continents.append({
            "code": code,
            "name": CONTINENT_CODE_TO_NAME.get(code, code),
        })
    # Sort by name for a clean, predictable order
    continents.sort(key=lambda x: (x["name"], x["code"]))
    return continents


def write_curated_continents(path: Path, continents: List[Dict[str, str]]) -> None:
    """Write curated continents with columns: code, name."""
    with path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name"])
        writer.writeheader()
        writer.writerows(continents)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    countries = load_countries(INPUT_COUNTRIES_CSV)
    write_curated_countries(OUTPUT_CURATED_COUNTRIES_CSV, countries)

    continents = derive_continents(countries)
    write_curated_continents(OUTPUT_CURATED_CONTINENTS_CSV, continents)

    print(
        f"Processed {len(countries)} countries → {OUTPUT_CURATED_COUNTRIES_CSV.name} and "
        f"{len(continents)} continents → {OUTPUT_CURATED_CONTINENTS_CSV.name}."
    )


if __name__ == "__main__":
    main()
