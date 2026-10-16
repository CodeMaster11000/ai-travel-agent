import pytest

from app.agent import _build_itinerary, extract_trip_details, plan_trip


def test_extract_trip_details():
    result = extract_trip_details(
        "Plan a 2-day trip to Jaipur for 2 people with a budget of ₹8,000"
    )

    assert result == {
        "city": "Jaipur",
        "people": 2,
        "days": 2,
        "budget": 8000.0,
    }


def test_extract_trip_details_rejects_missing_fields():
    with pytest.raises(ValueError, match="destination"):
        extract_trip_details(
            "Plan a 2-day trip for 2 people with a budget of 8000"
        )


def test_itinerary_does_not_repeat_attractions():
    attractions = [
        {"Name": "Hawa Mahal"},
        {"Name": "Amber Fort"},
        {"Name": "Jaigarh Fort"},
    ]

    itinerary = _build_itinerary(attractions, 2)

    assert itinerary.count("Hawa Mahal") == 1
    assert itinerary.count("Amber Fort") == 1
    assert itinerary.count("Jaigarh Fort") == 1


def test_plan_trip_uses_deterministic_budget_and_itinerary(monkeypatch):
    # This test does not require a running Ollama model.
    import app.agent as agent

    monkeypatch.setattr(
        agent,
        "_model_note",
        lambda city, selected, memories:
            "Group nearby attractions and verify opening hours.",
    )

    plan = plan_trip(
        "Plan a 2-day trip to Jaipur for 2 people with a budget of 8000"
    )

    assert "Estimated total: ₹" in plan
    assert "DAY-BY-DAY ITINERARY:" in plan
    assert "Amber Fort" in plan
    assert "Remaining budget: ₹" in plan


def test_itinerary_uses_all_days_when_enough_attractions_exist():
    attractions = [
        {"Name": "A", "time needed to visit in hrs": 5},
        {"Name": "B", "time needed to visit in hrs": 1},
        {"Name": "C", "time needed to visit in hrs": 2},
        {"Name": "D", "time needed to visit in hrs": 1},
    ]

    itinerary = _build_itinerary(attractions, 4)

    for day in range(1, 5):
        assert f"Day {day}:" in itinerary

    for name in "ABCD":
        assert itinerary.count(f"Visit {name}") == 1


def test_plan_note_is_grounded_and_does_not_generate_a_second_itinerary():
    from app.agent import _model_note

    selected = [
        {"Name": "Siddhivinayak Temple", "Type": "Temple"},
        {"Name": "Gateway of India", "Type": "Monument"},
    ]

    note = _model_note("Mumbai", selected, [])

    assert "Temple" in note
    assert "Monument" in note
    assert "Day 1" not in note
    assert "Siddhivinayak Temple" not in note


def test_plan_shows_budget_alert_when_over_budget():
    plan = plan_trip(
        "Plan a 5 day trip to Delhi for 3 people with a budget of 10000"
    )

    assert "BUDGET ALERT:" in plan
    assert "exceeds your budget by ₹" in plan
    assert "The planner has not changed your stated budget" in plan


def test_zero_dataset_fee_is_marked_for_verification():
    plan = plan_trip(
        "Plan a 2-day trip to Mumbai for 2 people with a budget of 10000"
    )

    assert (
        "listed as zero in dataset; verify current ticket policy"
        in plan
    )