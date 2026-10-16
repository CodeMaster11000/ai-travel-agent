"""Core planning coordinator: multi-step tool execution, scheduling, and structured plan assembly."""
import math
from app.agent.llm import generate_llm_reasoning_note
from app.agent.parser import resolve_trip_requirements
from app.schemas import (
    AttractionItem,
    DayPlan,
    TripPlanResponse,
)
from app.tools.attractions import calculate_attraction_fees, search_attractions
from app.tools.budget import calculate_budget
from app.tools.memory import get_memories
from app.tools.transports import estimate_transport
from app.tools.weather import get_weather


def _select_candidate_attractions(city: str, days: int, preferred_category: str | None, memories: list[dict]) -> list[dict]:
    """Retrieve and balance attractions from dataset based on ratings, duration, and preferences."""
    dataset_records = search_attractions(city, max_results=100)
    if not dataset_records:
        return []

    # Check preferences from SQLite memories if not specified in prompt
    effective_pref = preferred_category
    if not effective_pref and memories:
        for m in memories:
            if m.get("memory_key") in {"preferred_category", "interests", "preference"}:
                effective_pref = m.get("memory_value")
                break

    def _score(item: dict) -> float:
        score = 0.0
        try:
            score += float(item.get("Google review rating") or 0.0)
        except (ValueError, TypeError):
            pass
        if effective_pref and effective_pref.casefold() in str(item.get("Type", "")).casefold():
            score += 3.0  # Weight user preference strongly
        return score

    sorted_candidates = sorted(dataset_records, key=_score, reverse=True)

    # Pick up to 2 distinct attractions per day to maintain reasonable visit pacing
    target_count = min(len(sorted_candidates), days * 2)
    selected = []
    seen_names = set()
    for item in sorted_candidates:
        name = str(item.get("Name", "")).strip()
        if name and name.casefold() not in seen_names:
            selected.append(item)
            seen_names.add(name.casefold())
            if len(selected) >= target_count:
                break
    return selected


def _schedule_days(selected: list[dict], days: int, daily_transit_fee: float) -> list[DayPlan]:
    """Distribute attractions deterministically across days without duplicates."""
    days_list = [[] for _ in range(days)]
    for idx, item in enumerate(selected):
        day_idx = idx % days
        days_list[day_idx].append(item)

    day_plans = []
    for d_num, day_items in enumerate(days_list, start=1):
        attraction_models = []
        day_fee_sum = 0.0
        for item in day_items:
            try:
                fee = float(item.get("Entrance Fee in INR") or 0.0)
            except (ValueError, TypeError):
                fee = 0.0
            try:
                rating = float(item.get("Google review rating") or 0.0)
            except (ValueError, TypeError):
                rating = 0.0
            try:
                hours = float(item.get("time needed to visit in hrs") or 1.5)
            except (ValueError, TypeError):
                hours = 1.5

            day_fee_sum += fee
            attraction_models.append(AttractionItem(
                name=str(item.get("Name", "Attraction")),
                category=str(item.get("Type", "Sightseeing")),
                rating=rating,
                time_needed_hours=hours,
                fee_per_person=fee,
                fee_verified=(fee > 0),
                best_time=str(item.get("Best Time to visit", "All")),
            ))

        day_plans.append(DayPlan(
            day=d_num,
            theme=f"Day {d_num} Sightseeing & Culture",
            attractions=attraction_models,
            estimated_day_cost=round(day_fee_sum + daily_transit_fee, 2),
        ))
    return day_plans


def plan_trip(
    prompt: str,
    user_id: str | None = None,
    include_weather: bool = True,
    previous_prompt: str | None = None,
) -> TripPlanResponse:
    """Execute end-to-end multi-step agent planning workflow and return typed structured output."""
    requirements = resolve_trip_requirements(prompt, previous_prompt)
    city = requirements["city"]
    people = requirements["people"]
    days = requirements["days"]
    budget = requirements["budget"]
    interest = requirements["interest"]

    memories = get_memories(user_id) if user_id else []

    # Step 1: Query attraction database
    candidates = _select_candidate_attractions(city, days, interest, memories)
    if not candidates:
        raise ValueError(f"No attractions found for destination '{city}'. Check destination spelling.")

    # Step 2: Calculate verified entry fees
    attraction_names = [str(a["Name"]) for a in candidates]
    fee_data = calculate_attraction_fees(city, attraction_names, people=people)

    # Step 3: Call Transportation Service (Req-6)
    transit_info = estimate_transport(city=city, days=days, people=people)

    # Step 4: Budget computation and verification (Req-7)
    budget_breakdown = calculate_budget(
        budget=budget,
        people=people,
        days=days,
        transport_cost=transit_info.estimated_total_cost,
        attraction_costs_per_person=fee_data["total_per_person"],
    )

    # Step 5: Optional weather query & viability advisory (Req-5)
    weather_summary = get_weather(city) if include_weather else None

    # Step 6: Construct structured day plans
    daily_transit_fee = transit_info.estimated_total_cost / max(days, 1)
    day_plans = _schedule_days(candidates, days, daily_transit_fee)

    # Step 7: Synthesize analytical agent reasoning note (Req-2, Req-3)
    weather_snippet = weather_summary.forecast_snippet if weather_summary else "N/A"
    reasoning_note = generate_llm_reasoning_note(
        city=city,
        selected_attractions=candidates,
        budget_ok=budget_breakdown.is_within_budget,
        weather_info=weather_snippet,
    )

    # Step 8: Build human-readable formatted summary string alongside structured data
    summary_lines = [
        f"=== TRIP PLAN: {city.upper()} ===",
        f"Duration: {days} Days | Travelers: {people} | Budget: ₹{budget:,.2f}",
        "",
        "ITINERARY OVERVIEW:",
    ]
    for d in day_plans:
        summary_lines.append(f"Day {d.day}:")
        for a in d.attractions:
            fee_tag = f"₹{a.fee_per_person:.0f}" if a.fee_per_person > 0 else "Free / Unverified"
            summary_lines.append(f"  • {a.name} ({a.category}) - {a.time_needed_hours}h - {fee_tag}")
    
    summary_lines.extend([
        "",
        "ESTIMATED EXPENSE BREAKDOWN:",
        f"  • Accommodation: ₹{budget_breakdown.accommodation_cost:,.2f}",
        f"  • Food:          ₹{budget_breakdown.food_cost:,.2f}",
        f"  • Local Transit: ₹{budget_breakdown.transport_cost:,.2f} ({transit_info.mode})",
        f"  • Entrance Fees: ₹{budget_breakdown.attraction_fees:,.2f}",
        f"  • Total Cost:    ₹{budget_breakdown.estimated_total:,.2f}",
        f"  • Remaining:     ₹{budget_breakdown.remaining:,.2f}",
    ])

    if not budget_breakdown.is_within_budget:
        summary_lines.append(f"\n[!] BUDGET ALERT: Exceeds budget by ₹{abs(budget_breakdown.remaining):,.2f}")
    
    if weather_summary:
        summary_lines.extend([
            "",
            f"WEATHER ADVISORY ({weather_summary.city}):",
            f"  {weather_summary.forecast_snippet} - {weather_summary.outdoor_advisory}"
        ])

    summary_lines.extend(["", "AGENT NOTE:", f"  {reasoning_note}"])
    human_summary = "\n".join(summary_lines)

    return TripPlanResponse(
        city=city,
        travelers=people,
        duration_days=days,
        itinerary=day_plans,
        budget=budget_breakdown,
        weather=weather_summary,
        transportation=transit_info,
        agent_note=reasoning_note,
        human_readable_summary=human_summary,
    )