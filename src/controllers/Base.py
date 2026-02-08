from __future__ import annotations
from typing import Any, Optional, Dict, Tuple
from flask import jsonify, request
from werkzeug.exceptions import BadRequest

def json_ok(data: Any = None, status: int = 200):
    payload = {"ok": True, "data": data}
    return jsonify(payload), status

def json_error(message: str, status: int = 400, code: Optional[int] = None, details: Any = None) -> Tuple[Any, int]:
    payload = {"ok": False, "error": {"message": message, "code": code, "details": details}}
    return jsonify(payload), status

def get_json() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("No JSON data provided")
    if not isinstance(data, dict):
        raise BadRequest("JSON must be an object")
    return data

def require_fields(data: Dict[str, Any], fields: Tuple[str]) -> None:
    missing = [f for f in fields if f not in data or data[f] in (None, "null")]
    if missing:
        raise BadRequest(f"Missing {', '.join(missing)}")
    return None