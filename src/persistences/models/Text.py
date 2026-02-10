from datetime import datetime
from src.persistences.models import db

class Text(db.Model):
    __tablename__ = "texts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False)
    nonce = db.Column(db.LargeBinary, nullable=False)  # 12 bytes for AES-GCM
    ciphertext = db.Column(db.LargeBinary, nullable=False)  # includes tag
    content_size = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
