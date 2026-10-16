### FILE: app/main.py
"""FastAPI application exposing structured endpoints and interactive OpenAPI docs."""
from fastapi import FastAPI, HTTPException
from app.agent.core import plan_trip
from app.schemas import (
    AttractionSearchRequest,
    MemoryQueryRequest,
    MemorySaveRequest,
    TripPlanResponse,
    TripRequest,
)
from app.tools.attractions import search_attractions
from app.tools.memory import delete_memory, get_memories, save_memory
from app.tools.weather import get_weather

app = FastAPI(
    title="AI Travel Planning Agent",
    description="Agentic travel planning with function calling, tool execution, and structured outputs.",
    version="2.0.0",
)


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "AI Travel Planning Agent",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# FIX B6: Return typed Pydantic response (TripPlanResponse) fulfilling Req-10.
@app.post("/plan", response_model=TripPlanResponse)
def create_trip(request: TripRequest):
    try:
        return plan_trip(
            prompt=request.prompt,
            user_id=request.user_id,
            include_weather=request.include_weather,
            previous_prompt=request.previous_prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Planning execution failed: {exc}") from exc


@app.post("/attractions")
def attractions(request: AttractionSearchRequest):
    try:
        results = search_attractions(request.city, request.category, request.max_results)
        return {"city": request.city, "count": len(results), "attractions": results}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/weather")
def weather(city: str):
    summary = get_weather(city)
    return summary.model_dump()


@app.post("/memory/save")
def memory_save(request: MemorySaveRequest):
    try:
        return save_memory(request.user_id, request.key, request.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/get")
def memory_get(request: MemoryQueryRequest):
    try:
        memories = get_memories(request.user_id)
        if request.key:
            memories = [m for m in memories if m["memory_key"] == request.key.casefold()]
        return {"user_id": request.user_id, "memories": memories}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/delete")
def memory_delete(request: MemoryQueryRequest):
    if not request.key:
        raise HTTPException(status_code=422, detail="A memory_key is required for deletion.")
    try:
        return delete_memory(request.user_id, request.key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc