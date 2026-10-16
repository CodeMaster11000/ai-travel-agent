# 🌿 WanderAI — Agentic AI Travel Planner

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/Gradio-5.0+-orange.svg)](https://gradio.app/)
[![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:3b-black.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

WanderAI is an agentic travel planning system built with **FastAPI**, **Gradio**, **Ollama LLM function calling**, a **verified Indian attractions dataset**, live **Open-Meteo weather**, and thread-safe **SQLite session memory**.

Give it a prompt like *"Plan a 3-day trip to Jaipur for 2 people with a budget of 12000"* and the agent extracts your requirements, builds a non-overlapping day-by-day itinerary, checks live weather, computes a transparent itemized budget, and lets you refine the plan conversationally.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#️-system-architecture)
- [Project Structure](#-project-structure)
- [Installation Guide](#-installation-guide)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Create a virtual environment](#2-create-a-virtual-environment)
  - [3. Configure environment variables](#3-configure-environment-variables)
  - [4. Install Ollama and the Qwen model](#4-install-ollama-and-the-qwen-model)
- [Running the Services](#-running-the-services)
- [API Reference](#-api-reference--examples)
- [Testing](#-testing)
- [Configuration](#️-configuration)
- [Troubleshooting](#-troubleshooting)
- [Notes & Assumptions](#️-notes--assumptions)
- [License](#-license)

---

## 🌟 Key Features

1. **Multi-step agent reasoning & planning**
   - Breaks a traveler's request into coordinated tool calls: attraction retrieval, fee auditing, transit estimation, weather verification, and budget balancing.
   - Uses a local LLM through **Ollama** (`qwen2.5:3b`) with declarative tool-calling schemas, plus a heuristic fallback engine when Ollama is unavailable.
2. **Itemized financial breakdown ("Where Every Rupee Goes")**
   - **Multi-segment spend bar** showing the split across Lodging, Dining, Transit, and Sightseeing.
   - **Line-by-line cost ledger** with unit prices, traveler counts, and totals for each attraction ticket, meal, and hotel night.
3. **Adaptive light / dark interface**
   - A **Nordic Mint & Sky** light palette with an automatic **Obsidian Emerald** dark theme based on system/browser preference.
   - Timeline attraction badges, duration pills, star ratings, and best visiting hours.
4. **Verified local attraction dataset**
   - 600+ curated Indian destinations across Delhi, Mumbai, Jaipur, Kerala, Goa, West Bengal, and more.
   - Includes opening hours, category tags, review ratings, and entrance fees.
5. **Live weather & viability advisory**
   - Queries Open-Meteo's geocoding and forecast APIs for current temperature and rain probability, then gives an actionable outdoor advisory.
6. **Persistent SQLite memory**
   - Stores traveler preferences (e.g. `preferred_category = Fort`, `dietary = Vegetarian`) in a WAL-enabled SQLite database to guide future recommendations.
7. **Type-safe REST API**
   - Full OpenAPI / Swagger documentation with Pydantic v2 structured output schemas.

---

## 🏗️ System Architecture

```text
              User Prompt (Gradio UI or REST API)
                            │
                            ▼
                    app.agent.parser
        (extracts city, duration, budget, travelers)
                            │
                            ▼
                     app.agent.core
          (coordinates multi-step tool execution)
   ┌───────────┬─────────────┼─────────────┬───────────┐
   ▼           ▼             ▼             ▼           ▼
Attractions  Transport     Weather       Budget      Memory
   Tool        Tool      Tool (Live)      Tool        Tool
(data/*.csv)  (Modes)    (Open-Meteo)    (Ledger)    (SQLite)
   └───────────┴─────────────┴─────────────┴───────────┘
                            │
                            ▼
          app.agent.llm (Ollama / heuristic fallback)
                            │
                            ▼
             Structured Output (TripPlanResponse)
              ├── Day-by-day timeline
              ├── Itemized budget & category bar
              ├── Weather advisory
              └── Human-readable summary
```

---

## 📦 Project Structure

```text
ai-travel-planner/
├── app/
│   ├── __init__.py
│   ├── config.py            # Central configuration & paths
│   ├── schemas.py           # Pydantic models for structured output
│   ├── main.py              # FastAPI application (OpenAPI docs)
│   ├── ui.py                # Gradio web portal (light/dark themes)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py          # Agent orchestrator & day-by-day scheduler
│   │   ├── parser.py        # Request parser & revision resolver
│   │   └── llm.py           # Ollama function calling & synthesis
│   └── tools/
│       ├── __init__.py
│       ├── attractions.py   # Cached CSV lookup & fee verification
│       ├── budget.py        # Itemized cost calculations & alerts
│       ├── transport.py     # Transit mode selector & commute estimator
│       ├── weather.py       # Open-Meteo geocoding & forecast client
│       └── memory.py        # Thread-safe SQLite (WAL) persistent store
├── data/
│   └── attractions.csv      # Indian attractions dataset (600+ records)
├── tests/
│   ├── __init__.py
│   ├── test_agent.py        # Planning, parsing, and revision tests
│   ├── test_api.py          # Endpoint & schema tests
│   ├── test_budget.py       # Fee & budget edge-case tests
│   ├── test_memory.py       # Persistence & concurrency tests
│   └── test_transport.py    # Transport calculation tests
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── run_api.sh               # Launch the FastAPI server
├── run_ui.sh                # Launch the Gradio web UI
└── setup.sh                 # Setup script
```

---

## 🚀 Installation Guide

### Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.11+** | Check with `python3 --version` |
| **Git** | To clone the repository |
| **Ollama** *(optional but recommended)* | Runs the Qwen model locally for LLM reasoning |
| **~4 GB free RAM and ~2 GB disk** | For `qwen2.5:3b` (the model download is roughly 1.9 GB) |

> 💡 Ollama is optional. Without it, WanderAI falls back to grounded heuristic synthesis and still produces full itineraries, budgets, and weather advisories.

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-travel-planner.git
cd ai-travel-planner
```

### 2. Create a virtual environment

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Make sure `.env` contains:

```env
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_HOST=http://localhost:11434
```

### 4. Install Ollama and the Qwen model

WanderAI uses **Qwen 2.5 (3B)** through Ollama for tool calling and itinerary synthesis.

#### Step 4.1 — Install Ollama

**Linux**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS**

Download the installer from [ollama.com/download](https://ollama.com/download), or use Homebrew:

```bash
brew install ollama
```

**Windows**

Download and run the installer from [ollama.com/download](https://ollama.com/download).

Verify the installation:

```bash
ollama --version
```

#### Step 4.2 — Start the Ollama server

```bash
ollama serve
```

> The macOS and Windows desktop apps start the server automatically in the background. On Linux, the install script usually sets it up as a systemd service. If you get a "port already in use" message, Ollama is already running and you can skip this step.

#### Step 4.3 — Download the Qwen model

In a new terminal:

```bash
ollama pull qwen2.5:3b
```

This downloads the model (about 1.9 GB) the first time only.

#### Step 4.4 — Verify the model works

```bash
# List installed models (qwen2.5:3b should appear)
ollama list

# Quick interactive test (type /bye to exit)
ollama run qwen2.5:3b
```

You can also confirm the API is reachable, which is the endpoint WanderAI uses:

```bash
curl http://localhost:11434/api/tags
```

#### Using a different model (optional)

Any Ollama model with tool-calling support can be swapped in. Pull it, then update `OLLAMA_MODEL` in `.env`:

```bash
ollama pull qwen2.5:7b
```

```env
OLLAMA_MODEL=qwen2.5:7b
```

Larger models give better reasoning but need more RAM.

---

## 💻 Running the Services

### Gradio Web Portal (recommended)

```bash
python -m app.ui
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser.

**What's in the UI**

- **Itinerary & Cost Planner tab** — configure trips or request revisions (e.g. *"increase budget to 15000 and focus on forts"*).
- **Where the Money Goes** — multi-segment spending bar and itemized expense ledger.
- **Attraction & Fee Explorer tab** — filter the attractions database by city and category.
- **Traveler Profile & Memory tab** — store and inspect preferences saved in SQLite.
- **Light / Dark theme** — switches automatically with your system or browser preference.

### FastAPI REST Backend

In a separate terminal:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| Resource | URL |
|---|---|
| Swagger docs | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/health |

You can also use the helper scripts: `./run_ui.sh` and `./run_api.sh`.

---

## 📡 API Reference & Examples

### 1. Plan a trip — `POST /plan`

**Request**

```bash
curl -X POST "http://127.0.0.1:8000/plan" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Plan a 3-day trip to Jaipur for 2 people with a budget of 12000",
       "user_id": "traveler_one",
       "include_weather": true
     }'
```

**Response** *(truncated)*

```json
{
  "city": "Jaipur",
  "travelers": 2,
  "duration_days": 3,
  "itinerary": [
    {
      "day": 1,
      "theme": "Day 1 Sightseeing & Culture",
      "attractions": [
        {
          "name": "Amber Fort",
          "category": "Fort",
          "rating": 4.6,
          "time_needed_hours": 2.0,
          "fee_per_person": 100.0,
          "fee_verified": true,
          "best_time": "All"
        }
      ],
      "estimated_day_cost": 600.0
    }
  ],
  "budget": {
    "total_budget": 12000.0,
    "accommodation_cost": 3000.0,
    "food_cost": 3000.0,
    "transport_cost": 1500.0,
    "attraction_fees": 370.0,
    "estimated_total": 7870.0,
    "remaining": 4130.0,
    "is_within_budget": true,
    "budget_alert": null,
    "assumptions_note": "Defaults: Food ₹500/person/day; Stay ₹1500/room/night (2 night(s))."
  },
  "weather": {
    "city": "Jaipur",
    "temperature_current": 26.4,
    "condition": "Clear/Mild",
    "forecast_snippet": "Current temp: 26.4°C, Max rain probability: 0%.",
    "outdoor_advisory": "Favorable conditions for outdoor sightseeing."
  },
  "transportation": {
    "mode": "Balanced",
    "estimated_total_cost": 1500.0,
    "notes": "Based on balanced local transit (rideshare/taxis)."
  },
  "agent_note": "This itinerary arranges a curated balance of Fort, Palace in Jaipur. The plan aligns with your financial budget.",
  "human_readable_summary": "=== TRIP PLAN: JAIPUR ===\n..."
}
```

### 2. Search attractions — `POST /attractions`

```bash
curl -X POST "http://127.0.0.1:8000/attractions" \
     -H "Content-Type: application/json" \
     -d '{
       "city": "Jaipur",
       "category": "Fort",
       "max_results": 5
     }'
```

### 3. Save a traveler preference — `POST /memory/save`

```bash
curl -X POST "http://127.0.0.1:8000/memory/save" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "traveler_one",
       "key": "preferred_category",
       "value": "Fort"
     }'
```

---

## 🧪 Testing

```bash
# Run all unit and integration tests
pytest -v

# Run with a coverage report
pytest --cov=app tests/
```

| Test file | Covers |
|---|---|
| `test_agent.py` | Requirement extraction, conversational revisions, scheduling uniqueness |
| `test_api.py` | Endpoint schema validation and response structure |
| `test_budget.py` | Cost formulas, deficit alerts, ticket fee calculations |
| `test_memory.py` | SQLite persistence, update-in-place, case-insensitivity |
| `test_transport.py` | Group size scaling and vehicle allocation |

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:3b` | Ollama model name |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service base URL |
| `DEFAULT_DAILY_FOOD_PER_PERSON` | `500.0` | Default daily food allocation (INR) |
| `DEFAULT_ROOM_PER_NIGHT` | `1500.0` | Default hotel room rate (INR) |
| `MEMORY_DB_FILE` | `data/travel_memory.db` | SQLite database path |
| `ATTRACTIONS_FILE` | `data/attractions.csv` | Path to the attractions CSV dataset |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` on port 11434 | Ollama isn't running. Start it with `ollama serve`. WanderAI will use the heuristic fallback in the meantime. |
| `model "qwen2.5:3b" not found` | Run `ollama pull qwen2.5:3b` and confirm it appears in `ollama list`. |
| Model name in `.env` doesn't match | `OLLAMA_MODEL` must exactly match a name shown in `ollama list`. |
| Slow responses or out-of-memory errors | The 3B model needs about 4 GB RAM. Close other heavy apps, or rely on the heuristic fallback. |
| `Address already in use` (port 7860 / 8000) | Stop the other process, or run on a different port. |
| `ModuleNotFoundError: app` | Run commands from the project root with the virtual environment activated. |
| Weather section is empty | Open-Meteo needs internet access. Check your connection. The rest of the plan still works offline. |

---

## ⚠️ Notes & Assumptions

- **Illustrative cost estimates:** accommodation, local food, and taxi costs are configurable baseline defaults, not live prices.
- **Dataset currency:** attraction admission fees and timings come from `data/attractions.csv`. Verify current policies with the official monuments before you travel.
- **Single-day trips:** for 1-day itineraries (`duration_days = 1`), hotel cost is calculated as 0 nights (₹0.00).

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.