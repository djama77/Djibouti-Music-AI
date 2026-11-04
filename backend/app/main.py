from __future__ import annotations
import json, os
from typing import Any
from urllib.parse import urljoin
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Djibouti Music AI API", version="0.1.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["Content-Type","X-App-Access-Key"])

def require_demo_key(x_app_access_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("APP_ACCESS_KEY", "")
    if not expected: raise HTTPException(status_code=503, detail="APP_ACCESS_KEY is not configured.")
    if not x_app_access_key or x_app_access_key != expected: raise HTTPException(status_code=401, detail="Invalid or missing access key.")

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=512)
    lyrics: str = Field(default="", max_length=4096)
    language: str = Field(default="fr", pattern=r"^(so|aa|fr|ar|en)$")
    genre: str = Field(default="Afrobeat", max_length=80)
    duration: int = Field(default=60, ge=10, le=300)
    audio_format: str = Field(default="mp3", pattern=r"^(mp3|wav)$")
    instrumental: bool = False
    @field_validator("prompt","lyrics","genre")
    @classmethod
    def trim_text(cls, value: str) -> str: return value.strip()

class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str

def _unwrap(payload: dict[str, Any]) -> Any:
    if payload.get("error"): raise HTTPException(status_code=502, detail=str(payload["error"]))
    if payload.get("code", 200) not in (200,0): raise HTTPException(status_code=502, detail="ACE-Step returned an unsuccessful response.")
    return payload.get("data", payload)

def _ace_headers() -> dict[str,str]:
    key=os.getenv("ACE_STEP_API_KEY","").strip()
    return {"Authorization":f"Bearer {key}"} if key else {}

def _ace_url(path: str) -> str:
    return urljoin(os.getenv("ACESTEP_API_URL","http://localhost:8001").rstrip("/")+"/", path.lstrip("/"))

@app.get("/health")
async def health(): return {"status":"ok","service":"djibouti-music-ai-api"}

@app.post("/api/generate", response_model=GenerateResponse, dependencies=[Depends(require_demo_key)])
async def generate(body: GenerateRequest):
    payload={"prompt":f"{body.genre}, {body.prompt}","lyrics":"[Instrumental]" if body.instrumental else body.lyrics,"vocal_language":body.language,"audio_duration":body.duration,"audio_format":body.audio_format,"task_type":"text2music","thinking":True,"use_cot_caption":True,"use_cot_language":True,"batch_size":1}
    try:
        async with httpx.AsyncClient(timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS","30"))) as client:
            response=await client.post(_ace_url("/release_task"),json=payload,headers=_ace_headers()); response.raise_for_status(); data=_unwrap(response.json())
    except httpx.HTTPError as exc: raise HTTPException(status_code=502,detail=f"ACE-Step service unavailable: {exc.__class__.__name__}") from exc
    task_id=data.get("task_id") if isinstance(data,dict) else None
    if not task_id: raise HTTPException(status_code=502,detail="ACE-Step response did not contain a task_id.")
    return GenerateResponse(task_id=str(task_id),status=str(data.get("status","queued")),message="Generation queued.")

@app.get("/api/jobs/{task_id}", dependencies=[Depends(require_demo_key)])
async def job_status(task_id: str):
    try:
        async with httpx.AsyncClient(timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS","30"))) as client:
            response=await client.post(_ace_url("/query_result"),json={"task_id_list":[task_id]},headers=_ace_headers()); response.raise_for_status(); data=_unwrap(response.json())
    except httpx.HTTPError as exc: raise HTTPException(status_code=502,detail=f"ACE-Step service unavailable: {exc.__class__.__name__}") from exc
    if not isinstance(data,list) or not data: raise HTTPException(status_code=502,detail="ACE-Step returned no job result.")
    item=data[0]; status={0:"running",1:"succeeded",2:"failed"}.get(int(item.get("status",0)),"unknown"); result=item.get("result")
    if isinstance(result,str):
        try: result=json.loads(result)
        except json.JSONDecodeError: result=[]
    result=result if isinstance(result,list) else []; audio_url=None
    if status=="succeeded" and result and result[0].get("file"): audio_url=_ace_url(result[0]["file"])
    return {"task_id":task_id,"status":status,"audio_url":audio_url}
