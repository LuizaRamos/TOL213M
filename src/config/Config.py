import os
from pathlib import Path
from sqlalchemy.engine import make_url

RENDER_EXTERNAL_URL = "postgresql://bp_database_user:vm0iwT1Ya878okBSKOVyesNVxWEC0iDc@dpg-d69hv5f5r7bs73f8hseg-a.oregon-postgres.render.com/bp_database"

SRC_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = SRC_DIR / "Instance"

DEFAULT_DB_PATH = INSTANCE_DIR / "app.db"
DEFAULT_DB_URI = f"sqlite:///{DEFAULT_DB_PATH}"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = make_url(RENDER_EXTERNAL_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session
    SESSION_TYPE = "sqlalchemy"
    SESSION_PERMANENT = False