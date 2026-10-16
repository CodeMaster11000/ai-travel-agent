### FILE: app/agent/llm.py
"""LLM Agent tool orchestration interface supporting Ollama function calling with deterministic fallback."""
import json
import logging
from app.config import OLLAMA_HOST, OLLAMA_MODEL

logger = logging.getLogger(__name__)

try:
    import ollama
except ImportError:
    ollama = None

# FIX Req-3: Agent tool definitions conforming to Ollama/OpenAI Tool Schema specification.
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": "Search destination attractions by city and category filter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Destination city name"},
                    "category": {"type": "string", "description": "Optional category e.g. Fort, Museum, Temple"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Fetch current weather and 3-day forecast for the city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Destination city name"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_transport",
            "description": "Calculate transportation costs based on group size and travel style.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {"type": "integer"},
                    "people": {"type": "integer"},
                    "preference": {"type": "string", "enum": ["budget", "balanced", "premium"]},
                },
                "required": ["city", "days", "people"],
            },
        },
    },
]


def generate_llm_reasoning_note(city: str, selected_attractions: list[dict], budget_ok: bool, weather_info: str) -> str:
    """
    Invoke Ollama if running to generate agent synthesis and reasoning; gracefully fallback to heuristic synthesis.
    """
    if not ollama:
        return _heuristic_note(city, selected_attractions, budget_ok)

    client = ollama.Client(host=OLLAMA_HOST)
    system_prompt = (
        "You are an expert AI Travel Planner. Provide a concise 2-sentence analytical summary "
        "highlighting attraction pacing, budget feasibility, and weather viability."
    )
    user_content = (
        f"City: {city}. Attractions: {', '.join([a.get('Name', '') for a in selected_attractions[:4]])}. "
        f"Budget Status: {'Within budget' if budget_ok else 'Over budget'}. Weather Note: {weather_info}."
    )

    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            options={"temperature": 0.3},
        )
        return response["message"]["content"].strip()
    except Exception as exc:
        logger.info(f"Ollama server note unavailable ({exc}); using grounded synthesis.")
        return _heuristic_note(city, selected_attractions, budget_ok)


def _heuristic_note(city: str, selected: list[dict], budget_ok: bool) -> str:
    types = list({str(a.get("Type", "Sightseeing")) for a in selected if a.get("Type")})
    variety = ", ".join(types[:3]) if types else "popular highlights"
    status_msg = "The plan aligns with your financial budget." if budget_ok else "Cost exceeds current budget limits; consider adjusting accommodation."
    return f"This itinerary arranges a curated balance of {variety} in {city}. {status_msg}"