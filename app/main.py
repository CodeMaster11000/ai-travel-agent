from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import plan_trip
from app.tools.attractions import search_attractions
from app.tools.memory import delete_memory, get_memories, save_memory
from app.tools.weather import get_weather

app = FastAPI(
    title="AI Travel Planning Agent",
    description="Travel planning with a local LLM, attraction data, budget tools, weather, and SQLite memory.",
    version="1.1.0",
)


class TripRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Trip request or follow-up update.")
    previous_prompt: str | None = Field(default=None, max_length=2000, description="Previous complete trip request for follow-ups.")
    user_id: str | None = Field(default=None, max_length=200)
    include_weather: bool = False


class AttractionRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    max_results: int = Field(default=10, ge=1, le=100)


class WeatherRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)


class MemoryRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=500)
    value: str = Field(..., min_length=1, max_length=500)


class MemoryLookupRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    key: str | None = Field(default=None, max_length=500)


@app.get("/")
def home():
    return {
        "message": "AI Travel Planning Agent API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/plan")
def create_trip(request: TripRequest):
    try:
        return {
            "plan": plan_trip(
                request.prompt,
                user_id=request.user_id,
                include_weather=request.include_weather,
                previous_prompt=request.previous_prompt,
            )
        }
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The travel plan could not be generated.") from exc


@app.post("/attractions")
def attractions(request: AttractionRequest):
    try:
        results = search_attractions(request.city, request.category, request.max_results)
        return {"city": request.city, "count": len(results), "attractions": results}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/weather")
def weather(request: WeatherRequest):
    result = get_weather(request.city)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/memory/save")
def memory_save(request: MemoryRequest):
    try:
        return save_memory(request.user_id, request.key, request.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/get")
def memory_get(request: MemoryLookupRequest):
    try:
        memories = get_memories(request.user_id)
        if request.key:
            memories = [item for item in memories if item["memory_key"] == request.key.casefold()]
        return {"user_id": request.user_id, "memories": memories}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/delete")
def memory_delete(request: MemoryLookupRequest):
    if not request.key:
        raise HTTPException(status_code=422, detail="A memory key is required.")
    try:
        return delete_memory(request.user_id, request.key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
