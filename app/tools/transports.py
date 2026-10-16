### FILE: app/tools/transport.py
"""Transportation tool providing commute cost estimation and transit recommendations."""
from app.schemas import TransportDetail

# FIX Req-6: Introduce dedicated Transportation tool as required by Problem Statement.
def estimate_transport(city: str, days: int, people: int, preference: str = "balanced") -> TransportDetail:
    """
    Estimate local transportation costs based on group size, duration, and preference.
    Preference options: 'budget' (public transit/metro), 'balanced' (autos/cabs), 'premium' (private hire).
    """
    base_rates = {
        "budget": 200.0,     # Local metro/bus network
        "balanced": 500.0,   # Auto-rickshaws and app cabs
        "premium": 1500.0,   # Dedicated chauffeur car
    }
    
    style = preference.casefold() if preference else "balanced"
    rate_per_day = base_rates.get(style, 500.0)
    
    # Scale vehicle requirements if traveling in large groups (> 4 people)
    vehicles_needed = max(1, (people + 3) // 4) if style != "budget" else 1
    total_cost = rate_per_day * days * vehicles_needed

    notes = (
        f"Based on {style} local transit ({'public transit passes' if style == 'budget' else 'rideshare/taxis'}). "
        f"Assumes {vehicles_needed} vehicle(s) for {people} traveler(s) over {days} day(s)."
    )

    return TransportDetail(
        mode=style.capitalize(),
        estimated_total_cost=round(total_cost, 2),
        notes=notes,
    )