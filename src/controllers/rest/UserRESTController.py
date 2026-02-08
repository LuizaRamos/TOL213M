from urllib import request

from flask import Blueprint, g
from werkzeug.exceptions import BadRequest
from src.controllers.Base import *
from src.controllers.UserController import auth_required
from src.persistences.models import User
from src.persistences.models.User import *
from src.persistences.models.api_token import ApiToken
from src import db

user_api = Blueprint('user_api', __name__, url_prefix='/users')

@user_api.post("/register")
def register():
    try:
        data = get_json()
        require_fields(data, ("email", "password"))

        email = data["email"].strip().lower()
        password = data["password"]

        if "@" not in email or len(email) > 255:
            raise BadRequest("Email not valid", status = 400)

        if len(password) < 6:
            raise BadRequest("Password must be at least 6 characters")

        if User.query.filter_by(email=email).first():
            return json_error("Email already exists", status=400)

        user = User(email = email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return json_ok({"id": user.id, "email": user.email}, status=201)

    except Exception as e:
        return json_error(str(e), status = 400)

@user_api.post("/login")
def login():
    try:
        data = get_json()
        require_fields(data, ("email", "password"))

        email = data["email"].strip().lower()
        password = data["password"]

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return json_error("Invalid credentials", status = 400)

        token_value = ApiToken.new_token()
        token = ApiToken(token=token_value, user_id=user.id)

        db.session.add(token)
        db.session.commit()

        return json_ok({"token": token_value})

    except Exception as e:
        return json_error(str(e), status = 400)

    @user_api.post("/me")
    @auth_required
    def me():
        user: User = g.current_user
        return json_ok({"id": user.id, "email": user.email})

