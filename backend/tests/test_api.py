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


def test_generation_returns_task_id(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")

    async def fake_ace_request(method, path, **kwargs):
        assert method == "POST"
        assert path == "/release_task"
        assert kwargs["json"]["batch_size"] == 1
        return {"data": {"task_id": "task-123"}}

    monkeypatch.setattr("app.main.ace_request", fake_ace_request)
    response = client.post(
        "/api/generate",
        headers={"X-App-Token": "test-secret"},
        json={"prompt": "A calm Somali oud instrumental"},
    )
    assert response.status_code == 200
    assert response.json()["task_id"] == "task-123"


def test_task_status_exposes_safe_local_audio_url(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")

    async def fake_ace_request(method, path, **kwargs):
        return {"data": [{
            "task_id": "task-123",
            "status": 1,
            "result": '[{"file":"/v1/audio?path=%2Ftmp%2Fapi_audio%2Fsong.mp3","metas":{"duration":30}}]',
        }]}

    monkeypatch.setattr("app.main.ace_request", fake_ace_request)
    response = client.get("/api/tasks/task-123", headers={"X-App-Token": "test-secret"})
    assert response.status_code == 200
    assert response.json()["audio_url"] == "/api/tasks/task-123/audio"
    assert response.json()["result"][0]["metas"]["duration"] == 30


def test_task_status_rejects_external_audio_url(monkeypatch):
    from app.main import extract_audio_path, task_result_data

    items = task_result_data('[{"file":"https://example.com/audio.mp3"}]')
    assert extract_audio_path(items) is None


def test_audio_download_requires_completed_task(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")

    async def fake_ace_request(method, path, **kwargs):
        return {"data": [{"task_id": "task-123", "status": 0, "result": "[]"}]}

    monkeypatch.setattr("app.main.ace_request", fake_ace_request)
    response = client.get("/api/tasks/task-123/audio", headers={"X-App-Token": "test-secret"})
    assert response.status_code == 409


def test_audio_download_returns_file(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "test-secret")

    async def fake_ace_request(method, path, **kwargs):
        return {"data": [{
            "task_id": "task-123",
            "status": 1,
            "result": '[{"file":"/v1/audio?path=%2Ftmp%2Fapi_audio%2Fsong.mp3"}]',
        }]}

    async def fake_ace_download(path):
        assert path == "/tmp/api_audio/song.mp3"
        return b"fake-mp3-content", "audio/mpeg"

    monkeypatch.setattr("app.main.ace_request", fake_ace_request)
    monkeypatch.setattr("app.main.ace_download", fake_ace_download)
    response = client.get("/api/tasks/task-123/audio", headers={"X-App-Token": "test-secret"})
    assert response.status_code == 200
    assert response.content == b"fake-mp3-content"
    assert response.headers["content-type"] == "audio/mpeg"
    assert "djibouti-music-task-123.mp3" in response.headers["content-disposition"]
