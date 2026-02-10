from __future__ import annotations

import base64
from functools import wraps
from typing import Callable, Any, Optional
from flask import (request, g, Blueprint, render_template, abort,
                   session, redirect, url_for, flash)
from flask_login import (login_user, logout_user, login_required,
                         current_user)
import re

from src.controllers.Base import json_error
from src.controllers.UserController import user_controller
from src.persistences.models import db
from src.persistences.models.User import User
from src.persistences.models.api_token import ApiToken
from src.services.implementations.UserAuthServiceImplementation import UserAuthServiceImplementation

home_controller = Blueprint('home_controller', __name__, template_folder='templates')

def _get_bearer_token() -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token_value = auth.removeprefix("Bearer ").strip()
    return token_value or None

def _get_token() -> Optional[str]:
    return session.get("token") or _get_bearer_token()

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

@home_controller.route('/')
def index():
    return render_template("index.html")

@user_controller.post('/login')
def login_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid username or password")
        return redirect(url_for("home_controller.index"))

    master_key = UserAuthServiceImplementation.derive_master_key(password, user.kdf_salt)

    # Store in session (base64 because session must store serializable data)
    session["master_key"] = base64.b64encode(master_key).decode()

    login_user(user)
    flash("Login successful")
    return redirect(url_for("text_controller.dashboard"))

@user_controller.get("/register")
def register_page():
    return render_template("register.html")

@user_controller.post("/register")
def register_submit():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not username:
        flash("Name is required")
        return redirect(url_for("user_controller.register_page"))

    if password != confirm_password:
        flash("Passwords do not match")
        return redirect(url_for("user_controller.register_page"))

    # Same rule as HTML
    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

    if not re.match(password_regex, password):
        flash("Password must be at least 8 characters, include uppercase, lowercase and a number.")
        return redirect(url_for("user_controller.register_page"))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("User already exists")
        return redirect(url_for("user_controller.register_page"))

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Account created successfully")
    return redirect(url_for("home_controller.index"))
