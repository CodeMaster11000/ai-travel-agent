### FILE: app/agent/parser.py
"""Natural language request parsing and conversational revision resolver."""
import math
import re

# FIX B3: Robust regex parser that handles missing parameters with sensible defaults.
def extract_trip_updates(prompt: str) -> dict:
    """Extract whatever travel attributes are stated in the traveler's prompt."""
    if not prompt or not prompt.strip():
        return {}

    updates = {}
    
    # Destination capture: handles 'trip to Jaipur', 'visit Delhi', or isolated names
    city_match = re.search(
        r"\b(?:trip\s+(?:to|across|in)|travel\s+to|visit|destination\s+(?:is|to)|in|exploring)\s+"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"(?=\s+(?:for|with|on|under|within|budget|and|from|to)\b|[,.;\n]|$)",
        prompt,
        re.IGNORECASE,
    )
    if city_match:
        updates["city"] = city_match.group(1).strip(" .'-")

    # Traveler count capture
    people_match = re.search(r"\b(\d+)\s*(?:people|persons|travellers|travelers|adults|friends)\b", prompt, re.IGNORECASE)
    if people_match:
        updates["people"] = int(people_match.group(1))

    # Duration capture
    days_match = re.search(r"\b(\d+)\s*[- ]?day(?:s)?\b", prompt, re.IGNORECASE)
    if days_match:
        updates["days"] = int(days_match.group(1))

    # Budget capture
    budget_match = re.search(
        r"(?:budget(?:\s+(?:of|to|is|by))?|increase\s+(?:the\s+)?budget\s+to|"
        r"raise\s+(?:the\s+)?budget\s+to|under|within|spend(?:ing)?\s+of)\s*"
        r"(?:₹|INR\s*|Rs\.?\s*)?([\d,]+(?:\.\d{1,2})?)",
        prompt, re.IGNORECASE,
    )
    if budget_match:
        updates["budget"] = float(budget_match.group(1).replace(",", ""))

    # Category / Interest capture
    interest_match = re.search(
        r"\b(?:interested in|focus on|preference for|prefer|want to see)\s+([A-Za-z]+)\b",
        prompt, re.IGNORECASE,
    )
    if interest_match:
        updates["interest"] = interest_match.group(1).strip()

    return updates


def resolve_trip_requirements(prompt: str, previous_prompt: str | None = None) -> dict:
    """
    Combine prior session state with latest user input, filling defaults for missing MVP fields.
    """
    current_updates = extract_trip_updates(prompt)
    merged = {}

    if previous_prompt:
        merged.update(extract_trip_updates(previous_prompt))
    merged.update(current_updates)

    # City is the only strictly required non-defaultable parameter
    city = merged.get("city")
    if not city:
        # Fallback: check if prompt is just a city name
        single_word = prompt.strip().split()
        if len(single_word) <= 2 and single_word[0].isalpha():
            city = prompt.strip()
        else:
            raise ValueError("Please provide a destination city (e.g. 'trip to Jaipur').")

    people = merged.get("people", 2) # Default: 2 travelers
    days = merged.get("days", 3)     # Default: 3-day itinerary
    budget = merged.get("budget")

    # If traveler specified 'budget-friendly' or left budget unstated, infer an affordable ceiling
    if budget is None:
        budget = float(people * days * 2500)  # ₹2,500/day/person sensible default

    if people < 1 or days < 1 or budget < 0 or not math.isfinite(budget):
        raise ValueError("Travelers and days must be positive numbers; budget must be non-negative.")

    return {
        "city": city.title(),
        "people": people,
        "days": min(days, 14), # Cap at 14 days for MVP
        "budget": budget,
        "interest": merged.get("interest"),
    }