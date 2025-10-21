from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, Tuple


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CURATED_AIRPORTS = DATA_DIR / "curated_airports.csv"
AIRPORT_TIMEZONES_JSON = DATA_DIR / "airport-timezones.json"
TIMEZONE_OVERRIDES_PATH = DATA_DIR / "corrections" / "timezone_overrides.json"


def load_curated_airports() -> Dict[str, Dict[str, str]]:
    with CURATED_AIRPORTS.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row["iata"]: row for row in reader}


def load_overrides() -> Dict[str, str]:
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
            country = (value.get("countryCode") or "").strip()
        else:
            tz = (value or "").strip()
            country = ""
        if tz:
            overrides[code] = {"timezone": tz, "countryCode": country}
    return overrides


def load_timezone_map() -> Dict[str, Dict[str, str]]:
    data = json.loads(AIRPORT_TIMEZONES_JSON.read_text())
    deduped: "OrderedDict[str, Dict[str, str]]" = OrderedDict()
    for entry in data:
        code = (entry.get("code") or "").strip()
        if not code or code in deduped:
            continue
        deduped[code] = {
            "timezone": (entry.get("timezone") or "").strip(),
            "countryCode": (entry.get("countryCode") or "").strip(),
        }
    overrides = load_overrides()
    for code, payload in overrides.items():
        tz = payload.get("timezone", "")
        country = payload.get("countryCode") or deduped.get(code, {}).get("countryCode", "")
        if tz:
            deduped[code] = {"timezone": tz, "countryCode": country}
    return deduped


def verify_timezones() -> None:
    if not CURATED_AIRPORTS.exists():
        raise FileNotFoundError("curated_airports.csv not found. Run process_airports.py first.")
    if not AIRPORT_TIMEZONES_JSON.exists():
        raise FileNotFoundError("airport-timezones.json not found in data/.")

    airports = load_curated_airports()
    timezones = load_timezone_map()

    covered = []
    missing = []
    mismatched_country = []

    for code, airport in airports.items():
        tz_entry = timezones.get(code)
        if tz_entry is None or not tz_entry["timezone"]:
            missing.append(code)
            continue
        covered.append(code)
        if tz_entry["countryCode"] and tz_entry["countryCode"] != airport["iso_country"]:
            mismatched_country.append((code, airport["iso_country"], tz_entry["countryCode"]))

    print(f"Curated airports: {len(airports)}")
    print(f"Timezones available: {len(timezones)} (deduped)")
    print(f"Covered airports: {len(covered)} ({len(covered)/len(airports)*100:.2f}%)")
    print(f"Missing airports: {len(missing)}")
    if missing:
        print("Missing codes:", ", ".join(missing))

    print(f"Country mismatches: {len(mismatched_country)}")
    for code, expected_country, tz_country in mismatched_country[:10]:
        print(f"  {code}: curated={expected_country}, tz_source={tz_country}")


if __name__ == "__main__":
    verify_timezones()
