import logging

from errors import NotFoundError
from models.category import Category
from models.task import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow
from validators.task_validator import parse_search_params, validate_task_create, validate_task_update

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_references_exist(user_id, category_id):
    if user_id and not User.get_by_id(user_id):
        raise NotFoundError('Usuário não encontrado')
    if category_id and not Category.get_by_id(category_id):
        raise NotFoundError('Categoria não encontrada')


def list_tasks():
    now = utcnow()
    return [task.to_detailed_dict(now) for task in Task.list_with_relations()]


def get_task(task_id):
    task = _get_task_or_404(task_id)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(data):
    fields = validate_task_create(data)
    _ensure_references_exist(fields['user_id'], fields['category_id'])
    task = Task(**fields).save()
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def update_task(task_id, data):
    task = _get_task_or_404(task_id)
    changes = validate_task_update(data)
    _ensure_references_exist(changes.get('user_id'), changes.get('category_id'))
    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = utcnow()
    task.save()
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    task.delete()
    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    return [task.to_dict() for task in Task.search(**parse_search_params(args))]


def task_stats():
    total = Task.count()
    by_status = Task.count_by_status()
    done = by_status.get(STATUS_DONE, 0)
    return {
        'total': total,
        'pending': by_status.get(STATUS_PENDING, 0),
        'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(STATUS_CANCELLED, 0),
        'overdue': Task.count_overdue(utcnow()),
        'completion_rate': calculate_percentage(done, total),
    }
