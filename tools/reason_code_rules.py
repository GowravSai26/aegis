import json
from pathlib import Path
from typing import Optional

_DB: dict = {}

def _load() -> dict:
    global _DB
    if not _DB:
        path = Path(__file__).parent.parent / "data" / "reason_codes.json"
        _DB = json.loads(path.read_text())
    return _DB

def get_reason_code(code: str) -> Optional[dict]:
    return _load().get(code)

def get_required_evidence(code: str) -> list[str]:
    entry = get_reason_code(code)
    return entry["required_evidence"] if entry else []

def get_winability_factors(code: str) -> list[str]:
    entry = get_reason_code(code)
    return entry["winability_factors"] if entry else []

def get_all_codes() -> list[str]:
    return list(_load().keys())
