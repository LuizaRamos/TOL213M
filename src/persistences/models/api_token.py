from __future__ import annotations
from datetime import datetime
import secrets

from src import db

class ApiToken(db.Model):
    __tablename__ = "api_token"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", foreign_keys=[user_id])

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(64)

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None