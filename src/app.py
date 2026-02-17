from __future__ import annotations

import ssl
from pathlib import Path

from flask import Flask, render_template, request, redirect
from flask_session import Session
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

from src.config import Config
from src.persistences.models import db
from src.controllers.HomeController import home_controller
from src.controllers.UserController import user_controller
from src.controllers.TextController import text_controller

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def create_ssl_context():
    cert = PROJECT_ROOT / "cert.pem"
    key = PROJECT_ROOT / "key.pem"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.load_cert_chain(certfile=cert, keyfile=key)
    ssl_context.set_ciphers("ECDHE+AESGCM:ECGHE+CHACHA20")
    ssl_context.options |= ssl.OP_NO_COMPRESSION
    return ssl_context

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Initialize DB first
    db.init_app(app)

    # Consolidated Session Setup
    if app.config.get("SESSION_TYPE") == "sqlalchemy":
        app.config["SESSION_SQLALCHEMY"] = db
        app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
        # We use this check to prevent double-initialization during scripts
        if "session" not in app.extensions:
            try:
                Session(app)
            except Exception as e:
                if "already defined" not in str(e):
                    raise e
    elif app.config.get("SESSION_TYPE"):
        Session(app)

    login_manager = LoginManager()
    login_manager.login_view = "home_controller.index"
    login_manager.init_app(app)

    with app.app_context():
        from src.persistences.models.User import User
        from src.persistences.models.Text import Text
        from src.persistences.models.api_token import ApiToken
        #db.create_all()

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # Blueprints
    app.register_blueprint(home_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(text_controller)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    @app.before_request
    def force_https():
        if request.is_secure:
            return None

        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, ssl_context=create_ssl_context())