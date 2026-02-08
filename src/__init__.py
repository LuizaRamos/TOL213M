from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src import app
from src.controllers.rest.UserRESTController import user_api
from src.config import Config

app.register_blueprint(user_api)

db = SQLAlchemy()

class LoginManager:
    pass

login_manager = LoginManager()

def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'

    from src.controllers.HomeController import home_bp
    from src.controllers.UserController import user_bp
    from src.controllers.TextController import text_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(text_bp)

    with app.app_context():
        db.create_all()

    return app