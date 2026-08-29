"""Task use cases: validate input, talk to the models, shape the result. No SQL/ORM
access happens outside this layer's calls into the models, and no HTTP concerns
(request/response objects) live here — that stays in routes/task_routes.py."""
import threading

from sqlalchemy.orm import joinedload

import database
from config import settings
from database import db
from errors import ApiError
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import NotificationService
from utils.helpers import calculate_percentage, log_action, utc_now
from validators.task_validator import validate_task_payload

# One service instance for the process, configured from env (see config/settings.py)
# instead of the hardcoded SMTP credentials the audit flagged.
_notification_service = NotificationService(
    host=settings.SMTP_HOST,
    port=settings.SMTP_PORT,
    user=settings.SMTP_USER,
    password=settings.SMTP_PASSWORD,
)


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    return [_serialize(task) for task in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)
    return _serialize(task)


def create_task(data):
    if not data:
        raise ApiError('Dados inválidos')

    cleaned, error = validate_task_payload(data, partial=False)
    if error:
        raise ApiError(error)

    _ensure_references_exist(cleaned)

    task = Task(**cleaned)
    db.session.add(task)
    database.save()
    log_action('Task criada', f'{task.id} - {task.title}')

    if task.user_id:
        _notify_assignment_async(db.session.get(User, task.user_id), task)

    return _serialize(task)


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)

    if not data:
        raise ApiError('Dados inválidos')

    cleaned, error = validate_task_payload(data, partial=True)
    if error:
        raise ApiError(error)

    _ensure_references_exist(cleaned)

    for field, value in cleaned.items():
        setattr(task, field, value)
    task.updated_at = utc_now()

    database.save()
    log_action('Task atualizada', str(task.id))

    if cleaned.get('user_id'):
        _notify_assignment_async(db.session.get(User, cleaned['user_id']), task)

    return _serialize(task)


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)

    db.session.delete(task)
    database.save()
    log_action('Task deletada', str(task_id))


def search_tasks(query, status, priority, user_id):
    tasks_query = Task.query.options(joinedload(Task.user), joinedload(Task.category))

    if query:
        tasks_query = tasks_query.filter(
            db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
        )
    if status:
        tasks_query = tasks_query.filter(Task.status == status)
    if priority:
        tasks_query = tasks_query.filter(Task.priority == int(priority))
    if user_id:
        tasks_query = tasks_query.filter(Task.user_id == int(user_id))

    return [_serialize(task) for task in tasks_query.all()]


def get_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()
    overdue = Task.query.filter(
        Task.due_date < utc_now(),
        Task.status.notin_(['done', 'cancelled']),
    ).count()

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue,
        'completion_rate': calculate_percentage(done, total),
    }


def _notify_assignment_async(user, task):
    """Fire the "task assigned" email in a background thread so a slow/unreachable
    SMTP server (there's no timeout in smtplib.SMTP by default) can't add latency to
    the create/update request. Scalar values are read out of the ORM objects here,
    on the request's own thread/session, and only plain values cross into the
    background thread — see the NotificationService docstring for why."""
    if not user:
        return

    kwargs = dict(
        user_id=user.id,
        user_email=user.email,
        user_name=user.name,
        task_id=task.id,
        task_title=task.title,
        task_priority=task.priority,
        task_status=task.status,
    )
    threading.Thread(
        target=_notification_service.notify_task_assigned,
        kwargs=kwargs,
        daemon=True,
    ).start()


def _ensure_references_exist(cleaned):
    if cleaned.get('user_id') and not db.session.get(User, cleaned['user_id']):
        raise ApiError('Usuário não encontrado', 404)
    if cleaned.get('category_id') and not db.session.get(Category, cleaned['category_id']):
        raise ApiError('Categoria não encontrada', 404)


def _serialize(task):
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data
