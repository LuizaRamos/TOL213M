from datetime import datetime
from src.persistences.models import db

class Text(db.Model):
    __tablename__ = "texts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)

    # AES-GCM nonce + ciphertext for the text content
    content_nonce = db.Column(db.LargeBinary, nullable=False)
    content_ciphertext = db.Column(db.LargeBinary, nullable=False)

    # Wrapped DEK (Data Encryption Key) using user master key
    dek_wrapped_nonce = db.Column(db.LargeBinary, nullable=False)
    dek_wrapped_ciphertext = db.Column(db.LargeBinary, nullable=False)

    content_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
