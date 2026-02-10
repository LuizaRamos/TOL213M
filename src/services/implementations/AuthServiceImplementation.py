import os
from argon2 import PasswordHasher
from src.persistences.models.User import User
from src.persistences.repositories.UserRepository import UserRepository

ph = PasswordHasher()  # Argon2id defaults are good for coursework

class AuthServiceImplementation:
    def register(self, username: str, password: str):
        if UserRepository.find_by_username(username):
            raise ValueError("Username already exists")

        password_hash = ph.hash(password)
        kdf_salt = os.urandom(16)

        user = User(username=username, password_hash=password_hash, kdf_salt=kdf_salt)
        return UserRepository.create(user)

    def verify_password(self, user: User, password: str) -> bool:
        try:
            return ph.verify(user.password_hash, password)
        except Exception:
            return False
