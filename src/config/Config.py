import os
from pathlib import Path

RENDER_EXTERNAL_URL = "postgresql://bp_database_user:vm0iwT1Ya878okBSKOVyesNVxWEC0iDc@dpg-d69hv5f5r7bs73f8hseg-a.oregon-postgres.render.com/bp_database"

SRC_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = SRC_DIR / "Instance"

# Add this line to create the folder if it's missing
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = INSTANCE_DIR / "app.db"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    uri = os.environ.get("DATABASE_URI", RENDER_EXTERNAL_URL)

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg://", 1)
    elif uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session
    SESSION_TYPE = "sqlalchemy"
    SESSION_PERMANENT = False