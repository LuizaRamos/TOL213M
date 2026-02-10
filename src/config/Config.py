import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # SQLite DB
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "Instance", "app.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session (server-side)
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(os.path.dirname(BASE_DIR), "Instance", "sessions")
    SESSION_PERMANENT = False

