class AuthService:
    def register(self, username: str, password: str):
        raise NotImplementedError

    def login(self, username: str, password: str):
        raise NotImplementedError
