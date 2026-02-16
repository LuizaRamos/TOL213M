import os
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = SRC_DIR / "Instance"

DEFAULT_DB_PATH = INSTANCE_DIR / "app.db"
DEFAULT_DB_URI = f"sqlite:///{DEFAULT_DB_PATH}"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Get URL or fallback to local SQLite
    uri = os.environ.get("DATABASE_URL", DEFAULT_DB_URI)

    # Fix driver prefix for SQLAlchemy 1.4+ and Python 3.14 (psycopg v3)
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg://", 1)
    elif uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session
    SESSION_TYPE = "sqlalchemy"
    # SESSION_FILE_DIR is not needed when using SESSION_TYPE="sqlalchemy"
    SESSION_PERMANENT = False