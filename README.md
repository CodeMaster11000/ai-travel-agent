# AI Travel Planning Agent

A local-first travel planning MVP built with Python, FastAPI, Gradio, Ollama/Qwen, a CSV attractions dataset, Open-Meteo weather, and SQLite memory.

## Features

- **Trip planning:** extracts destination, duration, traveller count, and budget from a prompt.
- **Attraction search:** searches `data/attractions.csv`; optional category filtering.
- **Entrance-fee calculator:** sums exact dataset matches and flags missing/unknown fees.
- **Budget estimator:** computes food, transport, accommodation, and entrance-fee estimates in Python.
- **Itinerary builder:** schedules dataset-backed attractions without repeating them; the LLM is used for a short planning note rather than trusted for prices.
- **Weather:** optional current conditions and three-day forecast from Open-Meteo.
- **Persistent memory:** save, read, and delete preferences by user ID in SQLite.
- **REST API:** FastAPI endpoints with interactive Swagger docs.
- **Web interface:** Gradio tabs for planning, attraction search, weather, and memory.
- **Tests:** pytest coverage for calculations, dataset lookup, input parsing, itinerary uniqueness, and memory.

## Requirements

- Fedora/Linux, macOS, or Windows with Python 3.11+ recommended.
- Internet access for installing dependencies and retrieving weather.
- [Ollama](https://ollama.com/) installed and running for the local LLM note. The rest of the core plan uses Python and remains usable if the model is unavailable.
- The included dataset is local; attraction fees may be outdated.

## Setup on Fedora

From the extracted project directory:

```bash
chmod +x setup.sh run_api.sh run_ui.sh
./setup.sh
```

Install/start Ollama separately, then pull the configured model:

```bash
ollama pull qwen2.5:3b
ollama list
```

If Ollama is not running as a service, start it in another terminal with:

```bash
ollama serve
```

The setup script copies `.env.example` to `.env`. Edit `.env` if you use a different model or Ollama host.

## Run the project

Start the API in terminal 1:

```bash
./run_api.sh
```

- API home: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

Start the UI in terminal 2:

```bash
./run_ui.sh
```

- Gradio: http://127.0.0.1:7860

You can also run `python -m app.main` only through Uvicorn (recommended) and `python -m app.ui` for the UI.

## Example trip request

In the Gradio chat or `POST /plan`:

```json
{
  "prompt": "Plan a 2-day trip to Jaipur for 2 people with a budget of 8000",
  "user_id": "traveller_1",
  "include_weather": false
}
```

Use `include_weather: true` to include the current conditions and forecast in the plan. Saved preferences such as `preferred_category=Fort` can influence the default attraction selection when the prompt does not name specific places.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Basic health check |
| POST | `/plan` | Generate trip plan |
| POST | `/attractions` | Search the local dataset |
| POST | `/weather` | Fetch current conditions and forecast |
| POST | `/memory/save` | Save/update a preference |
| POST | `/memory/get` | Retrieve preferences |
| POST | `/memory/delete` | Delete a preference |

### Example requests

```json
POST /attractions
{
  "city": "Jaipur",
  "category": "Fort",
  "max_results": 10
}
```

```json
POST /memory/save
{
  "user_id": "traveller_1",
  "key": "preferred_category",
  "value": "Fort"
}
```

## Tests

```bash
source .venv/bin/activate
python -m pytest -v
```

The tests do not require live weather or an active Ollama model.

## Dataset and estimates

The attraction dataset is provided with this project and is searched locally. Its entry fees, ratings, best-time labels, and visit durations may be stale or incomplete; verify them with official sources before travelling. Food, transport, and accommodation costs are illustrative defaults, not live quotes. The budget model assumes one room and `days - 1` overnight stays by default.

## Notes

- `.env` and the generated SQLite database are ignored by Git.
- Do not commit API keys, personal data, or the generated memory database.
- The app binds to `127.0.0.1` by default, so it is intended for local development.
