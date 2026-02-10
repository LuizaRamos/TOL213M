import os
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = SRC_DIR / "Instance"

DEFAULT_DB_PATH = INSTANCE_DIR / "app.db"
DEFAULT_DB_URI = f"sqlite:///{DEFAULT_DB_PATH}"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", DEFAULT_DB_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session (server-side)
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = str(INSTANCE_DIR / "sessions")
    SESSION_PERMANENT = False