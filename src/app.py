from flask import Flask
from flask_session import Session
from flask_login import LoginManager
from src.config import Config
from src.persistences.models import db
from src.controllers.HomeController import home_controller
from src.controllers.UserController import user_controller
from src.controllers.TextController import text_controller

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DB first
    db.init_app(app)

    app.config["SESSION_SQLALCHEMY"] = db
    Session(app)

    login_manager = LoginManager()
    login_manager.login_view = "home_controller.index"
    login_manager.init_app(app)

    with app.app_context():
        from src.persistences.models.User import User
        from src.persistences.models.Text import Text
        from src.persistences.models.api_token import ApiToken
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # Blueprints
    app.register_blueprint(home_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(text_controller)

    return app
app = create_app()
