from datetime import datetime

from errors import ValidationError
from models.task import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_STATUSES,
)
from validators.common import is_int, optional_id, optional_int_param, require_body

DUE_DATE_FORMAT = '%Y-%m-%d'


def _validate_title_length(title):
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')


def _validate_status(status):
    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise ValidationError('Status inválido')


def _validate_priority(priority):
    if not is_int(priority) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')


def _parse_due_date(value, error_message):
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message)


def _normalize_tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return ','.join(tags)
    raise ValidationError('Tags inválidas')


def validate_task_create(data):
    require_body(data)

    title = data.get('title')
    if not title or not isinstance(title, str):
        raise ValidationError('Título é obrigatório')
    _validate_title_length(title)

    status = data.get('status', DEFAULT_STATUS)
    _validate_status(status)

    priority = data.get('priority', DEFAULT_PRIORITY)
    _validate_priority(priority)

    fields = {
        'title': title,
        'description': data.get('description', ''),
        'status': status,
        'priority': priority,
        'user_id': optional_id(data.get('user_id'), 'user_id'),
        'category_id': optional_id(data.get('category_id'), 'category_id'),
    }
    if data.get('due_date'):
        fields['due_date'] = _parse_due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        fields['tags'] = _normalize_tags(data['tags'])
    return fields


def validate_task_update(data):
    require_body(data)
    changes = {}

    if 'title' in data:
        title = data['title']
        if not isinstance(title, str):
            raise ValidationError('Título muito curto')
        _validate_title_length(title)
        changes['title'] = title

    if 'description' in data:
        changes['description'] = data['description']

    if 'status' in data:
        _validate_status(data['status'])
        changes['status'] = data['status']

    if 'priority' in data:
        _validate_priority(data['priority'])
        changes['priority'] = data['priority']

    if 'user_id' in data:
        changes['user_id'] = optional_id(data['user_id'], 'user_id')

    if 'category_id' in data:
        changes['category_id'] = optional_id(data['category_id'], 'category_id')

    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = _parse_due_date(due_date, 'Formato de data inválido') if due_date else None

    if 'tags' in data:
        changes['tags'] = _normalize_tags(data['tags'])

    return changes


def parse_search_params(args):
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': optional_int_param(args, 'priority'),
        'user_id': optional_int_param(args, 'user_id'),
    }
