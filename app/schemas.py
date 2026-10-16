### FILE: app/schemas.py
"""Pydantic schemas for structured input requests and output responses."""
from pydantic import BaseModel, Field


class AttractionItem(BaseModel):
    name: str = Field(..., description="Name of the attraction")
    category: str = Field(default="Sightseeing", description="Type/category of attraction")
    rating: float = Field(default=0.0, description="Google review rating out of 5")
    time_needed_hours: float = Field(default=1.5, description="Recommended visit time in hours")
    fee_per_person: float = Field(default=0.0, description="Entrance fee per person in INR")
    fee_verified: bool = Field(default=True, description="False if fee is 0 or uncertain")
    best_time: str = Field(default="All", description="Recommended time of day to visit")


class DayPlan(BaseModel):
    day: int = Field(..., description="Day index starting at 1")
    theme: str = Field(default="Exploration", description="Theme for the day")
    attractions: list[AttractionItem] = Field(default_factory=list, description="Scheduled attractions")
    estimated_day_cost: float = Field(default=0.0, description="Total expected day expenses in INR")


class BudgetBreakdown(BaseModel):
    total_budget: float
    accommodation_cost: float
    food_cost: float
    transport_cost: float
    attraction_fees: float
    estimated_total: float
    remaining: float
    is_within_budget: bool
    budget_alert: str | None = None
    assumptions_note: str


class WeatherSummary(BaseModel):
    city: str
    temperature_current: float | None = None
    condition: str = Field(default="Clear", description="General weather summary")
    forecast_snippet: str = Field(default="", description="3-day projection")
    outdoor_advisory: str = Field(default="", description="Advisory regarding weather viability")


class TransportDetail(BaseModel):
    mode: str
    estimated_total_cost: float
    notes: str


class TripPlanResponse(BaseModel):
    city: str
    travelers: int
    duration_days: int
    itinerary: list[DayPlan]
    budget: BudgetBreakdown
    weather: WeatherSummary | None = None
    transportation: TransportDetail
    agent_note: str
    human_readable_summary: str


class TripRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Trip request or revision update.")
    previous_prompt: str | None = Field(default=None, max_length=2000, description="Prior conversation context for revisions.")
    user_id: str | None = Field(default=None, max_length=200)
    include_weather: bool = Field(default=True)


class AttractionSearchRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    max_results: int = Field(default=10, ge=1, le=100)


class MemorySaveRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=500)
    value: str = Field(..., min_length=1, max_length=500)


class MemoryQueryRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    key: str | None = Field(default=None, max_length=500)