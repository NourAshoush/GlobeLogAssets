# GlobeLogAssets
Curated country and airport data—plus matching ISO flag assets—ready for direct use in client apps.

## Pipeline
1. `python process_countries.py`
   - Builds `data/curated_countries.csv` (cleaned ISO codes and names).
   - Builds `data/curated_continents.csv` (human-friendly continent labels).
2. `python process_airports.py`
   - Builds `data/curated_airports.csv` with only medium/large airports that have an IATA code.
3. `python validate_datasets.py`
   - Confirms every airport’s country exists in the curated list.
   - Lists countries currently lacking curated airports.
4. `python validate_flags.py`
   - Verifies flag filenames use uppercase ISO codes.
   - Flags any countries missing an asset or extra assets without a country.
5. `python build_sqlite.py`
   - Produces `data/globelog.sqlite` containing normalised tables and an FTS5 index for quick lookups.
6. `python verify_sqlite.py`
   - Compares the SQLite contents back to the curated CSVs.
   - Smoke-tests a handful of full-text searches to confirm text landed intact.

## Outputs & Stats
- `data/curated_countries.csv`
  - 248 ISO alpha-2 codes (non-ISO placeholders such as `XP` are skipped).
  - Names tidied for display (e.g. `Palestine`, `Western Sahara`, `Cocos Islands`, `Saint Helena & Tristan da Cunha`).
- `data/curated_continents.csv`
  - 7 continent rows (`AF`, `AN`, `AS`, `EU`, `NA`, `OC`, `SA`).
- `data/curated_airports.csv`
  - 4,480 records containing: `iata`, `name`, `latitude_deg`, `longitude_deg`, `continent`, `iso_country`, `municipality`, `icao_code`, `gps_code`.
- `data/globelog.sqlite`
  - Tables: `continent`, `country`, `airport`, plus `airport_search` (FTS5 virtual table).
  - Indices on `airport.country_code`, `airport.municipality`; `airport_search` enables instant text queries.

### Snapshot (current build)
- Countries without curated airports: `AD`, `AQ`, `AX`, `GS`, `HM`, `LI`, `MC`, `PN`, `PS`, `SM`, `TF`, `TK`, `VA`.
- Flag coverage: every curated country has a matching asset; no extras in `flags/`.

## SQLite Quick Reference
- FTS5 uses tokenised (word-based) matching, not edit-distance “fuzzy” search. A query such as `airport_search MATCH 'dubai'` matches tokens containing “Dubai”; add your own fuzzy layer if you need typo tolerance.
- Example query:
  ```sql
  SELECT iata, name
  FROM airport_search
  WHERE airport_search MATCH 'dubai'
  ORDER BY rank
  LIMIT 10;
  ```
- Bundle `globelog.sqlite` read-only in iOS. If you need write access, copy it to a writable directory on first launch.

## Sources
- Countries & airports: https://ourairports.com/data/
- Flags: https://flagpedia.net/
