from __future__ import annotations
from functools import wraps
from typing import Callable, Any
from flask import request, g
from src.controllers.Base import json_error
from src.persistences.models.api_token import ApiToken

def auth_required(f: Callable[..., Any]):
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return json_error("Unauthorized access", 401)

        token_value = auth.removeprefix("Bearer ").strip()
        if not token_value:
            return json_error("Unauthorized access", 401)

        token = ApiToken.query.filter_by(token=token_value).first()
        if not token or not token.is_active:
            return json_error("Invalid or revoked token", 401)

        g.current_user = token.user
        g.current_token = token
        return f(*args, **kwargs)

    return wrapper
