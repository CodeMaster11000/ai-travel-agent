import math
from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "attractions.csv"
FEE_COLUMN = "Entrance Fee in INR"
NAME_COLUMN = "Name"
CITY_COLUMN = "City"
TYPE_COLUMN = "Type"


def _load_dataset() -> pd.DataFrame:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Attractions dataset not found at {DATA_FILE}. "
            "Restore data/attractions.csv and try again."
        )
    try:
        frame = pd.read_csv(DATA_FILE)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not read the attractions dataset: {exc}") from exc

    frame.columns = frame.columns.astype(str).str.strip()
    required = {CITY_COLUMN, NAME_COLUMN, TYPE_COLUMN, FEE_COLUMN}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            "Attractions dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )
    return frame


def _clean_records(frame: pd.DataFrame) -> list[dict]:
    # Convert NaN/NaT values to None so API responses remain JSON-safe.
    cleaned = frame.astype(object).where(pd.notna(frame), None)
    records = cleaned.to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if hasattr(value, "item"):
                record[key] = value.item()
    return records


def _location_matches(frame: pd.DataFrame, location: str) -> pd.Series:
    """Match a destination against City, and State when the CSV provides it."""
    target = location.strip().casefold()
    city_matches = frame[CITY_COLUMN].astype(str).str.strip().str.casefold().eq(target)
    state_columns = [
        column for column in frame.columns
        if column.strip().casefold() in {"state", "state/union territory", "state or union territory"}
    ]
    if not state_columns:
        return city_matches
    state_matches = pd.Series(False, index=frame.index)
    for column in state_columns:
        state_matches |= frame[column].astype(str).str.strip().str.casefold().eq(target)
    return city_matches | state_matches


def search_attractions(
    city: str,
    category: str | None = None,
    max_results: int = 10,
) -> list[dict]:
    """Search the local CSV by city or, if available, state and optional category."""
    if not isinstance(city, str) or not city.strip():
        raise ValueError("A valid city name is required.")
    if category is not None and not isinstance(category, str):
        raise ValueError("Category must be text.")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 100:
        raise ValueError("max_results must be an integer between 1 and 100.")

    frame = _load_dataset()
    matches = frame[_location_matches(frame, city)].copy()

    if category and category.strip():
        matches = matches[
            matches[TYPE_COLUMN].astype(str).str.contains(
                category.strip(), case=False, na=False, regex=False
            )
        ]

    return _clean_records(matches.head(max_results))


def calculate_attraction_fees(
    city: str,
    attraction_names: list[str],
    people: int = 1,
) -> dict:
    """Sum entry fees for exact attraction names within a city/state destination."""
    if not isinstance(city, str) or not city.strip():
        raise ValueError("A valid city is required.")
    if not isinstance(attraction_names, list) or not attraction_names:
        raise ValueError("Provide at least one attraction name.")
    if isinstance(people, bool) or not isinstance(people, int) or people < 1:
        raise ValueError("People must be a positive integer.")

    frame = _load_dataset()
    city_rows = frame[_location_matches(frame, city)]
    if city_rows.empty:
        return {"error": f"No attractions found for {city}."}

    results, seen = [], set()
    total_per_person = 0.0

    for requested_name in attraction_names:
        if not isinstance(requested_name, str) or not requested_name.strip():
            raise ValueError("Every attraction name must be a non-empty string.")
        key = requested_name.strip().casefold()
        if key in seen:
            continue
        seen.add(key)

        match = city_rows[
            city_rows[NAME_COLUMN].astype(str).str.strip().str.casefold() == key
        ]
        if match.empty:
            results.append({
                "name": requested_name.strip(),
                "error": "Not found in the city's dataset; fee not included.",
            })
            continue

        row = match.iloc[0]
        raw_fee = row[FEE_COLUMN]
        try:
            fee = float(raw_fee)
        except (TypeError, ValueError):
            fee = math.nan

        if not math.isfinite(fee) or fee < 0:
            results.append({
                "name": str(row[NAME_COLUMN]),
                "error": "Entry fee is missing or invalid; fee not included.",
            })
            continue

        total_per_person += fee
        results.append({
            "name": str(row[NAME_COLUMN]),
            "fee_per_person": round(fee, 2),
            "fee_for_all_people": round(fee * people, 2),
        })

    return {
        "city": city.strip(),
        "people": people,
        "attractions": results,
        "total_per_person": round(total_per_person, 2),
        "total_for_all_people": round(total_per_person * people, 2),
        "note": "Fees come from the local CSV and may be outdated; verify before travel.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(search_attractions("Jaipur", max_results=10), indent=2, ensure_ascii=False))
