from __future__ import annotations

import csv
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Set, Tuple


DATA_DIR = Path(__file__).parent / "data"
FLAGS_DIR = Path(__file__).parent / "flags"
CURATED_COUNTRIES = DATA_DIR / "curated_countries.csv"
FLAG_EXTENSIONS = {".pdf", ".svg", ".png"}


class FlagValidationError(RuntimeError):
    pass


def load_country_codes(path: Path) -> Set[str]:
    with path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row.get("code", "").strip() for row in reader if row.get("code", "").strip()}


def index_flag_files(directory: Path) -> Tuple[Dict[str, Path], Dict[str, List[Path]]]:
    mapping: Dict[str, Path] = {}
    duplicates: Dict[str, List[Path]] = {}

    for path in directory.iterdir():
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in FLAG_EXTENSIONS:
            continue
        key = path.stem.upper()
        if key in mapping:
            duplicates.setdefault(key, [mapping[key]]).append(path)
        else:
            mapping[key] = path

    return mapping, duplicates


def rename_with_case(source: Path, code: str) -> bool:
    target = source.with_name(f"{code}{source.suffix.lower()}")
    if source.name == target.name:
        return False

    try:
        source.rename(target)
        return True
    except OSError:
        temp = source.with_name(f"{source.stem}_{uuid.uuid4().hex}{source.suffix.lower()}")
        source.rename(temp)
        temp.rename(target)
        return True


def validate_flags() -> int:
    if not CURATED_COUNTRIES.exists():
        raise FlagValidationError(
            "Missing curated_countries.csv. Run process_countries.py first."
        )
    if not FLAGS_DIR.exists():
        raise FlagValidationError(f"Missing flags directory: {FLAGS_DIR}")

    country_codes = load_country_codes(CURATED_COUNTRIES)
    if not country_codes:
        raise FlagValidationError("No country codes found in curated_countries.csv")

    flag_index, duplicate_files = index_flag_files(FLAGS_DIR)

    renamed_count = 0
    missing: List[str] = []
    failed: List[str] = []

    for code in sorted(country_codes):
        path = flag_index.get(code)
        if path is None:
            missing.append(code)
            continue

        if path.stem != code:
            if rename_with_case(path, code):
                renamed_count += 1
                # Update index with new path reference
                new_path = path.with_name(f"{code}{path.suffix.lower()}")
                flag_index[code] = new_path
            else:
                failed.append(code)

    extra_flags = sorted(set(flag_index.keys()) - country_codes)

    total_countries = len(country_codes)
    print(f"Validated {total_countries} curated countries against flag assets.")

    if renamed_count:
        print(f"Renamed {renamed_count} flag files to uppercase ISO codes.")
    else:
        print("All matching flag files already used uppercase ISO codes.")

    success = True
    if missing:
        success = False
        print(f"Missing {len(missing)} flags:")
        for code in missing:
            print(f"  {code}")

    if failed:
        success = False
        print("Failed to normalize filenames for codes: " + ", ".join(sorted(set(failed))))

    if duplicate_files:
        success = False
        print("Duplicate flag files detected:")
        for code, paths in sorted(duplicate_files.items()):
            formatted = ", ".join(str(p) for p in paths)
            print(f"  {code}: {formatted}")

    if extra_flags:
        print(f"Flags without matching country codes: {', '.join(extra_flags)}")

    if success:
        print("Every curated country has a flag asset in the flags directory.")
        return 0

    return 1


def main() -> None:
    try:
        sys.exit(validate_flags())
    except FlagValidationError as exc:
        print(f"Validation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
