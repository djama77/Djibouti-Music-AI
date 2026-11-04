import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import _unwrap, GenerateRequest

def test_unwrap_data():
    assert _unwrap({"code":200,"data":{"task_id":"abc"}})=={"task_id":"abc"}

def test_unwrap_rejects_error():
    from fastapi import HTTPException
    try: _unwrap({"code":500,"error":"bad"})
    except HTTPException as exc: assert exc.status_code==502
    else: raise AssertionError("Expected HTTPException")

def test_generation_request_bounds_and_language():
    req=GenerateRequest(prompt="A joyful song",language="so",duration=45)
    assert req.duration==45 and req.language=="so"

def test_generation_request_rejects_unknown_language():
    from pydantic import ValidationError
    try: GenerateRequest(prompt="A song",language="xx")
    except ValidationError: return
    raise AssertionError("Expected ValidationError")
