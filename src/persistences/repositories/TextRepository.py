from src.persistences.models import db
from src.persistences.models.Text import Text

class TextRepository:
    @staticmethod
    def create(text_obj: Text):
        db.session.add(text_obj)
        db.session.commit()
        return text_obj

    @staticmethod
    def list_for_user(user_id: int):
        return Text.query.filter_by(user_id=user_id).order_by(Text.created_at.desc()).all()

    @staticmethod
    def find_for_user(text_id: int, user_id: int):
        return Text.query.filter_by(id=text_id, user_id=user_id).first()
