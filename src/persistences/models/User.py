from datetime import datetime
import os
from argon2 import PasswordHasher
from flask_login import UserMixin
from src.persistences.models import db

ph = PasswordHasher()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(120), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.Text, nullable=False)

    kdf_salt = db.Column(db.LargeBinary, nullable=False, default=lambda: os.urandom(16))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = ph.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            return ph.verify(self.password_hash, password)
        except Exception:
            return False