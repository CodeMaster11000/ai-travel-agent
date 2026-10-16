
import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(city: str) -> dict:
    """Get current weather and a short forecast for a city."""

    if not isinstance(city, str) or not city.strip():
        raise ValueError("Please provide a valid city name.")

    city = city.strip()

    try:
        with httpx.Client(timeout=15.0) as client:
            # Find the city's geographic coordinates.
            geo_response = client.get(
                GEOCODING_URL,
                params={
                    "name": city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            locations = geo_data.get("results", [])

            if not locations:
                return {
                    "city": city,
                    "error": "City not found. Check the spelling and try again.",
                }

            location = locations[0]
            latitude = location["latitude"]
            longitude = location["longitude"]

            # Retrieve current conditions and a daily forecast.
            weather_response = client.get(
                FORECAST_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "apparent_temperature,is_day,precipitation,"
                        "weather_code,wind_speed_10m"
                    ),
                    "daily": (
                        "weather_code,temperature_2m_max,"
                        "temperature_2m_min,precipitation_probability_max"
                    ),
                    "forecast_days": 3,
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

        return {
            "city": location.get("name", city),
            "country": location.get("country", "Unknown"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_data.get("timezone"),
            "current": weather_data.get("current", {}),
            "daily_forecast": weather_data.get("daily", {}),
            "source": "Open-Meteo",
            "note": "Forecasts can change; check again before travelling.",
        }

    except httpx.HTTPError as exc:
        return {
            "city": city,
            "error": f"Weather service request failed: {exc}",
        }


if __name__ == "__main__":
    import json

    print(json.dumps(get_weather("Jaipur"), indent=2, ensure_ascii=False))
