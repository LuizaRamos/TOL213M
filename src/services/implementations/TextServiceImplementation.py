import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.persistences.models.Text import Text
from src.persistences.models import db

class TextServiceImplementation:
    def __init__(self, master_key: bytes):
        if len(master_key) != 32:
            raise ValueError("master_key must be 32 bytes (AES-256)")
        self.master_key = master_key

        def encrypt_and_store(self, user_id: int, title: str, plaintext: str) -> Text:
            data = plaintext.encode("utf-8")
            nonce = os.urandom(12)
            aesgcm = AESGCM(self.master_key)
            ct = aesgcm.encrypt(nonce, data, None)

            obj = Text(
                user_id=user_id,
                title=title or "Untitled",
                nonce=nonce,
                ciphertext=ct,
                content_size=len(data),
            )
            db.session.add(obj)
            db.session.commit()
            return obj

        def decrypt_for_user(self, text_obj: Text) -> str:
            aesgcm = AESGCM(self.master_key)
            pt = aesgcm.decrypt(text_obj.nonce, text_obj.ciphertext, None)
            return pt.decode("utf-8")
