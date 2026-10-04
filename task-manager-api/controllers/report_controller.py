from datetime import timedelta

from errors import NotFoundError
from models.category import Category
from models.task import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    Task,
)
from models.user import User
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_DAYS = 7


def _status_breakdown(by_status):
    return {
        STATUS_PENDING: by_status.get(STATUS_PENDING, 0),
        STATUS_IN_PROGRESS: by_status.get(STATUS_IN_PROGRESS, 0),
        STATUS_DONE: by_status.get(STATUS_DONE, 0),
        STATUS_CANCELLED: by_status.get(STATUS_CANCELLED, 0),
    }


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    by_priority = Task.count_by_priority()
    overdue_tasks = Task.list_overdue(now)
    completion = Task.completion_by_user()

    user_productivity = []
    for user in User.list_all():
        total, completed = completion.get(user.id, (0, 0))
        user_productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count(),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': _status_breakdown(Task.count_by_status()),
        'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_since(since),
        },
        'user_productivity': user_productivity,
    }


def user_report(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    now = utcnow()
    tasks = Task.list_by_user(user_id)
    by_status = {}
    for task in tasks:
        by_status[task.status] = by_status.get(task.status, 0) + 1
    statuses = _status_breakdown(by_status)
    total = len(tasks)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **statuses,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(statuses[STATUS_DONE], total),
        },
    }
