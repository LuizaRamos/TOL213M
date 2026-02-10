from src.persistences.models import db
from src.persistences.models.User import User

class UserRepository:
    @staticmethod
    def create(user: User):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def find_by_username(username: str):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_id(user_id: int):
        return User.query.get(user_id)
