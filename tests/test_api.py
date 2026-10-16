from fastapi.testclient import TestClient

from app.main import app
import app.agent as agent

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_attractions_endpoint():
    response = client.post("/attractions", json={"city": "Jaipur", "max_results": 5})
    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_plan_endpoint(monkeypatch):
    monkeypatch.setattr(agent, "_model_note", lambda city, selected, memories: "Verify opening hours.")
    response = client.post("/plan", json={
        "prompt": "Plan a 2-day trip to Jaipur for 2 people with a budget of 8000"
    })
    assert response.status_code == 200
    assert "TRIP PLAN: Jaipur" in response.json()["plan"]


def test_plan_endpoint_rejects_missing_details():
    response = client.post("/plan", json={"prompt": "I want to travel"})
    assert response.status_code == 400
