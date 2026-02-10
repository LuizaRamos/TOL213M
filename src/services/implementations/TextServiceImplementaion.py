import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.persistences.models.Text import Text
from src.persistences.repositories.TextRepository import TextRepository

class TextServiceImplementaion:
    def __init__(self, master_key: bytes):
        self.master_key = master_key

    def encrypt_and_store(self, user_id: int, title: str, plaintext: str):
        plaintext_bytes = plaintext.encode("utf-8")
        content_size = len(plaintext_bytes)

        # random per-record data key (DEK)
        dek = os.urandom(32)

        # encrypt content with DEK
        content_nonce = os.urandom(12)
        content_aesgcm = AESGCM(dek)
        content_ciphertext = content_aesgcm.encrypt(content_nonce, plaintext_bytes, None)

        # wrap DEK with master key
        wrap_nonce = os.urandom(12)
        master_aesgcm = AESGCM(self.master_key)
        wrapped_dek = master_aesgcm.encrypt(wrap_nonce, dek, None)

        text_obj = Text(
            user_id=user_id,
            title=title,
            content_nonce=content_nonce,
            content_ciphertext=content_ciphertext,
            dek_wrapped_nonce=wrap_nonce,
            dek_wrapped_ciphertext=wrapped_dek,
            content_size=content_size,
        )

        return TextRepository.create(text_obj)

    def decrypt_for_user(self, text_obj: Text) -> str:
        master_aesgcm = AESGCM(self.master_key)

        # unwrap DEK
        dek = master_aesgcm.decrypt(text_obj.dek_wrapped_nonce, text_obj.dek_wrapped_ciphertext, None)

        # decrypt content
        content_aesgcm = AESGCM(dek)
        plaintext_bytes = content_aesgcm.decrypt(text_obj.content_nonce, text_obj.content_ciphertext, None)

        return plaintext_bytes.decode("utf-8", errors="strict")
