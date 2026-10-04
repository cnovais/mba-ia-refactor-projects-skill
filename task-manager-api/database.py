from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, select

db = SQLAlchemy()


class BaseModel(db.Model):
    """Persistence helpers shared by every model."""
    __abstract__ = True

    @classmethod
    def get_by_id(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def list_all(cls):
        return db.session.scalars(select(cls).order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count()).select_from(cls))

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
