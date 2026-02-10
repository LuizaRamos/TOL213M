class TextService:
    def encrypt_and_store(self, user_id: int, title: str, plaintext: str):
        raise NotImplementedError

    def decrypt_for_user(self, user_id: int, text_id: int) -> str:
        raise NotImplementedError
