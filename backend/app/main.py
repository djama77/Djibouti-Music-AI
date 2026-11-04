import os
import secrets
from typing import Literal
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, HttpUrl

APP_NAME = "Djibouti Music AI"
app = FastAPI(title=APP_NAME, version="0.1.0")

origins = [item.strip() for item in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-App-Token"],
)


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    lyrics: str = Field(default="", max_length=4000)
    duration: int = Field(default=30, ge=10, le=180)
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    vocal_language: str = Field(default="en", min_length=2, max_length=16)
    thinking: bool = False


def require_app_token(x_app_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("APP_ACCESS_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Generation is disabled: APP_ACCESS_TOKEN is not configured.")
    if not x_app_token or not secrets.compare_digest(x_app_token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing application token.")


def upstream_config() -> tuple[str, dict[str, str]]:
    base_url = os.getenv("ACESTEP_BASE_URL", "").rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="ACE-Step GPU service is not configured.")
    headers = {}
    api_key = os.getenv("ACESTEP_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return base_url, headers


async def ace_request(method: str, path: str, **kwargs):
    base_url, headers = upstream_config()
    headers.update(kwargs.pop("headers", {}))
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=90.0)) as client:
            response = await client.request(method, f"{base_url}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="ACE-Step service timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"ACE-Step service returned HTTP {exc.response.status_code}.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Unable to communicate with ACE-Step service.") from exc
    if isinstance(payload, dict) and payload.get("error"):
        raise HTTPException(status_code=502, detail="ACE-Step rejected the request.")
    return payload


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "generation_configured": bool(os.getenv("ACESTEP_BASE_URL") and os.getenv("APP_ACCESS_TOKEN")),
    }


@app.post("/api/generate", dependencies=[Depends(require_app_token)])
async def generate(request: GenerateRequest):
    payload = {
        "prompt": request.prompt,
        "lyrics": request.lyrics,
        "audio_duration": request.duration,
        "audio_format": request.audio_format,
        "vocal_language": request.vocal_language,
        "thinking": request.thinking,
        "batch_size": 1,
    }
    result = await ace_request("POST", "/release_task", json=payload)
    data = result.get("data", result) if isinstance(result, dict) else {}
    task_id = data.get("task_id") if isinstance(data, dict) else None
    if not task_id:
        raise HTTPException(status_code=502, detail="ACE-Step did not return a task identifier.")
    return {"task_id": task_id, "status": "queued"}


@app.get("/api/tasks/{task_id}", dependencies=[Depends(require_app_token)])
async def task_status(task_id: str):
    if not task_id or len(task_id) > 128 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in task_id):
        raise HTTPException(status_code=400, detail="Invalid task identifier.")
    result = await ace_request("POST", "/query_result", json={"task_id_list": [task_id]})
    data = result.get("data", result) if isinstance(result, dict) else {}
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected ACE-Step task response.")
    return {"task_id": task_id, "status": data.get("status", 0), "result": data.get("result")}
