import pytest

from app.tools.budget import calculate_budget
from app.tools.attractions import calculate_attraction_fees, search_attractions


def test_budget_calculation():
    result = calculate_budget(budget=8000, people=2, days=2, attraction_costs_per_person=185)
    assert result["food"] == 2000
    assert result["transport"] == 1000
    assert result["nights"] == 1
    assert result["accommodation"] == 1500
    assert result["attractions"] == 370
    assert result["estimated_total"] == 4870
    assert result["remaining"] == 3130
    assert result["within_budget"] is True


def test_trip_over_budget():
    result = calculate_budget(budget=3000, people=2, days=2, attraction_costs_per_person=185)
    assert result["estimated_total"] == 4870
    assert result["remaining"] == -1870
    assert result["within_budget"] is False


@pytest.mark.parametrize("kwargs", [
    {"budget": 8000, "people": 0, "days": 2},
    {"budget": -1, "people": 2, "days": 2},
    {"budget": float("nan"), "people": 2, "days": 2},
])
def test_invalid_budget_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate_budget(**kwargs)


def test_jaipur_attraction_fees():
    result = calculate_attraction_fees(
        city="Jaipur",
        attraction_names=["Hawa Mahal", "Amber Fort", "Jaigarh Fort"],
        people=2,
    )
    assert result["total_per_person"] == 185
    assert result["total_for_all_people"] == 370


def test_unknown_attraction_is_not_charged():
    result = calculate_attraction_fees("Jaipur", ["Unknown Attraction"], people=2)
    assert result["total_per_person"] == 0
    assert result["total_for_all_people"] == 0
    assert "error" in result["attractions"][0]


def test_search_attractions_case_insensitive():
    results = search_attractions("jaipur", max_results=5)
    assert results
    assert all(item["City"].casefold() == "jaipur" for item in results)


def test_search_category_filter():
    results = search_attractions("Jaipur", category="Fort", max_results=20)
    assert results
    assert all("fort" in str(item["Type"]).casefold() for item in results)


def test_search_validates_max_results():
    with pytest.raises(ValueError):
        search_attractions("Jaipur", max_results=0)
