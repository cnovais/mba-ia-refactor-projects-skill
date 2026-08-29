from datetime import timedelta

from sqlalchemy import func

from database import db
from errors import ApiError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import PRIORITY_LABELS, calculate_percentage, utc_now


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = dict(
        db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    )
    priority_counts = dict(
        db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    )

    now = utc_now()
    overdue_tasks = Task.query.filter(
        Task.due_date < now,
        Task.status.notin_(['done', 'cancelled']),
    ).all()
    overdue_list = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in overdue_tasks
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago,
    ).count()

    user_stats = _user_productivity_stats()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            status: status_counts.get(status, 0)
            for status in ('pending', 'in_progress', 'done', 'cancelled')
        },
        'tasks_by_priority': {
            label: priority_counts.get(priority, 0)
            for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    done = sum(1 for task in tasks if task.status == 'done')
    pending = sum(1 for task in tasks if task.status == 'pending')
    in_progress = sum(1 for task in tasks if task.status == 'in_progress')
    cancelled = sum(1 for task in tasks if task.status == 'cancelled')
    high_priority = sum(1 for task in tasks if task.priority <= 2)
    overdue = sum(1 for task in tasks if task.is_overdue())

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total),
        },
    }


def _user_productivity_stats():
    # One query for totals, one for completed — instead of the original's
    # one Task.query.filter_by(user_id=...) call per user (N+1).
    totals = dict(
        db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all()
    )
    completed = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )

    stats = []
    for user in User.query.all():
        total = totals.get(user.id, 0)
        done = completed.get(user.id, 0)
        stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        })
    return stats
