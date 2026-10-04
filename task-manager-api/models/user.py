from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from database import BaseModel, db
from utils.helpers import utcnow

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)

# Checked against when the e-mail is unknown, so a login takes the same time either way.
_DUMMY_PASSWORD_HASH = generate_password_hash('dummy-password-for-timing')


class User(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        try:
            return check_password_hash(self.password, raw_password)
        except (ValueError, TypeError):
            # Unknown/legacy hash format: never treat it as a match.
            return False

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(select(cls).where(cls.email == email)).first()

    @classmethod
    def authenticate(cls, email, raw_password):
        """Returns the user only when the e-mail exists and the password matches."""
        user = cls.find_by_email(email)
        if not user:
            check_password_hash(_DUMMY_PASSWORD_HASH, raw_password)
            return None
        return user if user.check_password(raw_password) else None
