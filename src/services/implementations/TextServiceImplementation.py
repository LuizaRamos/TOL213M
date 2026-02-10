import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.persistences.models.Text import Text
from src.persistences.models import db

class TextServiceImplementation:
    def __init__(self, master_key: bytes):
        if not isinstance(master_key, (bytes, bytearray)):
            raise TypeError("master_key must be bytes")
        if len(master_key) != 32:
            raise ValueError("master_key must be 32 bytes (AES-256)")
        self.master_key = bytes(master_key)

    def encrypt_and_store(self, user_id: int, title: str, plaintext: str) -> Text:
        data = plaintext.encode("utf-8")
        nonce = os.urandom(12)  # recommended size for AES-GCM
        aesgcm = AESGCM(self.master_key)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        obj = Text(
            user_id=user_id,
            title=title or "Untitled",
            nonce=nonce,
            ciphertext=ciphertext,
            content_size=len(data),
        )
        db.session.add(obj)
        db.session.commit()
        return obj

    def decrypt_for_user(self, text_obj: Text) -> str:
        aesgcm = AESGCM(self.master_key)
        plaintext_bytes = aesgcm.decrypt(text_obj.nonce, text_obj.ciphertext, None)
        return plaintext_bytes.decode("utf-8")