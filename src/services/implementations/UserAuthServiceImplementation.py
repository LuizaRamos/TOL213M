import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from flask import session
from src.persistences.repositories.UserRepository import UserRepository
from src.services.implementations.AuthServiceImplementation import AuthServiceImplementation

class UserAuthServiceImplementation:
    def __init__(self):
        self.auth = AuthServiceImplementation()

    def derive_master_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=200_000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def register(self, username: str, password: str):
        return self.auth.register(username, password)

    def login(self, username: str, password: str):
        user = UserRepository.find_by_username(username)
        if not user:
            return None

        if not self.auth.verify_password(user, password):
            return None

        master_key = self._derive_master_key(password, user.kdf_salt)

        session["user_id"] = user.id
        session["username"] = user.username
        session["master_key_b64"] = base64.b64encode(master_key).decode("ascii")

        return user

    def logout(self):
        session.clear()

    def get_logged_in_user_id(self):
        return session.get("user_id")

    def get_master_key(self) -> bytes | None:
        mk = session.get("master_key_b64")
        if not mk:
            return None
        import base64
        return base64.b64decode(mk)
