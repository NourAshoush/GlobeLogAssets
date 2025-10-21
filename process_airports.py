from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

DATA_DIR = Path(__file__).parent / "data"
INPUT_AIRPORTS_CSV = DATA_DIR / "airports.csv"
OUTPUT_CURATED_AIRPORTS_CSV = DATA_DIR / "curated_airports.csv"
AIRPORT_TIMEZONES_JSON = DATA_DIR / "airport-timezones.json"
TIMEZONE_OVERRIDES_PATH = DATA_DIR / "corrections" / "timezone_overrides.json"

ALLOWED_TYPES = {"medium_airport", "large_airport"}
OUTPUT_FIELDNAMES = [
    "iata",
    "name",
    "latitude_deg",
    "longitude_deg",
    "continent",
    "iso_country",
    "municipality",
    "timezone",
    "icao_code",
    "gps_code",
]

def load_timezone_overrides() -> Dict[str, str]:
    if not TIMEZONE_OVERRIDES_PATH.exists():
        return {}
    try:
        data = json.loads(TIMEZONE_OVERRIDES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {TIMEZONE_OVERRIDES_PATH}: {exc}") from exc

    overrides: Dict[str, str] = {}
    for code, value in data.items():
        code = (code or "").strip().upper()
        if not code:
            continue
        if isinstance(value, dict):
            tz = (value.get("timezone") or "").strip()
        else:
            tz = (value or "").strip()
        if tz:
            overrides[code] = tz
    return overrides


def load_airports(path: Path) -> Iterable[Dict[str, str]]:
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def load_timezones(path: Path) -> Dict[str, str]:
    timezones: Dict[str, str] = {}
    if not path.exists():
        return load_timezone_overrides()

    data = json.loads(path.read_text(encoding="utf-8"))
    for entry in data:
        code = (entry.get("code") or "").strip().upper()
        if not code or code in timezones:
            continue
        tz = (entry.get("timezone") or "").strip()
        if tz:
            timezones[code] = tz

    # Apply overrides last so they win
    timezones.update(load_timezone_overrides())
    return timezones


def filter_airports(
    rows: Iterable[Dict[str, str]],
    timezones: Dict[str, str],
) -> Tuple[List[Dict[str, str]], Counter, int, int, int]:
    filtered: List[Dict[str, str]] = []
    type_counts: Counter = Counter()
    missing_iata = 0
    missing_timezone = 0
    missing_municipality = 0

    for row in rows:
        airport_type = row.get("type", "").strip()
        if airport_type not in ALLOWED_TYPES:
            continue

        iata_code = row.get("iata_code", "").strip()
        if not iata_code:
            missing_iata += 1
            continue

        municipality = (row.get("municipality") or "").strip()
        if not municipality:
            missing_municipality += 1

        timezone = timezones.get(iata_code, "")
        if not timezone:
            missing_timezone += 1

        type_counts[airport_type] += 1
        filtered.append(
            {
                "iata": iata_code,
                "name": row.get("name", "").strip(),
                "latitude_deg": row.get("latitude_deg", "").strip(),
                "longitude_deg": row.get("longitude_deg", "").strip(),
                "continent": row.get("continent", "").strip(),
                "iso_country": row.get("iso_country", "").strip(),
                "municipality": municipality,
                "timezone": timezone,
                "icao_code": row.get("icao_code", "").strip(),
                "gps_code": row.get("gps_code", "").strip(),
            }
        )

    filtered.sort(key=lambda airport: (airport["iata"], airport["name"]))
    return filtered, type_counts, missing_iata, missing_timezone, missing_municipality


def write_curated_airports(path: Path, airports: List[Dict[str, str]]) -> None:
    with path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(airports)


def summarize(
    airports: List[Dict[str, str]],
    type_counts: Counter,
    missing_iata: int,
    missing_timezone: int,
    missing_municipality: int,
) -> str:
    """Create a human-friendly summary of the curated airports."""
    countries = Counter(airport["iso_country"] for airport in airports)
    top_countries = ", ".join(
        f"{country}:{count}" for country, count in countries.most_common(5)
    ) or "n/a"
    medium_count = type_counts.get("medium_airport", 0)
    large_count = type_counts.get("large_airport", 0)
    return (
        f"Kept {len(airports)} airports (medium: {medium_count}, large: {large_count}). "
        f"Skipped {missing_iata} medium/large airports without IATA codes. "
        f"Missing timezones for {missing_timezone} airports. "
        f"Missing municipalities for {missing_municipality} airports. "
        f"Top countries by count: {top_countries}."
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = list(load_airports(INPUT_AIRPORTS_CSV))
    timezones = load_timezones(AIRPORT_TIMEZONES_JSON)
    filtered, type_counts, missing_iata, missing_timezone, missing_municipality = filter_airports(
        all_rows, timezones
    )
    write_curated_airports(OUTPUT_CURATED_AIRPORTS_CSV, filtered)

    print(
        f"Read {len(all_rows)} airports from {INPUT_AIRPORTS_CSV.name}. "
        f"Wrote {len(filtered)} → {OUTPUT_CURATED_AIRPORTS_CSV.name}."
    )
    if filtered:
        print(summarize(filtered, type_counts, missing_iata, missing_timezone, missing_municipality))
        sample = filtered[:5]
        print("Sample (first 5):")
        for airport in sample:
            print(
                f"  {airport['iata']:>3} | {airport['name']} | {airport['iso_country']} | "
                f"{airport['continent']} | {airport['latitude_deg']}, {airport['longitude_deg']}"
            )


if __name__ == "__main__":
    main()
