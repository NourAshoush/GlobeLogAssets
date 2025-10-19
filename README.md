# GlobeLogAssets
Curated country, continent, and airport datasets sourced from https://ourairports.com/data/ with matching ISO flag assets.

## Workflow
1. `python process_countries.py`
   - Generates `data/curated_countries.csv` with cleaned names and ISO-only codes.
   - Generates `data/curated_continents.csv` listing the continents referenced by the curated countries.
2. `python process_airports.py`
   - Generates `data/curated_airports.csv` limited to medium and large airports that provide an IATA identifier.
3. `python validate_datasets.py`
   - Confirms every airport country appears in `curated_countries.csv`.
   - Lists countries that currently have no curated airports.
4. `python validate_flags.py`
   - Ensures every curated country has an uppercase ISO flag in `flags/`.
   - Highlights any extra flag assets without a matching country.

## Curated Outputs
- `data/curated_countries.csv`
  - 248 ISO alpha-2 codes (non-ISO user codes like `XP` are excluded).
  - Names normalised for readability (parenthetical notes removed; examples: `Palestine`, `Western Sahara`, `Cocos Islands`, `Saint Helena & Tristan da Cunha`).
- `data/curated_continents.csv`
  - 7 entries mapping ISO continent codes to friendly labels.
- `data/curated_airports.csv`
  - 4,480 airports: only `medium_airport` or `large_airport` rows with a non-empty IATA code.
  - Columns: `iata`, `name`, `latitude_deg`, `longitude_deg`, `continent`, `iso_country`, `iso_region`, `icao_code`, `gps_code`.

## Data Snapshot
- Countries without a curated airport: `AD`, `AQ`, `AX`, `GS`, `HM`, `LI`, `MC`, `PN`, `PS`, `SM`, `TF`, `TK`, `VA`.
- Flag coverage: every curated country has a corresponding flag asset; no extra flags remain in `flags/`.

## Sources
- Countries and airports: https://ourairports.com/data/
- Flags: https://flagpedia.net/
