### FILE: app/tools/weather.py
"""Live weather forecast client using Open-Meteo REST API."""
import httpx
from app.schemas import WeatherSummary

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# FIX B4: Resilient timeout and structured output mapping for weather conditions.
def get_weather(city: str) -> WeatherSummary:
    """Fetch current conditions and 3-day projection for a destination city."""
    if not city or not city.strip():
        return WeatherSummary(city="Unknown", condition="Unavailable", outdoor_advisory="No city provided")

    clean_city = city.strip()
    try:
        with httpx.Client(timeout=6.0) as client:
            geo_res = client.get(
                GEOCODING_URL,
                params={"name": clean_city, "count": 1, "language": "en", "format": "json"},
            )
            geo_res.raise_for_status()
            locations = geo_res.json().get("results", [])
            if not locations:
                return WeatherSummary(
                    city=clean_city,
                    condition="Unknown",
                    outdoor_advisory="City coordinates not resolved; proceed with general seasonal planning.",
                )

            loc = locations[0]
            lat, lon = loc["latitude"], loc["longitude"]

            weather_res = client.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code,wind_speed_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "forecast_days": 3,
                    "timezone": "auto",
                },
            )
            weather_res.raise_for_status()
            w_data = weather_res.json()

            current = w_data.get("current", {})
            temp = current.get("temperature_2m")
            daily = w_data.get("daily", {})
            max_rains = daily.get("precipitation_probability_max", [0])
            peak_rain = max(max_rains) if max_rains else 0

            advisory = "Favorable conditions for outdoor sightseeing."
            if peak_rain > 50:
                advisory = f"High probability of rain ({peak_rain}% chance). Prioritize indoor museums and monuments."
            elif temp and temp > 38:
                advisory = f"High daytime temperature ({temp}°C). Schedule outdoor visits for early morning or evening."

            snippet = f"Current temp: {temp}°C, Max rain probability: {peak_rain}%."

            return WeatherSummary(
                city=loc.get("name", clean_city),
                temperature_current=temp,
                condition="Clear/Mild" if peak_rain < 40 else "Rainy/Overcast",
                forecast_snippet=snippet,
                outdoor_advisory=advisory,
            )
    except Exception as exc:
        return WeatherSummary(
            city=clean_city,
            condition="Unavailable",
            outdoor_advisory=f"Weather service temporarily unreachable ({exc}). Verify local forecasts.",
        )