### FILE: app/tools/attractions.py
"""Attractions dataset querying and entrance fee verification with in-memory caching."""
import functools
import math
import re
from pathlib import Path
import pandas as pd
from app.config import ATTRACTIONS_FILE

FEE_COLUMN = "Entrance Fee in INR"
NAME_COLUMN = "Name"
CITY_COLUMN = "City"
TYPE_COLUMN = "Type"

# FIX B2: In-memory cached loader to prevent reading attractions.csv on every query.
@functools.lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    if not ATTRACTIONS_FILE.is_file():
        raise FileNotFoundError(f"Attractions dataset missing at {ATTRACTIONS_FILE}.")
    try:
        frame = pd.read_csv(ATTRACTIONS_FILE)
    except Exception as exc:
        raise ValueError(f"Could not load attractions dataset: {exc}") from exc

    frame.columns = frame.columns.astype(str).str.strip()
    required = {CITY_COLUMN, NAME_COLUMN, TYPE_COLUMN, FEE_COLUMN}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Attractions CSV missing expected columns: {missing}")
    return frame


def _location_matches(frame: pd.DataFrame, location: str) -> pd.Series:
    target = location.strip().casefold()
    city_matches = frame[CITY_COLUMN].astype(str).str.strip().str.casefold().eq(target)
    state_columns = [
        col for col in frame.columns
        if col.strip().casefold() in {"state", "state/union territory", "state or union territory"}
    ]
    if not state_columns:
        return city_matches
    state_matches = pd.Series(False, index=frame.index)
    for col in state_columns:
        state_matches |= frame[col].astype(str).str.strip().str.casefold().eq(target)
    return city_matches | state_matches


def search_attractions(city: str, category: str | None = None, max_results: int = 10) -> list[dict]:
    """Search for attractions in a city with optional category filtering."""
    if not isinstance(city, str) or not city.strip():
        raise ValueError("A valid destination city name is required.")
    if max_results < 1 or max_results > 100:
        raise ValueError("max_results must be between 1 and 100.")

    frame = load_dataset()
    matches = frame[_location_matches(frame, city)].copy()

    if category and category.strip():
        matches = matches[
            matches[TYPE_COLUMN].astype(str).str.contains(
                category.strip(), case=False, na=False, regex=False
            )
        ]

    cleaned = matches.astype(object).where(pd.notna(matches), None)
    records = cleaned.head(max_results).to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "item"):
                r[k] = v.item()
    return records


# FIX B8: Resilient tokenized normalization to match attractions despite punctuation variance.
def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def calculate_attraction_fees(city: str, attraction_names: list[str], people: int = 1) -> dict:
    """Calculate entry costs for a specified group across candidate attractions."""
    if not attraction_names:
        return {"city": city, "people": people, "attractions": [], "total_per_person": 0.0, "total_for_all_people": 0.0}

    frame = load_dataset()
    city_rows = frame[_location_matches(frame, city)]
    if city_rows.empty:
        return {"error": f"No attractions found for destination: {city}"}

    results = []
    seen = set()
    total_per_person = 0.0

    normalized_map = {
        _normalize_name(str(row[NAME_COLUMN])): row
        for _, row in city_rows.iterrows()
    }

    for name in attraction_names:
        norm = _normalize_name(name)
        if norm in seen:
            continue
        seen.add(norm)

        matched_row = normalized_map.get(norm)
        if matched_row is None:
            results.append({
                "name": name,
                "fee_per_person": 0.0,
                "fee_for_all_people": 0.0,
                "verified": False,
                "error": "Attraction not present in dataset",
            })
            continue

        raw_fee = matched_row[FEE_COLUMN]
        try:
            fee = float(raw_fee)
        except (ValueError, TypeError):
            fee = 0.0

        is_valid_positive = math.isfinite(fee) and fee >= 0
        fee_val = fee if is_valid_positive else 0.0
        total_per_person += fee_val

        results.append({
            "name": str(matched_row[NAME_COLUMN]),
            "fee_per_person": round(fee_val, 2),
            "fee_for_all_people": round(fee_val * people, 2),
            "verified": (fee_val > 0),
        })

    return {
        "city": city,
        "people": people,
        "attractions": results,
        "total_per_person": round(total_per_person, 2),
        "total_for_all_people": round(total_per_person * people, 2),
    }