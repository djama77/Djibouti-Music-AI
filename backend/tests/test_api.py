from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_available():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generation_requires_configured_token(monkeypatch):
    monkeypatch.delenv("APP_ACCESS_TOKEN", raising=False)
    response = client.post("/api/generate", json={"prompt": "A calm Somali oud instrumental"})
    assert response.status_code == 503


def test_generation_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")
    response = client.post("/api/generate", json={"prompt": "A calm Somali oud instrumental"})
    assert response.status_code == 401


def test_generation_validates_prompt(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")
    response = client.post(
        "/api/generate",
        headers={"X-App-Token": "test-secret"},
        json={"prompt": "x"},
    )
    assert response.status_code == 422
