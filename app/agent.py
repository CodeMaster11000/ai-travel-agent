import json
import math
import os
import re

try:
    import ollama
except ImportError:  # Allows unit tests to run before optional model dependencies are installed.
    ollama = None

from dotenv import load_dotenv

load_dotenv()

from app.tools.attractions import search_attractions, calculate_attraction_fees
from app.tools.budget import calculate_budget
from app.tools.memory import get_memories
from app.tools.weather import get_weather

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MAX_ITINERARY_ATTRACTIONS = 12


def _extract_trip_updates(prompt: str) -> dict:
    """Extract whichever trip fields are present in a message."""
    if not isinstance(prompt, str) or not prompt.strip():
        return {}

    city_match = re.search(
        r"\b(?:trip\s+(?:to|across|in)|travel\s+to|visit|destination\s+(?:is|to)|in|across)\s+"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"(?=\s+(?:for|with|on|under|within|budget|and|from|to)\b|[,.;\n]|$)",
        prompt,
        re.IGNORECASE,
    )
    people_match = re.search(
        r"\b(\d+)\s*(?:people|persons|travellers|travelers|adults)\b",
        prompt, re.IGNORECASE,
    )
    days_match = re.search(
        r"\b(\d+)\s*[- ]?day(?:s)?\b", prompt, re.IGNORECASE
    )
    budget_match = re.search(
        r"(?:budget(?:\s+(?:of|to|is|by))?|increase\s+(?:the\s+)?budget\s+to|"
        r"raise\s+(?:the\s+)?budget\s+to|under|within|spend(?:ing)?\s+of)\s*"
        r"(?:₹|INR\s*|Rs\.?\s*)?([\d,]+(?:\.\d{1,2})?)",
        prompt, re.IGNORECASE,
    )

    updates = {}
    if city_match:
        updates["city"] = city_match.group(1).strip(" .'-")
    if people_match:
        updates["people"] = int(people_match.group(1))
    if days_match:
        updates["days"] = int(days_match.group(1))
    if budget_match:
        updates["budget"] = float(budget_match.group(1).replace(",", ""))
    return updates


def _validate_trip_details(details: dict) -> dict:
    missing = []
    if not details.get("city"):
        missing.append("destination (for example, 'trip to Jaipur')")
    if details.get("people") is None:
        missing.append("number of people")
    if details.get("days") is None:
        missing.append("duration (for example, '2-day')")
    if details.get("budget") is None:
        missing.append("total budget (for example, 'budget 8000')")
    if missing:
        raise ValueError("Please specify the " + ", ".join(missing) + ".")

    city = str(details["city"]).strip(" .'-")
    people = int(details["people"])
    days = int(details["days"])
    budget = float(details["budget"])
    if not city:
        raise ValueError("Please specify a valid destination.")
    if people < 1 or days < 1 or budget < 0 or not math.isfinite(budget):
        raise ValueError("People and days must be positive; budget must be non-negative.")
    if days > 30:
        raise ValueError("For this MVP, trip duration is limited to 30 days.")
    if people > 100:
        raise ValueError("For this MVP, traveller count is limited to 100.")
    return {"city": city.title(), "people": people, "days": days, "budget": budget}


