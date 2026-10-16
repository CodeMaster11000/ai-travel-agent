### FILE: tests/test_transport.py
"""Unit tests for the transportation estimation tool."""
from app.tools.transport import estimate_transport


def test_estimate_transport_default():
    result = estimate_transport("Jaipur", days=3, people=2)
    assert result.estimated_total_cost == 1500.0  # 500 * 3 days * 1 vehicle
    assert "Balanced" in result.mode


def test_estimate_transport_group_scaling():
    # 6 people require 2 vehicles for balanced/premium rideshare
    result = estimate_transport("Delhi", days=2, people=6, preference="balanced")
    assert result.estimated_total_cost == 2000.0  # 500 * 2 days * 2 vehicles