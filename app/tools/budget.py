### FILE: app/tools/budget.py
"""Itemized budget calculation and budget constraint evaluation."""
import math
from app.config import (
    DEFAULT_DAILY_FOOD_PER_PERSON,
    DEFAULT_ROOM_PER_NIGHT,
)
from app.schemas import BudgetBreakdown


def calculate_budget(
    budget: float,
    people: int,
    days: int,
    transport_cost: float,
    attraction_costs_per_person: float = 0.0,
    daily_food_per_person: float = DEFAULT_DAILY_FOOD_PER_PERSON,
    accommodation_per_room_per_night: float = DEFAULT_ROOM_PER_NIGHT,
    rooms: int = 1,
) -> BudgetBreakdown:
    """Calculate an itemized budget and assess viability."""
    if budget < 0 or not math.isfinite(budget):
        raise ValueError("Budget must be a non-negative finite number.")
    if people < 1 or days < 1 or rooms < 1:
        raise ValueError("People, days, and rooms must be positive integers.")

    # Calculate room nights: 1-day trips do not require overnight accommodation
    nights = max(days - 1, 0)
    accommodation = accommodation_per_room_per_night * rooms * nights
    food = daily_food_per_person * people * days
    attractions = attraction_costs_per_person * people
    estimated_total = food + transport_cost + accommodation + attractions
    remaining = budget - estimated_total
    is_within = remaining >= 0

    alert = None
    if not is_within:
        shortfall = abs(remaining)
        alert = (
            f"Estimated trip cost exceeds your budget by ₹{shortfall:.2f}. "
            f"Consider reducing hotel tier or prioritizing zero-fee public attractions."
        )

    assumptions = (
        f"Defaults: Food ₹{daily_food_per_person:.0f}/person/day; "
        f"Stay ₹{accommodation_per_room_per_night:.0f}/room/night ({nights} night(s))."
    )

    return BudgetBreakdown(
        total_budget=round(budget, 2),
        accommodation_cost=round(accommodation, 2),
        food_cost=round(food, 2),
        transport_cost=round(transport_cost, 2),
        attraction_fees=round(attractions, 2),
        estimated_total=round(estimated_total, 2),
        remaining=round(remaining, 2),
        is_within_budget=is_within,
        budget_alert=alert,
        assumptions_note=assumptions,
    )