import json
import os
import secrets
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import parse_qs, urlsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

APP_NAME = "Djibouti Music AI"
MAX_AUDIO_BYTES = 100 * 1024 * 1024
app = FastAPI(title=APP_NAME, version="0.2.0")

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


def validate_task_id(task_id: str) -> None:
    if not task_id or len(task_id) > 128 or any(
        ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in task_id
    ):
        raise HTTPException(status_code=400, detail="Invalid task identifier.")


def task_result_data(result):
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return []
    if isinstance(result, dict):
        result = [result]
    if not isinstance(result, list):
        return []
    return [item for item in result if isinstance(item, dict)]


def extract_audio_path(items: list[dict]) -> str | None:
    for item in items:
        file_ref = item.get("file")
        if not isinstance(file_ref, str):
            continue
        parsed = urlsplit(file_ref)
        # Only accept the documented relative ACE-Step audio route, never an arbitrary URL.
        if parsed.scheme or parsed.netloc or parsed.path != "/v1/audio":
            continue
        audio_path = parse_qs(parsed.query).get("path", [None])[0]
        if not audio_path or not audio_path.startswith("/") or "\x00" in audio_path:
            continue
        if ".." in PurePosixPath(audio_path).parts:
            continue
        return audio_path
    return None


async def ace_download(audio_path: str) -> tuple[bytes, str]:
    base_url, headers = upstream_config()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=120.0)) as client:
            response = await client.get(
                f"{base_url}/v1/audio",
                params={"path": audio_path},
                headers=headers,
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Audio download from ACE-Step timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"ACE-Step audio endpoint returned HTTP {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Unable to download audio from ACE-Step.") from exc

    if len(response.content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Generated audio exceeds the 100 MB download limit.")
    media_type = response.headers.get("content-type", "application/octet-stream").split(";")[0]
    if not media_type.startswith("audio/") and media_type != "application/octet-stream":
        raise HTTPException(status_code=502, detail="ACE-Step returned an unexpected audio content type.")
    return response.content, media_type


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
    validate_task_id(task_id)
    result = await ace_request("POST", "/query_result", json={"task_id_list": [task_id]})
    data = result.get("data", result) if isinstance(result, dict) else {}
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected ACE-Step task response.")

    items = task_result_data(data.get("result"))
    audio_available = bool(extract_audio_path(items))
    return {
        "task_id": task_id,
        "status": data.get("status", 0),
        "result": items,
        "audio_url": f"/api/tasks/{task_id}/audio" if audio_available else None,
    }


@app.get("/api/tasks/{task_id}/audio", dependencies=[Depends(require_app_token)])
async def download_task_audio(task_id: str):
    validate_task_id(task_id)
    result = await ace_request("POST", "/query_result", json={"task_id_list": [task_id]})
    data = result.get("data", result) if isinstance(result, dict) else {}
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict) or data.get("status") != 1:
        raise HTTPException(status_code=409, detail="Audio is not ready yet.")
    audio_path = extract_audio_path(task_result_data(data.get("result")))
    if not audio_path:
        raise HTTPException(status_code=404, detail="No downloadable audio file was returned for this task.")

    content, media_type = await ace_download(audio_path)
    suffix = PurePosixPath(audio_path).suffix.lower()
    if suffix not in {".mp3", ".wav", ".flac", ".opus", ".aac"}:
        suffix = ".audio"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="djibouti-music-{task_id}{suffix}"'},
    )
