import math


def calculate_budget(
    budget: float,
    people: int,
    days: int,
    daily_food_per_person: float = 500,
    daily_transport_total: float = 500,
    accommodation_per_room_per_night: float = 1500,
    rooms: int = 1,
    attraction_costs_per_person: float = 0,
) -> dict:
    """Calculate a transparent estimate using configurable default costs."""
    values = {
        "budget": budget,
        "daily_food_per_person": daily_food_per_person,
        "daily_transport_total": daily_transport_total,
        "accommodation_per_room_per_night": accommodation_per_room_per_night,
        "attraction_costs_per_person": attraction_costs_per_person,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a non-negative number.")

    for name, value in {"people": people, "days": days, "rooms": rooms}.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    food = daily_food_per_person * people * days
    transport = daily_transport_total * days
    nights = max(days - 1, 0)
    accommodation = accommodation_per_room_per_night * rooms * nights
    attractions = attraction_costs_per_person * people
    total = food + transport + accommodation + attractions

    return {
        "budget": round(budget, 2),
        "food": round(food, 2),
        "transport": round(transport, 2),
        "nights": nights,
        "accommodation": round(accommodation, 2),
        "attractions": round(attractions, 2),
        "estimated_total": round(total, 2),
        "remaining": round(budget - total, 2),
        "within_budget": total <= budget,
        "assumptions": (
            "Food, transport, and accommodation are illustrative defaults, not live prices. "
            "Entrance fees come from the local dataset and may be outdated."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(calculate_budget(
        budget=8000, people=2, days=2, attraction_costs_per_person=185
    ), indent=2))
