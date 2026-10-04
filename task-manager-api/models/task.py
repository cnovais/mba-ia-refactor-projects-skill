from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.orm import selectinload

from database import BaseModel, db
from utils.helpers import utcnow

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
TERMINAL_STATUSES = (STATUS_DONE, STATUS_CANCELLED)
DEFAULT_STATUS = STATUS_PENDING

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # priorities 1 and 2 count as "high priority"
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200


class Task(BaseModel):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_detailed_dict(self, now=None):
        data = self.to_dict()
        data['overdue'] = self.is_overdue(now)
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_user_task_dict(self, now=None):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(now),
        }

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in TERMINAL_STATUSES)

    # --- queries -----------------------------------------------------------

    @classmethod
    def _overdue_condition(cls, now):
        return (
            cls.due_date.is_not(None),
            cls.due_date < now,
            or_(cls.status.is_(None), cls.status.not_in(TERMINAL_STATUSES)),
        )

    @classmethod
    def list_with_relations(cls):
        query = select(cls).options(selectinload(cls.user), selectinload(cls.category)).order_by(cls.id)
        return db.session.scalars(query).all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.scalars(select(cls).where(cls.user_id == user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = select(cls)
        if text:
            pattern = f'%{text}%'
            query = query.where(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.scalars(query.order_by(cls.id)).all()

    @classmethod
    def list_overdue(cls, now):
        return db.session.scalars(select(cls).where(*cls._overdue_condition(now)).order_by(cls.id)).all()

    @classmethod
    def count_overdue(cls, now):
        return db.session.scalar(select(func.count()).select_from(cls).where(*cls._overdue_condition(now)))

    @classmethod
    def _count_grouped_by(cls, column):
        rows = db.session.execute(select(column, func.count()).group_by(column)).all()
        return {key: total for key, total in rows}

    @classmethod
    def count_by_status(cls):
        return cls._count_grouped_by(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls._count_grouped_by(cls.priority)

    @classmethod
    def count_by_user(cls):
        return cls._count_grouped_by(cls.user_id)

    @classmethod
    def count_by_category(cls):
        return cls._count_grouped_by(cls.category_id)

    @classmethod
    def completion_by_user(cls):
        """{user_id: (total_tasks, done_tasks)} in a single grouped query."""
        done = func.sum(case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.execute(select(cls.user_id, func.count(), done).group_by(cls.user_id)).all()
        return {user_id: (total, done_count or 0) for user_id, total, done_count in rows}

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(select(func.count()).select_from(cls).where(cls.created_at >= since))

    @classmethod
    def count_done_since(cls, since):
        return db.session.scalar(
            select(func.count()).select_from(cls).where(cls.status == STATUS_DONE, cls.updated_at >= since)
        )

    @classmethod
    def delete_by_user(cls, user_id):
        """Stages the deletion of a user's tasks; committed by the caller's next save/delete."""
        db.session.execute(delete(cls).where(cls.user_id == user_id))

    @classmethod
    def detach_category(cls, category_id):
        """Stages clearing category_id on tasks of a category; committed by the caller."""
        db.session.execute(update(cls).where(cls.category_id == category_id).values(category_id=None))