def extract_trip_details(prompt: str) -> dict:
    """Extract a complete trip request from a single message."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Please describe your trip.")
    return _validate_trip_details(_extract_trip_updates(prompt))


def resolve_trip_details(prompt: str, previous_prompt: str | None = None) -> dict:
    """Apply a follow-up update to the most recent complete trip request."""
    updates = _extract_trip_updates(prompt)
    required = {"city", "people", "days", "budget"}
    if required.issubset(updates):
        return _validate_trip_details(updates)

    if previous_prompt:
        previous = _extract_trip_updates(previous_prompt)
        if required.issubset(previous):
            # Only fields explicitly present in the follow-up are changed.
            previous.update(updates)
            return _validate_trip_details(previous)

    return _validate_trip_details(updates)


def _numeric(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _select_attractions(city: str, prompt: str, days: int, memories: list[dict]) -> list[dict]:
    """Select a varied set of dataset attractions for the requested duration."""
    all_attractions = search_attractions(city, max_results=100)
    if not all_attractions:
        return []

    prompt_lower = prompt.casefold()
    # Explicitly requested places take priority and are not silently replaced.
    explicit = [
        item for item in all_attractions
        if str(item.get("Name") or "").strip()
        and str(item["Name"]).strip().casefold() in prompt_lower
    ]
    if explicit:
        return explicit[:MAX_ITINERARY_ATTRACTIONS]

    preference = next(
        (
            str(item["memory_value"])
            for item in memories
            if item.get("memory_key", "").casefold() in {"preferred_category", "interests"}
        ),
        "",
    )

    def rating(item):
        value = _numeric(item.get("Google review rating"))
        return value if value is not None else 0.0

    # Prefer attractions matching saved interests, then rank by dataset rating.
    candidates = sorted(
        all_attractions,
        key=lambda item: (
            bool(preference) and (
                preference.casefold() in str(item.get("Type") or "").casefold()
                or preference.casefold() in str(item.get("Significance") or "").casefold()
            ),
            rating(item),
        ),
        reverse=True,
    )

    # Avoid picking only one kind of place (for example, several temples).
    # The dataset has no coordinates, so this is category diversity, not distance routing.
    target_count = min(max(days, days * 2), MAX_ITINERARY_ATTRACTIONS, len(candidates))
    chosen = []
    chosen_names = set()
    chosen_types = set()
    remaining = list(candidates)
    while remaining and len(chosen) < target_count:
        index = next(
            (
                i for i, item in enumerate(remaining)
                if str(item.get("Type") or "Unknown").strip().casefold() not in chosen_types
            ),
            0,
        )
        item = remaining.pop(index)
        name = str(item.get("Name") or "").strip()
        if not name or name.casefold() in chosen_names:
            continue
        chosen.append(item)
        chosen_names.add(name.casefold())
        chosen_types.add(str(item.get("Type") or "Unknown").strip().casefold())

    return chosen


def _build_itinerary(attractions: list[dict], days: int) -> str:
    """Create a deterministic schedule with no duplicate places or empty days when possible."""
    if not attractions:
        return "No attractions were available to schedule."

    day_groups = [[] for _ in range(days)]
    day_loads = [0.0 for _ in range(days)]
    # Place longer visits on the currently lightest day to avoid overloading one day.
    # This balances visit duration only; it cannot optimize geography without coordinates.
    ordered = sorted(
        enumerate(attractions),
        key=lambda pair: _numeric(pair[1].get("time needed to visit in hrs")) or 0.0,
        reverse=True,
    )
    for original_index, item in ordered:
        day_index = min(range(days), key=lambda index: (day_loads[index], index))
        day_groups[day_index].append((original_index, item))
        duration = _numeric(item.get("time needed to visit in hrs")) or 0.0
        day_loads[day_index] += duration

    # Keep an intuitive order where the dataset provides a preferred time of day.
    time_order = {"morning": 0, "all": 1, "afternoon": 2, "evening": 3}
    for index, group in enumerate(day_groups):
        group.sort(key=lambda pair: (
            time_order.get(str(pair[1].get("Best Time to visit") or "").strip().casefold(), 1),
            pair[0],
        ))
        day_groups[index] = [item for _, item in group]

    lines = []
    for day_number, day_items in enumerate(day_groups, start=1):
        lines.append(f"Day {day_number}:")
        if not day_items:
            lines.append("- No additional attractions were selected from the dataset.")
            continue
        for item in day_items:
            name = str(item.get("Name") or "Unnamed attraction").strip()
            details = []
            hours = _numeric(item.get("time needed to visit in hrs"))
            rating = _numeric(item.get("Google review rating"))
            best_time = item.get("Best Time to visit")
            if hours is not None and hours > 0:
                details.append(f"visit time: {hours:g} hour(s)")
            if rating is not None:
                details.append(f"dataset rating: {rating:g}/5")
            if best_time and str(best_time).strip().casefold() != "nan":
                details.append(f"dataset best time: {str(best_time).strip()}")
            suffix = f" ({'; '.join(details)})" if details else ""
            lines.append(f"- Visit {name}{suffix}")
    lines.append(
        "Planning limitation: the dataset does not include reliable coordinates, "
        "opening hours, or travel times, so this is not a distance-optimized route. "
        "Verify current hours, ticket rules, and travel time before departure."
    )
    return "\n".join(lines)


def _model_note(city: str, selected: list[dict], memories: list[dict]) -> str:
    """Return a grounded note; do not ask the LLM to invent a second itinerary."""
    if not selected:
        return f"No attractions were selected for {city}. Check the destination spelling and dataset."
    categories = []
    for item in selected:
        category = str(item.get("Type") or "").strip()
        if category and category.casefold() not in {value.casefold() for value in categories}:
            categories.append(category)
    if categories:
        note = "This plan includes a mix of " + ", ".join(categories[:4]) + " attractions from the dataset."
    else:
        note = "Use the day-by-day list as a draft, then confirm practical details before travelling."
    if memories:
        note += " Saved preferences were considered when selecting suggestions."
    note += " Check current entry fees and opening hours; dataset values may be outdated."
    return note


def plan_trip(
    prompt: str,
    user_id: str | None = None,
    include_weather: bool = False,
    previous_prompt: str | None = None,
) -> str:
    """Plan or revise a trip; follow-ups reuse the prior complete request."""
    details = resolve_trip_details(prompt, previous_prompt)
    city, people, days, budget = (
        details["city"], details["people"], details["days"], details["budget"]
    )

    memories = []
    if user_id and user_id.strip():
        memories = get_memories(user_id.strip())

    selection_prompt = f"{previous_prompt or ''}\n{prompt}"
    selected = _select_attractions(city, selection_prompt, days, memories)
    if not selected:
        return (
            f"No attractions were found for {city} in the local dataset. "
            "Check the city spelling or the data/attractions.csv file."
        )

    selected_names = [str(item["Name"]).strip() for item in selected if item.get("Name")]
    fee_result = calculate_attraction_fees(city, selected_names, people)
    if "error" in fee_result:
        return f"Could not calculate attraction fees: {fee_result['error']}"

    budget_result = calculate_budget(
        budget=budget,
        people=people,
        days=days,
        attraction_costs_per_person=fee_result["total_per_person"],
    )

    lines = [
        f"TRIP PLAN: {city}",
        f"Travellers: {people} | Duration: {days} days",
        "",
        "DAY-BY-DAY ITINERARY:",
        _build_itinerary(selected, days),
        "",
        "ATTRACTIONS AND ENTRANCE FEES:",
    ]
    for item in fee_result["attractions"]:
        if "fee_per_person" in item:
            fee_label = f"₹{item['fee_per_person']:.2f} per person"
            if item["fee_per_person"] == 0:
                fee_label += " (listed as zero in dataset; verify current ticket policy)"
            lines.append(f"- {item['name']}: {fee_label}")
        else:
            lines.append(f"- {item['name']}: fee unavailable ({item.get('error', 'unknown reason')})")

    lines.extend([
        "",
        f"Entrance fees per person: ₹{fee_result['total_per_person']:.2f}",
        f"Entrance fees for everyone: ₹{fee_result['total_for_all_people']:.2f}",
        "",
        "ESTIMATED BUDGET BREAKDOWN:",
        f"- Total budget: ₹{budget_result['budget']:.2f}",
        f"- Food: ₹{budget_result['food']:.2f}",
        f"- Transport: ₹{budget_result['transport']:.2f}",
        f"- Accommodation ({budget_result['nights']} night(s)): ₹{budget_result['accommodation']:.2f}",
        f"- Attractions: ₹{budget_result['attractions']:.2f}",
        f"- Estimated total: ₹{budget_result['estimated_total']:.2f}",
        f"- Remaining budget: ₹{budget_result['remaining']:.2f}",
        f"- Within budget: {'Yes' if budget_result['within_budget'] else 'No'}",
        "",
        "These are estimates. Dataset entrance fees may be outdated.",
        "Food, transport, and accommodation use illustrative default costs.",
    ])

    if not budget_result["within_budget"]:
        shortfall = abs(budget_result["remaining"])
        lines.extend([
            "",
            "BUDGET ALERT:",
            f"The estimate exceeds your budget by ₹{shortfall:.2f}.",
            "Consider cheaper accommodation, lower daily food/transport spending, or fewer paid attractions. "
            "The planner has not changed your stated budget or assumed discounts."
        ])
    else:
        lines.extend([
            "",
            "BUDGET NOTE:",
            f"The estimate is ₹{budget_result['remaining']:.2f} under your budget using the default assumptions. "
            "Keep a contingency for price changes and unexpected expenses."
        ])

    if memories:
        lines.extend(["", "SAVED TRAVEL PREFERENCES:"])
        lines.extend(f"- {item['memory_key']}: {item['memory_value']}" for item in memories[:10])

    if include_weather:
        lines.extend(["", "WEATHER CHECK:"])
        weather = get_weather(city)
        if "error" in weather:
            lines.append(f"Weather unavailable: {weather['error']}")
        else:
            current = weather.get("current", {})
            lines.append(
                f"Current temperature: {current.get('temperature_2m', 'N/A')}°C; "
                f"wind: {current.get('wind_speed_10m', 'N/A')} km/h."
            )
            forecast = weather.get("daily_forecast", {})
            dates = forecast.get("time", [])
            highs = forecast.get("temperature_2m_max", [])
            lows = forecast.get("temperature_2m_min", [])
            rain = forecast.get("precipitation_probability_max", [])
            for index, date in enumerate(dates):
                if index < len(highs) and index < len(lows):
                    rain_text = f", precipitation chance {rain[index]}%" if index < len(rain) else ""
                    lines.append(f"- {date}: {lows[index]}–{highs[index]}°C{rain_text}")
            lines.append("Forecasts can change; check again before travelling.")

    lines.extend([
        "",
        "PLANNING NOTE:",
        _model_note(city, selected, memories),
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print("AI Travel Planning Agent")
    print("Example: Plan a 2-day trip to Jaipur for 2 people with a budget of 8000")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.casefold() in {"exit", "quit"}:
                break
            if user_input:
                print(f"\nTravel Agent:\n{plan_trip(user_input)}\n")
        except (ValueError, TypeError) as exc:
            print(f"\nPlease check your request: {exc}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
