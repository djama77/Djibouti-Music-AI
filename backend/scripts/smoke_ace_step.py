#!/usr/bin/env python3
"""Live smoke test for a configured ACE-Step 1.5 API server.

Run with:
  ACESTEP_BASE_URL=https://your-gpu-host python scripts/smoke_ace_step.py --language so

The script submits one short generation, polls its task, downloads the result,
and validates that a non-empty audio file is returned. It never prints API keys.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib.parse import parse_qs, urlsplit

import httpx


def unwrap(payload: dict):
    if payload.get("error") or payload.get("code", 200) not in (0, 200):
        raise RuntimeError("ACE-Step returned an unsuccessful response envelope.")
    return payload.get("data", payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", default="so", help="ACE-Step vocal language code (e.g. so, aa, fr)")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900, help="Maximum wait for generation, in seconds")
    args = parser.parse_args()

    base_url = os.getenv("ACESTEP_BASE_URL", "").rstrip("/")
    if not base_url:
        print("BLOCKED: ACESTEP_BASE_URL is not configured.", file=sys.stderr)
        return 2

    headers = {}
    api_key = os.getenv("ACESTEP_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": "A short, gentle traditional Horn of Africa instrumental with plucked strings and soft percussion",
        "lyrics": "",
        "audio_duration": args.duration,
        "audio_format": "mp3",
        "vocal_language": args.language,
        "thinking": False,
        "batch_size": 1,
    }

    with httpx.Client(timeout=httpx.Timeout(30.0, read=120.0)) as client:
        response = client.post(f"{base_url}/release_task", json=payload, headers=headers)
        response.raise_for_status()
        data = unwrap(response.json())
        task_id = data.get("task_id") if isinstance(data, dict) else None
        if not task_id:
            raise RuntimeError("ACE-Step did not return a task_id.")
        print(f"PASS: generation task accepted ({task_id}).")

        deadline = time.monotonic() + args.timeout
        result_items = []
        while time.monotonic() < deadline:
            response = client.post(
                f"{base_url}/query_result",
                json={"task_id_list": [task_id]},
                headers=headers,
            )
            response.raise_for_status()
            data = unwrap(response.json())
            if isinstance(data, list):
                item = data[0] if data else {}
            elif isinstance(data, dict):
                item = data
            else:
                item = {}
            status = item.get("status", 0)
            if status == 2:
                raise RuntimeError("ACE-Step reported that generation failed.")
            if status == 1:
                raw_result = item.get("result", [])
                if isinstance(raw_result, str):
                    try:
                        raw_result = json.loads(raw_result)
                    except json.JSONDecodeError as exc:
                        raise RuntimeError("ACE-Step returned invalid result JSON.") from exc
                result_items = raw_result if isinstance(raw_result, list) else [raw_result]
                break
            time.sleep(5)
        else:
            raise TimeoutError(f"Generation did not finish within {args.timeout} seconds.")

        audio_ref = next(
            (entry.get("file") for entry in result_items if isinstance(entry, dict) and isinstance(entry.get("file"), str)),
            None,
        )
        if not audio_ref:
            raise RuntimeError("Completed task did not include an audio file reference.")

        parsed = urlsplit(audio_ref)
        if parsed.scheme or parsed.netloc or parsed.path != "/v1/audio":
            raise RuntimeError("ACE-Step returned an unexpected audio route.")
        audio_path = parse_qs(parsed.query).get("path", [None])[0]
        if not audio_path or not audio_path.startswith("/") or ".." in audio_path.split("/"):
            raise RuntimeError("ACE-Step returned an unsafe audio path.")

        audio_response = client.get(
            f"{base_url}/v1/audio",
            params={"path": audio_path},
            headers=headers,
        )
        audio_response.raise_for_status()
        content_type = audio_response.headers.get("content-type", "").split(";")[0]
        if not content_type.startswith("audio/") or not audio_response.content:
            raise RuntimeError("ACE-Step did not return a non-empty audio response.")
        if len(audio_response.content) > 100 * 1024 * 1024:
            raise RuntimeError("Generated audio exceeds the application's 100 MB limit.")

        print(f"PASS: generated audio downloaded ({len(audio_response.content)} bytes; {content_type}).")
        print("ACE-Step live smoke test: SUCCESS.")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACE-Step live smoke test: FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
